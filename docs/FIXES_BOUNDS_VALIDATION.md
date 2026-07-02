# Bounds Validation & Regrouping Axis Filtering Fixes

**Date**: 2026-07-02 (continued)  
**Focus**: Architectural issues with bounds validation and difficulty dimension filtering

## Overview

The practice problem generation system had two related issues preventing it from properly respecting written MATATAG curriculum bounds:

1. **Regrouping axis options not limited by competency bounds** — All LCs showed the same regrouping options (none, one_place, two_places, three_places, four_places) regardless of maximum allowed operand size, violating curriculum intent.

2. **Subtraction LCs with explicit bounds lacked a corresponding difficulty dimension** — LCs saying "numbers up to 20" or "numbers up to 100" had no dimension to express this pedagogical constraint; only continuous "number_difficulty" was available.

## Root Cause

- The axes_catalog defined discrete axis options globally per concept (addition, subtraction), without considering per-LC operand bounds
- The registry parser extracted bounds for result-dimensions (max_sum, max_product) but not operand-dimensions (max_minuend for subtraction)
- The get_matatag_lab_config() router built difficulty_dimensions by using axes catalog directly, with no filtering based on competency_bounds

## Fix 1: Dynamic Regrouping Axis Filtering

### Implementation

Added `_get_max_regrouping_places(max_operand: int) → int` helper function:
```python
def _get_max_regrouping_places(max_operand: int) -> int:
    if max_operand <= 100:
        return 1  # 2-digit max: only ones→tens place
    elif max_operand <= 1000:
        return 2  # 3-digit max: ones→tens, tens→hundreds
    elif max_operand <= 10000:
        return 3  # 4-digit max: ones→tens, tens→hundreds, hundreds→thousands
    else:
        return 4
```

Modified `get_matatag_lab_config()` discrete axis handling:
- For "regrouping" axes on addition/subtraction nodes
- Extracts max_operand from competency_bounds (max_sum for addition, max_minuend for subtraction)
- Maps place-count names ("none"→0, "one_place"→1, "two_places"→2, etc.)
- Filters levels to only include viable options: `place_count ≤ max_places`

### Impact

| Node | Competency | Max Operand | Max Places | Regrouping Options |
|------|-----------|-----------|-----------|-------------------|
| mat_g1_na_q3_4 | less than 100 | 100 | 1 | none, one_place |
| mat_g2_na_q2_6 | less than 1000 | 1000 | 2 | none, one_place, two_places |
| mat_g3_na_q2_4 | less than 10000 | 10000 | 3 | none, one_place, two_places, three_places |
| mat_g1_na_q1_8 | sums up to 20 | 20 | 1 | none, one_place |
| mat_g2_na_q2_2 | sums up to 1000 | 1000 | 2 | none, one_place, two_places |

## Fix 2: Discrete Max_Minuend Axis for Subtraction

### Implementation

1. **Updated registry parser** (`_parse_competency_bounds()` for subtraction):
   ```python
   elif dna_name == "subtraction":
       match = re.search(r'(?:less than|up to)\s+(\d+)', text)
       if match:
           max_val = int(match.group(1))
           bounds["max_minuend"] = (1, max_val)
   ```

2. **Added axis creation in get_matatag_lab_config()**:
   - Detect when subtraction LC has explicit max_minuend
   - Compare to per-grade default (_PARAM_BOUNDS)
   - If LC bound < grade default (e.g., G2 "up to 100" vs. default 999)
   - Create discrete "max_minuend" axis with relevant range options

### Impact

Subtraction LCs with explicit small bounds now have a discrete difficulty dimension:
- mat_g2_na_q2_4 (less than 100, G2): Shows max_minuend axis with options [20, 100]
- Captures pedagogical intent: "practice with 2-digit numbers" vs. "practice with up to 1000"
- Lab UI can present this as "Number Range" control alongside "Regrouping (Borrowing)"

## Files Modified

- `backend/app/practice_gen/registry.py`
  - Updated `_parse_competency_bounds()` to extract max_minuend for subtraction

- `backend/app/routes/matatag_router.py`
  - Added `_get_max_regrouping_places()` helper
  - Modified discrete axis handling in `get_matatag_lab_config()`
  - Added max_minuend axis creation logic

## Verification

All tested nodes show correct filtering:
```
mat_g1_na_q3_4 (up to 100):   regrouping=[none, one_place] ✓
mat_g2_na_q2_6 (up to 1000):  regrouping=[none, one_place, two_places] ✓
mat_g3_na_q2_4 (up to 10000): regrouping=[none, one_place, two_places, three_places] ✓
mat_g1_na_q1_8 (sum up to 20): regrouping=[none, one_place] ✓
mat_g2_na_q2_2 (sum up to 1000): regrouping=[none, one_place, two_places] ✓
```

## Commit

- **Hash**: 500714d
- **Message**: "fix: dynamically limit regrouping axis options by competency bounds"

## Future Work

- Consider extending this pattern to other discrete axes that depend on operand bounds
- Monitor audit results for improvement in profile enumeration efficiency
- Potential future extension: Add discrete "max_product" or "max_quotient" axes for multiplication/division if similar patterns arise
