"""
Attester packets — the blind evidence a CAPABILITY_PROVIDERS entry has to survive.

Why this exists
---------------
Rule 9 of the hardening protocol says a `CAPABILITY_PROVIDERS` entry is a *claim that
the artifact produces what the clause names*. That is a semantic claim, and no
mechanical check can evaluate it: "does `task_type=draw_construct` constitute
*drawing*?" is a reading of MATATAG, not a lookup. §6D (validate_capability) can prove
a provider is a wildcard; it cannot prove a specific provider is the *right* one.

Until 2026-08-19 the only party answering that question was the Fixer, about its own
table, with a red line in front of it — the identical structure that produced two sets
of fabricated judgment reviews, and it produced the identical outcome: 474 of 485
entries satisfied by a generic textual formatter, and `run_all` exiting 0.

So the Attester (Rule 1's fourth blind role) answers it instead. It sees one clause and
N rendered student-path samples. It does **not** see:

  * `CAPABILITY_PROVIDERS`, or that an entry is being defended at all
  * the DNA, the formatter registry, or the generator source
  * the node id, which would let it look any of the above up

It answers one question per capability: *do these rendered items exhibit what this
clause names?* -> PROVIDED / NOT_PROVIDED, naming the sample that shows it.

Blindness is a prompt contract, not a sandbox (§6 Runtime). This module's job is to
make the blind half easy to hand over intact: `--packets` writes what the Attester
sees, `--key` writes the mapping it must not see.

Sampling uses `is_student_path=True` — the real serving path. `is_lab=True` bypasses
the competency-bound clamp, so a Lab sample can exhibit a capability the student path
can never reach, which is the exact false positive this role exists to prevent.

Usage:
    python -m tests.attester_packets --node mat_g3_mg_q1_5 \
        --packets local_only/scratch/attester/batch1.json \
        --key     local_only/scratch/attester/batch1.key.json
    python -m tests.attester_packets --unearned --limit 25 ...   # the §6D queue
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

from backend.app.practice_gen.registry import get_node_info
from backend.app.practice_gen.validation import validate_capability as VC
from backend.app.practice_gen.validation.judgment_packets import (
    _render_sample,
    _variant_coverage_candidates,
    finalize_samples,
)

# Fixed so a packet is reproducible: an Attester verdict is about specific seeds, and
# a verdict that cannot be re-rendered is not evidence.
SAMPLE_SEEDS = [11, 23, 42, 57, 64, 78, 91, 103, 118, 127]
_PROVIDER_VARIANT_SAMPLES = 2
_PROVIDER_VARIANT_ATTEMPTS = 64


def _render(node_id: str, seed: int,
            difficulty_profile: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    """One canonical student-path sample, shared with judgment packet replay."""
    # Hand the shared static renderer its exact payload, but never describe that payload
    # here. A declared jump can be present in data while React draws none; only emitted
    # markup is evidence of what the learner sees.
    #
    # FIXED 2026-08-20. This read `fd.get("visual") or fd.get("visual_data")`, and the
    # pipeline emits NEITHER key -- it puts the payload in `format_data["visual_params"]`
    # and names it in the top-level `visual_type`. So the lookup silently returned None
    # for every sample ever built, and no packet in any batch has ever carried a visual.
    #
    # The cost of that was not theoretical. Attesters correctly reported what they could
    # see -- "a textual reference to a picture is not a picture", "every item describes a
    # figure the pupil cannot see" -- and ruled clauses naming a medium (arrays, number
    # line, block or bar models, pictorial models, square grids) NOT_PROVIDED across
    # several nodes. Those verdicts were measuring THIS FUNCTION, not the pipeline:
    # `mat_g1_na_q1_2` seed 42 really does render PlaceValueBlocks with tens=1, ones=3,
    # and `mat_g2_na_q3_1` seed 11 really does render GridArea rows=4 cols=3 shaded=true.
    # Every batch built before this fix must be re-judged on the medium clauses.
    #
    # Note an item can legitimately have no visual -- `mat_g2_na_q3_1` seed 42 ("take 2
    # equal jumps of 3 on the number line") has visual_type None, so that stem names a
    # model the item does not draw. That is a real finding, and it is only separable from
    # the packet bug once the payload is actually carried.
    return _render_sample(
        node_id,
        seed,
        difficulty_profile=difficulty_profile,
        include_private_variant_evidence=True,
    )


def _provider_variants_for(node_id: str, capability_id: str) -> List[tuple]:
    """Provider variants this node can actually request, derived from the live table.

    `CAPABILITY_PROVIDERS` is capability-wide, so one entry can name alternatives owned
    by different DNAs and grades. The node-specific candidate builder applies the same
    bounds and curriculum gates as the serving path. Their intersection is therefore
    the provider-variant set this node's packet owes; neither side is copied here.
    """
    declared = (VC.CAPABILITY_PROVIDERS.get(capability_id) or {}).get("variants") or []
    reachable = set(_variant_coverage_candidates(node_id))
    return sorted(
        {tuple(variant) for variant in declared if tuple(variant) in reachable},
        key=lambda pair: (str(pair[0]), str(pair[1])),
    )


def _variant_seed_candidates(variant: tuple) -> List[int]:
    """A stable seed sequence derived from the variant, never Python's salted hash()."""
    encoded = json.dumps(list(variant), sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256(encoded).digest()
    start = 10_000 + int.from_bytes(digest[:4], "big")
    step = 1 + int.from_bytes(digest[4:8], "big") % 1_000_003
    return [start + step * attempt for attempt in range(_PROVIDER_VARIANT_ATTEMPTS)]


def _variant_evidence_paths(value: Any, key: str, prefix: str = "") -> List[tuple[str, Any]]:
    """Every recursively nested value whose key exactly names the provider dimension."""
    found: List[tuple[str, Any]] = []
    if isinstance(value, dict):
        for child_key, child in value.items():
            path = f"{prefix}.{child_key}" if prefix else str(child_key)
            if str(child_key) == key:
                found.append((path, child))
            found.extend(_variant_evidence_paths(child, key, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_variant_evidence_paths(child, key, f"{prefix}[{index}]"))
    return found


def _matching_variant_evidence(sample: Dict[str, Any], variant: tuple) -> List[str]:
    """Paths proving the rendered generator values equal the advertised variant."""
    name, wanted = str(variant[0]), variant[1]
    matches: List[str] = []
    for path, actual in _variant_evidence_paths(
        sample.get("_provider_variant_evidence") or {}, name
    ):
        if actual == wanted or str(actual) == str(wanted):
            matches.append(path)
        elif isinstance(actual, (list, tuple, set)) and any(
            item == wanted or str(item) == str(wanted) for item in actual
        ):
            matches.append(path)
    return matches


def _render_provider_variant_samples(node_id: str, variant: tuple) -> tuple[List[int], Dict[int, Dict[str, Any]]]:
    """Render two deterministic samples for one reachable provider variant, or fail loud."""
    profile = {str(variant[0]): variant[1]}
    seeds: List[int] = []
    rendered: Dict[int, Dict[str, Any]] = {}
    failures: List[str] = []
    for seed in _variant_seed_candidates(variant):
        try:
            sample = _render(node_id, seed, difficulty_profile=profile)
        except Exception as exc:  # noqa: BLE001 — retained in the named failure below
            failures.append(f"seed {seed}: {type(exc).__name__}: {exc}")
            continue
        if sample is None:
            failures.append(f"seed {seed}: renderer returned no sample")
            continue
        evidence_paths = _matching_variant_evidence(sample, variant)
        if not evidence_paths:
            failures.append(f"seed {seed}: rendered values do not exhibit {variant!r}")
            continue
        sample["_provider_variant_observation"] = evidence_paths
        seeds.append(seed)
        rendered[seed] = sample
        if len(seeds) == _PROVIDER_VARIANT_SAMPLES:
            return seeds, rendered
    raise RuntimeError(
        "provider_variant_stratification_6F: "
        f"{node_id} could not render {_PROVIDER_VARIANT_SAMPLES} samples for provider "
        f"variant {variant!r}; tried {_PROVIDER_VARIANT_ATTEMPTS} deterministic seeds. "
        f"First failures: {failures[:3]}"
    )


def _assert_provider_variant_coverage(node_id: str, packets: List[Dict[str, Any]],
                                      key: Dict[str, Any]) -> None:
    """Fail by name if any advertised stratum lost either of its two samples."""
    by_item = {packet["item"]: packet for packet in packets}
    for item, private in key.items():
        packet = by_item[item]
        samples_by_seed = {sample["seed"]: sample for sample in packet["samples"]}
        for mapping in private.get("provider_variant_seed_map") or []:
            variant = tuple(mapping["variant"])
            seeds = list(mapping["seeds"])
            if len(seeds) < _PROVIDER_VARIANT_SAMPLES or len(set(seeds)) != len(seeds):
                raise RuntimeError(
                    "provider_variant_stratification_6F: "
                    f"{node_id}/{private['capability_id']} variant {variant!r} has seeds "
                    f"{seeds}; expected {_PROVIDER_VARIANT_SAMPLES} distinct samples"
                )
            missing = [seed for seed in seeds if seed not in samples_by_seed]
            if missing:
                raise RuntimeError(
                    "provider_variant_stratification_6F: "
                    f"{node_id}/{private['capability_id']} variant {variant!r} lost "
                    f"packet sample seed(s) {missing}"
                )
            expected = {str(variant[0]): variant[1]}
            wrong = [
                seed for seed in seeds
                if (samples_by_seed[seed].get("requested") or {}).get("difficulty_profile")
                != expected
            ]
            if wrong:
                raise RuntimeError(
                    "provider_variant_stratification_6F: "
                    f"{node_id}/{private['capability_id']} variant {variant!r} has "
                    f"non-matching requested profiles at seed(s) {wrong}"
                )



def render_prompt_block(packets: List[Dict[str, Any]]) -> str:
    """
    Emit the Attester-facing text VERBATIM from a packet.

    Blindness is a prompt contract, which means the dispatcher pastes the samples into
    the subagent prompt by hand -- and on 2026-08-20 that hand introduced a defect the
    packet did not have. A stem was shortened when pasted, so
    `mat_g2_na_q3_5` seed 23 reached the Attester as

        Rosa solved: "...you subtract ___ times before reaching 0". Rosa's answer
        contains an error.

    when the pipeline actually renders

        Rosa solved: "...you subtract ___ times before reaching 0". Rosa says the
        missing number is 10. Is Rosa correct?

    The Attester then correctly reported that there was nothing on the page to find an
    error in, and that verdict was filed as a pipeline defect. It was a transcription
    defect. Use this function instead of retyping: whatever it returns is what the
    Attester sees, and it is copied from the packet rather than summarised.
    """
    out: List[str] = []
    for item in packets:
        out.append("=" * 70)
        # The opaque item id is the ONLY handle the Attester has on this clause, and
        # `tests/attester_file.py` joins the returned verdicts to the key on it. Omitting
        # it forces the Fixer to re-identify each verdict by hand -- the retyping step
        # this function exists to remove.
        out.append(f"ITEM: {item['item']}")
        out.append(f"COMPETENCY (Grade {item['grade']}, Quarter {item['quarter']}):")
        out.append(item["competency"])
        out.append("")
        strata = item.get("provider_variant_strata") or []
        if strata:
            out.append("PROVIDER-VARIANT SEED MAP (variant labels withheld for blindness):")
            for stratum in strata:
                out.append(
                    f"  {stratum['stratum']}: "
                    + ", ".join(str(seed) for seed in stratum["seeds"])
                )
            out.append("")
        out.append("SAMPLES:")
        for s in item["samples"]:
            out.append(f"  seed {s['seed']}: {s['question_text']}")
            out.append(f"        key: {s['correct_answer']}")
            opts = s.get("options")
            if opts:
                vals = [str(o.get("value")) if isinstance(o, dict) else str(o) for o in opts]
                out.append(f"        options: {' / '.join(vals)}")
            if s.get("visual_type"):
                out.append(f"        VISUAL RENDERED: {s['visual_type']}")
                out.append(
                    "        rendered structure: "
                    + json.dumps(s.get("visual_render", {}).get("description"), ensure_ascii=False)
                )
            if s.get("hint"):
                out.append(f"        hint: {s['hint']}")
        out.append("")
        out.append(f"CLAUSE: {item['clause']}")
        out.append("")
    return "\n".join(out)

def build(node_ids: List[str], capabilities: List[str] | None = None) -> tuple:
    """
    Returns (packets, key).

    `packets` is the blind half: an opaque item id, the clause, and the samples.
    `key` is the half the Attester must never see: which node and which registered
    provider each item is really about.
    """
    packets: List[Dict[str, Any]] = []
    key: Dict[str, Any] = {}
    n = 0

    for node_id in node_ids:
        meta = get_node_info(node_id) or {}
        requires = meta.get("requires") or []
        samples_by_seed: Dict[int, Dict[str, Any]] = {}
        for seed in SAMPLE_SEEDS:
            s = _render(node_id, seed)
            if s is not None:
                samples_by_seed[seed] = s
        if not samples_by_seed:
            raise RuntimeError(
                f"{node_id}: rendered no student-path samples across seeds {SAMPLE_SEEDS}. "
                f"An Attester cannot rule on an empty packet, and a capability with no "
                f"reachable content is a §6C failure, not a packet to file."
            )

        variant_maps: Dict[str, List[Dict[str, Any]]] = {}
        rendered_by_variant: Dict[tuple, Dict[int, Dict[str, Any]]] = {}
        for req in requires:
            cap = str(req.get("id", ""))
            if capabilities is not None and cap not in capabilities:
                continue
            exact_map: List[Dict[str, Any]] = []
            variants = _provider_variants_for(node_id, cap)
            for variant in variants:
                if variant not in rendered_by_variant:
                    seeds, rendered = _render_provider_variant_samples(node_id, variant)
                    rendered_by_variant[variant] = rendered
                else:
                    rendered = rendered_by_variant[variant]
                    seeds = sorted(rendered)
                exact_map.append({"variant": list(variant), "seeds": seeds})
            variant_maps[cap] = exact_map

        # One filed attestation record carries one samples_judged block per node, not
        # per clause. Every item therefore receives this node-wide union. That keeps the
        # filer honest: it records every sample every verdict could cite, while the
        # opaque per-item map below says which seeds were deliberately allocated for
        # that clause without exposing CAPABILITY_PROVIDERS to the Attester.
        for exact_map in variant_maps.values():
            for mapping in exact_map:
                variant = tuple(mapping["variant"])
                for seed in mapping["seeds"]:
                    samples_by_seed[seed] = rendered_by_variant[variant][seed]

        from tests.frontend_renderer import attach_rendered_visual_descriptions

        ordered_samples = []
        for seed in sorted(samples_by_seed):
            sample = dict(samples_by_seed[seed])
            sample.pop("_provider_variant_evidence", None)
            sample.pop("_provider_variant_observation", None)
            ordered_samples.append(sample)
        samples = finalize_samples(attach_rendered_visual_descriptions(ordered_samples))

        for req in requires:
            cap = str(req.get("id", ""))
            if capabilities is not None and cap not in capabilities:
                continue
            n += 1
            item = f"item_{n:03d}"
            packets.append({
                "item": item,
                "clause": req.get("clause"),
                "competency": meta.get("competency", ""),
                "grade": meta.get("grade"),
                "quarter": meta.get("quarter"),
                "question": (
                    "Do the rendered items below exhibit what this clause names? "
                    "Answer PROVIDED or NOT_PROVIDED and name the seed(s) that show it."
                ),
                "provider_variant_strata": [
                    {"stratum": f"stratum_{index:03d}", "seeds": list(mapping["seeds"])}
                    for index, mapping in enumerate(variant_maps.get(cap, []), start=1)
                ],
                "samples": samples,
            })
            key[item] = {
                "node_id": node_id,
                "capability_id": cap,
                "registered_provider": VC.CAPABILITY_PROVIDERS.get(cap),
                "provider_variant_seed_map": variant_maps.get(cap, []),
            }
        node_items = [packet for packet in packets
                      if key[packet["item"]]["node_id"] == node_id]
        node_key = {packet["item"]: key[packet["item"]] for packet in node_items}
        _assert_provider_variant_coverage(node_id, node_items, node_key)
    return packets, key


def _unearned_targets() -> Dict[str, List[str]]:
    """The §6D queue: capabilities currently carried only by a generic formatter.

    Phase 1 only. §6D is emitted by `_validate_provision`, which reads nothing under
    validation_reports/, so building this queue never needed the 10s attestation sweep
    the whole-contract call used to drag in behind it.
    """
    out: Dict[str, List[str]] = {}
    for e in VC.validate_capability_provision():
        if "§6D" not in e:
            continue
        m = re.match(r"^(\S+): competency requires '([^']+)'", e)
        if m:
            out.setdefault(m.group(1), []).append(m.group(2))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", action="append", default=[])
    ap.add_argument("--unearned", action="store_true",
                    help="build packets for every capability §6D reports as unearned")
    ap.add_argument("--limit", type=int, default=0, help="cap the number of items (batch <=25)")
    ap.add_argument("--packets", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--record", help="also emit a pre-filled attestation record skeleton")
    args = ap.parse_args()

    caps = None
    nodes = list(args.node)
    if args.unearned:
        targets = _unearned_targets()
        nodes = nodes or sorted(targets)
        caps = sorted({c for n in nodes for c in targets.get(n, [])})
    if not nodes:
        raise SystemExit("no nodes selected: pass --node or --unearned")

    packets, key = build(nodes, caps)
    if args.limit:
        packets = packets[: args.limit]
        key = {k: v for k, v in key.items() if k in {p["item"] for p in packets}}

    # A record skeleton pre-filled with the exact samples the Attester will see, so a
    # filed verdict always carries re-renderable evidence. §6F fails any batch without
    # it; emitting it here means a future batch cannot omit it by accident.
    if args.record:
        skeleton = [{
            "batch": Path(args.record).stem,
            "attested_at": "<ISO timestamp>",
            "role": "Attester",
            "packet": {"builder": "tests/attester_packets.py",
                       "sampling": "is_student_path=True",
                       "node_id": nodes[0] if len(nodes) == 1 else "<one node per record>",
                       "seeds": SAMPLE_SEEDS,
                       # `options` is recorded because the Attester SEES it --
                       # render_prompt_block prints the option list under every
                       # sample -- so a verdict rests on it, and §6F freshness cannot
                       # check option drift or resolve an A-D key without it. This
                       # skeleton omitted the field until 2026-09-10 while `_render`
                       # above computed it: measured that day, 0 of 1790 recorded
                       # samples carried options, which left 137 of 151 live records
                       # unadjudicable and un-repairable (a record may not be edited;
                       # what was shown is simply not written down). Copy every field
                       # `_render` produces rather than a hand-listed subset, so the
                       # next field added to a packet cannot go unrecorded the same
                       # way.
                       "samples_judged": [
                           dict(s) for s in (packets[0]["samples"] if packets else [])
                       ]},
            "verdicts": [{"capability_id": key[p["item"]]["capability_id"],
                          "node_id": key[p["item"]]["node_id"],
                          "clause": p["clause"],
                          "verdict": "<PROVIDED|NOT_PROVIDED>",
                          "seeds_showing_it": [], "reasoning": "<from the Attester>",
                          "action_taken": "<what you did about it>"} for p in packets],
        }]
        Path(args.record).parent.mkdir(parents=True, exist_ok=True)
        Path(args.record).write_text(json.dumps(skeleton[0], indent=2, ensure_ascii=False),
                                     encoding="utf-8")
        print(f"record skeleton: {args.record}  (fill in verdicts, then file it)")

    for path, payload in ((args.packets, packets), (args.key, key)):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"packets: {len(packets)} item(s) -> {args.packets}")
    print(f"key:     {len(key)} mapping(s) -> {args.key}   (Attester must not see this)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
