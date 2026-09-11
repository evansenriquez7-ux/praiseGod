"""
Practice Generation — Capability Contract Validator (§6)

The problem this solves
-----------------------
`registry.py`'s `_parse_competency_bounds` is ~1,300 lines of keyword matching that
*infers* machine bindings from English competency prose ("count by 2s" -> skip_interval,
"capacit" -> measurement_type). Four of the five known defect shapes are that inference
guessing wrong: a key consumed but never bound, one text match too broad, a formatter
gated off the node that needs it, a boundary defined twice. For 151 nodes this has been
hand-patched node by node. Branch count grows with nodes and *collisions* grow faster,
so it does not survive grade 4, let alone 12.

The fix is to stop inferring. Each node **declares** what its competency requires, in
`data/skeletons/vocab_annotation.json` (the hand-authored source; the knowledge graph is
a build artifact and anything typed into it dies on the next rebuild). This module then
checks the declaration against both the curriculum text and the pipeline.

Three checks, and the first two are what keep the declaration honest
-------------------------------------------------------------------
§6A **provenance** — every `clause` is a literal substring of the node's own `competency`.
    Blocks *invention*: a requirement the curriculum never states cannot be declared.

§6B **coverage** — every content word of `competency` appears in at least one `clause`.
    Blocks *omission*, which is the loophole that would otherwise gut this whole design:
    an agent that cannot render "draw" could simply not declare "draw", and §6C would
    pass trivially. Coverage forces the declaration to account for every word the
    curriculum wrote.

    Together, §6A and §6B make the clauses *tile* the competency — which is AGENTS.md
    Content Rule 3 ("nothing beyond the curriculum's explicit scope, nothing less than
    its full scope") enforced mechanically rather than by review.

§6C **required ⊆ provided** — every declared capability maps to something the node's
    reachable (DNA, formatter, variant) space can actually produce. A capability with no
    provider is not a warning and not a judgment call: it is a named failure that says
    which node, which clause, and what to build. That message is the point of this module
    — it converts "an agent decided this node was too hard" into a work item.

No graceful fallbacks (AGENTS.md Protocol 3). A node with no `requires` block is a loud
failure, never a skip — `if "requires" not in node: continue` is precisely the bug that
let 94 non-PASS judgment reviews escape every content check.

Two phases, one seam
--------------------
§6A–§6E need nothing but the knowledge graph, the declarations and the provider table,
so they run in Phase 1 — the fast, artifact-free band that the fix-until-green loop can
re-run after every edit. §6F–§6H read `validation_reports/attestation/`, an artifact an
agent has to author first, so they run in Phase 2. `validate_capability_provision` and
`validate_capability_attestation` are those two halves; `CHECK_PHASE` records which
§-ref belongs to which, and two gates (`capability_phase_boundary_6`,
`capability_phase_partition_6`) keep the halves honest. See the block above
`CHECK_PHASE` for why the boundary is artifact-dependence and not "needs an LLM".
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Set

from backend.app.practice_gen.compatibility import (
    COMPATIBILITY,
    VARIANTS_BY_DNA,
    get_variants_for_dna,
    is_variant_available_at,
    node_grade_quarter,
)
from backend.app.practice_gen.validation._manifest import (
    CHECK_PHASE as _MANIFEST_CHECK_PHASE,
)

# §8 inventory: the assertions this module can independently fail on. Each must be
# proven by a mutation naming it in `Mutation.asserts`, or excused in
# validate_coverage.UNPROVEN_ASSERTIONS with a reason and a date.
# This module returns errors and prints nothing; run_all reports the group under
# `capability_contract` -- once per PHASE, same label, since it is one rollup for one
# contract. The sub-assertions are what a mutation must name: §6 is eight refs deep
# across two phases, and one mutation on the rollup would mark all of them proven.
# The last two are the seam itself -- see the CHECK_PHASE block near the bottom.
ASSERTIONS = (
    "capability_provenance_6A",
    "capability_orphan_provider_6A",
    "capability_coverage_6B",
    "capability_provision_6C",
    "capability_generic_formatter_6D",
    "capability_nondiscriminating_bounds_6E",
    "capability_unattested_6F",
    "capability_contradicted_6F",
    "capability_stale_attestation_6F",
    "capability_attestation_options_recorded_6F",
    "attester_reasoning_skeleton_6G",
    "attester_evidence_6G",
    "attester_plurality_6H",
    "capability_declarations_in_sync_6",
    "capability_phase_boundary_6",
    "capability_phase_partition_6",
    "capability_contract",   # run_all's rollup print for the stage
)
from backend.app.practice_gen.registry import (
    NODE_TO_DNA,
    get_all_node_ids,
    get_node_competency_bounds,
    get_node_info,
)

# Function words that carry no requirement. Kept deliberately generous: a word that
# belongs here is one no generator could ever be asked to "produce". Anything
# contentful must be covered by a clause, or listed in the node's own
# `requires_ignore` where the omission is visible in review and in the diff.
_STOPWORDS: Set[str] = {
    "a", "an", "and", "or", "the", "of", "to", "in", "on", "for", "with", "by", "as",
    "at", "from", "into", "up", "down", "that", "this", "these", "those", "is", "are",
    "be", "been", "such", "according", "using", "use", "used", "including", "includes",
    "include", "variety", "appropriate", "given", "e", "g", "i", "eg", "ie", "etc",
    "than", "then", "it", "its", "their", "them", "other", "others", "also", "may",
    "can", "will", "shall", "each", "any", "all", "both", "either", "neither",
}

# The curriculum-to-pipeline interface. A declared capability id is *provided* when one
# of these concrete artifacts is reachable for the node. This table is deliberately
# explicit rather than inferred -- inference is the thing this module exists to replace.
#
#   variants: (variant_key, variant_value) pairs; provided if the node has a DNA whose
#             VARIANTS_BY_DNA[dna][key] contains value.
#   formatters: formatter names; provided if the node has a DNA whose COMPATIBILITY[dna]
#             lists one of them.
#
# A capability absent from this table has NO provider, which is the correct and useful
# answer for anything the pipeline cannot yet do. Do not add an entry to silence a
# failure -- add one only when the artifact genuinely exists.
CAPABILITY_PROVIDERS: Dict[str, Dict[str, List[Any]]] = {
    # 'draw_line_relationships' was registered here with task_type=draw_construct.
    # A blind Attester (Rule 1), shown the clause "draw" and ten rendered student-path
    # samples with no node id and no knowledge that an entry existed, ruled NOT_PROVIDED:
    #   "No item asks the student to produce anything; all ten are four-option MCQs with
    #    no drawing surface, canvas, or visual payload. The three items that mention
    #    drawing use drawing only as narrative framing and still require selecting a name
    #    or description, which for a Grade 3 constructive verb is not the same act as
    #    drawing."
    # draw_construct renders MCQs *about* drawing technique. That is a real variant and it
    # is genuinely reachable -- which is exactly why §6D cannot catch it and why Rule 9
    # requires an Attester. Per Rule 9 the honest move is to leave the capability unmapped
    # and build the thing, so mat_g3_mg_q1_5 now reports its missing "draw" (Tick F).
    # Do not re-register this without an Attester verdict of PROVIDED on a rendered sample.
    #
    # A sibling entry 'draw_lines' survived that removal, claiming the same variant under
    # a name NO node requires. Nothing reported it: every §6 check is driven by a node's
    # `requires`, so an entry nothing requires is never read, never attested and never
    # contradicted -- while sitting ready to satisfy the first future node whose
    # competency happens to extract that id. Removed 2026-09-10 together with
    # `capability_orphan_provider_6A`, the gate that would have named it.
    # Required by mat_g1_na_q1_6 alone. Was a multiplication-table variant that makes no claim
    # about this clause; a blind Attester ruled it NOT_PROVIDED and §6F
    # enforced it as CONTRADICTED. Now points at the artifact that renders
    # exactly what the clause names.
    '0_and_5': {'variants': [('pair', '0 and 5'), ('pair', 'all ways to make 5')]},
    '10_100_1000': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    # Required by mat_g1_na_q1_6 alone. Was a multiplication-table variant that makes no claim
    # about this clause; a blind Attester ruled it NOT_PROVIDED and §6F
    # enforced it as CONTRADICTED. Now points at the artifact that renders
    # exactly what the clause names.
    '1_and_4': {'variants': [('pair', '1 and 4'), ('pair', 'all ways to make 5')]},
    '1_digit_number': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '1_digit_number_with_remainder': {'variants': [('remainder', 'with_remainder')], 'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '1_digit_number_without_remainder': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '1_to_2_digit_factors': {'variants': [('table', '2')], 'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '1_to_2_digit_numbers': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '1_to_2_step': {'variants': [('table', '2')], 'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '1st': {'formatters': ['cloze', 'mcq'], 'bounds': ['ordinal_range', 'max_ordinal']},
    # Required by mat_g1_na_q1_6 alone. Was a multiplication-table variant that makes no claim
    # about this clause; a blind Attester ruled it NOT_PROVIDED and §6F
    # enforced it as CONTRADICTED. Now points at the artifact that renders
    # exactly what the clause names.
    '2_and_3': {'variants': [('pair', '2 and 3'), ('pair', 'all ways to make 5')]},
    '2_digit_by_1_digit': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '2_digit_minus_1_digit': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '2_digit_minus_2_digit': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '2_digit_numbers': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '2_to_3_digit_by_1_digit': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '2_to_3_digit_factors': {'variants': [('table', '2'), ('table', '3')], 'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '2_to_3_digit_numbers': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '2_to_4_digit_by_leading_non_zero': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '2_to_4_digit_numbers': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '2nd': {'formatters': ['cloze', 'mcq'], 'bounds': ['ordinal_range', 'max_ordinal']},
    # Required by mat_g1_na_q1_6 alone. Was a multiplication-table variant that makes no claim
    # about this clause; a blind Attester ruled it NOT_PROVIDED and §6F
    # enforced it as CONTRADICTED. Now points at the artifact that renders
    # exactly what the clause names.
    '3_and_2': {'variants': [('pair', '3 and 2'), ('pair', 'all ways to make 5')]},
    '3_dimensional_objects': {'variants': [('concept_type', 'straight_curved')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '3_to_4_numbers': {'variants': [('num_operands', 'three_terms'), ('num_operands', 'four_terms')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '3rd': {'formatters': ['cloze', 'mcq'], 'bounds': ['ordinal_range', 'max_ordinal']},
    # Required by mat_g1_na_q1_6 alone. Was a multiplication-table variant that makes no claim
    # about this clause; a blind Attester ruled it NOT_PROVIDED and §6F
    # enforced it as CONTRADICTED. Now points at the artifact that renders
    # exactly what the clause names.
    '4_and_1': {'variants': [('pair', '4 and 1'), ('pair', 'all ways to make 5')]},
    '4_digit_number': {'formatters': ['cloze', 'mcq', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '5_groups_of_3': {'variants': [('table', '3'), ('table', '5')], 'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    # Required by mat_g1_na_q1_6 alone. Was a multiplication-table variant that makes no claim
    # about this clause; a blind Attester ruled it NOT_PROVIDED and §6F
    # enforced it as CONTRADICTED. Now points at the artifact that renders
    # exactly what the clause names.
    '5_is_5_and_0': {'variants': [('pair', '5 and 0'), ('pair', 'all ways to make 5')]},
    '5_threes': {'variants': [('table', '5')], 'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '6_7_8_9': {'variants': [('table', '6_7_8_9'), ('tables', '6'), ('tables', '7'), ('tables', '8'), ('tables', '9')], 'formatters': ['array_grid_read', 'array_grid_set', 'balance_scale', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    '6_7_8_and_9_multiplication_tables': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'add': {'variants': [('operation', 'add_subtract')], 'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'fraction_model_read', 'fraction_shade', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'add_numbers': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'addends': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'addition': {'variants': [('operation', 'add')], 'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'peso_money_build', 'peso_money_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'addition_and_subtraction': {'variants': [('operation_mix', 'mixed_add_sub')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'addition_of_money': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'addition_of_numbers': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'addition_subtraction_expression': {'formatters': ['balance_scale', 'cloze', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'addition_subtraction_sentences': {'variants': [('operation', 'addition_subtraction')], 'formatters': ['balance_scale', 'cloze', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'am_and_pm': {'formatters': ['clock_read', 'clock_set', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'amounts_less_than_100': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'an_object': {'variants': [('measurement_type', 'mass')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'analog_clock': {'formatters': ['clock_read', 'clock_set', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'apply_properties': {'variants': [('task_type', 'properties')], 'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'applying': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'area_attribute': {'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'area_formula_expression': {'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'array': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'associative_property': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'balance_scale': {'variants': [('unit', 'l')], 'formatters': ['cloze', 'mcq', 'ordering', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'basic_figures': {'variants': [('concept', 'slide_translation')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'basic_shapes': {'variants': [('concept', 'slide_translation')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'basic_shapes_and_figures': {'variants': [('concept', 'slide_translation')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'between_two_locations': {'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'bills': {'variants': [('denomination_type', 'bills')], 'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'block_or_bar_models': {'formatters': ['cloze', 'mcq', 'number_line_read', 'number_line_set', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'calendar': {'variants': [('task_type', 'day_and_month_calendar')], 'formatters': ['calendar_read', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'capacity_of_a_container': {'variants': [('measurement_type', 'capacity')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'centavo_coins_only': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'centavo_sign': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'centimeters': {'variants': [('unit_type', 'm')], 'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'certain': {'variants': [('scenario_type', 'certain_impossible')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'changing_the_grouping': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'changing_the_order': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'circles': {'variants': [('shape_set', 'extended_with_circles')], 'formatters': ['categorize', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'clockwise': {'variants': [('concept', 'rotation')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'coins': {'variants': [('denomination_type', 'coins')], 'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'collect_data': {'variants': [('experiment_type', 'spinner'), ('experiment_type', 'colored_tiles')], 'formatters': ['cloze', 'error_detect', 'fill_in_table', 'mcq', 'pictograph_read', 'pictograph_set', 'table_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'combination_of_bills_and_coins': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'combined_peso_coins_and_peso_bills': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'commutative_property': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'compare': {'variants': [('operation', 'compare'), ('task_type', 'compare_length_or_distance'), ('task_type', 'compare_pair'), ('task_type', 'measure_compare_or_distance'), ('unit_type', 'm'), ('scenario_type', 'comparative')], 'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq', 'ordering', 'peso_money_build', 'peso_money_read', 'ruler_measure', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'compare_capacities': {'variants': [('task_type', 'compare')], 'formatters': ['cloze', 'mcq', 'ordering', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'compare_masses': {'variants': [('measurement_type', 'mass'), ('task_type', 'compare')], 'formatters': ['cloze', 'mcq', 'ordering', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'compare_shapes': {'variants': [('task_type', 'compare_shapes')], 'formatters': ['categorize', 'cloze', 'mcq', 'ordering', 'shape_board', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'complete': {'variants': [('concept', 'complete_symmetric_figure')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'compose': {'variants': [('task_type', 'compose_decompose'), ('task_type', 'compose_total')], 'formatters': ['balance_scale', 'categorize', 'cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'shape_board', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'compose_figures': {'formatters': ['categorize', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'composite_figures': {'variants': [('shape_set', 'composite_figures')], 'formatters': ['categorize', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'compute_area': {'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'concrete': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'concrete_and_pictorial_models': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    # Required by mat_g1_na_q1_6 alone. Was a multiplication-table variant that makes no claim
    # about this clause; a blind Attester ruled it NOT_PROVIDED and §6F
    # enforced it as CONTRADICTED. Now points at the artifact that renders
    # exactly what the clause names.
    'concrete_materials': {'variants': [('representation', 'concrete_objects')]},
    'concrete_model': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'concrete_model_depiction': {'variants': [('task_type', 'recognize_model')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'concrete_models': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'concrete_objects': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'concrete_pictorial': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'corners_of_a_shape': {'formatters': ['categorize', 'cloze', 'mcq', 'ordering', 'shape_board', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'correct_order': {'formatters': ['calendar_read', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'count': {'variants': [('operation', 'count_sequence')], 'formatters': ['cloze', 'emoji_pictorial', 'fraction_model_read', 'fraction_shade', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'count_backward_from_a_given_number': {'variants': [('direction', 'backward')], 'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'count_forward_from_a_given_number': {'variants': [('direction', 'forward')], 'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'count_multiples': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'count_number_of': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'count_objects_to_a_total': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'counter_clockwise': {'variants': [('concept', 'rotation')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'counting_by_multiples': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'counting_up': {'variants': [('spine', 'counting_up'), ('task_type', 'counting_up')], 'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'create': {'formatters': ['cloze', 'mcq', 'pattern_sequence'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'create_equal_groups': {'variants': [('task_type', 'equal_groups')], 'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'curved_lines': {'variants': [('concept_type', 'straight_curved')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'curved_surfaces': {'variants': [('concept_type', 'straight_curved')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'cut_outs': {'formatters': ['categorize', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'data': {'formatters': ['fill_in_table', 'mcq', 'pictograph_read', 'pictograph_set', 'table_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'data_presented': {'formatters': ['bar_chart_read', 'bar_chart_set'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'data_set': {'formatters': ['bar_chart_read', 'bar_chart_set'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'data_table': {'variants': [('orientation', 'table')], 'formatters': ['bar_chart_read', 'bar_chart_set'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'day_and_month_of_the_year': {'formatters': ['calendar_read', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'days_in_a_week': {'variants': [('calendar_feature', 'days')], 'formatters': ['calendar_read', 'clock_read', 'clock_set', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'days_of_the_week': {'variants': [('calendar_feature', 'days')], 'formatters': ['calendar_read', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'decompose': {'variants': [('task_type', 'compose_decompose'), ('task_type', 'decompose'), ('task_type', 'decompose_pair'), ('task_type', 'name_the_pair')], 'formatters': ['balance_scale', 'categorize', 'cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'place_value_blocks_read', 'place_value_blocks_set', 'shape_board', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'decompose_figures': {'formatters': ['categorize', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'denominations': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'denominators_2_3_4_5_6_8': {'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'derive_area_formula': {'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'describe': {'variants': [('concept', 'slide_translation'), ('scenario_type', 'certain_impossible'), ('task_type', 'describe_position')], 'formatters': ['calendar_read', 'categorize', 'cloze', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'describe_effect': {'variants': [('concept', 'slide_translation')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'describe_position': {'variants': [('task_type', 'describe_position')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'describe_subtraction': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'describes': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'determine': {'formatters': ['calendar_read', 'cloze', 'mcq', 'pattern_sequence', 'peso_money_build', 'peso_money_read', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'determine_digit': {'formatters': ['cloze', 'mcq', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'determine_digit_given_place_value': {'formatters': ['cloze', 'mcq', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'determine_missing_terms': {'formatters': ['cloze', 'mcq', 'pattern_sequence'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'determine_next_term': {'formatters': ['cloze', 'mcq', 'pattern_sequence'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'determine_place_value': {'formatters': ['cloze', 'mcq', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'determine_value': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'determine_value_of_digit': {'formatters': ['cloze', 'mcq', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'difference_between': {'variants': [('task_type', 'explain_difference')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'different': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'different_denominations': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'different_orientation': {'formatters': ['categorize', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'different_size': {'formatters': ['categorize', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'digit_in_3_digit_number': {'formatters': ['cloze', 'mcq', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'digit_of_number': {'formatters': ['cloze', 'mcq', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'distance': {'variants': [('task_type', 'measure_compare_or_distance')], 'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'distances': {'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'distinguish': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'distinguish_shapes': {'formatters': ['categorize', 'cloze', 'mcq', 'ordering', 'shape_board', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'divide': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'divide_numbers': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'divided_by': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'division': {'variants': [('operation', 'multiplication_division')], 'formatters': ['array_grid_read', 'array_grid_set', 'balance_scale', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'division_expressions': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'divisor_2': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'domain_2_digit': {'formatters': ['cloze', 'mcq', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'draw': {'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'draw_effect': {'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'draw_geometric_object': {'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'draw_segment_of_given_length': {'variants': [('unit_type', 'm')], 'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'drawing_the_line_of_symmetry': {'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'duration_of_an_event': {'formatters': ['calendar_read', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'elapsed_time': {'variants': [('task_type', 'elapsed_time')], 'formatters': ['clock_read', 'clock_set', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'equal_distribution': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'equal_jumps': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'equal_jumps_on_a_number_line': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'equal_length': {'variants': [('task_type', 'equal_length')], 'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'equal_sharing': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'equal_to_one': {'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'equally_likely': {'variants': [('scenario_type', 'equally_likely')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'estimate': {'variants': [('task_type', 'estimate'), ('unit_type', 'm')], 'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'ruler_measure', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'estimate_area': {'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'estimate_capacity': {'variants': [('measurement_type', 'capacity'), ('task_type', 'estimate')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'estimate_difference': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'estimate_factors': {'variants': [('task_type', 'estimate')], 'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'estimate_mass': {'variants': [('measurement_type', 'mass'), ('task_type', 'estimate')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'estimate_product': {'variants': [('task_type', 'estimate')], 'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'estimate_quotient': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'even_and_odd_numbers': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'example_1': {'formatters': ['balance_scale', 'cloze', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'example_2': {'variants': [('tables', '2')], 'formatters': ['balance_scale', 'cloze', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'excluding_centavo_coins': {'variants': [('denomination_type', 'coins')], 'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'expanded_form': {'variants': [('strategy', 'expanded_form'), ('task_type', 'expanded_form')], 'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'experiments': {'variants': [('experiment_type', 'die_roll'), ('experiment_type', 'coin_toss')], 'formatters': ['cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    # Required by exactly one node: mat_g2_mg_q4_3, "Identify and *explain* the
    # difference between straight and curved lines, and flat and curved surfaces
    # of 3-dimensional objects." It previously named only 'mcq' + the 27-key
    # shared bounds catch-all -- neither of which makes any claim about
    # explanation -- and a blind Attester ruled it NOT_PROVIDED (§6F
    # CONTRADICTED) because every option was a bare label. geometric_lines now
    # carries task_type='explain_difference' items whose stems ask *why* / *how
    # they differ* and whose options are full explanatory statements.
    'explain': {'variants': [('task_type', 'explain_difference')]},
    'explain_generation': {'formatters': ['cloze', 'mcq', 'pattern_sequence'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'explore_pattern_across_cases': {'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'express_addends': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'expressing_tens_ones': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'extract_area_relationship_from_context': {'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'factors_2_3_4_5_10': {'variants': [('tables', '10'), ('tables', '2'), ('tables', '3'), ('tables', '4'), ('tables', '5')], 'formatters': ['balance_scale', 'cloze', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'fifties': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'figure': {'variants': [('concept', 'complete_symmetric_figure')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'find': {'variants': [('task_type', 'find_perimeter')], 'formatters': ['balance_scale', 'cloze', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'find_missing_number': {'formatters': ['array_grid_read', 'array_grid_set', 'balance_scale', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'fives': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'flat_surfaces': {'variants': [('concept_type', 'straight_curved')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'formation_of_equal_groups': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'fraction_charts': {'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'fraction_notation': {'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'fraction_tiles': {'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'fractions': {'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'give': {'formatters': ['calendar_read', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'given_place_value': {'formatters': ['cloze', 'mcq', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'grams_kilograms_and_or_milligrams': {'variants': [('unit', 'g'), ('unit', 'l')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'greater_than_one': {'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'group': {'variants': [('task_type', 'equal_groups')], 'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'groups_of_equal_quantities': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'groups_of_objects': {'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'half': {'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'half_circles': {'formatters': ['categorize', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'half_hour': {'variants': [('precision', 'half_hour'), ('precision', 'hour')], 'formatters': ['calendar_read', 'clock_read', 'clock_set', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'half_turn': {'variants': [('concept', 'rotation')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'halves': {'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'horizontal': {'variants': [('orientation', 'horizontal')], 'formatters': ['bar_chart_read', 'bar_chart_set'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'horizontal_bar_graph': {'variants': [('orientation', 'horizontal')], 'formatters': ['bar_chart_read', 'bar_chart_set'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'hour': {'variants': [('precision', 'half_hour'), ('precision', 'hour'), ('precision', 'quarter_hour')], 'formatters': ['calendar_read', 'clock_read', 'clock_set', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'hours': {'variants': [('precision', 'hour')], 'formatters': ['clock_read', 'clock_set', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'hours_in_a_day': {'variants': [('precision', 'hour')], 'formatters': ['clock_read', 'clock_set', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'hundred': {'variants': [('precision', 'nearest_hundred')], 'formatters': ['cloze', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'hundreds': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'identify': {'variants': [('operation', 'identify_name'), ('task_type', 'identify_and_measure'), ('task_type', 'identify_name'), ('task_type', 'identify_property'), ('concept', 'line_symmetry'), ('task_type', 'explain_difference')], 'formatters': ['categorize', 'cloze', 'fraction_model_read', 'fraction_shade', 'mcq', 'ruler_measure', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'identify_a_number_relative_to_another': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'identify_equal_length_segments': {'variants': [('task_type', 'equal_length'), ('unit_type', 'm')], 'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'identify_one_less_than_a_number': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'identify_one_more_than_a_number': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'identify_position': {'variants': [('concept', 'rotation')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'identity_property': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'illustrate': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'fraction_model_read', 'fraction_shade', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'illustrate_addition': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'illustrate_and_apply_properties_of_multiplication': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'illustrate_and_write': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'illustrate_area_with_tiles': {'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'illustrate_division': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'illustrate_multiplication': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'illustrate_properties': {'variants': [('task_type', 'properties')], 'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'illustrate_subtraction': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'images': {'formatters': ['cloze', 'mcq', 'pattern_sequence'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'impossible': {'variants': [('scenario_type', 'certain_impossible')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'in_pictures': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'peso_money_build', 'peso_money_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'increasing_decreasing': {'formatters': ['cloze', 'mcq', 'pattern_sequence'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'initial_facing_direction': {'variants': [('concept', 'rotation')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'interpret': {'formatters': ['fill_in_table', 'mcq', 'pictograph_read', 'pictograph_set', 'table_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'interpret_data': {'variants': [('task_type', 'interpret_data')], 'formatters': ['bar_chart_read', 'bar_chart_set'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'intersecting_lines': {'variants': [('concept_type', 'parallel_intersecting_perpendicular')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'inverse_of_addition': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'inverse_of_multiplication': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'involving': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'peso_money_build', 'peso_money_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'involving_subtraction': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'language': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'largest_to_smallest': {'formatters': ['cloze', 'mcq', 'ordering', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'length': {'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'lengths': {'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'less_least_likely': {'variants': [('scenario_type', 'comparative'), ('scenario_type', 'superlative')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'less_than_100': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'less_than_1000': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'less_than_10_000': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'less_than_20': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'letters': {'formatters': ['cloze', 'mcq', 'pattern_sequence'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'letters_example': {'formatters': ['cloze', 'mcq', 'pattern_sequence'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'line': {'variants': [('concept_type', 'point_line_segment_ray')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'line_segment': {'variants': [('concept_type', 'point_line_segment_ray'), ('unit_type', 'm')], 'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'line_symmetry': {'variants': [('concept', 'line_symmetry')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'liters': {'variants': [('unit', 'l')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'liters_and_or_milliliters': {'variants': [('unit', 'l')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'm_or_cm': {'variants': [('unit_type', 'cm'), ('unit_type', 'm')], 'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'measure': {'variants': [('task_type', 'identify_and_measure'), ('task_type', 'measure_compare_or_distance'), ('unit_type', 'm')], 'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'measure_capacity': {'variants': [('measurement_type', 'capacity')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'measure_distance': {'variants': [('unit_type', 'm')], 'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'measure_length': {'variants': [('unit_type', 'm')], 'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'measure_mass': {'variants': [('measurement_type', 'mass')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'measuring_tools': {'variants': [('unit', 'g'), ('unit', 'l'), ('unit_type', 'm')], 'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'measuring_tools_for_capacity': {'variants': [('measurement_type', 'capacity'), ('unit', 'g'), ('unit', 'l')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'meters': {'variants': [('unit_type', 'm')], 'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'milliliters': {'variants': [('unit', 'l')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'minutes': {'variants': [('precision', 'five_minutes')], 'formatters': ['clock_read', 'clock_set', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'minutes_in_an_hour': {'variants': [('precision', 'hour')], 'formatters': ['clock_read', 'clock_set', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'missing_number': {'formatters': ['balance_scale', 'cloze', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'modelling_division': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'models': {'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'money': {'variants': [('task_type', 'give_money')], 'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'peso_money_build', 'peso_money_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'months_in_a_year': {'variants': [('calendar_feature', 'months')], 'formatters': ['calendar_read', 'clock_read', 'clock_set', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'months_of_the_year': {'variants': [('calendar_feature', 'months')], 'formatters': ['calendar_read', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'more_most_likely': {'variants': [('scenario_type', 'comparative'), ('scenario_type', 'superlative')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'moved': {'variants': [('concept', 'rotation')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'multi_step': {'variants': [('concept', 'slide_translation')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'multiples_of_10': {'variants': [('table', '10')], 'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'multiples_of_10_or_100': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'multiplication': {'variants': [('operation', 'multiplication_division')], 'formatters': ['array_grid_read', 'array_grid_set', 'balance_scale', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'multiplication_as_repeated_addition': {'variants': [('task_type', 'repeated_addition')], 'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'multiplication_problems': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'multiplication_tables': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'multiply': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'multiply_numbers': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'multiplying_the_sum_of_two_addends': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'nearest_ten': {'variants': [('precision', 'nearest_ten')], 'formatters': ['cloze', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'next_term': {'formatters': ['cloze', 'mcq', 'pattern_sequence'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'non_standard_units': {'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'not_beyond_1000': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'notations': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'number_line': {'variants': [('fraction_model', 'number_line')], 'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'emoji_pictorial', 'error_detect', 'fraction_model_read', 'fraction_shade', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'number_of': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'number_of_bills': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'number_of_coins': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'number_of_days': {'variants': [('calendar_feature', 'days')], 'formatters': ['calendar_read', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'number_of_weeks': {'variants': [('calendar_feature', 'weeks')], 'formatters': ['calendar_read', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'number_sentence': {'formatters': ['array_grid_read', 'array_grid_set', 'balance_scale', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'numbers': {'variants': [('task_type', 'compose_total')], 'formatters': ['array_grid_read', 'array_grid_set', 'balance_scale', 'cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'ordering', 'pattern_sequence', 'place_value_blocks_read', 'place_value_blocks_set', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'numbers_example': {'formatters': ['cloze', 'mcq', 'pattern_sequence'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'numbers_up_to_20': {'variants': [('tables', '2')], 'formatters': ['balance_scale', 'cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'numeral_form': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'numerals': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'number_line_read', 'number_line_set', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'object': {'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'objects': {'variants': [('concept', 'rotation'), ('task_type', 'describe_position')], 'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'ordering', 'pattern_sequence', 'ruler_measure', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'observing_correct_order_of_operations': {'variants': [('operation_mix', 'mixed_add_sub')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'one_digit_numbers': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'one_direction': {'variants': [('directions', 'one_direction')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'one_multiplied_by_any_number': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'one_variable': {'formatters': ['fill_in_table', 'mcq', 'pictograph_read', 'pictograph_set', 'table_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'operands_2_1_digit': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'operands_2_2_digit': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'order': {'variants': [('operation', 'order'), ('task_type', 'order_sequence')], 'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq', 'ordering', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'order_numbers': {'formatters': ['cloze', 'mcq', 'ordering', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'ordinal_numbers': {'variants': [('task_type', 'identify_ordinal')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'organize_data': {'formatters': ['fill_in_table', 'mcq', 'pictograph_read', 'pictograph_set', 'table_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'outcomes': {'variants': [('scenario_type', 'equally_likely'), ('scenario_type', 'certain_impossible')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'parallel_lines': {'variants': [('concept_type', 'parallel_intersecting_perpendicular')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'parts_of_whole': {'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'pattern': {'formatters': ['cloze', 'mcq', 'pattern_sequence'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'patterns': {'formatters': ['cloze', 'mcq', 'pattern_sequence'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'perimeter': {'variants': [('task_type', 'find_perimeter'), ('task_type', 'identify_and_measure')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'perpendicular_lines': {'variants': [('concept_type', 'parallel_intersecting_perpendicular')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'peso_bills_only': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'peso_coins': {'variants': [('denomination_type', 'coins')], 'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'peso_coins_only': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'peso_sign': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'philippine_currency_symbols': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'php': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'pictograph': {'variants': [('task_type', 'tabular_and_pictograph')], 'formatters': ['fill_in_table', 'mcq', 'pictograph_read', 'pictograph_set', 'table_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'pictorial_model': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'pictorial_models': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'pictures': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'place_value_of_digit': {'formatters': ['cloze', 'mcq', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'plane_figure': {'variants': [('shape', 'square'), ('shape', 'rectangle'), ('shape', 'triangle')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'point': {'variants': [('concept_type', 'point_line_segment_ray')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'position': {'variants': [('task_type', 'identify_position'), ('task_type', 'describe_position')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'present': {'variants': [('task_type', 'present_or_organize')], 'formatters': ['fill_in_table', 'mcq', 'pictograph_read', 'pictograph_set', 'table_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'present_data': {'variants': [('task_type', 'present_data')], 'formatters': ['bar_chart_read', 'bar_chart_set', 'fill_in_table', 'mcq', 'pictograph_read', 'pictograph_set', 'table_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'problems': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'peso_money_build', 'peso_money_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'problems_involving_money': {'variants': [('context', 'word_problem')], 'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'problems_money': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'products_up_to_10_000': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'properties_of_addition': {'variants': [('task_type', 'properties')], 'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'putting_together': {'variants': [('spine', 'putting_together')], 'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'quarter': {'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'quarter_circles': {'formatters': ['categorize', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'quarter_hour': {'variants': [('precision', 'hour'), ('precision', 'quarter_hour')], 'formatters': ['calendar_read', 'clock_read', 'clock_set', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'quarter_turn': {'variants': [('concept', 'rotation')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'quarters': {'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'range_up_to_100': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'raw_data': {'formatters': ['fill_in_table', 'mcq', 'pictograph_read', 'pictograph_set', 'table_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'ray': {'variants': [('concept_type', 'point_line_segment_ray')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'read': {'variants': [('mode', 'read'), ('operation', 'read_write'), ('task_type', 'clock_reading'), ('task_type', 'read_and_write')], 'formatters': ['clock_read', 'clock_set', 'cloze', 'fraction_model_read', 'fraction_shade', 'mcq', 'number_line_read', 'number_line_set', 'peso_money_build', 'peso_money_read', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'read_and_write': {'variants': [('mode', 'read'), ('task_type', 'read_and_write')], 'formatters': ['clock_read', 'clock_set', 'cloze', 'mcq', 'number_line_read', 'number_line_set', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'real_life_situations': {'variants': [('context', 'weather'), ('context', 'coins'), ('context', 'spinners'), ('context', 'colored_objects')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'reason_inductively_from_cases': {'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'recognize': {'formatters': ['cloze', 'mcq', 'number_line_read', 'number_line_set', 'peso_money_build', 'peso_money_read', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'recognize_and_represent': {'formatters': ['cloze', 'mcq', 'number_line_read', 'number_line_set', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'recognize_geometric_object': {'variants': [('task_type', 'recognize_model')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'recognize_line_relationships': {'variants': [('task_type', 'recognize_model')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'rectangle': {'variants': [('shape_set', 'basic_triangles_rectangles_squares')], 'formatters': ['categorize', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'rectangle_figure': {'variants': [('shape', 'rectangle')], 'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'rectangles': {'variants': [('shape', 'rectangle'), ('shape_set', 'basic_triangles_rectangles_squares')], 'formatters': ['categorize', 'cloze', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'regrouping': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'peso_money_build', 'peso_money_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'repeated_addition': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'repeated_subtraction': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'repeating_and_decreasing': {'formatters': ['cloze', 'mcq', 'pattern_sequence'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'repeating_and_increasing': {'formatters': ['cloze', 'mcq', 'pattern_sequence'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'repeating_pattern': {'formatters': ['cloze', 'mcq', 'pattern_sequence'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'repeating_patterns': {'formatters': ['cloze', 'mcq', 'pattern_sequence'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'repetitions': {'formatters': ['cloze', 'mcq', 'pattern_sequence'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'represent': {'variants': [('task_type', 'model_representation')], 'formatters': ['categorize', 'cloze', 'fraction_model_read', 'fraction_shade', 'mcq', 'number_line_read', 'number_line_set', 'place_value_blocks_read', 'place_value_blocks_set', 'shape_board', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'rolling_die': {'variants': [('experiment_type', 'die_roll')], 'formatters': ['cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'round': {'formatters': ['cloze', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'ruler': {'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'scale': {'variants': [('scale_type', 'scale_10'), ('scale_type', 'scale_2'), ('scale_type', 'scale_5'), ('scale_type', 'with_or_without_scale')], 'formatters': ['fill_in_table', 'mcq', 'pictograph_read', 'pictograph_set', 'table_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'several_groups': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'shape_features_as_comparison_basis': {'formatters': ['categorize', 'cloze', 'mcq', 'ordering', 'shape_board', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'shapes_or_figures': {'variants': [('concept', 'line_symmetry')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'sides_of_a_shape': {'formatters': ['categorize', 'cloze', 'mcq', 'ordering', 'shape_board', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'similar_fractions': {'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'simple_2_dimensional_shapes': {'formatters': ['categorize', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'simple_interview': {'formatters': ['fill_in_table', 'mcq', 'pictograph_read', 'pictograph_set', 'table_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'single_bar_graph': {'formatters': ['bar_chart_read', 'bar_chart_set'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'single_bar_graphs': {'formatters': ['bar_chart_read', 'bar_chart_set'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'slide': {'variants': [('concept', 'slide_translation')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'small_number_of_possible_outcomes': {'variants': [('experiment_type', 'coin_toss'), ('experiment_type', 'die_roll')], 'formatters': ['cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'smallest_to_largest': {'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq', 'ordering', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'solve': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'solve_1_step_problems': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'solve_area_problem': {'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'solve_division_problems': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'solve_multiplication_problems': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'solve_problems': {'variants': [('task_type', 'solve_problem'), ('task_type', 'solve_problems_non_standard'), ('unit_type', 'm'), ('context', 'word_problem')], 'formatters': ['bar_chart_read', 'bar_chart_set', 'calendar_read', 'clock_read', 'clock_set', 'cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'peso_money_build', 'peso_money_read', 'ruler_measure', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'solve_problems_involving_addition_and_subtraction': {'variants': [('context', 'word_problem')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'solve_subtraction': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'square': {'variants': [('shape_set', 'basic_triangles_rectangles_squares')], 'formatters': ['categorize', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'square_centimeter': {'variants': [('shape', 'square')], 'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'square_figure': {'variants': [('shape', 'square')], 'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'square_grids': {'formatters': ['categorize', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'square_meter': {'variants': [('shape', 'square'), ('unit', 'square_m')], 'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'square_tile_array': {'variants': [('shape', 'square')], 'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'square_tile_covering': {'variants': [('shape', 'square')], 'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'square_tile_unit': {'variants': [('shape', 'square')], 'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'square_unit_abbreviation': {'variants': [('shape', 'square')], 'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'squares': {'variants': [('shape', 'square'), ('shape_set', 'basic_triangles_rectangles_squares')], 'formatters': ['categorize', 'cloze', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'step_10s': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'step_2s': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'step_5s': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'straight_lines': {'variants': [('concept_type', 'straight_curved')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'sub_2d_1d': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'sub_2d_2d': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'subtract': {'variants': [('operation', 'add_subtract')], 'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'subtract_numbers': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'subtraction_of_money': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'sum': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'sum_up_to_100': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'peso_money_build', 'peso_money_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'sums_up_to_1000': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'peso_money_build', 'peso_money_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'sums_up_to_10000': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'sums_up_to_20': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'symbols': {'formatters': ['cloze', 'mcq', 'ordering', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'symmetric_with_respect_to_a_line': {'variants': [('concept', 'complete_symmetric_figure')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'table': {'variants': [('task_type', 'organize_table')], 'formatters': ['fill_in_table', 'mcq', 'pictograph_read', 'pictograph_set', 'table_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'tables': {'variants': [('orientation', 'table')], 'formatters': ['bar_chart_read', 'bar_chart_set'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'tables_2_3_4_5_10': {'variants': [('table', '2_3_4_5_10')], 'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'tabular_form': {'formatters': ['fill_in_table', 'mcq', 'pictograph_read', 'pictograph_set', 'table_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'taking_away': {'variants': [('spine', 'taking_away')], 'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'tens': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'tens_ones': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'thousand': {'variants': [('precision', 'nearest_thousand')], 'formatters': ['cloze', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'time': {'variants': [('task_type', 'elapsed_time')], 'formatters': ['calendar_read', 'clock_read', 'clock_set', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'timetables': {'formatters': ['clock_read', 'clock_set', 'cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'tools': {'variants': [('task_type', 'measure_tools')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'tossing_coin': {'variants': [('experiment_type', 'coin_toss')], 'formatters': ['cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'translation': {'variants': [('concept', 'slide_translation')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'triangle': {'variants': [('shape_set', 'basic_triangles_rectangles_squares')], 'formatters': ['categorize', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'triangles': {'variants': [('shape', 'triangle'), ('shape_set', 'basic_triangles_rectangles_squares')], 'formatters': ['categorize', 'cloze', 'mcq', 'shape_board'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'twenties': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'two_containers': {'formatters': ['cloze', 'mcq', 'ordering', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'two_digit': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'two_dimensional_shapes': {'formatters': ['categorize', 'cloze', 'mcq', 'ordering', 'shape_board', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'two_direction_multi_step_slide': {'variants': [('concept', 'slide_translation')], 'formatters': ['mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'two_numbers': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'ordering', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'twos': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'unit': {'variants': [('task_type', 'choose_unit')], 'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'unit_fractions': {'variants': [('fraction_type', 'unit_fraction')], 'formatters': ['cloze', 'fraction_model_read', 'fraction_shade', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    # Required by mat_g1_na_q1_6 alone. Was a multiplication-table variant that makes no claim
    # about this clause; a blind Attester ruled it NOT_PROVIDED and §6F
    # enforced it as CONTRADICTED. Now points at the artifact that renders
    # exactly what the clause names.
    'up_to_10': {'variants': [('pair', '7 and 3')]},
    'up_to_100': {'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read', 'number_line_set', 'ordering', 'peso_money_build', 'peso_money_read', 'place_value_blocks_read', 'place_value_blocks_set', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'up_to_1000': {'variants': [('skip_interval', '1'), ('skip_interval', '10'), ('skip_interval', '100')], 'formatters': ['cloze', 'emoji_pictorial', 'mcq', 'number_line_read', 'number_line_set', 'ordering', 'peso_money_build', 'peso_money_read', 'place_value_blocks_read', 'place_value_blocks_set', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'up_to_10000': {'formatters': ['cloze', 'mcq', 'number_line_read', 'number_line_set', 'ordering', 'place_value_blocks_read', 'place_value_blocks_set', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'up_to_100th': {'formatters': ['cloze', 'mcq'], 'bounds': ['ordinal_range', 'max_ordinal']},
    'up_to_10th': {'formatters': ['cloze', 'mcq'], 'bounds': ['ordinal_range', 'max_ordinal']},
    'up_to_20': {'formatters': ['cloze', 'mcq', 'ordering', 'sort_order', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'up_to_20th': {'formatters': ['cloze', 'mcq'], 'bounds': ['ordinal_range', 'max_ordinal']},
    'up_to_2_digits': {'variants': [('number_size', '2_digit')], 'formatters': ['cloze', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'up_to_4_digits': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'up_to_peso_10000': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'use': {'formatters': ['cloze', 'mcq', 'ruler_measure'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'value_of_digit': {'formatters': ['cloze', 'mcq', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'values': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'vertical': {'variants': [('orientation', 'vertical')], 'formatters': ['bar_chart_read', 'bar_chart_set'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'vertical_bar_graph': {'variants': [('orientation', 'vertical')], 'formatters': ['bar_chart_read', 'bar_chart_set'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'vice_versa': {'formatters': ['cloze', 'fill_in_table', 'fraction_model_read', 'fraction_shade', 'mcq', 'ordering', 'pictograph_read', 'pictograph_set', 'sort_order', 'table_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'with_and_without_regrouping': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'with_and_without_remainder': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'with_regrouping': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'without_regrouping': {'formatters': ['cloze', 'emoji_pictorial', 'error_detect', 'mcq', 'number_bond', 'number_line_read', 'number_line_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'without_scale': {'formatters': ['fill_in_table', 'mcq', 'pictograph_read', 'pictograph_set', 'table_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'word_problem_context': {'variants': [('context', 'word_problem')], 'formatters': ['cloze', 'grid_area', 'mcq'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'words': {'formatters': ['cloze', 'mcq', 'number_line_read', 'number_line_set', 'peso_money_build', 'peso_money_read', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'write': {'variants': [('operation', 'read_write'), ('task_type', 'read_and_write')], 'formatters': ['clock_read', 'clock_set', 'cloze', 'fraction_model_read', 'fraction_shade', 'mcq', 'number_line_read', 'number_line_set', 'peso_money_build', 'peso_money_read', 'place_value_blocks_read', 'place_value_blocks_set', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'write_equivalent_expression': {'variants': [('operation', 'equivalent')], 'formatters': ['balance_scale', 'cloze', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'write_multiplication_sentence': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'write_value': {'formatters': ['cloze', 'mcq', 'peso_money_build', 'peso_money_read'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
    'zero_multiplied_by_any_number': {'formatters': ['array_grid_read', 'array_grid_set', 'cloze', 'error_detect', 'mcq', 'true_false'], 'bounds': ['range', 'max_value', 'max_count', 'max_sum', 'max_minuend', 'minuend_max', 'max_product', 'max_result', 'max_total', 'max_subtrahend', 'min_minuend', 'min_subtrahend', 'min_a', 'ordinal_range', 'digit_count', 'operand_digits', 'skip_interval', 'skip_pool', 'denominators', 'table', 'tables', 'max_ordinal', 'factors', 'products', 'minuends', 'subtrahends', 'addends']},
}

def _content_words(text: str) -> List[str]:
    """Lowercased alphanumeric tokens of `text`, minus function words."""
    tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower())
    return [t for t in tokens if t not in _STOPWORDS]


def _validate_provenance(node_id: str, competency: str, requires: List[Dict]) -> List[str]:
    """§6A — a clause the competency does not contain is invented, not declared."""
    errs: List[str] = []
    hay = competency.lower()
    for i, req in enumerate(requires):
        clause = str(req.get("clause", "")).strip()
        if not clause:
            errs.append(
                f"{node_id}: requires[{i}] ({req.get('id')!r}) has no 'clause'. Every "
                f"requirement cites the competency text it comes from."
            )
            continue
        if clause.lower() not in hay:
            errs.append(
                f"{node_id}: requires[{i}] ({req.get('id')!r}) cites clause {clause!r}, "
                f"which does not appear in the node's competency. Declaring a requirement "
                f"the curriculum never states is invention (AGENTS.md Content Rule 4)."
            )
    return errs


def _validate_no_orphan_providers(all_requires: Set[str]) -> List[str]:
    """
    §6A, the other direction — a provider entry no node requires is unreachable and
    therefore unchecked.

    Every other §6 check is driven by a node's `requires`: §6C asks whether a required
    capability has a provider, §6D whether that provider is discriminating, §6F whether
    a blind Attester agrees it is provided. All of them start from a requirement. An
    entry nothing requires is read by none of them — never attested, never contradicted,
    never provision-checked — while sitting in the table ready to satisfy the FIRST
    future node whose competency extracts that id. It would arrive pre-approved, with no
    Attester having ever seen a rendered sample of it. That is aimed squarely at the
    grades that do not exist yet (Scaling Mandate 4).

    Found the day it was written: `draw_lines` claimed `task_type=draw_construct` under a
    name no node requires, left behind when `draw_line_relationships` was deliberately
    unregistered on an Attester's NOT_PROVIDED ruling. The registration outlived the
    requirement by a rename and nothing in the harness could say so.

    Zero findings is the only acceptable state and there is no floor: unlike §6D's
    `_PROVISION_FLOOR`, an orphan is never a legitimate gap in the pipeline's ability —
    it is bookkeeping, and deleting the entry always clears it.
    """
    orphans = sorted(set(CAPABILITY_PROVIDERS) - all_requires)
    return [
        f"CAPABILITY_PROVIDERS declares {cap!r} -> {CAPABILITY_PROVIDERS[cap]}, but no "
        f"node's `requires` names it (§6A). Every §6 check is driven by a requirement, "
        f"so an entry nothing requires is never attested, never contradicted and never "
        f"provision-checked — and it will silently pre-approve the first future node "
        f"whose competency extracts this id. Delete the entry; re-add it only with a "
        f"requirement that names it and an Attester verdict behind it."
        for cap in orphans
    ]


def _validate_coverage(node_id: str, competency: str, requires: List[Dict],
                       ignore: List[str]) -> List[str]:
    """§6B — a competency word no clause covers is a requirement silently dropped."""
    covered: Set[str] = set()
    for req in requires:
        covered.update(_content_words(str(req.get("clause", ""))))
    covered.update(w.lower() for w in ignore)

    missing = [w for w in _content_words(competency) if w not in covered]
    if not missing:
        return []
    return [
        f"{node_id}: competency words {sorted(set(missing))} are covered by no requirement "
        f"clause. Either declare the requirement they describe, or list them in "
        f"'requires_ignore' with the reason. Silently dropping a competency word is how a "
        f"node passes while never generating what it was written to teach."
    ]


def _bound_restricts_to(bound: Any) -> Set[str] | None:
    """
    The set of values a competency bound permits for a *discrete* variant key, or None
    when the bound does not restrict a variant that way.

    A scalar bound pins the key to one value; a list bound restricts it to its members.
    A 2-tuple is always a continuous (min, max) range, never a discrete pair -- see
    docs/pgen_hardening.md -- so it restricts no variant and returns None.
    """
    if isinstance(bound, tuple):
        return None
    if isinstance(bound, (str, int)) and not isinstance(bound, bool):
        return {str(bound)}
    if isinstance(bound, list):
        return {str(b) for b in bound}
    return None


# §6D — the generic textual formatter family.
#
# These four are reachable from almost every DNA in the tree, so listing one as a
# capability's provider satisfies the clause on almost every node: it answers "can this
# node render text?", never "does this node render the thing the clause names".
#
# Measured 2026-08-19 on this tree:
#   * 27 of 28 DNAs offer at least one (only `bar_graphs` does not);
#   * 148 of 151 nodes reach at least one on the student path;
#   * 474 of 485 CAPABILITY_PROVIDERS entries list at least one, and removing the family
#     turns 0 reported capability problems into 59.
#
# That is the shape of a wildcard: a provider that matches everything is not a provider
# (Rule 9). §6D below recomputes provision with this family removed and fails, by name,
# any capability the family alone was carrying.
#
# Note for anyone extending this: do NOT threshold on `bounds` list length. An earlier
# audit named the 27-key `bounds` catch-all on 483 providers as the defeat mechanism;
# measured, deleting `bounds` from every provider moves the failure count 0 -> 0. It is
# inert padding. A check written that way flags 483 harmless entries and catches zero
# real ones. Equally, "is this entry's formatter list *only* generic?" catches 82 of the
# 474 — the other 392 mix a generic name in beside a specific one and `_validate_provision`
# ORs them, so the generic name carries the clause and the specific one is decoration.
# The question that discriminates is "what still provides this once the family is gone?"
_GENERIC_TEXTUAL_FORMATTERS: Set[str] = {"mcq", "cloze", "true_false", "error_detect"}


# §6E — the shared `bounds` catch-all.
#
# Rule 9 again, applied to the other column: "a `bounds` list is a numeric-ceiling
# provider and nothing else". A bounds list earns a capability only if it says something
# about THAT capability. A list carried verbatim by almost every entry in the table says
# nothing about any of them.
#
# Measured on this tree: there are exactly TWO distinct bounds lists across 484
# providers -- one 27-key list on 474 of them (97.9%) and one empty list on 10. Stripping
# `bounds` from every provider moves the reported failure count by 15, so the catch-all
# is now load-bearing for 15 capabilities across three ordinal nodes that ride it alone.
#
# The discriminator is SHARED-NESS, not length, and the distinction matters:
#
#   * A 1-key list carried by 474 entries is a wildcard and this check catches it.
#   * A 27-key list unique to one entry is a real claim and this check leaves it alone.
#
# `test_bounds_length_is_never_the_discriminator` pins that a length threshold must never
# be used here: an earlier audit named the 27-key list as the mechanism defeating §6C on
# the strength of its length, and measured *at that time* it was inert padding -- deleting
# it moved the count 0 -> 0, because the generic formatter family satisfied everything
# first. Length was the wrong question then and is the wrong question now; "how many
# entries carry this identical list?" is the right one, and it happens to be the question
# whose answer changed when §6D removed the bigger wildcard.
_SHARED_BOUNDS_FRACTION = 0.5


def _nondiscriminating_bounds() -> Set[frozenset]:
    """
    Bounds-list signatures carried by more than half of all registered providers.

    A list that most of the table shares cannot distinguish one capability from another,
    so it is not evidence that this node provides this clause. Returns signatures rather
    than lengths so the test that pins "length is never the discriminator" stays true by
    construction.
    """
    total = len(CAPABILITY_PROVIDERS)
    if not total:
        return set()
    counts: Dict[frozenset, int] = {}
    for spec in CAPABILITY_PROVIDERS.values():
        sig = frozenset(spec.get("bounds") or [])
        if not sig:
            continue  # an empty list provides nothing anywhere; it is not a wildcard
        counts[sig] = counts.get(sig, 0) + 1
    return {
        sig for sig, n in counts.items()
        if n > _SHARED_BOUNDS_FRACTION * total
    }


def _provided_for_node(node_id: str) -> Dict[str, Set[str]]:
    """
    The concrete artifacts reachable for this node **on the student path**.

    `VARIANTS_BY_DNA` is what a DNA *declares*; it is not what the node can serve.
    `_parse_competency_bounds` clamps discrete variant keys per node, and `is_student_path`
    applies that clamp -- so a node whose bounds pin `task_type='compare_shapes'` can never
    select `identify_name`, however loudly its DNA declares that value.

    Intersecting the declaration with the clamp is what stops a capability from being
    reported as provided by a variant value the student path can never reach. Without it,
    §6C answers "does some DNA list this value" when the question is "can this node produce
    it" -- and those diverge exactly on the nodes whose competency is narrower than its DNA.
    """
    dnas = NODE_TO_DNA.get(node_id) or []
    bounds = get_node_competency_bounds(node_id) or {}
    # The MATATAG progression gate, CALLED rather than mirrored. `generate_context`
    # refuses a variant value the curriculum has not introduced at this node's grade and
    # quarter, so a value it would refuse is not a provider for anything here however
    # loudly the DNA declares it -- registering one would clear a §6D finding while the
    # student path never renders it, which is the shape §6F reports as CONTRADICTED.
    # Same omission, same fix, as the review-packet builder on 2026-09-08.
    grade, quarter = node_grade_quarter(node_id)
    variants: Set[str] = set()
    formatters: Set[str] = set()
    for dna in dnas:
        known = get_variants_for_dna(dna)
        for key, values in (VARIANTS_BY_DNA.get(dna) or {}).items():
            allowed = _bound_restricts_to(bounds[key]) if key in bounds else None
            for v in values:
                if allowed is not None and str(v) not in allowed:
                    continue
                if (str(v) in known.get(key, [])
                        and not is_variant_available_at(dna, key, str(v), grade, quarter)):
                    continue
                variants.add(f"{key}={v}")
            # A bound the registry pins is reachable for this node by construction,
            # even when VARIANTS_BY_DNA does not list it. That happens for the
            # *sentinel* bounds this codebase uses where one node serves two tasks
            # chosen per seed (area's "find_area_or_missing_dimension", calendar's
            # "elapsed_days_or_weeks"): the DNA resolves them against its own rng, so
            # they are deliberately not Lab-selectable variant values. Without this,
            # §6C reported mat_g3_mg_q1_3 as having no reachable task_type at all --
            # the opposite of the truth, since the registry names exactly what it runs.
            # This does not loosen the clamp above: a value the bound excludes is still
            # excluded, which is what keeps the unreachable-value defeat caught.
            if allowed is not None:
                for v in allowed:
                    variants.add(f"{key}={v}")
        formatters.update(COMPATIBILITY.get(dna) or [])
    return {"variants": variants, "formatters": formatters}


def _validate_provision(node_id: str, requires: List[Dict]) -> List[str]:
    """§6C — required ⊆ provided. An unprovided capability is a build item, named."""
    errs: List[str] = []
    avail = _provided_for_node(node_id)
    shared_bounds = _nondiscriminating_bounds()
    dnas = NODE_TO_DNA.get(node_id) or []

    for req in requires:
        cap = str(req.get("id", ""))
        spec = CAPABILITY_PROVIDERS.get(cap)
        if spec is None:
            errs.append(
                f"{node_id}: competency requires {cap!r} (from clause "
                f"{req.get('clause')!r}), but no pipeline artifact provides it. "
                f"Reachable DNAs: {dnas or '[]'}. Build the formatter/variant/dd/DNA that "
                f"produces it and register it in CAPABILITY_PROVIDERS "
                f"(see docs/pgen_hardening.md Part 1) -- this is the fix, not a reason to defer "
                f"the node (AGENTS.md Content Rule 4)."
            )
            continue

        by_variant = [
            f"{k}={v}" for k, v in spec.get("variants", [])
            if f"{k}={v}" in avail["variants"]
        ]
        # §6D: a generic textual formatter is not a provider for anything (see the
        # measurement above the _GENERIC_TEXTUAL_FORMATTERS constant). Count what it
        # carries separately from what a specific artifact carries, so the two can be
        # told apart rather than OR'd into a single boolean.
        matched_formatters = [f for f in spec.get("formatters", []) if f in avail["formatters"]]
        by_specific_formatter = [
            f for f in matched_formatters if f not in _GENERIC_TEXTUAL_FORMATTERS
        ]
        by_generic_formatter = [
            f for f in matched_formatters if f in _GENERIC_TEXTUAL_FORMATTERS
        ]
        # A numeric ceiling is provided by the node's competency bounds rather than by
        # a variant value -- that is the one part of _parse_competency_bounds worth
        # keeping, since a range genuinely is derivable from "up to 100".
        # §6E: split the same way §6D splits formatters. A bounds list shared by most of
        # the table is a catch-all and carries nothing; one specific to this entry is a
        # genuine numeric-ceiling claim.
        by_bounds: List[str] = []
        bounds_is_shared = False
        if spec.get("bounds"):
            bounds = get_node_competency_bounds(node_id) or {}
            by_bounds = [b for b in spec["bounds"] if b in bounds]
            bounds_is_shared = frozenset(spec["bounds"]) in shared_bounds
        by_specific_bounds = [] if bounds_is_shared else by_bounds
        by_shared_bounds = by_bounds if bounds_is_shared else []

        discriminating = by_variant + by_specific_formatter + by_specific_bounds
        if discriminating:
            continue

        if by_generic_formatter:
            # The entry is registered and it "matches" -- but only via a formatter the
            # whole tree offers. Nothing here is evidence that this node produces what
            # the clause names, so the honest report is the same one an unregistered
            # capability gets: no pipeline artifact provides it.
            errs.append(
                f"{node_id}: competency requires {cap!r} (from clause "
                f"{req.get('clause')!r}), but no pipeline artifact provides it. "
                f"Its only reachable provider is the generic textual formatter family "
                f"{sorted(by_generic_formatter)}, which 27 of 28 DNAs offer and which "
                f"therefore discriminates nothing (§6D, AGENTS.md Rule 9)."
                + (
                    f" Its `bounds` list is also a catch-all that "
                    f"{sum(1 for s in CAPABILITY_PROVIDERS.values() if frozenset(s.get('bounds') or []) == frozenset(spec.get('bounds') or []))} "
                    f"of {len(CAPABILITY_PROVIDERS)} providers carry verbatim, so it "
                    f"rescues nothing either (§6E)."
                    if by_shared_bounds else ""
                )
                + f" Registered providers: {spec}. Reachable DNAs: {dnas or '[]'}. "
                f"Either build the formatter/variant/dd/DNA that renders what the clause "
                f"names and register that, or delete the entry and let this gap be "
                f"reported -- a generic textual formatter is never the answer."
            )
            continue

        if by_shared_bounds:
            errs.append(
                f"{node_id}: competency requires {cap!r} (from clause "
                f"{req.get('clause')!r}), but no pipeline artifact provides it. "
                f"Its only reachable provider is a `bounds` catch-all "
                f"{sorted(by_shared_bounds)} drawn from a list that "
                f"{sum(1 for s in CAPABILITY_PROVIDERS.values() if frozenset(s.get('bounds') or []) == frozenset(spec['bounds']))} "
                f"of {len(CAPABILITY_PROVIDERS)} providers carry verbatim, so it makes no "
                f"claim about this capability in particular (§6E, AGENTS.md Rule 9). "
                f"Registered providers: {spec}. Reachable DNAs: {dnas or '[]'}. "
                f"Either build the formatter/variant/dd/DNA that renders what the clause "
                f"names and register that, or delete the entry and let this gap be "
                f"reported. A bounds list is a numeric-ceiling provider and nothing else."
            )
            continue

        errs.append(
            f"{node_id}: capability {cap!r} (clause {req.get('clause')!r}) has "
            f"providers registered {spec}, but none is reachable from this node's "
            f"DNAs {dnas}. Either the node is mapped to the wrong DNA, or the "
            f"provider is gated off the node that needs it."
        )
    return errs


_ATTESTATION_DIR = Path(__file__).resolve().parents[4] / "validation_reports" / "attestation"


def _attestation_records() -> List[Dict[str, Any]]:
    """Every attestation batch on disk, whole, for the freshness pass."""
    if not _ATTESTATION_DIR.exists():
        return []
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(_ATTESTATION_DIR.glob("*.json"))]


def _load_attestations() -> Dict[tuple, Dict[str, Any]]:
    """
    Every blind Attester verdict on record, keyed by (node_id, capability_id).

    A verdict is about *specific rendered content*, so it is scoped to the node whose
    samples were judged -- the same capability on two nodes reaches different DNAs and
    renders differently, and a verdict earned on one says nothing about the other.
    """
    out: Dict[tuple, Dict[str, Any]] = {}
    if not _ATTESTATION_DIR.exists():
        return out
    for path in sorted(_ATTESTATION_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"attestation record '{path.name}' is not valid JSON: {exc}. An unreadable "
                f"verdict is not a missing verdict -- fix the file rather than deleting it."
            ) from exc
        for v in data.get("verdicts", []):
            node, cap, verdict = v.get("node_id"), v.get("capability_id"), v.get("verdict")
            if not (node and cap and verdict):
                raise ValueError(
                    f"attestation record '{path.name}' has a verdict missing node_id, "
                    f"capability_id or verdict: {v!r}"
                )
            if verdict not in ("PROVIDED", "NOT_PROVIDED"):
                raise ValueError(
                    f"attestation record '{path.name}': verdict must be PROVIDED or "
                    f"NOT_PROVIDED, got {verdict!r}. There is no 'partly'."
                )
            out[(node, cap)] = v
    return out


def _attestation_staleness(records: List[Dict[str, Any]]) -> List[str]:
    """
    §6F freshness -- an attestation is evidence about *specific rendered content*, and
    it stops being evidence the moment that content changes.

    §5 has enforced this for judgment reviews since the fabrication incident: every
    cited seed is re-rendered through the live pipeline and compared, because a review
    of content the generator no longer produces is not a review. Attestations decay the
    same way and for the same reason -- an Attester ruled that ten specific items do or
    do not exhibit a clause, and a generator change can invalidate that ruling without
    touching a single line of the provider table.

    Without this, the contract has a permanent hole: attest everything once, then change
    generators freely, and `run_all` keeps exiting 0 on evidence about content that no
    longer exists. That hole would be invisible and it would scale -- which matters
    because this harness is the foundation the remaining MATATAG grade levels get built
    on, and a gate that certifies stale evidence certifies it for every grade.

    Brought to §5 PARITY on 2026-09-10. It compares, in this order and per seed, the
    same four things `_validate_freshness` compares, using §5's own helpers rather than
    a second copy of the rule (a re-derived copy is how two gates that must agree drift
    apart):

        1. the stem;
        2. that a record carries the `options` it was shown, when the live render
           offers some -- otherwise nothing below can be adjudicated at all;
        3. the keyed VALUE, resolved through the record's own option table so an A-D
           slot moving is not read as content drift;
        4. the offered option multiset.

    Before that it compared the STEM ONLY, and the cost was measured across the 151 live
    records the day it was closed:

        stale on the stem (all this used to see)               :   8
        stem identical, NO recorded options while the live
          render offers some -- answer unresolvable, option
          drift uncheckable                                    : 134
        of those, samples whose raw answer field also moved    : 167 samples

    134 of 151, not the 50 that were predicted. The prediction assumed "Attester packets
    already carry `options`, so nothing new has to be recorded first". They do not, and
    that was the root defect: `tests/attester_packets._render` computes the option table
    and `render_prompt_block` prints it to the Attester, but the RECORD SKELETON the
    builder writes copied only seed/question_text/correct_answer/formatter. Measured
    before the fix: 0 of 1790 recorded samples carried `options`. The builder is fixed in
    the same commit, so records filed from now on are adjudicable; the 134 already on
    disk are not, and each must be re-attested. They may not be repaired in place -- the
    options that were shown are simply not recorded, and editing a record is forbidden.

    One correction to the record, since it was the stated motivation for this work.
    `docs/pgen_contract.md` and the campaign brief both cited "`b11_mat_g2_na_q3_5` seed
    11 was attested against a key of `False` and now renders an empty key". Re-rendered
    2026-09-10, that seed still keys `False`. The "empty key" was `_normalize(False)`
    returning "" -- the falsy collapse `_answer_value` exists to stop -- so the example
    was an artifact of the measurement, not a drift. Ten such would-be false positives
    were in that population.

    KNOWN LIMITATION, unchanged and named (Scaling Mandate 6): like §5, this does not
    compare the VISUAL PAYLOAD, and a capability clause about a medium is exactly the
    kind an attestation is filed for. A ShapeBoard can change from squares to hexagons
    under a byte-identical stem, answer and option set and still read fresh here.

    SECOND LIMITATION, measured rather than assumed: the packet builder renders with
    `is_student_path=True` and this re-renders through `_render_sample`, which does not.
    Across all 1510 recorded samples on 2026-09-10 the two paths agreed on stem, answer
    and option presence in every case, so the comparison is sound today -- but nothing
    enforces that they stay the same path, and if they diverge this gate reports drift
    that is really a path difference.
    """
    from backend.app.practice_gen.validation.judgment_packets import _render_sample
    from backend.app.practice_gen.validation.validate_judgment import (
        _answer_value,
        _option_values,
        _resolved_answer,
    )

    # A record that no longer supplies a single winning verdict is not evidence for
    # anything, and re-rendering its seeds asks whether content still matches a ruling
    # nothing consults. `_load_attestations` resolves (node_id, capability_id) by
    # last-file-wins over the same sorted glob, so replay exactly that rule here -- a
    # different rule would let the freshness pass and the verdict pass disagree about
    # which record is authoritative.
    #
    # Derived from the data, NEVER from the record's own `supersedes` string. A
    # self-declared field would let a batch retire an inconvenient verdict by asserting
    # it had been replaced; this way supersession has to be *earned* by filing a real
    # record that itself faces this same freshness check. Note the newer record is not
    # trusted either: if it is stale, it is reported under its own name.
    #
    # Whole-record, not per-verdict. batch018_mat_g3_na_q3_4 still owns all four of its
    # verdicts while its two siblings own none of theirs, so a blanket "an 018 exists,
    # skip it" rule would silently stop freshness-checking live evidence.
    winner = _winning_verdict_index(records)

    errs: List[str] = []
    for idx, rec in enumerate(records):
        verdict_pairs = [(v.get("node_id"), v.get("capability_id"))
                         for v in rec.get("verdicts", [])]
        if verdict_pairs and all(winner.get(pair) != idx for pair in verdict_pairs):
            continue

        packet = rec.get("packet") or {}
        node_id = packet.get("node_id")
        judged = packet.get("samples_judged")
        batch = rec.get("batch", "<unnamed batch>")
        if not node_id or judged is None:
            errs.append(
                f"attestation batch {batch!r} records no packet.node_id / "
                f"packet.samples_judged, so its verdicts cannot be checked for staleness. "
                f"An attestation that cannot be re-rendered is not evidence -- re-run the "
                f"packet builder and re-attest."
            )
            continue
        # One finding per record, first problem wins: a record is re-attested whole, so
        # a second reason to re-attest the same batch is not a second unit of work. The
        # order below is the order §5 uses and is load-bearing -- an answer cannot be
        # resolved without the option table, so the adjudicability check must precede
        # the answer comparison or a structurally uncheckable record is reported as an
        # answer-drift symptom instead.
        rebuild = (
            f"Rebuild the packet with: python tests/attester_packets.py --node {node_id} "
            f"--packets <f> --key <f> --record <f>, dispatch a blind Attester, and file "
            f"the replacement. Do not edit the record."
        )
        for sample in judged:
            seed = sample.get("seed")
            if seed is None:
                errs.append(f"attestation batch {batch!r}: a judged sample carries no seed.")
                continue
            current = _render_sample(node_id, seed)
            was, now = sample.get("question_text", ""), current.get("question_text", "")
            if " ".join(str(was).split()) != " ".join(str(now).split()):
                errs.append(
                    f"{node_id}: attestation batch {batch!r} is STALE (§6F) at seed {seed}. "
                    f"The Attester judged {was[:90]!r} but the pipeline now renders "
                    f"{now[:90]!r}. Every verdict in this batch is about content that no "
                    f"longer exists -- re-attest the batch. Do not edit the record."
                )
                break

            rec_opts = _option_values(sample)
            cur_opts = _option_values(current)

            # Whether an item is a choice item is decided by the LIVE RENDER, never by a
            # formatter name -- a grade-7 formatter that does not exist yet may carry an
            # option table too (Scaling Mandate 4).
            if cur_opts is not None and rec_opts is None:
                errs.append(
                    f"{node_id}: attestation batch {batch!r} records no 'options' at seed "
                    f"{seed}, but the live render of that seed offers {len(cur_opts)}: "
                    f"{cur_opts}. The Attester was shown those options by "
                    f"render_prompt_block, so its verdict rests on them -- but the record "
                    f"does not carry them, so option drift cannot be checked at all and on "
                    f"a key-valued formatter the answer cannot be resolved either. "
                    f"{rebuild}"
                )
                break
            if rec_opts is not None and cur_opts is None:
                errs.append(
                    f"{node_id}: attestation batch {batch!r} is STALE (§6F) at seed {seed} — "
                    f"it was attested as a choice item offering {rec_opts}, but the live "
                    f"render offers no options at all. The item stopped being a selection "
                    f"task after the attestation was filed. {rebuild}"
                )
                break

            rec_ans, rec_keyed = _resolved_answer(sample)
            cur_ans, cur_keyed = _resolved_answer(current)
            # Only compare resolved values when BOTH sides resolved through their own
            # option table. When either did not, the raw field is all there is.
            if rec_keyed != cur_keyed:
                rec_ans = _answer_value(sample.get("correct_answer"))
                cur_ans = _answer_value(current.get("correct_answer"))
            if rec_ans != cur_ans:
                errs.append(
                    f"{node_id}: attestation batch {batch!r} is STALE (§6F) at seed {seed} — "
                    f"the stem is unchanged but the item no longer keys the same answer. "
                    f"Attested: {rec_ans!r}; now keys: {cur_ans!r}. A capability verdict is "
                    f"about what the rendered item asks and answers, and the answer moved "
                    f"under it. {rebuild}"
                )
                break

            if rec_opts is not None and cur_opts is not None and rec_opts != cur_opts:
                errs.append(
                    f"{node_id}: attestation batch {batch!r} is STALE (§6F) at seed {seed} — "
                    f"the stem is unchanged but the item is no longer offered the same "
                    f"options. Attested: {rec_opts}; now offers: {cur_opts}. What a clause "
                    f"is exhibited by is judged off the whole item, options included. "
                    f"{rebuild}"
                )
                break
    return errs


# How many (node, capability) verdicts may share one normalized reasoning skeleton
# before it is a filled-in form rather than independent judgement. Deliberately the
# same number as §5's _MAX_SKELETON_CLUSTER: both gates ask the same question about
# the same kind of artifact, so weakening the idea should cost two visible diffs,
# not one. Measured 2026-08-23 across all 143 live verdicts: largest cluster was 2.
_MAX_ATTESTER_SKELETON_CLUSTER = 3

# One batch is one blind dispatch, and docs/pgen_judgment.md caps a blind batch at
# 25 items. A record carrying more did not come from one dispatch. Measured
# 2026-08-23: the largest record on disk carries 11.
_MAX_VERDICTS_PER_BATCH = 25


def _winning_verdict_index(records: List[Dict[str, Any]]) -> Dict[tuple, int]:
    """
    Which record currently owns each (node_id, capability_id) verdict.

    `_load_attestations` resolves duplicates by last-file-wins over a sorted glob.
    Every pass that judges "is this record still evidence?" must replay exactly that
    rule, or the passes disagree about which record is authoritative and a verdict
    can be live for one check and superseded for another.

    Derived from the records themselves, NEVER from a record's own `supersedes`
    string: a self-declared field would let a batch retire an inconvenient verdict by
    asserting it had been replaced. Supersession has to be earned by filing a real
    record that itself faces these same checks.
    """
    winner: Dict[tuple, int] = {}
    for i, rec in enumerate(records):
        for v in rec.get("verdicts", []):
            winner[(v.get("node_id"), v.get("capability_id"))] = i
    return winner


def _attestation_integrity(records: List[Dict[str, Any]]) -> List[str]:
    """
    §6G -- structural evidence that a verdict was earned rather than written.

    §6F asks two things of an attestation: that it exists, and that the content it
    judged still renders. Neither reads the verdict's own reasoning, so both are
    satisfied by a record whose reasoning was produced in bulk. §5 learned exactly
    this at cost: freshness passed all 151 fabricated reviews, because a template
    stapled onto a freshly-rendered samples block is fresh. The structural checks
    that finally caught them are ported here, because attestation is now the larger
    surface -- 787 (node, capability) verdicts against 151 reviews -- and it is
    dispatched in unattended batches where no human sees any single one.

    What each catches, and why more prose cannot satisfy it:

      * skeleton clustering -- strip node IDs, quoted spans and digits and a
        filled-in form collapses to one string across every clause it was stamped
        on. Independent judgements about different clauses do not collapse.
      * seed provenance -- a verdict names the seeds that show the clause, and seeds
        are structured data rather than prose. A verdict citing a seed absent from
        its own packet cited an item it was never shown; a PROVIDED verdict citing
        no seed asserts an observation it declines to locate.
      * batch size -- a blind batch is <= 25 items dispatched to one agent. A record
        carrying more is one pass over the provider table wearing a batch's name.

    Only *live* verdicts are judged, by `_winning_verdict_index`'s last-file-wins
    rule. A superseded record is no longer evidence for anything, and failing it
    forever would leave no legal move -- the record may not be edited (§6F) and may
    not be deleted.

    Quote provenance -- §5's fourth gate, and the one that caught 115 of the 151 --
    is deliberately NOT ported. Measured 2026-08-23, it fires on 16 of 143 honest
    verdicts, because an Attester is asked to state what would flip its verdict and
    writes that hypothesis in quotes ("Nothing short of an item that requires the
    student to construct..."). A review's rationale quotes to cite; an attestation's
    reasoning quotes to hypothesize. Shipping it here would fail honest work and
    teach the next agent that this gate is negotiable. Closing it needs a record
    field that separates citation from hypothesis, which is named work, not a
    threshold to tune.
    """
    from backend.app.practice_gen.validation.validate_judgment import _rationale_skeleton

    winner = _winning_verdict_index(records)
    errs: List[str] = []
    skeletons: Dict[str, List[tuple]] = {}

    for idx, rec in enumerate(records):
        batch = rec.get("batch", "<unnamed batch>")
        verdicts = rec.get("verdicts", []) or []
        packet = rec.get("packet") or {}
        packet_seeds = {s.get("seed") for s in (packet.get("samples_judged") or [])}

        live = [v for v in verdicts
                if winner.get((v.get("node_id"), v.get("capability_id"))) == idx]
        if not live:
            continue

        if len(verdicts) > _MAX_VERDICTS_PER_BATCH:
            errs.append(
                f"attestation batch {batch!r} carries {len(verdicts)} verdicts (§6G, max "
                f"{_MAX_VERDICTS_PER_BATCH} -- one blind dispatch). A record larger than a "
                f"batch is one pass over the table, not independent per-clause judgement. "
                f"Split it and re-attest each part with its own Attester."
            )

        for v in live:
            node_id, cap = v.get("node_id"), v.get("capability_id")
            reasoning = str(v.get("reasoning", "") or "").strip()
            if not reasoning:
                errs.append(
                    f"{node_id}: attestation of {cap!r} in batch {batch!r} carries no "
                    f"reasoning (§6G). A verdict without reasoning is a vote, and the "
                    f"contract does not count votes."
                )
                continue
            skeletons.setdefault(_rationale_skeleton(reasoning), []).append((node_id, cap))

            raw = v.get("seeds_showing_it")
            cited = [int(x) for x in re.findall(r"\d+", str(raw))] if raw is not None else []
            if v.get("verdict") == "PROVIDED" and not cited:
                errs.append(
                    f"{node_id}: attestation of {cap!r} in batch {batch!r} is PROVIDED but "
                    f"names no seed in 'seeds_showing_it' (§6G). A PROVIDED verdict asserts "
                    f"that specific rendered items exhibit the clause; it must say which."
                )
            for seed in cited:
                if seed not in packet_seeds:
                    errs.append(
                        f"{node_id}: attestation of {cap!r} in batch {batch!r} cites seed "
                        f"{seed} in 'seeds_showing_it', which is not in this record's own "
                        f"packet.samples_judged {sorted(s for s in packet_seeds if s is not None)} "
                        f"(§6G). The Attester cited an item it was never shown."
                    )

    for skeleton, pairs in sorted(skeletons.items()):
        if len(pairs) > _MAX_ATTESTER_SKELETON_CLUSTER:
            errs.append(
                f"attester boilerplate (§6G): {len(pairs)} verdicts share one normalized "
                f"reasoning skeleton (max {_MAX_ATTESTER_SKELETON_CLUSTER}) -- node IDs, "
                f"quoted spans and digits stripped, the reasoning is the same sentence "
                f"frame filled in per clause. That is a form, not independent judgement. "
                f"First: {sorted(pairs)[:5]}. Skeleton: {skeleton[:120]!r}"
            )
    return errs


def _validate_attestation(node_id: str, requires: List[Dict],
                          attested: Dict[tuple, Dict[str, Any]]) -> List[str]:
    """
    §6F -- a provider entry is a *claim*, and a claim nobody blind has checked is not
    evidence.

    §6C proves the claimed artifact exists and is reachable. §6D proves it is not a
    generic formatter every DNA already offers. **Neither can tell whether the artifact
    does what the clause names**, because that is a reading of MATATAG rather than a
    lookup: `task_type=draw_construct` is a real, reachable variant whose name asserts
    its own semantics, and it rendered multiple-choice questions *about* drawing on a
    competency that says "draw". Both mechanical checks passed it.

    Until 2026-08-20 the Attester that closes that gap had no enforcement: its verdicts
    sat in validation_reports/attestation/ and nothing read them, so a NOT_PROVIDED
    ruling took effect only if the Fixer chose to act on it. That is the same
    author-verifying-itself structure the role was introduced to break (Rule 11: make a
    guard mechanical in the same unit that creates it -- this one was owed).

    Two failures, deliberately distinct, because they mean different things and have
    different fixes:

      CONTRADICTED -- a blind Attester ruled NOT_PROVIDED and the table still claims it.
                      Delete the entry or build the artifact. Never re-file the verdict.
      UNATTESTED   -- nobody blind has ever looked. Not "probably fine": unexamined
                      green is exactly what this project has shipped three times.
    """
    errs: List[str] = []
    for req in requires:
        cap = str(req.get("id", ""))
        record = attested.get((node_id, cap))
        if record is None:
            errs.append(
                f"{node_id}: capability {cap!r} (clause {req.get('clause')!r}) is UNATTESTED "
                f"(§6F) -- no blind Attester has judged whether the pipeline's rendered "
                f"output exhibits what this clause names. Build a packet with "
                f"tests/attester_packets.py, dispatch an Attester (Rule 1), and file the "
                f"verdict in validation_reports/attestation/. An unverified claim is not a "
                f"provider."
            )
        elif record.get("verdict") == "NOT_PROVIDED" and cap in CAPABILITY_PROVIDERS:
            errs.append(
                f"{node_id}: capability {cap!r} (clause {req.get('clause')!r}) is "
                f"CONTRADICTED (§6F) -- a blind Attester ruled NOT_PROVIDED, and "
                f"CAPABILITY_PROVIDERS still claims {CAPABILITY_PROVIDERS[cap]}. "
                f"Attester's reasoning: {str(record.get('reasoning'))[:200]!r}. "
                f"Delete the entry and let the gap be reported, or build the artifact that "
                f"renders what the clause names and re-attest it. Do not re-file the verdict."
            )
    return errs



# Attestations filed from this date must name their Attester. Records predating it are
# grandfathered: 173 exist with no identity field at all, and invalidating them would
# destroy real blind judgement to punish a schema gap that was not their author's doing.
_ATTESTER_IDENTITY_REQUIRED_FROM = "2026-08-28"

# One Attester identity may cover at most this many nodes, mirroring §5's
# _MAX_NODES_PER_REVIEWER. An identity spanning more than a dispatch is one pass over the
# table, not independent per-clause judgement.
_MAX_NODES_PER_ATTESTER = 25


def validate_attester_plurality() -> List[str]:
    """
    §6H -- an Attester verdict must say WHO made it, and no one may make them all.

    §5 has enforced reviewer plurality since it was written: `reviewed_by` is required and
    one identity may not cover more than a batch. Attestation had no equivalent, and the
    reason is stark -- measured 2026-08-28, all 173 attestation records carry NO identity
    field whatsoever. `attested_by`, `attester`, `judged_by` are all absent.

    So the independence §6F exists to guarantee could not be checked on a surface four
    times larger than §5's (787 verdicts against 151 reviews). §6G caps how many verdicts
    one BATCH may hold, which stops a single record covering the table, but nothing stopped
    one identity filing every batch -- the author-verifying-itself structure the blind
    Attester role was created to break.

    Grandfathered, deliberately: records filed before the cutoff are exempt. Requiring an
    identity retroactively would fail 173 records whose judgement was genuinely blind, and
    a check that condemns honest work to close a schema gap teaches the next agent to
    distrust it.
    """
    errs: List[str] = []
    by_identity: Dict[str, Set[str]] = {}

    for record in _attestation_records():
        batch = record.get("batch") or "<unnamed>"
        attested_at = str(record.get("attested_at") or "")
        identity = (record.get("attested_by") or record.get("attester")
                    or record.get("judged_by") or "")
        identity = str(identity).strip()

        if attested_at[:10] >= _ATTESTER_IDENTITY_REQUIRED_FROM and not identity:
            errs.append(
                f"attestation batch {batch!r} was filed {attested_at[:10]} with no "
                f"'attested_by' identity (§6H). Since {_ATTESTER_IDENTITY_REQUIRED_FROM} a "
                f"verdict must name who made it, or its independence cannot be checked -- "
                f"which is the whole point of dispatching a blind Attester."
            )
            continue
        if not identity:
            continue  # grandfathered record, predating the requirement

        nodes = {v.get("node_id") for v in record.get("verdicts", []) if v.get("node_id")}
        by_identity.setdefault(identity.lower(), set()).update(nodes)

    for identity, nodes in sorted(by_identity.items()):
        if len(nodes) > _MAX_NODES_PER_ATTESTER:
            errs.append(
                f"attester plurality: identity {identity!r} covers {len(nodes)} nodes "
                f"(max {_MAX_NODES_PER_ATTESTER} -- one blind dispatch) (§6H). One identity "
                f"spanning more than a dispatch is a single pass over the table, not "
                f"independent per-clause judgement. First nodes: {sorted(nodes)[:5]}."
            )
    return errs


# ---------------------------------------------------------------------------
# The phase seam
# ---------------------------------------------------------------------------
# The boundary between the harness's two phases is NOT "does this check need an
# LLM". Every check in this module is programmatic: freshness is a mechanical
# re-render-and-compare, plurality is counting, seed provenance is a set lookup.
# The LLM's only job is to PRODUCE an attestation; it never validates one. The
# boundary that matters is:
#
#     DOES THIS CHECK NEED AN AGENT-AUTHORED ARTIFACT TO EXIST BEFORE IT RUNS?
#
#     no  -> Phase 1. Reads the knowledge graph, the `requires` declarations and
#            CAPABILITY_PROVIDERS, nothing else. Runs in the fix-until-green loop.
#     yes -> Phase 2. Reads validation_reports/attestation/, so it can only run
#            once an agent has filed one. Spans sessions; gated on Phase 1 green.
#
# That test is decidable rather than a matter of taste, which is what makes it
# enforceable. §6 straddled it for as long as it has existed: one function ran
# §6A-§6E (75 findings, 0.1s, needs no artifact) and §6F-§6H (90 findings, 9.9s,
# re-renders every attested seed) and reported both on ONE boolean. 75 findings
# that belong to the fast loop were therefore filed in the slow backlog, and
# nothing in the harness could tell the two bands apart.
#
# CHECK_PHASE is the registry, and it is the single source of truth: run_all
# imports it rather than keeping a second copy that could disagree with this one.
# Moved to _manifest 2026-09-09 and DERIVED here, not restated. The seam is harness-wide
# -- §5 is Phase 2 for exactly the reason §6F is -- so a §6 module is the wrong owner of
# the registry, and a second copy is what the original note ruled out. This view is the
# §6 slice; the two gates below are unchanged and still read `CHECK_PHASE`.
CHECK_PHASE: Dict[str, int] = {
    ref: phase for ref, phase in _MANIFEST_CHECK_PHASE.items() if ref.startswith("§6")
}

# Every §-ref a finding can cite, for the partition check below.
_SECTION_REF_RE = re.compile(r"§\d+[A-Za-z-]*")

# A path under validation_reports/ that must never exist. `_phase_boundary_failures`
# repoints _ATTESTATION_DIR here to re-run Phase 1 with the attestation corpus absent.
_ABSENT_ATTESTATION_PROBE = "__phase1_boundary_probe_must_not_exist__"


def _declared_nodes(
    node_ids: List[str] | None,
) -> tuple[List[tuple], List[str]]:
    """
    ((node_id, competency, requires, requires_ignore) per well-formed node, guard errors).

    Both phases walk the same nodes, so the walk lives here rather than being written
    twice and drifting. The guard errors -- no competency text, no `requires` block, a
    malformed one -- are returned separately because they belong to exactly ONE phase.
    They read the knowledge graph and nothing else, so they are Phase 1 findings, and
    Phase 1 is the only caller that reports them. Emitting them from both halves would
    double-count every undeclared node the moment a new grade lands with one.
    """
    rows: List[tuple] = []
    errs: List[str] = []
    for node_id in (node_ids if node_ids is not None else get_all_node_ids()):
        meta = get_node_info(node_id)
        competency = str((meta or {}).get("competency", "")).strip()
        if not competency:
            errs.append(f"{node_id}: no competency text in the knowledge graph.")
            continue

        requires = (meta or {}).get("requires")
        if requires is None:
            errs.append(
                f"{node_id}: no 'requires' declaration. Add one to "
                f"data/skeletons/vocab_annotation.json, authored from the competency text "
                f"alone (see docs/pgen_hardening.md Part 1), then rebuild the graph this "
                f"check reads: python scripts/rebuild_knowledge_graph.py. Undeclared nodes "
                f"are not skipped."
            )
            continue
        if not isinstance(requires, list) or not requires:
            errs.append(f"{node_id}: 'requires' must be a non-empty list of requirement records.")
            continue

        ignore = (meta or {}).get("requires_ignore") or []
        rows.append((node_id, competency, requires, ignore))
    return rows, errs


# The hand-authored source of the `requires` declarations. The knowledge graph the
# validators read is BUILT from it by scripts/rebuild_knowledge_graph.py.
_VOCAB_ANNOTATION_PATH = Path(__file__).resolve().parents[4] / "data" / "skeletons" / "vocab_annotation.json"
_KNOWLEDGE_GRAPH_PATH = Path(__file__).resolve().parents[4] / "data" / "knowledge_graph_g1_3.json"


def declaration_sync_failures() -> List[str]:
    """
    The declarations §6 validates must be the ones an author actually wrote.

    `get_node_info` reads data/knowledge_graph_g1_3.json, which is a BUILD ARTIFACT that
    scripts/rebuild_knowledge_graph.py generates from data/skeletons/vocab_annotation.json.
    Nothing checked the two agreed. So an author who edits the hand-authored source and
    does not rebuild has §6 validate a stale copy, silently and indefinitely -- and §6's
    own "no 'requires' declaration" message tells them to edit exactly the file the
    validator does not read.

    Found 2026-09-09 by a mutation that SURVIVED: `clause_not_in_competency` planted a
    bad clause in vocab_annotation.json and §6A never saw it (Mandate 2, second cause --
    the plant did not reach the code the validator runs). The two copies happened to be
    in sync at the time, so the drift had never bitten; nothing would have said so if it
    had.

    WIDENED 2026-09-10, because the drift this exists to catch was ON DISK while it
    passed. It compared two fields -- `requires` and `requires_ignore` -- and the graph
    checked in at 8cb8dd22 differed from a fresh build of the same skeleton in a THIRD
    field: 18 nodes carried a cumulative concept (`missing_number`, plus `addition` on
    one) that the skeleton no longer implies. Cumulative concept lists are the ground
    truth Content Rule 1 is judged against -- §1D's NOT_YET_KNOWN gating reads them --
    so a stale one means the vocabulary gate was validating against something nobody
    wrote, which is this function's own stated failure mode one field over.

    So it now compares the WHOLE artifact: the skeleton is rebuilt in memory and every
    node record is compared field by field. Two fields chosen by hand is a list that
    goes stale the moment the builder learns to derive something new; rebuilding is the
    only comparison that cannot drift from what the builder actually does. (Same
    reasoning as `_generated_formatter_exclusions.py`: asking the real thing beats
    modelling it.)

    Phase 1: both files are checked into the repo and present on a fresh clone. Neither
    is an agent-authored artifact, and the rebuild reads nothing else.
    """
    import contextlib
    import io
    import tempfile

    from scripts.rebuild_knowledge_graph import rebuild

    errs: List[str] = []
    try:
        built = json.loads(_KNOWLEDGE_GRAPH_PATH.read_text(encoding="utf-8"))["nodes"]
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        return [
            f"§6 declarations: could not read the generated graph "
            f"({type(exc).__name__}: {exc}). Until it can be compared with "
            f"data/skeletons/vocab_annotation.json, §6 is validating a copy nobody has "
            f"checked."
        ]

    # Built into a temp file rather than over the real one: a validator that rewrites
    # the artifact it is validating would make the failure disappear on the second run.
    with tempfile.TemporaryDirectory() as tmp:
        fresh_path = Path(tmp) / "knowledge_graph_rebuilt.json"
        with contextlib.redirect_stdout(io.StringIO()):
            rebuild(str(_VOCAB_ANNOTATION_PATH), str(fresh_path))
        fresh = json.loads(fresh_path.read_text(encoding="utf-8"))["nodes"]

    rebuild_hint = "Rebuild with: python scripts/rebuild_knowledge_graph.py"
    for node_id in sorted(set(built) | set(fresh)):
        if node_id not in fresh:
            errs.append(
                f"{node_id}: present in data/knowledge_graph_g1_3.json but a fresh build "
                f"of data/skeletons/vocab_annotation.json does not produce it. §6 "
                f"validates the generated copy, so it is checking a node nobody wrote. "
                f"{rebuild_hint}"
            )
            continue
        if node_id not in built:
            errs.append(
                f"{node_id}: data/skeletons/vocab_annotation.json declares it but "
                f"data/knowledge_graph_g1_3.json does not carry it, so §6 never sees it "
                f"at all. {rebuild_hint}"
            )
            continue
        for field in sorted(set(built[node_id]) | set(fresh[node_id])):
            want = fresh[node_id].get(field)
            got = built[node_id].get(field)
            if (want or None) == (got or None):
                continue
            errs.append(
                f"{node_id}: {field!r} in data/knowledge_graph_g1_3.json does not match "
                f"a fresh build of data/skeletons/vocab_annotation.json, which is where "
                f"it is authored. §6 validates the generated copy, so it is checking "
                f"something nobody wrote. {rebuild_hint}"
            )
    return errs


# FIVE, as of 2026-09-09, down from 75 the same day. Every one of them is the same
# capability, and it is a genuine feature gap rather than a registration one:
#
#   mat_g2_mg_q1_2  draw_effect                   "draw the effect"
#   mat_g3_mg_q1_4  draw_geometric_object         "draws"
#   mat_g3_mg_q1_5  draw_line_relationships       "draw"
#   mat_g3_mg_q4_0  draw                          "draw"
#   mat_g3_mg_q4_1  drawing_the_line_of_symmetry  "drawing the line of symmetry"
#
# MATATAG names the constructive verb in all five competencies, so under Content Rule 4
# building it is the fix -- and the thing to build is a formatter with a DRAWING SURFACE.
# The tree has none: every formatter either reads a visual or selects an option. The
# nearest artifact, `task_type='draw_construct'`, renders MCQs *about* drawing technique
# ("To draw parallel lines using a ruler and a set square, what is the correct
# technique?"), and a blind Attester shown ten of them and the clause "draw" ruled it
# NOT_PROVIDED: "no item asks the student to produce anything ... for a Grade 3
# constructive verb that is not the same act as drawing." Registering it anyway is
# exactly the move that produces a §6F CONTRADICTED, and the entry was deliberately
# removed once already. So the honest state is a named floor, not a registration.
#
# A FLOOR, and it may only ever SHRINK. It sits AT the finding count, not above it, so a
# sixth unprovided capability fails immediately -- and `wildcard_provider` clears it by
# an order of magnitude, so §6D stays provable (a floor above the real defect count makes
# a check unprovable, which is how §9 lost a mutation at RENDER_FLOOR=16).
_PROVISION_FLOOR = 5


def _phase1_findings(node_ids: List[str] | None) -> List[str]:
    """§6A/§6B/§6C/§6D/§6E over every registered node. Reads no agent-authored artifact."""
    rows, errs = _declared_nodes(node_ids)
    for node_id, competency, requires, ignore in rows:
        errs += _validate_provenance(node_id, competency, requires)
        errs += _validate_coverage(node_id, competency, requires, ignore)
        errs += _validate_provision(node_id, requires)
    # Tree-wide, and deliberately over EVERY declared node rather than the `node_ids`
    # subset: "no node requires this" is a statement about the whole tree, so computing
    # it from a scoped run would report every provider outside the scope as an orphan.
    all_rows, _ = _declared_nodes(None)
    errs += _validate_no_orphan_providers(
        {str(r.get("id")) for _n, _c, reqs, _i in all_rows for r in reqs}
    )
    # First in the list, because "the declarations you are reading are not the ones an
    # author wrote" invalidates every finding below it.
    return declaration_sync_failures() + errs


def _phase2_findings(node_ids: List[str] | None) -> List[str]:
    """§6F/§6G/§6H. Every one of these reads validation_reports/attestation/."""
    records = _attestation_records()
    attested = _load_attestations()
    errs = _attestation_staleness(records)
    errs += _attestation_integrity(records)
    # Guard errors are Phase 1's to report (see `_declared_nodes`); an undeclared node
    # has nothing to attest, and Phase 2 is gated on Phase 1 being green anyway.
    rows, _guard = _declared_nodes(node_ids)
    for node_id, _competency, requires, _ignore in rows:
        errs += _validate_attestation(node_id, requires, attested)
    # Tree-wide, not per node: plurality is a property of the whole attestation corpus.
    errs += validate_attester_plurality()
    return errs


def _phase_boundary_failures(node_ids: List[str] | None, findings: List[str]) -> List[str]:
    """
    `capability_phase_boundary_6` -- Phase 1 must produce the same findings with the
    attestation corpus ABSENT as it does with it present.

    This is the seam made mechanical rather than conventional. A split held only by a
    docstring lasts until the first agent who adds one attestation read to a Phase-1
    helper because it was convenient; nothing would report it, and Phase 1 would quietly
    stop being runnable in the fix-until-green loop -- while still exiting 0.

    KNOWN BLIND SPOT (Mandate 6): this is a BEHAVIOURAL test, not a static one. It
    catches a Phase-1 read whose result changes the findings, which is the definition of
    a dependency on this tree -- but a read that happens to produce identical output
    today (a check that fires only on a malformed record, say) is a LATENT dependency it
    cannot see. Closing that needs a static reachability pass over this module's AST,
    which is named work, not a threshold to tune.

    Rebinds a module global for the duration of the probe and restores it in a
    `finally`, so this is not safe to call from two threads at once. run_all drives this
    stage serially; if that ever changes, pass the directory down instead of swapping it.
    """
    global _ATTESTATION_DIR

    probe = _ATTESTATION_DIR.parent / _ABSENT_ATTESTATION_PROBE
    if probe.exists():
        raise FileExistsError(
            f"the Phase-1 boundary probe path '{probe}' exists, so Phase 1 cannot be "
            f"re-run with the attestation corpus absent and the seam is unchecked. "
            f"Delete it rather than skipping the check."
        )
    real = _ATTESTATION_DIR
    try:
        _ATTESTATION_DIR = probe
        without = _phase1_findings(node_ids)
    except Exception as exc:  # noqa: BLE001 - naming the breach beats a bare traceback
        return [
            f"capability_phase_boundary_6: Phase 1 (artifact-free) CRASHED when re-run "
            f"with validation_reports/attestation/ absent: {type(exc).__name__}: {exc}. "
            f"A Phase-1 check may not require an agent-authored artifact to exist -- that "
            f"is what makes it runnable in the fix-until-green loop. Move the check that "
            f"reads the corpus into `_phase2_findings`."
        ]
    finally:
        _ATTESTATION_DIR = real

    if without == findings:
        return []
    only_with = [f for f in findings if f not in without]
    only_without = [f for f in without if f not in findings]
    return [
        f"capability_phase_boundary_6: Phase 1 (artifact-free) produced "
        f"{len(findings)} finding(s) with validation_reports/attestation/ present and "
        f"{len(without)} with it absent, so it READS the attestation corpus and is not "
        f"artifact-free. {len(only_with)} finding(s) appear only when the corpus is "
        f"present, {len(only_without)} only when it is absent. First present-only: "
        f"{(only_with[:1] or ['<none>'])[0][:160]!r}. First absent-only: "
        f"{(only_without[:1] or ['<none>'])[0][:160]!r}. Move the check that reads the "
        f"corpus into `_phase2_findings` and register its §-ref as Phase 2 in CHECK_PHASE."
    ]


def _phase_partition_failures(findings: List[str], phase: int) -> List[str]:
    """
    `capability_phase_partition_6` -- a finding may only cite §-refs registered to the
    phase that produced it.

    The per-phase reconciliation. `_phase_boundary_failures` proves Phase 1 does not
    READ an artifact; this proves the two halves still REPORT what their contract rows
    say they report, so a check cannot migrate across the seam -- or be relabelled into
    the other phase -- without being named.

    KNOWN BLIND SPOT (Mandate 6): §6A, §6B and §6C findings cite no §-ref in their text,
    so this check cannot see them. That is safe in the direction that matters: all three
    are Phase 1, and the risk this guards is a Phase-2 check (which always cites §6F/§6G/
    §6H) surfacing in the Phase-1 half. Giving §6A-§6C messages their own refs would
    close it and is a message-text change, not a threshold.
    """
    seen: Dict[tuple, tuple] = {}
    for finding in findings:
        for ref in _SECTION_REF_RE.findall(finding):
            registered = CHECK_PHASE.get(ref)
            if registered == phase:
                continue
            key = (ref, registered)
            count, example = seen.get(key, (0, finding))
            seen[key] = (count + 1, example)

    errs: List[str] = []
    for (ref, registered), (count, example) in sorted(seen.items(), key=lambda kv: str(kv[0])):
        where = f"Phase {registered}" if registered is not None else "no phase at all"
        errs.append(
            f"capability_phase_partition_6: {count} finding(s) reported by the Phase "
            f"{phase} half of §6 cite {ref}, which CHECK_PHASE registers as {where}. A "
            f"check may not straddle the seam: either it needs an agent-authored "
            f"artifact to run (Phase 2) or it does not (Phase 1). First: "
            f"{example[:200]!r}"
        )
    return errs


def validate_capability_provision(node_ids: List[str] | None = None) -> List[str]:
    """
    PHASE 1 -- §6A/§6B/§6C/§6D/§6E, plus the two gates that keep the seam real.

    Artifact-free by construction and by check: reads the knowledge graph, the nodes'
    `requires` declarations and CAPABILITY_PROVIDERS, and runs with
    validation_reports/attestation/ absent. Measured 2026-09-08 on this tree: 75
    findings in 0.1s, 74 of them §6D.
    """
    findings = _phase1_findings(node_ids)
    return (findings
            + _phase_boundary_failures(node_ids, findings)
            + _phase_partition_failures(findings, 1))


def validate_capability_attestation(node_ids: List[str] | None = None) -> List[str]:
    """
    PHASE 2 -- §6F/§6G/§6H. Every check here reads validation_reports/attestation/.

    Gated on Phase 1 being green: an attestation is a ruling about rendered content, and
    there is no sense asking whether an Attester's verdict still holds on a node whose
    declaration does not even cite its own competency. Measured 2026-09-08: 90 findings
    in 9.9s (7 §6F-freshness, 83 §6F-CONTRADICTED), dominated by the re-render sweep.
    """
    findings = _phase2_findings(node_ids)
    return findings + _phase_partition_failures(findings, 2)


def validate_capability_declarations(node_ids: List[str] | None = None) -> List[str]:
    """
    Both phases of §6, for callers that want the whole picture in one list.

    Kept as the module's public entry point because `scripts/hardening_supervisor.py`
    bands the findings by section ref rather than by phase and needs both. Callers that
    only want the fast half should call `validate_capability_provision` directly -- it
    is ~100x cheaper and needs nothing on disk. `tests/attester_packets.py` was moved
    onto it with this split; its §6D queue never needed the attestation sweep it had
    been dragging in behind the whole-contract call.
    """
    return validate_capability_provision(node_ids) + validate_capability_attestation(node_ids)


if __name__ == "__main__":
    import argparse
    import sys

    # --phase mirrors run_all's. Phase 1 is ~100x cheaper (0.1s against 9.9s: the
    # attestation half re-renders every attested seed), so a mutation aimed at §6A-§6E
    # should not pay for the corpus sweep -- "a check that is expensive to prove tends to
    # end up unproven" is why validate_compat grew --only.
    ap = argparse.ArgumentParser(description="§6 capability contract")
    ap.add_argument("--phase", type=int, choices=(1, 2), default=None,
                    help="1 = artifact-free (§6A-§6E); 2 = attestation (§6F-§6H)")
    args = ap.parse_args()

    phase1 = validate_capability_provision() if args.phase in (None, 1) else []
    phase2 = validate_capability_attestation() if args.phase in (None, 2) else []
    over_floor = len(phase1) > _PROVISION_FLOOR
    failures = phase1 + phase2
    if failures:
        print(f"Capability contract: {len(failures)} failure(s) "
              f"({len(phase1)} Phase 1 / artifact-free, floor {_PROVISION_FLOOR}; "
              f"{len(phase2)} Phase 2 / attestation).")
        for f in failures:
            print(f"  - {f}")
    else:
        print("Capability contract: all nodes declare, cite, cover, and are provided for.")
    sys.exit(1 if (over_floor or phase2) else 0)
