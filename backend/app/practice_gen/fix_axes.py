import os
import sys

# Add backend to path so we can import
sys.path.insert(0, os.path.abspath('.'))

from backend.app.practice_gen.compatibility import VARIANTS_BY_DNA
from backend.app.practice_gen.axes_catalog import CONCEPT_AXES_CATALOG

new_catalog = {}
for concept, axes in CONCEPT_AXES_CATALOG.items():
    concept_variants = VARIANTS_BY_DNA.get(concept, {})
    new_axes = []
    for axis in axes:
        if axis.get("name") in concept_variants:
            print(f"Removing {axis['name']} from {concept} (it is a variant)")
        else:
            new_axes.append(axis)
    
    # If a concept has no axes left, give it a default continuous one
    if not new_axes and concept != "probability_language":
        print(f"Adding default number_difficulty to {concept}")
        new_axes.append({
            "name": "number_difficulty",
            "label": "Number Difficulty",
            "dim_type": "continuous",
            "default_min": 0.0,
            "default_max": 1.0,
            "divisions": 5,
            "default": 0.5,
        })
    new_catalog[concept] = new_axes

print("\n--- RESULTS ---")
for c, axes in new_catalog.items():
    print(f"{c}: {[a['name'] for a in axes]}")
