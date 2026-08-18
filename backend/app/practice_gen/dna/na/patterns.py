"""
DNA: Patterns (Number & Algebra)

Covers MATATAG grades 1–3 pattern competencies:
  G1 — repeating patterns (cycles of 2–3 elements, numbers up to 20)
  G2 — increasing/decreasing arithmetic patterns (step 1–10, up to 100)
  G3 — combined repeating+increasing/decreasing patterns (up to 1000)
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
    "g1": {"max_value": 20,   "cycle_length": (2, 3), "step": (1, 3)},
    "g2": {"max_value": 100,  "cycle_length": (2, 4), "step": (1, 10)},
    "g3": {"max_value": 1000, "cycle_length": (2, 5), "step": (1, 50)},
}


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="answer - common_difference",
        required_concept="patterns",
        label="cnt_wrong_interval",
        description="Used wrong step size when extending the pattern.",
    ),
    ErrorPattern(
        formula="answer + common_difference",
        required_concept="patterns",
        label="cnt_skip",
        description="Skipped a term, giving the value two steps ahead.",
    ),
    ErrorPattern(
        formula="first + (position - 1) * common_difference",
        required_concept="patterns",
        label="ar_wrong_op",
        description="Subtracted instead of added when the pattern is increasing.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_PATTERN    = VocabGated(requires_vocab="pattern",    preferred="pattern",    fallback="repeating group")
VOCAB_RULE       = VocabGated(requires_vocab="rule",       preferred="rule",       fallback="what it does")
VOCAB_TERM       = VocabGated(requires_vocab="term",       preferred="term",       fallback="number in the pattern")
VOCAB_INCREASING = VocabGated(requires_vocab="increasing", preferred="increasing", fallback="going up")
VOCAB_DECREASING = VocabGated(requires_vocab="decreasing", preferred="decreasing", fallback="going down")
VOCAB_REPEATING  = VocabGated(requires_vocab="repeating",  preferred="repeating",  fallback="same group again")


# K-3 appropriate letter pool for repeating patterns whose elements are
# letters rather than numbers -- the competency's own worked example
# names both ("numbers: 2,4,2,4...; letters: a,b,c,a,b,c...", mat_g1_
# na_q3_6), but this DNA only ever generated numeric cycles.
# Excludes g/l/m: single-letter unit abbreviations (gram/liter/meter)
# that are NOT_YET_KNOWN vocabulary at the grades this DNA serves --
# a pattern element rendered as a bare "g"/"l"/"m" in the text tripped
# §1D vocabulary_gating as a false-positive unit reference (confirmed
# live: seed 43's letter cycle ['e','h',...] still failed on stray 'g'/
# 'm' pulled from elsewhere in the pool across other seeds).
_LETTER_POOL = [c for c in "abcdefghijklmnop" if c not in ("g", "l", "m")]


# ─── helpers ──────────────────────────────────────────────────────────────────

def _make_repeating_sequence(start: int, cycle: List[int], length: int) -> List[int]:
    """Build a sequence by repeating the cycle starting at start offset."""
    return [cycle[i % len(cycle)] for i in range(length)]


def _make_arithmetic_sequence(first: int, step: int, length: int, increasing: bool) -> List[int]:
    direction = 1 if increasing else -1
    return [first + direction * step * i for i in range(length)]


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Generate a pattern sequence based on grade and difficulty profile.

    Returns:
        {
            "sequence":        list of ints shown to student (with one slot masked),
            "missing_index":   index of the missing/next term,
            "answer":          correct int value,
            "rule_description": human-readable rule string,
            "common_difference": step size (0 for pure repeating),
            "first":           first term,
            "position":        1-based position of answer,
        }
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    g_key = f"g{max(1, min(grade, 3))}"
    bounds = _PARAM_BOUNDS[g_key]
    diff_scalar = float(profile.get("difficulty_scalar", profile.get("number_difficulty", 0.5)))
    from backend.app.practice_gen.dna.base import log_interpolate, linear_interpolate
    
    max_val_bound = int(log_interpolate(10, bounds["max_value"], diff_scalar))
    max_val = int(profile.get("max_value", max_val_bound))
    
    step_lo_bound, step_hi_bound = bounds["step"]
    step_hi_bound = int(linear_interpolate(step_lo_bound, step_hi_bound, diff_scalar))
    step_lo = int(profile.get("step_lo", step_lo_bound))
    step_hi = int(profile.get("step_hi", step_hi_bound))

    cyc_lo_bound, cyc_hi_bound  = bounds["cycle_length"]
    cyc_hi_bound = int(linear_interpolate(cyc_lo_bound, cyc_hi_bound, diff_scalar))
    cyc_lo = int(profile.get("cycle_lo", cyc_lo_bound))
    cyc_hi = int(profile.get("cycle_hi", cyc_hi_bound))

    num_diff_scalar = diff_scalar

    pattern_type = profile.get("pattern_type", "growing")
    if pattern_type == "growing":
        pattern_type = "arithmetic_increasing"
    elif pattern_type == "increasing_or_decreasing":
        # Composite scope value (registry.py binds this for competencies
        # that explicitly name BOTH directions, e.g. "Determine the next
        # term in increasing or decreasing patterns") -- resolved here via
        # the generation seed, same pattern as missing_number.py resolving
        # its own "addition_subtraction" composite scope value.
        pattern_type = "arithmetic_increasing" if rng.random() < 0.5 else "arithmetic_decreasing"
    elif pattern_type == "increasing_decreasing_or_repeating":
        # "...numbers, letters and rhythmic properties, visual elements in
        # arts, AND REPETITIONS" (mat_g2_na_q2_8) names "repetitions" as
        # one of its own sub-cases, but resolving straight to
        # increasing_or_decreasing (arithmetic-only) meant this node could
        # never reach the "repeating" branch below -- the ONLY branch that
        # can use letters at all (use_letters is scoped entirely inside
        # `if pattern_type == "repeating":`), so "letters" (also explicitly
        # named) never appeared either despite an earlier fix adding
        # letter-cycle support (blind review, twice: "letters... never
        # appear" and "every sample is a numeric arithmetic sequence").
        pattern_type = rng.choice(["arithmetic_increasing", "arithmetic_decreasing", "repeating"])

    ask_type = profile.get("ask_type", "next")
    if ask_type == "next":
        ask_type = "next_term"
    elif ask_type == "missing":
        ask_type = "missing_middle"
    elif ask_type == "explain":
        ask_type = "state_rule"

    seq_length = 6  # always show 6-term window

    from backend.app.practice_gen.generators.number_difficulty import generate_number_by_window, generate_pair_by_window

    if ask_type == "identify_valid":
        # "Create a pattern" competencies (mat_g1_na_q3_7, mat_g2_na_q2_9)
        # have no free-form construction UI in this pipeline -- an MCQ/cloze
        # generator can't literally ask a student to build something. The
        # closest genuine, machine-gradable proxy is recognition: does the
        # student recognize which of several candidate sequences actually
        # satisfies the target pattern type, vs. sequences that look similar
        # but break the rule partway through? That's the same judgment
        # "create a valid pattern" requires, just probed via selection
        # instead of construction.
        if pattern_type == "repeating":
            cycle_len = rng.randint(cyc_lo, cyc_hi)
            # "Create repeating patterns using objects, images, or numbers" (mat_g1_na_q3_7)
            # supports three modalities: objects/shapes, letters, and numbers.
            modality = rng.choice(["objects", "letters", "numbers"])
            if modality == "objects":
                candidates = ["square", "triangle", "rectangle"]
                cycle = rng.sample(candidates, min(cycle_len, len(candidates)))
            elif modality == "letters":
                candidates = _LETTER_POOL
                cycle = rng.sample(_LETTER_POOL, min(cycle_len, len(_LETTER_POOL)))
            else:
                candidates = list(range(1, max_val + 1))
                cycle = [generate_number_by_window(candidates, num_diff_scalar, d=5, rng=rng) for _ in range(cycle_len)]
            
            if len(set(cycle)) < 2:
                alternatives = [c for c in candidates if c != cycle[0]]
                if alternatives:
                    cycle[-1] = rng.choice(alternatives)
            
            valid_seq = _make_repeating_sequence(0, cycle, seq_length)
            pattern_label = "repeating pattern"
            rule = f"Repeat the group: {', '.join(map(str, cycle))}"
        else:
            increasing = pattern_type != "arithmetic_decreasing"
            if increasing:
                # `first` must stay small enough that first + step*(n-1)
                # doesn't exceed max_val while climbing.
                pairs = [(f, s) for s in range(step_lo, step_hi + 1) for f in range(1, max(2, max_val - s * seq_length) + 1)]
                if not pairs:
                    pairs = [(1, step_lo)]
            else:
                # `first` must start large enough that first - step*(n-1)
                # never goes negative while descending (mirrors the
                # existing, already-correct arithmetic_decreasing branch
                # above -- reusing the increasing branch's pair formula
                # here previously let decreasing sequences start small and
                # go negative, e.g. "1, 0, -1, -2, -3, -4", which G1-G3
                # students haven't been introduced to negative numbers for).
                pairs = [(f, s) for s in range(step_lo, step_hi + 1) for f in range(s * seq_length + 1, max_val + 1)]
                if not pairs:
                    pairs = [(max_val, step_lo)]
            first, step = generate_pair_by_window(pairs, num_diff_scalar, d=5, rng=rng)
            valid_seq = _make_arithmetic_sequence(first, step, seq_length, increasing=increasing)
            pattern_label = "increasing pattern" if increasing else "decreasing pattern"
            rule = f"{'Add' if increasing else 'Subtract'} {step} each time"

        is_letter_seq = any(isinstance(v, str) for v in valid_seq)
        distractor_seqs = []
        seen = {tuple(valid_seq)}
        attempts = 0
        while len(distractor_seqs) < 3 and attempts < 50:
            attempts += 1
            corrupted = list(valid_seq)
            break_idx = rng.randint(1, len(corrupted) - 1)
            if is_letter_seq:
                # Numeric +/-N corruption crashes on a letter element (can't
                # add an int to a str) -- swap in a different letter from
                # the same candidate pool instead.
                other_letters = [c for c in candidates if c != corrupted[break_idx]]
                corrupted[break_idx] = rng.choice(other_letters) if other_letters else corrupted[break_idx]
            else:
                corrupted[break_idx] = max(0, corrupted[break_idx] + rng.choice([-3, -2, -1, 1, 2, 3]))
            if tuple(corrupted) not in seen:
                seen.add(tuple(corrupted))
                distractor_seqs.append(corrupted)
        while len(distractor_seqs) < 3:
            # Extremely small ranges can run out of distinct corruptions;
            # fall back to a fully-random same-length sequence rather than
            # loop forever or ship fewer than 3 options.
            if is_letter_seq:
                distractor_seqs.append([rng.choice(candidates) for _ in valid_seq])
            else:
                distractor_seqs.append([rng.randint(1, max(2, max_val)) for _ in valid_seq])

        answer_str = ", ".join(map(str, valid_seq))
        distractor_strs = [", ".join(map(str, d)) for d in distractor_seqs]
        # "CREATE ... patterns" (mat_g1_na_q3_7, mat_g2_na_q2_9): the
        # previous "Which of these sequences shows a repeating pattern?"
        # phrasing is pure recognition, with no trace of the competency's
        # own "create" verb anywhere in the text (blind review, twice:
        # "the competency verb 'create' is never actually exercised... no
        # sample ever asks the student to generate a pattern"). This is
        # still a selection task (this pipeline has no free-form
        # construction UI -- see the comment above), but naming the rule
        # to be applied and asking which option correctly CREATES/BUILDS
        # a sequence that follows it is a closer proxy to "create" than
        # asking the student to merely recognize an unspecified pattern.
        elements_str = ", ".join(map(str, cycle)) if pattern_type == "repeating" else None
        if elements_str:
            q_template = rng.choice([
                f"You want to create a repeating pattern using: {elements_str}. Which sequence correctly creates it?",
                f"Create a repeating pattern with the repeating group: {elements_str}. Which sequence shows this pattern?",
                f"Use the repeating unit {elements_str} to build a repeating pattern. Which sequence correctly creates it?",
            ])
            question = q_template
        else:
            first_term = valid_seq[0]
            question_templates = [
                f"You want to create {'an' if pattern_label[0] in 'aeiou' else 'a'} {pattern_label} where the rule is: {rule}. Which sequence correctly creates it?",
                f"Start at {first_term} and create {'an' if pattern_label[0] in 'aeiou' else 'a'} {pattern_label} with the rule: {rule}. Which pattern did you create?",
                f"Which sequence correctly shows {'an' if pattern_label[0] in 'aeiou' else 'a'} {pattern_label} starting at {first_term} and following the rule: {rule}?",
                f"Create a pattern that starts at {first_term} and uses the rule: {rule}. Which sequence shows this pattern?",
            ]
            question = rng.choice(question_templates)
        return {
            "blank_target": "answer",
            "task_type": "identify_valid_pattern",
            "pattern_kind": pattern_type,
            "answer": answer_str,
            "distractors": distractor_strs,
            "question": question,
            "rule_description": rule,
        }

    if pattern_type == "repeating":
        cycle_len = max(2, rng.randint(cyc_lo, cyc_hi))
        # "letters: a, b, c, a, b, c..." is the competency's own second
        # worked example alongside the numeric one -- weighted minority so
        # numeric cycles (the DNA's original, still-primary behavior)
        # keep dominating, but letters now genuinely appear (blind review
        # of mat_g1_na_q3_6: "not a single sample across all 14 seeds uses
        # letters").
        use_letters = rng.random() < 0.35
        if use_letters:
            candidates = _LETTER_POOL
            cycle = rng.sample(_LETTER_POOL, min(cycle_len, len(_LETTER_POOL)))
        else:
            candidates = list(range(1, max_val + 1))
            cycle = [generate_number_by_window(candidates, num_diff_scalar, d=5, rng=rng) for _ in range(cycle_len)]
        # A cycle whose members are all equal renders as "2, 2, 2, 2, 2, 2" — a
        # constant run with no repeating structure to notice, where the answer is
        # simply the number already on the page (validate_matrix §1F). Force at
        # least two distinct members so there is a cycle to perceive; a
        # single-element cycle is degenerate for the same reason, hence the
        # max(2, ...) on cycle_len above.
        if len(set(cycle)) < 2:
            alternatives = [c for c in candidates if c != cycle[0]]
            if not alternatives:
                raise RuntimeError(
                    f"generate_params (patterns): cannot build a repeating cycle with two "
                    f"distinct values — max_val={max_val} leaves no alternative to {cycle[0]}. "
                    f"(grade={grade}, profile={difficulty_profile})"
                )
            cycle[-1] = rng.choice(alternatives) if use_letters else generate_number_by_window(alternatives, num_diff_scalar, d=5, rng=rng)
        sequence = _make_repeating_sequence(0, cycle, seq_length + 1)
        step = 0
        rule = f"Repeat the group: {', '.join(map(str, cycle))}"
    elif pattern_type == "arithmetic_decreasing":
        pairs = []
        for s in range(step_lo, step_hi + 1):
            for f in range(s * seq_length + 1, max_val + 1):
                pairs.append((f, s))
        if not pairs:
            pairs = [(max_val, step_lo)]
        first, step = generate_pair_by_window(pairs, num_diff_scalar, d=5, rng=rng)
        sequence = _make_arithmetic_sequence(first, step, seq_length + 1, increasing=False)
        rule = f"Subtract {step} each time"
    elif pattern_type == "combined":
        # Create a nested pattern: an inner repeating loop + an outer
        # increasing OR decreasing step. E.g. [11, 12, 13, 21, 22, 23, 31,
        # 32, 33] (increasing) or [51, 52, 53, 41, 42, 43, 31, 32, 33]
        # (decreasing). The competency explicitly names both directions
        # ("repeating and increasing components OR repeating and
        # decreasing components"), but this branch always built an
        # increasing outer step -- the decreasing half was structurally
        # impossible to generate, not just unsampled by default.
        inner_cycle_len = rng.randint(2, 3)
        outer_step_mag = rng.choice([1, 2, 5, 10])
        
        # Cap sequence length to 9 terms to avoid UI clutter
        total_elements = min(9, inner_cycle_len * 3)
        seq_length = total_elements - 1
        max_block_idx = (total_elements - 1) // inner_cycle_len
        
        decreasing = rng.random() < 0.5
        inner_cycle = [rng.randint(1, 9) for _ in range(inner_cycle_len)]
        if decreasing:
            outer_step = -outer_step_mag
            # Start high enough that even after max_block_idx downward
            # steps, the smallest term (plus the largest inner-cycle
            # digit) stays a positive, grade-appropriate number.
            min_start = (max_block_idx * outer_step_mag + 1) * 10
            outer_start = min_start + rng.randint(0, 4) * 10
        else:
            outer_step = outer_step_mag
            outer_start = rng.randint(1, 5) * 10
        
        sequence = []
        for i in range(total_elements):
            block_idx = i // inner_cycle_len
            cycle_idx = i % inner_cycle_len
            val = (outer_start + block_idx * outer_step * 10) + inner_cycle[cycle_idx]
            sequence.append(val)
            
        step = outer_step * 10
        rule = f"Repeat the ones {inner_cycle} and {'subtract' if decreasing else 'add'} {abs(step)} every group"
    else:  # arithmetic_increasing (default)
        pairs = []
        for s in range(step_lo, step_hi + 1):
            for f in range(1, max(2, max_val - s * seq_length) + 1):
                pairs.append((f, s))
        if not pairs:
            pairs = [(1, step_lo)]
        first, step = generate_pair_by_window(pairs, num_diff_scalar, d=5, rng=rng)
        sequence = _make_arithmetic_sequence(first, step, seq_length + 1, increasing=True)
        rule = f"Add {step} each time"

    if ask_type == "next_term":
        missing_index = seq_length  # last position
        visible = sequence[:seq_length]
        answer = sequence[seq_length]
    elif ask_type == "missing_middle":
        missing_index = rng.randint(1, seq_length - 2)
        visible = sequence[:seq_length]
        answer = visible[missing_index]
        visible = visible[:]  # copy; caller masks missing_index
    else:  # state_rule
        missing_index = -1
        visible = sequence[:seq_length]
        answer = step if pattern_type != "repeating" else 0

    first_val = sequence[0]
    position = missing_index + 1 if missing_index >= 0 else seq_length + 1

    result_dict = {
        "blank_target": "answer",
        "sequence":          visible,
        "missing_index":     missing_index,
        "answer":            answer,
        "rule_description":  rule,
        "common_difference": step if pattern_type != "repeating" else 0,
        "first":             first_val,
        "position":          position,
        "pattern_kind":      pattern_type,
        "given_values":      {f"term_{i}": val for i, val in enumerate(visible)},
    }
    if pattern_type == "repeating":
        # fmt_pattern_sequence.py's trap builder needs the repeating unit
        # and its length to build cycle-aware distractors (other members
        # of the cycle, off-by-one-in-cycle) -- without these it indexed
        # into an empty fallback list ("list index out of range") once
        # patterns actually reached that formatter's repeating-kind trap
        # branch (see that file's own fix comment).
        result_dict["base_pattern"] = cycle
        result_dict["period"] = len(cycle)
    if isinstance(answer, str):
        # A letter answer can't use the shared numeric-offset distractor
        # padding (base_generator's type-consistency guard correctly
        # skips it for a string correct_answer), so without explicit
        # distractors here an MCQ/cloze render would have zero wrong
        # options to offer. Pick 3 other letters, excluding any already
        # used in this cycle so a distractor can't coincidentally also be
        # a valid position in the same pattern.
        pool = [c for c in _LETTER_POOL if c not in visible and c != answer]
        result_dict["distractors"] = rng.sample(pool, min(3, len(pool)))
    return result_dict


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hints for the given pattern problem."""
    seq   = values["sequence"]
    diff  = values["common_difference"]
    rule  = values["rule_description"]
    ans   = values["answer"]
    m_idx = values["missing_index"]

    term_label = VOCAB_TERM.resolve(cumulative_vocab)
    rule_label = VOCAB_RULE.resolve(cumulative_vocab)

    hints: List[str] = []
    hints.append(f"Look at the pattern: {seq}.")

    if diff != 0:
        direction = VOCAB_INCREASING.resolve(cumulative_vocab) if diff > 0 else VOCAB_DECREASING.resolve(cumulative_vocab)
        hints.append(f"The pattern is {direction} by {abs(diff)} each step.")
    else:
        rep = VOCAB_REPEATING.resolve(cumulative_vocab)
        hints.append(f"This is a {rep} {VOCAB_PATTERN.resolve(cumulative_vocab)}. Find the repeating group.")

    if m_idx >= 0:
        hints.append(f"The missing {term_label} is at position {m_idx + 1}.")
    hints.append(f"The {rule_label} is: {rule}. The answer is {ans}.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

PATTERNS_DNA = DNA(
    concept="patterns",
    dna_type="algorithmic",
    answer_formula="answer",
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=[
        "mcq",
        "cloze",
        "numeric_input",
        "pattern_sequence",
        # "fill_in_table" removed: that formatter is a categorical
        # count table (categories + counts, e.g. for pictographs) --
        # patterns.py never produces "categories"/"values" data, so it
        # always fell back to a hardcoded, content-free placeholder
        # ("A, B, C" / "1, 2, 3") regardless of seed or the actual
        # pattern (blind review of mat_g3_na_q3_6: "Fill in the table
        # with the correct counts", answer [1, 2, 3], for every seed
        # that landed on it -- unrelated to any generated pattern).
    ],
    requires_context=False,
    visual_home="PatternSequence",
    difficulty_axes=_DIFFICULTY_AXES,
)
