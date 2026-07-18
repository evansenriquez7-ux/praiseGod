# Docs Remediation — Making the docs/ Directory Stop Producing Bugs

**Audience:** autonomous coding agent (and human maintainer).
**Scope:** all `.md` files in `docs/` that govern the pg pipeline, plus the rules for writing any future agent-facing doc in this repo.
**Prerequisite:** execute only **after** `PGEN_HARDENING_PLAN.md` Phase 2 is complete, because the restructured docs point at harness checks that must exist first.

> **Status: Part 4 done-criteria met.**
> (a) `docs/` contains no binding rule without a named enforcer — `pgen_contract.md`/`pgen_judgment.md` are the only docs permitted a "MUST", enforced by a CI lint (`.github/workflows/validate-pgen.yml`, "Lint docs/ for un-enforced MUSTs").
> (b) No fact stated in two places — formatter/DNA names live in `compatibility.py`/`_manifest.py`; `DIFFICULTY_DIMENSIONS.md` and `INFRASTRUCTURE_WORKFLOW.md` link out rather than restate; three stale inline comments pointing at the deleted `pgen_checklist.md` (in `matatag_router.py`, `practice_router.py`, `money_peso.py`, `orchestrator.py`, `tests/README.md`) were repointed to `pgen_contract.md`/`testing_pipeline.md`.
> (c) `run_all` cross-checks the contract table — `run_all.py` now parses `docs/pgen_contract.md`'s `§`-refs at runtime (`_parse_contract_section_refs()`) and asserts they match the harness's own `CONTRACT_CHECKS` registry exactly (`PASS contract_doc_matches_registry`), catching drift in either direction, not just a hardcoded shadow copy of the doc.
> (d) `DOC_RULES.md` exists and is linked from the README — the repo had no root `README.md` at all; created one linking `DOC_RULES.md`, `pgen_contract.md`, `INFRASTRUCTURE_WORKFLOW.md`, and `AGENT_ENVIRONMENT.md`.
>
> One item remains a deliberate, explicit open question rather than a defect: the Advanced/bridge-tier scalar value (`1.1` vs `1.25`, `docs/BUG_BRIDGE_SCALAR.md`) is a pedagogical judgment call escalated to the maintainer — the single-source-of-truth *mechanism* is fixed, the *value* is not this agent's to pick.

---

## Part 1 — Diagnosis: how the current docs cause bugs

Your suspicion is correct. The docs aren't just failing to prevent bugs — several of their structural properties actively generate them. Understanding the mechanisms matters, because the fix is to make each mechanism impossible, not to write more careful prose.

### 1.1 The docs issue commands to the agent's judgment, not to a machine
`pgen_checklist.md` is written as imperatives aimed at an agent's self-assessment: "provably restrict," "ensure all logical variants," "must verify every item." None of these name an executable command whose exit code defines pass/fail. An instruction whose satisfaction is judged by the same agent that did the work will be judged satisfied. Every "MUST" that lacks an enforcing command is, functionally, a suggestion — and agents treat it as one under time/context pressure.

### 1.2 Unverifiable and verifiable items are interleaved, so everything gets the same (low) rigor
"Strict Scalar Mapping" is mechanically checkable. "Cognitive Capacity" is a judgment call. The checklist presents them identically, as sibling bullets. The effect: agents apply judgment-call rigor (eyeball it, check the box) to the mechanical items too. Mixing the two classes drags the checkable items down to the rigor level of the uncheckable ones.

### 1.3 Duplication has already drifted
"Formatter Comprehensiveness" appears **twice** in checklist §3 with slightly different wording. The pg-pipeline rules were moved from `INFRASTRUCTURE_WORKFLOW.md` §7 into the checklist, leaving a pointer — one move went fine, but the duplicate bullet shows edits are happening without review. Every duplicated statement is a future contradiction, and when docs contradict each other, agents silently pick whichever reading permits what they already built.

### 1.4 The docs describe intent; the code implements something adjacent; nothing detects the gap
Example already in the tree: the checklist mandates strict 0.0–1.0 scalar mapping to competency bounds, while the lab router exposes a 1.25 "bridge" scalar and `DIFFICULTY_LEVEL_MAP` defines 1.1 for "Advanced" — two different out-of-band values, neither mentioned in the checklist. Another: the checklist's fail-fast doctrine, while the frontend's option-shape fallback cascade and the CI's `|| true` embody the opposite. When doc and code diverge, agents inherit the divergence: they read the doc, observe the code, conclude the doc is aspirational, and stop trusting *all* docs — including the parts that were load-bearing.

### 1.5 Docs grow by accretion into context-window poison
`INFRASTRUCTURE_WORKFLOW.md` mixes deployment, SSH/FDA setup, Graphify, tunnel quirks, and (formerly) pg rules. Long mixed-topic docs mean the agent either loads everything (burning context, degrading attention by the time it writes code) or skims (missing the one binding rule). Both outcomes produce bugs. Doc length is not neutral; every non-binding sentence in an agent-facing doc taxes compliance with the binding ones.

### 1.6 The docs assign the agent tests it cannot run
"Mandatory Testing: …inspected the output…the final results that the UI expects." An agent without eyes on the rendered UI cannot perform this. A checklist item that is impossible to execute honestly guarantees a dishonest checkmark — and normalizes dishonest checkmarks for the other items.

---

## Part 2 — The doctrine (rules for every agent-facing doc, permanent)

Adopt these five rules repo-wide. They are the permanent fix; Part 3 applies them to the current files.

**R1 — Docs describe; the harness enforces.** No doc may contain a "MUST" about pipeline behavior unless it names the specific validator/assertion that enforces it (e.g. `validate_matrix §1A`). A MUST with no enforcer is either (a) a TODO to add the enforcer, tracked explicitly, or (b) a judgment item, which belongs in the clearly-marked judgment section (R3).

**R2 — One source of truth per fact; everything else links.** A rule, bound, name list, or table lives in exactly one place — and wherever possible that place is **code or data, not prose** (formatter names live in the adapter router; bounds live in `registry`/competency text; the doc links to them). Docs never restate lists that code owns.

**R3 — Separate the three doc species; never mix them in one file.**
- *Contracts* — binding behavior, each line paired with its enforcing check (short; the checklist becomes this).
- *Judgment guides* — items requiring human/reviewer-agent evaluation, explicitly labeled "not machine-checked," with instructions for **who** evaluates and **what evidence** they must produce.
- *Explainers* — design rationale and internals (`DIFFICULTY_DIMENSIONS.md` is already correctly this species). Explainers are reference material, loaded only when needed, never containing MUSTs.

**R4 — Doc changes ship with their enforcement, atomically.** Any PR that changes a contract doc must change the corresponding harness assertion in the same PR, and vice versa. A contract edit with no test diff is an automatic review rejection. This is what keeps doc and code from drifting apart again.

**R5 — Agent-facing docs are budgeted.** Contract docs: target under ~80 lines. If a contract doc grows past that, split by species (R3), don't compress prose. Every sentence must either bind behavior or route the reader; delete everything else.

---

## Part 3 — Concrete restructuring of the current docs/

### 3.1 Rewrite `pgen_checklist.md` → contract + judgment split

Replace the current file with two:

**`docs/pgen_contract.md`** (species: contract). A table, not prose bullets. One row per binding rule:

| Rule | Enforced by | Runs in |
|---|---|---|
| Scalar 0.0/1.0 map exactly to competency bounds | `validate_matrix` §1A | CI, blocks deploy |
| No leaky windows; monotonic windows | `validate_matrix` §1B | CI, blocks deploy |
| Every supported variant×formatter executes cleanly with valid answers | `validate_matrix` §1C | CI, blocks deploy |
| Unsupported combos raise; no silent substitution | `validate_matrix` §1C-reverse | CI, blocks deploy |
| No NOT_YET_KNOWN vocab in formatted output | `validate_matrix` §1D | CI, blocks deploy |
| Answer key survives formatting; interest-invariant | `validate_matrix` §1E | CI, blocks deploy |
| Registry/compatibility bidirectional coverage | `validate_compat` | CI, blocks deploy |
| Difficulty profiles meet MIN_ACCEPTANCE_RATE | `validate_dna` (feasibility) | CI, blocks deploy |
| Response payload matches strict schema | Pydantic model + `validate_matrix` §1C | runtime + CI |

Header of the file states the whole doctrine in three lines: *"A generator is done when `python -m backend.app.practice_gen.validation.run_all` exits 0 and the judgment review (pgen_judgment.md) is filed. Checking a box proves nothing; the command output proves everything. If you believe a rule here is wrong, change the harness and this table in the same PR — never quietly deviate."*

Keep the two prose doctrines (Matatag Lab as single source of truth; no graceful fallbacks) as a short preamble — they're genuinely load-bearing framing — but each now ends with its enforcement pointer (the Lab/portal shared-clamp code path; the strict-schema + no-fallback checks).

**`docs/pgen_judgment.md`** (species: judgment guide). Receives the items that resist automation: Competency Fulfillment, Comprehensive Coverage, Cognitive Capacity, Variant Comprehensiveness, Competency Alignment, Scale Appropriateness (the log/linear *choice*). For each: the question to answer, **who answers it** (a reviewer agent that did not write the implementation, given only the competency text + N rendered samples from fixed seeds), and the **required evidence artifact** (a filled review form per node committed to `validation_reports/judgment/`, citing sample seeds). This makes the honest version of "an agent must verify" possible: the verifier is not the author, and the output is an artifact, not a checkbox. Delete the duplicated "Formatter Comprehensiveness" bullet in the process (it collapses into Variant/Formatter Comprehensiveness here, evaluated once).

**"Mandatory Testing"** is deleted as written. Its intent is now covered by: `validate_matrix` (behavior), the strict schema (UI contract), and the judgment review of rendered samples. Do not carry forward any doc line asking an agent to attest to something it cannot execute.

### 3.2 `DIFFICULTY_DIMENSIONS.md` — keep, but demote MUSTs
It's already a correct explainer. Sweep it for any imperative that binds behavior; each such line either moves to the contract table (with an enforcer) or is rephrased as descriptive rationale. Add one line at the top: "Reference only. Binding rules live in pgen_contract.md." Resolve the 1.1 vs 1.25 bridge-scalar inconsistency while there: pick one value, define it in **one** code location, have both the level map and the lab router import it, and document it in the explainer with its enforcement note (the harness asserts bridge samples stay within the bridge window and never appear when the Lab config disables it).

### 3.3 `INFRASTRUCTURE_WORKFLOW.md` — split and de-poison
- Extract §6 (Graphify/agent env) into `docs/AGENT_ENVIRONMENT.md` — that plus the contract are the only docs an agent should need to load by default.
- §7 already correctly points to the pg docs; update the pointer to `pgen_contract.md`.
- Add a subsection documenting the new `validate-pgen.yml` gate, and explicitly annotate the hosting workflow's `|| true` with *why it is acceptable there and forbidden in validation workflows* — otherwise the pattern will be copied into the validation CI by a future agent that greps for prior art.
- Everything else (SSH, FDA, tunnels, cold starts) stays; it's human-facing ops material, fine at length, but should never be loaded into a generator-building agent's context.

### 3.4 New file: `docs/DOC_RULES.md`
Ten lines. States R1–R5 verbatim, plus: "Before creating any new .md in docs/, classify it as contract / judgment / explainer and obey that species' rules. New MUSTs require a same-PR enforcer." Link it from the repo README. This is the permanence mechanism — without it, the next agent reintroduces a prose checklist within a month.

### 3.5 Drift tripwires (cheap, do them)
- In `run_all.py`, add a check that every `validate_matrix` section referenced by `pgen_contract.md`'s table exists (parse the doc for `§1A`-style refs; assert each maps to an implemented check). A contract row pointing at a nonexistent check → CI failure. This mechanically enforces R4 in one direction.
- Grep-based lint in CI: fail if any file in `docs/` outside `pgen_contract.md`/`pgen_judgment.md` contains `MUST` in a pg-pipeline context (tune the pattern pragmatically; the goal is a speed bump, not perfection).

---

## Part 4 — Ordering & definition of done

1. Complete `PGEN_HARDENING_PLAN.md` Phases 0–2 (harness exists and passes).
2. Apply §3.1–§3.4 above; delete `pgen_checklist.md` only after both replacement files exist and the contract table's every row names a real, running check.
3. Add §3.5 tripwires to CI.
4. Done when: (a) `docs/` contains no binding rule without a named enforcer, (b) no fact is stated in two places, (c) `run_all` cross-checks the contract table, and (d) `DOC_RULES.md` exists and is linked from the README.

The end state to hold in mind: **the docs stop being the thing agents comply with, and become the map of the things the machine enforces.** Agents can't half-read a map into a bug — the harness catches them regardless of what they read.