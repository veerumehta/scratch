# Sibling check, 2026-10-12: policy-workbench, macer, assistant, kernel-lab, imdoc

Note (decides nothing), opus-xrepo. Window: commits since the 2026-10-10 survey
(`plans/plan_sibling_ideas_oct.md`), all branches: policy-workbench 14, macer 8, assistant 7,
kernel-lab 17, imdoc 6.

## For japes, ranked

1. **MACER's load checks are not run on japes' JTBD export** (policy-workbench, `jtbd_audit`
   official checks, vendored from the team's `jtbd-audit-lite` skill). Eleven checks in three
   priorities: P0 MACER rejects the set (`schema-invalid` field caps, `metric-key-format`,
   `metric-key-not-in-ontology`); P1 wrong or inconsistent results (`duplicate-id`,
   `metric-key-owned-twice`, `cross-section-dependency`, `text-lost`, `output-contract`,
   `calc-context-wrong`); P2 (`metric-truncation`, `missing-as-zero`, since retired by the SME
   review). `jazzx_sdk.pack.jtbdset_export` / `pipelines.policy.jtbdset.export_jtbdset` check none of
   them, and the JTBD writer's metrics have no `calculation_context` (macer raised that field's cap on
   10-12, so it is in use). A japes export can therefore be rejected by MACER at load. Proposal: a
   `jtbdset` lint with the same check names (so findings line up with the workbench's panel), run on
   export and on the coverage page; `calculation_context` on `_DraftMetric`.
2. **One retry rule** (macer `utils/retry.py`, 10-12): transient = 408/429/5xx and network errors,
   `Retry-After` never undercut, jitter, a blocking variant on a thread. japes already has this as
   `concurrency.is_transient_error` + `retry_async`, used by the LLM manager and agent models;
   `modes.utils.run_agent_with_retry` is the one family member that still decides transience by
   matching error text and ignores `Retry-After`. Small fix: route it through the shared rule.
3. **Verify, don't reject** (kernel-lab extractor, 10-11). Rejecting a save when a value's quote did
   not verify cost 14-16 points of verified values and 27% of rows on the Pulte loans; keeping the
   value with its provenance marked unverified (and reporting it) recovered them. japes' document agent
   refuses a value it cannot ground (`agents/document/agent.py` `_ground` returns no basis, then a
   refusal). Worth measuring on the Acra appraisal before changing: how many refused fields were
   right.
4. **A validation retry that needs a tool keeps tools callable** (macer `validated_output`, 10-12):
   `ToolRequiredValueError` names the tools; those errors are reported first in the capped list. japes'
   `agents.run_kit.ValidatedOutput` (adopted from macer) has no such case; it matters only where a
   validator's remedy is a tool call.
5. **Eval ideas from kernel-lab's run report**: re-read stability per column between two extractions
   of the same files (japes has an experiment noise floor, not an extraction one); a model diagnosis
   per wrong eval row with fixed causes and the layer to fix (reader, ontology, rule, pack layer,
   wording, JTBD text, answer key, judge), grouped into a ranked fix list. The second would fit the
   rule-trial report.
6. **Release rules for asks that never close** (kernel-lab Pulte overlays): a condition releases when
   named evidence arrives (a current card, an executed lease, a signed letter). japes keeps open
   conditions across reruns; no declared release rule. Note only until a scenario needs it.

## Context, nothing to absorb

- policy-workbench: 65 new e2e tests (workspace ops, audit, guideline versioning, review/publish);
  workspace identity by stored path, not slug (a slug collision merged two files' documents);
  "Refresh ontology" on demand instead of at startup and every 6 hours; loan clone in parallel, stopping
  at the first 401.
- macer: tools grouped under `MacerTools` with file access confined to its directory; retry policy
  table in `design/macer.md`.
- assistant: project and team access through Ory Keto (JP-1876); `MessageTrace` marked completed at
  finalization. The org's authorization direction, should Plato need project scoping.
- imdoc: source-document ontology resolved from a list of names in one OData query.

## Routing

1 and 4 are policy and agent code (sonnet-runtime holds both path sets now); 2 is runtime; 3, 5 and 6
are for the user to prioritise.
