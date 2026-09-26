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
# reviewer CLI, an empty diff, or an inconclusive review are not failures).
#
# `REVIEW_ENGINE` picks the reviewer: `claude` (the default) or `codex`. Both read the same prompt
# and diff on stdin, run read-only against the checkout, and must end with the same VERDICT line.

set -uo pipefail

cd "$(git rev-parse --show-toplevel)" || exit 1

REPO="${1:-$(basename "$(git rev-parse --show-toplevel)")}"
# A diff this size does not fit one useful pass, and a review that skims is worse than none.
MAX_LINES="${REVIEW_MAX_LINES:-4000}"
REVIEW_ENGINE="${REVIEW_ENGINE:-claude}"
# Claude is pinned to the top tier at high effort: see the invocation in `review_one` for why this
# is not left to the CLI's own config. A full model name, not an alias, for the same reason: an
# alias moves when a new model ships. Codex takes its own configured default unless overridden.
case "$REVIEW_ENGINE" in
    claude) default_model="claude-opus-5-5"; default_effort="high" ;;
    codex)  default_model=""; default_effort="" ;;
    *) echo "  ! REVIEW_ENGINE must be claude or codex, not '$REVIEW_ENGINE'"; exit 2 ;;
esac
REVIEW_MODEL="${REVIEW_MODEL:-$default_model}"
REVIEW_EFFORT="${REVIEW_EFFORT:-$default_effort}"

say() { printf '\n\033[1m%s\033[0m\n' "$1"; }

say "adversarial review of what is being pushed ($REPO, $REVIEW_ENGINE ${REVIEW_MODEL:-default model})"

if ! command -v "$REVIEW_ENGINE" >/dev/null 2>&1; then
    echo "  ! $REVIEW_ENGINE not on PATH — skipping the review"
    exit 0
fi

# `REVIEW_UPSTREAM` to review an arbitrary range -- a already-pushed commit, or a slice plan you
# want to see -- without moving the branch.
upstream="${REVIEW_UPSTREAM:-$(git rev-parse --abbrev-ref '@{upstream}' 2>/dev/null || echo "origin/$(git rev-parse --abbrev-ref HEAD)")}"
if ! git rev-parse --verify -q "$upstream" >/dev/null; then
    echo "  ! no upstream ($upstream) — reviewing the last commit instead"
    upstream="HEAD~1"
fi

# Resolved once, here. Everything downstream -- the diff, the transcript header, the baseline the
# next round reads -- has to name the same commit, and `HEAD` does not stand still: this loop
# commits and amends while a review is running, so a later `git rev-parse HEAD` answers about a
# tree this pass never saw.
reviewed_head="$(git rev-parse HEAD)"

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
    # The commit that was *reviewed*, not `HEAD` as it stands at exit. A fix committed or amended
    # while the pass was still running moves HEAD, and a baseline naming a commit these findings
    # were never about is worse than no baseline: the next round then diffs from a tree nobody
    # reviewed, and silently calls the result "since the last review".
    printf '%s\t%s\t%s\n' "$upstream" "$reviewed_head" "$transcript" > "$state_file"
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
    # What the baseline has to support is `git diff <saved_head> <reviewed_head>`, which is a
    # two-tree diff: it reads both trees and does not care how their histories relate. The
    # ancestry between them is therefore the wrong question, and asking it was the bug -- this
    # loop amends every round, an amended commit is NOT an ancestor of its replacement, and the
    # same-tree fallback cannot rescue it because the round's whole purpose is to change the
    # tree. So every round fell through to the full range, and the incremental mode this state
    # exists to drive had never once run.
    #
    # What is still worth checking is that the baseline belongs to the work being reviewed rather
    # than to some other branch, so that the two trees are two versions of one change and not two
    # unrelated ones. That is an ancestry test on the *upstream*, not on the head: whatever
    # `saved_head` is now, it grew from the same base.
    #
    # An identical tree needs no special case: the diff below comes out empty and the run already
    # reports "nothing changed since the last review" and exits.
    if [[ -n "${saved_head:-}" && "${saved_upstream:-}" == "$upstream" ]] \
       && git cat-file -e "$saved_head^{commit}" 2>/dev/null; then
        if git merge-base --is-ancestor "$upstream" "$saved_head" 2>/dev/null; then
            prior_head="$saved_head"
            [[ -r "${saved_transcript:-}" ]] && prior_transcript="$saved_transcript"
        else
            echo "  --  state names $(git rev-parse --short "$saved_head"), which did not grow" \
                 "from $upstream; reviewing the full range"
        fi
    fi
fi

diff_file="$run.diff"
if [[ -n "$prior_head" ]]; then
    git diff "$prior_head" "$reviewed_head" > "$diff_file" 2>/dev/null || : > "$diff_file"
    if [[ ! -s "$diff_file" ]]; then
        echo "  ok  nothing changed since the last review ($(basename "${prior_transcript:-none}"))"
        exit 0
    fi
    # The upstream check above says the baseline grew from the same base; it cannot say it is a
    # version of *this* work, because `.state` is keyed by the upstream's label and two branches
    # can share one. The trees answer it: a real prior round is nearer to HEAD than the upstream
    # is, so a "delta" bigger than the whole branch is two unrelated changes held against each
    # other. Prefer the full range, which is at least true.
    narrow_lines=$(wc -l < "$diff_file" | tr -d ' ')
    full_lines=$(git diff "$upstream...$reviewed_head" 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$narrow_lines" -gt "$full_lines" ]]; then
        echo "  --  state names $(git rev-parse --short "$prior_head"), whose delta against HEAD" \
             "($narrow_lines lines) is larger than the whole branch ($full_lines); it is not a"
        echo "      prior round of this work — reviewing the full range"
        prior_head=""
        prior_transcript=""
    fi
fi
if [[ -n "$prior_head" ]]; then
    base="$prior_head"
    range_label="$(git rev-parse --short "$prior_head")..HEAD (since the last review)"
    diff_range="$prior_head $reviewed_head"
else
    base="$upstream..."
    range_label="$upstream...HEAD"
    diff_range="$upstream...$reviewed_head"
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

# Bounded, so a long session does not accumulate them without limit. `+N` starts printing AT the
# Nth, so the bare `REVIEW_KEEP` deleted the newest-but-29 and kept one fewer than it advertised --
# which bites exactly when a long loop makes the older rounds worth reading.
ls -t "$review_dir"/*.md 2>/dev/null | tail -n +"$(( ${REVIEW_KEEP:-30} + 1 ))" \
    | xargs rm -f 2>/dev/null || :
{
    echo "# adversarial review -- $REPO"
    echo
    echo "- when: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    echo "- range: $range_label ($(git rev-parse --short "$reviewed_head"))"
    echo "- diff: $lines lines"
    echo
} >> "$transcript"

# The diff arrives with the instructions on stdin. The reviewer runs read-only (see
# `run_reviewer`) so it can inspect the checkout without altering the tree it is judging.
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

Start every finding on its own line, in exactly this shape and nothing else -- no `#` heading, no
bold, no bullet, nothing at all before the tag:

  [DEFECT] path/to/file.py:120 :: short-slug -- one sentence on the defect

`path:line` is where it lives. `slug` is two to four hyphenated lowercase words naming the defect
itself rather than the file -- `fico-floor-not-encoded`, `naive-as-of-not-coerced`,
`orphaned-wrap-fragments`. Give the same defect the same slug in every round even after its line
moves, and never reuse one slug for two defects in a file: `path :: slug` is the key a later round
matches on to tell "still open" from "new", and it is how a finding can be retired without being
re-argued. Then, on the lines after it, the concrete input or state that triggers it. If you are
not confident it is a real defect, tag it [NOTE] or leave it out.

Do not use `##` headings anywhere in your reply. This reply is concatenated with others into one
transcript and `##` is what separates them.

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

  * the claim holds -- say so on one line beginning `CHECKED:` (a plain line, not a heading) and
    do NOT raise it as a finding. The author has weighed it; repeating it costs a round and
    changes nothing.
  * the claim is wrong, or the code is worse than the `TODO` admits -- raise it, rate it, and say
    which part of the deferral does not hold. A `TODO` is not cover for a `high`.

Some findings have already been reported and accepted as they stand -- an extraction artifact in a
vendored corpus nobody will re-run, a shape the author has decided to live with. They arrive below
under `ACCEPTED FINDINGS`, one `path :: slug` per line. Those are settled, and a settled finding is
not a defect this diff introduces. Do not report one again, do not re-argue it, and do not restate
it as a [NOTE]: write `ACCEPTED: <path :: slug>` once, and nothing else about it. The one exception
is the same one that applies to a `TODO`: if the code around it has changed so that it is now worse
than its key describes, raise that as a new finding and say which part of the acceptance stopped
holding.

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

# Findings the author has retired without fixing them. `TODO(...)` on the code and a `skip` marker
# on a test are the only two closures the prompt above offers, and both are code constructs: a row
# in a pack YAML has nowhere to put either, so a corpus finding the author declines can only be
# reported again next round, and again after that. This file is the channel those findings lack --
# one `path :: slug` per line, `#` comments and blank lines ignored.
accepted_file="$state_dir/accepted.md"
if [[ -s "$accepted_file" ]]; then
    # Two plain greps rather than one alternation: `\?` in a BRE is a GNU extension and this
    # script runs wherever the checkout is.
    accepted_keys="$run.accepted"
    grep -v '^[[:space:]]*#' "$accepted_file" | grep -v '^[[:space:]]*$' > "$accepted_keys" || :
    if [[ -s "$accepted_keys" ]]; then
        echo "  --  carrying $(wc -l < "$accepted_keys" | tr -d ' ') accepted finding(s)"
        {
            echo
            echo "── ACCEPTED FINDINGS ─────────────────────────────────────────────────────────"
            echo
            cat "$accepted_keys"
        } >> "$prompt_file"
    fi
fi

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
        # 120 was about one slice of a four-slice transcript, so the accounting step below was
        # being asked about findings it had mostly not been shown.
        sed -n '6,'"${REVIEW_PRIOR_LINES:-800}"'p' "$prior_transcript"
        echo
        echo "Do two things, in this order:"
        echo
        echo "1. For each finding above, one line: \`WAS: <path :: slug> --"
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

# The reviewer CLI: prompt and diff on stdin, the final message into "$1", diagnostics into "$2".
# Read-only either way: Codex by its sandbox; Claude by `dontAsk`, which denies every tool not
# named in `--allowedTools`, with the writing tools also disallowed outright.
run_reviewer() {
    local out="$1" log="$2"
    case "$REVIEW_ENGINE" in
        codex)
            # `--output-last-message` keeps Codex progress and diagnostics out of the verdict text.
            local pins=()
            [[ -n "$REVIEW_MODEL" ]] && pins+=(-m "$REVIEW_MODEL")
            [[ -n "$REVIEW_EFFORT" ]] && pins+=(-c model_reasoning_effort="$REVIEW_EFFORT")
            codex -a never exec --sandbox read-only ${pins[@]+"${pins[@]}"} \
                --output-last-message "$out" - > "$log" 2>&1
            ;;
        claude)
            # `-p` prints only the final message, so stdout is the verdict text.
            claude -p --model "$REVIEW_MODEL" --effort "$REVIEW_EFFORT" \
                --permission-mode dontAsk --no-session-persistence \
                --allowedTools Read Grep Glob "Bash(git diff:*)" "Bash(git log:*)" \
                    "Bash(git show:*)" "Bash(git grep:*)" \
                --disallowedTools Edit Write NotebookEdit \
                > "$out" 2> "$log"
            ;;
    esac
}

# One pass over one diff. Echoes the findings indented; returns 1 for BLOCK, 2 for no verdict.
review_one() {
    local slice_diff="$1" label="$2" out log
    out="${review_out}.$(echo "$label" | tr -c 'A-Za-z0-9._-' '_')"
    log="$out.log"
    # A failed invocation is inconclusive even if it wrote a partial reply.
    #
    # Claude's model and effort are pinned rather than inherited from the CLI's own config. This
    # is the one task that is paid for by what it does *not* miss, so it takes the top tier and
    # the high effort whatever the interactive default is set to. Codex runs on its configured
    # default unless `REVIEW_MODEL`/`REVIEW_EFFORT` say otherwise.
    if ! { cat "$prompt_file"; printf '\n\n── DIFF TO REVIEW ──\n'; cat "$slice_diff"; } \
        | run_reviewer "$out" "$log"; then
        echo "  ! $REVIEW_ENGINE review did not complete"
        tail -n 20 "$log"
        return 2
    fi
    if [[ ! -s "$out" ]]; then
        echo "  ! $REVIEW_ENGINE returned no review"
        tail -n 20 "$log"
        return 2
    fi
    sed 's/^/    /' "$out"
    # `<<<` rather than `## $label`: the reviewer emits its own `##` headings, so the slice
    # boundary and the slice content were the same shape and no round could be read back
    # mechanically -- not by the next round, and not by anything counting findings.
    { echo; echo "<<<REVIEW $label>>>"; echo; cat "$out"; } >> "$transcript"
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
