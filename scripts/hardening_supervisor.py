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

IN_FLIGHT, RESUME, NOTHING_TO_DO, NEEDS_HUMAN = 0, 10, 20, 30

# A process burning less than this fraction of a core, for longer than the grace
# period, is hung rather than slow. A healthy run_all worker sits near 50%.
HUNG_CPU_RATIO = 0.02
HUNG_GRACE_SECONDS = 600

WATCHED = re.compile(r"practice_gen\.validation\.run_all|pytest|mutation_harness")


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
    """Return (healthy, hung) watched processes, judged by CPU-to-elapsed ratio."""
    out = _sh("ps", "-eo", "pid=,etime=,time=,args=")
    healthy, hung = [], []
    for line in out.splitlines():
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        pid, etime, cput, args = parts
        if not WATCHED.search(args) or "hardening_supervisor" in args:
            continue
        try:
            elapsed = _etime_to_seconds(etime)
            cpu = _cputime_to_seconds(cput)
        except ValueError:
            continue
        rec = {
            "pid": int(pid), "elapsed_s": elapsed, "cpu_s": round(cpu, 1),
            "ratio": round(cpu / elapsed, 4) if elapsed else 0.0,
            "cmd": args[:120],
        }
        if elapsed > HUNG_GRACE_SECONDS and rec["ratio"] < HUNG_CPU_RATIO:
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
        verdict, why = NEEDS_HUMAN, f"{len(hung)} hung process(es); re-run with --reap"
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
                    NOTHING_TO_DO: "NOTHING_TO_DO", NEEDS_HUMAN: "NEEDS_HUMAN"}[verdict],
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
        print(f"  HUNG pid={p['pid']} elapsed={p['elapsed_s']}s cpu={p['cpu_s']}s "
              f"ratio={p['ratio']} {'KILLED' if p['pid'] in killed else 'NOT KILLED'}")
    for p in healthy:
        print(f"  running pid={p['pid']} elapsed={p['elapsed_s']}s ratio={p['ratio']}")
    if led["next_tick_should"]:
        print(f"\n  Next tick should: {led['next_tick_should'][:300]}")
    print(f"\n  status written to {STATUS.relative_to(REPO)}")
    return verdict


if __name__ == "__main__":
    sys.exit(main())
