# Findings diff and a skinny-compatible MLflow run lookup (sonnet-runtime, 2026-10-18)

## 1. Findings-shaped comparison (not covered)
Checked `evaluation/experiment_comparison.py` and `comparison_export.py`: they pair scored `CaseRun`s by case id (score
deltas, fixed/broke flips, noise floor) and export CSV/ZIP through `csv_safe_cell`. Nothing compares keyed findings
(`{key, verdict, text}` per mnemonic) between two runs, and no workbook writer takes comparison data (workbooks exist
only in coverage and release reports, built directly with openpyxl).
Plan (it belongs in the SDK: any run that reports judged findings by a stable key needs it; no consumer named):
- `evaluation/findings_diff.py`: `diff_findings(left, right, *, key="key", verdict="verdict") -> FindingsDiff` with a
  row per key: `present_both | only_left | only_right`, and for present-both `unchanged | changed` (the verdicts and
  the text of each side). Counts by kind and a `changed_share`. Pure, no model; a verdict is compared after the
  same normalisation `_same` uses for facts (case and spacing).
- `comparison_export` takes a writer: `CellWriter` protocol (`write_rows(sheet, header, rows)`), with the CSV writer
  (apostrophe guard through `csv_safe_cell`) and an xlsx writer (openpyxl; a formula-looking string is stored as
  text with the cell's `quotePrefix` style, the workbook's own mechanism, never an apostrophe in the value).
  `comparison_workbook(comparison)` and `findings_diff_workbook(diff)` use it. Tests: a leading `=` survives a read-back
  of each format as the original text; diff kinds; the two writers hold identical rows.
- Client and route (`GET /eval/experiments/{a}/findings-diff/{b}`) follow once an experiment stores findings per case
  (they travel in `Invocation.output` / `ScorerResult.findings` today); the first slice is the function and writers.
## 2. MLflow run lookup with mlflow-skinny (partly covered)
Import survey: backend modules take an injected `MlflowClient` and import mlflow inside functions
(`trace_source`, `experiment_store`, `bridge`, `tracer`, `hooks`); three import it at module scope behind an
`ImportError` guard: `backends/mlflow/runtime.py` (`mlflow`, `mlflow.entities`, `mlflow.tracking.MlflowClient`, all in
skinny), `evaluation/backends/mlflow/reporter.py` and `dataset_sync.py` (`import mlflow`; dataset sync also needs
`mlflow.genai.datasets`, full mlflow only). `run_tracer` probes with `import mlflow`. So the tracing and store paths
should load under skinny, and the genai-dependent pieces (`dataset_sync`, `prompt_optimizers`) need full mlflow. Not
verified by running (no skinny environment here): a test must install only skinny in a throwaway venv.
Missing: any run lookup. The SDK never searches runs: `experiment_bridge` calls `client.get_run(run_id)` with an id it
already holds, and nothing resolves a run name to an id or downloads artifacts.
Plan: `MlflowRunLookup(client | tracking_uri)` in `observability/backends/mlflow/lookup.py`:
`run_id_for(experiment, run_name)` via `client.search_runs(..., filter_string="tags.mlflow.runName = '<name>'")`,
refusing zero or several matches by name; `download(run_id, artifact_path, dest)` via `client.download_artifacts`
(in skinny). A REST path (`httpx` to `/api/2.0/mlflow/runs/search` and `/get-artifact`) for a deployment with no mlflow
package at all, chosen when `import mlflow` fails. Tests: fake client for the search and the refusals; REST path against
a mock transport; a skinny-venv import test (CI-optional marker). The module imports nothing from mlflow at module scope.
