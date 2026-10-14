# Sibling parity: is each japes capability keeping pace?

Note, standing (updated on each sibling check), opus-xrepo. One lens per sibling, set by the user
2026-10-12. Each row: what the sibling does that japes does not (gap), or the reverse (ahead), with
the date seen and where it went. Absorbed work is built consumer-neutral (no client names; consumer
limits as pack data).

## macer: does the SDK's `AdjudicationAgent` keep pace?

Prior art: `status/superseded_macer_juno_japes_alignment.md` (to 2026-10-01), the 2026-10-04 survey
build (vote split, rejected evidence, open conditions kept on reruns, `ValidatedOutput` feedback).
Compared function by function 2026-10-12: `plans/note_parity_adjudication_20261012.md`. Verdict:
ahead on verdicts and citations, behind on conditions. The sibling uses japes only as its queue
runtime, not `AdjudicationAgent`.

| Seen | Sibling has | japes | Where it went |
|---|---|---|---|
| 10-12 | Typed conditions (type, timing, party, one subject, stable ids across runs) | plain strings | to discuss: canonical `OutcomeCondition`, vocabularies as pack data |
| 10-12 | Evidence scoped per rule, tools, read cap | one segment holding every rule and every document's full text; workspace, read cap, grounding and browse gate exist but are unwired | to discuss |
| 10-12 | Validation retry sends only the feedback | `run_kit.run_agent` resends the whole prompt and retries 400/401/404 (defect, every caller) | to route: sonnet-runtime |
| 10-12 | Case-level condition dedup across sections and runs, reason gate | none | to discuss |
| 10-12 | Rerun resolution with a cited message, incl. underwriter-made conditions and new documents | restate/resolve only for re-judged rules, no cite | to discuss |
| 10-12 | Output validation retries (pages, CONDITIONAL without conditions, metric keys, subject ids) | bad cites dropped silently | to discuss |
| 10-12 | n/a | vote collapses PASS and CONDITIONAL (both SATISFIED); winner order-dependent, conditions can be lost (defect) | to route |
| 10-12 | Extracted values per rule with provenance and calculation steps | deterministic derived metrics only | to discuss |
| 10-12 | Prior status and rationale in the rerun prompt; per-run document history | omitted; `resolve_run_mode` unused | to discuss |
| 10-12 | LLM applicability triage; program detection | `SegmentPlanner` unwired; program supplied | low |
| 10-12 | n/a | spec fields never read (`persona`, `regime_values`, `status_vocabulary`, `mounts`, `segments`); `segment_concurrency=6` literal | to route |
| 10-13 | Validation retries suppress tool calls with `tool_choice="none"` (keeps tools declared so the cached prefix and earlier tool calls stay valid), except when the remedy is a tool call (`ToolRetryRequiredError`, `ToolRequiredValueError`, those errors reported first); on main (#286) | `run_kit` keeps tools on retry; `ValidatedOutput` has no tool-required case | resent prompt fixed in `10a4b90e`; tool suppression deferred by sonnet-runtime (japes never removes tools on retry, no validator needs a tool remedy yet; shape recorded if a consumer hits it) |
| 10-13 | Disputed values across replicas settled by an agent that checks each candidate against the cited documents and re-runs the math, picking a candidate, never writing one; falls back to the vote (branch `akshG/loan-metric-verifier`, unmerged) | vote by popularity or order; no extracted values yet | to discuss: fits the vote-collapse fix and extracted values |
| 10-13 | Write provenance on every entity it writes (`created_by_process_id`, `updated_by_process_id`), read by the feedback track (branch `umang/support-ontology-names`) | runs carry ids; written records do not point back | note for the corrections plan (a correction names the run) |
| 10-13 | Ontology and entity references accepted by name or UUID, resolved once at the start (same branch) | n/a (packs name their catalog) | context |
| 10-12 | ahead: deterministic rules without a model, id-matched drops become INDETERMINATE, closed `Verdict`, page-precise hashed cites, rejected-evidence demotion, field-level rerun impact, vote tallies and stability scorers | | |
| 10-12 | One retry rule: transient = 408/429/5xx and network, `Retry-After` honoured, jitter | `concurrency.is_transient_error` + `retry_async`; `modes.utils.run_agent_with_retry` diverges | routed to sonnet-runtime |
| 10-12 | A validation retry whose remedy is a tool call keeps tools callable | `run_kit.ValidatedOutput` lacks it | routed (low) |
| 10-12 | `calculation_context` on a job's metrics, cap raised | missing from the JTBD writer and export | routed with the readiness checks |

## policy-workbench: does policy -> JTBD keep pace?

Prior art: `plans/note_plato_vs_policy_workbench.md` (2026-10-03), `plan_plato_authoring_review.md`.

| Seen | Sibling has | japes | Where it went |
|---|---|---|---|
| 10-12 | Readiness audit of a job set against what a downstream engine accepts (11 checks, three priorities), with fix guidance and an auto-fix for some | nothing on export | routed: structural checks in code, consumer contract as pack data |
| 10-12 | Ontology refresh on demand | catalog read per draft (no cache to refresh) | nothing to do |
| 10-13 | Ontology refresh resets first and falls back to the saved id; workspace document identity by stored path reverted from staging (#198/#203); reasoner panel cost hint removed | n/a | context |
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
feedback service moved into the SDK (2026-09-25/26). Compared 2026-10-12:
`plans/note_parity_eval_20261012.md`. Verdict: ahead on the evaluation core, behind on running live
external entities and on runtime feedback. The sibling never imported the shared contracts package,
so convergence is one-sided. Plan step 7 has no branch anywhere.

| Seen | Sibling has | japes | Where it went |
|---|---|---|---|
| 10-12 | Async long-running cases (webhooks, polling, deadlines, timeout/cancel/human-task states) | each case awaited inline | to discuss (blocks retiring it) |
| 10-12 | External agent/process invokers, per-experiment overrides (prompt, model, temperature, tools) | invoker passes scope only | to discuss (blocks retiring it) |
| 10-12 | Run isolation: knowledge snapshots per dataset version, clone per run, fail-closed hooks | none | to discuss |
| 10-12 | Trace scorers registered, named judge presets | classes exist, not registered; no trace attached | to discuss (cheap) |
| 10-12 | Comparison depth: key pairing across datasets, cohorts, config diff, flip-rate noise floor | pairs by case id | to discuss |
| 10-12 | Feedback injected at runtime, pinned feedback, combined retrieval | `render_feedback_block` has no caller | to discuss |
| 10-12 | Attribution job with callback; eval auto-emits feedback | protocol only; `FeedbackSource.JUDGE` never written | to discuss |
| 10-12 | Pagination/OData, dataset delete, xlsx export, MCP scorer mount, legacy routes | missing | depends on which callers exist (unknown) |
| 10-12 | Scorer composition, NL scorers with tools, per-scorer timeout; MLflow mirroring; optimize timeout/progress | narrower | low |
| 10-12 | ahead: regression gates, judge cache and spend cap, resumable experiments, digested datasets, noise floor, silver panels, domain scorers, fix ledger, feedback-to-guidance, tenancy, UI | | |

## 2026-10-14 review (`note_sibling_review_20261014.md`)

| Seen | Sibling has | japes | Where it went |
|---|---|---|---|
| 10-14 | kernel-lab reader v2: which document wins a field (document class order, then date), per-paper routing, merge by key, cell provenance; run-to-run differences 21% to 1.5% | document_ingest: the first read wins, later values go to `conflicts` (steps.py ~1323) | to discuss: precedence as pack data |
| 10-14 | assistant and eval-service: per-experiment agent overrides validated and forwarded (#266) | `AssistantInvoker` passes scope only | to discuss (cheap) |
| 10-14 | imdoc: cross-replica admission limiter; transcription as a queue worker with retryable vs permanent failures; outputs tagged so derived files never come back as sources; submitter and condition stamped on documents; largest first | per-process RateGate; inline transcription | to discuss |
| 10-14 | macer: a rerun ledger of documents considered per section, append-only | `RerunBasis` copies one prior run | to discuss |
| 10-14 | macer: subjects as B1/B2 tokens in prompts | documents aliased only | with typed conditions (sonnet-runtime) |
| 10-14 | assistant `JAPES_V2` | equals main, no migration pushed | watch |
