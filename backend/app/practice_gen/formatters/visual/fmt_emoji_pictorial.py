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
    a = values.get("a", 3)
    b = values.get("b", 2)
    
    # Determine operation from DNA concept
    operation = ctx.dna_concept if ctx.dna_concept in ("addition", "subtraction") else "addition"
    
    # Select random emoji
    emoji = rng.choice(_ALL_EMOJIS)
    
    # Get emoji name for reveal text
    base_name = _EMOJI_NAMES.get(emoji, "item")
    
    # Layout options (for addition only; subtraction shows all items inline)
    layout = rng.choice(["inline", "stacked", "separated"]) if operation == "addition" else "inline"
    
    # Build the display strings (capped to prevent massive JSON payloads and UI clutter)
    display = (emoji * a) if a <= 20 else f"(Large group of {a} {_pluralize(base_name, a)})"
    if a == 0: display = "0"

    if operation == "addition":
        display_b = (emoji * b) if b <= 20 else f"(Large group of {b} {_pluralize(base_name, b)})"
        if b == 0: display_b = "0"
    
    # For subtraction, build reveal display showing remaining items with explanation
    reveal_display = None
    reveal_text = None
    if operation == "subtraction":
        remaining = a - b
        # Show remaining emojis
        reveal_display = (emoji * remaining) if remaining <= 20 else f"(Large group of {remaining} {_pluralize(base_name, remaining)})"
        if remaining == 0: reveal_display = "(none left)"
        # Text explanation
        reveal_text = f"{remaining} {_pluralize(base_name, remaining) if remaining != 1 else base_name}"
    
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
    else:
        return a - b


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


def _build_question_text(params: dict) -> str:
    """
    Build the question text with emoji representation.
    
    Format:
    Line 1: Show and state how many items there are
    Line 2: Show and state how many are added/taken away  
    Line 3: Ask the question
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
            line1 = f"There are 0 {name_plural}."
        else:
            line1 = f"{group_a_str} — There {'is' if a == 1 else 'are'} {a} {name_a}."
        
        # Line 2: Show amount being added
        if b == 0:
            line2 = f"0 more {name_plural} are added."
        else:
            line2 = f"{group_b_str} — {b} more {name_b} {'is' if b == 1 else 'are'} added."
        
        # Line 3: Question
        line3 = f"How many total {name_plural} are there?"
        
    else:  # subtraction
        # Line 1: Show starting amount
        if a == 0:
            line1 = f"There are 0 {name_plural}."
        else:
            line1 = f"{group_a_str} — There {'is' if a == 1 else 'are'} {a} {name_a}."
        
        # Line 2: State how many taken away (no emoji display for taken items)
        if b == 0:
            line2 = f"0 {name_plural} are taken away."
        else:
            line2 = f"{b} {name_b} {'is' if b == 1 else 'are'} taken away."
        
        # Line 3: Question
        line3 = f"How many {name_plural} are left?"
    
    return f"{line1}\n{line2}\n{line3}"


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
    
    # Build question text
    question_text = _build_question_text(params)
    
    # Build distractors and MCQ options
    distractors = _generate_distractors(correct, params, rng)
    
    mcq_options = None
    final_answer = correct
    if answer_collection == "mcq":
        all_options = [correct] + distractors[:3]
        rng.shuffle(all_options)
        mcq_options = [
            {"key": chr(65 + i), "value": opt, "is_correct": opt == correct}
            for i, opt in enumerate(all_options)
        ]
        final_answer = next(o["key"] for o in mcq_options if o["is_correct"])
    
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
