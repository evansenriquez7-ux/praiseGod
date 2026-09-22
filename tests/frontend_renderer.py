"""Python bridge to the same browserless renderer used by the frontend evidence suite.

CONCURRENCY, AND THE TWO DEFECTS THAT LIVED HERE
------------------------------------------------
Six call sites funnel through `attach_rendered_visual_descriptions`, including BOTH §5's
`validate_judgment` and §6F's `validate_capability` freshness pass. Until 2026-09-22 this
module wrote its corpus and its result to ONE fixed pair of paths under `SCRATCH`, with no
pid, no uuid and no lock, and two defects rode on that:

  * the LOUD one -- two concurrent runs overwrite each other's files, the id sets disagree,
    and the `set(active) != set(by_id)` guard below raises. Measured symptom: §5 aborting
    with "renderer returned active evidence for [~400 packets]".
  * the SILENT one, which is why a recorded figure can move with no crash at all. `case_id`
    was `f"packet-{index}-seed-{seed}"` and OMITTED `node_id`, though `node_id` is right
    there and is even stored inside the case. Two different nodes' packets therefore both
    produced `packet-0-seed-11`. When two processes collided, the id SETS could coincide
    while the rendered structure belonged to the other process -- the guard passed, and one
    run attached the other run's visual evidence to its own samples. Measured cost: §6F
    reported 55 findings under concurrent load on a tree that had 61, against 61 on three
    clean runs. No crash and no warning.

    CORRECTED 2026-09-22: an earlier draft of this docstring also cited "§5 reported 1253
    where it has 1252" as a second symptom. That figure was MISATTRIBUTED and is not this
    defect. `run_all._stage_judgment_reviews_5` appends one aggregate finding the module's
    own CLI never emits, so 1252 (module) and 1253 (stage) are both correct for their entry
    point. Quote the entry point alongside any §5 figure.

Both halves are fixed here, and both are needed. A unique path alone leaves the colliding
id space in place for any future caller that shares a directory; `node_id` in `case_id`
alone still lets two runs trample one file. Fixing only the loud half keeps the quiet half
hidden behind it.

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
1. **Uniqueness is per (pid, uuid4), not a lock.** Two invocations cannot share a directory,
   but nothing serialises them: concurrent Node processes still compete for CPU, and this
   module makes no claim about how long a render takes under load. It removes cross-talk,
   not contention.
2. **A failed render leaves its directory behind, deliberately.** Cleanup runs only on the
   success path so the corpus and result that produced a failure survive for diagnosis; the
   raised error names the directory. The cost is that an aborted session leaks directories
   under `SCRATCH`, which is scratch space and outside `INPUT_ROOTS`.
3. **`case_id` uniqueness rests on `(node_id, index, seed)` being distinct WITHIN one call.**
   That is guaranteed here because `index` is the row's position in the batch, so it is
   unique on its own; `node_id` and `seed` are carried for cross-process distinctness and
   for legibility in the renderer's own findings strings. A future caller that rebuilt
   `case_id` without `index` would be relying on the weaker pair.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import uuid
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
            # node_id FIRST, and never omitted: two processes rendering different
            # nodes must not be able to mint the same id. See the module docstring.
            node_id = sample.get("node_id", "packet")
            case_id = f"{node_id}-packet-{index}-seed-{sample.get('seed')}"
            case = {
                "case_id": case_id,
                "node_id": node_id,
                "seed": sample.get("seed"),
                "formatter": sample.get("formatter"),
                "visual_type": visual_type,
                "visual_params": params,
            }
            visual_cases.append(case)
            by_id[case_id] = sample

    if visual_cases:
        # One directory per INVOCATION. Two concurrent callers cannot share a file at
        # all, so neither the loud overwrite nor the silent cross-talk is reachable.
        run_dir = SCRATCH / f"run-{os.getpid()}-{uuid.uuid4().hex}"
        run_dir.mkdir(parents=True, exist_ok=False)
        corpus_path = run_dir / "corpus.json"
        result_path = run_dir / "result.json"
        corpus_path.write_text(json.dumps({"cases": visual_cases}, indent=2) + "\n", encoding="utf-8")
        command = [
            "node", "--import", "tsx",
            str(FRONTEND / "src" / "staticRenderCli.jsx"),
            str(corpus_path), str(result_path),
        ]
        proc = subprocess.run(command, cwd=FRONTEND, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(
                f"render-derived packet evidence failed (exit {proc.returncode}); "
                f"corpus and result kept at {run_dir}:\n"
                f"{proc.stdout}{proc.stderr}"
            )
        result = json.loads(result_path.read_text(encoding="utf-8"))
        active = {
            outcome["case_id"]: outcome for outcome in result.get("outcomes", [])
            if outcome.get("mode") == "active"
        }
        if set(active) != set(by_id):
            raise RuntimeError(
                f"renderer returned active evidence for {sorted(active)}, "
                f"expected {sorted(by_id)}; kept at {run_dir}"
            )
        for case_id, sample in by_id.items():
            sample["visual_render"] = {
                "visual_type": sample["visual_type"],
                "renderer_input_digest": _renderer_input_digest(sample),
                "description": active[case_id]["description"],
            }
        # Success only. A failed run keeps its directory for diagnosis (limitation 2).
        shutil.rmtree(run_dir)

    for sample in rows:
        sample.pop("_visual_params", None)
    return rows
