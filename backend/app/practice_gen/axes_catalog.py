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
                                  'default_min': 20,
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
    'ordinal_numbers': [
        {
            'name': 'ordinal_range',
            'label': 'Ordinal Range',
            'dim_type': 'continuous',
            'default_min': 1,
            'default_max': 100,
            'divisions': 5,
            'default': 0.5,
        }
    ],
    'addition': [   {   'name': 'max_sum',
                        'label': 'Maximum Sum',
                        'dim_type': 'continuous',
                        'default_min': 2,
                        'default_max': 1000,
                        'divisions': 5,
                        'default': 0.5},
                    {   'name': 'regrouping',
                        'label': 'Regrouping (Carrying)',
                        'dim_type': 'discrete',
                        'options': [   {   'value': 'none',
                                           'label': 'No Regrouping'},
                                       {   'value': 'ones',
                                           'label': 'Regroup Ones'},
                                       {   'value': 'tens',
                                           'label': 'Regroup Tens'},
                                       {   'value': 'double',
                                           'label': 'Regroup Ones and Tens'}],
                        'default': 'none'},
                    {   'name': 'number_difficulty',
                        'label': 'Number Difficulty',
                        'dim_type': 'continuous',
                        'default_min': 0.0,
                        'default_max': 1.0,
                        'divisions': 5,
                        'default': 0.5}],
    'subtraction': [   {   'name': 'max_difference',
                           'label': 'Maximum Difference (Minuend)',
                           'dim_type': 'continuous',
                           'default_min': 2,
                           'default_max': 1000,
                           'divisions': 5,
                           'default': 0.5},
                       {   'name': 'regrouping',
                           'label': 'Regrouping (Borrowing)',
                           'dim_type': 'discrete',
                           'options': [   {   'value': 'none',
                                              'label': 'No Borrowing'},
                                          {   'value': 'ones',
                                              'label': 'Borrow in Ones Place'},
                                          {   'value': 'tens',
                                              'label': 'Borrow in Tens Place'},
                                          {   'value': 'double',
                                              'label': 'Borrow in Both '
                                                       'Places'}],
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
    'division': [   {   'name': 'max_quotient',
                        'label': 'Maximum Quotient',
                        'dim_type': 'continuous',
                        'default_min': 2,
                        'default_max': 100,
                        'divisions': 5,
                        'default': 0.5},
                    {   'name': 'number_difficulty',
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
                          'divisions': 3,
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
    """
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
                    s = (float(selected) - min_val) / (max_val - min_val)
                    scalars.append(max(0.0, min(1.0, s)))
                except (ValueError, TypeError):
                    scalars.append(0.5)
            continue

        option_values = [o["value"] for o in axis["options"]]
        if selected not in option_values:
            continue
        idx = option_values.index(selected)
        n = len(option_values)
        scalars.append(idx / (n - 1) if n > 1 else 0.5)

    return sum(scalars) / len(scalars) if scalars else 0.5
