"""Agent-session (Claude Code) cost of the Acra work, estimated from the session transcripts.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Reads every transcript under ``~/.claude/projects`` (main sessions and their subagents), prices each
assistant message once (lines repeat per content block under one message id) from its model and
usage, and attributes it to Acra when the turn it belongs to mentions Acra: a turn starts at a
message the user typed and runs to the next, and is Acra when any of its text (the user's words, the
assistant's text, tool inputs) matches `ACRA`. A subagent transcript is judged as a whole.

Writes ``agent_sessions.csv``, one row per session with Acra turns: the Acra-attributed cost (the
estimate) and the whole session's cost (the ceiling). `acra_cost_ledger.py` reads the file.
A session dedicated to the Acra work makes the estimate exact; until then it is a heuristic.

    python agent_session_costs.py
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path.home() / ".claude" / "projects"
OUT = Path(__file__).parent / "agent_sessions.csv"
ACRA = re.compile(r"\bacra\b|\bdscr\b|platinum select|acra-|acra_", re.IGNORECASE)
PER_MTOK = 1_000_000
#: $/MTok: input, output, cache read (claude-api skill table, cached 2026-10-06).
PRICES = {
    "claude-fable-5-1": (10.0, 50.0, 0.25), "claude-fable-5": (10.0, 50.0, 1.0),
    "claude-opus-5-5": (4.0, 20.0, 0.20), "claude-opus-5": (5.0, 25.0, 0.50),
    "claude-opus-4-8": (5.0, 25.0, 0.50), "claude-opus-4-7": (5.0, 25.0, 0.50),
    "claude-opus-4-6": (5.0, 25.0, 0.50), "claude-sonnet-5-5": (2.0, 10.0, 0.20),
    "claude-sonnet-5": (2.0, 10.0, 0.20), "claude-sonnet-4-6": (3.0, 15.0, 0.30),
    "claude-haiku-5-5": (0.10, 0.50, 0.01), "claude-haiku-4-5": (1.0, 5.0, 0.10),
}
#: Claude Haiku 5.5 above this prompt size bills at the higher rates below.
HAIKU_LONG_PROMPT = 100_000
HAIKU_LONG = (0.50, 2.50, 0.05)
CACHE_WRITE_5M, CACHE_WRITE_1H = 1.25, 2.0


def _price(model: str, usage: dict) -> float | None:
    base = next((p for name, p in sorted(PRICES.items(), key=lambda kv: -len(kv[0]))
                 if model.startswith(name)), None)
    if base is None:
        return None
    inp, cread = usage.get("input_tokens") or 0, usage.get("cache_read_input_tokens") or 0
    create = usage.get("cache_creation_input_tokens") or 0
    split = usage.get("cache_creation") or {}
    w1h = split.get("ephemeral_1h_input_tokens")
    w5m = split.get("ephemeral_5m_input_tokens")
    if w1h is None and w5m is None:
        w1h, w5m = 0, create
    if model.startswith("claude-haiku-5-5") and inp + cread + create > HAIKU_LONG_PROMPT:
        base = HAIKU_LONG
    i, o, r = base
    return (inp * i + (usage.get("output_tokens") or 0) * o + cread * r
            + (w5m or 0) * i * CACHE_WRITE_5M + (w1h or 0) * i * CACHE_WRITE_1H) / PER_MTOK


#: Text the harness injects into user messages (CLAUDE.md, memory, command echoes): not the turn's
#: subject, and CLAUDE.md names Acra, so left in it would mark every session's first turn Acra.
INJECTED = re.compile(r"<(system-reminder|local-command-\w+|command-\w+)>.*?</\1>", re.DOTALL)


def _texts(message: dict) -> list[str]:
    content = message.get("content")
    if isinstance(content, str):
        return [INJECTED.sub("", content)]
    out = []
    for block in content or []:
        if block.get("type") == "text":
            out.append(INJECTED.sub("", block.get("text", "")))
        elif block.get("type") == "tool_use":
            out.append(json.dumps(block.get("input", "")))
    return out


def _typed_by_user(line: dict) -> bool:
    if line.get("type") != "user" or line.get("isSidechain"):
        return False
    content = line["message"].get("content")
    if isinstance(content, str):
        return bool(INJECTED.sub("", content).strip())
    return any(b.get("type") == "text" and INJECTED.sub("", b.get("text", "")).strip()
               for b in content or []) and not any(
        b.get("type") == "tool_result" for b in content or [])


def session_cost(path: Path, whole: bool) -> dict:
    """Cost of one transcript: all of it, and the Acra turns (or all, when ``whole`` decides)."""
    messages: dict[str, tuple[str, dict, int]] = {}
    turn, turn_is_acra, acra_turns = 0, defaultdict(bool), 0
    first = last = entrypoint = None
    for raw in path.open():
        try:
            line = json.loads(raw)
        except json.JSONDecodeError:
            continue
        stamp = line.get("timestamp")
        first, last = first or stamp, stamp or last
        entrypoint = entrypoint or line.get("entrypoint")
        if _typed_by_user(line):
            turn += 1
        msg = line.get("message") or {}
        if any(ACRA.search(t) for t in _texts(msg)) if isinstance(msg, dict) else False:
            turn_is_acra[turn] = True
        if line.get("type") == "assistant" and msg.get("usage") and msg.get("model", "").startswith("claude"):
            key = msg.get("id") or line.get("uuid")
            prev = messages.get(key)
            if prev is None or (msg["usage"].get("output_tokens") or 0) >= (prev[1].get("output_tokens") or 0):
                messages[key] = (msg["model"], msg["usage"], turn)
    total = acra = 0.0
    unpriced = set()
    models = defaultdict(float)
    for model, usage, t in messages.values():
        cost = _price(model, usage)
        if cost is None:
            unpriced.add(model)
            continue
        total += cost
        models[model] += cost
        if whole or turn_is_acra[t]:
            acra += cost
    acra_turns = sum(1 for v in turn_is_acra.values() if v)
    return {"total": total, "acra": acra, "turns": turn, "acra_turns": acra_turns,
            "first": first, "last": last, "models": dict(models), "unpriced": sorted(unpriced),
            "any_acra": whole or acra_turns > 0,
            # `claude -p` (the review script, scripted runs) records sdk-cli; a terminal session cli.
            "kind": "headless" if entrypoint == "sdk-cli" else "interactive"}


def main() -> None:
    rows = []
    for project in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        for main_file in sorted(project.glob("*.jsonl")):
            res = session_cost(main_file, whole=False)
            sub_total = sub_acra = 0.0
            for sub in sorted((project / main_file.stem / "subagents").glob("*.jsonl")):
                text = sub.read_text(errors="ignore")
                s = session_cost(sub, whole=bool(ACRA.search(text)))
                sub_total += s["total"]
                sub_acra += s["acra"] if s["any_acra"] else 0.0
            if not (res["any_acra"] or sub_acra):
                continue
            rows.append({
                "project": project.name, "session": main_file.stem, "kind": res["kind"],
                "first": (res["first"] or "")[:16], "last": (res["last"] or "")[:16],
                "turns": res["turns"], "acra_turns": res["acra_turns"],
                "acra_cost_usd": round(res["acra"] + sub_acra, 4),
                "session_cost_usd": round(res["total"] + sub_total, 4),
                "models": ";".join(f"{m}={c:.2f}" for m, c in sorted(res["models"].items())),
                "unpriced_models": ";".join(res["unpriced"])})
    rows.sort(key=lambda r: r["first"])
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["project"])
        writer.writeheader()
        writer.writerows(rows)
    for kind in ("interactive", "headless"):
        sel = [r for r in rows if r["kind"] == kind]
        est = sum(r["acra_cost_usd"] for r in sel)
        ceiling = sum(r["session_cost_usd"] for r in sel)
        print(f"{kind}: {len(sel)} sessions with Acra turns: estimate ${est:.2f}, ceiling ${ceiling:.2f}")
    unpriced = {m for r in rows for m in r["unpriced_models"].split(";") if m}
    if unpriced:
        print("unpriced models (not counted):", sorted(unpriced))


if __name__ == "__main__":
    main()
