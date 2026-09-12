# Phase 2 hardening completion plan

**Species: explainer / implementation plan.** Revised 2026-09-12 after an independent review of
this document, incorporating the owner rulings recorded in steps 2, 3A, 3B, 5A, 6, 8A and the M3
cut. Earlier design decisions stand except where a ruling supersedes them.

This document describes work to implement; it does not claim that proposed checks exist or change
today's contracts. Binding changes
ship with their enforcement, tests, and [contract](pgen_contract.md) updates in the same commit,
following [DOC_RULES](DOC_RULES.md). The historical plan's “Phase 2 — Wire feasibility” is a
different numbering scheme; here Phase 2 means the agent-authored judgment phase in
[`_manifest.CHECK_PHASE`](../backend/app/practice_gen/validation/_manifest.py).

## Outcome and accepted decisions

The completed pipeline answers three questions with earned evidence: does each problem serve
its exact MATATAG learning competency; are its language and cognitive demands appropriate for
the learner's grade and quarter; and is the complete problem logically coherent and plausible
in its own context? Correct arithmetic does not rescue a story with impossible containment,
incompatible actions, contradictory quantities, broken causality, or unclear referents.

1. One review programme, one packet format, and one evidence-validation system. Keep the six
   existing judgment facets. Clause-level evidence supports `competency_fulfillment` and
   `comprehensive_coverage`; there is no seventh overlapping narrative facet.
2. The hardening work has two internal milestones: **M1 establishes and proves the consolidated
   system without losing the unresolved queue; M2 fixes the content and earns fresh independent
   reviews.** M1 is an engineering milestone, not pg completion. The content completion gate
   remains full `run_all` exiting 0 with all required judgment artifacts filed.
3. **Release promotion is out of scope for this document** (owner ruling 2026-09-12). `H-09` stays
   open and recorded in the status ledger; staging/production separation, canaries, telemetry,
   alerting and rollback are raised separately once M1 and M2 land. None of them gates content
   correctness, and carrying them here obscured the plan's actual blockers. The 2026-08-12 decision
   that removed pg validation from deployment is left standing for now, to be revisited on its own.

The implementation preserves curriculum requirements, owner rulings, and existing behavioral
protections. No lower census floors, increased finding allowances, blanket task exemptions,
invented PASS evidence, or changes to `requires_ignore` are part of this plan. Meaningfully
port existing tests to the surviving checks; add coverage for newly closed holes. Any actual
ground-truth correction follows AGENTS.md Protocol 5 and records the node, source, and reason.

## Evidence and current implementation state

All observations share git HEAD `c007b8ae`, but they do not describe one tree. Early probes ran
before the current uncommitted implementation; later measurements ran with 23 modified or
untracked paths. The snapshot column prevents a working-tree result from masquerading as evidence
for the commit. None of the partial work below is release evidence until it is reviewed, divided
into coherent contract/enforcement commits, and re-proved on a clean integration revision.

| Observation | Measured result | Snapshot |
|---|---|---|
| Legacy requirement inventory | 776 required pairs; 787 loaded pairs; 11 historical-only; 68 unresolved-content pairs | Existing `requirement_inventory.json`; stale, generated with only 3 dirty paths |
| Legacy assertion inventory | 104 assertions; 76 mutations; 39 allowlisted unproven assertions | Existing `assertion_migration.json`; stale, generated before the 79-mutation tree |
| Current fast unit collection | 473 selected / 475 discovered; 2 slow tests deselected | Current working-tree bytes |
| Current mutation corpus | 79 records; all 79 `detected: true`; all 79 `phase1_admissible: true`; proof evaluation reports 0 errors | Current working-tree bytes, not a clean commit |
| Current unproven assertion inventory | 39, including major content-correctness checks | Current working-tree bytes |
| Current census minima | 468 unit tests; 79 mutations; 151 nodes; 975 variant candidates | Current working-tree bytes |
| Current Phase 2 execution | 484 judgment problems; 217 capability problems (67 contradicted, 76 stale, 74 unadjudicable) | Current working-tree bytes |
| Current Phase 1 execution | Reached §10 only after earlier stages passed, then crashed on external Neon DNS before coverage/census | Current working-tree bytes |
| Current frontend execution | Build passes with an oversized-chunk warning; lint has 225 warnings; browser script crashes under ESM and has no assertions | Current working-tree bytes |
| Packet discrepancy | `mat_g1_na_q1_2`, seed 42: attester includes PlaceValueBlocks; judgment omits visual fields | Early review probe |
| Freshness hole | Same node/seed: corrupt recorded visual fields produce no judgment freshness error | Early review probe; still open |
| Clause-schema hole | Adding a seventh required facet in memory accepts an empty clause map | Early review probe; still open |
| Declaration-only mutation-proof hole | A synthetic assertion once counted as proven without execution | Early review probe; closed provisionally by `mutation_proof.py` and 79 executed records |

Three implementation slices already exist in the dirty tree and need integration review:
`tests/phase2_migration.py` plus its two reports implement a first version of step 0;
`validate_language.py`/§1J and `validate_options.py`/§1K implement the first two bounded
lints in step 3; and `mutation_proof.py`, `tests/isolated_corpus.py`,
`tests/mutation_harness.py`, `validate_coverage.py`, and
`validation_reports/mutation_proofs/` implement most of step 4. The proof corpus also shows
that `mcq_reviewed_without_options`, formerly blocked by the red live review corpus, is detected
against the isolated corpus and is Phase-1 admissible.

Graphify's local query identified the mutation/packet/validator connections but warned of
pre-#1504 node IDs and possible same-name collisions. Revalidate source locations and callers;
use the MCP when available and the local graph/CLI otherwise. Do not treat graph edges as
execution evidence.

## Review conclusion: current deployment blockers

The existing pipeline has useful breadth, but a green subset cannot presently certify a new
grade or a production release. These are the blocking findings the implementation closes. The
IDs are planning handles for the evidence ledger, not new contract references.

| ID | Finding | Required closure evidence |
|---|---|---|
| `H-01` | Phase 1 is not hermetic. `validate_grade` opens the configured database and the aggregate run aborts on DNS; generation and grading gaps can be skipped. | In-memory or isolated transactional grader fixture; planted accepted-wrong and rejected-correct answers; full Phase 1 completes without network or persistent student state. |
| `H-02` | Thirty-nine assertions are explicitly unproven, including concept gating, answer recomputation, monotonicity, maximum reach, vocabulary, interest, render schema, grading floor, KG monotonicity, and Lab/portal equivalence. | A current detected mutation for every content/release-critical assertion; any inherently non-mutable check has a narrow, owner-approved limitation and independent executable control. |
| `H-03` | The runner can lose the final summary and its two-direction evidence when a stage raises. Several validators catch an import/generation error and continue, so attempted work can be reported as coverage. | Stage ledger records scheduled, attempted, completed, failed, and crashed; exceptions become named failures; skipped obligations are failures; the non-fail-fast run reaches every independent stage and exits nonzero once at the end. |
| `H-04` | “Exhaustive matrix” covers discrete formatter combinations, but continuous axes are swept separately and serving context, experience, interest, renderer, and response mode are not one finite obligation model. | Machine-generated obligation manifest from the student route; exhaustive finite partitions for reachable state, including cross-axis boundary classes; zero missing, skipped, or unexpectedly unreachable obligations. |
| `H-05` | Vocabulary, interest, DNA, compatibility, render, and grade checks contain narrow representatives, first-DNA selection, low sample counts, G1–3 assumptions, tolerated floors/warnings, static approximations, or silent import paths. | Scale-safe checks over every applicable node/DNA/formatter/grade and final rendered output, with exact types, robust multi-digit grade parsing, real prerequisite edges, and named mutations on the live path. |
| `H-06` | Phase 2 evidence omits complete visuals/options in places, freshness does not bind every learner-visible field, and requirement evidence can be incomplete if clause extraction itself omitted curriculum text. | Canonical full-view packet and replay digest; full competency-to-requirement decomposition review; exact clause coverage; missing learner-visible evidence is unadjudicable and blocking. |
| `H-07` | The six facets do not yet force explicit judgments about contextual/logical validity, ambiguity, feedback/hints, misconception quality, interaction clarity, or accessibility. A mathematically valid item can therefore pair impossible objects, containers, actions, units, or causal relationships. Identity fields alone do not establish independent review quality. | Per-sample contextual-validity evidence inside the existing facets; bounded semantic-role/affordance checks; calibrated blind reviewers; dispatch-bound receipts; targeted dual review/adjudication; and cited student-view evidence. |
| `H-08` | Nothing executes the React components. §9 checks that a payload carries the keys a component reads, but never renders it, so a component that throws, ignores a conditional key, or draws an empty box passes every gate. The existing script is inert: CommonJS in an ESM package, an uninstalled Puppeteer import, unavailable bare `python`, Vite development mode, no assertions. | **No browser** (owner ruling). Headless `renderToStaticMarkup` over every registered component on real student-path payloads; component × payload-class behaviour tests including the `onAnswer` → `answers_match` round trip; results consumed by `run_all` as a digest-bound artifact; planted defects detected by name; pointer-drag geometry on two components recorded as an unproven blind spot. See step 5A. |
| `H-09` | Production deploys automatically from `main`, backend uses `:latest`, and neither workflow binds the deployed artifacts to Phase 1, Phase 2, mutations, browser results, or review evidence. | Staging/production separation, immutable SHA/digest artifacts, an attested release manifest, protected production promotion, canary replay, monitoring and tested rollback. |

The active status ledger is
`validation_reports/phase2_hardening/hardening_status.json`; do not revive the historical
per-tick narrative in `validation_reports/hardening_ledger.md`. Each H-row records
`id`, `status`, `owner`, `affected_assertions`, `baseline_evidence`,
`acceptance_checks`, `proof_artifacts`, `closing_revision`, and `updated_at`.
The first integration step creates and schema-validates those nine rows. Finding counts can
grow as stronger gates expose defects; a smaller count is not evidence of progress by itself.

## M1 — Build and prove the consolidated system

### 0. Establish a reproducible baseline and complete migration inventory

Begin with an integration checkpoint for the current dirty worktree. Review every diff and group
the existing work into coherent commits; binding behavior, its contract row, tests, and mutation
proof machinery move together. Do not commit unrelated generator changes merely to obtain a clean
tree. After the final integration commit, require a clean status, re-run the complete mutation
table, and regenerate both step-0 inventories. The existing reports are useful prototypes but
cannot be accepted because they describe 76 mutations and an earlier dirty-path set.

Record checkout and working-tree state, runtime versions, commands, explicit seeds/profiles,
unabridged failures, collected test IDs, mutation names, and assertion inventory. Execute
Phase 1, Phase 2, and the full mutation table sequentially; mutation runs modify files and
are not safe to overlap with another mutation run, validation, or content editing.

Review and retain `tests/phase2_migration.py` as the permanent migration/audit entry point,
with machine-readable reports in `validation_reports/phase2_hardening/`. Promote any remaining
useful probes from scratch into that tooling; do not make permanent evidence depend on
`local_only/` files.

Regenerate a row for every current `(node_id, requirement_id)` from the declarations actually
validated by the pipeline. Join all relevant old reviews and the existing winning-verdict
selection, retaining source file, packet/sample identity, author, date, verdict, and reasoning.
Account separately for historical pairs no longer required. Capture the entire old finding
inventory: contradictions, missing evidence, staleness, provenance, and integrity defects.

Each row receives an explicit state: unresolved content, missing review, stale/unadjudicable
evidence, current earned evidence, or historical-only with its existing ruling. These states
describe debt; they never substitute for a passing review. Capture all 776 baseline pairs,
not just the 67 contradictions. New requirements automatically add rows; unexpected removals
fail reconciliation and require an existing authorized ground-truth explanation.

Regenerate the assertion/test migration table with one row per existing assertion and mutation,
including each behavior within a shared label: current entry point, future entry point,
positive control, violating fixture, expected marker, and disposition. Resolve unproven
content-correctness checks before clearing the queue they purport to guard.

Inventory every warning, `continue`, exception handler, sample cap, floor, allowlist, exclusion,
and “not judged/not gated” branch in the harness. Each receives one of three dispositions:
remove it by checking the obligation, turn it into a named failure, or record a narrow inherent
limitation with an owner, scope, mitigation, and expiry/review trigger. Release-critical content,
grading, rendering, coverage, and evidence paths have no warning-only or silent-skip outcome.

### 0A. Make Phase 1 hermetic, complete, and honest before repairing content

Refactor `run_all` around an explicit stage registry and result record. Each scheduled stage
records its phase, contract references, command/input digest, start/end state, and named findings.
Run independent stages behind exception boundaries so a crash is a failed stage and does not
erase coverage/census/two-direction results. `--fail-fast` may stop after recording the failure;
the default audit continues through every independent stage. The two-direction check compares
the declared schedule with attempted and completed stages, so a crash cannot remove its own
expected references. Prove missing registration, wrong phase, crash, and unattempted-stage paths.

Make grading local and deterministic. Use an isolated in-memory or rolled-back database fixture,
create no persistent shared learner, and forbid network access. For every reachable response
contract, generate explicit-seed items and submit a known-correct answer, known-wrong answer,
malformed answer, and representation-equivalent answer where the contract permits one. Exercise
all production grader entry points and assert both acceptance and refusal; an always-true grader
and an always-false grader each have a detected mutation. A generation failure or unrenderable
answer is a named `(node, DNA, formatter, profile, seed)` obligation failure.

Strengthen the current Phase 1 modules against that manifest:

- DNA checks exercise every declared grade and profile, parse multi-digit grades, use exact typed
  comparisons, and treat invalid distractors as failures. Feasibility exclusions come from the
  same production gate and are proved in both directions.
- Compatibility checks cover KG→registry and registry→KG, every used and unused compatibility
  declaration, actual prerequisite edges, true reverse refusal, and behavioral Lab/student-portal
  equivalence. Existing reachability/dangling floors are driven to zero or justified by an owner
  ruling before production.
- Vocabulary and concept checks run every applicable DNA and final formatter output. Import or
  provenance loss fails. The vocabulary universe comes from the whole ordered KG; current-node
  introductions are allowed, later introductions are refused, and secondary DNA mappings receive
  the same audit.
- Interest checks run every applicable node/DNA and supported theme, prove that the theme reached
  learner-visible context, and compare mathematical invariants on the final problem. A missing or
  ignored theme is a failure rather than vacuous invariance.
- Language/options checks classify every produced domain as checked or unproved. Count/noun/verb
  agreement covers text and visual labels. Choice validation includes displayed identity, exact
  semantic equivalence, and exactly one answer satisfying the requested representation.
- Render checks validate conditional as well as unconditional component keys, then execute every
  component headlessly per step 5A. Grade checks consume the same rendered answer contract.
  Payload-only inspection remains a fast diagnostic and does not stand in for an executed render.

Update each affected contract row and validator limitation with the enforcing change. Before the
content queue is edited, run every new or strengthened check against a clean control and a planted
violation that reaches the production entry point. M1 cannot pass while a content-correctness
assertion remains in `UNPROVEN_ASSERTIONS`.

### 0B. Build and budget the student-path obligation manifest

First enumerate without generating. Derive only combinations reachable for each node through the
production registries and gates; do not multiply every node by every DNA, formatter, or interest
when production cannot select that pairing. The report
`validation_reports/phase2_hardening/obligation_budget.json` records counts by node, DNA,
formatter, discrete profile, continuous boundary/equivalence class, experience, theme/context
family, renderer, and response mode. It also names rejected combinations and the production rule
that makes each unreachable.

The current §1C filtering yields a lower bound of 4,325 allowed
`(node, DNA, formatter, discrete-assignment)` obligations across 463 node/DNA/formatter pairs.
Five seeds per obligation means 21,625 generated problems; ten means 43,250. Execute that volume
in the Python/backend harness, where problems can be generated and checked without browser startup,
DOM work, screenshots, or network round trips. Continuous/context/experience crossings in the
completed manifest can only increase that count. Do not multiply the same corpus through the
frontend. The frontend layer has a different equivalence relation, defined in step 5A: component ×
payload class, not node × formatter × variant — a component's behaviour is a function of its
params, not of which competency produced them.

Benchmark 1,000 representative obligations before finalizing the executor. Record median and
p95 time, memory, projected serial/parallel runtime, shard count, and cache keys. Initial
operational targets on the documented four-core reference runner are at most 30 minutes for the
pull-request tier, at most 30 minutes per release shard, and at most four hours wall time for all
release shards. Exceeding a target triggers caching, sharding, or generator optimization; it never
drops a required obligation or substitutes pairwise sampling for an exhaustive finite contract.

The pull-request backend tier runs every changed obligation plus fixed cross-family sentinels and
reports that it is partial. The release backend tier executes the complete manifest with the
required 5–10 deterministic seeds per obligation. It enumerates the Cartesian product of reachable
finite variants. Continuous domains declare curriculum-derived boundary and equivalence classes,
and those representatives cross the applicable finite dimensions.
Unpartitioned infinite behavior stays explicitly unproven. Each obligation is executed or rejected
by the production route for a named contradiction; candidate filtering, acceptance budgets, and
random misses cannot turn an obligation into a pass.

Acceptance for `H-04`: enumeration is deterministic; two independent derivations agree on the
reachable count; deletion of a route, profile, boundary class, context family, or response mode is
caught by name; every release shard is complete and non-overlapping; their union equals the
manifest; and the complete measured run meets the budget or has an approved optimization plan
before content repair proceeds.

### 1. Define the merged evidence record and lossless filing path

Implement a versioned judgment record with the following structure. Field names below are
the planned schema; none is an additional pedagogical facet.

| Field | Meaning and planned enforcement |
|---|---|
| `schema_version`, `node_id` | Explicit supported version and exact registered node |
| `competency_snapshot`, `requirements_snapshot` | Exact competency, grade/quarter context, and current requirement IDs/clauses; compare to live ground truth |
| `packet_digest`, `sampling_version` | Bind review to the actual delivered packet and sampling policy |
| `samples_reviewed` | Complete canonical reviewer-visible content, with replayable sample identities |
| `sample_assessments` | Per-sample checks for mathematical validity, contextual/logical validity, ambiguity, and learner-facing clarity; every delivered sample receives an explicit verdict and reasoning |
| `clause_evidence` | Exactly one entry for every required ID, without unknown or duplicate entries |
| Each clause entry | PASS/CONCERN/FAIL, reasoning, supporting `sample_ids`, reviewer and dispatch attribution |
| `findings` | The existing six verdicts/rationales; the two coverage/fulfillment facets reference the clause entries |
| `overall` | PASS only when all six facets and all required clause verdicts are PASS |
| Dispatch provenance | Delivered-packet digest, reviewer identity, date, blind-review declaration, and exact returned response reference |

A PASS clause cites at least one sample in the delivered packet that the independent reviewer
judges to exhibit it. A seed existing somewhere in the node is insufficient. A requirement
with several named subcases has evidence for those subcases, or receives CONCERN/FAIL. Do not
permit “unknown,” missing data, or an unobserved requirement to become PASS by default.

Before clause verdicts are accepted, the reviewer also checks that `requirements_snapshot`
losslessly decomposes the complete MATATAG competency. This is a schema prerequisite within
`competency_fulfillment`, not a seventh facet. A missing verb, object, range, representation,
subcase, or construction/recognition distinction makes the packet unadjudicable and blocks PASS.
Prove omission, duplication, altered wording, and unknown-clause paths against the full original
competency text; otherwise a perfect review of an incomplete declaration can still certify less
than the curriculum requires.

Every reviewed sample receives a contextual/logical-validity verdict within
`competency_alignment` and `cognitive_capacity`. The reviewer checks that entities can
reasonably participate in the stated action; objects fit their container or location; units and
attributes belong to the object; quantities and state transitions agree; pronouns and referents
are unambiguous; cause precedes and supports the result; and the situation is familiar enough
that implausibility does not distract from the intended mathematics. For example, “Mary put two
fruit bowls in her wallet and took one fruit bowl out” fails even if the subtraction and keyed
answer are correct. One invalid sample makes the node review non-PASS until the shared cause is
fixed and affected evidence is renewed.

Validate clause reasoning individually for presence, provenance, and template reuse; top-level
rationales do not stand in for clause reasoning. Preserve the old clause-level skeleton
threshold and provenance behaviors. Separate literal citations from hypothetical remediation
text so quote checks do not misclassify a proposed future example as observed evidence.

Extend `tests/judgment_batches.py` and implement a merged filing helper under `tests/`.
The helper joins reviewer responses to opaque packet item IDs, copies the exact delivered
samples, rejects missing/duplicate/foreign responses, and never authors or upgrades a verdict.
Retain the old filing helper's checks before retiring it.

Preserve both existing review-capacity protections: at most 25 nodes per reviewer identity
and at most 25 clause verdicts per blind dispatch. Plan batches by both limits. A future node
with more than 25 clauses uses several attributed dispatches and one consolidated node record;
it does not gain a larger exemption. The final node review references the complete clause
set. One programme does not promise exactly one dispatch regardless of content size.

Keep generator authors and independent reviewers separate. Reviewers receive the exact
competency, grade/quarter context, clauses, and rendered evidence; no generator source,
provider claims, previous verdicts, or defect-finding prompts. Preserve opaque mapping for
clause review. Independence remains a process property that identities alone cannot prove;
retain dispatch receipts and document that limitation.

Qualify the review process with a hidden calibration set containing known clean examples and
planted pedagogical defects, including mathematically correct but contextually impossible
stories. A reviewer/dispatcher identifies the defect class and cites the
right evidence before live verdicts are admissible. New capability types, construction tasks,
and high-risk interactive items receive two independent reviews with adjudication on
disagreement. Bind dispatch receipts and raw returned responses to packet and response digests;
self-declared reviewer names or blindness flags alone do not establish custody or independence.

### 2. Unify rendering, sample coverage, and freshness before retiring packets

Use one canonical sample renderer for packet construction, filing checks, and freshness,
explicitly on the student serving path. Reuse `_stratified_seeds` as the starting coverage
algorithm, not as a claim of exhaustive semantic coverage.

Make a sample's replay identity explicit: node, seed, requested difficulty profile/variant,
formatter constraints, experience, and serving mode. Record effective output choices too.
Existing reserved seed ranges can be decoded for legacy replay; new records do not depend
on seed arithmetic alone to describe a requested profile. Do not force unreachable variants
and then count them as capabilities students can receive.

Canonical content includes stem, resolved answer value, options, hint, cloze template,
visual type and full visual payload, and relevant response/interaction configuration.
Preserve False/0/missing distinctions and existing answer-slot equivalence tests. Pure option
reordering is equivalent only where presentation order is not part of the task; an ordered
or position-referenced task retains its observable order. No truncated visual excerpts as
the stored evidence of record.

For visual/interactive competency claims, reviewers receive a **textual description of what is
actually drawn**, browser-free. Today `_render_sample` reduces every sample to `seed`, `formatter`,
`question_text`, `correct_answer`, `options`, `hint`, `cloze_text` — **no visual fields at all**.
That is this document's own "judgment omits visual fields" and "corrupt recorded visual fields
produce no freshness error" rows, and the direct cause of `comprehensive_coverage` being scored PASS
twice on a number line that drew nothing: on a text-only surface, a stem *saying* "equal jumps" is
indistinguishable from a picture that draws them. A payload naming a drawing tool does not
demonstrate that a pupil can draw with it. Four constraints, in order of importance:

1. **Derive the description from the RENDERED OUTPUT, never from the payload.** `jump_count` and
   `jump_size` are read inside a branch and §9 enforces unconditional keys only, so a payload can
   carry its jumps while the component's guard fails and draws none. A payload-derived description
   would report "3 equal jumps of 5"; a render-derived one reports "no jump marks drawn". Describing
   the payload would rebuild the exact illusion this closes, and would be a second model free to
   drift from the component.
2. **One renderer, two consumers.** Parse the description from the step 5A static render, so packet
   construction, filing checks and freshness all read the same artifact rather than a third path.
3. **Emit countable structure, not only prose** — element counts, grid dimensions, tick counts,
   distinct labels and colours, group sizes. "A 4×5 grid of 20 unit squares, 12 shaded" is
   judgeable; "a grid of squares" is not. This is what makes `scale_appropriateness`'s visual-density
   subcriterion answerable at all.
4. **The describer is itself a check and carries its own mutation.** Plant a drawn element the
   description omits and confirm it is caught. An unproven describer feeding Phase 2 is worse than
   none, because it manufactures reviewer confidence.

Bind visual evidence to its sample and renderer inputs/version; relevant frontend changes invalidate
it even if backend text stays identical. **Named limit, recorded in the packet docstring, the
contract row and the reviewer guidance:** a textual description cannot carry crowding, overlap,
colour contrast, or real touch-target size. Those are answerable only to the extent constraint 3
quantifies them, and a clean description is never evidence of a clean layout.

Freshness checks compare the complete reviewed content, current competency/requirements,
sampling policy, and required sample identities. Additional historical samples cannot replace
a newly required sample. Missing visual or option data is unadjudicable evidence, not absence
of drift. A changed requirement cannot inherit its old PASS under an unchanged ID.

Audit `_stratified_seeds`, `_seed_renders`, `_try_render`, and their callers for the existing
catch-and-skip paths. Replace silent candidate loss with named reproducible failures. Derive
coverage obligations from the current allowed formats, discrete variants, and relevant numeric
boundaries; record obligations, attempted seeds, and gaps. Fixed budgets can bound work but
cannot silently turn unobserved obligations into completed coverage. Finite sampling does not
prove universal correctness; state its domain and limits in the docstring, contract, and log.

**Fix the sample allocation before step 7 dispatches anything.** A review campaign run on today's
allocation structurally cannot see cases the reviewer is being asked to judge. Each node currently
gets at most 19 samples in four **disjoint** groups — 5 base seeds with nothing pinned, ≤5
format-stratified, ≤3 max-difficulty with every continuous axis at 1.0 at once, ≤6 variant-coverage
with one discrete variant pinned. Formatter coverage is genuinely stratified and was designed; the
other dimensions were not. Measured 2026-09-12:

| Gap | Measurement | Fix |
|---|---|---|
| **Interest/theme has zero allocation** — the dimension that generates the *story*, and therefore drives both contextual coherence and language appropriateness | `interest` appears **0 times** in `judgment_packets.py`, although `pipeline.run()` already accepts `student_interest` | Pin 3 interest buckets per node: a themed interest, a contrasting theme, the neutral default. **One parameter.** |
| **30% of declared variants are permanently unreviewable** | 975 candidate `(variant, value)` pairs across 151 nodes against a cap of 6; **68 nodes exceed it**, leaving **292 pairs no packet can ever contain**. §7's census floor counts *candidates*, not coverage, so it cannot notice | Remove the cap so all 975 are reachable (+292 samples) |
| **Continuous difficulty has two points, not a range** | the auto-path default and all-axes-at-1.0; never one axis at a time, so "which axis made this too hard" is unobservable | Add a mid point; make max per-axis |
| **`experience` is never varied** | `run()` accepts it; the packet builder never passes it | Cover the reachable experiences |

That yields roughly 28 samples per node, about 4,200 tree-wide. **Named limit:** the groups remain
marginal, not crossed — a visual formatter at max difficulty with a pinned variant is still only
sampled by chance. State that in the sampling docstring, the contract row and the evidence log
rather than letting the packet imply joint coverage it does not have.

Prove the seed-set freshness gate first where its baseline is clean. For other new evidence
checks, use isolated valid control corpora and planted violations through the real production
entry points before activating them on legacy records. Synthetic fixtures stay under tests;
they are never filed as genuine reviews. After activation, production migration debt remains
a loud Phase 2 failure. An already-red rollup is not evidence that a new mutation was detected.

### 3. Integrate and finish the existing §1J/§1K bounded lints

The dirty tree already contains `validate_language.py`/§1J and
`validate_options.py`/§1K, their `run_all` and `CHECK_PHASE` registration, contract rows,
zero measured baselines over 9,060 language samples and 1,180 option-bearing samples, and
detected mutations. Review and land these as one coherent contract/enforcement slice before
expanding them. Preserve their declared limitations rather than treating their current zero
finding counts as complete language or semantic coverage. Keep mechanical per-clause provision
in Phase 1; declarations/reachability do not certify semantic fulfillment.

For agreement, start with explicit count/noun constructions and shared inflection logic used
by generators. Validate actual rendered student text, including nested problem statements;
use renderer context to distinguish an intentionally quoted erroneous statement from an
accidental grammatical defect. Cover singular/plural, irregular and invariant nouns, units,
and valid expressions such as “1 less” with positive and negative controls. Unknown linguistic
constructions are a documented coverage limit, not silently classified as correct grammar.

For options, distinguish identical displayed choices, semantic equivalence, and ambiguity
under the question's requested representation. Use exact typed numeric normalization where
applicable; avoid floating-point equality and unrestricted symbolic guesses. A task asking
for a particular representation can legitimately offer equal-valued representations, but
still fails on indistinguishable choices or multiple answers satisfying that request. No
blanket representation-task exclusion. Unsupported equivalence domains remain explicitly
unproven and require judgment evidence; future formatter/domain registrations declare support
or a named limitation rather than silently bypassing the check.

For each existing lint, define its domain and valid counterexamples; add controls for every
claimed branch; fix every occurrence of a shared root cause; and keep the zero-finding gate
with current detected mutations. Do not certify an extension by planting a defect whose
expected failure already appears in its control run. These remain bounded lints rather than
complete machine tests of age-appropriate language or common sense. Vocabulary, concept
gating, cognitive load, exact LC mapping, and full narrative plausibility retain their
existing checks and Phase 2 review.

### 3A. Build contextual logic as a separately staged capability

Treat contextual logic as its own project and reserve planned contract reference §1L. The
enforcing commit adds §1L together to `CONTRACT_CHECKS`, `CHECK_PHASE`,
`docs/pgen_contract.md`, `docs/testing_pipeline.md`, its assertion inventory, controls,
and detected mutations. No §1L contract row is added while the live baseline is red.

Start with a nonbinding inventory of every context source, template/spine, and slot use. The
interest bank alone currently has 26 themes and 663 role entries (552 distinct strings) across
actors, objects, places, `item1`, and `item2`; it is not a one-session lint migration. Produce
`context_semantics_inventory.json` with each source location, live combination count, proposed
semantic role, ambiguity requiring human ruling, and migration status.

Define reusable typed roles and affordances: actor, countable object, substance, container,
location, action, measurable attribute, unit, and state transition. A template declares the
roles and relationships it requires. Prefer small composable declarations near the context
source over a blacklist of absurd sentences. Annotate and validate one closed context family
against isolated controls first, then expand family by family. Before §1L activation, every
current source and reachable template/role combination is mapped or fails the migration
inventory by name; there is no grandfathered “unknown means pass” path.

The eventual validator checks rendered combinations for plausible containment/capacity,
object/action compatibility, attribute/unit compatibility, consistent before/action/after
quantities, and declared causal/reference relationships. Prove it through the production
renderer with a planted “two fruit bowls in a wallet, take one out” violation, valid fruit/basket
and coins/wallet controls, and incompatible action, unit, and state-transition mutations.

Acceptance for §1L: inventory has zero unmapped live sources; clean isolated controls pass;
each declared violation is detected by name; the full live baseline has zero findings before
the contract row activates; mutation proof is current; and Phase 2 packets cover every context
family. Subtle common-sense, cultural, and narrative coherence remains mandatory per-sample
judgment rather than being silently inferred from §1L.

### 3B. Generalize the clause→payload rule table

`tests/unit/test_media_the_competency_names.py` already asks the question that neither §9 nor §1G
can: does the picture depict **the thing the clause names**? It pins that the number line draws its
jumps and that `emoji_pictorial` draws the operation it is keyed to — and it lives in a unit test
precisely because the component reads `jump_count`/`jump_size` inside a branch, so the AST classes
them conditional and §9 enforces unconditional keys only.

It is a Scaling Mandate 4 stopgap: a hand-written two-node list. Generalize it into a declared rule
table, one assertion per clause family, anchored on §6's existing 776 `(node, requirement)` pairs —
"clause names equal jumps" → the payload carries `jump_count`/`jump_size` and their product equals
the keyed answer; "clause names a pictograph" → the payload carries the pictograph structure;
"the item draws countable objects" → those objects come from the problem's interest set or the
neutral defaults. Build **family by family, each activated at a measured zero** with its own control
and planted violation: a wrong assertion here is a wrong gate. Retire the two hand-written node pins
once their clauses are covered. Each rule cites the MATATAG clause it derives from and is ground
truth thereafter, editable only under AGENTS.md Protocol 5 with node, source and reason recorded.

This moves §6F's "judge the drawn artifact against the clause" — deferred under D-1 — out of agent
attestation for its **declared-feature** half. §6F keeps the judgment half.

**Its first expected finding already exists.** `fmt_emoji_pictorial.py:134` selects the emoji as
`rng.choice(_ALL_EMOJIS)` from a hardcoded 40-emoji table and **never reads interest context** —
`ctx` is consulted only for `values`, `dna_concept`, `correct_answer`, `node_id`, `seed` — while
`data/interest_bank.json` carries a per-interest `emoji` field. A pupil whose interest is `ppop`
(🎤) is shown a random 🌮. The text layer is interest-aware and the visual layer is interest-blind.
§4 `validate_interest` misses it: that is exactly the "missing or ignored theme is vacuous
invariance" hole `H-05` names. Per Scaling Mandate 5, fix the formatter first, then activate the
rule at a measured zero — do not activate the gate against a red baseline.

### 4. Make mutation coverage depend on executed evidence

The dirty tree already implements the core design in `mutation_proof.py`,
`tests/mutation_harness.py`, `tests/isolated_corpus.py`, and `validate_coverage.py`.
Current evidence contains 79 detected, Phase-1-admissible records and the proof consumer reports
zero errors. Review and land that slice; retain the rule that
`validate_coverage.proven_assertions()` consumes validated results rather than
`Mutation.asserts` declarations. Mutation executions remain serialized. This step is required
for M1 acceptance; dirty-tree records are integration evidence rather than release evidence.

The proof record includes schema version, mutation name/definition digest, asserted labels,
expected and observed markers, baseline and planted exit statuses, commands, node/seed/sample
identity, fixture manifest, environment/dependency fingerprint, and source/input digest. Bind
it to actual working-tree bytes, including uncommitted/new relevant files, not only git HEAD.
Include review/attestation fixture inputs when a tested check consumes them. Migrate all
custody mutations onto isolated deterministic review corpora, rendered through the production
pipeline and validated through the real entry points. Thus the proof bundle consumed in
Phase 1 never depends on genuine agent-authored review files. Live-corpus integration checks
remain Phase 2 work. Exclude only explicitly identified output files from fingerprints;
do not broadly exclude `validation_reports/` and accidentally omit consumed fixture inputs.

Before landing, correct `mutation_proof.py`'s stale phase-boundary docstring: it still describes
24 of 76 mutations touching genuine review corpora and being inadmissible, while
`tests/isolated_corpus.py` has moved those plants and all 79 current records are admissible.
Re-audit every named limitation against behavior whenever its implementation changes.

Reject missing, partial, stale, malformed, interrupted, survived, or unrelated-crash evidence.
Require the claimed failure absent in the baseline and present after the planted violation
reaches the real code path. Record the matching diagnostic, not merely the first unrelated
failure line. Publish completed proof results atomically only after mutation restoration and
input-digest verification. Check file restoration and preserve normal matrix reports.

Avoid recursive proof generation: `run_all` consumes completed proofs; it does not invoke the
mutation runner. Refactor mutations that use broad `run_all` wrappers to exercise their actual
production assertion entry points directly. Test the proof consumer itself with isolated proof
fixtures and controlled fingerprint inputs, then include those executions in the final proof
bundle. No public bypass flag that makes ordinary coverage validation accept stale proofs.

Test deletion of a result, changed sources/fixtures, changed mutation definitions, wrong
failure labels, dirty-tree edits, and interrupted writes. Preserve coverage inventory checks
and the shrink-only unproven allowlist. Existing allowlisted content-correctness gates remain
blockers until proved; do not reclassify new failures as “known unproven” to finish M1.

The whole-tree input digest intentionally invalidates every proof after a relevant edit. The
current 79-record run totals 716 seconds, with a 125-second slowest mutation. Run the affected
mutation while developing a check, then run the complete table after each coherent integration
checkpoint, at M1 acceptance, after the final M2 content change, and immediately before the
release manifest. Budget 15 minutes on the measured host for each full re-proof; if it exceeds
that target, record the measured time and optimize the runner rather than accepting stale proof.

### 5. Re-anchor the phase boundary and cut over without losing findings

Replace the attestation-directory-only probe with a boundary check guarding all agent-authored
review inputs consumed by the merged system. Exercise Phase 1 with those corpora inaccessible
in isolated tests, and detect forbidden reads even when they do not change today's findings.
Retain phase-registration/partition checks. Prove the new boundary by a mutation that actually
reads the merged evidence from a Phase 1 entry point; a missing symbol or dead reader is not
a successful proof. Machine-generated mutation results are Phase 1 inputs, not agent judgments;
Phase 1 can rebuild them from code and isolated test fixtures without a genuine review corpus.

Run old and new validators against controlled equivalent evidence during migration. Map every
old assertion, relevant unit test, and mutation to its surviving behavior before deleting the
old entry point. Preserve all old failure obligations, including per-clause seed provenance,
template detection, batch limits, and all freshness branches; allow additional honest failures.

Old records remain immutable historical evidence. Versioned new reviews live within the single
`validation_reports/judgment/` programme. Derive active evidence from actual filed records,
not a self-declared `supersedes` string. A newer malformed/non-PASS submission cannot expose
an older PASS as a silent fallback. Archival records do not become independently current merely
because they remain on disk. Missing new-schema reviews are reported explicitly.

Validate the migration inventory against current requirements and new evidence in Phase 2.
An old unresolved row closes only with current independent PASS evidence for that requirement
or an existing authorized ground-truth ruling. Copying an old negative verdict into a queue
is acceptable; presenting it as a new blind judgment is not. Missing legacy evidence is debt,
not permission to drop a row. Keep the reconciliation check until the entire queue is closed.

At cutover, consolidate runtime judgment enforcement into `validate_judgment.py`; retire the
attestation-only runtime, packet and filing helpers once their replacements pass. Update
`run_all.py`, `_manifest.py`, imports, assertion inventories, docstrings, and caller tests.
Port existing behavioral tests instead of reducing `CENSUS_FLOORS`; do not pad the count with
tests that merely mirror implementation. Query Graphify and search the tree for all retired
symbols, distinguishing archival citations from dangling executable callers.

Update the contract, judgment guide/schema example, and owner sequencing record together
with enforcing code. Record the accepted consolidation as superseding D-1's separate
re-attestation workflow, retaining its principle of reviewing stable content. Preserve D-2's
root-cause approach. Do not alter curriculum rulings R-1 through R-5.

### 5A. Close H-08 in Phase 1, without a browser

**Owner ruling 2026-09-12: a production-path browser gate is not feasible and is not built.**
Delete `frontend/run_servers_and_test.js` rather than repairing it — `require` in an ESM package,
Puppeteer absent from `package.json` and `node_modules`, bare `python` unavailable on this host,
Vite development mode, and no assertions. Remove `npm run test:e2e` from step 8's command block.

H-08's real content is three questions, and all three are programmatic. §9 already answers the
first and is already Phase 1 (`_manifest.CHECK_PHASE["§9"] == 1`), so nothing here moves a
frontend check *into* Phase 2 — it moves the rest of them *into* Phase 1 beside it.

| | Question | Mechanism |
|---|---|---|
| a | Does the payload carry every key the component reads? | §9 today — keys from the component AST via `tests/frontend/extract_visual_contract.mjs` |
| b | Does the component execute on that payload without throwing or drawing an empty box? | **New.** Headless static render |
| c | Does the render faithfully show what the payload declares? | **New.** Same static render, richer assertions |

**Static render.** The 22 components in `frontend/src/components/VisualSkeletons.jsx` are plain
functions of `({ params, onAnswer, disabled })` importing only `react` and `lucide-react`; every
`window.` reference sits inside a `useEffect`, which does not run under server rendering. Render
each with `react-dom/server`'s `renderToStaticMarkup` under Node, fed the student-path payloads §9
already builds. Assert no throw, and that output is not degenerate for features the payload
declares — a number line carrying `jump_count`/`jump_size` that emits zero jump marks is the
regression case, and is invisible to §9 because the component reads those keys inside a branch and
the AST therefore classes them conditional. §9 already shells out to `node`, so this crosses no new
dependency boundary.

**Component behaviour and edge cases.** Unit is *component × payload class*, not LC: behaviour is a
function of params, not of which competency produced them. 22 components × roughly eight classes
(empty, one element, typical, boundary/max, disabled/read-only, correct-answer round trip, wrong
answer, malformed) ≈ 180 tests running in seconds under `vitest` + `jsdom` +
`@testing-library/react` (three dev dependencies; `vite` is already present). Do **not** sweep the
obligation manifest through the DOM: the backend already owns that corpus per step 0B, and 20 of
the 22 components are driven purely by `onClick`/`onChange`, so payload breadth adds no frontend
path. This closes one seam nothing covers today — the value a component *emits* through `onAnswer`
for the correct selection must equal the keyed answer and be graded CORRECT by
`services.scoring.answers_match`. §10 tests graders against the key and §9 tests payloads against
the component's key list; the emitted value is untested by both.

Frontend results reach `run_all` as a **consumed artifact**, on the `mutation_proof.py` pattern:
the suite writes a machine-readable result bound to the input digest, and `run_all` verifies and
consumes it. A gate that regenerates its own evidence is not a gate, and this keeps `run_all`
Python-only at runtime.

**Named blind spot, recorded in the contract row and the validator docstring:** `jsdom` has no
layout engine, so `getBoundingClientRect()` returns zeros and the `clientX → value` arithmetic in
`NumberLineInteractive` and `BarChartInteractive` degenerates. Their `onClick`/`onChange` paths are
tested; pointer-drag geometry on those two components stays **unproven**, and is not described
otherwise. `@dnd-kit` is confined to `App.jsx` and `PracticeView.jsx`; no visual skeleton uses
drag-and-drop. The durable fix is to give every visual a non-pointer input path — an accessibility
improvement that also removes the blind spot — not to reintroduce a browser.

Acceptance for H-08: every registered component appears in the static-render coverage artifact with
a real student-path payload; planted defects (a thrown render, a dropped conditional key, a
degenerate visual, an `onAnswer` value disagreeing with the key) are each detected **by name**; the
emitted-value round trip runs for every component with an `onAnswer`; the artifact is bound to the
input digest and rejected when stale; and no test depends on an external database, a development
server, an arbitrary sleep, or a globally installed interpreter.

### M1 acceptance

- Phase 1 exits 0; all new lints are at zero findings; no increased allowances or lower census floors.
- Phase 1 completes with network disabled and an empty external database configuration; every
  scheduled stage appears in the ledger and every obligation is executed or fails by name.
- All new, migrated, and existing content-correctness guards have named detected mutations on
  the current inputs, with valid controls and completed machine-readable proof evidence.
- No content, coverage, render, grade, or evidence result is warning-only, silently skipped,
  tolerated by a numeric floor, or classified as checked when its semantic domain is unsupported.
- **§1L (step 3A) is NOT an M1 gate.** It is a separately staged capability; M1 requires only that
  its nonbinding `context_semantics_inventory.json` exists with zero unmapped live sources recorded,
  and that no §1L contract row has been added against a red baseline. Whichever context families are
  annotated by then pass their isolated controls and detect their planted containment, action, unit
  and state-transition violations through the rendered student path; families not yet annotated are
  named as unproved, not assumed clean.
- Each clause→payload family activated under step 3B has zero findings, cites the MATATAG clause it
  derives from, and detects its planted violation. The interest-blind emoji formatter is fixed
  before its family activates, so the gate is proved at a measured zero rather than against a red
  baseline.
- `_stratified_seeds` covers every declared `(variant, value)` pair with no per-node cap, pins
  interest explicitly, and varies difficulty across more than two points — measured, not asserted.
  Joint crossing remains uncovered and is named as a limit rather than implied.
- The Phase 1 frontend checks meet step 5A acceptance and publish complete component coverage;
  pointer-drag geometry on the two pointer components is recorded as an unproven blind spot rather
  than described as covered.
- Current requirements and all legacy unresolved findings reconcile without omissions.
- No seventh facet, no second active attestation programme, no vacuous phase-boundary check.
- The two known semantic examples remain regression fixtures: `mat_g2_mg_q4_2/hours_in_a_day`
  and `mat_g3_mg_q1_6/draw_segment_of_given_length`. Preserve their defective packets and exact
  seeds with provenance. Independent review establishes their semantic failure; validator
  mutations establish enforcement of missing/non-PASS clause evidence. Also test corrected
  positive controls; do not require repaired live nodes to fail forever.
- Full `run_all` is executed and its remaining content/re-review failures reported explicitly.
  Those failures are expected debt at M1, never described as a completed pg pipeline.

## M2 — Resolve the content and earn current reviews

### 6. Fix all content by root cause, including required capabilities

Group the consolidated findings by shared DNA, generator, formatter, adapter, packet, and
frontend cause. For each group, query affected callers and enumerate all affected nodes,
then verify the exact MATATAG clause and cumulative vocabulary/concept boundary for each LC.
Reproduce the defect on explicit seeds and profiles before editing.

Build missing variants, formatters, drawing/interaction surfaces, or other capabilities when
the written competency requires them. A recognition MCQ is not sufficient evidence for a
construction verb. Carry required behavior through backend output, compatibility, student
routing, frontend rendering/input, and answer evaluation; inspect actual student interaction.
Keep the Lab's diagnostic behavior separate from evidence of student-path availability.

Honor existing R-1 through R-5 decisions. Before the affected content queue is cleared, close
the currently documented enforcement gaps for R-3's scoped visual-rate requirement and R-4's
unbiased allowed-combination selection with named mutations, using step 3's control-first,
zero-baseline activation procedure. Derive routing checks from actual allowed
combinations and sampling logic; measure fixed-seed rendered outcomes as corroboration, not
an arbitrary “close enough” replacement for the owner's numeric rule. A rule scoped by the
owner to one LC stays scoped there through explicit policy data; it is not a node-specific
exception invented to pass a test. Do not equate independently uniform choices with uniform
choice over allowed joint combinations without demonstrating the equivalence.

Ratchet the existing capability finding allowance to zero as the missing required artifacts
are built. Do not unregister a required capability to remove a contradiction. Generator-fix
work leaves validators and the contract read-only; separate harness changes into independently
justified, mutation-proved work, as required by AGENTS.md.

After each coherent cause fix, run affected validators and mutations. Run the full mutation
table after each stable integration batch, as scheduled in step 4, before accepting its proof
bundle. Diagnose any survivor by observing whether its plant reaches the live path; repair the
fixture or gate according to the cause. Recompute affected packets/review debt, including
transitive frontend changes. Cite each served competency clause in the commit and evidence log.
No blanket re-review while shared content is still changing. Batch re-review **per root-cause
group**, not per individual fix: a later fix to shared code invalidates a review already paid for.

**Every confirmed contextual/logical defect becomes permanent.** §1L (step 3A) gates the
relationships its declarations express, and says itself that subtle common-sense, cultural and
narrative coherence stay per-sample judgment. A defect in that remainder is caught **once** unless
it is pinned, and nothing stops it returning when a generator changes — §1J/§1K catch their class
forever; an undeclared contextual defect does not. So each confirmed contextual or logical finding
produces both:

1. a **pinned regression fixture** — the defective packet, exact seed, and provenance; and
2. a **mutation** proving whatever now catches it.

Where the defect falls inside a relationship §1L already models, the fix is a **new declaration in
that context family**, which is how §1L's coverage grows from evidence rather than from guessing
which relationships matter — and which makes step 3A's annotation *aimed* at the families that
actually produce defects instead of exhaustive and hopeful. Where it falls outside, the fixture at
minimum pins node and seed so re-review is targeted rather than blanket, and the class is recorded
as a candidate for a future §1L role. This generalizes the two fixtures named in M1 acceptance
(`mat_g2_mg_q4_2/hours_in_a_day`, `mat_g3_mg_q1_6/draw_segment_of_given_length`) from examples
into a standing rule. It is the mechanism by which review generates gates, and under the Scaling
Mandate it is what stops grades 4–10 inheriting a defect class that was only ever fixed once.

### 7. Review stable content in one programme

After mechanical checks and root-cause fixes settle, build current merged packets for every
registered node. Validate packet completeness before dispatch. Reviewers independently assess
the existing six facets and all clause entries using complete samples and relevant visual/
interaction evidence. Neither the fixer nor a migration script supplies their verdicts.

Size the campaign from the generated packet inventory before dispatch. At today's 776 required
pairs, the 25-clause limit implies at least 32 dispatches for one clean clause round; the
25-node-per-reviewer limit implies at least 7 independent reviewer identities across 151 nodes.
Those are lower bounds: dual review of new/high-risk capabilities and nodes split across
dispatches increase them. Reserve capacity for the initial round plus two corrective rounds,
initially 96 dispatch-equivalents and 21 reviewer-round identity slots, then replace the reserve
with exact counts once the merged packet builder reports clause and dual-review assignments.
Record completed, rejected, expired, and redispatched packets so capacity cannot be inferred
from the number of files.

The latest recorded re-review moved from PASS=14/CONCERN=95/FAIL=42 to
PASS=14/CONCERN=93/FAIL=44. Schedule around the demonstrated likelihood of real corrective work;
do not assume the first merged round will pass or pre-author its replacement verdicts.

The six facets use explicit subcriteria so “pedagogically sound” is assessable without adding
another top-level verdict:

| Existing facet | Required subcriteria in reviewer evidence |
|---|---|
| `competency_fulfillment` | Complete competency decomposition; correct action (identify, solve, explain, draw, construct); mathematical and answer correctness |
| `comprehensive_coverage` | Every named clause, range, representation, and subcase appears in reachable student-path evidence |
| `cognitive_capacity` | Reading load, working-memory steps, abstraction, prerequisite concepts, directions, and contextual familiarity fit the grade and quarter |
| `variant_comprehensiveness` | Variants are meaningful, reachable, distinct, and proportioned without hiding required or rare cases |
| `competency_alignment` | Stem, options, hints, feedback, visuals, interaction, and grading all ask and reward the exact LC; the story's entities, actions, units, containment, causality, and state transitions are mutually coherent |
| `scale_appropriateness` | Quantities, contexts, vocabulary, visual density, touch/keyboard demands, and time-on-task suit the learner |

Across those facets, reviewers explicitly address contextual and logical validity, ambiguity,
the uniqueness of the correct response, distractor misconception quality, hint/feedback
correctness and helpfulness, interaction clarity, and basic accessibility of text and controls.
The reviewer records this for every sample, not only in a node-level summary. A top-level PASS
without subcriterion reasoning and cited samples is incomplete evidence.

File exact returned judgments through the merged filing helper. Resolve FAIL/CONCERN findings
by fixing content and re-reviewing affected nodes; do not edit reviewer reasoning to obtain
PASS. Plan one coordinated review campaign, with as many corrective rounds as actual findings
require. Any later relevant edit invalidates the affected evidence and mutation proofs.

### 8. Final verification and evidence filing

On stable inputs, execute the following commands, preserving exit statuses and full output.
The frontend command becomes available in step 5A. Run them sequentially; use the environment's
asynchronous process sessions for long runs. The mutation command publishes the proof artifact
reviewed in step 4.

```sh
PYTHONPATH=. .venv/bin/python tests/mutation_harness.py
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all --phase 1
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all --phase 2
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all
npm --prefix frontend ci
npm --prefix frontend run lint -- --max-warnings=0
npm --prefix frontend run build
npm --prefix frontend test
```

`npm --prefix frontend test` is the Phase 1 frontend suite from step 5A: static render over every
registered component plus the component × payload-class behaviour tests. Its coverage artifact is
part of this final evidence and is bound to the input digest.

`pytest tests/unit -m slow` is **not** in this sequence — see step 8A. Use targeted unit tests while
implementing individual changes; `run_all` covers the fast unit selection. If a verification step
changes a consumed input, regenerate the affected proof/review evidence and repeat only the checks
invalidated by that change before the final full run.

### 8A. Retire the two `slow` audits as gates, keeping the module

`tests/exhaustive_checklist_auditor.py` is a 1,473-line second copy of rules the harness now owns
from ground truth, and the copy has been the wrong one at least three recorded times: the
scalar-versus-value mismatch behind ~93% false findings, the SoC regex-stem-digit false positives,
and `mat_g1_dp_q3_0` scored CLEAN while serving a BarChart with an empty payload. Its vocabulary
dimension is a hand-written ten-word `FORBIDDEN_WORDS` list applied globally, where §1D reads
per-node `NOT_YET_KNOWN`/`cumulative_vocab` from the knowledge graph — the list is grade-blind and
cannot know `divisor` is forbidden at G2 and correct at G4, so it passes everything at grades 4–10.
That is Scaling Mandate 4 exactly. `validate_render`'s docstring already demotes the auditor:
it pins each advertised formatter and so never exercises the auto-select path students receive.

`test_parallel_audit` asserts only `run_audit(parallel=True) == run_audit(parallel=False)` — it
tests a `ProcessPoolExecutor`, not content, and its five-node sample includes `mat_g1_dp_q3_0`.
Neither test is mutation-proven; `unit_tests` sits in `UNPROVEN_ASSERTIONS`.

Disposition:

1. **Keep the module.** Five fast unit tests import its predicates
   (`test_regrouping_feasibility`, `test_formatter_supports_profile`,
   `test_semantic_leak_carveouts`, `test_strict_scalar_tolerance`), and
   `tests/run_checklist_audit.sh` keeps it available as a diagnostic sweep. Only `run_audit` is
   what the two slow tests drive.
2. **Produce the migration map first**, as step 0 already requires: one row per auditor dimension →
   the § check that owns it today. Delete a dimension only once it has a live owner. A dimension
   with **no** § owner is a real gap to build as a § check, never a reason to keep the auditor as a
   gate.
3. **The one unique dimension is breadth** — the auditor enumerates *pinned* formatter × profile
   combinations where the harness samples the student path. Step 0B's obligation manifest subsumes
   it; record it as folded into H-04 rather than lost.
4. Neither slow test enters the release lane. Both are deleted once their map rows have owners.

Stated as a limit: neither test was executed for this assessment, so their current pass/fail is
unknown. The claim is that their assertions restate rules the harness owns from better sources —
the migration map is what converts that reading into evidence.

Append commands, verbatim outputs, exit codes, checkout/input digests, seeds/profiles, detected
mutation markers, and node/clause evidence references to
[`validation_reports/HARDENING_EVIDENCE.md`](../validation_reports/HARDENING_EVIDENCE.md).
Store reusable audit reports under `validation_reports/phase2_hardening/`, and reusable
fixtures/tools under `tests/`. Record each remaining inherent limitation in its validator
docstring, contract row, and evidence log. No content-correctness guard described as working
without current mutation proof.

**M2 content completion means all of the following, on the same final inputs:** full `run_all` exits 0;
every registered node has complete, current, independent PASS evidence for all six facets and
every requirement; migration has no unresolved required rows; required capability provision
has no residual findings; the complete mutation table is detected with valid proof records;
no new silent skips, weakened checks, or reduced census floors have been introduced. Report
actual runtime and dispatch counts as costs; smaller code or fewer findings alone is not success.

## M3 — out of scope for this plan

**Owner ruling 2026-09-12: release promotion, staging/production separation, canary replay,
operational telemetry, alerting and rollback are cut from this document** and raised separately
once M1 and M2 land. None of them gates content correctness, they depend on infrastructure access
this plan does not assume, and carrying them here made the plan's scope unreadable against its
actual blocker (`H-09` stays open and unaddressed, recorded as such in the status ledger).

Two things from that section are *not* lost, because they are not release concerns:

- **The regression-feedback rule** — "feed reproducible incidents back into a permanent regression
  fixture and mutation where a guard was missing" — is re-homed into **step 6**, where it applies to
  review findings rather than production incidents. It is the single most load-bearing sentence that
  was sitting inside M3.
- **The digest discipline** (a candidate is bound to its exact inputs; rebuilding any input makes a
  different candidate) already exists in the harness as `mutation_proof.INPUT_ROOTS` and is enforced
  by §8. Nothing further is required here.

When M3 is revived, it starts from `H-09`'s row in
`validation_reports/phase2_hardening/hardening_status.json`, not from this section.

## Implementation file map

| Area | Current state and remaining changes |
|---|---|
| `backend/app/practice_gen/validation/judgment_packets.py` | Canonical student-path samples, explicit replay inputs, visual evidence, complete sampling obligations |
| `backend/app/practice_gen/validation/validate_judgment.py` | Merged schema, clause enforcement, expanded freshness/provenance, active-review resolution |
| `tests/judgment_batches.py`; new merged filing helper in `tests/` | Exact delivery, dual batch limits, response joins, immutable filing |
| `backend/app/practice_gen/validation/validate_capability.py` | Keep mechanical requirements/provision; migrate attestation behaviors and boundary enforcement |
| `validation/validate_language.py`, `validate_options.py` | Existing dirty §1J/§1K implementations; review, land, preserve proofs, and close only their declared bounded extensions |
| Planned contextual-logic validator and context declarations | Step 3A inventory, typed semantic roles/affordances, §1L registration, zero-baseline activation, and Phase 2 context-family coverage |
| `tests/mutation_harness.py`, `tests/isolated_corpus.py`, `validation/mutation_proof.py`, `validate_coverage.py`, `validation_reports/mutation_proofs/` | Existing dirty executed-proof implementation; review, fix docstring drift, land, and re-prove on the clean integration revision |
| `validation/run_all.py`, `validation/_manifest.py` | Stage registry/ledger, crash isolation, real check registration, phase boundaries, and honest summaries |
| `validation/validate_grade.py` and grader fixtures | Hermetic bidirectional grading over every response contract, without external database state |
| `validation/validate_render.py`; frontend component-contract tooling | Conditional payload enforcement; headless static render over every component; render-derived visual description consumed by the judgment packet |
| `validation/validate_dna.py`, `validate_compat.py`, `validate_vocab.py`, `validate_interest.py`, `validate_matrix.py` | Scale-safe obligation coverage; eliminate representative-only, first-DNA, G1–3, warning-only, and silent-skip paths |
| Existing `tests/unit/test_attestation_freshness.py`, `test_capability_contract.py`, `test_judgment_*` | Port all retained behaviors; add negative controls and new gap coverage |
| `tests/attester_packets.py`, `tests/attester_file.py` | Retire after parity and caller checks; preserve historical attestation files |
| `tests/phase2_migration.py`; `validation_reports/phase2_hardening/requirement_inventory.json`, `assertion_migration.json` | Existing but stale step-0 tooling/reports; review and regenerate after integration |
| Planned `validation_reports/phase2_hardening/hardening_status.json`, `obligation_budget.json`, `context_semantics_inventory.json` | Machine-checkable H-row status, coverage sizing/sharding, and contextual-semantic migration |
| Context entities/templates and DNA/formatters/compatibility/adapter/frontend paths discovered per cause | Typed semantic roles/affordances, curriculum-directed fixes, and required response surfaces |
| `frontend/package.json`; `tests/frontend/` | `vitest` + `jsdom` + `@testing-library/react`; static render and component × payload-class behaviour tests; delete `run_servers_and_test.js`. **No browser runner, no Puppeteer, no `test:e2e`** |
| `tests/exhaustive_checklist_auditor.py`; `tests/unit/test_checklist_audit.py`, `test_parallel_audit.py` | Keep the module (five fast tests import its predicates); retire both `run_audit` gates after the dimension→§-owner migration map (step 8A) |
| `.github/workflows/`, release-manifest tooling, deployment configuration | Exact-revision CI gates, immutable digests, staging/production separation, canary and rollback |
| Backend/frontend observability paths | Release/node/formatter/profile telemetry and replay without learner PII |
| `docs/pgen_contract.md`, `docs/pgen_judgment.md`, `docs/pgen_rulings.md` | Atomic enforcement updates, six-facet schema, accepted sequencing decision |

In rows abbreviated as `validation/...`, the directory is
`backend/app/practice_gen/validation/`. “Existing dirty” means present and executed in the
current working tree; it does not mean reviewed, committed, or accepted for release.

## Evidence for preparation and implementation-state review

The following executions occurred in this conversation before implementation. They verify
the baseline diagnosis and relevant existing tests; they do not certify M1 or M2.

```text
git rev-parse --short HEAD
c007b8ae

PYTHONPATH=. .venv/bin/python local_only/scratch/plan_fold_review/probe.py
```

Verbatim excerpts from the review probe:

```text
live_pairs=787 NOT_PROVIDED=79 CONTRADICTED=67
CONTRADICTED_nodes=43
required_pairs=776 required_NOT_PROVIDED=68 historical_pairs_not_required=11
attestation_freshness_errors=150
mat_g1_na_q1_2 seed=42 visual_only_corruption_errors=[]
empty_clause_map_schema_errors=[]
unexecuted_assertion_reported_proven=True
```

```text
PYTHONPATH=. .venv/bin/python -m pytest tests/unit/test_attestation_freshness.py tests/unit/test_judgment_antitemplate.py tests/unit/test_judgment_answer_resolution.py -q
32 passed in 0.28s

PYTHONPATH=. .venv/bin/python -m pytest tests/unit/test_capability_contract.py -q
35 passed, 1 skipped in 32.35s
```

The pipeline-wide deployment review then produced these current results:

```text
PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all --phase 1
PASS unit_tests (472 passed, 1 skipped, 2 deselected, 1 warning in 82.09s (0:01:22))
Nodes Checked: 151
Nodes Passed:  151
Nodes Failed:  0
PASS capability_contract (Phase 1: all nodes declare, cite, cover, and are provided for)
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not translate host name
"ep-winter-bird-ao6aql6n.c-2.ap-southeast-1.aws.neon.tech" to address:
nodename nor servname provided, or not known

PYTHONPATH=. .venv/bin/python -m backend.app.practice_gen.validation.run_all --phase 2
FAIL judgment_reviews (484 problem(s) — non-PASS verdicts or incomplete reviews)
FAIL capability_contract (Phase 2, 217 problem(s): 67 CONTRADICTED, 0 UNATTESTED,
76 STALE (§6F), 74 UNADJUDICABLE (no recorded options))
SOME PHASE 2 CHECKS FAILED. Please review the output above.

PYTHONPATH=. .venv/bin/python -c 'from backend.app.practice_gen.validation import validate_coverage as v; print(f"unproven_assertions={len(v.UNPROVEN_ASSERTIONS)}")'
unproven_assertions=39

PYTHONPATH=. .venv/bin/python -m pytest tests/unit -q --collect-only -p no:cacheprovider
473/475 tests collected (2 deselected) in 0.77s

(working directory: frontend) npm run build
✓ built in 743ms

(working directory: frontend) npm run lint
✖ 225 problems (0 errors, 225 warnings)

node frontend/run_servers_and_test.js
ReferenceError: require is not defined in ES module scope
```

The critique review added these current working-tree measurements:

```text
mutation proof corpus
proofs 79
detected_true 79
phase1_admissible_true 79
mcq_reviewed_without_options [(True, True)]
duration_count 79
duration_sum_seconds 716.0
duration_max_seconds 125.0

stored step-0 inventories
requirement_inventory.json: head c007b8ae, dirty_count 3
assertion_migration.json: head c007b8ae, dirty_count 2
assertion_migration.json: mutations_registered 76

current repository status
23 modified or untracked paths

interest-bank semantic-migration size
actors entries 160 distinct 147
objects entries 160 distinct 149
places entries 135 distinct 90
item1 entries 104 distinct 94
item2 entries 104 distinct 82
all_entries 663
all_distinct 552

current §1C assignment enumeration
nodes=151 node_dna_formatter_pairs=463 allowed_assignments=4325
backend_problems_at_5=21625 backend_problems_at_10=43250
at_0.5s_each: five_samples=180.2min ten_samples=360.4min
at_1s_each: five_samples=360.4min ten_samples=720.8min
```

The skipped unit test is not proof of a guard. Step 0 re-audits the actual mutation evidence and
replaces backlog-dependent fixtures where needed. This plan revision changes only the plan; the
dirty harness and generator work listed above predates it and remains unaccepted until the
integration checkpoint passes.

### Review measurements, 2026-09-12 (post-revision critique)

Read-only measurements taken while reviewing this document. They support the owner rulings recorded
in steps 2, 3B, 5A, 6, 8A and the M3 cut. No test was run; each is reproducible from the tree.

```text
# Judgment packet carries no visual fields (step 2)
_render_sample -> {seed, formatter, question_text, correct_answer, options, hint, cloze_text}
grep -c interest backend/app/practice_gen/validation/judgment_packets.py
0
# ...although pipeline.run() already accepts student_interest

# Variant coverage cap (step 2)
candidate (variant, value) pairs across 151 nodes : 975
cap per node                                      : 6
nodes exceeding the cap                           : 68
pairs no packet can ever contain                  : 292

# Emoji formatter is interest-blind (step 3B)
fmt_emoji_pictorial.py:134  emoji = rng.choice(_ALL_EMOJIS)
grep -c interest backend/app/practice_gen/formatters/visual/fmt_emoji_pictorial.py
0
# ...although data/interest_bank.json carries a per-interest `emoji` field

# Frontend component input paths (step 5A)
components in VisualSkeletons.jsx            : 22
driven purely by onClick/onChange            : 20
using getBoundingClientRect/clientX          : 2  (NumberLine, BarChart)
@dnd-kit in any visual skeleton              : 0  (App.jsx and PracticeView.jsx only)
puppeteer in frontend/package.json           : 0
§9 already shells out to `node`              : yes (extract_visual_contract.mjs, Babel)

# Auditor duplicates ground truth (step 8A)
tests/exhaustive_checklist_auditor.py FORBIDDEN_WORDS : 10 words, global, grade-blind
validate_vocab reads per-node NOT_YET_KNOWN / cumulative_vocab from the KG
fast unit tests importing the auditor's predicates    : 4

# Interrupted agent's tree validates clean (integration checkpoint)
registered mutations 79 / proof records 79 ; missing 0 ; orphan 0
all detected=true ; all restored_clean=true ; all phase1_admissible=true
distinct input_digest across all 79 records : 1
full mutation table wall time               : 716s total, 125s worst case
```
