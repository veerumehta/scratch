#!/usr/bin/env python3
"""Flag British spellings in what a push adds.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

The repo is written in US English (normalization, behavior, catalog, judgment). A review catches a
`normalisation` file name only if the reviewer notices, so this checks the diff that is about to
leave the machine, mechanically:

  * the added lines of every tracked text file in the pushed range (code, tests, docs, YAML),
  * the commit messages in the range.

Only what the push adds is checked: words that were already in the tree stay until someone touches
them. Lockfiles, model data and URLs are skipped.

The check is a word list, not a dictionary: `-ise` is not a suffix to ban (promise, exercise,
otherwise), so the verbs that take `-ize` in US English are listed by stem, and the other
spellings (colour, centre, licence, cancelled, ...) are listed whole. Add to `STEMS` / `FIXED`
when one slips through.

Escape hatches, for a quoted external name or a vendor string:
  * put `uk-ok` anywhere on the line (a comment is fine),
  * `JAPES_SKIP_SPELLING=1` skips the whole check (the hook honors it).

  check_us_spelling.py                       # default range: upstream, else origin/plato, dev, main
  check_us_spelling.py --range A..B          # an explicit range
  PUSH_REFS="$(cat)" check_us_spelling.py    # the four-column text git gives a pre-push hook
  check_us_spelling.py --self-test           # the word lists against known cases

Exit 0 when clean, 1 when a British spelling was added, 2 on a usage or git error.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

ZERO_SHA = "0" * 40
MARKER = "uk-ok"
#: Longest line of added text examined; a minified blob has no prose to check.
MAX_LINE_CHARS = 2000
#: Paths whose added lines carry vendor names and data, not our prose.
EXCLUDE_PATHSPECS = (
    ":(exclude)*.lock",
    ":(exclude)poetry.lock",
    ":(exclude)*package-lock.json",
    ":(exclude)*model_data.json",
    ":(exclude)*.svg",
    ":(exclude)common",
)
#: Branches a push with no upstream is compared against, in order.
BASE_CANDIDATES = ("origin/plato", "origin/dev", "origin/main")

#: Verb stems that take `-ize` in US English; matched with every `-ise` ending.
STEMS = (
    "apolog", "author", "capital", "categor", "central", "character", "critic", "custom", "digit",
    "emphas", "equal", "fertil", "final", "formal", "general", "harmon", "hypothes", "ideal",
    "immun", "industrial", "initial", "internation", "jeopard", "legitim", "local", "margin",
    "material", "maxim", "memor", "milit", "minim", "mobil", "modern", "nation", "neutral",
    "normal", "optim", "organ", "parameter", "penal", "personal", "polar", "popular", "priorit",
    "privat", "random", "ration", "real", "recogn", "revolution", "sanit", "serial", "social",
    "special", "stabil", "standard", "summar", "symbol", "sympath", "synchron", "systemat",
    "tabul", "theor", "token", "tranquil", "union", "urban", "util", "verbal", "virtual",
    "visual",
)
_ISE_ENDINGS = ("ise", "ises", "ised", "ising", "isation", "isations", "iser", "isers", "isable")

#: Whole words: British form -> US form. Plural and inflected forms are listed where they differ.
FIXED = {
    "analyse": "analyze", "analysed": "analyzed", "analysing": "analyzing",
    "paralyse": "paralyze", "catalyse": "catalyze",
    "behaviour": "behavior", "behaviours": "behaviors", "behavioural": "behavioral",
    "colour": "color", "colours": "colors", "coloured": "colored", "colouring": "coloring",
    "favour": "favor", "favours": "favors", "favoured": "favored", "favourite": "favorite",
    "honour": "honor", "honoured": "honored", "humour": "humor", "labour": "labor",
    "neighbour": "neighbor", "neighbours": "neighbors", "rumour": "rumor", "flavour": "flavor",
    "centre": "center", "centres": "centers", "centred": "centered", "fibre": "fiber",
    "litre": "liter", "metre": "meter", "theatre": "theater", "calibre": "caliber",
    "licence": "license", "licences": "licenses", "defence": "defense", "offence": "offense",
    "pretence": "pretense", "catalogue": "catalog", "catalogues": "catalogs",
    "programme": "program", "programmes": "programs", "judgement": "judgment",
    "judgements": "judgments", "acknowledgement": "acknowledgment", "ageing": "aging",
    "cancelled": "canceled", "cancelling": "canceling", "labelled": "labeled",
    "labelling": "labeling", "modelled": "modeled", "modelling": "modeling",
    "travelled": "traveled", "travelling": "traveling", "signalled": "signaled",
    "signalling": "signaling", "channelled": "channeled", "channelling": "channeling",
    "fuelled": "fueled", "levelled": "leveled", "counselled": "counseled",
    "marshalled": "marshaled", "totalled": "totaled", "tunnelled": "tunneled",
    "fulfil": "fulfill", "fulfils": "fulfills", "enrol": "enroll", "enrols": "enrolls",
    "instalment": "installment", "skilful": "skillful", "wilful": "willful",
    "learnt": "learned", "spelt": "spelled", "whilst": "while", "amongst": "among",
    "sceptic": "skeptic", "sceptical": "skeptical", "scepticism": "skepticism",
    "manoeuvre": "maneuver", "aluminium": "aluminum", "mould": "mold", "tyre": "tire",
    "practise": "practice", "grey": "gray",
}


def _us_ise(word: str) -> str:
    """The `-ize` form of an `-ise` word (normalise -> normalize)."""
    return re.sub(r"is(e|es|ed|ing|ation|ations|er|ers|able)$", r"iz\1", word)


_STEM_RE = re.compile(
    r"\b(?:%s)(?:%s)\b" % ("|".join(STEMS), "|".join(_ISE_ENDINGS)), re.IGNORECASE)
_FIXED_RE = re.compile(r"\b(?:%s)\b" % "|".join(sorted(FIXED, key=len, reverse=True)), re.IGNORECASE)
_URL_RE = re.compile(r"\S*://\S*")


def suggestion(word: str) -> str:
    """The US spelling of a flagged word, in the case it was written."""
    low = word.lower()
    us = FIXED.get(low) or _us_ise(low)
    if word.isupper():
        return us.upper()
    return us.capitalize() if word[:1].isupper() else us


def findings_in(text: str) -> list[tuple[str, str]]:
    """(british, us) pairs found in one line; empty when the line carries the escape marker."""
    if MARKER in text or len(text) > MAX_LINE_CHARS:
        return []
    text = _URL_RE.sub(" ", text)
    return [(m.group(0), suggestion(m.group(0)))
            for rx in (_STEM_RE, _FIXED_RE) for m in rx.finditer(text) if not _is_api_call(text, m)]


def _is_api_call(text: str, match: re.Match) -> bool:
    """A method call such as `task.cancelled()` names a library API, not our prose."""
    return match.start() > 0 and text[match.start() - 1] == "." and text[match.end():match.end() + 1] == "("


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def _exists(rev: str) -> bool:
    return subprocess.run(["git", "rev-parse", "--verify", "--quiet", rev],
                          capture_output=True, check=False).returncode == 0


def default_range() -> str:
    """Upstream..HEAD, else HEAD against the first of origin/plato, dev, main that exists."""
    if _exists("@{u}"):
        return "@{u}..HEAD"
    for base in BASE_CANDIDATES:
        if _exists(base):
            return f"{base}..HEAD"
    return "HEAD~1..HEAD"


def ranges_from_push_refs(refs: str) -> list[str]:
    """One range per pushed ref from the pre-push hook's `local_ref local_sha remote_ref remote_sha`."""
    ranges = []
    for line in refs.splitlines():
        parts = line.split()
        if len(parts) != 4 or parts[1] == ZERO_SHA:
            continue
        local_sha, remote_sha = parts[1], parts[3]
        if remote_sha == ZERO_SHA:
            base = next((git("merge-base", local_sha, b).strip() for b in BASE_CANDIDATES
                         if _exists(b)), "")
            ranges.append(f"{base}..{local_sha}" if base else f"{local_sha}~1..{local_sha}")
        else:
            ranges.append(f"{remote_sha}..{local_sha}")
    return ranges


def added_lines(rng: str):
    """(path, line number, text) of every line the range adds."""
    out = git("diff", "-U0", "--no-color", "--diff-filter=AMR", rng, "--", ".", *EXCLUDE_PATHSPECS)
    path, lineno = "", 0
    for raw in out.splitlines():
        if raw.startswith("+++ b/"):
            path = raw[6:]
        elif raw.startswith("@@"):
            match = re.search(r"\+(\d+)", raw)
            lineno = int(match.group(1)) if match else 0
        elif raw.startswith("+") and not raw.startswith("+++"):
            yield path, lineno, raw[1:]
            lineno += 1


def commit_messages(rng: str):
    """(short sha, message) of each commit in the range."""
    out = git("log", "--format=%h%x00%B%x01", rng)
    for chunk in out.split("\x01"):
        if "\x00" in chunk:
            sha, message = chunk.strip("\n").split("\x00", 1)
            yield sha.strip(), message


def check(ranges: list[str]) -> list[str]:
    found: list[str] = []
    for rng in ranges:
        for path, lineno, text in added_lines(rng):
            for british, us in findings_in(text):
                found.append(f"{path}:{lineno}: {british} -> {us}")
        for sha, message in commit_messages(rng):
            for lineno, text in enumerate(message.splitlines(), start=1):
                for british, us in findings_in(text):
                    found.append(f"commit {sha} message line {lineno}: {british} -> {us}")
    return sorted(set(found))


CLEAN = ("promise", "exercise", "otherwise", "premise", "surprise", "compromise", "enterprise",
         "revise", "precise", "program", "color", "behavior", "normalize", "catalog", "center",
         "license", "judgment", "canceled", "labeled", "organization", "recognized", "analyze",
         "utilize", "gray", "Normalization", "https://example.com/behaviour/colour")
FLAGGED = {
    "normalise": "normalize", "Normalised": "Normalized", "NORMALISATION": "NORMALIZATION",
    "organisation": "organization", "recognising": "recognizing", "serialise": "serialize",
    "initialises": "initializes", "behaviour": "behavior", "Colour": "Color",
    "centre": "center", "licence": "license", "catalogue": "catalog", "judgement": "judgment",
    "cancelled": "canceled", "labelling": "labeling", "analysed": "analyzed",
    "whilst": "while", "fulfil": "fulfill",
}


def self_test() -> int:
    bad = [w for w in CLEAN if findings_in(w)]
    miss = [(w, us) for w, us in FLAGGED.items() if findings_in(w) != [(w, us)]]
    marked = findings_in(f"# the vendor says behaviour  {MARKER}")
    for word in bad:
        print(f"false positive: {word} -> {findings_in(word)}")
    for word, us in miss:
        print(f"missed or wrong: {word} (want {us}) -> {findings_in(word)}")
    if marked:
        print(f"marker ignored: {marked}")
    print("self-test:", "FAILED" if (bad or miss or marked) else "ok")
    return 1 if (bad or miss or marked) else 0


def main(argv: list[str]) -> int:
    if os.environ.get("JAPES_SKIP_SPELLING") == "1":
        print("  --  skipped (JAPES_SKIP_SPELLING=1)")
        return 0
    if "--self-test" in argv:
        return self_test()
    try:
        if "--range" in argv:
            ranges = [argv[argv.index("--range") + 1]]
        else:
            ranges = ranges_from_push_refs(os.environ.get("PUSH_REFS", "")) or [default_range()]
        found = check(ranges)
    except (RuntimeError, IndexError) as exc:
        print(f"  --  not checked: {exc}")
        return 2
    if not found:
        print(f"  ok  no British spelling added ({', '.join(ranges)})")
        return 0
    print("  FAIL  British spelling added (the repo is US English):")
    for line in found[:60]:
        print(f"        {line}")
    if len(found) > 60:
        print(f"        ... and {len(found) - 60} more")
    print(f"        fix them, or mark a quoted external name with `{MARKER}` on the line")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
