# JACI CI Spread - CaseContext Checkpoint Wiring
# Plan for Claude Code Execution
# Author: Virendra Mehta
# Date: 2026-06-11

## Objective

Wire `CaseContext` (Schema Spec §7.1, Derived Object 1) writes into
`CIConductor.run_analysis()` at iteration boundaries and at run start/end.
This gives the conductor mid-loop checkpointing: a restarted run can resume
from the last persisted `CaseContext` rather than starting over from iteration 1.

The `CaseContextStore` is already in `CanonicalObjectStore` and ready.
The `CaseContext` Pydantic model is already in `jazzx_sdk.fabric.canonical.derived`.
The `Depend` sub-schema (typed blocking items on `pending_dependencies`) is already
defined. This plan is wiring only - no new SDK objects, no schema changes.

## What This Does NOT Change

- `CaseContext` model in `fabric.canonical.derived` - not touched
- `CanonicalObjectStore` / `CaseContextStore` - not touched
- `CIContext` (runtime operational form) - not touched
- `CanonicalTrace` / `CanonicalCaseFile` persistence (already wired) - not touched
- Any other scenario conductor (AML, CRE) - not touched
- UI demo_page.py - separate follow-on to surface checkpoint status in Trace tab
- Schema Spec freeze - CaseContext is already a derived object; no new objects

## The Checkpoint Design

`CaseContext` is written at four points in `run_analysis()`:

1. **Run start** - after context is created, before Phase 0. Records initial
   state: `active_policies` resolved from the pack, `autonomy_ceiling=2`,
   `pending_dependencies=[]`, `state="active"`. This is the "run opened" record.

2. **Each iteration boundary** - after Sentinel check, before the next
   Investigator call. Records: `evidence_bundle` (IDs of all verified evidence),
   `pending_dependencies` (open `Depend` objects built from active hypotheses
   that still need evidence), `state="investigating"`, `trace_id` (the context_id
   so the checkpoint links back to the trace).

3. **Post-convergence, pre-Reasoner** - records `state="synthesizing"`,
   final `evidence_bundle`, final `pending_dependencies` cleared or satisfied.

4. **Run end** - after `CanonicalTrace` + `CanonicalCaseFile` are persisted.
   Records `state="complete"` (or `"governor_blocked"` / `"guard_fired"`),
   final decision reference, `trace_id` pointing to the emitted trace.

Each write uses a **versioned** `case_context_id` (`ctx_{context_id}_{seq:02d}`,
seq monotonic per run) so the full per-iteration trail is preserved, not
overwritten. `case_id` (`{context_id}`) is the stable join key across the trail;
`domain_extensions.checkpoint_seq` orders it. The latest checkpoint is the max
`checkpoint_seq` for a given `case_id`.

## `Depend` Construction

Each active hypothesis that still has unfulfilled `evidence_needed` items
becomes a `Depend` of type `EVIDENCE_REQUIRED`. Hypotheses that have been
satisfied (all their `evidence_needed` types are in `ctx.evidence`) are
`DependencyStatus.SATISFIED`.

For the intercreditor flag (`application.intercreditor_required=True`),
add a `Depend` of type `CONDITION_PRECEDENT` with
`description="Intercreditor agreement required before commitment"` and
`status=OPEN`. This is never auto-satisfied by the loop - it requires
human action and persists until the case is closed.

## `CaseContext` Population from `CIContext`

`CIContext` is the operational runtime form. `CaseContext` is the canonical
governance form. The mapping:

| CaseContext field          | Source                                              |
|----------------------------|-----------------------------------------------------|
| `case_context_id`          | `f"ctx_{ctx.context_id}"`                           |
| `case_id`                  | `str(ctx.context_id)`                               |
| `subject`                  | `{"loan_id": app.loan_id, "company": app.company}`  |
| `state`                    | see per-checkpoint above                            |
| `active_policies`          | `["CI_CORE_LEVERAGE_POLICY", "CI_CORE_FCCR_POLICY", "CI_CORE_ABL_POLICY", "CI_CORE_LIEN_POLICY"]` |
| `evidence_bundle`          | `[ev.evidence_id for ev in ctx.evidence if hasattr(ev, "evidence_id")]` |
| `pending_dependencies`     | built from active hypotheses + intercreditor flag   |
| `autonomy_ceiling`         | `2` (RECOMMEND_ONLY for CI spread)                  |
| `trace_id`                 | `str(ctx.context_id)` (links to CanonicalTrace)     |
| `pack_id`                  | `self.pack_id or "ci-spread-core"`                  |
| `domain_extensions`        | `{"loan_type": app.loan_type.value, "iteration": ctx.iteration_count}` |

## Restart Pattern (not implemented in this plan, but enabled by it)

After this plan, a restart looks like:

```python
# Resume an interrupted run — latest checkpoint = max checkpoint_seq for this case_id
trail = sorted(
    (c for c in await fabric.canonical.case_context.list(pack_id="ci-spread-core")
     if c.case_id == context_id),
    key=lambda c: c.domain_extensions.get("checkpoint_seq", 0),
)
checkpoint = trail[-1] if trail else None
if checkpoint and checkpoint.state not in ("complete", "governor_blocked"):
    ctx = CIContext.from_case_context(checkpoint, application)
    # ctx.evidence and ctx.hypotheses are rebuilt from checkpoint
    # Loop resumes at checkpoint.domain_extensions["iteration"] + 1
```

`CIContext.from_case_context()` is NOT implemented in this plan - that is
the restart plan (a separate doc). This plan only writes the checkpoints.

## Files Changed

| File | Change |
|------|--------|
| `src/jaci/scenarios/ci_spread/conductor.py` | Add `_build_case_context()` helper; add `_checkpoint()` async helper; call at 4 points in `run_analysis()` |

No other files change.

## Step 1 - Add `_build_case_context()` to `CIConductor`

Add this method after `_run_entity_extraction()`:

```python
def _build_case_context(
    self,
    ctx: "CIContext",
    application: "LoanApplication",
    state: str,
    trace_id: str | None = None,
) -> "CaseContext":
    """Build a CaseContext snapshot from the current CIContext state.

    Called at iteration boundaries and run start/end to provide
    mid-loop checkpoints for restart and audit.

    Args:
        ctx: The live CIContext at checkpoint time.
        application: The LoanApplication being analyzed.
        state: Checkpoint state label: "active" | "investigating" |
               "synthesizing" | "complete" | "governor_blocked" | "guard_fired"
        trace_id: The context_id string (links to CanonicalTrace).

    Returns:
        CaseContext ready for fabric.canonical.put_case_context().
    """
    from jazzx_sdk.fabric.canonical.derived import (
        CaseContext,
        Depend,
        DependencyStatus,
        DependencyType,
    )

    # Evidence bundle: IDs of all evidence objects that have an evidence_id
    evidence_bundle = [
        str(ev.evidence_id)
        for ev in ctx.evidence
        if hasattr(ev, "evidence_id") and ev.evidence_id
    ]

    # Pending dependencies from active hypotheses
    pending_deps: list[Depend] = []
    fulfilled_types = {
        getattr(ev, "evidence_type", None) for ev in ctx.evidence
    }

    for hyp in ctx.hypotheses:
        content = getattr(hyp, "content", None)
        if content is None:
            continue
        needed = getattr(content, "evidence_needed", []) or []
        unfulfilled = [n for n in needed if n not in fulfilled_types]
        if unfulfilled:
            it = getattr(content, "issue_type", None)
            it_str = it.value if hasattr(it, "value") else str(it or "")
            pending_deps.append(Depend(
                dependency_type=DependencyType.EVIDENCE_REQUIRED,
                description=(
                    f"Hypothesis [{it_str}]: requires {', '.join(unfulfilled)}"
                ),
                status=DependencyStatus.OPEN,
                evidence_required=unfulfilled,
                owner="investigator",
            ))
        else:
            # All evidence satisfied for this hypothesis
            it = getattr(content, "issue_type", None)
            it_str = it.value if hasattr(it, "value") else str(it or "")
            pending_deps.append(Depend(
                dependency_type=DependencyType.EVIDENCE_REQUIRED,
                description=f"Hypothesis [{it_str}]: evidence complete",
                status=DependencyStatus.SATISFIED,
                evidence_required=[],
            ))

    # Intercreditor as a CONDITION_PRECEDENT dependency (never auto-satisfied)
    if getattr(application, "intercreditor_required", False):
        pending_deps.append(Depend(
            dependency_type=DependencyType.CONDITION_PRECEDENT,
            description=(
                "Intercreditor agreement required before commitment. "
                "Existing senior secured lender holds first lien on collateral."
            ),
            status=DependencyStatus.OPEN,
            owner="borrower",
        ))

    return CaseContext(
        case_context_id=f"ctx_{ctx.context_id}",
        case_id=str(ctx.context_id),
        subject={
            "loan_id": application.loan_id,
            "company": application.company,
            "loan_type": application.loan_type.value if application.loan_type else "",
            "requested_amount": application.requested_amount,
        },
        state=state,
        active_policies=[
            "CI_CORE_LEVERAGE_POLICY",
            "CI_CORE_FCCR_POLICY",
            "CI_CORE_ABL_POLICY",
            "CI_CORE_LIEN_POLICY",
        ],
        evidence_bundle=evidence_bundle,
        pending_dependencies=pending_deps,
        autonomy_ceiling=2,
        trace_id=trace_id or str(ctx.context_id),
        pack_id=self.pack_id or "ci-spread-core",
        domain_extensions={
            "loan_type": application.loan_type.value if application.loan_type else "",
            "iteration": ctx.iteration_count,
            "loop_status": ctx.loop_status.value if hasattr(ctx.loop_status, "value") else str(ctx.loop_status),
        },
    )
```

## Step 2 - Add `_checkpoint()` helper

```python
async def _checkpoint(
    self,
    ctx: "CIContext",
    application: "LoanApplication",
    state: str,
    trace_id: str | None = None,
) -> None:
    """Write a CaseContext checkpoint to fabric.canonical. Best-effort, never aborts."""
    try:
        case_ctx = self._build_case_context(ctx, application, state, trace_id)
        canonical = self._resolve_fabric().canonical
        if canonical is not None:
            await canonical.put_case_context(
                case_ctx,
                ontology_id=self.pack_id or "ci-spread-core",
            )
            logger.debug(
                "Checkpoint written: state=%s iteration=%d case_context_id=%s",
                state, ctx.iteration_count, case_ctx.case_context_id,
            )
    except Exception as e:  # noqa: BLE001 - checkpoint is never blocking
        logger.debug("Checkpoint write failed (non-blocking): %s", e)
```

## Step 3 - Wire checkpoints into `run_analysis()`

### Checkpoint 1: Run start

After `self.sentinel.reset()` and before Phase 0 intake, add:

```python
# Checkpoint 1: run opened
await self._checkpoint(ctx, application, "active")
```

### Checkpoint 2: Iteration boundary

At the END of each loop iteration, after the Sentinel check block and
before `continue` / next iteration, add:

```python
# Checkpoint 2: iteration boundary - current evidence + dependency state
await self._checkpoint(ctx, application, "investigating")
```

Specifically: after the Sentinel `for w in getattr(so, "warnings", [])` block
and before the `while` loop continues. If the Sentinel fires a guard and breaks,
the checkpoint at run-end (Checkpoint 4) will record the final state.

### Checkpoint 3: Post-convergence

After the `while` loop exits (regardless of exit reason) and before the
PlaybookExpert call, add:

```python
# Checkpoint 3: loop complete, entering synthesis
await self._checkpoint(ctx, application, "synthesizing")
```

### Checkpoint 4: Run end

After `CanonicalTrace` + `CanonicalCaseFile` are persisted (the existing
`try/except` block for canonical persistence), at the very end of that block,
add:

```python
# Checkpoint 4: run complete
_final_state = {
    LoopStatus.CONVERGED: "complete",
    LoopStatus.GOVERNOR_BLOCKED: "governor_blocked",
    LoopStatus.GUARD_FIRED: "guard_fired",
}.get(ctx.loop_status, "complete")
await self._checkpoint(ctx, application, _final_state, trace_id=trace.trace_id)
```

Note: `trace.trace_id` is available at this point since `CanonicalTrace` has
just been built. This gives the `CaseContext` a hard link to the trace.

## Acceptance Checks

```bash
cd /Users/sangit/src/jaci

# 1. CaseContext imports resolve
python -c "
from jazzx_sdk.fabric.canonical.derived import (
    CaseContext, Depend, DependencyType, DependencyStatus
)
print('CaseContext imports OK')
"

# 2. _build_case_context produces a valid CaseContext
python -c "
import asyncio
from jaci.scenarios.ci_spread.ui.demo_page import _load_fixtures, _run_conductor_cached
g, _ = _load_fixtures()
cf = _run_conductor_cached(g)
print('Run completed, checking canonical store...')
import json
from pathlib import Path
# The mock store writes JSON to output/ci_spread/
artifact_dir = Path('output/ci_spread') / g['loan_application']['loan_id']
contexts = list(artifact_dir.glob('*case_context*')) if artifact_dir.exists() else []
print(f'Artifact dir: {artifact_dir}, context files: {len(contexts)}')
"

# 3. Checkpoints written at correct states
python -c "
import asyncio, logging
logging.basicConfig(level=logging.DEBUG)
from jaci.scenarios.ci_spread.ui.demo_page import _load_fixtures, _run_conductor_cached
g, _ = _load_fixtures()
cf = _run_conductor_cached(g)
# Look for checkpoint log lines
" 2>&1 | grep -i 'checkpoint\|case_context' | head -20
# Expected: 4+ checkpoint log lines at states: active, investigating (x N), synthesizing, complete

# 4. CaseContext has correct fields
python -c "
import asyncio
from jaci.scenarios.ci_spread.conductor import CIConductor
from jaci.scenarios.ci_spread.ui.demo_page import _load_fixtures, _run_conductor_cached
from jazzx_sdk.fabric import FabricConfig, KnowledgeFabric, RetrievalMode
from jazzx_sdk.mock_services import MockKnowledgeHubClient

g, _ = _load_fixtures()
a = g['loan_application']

fabric = KnowledgeFabric(
    kh_client=MockKnowledgeHubClient(),
    config=FabricConfig(retrieval_mode=RetrievalMode.LOCAL),
)

async def run():
    from jaci.scenarios.ci_spread.schemas import LoanApplication, LoanType, LoanPurpose
    application = LoanApplication(
        loan_id=a['loan_id'], company=a['company'],
        loan_type=LoanType(a['loan_type']),
        loan_purpose=LoanPurpose(a.get('loan_purpose', 'working_capital')),
        requested_amount=a['requested_amount'],
        intercreditor_required=a.get('intercreditor_required', False),
    )
    from unittest.mock import MagicMock
    ctx_mock = MagicMock()
    ctx_mock.runtime = MagicMock()
    conductor = CIConductor(ctx=ctx_mock, ground_truth=g.get('expected_decision'))
    cf = await conductor.run_analysis(application, fabric=fabric)

    # Read back the final CaseContext checkpoint
    case_ctx = await fabric.canonical.get_case_context(
        f'ctx_{cf.context.context_id}'
    )
    assert case_ctx is not None, 'No CaseContext checkpoint found'
    assert case_ctx.state in ('complete', 'governor_blocked', 'guard_fired'), case_ctx.state
    assert case_ctx.pack_id == 'ci-spread-core'
    assert case_ctx.autonomy_ceiling == 2
    assert len(case_ctx.active_policies) == 4
    # Intercreditor open dependency should be present
    if a.get('intercreditor_required'):
        condition_deps = [
            d for d in case_ctx.pending_dependencies
            if d.dependency_type.value == 'condition_precedent'
        ]
        assert condition_deps, 'Intercreditor CONDITION_PRECEDENT dependency missing'
    print(f'CaseContext OK: state={case_ctx.state}, '
          f'evidence={len(case_ctx.evidence_bundle)}, '
          f'deps={len(case_ctx.pending_dependencies)}, '
          f'trace_id={case_ctx.trace_id[:20]}...')

asyncio.run(run())
"
```

## What This Does NOT Build Yet

- `CIContext.from_case_context()` - the restart entry point. Enabled by this
  plan but not implemented here. A restarted conductor can now find a checkpoint;
  it cannot yet hydrate from it.
- `DomainPack` governance record wiring at startup (`DomainPackHelper.from_yaml` +
  `fabric.canonical.put_domain_pack`). Separate plan.
- `CaseContext` display in the Trace tab UI. Separate follow-on.
- AML and CRE conductor checkpoint wiring. They adopt the same pattern after
  CI spread is validated.

## Why This Matters Beyond CI Spread

`CaseContext.pending_dependencies` with typed `Depend` objects is the
platform-level mechanism for tracking blocked work across all domains:
- AML: `EVIDENCE_REQUIRED` for missing transaction records; `APPROVAL_REQUIRED`
  for SAR filing authorization
- Mortgage: `CONDITION_PRECEDENT` for title insurance; `POST_CLOSE` for
  hazard insurance delivery
- CRE: `ONGOING_COVENANT` for quarterly DSCR reporting; `EXTERNAL_RESPONSE`
  for appraisal from third-party MAI appraiser

The conductor pattern is the same for all domains. Domain differences are only
in how `_build_case_context()` constructs the `Depend` objects from domain-
specific hypothesis and application content.
