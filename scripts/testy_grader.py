#!/usr/bin/env python3
"""
testy_grader.py — Batch test harness for testy.py problem generation.

Generates problems across many standards and types, validates structural
integrity, reports pass/fail statistics, and saves approved problems.

Usage:
    python scripts/testy_grader.py                         # run built-in suite
    python scripts/testy_grader.py --types mcq,ordering    # specific types only
    python scripts/testy_grader.py --standards 5.NF.A.1,L.4.1.g
    python scripts/testy_grader.py --interests "minecraft"
    python scripts/testy_grader.py --verbose               # show all problems
    python scripts/testy_grader.py --fail-only             # failures only
    python scripts/testy_grader.py --start-server          # start server first
"""

import sys
import json
import time
import argparse
import datetime
from pathlib import Path
from dataclasses import dataclass, field

# ── Path bootstrap ─────────────────────────────────────────────────────────────
# Allow running from any directory; import functions from testy.py
_SCRIPTS_DIR = Path(__file__).parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from testy import (
    ROOT,
    SCRATCH_DIR,
    ELIGIBLE_MODES,
    subject_category,
    mode_for_standard,
    normalize_standard,
    find_by_standard_file,
    load_standard_context,
    build_prompt,
    load_previous_problems,
    save_problem,
    extract_structured_output,
    server_is_running,
    start_server,
    run_testy_agent_http,
    run_testy_agent_subprocess,
    DEFAULT_PORT,
    DEFAULT_MODEL,
    REQUESTS_AVAILABLE,
)

# ── Constants ──────────────────────────────────────────────────────────────────

APPROVED_FILE = SCRATCH_DIR / "approved_problems.jsonl"

# ── Built-in test suite ────────────────────────────────────────────────────────
# Each entry: (standard, question_type, interests)
# Covers all 5 types, 5 grade bands, all subject categories

TEST_SUITE = [
    # ── Math — numeric_input ──────────────────────────────────────────────────
    ("K.OA.A.1",    "numeric_input", "dinosaurs"),
    ("3.NF.A.1",    "numeric_input", "soccer"),
    ("5.NF.A.1",    "numeric_input", "minecraft"),
    ("5.OA.A.1",    "numeric_input", "space exploration"),
    ("6.EE.A.1",    "numeric_input", "basketball"),
    ("7.NS.A.1",    "numeric_input", "cooking"),
    ("8.EE.A.1",    "numeric_input", "robotics"),

    # ── Math — multi_select ───────────────────────────────────────────────────
    ("1.OA.A.1",    "multi_select",  "superheroes"),
    ("5.NF.A.1",    "multi_select",  "art"),
    ("6.EE.A.1",    "multi_select",  "video games"),
    ("8.EE.A.1",    "multi_select",  "music"),

    # ── Math — ordering ───────────────────────────────────────────────────────
    ("3.MD.C.5",    "ordering",      "animals"),
    ("7.NS.A.1",    "ordering",      "history"),
    ("A-REI.B.3",   "ordering",      "sports"),

    # ── Math — mcq ───────────────────────────────────────────────────────────
    ("K.OA.A.1",    "mcq",           "trains"),
    ("3.NF.A.1",    "mcq",           "cats"),
    ("6.RP.A.1",    "mcq",           "fashion"),

    # ── Language — cloze ──────────────────────────────────────────────────────
    ("L.1.1.b",     "cloze",         "animals"),
    ("L.3.2.a",     "cloze",         "travel"),
    ("L.4.1.g",     "cloze",         "ocean"),
    ("L.5.1.b",     "cloze",         "movies"),
    ("L.6.1.c",     "cloze",         "technology"),

    # ── Language — multi_select ───────────────────────────────────────────────
    ("L.4.1.g",     "multi_select",  "cartoons"),
    ("L.6.1.c",     "multi_select",  "science"),

    # ── Language — mcq ───────────────────────────────────────────────────────
    ("L.1.1.b",     "mcq",           "holidays"),
    ("L.5.1.b",     "mcq",           "mythology"),

    # ── Reading — multi_select ────────────────────────────────────────────────
    ("RL.2.1",      "multi_select",  "fairy tales"),
    ("RL.5.3",      "multi_select",  "adventure"),
    ("RI.4.2",      "multi_select",  "nature"),
    ("RI.5.1",      "multi_select",  "inventions"),

    # ── Reading — ordering ────────────────────────────────────────────────────
    ("RL.3.3",      "ordering",      "animals"),
    ("RI.9-10.8",   "ordering",      "engineering"),

    # ── Reading — mcq ─────────────────────────────────────────────────────────
    ("RL.2.1",      "mcq",           "dogs"),
    ("RI.4.2",      "mcq",           "weather"),

    # ── Speaking/Listening ────────────────────────────────────────────────────
    ("SL.K.1.A",    "mcq",           "space"),
    ("SL.3.1.a",    "multi_select",  "community"),
    ("SL.5.1.a",    "mcq",           "environment"),
    ("SL.8.1.a",    "multi_select",  "global issues"),

    # ── Phonics (mcq only) ────────────────────────────────────────────────────
    ("RF.1.2.a",    "mcq",           "farm animals"),
    ("RF.2.3.a",    "mcq",           "playground"),
]

# ── Validation ────────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    passed:   bool
    failures: list = field(default_factory=list)   # blocking errors
    warnings: list = field(default_factory=list)   # non-fatal issues


def _is_parseable_number(value: str) -> bool:
    """Return True if value can be parsed as a number or math expression."""
    v = value.strip()
    if not v:
        return False
    # Try plain float first
    try:
        float(v)
        return True
    except ValueError:
        pass
    # Try fraction a/b
    if "/" in v:
        parts = v.split("/")
        if len(parts) == 2:
            try:
                float(parts[0]); float(parts[1])
                return True
            except ValueError:
                pass
    # Try sympy if available
    try:
        import sympy
        sympy.sympify(v, evaluate=False)
        return True
    except Exception:
        pass
    return False


def _has_format_disclosure(text: str) -> bool:
    """Check if text contains a format disclosure for student input."""
    patterns = [
        # numeric_input disclosures
        r"e\.g\.", r"for example", r"express your answer",
        r"enter\b", r"write your answer",
        r"acceptable", r"format:", r"as a fraction", r"as a decimal",
        r"as a whole number", r"round", r"simplest form",
        # cloze disclosures
        r"\btype\b", r"\bspell\b", r"\bfill\b", r"\bfill in\b",
        r"one word", r"per blank", r"each blank", r"spelling counts",
        r"punctuation mark",
    ]
    import re
    combined = "|".join(patterns)
    return bool(re.search(combined, text, re.IGNORECASE))


# Visual-reference patterns that indicate missing images
_VISUAL_PATTERNS = [
    r"\bshaded\b",
    r"\bshading\b",
    r"\bfigure below\b",
    r"\bdiagram below\b",
    r"\bpicture below\b",
    r"\bimage below\b",
    r"\bas shown\b",
    r"\bshown below\b",
    r"\blook at the\b",
    r"\buse the (figure|diagram|picture|image|model|graph|chart|table)\b",
    r"\bin the (figure|diagram|picture|image|model)\b",
    r"\bthe (figure|diagram|picture|image|model) (shows?|below|above|represents?)\b",
    r"\beach rectangle below\b",
    r"\beach shape below\b",
    r"\bnumber line below\b",
    r"\bcoordinate plane\b",
    r"\bdot (array|plot)\b",
    r"\barea model\b",
    r"\bfraction (bar|strip|model)\b",
    r"\bthe graph (shows?|below|above)\b",
    r"\bthe table below\b",
    r"\bthe model (shows?|below|above|represents?)\b",
    r"\bbelow (shows?|represents?|illustrates?)\b",
    r"\bthe following (figure|diagram|picture|image)\b",
]


def _has_visual_reference(text: str) -> bool:
    """Return True if the text references a visual element that doesn't exist in the app."""
    import re
    for pattern in _VISUAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def validate_structure(structured: dict, question_type: str) -> ValidationResult:
    """
    Validate the structural integrity of a parsed problem.
    Returns a ValidationResult with any failures (blocking) and warnings (advisory).
    """
    failures = []
    warnings = []
    p = structured  # shorthand

    problem     = p.get("problem", "").strip()
    choices     = p.get("choices", {})
    answer      = p.get("answer", "").strip()
    explanation = p.get("explanation", "").strip()
    correct     = p.get("correct", "").strip()
    order       = p.get("order", "").strip()

    # ── Shared checks ─────────────────────────────────────────────────────────
    if not problem:
        failures.append("PROBLEM field is empty or missing")
    if not explanation:
        warnings.append("EXPLANATION field is empty or missing")

    # ── Visual reference check (blocking — app has no images) ─────────────────
    # Check problem text and all choices for visual references
    full_text = problem + " " + " ".join(choices.values())
    if _has_visual_reference(full_text):
        import re as _re
        matched = next(
            (pat for pat in _VISUAL_PATTERNS
             if _re.search(pat, full_text, _re.IGNORECASE)),
            "unknown pattern"
        )
        failures.append(
            f"Problem references a visual element that does not exist in the app "
            f"(matched: '{matched}'). Rewrite without images or diagrams."
        )

    # ── Per-type checks ───────────────────────────────────────────────────────
    if question_type == "mcq":
        for letter in "ABCD":
            if letter not in choices:
                failures.append(f"Missing choice {letter})")
        if not answer:
            failures.append("ANSWER field is empty")
        elif answer.upper() not in "ABCD" or len(answer.strip()) != 1:
            failures.append(f"ANSWER '{answer}' is not a single letter A–D")
        elif answer.upper() not in choices:
            failures.append(f"ANSWER key '{answer.upper()}' not found in choices")

    elif question_type == "numeric_input":
        if not answer:
            failures.append("ANSWER field is empty")
        elif not _is_parseable_number(answer):
            warnings.append(f"ANSWER '{answer}' may not be a parseable number "
                            f"(verify manually)")
        if problem and not _has_format_disclosure(problem):
            warnings.append("No format disclosure found in problem stem "
                            "(student may not know how to format their answer)")

    elif question_type == "cloze":
        import re as _re
        blank_count = len(_re.findall(r"\{\{BLANK\}\}", problem, _re.IGNORECASE))
        if blank_count == 0:
            failures.append("No {{BLANK}} tokens found in PROBLEM stem")
        if not answer:
            failures.append("ANSWER field is empty (expected pipe-separated fills)")
        else:
            fills = [f.strip() for f in answer.split("|")]
            fill_count = len(fills)
            if blank_count > 0 and fill_count != blank_count:
                failures.append(
                    f"Blank count mismatch: {blank_count} {{{{BLANK}}}} in stem "
                    f"but {fill_count} fill(s) in ANSWER"
                )
            if any(not f for f in fills):
                failures.append("One or more fills in ANSWER are empty")
        if problem and not _has_format_disclosure(problem):
            warnings.append("No format disclosure found in problem stem")

    elif question_type == "multi_select":
        if not correct:
            failures.append("CORRECT field is empty or missing")
        else:
            correct_keys = [k.strip().upper() for k in correct.split(",") if k.strip()]
            if len(correct_keys) < 2:
                failures.append(
                    f"CORRECT has only {len(correct_keys)} key(s); "
                    f"multi_select requires at least 2 correct answers"
                )
            invalid = [k for k in correct_keys if k not in choices]
            if invalid:
                failures.append(
                    f"CORRECT key(s) {invalid} not found in choices — "
                    f"answer is unreachable"
                )
        if len(choices) < 4:
            failures.append(
                f"Only {len(choices)} choice(s) found; expected at least 4"
            )
        import re as _re
        if problem and not _re.search(r"select all|which of the following",
                                      problem, _re.IGNORECASE):
            warnings.append('Problem does not contain "Select all that apply" '
                            'or "Which of the following"')

    elif question_type == "ordering":
        if not order:
            failures.append("ORDER field is empty or missing")
        else:
            order_keys = [k.strip().upper() for k in order.split(",") if k.strip()]
            expected   = sorted(choices.keys()) if choices else list("ABCD")
            if sorted(order_keys) != sorted(expected):
                failures.append(
                    f"ORDER keys {order_keys} are not a permutation of "
                    f"choices {list(expected)}"
                )
            elif len(order_keys) != len(set(order_keys)):
                failures.append(f"ORDER contains duplicate keys: {order_keys}")
            # Warn if items appear to already be in correct order
            if order_keys == expected:
                warnings.append(
                    "ORDER matches alphabetical choice order — items may not "
                    "be properly shuffled"
                )
        if len(choices) != 4:
            failures.append(
                f"Ordering expects exactly 4 choices; found {len(choices)}"
            )
        import re as _re
        if problem and not _re.search(
            r"order|sequence|arrange|drag|first to last|correct order",
            problem, _re.IGNORECASE
        ):
            warnings.append('Problem does not contain sequencing language '
                            '("order", "arrange", "sequence", etc.)')

    return ValidationResult(
        passed   = len(failures) == 0,
        failures = failures,
        warnings = warnings,
    )

# ── Test runner ────────────────────────────────────────────────────────────────

@dataclass
class TestResult:
    standard:      str
    question_type: str
    interests:     str
    passed:        bool
    failures:      list
    warnings:      list
    elapsed_s:     float
    tokens:        dict
    raw_text:      str
    structured:    dict
    error:         str = ""   # set if generation itself failed


def run_single_test(
    standard:      str,
    interests:     str,
    question_type: str,
    port:          int   = DEFAULT_PORT,
    model:         str   = DEFAULT_MODEL,
    max_attempts:  int   = 2,
) -> TestResult:
    """Generate one problem and validate it. Retries once on empty/truncated output."""
    t_start = time.time()
    tokens  = {}

    std_norm = normalize_standard(standard)
    std_file = find_by_standard_file(std_norm)
    if not std_file:
        return TestResult(
            standard=std_norm, question_type=question_type,
            interests=interests, passed=False,
            failures=[f"Standard file not found for '{std_norm}'"],
            warnings=[], elapsed_s=time.time() - t_start,
            tokens={}, raw_text="", structured={},
            error="standard_not_found",
        )

    context  = load_standard_context(std_file)
    use_http = server_is_running(port) and REQUESTS_AVAILABLE

    last_result = None
    for attempt in range(1, max_attempts + 1):
        previous = load_previous_problems(std_norm)
        prompt   = build_prompt(std_norm, interests, context,
                                previous_problems=previous or None,
                                question_type=question_type)
        try:
            if use_http:
                raw_text, tokens, timing = run_testy_agent_http(prompt, port, model)
            else:
                raw_text, tokens, timing = run_testy_agent_subprocess(prompt, model)
        except Exception as exc:
            return TestResult(
                standard=std_norm, question_type=question_type,
                interests=interests, passed=False,
                failures=[f"Generation failed: {exc}"],
                warnings=[], elapsed_s=time.time() - t_start,
                tokens={}, raw_text="", structured={},
                error="generation_error",
            )

        if not raw_text.strip():
            last_result = TestResult(
                standard=std_norm, question_type=question_type,
                interests=interests, passed=False,
                failures=["Agent returned empty response"],
                warnings=[], elapsed_s=time.time() - t_start,
                tokens=tokens, raw_text="", structured={},
                error="empty_response",
            )
            if attempt < max_attempts:
                continue
            return last_result

        structured = extract_structured_output(raw_text)
        validation = validate_structure(structured, question_type)
        elapsed    = time.time() - t_start

        result = TestResult(
            standard=std_norm,
            question_type=question_type,
            interests=interests,
            passed=validation.passed,
            failures=validation.failures,
            warnings=validation.warnings,
            elapsed_s=elapsed,
            tokens=tokens,
            raw_text=raw_text,
            structured=structured,
        )

        if result.passed:
            return result

        # Check if the failure looks like a model truncation (very fast + missing fields)
        # Retry once in that case
        truncation_failures = {"PROBLEM field is empty or missing",
                               "ANSWER field is empty",
                               "CORRECT field is empty or missing",
                               "ORDER field is empty or missing"}
        is_truncation = any(f in truncation_failures for f in result.failures)
        if is_truncation and attempt < max_attempts:
            result.warnings.append(f"Attempt {attempt} truncated — retrying...")
            last_result = result
            continue

        return result

    return last_result

# ── Reporting ─────────────────────────────────────────────────────────────────

def format_report(
    results:    list,
    model:      str,
    verbose:    bool = False,
    fail_only:  bool = False,
) -> str:
    total    = len(results)
    passed   = sum(1 for r in results if r.passed)
    failed   = total - passed
    warnings = sum(len(r.warnings) for r in results)
    elapsed  = sum(r.elapsed_s for r in results)

    # Per-type stats
    type_stats: dict = {}
    for r in results:
        t = r.question_type
        if t not in type_stats:
            type_stats[t] = {"pass": 0, "total": 0}
        type_stats[t]["total"] += 1
        if r.passed:
            type_stats[t]["pass"] += 1

    # Per-subject stats
    subj_stats: dict = {}
    for r in results:
        s = subject_category(r.standard)
        if s not in subj_stats:
            subj_stats[s] = {"pass": 0, "total": 0}
        subj_stats[s]["total"] += 1
        if r.passed:
            subj_stats[s]["pass"] += 1

    lines = []
    lines.append("=" * 56)
    lines.append("  TESTY GRADER — Batch Test Report")
    lines.append(f"  Run at : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  Model  : {model}")
    lines.append("=" * 56)
    lines.append("")
    lines.append("SUMMARY")
    lines.append(f"  Tests run   : {total}")
    lines.append(f"  Passed      : {passed}  ({passed/total*100:.1f}%)")
    lines.append(f"  Failed      : {failed}  ({failed/total*100:.1f}%)")
    lines.append(f"  Warnings    : {warnings}")
    m, s = divmod(int(elapsed), 60)
    lines.append(f"  Total time  : {m}m {s}s")
    lines.append("")

    lines.append("BY TYPE")
    for t in ["mcq", "numeric_input", "cloze", "multi_select", "ordering"]:
        if t in type_stats:
            st = type_stats[t]
            pct = st["pass"] / st["total"] * 100
            bar = "✓" if st["pass"] == st["total"] else "✗"
            lines.append(
                f"  {bar}  {t:<16}  {st['pass']}/{st['total']}  ({pct:.1f}%)"
            )
    lines.append("")

    lines.append("BY SUBJECT")
    for s in ["math", "language", "reading", "sl", "phonics"]:
        if s in subj_stats:
            st = subj_stats[s]
            pct = st["pass"] / st["total"] * 100
            bar = "✓" if st["pass"] == st["total"] else "✗"
            lines.append(
                f"  {bar}  {s:<12}  {st['pass']}/{st['total']}  ({pct:.1f}%)"
            )
    lines.append("")

    # Failures section
    failures_list = [r for r in results if not r.passed]
    if failures_list:
        lines.append(f"FAILURES ({len(failures_list)})")
        for r in failures_list:
            lines.append(f"  ✗  {r.standard} / {r.question_type}"
                         f"  ({r.elapsed_s:.1f}s)")
            for f in r.failures:
                lines.append(f"       • {f}")
            if verbose and r.raw_text:
                lines.append("     Raw output (first 400 chars):")
                snippet = r.raw_text[:400].replace("\n", "\n       ")
                lines.append(f"       {snippet}")
        lines.append("")

    # Warnings section
    warnings_list = [(r, w) for r in results for w in r.warnings]
    if warnings_list:
        lines.append(f"WARNINGS ({len(warnings_list)})")
        for r, w in warnings_list:
            lines.append(f"  ⚠  {r.standard} / {r.question_type}  —  {w}")
        lines.append("")

    # Verbose: show all passing problems too
    if verbose and not fail_only:
        passing = [r for r in results if r.passed]
        if passing:
            lines.append(f"PASSED PROBLEMS ({len(passing)})")
            for r in passing:
                lines.append("-" * 56)
                lines.append(f"  {r.standard} / {r.question_type}  ({r.elapsed_s:.1f}s)")
                if r.structured.get("problem"):
                    for ln in r.structured["problem"].splitlines():
                        lines.append(f"  {ln}")
                if r.structured.get("choices"):
                    for letter in "ABCDE":
                        if letter in r.structured["choices"]:
                            lines.append(f"  {letter}) {r.structured['choices'][letter]}")
                if r.structured.get("answer"):
                    lines.append(f"  ANSWER: {r.structured['answer']}")
                if r.structured.get("correct"):
                    lines.append(f"  CORRECT: {r.structured['correct']}")
                if r.structured.get("order"):
                    lines.append(f"  ORDER: {r.structured['order']}")
                if r.structured.get("explanation"):
                    lines.append(f"  EXPLANATION: {r.structured['explanation']}")
            lines.append("")

    approved_count = sum(1 for r in results if r.passed)
    lines.append(f"APPROVED: {approved_count} problem(s) ready to save")
    lines.append("=" * 56)

    return "\n".join(lines)


# ── Approved file writer ───────────────────────────────────────────────────────

def save_approved(results: list, output_path: Path) -> int:
    """
    Write all passing problems to output_path in JSONL format.
    Returns the number of records written.
    Each record mirrors what the web app needs:
      question_mode, problem_text, standard, interests,
      answer / fills / correct_keys / order_keys, explanation.
    """
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(output_path, "a", encoding="utf-8") as f:
        for r in results:
            if not r.passed:
                continue
            s = r.structured
            choices = s.get("choices", {})
            problem_text = s.get("problem", "").strip()

            # Reconstruct the problem as presented to the student
            if choices and r.question_type in ("mcq", "multi_select", "ordering"):
                choices_block = "\n".join(
                    f"{letter}) {text}"
                    for letter, text in sorted(choices.items())
                )
                problem_text = f"{problem_text}\n{choices_block}"

            record: dict = {
                "standard":      r.standard,
                "question_mode": r.question_type,
                "interests":     r.interests,
                "problem_text":  problem_text,
                "skill":         s.get("skill", ""),
                "grade":         s.get("grade", ""),
                "explanation":   s.get("explanation", ""),
                "generated_at":  datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "elapsed_s":     round(r.elapsed_s, 1),
                "tokens":        r.tokens,
            }

            # Type-specific answer storage
            qt = r.question_type
            if qt in ("mcq", "numeric_input"):
                record["answer"] = s.get("answer", "")

            elif qt == "cloze":
                raw = s.get("answer", "")
                record["fills"]  = [f.strip() for f in raw.split("|") if f.strip()]
                record["answer"] = raw

            elif qt == "multi_select":
                raw = s.get("correct", "")
                record["correct_keys"] = [
                    k.strip().upper() for k in raw.split(",") if k.strip()
                ]
                record["answer"] = raw

            elif qt == "ordering":
                raw = s.get("order", "")
                record["order_keys"] = [
                    k.strip().upper() for k in raw.split(",") if k.strip()
                ]
                record["answer"] = raw

            f.write(json.dumps(record) + "\n")
            count += 1

    return count


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="testy_grader — batch test CCSS problem generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  testy_grader.py                          # run built-in suite\n"
            "  testy_grader.py --types numeric_input,cloze\n"
            "  testy_grader.py --standards 5.NF.A.1,L.4.1.g\n"
            "  testy_grader.py --verbose --fail-only\n"
            "  testy_grader.py --start-server --output scratch/my_approved.jsonl"
        ),
    )
    parser.add_argument("--standards", metavar="S1,S2,...",
                        help="Comma-separated standards (default: built-in suite)")
    parser.add_argument("--types", metavar="T1,T2,...",
                        help="Comma-separated types to test (default: per-suite)")
    parser.add_argument("--interests", default=None, metavar="INTERESTS",
                        help="Override interests for all tests (default: per-suite)")
    parser.add_argument("--port",  type=int, default=DEFAULT_PORT)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output", default=str(APPROVED_FILE), metavar="PATH",
                        help=f"Approved problems output file (default: {APPROVED_FILE.name})")
    parser.add_argument("--verbose",    action="store_true",
                        help="Print full problem text for all results")
    parser.add_argument("--fail-only",  action="store_true",
                        help="Print only failures and warnings")
    parser.add_argument("--no-save",    action="store_true",
                        help="Do not write approved problems to file")
    parser.add_argument("--start-server", action="store_true",
                        help="Start OpenCode server before running tests")

    args = parser.parse_args()

    # ── Optional server start ──────────────────────────────────────────────────
    if args.start_server:
        ok = start_server(args.port)
        if not ok:
            print("[ERROR] Could not start OpenCode server.", file=sys.stderr)
            sys.exit(1)

    # ── Build test cases ───────────────────────────────────────────────────────
    type_filter = (
        [t.strip() for t in args.types.split(",") if t.strip()]
        if args.types else None
    )

    if args.standards:
        # User-specified standards: test each with each requested type (or all eligible)
        std_list = [s.strip() for s in args.standards.split(",") if s.strip()]
        test_cases = []
        for std in std_list:
            std_norm = normalize_standard(std)
            cat      = subject_category(std_norm)
            eligible = ELIGIBLE_MODES[cat]
            types    = type_filter if type_filter else eligible
            for t in types:
                if t in eligible:
                    test_cases.append((
                        std_norm,
                        t,
                        args.interests or "space exploration",
                    ))
    else:
        # Built-in suite, optionally filtered by type
        test_cases = [
            (std, qt, args.interests or interests)
            for std, qt, interests in TEST_SUITE
            if (type_filter is None or qt in type_filter)
        ]

    if not test_cases:
        print("[ERROR] No test cases to run. Check --standards and --types.",
              file=sys.stderr)
        sys.exit(1)

    total = len(test_cases)
    use_http = server_is_running(args.port) and REQUESTS_AVAILABLE
    mode_str = f"server (:{args.port})" if use_http else "subprocess"
    print(f"[testy_grader] {total} test(s) | model: {args.model} | mode: {mode_str}")
    print()

    # ── Run tests sequentially ─────────────────────────────────────────────────
    results = []
    for i, (std, qt, interests) in enumerate(test_cases, 1):
        prefix = f"[{i:>2}/{total}] {std:<18} {qt:<16}"
        print(f"{prefix} generating...", end="", flush=True)

        result = run_single_test(std, interests, qt, args.port, args.model)
        results.append(result)

        status = "✓" if result.passed else "✗"
        warn   = f"  ⚠ {len(result.warnings)} warning(s)" if result.warnings else ""
        print(f"\r{prefix} {status}  {result.elapsed_s:.1f}s{warn}")

        if not result.passed and not args.fail_only:
            for f in result.failures:
                print(f"             • {f}")

    print()

    # ── Report ─────────────────────────────────────────────────────────────────
    report = format_report(results, args.model,
                           verbose=args.verbose,
                           fail_only=args.fail_only)
    print(report)

    # ── Save approved ──────────────────────────────────────────────────────────
    if not args.no_save:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        n = save_approved(results, out_path)
        print(f"[testy_grader] {n} approved problem(s) appended to: {out_path}")

    # Exit non-zero if any failures
    failed = sum(1 for r in results if not r.passed)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
