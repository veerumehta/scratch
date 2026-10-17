"""Collect the Acra material in one directory: the guideline documents, Acra's hand-built JTBDs, our
jobs and our code (from jobs on the trial pack, and segment-written from the 2026-10-11 runs), and
the comparison reports. Reads local Plato; writes nothing to it.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

    python acra_bundle.py [--out DIR] [--promote [--archive-as NAME]]
"""
from __future__ import annotations

import argparse
import json
import datetime
import shutil
from pathlib import Path

import httpx
import yaml

ROOT = Path("/Users/sangit/src/japes")
COVERAGE = Path(__file__).parent / "coverage"
API = "http://localhost:8000/api/v1"
HEAD = {"x-tenant-id": "acra-lending"}
DEFAULT_TRIAL, SOURCE = "acra-ledger-trial", "acra-dscr-policy"
TRIAL_POLICIES = {"standard": "policies/acra-standard.yaml", "platinum": "policies/acra-platinum.yaml"}
RUNS = COVERAGE / "runs_20261011.json"
TIMEOUT_SECONDS = 60
ARCHIVE_DIR = "archive"
BEST = ROOT / "docs" / "status" / "Acra" / "acra_bundle"
CANDIDATE = Path("/tmp/acra_bundle_candidate")
DOCS = ROOT / "documents" / "Acra"


def _get(http: httpx.Client, url: str, **params) -> httpx.Response:
    response = http.get(f"{API}{url}", params=params or None)
    response.raise_for_status()
    return response


def _rules(http: httpx.Client, path: str) -> list[dict]:
    content = _get(http, f"/packs/drafts/{TRIAL}", path=path).json()["content"]
    return [r for p in yaml.safe_load(content)["policies"] for r in p.get("rules", [])]


def _py_file(rule: dict, origin: str) -> str:
    cond = rule["condition"]
    head = [f"# rule: {rule.get('rule_id') or rule.get('name')}", f"# origin: {origin}",
            f"# description: {rule.get('description', '')}",
            f"# reads: {', '.join(cond.get('reads') or [])}"]
    if cond.get("derived_from"):
        head.append(f"# implements job: {cond['derived_from']}")
    return "\n".join(head) + "\n\n" + (cond.get("source") or "").rstrip() + "\n"


def _jobs_markdown(rules: list[dict], program: str) -> str:
    lines = [f"# Our jobs, {program} ({len(rules)})", ""]
    for r in rules:
        c = r["condition"]
        lines += [f"## {r['rule_id']}", "", f"**Purpose:** {c.get('purpose', '')}", ""]
        lines += [f"{i}. {s}" for i, s in enumerate(c.get("steps") or [], 1)]
        checks = c.get("checks") or []
        if checks:
            lines += ["", "**Checks:**"] + [f"- {x if isinstance(x, str) else json.dumps(x)}"
                                             for x in checks]
        if c.get("reads"):
            lines += ["", f"**Reads:** {', '.join(c['reads'])}"]
        if c.get("missing_reads"):
            lines += [f"**Missing data:** {', '.join(c['missing_reads'])}"]
        lines.append("")
    return "\n".join(lines)


def _promote(candidate: Path, best: Path, label: str | None) -> None:
    """Archive the current best as `archive/<label>`, then move the candidate's contents into `best`."""
    best.mkdir(parents=True, exist_ok=True)
    _archive_previous(best, label)
    for item in candidate.iterdir():
        shutil.move(str(item), best / item.name)


def _archive_previous(out: Path, label: str | None) -> None:
    """Move the current bundle into `archive/<label>` so `out` always holds the best-so-far."""
    present = [d for d in out.iterdir() if d.is_dir() and d.name != ARCHIVE_DIR]
    readme = out / "README.md"
    if not present and not readme.exists():
        return
    stamp = label or datetime.date.fromtimestamp((readme if readme.exists() else present[0]).stat().st_mtime).isoformat()
    target = out / ARCHIVE_DIR / stamp
    if target.exists():
        raise SystemExit(f"{target} exists; pass --archive-as with a new name")
    target.mkdir(parents=True)
    for item in [*present, *([readme] if readme.exists() else [])]:
        shutil.move(str(item), target / item.name)


def main() -> None:
    global TRIAL
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(CANDIDATE), help="where the candidate is built")
    parser.add_argument("--trial", default=DEFAULT_TRIAL, help="draft pack holding the jobs and code")
    parser.add_argument("--promote", action="store_true",
                        help="after building, archive the current best and replace it with this build")
    parser.add_argument("--archive-as", help="archive subfolder name for the bundle being replaced "
                        "(default: the date of its README)")
    args = parser.parse_args()
    out = Path(args.out)
    TRIAL = args.trial
    legacy = TRIAL == DEFAULT_TRIAL  # segment-written code and the 2026-10-11 comparisons belong to it
    dirs = {name: out / name for name in ("1_guidelines", "2_kstudio_jtbds", "3_sdk_jtbds",
                                          "4_sdk_code", "5_comparison")}
    shutil.rmtree(out, ignore_errors=True)
    for d in dirs.values():
        d.mkdir(parents=True)

    for f in DOCS.glob("*.docx"):
        shutil.copy2(f, dirs["1_guidelines"] / f.name.replace(" 1.docx", ".docx"))
    for f in DOCS.glob("acra_New_Guideline_JTBD*.json"):
        shutil.copy2(f, dirs["2_kstudio_jtbds"] / f.name)

    counts: dict[str, dict[str, int]] = {}
    with httpx.Client(timeout=TIMEOUT_SECONDS, headers=HEAD) as http:
        for program, path in TRIAL_POLICIES.items():
            rules = _rules(http, path)
            jobs = [r for r in rules if r["condition"].get("kind") == "procedure"]
            code = [r for r in rules if r["condition"].get("kind") == "python"]
            (dirs["3_sdk_jtbds"] / f"{program}_policy.yaml").write_text(
                yaml.safe_dump({"rules": rules}, sort_keys=False, allow_unicode=True))
            (dirs["3_sdk_jtbds"] / f"{program}_jobs.md").write_text(_jobs_markdown(jobs, program))
            target = dirs["4_sdk_code"] / "from_jobs" / program
            target.mkdir(parents=True)
            for r in code:
                (target / f"{'__'.join(r['rule_id'].split('.')[1:])}.py").write_text(_py_file(r, "written from a job"))
            counts[program] = {"jobs": len(jobs), "code_from_jobs": len(code)}
        exported = http.get(f"{API}/packs/drafts/{TRIAL}/jtbdset")
        if exported.status_code == 200:
            (dirs["3_sdk_jtbds"] / "jtbdset.json").write_text(json.dumps(exported.json(), indent=1))
        else:
            (dirs["3_sdk_jtbds"] / "jtbdset_REFUSED.txt").write_text(
                f"The export refused ({exported.status_code}): {exported.text}\n")
        (dirs["3_sdk_jtbds"] / "ledger.yaml").write_text(
            _get(http, f"/packs/drafts/{TRIAL}", path="ledger.yaml").json()["content"])
        (dirs["5_comparison"] / "coverage_trial.xlsx").write_bytes(
            _get(http, f"/packs/drafts/{TRIAL}/coverage", proposals="true", format="xlsx").content)

        if legacy:
            runs = {a["run_id"]: (job["document"], job["policy_id"])
                    for job in json.loads(RUNS.read_text()) if job["representation"] == "python"
                    for a in job["attempts"] if a["status"] == "succeeded"}
            proposals = _get(http, f"/authoring/review/{SOURCE}/proposals").json()
            for p in proposals:
                if p.get("run_id") not in runs or (p.get("rule") or {}).get("condition", {}).get("kind") != "python":
                    continue
                program = runs[p["run_id"]][0]
                target = dirs["4_sdk_code"] / "from_segments" / program
                target.mkdir(parents=True, exist_ok=True)
                rule = {**p["rule"], "name": p["name"]}
                (target / f"{'__'.join(p['name'].split('.')[1:])}.py").write_text(
                    _py_file(rule, f"written from a guideline segment, proposal {p['status']}"))
                counts[program]["code_from_segments"] = counts[program].get("code_from_segments", 0) + 1

    if legacy:
        for name in ("coverage_report.xlsx",):
            shutil.copy2(COVERAGE / name, dirs["5_comparison"] / "coverage_segments_vs_jobs.xlsx")
        for sub in ("compare", "compare_python_v2"):
            src = COVERAGE / "review_20261011" / sub / "compare_sets.xlsx"
            if src.exists():
                shutil.copy2(src, dirs["5_comparison"] / f"{sub}_vs_acra.xlsx")
        ledger_xlsx = COVERAGE / "ledger_live" / "coverage.xlsx"
        if ledger_xlsx.exists():
            shutil.copy2(ledger_xlsx, dirs["5_comparison"] / "coverage_trial_at_run.xlsx")

    (out / "README.md").write_text(_readme(counts, legacy))
    print(json.dumps(counts, indent=1))
    if args.promote:
        _promote(out, BEST, args.archive_as)
        print(f"promoted to {BEST}")
    else:
        print(f"candidate at {out}; compare with {BEST}, then rerun with --promote")


def _readme(counts: dict, legacy: bool) -> str:
    rows = "\n".join(f"| {p} | {c['jobs']} | {c['code_from_jobs']} |"
                     for p, c in counts.items())
    segments = ("- `4_sdk_code/from_segments/`: rules written directly from guideline segments (the 2026-10-11 runs),\n"
                "  a cross-check; most are proposals, not merged.\n") if legacy else ""
    return f"""# Acra DSCR: guidelines, hand-built JTBDs, our JTBDs and our code

Generated by `acra_bundle.py` from local Plato (trial pack `{TRIAL}`, proposals of `{SOURCE}`).

| Program | Our jobs | Code from jobs |
|---|---|---|
{rows}

- `1_guidelines/`: the two Acra consolidated guidelines (Standard, Platinum Select).
- `2_kstudio_jtbds/`: Acra's hand-built JTBD sets (123 Standard, 108 Platinum).
- `3_sdk_jtbds/`: our jobs per program, readable (`*_jobs.md`) and as rules (`*_policy.yaml`, jobs
  and code together); `jtbdset.json` is the export in the hand-built set's format; `ledger.yaml`
  links code to jobs.
- `4_sdk_code/from_jobs/`: one file per rule written from a job (header names the job).
{segments}- `5_comparison/`: coverage of the trial pack{", plus the segment-code and Acra-alignment comparisons" if legacy else ""}.

This folder is the current best; earlier versions are under `archive/`.
"""


if __name__ == "__main__":
    main()
