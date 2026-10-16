#!/bin/bash
# usage: ./taf.sh <agentId>  -- take the reply, audit it, and file it only if the audit is clean
set -uo pipefail
d=$(awk -v a="$1" '$2==a{print $1}' agents.map)
[ -n "$d" ] || { echo "no dispatch for $1" >&2; exit 2; }
./tk.sh "$1" || exit 3
PYTHONPATH=../../.. ../../../.venv/bin/python h4c.py audit "$d" > "audit_hv8/$d.json" 2>&1
rc=$?
if [ $rc -ne 0 ]; then echo "AUDIT-PROBLEMS $d: $(python3 -c "import json,sys;print(json.loads(open(sys.argv[1]).read().strip().splitlines()[-1])['problems'])" audit_hv8/$d.json | cut -c1-500)"; exit 1; fi
PYTHONPATH=../../.. ../../../.venv/bin/python h4c.py file "$d" 2>&1 | tail -1
