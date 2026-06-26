import os
import sys
import pprint

sys.path.insert(0, os.path.abspath('.'))

from backend.app.practice_gen.compatibility import VARIANTS_BY_DNA
from backend.app.practice_gen.axes_catalog import CONCEPT_AXES_CATALOG

new_catalog = {}
for concept, axes in CONCEPT_AXES_CATALOG.items():
    concept_variants = VARIANTS_BY_DNA.get(concept, {})
    new_axes = []
    for axis in axes:
        if axis.get("name") in concept_variants:
            pass
        else:
            new_axes.append(axis)
    
    # If a concept has no axes left, give it a default continuous one
    if not new_axes and concept != "probability_language":
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

with open("backend/app/practice_gen/axes_catalog.py", "r") as f:
    lines = f.readlines()

out = []
for i, line in enumerate(lines):
    if line.startswith("CONCEPT_AXES_CATALOG: Dict[str, List[dict]] = {"):
        out.extend(lines[:i+1])
        break

# format new_catalog
formatted = pprint.pformat(new_catalog, sort_dicts=False, indent=4)
# remove opening and closing braces
formatted = formatted[1:-1]
out.append(formatted + "\n}")
out.append("\n\n")

for i, line in enumerate(lines):
    if line.startswith("def get_axes_for_concept"):
        out.extend(lines[i:])
        break

with open("backend/app/practice_gen/axes_catalog.py", "w") as f:
    f.writelines(out)

print("Rewrote axes_catalog.py")
