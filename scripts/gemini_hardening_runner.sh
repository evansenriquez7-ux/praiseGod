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
# Main agent defaults to active environment setting: Gemini 3.7 Flash (High Effort)
MODEL="${HARDENING_MODEL:-}"
EFFORT="${HARDENING_EFFORT:-}"
TICK_CAP_SEC="${HARDENING_TICK_CAP_SEC:-5400}"      # 90 min cap
IDLE_SLEEP_SEC="${HARDENING_IDLE_SLEEP_SEC:-1800}"  # 30 min on NOTHING_TO_DO
BUSY_SLEEP_SEC="${HARDENING_BUSY_SLEEP_SEC:-300}"   # 5 min on IN_FLIGHT
PROBE_SLEEP_SEC="${HARDENING_PROBE_SLEEP_SEC:-2700}" # 45 min on rate limit
ERR_SLEEP_MIN="${HARDENING_ERR_SLEEP_MIN:-60}"
ERR_SLEEP_MAX="${HARDENING_ERR_SLEEP_MAX:-1800}"
DRY_RUN="${HARDENING_DRY_RUN:-0}"
MAX_TICKS="${HARDENING_MAX_TICKS:-0}"
# A usage limit is a pause, not an ending -- but only while the pause is shorter than
# the run. A weekly quota states a reset ~137h out; probing that every 45 minutes is
# ~183 pointless calls across 5.7 days. Past this bound the runner ends cleanly and
# says why, instead of burning the window it is waiting for.
MAX_LIMIT_WAIT_SEC="${HARDENING_MAX_LIMIT_WAIT_SEC:-21600}"   # 6h
MAX_CONSEC_LIMIT="${HARDENING_MAX_CONSEC_LIMIT:-8}"           # when the reset is unstated
# Anti-spin. On 2026-08-24 the campaign's target band emptied at tick 33 while the
# supervisor still said RESUME, so 455 consecutive ticks committed nothing but a ledger
# entry about having nothing to do. No prompt wording can be trusted to notice that;
# the runner counts it mechanically and stops.
NOOP_TICK_LIMIT="${HARDENING_NOOP_TICK_LIMIT:-12}"

# Exit codes from hardening_supervisor.py
IN_FLIGHT=0; RESUME=10; NOTHING_TO_DO=20; STALLED=30; HUNG_UNREAPED=40

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
    # Not JSON at all (a crashed binary, a truncated write): the phrase is the only
    # signal there is.
    if ! jq -e . "$f" >/dev/null 2>&1; then
        grep -qiE "usage limit|resource.?exhausted|rate limit|quota (exceeded|reached)" "$f" 2>/dev/null \
            && echo LIMIT || echo ERROR
        return
    fi
    # Two CLIs, two schemas, and this runner can dispatch to either. `claude -p --output-format
    # json` emits {is_error, subtype, result, api_error_status}; `agy --output-format json`
    # emits {status, response, error}. Reading only the first set is how a quota exhaustion
    # ("Individual quota reached ... Resets in 137h47m17s") classified as a generic ERROR on
    # 2026-08-26 and took the 30-minute error backoff forever instead of the limit path.
    local api_status is_err subtype st
    api_status="$(jq -r '.api_error_status // empty' "$f")"
    is_err="$(jq -r '.is_error // false' "$f")"
    subtype="$(jq -r '.subtype // empty' "$f")"
    st="$(jq -r '.status // empty' "$f")"

    if [[ "$api_status" == "429" || "$api_status" == "RESOURCE_EXHAUSTED" ]]; then echo LIMIT; return; fi

    # The phrase is authoritative ONLY on a run that actually failed. Grepping the whole
    # document first classified a *successful* tick as LIMIT whenever its own report
    # mentioned one -- which the tick protocol actively invites it to write.
    if [[ "$is_err" == "true" || "$st" == "ERROR" ]] \
       && _limit_blob "$f" | grep -qiE "usage limit|resource.?exhausted|rate limit|quota (exceeded|reached)"; then
        echo LIMIT; return
    fi
    if [[ "$is_err" == "true" || "$st" == "ERROR" ]]; then echo ERROR; return; fi
    if [[ "$st" == "SUCCESS" || "$subtype" == "success" ]]; then echo SUCCESS; return; fi
    echo ERROR
}

# Every field either CLI might carry the limit text in, as one string.
_limit_blob() {
    jq -r '[.result?, .error?, .response?, .message?] | map(select(type == "string")) | join(" ")' \
        "$1" 2>/dev/null
}

# Seconds until the usage window reopens, or empty when the payload does not say.
# agy states it as "Resets in 137h47m17s"; claude appends a unix epoch ("...|1755950400").
limit_reset_seconds() {
    local blob epoch now h m sec
    blob="$(_limit_blob "$1")"

    epoch="$(printf '%s' "$blob" | grep -oE '\|[0-9]{10}' | tr -d '|' | head -1)"
    if [[ -n "$epoch" ]]; then
        now="$(date +%s)"
        if (( epoch > now )); then echo $(( epoch - now )); return; fi
    fi

    if [[ "$blob" =~ [Rr]esets\ in\ ([0-9]+)h([0-9]+)m([0-9]+)s ]]; then
        h="${BASH_REMATCH[1]}"; m="${BASH_REMATCH[2]}"; sec="${BASH_REMATCH[3]}"
        echo $(( h * 3600 + m * 60 + sec )); return
    fi
    if [[ "$blob" =~ [Rr]esets\ in\ ([0-9]+)h([0-9]+)m ]]; then
        h="${BASH_REMATCH[1]}"; m="${BASH_REMATCH[2]}"
        echo $(( h * 3600 + m * 60 )); return
    fi
    if [[ "$blob" =~ [Rr]esets\ in\ ([0-9]+)m ]]; then
        echo $(( BASH_REMATCH[1] * 60 )); return
    fi
    echo ""
}

# A tick that moved nothing but its own bookkeeping did not work. The ledger, the status
# file and the graph cache are all bookkeeping; anything else counts.
tick_was_productive() {
    local before="$1" after="$2"
    [[ "$before" != "$after" ]] || return 1
    git diff --name-only "$before" "$after" 2>/dev/null \
        | grep -qvE '(hardening_ledger\.md|hardening_status\.json|^graphify-out/)'
}

# The run's terminal condition used to be a file's existence, and nothing read its
# contents, re-ran run_all, or checked that the §10 Green Audit had happened. §10 is a
# prompt instruction -- the same class of guarantee that produced 455 consecutive no-op
# ticks on 2026-08-24. In a system whose own status file is stamped "A claim, not
# evidence", this was the last place a claim was accepted as evidence, and it was the
# place that ended the run declaring victory.
#
# The supervisor is now the arbiter: it counts §1 (matrix), §5 (judgment) and §6
# (capability), and refuses to trust a matrix report that is partial or older than the
# generators it describes. NOTHING_TO_DO from it is a machine-derived green. Anything
# else means the DONE claim is false, and a false claim is set aside rather than obeyed.
verify_done_claim() {
    log "HARDENING_DONE present — verifying the claim before honouring it."
    "$PY" "$SUPERVISOR" --reap >>"$LOG" 2>&1
    local v=$?
    if (( v == NOTHING_TO_DO )); then
        log "  supervisor agrees: no findings in any band. The run is genuinely done."
        return 0
    fi
    # IN_FLIGHT is not a disagreement -- it means something was still running and the
    # queue could not be measured yet. Discarding a valid DONE file over a transient
    # race would be its own silent defect, so only a verdict that actually asserts
    # outstanding work retires the claim.
    if (( v == IN_FLIGHT )); then
        log "  supervisor busy (IN_FLIGHT); the claim is unverified, not refuted. Retrying next loop."
        return 1
    fi
    log "=========================================================="
    log "DONE CLAIM REJECTED — the supervisor does not agree the tree is green."
    log "  supervisor verdict: $v (wanted $NOTHING_TO_DO = NOTHING_TO_DO)"
    log "  A green audit that the queue contradicts is not a green audit. Moving the"
    log "  file aside so it is not re-litigated every tick, and continuing to work."
    log "=========================================================="
    mv "$DONE_FILE" "${DONE_FILE}.rejected.$(date +%Y%m%d_%H%M%S)" 2>/dev/null
    return 1
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
        local agy_cmd=(agy -p "$TICK_PROMPT" --output-format json --dangerously-skip-permissions --print-timeout "${TICK_CAP_SEC}s")
        if [[ -n "$MODEL" ]]; then
            agy_cmd+=(--model "$MODEL")
        fi
        if [[ -n "$EFFORT" ]]; then
            agy_cmd+=(--effort "$EFFORT")
        fi
        run_capped "$TICK_CAP_SEC" "$out" "${agy_cmd[@]}"
    elif command -v claude >/dev/null 2>&1; then
        local claude_cmd=(claude -p "$TICK_PROMPT" --output-format json --permission-mode bypassPermissions)
        if [[ -n "$MODEL" ]]; then
            claude_cmd+=(--model "$MODEL")
        fi
        run_capped "$TICK_CAP_SEC" "$out" "${claude_cmd[@]}"
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
consec_limit=0; noop_ticks=0
while true; do
    if [[ -f "$DONE_FILE" ]] && verify_done_claim; then
        log "=========================================================="
        log "HARDENING_DONE verified against the supervisor. Ending the run after $ticks tick(s)."
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
        "$STALLED")
            # The supervisor read committed history and found the loop producing commits
            # without producing work. Sleeping would just extend the spin; another tick
            # would add another ledger entry. End the run and say what to look at.
            log "=========================================================="
            log "SUPERVISOR VERDICT: STALLED — the loop is committing but not working."
            log "  This is the 2026-08-24 failure shape: findings outstanding, yet the"
            log "  last $(grep -oE 'STALL_COMMITS = [0-9]+' "$SUPERVISOR" | grep -oE '[0-9]+$') commits changed nothing but the ledger."
            log "  Check, in order:"
            log "   1. is a campaign pinning work to a band already at zero?"
            log "   2. does the priority order place an empty band above a non-empty one?"
            log "   3. is the tick protocol deferring the only band that has findings?"
            log "  Detail: PYTHONPATH=. .venv/bin/python3 scripts/hardening_supervisor.py --reap"
            log "=========================================================="
            exit 0 ;;
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

    # Rotate the ledger between ticks, never during one -- the active file is what the
    # agent appends to, and a 2 MB append-only file rewritten as a fresh git blob every
    # tick is what put 552 MB of ledger objects into this repo's history.
    "$PY" "$REPO/scripts/rotate_ledger.py" >>"$LOG" 2>&1

    head_before="$(git rev-parse HEAD 2>/dev/null)"
    run_tick "$out"; rc=$?
    if (( rc == 124 )); then result=TIMEOUT; else result="$(classify "$out")"; fi
    head_after="$(git rev-parse HEAD 2>/dev/null)"
    log "--- tick $ticks finished: $result (exit $rc)"

    # --- anti-spin -------------------------------------------------------------
    # A tick that only wrote a ledger entry did no work. One or two of those is a
    # measurement tick; a dozen in a row means the loop cannot reach its queue -- the
    # 2026-08-24 failure, where a campaign pinned work to a band that had emptied while
    # the supervisor still said RESUME, and the only legal act left was to re-measure.
    if [[ "$result" == "SUCCESS" ]]; then
        if tick_was_productive "$head_before" "$head_after"; then
            noop_ticks=0
        else
            noop_ticks=$(( noop_ticks + 1 ))
            log "tick $ticks moved nothing but bookkeeping (no-op streak: $noop_ticks/$NOOP_TICK_LIMIT)"
            if (( noop_ticks >= NOOP_TICK_LIMIT )); then
                log "=========================================================="
                log "SPIN DETECTED — $noop_ticks consecutive ticks changed nothing but the"
                log "ledger. The loop is not able to act on its queue. Ending the run so a"
                log "human can look, rather than burning quota re-measuring."
                log "  Check, in order:"
                log "   1. is a campaign pinning work to a band that is already at zero?"
                log "   2. does the supervisor's queue name a band the tick protocol defers?"
                log "   3. PYTHONPATH=. .venv/bin/python3 scripts/hardening_supervisor.py --reap"
                log "=========================================================="
                exit 0
            fi
        fi
    fi

    if (( MAX_TICKS > 0 && ticks >= MAX_TICKS )); then
        log "MAX_TICKS=$MAX_TICKS reached — exiting cleanly."
        exit 0
    fi

    case "$result" in
        SUCCESS|TIMEOUT)
            consec_err=0; consec_limit=0; err_sleep="$ERR_SLEEP_MIN" ;;
        LIMIT)
            consec_err=0; err_sleep="$ERR_SLEEP_MIN"
            consec_limit=$(( consec_limit + 1 ))
            reset_s="$(limit_reset_seconds "$out")"
            if [[ -n "$reset_s" ]] && (( reset_s > MAX_LIMIT_WAIT_SEC )); then
                log "=========================================================="
                log "QUOTA EXHAUSTED — the window reopens in $(( reset_s / 3600 ))h$(( (reset_s % 3600) / 60 ))m,"
                log "past the ${MAX_LIMIT_WAIT_SEC}s this runner will wait. Ending the run cleanly after"
                log "$ticks tick(s). Nothing is broken; the quota simply is not coming back today."
                log "  Window reopens at: $(date -r $(( $(date +%s) + reset_s )) '+%Y-%m-%d %H:%M:%S') — relaunch after that."
                log "  Raise the bound with HARDENING_MAX_LIMIT_WAIT_SEC if you want it to sleep through."
                log "=========================================================="
                exit 0
            fi
            if (( consec_limit >= MAX_CONSEC_LIMIT )); then
                log "=========================================================="
                log "QUOTA STILL CLOSED after $consec_limit consecutive limited ticks and no stated"
                log "reset. Ending the run rather than probing indefinitely."
                log "=========================================================="
                exit 0
            fi
            if [[ -n "$reset_s" ]]; then
                log "USAGE LIMIT: window reopens in ${reset_s}s — sleeping until then"
                sleep $(( reset_s + 60 ))
            else
                log "RATE / USAGE LIMIT (probe $consec_limit/$MAX_CONSEC_LIMIT): sleeping ${PROBE_SLEEP_SEC}s"
                sleep "$PROBE_SLEEP_SEC"
            fi ;;
        ERROR)
            consec_err=$(( consec_err + 1 ))
            log "tick error (consecutive: $consec_err). Backing off ${err_sleep}s"
            sleep "$err_sleep"
            err_sleep=$(( err_sleep * 2 )); (( err_sleep > ERR_SLEEP_MAX )) && err_sleep=$ERR_SLEEP_MAX ;;
    esac
done
