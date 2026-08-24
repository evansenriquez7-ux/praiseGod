#!/bin/bash
# Gemini / AGY Hardening Runner — OS-level supervisor for autonomous ticks.
#
# Usage:
#   HARDENING_DRY_RUN=0 HARDENING_MAX_TICKS=0 \
#   HARDENING_TICK_PROMPT="Read local_only/scratch/gemini_hardening_loop_prompt.md and run one tick. Campaign: ..." \
#     nohup caffeinate -dims bash scripts/gemini_hardening_runner.sh \
#     >> local_only/scratch/runner/gemini_nohup.log 2>&1 &
#
# To stop cleanly at any time:
#   touch local_only/scratch/HARDENING_STOP
#
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || { echo "FATAL: cannot cd to $REPO" >&2; exit 78; }

PY="$REPO/.venv/bin/python3"
SUPERVISOR="$REPO/scripts/hardening_supervisor.py"
RUN_DIR="$REPO/local_only/scratch/runner"
STOP_FILE="$REPO/local_only/scratch/HARDENING_STOP"
DONE_FILE="$REPO/local_only/scratch/HARDENING_DONE"
LOG="$RUN_DIR/gemini_runner.log"

TICK_PROMPT="${HARDENING_TICK_PROMPT:-Read local_only/scratch/gemini_hardening_loop_prompt.md and run one tick.}"
MODEL="${HARDENING_MODEL:-}"
TICK_CAP_SEC="${HARDENING_TICK_CAP_SEC:-5400}"      # 90 min cap
IDLE_SLEEP_SEC="${HARDENING_IDLE_SLEEP_SEC:-1800}"  # 30 min on NOTHING_TO_DO
BUSY_SLEEP_SEC="${HARDENING_BUSY_SLEEP_SEC:-300}"   # 5 min on IN_FLIGHT
PROBE_SLEEP_SEC="${HARDENING_PROBE_SLEEP_SEC:-2700}" # 45 min on rate limit
ERR_SLEEP_MIN="${HARDENING_ERR_SLEEP_MIN:-60}"
ERR_SLEEP_MAX="${HARDENING_ERR_SLEEP_MAX:-1800}"
DRY_RUN="${HARDENING_DRY_RUN:-0}"
MAX_TICKS="${HARDENING_MAX_TICKS:-0}"

# Exit codes from hardening_supervisor.py
IN_FLIGHT=0; RESUME=10; NOTHING_TO_DO=20; HUNG_UNREAPED=40

mkdir -p "$RUN_DIR"

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$LOG"; }

run_capped() {
    local cap="$1" out="$2"; shift 2
    set -m
    "$@" >"$out" 2>&1 </dev/null &
    local pid=$! waited=0
    set +m
    while kill -0 "$pid" 2>/dev/null; do
        if (( waited >= cap )); then
            log "TIMEOUT: ${cap}s exceeded; killing process group $pid"
            kill -9 -"$pid" 2>/dev/null
            wait "$pid" 2>/dev/null
            return 124
        fi
        sleep 10
        waited=$(( waited + 10 ))
    done
    wait "$pid"
}

classify() {
    local f="$1"
    if ! jq -e . "$f" >/dev/null 2>&1; then
        grep -qiE "usage limit|resource_exhausted|rate limit|quota exceeded" "$f" 2>/dev/null \
            && echo LIMIT || echo ERROR
        return
    fi
    local api_status is_err subtype status
    api_status="$(jq -r '.api_error_status // empty' "$f")"
    is_err="$(jq -r '.is_error // false' "$f")"
    subtype="$(jq -r '.subtype // empty' "$f")"
    status="$(jq -r '.status // empty' "$f")"
    if [[ "$api_status" == "429" || "$api_status" == "RESOURCE_EXHAUSTED" ]]; then echo LIMIT; return; fi
    if [[ "$is_err" == "true" ]] \
       && jq -r '.result // ""' "$f" | grep -qiE "usage limit|resource_exhausted|rate limit|quota exceeded"; then
        echo LIMIT; return
    fi
    if [[ "$is_err" == "true" ]]; then echo ERROR; return; fi
    if [[ "$status" == "SUCCESS" || "$subtype" == "success" ]]; then echo SUCCESS; return; fi
    if [[ "$status" == "ERROR" || "$subtype" == "error" ]]; then echo ERROR; return; fi
    echo ERROR
}

run_tick() {
    local out="$1"
    if [[ "$DRY_RUN" == "1" ]]; then
        log "DRY RUN: would spawn -> agent tick with prompt: $TICK_PROMPT"
        printf '{"is_error":false,"subtype":"success","api_error_status":null,"num_turns":1,"total_cost_usd":0,"result":"DRY_RUN"}\n' >"$out"
        return 0
    fi
    # If AGY CLI is available, run via agy / agentic runner, else log tick dispatch
    if command -v agy >/dev/null 2>&1; then
        if [[ -n "$MODEL" ]]; then
            run_capped "$TICK_CAP_SEC" "$out" agy -p "$TICK_PROMPT" --output-format json --dangerously-skip-permissions --print-timeout "${TICK_CAP_SEC}s" --model "$MODEL"
        else
            run_capped "$TICK_CAP_SEC" "$out" agy -p "$TICK_PROMPT" --output-format json --dangerously-skip-permissions --print-timeout "${TICK_CAP_SEC}s"
        fi
    elif command -v claude >/dev/null 2>&1; then
        if [[ -n "$MODEL" ]]; then
            run_capped "$TICK_CAP_SEC" "$out" claude -p "$TICK_PROMPT" --output-format json --permission-mode bypassPermissions --model "$MODEL"
        else
            run_capped "$TICK_CAP_SEC" "$out" claude -p "$TICK_PROMPT" --output-format json --permission-mode bypassPermissions
        fi
    else
        log "Runner dispatching tick via python supervisor harness..."
        run_capped "$TICK_CAP_SEC" "$out" "$PY" -c "
import sys
print('Executing tick prompt: $TICK_PROMPT')
"
    fi
}

log "=========================================================="
log "Gemini / AGY hardening runner starting | repo=$REPO"
log "  model=$MODEL  tick_cap=${TICK_CAP_SEC}s  dry_run=$DRY_RUN  max_ticks=$MAX_TICKS"
log "  prompt: $TICK_PROMPT"
log "  ends on: $DONE_FILE (verified green) — nothing else"
log "  stop by hand: touch $STOP_FILE"
log "=========================================================="

ticks=0; consec_err=0; err_sleep="$ERR_SLEEP_MIN"; total_cost=0
while true; do
    if [[ -f "$DONE_FILE" ]]; then
        log "=========================================================="
        log "HARDENING_DONE present — verified green. Ending the run after $ticks tick(s)."
        log "  $(head -c 300 "$DONE_FILE" 2>/dev/null | tr '\n' ' ')"
        log "=========================================================="
        exit 0
    fi

    if [[ -f "$STOP_FILE" ]]; then
        log "STOP file present — exiting cleanly after $ticks tick(s)."
        exit 0
    fi

    "$PY" "$SUPERVISOR" --reap >>"$LOG" 2>&1
    verdict=$?

    case "$verdict" in
        "$NOTHING_TO_DO")
            log "supervisor: NOTHING_TO_DO — sleeping ${IDLE_SLEEP_SEC}s"
            sleep "$IDLE_SLEEP_SEC"; continue ;;
        "$IN_FLIGHT")
            log "supervisor: IN_FLIGHT — work already running; sleeping ${BUSY_SLEEP_SEC}s"
            sleep "$BUSY_SLEEP_SEC"; continue ;;
        "$RESUME"|"$HUNG_UNREAPED")
            : ;;
        *)
            log "supervisor: unexpected exit $verdict — backing off ${err_sleep}s and retrying."
            sleep "$err_sleep"
            err_sleep=$(( err_sleep * 2 )); (( err_sleep > ERR_SLEEP_MAX )) && err_sleep=$ERR_SLEEP_MAX
            continue ;;
    esac

    ticks=$(( ticks + 1 ))
    stamp="$(date +%m%d_%H%M%S)"
    out="$RUN_DIR/gemini_tick_${stamp}.json"
    log "--- tick $ticks starting (cap ${TICK_CAP_SEC}s) -> $out"

    run_tick "$out"; rc=$?
    if (( rc == 124 )); then result=TIMEOUT; else result="$(classify "$out")"; fi
    log "--- tick $ticks finished: $result (exit $rc)"

    if (( MAX_TICKS > 0 && ticks >= MAX_TICKS )); then
        log "MAX_TICKS=$MAX_TICKS reached — exiting cleanly."
        exit 0
    fi

    case "$result" in
        SUCCESS|TIMEOUT)
            consec_err=0; err_sleep="$ERR_SLEEP_MIN" ;;
        LIMIT)
            consec_err=0; err_sleep="$ERR_SLEEP_MIN"
            log "RATE / USAGE LIMIT: sleeping ${PROBE_SLEEP_SEC}s before retry"
            sleep "$PROBE_SLEEP_SEC" ;;
        ERROR)
            consec_err=$(( consec_err + 1 ))
            log "tick error (consecutive: $consec_err). Backing off ${err_sleep}s"
            sleep "$err_sleep"
            err_sleep=$(( err_sleep * 2 )); (( err_sleep > ERR_SLEEP_MAX )) && err_sleep=$ERR_SLEEP_MAX ;;
    esac
done
