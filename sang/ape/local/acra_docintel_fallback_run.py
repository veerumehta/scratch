"""Read the loan-2 document with vision as primary and DocIntel as fallback; report counts only.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

    python acra_docintel_fallback_run.py --plato http://localhost:8000 --tenant acra-lending

Publishes a scratch pack (a copy of the end-to-end pack whose document agent declares the fallback), reads the uploaded
loan-2 document through it, and writes counts (never loan values) to the loan-2 folder.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path("/Users/sangit/src/japes")
SOURCE = Path("/Users/sangit/src/.scratch/sang/ape/local/acra_e2e/packs/acra-e2e-ours")
SCRATCH = Path("/Users/sangit/src/.scratch/sang/ape/local/acra_e2e/packs/acra-e2e-fallback")
LOAN = ROOT / "docs" / "status" / "Acra" / "Acra Lending" / "e2e" / "loan-2"
PACK_ID, VERSION = "acra-e2e-fallback", "0.0.1"
STEP = "documents"
POLL_SECONDS = 30


def build_pack() -> None:
    if SCRATCH.exists():
        shutil.rmtree(SCRATCH)
    shutil.copytree(SOURCE, SCRATCH)
    manifest = yaml.safe_load((SCRATCH / "pack_manifest.yaml").read_text())
    manifest["pack_id"], manifest["pack_version"] = PACK_ID, VERSION
    (SCRATCH / "pack_manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    agent = SCRATCH / "document_agent.yaml"
    agent.write_text(agent.read_text() + "\nengine:\n  default: vision\n  fallback: docintel:prebuilt-read\n")


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plato", required=True)
    parser.add_argument("--tenant", default="acra-lending")
    parser.add_argument("--run-id", help="summarize this run once it ends, instead of starting one")
    args = parser.parse_args()
    from jazzx_plato_client import PlatoClient
    from jazzx_sdk.pack.store import pack_archive

    document_id = json.loads((LOAN / "upload.json").read_text())["document_id"]
    async with PlatoClient(args.plato, tenant_id=args.tenant, timeout=3600) as plato:
        if args.run_id:
            while (run := await plato.case_run(args.run_id)).get("status") in ("queued", "running", "pending"):
                await asyncio.sleep(POLL_SECONDS)
        else:
            build_pack()
            await plato.publish_pack(pack_archive(SCRATCH), name=f"{PACK_ID}.zip",
                                     notes="scratch pack: vision with a DocIntel fallback")
            run = await plato.read_document(PACK_ID, document_id, step=STEP, split=True)
    out = run.get("output") or {}
    reads = [r for item in out.get("items", []) for r in item.get("pages_read") or []]
    summary = {
        "status": run.get("status"), "error": (run.get("error") or "")[:200], "documents": len(out.get("items", [])),
        "pages_read": len(reads), "by_engine": dict(Counter(r["engine"] for r in reads)),
        "fallback_pages": sum(1 for r in reads if r.get("fallback_from")),
        "fallback_from": dict(Counter(r["fallback_from"] for r in reads if r.get("fallback_from"))),
        "still_failed": sum(1 for r in reads if r.get("failed")), "cached": sum(1 for r in reads if r.get("cached")),
        "fallback_reasons": dict(Counter((r.get("reason") or "")[:60] for r in reads if r.get("fallback_from"))),
        "usage": out.get("usage"), "settings": out.get("settings"),
        "di_pages": dict(sum((Counter(item.get("di_pages") or {}) for item in out.get("items", [])), Counter())),
    }
    (LOAN / "fallback_run.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k not in ("usage", "settings")}, indent=2))
    print("cost", {k: round(v.get("cost_usd", 0), 4) for k, v in (summary["usage"] or {}).items()})
    return 0 if run.get("status") == "completed" else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
