"""Wait for a stored run by id and save its result under the e2e folder; prints status, class counts and usage only.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

    python scripts/local/acra_e2e_follow.py --run-id turn_... --label loan-2
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from jazzx_plato_client import PlatoClient

ROOT = Path("/Users/sangit/src/japes/docs/status/Acra/Acra Lending/e2e")
POLL_SECONDS = 30
TERMINAL = {"completed", "failed", "cancelled", "interrupted"}


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--tenant", default="acra-lending")
    args = parser.parse_args()
    async with PlatoClient(args.url, tenant_id=args.tenant, timeout=120) as plato:
        while True:
            try:
                run = await plato.case_run(args.run_id)
            except Exception as exc:  # noqa: BLE001 -- a missed poll is retried
                print("poll failed", type(exc).__name__, flush=True)
                await asyncio.sleep(POLL_SECONDS)
                continue
            if str(run.get("status")) in TERMINAL:
                break
            await asyncio.sleep(POLL_SECONDS)
    out = ROOT / args.label
    out.mkdir(parents=True, exist_ok=True)
    (out / "read_run.json").write_text(json.dumps(run))
    output = run.get("output") or {}
    items = output.get("items") or []
    classes: dict[str, int] = {}
    for item in items:
        label = ((item.get("doc_type") or {}).get("value")) or "unclassified"
        classes[label] = classes.get(label, 0) + 1
    print("status", run.get("status"), "items", len(items), "error", run.get("error"))
    print("classes", json.dumps(classes, sort_keys=True))
    print("usage", json.dumps(output.get("usage")))
    print("settings", json.dumps(output.get("settings")))


if __name__ == "__main__":
    asyncio.run(main())
