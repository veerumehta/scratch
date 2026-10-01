# Status: LUNA adoption sketch — jazzx-assistant on the japes chat conductor

Author: Virendra Mehta · Updated 2026-08-01
Repo: japes · Plan: docs/plans/plan_luna_adoption.md

**This plan is a usage sketch for the `jazzx-assistant` repo, not a japes build plan** — its own
header says so explicitly ("in the jazzx-assistant repo"). Every primitive the sketch calls
(`InteractiveAgent`, `build_chat_pipeline`, `build_chat_components`, `run_chat_turn`, `ChatTurn`,
`GateDecision`, `MlflowTracer`, `build_run_tags`, `CallerIdentity`) already exists in `jazzx_sdk` —
checked, not assumed. There is no japes-side work this plan asks for that isn't already shipped.

## The three "gaps LUNA still needs japes for"

- **Groundedness verifier guardrail** — already marked shipped by the plan's own text
  (`grounded_guardrail`); confirmed present and tested (see `status_assistant_vertical.md`).
- **Stage-progress stream event type** — real gap, but not a `jazzx_sdk`-internal change: it
  requires adding a member to `common.core.streaming.StreamEventType`, and `common/` is a git
  submodule (separate repo, shared platform infrastructure, own `pyproject.toml`/CLAUDE.md) —
  cross-repo shared-infra work, not something to do unilaterally. See the fuller note in
  `status_assistant_vertical.md`'s gap #2.
- **KH client bump** — already done, own `done_kh_client_bump.md`.
- **Answer-entity persistence** — this is `jazzx-assistant`-side wiring (its own `finalize`/persist
  step calling `fabric.entities.ensure`), not a japes gap; the primitive (`fabric.entities.ensure`)
  already exists.

## Net

Nothing actionable for japes here beyond what `status_assistant_vertical.md` already covers. The
actual adoption (jazzx-assistant deleting its hand-built stage pipeline in favor of this sketch) is
work inside that repo, outside this session's scope.
