#!/usr/bin/env python3
"""List large non-route functions under plato/ (candidates that may belong in jazzx_sdk).

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

usage: plato_helpers_scan.py [repo root, default /Users/sangit/src/japes]
"""
import ast
import subprocess
import sys
from pathlib import Path

DEFAULT_ROOT = "/Users/sangit/src/japes"
MIN_LINES = 35
SHOWN = 20
ROUTE_VERBS = {"get", "post", "put", "patch", "delete", "websocket", "api_route"}


def is_route(node):
    for dec in node.decorator_list:
        target = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(target, ast.Attribute) and target.attr in ROUTE_VERBS:
            return True
    return False


def main(root: Path) -> None:
    paths = subprocess.run(["git", "ls-files", "plato"], capture_output=True, text=True, cwd=root).stdout.split()
    found = []
    for rel in paths:
        if not rel.endswith(".py") or "/migrations/" in rel or "alembic" in rel:
            continue
        tree = ast.parse((root / rel).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not is_route(node):
                size = node.end_lineno - node.lineno + 1
                if size >= MIN_LINES:
                    found.append((size, rel, node.name))
    print(len(found), f"non-route functions of {MIN_LINES} or more lines under plato/")
    for size, rel, name in sorted(found, reverse=True)[:SHOWN]:
        print(f"  {size:4} {rel}:{name}")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT))
