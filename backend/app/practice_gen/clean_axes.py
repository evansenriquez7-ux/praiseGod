import pprint

with open("backend/app/practice_gen/axes_catalog.py", "r") as f:
    text = f.read()

# Instead of parsing the text, we will just evaluate it as a python module.
import importlib.util
import sys
spec = importlib.util.spec_from_file_location("axes_catalog_temp", "backend/app/practice_gen/axes_catalog.py")
foo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(foo)

cat = foo.CONCEPT_AXES_CATALOG

# Fix patterns
cat["patterns"] = [{
    "name": "number_difficulty",
    "label": "Number Difficulty",
    "dim_type": "continuous",
    "default_min": 0.0,
    "default_max": 1.0,
    "divisions": 5,
    "default": 0.5,
}]

# Fix perimeter
cat["perimeter"] = [{
    "name": "number_difficulty",
    "label": "Number Difficulty",
    "dim_type": "continuous",
    "default_min": 0.0,
    "default_max": 1.0,
    "divisions": 5,
    "default": 0.5,
}]

# Fix time_reading
cat["time_reading"] = [{
    "name": "number_difficulty",
    "label": "Time Interval Difficulty",
    "dim_type": "continuous",
    "default_min": 0.0,
    "default_max": 1.0,
    "divisions": 5,
    "default": 0.5,
}]

# Make sure all options have dim_type: discrete
for concept, axes in cat.items():
    for axis in axes:
        if "options" in axis and "dim_type" not in axis:
            axis["dim_type"] = "discrete"

with open("backend/app/practice_gen/axes_catalog.py", "r") as f:
    lines = f.readlines()

out = []
for i, line in enumerate(lines):
    if line.startswith("CONCEPT_AXES_CATALOG: Dict[str, List[dict]] = {"):
        out.extend(lines[:i+1])
        break

formatted = pprint.pformat(cat, sort_dicts=False, indent=4)
formatted = formatted[1:-1]
out.append(formatted + "\n}")
out.append("\n\n")

for i, line in enumerate(lines):
    if line.startswith("def get_axes_for_concept"):
        out.extend(lines[i:])
        break

with open("backend/app/practice_gen/axes_catalog.py", "w") as f:
    f.writelines(out)

print("Scrubbed remaining axes!")
