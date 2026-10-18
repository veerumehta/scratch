"""Upload one loan packet to local Plato and read it (split, classify, extract) by a pack's document step.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Prints ids, counts and usage only: never a file name, a borrower name or a document value. The packet is the
``--entry``-th file (sorted, 1-based) of the loans folder; the read result is saved under the e2e folder (ignored).

    python scripts/local/acra_e2e_ingest.py --entry 2 --label loan-2 [--pack acra-e2e-ours]
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from jazzx_plato_client import PlatoClient

ROOT = Path("/Users/sangit/src/japes/docs/status/Acra/Acra Lending")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--entry", type=int, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--pack", default="acra-e2e-ours")
    parser.add_argument("--engine", help="how scanned pages are read (auto, vision, docintel)")
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--tenant", default="acra-lending")
    args = parser.parse_args()
    path = sorted((ROOT / "loans").iterdir())[args.entry - 1]
    out = ROOT / "e2e" / args.label
    out.mkdir(parents=True, exist_ok=True)
    async with PlatoClient(args.url, tenant_id=args.tenant, timeout=900) as plato:
        stored = await plato.upload_document(path.read_bytes(), filename=f"{args.label}.pdf",
                                             subject=args.label, labels=["e2e"])
        document_id = stored.get("document_id") or stored.get("id")
        print("uploaded", document_id, flush=True)
        (out / "upload.json").write_text(json.dumps({"document_id": document_id}))
        run = await plato.read_document(args.pack, document_id, split=True,
                                        **({"engine": args.engine} if args.engine else {}))
        (out / "read_run.json").write_text(json.dumps(run))
        output = run.get("output") or {}
        items = output.get("items") or []
        print("status", run.get("status"), "items", len(items), "error", run.get("error"))
        classes: dict[str, int] = {}
        for item in items:
            label = ((item.get("doc_type") or {}).get("value")) or "unclassified"
            classes[label] = classes.get(label, 0) + 1
        print("classes", json.dumps(classes, sort_keys=True))
        print("usage", json.dumps(output.get("usage")))
        print("settings", json.dumps(output.get("settings")))


if __name__ == "__main__":
    asyncio.run(main())
