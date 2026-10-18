"""Build the Acra classification-and-splitting golden cases from the taxonomy workbook (sheet data only).

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Reads the workbook's Classification sheet and ``golden/label_mapping.csv`` (the reviewed label to Master
Taxonomy table) and writes ``golden/dataset_parts.json``: one case per Part with its expected segments
(0-based, inclusive pages, the SplitScorer's convention). A range's ``label`` is the master id; a category-only
range carries the master category; the ranges the user excluded (unmapped, unclassified) keep their pages
under ``excluded`` so boundaries stay whole. No loan file is opened and no loan text is read.

    python scripts/local/acra_classification_dataset.py
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import openpyxl

ACRA = Path("/Users/sangit/src/japes/docs/status/Acra")
WORKBOOK = ACRA / "Updated_Loan_Document_Taxonomy.xlsx"
GOLDEN = ACRA / "Acra Lending" / "golden"
#: Mapping statuses that give a range a scoreable class, and the ones that exclude it.
CLASSED = {"exact", "category renamed", "alias: CONFIRM"}
CATEGORY_ONLY = "category-only"


def master_categories(book) -> dict[str, str]:
    rows = [r for r in book["Master Taxonomy"].iter_rows(values_only=True) if r[0] and re.match(r"[A-Z]+-\d+", str(r[0]))]
    return {r[0]: r[1] for r in rows}


def main() -> None:
    book = openpyxl.load_workbook(WORKBOOK, read_only=True)
    category_of = master_categories(book)
    with open(GOLDEN / "label_mapping.csv", newline="") as fh:
        mapping = {row["acra_label"]: row for row in csv.DictReader(fh)}
    # category-only labels name the category the label itself gives; the master spells it as the user confirms
    parts: dict[str, list[dict]] = {}
    current = None
    for row in book["Classification"].iter_rows(values_only=True):
        if row[0] and str(row[0]).startswith("Part"):
            current = str(row[0]); parts[current] = []; continue
        if not (current and row[2] and str(row[0]).startswith(("pp.", "p. "))):
            continue
        first, *_, last = [int(n) for n in re.findall(r"\d+", str(row[0]))] * 2
        entry = mapping[row[2]]
        segment = {"start_page": first, "end_page": last, "acra_label": row[2], "confidence": row[3]}
        if entry["status"] in CLASSED:
            segment.update(label=entry["master_id"], category=category_of[entry["master_id"]], scored="class")
        elif entry["status"] == CATEGORY_ONLY:
            segment.update(label="", category=row[2].split(" / ")[0], scored="category-only")
        else:
            segment.update(label="", category="", scored="excluded", why=entry["status"])
        parts[current].append(segment)
    cases = []
    for name, segments in parts.items():
        segments.sort(key=lambda s: s["start_page"])
        cases.append({"case_id": name.lower().replace(" ", "-"), "pages": segments[-1]["end_page"] + 1, "segments": segments,
                      "excluded_pages": sum(s["end_page"] - s["start_page"] + 1 for s in segments if s["scored"] == "excluded")})
    GOLDEN.mkdir(parents=True, exist_ok=True)
    (GOLDEN / "dataset_parts.json").write_text(json.dumps({"cases": cases}, indent=2))
    for c in cases:
        scored = sum(s["end_page"] - s["start_page"] + 1 for s in c["segments"] if s["scored"] != "excluded")
        print(f'{c["case_id"]}: {c["pages"]} pages, {len(c["segments"])} ranges, {scored} scoreable pages, {c["excluded_pages"]} excluded')


if __name__ == "__main__":
    main()
