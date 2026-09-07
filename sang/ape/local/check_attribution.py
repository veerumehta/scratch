"""Check that new files carry author attribution.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Every file added to this repo carries an ``Author:`` line, and nothing anywhere may hint that the
work was AI-assisted. Both are easy to forget on a file created mid-task and awkward to notice in a
large diff, so this checks them mechanically.

    python scripts/check_attribution.py              # files added vs origin/dev, plus untracked
    python scripts/check_attribution.py --base main  # compare against a different base
    python scripts/check_attribution.py path/to/f.py # just these paths

Exit 1 if anything is missing attribution or carries an AI-attribution marker, so it can gate a
commit or a CI step.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ATTRIBUTION = "Author: Virendra Mehta <virendra.mehta@jazzx.ai>"

# Extensions that carry a header comment or docstring. Data files (.json, .lock) are excluded:
# there is nowhere to put a comment, and a stray key would change the content digest.
CHECKED_SUFFIXES = {".py", ".yml", ".yaml", ".sh", ".toml", ".md"}

# Anything implying the work was machine-generated. Checked case-insensitively over the whole file.
AI_MARKERS = re.compile(
    r"co-authored-by:\s*claude|generated with \[?claude|🤖 generated|"
    r"claude\s+(opus|sonnet|haiku)|anthropic\.com/claude-code",
    re.IGNORECASE,
)


def _git(*args: str) -> list[str]:
    out = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    return [line for line in out.stdout.splitlines() if line.strip()]


def added_files(base: str) -> list[Path]:
    """Files added relative to ``base``, plus anything untracked — i.e. everything new."""
    tracked = _git("diff", "--name-only", "--diff-filter=A", f"{base}..HEAD")
    untracked = _git("ls-files", "--others", "--exclude-standard")
    seen: dict[str, None] = {}
    for name in (*tracked, *untracked):
        seen.setdefault(name, None)
    return [Path(n) for n in seen]


def check(paths: list[Path]) -> int:
    missing: list[Path] = []
    flagged: list[tuple[Path, str]] = []

    this_file = Path(__file__).resolve()
    for path in paths:
        if not path.is_file() or path.suffix not in CHECKED_SUFFIXES:
            continue
        # This file spells the markers out in order to search for them, so it always matches itself.
        if path.resolve() == this_file:
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        if ATTRIBUTION not in text:
            missing.append(path)
        found = AI_MARKERS.search(text)
        if found:
            flagged.append((path, found.group(0)))

    for path in missing:
        print(f"  MISSING attribution  {path}")
    for path, marker in flagged:
        print(f"  AI MARKER {marker!r} in  {path}")

    if not missing and not flagged:
        print(f"all {len(paths)} new file(s) attributed, no AI markers")
        return 0
    print(f"\nAdd this line to each file's header comment or docstring:\n    {ATTRIBUTION}")
    return 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", help="specific paths; default is everything new vs --base")
    ap.add_argument("--base", default="origin/dev", help="git ref to diff against (default origin/dev)")
    args = ap.parse_args()

    paths = [Path(p) for p in args.paths] if args.paths else added_files(args.base)
    if not paths:
        print("no new files to check")
        raise SystemExit(0)
    raise SystemExit(check(paths))


if __name__ == "__main__":
    main()
