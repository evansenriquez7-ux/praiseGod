"""
DNA: Probability Experiment (Data & Probability)

Covers MATATAG grade 3 competency:
  mat_g3_dp_q3_0: Collect data from experiments with a small number of possible
                  outcomes (e.g., rolling a die or tossing a coin).
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set

from backend.app.practice_gen.dna.base import (
    DNA,
    ErrorPattern,
    VocabGated,
)


_ERROR_PATTERNS: List[ErrorPattern] = [
    ErrorPattern(
        formula="None",
        required_concept="probability_experiment",
        label="dp_exp_miscount",
        description="Miscounted the number of outcomes recorded in the experiment.",
    ),
]

_DIFFICULTY_AXES = [
    {
        "name": "experiment_type",
        "label": "Experiment Type",
        "dim_type": "discrete",
        "choices": ["coin_toss", "die_roll", "spinner", "colored_tiles"],
    },
]

VOCAB_EXPERIMENT = VocabGated(
    requires_vocab="experiment",
    preferred="experiment",
    fallback="activity",
)
VOCAB_OUTCOME = VocabGated(
    requires_vocab="outcome",
    preferred="outcome",
    fallback="result",
)


def generate_params(
    grade: int,
    difficulty_profile: Optional[Dict[str, Any]],
    seed: int,
) -> Dict[str, Any]:
    """Generate parameters for collecting and recording data from simple experiments."""
    rng = random.Random(seed)
    profile = difficulty_profile or {}

    exp_type = profile.get("experiment_type") or rng.choice(["coin_toss", "die_roll", "spinner", "colored_tiles"])

    task_subtype = rng.choice([
        "read_frequency",
        "find_total_trials",
        "most_least_frequent",
        "compare_outcomes",
        "missing_trial_count",
    ])

    if exp_type == "coin_toss":
        total_trials = rng.choice([10, 12, 15, 20, 25])
        heads_count = rng.randint(2, total_trials - 2)
        tails_count = total_trials - heads_count
        categories = ["Heads", "Tails"]
        counts = [heads_count, tails_count]
        
        if task_subtype == "missing_trial_count":
            target = rng.choice(["Heads", "Tails"])
            other = "Tails" if target == "Heads" else "Heads"
            other_val = tails_count if target == "Heads" else heads_count
            ans = heads_count if target == "Heads" else tails_count
            stem = f"In a coin toss experiment of {total_trials} tosses, the coin landed on {other} {other_val} times. How many times did it land on {target}?"
            distractors = [max(1, ans + 2), max(1, ans - 2), total_trials, other_val]
        elif task_subtype == "find_total_trials":
            stem = f"A student recorded coin toss results in a table: Heads ({heads_count}), Tails ({tails_count}). How many total tosses were recorded in the experiment?"
            ans = total_trials
            distractors = [heads_count, tails_count, total_trials + 2, max(1, total_trials - 5)]
        elif task_subtype == "compare_outcomes":
            diff = abs(heads_count - tails_count)
            more_side = "Heads" if heads_count >= tails_count else "Tails"
            less_side = "Tails" if more_side == "Heads" else "Heads"
            stem = f"A coin was tossed {total_trials} times. Heads occurred {heads_count} times and Tails occurred {tails_count} times. How many more times did {more_side} land than {less_side}?"
            ans = diff
            distractors = [diff + 1, max(1, diff - 1), heads_count, tails_count]
        else:
            target = rng.choice(["Heads", "Tails"])
            ans = heads_count if target == "Heads" else tails_count
            stem = f"A coin toss experiment was conducted with {total_trials} tosses. The results are: Heads: {heads_count}, Tails: {tails_count}. How many times did the coin land on {target}?"
            distractors = [tails_count if target == "Heads" else heads_count, total_trials, max(1, ans + 1), max(1, ans - 1)]

    elif exp_type == "die_roll":
        num_faces = 6
        total_trials = rng.choice([12, 18, 20, 24, 30])
        raw_counts = [rng.randint(1, 5) for _ in range(num_faces)]
        diff_trials = total_trials - sum(raw_counts)
        raw_counts[0] += diff_trials
        if raw_counts[0] < 1:
            raw_counts[0] = 1
            raw_counts[1] += (total_trials - sum(raw_counts))
        counts = raw_counts
        categories = ["1", "2", "3", "4", "5", "6"]
        table_str = ", ".join(f"Face {categories[i]}: {counts[i]}" for i in range(num_faces))
        
        if task_subtype == "most_least_frequent":
            direction = rng.choice(["most", "least"])
            if direction == "most":
                m = max(counts)
                best_idx = counts.index(m)
                ans = f"Face {categories[best_idx]}"
                stem = f"A 6-sided die was rolled {total_trials} times. The recorded tally is: {table_str}. Which face was rolled {direction} frequently?"
                other_indices = [i for i in range(num_faces) if i != best_idx]
                distractors = [f"Face {categories[i]}" for i in other_indices[:3]]
            else:
                m = min(counts)
                best_idx = counts.index(m)
                ans = f"Face {categories[best_idx]}"
                stem = f"A 6-sided die was rolled {total_trials} times. The recorded tally is: {table_str}. Which face was rolled {direction} frequently?"
                other_indices = [i for i in range(num_faces) if i != best_idx]
                distractors = [f"Face {categories[i]}" for i in other_indices[:3]]
        elif task_subtype == "find_total_trials":
            stem = f"The results of a rolling die experiment are recorded: {table_str}. How many total rolls were made in the experiment?"
            ans = total_trials
            distractors = [total_trials + 2, max(1, total_trials - 2), total_trials + 6, max(1, total_trials - 4)]
        else:
            q_face = rng.choice(categories)
            idx = categories.index(q_face)
            ans = counts[idx]
            stem = f"In a die rolling experiment of {total_trials} rolls, the results are: {table_str}. How many times did Face {q_face} appear?"
            distractor_pool = [c for i, c in enumerate(counts) if i != idx]
            distractors = list(dict.fromkeys(distractor_pool + [ans + 1, max(0, ans - 1), total_trials]))[:3]

    elif exp_type == "spinner":
        colors = ["Red", "Blue", "Green", "Yellow"]
        num_colors = rng.choice([3, 4])
        selected_colors = colors[:num_colors]
        total_spins = rng.choice([15, 20, 24, 30])
        raw_spins = [rng.randint(2, 8) for _ in selected_colors]
        raw_spins[0] += total_spins - sum(raw_spins)
        if raw_spins[0] < 1:
            raw_spins[0] = 2
            raw_spins[1] = total_spins - sum(raw_spins)
        counts = raw_spins
        categories = selected_colors
        table_str = ", ".join(f"{categories[i]}: {counts[i]}" for i in range(len(categories)))

        if task_subtype == "most_least_frequent":
            direction = rng.choice(["most", "least"])
            best_idx = counts.index(max(counts)) if direction == "most" else counts.index(min(counts))
            ans = categories[best_idx]
            stem = f"A spinner with colored sections was spun {total_spins} times. The outcomes recorded are: {table_str}. Which color was landed on {direction} often?"
            distractors = [c for c in categories if c != ans]
            if len(distractors) < 3:
                distractors.append("Orange")
        elif task_subtype == "find_total_trials":
            stem = f"A spinner experiment recorded these outcomes: {table_str}. What is the total number of spins in the experiment?"
            ans = total_spins
            distractors = [total_spins + 5, max(1, total_spins - 3), total_spins + 2, total_spins * 2]
        else:
            q_col = rng.choice(categories)
            idx = categories.index(q_col)
            ans = counts[idx]
            stem = f"A student spun a spinner {total_spins} times and recorded: {table_str}. How many times did the spinner land on {q_col}?"
            distractor_pool = [c for i, c in enumerate(counts) if i != idx]
            distractors = list(dict.fromkeys(distractor_pool + [ans + 2, max(0, ans - 2), total_spins]))[:3]

    else:
        tile_types = ["Red tile", "Blue tile", "Green tile"]
        total_draws = rng.choice([10, 15, 20, 25])
        raw_draws = [rng.randint(2, 8) for _ in tile_types]
        raw_draws[0] += total_draws - sum(raw_draws)
        if raw_draws[0] < 1:
            raw_draws[0] = 2
            raw_draws[1] = total_draws - sum(raw_draws)
        counts = raw_draws
        categories = tile_types
        table_str = ", ".join(f"{categories[i]}: {counts[i]}" for i in range(len(categories)))
        
        q_tile = rng.choice(categories)
        idx = categories.index(q_tile)
        ans = counts[idx]
        stem = f"In a probability experiment, a tile was picked from a bag and replaced {total_draws} times. Results: {table_str}. How many times was a {q_tile} drawn?"
        distractor_pool = [c for i, c in enumerate(counts) if i != idx]
        distractors = list(dict.fromkeys(distractor_pool + [ans + 1, max(0, ans - 1), total_draws]))[:3]

    cleaned_distractors = [d for d in distractors if d != ans]
    if len(cleaned_distractors) < 3:
        if isinstance(ans, int):
            cleaned_distractors.extend([ans + 3, max(0, ans - 3), ans + 4])
        else:
            cleaned_distractors.extend(["None of these", "All equal", "Other"])
    cleaned_distractors = list(dict.fromkeys(cleaned_distractors))[:3]

    return {
        "question": stem,
        "question_text": stem,
        "scenario": stem,
        "answer": ans,
        "correct_answer": ans,
        "distractors": cleaned_distractors,
        "experiment_type": exp_type,
        "task_subtype": task_subtype,
        "categories": categories,
        "counts": counts,
        "blank_target": "answer",
        "context": "pure",
        "structure": "result_unknown",
    }


def generate_hints(values: Dict[str, Any], cumulative_vocab: Set[str]) -> List[str]:
    exp_lbl = VOCAB_EXPERIMENT.resolve(cumulative_vocab)
    out_lbl = VOCAB_OUTCOME.resolve(cumulative_vocab)
    return [
        f"Look at the recorded data from the {exp_lbl}.",
        f"Each tally or count represents an {out_lbl}.",
        f"Find the requested value in the recorded data.",
    ]


PROBABILITY_EXPERIMENT_DNA = DNA(
    concept="probability_experiment",
    dna_type="textual",
    answer_formula=None,
    param_bounds={
        "g3": {},
    },
    error_patterns=_ERROR_PATTERNS,
    compatible_formatters=["mcq", "cloze", "true_false", "error_detect"],
    requires_context=False,
    visual_home=None,
    difficulty_axes=_DIFFICULTY_AXES,
)
