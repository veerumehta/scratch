"""Upload the three mortgage ontology copies to a tenant as reference catalogs.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Local only: it reads the sibling checkouts and calls a running Plato.

    PLATO_URL=http://localhost:8000 python scripts/local/upload_mortgage_references.py [TENANT]

Each copy is stored under its own id (`mortgage-macer`, `mortgage-app`, `mortgage-workbench`) at
version 2.0.0, so an adoption records which copy it came from. Re-running is a no-op while the
files are unchanged.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from jazzx_plato_client import PlatoClient

SRC = Path(os.getenv("SRC_ROOT", Path.home() / "src"))
COPIES = {
    "mortgage-macer": SRC / "macer/src/macer/data/ontologies/common/mortgage_ontology_v2.json",
    "mortgage-app": SRC / "mortgage-app/ontologies/common/mortgage_ontology_v2.json",
    "mortgage-workbench": SRC / "policy-workbench/backend/policyforge/prompts/ontology/mortgage_ontology_v2.json",
}


async def main(tenant: str) -> None:
    headers = {"x-user-id": os.environ["PLATO_USER_ID"]} if os.getenv("PLATO_USER_ID") else {}
    async with PlatoClient(os.getenv("PLATO_URL", "http://localhost:8000"), tenant_id=tenant,
                           request_headers_provider=lambda: headers) as plato:
        for reference_id, path in COPIES.items():
            schema = json.loads(path.read_text())
            stored = await plato.put_catalog_reference(reference_id, schema.get("version", "2.0.0"), schema)
            print(reference_id, stored["version"], f"{stored['entities']} entities",
                  "stored" if stored["created"] else "already stored")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "acra-lending"))
