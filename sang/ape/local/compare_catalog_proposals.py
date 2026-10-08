"""Snapshot a pack's catalog proposals from a running Plato, and compare two snapshots.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

    python scripts/local/compare_catalog_proposals.py snapshot baseline.json --tenant acra-lending
    python scripts/local/compare_catalog_proposals.py compare baseline.json now.json

A later extraction folds into the same store: proposals it re-finds keep their id, and the ones it
no longer finds stay as they were under their old ``set_id``. ``compare`` therefore reads the
newest ``set_id`` of the second snapshot as the new run unless ``--set`` names one.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

#: A field name that states a limit rather than a fact (min_, max_, a cap, a lookback).
_LIMIT = re.compile(r"(^|_)(min|max|minimum|maximum)(_|$)|limit|threshold|lookback|cap$")
#: Wording that makes two names for one fact differ: unit suffixes, boolean prefixes, abbreviations.
_NOISE = re.compile(r"(^|_)(is|has|status|required|allowed|pct|percent|months|days|years|count)(?=_|$)")
_ABBREVIATIONS = {"maximum": "max", "minimum": "min"}
SAMPLE = 8


def _stem(field: str) -> str:
    words = [_ABBREVIATIONS.get(w, w) for w in field.lower().split("_")]
    return _NOISE.sub("", "_".join(words)).replace("__", "_").strip("_")


def load(path: str) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def newest_set(proposals: list[dict[str, Any]]) -> str:
    return max(proposals, key=lambda p: p.get("last_seen") or "").get("set_id", "")


def describe(proposals: list[dict[str, Any]]) -> dict[str, Any]:
    fields = [p for p in proposals if p["catalog"]["op"] != "add_entity"]
    by_entity: dict[str, list[str]] = defaultdict(list)
    for p in fields:
        by_entity[p["catalog"]["entity"]].append(p["catalog"]["field"])
    clusters = []
    for entity, names in by_entity.items():
        stems: dict[str, list[str]] = defaultdict(list)
        for name in names:
            stems[_stem(name)].append(name)
        clusters += [(entity, group) for group in stems.values() if len(group) > 1]
    return {
        "total": len(proposals),
        "categories": dict(Counter(p["category"] for p in proposals)),
        "entities": len({p["catalog"]["entity"] for p in proposals}),
        "fields": len(fields),
        "limit_like": sorted(f"{p['catalog']['entity']}.{p['catalog']['field']}" for p in fields
                             if _LIMIT.search(p["catalog"]["field"])),
        "likely_synonyms": clusters,
        "names": {f"{p['catalog']['entity']}.{p['catalog']['field']}" for p in fields},
    }


def _print(label: str, d: dict[str, Any]) -> None:
    print(f"{label}: {d['total']} proposals, {d['entities']} entities, {d['fields']} fields, "
          f"categories {d['categories']}")
    print(f"  limit-like field names: {len(d['limit_like'])}  "
          f"{d['limit_like'][:SAMPLE]}")
    redundant = sum(len(g) - 1 for _, g in d["likely_synonyms"])
    print(f"  fields in a likely-synonym group beyond the first: {redundant} "
          f"in {len(d['likely_synonyms'])} groups")
    for entity, group in sorted(d["likely_synonyms"], key=lambda x: -len(x[1]))[:SAMPLE]:
        print(f"    {entity}: {', '.join(group)}")


async def _snapshot(args: argparse.Namespace) -> None:
    from jazzx_plato_client.client import PlatoClient

    async with PlatoClient(args.url, tenant_id=args.tenant) as plato:
        found = await plato.proposals(args.pack, kind="catalog")
    Path(args.output).write_text(json.dumps(found, indent=2) + "\n", encoding="utf-8")
    print(f"{len(found)} proposals written to {args.output}")


def _compare(args: argparse.Namespace) -> None:
    before, after = load(args.baseline), load(args.current)
    chosen = args.set or newest_set(after)
    new_run = [p for p in after if p.get("set_id", "") == chosen]
    _print("baseline", describe(before))
    _print(f"new run ({chosen})", describe(new_run))
    old, new = describe(before)["names"], describe(new_run)["names"]
    print(f"names in both: {len(old & new)}; only in baseline: {len(old - new)}; "
          f"only in the new run: {len(new - old)}")
    print(f"  only in the new run: {sorted(new - old)[:SAMPLE]}")
    left_over = [p for p in after if p.get("set_id", "") != chosen and p["status"] == "proposed"]
    if left_over:
        print(f"note: {len(left_over)} proposals from earlier runs are still pending in the store; "
              f"the review page shows them beside the new run's")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    snap = commands.add_parser("snapshot")
    snap.add_argument("output")
    snap.add_argument("--url", default="http://localhost:8000")
    snap.add_argument("--tenant", required=True)
    snap.add_argument("--pack", default="acra-dscr-policy")
    compare = commands.add_parser("compare")
    compare.add_argument("baseline")
    compare.add_argument("current")
    compare.add_argument("--set", help="the new run's set_id (default: the newest in current)")
    args = parser.parse_args(argv)
    if args.command == "snapshot":
        asyncio.run(_snapshot(args))
    else:
        _compare(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
