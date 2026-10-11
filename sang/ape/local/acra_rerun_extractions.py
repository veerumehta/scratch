"""Re-run the four Acra DSCR extractions (JTBD and Python, Standard and Platinum) on the local Plato.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Submits each run with the deployment's default model, at most ``--parallel`` at a time (the 2026-10-09
runs lost segments to OpenAI 429s when four overlapped), waits for each, and re-submits a run whose
segments failed, up to ``--attempts`` times. Writes the run ids, their failed segments and cost to
``--out`` (JSON), which the comparison scripts read.

    python acra_rerun_extractions.py [--only jtbd:standard,python:platinum] [--parallel 2]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

import httpx

API = "http://localhost:8000/api/v1"
HEAD = {"x-tenant-id": "acra-lending"}
PACK = "acra-dscr-policy"
DOCS = Path("/Users/sangit/src/japes/documents/Acra")
DOCUMENTS = {
    "standard": DOCS / "Acra_DSCR_Standard_Consolidated_Guidelines_v1_0.docx",
    "platinum": DOCS / "Acra_DSCR_Platinum_Select_Consolidated_Guidelines_v1_0 1.docx",
}
POLICIES = {"standard": "acra-standard", "platinum": "acra-platinum"}
JOBS = [("jtbd", "standard"), ("jtbd", "platinum"), ("python", "standard"), ("python", "platinum")]
POLL_SECONDS = 30
TERMINAL = {"succeeded", "failed", "cancelled"}
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


async def _one(http: httpx.AsyncClient, rep: str, doc: str, attempts: int) -> dict:
    tries = []
    for attempt in range(1, attempts + 1):
        path = DOCUMENTS[doc]
        resp = await http.post(f"{API}/authoring/extract/{PACK}/runs",
                               data={"policy_id": POLICIES[doc], "representation": rep},
                               files={"documents": (path.name, path.read_bytes(), DOCX)})
        resp.raise_for_status()
        run_id = resp.json()["run_id"]
        print(f"{rep}:{doc} attempt {attempt}: run {run_id}", flush=True)
        while True:
            await asyncio.sleep(POLL_SECONDS)
            run = (await http.get(f"{API}/authoring/extract/runs/{run_id}")).json()
            if run["status"] in TERMINAL:
                break
        cost = round(sum(u.get("cost_usd", 0) for u in (run.get("usage") or {}).values()), 4)
        tries.append({"run_id": run_id, "status": run["status"], "segments": run["segments"],
                      "failed_segments": run["failed_segments"], "proposals": run["proposals"],
                      "cost_usd": cost, "started_at": run["started_at"],
                      "finished_at": run["finished_at"], "error": run.get("error", "")})
        print(f"{rep}:{doc} run {run_id[:8]} {run['status']}: {run['proposals']} proposals, "
              f"{len(run['failed_segments'])} of {run['segments']} parts failed, ${cost}", flush=True)
        if run["status"] == "succeeded" and not run["failed_segments"]:
            break
    return {"representation": rep, "document": doc, "policy_id": POLICIES[doc], "attempts": tries}


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="")
    parser.add_argument("--parallel", type=int, default=2)
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--out", default=str(Path(__file__).parent / "coverage" /
                                             f"runs_{time.strftime('%Y%m%d')}.json"))
    args = parser.parse_args()
    wanted = {tuple(s.split(":")) for s in args.only.split(",") if s} or set(JOBS)
    gate = asyncio.Semaphore(args.parallel)

    async with httpx.AsyncClient(timeout=120, headers=HEAD) as http:
        async def gated(rep, doc):
            async with gate:
                return await _one(http, rep, doc, args.attempts)
        results = await asyncio.gather(*(gated(r, d) for r, d in JOBS if (r, d) in wanted))
    Path(args.out).write_text(json.dumps(results, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    asyncio.run(main())
