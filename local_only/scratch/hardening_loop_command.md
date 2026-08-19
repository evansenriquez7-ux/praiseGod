# The command to paste

```
Run the hardening supervisor: local_only/scratch/hardening_supervisor_prompt.md
```

That is the whole thing. **Do not paste state into the prompt.**

This file previously held a ~20-line prompt that restated the tree's condition — verdict counts,
provider counts, which units were done. Every one of those facts went stale the moment a tick landed,
and the stale copy kept getting re-pasted: on 2026-08-20 it told an agent that `run_all` exits 0
(it exits 1), that `bounds` is inert (it now carries 15 capabilities), and to restore two weakened
tests (done the previous evening as `fce7f8df`). A prompt that carries state is a prompt that lies.

State now lives in exactly one place per lifecycle:

| artifact | holds | changes |
|---|---|---|
| `hardening_supervisor_prompt.md` | what to do, and in what order | rarely |
| `hardening_loop_prompt.md` | durable protocol — rules, hazards, §0 scripts, tick types | rarely |
| `hardening_ledger.md` | current state + the work queue (`Next tick should:`) | every tick |
| `hardening_status.json` | machine-readable snapshot for the cheap check | every supervisor run |

## On scheduling

`/loop` is **session-only and in-memory** — it dies with the terminal, and during a rate-limit window
the REPL is never idle-and-healthy, so ticks do not fire. It cannot survive the two things worth
surviving (a dropped session, a 5-hour limit). Do not use it for durability.

For an unattended heartbeat, run the supervisor itself on a schedule — it is ~1 second and costs
nothing when there is no work:

```bash
PYTHONPATH=. .venv/bin/python3 scripts/hardening_supervisor.py --reap
```

For a schedule that outlives this session, use `/schedule` (cloud routine). Two things must be true
first: the **8 unpushed commits** need pushing, and the untracked artifacts under `local_only/` need
`git add -f` (the directory is gitignored, though 19 files in it are already tracked).
