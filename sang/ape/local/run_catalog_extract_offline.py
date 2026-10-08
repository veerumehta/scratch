"""Run catalog extraction over documents without Plato, and write the proposals as a snapshot.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

    python scripts/local/run_catalog_extract_offline.py documents/Acra --out now.json \\
        --reference-pack ci-spread-core

Calls the configured model (the same default Plato uses unless ``--model``), so it costs a few
cents. The output is the shape ``compare_catalog_proposals.py`` reads; nothing is stored.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import yaml

SEED_PACKS = Path("plato/data/seed_packs")
DOCUMENT_SUFFIXES = {".docx", ".pdf", ".md", ".txt"}


def _reference(pack_id: str) -> dict:
    from jazzx_sdk.pack.catalog import ontology_to_catalog

    root = SEED_PACKS / pack_id
    manifest = yaml.safe_load((root / "pack_manifest.yaml").read_text(encoding="utf-8"))
    name = f"pack:{pack_id}@{manifest['pack_version']}"
    wanted = manifest.get("catalog") or manifest.get("ontology")
    text = (root / wanted).read_text(encoding="utf-8")
    schema = json.loads(text) if manifest.get("catalog") else ontology_to_catalog(yaml.safe_load(text))
    return {name: schema}


async def _run(args: argparse.Namespace) -> None:
    from jazzx_sdk.agents.metering import CallMeter, use_meter
    from jazzx_sdk.agents.reasoning.agent import ReasoningAgent
    from jazzx_sdk.agents.service import AgentExecutionService
    from jazzx_sdk.llm.config import resolve_model
    from jazzx_sdk.pipelines.catalog_extract import run_catalog_extract
    from jazzx_sdk.tools.documents.conversion import convert_document

    files = sorted(p for p in Path(args.documents).iterdir() if p.suffix.lower() in DOCUMENT_SUFFIXES)
    documents = [(p.name, await asyncio.to_thread(convert_document, str(p))) for p in files]
    references = _reference(args.reference_pack) if args.reference_pack else {}
    reasoning = ReasoningAgent(AgentExecutionService(), model=args.model or resolve_model())

    async def stage(label: str) -> None:
        print(f"  {label}", file=sys.stderr)

    meter = CallMeter()
    with use_meter(meter):
        result = await run_catalog_extract(
            documents, reasoning=reasoning, catalog={}, references=references,
            pack_id=args.pack, set_id="offline", on_stage=stage)
    proposals = [p.model_dump(mode="json") for p in result.proposals.proposals]
    Path(args.out).write_text(json.dumps(proposals, indent=2) + "\n", encoding="utf-8")
    print(f"{len(proposals)} proposals from {result.parts} parts of {len(documents)} documents; "
          f"{result.consolidated} names joined; {len(result.thresholds)} thresholds left out; "
          f"failed parts {result.failed_parts}; failed joins {result.failed_consolidations}")
    print(f"usage {meter.total()}")
    if result.thresholds:
        print("thresholds:", ", ".join(result.thresholds))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("documents", help="a directory of policy documents")
    parser.add_argument("--out", required=True)
    parser.add_argument("--pack", default="acra-dscr-policy")
    parser.add_argument("--reference-pack", help="a seed pack whose ontology is the reference")
    parser.add_argument("--model")
    asyncio.run(_run(parser.parse_args()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
