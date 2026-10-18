"""One-off: rename quoted DSCR fact names ("fico" -> "CreditReport.representative_score") in Python files."""
import re
import sys
from pathlib import Path

from jaci.scenarios.dscr.schemas.dscr_schemas import CLTV, DSCR, ENTITY_NAMES

NAMES = {**ENTITY_NAMES, "cltv_pct": CLTV, "dscr": DSCR}
Q = re.compile(r"""(["'])(""" + "|".join(sorted(map(re.escape, NAMES), key=len, reverse=True)) + r""")\1""")
for p in map(Path, sys.argv[1:]):
    t = p.read_text()
    new, n = Q.subn(lambda m: m.group(1) + NAMES[m.group(2)] + m.group(1), t)
    if n:
        p.write_text(new)
    print(f"{n:4}  {p}")
