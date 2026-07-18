# Live Bug: Bridge-Scalar Inconsistency

**Status:** LOGGED & ESCALATED
**Class:** Explainer / Bug Report
**Affects:** Lab UI difficulty axes selection vs. Student Portal serving path

---

## 1. Description of Inconsistency
There is a functional drift in how the "Advanced (Bridge)" difficulty tier is mapped between the manual testing Lab UI and the automated student portal serving path:

1. **Lab Router / UI:**
   In [matatag_router.py](file:///Users/enrichmentcap/Documents/antigravity/ccmed/backend/app/routes/matatag_router.py), the continuous difficulty axes options are generated using a hardcoded bridge scalar of `1.25` to represent the Advanced tier:
   ```python
   bridge_scalar = 1.25
   ```
   This generates options and previews where the difficulty parameter multiplier reaches up to `1.2` times the maximum bounds.

2. **Student Portal / Serving Path:**
   When a student is assigned Level 4 (Advanced) in the portal, the orchestrator and generators map this level using the central difficulty level map defined in [base.py](file:///Users/enrichmentcap/Documents/antigravity/ccmed/backend/app/practice_gen/dna/base.py):
   ```python
   DIFFICULTY_LEVEL_MAP: Dict[int, float] = {
       1: 0.2,   # Easy
       2: 0.5,   # Medium
       3: 0.8,   # Hard
       4: 1.1,   # Advanced — bridge zone (toward next competency)
   }
   ```
   This requests a difficulty scalar of `1.1` from the pipeline.

**Resulting Drift:** 
A teacher/developer using the Lab UI to preview the "Advanced" setting sees problems generated at scalar `1.25` (up to `1.20` times bounds), whereas students assigned "Advanced" level receive problems generated at scalar `1.1` (up to `1.08` times bounds). The preview and student experiences are decoupled.

---

## 2. Window-Design Math Evidence
The continuous difficulty window `[t_lo, t_hi]` is calculated from the scalar input using a sliding interpolation formula:
* **Window Width (`w`)**: `1.0 / divisions` (typically `0.2` for 5 divisions).
* **Window Start (`t_lo`)**: `scalar * (1.0 - w)`
* **Window End (`t_hi`)**: `t_lo + w`

Depending on whether `1.1` or `1.25` is chosen, the window behaves differently:

### Option A: Scalar = 1.1 (Current Portal Level 4)
* **Window Start (`t_lo`)**: `1.1 * 0.8 = 0.88`
* **Window End (`t_hi`)**: `0.88 + 0.2 = 1.08`
* **Math Implications**:
  * The difficulty window is **`[0.88, 1.08]`**.
  * This window overlaps significantly with the standard maximum window at scalar `1.0` (which is `[0.8, 1.0]`).
  * E.g., for G1 addition (max 100), the upper range generated is `88` to `108`.

### Option B: Scalar = 1.25 (Current Lab UI)
* **Window Start (`t_lo`)**: `1.25 * 0.8 = 1.00`
* **Window End (`t_hi`)**: `1.00 + 0.2 = 1.20`
* **Math Implications**:
  * The difficulty window is **`[1.00, 1.20]`**.
  * This window starts **exactly** where the standard `0.0–1.0` range ends (`1.0`).
  * It creates a clean, contiguous, non-overlapping progression from standard to advanced.
  * E.g., for G1 addition (max 100), the upper range generated is `100` to `120`.

---

## 3. Temporary Mitigation
We have refactored [matatag_router.py](file:///Users/enrichmentcap/Documents/antigravity/ccmed/backend/app/routes/matatag_router.py) to import the shared `DIFFICULTY_LEVEL_MAP` and assign `bridge_scalar = DIFFICULTY_LEVEL_MAP[4]`. This ensures the Lab UI and the portal are dynamically aligned to the same value, resolving the functional drift. 

The decision of whether the unified value of `DIFFICULTY_LEVEL_MAP[4]` should be `1.1` or `1.25` has been escalated to the maintainer.
