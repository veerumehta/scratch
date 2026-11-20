"""Check field_sources.yaml against a coverage report: every unsupplied read has a source, no more.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Usage: check_field_sources.py <coverage.json> [field_sources.yaml]
Reads files only; no provider or database call.
"""
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

KINDS = {"document", "loan_record", "derived", "policy"}


def main(coverage_path: str, sources_path: str) -> int:
    coverage = json.loads(Path(coverage_path).read_text())
    sources = yaml.safe_load(Path(sources_path).read_text())
    rows = sources["fields"]
    bad = [name for name, row in rows.items() if row.get("source") not in KINDS]
    unsupplied = {g["data"]: g["jobs"] for g in coverage["unsupplied_reads"]}
    uncovered = sorted(set(unsupplied) - set(rows))
    extra = sorted(set(rows) - set(unsupplied))
    by_kind = Counter(rows[name]["source"] for name in unsupplied if name in rows)
    jobs_by_kind = Counter()
    for name, jobs in unsupplied.items():
        if name in rows:
            jobs_by_kind[rows[name]["source"]] += jobs
    new_fields = sorted({f for row in rows.values() for f in row.get("new_fields", [])})
    print(f"unsupplied reads: {len(unsupplied)}; with a source: {len(unsupplied) - len(uncovered)}")
    print("fields by source:", dict(by_kind))
    print("job-reads by source:", dict(jobs_by_kind))
    print(f"new raw fields the schema must gain ({len(new_fields)}):", *new_fields, sep="\n  ")
    print("uncovered:", uncovered or "none")
    print("sources for fields no longer unsupplied:", extra or "none")
    print("rows with an unknown source kind:", bad or "none")
    return 1 if (uncovered or bad) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else str(Path(__file__).with_name("field_sources.yaml"))))
