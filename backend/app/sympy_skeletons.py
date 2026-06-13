import random
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr

from typing import Optional


def get_question_skeleton(skill_id: str, seed: Optional[int] = None, grade_level: Optional[int] = None) -> dict:
    """
    Generates a deterministic mathematical skeleton using SymPy based on standard code.
    Returns:
        dict: {
            "skeleton_id": str,
            "variables": dict,
            "stem_template": str,
            "correct_answer": str,
            "options": dict, # Maps option key (e.g. "A", "B", "C", "D") to (value_str, trap_name_or_None)
            "math_expression": str,
            "sympy_correct": Any
        }
    """
    # Clean standard code
    skill_clean = skill_id.upper()
    
    # Determine effective grade level from the skill_id first, then fallback to student grade
    import re
    skill_grade = None
    # Match patterns like "3.OA.A.1" or "K.CC"
    match_grade = re.search(r"^(\d+)\.", skill_clean)
    if match_grade:
        skill_grade = int(match_grade.group(1))
    elif skill_clean.startswith("K"):
        skill_grade = 0
    elif any(hs in skill_clean for hs in ["N-RN", "A-SSE", "A-APR", "A-CED", "A-REI", "F-IF", "F-BF", "F-LE", "G-CO", "S-ID", "APR", "REI", "SSE"]):
        skill_grade = 9 # HS baseline
        
    g_eff = skill_grade if skill_grade is not None else (grade_level if grade_level is not None else 5)

    if seed is None:
        seed = random.randint(1000, 99999)
        
    # Use a local Random instance for thread safety (avoids corrupting global random state)
    rng = random.Random(seed)
    
    # Initialize variables that may or may not be set by generators
    a = b = c = d = 0
    math_expr = ""
    stem_template = ""
    correct_val = ""
    options_list = []

    # =========================================================================
    # STANDARD-SPECIFIC GENERATORS (ordered by grade level)
    # =========================================================================

    # --- Grade K: Counting & Cardinality (CC) ---
    if _match_domain(skill_clean, ["K.CC"]):
        # K.CC.A.1, K.CC.A.2: Counting sequences
        if "K.CC.A" in skill_clean or "K.CC.1" in skill_clean or "K.CC.2" in skill_clean:
            mode = rng.choice(["next", "count_by_10"])
            if mode == "next":
                a = rng.randint(1, 20)
                math_expr = f"{a} + 1"
                stem_template = f"What number comes right after {a}?"
                correct_val = str(a + 1)
                options_list = [
                    (correct_val, None),
                    (str(a - 1), "previous_number"),
                    (str(a + 2), "skipped_one"),
                    (str(a), "same_number")
                ]
            else:
                # Counting by tens
                tens = [10, 20, 30, 40, 50, 60, 70, 80, 90]
                a = rng.choice(tens[:-1])
                math_expr = f"{a} + 10"
                stem_template = f"If you are counting by tens, what number comes after {a}?"
                correct_val = str(a + 10)
                options_list = [
                    (correct_val, None),
                    (str(a + 1), "counted_by_ones"),
                    (str(a - 10), "counted_backwards"),
                    (str(a + 20), "skipped_ten")
                ]
        
        # K.CC.B.4, K.CC.B.5: Cardinality (how many)
        elif "K.CC.B" in skill_clean or "K.CC.4" in skill_clean or "K.CC.5" in skill_clean:
            a = rng.randint(1, 10)
            math_expr = f"count({a})"
            stem_template = f"If you have a row of {a} items and you add one more item at the end, how many items do you have now?"
            correct_val = str(a + 1)
            options_list = [
                (correct_val, None),
                (str(a), "forgot_to_add"),
                (str(a - 1), "subtracted_instead"),
                (str(a + 2), "added_too_many")
            ]
            
        # K.CC.C.6, K.CC.C.7: Comparing numbers
        elif "K.CC.C" in skill_clean or "K.CC.6" in skill_clean or "K.CC.7" in skill_clean:
            a = rng.randint(1, 10)
            b = rng.randint(1, 10)
            while a == b:
                b = rng.randint(1, 10)
            
            math_expr = f"max({a}, {b})"
            correct_val = str(max(a, b))
            stem_template = f"Which number is GREATER (bigger): {a} or {b}?"
            options_list = [
                (str(max(a, b)), None),
                (str(min(a, b)), "selected_smaller"),
                (str(a + b), "added_numbers"),
                ("0", "random_distractor")
            ]

    # --- Grade K: Operations & Algebraic Thinking (OA) ---
    elif _match_domain(skill_clean, ["K.OA"]):
        # K.OA.A.5: Add/Sub within 5
        if "OA.A.5" in skill_clean or "OA.5" in skill_clean:
            a = rng.randint(0, 5)
            b = rng.randint(0, 5)
            op = rng.choice(["+", "-"])
            if op == "+":
                while a + b > 5:
                    b = rng.randint(0, 5)
                correct_val = str(a + b)
                math_expr = f"{a} + {b}"
                stem_template = f"Solve: {a} + {b} = ?"
            else:
                if a < b: a, b = b, a
                correct_val = str(a - b)
                math_expr = f"{a} - {b}"
                stem_template = f"Solve: {a} - {b} = ?"
            
            options_list = [
                (correct_val, None),
                (str(abs(a - b)) if op == "+" else str(a + b), "wrong_operation"),
                (str(int(correct_val) + 1), "off_by_one_up"),
                (str(int(correct_val) - 1) if int(correct_val) > 0 else "4", "off_by_one_down")
            ]
        
        # K.OA.A.4: Making 10
        elif "OA.A.4" in skill_clean or "OA.4" in skill_clean:
            a = rng.randint(1, 9)
            math_expr = f"10 - {a}"
            stem_template = f"If you have {a} items, how many MORE items do you need to make 10?"
            correct_val = str(10 - a)
            options_list = [
                (correct_val, None),
                (str(a), "original_number"),
                (str(10 - a + 1), "off_by_one"),
                (str(a + 1), "neighbor_number")
            ]
        else:
            # Fallback for other K.OA standards
            a = rng.randint(1, 5)
            b = rng.randint(1, 5)
            correct_val = str(a + b)
            math_expr = f"{a} + {b}"
            stem_template = f"If you have {a} items and someone gives you {b} more items, how many do you have in total?"
            options_list = [
                (correct_val, None),
                (str(abs(a - b)), "subtracted"),
                (str(a + b + 1), "off_by_one"),
                (str(a), "first_number")
            ]

    # --- Grade K: Geometry (G) ---
    elif _match_domain(skill_clean, ["K.G"]):
        # Text-only shape questions — no visual references, no "which of these" image prompts.
        # Four question modes give 20+ distinct stems from the same 5 shapes.
        shape_data = {
            "Circle":    {"sides": 0, "corners": 0, "flat": True},
            "Square":    {"sides": 4, "corners": 4, "flat": True},
            "Triangle":  {"sides": 3, "corners": 3, "flat": True},
            "Rectangle": {"sides": 4, "corners": 4, "flat": True},
            "Hexagon":   {"sides": 6, "corners": 6, "flat": True},
        }
        correct_shape = rng.choice(list(shape_data.keys()))
        distractors   = [s for s in shape_data if s != correct_shape]
        info          = shape_data[correct_shape]
        mode          = rng.choice(["sides", "name_from_sides", "corners", "flat_or_solid"])

        if mode == "sides" and info["sides"] > 0:
            # "How many sides does a SQUARE have?"
            math_expr    = f"sides({correct_shape})"
            stem_template = f"How many sides does a {correct_shape.upper()} have?"
            correct_val   = str(info["sides"])
            # Pick three distractors with different side counts
            wrong_counts  = sorted({d_info["sides"] for d, d_info in shape_data.items()
                                     if d != correct_shape and d_info["sides"] != info["sides"]})
            wrong_counts  = rng.sample(wrong_counts, min(3, len(wrong_counts)))
            while len(wrong_counts) < 3:
                wrong_counts.append(rng.choice([1, 2, 5, 7, 8]))
            options_list  = [(correct_val, None)] + [(str(w), "wrong_count") for w in wrong_counts[:3]]

        elif mode == "name_from_sides" and info["sides"] > 0:
            # "Which shape has exactly 3 sides and 3 corners?"
            math_expr    = f"name_from_sides({info['sides']})"
            stem_template = (f"Which shape has exactly {info['sides']} side{'s' if info['sides'] != 1 else ''} "
                             f"and {info['corners']} corner{'s' if info['corners'] != 1 else ''}?")
            correct_val   = correct_shape
            wrong_shapes  = rng.sample([d for d in distractors
                                         if shape_data[d]["sides"] != info["sides"]], min(3, len(distractors)))
            while len(wrong_shapes) < 3:
                wrong_shapes.append(rng.choice(distractors))
            options_list  = [(correct_val, None)] + [(w, "wrong_shape") for w in wrong_shapes[:3]]

        elif mode == "corners":
            n = info["corners"]
            if n == 0:
                math_expr     = "corners(Circle)"
                stem_template  = "A circle has no corners. How many corners does a SQUARE have?"
                correct_val    = "4"
                options_list   = [("4", None), ("0", "circle_corners"), ("3", "triangle_corners"), ("6", "hexagon_corners")]
            else:
                math_expr     = f"corners({correct_shape})"
                stem_template  = f"How many corners (vertices) does a {correct_shape.upper()} have?"
                correct_val    = str(n)
                other_counts   = sorted({shape_data[d]["corners"] for d in distractors if shape_data[d]["corners"] != n})
                other_counts   = rng.sample(other_counts, min(3, len(other_counts)))
                while len(other_counts) < 3:
                    other_counts.append(rng.choice([1, 2, 5, 7]))
                options_list   = [(correct_val, None)] + [(str(w), "wrong_count") for w in other_counts[:3]]

        else:
            # flat_or_solid — or fallback for circle (0 sides)
            # "Which of these shapes is flat and has no straight sides?"
            math_expr     = f"flat_curved({correct_shape})"
            if info["sides"] == 0:
                stem_template  = "Which shape is perfectly round and has no straight sides or corners?"
                correct_val    = "Circle"
                options_list   = [("Circle", None), ("Square", "has_sides"),
                                   ("Triangle", "has_sides"), ("Rectangle", "has_sides")]
            else:
                stem_template  = (f"A {correct_shape.lower()} is a flat 2-D shape. "
                                   f"How many sides does it have?")
                correct_val    = str(info["sides"])
                others         = rng.sample([str(shape_data[d]["sides"]) for d in distractors
                                              if shape_data[d]["sides"] != info["sides"]], min(3, 4))
                while len(others) < 3:
                    others.append(str(rng.choice([1, 2, 5, 7])))
                options_list   = [(correct_val, None)] + [(w, "wrong_count") for w in others[:3]]

    # --- Grade K: Mathematical Practices (MP) ---
    elif _match_domain(skill_clean, ["K.MP"]):
        if "MP1" in skill_clean or "MP.1" in skill_clean:
            # MP1: Make Sense of Problems — text-only subtraction story (no picture reference)
            a = rng.randint(3, 8)
            b = rng.randint(1, a - 1)
            math_expr = f"{a} - {b}"
            stem_template = (f"There are {a} apples in a basket. "
                             f"Someone takes {b} apples away. "
                             f"How many apples are left in the basket?")
            correct_val = str(a - b)
            options_list = [
                (str(a - b), None),
                (str(a + b), "added_instead"),
                (str(b),     "selected_removed_count"),
                (str(a),     "selected_original_count"),
            ]
        elif "MP2" in skill_clean or "MP.2" in skill_clean:
            # MP2: Reason Abstractly (Abstract to Quantity)
            a = rng.randint(5, 12)
            math_expr = f"count({a})"
            stem_template = f"Which number tells how many items are in this group?"
            correct_val = str(a)
            options_list = [
                (correct_val, None),
                (str(a - 2), "too_low"),
                (str(a + 2), "too_high"),
                (str(a + 5), "random_guess")
            ]
        elif "MP3" in skill_clean or "MP.3" in skill_clean:
            # MP3: Critique Reasoning (Spot the Mistake)
            a = rng.randint(1, 4)
            b = rng.randint(1, 4)
            wrong_sum = a + b + 1
            math_expr = f"{a} + {b} = {wrong_sum}"
            stem_template = f"Sam says that {a} + {b} is {wrong_sum}. He shows his work with dots. Did Sam make a mistake?"
            correct_val = "Yes, Sam counted too many dots."
            options_list = [
                (correct_val, None),
                ("No, Sam is right.", "failed_to_spot_error"),
                ("Yes, Sam should have used colors.", "irrelevant_critique"),
                ("Yes, Sam's dots were too small.", "non_mathematical_critique")
            ]
        elif "MP4" in skill_clean or "MP.4" in skill_clean:
            # MP4: Model with Mathematics (Equation Matching)
            a = rng.randint(1, 5)
            b = rng.randint(1, 5)
            math_expr = f"{a} + {b}"
            stem_template = f"You have {a} items and you get {b} more. Which math sentence shows what happened?"
            correct_val = f"{a} + {b} = {a + b}"
            options_list = [
                (correct_val, None),
                (f"{a} - {b} = {abs(a - b)}", "wrong_operation"),
                (f"{a + b} - {a} = {b}", "inverse_operation"),
                (f"{a} + {b} = {a + b + 1}", "arithmetic_error")
            ]
        elif "MP5" in skill_clean or "MP.5" in skill_clean:
            # MP5: Use Tools (Tool Selection)
            math_expr = "tool_selection"
            stem_template = "You want to find out how long your desk is. Which tool should you use?"
            correct_val = "A ruler"
            options_list = [
                ("A ruler", None),
                ("A scale", "wrong_dimension_weight"),
                ("A clock", "wrong_dimension_time"),
                ("A thermometer", "wrong_dimension_temp")
            ]
        elif "MP6" in skill_clean or "MP.6" in skill_clean:
            # MP6: Attend to Precision (Vocabulary)
            math_expr = "precision_vocab"
            stem_template = "Look at this shape with 3 straight sides. What is the BEST name for it?"
            correct_val = "A triangle"
            options_list = [
                ("A triangle", None),
                ("A pointy shape", "imprecise_language"),
                ("A circle", "wrong_shape"),
                ("A box", "wrong_vocabulary")
            ]
        elif "MP7" in skill_clean or "MP.7" in skill_clean:
            # MP7: Look for Structure (Grouping)
            math_expr = "grouping_structure"
            stem_template = "If we put 10 red items and 10 blue items together, how many groups of 10 do we have?"
            correct_val = "2 groups"
            options_list = [
                ("2 groups", None),
                ("1 group", "failed_to_count_second_group"),
                ("20 groups", "confused_total_with_groups"),
                ("0 groups", "structure_blindness")
            ]
        elif "MP8" in skill_clean or "MP.8" in skill_clean:
            # MP8: Repeated Reasoning (Rules)
            a = rng.randint(2, 9)
            b = 1
            math_expr = f"{a} + 1"
            stem_template = f"When you add 1 to a number, you just say the next number. What is {a} + 1?"
            correct_val = str(a + 1)
            options_list = [
                (correct_val, None),
                (str(a - 1), "counted_backwards"),
                (str(a), "failed_to_apply_rule"),
                ("10", "distractor")
            ]

    # --- Grades 1-3: Geometry (G) ---
    elif _match_domain(skill_clean, ["1.G", "2.G", "3.G"]):
        if "1.G.1" in skill_clean:
            mode = rng.choice(["defining", "shape_by_attributes"])
            if mode == "defining":
                math_expr = "defining_attribute"
                stem_template = "Which of these is a DEFINING attribute of a triangle (something that makes it a triangle)?"
                correct_val = "It has 3 sides and is closed"
                options_list = [
                    (correct_val, None),
                    ("It is painted blue", "color_non_defining"),
                    ("It is very small", "size_non_defining"),
                    ("It is tilted to the right", "orientation_non_defining")
                ]
            else:
                math_expr = "shape_by_attributes"
                stem_template = "David drew a shape. The shape is closed and has exactly 3 straight sides. Which shape did David draw?"
                correct_val = "Triangle"
                options_list = [
                    (correct_val, None),
                    ("Square", "four_sides"),
                    ("Circle", "no_straight_sides"),
                    ("Rectangle", "wrong_shape")
                ]
        elif "2.G.1" in skill_clean:
            mode = rng.choice(["pentagon", "cube", "hexagon"])
            if mode == "pentagon":
                math_expr = "pentagon_attributes"
                stem_template = "Which shape has exactly 5 sides and 5 angles?"
                correct_val = "Pentagon"
                options_list = [
                    (correct_val, None),
                    ("Quadrilateral", "four_sides"),
                    ("Hexagon", "six_sides"),
                    ("Triangle", "three_sides")
                ]
            elif mode == "cube":
                math_expr = "cube_faces"
                stem_template = "How many equal square faces does a solid cube have?"
                correct_val = "6"
                options_list = [
                    (correct_val, None),
                    ("4", "forgot_top_bottom"),
                    ("8", "counted_corners"),
                    ("12", "counted_edges")
                ]
            else:
                math_expr = "hexagon_corners"
                stem_template = "A shape has exactly 6 corners (vertices). What is the name of this shape?"
                correct_val = "Hexagon"
                options_list = [
                    (correct_val, None),
                    ("Pentagon", "five_vertices"),
                    ("Triangle", "three_vertices"),
                    ("Quadrilateral", "four_vertices")
                ]
        elif "3.G.1" in skill_clean:
            mode = rng.choice(["shared_category", "attribute_comparison"])
            if mode == "shared_category":
                math_expr = "quadrilateral_category"
                stem_template = "Rhombuses, rectangles, and squares all belong to which larger category of shapes because they all have exactly 4 sides?"
                correct_val = "Quadrilaterals"
                options_list = [
                    (correct_val, None),
                    ("Triangles", "three_sides"),
                    ("Pentagons", "five_sides"),
                    ("Hexagons", "six_sides")
                ]
            else:
                math_expr = "square_rect_attributes"
                stem_template = "Which of the following is true about all squares and all rectangles?"
                correct_val = "They both have 4 right angles"
                options_list = [
                    (correct_val, None),
                    ("They both must have 4 equal sides", "square_only_attribute"),
                    ("They both have 3 sides", "triangle_attribute"),
                    ("They both have no parallel sides", "wrong_geometry")
                ]
        else:
            # Fallback for other Grades 1-3 geometry
            math_expr = "shape_identify"
            stem_template = "What is a shape with 4 sides called?"
            correct_val = "Quadrilateral"
            options_list = [
                ("Quadrilateral", None),
                ("Triangle", "three_sides"),
                ("Pentagon", "five_sides"),
                ("Hexagon", "six_sides")
            ]

    # --- Grades 1-3: Operations & Algebraic Thinking (OA) ---
    elif _match_domain(skill_clean, ["1.OA", "2.OA", "3.OA.A.1", "3.OA.A.2", "3.OA.A.3", "3.OA.A.4"]):
        # Multiplication/division as equal groups
        if "3.OA" in skill_clean:
            a = rng.randint(2, 9)  # number of groups
            b = rng.randint(2, 9)  # items per group
            product = a * b
            
            op_type = rng.choice(["mult", "div"])
            if op_type == "mult":
                math_expr = f"{a} × {b}"
                stem_template = f"Solve: {a} × {b} = ?"
                correct_val = str(product)
                options_list = [
                    (correct_val, None),
                    (str(a + b), "added_instead_of_multiplied"),
                    (str(product + a), "added_extra_group"),
                    (str(product - b), "subtracted_one_group")
                ]
            else:
                math_expr = f"{product} ÷ {a}"
                stem_template = f"Solve: {product} ÷ {a} = ?"
                correct_val = str(b)
                options_list = [
                    (correct_val, None),
                    (str(a), "confused_divisor_with_quotient"),
                    (str(product - a), "subtracted_instead_of_divided"),
                    (str(b + 1), "off_by_one")
                ]
        else:
            # Grades 1-2: Addition/subtraction
            a = rng.randint(1, 20) if "2.OA" in skill_clean else rng.randint(1, 10)
            b = rng.randint(1, 20) if "2.OA" in skill_clean else rng.randint(1, 10)
            if a < b:
                a, b = b, a  # ensure a >= b for subtraction
            
            op = rng.choice(["+", "-"])
            if op == "+":
                correct_val = str(a + b)
                math_expr = f"{a} + {b}"
                stem_template = f"Solve: {a} + {b} = ?"
                options_list = [
                    (correct_val, None),
                    (str(a - b), "subtracted_instead_of_added"),
                    (str(a + b + rng.choice([-1, 1])), "counting_off_by_one"),
                    (str(a * b) if a * b != a + b else str(a + b + 2), "multiplied_instead_of_added")
                ]
            else:
                correct_val = str(a - b)
                math_expr = f"{a} - {b}"
                stem_template = f"Solve: {a} - {b} = ?"
                options_list = [
                    (correct_val, None),
                    (str(a + b), "added_instead_of_subtracted"),
                    (str(a - b + rng.choice([-1, 1])), "counting_off_by_one"),
                    (str(b - a) if b != a else str(a - b + 2), "reversed_operands")
                ]

    # --- Grades 3-4: OA Unknown in Equations ---
    elif _match_domain(skill_clean, ["3.OA.D.8", "4.OA.A.3"]):
        # Two-step word problems
        a = rng.randint(3, 8)
        b = rng.randint(2, 6)
        c = rng.randint(1, 10)
        result = a * b + c
        
        math_expr = f"{a} × {b} + {c}"
        stem_template = f"A student buys {a} packs of {b} pencils each, then finds {c} more pencils. How many pencils in total?"
        correct_val = str(result)
        options_list = [
            (correct_val, None),
            (str(a * b), "forgot_second_step"),
            (str(a + b + c), "added_all_numbers"),
            (str(a * (b + c)), "wrong_order_of_operations")
        ]

    # --- Grade 4: Factors, Multiples & Patterns (OA.B.4, OA.C.5) ---
    elif _match_domain(skill_clean, ["4.OA.B.4", "4.OA.C.5"]):
        if "OA.B.4" in skill_clean:
            # Factors or Multiples
            mode = rng.choice(["factor", "multiple", "prime"])
            if mode == "factor":
                a = rng.choice([12, 16, 18, 20, 24, 30, 36])
                factors = [i for i in range(1, a + 1) if a % i == 0]
                correct_val = str(rng.choice(factors))
                stem_template = f"Which of the following is a factor of {a}?"
                options_list = [
                    (correct_val, None),
                    (str(a + 1), "neighbor_number"),
                    (str(a * 2), "multiple_instead_of_factor"),
                    (str(rng.randint(2, a-1)) if a > 3 else "5", "random_non_factor")
                ]
            elif mode == "multiple":
                a = rng.randint(3, 9)
                multiples = [a * i for i in range(2, 6)]
                correct_val = str(rng.choice(multiples))
                stem_template = f"Which of the following is a multiple of {a}?"
                options_list = [
                    (correct_val, None),
                    (str(a + 1), "neighbor_number"),
                    (str(rng.randint(2, a-1)), "factor_instead_of_multiple"),
                    (str(a * 10 + 1), "random_non_multiple")
                ]
            else:
                # Prime vs Composite
                primes = [2, 3, 5, 7, 11, 13, 17, 19, 23]
                composites = [4, 6, 8, 9, 10, 12, 14, 15, 16]
                is_prime_question = rng.choice([True, False])
                if is_prime_question:
                    correct_val = str(rng.choice(primes))
                    stem_template = "Which of the following numbers is prime?"
                    options_list = [(correct_val, None)] + [(str(c), "composite_number") for c in rng.sample(composites, 3)]
                else:
                    correct_val = str(rng.choice(composites))
                    stem_template = "Which of the following numbers is composite?"
                    options_list = [(correct_val, None)] + [(str(p), "prime_number") for p in rng.sample(primes, 3)]
        else:
            # Patterns (4.OA.C.5)
            start = rng.randint(1, 10)
            rule = rng.randint(2, 5)
            pattern = [start + rule * i for i in range(5)]
            correct_val = str(pattern[4])
            stem_template = f"Following the pattern {pattern[0]}, {pattern[1]}, {pattern[2]}, {pattern[3]}... what is the next number?"
            options_list = [
                (correct_val, None),
                (str(pattern[4] + rule), "extra_step"),
                (str(pattern[4] - 1), "counting_error"),
                (str(pattern[3] * 2), "multiplication_confusion")
            ]

    # --- Grades 2-5: Numbers & Operations in Base Ten (NBT) ---
    elif _match_domain(skill_clean, ["NBT"]):
        g = g_eff
        
        # Rounding (3.NBT.A.1, 4.NBT.A.3)
        if "NBT.A.1" in skill_clean or "NBT.A.3" in skill_clean or rng.random() < 0.2:
            if g <= 3:
                # Round to nearest 10 or 100
                a = rng.randint(11, 999)
                place = rng.choice([10, 100])
                if place == 100 and a < 100: a += 100
                
                correct_val = str(int(round(a / place) * place))
                math_expr = f"round({a}, {place})"
                stem_template = f"Round {a} to the nearest {place}."
                options_list = [
                    (correct_val, None),
                    (str(a), "did_not_round"),
                    (str(int(a // place * place)), "always_round_down"),
                    (str(int((a // place + 1) * place)), "always_round_up")
                ]
            else:
                # Round to nearest 1,000 or 10,000
                a = rng.randint(1001, 99999)
                place = rng.choice([1000, 10000])
                if place == 10000 and a < 10000: a += 10000
                
                correct_val = str(int(round(a / place) * place))
                math_expr = f"round({a}, {place})"
                stem_template = f"Round {a} to the nearest {place}."
                options_list = [
                    (correct_val, None),
                    (str(int(round(a / (place/10)) * (place/10))), "rounded_to_wrong_place"),
                    (str(int(a // place * place)), "always_round_down"),
                    (str(int((a // place + 1) * place)), "always_round_up")
                ]
        
        # Comparison (4.NBT.A.2)
        elif "NBT.A.2" in skill_clean:
            a = rng.randint(10000, 999999)
            # Create b that is similar to a but different in one place
            a_str = str(a)
            idx = rng.randint(0, len(a_str) - 1)
            b_list = list(a_str)
            b_list[idx] = str((int(b_list[idx]) + rng.choice([-1, 1])) % 10)
            b = int("".join(b_list))
            
            math_expr = f"{a} ? {b}"
            correct_val = ">" if a > b else "<"
            stem_template = f"Which symbol makes the statement true? {a} [?] {b}"
            options_list = [
                (">", None if a > b else "incorrect_comparison"),
                ("<", None if a < b else "incorrect_comparison"),
                ("=", "not_equal"),
                ("≥", "unnecessary_complexity")
            ]

        elif g <= 2:
            # 2-digit addition with regrouping
            a = rng.randint(15, 89)
            b = rng.randint(15, 89)
            correct_val = str(a + b)
            math_expr = f"{a} + {b}"
            stem_template = f"Add: {a} + {b} = ?"
            # Trap: forgot to carry the ten
            ones_sum = (a % 10) + (b % 10)
            no_carry = (a // 10 + b // 10) * 10 + (ones_sum % 10)
            options_list = [
                (correct_val, None),
                (str(no_carry), "forgot_to_carry"),
                (str(a + b + 10), "extra_carry"),
                (str(a + b - 10) if a + b > 10 else str(a + b + 1), "place_value_error")
            ]
        elif g <= 3:
            # 3-digit addition/subtraction
            a = rng.randint(100, 999)
            b = rng.randint(100, 999)
            if a < b:
                a, b = b, a
            op = rng.choice(["+", "-"])
            if op == "+":
                correct_val = str(a + b)
                math_expr = f"{a} + {b}"
                stem_template = f"Add: {a} + {b} = ?"
            else:
                correct_val = str(a - b)
                math_expr = f"{a} - {b}"
                stem_template = f"Subtract: {a} - {b} = ?"
            diff = rng.choice([-10, 10, -1, 1])
            options_list = [
                (correct_val, None),
                (str(int(correct_val) + 10), "place_value_tens_error"),
                (str(int(correct_val) + diff), "regrouping_error"),
                (str(int(correct_val) + 100), "place_value_hundreds_error")
            ]
        else:
            # Grades 4-5: Multi-digit multiplication
            a = rng.randint(12, 99)
            b = rng.randint(12, 99) if g >= 5 else rng.randint(2, 9)
            correct_val = str(a * b)
            math_expr = f"{a} × {b}"
            stem_template = f"Multiply: {a} × {b} = ?"
            # Trap: forgot to carry in multiplication
            partial = (a % 10) * b
            partial_tens = (a // 10) * b * 10
            no_carry_trap = str(partial + partial_tens) if partial + partial_tens != a * b else str(a * b + b)
            options_list = [
                (correct_val, None),
                (str(a + b), "added_instead_of_multiplied"),
                (no_carry_trap, "multiplication_carry_error"),
                (str(a * b + rng.choice([-a, a, -b, b])), "partial_product_error")
            ]

    # --- Grades 3-5: Fractions (NF) ---
    elif _match_domain(skill_clean, ["3.NF", "4.NF.A"]):
        # Fraction equivalence: a/b = ?/c
        b = rng.choice([2, 3, 4, 5, 6])
        a = rng.randint(1, b - 1)
        multiplier = rng.randint(2, 4)
        c = b * multiplier  # target denominator
        correct_num = a * multiplier
        
        math_expr = f"{a}/{b} = ?/{c}"
        stem_template = f"Find the equivalent fraction: {a}/{b} = ?/{c}. What number replaces the question mark?"
        correct_val = str(correct_num)
        options_list = [
            (correct_val, None),
            (str(a), "didnt_multiply_numerator"),
            (str(a + multiplier), "added_multiplier_instead"),
            (str(correct_num + 1), "off_by_one")
        ]

    elif "4.NF.B.3" in skill_clean or "4.NF.B.4" in skill_clean:
        # Grade 4: Add/subtract fractions with LIKE denominators
        d = rng.choice([3, 4, 5, 6, 8, 10])
        a = rng.randint(1, d - 1)
        c = rng.randint(1, d - 1)
        while a + c >= d * 2:  # keep result reasonable
            c = rng.randint(1, d - 1)
        
        f1 = sp.Rational(a, d)
        f2 = sp.Rational(c, d)
        
        if "B.3" in skill_clean:
            expr = f1 + f2
            correct_val = str(expr)
            math_expr = f"{a}/{d} + {c}/{d}"
            stem_template = f"Add: {a}/{d} + {c}/{d} = ?"
            options_list = [
                (correct_val, None),
                (f"{a + c}/{d + d}", "added_denominators_too"),
                (str(f1 - f2) if a > c else f"{c - a}/{d}", "subtracted_instead"),
                (f"{a * c}/{d}", "multiplied_numerators")
            ]
        else:
            expr = f1 * f2
            correct_val = str(expr)
            math_expr = f"{a}/{d} × {c}/{d}"
            stem_template = f"Multiply: {a}/{d} × {c}/{d} = ?"
            options_list = [
                (correct_val, None),
                (str(f1 + f2), "added_instead_of_multiplied"),
                (f"{a * c}/{d}", "forgot_to_multiply_denominator"),
                (f"{a + c}/{d * d}", "added_numerators_multiplied_denominators")
            ]

    elif "5.NF.A.1" in skill_clean:
        # Grade 5: Addition/Subtraction of fractions with UNLIKE denominators
        b = rng.randint(3, 12)  # Denominator 1
        a = rng.randint(1, b - 1)  # Ensure proper fraction
        d = rng.randint(3, 12)  # Denominator 2
        while b == d:
            d = rng.randint(3, 12)
        c = rng.randint(1, d - 1)  # Ensure proper fraction

        f1 = sp.Rational(a, b)
        f2 = sp.Rational(c, d)
        expr = f1 + f2
        correct_val = str(expr)
        
        # Trap 1: Add numerators and denominators (Very common student error!)
        trap_add_num_den = f"{a + c}/{b + d}"
        # Trap 2: Subtraction instead of addition
        trap_sub = str(f1 - f2)
        # Trap 3: Cross multiply error
        trap_mult_num_add_den = f"{a * c}/{b + d}"
        
        math_expr = f"{a}/{b} + {c}/{d}"
        stem_template = f"Solve: {a}/{b} + {c}/{d} = ?"
        options_list = [
            (correct_val, None),
            (trap_add_num_den, "add_numerators_and_denominators"),
            (trap_sub, "operation_sign_confusion"),
            (trap_mult_num_add_den, "multiplied_numerators_added_denominators")
        ]
        
    elif "5.NF.B.4" in skill_clean or "5.NF.B.5" in skill_clean:
        # Grade 5: Multiplication of fractions
        b = rng.randint(3, 12)
        a = rng.randint(1, b - 1)
        d = rng.randint(3, 12)
        c = rng.randint(1, d - 1)
        
        f1 = sp.Rational(a, b)
        f2 = sp.Rational(c, d)
        expr = f1 * f2
        correct_val = str(expr)
        
        trap_add = str(f1 + f2)
        trap_keep_den = f"{a * c}/{b}"
        trap_add_num_mult_den = f"{a + c}/{b * d}"
        
        math_expr = f"{a}/{b} × {c}/{d}"
        stem_template = f"Multiply: {a}/{b} × {c}/{d} = ?"
        options_list = [
            (correct_val, None),
            (trap_add, "added_instead_of_multiplied"),
            (trap_keep_den, "ignored_denominator_multiplication"),
            (trap_add_num_mult_den, "added_numerators_multiplied_denominators")
        ]

    elif _match_domain(skill_clean, ["5.NF.B.6", "5.NF.B.7", "6.NS.A.1"]):
        # Division of fractions (multiply by reciprocal)
        b = rng.choice([2, 3, 4, 5, 6])
        a = rng.randint(1, b - 1)
        d = rng.choice([2, 3, 4, 5, 6])
        c = rng.randint(1, d - 1)
        
        f1 = sp.Rational(a, b)
        f2 = sp.Rational(c, d)
        expr = f1 / f2  # a/b ÷ c/d = a/b × d/c
        correct_val = str(expr)
        
        math_expr = f"{a}/{b} ÷ {c}/{d}"
        stem_template = f"Divide: {a}/{b} ÷ {c}/{d} = ?"
        options_list = [
            (correct_val, None),
            (str(f1 * f2), "multiplied_instead_of_divided"),
            (f"{a * c}/{b * d}", "forgot_to_flip_reciprocal"),
            (str(f2 / f1), "flipped_wrong_fraction")
        ]

    # --- Grade 5: Order of Operations (OA) ---
    elif "5.OA.A.1" in skill_clean or "5.OA.1" in skill_clean:
        a = rng.randint(2, 12)
        b = rng.randint(2, 15)
        c = rng.randint(2, 15)
        
        # Expression: a * (b + c)
        result = a * (b + c)
        correct_val = str(result)
        math_expr = f"{a} × ({b} + {c})"
        stem_template = f"Evaluate the expression: {a} × ({b} + {c}) = ?"

        trap_no_paren = str(a * b + c)
        trap_all_mult = str(a * b * c)
        trap_all_add = str(a + b + c)
        
        options_list = [
            (correct_val, None),
            (trap_no_paren, "ignored_parentheses_precedence"),
            (trap_all_mult, "multiplied_all_terms"),
            (trap_all_add, "added_all_terms")
        ]

    # --- Grades 3-5: Measurement & Data (MD) ---
    elif _match_domain(skill_clean, ["3.MD", "4.MD", "5.MD"]):
        md_type = rng.choice(["area", "perimeter", "volume"])
        if md_type == "area" or "4.MD" in skill_clean:
            # Area of rectangle
            a = rng.randint(3, 15)  # length
            b = rng.randint(3, 15)  # width
            area = a * b
            perimeter = 2 * (a + b)
            
            math_expr = f"{a} × {b}"
            stem_template = f"Solve: Find the area of a rectangle with length {a} and width {b}."
            correct_val = str(area)
            options_list = [
                (correct_val, None),
                (str(perimeter), "calculated_perimeter_instead"),
                (str(a + b), "added_sides_only"),
                (str(area + a), "included_extra_side")
            ]
        elif md_type == "perimeter":
            a = rng.randint(3, 12)
            b = rng.randint(3, 12)
            perimeter = 2 * (a + b)
            area = a * b
            
            math_expr = f"2 × ({a} + {b})"
            stem_template = f"Solve: Find the perimeter of a rectangle with length {a} and width {b}."
            correct_val = str(perimeter)
            options_list = [
                (correct_val, None),
                (str(area), "calculated_area_instead"),
                (str(a + b), "forgot_to_double"),
                (str(2 * a + b), "only_doubled_one_side")
            ]
        else:
            # Volume of rectangular prism (Grade 5)
            a = rng.randint(2, 8)
            b = rng.randint(2, 8)
            c = rng.randint(2, 8)
            volume = a * b * c
            surface_area = 2 * (a*b + b*c + a*c)
            
            math_expr = f"{a} × {b} × {c}"
            stem_template = f"Solve: Find the volume of a box with length {a}, width {b}, and height {c}."
            correct_val = str(volume)
            options_list = [
                (correct_val, None),
                (str(a * b + c), "added_height_instead"),
                (str(a + b + c), "added_all_dimensions"),
                (str(a * b * 2 + c), "partial_calculation_error")
            ]

    # --- Grades 4-8: Geometry (G) ---
    elif _match_domain(skill_clean, ["4.G", "5.G", "6.G", "7.G", "8.G"]):
        g = g_eff
        if g <= 5:
            if "4.G.1" in skill_clean:
                mode = rng.choice(["ray", "perpendicular", "acute"])
                if mode == "ray":
                    math_expr = "ray_definition"
                    stem_template = "What is a geometric figure that has one starting endpoint and goes on forever in only one direction?"
                    correct_val = "Ray"
                    options_list = [
                        (correct_val, None),
                        ("Line segment", "two_endpoints"),
                        ("Line", "no_endpoints"),
                        ("Angle", "two_rays_meeting")
                    ]
                elif mode == "perpendicular":
                    math_expr = "perpendicular_lines"
                    stem_template = "What do we call two lines that cross each other at a perfect 90-degree right angle?"
                    correct_val = "Perpendicular lines"
                    options_list = [
                        (correct_val, None),
                        ("Parallel lines", "never_cross"),
                        ("Acute lines", "wrong_terminology"),
                        ("Obtuse lines", "wrong_terminology")
                    ]
                else:
                    math_expr = "acute_angle"
                    stem_template = "An angle measures less than 90 degrees (smaller than a square corner). What type of angle is it?"
                    correct_val = "Acute angle"
                    options_list = [
                        (correct_val, None),
                        ("Obtuse angle", "greater_than_90"),
                        ("Right angle", "exactly_90"),
                        ("Straight angle", "exactly_180")
                    ]
            elif "5.G.1" in skill_clean:
                mode = rng.choice(["read_coord", "coord_definition"])
                if mode == "read_coord":
                    x_val = rng.randint(2, 8)
                    y_val = rng.randint(2, 8)
                    while x_val == y_val:
                        y_val = rng.randint(2, 8)
                    a, b = x_val, y_val
                    math_expr = f"coordinate({x_val}, {y_val})"
                    stem_template = f"Starting at the origin (0, 0), you move {x_val} units right along the x-axis, and then {y_val} units up along the y-axis. What ordered pair represents this point?"
                    correct_val = f"({x_val}, {y_val})"
                    options_list = [
                        (correct_val, None),
                        (f"({y_val}, {x_val})", "swapped_x_y"),
                        (f"({x_val}, 0)", "forgot_y"),
                        (f"(0, {y_val})", "forgot_x")
                    ]
                else:
                    x_val = rng.randint(2, 9)
                    y_val = rng.randint(2, 9)
                    while x_val == y_val:
                        y_val = rng.randint(2, 9)
                    a, b = x_val, y_val
                    math_expr = f"definition({x_val}, {y_val})"
                    stem_template = f"In the ordered pair ({x_val}, {y_val}), what does the first number {x_val} represent?"
                    correct_val = "How far to move right along the x-axis"
                    options_list = [
                        (correct_val, None),
                        ("How far to move up along the y-axis", "swapped_coordinates"),
                        ("The distance from the top corner", "random_distractor"),
                        ("The coordinate of the origin", "origin_misconception")
                    ]
            else:
                # Area of triangle
                base = rng.randint(4, 16)
                height = rng.randint(3, 12)
                area = sp.Rational(base * height, 2)
                
                math_expr = f"(1/2) × {base} × {height}"
                stem_template = f"Solve: Find the area of a triangle with base {base} and height {height}."
                correct_val = str(area)
                options_list = [
                    (correct_val, None),
                    (str(base * height), "forgot_to_halve"),
                    (str(base + height), "added_instead"),
                    (str(sp.Rational(base * height, 2) + base), "added_base_to_area")
                ]
        elif g <= 7:
            # Area of circle (pi * r^2)
            r = rng.randint(2, 10)
            area = round(3.14159 * r * r, 2)
            circumference = round(2 * 3.14159 * r, 2)
            
            math_expr = f"π × {r}²"
            stem_template = f"Solve: Find the area of a circle with radius {r}. (Use π ≈ 3.14)"
            correct_val = str(round(3.14 * r * r, 2))
            options_list = [
                (correct_val, None),
                (str(round(2 * 3.14 * r, 2)), "calculated_circumference_instead"),
                (str(round(3.14 * r, 2)), "forgot_to_square_radius"),
                (str(round(3.14 * r * r * r, 2)), "cubed_radius_instead")
            ]
        else:
            # Pythagorean theorem
            triples = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17), (7, 24, 25)]
            triple = rng.choice(triples)
            a, b, c = triple
            
            math_expr = f"√({a}² + {b}²)"
            stem_template = f"Solve: Find the hypotenuse of a right triangle with legs of length {a} and {b}."
            correct_val = str(c)
            options_list = [
                (correct_val, None),
                (str(a + b), "added_legs_instead"),
                (str(a * b), "multiplied_legs_instead"),
                (str(c + 1), "calculation_off_by_one")
            ]

    # --- Grades 6-7: Ratios & Proportional Relationships (RP) ---
    elif _match_domain(skill_clean, ["6.RP", "7.RP"]):
        a = rng.randint(2, 6)  # first ratio term
        b = rng.randint(2, 8)  # second ratio term
        multiplier = rng.randint(2, 5)
        
        scaled_a = a * multiplier
        scaled_b = b * multiplier
        
        # Ask to find scaled_b given the ratio and scaled_a
        math_expr = f"{a}:{b} = {scaled_a}:?"
        stem_template = f"Solve: If the ratio is {a}:{b}, and the first value is {scaled_a}, what is the second value?"
        correct_val = str(scaled_b)
        options_list = [
            (correct_val, None),
            (str(scaled_a + b - a), "used_additive_reasoning"),  # Common proportional reasoning error
            (str(scaled_a * b), "multiplied_instead"),
            (str(b), "used_original_ratio_value")
        ]

    # --- Grades 6-8: Expressions & Equations (EE) ---
    elif _match_domain(skill_clean, ["6.EE", "7.EE", "8.EE"]):
        g = g_eff
        
        if "6.EE.1" in skill_clean:
            # Exponents for Grade 6
            mode = rng.choice(["evaluate", "write"])
            if mode == "evaluate":
                base = rng.choice([2, 3, 5])
                if base == 2:
                    exp = rng.choice([3, 4, 5])
                elif base == 3:
                    exp = rng.choice([3, 4])
                else:
                    exp = 3
                
                correct_val = str(base ** exp)
                math_expr = f"{base}^{exp}"
                stem_template = f"Evaluate the numerical expression: {base} to the power of {exp} (written as {base}^{exp})."
                options_list = [
                    (correct_val, None),
                    (str(base * exp), "multiplied_base_and_exponent"),
                    (str(exp ** base), "swapped_base_and_exponent"),
                    (str(base ** exp + rng.choice([-2, -1, 1, 2])), "calculation_slip")
                ]
                a, b = base, exp
            else:
                base = rng.randint(3, 8)
                exp = rng.randint(3, 5)
                math_expr = f"write({base}^{exp})"
                stem_template = f"Which numerical expression represents the product of {base} multiplied by itself {exp} times?"
                correct_val = f"{base}^{exp}"
                options_list = [
                    (correct_val, None),
                    (f"{base} × {exp}", "base_times_exponent"),
                    (f"{exp}^{base}", "swapped_base_and_exponent"),
                    (f"{base} + {base} + {base}", "repeated_addition")
                ]
                a, b = base, exp
        elif "7.EE.1" in skill_clean:
            # Linear expression expansion / simplification
            mode = rng.choice(["expand", "simplify"])
            if mode == "expand":
                # a(bx + c)
                a_coef = rng.randint(2, 6)
                b_coef = rng.choice([-3, -2, 2, 3, 4])
                c_const = rng.choice([-6, -5, 5, 6])
                
                # Math expression: a*(b*x + c)
                math_expr = f"{a_coef} * ({b_coef}*x + {c_const})"
                
                # Correct expansion
                correct_x = a_coef * b_coef
                correct_const = a_coef * c_const
                
                sign_str = "+" if correct_const > 0 else "-"
                opp_sign_str = "-" if correct_const > 0 else "+"
                correct_val = f"{correct_x}*x {sign_str} {abs(correct_const)}"
                stem_template = f"Expand the linear expression: {a_coef}({b_coef}x {sign_str} {abs(c_const)})."
                
                # Options list
                options_list = [
                    (correct_val, None),
                    (f"{correct_x}*x + {c_const}", "forgot_to_distribute_to_constant"),
                    (f"{a_coef + b_coef}*x {sign_str} {abs(correct_const)}", "added_coefficient"),
                    (f"{correct_x}*x {opp_sign_str} {abs(correct_const)}", "sign_error")
                ]
                a, b, c = a_coef, b_coef, c_const
            else:
                # (ax + b) - (cx - d) -> (a-c)x + (b+d)
                a_coef = rng.randint(5, 9)
                c_coef = rng.randint(2, 4)
                b_const = rng.randint(2, 8)
                d_const = rng.randint(2, 8)
                
                math_expr = f"({a_coef}*x + {b_const}) - ({c_coef}*x - {d_const})"
                
                correct_x = a_coef - c_coef
                correct_const = b_const + d_const  # b - (-d) = b + d
                correct_val = f"{correct_x}*x + {correct_const}"
                stem_template = f"Simplify the expression by combining like terms: ({a_coef}x + {b_const}) - ({c_coef}x - {d_const})."
                
                options_list = [
                    (correct_val, None),
                    (f"{correct_x}*x + {b_const - d_const}", "sign_error_on_constant"),
                    (f"{a_coef + c_coef}*x + {correct_const}", "added_x_coefficients_instead_of_subtracted"),
                    (f"{correct_x}*x + {b_const}", "forgot_second_constant")
                ]
                a, b, c, d = a_coef, b_const, c_coef, d_const
        elif "8.EE.1" in skill_clean:
            # Exponent properties (Grade 8)
            mode = rng.choice(["product", "quotient", "negative"])
            if mode == "product":
                base = rng.choice([2, 3, 4, 5])
                m = rng.randint(2, 5)
                n = rng.randint(2, 5)
                math_expr = f"{base}^{m} * {base}^{n}"
                stem_template = f"Simplify the expression using the properties of exponents: {base}^{m} × {base}^{n}."
                correct_val = f"{base}^{m + n}"
                options_list = [
                    (correct_val, None),
                    (f"{base}^{m * n}", "multiplied_exponents"),
                    (f"{base * 2}^{m + n}", "multiplied_bases"),
                    (f"{base}^{abs(m - n)}", "subtracted_exponents")
                ]
                a, b, c = base, m, n
            elif mode == "quotient":
                base = rng.choice([2, 3, 5, 6])
                m = rng.randint(6, 9)
                n = rng.randint(2, 5)
                math_expr = f"{base}^{m} / {base}^{n}"
                stem_template = f"Simplify the expression using the properties of exponents: {base}^{m} ÷ {base}^{n}."
                correct_val = f"{base}^{m - n}"
                options_list = [
                    (correct_val, None),
                    (f"{base}^{round(m / n, 1)}", "divided_exponents"),
                    (f"{base}^{m + n}", "added_exponents"),
                    (f"1^{m - n}", "divided_bases")
                ]
                a, b, c = base, m, n
            else:
                base = rng.choice([2, 3, 5, 7])
                n = rng.randint(2, 4)
                math_expr = f"{base}^(-{n})"
                stem_template = f"Which of the following is equivalent to the expression: {base}^(-{n})?"
                correct_val = f"1 / {base}^{n}"
                options_list = [
                    (correct_val, None),
                    (f"-{base}^{n}", "negative_base_instead"),
                    (f"-{n}^{base}", "swapped_base_and_exponent"),
                    (f"{base}^{n}", "ignored_negative_sign")
                ]
                a, b = base, n
        elif "8.EE.C.7" in skill_clean or "8.EE.C.8" in skill_clean or g >= 8:
            # Linear equations with variables on both sides: ax + b = cx + d
            x_val = rng.randint(1, 8)
            a = rng.randint(2, 7)
            c = rng.randint(1, a - 1)  # ensure a > c so coefficient is positive
            b = rng.randint(1, 10)
            d_val = (a - c) * x_val + b  # solve for d: ax + b = cx + d → d = (a-c)x + b
            
            math_expr = f"{a}x + {b} = {c}x + {d_val}"
            stem_template = f"Solve: {a}x + {b} = {c}x + {d_val}. What is x?"
            correct_val = str(x_val)
            options_list = [
                (correct_val, None),
                (str(-x_val), "sign_error"),
                (str(x_val + 1), "arithmetic_slip"),
                (str(d_val - b), "forgot_to_divide")
            ]
        elif g >= 7:
            # Two-step equations: ax + b = c
            a_val = rng.randint(2, 8)
            x_val = rng.randint(1, 10)
            b_val = rng.randint(1, 15)
            c_val = a_val * x_val + b_val
            
            math_expr = f"{a_val}x + {b_val} = {c_val}"
            stem_template = f"Solve: {a_val}x + {b_val} = {c_val}. What is x?"
            correct_val = str(x_val)
            options_list = [
                (correct_val, None),
                (str(round((c_val + b_val) / a_val, 1)), "added_b_instead_of_subtracting"),
                (str(round(c_val / a_val, 1)), "forgot_to_subtract_b"),
                (str(c_val - b_val), "forgot_to_divide_by_a")
            ]
            a, b, c = a_val, b_val, c_val
        else:
            # One-step equations: x + b = c or ax = c
            eq_type = rng.choice(["add", "mult"])
            if eq_type == "add":
                x_val = rng.randint(2, 15)
                b = rng.randint(2, 15)
                c = x_val + b
                math_expr = f"x + {b} = {c}"
                stem_template = f"Solve: x + {b} = {c}. What is x?"
                correct_val = str(x_val)
                options_list = [
                    (correct_val, None),
                    (str(c + b), "added_instead_of_subtracted"),
                    (str(c * b), "multiplied_instead"),
                    (str(x_val + 1), "off_by_one")
                ]
                a = x_val
            else:
                a = rng.randint(2, 9)
                x_val = rng.randint(2, 9)
                c = a * x_val
                math_expr = f"{a}x = {c}"
                stem_template = f"Solve: {a}x = {c}. What is x?"
                correct_val = str(x_val)
                options_list = [
                    (correct_val, None),
                    (str(c - a), "subtracted_instead_of_divided"),
                    (str(c + a), "added_instead_of_divided"),
                    (str(a), "confused_coefficient_with_solution")
                ]
                b = x_val

    # --- Grade 6-7: The Number System (NS) ---
    elif _match_domain(skill_clean, ["6.NS", "7.NS"]):
        if "7.NS" in skill_clean:
            # Integer arithmetic (negative numbers)
            a = rng.randint(-15, 15)
            b = rng.randint(-15, 15)
            while a == 0 or b == 0:
                a = rng.randint(-15, 15)
                b = rng.randint(-15, 15)
            
            op = rng.choice(["+", "-", "×"])
            if op == "+":
                correct = a + b
                math_expr = f"({a}) + ({b})"
                stem_template = f"Calculate: ({a}) + ({b}) = ?"
                options_list = [
                    (str(correct), None),
                    (str(a - b), "subtracted_instead_of_added"),
                    (str(abs(a) + abs(b)), "ignored_signs"),
                    (str(-correct), "flipped_sign")
                ]
            elif op == "-":
                correct = a - b
                math_expr = f"({a}) - ({b})"
                stem_template = f"Calculate: ({a}) - ({b}) = ?"
                options_list = [
                    (str(correct), None),
                    (str(a + b), "added_instead_of_subtracted"),
                    (str(b - a), "reversed_operands"),
                    (str(-correct), "flipped_sign")
                ]
            else:
                correct = a * b
                math_expr = f"({a}) × ({b})"
                stem_template = f"Calculate: ({a}) × ({b}) = ?"
                options_list = [
                    (str(correct), None),
                    (str(-correct), "wrong_sign_rule"),
                    (str(a + b), "added_instead_of_multiplied"),
                    (str(abs(a) * abs(b) if correct < 0 else -(abs(a) * abs(b))), "sign_rule_error")
                ]
            correct_val = str(correct)
        else:
            # 6.NS: Long division, GCF, LCM
            a = rng.randint(12, 99)
            b = rng.randint(2, 9)
            product = a * b  # ensure clean division
            
            math_expr = f"{product} ÷ {a}"
            stem_template = f"Divide: {product} ÷ {a} = ?"
            correct_val = str(b)
            options_list = [
                (correct_val, None),
                (str(a), "confused_dividend_with_quotient"),
                (str(b + 1), "off_by_one"),
                (str(product - a), "subtracted_instead")
            ]

    # --- Grades 6-7: Statistics & Probability (SP) ---
    elif _match_domain(skill_clean, ["6.SP", "7.SP"]):
        mode = rng.choice(["mean", "median", "probability"])
        if mode == "mean":
            count = rng.randint(4, 6)
            data = [rng.randint(1, 20) for _ in range(count)]
            total = sum(data)
            mean = round(total / count, 1)
            
            math_expr = f"mean({data})"
            stem_template = f"Find the mean (average) of the data set: {', '.join(map(str, data))}."
            correct_val = str(mean)
            options_list = [
                (correct_val, None),
                (str(total), "sum_instead_of_mean"),
                (str(round(total / (count - 1), 1)), "divided_by_wrong_count"),
                (str(max(data)), "selected_max_instead")
            ]
        elif mode == "median":
            count = 5 # odd count for simplicity
            data = sorted([rng.randint(1, 30) for _ in range(count)])
            median = data[2]
            
            math_expr = f"median({data})"
            stem_template = f"Find the median of the data set: {', '.join(map(str, data))}."
            correct_val = str(median)
            options_list = [
                (correct_val, None),
                (str(round(sum(data)/count, 1)), "calculated_mean_instead"),
                (str(data[0]), "selected_min"),
                (str(data[-1]), "selected_max")
            ]
        else:
            # Basic probability
            total_marbles = rng.randint(10, 25)
            red_marbles = rng.randint(2, total_marbles - 5)
            
            math_expr = f"{red_marbles}/{total_marbles}"
            stem_template = f"A bag has {total_marbles} marbles. {red_marbles} are red. What is the probability of picking a red marble?"
            correct_val = str(sp.Rational(red_marbles, total_marbles))
            options_list = [
                (correct_val, None),
                (f"{red_marbles}/{total_marbles - red_marbles}", "odds_instead_of_probability"),
                (f"1/{total_marbles}", "unit_fraction_error"),
                (f"{total_marbles - red_marbles}/{total_marbles}", "complement_probability")
            ]

    # --- Grade 8: Functions (F) ---
    elif _match_domain(skill_clean, ["8.F"]):
        # Linear function evaluation: f(x) = mx + b
        m = rng.randint(2, 6)
        b = rng.randint(-5, 10)
        x_val = rng.randint(1, 8)
        result = m * x_val + b
        
        b_str = f"+ {b}" if b >= 0 else f"- {abs(b)}"
        math_expr = f"f(x) = {m}x {b_str}, x = {x_val}"
        stem_template = f"If f(x) = {m}x {b_str}, what is f({x_val})?"
        correct_val = str(result)
        a, c = m, x_val
        options_list = [
            (correct_val, None),
            (str(m + x_val + b), "added_m_instead_of_multiplied"),
            (str(m * x_val), "forgot_constant_b"),
            (str(m * (x_val + b)), "wrong_order_of_operations")
        ]

    # --- High School: Seeing Structure in Expressions (SSE) ---
    elif _match_domain(skill_clean, ["SSE", "A-SSE"]):
        # Factoring quadratics: x² + bx + c = (x + r1)(x + r2)
        r1 = rng.randint(1, 8)
        r2 = rng.randint(-8, -1)
        while r1 + r2 == 0:
            r2 = rng.randint(-8, -1)
        
        b_coeff = r1 + r2
        c_coeff = r1 * r2
        
        b_sign = "+" if b_coeff >= 0 else ""
        c_sign = "+" if c_coeff >= 0 else ""
        
        math_expr = f"x² {b_sign}{b_coeff}x {c_sign}{c_coeff}"
        stem_template = f"Factor: x² {b_sign}{b_coeff}x {c_sign}{c_coeff}"
        
        # Format correct answer
        def _format_factor(root):
            if root > 0:
                return f"(x - {root})"
            else:
                return f"(x + {abs(root)})"
        
        correct_val = f"{_format_factor(r1)}{_format_factor(r2)}"
        a, b = r1, r2
        
        options_list = [
            (correct_val, None),
            (f"(x + {r1})(x + {r2})", "sign_error_all_additive"),
            (f"(x - {r1})(x + {r2})" if r2 < 0 else f"(x + {r1})(x - {r2})", "swapped_one_sign"),
            (f"(x + {abs(r2)})(x - {abs(r1)})", "swapped_roots")
        ]

    # --- High School: Reasoning with Equations (REI) ---
    elif _match_domain(skill_clean, ["REI", "A-REI"]):
        # Systems of linear equations
        x_val = rng.randint(1, 9)
        y_val = rng.randint(1, 9)
        while x_val == y_val:
            y_val = rng.randint(1, 9)
        
        s = x_val + y_val
        d = x_val - y_val
        
        math_expr = f"x + y = {s}, x - y = {d}"
        stem_template = f"Solve the system: x + y = {s} and x - y = {d}. What is (x, y)?"
        correct_val = f"({x_val}, {y_val})"
        a, b, c = x_val, y_val, s
        
        options_list = [
            (correct_val, None),
            (f"({y_val}, {x_val})", "swapped_x_and_y"),
            (f"({x_val}, {-y_val})", "y_sign_error"),
            (f"({s}, {d})", "used_constants_as_solution")
        ]

    # --- High School: Polynomials (APR) ---
    elif _match_domain(skill_clean, ["APR", "A-APR"]):
        # Polynomial multiplication: (x + a)(x + b) = x² + (a+b)x + ab
        a = rng.randint(1, 6)
        b = rng.randint(-6, 6)
        while b == 0:
            b = rng.randint(-6, 6)
        
        middle = a + b
        constant = a * b
        
        m_sign = "+" if middle >= 0 else ""
        c_sign = "+" if constant >= 0 else ""
        
        b_factor = f"+ {b}" if b > 0 else f"- {abs(b)}"
        
        math_expr = f"(x + {a})(x {b_factor})"
        stem_template = f"Expand: (x + {a})(x {b_factor})"
        correct_val = f"x² {m_sign}{middle}x {c_sign}{constant}"
        
        options_list = [
            (correct_val, None),
            (f"x² {m_sign}{middle}x", "forgot_constant_term"),
            (f"x² {c_sign}{constant}", "forgot_middle_term"),
            (f"x² {m_sign}{a*b}x {c_sign}{a+b}", "swapped_coefficients")
        ]

    # =========================================================================
    # GRADE-TIERED FALLBACK (for any standard without a specific generator)
    # =========================================================================
    else:
        g_level = g_eff
        
        if g_level >= 9:
            # High School fallback: Quadratic or Systems
            hs_choice = rng.choice(["quadratic", "system"])
            if hs_choice == "quadratic":
                r1 = rng.randint(1, 6)
                r2 = rng.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6])
                while r1 == r2 or r1 == -r2:
                    r2 = rng.randint(-6, 6)
                    if r2 == 0: r2 = 1
                
                b_coeff = -(r1 + r2)
                c_coeff = r1 * r2
                b_sign = "+" if b_coeff >= 0 else ""
                c_sign = "+" if c_coeff >= 0 else ""
                
                math_expr = f"x² {b_sign}{b_coeff}x {c_sign}{c_coeff}"
                stem_template = f"Factor the quadratic expression: x² {b_sign}{b_coeff}x {c_sign}{c_coeff}"
                correct_val = f"(x - {r1})(x - {r2})".replace("- -", "+ ")
                
                t1 = f"(x + {r1})(x + {r2})"
                t2 = f"(x - {r1})(x + {r2})"
                t3 = f"(x + {r1})(x - {r2})"
                
                options_list = [
                    (correct_val, None),
                    (t1, "sign_error_all_positive"),
                    (t2, "sign_error_first_negative"),
                    (t3, "sign_error_second_negative")
                ]
                a, b = r1, r2
            else:
                x_val = rng.randint(2, 9)
                y_val = rng.randint(2, 9)
                while x_val == y_val:
                    y_val = rng.randint(2, 9)
                    
                s = x_val + y_val
                d = x_val - y_val
                
                math_expr = f"x + y = {s}, x - y = {d}"
                stem_template = f"Solve the system of equations: x + y = {s} and x - y = {d}. What is the value of (x, y)?"
                correct_val = f"({x_val}, {y_val})"
                
                options_list = [
                    (correct_val, None),
                    (f"({y_val}, {x_val})", "coordinate_swap_error"),
                    (f"({x_val}, {-y_val})", "y_sign_error"),
                    (f"({-x_val}, {y_val})", "x_sign_error")
                ]
                a, b, c, d = x_val, y_val, s, d

        elif g_level >= 6:
            # Middle School: 2-step algebraic equations
            a_val = rng.randint(2, 6)
            x_val = rng.randint(2, 8)
            b_val = rng.randint(1, 10)
            c_val = a_val * x_val + b_val
            
            math_expr = f"{a_val}x + {b_val} = {c_val}"
            stem_template = f"Solve the equation: {a_val}x + {b_val} = {c_val}. What is the value of x?"
            correct_val = str(x_val)
            
            t1 = str(round((c_val + b_val)/a_val, 1))
            t2 = str(round(c_val/a_val - b_val, 1))
            t3 = str(x_val + rng.choice([-2, -1, 1, 2]))
            
            options_list = [
                (correct_val, None),
                (t1, "operator_addition_confusion"),
                (t2, "precedence_division_error"),
                (t3, "distractor_offset")
            ]
            a, b, c = a_val, b_val, c_val

        elif g_level >= 3:
            # Elementary: Basic Arithmetic with operator variability
            op = rng.choice(["+", "-", "*"])
            if op == "+":
                a = rng.randint(10, 99)
                b = rng.randint(10, 99)
                correct_val = str(a + b)
                math_expr = f"{a} + {b}"
                stem_template = f"Solve: {a} + {b} = ?"
                options_list = [
                    (correct_val, None),
                    (str(a * b), "multiplied_instead_of_added"),
                    (str(a - b), "subtracted_instead_of_added"),
                    (str(a + b + rng.choice([-2, -1, 1, 2])), "counting_off_by_one")
                ]
            elif op == "-":
                a = rng.randint(20, 99)
                b = rng.randint(5, a - 1)
                correct_val = str(a - b)
                math_expr = f"{a} - {b}"
                stem_template = f"Solve: {a} - {b} = ?"
                options_list = [
                    (correct_val, None),
                    (str(a * b), "multiplied_instead_of_subtracted"),
                    (str(a + b), "added_instead_of_subtracted"),
                    (str(a - b + rng.choice([-2, -1, 1, 2])), "counting_off_by_one")
                ]
            else:
                a = rng.randint(2, 9)
                b = rng.randint(2, 9)
                correct_val = str(a * b)
                math_expr = f"{a} × {b}"
                stem_template = f"Solve: {a} × {b} = ?"
                options_list = [
                    (correct_val, None),
                    (str(a + b), "added_instead_of_multiplied"),
                    (str(a - b), "subtracted_instead_of_multiplied"),
                    (str(a * b + rng.choice([-2, -1, 1, 2])), "counting_off_by_one")
                ]
        else:
            # Early Elementary (Grades 1-2): Single-Digit Arithmetic
            op = rng.choice(["+", "-"])
            if op == "+":
                a = rng.randint(1, 9)
                b = rng.randint(1, 9)
                correct_val = str(a + b)
                math_expr = f"{a} + {b}"
                stem_template = f"Solve: {a} + {b} = ?"
                options_list = [
                    (correct_val, None),
                    (str(a * b) if a * b != a + b else str(a + b + 3), "multiplied_instead_of_added"),
                    (str(abs(a - b)), "subtracted_instead_of_added"),
                    (str(a + b + rng.choice([-1, 1])), "counting_off_by_one")
                ]
            else:
                a = rng.randint(2, 9)
                b = rng.randint(1, a)
                correct_val = str(a - b)
                math_expr = f"{a} - {b}"
                stem_template = f"Solve: {a} - {b} = ?"
                options_list = [
                    (correct_val, None),
                    (str(a * b) if a * b != a - b else str(a - b + 3), "multiplied_instead_of_subtracted"),
                    (str(a + b), "added_instead_of_subtracted"),
                    (str(a - b + rng.choice([-1, 1])), "counting_off_by_one")
                ]

    # =========================================================================
    # POST-PROCESSING: Deduplicate, shuffle, assign keys
    # =========================================================================
    
    # Deduplicate option values
    unique_options = []
    seen_vals = set()
    for val, trap in options_list:
        # Normalize fraction representations
        try:
            parsed = sp.Rational(val)
            val_str = str(parsed)
        except Exception:
            val_str = str(val).strip()
            
        if val_str not in seen_vals:
            seen_vals.add(val_str)
            unique_options.append((val_str, trap))
            
    # If we don't have 4 options, fill with random distractors
    while len(unique_options) < 4:
        try:
            curr_val = sp.Rational(unique_options[0][0])
            rand_offset = rng.randint(-5, 5)
            if rand_offset == 0: rand_offset = 1
            new_val = str(curr_val + rand_offset)
        except Exception:
            new_val = str(rng.randint(1, 100))
            
        if new_val not in seen_vals:
            seen_vals.add(new_val)
            unique_options.append((new_val, "distractor"))

    # Shuffle options and assign ABCD keys using a DEDICATED shuffle RNG
    # This ensures the shuffle is independent of how many RNG calls were made during generation.
    shuffle_rng = random.Random(seed + 777)
    shuffle_rng.shuffle(unique_options)
    keys = ["A", "B", "C", "D"]
    options = {}
    for i, key in enumerate(keys):
        if i < len(unique_options):
            options[key] = {
                "value": unique_options[i][0],
                "trap_name": unique_options[i][1]
            }

    # Identify which key is correct
    correct_key = "A"
    # Normalize correct_val for comparison
    try:
        correct_rational = str(sp.Rational(correct_val))
    except Exception:
        correct_rational = str(correct_val).strip()
    
    for key, opt in options.items():
        if opt["value"] == correct_rational:
            correct_key = key
            break

    # Build variables dict
    variables_dict = {"a": a, "b": b}
    if c != 0:
        variables_dict["c"] = c
    if d != 0:
        variables_dict["d"] = d

    return {
        "skeleton_id": f"{skill_clean.lower()}_skel_{seed}",
        "variables": variables_dict,
        "stem_template": stem_template,
        "correct_answer": correct_val,
        "correct_key": correct_key,
        "options": options,
        "math_expression": math_expr
    }


def _match_domain(skill_clean: str, domains: list) -> bool:
    """
    Checks if a skill ID matches any of the given domain prefixes.
    Handles both dot-notation (5.NF.A.1) and dash-notation (A-REI.C.8).
    """
    for domain in domains:
        domain_upper = domain.upper()
        if domain_upper in skill_clean:
            return True
    return False


def validate_answer(math_expr: str, student_ans: str) -> bool:
    """
    Deterministic validation using SymPy solver.
    Parses and verifies if the student_ans is mathematically equivalent to the solved math_expr.
    """
    try:
        expr_solved = parse_expr(math_expr)
        ans_solved = parse_expr(student_ans)
        return sp.simplify(expr_solved - ans_solved) == 0
    except Exception:
        # Fallback to direct string matching
        return str(math_expr).strip() == str(student_ans).strip()


def generate_worked_example_steps(skill_id: str, skeleton: dict) -> list:
    """
    Generates pedagogically meaningful worked example steps based on the problem type.
    Returns a list of step strings that actually teach the solving process.
    """
    skill_clean = skill_id.upper()
    math_expr = skeleton.get("math_expression", "")
    correct = skeleton.get("correct_answer", "")
    variables = skeleton.get("variables", {})
    a = variables.get("a", 0)
    b = variables.get("b", 0)
    c = variables.get("c", 0)
    d = variables.get("d", 0)

    # 1.G.1 worked example
    if "1.G.1" in skill_clean:
        if "attribute" in skeleton.get("stem_template", "").lower():
            return [
                "Step 1: A defining attribute is something a shape MUST have to be that shape (like number of sides).",
                "Step 2: Non-defining attributes are things like color, size, or orientation, which can change without changing what the shape is.",
                "Step 3: A triangle MUST have exactly 3 straight sides and be closed.",
                f"Step 4: The correct defining attribute is: {correct}."
            ]
        else:
            return [
                "Step 1: Look at the attributes of the shape drawn.",
                "Step 2: It is closed and has exactly 3 straight sides.",
                "Step 3: A shape with 3 straight sides is called a Triangle.",
                f"Step 4: The shape is {correct}."
            ]

    # 2.G.1 worked example
    if "2.G.1" in skill_clean:
        if "cube" in skeleton.get("stem_template", "").lower():
            return [
                "Step 1: A solid cube is a 3D shape with square faces.",
                "Step 2: Count the faces: front, back, top, bottom, left, and right.",
                "Step 3: There are exactly 6 square faces.",
                f"Step 4: The answer is {correct}."
            ]
        elif "angles" in skeleton.get("stem_template", "").lower() or "sides" in skeleton.get("stem_template", "").lower():
            return [
                "Step 1: Look at the attributes: 5 sides and 5 angles.",
                "Step 2: A triangle has 3 sides; a quadrilateral has 4 sides.",
                "Step 3: A shape with exactly 5 sides and 5 angles is a Pentagon.",
                f"Step 4: The answer is {correct}."
            ]
        else:
            return [
                "Step 1: A corner or vertex is where straight sides meet.",
                "Step 2: Count the corners: 1, 2, 3, 4, 5, 6.",
                "Step 3: A shape with 6 corners (and 6 sides) is a Hexagon.",
                f"Step 4: The answer is {correct}."
            ]

    # 3.G.1 worked example
    if "3.G.1" in skill_clean:
        if "category" in skeleton.get("stem_template", "").lower():
            return [
                "Step 1: A quadrilateral is any closed shape with exactly 4 straight sides.",
                "Step 2: Rhombuses, rectangles, and squares all have exactly 4 sides.",
                "Step 3: Therefore, they all belong to the larger category of Quadrilaterals.",
                f"Step 4: The answer is {correct}."
            ]
        else:
            return [
                "Step 1: Think about the properties of squares and rectangles.",
                "Step 2: A square must have 4 equal sides, but a rectangle does not have to.",
                "Step 3: Both squares and rectangles are defined by having 4 right angles.",
                f"Step 4: The correct statement is: {correct}."
            ]

    # 4.G.1 worked example
    if "4.G.1" in skill_clean:
        if "forever" in skeleton.get("stem_template", "").lower() or "endpoint" in skeleton.get("stem_template", "").lower():
            return [
                "Step 1: A line goes on forever in both directions (no endpoints).",
                "Step 2: A line segment starts at one endpoint and ends at another (two endpoints).",
                "Step 3: A ray starts at one endpoint and goes on forever in one direction (one endpoint).",
                f"Step 4: The correct term is {correct}."
            ]
        elif "cross" in skeleton.get("stem_template", "").lower() or "angle" in skeleton.get("stem_template", "").lower() and "lines" in skeleton.get("stem_template", "").lower():
            return [
                "Step 1: Parallel lines never cross each other.",
                "Step 2: Perpendicular lines cross each other at a perfect 90-degree right angle.",
                "Step 3: Since these lines cross at a right angle, they are perpendicular.",
                f"Step 4: The answer is {correct}."
            ]
        else:
            return [
                "Step 1: A right angle is exactly 90 degrees (looks like a square corner).",
                "Step 2: An obtuse angle is larger than 90 degrees.",
                "Step 3: An acute angle is smaller than 90 degrees.",
                f"Step 4: Since this angle is less than 90 degrees, it is an {correct}."
            ]

    # 5.G.1 worked example
    if "5.G.1" in skill_clean:
        if "origin" in skeleton.get("stem_template", "").lower():
            return [
                "Step 1: In coordinate planes, an ordered pair is written as (x, y).",
                f"Step 2: The first number (x) represents the horizontal distance (move right from the origin). Here, we moved {a} units.",
                f"Step 3: The second number (y) represents the vertical distance (move up from the origin). Here, we moved {b} units.",
                "Step 4: Put them together into (x, y) format.",
                f"Step 5: The ordered pair is {correct}."
            ]
        else:
            return [
                "Step 1: Coordinate pairs are always written in the order (x, y).",
                "Step 2: The first coordinate (x) represents horizontal movement along the x-axis.",
                "Step 3: The second coordinate (y) represents vertical movement along the y-axis.",
                f"Step 4: Therefore, the first number represents: {correct}."
            ]

    # 6.EE.1 worked example
    if "6.EE.1" in skill_clean:
        if "power" in skeleton.get("stem_template", "").lower():
            return [
                f"Step 1: An exponent tells you how many times to multiply the base by itself.",
                f"Step 2: In {a}^{b}, {a} is the base and {b} is the exponent.",
                f"Step 3: Multiply {a} by itself {b} times: " + " × ".join([str(a)] * int(b)) + ".",
                f"Step 4: {a}^{b} = {correct}."
            ]
        else:
            return [
                f"Step 1: To represent a number {a} multiplied by itself {b} times, we use exponential notation.",
                f"Step 2: The number being multiplied ({a}) is the base.",
                f"Step 3: The number of times it is multiplied ({b}) is the exponent.",
                f"Step 4: This is written as {correct}."
            ]

    # 7.EE.1 worked example
    if "7.EE.1" in skill_clean:
        if "Expand" in skeleton.get("stem_template", "").lower():
            sign = "+" if c > 0 else "-"
            return [
                f"Step 1: Start with the expression: {a}({b}x {sign} {abs(c)}).",
                f"Step 2: Apply the distributive property by multiplying {a} by each term inside the parentheses.",
                f"Step 3: Multiply {a} × {b}x = {a * b}x.",
                f"Step 4: Multiply {a} × {c} = {a * c}.",
                f"Step 5: Combine the terms: {correct}."
            ]
        else:
            return [
                f"Step 1: Start with the expression: ({a}x + {b}) - ({c}x - {d}).",
                f"Step 2: Distribute the negative sign across the second group: -({c}x - {d}) = -{c}x + {d}.",
                f"Step 3: Rewrite the expression: {a}x + {b} - {c}x + {d}.",
                f"Step 4: Group like terms together: ({a}x - {c}x) + ({b} + {d}).",
                f"Step 5: Combine x terms: ({a} - {c})x = {a - c}x.",
                f"Step 6: Combine constant terms: {b} + {d} = {b + d}.",
                f"Step 7: Final simplified expression: {correct}."
            ]

    # 8.EE.1 worked example
    if "8.EE.1" in skill_clean:
        if "×" in skeleton.get("stem_template", "").lower():
            return [
                f"Step 1: When multiplying terms with the same base, keep the base and add the exponents: a^m × a^n = a^(m+n).",
                f"Step 2: The base is {a}, and the exponents are {b} and {c}.",
                f"Step 3: Add the exponents: {b} + {c} = {b + c}.",
                f"Step 4: The simplified expression is {correct}."
            ]
        elif "÷" in skeleton.get("stem_template", "").lower():
            return [
                f"Step 1: When dividing terms with the same base, keep the base and subtract the exponents: a^m ÷ a^n = a^(m-n).",
                f"Step 2: The base is {a}, and the exponents are {b} and {c}.",
                f"Step 3: Subtract the exponents: {b} - {c} = {b - c}.",
                f"Step 4: The simplified expression is {correct}."
            ]
        else:
            return [
                f"Step 1: A negative exponent represents the reciprocal of the base raised to the positive exponent: a^(-n) = 1 / a^n.",
                f"Step 2: The base is {a}, and the exponent is -{b}.",
                f"Step 3: Rewrite as a fraction with 1 in the numerator and the positive exponent in the denominator.",
                f"Step 4: The equivalent expression is {correct}."
            ]
    c = variables.get("c", 0)
    d = variables.get("d", 0)

    # Fraction addition (unlike denominators)
    if "5.NF.A.1" in skill_clean or ("NF" in skill_clean and "+" in math_expr):
        if "/" in math_expr and "+" in math_expr:
            try:
                parts = math_expr.split("+")
                frac1 = parts[0].strip()
                frac2 = parts[1].strip()
                n1, d1 = frac1.split("/")
                n2, d2 = frac2.split("/")
                n1, d1, n2, d2 = int(n1), int(d1), int(n2), int(d2)
                lcm = abs(d1 * d2) // sp.gcd(d1, d2)
                new_n1 = n1 * (lcm // d1)
                new_n2 = n2 * (lcm // d2)
                return [
                    f"Step 1: We need to add {frac1} + {frac2}.",
                    f"Step 2: Find the Least Common Denominator (LCD) of {d1} and {d2}: LCD = {lcm}.",
                    f"Step 3: Convert {frac1} → {new_n1}/{lcm} (multiply top and bottom by {lcm // d1}).",
                    f"Step 4: Convert {frac2} → {new_n2}/{lcm} (multiply top and bottom by {lcm // d2}).",
                    f"Step 5: Add the numerators: {new_n1} + {new_n2} = {new_n1 + new_n2}.",
                    f"Step 6: Result: {new_n1 + new_n2}/{lcm} = {correct}."
                ]
            except Exception:
                pass

    # Fraction multiplication
    if "5.NF.B.4" in skill_clean or ("NF" in skill_clean and "×" in math_expr):
        if "/" in math_expr and "×" in math_expr:
            return [
                f"Step 1: To multiply fractions, multiply the numerators together and the denominators together.",
                f"Step 2: Numerators: {a} × {c} = {a * c}.",
                f"Step 3: Denominators: {b} × {d} = {b * d}.",
                f"Step 4: Result: {a * c}/{b * d}.",
                f"Step 5: Simplify if possible. Final answer: {correct}."
            ]

    # Order of operations
    if "OA.A.1" in skill_clean and "(" in math_expr:
        return [
            f"Step 1: Look at the expression: {math_expr}.",
            f"Step 2: PEMDAS rule — solve Parentheses first: {b} + {c} = {b + c}.",
            f"Step 3: Now multiply: {a} × {b + c} = {correct}.",
            f"Step 4: Final answer: {correct}."
        ]

    # Multiplication/division (OA)
    if "OA" in skill_clean and ("×" in math_expr or "÷" in math_expr):
        if "×" in math_expr:
            return [
                f"Step 1: We need to find {a} × {b}.",
                f"Step 2: This means {a} groups of {b} items.",
                f"Step 3: Count by {b}s, {a} times: {', '.join(str(b * i) for i in range(1, a + 1))}.",
                f"Step 4: Final answer: {correct}."
            ]

    # Linear equations
    if "EE" in skill_clean and "x" in math_expr.lower():
        return [
            f"Step 1: Start with the equation: {math_expr}.",
            f"Step 2: Subtract {b} from both sides to isolate the term with x.",
            f"Step 3: Divide both sides by {a} to solve for x.",
            f"Step 4: x = {correct}."
        ]

    # Geometry (area/perimeter)
    if "MD" in skill_clean or "G" in skill_clean:
        if "area" in skeleton.get("stem_template", "").lower():
            return [
                f"Step 1: Area = length × width.",
                f"Step 2: Area = {a} × {b} = {correct}.",
                f"Step 3: Remember: area is measured in square units."
            ]
        elif "perimeter" in skeleton.get("stem_template", "").lower():
            return [
                f"Step 1: Perimeter = 2 × (length + width).",
                f"Step 2: Perimeter = 2 × ({a} + {b}) = 2 × {a + b} = {correct}.",
                f"Step 3: Remember: perimeter is the total distance around the shape."
            ]
        elif "K.G" in skill_clean:
            return [
                f"Step 1: Look at the shape's features.",
                f"Step 2: Does it have 3 sides? That's a Triangle.",
                f"Step 3: Does it have 4 equal sides? That's a Square.",
                f"Step 4: Is it perfectly round? That's a Circle.",
                f"Step 5: The answer is {correct}."
            ]

    # Kindergarten Counting & Operations
    if "K.CC" in skill_clean or "K.OA" in skill_clean or "K.MP" in skill_clean:
        if "after" in skeleton.get("stem_template", "").lower():
            return [
                f"Step 1: Start at the number {a}.",
                f"Step 2: Count up by one: {a}... {int(a) + 1}.",
                f"Step 3: The number that comes next is {correct}."
            ]
        elif "greater" in skeleton.get("stem_template", "").lower():
            return [
                f"Step 1: Compare {a} and {b}.",
                f"Step 2: Imagine {a} blocks and {b} blocks.",
                f"Step 3: Which pile is bigger?",
                f"Step 4: {correct} is the bigger number."
            ]
        elif "mistake" in skeleton.get("stem_template", "").lower():
            return [
                f"Step 1: Look at the problem: {math_expr}.",
                f"Step 2: Check the math: {a} + {b} is actually {a + b}.",
                f"Step 3: Since {correct.lower().replace('yes, ', '').replace('.', '')}, we know there was a mistake.",
                f"Step 4: The answer is {correct}."
            ]
        elif "tool" in skeleton.get("stem_template", "").lower():
            return [
                f"Step 1: What are we measuring? Length (how long something is).",
                f"Step 2: A ruler measures length.",
                f"Step 3: A scale measures weight.",
                f"Step 4: A clock measures time.",
                f"Step 5: The best tool is {correct}."
            ]
        elif "birds" in skeleton.get("stem_template", "").lower():
            return [
                f"Step 1: We started with {a} birds.",
                f"Step 2: {b} birds flew away. That means we take away {b}.",
                f"Step 3: {a} take away {b} leaves {a - b}.",
                f"Step 4: Choose the picture that shows {a - b} birds."
            ]
        elif "sentence" in skeleton.get("stem_template", "").lower():
            return [
                f"Step 1: You have {a} and get {b} more.",
                f"Step 2: 'More' means we add: +.",
                f"Step 3: Total is {a} + {b} = {a + b}.",
                f"Step 4: The correct math sentence is {correct}."
            ]
        elif "count" in math_expr:
            return [
                f"Step 1: Look at the objects in the box.",
                f"Step 2: Count them one by one: 1, 2, 3... {correct}.",
                f"Step 3: There are {correct} in total."
            ]
        elif "structure" in math_expr:
            return [
                f"Step 1: We have one group of 10 red blocks.",
                f"Step 2: We have another group of 10 blue blocks.",
                f"Step 3: Count the groups: 1... 2.",
                f"Step 4: There are {correct} of 10."
            ]
        elif "make 10" in skeleton.get("stem_template", "").lower():
            return [
                f"Step 1: You have {a} blocks.",
                f"Step 2: Count up from {a} until you reach 10.",
                f"Step 3: {', '.join(str(i) for i in range(int(a)+1, 11))}.",
                f"Step 4: You counted {correct} more numbers.",
                f"Step 5: {a} + {correct} = 10."
            ]
        elif "+" in math_expr:
            return [
                f"Step 1: Start with {a} items.",
                f"Step 2: Add {b} more items.",
                f"Step 3: Count them all together: 1, 2, 3... {correct}.",
                f"Step 4: {a} + {b} = {correct}."
            ]
        elif "-" in math_expr:
            return [
                f"Step 1: Start with {a} items.",
                f"Step 2: Take away {b} items.",
                f"Step 3: Count how many are left.",
                f"Step 4: {a} - {b} = {correct}."
            ]

    # Ratios
    if "RP" in skill_clean:
        return [
            f"Step 1: The ratio is {a}:{b}.",
            f"Step 2: Find the scale factor: {a * c} ÷ {a} = {c}.",
            f"Step 3: Multiply the second term by the scale factor: {b} × {c} = {correct}.",
            f"Step 4: The answer is {correct}."
        ]

    # Default generic worked example (still better than the old version)
    return [
        f"Step 1: Read the problem carefully: {math_expr}.",
        f"Step 2: Identify the operation needed.",
        f"Step 3: Perform the calculation step by step.",
        f"Step 4: The answer is {correct}."
    ]
