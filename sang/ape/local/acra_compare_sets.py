"""Compare the Acra DSCR extraction sets pairwise: programs against each other, ours against Acra's.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

The sets split the guidelines at different grain (Acra's 123 Standard jobs against our 56), so a
one-to-one pairing misses most of what they share. Each item on the left is aligned instead to the
right items that state the same requirement: lexical candidates (tf-idf over the text, shared reads,
shared numbers; the same id first), then one model call per left item that labels each candidate
``same`` (same requirement, same numbers and conditions), ``differs`` (same requirement, a number or
condition differs: the note says which), ``partial`` (overlaps part of it) or ``none``.

    python_programs   our Python rules, Standard vs Platinum
    jtbd_programs     our JTBDs, Standard vs Platinum
    acra_programs     Acra's JTBD files, Standard vs Platinum
    acra_vs_jtbd_std  Acra's Standard jobs vs our Standard JTBDs (how much of Acra ours covers)
    acra_vs_jtbd_plat Acra's Platinum jobs vs our Platinum JTBDs

Writes ``compare_sets.json`` and ``compare_sets.xlsx``.

    python acra_compare_sets.py --runs coverage/runs_20261011.json [--out coverage/compare]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path("/Users/sangit/src/japes")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from acra_coverage_report import (  # noqa: E402
    ACRA_JTBD, Tally, _cos, _doc, _fetch, _final_run_ids, _kind, _numbers, _tfidf, _tokens)

CANDIDATES = 6
TEXT_CHARS = 1500
CODE_LINES = 25
PARALLEL = 4
RELATIONS = ("same", "differs", "partial", "none")

SYSTEM = (
    "You compare underwriting requirements from two rule sets for mortgage guidelines. For the LEFT "
    "item, label each numbered RIGHT candidate: 'same' when it states the same requirement with the "
    "same numbers and conditions; 'differs' when it is the same requirement (the same subject and "
    "trigger, e.g. both govern vacant rate-and-term refinances) but a number, limit, list member or "
    "condition differs (say exactly what differs in the note, left value then right value); two "
    "requirements of the same kind about different subjects or triggers are 'none'; 'partial' when it covers only part of the left item or the left covers only part of it; "
    "'none' otherwise. Judge the requirement, not the wording or the item's size. Use only the "
    "numbers shown; one entry per candidate.")


def _section_of(reasoning: str) -> str:
    return re.sub(r".*from section '(.*)'$", r"\1", reasoning or "")


def _heading(text: str) -> str:
    found = re.search(r"^#+\s*(.+)$", text or "", re.M)
    return found.group(1).strip() if found else ""


def _ours_jtbd(p: dict) -> dict:
    c = p["rule"]["condition"]
    return {"id": p["name"].rsplit(".", 1)[-1], "section": _section_of(p.get("reasoning", "")),
            "title": c.get("purpose", ""), "reads": c.get("reads") or [],
            "text": "\n".join([*(c.get("steps") or []), *(c.get("checks") or [])])}


def _ours_python(p: dict) -> dict:
    c = p["rule"]["condition"]
    code = "\n".join(c.get("source", "").splitlines()[:CODE_LINES])
    return {"id": p["name"].rsplit(".", 1)[-1], "section": _heading(p.get("excerpt", "")),
            "title": (p.get("reasoning") or "").split(". ")[0], "reads": c.get("reads") or [],
            "text": f"{p.get('reasoning', '')}\nCode:\n{code}", "code": c.get("source", "")}


def _acra(doc: str) -> list[dict]:
    items = []
    for value in json.loads(ACRA_JTBD[doc].read_text())["values"]:
        text = next((r.get("requirement_text", "") for r in value.get("requirements") or []
                     if r.get("investor") == "COMMON"), "")
        items.append({"id": value["mnemonic"], "section": value.get("section", ""),
                      "title": value.get("skill", ""), "text": text,
                      "reads": [m["metric_key"] for m in value.get("loan_metrics") or []
                                if m.get("metric_key")]})
    return items


def _blob(item: dict) -> str:
    return f"{item['section']} {item['title']} {item['text']}"


def _candidates(left: list[dict], right: list[dict]) -> list[list[int]]:
    vecs, _ = _tfidf([_tokens(_blob(i)) for i in left] + [_tokens(_blob(i)) for i in right])
    lv, rv = vecs[:len(left)], vecs[len(left):]
    out = []
    for i, item in enumerate(left):
        reads, nums = set(item["reads"]), _numbers(item["text"])
        scored = []
        for k, other in enumerate(right):
            ro = set(other["reads"])
            jacc = len(reads & ro) / len(reads | ro) if reads | ro else 0.0
            on = _numbers(other["text"])
            numo = len(nums & on) / len(nums | on) if nums | on else 0.0
            same_id = 1.0 if item["id"].lower() == other["id"].lower() else 0.0
            scored.append((same_id + 0.6 * _cos(lv[i], rv[k]) + 0.3 * jacc + 0.1 * numo, k))
        out.append([k for s, k in sorted(scored, reverse=True)[:CANDIDATES] if s > 0])
    return out


def _schema():
    from pydantic import BaseModel, Field

    class Label(BaseModel):
        candidate: int
        relation: str = "none"
        note: str = ""

    class Labels(BaseModel):
        labels: list[Label] = Field(default_factory=list)

    return Labels


def _card(n: int, item: dict) -> str:
    return (f"[{n}] {item['id']} ({item['section']}): {item['title']}\nReads: {', '.join(item['reads'])}\n"
            f"{item['text'][:TEXT_CHARS]}")


async def _label(agent, Labels, item: dict, right: list[dict], cands: list[int]) -> list[dict]:
    if not cands:
        return []
    prompt = (f"LEFT\n{_card(0, item)}\n\nRIGHT CANDIDATES\n"
              + "\n\n".join(_card(k, right[k]) for k in cands))
    try:
        result = await agent.run(system_prompt=SYSTEM, messages=[{"role": "user", "content": prompt}],
                                 output_schema=Labels, temperature=0.0)
    except Exception as exc:  # noqa: BLE001 - recorded on the row, the report goes on
        return [{"right": None, "relation": "error", "note": type(exc).__name__}]
    out = result.output if isinstance(result.output, Labels) else Labels(**result.output)
    return [{"right": right[lab.candidate]["id"], "relation": lab.relation, "note": lab.note}
            for lab in out.labels if lab.candidate in cands and lab.relation in RELATIONS[:3]]


async def compare(agent, Labels, left: list[dict], right: list[dict]) -> dict:
    cands = _candidates(left, right)
    gate = asyncio.Semaphore(PARALLEL)

    async def one(i):
        async with gate:
            return await _label(agent, Labels, left[i], right, cands[i])

    labels = await asyncio.gather(*(one(i) for i in range(len(left))))
    rows, matched_right = [], set()
    for item, found in zip(left, labels):
        best = next((r for r in RELATIONS[:3] if any(f["relation"] == r for f in found)), "none")
        if any(f["relation"] == "error" for f in found):
            best = "error"
        rows.append({"id": item["id"], "section": item["section"], "title": item["title"],
                     "best": best, "matches": found})
        matched_right |= {f["right"] for f in found if f["right"]}
    unmatched_right = [{"id": r["id"], "section": r["section"], "title": r["title"]}
                       for r in right if r["id"] not in matched_right]
    return {"left_items": len(left), "right_items": len(right),
            "left_best": dict(Counter(r["best"] for r in rows)),
            "right_unmatched": len(unmatched_right), "rows": rows, "only_right": unmatched_right}


def _python_number_deltas(rows: list[dict], left: list[dict], right: list[dict]) -> list[dict]:
    code_l = {i["id"]: i["code"] for i in left}
    code_r = {i["id"]: i["code"] for i in right}
    out = []
    for row in rows:
        for m in row["matches"]:
            if m["relation"] in ("same", "differs") and m["right"] in code_r:
                a, b = _numbers(code_l[row["id"]]), _numbers(code_r[m["right"]])
                if a != b:
                    out.append({"left": row["id"], "right": m["right"], "relation": m["relation"],
                                "only_left": sorted(a - b), "only_right": sorted(b - a)})
    return out


def _xlsx(results: dict, path: Path) -> None:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws.append(["comparison", "left", "right", "left items", "right items", *RELATIONS, "error",
               "right items matched by nothing"])
    for name, r in results.items():
        if name == "cost":
            continue
        ws.append([name, r["left"], r["right"], r["left_items"], r["right_items"],
                   *(r["left_best"].get(k, 0) for k in (*RELATIONS, "error")), r["right_unmatched"]])
    ws.append([])
    ws.append(["model cost"] + [f"{k}: {v}" for k, v in results["cost"].items()])
    for name, r in results.items():
        if name == "cost":
            continue
        sheet = wb.create_sheet(name[:31])
        sheet.append(["left id", "section", "title", "best", "right id", "relation", "note"])
        for row in r["rows"]:
            for m in row["matches"] or [{"right": "", "relation": "", "note": ""}]:
                sheet.append([row["id"], row["section"], row["title"][:300], row["best"],
                              m["right"], m["relation"], m["note"]])
        for item in r["only_right"]:
            sheet.append(["", item["section"], "", "only right", item["id"], "", item["title"][:300]])
    wb.save(path)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", required=True)
    parser.add_argument("--out", default=str(Path(__file__).parent / "coverage" / "compare"))
    parser.add_argument("--budget", type=float, default=5.0)
    parser.add_argument("--only", default="", help="comma-separated comparison names")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    from jazzx_sdk.agents.service import AgentExecutionService

    agent = Tally(AgentExecutionService(), args.budget)
    Labels = _schema()
    proposals = [p for p in _fetch(_final_run_ids(Path(args.runs))) if p["kind"] == "rule"]
    py = {d: [_ours_python(p) for p in proposals if _doc(p) == d and _kind(p) == "python"]
          for d in ("standard", "platinum")}
    jt = {d: [_ours_jtbd(p) for p in proposals if _doc(p) == d and _kind(p) == "procedure"]
          for d in ("standard", "platinum")}
    acra = {d: _acra(d) for d in ("standard", "platinum")}
    plan = {
        "python_programs": (py["standard"], py["platinum"], "ours python standard", "ours python platinum"),
        "jtbd_programs": (jt["standard"], jt["platinum"], "ours jtbd standard", "ours jtbd platinum"),
        "acra_programs": (acra["standard"], acra["platinum"], "acra standard", "acra platinum"),
        "acra_vs_jtbd_std": (acra["standard"], jt["standard"], "acra standard", "ours jtbd standard"),
        "acra_vs_jtbd_plat": (acra["platinum"], jt["platinum"], "acra platinum", "ours jtbd platinum"),
    }
    wanted = {s for s in args.only.split(",") if s} or set(plan)
    results = {}
    for name, (left, right, ll, rl) in plan.items():
        if name not in wanted:
            continue
        r = await compare(agent, Labels, left, right)
        r.update(left=ll, right=rl)
        if name == "python_programs":
            r["number_deltas"] = _python_number_deltas(r["rows"], left, right)
        results[name] = r
        print(f"{name}: {len(left)} vs {len(right)} -> {r['left_best']}, right unmatched "
              f"{r['right_unmatched']}; cost so far ${agent.cost:.4f}", flush=True)
    results["cost"] = agent.summary()
    (out / "compare_sets.json").write_text(json.dumps(results, indent=1))
    _xlsx(results, out / "compare_sets.xlsx")
    print(agent.summary())


if __name__ == "__main__":
    asyncio.run(main())
