"""
Practice Generation — Difficulty Axes Catalog
==============================================

UI-ready axis definitions per DNA concept. Used by the
/api/matatag/difficulty-axes/{node_id} endpoint to populate
the Problem Lab axis controls.

Each entry is a list of axis dicts:
  {
    "name":    str,           # matches key in DNA.difficulty_axes
    "label":   str,           # human-readable label for the UI
    "options": [              # ordered easy → hard
      {"value": str, "label": str},
      ...
    ],
    "default": str            # value of the easiest / most common option
  }

================================================================================
Axis policy (2026-07-01)
================================================================================

The catalog distinguishes between two kinds of axis bounds:

  1. RESULT-BOUND axes (kept):
     `max_sum` (addition), `max_product` (multiplication), `max_total` (money).
     These bound the *result* of the operation. KEEP them on a node only if
     the LC explicitly says "sums up to N", "products up to N", or "total up
     to N" — i.e. the result ceiling is the curriculum's pedagogical target.

  2. OPERAND-BOUND competencies (no axis needed):
     Most MATATAG K-3 LCs say "operands less than N" (e.g. "Subtract numbers
     where both numbers are less than 100"). The operand bound is already
     enforced by the DNA's per-grade `_PARAM_BOUNDS[grade]` (g1: < 100,
     g2: < 1000, g3: < 10000). Adding a result-bound axis on top of this
     is redundant and causes the audit to enumerate 5x the profile space
     for the same generated problems.

     Specifically removed in this refactor:
       - `max_difference` from all subtraction nodes (9 nodes, all 9 LCs
         say "less than N" / "up to 20" — operand-bound, not result-bound)
       - `max_quotient` from all division nodes (10 nodes, all 10 LCs
         say "2,3,4,5,10 tables" or "2- to 3-digit" — operand-bound via
         per-grade bounds and table-level variants)

     If a future LC says "differences up to N" or "quotients up to N",
     re-add the axis to that node's lab config and update the DNA's
     `profile.get("max_*")` lookup to use it.

  3. `number_difficulty` is a per-number cognitive score (digit sum +
     divisibility + magnitude) — kept on all operational nodes. It does
     real work for some LCs (e.g. "identify the place value of the digit
     7 in 873") and noise for others. Decided per-LC as needed.
================================================================================
"""

from __future__ import annotations

from typing import Dict, List


# ═══════════════════════════════════════════════════════════════════════════════
# CATALOG
# ═══════════════════════════════════════════════════════════════════════════════

CONCEPT_AXES_CATALOG: Dict[str, List[dict]] = {
   'counting': [   {   'name': 'range',
                        'label': 'Number Range',
                        'dim_type': 'continuous',
                        'scale': 'logarithmic',
                        'default_min': 10,
                        'default_max': 10000,
                        'divisions': 5,
                        'default': 0.0}],
    'comparing_ordering': [   {   'name': 'max_value',
                                  'label': 'Maximum Value',
                                  'dim_type': 'continuous',
                                  'scale': 'logarithmic',
                                  'default_min': 20,
                                  'default_max': 10000,
                                  'divisions': 5,
                                  'default': 0.5},
                              {   'name': 'value_max',
                                  'label': 'Maximum Value',
                                  'dim_type': 'continuous',
                                  'scale': 'logarithmic',
                                  'default_min': 5,
                                  'default_max': 50,
                                  'divisions': 5,
                                  'default': 0.5},
                              {   'name': 'number_difficulty',
                                  'label': 'Number Difficulty',
                                  'dim_type': 'continuous',
                                  'default_min': 0.0,
                                  'default_max': 1.0,
                                  'divisions': 5,
                                  'default': 0.5}],
    'ordinal_numbers': [
        {
            'name': 'ordinal_range',
            'label': 'Ordinal Range',
            'dim_type': 'continuous',
            'scale': 'logarithmic',
            'default_min': 1,
            'default_max': 100,
            'divisions': 5,
            'default': 0.5,
        }
    ],
    'addition': [   {   'name': 'max_sum',
                        'label': 'Maximum Sum',
                        'dim_type': 'continuous',
                        'scale': 'logarithmic',
                        'default_min': 2,
                        'default_max': 1000,
                        'divisions': 5,
                        'default': 0.5},
                    {   'name': 'regrouping',
                        'label': 'Regrouping (Carrying)',
                        'dim_type': 'discrete',
                        'options': [   {   'value': 'none',
                                           'label': 'No Regrouping (0 places)'},
                                       {   'value': 'one_place',
                                           'label': 'Regroup One Place'},
                                       {   'value': 'two_places',
                                           'label': 'Regroup Two Places'},
                                       {   'value': 'three_places',
                                           'label': 'Regroup Three Places'},
                                       {   'value': 'four_places',
                                           'label': 'Regroup Four+ Places'}],
                        'default': 'none'},
                    {   'name': 'number_difficulty',
                        'label': 'Number Difficulty',
                        'dim_type': 'continuous',
                        'default_min': 0.0,
                        'default_max': 1.0,
                        'divisions': 5,
                        'default': 0.5}],
    'subtraction': [   {   'name': 'regrouping',
                           'label': 'Regrouping (Borrowing)',
                           'dim_type': 'discrete',
                           'options': [   {   'value': 'none',
                                              'label': 'No Borrowing (0 places)'},
                                          {   'value': 'one_place',
                                              'label': 'Borrow One Place'},
                                          {   'value': 'two_places',
                                              'label': 'Borrow Two Places'},
                                          {   'value': 'three_places',
                                              'label': 'Borrow Three Places'},
                                          {   'value': 'four_places',
                                              'label': 'Borrow Four+ Places'}],
                           'default': 'none'},
                       {   'name': 'number_difficulty',
                           'label': 'Number Difficulty',
                           'dim_type': 'continuous',
                           'default_min': 0.0,
                           'default_max': 1.0,
                           'divisions': 5,
                           'default': 0.5}],
    'missing_number': [   {   'name': 'number_difficulty',
                              'label': 'Number Difficulty',
                              'dim_type': 'continuous',
                              'default_min': 0.0,
                              'default_max': 1.0,
                              'divisions': 5,
                              'default': 0.5}],
    'place_value': [   {   'name': 'digit_count',
                           'label': 'Number of Digits',
                           'options': [   {   'value': '2_digit',
                                              'label': '2-Digit Numbers'},
                                          {   'value': '3_digit',
                                              'label': '3-Digit Numbers'},
                                          {   'value': '4_digit',
                                              'label': '4-Digit Numbers'}],
                           'default': '2_digit',
                           'dim_type': 'discrete'}],
    'number_reading': [   {   'name': 'range',
                              'label': 'Number Range',
                              'dim_type': 'continuous',
                              'scale': 'logarithmic',
                              'default_min': 10,
                              'default_max': 100}],
    'patterns': [   {   'name': 'number_difficulty',
                        'label': 'Number Difficulty',
                        'dim_type': 'continuous',
                        'default_min': 0.0,
                        'default_max': 1.0,
                        'divisions': 5,
                        'default': 0.5}],
    'fractions': [   {   'name': 'number_difficulty',
                         'label': 'Number Difficulty',
                         'dim_type': 'continuous',
                         'default_min': 0.0,
                         'default_max': 1.0,
                         'divisions': 5,
                         'default': 0.5}],
    'money_peso': [   {   'name': 'max_total',
                          'label': 'Maximum Total',
                          'dim_type': 'continuous',
                          'scale': 'logarithmic',
                          'default_min': 100,
                          'default_max': 10000,
                          'divisions': 5,
                          'default': 0.5},
                      {   'name': 'number_difficulty',
                          'label': 'Number Difficulty',
                          'dim_type': 'continuous',
                          'default_min': 0.0,
                          'default_max': 1.0,
                          'divisions': 5,
                          'default': 0.5}],
    'multiplication': [   {   'name': 'max_product',
                              'label': 'Maximum Product',
                              'dim_type': 'continuous',
                              'scale': 'logarithmic',
                              'default_min': 4,
                              'default_max': 1000,
                              'divisions': 5,
                              'default': 0.5},
                          {   'name': 'number_difficulty',
                              'label': 'Number Difficulty',
                              'dim_type': 'continuous',
                              'default_min': 0.0,
                              'default_max': 1.0,
                              'divisions': 5,
                              'default': 0.5}],
    'division': [   {   'name': 'number_difficulty',
                        'label': 'Number Difficulty',
                        'dim_type': 'continuous',
                        'default_min': 0.0,
                        'default_max': 1.0,
                        'divisions': 5,
                        'default': 0.5}],
    'rounding': [   {   'name': 'number_difficulty',
                        'label': 'Number Difficulty',
                        'dim_type': 'continuous',
                        'default_min': 0.0,
                        'default_max': 1.0,
                        'divisions': 5,
                        'default': 0.5}],
    'order_of_operations': [   {   'name': 'number_size',
                                   'label': 'Number Size',
                                   'options': [   {   'value': '1_digit',
                                                      'label': 'Single-Digit'},
                                                  {   'value': '2_digit',
                                                      'label': 'Two-Digit'}],
                                   'default': '1_digit',
                                   'dim_type': 'discrete'}],
    'area': [   {   'name': 'number_difficulty',
                    'label': 'Number Difficulty',
                    'dim_type': 'continuous',
                    'default_min': 0.0,
                    'default_max': 1.0,
                    'divisions': 5,
                    'default': 0.5}],
    'calendar': [   {   'name': 'calendar_feature',
                        'label': 'Calendar Feature',
                        'options': [   {   'value': 'days_order',
                                           'label': 'Days of the Week in '
                                                    'Order'},
                                       {   'value': 'months_order',
                                           'label': 'Months of the Year in '
                                                    'Order'},
                                       {   'value': 'full_calendar',
                                           'label': 'Full Calendar Grid'}],
                        'default': 'days_order',
                        'dim_type': 'discrete'}],
    'geometric_lines': [   {   'name': 'number_difficulty',
                               'label': 'Number Difficulty',
                               'dim_type': 'continuous',
                               'default_min': 0.0,
                               'default_max': 1.0,
                               'divisions': 5,
                               'default': 0.5}],
    'length_measurement': [   {   'name': 'number_difficulty',
                                  'label': 'Number Difficulty',
                                  'dim_type': 'continuous',
                                  'default_min': 0.0,
                                  'default_max': 1.0,
                                  'divisions': 5,
                                  'default': 0.5}],
    'mass_capacity': [   {   'name': 'number_difficulty',
                             'label': 'Number Difficulty',
                             'dim_type': 'continuous',
                             'default_min': 0.0,
                             'default_max': 1.0,
                             'divisions': 5,
                             'default': 0.5}],
    'perimeter': [   {   'name': 'number_difficulty',
                         'label': 'Number Difficulty',
                         'dim_type': 'continuous',
                         'default_min': 0.0,
                         'default_max': 1.0,
                         'divisions': 5,
                         'default': 0.5}],
    'shapes_2d': [   {   'name': 'number_difficulty',
                         'label': 'Number Difficulty',
                         'dim_type': 'continuous',
                         'default_min': 0.0,
                         'default_max': 1.0,
                         'divisions': 5,
                         'default': 0.5}],
    'symmetry_slides': [   {   'name': 'number_difficulty',
                               'label': 'Number Difficulty',
                               'dim_type': 'continuous',
                               'default_min': 0.0,
                               'default_max': 1.0,
                               'divisions': 5,
                               'default': 0.5}],
    'time_reading': [   {   'name': 'number_difficulty',
                            'label': 'Time Interval Difficulty',
                            'dim_type': 'continuous',
                            'default_min': 0.0,
                            'default_max': 1.0,
                            'divisions': 5,
                            'default': 0.5}],
    'bar_graphs': [   {   'name': 'num_categories',
                          'label': 'Number of Categories',
                          'dim_type': 'continuous',
                          'default_min': 3,
                          'default_max': 6,
                          'divisions': 4,
                          'default': 0.5},
                      {   'name': 'value_max',
                          'label': 'Maximum Value',
                          'dim_type': 'continuous',
                          'default_min': 20,
                          'default_max': 100,
                          'divisions': 4,
                          'default': 0.5}],
    'pictographs': [   {   'name': 'num_categories',
                           'label': 'Number of Categories',
                           'dim_type': 'continuous',
                           'default_min': 3,
                           'default_max': 6,
                           'divisions': 4,
                           'default': 0.5},
                       {   'name': 'value_max',
                           'label': 'Maximum Value per Category',
                           'dim_type': 'continuous',
                           'scale': 'logarithmic',
                           'default_min': 5,
                           'default_max': 50,
                           'divisions': 5,
                           'default': 0.5}],
    'probability_language': []
}

def get_axes_for_concept(concept: str) -> list:
    """Return the UI-ready axis list for a concept, or [] if not found."""
    return CONCEPT_AXES_CATALOG.get(concept, [])


def compute_difficulty_scalar(concept: str, axis_values: dict) -> float:
    """
    Compute a 0.0–1.0 difficulty scalar from the selected axis values.

    For each axis present in axis_values, compute the fraction:
        selected_index / (num_options - 1)

    Return the average across all axes. Falls back to 0.5 if nothing matches.

    For continuous axes declared with ``scale: 'logarithmic'`` and
    ``default_max / default_min >= 10``, the 0.5 scalar maps to the
    geometric mean of the range (not the arithmetic mean). This keeps
    on-grade vocabulary at the mid-difficulty for K-12 ranges that span
    orders of magnitude (e.g. ordinal 1–100, value_max 5–50).
    """
    import math

    axes = CONCEPT_AXES_CATALOG.get(concept, [])
    if not axes:
        return 0.5

    scalars = []
    for axis in axes:
        name = axis["name"]
        if name not in axis_values:
            continue
        selected = axis_values[name]

        if "options" not in axis:
            min_val = axis.get("default_min", 0.0)
            max_val = axis.get("default_max", min_val + 1.0)
            if max_val <= min_val:
                scalars.append(0.5)
            else:
                try:
                    s_val = float(selected)
                except (ValueError, TypeError):
                    scalars.append(0.5)
                    continue
                # Honor the declarative `scale` field. When set to
                # 'logarithmic' on a range whose endpoints span ≥ 10x,
                # invert via geometric-mean mapping. (AGENTS.md rule #4:
                # no silent fallback — if the scale field is missing on
                # a wide range, this still maps linearly rather than
                # silently switching to log.)
                scale = axis.get("scale")
                if (
                    scale == "logarithmic"
                    and min_val > 0
                    and max_val / min_val >= 10
                    and s_val > 0
                ):
                    log_min = math.log10(min_val)
                    log_max = math.log10(max_val)
                    if log_max > log_min:
                        s = (math.log10(s_val) - log_min) / (log_max - log_min)
                        scalars.append(max(0.0, min(1.0, s)))
                        continue
                s = (s_val - min_val) / (max_val - min_val)
                scalars.append(max(0.0, min(1.0, s)))
            continue

        option_values = [o["value"] for o in axis["options"]]
        if selected not in option_values:
            continue
        idx = option_values.index(selected)
        n = len(option_values)
        scalars.append(idx / (n - 1) if n > 1 else 0.5)

    return sum(scalars) / len(scalars) if scalars else 0.5
