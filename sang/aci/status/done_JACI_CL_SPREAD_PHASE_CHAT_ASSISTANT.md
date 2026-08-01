# Done: Activate Jazz on the Live Spread Phase, via the Chat Pipeline and Guidance Hook

Author: Virendra Mehta (via session) · Completed 2026-07-27
Repo: jaci · Landed: dev commits `c1bd7d3` (Phase 1), `9c21229` (Phase 2), `46f960c` (Phase 3)
Plan: docs/plans/plan_JACI_CL_SPREAD_PHASE_CHAT_ASSISTANT.md (superseded by this file)

All 3 phases landed, back-to-back, no deviations from the plan.

## What shipped

- `credit_outcome.live_spread_outcome(spread, loan_id=...)` / `seed_live_spread_fabric(...)` — the
  live-grounding counterpart to `yeti_assessment`/`seed_yeti_fabric`: a minimal `Outcome` carrying
  computed metrics only (leverage, current ratio, EBITDA, margins) from *this session's* spread,
  no covenant/decision context (an arbitrary live spread has no YETI-ABL-specific covenant
  policy). Same mechanism (`Outcome` → `local_fabric` → `fabric.canonical.find`) as the existing
  curated path, different source.
- `_get_jazz_response` now prefers `st.session_state["ci_spread_result"]` (the live spread) when
  present, falling back to the curated YETI fixture exactly as before otherwise.
- Jazz's turn now routes through `jazzx_sdk.agents.interactive.chat` (`run_chat_turn`/
  `build_chat_pipeline`/`build_chat_components`) instead of calling `agent.respond()` directly —
  no escalation in v1, every question still answers directly.
- `guidance_pack_id="ci-spread-core"` wired onto the spec, connecting Jazz to the japes guidance-
  injection hook (`plan_JAPES_2_3_0_GUIDANCE_INJECTION_HOOK.md` Phase 1) for the first time.
- `credit_outcome.attach_demo_guidance(fabric)` seeds one deployed `GuidanceAsset` (a field-exam/
  borrowing-base caveat) into an `InProcessGuidanceStore`, overriding `local_fabric`'s own default
  `RagGuidanceStore` (routing a fixed demo instruction through the mock's embedding pipeline is
  unnecessary fragility). First time `fabric.guidance` produces a visible effect anywhere in jaci.

## Acceptance criteria — verified

- Phase 1: with a live spread in session state, Jazz's grounding uses that spread's real computed
  metrics (verified against a hand-built fixture: leverage 1.2x, current ratio 2.0x, EBITDA 250 —
  the same numbers independently verified in this session's chart-of-accounts work); with no live
  spread, behavior is unchanged (same fixture path, same `Outcome`, same knowledge bindings).
- Phase 2: the chat-routed turn returns the identical `InteractiveResponse` shape (answer, sources,
  conversation_id) as calling `agent.respond()` directly would — `chat.py`'s own direct-route-
  equals-respond equivalence is verified at the japes level
  (`test_interactive_chat.py::test_direct_route_runs_the_agent`); this plan's own test proves the
  *specific* combination (chat.py + guidance_pack_id + live-spread-seeded fabric) works together.
- Phase 3: a leverage/borrowing-base question returns exactly one `GuidanceRef` and the rendered
  guidance text appears in the captured system prompt; a question with no attached guidance still
  returns `guidance_refs == []`, matching pre-Phase-3 behavior exactly.

## A design correction made mid-flight

The plan assumed `local_fabric`'s mock-backed config would leave `fabric.guidance` as `None`
(no RAG/KH collection configured). Checked directly before writing Phase 3's code: `local_fabric`
actually builds a real `RagGuidanceStore` by default (its `FabricConfig.guidance_collection_id`
has a non-empty default, and the mock RAG backing is non-`None`). The override in
`attach_demo_guidance` is still correct and necessary — a fixed demo seed is more reliably tested
via `InProcessGuidanceStore`'s deterministic token-overlap search than by putting it through the
mock's embedding-search pipeline — but the documented *reason* for the override was wrong until
corrected. Also incidentally confirmed: a `RagGuidanceStore` with nothing ever `put()` into it
degrades to an empty search result, not an error — `test_no_guidance_attached_means_no_guidance_
refs_by_default` exercises exactly this path.

## Notes for next time

- Escalation to `credit_analysis`/a reasoner, per-line citations from `SpreadPackage`/
  `SpreadLineItem` provenance (vs. today's `Outcome`-level summary), and reconciling Jazz's
  existing feedback capture (`InProcessFeedbackStore` → `optimize_prompt`) with `fabric.guidance`
  all remain explicitly out of scope, as the plan said.
- The mapping-correction learning loop (FR-MAP-6 / Stage 5 of `CommercialLendingwithYETIwithLearning.pdf`)
  is a separate, not-yet-scoped plan — targets `LineVocabulary`/chart-of-accounts resolution, not Jazz.
- CRE (`cre_underwriting`) still doesn't have the spread/credit-analysis pipeline split C&I already
  has — a real, separate gap named in this conversation, not touched here.
