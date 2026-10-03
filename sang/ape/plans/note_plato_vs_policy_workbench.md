# Note: what Plato still needs to match policy-workbench

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Written 2026-10-03 from three read-only inventories: the workbench backend (`policy-workbench/backend`),
its frontend (`frontend/src`), and Plato's authoring surface plus the prior plans
(`plan_policy_jtbd_extraction.md` §6 and §10, `plan_plato_authoring.md`). Nothing here is built. Frontend
per-screen detail is partly inferred from API usage; the workbench's own docs are stale in places
(README says "no git", architecture doc says Alembic is unused), so the code was trusted over them.

Standing decisions this note does not reopen: the SDK owns authoring and both apps are shells; the
workbench's git content backend, membership tables and Lexical editor are not lifted; its chat agents
are replaced by `pipelines.chat` plus `InteractiveAgent`, and chat writes only proposals.

## Where Plato already matches or exceeds it

Extraction from documents (three representations, per-rule provenance, program-scoped policies with
explicit relations, lint against the draft, Python rules); per-rule proposals with comments; draft then
immutable `pack_version`, activation with `If-Match`, audit trail (`/history`), releases; assess and
case runs with suspend and resume; eval control plane (datasets, experiments, compare, baselines,
custom scorers); feedback service; resumable SSE with `seq`; durable stop; lanes and admission; typed
client. The workbench has no equivalent of the per-rule model, assess, activation or the eval plane.

## Gaps, by priority

**P1: blocks "Plato runs the full loop" (the precondition for asking the workbench team to switch)**

| # | Gap | Workbench has | Plato has |
|---|---|---|---|
| 1 | Authoring chat not mounted | `/api/pf/process-stream`, sessions, cancel, history | `pipelines.authoring_chat` built, not routed |
| 2 | Review lifecycle for a whole draft | raise review, reviewer inbox, pending count, diff, activity, publish, close, rollback, comments | per-rule proposals only; `pack_review` unbuilt; publish is a direct author action |
| 3 | Reviewer vs author roles | `owner` and `reviewer` (reviewer from the gateway role `X-User-Roles`, not stored) | binary `may_author` in `whoami` |
| 4 | Draft history, diff, revert | versions, fork, revert, `GET /diff`, change traces | `pack_draft` mutable, no `pack_draft_event` |
| 5 | Comments on draft content | comments on a version, anchored to text or graph node | comments on proposals only |
| 6 | Persisted quality runs | quality rules per project, persisted runs, per-finding triage (`PATCH`) | lint runs inside extraction and publish check; nothing persisted or triaged |
| 7 | JTBDSet export and KH publish | `export-jtbd`, publish links a KH entity | the adapter exists (`pipelines.jtbdset`) with no route |
| 8 | User and reviewer lookup | `/api/users?q=`, `/api/reviewers` from the gateway directory | none |

**P2: parity worth having, not blocking**

| # | Gap | Note |
|---|---|---|
| 9 | Semver bump suggestion at publish | workbench: patch for one file, minor for several, major for several sections; trivial helper |
| 10 | Rebase a draft onto a newer published version | `sync-base`, `reset-to-baseline`, cached 3-way `mergeability`; also closes `TODO(draft-merge-lost-update)` |
| 11 | Extraction progress over SSE | extraction runs are poll-only; chat and case runs already stream |
| 12 | Queue and cost stats routes | `/queue-stats`, `/cost-stats`; the ledgers exist, no route |
| 13 | Reviewer comparison report | xlsx with blank accept/comments columns from `findings_compare` |
| 14 | Notifications | the workbench has none either (inbox is pull-based); keep parity, do not add |
| 15 | PDF convert as a tracked job, Notion import | `to_markdown` conversion exists inside extraction and `/documents`; no job record, no Notion connector |

**P3: not lifting, with reasons**

Git content backend and its outbox (`git_jobs`); membership and project tables (a second consumer now
exists, so revisit only if gateway roles prove insufficient, D3 below); the Lexical/TipTap editor and
chunked markdown save (client concern); the graph view parsed from markdown (Plato's canonical policy
is the source; a derived `GET .../graph` could come later if the screen is wanted); Azure Backup
routes; the dev user switcher and `/api/dev/*`; the legacy stub agent routes and `ai_stub`; folder
upload fan-out (client); the `pf_*` raw-SQL session store (Plato has `DbSessionStore`).

## Decisions wanted

| # | Question | Recommendation |
|---|---|---|
| D1 | How does the workbench frontend reach Plato? | Rewrite its `client.js` onto Plato's routes via `jazzx-plato-client`; do not add a `/api/projects/...` compatibility façade, which would fork the contract. The frontend is a Module Federation remote into `jaxi-web`, so only its API layer changes. |
| D2 | Does publish require review? | Yes in a deployed posture, optional locally: publish needs an approved `pack_review`. This was left open in `plan_plato_authoring.md`. |
| D3 | Roles and membership | Gateway roles only, no tables: `reviewer` and `author` from `X-User-Roles`, as the workbench does for reviewers. Per-pack owner can be the draft's creator. Revisit membership if per-project access lists are required. |
| D4 | MACER testing | The workbench's "Test with MACER" starts a Flowable process and reads MLflow. Plato's eval plane covers generic experiments. Decide whether Plato calls MACER (an external integration) or the eval plane replaces it; this is the largest functional difference and not decided here. |
| D5 | Rebase and 3-way merge (gap 10) | P2 unless several authors edit one pack concurrently; ask whether they do. |

## Suggested sequence

1. Mount the authoring chat (gap 1; runtime session; routes and SSE patterns exist).
2. `pack_review` plus roles (gaps 2 and 3): tables `pack_review` and `pack_review_comment` as the
   authoring plan already proposed, reviewer inbox and pending-count, publish gated on approval,
   `whoami` gains `roles` and `may_review`.
3. `pack_draft_event` with diff and revert (gap 4), then draft-file comments (gap 5).
4. Persisted lint runs with triage (gap 6); JTBDSet export route (gap 7); user lookup seam (gap 8).
5. Typed client methods and contracts land with each route, as for the other Plato routes.

Ownership: authoring, review and lint are the policy session's (`plato/api/authoring.py`, packs and
assess routes); the chat mount, SSE, jobs and client are the runtime session's. Gaps 2 to 8 therefore
want a plan from the policy session; gap 1 and gaps 11 and 12 are mine.

## Caveats

Plato route lists came from an inventory; three handlers were not opened (`POST /packs/drafts/{id}`,
the second method on `/sessions/{sid}`, `plato/jobs.py`). The workbench's quality panel, review roles
check and the reviewer-gated MACER button were inferred from API usage and a code comment, not traced
in the UI. Checked directly: no Plato route exports a JTBDSet, the authoring chat is not mounted,
`whoami` carries only `may_author`, and no `pack_draft_event` or `pack_review` exists.
