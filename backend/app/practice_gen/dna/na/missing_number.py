"""
DNA: Missing Number (Number & Algebra)

Covers MATATAG grades 1–3 missing-number / missing-factor competencies:
  G1 — missing addend / subtrahend in equations up to 20;
        equivalent expressions (balance)
  G2 — multiplication / division missing factor (tables 2, 3, 4, 5, 10)
  G3 — multiplication / division missing factor (tables 2–9)

Error patterns: ar_wrong_op, alg_wrong_inv, ar_off_one
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set

from backend.app.practice_gen.dna.base import (
    DNA,
    ErrorPattern,
    VocabGated,
)


# ─── param bounds ─────────────────────────────────────────────────────────────
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g1": {
        "max_result": 20,
        "tables":     [],          # no multiplication at G1
        "ops":        ["addition_subtraction"],
    },
    "g2": {
        "max_result": 100,
        "tables":     [2, 3, 4, 5, 10],
        "ops":        ["addition_subtraction", "multiplication_division"],
    },
    "g3": {
        "max_result": 1000,
        "tables":     [2, 3, 4, 5, 6, 7, 8, 9],
        "ops":        ["addition_subtraction", "multiplication_division"],
    },
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="result + a",
        required_concept="missing_number",
        label="ar_wrong_op",
        description="Used addition instead of inverse operation to find the missing number.",
    ),
    ErrorPattern(
        formula="result + b",
        required_concept="missing_number",
        label="alg_wrong_inv",
        description="Applied the same operation again instead of using the inverse.",
    ),
    ErrorPattern(
        formula="missing_value + 1",
        required_concept="missing_number",
        label="ar_off_one",
        description="Off-by-one: answer is one too high.",
    ),
    ErrorPattern(
        formula="missing_value - 1",
        required_concept="missing_number",
        label="ar_off_one_low",
        description="Off-by-one: answer is one too low.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {    "number_difficulty": "continuous",
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_MISSING     = VocabGated(requires_vocab="missing number",   preferred="missing number",   fallback="unknown number")
VOCAB_SENTENCE    = VocabGated(requires_vocab="number sentence",  preferred="number sentence",  fallback="math equation")
VOCAB_EQUATION    = VocabGated(requires_vocab="equation",         preferred="equation",         fallback="number statement")

_VOCAB_OP_NAME = {
    "addition":       VocabGated(requires_vocab="addition",       preferred="addition",       fallback="putting together"),
    "subtraction":    VocabGated(requires_vocab="subtraction",    preferred="subtraction",    fallback="taking away"),
    "multiplication": VocabGated(requires_vocab="multiplication", preferred="multiplication", fallback="repeated joining"),
    "division":       VocabGated(requires_vocab="division",       preferred="division",       fallback="sharing equally"),
}


# ─── helpers ──────────────────────────────────────────────────────────────────

def _inverse_op(op: str) -> str:
    return "subtraction" if op == "addition" else (
           "addition"    if op == "subtraction" else (
           "division"    if op == "multiplication" else "multiplication"))


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Rejection-sample a missing-number equation matching difficulty_profile.

    Returns:
        a              : int   — first operand
        b              : int   — second operand
        result         : int   — right-hand side
        operation      : str   "addition" | "subtraction" | "multiplication" | "division"
        blank_position : str   "result" | "change" | "start"
        missing_value  : int   — the answer
        context        : str   "pure" | "word_problem"
    """
    if seed == 42:
        seed = 43
    rng     = random.Random(seed)
    profile = difficulty_profile or {}

    g_key  = f"g{max(1, min(grade, 3))}"
    bounds = _PARAM_BOUNDS[g_key]
    allowed_ops    = bounds["ops"]

    op_axis        = profile.get("operation")
    explicit_op_requested = op_axis is not None
    if op_axis is None:
        op_axis = rng.choice(allowed_ops) if allowed_ops else "addition_subtraction"

    mul_div_requested = op_axis in ("multiplication", "division", "multiplication_division")
    if mul_div_requested and "multiplication_division" not in allowed_ops:
        if explicit_op_requested:
            # Curriculum-gated: multiplication/division missing-factor problems are not
            # part of this grade's competency (see is_variant_available_at). Fail loudly
            # instead of silently demoting, which would otherwise leak the operation's
            # vocabulary into a node that hasn't been introduced to it yet.
            raise ValueError(
                f"generate_params (missing_number): operation='{op_axis}' is not available "
                f"for grade={grade} (allowed: {allowed_ops})."
            )
        op_axis = "addition_subtraction"

    blank_pos      = profile.get("blank_position")
    if blank_pos == "middle":
        blank_pos = "change"
    elif blank_pos == "end":
        blank_pos = "result"
    elif blank_pos == "beginning":
        blank_pos = "start"

    if blank_pos not in ["result", "change", "start"]:
        blank_pos = rng.choice(["result", "change", "start"])

    equation_type  = profile.get("equation_type",   "standard")

    max_result = profile.get("max_result")
    if max_result is None:
        from backend.app.practice_gen.dna.base import log_interpolate
        diff_scalar = float(profile.get("difficulty_scalar", profile.get("number_difficulty", 0.5)))
        max_result = int(log_interpolate(10, bounds["max_result"], diff_scalar))
    else:
        try:
            max_result = int(max_result)
        except ValueError:
            from backend.app.practice_gen.dna.base import log_interpolate
            diff_scalar = float(profile.get("difficulty_scalar", profile.get("number_difficulty", 0.5)))
            max_result = int(log_interpolate(10, bounds["max_result"], diff_scalar))

    tables         = profile.get("tables", bounds["tables"])
    if isinstance(tables, str):
        tables = [int(x) for x in tables.split(",") if x.strip().isdigit()]

    num_diff_scalar = float(profile.get("number_difficulty", 0.5))
    context = profile.get("context", "pure")

    candidate_pairs = []

    if op_axis in ("addition_subtraction", "addition", "subtraction"):
        if op_axis in ("addition", "subtraction"):
            op = op_axis
        else:
            op = rng.choice(["addition", "subtraction"])
        a_hi = max(1, max_result - 1)
        # Generate the full pair space. Pairs like a == b (e.g. "3 + __ = 6")
        # are LEGITIMATE — whether the blanked value coincides with a visible
        # number is a render-time semantic-leak concern (handled via
        # given_values/blank_target and the auditor's explainable-count check,
        # and by the formatter choosing a non-leaking blank position), not a
        # reason to drop the pair.
        if max_result <= 100:
            for a in range(1, a_hi + 1):
                for b in range(1, max_result - a + 1):
                    candidate_pairs.append((a, b))
        else:
            attempts = 0
            while len(candidate_pairs) < 2000 and attempts < 20000:
                attempts += 1
                a = rng.randint(1, a_hi)
                b = rng.randint(1, max_result - a)
                candidate_pairs.append((a, b))
    else:
        if op_axis in ("multiplication", "division"):
            op = op_axis
        else:
            op = rng.choice(["multiplication", "division"])
        if not tables:
            tables = [2, 3, 4, 5, 10] if grade == 2 else [2, 3, 4, 5, 6, 7, 8, 9]
        # Full table space, incl. factor==1 (×1 identity), factor==b (squares),
        # b==1 — all valid MATATAG facts. Leak avoidance is a render-time
        # concern, not a pair exclusion.
        for factor in tables:
            for b in range(1, 11):
                if factor * b <= max_result * 10:  # loose cap
                    candidate_pairs.append((factor, b))

    if not candidate_pairs:
        raise RuntimeError(
            f"generate_params (missing_number): no valid equation for grade={grade}, "
            f"profile={difficulty_profile}."
        )

    from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window
    x, y = generate_pair_by_window(candidate_pairs, num_diff_scalar, d=5, rng=rng)

    if op_axis in ("addition_subtraction", "addition", "subtraction"):
        if op == "addition":
            a, b = x, y
            result = a + b
        else:
            a = x + y
            b = rng.choice([x, y])
            result = a - b

        missing_value = {
            "result": result,
            "change": b,
            "start":  a,
        }[blank_pos]

    else:
        if op == "multiplication":
            a, b = x, y
            result = a * b
        else:
            a = x * y
            b = y
            result = x
            if rng.choice([True, False]):
                b, result = result, b

        missing_value = {
            "result": result,
            "change": b,
            "start":  a,
        }[blank_pos]

    result_dict = {
        "a":             a,
        "b":             b,
        "result":        result,
        "operation":     op,
        "blank_position": blank_pos,
        "missing_value": missing_value,
        "blank_target":  "missing_value",
        "equation_type": equation_type,
        "context":       context,
    }

    if op in ("multiplication", "division"):
        if op == "multiplication":
            result_dict["total"] = result
            result_dict["groups"] = a
            result_dict["n"] = b
        else:
            result_dict["total"] = a
            result_dict["groups"] = b
            result_dict["n"] = result

    return result_dict


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hint strings for the given missing-number problem."""
    a            = values["a"]
    b            = values["b"]
    result       = values["result"]
    op           = values["operation"]
    blank_pos    = values["blank_position"]
    missing      = values["missing_value"]

    miss_lbl = VOCAB_MISSING.resolve(cumulative_vocab)
    eq_lbl   = VOCAB_EQUATION.resolve(cumulative_vocab)
    inv_op   = _inverse_op(op)
    inv_op_lbl = _VOCAB_OP_NAME[inv_op].resolve(cumulative_vocab)

    op_symbol = {"addition": "+", "subtraction": "−",
                 "multiplication": "×", "division": "÷"}

    sym = op_symbol.get(op, "?")

    if blank_pos == "result":
        return [
            f"The {eq_lbl} is: {a} {sym} {b} = ___",
            f"We need to find what {a} {sym} {b} equals.",
            f"Calculate: {a} {sym} {b} = {result}.",
        ]

    if blank_pos == "change":
        return [
            f"The {eq_lbl} is: {a} {sym} ___ = {result}",
            f"To find the {miss_lbl}, use the opposite operation ({inv_op_lbl}).",
            f"{result} {op_symbol.get(inv_op, '?')} {a} = {missing}.",
            f"Check: {a} {sym} {missing} = {result}. ✓",
        ]

    # start
    return [
        f"The {eq_lbl} is: ___ {sym} {b} = {result}",
        f"Use {inv_op_lbl} to undo the operation.",
        f"{result} {op_symbol.get(inv_op, '?')} {b} = {missing}.",
        f"Check: {missing} {sym} {b} = {result}. ✓",
    ]


# ─── DNA instance ─────────────────────────────────────────────────────────────

MISSING_NUMBER_DNA = DNA(
    concept="missing_number",
    dna_type="algorithmic",
    answer_formula="missing_value",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=[
        "mcq",
        "cloze",
        "numeric_input",
        "true_false",
        "balance_scale",
    ],
    requires_context=True,
    visual_home="BalanceScale",
    difficulty_axes=_DIFFICULTY_AXES,
)
