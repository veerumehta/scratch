"""List docstrings changed since a revision that a model or a schema reads.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Usage: model_facing_docstrings.py <rev> [paths...]

Flags a changed docstring on a function decorated as a tool (its description) or on a class
that subclasses a pydantic model (its JSON schema description).
"""

from __future__ import annotations

import ast
import subprocess
import sys

TOOL_DECORATORS = {"function_tool", "tool", "mcp_tool"}
MODEL_BASES = {"BaseModel", "BaseSettings", "RootModel"}


def _owners(source: str) -> dict[str, tuple[str, str]]:
    found = {}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names = {getattr(d, "id", None) or getattr(d, "attr", None)
                     or getattr(getattr(d, "func", None), "id", None)
                     or getattr(getattr(d, "func", None), "attr", None)
                     for d in node.decorator_list}
            if names & TOOL_DECORATORS:
                found[f"tool {node.name}"] = ("tool", ast.get_docstring(node) or "")
        elif isinstance(node, ast.ClassDef):
            bases = {getattr(b, "id", None) or getattr(b, "attr", None) for b in node.bases}
            if bases & MODEL_BASES:
                found[f"model {node.name}"] = ("model", ast.get_docstring(node) or "")
    return found


def main(rev: str, paths: list[str]) -> int:
    changed = subprocess.run(["git", "diff", "--name-only", rev, "--", *paths],
                             capture_output=True, text=True, check=True).stdout.split()
    hits = 0
    for path in (p for p in changed if p.endswith(".py")):
        try:
            old = _owners(subprocess.run(["git", "show", f"{rev}:{path}"],
                                         capture_output=True, text=True, check=True).stdout)
        except subprocess.CalledProcessError:
            continue
        new = _owners(open(path, encoding="utf-8").read())
        for key, (_, doc) in new.items():
            if key in old and old[key][1] != doc:
                hits += 1
                print(f"{path}: {key}")
    print(f"{hits} model-facing docstring(s) changed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2:] or ["."]))
