# plan_JAPES_1_9_6_EXPERIMENT_RUN
## ExperimentRun: Run/Comparison Layer for Evaluation

**Author:** Virendra Mehta
**Repo:** `japes/` only - no JACI changes, no MACER changes
**JAPES version:** 1.9.6 (no bump - additive module addition)

---

## Background and motivation

JAPES's evaluation layer answers one question well: does a pack get the right answer on a
fixed set of cases (GoldenCase -> EvaluationHarness -> CaseResult -> EvaluationResults).
It does not answer a second, independent question that both MACER and JACI need: which
configuration performs best across a sweep of variants (model, architecture, prompt
version) evaluated against a held-fixed case set.

MACER has been answering that second question by hand since March 2026 - experiments/
contains hand-maintained markdown tables comparing four architecture variants across seven
loans. utils/run.py::create_run() generates run names, MLflow experiments, output
directories, and logs settings as params - all domain-agnostic machinery that exists only
in MACER today.

JACI's GoldenCase/EvaluationHarness was built later for PoC-stage scenarios with no
equivalent run/configuration concept. EvaluationResults.labels is the closest thing, but
it is metadata on a single run, not a comparison key across runs.

This plan adds the missing piece: an ExperimentRun object as the comparison/index layer
over runs, with an MLflow bridge mirroring the existing CanonicalTrace / mlflow_bridge.py
pattern. MACER's create_run is a requirements document, not a target API - the object
stays backend-agnostic. MACER migration is out of scope.

---

## Orthogonality: ExperimentRun vs GoldenCase

These are independent axes, not a hierarchy.

GoldenCase fixes truth: input, expected, truth_mode, label_confidence, metamorphic
grouping. It does not vary across runs - the same kyc_001 case is the same case whether
scored under gpt-5.2 or gpt-5.4-mini, baseline or kg-hybrid.

ExperimentRun fixes the system under test: model, architecture, prompt version. A run is
"this configuration, against this case set." MACER's cross-loan table proves this - the
same loan runs under four architectures. Encoding that as four near-duplicate GoldenCase
variants would conflate metamorphic variants (input changes, asserts relation to base
outcome) with configuration variants (input unchanged, system under test changes).

No changes to golden_cases/ are required by this plan.

---

## Naming: why not CanonicalExperimentRun

Canonical* marks schema-spec-governed artifacts of record that Schema Spec v1.0 defines
and Knowledge Hub persists as authoritative (CanonicalTrace, CanonicalDecision, canonical
Evidence). ExperimentRun is an index and comparison key over things that are already
canonical - it links to CanonicalTrace ids, it does not replace or audit them. Naming it
Canonical* would wrongly imply Schema Spec governance it does not have or need.

ExperimentRun lives in jazzx_sdk/evaluation/experiment/, alongside golden_cases/ and
harness/ - its actual conceptual neighborhood - not in fabric/canonical/.

---

## Pre-requisite: two bug fixes (land in the same PR, before the new module)

Both confirmed by static inspection. Both are one-liners.

**Bug 1 - EvaluatorMode builds EvaluationReport without pack_id**

File: jazzx_sdk/modes/evolve/evaluator.py:159
Problem: EvaluationReport(...) is constructed without pack_id, but
fabric/canonical/derived.py:498 requires it. Raises ValidationError at runtime for any
EVOLVE-mode caller.
Fix: inject pack_id from the enclosing harness config at the EvaluationReport(...)
construction site. Do not make pack_id optional on EvaluationReport - it is required by
design.

**Bug 2 - L3ReviewStorage key mismatch**

File: jazzx_sdk/l3_review/storage.py:75, 117
Problem: reads and writes a "cases" key; EvaluationResults serializes "case_results".
Mismatch causes L3 review to silently read an empty list.
Fix: change the key in L3ReviewStorage from "cases" to "case_results". Do not rename the
field on EvaluationResults.

---

## What this plan changes

Four additive pieces. Nothing existing is removed, renamed, or made non-optional.

---

## Change 1 - New module: jazzx_sdk/evaluation/experiment/

Create the directory and two files: __init__.py and schema.py.

### jazzx_sdk/evaluation/experiment/__init__.py

Export ExperimentRun only. Do not export the MLflow bridge here - mirror the convention
where mlflow_bridge.py is imported directly at the call site, keeping the lazy-import
contract visible.

```python
from jazzx_sdk.evaluation.experiment.schema import ExperimentRun
__all__ = ["ExperimentRun"]
```

### jazzx_sdk/evaluation/experiment/schema.py

New file. Model ExperimentRun on the same pydantic BaseModel pattern as CanonicalTrace
and other fabric canonical objects. Key design decisions:

- run_id: str, default_factory=lambda: f"run_{uuid4()}" - consistent with trace_id,
  step_id, override_id naming
- run_name: str | None = None - optional human-legible display name, display-only, never
  parsed for identity
- pack_id: str (required), pack_version: str = "dev"
- dimensions: dict[str, str] = {} - free-form configuration axes (model, architecture,
  prompt_version, ...). Generalizes EvaluationResults.labels; packs migrate at own pace
- case_set_hash: str | None = None - content hash computed by GoldenCaseLoader.hash_cases
  (Change 2). Provably comparable across runs; not free text - see rationale below
- case_set_label: str | None = None - optional human-legible label (e.g. ontology version
  string), display only, never used for comparison correctness
- status: TraceStatus - reuse from jazzx_sdk/fabric/canonical/trace.py, same import.
  Do not introduce a parallel run-status enum
- started_at: datetime (required), completed_at: datetime | None = None
- trace_ids: list[str] = [] - CanonicalTrace ids produced during this run, links not
  embeds. Not populated by this plan (see implementation notes)
- case_results_ref: str | None = None - reference to EvaluationResults artifact (path or
  external_ref), link not embed
- metadata: dict[str, Any] = {}, domain_extensions: dict[str, Any] = {}

Add two convenience methods:

ExperimentRun.start(pack_id, *, dimensions, case_set_hash, case_set_label, run_name,
pack_version, **kwargs) -> ExperimentRun
  Constructs with status=TraceStatus.RUNNING, started_at=datetime.utcnow(). Avoids
  boilerplate at the harness call site.

ExperimentRun.complete(*, status=TraceStatus.COMPLETED) -> None
  Sets self.status and self.completed_at=datetime.utcnow(). Mutates in place, matching
  the harness call pattern for other terminal-state objects.

**Why case_set_hash is not free text:** MACER exp_013-016 show a JTBD ontology version
bump that was documented only in README prose. A string field has the same failure mode -
someone forgets to bump it, or typos it, and runs claimed comparable are not. A content
hash computed from the actual case files (sorted filenames + bytes) gives a provability
guarantee free text cannot: same hash = same case set, no human discipline required.

### Acceptance check

```bash
python3 -c "
from jazzx_sdk.evaluation.experiment.schema import ExperimentRun
from jazzx_sdk.fabric.canonical.trace import TraceStatus
run = ExperimentRun.start('kyc_anthropic', dimensions={'model': 'gpt-5.4'})
assert run.run_id.startswith('run_')
assert run.status == TraceStatus.RUNNING
run.complete()
assert run.status == TraceStatus.COMPLETED
assert run.completed_at is not None
print('PASS')
"
```

---

## Change 2 - Add GoldenCaseLoader.hash_cases()

File: jazzx_sdk/evaluation/golden_cases/loader.py

Add a new static method to the existing GoldenCaseLoader class. Do not modify load_cases,
load_case, or save_case.

Method signature:
```python
@staticmethod
def hash_cases(directory: Path, pattern: str = "*.json") -> str:
```

Implementation: sorted(directory.glob(pattern)), then for each file hash filename bytes +
file content bytes via hashlib.sha256, return hexdigest()[:16]. Sort order must match
load_cases (sorted glob) so the hash is deterministic regardless of filesystem iteration
order.

The harness (Change 3) calls this once per run. Callers that want only the hash call it
separately; load_cases is unchanged.

### Acceptance check

```bash
python3 -c "
from pathlib import Path
from jazzx_sdk.evaluation.golden_cases.loader import GoldenCaseLoader
import tempfile, json
with tempfile.TemporaryDirectory() as d:
    p = Path(d)
    (p / 'c.json').write_text(json.dumps({'case_id':'c1','description':'x','input':{},'expected':{}}))
    h1 = GoldenCaseLoader.hash_cases(p)
    assert h1 == GoldenCaseLoader.hash_cases(p)
    (p / 'c.json').write_text(json.dumps({'case_id':'c1','description':'y','input':{},'expected':{}}))
    assert GoldenCaseLoader.hash_cases(p) != h1
print('PASS')
"
```

---

## Change 3 - Wire ExperimentRun into EvaluationHarness

Three files: config.py, runner.py, results.py.

### jazzx_sdk/evaluation/harness/config.py

Add two optional fields to EvaluationConfig (the existing pydantic model):

- dimensions: dict[str, str] = Field(default_factory=dict) - run dimensions passed
  through to ExperimentRun. Distinct from labels, which is retained unchanged.
- case_set_label: str | None = Field(default=None) - passed through to
  ExperimentRun.case_set_label for display only.

### jazzx_sdk/evaluation/harness/runner.py

In EvaluationHarness.run(), make two additions:

**At the top of run(), after run_id is generated, before cases are loaded:**

Import ExperimentRun and GoldenCaseLoader (locally or at top of file, whichever matches
existing import style). Compute case_set_hash via GoldenCaseLoader.hash_cases wrapped in
try/except - log a warning on failure, set hash to None, do not abort the run. Construct
self.experiment_run = ExperimentRun.start(self.config.pack_id, dimensions=...,
case_set_hash=..., case_set_label=..., run_name=self.run_id).

**At the end of run(), after results is built, before return results:**

Set self.experiment_run.case_results_ref to the output path string if save_results is
true. Call self.experiment_run.complete() with status=TraceStatus.FAILED if
results.failed_cases == results.total_cases > 0, else TraceStatus.COMPLETED. Set
results.experiment_run_id = self.experiment_run.run_id.

self.experiment_run is a new instance attribute set inside run(), not __init__ - matching
the existing pattern for self.run_id and self.start_time.

Import TraceStatus from jazzx_sdk.fabric.canonical.trace if not already imported.

### jazzx_sdk/evaluation/harness/results.py

Add one field to the existing EvaluationResults pydantic model:

- experiment_run_id: str | None = Field(default=None) - linked ExperimentRun.run_id.
  None for results loaded from older JSON or constructed without a harness.

### Acceptance check

```bash
python3 -c "
from jazzx_sdk.evaluation.harness.config import EvaluationConfig
from pathlib import Path
import tempfile, json
with tempfile.TemporaryDirectory() as d:
    p = Path(d)
    (p / 'c.json').write_text(json.dumps({'case_id':'c1','description':'x','input':{},'expected':{}}))
    cfg = EvaluationConfig(pack_id='test_pack', golden_cases_dir=p,
                           dimensions={'model': 'gpt-5.4'}, case_set_label='v1')
    assert cfg.dimensions == {'model': 'gpt-5.4'}
    assert cfg.case_set_label == 'v1'
print('PASS')
"
```

Full harness.run() integration test (requiring a conductor_factory) belongs in
tests/test_experiment_run.py - see Suggested tests.

---

## Change 4 - New file: jazzx_sdk/evaluation/experiment/mlflow_bridge.py

Mirrors jazzx_sdk/mlflow_bridge.py exactly in pattern: the ExperimentRun schema carries
no MLflow fields; this bridge is the only place that knows how to translate between them.

**Critical constraint: never import mlflow at module level.** All mlflow imports stay
inside function bodies so that importing jazzx_sdk.evaluation.experiment never hard-
requires mlflow.

Four functions to implement:

**is_sensitive_key(key: str, *, extra_patterns: tuple[str,...] = ()) -> bool**
Returns True if key looks like a credential. Match against a tuple of patterns:
"api_key", "apikey", "secret", "password", "token", "credential", "connection_string".
Case-insensitive substring match. Mirrors MACER's utils/run.py::is_sensitive_key.

**mask_value(value: str | None) -> str**
Returns "[empty]" for falsy, "****" for len <= 8, else "{first4}...{last4}".
Mirrors MACER's utils/run.py::mask_value.

**experiment_run_to_mlflow(run, client, *, experiment_name, extra_params=None,
extra_tags=None) -> str**
Creates an MLflow run for an ExperimentRun. Logs dimensions, case_set_hash,
case_set_label, pack_id, pack_version as params (unmasked - these are config labels, not
credentials). Logs extra_params with masking applied for sensitive keys. Tags the run with
japes_run_id and japes_run_name. Terminates the MLflow run if status is not RUNNING.
Returns the MLflow run_id (caller stores it in ExperimentRun.metadata["mlflow_run_id"]).

**mlflow_run_to_experiment_run(mlflow_run_id, client, *, pack_id) -> ExperimentRun | None**
Best-effort reconstruction. Returns None on fetch failure with a logged warning. Recovers
dimensions from params minus the four reserved keys (case_set_hash, case_set_label,
pack_id, pack_version) - anything else in params round-trips into dimensions. Maps MLflow
status strings (FINISHED/FAILED/RUNNING/KILLED) to TraceStatus values.

### Acceptance check (no MLflow required)

```bash
python3 -c "
from jazzx_sdk.evaluation.experiment.mlflow_bridge import is_sensitive_key, mask_value
assert is_sensitive_key('OPENAI_API_KEY')
assert not is_sensitive_key('model_name')
assert mask_value('sk-proj-abcdef123456') == 'sk-p...3456'
assert mask_value(None) == '[empty]'
print('PASS')
"
```

MLflow-dependent functions are covered in tests/test_experiment_run.py using
MLFLOW_TRACKING_URI pointed at a tempdir.

---

## Change 5 - Export from jazzx_sdk/evaluation/__init__.py

Add ExperimentRun to the existing import block and __all__ list. Pattern matches how
EvaluationHarness, GoldenCase, EvaluationResults, etc. are currently exported.

---

## What this does NOT change

- golden_cases/schema.py, load_cases, load_case, save_case - untouched
- EvaluationResults.labels - retained as-is; dimensions coexists, packs migrate at own pace
- EvaluationHarness.run() signature and return type - unchanged
- mlflow_bridge.py (the existing trace bridge) - untouched, new bridge is a sibling
- fabric/canonical/ - ExperimentRun does not live here, no Schema Spec clause needed
- MACER - no changes; migrating MACER is out of scope, separate future plan
- Version string - no bump

---

## File change table

| File | Type | Change |
|---|---|---|
| jazzx_sdk/evaluation/experiment/__init__.py | New | Package init, export ExperimentRun |
| jazzx_sdk/evaluation/experiment/schema.py | New | ExperimentRun model with .start() / .complete() |
| jazzx_sdk/evaluation/experiment/mlflow_bridge.py | New | MLflow bridge, masking helpers |
| jazzx_sdk/evaluation/golden_cases/loader.py | Modify | Add GoldenCaseLoader.hash_cases() |
| jazzx_sdk/evaluation/harness/config.py | Modify | Add dimensions, case_set_label to EvaluationConfig |
| jazzx_sdk/evaluation/harness/runner.py | Modify | Create/complete ExperimentRun in run(); set results.experiment_run_id |
| jazzx_sdk/evaluation/harness/results.py | Modify | Add experiment_run_id field to EvaluationResults |
| jazzx_sdk/evaluation/__init__.py | Modify | Export ExperimentRun |

---

## Implementation notes

**ExperimentRun.status = FAILED is a quality-verdict aggregate, not an infra-failure
signal.** ExperimentRun sets FAILED when every case fails quality/gate assertions.
eval-service uses failed to mean the run could not be scored at all (infra crash, entity
error). These look identical at the object level but mean different things. Any adapter or
reporter consuming ExperimentRun.status must not forward it directly to eval-service's
TestCaseRunStatus.failed - doing so corrupts pass-rate reporting. Map to eval-service
status only after an explicit, documented translation step.

**trace_ids is not populated by this plan.** Populating it requires a pack-supplied
extractor (the conductor return type varies by pack). Leave as empty list; wire in a
follow-on plan when a real pack needs the linkage. The field is on the schema now to avoid
a second additive schema change later.

**compare_runs is out of scope.** This plan establishes the object and wires it into the
harness so runs accumulate the comparison key (dimensions + case_set_hash). The
query/aggregation layer is a separate follow-on plan - it has no existing reference
implementation and deserves its own design pass.

**Do not add golden_cases_dir to ExperimentRun.** Case set identity is case_set_hash
(content-addressed, portable). If a path is useful for debugging, put it in metadata.

**mlflow_run_to_experiment_run dimension recovery is best-effort.** Any param logged
outside this bridge round-trips into dimensions. Do not expand the reserved-key set
without a clear reason.

---

## Suggested tests (tests/test_experiment_run.py)

- test_experiment_run_start_and_complete - status transitions, completed_at set
- test_experiment_run_id_format - run_id starts with "run_"
- test_hash_cases_deterministic - same directory hashes identically
- test_hash_cases_changes_on_content_change - edited file changes hash
- test_hash_cases_stable_under_reorder - hash independent of filesystem iteration order
- test_evaluation_config_dimensions_default_empty - backward compat, labels untouched
- test_harness_creates_experiment_run - minimal fake conductor; assert
  results.experiment_run_id is set after harness.run()
- test_harness_case_set_hash_matches_loader - hash on run equals hash_cases() called
  independently in the test
- test_is_sensitive_key / test_mask_value - pure helpers, no MLflow
- test_experiment_run_to_mlflow_logs_dimensions - MLFLOW_TRACKING_URI=tempdir; assert
  params logged match dimensions plus reserved keys
- test_mlflow_run_to_experiment_run_roundtrip - write then read back; assert dimensions,
  case_set_hash, case_set_label survive the round trip

---

## End-to-end verification scenario

A pack author runs the same golden_cases_dir three times with different
EvaluationConfig.dimensions: {"model": "gpt-5.2", "architecture": "baseline"},
{"model": "gpt-5.2", "architecture": "kg_hybrid"}, {"model": "gpt-5.4-mini",
"architecture": "kg_hybrid"}.

Each harness.run() computes the same case_set_hash (case files unchanged) and creates a
distinct ExperimentRun with its own run_id and dimensions. Each
EvaluationResults.experiment_run_id points at its respective ExperimentRun.

All three ExperimentRun.case_set_hash values are identical - confirming without relying
on anyone saying so that the three runs are validly comparable on dimensions alone.

A future compare_runs query groups by case_set_hash, breaks out by dimensions, and
generates what MACER's hand-built cross-architecture table does today - from data, not
typed by hand.
