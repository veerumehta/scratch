"""Policy documents to each output the SDK can extract, offline, with the cost and a summary.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

    python scripts/local/policy_to_outputs.py documents/Acra \\
        --pack-dir plato/data/seed_packs/acra_dscr_policy --reference-pack ci-spread-core

Documents live in ``documents/<Tenant>/`` (gitignored) and so do the results: by default
``documents/<Tenant>/outputs/extract-<date>-<time>/``, so a tenant's sources and what came of them
sit in one folder. ``--out`` names another place.

Outputs, one directory each under that folder (pick with ``--only catalog,jtbd``; default all):

    catalog/       catalog.schema.json (every proposal applied, a preview) and proposals.json
    jtbd/          policy.yaml (jobs as rules), proposals.json, lint.txt
    obligations/   policy.yaml (modal clauses as rules; no model), proposals.json, lint.txt
    python/        policy.yaml (rules with Python conditions), proposals.json, lint.txt
    conditions/    policy.yaml (rules with structured conditions), proposals.json, lint.txt
    summary.md     what each produced, its cost and what failed

The catalog is extracted first and bounds what the jtbd, python and conditions extractions may
read (the template's ``reads``), as the pack's own catalog does in Plato. ``--pack-dir`` supplies
the jtbd template and the pack the lint checks rules against. Nothing is stored or published.
Costs model calls (a few cents for the catalog, more for jtbd), so it asks for none you did not list.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

ORDER = ("catalog", "jtbd", "obligations", "python", "conditions")
SEED_PACKS = Path("plato/data/seed_packs")
DOCUMENT_SUFFIXES = {".docx", ".pdf", ".md", ".txt"}
TEMPLATE_FILE = "jtbd_template.yaml"
CATALOG_FILE = "catalog.schema.json"
#: Where a documents folder keeps what was made from it.
OUTPUTS_DIR = "outputs"


def _reference(pack_id: str) -> dict:
    from jazzx_sdk.pack.catalog import ontology_to_catalog

    root = SEED_PACKS / pack_id
    manifest = yaml.safe_load((root / "pack_manifest.yaml").read_text(encoding="utf-8"))
    wanted = manifest.get("catalog") or manifest.get("ontology")
    text = (root / wanted).read_text(encoding="utf-8")
    schema = json.loads(text) if manifest.get("catalog") else ontology_to_catalog(yaml.safe_load(text))
    return {f"pack:{pack_id}@{manifest['pack_version']}": schema}


def _dump(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


async def _catalog(documents, reasoning, references, out: Path, args) -> dict[str, Any]:
    from jazzx_sdk.pack.catalog_proposals import CatalogChange, apply_changes
    from jazzx_sdk.pipelines.catalog_extract import run_catalog_extract

    result = await run_catalog_extract(documents, reasoning=reasoning, catalog={},
                                       references=references, pack_id=args.pack, set_id="offline")
    proposals = result.proposals.proposals
    _dump(out / "proposals.json", [p.model_dump(mode="json") for p in proposals])
    changes = [CatalogChange.model_validate(p.catalog) for p in proposals
               if p.catalog and p.category != "matched"]
    catalog = apply_changes({}, changes, references=references)
    _dump(out / CATALOG_FILE, catalog)
    return {"catalog": catalog, "proposals": len(proposals), "parts": result.parts,
            "notes": f"{result.consolidated} names joined; thresholds left out: "
                     f"{', '.join(result.thresholds) or 'none'}; failed {result.failed_parts}"}


async def _policy(representation, documents, reasoning, template, pack, out: Path, args):
    from jazzx_sdk.pipelines.policy_extract import (PolicyTurn, build_policy_pipeline,
                                                    default_step_error, run_policy_extract)
    from jazzx_sdk.server.policy_extract_api import _Document, default_components

    components = default_components(representation, reasoning=reasoning, policy_id=args.policy_id,
                                    template=template)
    result = await run_policy_extract(
        PolicyTurn(documents=[_Document(n, t) for n, t in documents], pack=pack,
                   pack_id=args.pack, policy_id=args.policy_id, set_id="offline"),
        pipeline=build_policy_pipeline(), components=components, on_step_error=default_step_error)
    if not hasattr(result, "proposals"):
        return {"proposals": 0, "parts": 0, "notes": f"refused: {result}"}
    proposals = result.proposals.proposals
    _dump(out / "proposals.json", [p.model_dump(mode="json") for p in proposals])
    findings = [f.describe() for f in result.lint.findings] if result.lint else []
    (out / "lint.txt").write_text("\n".join(findings) + ("\n" if findings else ""), encoding="utf-8")
    if result.policy is not None:
        (out / "policy.yaml").write_text(yaml.safe_dump(
            {"policies": [result.policy.model_dump(mode="json", exclude_none=True)]},
            sort_keys=False, allow_unicode=True, width=100), encoding="utf-8")
    observed = result.obligations
    return {"proposals": len(proposals), "parts": observed.segments,
            "notes": f"{len(findings)} lint findings; failed {observed.failed_segments}"
                     + ("" if result.policy is not None else "; no rules, policy.yaml not written")}


async def _run(args: argparse.Namespace) -> int:
    from jazzx_sdk.agents.metering import CallMeter, use_meter
    from jazzx_sdk.agents.reasoning.agent import ReasoningAgent
    from jazzx_sdk.agents.service import AgentExecutionService
    from jazzx_sdk.llm.config import ensure_provider_key, resolve_model
    from jazzx_sdk.pack import Pack
    from jazzx_sdk.pipelines.policy_jtbd import JtbdTemplate
    from jazzx_sdk.tools.documents.conversion import convert_document

    wanted = [r for r in ORDER if r in (args.only.split(",") if args.only else ORDER)]
    unknown = set(args.only.split(",")) - set(ORDER) if args.only else set()
    if unknown:
        print(f"unknown output {sorted(unknown)}; one of {ORDER}", file=sys.stderr)
        return 2
    ensure_provider_key()
    files = sorted(p for p in Path(args.documents).iterdir() if p.suffix.lower() in DOCUMENT_SUFFIXES)
    documents = [(p.name, await asyncio.to_thread(convert_document, str(p))) for p in files]
    out_root = Path(args.out) if args.out else (
        Path(args.documents) / OUTPUTS_DIR / datetime.now().strftime("extract-%Y-%m-%d-%H%M"))
    out_root.mkdir(parents=True, exist_ok=True)
    print(f"writing to {out_root}", file=sys.stderr)
    reasoning = ReasoningAgent(AgentExecutionService(), model=args.model or resolve_model())
    references = _reference(args.reference_pack) if args.reference_pack else {}

    pack_dir = Path(args.pack_dir) if args.pack_dir else None
    pack = Pack.from_manifest(pack_dir.name, pack_dir.parent) if pack_dir else None
    template_file = pack_dir / TEMPLATE_FILE if pack_dir else None
    template = (JtbdTemplate.from_yaml(str(template_file))
                if template_file and template_file.is_file() else JtbdTemplate())

    rows = []
    for representation in wanted:
        out = out_root / representation
        out.mkdir(exist_ok=True)
        print(f"{representation} ...", file=sys.stderr)
        meter = CallMeter()
        try:
            with use_meter(meter):
                if representation == "catalog":
                    produced = await _catalog(documents, reasoning, references, out, args)
                    template = template.bound_to_catalog(produced.pop("catalog"))
                else:
                    produced = await _policy(representation, documents, reasoning, template, pack,
                                             out, args)
        except Exception as exc:  # noqa: BLE001 - one output failing leaves the others
            produced = {"proposals": 0, "parts": 0, "notes": f"FAILED {type(exc).__name__}: {exc}"}
        usage = meter.total()
        rows.append((representation, produced, usage))
        print(f"  {produced['proposals']} proposals, ${usage.get('cost_usd', 0):.4f}, "
              f"{produced['notes']}", file=sys.stderr)

    lines = ["| output | proposals | parts | calls | cost USD | notes |", "|---|---|---|---|---|---|"]
    for name, produced, usage in rows:
        lines.append(f"| {name} | {produced['proposals']} | {produced['parts']} | "
                     f"{usage.get('calls', 0)} | {usage.get('cost_usd', 0):.4f} | {produced['notes']} |")
    (out_root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("documents", help="a directory of policy documents")
    parser.add_argument("--out", help="default: <documents>/outputs/extract-<date>-<time>")
    parser.add_argument("--only", help=f"comma-separated outputs, from {','.join(ORDER)}")
    parser.add_argument("--pack", default="acra-dscr-policy", help="the pack id proposals are filed under")
    parser.add_argument("--pack-dir", help="a pack directory: its template and the pack the lint checks")
    parser.add_argument("--reference-pack", help="a seed pack whose ontology is the catalog reference")
    parser.add_argument("--policy-id", default="extracted")
    parser.add_argument("--model")
    return asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    sys.exit(main())
