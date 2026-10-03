# Plan: Plato authoring review parity (gaps 2 to 8)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Written 2026-10-03 by the policy session. Source: `note_plato_vs_policy_workbench.md` (gaps), `plan_plato_authoring.md`
(§3 tables, §6 open decisions; its `pack_review` and `pack_draft_event` rows were never built), the code read on
2026-10-03, and `policy-workbench/backend/app/api/{proposals,diff,comments,quality,users}.py` (read only).
Nothing here is built.

## Decisions already made (not reopened)

| # | Decision |
|---|---|
| D1 | The workbench frontend moves onto Plato routes via `jazzx-plato-client`; no `/api/projects/...` facade. |
| D2 | Publish needs an approved `pack_review` in a deployed posture, optional locally. |
| D3 | Roles from gateway `X-User-Roles` (`reviewer`, `author`), no membership tables. Pack owner = draft creator. `whoami` gains `roles`, `may_review`. |
| D5 | One author per pack for now. Rebase and 3-way merge (gap 10) stay P2, out of scope. |
| D4 | MACER testing: undecided, out of scope. |
| Gap 1 | Authoring chat is the runtime session's. This plan only fixes how review treats chat-made proposals (section 8). |

## 1. Facts from the code that shape the design

| Fact | Where | Consequence |
|---|---|---|
| Deployed vs local is `strict_mode()` (env) with an explicit `strict=` override on routers; `withholding`, `relaxed_only`, `relaxed_write_allowed` already read it | `jazzx_sdk/config/posture.py`, `config/envvars.py` | Review gate = `require_review: bool \| None` on the packs router, `None` meaning `strict_mode()`. Same pattern as `strict`. No new env var. |
| No code reads `X-User-Roles`. `CallerIdentity` has `user_id`, `email`, `name` only; fields come from `x-security-context` or `x-user-*` headers | `jazzx_sdk/identity.py:188,224` | Phase 1 adds `roles` to `CallerIdentity` (same `_field` reader, header `x-user-roles`, lowercased, comma split). Role names are config (`PLATO_REVIEWER_ROLE`, `PLATO_AUTHOR_ROLE`, defaults `reviewer`, `author`), not literals. |
| `may_author` today = `not withholding(strict, auth)`, a posture check, not a role | `jazzx_sdk/server/whoami.py` | Keep it as the posture floor. Role check layers on top only when roles are present (section 2). |
| `pack_draft` records `updated_by_user_id` only; no creator | `jazzx_sdk/pack/draft_db.py:37` | Owner = creator needs `created_by_user_id` (migration 0016). Existing rows: null, treated as ownerless (any author may act). |
| `DbPackDraftStore.write_file`/`delete_file` already take `actor_id` and lock the draft row | `draft_db.py:182,223` | Events (gap 4) are written inside the same transaction as the write. |
| Publish is `POST /packs/drafts/{id}/publish`, gated only by `_refuse_unless_author` | `plato/api/packs.py:524` | The review gate goes here and on nothing else; direct upload `POST /packs` stays as is (decision R3). |
| Per-rule proposals and comments exist (`DbProposalStore`, `DbProposalCommentStore`, table `proposal_comment`) and are a different object from a draft review | `fabric/graph/proposal*.py`, `server/vocabulary_review.py` | `pack_review` is per-draft and new. Proposals are inputs to a draft (`merge-rules`), reviewed through the draft. |
| Stores are SQLAlchemy over `fabric.db`, so one implementation serves sqlite and postgres; tests also run on Postgres via `JAPES_TEST_POSTGRES_URL` | `draft_db.py`, CLAUDE.md | "Store protocol" below = a `Db*Store` class plus a small `Protocol` in the same module; no second backend. Every new test file gets the Postgres run. |
| Latest migration is `0015_policy_extraction_runs` | `plato/migrations/versions/` | New: 0016, 0017, 0018 (below). Chain via `down_revision`. |
| `export_jtbdset(policies, *, title, description, version, programs)` exists with no route; `import_jtbdset` likewise | `pipelines/jtbdset.py:180,228` | Gap 7 is a route plus a reader that lists a pack's policies. |
| `lint_pack(pack, *, policies)` returns `PackLintReport` of `PackLintFinding`; `ExtractionRun.linted` already carries a lint at extraction time | `pack/lint.py` | Gap 6 persists reports; it does not change lint. |

## 2. Roles and `whoami` (gap 3, with 2)

| Piece | Design |
|---|---|
| SDK: `jazzx_sdk/identity.py` | `CallerIdentity.roles: tuple[str, ...]`; `has_role(name)`. Reads `x-security-context.roles` or `x-user-roles`. |
| SDK: `jazzx_sdk/server/authoring_roles.py` (new) | `AuthoringRoles(reviewer: str, author: str)` from config; `may_author(identity, *, posture_ok)`; `may_review(identity)`; `refuse_unless_reviewer(request)`. A caller with no roles header at all (local, ungated) is treated as holding both, so local use needs no gateway. A caller with a roles header lacking `author` may not write drafts. |
| Separation of duties | A reviewer who is also the draft's owner may not approve that draft's review (`acting_user_id() != review.submitted_by`). Config toggle `PLATO_REVIEW_ALLOW_SELF_APPROVAL` default off in deployed, on locally (a single developer). Decision R4. |
| Plato: `whoami` | Adds `roles: list[str]`, `may_review: bool`. `may_author` keeps its meaning plus the role check. |
| Client | `whoami()` already returns a dict; add typed `Whoami` contract with `roles`, `may_review` in `jazzx_plato_client/contracts.py`. |

## 3. Gap 2: pack review lifecycle

### 3.1 SDK

| Piece | Path / type |
|---|---|
| Models | `jazzx_sdk/pack/review.py` (new): `PackReview` (id, pack_id, state, submitted_by, submitted_at, reviewer_id nullable, decided_by, decided_at, decision_note, base_version, head_digest, requested_reviewers list), `ReviewState` = `open \| approved \| changes_requested \| closed \| published`, `ReviewEvent`. |
| Store | `PackReviewStore` Protocol and `DbPackReviewStore(db, *, tenant_id)` in `jazzx_sdk/pack/review_db.py`: `submit`, `get`, `list(state, reviewer_id, submitted_by)`, `pending_count(reviewer_id)`, `decide`, `close`, `mark_published`, `for_pack(pack_id)`. Tenant fixed at construction like the other stores. |
| State machine | `open -> approved \| changes_requested \| closed`; `changes_requested -> open` (resubmit, new `head_digest`); `approved -> published` (publish) or `-> open` (draft changed after approval, automatic). One `open`/`approved` review per `(tenant, pack)`: unique partial index. |
| Head pin | `head_digest` = sha256 over sorted `(rel_path, content)` of the draft (`draft_digest(files)` in `draft_db.py`, using `jazzx_sdk.util.digest`). Approval stands only while the draft digest equals it. Gap 4 later swaps the digest for a revision number without changing the gate's shape. |
| Gate | `pack/review.py::require_approved(store, drafts, pack_id) -> PackReview` raises `ReviewRequired` / `ReviewStale`. |
| Rollback (workbench "rollback") | Not a review verb here: Plato has `DELETE /packs/{id}/{version}` (retire) and activation of an older version. Review row stays `published`. Noted, no build. |

### 3.2 Tables (migration `0016_pack_review`)

| Table | Columns |
|---|---|
| `pack_review` | `id` int pk, `tenant_id`, `pack_id`, `state`, `submitted_by`, `submitted_at`, `base_version` null, `head_digest`, `reviewer_id` null (assigned), `decided_by` null, `decided_at` null, `decision_note` text, `published_version` null; indexes on `(tenant_id, pack_id)`, `(tenant_id, state)`, `reviewer_id`; partial unique on `(tenant_id, pack_id)` where `state in ('open','approved')` (postgres and sqlite both support partial indexes). |
| `pack_comment` | `id`, `tenant_id`, `pack_id`, `review_id` null, `parent_id` null, `author_id`, `body`, `created_at`, `resolved_at` null, and anchor columns used by gap 5: `rel_path` null, `anchor` JSON null, `revision` int null. Created here so gap 5 needs no migration. |
| `pack_draft` (alter) | `created_by_user_id` string null. Postgres and sqlite both via `op.batch_alter_table`. |

### 3.3 Plato routes (`plato/api/pack_review.py`, new, registered like `authoring` in `plato/app.py`)

All under `{prefix}`; tenant from `tenant_of`; reads through `read_gate`, writes through `write_gate` as the drafts routes do.

| Method, path | Role | Request / response | Status |
|---|---|---|---|
| `POST /packs/drafts/{pack_id}/review` | owner or author | `{reviewer_id?, note?}` -> `PackReview` | 201; 404 no draft; 409 a review is already open; 422 draft empty or lint has errors (see 6) |
| `GET /packs/drafts/{pack_id}/review` | any reader | latest review for the pack, with `stale: bool` | 200; 404 none |
| `GET /packs/reviews?state=&mine=&assigned=` | any reader | list; `assigned=me` is the reviewer inbox | 200 |
| `GET /packs/reviews/pending-count` | reviewer | `{count}` for the caller | 200 |
| `GET /packs/reviews/{id}` | any reader | `PackReview` + `activity` (events) | 200; 404 |
| `POST /packs/reviews/{id}/decision` | reviewer, not the submitter unless R4 allows | `{decision: approve \| request_changes, note}` | 200; 403 role or self; 409 not open or stale digest; 422 empty note on request_changes |
| `POST /packs/reviews/{id}/close` | submitter or reviewer | `{note?}` | 200; 409 already terminal |
| `POST /packs/reviews/{id}/resubmit` | owner | `{note?}` re-pins `head_digest` | 200; 409 not `changes_requested` |
| `GET /packs/reviews/{id}/diff` | any reader | from gap 4's diff, base_version vs draft | lands with gap 4 |
| `POST /packs/drafts/{pack_id}/publish` (existing) | owner or author | adds `review_id` to the response | gate below |

Publish gate: if `require_review` (explicit, else `strict_mode()`) then `require_approved` must pass, else `409 {"code": "review_required" \| "review_stale"}`; on success the review moves to `published` with `published_version`, in the same request after `_publish_archive` returns (a failure after publish logs and leaves the version published, review stays `approved`; `mark_published` is idempotent). Locally with `require_review` false an approved review is not demanded, but if one is `open` publish still proceeds and closes it with note `published directly`.

### 3.4 Client

| Method (`PlatoClient`, `jazzx_plato_client/client.py`) | Contract (`contracts.py`) |
|---|---|
| `submit_pack_review(pack_id, *, reviewer_id=None, note="")` | `PackReview` |
| `pack_review(pack_id)` / `get_pack_review(review_id)` | `PackReview`, `PackReviewDetail` |
| `list_pack_reviews(state=None, assigned_to_me=False, mine=False)` | `list[PackReview]` |
| `pack_review_pending_count()` | `PendingCount` |
| `decide_pack_review(review_id, decision, note="")` | `PackReview` |
| `close_pack_review(review_id, note="")`, `resubmit_pack_review(review_id, note="")` | `PackReview` |
| `publish_draft(...)` (exists) | add `review_id: int \| None` to its contract |

### 3.5 Tests

| Test | Fails against current code because |
|---|---|
| `tests/test_pack_review.py::test_publish_refused_without_approval_when_strict` | strict publish succeeds today with no review. |
| `::test_approval_goes_stale_when_draft_changes` | no review exists to go stale. |
| `::test_self_approval_refused` and `::test_only_one_open_review_per_pack` (409) | routes absent. |
| `::test_state_machine_transitions_table` (every `(state, verb)` pair, legal and illegal) | module absent. |
| `tests/test_plato_whoami_catalog.py`: roles header `reviewer` gives `may_review` true; no header gives both true locally; header without `reviewer` gives false | `whoami` has neither field. The assertion on `X-User-Roles` is end to end through the ASGI app, not derived from the config constant. |
| `tests/test_pack_review_db.py` on sqlite and Postgres | store parity. |
| Client: `tests/test_plato_client_pack_review.py` against the ASGI app | typed contract round trip. |

## 4. Gap 4: draft history, diff, revert

| Piece | Design |
|---|---|
| Table `pack_draft_event` (migration `0017_pack_draft_event`) | `id` int pk (the revision), `tenant_id`, `pack_id`, `kind` (`opened \| write \| delete \| revert \| reset`), `rel_path` null, `actor_id`, `at`, `before_hash` null, `after_hash` null, `before` Text null, `after` Text null, `reverts_event_id` null. Full-text before and after (drafts are capped at `MAX_DRAFT_FILES` files and `MAX_DRAFT_FILE_BYTES` each, so growth is bounded by edits; retention is decision H1). |
| Store | `DbPackDraftStore` writes an event inside each `open`, `write_file`, `delete_file`, `discard` transaction (same session, under the existing row lock). New methods: `events(pack_id, *, after_id=None, rel_path=None, limit)`, `revision(pack_id) -> int`, `file_at(pack_id, rel_path, revision)`, `revert(pack_id, revision, *, rel_path=None, actor_id)` (appends a `revert` event; never rewrites history). |
| Diff | `jazzx_sdk/pack/diff.py` (new): `diff_files(base: dict[str,str], head: dict[str,str]) -> PackDiff` (per-file `added \| removed \| changed`, unified hunks via `difflib`, plus a rule-level summary for `policies/*.yaml`: rule ids added, removed, changed). Pure function, no store. Base for a draft = the `base_version` archive (`DbPackVersionStore` read), for a new pack empty. |
| Review pin upgrade | `pack_review.head_digest` stays; add `head_revision` int null column in 0017 so the review diff and stale check can use the revision when present. |
| Routes | `GET /packs/drafts/{pack_id}/events?after=&path=&limit=` -> `{events, next}`; `GET /packs/drafts/{pack_id}/diff?against=base \| revision:N` -> `PackDiff`; `POST /packs/drafts/{pack_id}/revert` `{revision, rel_path?}` -> `{revision}` (owner or author; 404 unknown revision; 409 file no longer exists and revert would need it); `GET /packs/reviews/{id}/diff` completes section 3.3. Reads under `read_gate`. |
| Client | `draft_events(...)`, `draft_diff(pack_id, against="base")`, `revert_draft(pack_id, revision, rel_path=None)`; contracts `DraftEvent`, `PackDiff`, `FileDiff`. |
| Tests | `test_draft_event_recorded_per_write` (fails: no events); `test_revert_restores_file_and_appends_event`; `test_diff_matches_difflib_on_known_pair` (expected hunks hand-written, not derived from `diff_files`); `test_event_and_write_roll_back_together` (inject failure after write); sqlite and Postgres. |

## 5. Gap 5: comments on draft content

| Piece | Design |
|---|---|
| Table | `pack_comment` from 0016 (`rel_path`, `anchor`, `revision`, `parent_id`, `resolved_at`). No new migration. |
| Anchor | `anchor` JSON: `{"kind": "line", "start": int, "end": int}` or `{"kind": "rule", "policy_id": str, "rule_id": str}` (the structured address Plato has that the workbench lacks, replacing its graph-node anchor). `revision` = draft revision at comment time. |
| Store | `DbPackCommentStore(db, *, tenant_id)`: `add`, `list(pack_id, review_id=None, rel_path=None, include_resolved)`, `edit` (author only, own body), `delete` (own, or reviewer), `resolve`/`reopen`. Rule-anchored comments survive edits; line anchors carry `revision` so a client can show "outdated" by comparing with `file_at`. No server-side re-anchoring (decision C2). |
| Routes | `GET /packs/drafts/{pack_id}/comments`, `POST /packs/drafts/{pack_id}/comments` (`review_id?` optional, defaults to the open review), `PATCH /packs/comments/{id}` (edit or `resolved`), `DELETE /packs/comments/{id}`. Roles: any author or reviewer may comment; edit own only; 403 else, 404 unknown, 422 anchor shape or path not in draft. |
| Client | `list_draft_comments`, `add_draft_comment`, `update_draft_comment`, `delete_draft_comment`; contract `PackComment`. |
| Tests | `test_comment_on_rule_anchor_rejects_unknown_rule` (422); `test_cannot_edit_others_comment`; `test_comment_after_revision_marks_outdated_line_anchor` (via `file_at`); tests fail against current code (routes absent). |

## 6. Gap 6: persisted quality runs with triage

| Piece | Design |
|---|---|
| Scope | Workbench "quality rules per project" are user-authored natural-language checks run by an LLM. Plato's equivalent today is deterministic `lint_pack`. This plan persists lint runs and triage and does not add LLM quality rules (decision Q1). |
| Table (migration `0018_pack_lint_run`) | `pack_lint_run`: `run_id`, `tenant_id`, `pack_id`, `revision` int null, `digest`, `source` (`draft \| version`), `version` null, `created_by`, `created_at`, `report` JSON (`PackLintReport`), `error_count`, `warning_count`. `pack_lint_triage`: `run_id`, `tenant_id`, `finding_key` (stable hash of `code`, `policy_id`, `rule_id`, `message`), `status` (`open \| accepted \| fixed \| wont_fix`), `note`, `by`, `at`; pk `(run_id, tenant_id, finding_key)`. Triage keyed by finding key, not index, so triage carries to the next run for the same finding (workbench keys by array index, which breaks when the list changes). |
| SDK | `jazzx_sdk/pack/lint_runs.py`: `LintRunStore` Protocol and `DbLintRunStore`; `run_lint(drafts, pack_id) -> run` builds the pack through `draft_pack` (existing) and `lint_pack` with the draft's policies. Same finding type; no change to `lint.py`. |
| Routes | `POST /packs/drafts/{pack_id}/lint-runs` (author; 201), `GET /packs/drafts/{pack_id}/lint-runs`, `GET /packs/lint-runs/{run_id}` (report plus per-finding triage merged), `PUT /packs/lint-runs/{run_id}/findings/{finding_key}` `{status, note}` (author or reviewer; 404; 422 bad status). |
| Review hook | Submitting a review runs and stores a lint run; error-level findings that are not triaged `accepted` or `wont_fix` refuse submit with 422 listing them (gap 2's 422). Warning level never blocks. Decision Q2: error findings blocking, or advisory only. |
| Client | `run_pack_lint`, `list_pack_lint_runs`, `get_pack_lint_run`, `triage_lint_finding`; contracts `PackLintRun`, `LintFindingState`. |
| Tests | `test_triage_survives_rerun_when_finding_unchanged` (fails: nothing persisted); `test_triage_key_changes_when_message_changes`; `test_submit_blocked_by_untriaged_error`; sqlite and Postgres. |

## 7. Gap 7: JTBDSet export and KH publish

| Piece | Design |
|---|---|
| SDK | `jazzx_sdk/pack/jtbdset_export.py`: `export_pack_jtbdset(pack, *, version, title=None) -> dict` reads the pack's `Policy` list (the loader the assessment already uses) and calls `export_jtbdset`. Round-trip with `import_jtbdset` is the contract. |
| Routes | `GET /packs/{pack_id}/{version}/jtbdset` (any reader, `application/json`, 404 unknown version, 422 when `export_jtbdset` refuses, e.g. an unclaimed product-scope policy, reason echoed). `GET /packs/drafts/{pack_id}/jtbdset` same for the draft (author). `POST /packs/{pack_id}/{version}/jtbdset/publish`: KH publish, see below. |
| KH publish | Needs the KH entity contract the workbench used (it links the published entity id on the version). Plato has a Knowledge Hub client (`fabric`); the call writes the artifact as a KH entity and records `{pack_id, version, kh_entity_id}`. Because `pack_version` is immutable, the link lives in a new table `pack_export_link` (migration `0018` or `0019`, added only if decision J1 is yes): `tenant_id`, `pack_id`, `version`, `kind`, `external_id`, `at`, `by`. Reviewer role required (a published artifact leaves the tenant). |
| Client | `export_jtbdset(pack_id, version)`, `export_draft_jtbdset(pack_id)`, `publish_jtbdset(pack_id, version)`; contract `JtbdSetArtifact` (`dict` passthrough plus `pack_id`, `version`). |
| Tests | `test_export_import_round_trip_preserves_rules` (fails: no route); `test_export_refuses_unclaimed_product_policy` (422 with the reason); `test_export_matches_workbench_fixture` using a JTBDSet fixture captured from the workbench, hand-written expected, not derived by the exporter. |

## 8. Gap 8: user and reviewer lookup

| Piece | Design |
|---|---|
| Seam | `jazzx_sdk/server/directory.py`: `UserDirectory` Protocol (`search(q, *, limit) -> list[DirectoryUser]`, `reviewers(*, limit)`), `DirectoryUser(user_id, email, name)`. Implementations: `GatewayDirectory(url, token_from_request)` (proxies the platform gateway `/auth/user`, filters by reviewer role as the workbench's `auth_gateway.fetch_reviewers` does) and `StaticDirectory(users)` for tests and local. Config: `PLATO_DIRECTORY_URL`; unset means `StaticDirectory` built from users seen in `pack_review` and `pack_draft` (best effort). No user table (D3). |
| Routes | `GET /users?q=&limit=` and `GET /reviewers`. Auth: any authenticated reader. Failure: gateway error is `502` with a reason; missing bearer token on a gateway directory is `401`. Response caps the list at a named `DIRECTORY_PAGE_LIMIT`. |
| Client | `search_users(q)`, `list_reviewers()`; contract `DirectoryUser`. |
| Tests | `test_reviewers_filtered_by_role` against a stub gateway; `test_gateway_error_is_502`; `test_static_directory_from_seen_users`. All new (routes absent). |

## 9. Review of chat-made proposals

Chat (gap 1) writes only per-rule proposals and, via `merge-rules`, draft files. Review treats both uniformly: a draft change by any actor produces a `pack_draft_event` with that actor, so a chat-made edit is reviewable in the diff and cannot be published without the review gate. The chat actor id is whatever `acting_user_id()` resolves for the turn (the human's); if the runtime session writes with a service id, events carry it, and review shows it. Ask for the runtime session: always set `actor_id` on its draft writes (a one-line contract, no code here).

## 10. Phased build order

| Phase | Scope | Migration | Done when |
|---|---|---|---|
| P1 | Gaps 2 + 3: `CallerIdentity.roles`, `authoring_roles`, `pack_review` + `pack_comment` tables, review store and routes (no diff yet), publish gate, `whoami` fields, client methods, `created_by_user_id`. | 0016 | The 3.5 tests green on sqlite and Postgres; the strict-publish test fails on the pre-change tree and passes after; `ruff` and `lint-imports` clean; CHANGELOG entry; `docs/DEPLOYMENT_ENV.md` regenerated if the roles env vars enter `BOOT_CONTRACT` (see 11). |
| P2 | Gap 4: events, diff, revert, `head_revision`, review diff route. | 0017 | Section 4 tests green; review stale check uses the revision; draft write and event atomicity test passes. |
| P3 | Gap 5: comment routes and client. | none | Section 5 tests green. |
| P4 | Gap 6: lint runs and triage, submit hook. | 0018 | Section 6 tests green; triage persists across a rerun. |
| P5 | Gap 7: export routes; KH publish if J1 yes. | 0019 only if J1 | Round trip and fixture tests green. |
| P6 | Gap 8: directory seam and routes. | none | Section 8 tests green. |
| Close | Full-range review (`REVIEW_UPSTREAM` the branch base), fixes, `done_` file moved with `git mv` from the `.scratch` root. | | Review clean. |

P1 is useful alone: the review loop works over HTTP before any UI. P4 depends on P1's submit route; P5 and P6 are independent of the rest after P1.

## 11. Cross-cutting checks (CLAUDE.md §8 and §9, applied up front)

| Check | Action |
|---|---|
| Route family | Every new route goes through `read_gate` or `write_gate` the way the sibling draft routes do; one test enumerates `app.routes` under `{prefix}/packs` and asserts each is gated (a family check, not a per-route one). |
| New env vars | `PLATO_REVIEWER_ROLE`, `PLATO_AUTHOR_ROLE`, `PLATO_DIRECTORY_URL`, `PLATO_REVIEW_ALLOW_SELF_APPROVAL`: declare in `BOOT_CONTRACT` and the rendered deployment doc; one assertion from running the app, not from the contract. |
| Named constants | Page and list limits, event page size, comment body cap, `DIRECTORY_PAGE_LIMIT`, role names: constants or config, no literals at use sites. |
| Client family | Each route lands with its client method and contract in the same phase; the client's route-coverage test (if present) must list the new routes. |
| Comments and prose | No archaeology; no plan filenames in code or commits; no em-dashes. New files carry the Author line. |
| Version | No version bump. Folds into the version in progress. |

## 12. Ownership

| Path | Owner |
|---|---|
| `jazzx_sdk/pack/review*.py`, `pack/diff.py`, `pack/lint_runs.py`, `pack/jtbdset_export.py`, `pack/draft_db.py` (events), `pipelines/jtbdset.py`, `pack/lint.py` | policy session |
| `plato/api/pack_review.py`, `plato/api/packs.py` (publish gate, draft routes), `plato/api/authoring.py`, `plato/migrations/versions/0016..0019` | policy session |
| `jazzx_sdk/identity.py` (`roles`), `jazzx_sdk/server/whoami.py`, `server/authoring_roles.py`, `server/directory.py` | policy session for these changes; `identity.py` is shared, tell the runtime session when P1 lands |
| `jazzx_plato_client/` methods and contracts for the above | policy session (they land with the routes); client packaging and release stay runtime's |
| Boot contract, deployment doc, releases | runtime session |
| Authoring chat mount and its use of draft actor ids | runtime session |

## 13. Decisions still needed

| # | Question | Recommendation |
|---|---|---|
| R1 | One open review per pack (partial unique index), or several concurrent? | One. Single author per pack (D5); a second review would race on the same draft. |
| R2 | Reviewer assigned at submit (workbench) or any reviewer may decide? | Optional assignee; unassigned reviews show in every reviewer's inbox. |
| R3 | Does direct archive upload `POST /packs` also need an approved review in strict? | No: it is the operator path for externally authored packs; document it. Say if it should be gated. |
| R4 | Self-approval: allowed locally, refused deployed? | Yes, the toggle in section 2. |
| H1 | Retention for `pack_draft_event` before/after text. | Keep all while a draft is open; on `discard` or after publish keep hashes and drop text after N days (config). Or keep forever, drafts are small. |
| C2 | Re-anchor line comments across edits server-side? | No: carry `revision`, show outdated; rule anchors cover the structured case. |
| Q1 | Gap 6 scope: persist lint only, or also build LLM quality rules like the workbench's? | Lint only now; LLM rules are a separate plan if the workbench team uses them. |
| Q2 | Do untriaged lint errors block review submission? | Yes in deployed, advisory locally. |
| J1 | Is KH publish of a JTBDSet wanted at all (needs the KH entity contract and a link table), or export-only? | Export-only until a consumer names the KH contract. |
| M1 | Is the gateway's role claim name for reviewers `reviewer`, and is there an `author` role at all? | Confirm with the platform team; if no `author` role exists, treat any authenticated caller as author. |
| D4 | MACER testing. | Still open, out of scope. |

## 14. What would make this wrong

- If the gateway does not forward `X-User-Roles` to Plato, D3 fails and a membership table returns; M1 checks this first, before P1.
- If several authors edit one pack (D5 reversed), the digest and revision pins make stale approvals correct but the draft itself still loses updates, so gap 10 moves to P1 and `TODO(draft-merge-lost-update)` stops being deferrable.
- If the workbench team keeps its own project and git model, D1 fails and this surface has no consumer.
