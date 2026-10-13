"""Propose a document registry from a hand-built job set's reference documents.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Reads the documents a job set's requirements list under "Reference Documents", sets each against an
existing registry and reference taxonomies, and prints what it would do (matched, reusable, alias,
new). With --out it writes the registry the accepted changes make; review it before the pack uses it.

    python scripts/local/build_document_registry.py JOBSET.json \
        [--reference mortgage-prod=path/to/document_classification_ontology.json ...] \
        [--registry document_types.yaml] [--out document_types.yaml]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from jazzx_sdk.pack.document_proposals import (
    apply_changes,
    candidates_from_jobset,
    classify_document,
    reference_registry,
)
from jazzx_sdk.pack.document_registry import DocumentRegistry


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("jobset", type=Path)
    parser.add_argument("--reference", action="append", default=[], metavar="ID=PATH")
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    records: list[dict] = []
    if args.registry and args.registry.is_file():
        loaded = yaml.safe_load(args.registry.read_text()) or []
        records = loaded.get("document_types", []) if isinstance(loaded, dict) else loaded
    registry = DocumentRegistry.from_records(records)
    references = {}
    for spec in args.reference:
        reference_id, _, path = spec.partition("=")
        references[reference_id] = reference_registry(json.loads(Path(path).read_text()),
                                                      reference_id=reference_id)

    changes = []
    for candidate in candidates_from_jobset(json.loads(args.jobset.read_text())):
        category, change = classify_document(candidate, registry, references)
        print(f"{category:9} {candidate.occurrences:4}  {candidate.name}"
              + (f"  -> {change.op} {change.id}" + (f" ({change.reference})" if change.reference else "")
                 if change else ""))
        if change is not None:
            changes.append(change)
    if args.out:
        args.out.write_text(yaml.safe_dump({"document_types": apply_changes(records, changes)},
                                           sort_keys=False))
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
