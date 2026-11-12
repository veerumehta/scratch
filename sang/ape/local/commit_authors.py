"""Which files in a range were added by someone else.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

A contributor's pull request or cherry-picked commit adds files that carry that contributor's header,
not ours, and an edit would put our name on their work. `foreign_added` lists the files a range adds
in commits whose author is not ours, so a check can skip them and report them once instead of failing.
The attribution check uses it, and `adversarial_review.sh` can print the same list as a [NOTE].

    python scripts/local/commit_authors.py [BASE]     # one "path<TAB>author" line per file (default origin/dev)
"""

from __future__ import annotations

import subprocess
import sys

#: The email in our `Author:` header; the checkout's own git identity is added to it (`own_emails`).
HEADER_EMAIL = "virendra.mehta@jazzx.ai"


def own_emails() -> set[str]:
    configured = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True, check=False)
    return {HEADER_EMAIL, configured.stdout.strip()} - {""}


def _run(args: list[str], cwd) -> list[str]:
    out = subprocess.run(["git", *args], capture_output=True, text=True, check=False, cwd=cwd).stdout
    return [line for line in out.splitlines() if line.strip()]


def foreign_added(base: str, *, own_emails: set[str], cwd=None) -> dict[str, str]:
    """``{path: author email}`` for each file ``base..HEAD`` adds whose first commit, followed through renames, is by an
    author outside ``own_emails``."""
    found: dict[str, str] = {}
    for path in _run(["diff", "--no-renames", "--name-only", "--diff-filter=A", base, "HEAD"], cwd):
        first = _run(["log", "--follow", "--diff-filter=A", "--format=%ae", "--", path], cwd)
        if first and first[-1] not in own_emails:
            found[path] = first[-1]
    return found


if __name__ == "__main__":
    for path, who in foreign_added(sys.argv[1] if len(sys.argv) > 1 else "origin/dev", own_emails=own_emails()).items():
        print(f"{path}\t{who}")
