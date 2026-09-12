"""
Practice Generation — Blind Judgment Review Packets

Builds the data a *blind* reviewer-agent needs to judge a node's generated
problems against its MATATAG competency — and nothing else. The reviewer is
handed only the competency text plus a set of rendered sample problems from
fixed seeds; it never sees the generator/DNA/formatter code. That is what makes
the resulting review genuine rather than the author grading its own homework
(`doc_rem.md` §3.1: "the verifier is not the author").

A packet is pure rendered output (question text, correct answer, options), so
handing it to a reviewer discloses no implementation detail.

CLI:
    python -m backend.app.practice_gen.validation.judgment_packets --node mat_g1_na_q1_0
    python -m backend.app.practice_gen.validation.judgment_packets --group mat_g1_na_q1
    python -m backend.app.practice_gen.validation.judgment_packets --all
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

from backend.app.practice_gen.pipeline import run
from backend.app.practice_gen.registry import get_all_node_ids, get_node_info, get_node_dnas, get_node_competency_bounds
from backend.app.practice_gen.axes_catalog import get_axes_for_concept
from backend.app.practice_gen.compatibility import VARIANTS_BY_DNA

# Fixed seeds so a review is reproducible and the harness can require >= 3 of them.
REVIEW_SEEDS: List[int] = [42, 43, 44, 45, 46]


def _max_difficulty_profile(node_id: str) -> Dict[str, float]:
    """
    A difficulty_profile pinning every continuous axis of every DNA this node
    maps to at scalar 1.0 -- the axis name varies per DNA (max_sum for
    addition, max_product for multiplication, number_difficulty for most
    others), so this is built generically rather than hardcoding one name.
    """
    profile: Dict[str, float] = {}
    for dna_name in get_node_dnas(node_id) or []:
        for axis in get_axes_for_concept(dna_name):
            if axis.get("dim_type") == "continuous":
                profile[axis["name"]] = 1.0
    return profile


# Seeds >= this are reserved for max-difficulty stratification (see
# _render_sample) -- disjoint from REVIEW_SEEDS (42-46) and _STRATIFY_SCAN
# (47-146) so a cited seed's number alone determines which profile to
# re-render with. This keeps validate_judgment.py's freshness check (which
# calls `_render_sample(node_id, seed)` with no profile argument at all)
# automatically consistent with what the packet builder rendered, with no
# schema change and no dependence on a reviewing agent propagating metadata.
_MAX_DIFFICULTY_SEED_FLOOR = 500
_MAX_DIFFICULTY_SEED_CEIL = 600

# Seeds >= this are reserved for discrete-variant coverage: many competencies
# name a specific sub-case (e.g. "with and without regrouping", "counting up
# vs. putting together") that corresponds to a real, already-implemented
# discrete variant value the DNA supports -- but nothing ever selects it by
# default, so a plain seed-only render never demonstrates it and a review
# never sees it (the identical root cause _stratified_seeds already fixed
# once for formatter coverage, recurring here for variant coverage instead).
# seed - _VARIANT_COVERAGE_SEED_FLOOR indexes a fixed, sorted list of
# candidate (variant_name, value) pairs so the mapping is reconstructible
# from (node_id, seed) alone, the same trick as the max-difficulty range.
_VARIANT_COVERAGE_SEED_FLOOR = 600


def _bound_allows(bound: Any, val: Any) -> bool:
    """
    True if `val` is compatible with a node's registry-computed competency
    bound for the same dimension name. Bounds come in several shapes
    (get_node_competency_bounds): a single str/bool/int pins the dimension
    to exactly that value; a list is a pool of allowed values; a (min, max)
    tuple is a continuous range. Only compare within a shape -- e.g. a
    numeric val against a tuple range -- otherwise assume incompatible types
    means the axis isn't the same one the bound refers to and allow it.
    """
    if isinstance(bound, tuple) and len(bound) == 2:
        try:
            return bound[0] <= val <= bound[1]
        except TypeError:
            return True
    if isinstance(bound, list):
        return val in bound
    return val == bound


def _variant_coverage_candidates(node_id: str) -> List[tuple]:
    """
    Sorted (variant_name, value) pairs worth demonstrating at least once:
    every discrete option from VARIANTS_BY_DNA and every discrete axis
    option from axes_catalog, across every DNA this node maps to. Sorted so
    the seed->pair mapping is stable across runs.

    Filtered against this node's own registry-computed competency bounds
    (get_node_competency_bounds) so a dimension the registry has already
    pinned to one value (e.g. this node's competency is "compare" only,
    not "add") never gets an out-of-bounds candidate value -- requesting
    one crashes generate_problem's boundary check on the non-student path
    (found via mat_g1_na_q4_1 seed 611 requesting operation='add' on a
    compare-only node).
    """
    pairs = set()
    # The bounds the PIPELINE will actually enforce when this node is rendered.
    #
    # The per-DNA bounds below are correct per DNA, but a multi-DNA node renders on one
    # of them, and the boundary check tests the request against these. mat_g3_mg_q2_2
    # ("Compare masses of objects") maps to both mass_capacity and comparing_ordering;
    # comparing_ordering legitimately parses task_type='compare_pair', so it was declared,
    # while the node's effective bounds pin task_type='compare' -- every render raised
    # "Boundary violation: requesting out-of-bounds discrete variant".
    #
    # Forcing the owning DNA would make it render, and that is the wrong fix: it produces
    # "Kuya Pat has 1054 marbles. Maria has 9170 marbles" on a node whose competency is
    # about comparing MASSES, and the identical marbles item on the capacity node. The
    # student path already serves the right content from mass_capacity ("Which is heavier:
    # 22 g or 47 g?"). A variant only worth demonstrating is one the node can be asked for
    # on the path it actually renders on.
    #
    # Measured before landing: 3 dropped, all 3 already failed to render, ZERO dropped
    # that the generator could produce.
    effective_bounds = get_node_competency_bounds(node_id) or {}
    for dna_name in get_node_dnas(node_id) or []:
        bounds = get_node_competency_bounds(node_id, dna_name)
        max_places = _max_regrouping_places_for(bounds)
        for var_name, opts in VARIANTS_BY_DNA.get(dna_name, {}).items():
            if isinstance(opts, list):
                bound = bounds.get(var_name)
                for v in opts:
                    if bound is not None and not _bound_allows(bound, v):
                        continue
                    eff = effective_bounds.get(var_name)
                    if eff is not None and not _bound_allows(eff, v):
                        continue
                    if var_name == "regrouping" and (
                        not _regrouping_fits(v, max_places)
                        or not _regrouping_applies(bounds)
                    ):
                        continue
                    if var_name == "tables" and not _tables_apply(bounds):
                        continue
                    if not _variant_reaches_this_node(node_id, dna_name, var_name, v):
                        continue
                    pairs.add((var_name, v))
        for axis in get_axes_for_concept(dna_name):
            if axis.get("dim_type") == "discrete":
                bound = bounds.get(axis["name"])
                for opt in axis.get("options", []):
                    val = opt.get("value") if isinstance(opt, dict) else opt
                    if bound is not None and not _bound_allows(bound, val):
                        continue
                    eff = effective_bounds.get(axis["name"])
                    if eff is not None and not _bound_allows(eff, val):
                        continue
                    # Same ceiling filter as the VARIANTS_BY_DNA branch above.
                    # `regrouping` is declared HERE, as a discrete axis, not in
                    # VARIANTS_BY_DNA -- filtering only that branch changed nothing.
                    if axis["name"] == "regrouping" and (
                        not _regrouping_fits(val, max_places)
                        or not _regrouping_applies(bounds)
                    ):
                        continue
                    if axis["name"] == "tables" and not _tables_apply(bounds):
                        continue
                    if not _variant_reaches_this_node(node_id, dna_name, axis["name"], val):
                        continue
                    pairs.add((axis["name"], val))
    return sorted(pairs, key=lambda p: (str(p[0]), str(p[1])))



def _max_regrouping_places_for(bounds: Dict[str, Any]) -> Optional[int]:
    """Borrow/carry positions this node's NUMBER CEILING physically admits, or None."""
    from ..dna.na.subtraction import max_regrouping_places

    ceiling = bounds.get("max_minuend") or bounds.get("max_sum") or bounds.get("max_result")
    if isinstance(ceiling, tuple):
        ceiling = ceiling[1]
    if not isinstance(ceiling, int):
        return None
    return max_regrouping_places(ceiling)


def _regrouping_applies(bounds: Dict[str, Any]) -> bool:
    """
    False when the node's competency pins a task_type for which regrouping is meaningless.

    An estimation competency ("Estimate the sum/difference of two numbers of up to 4
    digits") rounds each operand to its leading place BEFORE operating, so there is no
    borrow or carry column left to have a depth. Both DNAs say so in their own words when
    asked -- addition: "task_type='estimate' rounds each addend to its own leading place
    before adding"; subtraction: "task_type='estimate' rounds both operands before
    subtracting". Offering a regrouping candidate there is a contradictory declaration,
    not a generator gap: 8 of §2I's findings, on mat_g3_na_q2_2 and mat_g3_na_q2_5.

    Keyed off the node's OWN competency-derived bounds, so it says nothing about which
    levels a non-estimate node can reach -- that stays `_regrouping_fits`, and stays
    arithmetic.
    """
    return bounds.get("task_type") != "estimate"


def _variant_reaches_this_node(node_id: str, dna_name: str, var_name: str, value: Any) -> bool:
    """
    False when the pipeline's OWN curriculum gate would refuse this variant here.

    `generate_context` rejects a variant value the MATATAG progression has not
    introduced at the node's grade and quarter (base_generator.py, "c2. Curriculum-gate
    check"), so a candidate it would refuse is a declaration the node cannot honour --
    the reviewer gets a thinner packet and §2I reports a finding that names a gate doing
    its job. `CURRICULUM_VARIANT_GATES` is the single source of truth for when a variant
    enters the curriculum, and this CALLS it through the same `known_variants` guard the
    pipeline applies, in the same order. It does not restate the rule: a second copy is
    what caused the §2H defect and the over-filter §2I's docstring records.

    This replaces `_unit_type_applies`, which mirrored length_measurement.py's "standard
    units are G2+" rule by hand and was carried as a KNOWN LIMITATION from 2026-09-08.
    The gate table already carries ("length_measurement", "unit_type", "cm"/"m") -> (2, 1),
    so the general filter covers it exactly and the mirror is gone rather than annotated.

    Measured before landing (2026-09-08), all three directions, every DNA:
      * dropped and already failing  : 12  (the whole §2I finding list)
      * dropped but actually renders :  0  (no over-filter)
      * kept and still failing       :  0
    """
    from ..compatibility import (get_variants_for_dna, is_variant_available_at,
                                 node_grade_quarter)

    # The gate only judges individually-selectable variant values; generate_context
    # skips anything outside VARIANTS_BY_DNA before consulting it, so this must too.
    if str(value) not in get_variants_for_dna(dna_name).get(var_name, []):
        return True
    grade, quarter = node_grade_quarter(node_id)
    return is_variant_available_at(dna_name, var_name, str(value), grade, quarter)


def _tables_apply(bounds: Dict[str, Any]) -> bool:
    """
    False when the node's competency is not about multiplication or division at all.

    `tables` is a multiplication concept, but the missing_number DNA serves both
    arithmetic and multiplicative competencies, so its table options were offered to
    every node mapped to it. mat_g1_na_q3_1 ("Find the missing number in addition or
    subtraction sentences involving numbers up to 20") was asked to demonstrate
    tables='6' -- 8 of §2I's findings.

    Reads the node's OWN parsed `operation` bound rather than re-reading the competency
    text: the parser already resolves that phrase to "addition_subtraction",
    "multiplication_division" or "equivalent", and every node that legitimately carries
    a `tables` bound also carries operation="multiplication_division". An unpinned axis
    normally means "any value is allowed"; for an axis the competency's operation
    excludes outright, it means "not applicable".
    """
    operation = bounds.get("operation")
    if operation is None:
        return True
    return operation == "multiplication_division"


def _regrouping_fits(level: Any, max_places: Optional[int]) -> bool:
    """
    False only when `level` demands MORE borrow places than the ceiling can produce.

    A regrouping depth is bounded by digit count, not by any `regrouping` bound in the
    competency: a competency reading "with and without regrouping" pins that both cases
    occur, never how deep. So a max_sum of 20 (two digits, one carry position) was still
    offered three_places and four_places, and 28 such candidates could not render --
    28 of the 38 regrouping findings §2I reported.

    `max_regrouping_places` is the DNA's own single source of truth for this (its
    docstring names the four call sites that already defer to it); this is a fifth
    caller, not a second copy of the rule.

    Deliberately one-sided. §2I's docstring records an earlier attempt to predict
    producibility with `regrouping_is_feasible`, which over-filtered 3 candidates on 2
    nodes because `generate_params` normalises "one_place" -> "ones" before applying it.
    This drops a candidate ONLY when the arithmetic is unambiguous (required places
    exceed available places), so a normalisation difference cannot cause a false drop.
    Measured before landing: 28 dropped and all 28 already failed to render; ZERO
    candidates dropped that the generator could actually produce.
    """
    from ..dna.na.subtraction import REGROUP_LEVEL_PLACES

    if max_places is None:
        return True
    needed = REGROUP_LEVEL_PLACES.get(level)
    if needed is None:
        return True          # unknown level name: observe it, do not predict
    return needed <= max_places


def _render_sample(node_id: str, seed: int, difficulty_profile: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate one problem and reduce it to reviewer-facing rendered fields only."""
    if difficulty_profile is None and _MAX_DIFFICULTY_SEED_FLOOR <= seed < _MAX_DIFFICULTY_SEED_CEIL:
        difficulty_profile = _max_difficulty_profile(node_id)
    elif difficulty_profile is None and seed >= _VARIANT_COVERAGE_SEED_FLOOR:
        candidates = _variant_coverage_candidates(node_id)
        if candidates:
            var_name, val = candidates[(seed - _VARIANT_COVERAGE_SEED_FLOOR) % len(candidates)]
            difficulty_profile = {var_name: val}
    p = run(node_id, seed=seed, difficulty_profile=difficulty_profile)
    fd = p.get("format_data") or {}
    options = fd.get("mcq_options") or fd.get("options")
    sample: Dict[str, Any] = {
        "seed": seed,
        "formatter": p.get("format") or p.get("formatter"),
        "question_text": p.get("question_text", ""),
        "correct_answer": p.get("correct_answer"),
    }
    if options is not None:
        sample["options"] = options
    if p.get("hint"):
        sample["hint"] = p.get("hint")
    if fd.get("cloze_text"):
        sample["cloze_text"] = fd.get("cloze_text")
    return sample


# How far past REVIEW_SEEDS to look for rendering paths the base seeds miss, and
# how many extra samples to add. Both fixed so a packet stays reproducible.
_STRATIFY_SCAN = range(47, 147)
_MAX_EXTRA_SAMPLES = 5

# Fixed seeds >= _MAX_DIFFICULTY_SEED_FLOOR, rendered at every continuous
# axis pinned to 1.0 (see _render_sample). Up to 3 are kept per packet.
_MAX_DIFFICULTY_SEED_SCAN = range(500, 510)
_MAX_DIFFICULTY_SAMPLES = 3

# Up to this many discrete-variant-coverage samples are kept per packet.
_VARIANT_COVERAGE_SAMPLES = 6


def _stratified_seeds(node_id: str) -> List[int]:
    """
    REVIEW_SEEDS, plus one seed per rendering path those five happen to miss.

    Five fixed draws do not cover a node's formatter mix, and the gap is not
    theoretical. On mat_g1_mg_q1_0, mat_g1_mg_q1_1, mat_g2_mg_q1_0 and
    mat_g1_mg_q4_0 the base seeds render `mcq` five times out of five, while
    `read_mcq` — the ShapeBoard visual — is about 23% of what a student actually
    receives. That visual spent its entire existence discarding the DNA's item
    and drawing an unrelated board of random polygons, and no review ever saw it:
    across all 151 nodes the base seeds observed 233 of 598 distinct rendered
    formats, 39%. A judgment layer that cannot see a path cannot judge it, and
    the staleness gate then pins that blind spot in place, because it only
    re-renders the seeds a review already cites.

    Scanning for *distinct rendered format* is a proxy for "distinct rendering
    path", not a guarantee of one — two formats can share a code path and one
    format can hide several. It is, however, mechanical and reproducible, which
    a reviewer's intuition about what to sample is not.
    """
    # Every render that fails here goes through `_try_render`, which RECORDS it. Until
    # 2026-09-12 these two loops carried bare `except Exception: continue` -- the same
    # silent candidate loss `_try_render` was written to stop, still live two functions
    # away, and invisible for the same reason: a seed that vanishes from a scan looks
    # exactly like a seed the scan never reached. Ground Rule 3.
    seen = {}
    for seed in REVIEW_SEEDS:
        sample = _try_render(node_id, seed)
        if sample is None:
            continue  # recorded in _RENDER_FAILURES; the gate reports it
        seen.setdefault(sample.get("formatter"), seed)

    extra: List[int] = []
    for seed in _STRATIFY_SCAN:
        if len(extra) >= _MAX_EXTRA_SAMPLES:
            break
        sample = _try_render(node_id, seed)
        if sample is None:
            continue
        fmt = sample.get("formatter")
        if fmt not in seen:
            seen[fmt] = seed
            extra.append(seed)

    # REVIEW_SEEDS and _STRATIFY_SCAN both render at the DNA's default
    # difficulty scalar (0.5) -- every seed a review ever cited sampled from
    # the same truncated magnitude window, never the ceiling the competency
    # text actually states. This is not theoretical: mat_g3_na_q2_1 states
    # "sums up to 10 000", but at the default scalar the largest sum
    # observable across dozens of seeds tops out near 250 (log-scaled
    # windowing), so no review could ever have seen a near-ceiling item to
    # judge scale_appropriateness against -- confirmed by rendering the same
    # node at max difficulty and reaching 9985. _MAX_DIFFICULTY_SEED_SCAN is
    # a fixed, reproducible set of seeds that _render_sample (via the
    # reserved _MAX_DIFFICULTY_SEED_FLOOR range) automatically renders at
    # every continuous axis pinned to 1.0 instead.
    max_diff_extra = [s for s in _MAX_DIFFICULTY_SEED_SCAN if _seed_renders(node_id, s)][:_MAX_DIFFICULTY_SAMPLES]

    # Named sub-cases this DNA already implements as a real, selectable
    # variant value (e.g. regrouping="two_places", spine="counting_up") but
    # that a plain seed-only render never picks -- try each candidate and
    # keep it only if it renders and produces text genuinely different from
    # everything collected so far (some declared variants turn out not to
    # change output at all; padding the packet with a no-op duplicate would
    # not add coverage, just noise for the reviewer).
    seen_texts = {s["question_text"] for s in [
        *(x for x in (_try_render(node_id, sd) for sd in list(REVIEW_SEEDS) + extra + max_diff_extra) if x)
    ]}
    variant_extra: List[int] = []
    candidates = _variant_coverage_candidates(node_id)
    for i in range(len(candidates)):
        if len(variant_extra) >= _VARIANT_COVERAGE_SAMPLES:
            break
        seed = _VARIANT_COVERAGE_SEED_FLOOR + i
        sample = _try_render(node_id, seed)
        if sample is None:
            continue
        if sample["question_text"] not in seen_texts:
            seen_texts.add(sample["question_text"])
            variant_extra.append(seed)

    return list(REVIEW_SEEDS) + extra + max_diff_extra + variant_extra


# Every render this module gave up on, as {node_id: [(seed, "ExcType: message"), ...]}.
#
# `_try_render` used to `except Exception: return None` and say nothing. That silence hid a
# real, tree-wide defect for as long as it existed: measured 2026-09-04, 31 nodes offered at
# least one discrete variant-coverage candidate that CANNOT be generated -- mat_g1_na_q1_9
# ("sums up to 20") offering regrouping="four_places", which needs four carry positions;
# length nodes offering unit_type="cm"; four nodes offering number_type="multi_digit". Each
# one silently dropped out of its packet, so the reviewer saw fewer samples than the packet
# intended and no one learned that a declared variant is unproducible.
#
# CLAUDE.md #3 forbids exactly this shape. The skip itself has to stay -- a packet must
# still be buildable -- so the fix is to make it LOUD rather than to make it fatal: record
# every failure, expose it on the packet, and let a check with a shrinking floor drive the
# count down. A silent skip is indistinguishable from "there was nothing to render".
_RENDER_FAILURES: Dict[str, List[tuple]] = {}


def render_failures(node_id: str) -> List[tuple]:
    """(seed, error) pairs this module could not render for `node_id`. Never silent."""
    return list(_RENDER_FAILURES.get(node_id, []))


def _try_render(node_id: str, seed: int) -> Any:
    try:
        return _render_sample(node_id, seed)
    except Exception as exc:  # noqa: BLE001 - recorded and surfaced, never discarded
        _RENDER_FAILURES.setdefault(node_id, []).append(
            (seed, f"{type(exc).__name__}: {str(exc)[:160]}")
        )
        return None


def _seed_renders(node_id: str, seed: int) -> bool:
    """Whether this seed renders. A failure is RECORDED, never merely answered `False`."""
    return _try_render(node_id, seed) is not None


def build_packet(node_id: str) -> Dict[str, Any]:
    info = get_node_info(node_id)
    if info is None:
        raise ValueError(f"Unknown node '{node_id}' — cannot build a review packet.")
    seeds = _stratified_seeds(node_id)
    samples = [_render_sample(node_id, s) for s in seeds]
    return {
        "node_id": node_id,
        "grade": info.get("grade"),
        "quarter": info.get("quarter"),
        "subdomain": info.get("subdomain") or info.get("domain"),
        "competency_text": info.get("competency", ""),
        "sample_seeds": seeds,
        "samples": samples,
    }


def build_group(group_prefix: str) -> List[Dict[str, Any]]:
    ids = [n for n in get_all_node_ids() if "_".join(n.split("_")[:-1]) == group_prefix]
    if not ids:
        raise ValueError(f"No nodes found for group '{group_prefix}'.")
    return [build_packet(n) for n in sorted(ids)]


def _main() -> int:
    ap = argparse.ArgumentParser(description="Build blind judgment-review packets.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--node", help="Single node id, e.g. mat_g1_na_q1_0")
    g.add_argument("--group", help="Group prefix, e.g. mat_g1_na_q1")
    g.add_argument("--nodes", help="Comma-separated explicit node ids")
    g.add_argument("--all", action="store_true", help="Every registered node")
    args = ap.parse_args()

    if args.node:
        out: Any = build_packet(args.node)
    elif args.group:
        out = build_group(args.group)
    elif args.nodes:
        out = [build_packet(n.strip()) for n in args.nodes.split(",") if n.strip()]
    else:
        out = [build_packet(n) for n in sorted(get_all_node_ids())]

    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(_main())
