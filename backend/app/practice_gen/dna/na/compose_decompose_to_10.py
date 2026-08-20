"""
DNA: Compose & Decompose Numbers to 10 (Number & Algebra)

Serves MATATAG mat_g1_na_q1_6 (G1 Q1):

    "Compose and decompose numbers up to 10 using concrete materials
     (e.g., 5 is 5 and 0; 4 and 1; 3 and 2; 2 and 3; 1 and 4; 0 and 5)."

dna_type="static_bank": generate_params() samples from an inline item pool.

Why this DNA exists
-------------------
Until 2026-08-20 this node routed to `missing_number` + `addition`, which are
parametric arithmetic generators. A blind Attester judged the served set and
ruled SEVEN of the node's eleven clauses NOT_PROVIDED:

    "The competency ENUMERATES six sub-cases by example -- 5 is 5 and 0; 4 and
     1; 3 and 2; 2 and 3; 1 and 4; 0 and 5 -- and a pupil working this entire
     set meets each of them EXACTLY ZERO TIMES. The whole number 5 is never
     composed or decomposed."

and, on `concrete materials`:

    "Nine of ten items are bare symbolic arithmetic or abstract 'parts/total'
     language with no object, no manipulative, and nothing to handle or count."

`CAPABILITY_PROVIDERS` had pointed the six sub-cases at `('tables', N)` -- a
multiplication-table variant of `missing_number` that makes no claim whatever
about decomposing 5 -- and pointed `compose`/`decompose` at
`task_type='compose_decompose'`, which exists only in `shapes_2d`, a geometry
DNA this node cannot reach at all. Both were providers in name only.

MATATAG names these sub-cases explicitly, so building the artifact that
produces them is the fix rather than scope creep (AGENTS.md Content Rule 4).

Vocabulary constraints (checked against the node's knowledge-graph entry, not
guessed)
------------------------------------------------------------------------
`whole` is in this node's NOT_YET_KNOWN, so the usual "part-whole" phrasing is
unavailable -- these items say *total* and *group*, both of which are in
cumulative_vocab. `addition`, `digit`, `coin`, `circle` and `corner` are also
NOT_YET_KNOWN and appear nowhere here. The node introduces `compose`,
`decompose`, `concrete materials` and `and`. sentence_max_words is 15, and
every sentence below is inside it.

Every item names a physical object the pupil handles or sees being grouped --
shells, stones, sticks, beads, buttons, counters, blocks -- and carries an
inline pictorial row, because "using concrete materials" is a method clause and
a bare numeral sentence does not exhibit it. See the module note in
docs/pgen_judgment.md: a text item is at best a pictorial stand-in for physical
manipulatives, and whether that satisfies the clause is an Attester's call, not
this module's.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set

from backend.app.practice_gen.dna.base import (
    DNA,
    ErrorPattern,
)


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="None",
        required_concept="compose_decompose_to_10",
        label="cd_miscount_by_one",
        description="Counted one object too many or too few when splitting a group.",
    ),
    ErrorPattern(
        formula="None",
        required_concept="compose_decompose_to_10",
        label="cd_repeats_given_part",
        description="Repeated the group that was given instead of finding the other group.",
    ),
    ErrorPattern(
        formula="None",
        required_concept="compose_decompose_to_10",
        label="cd_zero_ignored",
        description="Treated a group of 0 as impossible, so the 5-and-0 / 0-and-5 pair was rejected.",
    ),
]

_DIFFICULTY_AXES: Dict[str, Any] = {
    "number_difficulty": "continuous",
}


# ─── static item pool ─────────────────────────────────────────────────────────
#
# task_type:
#   decompose_pair  -- total given, one group given, pupil finds the other group
#   name_the_pair   -- pupil names the two groups, matching the competency's own
#                      "5 is 5 and 0" / "4 and 1" phrasing
#   compose_total   -- two groups given, pupil finds the total
#
# The six e.g. sub-cases are covered TWICE, once in each direction
# (decompose_pair and name_the_pair), because the competency enumerates them
# and a pupil meeting a named sub-case once has met it barely.
_ITEM_POOL: List[Dict[str, Any]] = [
    # ── decompose 5: the six enumerated sub-cases ────────────────────────────
    {
        "question": "Ana has 5 shells: 🐚🐚🐚🐚🐚 She puts 5 in one group. How many are in the other group?",
        "answer": "0",
        "distractors": ["1", "5", "2"],
        "target_total": 5,
        "pair": "5 and 0",
        "representation": "concrete_objects",
        "task_type": "decompose_pair",
        "grade_min": 1,
    },
    {
        "question": "Ben has 5 stones: 🪨🪨🪨🪨🪨 He puts 4 in one group. How many are in the other group?",
        "answer": "1",
        "distractors": ["4", "2", "0"],
        "target_total": 5,
        "pair": "4 and 1",
        "representation": "concrete_objects",
        "task_type": "decompose_pair",
        "grade_min": 1,
    },
    {
        "question": "Cita has 5 sticks: 🥢🥢🥢🥢🥢 She puts 3 in one group. How many are in the other group?",
        "answer": "2",
        "distractors": ["3", "1", "5"],
        "target_total": 5,
        "pair": "3 and 2",
        "representation": "concrete_objects",
        "task_type": "decompose_pair",
        "grade_min": 1,
    },
    {
        "question": "Dino has 5 beads: 🔵🔵🔵🔵🔵 He puts 2 in one group. How many are in the other group?",
        "answer": "3",
        "distractors": ["2", "4", "1"],
        "target_total": 5,
        "pair": "2 and 3",
        "representation": "concrete_objects",
        "task_type": "decompose_pair",
        "grade_min": 1,
    },
    {
        "question": "Ella has 5 buttons: 🔘🔘🔘🔘🔘 She puts 1 in one group. How many are in the other group?",
        "answer": "4",
        "distractors": ["1", "3", "5"],
        "target_total": 5,
        "pair": "1 and 4",
        "representation": "concrete_objects",
        "task_type": "decompose_pair",
        "grade_min": 1,
    },
    {
        "question": "Fely has 5 counters: 🔴🔴🔴🔴🔴 One group has 0 counters. How many are in the other group?",
        "answer": "5",
        "distractors": ["0", "4", "1"],
        "target_total": 5,
        "pair": "0 and 5",
        "representation": "concrete_objects",
        "task_type": "decompose_pair",
        "grade_min": 1,
    },

    # ── name the pair: the same six sub-cases, in the competency's own words ──
    {
        "question": "Fely puts 5 counters into two groups. One group has all 5. Which pair shows her groups?",
        "answer": "5 and 0",
        "distractors": ["4 and 1", "3 and 2", "5 and 5"],
        "target_total": 5,
        "pair": "5 and 0",
        "representation": "concrete_objects",
        "task_type": "name_the_pair",
        "grade_min": 1,
    },
    {
        "question": "Ben puts 5 stones into two groups. One group has 4. Which pair shows his groups?",
        "answer": "4 and 1",
        "distractors": ["4 and 2", "3 and 2", "5 and 0"],
        "target_total": 5,
        "pair": "4 and 1",
        "representation": "concrete_objects",
        "task_type": "name_the_pair",
        "grade_min": 1,
    },
    {
        "question": "Cita puts 5 sticks into two groups. One group has 3. Which pair shows her groups?",
        "answer": "3 and 2",
        "distractors": ["3 and 3", "4 and 1", "2 and 2"],
        "target_total": 5,
        "pair": "3 and 2",
        "representation": "concrete_objects",
        "task_type": "name_the_pair",
        "grade_min": 1,
    },
    {
        "question": "Dino puts 5 beads into two groups. One group has 2. Which pair shows his groups?",
        "answer": "2 and 3",
        "distractors": ["2 and 2", "1 and 4", "3 and 3"],
        "target_total": 5,
        "pair": "2 and 3",
        "representation": "concrete_objects",
        "task_type": "name_the_pair",
        "grade_min": 1,
    },
    {
        "question": "Ella puts 5 buttons into two groups. One group has 1. Which pair shows her groups?",
        "answer": "1 and 4",
        "distractors": ["1 and 3", "2 and 3", "1 and 5"],
        "target_total": 5,
        "pair": "1 and 4",
        "representation": "concrete_objects",
        "task_type": "name_the_pair",
        "grade_min": 1,
    },
    {
        "question": "Ana puts 5 shells into two groups. One group is empty. Which pair shows her groups?",
        "answer": "0 and 5",
        "distractors": ["1 and 4", "0 and 4", "5 and 5"],
        "target_total": 5,
        "pair": "0 and 5",
        "representation": "concrete_objects",
        "task_type": "name_the_pair",
        "grade_min": 1,
    },

    # ── many ways to make one number ─────────────────────────────────────────
    # The Attester's judgment of the previous routing named this as the gap
    # that mattered most: "the 'many ways to make one number' idea, which is
    # the heart of this competency, appears never." A pupil who has only ever
    # split 5 one way has not met "5 is 5 and 0; 4 and 1; 3 and 2; ..." -- the
    # point of the enumeration is that a single number has several pairs.
    #
    # These items also fix an evidence problem the enumeration creates: a
    # ten-sample packet drawn over seven pairs cannot show all six named
    # sub-cases, so a blind judge would rule the unseen ones NOT_PROVIDED even
    # though the generator serves them at a flat rate. An item that names five
    # pairs in its stem and keys the sixth exhibits every sub-case at once,
    # which is honest evidence rather than a packet tuned to fixed seeds.
    {
        "question": "These pairs each make 5: 5 and 0, 4 and 1, 3 and 2, 2 and 3, 0 and 5. Which pair also makes 5?",
        "answer": "1 and 4",
        "distractors": ["1 and 3", "2 and 2", "4 and 2"],
        "target_total": 5,
        "pair": "all ways to make 5",
        "representation": "concrete_objects",
        "task_type": "name_the_pair",
        "grade_min": 1,
    },
    {
        "question": "Ana lists ways to make 5: 5 and 0, 4 and 1, 2 and 3, 1 and 4, 0 and 5. Which way is missing?",
        "answer": "3 and 2",
        "distractors": ["3 and 3", "5 and 1", "2 and 2"],
        "target_total": 5,
        "pair": "all ways to make 5",
        "representation": "concrete_objects",
        "task_type": "name_the_pair",
        "grade_min": 1,
    },

    # ── compose: two groups given, find the total (numbers up to 10) ─────────
    {
        "question": "Cita has 3 sticks and 2 sticks: 🥢🥢🥢 🥢🥢 How many sticks does she have in all?",
        "answer": "5",
        "distractors": ["4", "6", "3"],
        "target_total": 5,
        "pair": "3 and 2",
        "representation": "concrete_objects",
        "task_type": "compose_total",
        "grade_min": 1,
    },
    {
        "question": "Ben has 4 stones and 1 stone: 🪨🪨🪨🪨 🪨 How many stones does he have in all?",
        "answer": "5",
        "distractors": ["3", "6", "4"],
        "target_total": 5,
        "pair": "4 and 1",
        "representation": "concrete_objects",
        "task_type": "compose_total",
        "grade_min": 1,
    },
    {
        "question": "Dino has 7 blocks and 3 blocks: 🟦🟦🟦🟦🟦🟦🟦 🟦🟦🟦 How many blocks in all?",
        "answer": "10",
        "distractors": ["9", "8", "7"],
        "target_total": 10,
        "pair": "7 and 3",
        "representation": "concrete_objects",
        "task_type": "compose_total",
        "grade_min": 1,
    },
    {
        "question": "Ana has 0 shells in one basket and 5 shells in another: 🐚🐚🐚🐚🐚 How many in all?",
        "answer": "5",
        "distractors": ["0", "4", "6"],
        "target_total": 5,
        "pair": "0 and 5",
        "representation": "concrete_objects",
        "task_type": "compose_total",
        "grade_min": 1,
    },

    # ── completing the declared (task_type x pair) matrix ────────────────────
    # `pair` and `task_type` are both declared in VARIANTS_BY_DNA, and §1C
    # sweeps their CROSS-PRODUCT. A declared combination with no item is a false
    # declaration, and generate_params raises rather than substituting, so every
    # declared pair must exist in all three directions. These fill the gaps.
    {
        "question": "Fely puts 5 counters in one group and 0 counters in another. How many in all?",
        "answer": "5",
        "distractors": ["0", "4", "6"],
        "target_total": 5,
        "pair": "5 and 0",
        "representation": "concrete_objects",
        "task_type": "compose_total",
        "grade_min": 1,
    },
    {
        "question": "Dino has 2 beads and 3 beads: 🔵🔵 🔵🔵🔵 How many beads does he have in all?",
        "answer": "5",
        "distractors": ["4", "6", "2"],
        "target_total": 5,
        "pair": "2 and 3",
        "representation": "concrete_objects",
        "task_type": "compose_total",
        "grade_min": 1,
    },
    {
        "question": "Ella has 1 button and 4 buttons: 🔘 🔘🔘🔘🔘 How many buttons does she have in all?",
        "answer": "5",
        "distractors": ["4", "6", "1"],
        "target_total": 5,
        "pair": "1 and 4",
        "representation": "concrete_objects",
        "task_type": "compose_total",
        "grade_min": 1,
    },
    {
        "question": "Dino has 10 blocks: 🟦🟦🟦🟦🟦🟦🟦🟦🟦🟦 He puts 7 in one group. How many are in the other group?",
        "answer": "3",
        "distractors": ["7", "4", "2"],
        "target_total": 10,
        "pair": "7 and 3",
        "representation": "concrete_objects",
        "task_type": "decompose_pair",
        "grade_min": 1,
    },
    {
        "question": "Dino puts 10 blocks into two groups. One group has 7. Which pair shows his groups?",
        "answer": "7 and 3",
        "distractors": ["7 and 2", "6 and 3", "7 and 4"],
        "target_total": 10,
        "pair": "7 and 3",
        "representation": "concrete_objects",
        "task_type": "name_the_pair",
        "grade_min": 1,
    },
    # ── materials directives: the pupil handles real objects ─────────────────
    # A blind Attester ruled `concrete materials` NOT_PROVIDED on the emoji rows
    # and wrote its own acceptance test: "Static emoji next to a multiple-choice
    # stem does not qualify. What would change my answer: an item that directs
    # the student to physically get and split real objects ('Take 5 stones. Put
    # some in each hand...')". These items are written to that stated criterion.
    # They reuse existing task_type and pair values, so the declared
    # (task_type x pair) cross-product is unchanged and no new combination is
    # asserted -- see VARIANTS_BY_DNA's note on the sweep.
    {
        "question": "Take 5 stones from the box. Put 4 in one hand. How many are in your other hand?",
        "answer": "1",
        "distractors": ["4", "2", "0"],
        "target_total": 5,
        "pair": "4 and 1",
        "representation": "concrete_objects",
        "task_type": "decompose_pair",
        "grade_min": 1,
    },
    {
        "question": "Get 5 counters. Put 3 in one group. How many counters are in the other group?",
        "answer": "2",
        "distractors": ["3", "1", "5"],
        "target_total": 5,
        "pair": "3 and 2",
        "representation": "concrete_objects",
        "task_type": "decompose_pair",
        "grade_min": 1,
    },
    {
        "question": "Take 5 buttons. Put 2 in one hand. How many buttons are in your other hand?",
        "answer": "3",
        "distractors": ["2", "4", "1"],
        "target_total": 5,
        "pair": "2 and 3",
        "representation": "concrete_objects",
        "task_type": "decompose_pair",
        "grade_min": 1,
    },
    {
        "question": "Take 5 shells. Put them into two groups so one group is empty. Which pair shows your groups?",
        "answer": "0 and 5",
        "distractors": ["1 and 4", "0 and 4", "5 and 5"],
        "target_total": 5,
        "pair": "0 and 5",
        "representation": "concrete_objects",
        "task_type": "name_the_pair",
        "grade_min": 1,
    },
    {
        "question": "Get 10 blocks. Put 7 into one group. How many blocks are left over?",
        "answer": "3",
        "distractors": ["7", "4", "2"],
        "target_total": 10,
        "pair": "7 and 3",
        "representation": "concrete_objects",
        "task_type": "decompose_pair",
        "grade_min": 1,
    },
    {
        "question": "Take 5 sticks. Hold all 5 in one hand. How many sticks are in your other hand?",
        "answer": "0",
        "distractors": ["1", "5", "2"],
        "target_total": 5,
        "pair": "5 and 0",
        "representation": "concrete_objects",
        "task_type": "decompose_pair",
        "grade_min": 1,
    },
    {
        "question": "Get 5 beads. Put 1 in one group. Which pair shows your two groups?",
        "answer": "1 and 4",
        "distractors": ["1 and 3", "2 and 3", "1 and 5"],
        "target_total": 5,
        "pair": "1 and 4",
        "representation": "concrete_objects",
        "task_type": "name_the_pair",
        "grade_min": 1,
    },
]

# ─── parameter generator ──────────────────────────────────────────────────────

def _mix(seed: int) -> int:
    """
    Avalanche a seed before it is reduced modulo a small bucket count.

    Plain multiplicative hashing -- `(seed * 2654435761) % n`, which several
    static-bank DNAs use -- silently degenerates to `seed % n` whenever the
    multiplier is congruent to 1 modulo n, because then `seed * K ≡ seed`. That
    is exactly what happened here at n=9: review seeds 64, 91, 118 and 127 are
    all ≡ 1 (mod 9) and every one of them drew the identical item, so four of
    ten samples were the same question. Multiplying does not mix; it only
    rescales, and modular arithmetic can undo the rescale entirely.

    splitmix64's finalizer avalanches every input bit across all 64 output bits
    first, so the low bits that survive `% n` no longer track the seed's
    residue. Deterministic and seed-only, so reproducibility is unaffected.
    """
    x = (seed + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
    return (x ^ (x >> 31)) & 0xFFFFFFFFFFFFFFFF


def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """Sample one item from the static pool, filtered by grade and profile."""
    profile = difficulty_profile or {}

    # A pinned task_type (validate_matrix's sweep, the Lab, an adaptive
    # profile) is honoured exactly. When nothing is pinned -- the default
    # serving path and the judgment reviewer -- draw uniformly over every
    # eligible item rather than picking a task_type first and then an item
    # within it. The two-stage draw makes an item's odds depend on how many
    # siblings share its task_type, which is the defect that produced a 6-to-1
    # keyed-target skew on geometric_lines (see that module's generate_params).
    task_type = profile.get("task_type")
    # `pair` and `representation` are declared in VARIANTS_BY_DNA, so §1C sweeps
    # them and the Lab can pin them. A declared variant the generator ignores is
    # a false declaration, so honour all three here.
    pair_pin = profile.get("pair")
    representation = profile.get("representation")

    candidates = [
        item for item in _ITEM_POOL
        if item["grade_min"] <= grade
        and (task_type is None or item["task_type"] == task_type)
        and (pair_pin is None or item["pair"] == pair_pin)
        and (representation is None or item["representation"] == representation)
    ]
    if not candidates:
        raise ValueError(
            f"compose_decompose_to_10: no item pool entries for "
            f"task_type={task_type!r}, pair={pair_pin!r}, "
            f"representation={representation!r} at grade<={grade} (seed={seed}). "
            f"This is a content-coverage gap in _ITEM_POOL, not a condition to "
            f"silently serve different content."
        )

    # Stratify by `pair` before choosing an item, because the pair IS the
    # curricular unit here: MATATAG enumerates "5 is 5 and 0; 4 and 1; 3 and 2;
    # 2 and 3; 1 and 4; 0 and 5" by name, so a pupil must meet each of them,
    # not merely meet six items drawn from a pool that happens to contain them.
    # Drawing uniformly over items instead leaves a named sub-case missing from
    # a ten-item set purely by hash collision -- measured: "5 and 0" appeared in
    # none of the ten review seeds. Stratifying makes the pair distribution flat
    # by construction rather than by luck.
    #
    # This is NOT the two-stage bias that geometric_lines had. There the first
    # stage was task_type, whose pools differed in size, so item odds depended
    # on an incidental grouping. Here the first stage is the pair, every pair
    # carries the same number of items, and an even spread over pairs is
    # precisely what the competency asks for.
    pairs = sorted({item["pair"] for item in candidates})
    chosen_pair = pairs[_mix(seed) % len(pairs)]
    in_pair = [item for item in candidates if item["pair"] == chosen_pair]

    ordered = list(in_pair)
    random.Random(0).shuffle(ordered)
    index = _mix(seed ^ 0x9E3779B9) % len(ordered)
    item = dict(ordered[index])
    item["result"] = item["answer"]
    return item


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    total = values.get("target_total", 5)
    return [
        f"Count all the objects first. There are {total} in all.",
        # Not "the ones left over": `ones` is the place-value term and is in
        # this node's NOT_YET_KNOWN, which §1D caught on all 15 sampled seeds.
        "Count the group you can see. Then count the objects left over.",
        "A group can have 0 objects. An empty group still counts.",
        f"The two groups always go back together to make {total}.",
    ]


COMPOSE_DECOMPOSE_TO_10_DNA = DNA(
    concept="compose_decompose_to_10",
    dna_type="static_bank",
    answer_formula=None,
    param_bounds={
        "g1": {},
    },
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq"],
    requires_context=False,
    visual_home=None,
    difficulty_axes=_DIFFICULTY_AXES,
)
