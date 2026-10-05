"""
Medium composition — owner ruling 15 (2026-10-02).

When a MATATAG competency names a medium the learner works IN (*illustrate, represent,
concrete, models, draw*), the node must serve that medium as a REGULAR part of what a
pupil meets, not incidentally. Ruling R-4 forbids routing weights: a formatter is chosen
uniformly from the ones a node allows. So the only lever is the allowed SET (the R-3
precedent, which met "show a picture >= 50% of the time" by declaring formatters, never
by a weight). Ruling 15 binds it: compose the node's allowed formatters so visual or
interactive ones are at least half of what is served, dropping text formatters only as
far as needed.

This module is the ONE place that composition lives. Every selection site calls
`compose_for_node` -- `PracticeOrchestrator.generate_problem` and
`registry.get_node_formatters` (what a node advertises, and what the Lab offers).
`PracticeOrchestrator.generate_batch` delegates each item to `generate_problem`, so it
selects nothing of its own. `adapter.generate_problem`/`generate_batch` are NOT wired: they
have no production caller and select by a different rule, so wiring them would add a copy
no check can observe; they are named in §2J's contract row for an owner decision. One rule, one function: a second copy of the drop
list would let the advertised set and the served set disagree, which §2B/§2C exist to
catch and which memory "two entry points, one rule" records happening before.

Every requirement clause in the knowledge graph whose text names a medium
(`MEDIUM_CLAUSE_RE`) must be classified here, in exactly one of:

  * `COMPOSED`  -- the clause's medium is served on >= `MEDIUM_SHARE_FLOOR` of student-path
                   items, measured by §2J. `drop` lists the text formatters removed from the
                   node to get there (possibly none, when the node already meets it).
  * `DEBT`      -- the medium cannot be met with formatters that exist today; ruling 16
                   owes a build. Each entry names what must be built. This list may only
                   shrink.
  * `EXEMPT`    -- the matched word is not a medium the learner works in, by ruling 1's
                   grammar test, with the reason quoted.

§2J fails a matching clause that is in none of them, so a later grade's medium clause
cannot slip past by not being listed (memory: "allowlist checks drift silently").

NAMED LIMITS (Mandate 6):
  * §2J proves the medium is SERVED often enough. It does not prove the served visual
    exhibits the specific clause -- `mat_g2_mg_q1_0` served 43/60 visual items and a blind
    Attester still ruled "Represent" NOT_PROVIDED. Sufficiency is §6F's job; this is the
    necessary floor beneath it.
  * "interactive" is read from the served payload (`interaction_mode == "set"` or
    `visual_params.is_read_only is False`). It does not prove the interaction is a
    manipulative in ruling 12's sense; that too is §6F's.
  * The clause matcher is lexical. A medium named in words it does not list (for example
    "using counters") is not classified and so not gated.
  * §2J samples the DEFAULT student path only. A declared variant that only text formatters
    can serve is §2I's to catch: on 2026-10-02 dropping every text formatter from
    mat_g2_na_q3_4 left its declared word_problem context unservable, §2J stayed green, and
    §2I failed it by name.
"""
from __future__ import annotations

import re
from typing import Dict, Iterable, List, Tuple

# Words that name a medium the learner works in (ruling 1), or the medium itself.
MEDIUM_CLAUSE_RE = re.compile(
    r"\b(illustrat\w*|represent\w*|models?|modell?ing|draws?|drawing|concrete|pictorial|pictures?|different size|different orientation)\b",
    re.I,
)

# Ruling 15: "at least half". §2J measures the served share against this.
MEDIUM_SHARE_FLOOR = 0.5

# node_id -> {requirement id -> entry}. An entry is
#   {"clause": <the KG clause, verbatim>, "medium": "visual" | "interactive",
#    "competency": <the competency phrase it comes from, quoted>, "drop": [formatter, ...]}
COMPOSED: Dict[str, Dict[str, Dict]] = {
    'mat_g1_mg_q1_0': {
        'different_size': {
            'clause': 'different size',
            'medium': 'visual',
            'competency': 'Identify simple 2-dimensional shapes (triangle, rectangle, square) of different size and in different orientation.',
            'drop': ['mcq', 'categorize'],
            'note': 'The learner must see the shape sizes; text-only formatters cannot render them.',
        },
        'different_orientation': {
            'clause': 'different orientation',
            'medium': 'visual',
            'competency': 'Identify simple 2-dimensional shapes (triangle, rectangle, square) of different size and in different orientation.',
            'drop': ['mcq', 'categorize'],
            'note': 'The learner must see rotated shapes; text-only formatters cannot render them.',
        },
    },
    'mat_g1_na_q1_2': {
        'represent': {'clause': 'represent', 'medium': 'visual', 'competency': 'Recognize and represent numbers up to 100 using a variety of concrete and pictorial models (e.g., number line, block or bar models, and numerals).', 'drop': []},
        'concrete_models': {'clause': 'concrete', 'medium': 'interactive', 'competency': 'Recognize and represent numbers up to 100 using a variety of concrete and pictorial models (e.g., number line, block or bar models, and numerals).', 'drop': [], 'note': 'place_value_blocks_set is served'},
        'pictorial_models': {'clause': 'pictorial models', 'medium': 'visual', 'competency': 'Recognize and represent numbers up to 100 using a variety of concrete and pictorial models (e.g., number line, block or bar models, and numerals).', 'drop': []},
        'block_or_bar_models': {'clause': 'block or bar models', 'medium': 'visual', 'competency': 'Recognize and represent numbers up to 100 using a variety of concrete and pictorial models (e.g., number line, block or bar models, and numerals).', 'drop': []},
    },
    'mat_g1_na_q1_7': {
        'illustrate': {'clause': 'Illustrate', 'medium': 'visual', 'competency': "Illustrate addition of numbers with sums up to 20 using a variety of concrete and pictorial models and describes addition as 'counting up,' and 'putting together'.", 'drop': ['error_detect', 'true_false', 'cloze']},
        'pictorial_models': {'clause': 'pictorial models', 'medium': 'visual', 'competency': "Illustrate addition of numbers with sums up to 20 using a variety of concrete and pictorial models and describes addition as 'counting up,' and 'putting together'.", 'drop': ['error_detect', 'true_false', 'cloze']},
    },
    'mat_g1_na_q1_9': {
        'pictures': {'clause': 'pictures', 'medium': 'visual', 'competency': 'Solve problems (given orally or in pictures) involving addition with sums up to 20.', 'drop': ['error_detect', 'true_false', 'cloze'], 'note': "R-3 composed the sister clause on mat_g1_na_q4_6 to >= 50% pictures on the owner's ruling, and three blind Attesters judged it unmet; ruling 1 alone would accept a worded story."},
    },
    'mat_g1_na_q2_6': {
        'pictures': {'clause': 'pictures', 'medium': 'visual', 'competency': 'Solve problems (given orally or in pictures) involving addition with sums up to 100 without regrouping.', 'drop': ['error_detect', 'true_false', 'cloze'], 'note': "R-3 composed the sister clause on mat_g1_na_q4_6 to >= 50% pictures on the owner's ruling, and three blind Attesters judged it unmet; ruling 1 alone would accept a worded story."},
    },
    'mat_g1_na_q3_0': {
        'illustrate_subtraction': {'clause': 'Illustrate subtraction', 'medium': 'visual', 'competency': "Illustrate subtraction involving numbers up to 20 using a variety of concrete and pictorial models, and describes subtraction as 'taking away'.", 'drop': ['error_detect', 'true_false', 'cloze', 'mcq']},
    },
    'mat_g1_na_q3_3': {
        'in_pictures': {'clause': 'in pictures', 'medium': 'visual', 'competency': 'Solve subtraction problems (given orally or in pictures) where both numbers are less than 20.', 'drop': ['error_detect', 'true_false', 'cloze', 'mcq'], 'note': "R-3 composed the sister clause on mat_g1_na_q4_6 to >= 50% pictures on the owner's ruling, and three blind Attesters judged it unmet; ruling 1 alone would accept a worded story."},
    },
    'mat_g1_na_q3_4': {
        'pictorial_models': {'clause': 'pictorial models', 'medium': 'visual', 'competency': 'Subtract numbers where both numbers are less than 100 using concrete and pictorial models, without regrouping: 2-digit minus 1-digit numbers, and 2-digit minus 2-digit numbers.', 'drop': ['error_detect', 'true_false', 'cloze', 'mcq']},
    },
    'mat_g1_na_q4_0': {
        'illustrate': {'clause': 'Illustrate', 'medium': 'visual', 'competency': 'Illustrate 1/2 and 1/4 as parts of a whole.', 'drop': []},
    },
    'mat_g1_na_q4_1': {
        'models': {'clause': 'models', 'medium': 'visual', 'competency': 'Compare 1/2 and 1/4 using models.', 'drop': []},
    },
    'mat_g1_na_q4_6': {
        'in_pictures': {'clause': 'in pictures', 'medium': 'visual', 'competency': 'Solve 1-step problems (given orally or in pictures) involving addition of money where the sum is up to ₱100, or subtraction of money where both amounts are less than ₱100.', 'drop': ['cloze', 'mcq'], 'note': 'R-3 (owner): this node must show a picture >= 50% of the time. Measured 29/60 (48%) before composition, so R-3 had regressed with no gate to see it.'},
    },
    'mat_g2_na_q1_2': {
        'recognize_and_represent': {'clause': 'Recognize and represent', 'medium': 'visual', 'competency': 'Recognize and represent numbers up to 1000 using a variety of concrete and pictorial models, and numerals.', 'drop': []},
        'concrete_models': {'clause': 'concrete', 'medium': 'interactive', 'competency': 'Recognize and represent numbers up to 1000 using a variety of concrete and pictorial models, and numerals.', 'drop': [], 'note': 'place_value_blocks_set is served'},
        'pictorial_models': {'clause': 'pictorial models', 'medium': 'visual', 'competency': 'Recognize and represent numbers up to 1000 using a variety of concrete and pictorial models, and numerals.', 'drop': []},
    },
    'mat_g2_na_q1_7': {
        'illustrate_addition': {'clause': 'Illustrate addition', 'medium': 'visual', 'competency': "Illustrate addition of 2-digit and 1-digit numbers as 'counting up' on the number line.", 'drop': ['error_detect', 'cloze', 'mcq']},
    },
    'mat_g2_na_q2_5': {
        'in_pictures': {'clause': 'in pictures', 'medium': 'visual', 'competency': 'Solve problems (given orally or in pictures) involving subtraction where both numbers are less than 100, with and without regrouping.', 'drop': ['error_detect', 'true_false', 'cloze', 'mcq'], 'note': "R-3 composed the sister clause on mat_g1_na_q4_6 to >= 50% pictures on the owner's ruling, and three blind Attesters judged it unmet; ruling 1 alone would accept a worded story."},
    },
    'mat_g2_na_q3_0': {
        'concrete_objects': {'clause': 'concrete objects', 'medium': 'interactive', 'competency': "Count the number of concrete objects in a group by repeated addition and create equal groups, using language such as '5 groups of 3' and '5 threes'.", 'drop': ['error_detect', 'true_false'], 'note': 'array_grid_set: the pupil forms the equal groups'},
    },
    'mat_g2_na_q3_1': {
        'illustrate_multiplication': {'clause': 'Illustrate', 'medium': 'visual', 'competency': 'Illustrate and write multiplication as repeated addition, using a variety of concrete and pictorial models and numerals, and using groups of equal quantities, arrays, counting by multiples, and equal jumps on a number line.', 'drop': ['error_detect', 'true_false']},
        'concrete_model': {'clause': 'concrete', 'medium': 'interactive', 'competency': 'Illustrate and write multiplication as repeated addition, using a variety of concrete and pictorial models and numerals, and using groups of equal quantities, arrays, counting by multiples, and equal jumps on a number line.', 'drop': ['error_detect', 'true_false'], 'note': 'array_grid_set'},
        'pictorial_model': {'clause': 'pictorial models', 'medium': 'visual', 'competency': 'Illustrate and write multiplication as repeated addition, using a variety of concrete and pictorial models and numerals, and using groups of equal quantities, arrays, counting by multiples, and equal jumps on a number line.', 'drop': ['error_detect', 'true_false']},
    },
    'mat_g2_na_q3_4': {
        'illustrate_division': {'clause': 'Illustrate division', 'medium': 'visual', 'competency': 'Illustrate division through equal distribution of a number of objects into several groups.', 'drop': ['error_detect', 'true_false', 'cloze'], 'note': "mcq is kept: it is the only formatter that serves this node's declared word_problem context. Dropping it failed every word_problem seed (caught by §2I, not §2J)."},
    },
    'mat_g2_na_q4_0': {
        'represent': {'clause': 'Represent', 'medium': 'visual', 'competency': 'Represent and identify unit fractions with denominators 2, 3, 4, 5, 6, and 8.', 'drop': []},
    },
    'mat_g2_na_q4_3': {
        'represent': {'clause': 'Represent', 'medium': 'visual', 'competency': 'Represent and identify similar fractions with denominators 2, 3, 4, 5, 6, and 8 using groups of objects, fraction charts, fraction tiles, and the number line.', 'drop': []},
    },
    'mat_g2_mg_q1_0': {
        'represent': {'clause': 'Represent', 'medium': 'visual', 'competency': 'Represent and describe circles, half circles and quarter circles.', 'drop': []},
    },
    'mat_g3_mg_q1_0': {
        'illustrate_area_with_tiles': {'clause': 'Illustrate', 'medium': 'visual', 'competency': 'Illustrate and estimate the area of a square or rectangle using square tile units.', 'drop': ['cloze', 'mcq']},
    },
    'mat_g3_na_q1_0': {
        'represent': {'clause': 'Represent', 'medium': 'visual', 'competency': 'Represent numbers up to 10 000 using pictorial models and numerals.', 'drop': []},
        'pictorial_models': {'clause': 'pictorial models', 'medium': 'visual', 'competency': 'Represent numbers up to 10 000 using pictorial models and numerals.', 'drop': []},
    },
    'mat_g3_na_q4_6': {
        'represent': {'clause': 'Represent', 'medium': 'visual', 'competency': 'Represent fractions that are equal to one and greater than one using models.', 'drop': []},
        'models': {'clause': 'models', 'medium': 'visual', 'competency': 'Represent fractions that are equal to one and greater than one using models.', 'drop': []},
    },
    'mat_g3_na_q4_7': {
        'models': {'clause': 'models', 'medium': 'visual', 'competency': 'Add and subtract similar fractions using models.', 'drop': []},
    },
}

# node_id -> {requirement id -> {"clause", "medium", "competency", "owed": <what to build>}}
# Ruling 16 owes each of these a build. This list may only shrink.
DEBT: Dict[str, Dict[str, Dict]] = {
    'mat_g1_na_q1_6': {
        'concrete_materials': {'clause': 'concrete materials', 'medium': 'interactive', 'competency': 'Compose and decompose numbers up to 10 using concrete materials (e.g., 5 is 5 and 0; 4 and 1; 3 and 2; 2 and 3; 1 and 4; 0 and 5).', 'owed': 'a counters manipulative the pupil splits into two parts; today every item is MCQ (60/60)'},
    },
    'mat_g1_na_q1_7': {
        'concrete': {'clause': 'concrete', 'medium': 'interactive', 'competency': "Illustrate addition of numbers with sums up to 20 using a variety of concrete and pictorial models and describes addition as 'counting up,' and 'putting together'.", 'owed': 'a counters manipulative the pupil puts together or counts up with; number_line_set is interactive but not a manipulative (ruling 12)'},
    },
    'mat_g1_na_q1_8': {
        'illustrate': {'clause': 'Illustrate', 'medium': 'visual', 'competency': 'Illustrate by applying the following properties of addition, using sums up to 20: the sum of zero and any number is equal to the number, and changing the order of the addends does not change the sum.', 'owed': "a visual for the zero and order properties of addition; no visual formatter serves this node's items (0/60)"},
    },
    'mat_g1_na_q2_5': {
        'concrete_pictorial': {'clause': 'concrete and pictorial models', 'medium': 'interactive', 'competency': 'Add numbers with sums up to 100 without regrouping, using a variety of concrete and pictorial models for 2-digit and 1-digit numbers, and 2-digit and 2-digit numbers.', 'owed': 'a blocks or counters manipulative for 2-digit addition without regrouping'},
    },
    'mat_g1_na_q3_0': {
        'concrete_pictorial': {'clause': 'concrete and pictorial models', 'medium': 'interactive', 'competency': "Illustrate subtraction involving numbers up to 20 using a variety of concrete and pictorial models, and describes subtraction as 'taking away'.", 'owed': 'a counters manipulative the pupil takes away from'},
    },
    'mat_g1_na_q3_4': {
        'concrete_models': {'clause': 'concrete', 'medium': 'interactive', 'competency': 'Subtract numbers where both numbers are less than 100 using concrete and pictorial models, without regrouping: 2-digit minus 1-digit numbers, and 2-digit minus 2-digit numbers.', 'owed': 'a blocks manipulative for 2-digit subtraction without regrouping'},
    },
    'mat_g2_na_q1_10': {
        'illustrate_properties': {'clause': 'Illustrate', 'medium': 'visual', 'competency': 'Illustrate and apply the following properties of addition using sums up to 1000: the sum of zero and any number is equal to the number, changing the order of the addends does not change the sum, and changing the grouping of the addends does not change the sum.', 'owed': 'a visual for the zero, order and grouping properties of addition; 0/60 visual today'},
    },
    'mat_g2_na_q2_3': {
        'illustrate_subtraction': {'clause': 'Illustrate subtraction', 'medium': 'visual', 'competency': 'Illustrate subtraction of 2-digit by 1-digit on the number line and as an inverse of addition.', 'owed': 'a number-line visual for 2-digit minus 1-digit subtraction that this node can serve; 0/60 visual today'},
    },
    'mat_g2_na_q3_5': {
        'illustrate_and_write': {'clause': 'Illustrate and write', 'medium': 'visual', 'competency': 'Illustrate and write division expressions using a variety of concrete and pictorial models and numerals, in modelling division as equal sharing or formation of equal groups of objects, and repeated subtraction.', 'owed': 'a visual for the repeated-subtraction and expression variants; dropping text crashes 28/60 seeds, keeping MCQ leaves 23/60 visual'},
        'concrete_and_pictorial_models': {'clause': 'concrete and pictorial models', 'medium': 'interactive', 'competency': 'Illustrate and write division expressions using a variety of concrete and pictorial models and numerals, in modelling division as equal sharing or formation of equal groups of objects, and repeated subtraction.', 'owed': 'as above, plus an interactive sharing manipulative'},
        'modelling_division': {'clause': 'modelling division', 'medium': 'visual', 'competency': 'Illustrate and write division expressions using a variety of concrete and pictorial models and numerals, in modelling division as equal sharing or formation of equal groups of objects, and repeated subtraction.', 'owed': 'as above'},
    },
    'mat_g2_mg_q1_2': {
        'draw_effect': {'clause': 'draw the effect', 'medium': 'interactive', 'competency': 'Describe and draw the effect of one-direction multi-step slide (or translation) in basic shapes and figures.', 'owed': 'a grid on which the pupil slides a shape (ruling 16); 60/60 MCQ today'},
    },
    'mat_g3_mg_q1_4': {
        'concrete_model_depiction': {'clause': 'using models', 'medium': 'visual', 'competency': 'Recognize, using models, and draws a point, line, line segment, and ray.', 'owed': 'geometry_figure coverage for every object kind; dropping MCQ fails 41/60 seeds'},
        'draw_geometric_object': {'clause': 'draws', 'medium': 'interactive', 'competency': 'Recognize, using models, and draws a point, line, line segment, and ray.', 'owed': 'an interactive canvas on which the pupil draws a point, line, segment or ray'},
    },
    'mat_g3_mg_q1_5': {
        'draw_line_relationships': {'clause': 'draw', 'medium': 'interactive', 'competency': 'Recognize and draw parallel, intersecting, and perpendicular lines.', 'owed': 'an interactive canvas for drawing parallel, intersecting and perpendicular lines'},
    },
    'mat_g3_mg_q1_6': {
        'draw_segment_of_given_length': {'clause': 'draw', 'medium': 'interactive', 'competency': 'Identify and draw line segments of equal length using a ruler.', 'owed': 'an interactive ruler on which the pupil draws a segment of a given length'},
    },
    'mat_g3_mg_q4_0': {
        'draw': {'clause': 'draw', 'medium': 'interactive', 'competency': 'Describe and draw the effect of a two-direction multi-step slide (or translation) in basic shapes and figures.', 'owed': 'a grid on which the pupil slides a shape in two directions'},
    },
    'mat_g3_mg_q4_1': {
        'drawing_the_line_of_symmetry': {'clause': 'drawing the line of symmetry', 'medium': 'interactive', 'competency': 'Identify shapes or figures that show line symmetry by drawing the line of symmetry.', 'owed': 'an interactive figure on which the pupil draws the line of symmetry'},
    },
    'mat_g3_na_q3_1': {
        'illustrate_and_apply_properties_of_multiplication': {'clause': 'Illustrate and apply properties of multiplication', 'medium': 'visual', 'competency': 'Illustrate and apply properties of multiplication for the 6, 7, 8, and 9 multiplication tables: one multiplied by any number is equal to the number; zero multiplied by any number is zero; changing the order of the numbers being multiplied does not change the product; changing the grouping of the numbers being multiplied does not change the product; and multiplying the sum of two addends by a number is the same as the sum of the products of a number by each addend.', 'owed': 'a visual for the properties of multiplication; 0/60 visual today'},
    },
    'mat_g3_na_q4_0': {
        'illustrate_division': {'clause': 'Illustrate division', 'medium': 'visual', 'competency': 'Illustrate division through equal jumps on the number line and as inverse of multiplication.', 'owed': 'a number-line visual for division as equal jumps that this node can serve; 0/60 visual today'},
    },
}

# node_id -> {requirement id -> {"clause", "reason"}}
EXEMPT: Dict[str, Dict[str, Dict]] = {}


def dropped_formatters(node_id: str) -> Tuple[str, ...]:
    """The text formatters ruling 15 removes from this node, across all its composed clauses."""
    out: List[str] = []
    for entry in COMPOSED.get(node_id, {}).values():
        for fmt in entry.get("drop", ()):
            if fmt not in out:
                out.append(fmt)
    return tuple(out)


def compose_for_node(node_id: str, formatters: Iterable[str]) -> List[str]:
    """
    Apply ruling 15 to a node's candidate formatters, preserving order.

    Raises nothing and never refills: if dropping leaves an item with no formatter, the
    caller's own "no compatible formatters" error fires, naming the node. That is a
    composition defect to fix in the table, never a case to paper over here.
    """
    drop = set(dropped_formatters(node_id))
    return [f for f in formatters if f not in drop]


def classification(node_id: str, req_id: str) -> str | None:
    """Which list classifies (node, requirement), or None if unclassified."""
    for name, table in (("COMPOSED", COMPOSED), ("DEBT", DEBT), ("EXEMPT", EXEMPT)):
        if req_id in table.get(node_id, {}):
            return name
    return None
