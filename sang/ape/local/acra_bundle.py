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
import tempfile
from collections import Counter
from pathlib import Path

import httpx
import yaml

from jazzx_sdk.pack.ledger import DISPOSITIONS

ROOT = Path("/Users/sangit/src/japes")
COVERAGE = Path(__file__).parent / "coverage"
API = "http://localhost:8000/api/v1"
HEAD = {"x-tenant-id": "acra-lending"}
DEFAULT_TRIAL, SOURCE = "acra-ledger-trial", "acra-dscr-policy"
TRIAL_POLICIES = {"standard": "policies/acra-standard.yaml", "platinum": "policies/acra-platinum.yaml"}
#: Our extraction policy of each program, and the file name its set is written under (Acra's two files, per program).
PROGRAM_POLICIES = {"standard": "acra-standard", "platinum_select": "acra-platinum"}
SET_FILES = {"standard": "jtbdset_standard.json", "platinum_select": "jtbdset_platinum_select.json"}
BUNDLE_FORMAT = 2
RUNS = COVERAGE / "runs_20261011.json"
TIMEOUT_SECONDS = 60
ARCHIVE_DIR = "archive"
BEST = ROOT / "docs" / "status" / "Acra" / "acra_bundle"
CANDIDATE = Path("/tmp/acra_bundle_candidate")
DOCS = ROOT / "documents" / "Acra"
REFERENCES = Path(__file__).parent / "acra_kstudio_references.yaml"


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


def _draft_pack(http: httpx.Client, trial: str):
    """The trial draft's files, loaded as a pack in this process (nothing is written to Plato)."""
    from jazzx_sdk.pack.domain import load_materialized_pack

    root = Path(tempfile.mkdtemp(prefix="acra_bundle_draft_"))
    for entry in _get(http, f"/packs/drafts/{trial}").json()["files"]:
        rel = entry["rel_path"]
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(_get(http, f"/packs/drafts/{trial}", path=rel).json()["content"])
    return load_materialized_pack(root)


def _stages(runs_json: Path | None, http: httpx.Client) -> dict:
    """Per stage of the generation: model, provider and prompt versions, read from the extraction runs' provenance."""
    if runs_json is None or not runs_json.is_file():
        return {}
    stages: dict[str, dict] = {}
    for job in json.loads(runs_json.read_text()):
        for attempt in job["attempts"]:
            if attempt.get("status") != "succeeded":
                continue
            run = http.get(f"{API}/authoring/extract/runs/{attempt['run_id']}").json()
            for step in run.get("provenance") or []:
                held = stages.setdefault(step["step"], {"model": step.get("model"), "provider": _provider(step.get("model")),
                                                         "prompt_versions": {}})
                held["prompt_versions"].update({r["name"]: r["version"] for r in step.get("prompts") or []})
    return stages


def _provider(model: str | None) -> str:
    """The provider a model id belongs to (the stages run through the OpenAI Agents SDK for the OpenAI models)."""
    name = (model or "").lower().removeprefix("flex_")
    return "openai (agents sdk)" if name.startswith(("gpt", "o1", "o3")) else "anthropic" if "claude" in name else "unknown"


def _references(dest: Path) -> list[dict]:
    """The K-Studio sets of `REFERENCES`, each copied into ``dest`` under its id and described: title, version, jobs, digest."""
    import hashlib

    rows = []
    for ref in yaml.safe_load(REFERENCES.read_text())["references"]:
        source = ROOT / ref["file"]
        data = source.read_bytes()
        held = json.loads(data)
        name = f"{ref['id']}.json"
        (dest / name).write_bytes(data)
        rows.append({"id": ref["id"], "program": ref["program"], "file": name, "title": held.get("title"),
                     "version": held.get("version"), "jobs": len(held.get("values") or []), "source": ref["source"],
                     "model": ref["model"], "received": ref["received"], "sha256": hashlib.sha256(data).hexdigest()})
    return rows


def _job_examples(http: httpx.Client, trial: str) -> dict | None:
    """The fingerprint of the trial draft's worked examples for the code writer (label, content digest, kinds, what did not
    load), None when the draft has none; a bundle with other examples is told apart by it."""
    from jazzx_sdk.pipelines.policy.job_examples import JOB_EXAMPLES_PATH, load_job_examples

    response = http.get(f"{API}/packs/drafts/{trial}", params={"path": JOB_EXAMPLES_PATH})
    if response.status_code != 200:
        return None
    content = (response.json() or {}).get("content")
    return load_job_examples(content).fingerprint() if content else None


def _metadata(label: str, trial: str, counts: dict, sets: dict, pack, stages: dict, http: httpx.Client) -> dict:
    from jazzx_sdk import __version__ as sdk_version
    from jazzx_sdk.pipelines.policy.ledger import is_job
    from jazzx_sdk.rules.lib import LIB_VERSION

    info = http.get(f"{API}/info").json() if http else {}
    within = sum(1 for s in sets.values() for c in Counter(v["mnemonic"] for v in s["values"]).values() if c > 1)
    shared = len(set.intersection(*({v["mnemonic"] for v in s["values"]} for s in sets.values()))) if sets else 0
    jobs = [r for p in pack.policies if p.policy_id in PROGRAM_POLICIES.values() for r in p.rules if is_job(r)]
    return {"bundle_format": BUNDLE_FORMAT, "version": label, "trial_pack_id": trial,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "sdk_version": sdk_version, "plato_version": ((info.get("versions") or {}).get("plato") if isinstance(info, dict) else None),
            "library_version": LIB_VERSION, "export_fix": True, "stages": stages,
            "job_examples": _job_examples(http, trial) if http else None,
            "counts": {"per_program": counts, "jobs": sum(len(s["values"]) for s in sets.values()),
                       "own_mnemonics": sum(1 for r in jobs if ((r.domain_extensions or {}).get("jtbd") or {}).get("mnemonic")),
                       "duplicate_mnemonics_within_a_set": within, "mnemonics_shared_by_both_programs": shared,
                       "computable_checks": sum(len(r.condition.computable_checks or []) for r in jobs),
                       "checks": sum(len(r.condition.checks) for r in jobs)}}


def _promote(candidate: Path, best: Path, label: str | None) -> None:
    """Archive the current best as `archive/<label>`, then move the candidate's contents into `best`."""
    best.mkdir(parents=True, exist_ok=True)
    _archive_previous(best, label)
    for item in candidate.iterdir():
        shutil.move(str(item), best / item.name)


HTML_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Acra DSCR bundle</title>
<style>
:root{color-scheme:light dark;--line:#8884}
body{font:16px/1.5 system-ui,sans-serif;max-width:60rem;margin:2rem auto;padding:0 1rem}
table{border-collapse:collapse;margin:1rem 0}
th,td{border:1px solid var(--line);padding:.3rem .7rem;text-align:left}
code{background:var(--line);padding:0 .25em;border-radius:3px}
</style></head><body>
{body}
</body></html>
"""


def _write_readme(path: Path, text: str) -> None:
    """Write the README and its HTML render beside it."""
    from markdown_it import MarkdownIt

    path.write_text(text)
    body = MarkdownIt("commonmark").enable("table").render(text)
    path.with_suffix(".html").write_text(HTML_PAGE.replace("{body}", body))


def _archive_previous(out: Path, label: str | None) -> None:
    """Move the current bundle into `archive/<label>` so `out` always holds the best-so-far."""
    present = [d for d in out.iterdir() if d.is_dir() and d.name != ARCHIVE_DIR]
    readme = out / "README.md"
    readme_html = out / "README.html"
    if not present and not readme.exists():
        return
    stamp = label or datetime.date.fromtimestamp((readme if readme.exists() else present[0]).stat().st_mtime).isoformat()
    target = out / ARCHIVE_DIR / stamp
    if target.exists():
        raise SystemExit(f"{target} exists; pass --archive-as with a new name")
    target.mkdir(parents=True)
    for item in [*present, *(f for f in (readme, readme_html) if f.exists())]:
        shutil.move(str(item), target / item.name)


def main() -> None:
    global TRIAL
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(CANDIDATE), help="where the candidate is built")
    parser.add_argument("--trial", default=DEFAULT_TRIAL, help="draft pack holding the jobs and code")
    parser.add_argument("--label", help="this bundle's version label (default: today's date)")
    parser.add_argument("--runs", type=Path, help="the regeneration's runs.json, for the stages' models and prompts")
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
        from jazzx_sdk.pack.jtbdset_export import export_program_sets

        pack = _draft_pack(http, TRIAL)
        label = args.label or datetime.date.today().isoformat()
        sets = export_program_sets(pack, version=label, programs=PROGRAM_POLICIES)
        for program, artifact in sets.items():
            (dirs["3_sdk_jtbds"] / SET_FILES[program]).write_text(json.dumps(artifact, indent=1))
        metadata = _metadata(label, TRIAL, counts, sets, pack, _stages(args.runs, http), http)
        metadata["kstudio_references"] = _references(dirs["2_kstudio_jtbds"])
        (out / "bundle.json").write_text(json.dumps(metadata, indent=2))
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

    _write_readme(out / "README.md", _readme(counts, legacy, out, BEST, BEST if BEST.exists() else None))
    print(json.dumps(counts, indent=1))
    if args.promote:
        _promote(out, BEST, args.archive_as)
        _write_readme(BEST / "README.md", _readme(counts, legacy, BEST, BEST))
        print(f"promoted to {BEST}")
    else:
        print(f"candidate at {out}; compare with {BEST}, then rerun with --promote")


def _facts(bundle: Path) -> dict | None:
    """The coverage workbook's headline numbers for one bundle, or None when it has none."""
    from openpyxl import load_workbook

    path = bundle / "5_comparison" / "coverage_trial.xlsx"
    if not path.exists():
        return None
    book = load_workbook(path, read_only=True)
    cells = {row[0]: row[1] for row in book["Summary"].iter_rows(values_only=True) if row and row[0]}
    loose = next((n for n in book.sheetnames if n.lower().endswith("without a job")), None)
    dispositions = {d: cells.get(d, 0) for d in DISPOSITIONS}
    return {"jobs": sum(dispositions.values()), "dispositions": dispositions,
            "share": cells.get("coded share"), "units": cells.get("units"), "checked": cells.get("units checked"),
            "loose": book[loose].max_row - 1 if loose else None}


def _history(best: Path, current: Path | None, previous: Path | None = None) -> str:
    """One row per archived bundle, oldest first, then the best being replaced (if any), then the current one."""
    rows = [(d.name, _facts(d)) for d in sorted((best / ARCHIVE_DIR).glob("*")) if d.is_dir()]
    if previous is not None:
        rows.append(("previous best", _facts(previous)))
    if current is not None:
        rows.append(("current", _facts(current)))
    lines = ["| Bundle | Jobs | Code | Code and procedure | Coded share | Clauses checked | Code rules without a job |",
             "|---|---|---|---|---|---|---|"]
    for name, f in rows:
        if f is None:
            continue
        d = f["dispositions"]
        checked = f"{f['checked']} of {f['units']}" if f["units"] else "n/a"
        share = f"{f['share']:.0%}" if f["share"] is not None else "n/a"
        lines.append(f"| {name} | {f['jobs']} | {d['code']} | {d['code_and_procedure']} | {share} | {checked} | "
                     f"{'n/a' if f['loose'] is None else f['loose']} |")
    return "\n".join(lines)


def _readme(counts: dict, legacy: bool, bundle: Path, best: Path, previous: Path | None = None) -> str:
    rows = "\n".join(f"| {p} | {c['jobs']} | {c['code_from_jobs']} |"
                     for p, c in counts.items())
    segments = ("- `4_sdk_code/from_segments/`: rules written directly from guideline segments (the 2026-10-11 runs),\n"
                "  a cross-check; most are proposals, not merged.\n") if legacy else ""
    facts = _facts(bundle)
    now = ""
    if facts:
        table = "\n".join(f"| {d} | {n} |" for d, n in facts["dispositions"].items())
        now = f"""
## This version, in numbers

| Disposition | Jobs |
|---|---|
{table}

Coded share {facts["share"]:.0%} (jobs code decides at least in part); {facts["checked"]} of {facts["units"]} guideline
clauses are checked by some job. `5_comparison/coverage_trial.xlsx` has the detail; its Legend sheet defines every column.
"""
    return f"""# Acra DSCR: guidelines, hand-built JTBDs, our JTBDs and our code

Generated by `acra_bundle.py` from local Plato (trial pack `{TRIAL}`, proposals of `{SOURCE}`).

| Program | Our jobs | Code from jobs |
|---|---|---|
{rows}

- `1_guidelines/`: the two Acra consolidated guidelines (Standard, Platinum Select).
- `2_kstudio_jtbds/`: Acra's hand-built JTBD sets (123 Standard, 108 Platinum).
- `3_sdk_jtbds/`: our jobs per program, readable (`*_jobs.md`) and as rules (`*_policy.yaml`, jobs
  and code together); `jtbdset_standard.json` and `jtbdset_platinum_select.json` are our jobs, one set per
  program, in the hand-built set's format (each job carries `rule_id` and `program`; `mnemonic` is the job's own
  family mnemonic where it has one); `ledger.yaml` links code to jobs. `bundle.json` says how this version was
  made (trial pack, date, models and prompts per stage, SDK, Plato and library versions, counts).
- `4_sdk_code/from_jobs/`: one file per rule written from a job (header names the job).
{segments}- `5_comparison/`: coverage of the trial pack{", plus the segment-code and Acra-alignment comparisons" if legacy else ""}.
{now}
## Terms

- **Job**: a requirement written as prose steps and checks that a person or an LLM follows (a JTBD).
- **Code rule**: a Python function over case fields that decides some of a job's checks.
- **Procedure**: what is left to the reviewer when no check is computable.
- A job is **code** when every check is computable and a rule implements it, **code_and_procedure** when code decides
  some checks and a reviewer the rest, **procedure** or **not_computable** when no check is computable (the latter
  names the data it lacks), **computable_no_code** when a check could be code and nobody wrote it, **unassessed** when
  nobody said which checks are computable.

## Code without a job

The sheet "Code rules without a job" lists code written from a guideline segment that no job is matched to, plus code
not yet matched. It is not expected to be empty or always the same size:

- Code written *from a job* always has one: it names the job it implements, one rule per job here, so code from jobs
  can never exceed the jobs and cannot be an orphan. Jobs outnumber it because a job with no computable check gets no
  code (the not_computable and procedure rows above).
- Code written *from segments* (the cross-check pipeline) has no such guarantee. A rule left without a job means the
  job list lacks a requirement the segment code enforces, or the code is spurious. Its count tells how complete the
  job list is, not how good the code is. Segment code also matches jobs the job-written code did not reach, which is
  why jobs coded can exceed the code written from jobs.
- Action: write the job (the ledger can propose one from the rule's text) or drop the rule.

## History

{_history(best, bundle, previous)}

Earlier bundles are under `archive/`; each has its own README and comparison files.
"""


if __name__ == "__main__":
    main()
