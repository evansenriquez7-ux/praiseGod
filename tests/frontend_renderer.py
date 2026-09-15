"""Python bridge to the same browserless renderer used by the frontend evidence suite."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
SCRATCH = ROOT / "local_only" / "scratch" / "frontend_packet_render"


def _renderer_input_digest(sample: Dict[str, Any]) -> str:
    payload = {
        "visual_type": sample.get("visual_type"),
        "visual_params": sample.get("_visual_params"),
        "renderer": "frontend/src/staticRenderEvidence.jsx:v1",
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def attach_rendered_visual_descriptions(samples: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Attach render-derived evidence to visual samples in one Node invocation.

    ``_visual_params`` is an internal handoff and is always removed. The packet receives
    countable structure parsed from React's emitted markup, never a payload paraphrase.
    """
    rows = [dict(sample) for sample in samples]
    visual_cases = []
    by_id: Dict[str, Dict[str, Any]] = {}
    for index, sample in enumerate(rows):
        params = sample.get("_visual_params")
        visual_type = sample.get("visual_type")
        if visual_type or params is not None:
            if not visual_type or not isinstance(params, dict):
                raise RuntimeError(
                    f"sample index {index} seed {sample.get('seed')}: visual evidence "
                    "requires visual_type and dict visual_params"
                )
            case_id = f"packet-{index}-seed-{sample.get('seed')}"
            case = {
                "case_id": case_id,
                "node_id": sample.get("node_id", "packet"),
                "seed": sample.get("seed"),
                "formatter": sample.get("formatter"),
                "visual_type": visual_type,
                "visual_params": params,
            }
            visual_cases.append(case)
            by_id[case_id] = sample

    if visual_cases:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        corpus_path = SCRATCH / "corpus.json"
        result_path = SCRATCH / "result.json"
        corpus_path.write_text(json.dumps({"cases": visual_cases}, indent=2) + "\n", encoding="utf-8")
        result_path.unlink(missing_ok=True)
        command = [
            "node", "--import", "tsx",
            str(FRONTEND / "src" / "staticRenderCli.jsx"),
            str(corpus_path), str(result_path),
        ]
        proc = subprocess.run(command, cwd=FRONTEND, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(
                f"render-derived packet evidence failed (exit {proc.returncode}):\n"
                f"{proc.stdout}{proc.stderr}"
            )
        result = json.loads(result_path.read_text(encoding="utf-8"))
        active = {
            outcome["case_id"]: outcome for outcome in result.get("outcomes", [])
            if outcome.get("mode") == "active"
        }
        if set(active) != set(by_id):
            raise RuntimeError(
                f"renderer returned active evidence for {sorted(active)}, expected {sorted(by_id)}"
            )
        for case_id, sample in by_id.items():
            sample["visual_render"] = {
                "visual_type": sample["visual_type"],
                "renderer_input_digest": _renderer_input_digest(sample),
                "description": active[case_id]["description"],
            }

    for sample in rows:
        sample.pop("_visual_params", None)
    return rows
