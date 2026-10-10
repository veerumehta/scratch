#!/usr/bin/env python3
"""R3 baseline: trial the generated Python rules over the seed's synthetic gold loans.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Reads the proposals through a Plato's API (read-only), runs `RuleTrialInvoker` in process on each
case of tests/data/dscr_gold_cases (records only: no documents, no model call), and writes an
aggregate report. The generated cases a rule carries are not used; this is what the rules do on
loans the pack's own gold decisions are known for.

    trial_baseline.py --out ape/local/mining      (from the japes checkout)
"""

from __future__ import annotations

import argparse
import asyncio
import collections
import json
import urllib.request
from pathlib import Path
from types import SimpleNamespace

from jazzx_sdk.fabric.canonical.local_executor import LocalPythonExecutor
from jazzx_sdk.fabric.graph.proposal import Proposal
from jazzx_sdk.pack.domain import load_materialized_pack
from jazzx_sdk.pack.rule_trial import TRIAL_ENTITY, RuleTrialInvoker

SET_POLICY = {"acra-standard": "DSCR_STANDARD", "acra-platinum": "DSCR_PLATINUM_SELECT"}


def fetch(base: str, pack: str, tenant: str) -> list[dict]:
    request = urllib.request.Request(f"{base}/authoring/review/{pack}/proposals?kind=rule&limit=5000",
                                     headers={"x-tenant-id": tenant})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8000/api/v1")
    parser.add_argument("--pack", default="acra-dscr-policy")
    parser.add_argument("--tenant", default="acra-lending")
    parser.add_argument("--seed", default="plato/data/seed_packs/acra_dscr_policy")
    parser.add_argument("--cases", default="tests/data/dscr_gold_cases")
    parser.add_argument("--out", default="mining")
    args = parser.parse_args()

    rows = [r for r in fetch(args.base, args.pack, args.tenant)
            if r["kind"] == "rule" and (r["rule"]["condition"] or {}).get("kind") == "python"]
    props = [Proposal.model_validate({k: r[k] for k in (
        "proposal_id", "kind", "rule", "category", "confidence", "reasoning")}) for r in rows]
    policy_of = {p.proposal_id: next(v for k, v in SET_POLICY.items() if p.proposal_id.startswith(k))
                 for p in props}
    pack = load_materialized_pack(Path(args.seed))

    async def pack_for(pack_id, version):
        return pack

    async def proposals_for(pack_id, ids):
        return [p for p in props if p.proposal_id in set(ids)]

    invoker = RuleTrialInvoker(pack_for, proposals_for=proposals_for,
                               python_executor=LocalPythonExecutor())
    entity = SimpleNamespace(entity_type=TRIAL_ENTITY, entity_id=pack.pack_id)
    cases = sorted(Path(args.cases).glob("*.json"))
    verdicts: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    missing: collections.Counter = collections.Counter()
    decision = collections.defaultdict(dict)
    per_case = collections.defaultdict(collections.Counter)
    unstated = 0
    violated_rows = 0
    for policy in sorted(set(policy_of.values())):
        ids = [p.proposal_id for p in props if policy_of[p.proposal_id] == policy]
        for case_path in cases:
            gold = json.loads(case_path.read_text())
            out = (await invoker.invoke(entity, SimpleNamespace(input=gold["loan_application"]),
                                        config={"proposal_ids": ids, "policy_id": policy})).output
            decision[policy][case_path.stem] = (out["published_allowed"], out["allowed"],
                                                gold["expected"].get("allowed"))
            for pid, row in out["proposals"].items():
                verdicts[pid][row["verdict"]] += 1
                per_case[case_path.stem][row["verdict"]] += 1
                missing.update(row["missing"])
                if row["verdict"] == "violated":
                    violated_rows += 1
                    unstated += any(r["value"] in (None, "", "unspecified") for r in row["reads"])

    total = sum(sum(c.values()) for c in verdicts.values())
    by_verdict = collections.Counter()
    for c in verdicts.values():
        by_verdict.update(c)
    always_ind = [pid for pid, c in verdicts.items() if set(c) == {"indeterminate"}]
    always_sat = [pid for pid, c in verdicts.items() if set(c) == {"satisfied"}]
    always_vio = [pid for pid, c in verdicts.items() if set(c) == {"violated"}]
    flips = {p: {c: d for c, d in cs.items() if d[0] != d[1]} for p, cs in decision.items()}
    report = [
        "# R3 baseline: the generated Python rules over the synthetic gold loans", "",
        f"{len(props)} Python proposals, trialled by policy over {len(cases)} gold loans "
        f"({', '.join(c.stem for c in cases)}), records only, no documents, no model call.", "",
        "## Verdicts", "",
        f"- (proposal, case) pairs: {total}; " + ", ".join(f"{v} {n} ({100 * n / total:.0f}%)"
                                                          for v, n in by_verdict.most_common()),
        f"- Proposals indeterminate on every case: {len(always_ind)}/{len(props)}",
        f"- Proposals satisfied on every case: {len(always_sat)}/{len(props)}; violated on every case: "
        f"{len(always_vio)}/{len(props)} (a rule that fails every loan, good or bad, is suspect)", "",
        f"- Violations resting on a read the loan leaves unspecified (None, blank, 'unspecified'): "
        f"{unstated} of {violated_rows}; the rest fail on stated values", "",
        "## Fields the rules needed and the loans did not supply", "",
    ]
    report += [f"- `{f}`: {n} (proposal, case) pairs" for f, n in missing.most_common(15)] or ["- none"]
    report += ["", "## Decision with and without the proposals overlaid", "",
               "Each row: published `allowed`, `allowed` with all of that policy's proposals, gold `allowed`.", ""]
    for policy, cs in sorted(decision.items()):
        report.append(f"- {policy}: " + "; ".join(f"{c}: {d[0]} -> {d[1]} (gold {d[2]})"
                                                    for c, d in sorted(cs.items())))
    report += ["", f"Cases whose decision the overlay changed: "
               f"{sum(len(v) for v in flips.values())} of {sum(len(v) for v in decision.values())}.",
               "", "## Per case (verdict counts over all proposals)", ""]
    report += [f"- {c}: {dict(n)}" for c, n in sorted(per_case.items())]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "r3_baseline.md").write_text("\n".join(report) + "\n")
    print("\n".join(report))


if __name__ == "__main__":
    asyncio.run(main())
