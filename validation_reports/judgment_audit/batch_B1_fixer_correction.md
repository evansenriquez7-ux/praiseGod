# Fixer correction to `batch_B1.json` — 2026-08-12

The evaluator's audit artifact `batch_B1.json` is left exactly as filed. This note records one
finding in it that the Fixer verified and **rejected**, so a later tick does not act on it.

## Rejected void: `mat_g1_na_q1_8`

`batch_B1.json` lists `mat_g1_na_q1_8` in `voided_nodes`, on the grounds that the review's
`comprehensive_coverage` rationale claims no item uses 0 as an addend, while — per the evaluator —
"seed 45 in that node's own packet is literally `0 + 2 = ___`".

**That claim is false.** Enumerated from the packet the reviewer was given, all 18 samples:

```
seed   42 [mcq]                What is 1 + 1?                                  -> 2
seed   43 [mcq]                What is 1 + 2?                                  -> 3
seed   44 [true_false]         2 + 1 = 3. True or False?                       -> True
seed   45 [cloze]              1 + 2 = ___                                     -> 3      <-- not "0 + 2"
seed   46 [cloze]              1 + 2 = ___                                     -> 3
seed   50 [set_fill_in_blank]  Show 1 + 2 on the number line.                  -> 3
seed   55 [read_mcq]           How many items are there in total?              -> D
seed   84 [read_fill_in_blank] The two parts are 1 and 1. What is the sum?     -> 2
seed   85 [error_detect]       Maria says: 2 + 1 = 2. Is Maria correct?        -> has_error
seed  500 [read_mcq]           How many items are there in total?              -> B
seed  501 [true_false]         15 + 2 = 17. True or False?                     -> True
seed  502 [mcq]                What is 4 + 14?                                 -> 18
seed  601 [true_false]         Pia is on step 2. Pia climbs up 1 more steps... -> True
seed  603 [true_false]         1 + 1 = 1. True or False?                       -> False
seed  608 [error_detect]       Rico says: 2 + 1 = 4. Is Rico correct?          -> has_error
seed  611 [true_false]         2 + 1 = 4. True or False?                       -> False
seed  613 [mcq]                Is 1 + 2 the same as 2 + 1?                     -> True
seed  614 [mcq]                Start at 1. Count up 1 more...                  -> 2
```

Not one sample uses 0 as an addend; no sample's `question_text` contains the character `0` at all.
The reviewer's claim was accurate and its `FAIL` verdict is earned: this node's competency is
*"the sum of zero and any number is equal to the number, and changing the order of the addends does
not change the sum"*, and the identity half is never demonstrated, while only seed 613
(`Is 1 + 2 the same as 2 + 1?`) demonstrates commutativity.

**Disposition:** the review for `mat_g1_na_q1_8` is **kept**. It was not re-reviewed.

Reproduce:

```
PYTHONPATH=. .venv/bin/python3 -m backend.app.practice_gen.validation.judgment_packets \
  --node mat_g1_na_q1_8
```

## Note on evaluator reliability

The evaluator's other 24 nodes checked out, and its independent re-judgment matched the filed verdict
5/5. But this is the second instance in one tick of an agent asserting a specific sample value that the
packet does not contain — the same species of defect the evaluator itself correctly caught in
`mat_g1_na_q2_3`. **An evaluator's void is a claim, not a verdict: verify it against the packet before
re-dispatching a node.** Confirmed voids this tick were `mat_g1_na_q2_3` and `mat_g1_na_q3_5`; both
were re-reviewed blind by a third reviewer.
