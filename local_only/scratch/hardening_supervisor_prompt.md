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
| `30` | `NEEDS_HUMAN` | Inconsistent state. Report what is inconsistent and stop — do not paper over it with a tick. |

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

## The goal — so no tick optimises the wrong number

**A tick optimises VERIFIED COVERAGE, not the failure count** (established 2026-08-20). The
supervisor prints it:

```
capability findings: 60   <- a cost, not the goal
COVERAGE (the goal): attested 5/484 (1.0%) | reviewed 151/151 | mutations 9
```

A failure count can always be driven down by weakening something, and it was, three times. These
three numbers cannot be: the Attester never sees the provider table, the Reviewer never sees the
generator, and a mutation counts only when a planted bug actually made a check go red.

**Failures rising while coverage rises is progress.** Failures falling while coverage stays flat is
the signature of every past defeat. Report both movements, always. Never report a falling failure
count on its own.

Attestation scope is **all 484 provider entries** (decided 2026-08-20). Record every verdict in
`validation_reports/attestation/<batch>.json` — a verdict that exists only in a commit message is not
countable, and coverage that is not countable is not a goal.

`run_all` exiting 0 is **not** the objective and never was. It has been reached dishonestly three
times, and the tree is currently red on purpose: earlier ticks converted a false green into an earned
red. Every fast route back to green is forbidden — re-widening `CAPABILITY_PROVIDERS`, deleting §6D,
narrowing a declaration, rewriting a test around its own failure.

The objective is green **that survives audit**: every node carries a genuine blind PASS review, every
node declares what its competency requires and the pipeline genuinely provides it, and `run_all` exits
0 with no wildcard provider, no fabricated review, and no test rewritten around its own failure
anywhere in the tree. A tick that ends redder than it started because something dishonest was removed
has succeeded.
