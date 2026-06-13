"""
fmt_peso_money.py — PesoMoney visual formatter

Produces a FormattedProblem with Philippine currency visual_params.
Carves generation logic from visual_skeletons.py _gen_peso_money /
_traps_peso_money; does NOT import from that module.

Philippine denominations:
    Centavo coins : 1, 5, 10, 25, 50 sentimos
    Peso coins    : 1, 5, 10 pesos
    Bills         : 20, 50, 100, 200, 500, 1 000 pesos

    Grade 1: peso coins and bills only (no centavos).

interaction_mode:
    "read" — coins/bills are shown; student counts the total
    "set"  — student is given a total; they build the amount by choosing
             denominations (drag-and-drop UI)

answer_collection:
    "mcq"            — 4 total-amount choices
    "fill_in_blank"  — student types the total (integer, in pesos)
"""

import random
from typing import List, Optional, Tuple

from backend.app.practice_gen.dna.base import FormattedProblem, QuestionContext


# ─────────────────────────────────────────────────────────────────────────────
# Denomination tables
# ─────────────────────────────────────────────────────────────────────────────

CENTAVO_COINS: List[int] = [1, 5, 10, 25, 50]   # sentimos
PESO_COINS: List[int] = [100, 500, 1000]          # in centavos (×100)
PESO_BILLS: List[int] = [2000, 5000, 10000, 20000, 50000, 100000]  # in centavos

# Working in centavos avoids float arithmetic. All amounts stored as centavos
# internally; visual_params use centavo values with `exclude_centavos` flag
# telling the frontend to render only the bill/coin face (not "0.XX").

PESO_COIN_FACES: List[int] = [1, 5, 10]    # peso faces  (coins)
BILL_FACES: List[int] = [20, 50, 100, 200, 500, 1000]  # bill faces in pesos


def _grade_denominations(grade: int) -> Tuple[List[int], List[int]]:
    """
    Return (coin_faces_pesos, bill_faces_pesos) appropriate for a grade.

    Grade 1: peso coins only, small bills only.
    Grade 2–3: all peso coins + bills up to 100.
    Grade 4+: all denominations.
    """
    if grade <= 1:
        return [1, 5, 10], [20, 50, 100]
    if grade <= 3:
        return [1, 5, 10], [20, 50, 100, 200]
    return [1, 5, 10], BILL_FACES


def _target_range(grade: int, diff_level: int) -> Tuple[int, int]:
    """Return (min_amount, max_amount) in pesos for grade / difficulty."""
    if grade <= 1:
        return (5, 50) if diff_level == 1 else (10, 100)
    if grade <= 2:
        return (10, 100) if diff_level == 1 else (20, 200)
    if grade <= 3:
        return (20, 200) if diff_level == 1 else (50, 500)
    if grade <= 4:
        return (50, 500) if diff_level <= 2 else (100, 1000)
    return (100, 1000) if diff_level <= 2 else (200, 2000)


def _greedy(amount_pesos: int, coin_faces: List[int], bill_faces: List[int]):
    """
    Greedy decomposition of amount_pesos into coin and bill groups.

    Returns (coins_list, bills_list) where each is a list of face values
    (with repetition) sorted largest-first.
    """
    all_denoms = sorted(bill_faces + coin_faces, reverse=True)
    remaining = amount_pesos
    coins_used: List[int] = []
    bills_used: List[int] = []
    for d in all_denoms:
        while remaining >= d:
            if d in bill_faces:
                bills_used.append(d)
            else:
                coins_used.append(d)
            remaining -= d
    if remaining != 0:
        return None, None
    return coins_used, bills_used


def _build_visual_params(
    grade: int, diff_level: int, rng: random.Random
) -> dict:
    """
    Generate PesoMoney visual_params.

    visual_params keys:
        coins            — list of {"denomination": int, "count": int}
        bills            — list of {"denomination": int, "count": int}
        total            — int (pesos)
        exclude_centavos — bool
        coin_faces       — list[int] available coin denominations
        bill_faces       — list[int] available bill denominations
        require_fewest   — bool (advanced difficulty)
    """
    coin_faces, bill_faces = _grade_denominations(grade)
    lo, hi = _target_range(grade, diff_level)

    # Pick a target that is reachable (snap to smallest-coin multiple)
    smallest = coin_faces[0]  # 1 or 5
    target = rng.randint(lo, hi)
    # Snap to a multiple of the smallest coin to ensure reachability
    target = max(lo, (target // smallest) * smallest)
    if target > hi:
        target = hi

    coins_list, bills_list = _greedy(target, coin_faces, bill_faces)
    if coins_list is None:
        # Fallback: use a single bill or coin
        target = rng.choice(coin_faces + bill_faces)
        coins_list = [target] if target in coin_faces else []
        bills_list = [target] if target in bill_faces else []

    # Aggregate into {denomination: count}
    from collections import Counter
    coin_counts = Counter(coins_list)
    bill_counts = Counter(bills_list)

    coins_vp = [{"denomination": d, "count": c} for d, c in sorted(coin_counts.items())]
    bills_vp = [{"denomination": d, "count": c} for d, c in sorted(bill_counts.items())]

    require_fewest = diff_level >= 3

    return {
        "coins": coins_vp,
        "bills": bills_vp,
        "total": target,
        "exclude_centavos": True,       # G1–G6 use only whole pesos
        "coin_faces": coin_faces,
        "bill_faces": bill_faces,
        "require_fewest": require_fewest,
    }


def _build_traps(params: dict, rng: random.Random) -> dict:
    """Return trap dict mirroring visual_skeletons._traps_peso_money."""
    traps: dict = {}
    target = params["total"]
    traps["overcounted"] = {
        "value": target + rng.choice([1, 5, 10]),
        "description": "Total is more than target",
    }
    under = rng.choice([1, 5, 10])
    if target - under > 0:
        traps["undercounted"] = {
            "value": target - under,
            "description": "Total is less than target",
        }
    if target >= 20:
        traps["wrong_denomination_count"] = {
            "value": target + 20,
            "description": "Used too many of one denomination",
        }
    if target >= 10:
        traps["doubled_denomination"] = {
            "value": target + 10,
            "description": "Counted one denomination twice",
        }
    return traps


# ─────────────────────────────────────────────────────────────────────────────
# Main formatter
# ─────────────────────────────────────────────────────────────────────────────

def format_peso_money(
    ctx: QuestionContext,
    rng: random.Random,
    interaction_mode: str = "read",
    answer_collection: str = "mcq",
) -> FormattedProblem:
    """
    Build a PesoMoney FormattedProblem from a QuestionContext.

    interaction_mode "read":
        Coins/bills are displayed; student counts and reports the total.
    interaction_mode "set":
        Student is given a target amount and builds it from available
        denominations (drag-and-drop).

    answer_collection "mcq":
        Four peso-amount choices.
    answer_collection "fill_in_blank":
        Student types the peso total as an integer.
    """
    # ── 1. Resolve visual_params ───────────────────────────────────────────────
    if ctx.visual_params and "total" in ctx.visual_params:
        vp = ctx.visual_params.copy()
    elif ctx.values and "amounts" in ctx.values:
        amounts = ctx.values["amounts"]
        total = ctx.values["total"]
        coin_faces, bill_faces = _grade_denominations(ctx.grade)
        coins_list = [a for a in amounts if a < 20]
        bills_list = [a for a in amounts if a >= 20]
        from collections import Counter
        coin_counts = Counter(coins_list)
        bill_counts = Counter(bills_list)
        coins_vp = [{"denomination": d, "count": c} for d, c in sorted(coin_counts.items())]
        bills_vp = [{"denomination": d, "count": c} for d, c in sorted(bill_counts.items())]
        diff_profile = ctx.difficulty_profile or {}
        diff_level = min(len(diff_profile) + 1, 4) if diff_profile else 2
        require_fewest = diff_level >= 3
        vp = {
            "coins": coins_vp,
            "bills": bills_vp,
            "total": total,
            "target_amount": total,
            "exclude_centavos": True,
            "coin_faces": coin_faces,
            "bill_faces": bill_faces,
            "require_fewest": require_fewest,
        }
    elif ctx.values and ("total" in ctx.values or "answer" in ctx.values or "result" in ctx.values):
        total = ctx.values.get("total") or ctx.values.get("answer") or ctx.values.get("result")
        coin_faces, bill_faces = _grade_denominations(ctx.grade)
        coins_list, bills_list = _greedy(total, coin_faces, bill_faces)
        if coins_list is None:
            coins_list = []
            bills_list = []
        from collections import Counter
        coin_counts = Counter(coins_list)
        bill_counts = Counter(bills_list)
        coins_vp = [{"denomination": d, "count": c} for d, c in sorted(coin_counts.items())]
        bills_vp = [{"denomination": d, "count": c} for d, c in sorted(bill_counts.items())]
        diff_profile = ctx.difficulty_profile or {}
        diff_level = min(len(diff_profile) + 1, 4) if diff_profile else 2
        require_fewest = diff_level >= 3
        vp = {
            "coins": coins_vp,
            "bills": bills_vp,
            "total": total,
            "target_amount": total,
            "exclude_centavos": True,
            "coin_faces": coin_faces,
            "bill_faces": bill_faces,
            "require_fewest": require_fewest,
        }
    else:
        diff_profile = ctx.difficulty_profile or {}
        diff_level = min(len(diff_profile) + 1, 4) if diff_profile else 2
        vp = _build_visual_params(ctx.grade, diff_level, random.Random(ctx.seed))
        vp["target_amount"] = vp["total"]

    vp["is_interactive"] = (interaction_mode == "set")
    total = vp["total"]
    traps = _build_traps(vp, rng)

    # ── 2. Question text ──────────────────────────────────────────────────────
    if interaction_mode == "read":
        question_text = "Count the coins and bills shown. What is the total amount?"
    else:
        stem = f"Use coins and bills to make exactly ₱{total}."
        if vp.get("require_fewest"):
            stem += " Use the fewest pieces possible."
        question_text = stem

    # ── 3. Answer collection ──────────────────────────────────────────────────
    mcq_options = None
    if answer_collection == "mcq":
        distractor_amounts = []
        seen = {total}
        for t in traps.values():
            v = t.get("value")
            if v is not None and v not in seen and v > 0:
                seen.add(v)
                distractor_amounts.append(v)
            if len(distractor_amounts) == 3:
                break
        # Pad if needed
        offsets = [5, 10, 20, 50, 100, 2, 1]
        for off in offsets:
            if len(distractor_amounts) >= 3:
                break
            for sign in (-1, 1):
                candidate = total + sign * off
                if candidate > 0 and candidate not in seen:
                    seen.add(candidate)
                    distractor_amounts.append(candidate)
                if len(distractor_amounts) >= 3:
                    break

        all_opts = [total] + distractor_amounts[:3]
        rng.shuffle(all_opts)
        mcq_options = [
            {"key": chr(ord("A") + i), "value": v, "is_correct": v == total}
            for i, v in enumerate(all_opts)
        ]
        correct_answer = next(o["key"] for o in mcq_options if o["is_correct"])
    else:
        correct_answer = total

    format_data: dict = {"visual_params": vp}
    if mcq_options is not None:
        format_data["mcq_options"] = mcq_options

    fmt = f"{interaction_mode}_{answer_collection}"

    return FormattedProblem(
        problem_id=f"{ctx.node_id}_{ctx.seed}_pesomoney",
        node_id=ctx.node_id,
        competency_text=ctx.competency_text,
        grade=ctx.grade,
        seed=ctx.seed,
        question_text=question_text,
        correct_answer=correct_answer,
        distractors=ctx.distractors,
        hints=ctx.hints,
        format=fmt,
        format_data=format_data,
        is_visual=True,
        visual_type="PesoMoney",
        visual_params=vp,
        interaction_mode=interaction_mode,
        answer_collection=answer_collection,
        difficulty_profile=ctx.difficulty_profile or {},
        difficulty_axes_served=ctx.difficulty_axes_served,
        experience="standard",
        experience_config=None,
        interest_theme=ctx.interest_theme,
        spine_id=ctx.spine_id,
    )
