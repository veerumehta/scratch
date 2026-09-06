# Does japes need to depend on mlflow?

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: assessment, 2026-09-03. Read-only; nothing changed.

## Answer

**The abstractions already exist. japes does not depend on mlflow in any way that constrains it --
and the remaining question is not "can we abstract it" but "should the mlflow implementations ship
in this repository".** Those are different questions with different answers, and conflating them
would mean rebuilding seams that are already there.

Four abstract base classes already stand between the SDK and any tracing backend:

| ABC | File | Role |
| --- | --- | --- |
| `RunTracer` | `observability/run_tracer.py` | writes runs and spans |
| `TraceSource` | `observability/trace_source.py` | reads a stored run back as a `CanonicalTrace` |
| `EvaluationReporter` | `evaluation/reporter.py` | publishes evaluation results |
| `ExperimentStore` | `evaluation/experiment/store.py` | persists experiment runs |

`trace_source.py`'s own docstring already frames mlflow as one of several: *"`MlflowTraceSource` is
the first backend (an OTel / eval-service source can implement the same base)."* The design
intended this.

## How hard the dependency actually is

138 occurrences of "mlflow" across 20 files sounds like entanglement. **11 of them are imports**;
the other 127 are docstrings, comments and string literals.

Of those 11: **4 are module-level**, in exactly two files (`_mlflow_runtime.py`,
`evaluation/reporters/mlflow.py`), and 7 are deferred inside functions. `_mlflow_runtime.py` exists
precisely to hold the eager ones, and says so:

> *"Split out of `tracing.py` so mlflow leaves the eager import path... Do not import this module
> from `observability/__init__.py` or anywhere else on the eager path."*

So `import jazzx_sdk` does not import mlflow even with the extra installed. It is already an
optional extra, already absent from the default install, and the suite passes without it.

**On the strength of the dependency, there is nothing to fix.**

## What is actually mixed together

Where the concrete implementations sit is a different matter. Two files carry the ABC and its mlflow
implementation together:

| File | Lines | Contains |
| --- | ---: | --- |
| `observability/run_tracer.py` | 383 | `RunTracer` (ABC) **and** `MlflowTracer`, `_MlflowRun`, `_MlflowSpan` |
| `observability/trace_source.py` | 39 | `TraceSource` (ABC) **and** `MlflowTraceSource` |
| `evaluation/experiment/store.py` | 45 | `ExperimentStore` (ABC) **and** `MlflowExperimentStore` |

And five files are pure mlflow implementation with no abstraction in them at all:
`mlflow_bridge.py` (301), `agent_hooks.py` (319), `mlflow_env.py` (107), `_mlflow_runtime.py` (20),
`evaluation/experiment/mlflow_bridge.py` (137), plus `evaluation/reporters/mlflow.py` (83).

That is roughly **970 lines of mlflow-specific code** in a repository whose SDK layer is meant to be
backend-agnostic. `run_tracer.py` is the clearest case: 383 lines of which the ABC is perhaps 40.

## The three options

**A. Leave it.** The dependency is optional, the eager path is clean, and the ABCs are in place. A
consumer that wants a different backend implements the base class and never installs the extra.
Costs nothing today; the repository keeps ~970 lines it does not conceptually own.

**B. Split abstraction from implementation, same repository.** ABCs stay where callers expect them;
mlflow implementations move behind one boundary (`jazzx_sdk/observability/backends/mlflow/`, or
similar). Makes the seam visible and the line count honest, and the tier contract could then forbid
core modules importing the backend package. Import paths change, so it is a breaking change for
anyone importing `MlflowTracer` or `MlflowReporter` directly -- worth a consumer survey first, the
way the `handlers` split was.

**C. Move the implementations out of japes entirely** -- a `japes-mlflow` package, or into whichever
layer already owns deployment concerns (Plato is the candidate). The SDK then ships abstractions
only. This is the shape the question implies, and it is the one with real costs: a second package to
version and release, and a consumer who wants tracing now needs two installs and has to wire the
implementation in. It also strands `mlflow_bridge.spans_to_canonical_trace`, which is *generic*
span-to-`CanonicalTrace` mapping that `trace_source.py` deliberately keeps shared.

## Recommendation

**B, and not yet.** The gain from C over B is small -- the extra is already optional, so a consumer
who never installs it already pays nothing -- while the cost is a package boundary to maintain
forever. B captures most of the benefit: the seam becomes explicit, the tier contract can enforce
it, and if C ever becomes worthwhile the move is then mechanical because everything mlflow-specific
already sits in one directory.

"Not yet" because there is no pressure. Nothing is blocked on this, no second backend is being
written, and the eager-import problem it might have caused was already solved by
`_mlflow_runtime.py`. The moment it becomes worth doing is when a **second** backend implementation
appears -- an OTel or eval-service `TraceSource`, which `trace_source.py` already anticipates. At
that point the directory structure has to say which is which, and B pays for itself.

## Worth knowing either way

- **The reporters directory has one entry.** `evaluation/reporters/` contains only `mlflow.py`, with
  no `__init__` exports and no second reporter. A plural directory with one implementation is a
  seam that has never been exercised -- the first alternative reporter is what proves
  `EvaluationReporter` is the right shape, and until then it is untested design.
- **`agent_hooks.py` is the largest single piece (319 lines) and has no abstraction above it.**
  `MlflowTraceHooks` is reached through a lazy module `__getattr__`. If a second backend needs hooks,
  that is where a fifth ABC belongs, and its absence is the real gap rather than the dependency.
- **CI installs the mlflow extra deliberately** (recorded in `tests.yml`): the span calls are bound
  against real `MlflowClient` signatures so a renamed kwarg upstream fails in CI rather than in a
  deployment. Any move must keep that property, or it trades a visible failure for a silent one.
