"""§14 domain checks (validate_slots.check_slot / replay, unchanged) over seeds 1-40 + every pinned formatter."""
import sys, collections
from backend.app.practice_gen.validation import validate_slots as VS
from backend.app.practice_gen.registry import get_all_node_ids, get_node_formatters
from backend.app.practice_gen.slots import capture
from backend.app.services.orchestrator import PracticeOrchestrator
from backend.app.services import orchestrator as _orch
if __name__ == "__main__":
    bad = collections.Counter(); ex = {}
    for n in sorted(get_all_node_ids()):
        runs = [(s, None) for s in range(1, 41)] + [(s, f) for f in sorted(get_node_formatters(n) or []) for s in (3, 17, 29)]
        for seed, fmt in runs:
            seen = {}; real = _orch.apply_formatter
            def spy(ctx, f, rng):
                seen.update(ctx.values or {}); return real(ctx, f, rng)
            _orch.apply_formatter = spy
            try:
                with capture() as fills:
                    PracticeOrchestrator.generate_problem(node_id=n, seed=seed, formatter=fmt, is_student_path=fmt is None)
            except Exception:
                continue
            finally:
                _orch.apply_formatter = real
            texts = {f.text for f in fills}; produced = collections.Counter(f.text for f in fills)
            for f in fills:
                if VS.replay(f): bad[("mismatch", f.site)] += 1; ex.setdefault(("mismatch", f.site), (n, seed, fmt, VS.replay(f)))
                others = texts if produced[f.text] > 1 else texts - {f.text}
                for name, value, domain in f.slots:
                    r = VS.check_slot(value, domain, seen, others)
                    if r and r[0] in ("slot_domain_escape_14", "slot_text_unaccounted_14"):
                        k = (f.site, name); bad[k] += 1; ex.setdefault(k, (n, seed, fmt, r[1][:120]))
    for k, v in bad.most_common(): print(v, k, ex[k])
    print("TOTAL distinct", len(bad))
