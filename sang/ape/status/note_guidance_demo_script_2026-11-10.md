# Demo script: guidance change classes, forum approval and the audit trail (local Plato)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Local data only: no loan data, no provider calls, no spend. Verified step by step with HTTP calls against the running Plato (not in a browser).

## Setup (done 2026-11-10)

- Plato `http://localhost:8000` (pid listed by `scripts/local/plato_worktree.sh status`) from `/Users/sangit/src/japes-plato`, pinned at v2.7.1 `d71771ae`, started with `PLATO_REVIEW_ALLOW_SELF_APPROVAL=0` (so self-approval is refused, as in a deployed posture), `JAPES_RUN_BUDGET_USD=7`, `JAPES_PAGE_CACHE_DIR` as in the environment note. No run was in flight (turn_run and extraction runs: none running).
- The local database went from 0036 to 0042 (migrations 0037 to 0042). Backup before: `/private/tmp/claude-506/-Users-sangit-src-japes/9b46cfbd-a7e0-40cd-a2ef-9944b5ce3b4f/scratchpad/japes_plato_db_before_0042.dump` (custom format, pg_dump 17). To roll back: stop Plato, `dropdb japes_plato_db`, `createdb japes_plato_db`, `/opt/homebrew/opt/postgresql@17/bin/pg_restore -h localhost -p 55432 -d japes_plato_db <dump>`, restart the previous rev (`scripts/local/plato_worktree.sh restart e81282cf`).
- Seeded by `sang/ape/local/demo_guidance_setup.py` plus a fresh material and widening draft: packs `demo-guidance-lending` (governance file with a certification forum of two members) and `demo-guidance-open` (no governance file). Each has a deployed first version, an approved minor change, and drafts.

## People (paste into the page's identity box, `x-user-id`)

| Role | Name | Id |
|---|---|---|
| author | alice | `821c3f34-36fe-51ef-a33d-e9f47280600a` |
| owner (any reviewer) | bob | `2d88ba29-ea65-587c-aa40-c7833769c259` |
| forum member | carol | `d90996b3-ab42-53a1-a312-8a635a834bec` |
| forum member | dave | `78ea07b3-2eae-523b-85f2-348f8479d407` |
| not in the forum | frank | `9a09d0a2-a2cb-56e6-bead-f522c58ea19a` |

## Steps (Guidance page: `http://localhost:8000/api/v1/guidance/ui`, pack id `demo-guidance-lending` unless stated)

1. Load the pack. Expect: a deployed first version, an approved minor change (class `minor_behavioral`), and drafts (a `material_behavioral` one "Treat a lease under eighteen months..." and a `boundary_widening` one "Loosen the minimum DSCR to 1.15..."). The approved minor change was approved by the owner alone: open it, its audit has one `approve` event, step `owner`.
2. Self-approval refused: identity alice, open the material draft, Approve. Expect 409 `self_approval` (the author cannot approve; the posture is off).
3. Two-step approval: identity bob (owner), Approve the material draft. Expect 200 and the asset still `draft`, with one approval (`owner`) recorded.
4. Not a forum member: identity frank, Approve. Expect 409 `not_forum_member` (names the forum `certification-board`). Identity bob again: 409 `same_approver`.
5. Forum approval: identity carol, Approve. Expect `approved`, two approvals (owner, then certification_forum from `certification-board`).
6. Audit table of that asset: two `approve` events, newest first: carol `certification_forum` `certification-board`, bob `owner`; both `change_class material_behavioral`.
7. Widening change: identity bob on the `boundary_widening` draft, Approve: 409 `not_forum_member` (the owner alone never approves a widening); identity carol: `approved` in one step, audit shows `certification_forum`.
8. No-forum pack: pack id `demo-guidance-open`, material draft, identity bob, Approve: 409 `no_forum_declared` (a pack with no forum cannot approve a material or widening change; its minor change was approved by the owner alone).
9. Deploy any approved asset (identity bob, "deploy without a validator" ticked: no model is wired locally): the audit gains a `publish` event.

## Not shown or not checked

- Browser rendering of the page was not checked by me (HTTP only); sonnet-ui built it and has not browser-checked it either.
- No LLM validator runs (deploy needs "deploy without a validator" locally). The gate's tests (regression, gold, edge, cell recertification) are recorded, not run.
- Re-running the setup script creates new assets and fails at the second deploy of a near-duplicate; reset by dropping the two demo packs' guidance rows or re-seeding the database from the dump.
