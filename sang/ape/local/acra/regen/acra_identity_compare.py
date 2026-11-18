"""Our trial pack's jobs against Acra's K-Studio sets, aligned, with the equivalence counts: one comparison per program.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Exports the trial draft as one set, splits it by the policy each job's rule id names, and compares each half with the
K-Studio set of its program (a model labels each left job's candidates: one call per job, so this spends). Counts and cost
only are printed; the raw answers go to ``--out`` (a gitignored folder).

    python acra_identity_compare.py --pack acra-regen-6 --out <dir> [--only standard]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx

API = "http://localhost:8000/api/v1"
HEAD = {"x-tenant-id": "acra-lending"}
REFERENCES = Path("/Users/sangit/src/japes/docs/status/Acra/acra_bundle/2_kstudio_jtbds")
#: Program, the policy its jobs sit in, and the K-Studio set it is compared with.
PROGRAMS = {"standard": ("acra-standard", "standard_v17.json"),
            "platinum": ("acra-platinum", "platinum_select_v7.json")}
TIMEOUT_SECONDS = 3600


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--only", choices=sorted(PROGRAMS))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=TIMEOUT_SECONDS, headers=HEAD) as http:
        exported = http.get(f"{API}/packs/drafts/{args.pack}/jtbdset")
        exported.raise_for_status()
        whole = exported.json()
        for program, (policy, reference) in PROGRAMS.items():
            if args.only and program != args.only:
                continue
            ours = {**whole, "title": f"{args.pack} {program}", "values": [
                v for v in whole["values"] if str(v.get("rule_id", "")).startswith(f"{policy}.")]}
            (args.out / f"ours_{program}.json").write_text(json.dumps(ours))
            theirs = json.loads((REFERENCES / reference).read_text())
            answer = http.post(f"{API}/packs/compare", json={
                "left": {"artifact": ours}, "right": {"artifact": theirs}, "aligned": True})
            answer.raise_for_status()
            body = answer.json()
            (args.out / f"aligned_{program}.json").write_text(json.dumps(body))
            print(json.dumps({"program": program, "left_jobs": len(ours["values"]),
                              "right_jobs": len(theirs["values"]), "summary": body.get("summary"),
                              "equivalence": body.get("equivalence"),
                              "cost_usd": (body.get("usage") or {}).get("cost_usd")}, indent=1), flush=True)


if __name__ == "__main__":
    main()
