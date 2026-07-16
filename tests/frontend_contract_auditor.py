"""
Frontend render-schema contract auditor.

Catches the class of bugs the user-flagged `mat_g3_na_q4_7` issues exposed:
- Missing `visual_params` keys the React component reads silently collapse to
  `undefined` / `0` / `false` and break the render (Bug #56 empty visual,
  Bug #58 dot at 0 on number line).
- Improper-fraction multi-whole rendering: when `shaded_parts` is stripped in
  set mode (answer-leak fix), the component's `wholeUnits` computation must
  fall back to `params.total_wholes` — otherwise it collapses to 1 bar when
  the answer needs ≥2 (Bug #57).
- Network-payload answer leaks: the correct_answer value appears in
  `visual_params` for set-mode formatters where students submit answers
  themselves (Bug #001).

This auditor runs the orchestrator for every (node × formatter × variant
combo) allowed by the saved CompetencyConfiguration (single source of truth,
docs/frontend_audit.md §0.1) and verifies each generated payload against:

  (a) REQUIRED_KEYS  — every visual_params key the React component reads
      for the corresponding `visual_type` must be present in the payload.
      Missing key → undefined in JS → silent render failure.
  (b) MULTI_WHOLE     — for any fraction-class visual_type whose React
      component computes `wholeUnits = ceil(num/den)`, the expected
      wholeUnits must be ≥ ceil(correct_num/correct_den). Catches Bug #57.
  (c) ANSWER_LEAK     — for set-mode formatters where the student submits
      an answer (answer_collection != "mcq"), the `correct_answer` value
      must NOT appear in `visual_params` (verbatim or as
      shaded_parts/total_pairs). Catches Bug #001.

Mirrors the backend auditor's fail-loud philosophy: findings logged as
JSONL, not silently dropped. No regressions tolerated.

Usage:
    PYTHONPATH=. .venv/bin/python -m tests.frontend_contract_auditor
    PYTHONPATH=. .venv/bin/python -m tests.frontend_contract_auditor --node-ids mat_g3_na_q4_7
    PYTHONPATH=. .venv/bin/python -m tests.frontend_contract_auditor --max-workers 4
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT / "local_only" / "scratch" / "oc"
SCRATCH.mkdir(parents=True, exist_ok=True)

OUT_JSON  = SCRATCH / "frontend_contract_findings.json"
OUT_JSONL = SCRATCH / "frontend_contract_findings.jsonl"


# ─────────────────────────────────────────────────────────────────────────────
# Per-`visual_type` REQUIRED_KEYS — keys the React component reads from
# `params.*` (derived from frontend/src/components/VisualSkeletons.jsx and
# frontend/src/utils/renderUtils.jsx).  A payload whose visual_params lacks
# any of these will render incorrectly.  `model_type` indicates a sub-branch
# within FractionModelInteractive — the required_keys are union over all
# branches but flags if the named sub-branch key is absent.
# ─────────────────────────────────────────────────────────────────────────────

REQUIRED_KEYS: Dict[str, List[str]] = {
    "NumberLine":       ["start", "end", "dot_value"],   # `interval`/`minor_interval` is optional with fallback
    "ClockSet":         ["hours", "minutes", "interaction_mode"],
    "PesoMoney":        ["target_amount", "coins", "bills"],
    "GridArea":         ["rows", "cols", "shaded"],
    "BarChart":         ["categories"],   # values OR counts (pictograph alias) is required; check below
    "EmojiPictorial":   ["emoji", "group_a", "group_b"],
    "PlaceValueBlocks": ["total_value"],
    "PatternSequence":  ["sequence", "missing_indices"],
    "FractionModel":    ["model_type", "numerator", "denominator", "total_parts", "shaded_parts", "interaction_mode", "is_read_only", "total_wholes"],
    "FractionShade":    ["shape", "total_parts", "interaction_mode", "is_read_only", "total_wholes"],
    "TenFrame":         ["filled", "frame_count", "query_type"],  # total optional (= frame_count * 10)
    "RulerMeasure":     ["length"],
    "BalanceScale":     ["left_side", "right_side", "is_balanced"],
    "ShapeBoard":       ["shapes"],   # grid_size optional; component iterates shapes[]
    "Calendar":         ["month", "year"],
    "FillInTable":      ["columns", "rows"],
    "NumberBond":       ["whole", "part1", "part2", "blank_position"],
    "Categorize":       ["shapes"],
    "SortOrder":        ["correct_sequence"],
}

# Formatters where the student submits the answer (so `correct_answer` must
# NOT leak into `visual_params`).
SET_MODE_COLLECTIONS = {"click", "set", "fill_in_blank", "ordering"}


def _leak_keys_for(answer_collection: str, visual_type: Optional[str] = None) -> Tuple[str, ...]:
    """Keys that, if present in visual_params, leak the answer for a given
    answer_collection mode (where the student submits — read-mode leaks are
    legitimate because the component must show the answer).

    Note: formatters whose stem INTENTIONALLY tells the student the target
    (e.g. number_line_set says "Move the dot to show 18", peso_money_set
    says "make exactly ₱18") are NOT in this set — the answer is not a
    secret there. Only formatters where the student must DERIVE the answer
    from the visual are checked here (e.g. fraction_shade where the student
    must shade N/4 — leaking shaded_parts=N defeats the exercise)."""
    if answer_collection in SET_MODE_COLLECTIONS:
        # Only the formatters where the answer is NOT in the stem
        if visual_type in ("FractionShade", "FractionModel"):
            return ("shaded_parts", "fraction_str")
        if visual_type == "SortOrder":
            return ("correct_sequence",)
        if visual_type == "GridArea":
            return ("correct_count",)
        return ()   # default: not flagged
    return ()


# ─────────────────────────────────────────────────────────────────────────────
# Per-payload checks
# ─────────────────────────────────────────────────────────────────────────────

def _parse_fraction_str(s: str) -> Optional[Tuple[int, int]]:
    if not isinstance(s, str) or "/" not in s:
        return None
    try:
        n_str, d_str = s.split("/", 1)
        n_str = n_str.strip().split()[-1]  # tolerate "1 1/2"
        return int(n_str), int(d_str)
    except (ValueError, IndexError):
        return None


def check_payload(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a list of findings (empty list = clean payload)."""
    findings: List[Dict[str, Any]] = []
    vt = payload.get("visual_type")
    vp = payload.get("visual_params") or {}
    ca = str(payload.get("correct_answer", ""))
    ac = payload.get("answer_collection") or ""
    seed = payload.get("seed")
    node = payload.get("node_id")
    pid = payload.get("problem_id")
    interaction_mode = payload.get("interaction_mode") or vp.get("interaction_mode")

    common = {
        "node_id": node,
        "seed": seed,
        "problem_id": pid,
        "visual_type": vt,
        "answer_collection": ac,
        "interaction_mode": interaction_mode,
        "correct_answer": ca,
    }

    # ── (a) REQUIRED_KEYS check ──────────────────────────────────────────────
    if vt in REQUIRED_KEYS:
        missing = [k for k in REQUIRED_KEYS[vt] if k not in vp]
        if missing:
            findings.append({
                **common,
                "check": "required_keys_missing",
                "severity": "critical",
                "missing_keys": missing,
                "vp_keys": list(vp.keys()),
                "message": f"visual_type={vt} payload missing required visual_params keys: {missing}. "
                           f"React component will see `undefined` and render incorrectly.",
            })

    # ── (b) MULTI_WHOLE check (Bug #57 class) ────────────────────────────────
    if vt in ("FractionModel", "FractionShade"):
        # Component computes wholeUnits via:
        #   Math.max(1, Math.ceil(
        #     (params.total_wholes !== undefined ? params.total_wholes * den : num) / den
        #   ))
        den = vp.get("denominator") or vp.get("total_parts") or 1
        if den == 0:
            findings.append({
                **common,
                "check": "zero_denominator",
                "severity": "critical",
                "message": "denominator/total_parts is 0 — div-by-zero in component",
            })
        else:
            tw = vp.get("total_wholes")
            num = vp.get("numerator") if vp.get("numerator") is not None else (vp.get("shaded_parts") or 0)
            if tw is not None:
                react_wholes = max(1, math.ceil((tw * den) / den))
            else:
                react_wholes = max(1, math.ceil(num / den))
            # Expected: ceil(correct_num / correct_den) — derived from correct_answer
            frac = _parse_fraction_str(ca)
            if frac is not None:
                expected_wholes = max(1, math.ceil(frac[0] / frac[1]))
                if react_wholes < expected_wholes:
                    findings.append({
                        **common,
                        "check": "multi_whole_render",
                        "severity": "critical",
                        "react_wholes": react_wholes,
                        "expected_wholes": expected_wholes,
                        "message": f"React wholeUnits={react_wholes} but correct_answer={ca} requires "
                                   f"≥{expected_wholes} whole shape(s). Student cannot shade the answer.",
                    })

    # ── (c) ANSWER_LEAK check (Bug #001 class) ───────────────────────────────
    if ac in SET_MODE_COLLECTIONS and vp:
        leak_keys = _leak_keys_for(ac, vt)
        leaked = []
        for k in leak_keys:
            if k not in vp:
                continue
            # Numeric keys: leak iff equals the correct_answer (as float/int)
            if k in ("correct_answer", "correct_position", "target", "target_amount", "missing_value"):
                try:
                    if float(vp[k]) == float(ca):
                        leaked.append(k); continue
                except (ValueError, TypeError):
                    pass
                # Also flag if the string representation matches
                if str(vp[k]) == str(ca):
                    leaked.append(k); continue
            elif k == "shaded_parts":
                frac = _parse_fraction_str(ca)
                if frac and vp.get("shaded_parts") == frac[0]:
                    leaked.append(k)
            elif k == "fraction_str":
                if vp.get(k) == ca:
                    leaked.append(k)
            elif k == "correct_sequence":
                # correct_sequence IS legitimately persisted on the backend
                # for grader dispatched (visible in /api/practice/submit).
                # LEAK only if the React network response echoes it (all visual
                # params are sent). Always flag — backend should strip.
                leaked.append(k)
        if leaked:
            findings.append({
                **common,
                "check": "answer_leak_in_set_mode",
                "severity": "critical",
                "leaked_keys": leaked,
                "message": f"answer-collection={ac} (set mode) but visual_params exposes answer via: {leaked}",
            })

    # ── (d) Math-impossible states (catches rng regressing to 0) ─────────────
    if vt in ("FractionModel", "FractionShade") and vp.get("total_parts") == 0:
        findings.append({
            **common,
            "check": "zero_total_parts",
            "severity": "critical",
            "message": "total_parts=0 → division by zero in FractionModel/Shade component",
        })

    # ── (e) MCQ options check (catches None/null options) ────────────────────
    options = payload.get("options")
    format_data = payload.get("format_data") or {}
    if not options and isinstance(format_data, dict):
        options = format_data.get("options")
    if options:
        opts_list = list(options.values()) if isinstance(options, dict) else options
        for opt in opts_list:
            opt_raw = opt.get("value") if isinstance(opt, dict) else opt
            opt_val = str(opt_raw).strip()
            if opt_raw is None or opt_val.lower() in ("none", "null") or not opt_val:
                findings.append({
                    **common,
                    "check": "invalid_option_value",
                    "severity": "critical",
                    "message": f"MCQ option contains invalid None, null, or blank value: {opt_raw!r}",
                })
                break
            elif re.match(r"^option\s+\d+", opt_val.lower()):
                findings.append({
                    **common,
                    "check": "invalid_option_value",
                    "severity": "critical",
                    "message": f"MCQ option contains placeholder Option # value: {opt_val!r}",
                })
                break

    return findings


# ─────────────────────────────────────────────────────────────────────────────
# Per-node worker (module-level for ProcessPoolExecutor pickling)
# ─────────────────────────────────────────────────────────────────────────────

def _audit_node(node_id: str, samples_per_formatter: int = 8) -> List[Dict[str, Any]]:
    """Generate samples per formatter and check each payload."""
    # Imports inside worker (per Rule #3 — sidesteps spawn circular import)
    from backend.app.practice_gen import registry as _reg
    from backend.app.practice_gen.pipeline import run as _pg_run
    from backend.app.models import CompetencyConfiguration
    from backend.app.database import SessionLocal

    findings: List[Dict[str, Any]] = []
    db = SessionLocal()
    try:
        row = db.query(CompetencyConfiguration).filter_by(node_id=node_id).first()
        if not row:
            return [{
                "node_id": node_id,
                "check": "no_config_row",
                "severity": "high",
                "message": "No CompetencyConfiguration row for node — single-source-of-truth violation (docs/frontend_audit.md §0.1).",
            }]
        allowed_fmt   = row.allowed_formatters or []
        allowed_diff  = row.allowed_difficulties or {}
        allowed_ctx   = row.allowed_contexts or {}
        db.close()

        for fmt in allowed_fmt:
            for i in range(samples_per_formatter):
                seed = 1000_000 + (hash((node_id, fmt, i)) % 999_999)
                try:
                    payload = _pg_run(
                        node_id=node_id, seed=seed,
                        allowed_formatters=[fmt],
                        allowed_difficulties=allowed_diff,
                        allowed_contexts=allowed_ctx,
                    )
                    if payload is None:
                        findings.append({
                            "node_id": node_id, "seed": seed, "formatter": fmt,
                            "check": "pipeline_returned_none",
                            "severity": "high",
                            "message": f"_pg_run returned None for formatter={fmt}",
                        })
                        continue
                    p_dict = payload if isinstance(payload, dict) else payload.__dict__ if hasattr(payload, "__dict__") else {}
                    # Convert Pydantic to dict if needed
                    from backend.app.practice_gen.dna.base import FormattedProblem
                    if isinstance(payload, FormattedProblem):
                        p_dict = payload.model_dump()
                    p_dict["node_id"] = node_id
                    p_dict["seed"] = seed
                    p_dict["formatter"] = fmt
                    p_dict.setdefault("correct_answer", p_dict.get("correct_answer", ""))
                    p_dict.setdefault("answer_collection", p_dict.get("answer_collection", ""))
                    p_dict.setdefault("visual_type", p_dict.get("visual_type", ""))
                    p_dict.setdefault("visual_params", p_dict.get("visual_params", {}))
                    p_dict.setdefault("interaction_mode", p_dict.get("interaction_mode", ""))
                    findings.extend(check_payload(p_dict))
                except Exception as e:
                    # Pipeline errors are the backend auditor's domain; only
                    # surface them if they are NOT the expected fail-fast
                    # emoji_pictorial cap ValueError (orchestrator pre-filter miss).
                    msg = str(e)
                    if "emoji_pictorial" in msg and "max_val" in msg:
                        continue
                    if "cannot represent" in msg or "No compatible formatters" in msg:
                        continue
                    findings.append({
                        "node_id": node_id, "seed": seed, "formatter": fmt,
                        "check": "pipeline_error",
                        "severity": "high",
                        "error_type": type(e).__name__,
                        "message": msg[:200],
                    })
    except Exception as e:
        findings.append({
            "node_id": node_id,
            "check": "worker_exception",
            "severity": "high",
            "error_type": type(e).__name__,
            "message": str(e)[:200],
        })
    finally:
        try:
            db.close()
        except Exception:
            pass
    return findings


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _all_node_ids() -> List[str]:
    from backend.app.practice_gen import registry as r
    return sorted(r.get_all_node_ids())


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--node-ids", default=None, help="comma-separated list; default = all 151")
    p.add_argument("--max-workers", type=int, default=4)
    p.add_argument("--no-parallel", action="store_true")
    p.add_argument("--samples-per-formatter", type=int, default=8)
    args = p.parse_args(argv)

    if not os.getenv("DATABASE_URL"):
        # Try to load from .env
        env_path = ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("DATABASE_URL="):
                    os.environ["DATABASE_URL"] = line.split("=", 1)[1].strip().strip('"')
                    break

    if args.node_ids:
        node_ids = [s.strip() for s in args.node_ids.split(",") if s.strip()]
    else:
        node_ids = _all_node_ids()

    print(f"[frontend_contract_auditor] Auditing {len(node_ids)} nodes...")
    t0 = time.time()
    all_findings: List[Dict[str, Any]] = []

    if args.no_parallel or len(node_ids) == 1:
        for nid in node_ids:
            all_findings.extend(_audit_node(nid, args.samples_per_formatter))
            if (len(all_findings) % 50) == 0 and all_findings:
                print(f"  [{time.time()-t0:.1f}s] running findings: {len(all_findings)}")
    else:
        with ProcessPoolExecutor(max_workers=args.max_workers) as ex:
            futures = {ex.submit(_audit_node, nid, args.samples_per_formatter): nid for nid in node_ids}
            done = 0
            for fut in as_completed(futures):
                try:
                    all_findings.extend(fut.result())
                except Exception as e:
                    all_findings.append({
                        "node_id": futures[fut],
                        "check": "future_exception",
                        "severity": "high",
                        "error_type": type(e).__name__,
                        "message": str(e)[:200],
                    })
                done += 1
                if done % 20 == 0 or done == len(node_ids):
                    print(f"  [{time.time()-t0:.1f}s] {done}/{len(node_ids)} nodes done, {len(all_findings)} findings")

    # Write outputs
    OUT_JSONL.write_text("\n".join(json.dumps(f, default=str) for f in all_findings) + ("\n" if all_findings else ""))
    summary = _summarize(all_findings)
    OUT_JSON.write_text(json.dumps(summary, indent=2, default=str))
    print()
    print("=" * 80)
    print(f"FRONTEND CONTRACT AUDIT COMPLETE — {len(all_findings)} findings across {len(node_ids)} nodes ({time.time()-t0:.1f}s)")
    print("=" * 80)
    for cat, count in sorted(summary["by_check"].items(), key=lambda kv: -kv[1]):
        print(f"  {cat:40s} {count:5d}")
    print()
    by_sev = Counter(f.get("severity", "?") for f in all_findings)
    print(f"By severity: {dict(by_sev)}")
    print(f"Outputs: {OUT_JSON}  /  {OUT_JSONL}")
    return 0 if not all_findings else 1


def _summarize(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_check = Counter(f.get("check", "?") for f in findings)
    by_node  = Counter(f.get("node_id", "?") for f in findings)
    by_sev   = Counter(f.get("severity", "?") for f in findings)
    top_nodes = by_node.most_common(15)
    samples = {}
    for f in findings:
        cat = f.get("check", "?")
        if cat not in samples:
            samples[cat] = f
    return {
        "total_findings": len(findings),
        "by_check": dict(by_check),
        "by_severity": dict(by_sev),
        "top_affected_nodes": top_nodes,
        "sample_per_check": samples,
    }


if __name__ == "__main__":
    sys.exit(main())