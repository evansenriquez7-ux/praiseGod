"""
Frontend grader-contract round-trip auditor.

Catches the class of bugs where the three graders (portal, lab v1, lab v2)
disagree on `is_correct` for a known-correct student answer. Bug #002
(fraction_shade set_click portal=False vs v1/v2=True), #003 (cloze
v1=False vs portal/v2=True), and #004 (mcq value leniency) are the
canonical examples.

Strategy: for every (node × formatter) enabled in the saved
CompetencyConfiguration, generate a deterministic payload, derive a
known-correct student answer per the answer-collection mode, and submit
to all three grader routes via in-process TestClient. A passing node is
one where every formatter returns is_correct=True on all three graders.

The grader logic is invoked in-process via FastAPI's TestClient against
the live routes — this exercises the same code path the React frontend
hits when a student submits.

Usage:
    PYTHONPATH=. .venv/bin/python -m tests.grader_roundtrip_auditor
    PYTHONPATH=. .venv/bin/python -m tests.grader_roundtrip_auditor --node-ids mat_g3_na_q4_7
    PYTHONPATH=. .venv/bin/python -m tests.grader_roundtrip_auditor --no-parallel
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT / "local_only" / "scratch" / "oc"
SCRATCH.mkdir(parents=True, exist_ok=True)
OUT_JSON  = SCRATCH / "grader_roundtrip_findings.json"
OUT_JSONL = SCRATCH / "grader_roundtrip_findings.jsonl"


# ─────────────────────────────────────────────────────────────────────────────
# Emitters — inverse of the React component's `onAnswer` output for a given
# formatter. Given a problem payload, returns the known-correct student
# answer the React component would emit after a correct interaction.
# ─────────────────────────────────────────────────────────────────────────────

def _emit_correct(payload: Dict[str, Any]) -> Any:
    """Return the known-correct submission shape per answer_collection."""
    ac = payload.get("answer_collection") or ""
    ca = payload.get("correct_answer")
    fmt = payload.get("format") or ""
    is_visual = payload.get("is_visual", False)

    if ac == "mcq" or fmt == "mcq":
        # JSON keys from format_data mcq_options: pick is_correct option's key
        fd = payload.get("format_data") or {}
        opts = fd.get("mcq_options") or fd.get("options") or []
        if isinstance(opts, list):
            for o in opts:
                if isinstance(o, dict) and o.get("is_correct"):
                    return o.get("key", ca)
            # Fallback: correct_answer is 1 char → key
            if isinstance(ca, str) and len(ca) == 1 and ca.isalpha():
                return ca
        return ca
    if ac in {"click", "set"}:
        return ca  # Visual set mode: component emits the correct_answer string
    if ac == "fill_in_blank" or fmt == "cloze" or fmt == "fill_in_blank":
        return ca
    if fmt == "true_false" or ac == "true_false":
        return ca
    if fmt == "ordering":
        vp = payload.get("visual_params") or {}
        return vp.get("correct_sequence", ca)
    if fmt == "numeric_input" or ac == "numeric_input":
        return ca
    if fmt == "error_detect":
        return json.dumps(ca) if not isinstance(ca, str) else ca
    return ca


# ─────────────────────────────────────────────────────────────────────────────
# Per-node worker — module-level for ProcessPoolExecutor
# ─────────────────────────────────────────────────────────────────────────────

def _audit_node_grader(node_id: str, samples_per_formatter: int = 3) -> List[Dict[str, Any]]:
    from backend.app.practice_gen import registry as r  # noqa: F401
    from backend.app.practice_gen.pipeline import run as _pg_run
    from backend.app.models import CompetencyConfiguration, StudentProfile
    from backend.app.database import SessionLocal
    from backend.app.services.cache import _fallback_cache
    from fastapi.testclient import TestClient
    from backend.app.main import app

    findings: List[Dict[str, Any]] = []
    # Need a student for the portal route
    db = SessionLocal()
    try:
        student_name = f"GraderAudit_{node_id}"
        s = db.query(StudentProfile).filter_by(name=student_name).first()
        if not s:
            s = StudentProfile(name=student_name, pin_hash="x", age=8, grade=3, language_preference="en")
            db.add(s); db.commit(); db.refresh(s)
        sid = s.id
        row = db.query(CompetencyConfiguration).filter_by(node_id=node_id).first()
        if not row:
            return [{
                "node_id": node_id,
                "check": "no_config_row",
                "severity": "high",
                "message": "No CompetencyConfiguration row",
            }]
        allowed_fmt = row.allowed_formatters or []
        allowed_diff = row.allowed_difficulties or {}
        allowed_ctx = row.allowed_contexts or {}
    finally:
        db.close()

    client = TestClient(app)

    for fmt in allowed_fmt:
        for i in range(samples_per_formatter):
            seed = 500_000 + (hash((node_id, fmt, i)) % 499_999)
            try:
                p = _pg_run(node_id=node_id, seed=seed,
                            allowed_formatters=[fmt],
                            allowed_difficulties=allowed_diff,
                            allowed_contexts=allowed_ctx)
                if p is None:
                    continue
                pdict = p if isinstance(p, dict) else (p.model_dump() if hasattr(p, "model_dump") else dict(p))
                pid = pdict.get("problem_id") or f"{node_id}_{seed}_{fmt}"
                # Populate caches the routes read
                _fallback_cache["matatag:" + pid] = pdict
                _fallback_cache["practice_gen_v2:" + pid] = pdict
                _fallback_cache["practice_gen:" + pid] = pdict

                ans = _emit_correct(pdict)
                if ans is None:
                    continue

                # Portal /api/practice/submit (session_id=None ok)
                try:
                    r1 = client.post("/api/practice/submit", json={
                        "selected_answer": ans, "student_id": sid, "session_id": None,
                        "skill_id": node_id, "skeleton_id": pid,
                        "stem": "", "correct_answer": "",
                        "response_time_ms": 5000, "telemetry_flagged": False,
                    }).json().get("is_correct")
                except Exception as e:
                    r1 = f"ERR:{type(e).__name__}"

                # Lab v1 /api/matatag/lab/submit
                try:
                    ans_str = json.dumps(ans) if isinstance(ans, (list, dict)) else str(ans)
                    r2 = client.post("/api/matatag/lab/submit",
                                     params={"skeleton_id": pid, "student_answer": ans_str}).json().get("is_correct")
                except Exception as e:
                    r2 = f"ERR:{type(e).__name__}"

                # Lab v2 /api/matatag/lab/v2/submit
                try:
                    r3 = client.post("/api/matatag/lab/v2/submit",
                                     json={"problem_id": pid, "student_answer": ans}).json().get("is_correct")
                except Exception as e:
                    r3 = f"ERR:{type(e).__name__}"

                verdicts = {"portal": r1, "lab_v1": r2, "lab_v2": r3}
                truthy = {k: v for k, v in verdicts.items() if v is True}
                falsish = {k: v for k, v in verdicts.items() if v is False or (isinstance(v, str) and v.startswith("ERR"))}
                # Divergence: not all 3 agree, OR any returned False for a correct answer
                if any(isinstance(v, str) and "ERR" in v for v in verdicts.values()):
                    findings.append({
                        "node_id": node_id, "seed": seed, "formatter": fmt,
                        "problem_id": pid, "correct_answer": pdict.get("correct_answer"),
                        "submitted_answer": ans, "answer_collection": pdict.get("answer_collection"),
                        "check": "grader_route_error", "severity": "critical",
                        "verdicts": verdicts,
                        "message": f"Grader route raised an error: {verdicts}",
                    })
                elif len(truthy) < 3:
                    findings.append({
                        "node_id": node_id, "seed": seed, "formatter": fmt,
                        "problem_id": pid, "correct_answer": pdict.get("correct_answer"),
                        "submitted_answer": ans, "answer_collection": pdict.get("answer_collection"),
                        "visual_type": pdict.get("visual_type"),
                        "check": "grader_divergence", "severity": "critical",
                        "verdicts": verdicts,
                        "message": f"Correct answer graded as wrong by ≥1 route: {verdicts}",
                    })
            except Exception as e:
                msg = str(e)
                if "emoji_pictorial" in msg and "max_val" in msg:
                    continue
                if "No compatible formatters" in msg:
                    continue
                findings.append({
                    "node_id": node_id, "seed": seed, "formatter": fmt,
                    "check": "pipeline_error", "severity": "high",
                    "error_type": type(e).__name__, "message": msg[:200],
                })
    return findings


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _all_node_ids() -> List[str]:
    from backend.app.practice_gen import registry as r
    return sorted(r.get_all_node_ids())


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--node-ids", default=None)
    p.add_argument("--max-workers", type=int, default=2)  # Lower: each spins TestClient
    p.add_argument("--no-parallel", action="store_true")
    p.add_argument("--samples-per-formatter", type=int, default=3)
    args = p.parse_args(argv)

    if not os.getenv("DATABASE_URL"):
        env_path = ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("DATABASE_URL="):
                    os.environ["DATABASE_URL"] = line.split("=", 1)[1].strip().strip('"')
                    break

    node_ids = [s.strip() for s in args.node_ids.split(",")] if args.node_ids else _all_node_ids()

    print(f"[grader_roundtrip_auditor] Auditing {len(node_ids)} nodes...")
    t0 = time.time()
    all_findings: List[Dict[str, Any]] = []

    if args.no_parallel or len(node_ids) <= 2:
        for nid in node_ids:
            all_findings.extend(_audit_node_grader(nid, args.samples_per_formatter))
    else:
        with ProcessPoolExecutor(max_workers=args.max_workers) as ex:
            futures = {ex.submit(_audit_node_grader, nid, args.samples_per_formatter): nid for nid in node_ids}
            done = 0
            for fut in as_completed(futures):
                try:
                    all_findings.extend(fut.result())
                except Exception as e:
                    all_findings.append({
                        "node_id": futures[fut],
                        "check": "future_exception", "severity": "high",
                        "error_type": type(e).__name__, "message": str(e)[:200],
                    })
                done += 1
                if done % 20 == 0 or done == len(node_ids):
                    print(f"  [{time.time()-t0:.1f}s] {done}/{len(node_ids)} done, {len(all_findings)} findings")

    OUT_JSONL.write_text("\n".join(json.dumps(f, default=str) for f in all_findings) + ("\n" if all_findings else ""))
    summary = _summarize(all_findings)
    OUT_JSON.write_text(json.dumps(summary, indent=2, default=str))
    print()
    print("=" * 80)
    print(f"GRADER ROUND-TRIP AUDIT COMPLETE — {len(all_findings)} findings across {len(node_ids)} nodes ({time.time()-t0:.1f}s)")
    print("=" * 80)
    for cat, count in sorted(summary["by_check"].items(), key=lambda kv: -kv[1]):
        print(f"  {cat:40s} {count:5d}")
    print(f"Outputs: {OUT_JSON}  /  {OUT_JSONL}")
    return 0 if not all_findings else 1


def _summarize(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_check = Counter(f.get("check", "?") for f in findings)
    by_node = Counter(f.get("node_id", "?") for f in findings)
    by_sev = Counter(f.get("severity", "?") for f in findings)
    samples = {}
    for f in findings:
        cat = f.get("check", "?")
        if cat not in samples:
            samples[cat] = f
    return {
        "total_findings": len(findings),
        "by_check": dict(by_check),
        "by_severity": dict(by_sev),
        "top_affected_nodes": by_node.most_common(15),
        "sample_per_check": samples,
    }


if __name__ == "__main__":
    sys.exit(main())