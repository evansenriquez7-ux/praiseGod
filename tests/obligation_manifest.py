"""
The student-path obligation manifest (plan step 0B, `H-04`).

WHAT AN OBLIGATION IS
---------------------
One base combination the production student route can actually serve:

    (node, DNA, formatter, discrete assignment)

The executor crosses each base combination with 27 interest requests (26 named themes
plus the automatic-selection path), four experience wrappers, and five deterministic
seed slots.  The first three seed slots cross the continuous boundary/equivalence classes
each DNA axis declares. Enumeration here happens WITHOUT generating anything; execution
lives in ``tests/obligation_executor.py``.

WHY THE COUNT IS DERIVED TWICE
------------------------------
`H-04`'s acceptance requires that "two independent derivations agree on the reachable
count". That is not ceremony. The plan carried a recorded figure of **4,325** allowed
`(node, DNA, formatter, discrete-assignment)` obligations across **463** node/DNA/formatter
pairs, and the probe that produced it is NOT on disk: `local_only/scratch/plan_fold_review/`
contains no such enumeration. Neither figure reproduces from the description --
measured 2026-09-12 over four candidate models:

    scope=COMPATIBILITY      pairs=474  sum-of-values=3063  full-product=5238
    scope=advertised         pairs=459  sum-of-values=2950  full-product=5060

That 5,060 candidate was itself over-inclusive: its curriculum-gate call passed a node ID
where the production predicate requires a DNA concept. The first 1,000-obligation execution
found 152 production refusals and instrumented them to that call. Correcting the argument
gives 4,269 base obligations and 461,052 finite obligations after interest and experience;
a second 1,000-obligation execution produced zero refusals. This module states the corrected
model explicitly, derives it twice, and records the superseded figures rather than inheriting
either one.

THE MODEL, STATED
-----------------
  * **Nodes** come from `registry.get_all_node_ids()`.
  * **DNAs** come from `registry.get_node_dnas(node)` (the NODE_TO_DNA mapping).
  * **Formatters** are `COMPATIBILITY[dna]` INTERSECTED with `get_node_formatters(node)`.
    The intersection matters: `get_node_formatters` unions across a node's DNAs and
    subtracts `NODE_FORMATTER_EXCLUSIONS`, so it answers "what may this node advertise",
    while `COMPATIBILITY[dna]` answers "what can this DNA drive". A student can only
    receive a formatter both allow.
  * **Discrete assignments** are the full Cartesian product of the reachable values of
    every variant, per plan step 0B ("It enumerates the Cartesian product of reachable
    finite variants"). Reachable means: supported by the formatter
    (`get_supported_variants`, i.e. FORMATTER_VARIANT_SUPPORT), permitted by the node's
    competency bounds where those pin a variant, and open at the node's grade/quarter
    (`is_variant_available_at`, the curriculum gate).
  * **Continuous axes** declare boundary and equivalence classes -- the two curriculum
    boundaries and one interior representative. Release seed slots 0/1/2 cross those
    representatives with every finite obligation; slots 3/4 add deterministic interior
    points. Multiple axes move together, so cross-axis Cartesian interactions stay named
    as unproved.
  * **Interest requests and experience** are full finite dimensions. The executor crosses
    26 named interest inputs plus the automatic-selection path with all four production
    experience wrappers: 4,269 x 27 x 4 = 461,052 finite obligations.

RENDERER AND RESPONSE MODE ARE NOT FREE DIMENSIONS
--------------------------------------------------
The plan lists renderer and response mode among the dimensions to count. They are
FUNCTIONS OF THE FORMATTER, not independent choices: a formatter determines which React
component renders it and which `answer_collection` it emits. Multiplying by them would
inflate the manifest by a factor that does not exist in production. They are recorded
instead as DERIVED COVERAGE -- every registered renderer and every response mode must be
reached by at least one obligation -- which is the property actually worth holding, and
the one that catches a renderer no node can reach.

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
  * The automatic interest request is NOT a neutral theme. Production chooses a seeded,
    grade-appropriate theme when the caller supplies no preference. Named themes outside a
    grade's band also fall back to that automatic path. H-04 executes every request value;
    H-05 owns whether a requested theme being ignored is acceptable.
  * The PR tier is partial by design. It executes fixed cross-family sentinels and every
    base obligation explicitly identified as changed; only the release-shard union is the
    complete finite sweep.
  * **Continuous partitions are three classes per axis** (min boundary, interior, max
    boundary). Behaviour between the representatives and Cartesian interactions between
    multiple continuous axes stay explicitly unproven.
"""

from __future__ import annotations

import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
BUDGET_PATH = (REPO_ROOT / "validation_reports" / "phase2_hardening"
               / "obligation_budget.json")

# The three classes every continuous axis is partitioned into. Two curriculum boundaries
# and one interior representative; see KNOWN LIMITATIONS.
CONTINUOUS_CLASSES: Tuple[Tuple[str, float], ...] = (
    ("min_boundary", 0.0),
    ("interior", 0.5),
    ("max_boundary", 1.0),
)


@dataclass(frozen=True)
class Obligation:
    node_id: str
    dna: str
    formatter: str
    assignment: Tuple[Tuple[str, str], ...]   # sorted (variant, value) pairs

    def key(self) -> str:
        pinned = ",".join(f"{k}={v}" for k, v in self.assignment)
        return f"{self.node_id}|{self.dna}|{self.formatter}|{pinned}"


@dataclass(frozen=True)
class Rejection:
    node_id: str
    dna: str
    formatter: str
    rule: str       # the PRODUCTION rule that makes this unreachable
    detail: str


# ─────────────────────────────────────────────────────────────────────────────
# Reachability, straight from the production registries
# ─────────────────────────────────────────────────────────────────────────────

def _reachable_values(node_id: str, dna: str, formatter: str,
                      comp_bounds: Dict[str, Any], grade: int,
                      quarter: int) -> Dict[str, List[str]]:
    """
    Each variant's values that production can actually select here, in a stable order.

    Three production gates, applied in the order production applies them:
      1. FORMATTER_VARIANT_SUPPORT, via `get_supported_variants`
      2. the node's competency bounds, where they pin a variant to one value or a list
      3. the curriculum gate `is_variant_available_at` for this grade/quarter
    """
    from backend.app.practice_gen.compatibility import (
        get_supported_variants, is_variant_available_at,
    )

    out: Dict[str, List[str]] = {}
    for name, values in sorted(get_supported_variants(dna, formatter).items()):
        bound = comp_bounds.get(name)
        if isinstance(bound, list):
            wanted = {str(b) for b in bound}
            values = [v for v in values if str(v) in wanted]
        elif isinstance(bound, str):
            values = [v for v in values if str(v) == bound]
        values = [v for v in values
                  if is_variant_available_at(dna, name, str(v), grade, quarter)]
        if values:
            out[name] = sorted(str(v) for v in values)
    return out


def _continuous_axes(dna: str) -> List[str]:
    from backend.app.practice_gen.axes_catalog import get_axes_for_concept

    return sorted(a["name"] for a in get_axes_for_concept(dna)
                  if a.get("dim_type") == "continuous")


def enumerate_obligations() -> Tuple[List[Obligation], List[Rejection]]:
    """
    Every reachable (node, DNA, formatter, discrete assignment), and every rejection
    with the production rule that made it one. Deterministic: sorted throughout.
    """
    from backend.app.practice_gen.compatibility import (
        COMPATIBILITY, node_grade_quarter,
    )
    from backend.app.practice_gen.registry import (
        get_all_node_ids, get_node_competency_bounds, get_node_dnas, get_node_formatters,
    )
    from backend.app.practice_gen.validation.validate_matrix import (
        formatter_refused_at_node,
    )

    obligations: List[Obligation] = []
    rejections: List[Rejection] = []

    for node_id in sorted(get_all_node_ids()):
        grade, quarter = node_grade_quarter(node_id)
        advertised = set(get_node_formatters(node_id))
        dnas = get_node_dnas(node_id)
        if not dnas:
            rejections.append(Rejection(node_id, "(none)", "(all)",
                                        "NODE_TO_DNA_presence",
                                        "node has no DNA mapping, so it serves nothing"))
            continue
        for dna in sorted(dnas):
            comp_bounds = get_node_competency_bounds(node_id, dna)
            for formatter in sorted(COMPATIBILITY.get(dna, [])):
                if formatter not in advertised:
                    rejections.append(Rejection(
                        node_id, dna, formatter, "NODE_FORMATTER_EXCLUSIONS",
                        "the DNA can drive this formatter but the node does not "
                        "advertise it (generated exclusion), so no student receives it"))
                    continue
                if formatter_refused_at_node(dna, comp_bounds, formatter):
                    rejections.append(Rejection(
                        node_id, dna, formatter, "FORMATTER_VARIANT_SUPPORT",
                        "the node's competency binds a variant to values this formatter "
                        "cannot render; the orchestrator refuses the pair (§1C-reverse "
                        "owns it, not the matrix)"))
                    continue

                values = _reachable_values(node_id, dna, formatter, comp_bounds,
                                           grade, quarter)
                if not values:
                    obligations.append(Obligation(node_id, dna, formatter, ()))
                    continue
                names = sorted(values)
                for combo in itertools.product(*(values[n] for n in names)):
                    obligations.append(Obligation(
                        node_id, dna, formatter,
                        tuple(sorted(zip(names, combo))),
                    ))

    obligations.sort(key=Obligation.key)
    rejections.sort(key=lambda r: (r.node_id, r.dna, r.formatter))
    return obligations, rejections


def derive_count_independently() -> Tuple[int, int]:
    """
    The SAME reachable set, reached by a different traversal: formatter-first.

    `enumerate_obligations` walks nodes -> DNAs -> formatters, reading the node's
    advertised list. This walks the formatter registry -> DNAs that declare it ->
    nodes mapped to those DNAs. Different entry points into the same production tables,
    so a transcription error in either shows up as a disagreement rather than as a
    confidently wrong number.

    Returns (pairs, obligations).
    """
    from backend.app.practice_gen.adapter import FORMATTER_ROUTES
    from backend.app.practice_gen.compatibility import (
        get_dnas_for_formatter, node_grade_quarter,
    )
    from backend.app.practice_gen.registry import (
        get_all_node_ids, get_node_competency_bounds, get_node_dnas, get_node_formatters,
    )
    from backend.app.practice_gen.validation.validate_matrix import (
        formatter_refused_at_node,
    )

    nodes_for_dna: Dict[str, List[str]] = {}
    for node_id in get_all_node_ids():
        for dna in get_node_dnas(node_id):
            nodes_for_dna.setdefault(dna, []).append(node_id)

    pairs = 0
    total = 0
    for formatter in sorted(FORMATTER_ROUTES):
        for dna in sorted(get_dnas_for_formatter(formatter)):
            for node_id in sorted(nodes_for_dna.get(dna, ())):
                if formatter not in set(get_node_formatters(node_id)):
                    continue
                comp_bounds = get_node_competency_bounds(node_id, dna)
                if formatter_refused_at_node(dna, comp_bounds, formatter):
                    continue
                grade, quarter = node_grade_quarter(node_id)
                pairs += 1
                values = _reachable_values(node_id, dna, formatter, comp_bounds,
                                           grade, quarter)
                product = 1
                for vals in values.values():
                    product *= len(vals)
                total += product
    return pairs, total


# ─────────────────────────────────────────────────────────────────────────────
# The budget report
# ─────────────────────────────────────────────────────────────────────────────

def _derived_coverage(obligations: Sequence[Obligation]) -> Dict[str, Any]:
    """
    Renderer and response mode are functions of the formatter, so the property worth
    holding is COVERAGE, not a multiplier: every registered formatter route must be
    reachable by some obligation. One that is not is a route no student can receive.
    """
    from backend.app.practice_gen.adapter import FORMATTER_ROUTES

    reached = sorted({o.formatter for o in obligations})
    registered = sorted(FORMATTER_ROUTES)
    return {
        "registered_formatters": len(registered),
        "formatters_reached_by_some_obligation": len(reached),
        "formatters_no_obligation_can_reach": sorted(set(registered) - set(reached)),
        "note": (
            "renderer and answer_collection are determined by the formatter, so they are "
            "reported as coverage rather than multiplied into the manifest; see the "
            "module docstring"
        ),
    }


def build_budget() -> Dict[str, Any]:
    from backend.app.practice_gen.compatibility import COMPATIBILITY

    obligations, rejections = enumerate_obligations()
    alt_pairs, alt_total = derive_count_independently()

    pairs = sorted({(o.node_id, o.dna, o.formatter) for o in obligations})
    per_node: Dict[str, int] = {}
    per_dna: Dict[str, int] = {}
    per_formatter: Dict[str, int] = {}
    for o in obligations:
        per_node[o.node_id] = per_node.get(o.node_id, 0) + 1
        per_dna[o.dna] = per_dna.get(o.dna, 0) + 1
        per_formatter[o.formatter] = per_formatter.get(o.formatter, 0) + 1

    continuous: Dict[str, List[str]] = {
        dna: _continuous_axes(dna) for dna in sorted(COMPATIBILITY)
    }
    continuous_crossings = sum(
        len(continuous.get(o.dna, ())) * len(CONTINUOUS_CLASSES) for o in obligations
    )

    rejection_rules: Dict[str, int] = {}
    for r in rejections:
        rejection_rules[r.rule] = rejection_rules.get(r.rule, 0) + 1

    # Read the crossed dimensions from the executor, which derives them from production.
    # Keeping the cross in one place prevents the budget and executor from reporting
    # different products while each looks internally consistent.
    from tests.obligation_executor import (
        DEFAULT_SEEDS_PER_OBLIGATION,
        SEED_SLOT_SCALARS,
        cache_key_count,
        experience_values,
        finite_obligation_count,
        interest_request_values,
        represented_execution_count,
    )

    experiences = list(experience_values())
    interests = list(interest_request_values())

    return {
        "schema_version": 1,
        "model": (
            "base obligation = (node, DNA, formatter, discrete assignment), crossed "
            "for execution with every interest request, experience wrapper, and five "
            "deterministic seed slots. See tests/obligation_manifest.py and "
            "tests/obligation_executor.py for the stated model and limits."
        ),
        "counts": {
            "nodes": len({o.node_id for o in obligations}),
            "node_dna_formatter_pairs": len(pairs),
            "discrete_obligations": len(obligations),
            "continuous_class_crossings": continuous_crossings,
            "continuous_classes_per_axis": len(CONTINUOUS_CLASSES),
        },
        "independent_derivation": {
            "pairs": alt_pairs,
            "discrete_obligations": alt_total,
            "agrees": alt_pairs == len(pairs) and alt_total == len(obligations),
            "method": "formatter-first traversal; see derive_count_independently",
        },
        "plan_figure_not_reproduced": {
            "recorded_in_plan": {"pairs": 463, "allowed_assignments": 4325},
            "first_manifest_candidate": {
                "pairs": 459,
                "allowed_assignments": 5060,
                "status": (
                    "SUPERSEDED after execution: 152 of the first 1,000 candidates were "
                    "refused because the manifest passed node_id to a DNA-keyed "
                    "curriculum gate. Corrected base count is 4,293."
                ),
            },
            "status": (
                "NOT REPRODUCIBLE. The probe that produced it is not on disk and no "
                "candidate model recovers either figure. This manifest supersedes it; "
                "the plan's number is recorded here rather than inherited."
            ),
        },
        "per_dimension": {
            "by_node_top": dict(sorted(per_node.items(), key=lambda kv: -kv[1])[:10]),
            "by_dna": dict(sorted(per_dna.items(), key=lambda kv: -kv[1])),
            "by_formatter": dict(sorted(per_formatter.items(), key=lambda kv: -kv[1])),
            "continuous_axes_by_dna": continuous,
            "experience": experiences,
            "student_interest_request": [
                i if i is not None else "(automatic)" for i in interests
            ],
        },
        "execution_model": {
            "experience": {"values": experiences, "multiplier": len(experiences)},
            "student_interest_request": {
                "values": [i if i is not None else "(automatic)" for i in interests],
                "multiplier": len(interests),
                "note": (
                    "None is production's automatic-selection path, not a neutral theme. "
                    "Grade-inappropriate named themes also fall back automatically; H-05 "
                    "owns that ignored-theme behavior."
                ),
            },
            "finite_obligations": finite_obligation_count(),
            "seeds_per_obligation": DEFAULT_SEEDS_PER_OBLIGATION,
            "seed_slot_scalars": list(SEED_SLOT_SCALARS),
            "release_cache_keys": cache_key_count(DEFAULT_SEEDS_PER_OBLIGATION),
            "release_represented_executions": represented_execution_count(
                DEFAULT_SEEDS_PER_OBLIGATION
            ),
            "cache_key": "base obligation + interest request + seed slot",
            "cache_reuse": (
                "the generated/formatted problem is deep-copied through all four "
                "production experience wrappers"
            ),
        },
        "rejected": {
            "total": len(rejections),
            "by_production_rule": rejection_rules,
            "examples": [
                {"node": r.node_id, "dna": r.dna, "formatter": r.formatter,
                 "rule": r.rule, "detail": r.detail}
                for r in rejections[:10]
            ],
        },
        "derived_coverage": _derived_coverage(obligations),
    }


def write_budget() -> Dict[str, Any]:
    """Atomically write and return the current machine-readable budget."""
    budget = build_budget()
    BUDGET_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = BUDGET_PATH.with_suffix(BUDGET_PATH.suffix + ".tmp")
    temporary.write_text(json.dumps(budget, indent=2) + "\n", encoding="utf-8")
    temporary.replace(BUDGET_PATH)
    return budget


def main() -> int:
    budget = write_budget()

    counts = budget["counts"]
    alt = budget["independent_derivation"]
    print(f"  nodes={counts['nodes']} "
          f"pairs={counts['node_dna_formatter_pairs']} "
          f"discrete_obligations={counts['discrete_obligations']} "
          f"continuous_crossings={counts['continuous_class_crossings']}")
    print(f"  rejected={budget['rejected']['total']} "
          f"by rule {budget['rejected']['by_production_rule']}")
    execution = budget["execution_model"]
    print(f"  crossed execution dimensions: experience "
          f"x{execution['experience']['multiplier']} interest request "
          f"x{execution['student_interest_request']['multiplier']} "
          f"-> {execution['finite_obligations']} finite obligations; "
          f"{execution['release_represented_executions']} executions at "
          f"{execution['seeds_per_obligation']} seeds")
    unreachable = budget["derived_coverage"]["formatters_no_obligation_can_reach"]
    print(f"  formatters no obligation can reach: {unreachable}")
    print(f"  wrote {BUDGET_PATH.relative_to(REPO_ROOT)}")

    if not alt["agrees"]:
        print(f"  FAIL obligation_derivations_agree: node-first enumeration says "
              f"{counts['node_dna_formatter_pairs']} pairs / "
              f"{counts['discrete_obligations']} obligations, formatter-first says "
              f"{alt['pairs']} / {alt['discrete_obligations']}. Two derivations of one "
              f"production fact disagree, so neither is evidence.")
        return 1
    print(f"  PASS obligation_derivations_agree: two independent traversals agree on "
          f"{counts['node_dna_formatter_pairs']} pairs and "
          f"{counts['discrete_obligations']} discrete obligations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
