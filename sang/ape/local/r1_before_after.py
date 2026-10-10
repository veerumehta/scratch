#!/usr/bin/env python3
"""R1 measurement: regenerate the generated Python rules with the library prompt, trial both sets.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Reads the python proposals through a Plato's API (read-only), writes each clause again with
`PythonExtractor` (the current prompt: library API, safe reads, unknown) under a hard spend ceiling,
caches the results so a re-run spends nothing, then runs `RuleTrialInvoker` in process over the
synthetic gold loans for the old and the new rules and reports the difference. The rule text is
policy, not borrower data.

    r1_before_after.py --ceiling 10 --out ape/local/mining      (from the japes checkout)
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import collections
import json
import re
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import yaml

SET_POLICY = {"acra-standard": "DSCR_STANDARD", "acra-platinum": "DSCR_PLATINUM_SELECT"}
CONCURRENCY = 4


def fetch(base: str, pack: str, tenant: str) -> list[dict]:
    request = urllib.request.Request(f"{base}/authoring/review/{pack}/proposals?kind=rule&limit=5000",
                                     headers={"x-tenant-id": tenant})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def norm(value):
    if not isinstance(value, str):
        return value
    return " ".join(value.replace("_", " ").replace("-", " ").split()).casefold()


async def regenerate(rows, template, ceiling: float, cache: Path) -> tuple[dict, float, list]:
    from jazzx_sdk.agents.metering import CallMeter, use_meter
    from jazzx_sdk.agents.reasoning.agent import ReasoningAgent
    from jazzx_sdk.agents.service import AgentExecutionService
    from jazzx_sdk.llm.config import resolve_model
    from jazzx_sdk.pipelines.policy_code import PythonExtractor
    from jazzx_sdk.pipelines.policy_extract import ClauseSegment

    done = json.loads(cache.read_text()) if cache.exists() else {}
    meter = CallMeter()
    spent = lambda: sum(u.cost_usd for u in meter.usage().values())  # noqa: E731
    extractor = PythonExtractor(ReasoningAgent(AgentExecutionService(), model=resolve_model()),
                                reads=template.reads, policy_id="acra", units=template.units)
    gate = asyncio.Semaphore(CONCURRENCY)
    failures: list = []

    async def one(row):
        pid = row["proposal_id"]
        if pid in done:
            return
        async with gate:
            if spent() >= ceiling:
                failures.append((pid, "ceiling reached"))
                return
            rule_id = row["rule"]["rule_id"]
            segment = ClauseSegment(text=row["excerpt"] or row["reasoning"], marker=rule_id)
            try:
                candidate = await extractor._generate(segment, rule_id=rule_id,
                                                      citations=list(row["rule"].get("citations") or []),
                                                      derived_from=None)
            except Exception as exc:  # noqa: BLE001 - recorded, not retried: the spend is the point
                failures.append((pid, f"{type(exc).__name__}: {str(exc)[:160]}"))
                return
            done[pid] = candidate.rule.model_dump(mode="json")
            cache.write_text(json.dumps(done))

    with use_meter(meter):
        await asyncio.gather(*(one(r) for r in rows))
    return done, spent(), failures


async def trial(props, policy_of, seed, cases_dir):
    from jazzx_sdk.fabric.canonical.local_executor import LocalPythonExecutor
    from jazzx_sdk.pack.domain import load_materialized_pack
    from jazzx_sdk.pack.rule_trial import TRIAL_ENTITY, RuleTrialInvoker

    pack = load_materialized_pack(Path(seed))

    async def pack_for(pack_id, version):
        return pack

    async def proposals_for(pack_id, ids):
        return [p for p in props if p.proposal_id in set(ids)]

    invoker = RuleTrialInvoker(pack_for, proposals_for=proposals_for,
                               python_executor=LocalPythonExecutor())
    entity = SimpleNamespace(entity_type=TRIAL_ENTITY, entity_id=pack.pack_id)
    out: dict = {"rows": collections.defaultdict(list), "decision": collections.defaultdict(dict)}
    for policy in sorted(set(policy_of.values())):
        ids = [p.proposal_id for p in props if policy_of[p.proposal_id] == policy]
        for case_path in sorted(Path(cases_dir).glob("*.json")):
            gold = json.loads(case_path.read_text())
            result = (await invoker.invoke(
                entity, SimpleNamespace(input=gold["loan_application"]),
                config={"proposal_ids": ids, "policy_id": policy})).output
            out["decision"][policy][case_path.stem] = (
                result["published_allowed"], result["allowed"], gold["expected"].get("allowed"))
            for pid, row in result["proposals"].items():
                out["rows"][pid].append({"case": case_path.stem, **row})
    return out


def shares(rows) -> dict:
    counts = collections.Counter(r["verdict"] for rs in rows.values() for r in rs)
    total = sum(counts.values()) or 1
    return {k: (counts.get(k, 0), round(100 * counts.get(k, 0) / total)) for k in
            ("satisfied", "violated", "indeterminate", "not_applicable")} | {"total": total}


def always_violated(rows) -> list[str]:
    return [pid for pid, rs in rows.items() if rs and {r["verdict"] for r in rs} == {"violated"}]


def classify(source: str, rs: list[dict]) -> str:
    """Why an always-violated rule failed: an enum value spelled another way, a read the loan leaves
    unstated, or a stated value past a threshold."""
    constants = {c.value for c in ast.walk(ast.parse(source)) if isinstance(c, ast.Constant)
                 and isinstance(c.value, str)}
    values = [r["value"] for row in rs for r in row["reads"] if isinstance(r["value"], str)]
    if any(v != c and norm(v) == norm(c) for v in values for c in constants):
        return "enum_spelling"
    if any(r["value"] in (None, "", "unspecified", "unknown") for row in rs for r in row["reads"]):
        return "unstated_read"
    return "stated_value"


async def main() -> None:
    from jazzx_sdk.fabric.graph.proposal import Proposal
    from jazzx_sdk.pipelines.policy_jtbd import JtbdTemplate

    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8000/api/v1")
    parser.add_argument("--pack", default="acra-dscr-policy")
    parser.add_argument("--tenant", default="acra-lending")
    parser.add_argument("--seed", default="plato/data/seed_packs/acra_dscr_policy")
    parser.add_argument("--cases", default="tests/data/dscr_gold_cases")
    parser.add_argument("--ceiling", type=float, required=True, help="USD; the run stops at it")
    parser.add_argument("--out", default="mining")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = [r for r in fetch(args.base, args.pack, args.tenant)
            if r["kind"] == "rule" and (r["rule"]["condition"] or {}).get("kind") == "python"]
    template = JtbdTemplate.model_validate(
        yaml.safe_load((Path(args.seed) / "jtbd_template.yaml").read_text()))
    new_rules, spent, failures = await regenerate(rows, template, args.ceiling,
                                                  out / "r1_regenerated.json")

    def props(use_new: bool):
        found = []
        for r in rows:
            data = {k: r[k] for k in ("proposal_id", "kind", "rule", "category", "confidence", "reasoning")}
            if use_new and r["proposal_id"] in new_rules:
                data["rule"] = new_rules[r["proposal_id"]]
            found.append(Proposal.model_validate(data))
        return found

    policy_of = {r["proposal_id"]: next(v for k, v in SET_POLICY.items() if r["proposal_id"].startswith(k))
                 for r in rows}
    old_props, new_props = props(False), [p for p in props(True) if p.proposal_id in new_rules]
    before = await trial(old_props, policy_of, args.seed, args.cases)
    after = await trial(new_props, policy_of, args.seed, args.cases)
    old_src = {p.proposal_id: p.rule.condition.source for p in old_props}

    same_ids = {p.proposal_id for p in new_props}
    before_same = {k: v for k, v in before["rows"].items() if k in same_ids}
    s_before, s_after = shares(before_same), shares(after["rows"])
    stuck = [pid for pid in always_violated(before["rows"])]
    causes = collections.Counter(classify(old_src[pid], before["rows"][pid]) for pid in stuck)
    after_of_stuck = collections.Counter(
        ("still violated" if pid in always_violated(after["rows"])
         else "not regenerated" if pid not in after["rows"] else "changed")
        for pid in stuck)
    after_verdicts_of_stuck = collections.Counter(
        r["verdict"] for pid in stuck for r in after["rows"].get(pid, []))
    library = sum("import rules_lib" in r["condition"]["source"] for r in new_rules.values())
    unknown = sum("rules_lib.unknown" in r["condition"]["source"] for r in new_rules.values())
    flips = lambda d: "; ".join(  # noqa: E731
        f"{p}: " + ", ".join(f"{c} {v[0]}->{v[1]}" for c, v in sorted(cs.items())
                             if c in ("clean_pass", "band_boundary"))
        for p, cs in sorted(d["decision"].items()))
    fmt = lambda s: ", ".join(f"{k} {v[0]} ({v[1]}%)" for k, v in s.items() if k != "total")  # noqa: E731
    report = [
        "# R1 before and after: regenerating the generated Python rules with the library prompt", "",
        f"{len(rows)} rules; regenerated {len(new_rules)}; spent ${spent:.4f} of a ${args.ceiling} ceiling; "
        f"{len(failures)} not regenerated" + (f" ({'; '.join(f'{p}: {why}' for p, why in failures[:5])})" if failures else "") + ".",
        f"Regenerated rules importing `rules_lib`: {library}; using `unknown`: {unknown}.", "",
        "## Verdict shares over (rule, gold loan) pairs, the regenerated rules only", "",
        f"- before: {fmt(s_before)} of {s_before['total']}",
        f"- after:  {fmt(s_after)} of {s_after['total']}", "",
        "## The rules that violated every loan before",  "",
        f"- {len(stuck)} rules. Why they failed (by what the rule's own reads and constants show): {dict(causes)}",
        f"- After regeneration, of those: {dict(after_of_stuck)}; their verdicts now: {dict(after_verdicts_of_stuck)}", "",
        "## Decision with and without the overlay (published -> with all of a policy's rules)", "",
        f"- before: {flips(before)}", f"- after:  {flips(after)}", "",
        "Gold for clean_pass and band_boundary is `allowed`.",
    ]
    (out / "r1_before_after.md").write_text("\n".join(report) + "\n")
    (out / "r1_before_after.json").write_text(json.dumps({"before": before["rows"], "after": after["rows"]},
                                                          default=str))
    print("\n".join(report))


if __name__ == "__main__":
    asyncio.run(main())
