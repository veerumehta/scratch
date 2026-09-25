# Authoring in Plato: a draft workspace and a real UI

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: plan, 2026-09-20. Written against japes `c8b8ea4` on `v2.5.3`.

Builds on `plan_pack_store.md` §9.1, which already answered the question this plan implements.
Read that section first: it decided the shape, and nothing here overturns it.

## 1. The decision is already made, and it is the one being asked for

D1 was answered on 2026-09-08: *both, in stages*. A published `(pack_id, version)` stays
immutable, because that is what answers **which pack version produced this decision**. Crafting and
updating happens on a **draft**, which is not a `pack_version` row: it gets its own mutable row and
becomes an immutable `pack_version` at publish.

So "authoring, with versioning still immutability-based, including something marked as now fixed"
is `pack_draft` promoted to `pack_version`. Promotion *is* the marking-as-fixed. Stage 1 (import a
built pack) shipped in 2.5.2 with upload and activation. This plan is Stage 2.

The property that must survive: **nothing that has answered a request can change afterwards.** A
draft has never answered one. A published version has, or may.

## 2. What policy-workbench's schema says we would need

Its 32 tables split five ways. Plato covers one of them today.

| Concern | policy-workbench | Plato today |
|---|---|---|
| Authored content and history | `projects`, `documents`, `versions`, `doc_contents`, `graph_nodes/edges`, `baseline_docs` | nothing |
| Review workflow | `proposals`, `proposal_comments`, `proposal_views`, `proposal_activity_events`, `comments`, `change_traces` | nothing |
| Agent sessions | `agent_sessions`, `agent_messages`, `agent_staged_changes`, `ai_jobs` | `agent_session`, `turn_run`, `turn_run_event` |
| Identity and membership | `user_profiles`, `project_members` | nothing; identity is a gateway header |
| Assets, jobs, evaluation | `pdf_assets`, `file_assets`, `git_jobs`, `quality_runs`, `macer_*` | `pack_version` blobs |

Two structural differences decide the work:

**Its `versions` table is mutable-by-lineage, ours is immutable-by-contract.** `versions` carries
`parent_version_id`, `blob_path` and `commit_sha`; `agent_staged_changes` carries `rel_path`, `op`
and `content_hash`. That is an editable working copy with staged diffs over a git backing. Copying
it would put an editable row where `pack_version` guarantees there is not one. The draft table is
how we get the same capability without touching that guarantee.

**It has durable user rows; we deliberately do not.** Review needs to say who proposed, who
commented and who approved, and a gateway header cannot be a foreign key. This is a real new
concern for Plato, not a port.

## 3. Tables

Five new, all in `plato_control`, all tenant-scoped at construction (the rule
`DbAssistantManifestStore` set: a caller cannot omit the tenant on a query).

| Table | Holds | Notes |
|---|---|---|
| `pack_draft` | one mutable working copy per `(tenant_id, pack_id)` | `base_version` names the `pack_version` it was opened from, null for a new pack |
| `pack_draft_file` | the draft's files as rows: `rel_path`, `content`, `content_hash`, `op` | rows, not an archive; an archive is what publish *produces* |
| `pack_draft_event` | who changed what, when | the audit trail `config_audit_event` already models for settings |
| `pack_review` | a draft submitted for review: state, submitter, decision | absent in "no review" deployments; the state machine is draft → in_review → published |
| `pack_review_comment` | a comment on a draft file and line | threads by `parent_id`, like policy-workbench's |

`pack_version` is untouched. Publish reads the draft's files, builds the archive the existing
`DbPackVersionStore.publish` already takes, and writes the immutable row. `PackVersionExists`
stays the refusal for a re-publish.

**Identity.** `pack_review` and `pack_draft_event` need a durable author. Smallest thing that
works: store the gateway's user id as an opaque string, and add a `user_profile` row only when a
deployment needs display names. Do not build membership until a second consumer asks.

## 4. The UI

Plato has three pages today: `dashboard.html`, `packs.html`, `info.html`. Each is one
self-contained file with no build step, an inline CSP, and mount-prefix awareness for the gateway.
That is right for an operator console and cannot hold a file tree, a diff view and comment threads.

**A React SPA, served by Plato under the same prefix.** `ui/` already carries the stack decision
(React 18, Vite, MUI, Redux Toolkit, React Router), though its contents are a dead scaffold from
June describing a queue monitor that was never built; reuse the choice, not the code.

Three surfaces, in this order:

1. **Pack browser** — the existing `packs.html` content, as the SPA's first screen. Proves the
   serving, routing and auth path with a page that already exists.
2. **Draft editor** — file tree, editor, save. `pack_draft_file` rows behind it.
3. **Review** — submit, diff against `base_version`, comment, publish.

**The operator console stays as it is.** `/info`, `/health` and the degraded dashboard are what an
operator reads *when the replica will not start*, which is exactly when a JS bundle is the wrong
dependency. They remain static HTML; the SPA is an additional surface, not a replacement. This is
the same reasoning `create_info_router` already carries for staying ungated.

**Production deployments that do not author** get the SPA built out, or the routes refused by
posture. Prefer the posture gate: one image, and `relaxed_only` already exists for exactly this.

## 5. Order of work

1. `pack_draft` + `pack_draft_file` + the store, with migration `0005`. No UI: a draft can be
   created, edited and published through the API, and publish produces the same archive upload does.
2. Serve a built SPA from Plato, with the pack browser only. Settles the build, the prefix, the CSP
   and the auth path.
3. Draft editor in the SPA.
4. `pack_review` + comments, and the review surface.

(1) is useful alone: jaci and Studio can drive a draft over HTTP before any UI exists.

## 6. Open decisions

- **Does a draft belong to a tenant or to a user?** Tenant-scoped matches every other store here.
  Per-user drafts need a third scope and are what "two people editing" actually requires.
- **Does publish require review?** A deployment flag, or a property of the tenant. Not a code
  branch chosen once.
- **What does the SPA do about the no-build-step property?** Building it means japes ships a
  `node_modules` build in CI and a bundle in the image. That is a real change to what the image is,
  and it is the reason the three static pages were written the way they were.
- **Does the draft hold the pack as files or as structured rows?** Files keep the loader unchanged
  and make publish a zip. Rows make the editor richer and the loader a second consumer.
  `plan_pack_upload.md` §6 flags this as the thing that would make the archive-shaped design wrong.

## 7. What would make this wrong

- **If Studio becomes the only authoring path.** Then Plato's editor is a debugging tool and the
  draft table is a cache, not a system of record.
- **If review has to span packs.** `pack_review` is per-draft; a change set across several packs is
  a different object and a different table.
