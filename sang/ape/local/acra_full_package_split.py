"""Split the whole funded Acra loan file with the shipped DSCR document agent (local only).

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Runs the vision split from ``acra_scanned_validation`` over the full closing package (about 429
pages) with the seed pack's registry taxonomy, and reports AGGREGATE figures only: segment labels
with page counts, the share left as ``unknown``, confidence bands, which registry classes were found
and which were not, scanned-page count, cost and time. It prints no text from the documents and
writes nothing but the aggregate JSON (the file carries a real borrower; keep it out of git and out
of chat).

    python scripts/local/acra_full_package_split.py
    python scripts/local/acra_full_package_split.py --package /path/to/other.pdf --out /tmp/x.json

Needs the provider key in the environment (see japes' .env). Cost is a few tenths of a dollar at the
vision model's rate (40 pages cost about $0.04); the spec's vision budget caps it at $5.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import acra_scanned_validation as base  # noqa: E402

DEFAULT_PACKAGE = Path(
    "/Users/sangit/src/.scratch/sang/aci/plans/AcraL/Docs from DSCR CRE/Acra Lending/"
    "GoDocs - DSCR Loan Docs (File Funded in April 2026).pdf")
DEFAULT_OUT = Path(__file__).resolve().parent / "coverage" / "ingest_full" / "split_vision.json"
CONFIDENCE_BANDS = (0.5, 0.8, 0.95)


def _use_registry_taxonomy() -> list[str]:
    """Gives every spec the base module builds the seed pack's registry classes, as the
    `documents` step does (the pack's document_agent.yaml keeps thresholds only)."""
    from jazzx_sdk.pack.document_registry import DocumentRegistry

    taxonomy = DocumentRegistry.from_yaml(base.SEED / "document_types.yaml").taxonomy()
    if not taxonomy:
        raise SystemExit("the seed pack's registry has no classifiable documents")
    build = base._spec
    base._spec = lambda **over: build(**{"taxonomy": taxonomy, **over})
    return sorted(entry["label"] for entry in taxonomy)


def _aggregate(result: dict, registry: list[str]) -> dict:
    segments = result["segments"]
    pages_by_label: dict[str, int] = {}
    bands = {f"<{CONFIDENCE_BANDS[0]}": 0}
    for lo, hi in zip(CONFIDENCE_BANDS, CONFIDENCE_BANDS[1:] + (1.01,)):
        bands[f"{lo}-{min(hi, 1.0)}"] = 0
    for seg in segments:
        span = seg["pages"][1] - seg["pages"][0] + 1
        pages_by_label[seg["label"]] = pages_by_label.get(seg["label"], 0) + span
        key = f"<{CONFIDENCE_BANDS[0]}"
        for lo, hi in zip(CONFIDENCE_BANDS, CONFIDENCE_BANDS[1:] + (1.01,)):
            if lo <= seg["confidence"] < hi:
                key = f"{lo}-{min(hi, 1.0)}"
        bands[key] += span
    total = sum(pages_by_label.values()) or 1
    return {
        "segments": len(segments),
        "pages": total,
        "pages_by_label": dict(sorted(pages_by_label.items(), key=lambda kv: -kv[1])),
        "unknown_share": round(pages_by_label.get("unknown", 0) / total, 3),
        "pages_by_confidence": bands,
        "segments_needing_review": sum(1 for s in segments if s["review_pages"]),
        "registry_classes_found": sorted(set(pages_by_label) & set(registry)),
        "registry_classes_not_found": sorted(set(registry) - set(pages_by_label)),
        "labels_outside_registry": sorted(set(pages_by_label) - set(registry) - {"unknown"}),
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    base._load_env()
    registry = _use_registry_taxonomy()
    result = await base.split_phase("vision", args.package)
    report = {
        "scanned_pages": len(result["scanned_pages"]),
        "seconds": result["seconds"],
        "model_usage": result["model_usage"],
        "total_cost_usd": result["total_cost_usd"],
        **_aggregate(result, registry),
        "segment_list": result["segments"],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1))
    print(json.dumps({k: v for k, v in report.items() if k != "segment_list"}, indent=1))
    print(f"full report: {args.out}")


if __name__ == "__main__":
    asyncio.run(main())
