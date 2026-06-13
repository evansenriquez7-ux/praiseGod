"""
opencode_bridge.py — Async bridge for calling OpenCode subagents from FastAPI.

Uses asyncio.create_subprocess_exec so long-running agent calls (15-30s)
don't block the FastAPI event loop. Parses the JSON event stream that
`opencode run --format json` emits.

Usage:
    from backend.app.opencode_bridge import run_testy_agent

    result = await run_testy_agent("1.G.A.1", "biblical history")
    # result: { standard, skill, grade, problem, choices, answer, explanation, tokens }
"""

import asyncio
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Optional

# ── Binary resolution ─────────────────────────────────────────────────────────

def _find_opencode() -> str:
    found = shutil.which("opencode")
    if found:
        return found
    default = Path.home() / ".opencode" / "bin" / "opencode"
    if default.exists():
        return str(default)
    raise RuntimeError(
        "opencode binary not found. "
        "Install it or add ~/.opencode/bin to PATH."
    )

OPENCODE_BIN = _find_opencode()
ROOT = Path(__file__).parent.parent.parent  # repo root


# ── JSON event stream parser ──────────────────────────────────────────────────

async def _read_event_stream(stdout) -> tuple[str, dict]:
    """
    Consume the JSON event stream from `opencode run --format json`.

    Events of interest:
      { "type": "text",        "part": { "messageID": str, "text": str } }
      { "type": "step_finish", "part": { "tokens": { "input": int, "output": int, "total": int } } }
      { "type": "error",       "error": { ... } }

    Returns:
        (final_text, token_totals)
        final_text    — concatenated text from the last messageID
        token_totals  — { "input": int, "output": int, "context": int }
    """
    message_texts: dict[str, str] = defaultdict(str)
    message_order: list[str] = []
    token_totals = {"input": 0, "output": 0, "context": 0}

    async for raw in stdout:
        line = raw.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue

        ev_type = ev.get("type", "")
        part = ev.get("part", {})

        if ev_type == "text":
            msg_id = part.get("messageID", "unknown")
            chunk = part.get("text", "")
            if chunk:
                if msg_id not in message_texts:
                    message_order.append(msg_id)
                message_texts[msg_id] += chunk

        elif ev_type == "step_finish":
            tokens = part.get("tokens", {})
            token_totals["input"] += tokens.get("input", 0)
            token_totals["output"] += tokens.get("output", 0)
            token_totals["context"] = tokens.get("total", 0)

        elif ev_type == "error":
            err = ev.get("error", {})
            data = err.get("data", {})
            msg = data.get("message", str(err))
            raise RuntimeError(f"OpenCode agent error: {msg}")

    final_text = ""
    if message_order:
        final_text = message_texts[message_order[-1]]

    return final_text, token_totals


# ── Output parser ─────────────────────────────────────────────────────────────

def _clean(s: str) -> str:
    return re.sub(r"\*+", "", s).strip().strip("`").strip()


def _parse_testy_output(text: str) -> dict:
    """
    Parse the structured block that the testy agent emits.
    Tolerates markdown bold/italic markers and code fences.
    """
    result: dict = {}

    # Strip code fences
    text = re.sub(r"```[a-z]*\n?", "", text)

    single_line = {
        "standard": r"STANDARD:\s*\*{0,2}(.+?)\*{0,2}\s*$",
        "skill":    r"SKILL:\s*\*{0,2}(.+?)\*{0,2}\s*$",
        "grade":    r"GRADE:\s*\*{0,2}(.+?)\*{0,2}\s*$",
        "answer":   r"ANSWER:\s*\*{0,2}(.+?)\*{0,2}\s*$",
    }
    for key, pattern in single_line.items():
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if m:
            result[key] = _clean(m.group(1))

    exp_match = re.search(
        r"EXPLANATION:\s*\*{0,2}\n?([\s\S]+?)(?=\n[A-Z]{2,}:|```|$)",
        text, re.IGNORECASE,
    )
    if exp_match:
        result["explanation"] = _clean(exp_match.group(1))

    prob_match = re.search(
        r"PROBLEM:\s*\*{0,2}\n+([\s\S]+?)(?=\n\s*A\)|\nANSWER:)",
        text, re.IGNORECASE,
    )
    if prob_match:
        result["problem"] = _clean(prob_match.group(1))

    choices: dict[str, str] = {}
    for letter in "ABCD":
        m = re.search(
            rf"^{letter}\)\s*\*{{0,2}}(.+?)\*{{0,2}}\s*$",
            text, re.MULTILINE | re.IGNORECASE,
        )
        if m:
            choices[letter] = _clean(m.group(1))
    if choices:
        result["choices"] = choices

    return result


# ── Public interface ──────────────────────────────────────────────────────────

async def run_testy_agent(
    standard: str,
    interests: str,
    model: str = "opencode/deepseek-v4-flash-free",
    timeout: int = 120,
) -> dict:
    """
    Invoke the testy OpenCode subagent asynchronously.

    Args:
        standard:  CCSS standard code, e.g. "1.G.A.1"
        interests: Student interests string, e.g. "biblical history"
        model:     OpenCode model identifier (default: deepseek-v4-flash-free)
        timeout:   Max seconds to wait for the agent (default: 120)

    Returns:
        dict with keys: standard, skill, grade, problem, choices (dict A-D),
                        answer, explanation, tokens (dict), raw_text
    Raises:
        RuntimeError on agent error or timeout
    """
    standard = standard.strip().upper()
    prompt = f"standard: {standard} | interests: {interests}"

    cmd = [
        OPENCODE_BIN,
        "run",
        "--agent", "testy",
        "--model", model,
        "--format", "json",
        "--dangerously-skip-permissions",
        prompt,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        cwd=str(ROOT),
    )

    try:
        raw_text, tokens = await asyncio.wait_for(
            _read_event_stream(proc.stdout),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise RuntimeError(
            f"Testy agent timed out after {timeout}s "
            f"(standard={standard}, interests={interests})"
        )

    await proc.wait()

    if not raw_text.strip():
        raise RuntimeError("Testy agent returned an empty response.")

    structured = _parse_testy_output(raw_text)
    structured["tokens"] = tokens
    structured["raw_text"] = raw_text

    return structured
