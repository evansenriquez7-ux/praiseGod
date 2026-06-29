# Learning Competency Visual Components Audit Report

This report presents a comprehensive static analysis audit of all visual interactive components defined in [VisualSkeletons.jsx](file:///Users/enrichmentcap/Documents/antigravity/ccmed/frontend/src/components/VisualSkeletons.jsx) against their corresponding python formatters in `backend/app/practice_gen/formatters/visual/`.

The components have been audited against the rules and requirements of [pgen_checklist.md](file:///Users/enrichmentcap/Documents/antigravity/ccmed/docs/pgen_checklist.md).

---

## Summary of Critical Issues

### 1. State Overwrites (Immediate `onAnswer` on Mount)
Many components invoke `onAnswer()` automatically upon mounting because of `useEffect` hooks triggering on default/initial state variables before the student performs any actions. This can prematurely grade questions or corrupt parent response state.

### 2. Visual & Logic Answer Leaks
Several components pre-populate the interactive state with the correct answer from the backend payload (e.g. pre-shading fractions or placing number line dots at the correct coordinates on start), rendering the problem pre-solved for the student.

### 3. Missing Interactivity in `"set"` Mode
Certain components claim compatibility with `"set"` mode (where the student is asked to configure the visual to represent a given mathematical concept), but render entirely static templates with missing prop bindings, broken handlers, or zero input fields.

### 4. Data Type Mismatches
Frontend interactive state outputs raw numbers or complex objects (e.g., `{ hours, minutes }` or `{ bills, coins, total }`), while backend formatters/evaluators expect formatted strings (e.g., `"14:30"`) or single integers.

---

## Detailed Component Audits

### 1. ClockSetInteractive
* **Answer Leak**: **Yes**. In `set` mode, it pre-populates target position with `targetHours` and `targetMinutes`.
* **State Overwrites**: **Yes**. `useEffect` fires `onAnswer` with initial clock coordinates on-mount.
* **Data Type Mismatch**: **Yes**. Frontend returns `{ hours, minutes }` object, but the python formatter expects a formatted string `"HH:MM"`.

### 2. FractionModelInteractive & FractionShadeInteractive
* **Answer Leak**: **Yes (Critical)**. Pre-shades the model on mount in `set` mode using `params.numerator` / `params.shaded_parts`.
* **State Overwrites**: **Yes**. `useEffect` immediately submits `clickedParts` to `onAnswer` on mount.
* **Missing Interactivity**: **Yes (Broken Event Handlers)**.
  - **Broken Click Handlers**: The click handlers are incorrectly defined **inside the `style` object** rather than as JSX attributes, rendering the models completely non-interactive:
    ```javascript
    style={{ ..., onClick: () => { ... } }} // <-- WRONG! onClick is in style
    ```
  - **Number Line mode**: Hardcoded as `is_interactive: false` when `model_type === 'number_line'`, preventing any interaction in set mode.
* **Data Type Mismatch**: **Yes**. Frontend returns the number of shaded parts (e.g. `3`), but the backend expects the fraction string (e.g., `"3/4"`).

### 3. NumberLineInteractive
* **Answer Leak**: **Yes (Critical)**. The dot starts exactly at the correct answer position because of `dot_value` pre-population.
* **State Overwrites**: **Yes**. Immediately fires `onAnswer` with the initial coordinate on mount.
* **Data Type Mismatch**: **Yes (Critical)**. Frontend returns a raw float (e.g., `0.75` or `1.5`), while the backend expects fraction/mixed-number strings (e.g., `"3/4"` or `"1 1/2"`).

### 4. PatternSequenceInteractive
* **Missing Interactivity**: **Yes (Severe - Fully Static)**.
  - Component has no interactive inputs, state, or click selectors.
  - Does not accept `onAnswer` in its parameter signature.
  - Simply renders a static sequence with `?` boxes, making it impossible to answer in `set` mode.

### 5. TenFrameInteractive
* **Missing Interactivity**: **Yes (Severe - Fully Static)**.
  - Only accepts `params` and is completely read-only.
  - Lacks `onAnswer` bindings, click listeners to select/toggle circles, and disabled states.

### 6. ShapeBoardInteractive
* **Missing Interactivity**: **Yes (Severe)**.
  - Lacks drag-and-drop or sorting interactive bins in `set` mode.
* **Data Type Mismatch**: **Yes**. Returns the shape index instead of shape property strings.

### 7. PesoMoneyPicker
* **State Overwrites**: **Yes**. Automatically triggers `onAnswer` on mount with `{ bills: {}, coins: {}, total: 0 }`.
* **Data Type Mismatch**: **Yes**. Returns `{ bills, coins, total }` object, but the backend expects a raw integer representing the total currency value.

### 8. FillInTableInteractive
* **State Overwrites**: **Yes**. Triggers `onAnswer` with an array of `null` values on mount.

### 9. GridAreaInteractive
* **Answer Leak**: **Yes (Real-time Indicator)**. Shows a green checkmark (✓) indicator in real-time when the correct area is shaded before submitting.
* **State Overwrites**: **Yes**. Reports initial shaded size on mount.

### 10. PlaceValueBlocksInteractive & RulerMeasureInteractive
* **State Overwrites**: **Yes**. Fire `onAnswer(0)` or initial position values on mount.

---

## Action Plan & Implementation Guidance

1. **Ref-based First Render Guard**:
   Add a React ref (e.g., `isFirstRender = useRef(true)`) or a tracking state to guard `onAnswer` callbacks inside `useEffect` hooks, preventing them from firing during initial mount execution.
2. **Fix Event Handler Bindings**:
   Move `onClick` handlers out of the React `style` object and place them as proper JSX attributes on SVG or container elements in `FractionModelInteractive`.
3. **Data Type Alignment**:
   Update frontend components or backend evaluators to convert payloads to uniform formats (e.g., converting fraction selections to strings, parsing PesoMoney total to raw integer, etc.).
4. **Implement Missing Interactive States**:
   Introduce interactive input elements, interactive toggles, or click handlers to `PatternSequenceInteractive`, `TenFrameInteractive`, and `ShapeBoardInteractive` so students can submit configurations in `"set"` mode.

---

## Mapping Summary & Machine-Readable Findings

- The backend visual formatters under `backend/app/practice_gen/formatters/visual` were enumerated and mapped to frontend renderer entries in `frontend/src/utils/renderUtils.jsx`, which dispatch to implementations in `frontend/src/components/VisualSkeletons.jsx`.
- A machine-readable JSONL with one object per formatter/component mapping and per-finding details was written to `local_only/scratch/visual_audit_findings.jsonl`.
- Notable mapping to review: `fmt_pictograph.py` emits `visual_type = "BarChart"` and therefore routes to `BarChartInteractive`. Confirm whether pictograph-specific rendering parameters or styling are needed — otherwise no functional mismatch was detected.

If you want a follow-up, I can scaffold an adapter component for pictographs, run focused fuzz tests for pictograph cases, or expand the audit to non-visual formatters.
