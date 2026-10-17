Write the plan for evidence scoped per rule in AdjudicationAgent (see CLAUDE.md).

Read first:
- docs/plans/note_parity_adjudication_20261012.md, gap 2 ("Evidence access that scales") and rows 2.1, 2.3 and 2.4.
- docs/status/done_typed_conditions.md (just built on v2.6.3; its deviations section lists what is left).
- docs/plans/plan_programme_oct.md and docs/plans/note_sibling_parity.md (macer rows).
- Grep docs/plans and docs/status for prior art before writing.

State: branch v2.6.3 (SDK 2.6.3), local and unpushed. Commit on v2.6.3; no version bump, no push.

The problem (from the note): the adjudication step sends ONE segment holding every live rule and every
document's full text inline, rendered once per rule that reads it (jazzx_sdk/pipelines/steps.py
_run_adjudication, agents/adjudication/segment.py _render_batch_prompt, fabric/canonical/condition_evaluator.py
_batch_evidence). No tools, no read cap. A failed batch also makes every rule in the call INDETERMINATE, so
smaller segments shrink that blast radius.

Wire what already exists and is unused: EvidenceWorkspace, enforce_read_cap and ReadTooLarge,
PrecomputedGrounding, BrowseGate, tools/agent/dir_tools.build_source_tools, tool compression.

Scope the plan to cover:
- Segment by policy (section) in the step instead of one segment.
- Render each evidence field once per segment.
- An opt-in tool mode in run_segment: the reasoning agent reads the run's documents on demand inside
  EvidenceWorkspace.open(), with the read cap.
- PrecomputedGrounding for a pack's reference corpus.
- Per-segment cost in the trace.

Rules: plan first in docs/plans; consumer-neutral (no client or repo names; settings as pack data); tolerant
first (warn, record, surface; strict is opt-in pack data); CHANGELOG entries with line counts; the user runs one
review at the end. Put the decisions the user owes at the end of the plan and wait for them before building.

Already done, do not redo: typed conditions, vote keeps conditions, persona wired, transient-only retries.

Queued after this plan, in the user's order: Acra job-writer fixes (fold duplicate jobs across sections, map
missing-data jobs to catalog fields), blueprint chain from N1, document precedence on extraction targets,
per-experiment overrides on the assistant invokers, a supported ChatCoordinator extension hook. Also open:
gemini-4-argon needs a context window and status for its card, and a re-price on 2026-12-01.
