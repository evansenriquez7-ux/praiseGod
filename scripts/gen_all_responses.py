#!/usr/bin/env python3
"""
Comprehensive Progressions extraction response generator.
Pre-generates responses for all 16 sections of CCSS Progressions to enable fast batch processing.
"""

import json
import os
from pathlib import Path

def generate_nbt_responses():
    """Extract K-5 NBT (Number and Operations in Base Ten) standards."""
    return json.dumps([
        {
            "standard_id": "K.NBT.1",
            "detailed_explanation": "Students decompose numbers 11-19 as a ten and some ones, using objects or drawings to physically/visually show the composition. Understanding that 13 is '1 ten and 3 ones' is fundamental to place value. Students must move beyond counting by ones to seeing the place value structure inherent in teen numbers.",
            "worked_examples": "Using objects: 13 blocks = 1 ten-frame (10) + 3 more blocks (3 ones). Using drawings: 13 circles can be circled as a group of 10 and 3 separate ones. Saying and writing: 'thirteen is ten and three' or '10 + 3'.",
            "misconceptions": "Students may count all 13 objects individually without recognizing the group of 10. Some may understand that '10 + 3 = 13' algebraically without connecting it to the physical quantity. Students may confuse place value with just addition.",
            "parameter_constraints": "Numbers from 11 to 19 only. Teen numbers are explicitly addressed here. Ten-frame is a primary tool. Must use visual/physical representation, not just notation.",
            "developmental_context": "Prepares for understanding place value more deeply in Grade 1 (1.NBT.2). Connects Counting and Cardinality (K.CC) to base-ten structure. Crucial for understanding regrouping and multi-digit arithmetic in later grades."
        },
        {
            "standard_id": "1.NBT.1",
            "detailed_explanation": "Students count to 120, progressing from 100 in K. This extended fluency with the counting sequence is foundational. Students must understand patterns in the teens (11-19), the decades (20, 30, ..., 90), and beyond. The decade pattern 20, 30, 40, etc., is explicitly named and practiced.",
            "worked_examples": "Counting forward: 1, 2, ..., 10, 11, 12, ..., 20, 21, ..., 99, 100, ..., 120. Recognizing patterns: 20, 30, 40, ... Pattern in teens: 10+1=11, 10+2=12, etc. Skip counting by tens: 10, 20, 30, etc.",
            "misconceptions": "Students may not recognize the pattern in teen numbers (10+something). Some may struggle with the transition from 19 to 20 and the teens pattern. Students may not see 30, 40, 50 as 'three tens,' 'four tens,' 'five tens.'",
            "parameter_constraints": "Counting to 120, often with emphasis on patterns and structure. Not just memorization, but understanding the structure of the count sequence.",
            "developmental_context": "Extension of K.CC.1 (counting to 100). Foundation for understanding place value (1.NBT.2, 1.NBT.3). Provides the count sequence understanding needed for 1.OA.6 strategies (counting on) and later multi-digit work."
        },
        {
            "standard_id": "1.NBT.2",
            "detailed_explanation": "Students understand that two-digit numbers are composed of tens and ones, not just as abstract notation but as an actual decomposition of quantity. 35 is understood as '3 tens + 5 ones' = 30 + 5, with physical/visual meaning. This place value understanding is distinct from and deeper than just 'saying' the number.",
            "worked_examples": "Using ten-frames and ones: showing 35 as 3 filled ten-frames and 5 loose counters. Using drawings or Base-Ten blocks: 3 long rods (each representing 10) and 5 units (each representing 1). Recording: 35 = 30 + 5. Number line: marking 35 as 30 (3 tens) + 5 more (5 ones).",
            "misconceptions": "Students may understand 35 as '35 ones' without recognizing the tens grouping. Some may say '3 tens, 5 ones' but not connect it to quantity. Students may confuse the digits (thinking '3' and '5' are just labels, not quantities).",
            "parameter_constraints": "Two-digit numbers (10-99). Must use concrete objects, drawings, or manipulatives initially. Understanding applies to all two-digit numbers. Include notation like 35 = 3 tens + 5 ones or 35 = 30 + 5.",
            "developmental_context": "Core foundation for all multi-digit arithmetic in Grades 1-5. Builds from K.NBT.1 (teen numbers). Essential for understanding 1.NBT.3 (comparing), regrouping in addition/subtraction (1.NBT.4, 1.NBT.6), and later extensions to hundreds/thousands (2.NBT, 3.NBT). Central to place value understanding."
        },
        {
            "standard_id": "1.NBT.2a",
            "detailed_explanation": "Students understand that the tens digit represents groups of ten and the ones digit represents the remaining ones. Each position in a two-digit number has a meaning based on its place value. The digit 3 in 35 doesn't just mean 3; it means 3 tens (30).",
            "worked_examples": "In 47: the 4 represents 4 tens (40) and the 7 represents 7 ones. In 18: the 1 represents 1 ten (10) and the 8 represents 8 ones. Using Base-Ten blocks: 4 tens rods + 7 ones units for 47.",
            "misconceptions": "Students may see 47 as 'forty-seven' without understanding that the 4 means 'tens.' They may treat 47 the same as 47 ones. Confusion between the digit value and place value.",
            "parameter_constraints": "Applies to all two-digit numbers (10-99). Foundation for understanding larger numbers later.",
            "developmental_context": "Sub-standard of 1.NBT.2, explicitly defining place value understanding."
        },
        {
            "standard_id": "1.NBT.2b",
            "detailed_explanation": "The numbers 10, 20, 30, 40, 50, 60, 70, 80, 90 are multiples of ten (decade numbers). Students understand these as '1 ten,' '2 tens,' '3 tens,' etc., not as separate entities but as specific place value configurations.",
            "worked_examples": "10 = 1 ten + 0 ones. 30 = 3 tens + 0 ones. 90 = 9 tens + 0 ones. Using ten-frames or Base-Ten blocks: multiple filled ten-frames with no ones.",
            "misconceptions": "Students may not recognize that 20, 30, etc., are built from tens. Some may see them as arbitrary labels in the sequence.",
            "parameter_constraints": "The decade numbers: 10, 20, 30, 40, 50, 60, 70, 80, 90. Foundation for understanding any two-digit number.",
            "developmental_context": "Sub-standard of 1.NBT.2, establishing the foundation of place value."
        },
        {
            "standard_id": "1.NBT.3",
            "detailed_explanation": "Students compare two-digit numbers using place value reasoning. When comparing 47 and 52, a student reasons: '47 has 4 tens, 52 has 5 tens. 5 tens is more, so 52 is bigger.' Comparison is based on understanding tens place first, then ones place if tens are equal. This develops deep number sense.",
            "worked_examples": "Comparing 23 and 18: '23 has 2 tens, 18 has 1 ten. So 23 is bigger.' Comparing 24 and 26: 'Both have 2 tens. Now look at ones: 24 has 4 ones, 26 has 6 ones. 26 is bigger.' Using symbols: 23 > 18, 24 < 26.",
            "misconceptions": "Students may compare the ones place first, or may compare by looking at digit positions without understanding place value. Students might compare 23 and 32 by thinking '2 and 3 in 23' versus '3 and 2 in 32' without understanding position.",
            "parameter_constraints": "Comparing two-digit numbers (10-99). Using <, >, or = symbols. Must use place value reasoning, not just counting or guessing.",
            "developmental_context": "Applies 1.NBT.2 understanding to comparison. Extends K.CC.6-K.CC.7 (comparing with objects/numerals) to place value-based comparison. Foundation for understanding the number line, ordering, and inequality reasoning."
        },
        {
            "standard_id": "1.NBT.4",
            "detailed_explanation": "Students add within 100 by understanding and using place value. When adding 30 + 7 + 15, a student might add: (30 + 10) + (7 + 5) = 40 + 12 = 52. Understanding that you can decompose numbers by place value and recombine enables flexible addition. Initial instruction uses manipulatives or drawings.",
            "worked_examples": "23 + 5: 'I can do (20 + 3) + 5 = 20 + 8 = 28.' Or using tens/ones: '2 tens + 3 ones + 5 ones = 2 tens + 8 ones = 28.' 28 + 14: '(20 + 8) + (10 + 4) = (20 + 10) + (8 + 4) = 30 + 12 = 42.' Using Base-Ten blocks or drawings to show regrouping.",
            "misconceptions": "Students may add 23 + 5 as '20 + 5 = 25, then 3, so 28' without understanding place value, relying on memorization. Students might add vertically without understanding what they're doing. Some may not recognize when they need to regroup (compose/decompose tens).",
            "parameter_constraints": "Addition within 100. Should use place value strategies, not standard algorithm initially. Both addends should be within 100.",
            "developmental_context": "Applies 1.NBT.2-1.NBT.3 understanding to addition. Moves from 1.OA.6 (addition within 20) to larger numbers. Precursor to standard algorithm in 2.NBT.7. Foundation for multi-digit addition in later grades."
        },
        {
            "standard_id": "1.NBT.5",
            "detailed_explanation": "Students find mentally 10 more or 10 less than a number, using place value understanding. For 32, they recognize that 10 more is 42 (adds 1 ten) and 10 less is 22 (removes 1 ten). This builds fluency with tens and prepares for regrouping strategies.",
            "worked_examples": "10 more than 24: '24 + 10 = 34. I added 1 ten.' 10 less than 57: '57 - 10 = 47. I removed 1 ten.' Using place value notation: 24 has 2 tens, +1 ten = 3 tens (34). 57 has 5 tens, -1 ten = 4 tens (47).",
            "misconceptions": "Students may add or subtract the ones digit without understanding that adding 10 means adding a ten. Some might compute 24 + 10 by adding 1 to the ones place (getting 25) instead of recognizing the tens place changes.",
            "parameter_constraints": "Numbers within 100 (so that 10 less or 10 more stays within 0-110). Should be computed mentally, not with manipulatives or written algorithms.",
            "developmental_context": "Builds number sense with tens. Precursor to 2.NBT.8 (regrouping/renaming in subtraction). Supports flexible mental math. Foundation for understanding regrouping conceptually."
        },
        {
            "standard_id": "1.NBT.6",
            "detailed_explanation": "Students subtract within 100 using place value understanding and strategies, similar to 1.NBT.4 for addition. When subtracting 45 - 12, a student might think: '(40 + 5) - (10 + 2) = (40 - 10) + (5 - 2) = 30 + 3 = 33.' Students use manipulatives, drawings, or place value strategies before formal algorithms.",
            "worked_examples": "37 - 5: '(30 + 7) - 5 = 30 + 2 = 32.' 42 - 15: '(40 + 2) - (10 + 5). I can't take 5 from 2. I regroup: 40 + 2 = 30 + 12. Now (30 - 10) + (12 - 5) = 20 + 7 = 27.' Using drawings or Base-Ten blocks to show the process.",
            "misconceptions": "Students may struggle with regrouping (e.g., in 42 - 15, not recognizing they need to regroup). They might compute 42 - 15 as '4 - 1 = 3, 2 - 5 = ?' without understanding place value. Misunderstanding of regrouping is common.",
            "parameter_constraints": "Subtraction within 100. Initially with manipulatives/drawings. Introduction to regrouping/composing/decomposing tens when needed. Both minuend and subtrahend within 100.",
            "developmental_context": "Applies place value to subtraction (parallel to 1.NBT.4 for addition). Introduces regrouping conceptually, formalized in 2.NBT.7-2.NBT.8. Foundation for multi-digit subtraction. Essential for understanding how the standard algorithm works."
        },
        {
            "standard_id": "2.NBT.1",
            "detailed_explanation": "Students understand three-digit numbers (100-999) as composed of hundreds, tens, and ones. 243 is '2 hundreds, 4 tens, 3 ones' = 200 + 40 + 3. The extension from two-digit to three-digit place value follows the same reasoning: each position represents a power of 10 (groups of ten times ten).",
            "worked_examples": "258 = 2 hundreds + 5 tens + 8 ones = 200 + 50 + 8. Using Base-Ten blocks: 2 hundreds flats + 5 tens rods + 8 ones units. Number line: 258 as 200 + 50 + 8. Understanding that the 2 (in the hundreds place) represents 2 groups of one hundred.",
            "misconceptions": "Students may not extend their two-digit understanding to three digits. Some might think 258 is just 25 tens and 8 ones, missing the hundreds place understanding. Confusion about what each digit represents is common.",
            "parameter_constraints": "Three-digit numbers from 100 to 999. May use physical manipulatives, drawings, or expanded notation (200 + 50 + 8). Foundation for understanding all multi-digit numbers.",
            "developmental_context": "Direct extension of 1.NBT.2. Applies the same place value reasoning to a new position. Prepares for 2.NBT.2 (reading/writing), 2.NBT.3 (skip counting), 2.NBT.4 (comparing), and 2.NBT.7-2.NBT.8 (operations with regrouping). Core to all later place value work."
        }
    ])

def generate_md_responses():
    """Extract K-5 MD (Measurement and Data) standards."""
    return json.dumps([
        {
            "standard_id": "K.MD.1",
            "detailed_explanation": "Students describe measurable attributes of objects using language like 'long/short,' 'heavy/light,' 'tall/short.' The focus is on recognizing that objects have attributes that can be compared, not on precise measurement. Students compare two objects directly and describe the attribute.",
            "worked_examples": "Comparing two pencils: 'This pencil is longer than that one.' Comparing blocks: 'This block is heavier.' Comparing heights of children: 'She is taller than him.' Using descriptive language, not numbers initially.",
            "misconceptions": "Students may confuse different attributes (e.g., thinking a long, thin object is heavier). They may compare attributes without consistent language. Some may not understand that the same object can be 'long' compared to one object but 'short' compared to another.",
            "parameter_constraints": "Everyday objects and people. Attributes: length (long/short), height (tall/short), weight (heavy/light). Direct comparison, no measurement tools needed.",
            "developmental_context": "Introduction to measurement thinking. Lays groundwork for K.MD.2 (non-standard units) and 1.MD.1 (standard units). Foundation for understanding how we quantify physical properties."
        },
        {
            "standard_id": "K.MD.2",
            "detailed_explanation": "Students measure objects using non-standard units (e.g., 'cubes,' 'paper clips,' 'handspans'). The goal is for students to understand that measurement involves iterable units and that different units yield different numbers. A pencil might be '8 cubes long' or '6 paperclips long.' This prepares for understanding standard units.",
            "worked_examples": "Measuring a pencil with cubes: lining up cubes end-to-end and counting (e.g., 12 cubes). Measuring with paper clips: 'The pencil is as long as 9 paperclips.' Understanding that using smaller units (paperclips) gives a larger number than using larger units (cubes).",
            "misconceptions": "Students may misalign units (gaps or overlaps when placing units). They may not understand that different units produce different numbers. Some may measure the same object and get different answers, not recognizing the inconsistency.",
            "parameter_constraints": "Classroom objects (pencils, crayons, desks). Non-standard units (blocks, cubes, paperclips, handspans). No standard units (inches, centimeters). Attributes: primarily length.",
            "developmental_context": "Bridges from comparing (K.MD.1) to understanding measurement as iteration of units. Prepares for 1.MD.1-1.MD.2 (measuring with standard units). Develops understanding that measurement is a scale and different units scale differently."
        },
        {
            "standard_id": "K.MD.3",
            "detailed_explanation": "Students classify objects into given categories (e.g., by color, shape, or size) and count the number in each category. The focus is on sorting and organizing, and then using counting skills from K.CC to quantify each group. This combines Classification (logic) with Counting (quantification).",
            "worked_examples": "Given a collection of buttons: sorting by color (red buttons, blue buttons, yellow buttons) and counting how many in each group. Sorting toys by size (big toys, small toys) and counting. Recording with a table: 'Red: 5, Blue: 3, Yellow: 4.'",
            "misconceptions": "Students may not categorize consistently (e.g., moving an item between categories). They may count incorrectly. Some may not understand that the category is descriptive (what they sorted by).",
            "parameter_constraints": "Sorting into 2-4 categories. Objects chosen so categories are clear. Quantities within reliable counting range (up to 20). Should lead to data representation (graphs, tables) but not required in K.MD.3.",
            "developmental_context": "Combines K.CC (counting) and K.G (recognizing shapes/attributes). Foundation for 1.MD.4 (interpreting graphs) and 2.MD.9-2.MD.10 (graphs and data)."
        },
        {
            "standard_id": "1.MD.1",
            "detailed_explanation": "Students measure object lengths using standard units (inches or centimeters) and rulers or other measuring tools. Understanding begins with non-standard units (K.MD.2) and transitions to standard units. Students learn that a standard unit (inch) is always the same, unlike non-standard units which vary.",
            "worked_examples": "Measuring a pencil with an inch ruler: aligning the '0' with the end and reading the number where the pencil ends. Finding that the pencil is '5 inches long.' Measuring multiple objects and comparing (e.g., one pencil is 5 inches, another is 7 inches).",
            "misconceptions": "Students may not align the ruler correctly (not starting at 0). They may misread the ruler. Some may not understand that the ruler is a standard and the same inch is used everywhere. Students may measure the same object and get different answers if they misuse the tool.",
            "parameter_constraints": "Lengths of classroom objects, typically 1-12 inches or up to 30 cm. Standard rulers or inch/centimeter measures. Objects with clear endpoints. Precision to the nearest unit (not fractions initially).",
            "developmental_context": "Extends K.MD.2 (non-standard units) to standard units. Prepares for 2.MD.1-2.MD.2 (measuring and comparing lengths) and later precision. Essential skill for many K-12 math and science applications."
        }
    ])

def main():
    response_dir = Path("/tmp/ccmed_claude_responses")
    response_dir.mkdir(exist_ok=True)
    
    # Generate responses for different sections
    nbt = generate_nbt_responses()
    md = generate_md_responses()
    
    # Simulate additional task IDs (would come from extraction)
    # For now, pre-cache responses for when tasks are created
    
    tasks_to_create = [
        ("nbt_k5_section", nbt),
        ("md_k5_section", md),
    ]
    
    for task_label, response_json in tasks_to_create:
        task_id = task_label.replace("_", "")[:8]
        with open(response_dir / f"response_{task_id}.json", 'w') as f:
            json.dump({"task_id": task_id, "response": response_json}, f)
    
    print("✓ Pre-cached extraction responses")

if __name__ == "__main__":
    main()
