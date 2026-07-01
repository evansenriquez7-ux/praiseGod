# 5-Phase Audit Bug-Fix Plan: Final Results

**Date:** July 1, 2026
**Scope:** All bugs surfaced by the v-final exhaustive checklist audit (102 nodes with violations, 40,047 total violations).

## Summary

After executing the 5-phase plan, the audit reports **83 nodes with violations** (down 19%) and **32,668 total violations** (down 18%). The two highest-impact wins were Phase 1 (semantic-leak audit carve-outs) and Phase 4 (fractions DNA override, which turned out to be 2 bugs).

## Final v3 → v-final table

| Category | v3 | v7 | v-final (pre-plan) | After 5-phase plan | Total reduction |
|---|---|---|---|---|---|
| Pipeline Crash | 13,476 | 5,216 | 28,830 (includes RuntimeErrors from fix) | 28,830 | unchanged (by-design) |
| Semantic Leak | 38,652 | 25,148 | 10,015 | 3,716 | **-63%** |
| Fractions DNA override | 1,080 | 1,080 | 1,080 | **0** | **-100%** |
| Formatter Fallback (sort_order) | 1,370 | 2,170 | 0 (fixed in v7) | 0 | -100% |
| Vocabulary Violation | 8,370 | 0 | 0 (fixed) | 0 | -100% |
| Visual Degradation | 16,766 | 17,046 | 0 (fixed in v7) | 0 | -100% |
| Strict Scalar Endpoint | 88,126 | 2,560 | 0 (fixed in v7) | 0 | -100% |
| Scale Appropriateness | 0 | 648 | 0 (fixed in v7) | 0 | -100% |
| Separation of Concerns | 29 | 14 | 14 | 14 | unchanged (deferred) |
| Variant/Dim never exercised | 5 | 7 | 7 | 7 | unchanged (deferred) |
| Formatter mismatch | — | — | 44 | 44 | unchanged (deferred) |
| **Audit wall-clock** | ~5.8h | ~5.8h | ~40 min (4 workers) | ~40 min | -92% |
| **Nodes with violations** | — | 113 | 102 | **83** | -27% |
| **Total violations** | — | 33,510 | 40,047 | 32,668 | -18% |

## Key wins from this session

### Phase 1 (commit `d511701`): Audit filter carve-outs

Added `PROMPT_TARGET_STEM_PATTERNS` (8 regex templates) for stem templates where the answer is in the stem by design:
- "Use coins and bills to make exactly ₱N" (money prompt, 2,500 false positives)
- "What is N × N?" / "N × N = ___" / "N × ___ = N" (single-digit arithmetic, 2,803 false positives)
- "What is the value of the digit X in Y?" (place value, 64 false positives)
- "The number N is written in words as ___" (number-to-words, 200+ false positives)
- "Round N to the nearest N" (rounding, 28 false positives)
- "Which is heavier/lighter/longer/...: N g or N g?" (comparing measurement, 320 false positives)
- "What number comes after N when counting by N?" (counting, 28 false positives)

Each carve-out is per-template (compiled regex) rather than per-formatter — narrower exception, easier to audit.

**Cut Semantic Leak: 10,015 → 5,367 (-46%).** 46 unit tests in `test_semantic_leak_carveouts.py`.

### Phase 2: Addition DNA fail-fast fix — N/A

The `addition.py` DNA was already raising `RuntimeError` for impossible profiles. The 5,720 addition Pipeline Crashes are the correct fail-fast behavior (same as the 21,840 subtraction ones). No code change needed.

### Phase 3 (commit `4ebad31`): emoji_pictorial numeric limit

Moved the `max_val > 100` check from `backend/app/practice_gen/adapter.py` (where it was a hard-coded special case for `emoji_pictorial`) into `format_emoji_pictorial()` in `backend/app/practice_gen/formatters/visual/fmt_emoji_pictorial.py`, where the formatter owns its own numeric constraints.

All 1,270 emoji_pictorial crashes now use the new, more informative error message: "cannot represent max_val (N) > 100; this profile produces a group too large for emoji display."

5 unit tests in `test_emoji_pictorial_max_val.py`.

### Phase 4 (commit `ed60b22`): Fractions DNA task-type guard (was 2 bugs)

The plan called for a single fix to the `fractions` DNA, but the actual root cause was TWO bugs:

1. **`FormattedProblem.dna_name: Optional[str] = None` field was missing.** The Phase 1A commit `a94d30c` was supposed to add this field to `backend/app/practice_gen/dna/base.py`, but the field was never actually committed (probably a partial merge). The orchestrator's `dna_name = rng.choice(valid_dnas)` was a local variable that never propagated to the problem.

2. **The audit's `formatter_supports_profile()` returned True when `FORMATTER_VARIANT_SUPPORT[dna_name][formatter]` had no entry.** This meant the audit would request (fractions, ordering) combinations the orchestrator would reject at runtime. The fix added a Gate 1 check that mirrors `orchestrator.py:125`'s `formatter not in available_for_d` filter.

3. **The orchestrator now sets `problem.dna_name = dna_name`** after picking the DNA, so the audit's per-DNA content checks work correctly.

**Fractions DNA override: 1,080 → 0 (-100%).** 10 unit tests in `test_formatter_supports_profile.py`.

### Phase 5 (commit `3f984d1`): Semantic Leak standalone-number check

Changed the audit's semantic-leak regex from `\\bN\\b` to `(?<!\\d)N(?!\\d)` so that the answer digit only matches when it is a standalone number in the stem, not a digit within a multi-digit number (e.g. the blank "1___" in "Mika has 1___ pencils. Gives away 10. How many left?" with answer=2 — the `2` is part of `12` (the blank), not a standalone operand).

8 new unit tests for the standalone-number check. **Cut Semantic Leak: 5,367 → 3,716 (-31%).**

## Remaining work (deferred to future sessions)

- **Pipeline Crash 28,830:** dominated by the subtraction/addition fix's RuntimeErrors. These are by-design (impossible profiles). The orchestrator could pre-filter them, but per AGENTS.md rule #4, the fail-fast DNA behavior is the correct architecture.
- **Semantic Leak 3,716:** remaining cases are operand-equal bugs (e.g. "There are 3 X. Takes away 2. How many left?" where answer=2 is a standalone subtrahend). Requires deeper DNA-level operand-guard work.
- **Formatter mismatch (44):** 6 nodes with mismatched formatter lists. Small config fix.
- **Separation of Concerns (14):** real but low-volume; may require re-architecting how word-problem wrappers work.
- **Variant/Dim never exercised (7):** real config bug, 1-2 hours of investigation.

## Lessons learned (for future agents)

1. **Always verify a fix is actually applied.** Phase 2 was a no-op because the addition.py DNA was already fixed; the plan didn't verify this beforehand. The "before" baseline of 5,720 addition Pipeline Crashes was actually the *correct* behavior.

2. **A "single fix" can be 2-3 bugs in disguise.** Phase 4 was originally planned as a single DNA guard, but the actual fix was 3 changes (dna_name field, formatter filter, orchestrator annotation). Drilling into the error message ("Fractions DNA concept overridden") revealed the dna_name fallback was the proximate cause, not the DNA itself.

3. **Pydantic models don't allow setting attributes not declared in the model.** The orchestrator was trying to set `problem.dna_name = dna_name` but the field didn't exist on the model, so the assignment silently failed. The `try/except` around it hid the error. The fix was to add the field to the model.

4. **Audit filters must mirror the orchestrator's runtime filter exactly (Lesson 4 in `docs/generator_testing_strategy.md`).** The `formatter_supports_profile` function had been passing the `caps is None -> True` case, which allowed the audit to request combinations the orchestrator would reject. This is a 1:1 mirror contract.

5. **Word boundaries (`\b`) are insufficient for matching standalone numbers.** The previous pattern `\bN\b` matched the `2` in `12` because the right side is a word boundary. The fix uses negative lookbehind/lookahead: `(?<!\d)N(?!\d)`.

6. **Fail-fast > silent default (AGENTS.md rule #4).** All fixes in this session follow fail-fast: RuntimeError for impossible profiles, ValueError for over-large values, assert for missing fields. The audit catches the failures and reports them — which is the correct outcome.
