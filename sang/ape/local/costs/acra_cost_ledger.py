"""Acra cost ledger: every recorded model cost of the Acra work, per-unit rates, and a pack-cost forecast.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Collects, re-runnable at any time (rows are rebuilt from their sources, so nothing double counts):
- Plato extraction runs of the Acra packs (usage per step, duration, parts, proposals);
- Plato eval experiments of the tenant (usage per experiment, cases);
- local analysis reports under ``ape/local/coverage`` (the ``cost`` block each writes);
- ``acra_costs_manual.csv``: whatever no system records (agent sessions, people's hours, a script's
  printed cost). Add rows there by hand; the columns are its header.

Writes ``acra_costs.csv`` (the ledger) and ``acra_costs.xlsx``: Ledger, Summary, Rates (median cost,
time and calls per unit of work) and Forecast (inputs for a new pack, formulas over Rates).

    python acra_cost_ledger.py
"""

from __future__ import annotations

import csv
import json
import re
import statistics
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

HERE = Path(__file__).parent
LOCAL = HERE.parent
API = "http://localhost:8000/api/v1"
TENANT = "acra-lending"
PACKS = ("acra-dscr-policy", "dscr-core")
DOCS = Path("/Users/sangit/src/japes/documents/Acra")
#: Which guideline document each extraction policy reads.
POLICY_DOCS = {
    "acra-standard": ["Acra_DSCR_Standard_Consolidated_Guidelines_v1_0.docx"],
    "acra-platinum": ["Acra_DSCR_Platinum_Select_Consolidated_Guidelines_v1_0 1.docx"],
    "catalog": ["Acra_DSCR_Standard_Consolidated_Guidelines_v1_0.docx",
                "Acra_DSCR_Platinum_Select_Consolidated_Guidelines_v1_0 1.docx"],
}
MANUAL = HERE / "acra_costs_manual.csv"
COLUMNS = ["date", "category", "activity", "source_id", "model", "calls", "input_tokens",
           "output_tokens", "cached_tokens", "reasoning_tokens", "cost_usd", "cost_is_upper_bound",
           "minutes", "work_units", "unit", "outputs", "output_kind", "doc_words", "status", "notes"]


def _words(name: str) -> int:
    with zipfile.ZipFile(DOCS / name) as z:
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
    return len(re.sub(r"<[^>]+>", " ", xml).split())


def _minutes(start: str | None, end: str | None) -> float | None:
    if not start or not end:
        return None
    parse = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))  # noqa: E731
    return round((parse(end) - parse(start)).total_seconds() / 60, 1)


def _usage_sum(usage: dict) -> dict:
    keys = ("calls", "input_tokens", "output_tokens", "cached_tokens", "reasoning_tokens", "cost_usd")
    total = {k: sum((u.get(k) or 0) for u in usage.values()) for k in keys}
    total["cost_is_upper_bound"] = any(u.get("cost_is_upper_bound") for u in usage.values())
    total["model"] = ",".join(sorted({u.get("model", "") for u in usage.values() if u.get("model")}))
    return total


def extraction_rows(http: httpx.Client, words: dict[str, int]) -> list[dict]:
    rows = []
    for pack in PACKS:
        runs = http.get(f"{API}/authoring/extract/{pack}/runs").json()
        for run in runs if isinstance(runs, list) else []:
            u = _usage_sum(run.get("usage") or {})
            docs = POLICY_DOCS.get(run["policy_id"], [])
            rows.append({
                "date": run["started_at"][:10], "category": "extraction",
                "activity": f"extract {run['representation']}", "source_id": run["run_id"],
                **{k: u[k] for k in ("model", "calls", "input_tokens", "output_tokens", "cached_tokens",
                                     "reasoning_tokens", "cost_usd", "cost_is_upper_bound")},
                "minutes": _minutes(run.get("started_at"), run.get("finished_at")),
                "work_units": run["segments"], "unit": "parts", "outputs": run["proposals"],
                "output_kind": "proposals", "doc_words": sum(words.get(d, 0) for d in docs),
                "status": run["status"],
                "notes": f"{pack} {run['policy_id']}; {len(run['failed_segments'])} parts failed"
                         + (f"; {run['error'][:80]}" if run.get("error") else "")})
    return rows


def eval_rows(http: httpx.Client) -> list[dict]:
    rows = []
    for exp in http.get(f"{API}/eval/experiments").json():
        s = exp.get("summary") or {}
        u = s.get("usage") or {}
        rows.append({
            "date": (exp.get("created_at") or "")[:10], "category": "evaluation",
            "activity": f"eval {exp['entity']['entity_type']}", "source_id": exp["experiment_id"],
            "model": "", **{k: u.get(k) for k in ("calls", "input_tokens", "output_tokens",
                                                   "cached_tokens", "reasoning_tokens", "cost_usd",
                                                   "cost_is_upper_bound")},
            "minutes": _minutes(exp.get("started_at"), exp.get("completed_at")),
            "work_units": s.get("total"), "unit": "cases", "outputs": s.get("passed"),
            "output_kind": "passed", "doc_words": None, "status": exp.get("status"),
            "notes": f"{exp['name']}; pass rate {s.get('pass_rate')}"})
    return rows


def _items(report: dict) -> int:
    if "documents" in report:   # a coverage report: jobs plus rules aligned
        return sum(d["jobs"] + d["python_rules"] for d in report["documents"])
    return sum(v.get("left_items", 0) for k, v in report.items() if isinstance(v, dict) and k != "cost")


def analysis_rows() -> list[dict]:
    rows = []
    for path in sorted((LOCAL / "coverage").rglob("*.json")):
        report = json.loads(path.read_text())
        cost = report.get("cost") if isinstance(report, dict) else None
        if not isinstance(cost, dict) or "cost_usd" not in cost:
            continue
        kind = "coverage" if path.name.startswith("coverage") else "comparison"
        rows.append({
            "date": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d"),
            "category": "analysis", "activity": f"review {kind}",
            "source_id": str(path.relative_to(LOCAL)), "model": "",
            **{k: cost.get(k) for k in ("calls", "input_tokens", "output_tokens", "cost_usd",
                                         "cost_is_upper_bound")},
            "minutes": None, "work_units": _items(report), "unit": "items", "outputs": None,
            "output_kind": "", "doc_words": None, "status": "done",
            "notes": "stopped on budget" if cost.get("stopped_on_budget") else ""})
    return rows


def manual_rows() -> list[dict]:
    if not MANUAL.exists():
        MANUAL.write_text(",".join(COLUMNS) + "\n")
        return []
    with MANUAL.open() as f:
        return [{**row, "category": row.get("category") or "manual"} for row in csv.DictReader(f)]


def _num(value) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def rates(rows: list[dict]) -> list[dict]:
    """Median per-unit figures by activity, over completed rows with a cost."""
    out = []
    for activity in sorted({r["activity"] for r in rows}):
        done = [r for r in rows if r["activity"] == activity and r["status"] in ("succeeded", "completed", "done")
                and _num(r["cost_usd"])]
        if not done:
            continue

        def med(fn):
            vals = [v for v in (fn(r) for r in done) if v is not None]
            return round(statistics.median(vals), 6) if vals else None

        out.append({
            "activity": activity, "rows": len(done),
            "cost_per_row": med(lambda r: _num(r["cost_usd"])),
            "minutes_per_row": med(lambda r: _num(r["minutes"])),
            "cost_per_unit": med(lambda r: _num(r["cost_usd"]) / _num(r["work_units"])
                                 if _num(r["work_units"]) else None),
            "unit": done[0]["unit"],
            "cost_per_1k_words": med(lambda r: 1000 * _num(r["cost_usd"]) / _num(r["doc_words"])
                                     if _num(r["doc_words"]) else None),
            "minutes_per_1k_words": med(lambda r: 1000 * _num(r["minutes"]) / _num(r["doc_words"])
                                        if _num(r["doc_words"]) and _num(r["minutes"]) else None),
            "outputs_per_1k_words": med(lambda r: 1000 * _num(r["outputs"]) / _num(r["doc_words"])
                                        if _num(r["doc_words"]) and _num(r["outputs"]) is not None else None),
            "total_cost": round(sum(_num(r["cost_usd"]) for r in done), 4)})
    return out


def workbook(rows: list[dict], rate_rows: list[dict], words: dict[str, int], path: Path) -> None:
    from openpyxl import Workbook

    wb = Workbook()
    ledger = wb.active
    ledger.title = "Ledger"
    ledger.append(COLUMNS)
    for r in rows:
        ledger.append([r.get(c) for c in COLUMNS])

    summary = wb.create_sheet("Summary")
    summary.append(["category", "activity", "rows", "cost_usd", "minutes"])
    keys = sorted({(r["category"], r["activity"]) for r in rows})
    for cat, act in keys:
        sel = [r for r in rows if (r["category"], r["activity"]) == (cat, act)]
        summary.append([cat, act, len(sel), round(sum(_num(r["cost_usd"]) or 0 for r in sel), 4),
                        round(sum(_num(r["minutes"]) or 0 for r in sel), 1)])
    summary.append(["all", "", len(rows), round(sum(_num(r["cost_usd"]) or 0 for r in rows), 4),
                    round(sum(_num(r["minutes"]) or 0 for r in rows), 1)])
    summary.append([])
    summary.append(["guideline document", "words"])
    for name, n in words.items():
        summary.append([name, n])

    rate = wb.create_sheet("Rates")
    head = ["activity", "rows", "cost_per_row", "minutes_per_row", "cost_per_unit", "unit",
            "cost_per_1k_words", "minutes_per_1k_words", "outputs_per_1k_words", "total_cost"]
    rate.append(head)
    where = {}
    for i, r in enumerate(rate_rows, start=2):
        rate.append([r[h] for h in head])
        where[r["activity"]] = i

    # Forecast: inputs in column B, formulas over Rates; edit the inputs.
    fc = wb.create_sheet("Forecast")
    col = {h: chr(ord("A") + i) for i, h in enumerate(head)}

    def ref(activity: str, field: str) -> str:
        return f"Rates!${col[field]}${where[activity]}" if activity in where else "0"

    fc.append(["input", "value", "note"])
    inputs = [("guideline words (all documents)", sum(words.values()), "the Acra pair, as a default"),
              ("guideline documents (programs)", 2, ""),
              ("extraction attempts per document per representation", 2, "one retry when a part fails"),
              ("eval cases", 5, "Acra gold set size today"),
              ("eval iterations", 10, "experiments while tuning the pack (11 so far for Acra)"),
              ("review items (jobs and rules compared)", 1000, "this review compared about 1000")]
    for name, value, note in inputs:
        fc.append([name, value, note])
    fc.append([])
    fc.append(["forecast", "cost_usd", "minutes (flex tier; runs in parallel pairs)"])
    for rep in ("extract jtbd", "extract python", "extract catalog"):
        attempts = "$B$4" if rep != "extract catalog" else "1"
        fc.append([f"{rep}",
                   f"=$B$2/1000*{ref(rep, 'cost_per_1k_words')}*{attempts}",
                   f"=$B$2/1000*{ref(rep, 'minutes_per_1k_words')}*{attempts}/$B$3"])
    fc.append(["evaluation", f"=$B$6*$B$5*{ref('eval case_run', 'cost_per_unit')}",
               f"=$B$6*{ref('eval case_run', 'minutes_per_row')}"])
    fc.append(["review (coverage + comparisons)",
               f"=$B$7*AVERAGE({ref('review coverage', 'cost_per_unit')},{ref('review comparison', 'cost_per_unit')})",
               ""])
    last = fc.max_row
    fc.append(["total model cost", f"=SUM(B10:B{last})", f"=SUM(C10:C{last})"])
    fc.append([])
    fc.append(["Not in this forecast: agent sessions (Claude Code) and people's hours; add them to "
               "acra_costs_manual.csv to bring them into Rates."])
    wb.save(path)


def main() -> None:
    words = {name: _words(name) for docs in POLICY_DOCS.values() for name in docs}
    with httpx.Client(timeout=30, headers={"x-tenant-id": TENANT}) as http:
        rows = extraction_rows(http, words) + eval_rows(http) + analysis_rows() + manual_rows()
    rows.sort(key=lambda r: (r["date"] or "", r["category"], r["activity"]))
    with (HERE / "acra_costs.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    rate_rows = rates(rows)
    workbook(rows, rate_rows, words, HERE / "acra_costs.xlsx")
    total = sum(_num(r["cost_usd"]) or 0 for r in rows)
    print(f"{len(rows)} rows, ${total:.4f} recorded; words {words}")
    for r in rate_rows:
        print(r)


if __name__ == "__main__":
    main()
