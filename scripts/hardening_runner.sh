#!/bin/bash
# Hardening runner — the OS-level supervisor that /loop cannot be.
#
# Why this exists
# ---------------
# `/loop` compiles to CronCreate, which is session-only and in-memory ("nothing is
# written to disk, and the job is gone when Claude exits"), fires only while the REPL
# is idle, and auto-expires after 7 days. It therefore cannot survive the two things
# an unattended multi-day run must survive: a dropped session and a 5-hour usage
# limit. This script lives outside the session and does.
#
# What it deliberately does NOT do (the retired daemon's four failures, 2026-08-19)
# ---------------------------------------------------------------------------------
#   * It does no pipeline work and makes no judgement about WHAT the work is. That is
#     the tick prompt's job. This script decides only *whether to start one*.
#   * It never measures liveness by git-commit mtime ("rewards committing over
#     verifying"). Liveness is hardening_supervisor.py's process-tree CPU scan.
#   * It has no `|| true` anywhere. Every exit code propagates. A monitor that cannot
#     report red is a monitor that reports green.
#   * It does not default to --dry-run. Dry run is opt-in, for testing this script.
#
# When this run ends
# ------------------
# The run ends when `local_only/scratch/HARDENING_DONE` exists -- a tick writes it only
# after run_all exits 0 twice cleanly and the green audit passed. Nothing else ends it:
# not a usage limit (it probes until the window reopens, however long that takes), not a
# failing tick (it backs off and retries), not a supervisor that returns something
# unexpected. A loop that gives up on transient trouble is a loop that reports green by
# being absent.
#
# To stop it by hand at any time:
#   touch local_only/scratch/HARDENING_STOP
#
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || { echo "FATAL: cannot cd to $REPO" >&2; exit 78; }

PY="$REPO/.venv/bin/python3"
SUPERVISOR="$REPO/scripts/hardening_supervisor.py"
RUN_DIR="$REPO/local_only/scratch/runner"
STOP_FILE="$REPO/local_only/scratch/HARDENING_STOP"
# The one terminal condition. A tick writes this only after run_all has exited 0 twice
# with no edits between AND the green audit passed -- exit 0 has been reached dishonestly
# three times, so the audit is part of the condition, not an optional extra.
DONE_FILE="$REPO/local_only/scratch/HARDENING_DONE"
LOG="$RUN_DIR/runner.log"

TICK_PROMPT="${HARDENING_TICK_PROMPT:-Read local_only/scratch/hardening_prompt.md and run one tick.}"
MODEL="${HARDENING_MODEL:-opus}"
TICK_CAP_SEC="${HARDENING_TICK_CAP_SEC:-5400}"      # 90 min: 50 min run_all + working room
IDLE_SLEEP_SEC="${HARDENING_IDLE_SLEEP_SEC:-1800}"  # NOTHING_TO_DO -> re-check in 30 min
BUSY_SLEEP_SEC="${HARDENING_BUSY_SLEEP_SEC:-300}"   # IN_FLIGHT -> someone else is working
PROBE_SLEEP_SEC="${HARDENING_PROBE_SLEEP_SEC:-2700}" # limit backoff: probe every 45 min, forever
# Consecutive tick failures do NOT end the run. They slow it down, so a genuinely broken
# state (bad binary, corrupt tree) idles instead of spinning a tick every 20 seconds and
# burning the usage window for nothing. Exponential, capped.
ERR_SLEEP_MIN="${HARDENING_ERR_SLEEP_MIN:-60}"
ERR_SLEEP_MAX="${HARDENING_ERR_SLEEP_MAX:-1800}"
DRY_RUN="${HARDENING_DRY_RUN:-0}"
# 0 = run until stopped. Any positive N exits cleanly after N ticks, which is how
# you smoke-test the loop without committing to an unattended run. Bounding ticks
# is the right knob: the sleeps below only fire on NOTHING_TO_DO / IN_FLIGHT / a
# usage-limit probe, so on success the loop has no interval to shorten.
MAX_TICKS="${HARDENING_MAX_TICKS:-0}"

# Exit codes from hardening_supervisor.py
# NEEDS_HUMAN=30 is retired (2026-08-23). No verdict ends the run on a judgement call;
# see hardening_supervisor.py's docstring. A stray 30 now falls to the catch-all below.
IN_FLIGHT=0; RESUME=10; NOTHING_TO_DO=20; HUNG_UNREAPED=40

mkdir -p "$RUN_DIR"

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$LOG"; }

# Run a command with a hard wall-clock cap. This host has no `timeout`/`gtimeout`,
# so the watchdog is bash-native. Returns 124 on timeout, else the command's status.
run_capped() {
    local cap="$1" out="$2"; shift 2
    "$@" >"$out" 2>&1 &
    local pid=$! waited=0
    while kill -0 "$pid" 2>/dev/null; do
        if (( waited >= cap )); then
            log "TIMEOUT: ${cap}s exceeded; killing pid $pid and its descendants"
            pkill -9 -P "$pid" 2>/dev/null
            kill -9 "$pid" 2>/dev/null
            wait "$pid" 2>/dev/null
            return 124
        fi
        sleep 10
        waited=$(( waited + 10 ))
    done
    wait "$pid"
}

# SUCCESS | LIMIT | ERROR — decided from the result JSON, never from exit code alone.
classify() {
    local f="$1"
    if grep -qiE "usage limit reached|out of usage credits" "$f" 2>/dev/null; then
        echo LIMIT; return
    fi
    if ! jq -e . "$f" >/dev/null 2>&1; then
        echo ERROR; return
    fi
    local api_status is_err subtype
    api_status="$(jq -r '.api_error_status // empty' "$f")"
    is_err="$(jq -r '.is_error // false' "$f")"
    subtype="$(jq -r '.subtype // empty' "$f")"
    if [[ "$api_status" == "429" ]]; then echo LIMIT; return; fi
    if [[ "$is_err" == "true" ]]; then echo ERROR; return; fi
    if [[ "$subtype" == "success" ]]; then echo SUCCESS; return; fi
    echo ERROR
}

run_tick() {
    local out="$1"
    if [[ "$DRY_RUN" == "1" ]]; then
        log "DRY RUN: would spawn -> claude -p <prompt> --output-format json --model $MODEL --permission-mode bypassPermissions"
        printf '{"is_error":false,"subtype":"success","api_error_status":null,"num_turns":1,"total_cost_usd":0,"result":"DRY_RUN"}\n' >"$out"
        return 0
    fi
    run_capped "$TICK_CAP_SEC" "$out" \
        claude -p "$TICK_PROMPT" \
            --output-format json \
            --model "$MODEL" \
            --permission-mode bypassPermissions
}

# One cheap call on the same model, to find out whether the usage window has reopened.
# Same model matters: a probe on a different model proves nothing about this one.
probe_window_open() {
    local out="$RUN_DIR/probe_$(date +%s).json"
    if [[ "$DRY_RUN" == "1" ]]; then log "DRY RUN: would probe"; return 0; fi
    run_capped 300 "$out" claude -p "Reply with exactly: PROBE" \
        --output-format json --model "$MODEL"
    local verdict; verdict="$(classify "$out")"
    rm -f "$out"
    [[ "$verdict" == "SUCCESS" ]]
}

# A usage limit is never a reason to end the run -- it is a pause. Probe until the window
# reopens, for as long as that takes. Returns 1 only when STOP/DONE appeared meanwhile, and
# the caller's next loop iteration exits on it.
backoff_until_window_reopens() {
    local n=0
    while true; do
        n=$(( n + 1 ))
        log "USAGE LIMIT: sleeping ${PROBE_SLEEP_SEC}s, then probe $n"
        sleep "$PROBE_SLEEP_SEC"
        [[ -f "$STOP_FILE" ]] && { log "STOP file appeared during backoff"; return 1; }
        [[ -f "$DONE_FILE" ]] && { log "DONE file appeared during backoff"; return 1; }
        if probe_window_open; then
            log "USAGE WINDOW REOPENED after $n probe(s) ($(( n * PROBE_SLEEP_SEC / 60 )) min) — resuming"
            return 0
        fi
        log "still limited (probe $n, $(( n * PROBE_SLEEP_SEC / 60 )) min so far)"
    done
}

log "=========================================================="
log "hardening runner starting | repo=$REPO"
log "  model=$MODEL  tick_cap=${TICK_CAP_SEC}s  dry_run=$DRY_RUN  max_ticks=$MAX_TICKS"
log "  prompt: $TICK_PROMPT"
log "  ends on: $DONE_FILE (verified green) — nothing else"
log "  stop by hand: touch $STOP_FILE"
log "=========================================================="

ticks=0; consec_err=0; err_sleep="$ERR_SLEEP_MIN"
while true; do
    if [[ -f "$DONE_FILE" ]]; then
        log "=========================================================="
        log "HARDENING_DONE present — verified green. Ending the run after $ticks tick(s)."
        log "  $(head -c 300 "$DONE_FILE" 2>/dev/null | tr '\n' ' ')"
        log "=========================================================="
        exit 0
    fi

    if [[ -f "$STOP_FILE" ]]; then
        log "STOP file present — exiting cleanly after $ticks tick(s)"
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
            log "  The run does not end on this. If it repeats, the supervisor itself is the bug."
            sleep "$err_sleep"
            err_sleep=$(( err_sleep * 2 )); (( err_sleep > ERR_SLEEP_MAX )) && err_sleep=$ERR_SLEEP_MAX
            continue ;;
    esac

    ticks=$(( ticks + 1 ))
    stamp="$(date +%m%d_%H%M%S)"
    out="$RUN_DIR/tick_${stamp}.json"
    log "--- tick $ticks starting (cap ${TICK_CAP_SEC}s) -> $out"

    run_tick "$out"; rc=$?
    result="$(classify "$out")"
    cost="$(jq -r '.total_cost_usd // "?"' "$out" 2>/dev/null)"
    turns="$(jq -r '.num_turns // "?"' "$out" 2>/dev/null)"
    log "--- tick $ticks finished: $result (exit $rc, turns $turns, cost \$$cost)"

    if (( MAX_TICKS > 0 && ticks >= MAX_TICKS )); then
        log "MAX_TICKS=$MAX_TICKS reached — exiting cleanly. This is a bound, not a verdict:"
        log "  the last tick's own result was $result."
        exit 0
    fi

    case "$result" in
        SUCCESS)
            consec_err=0; err_sleep="$ERR_SLEEP_MIN" ;;
        LIMIT)
            consec_err=0; err_sleep="$ERR_SLEEP_MIN"
            # `continue` only fires if STOP/DONE appeared; the top of the loop exits on it.
            backoff_until_window_reopens || continue ;;
        ERROR)
            consec_err=$(( consec_err + 1 ))
            log "tick error (consecutive: $consec_err). The run does NOT end on errors. Head of output:"
            head -c 600 "$out" | tee -a "$LOG"; echo | tee -a "$LOG"
            log "backing off ${err_sleep}s before the next tick"
            sleep "$err_sleep"
            err_sleep=$(( err_sleep * 2 )); (( err_sleep > ERR_SLEEP_MAX )) && err_sleep=$ERR_SLEEP_MAX ;;
    esac
done
