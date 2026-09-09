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

# `.$$` on every working file: two reviews at once -- a push while a loop round is running, or
# two repos pushed together -- otherwise share these paths and read each other's diff.
run="${TMPDIR:-/tmp}/$REPO-push-review.$$"
# Swept on the way out: the findings live in the transcript below, so the diff, the prompt and the
# per-slice replies are scratch. Without this the pid that stops them colliding also stops them
# ever being reused, so they pile up one set per push.
# The state records what this run *saw*, not what it approved, so a BLOCK still narrows the next
# round -- the findings are carried forward with it. Set later, once `$transcript` exists; both
# handlers run on the same EXIT.
save_state() {
    # A round that reached a verdict, not one that merely started. `-s` was the first version and
    # it is satisfied by the five-line header, so an interrupted run left a baseline naming a
    # transcript with no findings -- and the next round then diffed nothing against it and skipped
    # itself with "nothing changed since the last review". A killed round must cost a re-run, not
    # a silently skipped one.
    [[ -n "${transcript:-}" ]] && grep -q '^VERDICT:' "$transcript" 2>/dev/null || return 0
    printf '%s\t%s\t%s\n' "$upstream" "$(git rev-parse HEAD)" "$transcript" > "$state_file"
}
trap 'rm -rf "$run".* 2>/dev/null || :; save_state' EXIT

# What this loop already reviewed, so a round costs the change rather than the branch. The state
# is the HEAD it last saw against this upstream; the diff below is then `<that>..HEAD`, which is a
# two-tree diff and so survives the `--amend` every round of this loop performs.
#
# The full range still gets reviewed: `pre_push_check` reviews `@{upstream}...HEAD` with no state
# to narrow it, and `REVIEW_FULL=1` forces it here. That matters, because a defect in code this
# round did not touch cannot be found by an incremental pass -- the previous findings are carried
# in below so it can at least tell what its own last pass concluded.
state_dir="$(git rev-parse --show-toplevel)/scripts/local/.reviews"
mkdir -p "$state_dir"
state_file="$state_dir/.state"
prior_head=""
prior_transcript=""
if [[ -z "${REVIEW_FULL:-}" ]]; then
    if [[ -r "$state_file" ]]; then
        # `upstream<TAB>head<TAB>transcript`, so a different range does not inherit the wrong
        # state.
        IFS=$'\t' read -r saved_upstream saved_head saved_transcript < "$state_file" || :
    else
        # No state yet, but the transcripts have been kept all along: the newest one records the
        # commit it reviewed and the range it used, so the first run after this feature starts
        # narrow instead of paying one more full pass to bootstrap itself.
        # Newest transcript that reached a verdict, for the same reason `save_state` checks:
        # an interrupted round leaves a header-only file, and taking that as the baseline would
        # skip the round it was supposed to seed.
        saved_transcript="$(grep -l '^VERDICT:' $(ls -t "$state_dir"/*.md 2>/dev/null) \
                            2>/dev/null | head -1)"
        if [[ -r "${saved_transcript:-}" ]]; then
            header="$(sed -n 's/^- range: \(.*\) (\([0-9a-f][0-9a-f]*\))$/\1\t\2/p' \
                      "$saved_transcript" | head -1)"
            saved_upstream="${header%%$'\t'*}"
            saved_head="${header##*$'\t'}"
            # Only the plain `<upstream>...HEAD` form: a sliced or `since the last review` label
            # does not name a base this can diff from.
            [[ "$saved_upstream" == *"...HEAD" ]] && saved_upstream="${saved_upstream%...HEAD}" \
                || saved_upstream=""
        fi
    fi
    if [[ -n "${saved_head:-}" && "${saved_upstream:-}" == "$upstream" ]] \
       && git cat-file -e "$saved_head^{commit}" 2>/dev/null; then
        prior_head="$saved_head"
        [[ -r "${saved_transcript:-}" ]] && prior_transcript="$saved_transcript"
    fi
fi

diff_file="$run.diff"
if [[ -n "$prior_head" ]]; then
    base="$prior_head"
    range_label="$(git rev-parse --short "$prior_head")..HEAD (since the last review)"
    diff_range="$prior_head HEAD"
    git diff $diff_range > "$diff_file" 2>/dev/null || : > "$diff_file"
    if [[ ! -s "$diff_file" ]]; then
        echo "  ok  nothing changed since the last review ($(basename "${prior_transcript:-none}"))"
        exit 0
    fi
else
    base="$upstream..."
    range_label="$upstream...HEAD"
    diff_range="$upstream...HEAD"
    git diff $diff_range > "$diff_file" 2>/dev/null || : > "$diff_file"
fi
lines=$(wc -l < "$diff_file" | tr -d ' ')

if [[ "$lines" -eq 0 ]]; then
    echo "  ok  nothing to review"
    exit 0
fi
review_out="$run.out"

# A transcript per run, so findings survive the push that produced them and can be read back
# later ("the hook found something") without re-running the review. Kept, not overwritten: two
# pushes in a row would otherwise leave only the second, and the first is the one that blocked.
# `.last-review.md` points at the newest for the common case.
review_dir="$(git rev-parse --show-toplevel)/scripts/local/.reviews"
mkdir -p "$review_dir"
transcript="$review_dir/$(date -u '+%Y%m%dT%H%M%SZ')-$$.md"
: > "$transcript"
ln -sf "$transcript" "$(git rev-parse --show-toplevel)/scripts/local/.last-review.md"

# Bounded, so a long session does not accumulate them without limit.
ls -t "$review_dir"/*.md 2>/dev/null | tail -n +"${REVIEW_KEEP:-30}" | xargs rm -f 2>/dev/null || :
{
    echo "# adversarial review -- $REPO"
    echo
    echo "- when: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    echo "- range: $range_label ($(git rev-parse --short HEAD))"
    echo "- diff: $lines lines"
    echo
} >> "$transcript"

# Read-only by construction: the diff arrives on stdin and edit/write tools are denied, so the
# reviewer cannot alter the tree it is judging.
prompt_file="$run.prompt"
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

Then rate every finding, on its own line, as `IMPORTANCE: high|medium|low -- <blast radius>`:

  high    silent wrong data, a credential or identity leak, or a failure a caller cannot see. Fix
          before this lands.
  medium  reachable, but it fails loudly or the caller can work around it. Fix or file, the
          author's call.
  low     no reachable trigger in any shipped configuration, or the cost of hitting it is one
          confusing log line. A `TODO` in the code is a complete response to these.

The blast radius is what you actually checked, not an adjective: name the call sites you
enumerated, the configurations that can reach the code, and whether anything outside this repo
depends on it. "Small blast radius" with nothing behind it is worse than no rating, because the
author will act on it. If you could not establish who reaches the code, say `IMPORTANCE: unknown`
and say what you could not determine -- do not guess low.

A `TODO(...)` already sitting on the code is a claim about blast radius, and it is checkable like
any other. Check it, then act on the result:

  * the claim holds -- say so in one line under a `CHECKED:` heading and do NOT raise it as a
    finding. The author has weighed it; repeating it costs a round and changes nothing.
  * the claim is wrong, or the code is worse than the `TODO` admits -- raise it, rate it, and say
    which part of the deferral does not hold. A `TODO` is not cover for a `high`.

A test carrying a `skip` marker whose reason names a `TODO` is parked deliberately. Do not raise
findings about it, and do not count it as missing coverage: say `PARKED: <test> (<todo>)` once and
move on. If you believe a parked test hides a defect in *shipped* code, raise that defect on the
code, not on the test.

Test-only findings -- a harness that could be more faithful, an assertion that could be tighter,
duplication between test files -- are `low` unless you can name the shipped-code defect they would
have caught. For those, a `TODO` plus a `skip` is a complete response and the expected one; say so
in the finding rather than asking for the test to be rewritten. Never propose deleting or weakening
a test that currently catches something: name what it catches instead.

The last line of your reply must be exactly `VERDICT: BLOCK` if you reported one or more [DEFECT],
or `VERDICT: PASS` otherwise -- [SYMMETRY] and [NOTE] findings never block, however strongly you
hold them. They are for the author to weigh, not a gate.
PROMPT

# What the last round concluded, appended to the prompt so this one verifies instead of
# re-deriving. Without it an incremental diff is strictly less information than a full one: the
# reviewer would see this round's edits with no idea which finding they answer.
if [[ -n "$prior_transcript" ]]; then
    {
        echo
        echo "── the previous round on this branch ──────────────────────────────────────────────"
        echo
        echo "The diff you were given is ONLY what changed since that round. These were its"
        echo "findings, verbatim:"
        echo
        sed -n '6,'"${REVIEW_PRIOR_LINES:-120}"'p' "$prior_transcript"
        echo
        echo "Do two things, in this order:"
        echo
        echo "1. For each finding above, one line: \`WAS: <file:line or its first few words> --"
        echo "   FIXED | STILL OPEN | REGRESSED\`, and for anything but FIXED say in a clause what"
        echo "   still holds. Judge it against the tree, not against the diff -- a finding can be"
        echo "   fixed by a change this diff does not contain. Do not re-argue a finding the"
        echo "   author declined with a \`TODO\` whose claim checks out; that is CHECKED, not open."
        echo "2. Then review the diff for defects it introduces, under the rules above. A finding"
        echo "   you already reported and marked STILL OPEN is not reported twice -- the line from"
        echo "   step 1 is the whole report for it."
        echo
        echo "You are not being asked to re-review the branch. Code this diff does not touch was"
        echo "covered by the round above and is covered again in full before the push."
    } >> "$prompt_file"
fi

# One pass over one diff. Echoes the findings indented; returns 1 for BLOCK, 2 for no verdict.
review_one() {
    local slice_diff="$1" label="$2" out
    out="${review_out}.$(echo "$label" | tr -c 'A-Za-z0-9._-' '_')"
    claude -p --disallowed-tools "Edit,Write,NotebookEdit" -- "$(cat "$prompt_file")" \
        < "$slice_diff" > "$out" 2>&1
    sed 's/^/    /' "$out"
    { echo; echo "## $label"; echo; cat "$out"; } >> "$transcript"
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
        1) echo; echo "  FAIL  review found defects (above)."
           echo "        transcript: $transcript"; exit 1 ;;
        0) echo "  ok  no defects reported"; exit 0 ;;
        *) echo "  ! review returned no verdict — treating as inconclusive, not blocking"; exit 0 ;;
    esac
fi

# ── sliced ────────────────────────────────────────────────────────────────────
# Packed by file, greedily, so a slice is a set of whole files: a diff cut mid-hunk asks the
# reviewer to judge code it cannot see. A single file larger than the budget gets its own slice
# and is sent whole -- reviewing it slightly over the line beats not reviewing it.
echo "  diff is $lines lines — reviewing in slices against $upstream"

slice_dir="$run.slices"
rm -rf "$slice_dir"; mkdir -p "$slice_dir"

slice=1
slice_lines=0
: > "$slice_dir/1.diff"
while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    file_diff="$slice_dir/.one.diff"
    git diff $diff_range -- "$path" > "$file_diff" 2>/dev/null || continue
    n=$(wc -l < "$file_diff" | tr -d ' ')
    [[ "$n" -eq 0 ]] && continue
    if [[ "$slice_lines" -gt 0 && $((slice_lines + n)) -gt "$MAX_LINES" ]]; then
        slice=$((slice + 1)); slice_lines=0; : > "$slice_dir/$slice.diff"
    fi
    cat "$file_diff" >> "$slice_dir/$slice.diff"
    slice_lines=$((slice_lines + n))
done < <(git diff --name-only $diff_range)
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
    echo "        transcript: $transcript"
    exit 1
fi
if [[ "$inconclusive" -gt 0 ]]; then
    echo "  ! $inconclusive of $reviewed slices returned no verdict — inconclusive, not blocking"
    exit 0
fi
echo "  ok  no defects reported across $reviewed slice(s)"
exit 0
