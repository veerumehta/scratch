#!/usr/bin/env bash
# Pin local Plato to the v2.6.4 tip, migrate its database to head, restart, then store the Acra taxonomy as
# the reference acra-taxonomy@2026-10-17. Run by the user.
set -euo pipefail
MAIN=/Users/sangit/src/japes
WT=/Users/sangit/src/japes-plato
TOOL=/Users/sangit/src/.scratch/sang/ape/local/plato_worktree.sh
REV=$(git -C "$MAIN" rev-parse --short v2.6.4)
"$TOOL" pin "$REV"
export JAPES_ENV_FILE="$MAIN/.env" JAPES_ENVIRONMENT=local
cd "$WT"
"$MAIN/.venv/bin/python" - "$WT/plato/alembic.ini" <<'PY'
import sys
from jazzx_sdk.config.envvars import load_env_file
load_env_file()
from alembic.config import main
main(argv=["-c", sys.argv[1], "upgrade", "head"])
PY
"$TOOL" restart "$REV"
sleep 5
cd "$MAIN"
PLATO_URL=http://localhost:8000 .venv/bin/python - <<'PY'
import asyncio, os
from pathlib import Path
from jazzx_plato_client import PlatoClient
import importlib.util
spec = importlib.util.spec_from_file_location("acra_taxonomy_report", "scripts/local/acra_taxonomy_report.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
TAXONOMY_COLUMNS = module.TAXONOMY_COLUMNS

async def main():
    path = Path("docs/status/Acra/Updated_Loan_Document_Taxonomy.xlsx")
    async with PlatoClient(os.environ["PLATO_URL"], tenant_id="acra-lending") as plato:
        print(await plato.upload_document_reference("acra-taxonomy", "2026-10-17", path.read_bytes(),
                                                    filename=path.name, columns=TAXONOMY_COLUMNS.model_dump()))
asyncio.run(main())
PY
