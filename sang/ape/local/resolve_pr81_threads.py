"""Reply to and resolve PR #81's open review threads: fixed ones name the fix, declined ones say why.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Dry run by default: prints each open thread and what it would post. `--apply` posts the reply
and resolves the thread. A thread no rule below matches is listed and left alone.

    python3 scripts/local/resolve_pr81_threads.py            # see the plan
    python3 scripts/local/resolve_pr81_threads.py --apply    # post and resolve
"""

import json
import subprocess
import sys

OWNER, REPO, PR = "JazzX-LLC", "japes", 81

# (path, phrase in the first comment, reply). First match wins.
RULES = [
    ("jazzx_sdk/agents/interactive/guardrail_kinds.py", "fresh",
     "Fixed in 428ee718: a host `GuardrailRegistry` is copied even with no pack guardrails, and every "
     "guardrail is copied at its own tier (a tier-1 floor was re-registered at 3). A dict or None "
     "host is returned as is: the binding adds to a copy of a dict, never to it."),
    ("jazzx_sdk/fabric/canonical/caps.py", "isinstance(raw, (int, float))",
     "Fixed in 428ee718: the compare value is read as the evaluators read a number (`_number`: a "
     "`Decimal`, a numeric string, a float); anything else, or a non-finite number, has no value."),
    ("jazzx_sdk/fabric/canonical/caps.py", "float(cell)",
     "Fixed in 428ee718: a cell that is neither an ineligible marker nor a number is unresolved, "
     "not a raised error."),
    ("jazzx_sdk/fabric/canonical/condition_evaluator.py", "membership",
     "Fixed in 428ee718: on a decimal catalog fact, the value, the comparison value and each "
     "membership member are read as the exact decimal a float spells before the strict type check."),
    ("jazzx_sdk/fabric/canonical/condition_evaluator.py", "non-finite",
     "Fixed in 428ee718, for every `_number` read in the matrix evaluator (axis and compare value): "
     "not a finite number is INDETERMINATE."),
    ("jazzx_sdk/fabric/db/locking.py", "session.bind",
     "Declined: `AsyncSession.bind` exists in SQLAlchemy 2.0 (it is how an engine-bound session "
     "reports its bind). The Postgres test that races concurrent claims on one key fails without "
     "the advisory lock and passes with it, so the dialect check does reach Postgres."),
    ("jazzx_sdk/formal/canonical_formulation.py", "KeyError",
     "Fixed in 428ee718: a source the draft names that is no longer supplied is refused as "
     "\"source changed after formulation\"."),
    ("jazzx_sdk/formal/compiler.py", "vacuous",
     "Fixed in 428ee718: the empty-selection error no longer prints the always-empty gap list."),
    ("jazzx_sdk/formal/compiler.py", "contains `:`",
     "Fixed in 428ee718: replacements match each compiled rule's recorded (policy_id, rule_id), not "
     "a split of the key."),
    ("jazzx_sdk/evaluation/metrics.py", "Mapping",
     "Fixed in 428ee718: `subset_match` walks any `Mapping`."),
    ("jazzx_sdk/runs/chat.py", "Orphaned",
     "Declined: `consuming` is awaited directly, so cancelling this task cancels the awaited task "
     "too; a test that cancels the execution mid-stream sees no events after it, with or without "
     "an extra cancel."),
    ("jazzx_sdk/runs/chat.py", "non-optional",
     "Fixed in 428ee718: `CoordinatedTurn.run` is typed `TurnRun | None`."),
    ("jazzx_sdk/agents/interactive/recorder.py", "Offset-based",
     "Tracked: the TODO at the call (`offset-pages-unordered`) records it; the stores in use "
     "return insertion order, and keyset paging waits on the canonical store exposing an order."),
    ("tests/test_plato_formal_gate.py", "Bare module import",
     "Fixed in 428ee718: imported as `tests.test_plato_packs_api`."),
    ("tests/test_plato_runs_api.py", "bare module names",
     "Fixed in 428ee718: both imported with the `tests.` prefix."),
    ("tests/test_plato_formal_gate.py", "lifespan",
     "Declined: the formal router has no startup state (its capacity semaphore is module "
     "level and the pack store is passed in), so entering the client changes nothing these "
     "tests exercise."),
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
