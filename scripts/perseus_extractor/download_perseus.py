"""
download_perseus.py

Downloads all Perseus exercise templates from the Kolibri Studio CDN.
- Reads exercise nodes + file IDs from khan_academy.sqlite3
- Fetches each .perseus ZIP from studio.learningequality.org
- Extracts assessment item JSONs (question content, hints, widgets)
- Saves one JSON file per exercise node to output/perseus_templates/
- Fully resumable: skips already-downloaded files
- Polite: 1s delay between requests, retries on transient failures

Output format per file (output/perseus_templates/{node_id}.json):
{
  "node_id": "...",
  "title": "...",
  "description": "...",
  "topic_path": ["Math", "Early math", "Counting", ...],
  "assessment_items": [
    {
      "item_id": "...",
      "question_content": "...",   # markdown+LaTeX
      "hints": ["...", ...],
      "widget_types": ["radio", "expression", ...],
      "answer_data": {...}          # full widget options
    },
    ...
  ],
  "mastery_model": {"type": "m_of_n", "m": 5, "n": 7},
  "randomize": true
}
"""

import sqlite3
import os
import requests
import zipfile
import json
import io
import time
import sys
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

DB_PATH = Path(__file__).parent.parent.parent / "scripts" / "jump_start" / "data" / "khan_academy.sqlite3"
OUTPUT_DIR = Path(__file__).parent / "output" / "perseus_templates"
STUDIO_URL = "https://studio.learningequality.org/content/storage/{a}/{b}/{file_id}.perseus"
DELAY = 0.1       # seconds between requests per thread (10 threads = ~1 req/s effective)
MAX_RETRIES = 3
RETRY_DELAY = 3.0
WORKERS = 10      # parallel download threads
print_lock = threading.Lock()


def get_all_nodes(conn):
    """Build full node map from DB."""
    c = conn.cursor()
    c.execute("SELECT id, title, description, parent_id, kind FROM content_contentnode")
    return {row[0]: {"id": row[0], "title": row[1], "description": row[2],
                     "parent_id": row[3], "kind": row[4]}
            for row in c.fetchall()}


def get_topic_path(node_id, all_nodes):
    """Walk up the parent chain and return list of ancestor titles."""
    path, nid, seen = [], node_id, set()
    while nid and nid not in seen:
        seen.add(nid)
        n = all_nodes.get(nid)
        if not n:
            break
        path.append(n["title"])
        nid = n["parent_id"]
    return list(reversed(path))


def get_exercise_file_map(conn):
    """Return list of (node_id, title, description, local_file_id) for all exercise+perseus rows."""
    c = conn.cursor()
    c.execute("""
        SELECT n.id, n.title, n.description, f.local_file_id
        FROM content_contentnode n
        JOIN content_file f ON n.id = f.contentnode_id
        JOIN content_localfile l ON f.local_file_id = l.id
        WHERE n.kind = 'exercise' AND l.extension = 'perseus'
    """)
    return c.fetchall()


def fetch_perseus_zip(file_id, retries=MAX_RETRIES):
    """Fetch .perseus ZIP from Studio CDN. Returns bytes or None on failure."""
    url = STUDIO_URL.format(a=file_id[0], b=file_id[1], file_id=file_id)
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                return resp.content
            elif resp.status_code == 404:
                print(f"  404 not found: {url}")
                return None
            else:
                print(f"  HTTP {resp.status_code} on attempt {attempt}: {url}")
        except requests.RequestException as e:
            print(f"  Request error on attempt {attempt}: {e}")
        if attempt < retries:
            time.sleep(RETRY_DELAY)
    return None


def parse_perseus_zip(zip_bytes, node_id):
    """
    Extract assessment items from a .perseus ZIP.
    Returns list of item dicts with question_content, hints, widget_types, answer_data.
    """
    items = []
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            # Get exercise index
            if "exercise.json" not in z.namelist():
                return items
            with z.open("exercise.json") as f:
                exercise_meta = json.load(f)

            mastery = {
                "type": exercise_meta.get("mastery_model", "m_of_n"),
                "m": exercise_meta.get("m", 5),
                "n": exercise_meta.get("n", 7)
            }
            randomize = exercise_meta.get("randomize", True)
            all_item_ids = exercise_meta.get("all_assessment_items", [])

            # Parse each item JSON (named {item_id}.json in the zip)
            zip_names = set(z.namelist())
            for item_id in all_item_ids:
                item_filename = f"{item_id}.json"
                if item_filename not in zip_names:
                    continue
                try:
                    with z.open(item_filename) as f:
                        item_data = json.load(f)
                except Exception:
                    continue

                question = item_data.get("question", {})
                q_content = question.get("content", "")
                widgets = question.get("widgets", {})
                widget_types = list({w.get("type") for w in widgets.values() if isinstance(w, dict)})

                # Extract answer data (varies by widget type)
                answer_data = {}
                for wname, wdata in widgets.items():
                    if not isinstance(wdata, dict):
                        continue
                    opts = wdata.get("options", {})
                    wtype = wdata.get("type", "")
                    if wtype == "radio":
                        choices = opts.get("choices", [])
                        answer_data[wname] = {
                            "type": "radio",
                            "choices": [{"content": c.get("content", ""),
                                         "correct": c.get("correct", False)}
                                        for c in choices]
                        }
                    elif wtype == "numeric-input":
                        answer_data[wname] = {
                            "type": "numeric-input",
                            "answers": opts.get("answers", [])
                        }
                    elif wtype == "expression":
                        # Answers stored in answerForms[].value where considered=="correct"
                        answer_forms = opts.get("answerForms", [])
                        correct_forms = [
                            f.get("value", "") for f in answer_forms
                            if f.get("considered") == "correct" and f.get("value")
                        ]
                        answer_data[wname] = {
                            "type": "expression",
                            "correct_values": correct_forms,
                            # keep full answerForms for reference (simplify flags etc.)
                            "answerForms": answer_forms,
                        }
                    elif wtype == "orderer":
                        answer_data[wname] = {
                            "type": "orderer",
                            "correct_options": [o.get("content", "")
                                                for o in opts.get("correctOptions", [])]
                        }
                    elif wtype == "input-number":
                        # Answer stored directly in opts["value"], not opts["answers"]
                        answer_data[wname] = {
                            "type": "input-number",
                            "value": opts.get("value"),
                            "answerType": opts.get("answerType", "number"),
                            "simplify": opts.get("simplify", ""),
                            "inexact": opts.get("inexact", False),
                            "maxError": opts.get("maxError", 0.1),
                        }
                    else:
                        answer_data[wname] = {"type": wtype, "options": opts}

                hints_raw = item_data.get("hints", [])
                hints = [h.get("content", "") for h in hints_raw if isinstance(h, dict)]

                items.append({
                    "item_id": item_id,
                    "question_content": q_content,
                    "hints": hints,
                    "widget_types": widget_types,
                    "answer_data": answer_data
                })

            return items, mastery, randomize

    except zipfile.BadZipFile:
        print(f"  Bad ZIP for node {node_id}")
        return [], {}, True


def process_one(args_tuple):
    """Worker function: download + parse one exercise. Returns (status, node_id, title)."""
    node_id, title, description, file_id, all_nodes = args_tuple

    out_path = OUTPUT_DIR / f"{node_id}.json"
    if out_path.exists():
        return ("skip", node_id, title)

    topic_path = get_topic_path(node_id, all_nodes)

    zip_bytes = fetch_perseus_zip(file_id)
    if zip_bytes is None:
        return ("fail", node_id, title)

    result = parse_perseus_zip(zip_bytes, node_id)
    if isinstance(result, tuple):
        items, mastery, randomize = result
    else:
        items, mastery, randomize = [], {}, True

    output = {
        "node_id": node_id,
        "title": title,
        "description": description or "",
        "topic_path": topic_path,
        "assessment_items": items,
        "mastery_model": mastery,
        "randomize": randomize
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False)

    time.sleep(DELAY)
    return ("ok", node_id, title)


def main():
    parser = argparse.ArgumentParser(description="Download Perseus exercise templates from Kolibri Studio")
    parser.add_argument("--limit", type=int, default=None, help="Max exercises to download (for testing)")
    parser.add_argument("--subject", type=str, default=None,
                        help="Filter by subject path prefix, e.g. 'Math' or 'Math by grade'")
    parser.add_argument("--workers", type=int, default=WORKERS, help="Parallel download threads")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    all_nodes = get_all_nodes(conn)
    exercises = get_exercise_file_map(conn)
    conn.close()

    print(f"Found {len(exercises)} exercise nodes with Perseus files")

    if args.subject:
        filtered = []
        for row in exercises:
            node_id = row[0]
            path = get_topic_path(node_id, all_nodes)
            if any(args.subject.lower() in p.lower() for p in path):
                filtered.append(row)
        exercises = filtered
        print(f"Filtered to {len(exercises)} exercises under '{args.subject}'")

    if args.limit:
        exercises = exercises[:args.limit]
        print(f"Limited to {args.limit} exercises")

    total = len(exercises)
    skipped = 0
    downloaded = 0
    failed = 0

    # Pre-count already done
    already_done = sum(1 for (nid, *_) in exercises if (OUTPUT_DIR / f"{nid}.json").exists())
    print(f"Already downloaded: {already_done}/{total} (resuming)")
    print(f"Starting {args.workers} parallel workers...\n")

    work_items = [(nid, title, desc, fid, all_nodes) for nid, title, desc, fid in exercises]

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_one, item): item for item in work_items}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            status, node_id, title = future.result()
            if status == "skip":
                skipped += 1
            elif status == "ok":
                downloaded += 1
            else:
                failed += 1

            if completed % 50 == 0 or completed == total:
                with print_lock:
                    print(f"[{completed}/{total}] +{downloaded} downloaded, "
                          f"{skipped} skipped, {failed} failed", flush=True)

    print(f"\n{'='*50}")
    print(f"Done. {downloaded} downloaded, {skipped} skipped, {failed} failed")
    print(f"Templates saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
