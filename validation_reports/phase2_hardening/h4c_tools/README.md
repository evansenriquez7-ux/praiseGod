# h4c_tools — batch H4-C's working tools, kept for the next session

Copied 2026-10-16 from `local_only/scratch/h4c/`, which is gitignored. Read the scripts before you run them.

- `chain.sh` is the re-proof chain: `zsh validation_reports/phase2_hardening/h4c_tools/chain.sh <batch>`, run
  detached with `nohup`. It reads the release-shard count from this chain's own benchmark, and moves stale shard
  receipts aside before it writes new ones.
- `h4c.py`, `taf.sh`, `tk.sh`, `logd.sh` and `mkdisp.py` take, audit and file §17 judge replies, and write dispatch
  texts. They assume H4-C's scratch layout: `local_only/scratch/h4c/{keys,prompts,replies,transcripts,ledger.json,
  agents.map}`. Copy and re-prove them before reuse; the filer they call is `tests/stem_file.py`.
- `render_dump.py`, `grounds.py` and `r49brief.py` are the ruling 49/51 render checks. Run them from the repo root
  with `PYTHONPATH=.`. `render_dump.py` writes `local_only/scratch/h4c/renders/<lc>.json`.
- `stats.py` gives the campaign counts quoted in the "H4-C" evidence entry.
- `r49.log` holds the ruling 49/51 result for every standing FAIL: one line per lc giving the real grounds, the
  disproofs and the action, plus the ruling-21 outcome lines. It is generator-queue context.
- `dispatch.log` is the timestamped log of every H4-C dispatch, SETASIDE and CORRECTION.
