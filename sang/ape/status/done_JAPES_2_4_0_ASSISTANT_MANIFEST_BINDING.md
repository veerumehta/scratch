# Done: Assistant Manifest Binding

Author: Virendra Mehta · Updated 2026-08-01
Repo: japes · Plan: docs/plans/plan_JAPES_2_4_0_ASSISTANT_MANIFEST_BINDING.md

**All four phases verified against the plan's own named acceptance tests, not just the code
existing.** Phases 2-3 matched spec exactly on first check. Phase 1's apparent gap turned out to
be a false alarm — corrected below. Phase 4 had one real, unintentional gap (stream/conversation
surface defaults contradicting the plan's explicit instructions) — fixed and tested. No live
consumer of this feature exists yet in either repo (checked directly), so the fix carries zero
regression risk to anything already running on it.

## Verified done, matching spec

- **Phase 2 (router as a declared field)** — `jazzx_sdk/agents/interactive/router.py`,
  `spec.router` field. All 4 named acceptance tests exist and pass:
  `test_default_llm_router_is_noop`, `test_unknown_router_raises_at_construction`,
  `test_intent_first_narrows_exposed_tools`, `test_intent_first_none_falls_back_to_full_catalog`.
- **Phase 3 (stock scope guardrail)** — `jazzx_sdk/agents/interactive/scope.py`,
  `_run_guardrails`'s widened `str | Refusal | None` return. All 6 named acceptance tests exist
  and pass: `test_scope_guardrail_blocks_out_of_scope_class`,
  `test_scope_guardrail_admits_in_scope_class`, `test_bind_spec_attaches_scope_guardrail`,
  `test_bind_spec_does_not_double_register_declared_guardrail`,
  `test_run_guardrails_accepts_refusal_return`, `test_run_guardrails_str_return_unchanged`.
  One **conscious, already-documented** deviation: the guardrail is a deterministic keyword match
  against `out_of_scope_action_classes`, not the LLM-classifier pattern the plan describes
  ("Building Agents using jazzx-sdk" §Shape A) — the module's own docstring states why (`bind_spec`
  has no LLM manager in hand at spec-binding time) and this was a deliberate call made while
  building it, not an oversight.
- **Exit criterion** — demonstrated against a new fixture (`tests/fixtures/manifest_binding/`, an
  internal "docs-assistant") rather than `examples/loan_assistant/` as the plan asked for. Also a
  conscious deviation (reasoned through when built): `examples/loan_assistant/` exists and could
  still be used to re-demonstrate this later, but the exit criterion itself is met either way.

## Phase 1's "narrowing to empty" — corrected, not actually a gap

An earlier pass of this file flagged a missing `test_bind_spec_refuses_narrowing_to_empty` as a
real bug. **That was wrong, and worth recording precisely because it looked exactly right on
first read.** Re-derived the logic directly: `narrowed_skills` (`profile.skills ∩
manifest.allowed_skills`) can only be empty, given a non-empty `profile.skills`, if *every* skill
in `profile.skills` is absent from `manifest.allowed_skills` — which is exactly the definition of
`unauthorized` (`profile.skills - manifest.allowed_skills`) being non-empty. `bind_spec()` already
raises on `unauthorized` *before* `narrowed_skills` is ever computed. Brute-forced every
skill-set combination over a small universe to confirm no counterexample exists — none does. The
scenario the plan's Phase 1 text worries about is a logical subset of the widening check already
in place; there is no code path where it fires independently, so there is nothing for a dedicated
test to exercise. The plan's own two-step description (raise on widening, separately raise on
empty intersection) named a redundant second check; the actual implementation correctly omitted it
rather than testing dead code.

## Real gap found and fixed (Phase 4)

Checked `_SURFACE_DEFAULTS` in `spec_binding.py` directly against the plan's table and its two
explicit prose rules:

1. **`stream: True` is set for `WORKSPACE`/`ASSISTANT`.** The plan's own table only lists
   `conversation` and `stream_tool_events` as defaulted fields, and says outright: "`spec.stream`
   is advisory... Do not set `stream=True` here" (since `respond_stream()` cannot produce
   structured output, and setting `stream=True` by default conflicts with that). The implemented
   table sets `"stream": True` anyway for both interactive surfaces — a direct contradiction of
   the explicit instruction, not a design choice stated anywhere.
2. **`conversation: True` is set unconditionally, never gated on a `store`.** The plan: "`bind_spec`
   sets `conversation=True` for `WORKSPACE`/`ASSISTANT` only when a store is being supplied, and
   otherwise leaves it False and logs at warning naming both missing pieces." `bind_spec()`'s
   actual signature takes no `store` parameter at all, and `_apply_surface_defaults` sets
   `conversation: True` regardless. `_conversation_active()` (`agent.py:334`) still gracefully
   returns `False` at runtime when no store is wired, so this isn't a crash — it's the exact
   "reads as if memory is on" silent-misconfiguration risk the plan named, just not prevented.

Neither `test_conversation_not_enabled_without_store` nor `test_surface_defaults_never_set_stream`
(both plan-named) existed in `tests/test_assistant_manifest_binding.py` before this fix.

**Fixed 2026-08-01.** `_SURFACE_DEFAULTS` no longer defaults `stream` at all for any surface.
`_apply_surface_defaults()` gained a `store: Any = None` parameter: `conversation` is set True for
WORKSPACE/ASSISTANT only when a store is actually passed through; otherwise it logs a warning
naming both requirements (`ConversationStore` at bind time, `session_id` per `respond()` call)
and leaves the field alone. `bind_spec()`/`build_from_manifest()` both gained a `store=` parameter
threading through to this check — `build_from_manifest` reads it from `**extra` (without popping
it) so the same store object also still reaches `InteractiveAgent.__init__` as before, unaffected.
Existing callers that never pass `store=` see the corrected (safer) default: `conversation` stays
False rather than silently-wrong-True. Added the plan's two missing named tests plus a third
(`test_conversation_enabled_when_a_store_is_supplied`) proving the positive case, and confirmed
`test_interactive_agent.py`'s 51-test regression surface stays green.

## Why the real gap (Phase 4) went unnoticed

This is exactly the failure mode the plan spent the most words warning about: a spec that reads
as memory-enabled but isn't. Not a functional crash — `_conversation_active()` still gracefully
returns `False` at runtime with no store wired, so no caller was visibly broken — which is exactly
why it went unnoticed with no status file forcing a phase-by-phase reconciliation against the
plan's own acceptance tests, until this pass checked the plan's *named but never-written* tests
against what actually exists.

## Commit note

`c417402` (which introduced `spec_binding.py`) is already pushed to `origin/dev`, so this fix is
a new commit, not an amend — per the standing "never amend a pushed commit" rule.
