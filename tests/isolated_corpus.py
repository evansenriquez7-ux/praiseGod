"""
Isolated review corpora — proving the custody gates without the live corpora.

WHY THIS EXISTS
---------------
Fifteen of the harness's mutations planted their violation directly into
`validation_reports/judgment/` or `validation_reports/attestation/` — genuine,
agent-authored review files. That worked, and it cost three things:

  1. **The proofs were not Phase-1 admissible.** Since 2026-09-12 §8 counts an assertion
     proven only when an EXECUTED mutation left a proof record bound to the working-tree
     bytes it ran against (`mutation_proof.INPUT_ROOTS`). A mutation that edits an
     agent-authored corpus is bound to files Phase 1 may not read and the fingerprint does
     not cover, so its proof was recorded and REJECTED for Phase 1 — correctly.
  2. **They could not run on a fresh clone.** A new grade's agent cannot prove §5 works
     before filing a single review, which is exactly backwards: the gate should be proved
     before the queue it polices fills up (Scaling Mandate 5).
  3. **They were hostage to the live queue.** `mcq_reviewed_without_options` is a correct
     plant against a check whose live baseline is red by construction, so the runner
     refused to score it — it sat unprovable while the re-review queue stayed open.

This module builds a small, VALID review corpus in a temporary directory, from live
renders through the production pipeline, and runs the real validator entry points against
it. A clean build must produce ZERO findings — that is the positive control the plan asks
for, and it runs on every invocation, before any plant. Then one named violation is
planted and the same entry point must report it.

HOW A MUTATION USES IT
----------------------
`PLANT` below is a module constant. The mutation harness plants a violation name into it
and runs this module; the baseline run (PLANT = None) is the clean control. Both runs
execute the same command, which is what lets `baseline_must_not_contain` discriminate. The
edited file is `tests/isolated_corpus.py` — inside the fingerprinted input set — so the
resulting proof is Phase-1 admissible.

WHAT THIS IS NOT
----------------
Not a replacement for the live corpora. The reviews built here are SYNTHETIC and are never
filed as genuine reviews; they exist only under a temporary directory and only for the
length of one run. Whether the live corpus is fresh, complete and honest remains §5's and
§6F-§6H's Phase 2 job on the real files. This module proves the GATES fire; the Phase 2
run proves the CORPUS holds.

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
* The entry point is called with `get_all_node_ids` narrowed to the corpus nodes, the same
  way every other validator takes `--node-ids`. The tree-wide walk itself is therefore not
  exercised here; it is exercised by the Phase 2 run on the real corpus.
* The corpus nodes are the first `CORPUS_SIZE` registered node ids in sorted order —
  derived from the registry, never a hand-picked list, so a new grade is covered by the
  same code. A node that cannot render enough distinct seeds is a loud failure here, not a
  skip.
* A clean control proving zero findings shows the corpus satisfies the gates; it does not
  show the gates are complete. That is what the planted violations are for, one per gate.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.practice_gen.registry import get_all_node_ids, get_node_info  # noqa: E402
from backend.app.practice_gen.validation import validate_capability as cap  # noqa: E402
from backend.app.practice_gen.validation import validate_judgment as jud  # noqa: E402
from backend.app.practice_gen.validation.judgment_packets import _render_sample  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# THE PLANT SLOT. The mutation harness rewrites this one line.
# ─────────────────────────────────────────────────────────────────────────────
PLANT: Optional[str] = None

# More than `_MAX_NODES_PER_REVIEWER` (25), because the plurality gates can only be
# planted on a corpus large enough to exceed one blind batch. Read from the validator
# rather than restated, so tightening the threshold cannot silently make the plant a no-op.
CORPUS_SIZE = jud._MAX_NODES_PER_REVIEWER + 1

SEEDS = (11, 23, 42, 57, 64)

# Distinct sentence frames. `_rationale_skeleton` strips node IDs, quoted spans and
# digits, so two rationales collapse together unless their FRAME differs. With
# `_MAX_SKELETON_CLUSTER` at 3, a corpus of 26 nodes needs at least 9 frames per finding;
# twelve leaves headroom and keeps the clean control's margin visible.
_FRAMES = (
    "The sampled items put this competency's own demand in front of the pupil directly, "
    "and the harder draws ask more of the same skill rather than of some unrelated one.",
    "Across the seeds shown, what varies is the load this competency names; nothing in the "
    "sample reaches past the quarter's stated scope.",
    "Every item read here stays inside the stated boundary, and the range that grows is the "
    "one the curriculum wording identifies.",
    "The wording of each stem matches what the competency asks a learner to do, and no "
    "sample requires an operation introduced after this node.",
    "Sampled at several seeds, the demand rises along the axis this node is about and "
    "along no other, which is what the alignment item asks.",
    "Nothing in these items assumes vocabulary from a later quarter, and the structure "
    "stays at the length a learner at this stage can hold.",
    "The items exercise the named skill in more than one surface form, so the sample is "
    "not a single template repeated at different magnitudes.",
    "What a learner must do here is stated plainly in each stem, and the quantities stay "
    "within the band this competency sets out.",
    "Read end to end, the sample covers the competency's clauses rather than only the "
    "easiest of them, and each draw is answerable from what it shows.",
    "The contextual dressing changes between draws while the mathematical demand does not, "
    "which is the invariance this item is checking for.",
    "Each stem asks for exactly one thing, and that thing is what the competency wording "
    "names; the distractors stay in the same representation as the key.",
    "The progression across seeds is in the competency's own dimension, and the smallest "
    "and largest draws both stay answerable at this grade.",
)

VIOLATIONS = (
    # §5
    "stale_stem", "stale_answer_same_key", "options_dropped", "schema_incomplete",
    "fabricated_quote", "verbatim_rationale", "template_skeleton", "single_reviewer",
    # §6F/§6G/§6H
    "attestation_stale", "attestation_answer_drift", "attestation_option_drift",
    "attester_no_evidence", "attester_template", "single_attester", "withdrawn_attestation",
)

_PHANTOM_QUOTE = "the pupils weigh the sampan in kilopascals"

# Which single-node plants have already been placed during this build. A plant that needs
# a particular shape (a keyed option table, a choice item) walks the corpus until it finds
# a node that has it; landing on none at all is a loud failure in `run_gate`, never a
# silent no-op that would score the mutation as SURVIVED for the wrong reason.
_PLACED: set = set()


def corpus_nodes() -> List[str]:
    """The first CORPUS_SIZE registered nodes, sorted. Derived, never hand-picked."""
    nodes = sorted(get_all_node_ids())[:CORPUS_SIZE]
    if len(nodes) < CORPUS_SIZE:
        raise RuntimeError(
            f"the registry holds {len(nodes)} nodes; this corpus needs {CORPUS_SIZE} to "
            f"exceed one blind batch, without which the plurality gates cannot be planted."
        )
    return nodes


def _samples_for(node_id: str) -> List[Dict[str, Any]]:
    """Live renders through the production pipeline. A render failure is loud."""
    out: List[Dict[str, Any]] = []
    for seed in SEEDS:
        try:
            out.append(_render_sample(node_id, seed))
        except Exception as exc:  # noqa: BLE001 -- named, never skipped
            raise RuntimeError(
                f"isolated corpus: {node_id} seed {seed} could not be rendered "
                f"({type(exc).__name__}: {exc}). The control corpus must be built from "
                f"content the pipeline actually serves; fix the render, do not drop the seed."
            ) from exc
    return out


# ─── the §5 corpus ────────────────────────────────────────────────────────────


_SINGLE_NODE_PLANTS = frozenset({
    "stale_stem", "stale_answer_same_key", "options_dropped", "schema_incomplete",
    "fabricated_quote", "attestation_stale", "attestation_answer_drift",
    "attestation_option_drift", "attester_no_evidence", "withdrawn_attestation",
})


def build_judgment_corpus(dest: Path, plant: Optional[str] = None) -> List[str]:
    _PLACED.clear()
    nodes = corpus_nodes()
    for i, node_id in enumerate(nodes):
        samples = _samples_for(node_id)
        reviewer = f"isolated-reviewer-{i // (CORPUS_SIZE // 2 + 1)}"
        findings = {}
        for j, item in enumerate(sorted(jud.REQUIRED_FINDINGS)):
            # The node id is appended so no two rationales are byte-identical (§5's
            # verbatim-reuse gate), while `_rationale_skeleton` strips it again -- so the
            # SKELETON is still the frame, and the clean corpus keeps at most
            # ceil(CORPUS_SIZE / len(_FRAMES)) nodes per frame, inside _MAX_SKELETON_CLUSTER.
            findings[item] = {
                "verdict": "PASS",
                "rationale": f"{_FRAMES[(i + j * 5) % len(_FRAMES)]} (node {node_id})",
            }
        review = {
            "node_id": node_id,
            "reviewed_by": reviewer,
            "review_date": "2026-09-12",
            "blind": True,
            "sample_seeds": list(SEEDS),
            "samples_reviewed": samples,
            "findings": findings,
            "overall": "PASS",
        }
        _apply_judgment_plant(plant, i, nodes, review, samples)
        path = dest / "_".join(node_id.split("_")[:-1]) / f"{node_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(review, indent=1, ensure_ascii=False), encoding="utf-8")
    _assert_placed(plant)
    return nodes


def _assert_placed(plant: Optional[str]) -> None:
    if plant in _SINGLE_NODE_PLANTS and plant not in _PLACED:
        raise RuntimeError(
            f"isolated corpus: the plant {plant!r} found no node in the corpus that can "
            f"carry its shape, so nothing was planted and a green run would mean nothing. "
            f"Widen SEEDS or CORPUS_SIZE; do not weaken the gate."
        )


def _apply_judgment_plant(plant: Optional[str], i: int, nodes: List[str],
                          review: Dict[str, Any], samples: List[Dict[str, Any]]) -> None:
    """One named violation, applied to the node(s) it needs. No plant -> the control."""
    if plant is None:
        return
    if plant == "single_reviewer":
        review["reviewed_by"] = "isolated-one-identity-for-everything"
        return
    if plant == "template_skeleton":
        # One frame across every node, node id still appended so the strings stay
        # DISTINCT -- otherwise the verbatim gate would fire first and the mutation
        # could not say which of the two it proved.
        node_id = review["node_id"]
        for item in review["findings"]:
            review["findings"][item]["rationale"] = f"{_FRAMES[0]} (node {node_id})"
        return
    if plant == "verbatim_rationale" and i in (0, 1):
        review["findings"]["scale_appropriateness"]["rationale"] = _FRAMES[3]
        return
    # The remaining plants need exactly ONE node, and not necessarily the first: the
    # same-key drift shape only exists on a node whose answer resolves through its own
    # option table, and which node that is depends on the tree. So the plant is placed on
    # the first ELIGIBLE node and recorded, rather than pinned to an index that a new
    # grade would quietly invalidate (Mandate 4).
    if plant in _PLACED:
        return
    if plant == "stale_stem":
        review["samples_reviewed"][0]["question_text"] = (
            str(samples[0].get("question_text", "")) + " PLANTED-DRIFT"
        )
    elif plant == "stale_answer_same_key":
        s = _first_keyed_sample(review["samples_reviewed"])
        if s is None:
            return                  # this node cannot carry the shape; try the next
        opts = s["options"]
        key = str(s.get("correct_answer"))
        c = next(k for k, o in enumerate(opts) if str(o.get("key")) == key)
        other = next(k for k, o in enumerate(opts)
                     if k != c and str(o.get("value")) != str(opts[c].get("value")))
        opts[c]["value"], opts[other]["value"] = opts[other]["value"], opts[c]["value"]
    elif plant == "options_dropped":
        s = _first_option_sample(review["samples_reviewed"])
        if s is None:
            return
        del s["options"]
    elif plant == "schema_incomplete":
        del review["findings"]["cognitive_capacity"]
        review["sample_seeds"] = review["sample_seeds"][:1]
    elif plant == "fabricated_quote":
        f = review["findings"]["competency_fulfillment"]
        f["rationale"] = f"{f['rationale']} A representative item reads '{_PHANTOM_QUOTE}'."
    _PLACED.add(plant)


def _first_option_sample(samples: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """A sample the pupil chooses from, or None when this node renders none."""
    for s in samples:
        if isinstance(s.get("options"), list) and s["options"]:
            return s
    return None


def _first_keyed_sample(samples: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """A sample whose answer resolves THROUGH its own option table (read_mcq shape)."""
    for s in samples:
        opts = s.get("options")
        if not (isinstance(opts, list) and opts):
            continue
        _value, keyed = jud._resolved_answer(s)
        if not keyed:
            continue
        key = str(s.get("correct_answer"))
        c = next((k for k, o in enumerate(opts) if str(o.get("key")) == key), None)
        if c is None:
            continue
        if any(k != c and str(o.get("value")) != str(opts[c].get("value"))
               for k, o in enumerate(opts)):
            return s
    return None


# ─── the §6 corpus ────────────────────────────────────────────────────────────


def build_attestation_corpus(dest: Path, plant: Optional[str] = None) -> List[str]:
    _PLACED.clear()
    nodes = corpus_nodes()
    dest.mkdir(parents=True, exist_ok=True)
    batch_no = 0
    for i, node_id in enumerate(nodes):
        samples = _samples_for(node_id)
        requires = (get_node_info(node_id) or {}).get("requires") or []
        if not requires:
            continue
        verdicts = []
        for j, req in enumerate(requires):
            cap_id = str(req.get("id", ""))
            clause = str(req.get("clause", ""))
            verdicts.append({
                "capability_id": cap_id,
                "node_id": node_id,
                "clause": clause,
                "verdict": "PROVIDED",
                "seeds_showing_it": list(SEEDS),
                "confidence": "high",
                # The clause text carries into the reasoning, so two verdicts about
                # different clauses do not collapse to one skeleton. That is the same
                # property §6G is testing for, satisfied honestly rather than by padding.
                "reasoning": (
                    f"{_FRAMES[(i + j) % len(_FRAMES)]} The items shown ask the pupil to "
                    f"{clause or 'do what this clause names'}."
                ),
                "action_taken": "none - entry stands",
            })
        # One record per node keeps every batch under _MAX_VERDICTS_PER_BATCH and gives
        # each its own packet, which is what the seed-provenance check reads.
        identity = f"isolated-attester-{i // (CORPUS_SIZE // 2 + 1)}"
        record = {
            "batch": f"isolated{batch_no:03d}_{node_id}",
            "attested_at": "2026-09-12T00:00:00+08:00",
            "attested_by": identity,
            "role": "Attester",
            "blindness": {"saw": ["clause", "competency text", "rendered samples"],
                          "did_not_see": ["CAPABILITY_PROVIDERS", "the node id"],
                          "samples_passed_inline": True,
                          "tool_uses_by_attester": 0},
            "packet": {"builder": "tests/isolated_corpus.py",
                       "sampling": "judgment_packets._render_sample",
                       "node_id": node_id,
                       "seeds": list(SEEDS),
                       "samples_judged": samples},
            "verdicts": verdicts,
            "incidental_findings": [],
        }
        _apply_attestation_plant(plant, i, record, samples)
        (dest / f"{record['batch']}.json").write_text(
            json.dumps(record, indent=1, ensure_ascii=False), encoding="utf-8")
        batch_no += 1
    _assert_placed(plant)
    return nodes


def _apply_attestation_plant(plant: Optional[str], i: int, record: Dict[str, Any],
                             samples: List[Dict[str, Any]]) -> None:
    if plant is None:
        return
    if plant == "single_attester":
        record["attested_by"] = "isolated-one-attester-for-everything"
        return
    if plant == "attester_template":
        for v in record["verdicts"]:
            v["reasoning"] = _FRAMES[0]
        return
    if plant in _PLACED:
        return
    if plant == "attestation_stale":
        record["packet"]["samples_judged"][0]["question_text"] = (
            str(samples[0].get("question_text", "")) + " PLANTED-DRIFT"
        )
    elif plant == "attestation_answer_drift":
        s = record["packet"]["samples_judged"][0]
        s["correct_answer"] = f"PLANTED-{s.get('correct_answer')}"
    elif plant == "attestation_option_drift":
        s = _first_option_sample(record["packet"]["samples_judged"])
        if s is None:
            return
        s["options"] = [dict(o, value=f"PLANTED-{o.get('value')}") if isinstance(o, dict) else o
                        for o in s["options"]]
    elif plant == "attester_no_evidence":
        record["verdicts"][0]["seeds_showing_it"] = []
    elif plant == "withdrawn_attestation":
        record["verdicts"] = record["verdicts"][1:]      # one clause left unattested
    _PLACED.add(plant)


# ─── running the real entry points against the isolated corpus ────────────────


@contextmanager
def _judgment_pointed_at(dir_: Path, nodes: List[str]) -> Iterator[None]:
    real_dir, real_ids = jud.JUDGMENT_DIR, jud.get_all_node_ids
    jud.JUDGMENT_DIR = dir_
    jud.get_all_node_ids = lambda: list(nodes)
    try:
        yield
    finally:
        jud.JUDGMENT_DIR, jud.get_all_node_ids = real_dir, real_ids


@contextmanager
def _attestation_pointed_at(dir_: Path) -> Iterator[None]:
    real = cap._ATTESTATION_DIR
    cap._ATTESTATION_DIR = dir_
    try:
        yield
    finally:
        cap._ATTESTATION_DIR = real


def run_gate(gate: str, plant: Optional[str]) -> List[str]:
    """Build the corpus (clean, or with one plant) and run the REAL entry point on it."""
    with tempfile.TemporaryDirectory(prefix="isolated_corpus_") as tmp:
        root = Path(tmp)
        if gate == "judgment":
            nodes = build_judgment_corpus(root, plant)
            with _judgment_pointed_at(root, nodes):
                return jud.validate_judgment_reviews()
        if gate == "attestation":
            nodes = build_attestation_corpus(root, plant)
            with _attestation_pointed_at(root):
                return cap.validate_capability_attestation(nodes)
        raise ValueError(f"unknown gate {gate!r}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a custody gate against an isolated corpus")
    ap.add_argument("--gate", choices=("judgment", "attestation"), required=True)
    ap.add_argument("--plant", choices=VIOLATIONS, default=None,
                    help="override PLANT from the command line (for diagnosis)")
    args = ap.parse_args()

    plant = args.plant or PLANT
    if plant is not None and plant not in VIOLATIONS:
        raise SystemExit(f"unknown planted violation {plant!r}; known: {sorted(VIOLATIONS)}")

    # The positive control ALWAYS runs first: a gate that reports a planted violation on a
    # corpus that was already failing has proved nothing.
    control = run_gate(args.gate, None)
    if control:
        print(f"  FAIL isolated_control_{args.gate} ({len(control)}): the CLEAN corpus is "
              f"not clean, so no plant run against it can be scored.")
        for c in control[:10]:
            print(f"    - {c[:300]}")
        return 2

    print(f"  PASS isolated_control_{args.gate}: a freshly built corpus of "
          f"{CORPUS_SIZE} node(s) produces 0 findings")
    if plant is None:
        return 0

    findings = run_gate(args.gate, plant)
    if not findings:
        print(f"  FAIL isolated_plant_{args.gate}: planted {plant!r} and the gate reported "
              f"NOTHING. Either the check is broken or the plant no longer reaches the code "
              f"it runs (Mandate 2) -- diagnose which before changing either.")
        return 1
    print(f"  FAIL isolated_plant_{args.gate} ({len(findings)}) planted={plant}:")
    for f in findings[:10]:
        print(f"    - {f[:400]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
