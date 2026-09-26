"""Reply to and resolve PR #75's open review threads: fixed ones name the fix, declined ones say why.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Dry run by default: prints each open thread and what it would post. `--apply` posts the reply
and resolves the thread. A thread no rule below matches is listed and left alone.

    python3 scripts/local/resolve_pr75_threads.py            # see the plan
    python3 scripts/local/resolve_pr75_threads.py --apply    # post and resolve
"""

import json
import subprocess
import sys

OWNER, REPO, PR = "JazzX-LLC", "japes", 75

# (path, phrase in the first comment, reply). First match wins.
RULES = [
    ("jazzx_sdk/pack/draft_db.py", "un-normalized",
     "Fixed in 7a5ecaca: `check_rel_path` returns the normalized path, so `a//b` and `./a/b` are "
     "one file on every read, write and delete."),
    ("jazzx_sdk/agents/adjudication/segment.py", "silently dropped",
     "Declined: not silent. A replica answering the wrong field is excluded from the vote, and a "
     "rule no replica answered usably becomes INDETERMINATE / CONDITION_UNEVALUABLE with "
     "\"every replica failed or dropped this obligation\" (`segment.py:246`)."),
    ("jazzx_sdk/fabric/canonical/python_check.py", "ImportFrom",
     "Declined: exempting imported names reopened the builtin (`from re import compile as eval` "
     "then `del eval`), so a forbidden builtin name is refused whatever binds it. "
     "`import re` + `re.compile` is the supported form."),
    ("jazzx_sdk/fabric/canonical/python_check.py", "Nested `async def`",
     "Fixed in 7a5ecaca: any `async def`, `await`, `async for`, `async with` or async "
     "comprehension anywhere in a rule is refused."),
    ("jazzx_sdk/pack/rule_merge.py", "Non-list",
     "Fixed in 7a5ecaca: a `policies:` that is not a list of mappings (including a falsy `{}`) is a "
     "`ValueError` naming the file, which the merge route answers with a 409."),
    ("jazzx_sdk/pack/manifest_loader.py", "programs",
     "Fixed in eabde980, without silently dropping the entry: `programs()` leaves out a value that "
     "is not a policy id or a list of them (numbers are ids, booleans and floats are not), and "
     "lint reports each one as `malformed_program` at its manifest path, so the mistake is "
     "visible instead of a 500 or a program that quietly applies nothing."),
    ("jazzx_sdk/experts/policy/default.py", "suppressed_ids",
     "Declined, and pinned in c87b29bc: precedence decides. Policies evaluate highest first, and "
     "the first directive to supersede a rule sets its reason. If the policy replacing Y outranks "
     "the one suppressing it, X stands in for Y and carries Y's replacement of Z; if the "
     "suppression outranks it, Y's chain is cut and Z evaluates. The suggested change would let "
     "a lower-precedence suppression undo a higher-precedence replacement. "
     "`test_replacing_and_suppressing_one_rule_is_decided_by_precedence` covers both orders."),
    ("jazzx_sdk/pack/draft_db.py", "rejected as dotfiles",
     "Not a defect: `PurePosixPath` drops `.` components, so `PurePosixPath(\"./foo/bar\").parts` "
     "is `('foo', 'bar')` and `check_rel_path(\"./foo/bar\")` returns `foo/bar`. "
     "`test_one_path_spelled_two_ways_is_one_file` pins it; `./.env` is still refused."),
    ("plato/migrations/versions/0006_policy_authoring.py", "ix_proposal_status",
     "Declined: 0006 shipped in v2.5.4, so editing it would not reach any database at head; "
     "a change needs a new migration, for a small write cost on a low-volume table. The comment "
     "list query is served by `ix_proposal_comment_proposal_id` (line 44), not the `pack_id` "
     "index."),
    ("jazzx_sdk/pack/draft_db.py", "TOCTOU",
     "Fixed in f7510cb3: `write_file`, `delete_file` and `discard` lock the draft row first "
     "(`blocking_locked_first`), in one order, so concurrent writers cannot pass the file-count "
     "check together or deadlock."),
    ("jazzx_sdk/fabric/canonical/python_check.py", "asname",
     "Fixed in f7510cb3: a dunder `as` name is refused at the import."),
    ("jazzx_sdk/fabric/canonical/python_check.py", "dict(ctx)",
     "Fixed in f7510cb3, as a closed rule: `ctx` may appear only as `ctx[key]` or `ctx.get(key)`, "
     "so `dict(ctx)`, `{**ctx}`, `f(ctx)` and `g = ctx.get` are all refused."),
    ("jazzx_sdk/experts/policy/default.py", "Unhandled exception from gate evaluator",
     "Declined: evaluators raise only on authoring errors, and the main-path gate a few lines "
     "below is unguarded the same way by design; a missing dependency or evidence withholds or "
     "excuses instead of raising."),
    ("jazzx_sdk/server/vocabulary_review.py", "Policy(...)",
     "Not a defect: `RuleMergeRequest` types `policy_type` and `scope` as enums, so FastAPI "
     "answers a bad value with a 422 before the handler builds the `Policy`."),
    ("jazzx_sdk/fabric/canonical/python_check.py", "__builtins__",
     "Fixed in 90f32028, as a class rather than this one name: bare dunder names are refused, and "
     "so is any module reached through an allowlisted one (imports at top level, exact module "
     "names, each name bound once, no `*`, a bound module used only as `module.attr`)."),
    ("jazzx_sdk/fabric/graph/proposal_comments.py", "NUL",
     "Fixed in 90f32028: comments and both draft-store write paths strip the real NUL byte and "
     "lone surrogates (`safety.sanitize.strip_unstorable_chars`), leaving escape text alone."),
    ("jazzx_sdk/fabric/graph/proposal_comments.py", "register_metadata",
     "Not a defect: `DbStore.register_metadata` exists (`jazzx_sdk/fabric/db/store.py:293`) and "
     "is how a store with its own declarative base registers its tables."),
    ("jazzx_sdk/pack/draft_db.py", "register_metadata",
     "Not a defect: `DbStore.register_metadata` exists (`jazzx_sdk/fabric/db/store.py:293`)."),
    ("jazzx_sdk/pack/rule_merge.py", "yaml.safe_load",
     "Fixed in 90f32028: both loads go through `_load_yaml`, which raises `ValueError` naming the "
     "file; the merge route answers that with a 409."),
    ("jazzx_sdk/pack/rule_merge.py", "ValidationError",
     "Not a defect: in pydantic v2 `ValidationError` subclasses `ValueError`, so the route's "
     "`except ValueError` already answers 409. `test_a_broken_policy_file_is_a_value_error_not_a_crash` "
     "pins it."),
    ("jazzx_sdk/server/policy_extract_api.py", "upload.filename",
     "Fixed in 90f32028: the 413 names the sanitized basename."),
    ("jazzx_sdk/server/policy_extract_api.py", "_evict",
     "Fixed in 90f32028: a submit with every `MAX_RUNS` slot still running is refused "
     "(`ExtractionBusy`, 503), and the route checks `has_room()` before reading uploads."),
    ("jazzx_sdk/agents/adjudication/segment.py", "KeyError",
     "Declined: an unregistered kind failing loudly is deliberate (`get_condition_evaluator`'s "
     "docstring). Condition kinds are a closed union whose every member registers at import, and "
     "a raising segment is reported in `failed_segments` rather than crashing adjudication."),
    ("jazzx_sdk/fabric/graph/proposal_store_db.py", "vocabulary_proposal",
     "Not a defect: no Plato migration ever created `vocabulary_proposal` (only the ORM name "
     "existed), and no sibling repo constructs a `DbProposalStore`, so there are no rows to move."),
    ("jazzx_sdk/pipelines/jtbdset.py", "int(sequence)",
     "Fixed in 4a306155: a `sequence` that is not a whole number leaves the rule at `Rule`'s "
     "default priority; the raw value stays in the rule's metadata."),
    ("jazzx_sdk/fabric/canonical/condition_evaluator.py", "ProcedureEvaluator.render_for_batch",
     "Fixed in 7c3ed945, with the natural-language one: see that thread."),
    ("jazzx_sdk/fabric/canonical/condition_evaluator.py", "render_for_batch",
     "Fixed in 7c3ed945, upstream of rendering: one `missing_evidence` rule is used by the "
     "natural-language, procedure and Python evaluators and by the batch splitter, so a rule "
     "missing a read is EVIDENCE_MISSING before the batch and never reaches the prompt."),
    ("jazzx_sdk/server/vocabulary_review.py", "CallerIdentity",
     "Not a defect: `CallerIdentity` is imported at the top of `create_vocabulary_review_router` "
     "(line 263) and both handlers are closures inside it; line 288 uses it the same way, and the "
     "comments route is covered by `test_policy_authoring_api.py`."),
    ("jazzx_sdk/fabric/canonical/condition_evaluator.py", "reads check runs before the agent",
     "Fixed in c62a4873: a missing profile or reasoning agent withholds (POLICY_NOT_ACTIVATED), "
     "asked before the evidence, in the ratio, matrix, natural-language and procedure evaluators."),
    ("jazzx_sdk/fabric/canonical/condition_evaluator.py", "Uncaught `ValueError`",
     "Fixed in c62a4873: the agent check withholds (POLICY_NOT_ACTIVATED) instead of raising, "
     "asked before the evidence."),
    ("jazzx_sdk/server/policy_extract_api.py", "before_write",
     "Fixed in c62a4873: `before_write` is awaited through `call_maybe_async`."),
    ("plato/api/packs.py", "404",
     "Fixed in c62a4873: `PackNotFound` is a 404, any other `materialize` failure a 503."),
    ("jazzx_sdk/pack/draft_db.py", "rowcount",
     "Fixed in b11194c0: `delete_file` stamps the draft only when a file was deleted."),
    ("jazzx_sdk/pack/draft_db.py", "assert",
     "Fixed in 578744f3: colliding seed paths are refused up front with a `ValueError` naming the "
     "path, and the assert is gone."),
    ("jazzx_sdk/fabric/canonical/python_check.py", "AsyncFunctionDef",
     "Fixed in 578744f3: an `async def` entrypoint is refused with its own message."),
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
