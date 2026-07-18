# Difficulty Dimensions in Practice Generation

> [!IMPORTANT]
> Reference only. Binding rules live in [pgen_contract.md](./pgen_contract.md).

Difficulty dimensions control the core progression of a problem's complexity across various problem generators (Math DNA). This document outlines how difficulty dimensions work, using the first three MATATAG Grade 1 learning competencies as an example.

## Core Concepts

Difficulty dimensions are defined in `backend/app/practice_gen/axes_catalog.py` and are applied in individual DNA files. They fall into two main categories:

1. **Continuous Scales (`dim_type: "continuous"`)**: Use a numeric scalar (0.0 to 1.0) to map to numerical bounds via **Windowed Sampling**. Wide ranges use logarithmic scales, while narrower ones use linear scales.
2. **Discrete Scales (`dim_type: "discrete"`)**: Predefined ordered steps of difficulty (e.g., regrouping options: none → ones → tens → double).

## Linear vs Logarithmic Scales

When defining a continuous difficulty dimension, choose whether the scalar interpolates the bounds **linearly** or **logarithmically** to maintain an evenly distributed difficulty curve for the student.

### 1. Logarithmic Ranges (Exponential Growth)
Use a logarithmic scale (`scale: "logarithmic"`) when the boundary spans multiple orders of magnitude (e.g., 10 to 10,000) across grade levels. 
If you used a linear scale from 10 to 10,000, a scalar of `0.1` (10% difficulty) would jump straight to 1,000, completely skipping the 100s. A logarithmic scale guarantees the scalar spends proportional time in the 10s, 100s, and 1,000s tiers.

**Examples (First 3 Competencies):**
- **`number_reading`**: The range scales from 1-100 (G1) up to 1-10,000 (G3). This is configured as logarithmic so early scalars appropriately hover in the tens and hundreds.
- **`counting`**: The max number skips from 100 (G1) to 10,000 (G3). This uses `log_interpolate` so difficulty increases multiplicatively, pacing the student's exposure to larger bounds.
- **`ordinal_numbers`**: The maximum ordinal value jumps from 10th (G1) to 100th (G3). This also uses `log_interpolate` to ensure students get sufficient practice in the 10s and 20s before hitting 99th.

### 2. Linear Ranges (Constant Growth)
Use a linear scale (`scale: "linear"`) when the dimension has a tight bound or represents an isolated, non-magnitude metric. 
Linear scales simply take a percentage of the difference between the min and max bounds.

**Examples:**
- **`num_categories` (Bar Graphs / Pictographs)**: Bounded between 3 and 6 categories. A linear interpolation is suited here.
- **`number_difficulty`**: A bounded complexity score defined from `0.0` to `1.0`.

## Understanding the Continuous Scalar and `d=5`

The continuous scalar value `0.0` to `1.0` represents the complete bounds/range specified in the learning competency. `0.0` maps to the minimum bound specified by the competency, and `1.0` maps to the maximum bound.

### Windowed Sampling (`d=5`) and Non-Overlapping Bounds
When a dimension specifies `divisions: 5` (referred to as `d=5`), it means splitting the bounds/range into 5 separate divisions which are mapped to the continuous scalar value. 

To ensure that testing and validation can guarantee the generated difficulty is exactly in the targeted range (i.e. no "Leaky Windows"), these divisions are designed to be completely isolated and **non-overlapping**. For example, avoid overlapping bounds like `[0, .2)`, `[0, .4)`, `[0, .6)`. 

The mapping for `d=5` strictly separates the bounds:
1. **Scalar `0`**: Maps to window `[0, 0.2)`
2. **Scalar `0.25`**: Maps to window `[0.2, 0.4)`
3. **Scalar `0.5`**: Maps to window `[0.4, 0.6)`
4. **Scalar `0.75`**: Maps to window `[0.6, 0.8)`
5. **Scalar `1`**: Maps to window `[0.8, 1.0]`

### Sliding Window Interpolation for Arbitrary Scalars
While the discrete scalars above represent the exact centers of the 5 difficulty tiers, the system fully supports continuous interpolation for any arbitrary scalar between `0.0` and `1.0`. 

The underlying engine calculates the exact target window `[t_lo, t_hi]` using a sliding interpolation formula:
1. **Window Width (`w`)**: Fixed at `1.0 / d` (e.g., `1.0 / 5 = 0.2`).
2. **Window Start (`t_lo`)**: Calculated as `scalar * (1.0 - w)`.
3. **Window End (`t_hi`)**: Calculated as `t_lo + w`.

For example, if an arbitrary scalar of `0.3` is provided:
- `t_lo = 0.3 * (1.0 - 0.2) = 0.24`
- `t_hi = 0.24 + 0.2 = 0.44`

This produces an exact, continuous target difficulty window of **`[0.24, 0.44]`**. The engine evaluates all candidate problems and filters them down to those whose complexity scores fall exactly within this sliding window, falling back to the closest candidate if the window is completely empty.

### Bridging to the Next Competency (Scalar > 1)
A scalar value greater than `1.0` represents advanced difficulty for bridging to the next learning competency. To prevent functional drift, the bridge scalar is dynamically linked and imported from `DIFFICULTY_LEVEL_MAP` in `base.py` (level 4). 

The target difficulty window shifts depending on the value configured in `DIFFICULTY_LEVEL_MAP[4]`:
* **If Scalar = 1.1**: The window is `[0.88, 1.08]`. It overlaps slightly with the standard range.
* **If Scalar = 1.25**: The window is `[1.0, 1.2]`. It starts exactly where the standard range ends, providing a clean contiguous progression.

## The `number_difficulty` Dimension
The `number_difficulty` dimension controls the cognitive complexity of the specific numbers chosen within a given boundary. It acts as an independent scale from the maximum range, preventing a computationally "hard" math problem (like 3-digit addition) from accidentally selecting cognitively easy numbers (like `100 + 100`).

> [!NOTE]
> The `number_difficulty` dimension is only appropriate for learning competencies that already incorporate larger numbers and where students have already mastered counting to 100. It is generally not applied to basic counting competencies.

### Calculation Logic
Currently, the `number_difficulty` score (a normalized scalar from `0.0` to `1.0`) is calculated dynamically based on the number type:

1. **Whole Numbers & Decimals**:
   - **Divisibility (50% weight)**: Scored using `1.0 - (gcd(x, 30) / 30.0)`. Highly divisible numbers (easier) score closer to `0.0`, while numbers coprime to 30 (harder) score closer to `1.0`.
   - **Digit Complexity (30% weight)**: Sums the individual digits relative to the maximum possible sum. Larger digits (7, 8, 9) increase cognitive load and score higher.
   - **Magnitude (20% weight)**: A log-linear scale assessing the number's size relative to the absolute maximum bound.

2. **Signed Integers**:
   - Uses the base whole number calculation on the absolute value, but adds a flat **+0.15 (+15%) difficulty penalty** for negative numbers to account for the cognitive load of processing signs.

3. **Fractions (`n/d`)**:
   - **Denominator Size (40% weight)**: Larger denominators increase the score.
   - **Improper Fraction Penalty (40% weight)**: Evaluates the `numerator / denominator` ratio. Improper fractions automatically receive a `+0.20` difficulty penalty.
   - **Simplification State (20% weight)**: Unsimplified fractions (`gcd(n, d) > 1`) receive a penalty as they require reduction.

4. **Pairs (Two Operands)**:
   - When generating an operation involving two numbers (e.g. `a + b`), the difficulty scores of both candidates are combined using a Root Mean Square (RMS) formula: `sqrt((score_a² + score_b²) / 2.0)`.

Once the scores are calculated for all candidate numbers within the bounds, the engine uses the **Windowed Sampling** logic to randomly select a number that falls exactly into the active difficulty window.

## Axis Policy: Result-Bound vs. Operand-Bound (2026-07-01)

The catalog distinguishes between two kinds of axis bounds, and the policy is: **only add an axis if the LC explicitly requires it.**

### Result-bound axes (kept only when the LC requires them)

| Axis | DNA | Bound | Required by |
|---|---|---|---|
| `max_sum` | addition | The result `a + b` | LCs that say "sums up to N" |
| `max_product` | multiplication | The result `a × b` | LCs that say "products up to N" |
| `max_total` | money | The total of coins/bills | LCs that say "up to ₱N" (money-domain result) |

**Removed in this refactor:**
- `max_difference` from **all 9 subtraction nodes** (no MATATAG K-3 LC says "differences up to N" — all say "both numbers are less than N", which is operand-bound)
- `max_quotient` from **all 10 division nodes** (no MATATAG K-3 LC says "quotients up to N" — all say "2,3,4,5,10 tables" or "2- to 3-digit numbers", which is operand-bound)

### Operand-bound competencies (no axis needed)

Most MATATAG K-3 LCs say "operands less than N" (e.g. "Subtract numbers where both numbers are less than 100"). The operand bound is already enforced by the DNA's per-grade `_PARAM_BOUNDS[grade]` (g1: a<100, g2: a<1000, g3: a<10000 for subtraction; q_max varies for division).

**Why the previous `max_difference` axis was wrong:** the axis bounds the *minuend* (a), not both operands. For an LC like "Subtract numbers where both numbers are less than 100", the axis value of 100 would allow `a=100, b=99` (minuend OK) but not `a=100, b=200` (minuend OK, b > a anyway). In practice the DNA's `a > b` constraint made it accidentally correct for operand-bound LCs, but the axis name did not match its semantic intent. Removing it eliminates the redundancy and the audit's 5x profile-count bloat.

### `number_difficulty`

Kept on all operational nodes. It does real work for some LCs (e.g. "identify the place value of the digit 7 in 873") and noise for others. Decided per-LC as needed.

### How to add a new axis

If a future LC says "differences up to N" or "quotients up to N":

1. Add the axis back to the concept's entry in `axes_catalog.py` (under that DNA's key)
2. Add a `profile.get("max_X")` lookup in the corresponding DNA, falling back to the per-grade `_PARAM_BOUNDS` when not present
3. Update the competency-text parser in `registry.py` to extract the bound from the LC text
4. Document the rationale in this file and in `axes_catalog.py`'s header
