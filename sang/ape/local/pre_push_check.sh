#!/usr/bin/env bash
# Run what CI runs, before pushing — so a red PR is something you chose, not something you found out.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
# Mirrors .github/workflows/tests.yml, which is the only check in this repo that a laptop can
# reproduce: CodeQL, the security scan and the code-review bot are org-level workflows with no
# local equivalent, so a green run here means "the suite and the lock are fine", not "the PR will
# be green".
#
# Four things, cheapest first:
#   1. lock consistency   — pyproject changed without re-locking fails `poetry install` in CI
#                           before a single test runs, and nothing local notices
#   2. environment drift  — CI installs from poetry.lock with a fixed extras set; a laptop that
#                           has drifted runs a different suite than CI will
#   3. the suite          — `pytest -q -rfs`, the exact invocation from tests.yml
#   4. adversarial review — a second pass over the diff for the case the author did not think
#                           of; see scripts/local/adversarial_review.sh
#
# Install as a hook (opt-in, per clone — nobody else is forced into it):
#   ln -sf ../../scripts/local/pre_push_check.sh .git/hooks/pre-push
# Remove it with `rm .git/hooks/pre-push`. Bypass once with `git push --no-verify`, or
# `JAPES_SKIP_PREPUSH=1 git push`.
#
# Run it by hand any time:
#   ./scripts/local/pre_push_check.sh              # lock + drift + suite
#   ./scripts/local/pre_push_check.sh --quick      # lock + drift only, no suite, no review
#   JAPES_SKIP_SUITE=1 git push                    # skip the suite, keep the review
#   JAPES_SKIP_REVIEW=1 git push                   # keep the suite, skip the review
#   ./scripts/local/pre_push_check.sh --ci-versions  # suite against the versions the lock pins
#
# Step 4 is `adversarial_review.sh`, which stands alone and works in any repo:
#   ./scripts/local/adversarial_review.sh
#   cd ../common && ~/src/japes/scripts/local/adversarial_review.sh common

set -uo pipefail

cd "$(git rev-parse --show-toplevel)" || exit 1

if [[ "${JAPES_SKIP_PREPUSH:-}" == "1" ]]; then
    echo "pre-push: skipped (JAPES_SKIP_PREPUSH=1)"
    exit 0
fi

QUICK=0
CI_VERSIONS=0
# A pass is recorded against the exact commit it verified. `git push` opens its connection to the
# remote *before* running this hook, so a hook that re-runs a 2-minute suite leaves that connection
# idle long enough for github to close it -- the checks pass and the push dies anyway. Running the
# script by hand and then pushing is the normal workflow, and the second run has nothing new to
# look at: same commit, same tree, same answer.
STAMP_DIR="$(git rev-parse --git-dir)/japes-prepush"
mkdir -p "$STAMP_DIR"
for arg in "$@"; do
    case "$arg" in
        --quick) QUICK=1 ;;
        --ci-versions) CI_VERSIONS=1 ;;
        -h|--help) sed -n '2,32p' "$0" | sed -E 's/^# ?//'; exit 0 ;;
    esac
done

# CI's extras, verbatim from tests.yml. mlflow/litellm/gemini/streaming/azure are deliberately out
# there, so a test needing one of them skips in CI and may well run here.
CI_EXTRAS="mcp templating finance pptx mlflow gemini plato"
# Repo the Dependabot alerts are read from (step 2c).
REPO_SLUG="JazzX-LLC/japes"
fail=0
warn=0

say() { printf '\n\033[1m%s\033[0m\n' "$1"; }

head_sha=$(git rev-parse HEAD 2>/dev/null || echo none)
dirty=$(git status --porcelain 2>/dev/null | md5 2>/dev/null || git status --porcelain | md5sum | cut -d" " -f1)
stamp="$STAMP_DIR/$head_sha-${dirty:-clean}"

if [[ -f "$stamp" && "${JAPES_FORCE_PREPUSH:-}" != "1" ]]; then
    echo "pre-push: already verified $(git rev-parse --short HEAD) with this tree ($(cat "$stamp"))."
    echo "          re-run with JAPES_FORCE_PREPUSH=1 to check again."
    exit 0
fi

# ── 1. lock consistency ───────────────────────────────────────────────────────
say "1/4  poetry.lock vs pyproject.toml"
if ! command -v poetry >/dev/null 2>&1; then
    echo "  ! poetry not on PATH — skipping (CI installs with it, so this check is worth having)"
    warn=1
elif poetry check --lock >/dev/null 2>&1; then
    echo "  ok  lock is consistent with pyproject"
else
    # `poetry check` also emits style warnings that are not lock problems; only the lock line fails.
    if poetry check --lock 2>&1 | grep -qi "lock file.*not consistent\|outdated"; then
        echo "  FAIL  lock is stale — CI's \`poetry install\` will fail before any test runs."
        echo "        fix: poetry lock   (then commit poetry.lock)"
        fail=1
    else
        echo "  ok  lock is consistent (pyproject style warnings ignored)"
    fi
fi

# ── 2. environment drift ──────────────────────────────────────────────────────
say "2/4  local environment vs what CI installs"
python - "$CI_EXTRAS" <<'PY'
import re, sys, pathlib, importlib.metadata as md

ci_extras = set(sys.argv[1].split())
lock = pathlib.Path("poetry.lock")
if not lock.exists():
    print("  ! no poetry.lock — skipping"); raise SystemExit(0)

# Parse `name = "x"` / `version = "y"` pairs. Deliberately not a TOML load: the lock is large and
# this only needs the two fields, so a dependency-free scan keeps the hook fast to start.
text = lock.read_text()
pinned = dict(re.findall(r'^name = "([^"]+)"\nversion = "([^"]+)"', text, re.M))

# The packages whose version actually changes what the suite does. A full comparison would flag
# every transitive nudge and get ignored within a week.
WATCH = ["openai", "openai-agents", "anthropic", "pydantic", "pytest", "pytest-asyncio"]
drift = []
for name in WATCH:
    want = pinned.get(name)
    try:
        have = md.version(name)
    except md.PackageNotFoundError:
        have = None
    if want and have and want != have:
        drift.append((name, want, have))

if drift:
    print("  ! installed versions differ from poetry.lock (CI uses the lock):")
    for name, want, have in drift:
        print(f"      {name:16} lock {want:12} local {have}")
    print("    a green run here is not proof CI is green. --ci-versions runs against the pins.")
else:
    print("  ok  watched packages match the lock")

# Extras CI does not install: a test needing one skips there and runs here, so a local pass can
# cover ground CI never sees.
EXTRA_PKGS = {"mlflow": "mlflow", "litellm": "litellm", "gemini": "google-genai",
              "azure": "azure-ai-documentintelligence"}


def installed(pkg: str) -> bool:
    try:
        md.version(pkg)
        return True
    except md.PackageNotFoundError:
        return False


present = [e for e, pkg in EXTRA_PKGS.items() if e not in ci_extras and installed(pkg)]
if present:
    print(f"  ! installed beyond CI's extras: {', '.join(sorted(present))}")
    print("    tests that skip in CI will run here — a local pass may cover more than CI does.")
PY

# ── 2b. workstation paths in tracked files ────────────────────────────────────
say "2b/4  absolute home paths in tracked files"
# A path like /Users/<someone>/src leaks one machine's layout into the shared tree, and where it
# guards a test it makes that test silently no-op for everyone else -- which the suite cannot
# report, because a test that never runs never fails. Tracked files only: scripts/local/ is
# gitignored and is exactly where such a path belongs.
leaks=$(git ls-files -z -- '*.py' '*.toml' '*.yaml' '*.yml' '*.cfg' \
        | xargs -0 grep -nE '"/(Users|home)/[a-z]|'"'"'/(Users|home)/[a-z]' 2>/dev/null)
if [[ -n "$leaks" ]]; then
    echo "  FAIL  workstation path in a tracked file:"
    echo "$leaks" | sed 's/^/        /'
    echo "        drive it from an environment variable, or move the file to scripts/local/"
    fail=1
else
    echo "  ok  no workstation paths in tracked files"
fi

# ── 2c. open dependency vulnerabilities ───────────────────────────────────────
say "2c/4  open Dependabot alerts on the default branch"
# Alerts are computed against the DEFAULT branch's dependency graph, not the branch being pushed,
# so nothing about a feature branch surfaces them -- they are easy to carry for weeks without
# noticing. The distinction that matters is whether upstream has shipped a fix:
#   * a patched version exists  -> actionable now, blocks the push
#   * no patched version yet    -> nothing to bump to, warn and move on
# Never fails on tooling: no gh, no auth, or no network means "not checked", not "blocked". A
# security gate that stops you working offline gets disabled, and then it checks nothing at all.
if ! command -v gh >/dev/null 2>&1; then
    echo "  --  skipped (gh not installed)"
elif ! alerts=$(gh api "repos/$REPO_SLUG/dependabot/alerts" --paginate \
        -q '.[] | select(.state=="open") | [.security_advisory.severity, .dependency.package.name, (.security_vulnerability.first_patched_version.identifier // "none"), .security_advisory.ghsa_id] | @tsv' 2>/dev/null); then
    echo "  --  skipped (gh cannot reach the API -- offline, or not authenticated)"
else
    actionable=$(printf '%s\n' "$alerts" | awk -F'\t' 'NF && $3 != "none"')
    unpatched=$(printf '%s\n' "$alerts" | awk -F'\t' 'NF && $3 == "none"')
    if [[ -n "$actionable" ]]; then
        echo "  FAIL  open alert with a fix available:"
        printf '%s\n' "$actionable" | awk -F'\t' '{printf "        %-8s %-24s -> %s  (%s)\n", $1, $2, $3, $4}'
        echo "        bump the floor in pyproject.toml and relock, or dismiss the alert with a reason"
        fail=1
    fi
    if [[ -n "$unpatched" ]]; then
        echo "  warn  open alert with no fixed version upstream (nothing to bump to):"
        printf '%s\n' "$unpatched" | awk -F'\t' '{printf "        %-8s %-24s  (%s)\n", $1, $2, $4}'
        echo "        confirm the vulnerable code path is unreachable from japes, and record why"
        warn=1
    fi
    [[ -z "$actionable$unpatched" ]] && echo "  ok  no open Dependabot alerts"
fi

# ── 3. the suite ──────────────────────────────────────────────────────────────
# `JAPES_SKIP_SUITE=1` keeps the review, which `--quick` does not: the review is the step that
# catches what a green suite does not, and the suite is the slow one. Symmetric with the
# `JAPES_SKIP_REVIEW=1` that already existed for the other direction.
if [[ "$QUICK" == "1" || "${JAPES_SKIP_SUITE:-}" == "1" ]]; then
    if [[ "$QUICK" == "1" ]]; then
        say "3/4  suite skipped (--quick)"
    else
        say "3/4  suite skipped (JAPES_SKIP_SUITE=1) -- the review below still runs"
    fi
else
    if [[ "$CI_VERSIONS" == "1" ]]; then
        say "3/4  pytest -q -rfs  (against poetry.lock's pins)"
        SHIM="${TMPDIR:-/tmp}/japes-ci-shim"
        # Shadow only the packages whose pins differ, on PYTHONPATH — a venv rebuild takes minutes
        # and this takes seconds, and neither the project venv nor any sibling repo is touched.
        rm -rf "$SHIM"
        pins=$(python - <<'PY'
import re, pathlib, importlib.metadata as md
text = pathlib.Path("poetry.lock").read_text()
pinned = dict(re.findall(r'^name = "([^"]+)"\nversion = "([^"]+)"', text, re.M))
out = []
for name in ("openai", "openai-agents"):
    want = pinned.get(name)
    try:
        have = md.version(name)
    except md.PackageNotFoundError:
        have = None
    if want and have and want != have:
        out.append(f"{name}=={want}")
print(" ".join(out))
PY
)
        if [[ -n "$pins" ]]; then
            echo "  pinning: $pins"
            python -m pip install -q --target "$SHIM" --no-deps $pins || { echo "  FAIL  could not install pins"; exit 1; }
            PYTHONPATH="$SHIM" python -m pytest -q -rfs || fail=1
            rm -rf "$SHIM"
        else
            echo "  local already matches the lock; running normally"
            python -m pytest -q -rfs || fail=1
        fi
    else
        say "3/4  pytest -q -rfs"
        python -m pytest -q -rfs || fail=1
    fi
fi

# ── 4. adversarial review of the outgoing diff ────────────────────────────────
# Lives in its own script: it is the only step here that is not japes-specific -- the others read
# poetry.lock, a fixed CI extras set and a hardcoded Dependabot slug, while this one just reads a
# diff -- so a sibling repo can run it directly:
#
#   cd ../common && ~/src/japes/scripts/local/adversarial_review.sh common
if [[ "$QUICK" == "1" || "${JAPES_SKIP_REVIEW:-}" == "1" ]]; then
    say "4/4  review skipped"
else
    # Repo-relative, not `dirname $0`: the hook is installed as a symlink into .git/hooks, and
    # BASH_SOURCE holds the *symlink* path, so dirname gave .git/hooks and the review never ran.
    # This script already cd'd to the toplevel on line 1, so the path below is well defined.
    if ! "$(git rev-parse --show-toplevel)/scripts/local/adversarial_review.sh" japes; then
        fail=1
    fi
fi

echo
if [[ "$fail" == "1" ]]; then
    echo "pre-push: FAILED — push blocked. Override with: git push --no-verify"
    exit 1
fi
# Record the pass against this exact commit+tree, and drop stamps for anything else: a stamp for a
# commit that has been amended away is a claim about a tree nobody can check.
# Stamped only by a run that skipped nothing: the stamp is a claim that this commit+tree passed
# the gate, and a run with the suite or the review turned off did not.
if [[ "$QUICK" != "1" && "${JAPES_SKIP_SUITE:-}" != "1" && "${JAPES_SKIP_REVIEW:-}" != "1" ]]; then
    find "$STAMP_DIR" -type f ! -name "$(basename "$stamp")" -delete 2>/dev/null || :
    date -u "+%Y-%m-%dT%H:%M:%SZ" > "$stamp"
fi
# Names what actually ran. The fixed list said "suite + review" whichever of them had been
# skipped, which is a green summary claiming a check nobody performed.
ran="lock + paths + deps"
[[ "$QUICK" == "1" || "${JAPES_SKIP_SUITE:-}" == "1" ]] || ran="$ran + suite"
[[ "$QUICK" == "1" || "${JAPES_SKIP_REVIEW:-}" == "1" ]] || ran="$ran + review"
if [[ "$warn" == "1" ]]; then
    echo "pre-push: ok, with warnings above (see 2c) [$ran]. CodeQL and the security scan still run on the PR."
else
    echo "pre-push: ok ($ran). CodeQL and the security scan still run on the PR."
fi
exit 0
