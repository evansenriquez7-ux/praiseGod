#!/usr/bin/env python3
"""
testy.py — Themed CCSS practice problem generator

Usage:
    python scripts/testy.py "1.G.A.1" "biblical history"
    python scripts/testy.py "4.NF.B.3c" "minecraft"
    python scripts/testy.py "L.K.1.e" "space exploration"

Server management:
    python scripts/testy.py --start-server
    python scripts/testy.py --stop-server
    python scripts/testy.py --start-server "1.G.A.1" "minecraft"   # start then generate

Options:
    --port PORT     OpenCode server port (default: 4096)
    --model MODEL   Model to use (default: opencode/deepseek-v4-flash-free)

When the server is running, each call creates a fresh session (clean history),
sends the prompt, collects the response, then deletes the session.
When no server is detected, falls back to `opencode run` subprocess.
"""

import sys
import os
import signal
import json
import shutil
import subprocess
import re
import time
import random
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Optional

try:
    import requests as _requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ── Constants ─────────────────────────────────────────────────────────────────

ROOT          = Path(__file__).parent.parent
BY_STANDARD   = ROOT / "data" / "processed" / "by_standard"
PID_FILE      = Path("/tmp/opencode_serve.pid")
DEFAULT_PORT  = 4096
DEFAULT_MODEL = "opencode/deepseek-v4-flash-free"
SCRATCH_DIR   = ROOT / "scratch"
SCRATCH_FILE  = SCRATCH_DIR / "gen_problems.jsonl"

# ── Problem type eligibility ──────────────────────────────────────────────────

ELIGIBLE_MODES = {
    "math":     ["mcq", "numeric_input", "multi_select", "ordering"],
    "language": ["mcq", "cloze", "multi_select"],
    "reading":  ["mcq", "multi_select", "ordering"],
    "sl":       ["mcq", "multi_select"],
    "writing":  ["writing_prompt"],
    "phonics":  ["mcq"],
}

# ── Binary resolution ─────────────────────────────────────────────────────────

def find_opencode() -> str:
    found = shutil.which("opencode")
    if found:
        return found
    default = Path.home() / ".opencode" / "bin" / "opencode"
    if default.exists():
        return str(default)
    print("[ERROR] opencode not found. Install it or add ~/.opencode/bin to your PATH.",
          file=sys.stderr)
    sys.exit(1)

OPENCODE_BIN = find_opencode()

# ── Scratch file (session problem history) ────────────────────────────────────

def _ensure_scratch_dir() -> None:
    """Create scratch directory if it does not exist."""
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)


def load_previous_problems(node_id: str) -> list:
    """
    Return all problems generated for node_id in the current session.
    Each item is a dict with at minimum 'problem_text' and 'answer'.
    """
    _ensure_scratch_dir()
    if not SCRATCH_FILE.exists():
        return []
    problems = []
    with open(SCRATCH_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("node_id") == node_id:
                    problems.append(obj)
            except json.JSONDecodeError:
                continue
    return problems


def save_problem(node_id: str, structured: dict, question_type: str = "mcq") -> None:
    """
    Append a generated problem record to the scratch file.
    structured is the dict returned by extract_structured_output().
    Only saves if a non-empty problem was parsed.
    Saves the problem exactly as it was presented to the student.
    """
    problem_text = structured.get("problem", "").strip()
    if not problem_text:
        return  # nothing useful to store

    _ensure_scratch_dir()

    # Append choices to problem_text for types that display them
    choices = structured.get("choices", {})
    if choices and question_type in ("mcq", "multi_select", "ordering"):
        choices_block = "\n".join(
            f"{letter}) {text}" for letter, text in sorted(choices.items())
        )
        problem_text = f"{problem_text}\n{choices_block}"

    record: dict = {
        "node_id":       node_id,
        "question_mode": question_type,
        "problem_text":  problem_text,
        "generated_at":  time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    # Type-specific answer storage
    if question_type in ("mcq", "numeric_input"):
        record["answer"] = structured.get("answer", "")

    elif question_type == "cloze":
        raw_answer = structured.get("answer", "")
        record["fills"]  = [f.strip() for f in raw_answer.split("|") if f.strip()]
        record["answer"] = raw_answer   # pipe-separated, for dedup prompt injection

    elif question_type == "multi_select":
        raw_correct = structured.get("correct", "")
        record["correct_keys"] = [
            k.strip().upper() for k in raw_correct.split(",") if k.strip()
        ]
        record["answer"] = raw_correct  # for dedup prompt injection

    elif question_type == "ordering":
        raw_order = structured.get("order", "")
        record["order_keys"] = [
            k.strip().upper() for k in raw_order.split(",") if k.strip()
        ]
        record["answer"] = raw_order    # for dedup prompt injection

    with open(SCRATCH_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def clear_all_problems() -> None:
    """Wipe the entire scratch file. Called on OpenCode server start."""
    _ensure_scratch_dir()
    SCRATCH_FILE.write_text("")


def clear_node_problems(node_id: str) -> None:
    """
    Remove all entries for node_id from the scratch file.
    Called when a student enters a different node.
    """
    _ensure_scratch_dir()
    if not SCRATCH_FILE.exists():
        return
    kept = []
    with open(SCRATCH_FILE, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
                if obj.get("node_id") != node_id:
                    kept.append(stripped)
            except json.JSONDecodeError:
                kept.append(stripped)  # preserve unparseable lines
    SCRATCH_FILE.write_text("\n".join(kept) + ("\n" if kept else ""))

# ── Server management ─────────────────────────────────────────────────────────

def server_is_running(port: int) -> bool:
    """Return True if opencode serve is healthy on the given port."""
    if not REQUESTS_AVAILABLE:
        return False
    try:
        r = _requests.get(f"http://localhost:{port}/global/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def start_server(port: int) -> bool:
    """
    Start opencode serve on the given port as a background process.
    Saves PID to PID_FILE. Polls until healthy (up to 15s).
    Returns True on success, False on timeout.
    """
    if server_is_running(port):
        print(f"[*] OpenCode server already running on :{port}")
        return True

    print(f"[+] Starting OpenCode server on port {port} ...", end="", flush=True)
    proc = subprocess.Popen(
        [OPENCODE_BIN, "serve", "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(ROOT),
    )
    PID_FILE.write_text(str(proc.pid))

    for _ in range(30):          # 30 × 0.5s = 15s max
        time.sleep(0.5)
        print(".", end="", flush=True)
        if server_is_running(port):
            print(f" ready  (PID {proc.pid})")
            clear_all_problems()
            print(f"[*] Cleared problem history ({SCRATCH_FILE.name})")
            return True

    print(" [TIMEOUT]")
    print("[ERROR] Server did not respond within 15s.", file=sys.stderr)
    return False


def stop_server() -> None:
    """Stop the opencode serve process recorded in PID_FILE."""
    if not PID_FILE.exists():
        print("[*] No PID file found — server may not be running.")
        return
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        PID_FILE.unlink(missing_ok=True)
        print(f"[✓] Stopped OpenCode server (PID {pid})")
    except ProcessLookupError:
        print(f"[*] Process not found — server was already dead.")
        PID_FILE.unlink(missing_ok=True)
    except ValueError:
        print("[ERROR] PID file is corrupt.", file=sys.stderr)
        PID_FILE.unlink(missing_ok=True)

# ── Standard helpers ──────────────────────────────────────────────────────────

def normalize_standard(code: str) -> str:
    """Uppercase and clean the standard code. e.g. '1.g.a.1' → '1.G.A.1'"""
    return code.strip().upper()


def find_by_standard_file(standard: str) -> Optional[Path]:
    """
    Try multiple naming conventions:
      dot format:          RI.4.2.json     (ELA)
      underscore format:   1_G_A_1.json    (Math / HS with hyphens → underscores)
    Also handles hyphens in standard codes (e.g. A-REI.B.3 → A_REI_B_3.json).
    Falls back to a case-insensitive glob scan.
    """
    dot_path = BY_STANDARD / f"{standard}.json"
    if dot_path.exists():
        return dot_path

    # Replace dots with underscores (and hyphens too for HS standards)
    underscore_name = standard.replace(".", "_").replace("-", "_") + ".json"
    us_path = BY_STANDARD / underscore_name
    if us_path.exists():
        return us_path

    # Case-insensitive fallback: normalize both to "all lowercase, no separators"
    def _norm(s: str) -> str:
        return re.sub(r"[.\-_]", "", s.lower())

    target_norm = _norm(standard)
    for f in BY_STANDARD.glob("*.json"):
        if _norm(f.stem) == target_norm:
            return f

    return None


def subject_category(standard: str) -> str:
    """Map a standard code to its ELIGIBLE_MODES key."""
    s = standard.upper()
    if s.startswith("W."):                return "writing"
    if s.startswith("RF."):               return "phonics"
    if s.startswith("SL."):               return "sl"
    if s.startswith(("RL.", "RI.")):      return "reading"
    if s.startswith("L."):                return "language"
    return "math"


def mode_for_standard(standard: str) -> str:
    """Randomly pick an eligible problem type for this standard."""
    return random.choice(ELIGIBLE_MODES[subject_category(standard)])

# ── Prompt construction ───────────────────────────────────────────────────────

def _grade_label(grade_level: int) -> str:
    """Convert numeric grade level to a readable string."""
    if grade_level == 0:
        return "Kindergarten"
    return f"Grade {grade_level}"


def _clean_question(text: str) -> str:
    """Strip Khan widget placeholders and normalize whitespace."""
    text = re.sub(r'\[\[☃[^\]]*\]\]', '', text)   # remove [[☃ widget]] tokens
    text = re.sub(r'\n{3,}', '\n\n', text)          # collapse excess blank lines
    return text.strip()


def load_standard_context(std_file: Path) -> dict:
    """
    Read a by_standard JSON file and return a context dict:
      {
        description: str,
        grade_label:  str,   e.g. "Grade 1" or "Kindergarten"
        subject:      str,
        examples:     list[{question: str, answer: str}]  (up to 3, MCQ only)
      }
    """
    with open(std_file, encoding="utf-8") as f:
        data = json.load(f)

    description = data.get("standard_description", "").strip()
    grade_raw   = data.get("grade_level", 1)
    try:
        grade_label = _grade_label(int(grade_raw))
    except (ValueError, TypeError):
        # Non-integer grade levels: "HS", "9-10", "11-12", etc.
        grade_label = f"Grade {grade_raw}"
    subject = data.get("subject", "").strip()

    # Extract up to 3 MCQ (radio) items from khan_exercises
    examples = []
    for exercise in data.get("khan_exercises", []):
        for item in exercise.get("items", []):
            if "radio" not in item.get("widget_types", []):
                continue
            question = _clean_question(item.get("question_content", ""))
            if not question:
                continue
            # Find the correct answer text from the radio widget
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
            if question:
                examples.append({"question": question, "answer": answer_text})
            if len(examples) >= 3:
                break
        if len(examples) >= 3:
            break

    return {
        "description": description,
        "grade_label":  grade_label,
        "subject":      subject,
        "examples":     examples,
    }


def build_prompt(
    standard: str,
    interests: str,
    context: dict,
    previous_problems: list = None,
    question_type: str = "mcq",
) -> str:
    """
    Build the complete self-contained prompt that the testy agent receives.
    The script provides all context; the agent only needs to write the problem.
    If previous_problems is provided, inject them so the agent avoids duplication.
    """
    lines = []
    lines.append(f"QUESTION TYPE: {question_type}")
    lines.append("")
    lines.append(f"CCSS Standard : {standard}")
    lines.append(f"Subject       : {context['subject']}")
    lines.append(f"Grade         : {context['grade_label']}")
    lines.append(f"Description   : {context['description']}")

    if context["examples"]:
        lines.append("")
        lines.append("EXAMPLE PROBLEMS (use as format and difficulty reference only — do not copy):")
        for i, ex in enumerate(context["examples"], 1):
            lines.append("")
            lines.append(f"{i}. {ex['question']}")
            if ex["answer"]:
                lines.append(f"   Correct answer: {ex['answer']}")

    if previous_problems:
        n = len(previous_problems)
        lines.append("")
        lines.append(
            f"ALREADY GENERATED THIS SESSION ({n} problem{'s' if n > 1 else ''}) — "
            "DO NOT repeat or closely resemble any of these:"
        )
        for i, prob in enumerate(previous_problems, 1):
            lines.append("")
            lines.append(f"  [Problem {i}]")
            for pline in prob.get("problem_text", "").splitlines():
                lines.append(f"  {pline}")
            if prob.get("answer"):
                lines.append(f"  Answer: {prob['answer']}")
        lines.append("")
        lines.append(
            "Your new problem MUST use a different real-world context, different "
            "characters or names, and different numbers or values. "
            "The CCSS skill being tested must remain identical."
        )

    lines.append("")
    lines.append(f"Student interest theme: {interests}")
    lines.append("")
    lines.append(
        "Generate exactly one original practice problem following the output format "
        "in your instructions. Return only the formatted block, no preamble."
    )

    return "\n".join(lines)


# ── HTTP path ─────────────────────────────────────────────────────────────────

def run_testy_agent_http(
    prompt: str,
    port: int,
    model: str,
) -> tuple[str, dict, dict]:
    """
    Call the testy agent via the running opencode HTTP server.

    Always creates a fresh session so there is zero chat history carried over
    from previous runs. The session is deleted after the response is received.

    Returns (raw_text, tokens, timing).
    """
    base       = f"http://localhost:{port}"
    session_id = None

    try:
        # 1. Fresh session — clean slate, no prior history
        r = _requests.post(f"{base}/session", json={}, timeout=10)
        r.raise_for_status()
        session_id = r.json()["id"]

        # 2. Send the pre-built prompt; block until the agent finishes
        # model string "provider/modelID" must be split into an object
        if "/" in model:
            provider_id, model_id = model.split("/", 1)
        else:
            provider_id, model_id = "opencode", model

        t_start = time.time()
        r = _requests.post(
            f"{base}/session/{session_id}/message",
            json={
                "agent": "testy",
                "model": {"providerID": provider_id, "modelID": model_id},
                "parts": [{"type": "text", "text": prompt}],
            },
            timeout=180,   # 3-minute ceiling for slow models
        )
        t_end = time.time()
        r.raise_for_status()

        data  = r.json()
        info  = data.get("info", {})
        parts = data.get("parts", [])

        # 3. Concatenate all non-ignored text parts for the final response
        raw_text = "\n".join(
            p["text"] for p in parts
            if p.get("type") == "text" and not p.get("ignored")
        ).strip()

        # 4. Tokens from AssistantMessage.tokens
        info_tok = info.get("tokens", {})
        cache    = info_tok.get("cache", {})
        tokens   = {
            "input":       info_tok.get("input",     0),
            "output":      info_tok.get("output",    0),
            "reasoning":   info_tok.get("reasoning", 0),
            "cache_read":  cache.get("read",  0),
            "cache_write": cache.get("write", 0),
            "context":     info_tok.get("total", 0),  # peak context window
            "cost":        info.get("cost", 0.0),
        }

        # 5. Server-side elapsed: message timestamps (Unix ms → seconds)
        t_info      = info.get("time", {})
        t_created   = t_info.get("created",   0)
        t_completed = t_info.get("completed", 0)
        t_server    = (t_completed - t_created) / 1000.0 if t_completed else 0.0

        timing = {"client": t_end - t_start, "server": t_server}

        # Surface any model/agent error embedded in the response
        if info.get("error"):
            err = info["error"]
            msg = err.get("data", {}).get("message", str(err))
            raise RuntimeError(f"Agent error: {msg}")

        return raw_text, tokens, timing

    finally:
        # Always delete the session — keeps the server clean
        if session_id:
            try:
                _requests.delete(f"{base}/session/{session_id}", timeout=5)
            except Exception:
                pass

# ── Subprocess path (fallback when server is not running) ─────────────────────

def run_testy_agent_subprocess(
    prompt: str,
    model: str,
) -> tuple[str, dict, dict]:
    """
    Invoke the testy agent via `opencode run` (no persistent server required).
    Returns (raw_text, tokens, timing).
    """
    cmd = [
        OPENCODE_BIN,
        "run",
        "--agent", "testy",
        "--model", model,
        "--format", "json",
        "--dangerously-skip-permissions",
        prompt,
    ]

    t_start = time.time()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        cwd=str(ROOT),
    )

    message_texts: dict = defaultdict(str)
    message_order: list = []
    raw_tokens = {"input": 0, "output": 0, "context": 0}

    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue

        ev_type = ev.get("type", "")
        part    = ev.get("part", {})

        if ev_type == "text":
            msg_id = part.get("messageID", "unknown")
            chunk  = part.get("text", "")
            if chunk:
                if msg_id not in message_texts:
                    message_order.append(msg_id)
                message_texts[msg_id] += chunk

        elif ev_type == "step_finish":
            toks = part.get("tokens", {})
            raw_tokens["input"]   += toks.get("input",  0)
            raw_tokens["output"]  += toks.get("output", 0)
            raw_tokens["context"]  = toks.get("total",  0)   # last step = peak context

        elif ev_type == "error":
            err  = ev.get("error", {})
            data = err.get("data", {})
            msg  = data.get("message", str(err))
            if "model" in msg.lower() or "invalid" in msg.lower():
                model_in_url = ""
                meta = data.get("metadata", {})
                url  = meta.get("url", "")
                if "/model/" in url:
                    model_in_url = url.split("/model/")[1].split("/")[0]
                print(f"\n[ERROR] Model not found: {msg}", file=sys.stderr)
                if model_in_url:
                    print(f"        Attempted model: {model_in_url}", file=sys.stderr)
                print(f"        Fix: update 'model:' in .opencode/agents/testy.md",
                      file=sys.stderr)
                print(f"        Run 'opencode models' to list available models.",
                      file=sys.stderr)
            else:
                print(f"\n[ERROR] OpenCode agent failed: {msg}", file=sys.stderr)
            proc.wait()
            sys.exit(1)

    proc.wait()
    t_end = time.time()

    final_text = message_texts[message_order[-1]] if message_order else ""
    tokens = {
        "input":       raw_tokens["input"],
        "output":      raw_tokens["output"],
        "reasoning":   0,
        "cache_read":  0,
        "cache_write": 0,
        "context":     raw_tokens["context"],
        "cost":        0.0,
    }
    timing = {"client": t_end - t_start, "server": 0.0}

    return final_text, tokens, timing

# ── Output parsing & formatting ───────────────────────────────────────────────

def clean(s: str) -> str:
    """Strip markdown bold/italic markers and noise."""
    return re.sub(r'\*+', '', s).strip().strip('`').strip()


def extract_structured_output(text: str) -> dict:
    """
    Parse the structured block the testy agent emits.
    Tolerates markdown bold/italic markers and code fences.
    Normalizes common blank markers (___  [blank]  ____) to {{BLANK}} for cloze.
    """
    result = {}
    text   = re.sub(r'```[a-z]*\n?', '', text)

    # Normalize cloze blank markers so validation always finds {{BLANK}}
    text = re.sub(r'\[BLANK\]|\[blank\]|\[_+\]', '{{BLANK}}', text)
    text = re.sub(r'\b_{2,}\b', '{{BLANK}}', text)   # standalone __ or ___

    single_line = {
        "standard": r"STANDARD:\s*\*{0,2}(.+?)\*{0,2}\s*$",
        "skill":    r"SKILL:\s*\*{0,2}(.+?)\*{0,2}\s*$",
        "grade":    r"GRADE:\s*\*{0,2}(.+?)\*{0,2}\s*$",
        "answer":   r"ANSWER:\s*\*{0,2}(.+?)\*{0,2}\s*$",
        "correct":  r"CORRECT:\s*\*{0,2}(.+?)\*{0,2}\s*$",
        "order":    r"ORDER:\s*\*{0,2}(.+?)\*{0,2}\s*$",
    }
    for key, pattern in single_line.items():
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if m:
            result[key] = clean(m.group(1))

    exp_match = re.search(
        r"EXPLANATION:\s*\*{0,2}\n?([\s\S]+?)(?=\n\s*[A-Z]{2,}:|```|$)",
        text, re.IGNORECASE,
    )
    if exp_match:
        result["explanation"] = clean(exp_match.group(1))

    prob_match = re.search(
        r"PROBLEM:\s*\*{0,2}\n+([\s\S]+?)(?=\n\s*A\)|\n\s*ANSWER:|\n\s*CORRECT:|\n\s*ORDER:)",
        text, re.IGNORECASE,
    )
    if prob_match:
        result["problem"] = clean(prob_match.group(1))

    choices = {}
    for letter in "ABCDE":
        m = re.search(
            rf"^{letter}\)\s*\*{{0,2}}(.+?)\*{{0,2}}\s*$",
            text, re.MULTILINE | re.IGNORECASE,
        )
        if m:
            choices[letter] = clean(m.group(1))
    if choices:
        result["choices"] = choices

    return result


def format_output(
    standard: str,
    interests: str,
    structured: dict,
    tokens: dict,
    timing: dict,
    raw_text: str,
    question_type: str = "mcq",
) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append(f"  STANDARD : {structured.get('standard', standard)}")
    lines.append(f"  SKILL    : {structured.get('skill', 'N/A')}")
    lines.append(f"  GRADE    : {structured.get('grade', 'N/A')}")
    lines.append(f"  THEME    : {interests}")
    lines.append(f"  TYPE     : {question_type}")
    lines.append("=" * 60)
    lines.append("")

    problem     = structured.get("problem", "")
    choices     = structured.get("choices", {})
    answer      = structured.get("answer", "")
    explanation = structured.get("explanation", "")
    correct     = structured.get("correct", "")   # multi_select
    order       = structured.get("order", "")     # ordering

    has_content = bool(problem or answer or correct or order)

    if not has_content:
        lines.append("(Could not parse structured output — raw response:)")
        lines.append("")
        lines.append(raw_text)
        lines.append("")
    else:
        # ── Problem stem ──────────────────────────────────────────
        if problem:
            lines.append("PROBLEM:")
            lines.append("")
            for line in problem.splitlines():
                lines.append(f"  {line}")
            lines.append("")

        # ── Choices (mcq, multi_select, ordering) ─────────────────
        if choices and question_type in ("mcq", "multi_select", "ordering"):
            for letter in "ABCDE":
                if letter in choices:
                    lines.append(f"  {letter}) {choices[letter]}")
            lines.append("")

        # ── Type-specific answer display ───────────────────────────
        if question_type == "mcq":
            if answer:
                lines.append(f"ANSWER: {answer}")
                lines.append("")

        elif question_type == "numeric_input":
            if answer:
                lines.append(f"ANSWER: {answer}")
                lines.append("")

        elif question_type == "cloze":
            if answer:
                fills = [f.strip() for f in answer.split("|")]
                lines.append("FILLS:")
                for i, fill in enumerate(fills, 1):
                    lines.append(f"  {i}. {fill}")
                lines.append("")

        elif question_type == "multi_select":
            if correct:
                lines.append(f"CORRECT: {correct}")
                lines.append("")

        elif question_type == "ordering":
            if order:
                lines.append(f"ORDER: {order}")
                lines.append("")

        # ── Explanation ────────────────────────────────────────────
        if explanation:
            lines.append("EXPLANATION:")
            for line in explanation.splitlines():
                lines.append(f"  {line}")
            lines.append("")

    # ── Footer ────────────────────────────────────────────────────
    lines.append("-" * 60)

    lines.append(
        f"  TOKENS   input: {tokens['input']:,}  "
        f"output: {tokens['output']:,}  "
        f"reasoning: {tokens['reasoning']:,}"
    )

    cache_read  = tokens.get("cache_read",  0)
    cache_write = tokens.get("cache_write", 0)
    context     = tokens.get("context",     0)
    cost        = tokens.get("cost",        0.0)

    if cache_read or cache_write:
        lines.append(f"           cache read: {cache_read:,}  write: {cache_write:,}")
    if context:
        lines.append(f"           peak context: {context:,}")
    if cost:
        lines.append(f"           cost: ${cost:.6f}")

    t_client = timing.get("client", 0.0)
    t_server = timing.get("server", 0.0)
    if t_server:
        lines.append(f"  ELAPSED  {t_client:.1f}s total  ({t_server:.1f}s model)")
    else:
        lines.append(f"  ELAPSED  {t_client:.1f}s")

    lines.append("-" * 60)

    return "\n".join(lines)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="testy — generate themed CCSS practice problems via OpenCode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            '  testy.py "1.G.A.1" "biblical history"\n'
            "  testy.py --start-server\n"
            '  testy.py --start-server "4.NF.B.3c" "minecraft"\n'
            "  testy.py --stop-server\n"
            '  testy.py --port 4097 "L.K.1.e" "space exploration"'
        ),
    )
    parser.add_argument("standard",  nargs="?", metavar="STANDARD",
                        help="CCSS standard code, e.g. 1.G.A.1")
    parser.add_argument("interests", nargs="?", metavar="INTERESTS",
                        help="Student interests, e.g. 'biblical history'")
    parser.add_argument("--start-server", action="store_true",
                        help="Start opencode serve in background, then exit (or generate if STANDARD+INTERESTS given)")
    parser.add_argument("--stop-server",  action="store_true",
                        help="Stop running opencode serve, then exit")
    parser.add_argument("--port",  type=int, default=DEFAULT_PORT,
                        help=f"Server port (default: {DEFAULT_PORT})")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--clear-node", metavar="NODE_ID",
                        help="Clear scratch history for NODE_ID (standard code), then exit")
    parser.add_argument("--type",
                        choices=["mcq", "numeric_input", "cloze",
                                 "multi_select", "ordering"],
                        default=None, dest="question_type", metavar="TYPE",
                        help="Force problem type (default: random per standard). "
                             "Choices: mcq, numeric_input, cloze, multi_select, ordering")

    args = parser.parse_args()

    # ── Server lifecycle ──────────────────────────────────────────────────
    if args.stop_server:
        stop_server()
        if not (args.standard and args.interests):
            return

    if args.start_server:
        ok = start_server(args.port)
        if not ok:
            sys.exit(1)
        if not (args.standard and args.interests):
            return

    if args.clear_node:
        clear_node_problems(args.clear_node)
        print(f"[*] Cleared problem history for node: {args.clear_node}")
        if not (args.standard and args.interests):
            return

    # ── Generation ────────────────────────────────────────────────────────
    if not (args.standard and args.interests):
        parser.print_help()
        sys.exit(1)

    standard = normalize_standard(args.standard)
    std_file = find_by_standard_file(standard)
    if not std_file:
        print(f"[ERROR] No by_standard file found for '{standard}'", file=sys.stderr)
        print(f"        Looked in: {BY_STANDARD}", file=sys.stderr)
        sys.exit(1)

    # Determine problem type: explicit flag takes priority, else random per standard
    node_id       = standard
    question_type = args.question_type or mode_for_standard(standard)

    # Load previous problems for dedup
    previous = load_previous_problems(node_id)

    # Script builds the complete prompt — agent only writes the problem
    context = load_standard_context(std_file)
    prompt  = build_prompt(standard, args.interests, context,
                           previous_problems=previous or None,
                           question_type=question_type)

    # Auto-detect: prefer HTTP server, fall back to subprocess
    use_http = server_is_running(args.port) and REQUESTS_AVAILABLE
    if use_http:
        mode = f"server (:{args.port}, fresh session)"
    elif not REQUESTS_AVAILABLE:
        mode = "subprocess  [requests not installed — install it to enable server mode]"
    else:
        mode = "subprocess  [no server detected — run --start-server to enable server mode]"

    print(f"Generating   : {standard}  ({args.interests})")
    print(f"Type         : {question_type}")
    print(f"Mode         : {mode}")
    print(f"Content file : {std_file.name}")
    print(f"Model        : {args.model}")
    print(f"Examples     : {len(context['examples'])} reference problem(s) included")
    print(f"History      : {len(previous)} previous problem(s) injected for dedup")
    print()

    try:
        if use_http:
            raw_text, tokens, timing = run_testy_agent_http(
                prompt, args.port, args.model
            )
        else:
            raw_text, tokens, timing = run_testy_agent_subprocess(
                prompt, args.model
            )
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    if not raw_text.strip():
        print("[ERROR] Agent returned no response.", file=sys.stderr)
        sys.exit(1)

    structured = extract_structured_output(raw_text)

    # Record for future dedup (only if we got a valid problem)
    save_problem(node_id, structured, question_type)

    output = format_output(standard, args.interests, structured,
                           tokens, timing, raw_text, question_type)
    print(output)


if __name__ == "__main__":
    main()
