"""Tests for the axes-catalog logarithmic scale and the auditor's
``build_test_profiles`` variant-coverage guarantee (Phase 1C).

Two regression targets:

1. Every ``continuous`` axis whose range spans ≥ 10× (``default_max /
   default_min >= 10``) must declare ``scale: 'logarithmic'`` so the
   orchestrator can map the 0.5 scalar to the geometric mean of the
   range (not the arithmetic mean). Without this, the mid-difficulty
   point is off-grade for K-12 ranges that span orders of magnitude
   (e.g. ordinal 1–100, value_max 5–50).

2. ``build_test_profiles`` in the auditor must fail fast if any
   config-declared contextual-variant option is missing from the
   returned profiles. AGENTS.md rule #4 forbids silent skipping; the
   guarantee here is that the profile builder either produces a
   profile containing each option or raises immediately.
"""
from __future__ import annotations

import math
import os
import sys

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, _REPO_ROOT)

from backend.app.practice_gen.axes_catalog import (  # noqa: E402
    CONCEPT_AXES_CATALOG,
    compute_difficulty_scalar,
)


# ─── axes_catalog.py: scale field is present on every wide-range axis ──────


def _continuous_axes_with_default_range():
    """Yield (concept, axis) for every continuous axis that has both
    default_min and default_max set."""
    for concept, axes in CONCEPT_AXES_CATALOG.items():
        for axis in axes:
            if axis.get("dim_type") == "continuous" and "default_min" in axis and "default_max" in axis:
                yield concept, axis


class TestLogScaleDeclarations:
    """Every continuous axis whose range spans >= 10x must declare
    ``scale: 'logarithmic'``."""

    @pytest.mark.parametrize("concept,axis", list(_continuous_axes_with_default_range()))
    def test_wide_range_axis_declares_logarithmic_scale(self, concept, axis):
        mn = axis["default_min"]
        mx = axis["default_max"]
        # 0.0..1.0 number_difficulty axes span 0/0 — skip them.
        if not mn or mn == 0:
            return
        ratio = mx / mn
        if ratio >= 10:
            assert axis.get("scale") == "logarithmic", (
                f"{concept}.{axis['name']} has range {mn}..{mx} "
                f"(ratio={ratio:.1f}) but is missing scale='logarithmic'"
            )

    def test_pictographs_value_max_declares_logarithmic(self):
        # Targeted regression: value_max (5, 50) in pictographs was
        # missing the scale field before Phase 1C.
        axis = next(a for a in CONCEPT_AXES_CATALOG["pictographs"] if a["name"] == "value_max")
        assert axis.get("scale") == "logarithmic"
        assert axis["default_min"] == 5
        assert axis["default_max"] == 50

    def test_comparing_ordering_value_max_declares_logarithmic(self):
        # Phase 1C added a value_max (5, 50) axis to comparing_ordering
        # specifically for K-1/G1 pictograph-style comparing tasks.
        axis = next(
            (a for a in CONCEPT_AXES_CATALOG["comparing_ordering"] if a["name"] == "value_max"),
            None,
        )
        assert axis is not None, "comparing_ordering is missing a value_max axis"
        assert axis.get("scale") == "logarithmic"
        assert axis["default_min"] == 5
        assert axis["default_max"] == 50


# ─── axes_catalog.py: compute_difficulty_scalar honors the scale field ──────


class TestComputeDifficultyScalarLogMapping:
    """When ``scale == 'logarithmic'``, scalar 0.5 must map to the
    geometric mean of the range, and the function must round-trip
    (feed-back) cleanly at every milestone."""

    def test_scalar_0p5_maps_to_geometric_mean_for_5_to_50(self):
        # pictographs.value_max: min=5, max=50, scale=logarithmic
        gm = math.sqrt(5 * 50)
        recovered = compute_difficulty_scalar(
            "pictographs", {"value_max": gm}
        )
        assert recovered == pytest.approx(0.5, abs=1e-6), (
            f"Expected scalar ~0.5 at geometric mean {gm}, got {recovered}"
        )

    def test_scalar_round_trip_at_endpoints_and_midpoints(self):
        log_min = math.log10(5)
        log_max = math.log10(50)
        for s in [0.0, 0.25, 0.5, 0.75, 1.0]:
            val = 10 ** (log_min + s * (log_max - log_min))
            recovered = compute_difficulty_scalar(
                "pictographs", {"value_max": val}
            )
            assert recovered == pytest.approx(s, abs=1e-6), (
                f"Round-trip mismatch at s={s}: val={val:.4f}, recovered={recovered}"
            )

    def test_scalar_0p5_maps_to_geometric_mean_for_ordinal_1_to_100(self):
        # ordinal_numbers.ordinal_range: min=1, max=100, scale=logarithmic
        gm = math.sqrt(1 * 100)  # = 10
        recovered = compute_difficulty_scalar(
            "ordinal_numbers", {"ordinal_range": gm}
        )
        assert recovered == pytest.approx(0.5, abs=1e-6), (
            f"Expected scalar ~0.5 at geometric mean 10, got {recovered}"
        )

    def test_linear_scale_axis_still_maps_arithmetically(self):
        # number_difficulty axes (0.0..1.0) have no scale field and no
        # range, so the linear mapping must remain unchanged.
        # Use an axis that has a number_difficulty (e.g. addition).
        assert compute_difficulty_scalar(
            "addition", {"number_difficulty": 0.5}
        ) == pytest.approx(0.5, abs=1e-6)
        assert compute_difficulty_scalar(
            "addition", {"number_difficulty": 0.0}
        ) == pytest.approx(0.0, abs=1e-6)
        assert compute_difficulty_scalar(
            "addition", {"number_difficulty": 1.0}
        ) == pytest.approx(1.0, abs=1e-6)


# ─── exhaustive_checklist_auditor.py: build_test_profiles variant coverage ──


class TestBuildTestProfilesVariantCoverage:
    """``build_test_profiles`` must include every config-declared
    contextual-variant option in the returned profiles. If any option
    is missing, it must raise (per AGENTS.md rule #4, no silent
    skipping)."""

    def _build_profiles(self, config, supported_variants=None):
        # Import here so harness-level import errors surface only when
        # the test is actually executed.
        from tests.exhaustive_checklist_auditor import (
            build_test_profiles,
        )
        return build_test_profiles(config, supported_variants or {})

    def test_every_variant_option_appears(self):
        config = {
            "difficulty_dimensions": [],
            "contextual_variants": [
                {
                    "name": "task_type",
                    "options": ["find_sum", "find_addend", "compare"],
                },
                {
                    "name": "representation",
                    "options": ["concrete", "abstract", "pictorial"],
                },
            ],
        }
        profiles = self._build_profiles(config)
        present_task_types = {p.get("task_type") for p in profiles}
        present_reps = {p.get("representation") for p in profiles}
        assert present_task_types >= {"find_sum", "find_addend", "compare"}
        assert present_reps >= {"concrete", "abstract", "pictorial"}

    def test_supported_variants_filter_narrows_coverage(self):
        # When the formatter's supported_variants filter passes through
        # only a subset of declared options, the returned profiles must
        # include exactly the surviving set — never silently less. The
        # filter is an explicit, documented step (AGENTS.md rule #4
        # allows this kind of explicit filter; it is the OPPOSITE of
        # silent defaulting).
        config = {
            "difficulty_dimensions": [],
            "contextual_variants": [
                {
                    "name": "task_type",
                    "options": ["find_sum", "find_addend", "compare"],
                },
            ],
        }
        supported_variants = {"task_type": ["find_sum"]}
        profiles = self._build_profiles(config, supported_variants)
        present = {p.get("task_type") for p in profiles}
        assert present == {"find_sum"}

    def test_filter_that_drops_everything_produces_no_profiles_for_that_variant(self):
        # If the supported_variants filter is restrictive enough to
        # drop every option, the function emits no profiles for that
        # variant and does NOT raise (the filter is explicit intent).
        config = {
            "difficulty_dimensions": [],
            "contextual_variants": [
                {
                    "name": "task_type",
                    "options": ["find_sum", "find_addend", "compare"],
                },
            ],
        }
        supported_variants = {"task_type": ["unrelated_value"]}
        # Should NOT raise — the explicit filter is permitted.
        profiles = self._build_profiles(config, supported_variants)
        # No profile contains any task_type value.
        for p in profiles:
            assert "task_type" not in p

    def test_sample_node_variant_coverage(self):
        # End-to-end against a real node config (mat_g1_na_q1_8 is the
        # canonical K-1 addition node from the project fixtures). The
        # test mirrors the auditor's own per-formatter supported_variants
        # union: it iterates the node's formatters and unions the
        # variant caps across the node's DNAs.
        from tests.exhaustive_checklist_auditor import (
            build_test_profiles,
        )
        from backend.app.practice_gen.compatibility import (
            get_formatters_for_dna,
            get_supported_variants,
        )
        from backend.app.practice_gen.registry import (
            get_node_dnas,
        )
        from backend.app.routes.matatag_router import (
            get_matatag_lab_config,
        )

        node_id = "mat_g1_na_q1_8"
        config = get_matatag_lab_config(node_id)
        dnas = get_node_dnas(node_id)

        # Build a supported_variants union across the node's DNAs AND
        # the formatters they accept (matches the auditor main loop at
        # lines 384-393 of exhaustive_checklist_auditor.py).
        formatters = set()
        for d in dnas:
            formatters.update(get_formatters_for_dna(d))
        sv_union: dict = {}
        for fmt in formatters:
            for d in dnas:
                if fmt in get_formatters_for_dna(d):
                    sv_for_d = get_supported_variants(d, fmt) or {}
                    for k, v in sv_for_d.items():
                        sv_union.setdefault(k, set()).update(v)
        supported_variants = {k: sorted(v) for k, v in sv_union.items()}

        # Should not raise — the addition node's declared task_type
        # options are find_sum, find_addend (compare is not in
        # supported_variants for any addition formatter).
        profiles = build_test_profiles(config, supported_variants)
        assert profiles, "build_test_profiles returned no profiles"

        # Every option that survived the supported_variants filter
        # must appear in the returned profiles.
        for variant in config.get("contextual_variants", []):
            name = variant["name"]
            declared = list(variant.get("options", []))
            if name in supported_variants:
                declared = [v for v in declared if v in supported_variants[name]]
            present = {p.get(name) for p in profiles}
            missing = [v for v in declared if v not in present]
            assert not missing, (
                f"Node {node_id}: contextual variant '{name}' is missing "
                f"options {missing} from the returned profiles."
            )
