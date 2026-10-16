#!/bin/zsh
# take by agentId using agents.map: tk.sh <agentId>
cd /Users/enrichmentcap/Documents/antigravity/ccmed/local_only/scratch/h4c
did=$(awk -v a="$1" '$2==a{print $1}' agents.map); [ -n "$did" ] || { echo "no dispatch for $1"; exit 1; }
./take.sh $did $1 && echo "$(date '+%F %T') TAKEN $did" >> dispatch.log
