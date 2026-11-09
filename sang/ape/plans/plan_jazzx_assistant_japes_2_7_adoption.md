# jazzx-assistant onto japes 2.7: pin, chat pipeline, processes

Author: Virendra Mehta

Source: read-only survey of `/Users/sangit/src/jazzx-assistant` `origin/main` on 2026-11-09 (imports and the pin by `git grep` and `git show`; tests not run) against japes 2.7.0 (`main` 2c8274b0; the 2.7 tree is `/Users/sangit/src/japes-v27`). This plan is for the jazzx-assistant team to execute in their repo; japes sessions never edit it. Contact for that repo: Poddar (see the team contacts note). `[V]` checked in code, `[U]` not verified.

## Status and modifications

How to use this section: the plan author may read and update it; implementers append one dated line per slice. Newest line last.

- 2026-11-09 drafted by opus-xrepo. Nothing run, nothing sent to the team.

## State

- `origin/main` pins japes at `e5c7128e` (2.6.6, the 2.6.6 `main` squash) through `[tool.uv.sources]` [V]. Their local checkout was on `dev` with an older pin (`ae974845`, 2.5.7); the team's branch state is what matters, not that checkout.
- Branch `feat/BSD-5632-register-workspace-claim` pins japes at `9c6431d1`, a commit that is not on japes `main`, and imports `jazzx_sdk.workspace_claim`, a module that exists only in an open japes PR (#101) [V]. It must not merge while pinned to a non-`main` commit. Branch `ai-gateway-migration` exists too (same AI Gateway change as on japes, macer and the others); a recent commit bumps japes to a gateway-branch head (`f129712`), also not on `main`.
- 28 files under `src/` import `jazzx_sdk`; none imports `jazzx_sdk.pipelines` [V]. What it uses: `jazzx_sdk.streaming`, `fabric`, `agents` and `agents.interactive` (`InteractiveAgent`, `InteractiveAgentSpec.from_dir`, `CompositeAgentHooks`, `SessionReaper`), `queue`, `handlers`, `server`, `clients`, `tools`, `llm.cost`. So it runs on the SDK's interactive agent layer, not on the SDK's chat pipeline package (`jazzx_sdk/pipelines/chat/`: engine, compose, preliminary, lifecycle). That is the adoption this plan is about.
- The chat pipeline migration already exists as a PR: jazzx-assistant PR #31 "Migration to chat pipelines in japes", branch `JAPES-V2`, one commit (`2882dc8`, 2026-10-14), 66 files, +6004 / -3165, open, review required, one review and one comment on it (ours; sent 2026-10-14), not merged [V via `gh`, read-only]. Its branch imports `jazzx_sdk.pipelines.chat` (six imports), `jazzx_sdk.runs`, `jazzx_sdk.conductor` and `agents.interactive.grounded` [V]. It is pinned to japes `6b2e9b88` (2.6.1) and has not moved in four weeks: 12 commits behind `main`, one ahead, and it conflicts with `main` when merged (`git merge-tree`) [V]. Of the 19 names it imports from the chat pipeline, 8 resolve at 2.7.1 by name (`ChatTurn`, `ChatTurnSpec`, `GateDecision`, `GroundPlan`, `DeadlinePolicy`, `DEADLINE_EXCEEDED`, `ground_step`, `ReconcileOutcome`); the rest were not found by my search and are not verified [U] (`open_durable_run_database` is the assistant's own, in `persistence/runs.py`).
- It already has its own two-stage answer (a quick findings-based reply before the full one; commits `da34577`, `2a9db89` on 2026-10-31 and 2026-11-03) [V from the log; implementation not read].
- Its assistant and kernel clients build requests with raw httpx and bypass the SDK's header machinery, so a forwarded workspace does not reach kernel from them (named as the known gap in japes PR #101; tracked on their side as BSD-5816) [V from the PR text].

## What 2.7.0 gives it (read `docs/status/CHANGELOG.md` from 2.6.7 to 2.7.0 first)

- Scope claims: `jazzx_sdk/scope_claims.py` (since 2.6.7) carries a host-declared claim from a message or header to named clients. The SDK names no claim; the host declares each [V].
- Chat pipeline: `jazzx_sdk/pipelines/chat/` with a preliminary-answer step whose reply says what follows (`compose.py`, `preliminary.py`) and a scope gate with its own model (`gate.model`) [V from the CHANGELOG entries; code not re-read].
- Processes: a `ProcessSpec` a pack declares, a launcher with Flowable and conductor backends, and process skills an assistant can call (`jazzx_sdk/processes/tools.py`: a start tool and a status tool per declared process [V]; no cancel tool there). The pack author owns the start variables; see `docs/status/note_process_integration_checklist.md` in japes.
- Host-breaking items: five tenant-keyed stores take a required `tenant_id` (only if the assistant uses the SDK's host-owned stores [U]); pipeline ids were renamed with one deprecation warning per old id.
- Reasoning deltas from Anthropic and Gemini native models, if the assistant ever shows reasoning.

## Slices (lowest risk first; each ends with their own suite green)

1. **Pin to 2.7.0.** `rev` to the japes `main` commit `2c8274b0`, relock, run their suite and import-contract tests. A pin is a `main` commit or a tag, never a branch head or a plato sha.
2. **Workspace claim, host-declared.** Declare the claim in the assistant at startup with the SDK's machinery instead of importing a japes module that is not on `main`: a `ScopeClaim` named `sub_tenant_id`, header `x-sub-tenant-id`, kind `uuid`, client `kernel`, sources `message` and `header`, passed to `register_scope_claims`. Three lines; their branch's test stays. Alternative: wait for japes to ship a preset, which is undecided.
3. **Kernel and assistant clients onto the SDK header path.** The gap named in the PR: move their raw-httpx calls to the SDK clients (or wrap their request headers with `with_scope_claims(provider, "kernel")`) so the claim reaches kernel; this is the actual fix for BSD-5816.
4. **Chat pipeline: PR #31 is the vehicle.** It is stale (2.6.1 pin, conflicts with `main`, which has since gained the fast answer and a pin bump). Rebase or redo it on `main` after slice 1, moving its pin to the 2.7.0 `main` commit, and re-resolve every name it imports from `jazzx_sdk.pipelines.chat`. Then compare their two-stage answer with `pipelines/chat/preliminary.py` and `compose.py`; adopt the SDK step where behavior matches, keep theirs where it differs and list the difference; adopt `gate.model` for the scope gate if they use a topic gate. Parity: their chat tests plus a recorded turn.
5. **AI Gateway.** Land the pin bump (slice 1) first; then their `ai-gateway-migration` against `common.core.ai_gateway`. Do not pin a gateway-branch head.
6. **Starting processes.** Use the pack's `process` declaration and the SDK's process skills to start and follow a Macer run from a conversation; the caller (the pack) provides the start values. Needs the pack author's answers from the checklist; no SDK change.
7. **Tenancy.** Only if the assistant uses the SDK's host-owned stores: `upgrade_tenant_keys` before deploy and `check_tenant_keys` in CI. Verify first whether it does [U].

Slices 1 and 2 are independent of the rest; 3 and 4 are the substance; 5 and 6 follow.

## Stays in the assistant

Grounding, ingress and websocket session handling, persistence, its UI contracts, its status vocabulary and its progress relay; the two-stage answer's wording and prompts unless slice 4 shows the SDK step matches.

## Decisions for the user

1. Declare the workspace claim in the assistant (slice 2), or ship a preset in the SDK (japes PR #101 as written puts `jazzx_sdk/workspace_claim.py` in the SDK root, against the SDK's own "names no claim" rule; if wanted, it belongs beside the kernel client in `jazzx_sdk/clients/`).
2. Whether the team finishes PR #31 (the chat pipeline migration, rebased onto 2.7.0), or closes it and keeps its own pipeline on the interactive agent layer, taking only slices 1 to 3, 5 and 6.

## Unverified

Their test results on any pin; whether they use host-owned stores; how their two-stage answer is built; what `anthropic`/`kernel` clients they use besides the two raw-httpx ones; whether `pipelines/chat` fits their grounding; branch states other than the two named.
