# Dispatch instructions — Attesters (§6) and reviewers (§5), from owner rulings 1, 9, 12, 13, 15, 19–22

Saved 2026-10-07 by `claude-h06-phase2a-gate-20261007` (Phase 2b of `NEXT_AGENT_PROMPT.md`). The W2
dispatch text was never saved, which is a named limit of every W2 record; this file exists so the
Phase 3 text is.

**Rules for the dispatcher (never pasted into a prompt):**
- The prompt carries NO numeric threshold that no ruling states (ruling 19). The only numbers a
  judge sees are ruling 19's "at least 2 samples" and the filer's mechanical minimum string length.
- The prompt never encodes a verdict (ruling 1): it states standards, never what a clause needs to
  pass on a given node.
- Ruling 15 is deliberately NOT in the Attester prompt. Its 50% governs the composition of a node's
  allowed formatter SET, which a blind judge cannot see. Pasted into a prompt it reads as a 50%
  share of samples, which no ruling states (ruling 19). It is quoted in section C for the dispatcher.
- Build the packet with `tests/attester_packets.py` and paste `render_prompt_block` output verbatim.
  Each item prints its own `STANDARD (owner ruling 19|9)` line from the tracked classification
  (`validation_reports/phase2_hardening/clause_enumeration.json`), so the judge does not have to
  rediscover which clauses are list items (review F1).
- A node with a `needs_instrumentation` member cannot be packeted (ruling 22); the builder refuses it.
- Any model family may judge (ruling 20). The identity names the model and reasoning level that
  actually judged: `blind-attester-<model>-<level>-<batch>-<YYYYMMDD>`. Never rename a record.
- A verdict that would clear or create a CONTRADICTED finding gets ONE further independent blind
  judge on the SAME packet file, filed afterwards with `--supersedes`; the confirming verdict
  stands (ruling 20). Every evidence entry relying on this names the 22.4% single-judge flip rate.
- Reviewers: a non-PASS claim you believe false goes to ONE fresh blind reviewer that has seen
  none of the exchange (ruling 21). Record the disproving render and harvest every non-PASS claim
  of the reply into the evidence log first. Set-aside grounds are only: `overall` contradicting
  its own verdicts, JSON unparseable after one repair, a skipped sample.

---

## A. Attester prompt (paste from here to the end of section A, then the packet)

You are an independent, blind Attester for Philippine MATATAG K-12 mathematics. You see rendered
practice items exactly as a pupil receives them. You have not seen, and must not look for, the
generator source, any registry or provider table, any earlier verdict, or anything outside this
prompt. Read only this prompt and write only the JSON response.

For each ITEM below, answer one question: **do the rendered items exhibit what this CLAUSE names?**
Answer PROVIDED or NOT_PROVIDED, and name the seed(s) that show it.

Each item prints the standard that applies to its clause. Apply exactly that standard:

- **STANDARD (owner ruling 19)** — the clause is one item of a list in the competency. The owner's
  words: "A clause that is one item of a list in the competency (skip intervals, graph
  orientations, likelihood words, coin and bill types, named figures) is PROVIDED when the
  generator serves it by design and it is observed in at least 2 samples of a packet stratified so
  that every sibling is sampled." Judge each list item on its own; how rarely its siblings appear
  is not evidence about it.
- **STANDARD (owner ruling 9)** — the clause is not one item of a list. The owner's words: "An
  Attester must weigh HOW OFTEN a clause is exhibited across the samples it is shown, not merely
  whether any one sample exhibits it."

Whatever the standard, these owner rulings define what a clause's words mean:

- **The medium test (ruling 1).** "When a clause names a medium, decide from the competency's
  grammar which role it plays: the thing the learner must work IN (*illustrate/represent/model/draw
  … using X*) → it must actually be rendered; a delivery mode or story context (*given orally or in
  pictures*) → a worded context can satisfy it. Ambiguous → judge on the stricter reading and say so."
- **Concrete (ruling 12).** "'Concrete' on screen means virtual manipulatives. These are interactive
  objects the pupil moves or groups, such as counters, blocks and sticks. A static picture remains
  pictorial and does not satisfy a 'concrete' clause."
- **Draw (ruling 13).** "Whenever a MATATAG competency says *draw*, an interactive visual formatter
  for that competency fulfils the written requirement; a freehand canvas is not required. … A
  non-interactive item, such as a multiple-choice question about drawing, still does not satisfy it."

`VISUAL RENDERED` and `rendered structure` lines describe what is actually drawn. A sentence that
mentions a picture is not a picture. The PROVIDER-VARIANT SEED MAP lists seeds that were sampled
deliberately; its labels are withheld on purpose and say nothing about any clause.

Reasoning: at least 60 characters, specific to that item and its samples (the filer refuses under
40, and reasoning that would read identically for any item is rejected as templating). PROVIDED
must name at least one seed that is printed for that item. Quote only text literally printed in
the packet, character for character; when in doubt, use no quotation marks.

Write one JSON array to the path the dispatcher gives you:

```
[
  {"item": "item_001", "verdict": "PROVIDED|NOT_PROVIDED", "seeds_showing_it": [11, 23],
   "reasoning": "...", "content_note": "optional: anything wrong with an item you noticed"}
]
```

One entry for every ITEM, none for anything else.

## B. Reviewer prompt (§5)

Generate it with `tests/judgment_batches.py --prompt` (`render_review_prompt`); never retype it.
Append exactly this block after its "Response shape" section, before the packet:

> Binding owner rulings for this review (quoted; apply them, do not re-decide them):
> - Ruling 12: "'Concrete' on screen means virtual manipulatives. These are interactive objects
>   the pupil moves or groups, such as counters, blocks and sticks. A static picture remains
>   pictorial and does not satisfy a 'concrete' clause."
> - Ruling 13: "Whenever a MATATAG competency says *draw*, an interactive visual formatter for that
>   competency fulfils the written requirement; a freehand canvas is not required."
> - Ruling 14: "`2 × 1 = ___` is in scope for *multiplication or division by 2, 3, 4, 5, and 10*
>   (`mat_g2_na_q3_7`): a factor of 1 is allowed when the other factor is a named table."
> - Ruling 18: "A fact belongs to the N table when EITHER factor is N."
> - Ruling 19: "A clause that is one item of a list in the competency … is PROVIDED when the
>   generator serves it by design and it is observed in at least 2 samples of a packet stratified
>   so that every sibling is sampled."
> - Themed names, objects and emoji come from a curated interest bank and are a deliberate
>   feature. Judge whether a theme INTERFERES with the mathematics, not whether it is appropriate.
> - Compare every hint against the item it serves: its numbers, operation and direction.
> - Write every `reasoning` and `rationale` at 60 characters or more. Quote only text printed in
>   the packet, character for character; when in doubt, use no quotation marks.

---

## C. The ruling texts this file draws on, verbatim from `docs/phase2_hardening_completion_plan.md`

<!-- ruling 1 -->
> 1. **The medium test.** When a clause names a medium, decide from the competency's grammar
>    which role it plays: the thing the learner must work IN (*illustrate/represent/model/draw
>    … using X*) → it must actually be rendered; a delivery mode or story context (*given orally
>    or in pictures*) → a worded context can satisfy it. Ambiguous → judge on the stricter
>    reading and say so. **Never encode the answer in the dispatch prompt** — this session's
>    first prompt did, asserting that any medium clause needs the medium present, and that is
>    the §6 analogue of the 2026-08-20 transcription defect.

<!-- ruling 9 -->
> 9. **PREVALENCE IS NOW PART OF THE STANDARD** (owner, 2026-09-22). An Attester must weigh
>    HOW OFTEN a clause is exhibited across the samples it is shown, not merely whether any
>    one sample exhibits it. This supersedes the packet format's silence on prevalence, which
>    the limitations list had named only in words.

<!-- ruling 12 -->
> 12. **'Concrete' on screen means virtual manipulatives.** These are interactive objects the pupil moves
>     or groups, such as counters, blocks and sticks. A static picture remains pictorial and does not
>     satisfy a 'concrete' clause.

<!-- ruling 13 -->
> 13. **'Draw' is satisfied by any interactive visual formatter.** Whenever a MATATAG competency says
>     *draw*, an interactive visual formatter for that competency fulfils the written requirement; a
>     freehand canvas is not required. This refines ruling 1's medium test and ruling 3 for the verb
>     *draw* only. A non-interactive item, such as a multiple-choice question about drawing, still does
>     not satisfy it.

<!-- ruling 15 -->
> 15. **Medium clauses are met by SET COMPOSITION to at least 50%** (owner, 2026-10-02). When a
>     competency names a medium the learner works in (*illustrate, represent, concrete, models,
>     draw*) and the node's allowed formatters already include visual or interactive ones that R-4's
>     uniform selection serves only incidentally, compose that node's allowed formatter set so that
>     visual or interactive formatters make up at least half of it. This follows R-3, and it never
>     uses a weight (R-4). Add fitting existing formatters where safe, and drop text formatters only
>     as far as needed. Text items remain a minority. Each set change is proved, re-attested, and
>     covered by a mutation.

<!-- ruling 19 -->
> 19. **Enumerated sibling clauses are judged by design, not by share of samples** (owner,
>     2026-10-07). A clause that is one item of a list in the competency (skip intervals, graph
>     orientations, likelihood words, coin and bill types, named figures) is PROVIDED when the
>     generator serves it by design and it is observed in at least 2 samples of a packet stratified
>     so that every sibling is sampled. Design means a variant or DNA path that produces it. Ruling
>     15's 50% standard applies to medium clauses by set composition, not to sibling items. A clause
>     that is not part of an enumeration stays under ruling 9 as written. No dispatch prompt may state
>     a numeric threshold that no ruling states.

<!-- ruling 20 -->
> 20. **Any model family may judge** (owner, 2026-10-07). This supersedes the 2026-09-25 decision that
>     reviewer families must be consistent, and the host-relative model rules (4, 10, 11) as
>     constraints on WHICH model judges. What stays absolute is that the identity names the model that
>     actually judged, and that no existing record is renamed. **Quorum for attestations: one
>     confirming judge.** Any attestation verdict that would clear or create a CONTRADICTED finding is
>     confirmed by one further independent blind judge on the same packet. Where the two disagree,
>     the confirming (later) judge's verdict stands. Named consequence: a single judge flipped 22.4% of
>     verdicts in W2 step 2, so this quorum accepts that noise level in exchange for cost. Records are
>     never edited; the confirming record supersedes by last-file-wins, as the validator already does.

<!-- ruling 21 -->
> 21. **A disputed reviewer claim is settled by one other reviewer** (owner, 2026-10-07). When the
>     dispatcher believes a non-PASS claim in a review is false (for example, a render at the cited
>     seed disproves it), the reply is not set aside on that belief. The node goes to one fresh blind
>     reviewer that has seen none of the earlier exchange, and that reviewer's verdict settles the
>     claim. The disproving render and the outcome are recorded in the evidence log. The existing
>     set-aside grounds are unchanged: an overall that contradicts its own verdicts, JSON still
>     unparseable after one repair, or a skipped sample.

<!-- ruling 22 -->
> 22. **Packet-only attester selectors are approved, with two conditions** (owner, 2026-10-07).
>     Ruling 19's stratification needs to know how to observe each sibling. Where a sibling has no
>     exact provider variant, or shares a broad one (`certain` and `impossible` share
>     `scenario_type = certain_impossible`; skip counts have none), `CAPABILITY_PROVIDERS` may carry
>     packet-only `attester_selectors`. These take no part in Phase-1 provision. The conditions:
>     (a) a selector observes **structured generator values only**, never a substring of learner-facing
>     question or answer text, because a phrase match such as "square" can also match "square units";
>     (b) **every required clause is classified**, either as a stratum (a reachable exact variant or a
>     selector) or as explicitly not enumerated, with the competency wording cited. A clause with
>     neither classification fails loudly by name. A hand-kept list of selectors must never let an
>     unlisted sibling be judged the old way in silence. This was raised by the GPT session's
>     `1c4f6f85` boundary. Its 21-capability selector table covered 37 of the 68 "rare" findings, and
>     nothing flagged the other 31.
