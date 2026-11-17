"""Warn-only: functions ADDED under plato/ in a git range that look like SDK logic, not hosting.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

    python scripts/local/check_plato_layering.py [BASE..HEAD]     (default: the pushed refs from PUSH_REFS, else @{u}..HEAD)

Rule: logic lives in jazzx_sdk; plato/ is the hosted shell (routes, page wiring, boot, job entry points, seed and demo data).
A function (a closure inside a router factory included) added under plato/ is listed when it is at least MIN_LINES long, is not an HTTP handler (not decorated with a
router/app attribute) and names no HTTP type (Request, Response, HTTPException, Depends, APIRouter, WebSocket) and imports
nothing from fastapi/starlette inside it. Each is a question, never a verdict: would a second host need it? Exit 0 always
(2 only when the range cannot be read), so a push is never blocked.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

#: A function shorter than this is glue, not logic.
MIN_LINES = 15
#: Names that tie a function to HTTP hosting.
HTTP_NAMES = {"Request", "Response", "HTTPException", "Depends", "APIRouter", "WebSocket", "StreamingResponse", "JSONResponse",
              "PlainTextResponse", "HTMLResponse", "FileResponse", "RedirectResponse", "UploadFile"}
#: Paths under plato/ that are not hosting logic candidates (revisions of the database, static pages).
SKIP_PARTS = ("plato/migrations/", "plato/static/")


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def _functions(source: str) -> dict[str, ast.AST]:
    """Every function by qualified name: top level, methods, and closures (a helper inside a router factory counts on its own;
    the factory itself is HTTP wiring and a closure is judged on what it names)."""
    out: dict[str, ast.AST] = {}

    def visit(body: list[ast.stmt], prefix: str) -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out[prefix + node.name] = node
                visit(node.body, f"{prefix}{node.name}.")
            elif isinstance(node, ast.ClassDef):
                visit(node.body, f"{prefix}{node.name}.")

    visit(ast.parse(source).body, "")
    return out


def _is_http(fn: ast.AST) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.Name) and node.id in HTTP_NAMES:
            return True
        if isinstance(node, ast.Attribute) and node.attr in HTTP_NAMES:
            return True
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", None) or ""
            if module.split(".")[0] in ("fastapi", "starlette") or any(a.name.split(".")[0] in ("fastapi", "starlette") for a in node.names):
                return True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for deco in node.decorator_list:
                text = ast.unparse(deco)
                if text.startswith(("router.", "app.", "api.")):
                    return True
    return False


def candidates(rng: str) -> list[tuple[str, str, int]]:
    base, _, head = rng.partition("..")
    head = head or "HEAD"
    files = [f for f in _git("diff", "--name-only", "--diff-filter=AM", rng, "--", "plato").split()
             if f.endswith(".py") and not f.startswith(SKIP_PARTS)]
    found: list[tuple[str, str, int]] = []
    for path in files:
        try:
            new = _functions(_git("show", f"{head}:{path}"))
        except (subprocess.CalledProcessError, SyntaxError):
            continue
        try:
            old = set(_functions(_git("show", f"{base}:{path}")))
        except (subprocess.CalledProcessError, SyntaxError):
            old = set()
        for name, fn in new.items():
            size = fn.end_lineno - fn.lineno + 1
            if name in old or size < MIN_LINES or _is_http(fn):
                continue
            found.append((path, name, size))
    return sorted(found, key=lambda row: -row[2])


def main(argv: list[str]) -> int:
    if "--range" in argv:
        ranges = [argv[argv.index("--range") + 1]]
    elif argv:
        ranges = [argv[0]]
    else:
        sys.path.insert(0, str(Path(__file__).parent))
        import check_us_spelling as ranges_of          # the same pushed-range logic the spelling check uses

        ranges = ranges_of.ranges_from_push_refs(os.environ.get("PUSH_REFS", "")) or [ranges_of.default_range()]
    rows: list[tuple[str, str, int]] = []
    try:
        for rng in ranges:
            rows += candidates(rng)
    except subprocess.CalledProcessError:
        print("  ! layering check: could not read the range, skipped")
        return 2
    if not rows:
        print(f"  ok  no function of {MIN_LINES}+ lines added under plato/ that is free of HTTP types")
        return 0
    print(f"  !  {len(rows)} function(s) added under plato/ with {MIN_LINES}+ lines and no HTTP types: candidate for jazzx_sdk")
    print("     (would a second host need it? plato/ is the hosted shell: routes, page wiring, boot, job entry points, seed data)")
    for path, name, size in sorted(set(rows), key=lambda row: -row[2]):
        print(f"      {path}:{name}  {size} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
