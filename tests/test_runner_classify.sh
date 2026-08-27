#!/bin/bash
# Both runners must classify a usage limit as a limit, on either CLI's schema.
#
# Why this file exists
# --------------------
# On 2026-08-26 the gemini runner met "Individual quota reached ... Resets in 137h47m17s"
# and classified it as a generic ERROR. Its whole limit branch was dead code: `classify()`
# read `.api_error_status`, `.is_error`, `.subtype` and `.result` -- Claude-CLI's schema --
# while `agy` emits `.status` and `.error`. Every one of those four fields was absent, so
# the payload fell through to the ERROR path and the runner retried a 137-hour quota on a
# 30-minute backoff, forever. Nothing failed loudly; it just span.
#
# The claude runner has the mirror-image blind spot: `backoff_until_window_reopens`
# rejects any stated reset beyond 6 hours as "a misparse, not a limit" and falls back to
# probing every 45 minutes with no ceiling. Correct for a 5-hour rolling window, wrong for
# a weekly quota -- 183 probes across 5.7 days.
#
# These cases pin both behaviours. Run: bash tests/test_runner_classify.sh
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/.."

PASS=0; FAIL=0
check() { # label expected actual
    if [[ "$2" == "$3" ]]; then
        printf '  ok    %-46s -> %s\n' "$1" "$3"; PASS=$((PASS+1))
    else
        printf '  FAIL  %-46s -> got %s, want %s\n' "$1" "${3:-<empty>}" "$2"; FAIL=$((FAIL+1))
    fi
}

# Pull the classifier out of a runner without executing its main loop.
load_runner_fns() { # script end-marker
    local tmp; tmp="$(mktemp)"
    sed -n "/^classify() {/,/^$2/p" "$1" | sed '$d' > "$tmp"
    # shellcheck disable=SC1090
    . "$tmp"
    rm -f "$tmp"
}

T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

# Fixtures: both CLIs' shapes, plus the real payload that caused the 2026-08-26 spin.
REAL_QUOTA="local_only/scratch/runner/gemini_tick_0826_132321.json"
cat > "$T/agy_quota.json" <<'J'
{"status":"ERROR","response":"","error":"Individual quota reached. Please upgrade your subscription to increase your limits. Resets in 137h47m17s."}
J
cat > "$T/agy_ok.json"        <<'J'
{"status":"SUCCESS","response":"I have started the preflight check.","error":null}
J
cat > "$T/agy_err.json"       <<'J'
{"status":"ERROR","error":"tool call failed: ENOENT"}
J
cat > "$T/agy_exhausted.json" <<'J'
{"status":"ERROR","error":"RESOURCE_EXHAUSTED: quota exceeded for this project"}
J
cat > "$T/cl_429.json"        <<'J'
{"is_error":true,"subtype":"error","api_error_status":"429","result":"rate limited"}
J
FUTURE_EPOCH=$(( $(date +%s) + 10800 ))   # 3h out; hardcoding one lets it expire
cat > "$T/cl_limit.json" <<J
{"is_error":true,"subtype":"error","result":"Claude AI usage limit reached|${FUTURE_EPOCH}"}
J
cat > "$T/cl_ok.json"         <<'J'
{"is_error":false,"subtype":"success","result":"tick done; noted the usage limit policy in section 13"}
J
cat > "$T/cl_err.json"        <<'J'
{"is_error":true,"subtype":"error","result":"validator raised"}
J
printf 'panic: resource_exhausted\n' > "$T/crash_quota.txt"
printf 'segmentation fault\n'        > "$T/crash_plain.txt"

echo "=============================================================="
echo "gemini runner (scripts/gemini_hardening_runner.sh)"
echo "=============================================================="
(
    load_runner_fns scripts/gemini_hardening_runner.sh "tick_was_productive() {"

    # The regression itself, against the byte-for-byte payload that caused it.
    if [[ -f "$REAL_QUOTA" ]]; then
        check "REAL 2026-08-26 quota payload" LIMIT "$(classify "$REAL_QUOTA")"
    fi
    check "agy: quota reached"                LIMIT   "$(classify "$T/agy_quota.json")"
    check "agy: RESOURCE_EXHAUSTED"           LIMIT   "$(classify "$T/agy_exhausted.json")"
    check "agy: success"                      SUCCESS "$(classify "$T/agy_ok.json")"
    check "agy: generic failure"              ERROR   "$(classify "$T/agy_err.json")"
    check "claude: api_error_status 429"      LIMIT   "$(classify "$T/cl_429.json")"
    check "claude: usage limit phrase"        LIMIT   "$(classify "$T/cl_limit.json")"
    check "claude: generic failure"           ERROR   "$(classify "$T/cl_err.json")"
    # The 2026-08-23 regression in the other direction: a tick that SUCCEEDED while
    # writing about limits must not buy itself a 45-minute sleep.
    check "success whose report mentions limit" SUCCESS "$(classify "$T/cl_ok.json")"
    check "non-json crash carrying the phrase" LIMIT   "$(classify "$T/crash_quota.txt")"
    check "non-json crash without it"          ERROR   "$(classify "$T/crash_plain.txt")"

    # The reset instant drives the ceiling, so it must parse from both dialects.
    r="$(limit_reset_seconds "$T/agy_quota.json")"
    check "agy reset 137h47m17s -> seconds"   496037  "$r"
    r="$(limit_reset_seconds "$T/cl_limit.json")"
    if [[ -n "$r" ]] && (( r > 10500 && r <= 10800 )); then
        check "claude epoch reset -> ~3h" "in-range" "in-range"
    else
        check "claude epoch reset -> ~3h" "in-range" "${r:-empty}"
    fi
    r="$(limit_reset_seconds "$T/agy_err.json")"
    check "no reset stated -> empty"          ""      "$r"

    exit $FAIL
)
GEM=$?

echo
echo "=============================================================="
echo "claude runner (scripts/hardening_runner.sh)"
echo "=============================================================="
(
    PASS=0; FAIL=0
    load_runner_fns scripts/hardening_runner.sh "tick_was_productive() {"

    check "claude: api_error_status 429"      LIMIT   "$(classify "$T/cl_429.json")"
    check "claude: usage limit phrase"        LIMIT   "$(classify "$T/cl_limit.json")"
    check "claude: success"                   SUCCESS "$(classify "$T/cl_ok.json")"
    check "claude: generic failure"           ERROR   "$(classify "$T/cl_err.json")"
    check "non-json crash carrying the phrase" LIMIT  "$(classify "$T/crash_quota.txt")"
    check "non-json crash without it"          ERROR  "$(classify "$T/crash_plain.txt")"
    # This runner may also be pointed at agy; it must not go blind if it is.
    check "agy: quota reached"                LIMIT   "$(classify "$T/agy_quota.json")"
    check "agy: success"                      SUCCESS "$(classify "$T/agy_ok.json")"

    r="$(limit_reset_seconds "$T/agy_quota.json")"
    check "agy reset 137h47m17s -> seconds"   496037  "$r"
    r="$(limit_reset_seconds "$T/cl_limit.json")"
    if [[ -n "$r" ]] && (( r > 10500 && r <= 10800 )); then
        check "claude epoch reset -> ~3h" "in-range" "in-range"
    else
        check "claude epoch reset -> ~3h" "in-range" "${r:-empty}"
    fi

    exit $FAIL
)
CL=$?

echo
echo "=============================================================="
echo "quota ceiling — the real payload must exceed each runner's wait bound"
echo "=============================================================="
(
    PASS=0; FAIL=0
    # 137h47m17s. Left to `backoff_until_window_reopens` / the 45-min probe loop this is
    # ~183 pointless calls across 5.7 days, which is what the 2026-08-26 run was doing
    # when it was stopped by hand.
    REAL_RESET=496037
    for f in scripts/gemini_hardening_runner.sh scripts/hardening_runner.sh; do
        bound="$(grep -oE 'MAX_LIMIT_WAIT_SEC:-[0-9]+' "$f" | head -1 | grep -oE '[0-9]+$')"
        if [[ -n "$bound" ]] && (( REAL_RESET > bound )); then
            check "$(basename "$f"): ends instead of probing" "ceiling-fires" "ceiling-fires"
        else
            check "$(basename "$f"): ends instead of probing" "ceiling-fires" "bound=${bound:-unset}"
        fi
        cap="$(grep -oE 'MAX_CONSEC_LIMIT:-[0-9]+' "$f" | head -1 | grep -oE '[0-9]+$')"
        if [[ -n "$cap" ]] && (( cap > 0 )); then
            check "$(basename "$f"): unstated-reset probe cap" "capped" "capped"
        else
            check "$(basename "$f"): unstated-reset probe cap" "capped" "${cap:-unset}"
        fi
    done
    exit $FAIL
)
CEIL=$?

echo
echo "=============================================================="
echo "anti-spin — a ledger-only tick must not count as work"
echo "=============================================================="
(
    PASS=0; FAIL=0
    # Against REAL history. The 2026-08-24 run committed 463 ledger-only commits out of
    # 478; `tick_was_productive` is what lets the runner tell those from real units.
    for f in scripts/gemini_hardening_runner.sh scripts/hardening_runner.sh; do
        name="$(basename "$f")"
        tmp="$(mktemp)"
        sed -n "/^tick_was_productive() {/,/^}/p" "$f" > "$tmp"
        # shellcheck disable=SC1090
        . "$tmp"; rm -f "$tmp"

        v() { if tick_was_productive "$1" "$2"; then echo PRODUCTIVE; else echo no-op; fi; }
        check "$name: ledger-only commit pair"   "no-op"      "$(v b610cce3 7795427a)"
        check "$name: HEAD did not move"         "no-op"      "$(v 7795427a 7795427a)"
        check "$name: one-line generator fix"    "PRODUCTIVE" "$(v 'c7781c25^' c7781c25)"
        check "$name: harness commit"            "PRODUCTIVE" "$(v 'ca962df8^' ca962df8)"

        lim="$(grep -oE 'NOOP_TICK_LIMIT:-[0-9]+' "$f" | head -1 | grep -oE '[0-9]+$')"
        if [[ -n "$lim" ]] && (( lim > 0 && lim < 455 )); then
            check "$name: spin limit below the 455 it must catch" "bounded" "bounded"
        else
            check "$name: spin limit below the 455 it must catch" "bounded" "${lim:-unset}"
        fi

        # The DONE claim must be verified, not trusted. Grep is the right assertion here:
        # running it needs a live supervisor, and what regressed historically was the
        # bare `[[ -f "$DONE_FILE" ]]` with nothing behind it.
        if grep -q 'if \[\[ -f "\$DONE_FILE" \]\] && verify_done_claim; then' "$f"; then
            check "$name: DONE claim is verified, not trusted" "verified" "verified"
        else
            check "$name: DONE claim is verified, not trusted" "verified" "bare-existence-check"
        fi
    done
    exit $FAIL
)
SPIN=$?

echo
echo "=============================================================="
if (( GEM == 0 && CL == 0 && CEIL == 0 && SPIN == 0 )); then
    echo "RUNNER GUARDS: all cases pass on both runners."
    exit 0
fi
echo "RUNNER GUARD FAILURES: gemini=$GEM claude=$CL ceiling=$CEIL anti-spin=$SPIN"
exit 1
