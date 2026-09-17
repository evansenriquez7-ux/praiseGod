#!/usr/bin/env python3
"""
Context semantics inventory — §1L (plan step 3A), milestone M1.

WHAT THIS IS, AND WHAT IT IS EMPHATICALLY NOT
----------------------------------------------
This module is **NONBINDING**. It gates nothing. `§1L` is deliberately absent from
`CONTRACT_CHECKS`, from `_manifest.CHECK_PHASE` and from `docs/pgen_contract.md`, because
plan step 3A forbids adding a §1L contract row while the live baseline is red — and this
module's whole purpose is to MEASURE how red that baseline is. Adding the row first is the
Mandate 5 hazard (a gate whose baseline is already red cannot be distinguished from the
noise it sits in). Do not promote any output of this module into a gate until its
findings are zero.

M1's acceptance, and the only thing this module claims, is:

    every live context source is MAPPED to a proposed semantic role,
    and every place where a template requires a DIFFERENT role than its
    source supplies is NAMED, with a reproducing seed.

WHAT A "CONTEXT SOURCE" IS HERE
--------------------------------
A context source is any location that contributes a *lexical* (noun/unit) surface to
learner-visible text. Numeric operands are not context; `{a}` carries no semantics to
validate. Four families are inventoried:

  A. `interest_bank`     — data/interest_bank.json, one record per (theme, slot, value).
  B. `neutral_slots`     — generators/interest.py NEUTRAL_SLOTS, the no-theme fallback.
  C. `spine_slot_use`    — generators/spines.py, one record per slot OCCURRENCE in a
                           template. This is where roles are *required*; families A/B are
                           where they are *supplied*.
  D. `dna_lexical_slot`  — literal nouns/units DNA modules author directly.

DNA-authored question templates are NOT a fifth family. They cannot carry interest
context: `generate_context` computes interest slots in step (e), AFTER the DNA has
produced its values in step (c), and slots are never passed into a DNA. A DNA stem reaches
a learner either bare or with the fixed `interest_cue` sentence prepended
(`base_generator.py`, the `if interest_theme is not None` block). That cue is inventoried
as a family-C template.

HOW LIVENESS IS MEASURED, AND WHY THE NUMBER IS A FLOOR
--------------------------------------------------------
`--observe` renders the real pipeline and records what actually reached `question_text`.
It is an OBSERVATION, never a prediction: a source is marked live because a render
produced it, not because this module reasoned that it would.

NAMED LIMITATION — `observed_live_renders == 0` DOES NOT MEAN DEAD. The observation pass
drives only the `context` and `structure` axes declared in `compatibility.VARIANTS_BY_DNA`.
It does not vary `task_type`, `table`, `number_type`, `strategy`, or any formatter-level
axis, and it uses a fixed seed range. Measured consequence: `meas_object` is statically
eligible on 130 of 151 nodes and was observed 0 times. Every record therefore carries
`statically_eligible_nodes` beside `observed_live_renders`, and a record with
static eligibility but no observation is `liveness: "UNRESOLVED"` — a lead for the next
agent, not a finding of dormancy. Treating UNRESOLVED as dead is how a real defect gets
filed as unreachable.

A SECOND NAMED LIMITATION — ROLE PROPOSALS ARE PROPOSALS. The role a family-A entry
supplies is inferred from the SLOT it sits in, which is the only declaration the bank
makes. The bank does not say whether "mountain" is a container or "sheep" is measurable.
Every such question is emitted as an owner ruling, never silently resolved here.

Usage
-----
    PYTHONPATH=. .venv/bin/python tests/context_semantics_inventory.py --write
    PYTHONPATH=. .venv/bin/python tests/context_semantics_inventory.py --check
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.practice_gen.compatibility import VARIANTS_BY_DNA  # noqa: E402
from backend.app.practice_gen.generators.base_generator import (  # noqa: E402
    _KG_NODES,
    generate_context,
)
from backend.app.practice_gen.generators.interest import (  # noqa: E402
    _INTEREST_BANK_PATH,
    _INTERESTS,
    NEUTRAL_SLOTS,
    get_grade_appropriate_interests,
)
from backend.app.practice_gen.generators.spines import ALL_SPINES  # noqa: E402
from backend.app.practice_gen.registry import get_all_node_ids, get_node_dnas  # noqa: E402
from backend.app.practice_gen.validation._manifest import load_dna  # noqa: E402

OUTPUT_PATH = (
    REPO_ROOT / "validation_reports" / "phase2_hardening" / "context_semantics_inventory.json"
)

# ═══════════════════════════════════════════════════════════════════════════════
# THE TYPED ROLE VOCABULARY (plan step 3A)
# ═══════════════════════════════════════════════════════════════════════════════
# Step 3A names these nine. `non_standard_unit` is added because
# length_measurement._NON_STANDARD_UNITS supplies countable objects ("paperclips",
# "steps") in unit position, which is neither a plain `unit` nor a plain
# `countable_object` and would otherwise be forced into a wrong box.
ROLE_VOCABULARY: Dict[str, str] = {
    "actor": "An animate participant who can perform actions and own objects.",
    "countable_object": "A discrete object that can be counted one by one.",
    "substance": "A mass noun measured rather than counted (flour, water).",
    "container": "Something that can hold objects and has a plausible capacity.",
    "location": "A place where an action happens; NOT necessarily a container.",
    "action": "A verb frame relating actors, objects and state.",
    "measurable_attribute": "A property with magnitude (length, mass, capacity).",
    "unit": "A standard unit of a measurable attribute (cm, kg, mL).",
    "non_standard_unit": "A countable object used as a measuring unit (paperclips).",
    "state_transition": "A before/action/after change in quantity or condition.",
}

# What each interest-bank slot DECLARES it supplies. This is the bank's only
# declaration; it is a slot-level claim, not a per-string guarantee.
SLOT_SUPPLIES_ROLE: Dict[str, str] = {
    "actors": "actor",
    "objects": "countable_object",
    "places": "location",
    "item1": "countable_object",
    "item2": "countable_object",
}

# Template slot name -> the bank slot that fills it (interest.get_interest_slots).
TEMPLATE_SLOT_TO_BANK_SLOT: Dict[str, str] = {
    "actor": "actors",
    "objects": "objects",
    "place": "places",
    "item1": "item1",
    "item2": "item2",
}

# ═══════════════════════════════════════════════════════════════════════════════
# FRAME RULES — what a template REQUIRES of the slot at a given occurrence
# ═══════════════════════════════════════════════════════════════════════════════
# Each rule is (marker_regex, required_role, rationale). The regex is matched against a
# window of the normalised template around one slot occurrence. Rules are ordered; the
# first match wins. A slot occurrence matching NO rule is recorded with
# frame_review_status="unreviewed_default" and counted separately — it is NOT silently
# blessed. "Unknown means pass" is exactly the grandfathering step 3A forbids.
# TWO BUGS THIS TABLE ALREADY CARRIED, kept as comments because both reported a confident
# wrong number rather than failing:
#
#  1. A trailing `\b` immediately after `\}` never matches -- the next character in these
#     templates is punctuation or a space, and `\b` needs a word character on one side.
#     That silently left 127 occurrences "unreviewed", including the `sub_removes`
#     containment frame this module exists to name.
#  2. Matching a rule against a WINDOW around the occurrence let a rule for one slot
#     claim a different slot in the same sentence: `{actor}` in `sub_removes` matched the
#     `A {place} has` container rule, producing 57 "role mismatches" of which most were
#     the window bleeding across slots.
#
# So: every pattern embeds its own slot placeholder, each rule declares the slot it may
# classify, and a match counts only when it SPANS the occurrence being classified.
FRAME_RULES: List[Tuple[str, str, str, str]] = [
    ("place",
     r"\bA \{place\} has\b",
     "container",
     "'A {place} has N {objects}' makes the place hold the objects; a location that "
     "cannot contain them renders as an impossible premise."),
    ("place",
     r"\bleft in the \{place\}",
     "container",
     "'how many are left IN the {place}' re-asserts containment in the question."),
    ("place",
     r"\b(at|in) the \{place\}",
     "location",
     "'at/in the {place}' situates the action; no containment is claimed."),
    ("objects",
     r"\bmeasured two \{objects\}",
     "measurable_attribute",
     "'measured two {objects} ... combined length' requires the object to HAVE a length "
     "worth measuring."),
    ("objects",
     r"total length of both \{objects\}",
     "measurable_attribute",
     "The question re-asserts that the objects have a length to total."),
    ("item1",
     r"\bmeasured a \{item1\}",
     "measurable_attribute",
     "'measured a {item1}' requires a singular, measurable object."),
    ("item1",
     r"\bOne \{item1\} is \{len_a\}",
     "measurable_attribute",
     "'One {item1} is N cm long' requires a measurable object."),
    ("item2",
     r"\bA second \{item2\} was \{len_b\}",
     "measurable_attribute",
     "'A second {item2} was N cm long' requires a measurable object."),
    ("objects",
     r"\{objects\} in (a|one|another) basket|basket has \{[ab]\} \{objects\}",
     "countable_object",
     "A basket frame bounds plausible capacity: the object must fit in a basket."),
    ("objects",
     r"\{objects\} in a box",
     "countable_object",
     "A box frame bounds plausible capacity."),
    ("objects",
     r"\{objects\} on the table",
     "countable_object",
     "A table frame requires an object that can sit on a table."),
    ("objects",
     r"\bshare \{a\} \{objects\} equally",
     "countable_object",
     "Equal sharing requires an object that can be divided into whole parts."),
    ("objects",
     r"for \{objects\} that cost ₱|buy \{groups\} \{objects\}",
     "countable_object",
     "A purchase frame requires a purchasable object with a plausible peso price."),
    ("objects",
     r"\barranged \{objects\} in \{groups\} rows",
     "countable_object",
     "An array frame requires an object that can be physically arranged in rows."),
    ("objects",
     r"\{objects\} are put in each bag",
     "countable_object",
     "A bagging frame bounds plausible capacity."),
    # Generic agent frame. REVIEWED, not assumed: all 49 templates were enumerated and
    # every {actor} occurrence sits in agent or possessor position (arranged/bought/
    # climbs/collected/gives/got/had/has/measured/paid/puts/removes/saved/is thinking/
    # should say). No template puts {actor} in object position.
    ("actor",
     r"\{actor\}",
     "actor",
     "{actor} occurs only in agent or possessor position across all 49 templates."),
    # Generic possession/transfer/comparison frames. REVIEWED: these impose countability
    # and nothing further -- no container, surface, measurement or purchase is asserted.
    ("objects",
     r"(has|had|have|got|gives away|gave|takes away|removes|used|collected|puts|"
     r"share|arranged|measured|How many|how many|fewer|more|of them|in all|together|"
     r"in each|groups of|taken out|left|there are|There are|There were)"
     r"[^.?]{0,30}\{objects\}"
     r"|\{objects\}[^.?]{0,40}"
     r"(does|did|are|were|is|in all|together|left|how many|How many)",
     "countable_object",
     "Plain possession/transfer/comparison frame; imposes countability only."),
    ("item1",
     r"\{item1\}",
     "countable_object",
     "{item1} appears only as a counted or purchased secondary item outside the "
     "measurement templates handled above."),
    ("item2",
     r"\{item2\}",
     "countable_object",
     "{item2} appears only as a counted or purchased tertiary item outside the "
     "measurement templates handled above."),
]

# Frames that additionally require the filled value to be SINGULAR. Recorded separately
# from the role, because number agreement is a different failure than role mismatch.
SINGULAR_REQUIRED_RULES: List[Tuple[str, str]] = [
    (r"\bmeasured a \{item1\}", "'measured a {item1}' reads 'measured a crayons' when "
                                "the bank entry is plural."),
    (r"\bA \{place\} has\b", "'A {place}' reads 'A arena' when the place begins with a "
                             "vowel; the template hard-codes the article 'A'."),
]

# Head nouns that make an entry container-LIKE, so that placing it inside a containment
# frame produces a container-in-container premise ("One basket has 28 hamster cages").
#
# NAMED BLIND SPOT: this is a SEED list, not a lexicon. An entry whose head noun is absent
# is NOT flagged, and absence of a flag is not evidence of plausibility. It exists to make
# the already-known instances countable and to give the eventual §1L rule a starting
# declaration; it must not be read as coverage.
#
# IT ALSO OVER-FLAGS, and deliberately so. Its criterion is "the head noun names a
# container", which is BROADER than the owner's 2026-09-17 criterion ("would normally fit in
# a typical basket"). After the bank was fixed, 13 entries still carry this flag -- jars,
# water bottles, bags of flour, eco bags, sticker packs and the like -- and every one of them
# satisfies the owner's rule, because a jar fits in a basket perfectly well. The only true
# container-in-container left is `bible/baskets`, which `Spine.render` substitutes. So a
# flag here is a LEAD to look at, never a finding; do not work this list down to zero.
CONTAINER_HEAD_NOUNS: Tuple[str, ...] = (
    "basket", "box", "bag", "jar", "cage", "bowl", "cup", "case", "crate", "bin",
    "tin", "can", "pack", "set", "sack", "bottle",
)

# Frames that place the filled object INSIDE a container.
CONTAINMENT_FRAME_MARKERS: Tuple[str, ...] = (
    r"\bin (a|one|another) basket\b", r"\bbasket has \{[ab]\} \{objects\}", r"\bin a box\b",
)

# Violations reproduced by EXECUTION during the M1 measurement. Each was rendered through
# `generate_context` at the seed recorded here and pasted verbatim. They are evidence, not
# illustrations: `reproduce` is a runnable description of how each was obtained.
REPRODUCED_VIOLATIONS: List[Dict[str, Any]] = [
    {
        "id": "CSI-V1",
        "kind": "silent_substitution_bypasses_vocabulary_gate",
        "node_id": "mat_g1_na_q2_5", "grade": 1, "seed": 7, "theme": "bible",
        "spine_id": "add_putting_together",
        "rendered": "✝️ Ruth has a math challenge about baskets. One basket has 28 "
                    "figs. Another basket has 60 figs. If you put all the figs together, "
                    "how many figs are there?",
        "source": "backend/app/practice_gen/dna/base.py::Spine.render",
        "status": "ADJUDICATED 2026-09-17 — NOT a defect; see CSI-R4",
        "what_is_wrong": [
            "SEVERITY CORRECTED. This record first called the cue/stem pair a "
            "learner-visible contradiction. That was overstated: the cue names the theme "
            "slot value ('baskets') while the stem counts figs INSIDE baskets, which is "
            "redundant, not contradictory. The mechanism was right -- the cue fires because "
            "the plural 'baskets' does not string-match 'One basket has' in the pre-cue "
            "text -- but the severity was not.",
            "'figs' is substituted INSIDE Spine.render, after get_interest_slots has "
            "applied the node's NOT_YET_KNOWN filter, so it reaches the stem without ever "
            "passing the vocabulary gate. Verified: 'figs' is absent from this node's "
            "cumulative_vocab. Under the owner's ruling that 'figs' is safe at every grade "
            "this has no live consequence, but the CHANNEL remains: any future substituted "
            "word would travel the same path past the gate.",
            "interest_visible_terms still records 'baskets', so the interest-visibility "
            "check is satisfied by a word the stem no longer contains.",
            "The rule is hard-coded to the single string 'baskets'. That gap was the real "
            "finding and is now CLOSED at the data layer rather than in this rule: the "
            "owner's fit criterion indicted objects the substitution never reached -- "
            "container-in-container ('hamster cages'), too-big ('bicycles', 'nets', "
            "'sheep'), and NON-PHYSICAL ('ranked matches', 'game lives', 'subscribers', "
            "'game servers', all in grade-5+ themes and therefore invisible at G1-3). "
            "16 of 26 themes had their `objects` rewritten on 2026-09-17.",
        ],
        "reproduce": "generate_context(load_dna('addition'), 'mat_g1_na_q2_5', 1, 7, "
                     "{'context':'word_problem','structure':'result_unknown'}, 'bible')",
    },
    {
        "id": "CSI-V2",
        "kind": "location_used_as_container",
        "node_id": "mat_g1_na_q3_3", "grade": 1, "seed": 13, "theme": "bible",
        "spine_id": "sub_removes",
        "rendered": "A mountain has 10 sheep. Daniel removes 2 sheep. How many sheep are "
                    "left in the mountain?",
        "source": "backend/app/practice_gen/generators/spines.py::sub_removes",
        "what_is_wrong": [
            "'A {place} has N {objects}' requires the place to be a container; the bank "
            "declares every places entry as a location only.",
            "'in the mountain' is also the wrong preposition for the noun.",
        ],
        "reproduce": "subtraction DNA, context=word_problem, structure=result_unknown",
    },
    {
        "id": "CSI-V3",
        "kind": "capacity_implausible",
        "node_id": "mat_g3_na_q2_4", "grade": 3, "seed": 18, "theme": "volleyball",
        "spine_id": "sub_removes",
        "rendered": "A beach has 4282 score sheets. Ate Alyssa removes 4170 score sheets. "
                    "How many score sheets are left in the beach?",
        "source": "backend/app/practice_gen/generators/spines.py::sub_removes",
        "what_is_wrong": [
            "Magnitude and container are chosen independently, so the operand range and "
            "the narrative capacity are unrelated.",
            "'in the beach' is the wrong preposition.",
        ],
        "reproduce": "subtraction DNA, context=word_problem, structure=result_unknown",
    },
    {
        "id": "CSI-V4",
        "kind": "article_noun_disagreement",
        "node_id": "mat_g1_na_q3_3", "grade": 1, "seed": 23, "theme": "basketball",
        "spine_id": "sub_removes",
        "rendered": "A arena has 10 basketballs. Marco removes 1 basketball. How many "
                    "basketballs are left in the arena?",
        "source": "backend/app/practice_gen/generators/spines.py::sub_removes",
        "what_is_wrong": [
            "The template hard-codes the article 'A' before a slot that can be filled with "
            "a vowel-initial noun.",
            "§1J checks count/noun agreement and explicitly does NOT check "
            "article/noun agreement, so no current gate catches this.",
        ],
        "reproduce": "subtraction DNA, context=word_problem, structure=result_unknown",
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# FAMILY D — lexical literals authored inside DNA modules
# ═══════════════════════════════════════════════════════════════════════════════
# Enumerated by reading the modules; each entry names the file and the symbol so the
# next agent can re-derive it. These are NOT scraped, because a scraper over arbitrary
# Python would report string literals that never reach a learner.
DNA_LEXICAL_SOURCES: List[Dict[str, Any]] = [
    {
        "source_location": "backend/app/practice_gen/dna/mg/length_measurement.py::_NON_STANDARD_UNITS",
        "slot": "unit",
        "values": ["paperclips", "hands", "steps", "blocks", "crayons"],
        "proposed_role": "non_standard_unit",
        "note": "Countable objects used in unit position. Contextual validity requires the "
                "measured object to be plausibly measurable in that unit.",
    },
    {
        "source_location": "backend/app/practice_gen/dna/mg/mass_capacity.py::_UNITS_FOR",
        "slot": "unit",
        "values": ["g", "kg", "mg", "mL", "L"],
        "proposed_role": "unit",
        "note": "Standard mass/capacity units, paired with _UNIT_RANGE magnitudes.",
    },
    {
        "source_location": "backend/app/practice_gen/dna/mg/area.py::unit_label",
        "slot": "unit",
        "values": ["sq cm", "sq m"],
        "proposed_role": "unit",
        "note": "Area units; length_unit is derived by stripping the 'sq ' prefix.",
    },
    {
        "source_location": "backend/app/practice_gen/dna/mg/area.py::surface_noun",
        "slot": "surface_noun",
        "values": ["garden", "card"],
        "proposed_role": "container",
        "note": "ALREADY-FOUND §1L DEFECT, fixed at source: the module pins 'garden' to "
                "sq m because blind review flagged 5cm x 2cm gardens as unpicturable. "
                "This is a declared attribute/unit compatibility relationship and is the "
                "seed example for the family-D rules.",
    },
    {
        "source_location": "backend/app/practice_gen/dna/mg/area.py::shape_noun",
        "slot": "shape_noun",
        "values": ["square", "rectangle", "rectangular"],
        "proposed_role": "measurable_attribute",
        "note": "Geometric shape naming; mathematical rather than contextual.",
    },
    {
        "source_location": "backend/app/practice_gen/dna/na/counting.py::dir_word",
        "slot": "dir_word",
        "values": ["forward", "backward"],
        "proposed_role": "state_transition",
        "note": "Direction of a counting transition.",
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _normalise(template: str) -> str:
    return " ".join(template.split())


def _head_short() -> str:
    return subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip()


def _spans(pattern: str, template: str, start: int, end: int) -> bool:
    """True when some match of `pattern` covers the occurrence at [start, end).

    Spanning is what makes a rule apply to THIS occurrence rather than to any occurrence
    in the neighbourhood. Matching a window instead let one slot's rule classify another
    slot in the same sentence; see the note above FRAME_RULES.
    """
    for match in re.finditer(pattern, template):
        if match.start() <= start and match.end() >= end:
            return True
    return False


def _classify_occurrence(template: str, slot: str, start: int, end: int
                         ) -> Tuple[Optional[str], str, str]:
    """Return (required_role, rationale, frame_review_status) for one slot occurrence."""
    for rule_slot, pattern, role, rationale in FRAME_RULES:
        if rule_slot != slot:
            continue
        if _spans(pattern, template, start, end):
            return role, rationale, "reviewed"
    default = SLOT_SUPPLIES_ROLE.get(TEMPLATE_SLOT_TO_BANK_SLOT.get(slot, ""), "countable_object")
    return (
        default,
        "No reviewed frame marker matched this occurrence; the slot's declared role is "
        "assumed and the occurrence is flagged for review.",
        "unreviewed_default",
    )


def _requires_singular(template: str, start: int, end: int) -> Optional[str]:
    for pattern, rationale in SINGULAR_REQUIRED_RULES:
        if _spans(pattern, template, start, end):
            return rationale
    return None


def _static_eligibility() -> Dict[str, List[str]]:
    """Nodes on which each spine passes `Spine.is_eligible` — the generator's own rule."""
    out: Dict[str, List[str]] = {}
    nodes = get_all_node_ids()
    for spine in ALL_SPINES:
        ok: List[str] = []
        for node_id in nodes:
            kg = _KG_NODES.get(node_id) or {}
            concepts = set(kg.get("cumulative_concepts", []))
            vocab = set(kg.get("cumulative_vocab", []))
            vocab.update(kg.get("student_vocab", []))
            vocab.update(kg.get("introduces_vocab", []))
            grade = int(node_id.split("_")[1][1:])
            if spine.is_eligible(concepts, grade, vocab):
                ok.append(node_id)
        out[spine.id] = ok
    return out


def observe(seeds: int) -> Dict[str, Any]:
    """Render the real pipeline and record what actually reached learner-visible text."""
    entry_hits: collections.Counter = collections.Counter()
    spine_hits: collections.Counter = collections.Counter()
    theme_hits: collections.Counter = collections.Counter()
    renders = errors = 0
    slots = list(SLOT_SUPPLIES_ROLE)

    for node_id in get_all_node_ids():
        grade = int(node_id.split("_")[1][1:])
        for concept in (get_node_dnas(node_id) or []):
            try:
                dna = load_dna(concept)
            except Exception:
                continue
            structures = VARIANTS_BY_DNA.get(concept, {}).get("structure", ["result_unknown"])
            contexts = VARIANTS_BY_DNA.get(concept, {}).get("context", ["pure"])
            for ctx_value in contexts:
                for structure in structures:
                    for theme in _INTERESTS:
                        for seed in range(seeds):
                            try:
                                ctx = generate_context(
                                    dna=dna, node_id=node_id, grade=grade, seed=seed,
                                    difficulty_profile={"context": ctx_value,
                                                        "structure": structure},
                                    interest_theme=theme, is_student_path=True,
                                )
                            except Exception:
                                errors += 1
                                continue
                            renders += 1
                            spine_hits[ctx.spine_id or "__none__"] += 1
                            theme_hits[ctx.interest_theme] += 1
                            text = ctx.question_text or ""
                            for slot in slots:
                                for value in _INTERESTS[theme].get(slot, []):
                                    if value and value in text:
                                        entry_hits[(theme, slot, value)] += 1
    return {
        "renders": renders,
        "errors": errors,
        "seeds_per_combination": seeds,
        "entry_hits": entry_hits,
        "spine_hits": spine_hits,
        "themes_resolved": sorted(t for t in theme_hits if t),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Inventory construction
# ═══════════════════════════════════════════════════════════════════════════════

def build(observation: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    entry_hits = observation["entry_hits"] if observation else collections.Counter()
    spine_hits = observation["spine_hits"] if observation else collections.Counter()
    eligibility = _static_eligibility()

    live_grades = sorted({int(n.split("_")[1][1:]) for n in get_all_node_ids()})
    live_themes = {t for g in live_grades for t in get_grade_appropriate_interests(g)}

    sources: List[Dict[str, Any]] = []
    role_mismatches: List[Dict[str, Any]] = []
    owner_rulings: List[Dict[str, Any]] = []

    # ── Family C first: it defines what roles are REQUIRED where ──────────────
    slot_requirements: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)
    for spine in ALL_SPINES:
        template = _normalise(spine.template)
        observed = spine_hits.get(spine.id, 0)
        eligible_nodes = eligibility.get(spine.id, [])
        for match in re.finditer(r"\{(\w+)\}", template):
            slot = match.group(1)
            if slot not in TEMPLATE_SLOT_TO_BANK_SLOT:
                continue  # numeric/value slot: no lexical semantics
            role, rationale, review = _classify_occurrence(
                template, slot, match.start(), match.end())
            singular = _requires_singular(template, match.start(), match.end())
            record = {
                "family": "spine_slot_use",
                "source_location": f"backend/app/practice_gen/generators/spines.py::{spine.id}",
                "spine_id": spine.id,
                "template": template,
                "slot": slot,
                "bank_slot": TEMPLATE_SLOT_TO_BANK_SLOT[slot],
                "char_offset": match.start(),
                "required_role": role,
                "required_role_rationale": rationale,
                "frame_review_status": review,
                "requires_singular": bool(singular),
                "requires_singular_rationale": singular,
                "grade_band": list(spine.grade_band),
                "required_concepts": sorted(spine.required_concepts),
                "statically_eligible_nodes": len(eligible_nodes),
                "observed_live_renders": observed,
                "liveness": _liveness(observed, len(eligible_nodes)),
                "migration_status": "inventoried_nonbinding",
            }
            sources.append(record)
            slot_requirements[TEMPLATE_SLOT_TO_BANK_SLOT[slot]].append(record)

    # The interest cue is a template too (base_generator, non-spine path).
    sources.append({
        "family": "spine_slot_use",
        "source_location": "backend/app/practice_gen/generators/base_generator.py::interest_cue",
        "spine_id": "__interest_cue__",
        "template": "{emoji} {actor} has a math challenge about {objects}.",
        "slot": "actor+objects",
        "bank_slot": "actors+objects",
        "char_offset": -1,
        "required_role": "actor",
        "required_role_rationale": "Fixed cue prepended when a themed render produced no "
                                   "themed text; asserts only that the actor 'has a math "
                                   "challenge about' the objects, which imposes no "
                                   "containment or measurability.",
        "frame_review_status": "reviewed",
        "requires_singular": False,
        "requires_singular_rationale": None,
        "grade_band": [1, 10],
        "required_concepts": [],
        "statically_eligible_nodes": len(get_all_node_ids()),
        "observed_live_renders": None,
        "liveness": "NOT_MEASURED",
        "migration_status": "inventoried_nonbinding",
    })

    # ── Families A and B: what roles are SUPPLIED ─────────────────────────────
    for theme, body in _INTERESTS.items():
        theme_is_live = theme in live_themes
        for slot, supplied in SLOT_SUPPLIES_ROLE.items():
            for index, value in enumerate(body.get(slot, [])):
                observed = entry_hits.get((theme, slot, value), 0)
                requirements = slot_requirements.get(slot, [])
                conflicting = sorted({
                    r["required_role"] for r in requirements
                    if r["required_role"] != supplied
                })
                singular_frames = sorted({
                    r["spine_id"] for r in requirements if r["requires_singular"]
                })
                ambiguity: List[str] = []
                if conflicting:
                    ambiguity.append(
                        f"slot supplies '{supplied}' but reachable templates require "
                        f"{conflicting}; the bank does not declare which entries satisfy them"
                    )
                if singular_frames and value.endswith("s"):
                    ambiguity.append(
                        f"value is plural but {singular_frames} render it after a singular "
                        f"article"
                    )
                if slot in ("objects", "item1", "item2") and _is_container_like(value):
                    frames = sorted({
                        r["spine_id"] for r in requirements
                        if any(re.search(p, r["template"]) for p in CONTAINMENT_FRAME_MARKERS)
                    })
                    if frames:
                        ambiguity.append(
                            f"value is container-like and {frames} place it INSIDE a "
                            f"container, producing a container-in-container premise"
                        )
                sources.append({
                    "family": "interest_bank",
                    "source_location": f"data/interest_bank.json#/interests/{theme}/{slot}/{index}",
                    "theme": theme,
                    "slot": slot,
                    "value": value,
                    "proposed_role": supplied,
                    "role_basis": "slot declaration (the bank's only declaration)",
                    "grade_band": body.get("grade_band"),
                    "theme_live_for_current_grades": theme_is_live,
                    "reachable_slot_positions": len(requirements),
                    "observed_live_renders": observed,
                    "liveness": _liveness(observed, len(requirements) if theme_is_live else 0),
                    "ambiguity_requiring_human_ruling": ambiguity,
                    "migration_status": "inventoried_nonbinding",
                })

    for slot_name, value in NEUTRAL_SLOTS.items():
        bank_slot = TEMPLATE_SLOT_TO_BANK_SLOT.get(slot_name, slot_name)
        supplied = SLOT_SUPPLIES_ROLE.get(bank_slot, "countable_object")
        requirements = slot_requirements.get(bank_slot, [])
        sources.append({
            "family": "neutral_slots",
            "source_location": f"backend/app/practice_gen/generators/interest.py::NEUTRAL_SLOTS[{slot_name!r}]",
            "theme": "__neutral__",
            "slot": bank_slot,
            "value": value,
            "proposed_role": supplied,
            "role_basis": "slot declaration",
            "grade_band": [1, 10],
            "theme_live_for_current_grades": True,
            "reachable_slot_positions": len(requirements),
            "observed_live_renders": None,
            "liveness": "NOT_MEASURED",
            "ambiguity_requiring_human_ruling": [],
            "migration_status": "inventoried_nonbinding",
            "note": "Reached only when the requested theme is absent from the bank; the "
                    "observation pass always requests a real theme, so this family is "
                    "inventoried but not observed.",
        })

    # ── Family D ──────────────────────────────────────────────────────────────
    for entry in DNA_LEXICAL_SOURCES:
        for value in entry["values"]:
            sources.append({
                "family": "dna_lexical_slot",
                "source_location": entry["source_location"],
                "slot": entry["slot"],
                "value": value,
                "proposed_role": entry["proposed_role"],
                "role_basis": "module-authored literal, classified by reading the module",
                "observed_live_renders": None,
                "liveness": "NOT_MEASURED",
                "ambiguity_requiring_human_ruling": [],
                "migration_status": "inventoried_nonbinding",
                "note": entry["note"],
            })

    # ── Role mismatches: a template requiring what its source does not supply ──
    for bank_slot, requirements in sorted(slot_requirements.items()):
        supplied = SLOT_SUPPLIES_ROLE[bank_slot]
        for record in requirements:
            if record["required_role"] == supplied:
                continue
            affected = [
                s for s in sources
                if s["family"] == "interest_bank" and s.get("slot") == bank_slot
                and s.get("theme_live_for_current_grades")
            ]
            role_mismatches.append({
                "spine_id": record["spine_id"],
                "template": record["template"],
                "slot": record["slot"],
                "required_role": record["required_role"],
                "supplied_role": supplied,
                "rationale": record["required_role_rationale"],
                "statically_eligible_nodes": record["statically_eligible_nodes"],
                "observed_live_renders": record["observed_live_renders"],
                "liveness": record["liveness"],
                "affected_live_bank_entries": len(affected),
                "disposition": "OPEN — needs owner ruling; no §1L row exists to enforce it",
            })

    owner_rulings.append({
        "id": "CSI-R1",
        "question": "Which `places` entries are containers (may fill 'A {place} has N "
                    "{objects}') and which are locations only?",
        "why": "sub_removes is the only template that makes {place} hold objects. The bank "
               "declares every places entry as a location. Rendered consequences are in "
               "`rendered_violations`.",
        "blocks": "§1L containment/capacity rules for family A.",
    })
    owner_rulings.append({
        "id": "CSI-R2",
        "question": "Should `item1`/`item2` entries be constrained to singular surface "
                    "forms, or should templates stop hard-coding the article?",
        "why": "meas_object renders 'measured a {item1}'. Four live-theme item1 entries are "
               "plural (dance shoes, running shoes, crayons, sport socks).",
        "blocks": "§1L number-agreement rules; overlaps §1J, which checks count/noun "
                  "agreement but NOT article/noun agreement.",
    })
    owner_rulings.append({
        "id": "CSI-R4",
        "status": "RULED 2026-09-17 — CLOSED",
        "question": "Should `Spine.render`'s hard-coded 'baskets' -> 'figs' substitution be "
                    "removed in favour of a declared role rule?",
        "ruling": "'figs' is fine for any grade level. As long as a substituted word is "
                  "something that would normally fit in a typical 'basket', then the "
                  "substituted word is ok. The substitution is KEPT.",
        "rule_established": "An object placed inside a container frame must plausibly fit "
                            "that container.",
        "remedy_chosen": "Fix the interest bank rather than add a declaration layer or "
                         "generalise the substitution table. Applied 2026-09-17: the "
                         "`objects` list of 16 of 26 themes was rewritten so every entry "
                         "plausibly fits a basket. Only `objects` was touched -- item1/item2 "
                         "never reach a containment frame.",
        "NAMED_LIMITATION": "This remedy GATES NOTHING. It corrects today's data and adds no "
                            "check, so the next author to add a theme entry can reintroduce "
                            "the same shape with nothing to stop them. The owner chose it "
                            "with that trade stated. Whoever builds the binding §1L row "
                            "should add the containment assertion then; until then the only "
                            "thing standing between a grade-5 theme and 'One basket has 28 "
                            "ranked matches' is this file and whoever reads it.",
    })
    owner_rulings.append({
        "id": "CSI-R3",
        "question": "Do theme object lists have to be theme-coherent? `volleyball.objects` "
                    "contains 'shuttlecocks' and 'rackets' (badminton/tennis equipment).",
        "why": "Theme coherence is not currently declared anywhere and cannot be inferred "
               "from the slot. Flagged by inspection, not by a detector.",
        "blocks": "§1L object/theme compatibility rules.",
    })

    live_sources = [s for s in sources if s.get("liveness") == "LIVE"]
    unmapped = [
        s for s in sources
        if s.get("liveness") == "LIVE"
        and not (s.get("proposed_role") or s.get("required_role"))
    ]
    unreviewed_frames = [
        s for s in sources if s.get("frame_review_status") == "unreviewed_default"
    ]
    unresolved = [s for s in sources if s.get("liveness") == "UNRESOLVED"]

    return {
        "schema_version": 1,
        "kind": "context_semantics_inventory",
        "binding": False,
        "contract_reference": "§1L (RESERVED, deliberately NOT registered)",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "head_short": _head_short(),
        "plan_step": "3A / M1",
        "hardening_row": "H-07",
        "role_vocabulary": ROLE_VOCABULARY,
        "measurement": {
            "live_grades": live_grades,
            "live_nodes": len(get_all_node_ids()),
            "themes_total": len(_INTERESTS),
            "themes_live_for_current_grades": sorted(live_themes),
            "spines_total": len(ALL_SPINES),
            "observation": {
                "renders": observation["renders"] if observation else None,
                "errors": observation["errors"] if observation else None,
                "seeds_per_combination": observation["seeds_per_combination"] if observation else None,
                "axes_driven": ["context", "structure"],
                "axes_NOT_driven": ["task_type", "table", "number_type", "strategy",
                                    "formatter-level axes"],
            } if observation else None,
        },
        "counts": {
            "sources_total": len(sources),
            "by_family": dict(collections.Counter(s["family"] for s in sources)),
            "live_sources": len(live_sources),
            "unmapped_live_sources": len(unmapped),
            "unresolved_liveness": len(unresolved),
            "unreviewed_frame_occurrences": len(unreviewed_frames),
            "role_mismatches": len(role_mismatches),
            "reproduced_violations": len(REPRODUCED_VIOLATIONS),
            "owner_rulings_requested": len(owner_rulings),
        },
        "acceptance_m1": {
            "requirement": "inventory has zero unmapped live sources",
            "unmapped_live_sources": len(unmapped),
            "met": len(unmapped) == 0,
            "explicitly_not_claimed": [
                "§1L is not registered and gates nothing",
                "role proposals are proposals, not owner rulings",
                "observed_live_renders == 0 does not establish dormancy",
            ],
        },
        "reproduced_violations": REPRODUCED_VIOLATIONS,
        "role_mismatches": role_mismatches,
        "owner_rulings_requested": owner_rulings,
        "unmapped_live_sources": unmapped,
        "sources": sources,
    }


def _is_container_like(value: str) -> bool:
    """True when the entry's own head noun names a container (see CONTAINER_HEAD_NOUNS)."""
    tokens = re.findall(r"[a-z]+", value.lower())
    return any(
        token == noun or token == noun + "s" or token == noun + "es"
        for token in tokens for noun in CONTAINER_HEAD_NOUNS
    )


def _liveness(observed: Optional[int], statically_reachable: int) -> str:
    if observed:
        return "LIVE"
    if statically_reachable:
        return "UNRESOLVED"
    return "NOT_REACHABLE_AT_CURRENT_GRADES"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the inventory JSON")
    parser.add_argument("--check", action="store_true",
                        help="re-derive and assert zero unmapped live sources")
    parser.add_argument("--seeds", type=int, default=4,
                        help="seeds per (node, dna, context, structure, theme)")
    parser.add_argument("--no-observe", action="store_true",
                        help="skip the render pass (liveness becomes NOT_MEASURED)")
    args = parser.parse_args()

    if not (args.write or args.check):
        parser.error("pass --write or --check")

    observation = None if args.no_observe else observe(args.seeds)
    inventory = build(observation)

    if args.write:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(json.dumps(inventory, indent=1, ensure_ascii=False) + "\n",
                               encoding="utf-8")
        print(f"wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")

    counts = inventory["counts"]
    print(f"sources={counts['sources_total']} "
          f"live={counts['live_sources']} "
          f"unmapped_live={counts['unmapped_live_sources']} "
          f"unresolved={counts['unresolved_liveness']} "
          f"unreviewed_frames={counts['unreviewed_frame_occurrences']} "
          f"role_mismatches={counts['role_mismatches']}")

    if args.check:
        if counts["unmapped_live_sources"]:
            print(f"FAIL context_semantics_inventory: "
                  f"{counts['unmapped_live_sources']} unmapped live source(s)")
            for source in inventory["unmapped_live_sources"][:20]:
                print(f"   {source['source_location']}")
            return 1
        print("PASS context_semantics_inventory: 0 unmapped live sources "
              "(NONBINDING — §1L is not registered)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
