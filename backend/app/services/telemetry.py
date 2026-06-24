import json
import datetime
from pathlib import Path
from typing import Optional

# Global in-memory caches to eliminate latency
ELA_SKELETON_CACHE = {}
QUESTION_CACHE = {} # key: f"{student_id}_{subject}_{subdomain}"
MATATAG_SKELETON_CACHE = {}  # key: skeleton_id (mat_grade_gen_seed format)
PRACTICE_GEN_CACHE = {}  # key: problem_id

# Path to the shared dedup scratch file
_SCRATCH_FILE = Path(__file__).parent.parent.parent.parent / "scratch" / "gen_problems.jsonl"

def load_previous_questions(student_id: int, node_id: str) -> list:
    if not _SCRATCH_FILE.exists():
        return []
    records = []
    try:
        with open(_SCRATCH_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if (obj.get("node_id") == node_id
                            and obj.get("student_id") == student_id
                            and obj.get("source") == "live_practice"):
                        records.append(obj)
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return records

def save_practice_question(
    student_id: int,
    node_id: str,
    problem_text: str,
    answer: str = "",
    subject: str = "Verbal",
    question_mode: str = "mcq",
) -> None:
    problem_text = problem_text.strip()
    if not problem_text:
        return
    record = {
        "student_id":    student_id,
        "node_id":       node_id,
        "subject":       subject,
        "question_mode": question_mode,
        "problem_text":  problem_text,
        "answer":        answer,
        "generated_at":  datetime.datetime.utcnow().isoformat(),
        "source":        "live_practice",
    }
    _SCRATCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_SCRATCH_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

def clear_student_history(student_id: int) -> None:
    if not _SCRATCH_FILE.exists():
        return
    try:
        kept = []
        with open(_SCRATCH_FILE, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    obj = json.loads(stripped)
                    if obj.get("source") == "live_practice" and obj.get("student_id") == student_id:
                        continue
                    kept.append(stripped)
                except json.JSONDecodeError:
                    kept.append(stripped)
        _SCRATCH_FILE.write_text("\n".join(kept) + ("\n" if kept else ""))
        print(f"[Dedup] Cleared session history for student {student_id}")
    except OSError as e:
        print(f"[ELA Dedup] Could not clear history: {e}")
