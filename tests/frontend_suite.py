"""
Build and execute the browserless frontend render evidence (§12).

The suite derives its corpus from production student-path obligations and renders the
React components with ``renderToStaticMarkup`` under Vitest/jsdom.  It writes a consumed
artifact only after the JavaScript suite exits zero, binding that evidence to the same
working-tree input digest used by mutation proofs.

Known limits
------------
* The current practice obligation graph reaches 15 of renderUtils' 20 registrations.
  The five legacy/dead registrations are recorded in the artifact, not called covered.
* jsdom has no layout engine. NumberLine and BarChart pointer-drag geometry remains
  unproven; their non-pointer paths and rendered structures are the browserless surface.
* Static descriptions quantify emitted markup, but cannot prove crowding, overlap,
  colour contrast, or real touch-target size.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
REPORT = ROOT / "validation_reports" / "phase2_hardening" / "frontend_static_render.json"
SCRATCH = ROOT / "local_only" / "scratch" / "frontend_static_render"


def _seed(key: str) -> int:
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:4], "big") & 0x7FFFFFFF


def _visual_contract() -> Dict[str, Dict[str, Any]]:
    sys.path.insert(0, str(ROOT))
    from tests.frontend_contract_auditor import visual_contract

    return visual_contract()


def build_corpus() -> Dict[str, Any]:
    """One real student-path payload for every reachable visual formatter."""
    sys.path.insert(0, str(ROOT))
    from backend.app.practice_gen.pipeline import run
    from tests.obligation_manifest import enumerate_obligations

    obligations, _ = enumerate_obligations()
    triples: Dict[Tuple[str, str, str], Any] = {}
    for obligation in obligations:
        triples.setdefault(
            (obligation.node_id, obligation.dna, obligation.formatter), obligation
        )

    contract = _visual_contract()
    by_payload_class: Dict[Tuple[Any, ...], Dict[str, Any]] = {}
    for obligation in triples.values():
        seed = _seed(obligation.key())
        problem = run(
            obligation.node_id,
            difficulty_profile=dict(obligation.assignment),
            formatter=obligation.formatter,
            seed=seed,
            is_student_path=True,
            forced_dna=obligation.dna,
        )
        if not problem.get("is_visual"):
            continue
        visual_type = problem.get("visual_type")
        visual_params = problem.get("visual_params")
        if not visual_type or not isinstance(visual_params, dict):
            raise RuntimeError(
                f"{obligation.key()} seed {seed}: visual student-path problem omitted "
                "visual_type or a dict visual_params payload"
            )
        conditional_present = tuple(
            key for key in contract.get(visual_type, {}).get("conditional", ())
            if key in visual_params
        )
        payload_class = (
            obligation.formatter,
            visual_type,
            conditional_present,
            problem.get("answer_collection"),
            problem.get("interaction_mode"),
        )
        by_payload_class.setdefault(
            payload_class,
            {
                "case_id": f"{obligation.formatter}:{obligation.node_id}:{seed}",
                "node_id": obligation.node_id,
                "dna": obligation.dna,
                "formatter": obligation.formatter,
                "seed": seed,
                "visual_type": visual_type,
                "visual_params": visual_params,
                "correct_answer": problem.get("correct_answer"),
                "answer_collection": problem.get("answer_collection"),
                "interaction_mode": problem.get("interaction_mode"),
            },
        )

    cases = sorted(by_payload_class.values(), key=lambda row: row["case_id"])
    produced = sorted({row["visual_type"] for row in cases})
    registered = sorted(contract)
    return {
        "schema_version": 1,
        "cases": cases,
        "production_visual_types": produced,
        "registered_visual_types": registered,
        "unreachable_renderer_registrations": sorted(set(registered) - set(produced)),
    }


def run_suite(report_path: Path = REPORT) -> Dict[str, Any]:
    from backend.app.practice_gen.validation.mutation_proof import input_digest

    SCRATCH.mkdir(parents=True, exist_ok=True)
    corpus_path = SCRATCH / "corpus.json"
    result_path = SCRATCH / "static_render_result.json"
    vitest_result_path = SCRATCH / "vitest_result.json"
    answer_result_path = SCRATCH / "answer_roundtrip_result.json"
    corpus = build_corpus()
    corpus_path.write_text(json.dumps(corpus, indent=2) + "\n", encoding="utf-8")
    result_path.unlink(missing_ok=True)
    vitest_result_path.unlink(missing_ok=True)
    answer_result_path.unlink(missing_ok=True)

    render_command = [
        "node", "--import", "tsx",
        str(FRONTEND / "src" / "staticRenderCli.jsx"),
        str(corpus_path), str(result_path),
    ]
    render_proc = subprocess.run(render_command, cwd=FRONTEND, text=True)
    if render_proc.returncode != 0:
        raise RuntimeError(
            f"frontend renderer failed with exit {render_proc.returncode}; "
            "no evidence artifact was written"
        )

    env = dict(os.environ)
    env["PGEN_STATIC_RENDER_CORPUS"] = str(corpus_path)
    env["PGEN_STATIC_RENDER_RESULT"] = str(vitest_result_path)
    env["PGEN_ANSWER_ROUNDTRIP_RESULT"] = str(answer_result_path)
    command = [
        "npm", "exec", "--prefix", str(FRONTEND), "--", "vitest", "run",
        str(FRONTEND / "src" / "static_render.test.jsx"),
        str(FRONTEND / "src" / "answerRoundtrip.test.jsx"),
        "--environment", "jsdom", "--root", str(FRONTEND),
    ]
    proc = subprocess.run(command, cwd=ROOT, env=env, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"frontend static-render suite failed with exit {proc.returncode}; "
            "no evidence artifact was written"
        )
    if not result_path.exists() or not vitest_result_path.exists() or not answer_result_path.exists():
        raise RuntimeError("frontend suite exited zero but wrote incomplete results; refusing false green")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("cases_executed") != len(corpus["cases"]):
        raise RuntimeError(
            f"frontend suite reported {result.get('cases_executed')} cases, expected "
            f"{len(corpus['cases'])}"
        )

    from backend.app.services.scoring import answers_match

    emissions = json.loads(answer_result_path.read_text(encoding="utf-8")).get("emissions")
    expected_interactive = [
        row for row in corpus["cases"]
        if row.get("interaction_mode") == "set" or row.get("answer_collection") != "mcq"
    ]
    expected_interactive_ids = sorted(row["case_id"] for row in expected_interactive)
    actual_emission_ids = sorted(
        row.get("case_id") for row in emissions or [] if isinstance(row, dict)
    )
    if (not isinstance(emissions, list)
            or len(actual_emission_ids) != len(set(actual_emission_ids))
            or actual_emission_ids != expected_interactive_ids):
        raise RuntimeError(
            "frontend answer suite case coverage disagrees with the production corpus: "
            f"recorded={actual_emission_ids}, expected={expected_interactive_ids}"
        )
    disagreements = [
        row for row in emissions
        if not answers_match(row.get("emitted_answer"), row.get("correct_answer"))
    ]
    if disagreements:
        for row in disagreements:
            print(
                "FAIL frontend_answer_roundtrip_13: "
                f"{row['case_id']} seed {row['seed']} emitted "
                f"{row.get('emitted_answer')!r}, keyed {row.get('correct_answer')!r}",
                file=sys.stderr,
            )
        raise RuntimeError(
            f"frontend_answer_roundtrip_13 found {len(disagreements)} emitted/key disagreement(s)"
        )

    artifact = {
        **result,
        "source_input_digest": input_digest(),
        "registered_visual_types": corpus["registered_visual_types"],
        "unreachable_renderer_registrations": corpus["unreachable_renderer_registrations"],
        "corpus_rule": (
            "one real forced-student-path payload per reachable formatter x conditional-key "
            "presence x interaction/answer mode class"
        ),
        "answer_roundtrips": emissions,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser(description="Build browserless frontend render evidence")
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    artifact = run_suite(args.report)
    print(
        f"PASS frontend_static_render_12: {artifact['cases_executed']} real payloads; "
        f"{len(artifact['production_visual_types'])} production visual types; "
        f"artifact {args.report.relative_to(ROOT)}"
    )
    if artifact["unreachable_renderer_registrations"]:
        print(
            "  NOT COVERED (unreachable registrations): "
            + ", ".join(artifact["unreachable_renderer_registrations"])
        )
    print("Praise God — the React render evidence is executable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
