#!/usr/bin/env bash
# Raise installed packages that are BEHIND poetry.lock to the locked version; leave ahead ones alone.
# Run from the checkout whose .venv you want fixed. Author: Virendra Mehta <virendra.mehta@jazzx.ai>
set -euo pipefail
cd "${1:-/Users/sangit/src/japes}"
pins=$(.venv/bin/python - <<'PY'
import importlib.metadata as m, tomllib
from packaging.version import Version
for p in tomllib.load(open("poetry.lock", "rb"))["package"]:
    if "source" in p and p["source"].get("type") in ("directory", "git"):
        continue
    try:
        have = m.version(p["name"])
        if Version(have) < Version(p["version"]):
            print(f'{p["name"]}=={p["version"]}')
    except (m.PackageNotFoundError, Exception):
        pass
PY
)
if [ -z "$pins" ]; then echo "nothing behind"; exit 0; fi
echo "raising:"; echo "$pins"
uv pip install --python .venv/bin/python $pins
