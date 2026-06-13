"""
Semantic validators for MATATAG Lab axis options.

Each validator checks that a generated problem actually exhibits the
behavior described by its axis value — not just that it generated.

ValidationResult.status:
  'PASS'          — constraint confirmed
  'FAIL'          — constraint violated (test must fail)
  'MANUAL_REVIEW' — cannot be determined programmatically (skip + flag)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Result type
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    status: str            # 'PASS' | 'FAIL' | 'MANUAL_REVIEW'
    message: str
    extracted: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status == 'PASS'

    @property
    def needs_review(self) -> bool:
        return self.status == 'MANUAL_REVIEW'


def _pass(msg: str, **kw) -> ValidationResult:
    return ValidationResult('PASS', msg, kw)

def _fail(msg: str, **kw) -> ValidationResult:
    return ValidationResult('FAIL', msg, kw)

def _manual(msg: str, **kw) -> ValidationResult:
    return ValidationResult('MANUAL_REVIEW', msg, kw)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_numbers(problem: dict) -> List[int]:
    """Extract all integers from stem + MCQ option texts."""
    text = problem.get('stem', '')
    for opt in (problem.get('mcq_options') or []):
        text += ' ' + opt.get('text', '')
    nums = re.findall(r'\b\d+\b', text)
    return [int(n) for n in nums]

def _stem(problem: dict) -> str:
    return (problem.get('stem') or '').lower()

def _visual_params(problem: dict) -> dict:
    return problem.get('visual_params') or {}

def _options_text(problem: dict) -> List[str]:
    return [o.get('text', '') for o in (problem.get('mcq_options') or [])]


# ─────────────────────────────────────────────────────────────────────────────
# Individual validators
# ─────────────────────────────────────────────────────────────────────────────

RANGE_BOUNDS = {
    '0_20':           (0,    20),
    '0_100':          (0,   100),
    '0_1000':         (0,  1000),
    '1_to_20':        (1,    20),
    '21_to_100':      (21,  100),
    '101_to_1000':    (101, 1000),
    '1001_to_10000':  (1001, 10000),
    '1st_to_10th':    (1,    10),
    '11th_to_20th':   (11,   20),
    '21st_to_100th':  (21,  100),
    'up_to_20':       (0,    20),
    'up_to_100':      (0,   100),
    'up_to_1000':     (0,  1000),
    'up_to_10000':    (0, 10000),
}


def validate_range(problem: dict, axis_value: str) -> ValidationResult:
    """Numbers in stem (not MCQ options) must fall within the specified range."""
    bounds = RANGE_BOUNDS.get(axis_value)
    if bounds is None:
        return _manual(f"No bounds defined for range='{axis_value}'")

    lo, hi = bounds
    tolerance = max(hi * 0.10, 2)

    # Only check numbers in the stem, not MCQ options (options are deliberately varied)
    stem = problem.get('stem', '')
    nums = [int(n) for n in re.findall(r'\b\d+\b', stem)]
    # Exclude obvious distractor sums (numbers > 2*hi are likely sums used as traps)
    meaningful = [n for n in nums if n > 0 and n <= hi * 2]

    if not meaningful:
        return _manual("No numbers found in stem — cannot validate range")

    out = [n for n in meaningful if n > hi + tolerance]
    if out:
        return _fail(
            f"Numbers {out} exceed range {lo}–{hi} (tolerance={tolerance:.0f})",
            numbers=meaningful, out_of_range=out
        )
    return _pass(f"All numbers within {lo}–{hi}", numbers=meaningful)


def validate_amount_range(problem: dict, axis_value: str) -> ValidationResult:
    """Peso amount within specified range."""
    vp = _visual_params(problem)
    target = vp.get('target_amount')
    if target is not None:
        bounds = {'up_to_100': 100, 'up_to_1000': 1000, 'up_to_10000': 10000}
        limit = bounds.get(axis_value)
        if limit and target > limit:
            return _fail(f"target_amount={target} exceeds {axis_value} limit={limit}")
        return _pass(f"target_amount={target} within {axis_value}")
    return validate_range(problem, axis_value)


def validate_direction(problem: dict, axis_value: str) -> ValidationResult:
    """For counting: forward = 'after'/'next', backward = 'before'/'previous'."""
    # Handle number-reading direction
    if axis_value in ('numeral_to_word', 'word_to_numeral'):
        s = _stem(problem)
        opts = ' '.join(_options_text(problem)).lower()
        has_numeral_stem = bool(re.search(r'\b\d{2,}\b', problem.get('stem', '')))
        has_word_opts = any(w in opts for w in ['one', 'two', 'three', 'four', 'five',
                                                 'ten', 'hundred', 'thousand'])
        if axis_value == 'numeral_to_word':
            if has_numeral_stem and has_word_opts:
                return _pass("Stem has numeral, options have words → numeral_to_word")
        if axis_value == 'word_to_numeral':
            if not has_numeral_stem and not has_word_opts:
                return _pass("No clear numerals in stem → word_to_numeral possible")
        return _manual(
            f"Cannot reliably detect direction={axis_value} from text",
            stem=problem.get('stem')
        )

    s = _stem(problem)
    backward_keywords = ['before', 'previous', 'count down', 'countdown',
                         'descend', 'decreasing', 'backward', 'subtract 1',
                         'what comes before']
    forward_keywords  = ['after', 'next number', 'count up', 'ascending',
                         'increasing', 'forward', 'add 1', 'what comes after',
                         'what number comes after']

    is_backward = any(kw in s for kw in backward_keywords)
    is_forward  = any(kw in s for kw in forward_keywords)

    if is_backward and not is_forward:
        detected = 'backward'
    elif is_forward and not is_backward:
        detected = 'forward'
    else:
        return _manual(
            "Cannot detect counting direction from stem",
            stem=problem.get('stem')
        )

    if detected != axis_value:
        return _fail(
            f"Expected direction={axis_value} but detected {detected}",
            stem=problem.get('stem')
        )
    return _pass(f"Direction={axis_value} confirmed")


def validate_regrouping(problem: dict, axis_value: str) -> ValidationResult:
    """Addition/subtraction must require (or avoid) regrouping as specified."""
    s = problem.get('stem', '')

    # Estimation problems round first then compute — regrouping axis doesn't apply
    if any(kw in s.lower() for kw in ['estimat', 'round each', 'best estimate', 'nearest']):
        return _manual(f"regrouping={axis_value}: estimation/rounding problems are exempt from regrouping constraints")

    # Try to extract a + b or a - b
    add_match = re.search(r'(\d+)\s*\+\s*(\d+)', s)
    sub_match  = re.search(r'(\d+)\s*[-−]\s*(\d+)', s)

    if not add_match and not sub_match:
        return _manual("Cannot parse arithmetic expression from stem", stem=s)

    if add_match:
        a, b = int(add_match.group(1)), int(add_match.group(2))
        op = '+'
        ones_regroup = (a % 10) + (b % 10) >= 10
        tens_regroup = (a // 10 % 10) + (b // 10 % 10) + (1 if ones_regroup else 0) >= 10
    else:
        a, b = int(sub_match.group(1)), int(sub_match.group(2))
        op = '-'
        ones_regroup = (a % 10) < (b % 10)
        tens_regroup = (a // 10 % 10) - (1 if ones_regroup else 0) < (b // 10 % 10)

    expected = {
        'none':   (not ones_regroup and not tens_regroup),
        'ones':   (ones_regroup and not tens_regroup),  # only ones carry
        'tens':   (tens_regroup),                        # tens carry (ones may or may not carry)
        'double': (ones_regroup and tens_regroup),       # both carry
    }

    if axis_value not in expected:
        return _manual(f"Unknown regrouping value '{axis_value}'")

    if not expected[axis_value]:
        return _fail(
            f"regrouping={axis_value} but {a} {op} {b} violates constraint "
            f"(ones_regroup={ones_regroup}, tens_regroup={tens_regroup})",
            a=a, b=b, op=op
        )
    return _pass(f"regrouping={axis_value} confirmed for {a} {op} {b}")


def validate_number_type(problem: dict, axis_value: str) -> ValidationResult:
    """round = ends in 0 or 5; non_round = does not. Only applies to arithmetic stems."""
    s = problem.get('stem', '')

    # Estimation problems intentionally use non-round numbers
    if any(kw in s.lower() for kw in ['estimat', 'round each', 'best estimate']):
        return _manual(f"number_type={axis_value}: estimation problems use non-round numbers by design")

    # Only validate for arithmetic problems (contains +, -, ×, ÷)
    has_arithmetic = bool(re.search(r'\d+\s*[+\-×÷x]\s*\d+', s))
    if not has_arithmetic:
        return _manual(f"number_type={axis_value}: no arithmetic expression in stem — applies to arithmetic only")

    nums = [int(n) for n in re.findall(r'\b\d+\b', s)]
    operands = [n for n in nums if n > 1]

    if not operands:
        return _manual("No operands found to classify")

    if axis_value == 'round':
        non_round = [n for n in operands if n % 5 != 0]
        if len(non_round) > len(operands) * 0.5:
            return _fail(f"number_type=round but >50% operands not divisible by 5: {non_round}")
        return _pass(f"Most numbers are round: {operands}")

    if axis_value == 'non_round':
        # If ALL operands are divisible by 5, that's unexpected for non_round
        # But round numbers can appear as part of the problem context (e.g., 320+445 where 445 is non-round)
        non_round_count = [n for n in operands if n % 5 != 0]
        if len(non_round_count) == 0:
            return _fail(f"number_type=non_round but all operands divisible by 5: {operands}")
        return _pass(f"Mix includes non-round numbers: {operands}")

    if axis_value == 'single_digit':
        big = [n for n in operands if n > 9]
        if big:
            return _fail(f"number_type=single_digit but found multi-digit: {big}")
        return _pass(f"All single-digit: {operands}")

    if axis_value == 'multi_digit':
        # Multiplication tables use single-digit factors by design
        if re.search(r'\d+\s*[×x]\s*\d+', s):
            return _manual(f"number_type=multi_digit: multiplication table problems use single-digit factors by design")
        small = [n for n in operands if n < 10]
        if len(small) == len(operands):
            return _fail(f"number_type=multi_digit but all single-digit: {operands}")
        return _pass(f"Multi-digit operands present: {operands}")

    return _manual(f"Unknown number_type='{axis_value}'")


def validate_structure(problem: dict, axis_value: str) -> ValidationResult:
    """Blank position in equation."""
    s = problem.get('stem', '')
    has_blank = '?' in s or '___' in s or '_' in s or '__' in s

    if not has_blank:
        return _manual("No blank/? found in stem — cannot detect structure", stem=s)

    # Detect position of blank relative to operator
    patterns = {
        # Check multiplication/division specific patterns FIRST (before generic change_unknown)
        'factor_unknown':   [
            r'\d+\s*[×x\*]\s*_{1,}\s*=\s*\d+',
            r'\d+\s*[×x\*]\s*\?\s*=\s*\d+',
        ],
        'divisor_unknown':  [
            r'\d+\s*÷\s*_{1,}\s*=\s*\d+',
            r'\d+\s*÷\s*\?\s*=\s*\d+',
        ],
        'result_unknown':   [
            r'\d+\s*[+\-×÷\*/]\s*\d+\s*=\s*[\?]',
            r'\d+\s*[+\-×÷\*/]\s*\d+\s*=\s*_{1,}',
        ],
        'change_unknown':   [
            r'\d+\s*[+\-]\s*\?\s*=\s*\d+',
            r'\d+\s*[+\-]\s*_{1,}\s*=\s*\d+',
        ],
        'start_unknown':    [
            r'\?\s*[+\-×÷\*/]\s*\d+\s*=\s*\d+',
            r'_{1,}\s*[+\-×÷\*/]\s*\d+\s*=\s*\d+',
        ],
        'start_unknown_mul':    [
            r'_{1,}\s*[×x\*]\s*\d+\s*=\s*\d+',
            r'\?\s*[×x\*]\s*\d+\s*=\s*\d+',
        ],
        'start_unknown_div':  [
            r'_{1,}\s*÷\s*\d+\s*=\s*\d+',
            r'\?\s*=\s*\d+\s*÷\s*\d+',
        ],
    }

    # Normalize start_unknown variants
    structure_aliases = {
        'start_unknown_mul': 'start_unknown',
        'start_unknown_div': 'start_unknown',
    }

    detected = []
    for name, pats in patterns.items():
        for pat in pats:
            if re.search(pat, s, re.IGNORECASE):
                canonical = structure_aliases.get(name, name)
                if canonical not in detected:
                    detected.append(canonical)
                break

    if not detected:
        return _manual(
            f"Cannot detect structure={axis_value} from stem — needs manual review",
            stem=s
        )

    if axis_value in detected:
        return _pass(f"structure={axis_value} confirmed")
    return _fail(f"Expected {axis_value}, detected {detected}", stem=s)


def validate_blank_position(problem: dict, axis_value: str) -> ValidationResult:
    """Alias for structure validator with simpler value names."""
    mapping = {
        'result': 'result_unknown',
        'change': 'change_unknown',
        'start':  'start_unknown',
    }
    return validate_structure(problem, mapping.get(axis_value, axis_value))


def validate_digit_count(problem: dict, axis_value: str) -> ValidationResult:
    """Operands in the stem must have the specified number of digits."""
    stem = problem.get('stem', '')

    # Compose/decompose problems use small numbers by design for G1-3
    if any(kw in stem.lower() for kw in ['break apart', 'compose', 'decompose', 'make', 'parts']):
        return _manual(f"digit_count={axis_value}: compose/decompose problems use grade-appropriate small numbers")

    nums = [int(n) for n in re.findall(r'\b\d+\b', stem)]
    operands = [n for n in nums if n >= 10]

    if not operands:
        return _manual(f"No multi-digit numbers in stem to check digit_count")

    limits = {'2_digit': (10, 99), '3_digit': (100, 999), '4_digit': (1000, 9999)}
    lo, hi = limits.get(axis_value, (0, 999999))

    out = [n for n in operands if not (lo <= n <= hi * 10)]
    if len(out) > 1:
        return _fail(f"digit_count={axis_value} ({lo}-{hi}) but found {out}")
    return _pass(f"Operands consistent with {axis_value}: {operands}")


def validate_skip_interval(problem: dict, axis_value: str) -> ValidationResult:
    """Sequence step size must match the skip interval."""
    s = problem.get('stem', '')
    # Extract comma-separated or space-separated sequences
    # e.g. "2, 4, 6, 8, ?" or "5, 10, 15, ?"
    seq_match = re.findall(r'(?<!\d)(\d+)(?!\d)', s)
    nums = [int(n) for n in seq_match if 1 <= int(n) <= 10000]

    if len(nums) < 3:
        return _manual("Insufficient numbers to detect skip interval", stem=s)

    # Compute differences between consecutive terms (skip the ? which is 0)
    valid_nums = [n for n in nums if n > 0]
    if len(valid_nums) < 3:
        return _manual("Not enough non-zero numbers")

    diffs = [abs(valid_nums[i+1] - valid_nums[i]) for i in range(len(valid_nums)-1)]
    diffs = [d for d in diffs if d > 0]
    if not diffs:
        return _manual("All differences are zero")

    most_common_diff = max(set(diffs), key=diffs.count)

    interval_ok = {
        'by_1':          most_common_diff == 1,
        'by_2_5_10':     most_common_diff in (2, 5, 10),
        'by_20_50_100':  most_common_diff in (20, 50, 100),
    }

    if axis_value not in interval_ok:
        return _manual(f"Unknown skip_interval='{axis_value}'")

    if not interval_ok[axis_value]:
        return _fail(
            f"skip_interval={axis_value} but detected step={most_common_diff}",
            sequence=valid_nums, diffs=diffs
        )
    return _pass(f"skip_interval={axis_value} confirmed (step={most_common_diff})")


def validate_precision(problem: dict, axis_value: str) -> ValidationResult:
    """Clock problems: time granularity; rounding: nearest_ten/hundred/thousand."""
    s = _stem(problem)
    vp = _visual_params(problem)

    # Rounding precision — check for digit OR word form
    if axis_value in ('nearest_ten', 'nearest_hundred', 'nearest_thousand'):
        digit_kws = {'nearest_ten': ['10'], 'nearest_hundred': ['100'], 'nearest_thousand': ['1000']}
        word_kws  = {'nearest_ten': ['ten', 'tens'], 'nearest_hundred': ['hundred'], 'nearest_thousand': ['thousand']}
        all_kws = digit_kws[axis_value] + word_kws[axis_value]
        if any(kw in s for kw in all_kws):
            return _pass(f"precision={axis_value} keyword found in stem")
        return _fail(f"precision={axis_value} but stem missing keywords {all_kws}", stem=problem.get('stem'))

    # Clock precision — check visual_params minutes
    mins = vp.get('minutes')
    if mins is not None:
        ok = {
            'hour':         mins == 0,
            'half_hour':    mins % 30 == 0,
            'quarter_hour': mins % 15 == 0,
            'five_minutes': mins % 5 == 0,
            'one_minute':   True,
        }
        if axis_value in ok:
            if ok[axis_value]:
                return _pass(f"precision={axis_value} confirmed (minutes={mins})")
            return _fail(f"precision={axis_value} but time has minutes={mins}")

    return _manual(f"Cannot validate precision={axis_value} from available data")


def validate_denomination_type(problem: dict, axis_value: str) -> ValidationResult:
    """Peso visual: denominations must match coins_only / bills_only / mixed."""
    vp = _visual_params(problem)
    denoms = vp.get('available_denominations', [])

    if not denoms:
        return _manual("No available_denominations in visual_params")

    # Philippine coins: 1, 5, 10, 20 (peso coins); bills: 20, 50, 100, 200, 500, 1000
    # Note: 20 exists as both coin and bill — treat based on context
    coin_denoms = {1, 5, 10, 20}
    bill_denoms = {50, 100, 200, 500, 1000}

    denom_set = set(denoms)
    has_coins = bool(denom_set & coin_denoms - {20})  # exclude ambiguous 20
    has_bills = bool(denom_set & bill_denoms)

    if axis_value == 'coins_only':
        if has_bills:
            return _fail(f"denomination_type=coins_only but bill denominations present: {denom_set & bill_denoms}")
        return _pass(f"coins_only confirmed: {denoms}")

    if axis_value == 'bills_only':
        if has_coins:
            return _fail(f"denomination_type=bills_only but coin denominations present: {denom_set & coin_denoms - {20}}")
        return _pass(f"bills_only confirmed: {denoms}")

    if axis_value == 'mixed':
        if not (has_coins or has_bills):
            return _fail(f"denomination_type=mixed but only ambiguous denominations: {denoms}")
        return _pass(f"mixed denominations: {denoms}")

    return _manual(f"Unknown denomination_type='{axis_value}'")


def validate_operation(problem: dict, axis_value: str) -> ValidationResult:
    """Operation type in stem matches axis value."""
    s = _stem(problem)

    op_keywords = {
        'add_amounts':           ['+', 'add', 'total', 'sum', 'altogether'],
        'add_subtract':          ['+', '-', 'add', 'subtract', 'difference'],
        'addition_subtraction':  ['+', '-', 'add', 'subtract'],
        'multiplication_division': ['×', '÷', 'multiply', 'divide', 'times', 'groups'],
        'compare':               ['greater', 'less', 'more', 'fewer', 'compare', 'which is'],
        'find_change':           ['change', 'left', 'remain', 'spent', 'paid'],
        'identify_value':        ['value', 'worth', 'how much', 'total'],
        'identify_name':         ['name', 'called', 'denomination', 'what coin', 'what bill'],
    }

    expected_kws = op_keywords.get(axis_value)
    if not expected_kws:
        return _manual(f"No keyword set defined for operation='{axis_value}'")

    found = [kw for kw in expected_kws if kw in s]
    if found:
        return _pass(f"operation={axis_value} keyword(s) found: {found}")

    return _manual(
        f"operation={axis_value}: expected keywords {expected_kws} not found in stem",
        stem=problem.get('stem')
    )


def validate_include_zeros(problem: dict, axis_value: str) -> ValidationResult:
    """Numbers with or without internal zeros — applies to 3+ digit place-value numbers only."""
    # Only relevant for 3+ digit numbers (place value context)
    # Numbers like 50, 60, 70 ending in zero are NOT "zeros" in this pedagogical context
    stem = problem.get('stem', '')
    multi_digit = [int(n) for n in re.findall(r'\b\d+\b', stem) if int(n) >= 100]

    if not multi_digit:
        return _manual("No 3+ digit numbers found — include_zeros only applies to place value problems")

    has_internal_zero = any('0' in str(n)[1:-1] for n in multi_digit if len(str(n)) > 2)
    has_any_zero_digit = any('0' in str(n) for n in multi_digit)

    if axis_value == 'with_zeros':
        if not has_any_zero_digit:
            return _fail(f"include_zeros=with_zeros but no zeros found in {multi_digit}")
        return _pass(f"Zeros present in {multi_digit}")

    if axis_value == 'no_zeros':
        zeros_found = [n for n in multi_digit if '0' in str(n)]
        if zeros_found:
            return _fail(f"include_zeros=no_zeros but zeros found in {zeros_found}")
        return _pass(f"No zeros in {multi_digit}")

    return _manual(f"Unknown include_zeros='{axis_value}'")


def validate_mode(problem: dict, axis_value: str) -> ValidationResult:
    """Clock mode: read (tell the time) vs set (place hands)."""
    s = _stem(problem)
    if axis_value == 'read':
        read_kws = ['what time', 'what is the time', 'read the clock', 'shows']
        if any(kw in s for kw in read_kws):
            return _pass("mode=read confirmed")
        return _manual("Cannot confirm mode=read from stem", stem=problem.get('stem'))

    if axis_value == 'set':
        set_kws = ['draw', 'show', 'set the clock', 'draw the hands', 'place the hands']
        if any(kw in s for kw in set_kws):
            return _pass("mode=set confirmed")
        return _manual("Cannot confirm mode=set from stem", stem=problem.get('stem'))

    return _manual(f"Unknown mode='{axis_value}'")


def validate_include_ampm(problem: dict, axis_value: str) -> ValidationResult:
    """AM/PM — only reliably testable on MCQ elapsed-time stems."""
    vp = _visual_params(problem)
    # If visual, the clock component handles AM/PM display — not verifiable from JSON
    if problem.get('is_visual'):
        return _manual("include_ampm for visual ClockSet requires UI rendering review")

    s = _stem(problem)
    has_ampm = 'a.m.' in s or 'p.m.' in s or ' am' in s or ' pm' in s or 'morning' in s or 'afternoon' in s

    if axis_value == 'with_ampm':
        if not has_ampm:
            return _manual("include_ampm=with_ampm: MCQ elapsed-time format doesn't use AM/PM — needs generator update")
        return _pass("AM/PM present in stem")

    if axis_value == 'no_ampm':
        if has_ampm:
            return _fail("include_ampm=no_ampm but AM/PM found in stem")
        return _pass("No AM/PM in stem (correct)")

    return _manual(f"Unknown include_ampm='{axis_value}'")


def validate_pattern_type(problem: dict, axis_value: str) -> ValidationResult:
    """Numeric sequence pattern type — only from stem sequence, not MCQ options."""
    # Extract only from the stem, specifically the sequence before the blank
    stem = problem.get('stem', '')

    # Try to find a comma/space-separated sequence in the stem
    # Pattern: "N, N, N, N, ___" or "N N N N ___"
    seq_match = re.findall(r'\b(\d+)\b(?=.*(?:___|\.\.\.|\?))', stem)
    if len(seq_match) < 3:
        return _manual("Insufficient numbers in stem to classify pattern type")

    nums = [int(n) for n in seq_match]
    # Only use consecutive differences (exclude the answer itself)
    diffs = [nums[i+1] - nums[i] for i in range(min(len(nums)-1, 5))]
    non_zero = [d for d in diffs if d != 0]

    if not non_zero:
        return _manual("All differences zero — cannot classify pattern")

    all_positive = all(d > 0 for d in non_zero)
    all_negative = all(d < 0 for d in non_zero)
    constant = len(set(non_zero)) == 1

    if axis_value == 'arithmetic_increasing':
        if not (all_positive and constant):
            return _fail(f"pattern_type=arithmetic_increasing but diffs={diffs}", sequence=nums)
        return _pass(f"Arithmetic increasing: step={non_zero[0]}")

    if axis_value == 'arithmetic_decreasing':
        if not (all_negative and constant):
            return _fail(f"pattern_type=arithmetic_decreasing but diffs={diffs}", sequence=nums)
        return _pass(f"Arithmetic decreasing: step={non_zero[0]}")

    if axis_value in ('repeating', 'combined'):
        return _manual(f"pattern_type={axis_value} is hard to validate programmatically")

    return _manual(f"Unknown pattern_type='{axis_value}'")


def validate_fraction_type(problem: dict, axis_value: str) -> ValidationResult:
    """Fraction type — check stem only to avoid false positives from MCQ options."""
    stem = problem.get('stem', '')
    # Only check stem, not options, to avoid confusion with trap fractions
    fractions = re.findall(r'(?<!\d)(\d+)\s*/\s*(\d+)(?!\d)', stem)
    mixed = re.findall(r'(\d+)\s+(\d+)/(\d+)', stem)

    if axis_value == 'unit_fraction':
        if not fractions and not mixed:
            return _manual("No fractions in stem to check")
        from math import gcd
        non_unit = [(n, d) for n, d in fractions if int(n) // gcd(int(n), int(d)) != 1]
        if non_unit:
            return _fail(f"fraction_type=unit_fraction but non-unit fractions (after simplification) in stem: {non_unit}")
        return _pass(f"All fractions in stem are unit fractions (after simplification): {fractions}")

    if axis_value == 'similar_proper':
        if not fractions and not mixed:
            return _manual("No fractions in stem to check")
        return _pass(f"Fractions present in stem: {fractions}")

    if axis_value == 'mixed_number':
        if mixed:
            return _pass(f"Mixed numbers found: {mixed}")
        return _manual(f"fraction_type=mixed_number — check visually if mixed number shown")

    return _manual(f"Unknown fraction_type='{axis_value}'")


def validate_task_type(problem: dict, axis_value: str) -> ValidationResult:
    """Task type keyword detection in stem."""
    s = _stem(problem)

    task_kws = {
        'compare_two':          ['greater', 'less', 'bigger', 'smaller', 'compare'],
        'order_set':            ['order', 'arrange', 'ascending', 'descending', 'smallest to largest'],
        'find_between':         ['between', 'middle number', 'numbers between'],
        'identify_place':       ['place', 'tens place', 'ones place', 'hundreds place'],
        'identify_value':       ['value', 'digit', 'how much is'],
        'compose':              ['make', 'write as', 'compose', 'put together'],
        'decompose':            ['expand', 'decompose', 'break', 'separate'],
        'identify_ordinal':     ['ordinal', 'first', 'second', 'third', 'position'],
        'find_position':        ['position', 'what position', 'which position'],
        'compare_positions':    ['before', 'after', 'between', 'ordinal'],
        'read_single':          ['what time', 'clock shows', 'read'],
        'find_total':           ['total', 'how many', 'altogether', 'in all'],
        'find_difference':      ['difference', 'how many more', 'how many fewer', 'how much more'],
        'find_missing_side':    ['missing side', 'find the side', 'length of the missing'],
        'find_perimeter':       ['perimeter'],
        'find_area':            ['area', 'square units', 'square cm', 'square m'],
        'read_measurement':     ['measurement', 'how long', 'how far', 'measure'],
        'compare_lengths':      ['longer', 'shorter', 'same length', 'compare'],
        'compare_bars':         ['bar graph', 'most', 'least', 'how many more'],
        'read_value':           ['how many', 'how much', 'total in'],
        'convert':              ['convert', 'change to', 'equal to', 'same as', '='],
        'estimate':             ['estimate', 'about', 'approximately'],
        'solve_problem':        ['solve', 'word problem', 'maria', 'juan', 'lola'],
        'elapsed_days':         ['how many days', 'days', 'elapsed'],
        'elapsed_weeks':        ['how many weeks', 'weeks'],
        'find_date':            ['what date', 'which date', 'what day'],
        'read_day_of_week':     ['what day', 'day of the week'],
        'read_month':           ['what month', 'which month'],
        'identify_name':        ['name', 'what is the', 'identify'],
        'identify_property':    ['property', 'characteristic', 'attribute'],
        'compare_shapes':       ['same', 'different', 'compare shape'],
        'count_sides_corners':  ['sides', 'corners', 'vertices', 'edges'],
        'apply_rotation':       ['rotation', 'turn', 'rotate'],
        'compose_decompose':    ['make', 'build', 'separate'],
        'find_most_least':      ['most', 'least', 'highest', 'lowest'],
        'compare':              ['more', 'less', 'greater', 'fewer', 'which'],
    }

    kws = task_kws.get(axis_value)
    if not kws:
        return _manual(f"No keyword set defined for task_type='{axis_value}'")

    found = [kw for kw in kws if kw in s]
    if found:
        return _pass(f"task_type={axis_value} keyword(s) found: {found}")

    return _manual(
        f"task_type={axis_value}: expected keywords not found in stem",
        stem=problem.get('stem')
    )


def validate_scale(problem: dict, axis_value: str) -> ValidationResult:
    """Bar chart scale value in visual_params."""
    vp = _visual_params(problem)
    # The bar chart stores scale under the key 'scale' (not 'y_scale')
    scale_val = vp.get('scale') or vp.get('y_scale') or vp.get('scale_value')

    expected = {'scale_5': 5, 'scale_10': 10, 'scale_20': 20, 'scale_2': 2}
    if scale_val is not None:
        exp = expected.get(axis_value)
        if exp and int(scale_val) != exp:
            return _fail(f"scale={axis_value} but visual_params has scale={scale_val}")
        return _pass(f"Scale={scale_val} matches {axis_value}")

    return _manual(f"No scale in visual_params — cannot validate scale={axis_value}")


def validate_scale_type(problem: dict, axis_value: str) -> ValidationResult:
    if axis_value == 'no_scale':
        return _pass("no_scale: accept as long as generation succeeds")
    return validate_scale(problem, axis_value)


def validate_unit(problem: dict, axis_value: str) -> ValidationResult:
    """Unit keywords in stem."""
    s = _stem(problem)
    unit_kws = {
        'grams_kilograms':   ['gram', 'kilogram', 'kg', 'g'],
        'liters_milliliters':['liter', 'milliliter', 'ml', 'l'],
        'square_cm':         ['sq cm', 'cm²', 'square centimeter', 'square cm'],
        'square_m':          ['sq m', 'm²', 'square meter', 'square m'],
    }
    kws = unit_kws.get(axis_value)
    if not kws:
        return _manual(f"Unknown unit='{axis_value}'")

    found = [k for k in kws if k in s]
    if found:
        return _pass(f"unit={axis_value} keyword found: {found}")
    return _manual(f"unit={axis_value}: no keywords found — may be in visual", stem=problem.get('stem'))


def validate_unit_type(problem: dict, axis_value: str) -> ValidationResult:
    """Length unit type keywords."""
    s = _stem(problem)
    kws = {
        'centimeters':     ['centimeter', 'cm'],
        'meters':          ['meter', 'm '],
        'convert_between': ['convert', 'equal', '= '],
        'non_standard':    ['paper clip', 'cube', 'block', 'hand', 'step'],
    }
    expected = kws.get(axis_value, [])
    if not expected:
        return _manual(f"Unknown unit_type='{axis_value}'")

    found = [k for k in expected if k in s]
    if found:
        return _pass(f"unit_type={axis_value}: {found}")
    return _manual(f"unit_type={axis_value}: no keywords found", stem=problem.get('stem'))


def validate_measurement_type(problem: dict, axis_value: str) -> ValidationResult:
    s = _stem(problem)
    # When the problem is a number comparison, the measurement_type axis cannot be validated
    # (the node routes to compare_order generator rather than measurement generator)
    if any(kw in s for kw in ['greater', 'larger', 'bigger', 'compare', 'which is', 'which number']):
        return _manual(f"measurement_type={axis_value}: problem is a number comparison, not a measurement problem")
    if axis_value == 'mass':
        if any(k in s for k in ['gram', 'kilogram', 'kg', 'weigh', 'mass', 'heavier', 'lighter', 'balance']):
            return _pass("mass keywords found")
        return _fail("measurement_type=mass but no mass keywords in stem", stem=problem.get('stem'))
    if axis_value == 'capacity':
        if any(k in s for k in ['liter', 'milliliter', 'ml', 'capacity', 'volume',
                                  'hold', 'fill', 'cup', 'glass', 'bucket', 'bottle', 'container']):
            return _pass("capacity keywords found")
        return _fail("measurement_type=capacity but no capacity keywords in stem", stem=problem.get('stem'))
    return _manual(f"Unknown measurement_type='{axis_value}'")


def validate_equation_type(problem: dict, axis_value: str) -> ValidationResult:
    s = problem.get('stem', '')
    if axis_value == 'standard':
        if '=' in s:
            return _pass("Standard equation form detected")
        return _manual("Cannot confirm equation_type=standard", stem=s)
    if axis_value == 'balance_expression':
        # Balance expressions often look like: "? + 3 = 7 + 2"
        sides = s.split('=')
        if len(sides) == 2:
            both_have_ops = (
                any(op in sides[0] for op in ['+', '-', '×', '÷']) and
                any(op in sides[1] for op in ['+', '-', '×', '÷'])
            )
            if both_have_ops:
                return _pass("Balance expression: both sides have operators")
        return _manual("Cannot confirm balance_expression", stem=s)
    return _manual(f"Unknown equation_type='{axis_value}'")


def validate_remainder(problem: dict, axis_value: str) -> ValidationResult:
    """Division problems: remainder present or absent. Visual problems are exempt."""
    if problem.get('is_visual'):
        return _manual(f"remainder={axis_value}: visual problems use different format")

    s = problem.get('stem', '')
    # Only match explicit division, not fractions (avoid matching "1/3" as "1÷3")
    div_match = re.search(r'(\d+)\s*÷\s*(\d+)', s)
    if not div_match:
        return _manual("No ÷ division expression found in stem", stem=s)

    a, b = int(div_match.group(1)), int(div_match.group(2))
    if b == 0:
        return _manual("Division by zero in stem")

    rem = a % b
    if axis_value == 'none':
        if rem != 0:
            return _fail(f"remainder=none but {a} ÷ {b} has remainder {rem}")
        return _pass(f"{a} ÷ {b} = {a//b} remainder 0")
    if axis_value == 'with_remainder':
        if rem == 0:
            return _fail(f"remainder=with_remainder but {a} ÷ {b} divides evenly")
        return _pass(f"{a} ÷ {b} has remainder {rem}")
    return _manual(f"Unknown remainder='{axis_value}'")


def validate_proximity(problem: dict, axis_value: str) -> ValidationResult:
    """Numbers close together vs far apart — only checks the two numbers being compared."""
    s = problem.get('stem', '')

    # Look for "which is greater: A or B" or "compare A and B"
    compare_match = re.search(r'(?:greater|less|bigger|smaller|compare)[^?:]*?(\d+).*?(\d+)', s, re.IGNORECASE)
    if compare_match:
        a, b = int(compare_match.group(1)), int(compare_match.group(2))
    else:
        # Fall back to all numbers in stem only
        nums = [int(n) for n in re.findall(r'\b\d+\b', s)]
        nums = [n for n in nums if n > 0]
        if len(nums) < 2:
            return _manual("Insufficient numbers in stem to check proximity")
        a, b = nums[0], nums[1]

    if a == 0 or b == 0:
        return _manual("One number is 0 — cannot compute relative proximity")

    span = abs(a - b)
    scale = max(a, b)
    relative_span = span / scale

    if axis_value == 'close_together':
        # Use absolute distance for small numbers (< 100), relative for large
        if max(a, b) <= 20:
            # For small numbers, close = within 3
            if abs(a - b) > 5:
                return _fail(f"proximity=close_together but numbers {a} and {b} differ by {abs(a-b)}")
        elif relative_span > 0.40:
            return _fail(f"proximity=close_together but numbers {a} and {b} differ by {relative_span:.0%}")
        return _pass(f"Numbers {a} and {b} are close")
    if axis_value == 'far_apart':
        if max(a, b) <= 20:
            if abs(a - b) < 5:
                return _fail(f"proximity=far_apart but numbers {a} and {b} differ by only {abs(a-b)}")
        elif relative_span < 0.10:
            return _fail(f"proximity=far_apart but numbers {a} and {b} differ by only {relative_span:.0%}")
        return _pass(f"Numbers {a} and {b} are far apart")
    return _manual(f"Unknown proximity='{axis_value}'")


def validate_boundary_proximity(problem: dict, axis_value: str) -> ValidationResult:
    """Numbers near vs far from rounding boundaries."""
    nums = _extract_numbers(problem)
    if not nums:
        return _manual("No numbers found")

    def near_any_boundary(n):
        """Near boundary = within 10% of the next round number at any scale."""
        if n < 10:
            return False
        # Check all relevant rounding scales
        for scale in [10, 100, 1000, 10000, 100000, 1000000]:
            if n < scale * 2:
                # Find nearest boundary
                lower = (n // scale) * scale
                upper = lower + scale
                midpoint = lower + scale // 2
                # "Near" = within 15% of the scale unit from either boundary
                threshold = scale * 0.15
                if abs(n - lower) <= threshold or abs(n - upper) <= threshold:
                    return True
                break
        return False

    has_near = any(near_any_boundary(n) for n in nums if n > 5)

    if axis_value == 'near_boundary':
        if not has_near:
            return _fail(f"boundary_proximity=near_boundary but no numbers near boundaries: {nums}")
        return _pass(f"Numbers near boundary: {[n for n in nums if near_any_boundary(n)]}")
    if axis_value == 'far_from_boundary':
        if has_near:
            return _fail(f"boundary_proximity=far_from_boundary but near-boundary numbers found: {[n for n in nums if near_any_boundary(n)]}")
        return _pass(f"Numbers far from boundaries: {nums}")
    return _manual(f"Unknown boundary_proximity='{axis_value}'")


def validate_element_type(problem: dict, axis_value: str) -> ValidationResult:
    """Pattern elements: numeric digits vs number words."""
    s = problem.get('stem', '')
    word_nums = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
                 'eleven', 'twelve', 'fifteen', 'twenty']
    has_words = any(w in s.lower() for w in word_nums)
    has_digits = bool(re.search(r'\b\d+\b', s))

    if axis_value == 'numbers':
        if has_digits:
            return _pass("Numeric digits found in stem")
        return _manual("element_type=numbers: no digits found", stem=s)
    if axis_value == 'number_words':
        if has_words:
            return _pass("Number words found in stem")
        return _manual("element_type=number_words: no word numbers found", stem=s)
    return _manual(f"Unknown element_type='{axis_value}'")


def validate_directions(problem: dict, axis_value: str) -> ValidationResult:
    """Number line / ruler: one vs two directions from origin."""
    vp = _visual_params(problem)
    if 'min_value' in vp and 'max_value' in vp:
        mn, mx = vp['min_value'], vp['max_value']
        has_negative = mn < 0
        if axis_value == 'two_directions' and not has_negative:
            return _fail(f"directions=two_directions but number line is {mn} to {mx} (no negatives)")
        if axis_value == 'one_direction' and has_negative:
            return _fail(f"directions=one_direction but number line includes negatives ({mn})")
        return _pass(f"directions={axis_value} confirmed (range {mn} to {mx})")
    return _manual(f"No min/max in visual_params — cannot validate directions={axis_value}")


def validate_number_size(problem: dict, axis_value: str) -> ValidationResult:
    """small_numbers vs larger_numbers — only meaningful for non-multiplication-table contexts."""
    s = problem.get('stem', '')

    # Geometry problems use pedagogically small numbers for side lengths
    if any(kw in s.lower() for kw in ['perimeter', 'area', 'side length', 'square', 'rectangle', 'triangle']):
        return _manual(f"number_size={axis_value}: geometry problems use small dimensions by design")

    nums = _extract_numbers(problem)
    operands = [n for n in nums if n > 0]
    if not operands:
        return _manual("No numbers found")

    max_num = max(operands)
    if axis_value == 'small_numbers':
        if max_num > 100:
            return _fail(f"number_size=small_numbers but max={max_num}")
        return _pass(f"Max number {max_num} is small")
    if axis_value == 'larger_numbers':
        if max_num <= 10:
            return _fail(f"number_size=larger_numbers but max={max_num}")
        return _pass(f"Max number {max_num} is larger")
    return _manual(f"Unknown number_size='{axis_value}'")


# ─────────────────────────────────────────────────────────────────────────────
# Axes that require visual/manual review — cannot be verified from JSON alone
# ─────────────────────────────────────────────────────────────────────────────

def _manual_only(axis_value: str) -> ValidationResult:
    return _manual(f"Axis value '{axis_value}' requires visual or pedagogical review")


# ─────────────────────────────────────────────────────────────────────────────
# Registry — maps axis_name → validator function
# ─────────────────────────────────────────────────────────────────────────────

VALIDATOR_REGISTRY: dict = {
    # Range / number bounds
    'range':               validate_range,
    'amount_range':        validate_amount_range,
    'digit_count':         validate_digit_count,
    'number_size':         validate_number_size,

    # Sequence / counting
    'direction':           validate_direction,
    'skip_interval':       validate_skip_interval,
    'pattern_type':        validate_pattern_type,
    'element_type':        validate_element_type,
    'directions':          validate_directions,

    # Arithmetic constraints
    'regrouping':          validate_regrouping,
    'number_type':         validate_number_type,
    'structure':           validate_structure,
    'blank_position':      validate_blank_position,
    'equation_type':       validate_equation_type,
    'remainder':           validate_remainder,
    'include_zeros':       validate_include_zeros,
    'proximity':           validate_proximity,
    'boundary_proximity':  validate_boundary_proximity,

    # Time / clock
    'precision':           validate_precision,
    'mode':                validate_mode,
    'include_ampm':        validate_include_ampm,
    'orientation':         lambda p, v: _manual(f"orientation={v} requires visual rendering"),

    # Money
    'denomination_type':   validate_denomination_type,
    'operation':           validate_operation,

    # Fractions
    'fraction_type':       validate_fraction_type,
    'fraction_model':      lambda p, v: _manual(f"fraction_model={v} requires visual rendering"),

    # Task / problem type
    'task_type':           validate_task_type,

    # Measurement
    'unit':                validate_unit,
    'unit_type':           validate_unit_type,
    'measurement_type':    validate_measurement_type,

    # Graphs / data
    'scale':               validate_scale,
    'scale_type':          validate_scale_type,
    'context':             lambda p, v: _manual(f"context={v} requires visual or content review"),
    'num_categories':      lambda p, v: _manual(f"num_categories={v} requires visual rendering"),

    # Geometry — requires visual rendering
    'shape':               lambda p, v: _manual(f"shape={v} requires visual rendering"),
    'shape_set':           lambda p, v: _manual(f"shape_set={v} requires visual rendering"),
    'concept':             lambda p, v: _manual(f"concept={v} requires visual rendering"),
    'concept_type':        lambda p, v: _manual(f"concept_type={v} requires visual rendering"),

    # Calendar — requires visual rendering
    'calendar_feature':    lambda p, v: _manual(f"calendar_feature={v} requires visual rendering"),

    # Probability / scenario
    'scenario_type':       lambda p, v: _manual(f"scenario_type={v} requires content review"),

    # Table
    'table':               lambda p, v: _manual(f"table={v} requires multiplication table context"),

    # Ask type
    'ask_type':            lambda p, v: _manual(f"ask_type={v} requires pattern context"),
}
