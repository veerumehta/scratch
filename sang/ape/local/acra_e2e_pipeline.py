"""Run one loan packet through the whole conditioned pipeline of a scratch pack on local Plato and write counts only.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

The pack is `acra-e2e-pipe-<variant>` from `acra_e2e_packs.py`: documents, assessment, adjudication, the investigation loop,
a policy check and the narrative. The packet is the one `acra_e2e_ingest.py` uploaded (`upload.json`); the documents step
reads it through the page cache. The raw result is saved under the e2e folder (ignored); the report and the messages hold
counts, ids and field names, never a value, name or amount. Plato holds the spend ceiling (`JAPES_RUN_BUDGET_USD`, set when
it was started); ``--stop-after`` also asks the run to stop once that many seconds have passed.

    python scripts/local/acra_e2e_pipeline.py --variant hybrid --label loan-2 [--publish] [--golden-conditions N]
"""

from __future__ import annotations

import argparse
import asyncio
import io
import json
import time
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from jazzx_plato_client import PlatoClient

ROOT = Path("/Users/sangit/src/japes/docs/status/Acra/Acra Lending/e2e")
PACKS = Path("/Users/sangit/src/.scratch/sang/ape/local/acra_e2e/packs")
POLL_SECONDS = 20
TERMINAL = {"completed", "failed", "cancelled", "interrupted"}
DECIDED = {"pass", "fail", "not_applicable"}
OPEN = {"pending_evidence", "pending_calculation", "waiver_required", "pre_review_required"}


def _zip(root: Path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(root).as_posix())
    return buffer.getvalue()


def _outcomes(assessment: dict[str, Any] | None) -> dict[str, Any]:
    """Counts of the assessment's outcomes per program (or overall): decided, open conditions, other undecided."""
    if not assessment:
        return {}
    blocks = assessment.get("programs") or {"": assessment}
    out = {}
    for name, block in blocks.items():
        counts = Counter(str(v) for v in (block.get("outcomes") or {}).values())
        out[name or "assessment"] = {
            "rules": sum(counts.values()), "decided": sum(counts[k] for k in DECIDED if k in counts),
            "open_conditions": sum(counts[k] for k in OPEN if k in counts),
            "by_outcome": dict(sorted(counts.items())), "withheld": len(block.get("withheld") or [])}
    return out


def _shape(value: Any) -> Any:
    """A structure's keys and sizes, never its values."""
    if isinstance(value, dict):
        return {k: _shape(v) if isinstance(v, (dict, list)) else type(v).__name__ for k, v in list(value.items())[:25]}
    if isinstance(value, list):
        return {"items": len(value)}
    return type(value).__name__


def summarize(output: dict[str, Any], elapsed: float, golden: int | None) -> dict[str, Any]:
    steps = [{"step": s.get("step"), "status": s.get("status"), "seconds": round((s.get("duration_ms") or 0) / 1000, 1)}
             for s in output.get("steps") or []]
    usage = output.get("usage") or {}
    investigation = output.get("investigation") or {}
    adjudication = output.get("adjudication") or {}
    documents = output.get("documents") or {}
    return {
        "status": output.get("status"), "gate": output.get("gate"), "elapsed_seconds": round(elapsed, 1),
        "health": [{"severity": h.get("severity"), "code": h.get("code")} for h in output.get("health") or []],
        "steps": steps,
        "cost_usd": {"total": (usage.get("total") or {}).get("cost_usd"),
                     "by_mode": {k: round(v.get("cost_usd") or 0, 4) for k, v in (usage.get("modes") or {}).items()},
                     "calls_by_mode": {k: v.get("calls") for k, v in (usage.get("modes") or {}).items()},
                     "incomplete_calls": (usage.get("total") or {}).get("incomplete_calls")},
        "assessment": _outcomes(output.get("assessment")),
        "adjudication_shape": _shape(adjudication),
        "investigation": {k: investigation.get(k) for k in ("status", "iterations", "guard_reason", "convergence_reason",
                                                            "iterations_after_deadline")}
                         | {"hypotheses": len(investigation.get("hypotheses") or []),
                            "evidence": len(investigation.get("evidence") or [])},
        "failed_modes": output.get("failed_modes"), "checks_shape": _shape(output.get("checks")),
        "documents": {"items": len(documents.get("items") or []), "unmapped": len(documents.get("unmapped") or []),
                      "missing": len(documents.get("missing") or [])},
        "golden_conditions": golden,
        "decision_present": output.get("decision") is not None, "narrative_present": bool(output.get("narrative"))}


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--variant", required=True, choices=["hybrid", "both"])
    parser.add_argument("--label", default="loan-2")
    parser.add_argument("--publish", action="store_true", help="publish and activate the scratch pack first")
    parser.add_argument("--golden-conditions", type=int, help="the packet's own conditions count, for the comparison")
    parser.add_argument("--stop-after", type=float, default=7200.0)
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--tenant", default="acra-lending")
    args = parser.parse_args()
    pack_id = f"acra-e2e-pipe-{args.variant}"
    out = ROOT / args.label / "pipeline"
    out.mkdir(parents=True, exist_ok=True)
    document_id = json.loads((ROOT / args.label / "upload.json").read_text())["document_id"]
    async with PlatoClient(args.url, tenant_id=args.tenant, timeout=900) as plato:
        if args.publish:
            published = await plato.publish_pack(_zip(PACKS / pack_id), name=f"{pack_id}.zip", notes="e2e pipeline run")
            print("published", published.get("pack_id"), published.get("version"), flush=True)
            await plato.activate_pack(published["pack_id"], published["version"])
        started = time.monotonic()
        run = await plato.submit_case_run(pack_id, {"loan_id": args.label, "documents": [{"document_id": document_id}]})
        run_id = run.get("run_id") or run.get("id")
        print("run", run_id, flush=True)
        stopped = False
        while True:
            await asyncio.sleep(POLL_SECONDS)
            state = await plato.case_run(run_id)
            if state.get("status") in TERMINAL:
                break
            if not stopped and time.monotonic() - started > args.stop_after:
                await plato._json("POST", f"/runs/{run_id}/stop")
                stopped = True
            print("  ", state.get("status"), int(time.monotonic() - started), "s", flush=True)
        elapsed = time.monotonic() - started
    (out / f"{args.variant}_raw.json").write_text(json.dumps(state))
    summary = summarize(state.get("output") or {}, elapsed, args.golden_conditions)
    summary["run_status"], summary["stop_requested"] = state.get("status"), stopped
    (out / f"{args.variant}_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
