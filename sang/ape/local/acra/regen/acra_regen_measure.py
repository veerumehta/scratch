"""Measure a regeneration's job files against the baseline: structure the job writer controls.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

    python acra_regen_measure.py <dir> [--clause REGEX ...] [--json OUT]

``<dir>`` holds ``standard_policy.yaml`` and ``platinum_policy.yaml`` (any ``*_policy.yaml``): the
jobs of a trial pack, as `acra_bundle.py` copies them. Reads files only; no Plato, no model.
Per policy file: jobs; citations and how many span more than one section; the most jobs one
citation has; near-duplicate pairs (check-text Jaccard); jobs with reads whose computable list is
empty; jobs per ``--clause`` pattern (matched against the ledger clause). With a Clauses sheet in
the coverage workbook it also counts units checked and cited only.
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
from collections import defaultdict
from pathlib import Path

import yaml

#: Check-text Jaccard from which two jobs are near-duplicates (the assessment's own bar).
NEAR_DUPLICATE = 0.6
WORD = re.compile(r"[a-z0-9]+")
SECTION_SEGMENT = 1


def _words(job: dict) -> set[str]:
    return set(WORD.findall(" ".join((job.get("condition") or {}).get("checks") or []).lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def measure(path: Path, clauses: list[str]) -> dict:
    data = yaml.safe_load(path.read_text())
    rules = data.get("rules") or [r for p in data.get("policies", []) for r in p.get("rules", [])]
    jobs = [r for r in rules if ((r.get("condition") or {}).get("kind") == "procedure")]
    sections: dict[str, set[str]] = defaultdict(set)
    per_citation: dict[str, int] = defaultdict(int)
    for job in jobs:
        parts = job["rule_id"].split(".")
        section = parts[SECTION_SEGMENT] if len(parts) > SECTION_SEGMENT else ""
        for citation in set(job.get("citations") or []):
            sections[citation].add(section)
            per_citation[citation] += 1
    words = [_words(j) for j in jobs]
    pairs = [(i, j) for i, j in itertools.combinations(range(len(jobs)), 2)
             if words[i] and words[j] and _jaccard(words[i], words[j]) >= NEAR_DUPLICATE]
    section_of = [j["rule_id"].split(".")[SECTION_SEGMENT] for j in jobs]
    out = {
        "jobs": len(jobs),
        "citations": len(sections),
        "citations_spanning_sections": sum(1 for s in sections.values() if len(s) > 1),
        "most_jobs_one_citation": max(per_citation.values(), default=0),
        "near_duplicate_pairs": len(pairs),
        "near_duplicate_pairs_across_sections": sum(1 for i, j in pairs if section_of[i] != section_of[j]),
        "reads_but_none_computable": sum(
            1 for j in jobs if (j["condition"].get("reads") and j["condition"].get("computable_checks") == [])),
        "reads_none": sum(1 for j in jobs if not j["condition"].get("reads")),
    }
    for pattern in clauses:
        rx = re.compile(pattern, re.IGNORECASE)
        out[f"jobs_matching[{pattern}]"] = sum(
            1 for j in jobs if rx.search(((j.get("domain_extensions") or {}).get("ledger") or {}).get("clause") or ""))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", type=Path)
    parser.add_argument("--clause", action="append", default=[])
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    result = {p.name.removesuffix("_policy.yaml"): measure(p, args.clause)
              for p in sorted(args.dir.glob("*_policy.yaml"))}
    text = json.dumps(result, indent=1)
    print(text)
    if args.json:
        args.json.write_text(text)


if __name__ == "__main__":
    main()
