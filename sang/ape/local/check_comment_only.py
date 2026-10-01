"""Check that the working tree differs from a revision only in docstrings and comments.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Usage: check_comment_only.py <rev> [paths...]

For every changed .py file under the paths, parses both versions, drops every docstring and
compares the ASTs. Prints each file whose code changed; exits 1 if any did.
"""

from __future__ import annotations

import ast
import subprocess
import sys


def _stripped(source: str) -> str:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if (isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                and body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            node.body = body[1:] or [ast.Pass()]
    return ast.dump(tree, include_attributes=False)


def main(rev: str, paths: list[str]) -> int:
    changed = subprocess.run(["git", "diff", "--name-only", rev, "--", *paths],
                             capture_output=True, text=True, check=True).stdout.split()
    broken = []
    for path in (p for p in changed if p.endswith(".py")):
        try:
            old = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True,
                                 text=True, check=True).stdout
        except subprocess.CalledProcessError:
            continue                                       # new since rev
        try:
            new = open(path, encoding="utf-8").read()
        except FileNotFoundError:
            broken.append(f"{path} (deleted)")
            continue
        if _stripped(old) != _stripped(new):
            broken.append(path)
    for path in broken:
        print(path)
    print(f"{len(changed)} changed, {len(broken)} with code changes")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2:] or ["."]))
