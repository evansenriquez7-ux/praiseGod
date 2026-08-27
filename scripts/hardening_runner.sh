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
# A usage limit is a pause, not an ending -- but only while the pause is shorter than
# the run. A 5-hour rolling window is worth waiting out; a weekly quota stating a reset
# ~137h away is not, and probing it every 45 minutes is ~183 pointless calls across 5.7
# days. Past this bound the runner ends cleanly and says why.
MAX_LIMIT_WAIT_SEC="${HARDENING_MAX_LIMIT_WAIT_SEC:-21600}"   # 6h
MAX_CONSEC_LIMIT="${HARDENING_MAX_CONSEC_LIMIT:-8}"           # when the reset is unstated
# Anti-spin. On 2026-08-24 a campaign's target band emptied at tick 33 while the
# supervisor still said RESUME, so 455 consecutive ticks committed nothing but a ledger
# entry about having nothing to do. No prompt wording can be trusted to notice that;
# the runner counts it mechanically and stops.
NOOP_TICK_LIMIT="${HARDENING_NOOP_TICK_LIMIT:-12}"

# Exit codes from hardening_supervisor.py
# NEEDS_HUMAN=30 is retired (2026-08-23). No verdict ends the run on a judgement call;
# see hardening_supervisor.py's docstring. A stray 30 now falls to the catch-all below.
IN_FLIGHT=0; RESUME=10; NOTHING_TO_DO=20; STALLED=30; HUNG_UNREAPED=40

mkdir -p "$RUN_DIR"

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$LOG"; }

# Run a command with a hard wall-clock cap. This host has no `timeout`/`gtimeout`,
# so the watchdog is bash-native. Returns 124 on timeout, else the command's status.
# `pkill -9 -P` reaches only DIRECT children, so a run_all the tick launched from its
# Bash tool -- a grandchild -- survived the 90-minute kill, kept three workers burning,
# and the supervisor then read it as *healthy* -> IN_FLIGHT -> 5-minute sleeps for up to
# ~50 min. `set -m` gives the job its own process group so a negative-pid kill takes the
# whole tree. stdin is /dev/null: an unattended job must never inherit a terminal.
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

# SUCCESS | LIMIT | ERROR — decided from the result JSON, never from exit code alone.
classify() {
    local f="$1"
    # Not JSON at all (a crashed binary, a truncated write): the phrase is the only
    # signal there is.
    if ! jq -e . "$f" >/dev/null 2>&1; then
        grep -qiE "usage limit|resource.?exhausted|rate limit|quota (exceeded|reached)" "$f" 2>/dev/null \
            && echo LIMIT || echo ERROR
        return
    fi
    # Two CLIs, two schemas. `claude -p --output-format json` emits {is_error, subtype,
    # result, api_error_status}; `agy --output-format json` emits {status, response,
    # error}. Reading only one set is how the gemini runner spent 2026-08-26 treating a
    # 137-hour quota exhaustion as a generic ERROR. This runner reads both so it cannot
    # go blind if it is ever pointed at the other CLI.
    local api_status is_err subtype st
    api_status="$(jq -r '.api_error_status // empty' "$f")"
    is_err="$(jq -r '.is_error // false' "$f")"
    subtype="$(jq -r '.subtype // empty' "$f")"
    st="$(jq -r '.status // empty' "$f")"

    if [[ "$api_status" == "429" || "$api_status" == "RESOURCE_EXHAUSTED" ]]; then echo LIMIT; return; fi

    # The phrase is authoritative ONLY on a run that actually failed. Grepping the whole
    # document first classified a *successful* tick as LIMIT whenever its own report
    # mentioned one -- which the tick protocol's §13 actively invites it to write -- and
    # bought a 45-minute sleep for a tick that had just succeeded. Proved 2026-08-23.
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
# claude appends a unix epoch ("...|1755950400"); agy states "Resets in 137h47m17s".
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

# The limit message carries the window's reset instant as a trailing unix epoch --
# "Claude AI usage limit reached|1755950400". Reading it turns a blind fixed-interval
# wait (which resumed up to PROBE_SLEEP_SEC late, every single time) into an on-time one.
limit_reset_epoch() {
    jq -r '.result // ""' "$1" 2>/dev/null | grep -oE '\|[0-9]{10}' | tr -d '|' | head -1
}

# A usage limit is never a reason to end the run -- it is a pause. Sleep to the stated
# reset if there is one, then probe until the window reopens, for as long as that takes.
# Returns 1 only when STOP/DONE appeared meanwhile, and the caller's next loop iteration
# exits on it.
backoff_until_window_reopens() {
    local src="${1:-}" n=0 epoch now wait_s
    if [[ -n "$src" && -f "$src" ]]; then
        epoch="$(limit_reset_epoch "$src")"
        now="$(date +%s)"
        if [[ -n "$epoch" ]] && (( epoch > now )); then
            wait_s=$(( epoch - now + 60 ))
            # A 5-hour window is 18000s. Anything past 6 hours is a misparse, not a limit;
            # say so loudly and fall back rather than sleeping through the whole run.
            if (( wait_s > 21600 )); then
                log "stated reset is ${wait_s}s away — implausible, ignoring it and probing blind"
            else
                log "USAGE LIMIT: window resets $(date -r "$epoch" '+%Y-%m-%d %H:%M:%S') — sleeping ${wait_s}s"
                sleep "$wait_s"
                [[ -f "$STOP_FILE" ]] && { log "STOP file appeared during backoff"; return 1; }
                [[ -f "$DONE_FILE" ]] && { log "DONE file appeared during backoff"; return 1; }
                if probe_window_open; then
                    log "USAGE WINDOW REOPENED at the stated reset — resuming"
                    return 0
                fi
                log "still limited past the stated reset — falling back to ${PROBE_SLEEP_SEC}s probes"
            fi
        fi
    fi
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

ticks=0; consec_err=0; err_sleep="$ERR_SLEEP_MIN"; total_cost=0
consec_limit=0; noop_ticks=0
while true; do
    if [[ -f "$DONE_FILE" ]] && verify_done_claim; then
        log "=========================================================="
        log "HARDENING_DONE verified against the supervisor. Ending after $ticks tick(s), \$$total_cost."
        log "  $(head -c 300 "$DONE_FILE" 2>/dev/null | tr '\n' ' ')"
        log "=========================================================="
        exit 0
    fi

    if [[ -f "$STOP_FILE" ]]; then
        log "STOP file present — exiting cleanly after $ticks tick(s), \$$total_cost"
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
            log "  The run does not end on this. If it repeats, the supervisor itself is the bug."
            sleep "$err_sleep"
            err_sleep=$(( err_sleep * 2 )); (( err_sleep > ERR_SLEEP_MAX )) && err_sleep=$ERR_SLEEP_MAX
            continue ;;
    esac

    ticks=$(( ticks + 1 ))
    stamp="$(date +%m%d_%H%M%S)"
    out="$RUN_DIR/tick_${stamp}.json"
    log "--- tick $ticks starting (cap ${TICK_CAP_SEC}s) -> $out"

    # Rotate the ledger between ticks, never during one -- the active file is what the
    # agent appends to, and a 2 MB append-only file rewritten as a fresh git blob every
    # tick is what put 552 MB of ledger objects into this repo's history.
    "$PY" "$REPO/scripts/rotate_ledger.py" >>"$LOG" 2>&1

    head_before="$(git rev-parse HEAD 2>/dev/null)"
    run_tick "$out"; rc=$?
    head_after="$(git rev-parse HEAD 2>/dev/null)"
    # A 124 is the tick hitting the wall clock, not a broken system: it did work and ran
    # out of room. Classifying it as ERROR punished exactly the ticks that worked longest,
    # doubling the backoff toward 30 min for doing a full Class A unit.
    if (( rc == 124 )); then result=TIMEOUT; else result="$(classify "$out")"; fi
    cost="$(jq -r '.total_cost_usd // 0' "$out" 2>/dev/null)"
    [[ "$cost" =~ ^[0-9]+(\.[0-9]+)?$ ]] || cost=0
    total_cost="$(jq -n --argjson a "$total_cost" --argjson b "$cost" '$a + $b')"
    # jq on a truncated/absent file emits nothing at all, so `// "?"` never fires --
    # which is exactly the TIMEOUT case, where no result JSON was ever written.
    turns="$(jq -r '.num_turns // "?"' "$out" 2>/dev/null)"; [[ -n "$turns" ]] || turns="?"
    sid="$(jq -r '.session_id // empty' "$out" 2>/dev/null)"
    log "--- tick $ticks finished: $result (exit $rc, turns $turns, cost \$$cost, run total \$$total_cost)"
    if [[ -n "$sid" ]]; then
        log "    session $sid — inspect with: claude --resume $sid"
    else
        log "    no session id — the tick wrote no result JSON (killed at the cap, or the binary failed)"
    fi

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
        log "MAX_TICKS=$MAX_TICKS reached (\$$total_cost) — exiting cleanly. This is a bound, not a verdict:"
        log "  the last tick's own result was $result."
        exit 0
    fi

    case "$result" in
        SUCCESS)
            consec_err=0; consec_limit=0; err_sleep="$ERR_SLEEP_MIN" ;;
        TIMEOUT)
            # Not a failure. Whatever the tick committed survives; the rest leaves a dirty
            # tree that the next tick's §1 RESUME unwinds, which is the designed path.
            consec_err=0; err_sleep="$ERR_SLEEP_MIN"
            log "tick hit the ${TICK_CAP_SEC}s cap — the next tick resumes an interrupted unit" ;;
        LIMIT)
            consec_err=0; err_sleep="$ERR_SLEEP_MIN"
            consec_limit=$(( consec_limit + 1 ))
            # A 5-hour rolling window is worth waiting out. A weekly quota is not: it
            # states a reset ~137h away, and `backoff_until_window_reopens` would probe
            # it every 45 minutes for 5.7 days without ever ending the run.
            reset_s="$(limit_reset_seconds "$out")"
            if [[ -n "$reset_s" ]] && (( reset_s > MAX_LIMIT_WAIT_SEC )); then
                log "=========================================================="
                log "QUOTA EXHAUSTED — the window reopens in $(( reset_s / 3600 ))h$(( (reset_s % 3600) / 60 ))m,"
                log "past the ${MAX_LIMIT_WAIT_SEC}s this runner will wait. Ending the run cleanly after"
                log "$ticks tick(s), \$$total_cost. Nothing is broken; the quota is not coming back today."
                log "  Raise HARDENING_MAX_LIMIT_WAIT_SEC if you want it to sleep through."
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
            # `continue` only fires if STOP/DONE appeared; the top of the loop exits on it.
            backoff_until_window_reopens "$out" || continue ;;
        ERROR)
            consec_err=$(( consec_err + 1 ))
            log "tick error (consecutive: $consec_err). The run does NOT end on errors. Head of output:"
            head -c 600 "$out" | tee -a "$LOG"; echo | tee -a "$LOG"
            log "backing off ${err_sleep}s before the next tick"
            sleep "$err_sleep"
            err_sleep=$(( err_sleep * 2 )); (( err_sleep > ERR_SLEEP_MAX )) && err_sleep=$ERR_SLEEP_MAX ;;
    esac
done
