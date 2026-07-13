# Frontend Audit Guide — MATATAG Practice Problem Generators

> *"Praise God" is your catchphrase.* Use it when a component SECURE/PASS row drops to zero.

This document is the **single source of truth** for the final frontend audit
run after the backend `exhaustive_checklist_auditor.py` passes. It supersedes
the two stale, divergent snapshots at `local_only/scratch/visual_components_audit.md`
(Jun 29, 34 lines) and `local_only/scratch/oc/visual_components_audit.md`
(Jul 1, 99 lines). **Those files are now historical only** — keep them read-only
for diffing, but the truth lives here.

## Why this audit exists

The backend auditor (`tests/exhaustive_checklist_auditor.py`) cannot see
React-side bugs: state overwrites that submit answers on mount, answer leaks
into `visual_params`, click handlers wired into the `style` object, data-type
mismatches between the React component and the backend grader, missing
drag-and-drop interactivity, hardcoded English chrome, lab-vs-portal config
divergence, and pictograph-vs-barchart visual-type collisions. The backend
auditor produces `repro_crashes.json` and `checklist_audit_report.json`; this
frontend audit consumes payloads (deterministic ones from `repro_crashes.json`
plus generated ones from each (node × formatter × profile) combination) and
verifies the React components render them correctly and grade them correctly.

A node is **only** considered green when:
1. The backend `exhaustive_checklist_auditor.py` reports 0 violations for it.
2. Every enabled formatter for that node passes the per-component checks in
   §3 (for visual formatters) or §4 (for text formatters).
3. Every enabled formatter passes the grader-contract round-trip in §5.
4. The lab→portal config propagation check in §6 passes.
5. The relevant i18n chrome check in §7 passes (only when `language_preference`
   is `tl`).

## Scope and prerequisites

You will audit:
- **22** components exported from `frontend/src/components/VisualSkeletons.jsx`
  (one of which, `NumberBondInteractive`, also has a dedicated file
  `frontend/src/components/NumberBondInteractive.jsx`).
- **10** text-render branches in `frontend/src/components/QuestionRenderer.jsx`.
- The lab/portal render dispatch in `frontend/src/App.jsx` and the
  `renderVisualInner` switch in `frontend/src/utils/renderUtils.jsx`.
- The three backend graders (portal `/api/practice/submit`, lab v1
  `/api/matatag/lab/submit`, lab v2 `/api/matatag/lab/v2/submit`) for the
  answer-shape contract.
- The lab→portal configuration propagation in
  `backend/app/models.py:CompetencyConfiguration`, written by
  `backend/app/routes/matatag_router.py:1191` and read by
  `backend/app/routes/practice_router.py:530` and `:766`.

**Before you audit**, run the backend auditor to populate the repro queue:

```bash
bash tests/run_checklist_audit.sh
# outputs:
#   local_only/scratch/oc/checklist_audit_report.json
#   local_only/scratch/oc/repro_crashes.json
```

Then clear bytecode cache if your code change is not loading:

```bash
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
```

## The repro harness

This audit is **runtime-verifiable**, not just static analysis. A single
Puppeteer harness (per §8 below) consumes the crash payloads and additional
generated payloads, mounts the React app, and asserts on the rendered DOM and
the grader's response. **Static analysis alone is insufficient** — it cannot
detect first-render `useEffect` overwrites or `disabled`-state answer reveals
because those are runtime behaviors.

The harness reads from two sources:

1. **`local_only/scratch/oc/repro_crashes.json`** — every backend crash
   deterministically re-triggerable via its saved `(node_id, seed, formatter,
   difficulty_profile)`. Each crash entry is a payload you must render and
   verify does not surface a frontend bug masking the backend bug.

2. **A generated (node × formatter × profile) matrix** — for each formatter
   enabled on a node, render a deterministic payload (fixed seed, fixed profile)
   through `_pg_run` and assert the React component renders it correctly and
   the grader accepts a known-correct answer.

The harness structure is specified in §8.

---

## Section 0: Pre-audit run rules (MANDATORY)

These rules gate every audit run. Skipping any rule produces false PASSes —
the 3 `mat_g3_na_q4_7` bugs flagged on 2026-07-13 each trace to a run-rule
violation below.

### 0.1 Use the SAVED DB config, not an assumed default

The MATATAG Lab's single-source-of-truth is the live `CompetencyConfiguration`
row in the Neon DB. The student portal reads that row at serve-time
(`practice_router.py:530,766`); the audit must consume the same row before
generating any payload.

```python
from backend.app.models import CompetencyConfiguration
from backend.app.database import SessionLocal
db = SessionLocal()
cfg = db.query(CompetencyConfiguration).filter_by(node_id=node_id).first()
allowed_formatters = cfg.allowed_formatters
allowed_difficulties = cfg.allowed_difficulties
allowed_contexts    = cfg.allowed_contexts
db.close()
```

**If the audit ran with an assumed config (e.g. `[cloze, mcq, ...]` when the
saved row has only `[fraction_model_read, fraction_shade]`), the audit is
invalid** — the orchestrator's formatter selection and the contextual-variant
filtering diverge from what the student actually exercises. The
`mat_g3_na_q4_7` audit on 2026-07-14 passed with `fraction_type=['proper']`,
but the saved row has `['proper','improper','mixed']`; the improper-fraction
regression (Bug #57) was invisible until a student flagged it.

If no row exists, fall back to `_build_all_enabled_config(node_id)`
(`practice_router.py:99`) — the same function the portal uses — and record
"default-config audit" in the pass register.

### 0.2 Re-audit after ANY `visual_params` schema change

When a fix strips, renames, or adds a `visual_params` key, the React
component's dependents on that key must be re-verified. Run rule 0.3 below
against the formatters touched AND every formatter sharing the same React
component.

### 0.3 Run the schema-render contract check

For every formatter × every enabled contextual-variant combination, render
the generated `visual_params` through the React component's exact derivation
lines (see Appendix D). Assert that every value the component reads from
`params.*` resolves to a valid (non-`undefined`, non-`NaN`) JavaScript value.
A missing key in `visual_params` that the component reads silently collapses
to `undefined` / `0` / `false` — which is exactly the failure mode behind
Bugs #56 / #57 / #58.

### 0.4 Audit must run for every distinct `fraction_type` and `model_type`

When the formatter supports improper and mixed fractions, the audit must
exercise all three flavors with seeds chosen to surface the
multi-whole-rendering branch:

- proper: `numer < denom` (single whole)
- improper: `numer > denom` (multiple wholes — exercises `wholeUnits ≥ 2`)
- mixed: integer + fractional part (multiple wholes — when applicable)

And every `model_type` (`area`, `set` / `set_model`, `number_line`) MUST be
audited independently — they take distinct render branches in
`FractionModelInteractive` (`:3422`, `:3444`, `:3480`). Skipping any branch
leaves a class of bugs unverified.

## Section 1: Visual component coverage matrix

This is the authoritative list of every visual component the frontend ships.
**All 22 must be audited.** A component is audited when every row in its
§3 subsection is checked off.

| # | Component | `renderUtils.jsx` case | Backend `visual_type` emitter | `onAnswer` prop wired in `renderUtils.jsx`? | `hasInteractedRef` guard? | Known issues (see §3 for detail) |
|---:|---|---|---|:---:|:---:|---|
| 1 | `NumberLineInteractive` (`VisualSkeletons.jsx:18`) | `NumberLine` (:30) | `fmt_number_line.py:703/575` | ✅ | ✅ (:65,:68) | Answer leak (`dot_value` pre-populate), dtype mismatch (float vs `"<n>/<d>"`) |
| 2 | `ClockSetInteractive` (:313) | `ClockSet` (:36) | `fmt_clock.py:283` | ✅ | ✅ (:332,:340) | Answer leak (`targetHours/Minutes`), dtype mismatch (`{hours,minutes}` vs `"HH:MM"`) |
| 3 | `PesoMoneyPicker` (:675) | `PesoMoney` (:38) | `fmt_peso_money.py:319` | ✅ | ✅ (:682,:700) | dtype mismatch (`{bills,coins,total}` object vs int) — **portal grader expects `total` int; v2 expects string** |
| 4 | `EstimationGateInteractive` (:1021) | **NONE** (orphaned) | — | — | ❌ (:1025) | **ORPHANED** — no dispatcher case in `renderUtils.jsx`; never reachable from UI. Fires `onAnswer` on first render (no guard). |
| 5 | `FillInTableInteractive` (:1139) | `FillInTable` (:46) | `fmt_fill_in_table.py:52` | ✅ | ✅ (:1142,:1150) | Fires `onAnswer` with array-of-`null` on mount before interaction completes (guard present but initial-state still null) |
| 6 | `RuleDiscoveryInteractive` (:1272) | `RuleDiscovery` (:48) | **NONE** — no backend formatter emits `RuleDiscovery` | ✅ | ❌ (:1276) | **ORPHANED** — dispatcher case exists but no backend `visual_type` produces this string. Component unreachable in normal flow. Fires `onAnswer` on every render. |
| 7 | `ConstraintSatisfactionInteractive` (:1393) | **NONE** (orphaned) | — | — | ❌ (:1397) | **ORPHANED** — no dispatcher case, no backend emitter, no `onAnswer` guard. |
| 8 | `BarChartInteractive` (:1514) | `BarChart` (:50) | `fmt_bar_chart.py:365` **AND** `fmt_pictograph.py:287` | ✅ | ❌ (:1554) | Fires `onAnswer` immediately in `useEffect`; multiple branches at :1561/:1568/:1573/:1575. Also renders **pictographs** because `fmt_pictograph.py` aliases `visual_type="BarChart"` — confirm pictograph styling. |
| 9 | `SortOrderInteractive` (:2166) | `SortOrder` (:28) | (textual; `sort_order` is alias for `ordering` formatter at `adapter.py:150`) | ✅ | ❌ (:2171) | **CRITICAL** — fires `onAnswer(items)` on mount with the shuffled array as the answer; **leaks `correct_sequence` to network payloads**. Backend deduplicates valid duplicates `[5,5,2]→[5,2]` (mathematically incorrect). |
| 10 | `GridAreaInteractive` (:2380) | `GridArea` (:40) | `fmt_array_grid.py:309` | ✅ | ✅ (:2398,:2401) | Real-time green ✓ indicator leaks correctness before submit; reports initial shaded size on mount; **backend emits L-shapes the frontend cannot render** (old audit, Batch 1) |
| 11 | `CategorizeInteractive` (:2552) | `Categorize` (:44) | `fmt_shape_board.py` (via `adapter.py:180`) | ✅ | ❌ (:2556) | Fires `onAnswer(assignments)` on every render; **no guard**. Emits a dict but v2 grader uses `str()` equality only. |
| 12 | `CalendarInteractive` (:2742) | `Calendar` (:42) | `fmt_calendar.py:279` | ✅ | ✅ (:2749,:2763) | Leaks `correct_duration` (old audit, Batch 1); `useEffect` overwrites student answer |
| 13 | `EmojiPictorialInteractive` (:2943) | `EmojiPictorial` (:34) | `fmt_emoji_pictorial.py:372` | ❌ (`renderUtils.jsx:35` omits `onAnswer`) | n/a (read-only) | **Answer leak** — renders `reveal_text` containing the answer when `disabled` is true (read-mode). Since read-mode passes `disabled=true`, the answer is immediately visible. |
| 14 | `PlaceValueBlocksInteractive` (:3135) | `PlaceValueBlocks` (:32) | `fmt_place_value_blocks.py:302` | ✅ | ✅ (:3149,:3185) | State overwrite on mount (initial `0`) |
| 15 | `PatternSequenceInteractive` (:3307) | `PatternSequence` (:52) | `fmt_pattern_sequence.py:302` | ✅ | ❌ (:3316 gate is `isInteractive && onAnswer`, not a `hasInteractedRef`) | **Fully static** — no interactive inputs, no state; renders `?` boxes. Missing interactivity in `set` mode; fires `onAnswer` on mount when `params` resolves. |
| 16 | `FractionModelInteractive` (:3394) | `FractionModel` (:54) | `fmt_fraction_model.py:262` | ✅ | ✅ (:3407,:3415) | **Critical** — pre-shades the model on mount using `params.numerator`/`params.shaded_parts`; **click handlers wired inside the `style` object instead of JSX attrs** (fully non-interactive); `model_type==='number_line'` hardcoded `is_interactive:false`; dtype mismatch (returns shaded count vs `"n/d"` string) |
| 17 | `FractionShadeInteractive` (:3519) | `FractionShade` (:56) | `fmt_fraction_shade.py:241` | ✅ | inherits from :3394 | Shares the broken `style.onClick` pattern with `FractionModelInteractive`; same pre-shade leak |
| 18 | `TenFrameInteractive` (:3526) | `TenFrame` (:58) | `fmt_ten_frame.py:271` | ❌ (`renderUtils.jsx:59` omits `onAnswer`) | ✅ (:3535,:3538) | **Fully static** — read-only; no click listeners to toggle circles; `set` mode unplayable. The `onAnswer` connection is dropped at the dispatcher so even if the component accepted it, submission fails. |
| 19 | `RulerMeasureInteractive` (:3592) | `RulerMeasure` (:60) | `fmt_ruler_measure.py:241` | ✅ | ✅ (:3600,:3603) | Leaks the pre-set correct length; **no interactivity** in `set` mode; **backend `randint(0,10)` for offset=0 defeats the offset difficulty curve** |
| 20 | `BalanceScaleInteractive` (:3680) | `BalanceScale` (:62) | `fmt_balance_scale.py:219` | ❌ (`renderUtils.jsx:63` omits `onAnswer`) | n/a (read-only) | Read-only by design — verify no cloak of false interactivity; backend `missing_value` should be answerable, but frontend has no input field |
| 21 | `ShapeBoardInteractive` (:3726) | `ShapeBoard` (:64) | `fmt_shape_board.py:256` | ✅ | ✅ (:3730,:3733) | Missing drag-and-drop / sorting bins in `set` mode; dtype mismatch (shape index vs property string); **backend may spawn a rectangle and a square in the same side-count sort question** |
| 22 | `NumberBondInteractive` (:3829 / `NumberBondInteractive.jsx`) | `NumberBond` (:66) | `fmt_number_bond.py:293` | ✅ | ✅ (:3833,:3836) | (Old audit said "missing entirely" — **stale**, the component now exists. Verify the rebuilt version round-trips an integer to the grader.) |

**Dispatcher coverage**: `renderUtils.jsx` has 21 explicit cases plus a default
that renders a red "Unknown visual type" box at `:69`. Two exports
(`EstimationGateInteractive`, `ConstraintSatisfactionInteractive`) have no
dispatcher case and are dead code — **they should be removed or wired**, and
either way audited for removal-or-connection.

**Pictograph collision**: `fmt_pictograph.py:287` aliases `visual_type="BarChart"`,
so `pictograph_read`/`pictograph_set` payloads route to `BarChartInteractive`.
This is intentional reuse but the audit must verify the pictograph-specific
`visual_params` keys (`symbol`, `ask_category`, `has_scale`, `counts`) are
honored by `BarChartInteractive`. If they are silently dropped, the pictograph
renders as a generic bar chart — a category-15 §3 violation.

---

## Section 2: Text-render branch coverage matrix (`QuestionRenderer.jsx`)

The non-visual renderer has 10 branches. Every branch must be audited against
the corresponding backend formatter that produces it.

| # | Branch | `QuestionRenderer.jsx` line | Backend formatter(s) producing it | Audit sub-section |
|---:|---|---|---|---|
| 1 | Worked-example guidance scaffold | :27-41 | (any formatter with `is_worked_example=true` and `worked_example_steps[]`) | §4.1 |
| 2 | Visual + MCQ option buttons | :60-116 | any visual formatter with `answer_collection="mcq"` (most `*_read` formatters) | §4.2 + §3 per component |
| 3 | Visual + interactive `set` (via `renderVisualInner` with `onAnswer`) | :117-124 | `*_set` formatters (`number_line_set`, `clock_set`, etc.) | §4.3 + §3 per component |
| 4 | Visual + free-text input | :125-151 | visual formatters with `interaction_mode!=="set"` and no MCQ | §4.4 |
| 5 | Cloze / `fill_in_blank` text input | :157-176 | `cloze`, `fill_in_blank` | §4.5 |
| 6 | Numeric / integer / decimal input | :179-198 | `numeric_input` | §4.6 |
| 7 | Writing prompt / `text_input` textarea | :201-219 | `writing_prompt` | §4.7 |
| 8 | Standard MCQ | :222-250 | `mcq` | §4.8 |
| 9 | True/False | :253-279 | `true_false` | §4.9 |
| 10 | Ordering text input (comma-separated) | :282-301 | `ordering`, `sort_order` (alias) | §4.10 |

---

## Section 3: Per-visual-component checklist

For every visual component in §1's matrix, run the following checks. The
notational conventions are:

- **PASS** — verified at runtime by the harness (§8) or hand-inspected against
  current source.
- **FAIL** — verified at runtime; reproduces the bug.
- **TODO** — not yet verified.

Failure categories (carry over from the older audits and extended):

- **A** — State Overwrite: `onAnswer` fires on first render.
- **B** — Answer Leak: `visual_params` exposes the correct answer, OR the
  component pre-populates interactive state with the correct answer, OR
  the component renders the answer text before submission.
- **C** — Network-Payload Leak: the answer is present in fetch payload
  visible to DevTools Network tab before the student submits.
- **D** — Missing Interactivity: `set` mode renders a static template with
  no input.
- **E** — Broken Event Handler: handlers wired into `style` object or wrong
  JSX attribute; component is rendered non-interactive.
- **F** — Data Type Mismatch: frontend returns a shape the grader does not
  accept (object, raw float, integer-index vs string-property, etc.).
- **G** — Visual params not honored: backend emits a `visual_params` key that
  the React component ignores (e.g. pictograph `symbol`).
- **H** — Quality / math / curriculum violation: backend produces a visually
  contradictory or curriculum-inappropriate visual.
- **I** — Mode-Signal Propagation: `interaction_mode` / `is_read_only` lives
  at top-level `FormattedProblem` but the React component reads from
  `params` (visual_params). Without explicit propagation into `vp`, the
  component cannot detect read vs set mode and renders an empty visual or a
  dot at position 0. Affects every visual formatter in §3 that branches on
  `isReadOnly` derived from `params`.
- **J** — Multi-Whole Rendering: for improper / mixed fractions, the
  component computes `wholeUnits = Math.ceil(num/den)`. When the formatter
  strips `shaded_parts` (answer-leak fix), `num` collapses to 0 and
  `wholeUnits` collapses to 1 — the student sees 1 bar where 4 are needed.
  The audit must verify `wholeUnits ≥ ceil(correct_num/correct_den)` for
  every improper/mixed payload.
- **K** — Post-Fix Render Regression: any fix that strips or renames a
  `visual_params` key MUST be re-audited across every formatter sharing
  that React component AND every `fraction_type` / `model_type`
  combination. Skipping this is how the answer-leak fix (#001) shipped
  a multi-whole rendering regression (Bug #57).
- **L** — Model-Type Naming Coercion: backend emits `model_type='set_model'`
  but the React component checks `=== 'set'`; the strict equality silently
  falls through to the area branch. Audit each `model_type` string the
  formatter emits vs the equality check the component performs.

### 3.1 `NumberLineInteractive` (`:18`)

- [ ] **A** `dot_value` pre-population. The dot starts at the correct answer
  position before the student interacts. Audit: render a `*_set` payload,
  assert the dot's initial CSS transform differs from the
  `visual_params.correct_answer` position.
- [ ] **F** dtype: returns raw float (`0.75`) but v2 grader (only NumberLine
  is special-cased at `matatag_router.py:1492`) does `str(parsed)==str(correct_answer)`
  with `tolerance`-float compare. Verify portal grader
  (`practice_router.py:1043`) uses tolerance-correct compare; verify v2 grader
  matches.
- [ ] **G** Confirm `divisions`, `content_type`, and fraction-string mode
  (`numerator/denominator`) render correctly.

### 3.2 `ClockSetInteractive` (`:313`)

- [ ] **A** `targetHours`/`targetMinutes` pre-populate.
- [ ] **B** Digital readout `{hours}:{minutes}` rendered below the clock
  canvas unconditionally in `set` mode.
- [ ] **F** **CRITICAL** — three-way divergence:
  - Portal grader (`practice_router.py:1066-1075`) expects `student.hour/minute`.
  - Lab v1 (`matatag_router.py:1023`) accepts `{hours, minutes}` dict OR `"h:m"` string.
  - Lab v2 (`matatag_router.py:1499`) does `str(parsed)==str(correct_answer)` only.
  The frontend returns `${hourStr}:${minStr}` (a string). Verify it parses
  correctly across all three graders. **A passing portal submission may fail
  the lab v2 grader.**
- [ ] **D** `set` mode: confirm hour/minute drag works; `read` mode (`isReadOnly`)
  is gated by `params.interaction_mode==='read' || params.is_read_only || !onAnswer`.

### 3.3 `PesoMoneyPicker` (`:675`)

- [ ] **A** Fires `onAnswer({bills:{}, coins:{}, total:0})` on mount (guard
  present but initial-state is an empty-wallet object).
- [ ] **F** **CRITICAL** — divergence:
  - Portal grader (`practice_router.py:1058-1065`) checks `student_answer.total == visual_params.target_amount`.
  - Lab v1 (`matatag_router.py:1014`) checks the integer total.
  - Lab v2 (`matatag_router.py:1499`) does `str(parsed)==str(correct_answer)` — the
    parsed object is `{bills,coins,total}`, the correct answer is an int —
    string representation compares `'{"bills":...}'` vs `'N'` and **always fails**.
  Verify `submitMatatagAnswer` in `App.jsx:1117-1118` (`JSON.stringify` for
  visual) sends the object; the v2 grader cannot grade it. **Either fix the
  component to return `total` (int) only, or fix the v2 grader.**

### 3.4 `EstimationGateInteractive` (`:1021`)

- [ ] **ORPHAN** — no `renderUtils.jsx` case. Either delete this component or
  wire a dispatcher case (`case 'EstimationGate':`). No backend formatter
  currently emits `EstimationGate`, so the audit decision is "confirm it is
  unreachable dead code" — list it under §10 dead-code findings.
- [ ] **A** If the decision is to keep it: no `hasInteractedRef` guard; fires
  `onAnswer` as soon as `estimate !== ''`. Add a guard before wiring.

### 3.5 `FillInTableInteractive` (`:1139`)

- [ ] **A** Reports `onAnswer(answers)` (array of `null`s) on mount before any
  cell is filled. The `hasInteractedRef` guard (line 1150) gates on
  `hasInteractedRef.current`, but the initial-firing behavior depends on
  when the ref is set — verify by rendering a `fill_in_table` payload and
  asserting no `onAnswer` fires before any input is typed.
- [ ] **F** Backend returns array-of-strings; verify the grader compares
  element-wise with `correct_answers` (`adapter.py:226`).

### 3.6 `RuleDiscoveryInteractive` (`:1272`)

- [ ] **ORPHAN** — `renderUtils.jsx:48` DOES dispatch `RuleDiscovery`, but no
  backend formatter emits `visual_type="RuleDiscovery"`. Confirm no DNA route
  in `backend/app/practice_gen/generators/` aliases it. Mark as dead-code
  pending backend support.
- [ ] **A** If wired: no `hasInteractedRef` guard; fires `onAnswer(expression)`
  on every render.

### 3.7 `ConstraintSatisfactionInteractive` (`:1393`)

- [ ] **ORPHAN** — no dispatcher case in `renderUtils.jsx`. Same disposition as
  §3.4: delete or wire.
- [ ] **A** No `hasInteractedRef` guard.

### 3.8 `BarChartInteractive` (`:1514`)

- [ ] **A** No guard — multiple `onAnswer` branches at `:1561/:1568/:1573/:1575`
  fire on first render. Verify what the initial `useEffect` emits and whether
  that produces a false submission.
- [ ] **G — Pictograph routing**: `fmt_pictograph.py:287` emits
  `visual_type="BarChart"`. Pictograph-specific `visual_params` keys are:
  `symbol`, `ask_category`, `has_scale`, `counts`. Verify
  `BarChartInteractive` renders pictograph mode correctly:
  - The pictograph should show `symbol` (emoji/icon) per category, not bars.
  - `has_scale` should toggle a half-symbol legend.
  - `ask_category` should drive the question text.
  If `BarChartInteractive` simply renders bars regardless, mark this as a **G**
  finding against pictograph and propose splitting the dispatcher case.
- [ ] **F** Lab v1 reads `barValues`/`barValues2`; lab v2 does
  `str(parsed)==str(correct_answer)` only. Verify the v2 string-equality path
  across array JSON shapes.

### 3.9 `SortOrderInteractive` (`:2166`)

- [ ] **A — CRITICAL** — fires `onAnswer(items)` on mount, immediately
  submitting the **shuffled** order as the student's answer. Verify in the
  harness: render a `sort_order` payload with `correct_sequence=[5,5,3]`,
  assert no `/submit` request fires until a drag ends.
- [ ] **C — CRITICAL** — `correct_sequence` is in `visual_params` (the fetch
  payload). Confirm the backend does not echo `correct_sequence` to the
  frontend in the v2 route; if it does, fix the route to strip it.
- [ ] **H — CRITICAL** — backend deduplicates valid duplicates `[5,5,2]→[5,2]`
  in the grader (`practice_router.py:1034-1042`, ordering branch). For a
  sequence containing intentional repeats, the dedup produces a wrong
  comparison. This is a backend bug surfacing in the frontend audit; route
  the fix to the grader, not the renderer.

### 3.10 `GridAreaInteractive` (`:2380`)

- [ ] **B** Real-time green-✓ indicator appears as soon as the student shades
  the correct area, before submission. Confirm by rendering a `grid_area`
  payload, asserting no ✓ appears before click, ✓ does not appear for a wrong
  count.
- [ ] **A** Reports initial shaded size on mount. The
  `hasInteractedRef` guard (line 2401) gates the call but the initial state
  may still propagate. Verify with harness.
- [ ] **G** — backend emits L-shapes in some `array_grid_read` payloads (per
  the old audit, Batch 1). Verify `GridAreaInteractive` renders L-shaped
  highlights; if it renders only rectangles, mark as a **G** finding.

### 3.11 `CategorizeInteractive` (`:2552`)

- [ ] **A** No guard. Fires `onAnswer(assignments)` on every render. Confirm
  no submission fires until the student drops the last shape into a bin.
- [ ] **F** Returns a dict-of-assignments; lab v1 grader at
  `matatag_router.py:1070` accepts a dict (stringified); lab v2 grader does
  `str(parsed)==str(correct_answer)` and **silently mis-grades**.

### 3.12 `CalendarInteractive` (`:2742`)

- [ ] **B** `correct_duration` leaked in `visual_params`. Confirm backend does
  not emit it (or strip it at route).
- [ ] **A** `useEffect` at `:2763` overwrites the student answer. Verify the
  guard gates correctly; old audit flagged it as overwrite.

### 3.13 `EmojiPictorialInteractive` (`:2943`)

- [ ] **B — CRITICAL** — conditionally renders `reveal_text` (which contains
  the answer) based on the `disabled` prop. Because read-mode always sets
  `disabled=true`, the answer is exposed to the student immediately. Verify
  by rendering a `emoji_pictorial_*` payload and asserting `reveal_text` does
  not appear before submission. Fix: gate on `answerResult && answerResult.is_correct`
  or remove `reveal_text` from `visual_params` entirely.
- [ ] Confirm `emoji`, `group_a`, `group_b`, `operation`, `layout`,
  `show_crossed` keys render.

### 3.14 `PlaceValueBlocksInteractive` (`:3135`)

- [ ] **A** Fires `onAnswer(0)` on mount. Verify the guard at `:3185` prevents
  the initial submission.
- [ ] Confirm `thousands/hundreds/tens/ones/total_value/question_type` keys
  render correctly across all six `question_type` variants emitted by
  `fmt_place_value_blocks.py:302`.

### 3.15 `PatternSequenceInteractive` (`:3307`)

- [ ] **D — Severe** — fully static. The component renders `?` boxes and has
  no input mechanism for the student to type the next term. `set` mode is
  unplayable.
- [ ] **A** The `useEffect` gate at `:3316` is `isInteractive && onAnswer`
  only — not a `hasInteractedRef`. Fires on mount when `params` resolves.
- [ ] Confirm `sequence`, `missing_indices`, `element_type`, `rule`,
  `pattern_kind`, `step`, `start`, `multiplier`, `a`, `b` keys are honored.

### 3.16 `FractionModelInteractive` (`:3394`)

**STALE findings (cleared 2026-07-14, commit 9b334b4)** — kept read-only for
diffing:
- Old **B** (pre-shade on mount): STALE — `clickedParts` initializer at
  `:3401-3406` returns `num` only when `isReadOnly`, otherwise `0`.
- Old **E** (`onClick` inside `style`): STALE — `onClick` is a JSX attribute
  at `:3455` and `:3498`.
- Old **D** (`number_line` hardcoded as non-interactive): STALE — line `:3432`
  is `is_interactive: !isReadOnly`.

**ACTIVE findings (post-fix, 2026-07-14)**:

- [ ] **I — Critical** — `FractionModelInteractive` derives read-only state
  from `params.interaction_mode === 'read' || params.is_read_only || !onAnswer`
  (`:3395`). The formatter's `interaction_mode` was originally a TOP-LEVEL
  `FormattedProblem` field, NOT inside `visual_params`. Fix applied
  2026-07-14: `fmt_fraction_model.py` now emits `vp["interaction_mode"]`
  and `vp["is_read_only"]`. Audit: render a `read_mcq` payload through the
  MCQ-over-visual dispatch path at `QuestionRenderer.jsx:62-68` (which
  spreads `visual_params` only) and assert the component renders the
  pre-shaded model, NOT an empty one. If `params.is_read_only` is missing,
  this is a **FAIL (mode-signal propagation)**.
- [ ] **J — Critical** — Multi-whole rendering. For improper fractions
  (e.g. `18/6`, `40/10`, `33/10`) the component must render
  `wholeUnits = ceil(num/den) ≥ 2`. Fix applied: `fmt_fraction_model.py`
  and `fmt_fraction_shade.py` now emit `vp["total_wholes"]`; the component
  reads it as `Math.max(1, params.total_wholes)` at `:3399`. Audit: for
  every improper/mixed payload, assert the rendered bar count is
  `ceil(correct_numerator/correct_denominator)`. If `wholeUnits === 1`
  for an improper fraction, **FAIL (multi-whole rendering)**.
- [ ] **L — High** — Model-type naming coercion. `fmt_fraction_model.py`
  emits `model_type='set_model'` but the React check at `:3444` was strict
  `=== 'set'` — fell through to the area branch silently. Fix applied: the
  check now accepts `'set' || 'set_model'`. Audit: enumerate every
  `model_type` string the formatter emits and verify the component has a
  matching `if` branch; new emit strings must add a matching branch.
- [ ] **F** Returns `"${clickedParts}/${den}"` at `:3416`; portal grader
  added `answer_collection=="click"` arm (`practice_router.py:1076`).
  Verify the grader contract holds for all 3 routes (see §5).
- [ ] **H — Backend** `fmt_fraction_model.py` flips `0/4` to `4/0`
  (division-by-zero distractor). Frontend should also guard against
  rendering `total_parts===0`; surface the backend fix.
- [ ] **K** Post-fix regression gate: any change to `vp` keys for this
  formatter MUST re-run the improper / mixed / proper matrix × all 3
  `model_type` values. The 2026-07-14 answer-leak fix (#001) shipped a
  wholeUnits regression because the verification matrix was `proper`-only.
  See §0.4.

### 3.17 `FractionShadeInteractive` (`:3519`)

- [ ] Thin wrapper around `FractionModelInteractive` (`:3519-3521`) — share
  every check in §3.16.
- [ ] **B / I — Critical** — In `set` mode, `shaded_parts` and
  `fraction_str` are STRIPPED from `visual_params` (answer-leak fix
  applied 2026-07-14). Confirm: render a `set_click` payload and assert
  `visual_params` does NOT include `shaded_parts` or `fraction_str`.
- [ ] **J — Critical** — `total_wholes` MUST be present in `set` mode so
  the component can render enough bars. Without it, improper-fraction
  shades collapse to 1 bar (Bug #57). Audit: for `set_click` with an
  improper result, assert `vp.total_wholes === ceil(result_n/den)`.
- [ ] **K** Regression gate: any change to the strip-set must re-verify
  multi-whole rendering (proper + improper + mixed × all 3 shapes).

### 3.18 `TenFrameInteractive` (`:3526`)

- [ ] **D — Critical wiring defect** — `renderUtils.jsx:58-59` dispatches
  `<TenFrameInteractive key params disabled />` WITHOUT the `onAnswer`
  prop. The `useEffect` guard at `:3538` checks `if (onAnswer && ...)` but
  `onAnswer` is `undefined`, so `onAnswer` is never called. The component is
  effectively read-only even though it has internal click logic.
  Fix: `renderUtils.jsx:59` should be:
  ```jsx
  return <TenFrameInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
  ```
- [ ] Confirm after the fix that the harness is able to log a click and
  submit an answer via `onAnswer`.

### 3.19 `RulerMeasureInteractive` (`:3592`)

- [ ] **B** Pre-set correct length is leaked.
- [ ] **D** No interactivity in `set` mode.
- [ ] **H — Backend** `randint(0,10)` for offset can produce 0, defeating the
  offset-difficulty curve. Surface this to the backend auditor; the frontend
  should also guard against `ruler_start===object_start` collisions.

### 3.20 `BalanceScaleInteractive` (`:3680`)

- [ ] **D** — read-only by design; no `onAnswer` prop wired in
  `renderUtils.jsx:63`. If the backend emits a `missing_value` that should be
  student-supplied, this is a **D** finding for `balance_scale` `set` mode.
  If balance-scale is intentionally read-only (no `*_set` formatter), mark
  PASS.
- [ ] Confirm `left_side`, `right_side`, `blank_side`, `is_balanced`,
  `missing_value`, `a`, `b`, `result`, `blank_target` render correctly.

### 3.21 `ShapeBoardInteractive` (`:3726`)

- [ ] **D** Missing drag-and-drop / sorting bins for `set` mode.
- [ ] **F** Returns the shape index (int) instead of property strings
  (e.g. `"sides=4"` per `fmt_shape_board.py`).
- [ ] **H — Backend** may spawn both a rectangle (4 sides) and a square (4
  sides) in the same "sort by side count" question — ambiguous.
- [ ] Confirm `shapes[]`, `grid_size`, `question_type` render; verify
  `orientation_deg` rotates the SVG.

### 3.22 `NumberBondInteractive` (`:3829`)

- [ ] **Stale finding cleanup**: old audit reported "NumberBond missing from
  the frontend" — superseded. The component exists (`:3829` and the dedicated
  file `NumberBondInteractive.jsx`) and is dispatched correctly at
  `renderUtils.jsx:66`. Verify by rendering a `number_bond` payload in the
  harness.
- [ ] **F** Returns an integer for `part1`/`part2`/`whole`; v2 grader does
  `str(parsed)==str(correct_answer)`. Verify integer stringifies correctly.
- [ ] Confirm the underscore-prefixed private values (`_whole`, `_part1`,
  `_part2`) in `visual_params` are not leaked to the DOM (no `B` violation).

---

## Section 4: Per-text-branch checklist

### 4.1 Worked-example scaffold (`:27-41`)

- [ ] Renders each step from `question.worked_example_steps[]` in order.
- [ ] Steps preserve any `\n` newlines and math notation rendered by
  `renderMath` (verify the `<span>` content is rendered, not the raw string).
- [ ] Scaffold does not interfere with the main question card — confirm the
  `<div>` with `style={{ borderLeft: '4px solid hsl(var(--warning))' }}` does
  not push the question below the fold on mobile.
- [ ] Vocabulary is grade-appropriate (mirror the backend auditor's
  vocab check; the steps are author-time, so this is a passive gate).

### 4.2 Visual + MCQ option buttons (`:60-116`)

- [ ] `renderVisualInner` is called with the spread `{ ...visual_params,
  is_interactive: false }` — verify that spread does not leak the answer via
  a `correct_*` key that the read-only component renders.
- [ ] For each option, the option button `onClick` fires `setAnswer(opt.key)`
  only when `!answerResult`. After submission, `disabled={!!answerResult}`
  prevents changes.
- [ ] The correct-option highlight: `isCorrectOpt` checks `opt.is_correct ||
  opt.key === answerResult.correct_answer || optValueStr === correctAnsStr ||
  opt.text === correctAnsStr`. **Audit:** if `correctAnsStr` is `null` (no
  `correct_answer` field in `answerResult`), the highlight falls back to
  `opt.is_correct`. Confirm `opt.is_correct` is set by the backend in the
  v2 response; confirm the lab route returns it.
- [ ] The `reveal_display` and `reveal_text` block (`:98-114`) renders only
  after submission (`answerResult` truthy). Verify `reveal_text` does not
  contain the literal answer in `visual_params` (which would be a **B**
  leak pre-submission).
- [ ] MCQ option `text` is rendered with `renderMath` — confirm LaTeX and
  mixed numbers (`1 1/2`) render.

### 4.3 Visual + interactive `set` (`:117-124`)

- [ ] `renderVisualInner` is called with `setAnswer` as the `onAnswer` and
  `!!answerResult` as `disabled`. Verify the visual component does not fire
  `onAnswer` on mount (this is the union with §3's per-component checks).
- [ ] The visual answer replaces the text answer in state. Confirm
  `handleAnswerSubmit` in `App.jsx:687-739` `JSON.stringify`s objects and
  `String()`s primitives — and that the portal grader accepts whichever
  shape the component produces (§5).

### 4.4 Visual + free-text input (`:125-151`)

- [ ] The free-text `<input>` is always `type="text"` (even for `numeric_input`
  questions that surface as read-only visuals). Confirm the backend grader
  coerces strings to ints/floats as needed (e.g. number-line read with MCQ
  fallback).
- [ ] `value={answer ?? ''}` — verify `null`/`undefined` answers do not
  render `"null"`.

### 4.5 Cloze / `fill_in_blank` (`:157-176`)

- [ ] The `<input>` is `type="text"`. Confirm backend grader does
  case-insensitive string compare (`practice_router.py:992`).
- [ ] For multi-blank cloze, confirm the answer state encodes multiple
  blanks; if the backend expects an array, verify the textbox placeholder
  hint matches.

### 4.6 Numeric input (`:179-198`)

- [ ] `<input type="number">` — confirm it accepts negatives, decimals,
  thousands separators (or document that it does not). Backend grader does
  float compare (`practice_router.py:985`).

### 4.7 Writing prompt (`:201-219`)

- [ ] `<textarea rows={4}>` — confirm long answers scroll; backend grader
  sends the long text to the writing-grader subagent.

### 4.8 Standard MCQ (`:222-250`)

- [ ] Option button highlight logic mirrors §4.2's `isCorrectOpt` checks.
  Verify the same fallback to `opt.is_correct` works for portal submission
  (`/api/practice/submit`) and lab v2 (`/api/matatag/lab/v2/submit`).
- [ ] For `error_detect` format, confirm `App.jsx:1111-1113` serializes
  `{has_error, correct_value}` as JSON and the v2 grader at
  `matatag_router.py:1452-1478` accepts the JSON.

### 4.9 True/False (`:253-279`)

- [ ] The button labels are hardcoded `['True', 'False']` (`:255`).
  Audit i18n (§7): when the student's `language_preference==='tl'`, the
  buttons remain English. Either translate or document the decision.
- [ ] Highlight logic: `isCorrectAnswer` compares
  `String(question.correct_answer) === val`. Verify `correct_answer` from the
  backend is `"True"`/`"False"` (string) on both portal and lab routes.

### 4.10 Ordering text input (`:282-301`)

- [ ] The placeholder `e.g., 1, 2, 3, 4` and instruction text are hardcoded
  English (`:284-290`). Audit i18n.
- [ ] Backend grader parses comma-separated input into a list
  (`practice_router.py:994-1002`); confirm it tolerates spaces and empty
  trailing elements.

---

## Section 5: Grader-contract round-trip

Three graders exist; **a node passes only when all three agree on the
correct-answer verdict for every enabled formatter**. Auditing this means
taking a known-correct student answer and verifying it grades as correct on
all three grader routes.

### 5.1 The three grader routes

| Grader | Route | Path | Dispatch |
|---|---|---|---|
| Portal | `/api/practice/submit` | `backend/app/routes/practice_router.py:861` | By `fmt` and (for visuals) `question_mode` — fully dispatched per visual type (`:979-1077`) |
| Lab v1 | `/api/matatag/lab/submit` | `backend/app/routes/matatag_router.py:960` | By `visual_type` — dispatched per visual type (`:1014-1097`) |
| Lab v2 | `/api/matatag/lab/v2/submit` | `backend/app/routes/matatag_router.py:1347` | By `format` + `answer_collection`; only `NumberLine` is special-cased for visuals (`:1492-1498`); everything else falls through to `str(parsed)==str(correct_answer)` (`:1499-1504`) |

### 5.2 Per-formatter expected answer shape

For every visual formatter, the audit submits a known-correct answer and
verifies the grader returns `is_correct=true`. **The v2 grader is the weak
point** — for `PesoMoney`, `ClockSet`, `SortOrder`, `Categorize`,
`FractionShade`, `GridArea`, `BarChart`, `NumberBond`, `PatternSequence`,
`TenFrame`, `BalanceScale`, `RulerMeasure`, `ShapeBoard`, `FillInTable`,
`Calendar`, `EmojiPictorial`, `PlaceValueBlocks`, the v2 grader does **only**
`str(parsed)==str(correct_answer)`. Verify the React component's emitted
answer's `JSON.stringify` matches the backend's `correct_answer` string, or
fix the v2 grader to add per-type dispatch matching v1's logic.

| Formatter | Component emits | Portal grader expects | Lab v1 grader expects | Lab v2 grader expects | Status |
|---|---|---|---|---|---|
| `number_line_read` | MCQ key | MCQ key (`:979`) | MCQ key | MCQ key | Verify |
| `number_line_set` | float | float ± tol (`:1043`) | (v1 has no NumberLine branch) | float ± tol (`:1492`) | Verify all three |
| `fraction_model_read` | MCQ key | MCQ key | MCQ key | MCQ key | Verify |
| `fraction_shade` | `"n/d"` string | string compare | string compare | `str(parsed)==str(correct_answer)` | Verify string equality |
| `peso_money_read` | MCQ key | MCQ key | MCQ key | MCQ key | Verify |
| `peso_money_build` | `{bills,coins,total}` obj | `obj.total == target_amount` (`:1058`) | int total (`:1014`) | str equality ONLY — **WRONG** | **FAIL** until v2 grader adds type dispatch |
| `clock_read` | MCQ key | MCQ key | MCQ key | MCQ key | Verify |
| `clock_set` | `"HH:MM"` string | `hour/minute` ints (`:1066`) | `{hours,minutes}` dict or `"h:m"` (`:1023`) | str equality — mismatch risk | Verify |
| `array_grid_read` | MCQ key | MCQ key | MCQ key | MCQ key | Verify |
| `array_grid_set` | int (shaded count) | str equality | str equality | str equality | Verify |
| `grid_area` | int (shaded.size) | MCQ key | MCQ key | MCQ key | Verify |
| `bar_chart_read` | MCQ key | MCQ key | MCQ key | MCQ key | Verify |
| `bar_chart_set` | `[barValues, barValues2]` array | array JSON (`:1051`) | array JSON | str equality — verify JSON | Verify |
| `pictograph_read` | MCQ key | MCQ key | MCQ key | MCQ key | Verify |
| `pictograph_set` | array | array JSON | array JSON | array JSON str | Verify both v1+v2 accept |
| `ten_frame` | (currently does not emit) | MCQ key | n/a | n/a | Verify the §3.18 wiring fix unlocks submission |
| `balance_scale` | (read-only, no emit) | MCQ key | MCQ key | MCQ key | Verify |
| `ruler_measure` | MCQ key | MCQ key | MCQ key | MCQ key | Verify |
| `sort_order` | array | list compare w/ dedup (`:1034`) | list compare | list compare | **FAIL** if duplicates due to backend dedup bug (see §3.9) |
| `shape_board` | integer index | MCQ key | str compare | str compare | **F** finding — should return property string |
| `pattern_sequence` | (currently static, no emit) | MCQ key | MCQ key | MCQ key | Verify after §3.15 wiring fix |
| `calendar_read` | MCQ key | MCQ key | MCQ key | MCQ key | Verify |
| `fill_in_table` | array | array JSON | array JSON | array JSON str | Verify |
| `number_bond` | int | int str equality | int str equality | int str equality | Verify |
| `emoji_pictorial` | (read-only, no emit) | MCQ key | MCQ key | MCQ key | Verify |
| `categorize` | dict-of-assignments | MCQ key | dict str (`:1070`) | `str(parsed)==str(correct_answer)` — **likely wrong** | Verify |
| `place_value_blocks_read` | MCQ key | MCQ key | MCQ key | MCQ key | Verify |
| `place_value_blocks_set` | int | int str equality | int str equality | int str equality | Verify |

### 5.3 Round-trip harness step

For each formatter, the harness (`frontend/audit/run_audit.mjs`, §8) does:

1. Generate a deterministic problem via `_pg_run` with a fixed seed.
2. Extract `visual_params`/`correct_answer` from the response.
3. Execute the harness's "correct answer emitter" per formatter (the inverse
   of each component's expected interaction — e.g. for `peso_money_build`,
   emit `total=target_amount`; for `number_line_set`, emit
   `visual_params.correct_answer`).
4. POST to all three grader routes; assert each returns `is_correct=true`.

A divergence (any grader returning `is_correct=false` while another returns
`true`) is a **FAIL** finding. Record the divergence in the §9 findings log.

---

## Section 6: Lab → portal config propagation

### 6.1 Configuration flow

1. Parent edits formatters/dimensions/variants in the MATATAG Lab UI.
   `fetchLabConfig` (`App.jsx:938-964`) fetches the compatible set; the parent
   toggles checkboxes.
2. Save: `POST /api/matatag/node/{node_id}/config` (`matatag_router.py:1191`)
   validates against `FORMATTER_VARIANT_SUPPORT` and persists the
   `CompetencyConfiguration` row (`matatag_router.py:1254-1266`).
3. Student portal: `GET /api/practice/question` (`practice_router.py:167`) and
   `GET /api/practice/{student_id}/batch` (`practice_router.py:639`) load the
   same `CompetencyConfiguration` row at `:530` and `:766`.
4. Default path: if no row exists, `_build_all_enabled_config(node_id)`
   (`practice_router.py:99-119`) reconstructs the all-ON default by calling
   `get_matatag_lab_config` — the same function the Lab UI's capability
   dropdown uses (`matatag_router.py:400`).

### 6.2 Audit checks

- [ ] **Same-config match**: with the backend running and a known config saved
  for `mat_g3_na_q4_7`, fetch `GET /api/matatag/node/mat_g3_na_q4_7/config`
  then `GET /api/practice/question?skill_id=mat_g3_na_q4_7&...`. Assert the
  `allowed_formatters` returned by the portal route honors the saved config
  (no formatter outside the saved set is returned). Use the deterministic
  script in `docs/generator_testing_strategy.md:391-401` as the model — run it
  for every audited node.
- [ ] **Default-path match**: delete the `CompetencyConfiguration` row for a
  node, fetch `GET /api/practice/question`. Verify the returned formatter is
  in the union of `get_matatag_lab_config(node_id).formatters`.
- [ ] **Client-side default patch**: `App.jsx:942-960` applies a frontend
  "if empty, default to all options" patch before saving. Verify this does
  not silently re-enable a formatter the parent explicitly disabled. Audit:
  fetch lab config, disable one formatter, save, re-fetch; confirm the
  disabled formatter stays disabled after the client-side patch.

### 6.3 `latest_audit_report_summary.md` and `CHECKLIST_AUDIT_BUG_FIXES.md`

`local_only/scratch/oc/CHECKLIST_AUDIT_BUG_FIXES.md` is the running session
log of backend audit fixes — the most recent entry is *"Lab vs Portal
divergence for `mat_g3_na_q4_7`"*. Read this log before each frontend audit
run; any node listed there warrants an extra §6 check.

---

## Section 7: i18n chrome audit

The student's `language_preference` (`'en'` or `'tl'`) is set in `App.jsx:2584`
and persisted to the backend. The backend uses it to switch explanation
strings; **the frontend UI chrome has no translation layer** (grep for `i18n`,
`useTranslation`, `react-i18next` returns nothing).

### 7.1 Hardcoded English UI strings to audit

| # | String | file:line | Visible during |
|---|---|---|---|
| 1 | `"Submit Answer"` | `PracticeView.jsx:777`, `ParentDashboard.jsx:1234` | Every question |
| 2 | `"Next Question"` | `PracticeView.jsx:799` | After submission |
| 3 | `"Correct! Awesome job!"` / `"Incorrect answer."` | `PracticeView.jsx:788` | After submission |
| 4 | `"True"` / `"False"` (hardcoded `['True','False']`) | `QuestionRenderer.jsx:255` | True/false questions |
| 5 | `"Fill in the blank..."` placeholder | `QuestionRenderer.jsx:162` | Cloze |
| 6 | `"Enter your answer..."` placeholder | `QuestionRenderer.jsx:137` | Visual free-text |
| 7 | `"Enter number..."` placeholder | `QuestionRenderer.jsx:184` | Numeric |
| 8 | `"Write your answer here..."` placeholder | `QuestionRenderer.jsx:205` | Writing |
| 9 | `"Enter the values in the correct order, separated by commas:"` | `QuestionRenderer.jsx:284-285` | Ordering |
| 10 | `"e.g., 1, 2, 3, 4"` placeholder | `QuestionRenderer.jsx:290` | Ordering |
| 11 | `"Worked Example Guidance Scaffold Active"` | `QuestionRenderer.jsx:31` | Worked example |
| 12 | `"Incorrect Answer"` (flag label) | `FlagModal.jsx:65` | Flag flow |
| 13 | `"Loading student profiles..."` | `LoginView.jsx:28` | Login |
| 14 | `"Loading available models…"` | `ParentDashboard.jsx:218` | Parent login |

### 7.2 Audit step

- [ ] Toggle a student's `language_preference` to `'tl'`. Walk through a
  practice session covering at least one formatter from each of: MCQ,
  true_false, cloze, ordering, visual set. Compile a list of English
  strings still rendered (screenshot each). Strings 1, 2, 3, 4, 9, 11
  are the highest-priority because they appear in every session.
- [ ] For Tagalog students, verify the backend's Tagalog explanation appears
  below the question (because the explanation IS produced by the backend,
  the frontend just renders `renderMath` on `answerResult.explanation`);
  verify no English leaks.

---

## Section 8: The runtime harness

The harness is `frontend/audit/run_audit.mjs` (not yet implemented — this
section is its specification; see directions for building it at §8.5).

### 8.1 Inputs

1. `local_only/scratch/oc/repro_crashes.json` — every backend crash, each
   with `(node_id, seed, formatter, difficulty_profile)`.
2. A node list from `backend/app/practice_gen/axes_catalog.py` (or the
   lab-portal `get_matatag_lab_config` route) — every node the backend
   audit covers.
3. A formatter list from `FORMATTER_VARIANT_SUPPORT` — every formatter
   enabled on each node.

### 8.2 Per-formatter correct-answer emitter table

The harness requires a per-formatter function that, given a problem
payload, returns the correct answer in the exact shape the React component
would emit after a correct interaction. **This is the contract bridge
between §3 (frontend) and §5 (grader).**

```js
// frontend/audit/correct_answer_emitters.mjs
export const EMITTERS = {
  mcq:            (p) => p.correct_key || p.correct_answer,
  true_false:     (p) => String(p.correct_answer) === 'True' || p.correct_answer === true ? 'True' : 'False',
  numeric_input:  (p) => parseFloat(p.correct_answer),
  cloze:          (p) => p.correct_answer,
  ordering:       (p) => p.visual_params?.correct_sequence || p.correct_answer,
  error_detect:   (p) => JSON.parse(p.correct_answer), // {has_error, correct_value}

  // visuals
  number_line_set:   (p) => parseFloat(p.visual_params.correct_answer),
  fraction_shade:    (p) => p.visual_params.fraction_str,
  peso_money_build:  (p) => p.visual_params.target_amount,
  clock_set:         (p) => `${String(p.visual_params.hours).padStart(2,'0')}:${String(p.visual_params.minutes).padStart(2,'0')}`,
  array_grid_set:    (p) => p.visual_params.correct_count,
  bar_chart_set:     (p) => p.visual_params.correct_answer,
  pictograph_set:    (p) => p.visual_params.correct_answer,
  sort_order:        (p) => p.visual_params.correct_sequence,
  fill_in_table:     (p) => p.visual_params.correct_answers,
  number_bond:       (p) => p.visual_params.blank_position === 'whole'
                       ? p.visual_params.whole
                       : (p.visual_params.blank_position === 'part1' ? p.visual_params.part1 : p.visual_params.part2),
  place_value_blocks_set: (p) => p.visual_params.total_value,
};
```

When a formatter is missing from this table, the harness raises
`MissingEmitterError` (per AGENTS.md rule #4 — no silent skipping). The
emitter must be added before that formatter is auditable.

### 8.3 Runtime assertions

For each (node, formatter, profile) the harness:

1. Generates a problem via the backend `_pg_run` route with a fixed seed.
2. If `is_visual`, mounts the corresponding component in a Puppeteer page
   via the Vite dev server with the problem payload injected.
3. Asserts no `onAnswer`-equivalent fetch fires before any DOM interaction
   (uses Puppeteer's request-interception on `/api/practice/submit` and
   `/api/matatag/lab/v2/submit`).
4. Asserts no DOM element renders the literal `correct_answer` string (CSS
   text-content sweep) before submission — the §3 answer-leak check.
5. Drives the correct interaction per the formatter's interaction emulator
   (drag, click, type) using the emitter table's inverse.
6. Asserts the appropriate `/submit` fetch is sent with the correct shape.
7. Asserts all three graders (portal, v1, v2) return `is_correct=true`.

### 8.4 Output files

- `local_only/scratch/oc/frontend_audit_report.json` —
  `{formatter: [{check, status, evidence, file:line}]}`.
- `local_only/scratch/oc/frontend_repro_findings.jsonl` — each failed
  assertion with `(node_id, seed, formatter, profile, expected, actual)`,
  ready to drive a fix-loop.
- `local_only/scratch/oc/frontend_audit_pass_register.md` — a single
  authoritative table replacing the two stale `visual_components_audit.md`
  files. One row per (component, check), status `PASS`/`FAIL`/`TODO`,
  last-verified commit SHA. This is the **only** file a future auditor
  needs to consult for state.

Snapshot before re-running:

```bash
cp local_only/scratch/oc/frontend_audit_report.json \
   local_only/scratch/oc/frontend_audit_report.$(date +%s).json
```

### 8.5 Build order

1. **Scaffold the harness**: spawn backend (`uvicorn`) + frontend (`npm run dev`),
   Puppeteer on `:5173`, request-intercept `/api/practice/.../batch` and
   `/api/matatag/lab/v2/generate` to return cached problems. Reuse the
   pattern from `local_only/scratch/verify_tf_highlight.js:8-79`.
2. **Per-interaction emulators**: implement the drag/click/type logic per
   `visual_type` (these go alongside the emitter table). Start with the
   10 highest-priority components from §3 (NumberLine, ClockSet,
   PesoMoney, SortOrder, GridArea, FractionModel, FractionShade,
   TenFrame, PatternSequence, ShapeBoard).
3. **Read `repro_crashes.json`** as a stream (it can be ~5 MB); for each
   entry, re-trigger the crash via `_pg_run` and run the runtime assertions.
4. **Run the matrix** `(node × formatter × profile)` for a 10-node pilot
   (the 10 most-difficult nodes per `latest_audit_report_summary.md`).
   Expand to all nodes after pilot passes.
5. **Wire CI**: add `npm run audit:frontend` bound to
   `node frontend/audit/run_audit.mjs --ci`, gated by a `slow` marker
   in `tests/pytest.ini`.

---

## Section 9: Findings log format

Every finding is logged as a single JSONL row in
`local_only/scratch/oc/frontend_repro_findings.jsonl`:

```json
{
  "component": "SortOrderInteractive",
  "file": "frontend/src/components/VisualSkeletons.jsx",
  "line": 2171,
  "check": "A_no_onAnswer_on_mount",
  "node_id": "mat_g2_na_q1_4",
  "seed": 3001,
  "formatter": "sort_order",
  "profile": {"number_difficulty": 0.5},
  "expected": "no /submit fetch before drag",
  "actual": "/api/practice/submit fired 12ms after mount",
  "status": "FAIL",
  "severity": "critical",
  "grader_route": "/api/practice/submit",
  "verified_at_commit": "<git-SHA>",
  "fix_owner": null,
  "verified_by": "<agent name>"
}
```

Findings are deduplicated by `(component, check)` for the §10 dead-code and
config findings; runtime findings keep their (node, seed) provenance for
deterministic re-trigger.

---

## Section 10: Dead code / orphaned component disposition

Three React components are not reachable from the normal render path:

| Component | `renderUtils.jsx` dispatcher case? | Backend `visual_type` emitter? | Disposition |
|---|---|---|---|
| `EstimationGateInteractive` | No | No | Delete unless a future formatter needs it; log under §10 |
| `RuleDiscoveryInteractive` | Yes (`RuleDiscovery`) | No | Either remove the dispatcher case or wire a backend emitter — log under §10 |
| `ConstraintSatisfactionInteractive` | No | No | Delete unless needed; log under §10 |

For each, the audit decision is binary:
- **Delete**: verify no code path imports the export outside of `renderUtils.jsx`
  and the file.
- **Wire**: add the missing dispatcher case (or backend emitter) before
  closing the audit; the wired component must then pass all §3 checks.

---

## Section 11: Run order (operator checklist)

1. **Pre-check**: clear bytecode cache; confirm Vite dev server can boot
   (`npm run dev`); confirm backend boots (`venv/bin/python -m uvicorn
   backend.app.main:app --port 8000`).
2. **Run the backend auditor** (per `docs/generator_testing_strategy.md`):
   `bash tests/run_checklist_audit.sh`. Confirm
   `local_only/scratch/oc/checklist_audit_report.json` and `repro_crashes.json`
   are fresh (check mtime).
3. **Run the frontend audit**: `node frontend/audit/run_audit.mjs` (when built)
   against fresh `repro_crashes.json`. Write
   `local_only/scratch/oc/frontend_audit_report.json` and
   `frontend_audit_pass_register.md`.
4. **Triage findings**:_items with severity `critical` must be fixed before any
   other work; `high` next; `medium` may ship with honor-system tracking.
5. **Re-verify per fix**: after fixing a finding, re-run only that
   `component × check` to flip its status to PASS in the pass register;
   update `verified_at_commit`.
6. **Close the audit**: when `frontend_audit_pass_register.md` shows 0 FAILs
   across all 22 components and 10 text branches, speak "Praise God" and
   document the closure in
   `local_only/scratch/oc/CHECKLIST_AUDIT_BUG_FIXES.md`.

---

## Section 12: Relationship to `docs/pgen_checklist.md`

This audit exists to enforce `docs/pgen_checklist.md`'s rules on the
frontend layers that the backend auditor cannot see:

- **§3 (Formatters)** — *Functional Integrity*: "The DNA must execute without
  errors for every formatter it claims compatibility with... Must also adhere
  to difficulty dimensions and variants. Must display visuals cleanly and have
  answer fields." This frontend audit enforces *display visuals cleanly and
  have answer fields* per component (§3 of this doc).
- **§3 (Visual Compatibility)** — "Ensure purely visual formatters correctly
  bypass or gracefully handle contextual variants (like word problems) that
  they are incompatible with." The runtime harness (§8) asserts the visual
  branch at `QuestionRenderer.jsx:60` does not render a word-problem stem when
  the formatter is visual.
- **§4 (Comprehensive Coverage)** — "The generator directly addresses EVERY
  aspect of the written MATATAG learning competency." The grader-contract
  round-trip (§5) is the practical enforcement: if the grader cannot grade the
  correct answer, the generator's claim of competency fulfillment is broken.
- **§4 (Vocabulary Gating)** — "All text, instructions, and concepts used are
  strictly grade- and quarter-appropriate." This audit's §7 (i18n chrome)
  extends vocabulary gating to the frontend chrome.

When the backend auditor adds a new category, add a corresponding row to §1's
matrix or §4's branch list here so the frontend side is audited too.

---

## Appendix A: Glossary

- **node** — a MATATAG curriculum subject-grade subdomain-quarter bundle
  (e.g. `mat_g3_na_q4`) holding related learning competencies.
- **lc** — learning competency, a specific node-component
  (e.g. `mat_g3_na_q4_1`).
- **pg** — practice problem generator; the pipeline (axes → DNA → compatibility
  → Lab → portal) that produces a `FormattedProblem` for a student.
- **formatter** — a problem-type module (MCQ, cloze, number-line-read,
  fraction-shade, etc.) in `backend/app/practice_gen/formatters/`.
- **visual_type** — a short string (`"NumberLine"`, `"BarChart"`, etc.)
  emitted by a visual formatter that drives the frontend dispatcher in
  `renderUtils.jsx`. Distinct from the formatter name
  (`number_line_read`, `bar_chart_read`, etc.) used in compatibility tables.
- **DNA** — the difficulty-pyramid generator for a node; selects operands
  based on a scalar. Each node has one DNA
  (e.g. `backend/app/practice_gen/dna/na/subtraction.py`).
- **auditor** — `tests/exhaustive_checklist_auditor.py`; the backend
  correctness gate. This document is the frontend analog.
- **harness** — the runtime Puppeteer-driven verification at §8.
- **pass register** — `local_only/scratch/oc/frontend_audit_pass_register.md`;
  the single authoritative status table; supersedes the two stale
  `visual_components_audit.md` snapshots.

## Appendix B: File map

| Path | Role |
|---|---|
| `docs/frontend_audit.md` | This document. |
| `docs/pgen_checklist.md` | The checklist the backend auditor enforces. |
| `docs/generator_testing_strategy.md` | Backend auditor operating manual; references this file. |
| `backend/app/services/orchestrator.py` | The orchestrator; sets `problem.dna_name` for per-DNA checks. |
| `backend/app/practice_gen/compatibility.py` | `FORMATTER_VARIANT_SUPPORT` + `FORMATTER_NUMERIC_LIMITS`. |
| `backend/app/practice_gen/adapter.py` | Per-formatter routes (`_FORMATTER_ROUTES`); `interaction_mode` + `answer_collection` defaults. |
| `backend/app/practice_gen/formatters/visual/fmt_*.py` | The visual formatters; each emits a `visual_type` string. |
| `backend/app/practice_gen/schemas/visuals.py:113` | `VisualSchemaRegistry.SCHEMAS`; validated by the auditor only. |
| `backend/app/routes/practice_router.py:861` | Portal grader `/api/practice/submit`. |
| `backend/app/routes/matatag_router.py:960` | Lab v1 grader. |
| `backend/app/routes/matatag_router.py:1347` | Lab v2 grader. |
| `backend/app/routes/matatag_router.py:1191` | Lab config save route. |
| `backend/app/routes/practice_router.py:530,766` | Portal routes reading `CompetencyConfiguration`. |
| `backend/app/models.py` | `CompetencyConfiguration` table model. |
| `frontend/src/components/VisualSkeletons.jsx` | The 22 visual components. |
| `frontend/src/components/QuestionRenderer.jsx` | The 10 text-render branches + visual dispatch. |
| `frontend/src/components/NumberBondInteractive.jsx` | Dedicated NumberBond file. |
| `frontend/src/utils/renderUtils.jsx` | The 21-case `visual_type` dispatcher. |
| `frontend/src/App.jsx` | `fetchLabConfig`, `fetchMatatagQuestion`, `submitMatatagAnswer`, `handleAnswerSubmit`, language toggle. |
| `frontend/src/views/PracticeView.jsx` | Hardcoded English chrome (Submit/Next/Correct strings). |
| `frontend/audit/run_audit.mjs` | (To be built per §8.) The runtime harness. |
| `frontend/audit/correct_answer_emitters.mjs` | (To be built per §8.2.) Per-formatter emitter table. |
| `local_only/scratch/oc/frontend_audit_report.json` | Harness output. |
| `local_only/scratch/oc/frontend_repro_findings.jsonl` | Per-finding reproducible entries. |
| `local_only/scratch/oc/frontend_audit_pass_register.md` | The authoritative status table. |
| `local_only/scratch/oc/checklist_audit_report.json` | Backend audit output (consumed as input). |
| `local_only/scratch/oc/repro_crashes.json` | Backend crash repro queue (consumed as input). |
| `local_only/scratch/oc/CHECKLIST_AUDIT_BUG_FIXES.md` | Cross-reference session log. |
| `local_only/scratch/visual_components_audit.md` | **Stale** — superseded; keep read-only for diffing. |
| `local_only/scratch/oc/visual_components_audit.md` | **Stale** — superseded; keep read-only for diffing. |

## Appendix C: First-render guard pattern (canonical fix)

For every component flagged with **A** (state overwrite on mount), apply this
canonical fix before close-renting the audit:

```jsx
export function ExampleInteractive({ params, onAnswer, disabled }) {
  const hasInteractedRef = useRef(false);

  useEffect(() => {
    if (onAnswer && !disabled && hasInteractedRef.current) {
      onAnswer(currentAnswer());
    }
  }, [currentAnswer, disabled]);

  const handleInteraction = (newVal) => {
    hasInteractedRef.current = true;
    // ... mutate state
  };
  // ...
}
```

The guard is `useRef(false)`, flipped to `true` *only* on a genuine user
interaction (click, drag, change), and gated inside the `useEffect` before
`onAnswer` is called.

**Do not** use `useRef(true)` (the inverse) — it flips the semantics and
fires `onAnswer` on the first render. The first-written audit doc
(`local_only/scratch/oc/visual_components_audit.md:82-83`) mistakenly
suggested `useRef(true)`; the canonical pattern is `useRef(false)`.