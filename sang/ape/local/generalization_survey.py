#!/usr/bin/env python3
"""Survey how general the SDK is, using jaci's scenarios as the yardstick. Read-only.

Part 1, per jaci scenario: how much is code (Python lines, own tools) and how much leans on the SDK and the
Plato client; per pack: how much is config. Part 2, in japes: domain words that belong to one scenario's field
(loan, patient, claim ...) found in SDK code, so a leak shows before a second domain trips over it.

Usage: generalization_survey.py [--jaci DIR] [--japes DIR] [--words a,b,c]

Author: Virendra Mehta <virendra.mehta@jazzx.ai>
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

DEFAULT_WORDS = ("loan", "borrower", "mortgage", "lender", "patient", "claim", "customer", "underwriting", "dscr")
CODE_SUFFIX = ".py"
CONFIG_SUFFIXES = {".yaml", ".yml", ".json", ".md", ".txt", ".csv"}
SKIP_PARTS = {"__pycache__", ".git", "node_modules", ".venv", "tests"}
SKIP_LEAK_PARTS = SKIP_PARTS | {"data", "sample_packs", "seed_packs", "seed_blueprints", "manifests"}
BYTES_PER_KB = 1024


def files(root: Path, suffixes: set[str], skip: set[str]):
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in suffixes and not skip & set(path.relative_to(root).parts):
            yield path


def lines_of(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def scenario_row(scenario: Path) -> tuple[int, int, int, int, int]:
    code = list(files(scenario, {CODE_SUFFIX}, SKIP_PARTS))
    text = [line for path in code for line in lines_of(path)]
    sdk = sum(1 for line in text if re.match(r"\s*(from|import)\s+jazzx_sdk", line))
    client = sum(1 for line in text if re.match(r"\s*(from|import)\s+jazzx_plato_client", line))
    tools = sum(1 for path in code if "tools" in path.relative_to(scenario).parts)
    return len(code), len(text), sdk, client, tools


def pack_row(pack: Path) -> tuple[int, int, int]:
    config = list(files(pack, CONFIG_SUFFIXES, SKIP_PARTS))
    code = list(files(pack, {CODE_SUFFIX}, SKIP_PARTS))
    return len(config), sum(path.stat().st_size for path in config) // BYTES_PER_KB, len(code)


def jaci_part(jaci: Path) -> None:
    print("## jaci scenarios (code and SDK reliance)\n")
    print("| scenario | py files | py lines | sdk imports | plato client imports | tools files |")
    print("|---|---|---|---|---|---|")
    for scenario in sorted(p for p in (jaci / "src/jaci/scenarios").iterdir() if p.is_dir() and p.name != "__pycache__"):
        print(f"| {scenario.name} | " + " | ".join(str(n) for n in scenario_row(scenario)) + " |")
    print("\n## jaci packs (config)\n")
    print("| pack | config files | config KB | py files |")
    print("|---|---|---|---|")
    for pack in sorted(p for p in (jaci / "config/packs").iterdir() if p.is_dir()):
        print(f"| {pack.name} | " + " | ".join(str(n) for n in pack_row(pack)) + " |")


def leak_part(japes: Path, words: tuple[str, ...]) -> None:
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, words)) + r")(?:s|_[a-z_]+)?\b", re.IGNORECASE)
    per_area: dict[str, Counter] = {}
    for path in files(japes / "jazzx_sdk", {CODE_SUFFIX, ".md"}, SKIP_LEAK_PARTS):
        area = "/".join(path.relative_to(japes / "jazzx_sdk").parts[:2])
        for line in lines_of(path):
            for match in pattern.finditer(line):
                per_area.setdefault(area, Counter())[match.group(1).lower()] += 1
    print("\n## domain words in jazzx_sdk (code and prompts, data folders skipped)\n")
    print("| area | total | by word |")
    print("|---|---|---|")
    for area, counts in sorted(per_area.items(), key=lambda kv: -sum(kv[1].values()))[:25]:
        detail = ", ".join(f"{w} {n}" for w, n in counts.most_common())
        print(f"| {area} | {sum(counts.values())} | {detail} |")
    print(f"\nareas with a hit: {len(per_area)}; total hits: {sum(sum(c.values()) for c in per_area.values())}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--jaci", type=Path, default=Path("/Users/sangit/src/jaci"))
    parser.add_argument("--japes", type=Path, default=Path("/Users/sangit/src/japes"))
    parser.add_argument("--words", default=",".join(DEFAULT_WORDS))
    args = parser.parse_args()
    jaci_part(args.jaci)
    leak_part(args.japes, tuple(w.strip() for w in args.words.split(",") if w.strip()))


if __name__ == "__main__":
    main()
