"""Pair Acra's K-Studio jobs with ours from the bundle (no Plato, no loan data), per program.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Reuses `acra_compare_sets.compare`: lexical candidates, then one model call per K-Studio job labelling each
candidate same, differs, partial or none. Writes pairs.json (the matched pairs by id) under --out.

    python scripts/local/acra_e2e_pair.py --out DIR [--budget 3]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, "/Users/sangit/src/japes")
sys.path.insert(0, str(HERE))

from acra_compare_sets import _acra, _schema, compare  # noqa: E402
from acra_coverage_report import Tally  # noqa: E402

BUNDLE = Path("/Users/sangit/src/japes/docs/status/Acra/acra_bundle/3_sdk_jtbds")
PROGRAMS = {"standard": "standard_policy.yaml", "platinum": "platinum_policy.yaml"}


def _ours(program: str) -> list[dict]:
    items = []
    for rule in yaml.safe_load((BUNDLE / PROGRAMS[program]).read_text())["rules"]:
        c = rule["condition"]
        if c.get("kind") != "procedure":
            continue
        items.append({"id": rule["rule_id"], "section": rule["rule_id"].split(".")[1], "title": c.get("purpose", ""),
                      "reads": c.get("reads") or [], "text": "\n".join([*(c.get("steps") or []), *(c.get("checks") or [])])})
    return items


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--budget", type=float, default=3.0)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    from jazzx_sdk.agents.service import AgentExecutionService

    agent, Labels, results = Tally(AgentExecutionService(), args.budget), _schema(), {}
    for program in PROGRAMS:
        r = await compare(agent, Labels, _acra(program), _ours(program))
        results[program] = {"left_items": r["left_items"], "right_items": r["right_items"], "left_best": r["left_best"],
                            "right_unmatched": r["right_unmatched"],
                            "pairs": [{"kstudio": row["id"], "ours": m["right"], "relation": m["relation"], "note": m["note"]}
                                      for row in r["rows"] for m in row["matches"] if m["right"]]}
        print(program, r["left_best"], f"cost ${agent.cost:.4f}", flush=True)
    results["cost"] = agent.summary()
    (args.out / "pairs.json").write_text(json.dumps(results, indent=1))
    print(agent.summary())


if __name__ == "__main__":
    asyncio.run(main())
