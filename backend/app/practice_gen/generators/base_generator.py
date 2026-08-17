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
from ..registry import get_node_competency_bounds, get_node_dnas
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
    is_student_path: bool = False,
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

    not_yet_known: Set[str] = set(node.get("NOT_YET_KNOWN", [])) if node else set()
    
    # Always include the current DNA concept in cumulative_concepts
    # This ensures error patterns for the current topic can generate distractors
    cumulative_concepts.add(dna.concept)
    for vocab in cumulative_vocab:
        cumulative_concepts.add(vocab)

    # ── b. Seeded RNG ─────────────────────────────────────────────────────────
    rng = random.Random(seed)

    # ── c. Inject competency bounds into difficulty_profile ───────────────────
    bounds = get_node_competency_bounds(node_id, dna.concept)
    profile_to_use = dict(difficulty_profile) if difficulty_profile else {}
    if is_student_path:
        for dim, bound_val in bounds.items():
            if isinstance(bound_val, tuple) and len(bound_val) == 2:
                min_val, max_val = bound_val
                # Override profile with strict max bounds from curriculum
                if dim not in profile_to_use or profile_to_use[dim] == "continuous":
                    profile_to_use[dim] = max_val
                elif isinstance(profile_to_use[dim], (int, float)) and profile_to_use[dim] > max_val:
                    profile_to_use[dim] = max_val
            else:
                # Override profile with strict discrete bounds from curriculum
                profile_to_use[dim] = bound_val
    else:
        # For non-student paths (harness/Lab/audit): do NOT clamp/override, use profile as-is
        # but still fill in any omitted dimensions using their bounds/defaults.
        for dim, bound_val in bounds.items():
            if dim not in profile_to_use:
                if isinstance(bound_val, tuple) and len(bound_val) == 2:
                    profile_to_use[dim] = bound_val[1] # use max bounds
                else:
                    profile_to_use[dim] = bound_val

    # ── c1. Scalar-vs-magnitude guard for bounds that are not catalog axes ────
    # A registry tuple bound whose key is NOT a registered continuous axis is
    # never scalar-mapped by the orchestrator (that loop iterates the axes
    # catalog), but the injection above hands whatever the caller supplied
    # straight to the DNA as a raw ceiling. Two such keys exist today:
    # subtraction's `max_minuend` (11 nodes) and rounding's `max_value` (4).
    # So `difficulty_profile={"max_minuend": 1.0}` -- the 0-1 scalar every
    # registered axis uses -- silently became a ceiling of 1, and
    # mat_g3_na_q2_5 ("up to 4 digits") served "2 - 2 = 0" while reporting a
    # competency maximum of 9999. Fail loudly instead of generating content
    # against a ceiling the caller did not mean (AGENTS.md rule #3); an int is
    # still honoured as the genuine magnitude it is.
    from ..axes_catalog import get_axes_for_concept as _axes_for
    _registered_axes = {a["name"] for a in _axes_for(dna.concept)}
    for dim, bound_val in bounds.items():
        if not (isinstance(bound_val, tuple) and len(bound_val) == 2):
            continue
        if dim in _registered_axes:
            continue  # scalar-mapped upstream; already an absolute value here
        supplied = profile_to_use.get(dim)
        if isinstance(supplied, float) and bound_val[1] > 2 and supplied <= 1.0:
            raise ValueError(
                f"'{dim}'={supplied!r} looks like a 0-1 difficulty scalar, but '{dim}' is not a "
                f"registered continuous axis for DNA '{dna.concept}', so nothing maps it onto the "
                f"competency bound {bound_val} — the DNA would receive a ceiling of "
                f"{int(supplied)}. Pass an absolute magnitude, or register '{dim}' in "
                f"axes_catalog.CONCEPT_AXES_CATALOG so it is scalar-mapped. "
                f"Reproduce: node={node_id} dna={dna.concept} seed={seed}."
            )

    # ── c2. Curriculum-gate check (grade/quarter) ─────────────────────────────
    # Some variant values are curriculum-gated to a later grade/quarter than
    # their DNA is otherwise reachable at (e.g. multiplication number_type=
    # multi_digit is G3Q3+, fractions operation=add/subtract is G3Q4+). This
    # cannot be checked inside generate_params() — it only receives `grade`,
    # not quarter. Reject loudly here rather than let the DNA silently
    # generate content the node hasn't reached yet.
    quarter_match = re.search(r"mat_g\d+_[a-z]+_q(\d+)", node_id)
    quarter = int(quarter_match.group(1)) if quarter_match else 1
    if difficulty_profile:
        from ..compatibility import is_variant_available_at, get_variants_for_dna
        known_variants = get_variants_for_dna(dna.concept)
        for var_name, opt_val in difficulty_profile.items():
            # Only validate genuine, individually-selectable variant values
            # (VARIANTS_BY_DNA). difficulty_profile is also auto-filled from
            # competency-bounds ground truth, which can carry composite/scope
            # values (e.g. missing_number operation="addition_subtraction")
            # that were never meant to be checked as a single Lab-UI option.
            if str(opt_val) not in known_variants.get(var_name, []):
                continue
            if not is_variant_available_at(dna.concept, var_name, str(opt_val), grade, quarter):
                raise ValueError(
                    f"generate_context: variant {var_name}='{opt_val}' for DNA '{dna.concept}' "
                    f"is not available at node '{node_id}' (grade={grade}, quarter={quarter})."
                )

    # ── d. Generate params (DNA-specific) ────────────────────────────────────
    dna_module = _import_dna_module(dna.concept)
    values: Dict[str, Any] = dna_module.generate_params(
        grade, profile_to_use, seed
    )

    # Add the active operation concept to cumulative_concepts so matching story spines are eligible
    op = values.get("operation")
    if op:
        cumulative_concepts.add(op)

    # ── d. Select spine ───────────────────────────────────────────────────────
    spine = None
    spine_id: Optional[str] = None
    # money_peso's own amount count must NOT depend on context (a prior fix
    # removed a "cap to 2 for word_problem" override specifically because
    # varying draws by context desyncs the RNG stream -- pgen_contract.md's
    # variant-sensitivity rule), so add_amounts can legitimately produce
    # 2-5 amounts regardless of context. But every money_* spine template
    # (money_total, money_spending, money_change) narrates exactly 2
    # amounts (a, b) while blank_target="result"/"change" still reflects
    # the sum/difference of ALL of them -- with 3+ amounts, the story
    # silently omits one and the stated answer no longer matches what the
    # story describes (e.g. "has ₱5 in bills and ₱500 in coins, how much in
    # all?" -> 506, silently including a 3rd, unmentioned ₱1). Skip the
    # narrative spine entirely rather than narrate a mismatched subset; the
    # symbolic/pure fallback still shows the true full computation.
    money_peso_amounts = values.get("amounts") if dna.concept == "money_peso" else None
    money_peso_narratable = money_peso_amounts is None or len(money_peso_amounts) == 2
    # div_money_share (spines.py) narrates "has PN, shares equally among M
    # friends, how much does each get?" and answers with the floor
    # quotient -- correct only when the division is exact. When remainder
    # != 0 the true story is "each gets Q, with R left over", which this
    # spine's blank_target="total" (the bare quotient) cannot express;
    # rendering it anyway serves an answer that silently drops the
    # remainder as if the money split evenly (reproduced at
    # mat_g2_na_q3_9/mat_g3_na_q4_5 seed 603 via the variant-coverage
    # stratification seed range: "PHP10 among 4 friends" keyed to 2,
    # dropping the PHP2 left over). Skip narration for any division render
    # with a nonzero remainder; the symbolic "a / b = ?" fallback still
    # shows the true computation without implying an even split.
    division_narratable = dna.concept != "division" or values.get("remainder", 0) == 0
    if money_peso_narratable and division_narratable and dna.requires_context and values.get("context", "pure") == "word_problem":
        blank_pos = values.get("blank_position") or values.get("blank_target")
        # `values.get("operation")` is only ever populated by missing_number.py
        # -- the plain multiplication/division/addition/subtraction DNAs never
        # set an "operation" key, so this remap was silently dead code for
        # every one of them; dna.concept (the DNA's own name) is the reliable
        # signal. multiplication/division's blank_target naming ("result",
        # "start"/factor_unknown->"b") doesn't match their spines' blank_target
        # naming ("total"/"groups"/"n") without this remap, so no word-problem
        # spine could ever pass the required_blank_target filter for them.
        current_op = values.get("operation") or dna.concept
        if current_op in ("multiplication", "division"):
            blank_map = {"result": "total", "start": "groups", "change": "n"}
            blank_pos = blank_map.get(blank_pos, blank_pos)
        elif current_op in ("addition", "subtraction"):
            blank_map = {"start": "a", "change": "b", "result": "result"}
            blank_pos = blank_map.get(blank_pos, blank_pos)

        spine = select_spine(
            node_cumulative_concepts=cumulative_concepts,
            grade=grade,
            rng=rng,
            prior_concepts=cumulative_concepts,  # all known = prior for now
            cumulative_vocab=cumulative_vocab,
            # Keep the narrative's unknown aligned with the DNA's unknown; a
            # result-unknown spine cannot voice a change_unknown (unknown=b)
            # problem without leaking b into the stem.
            required_blank_target=blank_pos,
            # Ensure the narrated operation matches what's actually being
            # computed (e.g. a multiplication DNA must not get narrated
            # with a subtraction-comparison "how many more" spine just
            # because subtraction is also in this node's cumulative
            # concepts by this grade).
            # dna.concept alone is the reliable domain signal for most
            # DNAs, but money_peso can compute EITHER addition
            # ("add_amounts") or subtraction ("find_change") depending on
            # its own resolved operation, and its 4 spines split along
            # that same line (money_total requires "addition";
            # money_spending/money_change require "subtraction") -- using
            # "money_peso" alone would let a subtraction-narrated spine
            # (e.g. "had X, spent Y, how much left?") get selected for an
            # add_amounts-computed problem, presenting a sum as if it were
            # a difference. Map to the finer-grained operation when known.
            current_operation=(
                {"add_amounts": "addition", "find_change": "subtraction"}.get(
                    values.get("operation"), dna.concept
                )
                if dna.concept == "money_peso"
                else dna.concept
            ),
            node_own_concepts=set(get_node_dnas(node_id) or []),
        )
        if spine is not None:
            spine_id = spine.id

    # ── e. Interest slots ─────────────────────────────────────────────────────
    resolved_theme = pick_interest(interest_theme, grade, rng)
    slots = get_interest_slots(resolved_theme, grade, rng, not_yet_known=not_yet_known)

    # ── f. Question text ──────────────────────────────────────────────────────
    # Accept either key: every other DNA returns "question", but ordinal_numbers
    # returns "question_text". That mismatch silently discarded the DNA's own
    # rendered template and fell through to the generic stem below, which asks
    # "What is the ordinal name for position 6?" while the DNA had computed the
    # answer for "A runner finished in sixth place. What position number is
    # that?" — a stem asking for a word, answered with a number.
    if values.get("question") is not None or values.get("question_text") is not None:
        question_text = values.get("question") or values["question_text"]
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
    # A narrated stem states its operands and ASKS for the result in prose, so the
    # result usually does not appear in the text at all. When the result happens to
    # equal one of those stated operands, the value-match below found the operand
    # and blanked that instead -- turning a solvable item into an underdetermined
    # one. Blind review caught both shapes:
    #   a=4, b=0, result=4  -> "Yna has ___ sketchpads. A classmate has 0
    #                           sketchpads. How many more sketchpads does Yna have?"
    #                           keyed 4, with 3/5/6 fitting the text equally.
    #   a=98, b=49, result=49 -> "...collected 98 loaves of bread and another group
    #                           collected ___ loaves of bread." keyed 49, unreachable.
    # This is the mirror of the known blank_target/spine mismatch: there the blank
    # LEAKS the unknown, here it HIDES a required given. When the blank value
    # collides with a stated operand the match is ambiguous, so nothing is blanked
    # and the prose question carries the unknown, which is what it was written to do.
    _stated = [
        v for k, v in values.items()
        if k != blank_target and isinstance(v, int) and not isinstance(v, bool)
    ]
    if blank_value is not None and blank_value in _stated:
        blank_value = None
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
    # Grades 1-3 have not met numbers below zero, so a negative option is
    # unreadable rather than tempting. Several ErrorPatterns legitimately
    # evaluate negative (reversed operands, "b - a"), and blind reviewers found
    # -34, -14, -3 and -1 on offer across money, addition and multiplication
    # items. Filtering here rather than in each formatter covers all 17 of them
    # from one place; the formatters' own padding refills the slot in range.
    def _as_fraction(value: Any):
        """Parse 'a/b' (or a bare int) into a Fraction; None if not numeric."""
        from fractions import Fraction

        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return Fraction(value)
        if isinstance(value, str) and "/" in value:
            num, _, den = value.partition("/")
            try:
                return Fraction(int(num.strip()), int(den.strip()))
            except (ValueError, ZeroDivisionError):
                return None
        return None

    def _is_equivalent_to_answer(value: Any) -> bool:
        """
        True when a distractor is mathematically equal to the answer even though
        its string form differs — "2/4" offered against a keyed "1/2" gives the
        item two correct options, and the uniqueness check compares strings so it
        sails through. Found by blind review of mat_g1_na_q4_2 seed 42.
        """
        fv, fa = _as_fraction(value), _as_fraction(correct_answer)
        return fv is not None and fa is not None and fv == fa

    def _is_out_of_grade_negative(value: Any) -> bool:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if isinstance(correct_answer, (int, float)) and not isinstance(correct_answer, bool):
            return value < 0 <= correct_answer
        return value < 0

    distractors: List[Any] = [
        d for d in values.get("distractors", [])
        if d is not None
        and not _is_out_of_grade_negative(d)
        and not _is_equivalent_to_answer(d)
    ]
    distractors_provenance: Dict[Any, str] = {d: "base" for d in distractors}
    # _eval_error_formula evaluates a pure-arithmetic formula (e.g. "a - b")
    # against every *numeric* key in `values`, regardless of what the DNA's
    # own blank_target actually answers with. For a categorical/string
    # answer (e.g. place_value's "identify_place" answering a place name
    # like "tens"), `values` can still incidentally hold numeric fields the
    # formula happily evaluates (place_value.py's own "number"/
    # "digit_at_position"/"value_at_position") -- appending that numeric
    # result as a "distractor" alongside the real string ones let
    # fmt_true_false.py's fill_value draw a number ("The answer is 22")
    # for a question asking for a place name, a nonsensical statement
    # (blind review of mat_g1_na_q3_5 seed 50). A numeric distractor is
    # only ever meaningful when the real answer is itself numeric.
    correct_is_str = isinstance(correct_answer, str)
    # A comparison-symbol answer (">", "<", "=") has a fixed 3-value domain
    # unrelated to any DNA's arithmetic ErrorPattern formulas -- fractions.py's
    # patterns evaluate numerator/denominator into fraction-NOTATION strings
    # (e.g. "2/1"), which pass the bare str-vs-str type check above and were
    # offered as "which sign is correct?" options alongside the real signs
    # (blind review of mat_g1_na_q4_1). A distractor for a sign answer must
    # itself be one of the other two signs, never a formula result of a
    # completely different shape.
    correct_is_comparison_symbol = correct_answer in (">", "<", "=")
    if values.get("task_type") != "estimate":
        for ep in filtered_patterns:
            if ep.formula == "None":
                continue
            try:
                distractor = _eval_error_formula(ep.formula, values)
                if (
                    distractor is not None
                    and not (correct_is_str and not isinstance(distractor, str))
                    and not (correct_is_comparison_symbol and distractor not in (">", "<", "="))
                    and distractor != correct_answer
                    and distractor not in distractors
                    and not _is_out_of_grade_negative(distractor)
                    and not _is_equivalent_to_answer(distractor)
                ):
                    distractors.append(distractor)
                    distractors_provenance[distractor] = ep.label
            except Exception:
                continue

    # An ESTIMATION item needs options far enough apart that estimating tells them
    # apart; an option a few percent from the answer forces exact computation and
    # quietly turns "estimate the area" into "compute the area". The DNA supplies
    # well-separated distractors for these items, but the shared error patterns are
    # appended afterwards and can land arbitrarily close by coincidence -- for a
    # 3 x 7 tiling the perimeter 2*(3+7) = 20 sits 4.8% from the area 21. So for
    # this item type the same separation rule that governs the DNA's own options
    # governs the error-pattern ones too. This drops a distractor, never the
    # answer, and only where the competency's verb is "estimate".
    if values.get("task_type") == "illustrate_tiles" and isinstance(correct_answer, int):
        _MIN_GAP = 0.2
        keep = [
            d for d in distractors
            if not isinstance(d, int)
            or abs(d - correct_answer) >= _MIN_GAP * abs(correct_answer)
        ]
        for dropped in [d for d in distractors if d not in keep]:
            distractors_provenance.pop(dropped, None)
        distractors = keep

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
        distractors_provenance=distractors_provenance,
        answer_formula=dna.answer_formula,
        question_text=question_text,
        question_text_with_blank=question_text_with_blank,
        blank_target=blank_target,
        hints=hints,
        competency_text=competency_text,
        cumulative_vocab=sorted(cumulative_vocab),
        visual_type=visual_type,
        visual_params=visual_params,
        node_id=node_id,
        grade=grade,
        seed=seed,
        interest_theme=resolved_theme if resolved_theme != "neutral" else None,
        spine_id=spine_id,
        difficulty_profile=profile_to_use,
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

    missing_lbl = VocabGated("missing number", "missing number", "unknown number").resolve(cumulative_vocab)
    expanded_lbl = VocabGated("expanded form", "expanded form", "broken apart form").resolve(cumulative_vocab)

    # ── Arithmetic operations ─────────────────────────────────────────────────
    if concept == "addition":
        if values.get("task_type") == "estimate":
            real_a = values.get("real_a", a)
            real_b = values.get("real_b", b)
            return f"Estimate the sum: {real_a} + {real_b}"
        strategy = values.get("strategy", "standard")
        prefix = f"Solve using {expanded_lbl}. " if strategy == "expanded_form" else ""

        if blank == "result":
            return f"{prefix}What is {a} + {b}?"
        elif blank == "b":
            result = values.get("result")
            return f"{prefix}{a} + ___ = {result}. What is the {missing_lbl}?"
        else:
            result = values.get("result")
            return f"{prefix}___ + {b} = {result}. What is the {missing_lbl}?"

    if concept == "subtraction":
        if values.get("task_type") == "estimate":
            real_a = values.get("real_a", a)
            real_b = values.get("real_b", b)
            return f"Estimate the difference: {real_a} − {real_b}"
        if values.get("task_type") in ("expanded_form", "counting_back", "taking_away") and values.get("question"):
            return values["question"]
        if blank == "result":
            return f"What is {a} − {b}?"
        elif blank == "b":
            result = values.get("result")
            return f"{a} − ___ = {result}. What is the {missing_lbl}?"
        else:
            result = values.get("result")
            return f"___ − {b} = {result}. What is the {missing_lbl}?"

    if concept == "multiplication":
        n = values.get("n", b)
        groups = values.get("groups", a)
        total = values.get("total", values.get("result"))
        if values.get("task_type") == "estimate":
            real_a = values.get("real_a", a)
            real_b = values.get("real_b", b)
            return f"Estimate the product: {real_a} × {real_b}"
        if values.get("task_type") == "equal_groups" and blank in ["total", "result"]:
            group_form = values.get("group_form")
            plural_name = values.get("plural_name")
            if not plural_name:
                _plurals = {1: "ones", 2: "twos", 3: "threes", 4: "fours", 5: "fives", 6: "sixes", 7: "sevens", 8: "eights", 9: "nines", 10: "tens"}
                plural_name = _plurals.get(a, f"{a}s")
            terms = " + ".join([str(a)] * b) if b <= 5 else f"{a} added {b} times"
            if group_form == "plural_name":
                return f"Count {b} {plural_name} by repeated addition ({terms}): how many in all?"
            unit = "group" if b == 1 else "groups"
            return f"There are {b} {unit} of {a} ({terms}). How many in all?"
        if values.get("task_type") == "repeated_addition" and blank in ["total", "result"]:
            terms = " + ".join([str(a)] * b)
            return f"{terms} = ___. What is {a} × {b}?"
        if values.get("task_type") == "skip_counting" and blank in ["total", "result"]:
            seq = ", ".join(str(a * i) for i in range(1, b + 1))
            return f"Count by {a}s: {seq}. What is {a} × {b}?"
        if values.get("task_type") == "number_line_jumps" and blank in ["total", "result"]:
            return f"Starting at 0, take {b} equal jumps of {a} on the number line. What is {a} × {b}?"
        if blank in ["total", "result"]:
            return f"What is {groups} × {n}?"
        elif blank in ["b", "n"]:
            return f"{groups} × ___ = {total}. What is the {missing_lbl}?"
        else:
            return f"___ × {n} = {total}. What is the {missing_lbl}?"

    if concept == "division":
        total = values.get("total", a)
        n = values.get("n", b)
        groups = values.get("groups", values.get("result"))
        if values.get("task_type") == "estimate":
            real_a = values.get("real_a", a)
            real_b = values.get("real_b", b)
            return f"Estimate the quotient: {real_a} ÷ {real_b}"
        if blank in ["result", "groups"]:
            return f"What is {total} ÷ {n}?"
        elif blank in ["b", "n"]:
            return f"{total} ÷ ___ = {groups}. What is the {missing_lbl}?"
        else:
            return f"___ ÷ {n} = {groups}. What is the {missing_lbl}?"

    # ── Place value ───────────────────────────────────────────────────────────
    if concept == "place_value":
        number = values.get("number", a)
        task_type = values.get("task_type", "identify_place")
        if task_type == "decompose":
            # "e.g." avoided deliberately: the vocab-gating checker tokenizes
            # on non-alphanumeric characters, so "e.g." was being split into
            # standalone tokens "e" and "g" -- and bare "g" is reserved
            # NOT_YET_KNOWN vocabulary (the gram abbreviation, introduced
            # later in mass_capacity), so this collided every time despite
            # having nothing to do with grams.
            return f"Write {number} as tens and ones, for example 45 = 40 + 5."
        digit = values.get("digit", values.get("digit_at_position", b))
        pv_label = VocabGated("place value", "place value", "value").resolve(cumulative_vocab)
        if task_type == "identify_place":
            return f"What place is the digit {digit} in, in the number {number}?"
        if task_type == "identify_digit":
            place_name = values.get("place_name", "tens")
            return f"In {number}, what digit is in the {place_name} place?"
        return f"What is the {pv_label} of the digit {digit} in {number}?"

    # ── Counting / ordinal ────────────────────────────────────────────────────
    if concept == "counting":
        direction = values.get("direction", "forward")
        if direction == "backward":
            return f"What number comes before {a} when counting by {b}?"
        else:
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
            # compare_two's answer is a relation symbol (">", "<", "="), but this
            # stem used to ask "Which is greater: 18 or 30?" — a question whose
            # answer is a *number*. Three independent blind reviewers flagged it:
            # a pupil answering "30" is marked wrong, and a pupil reading the key
            # literally is taught that "<" means greater. Ask for what is
            # actually keyed.
            return f"Compare the numbers: {a} ___ {b}. Which sign is correct: >, <, or =?"

    # ── Missing number ────────────────────────────────────────────────────────
    if concept == "missing_number":
        op_name = values.get("operation", "addition")
        op_symbol = {"addition": "+", "subtraction": "−",
                     "multiplication": "×", "division": "÷"}.get(op_name, "+")
        blank_pos = values.get("blank_position", "result")
        result = values.get("result", values.get("total"))
        if blank_pos == "start":
            return f"___ {op_symbol} {b} = {result}. What is the {missing_lbl}?"
        elif blank_pos == "change":
            return f"{a} {op_symbol} ___ = {result}. What is the {missing_lbl}?"
        else:
            return f"{a} {op_symbol} {b} = ___. What is the {missing_lbl}?"

    # ── Patterns ─────────────────────────────────────────────────────────────
    if concept == "patterns":
        seq = values.get("sequence", [])
        missing_index = values.get("missing_index", -1)
        rule_desc = values.get("rule_description")
        if missing_index == -1 and rule_desc is not None and "common_difference" in values:
            # ask_type="state_rule" (bound for "Explain how to generate ..."
            # competencies): the answer is the numeric step/common
            # difference, not a sequence term -- this branch previously
            # fell through to the "next number" default unconditionally
            # (missing_index==-1 also happens to be this task_type's
            # sentinel), asking for "the next number" when the actual
            # expected answer is the rule's step size, which doesn't even
            # continue the visible sequence.
            seq_str = ", ".join(str(x) for x in seq) if seq else f"{a}, ..."
            # "combined" patterns (mat_g3_na_q3_6: "repeating and
            # increasing/decreasing components") answer with the BLOCK-
            # to-block step, not a per-term difference -- same root cause
            # and identical fix as fmt_pattern_sequence.py's own copy of
            # this branch (see that file's comment for the full
            # explanation). This is a SEPARATE fallback code path (used
            # when a generic mcq/cloze formatter renders patterns content
            # via ctx.question_text instead of fmt_pattern_sequence.py's
            # own dedicated state_rule branch), so the same fix has to be
            # applied here too -- confirmed by blind review still finding
            # the mismatched phrasing on 8 of 10 samples after the first
            # fix, all via mcq/cloze specifically.
            if values.get("pattern_kind") == "combined":
                return (
                    f"This pattern follows a rule: {seq_str}, ... Each group of numbers repeats, "
                    f"then the next group changes by the same amount. What number is added or "
                    f"subtracted from one group to the next?"
                )
            return (
                f"This pattern follows a rule: {seq_str}, ... "
                f"What number is added or subtracted each time to generate it?"
            )
        if missing_index is not None and 0 <= missing_index < len(seq):
            # ask_type="missing_middle": the answer (visible[missing_index])
            # is one of the ALREADY-SHOWN terms, not a continuation past the
            # end of the sequence -- rendering every value unmasked and
            # phrasing it as "next number" (the next_term-only phrasing this
            # branch used unconditionally) asked the student to name a value
            # they could already see in the prompt, under the wrong verb
            # ("next" implies continuing past the end). Blank the masked
            # position and phrase it as finding a missing term instead.
            display = [("___" if i == missing_index else str(x)) for i, x in enumerate(seq)]
            seq_str = ", ".join(display)
            # "number" was hardcoded regardless of sequence content --
            # patterns.py can now generate letter cycles too ("letters:
            # a, b, c, a, b, c...", mat_g1_na_q3_6's own worked example),
            # and "What number is missing" is simply wrong for those.
            # "term" is accurate for both and matches this DNA's own
            # VOCAB_TERM vocabulary.
            unit = "term" if any(isinstance(x, str) for x in seq) else "number"
            return f"What {unit} is missing in the pattern: {seq_str}?"
        seq_str = ", ".join(str(x) for x in seq) if seq else f"{a}, ..."
        unit = "term" if any(isinstance(x, str) for x in seq) else "number"
        return f"What is the next {unit} in the pattern: {seq_str}?"

    if concept == "fractions":
        numer = values.get("numerator", a)
        denom = values.get("denominator", b)
        operation = values.get("operation")
        if operation == "compare":
            # "compare" set values["result"] to a comparison symbol
            # (>, <, =) but no question-text branch ever asked a
            # comparison question -- every sample fell through to the
            # single-fraction "what fraction is shaded" phrasing below
            # regardless of operation, so a served "=" or "<" answer keyed
            # against a stem that never posed a comparison (blind review
            # of mat_g1_na_q4_1: "compare 1/2 to 1/4" competency never
            # once rendered as an actual comparison).
            a_num = values.get("a_num", numer)
            a_den = values.get("a_den", denom)
            b_num = values.get("b_num", numer)
            b_den = values.get("b_den", denom)
            return (
                f"Compare the fractions: \\(\\frac{{{a_num}}}{{{a_den}}}\\) ___ "
                f"\\(\\frac{{{b_num}}}{{{b_den}}}\\). Which sign is correct: >, <, or =?"
            )
        if operation in ("add_subtract", "add", "subtract"):
            a_num = values.get("a_num", numer)
            b_num = values.get("b_num", 0)
            a_den = values.get("a_den", denom)
            b_den = values.get("b_den", denom)
            a_part = "1 part is" if a_num == 1 else f"{a_num} parts are"
            if operation == "subtract":
                b_part = "1 shaded part is" if b_num == 1 else f"{b_num} shaded parts are"
                return (
                    f"A shape is divided into {a_den} equal parts. {a_part} shaded. "
                    f"If {b_part} taken away, what fraction of the shape remains shaded: "
                    f"\\(\\frac{{{a_num}}}{{{a_den}}} - \\frac{{{b_num}}}{{{b_den}}}\\)?"
                )
            b_part = "1 more part is" if b_num == 1 else f"{b_num} more parts are"
            return (
                f"A shape is divided into {a_den} equal parts. {a_part} shaded and {b_part} shaded. "
                f"What fraction of the shape is shaded in all: "
                f"\\(\\frac{{{a_num}}}{{{a_den}}} + \\frac{{{b_num}}}{{{b_den}}}\\)?"
            )
        # The previous phrasing — "What fraction does \(\frac{n}{d}\) equal parts
        # represent?" — was both ungrammatical and self-answering: it displayed
        # the very fraction it asked the student to name, so the item measured
        # nothing (validate_matrix §1F). Describe the partitioning in words and
        # let the student express it as a fraction, which is the actual skill.
        part_word = "part is" if numer == 1 else "parts are"
        if numer > denom:
            # An improper fraction (mat_g3_na_q4_6: "fractions... greater
            # than one") can't be shaded on a single shape -- you cannot
            # shade more parts than the shape has. The single-shape
            # phrasing silently asked students to "shade 4 parts" of a
            # shape "divided into 3 equal parts" with no second shape ever
            # mentioned, which isn't representable at all. The standard
            # model for a fraction greater than one is several identical
            # shapes, each divided the same way, with the total shaded
            # count spread across them.
            num_wholes = -(-numer // denom)  # ceiling division
            return (
                f"There are {num_wholes} identical shapes, each divided into {denom} equal parts. "
                f"{numer} {part_word} shaded in total. What fraction is shaded?"
            )
        return (
            f"A shape is divided into {denom} equal parts. {numer} {part_word} shaded. "
            f"What fraction of the shape is shaded?"
        )

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
            # A centavo pile is denominated in centavos throughout, so every
            # face is written "50¢" and never "₱50" -- and a centavo piece is
            # always a coin, so the ₱20 bill/coin threshold must not be applied
            # to it. money_peso.generate_params sets this key; anything without
            # it is a peso pile, which is every item that existed before centavo
            # piles were reachable.
            is_centavo = values.get("denomination_unit") == "centavo"
            counts = Counter(amounts)
            parts = []
            for denom in sorted(counts.keys(), reverse=True):
                count = counts[denom]
                if is_centavo:
                    unit = "coin"
                    face = f"{denom}¢"
                else:
                    unit = "bill" if denom >= 20 else "coin"
                    face = f"₱{denom}"
                if count > 1:
                    unit += "s"
                parts.append(f"{count} {face} {unit}")

            if len(parts) == 1:
                desc = parts[0]
            elif len(parts) == 2:
                desc = f"{parts[0]} and {parts[1]}"
            else:
                desc = ", ".join(parts[:-1]) + f", and {parts[-1]}"
            if is_centavo:
                # Name the unit the answer is in, so the total is unambiguous.
                return f"What is the total value of {desc}, in centavos?"
            return f"What is the total value of {desc}?"
        else:
            total = values.get("total", values.get("result", a))
            return f"What is the total value of the money shown?"


    # ── Rounding ──────────────────────────────────────────────────────────────
    if concept == "rounding":
        number = values.get("number", a)
        # rounding.py's generate_params returns the numeric ceiling under
        # the key "round_to" (10/100/1000), never "precision" -- this read
        # the wrong key and silently fell back to its own default (10)
        # every time, so "Round X to the nearest 10" rendered regardless
        # of the DNA's actual computed precision (blind review of
        # mat_g3_na_q1_4: scale_appropriateness FAIL, "nearest hundred"
        # and "nearest thousand" never once appear in the rendered text,
        # even on samples whose own values already reflect them).
        precision = values.get("round_to", 10)
        return f"Round {number} to the nearest {precision}."

    # ── Number reading ────────────────────────────────────────────────────────
    if concept == "number_reading":
        number = values.get("number", a)
        word_form = values.get("word_form")
        task_type = values.get("task_type", "numeral_to_word")
        if task_type in ("word_to_numeral", "identify_value", "number_line") and word_form:
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
            u = values.get("unit", "")
            # Non-standard units (paperclips, hands, steps, blocks, crayons)
            # are all regular "-s" plurals -- "1 paperclips" reads as a
            # grammar error a Grade 1 reader stumbles on (blind review of
            # mat_g1_mg_q2_1). cm/m have no plural form to strip.
            u_a = u[:-1] if val_a == 1 and u.endswith("s") and u not in ("cm", "m") else u
            u_b = u[:-1] if val_b == 1 and u.endswith("s") and u not in ("cm", "m") else u
            return f"Which is longer: {val_a} {u_a} or {val_b} {u_b}?"
        unit = values.get("unit", "cm")
        length = values.get("length")
        unit = unit[:-1] if length == 1 and unit.endswith("s") and unit not in ("cm", "m") else unit
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
        mtype = values.get("measurement_type", "mass")
        if mtype == "mass":
            mc_lbl = VocabGated("mass", "mass", "weight").resolve(cumulative_vocab)
        else:
            mc_lbl = VocabGated("capacity", "capacity", "amount of liquid").resolve(cumulative_vocab)
        if task_type == "estimate":
            # "estimate" and "read_measurement" previously rendered
            # byte-identical text ("What is the mass of the object in g?")
            # -- estimation is now framed as rounding a precise reading to
            # the nearest round_to unit, which needs different phrasing and
            # must show the reading being rounded (read_measurement's own
            # phrasing doesn't give the student anything to round).
            val = values.get("value", "?")
            round_to = values.get("round_to", 10)
            # "Estimate" avoided in the literal text: it's vocab-gated to
            # the specific node that introduces it, and the exhaustive
            # matrix check tests this task_type against every node this
            # DNA is mapped to, including ones earlier in the curriculum
            # that haven't introduced the word yet (an actual collision
            # hit for length_measurement's equivalent fix).
            return (
                f"An object's {mc_lbl} measures {val} {unit}. "
                f"About how many {unit} is that, rounded to the nearest {round_to}?"
            )
        return f"What is the {mc_lbl} of the object in {unit}?"

    if concept == "perimeter":
        # Same bug as area's prior fallback: never showed the dimensions
        # needed to compute the answer, silently unanswerable for every
        # textual formatter.
        shape = values.get("shape", "rectangle")
        sides = values.get("sides", {})
        task_type = values.get("task_type", "find_perimeter")
        if task_type == "find_missing_side":
            perimeter = values.get("perimeter", "?")
            if shape == "triangle":
                known = values.get("known_sides", {})
                known_str = " and ".join(f"{v} cm" for v in known.values())
                return f"A triangle has a perimeter of {perimeter} cm. Two of its sides are {known_str}. What is the length of the third side?"
            known_side = values.get("known_side", "l")
            known_value = values.get("known_value", "?")
            other = "width" if known_side == "l" else "length"
            return (
                f"A {shape} has a perimeter of {perimeter} cm and a "
                f"{'length' if known_side == 'l' else 'width'} of {known_value} cm. What is its {other}?"
            )
        if values.get("context") == "word_problem":
            # "Solve problems involving perimeter" (mat_g2_mg_q4_6).
            #
            # METRES, not centimetres. These templates hardcoded cm, so every
            # narrated figure came out at a physically absurd size: "A rectangular
            # garden is 5 cm long and 12 cm wide.", "A triangular flower bed has
            # sides 3 cm, 9 cm, and 11 cm.", and in one sample a garden 1 cm wide.
            # A blind reviewer flagged the whole corpus: "all 14 contexts (gardens,
            # flower beds) are modelled at centimetre scale ... Metres are the
            # plausible unit at every one of these values." The magnitudes were
            # always fine for a garden; only the unit was wrong. The bare-geometry
            # framings below stay in cm, where an abstract figure is what is meant.
            if shape == "square":
                return (
                    f"A square garden has a side of {sides.get('s', '?')} m. "
                    f"How much fencing is needed to go all the way around it?"
                )
            if shape == "triangle":
                return (
                    f"A triangular flower bed has sides {sides.get('a', '?')} m, "
                    f"{sides.get('b', '?')} m, and {sides.get('c', '?')} m. "
                    f"How much edging is needed to go all the way around it?"
                )
            # A garden narrower than it is long reads as an error to anyone
            # picturing it; blind review found "a garden whose width exceeds its
            # stated length" on three seeds. The two sides are the same pair either
            # way, so ordering them costs nothing and the perimeter is unchanged.
            l_val, w_val = sides.get("l", "?"), sides.get("w", "?")
            if isinstance(l_val, int) and isinstance(w_val, int) and w_val > l_val:
                l_val, w_val = w_val, l_val
            return (
                f"A rectangular garden is {l_val} m long and "
                f"{w_val} m wide. How much fencing is needed to go all the way around it?"
            )
        if shape == "square":
            return f"A square has a side of {sides.get('s', '?')} cm. What is its perimeter?"
        if shape == "triangle":
            return f"A triangle has sides {sides.get('a', '?')} cm, {sides.get('b', '?')} cm, and {sides.get('c', '?')} cm. What is its perimeter?"
        return f"A {shape} has sides {sides.get('l', '?')} cm and {sides.get('w', '?')} cm. What is its perimeter?"

    if concept == "area":
        # The prior version ("Find the area of {shape}.") never showed the
        # actual dimensions needed to compute the answer at all -- correct
        # only by coincidence for a visual formatter that renders the grid
        # separately (grid_area), but silently unanswerable for every
        # textual formatter (mcq/cloze/numeric_input) that renders this
        # fallback, and identical across all 4 area competencies regardless
        # of task_type.
        shape = values.get("shape", "rectangle")
        unit = values.get("unit", "sq cm")
        sides = values.get("sides", {})
        task_type = values.get("task_type", "find_area")
        if shape == "square":
            s = sides.get("s", "?")
            dims = f"a side of {s} {unit.replace('sq ', '')}"
            rows_cols = f"{s} rows and {s} columns"
        else:
            l, w = sides.get("l", "?"), sides.get("w", "?")
            dims = f"sides {l} {unit.replace('sq ', '')} and {w} {unit.replace('sq ', '')}"
            rows_cols = f"{l} rows and {w} columns"
        if task_type == "find_missing_dimension":
            # No "?" placeholders. These three fields are the whole content of the
            # item; defaulting them printed a well-formed sentence with a hole in
            # it ("a length of ? m") that read as a rendering quirk rather than the
            # missing-data bug it was. If this raises, the DNA branch that built
            # `values` failed to supply them.
            missing = [k for k in ("area", "known_dimension", "known_value")
                       if values.get(k) is None]
            if missing:
                raise ValueError(
                    f"area stem: find_missing_dimension is missing {missing} in the "
                    f"generated values (shape={shape!r}, unit={unit!r}, values={values!r}). "
                    f"The DNA branch that produced this must set area, known_dimension "
                    f"('l' or 'w') and known_value."
                )
            area = values["area"]
            known_dim = values["known_dimension"]
            known_val = values["known_value"]
            other = "width" if known_dim == "l" else "length"
            return (
                f"A {shape} has an area of {area} {unit} and a "
                f"{'length' if known_dim == 'l' else 'width'} of {known_val} "
                f"{unit.replace('sq ', '')}. What is its {other}?"
            )
        if task_type == "illustrate_tiles":
            # Two phrasings alternated by a value already fixed by the seed
            # (parity of the answer) so the choice is deterministic without
            # threading a new rng parameter through this shared builder --
            # blind review flagged that every sample reused one frozen
            # sentence with only the numbers changing.
            area_val = values.get("answer", 0)
            if isinstance(area_val, (int, float)) and int(area_val) % 2 == 0:
                return (
                    f"A {shape} is covered edge-to-edge with unit square tiles, "
                    f"arranged in {rows_cols}. Estimate how many unit tiles cover "
                    f"the {shape} in all."
                )
            return (
                f"You are laying unit square tiles over a {shape}, fitting "
                f"{rows_cols} exactly. About how many tiles in total will you use?"
            )
        if task_type == "derive_formula":
            # The cases are shown and the RULE is asked for. Printing the rule in
            # the stem, as this branch used to, turns a derivation into an
            # application -- the defect a blind reviewer scored FAIL.
            cases = values.get("cases")
            if not cases:
                raise ValueError(
                    f"area stem: derive_formula has no 'cases' in the generated "
                    f"values (shape={shape!r}, values={values!r}). An inductive "
                    f"item needs several tiled cases to generalise from; the DNA "
                    f"branch that produced this must supply them."
                )
            # "a 8 by 2 rectangle" -- article agreement follows the spoken form of
            # the leading number, and 8 is the only single digit that takes "an"
            # (11 and 18 do too, but no dimension here reaches them). Blind review
            # caught this in four stems.
            def _case(r, c, t):
                article = "an" if r == 8 else "a"
                return f"{article} {r} by {c} {shape} takes {t} tiles"

            shown = ", ".join(_case(*case) for case in cases[:-1])
            shown += f", and {_case(*cases[-1])}"
            # Two framings, alternated on a value the seed has already fixed (the
            # first case's total), so the choice is deterministic without threading
            # a new rng through this shared builder -- the same device the
            # illustrate_tiles branch above uses. Blind review found all 15 samples
            # running on one sentence frame.
            if int(cases[0][2]) % 2 == 0:
                return (
                    f"Cover each {shape} with unit square tiles and count them: "
                    f"{shown}. Which rule always gives the number of tiles?"
                )
            return (
                f"Three {shape}s are tiled with unit squares: {shown}. "
                f"Which rule works for every one of them?"
            )
        return f"A {shape} has {dims}. What is its area in {unit}?"

    # ── Geometry ──────────────────────────────────────────────────────────────
    if concept == "shapes_2d":
        return "Identify the shape shown."

    if concept == "geometric_lines":
        return "Identify the type of line shown."

    if concept == "symmetry_slides":
        sym_lbl = VocabGated("line of symmetry", "line of symmetry", "symmetry line").resolve(cumulative_vocab)
        return f"Does this figure have a {sym_lbl}?"

    # ── Data / probability ────────────────────────────────────────────────────
    if concept == "pictographs":
        category = values.get("category", "item")
        count = values.get("count", a)
        pg_lbl = VocabGated("pictograph", "pictograph", "picture graph").resolve(cumulative_vocab)
        return f"How many {category} does the {pg_lbl} show?"

    if concept == "bar_graphs":
        category = values.get("category", "item")
        bg_lbl = VocabGated("bar graph", "bar graph", "graph").resolve(cumulative_vocab)
        return f"Read the {bg_lbl}. How many {category} are shown?"

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
    if a is None:
        a = 0
    if b is None:
        b = 0

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
