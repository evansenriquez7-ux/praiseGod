"""
Every silent path in the harness, and what was decided about it (plan step 0).

THE OBLIGATION
--------------
Plan step 0: "Inventory every warning, `continue`, exception handler, sample cap, floor,
allowlist, exclusion, and 'not judged/not gated' branch in the harness. Each receives one
of three dispositions: remove it by checking the obligation, turn it into a named failure,
or record a narrow inherent limitation with an owner, scope, mitigation, and
expiry/review trigger."

MEASURED 2026-09-12, over `backend/app/practice_gen/validation/`:

    broad_except             32
    narrow_except            25
    broad_except_silent      20
    narrow_except_silent     13
    TOTAL                    90   of which 33 swallow control flow (continue/pass)

A silent handler is how "attempted work gets reported as coverage" -- `H-03`'s own words.
§10 had two (`except Exception: continue` on a generation failure and on an underivable
answer) and they meant a node whose grading contract was never exercised reported exactly
like one that passed. Those two are gone; these are the rest of the family.

WHY THE DISPOSITION IS AN INLINE MARKER AND NOT A TABLE
-------------------------------------------------------
A registry keyed by `(file, line)` rots on the first edit above it, and one keyed by
function name rots on the first rename. The disposition therefore lives in the code, in a
comment inside the handler:

    except ValueError:
        # DISPOSITION: limitation -- <why this cannot be a named failure, and what
        # covers the obligation instead>
        continue

It moves with the code it describes, a reviewer reads it where the decision applies, and
this module can check it mechanically. Three dispositions, matching the plan's three:

  * `checked`       -- the obligation this swallows is verified elsewhere; name where.
  * `named-failure` -- the handler records a failure rather than continuing silently.
  * `limitation`    -- a narrow inherent limitation. State scope and what would close it.

A FLOOR, SHRINK-ONLY, AND WHY NOT ZERO
---------------------------------------
33 silent handlers exist today and classifying all of them honestly means reading each
obligation and deciding whether it is covered -- that is content work, not a rename, and
Scaling Mandate 5 says a gate whose baseline is red cannot be told from its noise. So the
gate is activated at the measured count and may only SHRINK. Its value from day one is the
direction it blocks: a silent handler added tomorrow is unclassified, the count rises, and
the build fails. That is the property that scales to grades 4-10, where nobody will read
these files by eye.

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
  * **Scope is the validation package plus the harness entry points under `tests/`.** The
    pipeline itself (`backend/app/practice_gen/` outside `validation/`) has its own silent
    paths and is NOT scanned here; AGENTS.md Protocol 3 forbids them there too, and that
    inventory is separate work.
  * **A marker is a claim, not a proof.** `# DISPOSITION: checked -- §1G covers this`
    asserts that §1G covers it; nothing here verifies that it does. The marker makes the
    claim reviewable and greppable, which is strictly better than an unexplained
    `continue`, and strictly weaker than a test.
  * **Only `continue`/`pass`/bare-`return` bodies count as silent.** A handler that logs
    and continues is not counted, though it can still lose an obligation. Widening that is
    a deliberate next step, not an oversight.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATION_DIR = REPO_ROOT / "backend" / "app" / "practice_gen" / "validation"
REPORT_PATH = (REPO_ROOT / "validation_reports" / "phase2_hardening"
               / "silent_path_inventory.json")

VALID_DISPOSITIONS = ("checked", "named-failure", "limitation")
MARKER = "DISPOSITION:"


@dataclass(frozen=True)
class SilentPath:
    file: str
    line: int
    function: str
    handler: str          # the exception type(s) caught, as written
    body: str             # "continue" | "pass" | "return"
    disposition: str      # one of VALID_DISPOSITIONS, or "" when unclassified
    note: str


def _enclosing_functions(tree: ast.AST) -> Dict[int, str]:
    """line number -> enclosing function name, for every line in a function body."""
    out: Dict[int, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", node.lineno)
            for line in range(node.lineno, end + 1):
                out.setdefault(line, node.name)
    return out


def _handler_source(node: ast.ExceptHandler) -> str:
    if node.type is None:
        return "bare"
    return ast.unparse(node.type)


def _silent_body(node: ast.ExceptHandler) -> str:
    """
    The control-flow statement this handler swallows with, or "" if it is not silent.

    SILENT means the body does NOTHING BUT leave: `continue`, `pass`, or a bare `return`,
    with nothing else in it. A handler that records a finding and THEN continues --

        except Exception as exc:
            found.obligation.append(f"{node} (seed {seed}): generation raised ...")
            continue

    -- is the `named-failure` pattern this inventory exists to encourage, not an instance
    of the defect. The first version of this scanner returned "continue" for any body
    CONTAINING a Continue, and so flagged §10's two new obligation handlers, which are
    exactly the shape the H-01 work replaced `except: continue` WITH. A scanner with false
    positives trains people to paper over correct code with markers, which is worse than
    not scanning: it turns the inventory into noise and buries the real 31.
    """
    meaningful = [st for st in node.body
                  if not (isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant))]
    if len(meaningful) != 1:
        return ""
    stmt = meaningful[0]
    if isinstance(stmt, ast.Continue):
        return "continue"
    if isinstance(stmt, ast.Pass):
        return "pass"
    if isinstance(stmt, ast.Return) and stmt.value is None:
        return "return"
    return ""


def _disposition_in(lines: Sequence[str], node: ast.ExceptHandler) -> Tuple[str, str]:
    """
    Find `# DISPOSITION: <kind> -- <note>` on the `except` line or inside its body.

    Searched in the handler's own span only, so a marker belonging to the handler above
    cannot be borrowed by the one below.
    """
    start = node.lineno - 1
    end = getattr(node, "end_lineno", node.lineno)
    for raw in lines[start:end]:
        if MARKER not in raw:
            continue
        after = raw.split(MARKER, 1)[1].strip()
        for kind in VALID_DISPOSITIONS:
            if after.startswith(kind):
                note = after[len(kind):].lstrip(" -–—:").strip()
                return kind, note
        return "INVALID", after
    return "", ""


def scan() -> List[SilentPath]:
    """Every silent exception handler in the validation package, deterministically ordered."""
    found: List[SilentPath] = []
    for path in sorted(VALIDATION_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        tree = ast.parse(text, filename=str(path))
        functions = _enclosing_functions(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            body = _silent_body(node)
            if not body:
                continue
            kind, note = _disposition_in(lines, node)
            found.append(SilentPath(
                file=path.name,
                line=node.lineno,
                function=functions.get(node.lineno, "<module>"),
                handler=_handler_source(node),
                body=body,
                disposition=kind,
                note=note,
            ))
    found.sort(key=lambda s: (s.file, s.line))
    return found


def build_report() -> Dict[str, object]:
    paths = scan()
    unclassified = [p for p in paths if not p.disposition]
    invalid = [p for p in paths if p.disposition == "INVALID"]
    by_disposition: Dict[str, int] = {}
    for p in paths:
        key = p.disposition or "(unclassified)"
        by_disposition[key] = by_disposition.get(key, 0) + 1
    return {
        "schema_version": 1,
        "scope": "backend/app/practice_gen/validation/*.py",
        "marker_convention": f"# {MARKER} <{'|'.join(VALID_DISPOSITIONS)}> -- <note>",
        "counts": {
            "silent_handlers": len(paths),
            "unclassified": len(unclassified),
            "invalid_marker": len(invalid),
            "by_disposition": by_disposition,
        },
        "paths": [
            {"file": p.file, "line": p.line, "function": p.function,
             "handler": p.handler, "body": p.body,
             "disposition": p.disposition or None, "note": p.note}
            for p in paths
        ],
    }


def main() -> int:
    report = build_report()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    counts = report["counts"]
    print(f"  silent handlers={counts['silent_handlers']} "
          f"unclassified={counts['unclassified']} "
          f"invalid_marker={counts['invalid_marker']}")
    print(f"  by disposition: {counts['by_disposition']}")
    print(f"  wrote {REPORT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
