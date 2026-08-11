"""
DNA: Probability Language (Data & Probability)

Covers MATATAG grade 3 probability language competencies.
  G3: "certain", "impossible", "equally likely", "more likely", "less likely"

dna_type="static_bank": generate_params() samples from an inline item pool.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set

from backend.app.practice_gen.dna.base import (
    DNA,
    ErrorPattern,
    VocabGated,
)


# ─── error patterns ───────────────────────────────────────────────────────────
_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="None",
        required_concept="probability_language",
        label="dp_prob_impossible",
        description="Assigned a probability greater than 1 or less than 0 (impossible event called likely, or certain event called impossible).",
    ),
    ErrorPattern(
        formula="None",
        required_concept="probability_language",
        label="dp_complement",
        description="Confused an event with its complement (e.g., described P(not A) as the same as P(A)).",
    ),
]


# ─── difficulty axes ──────────────────────────────────────────────────────────
_DIFFICULTY_AXES: Dict[str, Any] = {}


# ─── vocab-gated terms ────────────────────────────────────────────────────────
VOCAB_CERTAIN     = VocabGated(requires_vocab="certain",        preferred="certain",        fallback="will always happen")
VOCAB_IMPOSSIBLE  = VocabGated(requires_vocab="impossible",     preferred="impossible",     fallback="can never happen")
VOCAB_LIKELY      = VocabGated(requires_vocab="likely",         preferred="likely",         fallback="will probably happen")
VOCAB_UNLIKELY    = VocabGated(requires_vocab="unlikely",       preferred="unlikely",       fallback="will probably not happen")
VOCAB_EQ_LIKELY   = VocabGated(requires_vocab="equally likely", preferred="equally likely", fallback="have the same chance")
VOCAB_PROBABILITY = VocabGated(requires_vocab="probability",    preferred="probability",    fallback="chance of something happening")
VOCAB_OUTCOME     = VocabGated(requires_vocab="outcome",        preferred="outcome",        fallback="result")


# ─── static item pool ─────────────────────────────────────────────────────────
# Each item: {question, answer, distractors, scenario_type, context, probability_term}
_ITEM_POOL: List[Dict[str, Any]] = [
    # ── certain / impossible — coins ──────────────────────────────────────────
    {
        "question": "A bag has 5 red balls and no other colors. What is the chance of picking a red ball?",
        "answer": "certain",
        "distractors": ["impossible", "likely", "unlikely"],
        "scenario_type": "certain_impossible",
        "context": "colored_objects",
        "probability_term": "certain",
    },
    {
        "question": "A bag has only blue balls. What is the chance of picking a green ball?",
        "answer": "impossible",
        "distractors": ["certain", "likely", "equally likely"],
        "scenario_type": "certain_impossible",
        "context": "colored_objects",
        "probability_term": "impossible",
    },
    {
        "question": "You flip a coin. What is the chance of getting either heads OR tails?",
        "answer": "certain",
        "distractors": ["impossible", "likely", "unlikely"],
        "scenario_type": "certain_impossible",
        "context": "coins",
        "probability_term": "certain",
    },
    {
        "question": "You flip a regular coin. What is the chance of getting the number 3?",
        "answer": "impossible",
        "distractors": ["certain", "likely", "equally likely"],
        "scenario_type": "certain_impossible",
        "context": "coins",
        "probability_term": "impossible",
    },
    {
        "question": "A spinner has all sections colored red. What is the chance of landing on red?",
        "answer": "certain",
        "distractors": ["impossible", "unlikely", "likely"],
        "scenario_type": "certain_impossible",
        "context": "spinners",
        "probability_term": "certain",
    },
    {
        "question": "A spinner has all sections colored blue. What is the chance of landing on red?",
        "answer": "impossible",
        "distractors": ["certain", "likely", "unlikely"],
        "scenario_type": "certain_impossible",
        "context": "spinners",
        "probability_term": "impossible",
    },
    {
        # "(choose the correct word)" told the student to expect a single
        # word, but the keyed answer is a full clause -- an instruction/
        # answer type mismatch (blind review of mat_g3_dp_q3_4).
        "question": "It is impossible for it to rain. Under what condition would that be true?",
        "answer": "when there are no clouds and no moisture in the air",
        "distractors": ["on a Monday", "when the temperature is warm", "in the morning"],
        "scenario_type": "certain_impossible",
        "context": "weather",
        "probability_term": "impossible",
    },
    # ── likely / unlikely ─────────────────────────────────────────────────────
    {
        "question": "If you flip a coin 10 times, getting heads at least once is ___.",
        "answer": "likely",
        "distractors": ["unlikely", "impossible", "certain"],
        "scenario_type": "likely_unlikely",
        "context": "coins",
        "probability_term": "likely",
    },
    {
        "question": "If you flip a coin 10 times, getting heads 10 times in a row is ___.",
        "answer": "unlikely",
        "distractors": ["likely", "certain", "impossible"],
        "scenario_type": "likely_unlikely",
        "context": "coins",
        "probability_term": "unlikely",
    },
    {
        "question": "A bag has 8 red balls and 2 blue balls. What is the chance of picking a red ball?",
        "answer": "likely",
        "distractors": ["unlikely", "impossible", "certain"],
        "scenario_type": "likely_unlikely",
        "context": "colored_objects",
        "probability_term": "likely",
    },
    {
        "question": "A bag has 1 red ball and 9 blue balls. What is the chance of picking a red ball?",
        "answer": "unlikely",
        "distractors": ["likely", "certain", "impossible"],
        "scenario_type": "likely_unlikely",
        "context": "colored_objects",
        "probability_term": "unlikely",
    },
    {
        "question": "A spinner is mostly green with a tiny yellow section. What is the chance of landing on yellow?",
        "answer": "unlikely",
        "distractors": ["likely", "certain", "equally likely"],
        "scenario_type": "likely_unlikely",
        "context": "spinners",
        "probability_term": "unlikely",
    },
    {
        "question": "A spinner is mostly yellow with a tiny green section. What is the chance of landing on yellow?",
        "answer": "likely",
        "distractors": ["unlikely", "impossible", "equally likely"],
        "scenario_type": "likely_unlikely",
        "context": "spinners",
        "probability_term": "likely",
    },
    {
        "question": "The weather forecast shows a 90% chance of rain. Is rain likely or unlikely today?",
        "answer": "likely",
        "distractors": ["unlikely", "impossible", "certain"],
        "scenario_type": "likely_unlikely",
        "context": "weather",
        "probability_term": "likely",
    },
    {
        "question": "The weather forecast shows only a 5% chance of rain. Is rain likely or unlikely today?",
        "answer": "unlikely",
        "distractors": ["likely", "certain", "impossible"],
        "scenario_type": "likely_unlikely",
        "context": "weather",
        "probability_term": "unlikely",
    },
    # ── equally likely ────────────────────────────────────────────────────────
    {
        "question": "A bag has 5 red balls and 5 blue balls. The chances of picking red or blue are ___.",
        "answer": "equally likely",
        "distractors": ["red is more likely", "blue is more likely", "impossible"],
        "scenario_type": "comparative",
        "context": "colored_objects",
        "probability_term": "equally likely",
    },
    {
        "question": "A coin is flipped. The chance of heads and the chance of tails are ___.",
        "answer": "equally likely",
        "distractors": ["heads is more likely", "tails is more likely", "impossible"],
        "scenario_type": "comparative",
        "context": "coins",
        "probability_term": "equally likely",
    },
    {
        "question": "A spinner has two equal sections: one red and one blue. Spinning red or blue are ___.",
        "answer": "equally likely",
        "distractors": ["red is more likely", "blue is more likely", "certain"],
        "scenario_type": "comparative",
        "context": "spinners",
        "probability_term": "equally likely",
    },
    # ── comparative ───────────────────────────────────────────────────────────
    {
        "question": "A bag has 7 red balls and 3 blue balls. Which color is MORE likely to be picked?",
        "answer": "red",
        "distractors": ["blue", "they are equally likely", "neither can be picked"],
        "scenario_type": "comparative",
        "context": "colored_objects",
        "probability_term": "more likely",
    },
    {
        "question": "A bag has 2 yellow marbles and 8 green marbles. Which is LESS likely to be picked?",
        "answer": "yellow",
        "distractors": ["green", "they are equally likely", "neither"],
        "scenario_type": "comparative",
        "context": "colored_objects",
        "probability_term": "less likely",
    },
    {
        "question": "A spinner has 3 red sections and 1 blue section. Which outcome is more likely?",
        "answer": "red",
        "distractors": ["blue", "equally likely", "impossible"],
        "scenario_type": "comparative",
        "context": "spinners",
        "probability_term": "more likely",
    },
    {
        "question": "A box has 10 pencils and 2 pens. Picking a pencil vs picking a pen — which is more likely?",
        "answer": "pencil",
        "distractors": ["pen", "equally likely", "impossible"],
        "scenario_type": "comparative",
        "context": "colored_objects",
        "probability_term": "more likely",
    },
    {
        "question": "On a sunny day with no clouds, which event is more likely?",
        "answer": "It stays sunny.",
        "distractors": [
            "It rains heavily.",
            "It snows.",
            "A tornado happens.",
        ],
        "scenario_type": "comparative",
        "context": "weather",
        "probability_term": "more likely",
    },
    {
        "question": "A bag has 6 red balls and 4 blue balls. Is picking red more likely, less likely, or equally likely compared to picking blue?",
        "answer": "more likely",
        "distractors": ["less likely", "equally likely", "impossible"],
        "scenario_type": "comparative",
        "context": "colored_objects",
        "probability_term": "more likely",
    },
    {
        "question": "A bag has 3 red balls and 7 blue balls. Is picking red more likely, less likely, or equally likely compared to picking blue?",
        "answer": "less likely",
        "distractors": ["more likely", "equally likely", "certain"],
        "scenario_type": "comparative",
        "context": "colored_objects",
        "probability_term": "less likely",
    },
    # "most likely"/"least likely" (superlative, 3+ outcomes) were never
    # represented at all -- every existing "comparative" item is a 2-way
    # more/less/equally comparison (blind review of mat_g3_dp_q3_4:
    # comprehensive_coverage FAIL, these two named terms never appear
    # anywhere in the sample set).
    {
        "question": "A bag has 6 red balls, 3 blue balls, and 1 green ball. Which color is MOST likely to be picked?",
        "answer": "red",
        "distractors": ["blue", "green", "It is equally likely for all colors."],
        "scenario_type": "comparative",
        "context": "colored_objects",
        "probability_term": "most likely",
    },
    {
        "question": "A spinner has 5 sections: 3 yellow, 1 red, and 1 green. Which color is LEAST likely to be landed on?",
        "answer": "red or green",
        "distractors": ["yellow", "It is equally likely for all colors.", "blue"],
        "scenario_type": "comparative",
        "context": "spinners",
        "probability_term": "least likely",
    },
    {
        "question": "A box has 8 pencils, 5 pens, and 2 erasers. Which item is MOST likely to be picked at random?",
        "answer": "pencil",
        "distractors": ["pen", "eraser", "It is equally likely for all items."],
        "scenario_type": "comparative",
        "context": "colored_objects",
        "probability_term": "most likely",
    },
    {
        "question": "Which event is CERTAIN to happen when you roll a standard number cube (1–6)?",
        "answer": "Getting a number between 1 and 6.",
        "distractors": ["Getting a 7.", "Getting a 0.", "Getting a 10."],
        "scenario_type": "certain_impossible",
        "context": "colored_objects",
        "probability_term": "certain",
    },
    {
        "question": "Which event is IMPOSSIBLE when you flip a coin?",
        "answer": "Getting the number 5.",
        "distractors": ["Getting heads.", "Getting tails.", "Getting heads or tails."],
        "scenario_type": "certain_impossible",
        "context": "coins",
        "probability_term": "impossible",
    },
]


# ─── parameter generator ──────────────────────────────────────────────────────

def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """Sample one scenario from the static pool filtered by difficulty profile."""
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    # "Describe and compare outcomes... using: equally likely, less/least
    # likely, more/most likely, certain, and impossible" (mat_g3_dp_q3_4)
    # names all three implemented scenario_types worth of vocabulary, but
    # this always defaulted to "certain_impossible" alone when unbound --
    # the "comparative" pool (equally/less/more likely) and "likely_
    # unlikely" pool existed but were never once selected (blind review:
    # comprehensive_coverage FAIL, "only 2 of the 5 named terms appear...
    # 'equally likely', 'less/least likely', and 'more/most likely' never
    # occur"). Same fix for "context", which also silently pinned to
    # "colored_objects" every time.
    scenario_type = profile.get("scenario_type")
    if isinstance(scenario_type, list):
        # registry.py binds an allow-list (not a single value) for
        # competencies whose named vocabulary excludes one of this DNA's
        # scenario_types (e.g. mat_g3_dp_q3_4 excludes "likely_unlikely" --
        # bare "likely"/"unlikely" isn't among its own named terms).
        # Orchestrator-level list resolution only fires for CALLER-supplied
        # difficulty_profile keys, not ones injected later from registry
        # bounds, so this DNA has to resolve it itself.
        scenario_type = rng.choice(scenario_type)
    elif not scenario_type:
        scenario_type = rng.choice(["certain_impossible", "likely_unlikely", "comparative"])
    context = profile.get("context") or rng.choice(
        ["colored_objects", "coins", "spinners", "weather"]
    )

    candidates = [
        item for item in _ITEM_POOL
        if item["scenario_type"] == scenario_type
        and item["context"] == context
    ]
    if not candidates:
        candidates = [item for item in _ITEM_POOL if item["scenario_type"] == scenario_type]
    if not candidates:
        candidates = _ITEM_POOL

    chosen = dict(rng.choice(candidates))
    return {
        "blank_target": "answer",
        "question": chosen["question"],
        "scenario": chosen["question"],
        "answer": chosen["answer"],
        "probability_term": chosen["probability_term"],
        "distractors": chosen["distractors"],
        "scenario_type": chosen["scenario_type"],
        "context": chosen["context"],
    }


# ─── hint generator ───────────────────────────────────────────────────────────

def generate_hints(
    values: Dict[str, Any],
    cumulative_vocab: Set[str],
) -> List[str]:
    certain_label    = VOCAB_CERTAIN.resolve(cumulative_vocab)
    impossible_label = VOCAB_IMPOSSIBLE.resolve(cumulative_vocab)
    likely_label     = VOCAB_LIKELY.resolve(cumulative_vocab)
    unlikely_label   = VOCAB_UNLIKELY.resolve(cumulative_vocab)
    eq_label         = VOCAB_EQ_LIKELY.resolve(cumulative_vocab)

    return [
        f"{certain_label.capitalize()}: will always happen (probability = 1).",
        f"{impossible_label.capitalize()}: can never happen (probability = 0).",
        f"{likely_label.capitalize()}: happens more often than not.",
        f"{unlikely_label.capitalize()}: does not happen often.",
        f"{eq_label.capitalize()}: two events have the same chance.",
        "Count the favorable outcomes and compare to the total to decide.",
    ]


# ─── DNA instance ─────────────────────────────────────────────────────────────

PROBABILITY_LANGUAGE_DNA = DNA(
    concept="probability_language",
    dna_type="static_bank",
    answer_formula=None,
    param_bounds={
        "g3": {},
    },
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "categorize"],
    requires_context=False,
    visual_home=None,
    difficulty_axes=_DIFFICULTY_AXES,
)
