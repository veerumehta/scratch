#!/usr/bin/env python3
"""Flag references to gitignored planning files and plan labels in what a push adds.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Tracked code, tests, docs and commit messages must not name a gitignored file (plans, status notes, the
CHANGELOG, the session guide) or use the private labels of one (``K3``, ``Phase 4``, ``UAF``): a reader of
the repository cannot open the file, so the label means nothing and the rule it stood for is lost. State
the rule in a clause instead.

Checked, the same way `check_us_spelling.py` does it:

  * the added lines of every tracked text file in the pushed range,
  * the commit messages in the range.

Two strengths:

  * FAIL (blocks the push): file names and paths of gitignored files, and the label shapes that measured
    zero false positives over the cleaned tree and over the added lines of the last 200 commits
    (`K<n>`, `Phase <n>`, `Phase P<n>`, `UAF`, `E<nn>`, "kernel-salvage").
  * WARN (never blocks): shapes with legitimate uses, listed so a reviewer looks (`item <n>`,
    `slice <n>`, `step <n> of`, "per the plan", a bare CHANGELOG, "the chassis doc").

Shapes that are real terms here and are not checked: `P<n>` (a policy id in test data, ARCHITECTURE.md
principles), `G<n>` (guideline set versions), `§` (named external specs), `plan_*` identifiers in code.

Escape hatches:
  * put `plan-ref-ok` anywhere on the line (a comment is fine),
  * `JAPES_SKIP_PLAN_REFS=1` skips the whole check (the hook honors it).

  check_plan_refs.py                         # default range: upstream, else origin/plato, dev, main
  check_plan_refs.py --range A..B            # an explicit range
  PUSH_REFS="$(cat)" check_plan_refs.py      # the four-column text git gives a pre-push hook
  check_plan_refs.py --message FILE          # one commit message (the commit-msg hook), hard shapes only
  check_plan_refs.py --self-test             # the patterns against known cases

Exit 0 when clean or only warnings, 1 when a hard reference was added, 2 on a usage or git error.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from check_us_spelling import (  # the range logic is one implementation
    added_lines, commit_messages, default_range, ranges_from_push_refs)

MARKER = "plan-ref-ok"
#: A line longer than this is generated or minified text, not prose.
MAX_LINE_CHARS = 600
#: A gitignored file's own name, with its extension, must be at least this long to be searched for by name.
MIN_NAME_CHARS = 12
#: Where the gitignored plans and status notes live, read only to learn their names.
IGNORED_DIRS = (Path(__file__).resolve().parents[1] / "plans", Path(__file__).resolve().parents[1] / "status")

#: (description, regex). A hit is a FAIL.
HARD: tuple[tuple[str, str], ...] = (
    ("a gitignored docs path", r"\bdocs/(?:plans|status)\b"),
    ("a plan, done, note or status file name",
     r"\b(?:plan|done|stale|superseded|addendum|note|design_note)_[A-Za-z0-9][A-Za-z0-9_.-]*\.md\b"),
    ("a plan name", r"\bplan_[A-Z][A-Za-z0-9]*_[A-Za-z0-9_]+"),
    ("the CHANGELOG or session guide named as a file", r"\b(?:CHANGELOG|CLAUDE|AGENTS)\.md\b"),
    ("a plan item code (K<n>)", r"\bK\d{1,2}\b"),
    ("a plan phase label", r"\bPhases? \d+\b|\bPhase P\d\b"),
    ("a plan label (UAF)", r"\bUAF\b"),
    ("a plan item code (E<nn>)", r"\bE\d{2}\b"),
    ("a plan name (kernel-salvage)", r"kernel-salvage"),
)
#: (description, regex). A hit is a WARN.
WARN: tuple[tuple[str, str], ...] = (
    ("an item number of a plan", r"\bitems? #?\d+\b"),
    ("a slice number of a plan", r"\bslice \d+\b"),
    ("a step number of a plan", r"\bstep \d+ of\b"),
    ("a reference to a plan", r"\b(?:the|this) plan's own\b|\bper the plan\b|\bsee the plan\b"),
    ("a design document by role", r"\b(?:chassis|architecture|Studio design) (?:doc|review)\b"),
    ("the CHANGELOG named", r"\bCHANGELOG\b"),
)
_HARD = [(d, re.compile(p)) for d, p in HARD]
_WARN = [(d, re.compile(p)) for d, p in WARN]
_URL = re.compile(r"\S*://\S*")


def ignored_names() -> list[str]:
    """The names (no extension) of the gitignored plan and status files on this machine, long enough to be specific."""
    names: set[str] = set()
    for directory in IGNORED_DIRS:
        if directory.is_dir():
            names.update(path.stem for path in directory.iterdir()
                         if path.is_file() and len(path.stem) + 3 >= MIN_NAME_CHARS)
    return sorted(names, key=len, reverse=True)


def _name_pattern(names: list[str]) -> re.Pattern | None:
    return re.compile(r"\b(?:%s)\b" % "|".join(re.escape(n) for n in names)) if names else None


def findings_in(text: str, names: re.Pattern | None = None, *, warn: bool = True) -> list[tuple[str, str]]:
    """(severity, description) per reference on one line; empty when the line carries the escape marker."""
    if MARKER in text or len(text) > MAX_LINE_CHARS:
        return []
    text = _URL.sub(" ", text)
    found = [("FAIL", d) for d, rx in _HARD if rx.search(text)]
    if names is not None and names.search(text) and not any(s == "FAIL" and d.startswith("a plan") for s, d in found):
        found.append(("FAIL", "the name of a gitignored plan or status file"))
    if warn:
        found += [("WARN", d) for d, rx in _WARN if rx.search(text)]
    return found


def check(ranges: list[str]) -> tuple[list[str], list[str]]:
    """``(failures, warnings)``, each ``where: description: the line``."""
    names = _name_pattern(ignored_names())
    fails: list[str] = []
    warns: list[str] = []

    def record(where: str, text: str) -> None:
        for severity, description in findings_in(text, names):
            (fails if severity == "FAIL" else warns).append(f"{where}: {description}: {text.strip()[:100]}")

    for rng in ranges:
        for path, lineno, text in added_lines(rng):
            record(f"{path}:{lineno}", text)
        for sha, message in commit_messages(rng):
            for lineno, text in enumerate(message.splitlines(), start=1):
                record(f"commit {sha} message line {lineno}", text)
    return sorted(set(fails)), sorted(set(warns))


def check_message(path: str) -> list[str]:
    """Hard findings in one commit message file, git's own comment lines ignored."""
    names = _name_pattern(ignored_names())
    out = []
    for lineno, text in enumerate(Path(path).read_text().splitlines(), start=1):
        if text.startswith("#"):
            continue
        out += [f"line {lineno}: {d}: {text.strip()[:100]}"
                for s, d in findings_in(text, names, warn=False) if s == "FAIL"]
    return out


SHOULD_FAIL = (
    "job lint gates K3 K4 K9 K10",
    "See docs/plans/plan_eval_service_contract_convergence.md for the build-out",
    "# Phase 3 of the plan",
    "see plan_JAPES_2_7_0_EXPERT_SURFACE_AND_ANSWER_CONTRACT",
    "recorded in the CHANGELOG.md",
    "per CLAUDE.md the version stays",
    "UAF item 7",
    "the E18 item",
    "kernel-salvage hardening",
    "see done_2_6_9_scope.md",
)
SHOULD_PASS = (
    "job lint gates that bound a call, and a retry budget",
    'policy_id="P1", version="1.0.0"',
    "(ARCHITECTURE.md P10)",
    "a version as 3 or G3",
    "(Schema Spec v1.0 §7.1)",
    "plan_input_tokens and plan_estimate",
    "the plan call crossed the ceiling",
    "item 2 of the list",
    "See https://example.com/docs/plans/overview",
    "K-means over the rows",
    "a hex id 0xE12F and a sha k3f9",
    "the vendor says Phase 3 of the rollout  # plan-ref-ok",
)


def self_test() -> int:
    missed = [t for t in SHOULD_FAIL if not any(s == "FAIL" for s, _ in findings_in(t))]
    wrong = [(t, findings_in(t)) for t in SHOULD_PASS if any(s == "FAIL" for s, _ in findings_in(t))]
    for text in missed:
        print(f"missed: {text!r}")
    for text, found in wrong:
        print(f"false positive: {text!r} -> {found}")
    warned = [t for t in ("see the Studio design doc", "item 4 of the plan", "per the plan") if not
              any(s == "WARN" for s, _ in findings_in(t))]
    for text in warned:
        print(f"warning missed: {text!r}")
    ok = not (missed or wrong or warned)
    print("self-test:", "ok" if ok else "FAILED")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if os.environ.get("JAPES_SKIP_PLAN_REFS") == "1":
        print("  --  skipped (JAPES_SKIP_PLAN_REFS=1)")
        return 0
    if "--self-test" in argv:
        return self_test()
    if "--message" in argv:
        try:
            found = check_message(argv[argv.index("--message") + 1])
        except (OSError, IndexError) as exc:
            print(f"plan references: not checked: {exc}", file=sys.stderr)
            return 2
        for line in found:
            print(f"plan reference in the commit message, {line}", file=sys.stderr)
        if found:
            print("State the rule in a clause; do not name a gitignored file or a plan label "
                  f"(mark a quoted external name with `{MARKER}`).", file=sys.stderr)
        return 1 if found else 0
    try:
        if "--range" in argv:
            ranges = [argv[argv.index("--range") + 1]]
        else:
            ranges = ranges_from_push_refs(os.environ.get("PUSH_REFS", "")) or [default_range()]
        fails, warns = check(ranges)
    except (RuntimeError, IndexError) as exc:
        print(f"  --  not checked: {exc}")
        return 2
    for line in warns[:30]:
        print(f"  warn  {line}")
    if len(warns) > 30:
        print(f"  warn  ... and {len(warns) - 30} more")
    if not fails:
        print(f"  ok  no plan reference added ({', '.join(ranges)})" + (f"; {len(warns)} warning(s)" if warns else ""))
        return 0
    print("  FAIL  a gitignored file or a plan label was added (state the rule in a clause instead):")
    for line in fails[:60]:
        print(f"        {line}")
    if len(fails) > 60:
        print(f"        ... and {len(fails) - 60} more")
    print(f"        mark a quoted external name with `{MARKER}` on the line")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
