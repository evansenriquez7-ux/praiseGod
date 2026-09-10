"""
DNA: Ordinal Numbers (Number & Algebra)

Static-bank DNA. Item pool is authored inline as templates.

Covers MATATAG grades 1–3 ordinal competencies:
  G1 — 1st through 10th
  G2 — up to 20th
  G3 — up to 100th
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
# For static_bank the bounds document the ordinal range, not numeric operands.
_PARAM_BOUNDS: Dict[str, Dict[str, Any]] = {
    "g1": {"min_ordinal": 1,  "max_ordinal": 10},
    "g2": {"min_ordinal": 1,  "max_ordinal": 20},
    "g3": {"min_ordinal": 1,  "max_ordinal": 100},
}


# ─── ordinal utilities ────────────────────────────────────────────────────────

def _ordinal_suffix(n: int) -> str:
    """Return '1st', '2nd', '3rd', '4th', … for any positive integer."""
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    return f"{n}{['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]}"


_ORDINAL_WORDS = {
    1: "first",  2: "second",  3: "third",   4: "fourth",  5: "fifth",
    6: "sixth",  7: "seventh", 8: "eighth",  9: "ninth",  10: "tenth",
    11: "eleventh", 12: "twelfth", 13: "thirteenth", 14: "fourteenth",
    15: "fifteenth", 16: "sixteenth", 17: "seventeenth", 18: "eighteenth",
    19: "nineteenth", 20: "twentieth",
}

_TENS_ORDINAL = {
    2: "twentieth", 3: "thirtieth", 4: "fortieth", 5: "fiftieth",
    6: "sixtieth",  7: "seventieth", 8: "eightieth", 9: "ninetieth",
}


def _ordinal_word(n: int) -> str:
    """Return 'first', 'second', … 'one hundredth' for 1–100."""
    if n in _ORDINAL_WORDS:
        return _ORDINAL_WORDS[n]
    if n == 100:
        return "one hundredth"
    tens, ones = n // 10, n % 10
    if ones == 0:
        return _TENS_ORDINAL.get(tens, f"{n}th")
    # e.g. twenty-first
    _tens_prefix = {2: "twenty", 3: "thirty", 4: "forty", 5: "fifty",
                    6: "sixty", 7: "seventy", 8: "eighty", 9: "ninety"}
    prefix = _tens_prefix.get(tens, "")
    return f"{prefix}-{_ORDINAL_WORDS.get(ones, _ordinal_suffix(ones))}"


# ─── line-up subjects ─────────────────────────────────────────────────────────
# Every ordinal competency in G1-G3 reads "Describe the position of OBJECTS using
# ordinal numbers". Until 2026-09-09 this DNA rendered ordinal-word recall only --
# "Which word describes the 9th position?" -- with no object anywhere in the item, and
# §6D reported `objects` as unprovided on all three nodes. MATATAG names it, so building
# it is the fix (Content Rule 4). Names match the pool the rest of the tree uses
# (order_of_operations._WP_ACTORS).
_LINEUP_NAMES = ["Ana", "Ben", "Carlo", "Dina", "Elena", "Fidel", "Gina", "Hector",
                 "Iris", "Jose"]

# ...and the objects themselves. The name line-up above was filed as satisfying the
# clause `objects`, and on 2026-09-10 a blind Attester reading only the rendered page
# ruled it NOT_PROVIDED on all three ordinal nodes: "every situation on this page is
# populated by people, not things ... the position being described is never the position
# of an object." It is right, and the comment above claiming "the line-up IS the object
# set the clause names" was the author reading its own intent into the page rather than
# reading the page. MATATAG says "Describe the position of OBJECTS using ordinal
# numbers" on all three nodes, so rendering objects is the fix (Content Rule 4) and a
# wider reading of the word is not.
#
# The name line-up STAYS. A queue of pupils is a legitimate contextual variant and
# removing it would narrow the node to satisfy a check; both pools are now reachable and
# the object pool carries the clause.
#
# Vocabulary-checked against all three nodes' NOT_YET_KNOWN on 2026-09-10 (Content Rule
# 1): G1's set contains `circle`, `corner`, `coin` and `bill`, so no shape and no money
# noun appears here, and `line` is NOT_YET_KNOWN at G1 and G2, so no template below
# writes it as a standalone word ("lined up" is a different token to the whole-word
# gate, and is checked as rendered output by §1D either way).
_LINEUP_OBJECTS = [("mango", "mangoes"), ("notebook", "notebooks"),
                   ("sticker", "stickers"), ("marble", "marbles"),
                   ("egg", "eggs"), ("storybook", "storybooks"),
                   ("basket", "baskets"), ("shell", "shells"),
                   ("pencil", "pencils"), ("spoon", "spoons")]


def _lineup_pool(template_def: Dict[str, Any]) -> List[str]:
    """The set of things this template lines up: objects, or the pupils' names."""
    if template_def.get("lineup_pool") == "objects":
        return [singular for singular, _plural in _LINEUP_OBJECTS]
    return _LINEUP_NAMES


# ─── item template pool ───────────────────────────────────────────────────────
# Each template has:
#   "range_key": which grade/range this template suits
#   "template":  f-string with {ordinal}, {word}, {symbol} slots
#   "task_type": which difficulty axis task_type it addresses

_ITEM_TEMPLATES = [
    # identify_ordinal — symbol given, choose word
    {
        "range_key": "1st_to_10th",
        "template":  "Which word describes the {symbol} position?",
        "task_type": "identify_ordinal",
        "answer_key": "word",
        "choices_type": "words",
    },
    # identify_ordinal — word given, choose symbol
    {
        "range_key": "1st_to_10th",
        "template":  "Write the symbol for the {word} position.",
        "task_type": "identify_ordinal",
        "answer_key": "symbol",
        "choices_type": "symbols",
    },
    # find_position — position number given, pick ordinal symbol
    {
        "range_key": "11th_to_20th",
        "template":  "A runner is at position number {n}. In what place did the runner finish?",
        "task_type": "find_position",
        "answer_key": "symbol",
        "choices_type": "symbols",
    },
    # find_position — position number given, pick ordinal symbol
    {
        "range_key": "11th_to_20th",
        "template":  "What ordinal describes position number {n}?",
        "task_type": "find_position",
        "answer_key": "symbol",
        "choices_type": "symbols",
    },
    # compare_positions — two ordinals, which comes first
    {
        "range_key": "21st_to_100th",
        "template":  "Who arrived earlier: the student in {symbol} place or {symbol2} place?",
        "task_type": "compare_positions",
        "answer_key": "earlier_symbol",
        "choices_type": "symbols",
    },
    # compare_positions — between two ordinals, which is later
    {
        "range_key": "21st_to_100th",
        "template":  "Which position comes after {symbol}?",
        "task_type": "compare_positions",
        "answer_key": "next_symbol",
        "choices_type": "symbols",
    },
    # describe_position — the clause "the position of objects". The enumerated form can
    # only be used when the line-up is long enough to HAVE an {symbol} member, so
    # generate_params falls back to the scalable form below for large ordinals; that is
    # what keeps scalar 1.0 reaching a G3 ceiling of 100th (§1A) while still naming an
    # object at every value.
    {
        "range_key": "1st_to_10th",
        "template":  "{lineup} stand in a row. Who is {symbol} in the row?",
        "task_type": "describe_position",
        "answer_key": "object_at_position",
        "choices_type": "names",
        "needs_lineup": True,
    },
    # A stem that asks for a WORD must key a word. Both scalable describe_position
    # templates asked "Which word describes ...?" and keyed a SYMBOL against an
    # all-symbol option list, so the item answered a different question than it posed --
    # mat_g1_na_q1_5 seed 601 asked for a word and paid out 10th, while seed 42 asked
    # the same thing and correctly paid out tenth. Found 2026-09-10 by a blind reviewer
    # reading only the rendered page; no mechanical check looks at whether a stem's
    # requested FORM matches its key's form. `distractors` are derived from `answer_key`
    # (not from `choices_type`, which nothing outside this file reads), so switching the
    # key switches the option list with it.
    {
        "range_key": "any",
        "template":  "The pupils stand in a row. {actor} is number {n} in the row. "
                     "Which word describes {actor}'s position?",
        "task_type": "describe_position",
        "answer_key": "word",
        "choices_type": "words",
    },
    # describe_position, on OBJECTS. The two forms above put people in the row; these
    # two put things in it, which is what the clause `objects` names. Enumerated form
    # first (the pupil picks the object standing at the nth place), scalable form second
    # so a G3 ceiling of 100th still has an object in it.
    {
        "range_key": "1st_to_10th",
        "template":  "The {lineup} are lined up on a shelf from left to right. "
                     "Which one is in {symbol} place?",
        "task_type": "describe_position",
        "answer_key": "object_at_position",
        "choices_type": "names",
        "needs_lineup": True,
        "lineup_pool": "objects",
    },
    {
        "range_key": "any",
        "template":  "The {objects_plural} are placed in a row. One {object_singular} "
                     "is number {n} in the row. Which word describes its position?",
        "task_type": "describe_position",
        "answer_key": "word",
        "choices_type": "words",
        "lineup_pool": "objects",
    },
]


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="n",
        required_concept="ordinal_numbers",
        label="cnt_card_ord",
        description="Gave the cardinal count instead of the ordinal position.",
    ),
    ErrorPattern(
        formula="n + 1",
        required_concept="ordinal_numbers",
        label="cnt_ord_off",
        description="Off by one — gave the next ordinal position instead.",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {"number_difficulty": "continuous"}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_FIRST   = VocabGated(requires_vocab="1st",      preferred="1st",      fallback="number one")
VOCAB_ORDINAL = VocabGated(requires_vocab="ordinal",  preferred="ordinal",  fallback="order word")
VOCAB_POSITION= VocabGated(requires_vocab="position", preferred="position", fallback="order")


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """
    Static-bank generator: pick a template and fill in a random ordinal value.

    Returns:
        {
            "n":             int (ordinal position),
            "symbol":        str ("1st", "2nd", …),
            "word":          str ("first", "second", …),
            "question_text": str (rendered template),
            "answer":        Any (depends on template answer_key),
            "task_type":     str,
        }
    """
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    g_key = f"g{max(1, min(grade, 3))}"
    bounds = _PARAM_BOUNDS[g_key]
    min_ord = bounds["min_ordinal"]
    max_ord = bounds["max_ordinal"]

    # An EXPLICIT scalar always wins. Whether one was supplied is the whole question
    # below, so it is recorded before the default is applied rather than inferred from
    # the value afterwards -- 0.5 supplied and 0.5 defaulted are different facts.
    explicit_scalar = profile.get("difficulty_scalar", profile.get("number_difficulty"))
    diff_scalar = float(explicit_scalar) if explicit_scalar is not None else 0.5
    ordinal_range_val = profile.get("ordinal_range")
    if ordinal_range_val is not None:
        if isinstance(ordinal_range_val, (list, tuple)) and len(ordinal_range_val) == 2:
            min_ord = max(min_ord, int(ordinal_range_val[0]))
            max_ord = min(max_ord, int(ordinal_range_val[1]))
        else:
            # `ordinal_range` is a MAGNITUDE BOUND, not a difficulty scalar. It clamps
            # how far up the ordinal series this node may reach; it says nothing about
            # where inside that range an item should sit, and the scalar that does say
            # so already arrived as `number_difficulty`.
            #
            # This used to OVERWRITE diff_scalar with (max_ord - min_ord) /
            # (curriculum_max - min_ord). The orchestrator clamps the mapped axis value
            # to the node's own competency ceiling, so `max_ord` and `curriculum_max`
            # were the same number on every render of every ordinal node -- the
            # expression was structurally pinned to 1.0. Measured 2026-09-10: the
            # profile reaching this function carries number_difficulty=0.639 and
            # ordinal_range=100, and the scalar handed to the number window was 1.0 on
            # every one of ten seeds.
            #
            # It is a live student-facing defect, not a review artifact. Over 100 seeds
            # at default difficulty, mat_g3_na_q1_2 keyed 99th or 100th 75 times, and
            # mat_g1_na_q1_5 -- whose competency reads "1st, 2nd, 3rd, up to 10th" --
            # keyed 9th or 10th 64 times and 1st twice. The three ordinals the
            # competency names by hand were the ones a pupil almost never got asked.
            # Scalar 0.0 was hit just as hard from the other side: the mapped value
            # there is <= 1, which took the `val <= 1.0` branch and set diff_scalar to
            # 1.0 as well, so the difficulty axis had NO reachable low end at all.
            #
            # §1A never saw it: it asserts on the mapped difficulty_profile ceiling, not
            # on which ordinal the picker returns. Two blind Phase 2 roles found it
            # independently on the same day -- an Attester ("1st reaches the page only
            # as a distractor") and a reviewer ("eight of the ten seeds pin the target
            # at 9 or 10") -- which is the whole reason the judgment layer exists.
            try:
                val = float(ordinal_range_val)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"generate_params (ordinal_numbers): profile['ordinal_range'] is "
                    f"{ordinal_range_val!r}, which is neither a (min, max) pair nor a "
                    f"number (seed={seed}, grade={grade}). This used to be swallowed and "
                    f"the item rendered at whatever difficulty happened to be left over, "
                    f"which is the silent default Protocol 3 forbids."
                ) from exc
            # Two shapes arrive here and they mean opposite things. The ORCHESTRATOR
            # sends a mapped magnitude (10, 20, 100) clamped to the node's competency
            # ceiling. `judgment_packets._max_difficulty_profile` and the Lab send the
            # RAW SCALAR (0.0-1.0) for every continuous axis, by name, with no mapping
            # step in between. A value <= 1.0 is therefore a scalar -- an ordinal range
            # of "at most 1st" is not a thing anyone asks for -- and anything above it
            # is a magnitude bound.
            #
            # Dropping this branch is a regression that hides itself: the max-difficulty
            # seeds keep rendering, they just render at the default scalar, so the packet
            # silently stops demonstrating the competency ceiling while §1A-reach (which
            # drives the profile through the orchestrator's mapping, not this path) still
            # passes. It was caught within the hour by a blind reviewer noticing that
            # "up to 100th" never keyed 100th -- and only because the review packet's
            # seed >= 500 band exists to show the ceiling in the first place.
            if val <= 1.0:
                # A raw scalar, straight from a caller that names the axis and does no
                # mapping (the Lab, and any direct generate_params call). An ordinal
                # range of "at most 1st" is not a thing anyone asks for.
                diff_scalar = val
            else:
                max_ord = min(max_ord, int(val))
                # ...and only when NOTHING supplied a scalar, recover one from the
                # magnitude. `_max_difficulty_profile` pins every continuous axis to 1.0
                # by name and the orchestrator then maps that to a magnitude, dropping
                # `number_difficulty` on the way, so on that path the mapped value is the
                # only difficulty signal there is and this is what makes the review
                # packet's seed >= 500 band actually reach the competency ceiling.
                #
                # This recovery is what used to run UNCONDITIONALLY, and that is the
                # defect: the orchestrator clamps the mapped value to the node's own
                # competency ceiling, so `max_ord == curriculum_max` on every render and
                # the expression is structurally pinned to 1.0. It therefore threw away a
                # perfectly good number_difficulty=0.639 and generated every ordinal item
                # at maximum difficulty. Measured 2026-09-10 over 100 default-difficulty
                # seeds, before/after making the recovery conditional:
                #     mat_g1_na_q1_5   3 distinct keys -> 26   (1st keyed 2x -> 7x)
                #     mat_g2_na_q1_5   4 distinct keys -> 31
                #     mat_g3_na_q1_2   6 distinct keys -> 72   (-st/-nd/-rd now keyed)
                # A Grade 1 pupil whose competency reads "1st, 2nd, 3rd, up to 10th" was
                # being served 9th and 10th on 64 of 100 items.
                if explicit_scalar is None:
                    curriculum_max = bounds["max_ordinal"]
                    if curriculum_max > min_ord:
                        diff_scalar = (max_ord - min_ord) / (curriculum_max - min_ord)

    task_type = profile.get("task_type") or rng.choice(
        ["identify_ordinal", "find_position", "compare_positions", "describe_position"]
    )

    # Filter templates matching task_type.
    #
    # This used to fall back to the WHOLE pool when nothing matched, silently. Until
    # 2026-09-09 `VARIANTS_BY_DNA` declared task_type=['identify_position',
    # 'identify_object'] -- two values no template has ever carried -- so every request
    # for either hit that fallback and rendered an arbitrary item. The variant was
    # accepted, honoured by nothing, and indistinguishable from working: measured, both
    # values produced byte-identical output across six seeds. A silent fallback is
    # exactly what Protocol 3 forbids; an unknown task_type is now a named failure.
    candidates = [t for t in _ITEM_TEMPLATES if t["task_type"] == task_type]
    if not candidates:
        raise ValueError(
            f"generate_params (ordinal_numbers): task_type={task_type!r} matches no item "
            f"template (seed={seed}, grade={grade}). Implemented task types are "
            f"{sorted({t['task_type'] for t in _ITEM_TEMPLATES})}. Declaring a variant no "
            f"template carries renders an arbitrary item under a name that promises a "
            f"specific one."
        )

    template_def = rng.choice(candidates)

    min_ord = int(profile.get("min_ordinal", min_ord))
    max_ord = int(profile.get("max_ordinal", max_ord))
    
    number_candidates = list(range(min_ord, max_ord + 1))
    from backend.app.practice_gen.generators.number_difficulty import generate_number_by_window
    n = generate_number_by_window(number_candidates, diff_scalar, d=max(4, len(number_candidates)//2), rng=rng, num_type="ordinal")

    # If asking for next symbol, ensure n + 1 stays within curriculum bounds
    if template_def["answer_key"] == "next_symbol" and n >= max_ord:
        n = max(min_ord, max_ord - 1)

    # An enumerated line-up cannot have a 47th member. Swap to the scalable
    # describe_position form rather than clamping `n`, which would stop scalar 1.0
    # reaching a G3 competency ceiling of 100th.
    # The fallback keeps the POOL the chosen template was written for: an enumerated
    # object line-up that overflows must fall back to the scalable OBJECT form, not to
    # the pupils' one, or the clause `objects` silently stops being served at exactly
    # the ordinals a G2/G3 node reaches.
    if template_def.get("needs_lineup") and n > len(_lineup_pool(template_def)):
        _pool = template_def.get("lineup_pool")
        template_def = next(t for t in _ITEM_TEMPLATES
                            if t["task_type"] == "describe_position"
                            and not t.get("needs_lineup")
                            and t.get("lineup_pool") == _pool)

    symbol  = _ordinal_suffix(n)
    word    = _ordinal_word(n)

    # Resolve answer based on answer_key
    answer_key = template_def["answer_key"]
    if answer_key == "n":
        answer = n
    elif answer_key == "word":
        answer = word
    elif answer_key == "symbol":
        answer = symbol
    elif answer_key == "earlier_symbol":
        n2 = rng.randint(min_ord, max_ord)
        while n2 == n and max_ord > min_ord:
            n2 = rng.randint(min_ord, max_ord)
        symbol2 = _ordinal_suffix(n2)
        answer  = symbol if n < n2 else symbol2
    elif answer_key == "object_at_position":
        # The answer is whatever stands at the nth place -- an object for the object
        # templates, a pupil for the name ones -- and the distractors are the others in
        # the same row.
        lineup = _lineup_pool(template_def)[:max(n, 4)]
        answer = lineup[n - 1]
    elif answer_key == "next_symbol":
        answer = _ordinal_suffix(n + 1)
        n2, symbol2 = None, None
    else:
        answer = symbol

    # Render question text
    tpl = template_def["template"]
    ctx: Dict[str, Any] = {"n": n, "symbol": symbol, "word": word}
    if "{lineup}" in tpl:
        names = _lineup_pool(template_def)[:max(n, 4)]
        ctx["lineup"] = ", ".join(names[:-1]) + " and " + names[-1]
    if "{actor}" in tpl:
        ctx["actor"] = _LINEUP_NAMES[(n - 1) % len(_LINEUP_NAMES)]
    if "{object_singular}" in tpl:
        # Drawn from the RNG, not indexed by `n`. Indexing by n degenerates the moment
        # the difficulty window pins n to the competency ceiling: at G2 every sample
        # keys n=20 and at G3 every sample keys n=100, so `(n - 1) % 10` returned the
        # same noun on every seed and the whole node rendered "spoons" forever. Measured
        # over 200 seeds before this line changed: 23 object samples, 23 of them spoons.
        singular, plural = rng.choice(_LINEUP_OBJECTS)
        ctx["object_singular"], ctx["objects_plural"] = singular, plural
    if "symbol2" in tpl:
        if "n2" not in locals() or n2 is None:
            n2 = rng.randint(min_ord, max_ord)
            while n2 == n and max_ord > min_ord:
                n2 = rng.randint(min_ord, max_ord)
            symbol2 = _ordinal_suffix(n2)
        ctx["symbol2"] = symbol2
    try:
        question_text = tpl.format(**ctx)
    except KeyError:
        question_text = tpl

    curriculum_max = bounds["max_ordinal"]
    # Generate 3 unique distractors strictly within [min_ord, curriculum_max]
    distractors = []
    if answer_key == "object_at_position":
        # Distractors are the other objects in the same row -- an ordinal would not be
        # a plausible wrong answer to "which one is in 3rd place?", and would key a
        # different skill.
        others = [nm for nm in _lineup_pool(template_def)[:max(n, 4)] if nm != answer]
        rng.shuffle(others)
        return {
            "blank_target": "answer",
            "n": n, "symbol": symbol, "word": word,
            "question_text": question_text,
            "answer": answer,
            "task_type": task_type,
            "distractors": others[:3],
        }

    other_ns = [cand_n for cand_n in range(min_ord, curriculum_max + 1) if cand_n != n]
    rng.shuffle(other_ns)

    for candidate_n in other_ns:
        if len(distractors) >= 3:
            break
        if answer_key == "n":
            cand = candidate_n
        elif answer_key == "word":
            cand = _ordinal_word(candidate_n)
        else:
            cand = _ordinal_suffix(candidate_n)

        if cand != answer and cand not in distractors:
            distractors.append(cand)

    return {
        "blank_target": "answer",
        "n":             n,
        "symbol":        symbol,
        "word":          word,
        "question_text": question_text,
        "answer":        answer,
        "task_type":     task_type,
        "distractors":   distractors,
    }


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    """Return 2–4 step-by-step hints for an ordinal number problem."""
    n         = values["n"]
    symbol    = values["symbol"]
    word      = values["word"]
    task_type = values["task_type"]

    ord_label = VOCAB_ORDINAL.resolve(cumulative_vocab)
    pos_label = VOCAB_POSITION.resolve(cumulative_vocab)

    hints: List[str] = []

    if task_type == "identify_ordinal":
        hints.append(f"Ordinal numbers describe {pos_label} in order.")
        hints.append(f"The number {n} in order is called the {symbol} ({word}).")
        hints.append(f"Remember: 1st = first, 2nd = second, 3rd = third, then add -th.")

    elif task_type == "find_position":
        hints.append(f"'{word.capitalize()}' is an {ord_label} word.")
        hints.append(f"Count positions from the start: 1st, 2nd, 3rd, … until you reach {word}.")
        hints.append(f"{word.capitalize()} = position {n}, written as {symbol}.")

    elif task_type == "describe_position":
        hints.append(f"Count the objects in order from the front: 1st, 2nd, 3rd, …")
        hints.append(f"The {symbol} ({word}) place is position number {n}.")
        hints.append(f"Find the object standing at position {n}.")

    else:  # compare_positions
        hints.append(f"Smaller ordinal numbers come earlier (closer to the start).")
        hints.append(f"Compare the numbers: the smaller ordinal position is earlier.")
        hints.append(f"{symbol} means position {n}.")

    return hints


# ─── DNA instance ─────────────────────────────────────────────────────────────

ORDINAL_NUMBERS_DNA = DNA(
    concept="ordinal_numbers",
    dna_type="static_bank",
    answer_formula=None,
    param_bounds=_PARAM_BOUNDS,
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=[
        "mcq",
        "cloze",
    ],
    requires_context=True,
    visual_home=None,
    difficulty_axes=_DIFFICULTY_AXES,
)
