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
  10  RESUME         stalled, interrupted, or idle with work outstanding -> run a tick
  20  NOTHING_TO_DO  no work outstanding
  30  NEEDS_HUMAN    inconsistent state a tick should not paper over
  40  HUNG_UNREAPED  hung processes found and left alone; re-run with --reap

Why 40 is separate from 30: a hung process is routine and self-remediable -- the
caller re-runs with --reap and continues. A contract that cannot be evaluated is
not. Both were originally reported as NEEDS_HUMAN, which made "you did not pass a
flag" indistinguishable by exit code from "something is genuinely wrong." A monitor
whose red means two different things is the failure this repo keeps paying for.
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

IN_FLIGHT, RESUME, NOTHING_TO_DO, NEEDS_HUMAN, HUNG_UNREAPED = 0, 10, 20, 30, 40

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
        "next_tick_should": " ".join(m.group(1).split())[:400] if m else None,
    }


def capability_findings() -> int | None:
    """Cheap, seconds: how many capability problems the contract reports right now."""
    p = subprocess.run(
        [sys.executable, "-c",
         "from backend.app.practice_gen.validation import validate_capability as V;"
         "print(len(V.validate_capability_declarations()))"],
        cwd=REPO, capture_output=True, text=True, env={"PYTHONPATH": ".", "PATH": "/usr/bin:/bin"},
    )
    try:
        return int((p.stdout or "").strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None



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
    findings = capability_findings()
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
        verdict, why = NEEDS_HUMAN, "capability contract could not be evaluated"
    elif findings > 0:
        verdict, why = RESUME, f"{findings} capability finding(s) outstanding"
    else:
        verdict, why = NOTHING_TO_DO, "no capability findings and nothing in flight"

    status = {
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "verdict": {IN_FLIGHT: "IN_FLIGHT", RESUME: "RESUME",
                    NOTHING_TO_DO: "NOTHING_TO_DO", NEEDS_HUMAN: "NEEDS_HUMAN",
                    HUNG_UNREAPED: "HUNG_UNREAPED"}[verdict],
        "why": why,
        "processes": {"healthy": healthy, "hung": hung, "killed": killed},
        "git": {"head": head, "modified_tracked": len(modified), "untracked": len(untracked),
                "unpushed_commits": len(unpushed.splitlines()) if unpushed else 0},
        "ledger": led,
        "capability_findings": findings,
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
    print(f"  capability findings: {findings}   <- the work queue, not the score")
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
        print(f"\n  Next tick should: {led['next_tick_should'][:300]}")
    print(f"\n  status written to {STATUS.relative_to(REPO)}")
    return verdict


if __name__ == "__main__":
    sys.exit(main())
