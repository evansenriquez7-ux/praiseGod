"""
build_ccss_crosswalk.py

Maps Kolibri/Khan Academy exercise nodes to CCSS standard codes
by matching their topic_path against the known KA grade/domain structure.

Khan Academy "Math by grade" tree mirrors CCSS almost exactly:
  Math > Math by grade > Kindergarten > Counting > ...  -> K.CC
  Math > Math by grade > 3rd grade > Fractions > ...    -> 3.NF
  Math > 8th grade > Linear equations > ...             -> 8.EE

Also handles:
  - "Math" (course-based: Arithmetic, Pre-algebra, Algebra, Geometry, etc.)
  - "English Language Arts" (Grammar, Reading, Writing)

Output: scripts/perseus_extractor/output/ccss_crosswalk.json
  {
    "K_CC_A_1": ["node_id1", "node_id2", ...],
    "3_NF_A_1": [...],
    ...
  }

Also produces: ccss_crosswalk_annotated.json with full exercise metadata.
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict

TEMPLATES_DIR = Path(__file__).parent / "output" / "perseus_templates"
OUTPUT_DIR = Path(__file__).parent / "output"
CCMED_STANDARDS_DIR = Path(__file__).parent.parent.parent / "data" / "processed" / "by_standard"

# ---------------------------------------------------------------------------
# CCSS code inference rules based on KA topic path keywords
# Format: (path_keywords_lower, ccss_code_prefix)
# Matched in order — first match wins.
# Keywords are checked against the FULL path string (lowercased, joined).
# ---------------------------------------------------------------------------

# Grade prefix map from KA grade label (Math by grade tree)
GRADE_MAP = {
    "kindergarten": "K",
    "1st grade": "1", "2nd grade": "2", "3rd grade": "3",
    "4th grade": "4", "5th grade": "5", "6th grade": "6",
    "7th grade": "7", "8th grade": "8",
    "get ready for 3rd grade": "2", "get ready for 4th grade": "3",
    "get ready for 5th grade": "4", "get ready for 6th grade": "5",
    "get ready for 7th grade": "6", "get ready for 8th grade": "7",
}

    # KA course-name -> CCSS grade band (for course-based tree: Math > Early math, Arithmetic, etc.)
COURSE_GRADE_MAP = {
    "early math": "K",        # K-2 mix; domain will disambiguate
    "arithmetic": "3",        # 3rd-5th mix; domain will disambiguate
    "pre-algebra": "6",       # 6th-7th
    "get ready for algebra 1": "7",
    "algebra 1": "HS",
    "get ready for geometry": "HS",
    "geometry": "HS",
    "get ready for algebra 2": "HS",
    "algebra 2": "HS",
    "trigonometry": "HS",
    "get ready for precalculus": "HS",
    "precalculus": "HS",
    "statistics & probability": "HS",
    "ap®︎ calculus ab": "HS",
    "ap®︎ calculus bc": "HS",
    "ap®︎ statistics": "HS",
    "get ready for ap® calculus": "HS",
    "get ready for ap® statistics": "HS",
    "multivariable calculus": "HS",
    "differential equations": "HS",
    "linear algebra": "HS",
    "integrated math 1": "HS",
    "integrated math 2": "HS",
    "integrated math 3": "HS",
    "high school statistics": "HS",
    "high school": "HS",
    # Math by grade course labels
    "illustrative mathematics": "?",  # skip - no clear single grade
    "eureka math/engageny": "?",       # handled via grade sub-nodes below
}

# Eureka Math/EngageNY grade label -> CCSS grade
EUREKA_GRADE_MAP = {
    "kindergarten (eureka": "K",
    "1st grade (eureka": "1",
    "2nd grade (eureka": "2",
    "3rd grade (eureka": "3",
    "4th grade (eureka": "4",
    "5th grade (eureka": "5",
    "6th grade (eureka": "6",
    "7th grade (eureka": "7",
    "8th grade (eureka": "8",
}

# For Early math sub-units, refine grade from K vs 1 vs 2
EARLY_MATH_UNIT_GRADE = {
    "counting": "K",
    "addition and subtraction intro": "K",
    "place value (tens and hundreds)": "1",
    "addition and subtraction within 20": "1",
    "addition and subtraction within 100": "1",
    "addition and subtraction within 1000": "2",
    "measurement and data": "2",
}

# For Arithmetic sub-units, refine grade
ARITHMETIC_UNIT_GRADE = {
    "intro to multiplication": "3",
    "1-digit multiplication": "3",
    "intro to division": "3",
    "understand fractions": "3",
    "place value through 1,000,000": "4",
    "add and subtract through 1,000,000": "4",
    "multiply 1- and 2-digit numbers": "4",
    "divide with remainders": "4",
    "fractions": "4",
    "multiply fractions": "5",
    "divide fractions": "5",
    "decimals": "5",
    "multi-digit": "5",
    "factors and multiples": "4",
}

# Domain/cluster keyword -> CCSS domain code (grade-prefixed)
# More specific entries must come before more general ones
DOMAIN_RULES = [
    # -------- Counting & Cardinality (K only) --------
    # Must match very specifically — "counting" alone is too broad
    (["counting and cardinality", "count with small", "count to 1", "count by tens",
      "count objects", "count tens", "count in order", "count in pictures",
      "missing numbers", "numbers to 100", "count 1", "how many objects",
      "comparing numbers to 10", "comparing small numbers", "numbers 0 to 20",
      "numbers 0 to 120", "1 more or 1 less", "one more or one less",
      "more than", "fewer than", "comparing numbers"], "CC"),

    # -------- Number & Operations — Fractions --------
    # MUST come before OA so "multiply fractions" beats generic "multiply"
    (["fractions on the number line", "equivalent fraction", "compare fraction",
      "fraction of a whole", "unit fraction", "mixed number", "improper fraction",
      "add fraction", "subtract fraction", "multiply fraction", "divide fraction",
      "multiply fractions", "dividing fractions", "multiplying fractions",
      "fraction by whole", "whole number fraction", "fraction word problem",
      "decompose fraction", "fraction as division", "understand fraction",
      "recognize fraction", "fractions of shapes", "fractions of a set",
      "multiply mixed number", "divide mixed number", "fraction multiplication",
      "fraction division", "fractions and whole numbers",
      "multiply unit fraction", "divide unit fraction",
      "visually multiply", "visually divide"], "NF"),

    # -------- Operations & Algebraic Thinking --------
    # OA before NBT so "addition word problem" matches OA not NBT
    (["operations and algebraic thinking", "word problem", "number pattern",
      "fact family", "times table", "multiplication table",
      "properties of multiplication", "associative property", "commutative property",
      "write multiplication", "write division", "missing factor", "unknowns",
      "two-step", "multi-step", "multiply", "divide", "division",
      "repeated addition", "array", "making small numbers", "make 10",
      "add 3 numbers", "equal sign", "true or false equations",
      "relate addition and subtraction", "addition and subtraction intro",
      "addition and subtraction word problems",
      "intro to multiplication", "multiplication on the number line",
      "1-digit multiplication", "distributive property"], "OA"),

    # -------- Measurement & Data --------
    (["measurement and data", "measure length", "measure in inches", "ruler",
      "line plot", "bar graph", "picture graph", "telling time", "time to the",
      "elapsed time", "money", "coins", "dollars and cents", "liquid volume",
      "mass in grams", "area of rectangle", "area and perimeter", "perimeter of",
      "classify shapes", "attributes of shapes",
      # NOTE: "volume" alone is ambiguous; keep compound forms
      "volume of a rectangular", "volume of prism"], "MD"),

    # -------- Geometry --------
    (["geometry", "2d shapes", "3d shapes", "polygon", "quadrilateral",
      "composing shapes", "partitioning shapes", "parallel lines", "perpendicular lines",
      "line of symmetry", "coordinate plane", "coordinate grid", "plot point",
      "classify angle", "acute angle", "obtuse angle",
      "reflection", "rotation", "translation", "dilation", "congruent", "similar figures",
      "scale drawing", "scale copy", "cross section",
      "basic shapes", "properties of shapes", "composing shapes"], "G"),

    # -------- Ratios & Proportional Relationships (6-7) --------
    (["ratios and rates", "equivalent ratio", "unit rate", "proportional relationship",
      "constant of proportionality", "tape diagram", "double number line",
      "percent problems", "percent of", "ratio word problem",
      "percentages", "percent & rational"], "RP"),

    # -------- The Number System (6-8) --------
    (["negative number", "integers on a number line", "rational number",
      "absolute value", "opposite numbers", "adding negative", "subtracting negative",
      "multiplying negative", "dividing negative", "greatest common factor",
      "least common multiple", "gcf and lcm", "long division with remainders",
      "dividing fractions", "division of fraction", "factors and multiples"], "NS"),

    # -------- Expressions & Equations (6-8) --------
    (["variables & expressions", "equations & inequalities", "like terms",
      "one-step equation", "two-step equation", "solving equations",
      "linear equations", "slope", "slope-intercept", "y = mx", "y=mx",
      "system of equations", "systems of equations",
      "scientific notation", "exponent rules", "properties of exponents",
      "square roots", "cube roots", "irrational numbers",
      "exponents intro", "order of operations"], "EE"),

    # -------- Functions (8) --------
    (["functions", "input and output", "function table", "linear vs nonlinear",
      "comparing functions", "rate of change of a function",
      "graphing linear functions", "slope of a function"], "F"),

    # -------- Statistics & Probability (6-8) --------
    (["statistics", "mean, median", "mean and median", "dot plots",
      "histograms", "box plots", "stem-and-leaf", "scatter plot",
      "bivariate data", "two-way table", "measures of variability",
      "interquartile range", "mean absolute deviation",
      "experimental probability", "theoretical probability",
      "sample spaces", "basic probability"], "SP"),

    # -------- HS: Number & Quantity --------
    (["complex numbers", "imaginary numbers", "vectors", "matrices",
      "rational exponents and radicals", "nth root", "radical expressions"], "HSN"),

    # -------- HS: Algebra --------
    (["polynomial arithmetic", "polynomial factorization", "polynomial division",
      "polynomial graphs", "quadratic formula", "completing the square",
      "quadratic equations", "factoring quadratics", "binomial theorem",
      "rational expressions", "exponential models", "logarithms",
      "solving quadratics", "algebra foundations", "solving equations & inequalities",
      "forms of linear equations", "systems of equations",  # HS-level
      "inequalities (systems", "working with units"], "HSA"),

    # -------- HS: Functions --------
    (["trigonometric functions", "sinusoidal", "inverse functions",
      "composite functions", "piecewise functions",
      "arithmetic sequences", "geometric sequences",
      "domain and range", "transforming functions", "shifting functions",
      "exponential functions", "logarithmic functions",
      "exponential growth", "exponential decay", "modeling with functions"], "HSF"),

    # -------- HS: Geometry --------
    (["congruence", "similarity", "pythagorean theorem",
      "right triangle trigonometry", "law of sines", "law of cosines",
      "unit circle", "radians", "arc length", "sector area",
      "circle theorems", "inscribed angles", "central angles",
      "conic sections", "parabolas", "ellipses", "hyperbolas",
      "geometric proofs", "transformations"], "HSG"),

    # -------- HS: Statistics & Probability --------
    (["normal distribution", "z-scores", "confidence intervals", "hypothesis testing",
      "binomial distribution", "conditional probability",
      "permutations", "combinations", "counting principle", "expected value",
      "randomness, probability, and simulation", "two-way tables, venn"], "HSS"),
]

# ELA domain map
ELA_DOMAIN_RULES = [
    # ---- Language (L) — Grammar & Conventions ----
    # Parts of speech, punctuation, syntax, usage → L standards
    (["parts of speech", "the noun", "the verb", "the pronoun", "the modifier",
      "the preposition", "the conjunction", "punctuation", "syntax",
      "usage and style", "comma", "apostrophe", "semicolon", "colon",
      "grammar", "sentence", "clause", "fragment", "run-on", "subject-verb",
      "pronoun-antecedent", "parallel structure", "dangling modifier",
      "frequently confused words", "common expressions", "style and technique",
      "irregular plural", "irregular verb", "verb tense", "verb aspect",
      "modal verb", "relative pronoun", "relative clause", "relative adverb",
      "adjective", "adverb", "preposition", "conjunction", "article",
      "identifying nouns", "identifying verbs", "identifying prepositions",
      "meet the"], "L"),

    # ---- Reading Informational (RI) — nonfiction, informational, opinions ----
    (["reading informational text", "informational text", "close reading: informational",
      "reading for understanding: informational", "reading opinions",
      "main idea", "text features", "cause and effect",
      "connections between ideas", "relationships between ideas",
      "summarizing informational", "making inferences in informational",
      "evaluating a source", "reading more than one source"], "RI"),

    # ---- Reading Literature (RL) — fiction, poetry, drama, vocab-in-context ----
    (["reading creative fiction", "reading realistic fiction", "reading drama",
      "reading poetry", "close reading: fiction", "reading for understanding: fiction",
      "reading for understanding: drama", "reading for understanding: poetry",
      "applying vocabulary knowledge", "vocabulary",
      "messages and morals", "character", "theme", "elements of a story",
      "elements of a poem", "elements of a drama", "point of view",
      "summarizing stories", "making inferences in literary",
      "figurative language", "context clues", "affixes"], "RL"),

    # ---- Writing (W) ----
    (["writing", "opinion", "argument essay", "narrative writing",
      "informational writing", "research writing", "revise", "edit"], "W"),

    # ---- Speaking & Listening (SL) ----
    (["speaking", "listening", "discussion", "presentation", "collaborate"], "SL"),

    # ---- Reading Foundational (RF) ----
    (["foundational", "phonics", "phonemic", "fluency", "decoding",
      "sight word", "syllable"], "RF"),
]

# ELA grade map — KA ELA tree uses "2nd grade reading" / "3rd grade reading" labels
# Grammar is NOT grade-labeled; assign by topic complexity
GRADE_ELA_MAP = {
    "2nd grade reading": "2",
    "3rd grade reading": "3",
    "kindergarten": "K", "1st grade": "1",
    "4th grade": "4", "5th grade": "5",
    "6th grade": "6", "7th grade": "7", "8th grade": "8",
}

# Grammar topic → CCSS Language grade (based on CCSS placement)
GRAMMAR_GRADE_MAP = {
    # Nouns
    "identifying nouns": "1",
    "singular and plural nouns": "1",
    "common and proper nouns": "2",
    "concrete and abstract nouns": "3",
    "irregular plural nouns: f to -ves": "2",
    "irregular plural nouns: -en": "2",
    "irregular plural nouns: the base": "2",
    "irregular plural nouns: mutant": "2",
    "irregular plural nouns: foreign": "3",
    "irregular plural nouns review": "2",
    # Verbs
    "identifying verbs": "1",
    "introduction to verb agreement": "1",
    "introduction to verb tense": "2",
    "irregular verbs": "2",
    "action, linking, and helping verbs": "3",
    "simple verb aspect": "4",
    "progressive verb aspect": "4",
    "perfect verb aspect": "4",
    "perfect progressive verb aspect": "5",
    "managing time with tense and aspect": "5",
    "modal verbs": "4",
    # Pronouns
    "meet the personal pronoun": "1",
    "the question word": "1",
    "possessive pronouns and adjectives": "2",
    "reflexive pronouns": "2",
    "relative pronouns": "4",
    "indefinite pronouns": "3",
    "pronoun vagueness": "6",
    "pronoun person": "3",
    "pronoun number": "3",
    "choosing between subject and object pronouns": "5",
    "emphatic pronouns": "6",
    # Adjectives/Adverbs
    "meet the adjective": "1",
    "meet the article": "1",
    "choosing between definite and indefinite articles": "1",
    "meet the adverb": "2",
    "using adverbs and adjectives": "2",
    "comparative and superlative adjectives and adverbs": "3",
    "intensifiers and adverbs of degree": "4",
    "adjective order": "5",
    "commas and adjectives": "5",
    "identifying relative adverbs": "4",
    # Prepositions/Conjunctions
    "identifying prepositions": "1",
    "meet the preposition with pictures": "K",
    "prepositions about time and space": "1",
    "common prepositions": "2",
    "compound prepositions": "3",
    "prepositional phrases": "4",
    "coordinating conjunctions": "3",
    "meet the conjunction": "1",
    "coordinating and subordinating conjunctions": "5",
    "correlative conjunctions": "5",
    # Punctuation
    "three ways to end a sentence": "K",
    "meet the comma": "1",
    "punctuating lists": "2",
    "salutations, valedictions, dates, and addresses": "2",
    "introduction to contractions": "2",
    "meet the apostrophe": "2",
    "apostrophes and plurals": "3",
    "introduction to the possessive": "2",
    "advanced (plural) possession": "3",
    "commas and introductory elements": "5",
    "appositives": "5",
    "commas in dialogue": "3",
    "introduction to semicolons": "7",
    "using semicolons and colons": "7",
    "using semicolons and commas": "7",
    "introduction to colons": "7",
    "introduction to dashes": "8",
    "dashes and hyphens": "8",
    "introduction to ellipses": "8",
    "introduction to parentheses": "8",
    "italics, underlines, and quotation marks": "8",
    "choosing between its and it's": "3",
    # Syntax
    "declarative, interrogative, and imperative sentences": "1",
    "simple and compound sentences": "2",
    "rearranging simple and compound sentences": "2",
    "complex and compound-complex sentences": "5",
    "identifying subjects and predicates": "3",
    "identifying subjects, direct objects, and indirect objects": "4",
    "dependent and independent clauses": "4",
    "introduction to phrases and clauses": "4",
    "phrase and clause placement": "5",
    "relative clauses": "5",
    "recognizing fragments": "7",
    "recognizing run-ons and comma splices": "7",
    "subject-verb agreement": "6",
    "pronoun-antecedent agreement": "6",
    "dangling modifiers": "8",
    "parallel structure": "8",
    # Usage
    "frequently confused words: affect/effect": "7",
    "frequently confused words: assorted": "7",
    "frequently confused words: here/hear": "3",
    "frequently confused words: there/their/they're": "3",
    "frequently confused words: to/two/too": "3",
    "common expressions: easy": "3",
    "common expressions: medium": "5",
    "common expressions: hard": "7",
    "style and technique": "8",
    "the sound of language": "8",
}


def detect_grade(topic_path):
    """Detect CCSS grade from topic path list."""
    path_lower = " > ".join(topic_path).lower()

    # 1. Check explicit grade labels (Math by grade tree)
    for label, code in GRADE_MAP.items():
        if label in path_lower:
            return code

    # 2. Check Eureka Math grade labels
    for label, code in EUREKA_GRADE_MAP.items():
        if label in path_lower:
            return code

    # 3. Check KA course names (course-based tree)
    for course, grade in COURSE_GRADE_MAP.items():
        if course in path_lower:
            if grade == "?":
                return None
            # Refine Early math by sub-unit
            if course == "early math":
                for unit, g in EARLY_MATH_UNIT_GRADE.items():
                    if unit in path_lower:
                        return g
                return "K"
            # Refine Arithmetic by sub-unit
            if course == "arithmetic":
                for unit, g in ARITHMETIC_UNIT_GRADE.items():
                    if unit in path_lower:
                        return g
                return "3"
            return grade

    return None


def detect_ela_grade(topic_path, title):
    """Detect CCSS grade from ELA topic path and title."""
    path_lower = " > ".join(topic_path).lower()
    title_lower = (title or "").lower()

    # Reading units have explicit grade labels in path
    for label, code in GRADE_ELA_MAP.items():
        if label in path_lower:
            return code

    # Grammar: look up by exact title
    for exercise_title, grade in GRAMMAR_GRADE_MAP.items():
        if exercise_title in title_lower:
            return grade

    return None


def infer_ccss_code(topic_path, title, description):
    """
    Given a topic path list + title + description,
    return best-guess CCSS standard prefix (e.g. '3_NF', 'K_CC', 'HSA', '2_RL', '3_L').
    Returns None if no match.
    """
    path_str = " > ".join(topic_path).lower()
    title_lower = (title or "").lower()
    desc_lower = (description or "").lower()
    combined = path_str + " " + title_lower + " " + desc_lower

    # Check if it's ELA
    is_ela = "english language arts" in path_str or "grammar" in path_str
    if is_ela:
        grade = detect_ela_grade(topic_path, title)
        for keywords, domain in ELA_DOMAIN_RULES:
            if any(kw in combined for kw in keywords):
                if grade:
                    return f"{grade}_{domain}"
                return domain
        return None

    # Math: detect grade
    grade = detect_grade(topic_path)
    if grade is None:
        return None

    # Match domain
    for keywords, domain in DOMAIN_RULES:
        if any(kw in combined for kw in keywords):
            if grade == "HS":
                if domain.startswith("HS"):
                    return domain
                hs_map = {"OA": "HSA", "EE": "HSA", "F": "HSF",
                          "NF": "HSN", "G": "HSG", "SP": "HSS",
                          "NS": "HSN", "RP": "HSA"}
                return hs_map.get(domain, f"HS_{domain}")
            return f"{grade}_{domain}"

    return None


def ccss_prefix_to_file_pattern(prefix):
    """
    Given a CCSS prefix like '3_NF' or 'K_CC',
    return the glob pattern to match CCMed standard files.
    """
    return prefix


def load_templates():
    """Load all downloaded Perseus template files."""
    templates = []
    if not TEMPLATES_DIR.exists():
        return templates
    for f in TEMPLATES_DIR.glob("*.json"):
        try:
            with open(f) as fh:
                data = json.load(fh)
            templates.append(data)
        except Exception:
            pass
    return templates


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Loading Perseus templates from {TEMPLATES_DIR}...")
    templates = load_templates()
    print(f"  Loaded {len(templates)} templates")

    # Build crosswalk: ccss_prefix -> list of node metadata
    crosswalk = defaultdict(list)
    unmatched = []

    for t in templates:
        node_id = t["node_id"]
        title = t["title"]
        description = t.get("description", "")
        topic_path = t.get("topic_path", [])

        ccss = infer_ccss_code(topic_path, title, description)
        if ccss:
            crosswalk[ccss].append({
                "node_id": node_id,
                "title": title,
                "description": description,
                "topic_path": topic_path,
                "item_count": len(t.get("assessment_items", [])),
                "template_file": f"perseus_templates/{node_id}.json"
            })
        else:
            unmatched.append({
                "node_id": node_id,
                "title": title,
                "topic_path": topic_path
            })

    # Sort by CCSS code
    crosswalk_sorted = dict(sorted(crosswalk.items()))

    print(f"\nCrossWalk results:")
    print(f"  Matched: {sum(len(v) for v in crosswalk.values())} exercises across {len(crosswalk)} CCSS prefixes")
    print(f"  Unmatched: {len(unmatched)}")

    print("\nTop 30 CCSS prefixes by exercise count:")
    for code, items in sorted(crosswalk_sorted.items(), key=lambda x: -len(x[1]))[:30]:
        print(f"  {code}: {len(items)} exercises")

    # Save crosswalk
    out_path = OUTPUT_DIR / "ccss_crosswalk.json"
    with open(out_path, "w") as f:
        json.dump(crosswalk_sorted, f, indent=2)
    print(f"\nSaved crosswalk to {out_path}")

    # Save unmatched for manual review
    unmatched_path = OUTPUT_DIR / "unmatched_exercises.json"
    with open(unmatched_path, "w") as f:
        json.dump(unmatched, f, indent=2)
    print(f"Saved {len(unmatched)} unmatched exercises to {unmatched_path}")

    # Report which CCMed standard files would get coverage
    if CCMED_STANDARDS_DIR.exists():
        ccmed_files = {f.stem for f in CCMED_STANDARDS_DIR.glob("*.json")}
        matched_ccmed = set()
        for ccss_prefix in crosswalk:
            for ccmed_file in ccmed_files:
                if ccmed_file.startswith(ccss_prefix):
                    matched_ccmed.add(ccmed_file)
        print(f"\nCCMed standard files that would get Perseus exercises: {len(matched_ccmed)} / {len(ccmed_files)}")

    return crosswalk_sorted


if __name__ == "__main__":
    main()
