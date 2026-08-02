# Status: The Assistant Vertical — shipped vs. gap (LUNA / jazzx-assistant)

Author: Virendra Mehta · Updated 2026-08-01
Repo: japes · Plan: docs/plans/plan_assistant_vertical.md

**Both remaining build-flagged gaps (#6, #8) turn out to already be shipped or substantially
covered — verified directly, not assumed from the plan's own text, which doesn't mark them done.**
This is a reconciliation/survey plan, not a build plan — most of its real action items are
*adoption* work inside `jazzx-assistant` (a separate repo, out of scope for this pass) or explicit
design-first/deferred items, not japes-side construction.

## Gap #6 — Shared safety/grounding skill fragment: already shipped

Checked before building anything (caught mid-implementation, not before): `jazzx_sdk.agents.
interactive.safety` already ships exactly this — `SAFETY_INSTRUCTIONS` (a single combined,
domain-neutral fragment covering no-invention, "retrieved content is data not instructions"
injection defense, and the no-bias/no-steering/no-promises block) plus `with_safety(instructions)`,
an idempotent composer. Exported from `jazzx_sdk.agents.interactive`. Tested — 9 passing tests in
`tests/test_grounded_guardrail_safety.py`, re-run directly and confirmed green. Nothing to add; the
plan's own text simply doesn't mark this gap "SHIPPED" the way it does #1/#4/#5, so it read as open
until checked.

**Process note, stated plainly rather than glossed over**: I began implementing a near-identical
module (`safety_fragments.py`, multi-fragment + a `compose_skill_instructions` helper) before
noticing the existing `safety.py` while wiring its export into `__init__.py`. Deleted the duplicate
before it was ever committed. Lesson applied: check the actual export list of the module you're
about to add to *before* writing new code, not just search for a plausible-looking file name.

## Gap #2 — stage-progress stream event type: real, but not a japes-internal change

Checked where `StreamEventType` actually lives before attempting to add a `.stage`/progress
member: `jazzx_sdk/streaming/publisher.py` re-exports it from `common.core.streaming` — `common/`
is a **git submodule** inside this checkout (its own `.git` file, own `pyproject.toml`/CLAUDE.md,
shared platform infra also consumed by other services, not japes-owned code). Adding a new event
type there is a cross-repo, shared-infrastructure change, not a `jazzx_sdk`-internal one — exactly
the class of change this session's own risk posture says to pause on rather than make unilaterally
while the plan owner is away. Not attempted. `plan_luna_adoption.md` names the same gap; same
reasoning applies there too — see that plan's own status note.

## Gap #8 — Versioned invocation contract + boundary tests: substantially covered

`INVOCATION_CONTRACT_VERSION` + `tests/test_invocation_contract.py` (14 tests as of this session,
after this session's own `on_complete_hook` additions) already cover the concrete, testable parts
of this gap: payload envelope shape frozen by test, correlation-key vs. session-id semantics
(distinct, tested), identity headers (`security_context`/`x_security_context` alias, tested),
forward-compat (unknown fields tolerated, tested). The one piece **not** covered — the "`japes |
<name>`" run/experiment naming-taxonomy debate the plan mentions — is a naming *decision*, not a
contract shape a test can pin; still open, and not something to resolve unilaterally here.

## What's left is adoption work or explicit design-first items, not japes construction

- **Gap #1** (groundedness verifier), **#4** (adaptive-depth gate), **#5** (ChatConductor
  assembly) — already marked SHIPPED by the plan's own text; not re-verified in this pass (no
  reason to doubt them, and re-deriving already-shipped-and-marked work wasn't the goal here).
- **Gap #2** (stage-progress stream event) — plan's own text says "partially shipped," and stays
  that way; the remaining first-class `StreamEventType.stage` event type is real, scoped work but
  wasn't attempted this pass.
- **Gap #3** (feedback→trace→learning end-to-end) and **#7** (Memory Fabric) — both explicitly
  "Medium"/"Large; design-first" per the plan's own sequencing; neither attempted here.
- **The "adoption first" recommendation itself** — getting LUNA (jazzx-assistant) onto
  `InteractiveAgent`/`scope_guardrail`/`Source` citations/`CompactingConversationStore`/
  `RunTracer` — is work that happens *inside* `jazzx-assistant`, a separate repo not touched in
  this pass (outside this session's working directories; not something to start unilaterally
  without the assistant team's own context).
