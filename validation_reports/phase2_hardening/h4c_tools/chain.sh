#!/bin/zsh
# Re-proof chain (copied from H4-C's chain50.sh). usage: zsh chain.sh <batch>  -> logs in local_only/scratch/<batch>/chain
# Shard count comes from THIS chain's benchmark (2026-10-15: a hard-coded 6 put shards 3-5 over the 1800 s target
# on 0388fecf while the benchmark said 8).
cd /Users/enrichmentcap/Documents/antigravity/ccmed; [ -n "$1" ] || { echo 'usage: zsh chain.sh <batch>' >&2; exit 2; }; L=local_only/scratch/$1/chain; mkdir -p $L; export PYTHONPATH=.
step() { local name=$1; shift; echo "START $name $(date +%H:%M:%S)" >> $L/progress.log
  "$@" > $L/$name.log 2>&1; local rc=$?; echo "END $name EXIT $rc $(date +%H:%M:%S)" >> $L/progress.log; }
step regen .venv/bin/python -m scripts.regen_formatter_exclusions
step benchmark .venv/bin/python -m tests.obligation_executor --tier benchmark --sample-size 1000
N=$(.venv/bin/python -c "import json;print(json.load(open('validation_reports/phase2_hardening/obligation_benchmark.json'))['projection']['recommended_shard_count'])")
echo "shard count from benchmark: $N" >> $L/progress.log
step frontend env DATABASE_URL= .venv/bin/python tests/frontend_suite.py
step corpus .venv/bin/python tests/mutation_harness.py
git grep -n "planted mutation" -- backend scripts frontend/src data > $L/escaped_plants.log 2>&1
echo "escaped-plant grep lines: $(wc -l < $L/escaped_plants.log)" >> $L/progress.log
mkdir -p $L/old_receipts; mv validation_reports/phase2_hardening/obligation_release_shards/shard_*_of_*.json $L/old_receipts/ 2>/dev/null
for i in $(seq 0 $((N - 1))); do step shard$i .venv/bin/python -m tests.obligation_executor --tier release --shard-count $N --shard-index $i; done
step verify .venv/bin/python -m tests.obligation_executor --tier verify-release
step run_all .venv/bin/python -m backend.app.practice_gen.validation.run_all
echo "CHAIN DONE $(date +%H:%M:%S)" >> $L/progress.log
