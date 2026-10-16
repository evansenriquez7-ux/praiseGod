#!/bin/bash
# usage: ./logd.sh <dispatch_id> <agentId> [note]  -- appends one agents.map line and one dispatch.log line
set -euo pipefail
[ $# -ge 2 ] || { echo "usage: logd.sh did agentId [note]" >&2; exit 2; }
grep -q "^$1 " agents.map && { echo "already mapped: $1" >&2; exit 3; }
echo "$1 $2" >> agents.map
echo "$(date '+%F %T') DISPATCH $1 agent=$2 (HV8, 6ebbd1b3${3:+; $3})" >> dispatch.log
echo "logged $1 $2"
