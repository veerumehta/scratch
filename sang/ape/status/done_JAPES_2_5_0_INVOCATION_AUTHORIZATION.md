# Done: Invocation Authorization (per-hop InvocationContext cascade)

Author: Virendra Mehta · Completed 2026-07-30
Repo: japes · Landed: dev `f50a498` (unpushed, no version bump)
Plan: docs/plans/plan_JAPES_2_5_0_INVOCATION_AUTHORIZATION.md (superseded by this file)

All 4 phases landed. This plan's own grounding notes were unusually accurate (every claim I
spot-checked before starting — the exact `ResilientRunner` line number, all four existing
`check_action` callers' lazy-import convention, the `authority/` vs `governance` naming rationale —
matched current code precisely). Two real corrections were still found during implementation,
both from actually trying to build against the plan's literal text rather than trusting the prose.

## Correction 1: `TraceStepContextHelper` doesn't fit `check_hop`'s actual shape

The plan says a denial "emits a `TraceStep` via `TraceStepContextHelper` before returning."
Checked directly: `TraceStepContextHelper.__init__` takes a *live* `CanonicalTrace` instance, and
its only methods (`set_version_bundle`/`set_ipdv_context`/`set_domain_context`) attach metadata to
a `step_id` **already present** in that trace — there is no "create a new TraceStep" method, and
`check_hop` has no live trace object to construct one with (`InvocationContext` carries only a
`trace_id` string, by design — the SDK shouldn't hold a mutable trace reference across a
`ContextVar` boundary). Grepped every existing `check_action` caller
(`agents/document/agent.py`, `automation/governed.py`, `modes/operational/governor.py`,
`statemachine/engine.py`): **none of them use `TraceStepContextHelper` either** — they just return
the `Refusal` to their own caller. `check_hop` does the same, and populates `Refusal.trace_id`
(a field every `Refusal` already carries) from the ambient context — the real, already-existing
correlation mechanism, not a new one invented for this plan.

## Correction 2: a build-time refusal, not a runtime "tool result"

Phase 3 says "A refused hop returns the `Refusal` to the parent as a tool result, not an
exception." Skill/tool authorization happens while **building** the parent agent's tool list
(`_build_parent_tools`), before any Agents-SDK run starts — there is no in-flight tool call to
return a result from at that point. Making a refusal show up as an actual runtime tool-call output
would mean wrapping the Agents SDK's own `Tool`/`as_tool` internals to intercept invocation, a
materially bigger and riskier change than this pass should take on. Implemented instead as
**build-time exclusion**: a refused skill or tool is simply left out of the tool list the parent
model is ever shown (least-privilege — its existence isn't even hinted at), which the four
existing `check_action` callers' own "return the Refusal, let the caller decide" precedent
supports at least as directly as an in-band tool result would.

## What shipped

- **Phase 1** (`jazzx_sdk/authority/context.py`): `InvocationContext` (principal/actor_class/
  permission_scope/human_initiated/matrix/binding/overlay/execution_profile/trace_id/depth) and
  `PermissionScope` (`resource_selectors`/`denied_selectors`, exact+prefix `admits()`, `narrow()`
  as a semantically-correct intersection — not a raw list-intersection, which would wrongly
  produce nothing when a selector is covered by a broader prefix already held). `descend()` for a
  narrower child hop. Propagation mirrors `jazzx_sdk.handlers`' own `ContextVar` pattern exactly
  (`set_`/`get_`/`require_`/`clear_`/`reset_invocation_context`). Wired into `ResilientRunner.
  create_run`/`execute` at the same anchor as `capture_identity_headers`/`set_propagated_headers`
  (`TurnRun.invocation_context`, new field) — the juno #242 async-dispatch-boundary fix, generalized
  from identity to authorization.
- **Phase 2** (`check_hop`/`admit_hop`, same file): `permission_scope.admits()` always runs first
  (`AUTHORITY_EXCEEDED` on failure); delegates to the existing `check_action` — never
  reimplemented — when a `cell_id` and a matrix are both present; with no matrix, returns an
  `EffectiveAuthority` at the safest default ceiling (`AutonomyLevel.L0_ASSIST`) with
  `contributing_layers={"permission_scope": selector}` so a plain-tier trace still shows why a hop
  was admitted. `admit_hop` is the opt-in-friendly wrapper (`(True, None)` when no context is
  ambient at all) the interactive-path call sites actually use.
- **Phase 3** (`agents/interactive/`): a turn-entry hop (`assistant:<spec.name>` — `spec` has no
  `assistant_id` of its own, that's a manifest concept, so `spec.name` is the always-available
  stand-in), alongside the existing input guardrail in both `respond`/`respond_stream`. Skill
  (`skill:<name>`) and direct-tool (`tool:<name>`) hops in `_build_parent_tools`, with the
  **narrowing invariant**: while resolving a skill's own declared `tools`/`references`, the
  ambient context is temporarily narrowed to exactly those selectors, so a tool the *skill*
  declares but the *parent's own scope* never admitted is excluded even though the skill wanted
  it — not just "a tool the skill never declared," which was already structurally true before
  this plan. Knowledge-binding hops (`canonical:<type>`/`docs:<collection>`) in `resolve_knowledge`,
  refused bindings skipped (not raised), matching that function's existing best-effort posture for
  `docs` failures.
- **Phase 4**: `statemachine.engine.apply` and `automation.governed.GovernedAutomation.run` both
  prefer the ambient `InvocationContext`'s `matrix`/`actor_class`/`human_initiated`/`binding`/
  `overlay`/`execution_profile` over their own explicit arguments when one is set, falling back to
  the exact pre-existing call when not — verified by reverting each change and confirming the
  (pre-existing, unrelated) test failures were identical either way, not introduced by this work.
- 27 new tests across 5 files (`test_invocation_context.py` ×5, `test_authority_hop.py` ×6,
  `test_interactive_authorization.py` ×6, 4 new in `tests/test_resilient_runs.py`, 3 new in
  `tests/test_authority.py`).

## Acceptance criteria — verified

- `InvocationContext` survives a genuinely fresh `contextvars.Context` (the juno #242 shape for
  authorization, not just identity) when explicitly restored, and does not leak into one that
  never restores it. `require_invocation_context` raises when absent. `narrow()` only ever
  shrinks, never widens, and a `denied_selectors` entry always wins even through a narrow.
- `check_hop` refuses outside `permission_scope`, admits at a safe default ceiling with no matrix,
  delegates to (never reimplements) `check_action` when a matrix is present — verified by
  spying on the real `check_action` call and asserting its exact arguments — and every denial
  carries the ambient `trace_id`.
- A skill sub-agent cannot reach a tool outside its own declaration (pre-existing, still true) or
  outside the parent's own (narrowed) permission scope even when its own declaration wants it
  (this plan's actual addition) — both proven directly against the built tool list, not by
  inspecting internals. A turn refused at entry returns `blocked=True` with `last_hop_refusal` set.
  No `InvocationContext` configured anywhere reproduces pre-Phase-3 behavior exactly.
- `statemachine.apply`/`GovernedAutomation.run` prefer an ambient context that would refuse over an
  explicit argument that would admit (proving real precedence, not just presence), fall back
  identically when no context is set, and the same `InvocationContext` set once at a simulated
  "assistant turn" is still the one consulted several plain function calls later with nothing
  threaded through any intermediate signature.
- Full japes suite: 1978 passed (was 1975 before this plan's own new tests started), 3 skipped —
  no regressions. Two categories of test failure encountered during this work
  (`PolicyProfile`/`InvocationContext` "not fully defined" pydantic forward-ref errors in
  `tests/test_statemachine.py`/`tests/test_authority.py` when run in narrow isolation) were
  confirmed pre-existing by reverting this plan's changes entirely and reproducing the identical
  failure — a test-isolation fragility unrelated to this work, not introduced by it.

## Open questions the plan named for the executor to surface, not resolve (unresolved, as directed)

- Whether `PermissionScope.resource_selectors` should be a pack-supplied grammar rather than
  opaque strings — left opaque, per the plan's own stated v1 preference.
- Where `human_initiated` is authoritatively set (spoofability by a compromised host) — not
  addressed; `InvocationContext.human_initiated` is a plain field, trusted as given, same as
  Wave 3b's own `_human_initiated` on a bound spec.
- Whether a refused hop should count against `max_turns` — unaddressed; a refused skill/tool is
  excluded before any Agents-SDK run, so it never consumes a turn either way in this
  implementation, which happens to answer "no" for the build-time exclusion path but says nothing
  about a runtime refusal path this pass didn't build.

## Deliberately not done

- A runtime "refusal as an actual Agents-SDK tool-call result" (see Correction 2) — the exclusion
  approach satisfies the plan's opt-in/regression acceptance criteria; the deeper SDK-internals
  version is a separate, larger piece of work if ever needed.
- Making the interactive-path checks mandatory — stays opt-in, exactly as the plan's own Phase 3
  text requires ("becomes mandatory in a later version, once jazzx-assistant and juno have both
  adopted it").
