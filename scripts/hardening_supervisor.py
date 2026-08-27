#!/usr/bin/env python3
"""
Hardening supervisor — the CHEAP check that decides whether a tick is needed.

Why this exists
---------------
The loop conflated two jobs with wildly different costs: a *tick* is 45-60 minutes of
real work, and *deciding whether a tick is needed* should be seconds. Putting the
expensive one on a timer meant every heartbeat re-derived the whole world, and the
timer's real job — noticing that work had stalled — was never done at all. On
2026-08-19 a deadlocked `pytest` blocked the idle REPL, four scheduled ticks never
fired, and nothing reported it. A monitor that cannot report stalled is a monitor
that reports green.

So this script answers one question, deterministically and in seconds:

    should an agent start (or resume) a hardening tick right now?

It does NOT do pipeline work, does NOT run `run_all`, and does NOT decide what the
work is. It reports state and exits with a verdict code.

What it deliberately does NOT use as a liveness signal
------------------------------------------------------
**Git commit mtime.** The retired daemon measured liveness that way, and the
postmortem names the consequence: *"rewards committing over verifying."* An agent
that commits garbage every hour looks maximally alive. Liveness here is instead:

  * is a harness/agent process actually running, and is it burning CPU;
  * is the working tree dirty (a unit was interrupted mid-flight);
  * how long since the ledger last gained an entry.

Trust boundary
--------------
Everything this script prints is a *claim*, not evidence. It exists to decide
whether to act. It is never a substitute for §0, which re-derives state from disk
before any work is done. A status file trusted as evidence is precisely how the
ledger started lying.

Exit codes
----------
  0   IN_FLIGHT      a healthy tick is running; do nothing
  10  RESUME         stalled, interrupted, idle with work outstanding, the capability
                     contract is unevaluatable, or the §1 matrix evidence is not
                     current -> run a tick
  20  NOTHING_TO_DO  no work outstanding
  30  STALLED        committing but not working -- the loop cannot reach its own queue in ANY band
  40  HUNG_UNREAPED  hung processes found and left alone; re-run with --reap

What "work outstanding" counts (widened 2026-08-26)
--------------------------------------------------
The verdict used to come from `validate_capability` alone -- stage 8 of run_all's eight.
Stages 6 (the §1 behavioural matrix) and 7 (§5 judgment reviews) were not in it. So this
script could return NOTHING_TO_DO with 575 stale reviews open and a live §1C
`empty_execution_matrix` on mat_g3_na_q3_1 -- a node that renders no problems at all and
would still report PASS. During the 2026-08-24 run it reported a 158-item queue for 455
consecutive ticks while the real figure was 735.

It now sums all three bands. Stage 6 costs ~30 minutes over 151 nodes, so it is read from
`validation_reports/matrix_report.json` rather than re-executed -- and `matrix_evidence()`
refuses that report unless it covers every node and post-dates every file under
`backend/app/practice_gen/` and `data/skeletons/`. Anything else is reported as unmeasured
and forces a RESUME, because a band that cannot be measured is never a band that is clean.

The cost is honest: this check is ~27 seconds, not ~1. It was already ~11 (evaluating the
capability contract is not free). It runs once per tick, and a tick is 45-90 minutes.
`scripts/measure_queue.py` prints the per-band detail from this same measurement so the
tick protocol does not compute a second, divergent one.

Why code 30 is STALLED and not NEEDS_HUMAN (2026-08-26)
-------------------------------------------------------
Code 30 was retired on 2026-08-23 for good reasons, recorded below, and is deliberately
NOT restored in its old form. The distinction is who asserts it.

The old NEEDS_HUMAN was *agent-declared*: a tick decided its situation was the
maintainer's call and stopped. That legitimised deferral, which is why it went.

STALLED is *derived from committed history* and cannot be asserted, suppressed, or
argued with by a tick: it fires when the last STALL_COMMITS commits changed nothing but
the ledger, the status file and the graph cache, WHILE the queue is non-empty. That
conjunction has exactly one meaning — the loop is producing commits but not work.

It exists because its absence cost a 40-hour run. On 2026-08-24 a campaign drove §6F
UNATTESTED to zero at tick 33; the campaign then pinned work to an empty band while this
supervisor, counting a global queue, kept answering RESUME. The tick could not work a
deferred band, could not stop (the stop rule was keyed on the global count, which was
158), and could not escalate (Rule 10). The only legal act left was to re-measure and
write a ledger entry, which it did 455 times across 30 hours and 112M tokens. Nothing in
the system was able to say "I am producing output but not progress". This says it.

STALLED is not a kill switch for transient trouble: a broken import is still a Class C
repair, and a contested competency is still settled by the Rule 10 ladder. It fires only
on sustained, evidenced non-progress.

Why there is no NEEDS_HUMAN (retired 2026-08-23)
------------------------------------------------
There was a code 30, "inconsistent state a tick should not paper over", and its only
trigger was an unevaluatable capability contract. On an unattended multi-day run that
code was a kill switch: it ended the whole run over a broken import, and it legitimised
the same shape of deferral one layer up ("this node is the maintainer's call"). Both are
now handled by deciding instead of stopping. A contract that cannot be evaluated is a
Class C repair and the tick's only unit; a contested reading of a competency is settled
against MATATAG by the protocol's Rule 10 ladder and recorded as reversible.

This does not leave the run unstoppable, but note what actually stops it: NOT a circuit
breaker. An earlier draft of this docstring claimed three consecutive failed ticks opened
one; the runner has never had one and must not -- a loop that gives up on transient
trouble reports green by being absent. What exists is an exponential backoff (60s,
doubling, capped at 30 min) so a genuinely broken state idles instead of spinning, the
maintainer's HARDENING_STOP file, and HARDENING_DONE. A documented guard that does not
exist is the exact hazard the tick protocol's Rule 11 names, so this paragraph is the
correction rather than a deletion. Code 40 stays separate because a hung process is
routine and self-remediable: the caller re-runs with --reap and continues.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "local_only/scratch/hardening_ledger.md"
ATTEST = REPO / "validation_reports/attestation"
JUDGMENT = REPO / "validation_reports/judgment"
STATUS = REPO / "local_only/scratch/hardening_status.json"

IN_FLIGHT, RESUME, NOTHING_TO_DO, STALLED, HUNG_UNREAPED = 0, 10, 20, 30, 40

# How many consecutive bookkeeping-only commits mean the loop cannot act on its
# queue. Matches HARDENING_NOOP_TICK_LIMIT in both runners; the runner counts ticks
# in-process, this counts committed history, so it survives a restart.
STALL_COMMITS = 12

# A process burning less than this fraction of a core, for longer than the grace
# period, is hung rather than slow. A healthy run_all worker sits near 50%.
HUNG_CPU_RATIO = 0.02
HUNG_GRACE_SECONDS = 600

WATCHED = re.compile(r"practice_gen\.validation\.run_all|pytest|mutation_harness")
# The shell wrapper that launches a background job carries the whole command in its
# own args, so it matches WATCHED — and a wrapper legitimately burns ~0 CPU while its
# child does the work. Counting it made every healthy background run look hung once it
# passed the grace window. Only an actual interpreter is a candidate.
_INTERPRETER = re.compile(r"(^|/)(python[0-9.]*|Python)$")

# Orphaned multiprocessing workers — the actual cause of the 2026-08-20 "deadlock".
#
# `multiprocessing` spawn workers carry `spawn_main` in their args and NOTHING that
# identifies the job they belong to, so a pattern matching run_all/pytest never sees
# them. When a parent is killed (or dies), its workers are reparented to init and keep
# computing forever — and each one pegs a core.
#
# Measured on this 4-core host: 14 orphans alive at once, 59.7 core-hours burned, the
# oldest running 23 hours. Everything launched alongside them was starved to a few
# percent of a core, which looks exactly like a deadlock: run_all sat at 4.3s CPU over
# 73 minutes, pytest at 22s over 4h20m. Both were diagnosed as hangs. Neither was one.
#
# Worse, killing the parent by name made it worse each time, because the workers do not
# match the parent's pattern and survived every cleanup.
#
# An orphan is hung by definition — its parent is gone, so no result it computes can be
# collected. No grace period applies.
_SPAWN_WORKER = re.compile(r"multiprocessing\.spawn|spawn_main")


def _sh(*args: str) -> str:
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True).stdout.strip()


def _etime_to_seconds(etime: str) -> int:
    """ps elapsed time: [[dd-]hh:]mm:ss"""
    days = 0
    if "-" in etime:
        d, etime = etime.split("-", 1)
        days = int(d)
    parts = [int(p) for p in etime.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    return days * 86400 + parts[0] * 3600 + parts[1] * 60 + parts[2]


def _cputime_to_seconds(t: str) -> float:
    parts = t.replace("-", ":").split(":")
    parts = [float(p) for p in parts]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def scan_processes() -> tuple[list[dict], list[dict]]:
    """
    Return (healthy, hung) watched processes, judged by the CPU their whole process
    TREE is burning, not their own.

    A pool parent legitimately idles while its workers compute: measured on a live,
    healthy run_all, the parent sat at ratio 0.0069 while its three workers burned
    3:40, 3:40 and 9:46 of CPU over 9:51 of wall clock. Judging the parent alone would
    have declared that run hung five seconds later and --reap would have killed it.

    So the signal is the sum over the process and its descendants. A genuinely stalled
    tree burns nothing anywhere; a working one burns a core per worker.
    """
    out = _sh("ps", "-eo", "pid=,ppid=,etime=,time=,args=")

    # pid -> own cpu seconds, and pid -> children, for the whole table.
    own_cpu: Dict[int, float] = {}
    children: Dict[int, list] = {}
    for line in out.splitlines():
        f = line.split(None, 4)
        if len(f) < 5:
            continue
        try:
            pid_i, ppid_i, cpu_i = int(f[0]), int(f[1]), _cputime_to_seconds(f[3])
        except ValueError:
            continue
        own_cpu[pid_i] = cpu_i
        children.setdefault(ppid_i, []).append(pid_i)

    def tree_cpu(root: int) -> float:
        total, stack, seen = 0.0, [root], set()
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            total += own_cpu.get(n, 0.0)
            stack.extend(children.get(n, []))
        return total

    healthy, hung = [], []
    for line in out.splitlines():
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        pid, ppid, etime, cput, args = parts
        orphan_worker = _SPAWN_WORKER.search(args) and ppid == "1"
        if "hardening_supervisor" in args:
            continue
        if not (WATCHED.search(args) or orphan_worker):
            continue
        exe = args.split(None, 1)[0]
        if not _INTERPRETER.search(exe):
            continue  # shell wrapper, not the job itself
        try:
            elapsed = _etime_to_seconds(etime)
            cpu = _cputime_to_seconds(cput)
        except ValueError:
            continue
        tcpu = tree_cpu(int(pid))
        rec = {
            "pid": int(pid), "ppid": int(ppid), "elapsed_s": elapsed,
            "cpu_s": round(cpu, 1), "tree_cpu_s": round(tcpu, 1),
            "ratio": round(tcpu / elapsed, 4) if elapsed else 0.0,
            "own_ratio": round(cpu / elapsed, 4) if elapsed else 0.0,
            "orphan_worker": bool(orphan_worker),
            "cmd": args[:120],
        }
        # An orphan is hung whatever its CPU: it is burning a core to produce a result
        # nobody will ever collect. A low CPU ratio is the *other* signature.
        if orphan_worker or (elapsed > HUNG_GRACE_SECONDS and rec["ratio"] < HUNG_CPU_RATIO):
            hung.append(rec)
        else:
            healthy.append(rec)
    return healthy, hung


def reap(hung: list[dict]) -> list[int]:
    killed = []
    for p in hung:
        subprocess.run(["kill", "-9", str(p["pid"])], capture_output=True)
        killed.append(p["pid"])
    return killed


def ledger_state() -> dict:
    if not LEDGER.exists():
        return {"exists": False, "age_hours": None, "next_tick_should": None, "last_heading": None}
    text = LEDGER.read_text(encoding="utf-8", errors="replace")
    headings = re.findall(r"^## (.+)$", text, re.MULTILINE)
    tail = text[text.rfind("\n## "):] if "\n## " in text else text
    m = re.search(r"\*\*Next tick should:\*\*(.+?)(?=\n- \*\*|\n## |\Z)", tail, re.DOTALL)
    return {
        "exists": True,
        "age_hours": round((time.time() - LEDGER.stat().st_mtime) / 3600, 1),
        "last_heading": headings[-1] if headings else None,
        # 400 chars truncated the handoff to its first item, and §1 tells the tick this print
        # IS its starting point. A handoff that arrives cut in half is a handoff that lies.
        "next_tick_should": " ".join(m.group(1).split())[:4000] if m else None,
    }


# Every stage of run_all that can hold an open finding. The gate below counts ALL of
# them, and the reason it must is a 2026-08-26 postmortem: this function used to call
# validate_capability alone, so the verdict that decides "is there work?" was blind to
# stage 6 (the §1 behavioural matrix) and stage 7 (§5 judgment reviews). A live §1C
# `empty_execution_matrix` on mat_g3_na_q3_1 -- a node that renders no problems at all
# and would still report PASS -- sat unqueued through 455 consecutive ticks because the
# number those ticks optimised did not contain it. A queue that omits a band cannot
# report that band as outstanding, and a gate that cannot see a finding does not gate.
_QUEUE_PROBE = r"""
import json, re, collections
out = {}
NODE = re.compile(r'mat_g\d_\w+?_q\d_\d+')

def nodes(es):
    return {m.group(0) for e in es for m in [NODE.search(e)] if m}

from backend.app.practice_gen.validation import validate_capability as VC
from backend.app.practice_gen.validation import validate_judgment as VJ

c = VC.validate_capability_declarations()
j = VJ.validate_judgment_reviews()

d6d = [e for e in c if '6D' in e]
d6f = [e for e in c if '6F' in e]
stale_rev = [e for e in j if "must be 'PASS'" not in e]
verdict    = [e for e in j if "must be 'PASS'" in e]
un  = [e for e in d6f if 'unattested' in e.lower()]
con = [e for e in d6f if 'contradict' in e.lower()]
sta = [e for e in d6f if 'stale'      in e.lower()]

out["capability"] = len(c)
out["judgment"] = len(j)
# Per-band detail so the tick protocol reads one measurement instead of recomputing a
# second, divergent one. Two implementations of "the queue" is how the loop reported
# 158 while 735 findings stood.
out["bands"] = {
    "5_stale_reviews":     {"n": len(stale_rev), "nodes": len(nodes(stale_rev))},
    "5_non_pass":          {"n": len(verdict),   "nodes": len(nodes(verdict))},
    "6F_contradicted":     {"n": len(con),       "nodes": len(nodes(con))},
    "6F_stale_attest":     {"n": len(sta),       "nodes": len(nodes(sta))},
    "6F_unattested":       {"n": len(un),        "nodes": len(nodes(un))},
    "6D_wildcards":        {"n": len(d6d),       "nodes": len(nodes(d6d)),
                            "worst": collections.Counter(
                                m.group(0) for e in d6d for m in [NODE.search(e)] if m
                            ).most_common(5)},
}
out["verdict_tally"] = str(VJ.summarize_verdicts())

print("__QUEUE__" + json.dumps(out))
"""

MATRIX_REPORT = REPO / "validation_reports/matrix_report.json"


def matrix_evidence() -> dict:
    """
    What stage 6 currently proves, and whether that proof is still good.

    Stage 6 costs ~30 minutes over 151 nodes, so it is read from the report it leaves
    behind rather than re-executed. That trade is only safe if the report's *coverage*
    and *freshness* travel with the count -- an unreadable, partial or stale report has
    to read as "unmeasured", never as zero.

    Known limitation, stated so the next agent keeps looking: `validate_matrix --node X`
    overwrites the tree-wide report with that one node rather than merging into it. This
    function detects the resulting partial report and refuses it, but it cannot repair
    it -- only a full matrix run restores tree-wide §1 evidence.
    """
    sys.path.insert(0, str(REPO))
    from backend.app.practice_gen.registry import get_all_node_ids

    all_nodes = set(get_all_node_ids())
    m = {"state": "MISSING", "findings": 0, "covered": 0, "total": len(all_nodes)}
    if not MATRIX_REPORT.exists():
        m["trusted"] = False
        return m
    try:
        rep = json.loads(MATRIX_REPORT.read_text(encoding="utf-8"))
        if not isinstance(rep, dict):
            raise ValueError("matrix report is not an object")
    except (ValueError, OSError):
        m["state"] = "UNREADABLE"
        m["trusted"] = False
        return m

    rows = {k: v for k, v in rep.items() if k != "_executed_checks" and isinstance(v, list)}
    m["findings"] = sum(len(v) for v in rows.values())
    m["covered"] = len(set(rows) & all_nodes)
    m["mtime"] = MATRIX_REPORT.stat().st_mtime
    if m["covered"] < len(all_nodes):
        m["state"] = "PARTIAL"
    elif m["mtime"] < _newest_pipeline_mtime():
        m["state"] = "STALE"
    else:
        m["state"] = "FRESH"
    # Only a complete, current report may contribute a trustworthy zero.
    m["trusted"] = m["state"] == "FRESH"
    return m


def _newest_pipeline_mtime() -> float:
    """
    Newest mtime under the trees that determine what stage 6 would report.

    Deliberately mtime and not git: a working-tree edit that has not been committed
    still invalidates a matrix report, and the whole point of the freshness signal is
    to refuse to answer from evidence about content that has since changed.

    `validation/` is deliberately INCLUDED, though it is the harness rather than the
    content. A matrix report is a claim about what the current validators find in the
    current generators; editing `validate_matrix.py` -- adding a check, tightening a
    bound -- changes the first half of that just as surely as editing a DNA changes the
    second. Excluding it would have meant a Class C harness repair left the old §1
    evidence looking FRESH, which is the same cached-zero hole this function exists to
    close. The cost is a matrix re-run after harness edits, which is exactly when one
    is wanted.
    """
    newest = 0.0
    for root in ("backend/app/practice_gen", "data/skeletons"):
        base = REPO / root
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if not f.is_file():
                continue
            if "__pycache__" in f.parts or f.suffix == ".pyc":
                continue
            try:
                newest = max(newest, f.stat().st_mtime)
            except OSError:
                continue
    return newest



def bookkeeping_only_streak() -> int:
    """
    How many of the most recent commits changed nothing but the loop's own bookkeeping.

    The ledger, the status file and the graph cache are what a tick writes ABOUT its
    work. A commit containing only those is a tick that reported and did not act. Counted
    from committed history rather than from a tick counter so it survives a runner
    restart -- the 2026-08-24 spin outlived several.
    """
    out = _sh("git", "log", "--format=%H", "-n", str(STALL_COMMITS * 2))
    streak = 0
    for sha in out.splitlines():
        if not sha.strip():
            continue
        files = _sh("git", "show", "--name-only", "--format=", sha.strip())
        names = [f for f in files.splitlines() if f.strip()]
        if not names:
            break
        if all(
            f.endswith("hardening_ledger.md")
            or f.endswith("hardening_status.json")
            or f.startswith("graphify-out/")
            or "/ledger_archive/" in f
            for f in names
        ):
            streak += 1
        else:
            break
    return streak


def queue_state() -> dict | None:
    """
    Cheap, seconds: every open finding run_all would report, by band.

    Returns None only when the probe itself could not run -- an unevaluatable contract,
    which is a Class C repair and the tick's only unit. It never returns a count that
    silently omits a band; a band it could not measure is reported as unmeasured.
    """
    p = subprocess.run(
        [sys.executable, "-c", _QUEUE_PROBE],
        cwd=REPO, capture_output=True, text=True,
        env={"PYTHONPATH": ".", "PATH": "/usr/bin:/bin"},
    )
    line = next((l for l in (p.stdout or "").splitlines() if l.startswith("__QUEUE__")), None)
    if line is None:
        return None
    try:
        q = json.loads(line[len("__QUEUE__"):])
    except ValueError:
        return None

    m = q["matrix"] = matrix_evidence()
    q["total"] = q["capability"] + q["judgment"] + (m["findings"] if m["trusted"] else 0)
    return q



def coverage() -> dict:
    """
    Progress toward the goal, which is NOT the failure count.

    A failure count can be driven to zero by weakening a check, and has been, three
    times. These three numbers cannot: an Attester never sees the provider table, a
    blind reviewer never sees the generator, and a mutation only counts when the
    harness actually caught a planted bug. Widening a provider or deleting a check
    moves none of them up.
    """
    import json as _json

    attested = set()
    if ATTEST.exists():
        for f in ATTEST.glob("*.json"):
            for v in _json.loads(f.read_text()).get("verdicts", []):
                if v.get("capability_id") and v.get("node_id"):
                    attested.add((v["node_id"], v["capability_id"]))

    try:
        sys.path.insert(0, str(REPO))
        from backend.app.practice_gen.registry import get_all_node_ids, get_node_info
        # (node, capability) pairs, not table rows: a verdict is about specific rendered
        # content, so the same capability on two nodes needs two verdicts.
        total_caps = sum(len((get_node_info(n) or {}).get("requires") or [])
                         for n in get_all_node_ids())
    except Exception:
        total_caps = None

    reviewed = len(list(JUDGMENT.rglob("*.json"))) if JUDGMENT.exists() else 0

    mutations = None
    mh = REPO / "tests/mutation_harness.py"
    if mh.exists():
        mutations = len(re.findall(r"^\s{4}Mutation\($", mh.read_text(), re.MULTILINE))

    return {
        "capabilities_attested": len(attested),
        "capabilities_total": total_caps,
        "attested_pct": round(100 * len(attested) / total_caps, 1) if total_caps else None,
        "nodes_reviewed": reviewed,
        "nodes_total": 151,
        "mutations_registered": mutations,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reap", action="store_true", help="kill hung processes (default: report only)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable status only")
    args = ap.parse_args()

    healthy, hung = scan_processes()
    killed = reap(hung) if (args.reap and hung) else []

    porcelain = _sh("git", "status", "--porcelain")
    # An interrupted unit leaves *tracked* files modified. Untracked files are
    # usually new tooling that has not been committed yet, and treating them as a
    # stall signal makes the supervisor trigger on its own existence.
    modified = [l for l in porcelain.splitlines() if not l.startswith("??")]
    untracked = [l for l in porcelain.splitlines() if l.startswith("??")]
    dirty = modified
    head = _sh("git", "log", "--oneline", "-1")
    unpushed = _sh("git", "log", "--oneline", "origin/main..HEAD")
    led = ledger_state()
    q = queue_state()
    findings = None if q is None else q["total"]
    cov = coverage()

    if hung and not killed:
        verdict, why = HUNG_UNREAPED, (
            f"{len(hung)} hung process(es) found and left running; re-run with --reap. "
            f"Nothing else here is trustworthy until they are gone — a hung job blocks "
            f"the next tick from ever starting."
        )
    elif healthy:
        verdict, why = IN_FLIGHT, f"{len(healthy)} healthy process(es) running"
    elif dirty:
        verdict, why = RESUME, "working tree is dirty — a unit was interrupted mid-flight"
    elif findings is None:
        # Not a stop condition. An unevaluatable contract is a Class C repair, and it is
        # the tick's only unit -- Step 2 can measure nothing until it is fixed.
        verdict, why = RESUME, (
            "capability contract could not be evaluated -- CLASS C REPAIR is this tick's "
            "only unit; Step 2 cannot measure anything until it is fixed"
        )
    elif not q["matrix"]["trusted"]:
        # Never let an unmeasured band read as zero. A MISSING/PARTIAL/STALE/UNREADABLE
        # matrix report means stage 6 has no current evidence, and stage 6 owns the §1
        # content-correctness checks -- the band that outranks everything else here.
        m = q["matrix"]
        verdict, why = RESUME, (
            f"§1 matrix evidence is {m['state']} ({m['covered']}/{m['total']} nodes covered) "
            f"-- the queue is NOT measurable until a full matrix run refreshes it. "
            f"Run: PYTHONPATH=. .venv/bin/python3 -m backend.app.practice_gen.validation.validate_matrix. "
            f"Bands that could be measured: §1={m['findings']} (untrusted) "
            f"§5={q['judgment']} §6={q['capability']}"
        )
    elif findings > 0 and bookkeeping_only_streak() >= STALL_COMMITS:
        verdict, why = STALLED, (
            f"{bookkeeping_only_streak()} consecutive commits changed nothing but the "
            f"ledger while {findings} finding(s) stand. The loop is committing but not "
            f"working — it cannot reach its own queue. Check, in order: (1) is a campaign "
            f"pinning work to a band already at zero? (2) does the priority order place "
            f"an empty band above a non-empty one? (3) is the tick protocol deferring the "
            f"only band that has findings? Bands now: §1 matrix={q['matrix']['findings']}, "
            f"§5 judgment={q['judgment']}, §6 capability={q['capability']}."
        )
    elif findings > 0:
        verdict, why = RESUME, (
            f"{findings} finding(s) outstanding "
            f"(§1 matrix={q['matrix']['findings']}, §5 judgment={q['judgment']}, "
            f"§6 capability={q['capability']})"
        )
    else:
        verdict, why = NOTHING_TO_DO, (
            "no findings in any band (§1 matrix=0, §5 judgment=0, §6 capability=0) "
            "and nothing in flight"
        )

    status = {
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "verdict": {IN_FLIGHT: "IN_FLIGHT", RESUME: "RESUME",
                    NOTHING_TO_DO: "NOTHING_TO_DO", STALLED: "STALLED",
                    HUNG_UNREAPED: "HUNG_UNREAPED"}[verdict],
        "why": why,
        "processes": {"healthy": healthy, "hung": hung, "killed": killed},
        "git": {"head": head, "modified_tracked": len(modified), "untracked": len(untracked),
                "unpushed_commits": len(unpushed.splitlines()) if unpushed else 0},
        "ledger": led,
        "findings_total": findings,
        "findings_by_band": None if q is None else {
            "matrix_stage6": q["matrix"]["findings"],
            "judgment_stage7": q["judgment"],
            "capability_stage8": q["capability"],
        },
        "matrix_evidence": None if q is None else q["matrix"],
        "bands": None if q is None else q.get("bands"),
        "verdict_tally": None if q is None else q.get("verdict_tally"),
        # Kept under its old key so anything reading the previous schema still resolves,
        # but it is no longer the gate -- `findings_total` is.
        "capability_findings": None if q is None else q["capability"],
        "coverage": cov,
        "NOTE": "A claim, not evidence. §0 re-derives from disk before any work is done.",
    }
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(status, indent=2))
        return verdict

    print(f"VERDICT: {status['verdict']} — {why}")
    print(f"  head              : {head}")
    print(f"  tree              : {('MODIFIED (' + str(len(modified)) + ' tracked)') if modified else 'clean'}"
          f" | untracked: {len(untracked)} | unpushed: {status['git']['unpushed_commits']}")
    if q is None:
        print("  QUEUE             : UNMEASURABLE (capability contract did not evaluate)")
    else:
        m = q["matrix"]
        mark = "" if m["trusted"] else f"  <- {m['state']}, NOT counted"
        print(f"  QUEUE (all bands) : {findings}   <- the work queue, not the score")
        print(f"    §1 matrix  (6/8): {m['findings']}{mark}")
        print(f"    §5 judgment(7/8): {q['judgment']}")
        print(f"    §6 capability(8/8): {q['capability']}")
        print(f"  §1 matrix evidence: {m['state']} ({m['covered']}/{m['total']} nodes covered)")
    print(f"  COVERAGE (the goal): attested {cov['capabilities_attested']}/{cov['capabilities_total']}"
          f" ({cov['attested_pct']}%) | reviewed {cov['nodes_reviewed']}/{cov['nodes_total']}"
          f" | mutations {cov['mutations_registered']}")
    print(f"  ledger last entry : {led['last_heading']} ({led['age_hours']}h ago)")
    for p in hung:
        kind = "ORPHANED WORKER" if p.get("orphan_worker") else "HUNG"
        print(f"  {kind} pid={p['pid']} elapsed={p['elapsed_s']}s cpu={p['cpu_s']}s "
              f"ratio={p['ratio']} {'KILLED' if p['pid'] in killed else 'NOT KILLED'}")
    for p in healthy:
        print(f"  running pid={p['pid']} elapsed={p['elapsed_s']}s "
              f"tree_cpu={p['tree_cpu_s']}s ratio={p['ratio']} (own {p['own_ratio']})")
    if led["next_tick_should"]:
        print(f"\n  Next tick should: {led['next_tick_should'][:3000]}")
    print(f"\n  status written to {STATUS.relative_to(REPO)}")
    return verdict


if __name__ == "__main__":
    sys.exit(main())
