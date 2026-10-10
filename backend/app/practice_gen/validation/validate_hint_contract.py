"""
§16 -- the hint contract over the live tree, as a CONTENT stage (owner rulings 30 and 36;
batch H5).

`backend/app/practice_gen/hint_contract.hint_chain_violations` is the one statement of the
rule that a hint chain must explain the item it is served with (11 dimensions; read its
docstring for what each covers and does not). Until H5 the live sweep over every lc was the
parametrized unit test `test_no_served_hint_contradicts_its_item`, so a hint defect in ONE
generator failed `unit_tests` and made `run_all` exit 1 -- integrity -- although it is a
defect in content, named by lc and seed. Ruling 30 ("H5 moves the live-output sweeps into a
content stage that names lc and seed and exits 2") moves it here, unchanged in reach:

  * the same seeds: `judgment_packets._stratified_seeds` (the review seeds plus one seed per
    rendering path they miss), rendered by the same `_render_sample`;
  * the same function, `hint_chain_violations`, on the same rendered fields;
  * each finding labelled by its DIMENSION (`hint_contract_<dimension>`), read from the
    structured (dimension, message) pair, never from message text.

Serving still REFUSES a violating item (`adapter.apply_formatter` calls
`enforce_hint_contract`; ruling 36 leaves the existing dimensions enforced). A refused seed
would vanish from the sweep -- the 2026-09-25 lesson in the old test -- so this module
renders with that enforcement switched OFF for the duration of the sweep (restored in
`finally`), and judges the item a learner would have been served. A seed whose render
still raises (a hint builder that fails, say) is `hint_contract_unrendered_16`, never a
silent skip.

The unit tests that prove the RULE (each dimension's motivating case, every visual schema
classified, the serving path enforcing it) stay in `tests/unit/test_hint_contract.py`:
those are harness properties, and stay integrity.

CLI:  PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.validate_hint_contract [--node-ids a,b]

NAMED LIMITS (also in docs/pgen_contract.md §16 and the evidence log):
  1. Every limit of `hint_chain_violations`' dimensions (its docstring).
  2. The stratified seeds, not every seed: a rendering path the stratifier does not reach
     is not swept (its own docstring names the proxy it uses).
  3. Serving still refuses a violating item, so elsewhere in `run_all` such a seed shows up
     as a generation failure in the stages that render it (content in the matrix).
"""
from __future__ import annotations

import sys
from collections import OrderedDict
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional, Tuple

from backend.app.practice_gen import hint_contract as hc

ASSERTIONS = tuple(f"hint_contract_{d}" for d in hc.DIMENSIONS) + (
    "hint_contract_unrendered_16",   # a stratified seed that does not render at all
)


@contextmanager
def _serving_enforcement_off() -> Iterator[None]:
    """Let a violating item render so it can be judged by dimension; restored after."""
    from backend.app.practice_gen import adapter

    real = adapter.enforce_hint_contract
    adapter.enforce_hint_contract = lambda problem, formatter_name: None
    try:
        yield
    finally:
        adapter.enforce_hint_contract = real


def node_findings(node_id: str) -> List[Tuple[str, int, str]]:
    """(label, seed, message) for one lc over its stratified seeds."""
    from backend.app.practice_gen.validation import judgment_packets as jp

    out: List[Tuple[str, int, str]] = []
    before = len(jp.render_failures(node_id))
    with _serving_enforcement_off():
        seeds = jp._stratified_seeds(node_id)
        for seed, message in jp.render_failures(node_id)[before:]:
            out.append(("hint_contract_unrendered_16", seed,
                        f"stratification could not render seed {seed}: {message}"))
        for seed in seeds:
            try:
                sample = jp._render_sample(node_id, seed)
            except Exception as exc:  # noqa: BLE001 -- named finding, never a skip
                out.append(("hint_contract_unrendered_16", seed,
                            f"seed {seed} does not render: {type(exc).__name__}: {str(exc)[:160]}"))
                continue
            for dimension, message in hc.hint_chain_violations(
                hints=sample.get("hints"),
                stem=sample.get("question_text") or "",
                options=sample.get("options"),
                visual_type=sample.get("visual_type"),
                visual_payload=sample.get("visual_payload"),
                interaction_mode=(sample.get("effective") or {}).get("interaction_mode"),
                correct_answer=sample.get("correct_answer"),
            ):
                out.append((f"hint_contract_{dimension}", seed,
                            f"({sample.get('formatter')}) {message}"))
    return out


def collect_findings(node_ids: Optional[List[str]] = None) -> Dict[str, List[str]]:
    from backend.app.practice_gen.registry import get_all_node_ids

    grouped: "OrderedDict[Tuple[str, str], List[Tuple[int, str]]]" = OrderedDict()
    for node_id in (node_ids or sorted(get_all_node_ids())):
        for label, seed, message in node_findings(node_id):
            grouped.setdefault((node_id, label), []).append((seed, message))
    out: Dict[str, List[str]] = {label: [] for label in ASSERTIONS}
    for (node_id, label), hits in grouped.items():
        seed, message = hits[0]
        out[label].append(
            f"{node_id}: seed {seed} ({len(hits)} stratified seed(s)): {message}. Reproduce: "
            f"judgment_packets._render_sample({node_id!r}, {seed}) with serving enforcement off, "
            f"then hint_contract.hint_chain_violations. Owed: make the hint chain describe the "
            f"item it is served with (fix the generator's hint builder or the formatter's rewrap).")
    return out


def validate_all(node_ids: Optional[List[str]] = None) -> bool:
    findings = collect_findings(node_ids)
    total = 0
    for label in ASSERTIONS:
        items = findings[label]
        total += len(items)
        if items:
            print(f"  FAIL {label} ({len(items)}):")
            for item in items[:12]:
                print(f"    - {item}")
            if len(items) > 12:
                print(f"    ... and {len(items) - 12} more.")
        else:
            print(f"  PASS {label}")
    print(f"  §16: {total} finding(s) over {len(node_ids) if node_ids else 'all'} lc(s)")
    return total == 0


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="§16 the hint contract over the live tree (content)")
    ap.add_argument("--node-ids", help="comma-separated lc subset (proof mode)")
    args = ap.parse_args()
    return 0 if validate_all(args.node_ids.split(",") if args.node_ids else None) else 1


if __name__ == "__main__":
    sys.exit(main())
