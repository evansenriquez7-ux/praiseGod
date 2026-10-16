"""
Practice Generation — Every Content Finding Is Named (owner rulings 23 and 52)

Ruling 23 makes Phase 2 done only when "every finding [is] reported by name with its lc, seed
and what to build". Ruling 52 says what that means: each content finding prints

  * its **lc** (a registered lc id) -- or, for a route-level finding (ruling 53), the
    registered formatter route it names, written `route '<name>'`;
  * a **witness seed**: a render that shows the defect (`seed N`, `seeds [..]`,
    `seed=N`, `every seed of [..]`) -- or, only where no render can exist, the marker
    `ruled substitute (ruling 52)` followed by what stands in for the seed;
  * the **owed build**, introduced by `Owed:`.

How it is read. A stage reports a content finding the way the verdict already reads labels:
a `  FAIL <label>` line, then one `    - <finding>` line per finding (deeper-indented lines
continue the finding above them). `run_all` passes every stage's captured output to
`problems_in_output`, which checks every block whose label `_manifest.FINDING_CLASS`
classes CONTENT. Integrity blocks are not read: their remedy is harness work, not a
generator build.

  content_finding_named   INTEGRITY. A content finding without an lc (or route), a witness
                          seed or the substitute, or an owed build; a content block with no
                          finding lines under it; or a block cut short with `... and N more`
                          (a finding that is not printed is not reported by name).

The matrix reports structured findings, not `  FAIL` blocks; run_all checks each one through
`validate_matrix.named_finding`, the same text the matrix prints, so it is held to the same rule.

NAMED LIMITS (Scaling Mandate 6; also in the contract row):
  1. **A content label that has not fired is not read.** Its message shape is checked the
     first time it fires -- and then fails integrity by name, loudly, rather than passing.
  2. **Shape, not truth.** The rule proves a seed and an owed build are PRINTED, not that the
     seed reproduces the defect or that the build is the right one. Reproduction is each
     stage's own `Reproduce:` text; cross-process determinism of a seed is §14's
     determinism stage (ruling 54).
  3. **The substitute is self-declared.** A finding may print `ruled substitute (ruling 52)`
     where a witness render exists; only the rulings say where it is allowed (a
     NOT_PRODUCIBLE clause, a packet refused before any render, an lc-wide verdict on a
     retired record, an absence such as an unserved formatter or route).
"""
from __future__ import annotations

import re
import sys
from typing import Dict, Iterable, List, Optional, Set

ASSERTIONS = (
    "content_finding_named",   # a content finding lacks lc/route, witness seed or substitute, or owed build
)

SUBSTITUTE = "ruled substitute (ruling 52)"
_HEADER = re.compile(r"^  FAIL ([A-Za-z_][A-Za-z0-9_.]*)")
_ITEM = re.compile(r"^    - (.*)$")
_CONTINUATION = re.compile(r"^      \S")
_TRUNCATED = re.compile(r"^\s+\.\.\. and \d+ more")
_SEED = re.compile(r"\bseeds? -?\d|\bseeds \[-?\d|\bseeds? of \[-?\d|\bseed=-?\d")
_LEAD = re.compile(r"^([A-Za-z0-9_]+)\b")
_ROUTE = re.compile(r"^route '([^']+)'")


def _known_lcs() -> Set[str]:
    from backend.app.practice_gen.registry import get_all_node_ids

    return set(get_all_node_ids())


def _known_routes() -> Set[str]:
    from backend.app.practice_gen.adapter import FORMATTER_ROUTES

    return set(FORMATTER_ROUTES)


def finding_problems(finding: str, lcs: Set[str], routes: Set[str]) -> List[str]:
    """What ruling 52 finds missing from one finding's text (empty: it is named)."""
    missing = []
    route = _ROUTE.match(finding)
    lead = _LEAD.match(finding)
    if not ((route and route.group(1) in routes) or (lead and lead.group(1) in lcs)):
        missing.append("an lc id (or `route '<registered route>'`) as its first word")
    if not (_SEED.search(finding) or SUBSTITUTE in finding):
        missing.append(f"a witness seed (`seed N`) or `{SUBSTITUTE}`")
    if "Owed:" not in finding:
        missing.append("an owed build (`Owed: ...`)")
    return missing


def blocks(text: str) -> List[Dict[str, object]]:
    """Every `  FAIL <label>` block in `text`: {label, header, items, truncated}."""
    out: List[Dict[str, object]] = []
    current: Optional[Dict[str, object]] = None
    for line in text.splitlines():
        head = _HEADER.match(line)
        if head:
            current = {"label": head.group(1), "header": line.strip(), "items": [], "truncated": False}
            out.append(current)
            continue
        if current is None:
            continue
        item = _ITEM.match(line)
        if item:
            current["items"].append(item.group(1))
        elif _CONTINUATION.match(line) and current["items"]:
            current["items"][-1] += " " + line.strip()
        elif _TRUNCATED.match(line):
            current["truncated"] = True
        else:
            current = None
    return out


def problems_in_output(text: str, stage: str = "?", content_labels: Optional[Iterable[str]] = None,
                       lcs: Optional[Set[str]] = None, routes: Optional[Set[str]] = None) -> List[str]:
    """`content_finding_named` problems in one stage's printed output."""
    from backend.app.practice_gen.validation._manifest import CONTENT, finding_class

    if content_labels is None:
        is_content = lambda label: finding_class(label, family=True) == CONTENT  # noqa: E731
    else:
        is_content = set(content_labels).__contains__
    lcs = _known_lcs() if lcs is None else lcs
    routes = _known_routes() if routes is None else routes
    problems: List[str] = []
    for block in blocks(text):
        label = str(block["label"])
        if not is_content(label):
            continue
        items: List[str] = block["items"]  # type: ignore[assignment]
        if not items:
            problems.append(f"stage {stage!r}: content block {block['header'][:120]!r} lists no finding "
                            f"under it, so nothing is reported by name (ruling 23).")
        if block["truncated"]:
            problems.append(f"stage {stage!r}: content block {block['header'][:120]!r} is cut short with "
                            f"'... and N more'; every content finding must be printed (ruling 23).")
        for finding in items:
            missing = finding_problems(finding, lcs, routes)
            if missing:
                problems.append(f"stage {stage!r}: {label} finding {finding[:160]!r} lacks "
                                f"{'; '.join(missing)} (ruling 52).")
    return problems


def main() -> int:
    """Read a saved run_all log and report every unnamed content finding in it."""
    import argparse

    ap = argparse.ArgumentParser(description="ruling 52: every content finding names lc, seed, owed build")
    ap.add_argument("log", help="a saved run_all (or stage) output")
    args = ap.parse_args()
    with open(args.log, encoding="utf-8") as fh:
        problems = problems_in_output(fh.read(), stage=args.log)
    for p in problems:
        print(f"  - {p}")
    print(f"  {'FAIL' if problems else 'PASS'} content_finding_named ({len(problems)})")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
