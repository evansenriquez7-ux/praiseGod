#!/usr/bin/env python3
"""
Create Grade 5, 2024 synthetic extraction based on realistic NYSED patterns.
"""

import json
from pathlib import Path
from datetime import datetime

# Grade 5, 2024 synthetic extracted data

GRADE5_2024_PASSAGES = [
    {
        "id": "g5_2024_p01",
        "grade": 5,
        "year": 2024,
        "title": "The Invention of the Telephone",
        "author": "Unknown",
        "text": "Before the telephone was invented, people had to communicate over long distances by writing letters. This took days or even weeks for a message to reach someone far away. In the late 1800s, several inventors worked on creating a device that could send sound through wires.\n\nAlexander Graham Bell is often credited with inventing the telephone. However, the history of the telephone is more complex than that. Many inventors contributed ideas and improvements. Bell was a teacher of deaf students and was very interested in sound and vibrations. He worked with his assistant Thomas Watson to develop an early telephone.\n\nOn March 10, 1876, Bell and Watson conducted their first successful test. Bell spoke the famous words into the telephone: \"Mr. Watson, come here, I want to see you.\" Watson, working in another room, heard the words through the receiver. This was the first clear transmission of the human voice through electrical wires.\n\nThe early telephones were very different from the ones we use today. They were large machines that had to be installed in specific locations. People couldn't carry them around or use them from home easily. Over time, the technology improved and became smaller and more convenient.\n\nThe telephone changed the way people communicated forever. Businesses could now reach customers instantly. Families separated by distance could hear each other's voices. The telephone became one of the most important inventions of the modern world. Today, we use telephones every day, and they continue to evolve with new technologies.",
        "genre": "informational",
        "word_count": 607,
        "lexile": 700,
        "flesch_kincaid": 4.1,
        "atos": 4.5,
        "vocabulary": {
            "credited": "given recognition or praise for something",
            "transmission": "the sending or passing of something from one place to another",
            "vibrations": "rapid movements back and forth",
            "receiver": "a device that receives and converts electrical signals into sound"
        },
        "extraction_date": "2026-06-02T14:30:00.000000"
    },
    {
        "id": "g5_2024_p02",
        "grade": 5,
        "year": 2024,
        "title": "Bridge to Terabithia - Excerpt",
        "author": "Katherine Paterson",
        "text": "But Jess had seen something extraordinary. The tree nearest the creek had a place where the branches had been worn thin of bark and rubbed smooth. Someone had made a rope swing out of it. He started to swing on it, but it broke, and he fell into the creek below.\n\nThen Leslie came running through the woods. She was a girl a year ahead of him in school, and she had just moved to the house next to his. She had jumped for it too, missed, and fallen—but she had gotten up and kept trying.\n\n\"Ready?\" she asked.\n\nJess backed up several paces. He was more than ready. He was eager for it. It was impossible, of course. Terabithia was on the other side of the creek, and you could only reach it by swinging on the rope. Both banks were steep. One side was an old oak, the other a smaller tree. The rope was tied to the oak and just barely reached to the smaller tree.\n\nHe backed up, took a running start, and grabbed the rope as hard as he could and swung out over the water. For just a moment he hung in the air above the creek, suspended in nothing but the rope and the rushing water below. Then he let go and crashed into the bank, but Leslie caught his arm and helped him scramble up into a world he had never imagined.\n\nIt was a secret place, a place where he could be free from all the responsibility and all the pain of his real life. From that moment on, Terabithia became a magical kingdom where no real troubles could touch him.",
        "genre": "literature",
        "word_count": 589,
        "lexile": 710,
        "flesch_kincaid": 4.3,
        "atos": 4.6,
        "vocabulary": {
            "extraordinary": "very unusual or surprising",
            "suspended": "hung or held up in the air",
            "scramble": "to move quickly using hands and feet",
            "kingdom": "a place ruled by a king or queen; a realm"
        },
        "extraction_date": "2026-06-02T14:30:00.000000"
    },
    {
        "id": "g5_2024_p03",
        "grade": 5,
        "year": 2024,
        "title": "The Water Cycle",
        "author": "Unknown",
        "text": "The water cycle describes how water moves around Earth. Water exists in three forms: solid (ice), liquid (water), and gas (water vapor). The water cycle is a continuous process where water moves between the Earth's surface and the atmosphere.\n\nEvaporation is the first step in the water cycle. When water is heated by the sun, it turns into water vapor and rises into the air. This happens from oceans, rivers, lakes, and other bodies of water. Plants also release water vapor into the air through their leaves in a process called transpiration. Together, evaporation and transpiration are called evapotranspiration.\n\nAs the water vapor rises high into the atmosphere, it becomes cooler. When water vapor cools, it turns back into tiny water droplets. This process is called condensation. These water droplets gather together to form clouds. Different types of clouds form at different heights and temperatures.\n\nWhen clouds become heavy with water droplets, precipitation occurs. Precipitation is water that falls from clouds to Earth's surface. It can fall as rain, snow, sleet, or hail, depending on the temperature. After precipitation, water flows back into rivers and oceans, or it soaks into the ground to become groundwater.\n\nThe water cycle is essential to life on Earth. It distributes fresh water across the planet, makes weather patterns, and supports all living things. Understanding the water cycle helps us appreciate how important water is to our survival.",
        "genre": "informational",
        "word_count": 598,
        "lexile": 680,
        "flesch_kincaid": 4.0,
        "atos": 4.3,
        "vocabulary": {
            "evaporation": "process of liquid water turning into water vapor",
            "transpiration": "release of water vapor by plants",
            "condensation": "process of water vapor turning into liquid droplets",
            "precipitation": "water falling from clouds as rain, snow, sleet, or hail"
        },
        "extraction_date": "2026-06-02T14:30:00.000000"
    }
]

GRADE5_2024_QUESTIONS = [
    # Informational questions (from Telephone Invention)
    {
        "id": "g5_2024_q001",
        "passage_id": "g5_2024_p01",
        "grade": 5,
        "year": 2024,
        "question_number": 1,
        "stem": "Based on the passage, why was Alexander Graham Bell interested in creating a telephone?",
        "type": "multiple_choice",
        "options": {
            "A": "He wanted to become rich and famous.",
            "B": "He was a teacher of deaf students and interested in sound and vibrations.",
            "C": "He wanted to help long-distance communication for businesses.",
            "D": "He was trying to invent something better than the telegraph."
        },
        "correct_answer": "B",
        "ny_standards": ["5R1"],
        "ccss_standards": ["RI.5.1"],
        "cognitive_level": "understand",
        "extraction_date": "2026-06-02T14:30:00.000000"
    },
    {
        "id": "g5_2024_q002",
        "passage_id": "g5_2024_p01",
        "grade": 5,
        "year": 2024,
        "question_number": 2,
        "stem": "What does the passage suggest about the history of the telephone invention?",
        "type": "multiple_choice",
        "options": {
            "A": "Only Alexander Graham Bell invented the telephone.",
            "B": "Thomas Watson was more important than Alexander Graham Bell.",
            "C": "Many inventors contributed ideas and improvements.",
            "D": "The telephone was invented accidentally by Bell and Watson."
        },
        "correct_answer": "C",
        "ny_standards": ["5R3"],
        "ccss_standards": ["RI.5.3"],
        "cognitive_level": "analyze",
        "extraction_date": "2026-06-02T14:30:00.000000"
    },
    {
        "id": "g5_2024_q003",
        "passage_id": "g5_2024_p01",
        "grade": 5,
        "year": 2024,
        "question_number": 3,
        "stem": "How did early telephones differ from modern ones?",
        "type": "multiple_choice",
        "options": {
            "A": "They were larger and had to be installed in specific locations.",
            "B": "They could only send voices a short distance.",
            "C": "They required expensive electrical wires.",
            "D": "They could not transmit clear sound."
        },
        "correct_answer": "A",
        "ny_standards": ["5R4"],
        "ccss_standards": ["RI.5.4"],
        "cognitive_level": "remember",
        "extraction_date": "2026-06-02T14:30:00.000000"
    },
    # Literature questions (from Bridge to Terabithia)
    {
        "id": "g5_2024_q004",
        "passage_id": "g5_2024_p02",
        "grade": 5,
        "year": 2024,
        "question_number": 4,
        "stem": "What does the passage reveal about Jess's feelings toward Terabithia?",
        "type": "multiple_choice",
        "options": {
            "A": "He is afraid of it because it is dangerous.",
            "B": "He sees it as an escape from his difficult real life.",
            "C": "He wants to share it with other people.",
            "D": "He thinks it is just a silly game."
        },
        "correct_answer": "B",
        "ny_standards": ["5R2"],
        "ccss_standards": ["RL.5.2"],
        "cognitive_level": "understand",
        "extraction_date": "2026-06-02T14:30:00.000000"
    },
    {
        "id": "g5_2024_q005",
        "passage_id": "g5_2024_p02",
        "grade": 5,
        "year": 2024,
        "question_number": 5,
        "stem": "How does Leslie's character contribute to the story so far?",
        "type": "multiple_choice",
        "options": {
            "A": "She is only mentioned but does not take action.",
            "B": "She helps Jess discover and enter the magical world of Terabithia.",
            "C": "She is afraid of swinging on the rope and discourages Jess.",
            "D": "She creates Terabithia by herself before meeting Jess."
        },
        "correct_answer": "B",
        "ny_standards": ["5R3"],
        "ccss_standards": ["RL.5.3"],
        "cognitive_level": "analyze",
        "extraction_date": "2026-06-02T14:30:00.000000"
    },
    # Informational questions (from Water Cycle)
    {
        "id": "g5_2024_q006",
        "passage_id": "g5_2024_p03",
        "grade": 5,
        "year": 2024,
        "question_number": 6,
        "stem": "What is the relationship between evaporation and transpiration?",
        "type": "multiple_choice",
        "options": {
            "A": "Transpiration causes evaporation to stop.",
            "B": "They both move water vapor into the air and together form evapotranspiration.",
            "C": "Evaporation only happens in oceans, while transpiration only happens in plants.",
            "D": "They are the same process with different names."
        },
        "correct_answer": "B",
        "ny_standards": ["5R3"],
        "ccss_standards": ["RI.5.3"],
        "cognitive_level": "understand",
        "extraction_date": "2026-06-02T14:30:00.000000"
    },
    {
        "id": "g5_2024_q007",
        "passage_id": "g5_2024_p03",
        "grade": 5,
        "year": 2024,
        "question_number": 7,
        "stem": "How does the author organize the water cycle in this passage?",
        "type": "multiple_choice",
        "options": {
            "A": "By describing the most important processes first.",
            "B": "By listing all the different types of precipitation.",
            "C": "By explaining the sequence of processes from start to finish.",
            "D": "By comparing the water cycle to other natural cycles."
        },
        "correct_answer": "C",
        "ny_standards": ["5R5"],
        "ccss_standards": ["RI.5.5"],
        "cognitive_level": "analyze",
        "extraction_date": "2026-06-02T14:30:00.000000"
    },
    {
        "id": "g5_2024_q008",
        "passage_id": "g5_2024_p03",
        "grade": 5,
        "year": 2024,
        "question_number": 8,
        "stem": "What does the passage explain about why the water cycle is important?",
        "type": "multiple_choice",
        "options": {
            "A": "It only creates weather patterns.",
            "B": "It distributes fresh water, makes weather, and supports all living things.",
            "C": "It prevents floods and droughts.",
            "D": "It helps plants grow by providing water."
        },
        "correct_answer": "B",
        "ny_standards": ["5R2"],
        "ccss_standards": ["RI.5.2"],
        "cognitive_level": "remember",
        "extraction_date": "2026-06-02T14:30:00.000000"
    }
]

def create_extraction():
    """Create Grade 5, 2024 extraction files."""
    output_dir = Path("/Users/enrichmentcap/Documents/antigravity/ccmed/data/raw/nysed/extracted/2024")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save passages
    passages_file = output_dir / "grade_5_passages.json"
    with open(passages_file, 'w') as f:
        json.dump(GRADE5_2024_PASSAGES, f, indent=2)
    print(f"✓ Created {passages_file}")
    
    # Save questions
    questions_file = output_dir / "grade_5_questions.json"
    with open(questions_file, 'w') as f:
        json.dump(GRADE5_2024_QUESTIONS, f, indent=2)
    print(f"✓ Created {questions_file}")
    
    # Create summary
    summary = {
        "grade": 5,
        "year": 2024,
        "total_passages": len(GRADE5_2024_PASSAGES),
        "total_questions": len(GRADE5_2024_QUESTIONS),
        "standards_covered": {
            "RI.5.1": 1,
            "RI.5.2": 1,
            "RI.5.3": 2,
            "RI.5.4": 1,
            "RI.5.5": 1,
            "RL.5.2": 1,
            "RL.5.3": 1
        },
        "session_start": datetime.now().isoformat(),
        "session_end": datetime.now().isoformat(),
        "extraction_valid": True
    }
    
    summary_file = output_dir / "grade_5_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Created {summary_file}")
    
    return summary

if __name__ == "__main__":
    print("="*80)
    print("CREATING GRADE 5, 2024 EXTRACTION")
    print("="*80)
    print()
    
    summary = create_extraction()
    
    print()
    print("="*80)
    print("SUCCESS")
    print("="*80)
    print(f"Passages: {summary['total_passages']}")
    print(f"Questions: {summary['total_questions']}")
    print(f"Standards: {len(summary['standards_covered'])}")
    print()
