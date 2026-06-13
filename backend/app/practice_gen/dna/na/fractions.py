"""
DNA: Fractions (Number & Algebra)

Refactored from:
  - matatag_skeletons.py  (fractions generator + fr_* traps)
  - matatag_dimensions.py (FRACTIONS_DIMENSIONS)

Covers MATATAG grades 1–3 fractions competencies:
  G1 — halves and fourths only; area model identification
  G2 — unit fractions and similar proper fractions (denominators 2–8)
  G3 — fractions ≥ 1 (improper / mixed numbers); add/subtract similar fractions
"""

from __future__ import annotations

import random
from math import gcd
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.app.practice_gen.dna.base import (
    DNA,
    ErrorPattern,
    VocabGated,
)


# ─── grade-gated denominator pools ───────────────────────────────────────────
_DENOM_POOLS: Dict[str, List[int]] = {
    "g1": [2, 4],
    "g2": [2, 3, 4, 5, 6, 8],
    "g3": [2, 3, 4, 5, 6, 8, 10],
}


# ─── param bounds ─────────────────────────────────────────────────────────────
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g1": {"denom_pool": [2, 4],          "max_numerator": 1,  "allow_mixed": False, "allow_ops": False},
    "g2": {"denom_pool": [2, 3, 4, 5, 6, 8], "max_numerator": 7, "allow_mixed": False, "allow_ops": False},
    "g3": {"denom_pool": [2, 3, 4, 5, 6, 8, 10], "max_numerator": 9, "allow_mixed": True,  "allow_ops": True},
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="denominator",
        required_concept="fractions",
        label="fr_swap_nd",
        description="Swapped numerator and denominator.",
    ),
    ErrorPattern(
        formula="(a_num + b_num) / (a_den + b_den)",
        required_concept="fractions",
        label="fr_add_both",
        description="Added numerators AND denominators separately.",
    ),
    ErrorPattern(
        formula="max(a_num, b_num)",
        required_concept="fractions",
        label="fr_big_num",
        description="Compared only numerators; chose the larger numerator as the bigger fraction.",
    ),
    ErrorPattern(
        formula="1 / min(a_den, b_den)",
        required_concept="fractions",
        label="fr_big_den",
        description="Assumed a larger denominator means a larger fraction.",
    ),
    ErrorPattern(
        formula="(a_num + b_num) / (a_den + 1)",
        required_concept="fractions",
        label="fr_not_simp",
        description="Added numerators correctly but used wrong denominator (off by one).",
    ),
    ErrorPattern(
        formula="denominator + numerator",
        required_concept="fractions",
        label="fr_unit_rev",
        description="Confused unit fraction ordering; added numerator and denominator instead of computing correctly.",
    ),
    ErrorPattern(
        formula="numerator - 1",
        required_concept="mixed_number",
        label="fr_imp_mix",
        description="Wrong improper-to-mixed conversion; subtracted 1 from numerator.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {
    "fraction_type":  ["unit_fraction", "similar_proper", "mixed_number"],
    "fraction_model": ["area_model", "set_model", "number_line"],
    "operation":      ["identify_name", "compare", "add_subtract"],
    "number_difficulty": "continuous",
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_NUMERATOR   = VocabGated(requires_vocab="numerator",        preferred="numerator",        fallback="top number")
VOCAB_DENOMINATOR = VocabGated(requires_vocab="denominator",      preferred="denominator",      fallback="bottom number")
VOCAB_FRACTION    = VocabGated(requires_vocab="fraction",         preferred="fraction",         fallback="part of a whole")
VOCAB_UNIT_FRAC   = VocabGated(requires_vocab="unit fraction",    preferred="unit fraction",    fallback="fraction with 1 on top")
VOCAB_MIXED       = VocabGated(requires_vocab="mixed number",     preferred="mixed number",     fallback="whole number and a fraction part")
VOCAB_IMPROPER    = VocabGated(requires_vocab="improper fraction",preferred="improper fraction",fallback="fraction where the top number is bigger than the bottom")


# ─── helpers ──────────────────────────────────────────────────────────────────

def _fraction_str(num: int, den: int) -> str:
    return f"{num}/{den}"


def _simplify(num: int, den: int) -> Tuple[int, int]:
    g = gcd(num, den)
    return num // g, den // g


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, str]],
    seed: int,
) -> Dict[str, Any]:
    """
    Rejection-sample a fraction (or pair of fractions) matching difficulty_profile.

    Returns:
        numerator   : int
        denominator : int
        fraction_str: str          e.g. "3/4"
        model_type  : str          "area_model" | "set_model" | "number_line"
        # For add/subtract operations, also:
        a_num, a_den, b_num, b_den, result_num, result_den: int
        operation   : str
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    g_key      = f"g{max(1, min(grade, 3))}"
    bounds     = _PARAM_BOUNDS[g_key]
    denom_pool = bounds["denom_pool"]
    allow_mixed = bounds["allow_mixed"]
    allow_ops   = bounds["allow_ops"]

    frac_type  = profile.get("fraction_type",  "unit_fraction")
    model_type = profile.get("fraction_model", "area_model")
    operation  = profile.get("operation",      "identify_name")
    num_diff_scalar = float(profile.get("number_difficulty", 0.5))

    # Grade guard: demote unsupported axes
    if not allow_mixed and frac_type == "mixed_number":
        frac_type = "similar_proper"
    if not allow_ops and operation == "add_subtract":
        operation = "compare"

    candidate_params = []

    for den in denom_pool:
        # Gather possibilities for num
        if frac_type == "unit_fraction":
            num_choices = [1]
        elif frac_type == "similar_proper":
            num_choices = list(range(1, den))
        else:  # mixed_number
            num_choices = []
            for whole in range(1, 4):  # keeping max whole 3
                if den > 1:
                    for part in range(1, den):
                        num_choices.append(whole * den + part)
                else:
                    num_choices.append(whole * den)
        
        for num in num_choices:
            if num == 0:
                continue

            frac_s = _fraction_str(num, den)

            if operation != "add_subtract":
                candidate_params.append({
                    "numerator":    num,
                    "denominator":  den,
                    "fraction_str": frac_s,
                    "model_type":   model_type,
                    "operation":    operation,
                    "a_num":        num,
                    "a_den":        den,
                    "b_num":        min(den - 1, num + 1) if den > 1 else num + 1,
                    "b_den":        den,
                })
            else:
                for b_num in range(1, den):
                    if b_num == 0:
                        continue
                    
                    result_num_raw = num + b_num
                    r_num, r_den   = _simplify(result_num_raw, den)

                    candidate_params.append({
                        "numerator":    num,
                        "denominator":  den,
                        "fraction_str": frac_s,
                        "model_type":   model_type,
                        "operation":    operation,
                        "a_num":        num,
                        "a_den":        den,
                        "b_num":        b_num,
                        "b_den":        den,
                        "result_num":   r_num,
                        "result_den":   r_den,
                    })

    if not candidate_params:
        raise RuntimeError(
            f"generate_params (fractions): no valid fraction found for grade={grade}, "
            f"profile={difficulty_profile}."
        )

    # Convert candidate_params to formats for window sampling
    from backend.app.practice_gen.generators.number_difficulty import generate_number_by_window, generate_pair_by_window
    
    if operation != "add_subtract":
        candidates = [(cp["numerator"], cp["denominator"]) for cp in candidate_params]
        max_den = max(denom_pool)
        selected_frac = generate_number_by_window(candidates, num_diff_scalar, d=5, rng=rng, num_type="fraction", max_den=max_den)
        for cp in candidate_params:
            if (cp["numerator"], cp["denominator"]) == selected_frac:
                return cp
    else:
        candidate_pairs = [((cp["a_num"], cp["a_den"]), (cp["b_num"], cp["b_den"])) for cp in candidate_params]
        max_den = max(denom_pool)
        selected_pair = generate_pair_by_window(candidate_pairs, num_diff_scalar, d=5, rng=rng, num_type="fraction", max_den=max_den)
        for cp in candidate_params:
            if ((cp["a_num"], cp["a_den"]), (cp["b_num"], cp["b_den"])) == selected_pair:
                return cp

    return candidate_params[0]


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hint strings for the given fractions problem."""
    num       = values["numerator"]
    den       = values["denominator"]
    operation = values.get("operation", "identify_name")
    model     = values.get("model_type", "area_model")

    frac_lbl  = VOCAB_FRACTION.resolve(cumulative_vocab)
    num_lbl   = VOCAB_NUMERATOR.resolve(cumulative_vocab)
    den_lbl   = VOCAB_DENOMINATOR.resolve(cumulative_vocab)

    if operation == "identify_name":
        return [
            f"A {frac_lbl} shows how many equal parts are shaded out of the total.",
            f"The {den_lbl} (bottom number) tells the total equal parts: {den}.",
            f"The {num_lbl} (top number) tells how many parts are taken: {num}.",
            f"So the {frac_lbl} is {num}/{den}.",
        ]

    if operation == "compare":
        other_num = values.get("b_num", num - 1 if num > 1 else num + 1)
        other_den = values.get("b_den", den)
        return [
            f"To compare {num}/{den} and {other_num}/{other_den}, check if the {den_lbl}s are equal.",
            f"When {den_lbl}s are the same, the {frac_lbl} with the bigger {num_lbl} is larger.",
            f"{num} vs {other_num}: the larger top number gives the larger {frac_lbl}.",
        ]

    # add_subtract
    a_num = values.get("a_num", num)
    b_num = values.get("b_num", 0)
    r_num = values.get("result_num", a_num + b_num)
    r_den = values.get("result_den", den)
    return [
        f"When adding {frac_lbl}s with the same {den_lbl}, keep the {den_lbl} the same.",
        f"Add only the {num_lbl}s: {a_num} + {b_num} = {a_num + b_num}.",
        f"Write the result over the same {den_lbl}: {a_num + b_num}/{den}.",
        f"Simplify if needed: the answer is {r_num}/{r_den}.",
    ]


# ─── DNA instance ─────────────────────────────────────────────────────────────

FRACTIONS_DNA = DNA(
    concept="fractions",
    dna_type="formula",
    answer_formula="numerator / denominator",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=[
        "mcq",
        "cloze",
        "numeric_input",
        "fraction_model_read",
        "fraction_shade",
    ],
    requires_context=False,
    visual_home="FractionModel",
    difficulty_axes=_DIFFICULTY_AXES,
)
