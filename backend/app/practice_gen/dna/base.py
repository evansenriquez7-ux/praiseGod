"""
Practice Generation — DNA Base Definitions

All dataclasses, enums, and shared utilities for the DNA layer.

Sources:
  - DimensionSpec, log_interpolate, DIFFICULTY_LEVEL_MAP:
      refactored from difficulty_dimensions.py + matatag_dimensions.py
  - DNA, QuestionContext, ErrorPattern, Spine, VocabGated:
      new, per practice_gen_strategy.md architecture

DNA types:
  "formula"     — SymPy-computable answer. Standard type.
  "visual_read" — Answer from generated visual state. Correctness by construction.
  "static_bank" — Categorical answer. Hand-authored item pool.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# DIFFICULTY SCALE
# ═══════════════════════════════════════════════════════════════════════════════

DIFFICULTY_LEVEL_MAP: Dict[int, float] = {
    1: 0.2,   # Easy
    2: 0.5,   # Medium
    3: 0.8,   # Hard
    4: 1.1,   # Advanced — bridge zone (toward next competency)
}


def log_interpolate(min_val: float, max_val: float, t: float) -> float:
    """
    Logarithmic interpolation between min_val and max_val at position t.

    Produces slow growth at low t, accelerating toward max.
    Ideal for numeric ranges where early difficulties stay comfortable.

    Examples:
        log_interpolate(1, 1000, 0.0)  → 1
        log_interpolate(1, 1000, 0.5)  → ~31.6
        log_interpolate(1, 1000, 1.0)  → 1000
    """
    if min_val <= 0 or max_val <= 0:
        return min_val + t * (max_val - min_val)
    return min_val * math.pow(max_val / min_val, t)


def linear_interpolate(min_val: float, max_val: float, t: float) -> float:
    """Linear interpolation between min_val and max_val at position t."""
    return min_val + t * (max_val - min_val)


def interpolate(min_val: float, max_val: float, t: float, scale_type: str = "auto") -> float:
    """
    Interpolate between min_val and max_val using the given scale type.

    scale_type:
        "linear" — linear interpolation
        "log"    — logarithmic interpolation
        "auto"   — log if max/min >= 10 and both positive, else linear
    """
    if scale_type == "log":
        return log_interpolate(min_val, max_val, t)
    if scale_type == "auto":
        if min_val > 0 and max_val > 0 and max_val / min_val >= 10:
            return log_interpolate(min_val, max_val, t)
    return linear_interpolate(min_val, max_val, t)


# ═══════════════════════════════════════════════════════════════════════════════
# DIMENSION SPEC
# Refactored from difficulty_dimensions.py and matatag_dimensions.py.
# Single definition used by both formula and visual_read DNA types.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DimensionSpec:
    """
    Specification for a single difficulty dimension.

    Defines how a dimension scales from easy (0.0) to hard (1.0+).
    The bridge zone (> 1.0) allows a student near mastery to preview
    the next competency's difficulty range.
    """
    name: str
    value_type: str                     # "float" | "int" | "bool" | "choice"
    default_min: Any                    # Value at difficulty 0.0
    default_max: Any                    # Value at difficulty 1.0
    constraint_name: Optional[str]      # Key in extract_constraints() output that overrides default
    extrapolate: bool                   # Can exceed default_max in bridge zone?
    description: str
    scale_type: str = "auto"            # "linear" | "log" | "auto"
    choices: Optional[List] = None      # For value_type="choice" — ordered list easy→hard

    def value_at(self, t: float, override_min: Any = None, override_max: Any = None) -> Any:
        """
        Compute the dimension value at difficulty scalar t.

        If override_min/override_max are provided (from curriculum constraints),
        they replace default_min/default_max.
        """
        lo = override_min if override_min is not None else self.default_min
        hi = override_max if override_max is not None else self.default_max

        if not self.extrapolate:
            t = min(t, 1.0)

        if self.value_type == "choice" and self.choices:
            idx = interpolate(0, len(self.choices) - 1, t, self.scale_type)
            idx = max(0, min(len(self.choices) - 1, round(idx)))
            return self.choices[idx]

        raw = interpolate(float(lo), float(hi), t, self.scale_type)

        if self.value_type == "int":
            return max(int(lo), min(int(hi) if not self.extrapolate else int(raw * 2), round(raw)))
        if self.value_type == "bool":
            return raw >= 0.5
        return raw


# ═══════════════════════════════════════════════════════════════════════════════
# ERROR PATTERN
# Maps to a specific student misconception. Used as MCQ distractors.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ErrorPattern:
    """
    A pedagogically meaningful wrong answer.

    formula:          SymPy expression producing the distractor value.
                      Use the same parameter names as the DNA's answer_formula.
    required_concept: Concept that must be in node.cumulative_concepts for this
                      distractor to be offered. Prevents offering distractors that
                      presuppose knowledge the student hasn't received.
    label:            Short identifier for analytics (e.g. "off_by_one_high").
    description:      Human-readable explanation of the mistake.
    """
    formula: str
    required_concept: str
    label: str
    description: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# SPINE
# Narrative template for interest wrapping. DNA-agnostic.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Spine:
    """
    A reusable story template with named slots.

    Slots are filled from the student's interest theme in interest_bank.json.
    Eligibility is gated on two independent conditions:
      1. required_concepts ⊆ node.cumulative_concepts  (math gate)
      2. grade_band[0] <= student_grade <= grade_band[1]  (language gate)

    blank_target: which slot in the template holds the unknown value.
                  Must match a key in the QuestionContext.values dict.
    """
    id: str
    template: str
    required_concepts: Set[str]
    blank_target: str
    grade_band: Tuple[int, int]

    def is_eligible(self, cumulative_concepts: Set[str], grade: int) -> bool:
        return (
            self.required_concepts.issubset(cumulative_concepts)
            and self.grade_band[0] <= grade <= self.grade_band[1]
        )

    def render(self, slots: Dict[str, Any], values: Dict[str, Any]) -> str:
        """
        Fill template with interest slots and numeric values.
        
        Handles singular/plural automatically:
        - If {objects} is used after a number, it becomes singular when the number is 1
        - E.g., "1 basketballs" becomes "1 basketball"
        """
        ctx = {**slots, **values}
        result = self.template.format(**ctx)
        
        # Fix singular/plural for objects
        # Pattern: "1 <word>s" -> "1 <word>" (remove trailing 's' for quantity 1)
        import re
        
        def singularize(match):
            num = match.group(1)
            word = match.group(2)
            if num == "1" and word.endswith("s") and not word.endswith("ss"):
                # Handle specific irregulars found in interest bank
                irregulars = {
                    "loaves": "loaf",
                    "paintbrushes": "paintbrush",
                    "canvases": "canvas",
                    "matches": "match",
                    "boxes": "box"
                }
                if word in irregulars:
                    return f"1 {irregulars[word]}"
                # Handle es endings
                if word.endswith(("shes", "ches", "xes", "zes", "sses")):
                    return f"1 {word[:-2]}"
                # Handle ies endings
                if word.endswith("ies") and len(word) > 3 and word[-4] not in "aeiou":
                    return f"1 {word[:-3]}y"
                # Default: remove trailing 's'
                return f"1 {word[:-1]}"
            return match.group(0)
        
        # Match patterns like "1 basketballs", "1 apples", etc.
        result = re.sub(r'\b(1)\s+(\w+s)\b', singularize, result)
        
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# VOCAB GATED FRAGMENT
# A text fragment that is only inserted when required vocab is known.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class VocabGated:
    """
    A mathematical term fragment gated behind vocab knowledge.

    preferred:    Text used when requires_vocab is in node.cumulative_vocab.
    fallback:     Plain-language equivalent used before the term is introduced.

    Example:
        VocabGated(
            requires_vocab="sum",
            preferred="the sum is",
            fallback="the answer is",
        )
    """
    requires_vocab: str
    preferred: str
    fallback: str

    def resolve(self, cumulative_vocab: Set[str]) -> str:
        return self.preferred if self.requires_vocab in cumulative_vocab else self.fallback


# ═══════════════════════════════════════════════════════════════════════════════
# DNA
# Core specification of a mathematical concept.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DNA:
    """
    Specification of a mathematical concept for practice generation.

    dna_type:
        "formula"     — answer_formula is a SymPy expression.
        "visual_read" — answer is derived from visual_params; answer_formula is None.
        "static_bank" — problems are hand-authored; generation samples from item pool.

    param_bounds:
        Dict keyed by grade string ("g1", "g2", "g3") mapping parameter names
        to (min, max) tuples. Used by the rejection sampler.
        Example: {"g1": {"a": (1, 9), "b": (1, 9), "max_result": 20}}

    difficulty_axes:
        Dict mapping axis name → ordered list of levels, simplest first.
        Axes are DNA-specific and independent of each other.
        Example: {"regrouping": ["none", "ones", "tens", "double"]}

    compatible_formatters:
        List of formatter names this DNA can use.

    requires_context:
        True  → generator selects a story spine and fills interest slots.
        False → pure symbolic formulation ("What is 23 + 45?"). No spine.

    visual_home:
        The natural visual representation for this concept, if any.
        Must match a visual formatter name.
    """
    concept: str
    dna_type: str                                   # "formula" | "visual_read" | "static_bank"
    answer_formula: Optional[str]                   # SymPy expression; None for visual_read/static_bank
    param_bounds: Dict[str, Dict[str, Tuple]]       # {"g1": {"a": (1,9), ...}}
    error_patterns: List[ErrorPattern]
    compatible_formatters: List[str]
    requires_context: bool
    visual_home: Optional[str]
    difficulty_axes: Dict[str, List[str]]           # axis_name → [level0, level1, ...]

    # Derived at registration (populated by registry.py)
    node_ids: List[str] = field(default_factory=list)

    def param_bounds_for_grade(self, grade: int) -> Dict[str, Tuple]:
        """Return param_bounds for grade, falling back to nearest defined grade."""
        key = f"g{grade}"
        if key in self.param_bounds:
            return self.param_bounds[key]
        # Fall back to nearest lower grade
        for g in range(grade - 1, 0, -1):
            k = f"g{g}"
            if k in self.param_bounds:
                return self.param_bounds[k]
        # Fall back to highest defined grade
        return next(iter(self.param_bounds.values()))

    def axis_level_index(self, axis: str, level: str) -> int:
        """Return the index of a level within an axis (0 = easiest)."""
        levels = self.difficulty_axes.get(axis, [])
        return levels.index(level) if level in levels else 0

    def axis_scalar(self, axis: str, level: str) -> float:
        """Return a 0.0–1.0 scalar for a given axis level."""
        levels = self.difficulty_axes.get(axis, [])
        if not levels or len(levels) == 1:
            return 0.5
        idx = self.axis_level_index(axis, level)
        return idx / (len(levels) - 1)


# ═══════════════════════════════════════════════════════════════════════════════
# QUESTION CONTEXT
# Format-agnostic intermediate object produced by the Context Generator.
# Consumed by all formatters and experience wrappers.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class QuestionContext:
    """
    Format-agnostic intermediate produced by the context generator.

    Everything any formatter or experience wrapper might need is here.
    Formatters only consume — they never modify this object.
    """
    # ── Mathematical content ──────────────────────────────────────────────────
    values: Dict[str, Any]          # {"a": 5, "b": 3, "result": 8}
    correct_answer: Any             # 8
    distractors: List[Any]          # [7, 9, 2]  — from filtered error patterns
    answer_formula: Optional[str]   # "a + b"    — for SymPy validation record

    # ── Language content ──────────────────────────────────────────────────────
    question_text: str              # Full rendered question sentence
    question_text_with_blank: str   # Version with answer replaced by ___
    blank_target: str               # Which value is the blank ("result")
    hints: List[str]                # Step-by-step worked solution
    competency_text: str            # The learning competency from knowledge graph

    # ── Visual content (None if DNA has no visual_home) ───────────────────────
    visual_type: Optional[str]      # "NumberLine"
    visual_params: Optional[Dict]   # {"start": 0, "hop_from": 5, "hop_by": 3}

    # ── Metadata ──────────────────────────────────────────────────────────────
    node_id: str                    # MATATAG node: "mat_g1_na_q1_7"
    grade: int
    seed: int
    interest_theme: Optional[str]   # Which interest was applied
    spine_id: Optional[str]         # Which story spine was used

    # ── Difficulty ────────────────────────────────────────────────────────────
    difficulty_profile: Optional[Dict[str, str]]  # {"regrouping": "ones", ...}
    difficulty_axes_served: Dict[str, str]         # Actual axes produced (logged to student model)

    # ── DNA reference ─────────────────────────────────────────────────────────
    dna_concept: str                # "addition"
    dna_type: str                   # "formula" | "visual_read" | "static_bank"


# ═══════════════════════════════════════════════════════════════════════════════
# FORMATTED PROBLEM
# Final output of the pipeline. What the API and frontend consume.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class FormattedProblem:
    """
    Final output of the practice generation pipeline.

    Produced by a formatter operating on a QuestionContext,
    then optionally wrapped by an experience wrapper.
    """
    # ── Identity ──────────────────────────────────────────────────────────────
    problem_id: str                 # "{node_id}_{seed}"
    node_id: str
    competency_text: str
    grade: int
    seed: int

    # ── Content ───────────────────────────────────────────────────────────────
    question_text: str
    correct_answer: Any
    distractors: List[Any]
    hints: List[str]

    # ── Format ────────────────────────────────────────────────────────────────
    format: str                     # "mcq"|"cloze"|"numeric_input"|"ordering"|"true_false"|"error_detect"
    format_data: Dict[str, Any]     # Format-specific fields (e.g. shuffled options for MCQ)

    # ── Visual (None if textual) ──────────────────────────────────────────────
    is_visual: bool
    visual_type: Optional[str]
    visual_params: Optional[Dict]
    interaction_mode: Optional[str]     # "read" | "set"
    answer_collection: Optional[str]    # "mcq" | "fill_in_blank" | "drag" | "numeric_input"

    # ── Difficulty ────────────────────────────────────────────────────────────
    difficulty_profile: Dict[str, str]
    difficulty_axes_served: Dict[str, str]

    # ── Personalization ───────────────────────────────────────────────────────
    experience: str                 # "standard"|"hint_gated"|"mastery_drill"|"scaffolded"
    experience_config: Optional[Dict]
    interest_theme: Optional[str]
    spine_id: Optional[str]

    # ── Analytics capture ─────────────────────────────────────────────────────
    analytics: Dict[str, Any] = field(default_factory=lambda: {
        "time_to_answer_ms": None,
        "trap_triggered": None,
        "is_correct": None,
    })

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for API response."""
        import dataclasses
        return dataclasses.asdict(self)
