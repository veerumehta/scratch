"""Reply to and resolve PR #91's open review threads: each reply names the fix or says why not.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

The replies are the ones in /tmp/japes_pr91_replies.md, one per bot comment. Dry run by default:
prints each open thread and what it would post. `--apply` posts the reply and resolves the thread.
A thread no rule below matches is listed and left alone. This script never runs itself.

    python3 scripts/local/resolve_pr91_threads.py            # see the plan
    python3 scripts/local/resolve_pr91_threads.py --apply    # post and resolve
"""

import json
import subprocess
import sys

OWNER, REPO, PR = "JazzX-LLC", "japes", 91

# (path, phrase in the first comment, reply). First match wins.
RULES = [
    ("plato/api/pack_review.py", "fails open",
     "Fixed in 23874a8b for a strict posture: a review nobody owns (no submitter and no draft "
     "creator on record) is refused with a 403 instead of being open to any author. A relaxed "
     "posture still allows it by decision: review gating is optional locally, and a draft made "
     "without identity has nobody to check against. "
     "`test_resubmitting_a_review_nobody_owns_is_refused_in_a_strict_posture` and its relaxed "
     "twin pin both."),
    ("jazzx_sdk/pack/review_db.py", "decision_note",
     "Fixed in 23874a8b: a resubmit clears `decision_note` with `decided_by` and `decided_at`, so "
     "the next reviewer never sees the previous reviewer's note under no author."),
    ("plato/api/stats.py", "truncated",
     "Fixed in 5aeade22, at the query rather than the flag: `TurnRunStore.active(input_equals=)` "
     "selects the tenant's runs before the limit (a JSON-path filter on Postgres and sqlite), so "
     "another tenant's backlog neither crowds this tenant's runs out of the report nor marks it "
     "truncated, and `truncated` is about this tenant's own count. This route is the only caller "
     "of `active`; `cost-stats` reads a per-tenant store already."),
    ("jazzx_sdk/pack/review.py", "Lossy decode",
     "Fixed in 23874a8b: the digest decodes with `surrogateescape`, which is reversible, so two "
     "files that differ only in non-UTF-8 bytes digest differently. A review approved before this "
     "of a draft holding non-UTF-8 bytes no longer matches and must be resubmitted (409 "
     "`review_stale` until then); noted in the CHANGELOG."),
    ("plato/migrations/versions/0022_version_notes.py", "ACCESS EXCLUSIVE",
     "Accepted as is. On PostgreSQL 11 and later, adding a NOT NULL column with a constant "
     "default is a catalog-only change (no rewrite), and `pack_version` and `pack_draft` are "
     "small, low-write tables, so the lock is momentary. The migration runs at deploy before the "
     "replica serves. If a deployment ever sees it queue behind a long transaction, set "
     "`lock_timeout` on the migration connection; the three-step backfill would add risk for no "
     "gain here."),
    ("jazzx_sdk/server/eval_api.py", "dict(response.usage)",
     "Fixed in 5aeade22: `dict(response.usage) if response.usage else None`, as the session "
     "invoker already did. It is the only `dict(<x>.usage)` of an optional value in `jazzx_sdk`, "
     "`plato` and the client; the test runs usage `None`, `{}` and a real value and raises "
     "`TypeError` on the old line."),
    ("jazzx_plato_client/_feedback.py", "Boolean query",
     "Not a defect: httpx writes a bool query value as `true`/`false` (`httpx.QueryParams("
     "{'a': True})` is `a=true`), so no `_query` copy needs to lowercase it. A test (5aeade22) "
     "holds the wire format for the feedback and eval mixins and a stream, so a change of "
     "transport would be caught."),
    ("jazzx_sdk/evaluation/adjudication_scorers.py", "KeyError",
     "Fixed in 5aeade22: both reads go through `_votes_by_status`, which returns no votes for a "
     "tally with no `split` (or a non-mapping one), read as unanimous. The tally carries `split` "
     "today; this covers runs stored before it did and hand-written ones."),
    ("plato/api/pack_review.py", "Self-approval guard",
     "Fixed in 5aeade22 for a strict posture, at the cause: submitting, deciding, closing and "
     "resubmitting a review, and commenting or triaging, need a caller user id (401), so the "
     "self-approval check and the audit trail always have an identity. Locally nothing changes: "
     "self-approval is allowed there by default, and with it explicitly off an anonymous caller "
     "has no identity to compare, which the posture accepts."),
]

QUERY = """query($owner:String!,$repo:String!,$pr:Int!){repository(owner:$owner,name:$repo){
pullRequest(number:$pr){reviewThreads(first:100){nodes{id isResolved isOutdated path line
comments(first:1){nodes{body}}}}}}}"""


def gh(*args: str) -> dict:
    out = subprocess.run(["gh", "api", "graphql", *args], check=True, capture_output=True, text=True)
    return json.loads(out.stdout)


def main() -> None:
    apply = "--apply" in sys.argv
    data = gh("-f", f"query={QUERY}", "-F", f"owner={OWNER}", "-F", f"repo={REPO}", "-F", f"pr={PR}")
    threads = data["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    unmatched = []
    for t in (t for t in threads if not t["isResolved"]):
        body = t["comments"]["nodes"][0]["body"] if t["comments"]["nodes"] else ""
        reply = next((r for p, phrase, r in RULES if p == t["path"] and phrase in body), None)
        where = f"{t['path']}:{t['line']}{' (outdated)' if t['isOutdated'] else ''}"
        if reply is None:
            unmatched.append(where + " -- " + body.splitlines()[0][:100] if body else where)
            continue
        print(f"{where}\n  {body.splitlines()[0][:100] if body else ''}\n  -> {reply}\n")
        if apply:
            gh("-f", "query=mutation($id:ID!,$b:String!){addPullRequestReviewThreadReply("
                     "input:{pullRequestReviewThreadId:$id,body:$b}){comment{id}}}",
               "-F", f"id={t['id']}", "-f", f"b={reply}")
            gh("-f", "query=mutation($id:ID!){resolveReviewThread(input:{threadId:$id})"
                     "{thread{isResolved}}}", "-F", f"id={t['id']}")
    if unmatched:
        print("Left alone (no rule matches):")
        for line in unmatched:
            print("  " + line)
    if not apply:
        print("\nDry run. Re-run with --apply to post these replies and resolve the threads.")


if __name__ == "__main__":
    main()
