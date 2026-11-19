#!/usr/bin/env python3
"""Per-job baseline of Acra code generation from one regeneration's stored coverage report. Reads files only; no Plato, no model.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

usage: acra_baseline_by_job.py [coverage_dir, default coverage/regen_5 beside this repo's local root] [--out CSV]

A job is "coded" when its disposition is `code` or `code_and_procedure` (the share the regen log calls coded_share). Each job gets a cause class:
a coded job is `ok`, or flagged for an unprinted figure, a disagreement the aligner raised, or a read the case schema does not supply (the rule
answers unknown at run time); a job without code is classed from the reads it names as missing. The classes are a keyword reading of those
reads, so they are a first cut for a person to correct, not a verdict.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

LOCAL = Path(__file__).resolve().parents[2]
DEFAULT_DIR = LOCAL / "coverage" / "regen_5"
CODED = ("code", "code_and_procedure")

#: Cause classes (the order is the order a non-coded job is tested in).
POLICY = "other: the guideline needs an Acra answer or text it does not reproduce"
DERIVED = "missing function or derived field: a figure or rate the case does not carry"
EVIDENCE = "extraction gap: document evidence the case schema has no field for"
FACT = "extraction gap: a yes/no fact or attribute absent from the case schema"
ALIGN = "other: computable, no code linked (an orphan rule or an alignment miss)"
PROCEDURE = "other: a procedure by design"

_ASK_ACRA = re.compile(
    r"Acra['’]?s? (confirmation|determination|decision|approval|conformity|vetting|acceptab)|confirmation requested|sole discretion|"
    r"not reproduced|definition|meaning of|Legal requires|interacts|combines? with|Senior Management|Q-\d+|which score is|whether .*means", re.I)
_DERIVED = re.compile(
    r"\b(DSCR|DTI|LTV|CLTV|PITIA|calculated|annual (interest|principal|real estate|property|in-place|homeowner)|reserves (amount|are|months)|"
    r"months of|number of months|age of|first payment|maturity date|exchange rate|rating|ratio|percent)\b", re.I)
_EVIDENCE = re.compile(
    r"^(evidence|documentation|documents?|copy|certificate|executed|original|two \(2\)|english|trust|formation|operating|power of|ssa|pra|title|"
    r"letter|information (to|establishing)|proof|entity|ownership|identification|any |written|all-member|applicable|authorized|international|seller'?s)",
    re.I)


def classify(job: dict, unsupplied: set[str], rules_reads: dict[str, list[str]]) -> tuple[str, str]:
    """(state, cause class) for one coverage job row."""
    disposition = job["disposition"]
    if disposition in CODED:
        flags = []
        if job["unprinted"]:
            flags.append("a figure the code writes is not in the job text")
        if job["disagreements"]:
            flags.append("the aligner disagrees with the job")
        if any(read in unsupplied for rule in job["rules"] for read in rules_reads.get(rule, [])):
            flags.append("the rule reads a field the case does not supply")
        return ("coded, flagged" if flags else "coded", "; ".join(flags) or "ok")
    missing = job["missing_reads"]
    if disposition == "computable_no_code":
        return "not coded", ALIGN
    if disposition == "procedure":
        return "not coded", PROCEDURE
    if any(_ASK_ACRA.search(read) for read in missing):
        return "not coded", POLICY
    if any(_DERIVED.search(read) for read in missing):
        return "not coded", DERIVED
    if any(_EVIDENCE.match(read.strip()) for read in missing):
        return "not coded", EVIDENCE
    return "not coded", FACT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("coverage_dir", nargs="?", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    report = json.loads((args.coverage_dir / "coverage.json").read_text(encoding="utf-8"))
    unsupplied = {row["data"] for row in report["unsupplied_reads"]}
    rules_reads = _rules_reads(args.coverage_dir)
    rows, tally = [], Counter()
    for job in report["jobs"]:
        state, cause = classify(job, unsupplied, rules_reads)
        tally[(state, cause)] += 1
        rows.append({"job_id": job["job_id"], "kind": job["kind"], "disposition": job["disposition"], "state": state, "cause": cause,
                     "checks": job["checks"], "missing_reads": " | ".join(job["missing_reads"])})
    out = args.out or args.coverage_dir / "baseline_by_job.csv"
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    total = len(rows)
    coded = sum(1 for row in rows if row["state"].startswith("coded"))
    print(f"{total} jobs; coded {coded} ({coded / total:.1%}), flagged among them {sum(1 for r in rows if r['state'] == 'coded, flagged')}")
    for (state, cause), count in sorted(tally.items(), key=lambda item: (-item[1], item[0])):
        print(f"{count:4}  {state:15} {cause}")
    print(f"wrote {out}")
    return 0


def _rules_reads(coverage_dir: Path) -> dict[str, list[str]]:
    """Rule id to the fields it reads, from the exported rule files beside the status bundle when they are there."""
    bundle = LOCAL.parent / "status" / "Acra" / "acra_bundle" / "4_sdk_code" / "from_jobs"
    reads: dict[str, list[str]] = {}
    for path in bundle.glob("*/*.py") if bundle.is_dir() else ():
        text = path.read_text(encoding="utf-8")
        rule = re.search(r"# rule: (\S+)", text)
        line = re.search(r"# reads: (.*)", text)
        if rule and line:
            reads[rule.group(1)] = [item.strip() for item in line.group(1).split(",")]
    return reads


if __name__ == "__main__":
    sys.exit(main())
