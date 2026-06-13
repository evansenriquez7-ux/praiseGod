"""
Practice Generation — API Adapter
===================================

Main entry point for the new practice generation pipeline.

Provides:
  - generate_problem()  — single problem generation
  - generate_batch()    — batch of varied problems for a node
  - apply_formatter()   — routes ctx to the correct formatter
  - apply_experience()  — wraps FormattedProblem with an experience
  - to_legacy_dict()    — backward-compat shim for the existing API
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from .compatibility import get_formatters_for_dna
from .dna.base import FormattedProblem, QuestionContext
from .generators.base_generator import _import_dna_module, generate_context
from .registry import get_node_dnas, get_node_info


# ═══════════════════════════════════════════════════════════════════════════════
# FORMATTER WEIGHT MAP
# Textual formatters (mcq, numeric_input) are preferred for the majority of
# problems so the primary formatter bias is maintained.
# ═══════════════════════════════════════════════════════════════════════════════

_FORMATTER_WEIGHTS: Dict[str, float] = {
    "mcq": 3.0,
    "numeric_input": 2.5,
    "cloze": 1.5,
    "ordering": 1.0,
    "true_false": 1.0,
    "error_detect": 0.8,
    "fill_in_blank": 1.0,
    # Visual formatters get equal weight; specific bias toward the "home" type
    # is handled by the DNA's visual_home field.
}

_DEFAULT_WEIGHT = 0.6   # weight for any formatter not explicitly listed above


# ═══════════════════════════════════════════════════════════════════════════════
# FORMATTER ROUTER
# Maps compatibility table name → (module_path, function_name, extra_kwargs)
#
# For visual formatters that support read/set modes, the default is "read".
# Companion "set" entries map to the same function with interaction_mode="set".
# ═══════════════════════════════════════════════════════════════════════════════

# fmt: (module_attr_path, func_name, kwargs)
_FORMATTER_ROUTES: Dict[str, tuple] = {
    # ── Textual ───────────────────────────────────────────────────────────────
    "mcq": (
        "backend.app.practice_gen.formatters.textual.fmt_mcq",
        "format_mcq",
        {},
    ),
    "cloze": (
        "backend.app.practice_gen.formatters.textual.fmt_cloze",
        "format_cloze",
        {},
    ),
    # numeric_input is now an alias for cloze (use context variant instead)
    "numeric_input": (
        "backend.app.practice_gen.formatters.textual.fmt_cloze",
        "format_cloze",
        {},
    ),
    "ordering": (
        "backend.app.practice_gen.formatters.textual.fmt_ordering",
        "format_ordering",
        {},
    ),
    "true_false": (
        "backend.app.practice_gen.formatters.textual.fmt_true_false",
        "format_true_false",
        {},
    ),
    "error_detect": (
        "backend.app.practice_gen.formatters.textual.fmt_error_detect",
        "format_error_detect",
        {},
    ),
    # fill_in_blank → cloze (same sentence-blank approach, different label)
    "fill_in_blank": (
        "backend.app.practice_gen.formatters.textual.fmt_cloze",
        "format_cloze",
        {},
    ),
    # ── Visual – read ─────────────────────────────────────────────────────────
    "number_line_read": (
        "backend.app.practice_gen.formatters.visual.fmt_number_line",
        "format_number_line",
        {"interaction_mode": "read", "answer_collection": "mcq"},
    ),
    "array_grid_read": (
        "backend.app.practice_gen.formatters.visual.fmt_array_grid",
        "format_array_grid",
        {"interaction_mode": "read", "answer_collection": "mcq"},
    ),
    "place_value_blocks_read": (
        "backend.app.practice_gen.formatters.visual.fmt_place_value_blocks",
        "format_place_value_blocks",
        {"interaction_mode": "read", "answer_collection": "mcq"},
    ),
    "peso_money_read": (
        "backend.app.practice_gen.formatters.visual.fmt_peso_money",
        "format_peso_money",
        {"interaction_mode": "read", "answer_collection": "mcq"},
    ),
    "clock_read": (
        "backend.app.practice_gen.formatters.visual.fmt_clock",
        "format_clock",
        {"interaction_mode": "read", "answer_collection": "mcq"},
    ),
    "bar_chart_read": (
        "backend.app.practice_gen.formatters.visual.fmt_bar_chart",
        "format_bar_chart",
        {"interaction_mode": "read", "answer_collection": "mcq"},
    ),
    "pictograph_read": (
        "backend.app.practice_gen.formatters.visual.fmt_pictograph",
        "format_pictograph",
        {"interaction_mode": "read", "answer_collection": "mcq"},
    ),
    "fraction_model_read": (
        "backend.app.practice_gen.formatters.visual.fmt_fraction_model",
        "format_fraction_model",
        {"interaction_mode": "read", "answer_collection": "mcq"},
    ),
    "ruler_measure": (
        "backend.app.practice_gen.formatters.visual.fmt_ruler_measure",
        "format_ruler_measure",
        {"interaction_mode": "read", "answer_collection": "mcq"},
    ),
    "grid_area": (
        "backend.app.practice_gen.formatters.visual.fmt_bar_chart",
        "format_bar_chart",
        {"interaction_mode": "read", "answer_collection": "mcq"},
    ),
    "sort_order": (
        "backend.app.practice_gen.formatters.textual.fmt_ordering",
        "format_ordering",
        {},
    ),
    "shape_board": (
        "backend.app.practice_gen.formatters.visual.fmt_shape_board",
        "format_shape_board",
        {"interaction_mode": "read", "answer_collection": "mcq"},
    ),
    "ten_frame": (
        "backend.app.practice_gen.formatters.visual.fmt_ten_frame",
        "format_ten_frame",
        {"interaction_mode": "read", "answer_collection": "mcq"},
    ),
    "balance_scale": (
        "backend.app.practice_gen.formatters.visual.fmt_balance_scale",
        "format_balance_scale",
        {"interaction_mode": "read", "answer_collection": "mcq"},
    ),
    "pattern_sequence": (
        "backend.app.practice_gen.formatters.visual.fmt_pattern_sequence",
        "format_pattern_sequence",
        {"interaction_mode": "read", "answer_collection": "mcq"},
    ),
    "calendar_read": (
        "backend.app.practice_gen.formatters.visual.fmt_calendar",
        "format_calendar",
        {"interaction_mode": "read", "answer_collection": "mcq"},
    ),
    "categorize": (
        "backend.app.practice_gen.formatters.visual.fmt_shape_board",
        "format_shape_board",
        {"interaction_mode": "read", "answer_collection": "mcq"},
    ),
    # ── Visual – set ──────────────────────────────────────────────────────────
    "number_line_set": (
        "backend.app.practice_gen.formatters.visual.fmt_number_line",
        "format_number_line",
        {"interaction_mode": "set", "answer_collection": "fill_in_blank"},
    ),
    "array_grid_set": (
        "backend.app.practice_gen.formatters.visual.fmt_array_grid",
        "format_array_grid",
        {"interaction_mode": "set", "answer_collection": "fill_in_blank"},
    ),
    "place_value_blocks_set": (
        "backend.app.practice_gen.formatters.visual.fmt_place_value_blocks",
        "format_place_value_blocks",
        {"interaction_mode": "set", "answer_collection": "fill_in_blank"},
    ),
    "peso_money_build": (
        "backend.app.practice_gen.formatters.visual.fmt_peso_money",
        "format_peso_money",
        {"interaction_mode": "set", "answer_collection": "fill_in_blank"},
    ),
    "clock_set": (
        "backend.app.practice_gen.formatters.visual.fmt_clock",
        "format_clock",
        {"interaction_mode": "set", "answer_collection": "fill_in_blank"},
    ),
    "bar_chart_set": (
        "backend.app.practice_gen.formatters.visual.fmt_bar_chart",
        "format_bar_chart",
        {"interaction_mode": "set", "answer_collection": "fill_in_blank"},
    ),
    "fraction_shade": (
        "backend.app.practice_gen.formatters.visual.fmt_fraction_shade",
        "format_fraction_shade",
        {"interaction_mode": "set", "answer_collection": "fill_in_blank"},
    ),
    "fill_in_table": (
        "backend.app.practice_gen.formatters.visual.fmt_pattern_sequence",
        "format_pattern_sequence",
        {"interaction_mode": "set", "answer_collection": "fill_in_blank"},
    ),
    "number_bond": (
        "backend.app.practice_gen.formatters.visual.fmt_number_bond",
        "format_number_bond",
        {"interaction_mode": "read", "answer_collection": "fill_in_blank"},
    ),
    # ── Emoji Pictorial (pictorial model for addition/subtraction) ────────────
    "emoji_pictorial": (
        "backend.app.practice_gen.formatters.visual.fmt_emoji_pictorial",
        "format_emoji_pictorial",
        {"interaction_mode": "read", "answer_collection": "mcq"},
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# DNA INSTANCE ATTRIBUTE MAP
# Each DNA module exposes one DNA instance. This map lets us find it.
# ═══════════════════════════════════════════════════════════════════════════════

_DNA_INSTANCE_ATTR: Dict[str, str] = {
    "addition":           "ADDITION_DNA",
    "subtraction":        "SUBTRACTION_DNA",
    "multiplication":     "MULTIPLICATION_DNA",
    "division":           "DIVISION_DNA",
    "counting":           "COUNTING_DNA",
    "number_reading":     "NUMBER_READING_DNA",
    "ordinal_numbers":    "ORDINAL_NUMBERS_DNA",
    "place_value":        "PLACE_VALUE_DNA",
    "comparing_ordering": "COMPARING_ORDERING_DNA",
    "missing_number":     "MISSING_NUMBER_DNA",
    "patterns":           "PATTERNS_DNA",
    "fractions":          "FRACTIONS_DNA",
    "money_peso":         "MONEY_PESO_DNA",
    "rounding":           "ROUNDING_DNA",
    "order_of_operations":"ORDER_OF_OPERATIONS_DNA",
    "shapes_2d":          "SHAPES_2D_DNA",
    "length_measurement": "LENGTH_MEASUREMENT_DNA",
    "mass_capacity":      "MASS_CAPACITY_DNA",
    "time_reading":       "TIME_READING_DNA",
    "calendar":           "CALENDAR_DNA",
    "perimeter":          "PERIMETER_DNA",
    "area":               "AREA_DNA",
    "geometric_lines":    "GEOMETRIC_LINES_DNA",
    "symmetry_slides":    "SYMMETRY_SLIDES_DNA",
    "pictographs":        "PICTOGRAPHS_DNA",
    "bar_graphs":         "BAR_GRAPHS_DNA",
    "probability_language":"PROBABILITY_LANGUAGE_DNA",
}


def _get_dna_instance(dna_name: str):
    """Import the DNA module and return its DNA instance."""
    module = _import_dna_module(dna_name)
    attr = _DNA_INSTANCE_ATTR.get(dna_name)
    if attr and hasattr(module, attr):
        return getattr(module, attr)
    # Fallback: scan module for DNA instances
    from .dna.base import DNA
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, DNA):
            return obj
    raise ImportError(f"No DNA instance found in module for concept '{dna_name}'")


# ═══════════════════════════════════════════════════════════════════════════════
# ANSWER KEY FALLBACK MAP
# Many DNA generate_params functions return the answer under a key other than
# "result".  generate_context defaults blank_target to "result", so correct_answer
# may be None for these DNAs.  This map specifies which values key to try next.
# Priority: try each key in order, use the first non-None value found.
# ═══════════════════════════════════════════════════════════════════════════════

_ANSWER_KEY_FALLBACKS: Dict[str, List[str]] = {
    # result → answer fallback for most concepts
    "counting":           ["answer"],
    "area":               ["answer"],
    "bar_graphs":         ["answer"],
    "calendar":           ["answer"],
    "comparing_ordering": ["answer"],
    "geometric_lines":    ["answer"],
    "length_measurement": ["answer"],
    "mass_capacity":      ["answer"],
    "order_of_operations":["answer"],
    "ordinal_numbers":    ["answer", "word"],
    "patterns":           ["answer"],
    "perimeter":          ["answer"],
    "pictographs":        ["answer"],
    "probability_language":["answer"],
    "rounding":           ["answer"],
    "shapes_2d":          ["answer"],
    "symmetry_slides":    ["answer"],
    # money_peso uses "total"
    "money_peso":         ["answer", "total"],
    # missing_number uses "result" (already works) but also "answer" as backup
    "missing_number":     ["result", "answer"],
    # fractions: fraction_str is the canonical representation
    "fractions":          ["fraction_str", "numerator"],
    # number_reading: depends on direction; word_form is most common answer
    "number_reading":     ["word_form", "number"],
    # place_value: depends on task_type; value_at_position is most specific
    "place_value":        ["value_at_position", "digit_at_position"],
    # time_reading: time_str is the answer
    "time_reading":       ["time_str"],
}


def _fix_context_answer(ctx: QuestionContext) -> QuestionContext:
    """
    Patch ctx.correct_answer when it is None due to blank_target/key mismatch.

    Looks up _ANSWER_KEY_FALLBACKS for ctx.dna_concept and tries each fallback
    key in order. Mutates ctx in-place (dataclass fields are mutable).

    Also fixes question_text for concepts where _build_symbolic_question in
    base_generator.py uses generic 'a'/'b' keys that the DNA doesn't produce.

    Returns the (possibly patched) context.
    """
    if ctx.correct_answer is not None:
        # Still fix question_text if needed (even when answer is present)
        _fix_question_text(ctx)
        _fix_distractors(ctx)
        return ctx

    fallback_keys = _ANSWER_KEY_FALLBACKS.get(ctx.dna_concept, [])
    for key in fallback_keys:
        val = ctx.values.get(key)
        if val is not None:
            ctx.correct_answer = val
            ctx.blank_target = key
            # Also fix question_text_with_blank if it references the old blank
            if str(val) in ctx.question_text and "___" not in ctx.question_text:
                ctx.question_text_with_blank = ctx.question_text.replace(
                    str(val), "___", 1
                )
            break

    _fix_question_text(ctx)
    # Inject pre-built distractors from params if context has none
    _fix_distractors(ctx)
    return ctx


def _fix_distractors(ctx: QuestionContext) -> None:
    """
    Inject distractors from ctx.values["distractors"] when present.
    Some DNA modules (e.g. shapes_2d, probability_language, and custom operations)
    return a pre-built distractor list directly in their generate_params() output.

    Mutates ctx in-place.
    """
    built_in = ctx.values.get("distractors")
    if isinstance(built_in, list):
        correct = ctx.correct_answer
        ctx.distractors = [d for d in built_in if d != correct]
        return
    if ctx.distractors:
        return


def _fix_question_text(ctx: QuestionContext) -> None:
    """
    Fix question_text for DNAs where base_generator._build_symbolic_question
    uses 'a'/'b' fallback keys that don't exist in the DNA's values dict.

    Also uses embedded 'question' field from values when present (e.g. word problems),
    but ONLY if no spine was used (spine_id is None). When a spine is used, the
    spine-rendered question (which uses interest slots) takes priority.

    Mutates ctx.question_text and ctx.question_text_with_blank in-place.
    """
    v = ctx.values

    # First, check if DNA provided a custom 'question' field (e.g. word problems)
    # Only use this if NO spine was used — when a spine is used, it already
    # rendered the question with interest-themed slots (actor, objects, place)
    embedded = v.get("question")
    if embedded and v.get("context") == "word_problem" and ctx.spine_id is None:
        ctx.question_text = embedded
        answer = ctx.correct_answer
        if answer is not None and str(answer) in embedded and "___" not in embedded:
            ctx.question_text_with_blank = embedded.replace(str(answer), "___", 1)
        else:
            ctx.question_text_with_blank = embedded
        return

    # Only proceed with other fixes if question_text contains "None"
    concept = ctx.dna_concept
    if "None" not in ctx.question_text and concept not in ("number_reading", "counting"):
        # Still check for embedded question as fallback (only if no spine)
        if embedded and ctx.spine_id is None and (ctx.question_text.startswith("What is the answer?") or
                        ctx.question_text.startswith("Identify")):
            ctx.question_text = embedded
            ctx.question_text_with_blank = embedded
        return

    fixed: Optional[str] = None

    if concept == "counting":
        seq = v.get("sequence", [])
        skip = v.get("skip_by", "?")
        direction = v.get("direction", "forward")
        seq_str = ", ".join(str(x) for x in seq) + ", ___" if seq else "..."
        fixed = (
            f"What is the next number in this counting pattern? "
            f"{seq_str}  (counting {'forward' if direction == 'forward' else 'backward'} by {skip}s)"
        )

    elif concept == "number_reading":
        number = v.get("number", "?")
        task_type = v.get("task_type", "numeral_to_word")
        if task_type == "numeral_to_word":
            fixed = f"Write {number} in words."
        elif task_type == "numeral_to_expanded":
            fixed = f"Write {number} in expanded form."
        else:
            word = v.get("word_form", "?")
            fixed = f"What number is written as '{word}'?"

    elif concept == "place_value":
        number = v.get("number", "?")
        task = v.get("task_type", "identify_place")
        pos = v.get("target_digit_position", 0)
        digit = v.get("digit_at_position", "?")
        pos_names = {0: "ones", 1: "tens", 2: "hundreds", 3: "thousands"}
        pos_name = pos_names.get(pos, f"position {pos}")
        if task == "identify_place":
            fixed = f"What is the place value of the digit {digit} in {number}?"
        else:
            fixed = f"What digit is in the {pos_name} place of {number}?"

    elif concept == "time_reading":
        hour = v.get("hour", "?")
        minute = v.get("minute", 0)
        time_str = v.get("time_str", f"{hour}:{minute:02d}" if isinstance(minute, int) else "?:??")
        fixed = f"What time does the clock show? ({time_str})"

    elif concept == "fractions":
        numer = v.get("numerator", "?")
        denom = v.get("denominator", "?")
        fixed = f"What fraction does {numer} out of {denom} equal parts represent?"

    if fixed:
        ctx.question_text = fixed
        answer = ctx.correct_answer
        if answer is not None and str(answer) in fixed and "___" not in fixed:
            ctx.question_text_with_blank = fixed.replace(str(answer), "___", 1)
        else:
            ctx.question_text_with_blank = fixed

    # For DNAs that embed a 'question' key directly in generate_params output,
    # use it when question_text still has "None" or is a generic fallback.
    if "None" in ctx.question_text or ctx.question_text.startswith("Identify"):
        embedded = ctx.values.get("question")
        if embedded:
            ctx.question_text = embedded
            ctx.question_text_with_blank = embedded


def _weighted_choice(rng: random.Random, formatters: List[str]) -> str:
    """Pick a formatter from the list, weighted toward mcq and numeric_input."""
    weights = [_FORMATTER_WEIGHTS.get(f, _DEFAULT_WEIGHT) for f in formatters]
    total = sum(weights)
    r = rng.random() * total
    cumulative = 0.0
    for fmt, w in zip(formatters, weights):
        cumulative += w
        if r <= cumulative:
            return fmt
    return formatters[-1]


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def generate_problem(
    node_id: str,
    grade: int,
    seed: Optional[int] = None,
    difficulty_profile: Optional[Dict[str, Any]] = None,
    interest_theme: Optional[str] = None,
    formatter: Optional[str] = None,
    experience: str = "standard",
    experience_config: Optional[Dict] = None,
    allowed_formatters: Optional[List[str]] = None,
) -> FormattedProblem:
    """
    Generate a single FormattedProblem for the given node.

    Steps:
        1. Generate seed if not provided.
        2. Pick a DNA concept for the node.
        3. Generate a QuestionContext.
        4. Pick and apply a formatter.
        5. Apply the experience wrapper.

    Args:
        node_id: MATATAG node identifier, e.g. "mat_g1_na_q1_7".
        grade: Student grade (1–3).
        seed: Reproducibility seed. If None, a random seed is generated.
        difficulty_profile: Axis → level mapping, e.g. {"regrouping": "ones"}.
        interest_theme: Interest ID from interest_bank.json.
        formatter: Formatter name. If None, one is picked via weighted random.
        experience: Experience wrapper name ("standard", "mastery_drill",
            "hint_gated", "scaffolded").
        experience_config: Extra config passed to the experience wrapper.

    Returns:
        Fully populated FormattedProblem.

    Raises:
        ValueError: If node_id has no DNA mappings.
    """
    # 1. Seed
    if seed is None:
        seed = random.randint(10000, 99999)

    # 2. RNG
    rng = random.Random(seed)

    # 3. Pick DNA
    dna_names = get_node_dnas(node_id)
    if not dna_names:
        raise ValueError(f"No DNA mappings found for node_id '{node_id}'")

    dna_name = rng.choice(dna_names)
    dna = _get_dna_instance(dna_name)

    # 4. Generate context
    ctx = generate_context(dna, node_id, grade, seed, difficulty_profile, interest_theme)
    # Patch correct_answer when DNA answer key doesn't match default "result"
    ctx = _fix_context_answer(ctx)

    # 5. Pick formatter
    if formatter is None:
        available = get_formatters_for_dna(dna_name)
        if allowed_formatters:
            available = [fmt for fmt in available if fmt in allowed_formatters]
        if not available:
            available = ["mcq"]
        formatter = _weighted_choice(rng, available)

    # 6. Apply formatter
    problem = apply_formatter(ctx, formatter, rng)

    # 7. Apply experience
    return apply_experience(problem, experience, experience_config)


def apply_formatter(
    ctx: QuestionContext,
    formatter_name: str,
    rng: random.Random,
) -> FormattedProblem:
    """
    Route a QuestionContext to the correct formatter function.

    Args:
        ctx: Format-agnostic question context.
        formatter_name: Name from COMPATIBILITY table.
        rng: Seeded RNG (for reproducible shuffles inside formatters).

    Returns:
        FormattedProblem.

    Raises:
        ValueError: If the formatter_name is not in the routing table.
    """
    import importlib

    route = _FORMATTER_ROUTES.get(formatter_name)
    if route is None:
        # Unknown formatter — fall back to MCQ
        route = _FORMATTER_ROUTES["mcq"]

    module_path, func_name, extra_kwargs = route
    module = importlib.import_module(module_path)
    func = getattr(module, func_name)

    if extra_kwargs:
        return func(ctx, rng, **extra_kwargs)
    return func(ctx, rng)


def apply_experience(
    problem: FormattedProblem,
    experience: str,
    config: Optional[Dict],
) -> FormattedProblem:
    """
    Apply an experience wrapper to a FormattedProblem.

    Args:
        problem: Fully formatted problem.
        experience: Experience name: "standard", "mastery_drill",
            "hint_gated", "scaffolded".
        config: Experience-specific config dict (optional).

    Returns:
        Problem with experience fields set.
    """
    if experience == "standard":
        from .experiences.standard import wrap_standard
        return wrap_standard(problem)

    if experience == "mastery_drill":
        from .experiences.mastery_drill import wrap_mastery_drill
        state = config or {}
        return wrap_mastery_drill(problem, state)

    if experience == "hint_gated":
        from .experiences.hint_gated import wrap_hint_gated
        hints_revealed = (config or {}).get("hints_revealed", 0)
        return wrap_hint_gated(problem, hints_revealed=hints_revealed)

    if experience == "scaffolded":
        from .experiences.scaffolded import wrap_scaffolded
        step_index = (config or {}).get("step_index", 0)
        total_steps = (config or {}).get("total_steps", 1)
        return wrap_scaffolded(problem, step_index, total_steps)

    # Unknown experience — degrade to standard
    from .experiences.standard import wrap_standard
    return wrap_standard(problem)


def generate_batch(
    node_id: str,
    grade: int,
    count: int = 5,
    difficulty_profile: Optional[Dict[str, str]] = None,
    interest_theme: Optional[str] = None,
    experience: str = "standard",
) -> List[FormattedProblem]:
    """
    Generate a batch of varied problems for a node.

    Uses different seeds (base_seed + i) and avoids repeating the same
    formatter consecutively.

    Args:
        node_id: MATATAG node identifier.
        grade: Student grade (1–3).
        count: Number of problems to generate.
        difficulty_profile: Shared difficulty profile for the batch.
        interest_theme: Shared interest theme.
        experience: Experience wrapper for all problems.

    Returns:
        List of FormattedProblem instances.
    """
    base_seed = random.randint(10000, 99999)
    batch_rng = random.Random(base_seed)

    dna_names = get_node_dnas(node_id)
    if not dna_names:
        raise ValueError(f"No DNA mappings found for node_id '{node_id}'")

    # Collect all available formatters for this node
    available_formatters: List[str] = []
    seen: set = set()
    for dna_name in dna_names:
        for fmt in get_formatters_for_dna(dna_name):
            if fmt not in seen:
                seen.add(fmt)
                available_formatters.append(fmt)
    if not available_formatters:
        available_formatters = ["mcq"]

    problems: List[FormattedProblem] = []
    last_formatter: Optional[str] = None

    for i in range(count):
        seed = base_seed + i

        # Pick formatter avoiding consecutive repeats
        candidates = [f for f in available_formatters if f != last_formatter]
        if not candidates:
            candidates = available_formatters
        formatter = _weighted_choice(batch_rng, candidates)
        last_formatter = formatter

        problem = generate_problem(
            node_id=node_id,
            grade=grade,
            seed=seed,
            difficulty_profile=difficulty_profile,
            interest_theme=interest_theme,
            formatter=formatter,
            experience=experience,
        )
        problems.append(problem)

    return problems


def to_legacy_dict(problem: FormattedProblem) -> Dict[str, Any]:
    """
    Translate a FormattedProblem to the legacy skeleton dict format.

    This shim allows the existing API endpoints in main.py to consume
    the new pipeline without changing their response contract.
    """
    options_raw = problem.format_data.get("options", [])
    if not options_raw and problem.format_data.get("mcq_options"):
        options_raw = problem.format_data.get("mcq_options", [])

    # Legacy options format: {"A": value, "B": value, ...}
    if isinstance(options_raw, list):
        options = {o["key"]: o["value"] for o in options_raw if "key" in o}
    else:
        options = options_raw

    # Map question_mode based on visual type for proper grading in main.py
    question_mode = problem.interaction_mode or "mcq"
    if problem.visual_type == "PesoMoney":
        if problem.interaction_mode == "set":
            question_mode = "currency_picker"
        else:
            question_mode = "read"
    elif problem.visual_type == "ClockSet":
        if problem.interaction_mode == "set":
            question_mode = "clock_set"
        else:
            question_mode = "read"
    elif problem.visual_type == "BarChart":
        if problem.interaction_mode == "set":
            question_mode = "plotter_bar"
        else:
            question_mode = "read_bar"
    elif problem.visual_type == "NumberLine":
        if problem.interaction_mode == "set":
            question_mode = "number_line"
        else:
            question_mode = "read"
    elif problem.visual_type == "SortOrder":
        question_mode = "ordering"

    # Map correct_key for ELA/Fill-in-the-blank visual grading compatibility
    correct_key = problem.format_data.get("correct_key")
    if correct_key is None:
        mcq_opts = problem.format_data.get("mcq_options")
        if mcq_opts:
            for opt in mcq_opts:
                if opt.get("is_correct"):
                    correct_key = opt.get("key")
                    break
        if correct_key is None:
            if problem.answer_collection == "mcq":
                correct_key = "A"
            else:
                correct_key = str(problem.correct_answer)

    return {
        "skeleton_id": problem.problem_id,
        "problem_id": problem.problem_id,
        "node_id": problem.node_id,
        "question_text": problem.question_text,
        "stem": problem.question_text,
        "correct_answer": problem.correct_answer,
        "correct_key": correct_key,
        "options": options,
        "is_visual": problem.is_visual,
        "visual_type": problem.visual_type,
        "visual_params": problem.visual_params,
        "question_mode": question_mode,
        "grade": problem.grade,
        "seed": problem.seed,
        "difficulty_scalar": 0.5,
        "difficulty_dimensions": problem.difficulty_axes_served,
        "difficulty_axes_served": problem.difficulty_axes_served,
        "difficulty_profile": problem.difficulty_profile,
        "generator_type": "pipeline",
        "competency_text": problem.competency_text,
        "all_traps": {},
        "distractors": problem.distractors,
        "hints": problem.hints,
        "interaction_mode": problem.interaction_mode,
        "answer_collection": problem.answer_collection,
        "spine_id": problem.spine_id,
        "analytics": problem.analytics,
        # Pass-through new fields for consumers that know about them
        "format": problem.format,
        "format_data": problem.format_data,
        "experience": problem.experience,
        "interest_theme": problem.interest_theme,
    }
