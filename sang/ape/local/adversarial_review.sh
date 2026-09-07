#!/usr/bin/env bash
# A second pass over the outgoing diff, looking for the case the author did not think of.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
# The check the others structurally cannot make. The suite proves the cases I thought of; ruff
# proves the mechanical rules; neither reads the code looking for the case I did not think of.
# Every defect the PR reviewer has found here was of that kind -- an excluded input
# (`range(1, 24)` where 0 was the bug), a comment claiming a guarantee the code did not enforce, a
# handler enumerating three exception types and missing the fourth. Same model as the author, but a
# different job: reviewing a diff with no memory of writing it is not the same task as re-reading
# your own work, and that framing is where the findings come from.
#
# Its own script rather than a step inside `pre_push_check.sh`, because it is the one part of that
# check that is not japes-specific: the other steps read poetry.lock, a fixed CI extras set and a
# hardcoded Dependabot slug, while this one reads a diff. Every git command here is cwd-relative,
# so it reviews whatever checkout it is run from.
#
#   ./scripts/local/adversarial_review.sh                 # this repo, against its upstream
#   cd ../common && ~/src/japes/scripts/local/adversarial_review.sh common
#
# The name is optional -- it defaults to the checkout's directory -- and only keeps two repos' temp
# files apart and says which one is being reviewed.
#
# Exits 1 when the review reports a defect, 0 otherwise (including when it cannot run: a missing
# `claude`, an empty diff, or a diff too large to review in one pass are not failures).

set -uo pipefail

cd "$(git rev-parse --show-toplevel)" || exit 1

REPO="${1:-$(basename "$(git rev-parse --show-toplevel)")}"
# A diff this size does not fit one useful pass, and a review that skims is worse than none.
MAX_LINES="${REVIEW_MAX_LINES:-4000}"

say() { printf '\n\033[1m%s\033[0m\n' "$1"; }

say "adversarial review of what is being pushed ($REPO)"

if ! command -v claude >/dev/null 2>&1; then
    echo "  ! claude not on PATH — skipping the review"
    exit 0
fi

# `REVIEW_UPSTREAM` to review an arbitrary range -- a already-pushed commit, or a slice plan you
# want to see -- without moving the branch.
upstream="${REVIEW_UPSTREAM:-$(git rev-parse --abbrev-ref '@{upstream}' 2>/dev/null || echo "origin/$(git rev-parse --abbrev-ref HEAD)")}"
if ! git rev-parse --verify -q "$upstream" >/dev/null; then
    echo "  ! no upstream ($upstream) — reviewing the last commit instead"
    upstream="HEAD~1"
fi

diff_file="${TMPDIR:-/tmp}/$REPO-push-review.diff"
git diff "$upstream...HEAD" > "$diff_file" 2>/dev/null || : > "$diff_file"
lines=$(wc -l < "$diff_file" | tr -d ' ')

if [[ "$lines" -eq 0 ]]; then
    echo "  ok  nothing to review"
    exit 0
fi
review_out="${TMPDIR:-/tmp}/$REPO-push-review.out"

# Read-only by construction: the diff arrives on stdin and edit/write tools are denied, so the
# reviewer cannot alter the tree it is judging.
prompt_file="${TMPDIR:-/tmp}/$REPO-push-review.prompt"
cat > "$prompt_file" <<'PROMPT'
You are reviewing a diff that is about to be pushed. Report only defects you can point at in this
diff. No praise, no summary, no style opinions, no suggestions to add documentation.

Weight these highest, because they are what has actually shipped broken here before:
- an input the code excludes: empty, zero, one, None, and the boundary of every range or loop
  (a test sweeping `range(1, N)` when 0 is a valid input is the classic instance)
- a comment, docstring or name that claims a guarantee the code does not enforce
- an exception handler that enumerates types and misses one the block can raise, or that sits
  above the line that actually raises
- an error swallowed so that a caller's mistake is returned as an ordinary result
- a hardcoded absolute path, one machine's layout, or a consumer/repo name in shipped code
- a declared branch condition with no predicate behind it
- a fix applied in one place where a sibling has the same defect
- a knob, guard or capability added to one member of a family and not the others: the clients
  wrapping a service, the fabric stores, the routers an app mounts, the providers behind one
  interface. Check the whole family, not just the nearest sibling -- if three share a shape and
  one got the change, the other two are latent until shown otherwise

Tag every finding with exactly one of:

  [DEFECT]  wrong behaviour, and you can name the concrete input or state that produces it. The
            trigger must be something a caller can actually reach, not a hypothetical shape.
  [SYMMETRY] this diff solves something in a place-specific way when the same shape already
            exists elsewhere in THIS repo, and the consistent version is no more code: logic
            duplicated in a caller that belongs in the layer below, a rule stated in a test that
            the library cannot apply, a constant repeated instead of shared, a fix that reads as
            local when the layer could own it.
  [NOTE]    everything else: a comment that could be more precise, a claim that is true but
            narrower than stated, a naming or structure preference, a test that could assert more.

A [SYMMETRY] finding must name the specific existing file or symbol it should line up with, and
the generalization must be at least as small as what the diff does. Anything else is speculation:
do not raise it because another repository does it differently, because a future caller might want
it, or because an abstraction would be tidier. A capability nobody has asked for twice is not a
symmetry finding. Report at most two, and say nothing if the diff's shape is already the
consistent one.

Report at most three [NOTE]s and put them after the defects and symmetry findings. Do not raise a
[NOTE] whose only substance is that prose could be worded better -- say nothing instead.

For each finding give: file:line, one sentence on the defect, and the concrete input or state that
triggers it. If you are not confident it is a real defect, tag it [NOTE] or leave it out.

The last line of your reply must be exactly `VERDICT: BLOCK` if you reported one or more [DEFECT],
or `VERDICT: PASS` otherwise -- [SYMMETRY] and [NOTE] findings never block, however strongly you
hold them. They are for the author to weigh, not a gate.
PROMPT

# One pass over one diff. Echoes the findings indented; returns 1 for BLOCK, 2 for no verdict.
review_one() {
    local slice_diff="$1" label="$2" out
    out="${review_out}.$(echo "$label" | tr -c 'A-Za-z0-9._-' '_')"
    claude -p --disallowed-tools "Edit,Write,NotebookEdit" -- "$(cat "$prompt_file")" \
        < "$slice_diff" > "$out" 2>&1
    sed 's/^/    /' "$out"
    grep -q "^VERDICT: BLOCK" "$out" && return 1
    grep -q "^VERDICT: PASS" "$out" && return 0
    return 2
}

# A diff that fits goes in one pass. One that does not is reviewed in slices rather than skipped:
# skipping exits 0, so the gate passed silently on exactly the pushes big enough to need it -- and
# a workflow that squashes several rounds into one commit produces those every time.
if [[ "$lines" -le "$MAX_LINES" ]]; then
    echo "  reviewing $lines lines against $upstream ..."
    review_one "$diff_file" whole
    case $? in
        1) echo; echo "  FAIL  review found defects (above)."; exit 1 ;;
        0) echo "  ok  no defects reported"; exit 0 ;;
        *) echo "  ! review returned no verdict — treating as inconclusive, not blocking"; exit 0 ;;
    esac
fi

# ── sliced ────────────────────────────────────────────────────────────────────
# Packed by file, greedily, so a slice is a set of whole files: a diff cut mid-hunk asks the
# reviewer to judge code it cannot see. A single file larger than the budget gets its own slice
# and is sent whole -- reviewing it slightly over the line beats not reviewing it.
echo "  diff is $lines lines — reviewing in slices against $upstream"

slice_dir="${TMPDIR:-/tmp}/$REPO-push-review-slices"
rm -rf "$slice_dir"; mkdir -p "$slice_dir"

slice=1
slice_lines=0
: > "$slice_dir/1.diff"
while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    file_diff="$slice_dir/.one.diff"
    git diff "$upstream...HEAD" -- "$path" > "$file_diff" 2>/dev/null || continue
    n=$(wc -l < "$file_diff" | tr -d ' ')
    [[ "$n" -eq 0 ]] && continue
    if [[ "$slice_lines" -gt 0 && $((slice_lines + n)) -gt "$MAX_LINES" ]]; then
        slice=$((slice + 1)); slice_lines=0; : > "$slice_dir/$slice.diff"
    fi
    cat "$file_diff" >> "$slice_dir/$slice.diff"
    slice_lines=$((slice_lines + n))
done < <(git diff --name-only "$upstream...HEAD")
rm -f "$slice_dir/.one.diff"

total=$slice
# Bounded, so one enormous push cannot spawn an unbounded number of reviews. Slices beyond the cap
# are named rather than passed over in silence.
MAX_SLICES="${REVIEW_MAX_SLICES:-8}"
reviewed=0
blocked=0
inconclusive=0
for i in $(seq 1 "$total"); do
    if [[ "$i" -gt "$MAX_SLICES" ]]; then
        echo
        echo "  ! $((total - MAX_SLICES)) of $total slices not reviewed (cap $MAX_SLICES). Files:"
        for j in $(seq "$((MAX_SLICES + 1))" "$total"); do
            grep '^+++ b/' "$slice_dir/$j.diff" | sed 's|^+++ b/|        |'
        done
        break
    fi
    n=$(wc -l < "$slice_dir/$i.diff" | tr -d ' ')
    say "slice $i/$total ($n lines)"
    grep '^+++ b/' "$slice_dir/$i.diff" | sed 's|^+++ b/|    · |'
    review_one "$slice_dir/$i.diff" "slice$i"
    case $? in
        1) blocked=$((blocked + 1)) ;;
        2) inconclusive=$((inconclusive + 1)) ;;
    esac
    reviewed=$((reviewed + 1))
done

echo
if [[ "$blocked" -gt 0 ]]; then
    echo "  FAIL  $blocked of $reviewed reviewed slices found defects (above)."
    exit 1
fi
if [[ "$inconclusive" -gt 0 ]]; then
    echo "  ! $inconclusive of $reviewed slices returned no verdict — inconclusive, not blocking"
    exit 0
fi
echo "  ok  no defects reported across $reviewed slice(s)"
exit 0
