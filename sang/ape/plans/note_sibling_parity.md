# Sibling parity: is each japes capability keeping pace?

Note, standing (updated on each sibling check), opus-xrepo. One lens per sibling, set by the user
2026-10-12. Each row: what the sibling does that japes does not (gap), or the reverse (ahead), with
the date seen and where it went. Absorbed work is built consumer-neutral (no client names; consumer
limits as pack data).

## macer: does the SDK's `AdjudicationAgent` keep pace?

Prior art: `status/superseded_macer_juno_japes_alignment.md` (to 2026-10-01), the 2026-10-04 survey
build (vote split, rejected evidence, open conditions kept on reruns, `ValidatedOutput` feedback).
Not yet compared function by function.

| Seen | Sibling has | japes | Where it went |
|---|---|---|---|
| 10-12 | One retry rule: transient = 408/429/5xx and network, `Retry-After` honoured, jitter | `concurrency.is_transient_error` + `retry_async`; `modes.utils.run_agent_with_retry` diverges | routed to sonnet-runtime |
| 10-12 | A validation retry whose remedy is a tool call keeps tools callable | `run_kit.ValidatedOutput` lacks it | routed (low) |
| 10-12 | `calculation_context` on a job's metrics, cap raised | missing from the JTBD writer and export | routed with the readiness checks |

## policy-workbench: does policy -> JTBD keep pace?

Prior art: `plans/note_plato_vs_policy_workbench.md` (2026-10-03), `plan_plato_authoring_review.md`.

| Seen | Sibling has | japes | Where it went |
|---|---|---|---|
| 10-12 | Readiness audit of a job set against what a downstream engine accepts (11 checks, three priorities), with fix guidance and an auto-fix for some | nothing on export | routed: structural checks in code, consumer contract as pack data |
| 10-12 | Ontology refresh on demand | catalog read per draft (no cache to refresh) | nothing to do |
| 10-11 | ahead: job ledger with dispositions, coverage count, code from jobs, cross-check | (sibling has none) | built, `v2.6.2` |

## kernel-lab: do policy -> JTBD, policy -> code and JTBD -> code keep pace?

Prior art: `local/mining/r_kernel_lab_mortgage_report.md` (rules_lib helpers, 10-11),
`status/done_kernel_deep_dive_2026-07-26.md`.

| Seen | Sibling has | japes | Where it went |
|---|---|---|---|
| 10-11 | Keep an extracted value whose quote does not verify, marked unverified (recovered 14-16 pts) | document agent refuses an ungrounded value | to discuss: measure on the Acra appraisal |
| 10-11 | Re-read stability per column between two extractions | experiment noise floor only | to discuss |
| 10-11 | Model diagnosis per wrong eval row, by cause and fix layer, ranked fixes | none | to discuss (rule-trial report) |
| 10-10 | Release rules: a condition closes when named evidence arrives | open conditions kept, no release rule | note only |
| 10-11 | Hand-written evaluators repeat date, tolerance, flag and band helpers | `rules_lib` 1.1.0 took them | done |

## eval-service: does our eval and feedback keep pace?

Prior art: `status/done_eval_service_contract_convergence.md` (2026-08), the eval control plane and
feedback service moved into the SDK (2026-09-25/26). Not checked since.

| Seen | Sibling has | japes | Where it went |
|---|---|---|---|
| | | | |
