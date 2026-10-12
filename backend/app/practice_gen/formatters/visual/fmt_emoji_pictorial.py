"""
fmt_emoji_pictorial.py — Emoji Pictorial Model formatter

NEW formatter — Aligns with MATATAG competency:
"Illustrate addition/subtraction using a variety of concrete and pictorial models"

Shows emoji representations of objects that students can count.
For addition: Shows two groups of emojis, asks for total
For subtraction: Shows a group with some crossed out, asks for remainder

Example addition (putting_together):
    Question: "🍎🍎🍎 and 🍎🍎. How many apples altogether?"
    Answer: 5

Example addition (counting_up):
    Question: "Start with 🍎🍎🍎. Add 🍎🍎 more. How many now?"
    Answer: 5

Example subtraction (taking_away):
    Question: "🍎🍎🍎🍎🍎 take away 🍎🍎. How many left?"
    Answer: 3  (shows 3 apples, 2 crossed out)

visual_params:
    {
        "emoji": str,           # The emoji to use (🍎, ⭐, etc.)
        "group_a": int,         # First group count
        "group_b": int,         # Second group count (added or removed)
        "operation": str,       # "addition" or "subtraction"
        "layout": str,          # "inline" | "stacked" | "separated"
        "show_crossed": bool,   # For subtraction: show crossed-out emojis
    }

Grade band: (1, 2)

Traps:
    count_one_group   — counts only first or second group
    count_crossed     — includes crossed-out items in count
    off_by_one        — answer ± 1
"""

import random
from typing import List, Optional

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext
from backend.app.practice_gen.slots import E, S, derived, fill, join
from backend.app.practice_gen.formatters._distractor_fallback import augment_distractors


# ─────────────────────────────────────────────────────────────────────────────
# Emoji Sets (theme-appropriate for young learners)
# ─────────────────────────────────────────────────────────────────────────────

_EMOJI_SETS = {
    "fruit": ["🍎", "🍊", "🍋", "🍇", "🍓", "🍌", "🍑", "🍒"],
    "animals": ["🐶", "🐱", "🐰", "🐻", "🐸", "🐥", "🐢", "🐟"],
    "nature": ["🌸", "🌻", "🌺", "🌷", "🌼", "🍀", "🌳", "⭐"],
    "objects": ["📚", "✏️", "🎈", "🎁", "⚽", "🧸", "🎨", "🎵"],
    "food": ["🍪", "🍩", "🧁", "🍬", "🍫", "🥤", "🍕", "🌮"],
}

# Flat list for random selection
_ALL_EMOJIS = [e for emojis in _EMOJI_SETS.values() for e in emojis]

# Emoji names for question text
_EMOJI_NAMES = {
    "🍎": "apple", "🍊": "orange", "🍋": "lemon", "🍇": "grape", 
    "🍓": "strawberry", "🍌": "banana", "🍑": "peach", "🍒": "cherry",
    "🐶": "puppy", "🐱": "kitten", "🐰": "bunny", "🐻": "bear",
    "🐸": "frog", "🐥": "chick", "🐢": "turtle", "🐟": "fish",
    "🌸": "flower", "🌻": "sunflower", "🌺": "hibiscus", "🌷": "tulip",
    "🌼": "daisy", "🍀": "clover", "🌳": "tree", "⭐": "star",
    "📚": "book", "✏️": "pencil", "🎈": "balloon", "🎁": "gift",
    "⚽": "ball", "🧸": "teddy bear", "🎨": "paint", "🎵": "note",
    "🍪": "cookie", "🍩": "donut", "🧁": "cupcake", "🍬": "candy",
    "🍫": "chocolate", "🥤": "drink", "🍕": "pizza", "🌮": "taco",
}


# The copula choice the stem makes ("There is 1" / "There are 5"). Named so its slot can
# declare the generator's own two choices as its domain (H3, owner ruling 28).
_COPULAS = ("is", "are")
# Option letters, A first. `_OPTION_KEYS[i]` is `chr(65 + i)` for the four options this
# formatter offers; named so the keyed letter's slot can declare it (H3).
_OPTION_KEYS = ("A", "B", "C", "D")
_NAMES_DOMAIN = "noun:backend.app.practice_gen.formatters.visual.fmt_emoji_pictorial._EMOJI_NAMES"


def _pluralize(name: str, count: int) -> str:
    """Simple pluralization for emoji names."""
    if count == 1:
        return name
    # Handle irregular plurals
    if name in ["fish"]:
        return name
    if name.endswith("ch") or name.endswith("sh") or name.endswith("x") or name.endswith("s"):
        return name + "es"
    if name.endswith("y") and name[-2] not in "aeiou":
        return name[:-1] + "ies"
    return name + "s"


def _emoji_slot(emoji: str) -> S:
    """
    One drawn emoji as a slot (batch H4-0, owner ruling 42): a member of this formatter's own
    `_EMOJI_SETS` or an interest theme's declared emoji -- the two places `emoji` is drawn from.
    A repeated display is `join("", [_emoji_slot(emoji)] * n)`, identical to `emoji * n`.
    """
    from backend.app.practice_gen.generators.interest import _INTERESTS
    members = tuple(_ALL_EMOJIS) + tuple(d["emoji"] for d in _INTERESTS.values() if isinstance(d.get("emoji"), str))
    return S(emoji, E(members, "fmt_emoji_pictorial._EMOJI_SETS and the interest themes' emojis"))


def _get_emoji_name(emoji: str, count: int) -> str:
    """Get the name of an emoji, pluralized if needed."""
    name = _EMOJI_NAMES.get(emoji, "item")
    return _pluralize(name, count)


# ─────────────────────────────────────────────────────────────────────────────
# Parameter Builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_params(
    ctx: QuestionContext,
    rng: random.Random,
) -> dict:
    """
    Build emoji pictorial parameters from DNA context.
    """
    values = ctx.values
    if ctx.dna_concept == "counting":
        operation = "counting"
        a = ctx.correct_answer
        b = 0
    elif ctx.dna_concept in ("addition", "subtraction", "multiplication"):
        # This read "ctx.dna_concept if ctx.dna_concept in ('addition', 'subtraction')
        # else 'addition'" -- a silent default that drew `a + b` items beside an answer
        # keyed `a x b` the moment this formatter was pointed at a multiplication node.
        # The picture and the key contradicting each other is the one defect a
        # PICTORIAL model cannot survive, so an unhandled concept fails loudly instead:
        # a formatter that has no branch for a DNA does not render that DNA, it renders
        # something else (the same lesson fmt_number_line's money branch records).
        operation = ctx.dna_concept
        a = values.get("a", 3)
        b = values.get("b", 2)
    else:
        raise ValueError(
            f"emoji_pictorial has no pictorial model for concept {ctx.dna_concept!r} "
            f"(node={ctx.node_id}, seed={ctx.seed}). Add the branch that draws it "
            f"before declaring the pair compatible -- defaulting to 'addition' draws a "
            f"picture that contradicts the item's own answer key."
        )
    
    # An explicitly requested interest must reach the learner-visible picture.
    # Random selection here made the visual contradict its own interest metadata
    # (for example, a ppop request could draw a taco instead of the bank's microphone).
    # Automatic/neutral requests retain the deterministic seeded variety.
    if ctx.interest_theme:
        from backend.app.practice_gen.generators.interest import get_interest_emoji

        emoji = get_interest_emoji(ctx.interest_theme, ctx.grade)
    else:
        emoji = rng.choice(_ALL_EMOJIS)
    
    # Get emoji name for reveal text
    base_name = _EMOJI_NAMES.get(emoji, "item")
    
    # Layout options (for addition only; subtraction shows all items inline)
    layout = rng.choice(["inline", "stacked", "separated"]) if operation == "addition" else "inline"
    
    # Build the display strings (capped to prevent massive JSON payloads and UI clutter)
    # `a` repeats the answer on a counting item and the operand `a` otherwise (read above).
    a_slot = S(a, "value:answer" if operation == "counting" else "value:a")
    display = join("", [_emoji_slot(emoji)] * a) if a <= 20 else fill("(Large group of {a} {pluralize})", a=a_slot, pluralize=S(_pluralize(base_name, a), _NAMES_DOMAIN))
    if a == 0: display = "0"

    if operation == "multiplication":
        # b groups of a. "5 groups of 3" is mat_g2_na_q3_0's own wording and
        # mat_g2_na_q3_1 names "groups of equal quantities" outright, so the groups --
        # not one undivided heap of a*b items -- are the model the clause asks for.
        one_group = join("", [_emoji_slot(emoji)] * a) if a <= 20 else fill("(group of {a} {pluralize})", _src=('operation',), a=S(a, "value:a"), pluralize=S(_pluralize(base_name, a), _NAMES_DOMAIN))
        display = join("   ", [S(one_group, "fill")] * b) if b <= 10 \
            else fill("({b} groups of {a} {pluralize})", _src=('operation',), b=S(b, "value:b"), a=S(a, "value:a"), pluralize=S(_pluralize(base_name, a), _NAMES_DOMAIN))

    if operation == "addition":
        display_b = join("", [_emoji_slot(emoji)] * b) if b <= 20 else fill("(Large group of {b} {pluralize})", _src=('operation',), b=S(b, "value:b"), pluralize=S(_pluralize(base_name, b), _NAMES_DOMAIN))
        if b == 0: display_b = "0"
    
    # For subtraction, build reveal display showing remaining items with explanation
    reveal_display = None
    reveal_text = None
    if operation == "subtraction":
        remaining = a - b
        # Show remaining emojis
        reveal_display = join("", [_emoji_slot(emoji)] * remaining) if remaining <= 20 else fill("(Large group of {remaining} {pluralize})", _src=('operation',), remaining=S(remaining, "value:result"), pluralize=S(_pluralize(base_name, remaining), _NAMES_DOMAIN))
        if remaining == 0: reveal_display = "(none left)"
        # Text explanation
        reveal_text = fill("{remaining} {v}", _src=('operation',), remaining=S(remaining, "value:result"), v=S(_pluralize(base_name, remaining) if remaining != 1 else base_name, _NAMES_DOMAIN))
    
    params = {
        "emoji": emoji,
        "group_a": a,
        "group_b": b,
        "operation": operation,
        "layout": layout,
        "display": display,  # What to show initially
    }
    
    if operation == "addition":
        params["display_b"] = display_b
    
    if reveal_display:
        params["reveal_display"] = reveal_display
    if reveal_text:
        params["reveal_text"] = reveal_text
    
    return params

def _correct_answer(params: dict) -> int:
    """Calculate the correct answer."""
    a = params["group_a"]
    b = params["group_b"]
    if params["operation"] == "addition":
        return a + b
    elif params["operation"] == "subtraction":
        return a - b
    elif params["operation"] == "multiplication":
        return a * b
    else:  # counting
        return a


def _generate_distractors(
    correct: int,
    params: dict,
    rng: random.Random,
) -> List[int]:
    """
    Generate plausible wrong answers.
    """
    a = params["group_a"]
    b = params["group_b"]
    operation = params["operation"]
    
    distractors = set()
    
    # Count only one group
    distractors.add(a)
    distractors.add(b)

    # Off by one
    if correct > 0:
        distractors.add(correct - 1)
    distractors.add(correct + 1)

    # Wrong operation
    if operation == "addition":
        if a >= b:
            distractors.add(a - b)
    elif operation == "multiplication":
        # Added the groups instead of counting them all (a + b), and miscounted the
        # groups by one in either direction -- the two misconceptions an equal-groups
        # picture actually produces. `distractors` already carries a and b themselves
        # ("counted one group only", "counted the groups").
        distractors.add(a + b)
        distractors.add(correct - a)
        distractors.add(correct + a)
    else:
        distractors.add(a + b)

    # Count all (for subtraction, count including crossed out)
    if operation == "subtraction":
        distractors.add(a)

    # Remove correct answer and invalid values
    distractors.discard(correct)
    distractors = {d for d in distractors if d >= 0}
    
    # Convert to list and shuffle
    distractor_list = list(distractors)
    rng.shuffle(distractor_list)
    
    if len(distractor_list) < 3:
        distractor_list = augment_distractors(distractor_list, correct, target=3, max_delta=5)
        if len(distractor_list) < 3:
            raise ValueError(f"Formatter 'emoji_pictorial' requires at least 3 unique distractors, but got {len(distractor_list)}")

    return distractor_list[:3]


def _build_question_text(params: dict, context_variant: str = "word_problem") -> str:
    """
    Build the question text with emoji representation.
    """
    emoji = params["emoji"]
    a = params["group_a"]
    b = params["group_b"]
    operation = params["operation"]
    
    # Get the base name for pluralization
    base_name = _EMOJI_NAMES.get(emoji, "item")
    name_a = _get_emoji_name(emoji, a)
    name_b = _get_emoji_name(emoji, b)
    name_plural = _pluralize(base_name, 2)
    
    # Use display strings from params which are capped
    group_a_str = params.get("display", "(none)")
    group_b_str = params.get("display_b", "(none)")
    
    if operation == "addition":
        # Line 1: Show starting amount
        if a == 0:
            line1 = fill("There are 0 {name_plural}.", name_plural=S(name_plural, _NAMES_DOMAIN))
        else:
            line1 = fill("{group_a_str} — There {v} {a} {name_a}.", group_a_str=S(group_a_str, "fill"), v=S('is' if a == 1 else 'are', "enum:backend.app.practice_gen.formatters.visual.fmt_emoji_pictorial._COPULAS"), a=S(a, "value:a", src=("a",)), name_a=S(name_a, _NAMES_DOMAIN))
        
        # Line 2: Show amount being added
        if b == 0:
            line2 = fill("0 more {name_plural} are added.", name_plural=S(name_plural, _NAMES_DOMAIN))
        else:
            line2 = fill("{group_b_str} — {b} more {name_b} {v} added.", group_b_str=S(group_b_str, "fill"), b=S(b, "value:b", src=("b",)), name_b=S(name_b, _NAMES_DOMAIN), v=S('is' if b == 1 else 'are', "enum:backend.app.practice_gen.formatters.visual.fmt_emoji_pictorial._COPULAS"))
        
        # Line 3: Question
        line3 = fill("How many total {name_plural} are there?", name_plural=S(name_plural, _NAMES_DOMAIN))
        
    elif operation == "multiplication":
        # Group language only. "multiplication", "product" and "times" are all
        # NOT_YET_KNOWN at mat_g2_na_q3_0, whose competency is stated entirely in
        # groups ("5 groups of 3", "5 threes"), so the stem names what is drawn and
        # asks for the total.
        unit = "group" if b == 1 else "groups"
        line1 = fill("{group}", group=S(group_a_str, "fill"))   # the drawn groups (H3-R2)
        line2 = fill("There {v} {b} {unit} of {a} {name_a}.", v=S('is' if b == 1 else 'are', "enum:backend.app.practice_gen.formatters.visual.fmt_emoji_pictorial._COPULAS"), b=S(b, "value:b", src=("b",)), unit=S(unit, E(("group", "groups"), "group, singular or plural")), a=S(a, "value:a", src=("a",)), name_a=S(name_a, _NAMES_DOMAIN))
        line3 = fill("How many {name_plural} are there in all?", name_plural=S(name_plural, _NAMES_DOMAIN))

    elif operation == "subtraction":
        # Structured slots (H3, owner ruling 28); each string is identical to the f-string
        # it replaced. `a`/`b` repeat the DNA's generated operands.
        A, B = S(a, "value:a"), S(b, "value:b")
        plural = S(name_plural, _NAMES_DOMAIN)
        # Line 1: Show starting amount
        if a == 0:
            line1 = fill("There are 0 {names}.", names=plural)
        else:
            line1 = fill("{group} — There {verb} {a} {name}.",
                         group=S(group_a_str, "fill"),
                         verb=S(_COPULAS[0] if a == 1 else _COPULAS[1],
                                "enum:backend.app.practice_gen.formatters.visual.fmt_emoji_pictorial._COPULAS"),
                         a=A, name=S(name_a, _NAMES_DOMAIN))
        
        # Line 2: State how many taken away (no emoji display for taken items)
        if b == 0:
            line2 = fill("Taking away 0 {names}.", names=plural)
        else:
            line2 = fill("Taking away {b} {name}.", b=B, name=S(name_b, _NAMES_DOMAIN))
        
        # Line 3: Question
        line3 = fill("How many {names} are left?", names=plural)
        
    else:  # counting
        # A COUNTING item may not state its own count. This branch printed
        #     "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ — There are 10 stars."
        #     "Count the stars."
        #     "How many stars are there in all?"
        # so the stem supplied the answer it then asked for, and the item measured
        # nothing about counting. Found by blind review of mat_g1_na_q1_0 on
        # 2026-09-10 ("A counting item that supplies its own answer measures nothing
        # about counting"), which also caught the large-group form printing "There are
        # 73 drinks." in the sentence before asking for that count.
        #
        # The ADDITION and SUBTRACTION branches above legitimately state `a`: there it
        # is a given operand the pupil is handed, not the quantity being asked for.
        # Only the counting branch is asking for `a` itself.
        # Structured slots (H5, owner rulings 28 and 35); identical to the f-strings they
        # replaced. The picture is built from the count `a`, the generated answer.
        plural = S(name_plural, _NAMES_DOMAIN)
        if not a:
            line1 = fill("(no {names} are shown)", names=plural)
        elif a <= 20:
            line1 = fill("{group}", group=S(group_a_str, "fill", src=("answer",)))
        else:
            line1 = fill("(Large group of {a} {names})", a=S(a, "value:answer"),
                         names=S(_pluralize(base_name, a), _NAMES_DOMAIN))
        line2 = fill("Count the {names}.", names=plural)
        line3 = fill("How many {names} are there in all?", names=plural)
    return fill("{line1}\n{line2}\n{line3}",
                line1=S(line1, "fill"), line2=S(line2, "fill"), line3=S(line3, "fill"))


# ─────────────────────────────────────────────────────────────────────────────
# Main Formatter Function
# ─────────────────────────────────────────────────────────────────────────────

def format_emoji_pictorial(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Format a problem using emoji pictorial model.

    Args:
        ctx: QuestionContext with DNA values
        rng: Random number generator
        interaction_mode: "read" (count emojis) - set mode not yet implemented
        answer_collection: "mcq" | "fill_in_blank"

    Returns:
        FormattedProblem with emoji visual representation

    Raises:
        ValueError: If any of (a, b, number, answer, start) > 100. The
            emoji_pictorial formatter cannot represent groups larger
            than 100 (the per-item emoji would explode the JSON payload
            and the UI would be unreadable). This is fail-fast per
            AGENTS.md rule #4: surface the incompatibility, do not
            silently degrade to a placeholder.
    """
    # Numeric limit check: emoji_pictorial cannot represent groups > 100.
    # (Moved here from adapter.py so the formatter owns its own constraints.)
    vals = [
        ctx.values.get("a"),
        ctx.values.get("b"),
        ctx.values.get("number"),
        ctx.values.get("answer"),
        ctx.values.get("start"),
    ]
    int_vals = [v for v in vals if isinstance(v, (int, float))]
    max_val = max(int_vals) if int_vals else 0
    if max_val > 100:
        raise ValueError(
            f"emoji_pictorial: cannot represent max_val ({max_val}) > 100; "
            f"this profile produces a group too large for emoji display. "
            f"Use a different formatter (e.g. place_value_blocks_set) for "
            f"values > 100."
        )

    # Build parameters
    params = _build_params(ctx, rng)
    correct = _correct_answer(params)
    
    context_variant = ctx.values.get("context")
    if context_variant is None and ctx.difficulty_profile:
        context_variant = ctx.difficulty_profile.get("context")
    if context_variant is None:
        context_variant = "pure"

    # Build question text
    question_text = _build_question_text(params, context_variant)
    
    # Build distractors and MCQ options
    distractors = _generate_distractors(correct, params, rng)
    
    mcq_options = None
    final_answer = correct
    if answer_collection == "mcq":
        all_options = [correct] + distractors[:3]
        rng.shuffle(all_options)
        mcq_options = [
            {"key": _OPTION_KEYS[i], "value": opt, "is_correct": opt == correct}
            for i, opt in enumerate(all_options)
        ]
        final_answer = fill("{key}", key=S(next(o["key"] for o in mcq_options if o["is_correct"]),
                                            "enum:backend.app.practice_gen.formatters.visual.fmt_emoji_pictorial._OPTION_KEYS"))
    
    # Build format data
    format_data = {"visual_params": params}
    if mcq_options:
        format_data["mcq_options"] = mcq_options
    
    fmt = f"{interaction_mode}_{answer_collection}"
    
    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_emoji",
        node_id=ctx.node_id,
        competency_text=ctx.competency_text,
        grade=ctx.grade,
        seed=ctx.seed,
        question_text=question_text,
        correct_answer=final_answer,
        distractors=distractors,
        hints=ctx.hints,
        format=fmt,
        format_data=format_data,
        is_visual=True,
        visual_type="EmojiPictorial",
        visual_params=params,
        interaction_mode=interaction_mode,
        answer_collection=answer_collection,
        difficulty_profile=ctx.difficulty_profile or {},
        difficulty_axes_served=ctx.difficulty_axes_served,
        experience="standard",
        experience_config=None,
        interest_theme=ctx.interest_theme,
        spine_id=ctx.spine_id,
        given_values={k: v for k, v in ctx.values.items() if k != ctx.blank_target} if ctx.values else None,
        blank_target=ctx.blank_target,
    )
