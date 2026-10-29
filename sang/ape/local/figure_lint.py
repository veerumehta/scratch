"""Report figures a guideline clause prints that none of its linked jobs state.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

A clause counts as covered when any linked job cites it, even when the job
leaves out the clause's percentages, dollar amounts, durations, ratios or FICO
scores. This reads three files and lists, per clause, the figures that appear in
the clause text but in no linked job (skill, requirement text, loan metrics).

  clauses.json   {"PLAT-7.1": "clause text ...", ...}
  jobs.json      a jtbdset export ({"values": [...]}) or a bare list of jobs
  links.json     {"PLAT-7.1": ["job mnemonic", ...], ...}

Usage: figure_lint.py clauses.json jobs.json links.json [--csv out.csv]

Citation tags, section references and open-question ids are removed before the
figures are read, so "[G 5.32, p. 3]" and "Q-08" do not count as figures.
Figures are compared as a set per clause, so a figure stated by any linked job
counts for all of them.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

REFERENCE = re.compile(
    r"\[[^\]]*\]|§\s?[\d.]+(\([A-Za-z0-9]\))?|\b(PLAT|STD)-[\d.]+( to \d+\.\d+)?|\bQ-\d+|\bpp?\. ?\d+"
)
UNIT_ALIASES = {"mos": "month", "mo": "month", "months": "month", "days": "day", "years": "year",
                "yr": "year", "tradelines": "tradeline", "trade lines": "tradeline", "trade line": "tradeline"}
MAX_RATIO = 10
FICO_FLOOR, FICO_CEIL = 500, 899
SCALES = {"mm": 1e6, "m": 1e6, "million": 1e6, "k": 1e3}


def figures(text: str) -> set[str]:
    """Normalized figures in `text`: dollars, percents, durations, ratios and FICO scores."""
    text = REFERENCE.sub("", text).replace(",", "")
    found: set[str] = set()
    for m in re.finditer(r"\$\s?(\d+(?:\.\d+)?)\s?(MM|M|K|million)?(?![A-Za-z])", text, re.I):
        found.add("$%g" % (float(m.group(1)) * SCALES.get((m.group(2) or "").lower(), 1)))
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s?(?:%|percent|percentage)", text):
        found.add("%g%%" % float(m.group(1)))
    for m in re.finditer(r"(\d+)\s?[- ]?(months?|mos?|days?|years?|yr|tradelines?|trade lines?|business days)\b",
                         text, re.I):
        unit = m.group(2).lower()
        found.add(f"{int(m.group(1))} {UNIT_ALIASES.get(unit, unit)}")
    for m in re.finditer(r"(?<![\d.$])(\d\.\d{1,3})(?![\d%])", text):
        if float(m.group(1)) < MAX_RATIO:
            found.add("ratio%g" % float(m.group(1)))
    for m in re.finditer(r"\b(\d{3})\b", text):
        if FICO_FLOOR <= int(m.group(1)) <= FICO_CEIL:
            found.add("fico" + m.group(1))
    return found


def job_text(job: dict) -> str:
    parts = [job.get("skill", "")]
    parts += [r.get("requirement_text", "") for r in job.get("requirements", [])]
    parts += [f"{m.get('label', '')} {m.get('indicator_context', '')}" for m in job.get("loan_metrics", [])]
    return " ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("clauses")
    ap.add_argument("jobs")
    ap.add_argument("links")
    ap.add_argument("--csv", help="write the rows to this file")
    args = ap.parse_args()
    clauses = json.loads(Path(args.clauses).read_text())
    data = json.loads(Path(args.jobs).read_text())
    by_name = {j["mnemonic"]: j for j in (data["values"] if isinstance(data, dict) else data)}
    links = json.loads(Path(args.links).read_text())
    rows = []
    for clause, names in links.items():
        missing = sorted(figures(clauses[clause]) - set().union(*[figures(job_text(by_name[n])) for n in names]) if names else set())
        rows.append([clause, len(names), ", ".join(missing)])
    flagged = [r for r in rows if r[1] and r[2]]
    for clause, n, missing in flagged:
        print(f"{clause}\t{n} job(s)\tnot stated: {missing}")
    print(f"{len(flagged)} of {sum(1 for r in rows if r[1])} linked clauses print a figure no linked job states", file=sys.stderr)
    if args.csv:
        with open(args.csv, "w", newline="") as fh:
            csv.writer(fh).writerows([["clause", "linked jobs", "figures not stated"], *rows])
    return 0


if __name__ == "__main__":
    sys.exit(main())
