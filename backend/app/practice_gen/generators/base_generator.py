"""
Practice Generation — Context Generator
=========================================

The core generation function that transforms a DNA + node_id + seed
into a format-agnostic QuestionContext.

Responsibilities:
  1. Load knowledge_graph_g1_3.json at import time.
  2. Expose get_node() for callers that need raw node data.
  3. generate_context() — the main entry point.
  4. _import_dna_module() — dynamic import of DNA modules by concept name.
  5. _build_symbolic_question() — for non-context DNAs.
  6. _detect_axes_served() — back-infer difficulty axes from generated values.

Refactored from:
  - matatag_skeletons.py  (get_matatag_skeleton orchestration, lines 491–580)
  - curriculum_context.py (find_competency_in_curriculum, get_strand_progression)
  - constraint_extractor.py (extract_constraints)
"""

from __future__ import annotations

import importlib
import json
import math
import random
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..dna.base import DNA, QuestionContext, VocabGated
from ..registry import get_node_competency_bounds
from .interest import get_interest_slots, pick_interest
from .spines import select_spine


# ═══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE GRAPH — loaded once at import time
# ═══════════════════════════════════════════════════════════════════════════════

# generators/ → practice_gen/ → app/ → backend/ → ccmed/ (project root)
_KG_PATH: Path = (
    Path(__file__).parent.parent.parent.parent.parent
    / "data"
    / "knowledge_graph_g1_3.json"
)

_KG_NODES: Dict[str, Dict] = {}

try:
    with _KG_PATH.open(encoding="utf-8") as _f:
        _KG_NODES = json.load(_f).get("nodes", {})
except (FileNotFoundError, json.JSONDecodeError):
    # Graceful degradation: get_node() will return None for all queries.
    _KG_NODES = {}


# ═══════════════════════════════════════════════════════════════════════════════
# DNA MODULE IMPORT MAP
# Maps DNA concept name → dotted module path under practice_gen.dna
# ═══════════════════════════════════════════════════════════════════════════════

_DNA_MODULE_MAP: Dict[str, str] = {
    # Number & Algebra
    "addition":           "backend.app.practice_gen.dna.na.addition",
    "subtraction":        "backend.app.practice_gen.dna.na.subtraction",
    "multiplication":     "backend.app.practice_gen.dna.na.multiplication",
    "division":           "backend.app.practice_gen.dna.na.division",
    "counting":           "backend.app.practice_gen.dna.na.counting",
    "number_reading":     "backend.app.practice_gen.dna.na.number_reading",
    "ordinal_numbers":    "backend.app.practice_gen.dna.na.ordinal_numbers",
    "place_value":        "backend.app.practice_gen.dna.na.place_value",
    "comparing_ordering": "backend.app.practice_gen.dna.na.comparing_ordering",
    "missing_number":     "backend.app.practice_gen.dna.na.missing_number",
    "patterns":           "backend.app.practice_gen.dna.na.patterns",
    "fractions":          "backend.app.practice_gen.dna.na.fractions",
    "money_peso":         "backend.app.practice_gen.dna.na.money_peso",
    "rounding":           "backend.app.practice_gen.dna.na.rounding",
    "order_of_operations":"backend.app.practice_gen.dna.na.order_of_operations",
    # Measurement & Geometry
    "shapes_2d":          "backend.app.practice_gen.dna.mg.shapes_2d",
    "length_measurement": "backend.app.practice_gen.dna.mg.length_measurement",
    "mass_capacity":      "backend.app.practice_gen.dna.mg.mass_capacity",
    "time_reading":       "backend.app.practice_gen.dna.mg.time_reading",
    "calendar":           "backend.app.practice_gen.dna.mg.calendar",
    "perimeter":          "backend.app.practice_gen.dna.mg.perimeter",
    "area":               "backend.app.practice_gen.dna.mg.area",
    "geometric_lines":    "backend.app.practice_gen.dna.mg.geometric_lines",
    "symmetry_slides":    "backend.app.practice_gen.dna.mg.symmetry_slides",
    # Data & Probability
    "pictographs":        "backend.app.practice_gen.dna.dp.pictographs",
    "bar_graphs":         "backend.app.practice_gen.dna.dp.bar_graphs",
    "probability_language":"backend.app.practice_gen.dna.dp.probability_language",
}


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def get_node(node_id: str) -> Optional[Dict]:
    """
    Return the raw knowledge-graph node dict for node_id, or None.

    Args:
        node_id: MATATAG node identifier, e.g. "mat_g1_na_q1_7".

    Returns:
        Node dict from knowledge_graph_g1_3.json, or None if not found.
    """
    return _KG_NODES.get(node_id)


def generate_context(
    dna: DNA,
    node_id: str,
    grade: int,
    seed: int,
    difficulty_profile: Optional[Dict[str, Any]] = None,
    interest_theme: Optional[str] = None,
    is_lab: bool = False,
) -> QuestionContext:
    """
    Generate a format-agnostic QuestionContext from a DNA + node.

    Steps:
      a. Load node from knowledge graph (cumulative_vocab, cumulative_concepts).
      b. Construct a seeded RNG.
      c. Call the DNA-specific generate_params(grade, difficulty_profile, seed).
      d. Select a story spine when dna.requires_context is True.
      e. Resolve interest slots for the chosen theme.
      f. Build question_text and question_text_with_blank.
      g. Filter error_patterns to those whose required_concept is in
         cumulative_concepts.
      h. Compute distractors from filtered error patterns.
      i. Build hints via the DNA-specific generate_hints().
      j. Determine visual_type / visual_params when dna.dna_type == "visual_read".
      k. Detect which difficulty axes were actually served.
      l. Return a fully populated QuestionContext.

    Args:
        dna: DNA specification for the concept.
        node_id: MATATAG node identifier, e.g. "mat_g1_na_q1_7".
        grade: Student grade level (1–3 for G1–3 graph).
        seed: Integer seed for reproducibility.
        difficulty_profile: Optional axis → level mapping,
            e.g. {"regrouping": "ones", "structure": "result_unknown"}.
        interest_theme: Optional interest ID from interest_bank.json.
        is_lab: Whether this is called from the lab to bypass curriculum bounds.

    Returns:
        Fully populated QuestionContext.

    Raises:
        ValueError: If node_id is not found in the knowledge graph.
        RuntimeError: If the DNA module's generate_params raises after
            exhausting retry attempts.
    """
    # ── a. Load node ──────────────────────────────────────────────────────────
    node = _KG_NODES.get(node_id)
    if node is None:
        # Degrade gracefully with empty sets rather than raising, so the
        # pipeline can still produce a question for unknown/future nodes.
        cumulative_vocab: Set[str] = set()
        cumulative_concepts: Set[str] = set()
        competency_text: str = ""
    else:
        cumulative_vocab = set(node.get("cumulative_vocab", []))
        cumulative_concepts = set(node.get("cumulative_concepts", []))
        competency_text = node.get("competency", "")
    
    # Always include the current DNA concept in cumulative_concepts
    # This ensures error patterns for the current topic can generate distractors
    cumulative_concepts.add(dna.concept)

    # ── b. Seeded RNG ─────────────────────────────────────────────────────────
    rng = random.Random(seed)

    # ── c. Inject competency bounds into difficulty_profile ───────────────────
    bounds = get_node_competency_bounds(node_id, dna.concept)
    profile_to_use = dict(difficulty_profile) if difficulty_profile else {}
    if not is_lab:
        for dim, bound_val in bounds.items():
            if isinstance(bound_val, tuple) and len(bound_val) == 2:
                min_val, max_val = bound_val
                # Override profile with strict max bounds from curriculum
                if dim not in profile_to_use or profile_to_use[dim] == "continuous":
                    profile_to_use[dim] = max_val
                elif isinstance(profile_to_use[dim], (int, float)) and profile_to_use[dim] > max_val:
                    profile_to_use[dim] = max_val
            else:
                if dim not in profile_to_use:
                    profile_to_use[dim] = bound_val
    else:
        # For lab manual testing, do NOT cap/override with competency bounds!
        # But still fill in any omitted dimensions using their bounds/defaults.
        for dim, bound_val in bounds.items():
            if dim not in profile_to_use:
                if isinstance(bound_val, tuple) and len(bound_val) == 2:
                    profile_to_use[dim] = bound_val[1] # use max bounds
                else:
                    profile_to_use[dim] = bound_val

    # ── d. Generate params (DNA-specific) ────────────────────────────────────
    dna_module = _import_dna_module(dna.concept)
    values: Dict[str, Any] = dna_module.generate_params(
        grade, profile_to_use, seed
    )

    # ── d. Select spine ───────────────────────────────────────────────────────
    spine = None
    spine_id: Optional[str] = None
    if dna.requires_context:
        spine = select_spine(
            node_cumulative_concepts=cumulative_concepts,
            grade=grade,
            rng=rng,
            prior_concepts=cumulative_concepts,  # all known = prior for now
            # Keep the narrative's unknown aligned with the DNA's unknown; a
            # result-unknown spine cannot voice a change_unknown (unknown=b)
            # problem without leaking b into the stem.
            required_blank_target=values.get("blank_target"),
        )
        if spine is not None:
            spine_id = spine.id

    # ── e. Interest slots ─────────────────────────────────────────────────────
    resolved_theme = pick_interest(interest_theme, grade, rng)
    slots = get_interest_slots(resolved_theme, grade, rng)

    # ── f. Question text ──────────────────────────────────────────────────────
    if values.get("question") is not None:
        question_text = values["question"]
    elif spine is not None:
        try:
            question_text = spine.render(slots, values)
        except KeyError:
            # Template asked for a slot that values doesn't have — fall back.
            question_text = _build_symbolic_question(dna, values, cumulative_vocab)
    else:
        question_text = _build_symbolic_question(dna, values, cumulative_vocab)

    # question_text_with_blank: replace the blank_target value with "___"
    blank_target: str = values.get("blank_target", "result")
    blank_value = values.get(blank_target)
    if blank_value is not None and spine is not None and "___" not in question_text:
        # Replace the blank value only where it appears as a standalone
        # number — NOT as a substring inside a larger number. A naive
        # str.replace("0", …) turns "10" into "1___"; a digit-boundary
        # match ((?<!\d)…(?!\d), also guarding a trailing decimal) blanks
        # only the intended operand.
        import re as _re
        pattern = _re.compile(rf"(?<!\d){_re.escape(str(blank_value))}(?!\d)(?!\.\d)")
        question_text_with_blank, _n = pattern.subn("___", question_text, count=1)
        if _n == 0:
            # The blank value is not present as a standalone number (e.g. it
            # is inside a larger number or spelled as a word). Leave the stem
            # unblanked; the formatter's own no-blank guard decides whether
            # this context is usable. Never fall back to a substring replace,
            # which is what produced "1___" from "10".
            question_text_with_blank = question_text
    else:
        question_text_with_blank = question_text

    # ── g. Correct answer ─────────────────────────────────────────────────────
    correct_answer = values.get(blank_target)

    # ── h. Filter error patterns → distractors ────────────────────────────────
    filtered_patterns = [
        ep for ep in dna.error_patterns
        if ep.required_concept in cumulative_concepts
    ]
    distractors: List[Any] = [d for d in values.get("distractors", []) if d is not None]
    for ep in filtered_patterns:
        if ep.formula == "None":
            continue
        try:
            distractor = _eval_error_formula(ep.formula, values)
            if distractor is not None and distractor != correct_answer and distractor not in distractors:
                distractors.append(distractor)
        except Exception:
            continue

    # ── i. Hints ──────────────────────────────────────────────────────────────
    hints: List[str] = []
    if hasattr(dna_module, "generate_hints"):
        try:
            hints = dna_module.generate_hints(values, cumulative_vocab)
        except Exception:
            pass

    # ── j. Visual type / params ───────────────────────────────────────────────
    visual_type: Optional[str] = None
    visual_params: Optional[Dict] = None
    if dna.dna_type == "visual_read" and dna.visual_home:
        visual_type = dna.visual_home
        # Visual params are expected to be returned by generate_params for
        # visual_read DNAs.  Pull them out of values if present.
        visual_params = values.get("visual_params")

    # ── k. Axes served ────────────────────────────────────────────────────────
    difficulty_axes_served = _detect_axes_served(dna, values)

    # ── l. Build and return QuestionContext ───────────────────────────────────
    ctx = QuestionContext(
        values=values,
        correct_answer=correct_answer,
        distractors=distractors,
        answer_formula=dna.answer_formula,
        question_text=question_text,
        question_text_with_blank=question_text_with_blank,
        blank_target=blank_target,
        hints=hints,
        competency_text=competency_text,
        visual_type=visual_type,
        visual_params=visual_params,
        node_id=node_id,
        grade=grade,
        seed=seed,
        interest_theme=resolved_theme if resolved_theme != "neutral" else None,
        spine_id=spine_id,
        difficulty_profile=difficulty_profile,
        difficulty_axes_served=difficulty_axes_served,
        dna_concept=dna.concept,
        dna_type=dna.dna_type,
    )
    return ctx


# ═══════════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _import_dna_module(concept: str) -> Any:
    """
    Dynamically import the DNA module for a given concept name.

    Looks up the concept in _DNA_MODULE_MAP and imports the module.
    Raises ImportError if the concept is not in the map or the module
    cannot be imported.

    Args:
        concept: DNA concept name, e.g. "addition", "time_reading".

    Returns:
        The imported module object.

    Raises:
        ImportError: If concept is not mapped or the module is missing.
    """
    module_path = _DNA_MODULE_MAP.get(concept)
    if module_path is None:
        raise ImportError(
            f"No DNA module mapped for concept '{concept}'. "
            f"Known concepts: {sorted(_DNA_MODULE_MAP)}"
        )
    return importlib.import_module(module_path)


def _build_symbolic_question(
    dna: DNA,
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> str:
    """
    Build a plain symbolic question string for non-context DNAs.

    Uses VocabGated terms where available so the phrasing respects the
    student's current vocabulary.

    Args:
        dna: DNA specification.
        values: Generated parameter dict from generate_params.
        cumulative_vocab: Terms the student has been introduced to.

    Returns:
        A single question sentence string.

    Examples:
        addition   → "What is 23 + 45?"
        subtraction → "What is 67 − 34?"
        place_value → "What is the place value of the digit 4 in 342?"
        multiplication → "What is 6 × 7?"
        division   → "What is 42 ÷ 6?"
    """
    concept = dna.concept
    a = values.get("a", values.get("start"))
    b = values.get("b", values.get("skip_by"))
    blank = values.get("blank_target", "result")

    # ── Arithmetic operations ─────────────────────────────────────────────────
    if concept == "addition":
        strategy = values.get("strategy", "standard")
        prefix = "Solve using expanded form. " if strategy == "expanded_form" else ""
        
        if blank == "result":
            return f"{prefix}What is {a} + {b}?"
        elif blank == "b":
            result = values.get("result")
            return f"{prefix}{a} + ___ = {result}. What is the missing number?"
        else:
            result = values.get("result")
            return f"{prefix}___ + {b} = {result}. What is the missing number?"

    if concept == "subtraction":
        if blank == "result":
            return f"What is {a} − {b}?"
        elif blank == "b":
            result = values.get("result")
            return f"{a} − ___ = {result}. What is the missing number?"
        else:
            result = values.get("result")
            return f"___ − {b} = {result}. What is the missing number?"

    if concept == "multiplication":
        n = values.get("n", b)
        groups = values.get("groups", a)
        total = values.get("total", values.get("result"))
        if blank in ["total", "result"]:
            return f"What is {groups} × {n}?"
        elif blank in ["b", "n"]:
            return f"{groups} × ___ = {total}. What is the missing number?"
        else:
            return f"___ × {n} = {total}. What is the missing number?"

    if concept == "division":
        total = values.get("total", a)
        n = values.get("n", b)
        groups = values.get("groups", values.get("result"))
        if blank in ["result", "groups"]:
            return f"What is {total} ÷ {n}?"
        elif blank in ["b", "n"]:
            return f"{total} ÷ ___ = {groups}. What is the missing number?"
        else:
            return f"___ ÷ {n} = {groups}. What is the missing number?"

    # ── Place value ───────────────────────────────────────────────────────────
    if concept == "place_value":
        number = values.get("number", a)
        digit = values.get("digit", values.get("digit_at_position", b))
        pv_label = VocabGated("place value", "place value", "value").resolve(cumulative_vocab)
        return f"What is the {pv_label} of the digit {digit} in {number}?"

    # ── Counting / ordinal ────────────────────────────────────────────────────
    if concept == "counting":
        return f"What number comes after {a} when counting by {b}?"

    if concept == "ordinal_numbers":
        n = values.get("n", a)
        return f"What is the ordinal name for position {n}?"

    # ── Comparing / ordering ──────────────────────────────────────────────────
    if concept == "comparing_ordering":
        task_type = values.get("task_type", "compare_two")
        if task_type == "order_set":
            nums = values.get("numbers", [])
            nums_str = ", ".join(str(x) for x in nums)
            return f"Order these numbers from least to greatest: {nums_str}"
        elif task_type == "find_between":
            return f"What number is between {a} and {b}?"
        else:
            return f"Which is greater: {a} or {b}?"

    # ── Missing number ────────────────────────────────────────────────────────
    if concept == "missing_number":
        op_name = values.get("operation", "addition")
        op_symbol = {"addition": "+", "subtraction": "−",
                     "multiplication": "×", "division": "÷"}.get(op_name, "+")
        blank_pos = values.get("blank_position", "result")
        result = values.get("result", values.get("total"))
        if blank_pos == "start":
            return f"___ {op_symbol} {b} = {result}. What is the missing number?"
        elif blank_pos == "change":
            return f"{a} {op_symbol} ___ = {result}. What is the missing number?"
        else:
            return f"{a} {op_symbol} {b} = ___. What is the missing number?"

    # ── Patterns ─────────────────────────────────────────────────────────────
    if concept == "patterns":
        seq = values.get("sequence", [])
        seq_str = ", ".join(str(x) for x in seq) if seq else f"{a}, ..."
        return f"What is the next number in the pattern: {seq_str}?"

    if concept == "fractions":
        numer = values.get("numerator", a)
        denom = values.get("denominator", b)
        operation = values.get("operation")
        if operation in ("add_subtract", "add", "subtract"):
            a_num = values.get("a_num", numer)
            b_num = values.get("b_num", 0)
            a_den = values.get("a_den", denom)
            b_den = values.get("b_den", denom)
            op_sym = "+" if operation in ("add_subtract", "add") else "-"
            return f"What is \\(\\frac{{{a_num}}}{{{a_den}}} {op_sym} \\frac{{{b_num}}}{{{b_den}}}\\)?"
        return f"What fraction does \\(\\frac{{{numer}}}{{{denom}}}\\) equal parts represent?"

    # ── Money ────────────────────────────────────────────────────────────────
    if concept == "money_peso":
        operation = values.get("operation", "add_amounts")
        amounts = values.get("amounts")

        if operation == "find_change":
            paid = values.get("a")
            cost = values.get("b")
            if paid is not None and cost is not None:
                return f"You paid ₱{paid} for an item that costs ₱{cost}. How much change do you receive?"
            return "How much change do you receive?"

        if amounts:
            from collections import Counter
            counts = Counter(amounts)
            parts = []
            for denom in sorted(counts.keys(), reverse=True):
                count = counts[denom]
                is_bill = denom >= 20
                unit = "bill" if is_bill else "coin"
                if count > 1:
                    unit += "s"
                parts.append(f"{count} ₱{denom} {unit}")

            if len(parts) == 1:
                desc = parts[0]
            elif len(parts) == 2:
                desc = f"{parts[0]} and {parts[1]}"
            else:
                desc = ", ".join(parts[:-1]) + f", and {parts[-1]}"
            return f"What is the total value of {desc}?"
        else:
            total = values.get("total", values.get("result", a))
            return f"What is the total value of the money shown?"


    # ── Rounding ──────────────────────────────────────────────────────────────
    if concept == "rounding":
        number = values.get("number", a)
        precision = values.get("precision", 10)
        return f"Round {number} to the nearest {precision}."

    # ── Number reading ────────────────────────────────────────────────────────
    if concept == "number_reading":
        number = values.get("number", a)
        word_form = values.get("word_form")
        task_type = values.get("task_type", "numeral_to_word")
        if task_type == "word_to_numeral" and word_form:
            return f"Write the number: {word_form}."
        elif task_type == "numeral_to_expanded":
            return f"Write {number} in expanded form."
        else:
            return f"Write {number} in words."

    # ── Time reading ──────────────────────────────────────────────────────────
    if concept == "time_reading":
        hour = values.get("hour", a)
        minute = values.get("minute", 0)
        return f"What time does the clock show? ({hour}:{minute:02d})"

    # ── Calendar ──────────────────────────────────────────────────────────────
    if concept == "calendar":
        return "Use the calendar to answer the question."

    # ── Measurement ───────────────────────────────────────────────────────────
    if concept == "length_measurement":
        task_type = values.get("task_type")
        if task_type == "convert":
            val = values.get("value")
            from_u = values.get("from_unit")
            to_u = values.get("to_unit")
            return f"Convert {val} {from_u} to {to_u}."
        if task_type == "compare":
            val_a = values.get("value_a")
            val_b = values.get("value_b")
            u = values.get("unit")
            return f"Which is longer: {val_a} {u} or {val_b} {u}?"
        unit = values.get("unit", "cm")
        return f"Measure the object. Its length is ___ {unit}."

    if concept == "mass_capacity":
        task_type = values.get("task_type")
        mtype = values.get("measurement_type", "mass")
        if task_type == "convert":
            val = values.get("value")
            from_u = values.get("from_unit")
            to_u = values.get("to_unit")
            return f"Convert {val} {from_u} to {to_u}."
        if task_type == "compare":
            val_a = values.get("value_a")
            val_b = values.get("value_b")
            u = values.get("unit")
            return f"Which is {'heavier' if mtype == 'mass' else 'more'}: {val_a} {u} or {val_b} {u}?"
        unit = values.get("unit", "kg")
        return f"What is the mass/capacity of the object in {unit}?"

    if concept == "perimeter":
        shape = values.get("shape", "rectangle")
        return f"Find the perimeter of the {shape}."

    if concept == "area":
        shape = values.get("shape", "rectangle")
        return f"Find the area of the {shape}."

    # ── Geometry ──────────────────────────────────────────────────────────────
    if concept == "shapes_2d":
        return "Identify the shape shown."

    if concept == "geometric_lines":
        return "Identify the type of line shown."

    if concept == "symmetry_slides":
        return "Does this figure have a line of symmetry?"

    # ── Data / probability ────────────────────────────────────────────────────
    if concept == "pictographs":
        category = values.get("category", "item")
        count = values.get("count", a)
        return f"How many {category} does the pictograph show?"

    if concept == "bar_graphs":
        category = values.get("category", "item")
        return f"Read the bar graph. How many {category} are shown?"

    if concept == "probability_language":
        event = values.get("event", "this event")
        return f"How likely is {event} to happen?"

    if concept == "order_of_operations":
        expr = values.get("expression", f"{a} + {b}")
        return f"What is the value of {expr}?"

    # ── Generic fallback ──────────────────────────────────────────────────────
    result = values.get("result", values.get("total", "___"))
    return f"What is the answer? ({concept}: {a}, {b} → {result})"


def _detect_axes_served(dna: DNA, values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Back-infer which difficulty axis levels were actually produced.

    Checks the generated values against known axis semantics.  Only
    axes defined in dna.difficulty_axes are inspected.

    Args:
        dna: DNA specification.
        values: Generated parameter dict from generate_params.

    Returns:
        Dict of axis_name → detected_level string.
        Only axes that can be detected are included.

    Examples:
        If values has a=34, b=27, ones carry occurs → {"regrouping": "ones"}
        If values has a=20, b=30 → {"number_type": "round"}
    """
    axes = dna.difficulty_axes
    served: Dict[str, Any] = {}

    a = values.get("a", 0)
    b = values.get("b", 0)

    # ── regrouping axis ───────────────────────────────────────────────────────
    if "regrouping" in axes:
        ones_carry = (a % 10) + (b % 10) >= 10
        tens_carry = (a // 10 % 10) + (b // 10 % 10) >= 10
        if ones_carry and tens_carry:
            served["regrouping"] = "double"
        elif ones_carry:
            served["regrouping"] = "ones"
        elif tens_carry:
            served["regrouping"] = "tens"
        else:
            served["regrouping"] = "none"

    # ── number_type axis ──────────────────────────────────────────────────────
    if "number_type" in axes:
        levels = axes.get("number_type", [])
        if "single_digit" in levels or "multi_digit" in levels:
            if a >= 10:
                served["number_type"] = "multi_digit"
            else:
                served["number_type"] = "single_digit"
        else:
            if a % 10 == 0 and b % 10 == 0:
                served["number_type"] = "round"
            else:
                served["number_type"] = "non_round"

    # ── number_difficulty axis ────────────────────────────────────────────────
    if "number_difficulty" in axes:
        from backend.app.practice_gen.generators.number_difficulty import score_candidate
        def count_decimal_places(v: Any) -> int:
            if not isinstance(v, (int, float)):
                return 0
            if isinstance(v, int) or v.is_integer():
                return 0
            s = f"{v:.15f}".rstrip("0")
            if "." in s:
                return len(s.split(".")[1])
            return 0
        dec_places = max(count_decimal_places(a), count_decimal_places(b))
        max_val = max(a, b, 2)
        s_a = score_candidate(a, max_val, "whole", decimal_places=dec_places)
        s_b = score_candidate(b, max_val, "whole", decimal_places=dec_places)
        score = math.sqrt((s_a**2 + s_b**2) / 2.0)
        served["number_difficulty"] = str(round(score, 2))

    # ── structure axis ────────────────────────────────────────────────────────
    if "structure" in axes:
        blank_target = values.get("blank_target", "result")
        structure_map = {
            "result": "result_unknown",
            "b": "change_unknown",
            "a": "start_unknown",
            "n": "quotient_unknown",
            "groups": "divisor_unknown",
        }
        if blank_target in structure_map:
            served["structure"] = structure_map[blank_target]

    # ── table axis (multiplication / division) ────────────────────────────────
    if "table" in axes:
        n = values.get("n", values.get("b", 0))
        groups = values.get("groups", values.get("a", 0))
        factor = max(n, groups) if isinstance(n, int) and isinstance(groups, int) else 0
        levels = axes.get("table", [])
        if "6_7_8_9" in levels or "2_3_4_5_10" in levels:
            if factor in [6, 7, 8, 9]:
                served["table"] = "6_7_8_9"
            else:
                served["table"] = "2_3_4_5_10"
        elif factor <= 5 or factor == 10:
            served["table"] = "easy"
        else:
            served["table"] = "hard"

    # ── granularity axis (time_reading) ──────────────────────────────────────
    if "granularity" in axes:
        minute = values.get("minute", 0)
        if minute == 0:
            served["granularity"] = "hour"
        elif minute % 30 == 0:
            served["granularity"] = "half_hour"
        elif minute % 15 == 0:
            served["granularity"] = "quarter_hour"
        else:
            served["granularity"] = "minute"

    return served


def _eval_error_formula(formula: str, values: Dict[str, Any]) -> Any:
    """
    Evaluate a simple arithmetic formula string using values as variables.

    Only supports basic arithmetic operators and integer division.
    Uses a restricted eval to prevent arbitrary code execution.

    Args:
        formula: String like "a - b" or "(a % 10 + b % 10) + ...".
        values: Parameter dict providing variable bindings.

    Returns:
        Computed numeric value.

    Raises:
        Exception: If the formula cannot be evaluated.
    """
    # Restrict namespace to numeric values only.
    safe_ns = {k: v for k, v in values.items() if isinstance(v, (int, float))}
    # Re-map common aliases.
    if "total" in values and "total" not in safe_ns:
        safe_ns["total"] = values["total"]
    return eval(formula, {"__builtins__": {}}, safe_ns)  # noqa: S307
