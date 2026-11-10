# Review of the "SDK and Plato Roadmap" deck: accuracy, completeness, emphasis

Deck: https://claude.ai/artifact/XzCVGWdHbdyTyyUGNWH18g (Slides artifact, version 1794263689-1dbd; slides are `project/slides/<id>.html`, order in `project/deck.json`). Reviewed 2026-11-09 by opus-xrepo for Claude Desktop to apply. This covers only the reviewer's own findings; the viewer comments on the deck are handled separately.

Method: read all 26 slides (text and speaker notes, not rendered), then spot-checked claims against japes `origin/main` (SDK 2.7.0, Plato 0.3.0) and against our own repo surveys. "Verified" means checked in code or git; "Not verified" means taken from the deck.

## Verdict

Strong on architecture (three layers, agent versus pipeline, adoption phases) and honest about maturity. It overstates adoption in two places, is stale on SAIG readiness, and leaves out the evidence a decision-maker needs (who is on which version, what blocks measurement). The most decision-relevant fact, that most of Recipes and the Container are pending QA and unmeasured, shows only slide by slide, and the staffing "Request" is the last slide with nothing tying it to that gap.

## Corrections to make (slide id, text to find, evidence, proposed edit)

1. **capabilities (speaker notes and status pills) and lib (Who it is for): production use by Macer and Juno.** Split into two claims.
   - **Sandbox and Azure used by Macer: keep.** JAPES (Jazzx Platform Extension Service) was created so Macer could run inside the platform without affecting the rest of it, because the effects of running the OpenAI Agents SDK there were not known (user, 2026-11-09). Macer's use of the SDK's queue and runtime pieces is therefore the original purpose, and it matches what its `main` takes today (queue handler types). An earlier version of this note flagged the pill as unverified; that flag is withdrawn. "Sandbox" in the strict sense (a tool and code sandbox) was not checked.
   - **Agent execution used by Macer and Juno: fix.** Find: notes "Knowledge Fabric with its connectors and agent execution are in production, used by Jazz Assistant, Macer and Juno"; lib "Macer, Juno, Knowledge Studio: in production, in part". Evidence: Macer's `main` pins japes 2.4.9 and keeps its own run kit, retries and input filter locally (survey 2026-10-22, pin re-read 2026-11-09; the SDK run kit adoption is slice 2 of its migration plan and exists only on its `platform_v2` branch). As of 2026-11-06 one Juno module imported the SDK. The deck's own services slide says Macer is "SDK for storage" and "Builder Studio and Juno" is "Existing platform", so the slides disagree with each other.
   - Edit: name verified users per capability: Jazz Assistant (agent execution through the interactive agent), Macer (Knowledge Hub client, queue and runtime), Knowledge Studio (pricing, tracing, prompts; pinned 2.6.4). Do not list Macer or Juno under agent execution until the run kit adoption lands.
2. **lib (speaker notes): "through the LLM Gateway".**
   - Find: "...Anthropic Claude models, with Gemini also supported, through the LLM Gateway, all traced the same way".
   - Evidence: `origin/main` has no AI Gateway code (0 files). The gateway change is japes PR #108, being carried into 2.7.1.
   - Edit: "directly to each provider today; the AI Gateway path arrives with 2.7.1".
3. **ag-interactive (speaker notes): "Jazz Assistant runs on it".**
   - Find: "Jazz Assistant runs on it, and the Unified Assistant Framework builds on it".
   - Evidence: jazzx-assistant `origin/main` (pinned japes 2.6.6) imports the SDK's interactive agent layer and streaming but nothing from `jazzx_sdk.pipelines`. Its chat pipeline migration is jazzx-assistant PR #31, open since 2026-10-14, stale (pinned japes 2.6.1, conflicts with `main`).
   - Edit: say the interactive agent is in production through Jazz Assistant, and Question to Answer is pending QA with PR #31 as the path. The services slide row "Jazz Assistant: Built on SDK, Chat pipeline (Consolidate)" is consistent with that.
4. **needs and road: SAIG readiness is stale.**
   - Find: needs "Capabilities still to build: ... Releases with rollback, audit trail, tenant isolation"; road "Plato is ready for SAIG companies when: Releases are versioned and can be rolled back; Every run is audited and tenants are isolated".
   - Evidence (CHANGELOG, 2.7.0): tenant-keyed stores, a tenant directory and a strong guard shipped; audit events and pack rollback exist; 2.7.1 (not released) adds guidance approval by change class with forum approval and an audit event per transition.
   - Edit: move these to "built, pending QA", add what remains (QA of tenant isolation, a stable plato-client, a support owner), and mark the 2.7.1 governance item "in progress".
5. **Knowledge Studio.** No change needed. An earlier concern that "Knowledge Studio replaces Policy Workbench" conflicted with our records was wrong: Knowledge Studio is the renamed policy-workbench (user confirmed).

## What is missing (add or fold in)

- **An adopters-by-version slide.** As of 2026-11-09: Macer 2.4.9; Knowledge Studio 2.6.4; jazzx-assistant 2.6.6 on `main` plus an open chat-pipeline PR pinned to 2.6.1; jaci re-locked on 2.6.8 (2026-11-03); Juno one module. "Each moves at its own pace" hides this gap, which is the largest real adoption risk. Cite the date.
- **The governance and isolation gate for SAIG companies** as one readiness slide: tenant isolation, audit, release versioning and rollback, approval by change class with forum approval (2.7.1). It is the roadmap's own "ready when" list.
- **Measurement ownership.** Nearly every agent slide ends "accuracy measurement pending" with no owner, baseline or acceptance number. Add the owner and the blocker (typed spend approval, a subject-expert answer key) per item.
- **Breaking changes for hosts in 2.7.0:** five tenant-keyed stores take a required tenant id and need the upgrade step before deploy.
- **Cross-repo alignment:** every sibling repo moved to the AI Gateway through the shared `common` module this week; japes carries it in 2.7.1. A one-line mention under the Library.
- **Macer start needs nothing on Macer's side:** the process launcher polls by default, and the pack author supplies the start variables. This is on pipe-proc only in passing and is the point the Macer team most needs.
- **No dates or spend.** The deck says phases follow dependencies; if the audience is leadership, add the next two milestones with owners.

## Verified as accurate

- Version stamp "SDK 2.7.0, Plato 0.3.0" matches `main`.
- All 19 plato-client method names on the client slide exist (`chat`, `stream_chat`, `create_session`, `skills`, `invoke_skill`, `assistant_openapi`, `publish_pack`, `activate_pack`, `assess`, `upload_document`, `classify_document`, `submit_case_run`, `start_process`, `start_policy_to_pack`, `decide_proposal`, `create_experiment`, `submit_feedback`, `health`, `server_info`, `cost_stats`), and the constructor is `PlatoClient(base_url, *, tenant_id, ...)`.
- The process launcher statement (a pipeline step starts a Flowable process, messages it and waits; built in 2.7.0; pack-declared, permission-checked) matches the code.
- The mode count is internally consistent: 13 modes, 7 runnable.

## Not verified

"About half of Acra jobs get code"; the YETI and reference-case benchmark status; the status colors for Plato items; the pipeline names `Policy to Pack` and `Documents to Verified Fields` (a grep of the catalog file did not find their ids; they may be registered elsewhere); and everything visual (nothing was rendered).
