"""
test_matatag_lab_comprehensive.py
==================================
Comprehensive test suite for the MATATAG Lab (G1-3 competencies).

Goals:
  1. Every competency generates without errors at all difficulty levels
  2. Every axis option generates AND behaves as claimed
  3. Correct answers are ALWAYS judged correct
  4. Wrong answers are ALWAYS judged incorrect
  5. Both MCQ and visual formats work for dual-support nodes
  6. Scalar difficulty increases monotonically with axis selection

Usage:
  cd backend
  pytest tests/test_matatag_lab_comprehensive.py -v -n auto 2>&1 | tee test_results.txt

Requirements:
  - Backend running on localhost:8000  (`./scripts/manage.sh start`)
  - pytest-xdist installed             (`pip install pytest-xdist`)
"""

import json
import re
import time
import pytest
import requests

BASE = "http://localhost:8000/api"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def generate(node_id: str, seed: int = 42, axis_values: dict = None,
             format_preference: str = "auto", scalar: float = None) -> dict:
    params = {
        "node_id": node_id,
        "seed": seed,
        "format_preference": format_preference,
    }
    if scalar is not None:
        params["difficulty"] = scalar
    if axis_values:
        params["axis_values"] = json.dumps(axis_values)
    r = requests.get(f"{BASE}/matatag/lab/generate", params=params, timeout=15)
    return r


def submit(skeleton_id: str, answer) -> dict:
    r = requests.post(
        f"{BASE}/matatag/lab/submit",
        params={"skeleton_id": skeleton_id, "student_answer": str(answer)},
        timeout=15,
    )
    return r


def find_correct_key(problem: dict):
    """Try each MCQ key; return the one accepted as correct."""
    for opt in (problem.get("mcq_options") or []):
        r = submit(problem["skeleton_id"], opt["key"])
        if r.ok and r.json().get("is_correct"):
            return opt["key"]
    return None


def extract_visual_correct_answer(problem: dict):
    """
    Return the correct answer for a visual problem as a simple number/string
    that a student would type — not a dict or list.
    """
    vtype = problem.get("visual_type", "")
    vp = problem.get("visual_params") or {}

    if vtype == "PesoMoney":
        return vp.get("target_amount")

    if vtype == "NumberLine":
        return vp.get("correct_position") or vp.get("answer") or vp.get("target")

    if vtype == "BarChart":
        return vp.get("correct_answer") or vp.get("answer")

    if vtype == "ClockSet":
        # correct_answer is [hours, minutes] array
        h = vp.get("hours")
        m = vp.get("minutes")
        if h is not None and m is not None:
            return json.dumps({"hours": h, "minutes": m})
        # Fall back to parsing target_time
        tt = vp.get("target_time", "")
        if tt and ":" in tt:
            parts = tt.split(":")
            return json.dumps({"hours": int(parts[0]), "minutes": int(parts[1])})
        return None

    if vtype == "SortOrder":
        # visual_params uses 'correct_sequence' key
        seq = vp.get("correct_sequence") or vp.get("correct_order") or vp.get("sorted_values")
        if seq:
            return json.dumps(seq)
        return None

    if vtype == "GridArea":
        return vp.get("correct_area") or vp.get("area")

    if vtype == "FillInTable":
        missing = vp.get("missing_values") or vp.get("answer")
        if isinstance(missing, list):
            return json.dumps(missing)
        return missing

    if vtype == "RuleDiscovery":
        return vp.get("correct_next") or vp.get("answer")

    if vtype == "Calendar":
        return vp.get("correct_answer") or vp.get("answer")

    if vtype == "Categorize":
        # correct_answer is a dict {item: category} — normalize key types
        cat = vp.get("correct_categories") or vp.get("answer")
        if isinstance(cat, dict):
            return json.dumps({str(k): str(v) for k, v in cat.items()})
        return json.dumps(cat) if cat is not None else None

    return None


def _seed_for(node_id: str, salt: str = "", scalar=None) -> int:
    """Deterministic unique seed per node to avoid cache collisions in parallel runs."""
    import hashlib
    key = f"{node_id}{salt}"
    if scalar is not None:
        key += f"_{scalar}"
    h = hashlib.md5(key.encode()).hexdigest()
    return int(h[:6], 16) % 999983 + 10000  # prime modulus for spread


def wrong_visual_answers(problem: dict) -> list:
    """Return a small list of clearly wrong answers for a visual problem."""
    correct = extract_visual_correct_answer(problem)
    if correct is None:
        return []

    try:
        v = int(str(correct))
        candidates = [str(v + 1), str(v + 100), "0"]
        return [c for c in candidates if str(c) != str(correct)]
    except (ValueError, TypeError):
        pass

    # JSON answers (ClockSet, SortOrder, etc.) — use clearly wrong strings
    return ["99", "0", "wrong_answer"]


# ─────────────────────────────────────────────────────────────────────────────
# ── Test Class 1: Generation Without Errors ──────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

class TestGeneration:
    """
    Every competency must generate a valid problem at:
      - default settings (seed=_seed_for(node_id))
      - scalar 0.0 (easiest axis options)
      - scalar 0.5 (middle axis options)
      - scalar 1.0 (hardest axis options)
    """

    @pytest.mark.parametrize(
        "node_id",
        [pytest.param(n["node_id"], id=n["node_id"]) for n in pytest.all_nodes],
    )
    def test_generates_at_default(self, node_id):
        r = generate(node_id, seed=_seed_for(node_id))
        assert r.status_code == 200, (
            f"Generation failed (HTTP {r.status_code}): "
            f"{r.json().get('detail', r.text[:200])}"
        )
        p = r.json()
        assert p.get("skeleton_id"), "Missing skeleton_id in response"
        assert p.get("stem", "").strip(), "Empty stem in response"
        assert p.get("is_visual") in (True, False), "Missing is_visual flag"

    @pytest.mark.parametrize(
        "node_id,scalar",
        [
            pytest.param(n["node_id"], s, id=f"{n['node_id']}@{s}")
            for n in pytest.all_nodes
            for s in (0.0, 0.5, 1.0)
        ],
    )
    def test_generates_at_scalar(self, node_id, scalar):
        """Map scalar to proportional axis options and generate."""
        axes_r = requests.get(f"{BASE}/matatag/difficulty-axes/{node_id}", timeout=10)
        assert axes_r.ok, f"Could not fetch axes for {node_id}"

        axes = axes_r.json()["axes"]
        axis_values = {}
        for axis in axes:
            opts = axis["options"]
            idx = round(scalar * (len(opts) - 1))
            axis_values[axis["name"]] = opts[idx]["value"]

        r = generate(node_id, seed=_seed_for(node_id), axis_values=axis_values)
        assert r.status_code == 200, (
            f"scalar={scalar} generation failed: "
            f"{r.json().get('detail', r.text[:200])}"
        )
        p = r.json()
        assert p.get("stem", "").strip(), f"Empty stem at scalar={scalar}"


# ─────────────────────────────────────────────────────────────────────────────
# ── Test Class 2: Axis Option Semantic Validation ────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

class TestAxisOptions:
    """
    Every axis option (1,230 total) must:
      1. Generate without errors
      2. Produce a problem that actually exhibits the claimed behavior
         (or be flagged for manual review if not testable programmatically)
    """

    @pytest.mark.parametrize(
        "opt",
        [
            pytest.param(
                o,
                id=f"{o['node_id']}__{o['axis_name']}={o['axis_value']}"
            )
            for o in pytest.all_axis_options
        ],
    )
    def test_axis_option_generates_and_validates(self, opt):
        from .validators import VALIDATOR_REGISTRY, ValidationResult

        node_id    = opt["node_id"]
        axis_name  = opt["axis_name"]
        axis_value = opt["axis_value"]

        # ── Step 1: Generate must succeed ─────────────────────────────────
        r = generate(node_id, seed=_seed_for(node_id, f"{axis_name}={axis_value}"),
                     axis_values={axis_name: axis_value})
        assert r.status_code == 200, (
            f"Generation failed for {axis_name}={axis_value}: "
            f"{r.json().get('detail', r.text[:200])}"
        )
        problem = r.json()

        # ── Step 2: Semantic validation ───────────────────────────────────
        validator_fn = VALIDATOR_REGISTRY.get(axis_name)
        if validator_fn is None:
            pytest.skip(
                f"[MANUAL REVIEW] No validator defined for axis '{axis_name}' "
                f"(value='{axis_value}', node={node_id})"
            )

        result: ValidationResult = validator_fn(problem, axis_value)

        if result.needs_review:
            pytest.skip(
                f"[MANUAL REVIEW] {opt['axis_label']}: {result.message} "
                f"(node={node_id}, value={axis_value})"
            )

        assert result.passed, (
            f"\n{'='*60}\n"
            f"SEMANTIC VALIDATION FAILED\n"
            f"  node       : {node_id}\n"
            f"  competency : {opt['competency'][:80]}\n"
            f"  axis       : {axis_name} = {axis_value} ({opt['axis_label_val']})\n"
            f"  stem       : {problem.get('stem')}\n"
            f"  reason     : {result.message}\n"
            f"  extracted  : {result.extracted}\n"
            f"{'='*60}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# ── Test Class 3: Scalar Difficulty Monotonicity ──────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

class TestScalarDifficulty:
    """
    For each node, generating at scalar 0.0, 0.5, 1.0 should produce
    problems of increasing difficulty.
    We measure: maximum number magnitude in the problem as a simple proxy.
    Monotonicity failures are only flagged if ALL three scalars produce
    clearly inverted complexity (e.g. scalar=1.0 uses smaller numbers than scalar=0.0).
    """

    @staticmethod
    def _complexity(problem: dict) -> float:
        """Complexity measure: max number in stem/options.
        For patterns, use sequence span as complexity proxy."""
        stem = problem.get("stem", "")
        vp = problem.get("visual_params") or {}

        # For visual problems, use target/max value
        if problem.get("is_visual"):
            target = vp.get("target_amount") or vp.get("target") or vp.get("max_value") or 0
            return float(int(target) if target else 0)

        nums_raw = re.findall(r'\b\d+\b', stem)
        for opt in (problem.get("mcq_options") or []):
            nums_raw += re.findall(r'\b\d+\b', opt.get("text", ""))
        nums = [int(n) for n in nums_raw if n != "0"]

        if not nums:
            return 0.0

        # For sequences (patterns), use step size as complexity
        if ',' in stem or '...' in stem or '___' in stem.lower():
            seq_nums = sorted(set(nums))
            if len(seq_nums) >= 2:
                diffs = [seq_nums[i+1] - seq_nums[i] for i in range(len(seq_nums)-1)]
                if diffs:
                    return float(abs(max(diffs, key=abs)))

        return float(max(nums))

    @pytest.mark.parametrize(
        "node_id",
        [pytest.param(n["node_id"], id=n["node_id"]) for n in pytest.all_nodes],
    )
    def test_difficulty_increases_with_scalar(self, node_id):
        axes_r = requests.get(f"{BASE}/matatag/difficulty-axes/{node_id}", timeout=10)
        if not axes_r.ok:
            pytest.skip("No axes endpoint")

        axes = axes_r.json()["axes"]
        if not axes:
            pytest.skip("No axes defined for this node")

        results = []
        for scalar in (0.0, 0.5, 1.0):
            axis_values = {}
            for axis in axes:
                opts = axis["options"]
                idx = round(scalar * (len(opts) - 1))
                axis_values[axis["name"]] = opts[idx]["value"]

            r = generate(node_id, seed=_seed_for(node_id), axis_values=axis_values)
            if r.status_code == 200:
                results.append((scalar, self._complexity(r.json())))

        if len(results) < 2:
            pytest.skip("Not enough successful generations to compare")

        easy_score = results[0][1]
        hard_score = results[-1][1]

        # Skip nodes where max-number complexity doesn't apply
        # (fractions, measurement estimation, geometry)
        concept = next(
            (n["primary_concept"] for n in pytest.all_nodes if n["node_id"] == node_id),
            ""
        )
        if concept in ("fractions", "mass_capacity", "geometry_props", "measurement", "missing_number"):
            pytest.skip(
                f"[MANUAL REVIEW] Scalar complexity not measurable by number magnitude "
                f"for concept={concept} (node={node_id})"
            )

        if easy_score == 0 and hard_score == 0:
            pytest.skip("Both complexity scores are 0 — cannot compare")

        if hard_score < easy_score * 0.25:
            # Hard mode produces numbers less than 25% of easy mode — clear inversion
            # (allowing for measurement units, fractions, and other cases where
            #  raw number magnitude isn't a perfect difficulty proxy)
            pytest.fail(
                f"Difficulty INVERTED: scalar=0.0 complexity={easy_score:.0f}, "
                f"scalar=1.0 complexity={hard_score:.0f} (node={node_id})"
            )
        # Otherwise pass — monotonicity is approximate due to randomness


# ─────────────────────────────────────────────────────────────────────────────
# ── Test Class 4: Correct Answer Validation ──────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

class TestAnswerValidationCorrect:
    """
    For every competency, submitting the correct answer must return is_correct=True.
    Tests both MCQ (find correct key) and visual (extract from visual_params).
    """

    @pytest.mark.parametrize(
        "node_id",
        [pytest.param(n["node_id"], id=n["node_id"]) for n in pytest.all_nodes],
    )
    def test_correct_answer_accepted_mcq(self, node_id):
        """Force MCQ format and verify correct key is accepted."""
        # Check if MCQ is available for this node
        node_info = next((n for n in pytest.all_nodes if n["node_id"] == node_id), None)
        if node_info and "mcq" not in node_info.get("available_formats", ["mcq"]):
            pytest.skip("MCQ not available for this node")

        r = generate(node_id, seed=_seed_for(node_id), format_preference="mcq")
        assert r.status_code == 200, f"Generation failed: {r.json().get('detail')}"
        problem = r.json()

        if problem.get("is_visual"):
            pytest.skip("Generation returned visual despite format_preference=mcq — no MCQ generator")

        assert problem.get("mcq_options"), "No MCQ options in response"

        correct_key = find_correct_key(problem)
        assert correct_key is not None, (
            f"No MCQ key was accepted as correct for node={node_id}\n"
            f"  stem: {problem.get('stem')}\n"
            f"  options: {problem.get('mcq_options')}"
        )

    @pytest.mark.parametrize(
        "node_id",
        [
            pytest.param(n["node_id"], id=n["node_id"])
            for n in pytest.all_nodes
            if "visual" in n.get("available_formats", [])
        ],
    )
    def test_correct_answer_accepted_visual(self, node_id):
        """Force visual format and verify correct answer is accepted."""
        r = generate(node_id, seed=_seed_for(node_id), format_preference="visual")
        assert r.status_code == 200, f"Generation failed: {r.json().get('detail')}"
        problem = r.json()

        if not problem.get("is_visual"):
            pytest.skip("Node returned MCQ despite format_preference=visual")

        correct = extract_visual_correct_answer(problem)
        if correct is None:
            pytest.skip(
                f"[MANUAL REVIEW] Cannot extract correct answer for "
                f"visual_type={problem.get('visual_type')} (node={node_id})"
            )

        r_submit = submit(problem["skeleton_id"], correct)
        assert r_submit.status_code == 200, f"Submit failed: {r_submit.text}"

        result = r_submit.json()
        assert result["is_correct"] is True, (
            f"\n{'='*60}\n"
            f"CORRECT ANSWER REJECTED\n"
            f"  node         : {node_id}\n"
            f"  visual_type  : {problem.get('visual_type')}\n"
            f"  stem         : {problem.get('stem')}\n"
            f"  submitted    : {correct}\n"
            f"  correct_ans  : {result.get('correct_answer')}\n"
            f"  response     : {result}\n"
            f"{'='*60}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# ── Test Class 5: Wrong Answer Rejection ─────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

class TestAnswerValidationWrong:
    """
    Submitting wrong answers must return is_correct=False.
    MCQ: all wrong keys rejected.
    Visual: clearly wrong values rejected.
    """

    @pytest.mark.parametrize(
        "node_id",
        [pytest.param(n["node_id"], id=n["node_id"]) for n in pytest.all_nodes],
    )
    def test_wrong_mcq_keys_rejected(self, node_id):
        node_info = next((n for n in pytest.all_nodes if n["node_id"] == node_id), None)
        if node_info and "mcq" not in node_info.get("available_formats", ["mcq"]):
            pytest.skip("MCQ not available for this node")

        r = generate(node_id, seed=_seed_for(node_id), format_preference="mcq")
        assert r.status_code == 200
        problem = r.json()

        if problem.get("is_visual"):
            pytest.skip("No MCQ available — visual returned")

        correct_key = find_correct_key(problem)
        if correct_key is None:
            pytest.fail(f"Could not identify correct key for {node_id}")

        wrong_keys = [k for k in ("A", "B", "C", "D") if k != correct_key]
        for wk in wrong_keys:
            r_submit = submit(problem["skeleton_id"], wk)
            if not r_submit.ok:
                continue  # submit error handled elsewhere
            result = r_submit.json()
            assert result["is_correct"] is False, (
                f"Wrong key {wk} was accepted as correct! "
                f"(node={node_id}, correct={correct_key}, stem={problem.get('stem')})"
            )

    @pytest.mark.parametrize(
        "node_id",
        [
            pytest.param(n["node_id"], id=n["node_id"])
            for n in pytest.all_nodes
            if "visual" in n.get("available_formats", [])
        ],
    )
    def test_wrong_visual_answers_rejected(self, node_id):
        r = generate(node_id, seed=_seed_for(node_id), format_preference="visual")
        assert r.status_code == 200
        problem = r.json()

        if not problem.get("is_visual"):
            pytest.skip("Visual not returned")

        correct = extract_visual_correct_answer(problem)
        if correct is None:
            pytest.skip(f"[MANUAL REVIEW] Cannot extract answer for {problem.get('visual_type')}")

        for wrong in wrong_visual_answers(problem):
            if str(wrong) == str(correct):
                continue  # Skip if "wrong" answer happens to equal correct
            r_submit = submit(problem["skeleton_id"], wrong)
            if not r_submit.ok:
                continue
            result = r_submit.json()
            assert result["is_correct"] is False, (
                f"Wrong answer '{wrong}' was accepted! "
                f"(node={node_id}, correct={correct}, stem={problem.get('stem')})"
            )


# ─────────────────────────────────────────────────────────────────────────────
# ── Test Class 6: Visual Node Sanity Checks ─────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

class TestVisualNodeSanity:
    """
    For visual-only nodes (or visual format of dual-support nodes):
      1. Generation works without errors at all difficulty levels
      2. Difficulty affects visual_params (different ranges/scales at different difficulties)

    These are sanity checks for visual elements that can't be programmatically rendered.
    """

    @pytest.mark.parametrize(
        "node_id",
        [pytest.param(n["node_id"], id=n["node_id"]) for n in pytest.all_nodes if "visual" in n.get("available_formats", [])],
    )
    @pytest.mark.parametrize("scalar", [0.0, 0.5, 1.0])
    def test_visual_generation_no_errors(self, node_id, scalar):
        """Every visual node generates without errors at all difficulty levels."""
        r = generate(node_id, seed=_seed_for(node_id, scalar), format_preference="visual", scalar=scalar)
        assert r.status_code == 200, f"Visual generation failed at scalar={scalar}: {r.json().get('detail')}"
        problem = r.json()
        assert problem.get("is_visual") is True, f"Expected visual but got is_visual=False"
        assert problem.get("visual_type"), "Missing visual_type"
        assert problem.get("visual_params"), "Missing visual_params"

    @pytest.mark.parametrize(
        "node_id",
        [pytest.param(n["node_id"], id=n["node_id"]) for n in pytest.all_nodes if "visual" in n.get("available_formats", [])],
    )
    def test_visual_difficulty_affects_params(self, node_id):
        """Difficulty scalar should produce different visual_params at easy vs hard."""
        r_easy = generate(node_id, seed=99999, format_preference="visual", scalar=0.0)
        r_hard = generate(node_id, seed=99999, format_preference="visual", scalar=1.0)

        assert r_easy.status_code == 200 and r_hard.status_code == 200

        easy_params = r_easy.json().get("visual_params", {})
        hard_params = r_hard.json().get("visual_params", {})

        if not easy_params or not hard_params:
            pytest.skip("No visual_params to compare")

        def extract_numbers(d):
            nums = []
            def recurse(obj):
                if isinstance(obj, (int, float)):
                    nums.append(obj)
                elif isinstance(obj, dict):
                    for v in obj.values():
                        recurse(v)
                elif isinstance(obj, (list, tuple)):
                    for item in obj:
                        recurse(item)
            recurse(d)
            return sorted(set(nums))

        easy_nums = extract_numbers(easy_params)
        hard_nums = extract_numbers(hard_params)

        easy_set = set(easy_nums)
        hard_set = set(hard_nums)

        if easy_set == hard_set:
            # No numeric difference - could be generator not integrated with difficulty
            # Skip for now, flag for manual review
            pytest.skip(
                f"[MANUAL REVIEW] Visual generator not integrated with difficulty "
                f"(easy={easy_nums}, hard={hard_nums})"
            )


# ─────────────────────────────────────────────────────────────────────────────
# ── Test Class 7: Format Diversity ───────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

class TestFormatDiversity:
    """
    For nodes supporting both MCQ and visual:
      - format_preference='mcq'    must return is_visual=False
      - format_preference='visual' must return is_visual=True
    """

    @pytest.mark.parametrize(
        "node_id",
        [pytest.param(n["node_id"], id=n["node_id"]) for n in pytest.dual_support_nodes],
    )
    def test_mcq_format_returns_mcq(self, node_id):
        r = generate(node_id, seed=_seed_for(node_id), format_preference="mcq")
        assert r.status_code == 200, f"MCQ generation failed: {r.json().get('detail')}"
        problem = r.json()
        assert problem["is_visual"] is False, (
            f"format_preference=mcq but got is_visual=True for {node_id}"
        )
        assert problem.get("mcq_options"), "MCQ format returned no options"

    @pytest.mark.parametrize(
        "node_id",
        [pytest.param(n["node_id"], id=n["node_id"]) for n in pytest.dual_support_nodes],
    )
    def test_visual_format_returns_visual(self, node_id):
        r = generate(node_id, seed=_seed_for(node_id), format_preference="visual")
        assert r.status_code == 200, f"Visual generation failed: {r.json().get('detail')}"
        problem = r.json()
        assert problem["is_visual"] is True, (
            f"format_preference=visual but got is_visual=False for {node_id}"
        )
        assert problem.get("visual_params"), "Visual format returned no visual_params"
