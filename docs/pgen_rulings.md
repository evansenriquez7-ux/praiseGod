# Owner Rulings — curriculum decisions an agent may not make alone

**Species: contract** (see `docs/DOC_RULES.md`). Every ruling here is a decision about what
MATATAG requires that only the owner may take. An agent implements a ruling; it does not
author one, reinterpret one, or extend one to a case the ruling does not name.

Each row states the ruling verbatim, what it binds, and **its enforcing check** — or says
plainly that nothing enforces it yet, which is a gap, not a footnote (R1).

DOC_RULES R5 (the ~80-line budget) applies here as to any contract doc. Keep it by trimming
your own explanations — never a ruling's wording, which is what the next reader relies on.

---

## R-1 · Patterns stay numerical and alphabetical (2026-09-10)

> "ignore 'rhythmic properties' and 'visual elements in the arts'; stick with numerical and
> alphabetical patterns only. Alphabetic patterns such as ascending, or up to 5-letter
> repeating patterns, can be used."

Binds `mat_g1_na_q3_6`, `mat_g2_na_q2_8`. Six `requires` entries deleted 2026-09-10
(`rhythmic_properties`, `arts` on both) and `visual_elements` on both on 2026-09-11, when the
owner confirmed the campaign brief's six-row table had omitted it rather than scoped it out —
it comes from the identical competency phrase as `arts`.

Positive half built 2026-09-10: letter repeating units reach 3–5 (the competency prints a
3-letter example the pipeline could not produce), and ascending/descending alphabetic runs
exist where a competency names letters. Enforced by `validate_capability` §6A/§6B (the deleted
clauses may not return without a requirement) and `capability_orphan_provider_6A` (their
provider entries are gone and may not be re-added unrequired).

## R-2 · "Given orally or in pictures" is a disjunction (2026-09-10)

> "ignore 'oral' delivery. Using visual elements such as emojis will suffice."

Binds `mat_g1_na_q1_9`, `mat_g1_na_q2_6`, `mat_g1_na_q3_3`, `mat_g1_na_q4_6`,
`mat_g2_na_q2_5`. The capability extractor had flattened one two-armed requirement into two
mandatory ones. The `orally` / `given_orally` arm is deleted; the `pictures` / `in_pictures`
arm is **retained and must actually render**.

## R-3 · `mat_g1_na_q4_6`: written substitutes for oral, pictures ≥ 50% (2026-09-11)

> "for this particular lc pg, we can substitute 'written' for 'oral'. pictures or visual
> elements like emojis should be used minimum 50% of the time"

Scoped to this LC by the owner's own words. A written (textual) presentation satisfies the
arm that `orally` named, and **at least half** of this node's rendered items must carry a
picture or visual element. Under R-4 that rate is achieved by the COMPOSITION OF THE ALLOWED
FORMATTER SET, never by weighting one formatter above another.

**Enforcement: NOT YET BUILT.** Measured 2026-09-11 before the ruling: 49 of 300 seeds (16%).

## R-4 · No routing bias: uniform choice across allowed combinations (2026-09-11)

> "there should never be a bias. for an lc or dna, dd, contextual variants, and visual
> formatter combinations must be completely random across allowed combinations."

Binds the whole pipeline, not one node. Formatter choice, difficulty-dimension values and
contextual variants are drawn **uniformly at random from the combinations a node actually
allows**. Preferring one formatter, or one context, over another is forbidden however it is
spelled — a weight table, a probability literal, or an ordered fallback that reaches the first
option most often.

This overturns `adapter._FORMATTER_WEIGHTS` (mcq 3.0, cloze 1.5, everything else 0.6) and the
comment above it claiming a `visual_home` bias that the chooser never applied. Under this
ruling the correct answer was neither: no bias at all.

Consequence to hold in mind: a node's visual rate is now a property of its ALLOWED SET. To
serve a competency that names a medium (R-3), give the node more formatters of that medium —
do not re-introduce a weight.

**Enforcement: NOT YET BUILT.**

## R-5 · `requires_ignore` is human-authored ground truth (2026-09-11)

> "agents must see this requires_ignore as a human authored ground truth. this should be
> legally binding and something that can only be done by human judgement which can be
> verified by git history"

A word in a node's `requires_ignore` is a statement that MATATAG names something the pipeline
is not required to build. That is a curriculum ruling. **An agent may not add, alter or remove
an entry on its own initiative**, and the audit trail is git history: the commit that
introduces an entry must carry the owner's decision.

`requires_ignore_note` records the ruling and its reason at the point of use, so a later agent
reading `["rhythmic", "properties", "arts"]` can tell a curriculum decision from a stopword.

**Enforcement: NOT YET BUILT.**

---

## Decisions of sequencing (not curriculum, but binding on agents)

* **D-1 · Defer §6 re-attestation until content settles (2026-09-11).** The 136-record
  unadjudicable queue is not re-attested while §5 content debt is open, because a content fix
  re-stales fresh evidence immediately — §5 paid for that lesson on 2026-09-10 (500 findings
  became 617 the moment five generators changed). Re-attest once, against stable generation.
* **D-2 · Fix content debt by ROOT CAUSE across nodes, not node by node (2026-09-11).** The
  480 open §5 findings are grouped by shared generator cause and fixed per cause. Accept that
  one such fix re-stales many nodes at once and re-review them together.
