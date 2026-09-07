"""Replace em-dashes in a file with explicit, hand-chosen punctuation.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Em-dashes are not allowed in our prose, and a blind sweep is the wrong fix: the right replacement
is a comma, colon, semicolon, full stop or parentheses depending on what the dash was doing. This
applies a mapping the author writes out, then reports anything it did not cover so nothing is
silently left behind.

    python scripts/local/dedash.py path/to/file.md --report     # list remaining em-dash lines
    python scripts/local/dedash.py path/to/file.md              # apply RULES, then report

Add pairs to RULES for the file being cleaned. Each is matched literally and must be unique, so a
wrong guess fails loudly rather than corrupting a similar sentence elsewhere.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

EM = "—"

# (old, new). Written out by hand: each dash gets the punctuation its sentence actually wants.
RULES: list[tuple[str, str]] = [
    (f"writing silently {EM} a consumer", "writing silently. A consumer"),
    (f"content_digest`** {EM} the content hash", "content_digest`**: the content hash"),
    (f"byte-identical hash {EM} same name", "byte-identical hash: same name"),
    (f"(`server.security_headers`) {EM} CSP", "(`server.security_headers`): CSP"),
    (f"the stored values {EM} not the masked", "the stored values, not the masked"),
    (f"the same state {EM} and PATCH", "the same state, and PATCH"),
    (f"**module globals** {EM} a function-local", "**module globals**: a function-local"),
    (f"via `extra_routes`) {EM} three GETs", "via `extra_routes`): three GETs"),
    (f"($10.00/$45.00) {EM} the last OpenAI", "($10.00/$45.00), the last OpenAI"),
    (f"rates, not lifecycle {EM} a retired", "rates, not lifecycle: a retired"),
    (f"its real $0.15/$0.60 {EM}\n", "its real $0.15/$0.60.\n"),
    (f"entered without it {EM} each confirmed", "entered without it, each confirmed"),
    (f"for exactly this reason {EM} their cache-write",
     "for exactly this reason: their cache-write"),
    (f'this vendor\'s page" {EM} right for', 'this vendor\'s page": right for'),
    (f"rows carrying none {EM}\n", "rows carrying none,\n"),
    (f"URL it was read from {EM}\n", "URL it was read from:\n"),
    (f"retrieval date and note {EM} so the check", "retrieval date and note, so the check"),
    (f"pending counts disagreed {EM} `unreviewed_models()`",
     "pending counts disagreed: `unreviewed_models()`"),
    (f"walks JSON rows {EM} and a sign-off", "walks JSON rows, and a sign-off"),
    (f"for that id at all {EM} only `gemini-3-flash-preview`",
     "for that id at all, only `gemini-3-flash-preview`"),
    (f"($1.50/$9.00/$0.15) {EM} the model", "($1.50/$9.00/$0.15), the model"),
    (f"through `MlflowClient` {EM} the fluent", "through `MlflowClient`: the fluent"),
    (f"one loop that interleaves {EM} spans orphaned",
     "one loop that interleaves: spans orphaned"),
    (f"extra is absent {EM} the failure", "extra is absent, the failure"),
    (f"family registered** {EM} `gpt-5.6-sol`", "family registered**: `gpt-5.6-sol`"),
    (f"the short-context rate {EM} so an oversized", "the short-context rate, so an oversized"),
    (f"*everything sent* {EM} uncached input, cache reads and cache writes alike {EM}",
     "*everything sent* (uncached input, cache reads and cache writes alike)"),
    (f"1.5x output {EM} multipliers", "1.5x output; multipliers"),
    (f"an unfilled gap** {EM} the two look", "an unfilled gap**: the two look"),
    (f"no longer exists {EM} the vendor states", "no longer exists. The vendor states"),
    (f"at standard rates {EM} so a tier there", "at standard rates, so a tier there"),
    (f"block untouched {EM} stated in the script", "block untouched, stated in the script"),
    (f"overlay pattern safe {EM} a consumer carrying", "overlay pattern safe: a consumer carrying"),
    (f"this data has {EM} a model published", "this data has: a model published"),
    (f"`_model_data.py` by path {EM} safe precisely", "`_model_data.py` by path, safe precisely"),
    (f"else in the package {EM} and the two", "else in the package, and the two"),
    (f"Opus 4.8 and Sonnet 4.6** {EM} both were", "Opus 4.8 and Sonnet 4.6**: both were"),
    (f"worst-cased at $21/$168 {EM}\n", "worst-cased at $21/$168,\n"),
    (f"**zero production call sites** {EM}\n", "**zero production call sites**:\n"),
    (f"it is **borrowed** {EM} used as-is", "it is **borrowed**, used as-is"),
    (f"usage and outcome {EM} every reference", "usage and outcome: every reference"),
    (f"*how the\n  loop exited* {EM} converging", "*how the\n  loop exited*: converging"),
    (f"*do* isolate {EM} so", "*do* isolate, so"),
    (f"is never called {EM} on a borrowed", "is never called: on a borrowed"),
    (f"off `_notify_turn_complete` {EM} the one", "off `_notify_turn_complete`, the one"),
    (f"already pass through {EM} rather than", "already pass through, rather than"),
    (f"is\n  path-dependent {EM} the single-shot", "is\n  path-dependent: the single-shot"),
    (f"the agentic path the\n  reverse {EM} so emitting",
     "the agentic path the\n  reverse, so emitting"),
]


def report(text: str, path: Path) -> int:
    remaining = [(i, line) for i, line in enumerate(text.splitlines(), 1) if EM in line]
    for i, line in remaining:
        print(f"{path}:{i}: {line.strip()[:100]}")
    print(f"\n{len(remaining)} line(s) still containing an em-dash")
    return 1 if remaining else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", type=Path)
    ap.add_argument("--report", action="store_true", help="list em-dash lines, change nothing")
    args = ap.parse_args()

    text = args.path.read_text()
    if args.report:
        raise SystemExit(report(text, args.path))

    applied = missed = 0
    for old, new in RULES:
        count = text.count(old)
        if count == 0:
            print(f"  no match: {old[:60]!r}")
            missed += 1
            continue
        if count > 1:
            print(f"  AMBIGUOUS ({count} matches), skipped: {old[:60]!r}", file=sys.stderr)
            missed += 1
            continue
        text = text.replace(old, new, 1)
        applied += 1

    args.path.write_text(text)
    print(f"applied {applied} rule(s), {missed} unmatched\n")
    raise SystemExit(report(text, args.path))


if __name__ == "__main__":
    main()
