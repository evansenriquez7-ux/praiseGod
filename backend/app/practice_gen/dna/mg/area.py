"""
DNA: Area (Measurement & Geometry)

Covers MATATAG grade 3 area competencies only.
  G3: area of squares and rectangles in sq cm and sq m
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set

from backend.app.practice_gen.dna.base import (
    DNA,
    ErrorPattern,
    VocabGated,
    linear_interpolate,
)


# ─── param bounds ─────────────────────────────────────────────────────────────
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    # Minimum side is 2, not 1: a 1x1 square has an area numerically equal to its
    # own side, so "A square has a side of 1 m. What is its area in sq m?" prints
    # its answer in the stem (validate_matrix §1F), and the tiled phrasing renders
    # the ungrammatical "arranged in 1 rows and 1 columns". A single tile is not
    # an area exercise in any case.
    "g3": {
        "side_cm_min": 2,
        "side_cm_max": 50,
        "side_m_min":  2,
        "side_m_max":  20,
        # illustrate_tiles/derive_formula ask the student to visually tile-count
        # or trace rows × columns one tile at a time (mat_g3_mg_q1_0/_1) -- the
        # standard 2-50 cm range lets a rectangle reach e.g. 22x5=110 tiles,
        # blind review flagged that as too large to tile-count or trace at
        # first exposure. Keep those two task types near 10x10 or below.
        "side_cm_max_tiling": 12,
    },
}


# ─── operation gating (CLAUDE.md Content Rule 1) ──────────────────────────────
# An area is a multiplication, so the sides this DNA may draw are governed by the
# multiplication the student has actually met. All four area nodes sit at G3 Q1,
# and the knowledge graph is explicit about what that means:
#
#   mat_g3_mg_q1_2.cumulative_concepts  contains multiplication_tables_2_3_4_5_10
#                                       and division_tables_2_3_4_5_10
#   mat_g3_na_q3_0 (G3 *Q3*)            introduces multiplication_tables_6_7_8_9
#   mat_g3_na_q3_2 (G3 Q3)              introduces 2-3 digit x 1-digit
#
# So the 6/7/8/9 tables arrive two quarters *after* these nodes, and multi-digit
# by multi-digit appears nowhere in Grade 3 at all. Drawing sides from a free
# 2..50 range produced 'A rectangle has sides 25 cm and 26 cm' (25x26) and
# 'A rectangle has an area of 44 sq cm and a width of 22 cm' (44/22) -- both
# requiring operations introduced later, which is exactly what Content Rule 1
# forbids. Three independent blind reviewers flagged the magnitudes without
# conferring.
#
# Every area is therefore a fact from a table the student holds: one side is
# drawn from the known tables, the other from 2..10. Difficulty widens the pool,
# never past what has been taught.
_KNOWN_TABLES = (2, 3, 4, 5, 10)
_OTHER_SIDE_MAX = 10


# How each offered distractor rule computes, so an inductive item can prove its own
# cases rule them out. Keys must match the distractor strings exactly.
_RULE_VALUES = {
    "length + width":                   lambda a, b: a + b,
    "length + width + length + width":  lambda a, b: 2 * (a + b),
    "length + length":                  lambda a, b: a + a,
    "side + side":                      lambda a, b: a + a,
    "4 × side":                         lambda a, b: 4 * a,
    "side + 4":                         lambda a, b: a + 4,
}


def _assert_cases_determine(cases, answer, distractors, seed):
    """
    An inductive item is well posed only if the cases shown FALSIFY every distractor.

    If some distractor reproduces the keyed total on every case, the evidence supports
    two rules equally and the pupil is marked wrong for reasoning correctly. This is a
    property of the (cases, distractor pool) pair, so it is checked rather than assumed.
    """
    for d in distractors:
        rule = _RULE_VALUES.get(d)
        if rule is None:
            raise ValueError(
                f"area: distractor {d!r} has no entry in _RULE_VALUES (seed={seed}); "
                f"add one so the inductive item can prove its cases rule it out."
            )
        if all(rule(a, b) == total for a, b, total in cases):
            raise ValueError(
                f"area: inductive item is under-determined (seed={seed}). Distractor "
                f"{d!r} reproduces the keyed answer {answer!r} on every case {cases}, "
                f"so two rules fit the evidence. Vary a dimension the distractor "
                f"depends on, or drop it from the pool."
            )


# Estimation needs options far enough apart that estimating discriminates.
# mat_g3_mg_q1_0's competency is "Illustrate and ESTIMATE the area ... using square
# tile units", but its distractors came from the shared error patterns, and when
# those collided with the answer they were filtered out and fmt_mcq's fallback
# padded with correct +/- 1. A blind reviewer caught the result: seed 50 asked
# "Estimate how many unit tiles cover the square in all" against 15, 16 and 17 --
# "no estimation strategy separates them and the item silently demands an exact
# product". Options a fifth apart or more make the estimate do real work.
_ESTIMATE_MIN_RELATIVE_GAP = 0.2


def _estimation_distractors(rows: int, cols: int) -> List[int]:
    """
    Three wrong tile counts, each far enough from the true one to be told apart by
    estimating rather than by computing exactly.

    Candidates are the real misconceptions first -- added instead of multiplied,
    perimeter instead of area, one row too many or too few -- then filtered so every
    kept value differs from the answer, and from every value already kept, by at
    least _ESTIMATE_MIN_RELATIVE_GAP of the answer.
    """
    answer = rows * cols
    candidates = [
        rows + cols,            # added instead of multiplied
        2 * (rows + cols),      # perimeter instead of area
        (rows - 1) * cols,      # missed a whole row
        (rows + 1) * cols,      # counted a row twice
        answer * 2,             # doubled
        max(1, answer // 2),    # halved
    ]
    kept: List[int] = []
    for c in candidates:
        if c <= 0 or c == answer:
            continue
        if abs(c - answer) < _ESTIMATE_MIN_RELATIVE_GAP * answer:
            continue
        if any(abs(c - k) < _ESTIMATE_MIN_RELATIVE_GAP * answer for k in kept):
            continue
        kept.append(c)
        if len(kept) == 3:
            break
    return kept


def _table_and_cofactor(scalar: float, rng: random.Random) -> tuple:
    """
    A (table_factor, co_factor) pair whose product is a known-table fact at G3 Q1.

    `table_factor` is always one of _KNOWN_TABLES, so the product is a fact from a
    table the student has met and -- for the inverse task -- dividing by it is a
    `division_tables_2_3_4_5_10` fact. Difficulty grows the pool of tables and the
    size of the co-factor; it never reaches past the curriculum.
    """
    if scalar < 0.34:
        tables, other_max = (2, 3, 4), 5
    elif scalar < 0.67:
        tables, other_max = (2, 3, 4, 5), 8
    else:
        tables, other_max = _KNOWN_TABLES, _OTHER_SIDE_MAX
    return rng.choice(tables), rng.randint(2, other_max)


# ─── error patterns ───────────────────────────────────────────────────────────
# Formulas are shape-conditional by construction: "l"/"w" exist only in
# rectangle samples' values and "s" only in square samples' (area.py never
# sets both), so _eval_error_formula's NameError on the wrong shape is caught
# by base_generator.py's error-pattern loop and that pattern simply doesn't
# fire for that sample -- exactly the intended per-shape gating, with no
# conditional needed here.
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="l + w",
        required_concept="area",
        label="ms_perim_area",
        description="Added side lengths instead of multiplying (used perimeter logic for area).",
    ),
    ErrorPattern(
        formula="2 * (l + w)",
        required_concept="area",
        label="ms_area_perim",
        description="Gave 2*(l+w) instead of l*w (computed perimeter instead of area).",
    ),
    ErrorPattern(
        formula="s + s",
        required_concept="area",
        label="ms_perim_area_square",
        description="Added the two sides instead of multiplying (used perimeter logic for area) on a square.",
    ),
    ErrorPattern(
        formula="4 * s",
        required_concept="area",
        label="ms_area_perim_square",
        description="Gave 4*s instead of s*s (computed perimeter instead of area) on a square.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {
    "number_difficulty": "continuous",
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_AREA = VocabGated(
    requires_vocab="area",
    preferred="area",
    fallback="the number of square units that cover the shape",
)


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Returns side dimensions and the area answer.
    For find_missing_dimension tasks: gives area and one side, answer is the other.
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}
    bounds = _PARAM_BOUNDS["g3"]

    # No silent default. This key used to fall back to "find_area", which meant a
    # node the registry never bound still generated -- plausibly, and wrongly --
    # instead of saying so. mat_g3_mg_q1_2 and mat_g3_mg_q1_3 both rode that
    # default and collapsed onto each other. If this raises, the fix is a binding
    # in registry.py's _parse_competency_bounds, never a default here.
    task_type = profile.get("task_type")
    if not task_type:
        raise ValueError(
            f"area: 'task_type' is not bound for this node "
            f"(grade={grade}, seed={seed}, profile={profile!r}); "
            f"bind it in registry.py _parse_competency_bounds for the competency "
            f"that maps to this node. Expected one of: find_area, "
            f"find_missing_dimension, illustrate_tiles, derive_formula."
        )
    # mat_g3_mg_q1_3 ("Solve problems involving areas") wants both the direct and
    # the inverse task, varying per seed. The registry binds a sentinel because it
    # computes bounds once per node; resolving the choice there would freeze every
    # seed to one task forever. Resolved here against this call's own rng so the
    # split is deterministic per seed.
    if task_type == "find_area_or_missing_dimension":
        task_type = rng.choice(["find_area", "find_missing_dimension"])

    context   = profile.get("context", "pure")
    scalar    = float(profile.get("difficulty_scalar", profile.get("number_difficulty", 0.5)))

    # Every one of the four area competencies names "a square or rectangle" /
    # "squares and rectangles" explicitly. Without an explicit override, vary
    # shape per seed instead of silently defaulting to rectangle every time --
    # blind review found zero square samples across any node because nothing
    # ever selected one.
    shape = profile.get("shape") or rng.choice(["rectangle", "square"])
    # "Given the area and one side, find the other" is a division for a rectangle
    # but a square ROOT for a square, and square roots are not a Grade 3 skill --
    # they appear nowhere in this grade's cumulative vocabulary. The square branch
    # below also never set known_dimension/known_value, so the stem builder fell
    # back to its "?" placeholder and rendered "A square has an area of 25 sq m and
    # a length of ? m. What is its width?" (mat_g3_mg_q1_3, seed 45). Both problems
    # have the same answer: this task is a rectangle task.
    if task_type == "find_missing_dimension":
        shape = "rectangle"
    # mat_g3_mg_q1_2's competency names "sq. cm and sq. m" explicitly; vary
    # unit for find_area/word-problem framings. illustrate_tiles/derive_formula
    # are tile-by-tile counting exercises -- keep those cm-scale, not metres.
    unit = profile.get("unit")
    if unit is None:
        if context == "word_problem" and task_type != "find_missing_dimension":
            # Only the *garden* narration is pinned to metres. A garden measured in
            # centimetres is not a garden -- blind review flagged "gardens at
            # 5 cm x 2 cm, 3 cm per side" as unpicturable, next to the same frame
            # reading naturally in metres.
            #
            # The inverse task is excluded because it renders in the plain frame
            # ("A rectangle has an area of 126 sq cm and a width of 9 cm"), not as
            # a garden, so pinning it too would have made mat_g3_mg_q1_3 render in
            # metres 300 times out of 300 and thrown away half its unit variety
            # for no gain. The pure framings below still carry both units, which
            # is what mat_g3_mg_q1_2's "sq. cm and sq. m" requires.
            unit = "square_m"
        elif task_type in ("illustrate_tiles", "derive_formula"):
            # Tile-counting exercises stay cm-scale -- but only when they are not
            # the narrated garden above. This rule used to come FIRST, so a tiling
            # node's garden was pinned to centimetres before the garden rule could
            # run, and two blind reviewers independently caught the result
            # ("a square garden measuring 5 cm on each side", "2 cm long and 3 cm
            # wide"). Order matters here: the narration decides the unit.
            unit = "square_cm"
        else:
            unit = rng.choice(["square_cm", "square_m"])

    if unit == "square_cm":
        lo, hi = bounds["side_cm_min"], bounds["side_cm_max"]
        if task_type in ("illustrate_tiles", "derive_formula"):
            hi = bounds["side_cm_max_tiling"]
        unit_label = "sq cm"
    else:
        lo, hi = bounds["side_m_min"], bounds["side_m_max"]
        unit_label = "sq m"

    hi = max(lo, int(linear_interpolate(lo, hi, scalar)))

    # The known-table draw governs the dimensions; `lo`/`hi` above still select the
    # unit label and its magnitude band, but they may not widen the multiplication
    # past what G3 Q1 has been taught (see _table_and_cofactor).
    table_side, other_side = _table_and_cofactor(scalar, rng)

    # ── inductive derivation (mat_g3_mg_q1_1) ────────────────────────────────
    # "Explore inductively the derivation of the formulas for the areas of a
    # square and a rectangle using square tile units."
    #
    # This used to reuse find_area's computation and print the rule in the stem
    # ("Using the formula rows x columns, what is the total number of tiles?"),
    # so the pupil only ever APPLIED a supplied rule and the answer was a number.
    # A blind reviewer scored the node FAIL for exactly that: "No sample derives
    # anything... no correct answer is ever a formula, and side x side /
    # length x width are never elicited or named."
    #
    # Induction needs two things the old item had neither of: several cases to
    # generalise from, and a *rule* as the answer object. Note the competency
    # says "formulas", plural -- a square's side x side and a rectangle's
    # length x width are different rules, so the shape decides which is keyed.
    if task_type == "derive_formula":
        if shape == "square":
            # {2,3,4,5} choose 3 is only four case-triples, so seeds collided often
            # (a reviewer found 15 samples collapsing to 11 distinct items). The
            # 10-square is 100 tiles, which is large to picture but is only *read*
            # here -- the pupil induces from stated totals rather than counting -- so
            # it is offered at the top of the difficulty range, taking the pool to
            # ten triples.
            side_pool = [t for t in _KNOWN_TABLES if t <= (5 if scalar < 0.67 else 10)]
            sides = sorted(rng.sample(side_pool, 3))
            cases = [(v, v, v * v) for v in sides]
            answer = "side × side"
            distractors = ["side + side", "4 × side", "side + 4"]
            dims_word = "side"
        else:
            # One dimension held fixed across the cases so the pattern is
            # visible: the other varies, and the total tracks the product.
            # The fixed width may not be 2. At width 2 the distractor
            # "length + length" computes 2 x length, which is exactly length x width
            # for every case shown -- so a pupil who induces faithfully from all the
            # evidence has TWO rules consistent with it and is marked wrong. A blind
            # reviewer caught this on seeds 42 and 601 and scored the node FAIL for
            # it. An inductive item is only well posed if the presented cases
            # falsify every distractor; _assert_cases_determine below enforces that
            # for whatever pool is in play, so a future distractor change cannot
            # quietly reintroduce the ambiguity.
            # Widened past {3,4}: at low difficulty the old pool left six of eight
            # rectangle items pinned to a width of 4, so "the evidence a pupil sees
            # never once varies the width" (blind review). 2 stays excluded for the
            # reason _assert_cases_determine enforces.
            fixed = rng.choice([t for t in _KNOWN_TABLES
                                if t != 2 and t <= (5 if scalar < 0.34 else 10)])
            varying = sorted(rng.sample([v for v in range(2, _OTHER_SIDE_MAX + 1)
                                         if v != fixed], 3))
            cases = [(v, fixed, v * fixed) for v in varying]
            answer = "length × width"
            # No grouping symbols: a bracketed candidate makes the pupil parse
            # notation no stem at this grade uses, which is a reading load rather
            # than a mathematical one (blind review). The perimeter is spelled out
            # instead, so the classic perimeter-for-area confusion is still offered.
            distractors = ["length + width",
                           "length + width + length + width",
                           "length + length"]
            dims_word = "length and width"
        _assert_cases_determine(cases, answer, distractors, seed)
        return {
            "blank_target": "answer",
            "shape": shape,
            "shape_noun": shape,
            "task_type": "derive_formula",
            "cases": cases,
            "answer": answer,
            "distractors": distractors,
            "dims_word": dims_word,
            "unit": unit_label,
            "length_unit": unit_label.replace("sq ", ""),
            "context": context,
        }

    if shape == "square":
        # s * s must itself be a known-table fact, so the side is the table factor.
        s = table_side
        area = s * s
        # No find_missing_dimension branch here: it is redirected to the rectangle
        # path above, because recovering a square's side from its area is a square
        # root. The branch that used to live here returned answer_formula
        # "sqrt(area)" and omitted known_dimension/known_value entirely.
        # illustrate_tiles / derive_formula reuse find_area's computation --
        # they differ only in framing (tile-counting vs. formula-derivation
        # narration), not in the underlying math, matching the competency
        # wording exactly (mat_g3_mg_q1_0: "Illustrate and estimate the area
        # ... using square tile units"; mat_g3_mg_q1_1: "Explore inductively
        # the derivation of the formula[] ... using square tile units").
        return {
            "blank_target": "answer",
            "shape": "square",
            "sides": {"s": s},
            "s": s,  # top-level alias for the area_solve spine template
            "shape_noun": "square",
            # The surface the story tiles follows the unit. A garden measured in
            # centimetres is not a garden -- blind review caught "a square garden
            # measuring 5 cm on each side" -- but the item itself is fine, so the
            # fix is the noun, not the number. A forced `unit` variant bypasses the
            # metres rule above (that is what a forced variant is for), so the noun
            # has to derive from the unit actually in play rather than from context.
            "surface_noun": "garden" if unit_label == "sq m" else "card",
            "dims_phrase": f"measuring {s} {unit_label.replace('sq ', '')} on each side",
            "length_unit": unit_label.replace("sq ", ""),
            "unit": unit_label,
            "task_type": task_type if task_type in ("illustrate_tiles", "derive_formula") else "find_area",
            "answer": area,
            **({"distractors": _estimation_distractors(s, s)}
               if task_type == "illustrate_tiles" else {}),
            "answer_formula": "s * s",
            "context": context,
        }

    # rectangle
    # A "rectangle" sample with l == w renders identically to a square (e.g.
    # "6 rows and 6 columns") -- undermining the very distinction the shape
    # variance above exists to test, and blind review caught it happening
    # (mat_g3_mg_q1_0 seed 44). Walk the co-factor off the table factor rather
    # than redrawing, so the pair stays inside the known tables either way.
    if other_side == table_side:
        other_side = other_side + 1 if other_side < _OTHER_SIDE_MAX else other_side - 1
    # Which of the two is named "length" varies, so the table factor is not always
    # the first dimension read out; the product is a known-table fact regardless.
    if rng.random() < 0.5:
        l, w = table_side, other_side
        table_dim = "l"
    else:
        l, w = other_side, table_side
        table_dim = "w"
    area = l * w
    if task_type == "find_missing_dimension":
        # The divisor must be the table factor: area / table_side is then a
        # `division_tables_2_3_4_5_10` fact. Choosing the side at random here is
        # what produced '44 sq cm ... a width of 22 cm' (44/22), a two-digit
        # divisor that Grade 3 never teaches.
        known = table_dim
        known_val = l if known == "l" else w
        missing_val = w if known == "l" else l
        return {
            "blank_target": "answer",
            "shape": "rectangle",
            "area": area,
            "unit": unit_label,
            "known_dimension": known,
            "known_value": known_val,
            "task_type": "find_missing_dimension",
            "answer": missing_val,
            "answer_formula": "area / known_value",
            "sides": {"l": l, "w": w},
            "l": l, "w": w,
            "context": context,
        }
    return {
        "blank_target": "answer",
        "shape": "rectangle",
        "sides": {"l": l, "w": w},
        "l": l, "w": w, "s": l,  # top-level aliases for spine templates & error formulas
        "shape_noun": "rectangular",
        "surface_noun": "garden" if unit_label == "sq m" else "card",
        "dims_phrase": f"that is {l} {unit_label.replace('sq ', '')} long and {w} {unit_label.replace('sq ', '')} wide",
        "length_unit": unit_label.replace("sq ", ""),
        "unit": unit_label,
        "task_type": task_type if task_type in ("illustrate_tiles", "derive_formula") else "find_area",
        "answer": area,
        **({"distractors": _estimation_distractors(l, w)}
           if task_type == "illustrate_tiles" else {}),
        "answer_formula": "l * w",
        "context": context,
    }


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    area_label = VOCAB_AREA.resolve(cumulative_vocab)
    shape      = values.get("shape", "shape")
    unit       = values.get("unit", "sq cm")
    task_type  = values.get("task_type", "find_area")

    if task_type == "find_missing_dimension":
        known_val = values.get("known_value", "?")
        area      = values.get("area", "?")
        return [
            f"The {area_label} = length × width.",
            f"We know the area is {area} {unit} and one side is {known_val}.",
            f"Divide: {area} ÷ {known_val} = {values['answer']}.",
        ]

    sides = values.get("sides", {})
    hints = [f"The {area_label} tells us how many unit squares cover the shape."]

    if shape == "square":
        s = sides.get("s", "?")
        hints.append(f"Area of a square = side × side = {s} × {s} = {values['answer']} {unit}.")
    else:
        l, w = sides.get("l", "?"), sides.get("w", "?")
        hints.append(f"Area of a rectangle = length × width = {l} × {w} = {values['answer']} {unit}.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

AREA_DNA = DNA(
    concept="area",
    dna_type="algorithmic",
    answer_formula="answer",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "cloze", "numeric_input", "grid_area"],
    requires_context=True,
    visual_home="GridArea",
    difficulty_axes=_DIFFICULTY_AXES,
)
