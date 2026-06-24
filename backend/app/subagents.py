import os
import json
import uuid
import subprocess
import threading
import time
import re
from pathlib import Path
from typing import Optional


try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

import os
import json
import uuid
import threading
import time
import re
from pathlib import Path
from typing import Optional
from google import genai
from google.genai import types

_genai_client = None

class GenAIBridge:
    def __init__(self, model="gemini-2.5-flash"):
        self.model_name = model

    def prompt(self, text, temperature=None):
        global _genai_client
        if _genai_client is None:
            try:
                _genai_client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY")) if os.environ.get("GOOGLE_API_KEY") else genai.Client()
            except Exception:
                return "ERROR: GenAI SDK client failed to initialize"
        
        config_kwargs = {}
        if temperature is not None:
            config_kwargs["temperature"] = temperature
        
        try:
            response = _genai_client.models.generate_content(
                model=self.model_name,
                contents=text,
                config=types.GenerateContentConfig(**config_kwargs) if config_kwargs else None
            )
            return response.text
        except Exception as e:
            return f"ERROR: GenAI call failed: {str(e)}"

# ── Gemini bridge pool ────────────────────────────────────────────────────────
# Using the GenAIBridge now instead of subprocess-based ACPBridge

_bridge_pool: Optional["GenAIBridge"] = None
_bridge_pool_lock = threading.Lock()

def _get_bridge_pool() -> "GenAIBridge":
    global _bridge_pool
    if _bridge_pool is None:
        with _bridge_pool_lock:
            if _bridge_pool is None:
                # Direct SDK doesn't strictly need a pool, but maintaining interface compatibility
                _bridge_pool = GenAIBridge(model=_gemini_model)
    return _bridge_pool

def call_ai(prompt: str, temperature: Optional[float] = None, model: Optional[str] = None) -> str:
    """Routes the prompt through the GenAI SDK."""
    try:
        model_name = model or _get_bridge_pool().model_name
        bridge = GenAIBridge(model=model_name)
        return bridge.prompt(prompt, temperature)
    except Exception as e:
        return f"Error: GenAI SDK call failed: {str(e)}"

# ── In-memory AI routing config ───────────────────────────────────────────────

_gemini_model: str = "gemini-2.5-flash"

def set_ai_config(model: str) -> None:
    """Called by main.py at startup and on every POST /api/parent/config."""
    global _gemini_model
    
    # Ensure model is a valid Gemini model
    if not (model.startswith("gemini") or model.startswith("models/gemini")):
        model = "gemini-2.5-flash"
        
    _gemini_model = model
    print(f"[subagents] Gemini model set to: {model!r}", flush=True)
    
    global _bridge_pool
    if _bridge_pool is not None:
        _bridge_pool.model_name = model

def get_ai_config() -> tuple:
    return "gemini", _gemini_model


# ── Visual reference detection ─────────────────────────────────────────────────
# Shared with testy_grader.py — any text containing these patterns describes a
# visual element that cannot be rendered in this text-only app.

_VISUAL_PATTERNS = [
    r"\bshaded\b", r"\bshading\b",
    r"\bfigure below\b", r"\bdiagram below\b", r"\bpicture below\b", r"\bimage below\b",
    r"\bas shown\b", r"\bshown below\b", r"\blook at the\b",
    r"\bwhich of these\b", r"\bwhich picture\b", r"\bwhich image\b",
    r"\bwhich.{0,10}pictures?\b", r"\bwhich.{0,10}images?\b",
    r"\bwhich.{0,10}number lines?\b",
    r"A picture of",
    r"\buse the (figure|diagram|picture|image|model|graph|chart|table)\b",
    r"\bin the (figure|diagram|picture|image|model)\b",
    r"\bthe (figure|diagram|picture|image|model) (shows?|below|above|represents?)\b",
    r"\beach rectangle below\b", r"\beach shape below\b",
    r"\bnumber line below\b", r"\bcoordinate plane\b",
    r"\bdot (array|plot)\b", r"\barea model\b",
    r"\bfraction (bar|strip|model)\b",
    r"\bthe graph (shows?|below|above)\b",
    r"\bthe table below\b",
    r"\bthe model (shows?|below|above|represents?)\b",
    r"\bbelow (shows?|represents?|illustrates?)\b",
    r"\bthe following (figure|diagram|picture|image)\b",
]

def has_visual_reference(text: str) -> bool:
    """Return True if text references a visual element that doesn't exist in the app."""
    for pattern in _VISUAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False




def _format_age_grade_constraints(student_age: int, student_grade: int, language: str = "en", context: str = "question") -> str:
    """
    Build an explicit age/grade-appropriate language constraints block.
    `context` can be "question" (for generators) or "tutor" (for socratic tutor).
    `language` is the student's active language preference ("en" or "tl").

    This block is injected when the OpenCode backend is active to ensure the model
    produces developmentally appropriate text instead of defaulting to adult language.
    """
    is_tagalog = language.lower() == "tl"
    lang_label = "Tagalog (Filipino)" if is_tagalog else "English"

    if context == "tutor":
        intro = (
            f"This student is {student_age} years old in Grade {student_grade}. "
            f"Your replies MUST be written in {lang_label} at a level this child can easily understand."
        )
    else:
        intro = (
            f"This student is {student_age} years old in Grade {student_grade}. "
            f"ALL text you produce (stem, options, explanation) MUST be written in {lang_label} at this developmental level."
        )

    # Language-specific vocabulary guidance
    if is_tagalog:
        vocab_rules = """Strict vocabulary and complexity rules by grade band (ALL OUTPUT IN TAGALOG):
- Kindergarten & Grade 1 (ages 5-7): ONLY basic, everyday Tagalog words a Filipino 5-7 year old knows (aso, pusa, tatay, nanay, takbo, malaki, maliit, tulong, araw, bahay, tubig, kain). Maximum 1-2 ultra-short sentences (under 15-20 words total). NO English loanwords. NO multi-syllable formal Filipino. NO abstract concepts. NO words like "kalkulahin", "tukuyin", "kinakatawan", "magpasya".
- Grades 2-3 (ages 7-9): Simple Tagalog sentences with common everyday words. Maximum 1 short paragraph (3-4 sentences). Use "hanapin", "ipakita", "pareho" instead of formal terms. Avoid academic Filipino like "kalkulahin", "ipakita ang katibayan", "katumbas".
- Grades 4-5 (ages 9-11): Accessible everyday Tagalog. Slightly longer passages OK but keep sentences clear. Can introduce academic Tagalog terms if age-appropriate for Filipino elementary students.
- Grades 6-8 (ages 11-14): Grade-appropriate Filipino with some academic vocabulary. Can use formal Filipino where natural.
- Grades 9-12 (ages 14-18): Full academic Filipino appropriate for high school."""
    else:
        vocab_rules = """Strict vocabulary and complexity rules by grade band (ALL OUTPUT IN ENGLISH):
- Kindergarten & Grade 1 (ages 5-7): ONLY high-frequency sight words (cat, dog, run, big, help, sun, mom, dad). Maximum 1-2 ultra-short sentences (under 15-20 words total). NO multi-syllable words. NO abstract concepts. NO words like "determine", "represent", "analyze", "dribbling", "decides", "afternoon".
- Grades 2-3 (ages 7-9): Simple sentences with common everyday vocabulary. Maximum 1 short paragraph (3-4 sentences). Avoid words like "calculate", "determine", "demonstrate", "equivalent". Use "find", "show", "same as" instead.
- Grades 4-5 (ages 9-11): Accessible elementary vocabulary. Slightly longer passages OK but keep sentences clear and direct. Can introduce math terms if they've been taught at this level.
- Grades 6-8 (ages 11-14): Middle school reading level. Can use grade-appropriate academic vocabulary with context.
- Grades 9-12 (ages 14-18): High school level. Full academic language appropriate."""

    block = f"""
=== AGE-APPROPRIATE LANGUAGE CONSTRAINTS (CRITICAL) ===
{intro}

{vocab_rules}

ALL output MUST be in {lang_label}. DO NOT default to adult-level vocabulary, complex sentence structures, or abstract phrasing. Write as if speaking directly to a {student_age}-year-old {'Filipino ' if is_tagalog else ''}child in {lang_label}.
========================================================
"""
    return block


# --- Specialized Subagents ---

def narrate_question_subagent(
    math_expression: str,
    stem_template: str,
    options: dict,
    student_interest: str,
    language: str,
    student_age: int,
    student_grade: int,
    skill_id: Optional[str] = None
) -> dict:
    """
    Problem Narrator Subagent: Wraps the math skeleton in high-interest narratives
    matching age, language, and interests (e.g. basketball and the bible).
    """
    lang_name = "Tagalog (Filipino)" if language.lower() == "tl" else "English"
    
    prompt = f"""
You are the Problem Narrator subagent for an adaptive learning platform. Your task is to wrap a mathematical question into a narrative word problem matching the student's interests and age.

Student Profile:
- Age: {student_age} years old
- Grade: Grade {student_grade}
- Interests: {student_interest} (e.g., the Bible, History)
- Output Language: {lang_name}
"""

    prompt += _format_age_grade_constraints(student_age, student_grade, language=language, context="question")

    prompt += f"""
Mathematical Skeleton:
- Math Expression: {math_expression}
- Stem Template: {stem_template}
- Numeric Options (STRICTLY PRESERVE THESE KEYS):
  A: {options['A']['value']}
  B: {options['B']['value']}
  C: {options['C']['value']}
  D: {options['D']['value']}

Your narrative story MUST:
1. Incorporate the numbers and operation from the mathematical expression exactly.
2. EXTREME VARIABILITY & ENGAGEMENT: Ignore any generic nouns in the stem template (like "items"). You MUST invent a completely unique, highly creative scenario every time, grounded in the student's interests. Explore a vast range of different actions, topics, and settings (e.g. if the interest is 'Bible', don't just use Noah's Ark; explore specific miracles, historical architecture, or parables). Do not repeat previous setups.
3. The narrative difficulty and vocabulary MUST strictly match the student's age ({student_age} years old) and Grade level (Grade {student_grade}):
   - For Kindergarten (Grade 0) & Grade 1: The narrative MUST be extremely brief (maximum 1-2 simple sentences, under 15-20 words total). Use only concrete, high-frequency sight words and basic CVC words (like "cat", "dog", "run", "big", "sun", "glad", "help"). NEVER use complex or advanced terms like "dribbling", "Goliath", "decides", "practice", "afternoon". The options and explanation must be extremely brief and simple.
   - For Elementary (Grades 2-5): Keep the narrative to 1 short paragraph (3-4 simple sentences) with accessible elementary vocabulary.
   - For Middle/High School: Suitable age-appropriate reading and reasoning complexity.
4. IMPORTANT: In your "options" JSON field, the text for key "A" MUST correspond to the value {options['A']['value']}, "B" to {options['B']['value']}, and so on. Do NOT swap them.
5. Output a valid, clean JSON object. Do NOT wrap it in markdown block tags (no ```json).

Output JSON Schema:
{{
  "stem": "engaging narrative word problem text in {lang_name}",
  "options": {{
    "A": "thematic text for option A (must include the value {options['A']['value']})",
    "B": "thematic text for option B (must include the value {options['B']['value']})",
    "C": "thematic text for option C (must include the value {options['C']['value']})",
    "D": "thematic text for option D (must include the value {options['D']['value']})"
  }},
  "explanation": "A thematic step-by-step mathematical explanation of the correct solution in {lang_name}"
}}
"""
    response = call_ai(prompt, temperature=1.0)

    # Sanitize markdown formatting from response if returned
    response_clean = response.strip()
    if response_clean.startswith("```json"):
        response_clean = response_clean[7:]
    if response_clean.endswith("```"):
        response_clean = response_clean[:-3]
    response_clean = response_clean.strip()
    
    try:
        parsed = json.loads(response_clean)
        # Verify schema integrity
        if "stem" in parsed and "options" in parsed and "explanation" in parsed:
            # Overwrite options in skeleton with generated narrative strings
            for key in ["A", "B", "C", "D"]:
                options[key]["text"] = parsed["options"].get(key, options[key]["value"])
            return {
                "stem": parsed["stem"],
                "explanation": parsed["explanation"],
                "options": options
            }
        else:
            raise KeyError("Missing core keys in generated JSON")
    except Exception as e:
        print(f"Failed to parse narrated question from subagent: {str(e)}. Raw response: {response}")
        # Fallback to default skeleton
        for key in ["A", "B", "C", "D"]:
            options[key]["text"] = f"Value: {options[key]['value']}"
        return {
            "stem": f"Calculate the following math expression: {math_expression}",
            "explanation": f"The correct answer is {options['A']['value']} (if correct key is A). Simple fraction or arithmetic resolution.",
            "options": options
        }


def generate_math_question_ai(
    skill_id: str,
    grade_level: int,
    student_interest: str,
    language: str,
    student_age: int,
    previous_questions: list = None,
) -> dict:
    """
    AI fallback for Math question generation.

    Used when:
      1. SymPy exhausts variety for a standard (all stems already seen this session)
      2. SymPy generates a visual-reference question for a standard

    Produces a text-only MCQ testing the same CCSS standard.
    Returns a skeleton dict compatible with QuestionResponse building.

    skeleton_id uses 'ai_' prefix — the grader checks this prefix and looks up
    the skeleton from MATH_AI_CACHE instead of reconstructing from SymPy.
    """
    lang_name = "Tagalog (Filipino)" if language.lower() == "tl" else "English"

    standard_description = f"Grade {grade_level} Math standard {skill_id}"

    prompt = f"""You are a Math Curriculum Subagent for an adaptive K-12 platform.
Generate ONE multiple-choice math question testing the given standard.

Student Profile:
- Age: {student_age} years old
- Grade: Grade {grade_level}
- Interests: {student_interest}
- Output Language: {lang_name}

Math Standard:
- Code: {skill_id}
- Description: "{standard_description}"
"""

    prompt += _format_age_grade_constraints(student_age, grade_level, language=language, context="question")

    if previous_questions:
        pn = len(previous_questions)
        prompt += (
            f"\n\nALREADY SEEN BY THIS STUDENT ({pn}) — "
            "DO NOT repeat or closely resemble:\n"
        )
        for i, q in enumerate(previous_questions, 1):
            prompt += f"\n  [Q{i}] {q.get('problem_text', '')[:120]}\n"
        prompt += "\nChoose a completely different context, numbers, and question angle.\n"

    prompt += f"""
STRICT RULES:
1. Text-only. NO images, NO diagrams, NO "which of these" (implies visual), NO "shown below".
2. Exactly 4 options (A, B, C, D). One unambiguously correct.
3. Question must be answerable from the text alone — no external visuals needed.
4. Grade {grade_level} / Age {student_age} appropriate language.
5. Output ONLY a valid JSON object. No markdown fences.

Output schema:
{{
  "stem_template": "The full question text...",
  "options": {{
    "A": {{"value": "..."}},
    "B": {{"value": "..."}},
    "C": {{"value": "..."}},
    "D": {{"value": "..."}}
  }},
  "correct_key": "B",
  "correct_answer": "Exact text of correct option"
}}"""

    response = call_ai(prompt)
    resp = response.strip()
    for fence in ("```json", "```"):
        if resp.startswith(fence):
            resp = resp[len(fence):]
        if resp.endswith("```"):
            resp = resp[:-3]
    resp = resp.strip()

    try:
        parsed = json.loads(resp)
        parsed["skeleton_id"]    = f"ai_{uuid.uuid4().hex[:8]}"
        parsed["question_mode"]  = "mcq"
        parsed["math_expression"] = f"ai_gen:{skill_id}"
        # Ensure options have a 'value' key (normalise any flat-string options)
        for k in ["A", "B", "C", "D"]:
            opt = parsed.get("options", {}).get(k, {})
            if isinstance(opt, str):
                parsed["options"][k] = {"value": opt}
            elif "value" not in opt:
                parsed["options"][k]["value"] = str(opt)
        return parsed
    except Exception as e:
        print(f"[Math AI Fallback] Failed to parse response: {e}. Raw: {resp[:200]}")
        # Last-resort fallback skeleton
        return {
            "skeleton_id":    f"ai_{uuid.uuid4().hex[:8]}",
            "stem_template":  f"What does the standard {skill_id} ask students to practice?",
            "options":        {
                "A": {"value": "Addition"},
                "B": {"value": "Subtraction"},
                "C": {"value": "Multiplication"},
                "D": {"value": "Division"},
            },
            "correct_key":    "A",
            "correct_answer": "Addition",
            "question_mode":  "mcq",
            "math_expression": f"ai_gen:{skill_id}",
        }


def socratic_tutor_subagent(
    skill_id: str,
    stem: str,
    correct_answer,        # kept for signature compat but NEVER injected into prompt
    selected_answer: str,
    trap_name: str,
    chat_history: list,
    language: str,
    student_interest: str,
    student_age: int,
    student_grade: int,
    is_intro: bool = False,
) -> dict:
    """
    Socratic Tutor Subagent: Guide students to discover their mistakes on their own
    using structured dialogue and their core interest themes: {student_interest}.
    """
    if len(chat_history) == 0 or len(chat_history) == 1:
        if is_intro:
            fallback_msg = "Praise God and the Lord Jesus Christ, I'm your tutor today. How can I help you with this lesson?" if language.lower() != "tl" else "Purihin ang Diyos at ang Panginoong Hesukristo, ako ang iyong tutor ngayon. Paano kita matutulungan sa araling ito?"
        else:
            fallback_msg = "Praise God and the Lord Jesus Christ, I'm your tutor today. Let's analyze your answer together!" if language.lower() != "tl" else "Purihin ang Diyos at ang Panginoong Hesukristo, ako ang iyong tutor ngayon. Suriin natin ang iyong sagot nang sabay!"
        return {
            "reply": fallback_msg,
            "resolved": False
        }

    lang_name = "Tagalog" if language.lower() == "tl" else "English"
    
    # Detect subject track from skill_id
    subject_display = "Math"
    subject_type = "problem"
    concept_type = "mathematical"
    if skill_id.startswith("RL"):
        subject_display = "Reading Literature"
        subject_type = "reading passage question"
        concept_type = "reading comprehension & analysis"
    elif skill_id.startswith("RI"):
        subject_display = "Reading Informational Text"
        subject_type = "reading informational passage question"
        concept_type = "informational text comprehension"
    elif skill_id.startswith("RF"):
        subject_display = "Foundational Reading"
        subject_type = "foundational reading question"
        concept_type = "reading foundational skills"
    elif skill_id.startswith("SL"):
        subject_display = "Speaking & Listening"
        subject_type = "speaking & listening standard"
        concept_type = "verbal interaction & presentation"
    elif skill_id.startswith("W"):
        subject_display = "Writing"
        subject_type = "writing prompt or standard"
        concept_type = "composition & editing"
    elif skill_id.startswith("L"):
        subject_display = "Language & Grammar Mechanics"
        subject_type = "grammar question"
        concept_type = "language & grammar usage"

    # Format chat history
    formatted_history = ""
    for msg in chat_history:
        # Check if msg is a dict or an object
        if isinstance(msg, dict):
            role_val = msg.get("role")
            content_val = msg.get("content")
        else:
            role_val = getattr(msg, "role", "user")
            content_val = getattr(msg, "content", "")
            
        role = "Student" if role_val == "user" else "Tutor"
        formatted_history += f"{role}: {content_val}\n"
        
    context_block = (
        f"The student is reading intro lesson content for skill {skill_id}.\n"
        f"Current lesson being shown: '{stem}'"
    ) if is_intro else (
        f"- Question the student sees: '{stem}'\n"
        f"- What the student answered: {selected_answer}"
    )

    prompt = f"""
You are a warm, encouraging Socratic Tutor for a {student_age}-year-old Grade {student_grade} student.
Subject standard: {skill_id} ({subject_display})
Output language: {lang_name}
Student interests: {student_interest}

Problem Context:
{context_block}

Your Objectives:
1. NEVER reveal, hint at, or confirm the correct answer, even if the student asks directly.
   - If asked for the answer, redirect with a guiding question instead.
   - CRITICAL: Do NOT say things like "the answer is...", "that's correct", or confirm any specific value as right.
2. Guide the student to discover the answer themselves using the Socratic method — ask questions that help them reason step by step.
3. When the student asks a conceptual "what is" or "how to" question, explain it clearly using warm analogies related to {student_interest}.
4. Keep responses warm, supportive, and under 3-4 sentences (excluding ASCII art).
5. You MUST actively use ASCII art and emojis in your responses to visually engage the student when beneficial and appropriate for their grade level. DO NOT hesitate to use ASCII art.
6. Respond ONLY in {lang_name}.
7. Output a JSON object:
   - "reply": your Socratic reply text
   - "resolved": true only if the student has clearly arrived at the correct reasoning on their own (do NOT set true just because they stated a value — only when they show genuine understanding)

Chat History:
{formatted_history}

Output ONLY raw JSON. No markdown blocks.
CRITICAL: If you use ASCII art or any backslashes, you MUST properly escape them (use \\\\ for a single backslash, and \\n for newlines) so the response remains valid parseable JSON.
"""
    # When OpenCode is the active backend, inject age-appropriate language constraints
    if True:
        prompt += _format_age_grade_constraints(student_age, student_grade, language=language, context="tutor")

    response = call_ai(prompt, model="gemma-4-31b-it")

    response_clean = response.strip()
    if response_clean.startswith("```json"):
        response_clean = response_clean[7:]
    if response_clean.endswith("```"):
        response_clean = response_clean[:-3]
    response_clean = response_clean.strip()
    
    try:
        parsed = json.loads(response_clean)
        return {
            "reply": parsed.get("reply", "Paki-check ang iyong solusyon sa basketball court! Susubukan nating muli."),
            "resolved": parsed.get("resolved", False)
        }
    except Exception as e:
        print(f"[socratic_tutor_subagent] JSON parsing failed: {e}\nRaw response: {response_clean}", flush=True)
        fallback_msg = "Praise God and the Lord Jesus Christ, I'm your tutor today. How can I help you?" if language == "en" else "Purihin ang Diyos at ang Panginoong Hesukristo, ako ang iyong tutor ngayon. Paano kita matutulungan?"
        return {
            "reply": fallback_msg,
            "resolved": False
        }

def generate_ela_skeleton_subagent(
    skill_id: str,
    grade_level: int,
    student_interest: str,
    language: str,
    student_age: int,
    question_mode: str = "mcq",        # "mcq" or "writing_prompt"
    previous_questions: list = None,   # full question dicts already answered — must not repeat
) -> dict:
    """
    ELA Subagent: Generates reading comprehension (MCQ) or open-ended writing prompts.
    Grounds questions in official CCSS standard descriptions via ela_loader.
    """
    lang_name = "Tagalog (Filipino)" if language.lower() == "tl" else "English"

    # Load the official CCSS standard description from local JSON
    std_info = ela_loader.load_ela_standard(skill_id, grade_level)
    standard_description = std_info.get("description", f"Grade {grade_level} ELA standard {skill_id}")
    domain = std_info.get("domain", "English Language Arts")



    prompt = f"""
You are the ELA Reading Curriculum Subagent for an adaptive K-12 platform.
Generate a short reading passage and multiple-choice question testing the given standard.

Student Profile:
- Age: {student_age} years old
- Grade: Grade {grade_level}
- Interests: {student_interest}
- Target Language: {lang_name}

ELA Standard:
- Code: {skill_id}
- Domain: {domain}
- Official Description: "{standard_description}"
"""
    prompt += _format_age_grade_constraints(student_age, grade_level, language=language, context="question")

    if previous_questions:
        n = len(previous_questions)
        prompt += (
            f"\n\nALREADY ANSWERED BY THIS STUDENT "
            f"({n} question{'s' if n > 1 else ''}) — "
            "DO NOT repeat or closely resemble any of these:\n"
        )
        for i, q in enumerate(previous_questions, 1):
            prompt += f"\n  [Question {i}]\n"
            for line in q.get("problem_text", "").splitlines():
                prompt += f"  {line}\n"
            if q.get("answer"):
                prompt += f"  Answer: {q['answer']}\n"
        prompt += (
            "\nYour new passage and question MUST use a completely different "
            "real-world context, scenario, and subject matter. "
            "The CCSS standard being assessed must remain identical.\n"
        )

    prompt += f"""
Instructions:
1. Write a short engaging passage themed around the student's interests. The length, vocabulary, and syntactic complexity MUST strictly match the student's age ({student_age} years old) and Grade level (Grade {grade_level}):
   - For Kindergarten (Grade 0) & Grade 1: The passage MUST be ONLY 1 or 2 ultra-simple sentences (maximum 15-20 words total). Use only concrete, high-frequency sight words and basic CVC words (like "cat", "dog", "run", "big", "sun", "glad", "help"). NEVER use multi-syllable, abstract, or advanced vocabulary (like "diligent", "sewing", "neighbors", "circumstances"). The question and options must also be extremely brief and simple.
   - For Elementary (Grades 2-5): The passage must be 1 short paragraph (3-5 simple sentences). Use accessible elementary vocabulary.
   - For Middle & High School (Grades 6-13): The passage can be 1-2 paragraphs with age-appropriate complexity.
2. EXTREME VARIABILITY & ENGAGEMENT: To keep students maximally engaged, you MUST explore a vast range of different actions, topics, and scenarios within the student's interests. 
   - Avoid repetitive setups (e.g., if the interest is 'Bible', don't just do 'Noah and the Ark' or 'David the Shepherd' repeatedly). 
   - Instead, explore unique parables, historical biblical architectural measurements, specific miracles, or modern-day scenarios illustrating biblical values. 
   - If the interest is 'Basketball', explore different aspects like specific training drills, buzzer-beater physics, historical game moments, or team psychology.
   - The actions and context MUST change every time. Different names and numbers are NOT enough.
3. Formulate ONE clear question that directly tests the standard above.
4. Provide exactly 4 options (A, B, C, D). One must be unambiguously correct.
   - For grammar, usage, and conventions questions: Ensure that the correct option is the ONLY one that is grammatically correct and resolves the error. All 3 distractor/trap options must remain grammatically incorrect (e.g. keeping the original error, or introducing another clear grammatical error). Do NOT generate multiple options that are grammatically correct.
5. Place the question AFTER the passage in the stem_template field.
6. Do NOT wrap output in markdown blocks.

Output JSON Schema:
{{
  "stem_template": "The passage text...\\n\\nQuestion: What does the author mean when...",
  "options": {{
    "A": {{"value": "Option A text"}},
    "B": {{"value": "Option B text"}},
    "C": {{"value": "Option C text"}},
    "D": {{"value": "Option D text"}}
  }},
  "correct_key": "B",
  "correct_answer": "The exact text of the correct option",
  "math_expression": "Reading Comprehension: {skill_id}",
  "standard_description": "{standard_description}",
  "domain": "{domain}"
}}
"""

    last_error = None
    last_response = None
    for _attempt in range(3):
        last_response = call_ai(prompt)

        response_clean = last_response.strip()
        if response_clean.startswith("```json"):
            response_clean = response_clean[7:]
        if response_clean.endswith("```"):
            response_clean = response_clean[:-3]
        response_clean = response_clean.strip()

        try:
            parsed = json.loads(response_clean)
            # Post-generation visual reference backstop
            if has_visual_reference(parsed.get("stem_template", "")):
                print(f"[ELA Generator] Attempt {_attempt+1}/3: visual reference in stem — retrying")
                last_error = ValueError("Visual reference in generated stem")
                continue
            parsed["skeleton_id"] = f"ela_{uuid.uuid4().hex[:8]}"
            parsed["question_mode"] = question_mode
            parsed["standard_description"] = standard_description
            parsed["domain"] = domain
            return parsed
        except Exception as e:
            last_error = e
            print(f"[ELA Generator] Attempt {_attempt+1}/3 failed: {e}. Retrying...")

    # All 3 attempts failed — serve last-resort fallback
    print(f"Failed to parse ELA skeleton after 3 attempts: {last_error}. Raw response: {last_response}")
    return {
        "skeleton_id": f"ela_fallback_{uuid.uuid4().hex[:8]}",
        "stem_template": "Read the following sentence: The quick brown fox jumps over the lazy dog.\n\nWhat is the subject of this sentence?",
        "options": {
            "A": {"value": "fox"},
            "B": {"value": "dog"},
            "C": {"value": "jumps"},
            "D": {"value": "brown"}
        },
        "correct_key": "A",
        "correct_answer": "fox",
        "math_expression": "Reading Comprehension",
        "question_mode": "mcq",
        "standard_description": standard_description,
        "domain": domain
    }


def generate_ela_batch_subagent(
    skill_id: str,
    grade_level: int,
    student_interest: str,
    language: str,
    student_age: int,
    n: int = 2,
    question_mode: str = "mcq",
    previous_questions: list = None,
) -> list:
    """
    Generate `n` additional ELA questions for `skill_id` in a SINGLE LLM call.
    Because all `n` questions are produced together, the model can self-diversify —
    guaranteeing they share no passage, scenario, or context.

    `previous_questions` should include both the session history AND Q1 (already
    generated individually) so Q2..Qn avoid repeating any of them.

    Returns a list of `n` parsed skeleton dicts, each with a unique skeleton_id.
    Falls back to individual `generate_ela_skeleton_subagent()` calls for any
    entries that fail to parse.
    """
    lang_name = "Tagalog (Filipino)" if language.lower() == "tl" else "English"

    std_info = ela_loader.load_ela_standard(skill_id, grade_level)
    standard_description = std_info.get("description", f"Grade {grade_level} ELA standard {skill_id}")
    domain = std_info.get("domain", "English Language Arts")



    prompt = f"""You are the ELA Curriculum Subagent for an adaptive K-12 platform.
Generate exactly {n} COMPLETELY DIFFERENT reading comprehension questions,
all testing the SAME standard.

Student Profile:
- Age: {student_age} years old
- Grade: Grade {grade_level}
- Interests: {student_interest}
- Output Language: {lang_name}

ELA Standard:
- Code: {skill_id}
- Domain: {domain}
- Official Description: "{standard_description}"
"""

    prompt += _format_age_grade_constraints(student_age, grade_level, language=language, context="question")

    if previous_questions:
        pn = len(previous_questions)
        prompt += (
            f"\n\nALREADY ANSWERED BY THIS STUDENT OR ALREADY IN THIS BATCH "
            f"({pn} question{'s' if pn > 1 else ''}) — "
            "DO NOT repeat or closely resemble any of these:\n"
        )
        for i, q in enumerate(previous_questions, 1):
            prompt += f"\n  [Question {i}]\n"
            for line in q.get("problem_text", "").splitlines():
                prompt += f"  {line}\n"
            if q.get("answer"):
                prompt += f"  Answer: {q['answer']}\n"
        prompt += (
            "\nEach new question MUST use a completely different real-world context, "
            "scenario, and subject matter.\n"
        )

    prompt += f"""
CRITICAL DIVERSITY RULE: The {n} questions MUST NOT share any passage, scenario,
context, character, or setting. A student who reads Q1 gains ZERO advantage on Q2 or Q3.

Each question must follow this format:
- A short passage (length appropriate for Grade {grade_level}, interests: {student_interest})
- One clear multiple-choice question testing: "{standard_description}"
- Exactly 4 options (A, B, C, D); one unambiguously correct

Output a JSON ARRAY of exactly {n} objects. No markdown fences. No extra text.
[
  {{
    "stem_template": "Passage text...\\n\\nQuestion: ...",
    "options": {{
      "A": {{"value": "..."}},
      "B": {{"value": "..."}},
      "C": {{"value": "..."}},
      "D": {{"value": "..."}}
    }},
    "correct_key": "B",
    "correct_answer": "Exact text of correct option",
    "standard_description": "{standard_description}",
    "domain": "{domain}"
  }},
  {{ ... }},
  {{ ... }}
]"""

    response = call_ai(prompt)

    # Strip markdown fences if present
    resp = response.strip()
    for fence in ("```json", "```"):
        if resp.startswith(fence):
            resp = resp[len(fence):]
        if resp.endswith("```"):
            resp = resp[:-3]
    resp = resp.strip()

    # Parse the array
    results = []
    try:
        parsed = json.loads(resp)
        if not isinstance(parsed, list):
            raise ValueError("Expected JSON array")
        for entry in parsed[:n]:
            # Visual reference backstop — treat flagged entries as parse failures
            if has_visual_reference(entry.get("stem_template", "")):
                print(f"[ELA Batch] Visual reference detected in entry, skipping to fallback")
                continue
            entry["skeleton_id"] = f"ela_{uuid.uuid4().hex[:8]}"
            entry["question_mode"] = question_mode
            entry["standard_description"] = standard_description
            entry["domain"] = domain
            results.append(entry)
    except Exception as e:
        print(f"[ELA Batch] Failed to parse batch response: {e}. Raw: {resp[:300]}")

    # Fill any missing slots with individual fallback calls
    while len(results) < n:
        slot = len(results) + 1
        print(f"[ELA Batch] Falling back to individual generation for slot {slot}")
        try:
            fb = generate_ela_skeleton_subagent(
                skill_id=skill_id,
                grade_level=grade_level,
                student_interest=student_interest,
                language=language,
                student_age=student_age,
                question_mode=question_mode,
                previous_questions=previous_questions,
            )
            results.append(fb)
        except Exception as fe:
            print(f"[ELA Batch] Fallback also failed for slot {slot}: {fe}")
            break

    return results


