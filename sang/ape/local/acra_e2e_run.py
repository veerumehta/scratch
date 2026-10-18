"""Run one case record through the five variants of the Acra end-to-end comparison and write the report.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Variants on the same record: V1 K-Studio jobs (jobs_only), V2 our jobs (jobs_only), V3 our code (code_only),
V4 hybrid, V5 both. Packs come from `acra_e2e_packs.py`. The record is the extracted case (a JSON object of
facts); its values never reach the report, which holds counts, rule ids and field names. Spend is metered:
a variant stops asking the model at ``--variant-budget`` and the run stops at ``--total-budget``.

    python scripts/local/acra_e2e_run.py --case CASE.json --out DIR [--pairs pairs.json] [--golden-conditions N]
    python scripts/local/acra_e2e_run.py --dry-run --out DIR        # synthetic record, scripted model, no spend
    python scripts/local/acra_e2e_run.py --plato URL --tenant T ... # assess through a Plato that holds the two packs
                                                                    # (`--publish` stores them first; `--no-reason` skips jobs)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

from jazzx_sdk.agents.metering import CallMeter, use_meter
from jazzx_sdk.fabric.canonical.local_executor import LocalPythonExecutor
from jazzx_sdk.pack import Pack
from jazzx_sdk.pack.assessment import AssessmentOutcome, assess

PACKS = Path("/Users/sangit/src/.scratch/sang/ape/local/acra_e2e/packs")
SYNTHETIC = Path("/Users/sangit/src/japes/tests/data/dscr_gold_cases/double_cap.json")
VARIANTS = [("V1 K-Studio jobs", "acra-e2e-kstudio", "jobs_only"), ("V2 our jobs", "acra-e2e-ours", "jobs_only"),
            ("V3 our code", "acra-e2e-ours", "code_only"), ("V4 hybrid", "acra-e2e-ours", "hybrid"),
            ("V5 both", "acra-e2e-ours", "both")]
DEFAULT_VARIANT_BUDGET = 8.0
DEFAULT_TOTAL_BUDGET = 30.0
DECIDED = {AssessmentOutcome.PASS.value: "pass", AssessmentOutcome.FAIL.value: "fail",
           AssessmentOutcome.NOT_APPLICABLE.value: "not_applicable"}
OPEN_CONDITIONS = {AssessmentOutcome.PENDING_EVIDENCE.value, AssessmentOutcome.PENDING_CALCULATION.value,
                   AssessmentOutcome.WAIVER_REQUIRED.value, AssessmentOutcome.PRE_REVIEW_REQUIRED.value}
PAIR_RELATIONS = ("same", "differs")
#: The refusal that names a fact the record omits, and the most facts the harness will state as null for a pack.
OMITTED_FACT = re.compile(r"the input omits ([A-Za-z0-9_.]+),")
#: The refusal of a null for a fact that cannot be null. A numeric or boolean one is stated as the neutral value so
#: the rest can be measured; the report lists these as synthetic, and rules reading them are not to be trusted.
NULL_REFUSED = re.compile(r"the input gives null for ([A-Za-z0-9_.]+),")
PLACEHOLDERS = {"integer": 0, "number": 0, "boolean": False}
MAX_OMITTED_FACTS = 400
CLIENT_TIMEOUT_SECONDS = 3600.0


class BudgetExceeded(RuntimeError):
    """The variant's model spend reached its ceiling; further calls are refused."""


class _Budgeted:
    """A reasoning agent that refuses further calls once ``meter`` shows ``limit`` dollars spent."""

    def __init__(self, inner: Any, meter: CallMeter, limit: float) -> None:
        self.inner, self.meter, self.limit, self.stopped = inner, meter, limit, False

    async def run(self, **kwargs: Any) -> Any:
        if self.meter.total()["cost_usd"] >= self.limit:
            self.stopped = True
            raise BudgetExceeded(f"variant budget {self.limit} reached")
        return await self.inner.run(**kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner, name)


class _ScriptedJobs:
    """Dry run: every job passes, no model."""

    async def run(self, *, output_type: Any, **_: Any) -> Any:
        return output_type(status="PASS", rationale="scripted"), None, None


def _reasoning(dry_run: bool) -> Any:
    if dry_run:
        return _ScriptedJobs()
    from jazzx_sdk.agents.reasoning.agent import ReasoningAgent
    from jazzx_sdk.agents.service import AgentExecutionService
    from jazzx_sdk.llm.config import resolve_model

    return ReasoningAgent(AgentExecutionService(), model=resolve_model())


def _class_of(outcome: str) -> str:
    return DECIDED.get(outcome, "undecided")


def _reads(pack: Any) -> dict[str, list[str]]:
    """rule id -> the facts it reads, across the pack's policies."""
    found: dict[str, list[str]] = {}
    for policy in pack.policies:
        for rule in policy.rules:
            found[rule.rule_id] = list(getattr(rule.condition, "reads", None) or [])
    return found


def _flat(record: Any, prefix: str = "") -> set[str]:
    """The dotted names a record states (a nested object contributes ``Entity.field``)."""
    if isinstance(record, dict):
        return {name for key, value in record.items() for name in
                ({f"{prefix}{key}"} | _flat(value, f"{prefix}{key}."))}
    return set()


def _why(rule: str, outcome: str, assessment: Any, reads: dict[str, list[str]], stated: set[str]) -> str:
    missing = sorted(f for f in reads.get(rule, []) if f not in stated)
    if missing:
        return "missing data: " + ", ".join(missing[:4]) + (" ..." if len(missing) > 4 else "")
    if rule in assessment.withheld:
        return "withheld: the job was not run (no model, or the budget)" if not assessment.reasoned \
            else "withheld: the job could not be judged"
    engine = assessment.engines.get(rule)
    if engine is not None and engine.kind == "python" and outcome == AssessmentOutcome.UNABLE_TO_EVALUATE.value:
        return "code unevaluable"
    return f"no evidence: {outcome}"


async def _assess(pack: Any, pack_id: str, mode: str, inputs: dict[str, Any], *, dry_run: bool, budget: float,
                  programs: str | None, plato: Any, reason: bool, meter: CallMeter, reasoning: Any) -> Any:
    """The assessment, in this process or through Plato (whose model spend the response reports)."""
    if plato is None:
        with use_meter(meter):
            return await assess(pack, inputs, python_executor=LocalPythonExecutor(), reasoning_agent=reasoning,
                                engine_mode=mode, programs=programs)
    from jazzx_sdk.pack.assessment import PolicyAssessment

    body = await plato.assess(pack_id, inputs, programs=programs, reason=reason, engine_mode=mode)
    meter.usage_from_server = body.get("usage") or {}
    return PolicyAssessment.model_validate(body)


def _fact_type(packs: Path, pack_id: str, name: str) -> str | None:
    schema = json.loads((packs / pack_id / "schemas" / "loan_application.json").read_text())
    return (schema.get("properties", {}).get(name) or {}).get("type")


async def state_omitted_facts(plato: Any, pack_id: str, inputs: dict[str, Any], programs: str | None,
                              packs: Path) -> tuple[dict[str, Any], list[str]]:
    """``inputs`` with every fact the pack's rules read but the record omits stated as null, and those facts.

    The assessment refuses an omitted fact and names one at a time; each is the extraction not stating a fact a rule
    reads. A fact that cannot be null stops the loop (the refusal then names something else) and is returned as is."""
    from jazzx_plato_client.client import PlatoError

    filled, omitted = dict(inputs), []
    while len(omitted) < MAX_OMITTED_FACTS:
        try:
            await plato.assess(pack_id, filled, programs=programs, engine_mode="code_only")
            break
        except PlatoError as exc:
            detail = str(exc.detail)
            found = OMITTED_FACT.search(detail)
            if exc.status_code == 422 and found and found.group(1) not in filled:
                filled[found.group(1)] = None
                omitted.append(found.group(1))
                continue
            refused = NULL_REFUSED.search(detail)
            kind = _fact_type(packs, pack_id, refused.group(1)) if refused else None
            if exc.status_code == 422 and refused and kind in PLACEHOLDERS:
                filled[refused.group(1)] = PLACEHOLDERS[kind]
                omitted.append(f"{refused.group(1)} (not nullable: stated as {PLACEHOLDERS[kind]!r} to measure)")
                continue
            omitted.append(f"REFUSED: {detail[:200]}")
            break
    return filled, omitted


async def run_variant(name: str, pack: Any, mode: str, inputs: dict[str, Any], *, dry_run: bool, budget: float,
                      programs: str | None, pack_id: str = "", plato: Any = None, reason: bool = True) -> dict[str, Any]:
    meter = CallMeter()
    meter.usage_from_server = None
    reasoning = _Budgeted(_reasoning(dry_run and plato is None), meter, budget)
    started = time.monotonic()
    error = ""
    try:
        result = await _assess(pack, pack_id, mode, inputs, dry_run=dry_run, budget=budget, programs=programs,
                               plato=plato, reason=reason, meter=meter, reasoning=reasoning)
    except Exception as exc:  # noqa: BLE001 -- a failed variant is a row of the report, not the end of the run
        return {"name": name, "mode": mode, "error": f"{type(exc).__name__}: {exc}", "programs": {},
                "seconds": round(time.monotonic() - started, 1), "usage": meter.total()}
    reads, stated = _reads(pack), _flat(inputs)
    per_program = result.programs or {result.program or "default": result}
    summary: dict[str, Any] = {}
    for program, assessment in per_program.items():
        outcomes = {r: o.value for r, o in assessment.outcomes.items()}
        classes = Counter(_class_of(o) for o in outcomes.values())
        undecided = {r: _why(r, o, assessment, reads, stated) for r, o in outcomes.items() if _class_of(o) == "undecided"}
        summary[program] = {
            "rules": len(outcomes), "classes": dict(classes), "outcomes": outcomes, "undecided": undecided,
            "withheld": len(assessment.withheld), "open_conditions": sorted(r for r, o in outcomes.items() if o in OPEN_CONDITIONS),
            "decided_by": dict(Counter(assessment.decided_by.values())),
            "engine_summary": assessment.engine_summary.model_dump() if assessment.engine_summary else {},
            "comparison": [row.model_dump() for row in assessment.comparison],
            "fields_read": sorted({f for r in outcomes for f in reads.get(r, [])}),
            "fields_missing": sorted({f for r in outcomes for f in reads.get(r, []) if f not in stated}),
            "assessment_error": error}
    return {"name": name, "mode": mode, "error": error, "programs": summary, "stopped_on_budget": reasoning.stopped,
            "seconds": round(time.monotonic() - started, 1),
            "usage": meter.usage_from_server if meter.usage_from_server is not None else meter.total()}


def agreement(results: dict[str, dict[str, Any]], pairs: dict[str, Any] | None) -> dict[str, Any]:
    """K-Studio's V1 outcome against our V2 outcome on each paired requirement, per program."""
    if not pairs:
        return {}
    kstudio, ours = results.get("V1 K-Studio jobs"), results.get("V2 our jobs")
    if not kstudio or not ours:
        return {}
    out: dict[str, Any] = {}
    for program, data in pairs.items():
        if program == "cost":
            continue
        name = next((k for k in kstudio["programs"] if k.startswith(program[:4])), "")
        left = kstudio["programs"].get(name, {}).get("outcomes", {})
        right = next((v["outcomes"] for k, v in ours["programs"].items() if k.startswith(program[:4])), {})
        tally: Counter[str] = Counter()
        for pair in data["pairs"]:
            # An imported overlay job is named for its program (`MNEMONIC.program`).
            mine = next((i for i in (pair["kstudio"], f"{pair['kstudio']}.{name}") if i in left), None)
            if pair["relation"] not in PAIR_RELATIONS or mine is None or pair["ours"] not in right:
                continue
            a, b = _class_of(left[mine]), _class_of(right[pair["ours"]])
            tally["both undecided" if a == b == "undecided" else "one undecided" if "undecided" in (a, b)
                  else "agree" if a == b else "disagree"] += 1
        out[program] = dict(tally)
    return out


def write_report(report: dict[str, Any], out: Path) -> None:
    from openpyxl import Workbook

    book = Workbook()
    sheet = book.active
    sheet.title = "Summary"
    sheet.append(["variant", "program", "rules", "pass", "fail", "not applicable", "undecided", "withheld",
                  "open conditions", "decided by code", "decided by job", "cost usd", "seconds", "error"])
    for v in report["variants"]:
        for program, p in (v["programs"] or {"": {}}).items():
            c = p.get("classes", {})
            sheet.append([v["name"], program, p.get("rules"), c.get("pass", 0), c.get("fail", 0),
                          c.get("not_applicable", 0), c.get("undecided", 0), p.get("withheld"),
                          len(p.get("open_conditions", [])), p.get("decided_by", {}).get("code", 0),
                          p.get("decided_by", {}).get("job", 0), v["usage"]["cost_usd"], v["seconds"], v["error"]])
    why = book.create_sheet("Undecided")
    why.append(["variant", "program", "rule", "why"])
    for v in report["variants"]:
        for program, p in v["programs"].items():
            for rule, reason in p["undecided"].items():
                why.append([v["name"], program, rule, reason])
    ready = book.create_sheet("Readiness")
    ready.append(["variant", "program", "fields read", "fields missing", "missing"])
    for v in report["variants"]:
        for program, p in v["programs"].items():
            ready.append([v["name"], program, len(p["fields_read"]), len(p["fields_missing"]), ", ".join(p["fields_missing"])])
    both = book.create_sheet("Code vs job")
    both.append(["program", "job", "code rules", "code", "job verdict", "agree"])
    for v in report["variants"]:
        if v["mode"] == "both":
            for program, p in v["programs"].items():
                for row in p["comparison"]:
                    both.append([program, row["job_id"], ", ".join(row["code_rules"]), row["code_verdict"],
                                 row["job_verdict"], row["agree"]])
    agree = book.create_sheet("Agreement")
    agree.append(["program", "result", "pairs"])
    for program, tally in report["agreement"].items():
        for kind, count in tally.items():
            agree.append([program, kind, count])
    book.save(out / "e2e_report.xlsx")
    lines = ["# Acra end to end: variants on one case record", "",
             f"Total model spend: {report['total_cost_usd']} USD. Counts only; no loan values.", "",
             "| variant | program | rules | decided | undecided | open conditions | cost | s |", "|---|---|---|---|---|---|---|---|"]
    for v in report["variants"]:
        for program, p in (v["programs"] or {"": {}}).items():
            c = p.get("classes", {})
            decided = sum(c.get(k, 0) for k in ("pass", "fail", "not_applicable"))
            lines.append(f"| {v['name']} | {program} | {p.get('rules', '')} | {decided} | {c.get('undecided', 0)} | "
                         f"{len(p.get('open_conditions', []))} | {v['usage']['cost_usd']} | {v['seconds']} |")
    if report["agreement"]:
        lines += ["", "Agreement of V1 and V2 on paired requirements: " + json.dumps(report["agreement"])]
    (out / "e2e_report.md").write_text("\n".join(lines) + "\n")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--case", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--packs", type=Path, default=PACKS)
    parser.add_argument("--pairs", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--plato", help="assess through this Plato (the packs published in --tenant)")
    parser.add_argument("--tenant", default="acra-lending")
    parser.add_argument("--publish", action="store_true", help="with --plato: publish the two scratch packs first")
    parser.add_argument("--no-reason", action="store_true", help="with --plato: jobs are withheld, no model")
    parser.add_argument("--variant-budget", type=float, default=DEFAULT_VARIANT_BUDGET)
    parser.add_argument("--total-budget", type=float, default=DEFAULT_TOTAL_BUDGET)
    args = parser.parse_args()
    if not args.dry_run and not args.case:
        parser.error("--case is required unless --dry-run")
    args.out.mkdir(parents=True, exist_ok=True)
    inputs = (json.loads(SYNTHETIC.read_text())["loan_application"] if args.dry_run
              else json.loads(args.case.read_text()))
    programs = None if inputs.get("program_id") else "all"
    pairs = json.loads(args.pairs.read_text()) if args.pairs else None

    results: dict[str, dict[str, Any]] = {}
    spent = 0.0
    plato = None
    stated: dict[str, tuple[dict[str, Any], list[str]]] = {}
    if args.plato:
        from jazzx_plato_client import PlatoClient
        from jazzx_sdk.pack.store import pack_archive

        plato = await PlatoClient(args.plato, tenant_id=args.tenant, timeout=CLIENT_TIMEOUT_SECONDS).__aenter__()
        if args.publish:
            for pack_id in dict.fromkeys(p for _, p, _ in VARIANTS):
                published = await plato.publish_pack(pack_archive(args.packs / pack_id), name=f"{pack_id}.zip",
                                                     notes="scratch pack of the end-to-end run")
                print(f"published {pack_id}: {published.get('version')}")
    try:
        for name, pack_id, mode in VARIANTS:
            if spent >= args.total_budget:
                print(f"stopped: total budget {args.total_budget} reached before {name}")
                break
            pack = Pack.from_manifest(pack_id, args.packs)
            case_inputs = inputs
            if plato is not None and pack_id not in stated:
                stated[pack_id] = await state_omitted_facts(plato, pack_id, inputs, programs, args.packs)
                print(f"{pack_id}: {len(stated[pack_id][1])} fact(s) the record omits", flush=True)
            if plato is not None:
                case_inputs = stated[pack_id][0]
            results[name] = await run_variant(
                name, pack, mode, case_inputs, dry_run=args.dry_run, pack_id=pack_id, plato=plato,
                reason=not args.no_reason, budget=min(args.variant_budget, args.total_budget - spent), programs=programs)
            spent += results[name]["usage"]["cost_usd"]
            print(f"{name}: {results[name]['error'] or 'ok'}; cost {results[name]['usage']['cost_usd']}", flush=True)
    finally:
        if plato is not None:
            await plato.__aexit__(None, None, None)
    report = {"variants": list(results.values()), "agreement": agreement(results, pairs),
              "omitted_facts": {pack_id: omitted for pack_id, (_, omitted) in stated.items()},
              "total_cost_usd": round(spent, 4)}
    (args.out / "e2e_report.json").write_text(json.dumps(report, indent=1))
    write_report(report, args.out)


if __name__ == "__main__":
    asyncio.run(main())
