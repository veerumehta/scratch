# Done: Unified snake_case queue envelope

Author: Virendra Mehta · Updated 2026-08-01
Repo: japes · Plan: docs/plans/plan_unified_envelope.md

**Every japes-side action item in this plan is already complete or deliberately deferred by the
plan's own text — nothing left to build.** No status file existed for this plan; writing one now
after verifying directly rather than trusting the plan's own inline `[DONE]`/`[deferred]` tags.

## Verified against real code, not just the plan's own claims

- **Migration step 1** (contract test): `tests/test_envelope_contract.py` exists (commit
  `a1c3d67`, 2026-07-12 — predates this session), pins japes' emitted/parsed envelope to the Macer
  schema (nested tracking, snake_case, flat root status/error). Re-ran directly: **4/4 pass**,
  confirming this session's own `models.py` changes (adding `HookSpec`/`on_complete_hook` for
  `plan_invocation_completion_hooks.md`) did not regress the envelope contract.
- **Migration step 2** (`traceparent`): `Tracking.traceparent: Optional[str]` confirmed present in
  `jazzx_sdk/models.py`, same commit.
- **Migration steps 3-5** (`inline`/`ResultMetadata`, `ErrorInfo.retryable`/`code`/`details`,
  process-origin `Source` fields / `Target` / `Routing`) — all explicitly `[deferred]` by the
  plan's own text, each with a stated trigger condition ("add when a consumer needs them," "no
  producer needs them yet"). Not built here either, for the same reason the plan itself gives:
  building the plumbing before a real caller exists is exactly what this session's own working
  principle (`[[dont-generalize-unhit-problems]]`) argues against. Checked whether anything landed
  this session might qualify as a new trigger: `HookSpec`/`AgentDefinitionStore`/the SSRF fix are
  all orthogonal to payload size/error-typing/process-origin concerns — none of them is the
  "large-inline-payload" or "retryable-error-consumer" trigger this plan names.
- **Migration step 6** (flowable-core's `MacerResponseEnvelope.Header` reading flat `header.trace_id`
  instead of nested tracking) — a fix that belongs on flowable-core, not japes; the plan names a
  branch (`fix/macer-response-nested-tracking`) that lives outside this repo. Not actionable here.

## Open decisions — still open, not resolved by this pass

The plan's own three open questions (canonical ownership direction, whether to deprecate
`source.target_id`, whether to emit `metadata`/`inline` unconditionally once un-deferred) are
policy/design calls for the plan owner, not verification findings — left exactly as the plan states
them.
