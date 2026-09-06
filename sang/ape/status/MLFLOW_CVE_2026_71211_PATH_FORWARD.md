# The mlflow advisory: is there a path forward?

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: assessment, 2026-09-03. Written to justify a Dependabot dismissal.

## The alert

`GHSA-h7x2-h6g9-p789` / `CVE-2026-71211`, high severity, published 2026-08-05.
"MLflow AI Gateway permits SSRF through an unvalidated `api_base`."

- Vulnerable range: `>= 3.13.0, <= 3.15.2`
- `first_patched_version`: **none**
- Alert manifest: `poetry.lock`, scope `runtime`
- Currently locked: mlflow 3.15.1. Latest on PyPI: 3.15.2, itself inside the range.

## There is nothing to bump to

The obvious move is closed. No patched release exists, and the newest release is still vulnerable,
so upgrading cannot clear the alert. Downgrading is worse: below 3.13.0 leaves this range but
re-enters an earlier SSRF, and it also crosses the mlflow floor that pyproject already documents as
CVE-driven.

## `mlflow-skinny` looks like the answer and is not

Tempting, because the advisory names exactly one package: **`mlflow`**. `mlflow-skinny` is not
listed, so switching the extra would make the alert vanish.

Tested, and the reason it vanishes is not the reason it should. In a clean 3.15.2 skinny
environment, `mlflow.gateway`, `mlflow.gateway.config`, `mlflow.deployments` and `mlflow.server`
all import successfully. Skinny drops heavy *dependencies*, not the gateway *code*. The switch
would silence the alert while shipping the same bytes, which is worse than an honest dismissal
because it leaves nothing written down.

Recorded for completeness, since it was measured: skinny does cost real behaviour. `mlflow.openai`
fails to import under it (`ModuleNotFoundError: ModelInputExample`), so
`enable_mlflow_agent_autolog` degrades to its warning path and native Agents-SDK autolog is lost
(japes' own `MlflowTraceHooks` still works). The sqlite-backed tracking store also needs
`alembic`/`sqlalchemy` re-added. Otherwise 132 of the 134 mlflow-touching tests pass unmodified.
So skinny is arguable on install-size grounds; it is not a security fix, and should not be sold as
one.

## Why the finding is unreachable here

The vulnerability is in the **AI Gateway**, an mlflow server component: exploiting it requires
running the gateway and giving it a route whose `api_base` an attacker influences.

- `jazzx_sdk` and `plato` contain **zero** references to `mlflow.gateway`, `mlflow.deployments`,
  `api_base`, or any gateway configuration. Grepped, not assumed.
- The full mlflow import surface is four lines: `import mlflow`, `import mlflow.entities`,
  `from mlflow.tracking import MlflowClient`, `import mlflow.openai`. Tracking-client and tracing
  APIs only.
- mlflow is an **optional extra**, absent from a default install and off the eager import path.
- Since the backend split it is confined to `observability/backends/mlflow/` and
  `evaluation/backends/mlflow/`, with an import-linter contract that fails the build if anything
  above reaches in, function-level imports included.

Dependabot reports it as `runtime` because it reads `poetry.lock`, where an optional extra and a
hard dependency look alike. That is a lockfile artefact, not a description of what ships.

## Recommendation

**Dismiss as `vulnerable_code_not_actually_used`, citing this note.** Then set a reminder to
re-check when mlflow ships a fix, at which point the floor moves and the dismissal is retired.

Two things make that defensible rather than convenient: the vulnerable component is a server japes
never starts, and the boundary keeping mlflow at arm's length is now enforced by a contract rather
than by habit.

## The structural answer, when it is worth paying for

The alert recurs as long as mlflow sits in japes' lockfile at all. Option C from
`MLFLOW_ABSTRACTION_ASSESSMENT.md` -- implementations in a separate distribution, japes shipping
abstractions only -- is the one path that ends that permanently, and the backend split just made it
mechanical: two directories move, nothing else changes. Still not worth a package boundary to
maintain forever on the strength of one unreachable advisory. Worth revisiting if mlflow's
constraints bite a second time, which they have already done once (the `cryptography<50` pin
recorded in `pyproject.toml`).
