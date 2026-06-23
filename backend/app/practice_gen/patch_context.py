import re

file_path = "/Users/enrichmentcap/Documents/antigravity/ccmed/backend/app/practice_gen/compatibility.py"
with open(file_path, "r") as f:
    content = f.read()

# Add context to length_measurement, mass_capacity, time_reading, calendar, fractions, shapes_2d, area, perimeter, missing_number
updates = {
    '"length_measurement": {': '        "context": ["pure", "word_problem"],',
    '"mass_capacity": {': '        "context": ["pure", "word_problem"],',
    '"time_reading": {': '        "context": ["pure", "word_problem"],',
    '"calendar": {': '        "context": ["pure", "word_problem"],',
    '"fractions": {': '        "context": ["pure", "word_problem"],',
    '"area": {': '        "context": ["pure", "word_problem"],',
    '"perimeter": {': '        "context": ["pure", "word_problem"],',
}

for key, append_str in updates.items():
    if key in content:
        # Check if already has context
        segment = content[content.find(key):content.find("},", content.find(key))]
        if '"context":' not in segment:
            content = content.replace(key, key + "\n" + append_str)

with open(file_path, "w") as f:
    f.write(content)
