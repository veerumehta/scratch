# Deferred platform patterns

**Source:** a read-only survey of `~/src/mortgage-app` (branch `main`, ~884 Python files, ~1187
commits in the trailing 30 days). Two parallel surveys, one on agents/LLM/document handling and one
on platform/infrastructure.

**Why that repo is worth mining.** It declares no dependency on `jazzx_sdk` anywhere. Unlike juno,
jaci or the assistant repos — which consume japes and therefore tend to reflect our own patterns
back at us — anything good here was arrived at independently. It is also the current *live* domain:
its needs are the ones most likely to recur as jaci takes on further domains, so a pattern that
looks mortgage-specific today may be the first instance of a shape we see three more times.

**What was taken.** One thing, shipped as 2.4.9: windowed classification for package splitting
(`tools/documents/split.py`). Everything below was deliberately **not** built.

**The bar being applied.** A pattern is built when japes has a gap something already hits, not when
a pattern is merely good. Everything here is good; none of it responds to a failure japes has
actually had. That is the whole reason for the note — so the idea survives without the code, and so
a future decision starts from "has the trigger fired?" rather than from a blank page.

---

## 1. Durable per-key coordinator

**Where:** `fulfilment-process/docs/MACER_INVOCATION_SCHEDULER.md`

One long-lived process instance per business key (there, a loan) parked on an event gateway,
consuming nothing while idle. The load-bearing idea is that **the message is not the queue**: work
is written as a durable event entity *before* a fire-and-forget wakeup is sent, so a burst of a
thousand webhooks wakes the coordinator once and it drains what is durably queued rather than
trusting delivery. Three resilience layers stack on that: **self-re-trigger** (re-check for pending
work before sleeping, loop if any — covers wakeups dropped while busy), a **non-interrupting
watchdog timer** as a backstop for a crashed sender, and a **bounded serialization retry** so only
one run is ever in flight per key, with timed-out work re-queued rather than lost. Shutdown is
drain-not-cancel: finish the in-flight run, mark the remainder ineligible with a reason, terminate.

**Why not now.** `ConductorEngine` has suspension/resume and checkpointing for a single *run*.
Nothing in japes asks for a singleton coordinator scoped to a business key that serializes bursty
external triggers. Building it would be a new orchestration primitive with no caller.

**Trigger to build.** A japes consumer needs per-entity serialization across independent trigger
sources — the shape is "many webhooks, one entity, at most one run at a time, none dropped". The
first symptom is usually a consumer hand-rolling a `processing` flag on a row and discovering it
races.

**Shape if built.** Engine-agnostic; it maps onto any queue. Sits beside `ConductorEngine` rather
than inside it, because the coordinator's lifetime is the entity's, not a run's. The durable event
log belongs in `fabric` (`entities` or `db`); the wakeup is whatever transport the service already
has.

---

## 2. Declarative config reconciliation — flags, RBAC, app config

**Where:** `config/feature_flag/`, `config/app_config/`, `fulfilment-process/.github/deploy.py`
(`deploy_feature_flags`, `deploy_configs`, `deploy_permissions`, `load_rbac_config`),
`fulfilment-process/common/resources/rbac/*.yaml`

Three git-as-source-of-truth subsystems sharing one format: a base file plus a per-environment
overlay merged by key, with `{{PLACEHOLDER:default}}` tokens resolved through an
OS-env → env-section → common-section → inline-default precedence chain. Two details are the
interesting part, and both concern *not clobbering reality*:

- **Live value wins.** Once a flag exists, deploy seeds only its initial value and thereafter
  *reports* drift between file and live rather than silently correcting it. Someone flipped that
  flag in an incident; the file is not entitled to flip it back.
- **Explicit stale markers** (`stale_flags`, `stale_permissions`) make revocation a deliberate diff
  line rather than a side effect of a full reconcile. Deleting a line means "stop managing this";
  deleting a *resource* has to be said out loud.

RBAC reconciliation is additionally idempotent against a backend that does not dedupe writes: read
live tuple counts, insert-if-missing, collapse-if-duplicated, delete-if-stale — never blind-PUT.

**Why not now.** japes has a config-audit trail and optimistic concurrency on agent definitions, but
no feature-flag or RBAC-as-code story at all. This would be a new subsystem, not a gap-fill.

**Trigger to build.** japes services need environment-varying behaviour they cannot express as
settings, or a service starts managing external authorization state across environments.

**Shape if built.** The reusable core is narrower than the three subsystems: a *declarative resource
reconciler* — base/overlay/placeholder loader, plus idempotent upsert with a stale marker and an
optional live-value-wins mode — for any deploy-time-managed external state. `fabric`-adjacent, not
in `fabric`, since the state lives in someone else's system.

---

## 3. Hybrid process test framework

**Where:** `fulfilment-process/mock/hybrid_runner.py`, `mock_platform_server.py`,
`shared_kh_store.py`, `docs/hybrid-process-test-framework.md`

Runs the **real** orchestration engine and the **real** business-logic tools against a single
lightweight local server standing in for the platform boundary, with only third-party vendor
adapters swapped for fakes. A shared in-memory store backs both the mock's HTTP endpoints and
nested tool calls, so a step and the tools it invokes see consistent state. Assertions cover
process variables, store state, **and the ordered list of calls made** — call history as a
first-class output, not a debugging aid.

**Why not now.** A large build, and japes' own suite already exercises `ConductorEngine` directly.
The value accrues mostly to *consumers* of japes, who currently have no process-level regression
option short of a full environment.

**Trigger to build.** A consumer asks how to regression-test a conductor pipeline without deploying,
or we find ourselves writing the same pipeline-level fakes a third time.

**Shape if built.** Real `ConductorEngine` + one mock standing in for `fabric`'s stores +
call-history assertions. The insight worth keeping regardless of scale: **fake exactly one boundary,
and make the call log an assertable artifact.**

---

## 4. Declarative cross-system reconciliation

**Where:** `fulfilment-process/common/resources/tools/loan_audit_apply_mapping_tool.py`, with the
vendor-routing shim `los_audit_compare_tool.py` beside it

A generic diff engine comparing an external system's data against platform entities from a JSON
`mapping_config` rather than code: a JSONPath-lite walker (`foo[*]`, `foo[?field=='x']`), per-field
type normalizers, a registry of named semantic transforms (enum remapping, masking, phone/state
normalization), instance matching by configurable keys, and per-field findings —
`MATCH`/`MISMATCH`/`MISSING_IN_A`/`MISSING_IN_B` — with severity, priority-based dedup where several
source paths map to one destination, and a rolled-up verdict.

**Why not now.** japes' `reconcile.py` solves a genuinely different problem: voting N candidate
observations of *the same* value from multi-pass extraction. Field-by-field diffing of two
heterogeneous systems is not in it, and no japes consumer needs it today.

**Trigger to build.** A consumer holds a system of record alongside its own extraction and needs
"where do these disagree" as a governed artifact — most likely the first time an audit or a
regulator asks.

**Shape if built.** Only the enum tables are domain-specific. The walker, normalizer/transform
registry and finding model are domain-agnostic. Note the adjacency: the finding model is close to
`fabric.graph.check`'s `CheckResult`, and a `MISMATCH` between systems is close kin to a
`Contradiction` between documents — worth reconciling the two rather than growing a third
disagreement vocabulary.

---

## 5. Eventual-consistency checkpoint verifier

**Where:** `qa/shared/los/verifier.ts`, `qa/tests/closed-loop/*.spec.ts`

`pollUntil(getSnapshot, expectations, timeout)` against a downstream system, returning a structured
result — attempts, elapsed, per-field mismatches — rather than a bare timeout. Used to assert that a
change actually *converged* across independently-owned async systems, not merely that the write was
accepted.

**Why not now.** Small and clean, but it answers a question japes has not been asked. Nothing has
reported a "the write succeeded but the read didn't see it" failure.

**Trigger to build.** The first time a consumer's test is flaky because a fabric write has not
propagated, or someone writes a bare `sleep` before a read.

---

## 6. Bisecting paginated fetch

**Where:** `fulfilment-process/.github/deploy.py`, `fetch_ontology_page_resilient`

A listing endpoint returns 500 for any page window containing one unserializable record. Retrying is
useless — the failure is deterministic — so the fetch bisects the failing window recursively until
it isolates and skips exactly the poison row, **while still counting it toward the window size** so
pagination does not terminate early and silently drop everything after it.

**Why not now.** Genuinely clever and genuinely narrow. japes' store layers have not hit it.

**Trigger to build.** A store listing starts failing on a page rather than on a call.

---

## 7. Post-extraction screening: dual output

**Where:** `salesai-process/common/resources/tools/screening_rules_*.py`

After extraction, deterministic Python checks run against loan-level context and emit **two parallel
outputs**: an `issues` list written for the person who uploaded the document (severity, plain
reason, actionable next step) and a `check_log` audit trail (PASS/FAIL/SKIP per check with
reasoning). The name-matching helper is a reusable nugget on its own: unicode/case normalization,
honorific and suffix stripping, a nickname canonicalization table, then exact-set → subset →
initials → fuzzy fallback.

**Why not now.** japes has confidence floors, admission and typed `Refusal`s at the extraction
layer. This is a distinct second layer — cross-checks against *case* context after extraction —
and no consumer has asked japes to own it.

**Worth keeping either way.** The dual-output shape is the transferable idea and it recurs
everywhere: **the sentence a person reads and the record an auditor reads are different artifacts,
and deriving one from the other loses something.** japes already applies this in places
(`RuleOutcome.verdict` vs `.status`, `CheckResult.outcomes` vs `.findings`); it is worth applying
deliberately rather than rediscovering per surface.

---

## 8. Write-then-read-back — methodology, already checked

**Where:** `fulfilment-process/docs/ASYNC_WRITE_READ_BACK_RACE_CONDITIONS.md`

Not code. A systematic audit naming an anti-pattern precisely — *write → re-fetch → gate on expected
state* — which is racy under eventual consistency (observed delays to 2.4s), with the fix being to
trust the write's own return value rather than re-read. Directly relevant to `fabric`'s
`WriteOutcome`: re-reading to confirm a write defeats the guarantee the write already gave.

**Status: japes is clean.** Audited on 2026-08-28 across `jazzx_sdk/` for a write followed within
six lines by a read. One hit, and it was a false positive — `BlobStore.offload`'s `put` and
`materialize`'s `get` are separate entry points, not a sequence. Worth re-running if fabric's write
paths grow.

---

## Explicitly empty — do not re-survey

The surveys found nothing worth lifting in these areas, and the finding is negative rather than
shallow:

- **No saga / compensation / rollback engine** anywhere — only error boundaries that swallow, and
  capture-before-join for parallel branches.
- **No exponential backoff, jitter or circuit breaking** anywhere in that repo. Every retry is
  fixed-count, fixed-interval. If japes wants those, they are not coming from here.
- **No synthetic data generation** — fixtures are hand-authored.
- **No multi-tenancy model** beyond per-environment config overlays.
- **No novel agent architecture.** Their agents are YAML + prompt-markdown configs executed by an
  external BPMN engine, with Python only as glue. A different mechanism from japes' agent classes,
  not a better one — the transferable thing was the *algorithm* inside their splitting pipeline,
  which is what 2.4.9 took.
- **PDF→markdown conversion was checked and dismissed.** Theirs embeds `**[Page N]**` markers in
  prose; japes resolves a typed `PageLocator` from structured DocIntel JSON
  (`analyze_result_to_json`, `convert_document_and_structure`, `ConversionRegion`). Ours is the
  better design — a marker in prose is a string a reader has to re-parse. Not a gap.
