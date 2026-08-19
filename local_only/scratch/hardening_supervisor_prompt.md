# Hardening supervisor — the only thing you need to paste

    Run the hardening supervisor: local_only/scratch/hardening_supervisor_prompt.md

Everything else is on disk. Do not paste state into the prompt; state that lives in a prompt goes
stale the moment a tick lands, and a stale instruction costs a whole unit before anyone notices.

---

## Step 1 — Run the cheap check first. Always. It takes about a second.

```bash
PYTHONPATH=. .venv/bin/python3 scripts/hardening_supervisor.py --reap
```

`--reap` kills hung processes. Include it: a hung background job is what silently killed the previous
loop — cron ticks fire only while the REPL is idle, so one stuck process meant no tick fired again for
five hours, and because it fired nothing it also reported nothing.

The script never does pipeline work and never runs `run_all`. It answers one question — *should a tick
start right now?* — and exits with a verdict:

| exit | verdict | what you do |
|---:|---|---|
| `0` | `IN_FLIGHT` | A healthy process is running. **Report the one-line status and stop.** Do not start a second tick; two `run_all`s contend and neither is trustworthy. |
| `10` | `RESUME` | Work is outstanding or a unit was interrupted. **Go to Step 2.** |
| `20` | `NOTHING_TO_DO` | No findings, nothing in flight. Report in three lines and stop. Do not invent work. |
| `30` | `NEEDS_HUMAN` | Genuinely inconsistent state — e.g. the capability contract could not be evaluated at all. Report what is inconsistent and stop; do not paper over it with a tick. |
| `40` | `HUNG_UNREAPED` | Hung processes found and left running (you omitted `--reap`). **Re-run with `--reap`, then act on the new verdict.** Nothing else in the report is trustworthy until they are gone: a hung job blocks the next tick from ever starting, which is how the loop went dark for five hours on 2026-08-19. |

**What the script's output is, and is not.** It is a *claim*, produced to decide whether to act. It is
never evidence of state. Do not quote its numbers in a tick report and do not skip §0 because you read
it. A status file trusted as evidence is exactly how the ledger started lying.

It deliberately does **not** measure liveness by git-commit mtime. The retired daemon did, and the
postmortem names the consequence: *"rewards committing over verifying."* An agent committing garbage
hourly looks maximally alive. Liveness here is running processes and their CPU-to-elapsed ratio, a
modified tracked tree, and ledger age.

## Step 2 — Only on `RESUME`: run one tick

1. Read `local_only/scratch/hardening_loop_prompt.md` — the durable protocol. Hard rules, paid-for
   hazards, the §0 census scripts, tick types, runtime. It carries **no dated state**, so nothing in
   it expires.
2. Read the `Next tick should:` line the supervisor printed. That is your predecessor's handoff and
   it is the most valuable thing in the ledger — it exists so you do not re-derive their reasoning.
3. **Run §0 yourself anyway.** Re-derive every number from disk. Where §0 disagrees with the ledger,
   the supervisor, or anything you were told, **your measurement wins and the ledger records the
   drift.** Two prompts in a row have shipped stale premises; §0 is why that is survivable.
4. Work complete units back to back, committing each atomically, for as long as your budget allows.
   Stop when low on room — never mid-unit, never with an uncommitted tree.

## Step 3 — Before you finish, every time

- **No background job may be left outstanding.** Either `run_all` has landed and you recorded its
  exit line, or you killed it and said so. An outstanding job is what stops the next tick from ever
  starting. This is the single rule that would have prevented the five-hour outage.
- Ledger entry appended (protocol §4), ending with a specific `Next tick should:`.
- `validation_reports/HARDENING_EVIDENCE.md` entry for any commit that changed pipeline behaviour,
  with verbatim command output (Rule 7).
- Re-run the supervisor once at the end. It rewrites `hardening_status.json`, which is what the next
  wake-up reads.

## The goal — `run_all` exits 0, and the gate is what makes that mean something

**Exit 0 is the definition of done** (CLAUDE.md). It was gamed three times not because it is the
wrong target but because the gate behind it was incomplete. The answer is not a different goal — it
is a gate that cannot be cheaply satisfied. §6F now makes an unexamined provider claim a *failure*,
so exit 0 is unreachable until every declared capability has been judged by a blind Attester on
content that still renders.

**This harness is the foundation the remaining MATATAG grade levels get built on.** A gate that lets
one bad claim through does not let one bug through — it certifies the method that produces every
later grade. Closing a hole in the harness is never a detour from the node work; it is the higher-
leverage half of it.

**Within a tick, do not optimise the failure count.** It is the work queue, not the score, and it can
always be driven down by weakening something. The supervisor prints three numbers that cannot be:

```
capability findings: 843   <- the work queue
COVERAGE: attested 5/787 | reviewed 151/151 | mutations 11
```

The Attester never sees the provider table, the Reviewer never sees the generator, and a mutation
counts only when a planted bug actually made a check go red. **Failures rising while coverage rises
is progress. Failures falling while coverage stays flat is the signature of every past defeat.**
Report both movements; never a falling failure count alone.

Attestation scope is **all declared capabilities — 787 (node, capability) pairs**, not the 484 table
rows: a verdict is about specific rendered content, so the same capability on two nodes needs two
verdicts. Record every one in `validation_reports/attestation/<batch>.json` **with its
`packet.samples_judged`**, or §6F fails the batch as uncheckable.

