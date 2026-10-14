"""
§14's own domain checks (`validate_slots.check_slot` / `replay`, unchanged) over §14's own
`validate_slots.paths` (seeds 1-40 on the student path plus every advertised formatter pinned at
seeds 3, 17, 29). Since owner ruling 44b (batch H4) the stage renders these same paths, so this is
a per-(site, slot) view of what the stage reports per lc, not a wider one. Prints one line per escaping (site, slot) with its count
and first (lc, seed, formatter, reason), then the distinct total. A render that raises is printed
and counted, never skipped silently (Protocol 3).

Promoted from validation_reports/phase2_hardening/h3r2_tools/wide_check.py in batch H4-0.

    PYTHONPATH=. .venv/bin/python tests/slot_wide_check.py
"""
import collections

from backend.app.practice_gen.validation import validate_slots as VS
from backend.app.practice_gen.registry import get_all_node_ids
from backend.app.practice_gen.slots import capture
from backend.app.services.orchestrator import PracticeOrchestrator
from backend.app.services import orchestrator as _orch

if __name__ == "__main__":
    bad = collections.Counter(); ex = {}; raised = []
    for n in sorted(get_all_node_ids()):
        runs = VS.paths(n)      # §14's own enumeration (owner ruling 44b): one copy
        for seed, fmt in runs:
            seen = {}; real = _orch.apply_formatter

            def spy(ctx, f, rng):
                seen.update(ctx.values or {}); return real(ctx, f, rng)
            _orch.apply_formatter = spy
            try:
                with capture() as fills:
                    PracticeOrchestrator.generate_problem(node_id=n, seed=seed, formatter=fmt, is_student_path=fmt is None)
            except Exception as exc:   # a pinned pair that refuses: reported below, not hidden
                raised.append((n, seed, fmt, f"{type(exc).__name__}: {str(exc)[:120]}"))
                continue
            finally:
                _orch.apply_formatter = real
            texts = {f.text for f in fills}; produced = collections.Counter(f.text for f in fills)
            for f in fills:
                if VS.replay(f):
                    bad[("mismatch", f.site)] += 1; ex.setdefault(("mismatch", f.site), (n, seed, fmt, VS.replay(f)))
                others = texts if produced[f.text] > 1 else texts - {f.text}
                srcs, whys = dict(f.sources), dict(f.reasons)
                for name, value, domain in f.slots:
                    r = VS.check_slot(value, domain, seen, others, why=whys.get(name), src=srcs.get(name, ()),
                                      vocab=VS.lc_vocab(n))
                    if r and r[0] in ("slot_domain_escape_14", "slot_text_unaccounted_14"):
                        k = (f.site, name); bad[k] += 1; ex.setdefault(k, (n, seed, fmt, r[1][:120]))
    for k, v in bad.most_common():
        print(v, k, ex[k])
    for r in raised:
        print("RAISED", r)
    print("TOTAL distinct", len(bad), "| renders that raised:", len(raised))
