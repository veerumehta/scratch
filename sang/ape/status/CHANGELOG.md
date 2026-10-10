# Changelog

All notable changes to JAPES (JazzX SDK) will be documented in this file.

## [2.6.2] - unreleased

- **Generated rules are trialled before they merge, and written against a helper library.**
  *Trial.* `rule_trial` is an eval entity (`jazzx_sdk.pack.rule_trial`): a case's documents are read by
  the pack's own `document_ingest` step and its record assessed with a set of unmerged proposals
  overlaid (`overlay_pack`: the same merge `merge-rules` performs, on a throwaway copy of the pack cut
  to the ingest and assessment steps, so a trial calls no model but the document read and writes no
  store). Each proposal gets a verdict per case (`satisfied`, `violated`, `not_applicable`,
  `indeterminate`), the values it read and where from, the fields nothing supplied, and the case's
  decision with and without the overlay. The `trial_agreement` scorer compares verdicts with per-rule
  gold (`expected: {"rules": {proposal or rule id: verdict}}`), counting disagreements and unexpected
  indeterminates. A reviewer starts one (`rule_trial` experiments take the reviewer role); the proposals
  tab shows the latest trial that judged the proposal's current content, per case, with gold and the
  disagreements highlighted (`GET .../proposals/{id}/trials`). *Provenance.* Every rule outcome of a
  run lists `PolicyAssessment.reads`: the fields it read and the document and page each came from
  (the submitted record, a derived metric, or a document), shown on the runs page. *Fix.* `POST
  .../proposals/{id}/expand` (from the rule's code) and `/redo` (from its clause) regenerate a python
  rule from a note and the trial's failing cases as a superseding proposal (same rule id, id `~N`,
  `derived_from` / `superseded_by`, the old one no longer merges) and start a trial of it over the same
  cases. *Merge gating.* `PLATO_REQUIRE_TRIAL` (on when deployed, off locally) refuses merging a rule
  proposal no trial judged as it stands; a merged rule records `trial_ref` in its `domain_extensions`.
  *Library.* Python rules may `import rules_lib` (`jazzx_sdk.rules.lib`, delivered whole into the
  executor's child, `LIB_VERSION`, no imports, pure): `known`, `gaps`, `unknown` (the verdict "cannot
  tell", an indeterminate outcome naming the missing fields), `same` / `match` / `norm` (enum spelling)
  and `ratio`, chosen from what mining 51 generated rules showed they repeat (no date, unit or rounding
  helper yet: none appeared). A rule records the library version it was written against
  (`PythonCondition.lib_version`); lint warns where the pin differs from the delivered library and
  `retest_library_pins` re-runs those rules' cases after a bump. The python prompt shows the model the
  library's API, rendered from its docstrings. *A bug the trial found:* a python rule reading a number
  a typed fact catalog normalised to `Decimal` was withheld on every case (JSON cannot carry it), so 35
  of 51 generated rules were inert; reads now reach the rule as an int or float. *Executor on Linux.*
  `probe_isolation` asks the kernel whether the child's network namespace and process limit hold; in a
  deployed posture python rules are withheld where they do not (an assessment reports them pending,
  `/info` says why under `python_rules`, readiness is unaffected: a `BOOT_CONTRACT` row), and
  `/tmp/japes_executor_linux_check.sh` runs five container variants and nine escape attempts. Also this
  round: packs declare `requires: {japes: ">=2.6.2"}` (refused at load, check and publish) and
  unknown-key refusals name the running version; the field scorer takes `expected_any`; the document
  agent grounds a normalised value by a quote the extractor gave or a label the page prints
  (`ground_by_quote`, basis recorded on the field; a quote proves the words exist, not that they support
  the value, `TODO(quote-not-checked-against-value)`); the governor's own verdict and rationale are
  kept and what overrode them is recorded in `GovernorDecision.overrides`; the DSCR seed is resynced
  from jaci 0.2.14. Regenerating the 51 generated rules with the library prompt cut violations over the
  synthetic gold loans from 46% to 15% for $0.04 (+3027 / -112 lines, 66 files, since the second review round).

- **Packs declare the japes they need; one-of expected values; grounding by evidence; governor
  overrides recorded.** A manifest (domain or assistant) may carry `requires: {japes: ">=2.6.2"}` (a
  PEP 440 specifier, prereleases count): `PackManifestLoader` and `load_pack` refuse a pack needing
  another japes with "pack X needs japes >=2.6.2; this host runs japes 2.6.1", `check_pack_archive`
  reports it as the publish-blocking `requires_unmet`, and a malformed `requires` is refused rather
  than ignored. Pack load, check and conductor refusals that name an unknown key (pydantic
  `extra_forbidden`) now carry the running japes version (`explain_validation`), so an older host's
  refusal of a newer pack says why; no key-to-version lint is added, since no table of when each key
  appeared exists to build it from. The `field_path` scorer takes `expected_any: [...]` (the field
  passes on any of them; the expected record is not read). `DocumentAgent` grounds a value by its
  literal text, else by the words the extractor quoted for it when those are on the page
  (`ground_by_quote`, on by default: the extraction schema gains `evidence_quotes`, asked for by
  `documents/extract_quotes`), else by a printed label (`x-labels: {value: [labels]}` on the schema
  field, or the value's own words for a snake_case value); the basis is recorded on the field
  (`grounding`, `quote`), and a quote not found on the page grounds nothing, so a fabricated one is
  still refused. A quote proves only that the cited words exist, not that they support the value.
  The governor's verdict and rationale stay the model's own: what a failed assessment, a denial or an
  unrunnable policy check did is recorded in `GovernorDecision.overrides`
  (`by`, `clause`, `rules`, `decision_agrees`, `model_approved`), `approved` is the outcome, and the
  runs page shows the model's words and the overrides. The DSCR seed is resynced from jaci (0.2.14).
  Deferred, named in code: `TODO(sentinel-progress-config)`, `TODO(evidence-retry-config)`.

- **Second review round on the same range.** A run waiting on another caller's hold shows the model
  it waits on while it waits (`wait_on_gate` marks it on the run's `WaitLog`), `RefusalPlan.held` says
  a refusal held the gate (replacing two derivations), `rate_limit` reads the status with the one
  `_status_code`, the manager clears its own-hold flag on every pass, and the health signal for a run
  that only waited no longer says calls were retried. The bulk-reject dialog states that a rejected
  proposal stays rejected even when extracted again, the merge button no longer claims a count (merge
  takes one policy's rules), and an all-caps word is exempt from the text-quality check only up to
  `ACRONYM_MAX_CHARS`, so long garbled capitals are still read as bad text (+91 / -31 lines, 11 files).

- **Review fixes over the scanned-document, rate-limit and scorer work.** A run's flex fall back, its
  refusal count and its fall-back state are its own (`use_flex_fallback` opens a scope; a run that
  chose 0 is never moved by another's), the deployment's setting keeps one shared state, and the rate
  gate is held by a rate limit (429) alone: a timeout or 5xx backs off its own call and stalls no one.
  A retry's wait comes from one function used by `RetryingModel` and `LLMManager` (`on_refusal`); the
  reset headers are a 429's ask (at least a second), and a server error keeps `retry-after` only as a
  floor under its own backoff. A run's `waited_seconds` counts the holds it waited on beside its own
  refusals, `waiting` lists only models this run waited on, the beat carries the stage so a write
  cannot put an older one back, and a `flex_fallback_after` that `int()` would refuse is a 422. DocIntel
  pages with no priced model add to `unpriced_pages` and no longer mark a cost an upper bound; the offline
  stub's pages are not tallied, one provider is one tally key, and the DocIntel environment names are
  defined once. A page of acronyms (DSCR, CLTV) is not a bad text layer. A scorer that applied to no case
  has no mean, rate or delta (None), a document step that still records missing classes is not reported
  skipped, an identity compares as printed (case, spacing, `#`), the tab counts are for rule proposals,
  the packs page says a bulk reject cannot be reopened and clears a pack whose queue or runs cannot be
  read, and the price refresh follows the feed's pages and dates only a check that found every meter.
  (+~560 / -~170 lines)

- **An authoritative assessment no longer withholds approval from a decision that agrees with it.**
  With `deterministic_verdict: authoritative` a failed assessment forced `approved: false` even on a
  reasoner decision of `ineligible`, so a narrator gate of `governor_approved: true, decision_in:
  [ineligible]` could never fire (DSCR's governor approved 2 of 5 gold loans, and none of the 3
  ineligible ones got a narrative). The setting also reads `{mode: authoritative, adverse_decisions:
  [ineligible], decision_field: decision}`: a decision named there already says what the assessment
  says, so the governor keeps its own verdict and the assessment's violations are recorded in its
  `violations` and rationale ("the decision agrees"); every other decision is withheld as before, and
  the plain string form behaves as it did. The adjudication-denied branch follows the same rule; a check
  that could not run still withholds. It applies to the investigation step, `policy_check` and the
  legacy `investigation_loop` block. `refer_to_underwriter` is not adverse by default (nothing is):
  a referral does not state what the assessment states and a human decides next, so a pack lists it
  only if it wants its narrative on referrals. (+~190 / -~20 lines)

- **The operational modes default to the deployment's default model.** The investigator, verifier,
  reasoner, governor, narrator and sentinel each defaulted to `flex_gpt-5.4` (the sentinel to its
  `-mini`) in their own signature, long after the default moved on; they now take
  `llm.config.DEFAULT_MODE_MODEL` (the OpenAI default, currently `flex_gpt-6-luna`), and a test pins
  all six. A pack or run that names a model is unchanged. (+~25 / -~15 lines)

- **The verifier no longer asks for provenance the evidence never had.** The base verifier prompt
  (`3.0.0`) told the model to check `source_system` and `source_record_id` on the evidence object, which
  `Evidence` has neither of: a fixture or connector returns `Evidence(source="fixture:<file>",
  data={"records": [...]})` with provenance on each record, and the model sometimes flagged clean
  evidence for it (1 of 12 live runs on the old prompt, 0 of 12 on the new). The prompt now describes
  the shape (`source`, `data`, `metadata`), says a populated `source` is the provenance and that records
  carry theirs per record, and flags a record only for lacking what its siblings have. Evidence from a
  records list (`EvidenceTools`, `ToolRegistry`) carries `metadata.source_system` when every record
  shares one (`shared_provenance`), and the verifier is shown the evidence's `metadata`. Other
  producers (documents, the assessment, input) set `source` and are unchanged. (+~170 / -~40 lines)
  The verifier (`3.1.0`) then also checked the investigator's own request against data that never
  acted on it: a fixture or the case input answers with what the case holds whatever was asked, so a
  30-day lookback, an account or a depth that differs from the records is no fault of the data (8 of 8
  live runs flagged it on `3.0.0`, 0 of 8 on `3.1.0`). A source now records `metadata.params_applied`
  beside `query_params`: false for `input` and `fixture`, true for a connector and a registry tool, and
  the prompt judges the former on its content with the request as context and keeps the latter a
  contract (a connector that applied the request and returned rows outside it is still flagged, 8 of
  8). (+~90 lines)

- **An image request to OpenAI reached the API as the wrong shape.** The single-message fast path handed
  a content list of text and image blocks to the Responses API as top-level input items, which it
  refuses (`input_text`); the stubs in the tests never sent the request, so every image call on OpenAI,
  `classify_page_images` included, failed live. It is now one user message holding the blocks.

- **Splitting a scanned package keeps a document's pages together, and reading it has a dollar cap and
  a cache.** A window of scanned pages is classified by a versioned prompt that has the model write what
  each page shows (`observations`) before the label, and tells it that an e-signature certificate or
  disclosure belongs to the document signed, that transmittals, addenda and exhibits stay with their
  parent while complete documents side by side stay apart, and that an appraisal (1004/70, 1025/72,
  1007/1000) runs to forms, photograph pages and addenda; a mixed window carries scanned pages as images
  and digital ones as text. `split_identity: true` reads the printed identity of each page's document
  (a name or number, from its text or its image) so same-class pages of different loans never share a
  segment, and `attach_below` now runs on scanned pages too: the continuation check looks at both
  pages. `vision_budget_usd` caps what a run's vision reading spends (a call is charged as it answers,
  no new one starts once the cap is reached, and the pages left unread say so in `pages_read` and
  `vision_budget`); transcripts and window labels are cached by content hash, model, prompt and taxonomy
  in `JAPES_PAGE_CACHE_DIR` (or the `cache_dir` of the agent), so a rerun or a second step pays for
  neither again. Anthropic `cache_control` on window images was not added: overlapping windows share no
  prefix, so a cache write would cost a quarter more and never be read. (+~900 / -~60 lines)

- **A scorer can count on some cases only, and a presence scorer checks a value is there or is not.**
  A `ScorerSpec` takes `when: {<dotted path in the expected record>: <value or [values]>}` (strings
  compared ignoring case; a missing path does not match): where it does not hold the scorer is
  reported `skipped` (not applicable, with the failed condition as its comment), never a 0 or a 1.
  `presence` passes when the value at `actual_path` is present (not missing, null, blank or empty) or
  absent as expected: `present: true|false` in the params, else a boolean at `expected_path`, else
  whether the expected record has a value there. An experiment's per-scorer summary counts the cases a
  scorer applied to (`scored`) and did not (`skipped`), its mean and pass rate are over the applied ones
  alone, and a comparison's `by_scorer` carries both counts per side. (+~230 / -~10 lines)

- **The investigation loop owns three things jaci's AML evaluation found.** The sentinel's first
  iteration has nothing to compare with, so it is no longer counted stale (a threshold of 2 fired after
  one unchanged step), and a step that attested new evidence is not stale either
  (`SentinelMetrics.first_iteration`, `new_evidence_attested`). A request for evidence the loop already
  drew flagged or unavailable (same type and parameters) is refused before it reaches a source and
  recorded (`ctx.metadata["refused_evidence_requests"]`, with the verifier's reason, now kept on the
  evidence as `metadata.verifier_note`), and the investigator is shown what came back flagged or
  unavailable and why, with the instruction to seek another source or conclude. Each step of the loop
  says what it did on its record in `output.steps` (`detail`): the sentinel's metrics, threshold and
  guard, the investigator's requested types, the verifier's attested and flagged types with reasons, and
  the evidence step's refusals; a component sets it through `DETAIL_ANNOTATION`. (+~260 / -~15 lines)

- **A scanned or mixed document is read page by page, through a vision model, DocIntel OCR or a
  prebuilt form model.** A page is `digital`, `scanned` or `bad_text` (a layer of replacement or
  control characters, vowel-less words, or a few stray characters over a page-sized image; see
  `tools/documents/pages/assess.py`), and only the last two go to an engine, so a package spends on
  its scanned pages alone; splitting renders those pages and hands the digital ones over as text in
  the same window. `engine:` in `document_agent.yaml` (`auto`, `vision`, `docintel`,
  `docintel:<model>`; `by_class:` per class) chooses the reader, over which a step's `engine:` and a
  run's `?engine=` / `document_engine` apply; `auto` is DocIntel OCR where `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`
  and `_KEY` are set, else vision. A vision page is transcribed alone at its own resolution (at most
  2200 px), with the model's doubt (`low_confidence`, a reason) kept, one failed page tolerated and every
  page failing an error; extraction then reads the transcript, so grounding and page citations work, and
  each item lists `pages_read`. DocIntel authenticates with the resource key when `_KEY` is set (else the
  Azure identity chain). A DocIntel prebuilt form model (`docintel:prebuilt-mortgage.us.1004`) is
  opt-in per class, never a default and never chosen by `auto`: its fields map onto the pack's through
  `field_maps` (data, with `Entity.field` for a catalog field), carry the model's own confidence and page,
  stay limited by the class's `fields`, and any field it read that was not placed is reported on the
  item (`unmapped_reads`, with its reason) instead of dropped. The pack check names a mapping to a field
  nothing has and an `engine.by_class` class outside the taxonomy. (+~2700 / -~150 lines)

- **DocIntel is priced per page into the same usage and cost as model calls.** `model_data.json` gains
  `document_models` (`prebuilt-read`, `prebuilt-layout`, `prebuilt-*` for every other prebuilt model,
  with source, meter and date) and `document_sources`, read from Azure's Retail Prices API (eastus, S0;
  the pricing page renders its prices in script); `update_model_pricing.py` refreshes and checks them,
  so the staleness check covers them. Add-on features (high resolution, font, formula) and query fields
  are charged separately and not enabled. A document step's `ModeUsage` gains `pages` and `page_models`,
  its cost includes the pages, an unpriced model makes the figure inexact, and its provenance settings
  name the engines. `GET /models/documents` (client `document_models()`) lists the resource's models
  beside the LLM ones: provider, id, kind, unit, price or `price not recorded`, verified date and whether
  the resource offers it, asked of `GET {endpoint}/documentintelligence/documentModels` and cached an
  hour; the info page shows them. (+~900 / -~30 lines)

- **A rate-limited model is waited on together, and a long extraction shows how far it has got.** A
  retry honours the provider's own ask (`retry-after`, `retry-after-ms`, `x-ratelimit-reset-*`,
  Anthropic's reset timestamps) up to `JAPES_LLM_RETRY_HEADER_CAP_SECONDS`, else jittered exponential
  backoff (`JAPES_LLM_RETRY_BASE_SECONDS`, `_MAX_SECONDS`, `_ATTEMPTS`), on both the agents-SDK path and
  `LLMManager`. A process-wide gate per model holds every concurrent caller of a model one refusal has
  refused, so a run's segments no longer find the limit one 429 at a time. After
  `JAPES_LLM_FLEX_FALLBACK_AFTER` (or a run's `flex_fallback_after`) flex refusals a model's calls go to
  the standard tier, which costs more: off by default. An extraction run now records, while it runs,
  `segments` of `segments_total`, `proposals`, `calls`, `cost_usd`, `retries`, `waited_seconds`,
  `waiting` and `tier_fallbacks`, written every five seconds (store `update`), shown by the packs page
  and the stream, and reported in its health (`rate_limited`, `tier_fallback`). (+~900 / -~60 lines)

- **A step that did nothing is reported `skipped`, with why.** A step kind that returned without
  acting (the narrator's gate, a policy check or checkpoint with no decision, a checkpoint on a run
  that does not suspend, a document step on a case naming no documents) was recorded `ran`. A runner
  now calls `_skip(engine_state, reason)`, the engine records the step `skipped` with the reason as
  its note (`SKIPPED_ANNOTATION`), `output.steps` carries it as `reason`, and the runs page shows a
  "Why" column. The narrator's reason names the gate condition and its value. (+~90 / -~15 lines)

- **The DSCR seed is jaci's `0.2.8`, and records where it came from.** The seed now carries eleven
  document classes with per-class `fields` (hazard insurance reads none), and its document step is
  `required_when: documents` with the application, a lease or rent roll, the credit report and, for an
  entity borrower, the entity's documents. The sync script writes `SYNCED_FROM` (the source commit and
  pack version) into the seed, so a reviewer sees which source version it carries; the file names no
  consumer. The shipped-pack end-to-end test now reads an appraisal for its class's fields only and
  asserts the three core document groups it leaves missing. (+~120 / -~40 lines, plus the pack)

- **`document_ingest` reads each class for its own fields, and requirements can be groups, conditional,
  and wait for documents.** A taxonomy entry takes `fields: [...]`: a document admitted as that class is
  read for those fields only (a child inherits its parent's list unless it lists its own; a catalog field
  is named `Entity.field`), and a class with no `fields` key is read for all, as before; an explicit `fields: []` reads none (the document is classified and admitted, so it still satisfies `required_classes`, with no extraction call). A taxonomy key the SDK does
  not read (`field:` for `fields:`) is now a load error, and a listed field that neither `fields_schema`
  nor the catalog has is a pack-check finding. `required_classes` entries may be a class or
  `{any_of: [a, b], when: {<input field>: <value or list>}}`: a group is met by any one of its classes
  and the missing report names it whole (`rent_roll or survey`), a `when` binds only the cases whose
  field matches (case-folded), and the keyed form gains `base`, required of every case on top of its
  value's list. The check names a `when` on a field the input lacks or a value its enum forbids.
  `required_when: documents` holds a case to its requirements only when it names documents; the default
  `always` is unchanged, since a documentless case reporting its documents missing is what packs written
  so far rely on, and a pack that wants the other reading says so. `RequiredClasses.for_record` and
  `DocumentIngestStep.required_for` return `ClassNeed`s, not names. (+~330 / -~25 lines, 5 files)

- **The DSCR seed pack is jaci's, synced; a case can start from loan documents.** jaci owns
  `acra-dscr-policy`, and `plato/data/seed_packs/acra_dscr_policy` is a copy of its `0.2.5`
  (`scripts/local/sync_dscr_seed_from_jaci.sh` prints the diff, then copies only that pack with
  `--apply`; the seed keeps jaci's version number). Its conductor is a `conductor_pipeline`:
  `document_ingest` (`documents`, filling the record from `schemas/loan_document_fields.json`), the
  deterministic `assessment`, the investigation, the underwriter checkpoint and the narrative, so
  `POST /packs/acra-dscr-policy/runs` can name uploaded documents. A document read that the record
  has no field for is no longer dropped: `documents.unmapped` lists it with its value and page, a
  name that differs only in case or separators fills the record's own field and is listed in
  `documents.renamed`, and an unmapped read makes the run's health say `unresolved_gaps`.
  When the pack declares a catalog, `document_ingest` reads documents to it as well as to
  `fields_schema` (`use_catalog: false` turns it off): a catalog field that is one of the schema's
  lends it the catalog's description, values and unit, and every other scalar catalog field becomes a
  target of its own, so a read lands on the catalog's name (`Entity.field`) and is listed in
  `documents.catalog_reads`, information the record cannot hold and not a fault. Without a catalog
  nothing changes. The case-kind
  tests that ran on the seed as an `investigation_loop` pack now run on a frozen copy of it under
  `tests/data/packs`. An end-to-end test uploads a synthetic appraisal, runs the shipped pack
  against Plato and checks the filled fields, the assessed rules, and the document step's cost and
  provenance; a record-only run is checked unchanged. (+~700 / -~60 lines, plus the pack)

- **Policy extraction proposals are separated by the extraction that made them.** A proposal now
  records its extraction kind and run (`representation`, `run_id` on `Proposal` sets and stored rows,
  `ProposalView` and the client contract; `PolicyTurn` carries them), and the review routes filter on
  them: `GET proposals?representation=&run_id=`, the bulk `decisions` and `merge-rules` bodies, and
  `summary` returns status counts by kind and by run. `representation=-` selects proposals filed
  before the kind was kept. One narrowing function serves the list, a bulk ruling and a merge, so
  they cannot disagree. Client: `proposals`, `decide_proposals` and `merge_rules` take
  `representation` and `run_id`. The Packs page shows a tab per kind (JTBD, Python, Conditions,
  Obligations, and Earlier where older proposals exist) with proposed, accepted, rejected and merged
  counts, defaulting to the latest extraction's kind (catalog proposals stay on the Ontology page),
  and a run dropdown per tab labelled with date, documents, model, prompt version and cost. Accept
  all, Reject all (new), Merge accepted into draft and the JSON download act on the tab and run
  chosen, server-side, and say so in their text ("Merge 12 accepted JTBD proposals into draft"); the
  choice is remembered per browser. A proposal moves to the run that most recently proposed it.
  (+~620 / -~40 lines, 14 files)

- **PR #91's review comments.** The queue report scopes the run store to the caller's tenant
  before the limit (`TurnRunStore.active(input_equals=)`, a JSON-path filter on Postgres and sqlite),
  so another tenant's backlog neither crowds this tenant's runs out nor marks its report truncated.
  An eval case whose reply carries no usage records none instead of raising. The vote-stability scorer
  reads a tally with no `split` (a run stored before the tally carried one) as unanimous. In a strict
  posture, submitting, deciding, closing, resubmitting and commenting on a review, and triaging a
  lint finding, need a caller user id (401), so self-approval and the audit trail always have an
  identity; locally nothing changes. A bool query parameter needs no client change: httpx already
  sends `true`/`false`, now held by a test. (+~170 / -~15 lines, 10 files)

- **An extraction run shows what it is doing, and the dashboard's log buffer sees it; a Logs page.** An
  extraction run logged only failures, and the root logger defaults to WARNING, so the buffer
  behind the dashboard's Recent logs never saw an INFO record from any run: a run looked silent. Now
  a run logs when it starts (representation, documents, pack, model), at each stage, as parts are
  read (the catalog one by one, rule extraction in about ten steps whatever the corpus size), when
  joining names, every heartbeat while it runs ("still running after 90s: reading the documents")
  and when it ends with its parts, proposals, calls and cost. A process's logging is now one call,
  `jazzx_sdk.observability.configure_logging(LoggingConfig(...))`, that fronts `common`'s
  `setup_logging` (JSON with OpenTelemetry trace ids, Event Hub, noise suppression) and does the
  same job with the standard library where `common` is absent or `JAPES_LOGGING_BACKEND=stdlib`. A
  client says what it wants: its `namespaces` opened to the level (a library's loggers are left
  alone), `level_env` (Plato reads `PLATO_LOG_LEVEL` then `LOG_LEVEL`), text or JSON output
  (`USE_JSON_LOGGING`), a console handler only where the host configured none, an in-memory
  `buffer` of recent records (`observability.log_buffer`, moved from Plato's logs module), a rotating
  `file_path`, and the removal of a platform-injected `OTEL_EXPORTER_OTLP_*`. Calling it twice
  applies the later call's choices. Plato calls it at boot (`plato.api.logs.LOGGING`), which it
  never did, so its INFO records now reach the console and the dashboard. A **Logs** page
  (`{prefix}/logs/ui`, in the nav) reads the buffer, refreshes while
  open, filters by level and text, and says it is this replica's memory. (+~900 / -~110 lines, 18 files)

- **A client that hangs up no longer leaks a database connection, and a temperature nobody asked for
  is no longer set or warned about.** Starlette's `BaseHTTPMiddleware` (what `@app.middleware("http")`
  builds) cancels the handler when the client disconnects; a handler cancelled inside an asyncpg call
  never returned its connection and the pool's garbage collector terminated it later ("Exception
  terminating connection", "non-checked-in connection"). The identity gate, security headers, request
  metrics, the inbound header capture (a japes copy of `common`'s, with a test that it keeps what
  `common` keeps) and the mock knowledge hub's gate are now pure ASGI
  (`jazzx_sdk.server.asgi_middleware`), and `DbStore.session()` shields each round trip from anyio's
  cancellation (`jazzx_sdk.fabric.db.shield`), so a streamed response cut off mid-query finishes the
  query first. A test hangs up on a long POST and a stream against Postgres and asserts the pool is
  empty with no termination logged; it fails on the old stack for the stream. The governor,
  investigator, narrator and verifier no longer set `temperature=1.0`; the reasoner and the OpenAI
  provider set one only when the caller gave it (`agents.models.apply_temperature`), warning when an
  asked-for value is dropped by a reasoning-tier model and not for a default, and the evaluator's
  0.2 is `DEFAULT_TEMPERATURE`. The 4096 and 8192 token caps are `MODE_MAX_TOKENS` and
  `NARRATOR_MAX_TOKENS`. (+~480 / -~110 lines, 25 files)
- **Review fixes.** A catalog field's unit is kept only where every entity that has the field states
  it, whatever order the entities come in; a mnemonic whose prefix leaves no room gives none and a cut
  never ends in a number; `noise_from` must be a completed repeat of the baseline's entity and
  dataset; seeding blueprints reports any failure per blueprint and skips one already stored; the
  Ontology page clears the last draft's tree and proposals when no draft or tenant is chosen, tells a
  missing catalog from an unreadable or invalid one, shows a refused poll's own message and opens on
  `PLATO_DEFAULT_PACK`; the Packs page clears blueprint labels when a read fails and, like the
  Ontology page's catalog tree, ignores a slower answer for another tenant or draft. A draft that holds bytes that are not UTF-8 digests differently since the
  digest keeps them (`surrogateescape`): a review approved before that must be resubmitted.

- **Run health, a noise floor in experiment comparison, competency questions in the pack lint, and a
  standalone-client guard.** `jazzx_sdk.util.run_health`: an extraction run records `health`, signals
  with a severity read from the record (`no_segments`, `no_model_calls`, `most_parts_failed` are
  critical and fail the run with the reason; `no_proposals`, `parts_failed`, `joins_failed`,
  `lint_errors`, `not_linted` warn; thresholds left out inform), and a case run's `CaseResult.health`
  reports `no_decision` (critical), `pre_loop_failed`, `investigation_not_converged` and
  `unresolved_gaps` without changing its status. `compare_experiments(noise_floor=)` holds a case
  delta at or under it to `unchanged` (`within_noise`), `noise_floor_from` measures it from a repeat
  run of the baseline, and the compare route, runner and client take `noise_floor` or `noise_from`.
  A pack's `competency.yaml` lists questions with the `Entity.field` paths each needs; lint
  `unanswerable_question` flags a question the catalog cannot answer, `competency_malformed` a bad
  entry, `competency_without_catalog` a file with no catalog to check against. A test imports
  `jazzx_plato_client` and its CLI in a fresh interpreter and asserts the SDK, the server stack and
  the model providers are not pulled in. (+~420 / -~30 lines, 14 files)

- **Catalog extraction joins the names it gave one fact, and leaves thresholds to the rules.** After the
  parts are read, one model call joins entities that name one thing, then one call per entity joins its
  fields (a name from the catalog or a reference is preferred as canonical) and marks the names that
  state a limit the policy sets (`min_dscr`, `max_cltv_pct`) as thresholds, which are left out and
  listed; a call that fails leaves the names as found and is reported. The catalog is the vocabulary of
  facts a rule reads (lint, the JTBD writer and metric keys read it), so a limit belongs to the rule.
  `catalog_extract/instructions` is 1.1.0: facts not limits, one plain name per fact with no unit
  suffix or `is_` prefix, an enum rather than a new field, no tier tables as types, a short unit
  vocabulary, a reference's type kept unless the text contradicts it. New prompts
  `catalog_extract/consolidate_instructions` and `consolidate_prompt`. The extraction run records
  `consolidated` and `thresholds`, and the Ontology page says how many. (+~260 / -~10 lines, 7 files)

- **A pack version that is not PEP 440 is refused at publish, and runs cite the blueprint that pinned
  them.** `store.publish` raises `InvalidPackVersion` (422 from the upload, sample, draft and seed
  paths) naming the version, because no version range can select one; `version_satisfies` treats an
  existing non-PEP 440 version as satisfying nothing in `check_policy_binding`, the assistant
  manifest loader and blueprint resolution, instead of raising `InvalidVersion` (a 500). The seed
  `ci-spread-core` is `0.3.0` (was `0.3.0-draft`). A case run records `plato_blueprint` on its input
  (`blueprint_id`, `blueprint_version` and every member's pin), a chat or skill turn on its trace
  metadata, and an assessment in its answer, when the tenant's most recent activation of a blueprint
  pinned exactly the pack version the run used; a pack activated on its own, or since moved, cites
  nothing. (+~330 / -~40 lines, ~20 files)

- **Solution blueprints: the named set of packs that make one solution, activated together and pinned.**
  A blueprint (`jazzx_sdk.pack.blueprint`, tables `blueprint`, `blueprint_member`, `blueprint_pin`,
  migration 0025) names a policy pack, an assistant pack and optionally a core, each with a version
  range; it does not compose them. Publishing validates that every required member resolves to a live
  version of the right kind and that the assistant's `policy_pack_id` is the blueprint's policy and
  accepts its resolved version. `POST /blueprints/{id}/{version}/activate` activates core, policy and
  assistant through the pack activation path and records the exact versions as the tenant's pins; a
  member that will not activate stops the rest and pins nothing. Routes `GET /blueprints`,
  `GET /blueprints/{id}`, `PUT /blueprints/{id}/{version}`; client `blueprints`, `blueprint`,
  `put_blueprint`, `activate_blueprint`; CLI `blueprints`, `blueprint`, `blueprint-activate`. The packs
  page opens with a "Solution blueprints" section (a card per blueprint with each member's range,
  resolved version, pin and last publish, Edit draft, Ontology, Activate, and a form to publish a
  version), and the pack table is "All packs" with packs in no blueprint marked unassigned. The
  inventory gives each pack a `kind` (`domain` or `assistant`). `POST /packs/initialize` also
  publishes the bundled `acra-dscr` blueprint. **Renames (breaking ids):** the seed `dscr-core` is
  `acra-dscr-policy` (version `0.2.0`, a PEP 440 version a range can select) and the sample assistant
  `acra-dscr-core` is `acra-dscr-assistant`; published rows under the old ids are untouched and stay
  readable. (+~1500 / -~180 lines, ~95 files)

- **A pack can say how its jobs are filed and named, and policy extraction reads the pack's
  catalog.** `jtbd_template.yaml` takes `section_types` (a section to its type), `mnemonics`
  (a prefix family per section, a pattern, a 20-character cap), `roles`, `limits`
  (`skill_max_chars`, `section_type_min_chars`) and a `requirement_template`. The writer drafts a
  job's `section_type`, `assistant`, a mnemonic `topic`, `entity_types` and `loan_metrics`, and code
  holds the line: the section's type from the template's map, an assistant from `roles`, a mnemonic
  that is the section's prefix and the topic (or, when taken, the job's name a word further) that
  fits the pattern and length, ends in no number and repeats none in the pack or the run (none is
  left rather than numbered), a skill cut to its limit, and entity types and metric keys only from
  the catalog. The fields ride on the rule (`domain_extensions.jtbd`) and the JTBDSet export gives
  the job its mnemonic. A pack's `prompts/policy_jtbd/*.md` overrides the writer and planner
  prompts, loaded and versioned through `load_prompt(pack_files=)`. With a catalog, every
  extraction reads its fields: `JtbdTemplate.bound_to_catalog` sets `reads`, `units` (percent or
  fraction), `entities` and `metric_keys` from it, which python and condition rules and jobs are
  restricted to (obligations read no fields); a template `reads` the catalog does not declare is a
  lint warning (`template_read_not_in_catalog`). Without a catalog nothing changes. A manifest's
  `exports:` names what a pack can be turned into (`jtbdset`); listing exports without it refuses
  the JTBDSet export, and an unknown name is a lint finding. The DSCR seed carries a template from
  the JTBD ontology guide and `exports: [jtbdset]`. The ontology panel is its own page
  (`/ontology/ui`, in the nav), and the client's command line gained the catalog commands
  (`catalog-refs`, `catalog-ref-put`, `catalog-ref-delete`, `catalog`, `catalog-adopt`,
  `catalog-extract`, `catalog-merge`). (+~1,300 / -170 lines, 26 files)

- **Claude Haiku 5.5 has a model card.** `claude-haiku-5.5` (API id `claude-haiku-5-5`): 1M context,
  128K output, adaptive thinking (default effort `medium`), and `temperature`, `top_p` and `top_k`
  listed as rejected. Priced by prompt length: $0.10 in / $0.50 out up to 100,000 prompt tokens
  (cache write $0.125, read $0.01), $0.50 / $2.50 over it (write $0.625, read $0.05), the whole
  prompt at the rate of its length like the other long-context rows. The routing tiers still name
  Haiku 4.5. (+~50 / -0 lines, 2 files)

- **The provider models nobody tracks are ignored.** Eighteen OpenAI and Gemini ids the push
  check listed are in `ignored_models`. (+21 / -1 lines, 1 file)

## [2.6.1] - unreleased

Plato 0.2.1; `jazzx-plato-client` 0.2.1 (the client always carries Plato's version).

- **Answers to the second pull request review.** Resubmitting a review no one owns (a draft and a
  review made without identity) is refused in a strict posture and allowed in a relaxed one; a
  resubmitted review no longer carries the earlier reviewer's note; a draft's digest keeps bytes
  that are not UTF-8 apart (`surrogateescape`, the same digest for valid text). (+~60 / -4 lines,
  5 files)

- **Answers to the pull request review.** A rule re-judged on a rerun that gets no answer (its
  segment failed, or the model left it out) is INDETERMINATE and no longer keeps the earlier
  verdict; a rerun's changed fields reach the metrics derived from them (`through_metrics`), so a
  live rule reading a derived value is re-judged when its inputs change; an uncited SATISFIED or
  VIOLATED verdict on a rule with rejected evidence reaches no answer, like one citing only
  rejected evidence; a split unsure of a page leaves the decision for review. A draft's files and
  revision are read together (`DbPackDraftStore.snapshot`, used by submit, resubmit, comments,
  lint runs and the draft diff; 409 `draft_changing` if it never holds still), and migration 0024
  gives each draft that predates history a baseline of events, so a pinned revision holds all its
  files. A lint run lints the files it records (`run_lint(snapshot=)`, handed the submit route's
  own snapshot), the draft diff answers `draft_changing` in the same body, and an import that
  removes an overlay also drops it from string and partial `programs:` entries and from any
  `default_program(s)`. (+~420 / -40 lines, 26 files)

- **Review fixes over the models, assess, import and catalog work.** A run that suspends at its
  checkpoint resumes on the model it was submitted with (`resume_pipeline_case(model=)`), and the
  run's model reaches `document_ingest` through the metered service; the docs now say the run's
  model is used over the pack's pins (a mode named in `mode_overrides` still wins). `assess` with
  several programs refuses each program on its own missing facts and evidence gaps and skips it
  with the reason, refusing the call only when every program is refused. A comparison workbook
  accepts any label (characters a sheet title refuses become spaces). A `$ref` to a missing
  definition is a `ValueError` naming it, and a reference catalog holding one is refused on upload.
  A partial rejection of a verdict's cites reopens the conditions it had resolved. Importing again
  removes the `JTBD_*` policy files the earlier import wrote and this one did not, and an empty set
  is refused by name. The agent's provenance names a model only when one model served the turn.
  A program an import removed leaves the manifest's `programs:` too, and a refused program ordered after the selected one is skipped with its reason. The CLI answers a Plato that does not answer with a message and exit 1. The Ontology panel's
  catalog buttons follow the tenant rule, an empty confidence floor takes nothing, and a failed
  queue read is reported. (+~420 / -60 lines, 33 files)

- **Policy documents build a pack's catalog (the Ontology panel).** A new `catalog` extraction
  representation reads documents in parts, a model names the entities and fields each part speaks
  of (versioned prompts `catalog_extract/*`, cost recorded like the other steps), a candidate whose
  quoted excerpt is not in the text is dropped, candidates for one field merge across parts and
  documents, and each is classed against the draft's catalog and the chosen references (`id`,
  `id@version`, `pack:<pack_id>`): `matched`, `reusable` (a reference has it, so it is adopted with
  its `x-source`), `conflicting` (the catalog or a reference holds it differently; both sides are
  kept on the proposal) or `new`, filed as `Proposal(kind="catalog")` with its excerpt and sources;
  a field on an entity nothing has files the entity with it. Review uses the existing queue
  (`?kind=catalog`); `POST /authoring/review/{pack}/merge-catalog` writes the accepted ones into the
  draft's `catalog.schema.json`, adopting reusable ones from their reference, applying a conflict
  the document's way (accepting is the reviewer's choice) and refusing a result that is not valid
  JSON Schema. Lint reports an adopted field no rule or derivation reads (`unused_adopted_field`).
  The packs page gains the panel: reference picker and upload, the draft's catalog as a tree with
  sources, proposals grouped by class with their excerpt and the two sides of a conflict, accept all
  high-confidence (conflicts never in bulk), merge. A fact catalog may now hold 1024 facts
  (`MAX_CATALOG_FACTS`); a formal claim carries the whole catalog while it fits its 64 and
  otherwise only the facts its rules read, refusing by name when those alone are too many.
  Client: `start_extraction(representation="catalog", references=)`, `merge_catalog`.
  (+~1,900 / -60 lines, 38 files)

- **A pack's catalog can be JSON Schema, and fields are adopted from reference catalogs.** A
  manifest declares `catalog:` (JSON Schema 2020-12, entities under `$defs`) or the existing
  `ontology:` YAML, not both; `jazzx_sdk.pack.catalog` reads a catalog as the authored ontology dict
  (type arrays as nullable, enums without null, `$ref` to shared types and entities, `allOf`
  merged, arrays of entities as relationships) and writes it back, so the vocabulary, derivations
  and lint see either shape and `ci-spread-core`'s YAML round-trips exactly. `catalog_adopt.adopt`
  takes named fields of a reference entity into a catalog, field by field: a field's shared types
  come whole, an entity it points at as a stub, a reference's `required` lists not at all, each
  piece recording `x-source` (`<reference id>@<version>#<pointer>`), and a field already present
  that differs is a conflict for the reviewer. A tenant's reference library is a table
  (`catalog_reference`, migration 0023): `GET/PUT/DELETE /catalogs/references`, a published pack's
  catalog or ontology readable as `pack:<pack_id>`, and `POST /packs/{id}/catalog/adopt` writes the
  draft's `catalog.schema.json` (and names it in the manifest). Client: `catalog_references`,
  `put_catalog_reference`, `catalog_reference`, `delete_catalog_reference`, `adopt_into_catalog`.
  (+~720 / -10 lines, 17 files)

- **Cost shows on every Plato page, and says what it rests on.** A step's usage
  (`ModeUsage.cost_is_upper_bound`) is a ceiling when a call's model has no price card or none was
  reported; a run's summary now always carries a total, zero when no model was called, so an older
  run with none reads "not recorded" and a deterministic one reads $0. The run page shows each
  step's model, tokens and cost and the total; extraction runs show each step and the total;
  evaluation case runs carry `usage` (`Invocation.usage`, set by the pack assessment, case run,
  adjudication and assistant invokers), experiments sum it with how many cases reported it, and a
  comparison carries each side's cost in total and per case. `POST /packs/{id}/assess`, the JTBD
  import and the JTBD compare answer `usage` (an explicit zero off the model paths, metered when
  `reason=true` or `match_with_model` runs a model). One formatter, `plato/static/cost.js`, serves
  every page. Prompt files carry the author line. (+~420 / -40 lines, 22 files)

- **The push check lists models the providers serve that `model_data.json` does not track.**
  `scripts/check_new_models.py` asks each provider's model list (the key already in the
  environment; none, no network or an error is "not checked"), drops snapshots, embeddings, speech,
  image and fine-tune ids, and reports what no row tracks; on a terminal it offers to record them
  in `ignored_models`. Cached for a day, about two seconds, never fails the push
  (`JAPES_SKIP_MODEL_CHECK=1` skips it). The price diff takes about a minute, so the hook only
  reminds when it has not run for a week. (+~190 / -0 lines, 3 files)

- **An assistant can name the domain pack it works with.** `AssistantManifest` takes optional
  `policy_pack_id` and `policy_pack_version_range` (`pack_id` stays the assistant bundle's own key);
  activating an assistant pack fails with the missing pack or the published versions when the
  tenant has no live domain pack of that id inside the range
  (`jazzx_sdk.pack.activation.check_policy_binding`). Unset binds to nothing, so existing assistants
  activate as before; the Acra sample binds to `dscr-core` `>=0.1`. (+~60 / -1 lines, 4 files)

- **Several programs can be assessed in one call.** `assess(..., programs=[...] | "all")` and
  `POST /packs/{id}/assess?programs=a,b|all` (client `assess(programs=)`) assess those programs
  together when the input names no `program_id`; a pack may also declare `default_programs: [...]`
  with `select: first_eligible` in its assessment block. The shared preparation runs once and each
  program is checked over the same context (the core plus that program's overlay only), a live
  rule's identical question to the model is asked once, and the result adds `programs` (each
  program's own assessment), `selected_program` (the first that passes) and `skipped` (why each
  earlier one was passed over). The top-level fields are the selected program's, else the first's.
  A call that names one program, and the manifest's `default_program`, return what they did, with
  `programs: {}`. (+~210 / -50 lines, 6 files)

- **A version or a draft carries notes on where it came from.** `notes` on `pack_version` and
  `pack_draft` (migration 0022): upload takes a `notes` form field, `PUT /packs/drafts/{id}/notes`
  sets a draft's, publishing a draft carries them onto the version, and the packs page, the
  inventory and the client (`publish_pack(notes=)`, `set_draft_notes`) show them. (+~120 / -10
  lines, 12 files)

- **JTBDSets import into a pack draft, and two sets compare.** `POST /packs/{id}/jtbdset` imports a
  set into the pack's draft as policies; `POST /packs/{id}/jtbdset/programs` imports two sets, one
  per program (`jazzx_sdk.pack.jtbd_import`): jobs are paired by `jtbd_match` (the same id, then
  the same section and skill text, then the closest text and metric keys, a model settling only
  close calls, one call per section, with versioned prompts), a job whose text is identical in both
  goes to the core once and, with `match_with_model`, so does one in the same section whose
  deterministic checks carry exactly the same numbers and that a model confirms states the same
  requirement in other words (the other file's wording kept as `variants`); every other job goes to
  its program's overlay, as `<mnemonic>.<program>` (a pack keeps one rule per id), with the
  counterpart recorded as `also_as`. `POST
  /packs/compare` (client `compare_jtbds`, `compare_jtbds_xlsx`) takes two sides (a JTBDSet, a
  published version or a draft) and reports what only one has, and for each pair how it was made
  and the fields that differ (section, skill, text with its similarity, metric keys, entity and
  evidence types), as JSON or an xlsx workbook. `python -m jazzx_plato_client export-jtbdset |
  proposals | compare` reads and compares from a shell. Acra's two files, imported, share nothing:
  71 mnemonics appear in both, none with identical text. (+~1300 lines, 22 files)

- **More of what a run ran with is recorded, and more prompts are versioned files.**
  `InteractiveAgentSpec.from_dir(path, source=)` stamps the persona file and each skill's
  instructions with a `PromptRef` (`spec.persona_ref`, `spec.skill_refs`; `spec.prompt_refs()`
  gives a digest-only `inline` ref where a persona or skill was a string). A turn builds its
  instructions with `ComposedPrompt` (the persona, then the grounding and guidance as named
  fragments, the same text as before) and `InteractiveResponse.provenance` records an `agent` step
  (model, the persona's ref and a digest per fragment, sampling settings, the skills it could
  call, the answer schema's digest) and a `skill:<name>` step for each skill it called, read from
  the run's tool calls. `StepProvenance` gains `tools` and `output_schema_digest`, and
  `behaviour_digest` covers prompts, model, sampling settings, tool names and answer schema;
  `ReasoningAgent` reports the last three to the run's meter. The five investigation modes' prompt
  files (and the fallbacks) carry a `version`; `compose_mode_prompt` and `resolve_mode_prompt`
  return the text without its header as a `ResolvedPrompt` (a `str` that also holds its refs: the
  base's, and a pack's `mode_tuning/` as its own `pack` ref), so a case run's `provenance` names
  `modes/investigator` 1.0.0 rather than a digest. The condition evaluator's three prompts and the
  document step's three (`documents/classify_instructions`, `extract_instructions`,
  `continuation_instructions`) moved into files; `agents.run(prompts=)` carries refs to a
  metering wrapper. Tests: one for each bundled prompt changing under the same version, and one
  that a run's model survives `to_thread`, `create_task` and `call_maybe_async` and that no code
  uses `run_in_executor`. (+~700 / -95 lines, 53 files)

- **Prompts are versioned files, and every run records the model and prompts it ran with.**
  `jazzx_sdk.prompts`: `load_prompt(name, **fields)` renders `<root>/<name>.md` (an optional front
  matter `version`; a file with none is versioned by its content hash) and returns the text with a
  `PromptRef(name, version, digest, source)`. Lookup is the pack's `prompts/`, then the consumer
  roots (`JAPES_PROMPT_ROOTS`), then the SDK's own `jazzx_sdk/prompts/files/`; `source` says which.
  The extraction prompts (`policy_jtbd`, `policy_code`, `policy_conditions`) and the adjudication
  step's (`adjudication/instructions`, `batch_header`, `emit_instructions`) moved from constants
  into those files, byte for byte; the per-rule fragments adjudication appends (a rejected cite, a
  prior condition) are still code. `tests/data/prompt_digests.json` fails a test when a file's text
  changes under the same version. `ReasoningAgent.run(prompts=)` tells the run's `CallMeter` each
  call's model, usage and prompts, found with `current_meter()` (a context variable the run
  sets), so no call site threads a parameter. `ExtractionRun` and `CaseResult` gain
  `provenance: [StepProvenance]` (step, model, calls, prompts, a `behaviour_digest` over model,
  settings and prompt digests) beside the numeric `usage`; extraction runs gain `usage` per step
  and a case run's modes, adjudication and assessment each get an entry. A mode's system prompt is
  recorded as an `inline` ref (a digest; not yet a versioned file). Registry: `DbPromptRegistry`
  is tenant-keyed (default tenant for the platform's own prompts; migration `0021_prompt_registry`),
  Plato registers every prompt file at startup so a past run's text stays readable, and
  `GET /prompts`, `GET /prompts/{name}` and `GET /prompt-diff?name=&a=&b=` list, show and diff
  versions by the digest a run recorded (client: `prompts()`, `prompt()`, `prompt_diff()`).
  (+~1100 / -140 lines, 30 files)

- **A model can be chosen per run and per step.** `jazzx_sdk.llm.selection`: `selectable_models()`
  (model cards whose provider has a key, the configured default first), `check_selectable()` and
  `select_model(request, step, pack, tenant)`, which applies one order (request, step, pack,
  tenant, `{PREFIX}_LLM_MODEL`, provider default) and says which decided. `RunSettings(model,
  step_models)` reach every `ReasoningAgent` call of a run through a context variable. Extraction
  submit takes `model` and `step_models` (checked, 422 if unknown or without a key; recorded on the
  run); case runs take `?model=` (and `run_case(model=)`), which every mode a mode override or
  the pack does not name uses, the adjudication and assessment reasoning included, and
  `CaseResult.model` records it. `GET /models` lists the options; the packs page's authoring panel
  and the runs page's rerun controls have a model drop-down, and the runs page shows each run's
  model and its steps' behaviour digests. (client: `models()`, `start_extraction(model=,
  step_models=)`, `submit_case_run(model=)`) (+~450 / -30 lines, 20 files)

- **Acra and DSCR are the defaults.** The local default tenant is `acra-lending` (was
  `acme-hospital`), whatever order `PLATO_TENANTS` lists them in (`default_tenant(tenants)`;
  `PLATO_LOCAL_TENANT` still overrides); the packs page opens on the first listed tenant (the
  default, listed first) instead of "All tenants", which names none for a write, and opens its
  draft picker on `dscr-core` (`PLATO_DEFAULT_PACK`). (+~60 / -10 lines, 6 files)

- **The SDK decides whether a draft can take rules, and rules on proposals in bulk.**
  `jazzx_sdk.pack.authoring_status.authoring_status(files)` (domain pack, assistant pack or
  neither; whether an ontology is declared) behind `GET /packs/drafts/{pack}/authoring-status`;
  `POST .../authoring/review/{pack}/decisions` gives one ruling (`approve`, optionally by `kind` or
  `category`) to every proposal the lifecycle lets a reviewer give it to, each through the same
  checks as a single decision, reporting what it refused. The packs page shows both instead of
  carrying the logic. (client: `draft_authoring_status()`, `decide_proposals()`) (+~230 lines, 9 files)

- **The packs page guides policy authoring and exports what it extracts.** A "Build a pack from
  policy documents" guide sits above the authoring panel (one tenant, a domain-pack draft, upload,
  review, merge, publish). The panel names what the open draft is: an assistant pack
  (`manifest.yaml`) or a draft with no `pack_manifest.yaml` cannot take rules, and "All tenants"
  names no tenant (a request without `X-Tenant-Id` is the server's default tenant, which is how
  drafts and rules landed in the wrong one), so Extract, Accept all and Merge are disabled with the
  reason; a domain pack's note says whether it declares an `ontology:`. New controls: **Accept all
  pending** (one `approve` decision per pending proposal, after a confirm), **Download proposals
  JSON** (every status, with rule, sources, excerpt and reasoning) and **Download draft JTBDSet**.
  Switching tenant reloads the drafts. (+~150 / -4 lines, 2 files, +4 node tests)

- **An extraction run names the step it is in, and the packs page shows it.** `ExtractionRun.stage`
  (the poll, the SSE stream and the client's contract) is the pipeline step running now, set when
  a step starts, where it was the last one finished, so a run held in a long step (segmenting a
  large document) no longer reads as the step before it. The authoring panel prints "Extracting:
  <step> (<seconds>s)" on each poll instead of a bare "Extracting...". Counts inside a step
  (sections read, rules proposed so far) are not reported yet. (+~35 / -6 lines, 5 files)

- **PR review fixes.** `DbPackReviewStore.close_open` takes the row lock the other writers take; a
  draft revert is held to the files the draft will have, not the union of both versions; the user
  directory serves a gateway 401 as `DirectoryAuthRequired` (a 401) instead of a 502; an extraction
  stream whose run disappears still ends with `end` (`status: unknown`); a rerun adjudicates a
  rule the followed run never judged (the "nothing moved" shortcut and the carry-forward both
  skipped it, leaving it indeterminate); a VIOLATED verdict resting only on rejected evidence
  reaches no answer, as a SATISFIED one already did, and conditions the model closed on such
  evidence stay open; the page tests' `<script>` pattern ignores case. (+~150 / -15 lines,
  13 files)

- **A case run's `usage` counts the document and adjudication steps, and the assessment's calls.**
  A `document_ingest` step's agent calls are metered at the `AgentExecutionService`, an
  `adjudication` step's at `ReasoningAgent`, which tells a metering service its `record_usage(model=,
  usage=)` after each call (`usage.modes.document_ingest` / `adjudication`: calls, tokens, cost), so
  `total` is the run's spend rather than the investigation's; a step with no service wired gets a
  default one, so it is metered too. `policy_assessment.calls` is the calls the reasoning agent
  made, not 1. The tenant dropdown's database read logs at debug. A `deadline` field's type is
  not checked at publish (`TODO(deadline-type-unchecked-at-publish)`). (+~120 / -15 lines, 5 files)

- **Pack-root resolution lives in `jazzx_plato_client.packs`.** `discover_root`,
  `resolve_packs_root`, `resolve_pack_root`, `PackRootNotFoundError`, `id_spellings` and the two
  constants move there with `env_text` and `bare_name` inlined (mirrored from the SDK), so an app
  that only publishes its packs finds them without importing `jazzx_sdk`; a test imports the
  module with `jazzx_sdk` blocked. `jazzx_sdk.pack.roots` re-exports the same objects, so SDK
  callers do not change. (+141 / -155 lines, 3 files)

- **The investigation deadline guard can allow a few passes inside its window.** `deadline:
  {field: sar_deadline, within_hours: 48, iterations: 2}` lets the loop run at most `iterations`
  (>= 1) investigator passes once the deadline is within the window, then stops it as a guard
  firing with reason `deadline`; without `iterations` the loop still stops at once, before pass
  one. `CaseResult.investigation` (and the client's contract) gains `iterations_after_deadline`,
  the passes run inside the window (0 when it stopped at once), None when the window was never
  entered. `DeadlineGuard.fires(ctx)` is the guard the step now wires; it counts in
  `ctx.metadata["deadline_passes"]`. (+~50 lines, 5 files)

- **The Packs and Evaluation page tenant dropdowns list the tenants that have published packs.**
  With `PLATO_TENANTS` unset, `page_tenants(db)` reads the distinct tenant ids from `pack_version`
  (`published_tenants(db)`, sorted), so a new tenant appears as soon as it has a pack; a set
  `PLATO_TENANTS` still wins, and an empty or unreadable database falls back to the wiring's rule
  (the local default tenant, or none when deployed). `packs_html` and `evaluation_html` take
  `tenants=`. A request without `X-Tenant-Id` still resolves to the first configured tenant, and
  the job roles still read `PLATO_TENANTS`. `scripts/plato-local.sh` adds `barclays` to its
  default tenant list in both profiles. (+~75 / -12 lines, 6 files)

- **A case run's `investigation` carries the final hypotheses and the evidence.** Beside how the
  loop ended, `CaseResult.investigation` has `hypotheses` (id, content as the pack's schema shapes
  it, confidence, status, and the rationale cut to `RATIONALE_CHARS` = 500) and `evidence` (id,
  type, source, the verifier's status, the quality score, and the verifier's note, which is its
  attestation's findings, else null; the payload is left out, it can be large). A run waiting at
  its checkpoint has them in the output the run view now shows, so a reviewer sees what the
  decision rests on. (+~60 lines, 4 files)

- **A case run reports what each mode cost, and an experiment can override a mode's model.**
  `CaseResult.usage` (and the client's contract) holds, per mode (`investigator`, `verifier`,
  `reasoner`, `governor`, `narrator`, and `policy_assessment` when the assessment reasoned), its
  token buckets (fresh input, cache reads, cache writes, output less reasoning, reasoning), the
  calls made, its `model` and `cost_usd` priced per call at that model, and a run `total`. A mode
  that reports no model or usage is counted and costs 0. `run_case(mode_overrides={mode:
  {model, temperature}})` lays a model or temperature over the manifest's for one run (a name that
  is not a mode, or an unknown field, is refused); the `case_run` eval entity takes it as
  `config["modes"]`, so an experiment sweeps models over a pack with no variant published and reads
  the cost back in each case's output. Submitting a case run through the route takes no override.
  Also removed: `AgentExecutionService.register_hook` and its two lists, which nothing ever invoked
  (a governance hook that never ran); no caller in japes or the sibling repos. (+~230 / -45 lines,
  8 files)

- **The investigation step can declare a deadline guard.** `deadline: {field: sar_deadline,
  within_hours: 48}` on an `investigation` step (`DeadlineGuard`) stops the loop as a guard firing
  with reason `deadline`, checked each iteration before the investigator runs, once that datetime
  input field (an ISO time or a datetime; a naive time is read as UTC) is within the window of now
  or already past; a case without the field is not stopped. It is the `InvestigationSpec.
  deadline_guard` the loop already honoured, which a manifest could not set. The publish check
  refuses a field the input schema lacks. `CaseResult.investigation` (and the client's contract)
  now says how the loop ended: `status` (`converged`, `guard_fired` ...), `guard_reason`,
  `convergence_reason` and `iterations`, None without an investigation. (+~130 lines, 5 files)

- **One public fiscal-year key for periods.** `jazzx_sdk.finance.fiscal_year(period)` (the 4-digit
  year in a label, 0 when there is none), `chronological(periods)` (oldest first; one year or no
  year keeps the given order) and `latest_period(periods)` (the most recent, the first listed of
  equals) replace three private variants: `merge_spreads`, the Excel Trends sheet and
  `validate_package` (and its continuity, reconciliation and staleness checks, which had their own
  copy returning None for no year) now all use them. (+~35 / -15 lines, 6 files)

- **Review fixes on the periods contract.** `validate_package` tagged a compliance result's
  findings with `package.periods[-1]`, the oldest period for a single filing listed most recent
  first; it now takes the latest by the year in the label, so the `periods` order really is
  irrelevant to the package (its comment said so). `token_usage` clamps the cache and reasoning
  counts too, as its docstring said, and the Trends sheet's comment says periods of one year or with
  no year keep their listed order. (+~25 lines, 5 files)

- **The Excel Trends sheet compared the wrong columns.** `finance.excel._write_trends` put the
  second period's header over a formula comparing the first period with the label column (an error,
  shown blank), so every growth figure sat one period out, and with periods listed most recent first
  the growth had the wrong sign. Each Trends column now compares a period with the one before it in
  time (by the year in its label, in the order the statement sheets list them otherwise), with the
  period's own header over it. (+~25 / -15 lines, 2 files)

- **`jazzx_sdk.agents.token_usage`, and two contracts written down.** The Agents SDK `Usage` to
  `TokenUsage` conversion `run_agent` used is public as `token_usage(usage)` (exported from
  `jazzx_sdk.agents`), with a docstring saying which counts include which: the SDK's input total
  includes cached reads and cache writes, its output total includes reasoning; `TokenUsage` holds the
  fresh input, the cache reads and writes, the output less reasoning, each clamped at zero. A caller
  that re-derived this (reading a `cache_creation_input_tokens` that `Usage` does not have) gets
  cache writes priced at their own rate by calling it. `SpreadPackage.periods` now says it is in the
  source statement's order (usually most recent first), that `merge_spreads` returns oldest first
  and that nothing in the package depends on the order, so a consumer that does sorts explicitly.
  `PolicyProfile.get` says it is not `dict.get`. (+~35 lines, 5 files)

- **A run waiting at its checkpoint shows its output.** `GET /runs/{id}` returned `output` only for
  a run that had ended, so a reviewer opening a suspended run (after a reload, or a second
  reviewer) saw no assessment, steps or decision; only the journal's suspended frame carried them.
  A SUSPENDED run's output (the same the frame carries) is now in the view; a failed run's error is
  still masked as before. The client's `case_run` docstring says so, and the runs page, which
  reads `output`, now fills in for a waiting run. (+~8 lines, 3 files)

- **The image build checked a module that had moved.** The Dockerfile's (and the document analyzer
  example's) deploy-time import check named `jazzx_sdk.evaluation.feedback_sink`, which became
  `jazzx_sdk.evaluation.feedback.sink` when the feedback service moved into the SDK, so the build
  failed at that step. Both name the new path, and `tests/test_dockerfile_imports.py` resolves every
  non-`common` module either image check imports, so a move fails a test rather than a build.
  (+~40 lines, 3 files)

- **The sealed copies of a registry are kept for the last pair only.** `AssistantRuntime` kept every
  sealed registry pair it had merged a built-in into, so a Plato alternating between tenants with
  published packs (whose registries are composed afresh on each miss) grew one entry per request.
  It now holds the last pair, as the tenant pack cache upstream does, and `invalidate_all` drops it.
  The page tests hold timers only in the test that needs them. (+~25 lines, 3 files)

- **Review round on the fixes above.** A run naming one document twice is refused in
  `document_refs` (it made the previous run's `D<n>` order ambiguous, and ingesting a file twice
  has no use). The sealed-registry fix now makes a sealed copy of the registry with the built-ins
  added (`_sealed_with`, kept once per registry pair) instead of a read-through wrapper, so
  `catalog_text`, `tier_of`, `names(allowed, roles=)` and the guardrails all see the built-in. The
  runs page stops polling a run when another is opened, and a poll that fires for a run the page has
  left does nothing. The retry feedback's validation mode is pinned by a test to the mode the SDK
  parsed in (strict for a strict schema, lax otherwise). (+~120 / -30 lines, 7 files)

- **Review fixes: a rejection reads in the followed run's frame, a parent class is met by its
  children, a sealed registry is read with the built-in.** (1) A rerun's `rejected` cites name a
  document as the run the reviewer read showed it (alias, id or filename); they are now resolved
  among that run's items (`RerunBasis.items` keeps its order, `prior_items`) and then found in the
  new run by id, where before an alias was read against the new run's positions, so dropping or
  adding a document put the rejection on the wrong document or on none. A cite naming no document
  of the followed run is refused at submit (409), and one whose document the new run no longer has
  is dropped. (2) `document_classes(item)` is a document's admitted class and each level above it in
  the taxonomy; the required-class check, adjudication texts by class, investigation evidence and a
  rerun's changed classes use it, so `required_classes: [Income]` is met by a document admitted as
  `W-2` (the publish check already accepted parents). (3) `AssistantRuntime._resolve_registries`
  registered a built-in assistant's profile into the pack's registries, which `pack_registries`
  seals, so creating any session on a Plato with `PLATO_PACK_DIR` set raised
  `RegistryFrozenError`; a sealed registry is now read through a view that adds the built-in and is
  not written, an open one is written as before. The runs page also right-aligns its numbers, keeps
  Refresh for a read-only viewer, and drops an answer for a run the page has moved off. (+~210 /
  -40 lines, 8 files)

- **Diffs are served as aligned rows, and the reviews page shows them side by side.**
  `GET {prefix}/packs/reviews/{id}/diff/rows` and `GET {prefix}/packs/drafts/{id}/diff/rows`
  (`?path=`, `?context=`, drafts also `?against=`) return each changed file as rows: old beside
  new, a changed line paired with its partner and its changed words marked (`spans`), an unchanged
  stretch folded to `context` lines (default 3) as a `fold` row that says how many lines it hides,
  and a file over `MAX_DIFF_LINES` reported `too_large` without rows. A review's rows carry the
  review's line comments on the row each ends on, with `outdated` as the comments route gives it.
  The logic is `jazzx_sdk.pack.diff.side_by_side` / `diff_rows` (pure). The client gains
  `pack_review_diff_rows` and `draft_diff_rows` with `PackDiffRows`, `FileRows`, `DiffRow`
  contracts. The reviews page renders the rows as a table (changed words underlined, a fold
  expands its file, a line number points the comment form at that line, comment threads sit under
  their line) with a unified/side-by-side switch; this closes what the reviews entry above left
  to a later UI. (+~330 / -50 lines, 11 files)

- **Plato has a scorers page, and datasets can be edited (UI U4, U5, U6).** `GET {prefix}/scorers/ui`
  (nav: Scorers): the built-in catalog (including the adjudication and split scorers), a dry run
  of one scorer on an expected and an actual value (score, pass, comment, metrics, detail;
  nothing stored), and the tenant's custom scorers: list (archived optional), open one with its
  revisions, create, save the next revision with `If-Match` set to the revision read, archive and
  restore. On the evaluation page a dataset's cases are editable as JSON and saved as the next
  version with `If-Match` set to the version read (refused if it moved on), and a dataset can be
  forked; an experiment says which experiment is its entity's baseline. The page helpers' `call`
  takes extra headers for this. (+~420 lines, 8 files)

- **Plato has a reviews page (UI U7, static form).** `GET {prefix}/reviews/ui` (nav: Reviews): the
  reviewer inbox (state, assigned to me, submitted by me, and the count waiting on the caller), a
  review's fields and event history, approve, request changes, close and resubmit; the diff
  (rule changes and each file's unified diff, added and removed lines coloured); the draft's
  comments with replies, resolve and delete, and a form that anchors a new one to a file, a line
  range or a rule; and lint: run it now, open a run, and triage each finding
  (open, accepted, fixed, wont_fix) with the errors still blocking a review named. Controls that
  write follow the routes' own gate. No in-text highlighting or side-by-side diff: those wait for
  the React app. `plato/static/shared.js` holds the tenant, identity, idempotency-key and `call`
  helpers the new pages share, inlined by the server (`__SHARED_JS__`); the runs page now uses it.
  `tests/test_plato_pages_run.py` runs both pages' scripts in Node against a stub DOM and canned
  routes (inbox, open, approve, comment, lint triage; stats, find, open, rerun with a rejected
  cite), so a thrown error or a wrong request body fails a test. (+~700 lines, 8 files)

- **An experiment shows what each scorer reported (UI U3).** The evaluation page's experiment detail
  lists the cases (failures first, with each scorer's comment or the run's error) and a table of
  every named metric across them (cases reporting it, mean, max, total), from
  `eval/experiments/{id}/cases`. The adjudication scorers' false-pass and fragile counts and the
  split scorer's error kinds appear there with no per-scorer code. (+~55 lines, 1 file)

- **The runs page shows spend and queue (UI U2).** A "Spend and queue" section reads `cost-stats`
  (by model, user or assistant over the last day, 7 or 30 days; tokens, cached tokens, cost, marked
  as an upper bound where it is one) and `queue-stats` (queued, running and suspended per lane and
  the oldest queued wait, flagged when the report may be short). It sits on the runs page rather
  than the dashboard because both routes are tenant-scoped and the dashboard has no tenant. (+~50
  lines, 2 files)

- **Plato has a runs page (UI U1, rerun P5).** `GET {prefix}/cases/ui` (nav: Runs; not under
  `/runs`, where `/runs/{run_id}` would take it). Find a case's runs by pack and subject or open
  one by id; a run shows its status, version, what it follows, steps, decision and governor, the
  adjudicated rules (verdict, conditions marked carried or resolved, evidence with a tick to
  reject it, the vote split and dissent), the documents (class, the file a part was cut from, the
  pages the split was unsure of, missing classes, conflicts), and polls until it ends or waits.
  Reviewer controls (stop, approve or decline at the checkpoint, record the outcome) and **Rerun**
  (the run's case inputs, editable, with the ticked evidence as `rejected`, on its version or one
  named) appear only where the run routes accept writes. `GET /runs/{id}` now carries the run's
  `inputs`. Guards: every static page's inline scripts are checked with `node --check`, and the
  page's routes are checked against the router's. (+~430 lines, 7 files)

- **A rerun's prompt points at what moved (rerun, P4).** `DocumentFocus` (`new` documents, `cited`
  evidence per rule) goes to `AdjudicationAgent.adjudicate(focus=)` and `run_segment`: the batch
  prompt says which documents were added since the last run, and each rule's block says what its
  last verdict cited ("Its last verdict rested on: D1 page 2"), named as this run's documents
  (the prior citations are matched through the source file, since aliases are positional and a
  rerun may have more documents). (+~60 lines, 4 files)

- **A rerun does not read an unchanged document again (rerun, P3).** `RerunBasis` carries the prior
  run's ingested items by the file they came from (`items`, replacing the class map); a file the
  rerun names that the prior run ingested takes its items from there, with no conversion,
  classification or extraction, and its fills and conflicts are recomputed from them like any
  document's. A file the prior run did not have is read as usual; one it dropped counts as changed
  for the classes it was. A run on another version reads everything. (+~50 / -30 lines, 3 files)

- **A case run can follow a prior run of the case (rerun, P1-P2).** The submit body takes
  `rerun: {of: <run_id>, rejected: {<rule_id>: [{document, page?}]}}`. The run it names must be the
  tenant's, completed, of the same pack and subject (404 for an unknown or another tenant's run,
  409 for an unfinished run, another case, or evidence rejected where the pack adjudicates
  nothing); the new run pins that run's version unless `?version=` names another, which runs in
  full. `RerunBasis` (`pipelines.rerun`) copies out what the new run reads, so it is
  self-contained: the prior record (inputs plus what documents filled), the ingested files and the
  classes they were admitted as, and the adjudicated outcomes. The `adjudication` step then
  computes what changed (record fields that differ; classes of documents the prior run did not
  ingest or no longer has), re-judges the rules that read those and the rules a rejection names,
  carries the rest verbatim, and with nothing changed and nothing rejected makes no model call.
  Rejected evidence is matched by alias, filename or id and bars the cite as in the entry above;
  `AdjudicationAgent.adjudicate` takes `reconsider` (rule ids judged whatever changed) and
  `impacted_rules` takes `force`. `GET /runs/{id}` carries `rerun_of`; the client's
  `submit_case_run(rerun=)` takes a `RerunRequest` (`contracts.RerunRequest`, `RejectedCite`).
  Plato's run keys gain `plato_rerun`. (+~420 / -25 lines, 12 files)

- **A reviewer sees the split's doubts.** A document cut from a file (`derived_from`) whose split
  classified a page under `split_review_below` is listed on `documents.unsure_splits` (the part's
  id, the file's id, its label and the file's 1-based pages in question) and on the human
  checkpoint's payload as `unsure_splits`, beside `conflicts` and `missing_documents`. It does not
  by itself set a decision's `human_review_required`. (+~15 lines, 2 files)

- **A case run can cut a combined file into its documents.** `document_ingest` takes `split: true`:
  a PDF holding several documents (a loan package, a referral packet) is split as the pack's
  `document_agent.yaml` says, each part is stored as a document of its own (`put` on the run's
  document source, content-addressed, so a part is a document the rest of the run reads like any
  other: its class counts toward `required_classes`, its text goes to adjudication under its own
  alias, its cites point into it) and ingested as one. Its item carries `derived_from`: the file's
  document id, the 1-based pages, the label, the split confidence, the weakest page's, and the
  pages under `split_review_below`. A file that is one document stays itself. `DocumentAgent.split_blob`
  (and `SplitPart`) is the blob-sourced counterpart of `process_package`'s split, which now shares
  one `_split`. (+~140 / -30 lines, 8 files)

- **Adjudication cites a document by a short alias.** The `adjudication` step marked each document
  in the prompt with its id, a 64-character content digest the model had to copy into every cite,
  and a cite whose id came back altered was dropped without a trace. The marker is now
  `=== document D2 (lease.pdf) ===`; a cite resolves by alias (`D2`, also `D2 (lease.pdf)`),
  filename or the full id, and one naming no run document still drops. (+~45 / -6 lines, 2 files)

- **A rerun cannot silently drop a condition.** `AdjudicationAgent.adjudicate` hands each re-run
  rule the conditions its prior outcome left open (`narrative["conditions"]`, via
  `prior_conditions` on `run_segment`); the prompt asks the model to restate each one the evidence
  does not resolve and to list under `resolved` each it does. A prior condition the answer neither
  restates nor resolves stays on the verdict (`narrative["carried_conditions"]`), and one it
  resolves is dropped and recorded (`narrative["resolved_conditions"]`); matching is by text with
  case and spacing ignored. Before, a rerun replaced the verdict wholesale and an omitted
  condition vanished with no record that anything had closed it. Only a procedure condition carries
  conditions, so a yes/no rule is unchanged. (+~110 / -3 lines, 4 files)

- **The adjudication and split scorers are in the standard catalog.** `standard_scorers()` registers
  `adjudication_verdict_agreement`, `adjudication_vote_stability` and `document_split`, so
  Plato's scorer catalog lists them and an experiment or template can name them. (+~12 lines, 3 files)

- **A stray page or cover sheet can be folded into the document it belongs to.** `split_document`
  takes `attach_below` and `continues`: a run of at most `attach_below` pages is merged into the
  longer neighbour (the longer is tried first and lends its label) when `continues(before, after)`,
  asked over the earlier run's last page and the later run's first, says it carries that document
  on. Differing printed identities (`identity_of`) on those two pages veto the merge without a call;
  a decision is asked once per boundary. `continuation_check(agents)` is the model-backed check
  (one call per boundary, `CONTINUATION_SAMPLE_CHARS` of each page); `DocumentAgentSpec.split_attach_below`
  (default 0, off) turns it on in `process_package`. Until now a split only ever cut, so a
  mislabelled page inside a form made three documents of one. Text route only: the vision route has
  no page text to compare. (+~150 / -3 lines, 5 files)

- **A taxonomy can have levels.** A class takes `children` (a `DocClass`, or `{"label", ..., "children":
  [...]}` in a pack's taxonomy), and `classify_path` classifies into the top level and then, one
  model call per level, into the children of the class chosen, from one conversion and one text
  sample. It stops where the model names no child or answers under `min_confidence`, keeping the
  parent as the answer and naming it in `TaxonomyPath.terminated_at`; its `confidence` is the least
  confident level's. `DocumentAgent` descends a taxonomy that has children with `admission_floor`
  as the floor and records the path on `DocumentResult.doc_type_path` (empty for a flat taxonomy,
  which takes the one call it always did); `doc_type` stays the deepest label reached. `split_document`
  classifies pages against the top level only. `classify_document` is unchanged and ignores
  children. (+~170 / -20 lines, 6 files)

- **A split can be scored.** `jazzx_sdk.evaluation.split_scorers` (`SplitScorer`, `split_scorers()`,
  exported from `jazzx_sdk.evaluation`) judges each expected document as match, wrong label,
  boundary (ends differ), over split, under split or missed, counts the segments that overlap no
  expected document as extra, and reports the share of pages labelled as expected. The score is the
  share of expected documents matched; a wrong label under the right top level of a `/`-separated
  label path earns half. It fails on a missed document. `actual` and `expected` read as
  `DocumentSegment`s, `SegmentResult`s, dicts or a package-shaped `{"segments": [...]}`. (+~190 lines, 3 files)

- **A reviewer's rejected evidence cannot be cited again.** `AdjudicationAgent.adjudicate` and
  `run_segment` take `rejected` (`RejectedEvidence`: `{rule_id: [EvidenceCite]}`, a document, or one
  page of it). The rule's prompt block bars the evidence by name; a cite of it is dropped from the
  verdict, and a SATISFIED verdict that rested only on rejected cites becomes INDETERMINATE
  (`evidence_missing`) with the rejected cites recorded, so a rerun cannot re-clear a rule on the
  page a reviewer threw out. A rejection for another rule changes nothing. The `adjudication` case
  step does not pass rejections yet: a case run has no input for them. (+~110 / -8 lines, 3 files)

- **A schema retry says where the response failed, not only that it did.** With model data
  redacted (the agents SDK's default) a `ModelBehaviorError` carried no location, so the retry
  message told the model its answer was invalid without saying which field. `run_kit.ValidatedOutput`
  (an `AgentOutputSchema`) raises each failure as the location and message of up to
  `MAX_FEEDBACK_ERRORS` (8) pydantic errors, and never a value from the response; `validated_output`
  wraps a type or a schema (strictness kept; plain text and raw JSON schemas pass through).
  `run_agent` and `InteractiveAgent`'s output type go through it; `OpenAIProvider.build_agent` runs
  no retry loop and is unchanged. (+~95 / -3 lines, 4 files)

- **A split segment names the pages it was least sure of.** `DocumentSegment` carries `weakest` (its
  least confident page) and `review_pages` (0-based pages under `review_below`); `split_document`
  takes `review_below`, `DocumentAgentSpec.split_review_below` (default 0.5, `None` flags nothing)
  supplies it to `process_package`, and `SegmentResult` carries `weakest_confidence` and
  `review_pages`. `PackageResult.needs_review()` lists the segments with any. The mean
  `split_confidence` hid one bad page inside a confident run; a bookmark split has no per-page
  evidence, so its `weakest` is the segment's own confidence and it flags no page. (+~60 / -6 lines, 6 files)

- **A replicated verdict keeps its vote split, and adjudication has scorers.** With more than one
  replica `run_segment` records `inputs["votes"]` on each rule's outcome: votes considered, replicas
  excluded, the count per status, and the status and rationale of every vote that lost (no key for a
  single replica, so k=1 output is unchanged). `jazzx_sdk.evaluation.adjudication_scorers`
  (`adjudication_scorers()`, exported from `jazzx_sdk.evaluation`) scores an `adjudication` run:
  `VerdictAgreementScorer` (share of rules at the expected verdict; fails on a false pass, a
  SATISFIED where VIOLATED was expected, the costly error) and `VoteStabilityScorer` (share decided
  unanimously, and the count of fragile splits within `fragile_margin` votes). Expectations are a
  `{rule_id: verdict}` map, or a golden case's blob carrying it under `verdicts`. (+~230 / -2 lines, 5 files)

- **PR #89 review comments** (bot, `dev` -> `main`). Fixed: an `assistant_session` eval case whose
  `turns` is a string was iterated by character (it must be a non-empty list); a turn that fails
  (or raises) now still closes the session recording; `InProcessTurnRunStore.expire_suspended`
  re-reads each run as `reap_stale` does. Not changed: the in-process store's `claim_suspended`
  against `request_stop` interleaving (no method awaits anything that suspends, so each runs to
  completion; the class docstring says so), and the rename `workstation_python_executor` to
  `local_python_executor` (deliberate, listed above; no alias for an unreleased version).
- **sqlite: two runs of one key could be claimed at once** (PR #89's pytest failure,
  `test_concurrent_claims_on_sqlite_have_one_winner[mixed]`). The claim's compare-and-set covered the
  claimed run's own status only. A racer that had read the key idle and then read its head after
  another had committed took the next queued run, so both ran. `_claim` now also requires that no
  run of the key is RUNNING, in the same UPDATE (sqlite takes no key lock; Postgres' advisory lock
  is unchanged and the extra predicate is harmless there). The race test staggers its racers so the
  late-reader case happens every run (10 claims before the fix) instead of by timing.
- **The client version is shown beside Plato's.** `plato._version.client_version()` reads the
  installed `jazzx-plato-client`'s `__version__` (None when it is not installed); `/info` carries it
  as `versions.plato_client`, the dashboard's Versions panel lists "Plato client", and the entry
  point's `--check` output as `client_version`. The packs page now always lists each pack's
  `X-Tenant-Id` (the column was hidden for a single tenant), and a version's detail row names the
  header (`X-Tenant-Id: <tenant>`) its request already carried, so selecting a tenant first is not
  required. (+~40 / -6 lines, 7 files)
- **Review of the 2.6.1 range** (`origin/plato...HEAD`; slices 1 and 2 blocked). Fixed: replaying a
  draft's history starts at the last reset at or before the revision, so a pack whose old draft
  text was pruned can be reopened and still diff, revert and review (410 before); the authoring
  chat's tools need the author role where the routes do (a viewer could start an extraction
  through the chat); deleting a comment removes every reply under it, not only the direct ones;
  a local publish of an approved review that matches the draft marks it published, and a direct
  publish closes an approval the draft outgrew (it held the pack's review slot); a comment's
  `review_id` must be a review of the same pack (404); `/whoami` `may_review` follows the posture
  as `may_author` does; the lint-run list defaults to the store's limit constant; the gateway
  directory counts `$skip` by records read; `contracts.__all__` lists each model once and the
  five it left out; an unused constant. Tests: the retention test reads a pre-reset revision, a
  fixed-clock stats test, a pasted assert, an unclosed client, and the strict gate test no longer
  exempts the samples list. Left, as a `TODO(streamed-cost-user-from-context)`: a drained queued
  turn is costed to the draining request's user.
- **Testing a draft on the eval plane** (plan_plato_authoring_review P7; the workbench's "Test with
  MACER", no MACER integration). An `adjudication` eval entity beside `pack` and `case_run`:
  `AdjudicationInvoker` runs the SDK's `AdjudicationAgent` over the pack's active live rules with
  the case input as the record (`config.model` and `config.replicas` override the agent's), and
  `config.version` names a published version or `config.draft` the digest of an unpublished draft.
  `pinned_draft_pack` hands the draft out only while its content digest is the pinned one: it
  refuses on entry, and discards a case's result when the draft moved while the case ran, so a
  result names what it tested (`output.draft`, `output.pack_version`). `GET /packs/drafts/{id}`
  now carries the draft's `digest`. `PLATO_ADJUDICATOR_URL` swaps in `ExternalAdjudicationInvoker`,
  which POSTs `{pack_id, pack_version, draft, rules, input}` and takes the JSON answer as the
  output, so a MACER-style service is configuration. Starting an `adjudication` experiment takes
  the reviewer role (`before_start` on the experiments router; other entity types are not
  gated). Results are ordinary experiments, so compare and baselines apply. No new client
  method: `create_experiment` and `start_experiment` already take any entity type. Not done: the
  external adjudicator's request contract is this one, unconfirmed with any such service.
  (+~330 / -5 lines, 7 files)
- **User and reviewer lookup** (plan_plato_authoring_review P6, gap 8). `UserDirectory` seam in
  `jazzx_sdk.server.directory`: `GatewayDirectory` reads the platform gateway's `GET /auth/user`
  with the caller's own bearer token (pages of `DIRECTORY_PAGE_LIMIT` until the total, the same
  OData paging and field mapping the workbench uses) and filters reviewers by the configured
  reviewer role; `StaticDirectory` for tests; `SeenUsersDirectory`, the default without
  `PLATO_DIRECTORY_URL`, offers the user ids seen in reviews and drafts (those named or deciding a
  review are the reviewers; ids only, no names). No user table. `GET /users?q=&limit=` and
  `GET /reviewers`, withheld in a strict posture without auth, answers capped at
  `DIRECTORY_PAGE_LIMIT`; a missing token for the gateway is 401, a gateway failure 502 (the error
  class only, never the body). Client: `search_users`, `list_reviewers`; contract
  `DirectoryUser`. (+~330 / -0 lines, 8 files)
- **JTBDSet export** (plan_plato_authoring_review P5, gap 7). `export_pack_jtbdset` writes a
  pack's policies as a JTBDSet; `GET /packs/{id}/{version}/jtbdset` for a published version and
  `GET /packs/drafts/{id}/jtbdset` for a draft (version `draft`), withheld in a strict posture
  without auth like the other pack reads, 404 for an unknown pack, version or draft, 422 with the
  reason when the set cannot be exported (a product-scope policy no program claims, a draft that
  does not load). Programs come from overlay policies, so a program with no overlay is not
  exported. Export only: no Knowledge Hub publish and no link table until a consumer names the
  contract. Client: `export_jtbdset`, `export_draft_jtbdset`; contract `JtbdSetArtifact`.
  (+~170 / -0 lines, 7 files)
- **Lint runs of a draft, with triage** (plan_plato_authoring_review P4, gap 6). `run_lint` lints the
  draft as it is and `DbLintRunStore` keeps the run (table `pack_lint_run`, migration
  `0020_pack_lint_run`: revision, draft digest, who ran it, the report, error and warning counts).
  A finding is keyed by a hash of its code, subject and detail, so triage (`pack_lint_triage`,
  keyed by tenant, pack and finding key; `open`, `accepted`, `fixed`, `wont_fix`, a note, who and
  when) belongs to the pack and holds for any later run with the same finding; a finding whose
  text changed starts again as open. An error blocks until `accepted` or `wont_fix`. A draft that
  does not load lints as one `draft_does_not_load` error. Routes: `POST` and `GET
  /packs/drafts/{id}/lint-runs`, `GET /packs/lint-runs/{run_id}` (findings with key and triage,
  `blocking`), `PUT /packs/lint-runs/{run_id}/findings/{key}` (author or reviewer role; 404 for a
  key the run lacks, 422 for a status outside the four). Submitting a review lints the draft and
  keeps the run (`lint_run_id` in the answer); a deployed Plato answers 422
  `lint_errors_untriaged` with the findings while an error is untriaged, a local one only lists
  them. Client: `run_pack_lint`, `list_pack_lint_runs`, `get_pack_lint_run`,
  `triage_lint_finding`; contracts `PackLintRun`, `LintFindingState`. (+~590 / -3 lines, 10 files)
- **Comments on a draft's content** (plan_plato_authoring_review P3, gap 5). A comment sits on the
  draft, a file, a line range (`{"kind": "line", "start", "end"}`, with the file) or a rule
  (`{"kind": "rule", "policy_id", "rule_id"}`, the structured address the workbench's graph-node
  anchor lacks); `DbPackCommentStore` (table `pack_comment`, migration `0019_pack_comment`: a
  surrogate key with a tenant-scoped unique `comment_id`) records its author, body, the draft
  revision it was made at, the review it belongs to (the pack's open one unless named) and an
  edit and a resolved stamp. Nothing is re-anchored on the server; the list says each comment is
  `outdated`: a line range's file has events since its revision, or its rule is no longer in the
  draft. Routes: `GET/POST {prefix}/packs/drafts/{id}/comments` (`review_id`, `path`,
  `include_resolved`), `PATCH {prefix}/packs/comments/{id}` (`body`, its author only; `resolved`,
  an author or reviewer), `DELETE .../comments/{id}` (its author or a reviewer; its replies go
  with it). Adding validates the anchor against the draft (422 for an unknown rule or policy, a
  line anchor without a path or past the file's last line, a backwards range, a path the draft
  lacks) and a reply takes its thread's file, anchor and review. Commenting needs the author or
  the reviewer role; reading is open. Client `list_draft_comments`, `add_draft_comment`,
  `update_draft_comment`, `delete_draft_comment`; contract `PackComment`. `pack.diff.rules_in`
  is now public. Tests (sqlite and Postgres where run): the store with edits, resolution, a thread
  and two tenants; anchors, `outdated`, replies, rights and tenant isolation through the client;
  each of the rule check, edit-own, delete rights, `outdated`, the role gate and reply inheritance
  fails its test when removed.

- **Draft history, diff and revert** (plan_plato_authoring_review P2, gap 4). Each change to a
  draft is one `pack_draft_event` row (`opened`, `write`, `delete`, `revert`, `reset`; paths,
  actor, before and after hashes and text; migration `0018_pack_draft_event`) written in the
  transaction that made it, so a failed event leaves no write; a write of what is already there
  records nothing. An event's id is the draft's revision. `DbPackDraftStore` gains `revision`,
  `events` (paged by cursor, of one file if asked), `files_at` / `file_at` (replayed from the
  events; a `reset` starts again), `revert` (a file or the whole draft back to a revision, a
  `revert` event per file that changes, history only ever added to; reverting to when a file did
  not exist deletes it) and `prune_event_text`. `UnknownRevision` and `EventTextPruned` are
  `ValueError`s, so the routes' store wrapper does not turn them into a 503. New pure
  `pack.diff.diff_files(base, head)`: per file added, removed or changed with a unified diff and
  counts, and per rule (policy id, rule id) added, removed or changed, read from any YAML file
  holding policies. Routes: `GET {prefix}/packs/drafts/{id}/events` (`after`, `path`, `limit`;
  `next` cursor and the newest `revision`), `GET .../diff?against=base|revision:N` (404 unknown,
  410 text dropped, 422 malformed), `POST .../revert` (author), and `GET
  {prefix}/packs/reviews/{id}/diff`, the draft as it was when the review pinned it
  (`pack_review.head_revision`, also in 0018) against the version it was opened from. A
  discarded draft's old events lose their text after `PLATO_DRAFT_EVENT_TEXT_DAYS` (30; hashes
  stay; an open draft keeps all), swept by the existing `job:run-reaper`. Found building it: a
  review still `open` whose draft had changed could not be resubmitted, so it was stuck behind
  `review_stale`; resubmit is now legal from `open` too, when the draft changed (409 otherwise).
  Client `draft_events`, `draft_diff`, `revert_draft`, `pack_review_diff`; contracts
  `DraftEvent`, `DraftEvents`, `PackDiff`, `FileDiff`, `RuleChange`, `PackReview.head_revision`.
  Tests (sqlite and Postgres where run): event per change with hashes, replay and revert against
  hand-written states, atomicity with an injected failure, unified text and rule changes written
  out by hand, retention, the history over HTTP with pagination, the review diff keeping its pin;
  each of event recording, the replay reset, the no-op rule, the pin and the revert gate fails its
  test when removed.

- **Pack review: a draft is reviewed before it is published** (plan_plato_authoring_review P1, gaps 2
  and 3 with section 9). A **review** pins the draft it was opened on by digest (`draft_digest`, over
  paths and contents); an approval stands only while the draft still has it. States `open`,
  `approved`, `changes_requested`, `closed`, `published`, moved by the table in
  `pack.review.next_state` (a resubmit re-pins the draft, out of `changes_requested` or out of an
  approval the draft has outgrown); `DbPackReviewStore` (table `pack_review`, one `open` or
  `approved` review per pack by a partial unique index, events kept on the row; migration
  `0017_pack_review`). Routes: `POST/GET {prefix}/packs/drafts/{id}/review`, `GET
  {prefix}/packs/reviews` (`state`, `mine`, `assigned=me` for the inbox: assigned to the caller or
  to nobody), `.../reviews/pending-count`, `.../reviews/{id}`, `.../decision` (`approve` or
  `request_changes` with a note), `.../close`, `.../resubmit`; each answers `stale` (the draft moved
  on). **Publishing a draft needs an approved review where it is required** (`require_review`, else
  a strict posture): 409 `review_required` or `review_stale`; locally it needs none, and an open
  review a direct publish supersedes is closed "published directly". The answer carries
  `review_id`. **Roles** from the gateway: `CallerIdentity.roles` (decoded `x-security-context.roles`
  or the roles header), `AuthoringRoles` (`PLATO_REVIEWER_ROLE`, `PLATO_AUTHOR_ROLE`,
  `PLATO_ROLES_HEADER`, `PLATO_REVIEW_ALLOW_SELF_APPROVAL`); `whoami` gains `roles` and
  `may_review`, and `may_author` honours the author role; a configured author role (unset: any
  authenticated caller may author, strict included) gates every pack, draft and authoring write, deciding needs the reviewer role, and a reviewer may not approve
  what they submitted when deployed. **`created_by`** on `Proposal` (first proposer kept when a rule
  is proposed again), `ExtractionRun` and `pack_draft.created_by_user_id`, stamped from the caller
  by the extraction route, the authoring chat's tools and the draft store; `ProposalView` shows it.
  The family check `test_plato_route_gates` enumerates every `/packs` and `/authoring` route in a
  strict posture without auth and found two ungated reads: `GET /packs/{id}/history` (audit actors)
  and `GET /packs/{id}/active` now withhold like their siblings. `pack_comment` arrives with its
  routes (P3), not here. Client: `submit_pack_review`, `pack_review`, `get_pack_review`,
  `list_pack_reviews`, `pack_review_pending_count`, `decide_pack_review`, `close_pack_review`,
  `resubmit_pack_review`; contracts `PackReview`, `PackReviewEvent`, `PendingCount`, `WhoAmI.roles`
  and `.may_review`, `created_by` on `ExtractionRun` and `ProposalView`. Tests (sqlite and Postgres
  where run): every (state, verb) pair against a hand-written table, the store, the full strict
  flow through the client (unreviewed, open, approved, stale after an edit, resubmitted,
  published), self-approval, roles, one tenant, local publish; each of the publish gate,
  self-approval refusal, reviewer role, author role on pack writes and on authoring writes, the
  partial index, the stale check and the creator rule fails its test when removed.

- **Queue and cost statistics** (Plato vs policy-workbench, gap 12). `GET {prefix}/queue-stats`:
  this tenant's active runs by lane and status and the oldest queued wait, from the new
  `TurnRunStore.active(limit=)` (queued, running, suspended; `ACTIVE_STATUSES`), filtered by the
  tenant each run's input carries (`truncated` when it read `ACTIVE_RUN_LIMIT`). `GET
  {prefix}/cost-stats?group_by=model|user|assistant|day&since=&until=`: one `CostRecord` per model
  that served a turn (`llm.turn_cost.turn_cost_records`), written best-effort at the end of a
  blocking and a streamed turn into the new tenant-keyed `japes_turn_cost` table through
  `DbTenantCostStore(db, tenant_id=)` (migration `0016_cost_record`; the shared `cost_record` table
  has no tenant key, which Plato's tenancy rule refuses), summed by `summarize` over the last
  `COST_WINDOW_DAYS` unless `since` is given. `ModelCallLedger.usage()` gains `tokens_by_model`
  so each record names its own tokens. **Streamed agentic turns now report usage**: the streamed
  run had no ledger, so a streamed reply (what a UI uses) carried no usage and no cost; it now
  does, and its final event carries it (`TODO(single-shot-stream-usage)`: a skill-less streamed
  turn still reports none). Client `queue_stats`, `cost_stats`; contracts `QueueStats`,
  `CostStats`, `TurnUsage.tokens_by_model`. Tests (sqlite and Postgres where run): queue counts by
  lane, the store's active listing, record building and grouping, cost recorded and read back for
  a blocking and a streamed turn, another tenant sees neither report, the store's per-tenant
  isolation; each of the cost write, the
  cost tenant filter, the queue tenant filter and the streamed write fails its test when removed.

- **Extraction progress over SSE** (Plato vs policy-workbench, gap 11). `ExtractionRun.stage` is the
  pipeline step that last finished, written through the new run-store `progress` (which counts as a
  heartbeat and leaves an ended run alone) from the extraction's `on_step`. New
  `GET {prefix}/authoring/extract/runs/{run_id}/stream`: one `run` event per change and a last
  `end`, a `: keepalive` comment while quiet, read from the store so any replica serves it, 404 for
  another tenant's run. `jazzx_sdk.server.sse` now holds `SSE_HEADERS`, `frame` and `keepalive`
  (Plato's assistant routes and `run_routes` used their own copies). Client
  `stream_extraction_run`; contract `ExtractionRun.stage`. Tests: stages in order then `end` (a
  background task moves the run), another tenant, an ended run, and `progress` on the in-process,
  sqlite and Postgres stores (the heartbeat assertion fails if the DB store drops it).

- **`jazzx-plato-client` covers the caller-facing routes** (request from jaci's Domain tab).
  New methods, 59 in all, in mixins of `PlatoClient` (`_authoring`, `_eval`, `_feedback`, so
  `client.py` stays the core): policy authoring (`start_extraction`, `extraction_run(s)`,
  `proposals`, `proposal`, `proposal_summary`, `decide_proposal`, `proposal_comments`,
  `add_proposal_comment`, `merge_rules`), pack drafts (`drafts`, `draft`, `open_draft`,
  `write_draft_file`, `delete_draft_file`, `discard_draft`, `publish_draft`,
  `retire_pack_version`), evaluation (custom scorers and their revisions, scoring, dataset versions,
  update and fork, experiment list, compare, baseline and rerun, optimizations, templates),
  feedback (list, item, update, delete, review, history, duplicates, similar, export, aggregate,
  to-dataset), feedback configuration (stored, default, per entity) and formal checks. Contracts for
  the authoring shapes: `ExtractionRun`, `ProposalView`, `QueueSummary`, `ProposalComment`,
  `RuleMergeResult`. The built-in authoring assistant is served by the existing `assistants`,
  `chat` and `stream_chat`. A route-parity test calls every public method against a recorder and
  compares it with a real app's route table in both directions, so a method that calls a route the
  server does not serve, or a caller-facing route with no method, fails; the operator consoles,
  database, settings and seeding routes and the HTML pages are listed as excluded there. An
  end-to-end test runs the authoring loop through the client against a real app. Not covered: the
  vocabulary `merge` route (Plato does not mount it) and `feedback/{id}/process` (not mounted by
  default). `datasets()` and `dataset()` still take none of the filters the server accepts.

- **The authoring chat is an assistant every tenant has** (Plato vs policy-workbench, gap 1)
  (+191 / -46 lines tracked, plus 2 new files). `policy-authoring` is a built-in assistant, so the
  assistant routes serve it: `chat`, `chat/stream`, sessions, traces, releases, skills, stop. New
  `AssistantRuntime.add_builtin(BuiltinAssistant)`: its profile and skills join every tenant's
  registries, its manifest is stored for a tenant that has none under that id (a tenant's own wins),
  and `extra_for(tenant)` adds that tenant's tools to the agent, which is how the five authoring tools
  bind to a tenant's stores. `Skill.tool` exposes one catalog tool directly with no sub-agent; manifest
  validation and `bind_spec` accept only registry or def skills, so a manifest could not carry the bare
  tools before. A tool skill's route schema is the catalog tool's (or its declared `inputs`), and the
  inventory reports it as kind `tool`. `jazzx_sdk.server.authoring_assistant.authoring_builtin` builds
  the manifest (`SPECIALIST`, `ASSISTANT` surface, `L1_RECOMMEND`: it files proposals only), the
  profile and the skills. In Plato one `PolicyExtractionService` (`plato.api.authoring.
  authoring_service`) now serves both the authoring routes and the chat tools, so a chat
  `start_extraction` run is the router's run, with the same model, lint and relevance settings.
  The tools take a `before_write` hook and Plato passes `write_gate`, so the chat refuses the writes
  the routes refuse (a strict posture without auth) and answers `REFUSED`. Not attributable yet:
  neither `ExtractionRun` nor `Proposal` records who created it. Tests: the chat reaches the router's
  run list and review queue and another tenant sees neither, one shared service (fails against a
  second one), the builtin yields per-tenant tools, a tenant's own manifest is kept, the gate refusal
  starts nothing, and the `Skill.tool` unit cases.

- **fastapi is optional** (extras `server` and `plato`; `starlette` stays core, since
  `openai-agents` requires it). With `common` at `0cc5712` nothing the SDK reaches outside
  `jazzx_sdk/server/` and `config/posture.py` imports fastapi, so a consumer using only the SDK no
  longer installs it. **Breaking** for a consumer relying on japes for fastapi: install
  `japes[server]` or declare it (juno, macer and jazzx-assistant already do). `annotated-doc`,
  fastapi's helper, goes optional with it. Guards: `test_only_server_modules_import_fastapi_at_
  module_scope` (AST, every SDK module) and `test_the_sdk_core_imports_without_fastapi` (fresh
  interpreter, fastapi blocked); both fail on a planted import. Stale comments fixed: the
  telemetry-instrumentor note in `pyproject.toml`, the Dockerfile's "fastapi is core", and the
  import-boundary docstring's claim that `common` pulls fastapi.

- **Feedback export window, stated as it is.** `iter_feedback` claimed later inserts cannot shift
  pages; capping `until` at the export start only drops records *created* after it, and a record
  created before but committed mid-export still shifts offset pages by one (a duplicate at a page
  boundary, double-counted by `aggregate_feedback`). Docstring narrowed;
  `TODO(export-window-not-insert-stable)` (HTTP race window is milliseconds; no shipped in-process
  caller appends a pre-built `Feedback`).

## [2.6.0] - unreleased

Plato 0.2.0; `jazzx-plato-client` 0.2.0. Cut as a minor version for the separate client
distribution (begun as 2.5.8).

- **Review of `b23c4663..26183127`** (slices 3 to 8; 1 and 2 got no verdict after a network drop,
  9 sat past the 8-slice cap). `schema_model` raised `TypeError` for a `type` list and
  `RecursionError` for a recursive `$ref`, which the publish-time slot check (catching `ValueError`)
  and `skill_io.typed_inputs` (whose untyped fallback it bypassed) let through; both now raise
  `ValueError` (a `type` list is refused, use `anyOf`; a `$defs` cycle is refused when the builder
  is made). Four docstrings the trim made wider than the code: `ModalClauseExtractor` is the
  `obligations` representation's extractor, not test-only; `DbSettingsStore.write` applies
  bootstrap keys without persisting them; `split` with `vision` still raises when no page carries
  an image; `schema_facts` checks top-level properties only. `TODO(composite-live-child-unflagged)`
  on `AllOfEvaluator`. Full rerun, slice 2: a typed composed skill whose nested turn raised
  aborted the parent turn (`typed_skill_tool` caught only `ValidationError`); it now hands the
  model the SDK's error string, as the untyped and `as_tool` paths do. `Skill.spec_ref`'s comment
  names the fields it ignores (not `inputs`, `description`, timeouts). `TODO(bare-tool-route-
  requires-defaults)`; `TODO(inline-schema-refs-unresolved)` now says when it occurs.
  Slice 8: the up-front `$defs` cycle walk was exponential on shared refs and raised
  `AttributeError` for a non-object `$defs`; replaced by an in-progress check where a `$ref` is
  resolved (the existing memo keeps it linear), `admits_null` memoised per def (it was itself
  exponential through `anyOf` refs, before this work too), and a non-object `$defs` refused as
  `ValueError`. `is_readable` and `default_components` docstrings narrowed to the code.

- **urllib3 2.8.0** (floor `>=2.8.0`; Dependabot #129-#131: unbounded chunk-size line, HTTPS proxy
  TLS config, chunked deflate loop). PyJWT is already 2.15.1 here (#126-#128, #132, #133 are
  `main`'s 2.13.0 lock and close when 2.6.0 reaches `main`). README: changes land on `plato`, then
  `dev`, then `main`.

- **`common` submodule to `0cc5712`** (common #220 to #230: telemetry imported only when an
  exporter is configured, tornado CVE bump, GCRA admission control, Kafka producer reuse, SAS start
  time omitted, OTel log trace-context fix). Nothing japes imports was removed
  (`utils/redis_rate_limiter.py` is gone; japes never used it). `common`'s own OTel pins do not reach
  japes, which declares its own. Two `test_common_submodule_deps` parameters drop out because
  `common.utils.telemetry` no longer imports the FastAPI instrumentor at module scope. Unrelated
  to KH's rego removal, which rides the separate `knowledge-hub-client` pin.

- **Comments and docstrings cut to a minimum** across the non-test Python files v2.6.0 changed
  (+3168 / -13664 lines, 190 files). Rationale, history, cross-repo and customer references, spec
  citations and restating comments removed; `Author:` lines, `TODO(slug)`s and `noqa` kept. Code is
  unchanged: every file's AST, docstrings stripped, equals HEAD's. Docstrings that render elsewhere
  changed with it: `plato --help`, route descriptions in the OpenAPI documents, and pydantic model
  descriptions in JSON schemas. One test asserted the migrate route's old wording and now asserts
  its 403 contract. Left as they were: attribute docstrings (the AST check reads them as code),
  `@function_tool` docstrings (they are prompt text), and string literals.

- **Typed skill tools; every skill gets a route** (Plato service Phase 3, stage 2) (+276 / -34
  lines, 9 files, the `pack/schemas.py` move counted as its edits). A skill declaring `inputs` now
  reaches the parent model as a tool typed by them: a def-backed skill's `as_tool` gets
  `parameters=` a pydantic model built from the schema, and a composed (`spec_ref`) skill becomes a
  `FunctionTool` with that model's strict schema, asking the nested assistant with the validated
  arguments' JSON (a null for an omitted optional is dropped). The model comes from
  `schema_model`, the pack-schema builder, moved to `jazzx_sdk.util.schema_model` so `agents` can
  import it (`pack.schemas` re-exports it, paths unchanged); `additionalProperties: false` is
  dropped first, since a strict tool schema implies it. Inputs outside that subset, or that fail
  the SDK's strict conversion, keep the untyped tool with a warning. A skill without `inputs` is
  unchanged (its tool schema is asserted equal to the SDK's own default). New
  `agents.interactive.skill_io` (`typed_inputs`, `typed_skill_tool`, `UNTYPED_SKILL_INPUTS`).
  Routes: a def-backed skill without `inputs` is now invocable with body `UNTYPED_SKILL_INPUTS`
  (`{"input": str}`, the text its tool takes); a bare-name skill with the catalog tool's own
  `params_json_schema` (`InteractiveAgent.skill_tool`), not invocable when the catalog lacks it.
  Visibility and scope still refuse. No seed or jaci assistant skill declares `inputs`, so their
  tools are unchanged and they gain routes only. Tested at the tool boundary through
  `invoke_function_tool` with a real `Agent.as_tool` (structured args reach the sub-agent; an
  out-of-schema argument never does); no live model call.

- **Skill invoke: what makes a skill invocable, tightened** (review of `cd61f0f4..54600ce6`). A
  skill of an assistant whose profile needs `scope` was listed invocable and published in the
  OpenAPI document, yet every invoke failed (`respond` refuses a turn missing required scope, and
  an invoke carries none); it is now not invocable, naming the scope. A skill whose `inputs` is not
  valid JSON Schema made both routes answer 500 (`UnknownType` from the validator); `skill_endpoints`
  now runs `check_schema` and marks it not invocable with the schema error. A skill action whose
  skill a new release dropped between start and claim now fails its run ("no longer invocable")
  instead of completing with no skill offered. `_CurrentCanonical`, whose docstring claimed a
  rebuildable fabric nothing rebuilds, is gone: the trace route reads `runtime.fabric.canonical`.
  `TODO(inline-schema-refs-unresolved)` in `skills_openapi`: a skill schema's local `$ref`s resolve
  against the document root once inlined (no seed skill declares `$defs`).

- **Per-assistant OpenAPI** (Plato service Phase 3, stage 1, task 3) (+75 / -2 lines, 5 files).
  `skill_invoke.skills_openapi(endpoints, base=, title=, version=, description=, reply_schema=)`
  writes an OpenAPI 3.1 document (`OPENAPI_VERSION`; its schemas are JSON Schema 2020-12, as
  `Skill.inputs` is) with `invoke` and `actions` per invocable skill, the request body the skill's
  `inputs`. Plato `GET {prefix}/assistants/{aid}/openapi.json`, `info` from the manifest's name and
  description and `version` the bound release (`unreleased` when none). The test round-trips it:
  a body the document's schema accepts is accepted by the route it names. No OpenAPI validator is
  installed, so the document's shape is asserted, not validated against the 3.1 meta-schema.
  Client `assistant_openapi`.

- **Skill actions: 202 and an operation to poll** (Plato service Phase 3, stage 1, task 2)
  (+148 / -10 lines, 6 files). `POST {prefix}/assistants/{aid}/skills/{skill}/actions` validates as
  invoke does (404, 422 before any model), then starts a run on the streamed chat's
  `ChatCoordinator` under a queue key of its own (`action:<uuid>`, so actions run beside each
  other) and answers 202 `{operation_id, status}`; the operation id is the run id, so the run
  store's claim, heartbeat, reaper and journal are the operation's. The run's turn spec pins the
  skill (`PinnedAgent`) and its terminal event carries `skill`, `skill_ran` and `skill_output`.
  `GET {prefix}/operations/{id}` answers `{operation_id, assistant_id, skill, status, done,
  result}` (`result` the terminal event once done); a run of another tenant, or one that is not a
  skill action, is 404. Needs the streaming wiring (a run store). `runs.ChatTurnSpec.terminal` is
  now read when the run ends, not copied when the spec is built, so `on_complete` may add to it.
  Client: `start_skill_action`, `operation`, `contracts.Operation` (held to the route's keys).

- **Skills invoked over HTTP, as governed turns** (Plato service Phase 3, stage 1, task 1)
  (+411 / -27 lines, 9 files). The user decided (2026-10-02) that an invoke runs a normal chat turn
  whose router may select only that skill, not a direct call: guardrails, hop authorization,
  cost, the leak check and the turn's trace apply exactly as on `/chat`, so no ungoverned path
  around an assistant exists. `agents.interactive.skill_invoke`: `skill_endpoints(agent)` (a skill
  is invocable when it declares an `inputs` JSON Schema and no `visibility`, since a caller carries
  no roles to meet one; a bare-name skill and one without `inputs` say why not),
  `skill_input_problems` (jsonschema Draft 2020-12), `invoke_message`, and `PinnedAgent`, which
  narrows `_select_skills` for the wrapped agent only (keyed by its `spec`, so a composed
  assistant inside keeps its own skills) and keeps the pinned skill's last output. Plato:
  `GET {prefix}/assistants/{aid}/skills`; `POST {prefix}/assistants/{aid}/skills/{skill}/invoke`
  (governed: idempotent, configured-only), 404 for an unknown skill, 422 for one not invocable or a
  body its schema refuses, both before any model; answers `SkillInvokeReply` (`skill`, `ran`,
  `output` parsed as JSON where it parses, `reply` the turn's `ChatReply`). `/chat` and invoke share
  `_blocking_turn`. `Skill.inputs`' comment, which said nothing reads it, now says what does.
  Client: `skills`, `invoke_skill`, `SkillEndpoint`, `SkillInvokeReply`, held to the server. Stage
  2 (schemas derived for every skill, typed signatures in `_build_parent_tools`) and the async
  `actions`/`operations` shape and per-assistant OpenAPI follow.

- **A chat turn's trace of record** (Plato service Phase 4) (+694 / -57 lines, 13 files). The user
  decided `CanonicalTrace` is the format of record (UAF item 9). `agents.interactive.turn_trace.TurnTrace`
  wraps the agent (`observe`) so each skill reply is heard through `on_skill_result`, and its
  `record`, the lifecycle's `on_complete`, writes one `CanonicalTrace` per turn through the
  fabric's canonical store (a write failure is logged, never fails the turn). Its `VersionBundle`
  sits at `metadata["version_bundle"]` (trace.py is Spec-v1.5 frozen, so no new named fields):
  `model_versions` (the agent's model, or `unpinned`), `pack_version`, and in `extra` the
  `agent_release_id` (or `legacy_unversioned: true` for an assistant with no frozen release),
  `skill_versions` (each invoked skill's content pin, via `release.content_pin`, now module level),
  `model_data_version` (`llm.cost.MODEL_DATA_VERSION`) and `models_served`. Each skill step
  carries its own bundle through `TraceStepContextHelper`. `InteractiveAgent.skill_def(name)` is
  public. `runs.ChatTurnSpec` gains `on_complete` and `terminal` (fields the run's terminal event
  carries beside `TERMINAL_EVENT_KEYS`, which it may not name). Plato: `/chat` and `/chat/stream`
  record the trace where the wiring has a fabric; `ChatReply.trace_id`; a streamed turn's terminal
  event carries `release_id` and `trace_id` (`TODO(stream-release-id)` closed);
  `GET {prefix}/traces/{trace_id}` on the read gate, a trace of another tenant the same 404 as a
  missing one (`trace_router(visible=, dependencies=)`); no fabric, no trace and no route. Client:
  `PlatoClient.trace`, `contracts.ChatStreamEnd`, `VersionBundle`, `Trace.metadata` and
  `Trace.version_bundle`, `ChatReply.trace_id`; a test holds `VERSION_BUNDLE_KEY` to the SDK's.
  Begun by a background agent that stalled before committing; reviewed and finished here.
  Not in it: `GET /decisions/{id}`, which jaci's note also asks for.

- **Every synchronous call path refuses a batch-tier name; the tier is read once** (review of
  15b55b1d). The refusal sat only in `resolve_model`, but `ReasoningAgent.run` stripped the tier
  prefix before reaching it and a conductor mode's `api_model_name` stripped it through its
  injected parser, so both still made a standard call at the batch discount; and the OpenAI chat
  provider stripped it too. Each site re-derived the tier from a substring, and `with_cost_tier`'s
  was case-sensitive where `parse_model_tier` is not (`FLEX_gpt-6` lost its flex tier).
  `llm.model_identity` now has `cost_tier(name)` (`FLEX_TIER`, `BATCH_TIER` or None, any case,
  past provider prefixes; `parse_model_tier` shares its walk) and `sync_model_name(name)` (flex
  stripped, batch refused). Used by `resolve_model`, `ReasoningAgent.run`, `BaseMode.api_model_name`,
  both OpenAI provider call paths and `with_cost_tier`. Tests for each path the review named.

- **A `batch_` model name is refused for a synchronous call** (+14 / -4 lines, 2 files). Since the
  cost-tier prefix is stripped in `resolve_model` (fab0793e, flex reviewed sound: the card lookup
  normalizes the name, the agent keeps the prefixed name, and the ledger prices flex at half
  rate), a `batch_` name made a standard call while the ledger, reading the prefixed name, priced
  it at the batch discount: cost under-reported. `resolve_model` now raises `ValueError` for a
  batch-tier name (detected by `parse_model_tier`, so a model id merely containing `batch_` is not
  caught); nothing in japes or jaci calls one.

- **Policy extraction: percent units, timing discretion, mentioned fields, repeated clause
  numbers** (+270 / -32 lines, 9 files, three commits). From jaci's C&I extraction re-run (OCC Commercial Loans
  plus the YETI loan agreement).
  - Units: `JtbdTemplate.units` (`{field: fraction | percent}`, `policy_conditions.FIELD_UNITS`)
    reaches `ConditionExtractor` and `PythonExtractor` (`units=`). A threshold or gate printed as a
    percent ("10%", "10 percent") is kept on a `fraction` field as N/100 (the springing FCCR gate
    becomes `excess_availability_pct < 0.1`), on a `percent` field as printed, and on a field with
    no declared unit is refused to natural language (it was kept as 10 on a fraction field, so
    the gate held on every case). A number printed both as a percent and plain is refused; an
    unknown unit raises. Both prompts list each field with its unit (`described_fields`, `cltv (unit: fraction)`); the
    Python prompt allows the N/100 conversion on a fraction field. A Python rule's scale is not
    checked mechanically (`TODO(python-percent-unguarded)`: a literal in source cannot be tied to
    its field without parsing the comparisons); its own cases and proposal review carry it.
    "Percentage points" reads as a percent.
  - The condition prompt says discretion over when or how a comparison is tested ("or as
    otherwise specified by Lender" for a test date) leaves it deterministic, and that the fields
    listed are the ones the requirement constrains, not one it mentions in passing (the
    governing-law clause read `lien_position` for the word "liens"). Both are prompt changes, so
    they lower the rate rather than guarantee it; the relevance gate stays the drafted reads.
  - Citations: `ClauseSegment.section`, set by `clause_segments`, qualifies a clause number by the
    `ARTICLE n` heading above it (`loan.pdf#ARTICLE 2 1.`, a markdown `## ARTICLE 2` too), or by a
    titled one whose spaced dash (hyphen, en or em) sets off a capitalised title (`Article VIII -
    Financial Covenant`, YETI's form, cited `#Article VIII 1.`). Any other line opening
    "Article n" with lowercase after the number (a wrapped "Article 9 of the UCC") clears the
    article rather than guess, as does a `Schedule`/`Exhibit`/`Annex`/
    `Appendix` heading, leaving a `§`/`Section`/`Article`/`Clause` marker as printed; a section
    still repeated in the document carries its occurrence (`#1. (occurrence 2)`). `citation` and `coordinate` read it, and `split_long` pieces carry it.
    Rule ids are unchanged.
  - jaci: declare `units: {excess_availability_pct: fraction}` (and any other ratio field) on the
    template its extraction script builds, or a percent-printed threshold on that field now comes
    back natural language.

- **Full-range review notes, rounds 33-34** (+72 / -4 lines, 5 files). Round 33 reported no
  defects; its notes: an authoritative `policy_check` whose named policies (or, unnamed, any of the
  pack's policies, since each can be in force for some program) hold a live rule is refused at
  publish, since a check runs no reasoning agent and withholds that rule, refusing approval
  wherever it applies; `RequiredClasses.values` takes an unquoted YAML flag or number key (`true:`,
  `5:`) as its text, and refuses two keys a run matches as one (`5:` and `"5":`, `ABL` and
  ` abl`); a failed live-rule scan is a publish problem, not "no live rules"; the quickstart says a missing fact is refused
  after the documents' extraction, not before any model runs (document extraction is one).
  ci-spread-core seed: `ontology/ci_lending.yaml` resynced from jaci `65e1ed5`.

- **Full-range review fixes, round 32** (+20 / -7 lines, 4 files). The publish check matches a keyed
  `required_classes`' values as the run does (`_value_key`), so a number or flag enum publishes
  (it refused `"1"` for an integer `1`); ci-spread-core seed: `intake.yaml` from the authoring
  repo (its required types now live in the manifest's table), the diagnose map spells `ABL` as
  the schema does.

- **Full-range review fixes, round 31** (+144 / -33 lines, 8 files). A keyed `required_classes` matches the
  field's value as written (`True` is `"true"`, `5` is `"5"`), so a flag or number field no
  longer falls silently to the default; adjudication's re-read names its temporary file by the
  bare filename; a cite to page 0 or below cites the document, not a page; the quickstart lists
  all five once-only step kinds. ci-spread-core seed: `financial_fields.json` asks for whole
  dollars (a statement in thousands is scaled; each field `unit: USD`); the playbook `applies_to`
  lists, the ontology's loan-type comment, `pipelines.yaml`'s header and the deal overlay resynced
  from the authoring repo.

- **Full-range review fixes, round 30** (+76 / -24 lines, 10 files). A field a document step can fill is
  optional at submit only for a case naming documents (`input_model(with_documents=)`): one naming
  none is refused at submit instead of failing later in the run. A required document class the
  case's own evidence supplies (an `input` evidence source at a path the record fills) is not
  missing, so a demo case carrying its evidence is not flagged for review. Adjudication cites that
  are not a list read as none; page labels are read off the event loop; `had_structured_view`'s
  description names the digital-PDF page view; two seed comments corrected.

- **Required documents by an input field, and review round 29** (+118 / -16 lines, 7 files).
  `document_ingest.required_classes` may be `{by, values, default}` (`RequiredClasses`): the
  classes a case needs by the value of an input field, text compared ignoring case, `default` for
  a value the map does not name; checked at publish (`by` an input field, every value one its
  enum allows, every class in the taxonomy). ci-spread-core requires a borrowing base certificate
  of ABL and revolving credit only, by `loan_type` (the authoring repo's request; it closes
  `TODO(ci-required-documents-by-loan-type)`). Review: a number's short-value guard measures the
  value as written (`1.0` is "1"), so a whole float no longer matches a stray "1"; a digital
  PDF's `DocumentResult` reports its page view (`had_structured_view`); the C&I playbook reads the
  decision's computed `leverage_x`.

- **Printed page labels and the document's own references in citations** (+135 / -10 lines, 9 files). By
  the user's direction (front matter numbered in roman numerals, tables and exhibits named in the
  text). `PageLocator` gains `label` (the number printed on the page) and `ref` (the document's
  name for the place: `Table 4.2`, `Exhibit B`, `§ 6.1`); `page` stays the physical 1-based page a
  viewer opens, the standard practice (PDF page labels are presentation, `file.pdf#page=N` is
  physical). `tools.documents.conversion.page_labels` reads a PDF's `/PageLabels` table (PyMuPDF);
  `DocumentResult.page_labels` and `page_label_source` (`pdf_page_labels`) record it per document,
  and `DocumentAgent.process` labels each page locator. Adjudication's evidence marks pages
  `[page 5 (printed iv)]`; its prompt asks for the marker's page and the document's own name for
  the place; `EvidenceCite.ref` reaches the citation's locator (a cite without a page becomes a
  `SectionLocator` named by its ref). `TODO(locator-printed-ref)`: an extracted field's locator has
  no `ref` yet; a caption read during conversion would give it one.

- **Full-range review fixes, round 28** (+31 / -4 lines, 5 files). ci-spread-core no longer requires a
  borrowing base certificate of every case (an ABL document; every term loan was left for review),
  `TODO(ci-required-documents-by-loan-type)`; a hyphen in a range or date (`100-200`,
  `FY2025-2026`) is not read as a minus; an input schema declaring `documents` (reserved for the
  run's documents) is a check finding.

- **Full-range review fixes, round 27** (+32 / -8 lines, 7 files). A printed number followed by a
  separating comma is read (`$650,000, which`; round 25's pattern rejected any trailing comma);
  ci-spread-core's convergence counts a borrowing base certificate as a structural source, as the
  authoring repo's loop does; submit validates the record without its `documents`, as the run
  does; a document class that is also an input field is a check finding (adjudication would read
  document text for it).

- **Full-range review fixes, round 26** (+56 / -9 lines, 7 files). A negative number is located as
  printed (`-125,000`, `(125,000)`); a malformed adjudication cite is dropped
  (`_BatchItemVerdict.valid_cites`) rather than failing the whole batched answer; a playbook
  numeric test on a flag never holds; `describe_pack` keeps a metric id's first definition, as the
  fact catalog does.

- **Full-range review fixes, round 25** (+108 / -60 lines, 10 files). `locate_page_for_value` compares a
  number by value against every number a page prints (`_printed_numbers`: `650,000`, `2.50` and
  `2.5` alike, never part of a longer one), replacing four rounds of needle patches (`2.5` printed
  `2.50x` went unlocated after round 22's); a playbook `_any` test flattens a list field and
  ignores mappings (it raised on a hypotheses list field); `BlobDocumentStore` and the
  adjudication pin check use `util.digest.content_digest`; `describe_pack`'s metrics are unique by
  id; a check's `policies: []` is a check finding (it assessed every policy). The ci-spread-core
  seed's ontology and `core.yaml` resynced from the authoring repo (no em-dashes; the repo named
  in provenance), and its ontology comment no longer claims triples are written.

- **Full-range review notes, round 24 (first clean full round)** (+46 / -62 lines, 3 files). Removed a
  dead older copy of the adjudication step's body that round 23's edit left after its `return`; a
  document with no text (a scan without a text layer) does not supply its class to adjudication;
  the ci-spread-core decision and input schemas resynced from the authoring repo's re-export
  (`advance_rates` as a `$ref` to a typed `AdvanceRates`; `loan_id` required); two CI tests assert
  the outcome they are named for and resolve a `$ref`.

- **Full-range review fixes, round 23** (+204 / -32 lines, 9 files). Adjudication: a rule the assessment
  left pending is adjudicated when everything it reads is a document class the run supplies (a
  reasoned assessment pends a document-reading rule, which adjudication then skipped silently);
  one still pending is listed (`pending`) and counted unanswered, so it reaches the checkpoint and
  the review flag; a violated rule whose action is not `deny` (`violated`) goes on the payload and,
  unreviewed, leaves the Decision for review. `DocumentAgent.process` converts off the event loop
  (its DocIntel page count is carried back to the caller's context). A subject field the input
  does not require is a check finding. ci-spread-core seed schemas: `loan_id` required,
  `BorrowingBase.total_availability`/`excess_availability` nullable (an unstated figure was an
  affirmative zero that failed the availability rule), `advance_rates` declares
  `accounts_receivable` and `inventory`. The snapshot's coverage check is its own test.

- **ci-spread-core seed resynced from the authoring repo** (+40 / -14 lines, 6 files). The ontology
  (0.2.2: `UCACashFlowResult` and `DebtServiceCoverage` over `adjusted_cash_flow`, clearing the
  pack lint's `unreachable_derivation_input`), `RB_CI_OVERLAY`'s `overlay_id: rb-abl-2026`, the deal
  overlay's rule-level `replaces:`, `core.yaml`'s header and provenance, and `pack_version:
  0.3.0-draft`. The Python `class:` lines and eval paths stay stripped. `core.yaml` no longer names
  a consumer module, so the pin of such files drops it.

- **Full-range review fixes, round 22** (+29 / -7 lines, 6 files). The winning playbook leads, then
  the always-included ones, whatever order the map lists them in (a working-capital loan reported
  the memo scaffold as its top match); an integer never matches the whole part of a decimal
  (`1,200` inside `1,200.45`); the checkpoint payload carries `check_errors`, so a check that
  could not run is one the reviewer sees.

- **Full-range review fixes, round 21** (+56 / -23 lines, 10 files). A number is located as a whole
  number (`650,000` no longer matches inside `1,650,000` or `650,000,000`); the schema-only
  fallback extraction keeps the conversion's page regions; `describe_pack` lists every assessing
  step's metrics through the same `metric_refs` the fact catalog uses (ci-spread-core's check
  metrics were missing from describe); a lint subject for unreadable steps is `conductor.steps`;
  the deployed-posture storage warning names case documents too.

- **Full-range review fixes, round 20** (+51 / -18 lines, 7 files). `document_ingest` is once-only (a
  second one re-read every document and replaced the first's missing classes, clearing the review
  flag); the fact catalog takes every assessing step's metrics (a `policy_check`'s too, so
  ci-spread-core's `excess_availability_pct` is a typed fact); `describe_pack` reports an
  unreadable steps file as an error entry; tests: the client contract reads the documents
  route's own view, a run naming another tenant's document is a 422, document blobs have their
  own directory.

- **Full-range review fixes, round 19** (+51 / -19 lines, 5 files). `locate_page_for_value` adds a
  separated needle only for a number of at least `THOUSANDS` (`650,000`, and `650,000.00` where
  the value has cents), so `12.0` no longer matches a stray "12" and `0.8765` no longer matches
  "0.88": a wrong page citation was silent. A subject field a document step fills is a check
  finding (submit needs it first). `ModeFactory` states that it may be asked for `"sentinel"`.
  The loop-vs-pipeline test compares `tests.loop_snapshot.project`'s projection, the snapshot's
  own.

- **Full-range review fixes, round 18** (+71 / -14 lines, 6 files). An authoritative `policy_check` is no
  longer excused by adjudication's settled rules (reverting round 7's choice): adjudication judged
  the record, the check assesses the decision's figures; the refusal now names what the
  assessment withheld (`(withheld: R)`), which was round 7's complaint. Adjudication leaves a rule
  the assessment left pending (missing, stale or uncomputable evidence) pending, so a stale value
  is never adjudicated into a settlement. A `policy_check` that could not run leaves the Decision
  for review (unless a reviewer saw it), and an authoritative one adds a required action.

- **Full-range review fixes, round 17** (+73 / -14 lines, 6 files). `PolicyAssessment` records the rules
  the policy check withheld an allow for (`withheld`) and refusals that named no rule
  (`withheld_unattributed`, a policy outside its assumptions); an authoritative assessment is
  excused only when that set is exactly live rules adjudication settled, with no violation, failed
  cap or unattributed refusal. Before, an uncomputable deterministic rule (outcome
  `pending_calculation`) or a failed assumption beside a settled live rule let an approval past a
  failed gate. A `policy_check` whose figures cannot be assessed records a failed check
  (`error`; authoritative: the approval withheld) instead of failing the run after the loop.

- **Full-range review fixes, round 16** (+57 / -4 lines, 6 files). The checkpoint's payload names
  `missing_documents`, so the gap a resolution clears from review is one the reviewer was shown; a
  case naming documents for a pack with no `document_ingest` step is refused at submit and at
  run (`check_documents_read`) rather than pinned and ignored; the step-kind docstrings state the
  slot rule the check enforces; a document upload past the cap is tested (413).

- **Full-range review fixes, round 15** (+84 / -31 lines, 8 files). `document_ingest`'s schema key is
  `fields_schema` (the `*_schema` convention, so `describe_pack` lists it; was `schema`); a case
  missing a required document class leaves its Decision for review unless a reviewer saw it, and
  only the governor is said to see the gap (the narrator does not read the loop's metadata); a
  playbook context naming an input or decision field the schema lacks is a check finding; a
  pipeline of no steps is a check finding; the check's default-program and null-figure tests now
  run the step.

- **Full-range review fixes, round 14** (+101 / -42 lines, 11 files). A `policy_check`'s own
  `default_program` is the one it is assessed under (`_program_policy_ids` reads the step's before
  the pack's), and an unknown one is a check finding; `documents` is no longer a run-input slot
  but `document_ingest`'s, and an `adjudication` over documents with no document step before it
  is a check finding (`StepCheck.kinds_before`); one documents-shape rule (`document_refs`) for
  submit and run; one durability gate (`plato.api.packs.refuse_ephemeral_blobs(action, why)`) for
  pack publish and document upload; a pack schema object requiring keys it declares no properties
  for is refused; a document agent's taxonomy entry that is neither a label nor `{label}` is a
  check finding, not a crash.

- **Full-range review fixes, round 13** (+69 / -8 lines, 8 files). A human checkpoint `reviews` the
  decision (`StepKind.reviews`), so a later step that writes it (a `policy_check` after the
  checkpoint) is a check finding: the reviewer approves the decision every later step keeps;
  `POST /documents` refuses with 503 on a deployed replica whose blobs are not durable, the
  guard pack publish already has; an adjudication with no live rules in force spends no model
  call; the loop snapshot test requires a snapshot entry for every gold case.

- **Full-range review fixes** (+110 / -29 lines, 10 files). A resumed run's later steps get the host's
  `python_executor`, `documents` and `agents` (a `policy_check` after the checkpoint withheld
  every python rule on resume); a `decision_field` the decision leaves null assesses the record
  alone instead of failing the run; a diagnose rule testing an `input.` field for a value its enum
  does not allow is a check finding, and the ci-spread-core seed's map now uses the input's
  `LoanType` members (`revolving_credit` for `revolver`; `delayed_draw_term_loan`, no member,
  dropped), so a revolver matches the ABL playbook; the seed's input schema drops
  `special_instructions_path`, which nothing reads; `BlobDocumentStore`'s docstring states what a
  concurrent first upload does.

- **Review fixes over Phases 1-5** (+102 / -22 lines, 5 files). Every `always_include` playbook rule joins
  the winning one (the credit memo scaffold was dropped whenever an analysis rule matched); an
  authoritative `policy_check` counts the live rules adjudication settled; a decision field left
  null never overwrites the record's fact in a check; `CaseResult.documents` reports missing
  required classes when a run names no documents; an authoritative failure's rationale joins a
  refusal's reasons instead of replacing them (`_with_clause`, shared with denials); a playbook
  number test on a list or text never holds, and one on a `hypotheses.` source is a check
  finding. The missing-documents note says the governor and narrator see it, which is what reads
  `missing_documents`. Then: a playbook threshold that is not a number is a check finding (a
  value that is not a number never satisfies a comparison), and a rationale clause is matched
  whole, so one another contains (`CAP-1` in `CAP-10`) is still stated.
  The diagnose map is then one typed model (`DiagnoseMap`, `DiagnoseRule`) that both the run
  and the check read: a condition that is not `<name><test>`, an `_any` that is not a list,
  a comparison to something that is not a number, and conditions that are not a mapping are
  refused at publish rather than matching nothing; so is an `_any` list holding anything but
  plain values.

- **C&I as a `conductor_pipeline`: the playbook step, figures, documents in the loop, and the
  ci-spread-core seed off Python** (+1426 / -33 lines, 18 files). Phase 5 of the conductor-pipeline plan.
  - **`playbook`** (`PlaybookStep`: `diagnose_map`, `context`): the authoring repo's C&I playbook
    walker generalized. Rules `{id, conditions, playbook_id, confidence_boost, always_include}`
    with conditions `<name>_any` (text ignoring case), `_gt`, `_gte`, `_lt`, `_lte` over context
    names sourced from `input.<f>`, `decision.<f>` or `hypotheses.<f>`; first non-always match
    wins; `PLAYBOOK_BASE_CONFIDENCE` (or the map's `base_confidence`) plus boosts; each
    recommended playbook's `## section_id:` sections are its guidance refs. Writes a new
    `guidance` slot (`CaseResult.guidance`). Check: context sources, every rule's playbook
    declared, every condition on a context name with a known test.
  - **`policy_check.figures`**: names mapped to dotted paths into the decision; checked at
    publish against the decision schema's fields.
  - **Documents in the loop**: each admitted document is evidence of its class
    (`source: document:<id>`, its extracted fields as data) for the verifier;
    `document_ingest.required_classes` records `documents.missing` (in the loop's context
    metadata as `missing_documents`), and the check refuses a class outside the agent's taxonomy.
  - **The convergence gate counts only evidence a source supplied**, not UNAVAILABLE records.
  - **`assess(policy_ids=)` skips program selection**, so a pack with programs and an input
    naming none can still be checked against named policies.
  - **Pack schemas: an `object` naming no `properties` is a mapping of any keys** (`dict[str,
    Any]`). It was an empty model that dropped every key, which emptied C&I's
    `advance_rates` and so its A/R and inventory advance checks.
  - **ci-spread-core seed**: `conductor: kind: conductor_pipeline`, `[document_ingest (fills the
    financials; requires financial statements, a BBC and a debt schedule), investigation
    (sentinel; convergence on two iterations, the statements and a structural source),
    policy_check (advisory, the four core policies over the recommendation's figures,
    `excess_availability_pct` derived in `check_metrics.yaml`), human_checkpoint
    (CREDIT_COMMITTEE_APPROVAL), playbook, narrate (approved decisions)]`. New files: the input,
    hypothesis, decision and financial-fields JSON Schemas (from the authoring repo's models,
    in the supported subset), `evidence_tools.yaml` (each type from the case's own `evidence`
    object), `document_agent.yaml`, `check_metrics.yaml`. The seed publishes with no blocking
    finding and runs (`tests/test_ci_pipeline.py`). Not carried over, as TODOs in the manifest:
    entity extraction into the knowledge graph (`ci-entity-extraction-plugin`, the authoring
    repo's capability, to install as a step-kind plugin), the RB program overlay in the check
    (`ci-check-program-overlay`), `lien_position` (`ci-lien-position-derivation`). The evaluator
    and persist steps have no step kind: a run already persists its Trace and Decision, and
    scoring against ground truth is an eval experiment over the `case_run` entity.

- **The investigation step's loop guards, and review fixes to adjudication** (+153 / -12 lines,
  5 files). Phase 5's first part (C&I's loop), and the review over Phases 1-4.
  - **`sentinel`** (`SentinelTuning`: `signal_decay_threshold`, `confidence_change_threshold`)
    adds `SentinelMode` to the loop, capped at the step's `max_iterations`;
    `sdk_mode_factory("sentinel", ...)` builds it (no model call, no context).
  - **`convergence`** (`ConvergenceGate`: `min_iterations`, `evidence_all`, `evidence_any`) gates
    the investigator's claim to have converged, C&I's "two iterations, the financial
    statements and a structural source".
  - Review fixes: a failed cap composition with no binding rule still blocks once adjudication
    settles the live rules; a denial's rationale is stated once however often it is applied, and
    a refusal's own reason is kept; adjudication decides only the rules the assessment names in
    force (no legacy alias, nothing an overlay replaced), so it now `reads` the assessment;
    adjudicated text is checked against the pinned digest, and its conversion runs off the event
    loop.

- **The `policy_check` step: an assessment over the decision's figures, after the loop** (+189 /
  -5 lines, 5 files). Phase 4 of the conductor-pipeline plan (CRE's post-loop check).
  - **`policy_check`** (`PolicyCheckStep`, the `AssessmentSpec` keys plus `decision_field`,
    `policies`, `deterministic_verdict`): `assess` over the record with the decision (or its
    `decision_field`, which must be a mapping) laid over it. Reads `decision`, writes `checks`
    and `decision`, so one after the checkpoint or the narrator is a check finding. The result is
    `CaseResult.checks.<id>`; `authoritative` folds a failed check into the governor's verdict
    (and so into the Decision's `policy_refs`); `advisory` only records it. Check: the decision
    schema has the `decision_field`, and every named policy is the pack's.
  - **`assess(spec=, policy_ids=)`**: another step's settings; named policies are assessed as
    given, outside any program (so a `scope: product` policy no program lists can be a check's).

- **The `adjudication` step: a case's live rules decided against its documents** (+1793 / -28
  lines, 10 files, 1297 of them the snapshot below). Phase 3 of the conductor-pipeline plan.
  - **`adjudication`** (`agent:` an `AdjudicationAgentSpec` file, `rules: live`, `evidence:
    documents`): the live partition (`partition_rules`) of the rules in force
    (`pack.assessment.policies_in_force`, the selected program's, materialized as `assess` does),
    run through `AdjudicationAgent` over the record, the assessment's derived metrics and, by
    class, the run's documents' text marked `=== document <id> ===` and `[page N]` (the stored
    bytes converted again; no model call). A rule sees a class's documents when its `reads` names
    the class. Replicas collapse most-adverse first (`ADJUDICATION_PRIORITY`).
  - **Citations**: a batched verdict may carry `cites` (`EvidenceCite`: document, page), kept on
    the outcome's inputs under `CITES_INPUT_KEY`; the step turns them into `SourceCoordinate`s
    (the document's `source_file_id`, a `PageLocator`, its sha256) on `RuleOutcome.citations`.
    The batch prompt asks for them where the evidence marks documents and pages.
  - **Verdict composition** (the plan's §2.4, D4): an adjudicated violation of a `deny` rule
    (`denied`) withholds a governor approval, as an authoritative assessment's violation does,
    and joins its violations; an undecided rule (indeterminate, or left by a failed segment) is
    on the checkpoint's payload as `indeterminate` and, unreviewed, leaves the Decision for
    review; an authoritative assessment failing only on live rules it withheld, all of which
    adjudication `settled`, no longer overrides. `_Authoritative` is now `_Overriding`.
    `CaseResult.adjudication` carries outcomes, narrative, `denied`, `settled`, `indeterminate`,
    `failed_segments`.
  - The investigation step `uses` the adjudication, so one placed after it is a check finding.
  - **`tests/data/dscr_loop_snapshot.json`**: the five gold cases under `investigation_loop`
    (both decisions, plain and suspend-resume), projected (`tests/loop_snapshot.py`) from the
    output of the conductor as it was before Phase 1; `tests/test_loop_snapshot.py` holds the
    current runner to it, which answers the review's note that the loop-vs-pipeline test compares
    one engine with itself.
  - The document step's publish type check reads each property as `schema_model` does
    (`schema_facts`: a local `$ref`, a union with null), so the seed's `interest_rate` and
    `property_type` no longer read as untyped.

- **Documents on Plato: upload, pin, and resolve in a run** (+499 / -30 lines, 20 files). The
  runtime half of the conductor-pipeline plan's Phase 2, built in the policy session by the user's
  direction.
  - **`fabric.blob.documents.BlobDocumentStore`**: a tenant's documents over a `BlobStore`. The id
    is the sha256 of the bytes, so the same upload is the same document; keys sit under a digest
    of the tenant id (`documents/<16 hex>/<sha256>`), so a tenant id never becomes a path and one
    tenant cannot name another's document; metadata (`DocumentRef`: filename as a bare name,
    media type, size) is a JSON sidecar, so there is no table or migration. The first upload's
    filename stands. `DocumentRef` moved here from `pipelines.steps`, which re-exports it.
  - **`POST {prefix}/documents`** (multipart `document`, `read_capped` at
    `PLATO_DOCUMENT_UPLOAD_MAX_BYTES`, default 32 MiB, editable over `/config`; 422 for an empty
    upload or a filename with a path) and **`GET {prefix}/documents/{id}`** (404 for an id the
    caller's tenant has not stored). The pointer is never served. Mounted when the wiring sets
    `PlatoWiring.documents_for`, which both shipped wirings do, over the pack-archive blob store.
  - **Case runs**: `CaseRunService(documents_for=)` resolves a case's `documents` at submit
    (unknown id or a mismatched `sha256`: 422) and pins `{document_id, sha256, filename,
    media_type}` on the run; execution passes the tenant's store and the agents service to
    `run_case`. `CaseRunInvoker(documents=)` does the same for eval cases.
  - **Client**: `PlatoClient.upload_document` / `document`, contract `Document`;
    `CaseResult.documents` on the client contract.
  - Review-round fixes to the step: a document's pinned digest is checked before any model call
    as well as after the read; two documents disagreeing on a filled field is a conflict
    (`filled_from`); a conflict a reviewer resolved at the checkpoint no longer leaves the Decision
    for review; the publish check refuses a document field typed differently from the input's.

- **Documents in a case run: the `document_ingest` step** (+492 / -48 lines, 7 files). Phase 2 of the
  conductor-pipeline plan, the policy session's half; the documents route, blob scoping and the
  case submit/execute wiring are the runtime session's (plan §3.7).
  - **`document_ingest`** (`agent:` a `DocumentAgentSpec` file, `fields_schema:` the fields to extract,
    `fills: input`): each of the run input's `documents: [{document_id[, sha256]}]` is resolved by
    the host's `DocumentSource` (`resolve(document_id) -> DocumentRef(pointer, filename, sha256,
    media_type)`, plus its `blob`), run through `DocumentAgent.process_blob`, and refused when its
    bytes are not the digest the run pinned. With `fills: input` a field the record left out takes
    the first document's value, recorded in `CaseDocuments.filled` with its document and
    `SourceCoordinate`; a field the record states differently (numbers by value, text ignoring case)
    is a conflict, carried on the checkpoint's payload, on `CaseResult.documents`, and marking the
    Decision `human_review_required`. The record is then validated in full, so a fact neither the
    submitter nor a document supplied is refused before any model runs.
  - **Submit**: `input_model(pack)` makes a field a `fills: input` step can supply optional
    (`fillable_fields`); DSCR's `property_value` is `required`, so a loan with only an appraisal
    was refused at submit. `CaseState` gains `record` (the input as submitted, less `documents`,
    plus what was filled), which the assessment and the evidence tools now read, and
    `documents: CaseDocuments` (refs, items, filled, conflicts). `documents` is a run-input slot.
  - **Slot order**: a step that reads or uses a slot a later step writes is a finding, which now
    covers an assessment placed before the documents that fill its input.
  - **Pages without DocIntel.** `DocumentAgent` cites the page of a digital PDF: the conversion's
    page regions become the page view (`page_view_from_regions`), and a field from a chunk on one
    page takes that page. `locate_page_for_value` also finds a number printed with thousands
    separators (`650,000` for `650000`).
  - A non-mapping `conductor` block is a `conductor_unrunnable` finding (it published clean).
  - Check: a document step's agent file, schema, and (with `fills: input`) every field it fills
    being an input field.

- **A pack declares its case workflow: the `conductor_pipeline` kind and step kinds**
  (+1413 / -469 lines, 15 files). Phase 1 of the conductor-pipeline plan.
  - **Step kinds** (`pipelines.steps`): a `StepKind` is a strict config model, the `CaseState`
    slots it reads (and `uses` when present) and writes, and a runner; `once` allows one per
    pipeline, `nested` marks a step that runs its own engine. `step_kinds()` holds the SDK's
    `policy_assessment`, `investigation`, `human_checkpoint` and `narrate`, plus any an image
    installs under the `jazzx_sdk.step_kinds` entry point; `GET /info/catalog` lists them as
    `step_kinds`.
  - **`CaseState`**: typed slots `input`, `documents`, `assessment`, `adjudication`, `decision`
    (`CaseDecision`: decision, governor verdict, the reviewer's resolution and any replaced
    decision), `checks`, `narrative`, `trace` (`CaseTrace`: mode calls, the investigation's
    context, the assessment's reasoning record, where the checkpoint fell). It is what a
    suspension stores; `restore_state` rebuilds it with the pack's types.
  - **`conductor_pipeline`**: `steps:` inline, or a pack file holding the same list (`steps:
    conductor_steps.yaml`; not `pipeline:`, which is the dotted Python pointer Plato refuses). The
    steps run on a `ConductorEngine` over one `CaseState`; a human checkpoint suspends that engine
    and `resume_case` continues it from the next step. The investigation's own engine streams its
    mode steps in place of its container step, as before.
  - **`investigation_loop` is that pipeline with fixed steps**, compiled from its block
    (`[policy_assessment?, investigation, human_checkpoint?, narrate]`), so no manifest changes.
    Both kinds run through `run_pipeline_case` / `resume_pipeline_case`, which replace
    `run_investigation_case` / `resume_investigation_case`. Over the five DSCR gold cases the
    decisions, governor verdicts, violations, binding caps, narratives, Traces and Decisions
    match the previous implementation exactly (both decisions, plain and suspend-resume), and
    `tests/test_case_pipeline.py` holds the loop and a hand-written equivalent pipeline (inline
    and in a file) to the same. Visible differences: the assessment is now a step, so a run
    streams a `policy_assessment` step first and a stop request before it ends the run without
    one; a suspension's `payload` no longer carries `mode_calls` and `pre_loop` (the stored state
    does); the trailing `finalize` record is gone from `steps`.
  - **Publish check** (`conductor_problems`, `conductor_unrunnable`): a step of a kind the image
    lacks, a step reading a slot no earlier step writes (a checkpoint before the investigation),
    a step running before the step that writes a slot it `uses` (an authoritative investigation
    before its assessment would decide without it), duplicate step ids, a second once-only step, and each kind's own checks (schemas, evidence
    tools, modes and temperatures, the checkpoint among `human_checkpoints`, the narrate gate's
    field in the decision schema). Problems name the step: `conductor.steps.<id>.<field>` for a
    pipeline, the old `conductor.<key>` paths for `investigation_loop`.
  - **One reader for the conductor's steps.** `step_entries(loader)` is what `assess`
    (`assessment_entry` now takes the loader), the fact catalog's derived metrics, `describe_pack`'s
    schemas, `pre_loop_agent` (a step's `reasoning` / `model`, `pre_loop_reasoning` /
    `pre_loop_model` on the loop), case submit's subject field, `check_resolution` and the eval
    invoker's checkpoint (`case_checkpoint`) read. A block with no `kind` still serves its
    `pre_loop` assessment to `assess`. Lint's `invalid_assessment` and `unknown_default_program`
    name the step's path (`step_subject`). An unreadable steps file is a conductor finding, not a
    fact-catalog one. A `pre_loop` entry carrying a step-only key (`id`, `reasoning`, `model`) is
    still refused, never overwritten by the loop's `pre_loop_reasoning` / `pre_loop_model`.
  - `docs/DOMAIN_PACK_QUICKSTART.md` documents the kind.

- **Policy extraction and model calls, from jaci's first live run of the policy pipeline.**
  - **`flex_` model names.** The agents layer's `resolve_model` strips a cost-tier prefix
    (`flex_`, `batch_`) for every caller, and `ReasoningAgent` turns a `flex_` OpenAI name into
    `service_tier="flex"` unless its settings already name a tier. The default model is
    `flex_gpt-6-luna`, which `ReasoningAgent` sent as given, so every extraction call (jaci's
    script, Plato's authoring and policy-extract routes) answered 404 `model_not_found`. The tier
    goes back on through one helper, `agents.models.with_cost_tier`, on every OpenAI path:
    `ReasoningAgent`, `OpenAIProvider.build_agent`, its tool-calling path and its fast path.
  - **`temperature` on `gpt-6-luna`.** A card may set `unsupported_always`: its refused params
    are stripped on every call, not only alongside `reasoning_effort`. `gpt-6-luna`'s card sets it,
    since its API rejects `temperature=0.1` on a plain call (jaci's live ACORD extraction test);
    the gpt-5.4 family still keeps `temperature` without `reasoning_effort`, as confirmed live
    before. `llm.providers.openai` was the one path still conditioning on `reasoning_effort` for
    such a model; the agents providers and modes already stripped per card.
  - **Rule ids per clause.** `segment_key` (the document's base name with its extension, or a
    hash of the name where it slugs to nothing, and the clause's position) builds the rule ids of
    `ModalClauseExtractor`, `ConditionExtractor` and `PythonExtractor`; a clause marker alone
    repeats in a document that numbers clauses per article, so 119 clauses of a loan agreement
    proposed 8 rules (the springing FCCR covenant shared an id with the interest clause and was
    dropped). The propose step now merges candidates by content (action, gate, condition and
    wording), so the same clause in two documents is still one proposal with both sources, under
    its smallest id whatever the document order; two documents whose names slug alike get a
    suffixed id (logged), never an overwritten rule.
    `JtbdExtractor` was already unique: its section names are refused when repeated.
  - **Gated thresholds.** `ConditionExtractor` may propose one gate with its threshold ("FCCR at
    least 1.10 while availability is below 10%"): an applicability `expression` held to the same
    checks as the threshold (a declared field, a numeric comparison, a printed number); a gate that
    fails them, or names no field, refuses the expression rather than applying the threshold
    always.
  - **Unnumbered prose.** `ClauseSegmenter` splits a clause longer than `DEFAULT_MAX_UNIT_CHARS`
    at blank lines, then at sentence ends (rejoined with spaces), and numbers the pieces in order
    (`split_long`, now
    shared with `SectionSegmenter`); the OCC handbook, which has no clause numbers, reached the
    extractor as one 23,000-character segment and was proposed as one rule.
  - **Relevance.** `ConditionExtractor` and `PythonExtractor` (for a clause, not when formalizing
    an existing rule) propose nothing for a clause reading none of the pack's declared fields (a
    drafted threshold field counts),
    logged at info; borrowing-request mechanics, interest payment dates and a handbook cover page
    were proposed as rules. With no fields declared, everything is still proposed.

- **Review round 2 fixes** (`cd61f0f4..` re-review). The executor's module docstring and guard
  comment overclaimed after the lazy-import fix (they said every further import and open is
  refused); both now state the rule as it is: a stdlib import outside `REFUSED_MODULES`, and a
  read-only open or listing inside the stdlib, nothing else. The guard also read write intent only
  from a mode string, so `os.open(<stdlib file>, O_WRONLY)` (an `open` event with `mode=None` and
  the flags) passed; it now refuses any `O_WRONLY`/`O_RDWR`/`O_TRUNC`/`O_CREAT`/`O_APPEND` flag
  (test fails on the previous guard; `check_python_rule` bars `os` regardless). `assessment.py`'s
  two copies of "the fields rules in force read" are one `_fields_read`. A skill action's
  claim-time invocability check runs before the turn's trace is opened.

- **Evidence freshness reaches derived metrics; only what is read counts** (review of 040092c9;
  fixed by the runtime session in the policy session's path, its owner idle with a clean tree)
  (+106 / -11 lines, 3 files). A stale or undated field was withheld from the rules, but metrics
  derived from it had already been computed from the raw input and stayed in the context and in
  the caps: a CLTV rule was judged on a year-old appraisal and could pass (high). Gaps are now
  computed from the input before derivation; a gap's fields are kept out of `_derive`, and a
  metric reading one (`_metric_reads`: its bindings' names and refs) inherits the gap, so its
  rules resolve by the evidence's `missing_behavior`, and it is left out of `caps_context`. A
  `refuse` type refused the assessment even when no rule in force read its fields (a Standard
  input over a Platinum-only field); `_gaps_read_by` keeps only gaps on fields rules in force read,
  directly or through a metric. Evidence dated after the assessment day is a gap. A violation is
  routed by the `on_violation` of the rule in its own policy (`(policy_id, rule_id)`), not the
  last one of that id. A violation from failing evidence carries `policy_id`. Quickstart updated.

- **CREMF: assessment outcomes and evidence freshness** (+368 / -25 lines, 11 files).
  `PolicyAssessment.outcomes` maps every rule in force to an `AssessmentOutcome`: `pass`, `fail`,
  `pending_evidence`, `pending_calculation`, `waiver_required`, `pre_review_required`,
  `not_applicable`, `unable_to_evaluate` (the corpus's `ProgramEvaluation.outcome` vocabulary).
  A violation routes by the rule's new `on_violation` (`fail` default, `waiver_required`,
  `pre_review_required`; the corpus fans a Fail out to these) and still counts against `allowed`.
  A rule not evaluated for a missing input is `pending_calculation` when that input is an
  underivable metric, else `pending_evidence`; a withheld rule maps by its indeterminate reason,
  which `_withheld_refusal` now records in the refusal's `domain_extensions`
  (`indeterminate_reason`); a rule whose gate does not hold is `not_applicable`. `allowed`
  semantics are unchanged. Evidence types gain `freshness_window_days`, `as_of_field` (required
  with a window) and `missing_behavior` (`pending_evidence`, `fail`, `refuse`). `fields` keys name
  the inputs a type supplies; when the evidence is undated or older than its window at
  `assess(as_of=)` (default today, UTC), or (with `missing_behavior` set) a field is omitted,
  those inputs are withheld and the rules reading them resolve by the behaviour: pending
  (attested INDETERMINATE naming the stale evidence), failed (attested FAIL, added to
  `violations`, `allowed` false), or the assessment refuses. A type declaring a non-refusing
  `missing_behavior` takes its omitted facts out of the `missing_inputs: refuse` check. Unset,
  nothing changes. Plato `POST /packs/{id}/assess?as_of=` (422 for a non-date); client
  `assess(as_of=)` and `PolicyAssessment.outcomes`. `DOMAIN_PACK_QUICKSTART.md` documents both.

- **The executor's guard lets a lazy stdlib import load** (review of 3f6eba67). The guard refused
  any import not loaded when it was installed, so a rule using `datetime.strptime` (which imports
  `_strptime`, `locale` and `calendar` on first use) was withheld. It now allows, inside the
  stdlib directories only (`sysconfig` `stdlib`/`platstdlib`, raw and resolved): the import of a
  stdlib module not in `REFUSED_MODULES` (sockets, ssl, subprocess, ctypes, multiprocessing,
  asyncio, select/selectors, shutil, tempfile, urllib, http and the like), a read-only open of its
  file, and the `os.listdir`/`os.scandir` the import system makes. Every other open, listing and
  `os.`/`socket.`/`subprocess.`/`ctypes.` event stays refused. Test for the `strptime` case,
  which fails on the old guard.

- **The python executor is hardened and runs on deployed tiers** (+87 / -40 lines, 7 files).
  `LocalPythonExecutor`'s child, in addition to `-I -S`, an empty environment, the CPU/memory/
  file-size limits and the wall-clock kill: a read-only working directory (`READ_ONLY_DIR_MODE`);
  `RLIMIT_NOFILE` (`MAX_OPEN_FILES` 32), `RLIMIT_CORE` 0 and `RLIMIT_NPROC` 0 (best-effort, as
  `RLIMIT_AS` was); a new user + network namespace (`os.unshare`, Linux, Python 3.12+, where the
  kernel allows it unprivileged; skipped silently otherwise); then, after importing
  `python_check.ALLOWED_IMPORTS`, an audit hook that refuses any import not already loaded, every
  `open`, and every `socket.`, `subprocess.`, `os.`, `shutil.`, `ctypes.`, `resource.`, `signal.`,
  `_posixsubprocess.`, `pty.`, `fcntl.`, `mmap.` event plus `sys.addaudithook`. Measured first:
  rule code using all six allowed modules raises only `compile` and `exec`, so the guard costs a
  legitimate rule nothing. The allowed modules are imported before the namespace switch, since an
  unmapped user may not read a privately installed stdlib. The deployed-posture refusal is gone;
  Plato's `workstation_python_executor` is `local_python_executor` and installs on every tier, so
  python rules and python custom scorers run when deployed instead of being withheld. Still not a
  kernel sandbox (the docstring says so): a deployment running code from authors it does not
  trust installs its own isolated `PythonExecutor`. Tests: eight refusals (socket, subprocess,
  read and write opens, `os.system`, `os.listdir`, `os.fork`, `ctypes`), the allowed modules
  under the guard, and a run in a deployed posture. Verified on macOS only, where `unshare` and
  `RLIMIT_NPROC` do not apply; `/tmp/japes_executor_linux_check.sh` runs the tests in a Linux
  container.

- **Breaking (import path): `tools.ratio_evaluator` removed** (+5 / -12 lines, 3 files). The shim kept
  for jaci is gone; `jazzx_sdk.util.math.ratios` is the module and `jazzx_sdk.tools` still
  re-exports its names. Its test moves to `tests/test_util_math_ratios.py`. jaci's
  `tests/unit/test_corrections.py` imports the old path and needs the new one.

- **Breaking (import paths): `evaluation.feedback` is a package** (REFACTOR-2.4 Phase 10, revised)
  (+84 / -69 lines, 36 files). The twelve flat `evaluation/feedback*.py` modules (four when the plan
  was written) move into `evaluation/feedback/`: `feedback.py` is `feedback.core`, and
  `feedback_{config,db,index,learning,processing,quality,records,render,retrieval,sink,text}` are
  `feedback.<name>`. `jazzx_sdk.evaluation.feedback` re-exports core's six public names
  (`Feedback`, `FeedbackSource`, `FeedbackStore`, `InProcessFeedbackStore`, `Reaction`,
  `render_feedback`), so jaci's imports (all of that path) work unchanged; its feedback, HITL and
  maker-checker unit tests pass against this tree. The `jazzx_sdk.evaluation` facade is unchanged.
  The plan's `reporter.py -> reporters/base.py` is not done: the mlflow reporter now lives in
  `evaluation/backends/mlflow/`, which left `reporters/` an empty package nothing imports, so it
  is deleted and the `EvaluationReporter` ABC stays at `evaluation/reporter.py`.

- **Extraction runs keyed by tenant** (+5 / -4 lines, 2 files). `japes_policy_extraction_run`'s
  primary key is `(run_id, tenant_id)`, as Plato's tenancy contract requires of its tables
  (`test_platos_own_tables_comply` caught the plain column); migration 0015 amended in place,
  since it has not shipped.

- **Breaking (import paths): `conductor.strategies`** (REFACTOR-2.4 Phase 9) (+20 / -16 lines, 13 files).
  `fanout`, `replication` and `ensemble` (the chain the engine never imports) move to
  `jazzx_sdk.conductor.strategies.{fanout,replication,ensemble}`. `pipeline.py`, `checkpoint.py`
  and the rest stay at the package root; the 36-name `jazzx_sdk.conductor` facade is unchanged,
  so `jazzx_sdk.conductor.Checkpointer` (patched by string in jaci) and `jazzx_sdk.conductor.fan_out`
  still resolve. Old submodule paths are gone, unshimmed: no sibling repo imports them (jaci's
  fifteen consumers use the facade; its conductor unit tests pass against this tree). Accepted
  in the review file as `old-paths-dropped-unshimmed`.

- **`fabric` no longer imports `conductor`** (REFACTOR-2.4 Phase 8, revised) (+28 / -26 lines, 6 files).
  `import jazzx_sdk.fabric.canonical` loaded ten `conductor` modules, the engine among them,
  through one edge: `condition_evaluator` read `ExecutionKind` from `conductor.pipeline`, whose
  package init imports the engine. `ExecutionKind` now lives in `fabric.canonical.trace`, beside
  the other step-vocabulary enums; `conductor.pipeline` and the `conductor` facade re-export it,
  so every existing path (jaci's `from jazzx_sdk.conductor import ExecutionKind` included)
  resolves unchanged. The four `fabric -> conductor` ignores are gone from `.importlinter`, so the
  layer contract now enforces the direction; `test_the_canonical_package_loads_no_conductor_or_tools`
  fails on the old tree. The plan's move of `condition_evaluator.py` out of `canonical/` is not
  done: it now has about twenty SDK consumers across `pack`, `fabric.graph`, `canonical/caps`,
  `formal`, `adjudication` and `server` (the plan saw one), jaci's tests pin its path, and the
  payoff the plan named (the `tools`/`conductor`/`expressions` drag and the cycle) is gone with
  this change and the earlier cycle cuts. `finance/filings.py`'s registration comment named an
  import chain that no longer exists; it now states the real one (`jazzx_sdk.tools` imports it).

- **Durable policy extraction runs** (+470 / -66 lines, 9 files). `PolicyExtractionService(store=)`
  records runs in an `ExtractionRunStore` (`server.policy_extract_runs`: the `ExtractionRun` model,
  the protocol, `InProcessExtractionRunStore`, which keeps the old `MAX_RUNS` cap; and
  `server.policy_extract_runs_db.DbExtractionRunStore`, table `japes_policy_extraction_run`, Plato
  migration 0015). The run still executes as a task in the replica that accepted the upload (the
  documents are not persisted: up to 25 MB each, and a resubmit is cheap), so a poll on another
  replica now reads it and a restart keeps its history. A running run marks itself every
  `EXTRACTION_HEARTBEAT_SECONDS` (30); one unmarked for `EXTRACTION_STALE_SECONDS` (300) is failed
  ("no progress since ...; its process stopped. Submit it again.") the next time any replica
  reads runs or checks for room, with no job role: the write is conditional on the heartbeat it
  read, and `finish` never overwrites a run that already ended, so a late outcome cannot revive a
  reclaimed run. A run cancelled at shutdown records `failed` with `STOPPED_ERROR`. `MAX_RUNS`
  counts running runs across replicas for the Db store. Breaking (SDK): the service's `get`,
  `runs_for` and `has_room` are async; `authoring_chat.extraction_status` awaits it. Plato's
  authoring router passes the Db store. The client has no authoring methods, and the route
  shapes are unchanged.

- **Pack lint: a threshold the rule's description does not state** (+125 / -0 lines, 2 files).
  `lint_pack` warns `threshold_not_in_description` when a rule's description states numbers and
  none of them is the numeric threshold its condition encodes: an `expression` value, or a `ratio`
  threshold resolved from the pack's profiles (decimal strings parsed), at any `all_of`/`any_of`
  depth. Stated numbers read `$1,500,000`, `$1.5MM`, `1.20x` and `75%` (also as 0.75), not section
  references like `STD-3.16`; a description stating no number is not checked. Warning, not error:
  a description may legitimately state only context numbers. Runs over the pack's own policies
  merged with the caller's (`_pack_policies`), so a pack with a Python registry pointer is checked
  only for the policies passed in. Clean on both seed packs and jaci's six packs; a changed DSCR
  in `DSCR-HIGH-LTV-DSCR`'s description is caught. Matrix cells are not compared (their values
  live in profile tables keyed by axis bands). The note's second rule (a value enumerated in one
  list must appear in every list enumerating the field) is not built: eligible/ineligible lists
  legitimately differ, so it needs a declared relation first.

- **`PolicyProfile` validates in a fresh process** (+20 / -9 lines, 4 files). Since the SDK's
  top-level names load lazily, nothing imported `finance.periods` before a profile was used, and
  `PolicyProfile.source_precedence`'s forward reference stayed unresolved: `PolicyProfile.from_yaml`
  (so `Pack.policy_profiles`) raised `class-not-fully-defined` unless something else had imported
  `finance`. `PolicyProfile.model_rebuild` now brings `SourcePrecedencePolicy` into scope itself
  (one ignored `fabric.canonical.profiles -> finance.periods` edge), replacing periods.py's
  module-level rebuild. A sweep of all 537 modules, each imported first, found no other model left
  incomplete; `test_a_policy_profile_validates_in_a_fresh_interpreter` fails on the old code.

- **Suspended case runs expire** (+115 / -29 lines, 8 files). `TurnRunStore.expire_suspended(older_than_seconds)`
  (in-process and Db) ends every run SUSPENDED since before the cutoff INTERRUPTED with stop reason
  `runs.schema.EXPIRED` and a terminal `{"done": true, "status": "interrupted"}` event; the Db store
  does it under the rows' locks, so it cannot race a `claim_suspended`. `Reaper(suspended_ttl_seconds=)`
  runs it on each sweep (default None: a suspended run waits indefinitely, as before). Plato's
  `job:run-reaper` reads `PLATO_SUSPENDED_RUN_TTL_SECONDS` (unset or 0: off); an expired run's
  `/resume` answers 409 like any run not waiting. The age is `updated_at`, which the suspend sets.
  The `reap_stale` docstrings are cut to two lines each.

- **Breaking (import paths): leaf utilities under `jazzx_sdk.util`** (+36 / -36 lines, 35 files).
  `jazzx_sdk.utc` is `jazzx_sdk.util.utc`, `jazzx_sdk.digest` is `jazzx_sdk.util.digest`, beside
  `jazzx_sdk.util.math.ratios`: modules with no SDK dependencies, in the lowest import layer, off
  the package root. The old paths are gone (no sibling repo imports them); the review's
  `old-paths-dropped-unshimmed` is accepted.

- **Import cycles a fresh `import` of an SDK package hit** (+422 / -386 lines, 11 files, two
  commits; most of it the `ratio` move). Reported by jaci-37 (`import jazzx_sdk.modes` first in a
  process failed), bisected to the 2.6.0 carve-out; the cause is the lazy `jazzx_sdk/__init__`,
  which no longer imports `fabric` first in an order that happened to resolve the cycles. Five
  packages failed alone (`modes`, `expressions`, `finance`, `statemachine`, `fabric.graph`); all
  pass at `origin/dev`. Fixes: `fabric.canonical` no longer imports `tools` (the ratio evaluator
  moves to `jazzx_sdk.util.math.ratios`, under a new lowest-layer `util` package of leaf
  utilities with no SDK dependencies, for `fabric`, `finance` and `formal` to import; `tools.ratio_evaluator` re-exports it; the canonical
  layer had depended on a higher one); `fabric/__init__`'s guidance re-exports and `evaluation/__init__`'s
  `EvaluatorMode` / `EvaluationReport` re-exports are lazy; `fabric.graph.proposal` imports the
  state-machine engine where it runs, and `condition_evaluator` the expression evaluator.
  `tests/test_import_each_package.py` imports all 74 packages, each in a fresh interpreter (about
  7 s, in parallel); it fails on the unfixed tree.

- **jaci-37's review: the four open items** (+282 / -145 lines, 14 files, 8 commits).
  - Governor citations (SDK): `_stale_citations` returns its findings (deduped, a legacy alias or
    a rule of a policy not in force) and they land on the decision as
    `policy_checks: [..., "policy_citations"]` and `required_actions: ["update the citation: ..."]`,
    not only a log line. A decision schema opts in with a `policy_clauses_cited` string array.
    The long rationale docstring is cut to two lines.
  - Pre-loop reasoning (SDK, client contract): `assess` runs deterministically first (an input
    refusal still raises), then reasons with a metered agent; a model error keeps the
    deterministic assessment. `CaseResult.pre_loop` records `reasoned`, `model`, `usage`,
    `cost_usd` and any `error`, carried across a suspension in its payload (not the context,
    which the governor's prompt reads). `conductor.pre_loop_model` picks the model.
    `TODO(python-rules-assessed-twice)`.
  - Eval pins (SDK, Plato): `pack` and `case_run` eval outputs carry `pack_version`;
    `pack.domain.MaterializedPacks` (per tenant, by content digest, `MATERIALIZED_PACKS_KEPT`)
    loads a version once in Plato's eval `pack_for`. `config.version` pins the experiment.
  - Client: `PlatoError` is an `httpx.HTTPError` and a `RuntimeError`.

- **An agentic turn's cost prices each model call by the model that served it** (+211 / -20
  lines, 11 files, five commits). A skill with its own `model` was costed at the parent's rate:
  turn usage carried only summed tokens (the SDK's shared `Usage` records no model), and
  `AgentTraceHooks` priced its totals at its one `model_name`. Found from macer's equivalent fix.
  - SDK: `OpenAIProvider.build_agent` records the model name on the agent (`MODEL_NAME_ATTR`,
    read by `agents.models.served_model`); `stream_hooks.ModelCallLedger`, an `AgentHooks`
    composed into the parent and every skill sub-agent for the turn, keeps token buckets per
    serving model; `llm.cost.cost_by_model`. A blocking agentic `respond` reports the ledger's
    token totals (retries included, so tokens and cost cover the same calls), `cost_usd`,
    `cost_by_model` and `cost_is_upper_bound`, also on a max-turns reply. `AgentTraceHooks` prices
    per serving model. The single-shot path now carries `cost_is_upper_bound` too.
  - Plato: no change; `/chat` passes `usage` through `reply_fields`.
  - Client: `contracts.TurnUsage` types `ChatReply.usage` (the SDK's usage keys plus the cost
    keys; a test holds them equal).
  - Left: streamed agentic turns carry no usage (as before); an agent a caller passes in through
    `tools=` is outside the ledger.

- **A step failure `on_step_error` recovers is logged with its traceback** (+19 / -0 lines, 2
  files). `ConductorEngine` recorded it only on the span and the step note, so a chat-lifecycle
  host lost the traceback its own code used to log (found reviewing jazzx-assistant's
  `dev-to-japes`, whose orchestrator failure became an `operator_detail` string).

- **jaci batch 1: Plato routes and client contracts for SDK-free DSCR and clinical intake, and
  three loop fixes** (+1541 / -48 lines, 35 files, thirteen commits). From jaci's config-first inventory.
  - Fixes in `pipelines/kinds.py`: `sdk_mode_factory` gives the governor the pack's
    `policy_registry` (its citation and sunset checks ran nowhere on Plato); the investigator's
    request shape is `conductor.rich_evidence_requests` (default true, as before); new
    `conductor.pre_loop_reasoning` (default false) hands the run's `ReasoningAgent` to the
    pre-loop `assess`, which `CaseRunService` builds only for an investigation-loop pack that sets
    it. Reported but not a bug: schema-derived models admitting a null for an optional
    non-nullable property is deliberate (strict structured output fills every field), and a test
    pins it.
  - Packs: `GET /packs/{id}/active` (version, digest, activated at/by from the audit trail; 404
    with none), `GET /packs/{id}/{v}/describe` (`pack.inventory.describe_pack`: policies, programs,
    default program, profiles, ontology, conductor, modes, evidence types, playbooks, skills,
    metrics, checkpoints, every `*_schema` the conductor names; a part that fails is
    `<part>_error`), `content_digest` on `PackCheckReport` (what publish records).
  - `GET /whoami` (`server.whoami`: tenant, identity, `may_author`; no roles, which japes has no
    source for) and `GET /info/catalog` (`server.catalog.platform_catalog`: modes, conductor,
    pre-loop, condition, guardrail, compose, ground kinds, evidence sources and connectors,
    scorers); `condition_evaluator.condition_kinds()`.
  - Assistants: `GET /assistants` and `/assistants/{id}` (`AssistantRuntime.assistants` /
    `describe`, over a new `assistant_ids()` on both manifest stores), read-gated;
    `GET .../sessions/{sid}/progress` (`SessionRecorder.progress`, close's summary without
    writing); session create takes `pack_version` (409 unless served) and `scripted_replies`
    (relaxed posture only, 403 otherwise; per replica, through `AssistantRuntime.agent_with_llm`
    and a `ScriptedLLM`); the session and `/chat` reply carry `pack` (the serving assistant pack's
    id, version, digest).
  - Canonical reads scoped by owner, not `trace_routes` (the canonical store is not tenant-keyed,
    so a by-id read would cross tenants): `GET /runs/{id}/chain` (`CaseRunService.chain`) and
    `GET .../sessions/{sid}/chain` (`SessionRecorder.chain`): Trace, Decision, Outcomes.
  - Eval: `case_run` (`pack.eval_invoker.CaseRunInvoker`, the conductor without suspension) and
    `assistant_session` (`server.eval_api.AssistantSessionInvoker`, scripted turns in one session;
    output the session summary, or each answer) entities, wired in Plato. Scorers in
    `jazzx_eval_contracts`: `field_path`, `ratio`, `banded`, `at_least` (each over
    `actual_path`/`expected_path`); a configurable scorer built with no config takes it from the
    template's `params`, so `standard_scorers` registers regex, contains, schema_compliance, array
    and the four.
  - `jazzx-plato-client`: `contracts` (Evidence, Decision, Trace, Outcome, Refusal,
    PackCheckReport, ActivePack, PolicyAssessment, CaseResult, CaseRunChain, WhoAmI, ChatReply,
    SessionRecord, SessionProgress; extra fields allowed; a test holds their fields to the
    server's models) and methods for every new route plus pack contents/history and the eval
    datasets/experiments/scorers. Methods still answer dicts.
  - Review fixes: `pack.case_runs.pre_loop_agent` builds the pre-loop agent for both a run and
    a `case_run` eval (`CaseRunInvoker(agents=)`); scripted replies only on a new session (409),
    dropped on DELETE; `banded` matches an expected label before reading it as a number; the
    catalog's scorers come from `standard_scorers(llm)`; a session eval's turn scope wins over the
    experiment's. Left: a scripted session the idle sweep expires keeps its in-memory script, and
    two concurrent scripted creates race (relaxed demo only).
  - jaci's review of the batch (+353 / -76 lines, 24 files, four commits): `jazzx-plato-client`
    declares `pydantic` (a test reads each light package's imports against its declared
    dependencies); `FeedbackApiSink` keeps its token and identity when the caller's provider
    raises; an empty `session_id` is refused and scripts are looked up only for a real one, and a
    used-up script fails the turn; retiring the active version is a 409, and `/active` answers the
    served version (activated, else the newest) with `pinned`; `describe` without a registered
    profile answers `profile_error`; the `assistant_session` eval closes its session and scores
    the close, output always `{replies, ...}`; a `case_run` eval reports
    `checkpoint: {"skipped": <name>}`; a scorer spec's unknown `params` are refused when the
    template is built; `field_path` compares numbers only for real numbers, `ratio` refuses
    low > high, `banded` refuses repeated edges and NaN; the client's stream parser follows the
    event-stream rules; the client's and the SDK's `pack_archive` share one rule (any dot-named
    member skipped, an assistant folder's domain manifest left out, the SDK's timestamp and mode)
    and zip a folder to the same bytes; `describe` reports a schema error per entry and the pack
    path as `<pack>`; `progress` with no turns is incomplete (the rule in `_summary`);
    `store.is_pack_content` is the one content rule (archive, `DirectoryPackSource.read`, the
    contents listing). Client-zipped digests change once (timestamp and mode now the SDK's); a republish is still `unchanged`, since `publish_pack` compares members, and the client's member set changes only for a `.pyc`/`.pyo` outside `__pycache__`. Left: pre-loop reasoning's failure
    mode, usage and model; eval case runs unpinned; idempotency where no store is wired; scripted
    sessions per replica.
  - Pack activation across replicas (+130 / -12 lines, 7 files, five commits), from jaci's
    verification pass and the review after it. Pins load per replica at boot, while the durable
    `PLATO_ACTIVE_PACK` row is shared:
    - an activation merges into the stored value (`_stored_active`), not this replica's
      environment, which erased another replica's entry for a different pack (pre-existing);
    - retiring a version refuses the replica's pin or the stored one (`_durably_active`);
    - `If-Match` on activate compares with `_expected_active` (stored, else this replica's), and
      `/active` reports that as `stored_version` ("" for none), so it round-trips; the client's
      `activate_pack(if_match=)` sends it and `ActivePack.stored_version` types it; the quickstart
      names it;
    - `poetry.lock` relocked (`jazzx-plato-client`'s `pydantic`); the describe test also deletes a
      schema, the case that carries a path.
    - Left: `TODO(activation-merge-lost-update)`: two overlapping activations of different packs
      keep only the later write (no compare-and-set on the settings store).
  - **Breaking: governed-route idempotency replays the first answer** (+585 / -36 lines, 14
    files, four commits). `GovernedRouter` required an `Idempotency-Key` but nothing recorded a
    response, so a retry ran again; with a store it answered a stored receipt as 409, and keys
    were global. Now `jazzx_sdk.server.idempotency` (`RequestIdempotencyStore`: `begin` /
    `complete` / `abandon`, `InProcessRequestIdempotencyStore`, `request_hash`) and
    `server.idempotency_db.DbRequestIdempotencyStore` (table `japes_request_idempotency`, keyed
    tenant + `METHOD route-template` + key; Plato migration `0014_request_idempotency`). A
    mutating governed route claims the key against a hash of method, path with query, body and
    caller (`acting_user_id`); a repeat gets the first JSON response with `Idempotent-Replayed:
    true`, 409 while it runs, 422 for the key on another request or caller. A streamed, non-JSON
    or failed answer is released, so its retry runs. Retention `IDEMPOTENCY_RETENTION_SECONDS`
    (a day; `complete` purges the tenant's older rows), a dead claim frees after
    `IDEMPOTENCY_PENDING_SECONDS` (30 min). `GovernedRouter(idempotency_store_for=request ->
    store)` for a per-tenant store; an old `get`/`put` store is refused at construction. Sync
    endpoints run in the threadpool. Plato wires it by default (`PlatoWiring.idempotency_store_for`,
    tenant -> store) on the assistants and case-run routers. Not covered: the plain-`APIRouter`
    routes (pack publish/activate, eval, feedback), which are naturally repeat-safe or refuse a
    duplicate; a response model is not applied to a replay; a blocking turn past the pending
    window can run twice.
  - Not done here (jaci's later batches): composition, manifest asset keys, documents, finance,
    loop knobs, `/assess` options.

- **Plato's reusable logic moved into the SDK; Plato routes are HTTP translation over it**
  (+1633 / -1385 lines, 65 files, nine commits). No behavior change to Plato's routes; stored
  rows read as before (Plato passes its own table and key names in).
  - Loader and check: `jazzx_sdk.pack.assistant` and `jazzx_sdk.pack.check` (from `plato.packs`,
    removed); `pack.store.published_roots` shared by `published_registries` and
    `published_domain_packs` (+102 / -174, 22 files).
  - `pack.domain`: `domain_pack_record`, `materialized_pack`, `NotADomainPack`,
    `PackNamesPython`; `server.gates.write_gate` / `read_gate`; `audit.record_config_change`;
    `identity.acting_approver`; `Outcome.reviewer_answer`; `check_if_match` takes a string;
    `DbSettingsStore(table=)` / `setting_model(table)` with a per-table metadata, so Plato keeps
    `plato_setting` with no data migration (+225 / -136, 20 files).
  - `pack.activation`: `TenantPackRegistries` (pins, per-tenant registries, `activate`, `forget`,
    `on_invalidate`) and `Registries`, `parse_pack_reference`, `pack_references`,
    `with_pack_reference`, `has_assistants`, `register_assistants` (+284 / -249, 4 files).
  - `pack.case_runs.CaseRunService` (`submit`, `resume`, `record_outcome`, `view`, `owns`,
    `pinned_pack`) with `CaseRunKeys` naming the run-input keys, `RunNotWaiting`,
    `RunHasNoDecision`, `case_queue_key` (+275 / -170, 2 files).
  - `formal.local`: the bounded Z3 worker (`python -m jazzx_sdk.formal.local`), `run_local_worker`,
    `formal_slot`, `compile_packs`, `split_compile`, `PackCompile`, `LocalFormalError(kind)`;
    Plato keeps its posture gate, enable flag, origin/size checks and the kind-to-status map
    (+320 / -294, 6 files).
  - Chat host helpers: `pipelines.chat.agent_lifecycle` / `LifecycleUnrunnable`;
    `recorder.agent_recorder` / `recorded`; `session.session_expired`; `response.reply_fields`;
    Plato's `/chat` and streamed turn share one `_prepared` (+166 / -74, 6 files).
  - Drafts: `draft_db.text_files`, `draft_pack`, `apply_persona_prompt`, `PROFILE_PATH`;
    `seed.sample_packs(root)`; `inventory.read_pack_contents` (raises `PackNotFound` /
    `FileNotFoundError`; Plato maps 404) (+201 / -173, 7 files).
  - `server.feedback_api.db_feedback_processor` (Plato's job and route built it twice);
    `server.uploads.read_capped` (+49 / -33, 5 files). `policy_extract_api`'s single bounded
    read is left as is: already capped, its own message.
  - `agents.interactive.kernel_agents` (from `plato.kernel_sync`, removed), prose trimmed
    (+16 / -87, 3 files).
  - Review fixes (+59 / -10, 7 files): `compile_packs` takes a validated request too;
    `reply_fields` dumps `output` by alias, as `jsonable_encoder` did; resume checks the run is
    suspended before the approver (409 before 422, as before); `NoCanonicalStore` is the unwired
    refusal (503, bounded reason), so a store write failure is a 500 again.

- **The SDK talks to Plato through `jazzx-plato-client`** (+34 / -12 lines, 5 files).
  `FeedbackApiSink` posted to Plato's `/feedback` with its own httpx code; it now builds the body
  and calls `PlatoClient.submit_feedback` (`prefix=""` on its API-root URL), passing its identity
  headers and bearer token through the client's header provider, the sink's own winning as
  before. Constructor unchanged; callers are tests only. Two client changes it needed:
  `tenant_id` may be None (no `X-Tenant-Id`), and `PlatoError` is now an `httpx.HTTPError`, so the
  sink's documented error type holds and `except httpx.HTTPError` catches client refusals.
  - Import-linter: `jazzx_plato_client` and `jazzx_eval_contracts` are root packages, and a new
    contract forbids them importing `jazzx_sdk`, `plato` or `common`. The CI job installs both
    editable (`--no-deps`) first: uninstalled, the repo-root folder of the same name resolves
    instead of the package. Reproduced in a clean venv: 5 contracts kept.

- **`jazzx-plato-client`: `health()` and `turn_feedback(...)`**, asked for by jaci's adoption.
  `health()` reads `GET /health` at the service root (outside the API prefix; Plato serves it
  there). `turn_feedback(conversation_id=, message_id=, reaction=, rating=, text=, trace_id=,
  agent_id=, source=, **fields)` builds a `submit_feedback` body with the SDK's `Feedback.for_turn`
  fields, leaving unset ones out; `DEFAULT_REACTION` / `DEFAULT_SOURCE` are held to the SDK's
  `Reaction.NEUTRAL` / `FeedbackSource.USER`, and the body validates as `FeedbackSubmit`.

- **Breaking (packaging): `server` and `documents` extras** (+141 / -38 lines, 14 files).
  - `server` = uvicorn: server and dual modes need `japes[server]`; without it
    `_create_uvicorn_server` raises an `ImportError` naming the extra. FastAPI stays in core:
    `common.core` (which the queue runtime imports) imports it at load, so it cannot move until
    `common` stops doing that (a common-repo change).
  - `documents` = pymupdf, python-docx, beautifulsoup4, feedparser. Every import is on use, through
    `tools/documents/_deps.require(module, purpose)` (raises `ImportError` naming the extra) or the
    readers' own `DocumentConversionError`; the RSS connector's module-level `feedparser` import is
    now on use too. HTML text extraction already fell back without bs4.
  - `plato` includes both (and `anthropic`), so the image and CI are unchanged. Tests: core imports
    with the libraries blocked and both errors name their extra; the CI-extras check lists the
    three new extras as subsets of `plato`; the submodule-deps check reads a lock marker given per
    group (`{main = ..., dev = ...}`), which the relock produced for two packages.
  - Consumers: **jaci** runs server mode and the document tools: `japes[server,documents]`
    (it declares `pymupdf` itself). **jazzx-assistant** runs the queue runtime (no `server`) and
    calls `jazzx_sdk.tools.to_markdown`: `japes[mlflow,documents]`; its mock Hub/API apps import
    fastapi, still core. **juno** declares fastapi and uvicorn itself and imports only
    `ClientLayer` from japes.
- **`jazzx-eval-scorers` folded into `jazzx-eval-contracts`** as `jazzx_eval_contracts.scorers`
  (`git mv`; +70 / -114 lines, 17 files): one light evaluation package for eval-service instead of
  two. Contracts' floor drops to Python 3.11 (its code parses under the 3.11 grammar; no 3.12-only
  APIs), gains the `schema` extra (`jsonschema`), and its description widens to contracts and
  scorers, pydantic only. Version stays 0.1.0. SDK re-exports and the Dockerfile follow.

- **Breaking (packaging): `anthropic` leaves core** (+47 / -7 lines, 4 files). It is the new
  `anthropic` extra, and `plato` includes it. `AgentExecutionService` no longer imports the
  Anthropic provider at module load: `.anthropic` imports it on first use, and without the SDK
  raises an `ImportError` naming `japes[anthropic]`; `jazzx_sdk.llm.AnthropicProvider` already
  resolved lazily to a placeholder that says the same on construction. A test blocks the import
  and checks both. Consumers: jaci pins `anthropic` itself; jazzx-assistant and juno do not use it
  through japes. CI's test job installs `plato`, so the suite still has it.
- **`import jazzx_sdk` loads 269 modules, not 1,927**: no runtime, queue, `common`, fastapi or Azure.
  Every name outside the message models, the handler interface and identity resolves on first
  access through the existing `_LAZY_ATTRS`; `test_import_boundary` now asserts none of
  fastapi/starlette/azure/common loads. Full suite green (7,470).
- **Docstrings and comments trimmed** (`-127 / +31`), mostly the scorer code moved into
  `jazzx-eval-scorers`, which had carried long history-laden docstrings and em-dashes.

- **`jazzx-eval-scorers`, the scorers without the SDK** (+1259 / -615 lines, 14 files). eval-service
  cannot install japes (Python 3.11 vs >=3.12, `cryptography ^49` vs `>=50`, two top-level
  `common` packages, path dependencies, ~1,900 modules on import); this is what it can take.
  - `jazzx_eval_scorers/` beside the other two distributions: pydantic only, `python >=3.11`,
    extra `schema` (`jsonschema`). `core.py` is the former `evaluation/scorers.py` (ScorerResult,
    Finding, FunctionScorer, CompositeScorer, AdjudicatorScorer and its policies, ScorerRegistry,
    ScorerSpec/build_composite, ScorerInfo, Prediction); `metrics.py` moves whole. `_support.py`
    restates the two SDK helpers they used (a freezable name registry; `call_maybe_async`,
    sync callables on a worker thread). Importing it loads no `jazzx_sdk`, `plato`, `common`,
    `fastapi` or `azure` module (a subprocess test holds it).
  - `judge.py`: `JudgeScorer(judge, ...)` and `judge_policy`, over a caller's
    `judge(prompt) -> JudgeVerdict` coroutine. The SDK's `LLMJudgeScorer(llm, ...)` is a subclass
    over `model_judge(llm)` (`structured_call`), and its `llm_judge` policy accepts `llm=` or
    `judge=`; prompts unchanged.
  - `primitives.py`, from eval-service's set, reshaped to the `Scorer` protocol (configuration
    at construction, overridable from the score context as `ScorerSpec.params` arrive; a bad
    configuration refused at construction; `score` always in [0, 1], counts in `metrics`, detail
    in `metadata`): `RegexScorer` (flags by name, `search`/`match`/`fullmatch`, group
    assertions, input capped at `DEFAULT_MAX_INPUT_CHARS`), `ContainsScorer` (`all`/`any`,
    expected text as the fallback needle), `SchemaComplianceScorer` (Draft 7, JSON text parsed,
    errors with their paths), `ArrayScorer` with `EquivalenceRule` / `labels_equivalent`
    (rows by key or key pair, per-field and combined/any-field accuracy, present rate, missing
    and extra counts, `treat_missing_as_fail`; passes at `threshold`, and an unknown
    `primary_metric` is an error where eval-service fell back silently).
  - `jazzx_sdk.evaluation.scorers` and `.metrics` re-export; every existing import works and is
    the same class. `pyproject.toml` path dependency with the `schema` extra, lock updated,
    Dockerfile copies it and the image smoke imports `jazzx_eval_scorers.core`.
  - Not moved: trajectory and operational scorers (they read `CanonicalTrace`), QA and custom
    scorers. Next: the eval-service PR swaps its primitives onto this package.
- **Fix:** the pack audit read `X-Trace-Id` without `header_text` (`test_authority` caught it).

- **openai-agents locked at 0.22.3** (from 0.22.0; the `>=0.22.0` floor unchanged). Patch releases:
  concurrent async SQLite session startup (japes uses `SQLiteSession`), conditional approvals
  checked against validated arguments, subprocesses reaped on an early stream close, a missing
  `OPENAI_API_KEY` no longer cached; 0.22.1 added configurable output-guardrail blocked messages
  and server-wide guardrails on MCP tools, unused here so far. Its new dependency floors
  (`httpx2`, `pyjwt`, `starlette`, `urllib3`) were already met by the lock. Agent, session, MCP,
  guardrail and chat suites pass (763).

- **`tenant_id` in a key on six shipped tables** (+58 / -10 lines, 7 files). `eval_experiment`,
  `eval_case_run`, `eval_optimization_job`, `eval_custom_scorer_revision`, `eval_dataset_version`
  and `japes_feedback_history` carried `tenant_id` as an indexed column only. Each gains a unique
  constraint on `tenant_id` plus a key that is already unique (the primary key, or the existing
  unique pair), the shape `turn_run` and `model_overlay` use, so no row can violate it and no
  key changes. Plato migration `0013_tenant_keys` (batch mode, so sqlite rebuilds the table);
  checked against a populated 0012 database: rows kept, constraints present. The tenancy guard
  checks `register_all`'s tables with no exceptions; `TODO(shipped-tables-untenanted)` is closed.

- **Review round 1 fixes** (+179 / -33 lines, 14 files), from the adversarial review over
  `origin/dev..HEAD`.
  - `conductor_suspension` keys on `tenant_id` (`DbSuspensionStore(db, tenant_id=)`, every query
    scoped; migration `0011` gains the column in the primary key). Plato's runs router takes
    `suspension_store_for(tenant)` instead of one store. `tests/test_plato_tenancy.py`'s guard ran
    against an empty registry since Phase 0b; it now checks `register_all`'s tables, and lists six
    shipped 2.5.5 tables that carry `tenant_id` as an indexed column rather than in a key
    (`TODO(shipped-tables-untenanted)`) so a new one fails.
  - A replacement decision is validated against the pack's decision schema in the resume route
    (`kinds.check_resolution`), before the run is claimed: 422 and the run stays suspended,
    where it used to be claimed and then fail for good in the background.
  - `CaseRunner.execute` ends a run INTERRUPTED when a stop was asked while it ran to its
    checkpoint (it finished SUSPENDED with the flag set, and nothing could then resume or end it).
  - Materialize: a request joining a download whose owner was cancelled fetches afresh instead of
    raising `CancelledError`; `TieredMaterialization.one` serves from disk only a file this call
    wrote (one left by an earlier run went out as current while the background tier replaced it).
  - `GET /packs/{id}/history` keeps only pack and activation events; the client README installs
    from `main`, as the top-level README does.
  - Round 2 passed. Folded in after: `resume_investigation_case` calls `check_resolution`
    rather than restating its two checks (+3 / -3 lines). Notes left as they are: the cancel
    route is not tenant-scoped (unmounted; a service mounts it with its own `auth`); the
    approver guard runs per run, not at router build (Plato passes `require_approver=True`); a
    run stopped while suspended leaves its suspension row `suspended` (unreachable through the
    run); an assistant whose closure does not resolve serves with `release_id=""`; and
    `DSCR_STANDARD`'s 3.1.0 after losing its PPP rules (the seed regroup carried in from 2.5.7).

- **Tiered materialize** (+280 / -60 lines, 3 files), the tiered-materialize plan's three steps
  for jazzx-assistant's grounding latency. Its own precondition is still open: nobody has broken
  grounding into listing, probe, fetch and post-processing, so whether the fan-out is the cost is
  unmeasured.
  - In-flight dedup: `DocStore._inflight` maps `(collection_id, doc_id)` to the download in
    progress; a second request joins it (`asyncio.shield`), a failed one is dropped so a later
    request fetches afresh, and an owner's exception is marked retrieved.
  - Atomic writes: `_write_atomically` writes beside the target and `os.replace`s it, so the
    "already on disk" check never sees a partial file. Text is decoded as `encoding` and written
    as UTF-8 (`Path.write_text` used the locale's encoding).
  - `materialize_tiered(entities, output_dir, required=, doc_id_field=, name_fn=, ...)`: awaits
    the entities `required(entity)` admits, then starts the rest as a task
    (`TieredMaterialization.pending`; a failure is logged). Filenames come from
    `_named_documents` over the whole set (the suffix logic `materialize` used inline, now a
    module function both call), so the tiers name exactly as one call would; `display_name_fn`
    defaults to the raw `name_fn`, as before. The background tier starts after the required one
    has saved its manifest, so the two never race on a scope. `TieredMaterialization.one(entity)`
    returns a document from disk once written, else fetches it now, joining a background download
    in flight. Exported from `jazzx_sdk.fabric.docs`.
  - `materialize` without tiers behaves as before. Tests: the required tier returns while the
    rest downloads, colliding names across tiers, a mid-download request joining (one fetch), a
    second request served from disk, no `.part` file left.
  - The pack-store plan's remaining steps (`pack_dependency`, `pack_status`, the layered
    resolver) are each gated on a condition that has not arisen (a pack depending on another,
    operated certification, a second layer); nothing built.

- **Fix: concurrent run claims on sqlite all won** (+44 / -9 lines, 3 files). Closes
  `TODO(sqlite-read-then-write-unserialized)`, which called this unverified: a probe with ten
  claimers on one key returned the same run to all ten, each with its own token (one RUNNING
  row, ten executors). sqlite takes no row lock and the key's advisory lock is Postgres-only, so
  every racer read the key idle. `DbTurnRunStore._claim` is now a compare-and-set: an `UPDATE`
  conditioned on the status that was read, `rowcount == 1` or the claimer gets None. Covers
  `claim_next`, `claim_any` and `claim_suspended` on every backend. New test races ten claims
  (both shapes) on sqlite and expects one winner.
  - The other five deferred TODOs stay, their reasons unchanged: `reasoned-assess-runs-twice`
    (a cost only, under `?reason=true`; folding the passes would map a model failure to 422),
    `case-run-assess-unreasoned` (a deliberate default), `switched-store-not-backfilled` (needs
    a bounded backfill; rare), `zero-width-only-pattern-accepted` (undecidable in general), and
    `supersede-check-outside-admit-lock` (one await wide, needs a store mutation).

- **anthropic 1.x compatibility** (+100 / -6 lines, 5 files). anthropic 1.0 (1.11 is current)
  dropped `temperature`, `top_p` and `top_k` from `messages.create`/`stream`; the API still takes
  them. `llm.anthropic_wire.wire_params(params)` moves them into `extra_body` when the installed
  SDK's major version is 1 or later (`importlib.metadata`, cached), and passes them as arguments
  before. All five call sites go through it: `AnthropicProvider` (create, stream),
  `agents.anthropic_provider` (create with retries), `AnthropicNativeModel` (create, stream).
  Checked against a real anthropic 1.11 client on a mock transport: the temperature arrives in
  the request body. Also found: 1.x runs on `httpx2` and refuses an `httpx` client object; japes
  builds `AsyncAnthropic(api_key=)` only, so that does not reach it. The lock stays on 0.111 (the
  floor is `>=0.69.0`): moving it to 1.x is a separate decision, and wants the gated live smoke
  per provider, since every anthropic test mocks the client.

- **`jazzx_plato_client.packs`** (+187 / -1 lines, 4 files), the client plan's Phase 2: jaci's
  pack packaging, for any author. `pack_archive(folder)` (sorted members, `ZIP_EPOCH`
  timestamps, `MEMBER_MODE`; dotfiles and `__pycache__` left out; an assistant folder's
  `pack_manifest.yaml` left out, since Plato refuses an archive with both manifests),
  `archive_files`, `pack_manifest`, `is_assistant_folder`, and `publish_pack(plato, folder,
  activate=)`: check, refuse on a blocking finding (`ValueError` listing every error), publish,
  and on a 409 compare contents: identical is `unchanged`, different raises
  `PackVersionConflictError`. Tests against a real Plato cover deterministic bytes, the
  assistant-folder rule, idempotent republish, the conflict and a blocking check; the lightness
  probe imports `packs` too. jaci adopts it in its own change (its `scenarios/shared/plato.py`
  copies can go).

- **`jazzx-plato-client`, a Plato client without the SDK** (+450 / -262 lines, 10 files).
  Importing `jazzx_sdk.clients.plato_client` loaded about 1,500 modules (FastAPI, Azure,
  `common`) for a client that needs httpx. Decisions taken as the plan recommended: versioned in
  lockstep with Plato (0.1.9), pack packaging belongs in it (its Phase 2), no SDK bump.
  - `jazzx_plato_client/` beside `jazzx_eval_contracts/`, its own `pyproject.toml` (httpx,
    pyyaml), `README.md`. `client.py` is the former `jazzx_sdk/clients/plato_client.py`; the
    request-header forwarding is inlined (an `httpx` request hook, a raising provider logged and
    skipped) instead of `_header_hooks`. Git records it as a new file: the SDK path keeps a
    re-export of the public names, so `from jazzx_sdk.clients.plato_client import PlatoClient`
    still works and is the same class.
  - New: `server_info()` (`GET /info`), `submit_feedback(feedback, idempotency_key=)` (`POST
    /feedback` with `FeedbackSubmit`'s fields; a retry with the same `feedback_id` returns the
    stored record), and `ASSISTANT_ENTITY` / `TURN_METADATA_KEY`, restated like `DEFAULT_PREFIX`.
  - The SDK takes it as a `develop = true` path dependency (`poetry.lock` gains only that entry);
    the Dockerfile copies the project root into the builder and the package into the runtime
    stage, as for `jazzx_eval_contracts`, and the image smoke imports `jazzx_plato_client.client`.
  - Tests: the client tests import from `jazzx_plato_client`; the constants and the version are
    held to the server's and to `plato/_version.py` (package and `pyproject.toml`); a subprocess
    imports the package and asserts no `jazzx_sdk`, `plato`, `common` or `fastapi` module loaded;
    the SDK path is the same class; feedback and `/info` round-trip against `create_plato_app`.
  - README install line. Phase 2 (pack packaging from jaci) and jaci's adoption follow.

- **One declaration of the token buckets** (+40 / -23 lines, 5 files).
  `llm.cost_tracker.TOKEN_BUCKETS` (`CostRecord`'s five `*_tokens` fields) and `USAGE_KEYS`
  (those plus `total_tokens`). Derived from them: `pipelines.chat._turn_metrics`' zero-filled
  union, `agents_tracing.extract_token_usage`'s empty report, `CostTracker.get_token_breakdown`,
  and the OpenAI provider's empty usage. A test holds `TOKEN_BUCKETS` to `CostRecord`'s fields and
  every emitter to `USAGE_KEYS`, so a sixth bucket (image tokens) has one home. The rest of the
  vision plan was already built (`ImagePart`, `supports_vision`'s reader, `render_pdf_pages`,
  windowed image classification, Gemini parts); accuracy against labelled scans stays unmeasured.

- **Split: the identity veto** (+50 / -1 lines, 2 files). `split_document(identity_of=)`: an
  awaitable `(page, text) -> str | None` reading a page's printed identity (a name, an account
  number). Pages of one label whose identities differ are cut into separate segments, compared
  case- and spacing-insensitively; a page without one carries the last seen. Called only for
  pages in runs longer than one, under the split's `concurrency`. The vision plan's second P4
  idea: an identity mismatch is a hard veto, not a score a continuous-looking page can outvote.
  No default reader ships: the caller chooses the model and prompt ("transcribe, never infer").

- **Config versioning: audit trail, releases, conditional activation** (+344 / -17 lines, 15
  files). The config-versioning plan's Rev 2: Plato's pack store already is the immutable,
  content-addressed version store and activation its alias, so this wires what was missing rather
  than adding Skill/Profile version stores (Phase 3 superseded; Phase 7 dropped: no caller of
  `PUT /agents` in jaci, jazzx-assistant or juno, and Plato does not mount it).
  - Audit: Plato's pack routes append `ConfigAuditEvent`s to the tenant's `DbConfigAuditStore`
    (registered since 2.5.x, never written): `publish` (`target_kind="pack"`, the version,
    `after_digest` = the archive's content digest, `reason` = how it arrived: upload, sample,
    draft), `promote` on activation (`target_kind="pack_activation"`, `reason="from <previous>"`,
    before/after digests of the two versions), `retire` on delete. Actor `acting_user_id()`,
    trace from `X-Trace-Id`, source `plato.packs`; best effort (`record_best_effort`).
    `GET {prefix}/packs/{pack_id}/history` reads the trail, oldest first.
  - Activation: `If-Match: <active version>` ("" for none) makes it conditional; a stale value is
    a 409 naming the active version. Not atomic with the pointer write; absent means as before.
  - Releases: `release.release_from_registries(assistant_id, profile, profiles=, skills=, pins=)`
    freezes an assistant from live registries: each profile and skill its closure reaches
    (through `spec_ref`) pinned at the digest of its content (`CONTENT_PIN_LENGTH` chars as the
    version), guardrails and MCP servers by name, extra pins as given, validated by
    `freeze_release`. `ManifestRecord.release_id` (both manifest stores; `put(release_id=)`;
    Plato migration `0012_manifest_release`). Plato's `_register_assistants` freezes each
    composed assistant and writes a new head when the manifest *or* the release differs (a
    `ReleaseError` is logged and registers with none). `AssistantRuntime.binding(tenant,
    assistant) -> (agent, release_id)`; `agent_for` returns its agent. `/chat`'s `ChatReply`
    carries `release_id`. `AssistantKey`'s docstring no longer says the field is always empty.
  - Not in this: the streamed turn's release (`TODO(stream-release-id)`: it binds after the first
    frame); stamping the release on traces (`VersionBundle` is frozen under Spec v1.5, a
    cross-team change); audit of assistant registration; an atomic compare-and-set for the
    activation pointer.

- **Queue execution cancellation** (+275 / -5 lines, 8 files). A caller or operator can end a
  queue job before its lease runs out, through the execution record the worker already holds.
  - `QueueExecution.cancel_requested` / `cancel_reason`; `QueueExecutionStore.request_cancel(key,
    reason=)` on both stores. It creates the record when no worker has claimed the message yet
    (so the claim sees the flag), sets the flag on a PROCESSING one, and is a no-op (False) once a
    response exists (`SETTLED_STATUSES`: ready, delivering, completed). `DbQueueExecutionStore`
    gains two nullable columns, `cancel_requested` and `cancel_reason`: **the consuming service's
    migration for `japes_queue_execution` must add them.**
  - Runtime: an execution claimed with the flag already set settles `cancelled_response` without
    running the handler; a running one is read on each lease renewal, its handler task cancelled,
    and the same response settled through `store_result` / `mark_response_sent`, so a redelivery
    replays it. Latency is one renewal interval: `QueueSettings.lease_renewal_seconds` (capped by
    a third of the visibility timeout and of the lease) is the knob, no separate poller. A
    renewal that returns while the handler has already finished takes the handler's response.
    SIGTERM is unchanged: no flag, so the lease expires and another replica takes it.
    `jazzx_sdk.runtime.CANCELLED_STATUS = "cancelled"`; `ResponseMessage.status` lists it.
  - `jazzx_sdk.server.create_queue_cancel_router(store, prefix="/queue", auth=)`:
    `POST {prefix}/executions/{message_id}/cancel` with an optional `{reason}`, a governed route
    (X-Trace-Id) that refuses without `auth` in a deployed posture; the service mounts it through
    `serve(extra_routes=...)`. Not mounted automatically.
  - Not in this: `process_queue_until_empty` (unchanged, as the plan scoped it).

- **Human checkpoints in case runs** (+938 / -136 lines, 22 files). A case run can stop for a
  person and continue on their answer, in one run and one journal.
  - `conductor.human_checkpoint: <name>` on an `investigation_loop` pack, naming one of the
    manifest's `human_checkpoints` (the publish check reports one it does not declare). Given a
    `suspension_store=`, a run with a decision raises `SuspendRun` at a `human_checkpoint` step
    between the governor and the narrator; its payload carries the decision, the governor's
    verdict and the mode calls so far. `CaseResult.status == "suspended"`, `CaseResult.suspension`
    holds the id, and nothing is persisted yet. Without a store the step is not in the pipeline,
    which is how jaci's in-process runs and the eval invoker behave unchanged.
  - `resume_case(pack, inputs, suspension_id=, resolution=CheckpointResolution, approver=ActorRef,
    authority_basis=)`: the engine's `resume_durable` (single claim; the store's
    `require_approver`), with a new `restore=` hook that rebuilds the typed `Context`, the
    reasoner's decision and the `GovernorDecision` from a store that keeps them as JSON
    (`DbSuspensionStore`). `CheckpointResolution`: `approved`; `decision` replaces the reasoner's
    and needs `rationale`, a valid `OverrideReasonCode` and (at resume) an `authority_basis`; a
    rejection skips the narrator. The persisted Trace has the reviewer's step (mode governor, the
    approver's `ActorRef`) between the calls before and after; a replacement is an `OverrideEvent`
    on the reasoner's step with `superseding_decision_id`, `state_before`/`state_after`. The
    Decision's `human_review_required` is false once approved (unless a mode failed), true on a
    rejection. `CaseResult.checkpoint` records name, approval, replacement, approver, authority.
    `run_investigation_case` is now built over a `_Case` (types, engine, finish) shared with the
    resume; `investigation_loop.investigation_engine` is the engine `run_investigation` builds.
  - Runs: `TurnRunStatus.SUSPENDED`, neither active nor terminal: it holds no claim, does not
    block its key's FIFO, is not reaped or purged. `CaseRunner.execute` ends a suspended segment
    with `{"suspended": true, "status", "output"}` (not `done`); `ResilientRunner.resume` stops
    following at a suspended run. `TurnRunStore.claim_suspended` (both stores; the Db one under
    the key's advisory lock and the row's) moves SUSPENDED to RUNNING unless a stop was asked or
    the key has a run RUNNING; `CaseRunner.claim_suspended` returns the run and its token.
    `CaseRunner.request_stop` ends a suspended run INTERRUPTED (the flag first, so a resume
    cannot take it after). The runs contract's status set gains `suspended`.
  - Plato: `POST {prefix}/runs/{run_id}/resume` (`ResumeRequest`): 409 unless SUSPENDED or when
    the case has a run going, 422 for no approver or a replacement without `authority_basis`,
    202 and the stream. The approver is the governed caller (`actor_ref`); the body's `approver`
    only where the request carries none and the deployment does not require identity.
    `POST {prefix}/runs/{run_id}/outcome` (`RunOutcomeRequest`): an `Outcome` on the run's
    Decision, 409 without one. The stop route ends a suspended run. `GET /runs/{id}` shows
    `suspension` while suspended. The router refuses a suspension store that does not require
    an approver; the app wires `DbSuspensionStore(db, require_approver=True)`, registered in
    `register_all`, migration `0011_conductor_suspension`. The DSCR seed declares
    `human_checkpoint: ELIGIBILITY_DECISION_APPROVAL`, so its runs on Plato now pause.
  - `PlatoClient.resume_case_run`, `case_run_outcome`. `ManifestLoader.get_human_checkpoints`.
  - Not in this: documents upload for DSCR's optional appraisal (the plan's other Phase 3 item);
    a TTL for runs left suspended.
  - Follow-up (+28 / -8 lines, 2 files): the resume route's approver, and an outcome's
    `created_by`, are `acting_user_id()` (the authenticated `x-security-context`/`x-user-id`),
    not the governed `X-Actor-Ref` header, which a client sets freely. The body's `approver` is
    refused in a deployed posture as well as under `identity_required`.

- **Pack lint and the DSCR seed's program structure** (`eacaac6d`; reviewed clean).
  - `lint_pack` checks a pack's programs against its own YAML policies when the manifest names no
    registry pointer, whatever the caller passed (`scripts/pack_lint.py` and the extraction run's
    lint passed none or a draft's one policy, so the program checks were skipped); the caller's
    policies stand over the pack's by id, so an extraction draft is checked too. A pack whose
    policy files do not load falls back to the caller's policies rather than failing the lint;
    the publish check reports the file. `TODO(program-check-needs-policies)` is closed.
  - New warning `rule_repeated_across_programs`: a rule with the same gate, condition and action in
    more than one program's overlays, or in core and an overlay, which belongs once in a core
    policy (one overlay two
    programs share is not a repeat; exception rules count). A lint keyed to the
    programs' published differences was considered and dropped: rules of two programs carry
    different ids and nothing pairs them, so the lint could not tell which rule a difference is
    about.
  - `MatrixAxis.domain_extensions`: an axis declaring `profile_custom_key` has its band edges (every
    band bound, ascending) checked by `find_profile_literal_drift` against that profile list; a
    profile entry that is not a list of numbers, or a key on an axis with no bands, is a finding.
  - The `dscr_core` seed, mirroring jaci: the 15 state PPP buyout rules are once in
    `process.yaml` (`DSCR_PROCESS` 2.0.0, citing both consolidations) instead of in each program
    (the new warning found all 15 on the old seed); Standard is 54 rules, Platinum Select 29. The
    program loan bounds (the $2M DSCR floor, the $200k and $350k/$1.5M CLTV thresholds) and the
    loan-amount band edges of the grid and vacant-refinance caps are linked to profile keys.
    `TODO(ppp-rules-duplicated-per-program)` and `TODO(loan-bound-profile-claim-false)` are closed;
    `DSCR_STANDARD` is 3.1.0 and `DSCR_PLATINUM_SELECT` 1.1.0, having lost those rules, and a
    seed lint test also asserts zero profile drift.
  - The case conductor assesses the raw input, like the assess route, by decision: a fact a rule
    reads must be stated even where the input schema defaults it. `kinds.py` says so and
    `TODO(conductor-drops-validated-defaults)` is closed.

## [2.5.7] - PR #86 (plato -> dev)

Plato 0.1.9.

- **Dependency floors for 10 open Dependabot alerts on `main`:** `pyjwt >=2.15.1` (8 alerts, one
  critical; direct, and transitive via `mcp` and `msal`) and `oauthlib >=4.0.0` (2 alerts;
  transitive via `msrest` -> `requests-oauthlib`), locked at 2.15.1 and 4.0.0.

- **A host checks a declared lifecycle, and binds its grounding per session, through the SDK**
  (+175 / -55 lines, 10 files).
  - `pipelines.chat.host_lifecycle(spec, ..., fabric=, persist_hook=)` returns the declared
    lifecycle and the problems a host cannot run (the builder's own errors, `application_hook`
    persistence with no persist hook, ground sources with no fabric). Plato's chat routes (409)
    and pack check (`invalid_lifecycle`) both call it, so the two sets of rules cannot drift.
  - `runs.GroundingSessions(registry=, idle_seconds=, workspace_root=)`: `bind(declared, turn,
    fabric=, key=)` binds the turn's sources at once (the runners decide on the ground stage from
    them) and returns the turn's workspace, which holds the session's turn
    slot from the runner's entry to its end, so an idle reap never closes a session under a
    running turn. `bind` is async and reaps first, so a session idle past its TTL starts fresh
    rather than being revived by the lookup. Plato's grounding goes through it, with the SDK's
    `DEFAULT_GROUND_IDLE_SECONDS`.
  - An empty registry passed to `GroundingSessions`, `ComposePlan` or `GroundPlan` is the one
    used; `registry or default()` read an empty (falsy) registry as none.
  - Plato is 0.1.9 (0.1.8 shipped with 2.5.6).

- **Token accounting.**
  - The Agents SDK path counts cache-write tokens: `run_kit._usage_to_token_usage` sets
    `TokenUsage.cache_creation_tokens` from `input_tokens_details.cache_write_tokens` and takes
    them off the fresh input, so they are costed at the cache-write rate, not the input rate
    (the chat-completions provider already did).
  - `CostTracker.latest_input_tokens`, the compaction trigger's token source, is the last call's
    whole prompt (fresh, cached and cache-write input). The fresh input alone left out cached
    tokens, most of a context under prompt caching, so the trigger rarely fired.
- **The Knowledge Hub policy/Rego surface is removed.** Knowledge Hub dropped its policy and rego
  APIs, so every path here called endpoints that no longer exist, and the next client-api pin would
  have failed the whole client import. Gone: `KnowledgeHubClient.create_policy` / `read_policy` /
  `read_policies` / `update_policy` / `delete_policy` / `update_bundle` / `evaluate_policy` /
  `get_policy_bundle` and their imports (the `api.rego` group, `PolicyCreate`, `PolicyUpdate`,
  `PolicyEvaluationInput`); the mock client's equivalents and its `policies.json`;
  `jazzx_sdk.tools.knowledge_hub.policy` (`read_policy`, `list_policies`, `evaluate_policy`,
  `get_policy_by_name`); the three MCP policy tools; and the `fabric.opa` placeholder (with its
  `KnowledgeFabric.opa` attribute and platform-catalog row). Canonical policies
  (`fabric.canonical`) are the policy surface; the pack store holds them for Plato. A domain pack
  manifest declaring a `policy_bundle` is refused by `DomainPackFabric.initialize`, before anything
  is registered. `fabric.canonical.store.PolicyStore` stays on Knowledge Hub entities (the entity
  API is unaffected). No sibling repo used the removed surface through japes.
- **A run's first terminal write wins.** `TurnRunStore.finish` (both stores; under the row lock in
  `DbTurnRunStore`) returns a run that has already ended as it is and writes nothing, so a reaped
  run whose worker comes back, or a run cancelled after its own finish, keeps its end. The three
  executors' separate read-then-finish checks are gone (they were two writes, so a reap between
  them was still overwritten), and their result and failure paths are covered too.
  `ChatCoordinator` does not commit a turn whose run already ended (reaped while it ran), under
  either commit ordering: the run's record says it did not complete.
  `ResilientRunner`'s failure and generator-ended paths now finish with a terminal event
  (`{"done": true, "failed": true}` / `{"done": true}`) instead of a bare status update, so every
  terminal path journals its `done`.
- **Closing never starts a run.** A run claimed while `RunWorker.close` or
  `ChatCoordinator.close` runs (the claim in flight when `close` took its list) was started with
  no one settling it; it is handed back to the queue for another worker instead. New
  `TurnRunStore.release(run_id, claim_token)` (both stores): a claimed, unstarted run back to
  QUEUED, fenced on the claim and never an ended run. `drain_claims` takes a `release`.
- **A queued heartbeat is not taken for a dead worker.** A heartbeat waits for a pool connection
  like any session, up to the pool timeout (60 s by default in `common.core.db`), and the reaper's
  TTL was 30 s: a busy pool could get a live run reaped.
  - `Reaper`'s TTL defaults to `DEFAULT_REAP_TTL_SECONDS` (90 s), and it refuses a TTL that does
    not exceed the store's `heartbeat_wait_seconds()` (the heartbeat pool's timeout). Plato's
    `job:run-reaper` therefore reaps after 90 s of silence, not 30 s.
  - `DbTurnRunStore(..., heartbeat_db=)` beats on its own (small) pool, off the shared one.
  - A reaped run's error names the claim that went stale (`reaped_reason`).
- **`RunWorker(..., claim_headroom_seconds=)`** stops claiming that long before
  `max_lifetime_seconds` ends, so a long run is not taken with too little time left before the
  platform stops the replica; clamped so at least `MIN_CLAIM_WINDOW_SECONDS` (60 s) of claiming
  remains when the headroom exceeds a short lifetime.
- **Formal `check_rules` does not flag an ineligible matrix cell** (an always-false rule) as an
  infeasible scope: it is checked for reachability only, as `verify` already fails an item that
  lands in it. Every canonical policy with an NA cell failed `check_rules`.
- **`conductor_problems` reports a `temperature` on a mode that ignores it.** Only the reasoner's
  constructor takes one (`kinds.TEMPERATURE_MODES`); on the governor it was dropped silently, so a
  pack asking for a deterministic 0 still sampled. Pack check and publish now say so.
- **One `policy_assessment` kind and one metrics read.** `kinds.PRE_LOOP_ASSESSMENT` and the
  fact catalog both take `pack.assessment.ASSESSMENT_KIND`, and the catalog's metric facts come
  from `pack.assessment.metric_definitions`, the same read the assessment derives them with.
- **A malformed `policy_assessment` entry is refused at check and publish** (the pack linter's
  `invalid_assessment`, publish-blocking, for every pack whatever its conductor), not at the first
  `assess`: a misspelt key such as `defualt_program:` published and then every assessment raised.
  `pack.assessment.assessment_entry` is the one scan for the entry.
- **Error echoes are bounded and redacted.** Every server route that answered an exception's
  `str(exc)` (46 sites: `server/agent_config`, `eval_api`, `feedback_api`, `policy_extract_api`,
  `vocabulary_review`, and Plato's `database`, `packs` and `runs`) now answers
  `failures.reason(exc, limit=SERVED_REASON_LIMIT)`, as `assess` already did: one line, secrets
  redacted, the message capped at 200 characters, and prefixed with the exception type (so a
  detail reads `ValidationError: ...`). A pydantic error no longer reflects the submitted body in
  full. Plato's formal route and the eval routes' remaining messages go through `reason` too.
- **Feedback retrieval follows the current RAG store.** Plato's feedback router reads the process
  layer's `RAGStore` per request (`rag_for`, from `plato.app._feedback_rag`), and the per-tenant
  `RagFeedbackIndex` is rebuilt when the store changes (its cached collection ids name collections
  in the store they came from; `RagFeedbackIndex.rag`). A Knowledge Hub URL set after boot now
  moves semantic retrieval off the Mock's store. A router given a fixed `rag` behaves as before.
- **A checker defect does not refuse a valid pack.** Plato's pack check reports a pack that fails
  to load as `unloadable` (publish-blocking) as before, but a lint or conductor check that raises
  on a pack that loaded is now `check_incomplete` (`plato.packs.check.CHECK_INCOMPLETE`): reported
  and logged, not blocking. A stage failing on the pack's own data (an unreadable or unparseable
  file, `ValueError` / `OSError` / YAML error) still blocks, as `unloadable`; `conductor_problems`
  reports an evidence-tools file that is not YAML. A non-path `PackSource`'s guardrails stay unread
  (`TODO(packsource-guardrails-dropped)`; no caller passes one).
- **A session closed with no turns is not "complete"**, whatever its protocol requires: its
  Decision is the protocol's incomplete outcome, and its summary says `complete: false` too. And `subset_match` treats an empty mapping below
  the top as a leaf, so a gold case's `{"caps": {}}` requires an empty `caps` rather than scoring
  1.0 against an output with none.
- **Formal formulation names the candidate it refuses** for a condition kind or operator outside
  the JSON comparison subset (`is not formulatable: ...`), as it already did for a missing fact
  binding; that error escaped with a bare message. The formulation still refuses the whole draft
  for a bad candidate, by design.
- **`pack_archive` is deterministic.** Each entry carries a fixed timestamp and mode
  (`ARCHIVE_ENTRY_TIMESTAMP`, `ARCHIVE_ENTRY_MODE`) instead of the file's, so the same directory
  content is the same archive and the same `content_digest`, however recently the files were
  touched (a republish of unchanged content no longer reads as changed).
- **`FeedbackApiSink` and `EvalServiceClient` take a `request_headers_provider`**, as `PlatoClient`
  does: headers added to every request (the client's own win a clash), so a caller forwarding a
  signed-in user's identity no longer subclasses the sink to add them (jaci's ci_spread does).
- **The MCP server checks `Host` and `Origin`, and starts on either `mcp` major.**
  `JazzXMCPServer.run_streamable_http(host, port, allowed_hosts=, allowed_origins=)` turns on the
  transport's DNS-rebinding protection: a loopback bind answers to loopback names only, and any
  other bind needs `allowed_hosts` (`transport_security_for` raises `ValueError` without them; the
  mcp default left an off-loopback bind unchecked). `JazzXRuntime` takes
  `mcp_server_allowed_hosts` / `mcp_server_allowed_origins` (settings `MCP_SERVER_ALLOWED_HOSTS` /
  `MCP_SERVER_ALLOWED_ORIGINS`, JSON lists) and refuses an unchecked bind at start. The start
  itself failed on mcp 1.x with a `TypeError` (host and port are server settings there, and
  arguments of the run only on 2.x); it now sets whichever the installed major reads.
- **Pack assessment is hybrid.** `assess(pack, inputs, reasoning_agent=)` decides a live rule
  (a `natural_language` or `procedure` condition, or an `all_of` / `any_of` nesting one) with the
  `ReasoningAgent` passed, alongside the deterministic rules; without one a live rule is withheld
  and attested INDETERMINATE, as before. `PolicyAssessment.engines` maps each active rule of the assessed policies to a
  `RuleEngine(kind, live)` (`kind` is the condition kind, `UNCONDITIONAL_ENGINE` for a rule
  without one; `live` also covers an applicability gate and nested children, which the
  composites' own class-level `execution` does not), and `reasoned` says whether live rules had
  a model. Plato's `POST {prefix}/packs/{id}/assess` stays model-free by default;
  `?reason=true` builds a `ReasoningAgent` on the configured model (the runtime's
  `AgentExecutionService` when it has one). It assesses model-free first, so an input the
  assessment refuses answers 422 either way, then reasons; any error in the reasoned run (a
  missing provider key included, which is a `ValueError`) answers 502.
  The case run's pre-loop assessment and `PackAssessmentInvoker` stay deterministic: the first
  must agree with the default route, and the second re-checks what that route answers.
  `agents.adjudication.partition_rules` still classifies a composite by its own kind (its
  adjudication path batches only kinds that render into one prompt).
- **Policy extraction proposes a deterministic condition where the text states one.** A fourth
  representation, `conditions` (`pipelines.policy_conditions.ConditionExtractor`, on Plato's
  authoring page as "Thresholds, else natural language", and in the authoring chat's
  `start_extraction`), asks the model, per obligation clause, whether the clause is exactly one
  numeric threshold on one of the pack's fields (`JtbdTemplate.reads`, the bound the `python`
  representation uses). A proposed `expression` is kept only when the field is declared, the
  operator is one of `NUMERIC_OPERATORS`, and the number is printed in the clause
  (`printed_numbers`: thousands commas and decimals, `1.25x` and `80%` included); the value is
  taken as printed, not from the model. Otherwise the rule is `natural_language`, reading only
  declared fields, and the proposal's reasoning says which check refused the expression. A
  clause that obliges nothing calls no model. Every rule still goes through the proposal queue.
- **The rule evaluator and Z3 are checked against each other.** A new test compiles, for every
  rule a DSCR gold case's assessment decides, that rule alone and verifies the same record (with
  the derived metrics) under Z3: the two agree on all 32 the compiler supports (the other 20 are
  compiler gaps, reported as CANNOT_DETERMINE; a Z3 ERROR fails the test). It found one formal
  defect: a pack compiled for an overlay whose selected rules are all core rules (or whose overlay
  rules are all gaps) refused a claim naming that overlay with ERROR (`unknown overlay IDs`), since
  the engine took the known overlays from the compiled rules. `JsonRulePack.overlays` now records
  the overlays a pack was compiled for (identifiers, at most `max_overlays`, as a claim's are), and
  a claim may name any of them. Compiled artifacts carry
  the new field, so a pack compiled now hashes differently from the same pack compiled before;
  stored ones still load.
- **The formal compiler covers the whole DSCR seed.** Before, 51 of Standard's rules and 11 of
  Platinum Select's were gaps; now neither program has one. The engine agreement test now requires
  Z3 to decide every rule a gold case decides (52 of 52; any CANNOT_DETERMINE or ERROR fails it).
  - `in` / `not_in` compile to a set-membership predicate (`JsonPredicate.literals`, each member
    typed as the fact is, at most `max_set_literals`).
  - `any_of`, in a gate or a condition, compiles to alternatives (`JsonRule.when_any` /
    `require_any`, at most `max_alternatives`; a nested `any_of` flattens).
  - A `RatioCondition` compiles to `numerator / denominator op threshold` (`JsonPredicate.per`,
    threshold from the profile, typed as a decimal whatever the facts' types, real division). A
    zero denominator is excluded as a compiled assumption, so feasibility and scope checks cannot
    be satisfied through `x / 0`, and `verify` answers CANNOT_DETERMINE for a case with one (for
    any selected ratio, whether or not its rule applies to the case).
  - `tools.evaluate_ratio` (and so `RatioEvaluator`, `evaluate_ratios` and the stress-test
    `compute_fn` over it) decides pass/fail exactly (`ratio_holds`: decimals, cross-multiplied, a negative
    denominator flipping the comparison) instead of by float division, which put a ratio sitting
    on its threshold (1250.10 / 1000.08 against 1.25) on the wrong side. The reported value and
    margin are still the float ones, and the warning band applies to the exact verdict.
    A margin whose float sign contradicts the exact verdict (an epsilon on the threshold)
    reads as 0.0, and a non-finite input raises `ValueError`.
    `RatioEvaluator` turns that error, and a zero denominator's, into an INDETERMINATE
    (`CALCULATION_UNAVAILABLE`) outcome for the one rule, as `ExpressionEvaluator` does for a
    non-finite value; before, a zero denominator raised out of the whole assessment. The sibling
    `evaluate_value` gives a non-finite value (NaN, infinity, an int past float range) `n/a`, as it
    gives `None`, instead of scoring it (infinity used to pass).
  - `JsonPredicate.literals` must be a list.
  - `max_rules` rises from 128 to 512 (Standard's matrices expand to about 280 rules).
  - A matrix cell whose axis equality contradicts the rule's gate is dropped (it can never apply;
    compared as the fact's type, so `1.0` and `1` are one value), and a condition negating its own
    gate (`DSCR-OVER-2M-NO-RATIO`) compiles as `always_false`, the ineligible-cell shape. With
    both, `check_rules` passes on each seed program instead of reporting those as unreachable or
    infeasible scopes.
  - Formulation's supported subset follows the compiler, so an `in` / `not_in` candidate is now
    formulatable; a ratio candidate is still refused (formulation has no profile).
  - `docs/FORMAL_JSON_RULES.md` lists the subset.
- **Plato's extraction runs are linted against the tenant's draft.** The authoring router hands
  `PolicyExtractionService` a `pack_for` that opens the draft of the pack being extracted into as
  a `Pack` (unpacked into a scratch directory held for the run), so the lint step checks the
  proposed rules against the draft's vocabulary; before, Plato passed no pack and every run
  skipped its lint. `pack_for` may now return an async context manager yielding the pack, held
  open for the whole run. `ExtractionRun.linted` says whether a pack was there to lint against
  (no draft, or one that does not load, is `false`), so an empty `lint_findings` is not read as
  clean; the authoring page and the chat's `extraction_status` show it.
  The lint step treats the pack's own data errors (a half-written file a `Pack` reads lazily)
  as not linted rather than failing the run, whose proposals are already stored.
- **The Postgres advisory locks are tested.** A Postgres-only test holds a key in one transaction
  and checks that `try_advisory_xact_lock` passes over it, `advisory_xact_lock` waits for it, and
  both succeed once the holder ends (it fails with the locks made no-ops).
- **Claude Sonnet 5.5 and GPT-6.1 Sol are priced and carded, and Sonnet 5.5 is the Anthropic
  default.**
  - `claude-sonnet-5.5` (API id `claude-sonnet-5-5`): $2 / $10, cache read $0.20 (the standard
    0.1x), 5-minute cache write $2.50; 1M context, 128K output, adaptive thinking (not always on,
    default effort `high`), knowledge cutoff Jun 2026. Same price as Sonnet 5.
  - `gpt-6.1-sol`: $2 / $10, cached input $0.10 (5% of input, where GPT-6 Sol's is 10%), cache
    write $2.50; above 272k input tokens $4 / $15, cached $0.20, cache write $5; flex at half.
    1.05M context (922k max input), 128K output, reasoning efforts `low` to `max` (no `none` or
    `minimal`), knowledge cutoff 2026-04-30. It is the only GPT-6.1 model: Astra and Luna stay on
    GPT-6.
  - Both rows' `unsupported_request_params` are carried over from their predecessors (Sonnet 5,
    verified against the live API; GPT-6 Sol), not re-verified; provenance says so. Claude Opus
    5.5's row already matched the pricing page. Both providers' `verified` dates move to
    2026-09-30.
  - `PROVIDER_DEFAULT_MODEL["anthropic"]` is `claude-sonnet-5.5`. The vision-routing tests read
    the default instead of repeating its literal.
- **Shipped docstrings, comments and docs trimmed to what a user needs** (+1614 / -8529 lines, 86 files). The
  SDK ships to third parties, so rationale, failure stories, worked examples, design history
  and client or domain names now live here and in the plans, not in the package.
  - Every docstring and comment 2.5.7 added (66 files) is one or two lines; `TODO(slug)`s,
    pragmas and `Author:` lines are kept. `scripts/local/check_comment_only.py` (the AST with
    docstrings removed, against HEAD) shows no code changed; no tool function's docstring
    changed, and no trimmed pydantic docstring is an LLM output schema.
  - README (1077 to 275 lines), `docs/ARCHITECTURE.md` (1755 to 216), `DOMAIN_PACK_QUICKSTART.md`
    (1513 to 503), `CHAT_LIFECYCLE.md` (395 to 134), `DEPLOYMENT_ENV.md` (385 to 191, its generated
    table untouched), `LOCAL_TESTING.md`, `SETTINGS_CONFIGURATION.md`, `FORMAL_JSON_RULES.md`,
    `FORMAL_EVALUATION.md`, `plato/guide.md` (146 to 74), the five `examples/` READMEs and the
    `experts`, `evaluation` and `modes` package READMEs, and the `plato/data` sample and demo pack
    READMEs: terse references, generic examples.
  - The README's install lines install from git (japes is not on PyPI); `DOMAIN_PACK_QUICKSTART`
    describes the data-only pack model; the `experts` README lists the three expert types the
    code has (`policy`, `playbook`, `discovery`).
  - `examples/document_analyzer/ROADMAP.md` and `plato/data/seed_packs/dscr_core/ENCODING_NOTES.md`
    moved out of the repository, their references with them.
  - `examples/basic/main.py` and `examples/document_analyzer/main.py` import `QueueSettings` from
    `jazzx_sdk.queue`; `jazzx_sdk.queue_processor` has not existed since v2.5.0.
- **The application's turn records, behind the chat coordinator** (`runs.turn_store`; +1068 /
  -103 lines, 11 files). `runs.ChatTurnStore` is the protocol: `begin`, `commit`, `fail`,
  `interrupt`, `reconcile`, each mutation taking the run's claim token as `token` and returning an
  optional marker. `ChatCoordinator(turn_store=)`; `commit=` / `reconcile=` remain, as
  `HookTurnStore` (a store whose `begin` writes nothing and whose `fail` / `interrupt` hand the
  hook the turn's `ChatRun` when there is one), and passing both is refused.
  - `begin` runs after the turn factory and before the lifecycle; its `BeginResult` (`question`,
    `history`, `data`, `recorded`, `terminal_required`, `marker`, `rejection`) sets
    `turn.message`, `turn.history` and the new `ChatTurn.begun`. A rejection ends the turn with
    its `ChatError` and writes nothing more; a `begin` that raises or runs past its grace fails
    the turn (`BEGIN_FAILED`, `BEGIN_INDETERMINATE`, `CoordinatedTurn.mutation="begin"`).
  - One terminal mutation per execution by outcome (`commit`, `fail`, `interrupt`), ordered by
    `DurabilityPolicy`, skipped under `terminal_required=False`; a failed lifecycle and an
    aborted execution are recorded (`fail`, `interrupt` with reason `aborted`), not only a
    completed turn. `CoordinatedTurn.mutation` names the write.
  - Every mutation, `begin` included, is bounded by `commit_grace_seconds` and held through a
    cancellation for that long; with no grace, a cancel stops it at once.
  - `DurabilityPolicy` gains `caller_managed` (no store operation; the `ChatRun` on the result).
    `follow_up="retain"` hands a `delivery_before_best_effort_persist` write to a task the
    coordinator holds; the execution returns at the transfer, `close` settles it and
    `SettleReport.follow_ups_settled` / `follow_ups_unsettled` report it.
  - `interrupt_on_abandon=True` records an abandoned turn's interruption, otherwise unwritten.
  - `coordinator.reconcile(run_id, outcome=...)` settles an `indeterminate` write from the
    caller's own probe, so a `commit=`-only coordinator (no reconcile hook) is never stuck.
  - An execution keeps one record of what it wrote (`begin` landed, the terminal mutation
    attempted and its outcome), which every path reads: a cancel during a write never adds a
    second, a landed `commit` stands against a late cancel (the run finishes completed), a
    `begin` that lands inside a cancel is closed with `interrupt`, and a run reaped while its
    turn ran is closed with `interrupt` without its answer. A mutation returning
    `runs.NOT_RECORDED` wrote nothing and records `not_attempted` (`HookTurnStore` returns it
    when there is no `ChatRun` for the hook). A write past its grace is cancelled rather than
    left running. `close` waits for the follow-ups it cancels and marks their runs
    `indeterminate`. `follow_up` outside `delivery_before_best_effort_persist`, and
    `interrupt_on_abandon` without a store, are refused. After every write, cancel or reap the
    execution's record goes on the run with `update` (a `finish` on an ended run changes
    nothing), so an awaited best-effort commit cut short by `close`, a retained follow-up that
    lands inside its cancel grace (which `close` now waits out), and a commit a reap overtook
    all leave the run saying `confirmed` or `indeterminate`, never a stale `deferred`. A `begin`
    returning `NOT_RECORDED` leaves the turn settled, not `indeterminate`, a `begin` or commit
    returning it inside a cancel's grace included. `close` ends by recording, for every
    execution whose writes may still be open, what it knows (a write still in flight reads
    `indeterminate`), so no timeout can leave a run saying `deferred` behind an unsettled write. Once an execution
    attempted any write, the run's commit state is its record's to set, whatever came of the
    write (`not_attempted` for one that wrote nothing, under `retain` as under `await`), and it
    is written again if a write landed meanwhile.
  - `test_session_memory`'s stub of `_respond_agentic` takes the per-turn keywords
    (`grounding=`, `on_skill_result=`); it had failed since the agent began passing `grounding`.
- **A preliminary answer: a fast skill shown first, then joined to the full answer**
  (`jazzx_sdk.pipelines.preliminary`; +551 / -12 lines, 9 files). A profile's `lifecycle.preliminary`
  (`LifecyclePreliminary`: `skill`, optional `marker`, `labels` by marker value, `label`,
  `separator`) compiles into a `PreliminaryPlan` on the turn (`ChatTurn.preliminary`). Both
  reference answer steps hand the agent its `listener` as `on_skill_result`. The lane's first
  reply per turn is read: the marker line (`COVERAGE: full`) is stripped and its value picks the
  label; a value with no label, a reply without the line, or an empty one is not shown. What is
  shown runs through the declared compose steps, and a failed `leak_check` (any action) or a
  block drops it. A streamed turn publishes `{"preliminary": {"text", "coverage", "sources",
  "checks"}}`; either way it is kept (`ChatTurn.preliminary_answer`) and the compose stage joins
  it ahead of the full answer before its steps run, so `cite` rebuilds citations over both halves
  and both routes deliver (and, under caller persistence, record) the same reply. A lane brings a
  compose stage even with no steps declared. `declared_lifecycle(skills=)` refuses a lane whose
  skill is not the agent's; Plato and pack check pass the profile's skills (`invalid_lifecycle`).
  - The join is onto the chat text: `ComposePlan.compose(prefix=)` joins it after the `present`
    steps, and only onto a reply with no structured output or one whose answer a `present` step
    set; a structured reply's answer is otherwise its output's JSON and is left whole, however
    the schema arrived (profile, turn or agent). The lane's own compose run skips `present`
    (`skip=`), whose fallback would replace it. Label keys are case-folded, as the marker value
    is read. A reply is claimed before any await, so two calls in one step show one, and the
    claim is released when that reply is withheld or dropped. A full answer that failed or was
    cut short is delivered alone.
- **A skill's reply is heard as it returns, and a skill can be bounded in time.** (+182 / -17 lines, 4 files)
  - `InteractiveAgent.respond` / `respond_stream(on_skill_result=)`: an async
    `(skill_name, text)` callback, called from the parent's `on_tool_end` for each skill tool
    while the rest of the run goes on (`stream_hooks.SkillResultHooks`, built per turn and
    composed with the agent's own hooks, so concurrent turns on one agent do not share it). A
    callback that raises is logged, never raised into the run. Agentic path only.
  - `Skill.timeout_seconds` / `Skill.timeout_result`: a wall-clock bound on one call to a skill,
    through the Agents SDK tool's own `timeout_seconds` with `timeout_behavior="error_as_result"`,
    so a skill past it hands the parent `timeout_result` (or the SDK's timeout text) as its reply
    and the parent's other tool calls in the batch go on. Applies to sub-agent and `spec_ref`
    skills alike. `max_turns` bounds work, this bounds time.
- **Declared compose** (`jazzx_sdk.pipelines.compose`; +885 / -26 lines, 16 files). A profile's
  `lifecycle.compose.steps` lists steps by `kind` (`LifecycleCompose`, each a
  `LifecycleComposeStep` with `kind`, an optional `name`, and the kind's own keys); the compose
  stage runs them in order over the answered reply, on its surfaces: `answer` and
  `output.<field>` of the structured reply the profile's `output_schema` declares.
  - Built-in kinds (a `ComposeKinds` registry, extended through the `jazzx_sdk.compose_kinds`
    entry point, never overriding a built-in): `present` (the chat text from an output field, else
    a `fallback`), `cite` (the reply cites the grounded files a surface names, in order of first
    mention, instead of every grounded file; opt-in), `humanize` (grounded file names become their
    display labels), `leak_check` (identifiers from `sources` and/or `patterns`; `action` report,
    redact or block).
  - `GroundedSource.files` maps each file a `documents` or `entities` source wrote to its citation,
    which is what `cite` and `humanize` read.
  - Each step's findings are `DeliveryCheck`s (`step`, `kind`, `passed`, `surfaces`, `detail`,
    `count`) on the new `InteractiveResponse.checks`, and on the compose stage's span as
    `check.<step>.passed` / `check.<step>.count`, through the new `ConductorState.annotations` (a
    component's attributes for its own step's span, set when it returns).
  - A blocked, refused, cancelled, failed or incomplete reply is not composed; a blocking step
    ends the chain. The plan refuses an unknown kind, a step its kind refuses, two steps sharing a
    name, and a `cite` after a `humanize` over the same surface; steps reading output fields need
    `declared_lifecycle(output_schema=)`. Plato and pack check pass the profile's
    `output_schema`; a bad compose declaration is `invalid_lifecycle`.
  - A step's `sources` must name sources the lifecycle grounds (`ComposePlan(ground_sources=)`,
    which `declared_lifecycle` passes), so a typo cannot turn a leak check off. A `leak_check`
    pattern matching empty text is refused, a zero-width match is not a hit, and a file name or
    stem shorter than `MIN_IDENTIFIER_CHARS` is not an identifier. The plan checks every step's `surfaces` and `sources`, installed kinds' included, so a malformed one is a
    problem, not a `TypeError`. `_registry.has_methods` is the one shape test the ground and
    compose registries use.
  - Plato's `/chat` reply carries `output` (the structured reply) and `checks`; the stream's
    terminal frame already carried the whole reply.
  - Compose rewrites the final reply: streamed deltas carry the model's text, and under
    `agent_owned` persistence the stored history holds the agent's own answer.
- **Installed kinds load one way, for every registry of declared kinds.** (+153 / -60 lines, 7 files)
  `_registry.register_installed(registry, group, accepts=)` is how the ground, conductor,
  guardrail and evidence-connector registries take entries a package installs through their
  entry-point groups. The group is read once per process (`_registry.installed`, cached); a point
  that fails to load, or that `accepts` refuses (a callable for conductor, guardrail and evidence;
  an instance with the `GroundKind` shape for ground), is logged and left out, and the others
  still register; an installed entry never replaces one already registered. The conductor,
  guardrail and evidence loaders used to register whatever loaded (a failing import broke every
  build of the registry), and all four read the entry points on every call.
- **Requests carry no parameter the model's card refuses.** The Anthropic default
  (`claude-sonnet-5.5`) refuses `temperature` with a 400, and only `anthropic_native` read the
  card: the `LLMManager` Anthropic provider (`run` and `run_stream`) and the agent-tier
  `AnthropicProvider` now pass their request through `strip_unsupported_params`, and the OpenAI
  provider's `run_stream` strips the reasoning-tier params alongside `reasoning_effort`, as `run`
  already did (the adaptive-thinking tests now assert `temperature` is not sent to `claude-opus-4.8`,
  whose card refuses it). `reasoning/agent.py` imports `DEFAULT_AGENT_MODEL` from `llm.config`; the model-literal
  guard also catches `default="..."` and `claude-` / `gemini-` literals.
- **No default names a retired model.** (+31 / -10 lines, 3 files)
  - `RoutingStrategy.TIER_MODELS` routed to five models the table marks deprecated (`gpt-4o-mini`,
    `gpt-4o`, `claude-3-5-haiku`, `claude-sonnet-4`, `o3-mini`). Now: efficient `gpt-6-luna` /
    `claude-haiku-4.5`, capable `gpt-6.1-sol` / `claude-sonnet-5.5`, advanced `claude-opus-5.5` /
    `gpt-6-astra`; its fallback is the capable OpenAI model rather than `gpt-4o`.
  - `BaseMode`'s `model_name` defaults to `PROVIDER_DEFAULT_MODEL["openai"]`, not `gpt-4o`.
  - A test checks every provider default, the agent default, `BaseMode`'s, each routing tier and
    the routing fallback against the table's `deprecated` flag.
  - `claude-opus-4.8` is marked `deprecated` (Anthropic lists it as legacy); Anthropic's order is
    Sonnet 5.5 (default and capable tier), Opus 5.5 (advanced), Haiku 4.5 (efficient, the current
    Haiku).
- **Every default model comes from `PROVIDER_DEFAULT_MODEL`, and reaches its API in the API's
  form.** (+218 / -81 lines, 21 files)
  - Anthropic's API answers a dotted id (`claude-sonnet-5.5`) with a 404, and the default became
    dotted with Sonnet 5.5. `llm.model_identity.anthropic_wire_name` (the rule `anthropic_native`
    already applied) now also shapes the id at the `LLMManager` Anthropic provider's `run` and
    `run_stream` and at the agent-tier `AnthropicProvider`, so all four request sites send
    `claude-sonnet-5-5`.
  - OpenAI's GPT-6 models are sent `max_completion_tokens`: the rule reads the model card (an
    OpenAI reasoning model), so a new family needs its card row, not another name prefix. Every
    GPT-6 model was being sent `max_tokens`.
  - `llm.config.DEFAULT_AGENT_MODEL` (`gpt-6-luna`: the OpenAI default without its `flex_` alias,
    which the Agents SDK client does not parse) is the fallback for `resolve_agent_model_name`
    (whose routed branch also drops the alias now), `OpenAIProvider.build_agent`,
    `ReasoningAgent`, `AdjudicationAgentSpec.model`, `run_segment` and the evolve curator, all of which
    named `gpt-5.2`; the evolve `EvaluatorMode` (an `LLMManager` path) takes the configured default
    as is. `AgentExecutionService.run`'s per-provider fallbacks (`gpt-4o`, `claude-sonnet-4-5`,
    `gemini-2.5-flash`) and each `LLMManager` provider's `get_default_model` (`gpt-5.4-mini`,
    `claude-sonnet-4-5`, `gemini-2.5-flash`) read the table too.
- **Plato's blocking `/chat` runs the chat lifecycle, as `/chat/stream` does.** It called
  `agent.respond` directly, so the two routes of one assistant ran different paths. It now runs
  `run_chat_lifecycle` over `build_chat_components(agent=...)`; a turn that does not complete
  answers 502 with its `ChatError.user_message` (never the exception's text, which used to reach
  the caller as a 500). `ChatTurn.trace_id` carries the host's trace id to the agent from both
  reference answer steps (Plato's streamed turns lost it before); it is passed only when set,
  so an application agent without the keyword keeps working.
- **`concurrency.call_within(seconds, call)`** awaits a call within a budget and raises
  `BudgetExpired` when the budget ran out, whatever the call did with its cancellation; a
  `TimeoutError` of the call's own passes through. The chat stage budgets and the coordinator's
  commit grace both use it.
- **A chat turn can carry time budgets.** `ChatTurn.deadlines` takes a `DeadlinePolicy`
  (`total_seconds`, `stages` by name, `persist_grace_seconds`), on the monotonic clock from the
  lifecycle's start, for blocking and streaming alike. The work stages (everything before
  `persist`) share the total and each gets whichever of its own budget and the rest of the total
  ends first; `persist` is a protected write bounded only by its grace, and `finalize`, after it,
  only by its own `stages` entry, so a recorded answer is not failed on the clock. A stage past
  its budget raises `StageDeadlineExceeded`, which `chat_step_error` turns into a `ChatError`
  (`code="deadline_exceeded"`, `category="deadline"`, the stage, `retryable=True`), whatever
  the stage did with the cancellation (raised it, raised something else, or swallowed it and
  returned). A stage's own `TimeoutError` inside its budget stays an ordinary stage failure, and a
  `best_effort` persist past its grace is recorded in diagnostics like any other failure of it,
  the answer standing. A bounded stage keeps the reference marks the pipeline reads.
- **Declared grounding** (`jazzx_sdk.pipelines.grounding`, results in
  `agents.interactive.grounded`; +1725 / -60 lines, 16 files). A ground source is named, has a `kind`, and produces a
  `GroundedSource` (`context` prompt text, the `directory` it wrote, citation `sources`, `count`,
  `degraded`, `detail`); the turn's `GroundedContext` holds them with the labels that degraded, and
  is what the `ground` stage now emits and `ChatTurn.grounded` holds (a mapping by label, equal to
  a dict of the same items, so existing readers keep working). `GroundPlan(sources)` compiles
  `DeclaredSource`s (unknown kinds and each kind's own `problems` refused when it is built) into
  `ChatTurn.sources`, so `ground_step` runs them concurrently with its degrade, `required` and
  progress semantics. Kinds are a frozen `GroundKinds` registry (built-ins, then the
  `jazzx_sdk.ground_kinds` entry point, which cannot replace a built-in): `documents`
  (`fabric.docs.materialize` of filtered entities into the source's directory, a manifest as
  context), `entities` (one JSON file per entity), `canonical` (`fabric.canonical.find` as JSON
  context) and `rag` (`fabric.rag.search` over the turn's message, turn-scoped). `$scope`
  references resolve at any depth; each fetch checks the `ground:<name>` hop, and a refused one
  degrades. Files go under the turn's workspace (`ground_workspace(root)`, removed with the turn),
  or, for a session-cached source, under `ChatSession.directory(root)` (new; removed when the
  session closes); a session-cached source runs through `ChatSession.resource`, fetched once and
  joined, a degraded result not kept.
  The answering agent receives it: `InteractiveAgent.respond` / `respond_stream(grounding=)` add
  each source's `context` to the prompt beside the knowledge bindings', give a source that wrote
  files list / read / search tools keyed by source name (`build_directory_tools`), and add every
  source's citations to the reply. A skill whose `reads` names a ground source gets that source's
  tools and context in its sub-agent; a source no skill names goes to the agent itself, and one
  agent never reaches another's source. The reference answer steps pass `turn.grounded` when the
  turn gathered declared sources (so an agent without the keyword keeps working otherwise).
  A profile declares them: `lifecycle.ground.sources` (`LifecycleGround`, strict; each source a
  `LifecycleGroundSource` with `kind`, `required`, `cache`, and the kind's own settings as further
  keys, checked by the kind). `declared_lifecycle` compiles them into `DeclaredLifecycle.ground` (a
  `GroundPlan`; a source that does not check raises `ValueError`); `DeclaredLifecycle.bind(turn,
  fabric=, scope=, session=, workspace_root=)` puts them on the turn and returns its workspace, and
  `DeclaredLifecycle.components(agent, **overrides)` builds the lifecycle with the declared gate, a
  ground stage requiring the declared required sources, and `publish_ground_progress` (new on
  `ground_step` / `build_chat_components`: each source's progress as a `{"ground": {"active",
  "source", "failed"}}` stream event). A required source that cannot be gathered is a `ChatError`
  `code="grounding_failed"` (`GROUNDING_FAILED`), `category="resource"`, retryable, with
  `GROUNDING_FAILED_MESSAGE` for the user. Plato runs a profile's declared sources on `/chat` and
  `/chat/stream`: through the runtime's fabric, session-cached per (tenant, assistant, session) in
  the replica and dropped after `runs.session.DEFAULT_GROUND_IDLE_SECONDS` idle, files under `PLATO_GROUND_DIR`
  (the system temporary directory by default). A profile declaring sources on a wiring with no
  fabric, or a lifecycle that does not build, answers 409; pack check reports both, and
  `application_hook`, as the publish-blocking `invalid_lifecycle`.
  An agent run through a declared lifecycle grounds its `knowledge:` bindings the same way:
  `declared_lifecycle(spec, knowledge=)` compiles each binding into a ground source
  (`sources_from_knowledge`: a canonical binding is the `canonical` kind, a docs binding the new
  `docs` kind, a `fabric.docs` listing as `[doc]` lines with citations), named by
  `knowledge_source_name` (the binding's `name`, else `knowledge_<index>`), so they get progress,
  degrade and `required` too. `InteractiveAgent` skips a binding whose source the turn already
  gathered, so nothing is injected twice; called directly, it grounds its bindings as before. A
  binding and a declared source sharing a name is a `ValueError` (and `invalid_lifecycle` in pack
  check). Plato passes the profile's bindings. A session-cached source is kept per resolved
  setting (its `$` references filled in), so a session whose next turn names another loan is
  grounded in that loan.
  - An agent without skills (one call on its configured provider, no tools) gets the files its
    sources wrote in its prompt, up to `grounded.INLINE_FILES_MAX_CHARS` across the turn, with a
    count of the files left out (`GroundedContext.file_text`), rather than only their list.
    Dot-prefixed files (the materialize manifest) are skipped, as the directory tools hide them,
    and a file that is not UTF-8 text is counted as left out.
  - A source that only a skill routed out of this turn reads goes to the agent, context and tools.
  - Admission to a source (`ground:<name>`) is checked on every turn in its own invocation
    context, a session-cached or joined result included. A compiled knowledge binding is admitted
    by its own `canonical:` / `docs:` selector instead, as without a lifecycle
    (`DeclaredSource.hops`, `knowledge.knowledge_hop`, shared with `resolve_knowledge`).
  - `entities` gives two entities that map to the same file name their own files (`_2`, `_3`,
    in id order).
  - An installed ground kind that fails to load, or is not an instance carrying `cache`,
    `writes_files`, `problems()` and `fetch()`, is logged and left unregistered, so a profile
    naming it is refused as an unknown kind.
- **An assistant profile declares how the chat lifecycle runs it.** `InteractiveAgentSpec.lifecycle`
  (`ChatLifecycleSpec`, strict: a misspelt key fails when the profile loads) holds the turn
  policies (`persistence`, `persist_failure`, `cancel_after_answer`, `deadlines` as
  `LifecycleDeadlines`) and a gate kind, `scope` (`LifecycleGate`: `in_scope`, `out_of_scope`,
  `decline`). `pipelines.chat.declared_lifecycle(spec, llm=)` turns it into `DeclaredLifecycle`:
  the `ChatTurn` keyword arguments and a `classify` / `decline` for `build_chat_components`; the
  gate refuses, before grounding or answering, a message matching `out_of_scope` (a keyword check,
  first and deterministic) and, given `llm` and `in_scope` topics, one the stock scope guardrail's
  LLM check finds outside them. The keyword-first order is `build_scope_guardrail`'s own: with `llm=` it now
  refuses a listed `out_of_scope` topic before asking the model, which also changes a manifest
  that sets `out_of_scope_check_model` beside out-of-scope classes (`spec_binding.bind_spec`),
  whose listed topics the LLM check used to overrule.
  A gate neither check can run (only `in_scope` with no `llm`, or no topics) raises `ValueError`.
  Plato's `/chat` and `/chat/stream` run each assistant's declared lifecycle, the gate checked
  with the runtime's LLM; a turn that is not `agent_owned` binds no persist, and a profile
  declaring `application_hook` or a gate that cannot run answers 409 on both routes, before a
  turn starts. Not declarative yet: ground (workspace grounding from
  declared sources does not exist) and compose kinds (output-guardrail kinds for identifier
  humanizing and leak checks).
- **Typed turn events and a bounded outlet** (`jazzx_sdk.runs.outlet`), after jazzx-assistant's
  256-frame send queue. A `TurnEvent` is a journal event with its turn, key, session, the
  journal's per-turn `seq`, a `kind` and a `Delivery` class; `classify_event` (replaceable) makes
  the terminal event, an error and a text delta `required` and anything else `ephemeral`
  progress. `BoundedOutlet(capacity=, overflow=)`: full, it drops a new ephemeral event, a
  required one evicts the oldest ephemeral, and with only required events queued it detaches the
  reader (`OutletDetached`, `overflow="detach"`) or waits for room (`"block"`); `fence(turn_id)`
  drops a superseded turn's non-required events while its required ones, the terminal among them,
  still pass; `close(flush_timeout)` waits for the reader and detaches one too slow.
  `ChatTurnHandle.pump(outlet)` feeds a run's journal into an outlet to its terminal event; an
  outlet that detaches ends the pump and the run is left as its `DisconnectPolicy` says. Queued
  is not durable: the journal is the record a detached reader resumes from.
- **Process-local chat sessions and shared resources** (`jazzx_sdk.runs.session`), modelled on
  jazzx-assistant's `ws/` session, registry and grounding cache.
  - `SingleFlight(work, cacheable=)`: `get` starts the work or joins it; a joiner first receives
    the progress so far, then the live events, through its own callback. A cancelled joiner stops
    waiting and the work goes on (it is awaited shielded). A failure reaches every waiter and is
    never cached; a result `cacheable` rejects (a degraded one) is returned and not kept. `stop`
    cancels work in flight, and its waiters get `ResourceStopped`.
  - `ChatSession`: `turn()` holds one of the session's turn slots (`SessionTurnsAtCapacity`,
    `SessionClosed`) and touches its monotonic idle clock; `resource(name, work)` is a session's
    `SingleFlight`; `spawn_followup` holds work that outlives a turn (logged on failure, waited
    for on close); `close(timeout)` stops resources, waits, cancels what is left and reports it
    (`SettleOutcome`).
  - `SessionRegistry(max_sessions=, max_turns_per_session=)`: `open` refuses while draining,
    then at capacity; `reap_stale(older_than_seconds)` closes idle sessions with no pending work,
    in the shape `agents.interactive.session.SessionReaper` already sweeps; `drain(timeout)`
    closes every session within one budget and reports what it cancelled.
  - `ChatTurnSpec.context`: per-turn context providers (`ContextProvider`, e.g. `session.turn`,
    trusted identity, a trace), entered inside the coordinator's turn task before the lifecycle
    and exited once, after the commit has settled.
- **Duplicate turns and namespaced keys on the runs layer.** `TurnRun.turn_id` (a client message
  id) is unique on its key: `create_run` / `ChatCoordinator.submit(turn_id=, duplicate=,
  duplicate_ttl_seconds=)` answer a second submit of it with the first run, live or finished
  within the retention (`replay`, the default: a retried request follows the original), or refuse
  it with `DuplicateTurn` (`reject`). The check runs in `TurnRunStore.admit` under the key's lock,
  over the key's newest `RECENT_RUNS_CHECKED` runs, so concurrent submits of one id admit one run.
  On sqlite, which has no advisory lock and does not serialize a read-then-write across
  connections, `DbTurnRunStore.admit` now serializes one process's admissions, which also closes
  the same gap for `reject` there (`TODO(sqlite-read-then-write-unserialized)` marks the claim
  paths as untested on sqlite). `coordination_key(*parts)` names a key in a namespace as a JSON
  array, byte-identical to the keys Plato built by hand, which now use it.
- **A chat turn's persistence is one of the four the requirements name.** `PersistencePolicy`
  is `agent_owned` (the default: the agent's store, and the reference `persist` for the side
  branches), `application_hook` (the lifecycle records through the application's own `persist`,
  which must be bound), `external` (the caller writes, outside japes or in its own `persist`)
  and `none` (ephemeral: any bound `persist` is refused). The last three run the agent with
  `persist=False` and refuse the reference `persist`, all before any stage
  (`check_persistence`). `agent` and `caller` are still accepted, read as `agent_owned` and
  `external`; an unknown value is refused when the `ChatTurn` is built.
  `docs/CHAT_LIFECYCLE.md` describes the four.
- **A coordinator's commit can be indeterminate, and is reconciled before a supersede.**
  `ChatCoordinator(commit_grace_seconds=, reconcile=)`. A commit hook past its grace is
  `CommitState` `indeterminate` (never taken for `confirmed`; a `TimeoutError` the hook raises
  itself is an ordinary `failed` commit, with or without a grace; any failure once the grace
  has run out is indeterminate, whether the hook raised something else or swallowed the
  cancellation and returned): under `commit_before_delivery`
  the turn fails as `commit_indeterminate` with no value; under
  `delivery_before_best_effort_persist` the delivered turn stands. `TurnRun.commit_state` records
  every coordinated turn's commit. `ChatCoordinator.reconcile(run_id)` asks the application's
  hook what became of an indeterminate one (`ReconcileOutcome`: `confirmed`, `failed`,
  `indeterminate`, `superseded`, the last recorded as `failed`) and records it. A `supersede` on
  a key one of whose last `RECENT_RUNS_CHECKED` runs is still indeterminate is refused with
  `CommitUnresolved` (a `TurnRejected`), as jazzx-assistant refuses a barge-in whose interrupted
  write failed.
- **The runs layer's coordination types are exported and pinned.** `jazzx_sdk.runs` exports
  `DurabilityPolicy`, `DisconnectPolicy`, `CommitState`, `CommitHook` and `TurnFactory` beside
  `ChatCoordinator`, and `tests/test_runs_public_api.py` pins the exported names and every
  stored value (the policies, `CommitState`, `TurnRunStatus`), as the lifecycle's own test does.
- **`InputFilter` tells the agent what it took away.** Over budget, it first replaces the oldest
  `function_call_output` bodies with a stub naming the call (matched by `call_id`) and the size it
  returned, keeping every item, so each call keeps its output. Inside a `compression_scope` the
  full text goes into the scope's `ReferenceStore` and the stub names its `read_reference` id;
  outside one it says to call the tool again. `ReferenceStore.put` ids are now derived from the
  text (`reference_id`, a sha256 prefix) rather than random: the SDK runs the filter on the
  unfiltered history before every model call, so a random id stored a fresh copy of each elided
  output per call and changed the stub's bytes, missing the provider's prompt cache from there on.
  Storing the same text again returns the same id. The newest `keep_newest_outputs` (default
  `DEFAULT_KEEP_NEWEST_OUTPUTS`, 6) are never elided, a stub is never re-elided, and the caller's
  items are copied, not mutated. Whole reasoning groups are dropped only when that is not enough.
  An agent that finds a result silently gone re-reads it (macer measured 43% of document reads as
  repeats). `ReasoningGroupEvictStrategy` (the conversation store's compaction) is unchanged: what
  it drops is dropped from the stored session for good, where a stub would outlive its reference.
- **Background tasks are held until they end:** the drain `run_router`'s `on_start` starts,
  Plato's case-run drain, and `ChatCoordinator.start`'s drain (held by the coordinator, not only
  by the handle a caller may drop). The event loop keeps only a weak reference to a task.

## [2.5.6] - unreleased

Plato is 0.1.8 (from 0.1.7, which shipped to `main` with 2.5.5): case runs, formal checks,
the pack check and assess routes, recorded sessions, durable chat streaming, `job:run-reaper`
and the pilot fixes are Plato-visible, and `/health` reports this version to identify the image.

- **Pack assessment refuses an input that omits a field a rule in force reads, unless the pack
  says otherwise.** `policy_assessment.missing_inputs: refuse` (the default) or `skip`: under `skip`
  an omitted or non-nullable null fact's rules are attested as not evaluated and the rest of the
  assessment runs. No `default` mode: most schema defaults are pass-valued, so filling an omission
  would pass the rule it should trip. `assess` raises
  `ValueError` (a 422 from Plato's `POST /packs/{id}/assess`) naming every fact the pack's
  catalog declares, a rule of the selected policies reads, and the input leaves out; metric-derived
  facts are exempt. A null is refused too where the fact is not nullable: `FactBinding.nullable`
  (default True, so a bindings file keeps today's reading) is set by `schema_facts` exactly as
  `schema_model` reads the property, admitting null or optional with no default; the formal compile
  leaves it out of `JsonFact`. A nullable fact given as null (`interest_rate` off Illinois) is
  still assessed, and its rules are attested as not evaluated. An omitted field read as missing evidence, which skips its rule, so a record that
  left out a fail-closed term passed: a Platinum loan without `channel` cleared at the Wholesale
  DSCR minimum, an omitted `borrower_entity_type` switched off four state buy-out rules. The case
  conductor's pre-loop and `PackAssessmentInvoker` go through `assess`, so a partial record fails
  there too, loudly. `tests/data/dscr_gold_cases` state the whole `LoanApplication` (52 fields;
  outcomes unchanged), and the formal tests assess a whole record. The Platinum and Standard policy
  headers no longer carry `TODO(absent-channel-escapes-correspondent)`. `docs/ARCHITECTURE.md`
  states the rule.
- **The `dscr_core` seed's Standard program is re-based on its 8.17.2026 consolidated
  guidelines**, mirroring jaci: `DSCR_STANDARD` 3.0.0 cites STD-x on every rule, SD is the only
  ineligible state, Alaska buys out, Mississippi allows buy-out or the 5-year step, a warrantable
  condo above 80% LTV must be outside Florida, and 35 new rules cover the borrower, credit,
  property and transaction overlays the 6.15 encoding lacked (69 rules). Platinum Select gains
  tradelines, the 10/40 exclusion and listed-for-sale impounds (44 rules), and both programs read
  one credit-event vocabulary (`bankruptcy_or_foreclosure` and `short_sale_dil_or_modification`,
  each with its months), which replaces `previous_credit_event` / `months_since_credit_event`.
  The `double_cap` gold case in `tests/data/dscr_gold_cases` is a Florida non-warrantable condo and
  now binds on `DSCR-FL-CONDO-CLTV` at 75%.
- **Platinum's credit-event rule is gated on `previous_credit_event`** (default False), with
  `months_since_credit_event` defaulting to 0, so a flagged event with unstated months is denied
  where the caller posts the whole model. Known limit, `TODO(absent-channel-escapes-correspondent)`
  in `platinum_select.yaml`: `assess` reads an omitted field as missing and skips its rule, so
  every `LoanApplication` default a Platinum rule needs in order to deny or to apply (an unstated
  `channel` held to Correspondent, `borrower_entity_type: individual` opening four PPP gates, and
  more) holds only for a caller that posts
  the whole `LoanApplication` (jaci's `assess_on_plato` does). Applying the input schema's defaults
  in `FactCatalog.read_item` was tried and dropped: most of the seed's defaults are pass-valued
  model conveniences (HOA litigation, refinance listing, rural, vacant), so a record omitting them
  would attest PASS on evidence nobody supplied.
- **The `dscr_core` seed gains Acra's Platinum Select program**, mirroring jaci:
  `policies/platinum_select.yaml` (`DSCR_PLATINUM_SELECT`, `overlay_id: platinum_select`, 41 rules
  from the Platinum Select consolidated guidelines), its `plat_*` profile keys, `programs:
  platinum_select`, and the loan fields it reads. `LoanApplication.program_id` defaults to None, so
  the manifest's `default_program` is the one default. Tests that used `policies[0]` as a template
  now take `DSCR_PROCESS` by id: the policy directory loads alphabetically, so `policies[0]` became
  an overlay. `test_each_seed_program_is_assessed_by_its_own_rules_only` pins program selection on
  the seed. A `json.z3` claim that names no overlays, on a pack whose rules include overlays, is
  now refused (`ERROR`, "name the ones to check"): it checked the core rules alone and reported
  nothing of the overlays, which on the seed meant verifying the 8 process gates and none of the
  program's rules. `docs/FORMAL_JSON_RULES.md` says so.
- **The `dscr_core` seed is split by Acra program**, mirroring jaci's pack: `eligibility.yaml`
  (`DSCR_ELIGIBILITY`) became `process.yaml` (`DSCR_PROCESS`, scope institution, the 8 process-flow
  gates) and `standard.yaml` (`DSCR_STANDARD`, scope product, `overlay_id: standard`, the other 34
  rules, each unchanged). The manifest declares `programs: {standard: [DSCR_STANDARD]}` and
  `default_program: standard`, and `LoanApplication` gains `program_id`. A formal compile of the
  seed's DSCR rules now selects `overlays=["standard"]` in the compile and the claim alike (tests,
  `docs/FORMAL_JSON_RULES.md`, `examples/formal/canonical_dscr.py`); unsat-core ids read
  `DSCR_STANDARD:<rule>`. The scope-ladder test keeps its undeclared-scope-is-core guard on a copy
  of the seed with the scopes stripped.
- **Policy assessment is program-aware.** For a pack declaring `programs:`, `policy_assessment`
  checks the core policies plus the overlays of the one program the input names
  (`program_field`, default `program_id`, else the spec's `default_program`), and reports it as
  `PolicyAssessment.program`. An input naming no program with no default, or an unknown program,
  is refused. It used to evaluate every policy in the pack as core, so sibling programs such as
  Acra's Standard and Platinum Select would all have applied to every loan.
  A non-string program is refused like an unknown one. `lint_pack` reports
  `unknown_default_program`, and warns `program_overlay_id_mismatch` when a program's policy
  carries a different `overlay_id`: formal compilation selects overlays by `overlay_id`, so the two
  would compile and assess different rules.

- **Plato streams assistant turns durably (domain-pack runtime plan, Phase 0.1-0.2).** Both
  shipped wirings now build a run store, runner and dispatcher (`plato.wiring.durable_runs`), so
  `POST /assistants/{aid}/chat/stream`, `GET .../runs/{id}/stream?from_seq=` and
  `POST .../runs/{id}/stop` are mounted; before, neither wiring set them and the routes did not
  exist.
  - **A run is queued under a tenant-scoped key** (`plato.api.assistants.run_queue_key`: tenant,
    assistant, conversation). The run store is one partition and FIFO-claims by that key, and with
    the bare client `conversation_id` a drain could claim another tenant's queued run for the same
    id and execute it with the wrong tenant's agent. Latent until now because the routes were not
    mounted. The stream's first frame still reports the client's `conversation_id`.
  - **`job:run-reaper`** (new role): fails running runs whose worker stopped heartbeating (the
    SDK `Reaper`'s TTL) and purges finished runs and their journal after
    `DEFAULT_RUN_RETENTION_SECONDS` (a week). Exits 3 when the wiring has no run store.
  - **`PLATO_PROFILE=packs`** in `scripts/plato-local.sh` (Phase 0.3): `plato.wiring.default` at
    `JAPES_ENVIRONMENT=local`, sqlite at `.plato-packs.db`. That combination already publishes to
    local blob storage, activates, serves chat against the Mock Knowledge Hub and defaults the
    tenant, so the plan's "give `local.py` an activator" was not needed; the gap was only that no
    profile started it. dev-daily still refuses a publish to local blob storage.
  - **Assistants get the fabric** (Phase 0.4): the shipped wiring's `agent_extra` gains
    `fabric=CurrentFabric()`, which resolves the `ClientLayer`'s fabric on each use, so a profile
    with knowledge bindings grounds instead of raising "no fabric was provided", and an assistant
    bound before a `/v1/config` write sees the rebuilt layer's fabric. (`llm_manager` is still the
    boot-time layer's LLM; whether that goes stale after a key is set over HTTP is not yet checked.)
  - **`GET {prefix}/packs/{id}/{version}/archive`** (Phase 0.5): the published archive, verified
    against `content_digest` and sent with it as the `ETag`; 404 for no such version, 403 where
    pack contents are withheld. New `PackVersionStore.archive()` (abstract; `DbPackVersionStore`
    implements it), which shares the fetch-and-verify step with `materialize`.
  - **`POST {prefix}/packs/check`** (Phase 0.6): `plato.packs.check.check_pack_archive` checks an
    archive of either shape without publishing. Assistant packs get `check_assistant_pack`; domain
    packs are loaded as `Pack` and linted (`lint_pack`, YAML policies only), and manifest pointers
    to Python are reported without being resolved: `policies.registry` and `conductor.pipeline` as
    errors, unread `modes.*.class` / `experts.*.class` as warnings. **Publish runs the same check**
    and refuses on `PUBLISH_BLOCKING` (unloadable, unaddressable, `python_pointer`,
    `missing_skill`, `does_not_bind`, `guardrail_not_registered`) with 422 and the report; other
    findings (lint quality such as `unverifiable_rules`) come back with the publish. Behavior change:
    a pack with a pointer or an unregistered guardrail used to publish and then fail when served.
    `store_db._unpack` is now public as `unpack_archive`.
  - **An unregistered guardrail is an error** (Phase 0.8), not the "dropped silently" warning the
    check reported: the agent binds and then raises on every turn. Found live: Plato's bundled
    demo pack (the default `PLATO_PACK_DIR`) named `clinical_governor_in/out`, which only jaci
    registered, so every chat turn against it raised before the model was called.
  - **Guardrails as pack data** (Phase 1 item 5.2.1, pulled forward to fix the demo pack): new
    `jazzx_sdk.agents.interactive.guardrail_kinds` (`load_pack_guardrails`, `policy_keywords`,
    `GuardrailKinds` extended by the `jazzx_sdk.guardrail_kinds` entry point, `combined_catalog`).
    `ProfileRegistry.register(spec, guardrails=)` / `guardrails_for`; `build_from_manifest` merges
    the profile's pack catalog with the host's, fresh per build. `plato.packs.loader.pack_guardrails`
    reads a pack's `guardrails.yaml` at all three profile-registration sites. The demo pack gains
    `guardrails.yaml` and `policies/core.yaml` (the clinical-intake CI_ESC / CI_SCOPE policies), so
    its governors block with the rule id (`Refusal.reason_code`, message `"[<rule_id>] ..."`).
  - **`jazzx_sdk.clients.plato_client.PlatoClient`** (Phase 0.7): async httpx client for one
    tenant: packs (list, check, publish, activate, archive), assistant sessions and chat, and
    durable streams (`stream_chat`, `resume_run(from_seq=)`, `stop_run`) as parsed SSE frames.
    Sends a fresh `X-Trace-Id` per call and `Idempotency-Key` per mutating call unless given;
    raises `PlatoError(status_code, detail)` on a non-2xx. Case runs and session close/outcome
    arrive with their routes (Phases 1-2).
  - **A guardrail block names its rule** (Phase 1, 5.4): `InteractiveResponse.block_refusal` carries
    the blocking guardrail's `Refusal`, and Plato's `ChatReply.block_rule_id` is its
    `reason_code`. Taken from the guardrail run itself (`InteractiveAgent._guardrail_block`) rather
    than `last_guardrail_refusal`, which is agent state a concurrent turn on the same bound agent
    can overwrite between one turn's block and its read; `_run_guardrails` still sets it.
  - Review fixes for the above: a `guardrails.yaml` policy file must be a file inside the pack
    (`relative_name` plus containment; before, `policies: [/etc/x.yaml]` read the host's file and
    a parse error echoed its keys into the check's finding); `parameters.keywords` must be a list
    of non-empty strings (a bare string iterated to characters and `""` matched every text);
    `agent_with_persona` carries the profile's pack guardrails, and `build_from_manifest` now calls
    `profiles.guardrails_for` without a silent default; re-registering a profile without
    guardrails drops the old ones; `PlatoClient` takes `request_headers_provider` through the
    shared `install_request_headers_hook` like its siblings; the archive route maps a store
    `ValueError` (digest mismatch, no blob store) to 409 with its reason instead of a bare 500.
  - The check also refuses a guardrail listed on a phase it is not registered for
    (`guardrail_phase_mismatch`, blocking), which binds and then raises on every turn of that
    phase; a malformed `guardrails.yaml` (not YAML, not a mapping, an entry that is not a mapping)
    raises `ValueError` naming it.
  - **Recorded sessions** (Phase 1, 5.2.2-5.2.3 and 5.4): new `InteractiveAgentSpec.record`
    (`SessionRecordSpec`: ontology/pack ids, evidence type, the scope key naming the subject, the
    Trace's workflow, a `protocol` file beside `profile.yaml` that `from_dir` loads into
    `sections`, and the terminal decision literals; strict, so a misspelt key fails at load). New
    `jazzx_sdk.agents.interactive.recorder`: `SessionRecorder` (`record_turn`, idempotent `close`,
    `outcome`, `record`) rebuilds a session from its evidence rather than holding state, and
    `RecordingAgent` wraps an agent's `respond` / `respond_stream`. `AssistantRuntime.fabric`.
    Plato records both chat routes for a profile that opts in, keyed by `run_queue_key(tenant,
    assistant, session)` with source system `plato/<tenant>/<assistant>`, and serves
    `POST .../sessions/{sid}/close`, `POST .../sessions/{sid}/outcome` (409 before close) and
    `GET .../sessions/{sid}/record` (409 for an assistant that does not record). The demo pack
    opts in with the clinical-intake protocol; its acceptance test runs the red-flag persona over
    HTTP (block with `CI-ESC-*`, ESCALATED on close, one Trace, one Decision, one Outcome).
    Rev 2's "recorder as a persist stage" was wrong for Plato, whose assistant route calls
    `agent.respond` directly; the recorder is callable from either.
  - Review fixes: the Trace is keyed by source and session (`case_id`), as evidence already was,
    so two sources sharing a session key close separately; a second close reports the turns its
    Trace was built from, not ones recorded after; a close whose Decision write failed writes it
    on the next close instead of answering `decision: None` forever; a session of exactly
    `MAX_RECORDED_TURNS` is not reported truncated; a failed recording is logged rather than
    failing an answered turn (which a client would retry, duplicating it). Two closes racing can
    still each write a Trace (`TODO(concurrent-close-writes-twice)`: needs an idempotent canonical
    write). `ProfileRegistry.validate` checks a profile against its pack guardrails first.
  - Only a rule-backed block escalates: the recorder and `ChatReply.block_rule_id` read the rule
    from `Refusal.domain_extensions["rule_id"]` (`recorder.blocking_rule_id`), which
    `policy_keywords` sets, not `reason_code`, which the manifest scope guardrail fills with a
    reason. `PlatoClient` gains `close_session`, `session_outcome` and `session_record`.
  - **Deterministic pack assessment** (Phase 2, 4.2.1 and 4.5-4.6): new
    `jazzx_sdk.fabric.canonical.caps` (`compose_caps`, `CapComposition`: the minimum cell across
    every applicable matrix rule on one field, the binding rule named, an `NA` cell ineligible, an
    unresolvable cell unknown; generalized from jaci's DSCR `compose_caps`) and
    `jazzx_sdk.pack.assessment` (`assess`, `PolicyAssessment`, `AssessmentSpec` read from the
    manifest's `conductor.pre_loop` `policy_assessment` entry: `metrics:` as `MetricDefinition`s
    over the input's fields, `compose_caps:`, `profile:`; attestations per rule). The DSCR seed pack
    gains `metrics.yaml` (`cltv_pct`) and that entry, and matches all five of jaci's DSCR gold cases
    (copied to `tests/data/dscr_gold_cases`). Plato: `POST {prefix}/packs/{id}/assess` (against
    `?version=`, the tenant's pin, or the newest; 409 for an assistant pack, 422 for a pack without
    an assessment); activating a domain pack pins its version instead of answering "loaded no
    assistants" (`plato.wiring.default.pinned_version`).
  - Review fixes: caps compose over the rules in force (`active_rules`, less the rules
    `check_compliance` reports superseded), and a blocking gate leaves its cap unresolved as it
    withholds the rule; one NA predicate, `condition_evaluator.is_na_cell`, for the matrix evaluator
    and cap composition, so an authored `false` cell is ineligible in both (it was a 0.0 cap in
    composition); a refused metric removes its field from the record instead of letting a posted
    value of that name stand in; a rule the record lacks inputs for is attested INDETERMINATE
    (`allowed` still excuses it, as the policy check does); `assess(python_executor=)`, and Plato's
    assess route passes the wiring's executor, so a python rule runs on a workstation; the route
    refuses a stored pack that names Python (`policies.registry`, `conductor.pipeline`) with 422
    rather than import it; the local wiring gets an offline Mock-backed fabric
    (`PLATO_LOCAL_KH_DATA`, default `.plato-local-kh`), so recorded sessions work there too.
  - A pack cannot declare a guardrail named `platform_safety_floor` or `manifest_scope`: the
    binding adds those only where the name is absent, so a pack's would have replaced the platform
    check (`load_pack_guardrails` refuses, and the publish check reports it). An assessment's
    INDETERMINATE attestations cover only rules whose gate applies to the record.
    A rule whose gate cannot be evaluated for want of inputs is reported INDETERMINATE naming them.
    Caps compose only ceilings (`CEILINGS`: `<=`, `<`; a `>=` matrix rule is a floor), and a `<`
    cap is passed only strictly below it. New `jazzx_sdk.pack.domain.load_materialized_pack`, the
    one "load the pack at a materialized root" step, used by `published_domain_packs`, Plato's
    assess route, domain-pack activation and the publish check.
  - **Conductor kinds** (Phase 2, 4.2.2-4.2.7 and 4.3): a pack runs a case by naming a kind in
    `conductor.kind` and configuring it; it never names Python. New `jazzx_sdk.pipelines.kinds`
    (`run_case`, `conductor_kinds()` with further kinds from the `jazzx_sdk.conductor_kinds`
    entry point, `conductor_problems`, `CaseResult`, `sdk_mode_factory`) and its first kind,
    `investigation_loop`: the five modes over `pipelines.investigation_loop`, configured by
    `InvestigationLoopConfig` (strict: `input_schema`, `subject_field`, `pre_loop`
    (`policy_assessment` only), per-mode `model`/`temperature`, `hypothesis_schema`,
    `decision_schema`, `evidence_tools`, `max_iterations`, `on_reasoner_failure`, `narrator_gate`,
    `deterministic_verdict`). The pre-loop assessment is attested evidence and
    `ctx.metadata["policy_assessment"]`; with `deterministic_verdict: authoritative` a failed
    assessment overrides a governor approval as the governor returns, so the narrator gate sees the
    verdict that stands, and its violated rules join the governor's. Gates are structured
    (`narrator_gate: {governor_approved, decision_field, decision_in}`), not expressions: the
    expression grammar is numeric, with no strings or dotted access. Given the fabric's canonical
    store, a run persists a Trace with a step per mode call and a Decision; a decision schema with
    no `confidence` persists `UNSTATED_CONFIDENCE` (0.0) and requires human review.
  - `jazzx_sdk.pack.schemas` (`schema_model`, `load_schema_model`): pydantic models from a pack's
    JSON Schema, refusing any keyword outside `SUPPORTED_KEYWORDS` rather than validating less than
    written. `jazzx_sdk.pack.evidence_tools` (`EvidenceTools`, `EvidenceSource`): evidence types
    answered from the run input, a fixture keyed by subject id (with `default`), or a connector from
    the `jazzx_sdk.evidence_connectors` entry point; an unanswerable request is `UNAVAILABLE`
    evidence, not a stopped loop. `ConductorEngine(stop_requested=)` and
    `run_investigation(stop_requested=)`: asked before each step, a stop halts the run with status
    `interrupted` (new metric `investigation.interrupted`).
  - The DSCR seed pack declares an `investigation_loop` conductor: schemas generated from jaci's
    DSCR models, `mode_tuning/` from jaci's DSCR prompts, `evidence_tools.yaml` with credit report
    and appraisal fixtures (jaci's mock values), those two added to `evidence_types.yaml`, the
    narrator gated on an approved `ineligible` decision, the assessment authoritative. Plato's
    publish check refuses a conductor that could not run (`conductor_unrunnable`: a kind not
    installed, a schema that does not load, a subject or gate field the schema lacks, a fallback
    decision the schema rejects, an unknown mode, an evidence source that cannot answer).
  - **Case runs** (Phase 2, 4.4-4.5): `jazzx_sdk.runs.case.CaseRunner` (`submit`, `drain`,
    `execute`) runs a conductor over one case on the chat turns' store, claim, heartbeat, reaper,
    stop flag and journal: a step event per start and end, then `{"done": true, "status",
    "output"}`, or `{"done": true, "status": "failed", "error"}` for a run that raised. `TurnRun`
    gains `kind` (`TurnRunKind`: `turn`, `case`) and `output`; `TurnRunStore.runs_for(key,
    limit=)` (both stores); `ResilientRunner.create_run(kind=)`; `runner.restored_caller`, the
    identity-and-InvocationContext restore both runners share. No migration: `kind` and `output`
    ride the run's JSON `data` column, and a case's runs are found by their queue key, so the
    planned `0011` was not needed; `SUSPENDED` waits for human checkpoints (Phase 3).
  - Plato (`plato.api.runs`, mounted where a run store and a pack store are wired):
    `POST {prefix}/packs/{id}/runs` (governed; `?version=`, else the tenant's pin, else the newest;
    422 for a case outside the input schema or a pack with no `conductor.kind`, 404/409/422 as
    `assess` answers, 503 while degraded, as chat is; 202 with the run id and stream path),
    `GET {prefix}/runs/{id}`, `GET {prefix}/runs/{id}/stream?from_seq=`, `POST {prefix}/runs/{id}/stop`,
    `GET {prefix}/runs?pack_id=&subject_id=` (newest first, `RUN_LIST_LIMIT`). A run pins pack id,
    version and archive digest, and refuses to run if the stored version's digest has changed. It
    is queued under `case_queue_key` (tenant, pack, subject), so runs of one case serialize, and
    another tenant's run is a 404. Its modes call a fresh `AgentExecutionService` per run, and its
    Trace and Decision go to the runtime fabric's canonical store. `assess` and runs share
    `plato.api.packs.domain_pack_record` and `materialized_domain_pack`; chat and runs share
    `plato.api.assistants.not_configured`. `PlatoClient` gains `assess`, `submit_case_run`,
    `case_run`, `case_runs`, `stream_case_run` and `stop_case_run`.
  - **A domain pack is an eval entity** (Phase 2 parity): `jazzx_sdk.pack.eval_invoker`
    (`PackAssessmentInvoker`, `PACK_ENTITY = "pack"`) runs a case as the pack's deterministic
    assessment of its input, against `config["version"]` or the host's choice;
    `jazzx_sdk.evaluation.experiments.EntityInvokers` hands each case to the invoker for its
    entity's type. Plato's experiment runner serves `assistant` and, given its pack store, `pack`
    entities, the latter against the version `assess` would pick. New built-in scorer
    `subset_match` (`jazzx_sdk.evaluation.metrics`): the fraction of the leaves a case's expected
    value names that the output holds at the same path, so a case can name only the fields that
    matter. jaci's five DSCR gold cases pass as an experiment over `dscr-core` (verdict and binding
    cap).
  - Review fixes: a pack schema's `minimum`/`maximum` apply wherever a type sits (an `anyOf`
    member, `items`, a `$defs` entry), not only on a property's own schema, so the DSCR
    `residential_unit_count` bound of 1-4 now refuses 9; `default` anywhere but a property is
    refused. An authoritative assessment that fails only on composed caps cites the NA or
    unresolved cells, else the binding cap, in the governor's violations. An interrupted run no
    longer also counts `investigation.halted`. Every caller of `domain_pack_record` passes `has=`
    with its article, so the assistant-pack 409 reads "which has no an assessment" nowhere.
- **PR #82 review follow-ups** (fixed here rather than on the release branch; none was
  critical):
  - An assistant turn a guardrail blocked is still scored (a refusal is often the expected answer),
    and its scorers now see the block, in experiments and in prompt optimization alike: new
    `scorers.Prediction` (an output plus keys for its scorers' context) and `split_prediction`;
    `Invocation` extends `Prediction`; a `PredictFn` / `PromptTarget.predict` may return one; and
    `AssistantInvoker`, `AssistantPromptTarget` and `interactive_predict_fn` set
    `scorers.BLOCKED_KEY` to `{"reason", "rule_id"}` for a blocked turn (one helper,
    `agents.interactive.optimize.blocked_context`). The optimizer and the A/B helpers
    (`guidance_ab`: `validate_guidance`, `compare_manifests`) unwrap a `Prediction` before scoring.
    `AssistantPromptTarget.predict` and `interactive_predict_fn`'s predict return a `Prediction`
    rather than the bare output.
  - Feedback with no entity is duplicate-checked only against other entity-less feedback, not
    against every entity's, and no longer loses its candidates to newer entity feedback: new
    `FeedbackQuery.no_entity` (exclusive with `entity`) selects feedback recorded without one. The
    flag it sets, `potential_duplicate`, is display-only.
  - Plato's formal route stops a timed-out worker once (in `finally`), not twice, so a worker that
    ignores the first stop no longer costs a second stop timeout.
  - Not changed: an experiment whose read fails after its claim is left for `job:eval-reclaim`
    (the same database failure fails its `finish`, so reading the claimed copy would not help); an
    optimization's apply releasing its claim when the record fails to save is deliberate (the
    draft write is idempotent); `actor_id or ""` is stored as None by the draft store.
- **The chat lifecycle, for jazzx-assistant** (their requirements for 2.5.6, reshaped onto what
  japes has):
  - `stream_chat_turn` waits for its engine task to unwind when the stream is abandoned or its
    task cancelled, so the workspace is released and a caller waiting on the stream's task (a
    barge-in starting the replacement turn) finds no stage still running.
  - `run_chat_lifecycle` / `stream_chat_lifecycle` (new): a turn whose value is any type.
    They return (or end with a `ChatFinalEvent` carrying) a `ChatRun[T]`: `value` (finalize, else
    compose, else the answering branch; a failed step's substitute), `route`, `conductor` (the
    engine's `ConductorRun`), `status` in `TurnRun`'s vocabulary (`completed`, a refusal included;
    `interrupted`; `failed`), `error` (`ChatError`: `code`, `stage`, `user_message`,
    `operator_detail`, `retryable`) and `diagnostics`. `stream_chat_lifecycle` takes no `agent`;
    a stage publishing a `ChatFinalEvent` is refused as a `done` event is. `run_chat_turn` and
    `stream_chat_turn` are now adapters over the same cores, resolving the `InteractiveResponse`
    and logging the metrics they did. `answer_stream_step`'s `sink` is optional, defaulting to
    `turn.publish`.
  - A `prepare` stage (optional, between `validate` and `gate`; `build_chat_pipeline(with_prepare=)`,
    added by `pipeline_for` when bound, cancel-guarded, in the catalog): it emits the turn once
    for every later stage. The reference `prepare_step(app=)` emits a `PreparedTurn` (`messages`
    bounded by `turn_messages`, plus `app`, the application's value). With a `PreparedTurn`, the
    reference gate's `classify` and `escalate` see the turn with the prepared history, and the
    reference answer (blocking and streaming) sends the prepared messages, so the gate and the
    answer cannot see different histories. An application's own `prepare` may emit anything; its
    own stages read it from `state.emitted["prepare"]` (`prepared(state)` for a `PreparedTurn`).
  - Errors keep the user's text and the operator's apart. `chat_step_error` (new, the lifecycle
    runners' default `on_step_error`) halts and substitutes a `ChatError` (`<step>_failed`,
    `user_message` = `DEFAULT_ERROR_MESSAGE`, `operator_detail` = the failure's text); the run is
    `failed` with no value. `on_step_error=None` still propagates raw, and `CancelledError` is
    never converted. `default_step_error` (the legacy runners') is unchanged, now documented:
    `answer` is the user's, `incomplete_reason` the operator's. With a handler, a workspace that
    cannot be acquired fails the run (`workspace_acquire_failed`, nothing runs) and one that
    cannot be released is recorded in `diagnostics["workspace_release"]` with the value kept;
    without one, both propagate. Both streams' final event now follows the workspace release.
  - Case runs: a failed run's journal and `GET {prefix}/runs/{id}` (and the list) carry
    `runs.case.CASE_FAILED_ERROR` (`case_failed`, a generic message), not the exception's text,
    which stays on `TurnRun.error` and in the log.
  - Every way a turn ends is observed, once: the runners report through one report-once path, so
    a raw propagated failure (`turn_failed`, then raised), a workspace failure with no handler, a
    task cancel (`interrupted`) and an abandoned stream (new `ChatRun` status `abandoned`) each
    reach `on_complete` exactly once, and a raising callback changes nothing. The legacy stream
    still reports no response for an abandoned turn (it logs `chat.abandoned`, as before).
  - `ChatTurn.cancel_after_answer` (`deliver`, the default, or `drop`): with `drop`, the engine's
    `stop_requested` checks `turn.cancel` before every stage, so a cancel landing after the answer
    stops compose, persist and finalize, and the run is `interrupted` with no value (a barge-in).
    A `persist` that already ran is not undone. With `deliver`, the stage guards decide as before.
  - `ChatTurn.persistence` (`agent`, the default, or `caller`): with `caller`, the runners refuse
    (`PersistenceConflictError`, from `check_persistence`) a turn japes could still write, a
    `session_id` for the agent's conversation store or the reference `persist` bound, so no
    agent, session or reference stage records it; the application records it outside japes or
    in its own `persist`, which runs once after compose and before finalize. Four policies in the
    requirements collapse to these two: to japes, "external" and "none" both mean it writes
    nothing, and "application hook" is a bound `persist`. `ChatTurn.persist_failure` (`required`,
    the default: the step fails through `on_step_error`, `persist_failed`; or `best_effort`: the
    value stands and the error is in `diagnostics["persist"]`). A cancel during persist
    propagates either way.
  - Review fixes: the legacy runners keep propagating a workspace failure (classification is the
    lifecycle runners'), and a classified one is logged as well as recorded, so an abandoned
    stream cannot lose it. A step a handler recovered without halting leaves the turn to resolve
    as usual, named in `diagnostics["recovered"]`, instead of failing it. `PreparedTurn` refuses
    messages that do not end with the user's message.
- **Formal checks over canonical policy (PR #85, Sourav)** landed on `plato` and was brought into
  `v2.5.6`. Follow-ups here: an `Expression` needs a `value` or a `value_source` (a materialized
  one has both); with neither it no longer loads, so a threshold left out is refused rather than
  compared against `None`.
  The fact catalog a pack derives from its input schema is read by `pack.schemas`
  (`schema_facts`, new): a local `$ref`, a union with null and an `enum` resolve to their
  primitive type, and an unsupported keyword is refused, as for the input model. The loader's own
  parser skipped any property without a direct `type`, dropping DSCR's `residential_unit_count`
  and `interest_rate`, so the rules reading them had no fact to compile against. `unit` / `x-unit`
  join the schema's supported annotations.
  Plato's formal route never runs a JSON rule pack ungated. A request lists `compile` entries
  (`plato.api.formal.PackCompile`); Plato compiles each from the tenant's published domain pack
  (named version, else activated, else newest, as `assess`) and passes only those hashes to the
  worker as approved, so a caller-submitted compiled pack is refused and a caller cannot approve
  its own rules. The worker takes a `WorkerInput` (`request` plus a required
  `approved_rule_pack_hashes`) from its parent and refuses to run without the set. Approval is
  derived from the pack store rather than stored: a published version has passed the publish
  check and cannot change. `create_formal_router` gains `pack_store_for` and
  `tenant_from_request`.
  Review fixes: an empty `compile` list is a plain request (it reached the worker unvalidated);
  compiling runs inside the capacity slot and off the event loop; the case-run status constants
  (`kinds.INTERRUPTED`, `kinds.FAILED`) are shared with `runs.case` rather than restated; a
  pack schema's null allowance is found through a local `$ref` and in an `enum`.
- **Plato pilot findings** (from jaci's DSCR and clinical-intake pilots on Plato):
  - The investigator no longer fails every real call with `rich_evidence_requests=True`: its
    `RichHypothesisUpdate` output (a free-form `query_params` dict) goes to the agent runtime as
    `AgentOutputSchema(..., strict_json_schema=False)`, as the verifier's and narrator's do, since
    OpenAI's strict mode rejects any dict-shaped field. Every DSCR case run on Plato, and jaci's
    in-process `DSCRConductor`, were affected. A contract test now builds every mode the DSCR
    conductor uses through `sdk_mode_factory` and runs the output type each passes through the
    Agents SDK's own schema construction.
  - A failed mode no longer passes as success. `CaseResult.failed_modes` lists the modes that
    failed at least once; the run is `failed` when the investigator never succeeded (its decision
    rests on no investigation), else `degraded`. A `failed` result ends the case run `FAILED`
    with its output kept (`runs.case.FAILED_STATUSES`), and the Decision of a run with failed
    modes requires human review.
  - The scope gate reaches the LLM only when the manifest sets `out_of_scope_check_model`, as
    its docstrings said. A host supplying `llm_manager` (Plato always does) switched every
    assistant to the LLM check, which classifies against `in_scope_action_classes` as the
    allowed topics, so an assistant declaring none declined every turn, the bundled demo pack
    included. Open (a design question from the pilot): the scope gate runs before a pack's own
    input guardrails, so a red flag an LLM scope check misjudges is declined generically and
    never reaches the pack's escalation rule.
  - Activating an assistant-pack version serves its manifest without a restart: `activate`
    recomposes the tenant's registries after moving the pin, as `forget_packs` does. It used to
    drop the caches only, and `agent_for` reads the manifest store before composing, so the next
    agent bound the previous version's manifest (a publish recomposes too, under the old pin).
  - Models built from a pack's JSON Schema (`pack.schemas`, base `PackModel`) follow the schema
    on null. A property that allows null keeps `None`. A defaulted one takes its default and
    refuses null, so strict structured output must supply a value. One the schema neither
    requires, defaults nor lets be null is still accepted as absent on input, and is left out of
    the output when `None` (`PackModel.absent_when_none`), so a reader's own default applies.
    Every non-required field used to be nullable, so a case run's decision carried
    `conditions: null` and `condition_id: null`, which jaci's `EligibilityRecommendation`
    rejected (its `_without_nulls` workaround can go).
  - The publish check refuses an archive holding both `pack_manifest.yaml` and `manifest.yaml`
    (`ambiguous_manifest`, blocking), naming the role it would have published as. It used to be
    classified by whichever name `MANIFEST_NAMES` reads first, so an assistant pack carrying a
    domain manifest published as a domain pack and was never served, with nothing said.
  - Not changed (pilot item 6): `cltv_pct`'s `rounding_places: 2` is a policy decision for the
    DSCR corpus owner; the seed pack's `no_ontology` / `unverifiable_rules` check findings are
    noted, not fixed here.
- **Chat runtime, phase A** (jazzx-assistant's second requirements page):
  - `InteractiveAgent.respond(..., persist=False)` / `respond_stream(..., persist=False)`: the
    session id still names the turn (`conversation_id`, correlation), but no conversation is
    loaded, written, or bound to a native session. It covers the single-shot and agentic paths,
    and an injected `session_factory` session.
  - `ChatTurn(persistence="caller")` now accepts a `session_id`: the reference answer runs the
    agent with `persist=False`, `check_history_ownership` no longer refuses supplied history for
    it, and `check_persistence` refuses only the reference `persist`. A session id is then a
    correlation and resource-lookup key, as the requirements ask.
  - `ChatError.category` (`ChatErrorCategory`): the generic kind of failure japes owns, beside
    the specific `code`. `stage` (a stage failed or nothing answered), `resource` (the workspace),
    `persistence` (a failing `persist`, required or best effort), and `deadline`, `capacity`,
    `cancellation`, `abandonment`, `delivery` for the coordinator to come. An application maps its
    own store, authorization and domain failures to codes of its own.
  - A typed cancel reason. `CancelReason` (`user`, `superseded`, `deadline`, `drain`, `aborted`
    for a hard task cancel, and the default `cancelled`). `request_cancel(turn, reason)` sets the
    reason before the signal. `ChatRun.cancel_reason` on every interrupted run: not started,
    stopped mid-run, dropped after the answer, or aborted. It replaces the
    `diagnostics["cancel_reason"]` key. `ChatTurn.cancel_reason` still accepts a caller's own text.
  - A public surface: `jazzx_sdk.pipelines.chat.__all__`, grouped by use (turn input, runners,
    results / errors / events, policies and cancellation, pipeline building, reference stages).
    `tests/test_chat_public_api.py` holds it: every export resolves, nothing public is left
    out, and the stored literal values (`ChatStatus`, `ChatErrorCategory`, `CancelReason`,
    `Route`, and the turn's `persistence`, `persist_failure`, `cancel_after_answer`) are
    snapshotted, so changing one is a deliberate contract change. New user guide
    `docs/CHAT_LIFECYCLE.md`: the two runner pairs side by side, migrating from `run_chat_turn`,
    persistence ownership (`persist=False` included), errors, cancellation, the workspace and
    prepare, with the Python floor and dependencies.
  - Review fixes: the reference answer passes `persist=False` only for a caller turn that
    names a session, so an agent without the keyword still runs one that does not;
    `RecordingAgent` records nothing for a `persist=False` turn (its caller owns the record);
    a reason given through `request_cancel` before a hard task cancel survives it rather than
    reading `aborted`.
- **Chat runtime, phase B** (the coordinator on `jazzx_sdk.runs`):
  - `TurnRunStore.finish(run_id, event, **fields)` (both stores): a run's terminal fields and its
    terminal event in one write (one transaction in `DbTurnRunStore`), so a reader that sees the
    `done` event finds the run terminal, and one that finds it terminal sees `done`. Both
    `ResilientRunner` (completed, interrupted) and `CaseRunner` (completed or interrupted, failed)
    now finish through it. They used to journal `done` first and commit the status after, so a
    reconnecting reader could see a finished stream on a run still marked running.
  - Replacement policy (`runs.ReplacementPolicy`: `wait`, `reject`, `supersede`) on admission.
    `TurnRunStore.admit(run, replacement=...)` (both stores) decides against the key's active runs
    in the same step as the create; the DB store holds those rows locked for it.
    - `wait` is today's FIFO.
    - `reject` raises `runs.TurnRejected` (naming the active runs) and creates nothing.
    - `supersede` cancels the key's queued runs and asks its running one to stop; the new run is
      claimed only once that one is terminal, and each run's events stay on its own `run_id`.
    - `ResilientRunner.create_run`, `CaseRunner.submit` and `TurnDispatcher.submit` take
      `replacement=` (default `wait`).
    - Cancel-queued-and-stop-running is one helper per store, shared by `admit` and
      `request_stop_conversation`.
  - Stop reasons and deadlines.
    - `TurnRun.stop_reason` is set with the stop flag: `request_stop(run_id, reason=)` and
      `request_stop_conversation(key, reason=)` (default `user`, on the stores and
      `ResilientRunner`), `superseded` when admission supersedes, and `deadline` when a run runs
      out of time. A drain can say `drain`. Values are `pipelines.chat.CancelReason`'s; a caller's
      own text is accepted.
    - `TurnRun.deadline_seconds` is stored at admission (`create_run` / `CaseRunner.submit` /
      `TurnDispatcher.submit`), so whichever worker executes the run enforces it. Past it,
      `ResilientRunner.watch_deadline` asks the run to stop (monotonic, from the start of
      execution), and both runners cancel the watcher when the run ends.
    - Plato's `GET {prefix}/runs/{id}` reports `stop_reason`.
  - Lanes and capacity, policy-workbench's model.
    - `TurnRun.lane` (default `runs.DEFAULT_LANE`, `interactive`) and `TurnRun.principal` are set
      at admission (`create_run` / `CaseRunner.submit` / `TurnDispatcher.submit`).
    - `runs.LaneLimits(lanes={lane: n}, per_principal=n)`: its `admits(candidate, running)` is the
      one rule both stores apply.
    - `claim_next(..., limits=)` leaves a run queued while its lane or principal is full.
    - New `claim_any(lane, token, limits=)` claims the oldest admissible run in a lane across
      keys. A principal at its cap is skipped, not waited on, so it does not hold up the others.
    - `CaseRunner.drain_lane` is the worker-side loop over it, and `CaseRunner.drain` /
      `TurnDispatcher.drain` take `limits=`.
    - The DB store counts RUNNING runs under a per-lane transaction lock (new
      `fabric.db.locking.advisory_xact_lock`: `pg_advisory_xact_lock` on Postgres, a no-op on
      sqlite, whose writers are serialized), since row locks cannot cover a row another
      transaction is about to flip to RUNNING. `claim_any` scans at most `CLAIM_SCAN_ROWS` queued
      runs, since `lane` is in the run's JSON rather than a column.
    - Tested on sqlite and in process; the Postgres lock path has no test here yet.
  - The chat coordinator (`runs.ChatCoordinator`, in `jazzx_sdk/runs/chat.py`): a chat
    lifecycle turn run as a `TurnRun`, on the same admission, lanes, claim, heartbeat, stop flag,
    deadline and journal.
    - What runs is `stream_chat_lifecycle` over a `runs.ChatTurnSpec` (turn, components,
      workspace) that the application's turn factory builds from the run, so any worker that
      claims it can execute it from the stored input.
    - Every event a stage publishes is journaled; the terminal event is
      `{"done", "status", "route", "value", "error", "cancel_reason", "commit"}`, finished in
      the same write as the run's status. `error` is the `ChatError` without `operator_detail`,
      which goes on `TurnRun.error`. A stage event carrying `done` is refused, since readers stop
      at the first one.
    - `DurabilityPolicy`: `commit_before_delivery` runs the application's commit hook before the
      terminal event, and a failed commit fails the turn (`commit_failed`, category
      `persistence`) with no value delivered; `delivery_before_best_effort_persist` runs it after,
      logging a failure; `none` runs none. The hook is called at most once, with the `ChatRun`,
      and not for an abandoned turn. `runs.CoordinatedTurn` reports `commit` (`not_attempted`,
      `confirmed`, `failed`) and the hook's marker. The page's `caller_managed` is not a separate
      value: with the journal as the runs layer's own record, it behaves as `none`.
    - The durable stop flag becomes the turn's `request_cancel` with the run's `stop_reason`
      (polled every `STOP_POLL_SECONDS`), so a user stop, a supersede and a deadline reach
      `ChatRun.cancel_reason`. A turn stopped while queued runs no stage.
    - `runs.ChatTurnHandle` (`start`, or `handle(run_id)` for a run submitted elsewhere): an
      idempotent `cancel(reason)` (the first reason stands), `events(after_seq, disconnect=)`, and
      `result()`. `DisconnectPolicy` for a reader that leaves early: `detach` leaves the turn
      running; `cancel` stops it with reason `disconnected`; `abandon` cancels its producer, with
      reason `abandoned`, releasing the workspace and committing nothing.
    - `CancelReason` gains `disconnected` and `abandoned`.
    - A task-cancelled execution finishes the run interrupted with reason `aborted`; a turn
      factory or lifecycle that raises finishes it failed (`turn_failed`) and re-raises.
    - `drain(key)` and `drain_lane(lane)` as on `CaseRunner`.
  - Plato's `POST .../chat/stream` runs the chat lifecycle through the coordinator, so a
    Plato-hosted assistant's streamed turn goes through validate, gate, answer, persist and
    finalize rather than a bare `respond_stream`. The run's input carries `message` (was a
    `messages` list), and the stream's last frame is the coordinator's terminal event (its
    `InteractiveResponse` under `value`, was `response`). A dropped client detaches. The
    unused `dispatcher` is gone from `create_assistants_router`, `create_app`, `PlatoWiring` and
    `durable_runs`.
  - Shutdown and a worker loop (`jazzx_sdk/runs/worker.py`).
    - `runs.settle_runs(store, active, timeout=)`: asks each running execution to stop with
      reason `drain` (new `runs.schema.DRAIN`), waits up to `timeout`, cancels the rest (which
      finish `aborted`), and returns a `runs.SettleReport` of settled and unsettled run ids.
    - `ChatCoordinator.close(timeout)` settles the turns it is executing and refuses new
      `start`s; its drains stop claiming. Queued turns stay queued for another worker.
    - `runs.RunWorker(store, execute, lanes=, limits=, concurrency=, poll_seconds=,
      max_lifetime_seconds=)`: a worker process's loop. It claims across keys per lane within
      `LaneLimits` (`claim_any`), runs up to `concurrency` executions at once, survives a failing
      one, stops claiming once its lifetime is up and finishes what it holds, and `close(timeout)`
      settles through `settle_runs`. `execute` is `(run, claim_token)`: `ChatCoordinator.execute`,
      or a closure over `CaseRunner.execute` for case runs.
    - `CaseRunner` and `TurnDispatcher` have no `close` of their own: a process that needs
      bounded shutdown for them runs them under `RunWorker`.
  - Review fixes over phase B:
    - Every claim of a key takes the key's transaction lock (`DbTurnRunStore`; on Postgres,
      `pg_advisory_xact_lock`), so `claim_next` and `claim_any` cannot both find a key idle and
      start two runs on it. `claim_any` reads the lane's queue unlocked and takes a candidate's
      key lock without waiting (new `fabric.db.locking.try_advisory_xact_lock`), so it no longer
      row-locks other keys' queued runs, which made a concurrent `claim_next` skip a key's oldest.
    - `claim_any` pages through the lane's queue (`CLAIM_SCAN_ROWS` per page, lane filtered in
      SQL) instead of giving up after one window, so a backlog on busy keys or other lanes no
      longer starves a lane.
    - `claim_any` (both stores) considers only a key's oldest queued run, so a key whose oldest
      is passed over for its principal's cap, or sits in another lane, does not have a newer run
      started ahead of it.
    - `ResilientRunner.execute` and `CaseRunner.execute` finish a task-cancelled run interrupted
      with reason `aborted` (`runs.schema.ABORTED`, moved from `runs.chat`), as
      `ChatCoordinator.execute` does, instead of leaving it running for the reaper.
    - `RunWorker.run` survives a failing claim, retrying after the poll interval.
    - `settle_runs` bounds the unwinding of cancelled tasks by `timeout` too; one still unwinding
      is reported unsettled and left running.
    - Plato's turn factory still reads a run whose input carries `messages`; an empty `message`
      is a turn like any other.
    - A cancel that lands after a run's terminal write (`ResilientRunner`, or `ChatCoordinator`
      during a best-effort commit) leaves that write standing rather than rewriting the run
      `aborted` with a second `done` event.
    - `DbTurnRunStore`'s key-head check orders by `(created_at, run_id)`, as the lane scan does.
    - Tested on sqlite and in process, and on Postgres when configured (below).
  - Store tests can run on Postgres: set `JAPES_TEST_POSTGRES_URL` (shell or `.env`, the one key
    the suite reads from it). `tests/db_backend.py` gives `STORE_BACKENDS` (`memory`, `db`, plus
    `postgres` when set) and `open_db(backend)`, a `DbStore` on its own schema, dropped on
    dispose. The runs tests (`test_case_runner.py`, `test_chat_coordinator.py`) parametrize over
    it; a Postgres-only test races ten concurrent claims on one key, with each claim's row lock
    delayed so the racers overlap, and fails against the store before the key lock (four
    `claim_next` calls all claimed). The other DB-backed tests still run on sqlite only.
    Documented in `docs/LOCAL_TESTING.md` and `.env.template`.
  - Every DB-backed test now runs on Postgres too when the key is set: 58 test files take the
    `db_backend` fixture (`conftest.py`, over `tests.db_backend.DB_BACKENDS`) or `STORE_BACKENDS`,
    and build stores with `open_db(backend, path)`. Two stores opened on one path share a schema,
    as two sqlite stores on one file share a database; `conftest` drops a test's schemas after
    its stores are disposed. The Postgres engine has no pool, since an asyncpg connection
    belongs to its loop and sync tests build a store under `asyncio.run` and serve it through
    `TestClient`'s. Left on sqlite, each with its reason at the test: backend-name handling,
    sqlite paths and in-memory behavior, alembic run against a sqlite file, `DbStore`'s own
    engine and dispose, and stubs that never connect. With Postgres: 1462 passed, 3 skipped;
    sqlite alone: 1054 passed, 4 skipped. No production defect surfaced.
  - Review fixes: a path-named schema is salted with a per-run id, so a run never adopts a schema
    an earlier (killed) or concurrent run left on the same database, while two stores on one path
    still share a schema within a test; `conftest` disposes every store and drops the test's
    schemas even when one dispose raises, then raises that failure; `test_conversation_store_dogfoods_fabric_db` keeps its name.
  - Push-review fixes over phase B:
    - `DbTurnRunStore.admit` takes the key's lock first, so two `reject` (or `supersede`)
      admissions of an idle key, which has no active row to lock, cannot both find it idle.
    - `claim_any(..., kind=)` (both stores) and `RunWorker(kind=)` restrict a lane claim to one
      run kind; `CaseRunner.drain_lane` claims only case runs and `ChatCoordinator.drain_lane`
      only turns, so a host sharing one store across both never hands one kind to the other's
      executor.
    - Every drain (`CaseRunner.drain` / `drain_lane`, `ChatCoordinator.drain` / `drain_lane`,
      `TurnDispatcher.drain`) goes through `runs.worker.drain_claims`: a run whose execution
      raises is recorded and the drain carries on, raising the first failure once the queue is
      empty, so the runs behind it are not left queued with readers following them.
    - `check_persistence`'s docstring says what it guarantees: japes' own stages; an
      application's own `answer` runs its agent with `persist=False` itself.
  - Push-review fixes, second pass:
    - The `dscr_core` seed's `residential_unit_count` is a required integer (1-4), never null, as
      jaci's `LoanApplication` already makes it (derived 1 for single-unit types, stated for
      2-4 unit). Nullable, a 2-4 unit file with no count left `PLAT-TWO-UNITS-ONLY` unevaluated
      and a 3-4 unit property Platinum Select excludes was allowed; the Ohio/Pennsylvania
      "Residential 1-2" and Mississippi single-unit PPP gates were skipped the same way. `assess`
      now refuses the null.
    - The formal worker reads up to `LocalFormalConfig.worker_read_bytes` (`max_message_bytes`
      plus `worker_envelope_bytes`): the request limit measures canonical bytes, while the worker
      reads the envelope as the parent serializes it. The parent checks the exact payload against
      that same limit and answers 413 past it, so a caller's oversized request is no longer a
      worker 502.
    - `RunWorker(..., kind=)` is required (None claims every kind), since a store is shared by
      chat turns and case runs.
    - `jazzx_sdk.pack.store.manifests_in(directory)` names the `MANIFEST_NAMES` present; the
      upload check and the seeder both refuse a pack directory holding both names (the seeder
      published it silently from `pack_manifest.yaml`).
    - Three test files that import converted helpers (`test_plato_formal_gate.py`,
      `test_plato_runs_api.py`, `test_plato_client.py`) take `db_backend` too; they raised
      `TypeError` after the Postgres conversion.
    - Seed text: schema descriptions name this pack's paths, not jaci's; the profile and
      `DSCR-CONDO-HOA-RESERVES` name the 8.17 consolidated sources; `DSCR-OVER-2M-NO-RATIO` points
      at ENCODING_NOTES §3 G2; the ITIN loan-max comment no longer claims every loan-amount bound
      is profile-linked (`TODO(loan-bound-profile-claim-false)` lists the ones that are not), and
      `TODO(ppp-rules-duplicated-per-program)` records that Platinum's PPP rules copy Standard's.
    - `conftest` raises a dispose failure even when dropping the test schemas fails.
  - Push-review fixes, third pass:
    - `ChatCoordinator`'s stop watcher survives a failed store read, as the heartbeat does, so a
      stop, supersede, deadline or drain still reaches a turn after a connection blip.
    - `ResilientRunner` no longer rereads the run between starting its heartbeat and the `try`
      that stops it (it uses the run it just claimed), so a failing read cannot leave a
      heartbeat keeping a dead run RUNNING.
    - Plato's formal compile of a program pack with no overlays named uses the assessment's
      `default_program`, as `assess` does, or is refused when there is none, instead of silently
      checking only the core rules.
    - `ChatCoordinator.start(..., limits=)` drains within the limits it is given.
    - `assess` refuses an input stating a value its pack's case input schema does not allow
      (type, `enum`, bounds), as a case run's validation does; it read the raw input, so a
      `housing_history` of `0X120X12` skipped Standard's `DSCR-HOUSING-HISTORY-CLTV` (which
      matches exact spellings) and a 0x120x12 loan came back allowed. The seed's
      `housing_history` is an `enum` of its six ratings. `TODO(unit-count-not-tied-to-type)`
      records that nothing ties `residential_unit_count` to `property_type`.
    - A deadline stop that fails is retried on the heartbeat's cadence rather than lost.
    - `jazzx_sdk.pack.assessment.default_program(pack)` is the one program-selection rule, used by
      `assess` and Plato's formal compile. `PackCompile.overlays` omitted means that default
      program; an explicit `[]` means the core rules only.
    - Under `delivery_before_best_effort_persist` the terminal event's `commit` is `deferred`
      (new `CommitState` value): it is written before the commit runs, whose outcome is on
      `CoordinatedTurn.commit`.
  - PR #81 fixes, from a full-range review of v2.5.6:
    - Plato's streamed chat carries the request's `conversation_id` into the turn, as `/chat` passes
      it to the agent; the reply's ids (and the feedback attached to them) named the session id
      instead.
    - `request_stop` (both stores) leaves a run that has ended as it ended: stopping a finished
      run, from either Plato stop route, a deadline firing during a deferred commit, or a drain,
      stamped `stop_requested` and a reason on a completed record.
    - `request_stop` returns whether the run is now asked to stop (the store protocol, both
      stores, `ResilientRunner`), and the three stop routes (Plato's assistants and runs, the
      SDK's `run_routes`) answer with it rather than a literal `stop_requested: true`; the SDK
      route answers 202 when it takes the stop on and 200 for a run already ended.
    - `CaseRunner.execute`'s cancel path leaves a run that has already ended (reaped, say) as it
      is, as `ResilientRunner` and `ChatCoordinator` do, instead of rewriting it `aborted` with a
      second `done` event.
  - The `dscr_core` seed's rule-read string inputs are enums of the vocabularies their descriptions
    state: `property_state` (the 50 states, DC and the five territories), `citizenship_type`,
    `occupancy_subtype`, `dscr_documentation_type`, `borrower_entity_type`,
    `prepayment_penalty_requested` and `channel`. With `assess` refusing a value outside its
    schema, a mistyped `sd` or `ITIN` no longer skips the ineligible-state or ITIN rules and
    allows the loan. A test holds every value a rule compares against inside its field's enum.
    jaci's `LoanApplication` still types these as `str`, so a jaci input with another spelling is
    now refused by the seed's `assess`.
  - Plato's assistants get the current `ClientLayer`'s LLM (`plato.wiring.default.CurrentLLM`,
    beside `CurrentFabric`), so a provider key set through `/v1/config` reaches assistants already
    bound: `LLMManager` builds each provider once with the key it read then. Feedback retrieval's
    RAG store is still the boot layer's (`TODO(feedback-rag-bound-at-boot)`): its per-tenant
    index caches collection ids per store.
  - PR #81 bot review:
    - `combined_catalog` copies a host `GuardrailRegistry` even with no pack guardrails (the
      binding registered the scope guardrail into the shared host, reaching every assistant
      built through it), and copies every guardrail at its own tier (a tier-1 floor was
      re-registered at 3).
    - The expression evaluator reads a float on a decimal catalog fact (an authored YAML threshold
      on an unmaterialized `Pack.policy_registry`, a caller's context value, a membership list
      member) as the exact decimal it spells before `typed_scalar`'s strict check; such rules were
      withheld, and `in` against float members never matched a `Decimal`.
    - `compose_caps` reads its compare value as the evaluators read a number (`Decimal`, numeric
      string, float); a catalog-typed `Decimal` was None and every case failed its cap.
    - A matrix axis value that is not a finite number is INDETERMINATE, not a raised error.
    - `materialize_accepted_policy` refuses a draft whose source is no longer supplied with its
      "source changed" error rather than a `KeyError`; the compiler's empty-selection error no
      longer prints an always-empty gap list.
    - Two test files import sibling helpers as `tests.<module>`, like the rest of the suite.
    - Every `_number` read in the matrix evaluator (axis and compare value) turns a value that
      is not a finite number into INDETERMINATE rather than a raised error.
    - `compose_caps` reports a cell that is neither an ineligible marker nor a number as
      unresolved rather than raising.
    - The formal compiler matches an overlay's replacements on each compiled rule's recorded
      `(policy_id, rule_id)`, not by splitting the `policy_id:rule_id` key, which broke for ids
      holding `:`.
    - `subset_match` walks any `Mapping`, not only a `dict`.
    - `CoordinatedTurn.run` is typed optional, as `finish` can return None for a purged row.
  - `test_the_worker_reads_a_request_at_the_limit_inside_its_envelope` ran `formal_worker.main()`
    in the pytest process, which on Linux applied the worker's `RLIMIT_CPU` / `RLIMIT_AS` to the
    whole run and killed CI partway ("CPU time limit exceeded", exit 152). It stubs
    `_apply_linux_resource_limits`, as the sibling limits test fakes `resource`.
  - `test_pack_store.py` built its archives with `writestr` on bare names, which stamps the
    current time, so two builds either side of a two-second boundary differed in bytes and the
    cross-tenant blob-sharing test failed now and then (more often on Postgres, which is slower).
    Entries now carry a fixed `ARCHIVE_TIMESTAMP`.
  - `test_db_locking.py` gains a Postgres-only contention test: a row one transaction holds is
    skipped by another. It fails if the locking statement falls back to a plain select, which the
    contract tests cannot see. `skip_locked_first`'s docstring now says its lock covers every row
    the statement selects, so a caller that means one row limits it (all three callers do).
- **Python custom scorers run in Plato on a workstation.** New
  `jazzx_sdk.fabric.canonical.local_executor.LocalPythonExecutor`, the SDK's one `PythonExecutor`:
  each run is a child `python -I -S` with an empty environment (no inherited secrets), a fresh temp
  cwd, `RLIMIT_CPU`/`RLIMIT_FSIZE`/`RLIMIT_AS` set before the source runs (`RLIMIT_AS` is not
  enforced on macOS), a wall-clock timeout that kills the process group, a result cap
  (`MAX_RESULT_BYTES`) and a concurrency cap. Context and result travel as JSON; a policy rule's
  `(bool, dict)` result arrives as a tuple. It is defence in depth, not a sandbox, so it raises in a
  deployed posture. `PlatoWiring.python_executor` (new, default `None`) reaches the eval router;
  both shipped wirings set it from `plato.wiring.workstation_python_executor()`, which is `None` in
  a deployed posture, so dev-daily and up still store python scorers without running them until a
  deployment names an isolated executor. The same executor runs python policy rules for any host
  that puts it at `PYTHON_EXECUTOR_CONTEXT_KEY`; Plato's `assess` route does so with the wiring's.
  - A python custom scorer's case is coerced to JSON first (`jsonable`, now shared in
    `evaluation.scorers` with the experiment runner), so a structured assistant output (a model)
    scores instead of failing every case.
  - The child's CPU limit sits `CPU_LIMIT_MARGIN_SECONDS` past the wall-clock timeout, so a busy
    loop is reported as a timeout rather than killed by whichever limit fires first; a source
    that ends the child (`raise SystemExit`) raises `LocalExecutorError`.
- Version cut from `dev` at the v2.5.5 squash (`730c6c39`).

## [2.5.5] - unreleased

- **Full-range review fixes (origin/main...v2.5.5).**
  - **A Knowledge Hub outage no longer reads as "no such collection".** New
    `KnowledgeHubClient.find_collection_by_name` returns None only on a 404 and raises otherwise
    (`KnowledgeHubError`, or the transport error). `RAGStore.collection_id`, the three canonical
    stores' `_ensure_collection` / `_ensure_find_collection`, and `DocStore`'s collection ensure
    use it, so none of them creates a duplicate collection during an outage, and semantic feedback
    retrieval fails instead of returning `[]`. `get_collection_by_name` is unchanged (the MCP tool
    still uses it). Added to `KnowledgeHubLike` and the mock.
  - **An assistant eval case with nothing to say fails instead of scoring an empty prompt.** A dict
    input with neither `messages` nor a non-blank `query` (e.g. `{"question": ...}`, `{}`) raises in
    `AssistantInvoker` and `AssistantPromptTarget`, so the case records as failed. The feedback
    case synthesis prompt now names `inputs.query`, so cases it generates satisfy that contract.
  - **`GET /feedback/aggregate` says when it was capped.** The response is now
    `{"counts": {...}, "truncated": bool}` (`FeedbackAggregate`); `aggregate_feedback` takes
    `max_rows=` (default `EXPORT_MAX_ROWS`). The evaluation page reads `counts`, says "more
    than N" when the filtered count is truncated, and marks the tenant-wide chips `+` when theirs is. Breaking for the route's shape, which is new in this version.
  - Feedback routes reuse `eval_api`'s `_write_guard` and `_entity_filter` instead of restating them.
  - `scripts/plato-local.sh` strips surrounding quotes from `.env` values as dotenv does
    (`PORT="8001"` exported the quotes). `.env.local`, the script and `scripts/README.md` no longer
    point at a workstation-only Postgres script, and say `.env` is read from the start directory.

- **`python -m plato` reads `.env` on a workstation.** Every variable the environment leaves unset
  is filled from `.env` at the working directory (or the file `JAPES_ENV_FILE` names) before a role
  or wiring resolves, and the startup log lists the names it filled as `env_file=.env (...)`. A
  value already in the environment wins, blank or not. Skipped on a container platform (ACA or
  Kubernetes, by their injected variables); the image copies no `.env` either.
  - `jazzx_sdk.config.envvars.load_env_file()` / `env_file_path()`. The SDK never calls them; an
    entry point does, once. In Plato the call sits in the `__main__` block rather than `main()`,
    which tests call in-process.
  - `.env` is the only gitignored env file. `.env.local` is now a committed template for the
    `local` tier, beside `.env.dev-daily` and `.env.template`; a developer assembles `.env` from
    them (e.g. dev-daily's posture against a local Postgres and the Mock Knowledge Hub).
  - `plato/guide.md` (served at Plato's guide page) gains **Your `.env`** under "Locally": the
    templates table and a starter dev-daily-on-a-laptop set. README's `.env` section points there.
  - `scripts/plato-local.sh` no longer parses `.env.local`; its defaults (tier, wiring, tenants,
    run mode, sqlite fallback, port) yield to anything the environment or `.env` names.
    `PLATO_PROFILE=local` sets `JAPES_ENVIRONMENT=local` over `.env`, since the profile was asked
    for by name.
  - `llm.config`'s `dotenv_from=` lookup (`resolve_key`, `llm_from_env`, `ensure_google_credentials`)
    parses with python-dotenv instead of by prefix: `OPENAI_API_KEY` no longer matched an earlier
    `OPENAI_API_KEY_OLD=` line, and `export NAME=` lines now resolve.
  - Tests: `conftest.py` points `JAPES_ENV_FILE` at `/dev/null` for every subprocess and clears
    `JAPESSettings`' own `env_file`, so a developer's `.env` reaches no test. That second one was
    latent before: `test_a_blank_variable_is_unset_for_every_field_kind` failed for anyone whose
    `.env` set `JAPES_ENVIRONMENT`.

- **Feedback and evaluation you can see: an SDK sink, a Plato page, and jaci feeding it.**
  - **`FeedbackApiSink`** (`jazzx_sdk.evaluation.feedback_sink`) submits a `Feedback` to any host of
    the SDK's feedback routes (`server.feedback_api`; Plato today) and returns the stored
    `FeedbackRecord`. Tenant as `X-Tenant-Id`, optional bearer token, an optional `EntityRef` the
    feedback is filed under, the caller's identity headers forwarded, and `feedback_id` as the
    idempotency handle so a retry returns the stored record. Not best-effort: a refusal raises.
    - It is a `FeedbackSink`, not a `FeedbackStore`: the module already decided that a submitter to
      another service offers write only. `FeedbackSink` is now generic over the acceptance record
      (`FeedbackSink[FeedbackAcceptedV1]` for eval-service, `FeedbackSink[FeedbackRecord]` here),
      and the identity-header logic the two share moved to one helper. The submit timeout is the
      named `DEFAULT_SUBMIT_TIMEOUT`.
    - `FeedbackSubmit` gains `decision_id`, `outcome_id` and `pack_id`, the three `Feedback` fields
      it lacked, so a `Feedback` sent over HTTP arrives whole.
  - **Plato's evaluation page, `/api/v1/evaluation/ui`** (in the nav as Evaluation). Feedback with
    review-status counts, filters and a detail view (processing, context and overall summaries,
    quality, actionable items); approve, reject, process again, and add a piece of feedback to a
    dataset as a case. Datasets with their cases, experiments with pass rate and mean score and a
    comparison against another experiment or the entity's baseline (and "make this the
    baseline"), and optimization jobs. Self-contained like the other pages; tenant and identity
    fields shared with the packs page.
    - Write controls render only where both gates the routes apply would admit the write:
      Plato's `withholding` and the SDK routers' refusal of an unauthenticated deployed write.
    - Mounted with or without a database, so the nav link never 404s; without one the page says
      feedback and evaluation are not mounted. The degraded app omits it from its nav.
    - A test reads the page's own `call(...)` routes and checks each is mounted, so a renamed
      route cannot leave the page calling a 404.
    - README and `plato/guide.md` list it.
  - **`…/feedback/{id}/to-dataset` refuses a blank case and says when it added nothing.** A None or
    blank `input`/`expected` is a 422, checked in the library (`feedback_learning.check_case_value`,
    called by `feedback_case`) and by `FeedbackToDataset`. The case id comes from the feedback id,
    so a blank case stored once blocked the corrected one for good. The response gains `added`,
    false when the case was already there. The page checks both fields before sending, says when
    a case was already present, and says when its list shows only the newest page of what the
    filters match.
  - **jaci's ci_spread demo sends Jazz feedback to Plato** when `JACI_PLATO_URL` is set (tenant,
    token and the assistant id it is filed under are settings too); unset, it stays in the
    session. The question and the answer travel as `metadata["turn"]`, which is what Plato's
    processing summarizes when it does not host the assistant. A failed submission shows a
    warning instead of breaking the chat. Tested in jaci against the real Plato app over ASGI.

- **PR #75 review: fixes for v2.5.4 code, also carried to `dev`.**
  - **A missing deployment dependency withholds instead of raising, and is checked before the
    evidence.** `RatioEvaluator` and `MatrixEvaluator` (no `PolicyProfile` in context) and
    `NaturalLanguageEvaluator` and `ProcedureEvaluator` (no `ReasoningAgent`) now return
    `INDETERMINATE` / `POLICY_NOT_ACTIVATED` with the reason under `NOT_ACTIVATED_INPUT_KEY`,
    the contract `PythonEvaluator` already had for a missing executor. They share one helper.
    - Why both halves: missing evidence excuses a rule, so asking for the dependency after the
      reads let a case with a missing field silently pass a rule this deployment could never
      run. Asking first while still raising would instead crash every case, since
      `check_compliance` does not catch evaluator raises. Withholding is the governed answer.
    - Behavior change: `check_compliance({}, {})` on a ratio or matrix rule with no profile used
      to allow (the fields were missing) and now withholds the allow. A consumer that relied on
      the old `ValueError` for a missing profile or agent now gets the outcome instead.
    - Authoring errors still raise: a `RatioCondition.threshold` that is not `profile:<key>`, a
      malformed matrix `table`, a half-set `compare_field`/`direction`.
    - The first attempt at this round reordered the two agent checks but kept the raise; the
      follow-up review caught that it turned a silent allow into an uncaught exception.
  - **`create_policy_extract_router(before_write=...)` accepts an async hook.** It is awaited
    through `call_maybe_async`, as `tenant_of` already was. An async hook used to be called and
    its coroutine dropped, so its refusal never happened.
  - **Opening a Plato draft `from_version` tells a missing version from an unreachable store.**
    `PackNotFound` is a 404; any other `materialize` failure is a 503, where before every failure
    was a 404 and a blob-store outage read as "that version does not exist". The activate route
    already made this split.
  - `DbPackDraftStore.delete_file` stamps the draft's `updated_at` and author only when a file
    was deleted. A delete of a missing path used to record an edit that changed nothing.
  - **Round 3.**
    - **`check_python_rule` closes the module-reach class, not one shape of it.** The bot's
      `__builtins__['exec']` report was one instance; the adversarial review then found five more
      over four rounds (an aliased `from fractions import __builtins__`, `from fractions import
      sys`, `import re._parser` binding `re`, `m = fractions; m.sys`, a nested re-import winning
      last), each defeating the previous patch. The gate now enforces one rule set:
      - imports sit at the rule's top level, name an allowlisted module exactly (no submodules),
        bind each name once, and never use `*`;
      - a name bound by `import` is used only as `module.attr`, and `attr` must not itself be a
        module (checked against the real module, so `fractions.sys` is refused and
        `fractions.Fraction` is not);
      - `from <allowed> import <name>` refuses a module-valued or dunder `name`;
      - any bare dunder name is refused, alongside the existing dunder-attribute rule.
      - Behavior change: a rule that imports inside `check()` is now refused. The policy-code
        prompt says so ("once each and at the top of the source, used as module.name").
      - The module still says it is a gate, not a sandbox; the executor is the isolation
        boundary.
    - `DbProposalCommentStore.add` (author, body) and both `DbPackDraftStore` write paths
      (`open`'s seed and `write_file`) strip the real NUL byte and real lone surrogates through a
      new `jazzx_sdk.safety.sanitize.strip_unstorable_chars`. Postgres text rejects the first and
      UTF-8 encoding the second, which surfaced as a 500. Unlike `sanitize_text`/`strip_nulls`, it
      leaves the escaped-literal text (a backslash-u-0000 sequence) alone: in a draft that is
      rule source or YAML, and stripping it rewrote the file silently. Draft files carry merged
      model-written rule text, so the draft store had the same exposure as the comment store the
      bot named.
    - `merge_rules_into_draft` turns a YAML syntax error in the draft's policy file or manifest
      into a `ValueError` naming the file, which the merge route already answers with a 409
      instead of a 500.
    - `create_policy_extract_router` names an oversized upload by its sanitized basename in the
      413, not the raw client-supplied filename.
    - `PolicyExtractionService.submit` refuses with `ExtractionBusy` (a 503 at the route) when all
      `MAX_RUNS` slots hold runs that are still running. Only finished runs were ever evicted, so
      sustained concurrent submits grew the registry without bound. The route asks
      `has_room()` (side-effect free) before reading or converting any upload, so a saturated
      service refuses cheaply; eviction happens only when a run is actually admitted.
    - Declined, with reasons:
      - `_split_batchable` letting `get_condition_evaluator`'s `KeyError` escape for an
        unregistered kind. That lookup fails loudly by design (its docstring says so), a condition
        kind is a closed discriminated union whose every member registers at import, and the
        segment fails as a unit into `failed_segments` rather than crashing adjudication.
      - `DbProposalCommentStore` using `db.register_metadata`: `DbStore.register_metadata` exists
        (`jazzx_sdk/fabric/db/store.py`).
      - `Policy.model_validate` needing a `ValidationError` catch: pydantic v2's
        `ValidationError` subclasses `ValueError`, so the route's `except ValueError` already
        answers 409. A test now pins that.
  - **Round 4.** `import_jtbdset` takes a rule's priority from `sequence` only when it is a whole
    number (`4`, `"4"`, `4.0`); anything else (`"N/A"`, `"1.5"`, NaN) leaves `Rule`'s default
    rather than aborting the whole import with a `ValueError`. The raw `sequence` stays in the
    rule's metadata. The bare `100` default at the call site is gone: `Rule` owns it. Declined
    in the same round: `DbPackDraftStore` using `register_metadata`, which exists.
  - **Round 5.** A batched LLM rule missing a field it reads is EVIDENCE_MISSING before the batch,
    as `NaturalLanguageEvaluator`/`ProcedureEvaluator.evaluate` answer on a single call. Before,
    `_split_batchable` sent it to the model with `field: None` in its evidence, so the same case
    could be excused singly and violated in a batch. The check is one helper,
    `condition_evaluator.missing_evidence`, now used by the natural-language, procedure and Python
    evaluators and by the splitter. Declined in the same round: `vocabulary_review` "not importing"
    `CallerIdentity`, which the router factory imports and its handlers close over.
  - **Round 6.**
    - `check_rel_path` returns the normalized path (`a//b`, `./a/b` and `a/./b` are `a/b`), so one
      file spelled two ways is one draft row on every read, write and delete.
    - `check_python_rule` refuses async anywhere in a rule: `async def`, `await`, `async for`,
      `async with` and async comprehensions. A nested coroutine is never what a synchronous
      check means.
    - `merge_rules_into_draft` refuses a `policies:` that is not a list of mappings, a falsy `{}`
      included, with a `ValueError` naming the file (409 at the route) instead of an
      `AttributeError` (500).
    - Declined: exempting names imported from allowed modules from the forbidden-builtin check
      (`from re import compile`). Tried and reverted in the same round: `del` or `global` on the
      imported name brings the builtin back, so a forbidden builtin name is refused whatever binds
      it; `import re` + `re.compile` is the supported form. Also declined: a procedure answer in
      the wrong batch field being "silently dropped"; it is excluded from the vote and a rule no
      replica answered is CONDITION_UNEVALUABLE with a reason.
  - **Round 7.** A malformed `programs:` entry is a lint finding, not a crash. `programs: {p: 1.5}`
    used to raise `TypeError` out of `Pack.overlay_map`, which `lint_pack` turned into a 500. Now
    `PackManifestLoader.programs()` leaves out a value that is not a policy id or a list of ids
    (whole numbers count as ids and are stringified; booleans and floats do not), and the new
    `malformed_programs()` names each one by manifest path (`programs`, `programs/<id>`), which
    lint reports as `malformed_program`. The bot suggested dropping bad entries silently; that
    would have left a program applying nothing with no signal.
  - **Round 8 (declined, pinned).** The bot asked that a `suppresses` directive always cut a rule's
    replacement chain, even when a higher-precedence policy had already replaced that rule. That
    would let a lower-precedence suppression undo a higher-precedence replacement. Behaviour is
    unchanged: the first directive by precedence sets how a rule is superseded.
    `test_replacing_and_suppressing_one_rule_is_decided_by_precedence` pins both orders, and a
    comment at the suppression merge says so.
  - **Round 9: a full adversarial review of the PR range (`origin/main..dev`), with the bot's round.**
    The per-commit reviews only saw each fix, so v2.5.4 code nobody had touched kept surfacing a
    few findings per bot push. One review of all 172 files found these, fixed together:
    - **Authoring reads are withheld where pack-draft reads are.** In a strict posture without an
      auth dependency or required identity, every GET under the authoring extract and review
      routers is a 403 (an include-level dependency, so extraction runs are covered too).
      Proposals carry verbatim policy text. A deployed tier cannot start without
      `require_identity`, so this is the strict-but-not-deployed posture. On v2.5.5 the same gate
      covers Plato's eval and feedback routers (their `_tenant` refuses a GET there too, and
      `create_eval_router`/`create_feedback_router` take `identity_required`): feedback carries
      what users wrote and the turn it was about.
    - **Every publish obeys the upload size cap.** The check moved into `_publish_archive`, so a
      draft publish over `PLATO_PACK_UPLOAD_MAX_BYTES` is a 413, as the upload of that archive is.
    - **`check_rel_path` refuses `.`, `./` and `./.`**, which name no file and published a
      version that could never materialize.
    - **`DbPackDraftStore.write_file` and `delete_file` lock the draft row** (`blocking_locked_first`)
      before counting or deleting, in one order, so concurrent writes cannot pass the
      `MAX_DRAFT_FILES` check together.
    - **Model overlays are validated in the SDK store.** `put_pricing`/`put_card` raise
      `ValueError` for a payload `build_overlay` rejects; the Plato route maps it to 422 and no
      longer validates separately.
    - **Python rules:** `ctx` may appear only as `ctx[key]` or `ctx.get(key)` (so `dict(ctx)`,
      `{**ctx}` and `g = ctx.get` are refused, which had made every field reachable), and a
      dunder `as` name in `from ... import` is refused at the import.
    - **Two uploads with one name are a 422** before a run starts, not a run that fails.
    - **The unpack cache's marker** (now `store_db.UNPACK_MARKER`) is not offered as a draft file
      when a draft is opened from a published version.
    - **A withheld rule's warning reads "rule withheld --"**, since an unevaluable condition lands
      there too; the `RULE_NOT_ACTIVATED` reason code is unchanged.
    - The example adjudication harness collapses on the verdict, not the pack's status words.
    - Prose: stale `net_safety`/`path_safety` names, a stale field-precedence sentence in
      `segment.py`, a tautological guard in `check_compliance`, em-dashes in the sample-pack
      README and the packs page, the seed overlay's "matches core" descriptions, and `Author:`
      lines on the five `safety/`/`ui` modules that lacked them.
    - Tests: the output-type sweep resolves from the file, not the cwd, and asserts it checked
      something; the not-activated assertions read the reason, not the prefix; a literal refusal
      key uses `NOT_ACTIVATED_INPUT_KEY`.
    - Deferred: `TODO(draft-merge-lost-update)`, a merge's read-then-write with no compare-and-set
      on the draft file.
    - Declined: the bot's gate-evaluator try/except on a superseded rule (evaluators raise only
      on authoring errors, unguarded on the main path too, by design); `Policy(...)` outside the
      merge route's try (the request model types `policy_type` and `scope`, so FastAPI answers
      422 first); the Plato 0.1.6 version note (requested).
  - Not a defect: the review flagged `DbProposalStore`'s table rename (`vocabulary_proposal` to
    `proposal`) as orphaning rows. No Plato migration ever created `vocabulary_proposal` and no
    sibling repo constructs a `DbProposalStore`, so there were no rows to orphan.

- **Feedback, review round 1.**
  - **`feedback_id` is per tenant.**
    - `japes_feedback` is keyed `(tenant_id, feedback_id)`, in migration `0010`, edited in
      place since it never left this branch.
    - Before, a caller-chosen id another tenant already used failed with a 500, which also
      revealed that the id existed.
  - **Every mutation reads under a row lock** (`fabric.db.locking.blocking_locked_first`) and
    writes in the same transaction.
    - This covers `edit`, `set_review_status`, `delete`, `mark_duplicate` and
      `update_processing`.
    - A concurrent change is waited for rather than overwritten by a whole-record write.
  - **Processing opens review but never overrules it.** `update_processing` applies
    `review_status` only while the record is still `pending_review`. A reviewer who approved
    during a moderation call used to have the approval reverted to `under_review`.
  - **A backlog drains oldest first.** `FeedbackQuery.oldest_first`; `process_pending` used to
    take the newest of each status, so a steady stream of new submissions starved the oldest.
    Queries break `created_at` ties by id.
  - **Edits are checked and processed like submissions.**
    - `PUT /feedback/{id}` checks the category against the entity's config.
    - A text or category change is processed again in the background.
    - A metadata-only edit keeps both statuses, since metadata is not reviewed.
    - An edit that changes nothing returns the record untouched.
  - **Duplicates cannot point at duplicates.** Marking against a record that is itself a
    duplicate is refused, naming its canonical record. Two records could otherwise mark each
    other and both drop out of learning.
  - **Status filters are validated.** `FeedbackQuery` and the list, export and aggregate
    parameters type `review_status` and `processing_status`, so a typo is a 422 rather than an
    empty result.
  - **Context for processing, honestly.** An assistant keeps history only when it is built with a
    conversation store, and Plato's wirings pass none.
    - `AssistantFeedbackContext` reads the history when there is one, and otherwise the turn
      the submission carried in `metadata["turn"]` (`TURN_METADATA_KEY`): messages or text.
    - A missing assistant now means no context rather than a `failed` record.
    - `docs/ARCHITECTURE.md` no longer claims the conversation is always used.
  - Export and aggregate fix their window at the first page (`until`), so an insert mid-export
    cannot shift pages.
  - Knowledge Hub collection names carry a digest of the exact tenant, type and id, so
    `loan chat` and `loan-chat` no longer share one.
  - A retrieval test computes its expected counts from `MAX_FEEDBACK_PAGE`.
  - Round 2:
    - `FeedbackQuery.since` and `until` are read as UTC when naive, for every route and
      repository. A naive `until` compared with an aware "now" raised in export and aggregate,
      giving aggregate a 500 and export a 200 with a truncated body. A naive bound sent to
      Postgres would also have been read in the host's zone.
    - `mark_duplicate` locks both records, in id order, and checks the target under its lock,
      so two opposite marks made at once cannot both pass.

- **Semantic feedback retrieval through `fabric.rag`.** Seventh step of hosting feedback.
  Knowledge Hub embeds and searches, so the SDK has no embedding layer of its own.

  - `evaluation.feedback_index.RagFeedbackIndex(rag, tenant_id)` indexes approved, live,
    non-duplicate feedback as one KH document per record, in a collection per tenant and entity
    (`collection_name`). KH search has no metadata filter, so the collection is the scope.
  - `sync(record)` is the one rule: it removes the record's documents (found by `feedback_id`
    metadata) and adds one back only if the record still qualifies. `search` returns
    `(feedback_id, score)` pairs. `FeedbackIndex` is the protocol.
  - `similar_feedback(index=, mode="auto"|"lexical"|"semantic")`: `auto` is semantic when an
    index is given, else lexical.
    - Semantic results are thresholded at the entity's `similarity_threshold`, and `min_score`
      if higher.
    - It over-fetches `SEMANTIC_OVERFETCH` times, then re-checks each record, because the index
      can trail a review change.
    - `semantic` without an index is a 422 on the route.
  - `create_feedback_router(index_for=)`: review, edit, delete and duplicate changes are synced
    to the index. A failed sync is logged, not raised, since the record did change and its next
    change syncs again. `SimilarRequest.mode` selects the mode.
  - `RAGStore.collection_id(name, create=)` is new: a collection's id by name, optionally
    creating it.
  - Plato passes the client layer's `fabric.rag` when it has a fabric, and indexes per tenant.
    A fabric that will not build is logged and retrieval stays lexical, so Knowledge Hub cannot
    stop Plato starting.
  - Em-dashes removed from `fabric/rag/store.py`.
  - Not covered: an approved record whose summaries arrive after approval is indexed with its
    text alone until its next change.

- **Feedback into learning.** Sixth step of hosting feedback.

  - `evaluation.feedback_learning.add_feedback_case(datasets, dataset_id, record, input=,
    expected=)` adds a feedback record to a dataset as a case in the next version.
    - The caller supplies input and expected output: feedback says what was wrong, not what
      right looks like.
    - The case id is `feedback-<feedback_id>`, so a second add returns the dataset unchanged.
    - The case carries the feedback's category as a tag, and its ids as metadata.
    - `feedback_case` builds the case alone.
  - `POST /feedback/{id}/to-dataset {dataset_id, input, expected}` on the feedback router when a
    host passes `datasets_for=`. Plato does, against the tenant's eval datasets.
  - `OptimizationSpec.include_feedback` gives an optimization the entity's newest approved,
    non-duplicate feedback (`FEEDBACK_FOR_OPTIMIZATION`), snapshotted on the job as
    `OptimizationJob.feedback`. It steers the proposer through `optimize_prompt(feedback=)`.
    `synthesize_feedback_cases` also turns it into training cases.
  - `OptimizationRunner(feedback=)` is the repository it reads; creation refuses when
    feedback is asked for and none is wired. Plato wires its feedback store.
  - A seed failure on a synthesized case is named `synthetic #n`, since those cases follow the
    dataset's own.

- **Reading feedback back: similar, export, aggregate.** Fifth step of hosting feedback.

  - `evaluation.feedback_retrieval.similar_feedback(repository, configs, entity=, text=,
    top_n=, min_score=)` returns an entity's approved, non-duplicate feedback most like a text,
    best first, as `ScoredFeedback`. `top_n` defaults to the entity's configured `max_results`.
  - Scoring is lexical, so it works on sqlite and Postgres alike. `lexical_similarity` is shared
    terms over the smaller term set, which lets a short feedback item fully contained in a long
    turn score 1. Terms shorter than `MIN_TERM_LENGTH` and common `STOPWORDS` are left out, so
    unrelated texts do not match on "the" and "for". Only the newest `MAX_FEEDBACK_PAGE`
    approved records are scored.
  - The config's `similarity_threshold` is for semantic retrieval (step 7), since word overlap
    and cosine similarity are different scales. Lexical retrieval takes `min_score`.
  - `iter_feedback` pages through every matching record up to `EXPORT_MAX_ROWS`.
    `aggregate_feedback(query, group_by)` counts records by review or processing status,
    source, reaction, category, entity, day or ISO week.
  - Routes on the feedback router:
    - `POST /feedback/similar`.
    - `GET /feedback/export?format=csv|ndjson`, streamed; CSV columns are `EXPORT_COLUMNS`.
    - `GET /feedback/aggregate?group_by=`.
    - List, export and aggregate share one set of filter query parameters.

- **Plato hosts feedback.** Fourth step: the SDK's feedback routes for Plato's own assistants.

  - `/api/v1/feedback/...` and `/api/v1/feedback-config/...` (`plato/api/feedback.py`), per
    tenant, whenever Plato has a database. Writes are refused unauthenticated in a strict
    posture, like authoring and eval. A submission carries the governed trace id when its body
    has none.
  - Each new submission is processed in the background with the assistants' own LLM, so the
    local wiring stays keyless. `POST .../feedback/{id}/process` runs it again, from the start
    for a failed record. Without an LLM, feedback is stored and reviewed but not processed.
  - Context for the summary comes from `server.feedback_api.AssistantFeedbackContext`: the last
    `CONTEXT_MESSAGES` messages of the conversation the record names, read through the new
    `InteractiveAgent.history(session_id)`. It returns nothing for other entity types, a
    missing conversation, or an agent that keeps no history.
  - The SDK router takes `processor_for=`: it processes new submissions in the background and
    mounts `.../process`.
  - `job:feedback-process` (`plato.jobs.FEEDBACK_PROCESS_ROLE`) processes every tenant's
    unfinished feedback. It exits 3 without a database or an LLM, and warns over no tenants.
  - Migration `0010_feedback`: `japes_feedback`, `japes_feedback_history`,
    `japes_feedback_config`. Checked against the models with `compare_metadata`.
  - **Plato's "no feedback table" rule is retired.** Its test now asserts that no Plato table
    takes eval-service's `feedback` name, and that `japes_feedback` exists. The eval-service
    pass-through router is removed; no shipped wiring mounted it. Its sink tests move to
    `tests/test_eval_service_feedback_submission.py`.
  - Docs: `docs/ARCHITECTURE.md` gains the feedback paragraph and one-writer wording, and
    `plato/guide.md` the feedback routes and job.

- **Feedback processing.** Third step of hosting feedback.

  - `evaluation.feedback_processing.FeedbackProcessor(repository=, configs=, llm=, context=)`
    runs three stages, each moving `processing_status`, so a stopped run resumes where it left
    off:
    1. **validate**: moderation flags (toxic, spam, pii, low_quality) through the LLM, and
       `potential_duplicate` when the entity has feedback from the last 30 days with word
       overlap of at least `DUPLICATE_TEXT_OVERLAP`. Flags are tags for a reviewer, never a
       rejection. Review moves from `pending_review` to `under_review`, recorded in history as
       `PROCESSOR_ACTOR`.
    2. **summarize**: a summary of the turn when the host's `FeedbackContextProvider` supplies
       its text, and an overall summary of the feedback.
    3. **enrich**: `assess_feedback_quality` and `extract_actionable_items` when quality is
       enabled. This stage is best-effort: its failure is logged and the record still completes.
  - A failure in stage 1 or 2 marks the record `failed` with the reason.
  - `process_pending(limit=)` works through unfinished records, oldest first, for a job.
  - Prompts come from the entity's config when set, else `DEFAULT_CONTEXT_SUMMARY_PROMPT` and
    `DEFAULT_OVERALL_SUMMARY_PROMPT`. They are filled by plain replacement (`fill`), so an
    operator's prompt may contain other braces. Every LLM call uses the config's
    `summary_model`.
  - `FeedbackRepository.update_processing(feedback_id, revision=, changes=)` writes results
    against the revision processing started from. An edit made meanwhile wins and the stale
    results are dropped (`None`). Only `PROCESSING_FIELDS` may be written.
  - `FeedbackRecord.quality` is a `FeedbackQuality` and `actionable_items` a list of
    `ActionableItem`, the types the quality functions return (they were a dict and a string).
  - `FeedbackConfig.quality_metrics` is removed. Nothing read it, and the quality check scores
    useful, actionable and specific rather than a configurable metric list.

- **Feedback config per entity, with a tenant default.** Second step of hosting feedback.

  - `evaluation.feedback_config.FeedbackConfig`: summary model, moderation on/off, context and
    overall summary prompts (None uses the pipeline's own), quality on/off and metrics, allowed
    categories, similarity threshold and max results (`DEFAULT_SIMILARITY_THRESHOLD`,
    `DEFAULT_MAX_RESULTS`).
  - `FeedbackConfigStore.resolve(entity)` returns the entity's own config, else the tenant
    default, else the built-in, with its `source`. An entity config replaces the default whole
    rather than merging, so what an operator reads for an entity is what applies.
  - `put(base_revision=)`: `None` creates; otherwise it names the revision it replaces.
    `FeedbackConfigConflict` when stale. `DbFeedbackConfigStore` writes table
    `japes_feedback_config`, keyed by tenant and scope.
  - `create_feedback_router(configs= | configs_for=)` mounts `/feedback-config` (resolved, with
    `?entity_type&entity_id`), `/feedback-config/stored`, and `GET`/`PUT`/`DELETE` on
    `/feedback-config/default` and `/feedback-config/{entity_type}/{entity_id}`. `PUT` needs
    `If-Match` to replace a stored config (428/409).
  - With a config store, a submission whose category is not in its entity's allowed list is
    refused (422). Feedback with no category is always accepted, since positive feedback usually
    carries none.

- **Feedback records with a review lifecycle.** First step of hosting feedback in the SDK.

  - `evaluation.feedback_records`: `FeedbackRecord` wraps a submitted `Feedback` with the entity
    it is about, a `processing_status` (unprocessed through processed, failed, skipped) and a
    `review_status` (`pending_review`, `under_review`, `approved`, `rejected`), processor output
    fields, a duplicate link, soft delete and a `revision`. `FeedbackRepository` is the store
    protocol:
    - `create` is idempotent on `feedback_id`: a retry returns the stored record.
    - `query(FeedbackQuery)` filters by entity, statuses, source, category, turn refs, text
      substring, time range, deleted and duplicate rows, capped at `MAX_FEEDBACK_PAGE`.
    - `edit(base_revision=)` resets both statuses (what was reviewed is no longer what is
      there) and records old and new values. A stale revision raises `FeedbackConflict`.
    - `set_review_status`, soft `delete`, `mark_duplicate` / `duplicates_of`, and `history` of
      every review change, edit, duplicate mark and delete.
  - `parse_reaction` accepts `Reaction` values and the thumbs spellings UIs send.
  - `DbFeedbackStore` implements both `FeedbackStore` (`append` / `list` / `clear`, unchanged
    for callers) and `FeedbackRepository`.
    - `japes_feedback` grows tenant, entity, category, text, both statuses, duplicate, delete
      and revision columns beside the JSON record. `japes_feedback_history` is new.
    - The store is tenant-scoped at construction (`tenant_id=`, default `DEFAULT_TENANT`).
    - `append` is now idempotent rather than raising on a repeated id.
    - The ORM class is `FeedbackRow`; `FeedbackRecord` is the model.
    - An edit's revision check repeats in the UPDATE, so a lost race is a conflict.
  - `server.feedback_api.create_feedback_router(repository | repository_for=, prefix=, auth=,
    trace_id_for=)`:
    - `POST /feedback` answers 201 new or 200 for a retry, and fills a missing `trace_id` from
      the request.
    - List with every filter; get; `PUT` gated on `If-Match` (428/409); `PATCH .../review`;
      soft `DELETE`.
    - `.../history`, `.../duplicates`, `POST`/`DELETE .../duplicate`.
    - Writes without auth fail closed in a deployed posture.
  - `feedback.py` and `feedback_sink.py` docstrings state the current boundary: a host stores
    feedback for the entities it owns, and eval-service keeps its own. The sink's docstring no
    longer names a gitignored plan file. Em-dashes removed from `feedback.py`.

- **Evaluation datasets: versioned case sets with a store and HTTP routes.** First step of moving
  eval-service's control plane into the SDK so Plato and eval-service can both be thin hosts.

  - `evaluation.datasets`: `DatasetStore` over named datasets of `GoldenCase`s. Each version is
    immutable and carries a content digest (`dataset_digest`, order-independent), its parent, and
    a change summary from `diff_case_sets`. `revise(..., base_version=)` opens the next version
    and raises `DatasetConflict` when the base is stale; identical cases open nothing. `fork`
    copies a version into a new dataset and records its origin, which is also how a dataset moves
    to a different entity. Status is `draft`, `published` or `archived`; names are unique per
    tenant; a version holds at most `MAX_DATASET_CASES`; duplicate `case_id`s are refused.
  - `DbDatasetStore` on `fabric.db`, tenant-scoped at construction, tables `eval_dataset` and
    `eval_dataset_version`. A unique `(dataset_id, version)` turns a lost revision race into
    `DatasetConflict` rather than a second copy of one version. Exported lazily from
    `jazzx_sdk.evaluation`.
  - `server.eval_api.create_datasets_router(store | store_for=, prefix="/eval", auth=)`: list
    (by status or entity), create, get (any version), versions, `PUT .../cases` gated on
    `If-Match` through `check_if_match` (428 without it, 409 when stale), `PATCH` for name,
    description, tags and status, and fork. Responses carry the latest version as `ETag`. Writes
    without `auth` fail closed in a deployed posture. Not yet mounted in Plato.
- **Evaluation experiments: a dataset version, run against an entity, scored by a template.**
  Second step of the eval control plane.

  - `evaluation.experiments`: `Experiment` snapshots what decides its result at creation (dataset
    id, version and digest, the entity, the `EvalTemplate`, the invoker config), so two
    experiments with equal snapshots are comparable. `ExperimentSpec` is what a caller submits;
    `ExperimentRunner.create` resolves it, taking the dataset's latest version and bound entity
    when none is given, and refuses a template naming a scorer the registry lacks.
  - `Invoker` is the host's seam: `invoke(entity, case, config=) -> Invocation(output, trace_id,
    trace)`. `trace` reaches scorers as `context["trace"]` (the operational scorers read it) and
    is not stored. Scorers also get `context["input"]` and `context["case_id"]`.
  - `ExperimentRunner.start` claims and launches a background task; `run` claims and executes in
    the caller's task, for a job or a worker; `execute` runs every case not yet completed with
    `concurrency` at once (`DEFAULT_CASE_CONCURRENCY`), so restarting a failed experiment
    resumes it. A case whose invocation or scoring raises is recorded as a failed `CaseRun` and
    the rest continue; anything that stops the experiment marks it `failed` with the reason.
    `rerun` creates a new pending experiment from the same snapshot, linked by
    `source_experiment_id`.
  - `ExperimentSummary`: pass rate over all cases (failed invocations count against it), mean
    score over scored cases, and per-scorer mean score and pass rate keyed by `ScorerSpec` key.
  - `DbEvalExperimentStore` on `fabric.db`, tables `eval_experiment` and `eval_case_run`, the
    full model as JSON beside the filtered columns. `claim` is a conditional UPDATE on status, so
    one of two concurrent starts wins. Named `EvalExperimentStore` because `ExperimentStore` is
    already the MLflow run-record store.
  - `server.eval_api.create_experiments_router(runner | runner_for=, templates=, prefix=, auth=)`:
    list (by dataset, status, entity), create with an inline template or a `template_name` from
    the host's `EvalTemplateRegistry`, get, case runs, `POST .../start` (202; 409 unless pending
    or failed), `POST .../rerun`. The datasets and experiments routers share the entity filter
    and the deployed-posture write guard.
  - Not yet: nothing reclaims an experiment left `running` by a process that died; a host's job
    role owns that until Plato wires one.

- **Custom scorers and a scorer catalog.** Third step of the eval control plane.

  - `evaluation.custom_scorers`: `CustomScorerDefinition` is a scorer as data. `natural_language`
    holds guidelines graded by `LLMJudgeScorer`; braces in the guidelines reach the judge
    literally. `python` holds a script defining `score(case)` over `input`, `expected`, `actual`
    and `context`. It is checked on save by the policy rules' `check_python_rule` (allowlisted
    imports, no forbidden builtins, reads only those four keys) and runs only through the
    `PythonExecutor` protocol the policy rules already use, never in process. It may return a
    number in [0, 1], a bool, or `{"score", "passed", "comment"}`. Each kind refuses the other's
    body. Guidelines and scripts are bounded by `MAX_GUIDELINES_CHARS` and `MAX_SCRIPT_CHARS`.
  - Revisions are immutable; a scorer's name and kind are fixed at creation.
    `CustomScorerStore.revise(..., base_revision=)` raises `CustomScorerConflict` when stale.
    Archiving stops new pins, and revisions already pinned still resolve.
  - `ScorerCatalog(scorers, custom=, llm=, python_executor=)`: a host's built-in `ScorerRegistry`
    plus one tenant's custom scorers. A template names one as `custom:<name>` or
    `custom:<name>@<revision>`. `pin` rewrites bare references to the latest active revision,
    keeping the result key unpinned so summaries group across revisions. `build_template`
    resolves a template into its composite, raising `ValueError` for anything that does not
    resolve, including a kind whose LLM or executor the catalog lacks. `describe` lists
    built-ins, then active custom scorers.
  - `ExperimentRunner(scorers=)` takes a `ScorerRegistry` or a `ScorerCatalog`. `create` pins
    the template before storing it, so an experiment keeps scoring with the revision it was
    created against.
  - `DbCustomScorerStore` on `fabric.db`, tables `eval_custom_scorer` and
    `eval_custom_scorer_revision`.
  - `server.eval_api.create_scorers_router(catalog | catalog_for=, templates=, prefix=, auth=)`:
    - `GET /eval/scorers` lists the catalog; `POST /eval/scorers/score` scores one case, guarded
      like a write because it runs a judge or a script (502 when the scorer itself fails).
    - `GET /eval/templates` and `GET /eval/templates/{name}`.
    - Custom scorers: list, with `include_archived`; create; get any revision; list revisions;
      `PUT` gated on `If-Match`; archive and restore. These answer 404 when the catalog has no
      store.
  - Not built: the agent-judge kind (scorers bound as tools to an `InteractiveAgent`), until a
    real use needs it.

- **Plato hosts evaluation.** Fourth step of the eval control plane: the SDK's eval routers,
  mounted for Plato's own assistants.

  - `/api/v1/eval/datasets`, `/eval/experiments`, `/eval/scorers`, `/eval/templates` and
    `/eval/custom-scorers` (`plato/api/eval.py`). They are mounted whenever Plato has a database
    and use per-tenant stores, like the packs and authoring routes. Writes are refused
    unauthenticated in a strict posture, through the same `withholding` gate authoring uses.
  - The built-in scorers are `evaluation.standard_scorers(llm)`: `exact_match`,
    `within_tolerance`, `set_coverage`, `jaccard_overlap`, and `llm_judge` when there is an LLM.
    The LLM is the one the assistants are wired with, now readable as `AssistantRuntime.llm`, so
    the local wiring's judge is scripted and keyless.
  - `server.eval_api.AssistantInvoker(runtime, tenant_id)` runs a case as one turn against an
    `AssistantRuntime` assistant:
    - The input is `{"messages": [...]}`, `{"query": "..."}` or a bare string. The scope comes
      from `input["scope"]` merged with `config["scope"]`, and the config wins.
    - Each case gets its own conversation.
    - The output is the structured result when there is one, else the answer text.
    - A turn with an `error_code`, or an entity that is not an assistant, fails the case.
    - Bound to the request's tenant, so another tenant's assistant id resolves to nothing.
  - One `ExperimentRunner` per tenant for the life of the process, so the background task a
    started experiment runs on stays referenced.
  - `job:eval-reclaim` (`plato.jobs.EVAL_RECLAIM_ROLE`) fails experiments that have finished no
    case for `DEFAULT_EVAL_IDLE_SECONDS`, across every tenant. Restarting one resumes it. The job
    exits 3 when the wiring has no database, as `job:migrate` does.
  - This rests on `EvalExperimentStore.reclaim_stale(idle_since=)`, with `heartbeat_at` moving on
    claim and on every case run. The update is conditional on the heartbeat it read, so an
    experiment that made progress in between is left running.
  - Migration `0007_eval` creates the six `eval_*` tables. Checked against the models with
    alembic's `compare_metadata` as well as the suite's table and column tests. Plato still has
    no feedback table.
  - Docs:
    - `docs/ARCHITECTURE.md` gains the eval hosting decision and the one-writer rule.
    - `plato/guide.md` gains the eval routes and the list of job roles.
    - The README diagram now shows `job:*` and `eval`.

- **Experiment comparison and baselines.** Fifth step of the eval control plane.

  - `evaluation.experiment_comparison.compare_experiments(baseline, runs, candidate, runs)` pairs
    two completed experiments' case runs by `case_id`.
    - Each case is `improved`, `regressed` or `unchanged` on score; `unscored` when either side
      failed; or `only_baseline` / `only_candidate`.
    - Each case also carries a `flip` when its pass verdict changed: `fixed` or `broke`. This is
      what a mean hides.
    - `ExperimentComparison` carries the counts, `match_rate` over scored pairs, and pass-rate
      and mean-score deltas overall and per scorer key.
    - `same_case_set` says whether both ran the same dataset digest. Pairing holds either way.
  - `check_ab_bars` now gates an `ExperimentComparison` as well as an `ABResult`, through a
    `metrics()` both provide. A promotion gate can be `PassBar(metric="broke", maximum=0)` or the
    default `match_rate >= 0.95`. It uses the same vocabulary as `guidance_ab` rather than a
    second one.
  - Baselines, one per entity: `EvalExperimentStore.set_baseline` / `get_baseline`, table
    `eval_baseline`. `ExperimentRunner.set_baseline(experiment_id)` accepts only a completed
    experiment. `ExperimentRunner.compare(candidate_id, baseline_id=None)` compares against the
    entity's baseline when none is named.
  - Routes on the experiments router:
    - `GET /eval/experiments/{id}/compare?baseline=` (404 with no baseline; 409 unless both
      completed).
    - `POST /eval/experiments/{id}/baseline`.
    - `GET /eval/baselines/{entity_type}/{entity_id}`.
  - Plato migration `0008_eval_baseline`. The guide and `docs/ARCHITECTURE.md` mention
    comparison.
  - `guidance_ab`'s prose is cut to what is true now: the module docstring loses its phase
    history, `validate_guidance` its note about an earlier extraction, and `compare_manifests` a
    comment claiming the manifest version hash was duplicated (it calls the same
    `content_version`). Its em-dashes are gone.
- **Prompt optimization as a job.** Sixth step of the eval control plane.

  - `evaluation.optimization_jobs`:
    - `OptimizationRunner.start(spec)` snapshots the dataset version and digest, the pinned
      template and an `OptimizationConfig`, then runs `optimize_prompt` in the background.
    - The seed defaults to the target's current prompt.
    - Each scored candidate is saved as it arrives, so `GET` shows progress. That save is also
      the job's heartbeat.
    - `apply(job_id)` hands the winner to the host and records where it went. It refuses unless
      the job completed with an improvement and has not been applied, so a better score on a
      dataset is evidence and applying it is a separate decision.
    - `create` refuses without an LLM to propose with.
  - `PromptTarget` is the host's seam: `current_prompt`, `predict(entity, inputs, prompt)` and
    `apply`. A case input that is not a mapping arrives as `{"query": input}`.
  - `ReflectiveOptimizer(on_candidate=)` reports each candidate as it is scored, the seed
    first. It is a constructor argument, so the `PromptOptimizer` protocol that client backends
    implement is unchanged.
  - `DbOptimizationJobStore`, table `eval_optimization_job`, with `reclaim_stale`. A reclaimed
    job is failed, not resumed; the search restarts cheaply.
  - The experiment store and this one share `evaluation._reclaim.reclaim_stale_rows` rather than
    two copies of the conditional sweep.
  - `server.eval_api.create_optimizations_router`: start (202), list by entity, get, and
    `POST .../apply` (409 when there is nothing to apply). Template resolution (inline or
    `template_name`) is one `_resolve_template` shared with the experiments router.
  - `server.eval_api.AssistantPromptTarget(runtime, tenant_id, apply=)`: the prompt is the
    assistant's persona. Candidates run through the new
    `AssistantRuntime.agent_with_persona(tenant, assistant, persona)`, which binds the same
    manifest with only the profile's persona swapped and is not cached. The agent for a
    candidate is kept until the next candidate arrives. It shares the turn shaping with
    `AssistantInvoker`, and applying is the host's callable.
  - Plato mounts `/api/v1/eval/optimizations`. Its apply writes the winner into the tenant's
    **pack draft**, at the markdown file `profile/profile.yaml` names as the persona.
    - It refuses when no draft of the assistant's pack is open, or when the profile names no
      persona markdown file (inline or absent). The loader reads only a file the profile names,
      so there is no default path to write.
    - It never publishes: the draft goes through the packs routes like any other authoring
      change.
    - The proposer uses the assistants' own LLM.
  - `job:eval-reclaim` now sweeps optimization jobs as well as experiments
    (`plato.jobs.reclaim_eval_work`). Migration `0009_eval_optimization`.
  - Deviation from the plan: no `PromptRegistry` alias promotion. The job record already keeps
    every candidate, and the pack draft is where Plato's prompts are governed. A second store of
    prompt versions would be a second answer to "which prompt is this assistant on".
- **Eval control plane, review round 1.**
  - **Skipped results are neither scores nor failures.**
    - `summarize` counts a skipped case as passed, as `ScorerResult.skipped` defines, and leaves
      it out of `mean_score`. The new `ExperimentSummary.skipped` counts such cases.
    - A skipped sub-result is left out of `by_scorer`.
    - `compare_experiments` reads a case skipped on either side as `unscored`, not as a score of
      0 that could report `regressed`.
  - **Optimization heartbeat moves on every case.**
    - `OptimizationJobStore.touch` runs before each case, not only when a whole candidate has
      been scored.
    - A seed pass over a large dataset could otherwise outlast `DEFAULT_EVAL_IDLE_SECONDS`, and
      `job:eval-reclaim` failed a live job.
  - **A reclaimed row is not revived by its old process.**
    - `OptimizationJobStore.save` no longer moves a failed row back to running or completed, and
      returns False when it declines.
    - `EvalExperimentStore.finish` keeps the state of an experiment that is no longer running.
    - Before, the status flapped and a user who restarted on the failure ran two searches.
  - **Applying is atomic.**
    - `claim_apply` / `release_apply` on the job store use a new `applied_at` column, in
      migration `0009`. It was edited in place: it had never left this branch.
    - Of two concurrent applies, one applies. An apply whose target raises releases the claim,
      so it can be retried.
  - **A failed case is retried, and a prompt that still cannot be scored does not compete.**
    `optimize_prompt` retries a case whose run or scoring raises (`CASE_RETRIES`, one extra
    attempt). A candidate with a case that still fails is recorded with `score=0.0` and
    `rationale="not scored: ..."`, and never becomes best. A seed that cannot be scored fails
    the run, since there is nothing to improve on.
    - One flaky turn no longer fails a whole optimization job, which was the round-1 finding.
    - A failed case is not averaged in as a real 0, which would make a no-better prompt read as
      `improved` and put it in the pack draft.
  - **A missing assistant is a 404.** `evaluation.EntityNotFound(LookupError)` is the host's "no
    such entity", and `AssistantNotFound` now subclasses it. The optimization routes catch it
    by name, so an unrelated `IndexError` is not reported as a missing entity.
  - **A finish lands only for the run it claimed.** `claim` stamps a fresh
    `Experiment.run_token` (and a `run_token` column, in migration `0007`, edited in place).
    `EvalExperimentStore.finish(..., run_token=)` is one conditional UPDATE on it. A process
    that was reclaimed, then outlived a restart, can no longer write `completed` with a partial
    summary over the new run.
  - **A reclaimed optimization stops.** `execute` returns at once for a job that is not running.
    When a save is declined mid-run, it stops rather than spending the rest of the search on a
    job the store has failed.
  - **A failed save after apply releases the claim**, so the record cannot read "unapplied"
    while refusing a retry as "applied already".
  - Round 3 (passed, two notes, both closed):
    - A candidate that could not be scored has `Candidate.score = None` rather than a 0.0 that
      reads as measured.
    - A seed that fails on a case raises `optimization.CaseFailed` with the case's position,
      and the job's error names the dataset `case_id`. `CaseFailed` is exported from
      `jazzx_sdk.evaluation`; a caller of `optimize_prompt` that caught its pipeline's own
      exception from a seed failure now gets `CaseFailed`, with the original as `__cause__`.
  - **Custom scorer script check moved.** It now runs on save and again before each run, and a
    stored revision loads without it. A tightened `check_python_rule` can no longer stop saved
    revisions being listed or pinned, and still stops them running. Stores pass
    `STORED_CONTEXT_KEY` in the validation context.
  - **Request models extend their specs.** `ExperimentCreate` and `OptimizationCreate` subclass
    `ExperimentSpec` and `OptimizationSpec`, so a default changed on a spec is not shadowed by a
    copy in the router.
  - `job:eval-reclaim` warns when it sweeps no tenants, as `job:session-reaper` does.
  - `identity`'s docstring says "nothing from the SDK is imported at module level":
    `with_trace_context` imports one lazily.

- **One key for a scorer's case input, `SCORER_INPUT_KEY` (`"input"`).**
  - Experiments passed `context["input"]`, while `optimize_prompt` and `run_ab_comparison` passed
    `context["inputs"]`. A Python custom scorer therefore saw no input under optimization.
  - All four sites now use the constant. `"input"` is also what eval-service's judges read.
  - A scorer that read `context["inputs"]` must read `context["input"]`; nothing in japes, jaci
    or jazzx-assistant did.
- `scorers.py` and `optimization.py`: module docstrings cut to the rules they state, without the
  provenance paragraphs, and their em-dashes removed.
- **Plato 0.1.7.** `plato/_version.py`'s docstring is cut to the rule.

- **One UTC coercion, `jazzx_sdk.utc.as_utc`.** It is the rule behind every read of a naive
  timestamp (SQLite hands them back for timezone-aware columns; pack dates arrive naive), and it
  passes `None` through.
  - It replaces private copies in `llm.model_overlay_db`, `manifest.store_db`, `pack.draft_db`,
    `pack.store_db`, `interactive.session_db`, `audit.events_db`, `queue.execution_db` and the
    three eval stores.
  - It also replaces inline coercions in `observability.span_mapping`,
    `fabric.graph.proposal_comments` and `automation.schemas`.
  - `manifest.lifecycle.as_utc` re-exports it, so existing imports keep working. Its docstring had
    listed the copies as available work.
  - `fabric.canonical.policy` and `fabric.guidance.schema` now import it from `jazzx_sdk.utc`
    rather than reaching up into `manifest`.
  - Em-dashes removed from the files this touched.

- **Comments cut to what is true now** in files this change touched:
  - `identity`: the module docstring, `security_context`, the default header provider (now a
    precedence list), `default_request_headers`, `request_headers_allowlist`,
    `with_trace_context`, `KERNEL_HEADER_ALLOWLIST`, `kernel_request_headers` and
    `CallerIdentity`.
  - Two claims were false and are fixed: the security-context comment named
    `_security_context_headers` as `ClientLayer`'s default provider (it is
    `default_request_headers`), and `kernel_request_headers` said `ClientLayer.kernel` uses it
    (`ClientLayer.kernel` builds the same scoping over its own provider).
  - `KernelClient`'s docstring pointed at `jazzx_sdk.handlers.kernel_request_headers`, and
    `server/app.py`'s middleware comment at `handlers._default_request_headers`; both live in
    `identity`.
  - Em-dashes removed from `identity`, `clients/kernel_client`, `server/app` and
    `evaluation/__init__`.

- **`DEFAULT_TENANT` has one definition, `jazzx_sdk.identity.DEFAULT_TENANT`.** Nine stores
  (`pack.store`, `manifest.store_db`, `interactive.session_db`, `audit.events_db`, `runs.store_db`,
  `llm.model_overlay_db`, `fabric.graph.proposal_store_db`, `fabric.graph.proposal_comments`,
  `evaluation.datasets_db`) each declared their own `"default"`, because `pack.store`'s copy sat
  above most of them in the tier contract. `identity` is the bottom tier, so each now imports it;
  the old module-level names still resolve, so `from jazzx_sdk.pack.store import DEFAULT_TENANT`
  keeps working. Plato's wiring and model-overlay router import it from `identity`. The four
  near-identical docstrings that justified the copies are gone, and `parse_pack_reference`'s
  docstring is cut to the rule.

- **Chat pipeline: what a consumer's own stages need.** Third step toward hosting
  jazzx-assistant's turn.

  - `InteractiveResponse.error_code`: a stable code for a failed stage. `default_step_error` sets
    `<step>_failed` (`gate_failed`, `ground_failed`, `answer_failed`, ...). A consumer with its own
    vocabulary (jazz: `gate_error`, `grounding_failed`, `agent_error`) or per-stage wording binds
    a handler that calls `default_step_error` and updates the copy. Empty on the agent's
    max-turns reply, which is what separates a failure from a loop out of turns now that both are
    `incomplete=True`.
  - `GateDecision.verdict` keeps the classifier's typed verdict in `state.emitted["gate"]` for
    later stages and audit; `GateDecision.refusal` is a decline the gate wrote itself, which
    `refuse_step` uses over its configured `decline`.
  - `ChatTurn.metadata`: the caller's per-turn data (effective config, a program tag, ids), which
    japes never reads.
  - `ChatTurn.publish`: while `stream_chat_turn` runs, the sink any stage awaits to put an event
    on the stream; `None` on the blocking path and after the stream ends. A bound `answer` can
    now stream (tool events, reasoning, its own deltas), where before only the reference answer
    could. The generator yields published events unchanged, so its annotation is
    `AsyncGenerator[Any, None]`; a finished run still ends with `InteractiveStreamEvent(done=True)`.
    A stage publishing a `done` event raises (it would reach the consumer ahead of `compose` and
    `persist`, carrying the raw answer), and `chat.ttft_ms` is stamped at the first text delta,
    not the first event of any kind.
  - `structured_classifier_gate` keeps the parsed verdict on every `GateDecision` it returns,
    including a bare route string, `None`, or a mapper's `GateDecision` that set none.
  - A turn that produced no answer carries `error_code="no_answer"`, so it no longer reads as a
    max-turns reply.
  - The module docstring's streaming example skips events that are not `InteractiveStreamEvent`.
  - `run_chat_turn`'s `pipeline=` is optional. Omitted, it is built from the components by the
    new `pipeline_for(components, turn)`, the derivation `stream_chat_turn` already used, so a
    bound `compose`, `ground` or `escalate` gets its stage without a flag. Before, a caller that
    bound `compose` and passed `build_chat_pipeline()` got the branch's raw answer back, compose
    silently skipped. An explicit pipeline still runs as given.
- **Docs: the chat pipeline as a turn engine.** A new `docs/ARCHITECTURE.md` section: stages,
  what a consumer binds at each, the decisions (stages over a hook spec, `InteractiveResponse` as
  the envelope, caller-owned persistence, a sink rather than a transport, cooperative cancel) and a
  worked multi-stage assistant, blocking and streaming, checked by running it against stubs. The
  README's version lines name 2.5.5 in progress, 2.5.4 on `dev` and 2.5.3 as the last release on
  `main`; they had stopped at 2.5.2 and 2.5.1.

- **Chat pipeline: `compose` and `persist` stages, and `build_chat_components(overrides=...)`.**
  Second step toward hosting jazzx-assistant's turn. A consumer whose turn is more than one agent
  call now binds its own stages the way every other japes pipeline does, instead of the spec's
  proposed `ChatSpec` of hooks, `ChatResult` type and persistence-policy enum.

  `compose` is an optional stage (`build_chat_pipeline(with_compose=True)`) after the branches. A
  bound one reads the answering branch's value from `state.emitted` and returns what the user
  reads, as an `InteractiveResponse` carrying any application value on `.output`. It runs on
  every route including refuse, and like `finalize` it is not cancel-guarded, since composing is
  part of delivering an answer that exists. japes ships no reference compose.

  `persist` is a stage (`with_persist=True`, the default) whose reference component,
  `persist_step(agent)`, is the side-branch persistence that used to live inside `finalize_step`:
  escalate and refuse are appended through `agent.persist_turn`, the direct answer is left to
  `respond`. It now records what the user read, composed or not. `finalize_step()` is pure
  resolution and takes no `agent` (breaking for a direct caller of `finalize_step(agent)`; none
  exists outside `chat.py`), which also means overriding `finalize` no longer drops persistence.

  `overrides` merges last and always wins, as in `build_investigation_components`. A `None` value
  unbinds a step and drops its key: `{"persist": None}` is how a caller that owns its
  conversation record (jazz's socket path commits before it delivers) turns japes' writes off.
  `stream_chat_turn` derives `compose` and `persist` from the bound components as it already does
  for `escalate` and `ground`.

  A failing `compose` or `persist` is reported as the failed turn it is: `_final_response` now
  falls back to the *latest* `InteractiveResponse` emitted (the failing step's `on_step_error`
  substitute) rather than the first, which was the branch's own answer and made the failure
  invisible on both entry points.

  Every default pipeline gains a `Persist` stage in its `on_step` events. The catalog's chat
  `steps` and the README pipeline table list `compose` and `persist`.

- **Chat pipeline: the streaming path honours bound components, both paths resolve a turn alike,
  and cancel is checked between stages.** First step of making `pipelines.chat` host
  jazzx-assistant's turn (the `ReasoningEngine` spine).

  `stream_chat_turn` built its pipeline from its kwargs (`escalate is not None`,
  `bool(turn.sources)`), so a caller's `components["escalate"]` was dropped, and so was a
  `components["ground"]` on a turn declaring no `sources`, which is how a consumer grounding
  through one provider looks. It now builds from what is bound. The reference `ground_step` is
  marked (as `answer_step` already was), so it alone is left out for a turn without sources and
  `on_step` sees no empty Ground stage.

  `run_chat_turn` now resolves its result through `_final_response`, the resolver the streaming
  terminal event uses. Turns that returned `None` there now return what streaming returned: a
  cancelled turn with no answer is `cancelled`; otherwise an escalation with no `escalate`
  component declines (`block_reason="escalate_not_configured"`, wording `DEFAULT_DECLINE`), and
  any other turn with no answer is `incomplete`. Cancellation is checked first, on both paths, so
  a turn cancelled during a gate that chose escalation is not reported as a decline. The return
  annotation drops `| None`.

  `ChatTurn.cancel` was documented as checked between stages and was only checked before the
  run and between stream deltas. `chat_guards` now keeps gate, ground, escalate, answer and
  refuse from starting once it is set; `finalize` still runs, so an answer produced before the
  cancel is delivered.

  Stale prose from before v2.5.2's streaming rebuild corrected: the module docstring,
  `build_gate_pipeline` (no longer used by `stream_chat_turn`), `ChatTurn.grounded`,
  `ground_step`, `persist_side_branch`, `_notify_turn_complete` and `stream_chat_turn`.

*SDK 2.5.5, Plato 0.1.7 (Plato hosts evaluation). Work lives on the `v2.5.5` branch, cut from `dev`.*

## [2.5.4] - unreleased

- **Two PR #75 review fixes.** `DbPackDraftStore.open` now refuses seed files whose paths store
  as one (`m.yaml` and `m.yaml `, collapsed by `check_rel_path`'s strip) with a `ValueError`, which
  Plato's draft routes answer as a 422. Before, the file-path unique constraint fired, the
  race handler swallowed it, and an `assert` on the re-read surfaced as a 500 (or returned `None`
  under `python -O`). With seeds deduplicated, the `IntegrityError` handler covers only the
  concurrent-open race it was written for; the assert is an explicit raise. Closes
  `TODO(integrity-catch-too-broad)`.

  `check_python_rule` now reports an `async def` entrypoint as "must be a plain def, not async
  def" instead of "defines no top-level function", which sent the author looking for a function
  that was there. The executor would otherwise have got a coroutine back and failed the rule as
  a non-bool result.

- **The schema check is SDK code: `jazzx_sdk.fabric.db.SchemaVersion`.** Four SDK stores
  (`pack`, `manifest`, `llm.cost`, `agents.definition`) each tell their consumer that *table DDL
  belongs in the consuming service's alembic*, and then hand it nothing to verify that with. Plato
  had written the verifier; the next consumer would have written it again or skipped it.

  Not a move. Three things in it were the service's, and each is now a constructor argument: the
  alembic tree, an optional `on_unmigrated` hook (Plato refuses a database migrated under its old
  `plato_*` schema layout, which is its own history and nobody else's), and the sentences an
  operator reads. The upgrade command is derived from the tree rather than configured, so it
  cannot name a path the service does not use. `PLATO_SQLITE_PATH` and `PLATO_DB_BACKEND` are
  Plato's hints, passed in; the default says something true and generic.

  `plato/boot/schema_version.py` is 115 lines and keeps its module-level names, so every caller in
  the service is unchanged and the 50 existing tests pass as they stood.

  Two hazards the generalization introduced, both caught in review and fixed. `_script_directory`
  overrode the ini's `script_location` with `migrations` beside it, which for any service laying
  its tree out elsewhere made it and `upgrade_to_head` read different directories -- the exact
  drift a single place exists to prevent; the ini's own value is used now, with the sibling as a
  fallback only when the ini names none. And `upgrade_to_head` states as a precondition, not an
  aside, that the service's `env.py` must honour `config.attributes["store"]`: one reading
  `sqlalchemy.url` instead migrates whatever the ini names, while the read-back inspects only the
  store it was passed and reports success over a database it never touched.

- **The SDK root is 14 modules, not 24.** What was left there had stopped saying anything about
  the shape of the SDK, so four groupings now carry a feature each:

  `jazzx_sdk.safety` holds the six guards on boundaries where input japes does not control meets
  infrastructure it does: `oidc` (an inbound token), `net` (a caller-supplied URL), `paths` (a name
  joined onto our directory), `sanitize`, `templating` (an untrusted template), `odata` (a filter a
  value cannot break out of). `net_safety` and `path_safety` lose the stuttering suffix inside it.
  It replaces `sanitize` in the tier contract, which it fits: the group depends only on
  `concurrency` and `failures`.

  `jazzx_sdk.closure` takes `closure` as its `__init__` and `bpmn` beside it, which is what their
  own docstrings already described: `bpmn` reads a repository as "a reference graph `closure` can
  walk". The `jazzx_sdk.closure` import path is unchanged.

  `jazzx_sdk.aggregate` holds `portfolio` and `reconcile`, the two many-to-one shapes every domain
  re-rolls. Not in `finance`: both say in their own docstrings that they impose no domain.

  `jazzx_sdk.ui` becomes a package holding what the module held, leaving room for the thin-client
  work and keeping its import path identical.

  Consumers: juno imports one symbol from the SDK (`client_layer.ClientLayer`) and is untouched.
  jaci's only affected imports are `jazzx_sdk.ui`, whose path did not move, so it is untouched too.

- **Route prefixes are SDK code: `jazzx_sdk.server.prefix`.** `api_prefix()` and
  `mount_prefix()` read `API_V1_PREFIX`, which the module's own comment says matches every sibling
  service and the platform. Nothing in it was Plato's but the docstring. In `server/` because
  mounting HTTP routes is what it is for.

- **`cryptography` floor raised to 50.0.0, and mlflow to 3.16.1 to allow it.** mlflow was the
  reason alert #98 (PKCS#7 EnvelopedData Bleichenbacher oracle) sat deferred: through 3.15.1 it
  pinned `cryptography >=43.0.0,<50`, and forcing 50 dragged mlflow back to 3.2.0. 3.16.1 relaxed
  that to `<51`, so the floor and the tracing backend can both move forward and all three
  cryptography alerts close together.

  The mlflow bump is exercised, not assumed: mlflow is an optional extra, so a plain
  `poetry install` leaves the old one in place. Installed with the extras CI uses, and note that
  poetry left `mlflow` at 3.15.1 with `mlflow-skinny`/`mlflow-tracing` at 3.16.1 until a forced
  reinstall; the suite was re-run against the matched set.

- **Superseded: the 49.0.0 step below.** Two Dependabot alerts: a verifier accepting wildcard
  DNS names that escape `permittedSubtrees` (moderate), and exponential path-building on duplicate
  self-signed intermediates (high). There is no 48.x patch release, so 49.0.0 is the first fix.

  It does not hit the wall that alert #98 still sits behind: mlflow 3.15.1 pins
  `cryptography >=43.0.0,<50`, which admits 49 and holds mlflow where it is. #98 needs 50.0.0 and
  remains deferred for that reason.

  The relock also moved `msal` 1.34.0 to 1.39.0, which is forced rather than drift: 1.34.0 pinned
  `cryptography <49` and 1.39.0 allows `<51`. Nothing else moved.

- **An upload's own content is extracted, not its temporary pathname.** The policy-extract
  upload route wrote each upload's bytes to a temp path and then asked `to_markdown`, which takes
  a path *or* inline markdown and returns anything it declines to treat as a path unchanged. A
  filename carrying a newline makes the temp path one of those, so the document became its own
  pathname and the run proposed rules from nothing. `httpx` percent-encodes such a filename, as
  RFC 7578 asks; Starlette passes through one from a client that does not, which is the case the
  test builds by hand. It calls `convert_document` now, the path-only entry point, whose raise the
  route already turns into a 422 naming the file.

  The rest of the family was checked and is correct: `classify`, `extract` and
  `InteractiveAgent._read` all document path-or-text input and want the front door.

- **The JTBD extraction CLI refuses a corpus it cannot cite, and reports a run that proposed
  nothing.** Three ways a bad run looked like a good one:

  `to_markdown` returns anything it cannot resolve to a file unchanged, which is the right
  contract for a front door taking either a path or already-converted markdown. Every CLI argument
  is a path, so anything it declines to convert was extracted as a document whose text was its own
  path. It calls `convert_document` instead, which is the path-only entry point and raises. That
  also reads two documents the front door would have declined: a path over its 512-character
  limit, and a file whose text happens to equal its own path.

  The CLI now passes `default_step_error` to `run_policy_extract`. It is opt-in, so a step that
  raises, such as the corpus refusal below, left a traceback instead of the refusal `_main`
  already knows how to print.

  A repeated document name makes two documents cite as one, since a citation is the name plus the
  clause marker. Refused in `segment_step` rather than in the CLI: the CLI and
  `PolicyExtractionService` share that step, and a check on one entry point left the other
  collapsing silently. Refused rather than disambiguated, which would put a machine's directory
  layout into a pack's citations.

  A run proposing no rules leaves `result.policy` as `None`, so nothing was written and the exit
  code was 0. With `--out` pointing at an earlier run's policy, that presented the old file as
  this run's artifact. It now says so on stderr and exits non-zero; the stale file is still left
  alone rather than truncated, so nothing is lost either way.

- **A composite reports the child that could not run, not the first one that stopped.**
  `_composite_reason` special-cased only the unapproved reason and otherwise took child order, so
  an `all_of` whose first child lacked data and whose second could not be evaluated reported the
  data gap, which excuses the rule. Any withholding reason now outranks a data gap;
  `POLICY_NOT_ACTIVATED` still ranks first among them, because it is the one whose refusal text
  names the key an operator has to approve.

- **A blank procedure status is refused.** Keying statuses for matching made a whitespace-only
  status key to the empty string, which is also what a model answering nothing keys to, so a blank
  answer resolved as that outcome's verdict. `min_length=1` on the field does not catch it, since
  a space is one character.

- **A split clause keeps its heading.** `_split_long` builds replacement segments and did not
  carry the new field, so a clause long enough to split lost the qualification a short one kept.

- **One rule matches a procedure status everywhere.** `JtbdExtractor._candidate` case-folded its
  own way, so a template declaring `" PASS "` kept the template's generic criterion instead of the
  generated requirement. It uses `outcome_key` now, as validation and lookup do.

  Deferred, as `TODO(dependency-check-order)` in `condition_evaluator.py`: the natural-language,
  procedure, ratio and matrix evaluators check evidence before their deployment dependency, so a
  missing field masks a missing agent or profile the same way it masked the Python executor. They
  `raise` where `PythonEvaluator` withholds, and `check_compliance` does not catch it, so
  reordering alone turns a silent allow into an uncaught exception rather than a governed refusal.
  Making them withhold is the right fix and is a change to four evaluators' error contract.

- **A governing rule that could not run no longer passes silently.** `check_compliance` handled
  only `POLICY_NOT_ACTIVATED` as withholding and skipped every other `INDETERMINATE` under a
  comment that said "missing data". `CONDITION_UNEVALUABLE` is not missing data: it is the rule
  failing to run at all. A procedure answering a status the pack never declared, or a Python rule
  whose condition could not be read, came back inside `allowed=True` with empty warnings and "All
  policy gates passed" -- the worst shape a compliance engine has, a gate nobody evaluated
  reported as a gate that passed.

  The split now lives in one named place, `WITHHOLDING_REASONS` behind `gate_blocks`, which the
  three gate call sites already shared and which `check_compliance` now asks of a rule's own
  condition too. `IndeterminateReason` has four members and a test pins which two withhold, so
  the next one added has to answer the question rather than inherit a default.

- **The Python executor is checked before the reads.** Whether an executor is installed is a
  property of the deployment, not of the case, but it was asked second: a rule with a missing read
  answered `EVIDENCE_MISSING` on a replica that could never have run it, and missing evidence
  excuses the rule, so an unexecutable governing rule came back inside an allow. `PythonEvaluator`
  already claimed in its docstring that every way it cannot run withholds; now it does.

- **Two procedure statuses one lookup cannot tell apart are refused.** Uniqueness compared the raw
  strings while `outcome()` case-folded, so a pack could declare `PASS -> SATISFIED` and
  `pass -> VIOLATED`, pass validation, and have the violation resolve as the satisfaction.
  `outcome_key` is now the one rule both use, so they cannot disagree again; it also strips, which
  the lookup did to its argument and not to the declaration.

- **`PythonExtractor` can build its output schema.** `_DraftCase.context` is an open dict, which
  is invalid under the strict JSON schema `AgentOutputSchema` defaults to, so `AgentOutputSchema`
  raised before any model call and every `extract` and `formalize` failed on construction. Built
  non-strict, with a test that sweeps every `output_type` in the SDK rather than this one.

- **A clause keeps the heading that qualifies it.** The heading was used only as a fallback
  marker, so a numbered clause under "Only for loans above $1,000,000" reached the model as a bare
  obligation and the rule extracted from it applied to every loan. `ClauseSegment.heading` carries
  it beside `text`, and one `_render_unit` puts it in both prompts that show units; it was written
  out twice and only one copy would have got this.

- **`fabric` no longer imports `pack`.** Two `fabric.graph` modules took `DEFAULT_TENANT` from
  `pack.store`, which is upward in the tier contract and failed `lint-imports` on the default
  branch. Declared locally, as the five other stores outside `pack` already do.

- **An authoring chat: `jazzx_sdk.pipelines.authoring_chat`.** `authoring_tools(service=, store=,
  tenant_id=, reasoning=)` gives an `InteractiveAgent` five tools: `start_extraction` (document
  text into a run), `extraction_status`, `list_rule_proposals`, `propose_rule_edit` and
  `check_rule_ambiguity` (policy-workbench's ambiguity review, as one structured call).
  `build_authoring_chat` wires them into `pipelines.chat` with `authoring_agent_spec` (tools as
  direct skills). The chat writes only proposals: an edit is a new `<policy>:<rule>~edit-*`
  proposal beside the original, reviewed and merged like any extracted rule. No router step: the
  agent chooses the tool. Not yet mounted in Plato, whose assistants get no tools today (the
  domain-pack runtime plan's 0.4).
- `packs.html` reads every FastAPI `detail` shape (string, `{message}`, validation array).

- **Plato: authoring routes.** `plato/api/authoring.py` mounts the SDK's extraction and
  proposal-review routers at `{prefix}/authoring/extract/...` and `{prefix}/authoring/review/...`,
  with stores built per request for the resolved tenant (`DbProposalStore`, `DbPackDraftStore`,
  `DbProposalCommentStore`), writes behind the packs routes' author gate, and extraction on the
  configured model. The JTBD template comes from the tenant's draft file `jtbd_template.yaml` when
  there is one. Mounted only when a database is wired. Migration `0006_policy_authoring` creates
  `proposal` and `proposal_comment`; `plato/models.py` registers both stores. Flow: upload documents
  to a run, review and approve proposals, `merge-rules` into the pack draft, then the existing draft
  publish. `packs.html` gets an "Author policy from documents" panel under the draft editor:
  upload and extract, proposal cards (rule, steps or source, cited excerpt, reasoning) with the
  lifecycle's own buttons and comment threads, and merge-into-draft.
- The extraction router accepts an async `tenant_of`; the review router resolves the vocabulary per
  request with `vocabulary_for_request` and its stores once per handler.

- **Authoring over HTTP, in the SDK.** Router factories any shell mounts, with no Plato import:
  - `server.policy_extract_api`: `POST {prefix}/{pack_id}/runs` (multipart documents, `policy_id`,
    `representation`: `jtbd` | `obligations` | `python`) converts each upload through the SDK's
    `to_markdown` and starts a `PolicyExtractionService` run; `GET {prefix}/runs/{id}` and
    `GET {prefix}/{pack_id}/runs` poll. Runs are in-process tasks with an in-memory registry,
    tenant-scoped through `tenant_of(request)`; proposals land in the `ProposalStore` as proposed,
    so a restart loses the run record, not the work. `default_components(representation, ...)`
    builds the pipeline for each representation.
  - `create_proposal_review_router` (the vocabulary review router, now also for rules): the
    proposal view carries `rule`; `drafts=` mounts `POST {prefix}/{pack_id}/merge-rules` (accepted
    `<policy_id>:*` rule proposals into the pack draft via `merge_rules_into_draft`, merged ones
    recorded back as `merged`); `comments=` mounts proposal comment threads, author from the caller
    identity.
  - `fabric.graph.proposal_comments`: `ProposalComment`, in-process and `DbProposalCommentStore`
    (`proposal_comment` table, tenant-scoped at construction).
  - `DbProposalStore` is tenant-scoped at construction (`tenant_id=`), its table renamed
    `vocabulary_proposal` -> `proposal` with `tenant_id` in the key, since it now holds rules too
    and Plato requires tenant in every key. No consumer outside japes used it.
  - The extraction router refuses a submit in a deployed posture without `auth` and a resolvable
    caller, passes the tenant to `components_for` / `pack_for` (so each tenant writes its own
    proposal store), refuses an upload with no usable filename, and keeps at most `MAX_RUNS` run
    records. A comment's `parent_id` must be a comment on the same proposal.
  - The review router resolves its stores per request when given `store_for` / `drafts_for` /
    `comments_for`, so a tenant reviews its own queue.
  - `PolicyTurn.pack_id` files proposals under a pack when no `Pack` object is given; without it
    they were filed under an empty pack id.
- JTBDSet export replays a block verbatim only while its condition, title (the rule description)
  and reference documents all match what was imported; any edit renders from structure.

- **JTBDSet in and out: `jazzx_sdk.pipelines.jtbdset`.** `import_jtbdset(artifact, pack_id=...)`
  turns a policy-workbench / MACER JTBDSet into pack policies: one `scope: institution` policy per
  section with a `procedure` rule per JTBD (Purpose, Step N, Deterministic Validation Rules and
  Outcomes headings map to purpose, steps, checks and outcome criteria; reference documents and
  metadata such as `loan_metrics`, `assistant` and `sequence` ride in `domain_extensions`), plus one
  `scope: product` policy per program block. An overlay block composes with the base rule, as its
  "applied on top of" wording says; `NOT_APPLICABLE` becomes a `suppresses`; `NO_CHANGE` becomes
  nothing. The result carries `programs` for the manifest. `export_jtbdset` inverts it, so MACER can
  still be fed. Structure round-trips; markdown whitespace does not. A block with no step headings
  imports and exports whole, as one step.
- `PythonExtractor.extract` names a clause's rule by its marker as written, like
  `ModalClauseExtractor`.

- **Generated Python rules: `kind: python`.** `PythonCondition` holds one module, an entrypoint
  (`check(ctx) -> bool | (bool, dict)`), `reads`, `derived_from` and author-written `cases`.
  - `python_check.check_python_rule` is a static gate, not a sandbox: it must parse, define the
    entrypoint with one parameter, import only math/decimal/fractions/statistics/datetime/re, use
    no `exec`/`eval`/`open`/`getattr`-style builtins or dunder attributes, and read the context
    only by literal keys named in `reads`.
  - `PythonEvaluator` runs through a `PythonExecutor` found at
    `context[PYTHON_EXECUTOR_CONTEXT_KEY]` and passes it only the declared reads. None ships:
    Every way it cannot run (no executor, source failing the check, which is never sent, the
    executor failing, a malformed result) is `policy_not_activated`, which withholds an allow
    instead of skipping. Every read is required.
  - `lint_pack` reports `unsafe_python` at any nesting.
  - `pipelines.policy_code.PythonExtractor` generates one from a clause or an existing rule
    (`formalize`, keeping its citations); source failing the check is a failed segment. A generated
    rule does not replace what it formalizes; retiring the English rule is left to an author.
- `programs:` accepts a bare string for one overlay (it was split into characters), and
  `lint_pack` warns `overlay_in_no_program` for a `scope: product` policy no program lists.

- **Programs are pack data: manifest `programs:`.** `programs: {program_id: [overlay policy ids]}`
  is read by `Pack.overlay_map`, and `DefaultPolicyExpert.from_pack(pack)` wires registry, core
  policies and that map. Until now the program-to-overlay map existed only in consumer Python
  (jaci's `OVERLAY_MAP`s), which a pack served by Plato cannot have. `lint_pack` reports
  `unknown_program_policy` and `program_policy_not_overlay` (a program naming a policy that is not
  `scope: product`, which therefore also runs as core). Seed `ci-spread-core` declares
  `rb-abl-2026`, jaci's id. The `overlay_map` docstring no longer says overlays win "for any field
  both define", which stopped being true when field-claiming was retired.

- **Policy precedence is declared per rule; field-claiming is retired.** `check_compliance` used
  to skip every lower-precedence rule reading a field a higher-precedence rule had evaluated. That
  was replace-by-field and implicit: an overlay tightening a cap switched the core cap off instead
  of composing with it, and a replacement removed every rule on the field rather than the one
  meant. Now:
  - `Rule.replaces: list[str]` names lower rules this one stands in for, taking effect only where
    the replacing rule applies (its applicability gate passes). A shared rule id replaces the same
    way, which is how the deal special-instructions file already overrides a program rule.
  - `Policy.suppresses: list[RuleSuppression]` (rule id, reason, citations) removes lower rules
    wherever the policy applies: a program making a base provision inapplicable.
  - Everything else evaluates, so tightening composes and the tightest threshold binds.
  - `ComplianceResult.metadata["superseded"]` lists the rules skipped this case and why.
  - A replacement refused for unapproved thresholds still replaces (the allow is withheld
    anyway); one short of data replaces nothing, so the base rule still runs. This settles
    `TODO(refused-rule-field-claim)`.
  - Replacement chains: a rule that is itself replaced (the deal file reusing an overlay rule's
    id) passes on what it replaced, so the core rules the overlay retired stay retired.
  - A conditionless rule with a gate replaces where its gate passes.
  - `lint_pack` reports `dangling_relation` for a `replaces`/`suppresses` naming no rule in
    another policy.

  Migration, behaviour-preserving: the plato seed `ci-spread-core` RB overlay now declares
  `replaces` for the core ceiling/floor *and* warning tiers it used to shadow (its
  `supersedes_core_rule` parameter named only the ceiling/floor; the parameter is gone). jaci's
  CRE MAA/CFI overlays and its `ci-spread-core` copy got the same, in jaci.

  Found by a survey of every overlay/core pair sharing a field: AML's
  `OPS-AUTONOMY-CEILING-HIGH-RISK` ("cannot be overridden by Overlay") shares `risk_tier` with
  `BSA-EDD-HIGH-RISK` in an earlier core policy and was being skipped whenever that rule
  evaluated. It now evaluates. The two also compare against `HIGH` and `high` respectively; left
  as found.

- **Accepted rules go into a pack draft: `jazzx_sdk.pack.rule_merge.merge_rules_into_draft`.**
  The rule counterpart of `KGAgent.merge`. Every accepted `Proposal(kind="rule")` is folded into
  one policy in a draft file (default `policies/<policy_id>.yaml`); an id already in the file is
  replaced, new ids are appended, other policies and top-level keys in the file are kept, and the
  merged proposals come back `merged` for the caller's store. It writes a draft only, so publishing
  stays the act that puts rules into force; the written policy is ACTIVE by default for that
  reason. It also reports whether the draft's manifest actually loads the file: `policies.dir` is
  not recursive, so `policies/jtbd/x.yaml` under `dir: policies` would publish and never be
  enforced. `manifest_reaches` states the loader's rules for that check.

- **Jobs to be done from a policy corpus: `jazzx_sdk.pipelines.policy_jtbd`.** The `procedure`
  representation of policy extraction, plugged into its two seams. `SectionSegmenter` splits every
  document at its markdown headings and clause markers (long pieces at paragraphs), labels the
  units `U1..Un`, and asks one LLM call to group unit ids into sections; the model only groups, so
  each section's text and citations come from the units themselves, and a unit the plan leaves out
  lands in an "Unassigned provisions" section instead of disappearing. `JtbdExtractor` makes one
  call per section and turns each job into a `procedure` rule citing the units it came from.
  `JtbdTemplate` (YAML) is the pack's say: section taxonomy, step outline, outcome vocabulary, and
  the evidence type ids and context fields a job may name. Names the template does not declare
  are dropped and recorded in the candidate's reasoning, never passed to the rule.
  `scripts/policy_jtbd_extract.py` runs it over real documents with the configured model and writes
  the DRAFT policy YAML.

  The policy pipeline's spine grew what that needed. `ClauseSegment.parts` makes a segment a
  composite of the clauses it was built from, `documents` names every document it draws on (so a
  section spanning two documents counts as two sources), and `label` is the handle a prompt uses.
  Extractors may be async and run `extract_concurrency` segments at a time. An extractor raising on
  a segment used to vanish without a trace; it is now logged and listed in
  `CorpusObligations.failed_segments`, and the step emits `ExtractedCandidates`. A candidate's
  `excerpt` is what the reviewer reads, instead of the whole segment.

- **Policy extraction takes a `Segmenter`.** `build_policy_components(segmenter=...)` decides how
  the corpus becomes units of extraction; `ClauseSegmenter` (the existing clause-marker split) is
  the default, so nothing changes for current callers. A segmenter sees every document at once as
  `(name, text)` pairs, because a topic-level unit such as a JTBD section draws on several
  documents, and it may be async.

- **A JTBD is a condition kind: `procedure`.** `ProcedureCondition` holds a purpose, ordered
  steps, checks stated in prose, the pack's evidence types the steps review, `reads`, and a
  declared set of `ProcedureOutcome`s, each a pack status (`PASS`, `CONDITIONAL`, ...) with the
  `Verdict` it counts as. The pack decides what `CONDITIONAL` means; the SDK does not guess. A
  procedure must be able to pass and to fail, and no outcome may be `INDETERMINATE`, which is the
  evaluator's own answer. `ProcedureEvaluator` is LIVE and stochastic, runs the steps through the
  `ReasoningAgent` in context, and maps the status the model names onto its declared outcome; a
  status the procedure never declared comes back `INDETERMINATE` (`condition_unevaluable`) rather
  than being coerced. Conditions the outcome carries land in `RuleOutcome.narrative`. Round-trips
  through `load_policies`, including shape-sniffing when `kind` is omitted.

  Adjudication's batch path no longer assumes every LIVE rule is `natural_language`: it asserted
  so, and a procedure rule would have crashed the segment. Each LIVE evaluator now renders itself
  into the batch and reads its own answer back (`BatchableEvaluator`), a batch item carries
  `status` beside `satisfied`, and a LIVE kind that cannot batch is reported `INDETERMINATE`
  instead of dropped. `lint_pack` reports `unknown_evidence_type` for an evidence type a rule
  reviews that the pack does not declare; it needs no ontology, so it runs on packs without one.

- **Two more Plato stores are SDK code.** `plato/packs/draft.py` is
  `jazzx_sdk.pack.draft_db`, beside the `store_db` it is the mutable half of, and
  `plato/reference/model_overlay.py` is `jazzx_sdk.llm.model_overlay_db`, beside the `cost` and
  `model_cards` tables it writes into. Neither imported a framework or anything from Plato, and
  both re-declared `DEFAULT_TENANT` next to an SDK that already had one. Plato keeps the routes,
  the lifespan and the migrations; `plato/reference/` held nothing else and is gone. The overlay
  tests split the same way: the store and its rules in `tests/test_model_overlay.py`, the route
  and lifespan in `tests/test_plato_model_overlay.py`.

- **Each pack loader says which pack shape it reads.** `plato.packs.loader` takes an *assistant*
  pack (manifest, profile, persona, skills) and `jazzx_sdk.pack.loader` takes a *domain* pack
  (ontologies, policy bundles). The matching names were the whole confusion; neither reads the
  other's directory.

- **A backend name nothing recognises is said, not silently defaulted.** Each dispatch takes one
  name and treats everything else as its default, so `blob_backend=azuer` wrote bytes to local
  disk behind rows claiming durability and logged nothing. `jazzx_sdk.backend_names` holds the
  recognised set per surface and one `check_backend` that warns and *returns* the name actually
  used, so a store keeps the backend it dispatches on rather than the typo -- `DbStore.backend`
  answered `sqllite` while every read went through `common`. Wired at all five dispatches (`blob`,
  `db`, `conversation`, `guidance`, and the run tracer), not just the one where it was found. A
  warning rather than a refusal: these are built in tests and notebooks with partial
  configuration, and the deployment-level refusals already live in `jazzx_sdk.config.posture`.

  Plato's `_pack_blob` keeps its own warning. It coerces the backend to `local` before constructing
  the store, so the SDK check never sees `PLATO_PACK_BLOB_BACKEND` and the durability half of that
  message is posture-gated in a way the library cannot be.

- **The pack inventory is SDK code: `jazzx_sdk.pack.pack_inventory`.** Store in, dict out, no
  framework. What it encodes is a fact about `PackVersionStore`, not about one page: `versions()`
  answers in `published_at` order rather than version order, so a backport reads oddly and the
  newest row is `last_published_version`, never `latest`. A second operator surface would
  re-derive that or get it wrong. `_MANIFEST_KEYS` went with it as `MANIFEST_SUMMARY_KEYS`. The
  routes, the prefix, the nav entry and `packs.html` stay in Plato; those are the service's own
  surface.

- **Review carry-overs closed.** The statement map no longer carries a second `@lru_cache` on top
  of the cached `owned_tables()` it is built from, and its test asserts the two properties that
  matter (the quoted registered name, the bound `:limit`) rather than restating the template the
  code derives. `run_tests.sh`, `scripts/README.md` and `net_safety.py` name the oidc module and
  test where they now live.

- **Seeding a pack store is SDK code: `jazzx_sdk.pack.seed_packs`.** It was most of
  `plato/seed.py` (198 lines, 52 left) with no framework import and no service state: a store, a
  directory, and four buckets back (`published`, `skipped`, `not_packs`, `failed`). Any consumer
  with an empty database and a
  checkout of authored packs now has one call rather than its own loop. `root` is a required
  argument, because *which* directory holds a deployment's bundled packs is the service's business;
  `plato.seed` keeps `PLATO_SEED_PACKS_DIR` and the bundled default and hands the answer in, which
  is all that is left of it.

- **`acting_user_id` moved to `jazzx_sdk.identity`.** It lived in `server/settings_store_db.py`,
  which made it FastAPI-tiered for no reason: its body is one `CallerIdentity.from_context()` call
  and nothing about it is a settings store. Lifting the seeder exposed that -- `pack` importing
  `server` is a layer violation `lint-imports` catches -- so it now sits beside the `CallerIdentity`
  it reads. All five importers were repointed; there is no re-export.

- **Inbound token verification is SDK code: `jazzx_sdk.oidc`.** It was `plato/auth/oidc.py`, and
  its own docstring is the argument -- *nothing in this estate verifies an inbound token; every JWT
  reference in japes and common is outbound*. 436 lines, no framework import, no service state, and
  no caller in Plato: written, tested and unwired, so the next service to need it would have
  written it again. Flat beside `identity.py`, which is what it produces, rather than under
  `server/`, which is FastAPI-tiered.

- **The table read picks a statement rather than building one.** `read_table` allowlisted the name
  and then interpolated it, which CodeQL still reads as a query built from a request. Every
  `SELECT` is now built from `owned_tables()` and the request only chooses which, so no request
  byte reaches the SQL even if the lookup were wrong -- provenance rather than validation.

- **Choosing a pack opens its row again.** `expanded` is keyed by tenant and pack together, and
  the picker added the bare `pack_id`, so the key matched nothing and the chosen row always
  rendered closed while a comment above it described the opposite.

*SDK 2.5.4, Plato 0.1.6. Work lives on the `v2.5.4` branch, cut from `dev` after 2.5.3
squash-merged.*

- **A stale schema names the revision gap instead of failing in the driver.** A serving replica
  comes up on an out-of-date schema by design -- `check_schema` reports rather than exits -- so the
  first request to a table a later migration adds answered
  `relation "pack_draft" does not exist`, which names neither the revision nor the fix. The draft
  routes now answer 503 with *this replica expects 0005_pack_draft and the database is at 0004;
  migrate it from the Details page*, and the packs page shows it rather than hiding the panel.

  `schema_gap` is asked only after a call has already failed, so it costs one round trip on a path
  that was returning an error anyway and nothing on the ordinary one. It is a diagnosis and never a
  trigger: migrating stays `job:migrate`'s work or an operator pressing Migrate, because a schema
  write driven by whichever request arrived first is what those two exist to prevent.

  Which way the gap runs decides the advice. A database carrying a revision this image does not
  ship is a replica older than its schema -- what a rolling deploy looks like while `job:migrate`
  has already run -- and telling that one to migrate points at a job that is finished. It is told
  to deploy the newer image instead. The driver's own sentence is still logged with the diagnosis,
  since the gap explains the failure rather than replacing it.

- **One tenant's activation no longer erases another's.** `pins_for` cleared the whole pin map on
  any miss, so with a multi-entry `PLATO_ACTIVE_PACK` the second entry wiped the first at boot,
  and the first composition for a previously unseen tenant silently reversed every other tenant's
  rollback -- only the last entry ever took effect. It drops the keys from a previous store now,
  which is what the clear was for. The caches beside it are recomputable and safe to clear
  wholesale; a pin is operator intent and is not. A read no longer creates an entry either: a
  composition asks about every tenant it serves, so inserting one per tenant grew the map with
  every distinct id a request carried, where the clear it replaced had capped it at one.

- **`read_table` allowlists the table itself.** The check lived in the route with a comment saying
  the caller does it, which holds until the second caller, and the name is interpolated into a
  `SELECT` because no dialect binds a table name. The row limit is bound rather than interpolated,
  and `owned_tables()` is cached, since checking in both places rebuilt the whole registration
  twice per request.

- **A pack can be edited in the console: `pack_draft` and `pack_draft_file`, migration 0005.**
  `plan_plato_authoring.md`'s stage 2. A draft is the mutable working copy `pack_version` refuses
  to be: one per `(tenant_id, pack_id)`, files as rows rather than an archive, because an archive
  is what publish produces and rows are what an editor reads a path at a time. Publish builds the
  same zip an upload carries and goes through the same `_publish_archive`, so `PackVersionExists`
  still refuses a re-publish and `pack_version` is never edited. The draft survives publication:
  the next edit opens the next version rather than starting again.

  Opened from a published version (`Edit` on any version row), from a bundled sample, or empty.
  Paths are checked on the way in, where the editor can say so, rather than at publish: a draft
  becomes a zip, so a `../` stored here would be a `../` in the archive.

  **A textarea, not an SPA.** The plan calls for React under the same prefix, and that is a real
  change to what the image is -- a build step, `node_modules` in CI, a bundle in the layer. A file
  picker and an editor are enough to change a persona or a threshold without leaving the console,
  and they cost none of it. The diff view and comment threads the plan wants next are what would
  justify the build; this does not pretend to be them.

  Every pack write goes through one `_refuse_unless_author` -- upload, sample and each draft edit
  -- rather than three copies of the same 403. The draft store is built from the request's tenant:
  without it every tenant on the page shared one set of drafts, which a store-level test could not
  see because the store was never the thing that was wrong. Opening reports the members it could
  not bring along, rather than logging them and publishing a pack quietly missing a file.

- **Four sample assistant packs ship with the image, and the packs page publishes one.**
  `plato/data/sample_packs` holds the demo-tenant packs that existed only as rows in a local
  database, generated by a gitignored script: nothing reviewable, nothing another machine could
  reproduce. `GET /packs/samples` lists them and `POST /packs/samples/{name}` publishes one into
  the calling tenant, through `pack_archive` and `store.publish` -- the upload route's own two
  calls, so a sample meets every rule an uploaded pack does. Not in `seed_packs`: `initialize`
  sweeps that directory into whichever tenant pressed the button, and `seed_packs` refuses an
  assistant pack by design.

- **The packs page says what a pack is made of, and links the quickstart.**
  `docs/DOMAIN_PACK_QUICKSTART.md` was linked from the README and from nothing an operator about
  to publish could see. The page now names the minimum layout and links it; `plato/guide.md`
  gained a Packs section doing the same, since it had covered running Plato and not authoring for
  it. A test holds each sample against `check_assistant_pack`, which is what caught the first cut
  of them dropping `pack_version_range` -- they zipped and published fine and would have failed at
  the first chat turn. Publishing is one `_publish_archive` shared by the upload route and
  the sample route, because the two were the same rule twice and had already drifted on
  whether an empty key is a 422.

## [2.5.3] - unreleased

*SDK 2.5.3, Plato 0.1.5. Work lives on the `v2.5.3` branch, cut from `dev` after 2.5.2 squash-merged.*

- **Plato's mark is the one the sidebar already gives it.** The browser tab showed a portico
  (`AccountBalance`) while dev-daily's sidebar showed two stacked racks (`Dns`), and the portico
  was another service's glyph anyway. `LOGO_PATH` is the `Dns` path now, which moves the favicon
  and `static/logo.svg` together -- a test already holds those two to the same mark.

- **Claude Opus 5.5 is priced and carded.** `claude-opus-5-5` at $4/$20 per million against Opus
  5's $5/$25, 1M context, 128k output, adaptive thinking, knowledge cutoff June 2026. Its cache
  reads are 0.05x input rather than the 0.1x every other Claude model uses, which the pricing page
  footnotes as an exception; taking the multiplier for granted would have priced them double. The
  Anthropic default stays `claude-sonnet-5`, which is still the cheaper model at $2/$10.

- **A model's rate or card can be corrected without a release.** `plato.reference.model_overlay`
  had the durable half built and tested -- append-only table, newest row per model wins, applied
  into the process rather than read on the costing path -- and nothing reached it: no route, no
  boot application, and the refresher never started. `GET/POST {prefix}/models/overlay` records a
  correction and applies it before answering, so the caller's next request is priced at what they
  just set; other replicas pick it up within the refresh interval. The payload is built through
  the same rule the applier uses, `build_overlay`, and refused 422 if it will not construct:
  stored first, a typo answered 200, failed to apply with only a log line, and -- newest row per
  model winning -- buried the last correction that did work. Values are checked as well as keys:
  a dataclass does not type-check, so `{"input": "3.0"}` built a `ModelPricing` happily and failed
  much later inside `compute_cost` as `float * str`, for every tenant and every replica. A card's
  window and output cap are checked the same way, since a string there fails wherever a consumer
  compares a prompt against it instead.

  The refresh runs in the serving replica rather than as a job, which is the opposite of what
  `plato.jobs` argues for a sweep and right for the same reason: a reaper mutates shared rows, so
  one run per replica multiplies the work, while this mutates only the in-process registry that a
  job could never reach. `create_app` grew a `lifespan` parameter to hold it, since a boot-time
  `asyncio.run` cannot own a task that has to outlive the loop it started on.

  Scoped to `DEFAULT_TENANT` deliberately: `register_model_pricing` writes a process-global table,
  so applying one tenant's overlay would price every other tenant's calls with it. The column
  stays for a future where the registry is scoped too.

- **The OpenAI default is `flex_gpt-6-luna`.** Half the cost of `flex_gpt-5.6-luna` for the same
  turn ($0.00150 against $0.00320 at 20k+2k), newer, and six reasoning efforts instead of four.
  Every consumer that has not set `JAPES_LLM_MODEL` moves with it. `DEFAULT_VISION_MODEL` in
  `tools/documents/classify.py` still names 5.6 Luna: that one is a classification-accuracy choice
  rather than a cost one, so it wants its own check before it moves.

- **The GPT-6 line is flex-eligible, and flex eligibility is data now.** OpenAI serves all three on
  the cost-optimized tier at half the standard rate, so `flex_gpt-6-luna` costs $0.0015 for a
  20k+2k turn against `flex_gpt-5.6-luna`'s $0.0032 -- half, where the two standard tiers differ by
  6%. `FLEX_ELIGIBLE` was a literal in `model_identity.py`; it reads `pricing.flex` from
  `model_data.json` now, so a new model stays one JSON edit. The flag rides on the pricing row
  rather than the card because eight of the seventeen eligible models carry no card.

- **The 5.6 cards understated their reasoning efforts.** All three list `none, low, medium, high`
  while the model pages give six, so asking for `xhigh` or `max` drew a warning saying the value
  was not carded. The test that covered that warning had used `xhigh` as its out-of-range value
  and went green against a card that was wrong; it derives an impossible value now.

- **The GPT-6 line is priced and carded.** `gpt-6-astra` at $10/$50 per million, `gpt-6-sol` at $2/$10 and
  `gpt-6-luna` at $0.10/$0.50, each with a 1.05M window, 128k output, and the long-context tier
  above 272k prompt tokens (2x input and cache rates, 1.5x output). Cache-write rates are recorded
  for all three, which the 5.6 rows omit. Astra carries five reasoning efforts where the other two
  carry six: its page does not list `none`. No bare `gpt-6` alias, which no model page mentions.
  One JSON edit, no code.

- **The Knowledge Hub bulk archive reader catches what a corrupt member actually raises.** It
  caught `BadZipFile` only, so a member whose deflate stream is corrupt, or is encrypted or uses
  an unsupported method, escaped instead of reaching the per-document fallback the handler exists
  for. Same family as the pack-manifest read above.

  Its single-document sibling had the reverse problem, and a worse one: opening and reading sat in
  one `try`, and `zf.read` answers a corrupt member with `BadZipFile` as well, so that arm returned
  the whole archive as the document's bytes -- silently, under the document's name, for every
  `fabric.docs.materialize` consumer. Only the open can mean "not a zip", so the two are separate
  now and a read failure reaches `_fetch`, which drops the document with a warning. `_permanent`
  classifies an unreadable archive as permanent alongside a denial and a missing capability: the
  hub returns the same bytes each attempt, so retrying only burned the backoff before the drop.

- **A pack member with a corrupt deflate stream is a refusal, not a traceback.** `zlib.error` is
  not a `BadZipFile`, so it escaped the conversion every other read failure goes through and
  reached the upload route as a 500. Corrupting the head of a member's compressed payload
  reproduces it: zlib rejects the block type before any CRC is checked.

- **A migration that cannot read the current revision is still attributed.** That read sat outside
  the `try`, so a database that failed there skipped the log line naming who asked and answered a
  bare 500 -- on the one irreversible action a relaxed posture allows.

- **The packs page never reads a tenant its picker is not showing.** A tenant remembered in
  `localStorage` that `PLATO_TENANTS` no longer lists went into the hidden field while the select
  stayed on its first option, so every read, expand and delete went to a tenant the page was not
  naming -- under a heading that said "All tenants". `chooseTenant` now decides, keeping a saved
  value only where the deployment still serves it, and the picker follows the field
  unconditionally. Its own function because a test runs it: the first cut of that test greped the
  page for two source lines and missed a defect on the line between them, where a remembered `"*"`
  against an empty tenant list stored the text "undefined" as the tenant.

- **One pack file is read bounded, not read whole and then sliced.** `read_text` pulled an entire
  member into memory to return 20,000 characters of it, and a member's size is capped only by the
  256 MB archive cap. Same shape as the manifest read, with the newline normalising text mode did
  kept explicitly.

- **The mount sweep covers the dashboard's fetch prefix again.** It matched `const PREFIX` only,
  and the dashboard's is `const prefix` since it stopped deriving one from the `api-info` href, so
  that page's prefix went unchecked while a comment claimed it was covered.

- **A cancelled chat stream no longer abandons a task on the delta queue.** Cancellation lands
  inside the `asyncio.wait` on that queue, where the pending `get` is a task of its own; only the
  run was cancelled, so it waited on a queue nothing would fill and asyncio logged "Task was
  destroyed but it is pending!" for every abandoned turn. The `GeneratorExit` arm needs no such
  line: it is thrown at a yield, and the getter is settled at every one.

- **`byte_budget` says what to set instead of raising a TypeError.** Its factory read the budget
  with `or`, so `max_chars=None` -- documented as "no char budget" -- reached `ByteBudgetStrategy`
  and failed its `< 1` check on a `NoneType` comparison. It reads `max_chars` as a budget in bytes
  and says so; the `max_bytes` it also looked for is not a field `CompactionPolicy` has, and
  `extra="ignore"` would have dropped one written in a spec.

- **Activating a version that was never published answers 404.** Everything `activate` raised
  became one 409, so a caller branching on the status could not tell a missing version from a pack
  that loaded no assistants.

- **The forged-mount test checks the rendered page, not only its hrefs.** The pattern stops at the
  first quote, so a payload that closed the attribute and added another was read as a clean href
  and passed.

- **A pack archive's manifest member is capped at 1 MB.** `MAX_ARCHIVE_UNCOMPRESSED_BYTES` is a
  sum over the archive, so a single member could declare all 256 MB of it, pass the gate, and be
  read whole and YAML-parsed: measured at 50 MB, a 48 KB upload held a worker for 85 seconds and
  131 MB. The manifest is now read through `open` with a bounded read, so the refusal costs the
  first megabyte rather than the whole member. `store_db._unpack` had the member-path check and no
  size check at all, and it is the call that writes to disk and also runs on archives already in
  the store; it applies the same gate before extracting.

  Raised in review as a zip bomb defeating the declared-size check. That mechanism does not hold:
  CPython bounds a member's output at the declared size, so a lying-small header truncates and
  fails CRC rather than expanding. The cap is worth having for the reason above instead. Raised a
  second time against `_unpack`, where the claim was that `extractall` writes every member with no
  limit; measured, a 48 KB archive declaring 0 bytes writes 0 bytes and raises. A test pins that
  bound, since it is what makes the gate sufficient rather than merely cheap.

  `manifest_from_archive` no longer takes `max_uncompressed_bytes`. `_unpack` cannot learn a
  caller's override, so a publish admitted under a raised cap would be a version that can
  never materialize, on a row that is immutable. One cap, read from the constant on both sides.

- **`PROJECT_NAME` is documented as `japes-plato`.** `DEPLOYMENT_ENV.md` said `plato` while
  `plato/defaults.py` has set `japes-plato` since it was written, which is the OTEL service name
  when `APP_NAME` is unset. That table is hand-written, unlike the boot table below it, and nothing
  held it to the code; a test now pins every row of it to `COMMON_DEFAULTS`.

- **The packs page offers the tenants this deployment serves.** The `X-Tenant-Id` field was a
  blank box on a page that refuses to read without one, so an operator had to already know the
  answer. It is now a picker backed by `PLATO_TENANTS`, read from the same variable the routes
  use -- through `_tenants`, the wiring's own rule, so the local posture's single default tenant
  is offered too rather than an empty picker. A select rather than a datalist, which shows nothing
  until the field is clicked and so left the page opening as a blank box over a refusal.

  **It opens on every tenant.** Production serves one, and that is this view with one entry rather
  than a different view. The page fans out over the configured tenants, one tenant-scoped request
  each, and merges the answers into one table with a `Tenant` column, so no cross-tenant read
  exists on the server and the route keeps requiring `X-Tenant-Id`. A tenant that refuses is named
  beside the packs that read rather than replacing them. Every per-version read, file read and
  delete carries the tenant of the row it came from; publishing and initializing ask for a single
  tenant, since neither has a meaning across four.

- **The nav is pages; a JSON route is linked from the page that renders it.** It carried two
  rows -- four pages, then eight raw routes -- so `Packs` and `packs` sat beside each other
  meaning different things, and `packs` was a link a browser could not follow at all, being the
  one tenant-scoped route there. Now: Dashboard, Details, Packs, Guide, the same on every page.
  Each dashboard panel links the route it renders, the details page links `/info`, and `health`,
  `openapi` and `info` sit together on the dashboard. The packs page links nothing: `/packs`
  needs `X-Tenant-Id`, which an anchor cannot carry, and that is the same reason it left the nav.

  `dashboard.html` read the API prefix by parsing the `info` link's `href`, which is what made
  removing it hazardous (a `TODO(omit-info)` recorded that). It now reads the substituted
  `__API_PREFIX__`, as `packs.html` already did.

- **The unnamed-tier advisory is logged once per process.** `check_settings` has two boot callers,
  so every dev-daily startup log carried that paragraph twice.

- **A published version can be looked through.** The packs page listed packs and versions and
  could not show what was in one. `GET /v1/packs/{pack_id}/{version}` returns the manifest and the
  file list, and `?path=` one file's text; a version row expands into both, and a file row into
  its contents. Through `materialize`, so opening the same version twice reads the digest-keyed
  cache rather than the blob store. The path is matched against what was listed rather than joined
  onto the root, dotfiles are excluded (the unpack cache's own marker is not pack content), and
  the text is bounded.

  Every operator-facing failure reason across `plato/` now reports the exception's message, not
  just its type: the pack list and version read, the per-table count and the table read on the
  database panel, and the seed report. "RuntimeError" told an operator nothing about which
  failure it was.

- **The logs panel takes a level.** It was fixed at whatever the root logger captured; a selector
  now narrows it, reloading that panel alone. The buffer holds what the logger let through, so a
  level below `effective_level` returns nothing rather than more, and the meta line says
  "captured" to keep that distinction.

  It selects one level rather than a floor, and both of the panel's sentences now say so: the
  options read "ERROR only", an empty view reads "No ERROR records among the 143 kept", and the
  meta line counts the filtered records against the unfiltered total. `/logs` returns that total
  alongside `capacity`. Before this, picking `ERROR` over a buffer of INFO claimed "Nothing logged
  at INFO or above since this replica started", which was false, and the stale count from the
  previous read stayed on screen beside it -- every panel's empty path clears its meta now.
  The response echoes the level it was filtered by, so a sentence describes the answer it has
  rather than a selector that may have moved while the fetch was in flight.

- **The pack inspect route reports an unreadable store instead of failing.** `read_pack_contents`
  guarded `materialize` and not the `store.get` above it, so an unreachable database answered 500
  and the page showed "HTTP 500" rather than the store's own sentence. Same rule as `pack_inventory`.
  Opening a file showed `detail` only, so that sentence became "could not read <path>"; it reads
  `reason` too, as the version row already did.

- **The raw `packs` link is gone from the nav's JSON row.** It is the only tenant-scoped route
  there, so a browser that cannot set `X-Tenant-Id` got a 400 from it; `Packs` reaches the page
  that can. The packs page now also says which field to fill when a read is refused for want of a
  tenant -- the server's own sentence, plus where to fix it. No tenant is guessed: naming one for
  the operator is the cross-tenant read the refusal exists to prevent.

- **Seeding refuses a non-durable archive, like uploading already did.** `POST /v1/packs`
  refused on a deployed replica whose blob backend is not `azure` -- the row commits and outlives
  the bytes -- while `POST /v1/packs/initialize` wrote the same archives to the same store with no
  such check. A rule about whether the bytes survive cannot depend on how they arrived.

- **An activation is a per-tenant pin, and it reaches requests.** Once requests composed from
  the store, `activate` was rebinding a pair nothing on the request path read: activating
  `hc 1.0.0` while 2.0.0 was published logged "now serving 1.0.0", returned 200, and 2.0.0 kept
  serving, so a rollback was a silent no-op. `published_registries` takes `pinned`, a
  `pack_id -> version` map, and serves the pinned version in place of the most recently published
  one; `activate` records the pin for the tenant it names and drops that tenant's composition.
  This is the versioning model: each tenant holds the version it is on, and a rollout or rollback
  is an operation on one tenant.

  The same change closes a leak. The pair `activate` used to rebind was also every tenant's
  fallback, so with no `PLATO_PACK_DIR` a `mortgage` request answered from `healthcare`'s
  activated pack. The pair is now the image's pack and nothing rebinds it; resolution is the store
  with pins, then the image's pack, then nothing. A pin naming an unpublished version warns and
  serves the published one.

  **`PLATO_ACTIVE_PACK` holds one reference per tenant and pack**, comma-separated like
  `PLATO_TENANTS`, and boot restores each on its own. As one scalar it kept only the last
  activation across a restart, which undid every other tenant's rollback silently. Pins are keyed
  on the live store like the caches beside them, so a database swap does not carry a version from
  one database to another. A pin that will not materialise at boot is a boot note, as before:
  the replica is not serving what it was told to, and `/health` says so. That this unreadies the
  other tenants of a demo replica is accepted, because a deployment is one tenant.

- **A boot note can be dropped by the recovery that resolves it.** Notes lived for the process:
  a pin that failed at boot because the blob store was briefly unreachable kept `/health` at 503
  after the same version was activated successfully at runtime. `record_boot_note` takes a
  `key`, and `drop_boot_note(key)` forgets that one note; the boot activation records under the
  reference and a runtime activation of it drops it. The migrate route uses the same primitive:
  the entry point records the schema refusal under a key, and a successful migration through the
  route drops it, which is the "never migrated" note that kept dev-daily's `/health` at 503 after
  the migration had run. The key is the parsed reference, so `pack/1.0.0` and
  `default/pack/1.0.0` are one pin.

- **The dashboard expands a table into its rows, and the packs page has a pack selector.** The
  database panel listed table names and row counts with no way to see what was in them; clicking a
  table now fetches `GET /v1/database/tables/{table}` and renders the rows beneath it, fetched
  once and kept across a collapse.

  **Secrets stay masked.** `plato_setting` holds what `/config` serves masked -- the connection
  string and every API key -- so the route masks the same keys, read from the settings catalog
  rather than a second list. The table name is checked against `plato.models.owned_tables()`
  before it reaches a `SELECT`, values are bounded (a manifest column is a whole document), and
  the route is withheld under the same gate as the rest of the panel.

  The packs page lists every pack in a selector; choosing one narrows the table to it and opens
  it. Shown only when there is more than one pack, since the point is choosing between them.

- **Each tenant serves its own published packs.** `AssistantRuntime` was constructed with
  `registries=lambda _tenant: ...`, discarding the tenant, so one replica served one composed pack
  set to everybody and `activate` rebound it process-wide: whichever tenant activated last won for
  all of them. `registries_for(tenant)` now composes that tenant's published packs through
  `published_registries`, which already existed for this and had no caller outside tests. Cached
  per tenant and dropped for the one tenant an activation names.

  Layered, not replaced: the pack the image ships stays the platform layer, and a tenant whose
  store yields no assistants falls back to the process pair, so a tenant that has published
  nothing serves what it served before. An unreachable store warns and falls back rather than
  failing the turn, and both fallbacks are cached, since this is the chat path.

  Which pack a tenant serves is resolved in one place. No route, handler or agent takes a
  `pack_id`: they address a tenant, and the wiring answers.

  The cache is keyed on `(tenant, id(handle.current))`, the convention the manifest, session and
  pack stores beside it already follow, so a database swap cannot hand back registries composed
  from the retired one. `pack_forgetter()` is the seam `plato.api.packs` calls after publish,
  delete and seed; without it a warm replica kept serving a retired version while a freshly
  started one served the new, with nothing reporting the difference.

  **Publishing a pack now makes its assistant addressable.** `agent_for` resolves the manifest
  from the manifest store and `upload_pack` never wrote there, so four uploaded packs answered 404
  until something seeded it. Composition reconciles the two, which also repairs packs published
  before this. Guarded on a real difference: `put` stores a new head and demotes the prior one,
  and `release_id` is part of the agent cache key, so an unconditional write would rebuild every
  agent on every turn.

- **`--check-pack ""` read the working directory.** `Path("")` is `.`, so an unset variable in a
  CI wrapper rglobbed and read every file under the cwd into memory before reporting `unloadable`:
  measured from the repo root at 35,554 files, 922 MB, 1.13 GB peak RSS. In a memory-capped
  container that is an OOM kill rather than an error. An empty source is now named, not read.

- **A guardrail the profile names and nothing registers is reported.** The same declared-name join
  the skill check already made, one layer out: `build_from_manifest` drops an unregistered
  guardrail silently, so the bundled demo pack certified as clean while both of the clinical
  governors its profile declares resolved to nothing. `check_assistant_pack` now compares the
  declared names against the guardrails the bound agent actually carries and warns per name; the
  pack still binds, so it is a warning. `bind` returns the agent alongside the failure, and
  `bind_failure` is the wrapper for callers that only want the latter. `describe()` reports
  findings and the bind confirmation together rather than one or the other.

- **A database migrated under the old schema layout is refused, not re-migrated.** With the
  revision row back in the default schema, a Postgres database carrying
  `plato_control.alembic_version` reads as never-migrated, and an upgrade would build a second
  copy of every table beside the orphaned ones. `current_revision` now looks for the legacy row
  before answering `None` and raises naming the situation. No migration moves the tables; it is a
  person's call.

  The probe rolls the connection back first. Postgres aborts the transaction on the failed
  `alembic_version` read, so without it the probe raised "current transaction is aborted" and the
  guard never fired. Verified against a 16 cluster carrying the old layout: the refusal fires with
  the rollback and does not without it.

  The empty-source guard moved into `DirectoryPackSource.read`, which refuses a directory with no
  `manifest.yaml` before walking it. `str(Path(""))` is `"."`, so a guard on the string alone
  covered the argparse form and not a caller passing a `Path`.

- **`compress_tool_output` no longer swaps a falsy compressor for the default.** The last
  `x or Default()` of the family whose siblings became `is not None`.

- **Citation rewriting absorbed unbalanced decoration.** `SourceBuilder.rewrite` walked left and
  right independently, so a delimiter that was not adjacent to the anchor was eaten on one side
  only: `(see loan_1_sarah.pdf)` came out as `(see MARKER` with the closing bracket gone, and
  `[the file](loan_1_sarah.pdf)` lost its link destination. The existing test covered only the
  symmetric-and-adjacent shapes hugging the token, which is why it passed. The walk now steps
  outward in lockstep and absorbs a closer only when its opener is the character being absorbed on
  the left. No caller wires `rewrite` yet; the failure would have been mangled answer text.

- **A boot-time `asyncio.run` left every request talking to a dead event loop.**
  `_apply_durable_settings` applies `/v1/config` settings before uvicorn starts, which means an
  `asyncio.run` against the shared store, which builds `common`'s memoised engine inside a loop
  that then closes. An asyncpg pool belongs to the loop that filled it, so every later request
  touching the database failed `got Future attached to a different loop`. This predates the schema
  work and is why Plato could not serve on Postgres at all.

  `_drop_boot_loop_bindings` runs after **each** boot-time `asyncio.run` -- applying settings and
  activating `PLATO_ACTIVE_PACK` are separate loops, and forgetting once at the end lets the
  second rebind what the first cleared. It forgets `common`'s engine global (through
  `_forget_common_engine`, which already existed for the swap path), the store's sessionmaker, and
  the azure blob client, whose `AsyncBlobServiceClient` and lock bind the same way and which the
  activation loop is what first opens. Reset rather than closed: `aclose_instance` needs the loop
  that has gone, and `reset_instance` is the synchronous variant the provider ships for it.

  Both halves are needed: `DbStore` caches its *sessionmaker* bound to the engine that existed
  when it was built, so `engine()` rebuilt correctly while `session()` stayed on the dead pool.
  `DbStore.forget_sessions()` drops it, and is a no-op on sqlite -- where the store owns the
  engine, so clearing the sessionmaker alone would open a second `:memory:` database -- and on an
  injected sessionmaker.

  `current_revision` takes `own_engine` for the callers that run their own loop (`check_schema`),
  and `DbStore.migration_engine()` builds from the connection string rather than resolving the
  shared engine, since resolving it is what creates it on the wrong loop. The request-path callers
  keep the pooled engine, its `connect_args` and its `application_name`.

  `migrations/env.py` picks its failure message from whether a connection was in hand, not from
  the exception's type. A wrong password and a bad revision chain are both `OperationalError` to a
  caller inspecting them, and they send the reader to opposite places; `connect_failure` and its
  new counterpart `statement_failure` share `fabric.db.dsn`'s redaction rule.

- **Plato's tables move to the default schema, the convention the estate already runs.** The five
  `plato_*` Postgres schemas were a boundary inside a boundary terraform already provides: every
  service has its own database on the shared Flexible Server. They also did not work. The models
  carry no `schema=` so they stay portable to sqlite, so the ORM emitted unqualified names against
  schema-qualified tables, and after a correct migration the runtime could not read `pack_version`
  at all. `/api/v1/database` reported "the schema may not be migrated" on a migrated database for
  the same reason.

  kernel puts everything in `public` across 84 revisions; juno runs ~35 tables inherited from a
  shared gateway schema beside its own `juno_*` ones, in one database, no schemas. The rule is
  prefix on collision, which Plato already followed for `plato_setting`. `plato/schemas.py`,
  `TABLE_SCHEMAS` and `schema_for` are gone; the projection rule they carried survives as a
  `projection_*` naming convention on `plato/models.py`.

  **sqlite gains more than Postgres.** Every schema branch was a `if dialect == "sqlite"` fork, so
  the suite (which runs sqlite) never executed the Postgres half of any of them, which is how all
  of this survived. 26 such lines are gone and the two backends now run one path. It also fixes a
  live sqlite bug: `include_object` filtered by schema, and a reflected sqlite table has none, so
  `alembic revision --autogenerate` on sqlite silently considered no tables. It now filters by the
  registered table names, identically on both.

  Verified against a real 16 cluster: migrate an empty database through `POST /v1/database/migrate`,
  tables land in `public`, `/v1/packs` reads, and `/v1/database` counts 8 of 8 with no complaint.

- **Plato's Postgres migrations could not run.** `_take_migration_lock` set its two timeouts with
  bound parameters, and a utility statement takes none: `SET lock_timeout = :value` reached the
  server as `SET lock_timeout = $1` and failed with a syntax error before any revision ran. It
  shipped in 2.5.0 and survived because the whole lock block is Postgres-only while the suite runs
  sqlite, which skips it. Now `SELECT set_config(...)`, which is a function and does take a
  parameter; verified against a real 16 cluster, where the values apply (`SHOW lock_timeout` =
  `30s`) and the chain reaches `0004_pack_version_retired_at` with all five schemas and nine
  tables.

  A source guard in `tests/test_plato_migration.py` now rejects `SET x = :param` in `env.py`,
  since nothing the suite can execute reaches that code.

  **A failure after connecting is no longer reported as a failure to connect.** `env.py` wrapped
  every exception in `connect_failure`, so the syntax error above surfaced as "could not connect to
  the database (host=... port=...)", which points at the DSN, the firewall and the credentials.
  `jazzx_sdk.fabric.db.dsn.is_connect_failure` now decides, and lives there rather than in `env.py`
  because alembic's module cannot be imported outside alembic and so cannot be tested.

- **A pack can be checked before it is served, and the bundled one was broken.** `load_pack`
  raises on the first thing wrong, which is right for a serving path and wrong for an author: a
  pack with three problems takes three attempts to find them, and the attempt happens on a
  deployed replica. Nothing checked the joins that only fail at bind time at all.

  `plato.packs.check.check_assistant_pack` collects instead of raising and goes one stage further
  than loading: the manifest parses, the profile parses, every skill the profile names is present,
  and the manifest binds against the registries the pack itself supplies. `python -m plato
  --check-pack DIR` prints the findings and exits non-zero on an error, so CI and a pre-publish
  step can gate on it. Findings reuse `PackLintFinding`, the vocabulary the domain-pack lint
  already established, so a caller checking both halves of a pack reads one shape.

  **It found a real defect on its first run, in the pack Plato ships as its default.**
  `manifest.yaml` said `profile_ref: clinical-intake`, the assistant id, while the profile carried
  `name: clinical_intake_agent`. Loading registers the profile and the skills and succeeds;
  `build_from_manifest` resolves the reference and does not, and that happens on the first chat
  turn. A replica with no configuration at all started clean, reported `configured: true`, and
  would have failed on the first message. Fixed in the manifest.

  Boot notes the same condition now. Not raised: the registries are real and the rest of the
  deployment is fine, so an unbindable pack is a readiness fact rather than a reason to refuse the
  pack. It honours `record=False`, so a runtime activation still cannot take a serving replica out
  of rotation over a pack its caller is about to be refused.

  **The bind check binds the way the replica does.** Both the boot note and `--check-pack`
  first bound without the `llm_manager` the serving path passes, so a pack declaring
  `out_of_scope_check_model` (a documented manifest field) was reported as unbindable when it
  binds correctly: at boot that reaches `/health` and takes a working replica out of rotation,
  and in CI it rejects a good pack. One shared `plato.packs.check.bind_failure` is now the only
  bind path for a caller that wants to know whether a pack would serve rather than to serve it,
  and it supplies a stand-in manager where the manifest asks for one. Neither caller keeps the
  agent it builds, and the guardrail only closes over the manager, so the check stays structural
  and needs no LLM configured.

  `--check-pack ""` now checks rather than starting the role, so an unset variable in a CI
  wrapper fails the step instead of booting a server.

- **Tool-call recall catches a narrower repeat, not just an identical one.** `recall_tool_output`
  keyed on a hash of the arguments, so it caught a file re-read whole and nothing else. The
  measured run that motivated the seam read one file across 50 distinct line ranges, most of them
  inside a range it had already read: by key alone, all 50 were misses.

  `covers` is an optional predicate over (earlier arguments, this call's arguments). The caller
  owns the rule, because only it knows which argument is a range, a page set or a filter; japes
  owns the scan. Without it the behaviour is unchanged, so a caller that supplies no rule gets no
  guessing.

  `line_range_covers` ships the rule for `read_document`, keyed on its real parameter names with
  `end_line=None` as end of file. It lived only in a test before, under argument names no tool in
  the repo uses, so no caller could have passed it.

  Two rules in the scan, both pinned by mutation. Newest first, because a wider recent result is
  likelier to still be in the model's context than an older exact one. And an empty earlier result
  never covers: there is nothing to read back, so pointing a later call at it would hide a real
  answer rather than defer it.

  A covered call is not recorded, and that is deliberate rather than an oversight: it never
  produced content, so there is nothing to point a later call at.

## [2.5.2] - unreleased

*SDK 2.5.2, Plato 0.1.4. Work lives on the `v2.5.2` branch, cut from `dev` after 2.5.1 squash-merged
(`e4eabd4`).*

- **`SourceBuilder` can canonicalise an answer's citation markers, not just read them.**
  `build` scans an answer for anchors and resolves them to grounded `Source`s. `rewrite` is the
  other direction, and the half a renderer needs: a model writes its citations in whatever
  punctuation it lands on that turn, so a consumer parsing them with a regex gets a different
  shape each time, and a prompt cannot fix that. Canonicalising the delivered text is the same
  answer this module already gives for provenance, which is never taken from the model directly.

  `render(source, token)` owns the emitted form, because what a marker must look like is the
  consumer's contract rather than this module's; a caller wanting one marker per page emits them
  itself. japes owns the parts that are the same everywhere: span tracking, replacement in
  last-match-first order so an emitted marker longer than the token it replaces does not shift
  every span after it, and absorbing decoration the model already put around the anchor rather
  than wrapping it again, which would otherwise turn an already-parenthesised citation into a
  doubly-parenthesised one and break a strict consumer regex just as badly.

  `_` is deliberately not decoration: it is a valid filename character, so stripping it would eat
  real text from a compound token with no separating space.

  Extraction has to run first, and a test pins it: rewriting replaces the anchor with the marker,
  so the raw tokens are gone from the result. `build` reads the model's answer, `rewrite` produces
  what is shipped.

- **The MCP surface works on `mcp` 2.x.** 2.0 renamed `FastMCP` to `MCPServer` and moved it from
  `mcp.server.fastmcp` to `mcp.server.mcpserver`. All four modules under `jazzx_sdk/mcp/` imported
  the old path, so on 2.x every one of them raised `ModuleNotFoundError` at import, and that took
  `jazzx_sdk.JazzXMCPServer` with it: the lazy export in `jazzx_sdk/__init__.py` defers the cost of
  that import, not its failure. `test_import_boundary`'s "every exported name actually resolves"
  caught it the moment an environment had 2.x installed.

  `jazzx_sdk/mcp/compat.py` resolves the class under either major and the modules import from
  there, so the declared floor stays a floor: no ceiling was added. Only the name and location
  moved, verified against 2.1.1 for everything japes touches, namely the positional server name,
  the `.tool()` decorator, and `run_streamable_http_async`'s `host`/`port`.

  `tests/test_mcp_server.py` drove `ToolManager.call_tool` directly, which gained a required
  `context` parameter in 2.x. The 15 call sites go through one helper that decides from the
  signature, rather than the suite being pinned to whichever major happens to be installed.

- **A migration that cannot reach the database says which database.** `alembic -c
  plato/alembic.ini upgrade head` against an unreachable host emitted about a hundred lines of
  driver internals ending in a bare `TimeoutError`, naming no host, no port and no database. That
  is the only question worth asking when a migration will not run, and the engine already holds
  the answer. It is also the command `schema_version` tells an operator to copy and paste, so the
  raw traceback is what they meet.

  `fabric.db.dsn.connect_failure` builds the message from `dsn_summary`, which is where the
  never-carry-the-DSN rule already lives because it carries the password. `run_migrations_online`
  wraps the connect and re-raises with it, chained from the original so nothing is swallowed. Both
  migration paths go through that function, so the in-process `job:migrate` gets it too.

  A timeout earns one extra sentence and nothing else does: it is the shape that looks like a code
  fault and is not, because the socket opened and the handshake never completed, which makes it the
  network path rather than the credentials or the database name. A refusal or an auth failure
  reports itself by name already, and adding a guess there would mislead.

- **The Azure DocIntel tests run with the extra installed too.** They only ever ran without it.
  `analyze` builds a real `AnalyzeDocumentRequest` when `azure-ai-documentintelligence` is present
  and falls back to a dict when it is not, and the assertions subscripted the body, so installing
  the extra turned two passing tests into `KeyError: 'bytes_source'`. A third asserted the
  "install the extra" error while depending on the extra genuinely being absent, so with it
  installed it built a real client and reached `DefaultAzureCredential` against the network.

  The assertions read the field from either shape now, and the absence is simulated rather than
  inherited from the environment. Verified both ways: without the package, and with the request
  model stubbed in. Reverting the accessor fails the two tests under the stub, which is the
  environment that reported them.

  Two corrections to that simulation, from review. It blocked `azure.identity`, which is a
  mandatory dependency (`pyproject.toml:31`) rather than part of the `azure` extra, so it stood in
  for a state no install can reach; and it did not block the `.models` submodule, which a dotted
  import resolves against before its parent. It now blocks the two names the extra actually
  provides.

  CI never installed the `azure` extra, so the request-model branch had no coverage there and the
  fix was only ever exercised on a developer machine. `tests.yml` installs it now, the pre-push
  hook's `CI_EXTRAS` moves with it, and `azure` comes off the excluded list in
  `test_ci_extras_coverage` -- its reason there, "gates no tests", had stopped being true. That
  guard is what caught the omission, which is what it exists for. The workflow comment said
  `azure` stayed out, one line above the command that installs it, and now carries its reason
  beside the others.

  The coverage gap moved rather than closed, and a `TODO(dict-arm-now-uncovered)` says so: with
  the extra installed, the dict fallback is the arm CI no longer reaches. It is reachable in
  production only by an install without the extra that also injects a client, and there is no
  such caller here.

  The subset guard now runs over both exclusions that claim to be a strict subset of `plato`
  rather than `bpmn` alone; `telemetry` made the same claim and nothing checked it. Adding a
  package to `telemetry` that `plato` lacks fails it.

- **`anyio >=4.14.2`.** Two Dependabot alerts on the default branch, one critical
  (GHSA-82r6-8w77-94w6, GHSA-5p39-cfhj-2xmp). Transitive only, and widely so: httpx, openai,
  anthropic, starlette, sse-starlette, mcp, google-genai and watchfiles all pull it, with the
  lock sitting at 4.11.0.

  A floor in `pyproject.toml` rather than a lock bump, which is the shape the rest of that block
  uses and the correction the soupsieve review made: an install that does not consume this lock
  resolves the package freshly, and no dependent caps it below the fix (the tightest are `<5`),
  so the floor is the constraint that actually holds. The relock moved anyio and nothing else.

- **`PROJECT_NAME` defaults to `japes-plato`.** Every japes consumer carries the japes prefix
  across the platform, so the container app is `dev-env-jaxi-japes-plato`, the image is
  `ghcr.io/jazzx-llc/japes-plato`, the database is `japes_plato_db` and the pack-archive container
  is `japes-plato`. The one place that still said plain `plato` was the service's own name.

  It matters because `CommonSettings` resolves the OTEL service name as `app_name or project_name`.
  A deployment that sets `APP_NAME` never noticed, which is every one that exists today; one that
  does not would report itself under a name the rest of the platform does not use.

  The test that pinned the old value now reads it from `COMMON_DEFAULTS` rather than spelling it
  again. A second copy of a name is how a rename lands in the code and leaves a test asserting the
  old one, which is what happened here: two assertions, one updated and one missed on the first
  pass.

- **A tool call this run already made comes back as a marker, not a second copy.**
  `tools/agent/tool_compression` already owned one half of this: an output too big to sit in
  context goes to a run-scoped `ReferenceStore` and comes back as a preview plus a
  `read_reference` id. `tool_recall` is the other half, and it is a different problem: a small
  output repeated ninety times costs more than a large one returned once, because each result
  becomes another conversation item re-sent on every later turn.

  The shape came from a measured agent run: about three quarters of file reads re-read a file the
  same run had already read, and those repeats were roughly half of all tool-output bytes; a
  similar share of searches re-ran a query already run; and an empty result invited a reworded
  retry of the same term. The calls themselves are milliseconds, so the cost is entirely the
  prompt they accumulate in.

  `recall_scope` plus `recall_tool_output(text, tool=, arguments=)`. A repeat returns a marker
  naming the `read_reference` id of the first result, so nothing is lost. An empty result is
  recalled as "already tried these arguments and matched nothing" rather than as a reference to
  nothing, which is the case that was inviting the reworded retry. Argument order does not defeat
  the key. Outside a scope it is the identity function, so a client that has not opted in is
  unaffected.

  A recall scope joins an enclosing compression scope rather than opening a competing one, so one
  `read_reference` expands markers from either half. That is why `active_reference_store()` is now
  exported: it is how the second seam finds the first one's store.

  **It also found a real defect in the first seam.** `compression_scope(store)` read
  `store or ReferenceStore()`, and `ReferenceStore` defines `__len__`, so an empty store is falsy
  and a caller-supplied one was silently replaced by a fresh one at every scope open, which is
  exactly when it is empty. Every reference written afterwards went somewhere the caller could not
  read. Fixed to `is not None`, with the same trap avoided in both new constructors.

  The pattern `x or SomeDefault()` appears at 27 sites in `jazzx_sdk`, and it only bites where the
  supplied object is falsy when empty. Every other default-able class at those sites (tracers,
  providers, config and key objects) defines neither `__len__` nor `__bool__`, so they are always
  truthy and always used. The two stores in this seam were the exception.

- **A turn that stops to ask reports the choice as data.** `InteractiveResponse` carried
  `blocked`, `incomplete`, `cancelled` and `truncated`, and nothing for "this turn needs a human
  to pick". An agent that had to ask ended its turn with the question inside `answer`, leaving
  every caller to parse prose to discover that it was asked at all, what the options were, and
  which one the agent preferred.

  `needs_decision: list[Decision]`, each a question plus ranked `DecisionOption(value, label,
  description, recommended)`. `outcome` gains `"needs_decision"`, placed after `refused` and
  before `incomplete`: a turn that stopped to ask reached a decision point, and reporting it as
  incomplete would put it in the same bucket as a loop that ran out of turns.

  The paired invariant is the part worth having: `output` is forced to None whenever
  `needs_decision` is non-empty, so a partial structured result can never be read as a finished
  one while the turn is still waiting to be told what to produce. `answer` still carries the
  question in prose for a caller that renders text only.

- **One history per turn.** The gate classified `turn.message` alone while the answer ran against
  store-loaded history, so two stages of one turn disagreed about what the conversation was, and a
  follow-up whose meaning lived in the conversation ("and for a condo?") was judged as if it had
  arrived cold. `ChatTurn` carries `history` now, and `turn_messages` is what every stage reads.

  Injectable rather than only store-resolved, because a real assistant's conversation often lives
  outside japes -- an assistant API, a KH conversation -- and its agent runs with no session at all.
  Supplying both is refused loudly: the store would prepend its own copy and the turn would answer
  over every message twice, which is unattributable afterwards. A turn that supplies nothing is
  unchanged.

  The budget is UTF-8 bytes over `history + [question]` together, applied once. Trimming the
  question separately lets a turn exceed the budget by exactly what the user just typed, and bytes
  rather than characters because a non-ASCII conversation costs up to four times what a character
  count suggests. `ByteBudgetStrategy` (registered as `byte_budget`) is the reusable half; japes
  had no size-based compaction at all, only turn-count and structural.

  The gate sees a small window rather than all of it, defaulting to two exchanges: more history
  resolves a follow-up and *hurts* scope drift, since a gate handed a wholly in-scope conversation
  routes an out-of-scope outlier as in-scope. The classifier prompt now says which message it is
  scoring, having said "the user's message" in the singular while being handed several.

- **Plato's links follow the gateway mount.** A gateway that routes `/plato` to the container
  strips the prefix before forwarding, so the routes sit at `/api/v1` while the browser's address
  bar says `/plato/api/v1`. Every link the pages emit was absolute and unaware of it: the nav,
  `/docs`, `/health`, `/openapi.json` and the `__API_PREFIX__` the dashboard's own fetches are
  built from. The page would load and every link on it would leave the mount.

  `prefix.mount_prefix(request)` reads `X-Forwarded-Prefix` and the render functions take a
  `mount` they prepend. Routing is untouched, because the prefix is stripped before Plato sees it;
  only link generation changes. The header is client-supplied and lands inside an href, so it is
  accepted only as plain `/segment` parts and anything else reads as absent, degrading to the
  links a direct visit needs.

  Not moved into `jazzx_sdk`: nothing there serves HTML with absolute links, so there is no second
  caller yet. It moves the day one appears. Most services need none of this -- a JSON API emits no
  links, which is why they route today with no equivalent code; Plato is the odd one because it
  ships a dashboard.

  The first cut fixed four of the six `HTMLResponse` sites. The packs page and the degraded
  replica's dashboard kept emitting unprefixed links, so the nav link the fixed dashboard now
  points at led to a page whose own `fetch` left the mount and rendered a 404. The sweep that
  missed them checked `/` alone; it is parametrized over every HTML page now, asserts the
  `const PREFIX` the pages' fetches are built from, and covers the degraded dashboard separately
  since `create_plato_app` does not serve it. Both defects fail it when reverted.

  The degraded dashboard registers through `app.add_route` rather than `@app.get`: it is the one
  route there that needs the request, every fastapi import in `plato/__main__.py` is function-local
  so a `job:*` role never pays for the server stack, and FastAPI resolves annotations against
  module globals -- so `request: Request` read as a query parameter and answered 422.

- **Plato has a mark, from one source.** A portico: Material Icons' `AccountBalance` (Apache 2.0),
  which is the Greek reference the name asks for and, in this domain, the finance glyph too. It
  replaces a blue circle that had been copy-pasted into four files.

  Still inlined, which was the right call and stays one: a `<link>` to a file costs a request per
  page, and no link at all costs a `/favicon.ico` 404 per load. What changes is that the four
  copies become `FAVICON`, fed through the same `__PLACEHOLDER__` mechanism the nav already uses.
  `static/logo.svg` carries the same path for use outside the served pages, and a test holds the
  two together.

- **The streaming chat turn is a real pipeline.** `stream_chat_turn` ran `validate` and `gate`
  through the conductor and then branched by hand, so `ground` and `finalize` did not exist while
  streaming and no step could be overridden. A consumer with post-answer work -- citations,
  persistence, an output check -- had nowhere to put it, which is most of why the canonical
  assistant hand-rolls its turn instead of adopting this.

  `answer_stream_step` resolves the contract mismatch: a conductor step emits one value and a token
  stream is many, so the deltas leave through a sink and the step returns what the stream
  assembled. Every stage then runs on both paths, and `stream_chat_turn` takes the same
  `components` dict `run_chat_turn` does. The sink is the caller's: a turn produces a result and an
  adapter delivers it, so the pipeline decides when to publish and never how.

  Publishing is a rendezvous rather than a buffer -- the sink waits for the consumer to have
  yielded, not merely taken. Any buffering lets the answer step finish the whole stream before a
  `cancel` set mid-read is observed, turning a barge-in into a fully delivered answer. Only the
  reference `answer` impl is swapped for the streaming one, so a caller's own component survives.

- **`InteractiveResponse.outcome`.** `blocked`, `incomplete` and `cancelled` are independent, so a
  response can carry more than one and every adapter decided precedence for itself. One property
  resolves it: cancellation wins, then refusal, then incompleteness.

- **Plato 0.1.4 -- `PLATO_WIRING` values must change.** `plato.wiring_default:build` is now
  `plato.wiring.default:build`, and `plato.wiring_local:build` is `plato.wiring.local:build`. No
  compatibility shim: there is one deployment and we own it, so a flag day beats carrying two
  paths. An unmigrated value fails loudly rather than quietly -- `load_wiring` raises
  `WiringError`, a `job:*` role exits 4 and a serving replica comes up on `/info` with the reason,
  which is what the boot contract is for.

  `plato/` had 27 modules and 6,171 lines flat at its root. Now ten, with `api/` (the eight
  routers, `_api` suffix dropped on the way in), `boot/` (the contract, posture and schema check
  `__main__` consults before serving), `auth/` (oidc and tenancy), and `wiring/` (the contract plus
  the two shipped implementations; the contract is re-exported so `from plato.wiring import
  PlatoWiring` is unchanged, while `default` and `local` deliberately are not -- importing one by
  accident is how a local wiring reaches a deployed process). `migration/` became `kernel_sync/`,
  because a data migration off kernel and the alembic `migrations/` tree next door are not the
  same kind of thing and the names differed by one letter.

  Three modules located files relative to their own `__file__` and silently pointed one level too
  deep once moved: the info router's `static/` pages and `guide.md`, and two separate resolutions
  of `alembic.ini`. Each names the package root once now rather than repeating the assumption per
  asset. The suite caught all three, which is the argument for moving in steps.

- **A connection string that does not parse can be corrected without a redeploy.** SQLAlchemy
  answers every malformed value with one sentence -- "Could not parse SQLAlchemy URL from given URL
  string" -- and omits the value, correctly, because it carries a password. So an empty string, a
  missing `postgresql+asyncpg://` scheme, a libpq `host=... dbname=...` string, an ADO
  `Server=...;Database=...` one, a value the deployment wrapped in quotes and an unsubstituted
  `<placeholder>` were the same line in the log, with nothing to act on.

  `connection_string_complaint()` describes the shape and never the value, and the schema refusal
  carries it, so `/info` and the startup log say which of those it is. Two tests hold the safety
  property: no complaint may contain the configured string, asserted over the whole case list so a
  branch added later is covered. It lives in the wiring rather than beside `check_schema`, because
  that module reads no environment variable by design -- an escape hatch on a safety check outlives
  the incident it was added for -- and describing a misconfiguration means reading two.

  The backend's default is the posture's, not a constant: sqlite on a laptop, `common` deployed. Two
  sites already spelled that and a third copy would have complained about a missing
  `DB_ASYNC_CONNECTION_STR` on every local run, so it is `resolved_db_backend()` now.

  **And the variable is editable.** It joins `BOOTSTRAP_KEYS` and the settings catalogue, marked
  secret so the GET masks it, which is what makes the fix reachable: the surface that repairs a
  broken database must not itself need one. Applying it clears `common`'s two module-level memos --
  the settings object *and* the engine -- without which a swap rebuilt the `DbStore` and handed it
  back the engine built from the old string. A failed swap leaves the serving store alone, since
  `DbStore` caches its own sessionmaker and a store that never built one has nothing to lose.

- **The image bundles an assistant pack, so a replica serves something with no configuration.**
  `PLATO_PACK_DIR` had no default and could not have had one: the two bundled `seed_packs` are
  *domain* packs -- `pack_manifest.yaml`, no `profile/` -- which `plato.packs.loader` refuses, and
  `plato.wiring.local`'s demo profile defaults to a sibling checkout absent from every container.
  So the degraded note pointed an operator at a wiring that could not help, and nothing in the
  artefact could satisfy the variable.

  `plato/data/demo_pack` is a frozen snapshot of jaci's `clinical-intake-core/agent` -- two
  declarative skills, a persona, no Python bindings, which is why it loads in a japes-only process
  where `ci-spread-core` needed its `jaci.*` bindings stripped. Clinical rather than a lending
  domain because it was the only pack in jaci with an agent profile at all; `dscr_core`,
  `cre_underwriting_core`, `aml_investigation_core` and `insurance_diligence_core` carry no
  `profile.yaml` in any layout, and authoring a DSCR persona here would have meant inventing
  credit-analysis content owned elsewhere.

  **Frozen deliberately**, which is not the debt `TODO(seed-pack-vendoring)` records next door:
  those snapshots track packs somebody is still editing, and this one tracks nothing. It exists so
  a replica has an assistant before a deployment publishes its own, and activation supersedes it.
  The only reason to touch it is a format change -- a required field added to `AssistantManifest`,
  or a change to what a profile must contain -- and `test_the_bundled_demo_pack_loads` is what
  reports that, since a silently unloadable default reads as a correctly set variable.

  Its `manifest.yaml` is generated through `jazzx_sdk.manifest.AssistantManifest` rather than
  written by hand: eight fields are required and a hand-rolled file failed validation on all eight.

- **A pack can be uploaded.** `POST {prefix}/packs` takes a multipart `.zip`, reads the manifest
  from it and publishes it as a new version. The store layer already did the work -- content-
  addressed blobs with dedup, immutable versions, member-path checks before extraction -- so what
  was missing was the ingress: a pack authored offline had no way in but the bundled-seed route.

  `manifest_from_archive` sits beside `pack_archive` in `jazzx_sdk.pack.store`, for the reason that
  function's docstring already gives: the archive shape is the store's contract, and a reader living
  in a consumer is a reader that drifts from the writer. It also carries the decompression cap,
  which is where a bomb can still be refused cheaply -- the existing member-path check is the
  traversal defence and was never a decompression one.

  **Not `relaxed_only`, unlike seeding and deletion.** A pack is authored offline and arrives
  continuously, production included, so a rule that refuses outside local and dev-daily is a
  registry nobody can fill. Upload takes `/config`'s rule instead: accepted in any posture once the
  deployment supplies an auth dependency. No shipped wiring sets one, so the 403 names exactly that
  rather than leaving an operator to guess.

  **Publishing is not activating**, deliberately: the version lands in the store and nothing that is
  serving changes, so a pack can be pushed without coordinating with a release and a rollback is
  re-activating a predecessor. Activation is the second step and ships in this release, below.

  What stops an archive surviving is three conditions, not one, and the guard now asks all three
  through `pack_archive_complaint()`. Keying on the backend alone let `PLATO_PACK_BLOB_BACKEND=azure`
  with no `STORAGE__CONNECTION_STRING` past it: the upload then reached `common.core.storage`, which
  raises `Azure Storage connection string is required` on the *write*, from a module with no idea it
  was serving a Plato route -- after Plato had told the caller its own check was satisfied. The
  container name is the third. `_pack_blob` warns about the missing credential at boot too, because
  that raise otherwise waits for the first publish, which on a relaxed-only route may be weeks.

  `pack_archives_are_durable()` stays as it was and keeps keying on the backend name, deliberately:
  it answers *which store to build*, and falling back to local because credentials are absent would
  write archives to container disk and report success -- the silent loss the whole guard exists to
  prevent. Raising there is the better failure; the complaint is the other question.

  The durability refusal asks `pack_archives_are_durable()`, exported from `plato.wiring.default`
  beside the store it guards, rather than testing the backend string for `"local"`. That spelling
  is the bug `_pack_blob`'s own comment records having already fixed once: `BlobStore` treats every
  non-`azure` value as local, so `Azure` with a capital or `azure-blob` would have passed the guard
  and still written to the container filesystem with `has_archive: true` on the row.

  `manifest_from_archive` also runs `_unpack`'s member-path check, not just its manifest search.
  Without it an archive holding a `../escaped.yaml` parsed, published, and then raised on every
  `materialize` -- a version number permanently burned on a pack that can never be served, with the
  row immutable. And everything `zipfile.read` raises becomes a `ValueError`: an encrypted member is
  a `RuntimeError`, an unsupported compression method a `NotImplementedError`, a bad CRC a
  `BadZipFile`, so a password-protected upload answered 500 with a traceback instead of naming the
  problem with the file.

  Two refusals worth naming. An upload over `PLATO_PACK_UPLOAD_MAX_BYTES` answers 413, measured
  while reading rather than trusted from `Content-Length`, because the archive is resident twice --
  once in the route, once in `_unpack`'s `BytesIO`. And an upload on a deployed tier whose
  `PLATO_PACK_BLOB_BACKEND` is still local answers 503: the bytes would go to a filesystem that does
  not survive a restart while the row would, and this route is the only place that can be enforced,
  since `_pack_blob`'s boot note is deliberately outside the readiness list.

- **`dev` is a deployed tier now, reading as `dev-daily`.** It mapped to `local`, on the grounds
  that it reads as "my laptop" and means that in jaci's `.env.template`. The reversal is about who
  can fix each mistake. A cloud container is provisioned by another team, so the tier variable it
  carries is whatever their convention sets -- and `dev` resolving to local left a deployed replica
  with identity off, the sqlite fallback in place of Postgres and every deployed-only readiness
  check skipped, while `/info` reported `environment: local`. Correcting that meant asking for a
  per-service variable and waiting. A laptop is the machine its owner edits, so the same mistake
  there is one line in a file they already control: `local`.

  `test` stays local, deliberately -- nothing provisions a container as `test`, so the asymmetry
  with `dev` is the point rather than an inconsistency.

  **Two variables that disagree now resolve to the stronger tier, not the first one set.** That was
  a safety property the old mapping supplied by accident: `environment_tier` took the first
  *deployed* signal, which covered the masking case only while every alias below `dev-daily` was
  non-deployed. With `dev` deployed, `JAPES_ENVIRONMENT=dev` beside `ENVIRONMENT=production` would
  have answered `dev` and run a production replica relaxed. `_strongest_signal` is the one reader
  both `environment_tier` and `deployed_posture` go through; ties keep variable order, so the list
  still expresses precedence between equals. Two existing tests pinned the masking case and pass
  unchanged, which is what says the property survived rather than being restated.

  **`JAPESSettings` no longer fills in localhost URLs for `dev`.** Three validators returned
  `http://localhost:8000` / `:8001` / `:8080` for the Knowledge Hub, kernel and process URLs on the
  premise that `dev` was a laptop. Left in place, a deployed replica would look configured to every
  check that asks whether a URL is *set* and answer from nothing -- the silent-success shape this
  release has been removing elsewhere. They return empty now, so the gap is reported.

  The same three now resolve the tier through `tier_of` rather than comparing the configured string,
  which fixes a defect that predates this release: they tested `env == "prod"`, so `production` --
  the canonical name, and the one the field's own documentation recommends -- filled in nothing
  while `prod` filled in the production URLs. `tier_of` is also what `strict_for` had spelt inline,
  so there is now one place a configured name becomes a tier.

  A laptop still on `JAPES_ENVIRONMENT=dev` will start demanding Postgres, a tenant list and
  `X-Tenant-Id` per request, and will report the gaps at `/info` rather than serving quietly.
  jaci's `.env.template` carries `JAPES_ENVIRONMENT=dev` and wants `local`.

- **`/info` says which container is answering.** Everything it reported described the *image* --
  versions, commit, tier, schema revision -- and two revisions of one Container App report all of
  them identically. So an operator holding the environment of a container deployed months earlier
  had nothing to contradict it, and a debugging session drew every conclusion from the wrong
  replica. `config.host` adds the container app's name, its revision, the replica name, `APP_NAME`
  and the hostname, rendered as a Host card on the details page.

  Safe unauthenticated, which this route has to be: `/info` is the one router without the
  `withholding` gate, deliberately, because it is what an operator reads when a replica will not
  start -- exactly when no identity middleware is running and no `auth` dependency exists to unlock
  anything. The block is names and a revision string. The hostname is reported only on a container
  platform, where it *is* the replica name; on a laptop it is the name of somebody's machine, which
  an open endpoint has no business publishing.

  **An unlabelled container is `dev-daily` now, not `local`.** Nothing set resolved to `local`,
  which is the right default for a laptop and permissive everywhere else: identity stops being
  required, the posture-gated readiness checks are skipped, and each consumer reading
  `deployed_posture()` takes its local branch. The only symptom was `/info` reporting
  `environment: local` -- also what a correct laptop reports, so there was nothing to notice. The
  deployment that ran this way had `JAPES_ENVIRONMENT` *declared and empty*, and a blank value is
  not-configured everywhere else here (`env_text`), so it is not-configured for this too.

  An injected platform variable (`CONTAINER_APP_NAME` and its siblings, or
  `KUBERNETES_SERVICE_HOST`) *proves* the process is in a container, so the promotion rests on
  evidence rather than a guess. **It stops at `dev-daily`, and that ceiling is the whole safety
  argument**: dev-daily is deployed but relaxed, so an inferred tier can only add refusals and
  reports -- it cannot open anything, and it cannot refuse a boot. `staging` and `production` are
  never inferred, because `check_settings` *does* refuse a strict tier with identity off and a
  guess must not be able to do that; a container at either must name it. `JAPES_ENVIRONMENT=local`
  is the opt-out, and a named tier always wins over the inference.

  The tier is not read from the container's **name**, only from the platform variables' presence. A
  container app's name is chosen by whoever provisioned it and validated by nothing, so reading a
  tier out of it would make renaming the app -- an ordinary action taken for unrelated reasons -- a
  change to that deployment's security posture. It is also not the tier: dev-daily's own app is
  `dev-env-jaxi-japes-plato`, where `dev-env` is the Azure environment's resource name.

  `check_settings` still logs that the tier was inferred, and `/info` carries the sentence beside
  the identity that makes it legible. That warning sits *before* the posture branch rather than
  inside its `not posture` arm -- an inferred tier is a deployed posture, so the arm it used to
  live in is no longer reached on the deployment it was written for.

  `.env.dev-daily` is a review list rather than a set of instructions now: the container is
  terraform-managed (`japes_plato_*` in `module-dev/aca`, values in `Jazzx/jaxi/dev` on the `dev`
  branch), and an `azurerm_container_app` env list is declarative -- so a variable entered by hand
  in the portal and absent from the module is removed by the next apply. Which makes anything in
  that file terraform does not set a gap in the module, and one was: `OTEL_SAMPLER_RATIO`. Plato is
  the only container app in that module with no env block for it, the environment already sets the
  module-wide variable to `0.2`, and the application's own default is `1.0` -- so an apply would
  have dropped the hand-entered value and started tracing every request. The database name was
  wrong here too: the postgres module creates `japes_plato_db`, and this file and the deployment
  doc both said `plato_db`, which nothing creates.

  `.env.dev-daily` now marks which of its assignments restate a code default (`PLATO_DB_BACKEND`
  on a deployed tier, `OTEL_SERVICE_NAMESPACE`, `ENABLE_TELEMETRY`) and which are load-bearing
  (`JAPES_RUN_MODE`, whose default is `queue`; `OTEL_SAMPLER_RATIO`, whose default traces every
  request). A test holds each marker against whatever declares the default, so a changed default
  cannot leave a false claim in the file devops works from -- and the marker sits on the comment
  line above, never inline, because an inline comment in that file would be pasted into the value.

- **Activating a published pack, without a restart.** The store held versions nobody could serve:
  `PLATO_PACK_DIR` is a filesystem path read once at boot and the pack store knew nothing about it,
  so `docs/plans/plan_pack_upload.md` §4c's two missing halves -- a pointer saying which published
  version this deployment serves, and a reload -- were what stood between an upload and a running
  assistant. `POST {prefix}/packs/{pack_id}/{version}/activate` is both.

  `PLATO_ACTIVE_PACK` is the pointer, `[tenant/]pack_id/version`, and it is durable rather than
  in-process: the activation outlives the replica that made it, so a restart serves the same version
  instead of falling back to whatever path the container was built with. The tenant may be omitted
  and fills with `DEFAULT_TENANT`, which is where a pack published without one already lands, rather
  than a fourth sentinel beside `PLATFORM_TENANT` and the two local ones. Read-only on `/config`: a
  PATCH there would move the pointer and keep serving the old pack.

  The reload is a rebinding, not a restart. `registries=` is handed to `AssistantRuntime` as a
  lambda closing over two names, so replacing them is visible to the next request and to nothing in
  flight -- the same shape `DatabaseHandle` uses for the store, and the reason neither needs a lock.
  The version is materialised through the pack store's digest-keyed cache rather than copied, so
  activating a version twice is a cache hit and activating one whose blob is gone raises rather than
  serving a stale tree.

  **Rebinding the pair was not enough, and the doc said it was.** `AssistantRuntime` consults
  `registries` on a cache miss only, so every assistant a replica had already answered a turn for
  stayed bound to the retired pack's profile and skills: the route answered `activated: true`, the
  pointer moved, and a warm replica kept serving the pack the operator had just rolled back from --
  an apparently-applied rollback, which is worse than a refused one. `invalidate_all()` is the
  missing half. `invalidate` could not express it: the stale set is not one assistant's, it is
  everything bound against the previous registries. It also fixes the effect's scope in
  `docs/DEPLOYMENT_ENV.md`, which claimed immediacy "because the runtime resolves its registries per
  request" -- and states the honest limit, that activation reloads **the replica that served the
  request** and the others pick the version up when they next restart.

  Two refusals. A version that loads to no assistants is declined rather than swapped in: replacing
  a serving pack with an empty one takes a replica from answering to answering 503, which is worse
  than a 409 saying so. And a failed activation records no boot note -- the third instance in this
  release of one rule. `_registries` notes when a pack will not load, which is right at boot and
  wrong at runtime: the previous pack is still serving correctly, but a note reaches
  `readiness_provider`, `/health` answers `ready: false`, and `_WIRING_NOTES` clears only at the top
  of `build()` -- so one operator trying a bad pack would have taken the replica out of rotation for
  the life of the process. The boot path still notes, deliberately: there the deployment is serving
  assistants it did not choose.

  `docs/DEPLOYMENT_ENV.md` is now held against the code rather than maintained by hand. Every key
  `plato_settings_catalog()` and `plato.defaults` expose must appear there, one test case per
  variable. It found `JAPES_SPAN_TEXT_MAX_CHARS` undocumented on its first run, and it matches
  variable *tokens* rather than searching the file for a substring -- a substring passes for a key
  that is a strict prefix of a documented one, and for one mentioned only in a sentence saying it is
  unsupported.

- **The vendored `common`'s dependencies are declared, and checked.** `common` is a git submodule
  japes *packages* (`{include = "common"}`) rather than takes as a path dependency -- it cannot be
  one, since `common/pyproject.toml` sets `package-mode = false` -- so poetry never reads its ~60
  declared dependencies and japes re-declares by hand the subset its own code reaches. Five were
  missing.

  The one that shipped: `common/core/db.py` imports `sqlmodel`, and it is the module `fabric.db`
  loads for the `common` backend -- `DbStore`'s default and Plato's deployed one. Every database
  question on the deployed replica answered `ModuleNotFoundError`, reported as a degradation rather
  than raised, so the image built, started, passed the Dockerfile's import check and served. Schema
  unverifiable, pack inventory unavailable, seeding failed, durable settings unreadable: one missing
  distribution behind all of it.

  The others were dormant. `common/utils/telemetry.py` imports `azure-monitor-opentelemetry-exporter`
  and `opentelemetry-exporter-otlp-proto-http` at module level with no guard, on a path
  `CommonSettings` construction reaches whenever `enable_telemetry` is true -- which is its default,
  so that container could not have telemetry switched on without dying at import. `fabric.blob`
  reaches `azure-storage-blob`, whose sibling `azure-storage-queue` was declared and it was not.

  **Four of the five are extras, not core dependencies**, and the split is drawn on whether absence
  is survivable. Every japes caller of `common.utils.telemetry` guards `ImportError` and logs --
  `observability/trace_context.py`, `observability/telemetry.py` -- and `common/core/__init__.py`
  wraps its own auto-setup the same way, so the three OpenTelemetry/Azure Monitor distributions cost
  telemetry when absent and break nothing. `azure-storage-blob` sits behind
  `BlobStore._backend == "azure"`, which a deployment opts into. All four are in the `plato` extra
  (and a `telemetry` extra for a consumer who wants Application Insights without the rest), so the
  image and CI still install and check them, while jaci, k9 and macer stop carrying an Azure
  Monitor exporter for an SDK they use without it.

  `sqlmodel` stays core, and that is the same test giving the opposite answer:
  `DbStore._sessionmaker` does *not* guard, and `common` is `DbStore`'s default backend, so a
  consumer that installs no extra and calls `DbStore()` gets exactly the `ModuleNotFoundError` this
  work removed.

  A fifth followed from fixing the detector: `opentelemetry-instrumentation` is the base API and
  ships no FastAPI instrumentor, so declaring it covered `common/utils/telemetry.py`'s unguarded
  `FastAPIInstrumentor` import not at all. Every image built so far had telemetry dead behind one
  logged `ImportError`, and the in-image check that would have caught it could not have built.

  A test now does mechanically what nobody was doing by memory: parse every `common` module japes
  imports at runtime, follow its imports transitively -- relative forms resolved, since `common`
  wires most of its own graph that way -- and assert each third-party module resolves. Imports the
  code guards behind `try`/`except ImportError` are treated as the declared optionals they are, as
  are `if TYPE_CHECKING:` blocks and japes' own extras. The Dockerfile's build check now imports the
  module behind each of the five, so this class of gap fails the build rather than the deployment.

  The sweep asserts against **what the image installs**, not against the venv running pytest. Importability
  alone is the wrong question: the image installs `--only main` from the lock, so a module that
  resolves for a developer because a standalone wheel happens to be sitting in their environment
  passes an import check and fails the build -- which is exactly how the FastAPI instrumentor hid.
  Each reached module is attributed to a distribution through its own file, since no rule turns
  `opentelemetry.instrumentation.fastapi` into `opentelemetry-instrumentation-fastapi` while
  `opentelemetry.instrumentation.logging` comes from `opentelemetry-instrumentation`. "What the
  image installs" is resolved rather than approximated: every `name =` in the lock counts the dev
  group and the extras `--extras plato` omits, so the set is the transitive closure of the main
  dependency table over the lock's own graph, with markers evaluated the way
  `test_ci_extras_coverage` already evaluates them. A namespace package is left unattributed
  instead of credited to whichever distribution the filesystem lists first.

- **A durable layer that is down says so once.** The warning was emitted per read, and
  `settings_api` reads twice per `GET /config` -- once for the ETag, once for the body -- so a
  dashboard polling a replica whose database could not be reached filled all 500 lines of the log
  buffer with one sentence and pushed out the tracebacks that explained it. Deduped on the failure
  *reason* rather than a flag, so a durable layer that starts failing a new way is still reported,
  with an `info` line when it comes back.

- **A Plato deployment sets one variable.** `CommonSettings` declares `api_v1_prefix`, `debug`,
  `project_name`, `version` and `description` with no defaults, so a container missing any of them
  died with a pydantic validation error naming the field -- which reads as nothing like the missing
  configuration it is. All five are Plato's own identity or the prefix every sibling service
  already uses, so `plato/defaults.py` supplies them, applied from `plato/__init__.py`: the only
  module guaranteed to run before anything reaches `common.core`.

  `PLATO_WIRING` joins them, defaulting to `plato.wiring.default:build`. Unset, it produced a
  replica serving `/info` alone -- and so no database, no settings store, and nothing an operator
  could correct from the dashboard, which is the surface that exists to correct exactly this. A
  deployment naming its own factory still wins, and the boot contract's row now describes a spec
  that will not import rather than an absent one.

  `DB_ASYNC_CONNECTION_STR` deliberately gets none: a default there points a replica at a database
  nobody chose, and refusing to start is the better answer to that. A variable declared and left
  blank counts as unset throughout, so a container platform rendering an empty declaration as `""`
  gets the default rather than an empty `project_name` reported as configured.

- **Plato migrates itself.** `job:migrate` and `POST {prefix}/database/migrate` run the migrations
  the image carries, so bringing a database to head needs neither a shell on the container nor a
  separate job definition -- the replica already holds the migration tree, `alembic.ini` and the
  credentials it connects with. The endpoint reports `expected`, `before`, `after` and `applied`,
  answers 503 where the wiring names no database, and is confined to relaxed postures the way pack
  seeding is: a migration is irreversible, and the tier gate is what keeps the route from existing
  in staging or production at all. Concurrency is `migrations/env.py`'s advisory lock -- several
  replicas asked at once serialise, and all but the first find the work done.

  `job:migrate` is the one role exempt from the stale-schema refusal every other `job:*` takes,
  because a job whose whole purpose is to end that state cannot be refused for being in it. The
  boot contract row names the exemption rather than leaving the rendered table claiming an exit
  the code does not take.

  Running alembic in-process applies `alembic.ini`'s logging section, whose `disable_existing_loggers`
  defaults to true and switches off every logger the ini does not name -- which is every `plato.*`
  and `jazzx_sdk.*` one. A replica that migrated from the dashboard would have served the rest of
  its life silently, and the first symptom would have been an incident with no logs. The caller
  opts out through `config.attributes` now, and the command-line path stops disabling loggers it
  never configured.

  `upgrade_to_head(db)` migrates the `db` it is handed. `migrations/env.py` resolved its own store
  from the environment, so the database that got migrated and the database that got reported could
  be two different ones: with `PLATO_DB_BACKEND=sqlite` and no path they are separate `:memory:`
  databases, the whole chain applied to a throwaway, and the read-back reported the untouched one.
  The store identity travels through `config.attributes` -- an equivalent store rather than that
  store, since alembic runs in its own thread and an async engine cannot cross event loops -- and
  `DbStore` grew the `backend`/`sqlite_path` accessors that makes it possible. The version table's
  schema now follows the dialect of the connection in hand rather than re-reading
  `PLATO_DB_BACKEND`, which was the same second source of truth one level down.

  And reaching a revision that is not head is a failure. `None` means "never migrated", which is
  the one value that cannot be the outcome of a successful upgrade, yet `before == after == None`
  read as "nothing to apply" with exit 0 and HTTP 200 -- so an operator running `job:migrate` to
  clear the exit-5 refusal saw success and watched the next job exit 5 again. `upgrade_to_head`
  raises `SchemaStaleError`, because the claim was already in its docstring and putting the check
  in each caller would have been two rules.

  The route says who asked (the line `delete_pack_version` already writes, this being the other
  irreversible write a relaxed posture allows), reports the reason rather than a bare 500, and no
  longer publishes the `_` auth parameter that `Depends(auth) if auth else None` turned into a
  query string field. Its docstring claimed the tier gate kept it "from existing in staging or
  production at all", which is false -- `relaxed_only` refuses the call and does not unregister the
  path, and that sentence was rendered into the published OpenAPI description of a route the same
  document lists.

  An in-memory sqlite store is refused before anything runs, as `UnmigratableStoreError`. Passing
  the identity does not rescue that case: `DbStore` gives every `:memory:` store its own
  `StaticPool`, so the database exists only inside the store that opened it and the equivalent one
  alembic builds is a second, empty database -- the exact configuration `python -m plato` resolves
  with no `PLATO_SQLITE_PATH`. Diagnosed after the fact it reads as the wrong database rather than
  as no reachable database, so both callers answer it the way they already answer "the wiring names
  no database": 503 from the route, exit 3 from the job.

  The route's audit line moved below the write it describes. Written above it, in the past tense,
  it recorded a successful migration for every migration that failed; a failure is now logged with
  its reason as well as returned, so the record does not stop at the attempt.

  Every spelling of in-memory is refused, not just an unset path: `":memory:"` is the one that says
  it out loud, and a truthiness check let it through the guard written to catch it. It is a value
  an operator can type, `PLATO_SQLITE_PATH` being a bootstrap key the dashboard's config panel
  edits and a write there rebuilding the engine from it.

  A migration that raises inside alembic -- a DDL failure, a statement timeout on an ALTER queued
  behind a live reader -- is audited too. Enumerating the two refusals this code raises left the
  one irreversible operation on the route with no record of who asked, while part of the revision
  chain may have applied.

  **Controls a replica would refuse are no longer rendered.** The pages carry a server-rendered
  verdict rather than fetching one, and three of the four were latent before the migrate button
  made the rule explicit: `packs.html` offered Delete and Initialize, both `relaxed_only`, and
  `dashboard.html` a config save. Each failed on click instead of being absent.

  What the pages ask is `relaxed_only`'s own predicate, not a copy of it. Strictness is one of its
  three conditions -- the others are a tier outside local/dev-daily and a tier variable it cannot
  read -- so gating on strictness alone offered all three controls under
  `JAPES_ENVIRONMENT=staging JAPES_STRICTNESS=relaxed` and under a misspelt `ENVIRONMENT`, both of
  which then answered 403. `relaxed_write_allowed()` is that decision as a question rather than a
  refusal, `relaxed_only` is built on it, and the pages render it.

  The `strict=` override each router accepts reaches the pages too. It short-circuits every tier
  condition, so a page that did not forward it asked a different question from the routes beside
  it: a `strict=True` packs router on a laptop kept rendering Delete and the seed panel while every
  click answered 403. `create_plato_app` now binds one value for the three `relaxed_only` routers
  and the pages that render controls for them. The details page needs it passed explicitly --
  `migrate_strict` -- because its button belongs to a route the database router owns; it also hides
  that button where `omit_nav` says this app mounts no database router at all, since there the
  route is absent rather than refused and the click would 404.

  The config save asks a different question from the other three, which is the part worth stating:
  `/config`'s PATCH is not `relaxed_only` and is always registered -- a strict, unauthenticated
  replica swaps in one answering 403, because an absent route reads as a bad URL -- while a strict
  replica built *with* an auth dependency accepts the write. Gated on the tier it would have hidden
  the control from exactly the configuration that 403 tells operators to adopt, so the page renders
  `withholding(strict, auth)`, the same call the router makes.

- **Which modes are catalog-only is data, and checked.** `MODE_REGISTRY` declares thirteen modes
  and the SDK ships a `BaseMode` subclass for seven; which seven lived only in a `stubs.py`
  sentence, which had drifted. It named four catalog-only modes where there are six: `conductor`
  and `curator` have no `BaseMode` subclass either. Neither is absent -- `conductor` is the
  pipeline engine in `jazzx_sdk.conductor` and `curator` is a set of functions in
  `modes/evolve/curator.py` -- they are not implemented *as runnable modes*, which is the
  distinction a pack author greping for `ConductorMode` needs and the prose obscured. The set is
  `CATALOG_ONLY_MODES` now, and a test asserts both directions: nothing declared catalog-only has
  an implementation, and nothing lacking one goes undeclared. The sentence also named a consumer
  repo, which shipped SDK code should not.

- **The pipeline catalog's `steps` is checked against a pipeline, not against itself.** It was the
  one field in `PipelineContract` nothing verified, and it had drifted: `ground` landed in the chat
  pipeline and the entry never gained it. Three tests named `*_contract_matches_its_real_module`
  looked like the check and were not -- `assert contract.turn_type == "ChatTurn"` is the registry
  compared to literals restating the registry, and would pass with the class deleted. The
  importability test beside them already covered `module`/`turn_type`/`entrypoint` for real, so
  those three were redundant as well as misnamed; a name claiming to match a real module, on a body
  that reads no module, is what stops someone writing the check that is missing.

  `steps` now says what it means -- the **maximal** set, every optional stage included, since a
  default build yields a subset -- and a parametrized test builds each pipeline with every boolean
  flag on and compares. `PipelineContract` gained `builder`, because a module can define more than
  one (`build_gate_pipeline` sits beside `build_chat_pipeline`) and a test that guessed would pick
  by `dir()` ordering. Verified against three kinds of drift: a missing step, a renamed step id,
  and a builder name that no longer resolves.

- **soupsieve 2.8.4 -> 2.9.2 in the lock.** Two Dependabot alerts on `main` (polynomial-time ReDoS,
  O(n^2), in the `IDENTIFIER` and `VALUE` selector sub-patterns). It is a transitive pin only:
  `beautifulsoup4 >=4.12.0` pulls it and asks for `soupsieve >=1.6.1`, so nothing in `pyproject.toml`
  changed and the lock's content hash is unchanged. `poetry update soupsieve --lock` touched that one
  entry and no other.

## [2.5.1] - 2026-09-08

*SDK 2.5.1, Plato 0.1.3. All 2.5.1 work lives on the `v2.5.1` branch so it can land on `dev` as one
squash; `dev` stays at what is pushed, for the 2.5.0 merge to `main`.*

*`v2.5.1` is rebased onto the pushed `dev` (`25f5d35`), keeping its three commits. No conflicts,
including in the two files both branches had touched.*

- **A dedicated packs page, and the pack store's first writes.** `pack_version` decides what a
  domain is and the dashboard showed it as a row count beside seven other tables. `GET
  {prefix}/packs/ui` is a page of its own: one row per pack with domain, segment and latest
  version, expanding into that pack's versions with status, visibility, publisher, digest, archive
  presence and declared dependencies. Expansion survives a reload, so a delete does not collapse
  the pack being worked in.

  `GET {prefix}/packs` is the JSON behind it, gated like `database` and `metrics`, and it never
  raises: an unwired or unreachable store reports `available: false` with a reason, and one
  unreadable pack costs that pack's versions rather than the page.

  `DELETE {prefix}/packs/{pack_id}/{version}` is the only mutation the table permits, because a
  published version is immutable by construction -- the key carries no surrogate, so an edit is a
  new version and retirement is a delete. `PackVersionStore.delete` is tenant-scoped by that key
  and idempotent, and it keeps the archive: the blob key is the content digest and copy-on-adopt
  means two tenants legitimately share one, so reclaiming it needs a count across every tenant
  that a tenant-scoped store cannot ask. `TODO(orphan-blob-gc)` records that.

  `POST {prefix}/packs/initialize` publishes `plato/data/seed_packs` -- `dscr_core` and
  `ci-spread-core`, the two packs that ship with the image -- into the calling tenant, so a fresh dev-daily database is not empty on the
  page it is meant to be verified through. `PLATO_SEED_PACKS_DIR` points somewhere else, which is
  how a developer seeds the packs they are editing rather than the snapshot. Idempotent by
  `(pack_id, version)`: `publish` refuses a duplicate and this is something someone does twice.
  Editor and build junk (`.DS_Store`, `__pycache__`, `*.pyc`) never reaches an archive.

  Both writes are relaxed-posture only -- `local` and `dev-daily` -- through one shared gate rather
  than a check spelled per route. Deliberately harder than `/v1/config`'s PATCH, which admits a
  write in a strict posture as soon as an auth dependency is present: that is the right trade for
  fixing a Knowledge Hub URL and the wrong one for rows that say which rules a decision was made
  under.

  The router takes `store_for(tenant)` rather than a store, the shape `session_store_for` has:
  `PackVersionStore` is tenant-scoped at construction, so one store on the app would have served
  every tenant the first one's packs -- wrong exactly where several tenants are the point.

  The review round on it found the seeding verified the wrong thing: that the packs *publish*, not
  that they load. Three of the five vendored packs point `policies.registry`, `conductor.*` or
  `experts.*.class` at `jaci.*` dotted paths, and jaci is not a japes dependency -- so the image
  ships a pack that raises `ModuleNotFoundError` on `policy_registry` and `initialize` reports it
  published. Recorded as `TODO(seed-pack-consumer-pointers)` and a strict xfail rather than settled
  by guess: either the vendored copies drop the pointers in favour of the declarative files they
  already carry, or those packs are not seed data.

  `dscr_core` also declared `policies:` and no `profiles:`, so the profile beside its rules was
  never loaded and the ten rules resolving `profile:`/`profile_table:` references had nothing to
  resolve against. Declared now; the profile answers with 7 thresholds and 5 grids.

  And `Threshold` failed open on a typo. `frozen=True` without `extra="forbid"` let pydantic drop
  an unmodelled key, so `{value: '1.20', status: active, provinance: secondary_source}` built an
  institution-authored, *active* threshold and `get` served the figure as the institution's own --
  on the one field the type exists to govern, with the coercion's own comment claiming an unmodelled
  key was refused. Extras are forbidden, so a misspelling and unmodelled metadata are both refused
  by both accessors.

  Smaller: the degraded nav offered the two new pack links it does not mount, which is the case
  `nav_html`'s `omit` list exists for; a mistyped `PLATO_SEED_PACKS_DIR` rendered as "0 published,
  0 already there" because the page dropped `reason`; `seed.py` claimed assistant packs seed when
  an `AssistantManifest` has no `pack_version` to publish under, and reported them as declaring no
  `pack_id` when they do; `GuidanceAsset.is_active` carried the same naive-datetime crash `as_utc`
  was extracted for; and one new test asserted `sorted(x) == x` over the same list.

  A second round on it found the deferral's own enumeration wrong: three packs named, four
  carrying `jaci.*` pointers. `clinical-intake-core` has one on `modes.evaluator.class`, which the
  parked test cannot see because it reads `policy_registry` and `policy_profile()` and never
  touches `modes:` -- so a fix following that note literally would have left one pack broken. Only
  `dscr_core` is clean. The note names all four now and a test pins the set against the manifests,
  since a sentence someone has to keep in step is not a record.

  An existing but empty seed root returned no `reason`, rendering as "0 published, 0 already
  there" -- the same misread as a missing root, one input over. Neither write recorded who asked:
  the page carries a **By** column that always showed a dash, `publish` already takes the
  argument, and `settings_store._actor` already owned the best-effort lookup. `pack_inventory`
  claimed never to raise while the row transform sat outside its per-pack guard.
  `_manifest_of` returned on the first unreadable manifest name instead of trying the other. And
  `TODO(if-match-post)` was deferred on "there is no route to fix against", which `POST
  {prefix}/packs/initialize` makes false.

  A third round found the feature dead in every deployment. `create_plato_app` grew a
  `pack_store_for` kwarg, the router used it and the nav advertised the page, but `PlatoWiring` had
  no such field and `build_app` passed none -- so `/packs` answered "no pack store is wired" and
  both writes 503'd for any real server. All 24 tests built the app directly with their own
  factory, which is why none of them saw it. The wiring carries it now, built beside
  `session_store_for` with the same per-tenant caching, and the new test goes through `build_app`.
  Archives need somewhere to live, so `_pack_blob` resolves `PLATO_PACK_BLOB_BACKEND`/`_DIR`/
  `_CONTAINER`, local by default: a replica with no object store configured still publishes.

  `nav_html`'s docstring and `TODO(omit-info)` both still quoted the degraded omission tuple as
  three entries after it grew to five, in the file whose stated purpose is that three files cannot
  drift into three link sets. They point at its owner now instead of restating it.

  A fourth round found the same shape one layer out: the page could not work where it is aimed. The
  shipped tenant resolver *raises* on a deployed posture with no `X-Tenant-Id` -- rightly, since
  serving an unlabelled request as some arbitrary tenant is a cross-tenant read -- and the page sent
  no such header, so every fetch 500'd on dev-daily, the posture this surface exists for. The route
  answers 400 naming the header now, and the page carries a tenant field on `info.html`'s
  affordance: client-side, remembered, re-reads on Enter. All four fetches go through one helper.

  `load()` also mapped every non-2xx to `null`, which renders as "Pack store not readable" -- the
  page blaming the store for a request problem, while its two write paths already read `detail`.
  `seed.py` dropped the `.strip()` `publish` applies to the same key, so a padded `pack_id` missed
  the already-published lookup and a second run reported `failed` where it should say `skipped`.
  `pack_inventory`'s "never raises" now covers the sort and record reads that sat outside its
  guards, and `_MANIFEST_KEYS` no longer claims to be what an operator reads on a page with no
  manifest column.

  **Retiring a version no longer frees its number.** `delete` removed the row, so publishing the
  same `(pack_id, version)` afterwards succeeded with different bytes -- in-place editing with an
  extra call, and nothing recording that the version had ever held anything else. Measured:
  digest `e060ce02` became `a8ecd153` under one version and `versions()` showed a single `0.1.0`.
  Over HTTP that is `DELETE .../packs/{id}/{version}` then `POST .../packs/initialize`, and bundled
  seed content changes without a `pack_version` bump -- so a re-initialize after an image upgrade
  substituted content under an unchanged version.

  `0004_pack_version_retired_at` adds the tombstone. `delete` sets `retired_at`, the three reads
  skip it, and `publish` asks `_row_including_retired` rather than `get` -- the one read that must
  not filter, because filtering it there would have left the tombstone doing nothing at all. The
  language is *retire* now, on the route, its 404 and the page, since that is what it does.

  Two more from the same round: `detect_cross_period_addback_inconsistency` raised
  `ThresholdNotActivated` out of a findings function while `policy_lint` in the same change
  explicitly reports it, so an unapproved severity knob lost every finding the call would have
  produced -- named in `detail` now. And `_warning_refs` returning `{}` left `policy_id`/`rule_id`
  absent where the violations loop always sets them, so a consumer keying on `rule_id` got a
  `KeyError` instead of the `None` the docstring's own story implies.

  `load_workbook_layout` picked up two `TODO`s from the same review, both pre-existing and neither
  built here. A layout `key` that resolves against neither the chart of accounts nor the metric
  catalog loads clean and then emits a labeled row of empty cells in a *governed* workbook with no
  exception entry -- validating it needs the pack's own accounts and metrics, which that function
  deliberately does not take, so the check belongs where the caller has both. And a
  `live_formula: true` sheet declared before its Inputs sheet silently writes literals instead of
  formulas: a workbook that looks right and is not live. A shipped layout's header claims the first
  check already happens.

  The seed set is `dscr_core` and `ci-spread-core`, re-vendored after their manifests were fixed at
  source. `ci-spread-core` declares `policies: {dir: policies}` instead of a `registry:` pointer
  into consumer code plus an enumerated `core:` -- verified to yield the same six policy ids the
  code registry held, so the swap is behaviour-preserving rather than the credit decision it was
  first described as. `dscr_core` declares its `profiles:` dir. Both now load inside the image,
  which is what the parked strict xfail was waiting for; it flipped and is a plain test.

  Wiring the pack store into `wiring_default` and not `wiring_local` left the feature dead in
  `local` -- one of the two postures its writes are admitted in, and the one a laptop runs -- while
  the test written for exactly that failure covered `wiring_default` alone. The third time this
  release that a producer was added without visiting every construction of it.

  Retiring a seeded version then re-initializing reported `failed: ValueError`: the pre-check reads
  through `get`, which filters a tombstone, while `publish` sees one and refuses. `PackVersionExists`
  carries `retired`, so a caller tells "nothing to do" from a fault without matching on a message,
  and the answer is `skipped: retired`.

  `_pack_blob` warns on a deployed posture as `_db` does for the same shape: the rows go to Postgres
  and local archive bytes do not, after which `has_archive: true` claims an archive that is gone.
  `pack_inventory` guards the record reads without hiding the pack -- the first attempt dropped an
  unreadable one, contradicting its own test, so it is two guards that mean different things. The
  consumer-module guard reads every file rather than manifests only, and pins the set: `dscr_core`
  was called clean on a manifest-only read and its notes name `jaci.*`. Clearing the tenant field
  clears the stored value instead of silently re-sending the old one.

  `_pack_blob` keyed its durability guard on `== "local"` while `BlobStore` treats every
  non-`azure` backend as local, so `Azure` with a capital -- or any typo -- skipped both the
  `local_dir` and the warning: archives to `./blobs` inside the container, `has_archive: true` on
  the row, bytes gone with the pod, silently. It guards the complement now, as `_db` does and as
  its own docstring claimed to.

  The **By** column had no way to be filled. `_actor()` reads the identity header and the page sent
  none, so every seeded row stored null and each retire logged an unattributed caller for what the
  module docstring calls a governed act; `info.html` has carried that field all along and the page
  with the writes did not. And the fetch-exception path still reported "Pack store not readable"
  for a replica that was restarting -- the misattribution the branch above it had just been fixed
  for.

  Two tests say what they do: the local-wiring one greps source rather than calling `build()`,
  which `SystemExit`s without an assistant-profile checkout, and is named for that; the
  consumer-module guard reads every text file rather than a `.yaml`/`.md` allowlist, its own
  docstring having rejected a guard that reads a fraction of the tree.

  An unreadable pack rendered as `Versions 0` beside a populated `Latest`. A pack row cannot exist
  with no live versions, so an empty list means the second query failed -- wrong data whose only
  trace was a log line, against `pack_inventory`'s own promise that the operator learns the pack is
  unreadable. `versions_error` travels in the JSON, the row says "unreadable", and the header count
  reports how many rather than undercounting.

  Two symmetries, both the same mistake: restating an invariant locally instead of extending the
  family. `_pack_blob()` was resolved inside `pack_store_for`, on the cache-miss path, so with two
  or more tenants its warnings re-fired per request while `_db`'s land once at boot -- hoisted
  beside it. And the four page-family invariants in `test_plato_info_api` enumerate pages by hand;
  `packs_html` was in none of them, with two restated in its own file instead. It is in all four
  now, including the external-host scan whose docstring records `info.html` having been left
  "scanned by nothing" exactly this way once before.

  Smaller: `#empty` doubled as the error channel, so a failed retire's message was wiped by the
  next expander click; errors have their own element. A `count("headers(")` assertion also matched
  the prose comment describing the helper. `TODO(azure-blob-container-singleton)` records that
  `PLATO_PACK_BLOB_CONTAINER` only applies if pack archives are the process's first azure consumer.

  The round after that was mostly the round before it. The error channel added to stop messages
  being wiped never cleared on success, so a refusal from a blank tenant field sat beside the table
  that rendered once one was supplied, and the failure path left "Nothing published yet." visible
  underneath; both reset per attempt now. The `headers(` assertion "corrected" by subtracting the
  definition still counted the prose comment describing it, so it sat at its threshold on the
  strength of a sentence -- it counts call sites. The azure-container `TODO` claimed the collision
  was unreachable because this is plato's only `backend="azure"` construction; `fabric.fabric`
  builds a second from `JAPES_BLOB_*` that plato instantiates through `_client_layer()`. And the
  identity field invites a value `get_current_user_id` discards: it parses `x-user-id` as a UUID
  and returns `None` otherwise, so a name typed there left the row unattributed.

  Two that were not: the pack-archive degradation was logged at boot and not reported, while `_db`'s
  sqlite equivalent goes through `missing_config` to `/info` and the dashboard -- so one
  container-start line was the only trace that a published pack cannot be materialized after a
  restart. And `azure` with no container warned nothing while the local branch warns twice.

  Reporting it through `missing_config` was then reverted, because it broke readiness. That list is
  what `/health` answers 503 from and what a strict posture refuses every chat route on, and the
  note is true whenever `PLATO_PACK_BLOB_BACKEND` is unset -- its default. Measured: a staging
  replica with tenants, a Knowledge Hub, an LLM key and a `common` database got exactly one
  degraded note, this one, so it would fail its container probe over a pack store it may never
  publish to. The sqlite degradation it claimed to copy fires only on a database that genuinely
  cannot persist. `_pack_blob` warns at boot; the comment records why it goes no further, and a
  test holds a configured replica ready. The claim that `/v1/config` could clear the note was false
  as well -- the key is not in the settings catalogue.

  `#meta` kept the version count from the last successful read, so a mistyped tenant rendered
  "3 versions" beside "unavailable" -- the third stale-channel bug in that file, now cleared on
  every path.

  **A bare threshold no longer claims a provenance it was not given.** `get_threshold` answered
  `INSTITUTION_AUTHORED` for every plain value, including the shipped DSCR profile whose own header
  credits its numbers to a vendor program summary -- the attribution `looks_authored` refuses to
  invent for one mapping, invented for every profile. `ThresholdProvenance.UNSPECIFIED` is the
  default and what a bare value reports; `ACTIVE` stays, because "a bare value is served" is true.

  The grid `TODO` also had its blast radius backwards: it said the gate "covers seven of its
  numbers and not the rest", and that profile authors all seven thresholds as bare strings, so the
  gate covers *none* of its 157. Adopting it means authoring provenance on the thresholds, not only
  closing the grid.

  `_evaluate_composite` lifts a child's refusal onto its own `inputs`, which deleted the recursive
  `limbs` walker in `experts.policy.default` -- the only code outside the condition evaluator that
  knew the shape it builds. A grandchild refusal still reaches the warning.

  One resolver, one guard. `_store` caught the tenant resolver's raise and wrote a comment
  explaining why, while `assistants_api._tenant` calls the same resolver -- so every chat route
  answered 500 with a stack trace for the request the packs route answered "X-Tenant-Id is
  required". `plato.tenancy.tenant_of` is shared by both; proven by reverting.

  `latest_version` was a lie in the field name: it is `list_packs()`'s row, chosen by
  `published_at`, which that method's docstring calls the wrong answer for a caller reading it as
  the highest version. Publish `0.2.0`, backport `0.1.1`, and the page said `Latest 0.1.1` above
  its own expanded rows listing `0.2.0`. It is `last_published_version` under "Last published".

  Smaller: `packs_html` lost an `omit` parameter no caller passes; the identity field shares
  `info.html`'s storage key rather than making an operator retype a UUID one nav click away;
  `PlatoWiring.pack_store_for` sits genuinely last, and its comment no longer justifies its
  position with a dataclass rule that did not apply to a defaulted field; the store-cache docstring
  says what it is (one entry, cleared per miss) instead of contradicting the note 30 lines above
  it; `TODO(publish-tick-tie)`'s stated reason is no longer "no caller invokes publish yet", which
  the seed route made false. And one ordering assertion was deleted rather than corrected a third
  time -- `seed_packs` iterates a sorted list, so it could never have failed.

- **Review round: the withholding branch outranked the precedence check that should have
  silenced it.** Two defects in the not-activated work, both in the ordering of decisions rather
  than in any single one.

  `check_compliance` evaluated a rule's applicability gate *before* checking whether a
  higher-precedence policy already owns the field the rule reads. So a rule an overlay had
  replaced could still reach the `gate_blocks` branch and withhold `allowed` on its own gate's
  unapproved threshold -- and nothing the operator did could clear it, because approving that
  seed changes the answer of a rule that does not apply. The field-precedence check moved above
  the gate, which also stops evaluating a gate whose rule is skipped either way.

  In `_evaluate_composite`, the refusal *text* was first-child-wins while the composite's
  `indeterminate_reason` gives `POLICY_NOT_ACTIVATED` precedence, so the two disagreed: a
  satisfied `any_of` limb still carries the refusal text of its own refused child, and
  `all_of[any_of[seedA, ok], ratio(seedB)]` reported the reason from `seedB` under text naming
  `seedA`. An operator reads that text to know which key to approve. The text now comes from the
  child that actually blocked, on the same precedence the reason uses, and is carried only when
  the composite's reason is the one it explains -- so an `EVIDENCE_MISSING` outcome no longer
  ships a stray refusal from a limb that passed.

  The warning line also had no single owner: `experts.policy` built it in two pieces and
  `finance.validation` kept a regex guessing at the join, two packages apart with nothing tying
  them together. `format_not_activated`/`parse_not_activated` now sit together in
  `fabric.canonical.refusal` -- which both sides already import at runtime, unlike `experts`,
  whose import in `validation` is deliberately `TYPE_CHECKING`-only -- with `NOT_ACTIVATED_INPUT_KEY`
  replacing four bare string literals. A round-trip test fails if the format changes without the
  parser. `ComplianceResult.warnings` stays `list[str]`: a second structured field duplicating a
  display channel is the kind of API growth that invites its own drift.

  Declined, with the measurement: the two gate sites differed in that one wrapped
  `gate_outcome.inputs` in `dict(...)` and the other did not. Pydantic v2 rebuilds a dict field
  during validation, so the wrapper never protected anything -- it only made one of the two read
  as if the other were unsafe. Dropped rather than mirrored.

- **`seed_packs` called three kinds of "not a pack" already published.** A directory with no
  readable manifest, an assistant pack, and a manifest with no `pack_id` all landed in `skipped`
  beside the genuine already-published case, and the page renders `skipped.length` as "already
  there". Pointing the seeder at a checkout whose asset-only directories keep their manifest as a
  sibling top-level file -- the documented use of `PLATO_SEED_PACKS_DIR` -- reported three packs
  as sitting in the store that had never been published. `not_packs` is now its own bucket, its
  own count on the page, and the test asserts the two are distinguishable on a second run rather
  than merely that a bad directory is non-fatal.

  `TODO(seed-pack-vendoring)` records what the bundled copies are and are not: nothing keeps them
  in step with the consumer-authored originals, which are the edited ones, and the packs name that
  consumer's Python modules in their layout and reclassification declarations, so those entry
  points do not resolve in a plato-only deployment. The policy and profile corpora, which is what
  the page is verified through, do.

  The vendored copies also carried gitignored plan filenames into a tracked tree, in nineteen
  provenance comments across eleven files of the authoring repo. Rewritten at the source to name
  the subject instead, keeping every phase and FR reference.

- **Review round: the fourth message channel, and a resolver shape nobody catches.** All four
  findings were low and all four were consistency gaps rather than reachable bugs, which is what
  the round was for.

  `packs.html` grew a fourth message channel with `#seed-result`, and `load()`'s reset block --
  extended three times already for `#problem`, `#empty` and `#meta` -- did not cover it, so
  "6 published, 0 already there" sat over a table a later delete had changed underneath. The
  one-line fix the finding proposed would have broken the feature: `seed()` writes its message and
  *then* awaits `load()`, so resetting there deletes the only report of what the run did. `seed()`
  now computes the message, awaits the re-render, and writes it last; `load()` owns all four
  channels, and a test pins that ordering so the next person does not reintroduce it.

  `tenant_of`'s docstring promises "an HTTP answer, or `HTTPException(400)`" and the handler
  enumerated `ValueError` alone. `PlatoWiring.tenant_from_request` is a documented extension
  point, and the obvious way to write one is `request.headers["X-Tenant-Id"]` -- a `KeyError`,
  which escaped as exactly the 500-with-a-stack-trace this helper exists to prevent. Now
  `LookupError` too; a `TypeError` from a resolver still surfaces, being a defect in it rather
  than a missing header.

  `wiring_local` pointed the pack unpack cache at `CACHE`, the assembled assistant-pack directory
  that `_assemble_pack` marks and `rmtree`s on every boot and `pack_registries` then reads as a
  pack root -- so digest directories would land beside `profile/` and the cache would be discarded
  per boot. `PLATO_LOCAL_PACK_CACHE` gives it its own directory, as the archive bytes already had.
  Nothing deployed was affected: `wiring_default` passes no `cache_root` and gets the tempdir
  default. `.gitignore` covered `.plato-local-pack/` and neither sibling, so both would
  show as untracked the first time the local wiring ran; one glob now covers all three.

  And one test located the bundled pack by a CWD-relative literal where its sibling in the same
  diff asks `default_seed_root()` -- the function that owns where seed packs live. It failed from
  any directory but the repo root, which is how it is run from the consumer's venv.

- **Inline review of the three rounds above, which found more.** Four things, two of them
  defects this branch's own review rounds introduced.

  The `#seed-result` fix was wrong in its failure path: `seed()`'s `!response.ok` branch still
  wrote the element directly, before the `load()` that now clears it, so the final assignment
  overwrote it with the empty string. A 403 from a strict posture reported *nothing at all* --
  worse than the staleness being fixed. Every branch routes through one variable now, and the
  test asserts the exact set of writes rather than just their order, because ordering was what
  the previous test checked and this slipped past it.

  `_evaluate_composite`'s `fallback` was not merely dead code. A `POLICY_NOT_ACTIVATED` composite
  always has a child reporting that reason and carrying its text, so `fallback` could only ever
  fire for a child that reported something else -- reintroducing exactly the mislabeling the
  change was made to remove. Deleted rather than kept as defensiveness.

  `parse_not_activated` matched any line containing `-- a/b:`. `warnings` is free text and the
  annotation admits any producer, so an unrelated advisory could contribute a policy and rule id
  to a finding that had neither. Now anchored on the prefix `format_not_activated` writes, which
  is the point of the two living together. All three helpers are exported from
  `fabric.canonical` alongside the rest of the refusal surface.

  Two authoring mistakes in the pack corrections: the `notes:` keys added to two C&I rules are
  silently dropped by `Rule` (pydantic default `ignore`), so they read as model fields while
  being invisible to every consumer -- YAML comments, which is what they are. And the new `$2M`
  availability leg had no test reaching it at all, in either repo: the suites passing said nothing
  about it. Four parametrized cases now cover both legs, including the permissive one the finding
  named, plus a check that the conductor supplies the dollar field the rule reads.

  A second inline pass over that delta found no further defects, and one coverage gap:
  `dscr_core` had a seed-pack test loading it through `Pack.from_manifest` and `ci-spread-core`,
  whose rule shape this branch changed, had none. `load_policies()` on a file proves the YAML
  parses; it does not prove the manifest declares it, that `is_policy_document` accepts it, or
  that a combinator survives the route plato publishes and reads through. Both packs are now
  pinned there -- six policies and eleven rules for one, forty-one for the other.

- **Review round: a bundled pack that could not load, and the typed refusal it should have been
  from the start.**

  `ci-spread-core`'s bundled manifest bound `experts.*.class`, `conductor.class`,
  `conductor.pipeline` and `modes.evaluator.class` to `jaci.*` symbols, and
  `evaluation.gold_cases_path`/`runner` to paths inside the authoring repo. japes declares no
  `jaci` dependency, so `Pack.conductor` -- a `cached_property` that resolves on plain attribute
  access -- raised `ModuleNotFoundError` on a pack `POST /packs/initialize` publishes into any
  tenant. The previous round had recorded this as `TODO(seed-pack-vendoring)` on the reasoning
  that the pointers "fail when something resolves them, not on load", which was simply wrong about
  `conductor`. The bindings are gone from the snapshot and the declarative config they sat beside
  stays; `dscr_core`'s `gold_cases_path` went the same way. The bundled copy is a filtered copy of
  the authoring repo's now, not a verbatim one, and
  `test_a_bundled_seed_pack_is_loadable_in_a_japes_only_process` touches everything on `Pack` that
  resolves a symbol, so re-vendoring verbatim fails there rather than shipping.

  `ComplianceResult.refusals: list[Refusal]` replaces the string round trip. `Refusal` is the
  SDK's "declined, as data rather than an exception" carrier, it lives in the module the sentence's
  formatter had been added to, `statemachine.engine` already mints one for the identical
  `ThresholdNotActivated` condition, and it has slots for both the refs (`domain_extensions`) and
  what would clear it (`remediation`) -- which the sentence never carried. `warnings` keeps its
  `list[str]` shape and is rendered *from* `refusals`, so the list a caller displays and the one
  it reads structurally cannot disagree; `format_not_activated`, `parse_not_activated`, the prefix
  and the anchored regex are all deleted. Third finding on that pair, and the one that removed it
  rather than tightening it.

  Smaller consistency work in the same pass. `blocked_gate_outcome` joins `gate_blocks` beside the
  evaluator dispatcher: the predicate had been hoisted and the outcome it gates left written out
  at each call site, where `segment.py` dropped `action` and `check.py` kept it. `is_assistant_manifest`
  gives the seeder the discriminator `is_assistant_pack` exists to own, rather than a second
  spelling of `"assistant_id" in manifest`. `withheld("published packs")` keeps `packs=[]`, as its
  three sibling routes keep their collection keys. `tenant_of` composes a sentence for a
  `LookupError` instead of serving a `KeyError`'s bare quoted key, through the same
  redact-and-collapse as every other served-text path. And the dead awaitable branch in `_store`
  is gone, along with a factory docstring that omitted the route it registers.

  `not_yet_effective` is now its own list on both `StalenessReport` and `PolicyResolutionResult`.
  `is_active` covers the whole window, so a policy authored `status: active` with a future
  `effective_date` failed it and was reported as *stale* -- telling a caller to review and update
  a policy that has not started, and answering `detect_stale_pinned_policies`' "since been
  superseded" with one superseded by nothing. `Policy.is_not_yet_effective` is the shared
  predicate, because the same `not is_active` list existed one function away.

  Two corrections to comments that overclaimed. `Threshold`'s `extra="forbid"` note said a
  misspelled governance key is a refusal; it is only that once `looks_authored` has recognised the
  mapping, which keys on `provenance`/`status` -- so a mapping whose *sole* governance key is
  misspelled is not read as governance at all, is never coerced, and `get` returns the raw dict.
  That is the deliberate price of letting an unrelated mapping through untouched, now stated and
  pinned. And `_apply_applicability_gate` claimed to mirror `check_compliance` "exactly", which
  stopped being true when that function gained its field-precedence check; its `not_applicable`
  list is renamed `withheld`, since a blocked gate is INDETERMINATE.

  One test guard was holding nothing: it filtered the readiness list on `"Pack archive"`, which no
  note in `wiring_default` has ever contained -- its wording is lowercase. It asserts the whole
  list now, and re-adding the note fails it.

- **Review round: the typed refusal dropped the shape it replaced, and a predicate narrowed for
  the third time.**

  `policy_violations_to_findings` read `refusals` and stopped reading `warnings`, but
  `ComplianceResult` is exported and a pack expert written against the older shape fills
  `warnings` and not the field this became. That answered `[]` -- a clean spread for a deal the
  expert refused, which is the exact failure the function's own docstring says it closed.
  `warnings` is read again when `refusals` is empty, for its text alone: the in-repo producer sets
  both from one list, so preferring the typed field cannot double-count. The docstring had also
  gone stale against its own loop.

  `looks_authored` keyed on `provenance` *or* `status`, and `status` is an ordinary word in a
  bucket that holds arbitrary pack data: `{status: enabled, region: west}` under `custom` was read
  as a claimed threshold, failed `Threshold(**found)`, stayed a dict and was then refused by
  `get` -- profile data that used to resolve, raising. `provenance` alone is unambiguous and still
  counts on its own; `status` counts only alongside a `value`. Third narrowing of this predicate:
  it keyed on `value` first, which coerced mappings that had nothing to do with thresholds, then
  on either governance key. What both got wrong is that only one of the two words means anything
  specific here.

  Two reporting fixes from widening `is_active`. `detect_staleness` built its reason as
  `not_in_force() or <status sentence>`, so a policy that is *both* draft and future-dated was
  reported purely as a window problem -- telling the reader to update a policy whose real problem
  is that nobody approved it, and losing the deprecation on a deprecated-and-expired one. Both
  causes are joined now, as `Rule.activation_block` already joined its own. And the Governor's
  citation check logged "cites rule from deprecated policy" for any `not policy.is_active`, which
  since the widening includes a policy that has not started; it names the policy's own reason
  instead. The stub in its test carried `is_active` and nothing else, so the missing attributes
  raised inside an `except Exception` and the warning the test asserts on became a debug line --
  widened to what the check actually reads.

  Smaller: `PackVersionExists` and `is_assistant_manifest` re-export from `jazzx_sdk.pack`
  alongside the siblings they were added beside, so `plato/seed.py` imports from the facade like
  its neighbours; `blocked_gate_outcome`'s docstring described neither call site; and the dead
  `effective_date is None` guard in `is_not_yet_effective` is gone, `effective_date` being
  required on `Policy`.

  `TODO(refused-rule-field-claim)` records the one finding left as a deferral: a refused rule
  `continue`s before claiming its field, so a lower-precedence rule on that field still evaluates
  and can cite the threshold an overlay was meant to supersede. `allowed` is already False, so the
  cost is a misleading entry rather than a wrong verdict, and the EVIDENCE_MISSING branch beside
  it has always behaved the same way -- whether a rule that established nothing may claim a field
  is a governance question, and both branches should move together.

- **Review round: the pin that read one spelling, and a posture rule that lost its override.**

  `test_which_seed_pack_files_name_consumer_modules_is_pinned` detected the consumer with
  `"jaci." in text`, which only ever matched a dotted module path -- so `jaci/scripts/...`,
  "jaci's own MetricResult shape", and this branch's own comment on the manifest were invisible.
  Nine files carry the name; the pin listed six, and its docstring is the thing that says a guard
  reading a fraction of the tree is worse than none. It matches the bare word now.

  `_refuse_unless_relaxed` moved out of `packs_api` into `posture.relaxed_only`, beside
  `withholding`/`withheld` (the read side) and `require_if_match` (a mutating-request
  precondition) -- a posture rule written inside one router is one the next router writes again.
  `config_api` keeps its own gate: its admission differs (auth is enough there) and its refusal is
  a route replacement with a dict detail, so folding both in would add code rather than remove it.
  The move dropped the `strict=` pass-through the closure had captured, which no test caught
  because they all set the posture through the environment; both call sites pass it and the test
  now exercises an explicit override.

- **Review round: the served refusal named a Python type, and the suite trusted a shell
  variable.**

  `tenant_of` routed a resolver's message through `failures.reason`, which *always* prefixes the
  exception class -- so the shipped deployed resolver's 400 read `ValueError: X-Tenant-Id is
  required...`, a type name handed to an unauthenticated caller and worse than the bare `str(exc)`
  it replaced. It also passed no `SERVED_REASON_LIMIT`, which twelve other served-text paths in
  plato do. Both go through one local `served()` now: collapse, redact, bound, no type name;
  `reason` stays in the log lines, where the type is useful and nothing is served. And the
  `if not found` branch -- the one a `.get`-style resolver reaches, which is what both shipped
  resolvers are -- answered "could not resolve a tenant for this request", naming nothing. It
  names the conventional header, and none of the three paths drop the cause any more.

  `PLATO_SEED_PACKS_DIR` was not stripped in the packs tests. Thirteen of them reach
  `default_seed_root()`, four took the fixture that cleaned the environment, and every assertion
  about the *bundled* packs was really about whatever that variable pointed at -- the suite would
  pass or fail on a shell setting. Stripping it is autouse now, precisely because making it
  opt-in is how nine tests ended up uncovered.

  `pack_archive` moved from `plato/seed.py` to `jazzx_sdk.pack.store`, beside `MANIFEST_NAMES` and
  for its reason: the archive shape is the store's contract, `store_db._unpack` is the reader that
  has to agree with it, and a writer living in a consumer drifts from the reader. `settings_store._actor`
  became `acting_user_id` at its second importer, where the underscore stopped being true.

  The deployed `pack_store_for` passed no `cache_root`, so the wiring that runs in a container was
  the one falling back to `<tempdir>/japes-packs` while the laptop wiring had its own directory:
  `PLATO_PACK_CACHE_DIR` sits beside `PLATO_PACK_BLOB_DIR` now, and `.gitignore` covers both
  deployed defaults, which it did not.

  Three smaller ones. `_manifest_of` returned the first parseable dict, so a `pack_manifest.yaml`
  with no `pack_id` shadowed a complete `manifest.yaml` beside it and the directory reported no
  identity -- the readable-but-anonymous twin of a shadowing case already fixed for unparseable
  files. The "not a durable backend" warning was posture-gated in both halves, so a typo on a
  laptop wrote to local storage in silence; a typo is a typo anywhere, and only the durability
  sentence is the posture's business. And `pack_inventory`'s "versions newest-first" is
  `published_at` order, which puts a backport first -- the distinction the code makes two
  functions down and the docstring and the page both blurred.

  Two things declined with the measurement. `TODO(seed-digest-drift)`: comparing
  `record.content_digest` against `pack_archive(pack_dir)` to tell an operator the bundled bytes
  drifted is one call away and would be wrong, because `zipfile.write` records each file's mtime
  and a rebuilt image with byte-identical content digests differently (measured) -- it needs a
  content-only digest first. And the guard around `sorted(latest, key=...)` is gone rather than
  kept: its own comment said `PackVersionRecord` is frozen with every field defaulted and
  `pack_id` is a non-null primary key, so nothing could make it raise.

- **Review round: two branches that skipped a check, and one fix that opened the opposite hole.**

  Widening `Policy.is_active` to cover the effective window made `detect_staleness` route a
  future-dated ACTIVE policy into its first branch, which `continue`d before the third check --
  so a pinned version that had been superseded stopped being reported, and
  `detect_stale_pinned_policies` reads `stale_policies` only, so `not_yet_effective` compensated
  for neither. The three `continue`-separated checks are now independent facts gathered
  independently, with the pin evaluated first and unconditionally: whether a pin has been
  superseded is a fact about the pin, not about whether the policy is in force today. A policy
  that is both scheduled and holding a stale pin appears in both lists rather than whichever the
  branch order reached first.

  The `warnings` fallback added last round converted *every* string into a
  `POLICY_VIOLATION`/`Severity.POLICY` finding, and `warnings` is documented one file over as
  "mostly non-blocking". A real consumer appends "Confidence below group threshold: 0.72
  (min 0.85)" there and sets no `refusals`, so an `allowed=True` result grew a policy violation
  for something that violated nothing. It now fires only for the case it exists for: a refusal
  with no violations to show.

  `as_utc` moved to `jazzx_sdk.manifest.lifecycle`, the dependency-free module this branch created
  for exactly this problem when `PolicyStatus` moved there. A pure datetime coercer living in
  `policy.py` forced `fabric/guidance/schema.py` to import it from inside a function to dodge the
  cycle; that deferred import is gone, and the six private copies of the same three lines across
  `manifest`, `pack`, `agents`, `observability`, `audit` and `queue` now have somewhere public to
  land. `fabric.canonical` re-exports it, so no consumer path changed.

  `_UNTESTED_RATIONALE` described three of `IndeterminateReason`'s four members and let the fourth
  reach the fallback sentence, so a fifth added later would silently be described as missing
  inputs -- the false assertion that map was introduced to stop. Every member is mapped now and an
  unmapped one raises at import. `pack_archive` also skips `.git`: it is exported for consumers
  publishing arbitrary directories since last round, and a pack that is its own checkout would
  have embedded the object store.

  Deleted rather than kept: `" and ".join(causes) or "not active"`, whose fallback was
  unreachable inside a branch that guarantees at least one cause.

- **Review round: a posture guarantee the gate did not enforce, and a row its own archive
  contradicted.**

  `relaxed_only` gated on `strict_mode()`, and `JAPES_STRICTNESS=relaxed` loosens every tier
  except `production` -- so a `staging` replica with that variable set accepted a pack delete and
  a seed write, unauthenticated, because no shipped wiring sets `auth`. The docstring, the served
  403 and this module's own header all promised "local, dev-daily". It reads `environment_tier()`
  now, which is the question actually being asked and is the one thing that variable cannot
  loosen.

  Seeding published a row whose archive disagreed with it. `pack_archive` takes the whole
  directory and every reader of it prefers `MANIFEST_NAMES` order, so a `pack_manifest.yaml` that
  is unreadable or declares no `pack_id` -- exactly when the manifest search falls through to
  `manifest.yaml` -- was published under the sibling's identity while the archive still led with
  the bad one: `compose_domain_packs` logged "could not be loaded", the pack reached no registry,
  and `/packs` showed it with `has_archive: true`. An authoring error returned as a success. Such
  a directory is now reported with a reason naming both files. The test that covered this asserted
  the pack *was* published, so its expectation was the thing that had to change; what it was
  originally for -- a broken manifest must not make the directory invisible -- still holds, since
  the reason names it.

  Three claims corrected where the code had moved underneath them: the guard around building the
  inventory `entry` had no reachable trigger for the same reason given two lines above for putting
  no handler on the sort, and a comment called both "load-bearing"; "a pack row cannot exist with
  zero live versions" is true of a snapshot but `list_packs()` and `versions()` are two reads, so
  a concurrent retire between them yields the empty list the comment calls impossible; and the
  page still named `_actor()`, renamed to `acting_user_id` in the same branch.

- **Review round: the posture gate lost its other direction, and the drift lint had a blind
  spot the fix would have walked into.**

  Moving `relaxed_only` off `strict_mode()` last round fixed the loosening direction and dropped
  the tightening one: `JAPES_STRICTNESS=strict` -- the variable `check_settings` documents as
  turning the refusal back on -- left the two pack writes open on a dev-daily replica while
  `PATCH {prefix}/config` on that same replica was refused, and an unauthenticated delete burns a
  version number permanently. It reads `strict_mode() or environment_tier() not in (LOCAL,
  DEV_DAILY)` now; all six tier/strictness combinations are pinned, where the test added last
  round covered only loosening. Second defect in this one gate in two rounds.

  `find_profile_literal_drift` inspected a rule's `condition` and `applicability` only when their
  kind was `expression`, so a declaration nested inside an `all_of` was invisible. That mattered
  immediately: `DSCR-IO-MIN-LOAN`'s description promised "minimum loan amount of $250,000 **and**
  minimum FICO 640" while encoding only the amount, and `profile.custom.fico_min_io` sat at 640
  with no rule reading it -- so an interest-only loan at FICO 620 returned SATISFIED, and the
  policy registry hands `description` back verbatim as guidance text, telling a caller a check
  ran that did not. Encoding the second leg as an `all_of` would have moved *both* declarations
  out of the lint's reach while the diff appeared to add one. The lint walks composites now and
  labels the slot it found (`condition[1]`), the corpus went from 8 visible declarations to 10,
  and the consumer's pin uses the lint's own traversal rather than a second copy of it.

  Also from this round: `plato_settings_catalog`'s "the exact set `wiring_default` consults and no
  more" stopped being true when the pack-store variables arrived, and adding them would be the
  failure that docstring warns about rather than a fix -- `pack_blobs` resolves once in `build()`
  and `_rewire` re-reads only the bootstrap keys, so a PATCH would render as accepted and change
  nothing. Stated as deploy-time variables instead, with what making them editable would require.
  And two comments in the bundled manifest recorded what it used to bind and to which repo:
  archaeology in shipped data, held in place by the very pin that tracks consumer references.
  They state the rule now, so `pack_manifest.yaml` has left that pin.

- **Review round: the first `high` of the branch, and one declared-asset channel left dark.**

  Two of three slices passed. The one that did not found a permissive silent pass in the bundled
  DSCR corpus: `DSCR-OVER-2M-DSCR` states the >$2M floor as a `ratio` condition, which reads
  INDETERMINATE on a No Ratio file, so `check_compliance` skipped it and a $2.5M no-ratio loan
  returned `allowed=True` with zero violations *and* zero warnings -- while the same loan with a
  documented DSCR of 0.9 was denied. The corpus' own notes describe this hazard and prescribe the
  fix (a twin rule keyed on `dscr_documentation_type`), and it had been applied to two of the
  three sites. `DSCR-OVER-2M-NO-RATIO` is the third.

  The remaining bare-ratio rule, `DSCR-HIGH-LTV-DSCR`, needs no twin: a no-ratio file is capped at
  75% CLTV, below its own `cltv_pct > 80` gate, so the case cannot arise -- verified by running a
  no-ratio file at 85% and watching the cap deny it. Masked rather than absent, which is now
  recorded on the rule, because raising that cap would open the hole silently.

  `ci-spread-core` ships `evidence_types.yaml` with seven ids in the shape the loader reads, and
  the manifest declared no `evidence_types:` key -- so `Pack.evidence_types` was `[]` while the
  same manifest's `convergence_evidence_required` named three of those ids. The tool registry
  derives its requestable set from that list, so an Investigator built from this pack could
  request nothing. One line, and it is the argument `dscr_core`'s manifest already makes for its
  own `profiles:` block.

  Four claims in the pack notes had gone stale, three of them from this branch's own changes:
  the paragraph saying composite drift-lint coverage is a japes gap (closed last round, and this
  diff depends on the recursion) -- which was the stated reason four PPP literals were left
  unlinked, so linking them is now possible; the rule-shape table's counts, which drifted every
  time a rule was added and are now stated corpus-wide rather than per-group; and
  `fico_min_io`'s place on the orphaned-keys list, which it left when the rule grew the leg its
  description had always promised. `pack_inventory`'s manifest comment claiming `pipelines.yaml`
  is "the declarative form of the same pipeline" is a `TODO(conductor-pipeline-from-yaml)` now:
  nothing reads that file, and letting a manifest name a YAML pipeline is a japes change.

  And the consumer-reference pin says what it checks. It matches the repo name, so two files
  naming consumer-only *symbols* (`load_deal_special_instructions`, `CIConductor`) are invisible
  to it; a detector for "a symbol japes cannot import" would be an open-ended list of names
  rather than a guard, so those two are recorded in the docstring instead of matched.

- **Review round: two claims that were mine, and two one-line coverage gaps.**

  `not_yet_effective`'s field description said it was "withheld from execution like a stale one",
  and nothing withholds either list: `resolve()` builds `precedence_order` without consulting
  `is_active`, and `check_compliance` iterates it referring to neither list. No behaviour changed
  when that description arrived -- the claim did. It now says reported-not-enforced and points at
  `TODO(activation-vs-active-rules)`, which is where the enforcement gap already sits. Two
  sibling docstrings describing `is_active`'s pre-window meaning went with it
  (`current_policies`, `active_only`).

  `pack_archive` returned a valid, empty 22-byte zip for a directory that does not exist or holds
  no archivable files, so a caller's path mistake came back as an ordinary archive -- published,
  a row whose archive `_unpack` can never find a manifest in, surfacing at `materialize()` far
  from the cause. It raises now. The one shipped caller finds a manifest first, so nothing
  reached it; the function is exported from `jazzx_sdk.pack`, so the next caller need not be here.

  `find_profile_literal_drift` iterated `policy.rules` only. `Policy._all_rules()` exists in this
  same branch precisely because "an exception rule is a rule, and gating only `rules` left a seed
  one absent from both" -- so a `profile_custom_key` on an `exception_rules` entry was never
  checked, the same silent coverage loss the composite recursion closed one collection over.

- **Review round: a refusal that crashed, and an approval nobody gave.**

  `PolicyProfile.get` built its refusal message with `sorted(found)`, which raises `TypeError` on
  mixed key types -- and YAML parses a bare `2024:` as an int, so an edition-keyed governance
  block reached it. That `TypeError` escapes every handler that catches
  `ThresholdNotActivated`/`KeyError`/`ValueError`, at all three sites that catch one
  (`statemachine.engine`, `finance.validation`, `condition_evaluator`), so a refusal surfaced as
  a crash. `sorted(map(str, found))` at both sites. The parametrization covering this swept string
  keys only, which is why it missed the single key type that changes the exception.

  `get_threshold` wrapped a plain mapping as `status=active, is_executable=True, value={...}` --
  an affirmative approval for something nobody approved, which is the one statement this type
  exists to withhold. `get` still hands unrelated `custom` data back untouched, deliberately;
  asked for the *record*, a mapping that claims no governance now has none. The bare-value
  contract is unchanged: a scalar still reads back active and unattributed.

  `pack_key(manifest)` joins `MANIFEST_NAMES`, `pack_archive` and `is_assistant_manifest` in
  `jazzx_sdk.pack.store`. The `(pack_id, pack_version)` derivation was spelled twice, and the
  four-line comment on the second copy existed only to say the two had to stay in step -- which
  they had not: a padded value missed the seeder's pre-check, reached `publish`, and came back as
  `failed: ValueError` instead of `skipped`.

  `_no_seed_root_override` moved to `tests/conftest.py`. Per-file was not enough twice: it began
  opt-in, leaving nine of thirteen tests in one file asserting about "the bundled packs" while
  really asserting about a shell variable; made autouse there, a second file then borrowed
  `default_seed_root()` without the guard. Suite-wide, a third cannot.

  Smaller: `wiring_default`'s pack cache and local blob root now `.resolve()`, as
  `default_seed_root()` and both of `wiring_local`'s equivalents already did (the image's runtime
  WORKDIR is `/app` and does not move, so this is consistency, not a live fault -- checked). The
  0004 migration's index comment claimed "every read filters on it ... the one predicate they
  share"; all three reads filter `tenant_id` *and* `retired_at IS NULL`, and `retired_at` is NULL
  for essentially every row, so the index matches the ORM model rather than serving those queries.
  And `TODO(seed-pack-vendoring)` still said the bundled packs name resolvable entry points after
  the bindings were stripped -- it defers one thing now, which is that nothing keeps the copies in
  step.

- **Review round: the halves a shared builder left behind.** Slice 1 passed; every finding was
  a family this branch's own fixes half-converted.

  `inapplicable_gate_outcome` joins `blocked_gate_outcome` beside `gate_blocks`. Hoisting the
  blocked branch's builder and leaving its NOT_APPLICABLE twin written out at the call site meant
  that twin went on dropping `action` -- the exact drift the pair exists to stop, surviving in the
  half the fix skipped. Both are exported from `fabric.canonical` now; only one was, so the three
  call sites imported them from two different places.

  `find_profile_literal_drift` spelled `(*policy.rules, *policy.exception_rules)` inline while its
  own comment named `Policy._all_rules()`, added in this same branch for that reason. It calls it.
  That accessor's `TODO` claimed "no caller reads these accessors yet", which reading it made
  false -- corrected to name the one caller that now does.

  `detect_staleness`' docstring still said "three independent checks, first match wins per
  policy" after the body was rewritten to gather every cause and join them, which is what lets a
  policy that is both deprecated and holds a superseded pin report both. And
  `manifest/lifecycle.py`'s `__all__` listed `PolicyStatus` alone, omitting the `as_utc` its own
  module docstring tells six siblings to migrate onto.

- **Review round: an overlay evaluating as core, and a blank value serving as approved.**

  A pack shipping an overlay in the same policy corpus had it evaluated as *core*.
  `DefaultPolicyExpert` defaults `core_policy_ids` to every policy it holds, and field precedence
  is registry order, so `ci-spread-core`'s `RB-CI-LEVERAGE-CEILING` claimed `leverage_x` ahead of
  the institution policy it narrows -- purely because `conventions.yaml` sorts before
  `core.yaml` -- and both core leverage rules stopped running. `leverage_x=3.2` produced zero
  findings. It survived only because the overlay's placeholder ceiling happens to equal core's.

  `PolicyScope` carried the answer all along: its docstring states the ladder ("product takes
  precedence over institution"), the pack declares `scope: product` on the overlay, and nothing
  in japes read the field. `Pack.core_policy_ids` and `Pack.overlay_policy_ids` derive from it, so
  a consumer hydrates the expert from the pack instead of guessing. Core governs by default and
  `program_id` activates the overlay, which is what `supersedes_core_rule` always claimed and
  never did.

  The first cut of that split was worse than the bug. Keying it on "is not institution" put a
  policy with *no* declared scope in the overlay set -- `Policy.scope` is optional and defaults to
  `None`, so `dscr_core` came back with an empty `core_policy_ids`, i.e. a consumer evaluating no
  policies at all. It splits on an explicit `PolicyScope.PRODUCT` now; an undeclared scope is the
  base of the ladder, and `DEAL` arrives per call rather than sitting in a registry. Caught by
  checking the second pack rather than by the round that followed.

  `Threshold.value` accepted `None`. YAML reads `value:` with nothing after it as null and `Any`
  took it, so one character separated a refusal from an *official-source, active, executable*
  threshold whose figure was `None` -- and the field's own description promised a number. Two of
  its three consumers turned that into a crash rather than a refusal (`decimal.InvalidOperation`
  in `evaluate_guard`, `TypeError` from the ratio evaluator's `float()`), neither caught by the
  handlers around them. Refused at validation now, as an omitted `value:` already was.

  Four test assertions read `profile.thresholds[...]` directly and would have broken against a
  `Threshold` object the first time a profile adopted the governance form the gate exists for.
  They use `get()`, which is the contract.

- **Inline pass over the round above, which found three things it had left.**

  The `Threshold.value` validator refused `None` and nothing else, so `value: ""`, a
  whitespace-only scalar, `value: []` and `value: {}` all still built an approved threshold that
  reached the same `decimal.InvalidOperation` -- the defect the validator was added for, in four
  further shapes one character apart. It refuses empty now. Deliberately *not* non-numeric: the
  shipped profile's `custom` holds `ineligible_states` and `high_ltv_eligible_property_types` as
  lists and the drift lint compares against them, so a non-numeric figure is legitimate. Zero is a
  figure and passes.

  `inapplicable_gate_outcome` had been applied to one of *two* hand-built sites, and it was the
  narrower of the two shapes: `check_graph`'s copy kept the gate's own `inputs` -- which say which
  values made the rule inapplicable -- where `run_segment`'s kept only a verdict summary. Adopting
  either side's shape would have silently narrowed the other, which having three copies concealed.
  The builder carries both, all three sites use the pair, and the only `NOT_APPLICABLE`
  construction left in the SDK is inside the builder itself.

  `Pack.core_policy_ids` returning `[]` for a pack whose every policy is `scope: product` is
  correct -- it contributes no core policy -- but it looks exactly like the bug where an
  *undeclared* scope emptied the set, so the distinction is written down rather than left to be
  rediscovered.

- **Review round: PASS, and four claims of mine that had drifted from the code beside them.**
  No defect survived the reviewer's own verification.

  `_value_is_present` had made `get_threshold` raise `pydantic.ValidationError` out of an accessor
  whose contract names `ThresholdNotActivated` and `KeyError` -- and made the two accessors
  disagree about whether a key resolves at all: `get` served `""` where `get_threshold` raised.
  Refused in the documented currency now, on the mapping precedent: `get` hands back what is
  there, and asked for a *record* of an empty figure there is none to give.

  `policy_violations_to_findings`' two newer branches set `detail["source"]` and cite "the
  violations loop above" for keeping their keys uniform -- while that loop, the one case this
  function has always produced, set no `source` at all. A consumer switching on it to tell a
  violation from a refusal got `None` for the commonest kind.

  Both `not_yet_effective` descriptions pointed a reader at `TODO(activation-vs-active-rules)` for
  why the list is reported rather than enforced. That TODO records the `_all_rules`/`active_rules`
  divergence and says nothing about it -- and correcting the TODO earlier in this branch is what
  left the pointer aimed at an unrelated deferral. The descriptions say the thing directly.

  And `as_utc`'s docstring named six modules carrying private copies as having "somewhere public
  to land", which reads as though they were converted. None is: each is module-private with
  in-repo callers and identical behaviour, so it is duplication rather than drift, and the
  conversion is available work rather than something that happened.

- **Review round: a vocabulary the pack's own matchers reject, and a guard that outgrew its
  tuple.** Slice 1 passed with no defect surviving verification; slices 2 and 3 blocked.

  The bundled `ci-spread-core` ontology enumerated `loan_type` as
  `abl | revolver | term_loan | ddtl` while all five matchers in the pack spell the fourth
  `delayed_draw_term_loan`, so a facility authored to the pack's own documented vocabulary matched
  none of them and fell through `diagnose_map`'s fallback to the ABL revolver playbook. Wrong
  guidance rather than an empty result.

  Two fields the pack's rules read were declared nowhere. `excess_availability_pct` meant
  `CI-ABL-MIN-AVAILABILITY` could return VIOLATED or INDETERMINATE and never SATISFIED, since
  `check_compliance` skips an indeterminate rule without recording it -- and the comment above
  that leg had reasoned twice about the *denominator* without asking whether the field existed.
  Sweeping every field the rules read against the ontology then found a second the finding had not
  named.

  `plato/guide.md` gained the two `/packs` routes the nav had already gained, and
  `test_the_guide_lists_the_withholding_on_every_gated_route` now covers all four routes that
  withhold -- it had stayed at three while `packs` became the fourth, so the guard passed while
  its own name stopped being true.

  A `plato/seed.py` comment credited a test name that no longer exists, and the
  missing-field deferral in the bundled DSCR notes discharged its risk by pointing at a schema
  that exists only in the authoring repo: for this copy, four of the fourteen PPP rules report
  NOT_APPLICABLE rather than denying when the field is absent, which the notes now say.

  **A mechanical break, and the guard that was missing.** One of those pack edits used a `replace`
  whose `old` string matched as a *substring* of a more-indented line, so `s.count(old) == 1`
  passed and the key was silently dedented out of its block -- five tests failed on unparseable
  YAML. The same hazard had already been observed once in this branch and noted as luck rather
  than defended against. Every YAML touched is parse-checked per edit now, not at the end of a
  batch: it is the class of defect a reading pass cannot see and one command catches.

- **Review round, slice 4: the guard that was not guarding.** Every finding was in a test of
  mine, and the first was the one holding the most important line.

  `test_a_bundled_seed_pack_is_loadable_in_a_japes_only_process` used
  `getattr(pack, attribute, None)`, and `AttributeError` is exactly what `_resolve` raises when a
  pointer's module imports but the symbol is missing -- so the default swallowed half the
  resolution failures the test exists to catch. Demonstrated: a manifest pointing at
  `plato.seed.NoSuchSymbol` returns `None` through the default and raises on direct access. The
  same default hid a dead entry: `conductor_pipeline` is not a `Pack` attribute at all, so one of
  fourteen names checked nothing. Direct access now, with every name asserted to exist first.

  `page.count("headers: headers(") == 3` counted the fetches that *do* carry the tenant header,
  not the fetches -- so a fourth `fetch(` without one would have left it green while answering 400
  on a deployed replica, the regression the test names in its own docstring. The two counts are
  compared to each other.

  Two more from the same family: the loadability test was parametrized on a literal pair of pack
  ids while its sibling nine lines up already iterates the tree, so a third bundled pack would
  have got the sibling's registry check and never the conductor/experts resolution where the
  unresolvable bindings lived; and that sibling hardcoded `pack_manifest.yaml` outside its own
  `try`, where `MANIFEST_NAMES` has two entries and `seed_packs` publishes either -- a pack
  carrying only `manifest.yaml` would have errored instead of reporting through `broken`. Both now
  go through the tree and `_manifest_of`.

- **First incremental round: 503 lines instead of 12,526, and the churn rate became visible.**
  The review's narrow mode had never once run -- its ancestry test asked whether the saved head is
  an ancestor of HEAD, and this loop amends every round, so an amended commit is never an ancestor
  of its replacement and every round fell through to the full range. Fixed in the script, and the
  first `WAS:` accounting the loop has produced accounts for all 26 of the previous round's
  findings: 16 FIXED, 10 STILL OPEN, 0 REGRESSED.

  What that made measurable: **three of this round's five new items were manufactured by last
  round's fixes.** The `ddtl` vocabulary pass landed on three of four `applies_to` lists, missing
  the loan-package scaffold -- and the ontology comment written in that same pass claimed "the
  manifest's two playbook `applies_to` lists", counting the two that already had the long
  spelling. Correcting "6 ratio thresholds" to 7 left "11 custom scalars" and "18 keys" standing
  while the same change added a twelfth custom key. And a new parenthetical called one rating
  scale "the only one in this playbook" where a second section has one. On a whole-branch diff a
  fix-introduced defect is indistinguishable from a pre-existing one; on a per-round delta it is
  just visible.

  Also closed from the standing list: the `TODO(seed-pack-vendoring)` docstring had been left
  ending mid-sentence at "...without that consumer's checkout. Two" by an earlier rewrite of
  itself, and `as_utc`'s docstring said six private copies where seven named helpers exist -- it
  omitted `plato/reference/model_overlay`, counting only the SDK ones, and an eighth module
  coerces inline without defining a helper at all.

  `relaxed_only` inherits `environment_tier()`'s fail-open: an unrecognised `JAPES_ENVIRONMENT`
  (`stg`, or a typo) reads as `local` and admits the pack writes. Recorded as
  `TODO(relaxed-only-fails-open-on-unknown-tier)` rather than fixed, because `deployed_posture`,
  `withholding` and `check_settings` all read that value the same way and `JAPESSettings`
  validates the name separately -- tightening this one gate would make it disagree with its three
  siblings. The TODO carries the review's own finding slug, which is the convention now in
  CLAUDE.md §7: a `# TODO(slug)` comment closes `path :: slug`, and it works in pack YAML as
  readily as in Python.

- **The deferral was wrong, so the gate is fixed instead.** `relaxed_only` inherited
  `environment_tier()`'s fail-open, and last round that was recorded as a `TODO` on the reasoning
  that `JAPESSettings` validates the tier name loudly elsewhere. It does not for this process:
  nothing in plato constructs it, and its `env_prefix="JAPES_"` binds `JAPES_ENVIRONMENT` alone --
  not the `JAPES_ENV`, `ENVIRONMENT` or `APP_ENV` that `environment_tier` also reads. Two of the
  deferral's three claims held; the load-bearing one did not.

  So `ENVIRONMENT=prodution` on a deployed replica resolved LOCAL and let an unauthenticated
  caller retire a published pack version -- no startup error, an ordinary 200. The gate refuses an
  unreadable tier now and names the variable to fix. Mapping an unknown name to LOCAL stays right
  for `environment_tier` itself: refusing to start a laptop over a typo is the correct trade for a
  startup check and the wrong one for a destructive write, which is the asymmetry this encodes.

  Both of this round's findings were against claims written in the previous one: that deferral,
  and a comment corrected from "two `applies_to` lists" to "all four" when three is the answer --
  `pb-ci-abl-001` is `[abl, revolver]` and correctly names no term-loan variant.

  The round itself: 160 lines against the previous 503 and 12,526 before that, 7 FIXED / 3 STILL
  OPEN / 0 REGRESSED, and the first five `ACCEPTED:` suppressions -- each carried finding answered
  in one line instead of being argued again.

- **All four findings this round were in the thirty lines written the round before.** The
  unreadable-tier gate closed a real fail-open and introduced three problems of its own, which is
  the churn rate the incremental mode now makes visible.

  It read `os.getenv` directly, so a posture variable that is *set but empty* -- a compose
  passthrough whose host variable is unset, a bare line in an env file -- counted as an
  unrecognised tier and refused the pack writes on a laptop where every other reader resolves
  `local`. `envvars` already owns that distinction: `env_text` exists because blank means *not
  configured*. Second time in this branch an emptiness check handled `None` and forgot `""`.

  The predicate moved to `jazzx_sdk.config.envvars.unreadable_tier_vars()`, beside the two other
  readers of those variables, instead of being built inline in a Plato helper reaching across the
  package for two private names.

  And hardening the write gate alone was the wrong shape. `environment_tier` maps an unknown name
  to LOCAL, so `ENVIRONMENT=prodution` resolves "not deployed" in `wiring_default`'s store and
  Knowledge Hub choices too -- a production replica quietly running an in-process store against a
  Mock Knowledge Hub, which is worse than the write it was admitting. `check_settings` refuses to
  start on an unreadable tier now, which is what covers readers a per-request gate cannot reach;
  the gate keeps its own refusal as defence in depth. The earlier argument that tightening one
  gate would make it disagree with its siblings was right, and the answer was to fix the siblings
  rather than to defer.

  Also: the summary line still described only the relaxed-posture refusal, and
  `if blocked and unrecognised` carried a term with no predicate of its own.

- **A job walked past the boot refusal.** Last round's claim that "refusing once at boot is what
  covers those" held for a serving role and not for `JAPES_RUN_MODE=job:*`: `load_wiring()` has
  already chosen sqlite and a Mock Knowledge Hub from the unreadable tier, `check_posture` printed
  the refusal, and control reached `run_job` -- the job completed its writes through the wrong
  backend. The schema refusal one block down already had the guard this needed; the posture
  refusal did not. A job exits 6 now, and the comment above the block says which role the
  `create_plato_app` backstop actually covers.

  `unreadable_tier_vars` also restated `env_text`'s blank-means-unset rule with `os.getenv` and
  two `.strip()` calls, in the module that defines `env_text` and while citing it by name. It
  calls it.

  Two docstrings and a vacuous test: `check_settings`' summary described only the
  identity refusal and not the unconditional tier one, and did not mention that passing
  `environment=` explicitly -- which the next paragraph recommends for tests -- skips it. And the
  test asserting the startup half never reached the entry point that decides what a refusal
  costs: its first version exited 4 on wiring resolution and passed for the wrong reason, so it
  now stubs `load_wiring` and fails with `0 == 6` against the unfixed code.

- **The mock Knowledge Hub answers the codes the real one does, so a caller's error branching can
  be trusted.** The HTTP double existed to give a pack a real round trip through the generated
  client, and then collapsed four service behaviours into `400`: a duplicate entity name, a schema
  validation failure, a missing `json_value` and a genuinely malformed body were indistinguishable.
  A consumer branching on `409` or `422` therefore passed against the double and broke against the
  service, which is the one bug class an HTTP double exists to catch. Verified against the Hub's own
  source rather than a consumer's comment: its v1 entity create enforces name uniqueness and
  answers `409`, and validation errors map to `422`.

  Uniqueness is enforced by the **app**, not the client double, and the first cut got that wrong.
  A client-level mock that raised on a duplicate handed its callers a path production cannot
  produce: the real `KnowledgeHubClient.create_entity` logs the status and returns `None`, which
  is what `EntityStore.create` documents and what `CanonicalStore.store_policy`'s `result is None`
  branch is written against. So the client keeps creating and only the HTTP app refuses, on a
  `(collection_id, name)` set it records as it creates -- the service is what enforces uniqueness,
  so the service stand-in is where it belongs.

  `MockKnowledgeHubClient` gained `EntityValidationError`, a `ValueError` subclass so anything
  already catching `ValueError` around a mock write is unaffected. Both the create and the update
  route map it to `422`, and both answer `409` on a name already taken in that collection --
  update included, because the real v1 PATCH maps its own `EntityValidationError` to `422` and an
  `IntegrityError` to `409`, and fixing only the create left the same collapse one route over. A
  rename frees the name it left, which is the only way a name is released (there is no delete
  route), so the app cannot refuse a name nothing holds.

  Two rounds of review found the ordering wrong in both directions, and both are now the
  service's. **Validation precedes the conflict**, because the real create validates before the
  insert whose integrity error becomes the 409 -- a body that is both a repeat name and
  schema-invalid is a 422, where checking the conflict first made it a 409. The app asks the
  delegate to validate without writing (`validate_entity`, and `validate_update` for the update
  route, which was extracted from `update_entity` so the effective-pair rule keeps one owner
  rather than being restated in the app). **A present-but-blank name is refused**, as the
  service's body model refuses it: an earlier cut stored it and then maintained the conflict set
  around it, modelling a state the Hub never reaches. And the conflict set is maintained on
  **both** halves of its `(collection_id, name)` key, since `collection_id` is patchable too --
  keying it on the name alone left a vacated name blocked and a taken one unrecorded, the latter
  being the quiet direction where the mock accepts what the service refuses. Names compare
  exactly, as the service's unique constraint does; stripping them folded ` e-1 ` onto `e-1` and
  invented a conflict.

  A `null` for either key field means "not supplied", not "set to None": the delegate writes a
  field only when it is not `None`, so a JSON null leaves the stored value in place. A round of
  this fix stringified it into the key as `"None"`, discarding the entity's live key and recording
  a phantom, after which the app accepted a duplicate the service refuses -- at 200, with a
  plausible body. A client that serializes unset optionals as null hits that on any partial PATCH.
  A blank `collection_id` is refused alongside a blank name, since the service types it `UUID` and
  no empty string parses as one. The create route draws the same null distinction, which took a
  further round: a null `name` passed its guard (`str(None)` is truthy), was stored as the field's
  value, and put the phantom `"None"` into the conflict set, which then refused an entity
  legitimately named `None`. The two routes still answer a null differently -- 400 on create, 200
  on update -- and that is the point rather than a leftover, since a create's fields are required
  and an update's are optional.

  Sixteen test functions, fourteen of which were watched to fail against the behaviour they pin: a duplicate
  create accepted as `201`, three `400`-vs-`422` cases (create schema, update schema, missing
  `json_value`), a schema-invalid duplicate answering `409`, a rename silently overwriting at
  `200`, a vacated name still refused at `409`, a blank name stored at `200`, a blank
  `collection_id` stored at `200`, a collection move leaving both directions wrong, a null key
  field poisoning the key on either route, and a padded name refused at `409`. The other two are controls that
  stop the change being satisfied by refusing everything: the same name in a second collection,
  and the client double creating both rather than raising. The
  missing-scalar-field `400` stays, now with a `TODO(missing-fields-still-400)` recording why: the
  real route's detail shape differs too, so matching the code alone would be half a fix.

- **The close budget is one budget, and the retired stores stay on the list until they use it.**
  `dispose_all` emptied the retired list before disposing anything, so a current store that stalled
  or raised took the rest with it -- dropped having been neither closed nor recorded, which
  narrowed the "drains that list when the process ends" sentence written one round earlier. It pops
  one at a time now, and the constant's comment says the bound covers the whole call rather than a
  single pool, which is what `asyncio.wait_for` actually wraps. A unit test retires two stores
  behind a failing current one and asserts both survive on the list; against the old ordering it
  reads `assert [] == ['first', 'second']`. Also: the blocking-dispose test pins `TimeoutError`
  rather than the prefix its raising sibling shares, and the two new env-name constants joined
  `__all__` beside `WIRING_ENV`.

- **The bundled `dscr_core` notes described a prepay default that no longer passes.** The pack's
  `ENCODING_NOTES.md` §1b stated `prepayment_penalty_requested` defaults to `"no_prepay"` and
  cited that as the reason no gold case needed updating. The consumer's default is `"unspecified"`
  now, so the 13 state buyout rules deny until the structure is stated, and the notes said the
  opposite of what the rules do. Corrected in the bundled copy, which is identical to the
  consumer's. The behaviour itself is the consumer's schema, not this repo's.

- **A `high`: every `job:*` role computed its exit code and then hung.** The boot contract
  promised a job exits 4, 5 or 6; only row 1 actually did. A `fabric.db` sqlite store runs one
  non-daemon `aiosqlite` worker thread per connection and nothing closed the pool, so the moment a
  role got far enough to open a store -- a posture refusal, a stale schema, *or a healthy sweep* --
  the interpreter never shut down and the code was never delivered. An ACA Job sat until its
  platform timeout, which a supervisor cannot distinguish from work in progress.

  `plato.wiring.release_wiring` closes the pools after the role decides its code, on every path
  including the serving ones, and `DatabaseHandle.dispose_all` drains the stores a `/v1/config`
  database swap retired -- which is what its own docstring already promised the process end would
  do. `run_role` split into a resolve-and-release shell plus `_run_resolved`, so one `finally`
  covers every branch.

  Closing the pools is not enough on its own, which the first cut of this fix got wrong: a raising
  `dispose` leaves the same thread alive, so swallowing that error kept the code and lost the exit.
  Delivering the code is the contract, so `plato.__main__` ends the process outright and
  `release_wiring` keeps the shutdown clean rather than making it possible. The exit handlers run
  by hand first -- `os._exit` runs none, and `jazzx_sdk.llm.config` registers the unlink for a
  decoded service-account key, so forcing the exit without them left a plaintext credential on
  disk after every run. Both are pinned: one test sabotages `dispose` and still expects the row's
  code, another runs a job with `GOOGLE_APPLICATION_CREDENTIALS_B64` set and expects no key left
  in `TMPDIR`.

  The review's follow-up round closed the rest of it. `release_wiring` runs in `run_role`'s
  `finally`, before the entry point's exit, so the guarantee covered a `dispose` that *raises* and
  not one that *blocks* -- an unbounded await there reproduces the same hang. The wait is bounded
  by `PLATO_POOL_CLOSE_TIMEOUT_SECONDS` (default 10, floor 1) and a third test holds it with a
  `dispose` that sleeps an hour. The `except` around `atexit._run_exitfuncs()` came out: atexit
  reports a callback's exception as unraisable and continues, so there was nothing to catch and
  the comment claimed a property that was atexit's. `_TIER_VARS` in the test now derives from
  `_POSTURE_ENV_VARS` instead of repeating its four names, and `swap_database`'s docstring no
  longer says the retired store "is never disposed" -- `dispose_all` drains it at exit, which is
  what `replace` had always promised.

  The test that was supposed to hold row 6 to its code path is the reason this shipped: it stubbed
  `load_wiring`, which is precisely the call that opens the store, so it asserted a return value
  from a process that in production never ended. Both untested rows are now subprocesses under a
  timeout that fails naming the hang, and both fail against the unfixed code. Checked and not
  changed: `KnowledgeFabric` has no `dispose()`, but neither sqlite shape leaks a thread through
  it, so the gap is Plato's rather than the SDK's.

- **A `high`: shipped behaviour changed without its declared contract.** `plato/boot_contract.py`
  is the single owner of the boot policy, and `plato/__main__.py`'s own rule is "a change to the
  policy is a change to `BOOT_CONTRACT`". The previous round made a job exit 6 on a posture
  refusal and left the row saying `job_exit=SERVES` -- so `JOB_EXIT_CODES`, the table rendered into
  `docs/DEPLOYMENT_ENV.md`, and the docs sentence calling those codes "the only exit codes worth
  branching on" all described behaviour the code no longer had. An orchestrator branching on 4/5
  would see an undocumented 6 while the documentation said the job ran.

  Invisible to the suite, which is the part worth keeping: the doc-table test asserts the docs
  equal `as_markdown_table()`, and both derive from the same row, so a change to the *code* alone
  drifts in all three artefacts at once without failing anything. Row 1 (`PLATO_WIRING` unset) had
  a test holding its code against its row; this row did not.

  The row, `JOB_EXIT_CODES` and the rendered table are in step, and the missing test now lives
  beside row 1's, asserting `entry.main([]) == rule.job_exit` rather than a literal 6 -- which is
  the assertion that would have caught this. Verified in both directions: a stale row fails
  `6 == None`, stale code fails `0 == 6`.

  Two attempts at that test were discarded first, both for the reason this session keeps
  finding: without `PLATO_WIRING` it exits 4 on wiring resolution and never reaches the posture
  check, and with `wiring_default:build` the subprocess blocks. It runs in-process with
  `load_wiring` stubbed, and the source-scraping guard written in between was dropped once the
  real-path version worked -- one guard that reaches its claim beats two that approximate it.

- **A rule can be authored, cited and reviewed before it may execute.** `Policy.status` was the
  only gate, and it is the wrong grain for a transcribed corpus: one policy holds forty rules of
  which two are approved, so promoting the policy promotes all forty. `PolicyStatus` gains `seed`
  (transcribed from a source that is not the approved edition -- nobody is drafting it, and it must
  never yield a number) and `suspended` (withdrawn without a successor, which `deprecated` implies).
  `Rule` gains `status`, `effective_from`, `effective_to` and `approval_refs`, plus
  `activation_block` -- a sentence rather than a bool, because a caller answering "why can I not
  evaluate this" has to report it. `Policy.executable_rules` and `activation_blocks` are the
  publish-everything, compute-with-the-approved-few pair.

  A rule may restrict itself below its policy and may not promote itself above it. The first
  version read the rule's own status outright, so `status: active` inside a seed policy executed,
  which is self-promotion out of an ungoverned corpus and what a bulk edit over dozens of
  transcribed rules does by accident.

  Nothing in the evaluation path reads any of it. Most packs here are `draft`, so gating evaluation
  on status would stop them all evaluating; this is vocabulary plus an opt-in query, and wiring it
  in is a later, deliberate change.

- **`IndeterminateReason`, because "no answer" has causes that need different handling.** Missing
  inputs are a request for evidence; a derivation that could not run is a retry; a rule that exists
  but may not execute is a configuration problem -- and that last one is indistinguishable from the
  first two from outside, while the fix is to pin an approved source rather than go and find a
  document. Four values, a validator refusing the field on any verdict but `INDETERMINATE`, and
  `RuleOutcome.not_activated` to build the outcome an unapproved rule owes its caller.

  Deliberately not a new closed outcome enum: `Verdict` already carries satisfied/violated/
  not-applicable/indeterminate with an algebra, and its docstring already separates indeterminate
  from not-applicable. Routings like pre-review and waiver are `RuleAction.ESCALATE` and
  `REQUIRE_APPROVAL`. A second vocabulary over the same ground would have duplicated both.

- **A threshold can be held without being usable.** `PolicyProfile.get` was fail-closed on an
  absent key; the case it could not express is a key that is present and must not be served -- a
  grid restated from a source nobody approved, where handing the figure back as though it were the
  institution's policy is the risk. `Threshold` carries value, `ThresholdProvenance`, status and
  citation. `get` resolves it to its value, so arithmetic at the call site is unaffected by a
  profile adopting the richer form, and raises `ThresholdNotActivated` when the status does not
  allow it -- not a `KeyError`, because "no such threshold" and "present, not approved" need
  different handling. `get_threshold` returns the record for a report, wrapping a bare value as
  institution-authored and active, which is what authoring one has always meant. Wrapping defaults
  to `seed`: a threshold is wrapped because its provenance is in question, so the refusing status
  is the right default rather than the one you must remember.

  All three buckets `get` searches are gated, not just `thresholds`.

- **`PolicyStatus` moved to `jazzx_sdk.manifest.lifecycle`,** re-exported from
  `fabric.canonical.policy` so every existing import resolves. `profiles` needs it and importing it
  from `policy` cycles (`policy` reaches `finance.periods`, which imports `PolicyProfile`). It is
  `autonomy.py`'s shape: a vocabulary several layers share, depending on nothing.

  The review round on all of the above found the gate did nothing in any real pack. It fired on a
  `Threshold` *instance*, and YAML -- the only authoring path a shipped pack has -- yields a plain
  dict, so `get` returned the whole mapping and `get_threshold` reported a seed/secondary-source
  figure as institution-authored and active. An affirmative false statement about provenance, on
  the one feature whose purpose is refusing unapproved figures, and every test passed because they
  all built `Threshold` in Python. Coerced at validation now, bounded to mappings that carry
  `value` and nothing but `Threshold`'s own fields, and tested through `from_yaml`.

  Three more in the same round. `executable_rules` gated on `status` alone, so a policy outside its
  own window reported every rule executable and no blocks -- it checks `effective_date` too, which
  `is_active` does not. `effective_status` discarded the rule's own status whenever the policy was
  not active, so an `archived` rule in a `draft` policy answered `draft`, losing a restriction it
  had declared and contradicting the docstring; the test for that direction only covered the active
  policy. And blame was inferred by comparing the resolved status against the rule's own, so a draft
  rule in a draft policy read "rule is draft" when the rule adds nothing.

  `ThresholdNotActivated` also escaped the two handlers that catch `KeyError` only: the statemachine
  guard now returns `guard_not_activated` and the ratio evaluator an `INDETERMINATE` carrying
  `policy_not_activated`. Nine sibling sites in `condition_evaluator` -- the default evaluation
  path, unlike the adjudication one first annotated -- name their cause. `profiles` imports
  `PolicyStatus` from `manifest.lifecycle`, which is the decoupling that module was added for and
  did not take.

  A second round on the same code, answered mostly by deleting. `effective_status` promised the
  narrower of a rule's status and its policy's over a set with no ordering, so each version was
  wrong in whichever direction the last had fixed -- `archived` rule in a `draft` policy answering
  `draft`, then `draft` rule in an `archived` policy answering `draft`. It is gone;
  `activation_block` names both causes when both block and nothing ranks them. `RuleOutcome.
  not_activated` is gone too: no caller, and its default status string was a third pack vocabulary
  beside the `INDETERMINATE` everything else uses. And `Threshold.value` no longer claims to hold a
  table cell, since `tables` has no gate -- a nested shape rather than a wider version of this one,
  recorded as `TODO(threshold-grid-provenance)` rather than built on a round that had already found
  two coercion defects.

  The coercion was one of them: keyed on "every key is a `Threshold` field", a bare `{value: 7}`
  became a *seed* threshold and `get` refused profile data that had always resolved. Breaking a
  working profile to gate a problem it does not have is the worse failure, so a governance field is
  required as well. `ThresholdNotActivated` subclasses `ValueError` and `finance.validation` had a
  pre-existing `except ValueError` around a `profile.get`, which swallowed the refusal and let the
  finding take its default severity -- invisibly, which is the mode this feature exists to prevent.
  And the composite `all_of`/`any_of` outcome dropped its children's `indeterminate_reason`, so a
  seed threshold nested in a composite reported no cause at all.

  A third round found the consumer nobody had checked. `fabric.graph.check.finding_from` derives
  its rationale from `verdict == INDETERMINATE` and *asserts* the cause -- "the case does not supply
  <reads>" -- so a rule blocked by an unapproved threshold produced a governance-facing escalation
  saying the case had withheld values it had in fact supplied. Adding a producer and not visiting
  the consumers is the symmetry rule failing on its own subject. Each cause now says what it means,
  with the missing-inputs sentence kept for `EVIDENCE_MISSING` and for an outcome carrying no reason.

  `executable_rules` and `activation_blocks` read `rules` only, while `get_rule` and
  `PolicyRegistry` both treat `exception_rules` as first-class -- so a seed exception rule was
  missing from the executable set and from the blocks, invisible in both directions. The threshold
  coercion could also fail a whole profile load: `{value: 5, status: ok}` matched the predicate and
  then raised, reported against `custom.status` rather than `custom.<key>.status`. It leaves a
  mapping as authored when it will not construct.

  Three copies of "read a naive bound as UTC" became `_as_utc`, one of them pre-existing in
  `is_active`. `manifest` exports `PolicyStatus` beside `AutonomyLevel` and `SurfaceType`. The
  reason validator no longer adds a second error when `verdict` itself failed validation. And the
  composite's reason pick is described as arbitrary, which it is.

  A fourth round found the feature answering `allowed=True` on adoption. `check_compliance` skips
  every `INDETERMINATE` as "required context data missing", so a rule whose ratio threshold was
  declared-but-unapproved was dropped from `applied_policies`, raised no violation, and returned
  "No policy violations detected" about a governing rule nobody had cleared -- `warnings=[]` was
  hardcoded at both return sites. `POLICY_NOT_ACTIVATED` withholds the allow and names the rule
  now; missing data still skips. The adjudication applicability gate had the same shape, recording
  `NOT_APPLICABLE` -- whose field doc reads "a structural applicability check said this rule doesn't
  apply" -- for a rule that does apply.

  The grid TODO's justification was false. "No shipped profile authors a grid" was read off a grep
  of this repo; the consumer's own profile carries 150 cells across five grids from the same
  unapproved document as its seven `thresholds:`, so the gate covers seven of its numbers and not
  the rest. Not a regression, and now stated.

  `as_of` was left as passed while the bound was normalised, so a naive one -- the documented pack
  shape -- raised `TypeError`; the bound-side test covered half the comparison. `is_active` defers
  to the same window as `executable_rules`, so a future-dated policy no longer reads active in the
  governor and staleness paths. `get_threshold` no longer reports a mapping the coercion declined as
  institution-authored and active. `finance.validation` catches `KeyError` as well, a pre-existing
  crash on the line being edited. And `as_utc` is public on `fabric.canonical` rather than a private
  name imported across modules, which retired a fourth open-coded copy in the staleness path.

  A fifth round found the same defect one `if` above the one just fixed. `check_compliance`'s
  *applicability* branch still skipped every non-SATISFIED gate, so a rule whose gate read an
  unapproved threshold answered "All policy gates passed" -- and the adjudication twin, whose
  docstring says it mirrors this function exactly, had received the branch while this had not. Both
  share one warning builder now, which also carries `policy_id`, since two policies in precedence
  order can hold the same rule id.

  The composite masked it too: `reasons[0]` picked by child order, so a first child that was merely
  missing data hid an unapproved sibling and the composite read as a data gap. The comment called
  that pick arbitrary while it had become load-bearing for the allow decision. `POLICY_NOT_ACTIVATED`
  wins. The rationale also reported only the unapproved count when a run had both, dropping the
  violation text for any caller that surfaces it rather than iterating `policy_violations`. And
  `policy_lint.find_profile_literal_drift` compared a `Threshold` object against a literal, so an
  *approved* wrapped value reported drift and the assert form raised on a profile that had not
  drifted; it reads through `get_threshold().value`.

  What a mapping claiming governance it cannot back does has now taken three positions: it failed
  the profile load, then was served as authored while `get_threshold` refused it, and now both
  accessors refuse the key and the load succeeds. The middle one had `get` -- the accessor feeding
  arithmetic -- as the lax one, which is what made it wrong. One `_looks_authored` predicate decides
  for both so they cannot drift apart again.

  A sixth round found the third applicability-gate site and, more usefully, named why two rounds had
  missed it: the rule was written inline in three callers instead of once beside the dispatcher they
  all use. `gate_blocks` sits there now. The missed site was the worst of the three -- `check_graph`
  builds findings for VIOLATED and INDETERMINATE only, so recording `NOT_APPLICABLE` dropped the
  rule from the result with no signal at all, and the `_UNTESTED_RATIONALE` entry added for exactly
  this cause was unreachable from the gate path.

  Making `is_active` cover the whole window had a consequence one caller away: `detect_staleness`
  reported "status is 'active' (or past expiry), not active" for a future-dated policy. `not_in_force`
  is public, so the reason is the policy's own sentence. `policy_lint` was still reading the wrong
  bucket -- the previous fix went through `get_threshold`, which searches `thresholds` first, so a
  key in both was compared against the wrong value under a message naming `custom`, and a refusal
  could raise out of a function documented to return findings.

  `ComplianceResult.warnings` described itself as non-blocking while `allowed` is now derived from
  it. The composite warning no longer degrades to a bare "not activated": the refusal sits in a
  limb. And a find/replace had turned `fabric.graph.check`'s module docstring into a 210-character
  line quoting text the code never emits.

  A seventh round found the same class as the fourth, one field over. `_looks_authored` required
  ``value``, so a block declaring `status: seed` and forgetting its number was not a threshold at
  all: `get` handed the raw mapping to arithmetic and `get_threshold` called it institution-authored
  and *active*. The governance claim is the whole test now, value or not.

  `policy_violations_to_findings` read `policy_violations` only, so `allowed=False` with an empty
  violation list produced no findings and `validate_package` reported a clean spread for a deal the
  expert had refused -- the in-repo instance of the caller shape the rationale fix two rounds earlier
  was reasoning about, fixed where it was looked at and not in the sibling. The nested-limb search
  went one level, so a grandchild refusal lost the threshold key.

  `_all_rules` does not apply the `legacy_alias` filter `active_rules` does, so a sunset rule reports
  executable and is never evaluated; `TODO(activation-vs-active-rules)` records it rather than
  changing what `active_rules` means for a caller that does not exist yet. Two docstrings corrected,
  one of which contradicted a sibling three lines above it.

  An eighth round, and the first with no high finding. Four of its five were the seventh round's own
  debris: the warning findings carried no `policy_id`/`rule_id` in `detail` while the sibling loop
  twelve lines above carries both, so a consumer keying its review picker on `rule_id` gave two
  unapproved rules in one policy the same key and kept one; the adjudication gate hardcoded
  `POLICY_NOT_ACTIVATED` where its sibling propagates the gate's own reason, which is wrong the
  moment `gate_blocks` admits a second; `policy_lint` reached through `PolicyProfile._looks_authored`,
  so the predicate is public; and two docstrings, one of them the previous round's own rewrite.

  Left as it stands, with the reason: a policy with `status: active` and a future `effective_date`
  now reports in `stale_policies`, which means the opposite of what happened. A second bucket on
  `StalenessReport` is a change to the expert contract for a case neither repo authors, and
  enforcement is unaffected -- `resolve` builds `precedence_order` from the pack's own ids, never
  from `is_active`.

- **Plato serves a published domain pack.** The answer to *what consumes one*: it had no notion of
  a domain pack at all -- every pack path was the assistant kind that `build_from_manifest` binds,
  so a `Pack` had nowhere to land and a domain pack could be published, materialized, and still
  unusable.

  `plato.packs.domain.published_domain_packs(store)` is the mirror of `published_registries`: same
  tenant scoping, same materialize-then-load, same `assistant_id` discriminator, returning `Pack`
  objects. `domain_pack_summary` gives an operator surface counts and ids rather than contents,
  catching per pack so one malformed pack cannot blank the view.

  `Pack`, not a new type: everything a domain pack means is already its surface, and a second
  object over the same manifest would be somewhere for the two to disagree. What was missing was
  never the object, only a way to get one per tenant without a checkout.

  A bug in the first version, caught by the two-halves test: it loaded via
  `Pack.from_manifest(pack_id, root.parent)` on the claim that `materialize` returns the pack's own
  directory -- true only when the archive *nests* it. A flat archive unpacks with the manifest at
  the cache root, so the parent was a level too high and the id lookup found nothing. It loads from
  the returned root now.

  Proven on an authored pack through a real store: publish, `published_domain_packs`, and the
  eligibility grid's `dscr_min_high_ltv` comes back `1.20`. The companion test asserts each
  resolver returns only its own half, since a store holds both shapes.

  The round on it also found the `profiles.default` branch re-reading by path instead of matching
  what `profile_files` found -- so a `default:` naming a missing file warned, let `policy_profiles`
  succeed, then raised `FileNotFoundError`. It falls through with a warning now. `profile_files`
  and `policy_files` were the same twenty lines twice; both call one `_declared_files` with a
  per-kind `keep` filter, which is where that filter should have lived to begin with.

  And the tests hardcoded a consumer checkout's absolute path -- one machine's layout and another
  repo's name in committed code -- when this repo already had `JAPES_REAL_PACKS_DIR` for exactly
  that, with the reasoning written down. Both use it now.

  The round after that found the case a published domain pack actually hits: `Pack.from_loader`
  leaves `_packs_root` unset, so `_can_merge` is permanently false and a pack declaring
  `depends_on` returned only its *own* playbooks, evidence types and skills -- silently, against
  `evidence_types`' own promise that the local list is what a caller gets only for a pack with no
  dependencies. Real packs declare them. A materialized cache has no siblings to merge from, so it
  warns and names the dropped dependencies; publishing the closure is what `pack_dependency` is
  for.

  Two claims of mine were false again. "One load, both views" described a plain method that
  `policy_profile` reads twice, so every declared YAML was re-parsed on each read -- measured at
  four `from_yaml` calls per call and four more per re-read, now two, one per profile, as a
  `cached_property` like every sibling accessor on that class. And the `Raises:` block said a
  validated field "cannot be wrong by the time this runs", which `model_construct` and
  `model_copy(update=...)` both walk past in pydantic v2.

  Smaller, from the same round: a `default:` naming a missing file raised "declares 2 profiles and
  no `profiles.default`" when one *was* declared and merely unresolvable -- two situations, two
  messages now, since the exception is what a caller sees while the warning only reaches a log; and
  the summary handlers reduced an exception to its type name with nothing logged, leaving an
  operator able to see a pack was broken and unable to learn which file.

  The push-time round found the two ways `policy_profile` could hand back the wrong institution's
  thresholds. Keyed by `profile_id`, two files declaring the same id collapsed into one entry, so
  the single-profile branch returned whichever parsed last -- measured: two profiles, `9.99` from
  the second file, no warning. And an id the pack does not declare answered `None`, which is what a
  pack with no profiles at all answers, so `pack.policy_profile(pinned) or pack.policy_profile()`
  fell back to the default institution when a pinned id went stale. Both raise now, and `None`
  means only the one thing the docstring attributes it to. `plato.packs.domain` also read a literal
  `pack_manifest.yaml` while the store had a constant for both spellings -- that constant is public
  now and shared, since it exists *because* the store and its reader disagreed about the name once.

  The full-range round after it found the profile accessors' remaining hole and the one the archive
  guards left. A ``dir:`` scan reads every YAML in the folder, so a `notes.yaml` beside a profile
  made `PolicyProfile.from_yaml` raise and `policy_profiles` return *nothing* -- not the stray file
  skipped, the pack's real profile gone. `policy_files` had taken `keep=is_policy_document` for
  exactly that since it was written; profiles now have `is_policy_profile_document` beside
  `PolicyProfile`, and `keep` applies to the folder scan only, so a path the manifest names
  outright still fails loudly instead of vanishing as though it were somebody's notes.

  And `publish` requires archive bytes without validating them, so a row whose archive is not a
  zip, whose blob the store no longer has, or whose digest does not match reached `materialize`
  and took the whole composition down -- the failure `published_registries`' own docstring said it
  refuses, true until then only of the two branches that had guards. Both resolvers guard the row
  now and name the pack they skipped. What is left is stated rather than implied: `tenant_registries`
  reads each root through `load_pack` after the loop, so a well-formed archive that is not a loadable
  pack still aborts, and guarding that means composing pack by pack instead of handing over a root
  list. A `TODO` says so at the call site.

  Smaller, from the same round: `"assistant_id"` was spelled independently in both resolvers to tell
  the two pack shapes apart, which is what `MANIFEST_NAMES` had just been made public to stop --
  `is_assistant_pack` sits beside `PackVersionRecord` now. `reason`'s ``limit`` reached six more
  call sites whose text is served or stored (three `TokenError` messages, the key-fetch message, the
  schema-check note and three boot notes); the one left uncapped prints to stderr from the CLI. The
  abstract `materialize` named only `PackNotFound` while its implementation raises three more
  things. And the duplicate-`profile_id` message named the second file and "another", so an author
  still had to grep the folder for the pair.

  The round after that found the first of those fixes was half a fix: `policy_profile` returned
  `None` before it looked at the id, so a named id against a pack declaring *no* profiles still
  came back `None` -- the conflation the branch exists to refuse, surviving in the one case with
  nothing to compare against, with the docstring's two sentences contradicting each other over it.
  The id check runs first now.

  It also found the asset joins. Every `pack_id` join got `bare_name` in this release while the
  eleven joins that resolve *manifest*-declared paths got nothing, though the manifest is the less
  trusted of the two once a pack arrives from a store: `materialize` unpacks a published manifest
  and hands its root to the loader. Measured before the guard: `policies: {core: ../../elsewhere/
  leak.yaml}` came back from `policy_files()` as a path outside the pack, and `load_policies` read
  it. All eleven go through one `_asset_path` now, on `relative_name` rather than `bare_name`,
  because a declared asset nests (`policies/overlays/rb_ci.yaml`) and only escaping is the fault.
  One of them turned out to join `""` for a playbook entry with no `path:` and fail on the pack's
  own directory; it warns.

  `reason`'s ``limit`` reached six more sites, the ones that put it in a *returned* object rather
  than a log: three `Refusal.message`, `InteractiveResponse.incomplete_reason`, a span attribute
  and a Trace note. Five stay uncapped, all log-only, two of which build their served body through
  `redact_secrets` separately.

  Three smaller ones. `domain_pack_summary` left `has_policy_registry` unassigned when `policies`
  raised, so a consumer reading it got a `KeyError` instead of the error reported beside it. Both
  `prompt_loader` `Raises:` blocks credited the `ValueError` to `pack_id` when `mode_name` is
  checked first and unconditionally -- and `modes/base.py` quotes one of them as its contract. And
  a comment called `register_all` a module.

  A third round, on the profile filter added two rounds earlier. Its docstring claimed a malformed
  profile "still fails loudly", and the one malformation that matters does the opposite: the shape
  check reads `profile_id`, so a file spelling it `profile-id` loses the only thing telling it from
  somebody's notes and is skipped like notes -- `policy_profile()` then answers `None`, which is
  the one meaning that method reserves. The claim went rather than a third case being added to the
  predicate; `_declared_files` logs every file `keep` rejects, at debug, because a pack legitimately
  holds other assets in that folder and a warning would fire on every load of one.

  `published_domain_packs` read `depends_on()` inside the per-row load guard, so a manifest naming
  an unknown fragment kind dropped a pack whose `pack_id`, `version` and `policy_registry` all
  resolved -- and since `published_registries` never calls it, the same row composed as an assistant
  pack and vanished as a domain one. The advice now runs after the pack is in, guarded on its own.

  Not everything the round raised was true: it reported a `profiles.default:` naming a missing file
  as returning `None` with no diagnostic, and `_declared_files` already logs "not found" on that
  path. The duplicated row loop it flagged for a third time is real and now carries a
  `TODO(share-published-row-loop)` with the shape it should take: both readers are still test-only,
  and they are also where the two pack shapes are defined, so folding them together in the same
  pass as two defect fixes would settle that by accident.

  `is_policy_profile_document` says why it is not `is_policy_document(key="profile_id")` -- a bare
  top-level list is a policy document and not a profile. `env_text(*names) if names else ""` lost a
  branch that could not run. And `_archive` in the store tests takes a manifest override, because
  the loader reads the manifest the archive carries while the published dict sets the row's columns
  -- a distinction a test asserting on `depends_on` needs and did not have.

  A fourth round, and none of it in the profile accessors, which have settled. Two defects, both
  claims that read as enforced and were not. The cache-marker containment check used
  `Path.is_relative_to` on unresolved paths, and pathlib does not collapse `..`, so
  `<entry>/../../elsewhere` is relative to `<entry>` by that test -- measured `True`. The marker is
  a file in a predictable shared directory whose contents come back as a pack root, and the branch
  returns before the digest is re-verified, so nothing downstream would have noticed. `_unpack` had
  resolved both sides all along.

  And `list_packs` was documented as "the most recent version of each pack" while the query orders
  by `published_at`: publish `0.2.0`, then a `0.1.1` backport, and it answers `0.1.1`. The
  `publish-tick-tie` note deferred that alongside the same-microsecond tie on the grounds that it
  "needs two round-trips inside one microsecond", which is true of the tie and false of this -- an
  ordinary sequence of two calls. Last-published is the right answer for "what did this tenant last
  ship", so the wording moved rather than the ordering, and both `list_packs` and `get` now say
  "published, not highest"; ordering on a parsed version needs a prerelease policy no caller has
  asked for.

  Both sibling guards this release wrote lessons for and left on the old spelling are lined up:
  `DomainPackFabric`'s two manifest-path joins take `relative_name` like the eleven on the
  `PackManifestLoader` side, and `plato.packs.loader` moved from `startswith` to `is_relative_to`
  -- the check whose own comment in `store_db` explains why `startswith` admits a same-prefix
  sibling. `MANIFEST_NAMES` moved to the host-free `store` module, since a reader wanting it was
  importing the sqlalchemy one for a two-element tuple. And "name one" now says how, for the list
  form of `profiles:` that has nowhere to put a `default:`.

  A fifth round came back with no defects. Two of its three notes were worth taking. `materialize`
  answered two different `Path`s for one directory -- the unpack branch unresolved, the cache-hit
  branch resolved, and on macOS `gettempdir()` is `/tmp`, a symlink to `/private/tmp`, so one
  version came back as `/tmp/japes-packs/<digest>` and then `/private/tmp/...`. Its test passed only
  because pytest's `tmp_path` is already resolved; it asserts a resolved answer now.

  And `limit=200` was a bare literal at nineteen sites, all added in this release, which is how a
  twentieth picks a different number -- Plato's settings paths already carry unrelated `120`s and
  `_safe_detail` a hardcoded 1000. It is `SERVED_REASON_LIMIT` now, exported alongside `reason`
  since a caller passing `limit` needs it. The pre-existing `120`s are left alone: nothing shows
  they answer the same question.

  Declined, with the measurement: converting the two archive-member guards to `relative_name` was
  offered as placement only, and is not. `relative_name("a/../b")` refuses while the resolve-and-
  compare accepts it, correctly -- it stays inside the root. Uniformity there would tighten which
  archives unpack, on a guard that is right as written.

  A sixth round crossed the size limit and reviewed in two slices, which is how `wiring_default`
  and `app.py` got read properly for the first time -- the fifth round's clean pass had covered
  them in one skim. Two defects, both with a running consequence.

  `discover_root` walked out of `site-packages`. A wheel at
  `<proj>/.venv/lib/python3.12/site-packages/plato/` resolved `<proj>`, so `_REPO` -- which feeds
  the sqlite path and the alembic run -- pointed at an unrelated consumer's tree. The `parents[1]`
  it replaced was accidentally safe there: it answered `site-packages`, failed the marker and fell
  through to cwd, which makes the resolver a regression on that one path. The walk stops at an
  install directory now, for every caller. The docstring had named the risk and waved it off as
  "unreachable in the image -- the cwd fallback still answers there", wrong twice: cwd is never
  consulted once discovery succeeds, and the image is safe because nothing above `/app/plato/`
  carries a `pyproject.toml`.

  And the re-wire compared against a boot snapshot no swap updated, so after the first one it was
  wrong in both directions: an unrelated config write still differed from boot and swapped again,
  leaking an engine, since `swap_database` disposes nothing; and a path moved a -> b -> a matched
  boot, so it returned early while the process kept writing to `b` and `/v1/config` reported `a`.
  It tracks the live wiring now, recorded after the swap rather than before, so a swap that raises
  does not register a state the process is not in.

  A third reachability claim was false in the same way as the other two. "A staging or production
  deployment cannot get here at all" is not what the code enforces: `withholding` returns false as
  soon as `auth` is not None, so a strict deployment built with an auth dependency can PATCH a
  bootstrap key and run `create_all()` DDL against its real database. Corrected in the three places
  that asserted it; the gate itself is as designed, since authenticated writes are what passing
  `auth` is for.

  Smaller: two comments in `plato.packs.domain` had gone stale against their own code -- one still
  listed unknown fragment kinds among what the load guard catches after `depends_on()` moved out,
  and the other claimed the round-4 reordering stopped a consumer's `KeyError` when `policy_registry`
  is the statement that raises, so it did not. Absent-on-failure is a documented contract there now.
  `SERVED_REASON_LIMIT`'s note said "a bare 200 at nineteen call sites" without adding that fifteen
  of them passed no limit at all before this release, which makes adopting it a truncation change
  and not only an extraction. The store contract exports from `jazzx_sdk.pack` alongside the rest,
  as `jazzx_sdk.runs` does for its own, with `store_db` still behind its own import so sqlalchemy
  stays off the eager path.

  A seventh round, sliced again, found the cache branch trusting the marker to mean the tree is
  there. A cleaner sweeping `gettempdir()` takes the extracted files and leaves the marker -- every
  `materialize` refreshes the marker's atime, the files' not -- and the branch then answered with a
  directory holding nothing but the marker. Forever, with the archive intact in the blob store and
  nothing logged: downstream a published pack was silently dropped, and recovery meant deleting the
  marker by hand. It checks for a manifest and re-unpacks now.

  The three served error envelopes -- the queue processor's terminal reply, the server handler's,
  the runtime handler's -- put `redact_secrets(str(exc))` into a response with no bound, which
  earlier rounds of this release mistook for a log-only site and left alone. `SERVED_REASON_LIMIT`
  applies to all three, and to `kid` in the OIDC unknown-key refusal, which comes from
  `get_unverified_header` and is caller-chosen in both content and length.

  Four claims were wrong. `roots`'s header said `env()` where the code uses `env_text` for a
  distinction a test pins. `content_digest` was documented as covering "the archived asset bytes",
  which a manifest-only row does not have -- it digests the manifest. And a test docstring said
  "three of seven" and "one of the six" for a `register_all` that builds seven stores across eight
  tables, the same drift the route's own comment dropped its count to avoid.

  The migration-head test was a step from breaking on the next generated file: `script.py.mako`
  emits `${repr(...)}`, which Python renders in single quotes, and alembic names files in hex -- so
  a generated revision matched neither the `[0-9]*.py` glob nor the double-quote pattern, would have
  been left out of the chain, and the assertion would have failed over a head it had not read. Both
  halves demonstrated on a file shaped the way alembic writes one.

- **The cache marker was trusted, not checked.** `materialize` short-circuits on a
  `.pack_manifest_root` marker and returned the path it names -- a file in a predictable shared
  directory (`gettempdir()/japes-packs/<digest>`), whose contents became a pack root, from which
  `Pack._resolve` will `import_module` a manifest pointer. The deferral recorded in that code
  covered trusting an already-unpacked *tree*; a pointer out of the cache is a different thing.
  A marker naming anything outside its own cache entry is now ignored, warned about, and
  re-unpacked. Its sibling containment check moved from `str.startswith` to `is_relative_to`:
  without a separator, `../<same-prefix>extra/x` resolved to a sibling of the root and passed the
  guard whose stated purpose was to fail on a member that tried.

  `mode_name` turned out to be the other half of the join the pack-id guard had just closed: same
  `read_text` expression, plus three more in the same module. Checked once where it enters each
  public function rather than at four joins, which is the shape the `pack_id` guard should have
  taken too.

  And the `-`/`_` spelling rule -- left duplicated on purpose two rounds earlier, on the argument
  that folding two callers together in the same pass as a defect fix invites a third finding -- was
  raised again, so it is one `id_spellings()` now, shared by `pack.roots` and `from_pack_id`.

  Three claims corrected with them: the summary docstring said all four metadata reads were
  defensive when they sit outside the handlers, and two test docstrings said `fragments: [profiles]`
  lets a dependency import a profile. It validates and merges nothing -- `_MERGE_ID_FIELD` covers
  playbooks, evidence types and skills only -- exactly as for `ontology` and `mode_tuning`.

- **The review's own state file could narrow against abandoned history.** `saved_upstream` was
  compared as a *label*: `HEAD~1` equals `HEAD~1` while resolving somewhere else entirely after a
  squash or a branch switch, so the comment's claim that "a different range does not inherit the
  wrong state" was not something the code checked. It now requires the saved head to be an
  **ancestor** of HEAD; accepts a rewritten-history-but-identical-tree case as "nothing changed",
  which is what an amend or a squash of already-reviewed work is; and otherwise declines to narrow
  rather than diffing two unrelated trees and reporting their difference as a change.

- **A pack can declare its policy profile, so a published pack is usable from its manifest.** The
  question that closes: *what consumes a published domain pack?* Investigating DSCR as Plato's use
  case found the blocker sits upstream of Plato. A pack's policies name thresholds and the
  `PolicyProfile` is what those names resolve to, and `FRAGMENT_KINDS` had no `profiles` -- so the
  one asset that makes the rules mean anything was reachable only by a path its consumer hardcoded.
  Workable from a checkout; impossible from a store, where the manifest is the only thing that
  travels with the bytes. A pack could be published, materialized, and still not usable.

  `profiles` is a fragment kind now, with `PackManifestLoader.profile_files()` taking the shapes
  `policy_files()` already takes -- `dir:`, `default:`, a bare path, a list -- plus
  `Pack.policy_profiles` keyed by `profile_id` and `Pack.policy_profile(id=None)`.

  Two decisions in that accessor. No declared profile answers `None` rather than raising: a pack
  legitimately has none, and a caller that needs one can say so more clearly than the accessor can.
  Several with no `default:` *raises*: a `PolicyProfile` carries an `institution_ref`, so more than
  one is a legitimate shape, and taking the first of an unordered set is how a run silently applies
  another institution's thresholds.

  Proven on the shipped DSCR pack rather than a stand-in -- `policy_registry` from `policies.dir`
  and `dscr_min_high_ltv: 1.20` from the declared profile, both through the manifest with no
  consumer naming a file. That test skips when the consumer's checkout is not beside this one,
  since a missing fixture is not a defect. Seven tests, all failing against the code before.

  `FRAGMENT_KINDS` is pinned by a snapshot test, which failed and was right to: adding a kind
  changes what every pack manifest may declare. Updated deliberately, with the reason in the test.

- **`packs_root` is resolvable, not just accepted.** `PackManifestLoader.from_pack_id(pack_id,
  packs_root)` always took the root from its caller and nothing here supplied one, so a consumer
  computed its own -- typically by counting directories up from `__file__`, a count correct only
  for the nesting of the file it sits in. Move the module and its path breaks and nothing else,
  which reads as a missing pack rather than an import error.

  `jazzx_sdk.pack.roots` supplies it: `discover_root` finds a project root by marker rather than
  by counting, `resolve_packs_root` consults an environment override *first* so a deployment with
  no repo above the installed package still works, and `resolve_pack_root` reconciles `-`/`_` so
  `dscr-core` finds `dscr_core/` -- the same reconciliation `from_pack_id` already did internally,
  now available to a caller that only wants the directory.

  Env var names are the caller's: `resolve_packs_root(*env_names)` takes them and `env()` tries
  them in order, so the SDK supplies the mechanism and the consumer supplies the vocabulary. That
  is what lets a domain collapse its own path helper to the few lines that name its knobs.

  It is also deliberately where a `PackVersionStore` lookup lands. With `published_registries`
  above serving assistant packs from the store, this is the seam for the *domain* pack half --
  which is the question the store cannot answer yet.

  The review round on it found the day's own lesson missed one function further: `resolve_pack_root`
  joined an unvalidated `pack_id`, so `""` resolved to `packs_root` itself and `"../secret"` to a
  directory beside it, both returned as a pack root. Measured. `path_safety.bare_name` -- added
  earlier in this same release for this exact join -- guards it now.

  Three more from that round. `env` plus a truthiness test is the shape `env_text` was added to
  own, and the docstring cited `env`'s contract while the code followed `env_text`'s, since a blank
  falls through to discovery. A *file* named `config` satisfied the directory marker; the first fix
  for that hardcoded the name while its own docstring described a trailing-slash convention, so
  `DEFAULT_MARKERS` is `("pyproject.toml", "config/")` and the slash now means what it says. And
  `plato/wiring_local.py` was the last live counting site in this repo -- `parents[1]` plus a lone
  `pyproject.toml` check, both of the failures this module exists to remove -- so it uses
  `discover_root`, whose `None` composes with the cwd fallback it already had.

  Then the round after that caught the migration itself, and it was the worst find of the set: the
  default markers require a `config/` directory and **this repo has none**, so `discover_root`
  returned `None` in `wiring_local` and every path derived from `_REPO` -- the sqlite file, the
  cache, the sibling-profile default, and `cwd=` for the alembic subprocess -- silently became
  working-directory-relative. Measured: `_find_root()` from `/tmp` returned `/private/tmp`, so
  `python -m plato` outside the repo root would migrate one database and create an empty other,
  the exact failure `_anchored` was written against.

  The error was applying markers that describe a *consumer's* layout to this repo. The call site
  passes `markers=("pyproject.toml",)` now and says why. Its test passed only because pytest runs
  from the repo root; it `chdir`s first now, and fails against the unfixed code with the tmp path
  where the checkout should be.

  That round also found `from_pack_id` carrying the identical unvalidated join -- and unlike
  `resolve_pack_root` it has a shipped caller in `Pack.from_pack_id`, so guarding the new function
  and leaving the old one open was the one-of-a-family miss again. Both guard now. The raise
  contract is stated rather than half-promised: `ValueError` for a malformed id, which is the
  caller's mistake, and `PackRootNotFoundError` for a well-formed id with no directory, which is
  the packs directory's state. And a *directory* named `pyproject.toml` satisfied the file marker,
  the file-vs-directory confusion fixed in one direction only when the trailing `/` was added.

  The round after found members three and four, and the worst of the set: `modes/prompt_loader`
  joins `pack_id` in two places and then `read_text`s the result, so an escaped path returns an
  arbitrary file's contents *as a prompt* -- instruction the model follows, rather than a wrong
  directory. The two that return a path were guarded first and the two that read were not. Ten
  parametrized cases do not raise against the unguarded code.

  Scoped honestly: in this repo a mode's `pack_id` is manifest-derived, so this is a boundary
  rather than a fix for a live route, and the docstring says that instead of implying a
  reachable exploit. `""` is excluded from those two, deliberately -- `pack_id` is optional there
  and both gate on truthiness, so an empty id means "no pack tuning" and never reaches the join.

  Three of my own claims corrected with them. The docstring named `Pack.from_pack_id`, which does
  not exist -- it is `Pack.from_manifest` -- and called it a shipped caller, an out-of-repo claim
  stated as in-repo fact. The two lists of bad ids had already drifted into a subset, dropping the
  two cases with distinct mechanisms, so there is one shared list now. And `markers=`
  `("pyproject.toml",)` in `wiring_local` does reinstate what `DEFAULT_MARKERS` warns against; it
  is kept, because this repo has no `config/` for the default set to match and the image's
  `WORKDIR /app` carries no `pyproject.toml`, but the docstring says so rather than claiming a
  checkout is required.

  And a *fifth*: `evaluation/harness/config.py` joins `pack_id` into `get_output_path`, which
  unlike every read above is a **write** target -- `pack_id="../.."` puts eval output two
  directories above `output_dir`. Guarded with a pydantic field validator rather than at the join,
  because construction is the single place an id enters and a path can be built from it more than
  once. The comment claiming the family was covered was, once again, a census that was false when
  written; it now names the shared rule and says that where-else is a question for a grep.

  The `Raises:` gap came with it, and it is the same one fixed in `roots.py` the round before and
  not carried across: both prompt loaders documented `FileNotFoundError` alone while the new guard
  raises `ValueError`, and `modes/base.py` quotes that block as *the* contract when it justifies
  propagating. Both state it now. The prompt cases also moved to `test_modes_framework`, beside
  the other `resolve_mode_prompt` tests, importing the shared id list rather than restating it.

  Left as noted: the `-`/`_` candidate spelling is duplicated between here and `manifest_loader`.
  Folding two callers into a shared helper in the same pass that fixed a defect in one of them is
  how the next round finds a third thing.

- **A published pack now serves a tenant, which is what the pack table was for.** The store
  landed without the half that uses it: the `pack_version` row, `PackVersionStore` and the
  migration all shipped, while `plato/packs/loader.py` still read a directory -- so pack bytes
  still came from the container image and the plan's acceptance criterion (*a pack published to a
  running Plato serves a new tenant with no deploy and no code change*) was exactly as unproven as
  it had been before the table existed.

  `published_registries(store)` closes it: `list_packs()`, `materialize()` per record, then the
  `tenant_registries()` that already existed. Materialize-then-load, which is the plan's own
  recommendation and what the loader's docstring anticipated ("adopting a durable store later is a
  new caller rather than a change here") -- a second mapping-based implementation of what a pack
  means is the thing worth not having twice. No tenant argument, because the store is tenant-scoped
  at construction.

  **Writing the test found the store and the runtime disagreeing about what a pack is.**
  `materialize` located the pack root by `pack_manifest.yaml`, the domain-pack name
  `PackManifestLoader` reads, while Plato's loader reads `manifest.yaml` plus `profile/`. So an
  assistant-shaped pack *published without complaint and then failed at materialize* -- the worst
  moment to learn it. The root is recognised by either name now, root before nested for both. This
  is the three-representations finding in §3 of the plan arriving as a defect rather than as prose.

  The test publishes the shipped `manifest_binding` fixture, which is the pack
  `test_assistant_manifest_binding` binds a live agent from, so the published bytes are provably
  the shape the runtime accepts rather than one invented to satisfy the store. It names no
  filesystem pack directory anywhere. A second test covers the tenant that has published nothing,
  which is a state to report rather than an error -- `PackNotFound` answers a different question.

  Still open from that plan: the publish gate (step 3), which is where this belongs long-term --
  `publish` will still accept an archive `materialize` could reject.

  The review round on it found three defects in the new code, two of which would have met the first
  real pack. `published_registries` fed *every* published row to `load_pack`, so a single domain
  pack -- the shape the rest of that test file publishes, and the shape the new `_MANIFEST_NAMES`
  comment says the store carries on purpose -- aborted the whole composition and made the tenant
  unservable. And a manifest-only row, legal by construction with `content_ref` `None`, raised
  `PackNotFound` and took every other pack down with it, which the sibling test asserts is not how
  an absence is reported. Both are skipped now, on `assistant_id`: required on `AssistantManifest`,
  absent from a domain manifest, so the row settles the question without materializing anything.

  The third was the freeze assertion in the new test, vacuous: `SkillRegistry` has no `values()`,
  so `next(iter(skills.values()))` raised `AttributeError`, `pytest.raises(Exception)` swallowed
  it, and `register` was never reached. It registers for real now and expects
  `RegistryFrozenError`.

  One claim of mine corrected with it: materialize-then-load was justified as avoiding "a
  mapping-based second implementation of what a pack means", but `MappingPackSource` exists and
  `load_pack` already accepts it, so that route reuses the same rules. The real reason is
  `materialize`'s digest-keyed cache, which is what the docstring says now.

  The round after that found the *fix* had made a fourth: once domain packs are skipped by
  `assistant_id`, the only row the `content_ref is None` branch can reach is an assistant pack
  whose `profile/` never got published -- a publish-time mistake -- and it was skipped at
  `logger.debug`. So a tenant served no assistant with nothing saying why. My justification for
  skipping it, "legal by construction", described exactly the population the line above had already
  handled. It warns and names the pack now, and still composes the rest: raising would let one
  broken row make the tenant unservable, which is the defect it was introduced to fix.

  The test for it never reached that branch either -- it published the domain-pack fixture, which
  the `assistant_id` check skips first, so it passed with the branch deleted. It publishes an
  assistant manifest with no archive now and asserts the warning. The first version of *that*
  assertion used `r.message % r.args`, which raises `TypeError` on a record whose args do not match
  its template; `getMessage()` is what formats a log record.

- **Two PR review items recorded as TODOs rather than changed.** `TODO(if-match-post)`: `POST` in
  the `If-Match` method set is wrong for a POST that *creates* -- there is no ETag to send, so it
  would take a 428 it cannot satisfy -- but `require_if_match` is exported and called only from
  tests, so there is no route to fix against and removing POST now would guess which way the first
  one goes. `TODO(migration-concurrent-index)`: one transaction per migration run is what makes a
  failure roll back instead of half-applying, and the cost is that `CREATE INDEX CONCURRENTLY` can
  never appear in a migration. Nothing needs one; the TODO names both wrapping sites (the offline
  branch as well as the online one the review pointed at) and says to scope any future change to
  the migration that needs it rather than dropping the transaction for the whole chain.

- **The last review round's five low findings, folded in here.** `reason` is on the package surface
  now, with the `__all__` snapshot updated deliberately -- which is what that gate asks for, and
  two earlier refusals to do it rested on the weaker argument that nothing in-repo needed the name.
  `verify`'s two `TokenError` messages, and the two boot notes in `plato/__main__` and
  `wiring_default`, go through `reason` like the rest. The queue envelope binds its scrubbed detail
  once, as its three siblings do, and now has a test -- it was the one of the four with none, which
  is what would have let a later edit drop the scrub silently; it fails with `redact_secrets`
  removed. And the docstring no longer claims `reason` does "the same two things" as
  `_safe_detail`, which caps at 1000 unconditionally while `reason` truncates only when asked.

  Three claims from that pass were wrong and the round after caught each. The new queue test said
  it covered "the one of the four envelopes with no test" -- but `inbound.py`'s existing test
  asserted only `status` and `error.type`, so it passed with the scrub removed; two assertions in
  that test close it, and all four envelopes are now genuinely covered. "The rest put the message
  in a trace note or a refusal" was false of `server/console_api.py`, which puts an uncapped
  `reason(exc)` straight into an HTTP body, contradicting the paragraph three lines above it; it
  caps at 200 now like the other two body-bound callers, and the docstring says to pass `limit` for
  anything body-bound. And `TODO(migration-concurrent-index)`'s "one transaction for the whole run"
  is Postgres-only: with `transactional_ddl` False it degrades to a `nullcontext` and alembic
  commits per revision, which is the sqlite dev path and what `_take_migration_lock`'s docstring
  already said.

  Also from that round: the `print` beside the scrubbed wiring note was still raw, so the same
  exception reached stderr unredacted. Both sinks take one `detail` now, as the sibling handler
  does.

- **The pack store's blob key was not tenant-safe, and the test could not see it.** Found by the
  review round on the commit above. The key was `packs/{pack_id}/{version}.zip` -- no tenant, no
  digest -- and `BlobStore.put` is a plain write, so a second tenant publishing its own edited
  `dscr-core 0.1.0` overwrote the first tenant's bytes. The first tenant's row is immutable and
  still pointed there, so it served the *other* tenant's pack under its own now-wrong digest.
  Reproduced end to end: `ACME GOT OTHER'S PACK: True`.

  The key is content-addressed now (`packs/sha256/<digest>.zip`, the same shape
  `BlobStore.offload(dedup=True)` already uses), which also makes copy-on-adopt's "blob shared by
  digest" true rather than a collision that happens to be harmless when the bytes match. And
  `materialize` re-hashes what it fetched: nothing on the read path checked, which is what made the
  substitution silent instead of loud.

  Why the test missed it: every archive in the file was byte-identical, so the cross-tenant test
  exercised the colliding key and passed. The fixture takes a content marker now, and both new
  tests were checked against the old code. That test also shares the cache root, which is what
  production has -- the one construction site passes no `cache_root`, so every tenant in a process
  takes the same default and `_cache_dir` keys on digest alone.

  The review round on the fix found the key rule now existed twice: spelled here and again inside
  `BlobStore.offload(dedup=True)`, reached by different hash functions, so the same archive routed
  through `offload` would have landed under a second key -- which is what dedup exists to prevent.
  `BlobStore.content_key` owns the derivation now and both callers ask for it, since the keyspace
  is the blob store's.

  The next round caught that the shared helper still re-implemented the *hash* with a bare
  `hashlib.sha256` while `jazzx_sdk/digest.py` exists as "one implementation, importable from any
  layer" -- so `publish` derived the row's digest from `content_digest` and the key from
  `content_key`, two functions on adjacent lines agreeing only because the argument is `bytes`. It
  uses `content_digest` now. No test pins it: for `bytes` the two produce identical output, so any
  assertion passes against either, and the reason it is untestable is recorded where the choice is.
  A tautological test written for it was deleted rather than kept.

  The helper's docstring no longer claims to prevent the double-write either -- it gives one hash
  rule and one key shape, and identical content under two prefixes is still two blobs.

- **A blob key is a name, not a path.** `BlobStore.put` does `self._local_dir / key`, which treats
  an absolute key as a path (`/etc/x` discards the blob directory entirely) and lets a `..` climb
  out. The guard went on the key *builder* first, which was the wrong half: `offload(key=...)` and
  every direct `put` never touch the builder, and a review round pointed at the repo's own
  precedent one file over -- `pack.store_db._unpack` guards the write, not the caller.

  Refused by shape at `put` now, which covers a bad prefix, a bad suffix and a caller-supplied key
  in one rule. By shape rather than by resolving and comparing, because a *contained* `..` is safe
  to write and still breaks the round trip: `put` writes the resolved path while the pointer it
  returns carries the key unresolved, so `get` looked elsewhere and returned `None` for something
  just written. Found by a test asserting that shape was allowed -- no caller needs a `..`, since
  every prefix in the repo is a literal.

  The next round found the guard was still in the wrong place, and this one was a live
  arbitrary-file read: `get` and `delete` build `local_dir / key` from a **caller-supplied**
  pointer, so guarding `put` alone left the *more* exposed pair open. Measured:
  `get("blob://../secret.txt")` returned that file's bytes and `delete("blob://../victim.txt")`
  unlinked it. Reachable from `DocumentAgent.process_blob` and from any stored `__blob__` ref, so
  through a library consumer rather than an in-repo route.

  Every local read, write and delete goes through one `_local_path` now, which is the path
  construction itself and so cannot be bypassed. My own comment had claimed `put` was "the only
  place every key passes", which was the error: two other methods build the same path. The claim
  in `content_key`'s docstring is also scoped to the local backend now -- an Azure blob name has no
  traversal semantics, and the flat promise held for one of the two.

- **The same traversal was in `fabric.docs`, and that one reads a document.** The round after
  found `DocStore` doing the identical unchecked join in three places (`_put_local`, `_get_local`,
  `_delete_local`): `get("../secret.txt")` returned that file's bytes *as a document*, measured
  under `retrieval_mode: local` and reachable under `cached` whenever Knowledge Hub is down. The
  name is not ours to trust -- it arrives as a `document_id` from an agent tool call, or a
  caller-supplied `doc_id` from `tools.documents.local_cache`.

  Same shape, same layer, one builder. This is the third time in the session a guard landed on one
  member of a family, and the second time the sibling was the more exposed one; the review found it
  by looking for the sibling rather than by being told.

  Then the round after that found a **fourth** local read: `_get_test_fixture` joins
  `golden_cases_dir`, not `self._local_dir`, so guarding the three sites that use the latter left
  it serving exactly the input they had started refusing (`{"content": ..., "source":
  "test_fixture"}`), sidecar included. The guard takes a root now. Fixing three of four while
  editing the function is the same miss one level finer. (An earlier version of this entry, and the
  comment it came from, called these "the four branches of `get()`" -- the count was right and the
  thing counted was not; `get()`'s four modes are STRICT/CACHED/LOCAL/TEST and STRICT joins no
  path.)

  The guard also sat *inside* each `try`, so its `ValueError` was rewrapped as the
  `KnowledgeFabricError` a missing document raises -- collapsing the very distinction it was added
  to preserve, which `BlobStore` keeps by construction. Hoisted above the handler in all four.

  Which changed the *documented* contract, and the next round caught it: every `Raises:` block on
  `put`/`get`/`delete` promised `KnowledgeFabricError` alone, and that was true only while the
  handler was doing the rewrapping. A consumer catching the documented type now misses the refusal.
  `ValueError` is documented on all five blocks rather than rewrapped back into the base, because
  the split is the point and `BlobStore` raises the same type for the same reason. In-repo callers
  are unaffected either way (`agents/interactive/reads.py` catches bare `Exception`;
  `tools/documents/local_cache.py` catches nothing, so the type change propagates identically).

  The line as first written was itself an overclaim, caught the round after: only the local path
  validates, so `put(name="", location="hub")` -- the documented default location -- returns a hub
  document id for an unnamed document, and a STRICT `get` raises `KnowledgeFabricError`. Scoped to
  "if the name reaches the local filesystem", one phrasing true at all five sites rather than five
  bespoke conditions.

  Same round: the sidecar path was routed through the guard in the TEST branch only, while the
  other three built it raw. All four derive from a name the guard already refused above, so the
  consistent shape is the smaller one -- the redundant call is gone rather than replicated three
  times, since appending a suffix cannot introduce a `..` or an absolute prefix. And the guard is
  named `_local_path` again, pairing with the `BlobStore` sibling its own docstring cites.

  Two claims corrected: the exposure is a library consumer calling `docs.get` directly, *not* the
  two call sites the comment named -- `agents.interactive.reads` checks the id against the listing
  first and `tools.documents.local_cache` reads its id from an on-disk manifest. And an assertion
  claiming to prove "the file was read out" could not: reading a file does not change it, so the
  `raises` was carrying that case alone.

  Two claims of mine narrowed to what the code does: "either order is correct" for a same-tick tie
  is not true when `get(pack_id)` is documented as the latest version (`TODO(publish-tick-tie)`),
  and the digest re-hash guards the *fetch* path only -- the cache short-circuit returns without
  hashing, and the default cache root outlives the process.

  Also from that round: `seq` was `autoincrement=True` on a non-primary-key column, which
  SQLAlchemy ignores -- every row got `0`, so the tiebreak four comments credited did nothing.
  Dropped rather than made real: the key already makes two rows for one version impossible, so the
  only tie would be two different versions published in the same microsecond, where either order is
  correct. And the zip-slip rationale was wrong in two places -- CPython sanitizes member paths
  (measured: `../escaped.yaml` lands at `root/escaped.yaml`; the escaping shape is `tarfile`'s), so
  the guard is fail-loud defence rather than the boundary the comment claimed, and one test
  assertion checked a path the code could never write.


- **A published pack has somewhere to live: `pack_version`, stage 1 of the pack store.**
  `plan_pack_store.md` §10 step 2. A pack lived only on a filesystem, which makes it something
  baked into an image and leaves *which pack version produced this decision* unanswerable once the
  working tree has moved on.

  `jazzx_sdk/pack/store.py` is the ABC and the record; `store_db.py` is the durable implementation
  -- both in the SDK, beside the loader they feed, which is where `AssistantManifestStore` and
  `DbAssistantManifestStore` already put that split (the plan said "protocol in the SDK,
  implementation in Plato"; the code says otherwise and the code wins). Plato owns the
  registration, the schema assignment and migration `0003_pack_version`.

  The design points that cost the most thought, each inherited rather than invented: a published
  `(pack_id, version)` is immutable, so certification and drafts are deliberately absent -- both
  are cheap to add against an immutable row and expensive to retrofit against a mutable one.
  `tenant_id` is *in* the primary key, because `verify_tables` requires a key and a plain column is
  a filter a query can forget. The manifest is stored inline and the asset tree as a blob pointer,
  for the reason a package registry does not shred a wheel. And `materialize` keys its unpack cache
  on the content digest, which is the same skip `fabric.docs.materialize` makes for a document
  whose hash has not changed.

  Ten tests, driving a real sqlite `DbStore` and a local `BlobStore` rather than stubs, and the
  materialize test loads the unpacked tree through `PackManifestLoader` -- which is the acceptance
  criterion the plan names. Two findings from writing them: `db.session()` does not commit on exit,
  so the first `publish` wrote nothing and `get` read nothing; and a fixture whose policy YAML was
  not a *policy document* proved nothing about assets arriving, because `policy_files()` correctly
  filters the folder through `is_policy_document`.

  `test_the_expected_revision_comes_from_the_migration_tree` asserted the literal `"0002_setting"`
  under a docstring arguing against exactly that -- so it failed the moment a third migration
  landed, over a stale number nobody had updated. It computes the head from the chain now (the one
  revision no other file names as its `down_revision`) and additionally catches a two-headed chain.

  D1 is recorded in the plan: **both, staged.** A published version stays immutable; "the pack's own
  app crafts and updates it" is a *draft*, which gets its own mutable row in stage 2 and becomes a
  `pack_version` at publish -- deliberately outside the version table, which is where the plan put
  it. D2 (copy-on-adopt), D3 (materialize) and D7 (no `plato_` prefix) taken as recommended.



- **`GET {prefix}/database` lists every table Plato owns, not the subset the process happened to
  construct.** `db.metadata` fills as a side effect of `Db*Store.__init__`, so the listing was
  whatever the wiring built -- three of seven under `wiring_local`, which reads as "Plato has three
  tables" to an operator looking at the dashboard. `plato/models.py:register_all` is the module
  that exists to make the set enumerable rather than emergent, so `describe_database` calls it:
  registration is idempotent, constructing a store opens no connection, and doing it in the
  function rather than the route means a direct caller of the exported function gets the same
  answer.

  The route's own docstring argued metadata-over-reflection in one direction only -- a table
  missing from the database shows as an error against a row the operator can see. The inverse, a
  table that exists but whose store was never constructed, vanished silently.

  The test uses a real `DbStore`: `DbTurnRunStore` is the one of the six needing more than
  `register_metadata` (it calls `db.repository`), so against a thin stub it raises after three
  tables are already registered and the broad `except` reports that shortened list as success --
  which is how the first version of this test agreed with the bug. `TODO(partial-registration-
  marker)` records that a partial registration still reports as an ordinary success with no
  `reason`; every shipped caller passes the `DatabaseHandle`, so only a duck-typed store reaches
  it.

- **`swap_database` created no tables.** The review round on the change above found the same
  emergent-metadata bug one function over, and this one loses data rather than under-reporting:
  `create_all` iterates *registered* metadata and `_db` returns a bare `DbStore`, so a swap
  created nothing, logged success, and left every later session, manifest or settings query
  failing `no such table`. Measured: zero metadata, zero tables. Reachable through
  `POST /v1/config` changing `PLATO_SQLITE_PATH` or `PLATO_DB_BACKEND` in a relaxed posture --
  strict refuses those writes, so no staging or production path.

  `register_all(replacement)` before `create_all()`, the same line as the route fix. Three swap
  tests existed and none asserted that a table was present, which is why it survived; the new one
  does.

  `TODO(swap-schema-placement)` records what the fix inherits: the models carry no `schema=` so
  they stay portable to sqlite, so a non-sqlite swap creates all seven unqualified rather than in
  the `plato_*` schemas the migration assigns, and nothing here sets a `search_path`. The replica
  works against them, but a later alembic upgrade on that database builds a second copy. Turning
  the no-op into real DDL is what made that a live consequence rather than a latent one.

  Two corrections that came out of the same rounds. `swap_database`'s docstring said the retired
  store is "kept referenced rather than disposed", and `del previous` does the opposite -- it drops
  the last handle the function holds; what is true is that it is never *disposed*, and an in-flight
  session's own reference is what keeps it alive. And the retired-store disposal in the tests
  landed on one of the two same-shaped ones; both dispose both stores now, before their assert, so
  a failing assert still disposes -- which is all four `swap_database` tests (the other two already
  did, or swap into a failure with no second store).



- **An empty exception message no longer erases the reason, anywhere in Plato.** The empty-`str(exc)`
  fix landed as a private `_reason` in `plato/oidc.py`, and the review round after it found four
  *mounted* sites carrying the identical format string with the identical hole -- `plato/info_api.py`
  (both the schema and database blocks), `plato/database_api.py`, `plato/schema_version.py` and two
  in `plato/__main__.py`. Unlike `oidc.py`, which nothing imports outside its tests,
  `create_info_router` is mounted from both `plato/app.py` and `plato/__main__.py`, so `/info`
  answered a database read timeout with `cannot reach the database: TimeoutError: ` in every shipped
  server config. Measured against the unfixed code, which is what the new test asserts.

  `jazzx_sdk.failures.reason` owns it now, with a `limit` for the call sites that bound their
  output. It went into `plato/reasons.py` first, which the next round showed was the wrong layer:
  `jazzx_sdk/server/console_api.py` renders the identical string into a *response* field and
  cannot import `plato` -- nothing in the SDK does, and the dependency only runs the other way.
  `failures.py` already existed for exactly this ("turn an opaque exception into a message a caller
  can act on") and is top-level by design, so the module was a new file for one round and is now
  four lines in the one that was already there.

  The family's disposition in full: eight message sites converted, plus `console_api`'s; the four
  logger calls in `settings_store` and `wiring_default` converted too, since they hand-rolled
  precisely `reason(exc, limit=120)`; the five SDK sites the next round named
  (`pipelines/vocabulary_build`, `pipelines/document_ingest`, `pipelines/chat`, `conductor/engine`
  twice) converted as well, which leaves `grep` finding no site with the trailing-colon shape
  anywhere in `jazzx_sdk/` or `plato/`; and two sites that format the type *without* the message
  left alone, having never had the hole.

  `reason` also redacts now. It did not, while `_safe_detail` four lines below it and the Knowledge
  Hub client's formatter both do -- and `reason`'s output reaches HTTP response bodies through
  `describe_database` and `registry_inventory`. Wrapping it in `redact_secrets` was not enough on
  its own: the named trigger is a SQLAlchemy `ArgumentError` quoting the DSN it could not parse,
  whose password sits in the URL's userinfo, and neither `redact_secrets` nor
  `net_safety.redact_urls` (http/https only) covered `postgresql://u:pw@h`. That pattern is in
  `redact_secrets` now, where every existing caller gets it too, and it runs before the truncation
  rather than after -- cutting a credential in half leaves its front in place with no pattern left
  to match.

  That pattern then leaked three ways, all measured by the next round: requiring a user before the
  `:` missed `redis://:pw@h`, the documented Redis form; excluding `/` missed a pasted password
  containing one; and stopping at the *first* `@` left the tail of `u:p@ss@h` in place. Three
  attempts to say what a password may contain, so it says nothing about that now and bounds on the
  **last** `@` of the authority instead. The trade is one over-redaction -- an authority with a port
  whose path holds an `@` (`https://h:8443/a@b`) scrubs the `8443/a` -- which is pinned by a test
  as the accepted behaviour rather than left to be rediscovered. This matters past `reason`:
  `redact_secrets` is the only scrub on the `/logs` ring buffer, on `cost_tracker`'s serialized
  payloads and on `channels.notify`'s webhook bodies.

  My justification for the pattern was also false: SQLAlchemy 2.0.44 raises `Could not parse
  SQLAlchemy URL from given URL string` with no DSN in it -- the quoted-DSN wording is 1.4's. The
  pattern is still right; the *because* was not measured, so it is gone rather than restated.

  `reason` collapses whitespace too, the second thing `_safe_detail` does twelve lines below. The
  four `limit=120` log sites fire on a *normal* first boot, where a driver error carries its SQL and
  a docs link across three lines and the truncation cut mid-URL.

  The step-error family closed at the same time: the review named five `default_step_error`
  implementations and there are six (`chat` was already converted; `investigation_loop` carries no
  message), and widening the grep past what it named turned up two more in
  `modes/operational/governor.py` that no round had flagged. All converted. One site is left
  deliberately: `clients/knowledge_hub_client.py` keeps its own formatter because it applies
  `redact_urls`, which strips a signed URL's query -- added for a measured leak where a redirect
  exposed the second hop's signature -- and `reason` does not. The round after made the better
  point that the dangling colon can go *while keeping* that scrub, which is what it does now.

- **`policy_extract`'s opt-in step-error handler could not construct.** Found by the review round
  on the pass above, because that pass edited this function's message line and not the rest of it.
  `RefusalClass.INSUFFICIENT_EVIDENCE` is not a member, and `refusal_class=`/`reason=` are not the
  model's fields (`reason_code`/`reason_class`/`message` are, the first two required). Measured:
  `AttributeError: type object 'RefusalClass' has no attribute 'INSUFFICIENT_EVIDENCE'`. The
  conductor calls `on_step_error` from inside its own `except`, so "degrade to a typed `Refusal`
  instead of crashing" crashed *over* the failure it was handling. It is the one of six
  `default_step_error` implementations with no test; the other five work. Fixed to the sibling
  shape and given that test.

- **The handler-error response envelopes went out unscrubbed.** They put bare `str(e)` into both
  `payload.data.error` and `error.message`, and an exception quotes what it was handed: an httpx
  failure on a Knowledge Hub blob fetch names the final hop with `sig=` intact (the leak
  `redact_urls` exists for), and a driver error carries `postgresql://user:pw@host`. That body is
  returned to the HTTP caller, and `/invoke` is served by every server-mode app.

  Fixed at `server/inbound.py` first, whose own comment says "mirror `/invoke`" -- and `/invoke`
  itself was not fixed in the same pass, which the next round caught as a high. Widening the grep
  past the two sites it named found the envelope family is **four**: `server/app.py`,
  `server/inbound.py`, `runtime/__init__.py` and `queue/processor.py`, all now scrubbed, plus two
  unredacted `logger.error` lines beside them.

  They scrub with `redact_secrets` rather than `reason`, which was the second correction: `reason`
  prefixes the exception type, `error.type` is already its own field in the envelope, and
  `tests/test_server.py` pins `error.message == "Something went wrong"` -- so the first version
  changed a caller-visible shape to add something the envelope already carried. That test failing
  is what surfaced it, after the review's own note on the shape change had been waved off as "no
  parser matches on it". A new test pins the goal instead of the mechanism: no credential in the
  body, message shape unchanged.

  Out of scope deliberately: roughly twenty-five further `{"error": str(e)}` sites under `tools/`,
  plus `fabric.py`, `condition_evaluator` and `gemini_provider`. Those are tool results read
  in-process or by a model, not HTTP bodies returned to a caller, and converting them is its own
  change with its own risk.

- **`policy_extract`'s handler returned a `Refusal` the run then discarded.** It was the only one
  of six `default_step_error` implementations not setting `state.halt`, and the engine breaks on
  nothing else while `finalize` carries no guard -- so a failed step ran on, `finalize` emitted a
  `PolicyExtraction`, and the run reported `complete` with the refusal buried inside it. That also
  left the recovery branch in `run_policy_extract` unreachable, and its own docstring's "a refusal
  halts the run" false. Halted now, with the `remediation` both `Refusal`-returning siblings pass.

  The test written for the construction fix one round earlier passed `None` for `state`, which is
  exactly why this was invisible in it. It builds a real `ConductorState` now, and the halt
  assertion fails against the unfixed handler.

  Three comments of mine were corrected in the same round, all the same failure: a *because* that
  was not measured. "Bounded by the last `@` rather than by what a password may contain" was still
  bounded by `?`, `#` and whitespace, so a raw `p#w` password passes (left deliberately -- both
  characters must be percent-encoded to survive a URL parser, and the encoded form redacts -- but
  now stated). And "told the operator nothing", in two places, was false: the exception type was
  always printed, so what the change buys is the colon plus redaction and one-lining, not the
  diagnosis. `limit` also applies before the emptiness check rather than
  after, so `limit=0` returns the type name instead of the trailing colon the function exists to
  remove.

  It is not re-exported from `jazzx_sdk` itself: the `__all__` snapshot gate in
  `tests/test_import_boundary.py` failed the addition, which was the right catch -- the export was
  added only to silence an `F401` on an import I had just written, and nothing imports it from the
  package root. `jazzx_sdk.failures.reason` is the path every caller uses.

- **A blob key and a document name are names, not paths.** Brought onto `dev` from the 2.5.1 work
  rather than left to arrive with it, because `dev` is what merges to `main` as 2.5.0 and these are
  a silent arbitrary local-file read and unlink. Both were measured independently by the review
  round on the pushed commit: `get("blob://../secret.txt")` returned the file's bytes,
  `delete("blob://../victim.txt")` returned `True` and unlinked it, `put(key="/tmp/.../x")` wrote
  outside the blob directory, and `DocStore(retrieval_mode="local").get("../secret.txt")` returned
  that file as a document -- the last also reachable under `cached` whenever Knowledge Hub is down,
  which is the fallback path rather than an exotic setting.

  Every local read, write and delete on both stores goes through one `_local_path` that refuses by
  shape, so there is no boundary left to forget. `DocStore` has four such branches, the TEST-mode
  fixture read included, since it joins `golden_cases_dir` rather than the cache directory. By
  shape rather than by resolving and comparing, because the name is echoed back in `file_path` and
  a contained `..` would make that disagree with where the bytes came from.

  `blob.content_key` came with the files. It is unused on `dev` -- it exists for the pack store,
  which stays on 2.5.1 -- and imports nothing from `pack`, so it carries no dependency; the
  alternative was hand-splitting a diff, which is how a security fix gets landed incompletely.
  Reverting the two source files fails ten tests, every one of them `DID NOT RAISE`.

  The review round on that fix then found the same miss one layer up: the guard went on the blob
  *key* and not on the blob *filename* beside it. `DocumentAgent.materialize_blob_to(pointer, dest,
  filename="../../escaped.txt")` wrote the bytes outside `dest` and returned that path as an
  ordinary success, and `process_blob` builds the identical `Path(tmp) / filename`. The name
  arrives with the pointer, from `DocumentIngestTurn.blob_pointers` -- the same caller-supplied
  source the new guard's own docstring cites as why `get` and `delete` were the exposed pair.

  Both go through one `_blob_filename` now, which refuses rather than coercing to
  `Path(filename).name`. Coercing is right in `tools.documents.local`, where the name comes from a
  `Content-Disposition` header nobody controls and the alternative is failing the download; here
  the caller chose the name, so a silent rename leaves it looking for a file that is not there.
  Refusing also matches the two guards this was found beside.

  Two mistakes on the way, both caught by the tests written for it: the first version coerced while
  its docstring said it refused, and `".."` passed the comparison on its own because pathlib does
  not resolve it -- `Path("..").name` is `".."`, so it equals its own `.name`. Both tests fail
  against the unfixed code, the second with a `PermissionError` on `/tmp/.../../../escaped.pdf`,
  which is the escape being attempted and stopped by the filesystem rather than by us.

  The round after found the third layer of the same family: `turn.collection_id` reaches
  `_scratch_dir` as a path component, so `"../../elsewhere"` placed the scratch folder outside the
  base and `process_dir` globbed it and wrote its artifacts there. Guarded in `_scratch_dir`
  itself, not at that one caller -- it is the only builder there, and every other part it receives
  is a literal or a `.stem`, so the rule costs them nothing and the next branch cannot forget it.

  Three test corrections from the same round, all of them the test being weaker than it read. The
  `rglob` assertion claimed to prove "nothing was written under `tmp_path`" while the escape lands
  in `tmp_path.parent`, outside anything it can see -- the same shape as the blob-store assertion
  corrected earlier in this release. A bare `pytest.raises(ValueError)` would have stayed green off
  the missing-pointer raise in the same method if a fixture stopped resolving the pointer, so it
  matches the message now. And `"."` had no case -- though the comment added with it inverted the
  two clauses, which the next round caught: `Path(".").name` is `""`, so the equality clause does
  catch `"."`, and it is `".."` that needs the explicit tuple because pathlib does not resolve it.

  That round also found the assertion in the *new* `collection_id` test could not observe its own
  escape -- it looked one directory too high, and the branch only builds a string while the fake
  agent writes nothing, so nothing is created either way. Removed rather than corrected: the
  `raises` is the whole test, and saying that is better than a check shaped like evidence.

  And "every other part is a literal or a `.stem`, so the rule costs them nothing" was not
  measured. The correction was not measured either: it claimed a file named `...zip` (stem `".."`)
  had unpacked into the base's *parent*, and the round after that showed the only stem call site
  passes `("unpacked", stem)`, so the path was `base/unpacked/..` -- which resolves to `base`.
  Nothing escaped. Both stems are refused now because a bare name is the rule, not because they
  got out.

  Three rounds on one sentence, and three rounds where the only findings were comment claims of
  mine being false. The archaeology is gone rather than rewritten a fourth time: a docstring says
  what the code enforces, and the history lives here, where being wrong is cheap and a narrative is
  the point. The same applies to the caller surveys corrected earlier in this entry -- a count of
  call sites is stale as soon as one is added.

- **The JWKS fetch could be pointed inside the network.** From the PR review round on the pushed
  commit. `OidcSettings` checked the URL's *scheme*, which says the fetch is encrypted, not where
  it goes -- so `jwks_uri=https://169.254.169.254/latest/meta-data` was fetched and its body parsed
  as a key set. The guard already existed one layer over: `net_safety.is_private_ip` names that
  exact address in its own docstring, and `plato/oidc.py` did not import `net_safety` at all.

  Through `net_safety.fetch_validated` now, which is also the loop that re-checks every redirect
  hop (a client following redirects itself is checked once and then sent wherever the first
  response points) and which offloads the resolver rather than blocking the loop this class went
  async to keep free. Against the pre-fix code the new test takes ten seconds, because the request
  is really attempted.

  `OidcSettings.allow_hosts` comes with it, and is not optional: the common Keycloak shape is
  in-cluster, which resolves private, so a bare private-address rule would refuse the primary
  deployment rather than block anything. Same contract as the Knowledge Hub client's blob
  allow-list -- it admits a stated host, it does not disable the guard. Loopback stays permitted
  because `_is_secure_url` already blessed `http://` there for a dev instance, and a guard that
  breaks local development is a worse bug than the one it fixes.

- **`gitpython` floor to 3.1.59.** Five advisories published 2026-09-09, one critical, all fixed in
  3.1.59; the push gate reported them against the default branch. It is a transitive dependency of
  the mlflow extra and already carried a direct floor for six earlier CVEs, so this is that floor
  moved. Locked at 3.1.62, and `gitpython` is the only package the relock moved.

- **One home for "is this name safe to join onto a directory".** The push review found two more
  members of the family the traversal guards were written for, and the reason both existed is that
  the rule had been hand-written four times.

  `materialize()` had no guard at all: it writes `out / name_fn(entity)`, and for
  `sync_collection` that name is the Knowledge Hub's stored document name -- remote, and
  user-supplied at upload. Reproduced end to end: `wrote outside out? True -> /tmp/.../evil.pdf`,
  two levels above the output directory. `process_dir` then globs `out`, never sees the file, and
  the run drops it silently as well.

  And `"."` passed both `_local_path` guards, because `PurePosixPath(".").parts` is `()` -- so it is
  neither empty, absolute, nor `..`-bearing -- while `Path("blobs") / "."` is `blobs`. Measured:
  `put(b"x", key=".")` wrote a *file* at the blob directory's own path and left every later write
  failing `FileExistsError` on it. `_blob_filename`'s docstring had claimed the family "answers a
  bad name the same way"; that was false for exactly this input, in the direction that matters.

  So `jazzx_sdk.path_safety` owns the two rules now -- `relative_name` (may nest, may not escape)
  and `bare_name` (one component) -- and all five sites call it: both `_local_path`s, `materialize`,
  `_blob_filename`, and `_scratch_dir`. Top-level and dependency-free because `fabric` cannot
  import `agents` and both need it, which is the same reason `digest` and `net_safety` sit there.
  `relative_name` for `materialize` was the wrong of the two, and the next round measured why:
  `out`'s consumer globs it non-recursively, so a nested name is written and never seen, and a
  document named `.japes/manifest.json` lands on the run manifest `process_dir` keeps there --
  `manifest now: b'%PDF evil'`, with `materialize` returning it as an ordinary success and the next
  run reading document bytes as its manifest. It is `bare_name` now, matching the two neighbouring
  guards that already used it for this shape. Permitting nesting to avoid refusing a name no caller
  needs traded a loud refusal for silent data loss.

  Two corrections in `path_safety` itself from that round. The `"."` member of the parts set did
  nothing in `relative_name` -- pathlib strips single dots, so `"a/./b"` is already `("a", "b")` and
  could never match it -- while the error text claimed to refuse a `"."` segment; the two cases are
  separate checks now, each saying what it enforces. And the shape check used `PurePosixPath` while
  the join uses `Path`, so on Windows `..\x` would pass a check that its own join then lets out;
  both use `PurePath`. Pre-existing in the inline guards, and worse once centralized as "the same
  rule for every join site".

  Two flaws in the test written to prove it, both the shapes these guidelines name: the entity
  fixture put `doc_id` at the top level where production reads it from inside `json_value`, and the
  `_KH` stub took `doc_ids` returning a dict where the real client takes `document_ids=` and
  returns a ZIP -- so the download failed, the write under test never ran, and the `raises` was
  passing for the wrong reason.

- **Boot notes are served, so they are scrubbed and bounded.** Brought onto `dev` for the same
  reason as the path guards: `/info` renders `boot_notes` under `degraded` and `/health` under
  `missing`, so a `PLATO_WIRING` import or a pack load failing with a driver error put
  `postgresql://user:password@host` into every response a degraded replica gave -- an
  unauthenticated probe surface. Both call sites go through `reason` now, and `record_boot_note`
  caps at `BOOT_NOTE_MAX_CHARS`; the cap is at the source rather than at the callers because there
  are several and a later one would have to remember.

  The first version of the test for it was wrong twice. Its redaction assertion composed the note
  by calling `reason(exc)` *in the test*, so it could not tell whether the shipped call site did --
  the only thing worth asserting; it drives `_registries` with a raising `pack_registries` now. And
  the cap assertion imported `BOOT_NOTE_MAX_CHARS`, so against the unfixed code it failed on
  `ImportError` rather than on behaviour, and would have passed by agreeing with whatever the
  constant said. It uses the literal, and the two now fail as `assert [2015] == [500]` and with the
  DSN present in the note.

  The review round then turned the argument back on the change: the *bound* went to the source
  because "a later caller would have to remember", while redaction stayed at each caller -- and
  forgetting to redact is the demonstrated failure, not the hypothetical one, since this fix was
  two call sites that interpolated a raw exception. So `record_boot_note` does
  `redact_secrets(note)[:BOOT_NOTE_MAX_CHARS]`: redaction before truncation for the reason `reason`
  gives, idempotent for callers already going through it, and a caller that forgets is covered
  rather than trusted. A test passes an unscrubbed DSN straight in.

  `TODO(bound-missing-config)` records the other producer of that served list: `missing_config`
  echoes the `PLATO_PACK_DIR` repr with neither treatment, and bounding in `resolve_degraded` would
  cover both. Left because that value is written by whoever deploys -- a long `/info` field, not a
  credential we introduced. And the constant's comment no longer claims room "for a driver message
  with its cause": the budget covers the prefix too, so the cause is what gets cut.

  The round after that caught a comment asserting commit history -- "two of these call sites passed
  a raw exception until the commit that added this" -- written in the same session as the note
  saying not to do that. Gone from the comment and the test docstring; the rule they state holds
  from the code beneath them.

- **`TODO(settings-store-env-leak)`** records a test-isolation bug found while reviewing the above
  and confirmed to predate it. `apply_to_environment` writes `os.environ` directly and the settings
  store tests call it, so what it sets outlives the test -- the autouse fixture's
  `monkeypatch.delenv` only restores what was there when the test started. Reproduces as
  `pytest tests/test_plato_settings_store.py tests/test_plato_info_api.py`
  (`assert None == 'sqlite'`), and is unreachable in the suite's own order: nothing randomizes it,
  and `info_api` sorts before `settings_store`. Which also means the `-p no:randomly` this session
  put on every full-suite run was a no-op -- that plugin is not installed.


- **A URL check ran on the event loop.** `net_safety.validate_url_safe` ends in
  `socket.getaddrinfo`, and `WebhookChannel.send` is an `async def` that called it inline -- so
  every webhook send stalled every other coroutine for as long as the resolver took. Offloaded via
  `call_maybe_async`, which `fetch_validated` and `plato/oidc` already do for the same call. The
  review named the function; the caller was found by grepping for it.

  Two findings from that round are rejected on measurement, not judgement. `InvalidIssuerError`
  was said to carry the presented issuer: on the installed PyJWT it is the fixed string
  `Invalid issuer`. The header-parse error was said to include decoded header bytes from the
  token: it is `Invalid header string: 'utf-8' codec can't decode byte 0x81 in position 15`, a
  codec diagnostic naming a byte value and an offset. Neither discloses token content.

  `TODO(jwks-discovery)` records the third: `/protocol/openid-connect/certs` is Keycloak's path
  rather than a standard one, so the default is wrong for Azure AD, Google and Auth0, and the
  portable answer is to read `jwks_uri` from `{issuer}/.well-known/openid-configuration`. An
  operator can already set it explicitly and nothing mounts `TokenVerifier`, so no deployment is
  wrong today; discovery is its own change, with a second fetch, its own cache and its own failure
  mode.

- **An OIDC issuer without an audience is refused at construction.** From PR #67 review. `verify()`
  passes `audience or None`, and PyJWT with `audience=None` and `verify_aud=True` inverts the check
  rather than tightening it: a token carrying `aud` is rejected while one omitting it is accepted.
  Verified against the installed PyJWT -- `InvalidAudienceError` for the compliant token, ACCEPTED
  for the one with no `aud`.

  So an operator who sets `issuer` and forgets `audience` gets either every request failing (with a
  compliant IdP) or silent acceptance of any token from that issuer -- which is exactly the
  cross-service reuse the `require_audience` note warns about. Neither outcome is visible from the
  failing request, so the configuration is refused where it is built. `require_audience=False` is
  the explicit opt-out, and an issuer-less settings object still means verification is off.

  No shipped wiring constructs `OidcSettings`; it is a seam consumers wire themselves, so this
  refuses a configuration none of our own paths can reach and protects the ones that do. Six tests
  that built `issuer` without an audience to exercise URL and `enabled` behaviour now carry the
  companion value.

  Three review rounds on that fix, each finding the previous one half-done, and the third supplied
  a smaller fix than any of mine. First the check accepted `"   "`, which reaches `jwt.decode` as
  an audience and fails `aud` matching on every real token -- the one place this module would have
  treated whitespace as a value, where it strips `sub` and both optional claims. Then stripping
  only for the blankness *test* left `" plato "` stored raw and reaching `jwt.decode` verbatim:
  the same failure moved from the blank value to the padded one. Then `audience` was stripped and
  `issuer`/`jwks_uri` were not, though padding fails identically on both --
  `urlsplit(" https://kc/realms/x ")` yields `scheme="https"` with the space left on the path, so
  a padded issuer clears the scheme check, then mismatches `iss` on every token and hands httpx a
  `jwks_uri` with a space in it.

  All three are stripped and stored in one loop now, which is fewer lines than the single-field
  version it replaces, and `or ""` makes a `None` from a caller building one field at a time mean
  absent rather than `AttributeError`. The fields are annotated `str | None` to match: that is
  what the constructor takes, and `__post_init__` normalizes each to a stripped `str`, so every
  read is a `str` regardless. `mypy strict = true` is set in `pyproject.toml` and nothing in CI
  runs it, so the annotation is documentation -- which is the reason for it to say what the tests
  guarantee rather than something narrower. `resolved_jwks_uri`'s attribute access defaults, since
  that was the one place widening the annotation cost anything.

  Six review rounds landed on this one commit, and the last three found only a claim in the
  previous round's comment -- "every read narrows or defaults" was not true of the `issuer` passed
  to `jwt.decode`. The comments state what they need to and no more now, which is what ends that
  pattern: a sweeping claim about a whole file invites a counter-example every round, where a
  local reason for a local line does not. `TODO(frozen-settings)` records the remaining reach: the
  dataclass is not frozen, so building a field at a time bypasses both checks, which is
  pre-existing for the scheme check and left because freezing breaks that construction style for
  a consumer.

## [2.5.0] - 2026-09-07

*Post-merge fixes from PR #67 review, on `dev` so they land on that PR.*

- **An unreachable issuer was a 500, not a 401.** `verify`'s docstring promises `TokenError` --
  *"so a caller cannot treat an unverified token as an anonymous one by forgetting a check"* -- and
  the key load sat outside the `try` that made the promise, so `httpx.ConnectError` propagated
  past every caller catching `TokenError`. Reproduced: `ESCAPED as ConnectError`. Wrapped, and a
  transport failure is a refusal like any other.

- **A down issuer was re-fetched on every verify.** `_fresh_enough` gates the 30-second cooldown on
  `_cache.fetched`, and a raising fetch never set it -- so the rate limit held only while the
  endpoint was *up*, which is the case it does not need to hold for. Measured: five verifies drove
  five fetches. A failed fetch now stamps the cache with an empty key set before re-raising, so the
  window applies to the failure too: the token fails either way, and now it fails without a network
  call. One fetch for five verifies.

  The review round on that fix found it was worse than the bug: stamping with an **empty** key set
  meant one blip during a forced refetch rejected every valid token for the whole cooldown, even
  after the issuer recovered. Measured -- a `k1` token that verified before the blip failed
  `unknown key 'k1'` immediately after it, issuer back up. The keys are kept now and only the clock
  is stamped: a cached key does not stop being valid because a later fetch failed.

  Same round: the stamp covered the fetch only, so a fetch that *returned* a malformed document
  (`{"keys": None}`, or a top-level list -- both shapes an intercepting proxy serves with a 200)
  raised past it and kept the unbounded re-fetch open on exactly the path the stamp exists to
  close. The whole parse is inside the guard now. And the test asserting the transport path passed
  `_verifier`'s first positional argument, which is the JWKS *document*, not a fetcher -- so it was
  green on `'function' object has no attribute 'get'`, an unrelated failure the new wrap converts
  into the same `TokenError` it asserted. The cooldown test now also proves the window *expires*,
  which a cache stamped once and never retried would have satisfied.

  A third round on the same fix found two more. The cooldown returned the cache, so on a cold cache
  the *first* verify of an outage said "could not fetch signing keys" and every one after it said
  "token signed by unknown key" -- blaming the caller's token for the issuer being down, and
  telling an operator nothing about the issuer. Measured: `0 -> could not fetch`, then
  `1 -> unknown key`, `2 -> unknown key`. The cache remembers why the attempt failed and re-raises
  it while the window holds, but only when it has nothing usable: keys from before the failure
  still answer. And `entry.get("kid")` sat *outside* the guard whose comment has always said "one
  unusable key must not void the whole set", so a non-mapping entry -- or `keys` served as an
  object, which iterates to strings -- discarded every key parsed before it.

  Both survived the previous round because the three rate-limit tests asserted `raises(TokenError)`
  without a message. They assert the message now, which is what would have caught the inversion.

  A fourth round found the same lesson as the field directly above it: `error=str(exc)` tested for
  truthiness fails open, and a JWKS *timeout* is that case -- httpcore raises
  `ReadTimeout(TimeoutError())` and httpx maps it to `mapped_exc(str(exc))`, so `str()` is `""`.
  Measured: `could not fetch signing keys: `, then two verifies blaming the token. So the one
  failure an operator is most likely to be diagnosing was the one that reintroduced the misreport.
  `failed` is a separate bool now, for exactly the reason `fetched` is separate from `fetched_at`,
  and the reason names the exception type so an empty message still says `ReadTimeout`.

  `TODO(jwks-error-detail)` records what is left: the message carries the underlying exception, and
  `raise_for_status` puts the resolved JWKS URL in it, so a middleware rendering `TokenError` as a
  401 detail would hand an internal hostname to an unauthenticated caller. Nothing mounts
  `TokenVerifier` in a request path yet, and the middleware is the right place to decide what a 401
  body says.

  A fifth round: the handler's comment ended "Log-only here" and the handler had **no log call** --
  so with the same comment telling a future middleware not to echo the message, the diagnosis
  `error` was added to preserve reached neither the logs nor the response. The operator got
  nothing, which is the exact failure the field exists to prevent. It logs now, and a test asserts
  it does.

  A sixth round pointed at the *sibling* branch: a fetch that succeeded and produced nothing usable
  (`{"keys": []}` during a rotation gap) rebuilt the cache without the warm key set, so a valid
  token was rejected for the 30-second window even after the issuer recovered. Copying the failure
  branch's "keys are kept" fixed that and introduced something worse, which the seventh round
  measured: `_fresh_enough` never expires a non-empty cache on the unforced path, and each later
  empty fetch re-copied the keys forward, so a **withdrawn key kept verifying for the process
  lifetime**. A revocation that never takes effect, traded for a 30-second availability dip.

  The two branches are not the same case, which is the thing to keep: a fetch that *failed* leaves
  the issuer's key set unknown, so a cached key is still presumed good; a fetch that *succeeded* and
  said "no keys" is the issuer answering, and the cache must follow it. So the keys are dropped
  again -- what survives from the sixth round is the *message*, since the empty set is answered
  through `_or_last_error` and raises "the issuer published no usable signing keys" rather than
  letting the caller blame the token for an unknown kid. The test that asserted the retained-keys
  property is replaced by one asserting the withdrawal takes effect and stays in effect an hour
  later.

  Two of that round's notes are parked rather than fixed, both test-only with no shipped
  consequence: `TODO(malformed-jwks-clock)` records that the malformed-document test uses a
  constant clock, so it cannot tell a working cooldown from a cache stamped once (the same stamp is
  exercised with an advancing clock by the down-issuer test); and `verify`'s outer `except
  Exception` backstop stays uncovered, which the test that names it already says in place. A third
  note is rejected: it claimed the first verify on the empty-JWKS path misreports an unknown kid,
  but the caller's forced-refetch retry routes through `_or_last_error` and gets the realm message
  already -- a test written for it passed against the unfixed code, so it was deleted rather than
  kept.

  Three more from that round, each a divergence rather than a bug: the empty-`str(exc)` guard was
  inline in one handler while its sibling in `verify` re-emitted a raw `{exc}` -- so the same
  timeout would have produced the empty message one function up, fixed one round earlier. Both
  share a `_reason(exc)` helper now, and `verify`'s handler says it is a backstop rather than the
  conversion that does the work. A fetch that *succeeded* and produced no usable keys
  (`{"keys": []}` during a rotation gap, every entry `kid`-less) still reported "token signed by
  unknown key" for the window -- the same misdiagnosis for a misconfigured realm instead of a down
  one -- so it records its own condition. And the `error` field's comment read broader than the
  code, which raises only while the cache has nothing usable.



*Post-push round: the sliced adversarial review (see below) and PR #67's bot both ran against the
pushed commit, which the size-capped review had skipped.*

- **Review round 42: clean.** Both prior findings verified FIXED and no new findings -- the first
  round of the loop to report nothing at all.

  Where the loop got to, for the record: the last finding against shipped behaviour was round 34
  (`_strip_userinfo` over-redacting an object key). Rounds 35 to 41 were comment accuracy in the
  previous round's comment about one line, which ended when the constraint those comments kept
  mis-describing was enforced in code instead. The incremental range is what made those rounds
  cheap: 45 lines and about a minute each, against 5,500 lines and twenty minutes before.

  What an incremental pass cannot see is a defect in code a round did not touch. The full range
  last passed in round 32, and every change since has been reviewed by the chain, so the only gap
  is something round 32 itself missed -- which is why `pre_push_check` reviews
  `@{upstream}...HEAD` with no state to narrow it.

- **Review round 41: PASS, no defects.** Two notes, both tidying after the clamp: the raise
  quoted the raw `max_redirects` and so reported a bound the loop had not used
  (`Too many redirects (> -1)`), and the widened `max(0, budget) + 1` assertion had no param that
  reached it. The bound is a named local used by both the loop and the message, and `(1, -1,
  False)` exercises the raise path on a negative budget.

- **Review round 40: PASS, and the finding chain ends by enforcing what four rounds described.**
  The note was that "every caller supplies a positive constant" is a property of *in-repo* callers
  that nothing constrains: `fetch_validated` is exported and takes `max_redirects` as an ordinary
  keyword, so a consumer passing `-1` gets `range(0)`, skips the loop, and reaches a raise that
  reports a URL nothing validated.

  The budget is clamped at zero now, which is the only sensible reading of a negative one, and the
  caveat is deleted along with the gap it described. Rounds 35 through 40 each found an inaccuracy
  in the previous round's comment about this one line; the code enforcing it is what terminates
  that. The boundary test gained the negative case beside the 0, 5 and 6-hop ones.

- **Review round 39: PASS, no defects.** One note, and again a count in the comment written the
  round before: "the one caller" of `fetch_validated` where there are two. Both supply a positive
  constant, so the conclusion held, but the number did not. Rewritten as the property rather than
  the count -- a count is invalidated by the next caller and a property is not, which is the
  general form of the miscount that has now appeared four times on this branch
  (`SENSITIVE_KEY_NAMES`'s two consumers, the truthy-string list's five copies, `_body_excerpt`'s
  seven sites, `redact_url`'s five).

- **Review round 38: PASS, no defects.** One note: the enumeration said all three of
  `fetch_validated`'s raises run after `check(current)`, but the too-many-redirects one sits
  outside the loop and redacts `url` rather than `current` -- so a caller passing
  `max_redirects < 0` skips the loop body and prints a URL nothing validated. Split into the two
  inside-loop raises and that one, with its own grounds: the sole caller supplies
  `WEB_MAX_REDIRECTS`, so nothing reaches it.

  Three consecutive PASS rounds, each finding only an inaccuracy in the previous round's comment.
  That is the fixed point: no defect has been reported against shipped behaviour since round 34.

- **Review round 37: PASS, no defects.** One note, and it was the line numbers in the `TODO`
  written the round before going stale by exactly the six lines that `TODO` inserted above them.
  A line number in a comment goes stale by construction, so the five sites are named rather than
  numbered now -- `validate_url_safe`'s no-hostname raise, `fetch_validated`'s three raises, and
  `redact_urls`' lambda -- with the reason each one lands where it does attached to the name.

- **Review round 36: PASS, no defects.** Two FIXED, one CHECKED, one note -- and the note was a
  miscount in the `TODO` written the round before: "the four `redact_url` call sites" where there
  are five, and the fifth is the one the deferral's reasoning does not cover. `redact_urls`' lambda
  is fed hub-authored text, so "rejecting the URL anyway" does not apply there. The `TODO` now
  enumerates all five with where each lands, and the grounds for the fifth are its own: the matcher
  requires `https?://`, so only the literal empty-authority form reaches that branch through it,
  and no hub path emits it. Counted with `grep` before writing the number this time.

- **Review round 35: PASS, no defects.** Three of the previous round's four findings FIXED, and
  the two remaining notes were claims of mine rather than behaviour.

  `redact_urls`'s summary has now been wrong in both directions -- "query stripped" missed the
  userinfo and fragment, "reduced to scheme, host and path" missed that a query leaves
  `?<redacted>` behind and that the no-authority form is out of scope. It states all four facts
  and names both earlier errors.

  Two deferrals recorded with what was checked rather than fixed. `TODO(path-userinfo-last-at)`:
  on the no-authority branch the path keeps `rpartition`'s last-`@` rule, so
  `http:host/docs/report@2026.pdf` loses the host along with the password -- reachable only from
  `validate_url_safe`'s own "no hostname" message, which is rejecting that URL anyway, since the
  other three `redact_url` sites run after a hostname has been required. And the header-scan
  guard's docstring now separates what it does discover (modules) from what it does not (shapes):
  it matches a double-quoted name in a one-line `.get(`, which is what all nine sites use. Left
  deliberately after three rounds reported it, because the alternative is the multi-pattern scan
  this branch was already burned by twice, each round's guard defeated by a shape the last had not
  considered.

- **Review round 34.** Seven of the previous round's eight findings verified FIXED against the
  tree, one still open, and one defect in the fix itself.

  `_strip_userinfo` ran on the path unconditionally rather than only when there is no authority to
  hold userinfo, so any `@` in a legitimate object key took everything before it:
  `.../uploads/alice@corp.com/doc.pdf` became `.../<redacted>@corp.com/doc.pdf`, and an uploaded
  `report@2026.pdf` lost its name. Over-redacting is not the safe direction when what disappears
  is the identifier the log line exists to give an operator -- and it failed silently, leaving a
  plausible URL naming the wrong document. The path call is guarded now, with a test on the object
  key alongside the userinfo one.

  `redact_urls`'s summary still said "the query stripped"; delegating to `redact_url` means it
  strips userinfo and the fragment too.

- **Review round 33, the first incremental one: 146 lines instead of 5,521.** One slice, a
  `FIXED | STILL OPEN` verdict on each of the previous round's seven findings, then two defects in
  what changed. Both were in the userinfo redaction added the round before.

  `redact_urls` hand-rolled the same rule `redact_url` had just gained, with a different matcher,
  and the two disagreed: its character class excluded `/` but not `?`, so on a pathless URL it
  matched across the query separator and consumed the `?`, leaving the query substitution unable
  to fire -- `https://host?sig=abc@def` came out as `https://<redacted>@def`, losing the host and
  keeping the tail of the signature. It redacted *less* than before the change. It delegates to
  `redact_url` per match now, which states the rule once and closes the gap for free.

  `redact_url` stripped userinfo only from the authority, so a scheme with no `//` kept it in the
  path: `http:alice:s3cret@host/x` passed the password through verbatim into
  `validate_url_safe`'s own "no hostname" message. Both components are stripped, and the
  `https?://`-only boundary of `redact_urls` is now stated rather than implied.

  Three findings the previous round reported came back STILL OPEN because an edit batch had
  aborted on its first mismatch and I reported the later edits as applied: the cwd-relative
  catalogue read and the vacuous `"S" not in ...split("sig=")` assertion were never written. Both
  fixed, one file per script, each verified immediately. The parked external-host test also
  covers `/info/ui` now -- it listed two of the three pages it claimed to gather, so closing
  `TODO(protocol-relative)` would have re-enabled a narrower check than the one it replaced.

- **A killed review no longer skips the next round.** `save_state` recorded any run whose
  transcript was non-empty, and the five-line header makes it non-empty -- so an interrupted round
  left a baseline naming a transcript with no findings, and the next round diffed nothing against
  it and reported "nothing changed since the last review". Both the state write and the bootstrap
  now require a transcript that reached a `VERDICT:`. Found by reading the state after a kill, not
  by review.

- **Review round 32: PASS on both slices.** Five `CHECKED:` lines and one `PARKED:` line, which
  is the first round where the deferrals cost nothing to re-verify. Two `medium` notes taken, three
  `low` ones where the claim was mine and wrong.

  Parking three tests behind `TODO(protocol-relative)` took out assertions the deferral was not
  about: the served page's `<title>`, and `_markdown`'s HTML escaping, which nothing else in the
  suite covers -- so the guide renderer's escaping had zero coverage while the reason named only
  the external-URL scan. The parked assertion now lives in one test of its own, the other three
  keep everything else, and the dashboard test whose entire substance was that assertion is gone
  rather than left asserting nothing.

  `redact_url` stripped the query and kept userinfo, so `https://user:pass@host/x` survived a
  function whose test is named "never reaches a message whole" -- reachable from the
  agent-callable `read_from_url`, whose 204 and redirect-budget raises interpolate the URL into
  the buffer `plato/logs_api.py` serves. Both redactors strip it now.

  Three claims of mine corrected: `x-amz-signature` is redundant in `SIGNED_URL_PARAM_NAMES`
  (`-` is a non-word character, so `\b` falls before `signature` and that entry already covers
  all three forms -- measured), `TODO(is-private-ip-v4-only)`'s "left as the more restrictive
  behaviour" stopped being true once an `UnsafeUrlError` began latching v2 off for the store's
  lifetime, and a `"S" not in ...split("sig=")` assertion could only ever pass. One test also read
  `docs/DEPLOYMENT_ENV.md` relative to the cwd where eight sibling modules resolve from `__file__`.

- **The review remembers what it found.** A round now diffs `<the commit it last reviewed>..HEAD`
  rather than the whole branch, and carries the previous transcript's findings in with it: first a
  one-line `FIXED | STILL OPEN | REGRESSED` verdict on each, then new defects in what changed. The
  baseline bootstraps from the newest saved transcript when no state file exists, so the
  transcripts kept all along are what make the first narrow round possible. State records what a
  round *saw*, not what it approved, so a `BLOCK` still narrows the next one.

  The full range is not abandoned: `pre_push_check` reviews `@{upstream}...HEAD` with no state to
  narrow it, and `REVIEW_FULL=1` forces it here. That matters, because a defect in code a round
  did not touch cannot be found by an incremental pass.

- **Review round 31.** One `high`, one `medium`, and the `high` was the previous round's fix
  landing on one of two entry points while its test bypassed the other.

  `_probe_v2` re-raised `KnowledgeHubBlobUnreachableError` -- it subclasses `KnowledgeHubError`,
  not `Unsupported` -- and `_v2_probed` is assigned *after* the await, so on a fresh `DocStore`
  (which is what every caller constructs) the flag never got set: each document in turn took the
  probe lock, re-probed, spent its retries and was dropped. Reproduced: 0 of 3 documents, v1 never
  asked, 9 wasted v2 calls. Now 3 of 3 with one wasted call. The probe also stopped concluding
  "this hub answers v1 but not v2" from an unreachable host: v1 answering says nothing about the
  route, and latching it off for the store's lifetime is what a transient failure must not do.

  The test now drives both entry points. It had set `_v2_download`/`_v2_probed` directly to reach
  the post-probe branch, which is exactly how the probe branch stayed uncovered.

  Three more raw identity-header reads: `inbound.py`'s `X-Correlation-Key` (a public SDK seam, so
  a consumer's padding gave two keys for one trace) and `X-Tenant-Id` in both wirings, where a
  padded id is a second partition. And the guard meant to catch these hard-coded three module
  names, so it could not see any of them -- it discovers modules by scanning `jazzx_sdk/` and
  `plato/` now, against a list of headers that carry an identity or a partition key.
  `x-security-context` stays exempt: it is the encoded envelope, decoded rather than compared.
  Verified by reverting each of the three in turn -- the guard catches all three.

- **Review round 30.** Two defects.

  A blob host japes cannot *reach* is not the same as one it refuses by policy, and only the
  second downgraded the route. So on a deployment whose signed URLs name a host only the hub's own
  network resolves, every document spent its retries and `materialize` returned short with one
  warning apiece -- while v1, which streams bytes through the hub japes had just finished talking
  to, was never tried. `JAPES_KH_BLOB_HOSTS` did not rescue it either: naming the host skips the
  guard and the connection still fails.

  `KnowledgeHubBlobUnreachableError` is that case -- an unresolvable host or a refused connection
  -- and it reconciles the two readings this went back and forth on. It stays retryable, because a
  resolver blip is transient, and `fabric.docs` falls through to v1 for the same document rather
  than dropping it, without latching the route off, because the host may be reachable next call.

  The dashboard never un-hid a panel's empty sentence, and `load()` re-runs every ten seconds: a
  fresh replica said "Nothing logged at INFO or above" and then kept that line above fifty live
  records, and a recovered database kept "Not connected" above its table. The three blocks the
  shared frame replaced each had the omission separately; one line in the frame covers all of
  them. Verified by driving two refresh passes through the harness: the sentence shows on pass one
  and is gone on pass two, and it persists on both passes without the fix.

- **Review round 29.** One defect: `_body_excerpt`'s docstring claimed "every body interpolated
  in this module goes through here", and seven sites still passed `response.content` whole --
  `create_document_v2`, `delete_ontology`, `create_entity`, `create_entity_v2`, `update_entity`,
  `delete_entity`, `delete_policy`. The durable cost was the false claim: it reads as a rule
  already enforced, so the next body-interpolating log would skip the helper.

  All seven converted, so the claim is true. Enumerated first: `grep '\.content'` gives fourteen
  hits -- the four already converted, these seven, two return values, and a comment -- and the
  return values are deliberately untouched. Each now truncates at 200 bytes as well as stripping
  any query, which the untruncated ones did not.

  The test asserts the rule rather than the instances: any `.content` reaching a line that is not
  a `return` must go through the helper, so the eighth site fails the suite instead of the next
  review round.

- **Review round 28.** One defect, and the same mistake in a new shape: I widened a shared
  constant after checking one of its two consumers.

  `SENSITIVE_KEY_NAMES` is read by `_KEY_VALUE_RE`, which wraps each name in `\b`, and by
  `experiment_bridge.is_sensitive_key`, which tests `p in key_lower`. Adding `sig` for the
  signed-URL case was correct for the first and wrong for the second: `design_version`,
  `signal_threshold`, `assignee` and `sign_off` all began masking in the MLflow params the bridge
  publishes -- silently, as a masked value rather than an error. Verified against both consumers
  before and after.

  The three query-parameter names live in their own `SIGNED_URL_PARAM_NAMES` now, which only the
  anchored matcher reads, and `signature`/`x-amz-signature` do real work there rather than being
  redundant under substring matching. The test drives both consumers, because checking one is what
  produced the defect.

- **Review round 27.** One `medium`, three `low`. The three `CHECKED:` lines confirmed the
  deferrals from the previous round hold, which is the first round that cost nothing to re-verify.

  The `medium` was a `data:` guard that had overcorrected. Round 22 refused a comma with nothing
  after it, reasoning that an empty payload is the zero-byte document the missing-comma guard
  exists to prevent. RFC 2397's `<data>` production may be empty, `MockKnowledgeHubClient` emits
  exactly `data:<type>;base64,` for a document whose `content` is absent, and the HTTP branch of
  the same function returns a zero-length 200 body as the document -- so the guard turned an empty
  document into a retried, dropped one on the mock-app path. Only a missing comma is malformed now.

  Every response body this module interpolates goes through `_body_excerpt`, not just the two that
  read a URL out of it: the body is the JSON carrying the signed URL, so a hub returning it under
  a renamed key (`{"url": null, "signed_url": "...?sig=..."}`) put a live signature into the
  message. That also makes `TODO(httpx-request-log)`'s claim that our own records carry no
  signature true again, and it says so.

  Recorded: `allow_hosts` matches on hostname alone, so one entry admits every port on that host
  and `_blob_allow_hosts` always includes the hub's own -- left because the only way in is a URL
  the hub itself returned, and a hub that can hand you a URL can already hand you its bytes. And
  `plato-local.sh`'s degraded line printed a bare `8000/` where the line above it prints the full
  URL.

- **Test-only findings are parked, not chased.** Eight tests carry a `skip` whose reason names
  its `TODO`: the five node-harness tests (`TODO(harness-null-ids)`) and the three
  self-contained-page assertions (`TODO(protocol-relative)`). Each `TODO` records the check that
  established no shipped trigger, and the harness module says what re-enabling costs -- those five
  are the only executable coverage of `loadPanel`/`loadPanels` and they catch four defects this
  branch fixed, so they should come back before `dashboard.html` is edited again.

  The review script now treats a `TODO` as a checkable claim rather than either an excuse or an
  invitation: if the claim holds it reports `CHECKED:` in one line and raises nothing, and if the
  code is worse than the deferral admits it raises and rates it. A test skipped with a `TODO` in
  its reason is `PARKED:` and off the table, with one exception -- a defect in shipped code that a
  parked test would have caught is raised against the code. Test-only findings are `low` unless the
  shipped-code defect they would catch can be named, and for those a `TODO` plus a `skip` is the
  expected response; weakening or deleting a test that currently catches something is never
  proposed.

- **Review round 26, and the loop stops here.** One `medium`, one `unknown`, five `low`. The two
  rated above `low` were fixed; the rest are `TODO`s in the code with what was checked.

  The `medium` was a regression from the round before: `gemini.py` read its env with `env`, which
  returns `""` for a declared-but-empty variable and so ends the fallback chain -- the exact hazard
  `env_text` was added for. A compose file listing `JAPES_GEMINI_API_KEY=` and supplying the real
  key under `GEMINI_API_KEY` got an unavailable provider. All five reads in that file use
  `env_text` now, including the three in `build_genai_client` that predate this branch.

  The `unknown` turned out worse than the review suspected. `_resolves` used `gethostbyname`, which
  is IPv4-only, so `::1` and any AAAA-only host reported as unresolvable -- routing a permanent
  refusal down the transient path where it is retried per document and never falls back to v1.
  Measured: `ipv6.google.com` came back `False`. It asks `getaddrinfo` now. The same IPv4-only
  limitation in `is_private_ip` predates this branch and is left as `TODO(is-private-ip-v4-only)`:
  widening it means deciding what "private" means for `fe80::`, `fc00::/7` and `::1`, which is a
  change to the guard's rule rather than a fix.

  Two `low`s were taken because they were incomplete work this session had claimed was complete:
  `correlation_key` was still a raw read three lines above the two converted to `header_text`, and
  the guard meant to catch that matched only a single-argument `get(...)` -- so it missed the
  two-argument form, which was the one still raw. It matches on the header name now, and catches
  both arities. And `_identity_text` had quietly changed truthiness to `is not None`, making a
  decoded claim of `0`/`False`/`[]` the principal instead of deferring to the header beside it.

  Recorded, not fixed: the node harness fabricates an element for any id where a browser returns
  `null`; `"config-panel"` in one degraded assertion is inert because that guard lives outside the
  extracted code; the self-contained-page scan misses protocol-relative URLs; and seven tests in
  `test_net_safety.py` each re-implement the same transport swap. All four are test-only, none has
  a trigger in shipped code, and each `TODO` carries the check that established that.

- **Review round 25.** The ratings did their job: one `high`, seven `low`. The high one was a
  credential leak still open on the same line that redacts.

  `_collect_task_archive` redacted the interpolated message and then passed `exc_info=True`, and
  the formatted traceback carries httpx's own text, which names the whole signed URL. The record
  lands in the buffer `plato/logs_api.py` serves and the dashboard renders `traceback` verbatim.
  `redact_secrets` did not save it: `SENSITIVE_KEY_NAMES` had no `sig` entry, verified against
  that exact string. Fixed at both layers -- the traceback is gone from that call (the frames were
  storage's, not ours) and `sig`/`signature`/`x-amz-signature` are credentials to the redactor now,
  which also covers any path nobody has thought of. Checked for false positives: `config=` and
  `design=` are untouched, because the pattern is word-anchored.

  Writing that test surfaced one the review had not: httpx's own logger writes
  `HTTP Request: GET <full url>` at INFO, so the raw record in the *process* log carries the
  signature even though the served endpoint is now redacted. Recorded as `TODO(httpx-request-log)`
  rather than fixed: raising another library's log level from inside a fetch is a side effect on
  the host application, and the exposure that matters is covered. The test asserts the served form
  and filters our own records by logger name, so it says which of the two it is checking.

  Taken from the `low` pile only where the finding was about something this session added: a
  `TODO(csp-info-ui)` describing a gap that did not exist (the loop above it already covers both
  paths), an assertion claiming to check a signature on a branch that interpolates no URL, and
  `set(fetched)` where the duplicate-fetch class this file exists for needs the list. The sixth
  hand-rolled `MODEL_CARDS.pop` is gone now that the conftest fixture covers it, and that
  fixture's shallow copy is recorded with what was checked -- `ModelCard` is frozen, so an
  in-place mutation would raise.

- **Review round 24, triaged rather than exhausted.** Nine findings; five taken, four recorded as
  `TODO`s with the trigger and the blast radius written down so the deferral is checkable.

  The one that mattered: a refused blob host fell back to v1 only inside `_probe_v2`, which runs
  once per store. On the settled path the error raised, `_permanent` excluded it from retry, and
  `_fetch` dropped the document as absent -- so a store whose probe settled `_v2_download = True`
  (the first document's signed URL on the hub's own host, which is always admitted) silently lost
  that document and every later one on separate storage, one warning apiece. It latches and falls
  through to v1 now, the way `_bulk_fetch` already latched `_bulk_available`.

  The behavioural dashboard harness auto-created an element for any id, so it could not see the
  way the real page breaks after a markup rename: `getElementById` returning `null`. It seeds the
  ids the rendered page actually contains and returns `null` otherwise. And each panel's failure
  is contained: the frame's `try` covered only the fetch, where the three blocks it replaced
  covered fetch and render both, so a route that stopped returning `routes` would have taken every
  later panel with it.

  `"database"` joins the three route tuples that pin the identity gate on the working app -- it is
  the third router `create_plato_app` hands `identity_required` and it was in neither loop.
  Verified by regression: with the knob removed from that router, two tests now fail that passed
  before. It stays out of the degraded app's tuple, which mounts only two of the three.

  Recorded and not fixed, each with what was checked: `omit=("info",)` would break the dashboard
  script (one production caller passes `omit`, with three labels, never `info`); the self-contained
  page scan reads `<style>` blocks and not `style=` attributes (no page has one carrying a `url(`);
  `/api/v1/config`'s gating is absent from its guide row (a refused write, not a withheld body, so
  it needs different words); and the looser page CSP is asserted for `/` only (both pages come from
  one `_PAGE_HEADERS` constant, so they cannot differ).

- **The review now rates findings.** Every finding carries `IMPORTANCE: high|medium|low` with the
  blast radius it actually established -- the call sites enumerated, the configurations that reach
  the code, whether anything outside the repo depends on it -- or `unknown` when it could not tell.
  An unsubstantiated "small blast radius" is worse than no rating, because the author acts on it.
  A `TODO` on the code neither excuses a finding nor invites one: a deferral is a claim about blast
  radius and is checkable like any other.

- **Review round 23.** Three defects, and two of them were in round 22's own redaction work.

  A refused blob host is not always permanent. `is_private_ip` fails closed on `socket.gaierror`,
  which is correct for an SSRF guard and wrong as a verdict: routing that through
  `KnowledgeHubUnsupportedError` meant one DNS hiccup on the storage host dropped a document with
  no retry and one warning, against that class's own promise to be distinct from a transient
  failure. `net_safety.UnresolvableHostError` is the same refusal with a different answer to "can
  a retry fix this", and both blob callers treat it as transient.

  The refinement is skipped when `is_private_ip` has been replaced, because it is the seam nine
  test files patch and a stub saying "private" is authoritative: second-guessing it with a real
  lookup reported every stubbed host as unresolvable, since a test hostname does not resolve.

  Redaction keyed on the URL the caller passed missed the URL the failure actually names:
  `fetch_validated` follows redirects itself and httpx reports the final hop, so a signed URL
  redirecting to a second signed URL left the second one's signature in the message.
  `redact_urls` scrubs by pattern, which needs no assumption about which URL that was.

  And the Gemini alignment stopped one line short again: `_vertex_mode` learned to read
  `JAPES_GOOGLE_CLOUD_PROJECT` while `__init__` on the line above still read only
  `GEMINI_API_KEY`/`GOOGLE_API_KEY`, so a deployment using this repo's prefixed convention was
  told the provider was unavailable for a client that would have worked.

  `authority/context` now asks `header_text` like its two siblings, and the source-inspection test
  no longer exempts it -- an exempted third builder is how the rule drifted to begin with. Model
  cards are restored by one conftest fixture rather than five hand-rolled pops and a sixth that
  was missing: `test_vision_content.py` was leaving four cards in the process-global table. The
  redirect budget is asserted at its boundary (5 hops resolve, 6 raise, and 0 means no redirect at
  all), `identity_from_claims` is tested against a whitespace subject, and the message
  `docs/DEPLOYMENT_ENV.md` tells an operator to grep for is pinned to the one the code raises --
  the first version of that row quoted a message no branch produces.

- **The dashboard's four panels are one code path.** Not a review finding: the four
  hand-written panel blocks were where the review kept finding the same disagreement, so they were
  the one place a structural change paid. Five parallel statements of the same fact
  (`_NAV_PANELS`, the nav list, four fetch guards, three `withheld` branches, and three
  inconsistent id families -- `db-*` beside `metric-rows` beside `log-*`) are now one
  `PANEL_LABELS` tuple, one derived `panel_id`, and one `loadPanel` frame. Each panel supplies only
  what is its own: its route, what an empty answer means, and how one row is drawn.

  The id convention is what closes the class of bug rather than any individual fix: every element
  a panel touches is `<label>-*`, derived from the same label as the nav entry, so a mapping
  between the two cannot drift.

  `tests/test_plato_dashboard_behaviour.py` runs the page's own `loadPanels` under node against a
  stub DOM and a stub `fetch`, and asserts what it did -- which routes were requested, what each
  panel's rows and meta and empty text ended up as. Every earlier guard on this file matched a
  string in the rendered page, and one of them passed against a guard written as a top-level
  `return` that stopped three panels rendering at all. Four defects from earlier rounds were
  replayed against the new tests and all four are caught; six string-matching tests are removed as
  superseded by strictly stronger ones. The whole page was also run against a live replica: 3
  table rows, 6 metrics rows, and the logs panel's own empty message.

- **Review round 22.** One defect, one symmetry finding, and both were about the same thing --
  a signed URL is a credential.

  The blob path's error messages carried the whole signed URL, query signature included.
  `fetch_validated`'s `raise_for_status` produces httpx's `"Client error '403 Forbidden' for url
  '<full url>'"`, and that was interpolated verbatim into a `KnowledgeHubError` which `materialize`
  logs at WARNING and `plato/logs_api.py` then serves. An expired signature is the ordinary case on
  that path. `net_safety.redact_url` reduces a URL to scheme, host and path, and every message
  either module builds goes through it -- the same care `dsn_summary` and `display_path` already
  take with a DSN and a home directory.

  `_collect_task_archive` is the sibling that fetches a signed URL the same way, and it swallowed
  the refusal into `None`: with `JAPES_KH_BLOB_HOSTS` unset, every `materialize` over the bulk
  threshold paid the trigger call, the full poll and the link call again on every run. It raises
  `KnowledgeHubUnsupportedError` now, which the store's existing latch handles.

  `_permanent` is one rule for "retrying cannot change this", covering both a denial and a missing
  capability -- a refused blob host was burning the full exponential backoff per document.

  And the third reader of `X-Trace-Id`: `authority/context` got the blank-is-absent rule,
  `governed_http` treated blank as absent but not padding, and `server/app` did neither. All three
  go through `identity.header_text` now, along with `X-Span-Id`, `X-Actor-Ref` and
  `X-Surface-Ref`, which have the identical shape.

- **Review round 21.** One defect, in round 20's own fix, and the worst of the loop: the
  "a hidden panel does not ask" guard was written as `if (...hidden) return;` at the top level of
  `load()`, so on the degraded replica it returned before the metrics, logs and config blocks and
  those panels never rendered at all -- on the one app whose own comment says that is when an
  operator most wants them. The test asserted the guard *string* was present, which the broken
  shape satisfied, so the full suite stayed green. One `shown(id)` helper now wraps each block,
  all four panels have it, and the test asserts each guard wraps its own fetch and that no guard
  leaves the function.

  A blob host the SSRF policy refuses now reports as `KnowledgeHubUnsupportedError` rather than
  `KnowledgeHubError`, so `fabric.docs` falls back to v1 instead of failing the whole collection.
  It refuses every document identically, which makes it the route that is unusable and not the
  document; v1 streams bytes through the hub and works. `net_safety.UnsafeUrlError` (a
  `ValueError`, so existing callers are unaffected) is what distinguishes a policy refusal from a
  transport failure, and the client warns with the variable that fixes it.

  `guide.md`'s `/api/v1/database` row promised a withheld response no shipped wiring can produce:
  `check_settings` refuses to start a strict posture with identity off, and the degraded app does
  not mount the route. The row says that now instead.

- **Review round 20: PASS, no defects or symmetry findings.** The families this branch claims to
  have closed were checked and are complete: no truthy-string env parse outside `envvars.TRUTHY`,
  no bare `httpx.AsyncClient` blob fetch in `clients`, and the one other `validate_url_safe`
  caller does not follow redirects. Three notes taken.

  Moving the reachability probe ahead of the counting loop meant a reachable database whose every
  table count failed came back `connected: true` with a `reason` no panel rendered: the operator
  used to read that as "Not connected: no table could be counted". The connected branch shows it
  now.

  A hidden panel still fetched its route, so the degraded replica answered a 404 per dashboard
  load for each of Database and Configuration. The nav link and the panel were two ways to an
  unmounted route; the fetch was the third.

  `/info` is the one `create_*_router` without the gate, and the rationale did not say why. It is
  what an operator reads when a replica will not start, which is exactly when no identity
  middleware is running and no `auth` dependency exists to unlock anything: a gate would withhold
  the answer in the case the route was built to give. Its fields are chosen to be safe to hand
  out instead, and that is now written where the exemption lives.

- **Review round 19: PASS, no defects.** Four findings, all taken, and one of them a reversal.

  Round 17 narrowed the legacy manifest adoption to the documents each run covers, to stop a
  foreign entry being carried into the collection's scope. That was the wrong trade: the legacy
  read is gated on the collection's scope being empty, so a first run covering 5 of 100 documents
  wrote 5 entries and never read the legacy key again, re-downloading the other 95 for good.
  Over-reporting is what this store already accepts and documents -- a hash only permits a skip,
  and that decision also requires the file to be on disk. The whole map is adopted again, with a
  test for the partial first run.

  `api_prefix` was the last hand-spelled copy of the blank-is-unset rule; a grep for the pattern
  now returns only `env_text` itself.

  Two claims narrowed to what the code does: the empty-`data:`-payload guard is about a malformed
  URL, not parity with the HTTP path, which returns a `200` with a zero-length body as the
  document; and `_safe_fetch`'s two `Raises:` lists now name the `ValueError` a `204` produces,
  which a caller reading them would have been catching as `HTTPStatusError`.

- **Review round 18: PASS, no defects.** Five findings, all taken, two of them families the
  previous round had counted wrong.

  There were five copies of the truthy-string list, not four. The one missed is the most drifted:
  the queue's `use_managed_identity` tested `== "true"`, so `JAPES_USE_MANAGED_IDENTITY=1` (or
  `yes`, or `on`) read as False and sent the client down the connection-string path, which then
  raises when no connection string is set. And the Gemini unification stopped one line short:
  `build_genai_client` reads `JAPES_GOOGLE_CLOUD_PROJECT` first while `_vertex_mode` read only
  `GOOGLE_CLOUD_PROJECT`, so a deployment setting the prefixed name was told the provider was
  unavailable though the client would have been built and worked.

  Three claims corrected: `describe_database`'s two early returns carried neither `tables` nor
  `truncated`, which its own docstring tells an exported caller to rely on; `require_200` does not
  decide `204`/`205`, which carry no body and are refused either way; and the metrics docstring
  named one of the two unlocks where its sibling names both.

- **Review round 17.** Two defects.

  A listing row that identifies nothing was treated as weakly identified rather than as no
  information. `_collection_metadata` passes `updated_at` straight through, so a hub that omits it
  gives rows with no digest at all; those went into the probe's `weak` group, and one probe
  concluding "the endpoint adds no sha256" then left the other five with no digest either, out of
  the manifest and re-downloaded on every run with `page_count` never filled. Verified against
  this tree: one metadata call and one manifest entry for six documents, where the shape this
  replaced made six of each. They are asked now, like an unlisted row.

  `trace_id` kept the blank-header-is-present bug the identity fields beside it had just had
  removed: `governed_http` substitutes a generated id only when it is `None`, so `X-Trace-Id:`
  with no value travelled the hop as `""` and landed in the refusal record.

  `env_flag` joins `env_text`/`env_list`, retiring four copies of the truthy-string list --
  `launcher._env_bool`, `wiring_default.identity_requested`, and the Gemini pair, which had
  already drifted by reading `on` as no. `identity_requested`'s own docstring had warned that two
  copies diverge on the next edit; there were four.

  `JAPES_KH_BLOB_HOSTS` reached the deployment catalogue: without it a deployment whose hub hands
  out `http://minio:9000` signed URLs goes from working to a refused private address on upgrade,
  with the fix discoverable only by reading a docstring. Every dashboard panel is omittable now,
  not just the two the degraded app happens to drop. And `env_list`'s real default is asserted:
  every case passed `default=("a",)`, so unset-means-empty, which `_blob_allow_hosts` depends on,
  was untested.

- **Review round 16: PASS, no defects.** Five findings, all taken.

  With `_identity_text` owning the blank-and-padded rule, `build_invocation_context_from_headers`
  was restating it under a twelve-line comment describing bugs the layer below now prevents; that
  restating is how the two came apart in the first place. Twelve lines and two `.strip()` calls
  gone. The claims path had the same gap in the other direction: `identity_from_claims` stripped
  `sub` and passed `preferred_username`/`email` through, so `"  alice  "` from a token was a
  different principal from `"alice"` through a gateway, against its own docstring's promise that
  the two produce one identity.

  The legacy manifest adoption took the whole path-scoped map. The save loop visits only this
  run's documents, so an entry for a document outside the collection survived and was written
  under the collection's scope from then on. Only this run's ids are adopted now.

  Two records rather than changes: `_NO_BODY_STATUSES` had two comments disagreeing about 304, and
  the blob path's redirect budget went from httpx's 20 to `DEFAULT_MAX_REDIRECTS`. The 5 is right
  here -- it is the number argued for a signed storage URL behind a CDN -- but a deliberate
  narrowing should say so where the sibling defends its own 10.

- **Review round 15.** Two defects, both in round 14's own fixes, and both the same mistake:
  fixing part of a family.

  `x-user-id` was the member of the `x-user-*` set the strip rule skipped, and `UUID()` does not
  tolerate surrounding whitespace, so a gateway that padded the header made the caller anonymous
  and every route under `require_identity` answered 401. Both readers strip now.

  `connected` still meant "an engine URL could be built" on the counting path, which downgrades it
  only when every count fails: a store whose registered metadata lists no tables has no counts to
  fail, so the default route called an unreachable database connected while `?count_rows=false` on
  the same route said otherwise. The `SELECT 1` runs before both paths now, and the all-counts-
  failed message says the schema may not be migrated, which is what it can still mean once the
  connection has answered.

  `omit` reached the dashboard's nav and not its panels, so the degraded app dropped the
  Configuration and Database links and then rendered both panels against routes it does not mount.
  And two comments claiming more than their code: the `fetch_signed_url` move does not let
  `download_to_file` take a `data:` URL (`_safe_fetch` refuses a non-http(s) URL at its own front
  door), and `sync_collection`'s legacy manifest read can find a path-scoped entry left by a
  direct `materialize()` into the same directory.

- **Review round 14: PASS, no defects.** Five findings, all taken.

  One header set had two readers and two answers. `build_invocation_context_from_headers` got the
  blank-and-padded rule in round 9; `identity.py`, the layer it reads through, did not, so
  `get_current_user_email()` answered `""` for `x-user-email:` and `" a@b.c "` for a padded one
  while the context builder answered `None` and `"a@b.c"` for the same request. Both go through
  one `_identity_text` now.

  `fetch_signed_url` moved to `net_safety` beside `fetch_validated`. It names nothing
  hub-specific, and `clients` sits below `tools` in the layer contract, so while it lived in the
  Knowledge Hub client `documents.local` could not reach it and `download_to_file` could not take
  a `data:` URL at all. The client imports the name it calls.

  Three smaller ones: `_probe_failed.discard` could never fire (`_current_hash` runs at most once
  per document per run) under a comment crediting it with an effect the digest restore actually
  has; `304` left `_NO_BODY_STATUSES`, which its own comment said `raise_for_status` refuses
  first; and `_dsn_summary` became `dsn_summary`, since two modules import it and the underscore
  claimed a privacy the import contradicts.

- **Review round 13.** One defect, in round 12's own fix. Withholding the database route by
  asking `describe_database(count_rows=False)` avoided the 40 discarded scans, but that path
  returns before opening a session, so `connected` meant "an engine URL could be built": a replica
  with Postgres down answered `connected: true, withheld: true` to an anonymous caller while the
  counting path on the same route reported it could not reach the database at all. The docstring
  and the new test both asserted a guarantee the path did not keep. `count_rows=False` now runs one
  `SELECT 1`, which fixes `?count_rows=false` on the open route as well.

  `env_number` and both strictness readers spelled `env_text`'s rule by hand in the file that
  defines it. `environment_tier` and `deployed_posture` keep their own loops: they scan every name
  for a deployed tier, so first-non-blank would change what they answer.

  A base64 `data:` payload is percent-decoded before decoding and validated after: `b64decode`
  drops non-alphabet characters by default, so `...;base64,ab%2Bcd` returned corrupt bytes as a
  successful download. And the metrics and logs panels clear their rows when withholding, which
  only the database panel did.

  Not taken: `page_count` reaching only the probed document when a hub's metadata endpoint carries
  it without `sha256`. The field is documented as absent whenever nothing asked, and dropping a
  real value from the one document we did ask about to make the set uniform is worse than the
  inconsistency.

- **Review round 12: PASS, no defects.** Five findings taken anyway, four of which the previous
  round's own fixes created.

  `fetch_validated`'s `validate` parameter is gone, and with it the exclusivity `ValueError`
  against `allow_hosts` and `documents.local._validate_url_safe`. The seam existed so a caller's
  wrapper stayed the object its SSRF tests patched, but the same round deleted the module alias
  those tests patched through, leaving a wrapper that called `validate_url_safe(url)` and a
  parameter whose only value was the function's own default. `_safe_fetch` reaches the rule
  directly now, and a test asserts `documents.local` names `is_private_ip` nowhere.

  `GET {prefix}/database` ran `describe_database` and then withheld the answer: on a strict
  deployment with `require_identity=False`, an unauthenticated request drove up to
  `MAX_TABLES_COUNTED` (40) `SELECT COUNT(*)` scans per call and returned none of them. The gate
  now asks with `count_rows=False`, which is all `connected` needs. `logs` and `metrics`, the
  siblings whose shape this router's docstring cites, already returned before doing the work.

  A `data:` URL with a comma and nothing after it (`data:application/pdf;base64,`) reached exactly
  the outcome the comma guard was written to prevent, a zero-byte document reported as a
  successful download; it is refused now, as the HTTP path already refuses a 204 for that reason.

  Two comments that outran their code: `validate_url_safe`'s worked example still pointed at the
  manual-redirect loop the same diff deleted, and `authority/context` justified stripping a
  `user_id` that `identity_from_headers` returns as a parsed `UUID`.

- **Review round 10 (full range): no defects.** Four findings, all taken. One was a regression
  introduced by the previous round's own tidying: adopting `net_safety.DEFAULT_MAX_REDIRECTS` in
  `_safe_fetch` halved the redirect budget for `read_from_url` and `download_to_file` from 10 to
  5, and that 5 is argued for a signed storage URL behind a CDN, not for arbitrary web fetches --
  so a 6-hop chain that resolved began raising. It has its own `WEB_MAX_REDIRECTS` again, with the
  reason written down.

  `env_list` joins `env_text` and `env_int`: the comma-list parse was spelled inline in the
  Knowledge Hub client and again in `wiring_default`, with the blank filter in a different position
  each time. A value naming nothing (`","`) now means the same as unset. And two docstrings: one
  claimed `PLATO_LOCAL_ROOT` holds the migration tree six lines below the correction saying it does
  not, and `nav_html`'s `omit` matches labels while its own text described paths.

- **Review round 9.** One defect, and it undid the safety of round 6's own fix: a header that is
  present but blank produced an identity. `email or name` yields `""`, and the context builder
  tested `is None`, so `x-user-name:` gave a context whose principal is the empty string -- an
  anonymous request the middleware admitted, and the `identity_required` gate then opened for.
  On a strict deployment `GET /api/v1/logs` returned the buffered records and `/api/v1/metrics`
  the full per-route inventory, both of which were withheld before that gate existed. It is the
  same empty-identity hole closed on the token path earlier in this section, left open on the
  header path the gate actually rests on. An empty identity is not an identity, in
  `build_invocation_context_from_headers` as in `verify`.

  Three notes: the refresh floor used `fetched_at > 0` as its "has fetched" sentinel, so an
  injected clock with a zero origin made a successful fetch indistinguishable from never having
  fetched and the floor failed open again -- a separate flag now; the security-header test
  asserted only that *a* policy was present, which would have passed with the dashboard silently
  getting the API's `default-src 'none'` and rendering as unstyled text; and a docstring still
  described the Swagger route that round 8 deleted.

- **Review round 8: no defects.** Five non-blocking findings, fixed anyway, one of which was
  substantive: the degraded app is built by hand rather than by `create_app`, so it attached none
  of the response security headers -- every degraded response went out with no CSP, no
  frame-ancestors and no nosniff, on the replica an operator is most likely to open in a browser.
  The `/` page had one only because it sets its own. FastAPI's CDN-loaded `/docs` is dropped there
  too, as the working app already does: it was mounted and reachable, so the nav omission had been
  hiding a page that worked, for a reason (the CSP blanking it) that no header was being set to
  make true.

  The rest: `sync_collection` passed `manifest_scope or collection_id`, which is `materialize`'s
  own default now -- and passing it made `manifest_scope is None` false in there, silently
  disabling the adoption of a manifest recorded under the previous path-based scope. A comment
  claimed `_dsn_summary` resolved the engine accessor when both callers still did it themselves,
  so it now does. `fetch_validated` accepted `validate` and `allow_hosts` together and quietly
  honoured only the first. `_safe_fetch` still had its own `max_redirects=10` beside the constant
  extracted for it. And the new `env_*` test file promised coverage of the numeric readers and
  contained one test for the text one.

- **Review round 7.** The SSRF guard added earlier in this section broke an ordinary
  deployment: `validate_url_safe` refuses any host resolving private *and* fails closed on one
  that does not resolve, so a Knowledge Hub whose blob URLs point in-cluster
  (`http://minio:9000`, a compose stack, or a hub serving blobs from its own address) had every
  `download_document_v2` raise. It now accepts hosts the deployment has declared: the hub's own,
  automatically, plus `JAPES_KH_BLOB_HOSTS`. The scheme rule and the private-IP rule still apply
  to everything else, so this admits a named host rather than disabling the guard.

  `_probe_failed` was added to and never discarded, so a document whose first metadata call
  failed had its *successful* retry thrown away for the listing's weaker digest -- and
  re-downloaded on the run after the retry worked. The test passed because it asserted only the
  call count; it asserts the recorded digest now.

  `create_config_router` was the third member of the withholding family without the new
  `identity_required` kwarg, so one predicate meant two things. That asymmetry is real and is now
  stated rather than implied by an omission: a gateway-injected header identifies who is asking
  without being an authorization decision, which is enough to *read* diagnostics and not enough
  to *write* configuration. The guide and the logs docstring said these routes need an `auth`
  dependency, which stopped being true when `require_identity` began unlocking them.

- **Review round 6.** The consequential defect: the withholding gate keyed on `auth is None`,
  and *no shipped wiring sets `PlatoWiring.auth`* -- so on every strict deployment there is, an
  authenticated operator saw a permanently empty metrics table and no log records, while
  `require_identity` was already authenticating each request and the guide described an `auth`
  path no wiring takes. Identity middleware is now the other way a caller can be known, so a
  working replica serves both and the degraded app -- which has no middleware and cannot be given
  any -- still withholds.

  The digest preservation added in round 5 covered the probed document and not the batch behind
  it: a failed metadata call reports `None` for any document, and letting that overwrite a listing
  digest costs a re-download on every run. It applies to all of them now.

  `create_config_router` -- which `logs_api` cites as the shape it copied -- was the one member of
  that family still spelling the predicate out after it was extracted for the other two.

  Three notes: a docstring reflow had lost its indentation and read as a fragment; two
  `fetch_validated` tests and the `env_text` test had landed in the materialize file rather than
  beside what they test; and the `data:` branch matched `;base64` case-sensitively where the
  grammar is case-insensitive, and returned a zero-byte document for a URL with no comma at all
  instead of refusing it.

- **Review round 5.** Three defects, all in rounds 3 and 4's own changes.

  The sharpest was a branch that could not fire: `get_document_metadata` swallows every error and
  returns `None`, so `_current_hash` stored `{}` and the "the probe call failed" test was
  indistinguishable from "the record was empty". The test pinning it passed only because its stub
  *raised*, which the production client never does -- so against a real hub a timeout on the
  probed document still concluded "this hub does not hash" and denied every other document its
  backfill, while overwriting the probed document's listing digest with `None` so it re-downloaded
  on every run. Failures are recorded explicitly now, and the listing's digest is kept when the
  call does not answer.

  `fetch_validated`'s no-`Location` exit returned before the status check, and httpx calls any 3xx
  a redirect -- so a `302` without the header, or a `304`, came back as an empty body the caller
  read as content. Both exits are one path now. And delegating `read_from_url` to that helper
  imported a 200-only rule into a general web fetch that legitimately meets `203` and `206`, so
  the rule is opt-in and only the Knowledge Hub client asks for it.

  Three notes: the scope docstring claimed a default that only holds when a collection is given;
  the guide said log records and metrics are withheld in a "deployed" posture when the gate is
  strictness, and `dev-daily` is deployed but deliberately relaxed; and `DEFAULT_TIMEOUT` is an
  `httpx.Timeout` passed into two `float` parameters.

- **Review round 4.** The defect was round 3's fix again: a document the listing never returned
  has no digest at all, not even the `updated_at` fallback -- and the walk gives up after its page
  budget, so partial coverage is a designed state rather than an edge. The probe's conclusion is
  about what the metadata endpoint adds to a *listed* row, so unlisted ids are now always asked.

  Two symmetry findings, both duplication this session created: the withholding gate and its
  `{"withheld": True, "reason": ...}` reply were spelled once in `logs_api` and again in
  `metrics_api`, and now live in `plato.posture`; and `resolve_kh_token` kept its own copy of the
  blank-is-unset loop that `env_text` had just been extracted from, while its docstring cited it
  as the precedent.

  Three notes: the dashboard's withheld branch dropped the totals the router keeps deliberately,
  so a deployed replica rendered as having served nothing; the "transient, so it raises" comment
  had come to sit over a refused host and a storage 404, neither of which a retry fixes; and a
  non-base64 `data:` URL was returned without percent-decoding, so `data:text/plain,a%20b` gave
  `b"a%20b"`.

- **Review round 3.** Both defects were in round 2's own fix: the one-document probe conflated
  "the listing gave a weak digest" with "no listing ran at all". Below the threshold every id is
  weak by construction, so one probe decided the strategy for documents nothing was known about
  and left the rest with no digest -- `_needs_download` then said yes on every run and
  `page_count` was never filled, silently disabling the per-document path the threshold exists to
  select. And `_current_hash` reports any failure as `None`, indistinguishable from "no hash", so
  one timeout suppressed the metadata call for every remaining document. The probe now runs only
  when a listing produced no hashes, picks the lowest id rather than whatever set ordering
  offered, and falls back to asking everyone when it fails rather than concluding from it.

  The blank-is-unset rule was hand-spelled at four sites in `wiring_local`; `envvars` owns env
  reading and already stated it once, so it is now `env_text` beside `env` and `env_int`.

  Three notes: `raise_for_status` accepts every 2xx, so a `204` returned its empty body as the
  document -- only 200 is content now; the test named "not walked pointlessly" only ever avoided
  the metadata calls, not the walk; and two comments claimed the degraded app has no `/docs` when
  FastAPI's Swagger UI is mounted there -- the link resolves, to a CDN page the CSP blanks, which
  is a reason to omit it but not the one given.

- **Review round 2 (the loop now runs after every commit).** Three of the four defects were the
  same shape: a guard applied to one member of a family and not the others.

  The dashboard's metrics panel had no reader for the `withheld` response the logs panel was given,
  so a deployed replica that had served traffic rendered "No requests served yet." beside a
  non-zero request total in the same payload. The nav omission was applied to `/` and not to
  `/info/ui`, which renders the same nav -- so the three 404s moved one click away instead of
  going. And `status` was the third member of the script's port family without the ownership check
  `start` and `stop` had just been given, so it still reported another repo's uvicorn as a running
  Plato.

  The redirect-following loop was a line-for-line re-derivation of `tools.documents.local`'s.
  `clients` sits *below* `tools` in the layer contract and cannot import it, so the loop moved to
  `net_safety` -- where `validate_url_safe` already lives and both tiers already import from --
  and both now call it. Converting the `tools` side broke 13 of its SSRF tests, which patch a
  module-local alias my delegation bypassed: they had gone on passing against the real resolver
  instead of the stub. The validator is injectable now, so each caller's seam survives.

  Three notes with it: PyJWT's `require` checks a claim's presence and not its content, so
  `"sub": ""` decoded fine and reached a direct caller; `listing_has_sha256` put an all-legacy
  collection on a hashing hub on the wrong side of the cost model, which one probe call now
  settles instead of a guess; and the guide offered an `auth` dependency on the degraded path,
  where there is no way to supply one.

- **SSRF on the signed-URL fetches.** The URL comes out of a Knowledge Hub response and was
  fetched with `follow_redirects=True` and no validation, at both sites -- so a manipulated or
  open-redirecting response was an unauthenticated GET from inside the deployment's network.
  `net_safety.validate_url_safe` already existed for this. Both sites now share one
  `fetch_signed_url` that validates every hop before fetching it, because that helper's own
  docstring says a caller following redirects must, and follows redirects itself rather than
  leaving it to httpx. A `data:` URL is decoded locally and never fetched -- that is what the
  Mock Knowledge Hub hands out, and it touches no network.

- **A signed token without a subject is refused.** PyJWT does not require `sub`, so one produced
  `{"userId": ""}` -- which a caller keying storage on it reads as a single shared anonymous user
  rather than as no identity. Required in `verify`, and refused again in `identity_from_claims`
  for claims that did not come through it.

- **An issuer publishing no usable keys could be hammered.** The 30-second refresh floor was
  gated on the cache *holding* keys, so `{"keys": []}` -- or entries with no `kid`, which are
  dropped -- failed open: both the unforced and the forced load re-fetched on every request, two
  issuer fetches per request, unbounded. A fetch counts even when it yielded nothing.

- **Per-route metrics are withheld like log records.** `logs` was gated for a deployed posture
  because the degraded app has no identity middleware; `metrics` sits on that same app with no
  `auth` and no guard, serving the route inventory and per-route request and error volumes to
  anything that could reach the port. The totals and uptime stay, because a probe needs them and
  they name nothing.

- **The degraded nav offered three routes it does not mount.** Guide, config and database each
  404'd from a nav an operator was reading while already debugging a replica that would not start.

- **The guide promised logs a deployed posture withholds,** and `boot_contract.py` had it right
  all along. Corrected, along with the routes table. Its em-dashes are gone too.

- **A hub with no `sha256` at all is no longer walked pointlessly.** A weaker digest is worth a
  metadata call only where that call can improve it: on a hub predating hash computation nothing
  has one, so the paginated walk *plus* N metadata calls was strictly worse than the N calls
  alone. Told apart now by whether any listing row carried one.

- **`./scripts/plato-local.sh` stopped killing whatever held the port.** `listening()` is pure
  port occupancy, so `stop` and `restart` SIGTERMed another repo's uvicorn, a Streamlit or a
  Docker proxy and `kill -9`'d it five seconds later, while `start` called it "already running".
  It checks the process is Plato now, and refuses rather than guessing.

  `wait_until_up` also used `curl -fsS`, which treats the degraded replica's 503 `/health` as a
  failure -- so a typo'd `PLATO_WIRING` burned the full 30 seconds and reported that nothing came
  up, the exact confusion the fallback `/health` exists to remove. It waits for an answer, then
  reports the reason: two seconds instead of thirty.

- **Three `wiring_local` knobs treated an empty variable as a value,** where two others in the
  same file already guarded it. `PLATO_LOCAL_DB=` made the database path the root *directory*;
  `PLATO_LOCAL_CACHE=` pointed the pack cache there; `PLATO_LOCAL_TENANT=` put `""` on every
  session and manifest row. The boot line also prints paths through `display_path` now, for the
  reason the dashboard does.

- **The external-reference check could not see a stylesheet load.** It matched `src=`/`href=`
  attributes only, so `@font-face { src: url(https://...) }` or `@import` passed all three "no
  CDN, no external font" assertions -- which the bare `"http://" not in body` check they replaced
  did catch.

- **The review itself: sliced rather than skipped.** The push went out unreviewed because the diff
  exceeded the one-pass cap and the hook exits 0 there -- so the gate passed silently on exactly
  the pushes big enough to need it, which a workflow that squashes several rounds into one commit
  produces every time. It now packs whole files into slices, blocks if any slice reports a defect,
  caps the slice count, and names the files in any slice it could not reach.

- **Smaller corrections.** `_dsn_summary` already owned the engine/URL introspection
  `effective_settings` re-spelled; `materialize` and `sync_collection` documented a default scope
  the code no longer uses; an explicit `timeout_seconds=0` bypassed the floor its own constant
  documents; the v2 entity docstrings named `KnowledgeHubError` where the code raises the
  `Unsupported` subclass a caller is meant to branch on; a duplicated span-shape test that read
  the ambient cap moved beside the pair that owns that contract; two subprocess tests parsed
  stdout without checking the exit code; a registered test model card had no cleanup; and an OIDC
  test's name described a path it did not exercise.

## [2.5.0] - 2026-09-06

*Continues the [2.5.0] section below, which carries `plato 0.1.1`. `2.4.9` sits between the two, and
`2.4.8` below them, because both merged in from `dev` while this release was in progress; the
interleaving is how that shows.*

- **Inbound token verification hardened (PR review).** Three findings on `plato/oidc.py`, all
  latent because nothing wires `TokenVerifier` into a request path yet, which is the window to fix
  the shape rather than patch it.

  **An `http://` issuer is refused at construction.** Signing keys over plaintext are worse than
  no verification: an observer between Plato and the issuer can substitute their own public key,
  after which every token they sign passes. The review named `issuer`; `jwks_uri` is the URL
  actually fetched, so both are checked. `http` on loopback still works, which is the normal shape
  for a local identity provider and has no network for an observer to sit on.

  **`verify` is async.** The key fetch was a blocking `httpx.get` with a 10s timeout, and Plato's
  identity middleware is an `async def` -- so wiring it there would have stalled every request on
  the loop for as long as the issuer took. `fetch_jwks` stays injectable and now takes either a
  sync or an async callable.

  **One fetch under contention.** Check-then-fetch let every caller arriving on a stale cache read
  it as stale and call the issuer before any of them wrote, so a burst naming an unknown `kid`
  dispatched as many fetches as there were callers. Double-checked under an `asyncio.Lock`; the
  30-second floor now actually holds.

- **The health probe and the server agree on the port.** They read `PORT` differently, so they
  disagreed on every value `env_int` normalises: with `PORT=""` the server bound 8000 while the
  probe built `http://127.0.0.1:/health`, which urllib connects to port 80 -- so `--health`
  reported `unhealthy` and exited 1 for a replica that was serving. Converting the two
  `uvicorn.run` calls in the previous change is what made this reachable: before that, the same
  environment crashed uvicorn at startup and the mismatch could not be observed.

- **The Mock Knowledge Hub's HTTP double serves the v2 routes.** The in-process
  `MockKnowledgeHubClient` was given the single-document and bulk methods while the double kept
  only the v1 archive route -- so a replica wired to Mock KH took `_probe_v2`'s doomed path on
  every new `DocStore`, and nothing short of a real hub exercised the route that is now the
  default. All four steps are there (document access, trigger, status, link), the bulk trigger
  requires the same `x-user-id` the real one declares, and a `data:` URL stands in for the signed
  one.

- **A suffixed filename is attributed even when its base name is also requested.** The collision
  check ran before the exact-name lookup, so a document really called `Report (2).pdf` was
  discarded from the archive whenever `Report.pdf` was in the same request -- the strip matched
  and it was read as a KH rename -- and re-fetched individually every run. The earlier fix only
  covered the case where no `Report.pdf` exists, which is what its test asserted.

- **Three claims trimmed to what the code does.** `_bulk_fetch`'s docstring said bulk "must not be
  able to fail the materialize" while a denial deliberately propagates eight lines below, and
  `bulk_download_documents` claimed it never raises while raising for an old pin, a missing user
  id and a denial. And a comment added in the previous change blamed a hazard on a call site that
  never had it: the `os.getenv(a) or os.getenv(b)` chain it replaced already skipped an empty
  value -- the hazard is in routing such a chain through `env`, not in the chain itself.

- **A transient failure on the probing document no longer downgrades the whole store.**
  `_v2_probed` was set *before* awaiting the probe, so a refused signed URL raised out with the
  route still unknown but recorded as probed -- and `DocStore` is long-lived behind
  `fabric.docs`, so that one bad moment sent every later `materialize` down v1 as well. Exactly
  what `_v2_unsupported` exists to prevent, undone by the ordering of two lines. The flag is set
  only once the probe returns.

- **An empty variable no longer ends a fallback chain.** `env` treats a set-but-empty value as
  set, so `env_int("JAPES_UI_PORT", "PORT", ...)` took its default without ever consulting `PORT`:
  with a blank `JAPES_UI_PORT` and the platform's `PORT=8080` the UI bound 8501, a port nothing
  routes to. An empty string is not a number, so `env_number` now takes the first *non-empty*
  name. This is the hazard its own docstring cites, reintroduced one layer up while fixing it.

- **`env_int` reaches Plato's own entry points.** Both called `int(os.getenv("PORT", "8000"))`,
  where `PORT=""` raises and the server does not start -- the same conversion applied to the
  queue, the launcher and the span cap in the previous change, and not to the two call sites in
  the service being changed.

- **The JWKS fetcher is dispatched by `call_maybe_async`.** `_fetch_and_cache` hand-rolled
  sync/async dispatch by calling the injected fetcher inline and testing the result -- which runs a
  synchronous fetcher *on the event loop*, the precise stall this class was made async to avoid.
  The repo has one home for that dispatch, which offloads a sync callable, and this same change
  already used it in `settings_api`.

- **A narrowed poll ceiling is reported rather than reversed.** `floor=BULK_POLL_INITIAL_SECONDS`
  silently handed back the initial interval, so an operator lowering the ceiling got the opposite
  of what they set with no indication. The invariant holds, and now says so.

- **A test that pinned formatting instead of behaviour is gone.** It regexed the inline JS for an
  exact expression, so hoisting that expression into a local would fail it with nothing changed.
  The branch logic is asserted through the router; the page test now only checks what the router
  cannot.

- **The same false-claim defect, one field over.** `PLATO_SQLITE_PATH`'s effective value went
  through `display_path`, so an absolute stored path could never equal its own resolved value and
  the panel reported it as not applied -- exactly what had just been fixed for `PLATO_DB_BACKEND`
  six lines above. Compared in the same form now, and omitted when the two agree. The router also
  drops any hint equal to the stored value, so a provider that spells a value differently cannot
  produce that claim again.

- **An unsettled probe no longer serialises the batch.** `_probe_v2` is documented as running once
  under a lock, and that held only when a probe *settled* the flag. It cannot settle when neither
  route has the document -- a stale KG reference, a deleted document -- so every document took the
  lock in turn and a ten-at-a-time batch ran at peak concurrency 1. Whether a probe has run is now
  recorded separately from what it concluded.

- **`env_int` reaches the rest of the estate.** Six queue knobs and two launcher knobs still did
  `int(env(...))` / `int(os.getenv(...))`, which is the empty-string hazard the helper was
  introduced for -- converted in `agent_hooks` and not in its siblings.

- **A manifest recorded under the previous default scope is adopted.** The default moved from the
  output directory to the collection id; `DbMaterializeManifestStore` keys its rows on the scope,
  so those rows were addressed by the old key and invisible under the new one. The file store had
  a flat-map bridge and this had none, so an upgrade cost one re-download of everything.
  `materialize` reads the old key once when the new one is empty and re-saves under the new one.

- **Two tests said less than they looked like.** Both `test_a_document_the_listing_cannot_identify`
  and the legacy-document test built a client and immediately rebound the name to a subclass, so
  the setup between them mutated a discarded object. And the dashboard assertion checked only that
  `f.effective` and "in effect" appeared in the page -- it would have passed with the comparison
  inverted, which is the defect above it. It now asserts the rendered guard.

- **The collection listing now implements the cost model it documents.** `list_probe_threshold`'s
  comment states it -- the listing's cost is the size of the *collection*, the per-document cost is
  the size of the *request* -- and the gate only ever read the request. Six documents out of a
  thirty-thousand-document collection therefore walked the full page ceiling, identified none of
  them, logged a WARNING every run, and then made the six metadata calls it was meant to replace:
  strictly worse than not listing at all. The walk now carries a budget of one page per requested
  document, so it can never spend more calls than the alternative would, and giving up is logged
  as the cost model working rather than as a fault.

- **The configuration panel stopped contradicting itself about the database backend.**
  `effective_settings` reported SQLAlchemy's drivername while the field's vocabulary is
  `sqlite`/`common`, so the two could never be equal and the page took its "differs from stored"
  branch every time: `in effect: postgresql+asyncpg (the stored value is not applied)` when it was
  applied. It now answers in the field's own terms.

- **A document legitimately named `Report (2).pdf` is attributed from a bulk archive.** The
  collision matcher claimed any basename ending ` (N)`, so a real filename of that shape was read
  as one KH had renamed and re-fetched individually on every run. A rename is only a rename when
  the un-suffixed name is another wanted document, which is now the test.

- **`span_text_max_chars` reads through `env_int`,** rather than hand-rolling the same
  empty/unparseable/floor contract the helper had just been introduced for -- and which
  `effective_settings` calls it to obtain. `KnowledgeHubUnsupportedError` is exported from
  `jazzx_sdk.clients` beside its siblings: it is the one new error whose documented purpose is for
  a caller to branch on, and it was the one not exported.

- **Two smaller corrections.** A malformed document id in a bulk request raised a bare
  `ValueError` from above the `try`, out of a method whose every other failure is a logged `None`.
  And four `getattr(self._config, ..., <literal>)` fallbacks were dead branches -- `__init__`
  always builds a `FabricConfig` -- one of which carried a literal contradicting the real default
  (`0`, bulk off, against the field's `25`).

- **A bulk task whose status call fails no longer polls out the window.** The generated
  `asyncio_detailed` does not raise on an error response, so a 404 (the task record expired) or a
  500 arrived as `parsed is None` -- read as an unknown state, which this code deliberately treats
  as "still running", it polled the full patience window before the caller could fall back. Five
  minutes by default, and the test for it took 30 seconds to fail against the old behaviour.
  `BULK_POLL_TIMEOUT_SECONDS` is also floored now, the one member of that family read without one:
  at zero or below, `_await_task` gave up after a single status call and bulk was silently off for
  every caller that did not pass `timeout_seconds` itself.

- **A `NullMaterializeManifestStore` spends no identifying calls again,** which is the whole
  contract of that store. The listing had been gated on set size alone, so a large set walked the
  collection for a store that cannot skip a single download -- and populated `page_count` where
  the field's own comment said it would be `None`.

  Fixing that naively coupled two callers that want the listing for different reasons: the probe
  wants digests, and the bulk path wants the names it attributes archive members with, which is
  worth the walk whatever the manifest store is. Three tests caught it. Both are asked now, and
  `unique_ids` bounds `to_download` from above so a set too small for bulk cannot claim to need
  it.

- **A denial is not retried per document.** `retry_async` owns which exceptions retry via
  `retryable=`, and the rule was stated only in the handler above it -- so a 403 burned the full
  exponential backoff for every document before the re-raise could surface it. One kwarg, in the
  place that decides.

- **The dashboard no longer reports a Postgres database name as the SQLite path.**
  `PLATO_SQLITE_PATH`'s effective value came from `url.database` for every backend, and that field
  is labelled "sqlite backend only". The driver name was already being read one line above.

- **Two smaller corrections.** The dead `if not worth_listing: unresolved = ...` assignment is
  gone -- the comprehension above already yielded every id in that case. The configuration panel's
  "(overridden below)" pointed at nothing below it and reversed the meaning: when the stored value
  differs from the effective one, the stored value is the one *not* applied. And the mock's
  `download_document_v2` ignored `collection_id`, answering for a document that lives in another
  collection where the real route 404s.

- **Numeric environment variables get one guarded reader.** `envvars.env_number` /
  `env_int` now handle the three ways an env-configured number goes wrong -- unset, empty, and
  unparseable -- in the module that documents the empty-string hazard in the first place. Two
  defects closed with it:

  `FabricConfig`'s four new int knobs did `int(env(...) or N)` unguarded, and they are its only
  int env fields, so `JAPES_KH_LIST_PAGE_SIZE=none` raised out of `default_factory` and *no*
  `FabricConfig` could be constructed at all. The `_seconds` helper added in the same change
  guarded exactly this for its own knobs and the config siblings did not get it -- so the helper
  is gone and both read the shared one.

  And the floor was applied only on the parse path, so it did not hold when the variable was
  merely unset: `JAPES_KH_BULK_POLL_INITIAL_SECONDS=10` against a defaulted ceiling gave
  `initial=10, max=5`, and `min(delay, MAX, remaining)` silently discarded the configured
  interval. The floor now applies to the answer.

- **A bulk job is not started without the names to attribute it.** `bulk_download_threshold` and
  `list_probe_threshold` are set independently, so a bulk threshold below the probe threshold is
  reachable by configuration alone -- and there the job ran, attributed nothing (KH names members
  after the document, and no listing means no names), latched `_bulk_available=True`, and every
  document was fetched individually anyway. Every call, with one INFO line.

- **Every task's exception is retrieved when a document is denied.** `_fetch` was given a
  `KnowledgeHubAccessError` re-raise inside a bare `asyncio.gather`, which surfaces the first and
  leaves the siblings running unawaited -- each then reporting "Task exception was never
  retrieved" for the identical 403, with nothing able to catch it. Outcomes are collected first,
  then one is raised.

- **`page_count`'s comment is honest.** It said "None elsewhere and where KH has not computed it",
  but it only ever comes from the probe or the listing -- so a `NullMaterializeManifestStore`,
  which exists to spend no calls, leaves it `None` for a PDF that does have one. Stated rather
  than papered over: spending calls to fill a field would contradict that store's whole contract.

- **The bulk user-id guard is shared, not copied.** The mock had a verbatim duplicate of the
  client's `_current_user_id` and its three-line message; both now come from one module-level
  helper and one constant, so the guard that decides whether a bulk download is attempted cannot
  drift between them.

- **The v2 entity comment is back above its own flag,** having been stranded ~70 lines up by the
  bulk and download blocks inserted beneath it -- where it read as documenting
  `KH_V2_BULK_AVAILABLE`.

- **An empty duration variable no longer breaks the import.** `float(os.getenv(NAME, "300"))`
  runs at module scope, and `os.getenv`'s default covers *unset*, not *empty* -- so
  `JAPES_KH_BULK_TIMEOUT_SECONDS=` (a compose file or configmap entry with no value) raised
  `ValueError` and took the whole `jazzx_sdk.clients` package down. `jazzx_sdk.config.envvars.env`
  documents this exact hazard, which is why the fabric knobs in the same change read
  `env(...) or <default>`. All three durations now go through one helper that treats empty and
  unparseable alike: default, with a warning.

- **The collection listing has to earn its place.** It was made unconditional on the reasoning
  that it is "a single call". It is a paginated walk, and its worst case is a requested id no
  longer in the collection: neither of the loop's exits ("a short page", "found everything asked
  for") fires, so one stale KG entity walks the whole collection to conclude what a single
  metadata call answers with a 404. The listing's cost is the size of the *collection* and the
  per-document cost is the size of the *request*, so `list_probe_threshold` (default 5) decides
  between them -- and below it the metadata call answers the digest and the page count together
  anyway.

- **`bulk_download_threshold` is floored,** like the two paging fields twelve lines below it.
  At `-1` the value stayed truthy and `len(to_download) >= -1` was always true, so every
  `materialize` took the bulk path -- a one-document one included, and a queue job with no
  identity header for it to use.

- **A denied listing is not an empty collection.** `_bulk_fetch` and `_fetch` were each given an
  explicit `KnowledgeHubAccessError` re-raise; `_collection_metadata`, the third new call site on
  the same path, still swallowed it. The import is hoisted to module scope now rather than
  repeated in three function bodies.

- **Two smaller corrections.** The mock's access response read `mime_type`, a key the mock never
  writes (`create_document` stores `content_type`), unobservable only because that value is
  currently hardcoded. And `plato/oidc.py`'s docstring justified the async conversion with a
  middleware that does not exist yet -- the reasoning is sound as a choice made while the shape is
  still free to change, which is what it now says.

- **A denied per-document download is no longer an empty result.** `_bulk_fetch` was given a
  `KnowledgeHubAccessError` re-raise last round and `_fetch` was left swallowing the identical
  error three hundred lines below -- so below the bulk threshold, or with it set to 0 (a
  documented setting), a caller with no grant on the collection got `materialize` returning
  nothing but warnings. The comment justifying the bulk re-raise named this exact path.

- **A hub without the bulk route is asked once.** The single-document route latches
  `_v2_download`; the bulk route caught bare `Exception` and re-probed on every call, so a v1-only
  hub paid a doomed trigger round trip per `materialize`. It now classifies with the same
  `_v2_unsupported` predicate and latches `_bulk_available`, which is what
  `KnowledgeHubUnsupportedError`'s own docstring exists to allow.

- **The mock requires a user id for a bulk download, like the real route.** It ignored `user_id`
  entirely while the same mock had just been given the empty-selection refusal on the stated
  grounds that a mock must not pass where production fails -- and the identity requirement is the
  one that bites in a queue job, where no inbound request supplies one.

- **Computed fields are read from the listing row as well as from `meta_data`.** KH writes
  `sha256`/`page_count` into the `meta_data` column on upload and on backfill, so the bag is where
  a listing row carries them -- confirmed in Knowledge Hub's own source, against a review finding
  that read the generated model's declared fields and concluded otherwise. But
  `DocumentMetadataResponse` shows KH also has a shape that carries them flat, and an unknown
  top-level key lands in the row's `additional_properties`, so both are read now. Breadth rather
  than a fix, and one line.

- **Two orphaned comments reunited with what they describe,** both left behind by insertions in
  this same change: the listing-page note above a class it no longer applied to, and the
  single-document flag's note above the bulk flag.

- **A legacy document gets its metadata call again.** `_doc_hash_from_metadata` falls back to
  `updated_at`, and every listing row carries one -- so a document with no computed `sha256` still
  produced a truthy digest, `unresolved` was always empty, and the metadata call that is the only
  thing which backfills `sha256` and `page_count` was never made. The documented fallback was
  unreachable, and the tell was in this diff's own test, which had to strip `updated_at` from a
  synthetic listing to reach the branch. The fallback now fires on a digest that is not a
  `sha256:`, not on the absence of one.

- **The default manifest scope is the collection, as `sync_collection` always had it.** It was the
  output directory as the caller spelled it, which was harmless while the manifest was one flat
  map and is not now that storage is partitioned by that key: the same directory reached
  relatively on one run and absolutely on the next, or a volume mounted at two paths, is a
  different scope with nothing in it, so the whole set re-downloads.

- **A denied bulk download is no longer reported as an unavailable one.** `_bulk_fetch`'s blanket
  handler caught `KnowledgeHubAccessError`, which every `except Exception` in the client is
  careful to re-raise -- so a 403 for the forwarded `x-user-id` logged "bulk download
  unavailable", downgraded to per-document, and the identical denial there exhausted the retries
  and dropped the documents with only warnings.

- **`meta_data` cannot override the row it rides on.** Spread after `name` and `updated_at`, a
  document whose uploader stored either key in that free-form bag would drive archive member
  attribution and the change probe with it.

- **The listing knobs live in `FabricConfig`,** beside `bulk_download_threshold`, rather than as
  module-level `os.getenv` globals added in the same change. They can now be set per fabric, and
  the test for the zero-page-size floor no longer needs `importlib.reload`.

- **The mock refuses an empty document selection like the real client.** It still built a valid
  empty archive for `[]`, and the new mock bulk route delegated to it -- a mock a test passes
  against and production does not.

- **`"[::1]"` dropped from the OIDC loopback set:** `urlsplit` strips the brackets, so the entry
  could never match and `"::1"` already covered it.

- **The configuration panel reports what the replica resolved, not just what is stored.** Blank
  fields, including `JAPES_ENVIRONMENT` on a replica whose `/info` said `local`. The page was
  accurate and useless: those variables are genuinely unset, and the values come from defaults or
  from the wiring. The posture keys default when absent, the span cap has its own default, and the
  local wiring hands the database backend and path to `DbStore` in code -- so the two read-only
  posture fields, on the page precisely to show what the replica decided, showed nothing.

  `SettingField` gains an `effective` value and `create_settings_router` an optional provider for
  it; Plato resolves the posture, the span cap and the live database URL. The page renders it as
  the field's placeholder plus an "in effect" line, marked `(default)` or `(overridden below)` so
  a stored value is never confused with a resolved one.

  Never populated for a secret: masking `value` is pointless if the same string is reported under
  another name, and the router drops the hint rather than trusting each provider to remember. A
  provider that raises is logged and omitted -- a hint is not worth failing the panel for.

- **The bulk poll intervals are floored, like the listing knobs already were.**
  `JAPES_KH_BULK_POLL_INITIAL_SECONDS=0` left the backoff at zero forever (`0 * 2` is still zero)
  and `sleep(0)` returns at once, so the poll became a tight loop against KH for the whole
  patience window -- thousands of status calls for one archive. `JAPES_KH_BULK_POLL_MAX_SECONDS=0`
  did the same from the other side, pinning every sleep to zero whatever the initial value was.
  `_LIST_PAGE_SIZE` and `_LIST_MAX_PAGES` were already floored against exactly this input class,
  which is what made the omission a real inconsistency rather than a hypothetical one.

- **`KnowledgeHubUnsupportedError` reaches the whole optional-binding family.** It was introduced
  for the v2 download routes while `create_entity_v2` and `read_entities_v2` -- the precedent the
  new code's own comment cites -- still raised a bare `KnowledgeHubError` for the identical
  "this client pin lacks the binding" condition, so a caller could downgrade permanently on one
  and not the others.

- **Smaller corrections from the same review.** The per-call `manifest_store` is typed against
  `MaterializeManifestStore` rather than `Any`, which matters because `materialize` compares it
  against `NullMaterializeManifestStore` to decide whether to probe at all. `_bulk_fetch` takes
  the listing as a required argument, since the only caller always supplied it and the optional
  branch could never run. `AttributeError` no longer counts as "this hub has no v2": `hasattr`
  already covers the absent method, so the only ones left come from inside the client and would
  have downgraded the store while hiding themselves.

- **Only one document probes the v2 route.** The comment claimed the probe "costs one call rather
  than one per document", but `materialize` runs documents concurrently and the flag is read per
  coroutine -- so on a hub with no v2 route, up to `concurrency` documents each paid a doomed call
  before any of them wrote the answer. The probe now happens once under a lock, and lives in its
  own `_probe_v2` rather than as a branch inside the download path.

- **`download_document_v2` reports absence and failure differently (PR review).** It returned
  `None` for everything: a 404, a non-200 access call, an expired or refused signed URL, an
  unreachable blob host. On a hub already proven to serve v2, one 403 mid-batch therefore looked
  exactly like a missing document -- `materialize` dropped it from the result, and `retry_async`
  never saw it, because it only retries a raise. Now `None` means 404 and nothing else; every
  other failure raises. `KnowledgeHubUnsupportedError` separates "this pin or hub has no v2 route"
  (downgrade permanently) from "this call failed" (retry), which were the same type. `materialize`
  keeps the probe fallback on `None`, because a hub with no v2 route 404s it exactly as a missing
  document does -- that one ambiguity is real and unavoidable, and it is now the only one.

  A transient v2 failure also no longer downgrades the rest of the batch: the blanket handler
  flipped `_v2_download` False for the life of the store, so a single `ConnectError` sent every
  later document down v1 on a hub that does serve v2.

- **An empty `document_ids` no longer downloads the whole collection.** `if document_ids else
  UNSET` mapped `[]` to `UNSET`, which the API reads as "everything", so an explicit empty
  selection archived and downloaded the entire collection. `download_documents` was cited here as
  getting it right and did not: it passed `[]` through, httpx drops an empty-list query param
  entirely, and KH's own filter is `if document_ids:` -- equally falsy -- so the server saw no
  filter and archived everything by a different route to the same place. Both refuse an empty
  selection now. An explicit `timeout_seconds=0` is also honoured rather than becoming the 300s
  default.

- **The collection listing terminates on its own.** `JAPES_KH_LIST_PAGE_SIZE=0` -- a plausible
  reading of "no paging", and the neighbouring `bulk_download_threshold` does document 0 as
  meaningful -- left `skip` unchanged with `len(batch) < page` false forever, hanging every
  `materialize` inside a `try` that cannot catch a hang. The size is floored at 1, and the loop
  now has a page ceiling (`JAPES_KH_LIST_MAX_PAGES`) so it does not depend on the hub returning a
  short page: a hub answering full pages of documents nobody asked about satisfied neither exit
  condition.

- **The bulk path stopped listing the collection twice.** `_bulk_fetch` re-fetched the listing
  `materialize` already held for exactly those ids -- on the bulk path, which is the large
  collection by definition, that doubled the full paginated walk. It also now guards
  `download_document_v2` with `hasattr` the way it always guarded `bulk_download_documents`, so an
  older client's `AttributeError` reaches the feature check rather than the blanket handler.

- **One fabric can keep more than one manifest.** `FileMaterializeManifestStore` accepted `scope`
  and ignored it, on the reasoning that one directory needs one manifest. The reason first given
  here was wrong and is corrected: the two runs did *not* overwrite each other, because
  `materialize` loads the map, updates only its own doc ids and saves the union. What the flat
  file did not give is isolation -- every scope read every other scope's entries, and
  `DbMaterializeManifestStore` partitioned where this did not, so the two stores answered the same
  question differently. The file is now
  partitioned by scope, as the DB store always was, and `materialize()`/`sync_collection()` also
  take a `manifest_store` per call for when the two should not share a file at all. A manifest
  written by the previous version is kept as a fallback for any scope that has not written yet, so
  the upgrade does not cost one re-download of everything per scope.

- **The change probe is one call per collection, not one per document.** It made a
  `get_document_metadata` request for every unique document. KH's `listDocuments` returns
  `meta_data` -- a free-form bag where its upload pipeline stores `sha256` and `page_count`,
  verified to survive the generated model's `to_dict()` -- along with `updated_at` and `name`, for
  every document in the collection. One paginated listing now answers
  the probe, the page count and the bulk archive's member attribution together. Only a document
  the listing cannot identify still costs its own call: `sha256` is absent until KH's metadata
  endpoint backfills a legacy upload, and only that endpoint does the backfill.

- **`MaterializedDoc.page_count`.** From the same listing, so it costs nothing extra. `None` for
  non-PDFs and for a document whose count KH has not computed, which is what KH itself reports.

- **Bulk download, and fabric choosing between the two routes.** `bulk_download_documents`
  drives KH's v2 job: trigger, poll to a terminal state, ask for the link, fetch the archive from
  storage. Backed-off polling with a cap (`JAPES_KH_BULK_TIMEOUT_SECONDS`,
  `JAPES_KH_BULK_POLL_INITIAL_SECONDS`, `JAPES_KH_BULK_POLL_MAX_SECONDS`). An unrecognised task
  state counts as still running: guessing "done" loses the archive and guessing "failed" abandons
  a job that would have succeeded, so the timeout is what ends it.

  **Bulk is not simply better, which is why fabric picks.** `materialize` uses one archive at or
  above `bulk_download_threshold` (default 25, `JAPES_KH_BULK_THRESHOLD`, 0 disables) and the
  per-document route below it. Three round trips plus an archive build cost more than a handful of
  documents' bytes. More decisively, **the bulk route requires an `x-user-id` header and the
  per-document route does not** -- it is the subject KH authorizes against, so bulk is unavailable
  in a queue job or anywhere else with no inbound request, which is where a batch download looks
  most attractive. Rather than send an empty header, the method raises and names the alternative;
  `materialize` treats that as a fallback, never an error, because per-document already works.

  **Archive members are attributed, not assumed.** KH names them after the document, not its id,
  so fabric resolves `{doc_id: name}` in one `list_documents` call and matches on that, with the
  id as a second chance. Anything ambiguous is deliberately left out and fetched individually:
  two documents sharing a name would otherwise write one document's bytes to the other's file,
  which is silently wrong content and worse than a slower download. A partial archive tops up
  per document; a response that is not an archive falls back whole.

  Member naming is now read from Knowledge Hub's own source rather than inferred:
  `sanitize_string(doc.name)`, with a repeated name broken by an appended ` (1)`, ` (2)` in
  whatever order KH iterates the documents. That order is not reproducible from here, so a
  suffixed member is never attributed -- it is detected and fetched individually. Matching also
  tries an ASCII-normalized form, because the sanitizer strips non-ASCII. KH skips a document it
  cannot read rather than failing the archive, which confirms a partial archive as a normal case
  the top-up path already covers. The task-state vocabulary is still read from the generated
  client, which is why an unknown state waits rather than deciding.

- **`download_document_v2`: one document over the v2 signed-URL path.** The v1 route has KH read
  the blob, build a one-member ZIP around it and stream that back through the service, so
  `fabric.docs.materialize`'s per-document loop paid compression and a proxy hop on every
  document. v2 answers with a short JSON access response and the bytes come straight from storage.
  The generated client already carried the bindings and japes was not calling them.

  `access_only=True` returns that response (`url`, `expires_at`, `file_name`, `content_type`,
  `size`, `disposition`) without fetching the blob, for a caller that can hand the URL to a
  browser and never move the bytes through this process.

  The signed URL is fetched with a bare client, deliberately: it carries its own authorization,
  and reusing the configured one would send the Knowledge Hub bearer token and the identity
  headers its hook injects to the storage host. A test asserts that, and fails if the configured
  client is used.

  `materialize` prefers v2 and falls back to v1, because a deployment may not serve v2 yet. The
  fallback is not just an exception guard: `download_document_v2` reports failure as `None` rather
  than raising, and a v1-only deployment 404s the v2 route exactly as a missing document would --
  so while probing, whichever route answers settles it, and once v2 has worked a `None` means the
  document is genuinely absent rather than costing a wasted v1 round trip per miss. Available on
  the same terms as the v2 entity API: an older client pin loses this method and nothing else.

- **A degraded replica no longer serves its log buffer to anyone who can reach the port.** The
  fallback app is a bare `FastAPI` with no identity middleware, and it is exactly where an
  unresolvable `PLATO_WIRING` lands in a deployed environment -- so an unauthenticated caller could
  read every buffered record. Log records are content, not counters, so a deployed posture now
  withholds them unless the deployment passed an `auth` dependency, which is the same shape
  `create_config_router` uses for writes. The panel shows the reason instead of the records.
  `boot_contract.py` claimed the degraded surface was "`/info` alone ... strictly smaller than a
  gated app"; it has not been that since the diagnostics were added, and the row now says what is
  actually served.

- **The guide ships.** `_GUIDE` pointed at `docs/PLATO.md`, and `docs/` is copied into neither the
  image nor a wheel -- so `/docs` and `/redoc` served "The guide is not present in this image" in
  every artifact except a source checkout, while the nav still linked to it. The file moved to
  `plato/guide.md`, beside the module. Verified by building the wheel: it carries the guide, the
  alembic ini, the migration tree and the dashboard.

- **`create_feedback_router` follows `API_V1_PREFIX`.** It is the one router a consumer constructs
  itself and passes through `extra_routes`, so its static default left feedback on `/api/v1` while
  every route `create_plato_app` built moved.

- **The local boot output names a path that exists.** Both branches printed `/v1/info`, which has
  404'd since the prefix moved; the same stale path survived in the boot contract, the wiring
  docstring and the feedback module docstring.

- **A test fixture stopped evicting third-party modules.** `tests/test_plato_wiring.py` deleted
  every module imported during a test, to clean up the fake wiring modules it installs. Importing
  `plato.wiring_local` pulls in `sqlalchemy.orm` for the first time, so that got deleted while
  `sqlalchemy.inspection` survived, and a later test failed with `Type <class 'object'> is already
  registered`. The full suite passed only because something earlier happened to import
  `sqlalchemy.orm` first. The fixture now drops only the `plato_test_*` modules it created.

- **`logger.exception(...)` reaches the log panel with its traceback.** Only `getMessage()` was
  kept, so the call an operator opens that panel to read arrived as its least informative line.
  Redacted and tail-trimmed like the message, and rendered under it in the same cell.

- **`?limit=0` returns no records.** `max(1, min(limit, maxlen))` handed back one to a caller who
  asked for none.

- **A trailing slash in `API_V1_PREFIX` no longer takes the replica down.** FastAPI asserts a
  router prefix starts with `/` and does not end with one, and it asserts while the app is being
  built -- so `API_V1_PREFIX=/api/v1/` raised in `create_plato_app`, `run_role` fell back to the
  info-only app, and that raised the same assertion: the container exited on a traceback,
  contradicting both the "a serving role always comes up" contract and the promise that setting
  the variable moves the routes. `api_prefix()` now normalizes, so `api/v1`, `/api/v1/` and
  `//api//` all resolve to something a router accepts.

- **Flex is asked for only where it exists.** `vision_flex=True` prefixed `flex_` onto whatever
  model was resolved, and only the OpenAI provider strips that alias -- so on
  `JAPES_LLM_PROVIDER=anthropic` it reached `messages.create()` as part of the model name and
  would have 400'd on the first call. The eligibility rule existed as a set in a test file, which
  is why nothing in the library could apply it; it now lives in `llm.model_identity` as
  `FLEX_ELIGIBLE` and `supports_flex()`, and the test imports it rather than keeping a copy that
  could drift while both looked green.

- **An unconfigured deployment names no vision model at all.** `vision_model_for` was annotated
  `-> str | None` and documented as returning `None` when the runner's own default already reads
  images, but it could never return `None`: `resolve_model()` always answers, falling back to the
  global default. So an `AgentExecutionService(default_provider="anthropic")` passed as `agents=`
  got an OpenAI model pinned onto it, and `agents.run` infers the provider from an explicit model
  name -- the override the docstring said it avoided. It now returns `None` unless the caller
  named a model or the environment named a provider or model.

- **`./scripts/plato-local.sh --help` prints the header, and stops there.** The usage branch had a
  hardcoded line range that ran four lines past it, presenting `set -uo pipefail` and a `cd` as
  usage. It now reads to the first line that is not a comment, so the text cannot drift from the
  header again.

- **`GET {prefix}/database?count_rows=false` reports `truncated`** like the counting path, so a
  consumer tests the field rather than its absence.

- **A markdown table needs a real separator.** `set(line) <= set("|-: ")` is satisfied by a blank
  line, so a lone `|`-prefixed row followed by one rendered an empty `<table>`. Not reachable from
  the current guide, only from a future edit to it.

- **The tool-span output shape is pinned.** It changed from a bare string to `{"text": ...}` when
  the cap became configurable, and nothing recorded that, so a span reader treating the field as
  text would have found a mapping.

- **A degraded replica serves `/info` where a healthy one would.** The fallback app mounted every
  router on the static constant while `create_plato_app` resolved through `api_prefix()`, so with
  `API_V1_PREFIX` set the two disagreed -- and an operator probing the configured path during a
  wiring failure would have got a 404, which reads as "the process never started" rather than "it
  started and cannot serve". That is the exact drift the comment removed in the previous change
  had warned about, reintroduced by making only one side configurable. The app is now built by
  `_info_only_app`, separately from serving it, which is also what lets the boot-contract tests
  assert on real routes instead of grepping the function's source.

- **`/redoc` is served, not left blank.** `/docs` was fixed by dropping FastAPI's CDN page; its
  sibling was left in place under the same `default-src 'none'`, so it returned 200 with
  `cdn.jsdelivr.net` assets and rendered nothing. Both now serve the guide.

- **The guide's routes table follows the prefix.** `guide_html` substituted the nav and left the
  table on `/api/v1`, so a moved deployment read a page that contradicted itself. The substitution
  now runs over the body, and the file keeps the default prefix on disk so it still reads correctly
  in the repository. The logs row also said "the last 500 log records" where the endpoint returns
  200 per request from a 500-record buffer.

- **The local wiring no longer writes into `site-packages`.** `parents[1]` is the repo root in a
  source or editable checkout and `site-packages` from a wheel, which is where the sqlite file,
  the pack cache and alembic's working directory would have gone -- and the stated reason for
  moving this module into the package was precisely that it should work when installed. The root
  is now the checkout when it looks like one, and otherwise `PLATO_LOCAL_ROOT` or the working
  directory. Alembic is pointed at the ini by absolute path, since `script_location` is relative
  to the ini itself.

- **A second `attach_log_buffer` applies what it asked for.** The call was gated on "already
  attached", and `run_role` attaches with defaults before `create_plato_app` attaches again, so a
  non-default capacity was unreachable in the serving path. There is still one handler; a resize
  keeps the records already buffered.

- **Reviewed and rejected: the Fable 5.1 cache rate.** `cached_input: 0.25` against `input: 10.0`
  is 0.025x where every other Claude model is 0.1x, which reads as a missing digit. It is not: the
  pricing page footnotes Fable 5.1 and Mythos 5.1 as the documented exception. The row's
  provenance note now says so, so the next reader has the answer without re-deriving it from the
  ratio.

- **Reviewed and rejected: the metrics middleware's `500` seed.** Reported as counting a dropped
  SSE stream as a server error. A mid-stream disconnect does not reach that path -- `call_next`
  returns the response before the body streams, so the recorded status is the response's own 200.
  The seed covers an unhandled handler error, which does arrive as a raise because this middleware
  sits inside `ServerErrorMiddleware` and outside `ExceptionMiddleware`, and 500 is correct there.
  Changing it to a client-error code was tried and dropped real failures out of the error count. A
  test now pins both halves.

- **The vision flex tier is a model alias, not a provider argument.** `classify_page_images` and
  `split_document` took a `service_tier` string and passed it to the provider verbatim, where
  OpenAI accepts only `auto`/`default`/`flex`/`priority` -- so the default `"standard"` was an
  invalid value, and it also suppressed japes' own flex translation, which is guarded on
  `service_tier` being absent. Asking for flex therefore disabled it. Flex is now expressed as the
  `flex_` model prefix that `parse_model_tier` already strips, which is the one mechanism japes
  owns end to end.

- **The vision default no longer overrides the deployment's provider.** A hardcoded
  `gpt-5.6-luna` meant a deployment on `JAPES_LLM_PROVIDER=anthropic`, holding only an Anthropic
  key, was routed to OpenAI for page classification and failed on a call that used to work.
  `vision_model_for()` keeps the configured default whenever its card says it reads images, and
  substitutes only for a text-only default. An uncarded model is left alone: it may well have
  vision, and swapping it on a guess is the override being fixed.

- **One missing table no longer hides every later row count.** The database panel counted all
  tables in a single session; postgres aborts the whole transaction on the first failed statement,
  so the alphabetically-first table the migration had not created turned every subsequent count
  into `PendingRollbackError` -- in exactly the degraded-schema state `/info` exists to report. A
  session per table now. Every table failing is reported as one connection problem rather than as
  many table problems.

- **`API_V1_PREFIX` moves the routes, as the guide already claimed.** `api_prefix()` was written
  and exported and then never called, so `create_plato_app` used the constant and the environment
  variable did nothing. The prefix now resolves through it when the caller passes none, an explicit
  argument still wins, and the page links follow. `docs/DEPLOYMENT_ENV.md` said Plato served `/v1`
  and that the variable was read by nothing; both were true until 2.5.0 and are corrected.

- **The default model moves to `flex_gpt-5.6-luna` and `claude-sonnet-5`.** Both are newer and
  cheaper than what they replaced: for 1M input and 100k output, $0.58 against $7.25 on OpenAI and
  $3.00 against $4.50 on Anthropic. The `flex_` prefix is kept, so OpenAI calls stay on the
  cost-optimized tier as they already were. `split_document` takes `vision_flex` to opt a page
  split into flex -- throughput-bound work, where the `429 Resource Unavailable` flex returns is a
  normal outcome the llm tier already falls back from. Two tests hold the line: every provider
  default must be carded, and a future bump must not silently make the default more expensive.

- **Claude Fable 5.1 is carded**: 1M context, 128K output, vision and tools, `$10/$50`, and cache
  reads at `$0.25/MTok` -- a quarter of Fable 5's, which is the headline change. Its provenance
  records the retrieval time, not just the date: vendor pages move during a day. Note that forced
  tool use returns an error on this model, unlike Fable 5.

- **What a span retains is capped, and the cap is configurable.** Tool spans truncated at a bare
  `1000` characters and LLM spans recorded no output at all, so the larger of the two was the one
  not covered. Both now use `JAPES_SPAN_TEXT_MAX_CHARS` (default 4000, editable from the
  dashboard), and a truncated output carries its `raw_length` -- a cut 40KB answer and a short one
  look identical otherwise, and the difference is usually what the reader is chasing. An LLM
  summary also keeps `output_types` and `status` whole, which is what separates "the model refused"
  from "the model answered and we cut it". A bad value falls back rather than raising: tracing must
  never fail the run it is tracing.

- **Commits are shown short.** A 40-character hash wraps onto a second line in the Build card;
  12 identify a commit uniquely in a repository this size, and the full value stays on the tooltip.

- **`common` reports its commit instead of "installed (unversioned)".** It is a submodule whose
  packaging version has not moved in a long time, so the old string said something was installed
  and nothing about which. Fixing it surfaced that `build_info()` ran twice per `/info` request,
  shelling out to git each time in a working tree; it now runs once.

- **Plato serves a dashboard at `/`, and the pages it serves now actually run.** Seven panels over
  the JSON APIs -- deployment tier, versions, schema revision, database tables and row counts,
  request counters, recent logs, configuration -- refreshing every 10s and pausing when the tab is
  hidden, so a dashboard left open does not keep counting itself in the metrics it displays.

  **The pages were dead in a browser, including the `/info/ui` that already shipped.** The API's
  `default-src 'none'` blocks a self-contained page's own inline `<style>` and `<script>`, so a
  browser rendered the labels as unstyled text and ran nothing. `security_headers.page_csp()` is
  the policy for a single-file page; the middleware already used `setdefault` for exactly this, and
  the JSON API keeps the strict default. `spa_csp` does not fit: its `script-src 'self'` permits a
  *file* and still blocks an inline script.

  Three new read-only routes back the panels. `{prefix}/logs` is a bounded ring buffer (500
  records) on the root logger, redacted through `redact_secrets` -- a connection string logged once
  would otherwise sit in memory and be served to whoever opens the page -- and it reports the
  effective log level, so an empty panel reads as "nothing logged at WARNING" rather than as a
  broken capture. `{prefix}/metrics` counts requests per route *template*, never the raw path,
  because per-id keys grow without bound; an unmatched request collapses to one key so a scanner
  cannot mint one per URL. `{prefix}/database` reports backend, host and per-table row counts, and
  never the DSN, which carries the password.

  Logs, metrics and the dashboard are served on the degraded path too. A replica that could not
  build an app now shows what it is and the boot warning explaining why, which is when an operator
  most needs both.

  **The configuration panel writes.** Fields render from the catalogue with the right input type,
  and Save posts to the `PATCH {prefix}/config` that already validates, persists and re-wires -- so
  the posture gate stays on the endpoint rather than being re-implemented in a page. Two details
  are load-bearing: only changed fields are sent, because posting the whole form would rewrite a
  field another operator edited between the read and the write; and a password box still showing
  its mask is not an edit, or saving anything would overwrite every secret with the placeholder.
  `JAPES_ENVIRONMENT` and `JAPES_STRICTNESS` render disabled -- a replica must not promote or relax
  its own posture over HTTP.

  **One nav across all three pages**, defined once rather than in each file, so they cannot drift
  into three link sets. The page you are on renders as text rather than a link, and the JSON routes
  sit behind a divider -- `info` the page and `info` the JSON are the same information, and a
  reader should be able to tell which they are about to open.

  **`/docs` serves a written guide instead of a blank page.** FastAPI registers its own Swagger UI
  there first, so it won the route and then failed to load, pulling from a CDN the CSP blocks.
  Dropping that route and serving `docs/PLATO.md` makes the path useful: how to run Plato, every
  route, how configuration changes, and what a degraded replica does. Rendered by a small markdown
  function rather than a library, since a dependency in the wheel for one page is not worth it.

  **`scripts/plato-local.sh`** is `start`/`stop`/`restart`/`status`/`logs`/`run`. `start` waits for
  `/health` and tails the log if it never answers -- with a non-fatal boot, silence is the only real
  failure. `status` reports version, tier, posture, commit and anything degraded.

  **Nothing on the page names the machine it runs on.** An absolute path carries the username, and
  this page gets screenshotted, so paths are shown relative to the working directory or `~`-elided.
  Both pages carry an inline favicon, having previously generated a `/favicon.ico` 404 per load -- requests the
  metrics panel then reported as unmatched.

- **A scanned package can now be split and classified by looking at its pages.**
  `split_document(..., vision=True)` renders the pages and classifies what they show, where it
  previously raised `DocumentNotReadableError` and sent the caller to DocIntel. DocIntel returns
  text and leaves the split unsolved; this answers both in one pass.

  **The algorithm did not change, and that is the point.** `split` already windowed pages with
  overlap and voted per page weighted by confidence *and* centrality; smoothing, short-run
  absorption and family merging all operate on labels. Exactly one line coupled any of it to text
  -- how a window becomes classifier input -- so the vision route is a fork there and reaches the
  same machinery. A second implementation for images would have been the mistake.

  **A page counts as scanned when it has no text *and* carries an image.** "No text" alone is not
  enough in either direction: requiring *every* page to be blank meant `vision=True` was silently
  ignored on a combined packet with a digital cover sheet, which is the shape this route exists
  for; counting any blank page meant one genuine separator sheet rasterized an entire digital
  document and threw away a good text layer. Once one page qualifies every page is rendered, since
  a window holding images for some pages and text for others puts two kinds of evidence in one
  ballot.

  `ocr_fallback` does not also run when vision answered -- DocIntel bills per page and its text
  would be discarded -- and `max_pages` is applied before rendering rather than after, since
  rasterizing 500 pages to classify 10 is minutes of work for nothing.

  Two smaller decisions follow from what the evidence is. The filename heuristic does not run on
  the image path: it fires before any model call on the text path, but a scanned package is
  precisely where one filename covers forty pages. Bookmarks are skipped too, since labelling an
  outline segment joins its pages' text, which is empty by definition here.

- **An image reaches any provider from one neutral part.** `ImagePart` is the counterpart to
  `format_tools`: a caller builds one and the provider it reaches converts it, rather than
  hand-writing `input_image` for OpenAI, `source.base64` for Anthropic and `inline_data` for
  Gemini and picking correctly every time. Bytes are held as bytes, so a caller that read a file
  does not encode for a format it has not chosen, and the same part can go to two providers.

  `detail` is the one knob carried neutrally, because it is the one that sets tokens per page:
  OpenAI names it `detail`, Gemini `media_resolution`, and Anthropic has no equivalent.

  **Images are not the only thing that needs translating.** A Responses content list accepts
  `input_text`/`input_image`/`input_file` and nothing else, so the neutral `{"type": "text"}` block
  -- which Anthropic takes verbatim and Gemini maps -- is rejected by OpenAI. Every block of a
  list-content message is converted, so one block shape cannot go out two ways in a request.

  **Conversion happens on every path a caller actually reaches**, which took several passes to get
  right. `AgentExecutionService.run` delegates to `LLMManager` for any call without tools, so the
  llm tier needed it as much as the agent tier -- and that tier speaks Chat Completions, where an
  image is `image_url` wrapped in an object rather than Responses' flat `input_image`. Two APIs
  carrying the same idea in different shapes, so there are two translators. `OpenAIProvider.run`
  also returns from a single-message fast path, which is the *default* route for a bare
  `AgentExecutionService()`, so the conversion sits above that branch rather than below it.

  `llm.providers.local` flattens content for a text-only backend, naming an image rather than
  serialising it: base64 in a prompt is noise a model cannot read. And the request ledger records
  `{"type": "image", "media_type", "bytes"}` instead of the bytes -- `CostTracker._offload_payload`
  serialises then regex-scans what it captures, so a 40-page split would have written and scanned
  tens of megabytes nobody reads back.

  **`supports_vision` has its first reader.** It had been defined on `ModelCard` and fed from
  `model_data.json` since it was added, and nothing consulted it. An image bound for a text-only
  model now fails before the request goes out. Only a card that positively says no refuses --
  the card set is incomplete by design, and refusing everything unregistered would make vision
  unusable on any new model.

- **Message content reaching Gemini was converted in three places and each got a content list
  wrong differently.** The agent tier wrapped it in `str()` and sent the Python repr as text; the
  llm tier passed the list itself where a string belongs; the native models joined the text parts
  and dropped everything else silently. Three implementations, three wrong answers for one input.
  `llm.gemini_content` owns the conversion now, and an unknown block raises rather than vanishing.

  **The native models raise too**, which matters more than it sounds: `resolve_model` routes a
  `claude...` or `gemini...` model through `AnthropicNativeModel`/`GeminiNativeModel`, whose content
  flattening kept only blocks carrying a `text` key. Once the SDK began producing image blocks, an
  image sent through the generic provider was discarded, nothing warned, and the model answered
  plausibly from the prompt alone. Asking about a page without sending the page is worse than not
  asking.

  An empty turn still produces one empty part rather than none: a `Content` with `parts=[]` is
  rejected outright, and `{"role": "assistant", "content": ""}` is a legitimate history entry.

- **PDF pages render to a pixel budget rather than a fixed DPI.** Measured against a real loan
  corpus: US Letter at 110 DPI lands at 1.13 MP, just inside Anthropic's downscale threshold, while
  Legal at the same DPI is 1.44 MP and gets downscaled on arrival -- and that corpus is *majority*
  Legal, so a Letter-tuned DPI would have been wrong for most of it. Fitting each page to 1.15 MP
  gives every page size the most resolution that survives. PNG rather than JPEG, which is
  counterintuitive and measured: a rendered text page is mostly flat white, and PNG wins by 13 KB
  at these sizes.

- **Measured, and it inverts the premise the work was proposed on.** Vision is *not* cheaper than
  extracted text: 1.4x on OpenAI, 1.9x on Gemini, 2.7x on Anthropic, per page, on the pages where
  both routes are possible. The corpus-wide figure of 13x cheaper-for-text is an artifact -- 80% of
  those pages have no text layer, where text is not more expensive but unavailable.

  So the justification is capability, not cost. Vision is the only route that reads a scanned
  package, and it is cheaper than DocIntel while also deciding boundaries. On a readable page it
  stays the fallback. An image is a fixed cost per page and text scales with density, so a dense
  enough page does cross over -- above ~765 text tokens on OpenAI, ~1508 on Anthropic -- but that
  is a per-corpus measurement, not a default. Accuracy is not measured: a cheaper route that is
  wrong more often is not cheaper.

- **Three SWIG shutdown warnings are filtered, by exact message.** PyMuPDF's generated bindings
  define types with no `__module__`, which Python 3.12 deprecates, and the warning fires at
  interpreter shutdown so it lands after pytest's summary with nothing to attribute it to. Scoped
  to those three messages rather than a blanket `DeprecationWarning` ignore, which would hide the
  ones worth seeing -- the anthropic 1.0 migration among them.

- **The MLflow reporter addressed runs through process-global state and blocked the event loop.**
  `MlflowReporter.report` was `async def` and did every MLflow call inline: `set_experiment`,
  `start_run`, three `log_*` calls and an artifact upload, all synchronous HTTP against a tracking
  server. The `async` signature hid it, since a caller awaiting this reasonably assumes it yields.
  It now runs under `asyncio.to_thread`.

  `mlflow.start_run` keys off a *thread-local* active run, so two concurrent publishes interleaved
  into whichever entered last. Runs are now created through `MlflowClient` and addressed by explicit
  `run_id` on every call -- which `observability/backends/mlflow/tracer.py` already did, and stated
  the reason for. One module had the answer and its sibling did not.

  `create_run` has no context manager, so the run is terminated explicitly in a `finally` with
  `FINISHED`/`FAILED`; without it a failed publish leaves a run `RUNNING` forever, which reads as a
  job that never finished rather than one that failed. `experiment_run_to_mlflow` lost its one line
  of global state (`mlflow.set_experiment`) for the same reason, and `log_artifact_with_retry` now
  documents that it sleeps up to 30s and must be called off the loop.

  Its return value is checked rather than dropped: it reports exhaustion by returning `False`
  instead of raising, so a run whose results artifact never uploaded was reported `FINISHED` with
  params and metrics and no results, and the caller had no way to know.

- **Importing `jazzx_sdk` no longer imports SQLAlchemy.** `evaluation/__init__` eagerly imported the
  two DB-backed stores, which define ORM models at class-definition time, and `fabric.guidance`
  reaches them through `evaluation.prompt_registry` -- so anyone touching guidance paid for the ORM.
  They resolve through `__getattr__` now, matching the pattern `observability/__init__` already
  used. 1697 modules to 1572 on a bare import.

- **The Plato boot contract is one table, and `--health` is the readiness probe.** The policy -- a
  serving role comes up and reports, a `job:*` role refuses -- was stated as prose in eight places,
  and changing it meant finding all eight. It is data in `plato/boot_contract.py` now, the
  documentation table is rendered from it, and `tests/test_plato_boot_contract.py` holds each row to
  the code path it describes.

  Making the boot non-fatal removed the signal an orchestrator relied on, and nothing replaced it.
  `python -m plato --health` probes the container's own `/v1/health` and exits non-zero unless
  `configured` is true. `--check` cannot answer that: it parses the environment in a second process
  and never sees what this one resolved, so it is documented as a parse diagnostic, not a gate.
  `create_app` grew a `readiness_provider` hook to put the answer on `/health`, the one path the
  identity middleware exempts -- a probe against `/info` was 401'd on every strict-posture replica.

  Building the table surfaced one thing the prose had wrong. Three situations leave a replica
  serving `/info` alone, so "blocks chat" is meaningless for them: there are no chat routes to
  block. Exactly one row turns a turn into a 503.

- **Configuration written through `/v1/config` now survives a restart, and the database itself can
  be swapped at runtime.** Migration `0002_setting` adds `plato_setting`, and `DbSettingsStore`
  reads the environment overlaid with what the database holds -- the database winning, because a
  value written through the API is a later decision than the container's environment.

  **Two layers, because one is impossible.** `PLATO_DB_BACKEND`, `PLATO_SQLITE_PATH` and
  `DATABASE_URL` say *which* database the durable layer is in, so writing them into it and then
  swapping the database leaves the new value in the old one. Those stay in the environment;
  everything else persists.

  **A NULL value is not a missing row.** Writing an empty value persists "explicitly unset", which
  has to survive a restart or the environment's value silently returns. `forget()` drops the row
  instead, so the deployment's own configuration applies again. Both intentions come up.

  **`tenant_id` on a deployment-wide table.** `plato.tenancy` requires it in every table's key, and
  the rule earns its bluntness -- the table exempted "because it is not tenant data" is the one that
  later holds some. Deployment-wide rows carry the reserved `_platform` id, the same answer
  `PLATO_PACK_TABLE_DESIGN.md` reached for shared packs, and per-tenant settings stay possible
  without a migration.

  **The live database swap.** `DbStore.dispose()` marks a store permanently dead, so a swap cannot
  mutate one in place: `DatabaseHandle` holds the current store behind a single reference every
  per-tenant store resolves through, and the caches are keyed on the store they were built against
  so a swap cannot hand back one bound to the retired engine. The replacement is built and its
  tables created *before* the swap, so an unreachable database leaves the running one in place.

  In-flight requests finish against the old database. Nothing can know when the last session on the
  retired engine closes, so it is kept referenced rather than disposed -- disposing immediately
  fails a request that was already mid-flight and did nothing wrong. Only reachable in a relaxed
  posture, since that is where config writes are, which is also why `create_all()` is acceptable
  there rather than the alembic chain.

  Durable settings are exported into the environment at boot, before the wiring resolves anything:
  a setting written yesterday is only durable if something reads it back, and every consumer of it
  reads the environment. Never fatal -- a replica that cannot reach its settings table starts on
  its environment, degraded and saying so.

- **Plato serves its own configuration at `/v1/config`, and a relaxed replica can be fixed over
  HTTP without a redeploy.** Most of this already existed and nothing mounted it:
  `jazzx_sdk.server.settings_api` does masking, unknown- and non-editable-key rejection,
  `If-Match` concurrency and audit. Plato now supplies the catalogue its wiring actually reads --
  and no more, because a field nothing reads is a control that appears to work.

  **`SettingsStore` accepts async implementations.** It was a sync protocol, which quietly ruled
  out every store a deployment wants: `fabric.db` is async-only, so a database-backed store could
  only have honoured a sync `read` by calling `asyncio.run` on the loop already running the
  request, which raises. The router awaits either through `call_maybe_async`, so existing sync
  stores are unaffected.

  **The posture gate is injectable.** `settings_api` refuses unauthenticated writes in a *deployed*
  posture, which would have blocked dev-daily -- the one environment where someone needs to fix a
  Knowledge Hub URL without a redeploy. `posture_gate` lets a caller that has thought about it pass
  `strict_mode` instead; the default stays `deployed_posture`, because that is the safe answer for a
  library whose consumer has not.

  **`degraded` is a callable now, not a boot snapshot.** `missing_config()` recomputes from the
  environment as it is, so `/info` and the chat gate see a value set a moment ago. A snapshot would
  have meant the endpoint asked to confirm a fix denying the fix happened. Verified end to end: a
  strict replica 503s, the value is set over HTTP, and the same process serves.

  Read is open in every posture, since "what is this replica configured with" is the question asked
  about a box behaving oddly and the answer is already masked. Writes need a relaxed posture or an
  `auth` dependency, and the posture keys themselves are non-editable -- a replica must not be able
  to promote or relax itself in response to a request.

  Re-wiring lives in the store's `write`, not in a wrapper around the route: replacing a FastAPI
  endpoint with a generic `*args, **kwargs` function leaves FastAPI seeing no parameters, and the
  body it then never parses comes back as a 422 that looks like the caller's fault. That was the
  first shape of it.

- **A real-shaped profile now ships with the suite.** Two pack tests ran against a jazzx-assistant
  checkout beside japes, so they only ever ran on a machine that had both -- in CI they skipped,
  printing a path under the runner's home that read like a misconfiguration. `tests/fixtures/
  reference_profile` mirrors the structure (persona in its own file, empty `scope`, both streaming
  flags, three skills as separate documents with tools and references) and two tests cover the
  loader and the runtime binding path everywhere. Confirmed by breaking the fixture: a dangling
  `persona.md` reference and a dropped skill each fail a different one.

  Generic on purpose. Pinning the fixture to a consumer's domain would make every edit here a
  question about whether their assistant still works, which is a contract test belonging in their
  repo -- their CI has the profile by definition, and a failure would land where the fix is. The
  sibling-gated pair stays as local extra assurance, with a skip reason that says so.

- **The suite runs clean: zero warnings, down from eleven.** Two unrelated causes, both of them
  noise that trained the eye to skip the warning block.

  Nine classes named `Test*` are subjects, not tests: experts, skills and pydantic models whose
  bases take constructor arguments, so pytest tried to collect each one and skipped it with a
  warning. `__test__ = False` is the documented opt-out and keeps each name matching the thing it
  implements, rather than renaming the subject to please the collector.

  Two `datetime.utcnow()` calls in `test_automation_handler.py` are deliberately naive -- they
  assert the handler tolerates a datetime with no tzinfo. `utcnow()` is deprecated, and its
  naive-UTC replacement is an aware `now()` with the tzinfo dropped, which keeps the input naive
  instead of quietly fixing the thing under test.

- **The double's own contract is now pinned by tests, after two rounds of getting it wrong.**
  Recording calls on the class made the base class's list process-global for directly-constructed
  instances: a scripted list resumed at whatever the previous test left behind, so a fresh agent's
  *first* call returned the second response, and `last_call()` handed back another test's call
  instead of raising. Class-level state is only safe on a `returning()` subclass, which belongs to
  one test; the base class is shared by the whole process. Bound subclasses record on the class
  (one flow, several agents), direct instances record on themselves, and the scripted index follows
  whichever is authoritative.

  `last_call()` had the same split-brain: a `classmethod` reads the class list either way, so a
  directly-constructed agent that *had* been called raised "was never called". It is a descriptor
  now, binding to the instance's record on an instance and the class's on a bound subclass. The
  test that was meant to cover it asserted only the never-called case, which is the one path where
  the empty class list happens to give the right answer -- it passed against the broken code.

  Also: `returning(RuntimeError)` raises rather than handing the class back as a result, an empty
  script is a loud error rather than `None` on every call, and the module docstring's em-dash is
  gone along with the ones in the Plato modules added alongside it.

  Nine tests now cover the shapes, each one a case a hand-rolled double had and a draft of this got
  wrong. A test double's failures are silent by construction, which is exactly how a two-value
  unpack survived against a three-value contract.

- **A real bug, found by migrating the hand-rolled doubles onto `ScriptedReasoningAgent`.**
  `ReasoningAgent.run` returns `tuple[Any, SQLiteSession, TokenUsage]`, and
  `agents/reasoning/grounding.py:184` unpacked two. Every real call to `HeadingsOnlySelector`
  raised `ValueError: too many values to unpack` -- caught by the surrounding `except`, logged as
  "selection call failed", and degraded to no selection. So headings-only grounding selected
  nothing, on every call, quietly.

  The test could not catch it because its hand-rolled double returned two values as well: the
  double agreed with the bug instead of with the contract. That is the argument for a shipped
  double in one line -- seven test files each wrote their own, and each was free to be wrong in its
  own direction. Confirmed by restoring the two-value unpack against the migrated test, which now
  fails.

  Seven files migrated (`curator_synthesis`, `evaluator_mode`, `adjudication_agent`,
  `adjudication_segment`, `learning_candidate_adapter`, `precomputed_grounding`,
  `condition_evaluator`); no hand-rolled `ReasoningAgent` double remains. `test_split.py` keeps
  its own, correctly -- that one doubles `AgentExecutionService`, a different interface.

  Three defects in the shipped double surfaced while migrating real usages, each from a shape a
  hand-rolled version had and the first draft did not: a callable response stored as a class
  attribute became a *bound method* and arrived with `self` as an extra positional; a scripted list
  restarted per instance, so a flow building one agent per segment handed every segment the first
  response; and calls recorded only on the class meant two directly-constructed instances shared
  one history. Responses that are exceptions are now raised rather than returned, which is how a
  test says "this call fails".

- **`ScriptedReasoningAgent`, and the last `synthesize_bucket(llm=...)` caller is gone.** The SDK
  deprecated `llm=` in favour of `agents=` while shipping a test double only for the deprecated
  path, so every caller testing the replacement hand-rolled one -- five test files here did, and
  `test_learning_loop_end_to_end.py` stayed on the deprecated call for exactly that reason, its
  docstring saying "swapping it is a separate change". A deprecation whose replacement is harder to
  test than the thing it replaces does not get adopted.

  `jazzx_sdk.agents.scripted.ScriptedReasoningAgent` is the counterpart to `ScriptedLLM`: a fixed
  response, a list consumed in order, or a callable receiving the call's kwargs -- the three shapes
  the hand-rolled versions grew, including routing on `name` where one flow makes several
  differently-named calls. `returning()` builds the bound subclass each of them defined by hand.

  The suite now runs clean of that warning, verified with `-W error::DeprecationWarning`.

- **A pricing overlay for any model with a long-context tier registered broken.**
  `plato/reference/model_overlay.py` stored pricing with `asdict()`, which renders `long_context`
  as a nested dict, and reloaded it with `ModelPricing(**payload)`, which takes that dict as-is.
  Construction *succeeds*, so the overlay registered with a plain dict where a `LongContextPricing`
  belongs, past the `except` that would have logged and skipped a malformed row. The failure then
  surfaced as `AttributeError: 'dict' object has no attribute 'threshold_prompt_tokens'` from
  `for_prompt_size`, at cost-computation time, far from the load that caused it.

  Every frontier model with a large-prompt premium carries a tier, so this was the common case for
  exactly the models an operator is most likely to correct a rate on.

  `_pricing_from_json` already did this correctly for the bundled `model_data.json` and was
  private, so the overlay hand-rolled its own version and got it wrong. It is now
  `pricing_from_mapping`, public, and both callers use it: reconstructing pricing from a dict is
  one operation, and the second hand-rolled copy was the bug. The card path alongside it had
  already been written carefully for the same class of problem (`_CARD_TUPLE_FIELDS` rehydrates its
  tuples), which is what makes the pricing omission an oversight rather than a shared gap.

  Reported in review of the pushed branch; confirmed by restoring `ModelPricing(**payload)` against
  the new test, which fails.

- **Four fixes from the first real deployment's environment, and the boot is now unstoppable.**

  `PLATO_WIRING` was set to `acme.plato_wiring:build` -- the placeholder from this repo's own
  documentation, written before a shipped wiring existed. The docs now name
  `plato.wiring_default:build`. (A placeholder failed at boot when this landed; the boot contract
  above later reversed that for serving roles, which come up on `/info` with the reason instead.
  A `job:*` role still exits 4.)

  `JAPES_REQUIRE_IDENTITY=true` was silently ignored: the wiring built
  `ServerSettings(require_identity=strict)`, and with no environment tier that is `False`. A
  deployment asking for identity enforcement got none and was told nothing. An explicit request now
  wins in any posture, and still cannot turn enforcement *off* in a strict one.

  `KH_API_KEY` -- the name the platform actually sets -- was read by nothing, so a deployment that
  supplied its Knowledge Hub token got an unauthenticated client. Accepted now, with the
  JAPES-prefixed names still winning.

  **Blank means unset only where blank is not a value the field could hold.** The first attempt
  dropped every blank key so the field's default applied -- fine for a `bool` or a `Literal`, which
  cannot be `""`, and wrong for a `str` whose default is non-empty. `llm_fallback_provider=""` is
  how a deployment says "no fallback" (`llm/manager.py` gates on `if fallback and
  fallback_provider`), so clearing it silently re-enabled Anthropic on every primary failure for an
  OpenAI-only deployment. It also contradicted `env()`, whose contract is that an empty string
  counts as set.

  Making the documented "every field" true then needed a settings *source*, not a validator: the
  env source JSON-decodes a complex field before any validator runs, so `JAPES_LLM_TASK_ROUTING=""`
  raised `SettingsError` regardless. `_BlankAwareEnvSource` drops a blank per field, ahead of the
  decode. Its type test unwraps unions only -- recursing into a generic's parameters made
  `dict[str, dict[str, str]]` report `str` among its types, so a dict field read as one a blank
  could legitimately fill. The alias lookup matters for the same reason: pydantic-settings keys an
  aliased field by its alias, so every `JAPES_`-prefixed variable was taking the unknown-key branch.

  A blank value crashed `JAPESSettings` -- first `JAPES_ENVIRONMENT`, and after a per-field fix
  still `use_managed_identity` and `llm_enable_local`, booleans on the same model fed by the same
  platform. The coercion is model-wide now, dropping blank keys so each field's own default
  applies, because a rule stated unconditionally in the docs cannot have an unwritten list of
  exceptions. Relatedly, a *blank* `JAPES_KNOWLEDGE_HUB_TOKEN` shadowed a filled `KH_API_KEY`:
  `env()` treats an empty string as set by design, so the token lookup now takes the first
  non-blank name. An empty `JAPES_ENVIRONMENT=""` crashed `JAPESSettings`. Container platforms render a
  declared-but-valueless variable as `""`, so the literal rejected it and every caller of
  `get_runtime_settings()` raised. Empty now means unset, which is what the operator meant; a typo
  is still rejected loudly.

  **And a schema behind the image no longer exits 5 for a serving role.** `/info` reports which
  revision the image expects against what the database has, and a replica that answers that is
  worth more than one that exits having printed it once. A `job:*` role still refuses: it takes no
  requests, consults no gate, and writes, so a sweeper deleting rows through the image's models
  against an older schema corrupts quietly -- which is the failure the check exists for, and which
  the first version of this change removed for every role at once.

  Getting that reported at all took two corrections. `build()` returned a *snapshot* of what was
  missing, so a note recorded a moment later never reached `/info`, which answered
  `configured: true` against a mismatched schema -- strictly worse than the exit it replaced. It
  now hands over the function. And the note lived in `plato/__main__`, which under `python -m plato`
  runs as `__main__`: importing `plato.__main__` executes the file a second time and binds a
  *different* list than the one appended to, so the value was never going to arrive. State shared
  across that boundary now lives in an ordinarily-imported module.

  **What `degraded` reports is the running process, not the environment and not a boot snapshot.**
  Both of those were wrong in opposite directions. Reading the environment cleared the pack gap the
  moment `PLATO_PACK_DIR` was set, while the process kept the empty registries it loaded once --
  `/info` claiming assistants the replica could not serve. A boot note went stale the other way: a
  database corrected through `swap_database` kept being reported as sqlite until a restart.

  So each check reads whatever actually decides the answer: the process for the pack (are there
  skills?) and the database (what is the *current* store?), the environment for the Knowledge Hub
  URL, LLM key and tenants, and boot notes only for what neither can rediscover -- a schema behind
  the image, and a pack path that was set but would not load. The pack message says a restart is
  what fixes it, since setting the variable will not.

  The pack predicate itself then got written twice. The first version probed `_skills` and `all()`
  -- names `SkillRegistry` does not have; it is a `NamedRegistry` with `_items` and `__len__` --
  so every registry read as empty and a *correctly configured* deployment permanently reported
  "No assistants loaded", 503-ing its chat routes in a strict posture. Guessing at an API
  defensively was worse than reading it: `getattr` with a default does not raise, so the `except`
  written to catch exactly that never fired. It is `len(skills)` now.

  Nothing caught it because no test in that file had ever built against a pack that loads -- every
  one pointed `PLATO_PACK_DIR` at `/nonexistent/pack`, so the negative case asserted the absence of
  three other reasons and never that the pack gap was absent. There is a loadable pack from the
  shipped reference profile now, and the always-on predicate fails against it.

  `PlatoWiring.degraded` is declared as the tuple-or-callable it now is, with `resolve_degraded()`
  for consumers; it had kept a `tuple[str, ...]` annotation while the shipped wiring assigned a
  function, so `" ".join(wiring.degraded)` raised `TypeError`.

  **Boot notes reach every wiring, not just the shipped one.** They were merged inside
  `plato.wiring_default`, so a deployment naming its own factory -- the documented normal case --
  got `configured: true` and an open chat gate against a mismatched schema, having also lost the
  exit that used to catch it. The merge is in `plato.wiring.resolve_degraded`, which every role's
  app goes through whoever built the wiring.

  **And the posture gate applies the rule the wiring applies.** It checked
  `JAPES_REQUIRE_IDENTITY` alone while `build()` had been changed to `strict or requested`, so a
  production replica with the variable unset returned 3 and never started -- the gate refusing the
  very configuration it was about to produce. That is the exact sibling of the bug it was fixing,
  one file away.

  `resolve_kh_token` moved to `jazzx_sdk.config.envvars`, the tier both readers can import.
  `ClientLayer` and `FabricConfig` read the same platform credential under *different name lists*,
  so a deployment could end up with an authenticated Knowledge Hub client and an unauthenticated
  fabric one. The import-linter contract caught the first attempt, which had `fabric` importing
  `client_layer`.

  Also: `_apply_durable_settings` called `asyncio.run` unconditionally, so building inside a
  running loop raised and leaked an un-awaited coroutine, surfacing as a RuntimeWarning against
  whichever test was collecting garbage. It now closes the coroutine and says why it skipped.

  First-boot logging is one line rather than a traceback: before migrations the settings table
  legitimately does not exist, and a stack trace there reads as a failure in a log whose next line
  says the replica started fine.

- **Plato 0.1.2.** The deployable wiring, the four deployment tiers, the strictness axis, and
  `/v1/config` with durable settings and a runtime database swap. The SDK stays at 2.5.0: Plato's
  version tracks the service, not the library it is built on.

- **Plato ships a deployable wiring, and `dev-daily` is now a posture the platform recognises.**
  The cloud replica reached `PLATO_WIRING is not set` -- correct behaviour, since the package
  deliberately ships no default: Plato hosts *someone's* assistant. That argument holds for the
  pack and the tenants and does not hold for the plumbing around them, which every environment
  resolves identically and was about to be re-derived per deployment.

  **Four deployment tiers, one canonical name each: `local`, `dev-daily`, `staging`,
  `production`.** `deployed_posture()` recognised only `production`/`prod`/`staging`, so a shared
  cloud environment reported `environment=local` and ran with identity enforcement off, in-process
  stores allowed and a Mock Knowledge Hub permitted -- the same exposure as production, since other
  people can reach it, with none of the guards.

  The cloud tier is `dev-daily` rather than `dev` deliberately. `dev` reads as a synonym for "my
  laptop" and means exactly that in jaci's `.env.template` and juno, so naming the cloud tier `dev`
  would flip both to deployed and take away the Mock fallback their developers rely on -- a failure
  landing on laptops, pointed the opposite way to the one the tier exists to prevent. `dev` and
  `test` are accepted aliases of `local`, and `prod` of `production`; aliases resolve rather than
  being rejected because a name the table does not know reads as *not deployed*, which loses a
  fail-safe quietly.

  **Strictness is a second axis, and `dev-daily` is relaxed by default.** Deployed and strict came
  apart the moment dev-daily existed: *deployed* is about what a replica holds, *strict* is about
  what the environment is for. dev-daily is where someone pushes a branch to see whether it works,
  so a tier that refuses to start without a real Knowledge Hub, Postgres and identity headers does
  not serve it. `strict_mode()` is strict on `staging`/`production` and relaxed on
  `local`/`dev-daily`, and `JAPES_STRICTNESS` overrides it -- tightening any tier, loosening every
  one except `production`, where the guards it would disable are the only thing between an
  anonymous caller and real data.

  Relaxed, a Plato replica comes up the way a laptop does: Mock Knowledge Hub, sqlite, identity
  off, chat serving. What is missing is still collected, logged at boot and reported by `/info`; it
  is advice there and enforcement (`enforce_degraded`) on staging and production.

  Four guards moved onto the new axis -- the Mock Knowledge Hub refusals in `client_layer` and
  `fabric`, the durable-queue-store requirement in `runtime`, and Plato's `require_identity`
  refusal. Two deliberately did not: an unauthenticated configuration write and an unattributed
  actor stay gated on *deployed*, since neither stops a replica coming up and relaxing them costs
  real exposure on a shared environment for no gain. A first pass moved all six, which is what
  five posture tests caught.

  `check_settings(environment=...)` takes the environment as an argument so tests need not mutate
  the process, so strictness reads it through `strict_for(name)` rather than the process
  environment -- otherwise the check reads one environment and its strictness another, and the
  injection seam silently stops working.

  `environment_tier()` returns the tier and `deployed_posture()` still returns the operator's own
  spelling, since that is what lands in logs and error messages. One table backs both, and
  `JAPESSettings.environment` now derives its allowed values from it rather than restating them.

  **`plato/wiring_default.py`** is the shipped factory: `PLATO_WIRING=plato.wiring_default:build`.
  One file for both postures, deciding by posture rather than by two files drifting apart.
  Deployed, it expects Postgres via `common.core.db`, a Knowledge Hub URL, an LLM provider key, an
  explicit `PLATO_TENANTS`, and `X-Tenant-Id` per request, and turns `require_identity` on.
  `scripts/plato_wiring.py` stays the zero-infra demo.

  **It starts anyway when those are missing, and says so in three places.** Refusing to boot was
  the first shape of this, and it was the wrong trade: the exit reports only the first missing
  variable, so four missing variables cost four deploy cycles. Now every missing item is collected
  into `PlatoWiring.degraded` and the boot continues. The startup log lists all of them; `GET
  /info` reports `extra.configured` and `extra.degraded`; and the chat routes answer 503
  `plato_not_configured` naming what is missing, rather than serving a Mock Knowledge Hub's empty
  context as though it were real. Sessions, `/info` and the migration check keep working, which is
  why the database falls back to sqlite (itself reported) instead of being withheld: those are the
  surfaces you diagnose with. Identity is not relaxed by degradation.

  **A pre-existing crash surfaced on the way, and is why the list is derived rather than
  restated.** `JAPESSettings.environment` was `Literal["dev", "staging", "prod"]` while
  `deployed_posture()` treats `production` as its canonical deployed value, so any service setting
  `JAPES_ENVIRONMENT=production` died inside `get_runtime_settings()` instead of being recognised
  as deployed. Restating the names in two places is what allowed that, so the literal is now
  `Literal[ENVIRONMENT_NAMES]` off the tier table and a test asserts the derivation holds.

  The two reads fail in opposite directions on purpose: `environment_tier()` treats an unknown name
  as `local`, because guessing that a typo means production would refuse to start a laptop, and
  `JAPESSettings` rejects it loudly. Together a typo gets one clear error instead of a quiet loss
  of every fail-safe.

  **The environment-resolved `ClientLayer` moved out of `jazzx_sdk.ui`.** `get_client_layer` and
  friends were named for their first caller; nothing in them was Streamlit-specific, and a server
  wiring should not reach into a module called `ui` for the platform handle a deployment runs on.
  They now live in `client_layer.py`, beside the `ClientLayer` they build and the env resolution
  they use, with `jazzx_sdk.ui` re-exporting the public three so jaci's imports keep working
  (surveyed first: only jaci's two UI pages and one japes test).

  Nine tests, including the one distinction the tier rests on -- `dev` non-deployed, `dev-daily`
  deployed, `production` deployed but not pre-production -- and a fixture that clears the LLM keys,
  because a developer's own key silently satisfied that check while the test was being written.

- **The reference chat conductor can require its grounding, and no longer loses escalated turns
  from history.** Both came out of reading what jazzx-assistant's handler does above a single agent
  call, and both are cases where the pipeline could not express something a consumer had to
  orchestrate outside it -- which is the thing `ground_step` was written to prevent.

  **Required grounding.** `gather_degrading` degrades every source to its default so one dead
  system cannot sink a turn. That is right for advisory context and wrong for evidence: a turn
  grounding on a loan record that is down answered confidently from an empty default, and nothing
  in `turn.grounded` could tell that default from a real empty result. `ground_step(required=...)`
  and `build_chat_components(required_sources=...)` name the sources whose absence must stop the
  turn (`True` for all), raising `GroundingRequiredError`, which `run_chat_turn`'s existing
  `on_step_error` already turns into an incomplete reply that halts the run. Default stays
  `False`, so every current caller keeps degrade-everything.

  Which sources degraded is read off `gather_degrading`'s own `SourceProgress.failed` reports
  rather than re-derived, by chaining a recording hook onto the caller's. The primitive needed no
  change: it already knew, it just had no one to tell. A second return value would have been a
  thing every other caller had to ignore.

  **Side-branch persistence.** `respond` persists its own turn, so the direct route was covered and
  the other two were not: `escalate` and `refuse` both hand back an answer the user reads without
  touching the agent, leaving conversation history with a hole exactly where the turn was most
  worth keeping, and the next turn then loaded a history that skipped it. Closing it needed a
  public seam -- `_persist_turn` was private, so a pack could not do it either -- so
  `InteractiveAgent.persist_turn` now exposes the same decision `respond` makes, with the same
  conversation guard. `persist_side_branch` is shared by `finalize_step` and `stream_chat_turn`'s
  three one-shot returns, because a copy in each is two chances for the routes to disagree about
  what history contains. It fails soft: bookkeeping must never lose a delivered answer.

  Eight tests, each confirmed to fail against the previous behaviour: required-source failure stops
  the turn and the agent is never called, `required=True` covers every source, a non-required
  failure still degrades, the caller's progress hook still fires alongside the recorder, escalated
  and refused answers are persisted, the direct branch is *not* persisted twice, a store failure
  still delivers the answer, and the streaming route persists its side branches too.

- **`aiosqlite` became a core dependency, having been declared as a dev one.** It was added for
  tests ("zero-infra backend for testing SqlConversationStore") and a runtime branch then grew onto
  it: `DbStore._sessionmaker` builds a `sqlite+aiosqlite://` engine whenever `backend="sqlite"` is
  selected. A dev-group dependency is absent from every non-dev install, so that path raised
  `ModuleNotFoundError: No module named 'aiosqlite'`.

  The first attempt put it in the `plato` extra, which was the wrong home twice over. The backend is
  chosen by `FabricConfig.db_backend` -- core SDK config read from `JAPES_DB_BACKEND` /
  `JAZZX_DB_BACKEND`, nothing to do with hosting -- so a plain `pip install japes` could select
  `"sqlite"` and still break. And extras are not installed by a bare `poetry install`, which
  `docs/LOCAL_TESTING.md` documents, so the suite's own sqlite tests would have errored rather than
  skipped: the comment claiming they "skip w/o aiosqlite" described a guard that does not exist.

  Core is the honest placement, and cheap: 55 KB, no runtime dependencies of its own. Verified on a
  plain install with no extras at all -- `JAPES_DB_BACKEND=sqlite` resolves and a session opens,
  while `alembic` correctly stays absent as an extras-gated dependency. The lock diff is one field,
  `optional = true` to `false`. The image guard names `aiosqlite` too, since it is the one core
  dependency nothing on the eager import path pulls.

- **The Plato image shipped empty, and the build reported success.** The container died on
  `import pydantic` at `jazzx_sdk/models.py:30`, a core dependency, which meant nothing at all had
  installed rather than an extra being missed.

  Three faults, compounding. `pyproject.toml` declares `jazzx-eval-contracts` as a *path*
  dependency and `README.md` as the readme, but the builder stage copied only `pyproject.toml` and
  `poetry.lock`, so `poetry install` failed with `Path /build/jazzx_eval_contracts ... does not
  exist`. The install line then ended `&& git config --unset ... || true`, and since `&&` and `||`
  associate left at equal precedence that binds to the whole chain: a failed install short-circuits
  to `true` and the RUN exits 0. And the stage boundary copies `site-packages` whether or not
  anything landed in it, so the empty result was invisible until deploy.

  A fourth fault sat behind those, and the first pass at this missed it: `jazzx-eval-contracts` is
  declared `develop = true`, so poetry installs it *editable*. site-packages receives a `.pth`
  holding the absolute builder path `/build/jazzx_eval_contracts`, never a copy of the package, and
  the runtime stage copies site-packages without that directory. A `.pth` naming a missing directory
  is ignored in silence, so the build would have gone green and the image still could not import the
  package -- reached through `EvalServiceFeedbackSink` behind `POST /v1/feedback`, among others. The
  source is now copied into `/app`, but not the way the neighbouring copies work, and the first
  attempt at this got that wrong too: `jazzx_sdk`, `common` and `plato` are directories that *are*
  packages, while `jazzx_eval_contracts/` is a project root holding `pyproject.toml`, `tests/`,
  `scripts/` and the package one level down. Copying the root puts an `__init__.py`-less directory
  on `PYTHONPATH`, where `import jazzx_eval_contracts` quietly succeeds as an empty namespace
  package while every submodule import fails. The builder stage wants the root, because poetry reads
  its `pyproject.toml`; the runtime stage wants the package. The two paths are deliberately
  different.

  That asymmetry also disarmed the check: a bare `import jazzx_eval_contracts` passes in exactly the
  broken state, so the assertion imports `jazzx_eval_contracts.feedback` instead.

  So: the directory and README are copied into the builder, the contracts source into the runtime
  stage, the `|| true` is braced to cover only the cleanup, and the runtime stage asserts the five
  imports that each stand for one way this can break, plus `jazzx_sdk.evaluation.feedback_sink`,
  which is lazy and therefore invisible to a bare `import jazzx_sdk`.

  The same faults were in `examples/document_analyzer/Dockerfile` and
  `examples/basic/Dockerfile.sample`, which build from the repo root against the same manifest;
  both are fixed rather than left to fail the same way, and both gained the import check.

  `examples/basic/` is excluded by `.dockerignore`, so that one is a template nobody builds from
  here. It is fixed anyway: a sample is copied, and a broken sample propagates.

  Verified without a daemon: `poetry check --lock` passes on the fixed builder context and still
  reports both errors on the old one; the braced form exits 1 on a failed install while still
  tolerating a failed cleanup; an editable install's `.pth` was shown to hold an absolute source
  path and to raise `ModuleNotFoundError` once that directory is moved away; the new assertion fails
  on exactly that condition; and each `RUN python -c` payload is reassembled the way Docker joins
  continuation lines and parsed with `ast.parse`, which is what catches a doubled backslash making
  the guard-rail line itself a syntax error.

- **MLflow moved behind a backend boundary, and the SDK's public surface is now the abstractions
  only.** The four abstract base classes already existed -- `RunTracer`, `TraceSource`,
  `AgentTraceHooks`, `EvaluationReporter`, `ExperimentStore` -- but their mlflow implementations sat
  beside them, in three cases inside the same file. `run_tracer.py` was the clearest: 383 lines of
  which the ABC was about forty.

  Implementations now live in `observability/backends/mlflow/` (tracer, trace source, hooks,
  runtime, env) and `evaluation/backends/mlflow/` (reporter, experiment store and its bridge).
  `MlflowTracer`, `MlflowTraceSource` and `MlflowTraceHooks` have left `jazzx_sdk.__all__`, and
  `MlflowExperimentStore` has left `evaluation`'s: a backend is reached at its own path or built by
  `resolve_tracer`, never exported as though it were the interface.

  **Two directories, not one, and the tier contract is what determined that.** The first attempt put
  every mlflow file under `observability/backends/`, and the contract broke: `evaluation` sits above
  `observability`, so a class implementing `EvaluationReporter` cannot live below it without
  importing upward. A backend belongs with the abstraction it implements, which is a better rule
  than "all mlflow code in one place" and would not have been obvious without the check.

  **`AgentTraceHooks` turned out to be an abstraction living in the mlflow file.** The assessment
  that preceded this work recorded `agent_hooks.py` as 319 lines with "no abstraction above it" --
  wrong. It contains an ABC (needing only openai-agents) *and* the mlflow subclass, coupled through
  a factory call rather than an import, so they separated cleanly. The base class no longer sits
  behind an optional dependency it does not use.

  A fourth contract now enforces the boundary: nothing may import a backend at module scope, with
  one registered exemption for `resolve_tracer`, the factory whose job is choosing one. That
  exemption is explicit because import-linter counts a function-level import like any other --
  which is the better outcome, since any *other* module reaching for a backend now fails even if it
  does so lazily. Verified by adding such an import and watching it break.

  **Two follow-up fixes, both found in review of the above.** The lazy `AgentTraceHooks` entry was
  retargeted at `backends/mlflow/hooks.py`, which serves only `MlflowTraceHooks`, so an export that
  stayed listed in `__all__` stopped resolving -- `from jazzx_sdk import AgentTraceHooks` raised, and
  the whole suite passed, because the surface test compares name *sets*. `test_every_exported_name_
  actually_resolves` now gets every name in `__all__` on all three packages.

  And the boundary the contract names had a crossing it structurally cannot see:
  `observability/__init__.py` re-exported three helpers from `backends/mlflow/env.py` at module
  scope. An import-linter `forbidden` contract skips any pair whose forbidden module descends from
  the source, so `observability -> observability.backends.**` reports KEPT however it is listed
  (measured: the edge is in the grimp graph and the contract still passes). The crossing is now
  gone -- those three resolve lazily, like `AgentTraceHooks` -- and `test_no_backend_on_the_eager_
  path` asserts in a subprocess that no backend module reaches `sys.modules` on a bare package
  import. The contract was renamed to `no abstraction imports a backend at module scope`, which is
  what it actually checks. Both tests were confirmed to fail against the defects they describe.

  `RunContext` moved with the mlflow half rather than staying in `span_mapping.py`. It is a handle
  whose purpose is carrying an `MlflowClient`, so keeping it in the module that advertises importing
  no mlflow was the same mismatch the split existed to fix, and its callers use it alongside
  `log_artifact_with_retry`. Nothing in japes constructs one yet: it and `log_artifact_with_retry`
  are two thirds of macer's `utils/run.py` trio, ported for the SDK consolidation, and the
  `create_run` factory is still outstanding.

  `observability/mlflow_bridge.py` is gone, split rather than renamed. The name was the visible
  problem and the mixed contents were the real one: `spans_to_canonical_trace` and its helpers work
  on anything span-shaped and import no mlflow, but `safe_link_traces_to_run`,
  `safe_update_current_trace`, `log_artifact_with_retry` and `mlflow_run_to_canonical_trace` all
  `import mlflow` in their bodies. One file, both sides of the boundary the rest of this change
  draws. The generic half is now `observability/span_mapping.py`, next to the abstractions it
  serves; the mlflow half is `observability/backends/mlflow/bridge.py`. `trace_source.py`'s
  docstring had asserted the whole file imported no mlflow, which was true of the part it used and
  false of the file.

  Part of the motivation is version containment rather than tidiness: mlflow's constraints have
  pinned unrelated packages before, and it currently carries a high-severity advisory with no fixed
  release. Confined to two directories the SDK never imports eagerly, that is a contained problem.

  Consumers: k9 imports `RunTracer`/`RunHandle`/`SpanHandle` and ships its own `PrintingTracer` on
  that base -- untouched by this, and standing proof the seam works. jaci imported `MlflowReporter`
  by its old path; that one line is fixed alongside. No other repository referenced any of it.

- **LiteLLM is gone, and `openai-agents` moves 0.20 -> 0.22 with `openai` 2.x -> 3.3.** One optional
  dependency was setting the floor for the whole SDK: every litellm release through 1.98.0 pinned
  `openai<3.0.0`, while openai-agents 0.21+ requires `openai>=3.0.0`. Removing it was blocked on
  capability, not on will, and the three things it still did have each been replaced first:

  - Claude as an Agents-SDK model -> `AnthropicNativeModel`, including the `cache_control` injection
    that was the litellm-backed model's whole reason for existing.
  - Bare Gemini -> `GeminiNativeModel`.
  - **Gemini on Vertex AI** -> `build_genai_client`, the last capability only the passthrough had.

  Deleted: `jazzx_sdk/agents/anthropic_model.py`, its lazy export from `jazzx_sdk.agents`, the
  `litellm/<provider>/<model>` dispatch in `resolve_model`, `_litellm_model`,
  `_litellm_anthropic_name`, the `JAPES_ANTHROPIC_LITELLM` escape hatch, and the `litellm` extra.

  **A stale `litellm/` prefix still resolves.** Names recorded while that was the route carry the
  qualifier, and a stored name should not fail on a prefix that has merely stopped meaning
  something -- it is stripped and the provider inferred from what is left. The prefix also stays in
  `model_identity`'s strip list for the same reason. What is gone is any *dispatch* on it: a
  provider japes has no adapter for is now unreachable through `resolve_model`, and writing an
  adapter is the route rather than a passthrough that constrains every other dependency.

  Four tests went with the deleted module. Their coverage did not: cache_control injection and its
  empty-block skip are the native adapter's now and are tested there, which a comment in
  `test_agent_models.py` records so the deletion does not read as lost coverage. One test asserted
  the passthrough still existed by grepping `resolve_model`'s source; it now asserts the opposite
  behaviourally -- a `litellm/vertex_ai/...` name resolving to `GeminiNativeModel` with the
  qualifier stripped -- because the source form also matched the docstring explaining the
  tolerance, and would have failed for the wrong reason.

  Consumers: jaci pinned `japes[litellm]` and is fixed separately (it imports no litellm; its
  Anthropic eval harness passes a model *name* and lets `resolve_model` choose, which has been the
  native path since that adapter landed). macer and eval-service use litellm as their own direct
  dependency, unrelated to this extra. k9, juno, jazzx-assistant, assistant, kernel: no usage.

- **Gemini reaches Vertex AI natively, which was the last thing only LiteLLM could do.** Vertex
  takes a Google Cloud project and location and authenticates with ambient credentials, none of
  which a bare model name can express -- so `litellm/vertex_ai/<model>` was the only route, and that
  one passthrough kept the whole SDK pinned at `openai-agents` 0.20.

  `build_genai_client` is now the single place a `google-genai` client is constructed, taking
  `vertexai`/`project`/`location`. Both tiers use it -- the LLM tier's single-shot `run` and the
  agent tier's tool loop each had their own `Client(api_key=...)` line, and a second one is how the
  two come to disagree about which account a request bills.

  Vertex turns on when asked, or when `GOOGLE_GENAI_USE_VERTEXAI` is set *and* a project resolves.
  That is the variable `google-genai` reads itself, so a deployment already configured for Vertex
  needs no japes-specific setting. The flag alone is deliberately not enough: Vertex without a
  project cannot work, and switching paths on it would turn a missing setting into a confusing
  credentials error. Asking for Vertex explicitly with no project is refused outright rather than
  falling back to the api-key path, which would silently bill a different account.

  `is_available()` no longer means "has an api key". On Vertex there is no key, and reporting a
  correctly configured deployment as unavailable is worse than the check being slightly longer.

  Two things the tier contract caught while this was written, both worth recording. Importing
  `jazzx_sdk.config` -- the package -- pulls `config.settings`, which imports `client_layer` and
  through it most of the SDK; a two-line env helper should not drag the runtime facade in behind
  it, so the import is `jazzx_sdk.config.envvars` directly. And the first draft added Vertex to the
  agent-tier provider alone, leaving the LLM tier on its own client: the contract did not object to
  that, but the duplication is the shape CLAUDE.md's symmetry rule names, which is why the builder
  is shared rather than copied.

- **The native Anthropic model asks for prompt caching, not just reports it.** `AnthropicNativeModel`
  read Anthropic's cache counts back into `InputTokensDetails` but never injected a `cache_control`
  directive, so every Claude turn on the native path paid full price while the usage fields dutifully
  reported zero cached tokens. The LiteLLM-backed `AnthropicModel` it replaces did inject them --
  that was the reason it existed, in its own words, "(LiteLLM doesn't do this for you)".

  The failure mode is why this mattered: nothing errors. A request without breakpoints succeeds,
  returns the right answer, and reports a cache hit rate of zero. The bill is the only signal.

  Breakpoints are spent as the LiteLLM path spent them -- the system prompt, the message before each
  of the last two user turns, and the final message. Everything *before* a breakpoint becomes
  eligible for reuse, so they sit behind the parts that do not change between turns. Anthropic
  allows four; a test asserts we never exceed that, since going over is a 400 rather than a
  degradation.

  Empty blocks are skipped, because Anthropic rejects `cache_control` on empty text and a breakpoint
  spent there would buy a 400 in exchange for saving nothing. Caller blocks are copied rather than
  marked in place.

  One existing test changed shape: `system` now reaches the API as a cached text block rather than a
  bare string, because the directive attaches to a block and that is the only form Anthropic accepts
  it on. The test's purpose -- parity between the streaming and blocking paths -- is untouched; both
  still go through one `_request` builder.

  This is a prerequisite for dropping the `litellm` extra rather than part of it. Verified
  separately: with litellm's declaration removed, `openai-agents` resolves to 0.22.0 and `openai` to
  3.3.0, and the whole suite passes on them -- so litellm is indeed the wall holding the SDK at
  0.20, and the only thing it was still doing for us is the caching now ported here.

- **The mock Knowledge Hub validates updates, not just creates.** `MockKnowledgeHubClient` called
  `_validate_entity` from `create_entity` and nowhere else, so a mock-backed test could write a
  valid entity and then update it into a shape its ontology forbids with nothing objecting. Real KH
  validates both (`update_entity_with_validation`), which made the mock weaker than the thing it
  stands in for -- the one property a mock must not have.

  Validation is against the **effective** ontology and entity type: a partial update may change
  either, and checking the new value against the stored pair would validate it against the schema it
  is leaving rather than the one it is joining. Real KH shipped that exact bug and fixed it in its
  own `93ea215` ("json_value validated against the pre-update schema -> now validated against the
  effective ontology_id/entity_type"), so a mock repeating it would be wrong the same way twice.

  It runs before the write, so a rejected update leaves the stored entity untouched. Raising after
  mutating would be worse than not validating: the store would hold a value the schema forbids, and
  the next read would look authoritative.

  A name-only update is not re-validated. Nothing the schema describes has changed, and checking
  anyway would surface invalidity predating the call, reported as a failure of the rename.

  A metadata-only update is not re-validated either. That case is the seam between two changes that
  landed separately -- write provenance added `metadata` to this method, validation was added around
  `json_value` -- and metadata is the provenance envelope rather than part of the value the ontology
  describes. Stamping who touched an entity must not fail on invalidity predating the stamp.

  Found by surveying sibling repositories: jazzx-assistant added the same validation to its own
  hand-rolled mock KH on 2026-09-02. That japes ships a reusable mock KH precisely so packs stop
  hand-rolling one, and a consuming repo has its own anyway, is a separate question worth asking
  them -- recorded in `SIBLING_SURVEY_2026-09-02.md`.

- **`settings.py` and `env.py` became `config/`.** One concern read from two directions: `env()`
  resolves a `JAPES_`-preferred variable name with a legacy fallback, and `JAPESSettings` is the
  typed surface built on that same convention -- which `settings.py`'s own docstring already pointed
  at. Neither had a consumer outside this repository, so nothing needed a shim.

  `env.py` is `config/envvars.py` rather than `config/env.py`, and the reason is worth recording
  because the first attempt shipped the bug: re-exporting the `env()` function from the package
  `__init__` **shadows a submodule of the same name**. `jazzx_sdk.config.env` then resolves to the
  function, and three tests that `monkeypatch.setattr` against
  `jazzx_sdk.config.env.deployed_posture` failed with "'function' object has no attribute". Renaming
  the module removes the collision rather than working around it.

- **The shared-contracts grouping was proposed here and then dropped, because the data said no.**
  `models.py`, `events_domain.py` and `failures.py` are each bottom-tier and widely imported, which
  is what made them look like a set. Their consumers are nearly disjoint: `models` reaches 10
  packages, all transport and runtime (`server`, `channels`, `clients`, `queue`, `observability`);
  `events_domain` reaches 2 (`automation`, `statemachine`); `failures` reaches 7 and none of them
  overlap the first group meaningfully (`agents`, `llm`, `tools`, `evaluation`). A package holding
  all three would have no coherent audience, which is structure for its own sake.

  `contracts.py` does not belong with them either, for the opposite reason: it imports *upward*,
  from `fabric.canonical` and `evaluation`, because it is the curated Tier-1 import surface a
  library consumer opens -- a facade over definitions, not a definition. Grouping a top-of-stack
  re-export with bottom-of-stack primitives would have been flagged by the tier contract.

- **Three root-level clusters became packages: `queue/`, `runtime/`, `concurrency/`.** Seven modules
  that sat as peers of `fabric` and `agents` while being one tier's worth of one concern each.
  `queue_processor.py`, `queue_execution.py` and `queue_execution_db.py` are now
  `queue/processor.py`, `queue/execution.py` and `queue/execution_db.py`; `launcher.py` joins
  `runtime/`; `concurrency_guard.py` joins `concurrency/`.

  Two of the three cost nothing to import. `concurrency.py` and `runtime.py` became the packages'
  `__init__.py`, so every `from jazzx_sdk.concurrency import ...` and `from jazzx_sdk.runtime
  import ...` still resolves -- and `concurrency` has fifteen importers.

  The queue move does break one import path, deliberately. Four repositories -- jaci, k9,
  jazzx-assistant and macer -- do `from jazzx_sdk.queue_processor import QueueSettings`, reaching
  past the public API into a private module path. `QueueSettings` is already exported from
  `jazzx_sdk` itself and listed in `__all__`, so the fix on each side is `from jazzx_sdk import
  QueueSettings`: one line per repository, and an import that will not break the next time a module
  moves. A shim would have preserved the habit that made a rename breaking in the first place.

  No change to the debt list -- grouping alters shape, not direction, and it would be misleading to
  report otherwise. Top-level entries went from 55 to 53, which is the honest measure of what
  grouping alone buys.

- **Two server-tier route modules moved into `server/`, where their imports already pointed.**
  `observability/trace_routes.py` and `runs/server.py` both import `server.governed_http`: route
  factories living in core packages. Their own docstrings said as much -- one described itself as
  "consistent with the rest of japes' server tier" -- so the code had known for a while.

  They are now `server/trace_routes.py` and `server/run_routes.py` (renamed, because
  `server/server.py` names nothing). No shim: a survey across japes, jaci, k9, jazzx-assistant,
  juno, macer, assistant and eval-service found them referenced only by japes' own two tests.
  Neither was ever exported from its package `__init__`, which is why nothing depended on them.

  The debt count went 16 -> 17, and the direction is worth explaining. `runs -> server` cleared,
  which is -1. `observability` was never in the layer list at all, so its inversion was invisible to
  the contract -- and an unpoliced module is exactly where the next one hides. Bringing it under the
  contract exposed two pre-existing edges (`observability -> agents`, `identity -> observability`),
  which is +2. The longer list is the stronger one: one real inversion is gone for good, and the
  package that hid it is now policed.

  Left alone deliberately: `identity.with_trace_context` imports `observability.trace_context`, and
  its own docstring says trace propagation is orthogonal to identity. Moving it would relocate the
  edge rather than remove it, since `kernel_request_headers` in the same module composes with it.

- **The tier debt list is down from 29 pairs to 16, with no code moved.** All of it came from making
  the contract describe the code more accurately rather than from loosening it -- the ratchet still
  catches a new cross-tier edge, verified again by adding `fabric -> server` and watching it break.

  `exclude_type_checking_imports = True` accounts for 7 of the 13. Type-only imports are not runtime
  dependencies, and counting them had one `if TYPE_CHECKING` annotation in `handlers.py` reporting
  the SDK's identity primitives as dependents of llm, agents, mcp and fabric -- through
  `ClientLayer`, which they never touch at runtime.

  The other 6 were the layer order being wrong, in three ways worth naming because each was a
  mistaken assumption about the architecture rather than a defect:

  - `streaming` is a transport primitive agents publish *to*, not a host sitting above them.
  - `statemachine` consults `authority`, so it cannot sit below it.
  - `pack` and `manifest` are configuration nothing lower reads, so they belong near the top.
    Moving them cleared five pairs and introduced three (`fabric -> manifest`,
    `authority -> manifest`, `pipelines -> pack`), which is where ordering stops paying.

  What remains needs code, not a different sort. Two are files in the wrong package -- `runs/server.py`
  and `observability/trace_routes.py` both import `server.governed_http`, being server-tier route
  modules living in core packages. One is a client reaching into runtime internals
  (`clients/japes_queue_client.py` importing `queue_processor._build_provider_pair` and
  `_parse_message`). The rest are shared *types* sitting inside higher packages -- `modes.schemas`
  read by `tools`, `finance.vocabulary` read by `expressions` -- where the fix is to move the type,
  and each move is a breaking import for consumers.

- **Caller identity moved out of `handlers.py` into `jazzx_sdk.identity`, with no shim.**
  `handlers.py` held two unrelated things: the handler contract a consumer implements
  (`Handler`, `BaseHandler`, `HandlerContext`, `job_id_for`) and the platform's identity
  primitives -- security context, inbound-header capture, `CallerIdentity`, and the outbound header
  set that forwards them. Fourteen packages imported it, more than any module here except `fabric`
  and `concurrency`, so under a name that reads as message-handling runtime nothing said whether a
  core module depending on it was reaching upward or sideways.

  A correction to the earlier note in this file: `handlers.py` was described as containing no
  handlers. It does -- `HandlerContext` alone is imported 23 times by consumer repos. The first
  reading covered only the file's first 300 lines. It was never misnamed; it was two concerns
  sharing a file, which makes the fix a split rather than a rename and far cheaper.

  **No shim, because the survey said none was needed.** Consumers were counted before anything
  moved: juno and macer import `jazzx_sdk.handlers` not at all; jaci (16 files), k9 (5) and
  jazzx-assistant (2) import `HandlerContext` and `BaseHandler`, which have not moved. Exactly one
  external import touches the identity half -- `default_request_headers`, in one jazzx-assistant
  test -- so a compatibility layer would have existed for a single line in a single test.

  The halves turned out to share no code at all, only a file: the one apparent crossing,
  `security_context`, is a `HandlerContext` *field* carrying the inbound value, not a call into
  that machinery. So neither module imports the other. 22 files inside this repo were repointed,
  including four tests that reached for the module object rather than importing names.

  `identity` joins the tier contract in the bottom layer. The debt list went from 30 pairs to 29 --
  the split was about making the tiers nameable, not about breaking the cycle, and it is honest that
  it barely moved that number.

- **The SDK's tiers are declared and enforced, and the measurement says they are not tiers yet.**
  `.importlinter` guarded only package boundaries (`jazzx_sdk` never imports `plato`, `common`
  imports neither). Nothing constrained direction *inside* `jazzx_sdk`, so the core/queue/server
  split lived in prose and a lower tier importing its host was a review-time question at best.

  What the measurement found, before any contract was written:

  - **26 of the SDK's top-level modules form a single import cycle** -- `fabric`, `agents`,
    `server`, `clients`, `conductor`, `modes`, `llm`, `tools`, `handlers` and 17 more are all
    mutually reachable. No ordering of layers can pass outright against that.
  - **39% of cross-package imports (241 of 605) are deferred inside functions.** That is what keeps
    the cycle from failing at import time, and why it went unseen.
  - `handlers.py` contains no handlers. It is security context, header propagation and
    `CallerIdentity` -- the third most depended-upon module in the SDK (14 importers, behind
    `fabric` at 23 and `concurrency` at 15) under a name that says nothing about which tier it is.
  - `observability/trace_routes.py` imports `server.governed_http`: server-tier code inside a core
    package.

  The contract that landed is a **ratchet**, not a clean bill of health: seven tiers ordered by the
  measured direction of dependencies rather than by intent, and 30 wrong-way pairs registered as a
  debt list that may only shrink. It passes today and any *new* cross-tier edge fails CI -- verified
  by adding a `fabric -> server` import and watching it break, then removing it. The ordering itself
  was iterated against the graph: the first attempt (written from the intended architecture) had 32
  violating pairs, and correcting it to the real direction cut that to 27. `mcp` moved into the
  `agents` tier for the same reason -- it exposes agent capabilities, so it is a peer, not a layer
  below.

  One registered edge is explicitly not debt: `handlers -> client_layer` exists only under
  `if TYPE_CHECKING`, for a single annotation. import-linter reads the AST and counts it, and
  through it everything `ClientLayer` touches -- which would report the SDK's identity primitives as
  depending on llm, agents, mcp and fabric, which at runtime they do not.

  Known limitation, worth stating: the debt entries are per top-level *pair*, so a new import
  between two modules already on the list is not caught. Tightening that means shrinking the list,
  which is the point.

- **Two suite warnings fixed, one left standing with its cause named.** `plato/alembic.ini` now
  declares `path_separator = os` instead of inheriting the legacy split on spaces, commas and
  colons -- which alembic warns is going away, and which would silently fragment the repo-root path
  under a directory containing any of those characters. `test_transaction_context.py` reads
  `model_fields` off the model class rather than an instance, deprecated in pydantic 2.11 and gone
  in v3; it was the only instance-level use in the repo.

- **`DbStore.dispose()`, and the suite stops leaking sqlite worker threads.** `DbStore` opened an
  `aiosqlite` engine lazily and offered no way to close it, so each of the ~50 stores the suite
  builds left a worker thread bound to the loop it was created under. When such a store was
  collected -- often several files later -- the thread woke to a closed loop and raised, and pytest
  reported it against whichever test happened to be running. No file emitted it alone, which is
  what made it hard to place.

  `dispose()` closes only an engine the store opened itself: a `common.core.db` factory or an
  injected sessionmaker belongs to whoever built it, and closing those from here would drop
  connections other callers still hold. It is idempotent and a no-op on a store that never resolved
  an engine.

  A disposed store refuses reuse rather than reopening. Reopening reads as harmless and is not: on
  the `:memory:` default a second engine is a different, empty database, so the next query fails as
  `no such table` with nothing naming the dispose that caused it.

  Tests get it through an autouse fixture that tracks instances, rather than 49 inline call sites
  opting in one by one -- none of them sit in a fixture, and one written tomorrow would not opt in.
  The tracking holds **strong** references: a store that falls out of scope mid-test is exactly the
  one that leaks, and a `WeakSet` (tried first) let it be collected before teardown saw it, which is
  why the first attempt changed nothing. Verified causally: 0 warnings with the fixture, 10 with it
  switched off.

- **A gateway without routing no longer breaks model resolution.** `resolve_agent_model_name` read
  `gateway.task_routing` directly, while the branch above it already treated "no gateway" as "no
  routing". `gateway` is duck-typed, so any stand-in that is not an `LLMManager` -- a scripted
  manager wired into a local host, say -- raised `AttributeError` from inside model resolution and
  surfaced as a 500 on the first agentic turn. It now reads through `getattr` and falls through to
  the default, which is what "no routing" already meant one line earlier.

- **`scripts/plato_wiring.py`: Plato runs on a workstation.** The manifest's `allowed_skills` is
  derived from the profile's own `skills/*.yaml`, for the same reason the stub tool catalog is
  derived: a hardcoded mirror of a sibling checkout drifts silently when a skill is added, and
  fails the manifest write with a bare `ValueError` when one is renamed.

  The stubs are real `FunctionTool` objects, not bare callables. `Agent(tools=[...])` accepts a
  plain function and stores it unwrapped, so the mistake survives construction and every turn that
  never reaches a skill; it fails later inside `Converter.tool_to_openai` with "Hosted tools are not
  supported ... Got tool type: `<class 'function'>`". Verified at that exact call: a plain callable
  raises there, and all 11 stubs now serialise. `@function_tool` derives its schema from a
  signature, which a stub generated per tool name has none of, so the schema is declared explicitly
  and left non-strict -- the real skills call these with argument sets this file cannot know, and a
  strict schema would reject the call rather than stub it.

  `_assemble_pack` refuses to `rmtree` a directory it did not create, checked by a marker file it
  writes. `PLATO_LOCAL_CACHE` is a path a person types, and the unconditional delete would have
  taken whatever they pointed it at, and the marker is written *before* the copy so a boot
  interrupted partway leaves a directory the next boot still recognises as its own.

  The manifest write runs under a throwaway `asyncio.run` loop, opening the engine under a loop
  that closes immediately -- left alone deliberately, because plato does the same thing to the same
  store moments later, when `check_schema_or_report` runs `assert_schema_current(db)` before
  uvicorn starts. An earlier revision seeded through a separate short-lived store to keep the
  runtime's engine pristine; it bought nothing for that reason and is gone. File-backed sqlite
  serves correctly afterwards, verified against a running server.

  Plato ships no default `PLATO_WIRING`
  on purpose -- a container that boots into a stub looks healthy to an orchestrator -- which is
  right for a deployment and a wall for anyone who wants to watch it serve. This supplies one:
  sqlite on disk, `ScriptedLLM`, and stub tools derived from whatever the profile's skills declare
  rather than a fixed list, so a tool added to the profile is covered instead of breaking the boot.

  The database is built by running the real alembic tree, not `create_all`: Plato refuses a
  database carrying no revision stamp, and satisfying that check any other way would be lying to
  it. A local boot therefore exercises the migrations the way a deployment does.

  Tracked in `scripts/` rather than gitignored under `scripts/local/`, because the wall is not
  workstation-specific -- every clone meets it -- and `scripts/` is outside `packages`, so nothing
  reaches a consumer's install.

  **Stated plainly because the wiring makes it look free: a chat turn calls the real OpenAI API.**
  `ScriptedLLM` answers the scope guardrail and the non-agentic path, but this profile's turns take
  the agentic path, which builds an OpenAI agent directly rather than going through `llm_manager`.
  Measured against a live server: sessions, `/health` and `/v1/info` need no key; one turn was ~7k
  input tokens on `OPENAI_API_KEY`, and with no key it fails outright rather than falling back to
  the script. Boot prints which state you are in.

- **A guard so CI's extras cannot silently fall behind again.** `tests/test_ci_extras_coverage.py`
  asserts every extra `pyproject.toml` declares is either installed by the workflow or named in an
  `EXCLUDED` map with the reason it is safe to leave out. Adding an extra now forces that decision
  rather than defaulting to silence, and three companion checks keep the map honest: nothing may be
  both installed and excluded, `EXCLUDED` may not name an extra that no longer exists, and the
  gitignored pre-push hook's `CI_EXTRAS` must match the workflow (skipped where the hook is absent).

  Deliberately not an import scan. The `gemini` failure came from a *lazy* import inside
  `jazzx_sdk.agents.gemini_provider`, not from anything the test files import at module level, so no
  static scan of `tests/` could have seen it -- and reproducing it needs a CI-shaped install, which
  a test running inside the developer's own environment cannot conjure. The list itself is what is
  checkable exactly and cheaply.

  `greenlet` gets its own check, because it is a main-group dependency with a platform marker
  rather than an extra: nothing in the extras logic can see it, and deleting its declaration would
  look harmless on any machine that already carries the package. That check evaluates the marker
  against an `arm64` environment rather than looking for the string, so an unconditional
  `greenlet = ">=3.0.0"` -- which covers Apple Silicon and more besides -- passes. A guard that
  reddened on the safer declaration is one somebody deletes.

  The `bpmn` exclusion is the one reason mechanically checkable from data the file already parses,
  so it is checked: `extras["bpmn"] <= extras["plato"]`. If `bpmn` ever gains a package `plato`
  lacks, "adds nothing" stops being true, and an exclusion that quietly became wrong is worse than
  one never written down.

  Each was verified by reintroducing the drift it targets and confirming it fails: dropping `plato`
  from the workflow, pointing the hook at a stale set, marking an installed extra as excluded,
  naming an extra that does not exist, deleting greenlet outright, and narrowing its marker to
  SQLAlchemy's own platform list -- plus the converse, that the unconditional declaration passes.

  The workflow lookup anchors on the `run:` line rather than the first `--extras` in the file --
  roughly fifty lines of prose about extras sit above it, and an example command quoted there would
  otherwise be compared instead of the real one, with every assertion still green.

- **`greenlet` is declared for Apple Silicon, which SQLAlchemy's own marker misses.** SQLAlchemy's
  async layer requires greenlet and declares it, but its marker lists `aarch64` -- Linux's name for
  the chip -- and not `arm64`, macOS's name for the same chip. A fresh `poetry install` on Apple
  Silicon therefore omits it, and 178 tests die with `ValueError: the greenlet library is required`.
  Nothing warns; the package simply is not there.

  It only surfaces on a rebuild. Any environment created before this carries greenlet from some
  earlier install and looks healthy, which is why a working machine is not evidence.

  Declared for `arm64`/`ARM64` only -- the spellings SQLAlchemy's marker misses -- so no platform
  resolves it twice; the lock change is two lines, appending those two values to the existing
  marker. Verified by uninstalling greenlet, confirming it was gone, and re-running `poetry install`:
  it comes back from the lock. Removable once SQLAlchemy's own marker covers macOS.

- **CI installs the `plato` extra, so the BPMN resolver tests run and `alembic` stops being
  accidental.** `common/refs/extract.py` imports `defusedxml`, which only the `bpmn` and `plato`
  extras supply, so all 22 tests in `test_bpmn_resolver.py` failed at import in a CI-shaped
  install -- the same shape as the `gemini` gap: a branch adds tests needing an extra, CI's list
  does not move with it. Found by rebuilding the local venv from scratch, which is the only way it
  surfaces; an older environment carries the package from some earlier install and looks fine.

  `plato` rather than the narrower `bpmn` because it also declares **`alembic`**, which nothing
  else in CI's list does. Plato's migration tests were getting it transitively from `mlflow`, so
  dropping the mlflow extra would have broken migration tests with nothing naming the connection.
  Verified rather than assumed: uninstalling both packages and re-running `poetry install` with
  this extras list brings back `alembic 1.18.4` and `defusedxml 0.7.1` from the list itself.

- **The Gemini provider tests run in CI instead of failing, and the ones that need no SDK keep
  running without it.** CI installed `mcp templating finance pptx mlflow` but not `gemini`, so
  `google.genai` was absent and tests died at the first lazy `from google.genai import types`.

  The SDK modules were already right -- they import `google.genai` inside the functions that need
  it, so importing `gemini_provider`/`gemini_native` costs nothing without the extra. Two changes
  sit on top of that:

  *CI installs the `gemini` extra.* One package, and the tests are offline (fake key, stubbed
  client). Without it, `GeminiProvider` and `GeminiNativeModel` -- both shipped and exported -- had
  no CI coverage at all. The extra lands *with* the marks rather than instead of them: before this,
  a CI without it failed outright, and marks alone would have turned that into a green run
  verifying nothing -- a skip reading as a pass, the failure the `mlflow` extra was added to fix.

  *The guard is a per-test marker, not a module-level `importorskip`.* Only 21 of the 31 tests build
  requests through `google.genai` types; the other 10 exercise `_usage`, `_output_items`,
  `resolve_model` and the `AgentExecutionService` registry and touch no Gemini SDK type. Skipping
  the file wholesale would have stopped those 10 running for anyone installed without the extra --
  turning tests that passed into tests that no longer run. Which 21 need it was determined by making
  `google.genai` unimportable and reading the failures, not by inspection.

  Verified in both installs: with the extra, 31 pass; without it, 10 pass and 21 skip with a stated
  reason. The lock is bumped in the same commit so CI tests what was verified: it pinned
  `google-genai` 2.8.0 while this work was done against a newer local install, which is exactly the
  gap that makes a local pass meaningless. `poetry update google-genai --lock` moved two packages --
  `google-genai` 2.8.0 -> 2.21.0 and its dependency `google-auth` 2.55.0 -> 2.57.0 -- and the 31
  tests were re-run against 2.21.0 rather than assumed compatible. The pre-push hook's `CI_EXTRAS` is updated in the same breath -- it had drifted when
  `mlflow` was added, and that drift is what let a local pass look like a CI pass.

- **The curator tests exercise the supported synthesis path, not the deprecated one.**
  `synthesize_bucket` has taken `agents=<AgentExecutionService>` since `llm=` was deprecated, but
  five tests still called it the old way, so every suite run carried five `DeprecationWarning`s.

  The warnings were the symptom; the problem was where the coverage sat. Everything substantive --
  applicability, feedback/attribution/evidence provenance, the red-teaming batch, draft persistence
  -- ran through the path scheduled for deletion, while `agents=` had a single test. When `llm=`
  goes, those tests would have gone with it and taken the coverage rather than moving it.

  Those five now use `agents=` through the existing `ReasoningAgent` monkeypatch seam (moved above
  the tests in `test_curator_synthesis.py`, with a local stub added to
  `test_learning_candidate_adapter.py`). The deprecated path keeps exactly one test, which asserts
  the warning fires via `pytest.deprecated_call()` -- so the shim stays covered until it is removed,
  and no warning leaks. Both files pass under `-W error::DeprecationWarning`. Suite warnings 20 -> 15.

- **The last pydantic v1-style `class Config` is gone.** `FabricConfig` still declared its settings
  through the inner class pydantic v2 deprecated and v3 removes, so every test run carried a
  `PydanticDeprecatedSince20` warning. It is now `model_config = ConfigDict(use_enum_values=True)`,
  and it was the only one left in `jazzx_sdk` -- every other model had already migrated.

  `use_enum_values` is carried across verbatim and noted in place, because what it changes is
  subtle: it alters the *stored* type, so `retrieval_mode` holds the string `"strict"` rather than
  `RetrievalMode.STRICT` and `model_dump()` emits a plain string. Comparisons are unaffected --
  `RetrievalMode` is a `str, Enum`, so `mode == RetrievalMode.STRICT` holds either way -- which is
  precisely the trap: dropping the setting would look harmless at every in-repo call site while
  changing the serialised shape for anything persisting or transmitting the config.

- **The open MLflow SSRF advisory is recorded where the floor is declared.**
  GHSA-h7x2-h6g9-p789 / CVE-2026-71211 (unvalidated `api_base` in MLflow's AI Gateway) has **no
  fixed release**: it covers `>=3.13.0,<=3.15.2` and 3.15.2 is the latest published version, so
  there is nothing to bump to, and dropping below 3.13 reinstates the webhook-delivery SSRF this
  floor was raised to close. It is also not reachable from japes, which uses only mlflow tracking
  (`MlflowClient`, entities, runs) and runs no gateway. Documented rather than silently carried, so
  the next person to see the alert does not re-derive the analysis.

- **The real-assistant test no longer hardcodes a workstation path.**
  `tests/test_plato_packs.py` pinned the `jazzx-assistant` profile to an absolute path under one
  developer's home directory, so on every other machine the skip read as "the sibling is absent"
  when the real reason was "you are not that person". It now resolves the sibling relative to this
  checkout -- the `<workspace>/japes`, `<workspace>/jazzx-assistant` layout every JazzX repo already
  uses, so the default needs no configuration -- with `JAPES_ASSISTANT_PROFILE_DIR` to override,
  matching the existing `JAPES_REAL_PACKS_DIR` convention. The skip reason now names the path it
  looked at and the variable that changes it.

- **Entity write provenance verified against the landed Knowledge Hub contract.** KH `93ea215`
  ("add metadata JSONB column") added an optional, free-form, client-owned `metadata` JSONB column
  on `entity`, exposed on `EntityCreate`/`EntityUpdate`/`EntityRead` under the wire name `metadata`.
  That confirms the key this client already wrote to, so `WRITE_METADATA_KEY` stops hedging about a
  spelling it had to guess. It still rides on `additional_properties` because japes' vendored
  `EntityCreate` predates the change; the serialised body is byte-identical to what a regenerated
  client produces, so regenerating `client-api` is a drop-in rather than a migration.

  **Updates merge, they do not replace** (KH's `_merge_metadata_on_update`): adding
  `updated_by_process_id` leaves `created_by_process_id` in place. The mock now merges on both
  update paths, and the docstring that claimed the opposite -- written when the contract was still
  unknown -- is corrected. Omitting the key leaves the column untouched; this client sends omission
  for an empty dict too, so KH's explicit-null "clear the column" case is deliberately not
  expressible, the safe default being to say nothing.

  The test that pinned the old behaviour reused a single metadata key, where merge and replace give
  identical results and the assertion proved nothing. It now uses distinct
  `created_by_process_id` / `updated_by_process_id` keys, covers a repeated update (the rerun case),
  and fails if the mock reverts to overwriting.

  **`update_entity_json` no longer takes `metadata` at all.** KH's json-patch endpoint accepts only
  `path`/`value`/`updates` plus the `x-user-id` header, and its body has no `metadata` field now or
  after client regeneration -- so the parameter was accepted and dropped on every call. An earlier
  revision of this work argued the opposite (that omitting it would make json-patch "the one write
  that records nothing"); checking the endpoint rather than reasoning by symmetry showed the
  parameter itself was the thing recording nothing. A parameter that silently discards what it is
  given is worse than its absence, so it is gone and the docstring says why.

  japes does not interpret the object's contents: the process-id keys belong to the caller, so KH
  and its callers can add keys without japes changing.
- **Fixed: a successful `create_triple` could not return.** `create_entity` returns the entity dict,
  or None when the write failed -- never an HTTP `Response`. `create_triple` checked
  `hasattr(response, "parsed")` and then read `response.status_code`, so a *successful* create
  failed the first probe, fell into the error branch, and raised `AttributeError: 'dict' object has
  no attribute 'status_code'`. The success path could not return at all. Nothing exercised it, so
  the bug sat behind a green suite; a failure now raises naming the triple that failed.

- **Fixed: the MCP `knowledge_hub_create_entity` tool reported failures as successes.** The same
  shape confusion, found by checking the family rather than the one instance. Both the `parsed` and
  `status_code` probes were False on failure, so the tool fell through to `json.dumps(None)` and
  answered the literal string `null` -- an ordinary successful result, as far as whatever drives the
  MCP session can tell. It now returns an error object naming the entity and collection.

  The existing test asserted `status_code == 201` against a Response-shaped `MagicMock` the real
  client never returns, so the fixture had encoded the bug rather than catching it. It now returns a
  dict, and a failure-path test was added. `test_policy_store.py` had the same drift -- a
  Response-shaped `create_entity` beside a dict-returning `create_collection` in one fixture -- so
  it exercised only the canonical store's tolerance arm and never the path production takes.

- **Fixed: `check_kh_connection.py` reported a successful entity create as skipped.** The same
  shape confusion in the script whose entire job is saying whether KH works. It read
  `response.parsed` off the dict `create_entity` returns, raising `AttributeError` straight into a
  bare `except` that logged "create_entity (person_result) skipped" -- so a healthy KH looked
  degraded, and the HTTP-status branch below it was unreachable.

  The canonical stores keep their `.parsed` arm deliberately: `KnowledgeHubLike.create_entity` is
  declared `-> Any`, so unlike the concrete client there is no contract there saying a Response
  cannot arrive, and the arm is tolerance across an untyped protocol boundary rather than dead code.

- **`KernelLLMModel` conformed to the protocol the runner actually calls — both halves were
  broken.** Found while using it as the template for the native Anthropic model, and broken in the
  same way twice: the adapter returned what read like a reply rather than what `agents.Model`
  defines.

  `get_response` built its `ModelResponse` from `content=` / `raw_response=`, neither of which is a
  field on it — required are `output`, `usage`, `response_id`. Every call raised a pydantic
  `ValidationError` before the runner ever saw a reply, so the Kernel path could not have been
  exercised through `Runner` at all. It now returns real output items and a real `Usage`, with a
  reply that reports no usage counting zero rather than `None`: the turn still happened, and a cost
  tracker summing `None` crashes where summing zero is a known gap.

  `stream_response` carried `# TODO`s and did `yield response` — a `ModelResponse` where a stream
  event belongs, so the type error surfaced somewhere downstream in a caller with no way to know
  why. Kernel's LLM API has no streaming endpoint, so it now runs the blocking call and emits the
  sequence the runner expects around the result: created, one text delta, completed. Not
  token-incremental, and the docstring says so — but a stream of the right shape, and an empty
  answer still opens and closes it rather than hanging a consumer waiting on `completed`.

- **An assertion now carries where it came from, typed: `Triple.coordinate`.**
  `source` and `section` are strings a reader has to re-parse and a machine cannot navigate --
  "page 4", "4" and "p.4" mean one place and none of them resolves back to it. The document stack
  already resolved a real `SourceCoordinate` per field (a Page/Section/Cell locator plus a content
  hash), and `emit_assertions` was flattening it to those two strings at the moment the assertion
  was built: the typed value existed and was discarded one layer before anything could use it. It
  is now carried, not re-derived. `source`/`section` are untouched, for display and for every
  caller already reading them; the field is optional because a merged triple has several origins
  and an asserted one may have no document at all.

  Verified across every hop that could quietly drop it -- `CaseGraph.build`, `model_dump` +
  revalidation, and `merge_subjects` -- because a flag is worth its weakest hop, and this is the
  boundary that ate `truncated` and then `cost_is_upper_bound`.

  **Where the chain stops is documented rather than left to be discovered.** The Knowledge Hub
  write contract (`create_triple`/`bulk_create_triples`) is a flat six-field projection, so
  persisting through `KGStore` drops the coordinate silently. Closing that needs the KH API to
  accept it -- a cross-service change, not one this layer can make alone -- so `add_triples` now
  says so in the place someone would be about to rely on it.

  `triple.py` called itself a leaf module with "no fabric/runtime imports"; it now imports
  `fabric.canonical.evidence`, which is stdlib-and-pydantic only. The docstring says what the one
  dependency is and that the real constraint -- no store, client or runtime import -- still holds,
  rather than leaving a claim that had quietly become false.

  In the policy pipeline this closes the deferral its own docstring recorded: `ClauseSegment` now
  resolves a `SectionLocator`-based coordinate (a clause's address is its section marker; the page
  it falls on is typesetting), an extracted rule cites its clause through `Rule.citations`, and a
  proposal carries the clause text as its `excerpt` -- because a reviewer ruling on an extracted
  rule needs the sentence it came from, which is the only question being asked of them.

- **`lint_pack` no longer reports a pass because it had nothing to check with.**
  A pack with no ontology got a `no_ontology` *warning* and an immediate return -- before its
  policies were counted or examined. So a pack whose every rule was unverifiable came back
  `ok=True, rules=0`: rules reported as *absent* rather than as *unchecked*, and a clean bill on a
  governance asset nobody had looked at.

  Found by pointing the machinery at a real pack rather than by reading it. jaci's `dscr-core` has
  41 authored eligibility rules and declares no ontology, and the report said `ok=True, rules=0`.
  It now counts what it was handed and raises `unverifiable_rules` as an **error**, so `ok` is
  False and the count is 41. A pack with no ontology *and* no policies stays a warning: nothing was
  asked of the lint, so nothing went unanswered.

  This is the failure `pipelines.policy_extract`'s own `lint_step` was written to avoid -- "a lint
  that passes because it had no vocabulary is the most misleading result available" -- present in
  the function underneath it. The pipeline guarded the case; the primitive did not.

- **A policy corpus becomes a pack's rules: `pipelines.policy_extract`, and `Proposal` learns to
  carry one.** The vocabulary pipeline turns a corpus into what a domain *can say*; this turns one
  into what a domain *requires*, and they are halves of one arc -- an extracted rule is only worth
  having if the vocabulary can supply what its condition reads.

  **`Proposal` was the blocker.** `kind` was `Literal["concept", "relationship"]`, so a rule could
  not enter the queue at all. Widening it to `"rule"` makes the whole existing lifecycle -- admission
  thresholds, the persisted `ProposalStore`, the review surface, the audit trail -- apply to rules
  unchanged, rather than growing a second curation system beside the first. `Rule` is
  forward-referenced and resolved by a `model_rebuild` at the end of policy.py: `fabric.canonical.
  policy` reaches `tools/__init__` -> `graph.triple` and back into `fabric.graph`, so a module-scope
  import is a real cycle (the same one that keeps `check.py` out of `graph/__init__`), and the
  pattern mirrors periods.py -> profiles.py.

  **A Proposal is deliberately not the answer for a case graph.** A proposal changes what is true
  for every future case; a case-level finding changes what is true for one. A loan's own facts are
  never proposed -- they are asserted with evidence or refused, and their machinery is
  `Assertion.confidence`/`admit`, `Contradiction`, `Coverage`, `Refusal`, and
  `agents.adjudication` where a person must decide. Accepting a proposal writes to a *shared*
  artifact, so admitting one case's income would change the pack on the strength of a single
  document. Evidence still flows case graph -> `FrequencyAccumulator` -> proposal; the accumulator
  crossing a threshold is the boundary, and it is what keeps the two apart. Written into the type's
  own docstring, because this is the distinction the next person will be tempted to collapse.

  **Lint is a stage, not a lint.** `lint_pack`'s `unreachable_input` check already catches the
  failure that matters -- it found `FCCR` reading `taxes` where the ontology declares `tax_expense`.
  An *extracted* rule is far likelier to invent a name than an authored one, so the periodic audit
  becomes a gate: the gap is reported on the run that proposed it, beside its evidence, while
  somebody is still looking. It reports and never repairs; binding `taxes` to `tax_expense` on a
  name-similarity guess would be a wrong auto-binding on a policy input, which is worse than an
  honest gap. Without a pack the stage reports nothing rather than passing -- a lint that "passes"
  because it had no vocabulary is the most misleading result available.

  **Conditions come out `natural_language`, deliberately.** A one-shot parse from prose into an
  `expression` is where extraction quietly invents thresholds. Promotion to a deterministic kind is
  a separate reviewable act once the thresholds are actually identified, so a half-understood rule
  degrades to "stated but stochastic" rather than to a confident wrong number. Extraction itself is
  a seam (`ObligationExtractor`) -- the pipeline owns the governance around it, which is the part
  that is the same whatever the extractor is. `ModalClauseExtractor` is a labelled floor for tests,
  and declares `reads=[]` rather than guessing field names it cannot identify.

  Segmentation is clause-level, not page-level: a rule's boundary is a section marker, and the page
  it falls on is an artifact of typesetting. Text with no markers comes back as one segment rather
  than none -- an unmarked policy is still a policy. "should" is not an obligation; admitting
  advisory language as a rule would overstate what the document requires.

- **The remaining three signature annotations that resolved nowhere.** `Path` (twice) and
  `DirectoryResult` in `agents/document/agent.py` -- the same defect as the five closed in 2.4.9,
  left with this release because the module carries the KG `emit_assertions` work.
  `DirectoryResult` joined the existing `document.schema` import rather than opening a second one
  from the same module.

- **An unpriced cost now says it is a ceiling: `cost_is_upper_bound` on both tiers.**
  An uncatalogued model costs at `DEFAULT_PRICING`, which is deliberately the *most expensive*
  card, so the figure over-reports rather than under-reports. `compute_cost` warns once per model
  at the point it happens, but a warning is not carried on the result: everything downstream saw a
  float indistinguishable from measured spend. On 100k/50k tokens that float is $10.50 where
  `gemini-2.5-flash` is $0.155.

  The flag rides beside the number on `AgentExecutionTrace`, `ProviderResult` and `LLMResult`, and
  says what is true of it: `DEFAULT_PRICING` being the top card makes the cost a genuine upper
  bound, safe to budget against but not to bill, report as spend, or average into a rate. The point
  is the aggregate — one unpriced model in a run makes the whole total a ceiling, and a consumer
  can now notice that instead of publishing it.

  It is set through one `record_cost(trace, model, **buckets)` helper rather than a second line at
  each of the four provider sites, because the pair must not come apart: a `cost_usd` written
  without its provenance is a guess wearing the costume of a measurement. The buckets differ by
  provider (OpenAI's `reasoning_tokens`, Anthropic's `cache_creation_tokens`) and pass straight
  through. On the LLM tier the flag is derived from the name that was actually costed — the
  tier-adjusted one for a `flex_`/`batch_` call — so it cannot disagree with the number beside it.

  **Propagated through `LLMResult`, not left at the provider.** `LLMResult.truncated`'s own
  docstring records this failure already: computed correctly by every provider, then dropped at
  exactly that dataclass boundary. A flag is worth its weakest hop, so a test asserts every
  `LLMResult` construction in the manager carries it — the primary path and the fallback path —
  rather than pinning one instance.

  Five test doubles hand-rolled `SimpleNamespace` in place of `ProviderResult` and broke on the new
  field. They now construct the real dataclass, which is the actual fix: a lookalike double stops
  matching the contract silently, so the next field added breaks the tests instead of the code
  under test. That is the second time this shape has bitten, after `truncated`.

- **Gemini reaches the agent tier: `AgentExecutionService.gemini`, and a real tool loop behind it.**
  AES already *inferred* `gemini` from a model name and then refused it, with a hint saying to use
  OpenAI or Anthropic for anything with tools. That was the last asymmetry in the provider story —
  three backends, two of which could run an agent and one that could only answer.

  `agents/gemini_provider.py` implements the same `run` contract its siblings satisfy: same
  arguments, same `AgentResult`, same `AgentExecutionTrace`, same shared `compute_cost`. A caller
  writing against the generic tier cannot tell which provider answered from the shape of what comes
  back, which is the entire promise of a generic tier. The one place the loops genuinely differ is
  that Gemini matches a tool result to its call by **name** rather than by a call id.

  A failing tool is reported to the model as its result rather than raised — the model asked for
  something that did not work, and telling it so is what lets it recover, where raising ends a turn
  it could have finished. Usage accumulates across rounds, because a turn's cost is every round it
  took; `thoughts_token_count` counts toward output because it is billed.

  All three refusal paths now share one message — `Unsupported provider: X. Supported: openai,
  anthropic, gemini.` — where a third site had been raising its own hardcoded string, so a caller
  who named a bad provider *with* a model got different words than one who named it without. The
  message names the supported set and stops there, and that is the SDK-level stance rather than a
  tidying preference: reaching a model is the smallest part of running one usefully. Pricing,
  guardrails and the per-model request quirks (`unsupported_request_params`, caching, reasoning
  settings) are all keyed by model family, so a model japes does not know is a model it cannot cost
  or constrain — an uncatalogued one falls back to `DEFAULT_PRICING` and bills 100k/50k tokens at
  $10.50 where `gemini-2.5-flash` costs $0.155. Knowing the family is the precondition for the rest
  of the SDK doing its job, and an adapter added on purpose when something is actually needed is
  worth more than a passthrough that makes every provider look half-available. Existing tests used **gemini**
  as their example of an unsupported provider — the set that message rejects is exactly the set
  with no adapter, and it shrinks by one each time an adapter is written, so they moved to
  `kimi-k3` and `vertex`.

  The LLM tier's own refusal was misdirecting in the same way, and worse: `_get_provider` reported
  `Provider kimi-k3 not enabled` for a provider it has no adapter for, sending someone to look for
  a switch that does not exist, while the `Unknown provider` line beneath it was unreachable —
  `_provider_config` holds exactly the four constructible names, so the enabled-check caught
  everything first. Those are two different problems (**unsupported**: nothing you can do;
  **supported but disabled**: `local` with `enable_local=False`, genuinely a switch) and they now
  say so separately, with the supported set read off the config so it cannot drift. The dead branch
  became the wiring assertion it actually is: a provider configured with no constructor.

  **Providers are strict, models are not, and that asymmetry is deliberate.** The two are
  distinguishable — `provider_for_model()` resolves a family by pattern, `is_priced()` says whether
  the catalogue knows a specific model — and they are treated differently on purpose. Provider
  support is a fact about code japes has written, so an unsupported one is a hard error. Model
  support is a fact about a catalogue that is always behind: `gpt-5.4-mini` is priced,
  `gpt-5.9-turbo-preview` is not, and both route to OpenAI correctly because the pattern matches
  the family rather than an enumerated list. Gating on the catalogue would break every new model on
  the day it ships, so nothing does. The real cost of an uncatalogued model is not a refusal but a
  silent one: it prices at `DEFAULT_PRICING` and overstates by orders of magnitude, which
  `compute_cost` already warns about at the point it happens.

  **The provider story, whole:** four backends (OpenAI, Anthropic, Gemini, Kernel) behind two
  layers japes owns — `AgentProvider` for the agent tier's loop, `agents.Model` for the Agents SDK
  runner — with `resolve_model` dispatching and `RetryingModel` decorating any of them. What LiteLLM
  offered was one interface over many providers; what it cost was a dependency pinning
  `openai<3.0.0` and translating in a layer japes did not own. The equivalence a LiteLLM user should
  check is exactly this: one `run` contract, one trace shape, one cost model, and per-provider
  quirks handled where they are visible.

- **`GeminiNativeModel`: the last provider off LiteLLM.** `google-genai` was already an optional
  dependency here serving `GeminiProvider`, so the layer being removed was never fetching anything
  the SDK could not fetch itself — it was translating, and this does the same translation one hop
  closer in. Blocking, streaming and a real tool call all verified against the live API.

  **Two mismatches that fail silently rather than loudly, which is why they are pinned.** Gemini's
  assistant role is `model`; sending `assistant` does not error, it makes the model read its own
  previous turns as the user's and answer accordingly. And Gemini identifies a tool result by the
  function's **name** where Responses uses the `call_id` of the call it answers — nothing in a
  `function_call_output` carries that name, so the mapping walks the input in order and remembers
  what the earlier `function_call` was called.

  Gemini streams whole parts rather than opening and closing a block the way Anthropic does, so the
  item lifecycle is synthesised: the first chunk carrying text opens the item, later chunks delta
  into it, and it closes when the stream ends. A consumer sees one shape whichever provider
  answered, which is the point of doing this at the model layer.

  Usage needed care: Gemini counts `thoughts_token_count` inside `total_token_count` but **outside**
  `candidates_token_count`, so output is the sum of the two — reporting candidates alone understates
  what the turn produced. Verified against a live response reporting 9 / 1 / 24 / 34.

  **LiteLLM now serves one thing only:** an explicit `litellm/<provider>/<model>` name — a genuine
  passthrough for a provider japes has written no adapter for, including Vertex AI's
  project/location routing, which a bare model name cannot express. Dropping the extra is now a
  question about that passthrough rather than about Claude or Gemini, and dropping it lifts the
  openai-agents ceiling its `openai<3.0.0` pin imposes.

- **The Claude catalogue, rebuilt from the API rather than from memory.** Five models added
  (`claude-opus-5`, `claude-sonnet-5`, `claude-opus-4.7`, `claude-opus-4.6`, `claude-fable-5`) and
  two existing rows given the cards they lacked (`claude-opus-4.5`, `claude-sonnet-4.5`). Limits and
  capabilities come from `GET /v1/models`, which reports `max_input_tokens`, `max_tokens` and a
  capability object per model; rates from the pricing page. Nothing was recalled — the one existing
  row that overlapped, `claude-opus-4.8`, matched the fetched rates exactly, which is what made the
  field mapping trustworthy.

  Provenance records the sources and the date and deliberately claims **no human reviewer**: these
  are machine-read and unreviewed, and signing them off as reviewed would be the kind of false
  attribution the block exists to prevent. `claude-fable-5` is documented as current but 404s on the
  account used to probe, and its provenance says so.

- **`temperature` is rejected by Claude's adaptive-thinking models, and we were sending it.** Found
  by probing every catalogue id live: `claude-opus-5`, `claude-sonnet-5`, `claude-opus-4.8` and
  `claude-opus-4.7` answer a request carrying `temperature` with a 400 — *"`temperature` is
  deprecated for this model"* — while 4.6 and earlier accept it. Four of the nine reachable models,
  including the two newest, failed every call the native path made.

  This is the same class of thing OpenAI's reasoning tier does and which
  `unsupported_request_params` already describes per model, so the fix reuses it rather than
  hard-coding a list: the four cards declare it, and `AnthropicNativeModel` strips what the card
  names. A future model needs a card edit, not a code change. All nine reachable models now
  round-trip live.

- **A live smoke test found what a faked stream could not: our own Claude ids 404.** The catalogue
  writes a version as `claude-haiku-4.5`; Anthropic's API wants `claude-haiku-4-5` and returns a
  flat 404 for the dotted form. Nothing caught it because the LiteLLM path never sent our id
  straight through and a faked SSE answers to any string. One real call found it.
  `AnthropicNativeModel` now normalises on the way out; dated ids carry no dots and pass unchanged.

  Probing every Claude id in the catalogue against the live API turned up a second, separate
  problem this does **not** fix: five of the ten are models the account cannot reach at all —
  `claude-opus-4.1`, `claude-opus-4`, `claude-sonnet-4`, `claude-3.5-haiku`, `claude-3-haiku` — and
  the live list carries four we do not have (`claude-opus-4-6`, `claude-opus-4-7`, `claude-opus-5`,
  `claude-sonnet-5`). That is catalogue currency, and each row needs pricing nobody should invent,
  so it is reported rather than guessed at.

  The live tests are opt-in beside the existing ones (`RUN_LIVE_LLM=1` plus the key), cheap, and
  cover blocking, streaming, and a real tool call — the last being the half a fake vouches for
  least, since it is where Anthropic either accepts the tool schema we build or does not.

- **`AnthropicNativeModel`: Claude through the Agents SDK without LiteLLM in the middle.** One
  dependency sets the ceiling on the whole SDK — LiteLLM pins `openai<3.0.0` while openai-agents
  0.21+ needs `openai>=3.0.0` — for an extra exactly one consumer installs. This is the same model
  without that layer: japes' own Anthropic client wired straight to the `agents.Model` protocol.

  **Both halves are native.** `get_response` sends one request; `stream_response` reads Anthropic's
  SSE and translates it into the Responses events the runner expects. Two streams describing the
  same thing in different vocabularies — Anthropic opens a content block and deltas into it, the
  Responses API adds an output item and deltas into it — and that translation is precisely what
  LiteLLM was performing one hop further out, which is why doing it here removes the layer rather
  than duplicating it.

  Text and tool arguments both stream. Arguments arrive as JSON fragments where only the
  concatenation parses, so the call is assembled once at the block's end rather than re-parsed per
  delta; `sequence_number` increases monotonically across every branch, because a consumer ordering
  by it must never see two events claim the same slot. A `ThinkingDelta` is deliberately not
  emitted: the Responses vocabulary has no event for it here, and inventing one would put Claude's
  reasoning trace into a stream a UI renders verbatim. Anthropic reports input tokens at the start
  and output tokens at the end, so usage is merged across both — reading either alone reports a
  turn that cost nothing to send or nothing to receive.

  **Unmapped input shapes raise.** An item silently dropped is a tool result that never reached the
  model, or a turn of history that vanished — both of which read as the model behaving badly rather
  than as a missing branch. A `NotImplementedError` naming the item type is the failure that gets
  the branch written. Handoffs raise for the same reason. Malformed tool arguments do *not*: the
  model wrote them, so they surface as an empty call for the tool to reject, not an exception
  inside the request path.

  **Native is now the default.** Claude used to raise `ImportError` without the extra, leaving a
  consumer who never wanted LiteLLM unable to reach Claude at all. The remaining argument for
  keeping LiteLLM in front was that it had carried Claude in production — it has not, since the one
  consumer installing the extra is a proof of concept. `JAPES_ANTHROPIC_LITELLM=1` forces the old
  path back. The extra still serves everything else it did (Gemini, any explicit
  `litellm/<provider>` name), so this narrows what depends on it; dropping it entirely is what
  lifts the openai-agents ceiling its `openai<3.0.0` pin imposes.

- **`preserve_raw_usage`: a provider's own usage payload survives normalisation.** Not what it
  looked like from the outside. It does **not** replace the extractor's field-by-field reading —
  the snapshot it keeps is rawer, not tidier, and still has to be parsed. What it does is make a
  count survive that `Usage` has no field for.

  `Usage` models `cached_tokens` and `cache_write_tokens` and nothing else about caching, so a
  provider's own `cache_creation_input_tokens` reaches the cost tracker today only because the
  object handed over happens to still carry the attribute — an accident of which path produced it,
  not a guarantee. With this on, the SDK keeps a snapshot of the provider payload taken before it
  normalises, and `extract_token_usage` prefers it for exactly the fields normalisation drops.

  Read at the top level *and* one nesting down, because a snapshot is unnormalised by definition and
  the same count sits beside its siblings in one provider's payload and under a details object in
  another. A non-numeric value counts as absent rather than raising: a usage figure is telemetry,
  and a malformed one must not take down the call it describes. The snapshot never lowers a count
  already reported, and with no snapshot the extraction is byte-identical to before.

- **`prompt_cache_options`: a pack can say how its prompts should be cached, not just where.**
  japes already had `build_prompt_cache_key`, and cached tokens were already *measured* in the
  usage extractor and the cost tracker — but nothing could influence whether a hit happened.

  The two are complementary and the distinction is the point. `prompt_cache_key` decides **which**
  cache a turn routes to, and stays in `extra_args` because the SDK still has no field for it —
  checked, not assumed. `prompt_cache_options` decides **how** caching behaves:
  `{"mode": "explicit"}` opts a call in deliberately rather than relying on implicit prefix
  matching, and `{"ttl": "30m"}` holds the entry far longer than the implicit window. A persona plus
  a knowledge block plus a tool catalog is a long static prefix repeated on every turn of a session,
  where the gap between a hit and a miss is most of the prompt.

  Named on `build_model_settings` rather than falling through `**extra`, for the reason already
  stated there for `reasoning_summary` and `response_include`: it is a `ModelSettings` field, not a
  raw provider arg. Passed only when asked for — sending `{"mode": "implicit"}` explicitly is not
  the same request as sending no options at all — so a spec that does not set it still builds no
  settings object, unchanged.

- **`InteractiveAgentSpec.tool_name_collision`: a pack can refuse a run whose tools collide.**
  The agent composes its catalog from several independent sources — a skill registry, knowledge
  bindings, and MCP servers — none of which knows what the others named their tools. `parent_tools`
  is a plain list, so two tools sharing a name both reach the model and one of them wins; what the
  model then calls is not what it meant to call, silently.

  Set to `"error"` and the run is refused instead. The default stays the SDK's own `"warn"`, so an
  existing pack with a benign duplicate is unaffected and raising the bar is opt-in rather than a
  migration. Threaded through all three `Runner` call sites — blocking, reasoning-stream, and token
  stream — because a collision does not become acceptable because the caller wanted tokens.

  **Delegated to the SDK rather than checked here, and that is the finding**: MCP tool names are
  fetched from the server at run time, so the cross-source collision that matters most is invisible
  to anything japes could inspect while building the agent. A build-time diagnostic naming which
  sources clashed would have missed exactly the case worth catching. The `RunConfig` is built only
  when the policy differs from the default, so a pack that never sets it gets byte-identically the
  `Runner` call it got before.

- **openai-agents floor raised 0.17.0 → 0.20.0.** Eight releases behind, and the suite passes on
  the new one unchanged — 4000 tests, no code change needed. `Model.get_response`/`stream_response`
  are untouched across the range, which is why `kernel_model`, `anthropic_model` and
  `openai_provider` are unaffected.

  **The ceiling is 0.20.x, and the wall is litellm rather than us.** 0.21+ requires
  `openai>=3.0.0`; every litellm release through 1.98.0 pins `openai<3.0.0`. Verified against PyPI
  metadata rather than assumed. Worth knowing precisely, because litellm is an *optional* extra:
  the suite also passes on **0.22.0 with openai 3.6.0**, so nothing in japes blocks the newest — a
  consumer who does not install the litellm extra can resolve straight past it, which the `>=` floor
  deliberately permits. The floor is not capped; only the lock sits at 0.20.0, because the lock
  resolves every extra together.

  What 0.20 brings that we can now reach: `ModelSettings.prompt_cache_options` (we already *measure*
  cached tokens without being able to steer them, and a pack's static instruction block is exactly
  the long-prefix case), `preserve_raw_usage` (instead of scraping provider usage field by field),
  `ToolNameCollisionPolicy` (`InteractiveAgent` composes tools from a skill registry, KH and MCP
  servers, where a clash is currently undefined), and `FunctionTool.allowed_callers` — a native hook
  for the boundary the tool zero-data-retention note describes. All verified present, none wired up
  yet.

  Also: the document-analyzer example still floored at `openai-agents>=0.1.0`; raised to match.

- **A chat turn can be stopped, and stopping is not failing.** `chat.py` had no vocabulary for "a
  turn in flight was told to stop" — the closest was `GeneratorExit`, which means something else
  entirely: the reader left, nobody stopped the turn. `InteractiveResponse` gains `cancelled` /
  `cancel_reason` as a third terminal state beside `blocked` and `incomplete`, and `chat.cancelled`
  is its own metric rather than folded into `chat.failed`, so a deploy that drained cleanly does not
  read as an outage.

  **Two mechanisms, because there are two real ones.** `ChatTurn.cancel` is anything with
  `is_set()`, checked before the turn starts, before the gather, and between deltas — cooperative,
  so a barge-in closes the stream with a terminal event rather than just stopping, since a stream
  that stops is indistinguishable from a crashed one. `asyncio.CancelledError` is the hard path: it
  is recorded and then **re-raised**, never swallowed. Swallowing it would leave `task.cancel()`
  unable to stop the task, which is the one thing the caller asked for; letting it propagate
  unrecorded would file a deliberate stop as an unexplained failure.

  How a cancel *request* reaches the turn is deliberately not modelled — a second HTTP call, a
  pub/sub message to the owning worker, a shutdown handler are all the runtime's business. japes
  owns the state and the guarantees around it: the workspace is released, `on_complete` fires, and
  the metrics say what happened.

- **`chat.py` gains a pre-answer `ground` step and a per-turn workspace.** The reference chat
  pipeline was introduced as the substrate for exactly the consumers that then did not adopt it,
  and reading their turn flows says why: both do real work between routing and answering that
  `validate → gate → answer → refuse → finalize` has no place for.

  **`ground`** gathers what the turn needs before the model is asked anything.
  `InteractiveAgent` grounds itself from its knowledge bindings, and for a pack whose context is a
  retrieval query that is the whole story — it is not, when the context is several independent
  fetches from different systems, any of which can fail alone. The bindings have no way to say
  "four sources at once, and a missing one degrades rather than sinking the turn", so a consumer
  needing that orchestrates it outside the pipeline, where it stops being traced, stops being a
  stage, and stops being visible to progress. Sources are declared on `ChatTurn` as
  `label -> (thunk, default)`; `gather_degrading` already did the hard part, including its own
  in-flight progress hook at a finer granularity than the engine's per-step events. Off by default,
  and skipped for a turn declaring no sources.

  **`workspace`** holds a per-turn resource for the length of the turn and releases it however the
  turn ends. Two consumers converged on this from different domains — a scratch directory the
  retrieval and the answer both read, and a checked-out working copy reconciled afterwards — and
  neither fits a step: the resource outlives the stage that creates it, and release has to run on
  the failure and abandonment paths too. On the streaming route it is released even when the
  consumer walks away mid-stream, which is the case a plain `async with` around a yield misses and
  the one that strands a directory or a checkout.

  Both are additive: a pack that passes neither sees no change.
