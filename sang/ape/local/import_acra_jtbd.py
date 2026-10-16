"""Import Acra's Standard and Platinum JTBDSets into dscr-core as version 0.0.0.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Local only: it reads documents/Acra/ (untracked) and calls a running Plato.

    PLATO_URL=http://localhost:8000 python scripts/local/import_acra_jtbd.py [--publish]

Without --publish the import stops at the draft, for you to read. It refuses if the tenant already
has a dscr-core draft, so it never mixes the import into someone's working copy. Publish this
before publishing our extraction as 1.0.0, so 1.0.0 stays the newest version.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from jazzx_plato_client import PlatoClient

PACK = "dscr-core"
TENANT = "acra-lending"
VERSION = "0.0.0"
FILES = {"standard": "acra_New_Guideline_JTBD.json",
         "platinum_select": "acra_New_Guideline_JTBD_Platinum.json"}
NOTES = ("Acra 9.0.0, imported from acra_New_Guideline_JTBD.json + _Platinum.json "
         "(Standard 9.0.0, Platinum 7.0.0)")


async def main(publish: bool) -> None:
    folder = Path(__file__).resolve().parents[2] / "documents" / "Acra"
    sets = {program: json.loads((folder / name).read_text()) for program, name in FILES.items()}
    headers = {"x-user-id": os.environ["PLATO_USER_ID"]} if os.getenv("PLATO_USER_ID") else {}
    async with PlatoClient(os.getenv("PLATO_URL", "http://localhost:8000"), tenant_id=TENANT,
                           request_headers_provider=lambda: headers) as plato:
        drafts = (await plato.drafts()).get("drafts", [])
        if any(d["pack_id"] == PACK for d in drafts):
            raise SystemExit(f"{TENANT} already has a {PACK} draft; publish or discard it first")
        result = await plato.import_jtbdset_programs(
            PACK, sets, version=VERSION, domain="commercial_lending", segment="dscr", notes=NOTES)
        print(json.dumps(result, indent=2))
        if publish:
            print(json.dumps(await plato.publish_draft(PACK), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true")
    asyncio.run(main(parser.parse_args().publish))
