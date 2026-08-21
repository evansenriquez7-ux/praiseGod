"""
Generated: (node, formatter) pairs the orchestrator always refuses.

DO NOT EDIT BY HAND. Regenerate with:
    PYTHONPATH=. .venv/bin/python3 -m scripts.regen_formatter_exclusions

Why this exists
---------------
`get_node_formatters()` unions COMPATIBILITY across a node's DNAs and nothing narrowed
it per node, so a node advertised whatever any of its DNAs could do whether or not the
orchestrator would serve it. Measured 2026-08-21: 228 of 690 (node, formatter) pairs
across 86 of 151 nodes were refused, and the Lab builds its menu from that list, so a
third of the offerings raised when a user picked them.

Derived EMPIRICALLY rather than computed. Three separate attempts to model the
orchestrator's eligibility rules statically all drifted from it -- the last scored
646/690 with 43 FALSE REFUSALS, i.e. it would have stripped formatters that demonstrably
work, because the numeric filter keys on the values actually generated rather than on the
node's declared ceiling. Asking the orchestrator is the only thing that cannot drift.

Every pair below was verified refused at ALL of 12 seeds (11, 23, 42, 57, 64, 78, 91,
103, 118, 127, 555, 999), so none is a seed-dependent false alarm. §2B keeps this file
honest: if a pair here becomes servable, or a new unservable pair appears, §2B fails.

Note: after narrowing, 33 nodes are left with exactly ONE formatter. That is not caused
by this file -- those nodes only ever had one servable formatter and the rest were
phantom offerings -- but it is thin variety and is recorded in the hardening ledger as a
content finding in its own right.
"""

from typing import Dict, List

NODE_FORMATTER_EXCLUSIONS: Dict[str, List[str]] = {
    'mat_g1_dp_q3_0': ['fill_in_table', 'pictograph_read', 'pictograph_set', 'table_read'],
    'mat_g1_dp_q3_1': ['fill_in_table', 'mcq', 'pictograph_read', 'table_read'],
    'mat_g1_dp_q3_2': ['fill_in_table', 'mcq', 'pictograph_set', 'table_read'],
    'mat_g1_dp_q3_3': ['mcq', 'pictograph_read', 'pictograph_set', 'table_read'],
    'mat_g1_mg_q1_1': ['cloze', 'ordering', 'sort_order', 'true_false'],
    'mat_g1_mg_q2_0': ['cloze', 'mcq'],
    'mat_g1_mg_q2_1': ['cloze', 'mcq'],
    'mat_g1_mg_q2_2': ['ruler_measure'],
    'mat_g1_mg_q4_1': ['cloze', 'mcq'],
    'mat_g1_mg_q4_2': ['calendar_read'],
    'mat_g1_mg_q4_3': ['cloze', 'mcq'],
    'mat_g1_mg_q4_4': ['calendar_read'],
    'mat_g1_na_q1_1': ['number_line_read', 'number_line_set', 'place_value_blocks_read', 'place_value_blocks_set'],
    'mat_g1_na_q1_2': ['cloze', 'mcq', 'true_false'],
    'mat_g1_na_q1_3': ['ordering', 'sort_order'],
    'mat_g1_na_q1_4': ['cloze', 'mcq', 'true_false'],
    'mat_g1_na_q1_7': ['cloze', 'emoji_pictorial', 'error_detect', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'],
    'mat_g1_na_q1_8': ['cloze', 'emoji_pictorial', 'error_detect', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'],
    'mat_g1_na_q1_9': ['number_bond', 'number_line_read', 'number_line_set'],
    'mat_g1_na_q2_0': ['cloze', 'mcq', 'true_false'],
    'mat_g1_na_q2_2': ['mcq', 'place_value_blocks_read', 'place_value_blocks_set'],
    'mat_g1_na_q2_3': ['place_value_blocks_read'],
    'mat_g1_na_q2_4': ['emoji_pictorial', 'number_bond', 'number_line_read', 'number_line_set'],
    'mat_g1_na_q2_6': ['number_bond', 'number_line_read', 'number_line_set'],
    'mat_g1_na_q3_1': ['balance_scale'],
    'mat_g1_na_q3_2': ['balance_scale'],
    'mat_g1_na_q3_3': ['number_bond', 'number_line_read'],
    'mat_g1_na_q4_1': ['fraction_shade'],
    'mat_g1_na_q4_2': ['fraction_model_read', 'fraction_shade'],
    'mat_g1_na_q4_6': ['peso_money_build', 'peso_money_read'],
    'mat_g2_dp_q3_0': ['fill_in_table', 'mcq', 'pictograph_set', 'table_read'],
    'mat_g2_dp_q3_1': ['fill_in_table', 'mcq', 'pictograph_set', 'table_read'],
    'mat_g2_mg_q2_0': ['cloze', 'mcq'],
    'mat_g2_mg_q2_1': ['ruler_measure'],
    'mat_g2_mg_q2_2': ['ruler_measure'],
    'mat_g2_mg_q2_3': ['ruler_measure'],
    'mat_g2_mg_q4_0': ['cloze', 'mcq'],
    'mat_g2_mg_q4_1': ['cloze', 'mcq'],
    'mat_g2_mg_q4_2': ['clock_read', 'clock_set'],
    'mat_g2_na_q1_0': ['emoji_pictorial'],
    'mat_g2_na_q1_1': ['number_line_read', 'number_line_set', 'place_value_blocks_read', 'place_value_blocks_set'],
    'mat_g2_na_q1_10': ['cloze', 'emoji_pictorial', 'error_detect', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'],
    'mat_g2_na_q1_2': ['cloze', 'mcq', 'true_false'],
    'mat_g2_na_q1_3': ['emoji_pictorial'],
    'mat_g2_na_q1_4': ['cloze', 'mcq', 'true_false'],
    'mat_g2_na_q1_6': ['mcq', 'place_value_blocks_read', 'place_value_blocks_set'],
    'mat_g2_na_q1_7': ['emoji_pictorial', 'number_bond'],
    'mat_g2_na_q1_8': ['emoji_pictorial', 'number_bond', 'number_line_read', 'number_line_set'],
    'mat_g2_na_q1_9': ['emoji_pictorial'],
    'mat_g2_na_q2_2': ['emoji_pictorial', 'number_bond', 'number_line_read', 'number_line_set', 'peso_money_build', 'peso_money_read'],
    'mat_g2_na_q2_5': ['number_bond', 'number_line_read'],
    'mat_g2_na_q2_6': ['emoji_pictorial'],
    'mat_g2_na_q2_7': ['emoji_pictorial', 'number_bond', 'number_line_read'],
    'mat_g2_na_q3_3': ['array_grid_read', 'array_grid_set'],
    'mat_g2_na_q3_7': ['balance_scale'],
    'mat_g2_na_q3_9': ['array_grid_read', 'array_grid_set'],
    'mat_g2_na_q4_2': ['fraction_model_read', 'fraction_shade'],
    'mat_g2_na_q4_5': ['fraction_model_read', 'fraction_shade'],
    'mat_g3_dp_q3_1': ['bar_chart_read'],
    'mat_g3_dp_q3_2': ['bar_chart_set'],
    'mat_g3_dp_q3_3': ['bar_chart_set'],
    'mat_g3_mg_q1_1': ['grid_area'],
    'mat_g3_mg_q1_2': ['grid_area'],
    'mat_g3_mg_q1_3': ['grid_area'],
    'mat_g3_mg_q1_6': ['ruler_measure'],
    'mat_g3_mg_q2_2': ['ordering', 'sort_order', 'true_false'],
    'mat_g3_mg_q2_5': ['ordering', 'sort_order', 'true_false'],
    'mat_g3_na_q1_0': ['cloze', 'mcq', 'true_false'],
    'mat_g3_na_q1_1': ['number_line_read', 'number_line_set', 'place_value_blocks_read', 'place_value_blocks_set'],
    'mat_g3_na_q1_3': ['mcq', 'place_value_blocks_read', 'place_value_blocks_set'],
    'mat_g3_na_q1_5': ['ordering', 'sort_order'],
    'mat_g3_na_q1_6': ['cloze', 'mcq', 'true_false'],
    'mat_g3_na_q2_1': ['emoji_pictorial'],
    'mat_g3_na_q2_2': ['cloze', 'emoji_pictorial', 'error_detect', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'],
    'mat_g3_na_q2_3': ['emoji_pictorial', 'number_bond', 'number_line_read', 'number_line_set'],
    'mat_g3_na_q2_4': ['emoji_pictorial'],
    'mat_g3_na_q2_5': ['emoji_pictorial'],
    'mat_g3_na_q3_1': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'true_false'],
    'mat_g3_na_q3_2': ['array_grid_read', 'array_grid_set'],
    'mat_g3_na_q3_3': ['array_grid_read', 'array_grid_set'],
    'mat_g3_na_q3_4': ['array_grid_read', 'array_grid_set'],
    'mat_g3_na_q4_2': ['balance_scale'],
    'mat_g3_na_q4_3': ['array_grid_read', 'array_grid_set'],
    'mat_g3_na_q4_5': ['array_grid_read', 'array_grid_set'],
    'mat_g3_na_q4_6': ['fraction_model_read', 'fraction_shade'],
}
