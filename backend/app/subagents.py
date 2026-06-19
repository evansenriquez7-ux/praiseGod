import os
import json
import uuid
import subprocess
import threading
import time
import re
from pathlib import Path
from typing import Optional
# from backend.app import ela_loader

class DummyElaLoader:
    @staticmethod
    def load_ela_standard(skill_id, grade_level):
        return {"code": skill_id, "description": "Dummy CCSS Standard Description", "domain": "Dummy ELA Domain", "grade_level": grade_level}
ela_loader = DummyElaLoader()

# ── By-standard node directory (processed curriculum data) ─────────────────────
_BY_STANDARD_DIR = Path(__file__).parent.parent.parent / "data" / "processed" / "by_standard"

# ── by_standard node directory ─────────────────────────────────────────────────
_BY_STANDARD_DIR = Path(__file__).parent.parent.parent / "data" / "processed" / "by_standard"

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
                _bridge_pool = GenAIBridge(model=_opencode_model)
    return _bridge_pool

def call_gemini_cli(prompt: str, temperature: Optional[float] = None) -> str:
    """Routes the prompt through the GenAI SDK."""
    try:
        return _get_bridge_pool().prompt(prompt, temperature)
    except Exception as e:
        return f"Error: GenAI SDK call failed: {str(e)}"

# ... (rest of the file remains largely the same) ...


# ── OpenCode chat bridge (synchronous) ────────────────────────────────────────

# Pre-approved temp directory — isolated from the repo so any files OpenCode
# decides to write as a side-effect never land in the working tree.
_OC_WORK_DIR = "/var/folders/db/v4l6qxx55vs19dxhbjs6cx_w0000gn/T/opencode"

# Prefix injected before every plain-chat prompt to suppress file-write tool use.
_NO_FILE_WRITE_PREFIX = (
    "CRITICAL INSTRUCTION: You are operating in text-only output mode. "
    "Output ONLY plain text or a JSON object in your response. "
    "Do NOT write any files. Do NOT use any file-write tools. "
    "Do NOT create or modify files on disk. Return your answer as text only.\n\n"
)

def call_opencode_cli(prompt: str, model: str, timeout: int = 120) -> str:
    """
    Calls OpenCode for a plain-text completion (no agent).
    Uses `opencode run --model <model> --format json` and parses the JSON event
    stream to extract the final assistant message text.

    Runs in a sandboxed temp directory so any accidental file writes by the
    model never land in the repo working tree.

    Retries once on transient "Model not found" errors with a brief delay.
    """
    import shutil
    import time
    from collections import defaultdict
    from pathlib import Path
    import os

    opencode_bin = shutil.which("opencode") or str(Path.home() / ".opencode" / "bin" / "opencode")

    # Ensure the isolated work directory exists
    os.makedirs(_OC_WORK_DIR, exist_ok=True)

    safe_prompt = _NO_FILE_WRITE_PREFIX + prompt

    def _run_once(model_name: str) -> str:
        try:
            result = subprocess.run(
                [
                    opencode_bin,
                    "run",
                    "--model", model_name,
                    "--format", "json",
                    "--dangerously-skip-permissions",
                    safe_prompt,
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=_OC_WORK_DIR,
            )
        except subprocess.TimeoutExpired:
            return f"Error: OpenCode call timed out after {timeout}s"
        except Exception as e:
            return f"Error: OpenCode call failed: {e}"

        # Parse the JSON event stream
        message_texts: dict = defaultdict(str)
        message_order: list = []

        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "text":
                part = ev.get("part", {})
                msg_id = part.get("messageID", "unknown")
                chunk = part.get("text", "")
                if chunk:
                    if msg_id not in message_texts:
                        message_order.append(msg_id)
                    message_texts[msg_id] += chunk
            elif ev.get("type") == "error":
                err = ev.get("error", {})
                msg = err.get("data", {}).get("message", str(err))
                return f"Error: OpenCode agent error: {msg}"

        if message_order:
            return message_texts[message_order[-1]]
        return f"Error: OpenCode returned no text (stderr: {result.stderr[:300]})"

    # First attempt with the exact model name from the dropdown
    response = _run_once(model)

    # If we get a "Model not found" error, retry once after a brief delay
    # (handles transient availability issues)
    if "Model not found" in response:
        print(f"[OpenCode CLI] Model not found on first try: {model!r}. Retrying in 2s...", flush=True)
        time.sleep(2)
        response = _run_once(model)
        if "Model not found" in response:
            print(f"[OpenCode CLI] Model still not found after retry: {model!r}", flush=True)

    return response

# ── In-memory AI routing config ───────────────────────────────────────────────

_ai_backend: str = "gemini"
_opencode_model: str = "gemini-2.5-flash"

def set_ai_config(model: str) -> None:
    """Called by main.py at startup and on every POST /api/parent/config."""
    global _ai_backend, _opencode_model
    _ai_backend = "gemini"
    
    # Force valid Gemini model, ignoring any lingering OpenCode or Gemma references in DB
    if "opencode" in model or "gemma" in model or "deepseek" in model:
        model = "gemini-2.5-flash"
        
    _opencode_model = model
    print(f"[subagents] Gemini model set to: {model!r}", flush=True)
    
    global _bridge_pool
    if _bridge_pool is not None:
        _bridge_pool.model_name = model

def get_ai_config() -> tuple:
    return _ai_backend, _opencode_model

def call_ai(prompt: str, temperature: Optional[float] = None) -> str:
    """
    Thin router: directs the prompt to either the Gemini ACP bridge pool
    or an OpenCode subprocess based on the parent-configured backend.
    """
    if _ai_backend == "opencode":
        print(f"[call_ai] Using OpenCode model: {_opencode_model}", flush=True)
        return call_opencode_cli(prompt, _opencode_model)
    return call_gemini_cli(prompt, temperature)

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


# ── by_standard context loader ─────────────────────────────────────────────────

def _find_by_standard_file(skill_id: str):
    """
    Resolve a CCSS standard code to its by_standard JSON file.
    Tries three strategies, mirroring scripts/testy.py:
      1. Direct dot format:       RL.3.1.json
      2. Underscore format:       3_OA_A_1.json  (dots + hyphens → underscores)
      3. Case-insensitive glob fallback (strips all separators for comparison)
    Returns a Path on hit, None on miss.
    """
    # Strategy 1 — dot format (ELA standards)
    dot_path = _BY_STANDARD_DIR / f"{skill_id}.json"
    if dot_path.exists():
        return dot_path

    # Strategy 2 — underscore format (Math standards)
    us_name = skill_id.replace(".", "_").replace("-", "_") + ".json"
    us_path = _BY_STANDARD_DIR / us_name
    if us_path.exists():
        return us_path

    # Strategy 3 — case-insensitive glob (handles capitalisation differences)
    def _norm(s: str) -> str:
        return re.sub(r"[.\-_]", "", s.lower())

    target = _norm(skill_id)
    try:
        for f in _BY_STANDARD_DIR.glob("*.json"):
            if _norm(f.stem) == target:
                return f
    except Exception:
        pass

    return None


def _load_by_standard_context(skill_id: str) -> dict:
    """
    Load enrichment data from the by_standard node JSON file for `skill_id`.

    IMPORTANT: Only extracts student-facing content (example problems, question
    stems, answer choices).  Strips all metadata (curriculum references, URLs,
    source IDs, image/video placeholders, teacher instructions, standard codes).

    Returns a dict:
      {
        "description": str,        (the standard's pedagogical skill description)
        "grade_label":  str,       e.g. "Grade 3" or "Kindergarten"
        "subject":      str,
        "examples":     list[{"question": str, "answer": str}]  (up to 3)
      }
    Returns {} silently if the file doesn't exist or any error occurs.
    """
    try:
        std_file = _find_by_standard_file(skill_id)
        if std_file is None:
            return {}

        with open(std_file, encoding="utf-8") as f:
            data = json.load(f)

        description = data.get("standard_description", "").strip()
        grade_raw   = data.get("grade_level", "")
        subject     = data.get("subject", "").strip()

        try:
            grade_int   = int(grade_raw)
            grade_label = "Kindergarten" if grade_int == 0 else f"Grade {grade_int}"
        except (ValueError, TypeError):
            grade_label = f"Grade {grade_raw}" if grade_raw else ""

        # Extract up to 3 example problems ─────────────────────────────────
        examples = []

        # Priority 1: NYSED released items — cleanest student-facing content
        for nysed in data.get("nysed_items", []):
            stem = nysed.get("stem", "").strip()
            if not stem:
                continue
            options = nysed.get("options", {})
            correct_key = nysed.get("correct_answer", "")
            answer_text = options.get(correct_key, "") if correct_key else ""
            # Format as a complete MCQ example
            q_lines = [stem]
            for k in ["A", "B", "C", "D"]:
                if k in options:
                    q_lines.append(f"  {k}) {options[k]}")
            examples.append({"question": "\n".join(q_lines), "answer": answer_text})
            if len(examples) >= 3:
                break

        # Priority 2: Khan Academy MCQ (radio) items — good student-facing content
        if len(examples) < 3:
            for exercise in data.get("khan_exercises", []):
                for item in exercise.get("items", []):
                    if "radio" not in item.get("widget_types", []):
                        continue
                    raw_q = item.get("question_content", "")
                    # Strip widget placeholders
                    question = re.sub(r"\[\[☃[^\]]*\]\]", "", raw_q)
                    question = re.sub(r"\n{3,}", "\n\n", question).strip()
                    if not question:
                        continue
                    # Skip if it still contains visual/media references
                    if _is_non_student_facing(question):
                        continue
                    answer_text = ""
                    for widget_data in item.get("answer_data", {}).values():
                        if widget_data.get("type") != "radio":
                            continue
                        for choice in widget_data.get("choices", []):
                            if choice.get("correct"):
                                answer_text = choice.get("content", "").strip()
                                break
                        if answer_text:
                            break
                    # Skip answers that are images/visual content
                    if answer_text and _is_non_student_facing(answer_text):
                        answer_text = ""
                    examples.append({"question": question, "answer": answer_text})
                    if len(examples) >= 3:
                        break
                if len(examples) >= 3:
                    break

        # Priority 3: Math problems — filter to only self-contained, student-facing ones
        if len(examples) < 3:
            for prob in data.get("problems", []):
                text = prob.get("text", "").strip()
                if not text:
                    continue
                # Clean and filter out non-student-facing content
                cleaned = _clean_problem_text(text)
                if cleaned and not _is_non_student_facing(cleaned):
                    examples.append({"question": cleaned, "answer": ""})
                if len(examples) >= 3:
                    break

        return {
            "description": description,
            "grade_label":  grade_label,
            "subject":      subject,
            "examples":     examples,
        }

    except Exception as e:
        print(f"[by_standard] Error loading context for {skill_id}: {e}")
        return {}


def _is_non_student_facing(text: str) -> bool:
    """
    Returns True if the text contains indicators that it's NOT student-facing
    content (curriculum metadata, teacher instructions, visual references, etc).
    """
    # Image/table/video placeholders
    if re.search(r"###(IMAGE|TABLE|FIGURE|VIDEO)\d*###", text, re.IGNORECASE):
        return True
    # Graphie/image markdown (Khan Academy internal image format)
    if re.search(r"web\+graphie:|!\[.*\]\(.*graphie|LOCALPATH", text):
        return True
    # References to curriculum lessons/tasks
    if re.search(r"(Anchor Task|Lesson \d|from Lesson|from Unit|Problem Set)", text, re.IGNORECASE):
        return True
    # Teacher-facing instructions
    if re.search(r"(Add the new facts|to your multiplication table|Watch the following video|Act \d:)", text, re.IGNORECASE):
        return True
    # Standard code references (CCSS, CCRA, NYSED identifiers)
    if re.search(r"\b(CCSS|CCRA|NYSED|NYSP12|Common Core|standard\s+\w+\.\d)", text, re.IGNORECASE):
        return True
    # URLs and file references
    if re.search(r"https?://|\.html\b|\.pdf\b|\.json\b", text, re.IGNORECASE):
        return True
    # References to external resources or curriculum structure
    if re.search(r"(curriculum|Fishtank|EngageNY|Eureka Math|module \d)", text, re.IGNORECASE):
        return True
    # Perseus/Khan widget references that leaked through
    if re.search(r"☃|☣|widget_types|answer_data", text):
        return True
    # Visual reference patterns (shared with has_visual_reference but broader)
    if has_visual_reference(text):
        return True
    return False


def _clean_problem_text(text: str) -> str:
    """
    Clean a raw problem text block to extract only student-facing content.
    Strips metadata, curriculum references, image placeholders, and
    extracts the first self-contained problem sub-part.
    """
    # Remove image/table/video placeholders
    text = re.sub(r"###(IMAGE|TABLE|FIGURE|VIDEO)\d*###", "", text)
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove markdown headers that are just "Problem N" — keep the content below
    text = re.sub(r"^Problem\s+\d+\s*\n?", "", text, flags=re.MULTILINE)
    # Remove sub-part labels like "a." "b." "i." "ii." at start of line
    # (keep the content)
    text = re.sub(r"^\s*[a-z]\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[ivx]+\.\s+", "", text, flags=re.MULTILINE)
    # Collapse excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    # If text is very long (multi-problem dump), take only the first meaningful chunk
    # Split on "Problem" boundaries and take the first substantial one
    chunks = re.split(r"\n(?=Problem\s+\d)", text)
    if chunks:
        # Take the first chunk that has reasonable length (>20 chars, <500 chars)
        for chunk in chunks:
            chunk = chunk.strip()
            if 20 < len(chunk) < 500:
                return chunk
        # If no chunk in ideal range, just take first chunk truncated
        first = chunks[0].strip()
        if len(first) > 500:
            # Truncate at sentence boundary
            sentences = first[:500].rsplit(".", 1)
            return sentences[0] + "." if len(sentences) > 1 else first[:400]
        return first

    return text[:500] if len(text) > 500 else text


def _format_by_standard_section(ctx: dict) -> str:
    """
    Format a loaded by_standard context dict into a prompt-injectable text block.

    CRITICAL: The description is framed as the SKILL THE STUDENT SHOULD PRACTICE,
    not as content to quiz them about.  The AI must never ask "what does this
    standard say?" or reference the standard code in student-facing text.
    """
    lines = ["\n=== SKILL CONTEXT (for your reference — NOT student-facing) ==="]
    lines.append("NOTE: The information below tells YOU what skill to assess.")
    lines.append("NEVER show standard codes, descriptions, or curriculum metadata to the student.")
    lines.append("NEVER ask the student what a standard means or what it requires.")
    lines.append("")
    if ctx.get("description"):
        lines.append(f"Skill being assessed: {ctx['description']}")
    if ctx.get("subject"):
        lines.append(f"Subject area: {ctx['subject']}")
    if ctx.get("grade_label"):
        lines.append(f"Target level: {ctx['grade_label']}")
    if ctx.get("examples"):
        lines.append("\nEXAMPLE PROBLEMS (use these as format/difficulty reference only — do NOT copy or closely paraphrase):")
        for i, ex in enumerate(ctx["examples"], 1):
            lines.append(f"\n  Example {i}:")
            # Indent each line for clarity
            for line in ex["question"].splitlines():
                lines.append(f"    {line}")
            if ex.get("answer"):
                lines.append(f"    [Correct: {ex['answer']}]")
    lines.append("\n=============================================================\n")
    return "\n".join(lines)


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
    
    # Load enriched research context if available
    research_context = ""
    if skill_id:
        try:
            safe_name = skill_id.replace('.', '_').replace('-', '_')
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            research_file = os.path.join(base_dir, "data", "research", f"{safe_name}_Context.md")
            if os.path.exists(research_file):
                with open(research_file, "r", encoding="utf-8") as f:
                    research_context = f.read().strip()
                print(f"[Problem Narrator] Loaded enriched pedagogical context for {skill_id}")
        except Exception as e:
            print(f"[Problem Narrator] Error loading context: {e}")
            
    prompt = f"""
You are the Problem Narrator subagent for an adaptive learning platform. Your task is to wrap a mathematical question into a narrative word problem matching the student's interests and age.

Student Profile:
- Age: {student_age} years old
- Grade: Grade {student_grade}
- Interests: {student_interest} (e.g., the Bible, History)
- Output Language: {lang_name}
"""

    if research_context:
        prompt += f"\n=== ENRICHED PEDAGOGICAL RESEARCH & CONSTRAINTS ===\n{research_context}\n===================================================\n"

    # When OpenCode is the active backend, also inject the by_standard node data
    if True:
        bs_ctx = _load_by_standard_context(skill_id)
        if bs_ctx:
            prompt += _format_by_standard_section(bs_ctx)
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

    std_info = ela_loader.load_ela_standard(skill_id, grade_level)
    standard_description = std_info.get(
        "description", f"Grade {grade_level} Math standard {skill_id}"
    )

    # Load enriched research context if available
    research_context = ""
    try:
        safe_name = skill_id.replace('.', '_').replace('-', '_')
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        research_file = os.path.join(base_dir, "data", "research", f"{safe_name}_Context.md")
        if os.path.exists(research_file):
            with open(research_file, "r", encoding="utf-8") as f:
                research_context = f.read().strip()
    except Exception:
        pass

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

    if research_context:
        prompt += f"\n=== ENRICHED CONTEXT ===\n{research_context}\n========================\n"

    # When OpenCode is the active backend, also inject the by_standard node data
    if True:
        bs_ctx = _load_by_standard_context(skill_id)
        if bs_ctx:
            prompt += _format_by_standard_section(bs_ctx)
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
"""
    # When OpenCode is the active backend, inject age-appropriate language constraints
    if True:
        prompt += _format_age_grade_constraints(student_age, student_grade, language=language, context="tutor")

    response = call_ai(prompt)

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
    except Exception:
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

    # Load enriched research context if available
    research_context = ""
    try:
        safe_name = skill_id.replace('.', '_').replace('-', '_')
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        research_file = os.path.join(base_dir, "data", "research", f"{safe_name}_Context.md")
        if os.path.exists(research_file):
            with open(research_file, "r", encoding="utf-8") as f:
                research_context = f.read().strip()
            print(f"[ELA Generator] Loaded enriched pedagogical context for {skill_id}")
    except Exception as e:
        print(f"[ELA Generator] Error loading context: {e}")

    if question_mode == "writing_prompt":
        prompt = f"""
You are the ELA Writing Curriculum Subagent for an adaptive K-12 platform.
Generate an engaging, grade-appropriate open-ended writing prompt.

Student Profile:
- Age: {student_age} years old
- Grade: Grade {grade_level}
- Interests: {student_interest}
- Target Language: {lang_name}

ELA Writing Standard:
- Code: {skill_id}
- Domain: {domain}
- Official Description: "{standard_description}"
"""
        if research_context:
            prompt += f"\n=== ENRICHED PEDAGOGICAL RESEARCH & CONSTRAINTS ===\n{research_context}\n===================================================\n"

        # When OpenCode is the active backend, also inject the by_standard node data
        if True:
            bs_ctx = _load_by_standard_context(skill_id)
            if bs_ctx:
                prompt += _format_by_standard_section(bs_ctx)
            prompt += _format_age_grade_constraints(student_age, grade_level, language=language, context="question")

        if previous_questions:
            n = len(previous_questions)
            prompt += (
                f"\n\nALREADY ANSWERED BY THIS STUDENT "
                f"({n} prompt{'s' if n > 1 else ''}) — "
                "DO NOT repeat or closely resemble any of these:\n"
            )
            for i, q in enumerate(previous_questions, 1):
                prompt += f"\n  [Prompt {i}]\n"
                for line in q.get("problem_text", "").splitlines():
                    prompt += f"  {line}\n"
            prompt += (
                "\nYour new prompt MUST use a completely different context, "
                "scenario, and subject matter. "
                "The CCSS standard being assessed must remain identical.\n"
            )

        prompt += f"""
Instructions:
1. Create a focused writing prompt that directly assesses the standard above.
2. Theme the prompt around the student's interests to make it engaging.
3. The prompt length and difficulty must match the student's age ({student_age} years old) and Grade level (Grade {grade_level}):
   - For Kindergarten (Grade 0) & Grade 1: The prompt must only ask for 1 very simple sentence (e.g. write one simple sentence about a happy dog or write one word). NEVER ask for paragraphs or complex essays. Use extremely simple, sight words.
   - For Elementary (Grades 2-5): Ask for 1 short paragraph (3-4 simple sentences).
   - For Middle & High School (Grades 6-13): The prompt can ask for 1-3 paragraphs of original student writing.
4. Include a brief, friendly setup sentence before the actual prompt.
5. Do NOT include any sample answer or outline.
6. Output a clean JSON object. Do NOT wrap in markdown blocks.

Output JSON Schema:
{{
  "stem_template": "Setup sentence + the writing prompt question...",
  "options": {{}},
  "correct_key": "",
  "correct_answer": "",
  "math_expression": "Writing: {skill_id}",
  "standard_description": "{standard_description}",
  "domain": "{domain}"
}}
"""
    else:  # MCQ reading comprehension or grammar
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
        if research_context:
            prompt += f"\n=== ENRICHED PEDAGOGICAL RESEARCH & CONSTRAINTS ===\n{research_context}\n===================================================\n"

        # When OpenCode is the active backend, also inject the by_standard node data
        if True:
            bs_ctx = _load_by_standard_context(skill_id)
            if bs_ctx:
                prompt += _format_by_standard_section(bs_ctx)
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
    if question_mode == "writing_prompt":
        return {
            "skeleton_id": f"ela_fallback_{uuid.uuid4().hex[:8]}",
            "stem_template": f"Write a short paragraph about something you care about that connects to this idea: {standard_description}",
            "options": {},
            "correct_key": "",
            "correct_answer": "",
            "math_expression": f"Writing: {skill_id}",
            "question_mode": "writing_prompt",
            "standard_description": standard_description,
            "domain": domain
        }
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

    # Load enriched research context if available
    research_context = ""
    try:
        safe_name = skill_id.replace('.', '_').replace('-', '_')
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        research_file = os.path.join(base_dir, "data", "research", f"{safe_name}_Context.md")
        if os.path.exists(research_file):
            with open(research_file, "r", encoding="utf-8") as f:
                research_context = f.read().strip()
    except Exception:
        pass

    prompt = f"""You are the ELA Curriculum Subagent for an adaptive K-12 platform.
Generate exactly {n} COMPLETELY DIFFERENT {'reading comprehension' if question_mode == 'mcq' else 'writing'} questions,
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

    if research_context:
        prompt += f"\n=== ENRICHED PEDAGOGICAL RESEARCH & CONSTRAINTS ===\n{research_context}\n===================================================\n"

    # When OpenCode is the active backend, also inject the by_standard node data
    if True:
        bs_ctx = _load_by_standard_context(skill_id)
        if bs_ctx:
            prompt += _format_by_standard_section(bs_ctx)
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

    if question_mode == "mcq":
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
    else:  # writing_prompt
        prompt += f"""
CRITICAL DIVERSITY RULE: The {n} prompts must address completely different scenarios.

Output a JSON ARRAY of exactly {n} objects. No markdown fences. No extra text.
[
  {{
    "stem_template": "Setup sentence + the writing prompt...",
    "options": {{}},
    "correct_key": "",
    "correct_answer": "",
    "standard_description": "{standard_description}",
    "domain": "{domain}"
  }},
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


def grade_writing_subagent(
    student_text: str,
    standard_description: str,
    skill_id: str,
    grade_level: int,
    student_interest: str,
    language: str
) -> dict:
    """
    6-Trait Analytic Writing Scorer Subagent.
    Scores student writing across 6 independent traits (1-4 scale each).
    Returns structured JSON with per-trait scores, feedback, and composite verdict.
    """
    lang_name = "Tagalog (Filipino)" if language.lower() == "tl" else "English"

    prompt = f"""
You are an expert K-12 writing assessor. Score the following Grade {grade_level} student writing sample
using the 6-Trait Analytic Writing Rubric. Be fair, grade-appropriate, and encouraging in your feedback.

ELA Standard Being Assessed:
- Code: {skill_id}
- Description: "{standard_description}"

Student Profile:
- Grade: {grade_level}
- Language: {lang_name}
- Interests: {student_interest}

Student's Writing:
---
{student_text}
---

Scoring Rubric (score each trait 1-4):
- 4 = Exceeds grade-level expectations
- 3 = Meets grade-level expectations
- 2 = Developing, approaching grade level
- 1 = Beginning, significant gaps

Traits to Score:
1. Ideas: Clarity of central claim/argument, relevance, supporting details
2. Organization: Logical structure, transitions, clear intro and conclusion
3. Voice: Appropriate tone for audience and purpose, engagement
4. Word Choice: Precision, grade-level vocabulary, descriptive language
5. Sentence Fluency: Sentence variety, rhythm, flow when read aloud
6. Conventions: Grammar, spelling, punctuation, capitalization

Output ONLY a raw JSON object (no markdown, no explanation outside JSON):
{{
  "ideas": 2,
  "organization": 1,
  "voice": 3,
  "word_choice": 2,
  "sentence_fluency": 2,
  "conventions": 3,
  "composite": 2.17,
  "verdict": "developing",
  "trait_feedback": {{
    "ideas": "Your main point is present but needs specific evidence or examples to support it.",
    "organization": "Try starting with a clear opening sentence that states your main idea.",
    "voice": "Your enthusiasm comes through! Keep that personal connection.",
    "word_choice": "Good start. Try replacing common words with more specific ones.",
    "sentence_fluency": "Most sentences follow a similar pattern. Try starting one differently.",
    "conventions": "Strong spelling and punctuation! Watch for comma usage."
  }}
}}

Verdict must be exactly one of: "exceeds", "meets", "developing", "beginning"
(exceeds: 3.5-4.0, meets: 2.5-3.4, developing: 1.5-2.4, beginning: 1.0-1.4)
"""

    # When OpenCode is the active backend, inject age-appropriate language constraints for feedback
    if True:
        # Estimate age from grade_level (grade 0 = ~5, grade 1 = ~6, etc.)
        est_age = grade_level + 5 if grade_level <= 12 else 17
        prompt += _format_age_grade_constraints(est_age, grade_level, language=language, context="tutor")

    response = call_ai(prompt)

    response_clean = response.strip()
    if response_clean.startswith("```json"):
        response_clean = response_clean[7:]
    if response_clean.endswith("```"):
        response_clean = response_clean[:-3]
    response_clean = response_clean.strip()

    try:
        parsed = json.loads(response_clean)
        # Ensure composite is recalculated for integrity
        trait_keys = ["ideas", "organization", "voice", "word_choice", "sentence_fluency", "conventions"]
        scores = [parsed.get(k, 1) for k in trait_keys]
        composite = round(sum(scores) / len(scores), 2)
        parsed["composite"] = composite
        # Ensure verdict matches composite
        if composite >= 3.5:
            parsed["verdict"] = "exceeds"
        elif composite >= 2.5:
            parsed["verdict"] = "meets"
        elif composite >= 1.5:
            parsed["verdict"] = "developing"
        else:
            parsed["verdict"] = "beginning"
        return parsed
    except Exception as e:
        print(f"Failed to parse writing grade from subagent: {str(e)}. Raw: {response}")
        return {
            "ideas": 1, "organization": 1, "voice": 1,
            "word_choice": 1, "sentence_fluency": 1, "conventions": 1,
            "composite": 1.0, "verdict": "beginning",
            "trait_feedback": {
                "ideas": "Please try to expand your response with more detail.",
                "organization": "Make sure your response has a clear beginning and end.",
                "voice": "Let your own perspective come through in your writing!",
                "word_choice": "Try using more specific and descriptive words.",
                "sentence_fluency": "Vary the way you begin your sentences.",
                "conventions": "Review grammar and punctuation before submitting."
            }
        }


def writing_socratic_tutor_subagent(
    student_question: str,
    trait_scores: dict,
    standard_description: str,
    skill_id: str,
    student_text: str,
    chat_history: list,
    language: str,
    student_age: int,
    student_grade: int,
    student_interest: str
) -> dict:
    """
    Writing-Mode Socratic Tutor Subagent.
    Reactive-only: answers ONLY what the student explicitly asks.
    Uses trait scores as private context to nudge toward weak areas without lecturing.
    """
    lang_name = "Tagalog" if language.lower() == "tl" else "English"

    # Format the private trait context for the tutor
    trait_context = "\n".join([
        f"- {trait.replace('_', ' ').title()}: {score}/4"
        for trait, score in trait_scores.items()
        if trait in ["ideas", "organization", "voice", "word_choice", "sentence_fluency", "conventions"]
    ])

    # Format chat history
    formatted_history = ""
    for msg in chat_history:
        if isinstance(msg, dict):
            role_val = msg.get("role")
            content_val = msg.get("content")
        else:
            role_val = getattr(msg, "role", "user")
            content_val = getattr(msg, "content", "")
        role = "Student" if role_val == "user" else "Coach"
        formatted_history += f"{role}: {content_val}\n"

    prompt = f"""
You are a warm, Socratic Writing Coach for a {student_age}-year-old Grade {student_grade} student.
Your role is to ONLY answer the specific question the student has asked. Do NOT volunteer
extra information or corrections they didn't ask about.

However, you have private context (the student cannot see this) that you use to shape HOW
you answer — guiding them gently toward their weakest areas without being explicit about it.

=== PRIVATE CONTEXT (student cannot see this) ===
Writing Standard: {skill_id} - "{standard_description}"
Student's Writing Sample:
"{student_text[:500]}..."

Trait Scores (private):
{trait_context}
=== END PRIVATE CONTEXT ===

Student Profile (visible context):
- Age: {student_age}, Grade: {student_grade}
- Interests: {student_interest}
- Output Language: {lang_name}

Conversation History:
{formatted_history}

Student's Current Question: "{student_question}"

Your Response Rules:
1. Answer ONLY what the student asked — do not proactively teach other traits.
2. Use Socratic questioning where possible (guide with questions, not answers).
3. If their question touches a weak trait (low score), gently help them see the gap without
   saying "you scored low on..." — instead, ask guiding questions.
4. Keep response warm, encouraging, and under 4 sentences.
5. Use the student's interest themes ({student_interest}) when helpful for analogies.
6. Output ONLY raw JSON.

JSON Output:
{{
  "reply": "your coaching response in {lang_name}"
}}
"""

    # When OpenCode is the active backend, inject age-appropriate language constraints
    if True:
        prompt += _format_age_grade_constraints(student_age, student_grade, language=language, context="tutor")

    response = call_ai(prompt)
    response_clean = response.strip()
    if response_clean.startswith("```json"):
        response_clean = response_clean[7:]
    if response_clean.endswith("```"):
        response_clean = response_clean[:-3]
    response_clean = response_clean.strip()

    try:
        parsed = json.loads(response_clean)
        return {"reply": parsed.get("reply", "Great question! Think about how your writing connects to what the prompt is asking — what's the most important idea you want the reader to remember?")}
    except Exception:
        return {"reply": "That's a thoughtful question! Consider reading your writing aloud — does each sentence support your main idea? What would make it even stronger?"}
