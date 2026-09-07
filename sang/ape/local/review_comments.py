"""Show every comment and docstring line a diff adds, for a human read-through.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Code is reviewed by reading the code; prose is not. Comments and docstrings slip through a large
diff unread, and they are exactly where a machine-written tell shows up — a summary of what the
line below does, hedging, or a register that doesn't match the rest of the file. This pulls just
the added prose out so it can be scanned on its own.

    python scripts/local/review_comments.py                 # added prose vs origin/dev
    python scripts/local/review_comments.py --base HEAD~1
    python scripts/local/review_comments.py --paths jazzx_sdk/llm
    python scripts/local/review_comments.py --stats          # per-file counts only
"""

from __future__ import annotations

import argparse
import re
import subprocess

# An added line that is a `#` comment, or sits inside a docstring. Detected loosely on purpose: a
# false positive costs one line of reading, a miss defeats the point.
COMMENT = re.compile(r"^\+\s*#")
# Every triple-quote on the line, wherever it sits. Matching only at line start misses a docstring
# that closes mid-line, which leaves the state inverted for the rest of the file — printing code as
# prose and dropping the prose itself.
TRIPLE = re.compile(r'"""|\'\'\'')
OPENS_DOCSTRING = re.compile(r'^\s*(?:[rRbBuUfF]{0,2})("""|\'\'\')')


def diff_lines(base: str, paths: list[str]) -> list[str]:
    # `base` alone, not `base..HEAD`: the working tree has to be included, or prose edited since
    # the last commit is invisible to the very review this exists for.
    cmd = ["git", "diff", "-U0", base, "--"]
    out = subprocess.run(cmd + (paths or []), capture_output=True, text=True, check=False)
    return out.stdout.splitlines()


def collect(lines: list[str]) -> dict[str, list[str]]:
    """Map file -> added prose lines, tracking docstring state so bodies are included."""
    found: dict[str, list[str]] = {}
    current = ""
    in_docstring = False

    for line in lines:
        if line.startswith("+++ b/"):
            current = line[6:]
            in_docstring = False
            continue
        if line.startswith("@@"):
            # Hunks are disjoint under -U0, so a docstring whose closing line is unchanged (and
            # therefore absent) would leave the state open for the rest of the file, printing all
            # the code after it as prose. Each hunk starts fresh: a docstring straddling a hunk
            # boundary loses a few lines, which is far better than a runaway.
            in_docstring = False
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        if not current.endswith((".py", ".yml", ".yaml", ".toml", ".sh")):
            continue

        body = line[1:].rstrip()
        was_in_docstring = in_docstring
        # Each triple-quote flips the state, so a docstring that opens and closes on one line nets
        # out to no change and one closing mid-line is caught.
        if TRIPLE.findall(body):
            in_docstring = (len(TRIPLE.findall(body)) % 2 == 1) != in_docstring

        if was_in_docstring or in_docstring or OPENS_DOCSTRING.match(body) or COMMENT.match(line):
            found.setdefault(current, []).append(body)

    return found


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="origin/dev", help="git ref to diff against")
    ap.add_argument("--paths", nargs="*", default=[], help="limit to these paths")
    ap.add_argument("--stats", action="store_true", help="per-file counts only")
    ap.add_argument("--contains", metavar="TEXT",
                    help="only prose lines containing TEXT (e.g. an em-dash, to find them)")
    args = ap.parse_args()

    found = collect(diff_lines(args.base, args.paths))
    if args.contains:
        found = {k: [line for line in v if args.contains in line] for k, v in found.items()}
        found = {k: v for k, v in found.items() if v}
    if not found:
        print("no added comments or docstrings")
        return

    total = sum(len(v) for v in found.values())
    if args.stats:
        for path in sorted(found, key=lambda p: -len(found[p])):
            print(f"{len(found[path]):>5}  {path}")
        print(f"\n{total} added prose line(s) across {len(found)} file(s)")
        return

    for path in sorted(found):
        print(f"\n{'=' * 78}\n{path}  ({len(found[path])} lines)\n{'=' * 78}")
        for body in found[path]:
            print(body)
    print(f"\n{total} added prose line(s) across {len(found)} file(s)")


if __name__ == "__main__":
    main()
