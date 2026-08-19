"""
Mutation tests for the capability contract (§6A/§6B/§6C).

These exist because green is not evidence. Phase 4 of pgen_hardening.md was recorded
as done for weeks and scored 4/7 the first time it was honestly executed, so every
check here is proved by planting the exact violation it claims to catch.

The load-bearing case is `test_omission_survives_provenance_but_not_coverage`. §6A
alone is not enough: an agent whose pipeline cannot render "draw" could simply omit
the draw requirement, and §6C (required ⊆ provided) would then pass trivially. Only
§6B coverage closes that, and this test pins the division of labour so a future
refactor cannot quietly drop it.
"""

from backend.app.practice_gen.validation import validate_capability as VC

COMPETENCY = "Recognize and draw parallel, intersecting, and perpendicular lines."

HONEST = [
    {"kind": "task", "id": "recognize_lines", "clause": "Recognize"},
    {"kind": "task", "id": "draw_lines", "clause": "draw"},
    {"kind": "object", "id": "parallel_lines", "clause": "parallel"},
    {"kind": "object", "id": "intersecting_lines", "clause": "intersecting"},
    {"kind": "object", "id": "perpendicular_lines", "clause": "perpendicular lines"},
]


def test_honest_declaration_passes_provenance_and_coverage():
    assert VC._validate_provenance("N", COMPETENCY, HONEST) == []
    assert VC._validate_coverage("N", COMPETENCY, HONEST, []) == []


def test_invention_is_caught_by_provenance():
    """A requirement the curriculum never states cannot be declared."""
    invented = HONEST + [
        {"kind": "task", "id": "estimate_angle", "clause": "estimate the angle"}
    ]
    errs = VC._validate_provenance("N", COMPETENCY, invented)
    assert any("estimate_angle" in e and "does not appear" in e for e in errs), errs


def test_omission_survives_provenance_but_not_coverage():
    """
    The loophole this whole design would otherwise have: drop the requirement you
    cannot satisfy, and required ⊆ provided passes vacuously.
    """
    omitted = [r for r in HONEST if r["id"] != "draw_lines"]

    # Provenance cannot see an omission -- everything still cited is genuine.
    assert VC._validate_provenance("N", COMPETENCY, omitted) == []

    # Coverage does, by name.
    errs = VC._validate_coverage("N", COMPETENCY, omitted, [])
    assert any("'draw'" in e or "draw" in e for e in errs), errs


def test_requires_ignore_must_be_explicit_to_excuse_a_word():
    """Ignoring a competency word is possible but visible -- never a silent default."""
    omitted = [r for r in HONEST if r["id"] != "draw_lines"]
    assert VC._validate_coverage("N", COMPETENCY, omitted, []) != []
    assert VC._validate_coverage("N", COMPETENCY, omitted, ["draw"]) == []


def test_missing_clause_is_an_error_not_a_skip():
    no_clause = [{"kind": "task", "id": "draw_lines"}]
    errs = VC._validate_provenance("N", COMPETENCY, no_clause)
    assert any("no 'clause'" in e for e in errs), errs


def test_unprovided_capability_names_the_node_and_the_clause():
    """
    The acceptance test for the entire capability contract: mat_g3_mg_q1_5's
    competency says "draw" and nothing in the pipeline draws, so the harness must
    say so itself rather than leaving it to a reviewer's judgment.

    RESTORED 2026-08-19 (hardening Unit 1). Between bc2f8e29 and cc5977f5 this was
    rewritten onto a synthetic capability id ("draw_unprovided_lines") passed
    directly to the private _validate_provision. That form is absent from
    CAPABILITY_PROVIDERS by construction, so it passes for any table whatsoever and
    stopped describing the system (Rule 3). The real declaration, through the public
    entry point, is the acceptance test.
    """
    errs = VC.validate_capability_declarations(["mat_g3_mg_q1_5"])
    draw = [e for e in errs if "draw_line" in e]
    assert draw, f"expected an unprovided-capability failure for draw_lines, got {errs}"
    assert "mat_g3_mg_q1_5" in draw[0]
    assert "no pipeline artifact provides it" in draw[0]


# --- §6D: a generic textual formatter is not a provider -----------------------

def test_generic_textual_formatter_is_not_a_provider():
    """
    The mechanical form of Rule 9, planted and proved (Rule 11).

    In August 2026 `run_all` reached exit 0 with 474 of 485 CAPABILITY_PROVIDERS
    entries listing mcq/cloze/true_false/error_detect among their providers. 27 of 28
    DNAs offer at least one, so the generic name satisfied the clause on almost every
    node and the specific artifact beside it was decoration. Not one assertion was
    weakened -- §6C simply answered "yes" to every question it was asked.

    This plants that exact shape on a capability that currently passes on a real,
    discriminating provider, and requires §6D to catch it BY NAME.
    """
    import copy

    target, node = "count_forward_from_a_given_number", "mat_g1_na_q1_0"
    original = copy.deepcopy(VC.CAPABILITY_PROVIDERS)
    try:
        # Scoped to §6D findings on purpose. This test's claim is about §6D's
        # discrimination, and §6F independently reports the same capability as
        # UNATTESTED until an Attester rules on it. Letting an unrelated §6F finding
        # fail a §6D test would couple the two checks and make either one impossible
        # to change alone. The §6D claim itself is unchanged and unweakened.
        baseline = [e for e in VC.validate_capability_declarations([node])
                    if target in e and "§6D" in e]
        assert not baseline, (
            f"{target} is expected to pass §6D on its real provider before mutation; "
            f"got {baseline}"
        )

        VC.CAPABILITY_PROVIDERS[target] = {"formatters": ["mcq", "cloze"]}
        errs = VC.validate_capability_declarations([node])
        caught = [e for e in errs if "§6D" in e and target in e]
        assert caught, f"MUTATION SURVIVED: a wildcard provider was not caught. got {errs}"
        assert node in caught[0]
        assert "no pipeline artifact provides it" in caught[0]
    finally:
        VC.CAPABILITY_PROVIDERS.clear()
        VC.CAPABILITY_PROVIDERS.update(original)

    assert not [e for e in VC.validate_capability_declarations([node])
                if target in e and "§6D" in e], (
        "the mutation was not cleanly reverted — §6D still fires on the restored entry"
    )


def test_generic_formatter_does_not_mask_a_specific_one():
    """
    The discrimination must key on *what survives removing the family*, never on how
    the entry looks. 392 of the 474 wildcard entries mixed a generic name in beside a
    specific one, so a check asking "is this entry only generic?" catches 82 of 474.

    A specific, reachable provider standing beside a generic name is still a provider:
    §6D must stay silent here or it would flag 392 entries it has no business touching.
    """
    import copy

    target, node = "count_forward_from_a_given_number", "mat_g1_na_q1_0"
    original = copy.deepcopy(VC.CAPABILITY_PROVIDERS)
    try:
        # The real entry is exactly this mixed shape: a reachable variant + 'mcq'.
        # (Fixture repointed 2026-08-19 when draw_line_relationships was DELETED on an
        # Attester NOT_PROVIDED ruling. The claim under test is unchanged; only the
        # subject moved, because the old subject no longer exists.)
        spec = VC.CAPABILITY_PROVIDERS[target]
        assert "mcq" in spec.get("formatters", []), "fixture assumes the mixed shape"
        assert spec.get("variants"), "fixture assumes a specific provider is present"

        # Scoped to §6D for the same reason as above: §6F's UNATTESTED finding on this
        # capability is a separate, legitimate report, not a §6D false positive.
        errs = [e for e in VC.validate_capability_declarations([node])
                if target in e and "§6D" in e]
        assert not errs, f"§6D fired on an entry with a real specific provider: {errs}"
    finally:
        VC.CAPABILITY_PROVIDERS.clear()
        VC.CAPABILITY_PROVIDERS.update(original)


def test_bounds_length_is_never_the_discriminator():
    """
    Guards against the decoy that cost an earlier audit a day.

    483 of 485 providers carry an identical 27-entry `bounds` catch-all, and that audit
    named it as the mechanism defeating §6C. It was not: measured *before* §6D existed,
    deleting `bounds` from every provider moved the failure count 0 -> 0, because the
    generic formatter family was satisfying everything first. A check thresholding on
    bounds length would have flagged 483 harmless entries and caught zero real ones.

    (With §6D active the family no longer satisfies, so `bounds` does become load-bearing
    for the ~15 capabilities that leaned on both -- stripping it now moves the count
    further. That is the contract working, not the decoy returning. What must never
    happen is §6D keying on how *long* a bounds list is, which is what this pins:
    padding a list with keys the node's competency bounds do not contain changes
    nothing, in either direction.)
    """
    import copy
    import re

    def _identities():
        """(node, capability) pairs §6D flagged -- not the message text, which echoes
        the spec and therefore changes when the spec is padded."""
        return {
            m.groups()
            for e in VC.validate_capability_declarations()
            if "§6D" in e
            for m in [re.match(r"^(\S+): competency requires '([^']+)'", e)]
            if m
        }

    JUNK = [f"junk_bound_{i}" for i in range(100)]
    original = copy.deepcopy(VC.CAPABILITY_PROVIDERS)
    try:
        flagged = _identities()
        assert flagged, "fixture expects at least one §6D finding to pad"

        for spec in VC.CAPABILITY_PROVIDERS.values():
            spec["bounds"] = list(spec.get("bounds") or []) + JUNK
        padded = _identities()
    finally:
        VC.CAPABILITY_PROVIDERS.clear()
        VC.CAPABILITY_PROVIDERS.update(original)

    assert padded == flagged, (
        f"§6D's verdict moved when every bounds list was padded with 100 keys no node "
        f"declares ({len(flagged)} -> {len(padded)} findings; symmetric difference "
        f"{sorted(padded ^ flagged)[:5]}). The check is reading the shape of the bounds "
        f"list rather than what actually provides the capability."
    )


# --- §6F: a claim nobody blind has checked is not evidence --------------------

def test_contradicted_entry_is_caught_by_name():
    """
    The regression §6F exists to stop: someone re-registers what a blind Attester
    already rejected.

    On 2026-08-19 an Attester ruled `draw_line_relationships` NOT_PROVIDED from ten
    rendered samples, without knowing the entry existed. The entry was deleted by hand.
    Nothing prevented it coming back — the verdict sat in validation_reports/attestation/
    and no validator read it, so the ruling took effect only if the Fixer chose to act
    on it. That is the same author-verifying-itself structure the Attester was
    introduced to break.
    """
    import copy

    node, cap = "mat_g3_mg_q1_5", "draw_line_relationships"
    original = copy.deepcopy(VC.CAPABILITY_PROVIDERS)
    try:
        assert not [e for e in VC.validate_capability_declarations([node]) if "CONTRADICTED" in e], (
            "fixture expects the rejected entry to be absent before the mutation"
        )
        VC.CAPABILITY_PROVIDERS[cap] = {"variants": [("task_type", "draw_construct")]}
        errs = [e for e in VC.validate_capability_declarations([node]) if "CONTRADICTED" in e]
        assert errs, "re-registering an Attester-rejected capability was not caught"
        assert cap in errs[0] and node in errs[0]
        assert "NOT_PROVIDED" in errs[0], "the failure must quote the verdict it contradicts"
    finally:
        VC.CAPABILITY_PROVIDERS.clear()
        VC.CAPABILITY_PROVIDERS.update(original)


def test_unattested_capability_is_a_failure_not_a_skip():
    """
    An unexamined claim is not a passing claim. `if not attested: continue` is precisely
    the bug that let 94 non-PASS judgment reviews escape every content check.
    """
    errs = VC.validate_capability_declarations(["mat_g1_mg_q4_0"])
    unattested = [e for e in errs if "UNATTESTED" in e]
    assert unattested, "a node with no filed Attester verdicts reported none unattested"
    assert "no blind Attester has judged" in unattested[0]


def test_attested_capability_is_not_reported_unattested():
    """§6F must clear once a verdict is on file, or it is a counter rather than a check."""
    errs = VC.validate_capability_declarations(["mat_g3_mg_q1_5"])
    unattested = [e for e in errs if "UNATTESTED" in e]
    for cap in ("recognize_line_relationships", "parallel_lines",
                "intersecting_lines", "perpendicular_lines"):
        assert not any(cap in e for e in unattested), (
            f"{cap} has a filed PROVIDED verdict but is still reported UNATTESTED"
        )


def test_attestation_verdict_must_be_binary():
    """There is no 'partly provided'. A malformed record is loud, never skipped."""
    import json as _json

    bad = VC._ATTESTATION_DIR / "_tmp_invalid_for_test.json"
    bad.write_text(_json.dumps({"verdicts": [
        {"node_id": "n", "capability_id": "c", "verdict": "PARTLY"}]}), encoding="utf-8")
    try:
        raised = False
        try:
            VC._load_attestations()
        except ValueError as exc:
            raised = "PROVIDED or " in str(exc)
        assert raised, "a non-binary verdict was accepted"
    finally:
        bad.unlink(missing_ok=True)


def test_attestation_goes_stale_when_content_drifts():
    """
    An attestation is evidence about specific rendered content and stops being evidence
    the moment that content changes. Without this, the contract has a permanent hole:
    attest everything once, then change generators freely, and run_all keeps exiting 0
    on evidence about content that no longer exists.

    §5 has enforced the same rule for judgment reviews since the fabrication incident.
    """
    import json as _json
    from pathlib import Path

    rec = next(Path(VC._ATTESTATION_DIR).glob("*.json"))
    original = rec.read_text(encoding="utf-8")
    try:
        d = _json.loads(original)
        node = d["packet"]["node_id"]
        d["packet"]["samples_judged"][0]["question_text"] = "a stem the pipeline never rendered"
        rec.write_text(_json.dumps(d), encoding="utf-8")

        errs = [e for e in VC.validate_capability_declarations([node]) if "STALE" in e]
        assert errs, "FRESHNESS HOLE: an attestation about drifted content was accepted"
        assert "re-attest" in errs[0]
    finally:
        rec.write_text(original, encoding="utf-8")

    assert not [e for e in VC.validate_capability_declarations([node]) if "STALE" in e]


def test_attestation_without_samples_cannot_be_checked_and_fails():
    """A record that cannot be re-rendered is not evidence — and is never silently skipped."""
    import json as _json
    from pathlib import Path

    rec = next(Path(VC._ATTESTATION_DIR).glob("*.json"))
    original = rec.read_text(encoding="utf-8")
    try:
        d = _json.loads(original)
        node = d["packet"]["node_id"]
        d["packet"].pop("samples_judged")
        rec.write_text(_json.dumps(d), encoding="utf-8")
        errs = [e for e in VC.validate_capability_declarations([node])
                if "cannot be checked for staleness" in e]
        assert errs, "an unverifiable attestation was accepted"
    finally:
        rec.write_text(original, encoding="utf-8")


# --- §1A-reach: the payload scanner must not measure its own input ------------

def test_reach_scanner_excludes_the_echoed_difficulty_profile():
    """
    `given_values` echoes the request's difficulty profile alongside real operands.
    Scanning the echo made §1A-reach measure its own input: a "sums up to 20" node
    echoes `max_sum: 20`, so the check saw a peak of 20 and reported the ceiling
    reached while no generated value ever exceeded 19.

    This is the same false-green the 2026-07-26 audit fixed in §1A/§1B ("only ever
    compared the echoed difficulty_profile value, never the numbers the DNA actually
    generated"), which had survived in this sibling helper.
    """
    from backend.app.practice_gen.validation.validate_matrix import (
        _numeric_payload_values,
        _profile_echo_keys,
    )

    problem = {
        "given_values": {"a": 9, "b": 10, "max_sum": 20, "context": "pure"},
        "correct_answer": 19,
    }
    labels = {lbl for lbl, _ in _numeric_payload_values(problem)}
    values = {v for _, v in _numeric_payload_values(problem)}

    assert "given_values.max_sum" not in labels, "the echoed bound is being measured as content"
    assert 20.0 not in values, "peak reflects the echoed ceiling, not generated content"
    assert labels == {"given_values.a", "given_values.b", "correct_answer"}
    assert max(values) == 19.0

    # Derived from the registries, not hand-listed, so a new axis cannot reintroduce it.
    assert "max_sum" in _profile_echo_keys()
    assert "context" in _profile_echo_keys()
