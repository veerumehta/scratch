"""The loan-2 end-to-end V5 (our jobs and code, both) with the disagreement verifier on; counts only.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

    python acra_verifier_run.py --plato http://localhost:8000

Reads the loan-2 case record, states omitted facts as the end-to-end run does, assesses `acra-e2e-ours` in `both` with the
verifier, and writes counts (never loan values) to the loan-2 folder.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
LOAN = Path("/Users/sangit/src/japes/docs/status/Acra/Acra Lending/e2e/loan-2")
PACK = "acra-e2e-ours"


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plato", required=True)
    parser.add_argument("--tenant", default="acra-lending")
    args = parser.parse_args()
    import acra_e2e_run as E
    from jazzx_plato_client import PlatoClient

    inputs = json.loads((LOAN / "case.json").read_text())
    programs = None if inputs.get("program_id") else "all"
    async with PlatoClient(args.plato, tenant_id=args.tenant, timeout=3600) as plato:
        filled, _omitted = await E.state_omitted_facts(plato, PACK, inputs, programs, E.PACKS)
        began = time.monotonic()
        body = await plato.assess(PACK, filled, programs=programs, reason=True, engine_mode="both",
                                  verify_disagreements=True)
        seconds = round(time.monotonic() - began, 1)
    results = body.get("programs") or {"": body}
    summary = {"seconds": seconds, "usage": body.get("usage"), "programs": {}}
    for program, result in results.items():
        rows = result.get("comparison") or []
        stats = result.get("engine_summary") or {}
        summary["programs"][program] = {
            "pairs": len(rows), "disagreements": sum(1 for r in rows if r.get("agree") is False),
            "verified_by": dict(Counter(r.get("verified_by") or "none" for r in rows if r.get("agree") is False)),
            "verifier_verdicts": dict(Counter(r.get("verifier_verdict") or "not asked" for r in rows if r.get("agree") is False)),
            "summary_verified": stats.get("verified"), "summary_unresolved": stats.get("unresolved")}
    (LOAN / "verifier_run.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
