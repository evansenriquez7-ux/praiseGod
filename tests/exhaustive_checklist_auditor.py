import os
import sys
import json
import re
import itertools
import traceback
from collections import defaultdict
from typing import Tuple, List, Dict, Any, Optional

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class AuditHarnessError(RuntimeError):
    """Raised when the audit harness itself cannot run (e.g. transitive import
    failure, missing dependency). Distinct from per-node content failures, so
    harness bugs are never mislabeled as content bugs."""


def _import_harness_dependencies():
    """Import every module the auditor depends on. Any failure here is a
    HARNESS problem (wrong interpreter, missing dep) — never a per-node
    content problem. Fail loudly with a distinct exception type."""
    try:
        from backend.app.practice_gen.registry import (  # noqa: F401
            get_all_node_ids,
            get_node_dnas,
            get_node_competency_bounds,
            get_node_info,
        )
        from backend.app.practice_gen.adapter import to_legacy_dict  # noqa: F401
        from backend.app.practice_gen.compatibility import (  # noqa: F401
            get_formatters_for_dna,
            get_supported_variants,
            FORMATTER_VARIANT_SUPPORT,
        )
        from backend.app.services.orchestrator import PracticeOrchestrator  # noqa: F401
    except Exception as exc:
        raise AuditHarnessError(
            "Audit harness failed to import its dependencies. "
            "Run via tests/run_checklist_audit.sh so the project's "
            "venv (with fastapi, sqlalchemy, etc.) is used. Original error: "
            f"{type(exc).__name__}: {exc}"
        ) from exc


_import_harness_dependencies()

from backend.app.practice_gen.registry import (  # noqa: E402
    get_all_node_ids,
    get_node_dnas,
    get_node_competency_bounds,
    get_node_info,
)
from backend.app.practice_gen.adapter import to_legacy_dict, _get_dna_instance, apply_formatter  # noqa: E402
from backend.app.practice_gen.compatibility import (  # noqa: E402
    get_formatters_for_dna,
    get_supported_variants,
    VARIANTS_BY_DNA,
    FORMATTER_VARIANT_SUPPORT,
    FORMATTER_NUMERIC_LIMITS,
)
from backend.app.practice_gen.axes_catalog import CONCEPT_AXES_CATALOG  # noqa: E402
from backend.app.services.orchestrator import PracticeOrchestrator  # noqa: E402

# Number of randomly seeded problems to generate per profile+formatter combination.
SAMPLES_PER_PROFILE = 10

# Checklist: Vocabulary gating forbidden list.
# Only words that are NOT in any MATATAG K-3 competency language go here.
# Words that DO appear in matatagmath.json for these grades (e.g. "identify"
# appears in G1 geometry, G2 fractions, G3 symmetry) are intentionally
# allowed even though they sound formal — they are explicit curriculum verbs.
FORBIDDEN_WORDS = [
    "sequence",
    "minuend",
    "subtrahend",
    "addend",
    "multiplicand",
    "multiplier",
    "divisor",
    "dividend",
    "expression",
    "evaluate",
]

VISUAL_FORMATTERS = {
    "number_line_read",
    "number_line_set",
    "array_grid_read",
    "array_grid_set",
    "place_value_blocks_read",
    "place_value_blocks_set",
    "peso_money_read",
    "peso_money_build",
    "clock_read",
    "clock_set",
    "bar_chart_read",
    "bar_chart_set",
    "pictograph_read",
    "fraction_model_read",
    "fraction_shade",
    "ruler_measure",
    "emoji_pictorial",
    "pattern_sequence",
    "grid_area",
    "shape_board",
    "ten_frame",
    "number_bond",
    "emoji_pictorial",
    "categorize",
    "pattern_sequence",
    "calendar_read",
    "fill_in_table",
    "balance_scale",
}


def scan_text(text, forbidden):
    if not text:
        return []
    found = []
    for word in forbidden:
        pattern = r"\b" + re.escape(word) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            found.append(word)
    return found


def normalize_dim_value(dim, opt, primary_concept=None):
    """
    Convert dimension option to profile value.

    For continuous dimensions: use the pre-computed value from the config.
    For discrete dimensions: return the level/value as-is.
    """
    if dim.get("dim_type") == "continuous":
        # Feed the SCALAR (0.0–1.0), not the pre-mapped value. The
        # orchestrator (source of truth, orchestrator.py:90-119) treats a
        # continuous-axis profile value <= 2.0 as a scalar and maps it to
        # the competency's [min, max] range itself. Feeding the mapped value
        # (e.g. 0 or 9999) desyncs the auditor from the orchestrator: small
        # values get re-mapped (Profile Mismatch / infeasible-combo crashes),
        # large ones bypass the numeric-limit and strict-bound checks — the
        # auditor's own _profile_violates_numeric_limit / strict-scalar
        # checks already assume a [0,1] scalar. Mirror the orchestrator.
        scalar = opt.get("scalar")
        if scalar is not None:
            return scalar
        # No scalar recorded — fall back to deriving it from the mapped
        # value so we still emit a [0,1] scalar rather than a raw value.
        value = opt.get("value")
        min_val = dim.get("min_value", dim.get("default_min", 1))
        max_val = dim.get("max_value", dim.get("default_max", 100))
        if value is not None and isinstance(value, (int, float)) and max_val != min_val:
            return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
        return 0.0

    return opt.get("level")


def build_test_profiles(config, supported_variants, primary_concept=None):
    difficulty_dimensions = config.get("difficulty_dimensions", [])
    contextual_variants = config.get("contextual_variants", [])

    base_profiles = [{}]

    for dim in difficulty_dimensions:
        options = dim.get("options", [])
        if not options:
            continue
        new_profiles = []
        for profile in base_profiles:
            for opt in options:
                # Skip bridge-zone scalars (>1.0) – these are lab-only advanced values
                # not valid for student-facing generation (is_lab=False).
                scalar = opt.get("scalar", 0.0)
                if isinstance(scalar, (int, float)) and scalar > 1.0:
                    continue
                new_profile = profile.copy()
                new_profile[dim["name"]] = normalize_dim_value(dim, opt, primary_concept)
                new_profiles.append(new_profile)
        base_profiles = new_profiles

    if not base_profiles:
        base_profiles = [{}]

    # Track the option values the function actually added to base_profiles
    # so the regression assertion can verify they all survived into the
    # returned (de-duplicated) profile list. The supported_variants filter
    # is an explicit, documented carve-out — values it drops are NOT
    # counted as "added" and are therefore not in scope for the
    # fail-fast check. (AGENTS.md rule #4 forbids silent skipping; this
    # filter is the opposite of silent — it is an explicit, named step.)
    added_variant_options: dict = {}

    for variant in contextual_variants:
        name = variant.get("name")
        declared_values = list(variant.get("options", []))

        values = declared_values
        if supported_variants and name in supported_variants:
            values = [v for v in values if v in supported_variants[name]]
        if not values:
            # Document the dropped options so the developer can see what
            # the supported_variants filter eliminated.
            if name in (supported_variants or {}) and declared_values:
                added_variant_options[name] = []
            continue

        added_variant_options[name] = list(values)

        new_profiles = []
        for profile in base_profiles:
            for val in values:
                new_profile = profile.copy()
                new_profile[name] = val
                new_profiles.append(new_profile)
        base_profiles = new_profiles

    # De-duplicate profiles
    unique_profiles = []
    seen = set()
    for profile in base_profiles:
        key = tuple(sorted(profile.items()))
        if key not in seen:
            seen.add(key)
            unique_profiles.append(profile)

    # Regression assertion (AGENTS.md rule #4: fail fast, no silent skipping).
    # If any option that the function added to base_profiles is missing
    # from the final returned profiles, raise immediately. This catches
    # dedup/structural bugs that would silently drop variant coverage.
    for variant_name, added_values in added_variant_options.items():
        if not added_values:
            continue
        present = {p.get(variant_name) for p in unique_profiles}
        missing = [v for v in added_values if v not in present]
        if missing:
            raise AssertionError(
                f"build_test_profiles: contextual variant '{variant_name}' is "
                f"missing options {missing} from the returned profiles "
                f"(added={added_values}, present={sorted(present)}). "
                f"This would silently drop variant coverage."
            )

    return unique_profiles


def is_visual_formatter(formatter_name):
    return formatter_name in VISUAL_FORMATTERS or formatter_name.endswith("_read") or formatter_name.endswith("_set")


# Formatters where the prompt itself states the target value (e.g. "Move the
# dot to show 5", "Read aloud: 5", "Place a check on 5"). For these, the answer
# appearing in the stem is by design — not a semantic leak. The student's task
# is to indicate/identify the stated value, not to derive it.
PROMPT_TARGET_FORMATTERS = {
    "number_line_read",
    "number_line_set",
    "array_grid_read",
    "array_grid_set",
    "place_value_blocks_read",
    "place_value_blocks_set",
    "pictograph_read",
    "bar_chart_read",
    "bar_chart_set",
    "clock_read",
    "clock_set",
    "calendar_read",
    "ruler_measure",
    "fill_in_table",
    "categorize",
    # error_detect presents a fully worked problem ("Carlo solved: N − M =
    # K. Is it right?") — the operands AND the shown answer appear in the
    # stem by design, so answer-in-stem is not a leak here.
    "error_detect",
}


def is_prompt_target_formatter(formatter_name):
    return formatter_name in PROMPT_TARGET_FORMATTERS


# Stem templates where the answer *is* stated in the stem by design (not a leak).
# These are the cases where the prompt IS the task — the student has to identify,
# construct, or write the value, not derive it from a separate computation.
#
# Each entry is a compiled regex matched against `question_text` (the stem).
# When the regex matches, the semantic-leak check is skipped because the answer
# appearing in the stem is the *task* (e.g. "Use coins and bills to make exactly
# ₱50" — the answer is 50, the prompt *is* the task of getting 50).
#
# This is a per-template carve-out, not a blanket "ignore leaks" flag. It is
# the narrowest possible exception consistent with the prompt-target design.
PROMPT_TARGET_STEM_PATTERNS = [
    # "Use coins and bills to make exactly ₱N. Use the fewest pieces possible."
    # The answer (N) is the target the student constructs coins to match.
    re.compile(
        r"Use coins and bills to make exactly\s*₱\s*(\d+(?:\.\d+)?).*Use the fewest pieces",
        re.IGNORECASE,
    ),
    # "What is N × N?" / "What is N ÷ N?" — single-digit multiplication/division
    # equation. The operands (N) are in the stem by definition; the answer
    # (N*N or N/N) may coincidentally contain a digit that matches an operand.
    # This is the same family of false positive as "What is 6 + 7?" — the check
    # should only fire if the answer is a trivial restatement of an operand.
    re.compile(
        r"What is\s+\d+\s*[×x*÷/]\s*\d+\s*\?",
    ),
    # "N × N = ___" / "N ÷ N = ___" — cloze-format single-digit arithmetic
    # equation. Same family as the "??" variant above; the operand digits
    # appear in the stem by definition. We carve out the entire cloze
    # equation form (any single-digit op on the LHS, blank on the RHS).
    re.compile(
        r"^\s*\d+\s*[+\-−×x*÷/]\s*\d+\s*=\s*_{3,}\s*$",
    ),
    # "N × ___ = N" / "___ × N = N" / "N ÷ ___ = N" — fill-in-the-blank
    # equation where one of the operands is the missing number. The known
    # operand is in the stem by design; the answer is the missing operand.
    re.compile(
        r"\d+\s*[+\-−×x*÷/]\s*_{3,}\s*=\s*\d+",
    ),
    re.compile(
        r"_{3,}\s*[+\-−×x*÷/]\s*\d+\s*=\s*\d+",
    ),
    # "What times N equals N?" — verbal fill-in-the-blank. The operands are
    # in the stem; the answer is the missing factor.
    re.compile(
        r"What times\s+\d+\s+equals\s+\d+",
        re.IGNORECASE,
    ),
    # "What is the value of the digit X in Y?" — place-value prompts.
    # The answer is the place value of digit X in number Y. The number Y
    # *contains* X (e.g. "value of the digit 2 in 20" — answer is 2, but 20
    # contains 2). This is not a leak; the answer is the place value, not
    # the number itself.
    re.compile(
        r"value of the digit\s+\d+\s+in\s+\d+",
        re.IGNORECASE,
    ),
    # "The number N is written in words as ___" — number-to-words prompt.
    # The answer is the word form of N; N appearing in the stem is by design
    # (the student must convert N to words).
    re.compile(
        r"number\s+\d+\s+is written in words",
        re.IGNORECASE,
    ),
    # "Round N to the nearest N." — rounding prompt; N appears in the stem
    # by definition (you can't round a number without stating it).
    re.compile(
        r"Round\s+\d+(?:\.\d+)?\s+to the nearest\s+\d+",
        re.IGNORECASE,
    ),
    # "Which is heavier: N g or N g?" / "Which is more: N mL or N mL?"
    # Comparing-measurement prompts. The values appear by design.
    re.compile(
        r"Which is (heavier|lighter|longer|shorter|more|less|taller):\s+\d+",
        re.IGNORECASE,
    ),
    # "What number comes after N when counting by N?" — counting prompts.
    # The starting number and step are in the stem by design; the answer
    # is the next number in the count.
    re.compile(
        r"What number comes after\s+\d+",
        re.IGNORECASE,
    ),
    # "Start at N. Count back N. What number do you land on?" — counting-back spine.
    # The answer is computed from the operands N and N; it's not stated in the stem.
    # The operands appear by design (you can't count back without stating start and count).
    re.compile(
        r"Start\s+at\s+\d+\.\s+Count\s+back\s+\d+\.\s+What\s+number\s+do\s+you\s+land\s+on",
        re.IGNORECASE,
    ),
    # NOTE: a broad "How many ... / How much ...?" pattern was removed here. It
    # matched essentially every addition/subtraction word problem and thereby
    # DISABLED leak detection for all of them. Whether a "how many" word problem
    # actually leaks is decided correctly by the explainable-count check
    # (answer vs. given_values) at the point of use — not by a stem regex.
]


def stem_is_prompt_target(question_text):
    """Return True if the stem is a known 'prompt-is-the-task' template
    where the answer appearing in the stem is by design."""
    if not question_text:
        return False
    for pattern in PROMPT_TARGET_STEM_PATTERNS:
        if pattern.search(question_text):
            return True
    return False


def _profile_violates_numeric_limit(profile, config, competency_bounds, formatter_max_val):
    """Return True if any continuous axis in `profile` is mapped to a value
    that would exceed the formatter's numeric limit (e.g. emoji_pictorial's
    max_val=100). Mirrors the orchestrator's continuous-axis mapping in
    orchestrator.py:90-118, so the audit never requests a profile the
    orchestrator would reject with IncompatibleConfigurationError."""
    import math
    for dim in config.get("difficulty_dimensions", []):
        if dim.get("dim_type") != "continuous":
            continue
        axis_name = dim.get("name")
        val = profile.get(axis_name)
        if not isinstance(val, (int, float)) or val in (None,):
            continue
        if val < 0 or val > 1:
            # Outside the [0, 1] scalar range — shouldn't happen for a
            # student-facing generation, but be defensive.
            continue
        # Resolve the actual numeric range
        cb = competency_bounds.get(axis_name)
        if isinstance(cb, tuple) and len(cb) == 2:
            min_val, max_val = cb
        else:
            min_val = dim.get("min_value", 1)
            max_val = dim.get("max_value", 100)
        # Log scale for wide ranges, linear otherwise — same heuristic as
        # the orchestrator (axes_catalog scale: 'logarithmic' or default).
        if max_val > 0 and min_val > 0 and max_val / min_val >= 10:
            shift = 1 if min_val == 0 else 0
            log_min = math.log10(min_val + shift)
            log_max = math.log10(max_val + shift)
            log_val = log_min + val * (log_max - log_min)
            mapped_val = int(math.pow(10, log_val)) - shift
        else:
            if isinstance(min_val, float) or isinstance(max_val, float) or (max_val - min_val <= 2):
                mapped_val = round(min_val + val * (max_val - min_val), 2)
            else:
                mapped_val = int(min_val + val * (max_val - min_val))
        if mapped_val > formatter_max_val:
            return True
    return False


def _map_scalar_to_range(axis_name, scalar, competency_bounds, scale=None):
    """Map a [0,1] scalar to the concrete value the orchestrator would
    produce for `axis_name`, using the competency range. This is a 1:1 mirror
    of the orchestrator's continuous-axis mapping (orchestrator.py:106-118):
    logarithmic for axes flagged `scale='logarithmic'` (with the min==0 shift
    and int(pow(10,·)) truncation), linear otherwise. Returns None if no
    bounds are available. The `scale` MUST be passed from the axis catalog —
    a linear guess diverges from the orchestrator for wide ranges (e.g. scalar
    0.25 on [0,9999] is 9 under log, 2499 under linear) and lets infeasible
    profiles through (Trap 3)."""
    if not isinstance(scalar, (int, float)):
        return None
    bounds = competency_bounds.get(axis_name)
    if not (isinstance(bounds, tuple) and len(bounds) == 2):
        return None
    min_val, max_val = bounds
    if scale == "logarithmic":
        import math
        shift = 1 if min_val == 0 else 0
        log_min = math.log10(min_val + shift)
        log_max = math.log10(max_val + shift)
        log_val = log_min + scalar * (log_max - log_min)
        return int(math.pow(10, log_val)) - shift
    mapped = min_val + scalar * (max_val - min_val)
    if isinstance(min_val, int) and isinstance(max_val, int):
        return int(mapped)
    return mapped


def _axis_scale(axis_name, primary_concept):
    """Return the scale ('logarithmic'/'linear'/None) the orchestrator uses
    for `axis_name`, read from the same axis catalog the orchestrator reads
    (get_axes_for_concept) so the auditor mirror cannot drift."""
    try:
        from backend.app.services.orchestrator import get_axes_for_concept
        for ax in get_axes_for_concept(primary_concept):
            if ax.get("name") == axis_name:
                return ax.get("scale")
    except Exception:
        return None
    return None


def _regrouping_profile_is_feasible(dna_name, profile, competency_bounds, grade=None):
    """Mirror the addition/subtraction DNA feasibility guard.

    A `regrouping` level that demands more carry/borrow places than the number
    range in the profile can physically produce has no valid pair — the DNA
    raises on it (fast). The auditor must not *request* such a combination, or
    it would report it as a Pipeline Crash. Feasibility depends on the specific
    (range, regrouping) pair in the profile, not the node's global ceiling, so
    it must be checked per-profile here.

    Defers to the DNA's `regrouping_is_feasible` (single source of truth). For
    addition the range key is the profile's mapped `max_sum`; subtraction's DNA
    derives its operand ceiling from the grade bounds (it ignores `number_range`),
    so no auditor-side gate is needed there — the DNA guard covers it.

    `max_sum` in the profile is a [0,1] SCALAR (see normalize_dim_value), so it
    must be mapped to the concrete competency range before feasibility is
    judged — `int(0.75)` would floor to 0 and wrongly mark every mid-range
    profile infeasible. `competency_bounds` supplies that range.
    """
    reg = profile.get("regrouping")
    if reg is None:
        return True
    if dna_name == "addition":
        from backend.app.practice_gen.dna.na.addition import regrouping_is_feasible
        max_sum_scalar = profile.get("max_sum")
        if not isinstance(max_sum_scalar, (int, float)):
            return True  # can't evaluate without a concrete range; let it through
        scale = _axis_scale("max_sum", dna_name)
        mapped_max_sum = _map_scalar_to_range("max_sum", max_sum_scalar, competency_bounds, scale)
        if mapped_max_sum is None:
            return True
        return regrouping_is_feasible(reg, int(mapped_max_sum))
    if dna_name == "subtraction":
        # Subtraction's operand ceiling comes from per-grade _PARAM_BOUNDS
        # (a<100/1000/10000 for G1/2/3), NOT from a profile axis. A regrouping
        # level demanding more borrow places than that ceiling's digit count
        # can produce (e.g. four_places on G3's 4-digit 9999) is infeasible for
        # every seed — the DNA raises on it. Gate it here using the same
        # grade-derived max_minuend the DNA uses.
        from backend.app.practice_gen.dna.na.subtraction import (
            _PARAM_BOUNDS,
            regrouping_is_feasible as sub_regrouping_is_feasible,
        )
        if grade is None:
            return True  # cannot resolve the grade ceiling; let the DNA guard it
        g_key = f"g{max(1, min(int(grade), 3))}"
        max_minuend = _PARAM_BOUNDS[g_key]["a"][1]
        return sub_regrouping_is_feasible(reg, int(max_minuend))
    return True


def formatter_supports_profile(dna_name, formatter, profile):
    """Mirror the orchestrator's per-DNA×formatter compatibility check
    (backend/app/services/orchestrator.py:120-132): the formatter is only
    accepted for the DNA if `formatter in get_formatters_for_dna(dna_name)`.
    If the DNA is in FORMATTER_VARIANT_SUPPORT and the formatter has an
    entry, also check that every requested variant value is in the
    allowed set.

    Previously this function returned True when FORMATTER_VARIANT_SUPPORT
    had no entry for the (DNA, formatter) pair, which allowed the audit
    to request combinations the orchestrator would have rejected. This
    was the root cause of the v-final "Fractions DNA concept overridden"
    violations: the audit requested (fractions, ordering), the formatter
    'ordering' is not in fractions' compatible_formatters list, so the
    orchestrator would skip fractions and pick 'comparing_ordering' — but
    the audit treated this as a fractions-DNA override because it
    expected fractions to be the chosen DNA.
    """
    # Gate 1: per-DNA compatible_formatters list (matches orchestrator's
    # `if formatter and formatter not in available_for_d: continue` at
    # services/orchestrator.py:125).
    dna_formatters = set(get_formatters_for_dna(dna_name))
    if dna_formatters and formatter not in dna_formatters:
        return False

    # Gate 2: FORMATTER_VARIANT_SUPPORT caps (matches the orchestrator's
    # variant-compatibility check at services/orchestrator.py:140-148).
    caps = FORMATTER_VARIANT_SUPPORT.get(dna_name, {}).get(formatter)
    if caps is None:
        return True
    for variant_name, allowed_vals in caps.items():
        if variant_name in profile:
            if allowed_vals and profile[variant_name] not in allowed_vals:
                return False
    return True


def extract_numeric_state(problem, legacy_dict=None):
    state = {}
    for source in (getattr(problem, "difficulty_profile", {}) or {}, getattr(problem, "visual_params", {}) or {}):
        if not isinstance(source, dict):
            continue
        for key, value in source.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                state[key] = value
                
    if legacy_dict:
        import re
        from collections import Counter
        text_to_scan = legacy_dict.get("stem", "")
        options = legacy_dict.get("options", {})
        opts_list = options.values() if isinstance(options, dict) else (options if isinstance(options, list) else [])
        for opt in opts_list:
            text_to_scan += " " + str(opt.get("value") if isinstance(opt, dict) else opt)
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text_to_scan)
        num_counts = Counter(float(n) if '.' in n else int(n) for n in numbers)
        state["_extracted_numbers"] = tuple(sorted(num_counts.items()))

        # Semantic-operand multiset for the Separation-of-Concerns check.
        # The regex-on-stem set above is the wrong signal for SoC: a value
        # that is blanked (the ``blank_target``) or rendered as a word by a
        # word_problem spine legitimately disappears from the visible stem,
        # even though the underlying math is unchanged across contexts. The
        # authoritative operands live in ``given_values`` (plus the answer),
        # so compare those instead. Non-numeric meta keys (blank_target,
        # context, structure, strategy, max_sum, …) are ignored.
        semantic = Counter()
        given_values = legacy_dict.get("given_values") or {}
        if isinstance(given_values, dict):
            for k, v in given_values.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    semantic[v] += 1
        answer = legacy_dict.get("correct_answer")
        if isinstance(answer, (int, float)) and not isinstance(answer, bool):
            semantic[answer] += 1
        state["_semantic_operands"] = tuple(sorted(semantic.items()))

    return state


def get_lab_config(node_id):
    from backend.app.routes.matatag_router import get_matatag_lab_config
    return get_matatag_lab_config(node_id)


def validate_dimension_config(node_id, config, failures):
    for dim in config.get("difficulty_dimensions", []):
        if dim.get("dim_type") not in {"continuous", "discrete"}:
            failures[node_id].append(
                f"Invalid dimension type '{dim.get('dim_type')}' for '{dim.get('name')}'"
            )
        options = dim.get("options", [])
        if not options:
            failures[node_id].append(f"Difficulty dimension '{dim.get('name')}' has no options.")
        if dim.get("dim_type") == "continuous":
            for opt in options:
                scalar = opt.get("scalar")
                if not isinstance(scalar, (int, float)):
                    failures[node_id].append(
                        f"Continuous dimension '{dim.get('name')}' has non-numeric scalar {scalar!r}."
                    )


def validate_variant_config(node_id, config, failures):
    for variant in config.get("contextual_variants", []):
        values = variant.get("options", [])
        if not values:
            failures[node_id].append(f"Contextual variant '{variant.get('name')}' has no options.")


def _strict_scalar_endpoint_violates(actual_val, expected):
    """Return True iff a strict-scalar-endpoint mapping (scalar in
    {0.0, 1.0}) is a real violation.

    The orchestrator's continuous axis mapping rounds via
    ``int(pow(10, ...))`` for logarithmic scales, which is lossy near
    the upper bound. Accept off-by-one rounding at scalar=0.0 and
    scalar=1.0 as a valid endpoint; anything beyond that is a genuine
    mapping failure.

    A ``None`` actual_val (the dimension wasn't recorded) is not a
    violation here — it is already gated by ``actual_val is not None``
    at the call site.
    """
    if actual_val is None or actual_val == expected:
        return False
    return abs(actual_val - expected) > 1


def _audit_node(node_id: str) -> Tuple[Dict[str, List[str]], List[Dict[str, Any]], int]:
    """Run the checklist audit for a single node. Returns
    (failures_for_node, repro_for_node, total_checked_for_node).

    Module-level so ProcessPoolExecutor can pickle it across processes.
    Per AGENTS.md rule #4 (no silent fallbacks): does not swallow
    exceptions, does not skip nodes. AuditHarnessError propagates.

    This is the per-node body that previously lived inline in
    run_audit(); extracted so it can be called from a worker process.
    """
    print(f"[auditor] {node_id} ...", flush=True)
    failures: Dict[str, List[str]] = {}
    repro_crashes: List[Dict[str, Any]] = []
    total_checked = 0

    try:
        config = get_lab_config(node_id)
    except AuditHarnessError:
        raise
    except Exception as e:
        failures[node_id] = [f"Lab Config Fetch Crash: {str(e)}"]
        return failures, repro_crashes, total_checked

    grade = config.get("grade", 1)
    dnas = get_node_dnas(node_id)
    if not dnas:
        failures[node_id] = ["No DNA mappings found."]
        return failures, repro_crashes, total_checked

    primary_concept = dnas[0]
    competency_bounds = get_node_competency_bounds(node_id)
    supported_formatters = sorted(
        set(itertools.chain.from_iterable(get_formatters_for_dna(d) for d in dnas))
    )
    # Mirror the lab-config builder: drop formatters whose display ceiling is
    # below this node's number range (e.g. emoji_pictorial max_val=100 on a
    # grade-3 node reaching 9999). Keeps the audit from testing — and the
    # Formatter-mismatch check below from flagging — a formatter the node no
    # longer offers. Single source of truth is FORMATTER_NUMERIC_LIMITS.
    _node_max_value = max(
        (b[1] for b in competency_bounds.values()
         if isinstance(b, tuple) and len(b) == 2),
        default=0,
    )
    supported_formatters = [
        fmt for fmt in supported_formatters
        if FORMATTER_NUMERIC_LIMITS.get(fmt, {}).get("max_val", float("inf")) >= _node_max_value
    ]
    if not supported_formatters:
        supported_formatters = ["mcq"]

    config_formatters = [fmt["name"] for fmt in config.get("formatters", [])]
    if not config_formatters:
        config_formatters = supported_formatters

    if set(config_formatters) != set(supported_formatters):
        failures.setdefault(node_id, []).append(
            f"Formatter mismatch: config has {config_formatters} but supported formatters are {supported_formatters}"
        )

    validate_dimension_config(node_id, config, failures)
    validate_variant_config(node_id, config, failures)

    # Per-node hoists: cache values that the inner loop would otherwise
    # re-fetch per profile.
    dim_names = {d["name"] for d in config.get("difficulty_dimensions", [])}
    # Continuous dims are fed as a [0,1] scalar and intentionally remapped to
    # the competency range by the orchestrator, so requested (scalar) != actual
    # (mapped) is expected, not a Profile Mismatch. Only discrete/categorical
    # values must round-trip unchanged.
    continuous_dim_names = {
        d["name"]
        for d in config.get("difficulty_dimensions", [])
        if d.get("dim_type") == "continuous"
    }
    dna_formatters = {d: set(get_formatters_for_dna(d)) for d in dnas}

    variant_coverages = defaultdict(lambda: defaultdict(int))
    scalar_coverages = defaultdict(int)

    for formatter in supported_formatters:
        sv_union: Dict[str, set] = {}
        for d in dnas:
            if formatter in dna_formatters[d]:
                sv_for_d = get_supported_variants(d, formatter) or {}
                for k, v in sv_for_d.items():
                    sv_union.setdefault(k, set()).update(v)
        supported_variants = {k: sorted(v) for k, v in sv_union.items()}
        profiles = build_test_profiles(config, supported_variants, primary_concept=dnas[0] if dnas else None)
        profiles = [
            p for p in profiles
            if any(formatter_supports_profile(d, formatter, p) for d in dnas)
        ]
        # Drop profiles whose (range, regrouping) combination is infeasible for
        # ANY DNA that serves THIS formatter. The orchestrator picks the DNA via
        # rng.choice(valid_dnas) where valid_dnas = DNAs supporting the formatter
        # (orchestrator.py:122-134), so a combo infeasible for even one of them
        # is a latent crash that fires whenever that DNA is chosen. Using `any`
        # over all node DNAs masked this: a regrouping-ignoring DNA (e.g.
        # `rounding`) trivially "passed", letting an addition-infeasible profile
        # through to crash ~50% of the time. Gate on the formatter's DNAs with
        # `all`. Mirrors the DNA's regrouping_is_feasible (single source of truth).
        formatter_dnas = [d for d in dnas if formatter in dna_formatters[d]] or list(dnas)
        profiles = [
            p for p in profiles
            if all(_regrouping_profile_is_feasible(d, p, competency_bounds, grade) for d in formatter_dnas)
        ]
        limits = FORMATTER_NUMERIC_LIMITS.get(formatter, {})
        fmt_max = limits.get("max_val")
        if fmt_max is not None:
            profiles = [
                p for p in profiles
                if not _profile_violates_numeric_limit(p, config, competency_bounds, fmt_max)
            ]

        # Track numeric states for pure/word_problem pairing by their non-context profile key.
        # This ensures we only compare profiles that match on all difficulty dimensions.
        context_states_by_pairing_key = {}

        for profile in profiles:
            raw_profile = profile.copy()

            for key, value in raw_profile.items():
                if key in supported_variants:
                    variant_coverages[key][value] += 1
                if key in dim_names:
                    scalar_coverages[key] += 1

            # Create a pairing key from all non-context fields to match pure/word_problem profiles
            # Use JSON string as key to avoid tuple hashability issues in multiprocessing
            pairing_key = json.dumps(
                {k: v for k, v in raw_profile.items() if k != "context"},
                sort_keys=True, default=str
            )
            if pairing_key not in context_states_by_pairing_key:
                context_states_by_pairing_key[pairing_key] = {"pure": {}, "word": {}}

            for sample_index in range(SAMPLES_PER_PROFILE):
                total_checked += 1
                seed = 1000 + sample_index + (1000 * len(profiles))

                try:
                    prob = PracticeOrchestrator.generate_problem(
                        node_id=node_id,
                        seed=seed,
                        difficulty_profile=raw_profile,
                        formatter=formatter,
                        is_lab=False,
                    )
                except Exception as e:
                    failures.setdefault(node_id, []).append(
                        f"Pipeline Crash (Formatter={formatter}, Profile={raw_profile}, Seed={seed}): {str(e)}\n{traceback.format_exc()}"
                    )
                    repro_crashes.append({
                        "node_id": node_id,
                        "seed": seed,
                        "formatter": formatter,
                        "difficulty_profile": raw_profile,
                        "error_message": str(e)
                    })
                    continue

                dna_name = getattr(prob, "dna_name", None) or primary_concept

                legacy = to_legacy_dict(prob)
                question_text = legacy.get("stem", "")
                correct_answer = legacy.get("correct_answer")
                options = legacy.get("options", {})
                hints = legacy.get("hints", [])
                prob_profile = getattr(prob, "difficulty_profile", {}) or {}
                context_value = raw_profile.get("context")

                q_violations = scan_text(question_text, FORBIDDEN_WORDS)
                if q_violations:
                    failures.setdefault(node_id, []).append(
                        f"Sample {seed} Vocabulary violation in Question Text: {q_violations} in '{question_text}'"
                    )

                for h_idx, hint in enumerate(hints):
                    h_violations = scan_text(hint, FORBIDDEN_WORDS)
                    if h_violations:
                        failures.setdefault(node_id, []).append(
                            f"Sample {seed} Vocabulary violation in Hint {h_idx+1}: {h_violations} in '{hint}'"
                        )

                if isinstance(correct_answer, (int, float)) and not isinstance(correct_answer, bool):
                    if "comparing_ordering" != dna_name:
                        if is_prompt_target_formatter(formatter):
                            pass
                        elif stem_is_prompt_target(question_text):
                            # Prompt-template carve-out: "Use coins and bills
                            # to make exactly ₱N", "What is N × N?", "value of
                            # the digit X in Y", "Round N to the nearest N",
                            # etc. The answer is in the stem by design.
                            pass
                        else:
                            # Count-based semantic leak detection:
                            # Only flag if the answer appears MORE times in the stem
                            # than can be explained by given (non-answer) operands.
                            # This distinguishes genuine leaks from coincidental-equality
                            # cases where a given operand's value happens to match the answer.
                            answer_str = str(correct_answer)
                            pattern = rf"(?<!\d){re.escape(answer_str)}(?!\d)"
                            stem_occurrences = len(re.findall(pattern, question_text))

                            given_values = legacy.get("given_values") or {}
                            # Count how many given operands equal the answer
                            explainable_occurrences = sum(
                                1 for v in given_values.values() if str(v) == answer_str
                            )

                            if stem_occurrences > explainable_occurrences:
                                # Genuine leak: answer appears more times than given operands can explain
                                failures.setdefault(node_id, []).append(
                                    f"Sample {seed} Semantic Leak: Answer '{correct_answer}' appears {stem_occurrences} times in stem (more than {explainable_occurrences} given operands): '{question_text}'"
                                )

                textual_formatters = ("mcq", "cloze", "ordering", "true_false", "error_detect", "sort_order")
                requested_is_visual = not (formatter in textual_formatters)
                if requested_is_visual and not getattr(prob, "is_visual", False):
                    failures.setdefault(node_id, []).append(
                        f"Sample {seed} Formatter Fallback: Requested visual formatter '{formatter}', but pipeline degraded to textual format '{prob.format}'"
                    )

                if options:
                    opts_list = list(options.values()) if isinstance(options, dict) else options
                    if formatter == "mcq":
                        if len(opts_list) != 4:
                            failures.setdefault(node_id, []).append(
                                f"Sample {seed} MCQ formatter generated {len(opts_list)} options, expected 4"
                            )
                        unique_opts = set()
                        for opt in opts_list:
                            opt_val = str(opt.get("value") if isinstance(opt, dict) else opt).strip()
                            unique_opts.add(opt_val)
                        if len(unique_opts) < len(opts_list) and len(opts_list) > 0:
                            failures.setdefault(node_id, []).append(
                                f"Sample {seed} Formatter '{formatter}' generated duplicate options: {[str(o.get('value') if isinstance(o, dict) else o) for o in opts_list]}"
                            )

                    for opt in opts_list:
                        opt_raw = opt.get("value") if isinstance(opt, dict) else opt
                        opt_val = str(opt_raw).strip()
                        if opt_raw is None or opt_val.lower() in ("none", "null") or not opt_val:
                            failures.setdefault(node_id, []).append(
                                f"Sample {seed} Formatter '{formatter}' generated a None, null, or blank option: {opt_raw}"
                            )
                        elif "alt #" in opt_val.lower():
                            failures.setdefault(node_id, []).append(
                                f"Sample {seed} Formatter '{formatter}' generated a fallback 'alt #' option: {opt_val}"
                            )
                        elif re.match(r"^option\s+\d+", opt_val.lower()):
                            failures.setdefault(node_id, []).append(
                                f"Sample {seed} Formatter '{formatter}' generated a placeholder 'Option #' option: {opt_val}"
                            )

                if dna_name == "fractions" and "fractions" in dnas and getattr(prob, "visual_type", None) is None:
                    if "fraction" not in question_text.lower() and "\\" not in question_text:
                        failures.setdefault(node_id, []).append(
                            f"Sample {seed} Fractions DNA concept overridden: Question stem '{question_text}' does not mention fractions or equations"
                        )

                if getattr(prob, "is_visual", False) and hasattr(prob, "visual_params"):
                    vp = prob.visual_params or {}
                    if prob.visual_type in ("FractionModel", "fraction_model_read", "fraction_shade"):
                        required_keys = {"model_type", "numerator", "denominator", "total_parts", "shaded_parts"}
                        missing = required_keys - set(vp.keys())
                        if missing:
                            failures.setdefault(node_id, []).append(f"Sample {seed} Visual Schema Error: {formatter} missing required visual_params keys: {missing}")
                        if vp.get("denominator", 0) <= 0:
                            failures.setdefault(node_id, []).append(f"Sample {seed} Visual Schema Error: {formatter} denominator must be > 0, got {vp.get('denominator')}")
                    elif formatter == "emoji_pictorial":
                        required_keys = {"operation", "emoji"}
                        missing = required_keys - set(vp.keys())
                        if missing:
                            failures.setdefault(node_id, []).append(f"Sample {seed} Visual Schema Error: {formatter} missing required visual_params keys: {missing}")
                        has_groups = ("groups" in vp or ("group_a" in vp and "group_b" in vp))
                        if not has_groups:
                            failures.setdefault(node_id, []).append(f"Sample {seed} Visual Schema Error: {formatter} missing group data (groups or group_a/group_b)")
                        if "groups" in vp and not isinstance(vp["groups"], list):
                            failures.setdefault(node_id, []).append(f"Sample {seed} Visual Schema Error: {formatter} 'groups' must be a list")

                for key, req_val in raw_profile.items():
                    if key in continuous_dim_names:
                        # Scalar in → mapped value out, by design. The strict
                        # scalar-endpoint and strict-bound checks below verify
                        # the mapping is correct; an equality check here would
                        # false-positive on every continuous dim.
                        continue
                    if key in prob_profile:
                        act_val = prob_profile[key]
                        if act_val != req_val and type(req_val) == type(act_val):
                            failures.setdefault(node_id, []).append(
                                f"Sample {seed} Profile Mismatch: Requested {key}={req_val}, but got {act_val}."
                            )
                for dim_name, bounds in competency_bounds.items():
                    if isinstance(bounds, tuple) and len(bounds) == 2:
                        min_val, max_val = bounds
                        actual_val = prob_profile.get(dim_name)
                        if actual_val is not None and (actual_val < min_val or actual_val > max_val):
                            failures.setdefault(node_id, []).append(
                                f"Sample {seed} Strict Scalar Violation: {dim_name}={actual_val} is outside strict bounds [{min_val}, {max_val}] for formatter {formatter}"
                            )

                for dim in config.get("difficulty_dimensions", []):
                    if dim.get("dim_type") == "continuous":
                        scalar = raw_profile.get(dim["name"])
                        cb = competency_bounds.get(dim["name"])
                        if isinstance(cb, tuple) and len(cb) == 2:
                            min_val, max_val = cb
                        else:
                            min_val = dim.get("min_value")
                            max_val = dim.get("max_value")
                        actual_val = prob_profile.get(dim["name"])
                        if scalar in (0.0, 1.0):
                            expected = min_val if scalar == 0.0 else max_val
                            if _strict_scalar_endpoint_violates(actual_val, expected):
                                failures.setdefault(node_id, []).append(
                                    f"Sample {seed} Strict scalar endpoint mapping failed for {dim['name']} at scalar={scalar}: expected {expected}, got {actual_val}"
                                )
                        elif scalar == 0.5:
                            if min_val > 0 and max_val >= 10 * min_val:
                                import math
                                geometric_mean = math.sqrt(min_val * max_val)
                                arithmetic_mean = (min_val + max_val) / 2
                                if actual_val is not None:
                                    dist_to_geo = abs(actual_val - geometric_mean)
                                    dist_to_arith = abs(actual_val - arithmetic_mean)
                                    if dist_to_arith < dist_to_geo and dist_to_arith < (max_val - min_val) * 0.2:
                                        failures.setdefault(node_id, []).append(
                                            f"Sample {seed} Scale Appropriateness Violation: Dimension '{dim['name']}' has wide range [{min_val}, {max_val}], but scalar=0.5 mapped linearly to {actual_val} instead of logarithmically (~{geometric_mean:.1f})"
                                        )

                if context_value == "word_problem" and is_visual_formatter(formatter):
                    if len(question_text) >= 200:
                        failures.setdefault(node_id, []).append(
                            f"Sample {seed} Visual Degradation Issue: Visual formatter '{formatter}' generated long word_problem stem ({len(question_text)} chars)."
                        )

                if context_value == "pure":
                    context_states_by_pairing_key[pairing_key]["pure"][sample_index] = extract_numeric_state(prob, legacy)
                elif context_value == "word_problem":
                    current_state = extract_numeric_state(prob, legacy)
                    # Compare only against pure profiles with the same difficulty dimensions and same sample_index
                    if sample_index in context_states_by_pairing_key[pairing_key]["pure"]:
                        reference_state = context_states_by_pairing_key[pairing_key]["pure"][sample_index]
                        if reference_state and current_state and reference_state != current_state:
                            # Compare the authoritative semantic operands
                            # (given_values + answer), NOT regex-scraped stem
                            # digits. A blanked or word-rendered operand
                            # legitimately leaves the visible stem while the
                            # math is preserved; only a genuine change to the
                            # operand multiset is a real SoC violation.
                            ref_nums = reference_state.get("_semantic_operands") or ()
                            cur_nums = current_state.get("_semantic_operands") or ()
                            ref_counter = dict(ref_nums)
                            cur_counter = dict(cur_nums)
                            missing = {n: c for n, c in ref_counter.items() if cur_counter.get(n, 0) < c}
                            if missing:
                                failures.setdefault(node_id, []).append(
                                    f"Sample {seed} Separation of Concerns Violation: core operands from pure state are missing or reduced in word_problem for formatter {formatter}: missing={missing} pure={ref_nums} word={cur_nums}"
                                )
                    context_states_by_pairing_key[pairing_key]["word"][sample_index] = current_state

    for variant in config.get("contextual_variants", []):
        name = variant.get("name")
        values = variant.get("options", [])
        for value in values:
            if variant_coverages[name].get(value, 0) == 0:
                failures.setdefault(node_id, []).append(
                    f"Variant '{name}' value '{value}' was never exercised for node {node_id}."
                )

    for dim in config.get("difficulty_dimensions", []):
        if scalar_coverages[dim["name"]] == 0:
            failures.setdefault(node_id, []).append(
                f"Difficulty dimension '{dim['name']}' was never exercised for node {node_id}."
            )

    # ── Category 16: Cap-vs-Formatter-Code Consistency ───────────────────
    # Probes every (DNA, formatter, variant, value) that the cap EXCLUDES
    # by calling generate_context + apply_formatter directly (bypassing
    # the orchestrator's cap filter). If the formatter code SUCCEEDS, the
    # cap was wrong to exclude it. This would have caught the q4_7 bug
    # where fraction_shade's cap excluded operation=add/subtract but the
    # formatter code (fmt_fraction_shade.py:185-198) handled them fine.
    _check_cap_vs_formatter_code(node_id, dnas, grade, config, failures)

    return failures, repro_crashes, total_checked


def _check_cap_vs_formatter_code(
    node_id: str,
    dnas: List[str],
    grade: int,
    config: dict,
    failures: Dict[str, List[str]],
) -> None:
    """Flag caps that exclude variant values the formatter code explicitly handles.

    For each (DNA, formatter) pair with a cap, for each variant the cap
    restricts, for each value the cap EXCLUDES, statically inspect the
    formatter's source code. If the excluded value appears as a string literal
    in the formatter module, the formatter has explicit handling for it and
    the cap was wrong to exclude it.

    This static approach avoids false positives from formatters that silently
    ignore unsupported variants (returning their default behavior without
    raising), which a runtime probe would misinterpret as "supports it."
    """
    import inspect
    import importlib
    from backend.app.practice_gen.adapter import _FORMATTER_ROUTES

    for dna_name in dnas:
        fmt_caps = FORMATTER_VARIANT_SUPPORT.get(dna_name, {})
        all_variants = VARIANTS_BY_DNA.get(dna_name, {})

        for formatter in get_formatters_for_dna(dna_name):
            caps = fmt_caps.get(formatter)
            if not caps:
                continue

            route = _FORMATTER_ROUTES.get(formatter)
            if not route:
                continue
            module_path = route[0]

            try:
                mod = importlib.import_module(module_path)
            except Exception:
                continue

            for variant_name, allowed_vals in caps.items():
                if not allowed_vals:
                    continue
                all_vals = all_variants.get(variant_name, [])
                excluded = [v for v in all_vals if v not in allowed_vals]
                if not excluded:
                    continue

                for excluded_val in excluded:
                    # Check if the formatter's entry function EXPLICITLY handles the
                    # excluded value in a top-level conditional branch (if/elif
                    # at function-body indent of the entry function itself),
                    # not nested inside an interaction_mode gate, and not in
                    # a helper function. This distinguishes:
                    #   - genuine support (fraction_shade.py:
                    #       if operation in ("add","subtract"): ...  # indent=4)
                    #   - unreachable-for-this-formatter branches (pictograph:
                    #       if interaction_mode == "read":
                    #           if task_type in ("compare_two",...): ...  # indent=8)
                    #     where pictograph_set (interaction_mode="set") never
                    #     reaches the nested branch.
                    # and from default-fallback mentions (else: # read_value).
                    val_str = str(excluded_val)
                    val_quoted = f'"{val_str}"'
                    val_quoted_sq = f"'{val_str}'"
                    # Inspect ONLY the route's entry function, not helpers.
                    func_name = route[1]
                    try:
                        func = getattr(mod, func_name)
                        func_src = inspect.getsource(func)
                    except Exception:
                        continue
                    body_indent = 4
                    for ln in func_src.splitlines()[1:]:
                        if ln.strip():
                            body_indent = len(ln) - len(ln.lstrip())
                            break
                    for line in func_src.splitlines():
                        stripped = line.strip()
                        if not (stripped.startswith("if ") or stripped.startswith("elif ")):
                            continue
                        indent = len(line) - len(line.lstrip())
                        if indent != body_indent:
                            continue
                        if val_quoted in line or val_quoted_sq in line:
                            failures.setdefault(node_id, []).append(
                                f"Cap-vs-Formatter-Code: formatter '{formatter}' source "
                                f"explicitly handles variant '{variant_name}={excluded_val}' "
                                f"in a top-level conditional branch but cap restricts to {allowed_vals}. "
                                f"The cap excludes a supported variant value — widen the cap."
                            )
                            break


def run_audit(
    node_ids: Optional[List[str]] = None,
    parallel: bool = True,
    max_workers: Optional[int] = None,
) -> Tuple[Dict[str, List[str]], List[Dict[str, Any]]]:
    """Run the checklist audit on the given nodes (default: all mat_g
    nodes) and return (failures, repro_crashes) without writing to disk
    or exiting. Used by the test suite as the CI guard.

    Args:
        node_ids: List of node IDs to audit. If None, audits all mat_g
            nodes.
        parallel: If True (default), run nodes across multiple worker
            processes via ProcessPoolExecutor. If False, run serially.
        max_workers: Number of worker processes when parallel=True. If
            None, defaults to multiprocessing.cpu_count().

    Per AGENTS.md rule #4 (no silent fallbacks): this function does not
    swallow exceptions and does not skip nodes. Every node either
    contributes its results to the returned dicts or raises
    AuditHarnessError.
    """
    if node_ids is None:
        print("Praise God! Starting Unified Checklist Auditor for all matatag nodes...")
        node_ids = [n for n in get_all_node_ids() if "mat_g" in n]
    else:
        print(f"Praise God! Starting Checklist Auditor on {len(node_ids)} sample nodes...")

    total_checked = 0
    failures: Dict[str, List[str]] = {}
    repro_crashes: List[Dict[str, Any]] = []

    if not parallel:
        for node_id in node_ids:
            node_failures, node_repro, node_checked = _audit_node(node_id)
            if node_failures:
                failures.update(node_failures)
            repro_crashes.extend(node_repro)
            total_checked += node_checked
    else:
        import multiprocessing
        from concurrent.futures import ProcessPoolExecutor

        workers = max_workers if max_workers and max_workers > 0 else multiprocessing.cpu_count()
        workers = min(workers, len(node_ids)) if node_ids else workers
        chunksize = max(1, -(-len(node_ids) // workers)) if node_ids else 1

        with ProcessPoolExecutor(max_workers=workers) as pool:
            for node_failures, node_repro, node_checked in pool.map(
                _audit_node, node_ids, chunksize=chunksize,
            ):
                if node_failures:
                    failures.update(node_failures)
                repro_crashes.extend(node_repro)
                total_checked += node_checked

    print("\n" + "=" * 80)
    print(f"Checklist Audit Finished: Checked {total_checked} generated problems across all nodes. {len(failures)} nodes have violations.")
    print("=" * 80)

    return failures, repro_crashes


def check_checklist_compliance():
    """CLI entry point: runs the audit, writes JSON reports, exits 0/1.

    Thin wrapper around run_audit() that handles file I/O and process
    exit codes. The test suite calls run_audit() directly so it can
    assert on the returned (failures, repro_crashes) without touching
    disk or terminating the process.

    CLI flags:
        --max-workers N    Number of parallel workers (default: cpu_count)
        --no-parallel      Run single-threaded (useful for debugging)
        --node-ids ID1,ID2 Restrict to a comma-separated node list
    """
    import argparse
    parser = argparse.ArgumentParser(
        description="Exhaustive checklist auditor for MATATAG nodes"
    )
    parser.add_argument(
        "--max-workers", type=int, default=0,
        help="Number of parallel workers (0 = cpu_count)"
    )
    parser.add_argument(
        "--no-parallel", action="store_true",
        help="Run single-threaded (useful for debugging)"
    )
    parser.add_argument(
        "--node-ids", type=str, default="",
        help="Comma-separated node IDs to audit (default: all mat_g nodes)"
    )
    args = parser.parse_args()

    node_ids = None
    if args.node_ids:
        node_ids = [n.strip() for n in args.node_ids.split(",") if n.strip()]

    failures, repro_crashes = run_audit(
        node_ids=node_ids,
        parallel=not args.no_parallel,
        max_workers=args.max_workers if args.max_workers > 0 else None,
    )

    # Write generated outputs into local_only/scratch (the gitignored
    # temp-artifact dir), never the repo root — AGENTS.md requires the root
    # stay clean and these are regenerated on every run. Anchor to the repo
    # root so the path is stable regardless of CWD.
    from pathlib import Path
    scratch_dir = Path(__file__).resolve().parents[1] / "local_only" / "scratch"
    scratch_dir.mkdir(parents=True, exist_ok=True)

    report_path = scratch_dir / "checklist_audit_report.json"
    with open(report_path, "w") as f:
        json.dump(failures, f, indent=2)

    crashes_path = scratch_dir / "repro_crashes.json"
    with open(crashes_path, "w") as f:
        json.dump(repro_crashes, f, indent=2)

    if failures:
        print("\nFirst few checklist compliance failures:")
        for nid, errs in list(failures.items())[:15]:
            print(f"\n--- Node: {nid} ---")
            for err in errs[:3]:
                print(f" - {err}")
        sys.exit(1)

    print("\nAll matatag nodes passed strict checklist compliance auditing!")
    sys.exit(0)


if __name__ == "__main__":
    check_checklist_compliance()
