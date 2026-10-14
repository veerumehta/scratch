"""The Acra JTBD ledger, live, on a trial pack: copy the draft, merge jobs, write code from them,
align segment code, and read coverage (local Plato; the real acra-dscr-policy draft is not touched).

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Phases, each its own command so a long one can run in the background and the next resume after it:

    python acra_ledger_live.py copy          # open TRIAL from the acra-dscr-policy draft
    python acra_ledger_live.py seed          # or: open TRIAL from the japes seed folder
    (ACRA_TRIAL and ACRA_DIR choose the trial pack id and the output directory)
    python acra_rerun_extractions.py --pack acra-ledger-trial --out <DIR>/runs.json   # 4 extractions
    python acra_ledger_live.py merge-jobs    # approve and merge the runs' jobs into each policy
    python acra_ledger_live.py code          # job runs per policy, then approve and merge their code
    python acra_ledger_live.py align         # alignment over every policy, proposing orphan jobs
    python acra_ledger_live.py coverage      # coverage (with proposals) as JSON and xlsx, summarised

State (runs started, counts) is kept in ``<DIR>/state.json``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx

API = "http://localhost:8000/api/v1"
HEAD = {"x-tenant-id": "acra-lending"}
SOURCE = "acra-dscr-policy"
TRIAL = os.environ.get("ACRA_TRIAL", "acra-ledger-trial")
SEED = Path("/Users/sangit/src/japes/plato/data/seed_packs/acra_dscr_policy")
POLICIES = {"acra-standard": "Acra Standard DSCR (jobs)", "acra-platinum": "Acra Platinum Select DSCR (jobs)"}
DIR = Path(os.environ.get("ACRA_DIR", Path(__file__).parent / "coverage" / "ledger_live"))
POLL_SECONDS = 30
TERMINAL = {"succeeded", "failed", "cancelled"}
TIMEOUT_SECONDS = 120


def _state() -> dict:
    path = DIR / "state.json"
    return json.loads(path.read_text()) if path.exists() else {}


def _save(state: dict) -> None:
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / "state.json").write_text(json.dumps(state, indent=1))


def _check(response: httpx.Response) -> dict:
    if response.status_code >= 400:
        sys.exit(f"{response.request.method} {response.request.url}: {response.status_code} {response.text[:500]}")
    return response.json()


def _wait(http: httpx.Client, run_id: str) -> dict:
    while True:
        run = _check(http.get(f"{API}/authoring/extract/runs/{run_id}"))
        if run["status"] in TERMINAL:
            cost = round(sum(u.get("cost_usd", 0) for u in (run.get("usage") or {}).values()), 4)
            print(f"  run {run_id[:8]} {run['representation']} {run['policy_id'] or '*'}: {run['status']}, "
                  f"{run['segments']} parts, {len(run['failed_segments'])} failed, {run['proposals']} "
                  f"proposed, ${cost}{'; ' + run['error'] if run.get('error') else ''}", flush=True)
            return run
        time.sleep(POLL_SECONDS)


def copy(http: httpx.Client) -> None:
    """TRIAL opened empty, then every file of SOURCE's draft written into it with the pack id swapped."""
    _check(http.post(f"{API}/packs/drafts/{TRIAL}", json={}))
    files = _check(http.get(f"{API}/packs/drafts/{SOURCE}"))["files"]
    for entry in files:
        path = entry["rel_path"]
        content = _check(http.get(f"{API}/packs/drafts/{SOURCE}", params={"path": path}))["content"]
        _check(http.put(f"{API}/packs/drafts/{TRIAL}",
                        json={"rel_path": path, "content": content.replace(SOURCE, TRIAL)}))
    print(f"copied {len(files)} files from {SOURCE} into {TRIAL}")


def seed(http: httpx.Client) -> None:
    """TRIAL opened empty, then every text file of the japes seed folder written into it with the pack
    id swapped: a fresh start from the synced seed rather than from the tenant's draft."""
    _check(http.post(f"{API}/packs/drafts/{TRIAL}", json={}))
    written = 0
    for path in sorted(SEED.rglob("*")):
        rel = path.relative_to(SEED).as_posix()
        if not path.is_file() or rel == "SYNCED_FROM" or path.suffix not in {".yaml", ".yml", ".json", ".md"}:
            continue
        _check(http.put(f"{API}/packs/drafts/{TRIAL}",
                        json={"rel_path": rel, "content": path.read_text().replace(SOURCE, TRIAL)}))
        written += 1
    print(f"wrote {written} seed files into {TRIAL}")


def _approve_and_merge(http: httpx.Client, representation: str, run_ids: dict[str, list[str]]) -> dict:
    """Approve the proposals of each policy's runs and merge them into that policy of TRIAL."""
    merged = {}
    for policy_id, runs in run_ids.items():
        for run_id in runs:
            decided = _check(http.post(f"{API}/authoring/review/{TRIAL}/decisions", json={
                "trigger": "approve", "kind": "rule", "representation": representation, "run_id": run_id}))
            print(f"  {policy_id} run {run_id[:8]}: {json.dumps(decided)[:200]}")
            result = _check(http.post(f"{API}/authoring/review/{TRIAL}/merge-rules", json={
                "policy_id": policy_id, "name": POLICIES[policy_id], "representation": representation,
                "run_id": run_id}))
            merged.setdefault(policy_id, []).append(result)
            print(f"  merged into {policy_id}: {json.dumps(result)[:300]}")
    return merged


def merge_jobs(http: httpx.Client) -> None:
    runs = json.loads((DIR / "runs.json").read_text())
    run_ids: dict[str, list[str]] = {}
    for job in runs:
        if job["representation"] == "jtbd":
            # Each attempt is a whole extraction, and job names vary between runs, so merging two
            # attempts doubles the jobs: take the last that succeeded.
            done = [a["run_id"] for a in job["attempts"] if a["status"] == "succeeded"]
            if done:
                run_ids.setdefault(job["policy_id"], []).append(done[-1])
    state = _state()
    state["jobs_merged"] = _approve_and_merge(http, "jtbd", run_ids)
    _save(state)


def code(http: httpx.Client) -> None:
    state = _state()
    run_ids = {}
    for policy_id in POLICIES:
        run = _check(http.post(f"{API}/authoring/extract/{TRIAL}/job-runs", json={"policy_id": policy_id}))
        run_ids[policy_id] = run["run_id"]
        print(f"job run {run['run_id']} for {policy_id}", flush=True)
    finished = {p: _wait(http, r) for p, r in run_ids.items()}
    state["job_runs"] = {p: {k: run[k] for k in ("run_id", "status", "segments", "proposals",
                                                  "failed_segments", "error")}
                         for p, run in finished.items()}
    state["code_merged"] = _approve_and_merge(
        http, "python", {p: [r["run_id"]] for p, r in finished.items() if r["status"] == "succeeded"})
    _save(state)


def align(http: httpx.Client) -> None:
    state = _state()
    run = _check(http.post(f"{API}/authoring/extract/{TRIAL}/alignment-runs",
                           json={"policy_id": "", "propose_jobs": True}))
    print(f"alignment run {run['run_id']}", flush=True)
    done = _wait(http, run["run_id"])
    state["alignment"] = {k: done[k] for k in ("run_id", "status", "segments", "proposals",
                                               "failed_segments", "error")}
    _save(state)


def coverage(http: httpx.Client) -> None:
    report = _check(http.get(f"{API}/packs/drafts/{TRIAL}/coverage", params={"proposals": "true"}))
    (DIR / "coverage.json").write_text(json.dumps(report, indent=1))
    workbook = http.get(f"{API}/packs/drafts/{TRIAL}/coverage", params={"proposals": "true", "format": "xlsx"})
    (DIR / "coverage.xlsx").write_bytes(workbook.content)
    merged = [j for j in report["jobs"] if not j["pending"]]
    print("all jobs:", report["counts"], "coded share", report["coded_share"])
    print("merged jobs only:", {d: sum(1 for j in merged if j["disposition"] == d) for d in report["counts"]})
    print("by policy:", report["by_policy"])
    print("orphans", len(report["orphans"]), "unaligned", len(report["unaligned"]))
    print("schema backlog:", [(g["data"], g["jobs"]) for g in report["schema_backlog"][:10]])
    print("disagreements:", sum(1 for j in report["jobs"] if j["disagreements"]),
          "jobs with unprinted figures:", sum(1 for j in report["jobs"] if j["unprinted"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("copy", "seed", "merge-jobs", "code", "align", "coverage"))
    args = parser.parse_args()
    with httpx.Client(timeout=TIMEOUT_SECONDS, headers=HEAD) as http:
        {"copy": copy, "seed": seed, "merge-jobs": merge_jobs, "code": code, "align": align,
         "coverage": coverage}[args.phase](http)


if __name__ == "__main__":
    main()
