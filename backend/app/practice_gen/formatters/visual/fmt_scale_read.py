"""
fmt_scale_read.py — ScaleRead visual formatter (mass and capacity)

The mass/capacity analogue of `fmt_ruler_measure`, and it exists for the same
reason that formatter does: a "read the measurement" task is answerable only if
the instrument is drawn.

WHY THIS EXISTS — measured, not assumed
---------------------------------------
`mass_capacity`'s `read_measurement` task was served by `mcq` and `cloze`, which
emit no visual at all. Every item on `mat_g3_mg_q2_0` and `mat_g3_mg_q2_3` was
therefore UNANSWERABLE, at 20 of 20 seeds each:

    mat_g3_mg_q2_0 seed1: "What is the mass of the object in g?"        -> 1
    mat_g3_mg_q2_3 seed1: "What is the capacity of the container in L?" -> 8

There is no object, no container and no number anywhere in the stem; the reading
lived in the DNA's `values["value"]` and nothing rendered it. `length_measurement`
had already solved the identical problem the correct way — `ruler_measure` owns
`read_measurement` there and FORMATTER_VARIANT_SUPPORT forbids `mcq`/`cloze` from
it — so this is a port of a pattern already live in production (RulerMeasure
renders on three G1/G2 length nodes), not a new invention.

interaction_mode:
    "read" — instrument and pointer shown; the student reads the measurement.
    There is deliberately no "set" mode: MATATAG G3 asks the pupil to *measure
    using appropriate tools*, not to set a dial, and a mode nothing routes to
    would be a declaration with no behaviour behind it.

visual_params:
    {
        "reading":       int,   # what the instrument shows, ON a graduation
        "unit":          str,   # g | kg | mg | mL | L
        "scale_max":     int,   # full-scale value, a whole number of ticks
        "tick_interval": int,   # value between graduations
        "instrument":    str,   # "dial" (mass) | "cylinder" (capacity)
        "object_label":  str,   # what is being measured, for the drawing
    }

Traps (all misreadings of THIS instrument, not generic near-misses):
    one_tick_high / one_tick_low — counted one graduation wrong
    tick_count                   — read the NUMBER of graduations, ignoring
                                   what each one is worth (the classic error
                                   when tick_interval != 1)
    scale_max_value              — read the instrument's capacity, not the pointer
"""

import random

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext, VocabGated
from backend.app.practice_gen.formatters._distractor_fallback import augment_distractors
from backend.app.practice_gen.formatters._option_order import shuffle_options


# Graduations a real G3 instrument is marked in. Kitchen scales step in
# 1/2/5/10/25/50/100 g; graduated cylinders in 1/5/10/25/50 mL; larger
# platform scales in 250/500/1000 g. Every value here is a granularity a
# pupil can count along, which is the whole requirement.
_TICKS = (1, 2, 5, 10, 25, 50, 100, 250, 500, 1000)

# What the instrument is holding, so the stem and the drawing name the same
# thing. Deliberately generic: naming a specific object ("a mango weighs...")
# would assert a real-world mass this DNA does not model and cannot check.
_MASS_LABELS = ("the object", "the parcel", "the bag")
_CAPACITY_LABELS = ("the container", "the jug", "the bottle")


def _scale_for(value: int) -> tuple:
    """
    Choose (reading, tick_interval, scale_max) so the reading is EXACTLY readable.

    The reading is snapped onto a graduation, because a pointer between two marks
    has no exact answer and this formatter is asked for one. The tick is chosen to
    put the reading between roughly 4 and 20 graduations from zero -- few enough
    to count, many enough that the pupil is reading a scale rather than a single
    mark. Preference is for a graduation count near 10.

    Returns the SNAPPED reading, which is the correct answer: this formatter is
    the authority on what it draws, exactly as fmt_ruler_measure's
    `params["length"]` is for the ruler.
    """
    if value <= 0:
        raise ValueError(
            f"fmt_scale_read: cannot draw a reading of {value!r}. A non-positive mass or "
            f"capacity is not a measurement; fix the DNA's value generation rather than "
            f"substituting a readable number here."
        )
    best = None
    for tick in _TICKS:
        n = max(1, int(round(value / tick)))
        # 0 = the readable band, 1 = too few graduations, 2 = too many to count
        band = 0 if 4 <= n <= 20 else (1 if n < 4 else 2)
        candidate = (band, abs(n - 10), tick, n)
        if best is None or candidate < best:
            best = candidate
    _band, _dist, tick, n = best
    reading = n * tick
    # Headroom above the reading so the pointer is not pinned at full scale --
    # an instrument whose maximum IS the reading teaches nothing about reading a
    # scale, and makes the `scale_max_value` trap indistinguishable from the answer.
    headroom = max(2, -(-n // 4))
    # FLOOR of 6 graduations. Without it a reading of 1 produced a 0-3 scale, on
    # which only three positive readings exist at all -- so a 4-option MCQ could
    # not be built from on-scale values and the pool fell through to a 0 g option,
    # i.e. an object with no mass. The DNA's per-unit ranges start at 1, so this
    # is reached often, not rarely.
    total_grads = max(n + headroom, 6)
    return reading, tick, tick * total_grads


def _build_traps(reading: int, tick: int, scale_max: int, rng: random.Random) -> list:
    """Up to 3 distractors, each a real misreading of this instrument."""
    traps: list = []
    seen = {reading}

    # Read the graduation COUNT instead of the value. Only a distinct error when
    # the ticks are not worth 1 each -- otherwise it equals the answer.
    if tick != 1:
        tick_count = reading // tick
        if tick_count > 0 and tick_count not in seen:
            traps.append(tick_count)
            seen.add(tick_count)

    # Off by one graduation, either way.
    for delta in (tick, -tick):
        candidate = reading + delta
        if candidate > 0 and candidate not in seen:
            traps.append(candidate)
            seen.add(candidate)

    # Read the instrument's capacity rather than the pointer.
    if scale_max not in seen:
        traps.append(scale_max)
        seen.add(scale_max)

    rng.shuffle(traps)
    if len(traps) < 3:
        # `augment_distractors` refuses NEGATIVE candidates but allows ZERO, which is
        # right for arithmetic (0 is a real sum) and wrong here: a reading of 0 g is
        # an object with no mass, and it reached options as `('B', 0)` against a
        # correct answer of 1 g. Filter to strictly positive and, if that leaves a
        # shortfall, walk outward on the positive side rather than accept a
        # non-measurement. The shared helper is left alone -- 15 formatters use it
        # and zero is legitimate for most of them.
        padded = augment_distractors(traps, reading, target=3 + 2,
                                     max_delta=max(3, tick * 3))
        traps = [d for d in padded if isinstance(d, (int, float)) and d > 0][:3]
        step = 1
        while len(traps) < 3 and step <= tick * 8:
            for candidate in (reading + step, reading - step):
                if candidate > 0 and candidate != reading and candidate not in traps:
                    traps.append(candidate)
                    if len(traps) == 3:
                        break
            step += 1
        if len(traps) < 3:
            raise ValueError(
                f"Formatter 'scale_read' requires at least 3 unique positive distractors, "
                f"but got {len(traps)} for reading={reading} tick={tick} "
                f"scale_max={scale_max}."
            )
    return traps[:3]


def _stem(instrument: str, unit: str, object_label: str, cumulative_vocab) -> str:
    """
    Ask for the reading the drawing shows.

    The measured quantity is vocab-gated the same way base_generator gates it for
    this DNA, so a node that has not introduced "mass"/"capacity" still gets a
    sentence it can read.
    """
    if instrument == "dial":
        quantity = VocabGated("mass", "mass", "weight").resolve(cumulative_vocab)
        tool = "scale"
    else:
        quantity = VocabGated(
            "capacity", "capacity", "amount of liquid"
        ).resolve(cumulative_vocab)
        tool = "measuring cylinder"
    return (
        f"Look at the {tool}. What is the {quantity} of {object_label}? "
        f"Give your answer in {unit}."
    )


def format_scale_read(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build a ScaleRead FormattedProblem from a QuestionContext.

    Pulls the reading from `ctx.values` (mass_capacity DNA). Keys used:
    `value`, `unit`, `measurement_type`.
    """
    values = ctx.values or {}

    raw = values.get("value")
    if raw is None:
        raise ValueError(
            f"fmt_scale_read: node {ctx.node_id} seed {ctx.seed} produced no 'value' to "
            f"read. This formatter draws a measurement and cannot invent one; it should "
            f"only be routed to a task_type that supplies a reading."
        )
    mtype = values.get("measurement_type", "mass")
    unit = values.get("unit") or ("g" if mtype == "mass" else "mL")

    reading, tick, scale_max = _scale_for(int(raw))
    instrument = "dial" if mtype == "mass" else "cylinder"
    labels = _MASS_LABELS if mtype == "mass" else _CAPACITY_LABELS
    object_label = labels[ctx.seed % len(labels)]

    vp = {
        "reading": reading,
        "unit": unit,
        "scale_max": scale_max,
        "tick_interval": tick,
        "instrument": instrument,
        "object_label": object_label,
    }

    # The drawing is the question, so the snapped reading is the answer. The DNA's
    # own `answer` is the unsnapped value and is deliberately NOT used: it would
    # disagree with the graduation the pointer sits on, which is the one thing the
    # pupil can actually read.
    correct_answer = reading
    traps = _build_traps(reading, tick, scale_max, rng)

    mcq_options = None
    if answer_collection == "mcq":
        all_opts = [correct_answer] + traps[:3]
        shuffle_options(all_opts, ctx.node_id, ctx.seed)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": v, "is_correct": v == correct_answer}
            for i, v in enumerate(all_opts)
        ]
        final_answer = next(o["key"] for o in mcq_options if o["is_correct"])
    else:
        final_answer = correct_answer

    question_text = _stem(instrument, unit, object_label, ctx.cumulative_vocab)

    format_data: dict = {"visual_params": vp}
    if mcq_options:
        format_data["mcq_options"] = mcq_options

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_scaleread",
        node_id=ctx.node_id,
        competency_text=ctx.competency_text,
        grade=ctx.grade,
        seed=ctx.seed,
        question_text=question_text,
        correct_answer=final_answer,
        distractors=traps,
        hints=ctx.hints,
        format=f"{interaction_mode}_{answer_collection}",
        format_data=format_data,
        is_visual=True,
        visual_type="ScaleRead",
        visual_params=vp,
        interaction_mode=interaction_mode,
        answer_collection=answer_collection,
        difficulty_profile=ctx.difficulty_profile or {},
        difficulty_axes_served=ctx.difficulty_axes_served,
        experience="standard",
        experience_config=None,
        interest_theme=ctx.interest_theme,
        spine_id=ctx.spine_id,
        given_values={k: v for k, v in values.items() if k != ctx.blank_target} or None,
        blank_target=ctx.blank_target,
    )
