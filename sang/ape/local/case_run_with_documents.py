"""Start a case run over one loan file on a local Plato, and print aggregate figures (local only).

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Uploads the file, submits a case on the pack that names it (the pack's `documents` step splits,
classifies and reads it), polls until the run ends or waits at a checkpoint, and prints the status,
the documents step's counts and the missing required classes. It prints no document text and no
extracted values. The run itself is stored in Plato, with the extracted values: use it on a local
Plato only, never one that other people read.

    python scripts/local/case_run_with_documents.py --tenant <tenant> --pack <pack_id> \\
        --file /path/to/package.pdf [--base-url http://localhost:8000] [--loan-id <id>]

A file over Plato's document upload cap (`PLATO_DOCUMENT_UPLOAD_MAX_BYTES`) is refused with 413.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "/Users/sangit/src/japes/jazzx_plato_client")

from jazzx_plato_client import PlatoClient  # noqa: E402

POLL_SECONDS = 10
TERMINAL = {"completed", "failed", "interrupted", "cancelled", "suspended"}


def _by_class(items: list) -> dict:
    """Items per admitted class (`doc_type.value`); a refused item counts under `unclassified`."""
    out: dict[str, int] = {}
    for item in items:
        label = (item.get("doc_type") or {}).get("value") or "unclassified"
        out[label] = out.get(label, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def _counts(output: dict) -> dict:
    docs = (output or {}).get("documents") or {}
    return {
        "refs": len(docs.get("refs") or []),
        "items": len(docs.get("items") or []),
        "pieces_by_class": _by_class(docs.get("items") or []),
        "fields_filled": len(docs.get("filled") or {}),
        "conflicts": len(docs.get("conflicts") or []),
        "missing_required_classes": docs.get("missing") or [],
        "unsure_splits": len(docs.get("unsure_splits") or []),
        "unmapped": len(docs.get("unmapped") or []),
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--pack", required=True)
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--loan-id", default="LOCAL-INGEST-1")
    parser.add_argument("--timeout-minutes", type=float, default=30)
    args = parser.parse_args()

    client = PlatoClient(args.base_url, tenant_id=args.tenant)
    async with client:
        uploaded = await client.upload_document(args.file.read_bytes(), filename=args.file.name,
                                                media_type="application/pdf")
        document_id = uploaded["document_id"]
        print(f"uploaded: id={document_id} bytes={args.file.stat().st_size}")
        started = await client.submit_case_run(
            args.pack, {"loan_id": args.loan_id, "documents": [{"document_id": document_id}]})
        run_id = started["run_id"]
        print(f"run: {run_id} (open /runs/ui on the Plato page to watch)")
        deadline = time.monotonic() + args.timeout_minutes * 60
        while True:
            run = await client.case_run(run_id)
            status = str(run.get("status"))
            print(f"  status={status}")
            if status in TERMINAL or time.monotonic() > deadline:
                break
            await asyncio.sleep(POLL_SECONDS)
        print(json.dumps({"status": status, "documents": _counts(run.get("output") or {}),
                          "error": run.get("error")}, indent=1))


if __name__ == "__main__":
    asyncio.run(main())
