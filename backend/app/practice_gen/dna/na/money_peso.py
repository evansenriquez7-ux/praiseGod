"""
DNA: Money / Philippine Peso (Number & Algebra)

Covers MATATAG grades 1–3 money competencies:
  G1 — coins only up to ₱100, no centavos (₱1, ₱5, ₱10, ₱20, ₱50, ₱100)
  G2 — coins + bills up to ₱1000, centavos allowed
  G3 — all Philippine currency up to ₱10000
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set

from backend.app.practice_gen.dna.base import (
    DNA,
    ErrorPattern,
    VocabGated,
)


# ─── Philippine currency denominations ────────────────────────────────────────
# G1: coins only, no centavos
_DENOMS_G1 = [1, 5, 10, 20, 50, 100]

# G2: coins + small bills, centavos allowed (stored as centavos integer: 25 = ₱0.25)
_DENOMS_G2_PESOS    = [1, 5, 10, 20, 50, 100, 200, 500, 1000]
_DENOMS_G2_CENTAVOS = [25, 50]  # ₱0.25, ₱0.50 in centavo units

# G3: all (same as G2 but up to ₱1000 bills)
_DENOMS_G3_PESOS    = [1, 5, 10, 20, 50, 100, 200, 500, 1000]


# ─── param bounds ─────────────────────────────────────────────────────────────
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g1": {"max_total": 100,   "max_items": 4, "allow_centavos": False},
    "g2": {"max_total": 1000,  "max_items": 5, "allow_centavos": True},
    "g3": {"max_total": 10000, "max_items": 6, "allow_centavos": True},
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="total - amounts[0]",
        required_concept="money_peso",
        label="ar_wrong_op",
        description="Subtracted first amount instead of adding all amounts.",
    ),
    ErrorPattern(
        formula="total + 1",
        required_concept="money_peso",
        label="ar_off_one",
        description="Off by one peso in the total.",
    ),
    ErrorPattern(
        formula="total - 10",
        required_concept="money_peso",
        label="ar_no_regroup",
        description="Forgot to carry when summing amounts crossing a ten.",
    ),
    ErrorPattern(
        formula="total * 10",
        required_concept="money_peso",
        label="ms_conv_dir",
        description="Confused denomination units (e.g., treated centavos as pesos).",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {
    "number_difficulty": "continuous",
}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_CENTAVO      = VocabGated(requires_vocab="centavo",      preferred="centavo",      fallback="small coin")
VOCAB_DENOMINATION = VocabGated(requires_vocab="denomination", preferred="denomination", fallback="type of coin or bill")
VOCAB_CHANGE       = VocabGated(requires_vocab="change",       preferred="change",       fallback="money back")
VOCAB_PESO         = VocabGated(requires_vocab="peso",         preferred="peso",         fallback="₱")


# ─── number-to-words helper ───────────────────────────────────────────────────
_ONES = [
    "", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen",
]
_TENS = [
    "", "", "twenty", "thirty", "forty", "fifty",
    "sixty", "seventy", "eighty", "ninety",
]

def num_to_words(n: int) -> str:
    if n <= 0 or n > 10000:
        return str(n)
    if n == 10000:
        return "ten thousand"
    parts = []
    thousands = n // 1000
    remainder = n % 1000
    if thousands:
        parts.append(f"{_ONES[thousands]} thousand")
    hundreds = remainder // 100
    remainder = remainder % 100
    if hundreds:
        parts.append(f"{_ONES[hundreds]} hundred")
    if remainder > 0:
        if remainder < 20:
            parts.append(_ONES[remainder])
        else:
            tens = remainder // 10
            ones = remainder % 10
            chunk = _TENS[tens]
            if ones:
                chunk = f"{chunk}-{_ONES[ones]}"
            parts.append(chunk)
    return " ".join(parts)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _pick_amounts(
    rng: random.Random,
    denominations: List[int],
    max_total: int,
    max_items: int,
) -> List[int]:
    """Pick a list of denomination values that sum within max_total."""
    for _ in range(200):
        n = rng.randint(2, max_items)
        chosen = [rng.choice(denominations) for _ in range(n)]
        if sum(chosen) <= max_total:
            return chosen
    # Fallback: two smallest denoms
    return [denominations[0], denominations[0]]


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Generate a money problem for the given grade.
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    g_key = f"g{max(1, min(grade, 3))}"
    bounds = _PARAM_BOUNDS[g_key]
    max_items      = bounds["max_items"]
    allow_centavos = bounds["allow_centavos"]

    context = profile.get("context", "pure")
    spine = profile.get("spine", None)

    max_total_prof = profile.get("max_total")
    if max_total_prof is None:
        from backend.app.practice_gen.dna.base import log_interpolate
        diff_scalar = float(profile.get("difficulty_scalar", profile.get("number_difficulty", 0.5)))
        max_total = int(log_interpolate(10, bounds["max_total"], diff_scalar))
    elif isinstance(max_total_prof, (int, float)):
        max_total = int(max_total_prof)
    elif isinstance(max_total_prof, str):
        legacy_map = {"up_to_100": 100, "up_to_1000": 1000, "up_to_10000": 10000}
        max_total = legacy_map.get(max_total_prof, 100)
    else:
        max_total = 100

    max_total = max(20, min(max_total, 10000))

    operation = profile.get("operation", "add_amounts")
    denom_type = profile.get("denomination_type", "mixed")
    num_diff_scalar = float(profile.get("number_difficulty", 0.5))

    if grade == 1 or not allow_centavos:
        denom_pool = _DENOMS_G1
    else:
        denom_pool = _DENOMS_G3_PESOS

    if denom_type == "coins_only":
        denom_pool = [d for d in denom_pool if d <= 20]
        if not denom_pool:
            denom_pool = [1, 5, 10]
    elif denom_type == "bills_only":
        denom_pool = [d for d in denom_pool if d >= 20]
        if not denom_pool:
            denom_pool = [20, 50, 100]

    candidates = []
    for _ in range(500):
        n = rng.randint(2, max_items)
        if context == "word_problem":
            n = 2
        chosen = [rng.choice(denom_pool) for _ in range(n)]
        t = sum(chosen)
        if t <= max_total:
            candidates.append((t, chosen))
    
    if not candidates:
        t = denom_pool[0] * 2
        candidates.append((t, [denom_pool[0], denom_pool[0]]))

    candidate_pairs = [(c[0], 0) for c in candidates]
    from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window
    selected_pair = generate_pair_by_window(candidate_pairs, num_diff_scalar, d=5, rng=rng)
    
    matching = [c for c in candidates if c[0] == selected_pair[0]]
    selected_c = rng.choice(matching)
    amounts = selected_c[1]
    total = selected_c[0]

    if operation == "compare":
        t1, amounts1 = total, amounts
        other_candidates = [c for c in candidates if c[0] != t1]
        if not other_candidates:
            other_candidates = [(t1 + 10, [10])]
        selected_other = rng.choice(other_candidates)
        t2, amounts2 = selected_other[0], selected_other[1]

        third_candidates = [c for c in candidates if c[0] != t1 and c[0] != t2]
        if not third_candidates:
            third_candidates = [(t1 + t2 + 10, [10, 10])]
        selected_third = rng.choice(third_candidates)
        amounts3 = selected_third[1]

        def get_desc(amts):
            from collections import Counter
            counts = Counter(amts)
            parts = []
            for denom in sorted(counts.keys(), reverse=True):
                count = counts[denom]
                is_bill = denom >= 20
                unit = "bill" if is_bill else "coin"
                if count > 1:
                    unit += "s"
                parts.append(f"{count} ₱{denom} {unit}")
            if len(parts) == 1:
                return parts[0]
            elif len(parts) == 2:
                return f"{parts[0]} and {parts[1]}"
            else:
                return ", ".join(parts[:-1]) + f", and {parts[-1]}"

        desc1 = get_desc(amounts1)
        desc2 = get_desc(amounts2)
        desc3 = get_desc(amounts3)

        question = f"Which has a greater value: {desc1} or {desc2}?"
        if t1 > t2:
            correct_ans = desc1
            distractors = [desc2, "They are equal", desc3]
        else:
            correct_ans = desc2
            distractors = [desc1, "They are equal", desc3]

        return {
        "blank_target": "answer",
            "amounts": amounts1,
            "total": t1,
            "operation": "compare",
            "context": context,
            "question": question,
            "answer": correct_ans,
            "distractors": distractors
        }

    elif operation == "read_write":
        task = rng.choice(["words_to_numeral", "numeral_to_words", "symbols"])
        if grade == 1:
            total_rw = rng.choice([5, 10, 20, 50, 100])
        elif grade == 2:
            total_rw = rng.choice([20, 50, 100, 200, 500, 1000])
        else:
            total_rw = rng.randint(20, 9999)

        if task == "numeral_to_words":
            words = num_to_words(total_rw)
            question = f"How is ₱{total_rw} written in words?"
            correct_ans = f"{words} pesos"
            wrong_total1 = total_rw + rng.choice([10, 5, 20, 100])
            wrong_total2 = total_rw - rng.choice([10, 5, 2, 50])
            if wrong_total2 <= 0:
                wrong_total2 = total_rw + 50
            distractors = [
                f"{num_to_words(wrong_total1)} pesos",
                f"{num_to_words(wrong_total2)} pesos",
                f"{words} centavos"
            ]
        elif task == "words_to_numeral":
            words = num_to_words(total_rw)
            question = f"How is '{words} pesos' written using the peso symbol?"
            correct_ans = f"₱{total_rw}"
            distractors = [
                f"₱{total_rw * 10}",
                f"₱{total_rw - 5 if total_rw > 5 else total_rw + 5}",
                f"{total_rw}¢"
            ]
        else: # symbols
            if grade == 3:
                cent_choice = rng.choice([25, 50])
                question = f"How is {cent_choice} centavos written as a decimal of a peso using the ₱ symbol?"
                correct_ans = f"₱0.{cent_choice}"
                distractors = [
                    f"₱{cent_choice}",
                    f"₱0.0{cent_choice}",
                    f"{cent_choice}¢"
                ]
            else:
                question = f"How is ₱{total_rw} written using the currency code PhP?"
                correct_ans = f"PhP {total_rw}"
                distractors = [
                    f"₱{total_rw}",
                    f"PhP{total_rw}c",
                    f"{total_rw} PhP"
                ]
        return {
        "blank_target": "answer",
            "amounts": [total_rw],
            "total": total_rw,
            "operation": "read_write",
            "context": context,
            "question": question,
            "answer": correct_ans,
            "distractors": distractors
        }

    result_dict = {
        "blank_target": "answer",
        "amounts":            amounts,
        "denominations_used": amounts,
        "total":              total,
        "operation":          operation,
        "context":            context,
    }

    if operation == "find_change":
        # For find_change: the two amounts represent paid & cost;
        # the answer is the change = paid - cost.
        paid = max(amounts[0], amounts[1]) if len(amounts) >= 2 else amounts[0]
        cost = min(amounts[0], amounts[1]) if len(amounts) >= 2 else 0
        change = paid - cost
        if change <= 0:
            # Ensure paid > cost by forcing it
            cost = paid - rng.randint(1, max(1, paid - 1))
            change = paid - cost
        result_dict["a"] = paid
        result_dict["b"] = cost
        result_dict["result"] = change
        result_dict["amounts"] = [paid, cost]  # override amounts so hints are correct
    else:
        # add_amounts / identify_value: correct answer is the sum (total)
        result_dict["result"] = total
        result_dict["a"] = amounts[0] if amounts else 0
        result_dict["b"] = amounts[1] if len(amounts) > 1 else amounts[0] if amounts else 0

    return result_dict


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hints for the given money problem."""
    amounts   = values["amounts"]
    total     = values["total"]
    operation = values["operation"]

    peso_label   = VOCAB_PESO.resolve(cumulative_vocab)
    change_label = VOCAB_CHANGE.resolve(cumulative_vocab)

    hints: List[str] = []
    
    if operation == "compare":
        hints.append("Find the total value of the first group of money.")
        hints.append("Find the total value of the second group of money.")
        hints.append("Compare the two values to see which one is greater.")
        return hints

    if operation == "read_write":
        hints.append("Read the number or words given in the question carefully.")
        hints.append("Think about the spelling of number words or the position of the currency symbol.")
        hints.append("Remember that pesos use ₱ or PhP, and centavos can be written as a decimal.")
        return hints

    hints.append(f"You have these amounts: {[f'{peso_label}{a}' for a in amounts]}.")

    if operation == "add_amounts":
        running = 0
        for i, amt in enumerate(amounts):
            running += amt
            hints.append(f"Step {i + 1}: Add {peso_label}{amt} → running total = {peso_label}{running}.")
        hints.append(f"The total is {peso_label}{total}.")
    elif operation == "find_change":
        paid = amounts[0]
        cost = amounts[1] if len(amounts) > 1 else total
        chg  = paid - cost
        hints.append(f"You paid {peso_label}{paid} for an item that costs {peso_label}{cost}.")
        hints.append(f"{change_label.capitalize()} = {peso_label}{paid} − {peso_label}{cost} = {peso_label}{chg}.")
    else:  # identify_value
        hints.append(f"Look at each {VOCAB_DENOMINATION.resolve(cumulative_vocab)} shown.")
        hints.append(f"Count the total: {' + '.join(str(a) for a in amounts)} = {total}.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

MONEY_PESO_DNA = DNA(
    concept="money_peso",
    dna_type="formula",
    answer_formula="sum(amounts)",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=[
        "mcq",
        "cloze",
        "numeric_input",
        "peso_money_read",
        "peso_money_build",
    ],
    requires_context=True,
    visual_home="PesoMoney",
    difficulty_axes=_DIFFICULTY_AXES,
)
