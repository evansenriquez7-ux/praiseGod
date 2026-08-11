"""
DNA: Comparing and Ordering Numbers (Number & Algebra)

Covers MATATAG grades 1–3 comparison competencies:
  G1 — compare two numbers up to 20; order sets up to 100
  G2 — compare/order up to 1000
  G3 — compare/order up to 10000; explicit >, <, = symbol use
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
    "g1": {"max_value": 100,   "set_size": (2, 4)},
    "g2": {"max_value": 1000,  "set_size": (2, 5)},
    "g3": {"max_value": 10000, "set_size": (3, 6)},
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="numbers[1]",
        required_concept="comparing_ordering",
        label="cnt_ord_off",
        description="Off by one position when ordering — picked the adjacent value.",
    ),
    ErrorPattern(
        formula="numbers[0] // 10",
        required_concept="comparing_ordering",
        label="pv_dig_val",
        description="Compared the tens digit value instead of full place value.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {"number_difficulty": "continuous"}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_GT    = VocabGated(requires_vocab="greater than", preferred="greater than", fallback="bigger than")
VOCAB_LT    = VocabGated(requires_vocab="less than",    preferred="less than",    fallback="smaller than")
VOCAB_EQ    = VocabGated(requires_vocab="equal to",     preferred="equal to",     fallback="the same as")
VOCAB_GT_SY = VocabGated(requires_vocab=">",            preferred=">",            fallback="is more")
VOCAB_LT_SY = VocabGated(requires_vocab="<",            preferred="<",            fallback="is less")
VOCAB_EQ_SY = VocabGated(requires_vocab="=",            preferred="=",            fallback="equals")


# ─── helpers ──────────────────────────────────────────────────────────────────

def _compare_symbol(a: int, b: int) -> str:
    if a > b:
        return ">"
    if a < b:
        return "<"
    return "="


def _close_pair(rng: random.Random, max_val: int) -> tuple:
    """Return two numbers that differ by at most 5% of max_val (min gap 1)."""
    gap = max(1, max_val // 20)
    a = rng.randint(1, max_val - gap)
    b = a + rng.randint(1, gap)
    return (a, b) if rng.random() < 0.5 else (b, a)


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Generate a comparison/ordering problem.
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    g_key = f"g{max(1, min(grade, 3))}"
    bounds = _PARAM_BOUNDS[g_key]

    # "context" is declared as a variant axis (VARIANTS_BY_DNA) but the
    # orchestrator only auto-varies a declared axis when the CALLER passes
    # allowed_contexts/allowed_difficulties explicitly (Lab UI) -- an
    # ordinary generation call never does, so this always defaulted to
    # "pure" and every sample used the identical bare stem regardless of
    # what VARIANTS_BY_DNA claims is possible (blind review: "11 of 12
    # samples reuse the identical bare stem... the only contextualized
    # item... originates from a different (spine) mechanism"). Auto-vary
    # here, weighted toward "pure" since bare-number comparison/ordering
    # is still this competency's core skill.
    context = profile.get("context") or ("word_problem" if rng.random() < 0.3 else "pure")
    spine = profile.get("spine", None)

    max_val_prof = profile.get("max_value")
    if max_val_prof is None:
        from backend.app.practice_gen.dna.base import log_interpolate
        diff_scalar = float(profile.get("difficulty_scalar", profile.get("number_difficulty", 0.5)))
        effective_max = int(log_interpolate(10, bounds["max_value"], diff_scalar))
    elif isinstance(max_val_prof, (int, float)):
        effective_max = int(max_val_prof)
    elif isinstance(max_val_prof, str):
        range_caps = {"up_to_20": 20, "up_to_100": 100, "up_to_1000": 1000, "up_to_10000": 10000}
        effective_max = range_caps.get(max_val_prof, 100)
    else:
        effective_max = 100

    effective_max = max(2, min(effective_max, 10000))
    raw_task_type = profile.get("task_type", "compare_pair")
    task_type = raw_task_type
    if task_type == "compare_pair":
        task_type = "compare_two"
    elif task_type == "order_sequence":
        task_type = "order_set"

    proximity = profile.get("proximity", "far_apart")
    num_diff_scalar = float(profile.get("number_difficulty", 0.5))

    if task_type == "compare_two":
        # "=" as a genuine correct answer (not just a wrong-answer option
        # inside a False claim) requires a == b, but the two draws below
        # are independent random ints over a range up to 10000 -- the odds
        # of landing on a==b by pure chance are ~1/effective_max, so "="
        # essentially never appeared as the correct symbol even though the
        # competency explicitly names "=, >, and <" as three required
        # symbols (blind review of mat_g3_na_q1_5: "'=' never appears as a
        # correct answer in any of the 16 samples"). Force it deliberately
        # a fraction of the time instead of leaving it to chance.
        force_equal = rng.random() < 0.2
        if force_equal:
            a = rng.randint(1, effective_max)
            b = a
        else:
            candidates = []
            for _ in range(500):
                if proximity == "close_together":
                    x, y = _close_pair(rng, effective_max)
                else:
                    x = rng.randint(1, effective_max)
                    y = rng.randint(1, effective_max)
                if x != y:
                    candidates.append((x, y))
            from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window
            a, b = generate_pair_by_window(candidates, num_diff_scalar, d=5, rng=rng)
        numbers = [a, b]
        answer = _compare_symbol(a, b)
        distractors = [o for o in [">", "<", "="] if o != answer]
        distractors.append("cannot be determined")

    elif task_type == "order_set":
        sz_lo, sz_hi = bounds["set_size"]
        n = rng.randint(sz_lo, sz_hi)
        if proximity == "close_together":
            max_base = max(1, effective_max - n * 5)
            base = int(max_base * num_diff_scalar)
            base = max(1, min(max_base, base + rng.randint(-5, 5)))
            numbers = [base + rng.randint(0, 5) for _ in range(n)]
        else:
            numbers = []
            for _ in range(n):
                val = int(effective_max * num_diff_scalar) + rng.randint(-10, 10)
                numbers.append(max(1, min(effective_max, val)))
        
        numbers = set(numbers)
        # Ordering a set is only a genuine ordering task with >= 3 distinct
        # values (2 values is just a comparison, already covered by
        # task_type="compare_two"). The previous version padded by
        # appending to the raw list and only de-duplicating once *after*
        # the loop exited, so its `while len(numbers) < 3` condition
        # checked list length, not distinct count -- when effective_max was
        # small (e.g. a low-difficulty-scalar G1 draw), the appended values
        # frequently duplicated existing ones and the final set could still
        # have fewer than 3 distinct numbers. Guarantee distinctness
        # directly instead of hoping padding-then-dedup lands on >= 3.
        attempts = 0
        while len(numbers) < 3 and attempts < 200:
            numbers.add(rng.randint(1, max(3, effective_max)))
            attempts += 1
        numbers = list(sorted(numbers))

        answer = ", ".join(map(str, sorted(numbers)))
        d1 = ", ".join(map(str, sorted(numbers, reverse=True)))
        
        shuffles = set()
        for _ in range(50):
            shuf = list(numbers)
            rng.shuffle(shuf)
            shuf_str = ", ".join(map(str, shuf))
            if shuf_str != answer and shuf_str != d1:
                shuffles.add(shuf_str)
            if len(shuffles) >= 2:
                break
        shuffles_list = list(shuffles)
        while len(shuffles_list) < 2:
            shuffles_list.append(f"{answer} (reversed)")
            
        distractors = [d1] + shuffles_list[:2]

    else:  # find_between
        effective_max = max(3, effective_max)
        candidates = []
        for _ in range(500):
            a = rng.randint(1, effective_max - 2)
            b = rng.randint(a + 2, effective_max)
            candidates.append((a, b))
        from backend.app.practice_gen.generators.number_difficulty import generate_pair_by_window
        a, b = generate_pair_by_window(candidates, num_diff_scalar, d=5, rng=rng)
        
        between = rng.randint(a + 1, b - 1)
        numbers = [a, b]
        answer = between
        
        d1 = a - rng.randint(1, 5)
        if d1 < 0:
            d1 = b + rng.randint(1, 5)
        d2 = b + rng.randint(1, 5)
        d3 = rng.choice([a, b])
        distractors = [d1, d2, d3]

    result_dict = {
        "blank_target": "answer",
        "numbers": numbers,
        "numbers_str": ", ".join(map(str, numbers)),
        "answer": answer,
        "task_type": raw_task_type,
        "context": context,
        "a": numbers[0] if len(numbers) > 0 else None,
        "b": numbers[1] if len(numbers) > 1 else None,
        "distractors": distractors,
    }
    if task_type == "order_set":
        # fmt_ordering.py's primary sequence-resolution path reads
        # ctx.values["sequence"] (a plain list of the raw numbers to sort).
        # Without it, the formatter fell back to `[correct_answer] +
        # distractors` -- but for this task_type, correct_answer and each
        # distractor are already comma-joined STRINGS representing a full
        # permutation (e.g. "1, 2, 6"), so the fallback re-joined those
        # strings together into one garbled, repeated-numbers question
        # ("Arrange these numbers...: 1, 2, 6, 6, 2, 1, 1, 6, 2 (reversed)").
        # This task_type was effectively dead code before registry.py
        # started binding it, so the mismatch was never exercised.
        result_dict["sequence"] = numbers
        # Every "order numbers ... from smallest to largest, and vice
        # versa" competency names BOTH directions explicitly, but nothing
        # ever set "direction" -- fmt_ordering.py defaults it to
        # "ascending" whenever the key is absent, so the descending half
        # was never once generated (blind review of mat_g1_na_q1_4,
        # mat_g2_na_q1_4, mat_g2_na_q4_2, and others). Vary it by seed
        # unless a caller explicitly pins one.
        result_dict["direction"] = profile.get("direction") or rng.choice(["ascending", "descending"])

    if context == "word_problem":
        # This DNA had no word-problem framing generation anywhere --
        # `context` was stored but never used to vary the rendered text,
        # so every sample (aside from the rare item routed through the
        # separate spine system) used the identical bare "Compare the
        # numbers: X ___ Y"/"Arrange these numbers..." stem regardless of
        # context (blind review: variant_comprehensiveness FAIL/CONCERN
        # across mat_g1_na_q1_3/_4, mat_g1_na_q2_0, mat_g2_na_q1_4,
        # mat_g3_na_q1_5/_6 -- "11 of 12 samples reuse the identical bare
        # stem"). fmt_mcq.py/fmt_cloze.py/fmt_ordering.py were updated to
        # prefer this "question" key when present, same pattern as every
        # other word-problem DNA fix this session.
        actor = rng.choice(["Ana", "Ben", "Liza", "Jose", "Maria", "Kuya Pat"])
        # (singular, plural) -- word-problem items reference specific
        # counts that can legitimately be 1, and "1 marbles" is the same
        # missing-pluralization defect blind review flagged repeatedly
        # elsewhere this session ("1 clip highlights", "1 water bottles").
        item_pairs = [
            ("marble", "marbles"), ("sticker", "stickers"),
            ("seashell", "seashells"), ("storybook", "storybooks"),
            ("pencil", "pencils"),
        ]
        if task_type == "order_set":
            singular, plural = rng.choice(item_pairs)
            item_word = singular if len(numbers) == 1 else plural
            direction_word = "smallest to largest" if result_dict["direction"] == "ascending" else "largest to smallest"
            result_dict["question"] = (
                f"{actor} counted {item_word} collected by {len(numbers)} friends: "
                f"{', '.join(map(str, numbers))}. Arrange the counts from {direction_word}."
            )
        elif task_type != "find_between":
            singular, plural = rng.choice(item_pairs)
            a_word = singular if a == 1 else plural
            b_word = singular if b == 1 else plural
            friend = rng.choice([n for n in ("Ben", "Liza", "Jose", "Maria") if n != actor])
            # Deliberately doesn't restate ">, <, or =" inline: fmt_cloze.py's
            # shared blank-insertion step finds the correct answer's own
            # string value ANYWHERE in the question text and replaces it --
            # when the answer happens to be "<" (a character that can
            # legitimately appear in this sentence's own wording), it
            # corrupted "...>, <, or =?" into "...>, ___, or =?" (found live
            # testing seed 72/603). Each formatter already presents its own
            # options/blank separately; the narrative doesn't need to list
            # them.
            result_dict["question"] = (
                f"{actor} has {a} {a_word}. {friend} has {b} {b_word}. "
                f"Which sign correctly compares the two amounts?"
            )

    return result_dict


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hints for a comparison/ordering problem."""
    numbers   = values["numbers"]
    answer    = values["answer"]
    task_type = values["task_type"]

    gt = VOCAB_GT.resolve(cumulative_vocab)
    lt = VOCAB_LT.resolve(cumulative_vocab)
    eq = VOCAB_EQ.resolve(cumulative_vocab)

    hints: List[str] = []

    if task_type in ("compare_two", "compare_pair"):
        a, b = numbers[0], numbers[1]
        hints.append(f"Compare {a} and {b}.")
        if "place value" in cumulative_vocab and "digit" in cumulative_vocab:
            hints.append("Start from the largest place value and compare each digit.")
        else:
            hints.append("Start from the leftmost number and compare one at a time.")
        if a > b:
            hints.append(f"{a} is {gt} {b}, so we write {a} > {b}.")
        elif a < b:
            hints.append(f"{a} is {lt} {b}, so we write {a} < {b}.")
        else:
            hints.append(f"{a} is {eq} {b}, so we write {a} = {b}.")

    elif task_type in ("order_set", "order_sequence"):
        hints.append(f"Numbers to order: {numbers}.")
        hints.append(f"Find the smallest number first, then the next smallest.")
        hints.append(f"Ordered from least to greatest: {sorted(numbers)}.")

    else:  # find_between
        a, b = numbers[0], numbers[1]
        hints.append(f"Find a number between {a} and {b}.")
        hints.append(f"Any number {gt} {a} and {lt} {b} works.")
        hints.append(f"One correct answer is {answer}.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

COMPARING_ORDERING_DNA = DNA(
    concept="comparing_ordering",
    dna_type="algorithmic",
    answer_formula="answer",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=[
        "mcq",
        "cloze",
        "ordering",
        "sort_order",
        "true_false",
    ],
    requires_context=True,
    visual_home="SortOrder",
    difficulty_axes=_DIFFICULTY_AXES,
)
