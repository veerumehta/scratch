"""Who still reads kernel agent rows, and how.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Phase 6's kernel converter is built, and nobody has counted what it would run against. This is that
count: a read-only sweep of the sibling checkouts for every way a caller can reach a kernel `Agent`
row, grouped by how hard each one is to move.

Three access paths, and they do not cost the same to migrate:

* **db**    -- direct SQLModel/SQLAlchemy against kernel's `agent` table. Moves only when kernel's
               database does, so these gate the retirement.
* **http**  -- calls kernel's agent API, via the generated `kernel_client` package or japes'
               `KernelClient` wrapper. Repointable at Plato without touching kernel.
* **embed** -- the caller carries its own agent definitions and never reads kernel at all. Already
               migrated in every sense that matters; counted so the total is honest.

**Generated code is excluded, and that is the difference between a useful number and a useless
one.** A first pass counted 572 "http callers"; almost all of them were `client-api`'s generated
kernel client (one file per route, so it reproduces kernel's API surface rather than using it) and
juno's generated file for *its own* assistant API. Matching a `/agents` URL string finds providers
and client libraries as readily as callers. What actually indicates a dependency on kernel's agent
API is importing the client, so that is what this matches.

Counts are **distinct files**, not lines: twelve calls in one module is one thing to migrate, not
twelve.

Read-only: greps checkouts, never opens a database, never writes. Names and line numbers only,
never file bodies, since some of these repos hold credentials in config.

Usage:
  ./scripts/local/kernel_agent_callers.py                  # every sibling repo
  ./scripts/local/kernel_agent_callers.py juno jaci        # named repos only
  ./scripts/local/kernel_agent_callers.py --detail         # every hit, not just the roll-up
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

SRC = Path("/Users/sangit/src")

#: Repos worth asking. kernel itself is excluded: it owns the table, so every line matches and none
#: of them is a caller.
DEFAULT_REPOS = [
    "juno", "jaci", "jazzx-assistant", "assistant", "macer", "macer-japes",
    "k9", "knowledge_hub", "eval-service", "client-api", "policy-workbench",
]

#: (access path, label, regex). Ordered most-expensive-first so a line that matches two is
#: attributed to the one that actually gates the migration.
PATTERNS: list[tuple[str, str, str]] = [
    ("db", "imports kernel's agent models", r"from app\.agent(\.models)?\s+import|import app\.agent"),
    ("db", "declares an agent table", r"""__tablename__\s*=\s*["']agent["']"""),
    ("http", "imports the generated kernel client's agent API",
     r"from kernel_client[\w.]*\.agents?\b|kernel_client\.api\.agents"),
    ("http", "uses japes' KernelClient", r"\bKernelClient\b|kernel_client\.\w*agent"),
    ("embed", "builds a spec in code", r"InteractiveAgentSpec\("),
    ("embed", "ships a profile directory", r"profile\.yaml"),
]

_SKIP_DIRS = {".venv", "node_modules", "__pycache__", ".git", "dist", "build", ".mypy_cache"}

#: Generated code reproduces an API surface rather than depending on it. Counting it answers "how
#: many routes does kernel have", which nobody asked.
_GENERATED_MARKERS = ("repo_clients/", "/api/rest/", "_pb2", "openapi_client", "generated/")


def _repo_hits(repo: Path, pattern: str) -> list[tuple[str, int, str]]:
    """Every match for one pattern, as (path, lineno, matched-line-trimmed)."""
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "grep", "-nIE", "--", pattern],
            capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return []
    if out.returncode not in (0, 1):
        return []

    hits = []
    for line in out.stdout.splitlines():
        parts = line.split(":", 2)
        if len(parts) != 3:
            continue
        path, lineno, text = parts
        if any(skip in path for skip in _SKIP_DIRS):
            continue
        if any(marker in path for marker in _GENERATED_MARKERS):
            continue
        hits.append((path, int(lineno), text.strip()[:120]))
    return hits


def audit(repos: list[str]) -> dict[str, dict[str, list]]:
    """repo -> access path -> [(label, path, lineno, text)]."""
    results: dict[str, dict[str, list]] = {}
    for name in repos:
        repo = SRC / name
        if not (repo / ".git").exists():
            continue

        seen: set[str] = set()
        by_access: dict[str, list] = defaultdict(list)
        for access, label, pattern in PATTERNS:
            for path, lineno, text in _repo_hits(repo, pattern):
                if path in seen:        # one file is one migration; first pattern wins
                    continue
                seen.add(path)
                by_access[access].append((label, path, lineno, text))
        results[name] = dict(by_access)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repos", nargs="*", default=None)
    parser.add_argument("--detail", action="store_true", help="list every hit")
    args = parser.parse_args()

    results = audit(args.repos or DEFAULT_REPOS)

    print("files touching kernel agent rows (generated clients excluded)\n")
    print(f"{'repo':<22} {'db':>4} {'http':>6} {'embed':>6}   verdict")
    print("-" * 78)
    totals = defaultdict(int)
    for name, by_access in sorted(results.items()):
        db = len(by_access.get("db", []))
        http = len(by_access.get("http", []))
        embed = len(by_access.get("embed", []))
        totals["db"] += db
        totals["http"] += http
        totals["embed"] += embed

        if db:
            verdict = "blocks retirement: reads the table directly"
        elif http:
            verdict = "repointable at Plato without touching kernel"
        elif embed:
            verdict = "already independent of kernel"
        else:
            verdict = "no kernel agent usage found"
        print(f"{name:<22} {db:>4} {http:>6} {embed:>6}   {verdict}")

    print("-" * 78)
    print(f"{'TOTAL':<22} {totals['db']:>4} {totals['http']:>6} {totals['embed']:>6}")

    if args.detail:
        for name, by_access in sorted(results.items()):
            for access in ("db", "http", "embed"):
                for label, path, lineno, text in by_access.get(access, []):
                    print(f"\n[{access}] {name}/{path}:{lineno}  ({label})\n    {text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
