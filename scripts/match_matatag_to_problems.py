#!/usr/bin/env python3
"""
Match MATATAG Math learning competencies to Khan Academy Perseus practice problems.

Uses TF-IDF cosine similarity to match each competency string (from matatagmath.json)
against the title + description of all 9,072 Perseus exercise templates.
Only returns text-usable items (no image/graph/interactive widgets).

Output mirrors the matatagmath.json hierarchy, replacing each competency string with
an object containing the competency text and its top-3 matched practice problems.
"""

import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATATAG_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "ph", "matatagmath.json")
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "scripts", "perseus_extractor", "output", "perseus_templates")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "ph", "matatag_matched_problems.json")

# Widget types that require visual/interactive rendering — skip these
EXCLUDED_WIDGETS = {
    "image", "interactive-graph", "grapher", "sorter", "matcher",
    "orderer", "measurer", "transformer", "plotter",
    "label-image", "number-line", "interaction", "categorizer", "matrix",
}

# How many problems to attach per competency
TOP_N_PROBLEMS = 3
# How many candidate templates to consider before filtering for valid items
CANDIDATE_BUFFER = 30

# Citation pattern to strip from competency text before querying
CITE_PATTERN = re.compile(r"\[cite:\s*[\d,\s]+\]")


def tokenize(text):
    """Lowercase, split on non-alphanumeric, return list of tokens."""
    return re.findall(r"[a-z0-9]+", text.lower())


def strip_citation(text):
    """Remove [cite: ...] patterns from competency text."""
    return CITE_PATTERN.sub("", text).strip()


def build_metadata_index(templates_dir):
    """
    Scan all template JSON files and build a lightweight metadata index.
    Returns: dict[node_id] = {title, description, topic_path, document_tokens}
    """
    index = {}
    files = [f for f in os.listdir(templates_dir) if f.endswith(".json")]
    total = len(files)

    for i, filename in enumerate(files):
        if (i + 1) % 1000 == 0:
            print(f"  Indexing: {i + 1}/{total}...", file=sys.stderr)

        filepath = os.path.join(templates_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        node_id = data.get("node_id", filename.replace(".json", ""))
        title = data.get("title", "")
        description = data.get("description", "")
        topic_path = data.get("topic_path", [])

        # Build the searchable document from title + description + last 2 topic path segments
        topic_tail = " ".join(topic_path[-2:]) if len(topic_path) >= 2 else " ".join(topic_path)
        document = f"{title} {description} {topic_tail}"
        tokens = tokenize(document)

        if not tokens:
            continue

        index[node_id] = {
            "title": title,
            "description": description,
            "topic_path": topic_path,
            "tokens": tokens,
            "filepath": filepath,
        }

    print(f"  Indexed {len(index)} templates.", file=sys.stderr)
    return index


def build_tfidf_index(metadata_index):
    """
    Build an inverted TF-IDF index from the metadata.
    Returns: (inverted_index, idf_weights, doc_norms)
      inverted_index: term -> {node_id: tf_idf_weight}
      idf_weights: term -> idf
      doc_norms: node_id -> L2 norm of document vector
    """
    N = len(metadata_index)

    # Document frequency: how many documents contain each term
    df = Counter()
    doc_tf = {}  # node_id -> Counter of term frequencies

    for node_id, meta in metadata_index.items():
        tf = Counter(meta["tokens"])
        doc_tf[node_id] = tf
        for term in tf:
            df[term] += 1

    # IDF weights
    idf = {}
    for term, freq in df.items():
        idf[term] = math.log(N / freq)

    # Build inverted index with TF-IDF weights and compute doc norms
    inverted = defaultdict(dict)
    doc_norms = {}

    for node_id, tf in doc_tf.items():
        norm_sq = 0.0
        for term, count in tf.items():
            weight = count * idf.get(term, 0)
            if weight > 0:
                inverted[term][node_id] = weight
                norm_sq += weight * weight
        doc_norms[node_id] = math.sqrt(norm_sq) if norm_sq > 0 else 1.0

    print(f"  Built TF-IDF index: {len(idf)} unique terms.", file=sys.stderr)
    return inverted, idf, doc_norms


def query_tfidf(query_text, inverted_index, idf, doc_norms, top_k=CANDIDATE_BUFFER):
    """
    Score all documents against a query string using TF-IDF cosine similarity.
    Returns: list of (node_id, score) sorted descending, top_k results.
    """
    query_tokens = tokenize(query_text)
    if not query_tokens:
        return []

    query_tf = Counter(query_tokens)

    # Build query vector and compute query norm
    query_weights = {}
    query_norm_sq = 0.0
    for term, count in query_tf.items():
        w = count * idf.get(term, 0)
        if w > 0:
            query_weights[term] = w
            query_norm_sq += w * w

    query_norm = math.sqrt(query_norm_sq) if query_norm_sq > 0 else 1.0

    # Accumulate dot products via inverted index
    scores = defaultdict(float)
    for term, q_weight in query_weights.items():
        if term in inverted_index:
            for node_id, d_weight in inverted_index[term].items():
                scores[node_id] += q_weight * d_weight

    # Normalize to cosine similarity
    results = []
    for node_id, dot in scores.items():
        cosine = dot / (query_norm * doc_norms[node_id])
        results.append((node_id, cosine))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


def is_item_text_usable(item):
    """Check if an assessment item can be rendered as text (no excluded widgets, no inline images)."""
    widget_types = set(item.get("widget_types", []))
    if len(widget_types & EXCLUDED_WIDGETS) > 0 or len(widget_types) == 0:
        return False

    # Reject items with inline images in question text
    question = item.get("question_content", "")
    if "![" in question or "web+graphie:" in question:
        return False

    return True


def extract_best_item(template_data):
    """
    From a loaded template, find the best text-usable assessment item.
    Prefers radio > numeric-input > expression > other.
    Returns the item dict or None.
    """
    items = template_data.get("assessment_items", [])
    valid_items = [item for item in items if is_item_text_usable(item)]

    if not valid_items:
        return None

    # Preference ordering
    def item_priority(item):
        wt = set(item.get("widget_types", []))
        if wt == {"radio"}:
            return 0
        elif "numeric-input" in wt or "input-number" in wt:
            return 1
        elif "expression" in wt:
            return 2
        elif "dropdown" in wt:
            return 3
        return 4

    valid_items.sort(key=item_priority)
    return valid_items[0]


def find_problems_for_competency(competency_text, inverted_index, idf, doc_norms, metadata_index):
    """
    Given a competency string, find the top-3 text-usable practice problems.
    Deduplicates by title to avoid returning the same exercise from different topic paths.
    Returns a list of problem dicts.
    """
    query = strip_citation(competency_text)
    candidates = query_tfidf(query, inverted_index, idf, doc_norms, top_k=CANDIDATE_BUFFER)

    problems = []
    seen_titles = set()

    for node_id, score in candidates:
        meta = metadata_index[node_id]

        # Deduplicate: skip if we already have a match with this title
        title = meta["title"]
        if title in seen_titles:
            continue

        # Load the full template to get assessment items
        try:
            with open(meta["filepath"], "r", encoding="utf-8") as f:
                template_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        item = extract_best_item(template_data)
        if item is None:
            continue

        seen_titles.add(title)
        problems.append({
            "template_id": node_id,
            "title": meta["title"],
            "topic_path": meta["topic_path"],
            "similarity_score": round(score, 4),
            "item_id": item.get("item_id", ""),
            "question_content": item.get("question_content", ""),
            "hints": item.get("hints", []),
            "widget_types": item.get("widget_types", []),
            "answer_data": item.get("answer_data", {}),
        })

        if len(problems) >= TOP_N_PROBLEMS:
            break

    return problems


def process_matatag(matatag_data, inverted_index, idf, doc_norms, metadata_index):
    """
    Walk the matatagmath.json hierarchy and replace each competency string
    with an object containing the competency and its matched problems.
    """
    result = {}
    competency_count = 0
    matched_count = 0

    # Structure: Mathematics > Grade > Strand > Quarter > [competencies]
    for subject, grades in matatag_data.items():
        result[subject] = {}
        for grade, strands in grades.items():
            result[subject][grade] = {}
            for strand, quarters in strands.items():
                result[subject][grade][strand] = {}
                for quarter, competencies in quarters.items():
                    result[subject][grade][strand][quarter] = []
                    for comp_text in competencies:
                        competency_count += 1
                        problems = find_problems_for_competency(
                            comp_text, inverted_index, idf, doc_norms, metadata_index
                        )

                        if problems:
                            matched_count += 1

                        result[subject][grade][strand][quarter].append({
                            "competency": comp_text,
                            "matched_problems": problems,
                        })

                        if competency_count % 25 == 0:
                            print(f"  Processed {competency_count} competencies...", file=sys.stderr)

    print(f"\n  Done: {competency_count} competencies, {matched_count} with at least 1 match.", file=sys.stderr)
    return result


def main():
    print("=" * 60, file=sys.stderr)
    print("MATATAG → Perseus Practice Problem Matcher", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Load MATATAG curriculum
    print("\n[1/5] Loading MATATAG curriculum...", file=sys.stderr)
    with open(MATATAG_PATH, "r", encoding="utf-8") as f:
        matatag = json.load(f)

    # Build metadata index from templates
    print("\n[2/5] Building metadata index from 9,072 templates...", file=sys.stderr)
    metadata_index = build_metadata_index(TEMPLATES_DIR)

    # Build TF-IDF inverted index
    print("\n[3/5] Building TF-IDF inverted index...", file=sys.stderr)
    inverted_index, idf, doc_norms = build_tfidf_index(metadata_index)

    # Match competencies to problems
    print("\n[4/5] Matching competencies to practice problems...", file=sys.stderr)
    output = process_matatag(matatag, inverted_index, idf, doc_norms, metadata_index)

    # Write output
    print("\n[5/5] Writing output...", file=sys.stderr)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  Output written to: {OUTPUT_PATH}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


if __name__ == "__main__":
    main()
