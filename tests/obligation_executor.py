"""Execute the finite student-path obligation manifest (plan step 0B, H-04).

The enumerator in :mod:`tests.obligation_manifest` proves what production says is
reachable.  This module proves that those declarations can actually be served.  Its
finite execution unit is:

    (node, DNA, formatter, discrete assignment, interest request, experience, seed slot)

Five deterministic seed slots are required for release.  Slots 0, 1, and 2 pin every
continuous axis to its minimum boundary, interior representative, and maximum boundary;
slots 3 and 4 are additional deterministic interior samples.  Axes move together within
a slot.  Cross-axis Cartesian interactions remain unproved: the manifest partitions each
axis independently and does not claim the product of multiple continuous axes.

The expensive generator/formatter result is cached across the four experience wrappers.
That cache is sound because ``apply_experience`` is the final production step and none of
the wrappers changes generation inputs.  The cache key is therefore the base obligation,
interest request, and seed slot; all four production wrappers are then executed on deep
copies.  The benchmark and every shard report both cache-key generations and represented
finite executions so the optimization cannot masquerade as dropped coverage.

CLI examples::

    python -m tests.obligation_executor --tier benchmark --sample-size 1000
    python -m tests.obligation_executor --tier pr
    python -m tests.obligation_executor --tier release --shard-count 6 --shard-index 0
    python -m tests.obligation_executor --tier verify-release

The PR tier is explicitly partial: it runs fixed sentinels spanning every current node,
DNA, formatter, interest-request value, experience, and continuous seed slot.  Callers may
also pass ``--changed-obligation-key``; every matching base obligation is then crossed with
all interests, experiences, and seed slots.  A release is complete only when receipts for
all shards verify as a non-overlapping union of the current manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import resource
import statistics
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = REPO_ROOT / "validation_reports" / "phase2_hardening"
BENCHMARK_PATH = REPORT_ROOT / "obligation_benchmark.json"
RELEASE_RECEIPT_DIR = REPORT_ROOT / "obligation_release_shards"

DEFAULT_SEEDS_PER_OBLIGATION = 5
REFERENCE_WORKERS = 4
TARGET_PR_SECONDS = 30 * 60
TARGET_SHARD_SECONDS = 30 * 60
TARGET_RELEASE_SECONDS = 4 * 60 * 60

# The first three slots prove the declared continuous classes.  Two further interior
# points provide the plan's minimum of five deterministic seeds without claiming new
# equivalence classes.
SEED_SLOT_SCALARS: Tuple[float, ...] = (0.0, 0.5, 1.0, 0.25, 0.75)


@dataclass(frozen=True)
class ExecutionFailure:
    cache_index: int
    seed: int
    obligation_key: str
    exception_type: str
    message: str


@dataclass(frozen=True)
class CacheResult:
    cache_index: int
    elapsed_seconds: float
    represented_executions: int
    response_modes: Tuple[str, ...]
    renderers: Tuple[str, ...]
    peak_rss_bytes: int
    failure: Optional[ExecutionFailure]


@lru_cache(maxsize=1)
def _base_obligations():
    from tests.obligation_manifest import enumerate_obligations

    return tuple(enumerate_obligations()[0])


@lru_cache(maxsize=1)
def experience_values() -> Tuple[str, ...]:
    from backend.app.practice_gen.pipeline import get_pipeline_status

    return tuple(sorted(get_pipeline_status()["experiences_available"]))


@lru_cache(maxsize=1)
def interest_request_values() -> Tuple[Optional[str], ...]:
    bank = json.loads((REPO_ROOT / "data" / "interest_bank.json").read_text(
        encoding="utf-8"
    ))["interests"]
    # None means the production automatic-selection path.  It is not a neutral theme:
    # pick_interest() deterministically chooses a grade-appropriate theme from the seed.
    return (None, *sorted(bank))


def base_manifest_digest() -> str:
    """Digest the exact ordered base keys and execution dimension values."""
    payload = {
        "base_keys": [o.key() for o in _base_obligations()],
        "experiences": experience_values(),
        "interest_requests": [v if v is not None else "(automatic)"
                              for v in interest_request_values()],
        "seed_slot_scalars": SEED_SLOT_SCALARS,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def source_input_digest() -> str:
    """Bind benchmark/receipts to the same working-tree bytes as mutation proofs."""
    from backend.app.practice_gen.validation.mutation_proof import input_digest

    return input_digest()


def finite_obligation_count() -> int:
    """Count before seed slots: base × interest requests × experience wrappers."""
    return len(_base_obligations()) * len(interest_request_values()) * len(experience_values())


def cache_key_count(seeds_per_obligation: int = DEFAULT_SEEDS_PER_OBLIGATION) -> int:
    _validate_seed_count(seeds_per_obligation)
    return len(_base_obligations()) * len(interest_request_values()) * seeds_per_obligation


def represented_execution_count(
    seeds_per_obligation: int = DEFAULT_SEEDS_PER_OBLIGATION,
) -> int:
    return cache_key_count(seeds_per_obligation) * len(experience_values())


def _validate_seed_count(seeds_per_obligation: int) -> None:
    if not 5 <= seeds_per_obligation <= 10:
        raise ValueError(
            f"seeds_per_obligation={seeds_per_obligation}; the release contract requires 5-10"
        )


def decode_cache_index(
    cache_index: int,
    seeds_per_obligation: int = DEFAULT_SEEDS_PER_OBLIGATION,
) -> Tuple[Any, Optional[str], int]:
    total = cache_key_count(seeds_per_obligation)
    if cache_index < 0 or cache_index >= total:
        raise IndexError(f"cache_index={cache_index} outside [0, {total})")
    per_base = len(interest_request_values()) * seeds_per_obligation
    base_index, remainder = divmod(cache_index, per_base)
    interest_index, seed_slot = divmod(remainder, seeds_per_obligation)
    return (_base_obligations()[base_index], interest_request_values()[interest_index],
            seed_slot)


def encode_cache_index(
    base_index: int,
    interest_index: int,
    seed_slot: int,
    seeds_per_obligation: int = DEFAULT_SEEDS_PER_OBLIGATION,
) -> int:
    _validate_seed_count(seeds_per_obligation)
    if not 0 <= base_index < len(_base_obligations()):
        raise IndexError(f"base_index={base_index}")
    if not 0 <= interest_index < len(interest_request_values()):
        raise IndexError(f"interest_index={interest_index}")
    if not 0 <= seed_slot < seeds_per_obligation:
        raise IndexError(f"seed_slot={seed_slot}")
    return ((base_index * len(interest_request_values()) + interest_index)
            * seeds_per_obligation + seed_slot)


def stable_seed(obligation_key: str, interest: Optional[str], seed_slot: int) -> int:
    material = (
        f"{obligation_key}|interest={interest or '(automatic)'}|seed_slot={seed_slot}"
    ).encode("utf-8")
    # Stay in signed 31-bit space for parity with database/API consumers while keeping
    # the mapping deterministic across processes and Python versions.
    return int.from_bytes(hashlib.sha256(material).digest()[:4], "big") & 0x7FFFFFFF


def difficulty_profile_for(obligation: Any, seed_slot: int) -> Dict[str, Any]:
    from tests.obligation_manifest import _continuous_axes

    profile: Dict[str, Any] = dict(obligation.assignment)
    scalar = SEED_SLOT_SCALARS[seed_slot % len(SEED_SLOT_SCALARS)]
    for axis_name in _continuous_axes(obligation.dna):
        profile[axis_name] = scalar
    return profile


def shard_indices(
    shard_index: int,
    shard_count: int,
    seeds_per_obligation: int = DEFAULT_SEEDS_PER_OBLIGATION,
) -> range:
    if shard_count < 1:
        raise ValueError(f"shard_count={shard_count}; expected at least 1")
    if shard_index < 0 or shard_index >= shard_count:
        raise ValueError(
            f"shard_index={shard_index}; expected 0 <= shard_index < {shard_count}"
        )
    return range(shard_index, cache_key_count(seeds_per_obligation), shard_count)


def _first_base_indices_by_dimension() -> List[int]:
    """Fixed cross-family sentinels spanning all current nodes/DNAs/formatters."""
    selected: set[int] = set()
    seen_nodes: set[str] = set()
    seen_dnas: set[str] = set()
    seen_formatters: set[str] = set()
    for index, obligation in enumerate(_base_obligations()):
        if obligation.node_id not in seen_nodes:
            selected.add(index)
            seen_nodes.add(obligation.node_id)
        if obligation.dna not in seen_dnas:
            selected.add(index)
            seen_dnas.add(obligation.dna)
        if obligation.formatter not in seen_formatters:
            selected.add(index)
            seen_formatters.add(obligation.formatter)
    return sorted(selected)


def pr_sentinel_indices(
    seeds_per_obligation: int = DEFAULT_SEEDS_PER_OBLIGATION,
) -> List[int]:
    """One cache key per cross-family sentinel, rotated over interests/seed slots."""
    base_indices = _first_base_indices_by_dimension()
    interests = interest_request_values()
    selected = {
        encode_cache_index(
            base_index,
            ordinal % len(interests),
            ordinal % seeds_per_obligation,
            seeds_per_obligation,
        )
        for ordinal, base_index in enumerate(base_indices)
    }
    # Independently guarantee every interest request and continuous seed slot appears,
    # even if a future tree has fewer cross-family sentinels than either dimension.
    for interest_index in range(len(interests)):
        selected.add(encode_cache_index(
            base_indices[interest_index % len(base_indices)], interest_index,
            interest_index % seeds_per_obligation, seeds_per_obligation,
        ))
    for seed_slot in range(seeds_per_obligation):
        selected.add(encode_cache_index(
            base_indices[seed_slot % len(base_indices)],
            seed_slot % len(interests), seed_slot, seeds_per_obligation,
        ))
    return sorted(selected)


def representative_indices(
    sample_size: int,
    seeds_per_obligation: int = DEFAULT_SEEDS_PER_OBLIGATION,
) -> List[int]:
    """Deterministic 1,000-style sample covering all finite dimensions first."""
    total = cache_key_count(seeds_per_obligation)
    if sample_size < len(pr_sentinel_indices(seeds_per_obligation)):
        raise ValueError(
            f"sample_size={sample_size} is smaller than the "
            f"{len(pr_sentinel_indices(seeds_per_obligation))} required sentinels"
        )
    if sample_size > total:
        raise ValueError(f"sample_size={sample_size} exceeds {total} cache keys")
    selected = set(pr_sentinel_indices(seeds_per_obligation))
    if sample_size > 1:
        for ordinal in range(sample_size):
            selected.add(round(ordinal * (total - 1) / (sample_size - 1)))
            if len(selected) >= sample_size:
                break
    candidate = 0
    while len(selected) < sample_size:
        selected.add(candidate)
        candidate += 1
    return sorted(selected)[:sample_size]


def changed_base_indices(keys: Sequence[str]) -> List[int]:
    """Resolve exact base keys; an unknown key is a loud stale-manifest failure."""
    if not keys:
        return []
    wanted = set(keys)
    by_key = {obligation.key(): index for index, obligation in enumerate(_base_obligations())}
    unknown = sorted(wanted - set(by_key))
    if unknown:
        raise ValueError(
            f"{len(unknown)} changed obligation key(s) are absent from the current manifest: "
            f"{unknown[:5]}"
        )
    return sorted(by_key[key] for key in wanted)


def pr_indices(
    changed_keys: Sequence[str],
    seeds_per_obligation: int = DEFAULT_SEEDS_PER_OBLIGATION,
) -> List[int]:
    selected = set(pr_sentinel_indices(seeds_per_obligation))
    for base_index in changed_base_indices(changed_keys):
        for interest_index in range(len(interest_request_values())):
            for seed_slot in range(seeds_per_obligation):
                selected.add(encode_cache_index(
                    base_index, interest_index, seed_slot, seeds_per_obligation
                ))
    return sorted(selected)


def _rss_bytes() -> int:
    raw = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # Linux reports KiB; macOS reports bytes.
    return raw if sys.platform == "darwin" else raw * 1024


def _execute_cache_key(payload: Tuple[int, int]) -> CacheResult:
    cache_index, seeds_per_obligation = payload
    obligation, interest, seed_slot = decode_cache_index(
        cache_index, seeds_per_obligation
    )
    seed = stable_seed(obligation.key(), interest, seed_slot)
    profile = difficulty_profile_for(obligation, seed_slot)
    readable_key = (
        f"{obligation.key()}|interest={interest or '(automatic)'}|seed_slot={seed_slot}"
    )
    started = time.perf_counter()
    response_modes: set[str] = set()
    renderers: set[str] = set()
    try:
        from backend.app.practice_gen.adapter import apply_experience
        from backend.app.services.orchestrator import PracticeOrchestrator

        # Generate once at the exact production seam immediately before the experience
        # wrapper, then exercise every production wrapper on an independent deep copy.
        base_problem = PracticeOrchestrator.generate_problem(
            node_id=obligation.node_id,
            seed=seed,
            difficulty_profile=profile,
            interest_theme=interest,
            formatter=obligation.formatter,
            experience="standard",
            is_student_path=True,
            forced_dna=obligation.dna,
        )
        for experience in experience_values():
            problem = apply_experience(base_problem.model_copy(deep=True), experience, None)
            if problem.node_id != obligation.node_id:
                raise AssertionError(
                    f"served node={problem.node_id!r}, requested {obligation.node_id!r}"
                )
            if problem.dna_name != obligation.dna:
                raise AssertionError(
                    f"served DNA={problem.dna_name!r}, requested {obligation.dna!r}"
                )
            if problem.formatter_name != obligation.formatter:
                raise AssertionError(
                    f"served formatter={problem.formatter_name!r}, requested "
                    f"{obligation.formatter!r}"
                )
            if problem.experience != experience:
                raise AssertionError(
                    f"served experience={problem.experience!r}, requested {experience!r}"
                )
            response_modes.add(str(problem.answer_collection or "(missing)"))
            renderers.add(str(problem.visual_type or "(text)"))
        failure = None
    except Exception as exc:
        failure = ExecutionFailure(
            cache_index=cache_index,
            seed=seed,
            obligation_key=readable_key,
            exception_type=type(exc).__name__,
            message=str(exc),
        )
    return CacheResult(
        cache_index=cache_index,
        elapsed_seconds=time.perf_counter() - started,
        represented_executions=len(experience_values()),
        response_modes=tuple(sorted(response_modes)),
        renderers=tuple(sorted(renderers)),
        peak_rss_bytes=_rss_bytes(),
        failure=failure,
    )


def execute_indices(
    indices: Iterable[int],
    *,
    workers: int,
    seeds_per_obligation: int = DEFAULT_SEEDS_PER_OBLIGATION,
    progress_every: int = 0,
) -> Tuple[List[CacheResult], float]:
    """Execute a bounded work queue and stop submitting on the first failure.

    ``ProcessPoolExecutor.map`` eagerly queued a complete release shard and returned in
    input order. A slow early key therefore hid all later progress, and a failed key still
    allowed hours of unnecessary generation. At most ``workers * 2`` keys are now in
    flight, completions are observed as they happen, and release callers can publish
    periodic progress without weakening the final all-or-nothing receipt.
    """
    if workers < 1:
        raise ValueError(f"workers={workers}; expected at least 1")
    if progress_every < 0:
        raise ValueError(f"progress_every={progress_every}; expected at least 0")
    payloads = iter((index, seeds_per_obligation) for index in indices)
    started = time.perf_counter()
    results: List[CacheResult] = []

    def record(result: CacheResult) -> bool:
        results.append(result)
        if progress_every and len(results) % progress_every == 0:
            print(
                f"progress cache_keys={len(results)} elapsed="
                f"{time.perf_counter() - started:.3f}s",
                flush=True,
            )
        return result.failure is not None

    if workers == 1:
        for payload in payloads:
            if record(_execute_cache_key(payload)):
                break
    else:
        pool = ProcessPoolExecutor(max_workers=workers)
        stopped_early = False
        try:
            pending = set()
            for _ in range(workers * 2):
                try:
                    pending.add(pool.submit(_execute_cache_key, next(payloads)))
                except StopIteration:
                    break
            while pending:
                completed, pending = wait(pending, return_when=FIRST_COMPLETED)
                for future in completed:
                    if record(future.result()):
                        stopped_early = True
                        break
                    try:
                        pending.add(pool.submit(_execute_cache_key, next(payloads)))
                    except StopIteration:
                        pass
                if stopped_early:
                    for future in pending:
                        future.cancel()
                    break
        finally:
            pool.shutdown(wait=not stopped_early, cancel_futures=stopped_early)
    return sorted(results, key=lambda result: result.cache_index), time.perf_counter() - started


def _percentile(values: Sequence[float], quantile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    return ordered[math.ceil(quantile * len(ordered)) - 1]


def summarize_results(
    results: Sequence[CacheResult], elapsed_seconds: float,
) -> Dict[str, Any]:
    failures = [asdict(r.failure) for r in results if r.failure is not None]
    durations = [r.elapsed_seconds for r in results]
    return {
        "cache_keys_completed": len(results),
        "represented_executions": sum(r.represented_executions for r in results),
        "elapsed_seconds": elapsed_seconds,
        "worker_median_ms": statistics.median(durations) * 1000 if durations else 0.0,
        "worker_p95_ms": _percentile(durations, 0.95) * 1000,
        "peak_rss_bytes": max((r.peak_rss_bytes for r in results), default=0),
        "response_modes": sorted({mode for r in results for mode in r.response_modes}),
        "renderers": sorted({renderer for r in results for renderer in r.renderers}),
        "failures": failures,
    }


def benchmark(
    sample_size: int = 1000,
    workers: int = REFERENCE_WORKERS,
    seeds_per_obligation: int = DEFAULT_SEEDS_PER_OBLIGATION,
) -> Dict[str, Any]:
    indices = representative_indices(sample_size, seeds_per_obligation)
    results, elapsed = execute_indices(
        indices, workers=workers, seeds_per_obligation=seeds_per_obligation,
        progress_every=1000,
    )
    summary = summarize_results(results, elapsed)
    projected_release_seconds = (
        elapsed / len(indices) * cache_key_count(seeds_per_obligation)
    )
    recommended_shards = max(1, math.ceil(
        projected_release_seconds / TARGET_SHARD_SECONDS
    ))
    return {
        "schema_version": 1,
        "kind": "obligation_executor_benchmark",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python": sys.version,
        "workers": workers,
        "sample_size": sample_size,
        "seeds_per_obligation": seeds_per_obligation,
        "manifest_digest": base_manifest_digest(),
        "source_input_digest": source_input_digest(),
        "counts": {
            "base_obligations": len(_base_obligations()),
            "interest_requests": len(interest_request_values()),
            "experiences": len(experience_values()),
            "finite_obligations": finite_obligation_count(),
            "release_cache_keys": cache_key_count(seeds_per_obligation),
            "release_represented_executions": represented_execution_count(
                seeds_per_obligation
            ),
        },
        "measurement": summary,
        "projection": {
            "release_wall_seconds_at_measured_throughput": projected_release_seconds,
            "release_wall_hours_at_measured_throughput": projected_release_seconds / 3600,
            "recommended_shard_count": recommended_shards,
            "projected_seconds_per_shard": projected_release_seconds / recommended_shards,
        },
        "targets": {
            "pr_seconds": TARGET_PR_SECONDS,
            "release_shard_seconds": TARGET_SHARD_SECONDS,
            "release_total_seconds": TARGET_RELEASE_SECONDS,
            "release_projection_within_budget": (
                projected_release_seconds <= TARGET_RELEASE_SECONDS
            ),
            "shard_projection_within_budget": (
                projected_release_seconds / recommended_shards <= TARGET_SHARD_SECONDS
            ),
        },
        "cache": {
            "key": "base obligation + interest request + seed slot",
            "reuse": (
                "one generator/formatter execution is deep-copied through all four "
                "production experience wrappers"
            ),
        },
        "sample_indices_sha256": hashlib.sha256(
            json.dumps(indices, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }


def run_release_shard(
    shard_index: int,
    shard_count: int,
    *,
    workers: int = REFERENCE_WORKERS,
    seeds_per_obligation: int = DEFAULT_SEEDS_PER_OBLIGATION,
) -> Dict[str, Any]:
    indices = shard_indices(shard_index, shard_count, seeds_per_obligation)
    results, elapsed = execute_indices(
        indices,
        workers=workers,
        seeds_per_obligation=seeds_per_obligation,
        progress_every=1000,
    )
    summary = summarize_results(results, elapsed)
    return {
        "schema_version": 1,
        "kind": "obligation_executor_release_shard",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workers": workers,
        "seeds_per_obligation": seeds_per_obligation,
        "manifest_digest": base_manifest_digest(),
        "source_input_digest": source_input_digest(),
        "sharding": {
            "algorithm": "cache_index modulo shard_count",
            "shard_index": shard_index,
            "shard_count": shard_count,
            "first_cache_index": indices.start,
            "stride": indices.step,
            "expected_cache_keys": len(indices),
            "total_cache_keys": cache_key_count(seeds_per_obligation),
        },
        "measurement": summary,
    }


def release_receipt_findings(
    receipt_dir: Path = RELEASE_RECEIPT_DIR,
) -> Tuple[List[str], Dict[str, Any]]:
    """Verify complete, current, non-overlapping release-shard receipts.

    Absence and incompleteness are both blocking findings: a missing run may never look
    like a passing release, and a half-run may never look like a smaller green release.
    The modulo partition lets completeness and overlap be checked from counts and shard
    identities without serializing 579,555 integer indices into the receipts.
    """
    paths = sorted(receipt_dir.glob("shard_*_of_*.json")) if receipt_dir.exists() else []
    if not paths:
        return [
            "no release shard receipts exist; the complete finite sweep is uncertified"
        ], {
            "status": "not_run",
            "complete": False,
            "receipts": 0,
            "message": "no release shard receipts exist; the PR tier is partial",
        }

    findings: List[str] = []
    receipts: List[Dict[str, Any]] = []
    for path in paths:
        try:
            receipts.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(f"{path.name}: unreadable receipt: {exc}")
    if not receipts:
        return findings, {"status": "invalid", "complete": False, "receipts": 0}

    first = receipts[0]
    shard_count = first.get("sharding", {}).get("shard_count")
    seeds = first.get("seeds_per_obligation")
    if not isinstance(shard_count, int) or shard_count < 1:
        findings.append(f"invalid shard_count={shard_count!r}")
        shard_count = 1
    if not isinstance(seeds, int):
        findings.append(f"invalid seeds_per_obligation={seeds!r}")
        seeds = DEFAULT_SEEDS_PER_OBLIGATION

    expected_manifest = base_manifest_digest()
    expected_source = source_input_digest()
    expected_total = cache_key_count(seeds)
    expected_indices = set(range(shard_count))
    seen_indices: List[int] = []
    completed_cache_keys = 0
    represented_executions = 0
    elapsed_seconds = 0.0

    for receipt in receipts:
        sharding = receipt.get("sharding", {})
        measurement = receipt.get("measurement", {})
        index = sharding.get("shard_index")
        if receipt.get("schema_version") != 1:
            findings.append(f"shard {index}: unsupported schema_version")
        if receipt.get("kind") != "obligation_executor_release_shard":
            findings.append(f"shard {index}: wrong receipt kind")
        if receipt.get("manifest_digest") != expected_manifest:
            findings.append(f"shard {index}: manifest digest is stale")
        if receipt.get("source_input_digest") != expected_source:
            findings.append(f"shard {index}: source/input digest is stale")
        if receipt.get("seeds_per_obligation") != seeds:
            findings.append(f"shard {index}: seeds_per_obligation disagrees")
        if sharding.get("shard_count") != shard_count:
            findings.append(f"shard {index}: shard_count disagrees")
        if not isinstance(index, int):
            findings.append(f"receipt has invalid shard_index={index!r}")
            continue
        seen_indices.append(index)
        expected_shard_keys = len(shard_indices(index, shard_count, seeds)) \
            if 0 <= index < shard_count else -1
        if sharding.get("expected_cache_keys") != expected_shard_keys:
            findings.append(f"shard {index}: expected-cache-key count disagrees")
        if measurement.get("cache_keys_completed") != expected_shard_keys:
            findings.append(f"shard {index}: incomplete cache-key execution")
        expected_executions = expected_shard_keys * len(experience_values())
        if measurement.get("represented_executions") != expected_executions:
            findings.append(f"shard {index}: represented-execution count disagrees")
        if measurement.get("failures"):
            findings.append(
                f"shard {index}: {len(measurement['failures'])} execution failure(s)"
            )
        elapsed = measurement.get("elapsed_seconds")
        if not isinstance(elapsed, (int, float)) or elapsed < 0:
            findings.append(f"shard {index}: invalid elapsed_seconds={elapsed!r}")
        elif elapsed > TARGET_SHARD_SECONDS:
            findings.append(
                f"shard {index}: {elapsed:.3f}s exceeds {TARGET_SHARD_SECONDS}s target"
            )
        completed_cache_keys += measurement.get("cache_keys_completed", 0) \
            if isinstance(measurement.get("cache_keys_completed"), int) else 0
        represented_executions += measurement.get("represented_executions", 0) \
            if isinstance(measurement.get("represented_executions"), int) else 0
        elapsed_seconds += elapsed if isinstance(elapsed, (int, float)) else 0.0

    if set(seen_indices) != expected_indices or len(seen_indices) != len(set(seen_indices)):
        findings.append(
            f"shard identities are incomplete or overlap: expected "
            f"{sorted(expected_indices)}, got {sorted(seen_indices)}"
        )
    if completed_cache_keys != expected_total:
        findings.append(
            f"shard union covers {completed_cache_keys} cache keys, expected {expected_total}"
        )
    expected_executions = represented_execution_count(seeds)
    if represented_executions != expected_executions:
        findings.append(
            f"shard union represents {represented_executions} executions, expected "
            f"{expected_executions}"
        )
    if elapsed_seconds > TARGET_RELEASE_SECONDS:
        findings.append(
            f"release shards total {elapsed_seconds:.3f}s, above "
            f"{TARGET_RELEASE_SECONDS}s target"
        )

    return findings, {
        "status": "complete" if not findings else "invalid",
        "complete": not findings,
        "receipts": len(receipts),
        "shard_count": shard_count,
        "cache_keys": completed_cache_keys,
        "represented_executions": represented_executions,
        "elapsed_seconds": elapsed_seconds,
    }


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _print_summary(payload: Dict[str, Any]) -> None:
    measurement = payload["measurement"]
    print(
        f"cache_keys={measurement['cache_keys_completed']} "
        f"represented_executions={measurement['represented_executions']} "
        f"elapsed={measurement['elapsed_seconds']:.3f}s "
        f"median={measurement['worker_median_ms']:.3f}ms "
        f"p95={measurement['worker_p95_ms']:.3f}ms "
        f"peak_rss={measurement['peak_rss_bytes']}B "
        f"failures={len(measurement['failures'])}"
    )
    for failure in measurement["failures"][:20]:
        print(
            f"FAIL obligation_execution_11: index={failure['cache_index']} "
            f"seed={failure['seed']} key={failure['obligation_key']} "
            f"{failure['exception_type']}: {failure['message']}"
        )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tier", choices=("benchmark", "pr", "release", "verify-release"), required=True
    )
    parser.add_argument("--workers", type=int, default=REFERENCE_WORKERS)
    parser.add_argument("--seeds-per-obligation", type=int,
                        default=DEFAULT_SEEDS_PER_OBLIGATION)
    parser.add_argument("--sample-size", type=int, default=1000)
    parser.add_argument("--shard-count", type=int)
    parser.add_argument("--shard-index", type=int)
    parser.add_argument("--changed-obligation-key", action="append", default=[])
    args = parser.parse_args(argv)

    if args.tier == "benchmark":
        payload = benchmark(args.sample_size, args.workers, args.seeds_per_obligation)
        _write_json(BENCHMARK_PATH, payload)
        _print_summary(payload)
        projection = payload["projection"]
        print(
            f"projected_release={projection['release_wall_hours_at_measured_throughput']:.3f}h "
            f"recommended_shards={projection['recommended_shard_count']} "
            f"projected_per_shard={projection['projected_seconds_per_shard'] / 60:.3f}m"
        )
        print(f"wrote {BENCHMARK_PATH.relative_to(REPO_ROOT)}")
    elif args.tier == "pr":
        indices = pr_indices(args.changed_obligation_key, args.seeds_per_obligation)
        results, elapsed = execute_indices(
            indices, workers=args.workers,
            seeds_per_obligation=args.seeds_per_obligation,
        )
        payload = {
            "kind": "obligation_executor_pr_partial",
            "partial": True,
            "changed_base_obligations": len(changed_base_indices(
                args.changed_obligation_key
            )),
            "fixed_sentinels": len(pr_sentinel_indices(args.seeds_per_obligation)),
            "measurement": summarize_results(results, elapsed),
        }
        _print_summary(payload)
        print("PARTIAL PR TIER: fixed sentinels plus every explicitly changed obligation")
    elif args.tier == "release":
        if args.shard_count is None or args.shard_index is None:
            parser.error("--tier release requires --shard-count and --shard-index")
        payload = run_release_shard(
            args.shard_index, args.shard_count, workers=args.workers,
            seeds_per_obligation=args.seeds_per_obligation,
        )
        path = RELEASE_RECEIPT_DIR / (
            f"shard_{args.shard_index:03d}_of_{args.shard_count:03d}.json"
        )
        _write_json(path, payload)
        _print_summary(payload)
        print(f"wrote {path.relative_to(REPO_ROOT)}")

    else:
        findings, summary = release_receipt_findings()
        if findings:
            for finding in findings:
                print(f"FAIL obligation_release_shards_11: {finding}")
        else:
            print(
                f"release_status={summary['status']} receipts={summary['receipts']} "
                f"complete={summary['complete']}"
            )
        return 1 if findings or not summary["complete"] else 0

    return 1 if payload["measurement"]["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
