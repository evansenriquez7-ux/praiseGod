"""H4-C campaign helper (dispatcher side; never authors or edits a verdict).

  shape   <transcript>                      print each transcript line's structure (no content)
  take    <dispatch_id> <transcript>        copy the transcript, write the judge's final reply byte for byte
  audit   <dispatch_id>                     transcript audit + every refusal tests/stem_file.py would raise (dry run)
  file    <dispatch_id>                     file through tests/stem_file.py (only after a clean audit)

Dispatch ids: stem-batch44N-S44N-NNN-{first|confirming}[-rK]. The ledger (ledger.json) maps each to its item,
role, the first record it confirms, and its status. Run from the repo root with PYTHONPATH=.
"""
import argparse, json, re, shutil, subprocess, sys, types
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/enrichmentcap/Documents/antigravity/ccmed")
H = ROOT / "local_only/scratch/h4c"
LEDGER = H / "ledger.json"
sys.path.insert(0, str(ROOT))


def ledger():
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else {}


def save(led):
    LEDGER.write_text(json.dumps(led, indent=1, sort_keys=True) + "\n")


def parse_id(did):
    m = re.fullmatch(r"stem-batch(\d+)-(S\d+-\d{3})-(first|confirming)(?:-r(\d+))?", did)
    if not m:
        raise SystemExit(f"bad dispatch id {did!r}")
    return m.group(1), m.group(2), m.group(3)


def paths(did):
    batch, item, role = parse_id(did)
    group = item.split("-")[0]
    return {"packets": H / "keys" / f"{group}.json", "key": H / "keys" / f"{group}.key.json",
            "prompt": H / "prompts" / f"{item}.prompt.txt", "reply": H / "replies" / f"{did}.txt",
            "transcript": H / "transcripts" / f"{did}.jsonl", "item": item, "role": role, "batch": batch}


def lines(transcript):
    out = []
    for raw in Path(transcript).read_text(encoding="utf-8").splitlines():
        if raw.strip():
            out.append(json.loads(raw))
    return out


def blocks(d):
    c = (d.get("message") or {}).get("content")
    return c if isinstance(c, list) else []


def cmd_shape(a):
    for i, d in enumerate(lines(a.transcript)):
        m = d.get("message") or {}
        c = m.get("content")
        desc = [(b.get("type"), b.get("name"), sorted((b.get("input") or {}))) for b in c] if isinstance(c, list) \
            else (type(c).__name__, len(c) if isinstance(c, str) else None)
        print(i, d.get("type"), m.get("role"), m.get("model"), m.get("stop_reason"), desc, sorted(d))


def final_reply(ls):
    """The text of the LAST assistant message that carries text, exactly as the model emitted it."""
    hand = [b["input"]["message"] for d in ls for b in blocks(d)
            if b.get("type") == "tool_use" and b.get("name") == "SubagentHandback"]
    if hand:
        if len(hand) != 1:
            raise SystemExit(f"{len(hand)} SubagentHandback calls; refusing to choose one")
        return hand[0]
    for d in reversed(ls):
        m = d.get("message") or {}
        if m.get("role") != "assistant":
            continue
        texts = [b["text"] for b in blocks(d) if b.get("type") == "text"]
        if texts:
            if len(texts) != 1:
                raise SystemExit(f"final assistant message has {len(texts)} text blocks; refusing to join them")
            return texts[0]
    raise SystemExit("no assistant text in the transcript")


def tool_report(ls, prompt_path, n_lines):
    """(tool uses by name, problems). Reads must be of the prompt only and must cover every line."""
    uses, problems, covered, models = [], [], set(), set()
    results = {}
    for d in ls:
        for b in blocks(d):
            if b.get("type") == "tool_result":
                results[b.get("tool_use_id")] = b
    for d in ls:
        m = d.get("message") or {}
        if m.get("role") == "assistant" and m.get("model"):
            models.add(m["model"])
        for b in blocks(d):
            if b.get("type") != "tool_use":
                continue
            name, inp = b.get("name"), b.get("input") or {}
            if name == "SubagentHandback":
                continue      # the reply itself, taken by final_reply
            uses.append(name)
            if name != "Read":
                problems.append(f"tool {name} used ({json.dumps(inp)[:120]})")
                continue
            if inp.get("file_path") != str(prompt_path):
                problems.append(f"Read of another path {inp.get('file_path')!r}")
                continue
            res = results.get(b.get("id"))
            if res is None or res.get("is_error"):
                continue      # a failed read covers nothing
            off = int(inp.get("offset") or 1)
            lim = int(inp.get("limit") or 2000)
            off = max(off, 1)
            covered |= set(range(off, min(off + lim, n_lines + 1)))
    missing = sorted(set(range(1, n_lines + 1)) - covered)
    if missing:
        problems.append(f"read covers {len(covered)} of {n_lines} lines; first unread line {missing[0]}")
    return uses, problems, sorted(models)


def cmd_take(a):
    p = paths(a.dispatch_id)
    for k in ("reply", "transcript"):
        if p[k].exists():
            raise SystemExit(f"{p[k]} exists; never overwritten")
    p["transcript"].parent.mkdir(exist_ok=True)
    shutil.copyfile(a.transcript, p["transcript"])
    ls = lines(p["transcript"])
    reply = final_reply(ls)
    p["reply"].write_text(reply, encoding="utf-8")
    led = ledger()
    ent = {"item": p["item"], "role": p["role"], "status": "taken"}
    if p["role"] == "confirming":
        firsts = [d for d, e in led.items() if e.get("item") == p["item"] and e.get("role") == "first"
                  and e.get("status") == "filed"]
        if len(firsts) != 1:
            raise SystemExit(f"{a.dispatch_id}: {len(firsts)} filed first record(s) for {p['item']}: {firsts}")
        ent["confirms"] = firsts[0]
    led.setdefault(a.dispatch_id, {}).update(ent)
    save(led)
    print(f"took {a.dispatch_id}: reply {len(reply)} chars")


def n_prompt_lines(prompt):
    # The Read tool numbers lines as splitlines() does.
    return len(prompt.read_text(encoding="utf-8").splitlines())


def stem_args(did, filed_at, tool_uses, confirms):
    p = paths(did)
    who = f"blind-stem-judge-claude-haiku-batch{p['batch']}-{did[len('stem-batch') + len(p['batch']) + 1:]}"
    rel = lambda x: str(x.relative_to(ROOT))  # noqa: E731
    return types.SimpleNamespace(
        packets=rel(p["packets"]), key=rel(p["key"]), item=p["item"], reply=rel(p["reply"]), role=p["role"],
        confirms=confirms, judged_by=who, dispatch_id=did, filed_at=filed_at,
        delivery=(f"Claude Code Agent tool, model=haiku, subagent_type=general-purpose; the judge was told to read only "
                  f"{rel(p['prompt'])} (tests/stem_file.py prompt output, item {p['item']}; no lc id, no key or packets "
                  f"file in that directory) and reply with what it asks; dispatched with CLAUDE.md loaded (ruling 29). "
                  f"Blindness is a prompt contract, audited from the subagent transcript."),
        tool_uses=tool_uses, prompt=rel(p["prompt"]), review_dir=str(ROOT / "validation_reports/stem_review"))


def audit(did):
    """(problems, args) -- transcript problems plus every refusal the filer would raise."""
    p = paths(did)
    led = ledger()
    ent = led.get(did) or {}
    ls = lines(p["transcript"])
    n = n_prompt_lines(p["prompt"])
    uses, problems, models = tool_report(ls, p["prompt"], n)
    tool_uses = (f"From the subagent transcript: {len(uses)} tool use(s), all Read of its own prompt file "
                 f"({n} lines, every line read); no other tool, path or search. Model reported in the transcript: "
                 f"{', '.join(models) or 'none recorded'}." if not problems else "AUDIT FAILED")
    confirms = ent.get("confirms") if p["role"] == "confirming" else None
    args = stem_args(did, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), tool_uses, confirms)
    import importlib.util
    spec = importlib.util.spec_from_file_location("stem_file", ROOT / "tests/stem_file.py")
    SF = importlib.util.module_from_spec(spec); spec.loader.exec_module(SF)
    item = SF._load_item(str(ROOT / args.packets), args.item)
    keys = json.loads((ROOT / args.key).read_text(encoding="utf-8"))
    raw = p["reply"].read_text(encoding="utf-8")
    try:
        rec = SF.build_record(item, keys[args.item], raw, types.SimpleNamespace(**{**vars(args), "prompt": str(ROOT / args.prompt)}))
        problems += SF.refusals(rec, Path(args.review_dir))
    except SystemExit as exc:
        problems.append(f"filer refused: {exc}")
    try:
        from backend.app.practice_gen.validation import validate_stem_review as VSR
        v = VSR.parse_reply(raw)
        summary = {"overall": v.get("overall"), "failing": v.get("failing_templates"),
                   "not_producible": sorted(c for c, x in (v.get("clauses") or {}).items()
                                            if isinstance(x, dict) and x.get("verdict") == "NOT_PRODUCIBLE")}
    except Exception as exc:  # noqa: BLE001 - reported, the reply is then set aside
        summary = {"unparseable": f"{type(exc).__name__}: {exc}"}
    return problems, args, summary, models


def cmd_audit(a):
    problems, args, summary, models = audit(a.dispatch_id)
    led = ledger()
    led.setdefault(a.dispatch_id, {}).update({"audit": problems or "clean", "summary": summary, "models": models})
    save(led)
    print(json.dumps({"dispatch": a.dispatch_id, "summary": summary, "models": models,
                      "problems": problems or "none"}, ensure_ascii=False))
    return 1 if problems else 0


def cmd_file(a):
    problems, args, summary, _m = audit(a.dispatch_id)
    if problems:
        raise SystemExit(f"REFUSING to file {a.dispatch_id}: audit problems {problems}")
    cmd = [str(ROOT / ".venv/bin/python"), "tests/stem_file.py", "file", "--packets", args.packets, "--key", args.key,
           "--item", args.item, "--reply", args.reply, "--role", args.role, "--judged-by", args.judged_by,
           "--dispatch-id", args.dispatch_id, "--filed-at", args.filed_at, "--delivery", args.delivery,
           "--tool-uses", args.tool_uses, "--prompt", args.prompt]
    if args.confirms:
        cmd += ["--confirms", args.confirms]
    r = subprocess.run(cmd, cwd=ROOT, env={"PYTHONPATH": ".", "PATH": "/usr/bin:/bin"}, capture_output=True, text=True)
    print(r.stdout.strip(), r.stderr.strip()[-2000:])
    led = ledger()
    led.setdefault(a.dispatch_id, {}).update({"status": "filed" if r.returncode == 0 else f"file-exit-{r.returncode}",
                                               "filed_at": args.filed_at})
    save(led)
    return r.returncode


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("shape"); s.add_argument("transcript")
    t = sub.add_parser("take"); t.add_argument("dispatch_id"); t.add_argument("transcript")
    u = sub.add_parser("audit"); u.add_argument("dispatch_id")
    f = sub.add_parser("file"); f.add_argument("dispatch_id")
    a = ap.parse_args()
    return {"shape": cmd_shape, "take": cmd_take, "audit": cmd_audit, "file": cmd_file}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
