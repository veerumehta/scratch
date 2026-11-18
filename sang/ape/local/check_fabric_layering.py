"""Warn-only: public methods ADDED to a service client in a git range that nothing above the client layer calls.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

    python scripts/local/check_fabric_layering.py [BASE..HEAD]   (default: the pushed refs from PUSH_REFS, else @{u}..HEAD)

Rule: higher-level abstractions live in the fabric layer so consumers rarely need the client. A public method new to a client
class in CLIENT_FILES, with no call to it (``.name(``) anywhere under jazzx_sdk or plato outside jazzx_sdk/clients, is printed as a
question, never a verdict: who is the consumer, and what layer do they stand at? (A consumer below the fabric, such as a service
that calls the generated client directly, is a reason to stay at the client.) The Strict and Workspace wrappers, the mock and
kh_protocol.py mirror the client and are not scanned. A name the same range also adds to a fabric store is skipped. Exit 0
always (2 only when the range cannot be read), so a push is never blocked.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

#: The service clients whose public methods are checked, one tuple so a new client is one line.
CLIENT_FILES = (
    "jazzx_sdk/clients/knowledge_hub_client.py",
    "jazzx_sdk/clients/kernel_client.py",
    "jazzx_sdk/clients/eval_service_client.py",
    "jazzx_sdk/clients/japes_queue_client.py",
)
#: Classes in those files that mirror the client rather than add to it.
WRAPPER_PREFIXES = ("Strict", "Workspace", "Mock", "_")
#: Where a caller above the client layer lives, and the part of it that is the client layer itself.
CALLER_ROOTS = ("jazzx_sdk", "plato")
CLIENT_LAYER = "jazzx_sdk/clients"
FABRIC_ROOT = "jazzx_sdk/fabric"


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def _show(rev: str, path: str) -> str | None:
    result = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


def _public_methods(source: str) -> set[tuple[str, str]]:
    """(class, method) of every public method of every client class (not a wrapper) in ``source``."""
    out: set[tuple[str, str]] = set()
    for node in ast.parse(source).body:
        if isinstance(node, ast.ClassDef) and node.name.endswith("Client") and not node.name.startswith(WRAPPER_PREFIXES):
            out |= {(node.name, item.name) for item in node.body
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and not item.name.startswith("_")}
    return out


def _added_to_fabric(base: str, head: str, rng_files: list[str]) -> set[str]:
    """Names of the methods the range adds to files under the fabric."""
    added: set[str] = set()
    for path in (f for f in rng_files if f.startswith(FABRIC_ROOT) and f.endswith(".py")):
        new, old = _show(head, path), _show(base, path)
        names = lambda src: {n.name for n in ast.walk(ast.parse(src)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}  # noqa: E731
        added |= names(new or "") - names(old or "")
    return added


def _called_above_the_client(head: str, name: str) -> bool:
    result = subprocess.run(
        ["git", "grep", "-l", "-E", rf"\.{name}\(", head, "--", *CALLER_ROOTS, f":(exclude){CLIENT_LAYER}"],
        capture_output=True, text=True)
    return bool(result.stdout.strip())


def findings(rng: str) -> list[tuple[str, str, str]]:
    base, _, head = rng.partition("..")
    head = head or "HEAD"
    changed = _git("diff", "--name-only", "--diff-filter=AM", rng, "--", "jazzx_sdk").split()
    in_fabric = _added_to_fabric(base, head, changed)
    found: list[tuple[str, str, str]] = []
    for path in (p for p in CLIENT_FILES if p in changed):
        new = _show(head, path)
        if new is None:
            continue
        added = _public_methods(new) - _public_methods(_show(base, path) or "")
        for cls, name in sorted(added):
            if name not in in_fabric and not _called_above_the_client(head, name):
                found.append((path.rsplit("/", 1)[-1], cls, name))
    return found


def main(argv: list[str]) -> int:
    if "--range" in argv:
        ranges = [argv[argv.index("--range") + 1]]
    elif argv:
        ranges = [argv[0]]
    else:
        sys.path.insert(0, str(Path(__file__).parent))
        import check_us_spelling as ranges_of

        ranges = ranges_of.ranges_from_push_refs(os.environ.get("PUSH_REFS", "")) or [ranges_of.default_range()]
    rows: list[tuple[str, str, str]] = []
    try:
        for rng in ranges:
            rows += findings(rng)
    except subprocess.CalledProcessError:
        print("  ! fabric layering check: could not read the range, skipped")
        return 2
    if not rows:
        print("  ok  every public client method added has a caller above the client layer, or none was added")
        return 0
    print(f"  !  {len(rows)} public client method(s) added with no caller above the client layer")
    print("     (higher-level abstractions live in the fabric layer so consumers rarely need the client)")
    for file, cls, name in sorted(set(rows)):
        print(f"      client method with no fabric abstraction: {cls}.{name}  [{file}]  (who is the consumer and what layer do they stand at?)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
