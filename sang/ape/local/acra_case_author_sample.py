"""Measure the independent case author on the same jobs: the regen-4b jobs, code written once with the flag off and once on.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

    python acra_case_author_sample.py --jobs 10 [--policies acra-standard acra-platinum]

Two trial packs are opened from the regen-4b draft (the same merged jobs); the same codable jobs are sent to the code writer in
each, the second with ``independent_cases: true``. Prints counts and cost only. Policy documents only: no loan file is read.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx
import yaml

HERE = Path(__file__).parent
SOURCE = "acra-regen-4b"
CODABLE = {"code", "code_and_procedure"}
COVERAGE = HERE / "coverage" / "regen_4b" / "coverage.json"
RESULT = HERE / "coverage" / "case_author_sample.json"


def pick(per_policy: int, policies: list[str]) -> dict[str, list[str]]:
    jobs = json.loads(COVERAGE.read_text())["jobs"]
    return {p: sorted(j["job_id"] for j in jobs if j["policy_id"] == p and j["disposition"] in CODABLE)[:per_policy]
            for p in policies}


def run_trial(trial: str, flag: bool, chosen: dict[str, list[str]]) -> dict:
    os.environ["ACRA_TRIAL"], os.environ["ACRA_DIR"] = trial, str(HERE / "coverage" / trial)
    sys.path.insert(0, str(HERE))
    import acra_ledger_live as L

    L.SOURCE, L.TRIAL, L.DIR = SOURCE, trial, HERE / "coverage" / trial
    http = httpx.Client(headers=L.HEAD, timeout=L.TIMEOUT_SECONDS)
    L.copy(http)
    if flag:
        template = L._check(http.get(f"{L.API}/packs/drafts/{trial}", params={"path": L.TEMPLATE}))["content"]
        body = yaml.safe_load(template) or {}
        body["independent_cases"] = True
        L._check(http.put(f"{L.API}/packs/drafts/{trial}", json={"rel_path": L.TEMPLATE,
                                                                  "content": yaml.safe_dump(body, sort_keys=False)}))
    out = {"policies": {}}
    for policy_id, jobs in chosen.items():
        run = L._check(http.post(f"{L.API}/authoring/extract/{trial}/job-runs",
                                 json={"policy_id": policy_id, "jobs": jobs}))
        finished = L._wait(http, run["run_id"])
        cost = round(sum(u.get("cost_usd", 0) for u in (finished.get("usage") or {}).values()), 4)
        calls = sum(u.get("calls", 0) for u in (finished.get("usage") or {}).values())
        out["policies"][policy_id] = {"jobs": len(jobs), "status": finished["status"], "proposals": finished["proposals"],
                                      "failed": len(finished["failed_segments"]), "cost_usd": cost, "calls": calls,
                                      "run_id": finished["run_id"]}
        L._approve_and_merge(http, "python", {policy_id: [finished["run_id"]]})
    out["extensions"] = ledger_counts(http, L, trial)
    return out


def ledger_counts(http, L, trial: str) -> dict:
    """Counts of the independent-case keys over the trial's code rules (no rule text)."""
    rules = cases = mismatching = 0
    for entry in L._check(http.get(f"{L.API}/packs/drafts/{trial}"))["files"]:
        if not entry["rel_path"].startswith("policies/"):
            continue
        text = L._check(http.get(f"{L.API}/packs/drafts/{trial}", params={"path": entry["rel_path"]}))["content"]
        for policy in (yaml.safe_load(text) or {}).get("policies", []):
            for rule in policy.get("rules", []):
                ledger = ((rule.get("domain_extensions") or {}).get("ledger")) or {}
                if "independent_cases" in ledger:
                    rules, cases = rules + 1, cases + ledger["independent_cases"]
                    mismatching += 1 if ledger.get("independent_case_mismatches") else 0
    return {"code_rules_with_independent_cases": rules, "cases": cases, "rules_with_a_mismatch": mismatching}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=10, help="codable jobs in all, split across the policies")
    parser.add_argument("--policies", nargs="*", default=["acra-standard", "acra-platinum"])
    args = parser.parse_args()
    per_policy = max(1, args.jobs // len(args.policies))
    chosen = pick(per_policy, args.policies)
    result = {"jobs": {p: len(j) for p, j in chosen.items()},
              "off": run_trial("acra-casing-off", False, chosen), "on": run_trial("acra-casing-on", True, chosen)}
    RESULT.write_text(json.dumps(result, indent=1))
    print(json.dumps({k: v for k, v in result.items()}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
