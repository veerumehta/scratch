"""Set a document taxonomy workbook against a catalog reference and a job set's documents; nothing is adopted.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Reads the taxonomy's master sheet through a declared column mapping, proposes for each entry the nearest entries of
a second reference (for example the loan system's list) by name, and lists the entries no job reads and the
job-named documents matching no entry. Every match is a proposal for a person to confirm.

    python scripts/local/acra_taxonomy_report.py TAXONOMY.xlsx --coverage coverage.json \
        --registry document_types.yaml [--bytepro LIST.xlsx] [--out report.json]
    python scripts/local/acra_taxonomy_report.py --plato URL --tenant T --taxonomy-ref ID@VERSION \
        [--bytepro-ref ID@VERSION] --coverage coverage.json --registry document_types.yaml   # stored references
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from jazzx_sdk.pack.document_adopt import suggest_documents
from jazzx_sdk.pack.document_reference import DocumentColumns, DocumentEntry, read_document_table
from jazzx_sdk.pack.document_reference_db import DocumentReference

TAXONOMY_SHEET = "Master Taxonomy"
TAXONOMY_COLUMNS = DocumentColumns(
    category="Category", name="Sub-Category / Document Form", code="Taxonomy ID", aliases="Common Aliases",
    cues="Purpose / Classification Guidance", attributes={"priority": "Priority"}, header_row=5,
    sheets=[TAXONOMY_SHEET])
LIST_COLUMNS = DocumentColumns(category="Category", name="Name", code="Code", single_instance="Only One Approved",
                               scopes={"Commercial": "commercial", "Consumer": "consumer"})
#: A job document counts as matching an entry from this score (Jaccard of words, 1 for the same spelling).
MATCH_SCORE = 0.5
PROPOSALS = 3


def _reference(path: Path, columns: DocumentColumns, name: str) -> DocumentReference:
    entries, _ = read_document_table(path.read_bytes(), path.name, columns)
    return DocumentReference(name, "report", "", entries, datetime.now(timezone.utc))


def _stored(url: str, tenant: str, ref: str) -> DocumentReference:
    """A reference read from Plato's library, ``id@version``."""
    import asyncio

    from jazzx_plato_client import PlatoClient

    reference_id, _, version = ref.partition("@")

    async def fetch() -> dict:
        async with PlatoClient(url, tenant_id=tenant) as plato:
            return await plato.document_reference(reference_id, version=version or None)

    stored = asyncio.run(fetch())
    return DocumentReference(reference_id, stored["version"], stored.get("digest", ""),
                             [DocumentEntry.model_validate(e) for e in stored["entries"]], datetime.now(timezone.utc))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("taxonomy", type=Path, nargs="?")
    parser.add_argument("--plato", help="read the references from this Plato instead of workbooks")
    parser.add_argument("--tenant", default="acra-lending")
    parser.add_argument("--taxonomy-ref")
    parser.add_argument("--bytepro-ref")
    parser.add_argument("--coverage", type=Path, required=True, help="a coverage report's JSON (its jobs name documents)")
    parser.add_argument("--registry", type=Path, required=True, help="the pack's document_types.yaml (labels of job names)")
    parser.add_argument("--bytepro", type=Path, help="the second reference's workbook (Commercial and Consumer sheets)")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if bool(args.plato) != bool(args.taxonomy_ref) or not (args.plato or args.taxonomy):
        parser.error("give a taxonomy workbook, or --plato with --taxonomy-ref")

    taxonomy = (_stored(args.plato, args.tenant, args.taxonomy_ref) if args.plato
                else _reference(args.taxonomy, TAXONOMY_COLUMNS, "acra-taxonomy"))
    labels = {r["id"]: [r.get("label", r["id"]), *r.get("aliases", [])]
              for r in yaml.safe_load(args.registry.read_text())["document_types"]}
    jobs = json.loads(args.coverage.read_text())["jobs"]
    named: dict[str, int] = {}
    for job in jobs:
        for doc in (*job["documents"], *job["undeclared_documents"]):
            named[doc] = named.get(doc, 0) + 1

    read: dict[str, list[str]] = {}
    unmatched: list[str] = []
    for doc in named:
        found = [s for text in labels.get(doc, [doc.replace("_", " ")])
                 for s in suggest_documents(taxonomy, text, limit=PROPOSALS, floor=MATCH_SCORE)]
        if not found:
            unmatched.append(doc)
        for suggestion in found:
            read.setdefault(suggestion["code"], []).append(doc)
    report = {
        "entries": len(taxonomy.entries), "job_documents": named,
        "job_documents_matching_no_entry": unmatched,
        "entries_a_job_reads": {c: sorted(set(d)) for c, d in read.items()},
        "entries_no_job_reads": [{"code": e.code, "name": e.name, "category": e.category,
                                  "priority": e.attributes.get("priority", "")}
                                 for e in taxonomy.entries if e.code not in read]}
    if args.bytepro or args.bytepro_ref:
        other = (_stored(args.plato, args.tenant, args.bytepro_ref) if args.bytepro_ref
                 else _reference(args.bytepro, LIST_COLUMNS, "bytepro"))
        proposals = {e.code: suggest_documents(other, e.name, limit=PROPOSALS) for e in taxonomy.entries}
        report["bytepro_proposals"] = {c: p for c, p in proposals.items() if p}
        report["entries_matching_no_bytepro_entry"] = [c for c, p in proposals.items() if not p]
    text = json.dumps(report, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    unread = report["entries_no_job_reads"]
    print(f"{report['entries']} entries; {len(report['entries_a_job_reads'])} read by a job, {len(unread)} read by none "
          f"({sum(1 for u in unread if u['priority'] == 'Core')} Core)")
    print(f"job documents matching no entry: {unmatched}")
    if "bytepro_proposals" in report:
        print(f"entries with a BytePro proposal: {len(report['bytepro_proposals'])}; none: "
              f"{len(report['entries_matching_no_bytepro_entry'])}")


if __name__ == "__main__":
    main()
