# Design note: one function library for pack, tool and generated-code computation

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Design note, 2026-11-18. Decides nothing; no code built or moved. Read from the `v2.7.5` tree (`jazzx_sdk/`) and macer's `origin/feat/income-worksheet-formula-metrics` (read-only). Counts are files that import the module (a grep), not call sites. Folder: `docs/status/computation/` is new (status held `Acra/`, `done/`, `macer/`, `slides_japes_sdk_plato/`, `stale/`, `superseded/` and flat files; nothing computation-related to join). For review by `sonnet-packs`, who owns code refinement and the income worksheet.

## 1. What exists today: six places that compute

| Place | What it is | Numbers | Unknown or zero handling | Files that import it |
|---|---|---|---|---|
| `jazzx_sdk/expressions/` (5 files, 1,160 lines) | The formula DSL: `parse`, `validate`, `evaluate` with a `ResolutionContext`, governed decimal plus a full `MetricDerivation` (inputs, steps) or a typed `Refusal` (`evaluate.py:230-460`); `MetricDefinition` as pack data (`definition.py`) | `Decimal` | refuses, with a reason code | 12 (7 in `jazzx_sdk`/`plato`) |
| `finance/metrics.py` (202 lines) | 18 named credit-analysis ratios over one period (`leverage`, `interest_coverage`, `dso_days`, `cash_conversion_cycle`, ...) and a `Financials` model | `float` | `None`; `strict=True` raises `MetricRefusal` | 7 (5) |
| `util/math/ratios.py` (257 lines) | Not ratio formulas: compare a ratio with a threshold (`ratio_holds`, `evaluate_ratio`, `evaluate_covenant_policy`), warning zones, shocks and sensitivity (`apply_shock`, `run_sensitivity`), `RatioResult` | `float` | treats a non-finite value as a breach | 6 (5) |
| `tools/calculate.py` (138 lines) | The model's calculator: `Calculator` over the DSL's light evaluator, a `CalculationLog`, `calculate_tool` (offered to adjudication by `evidence.calculator`, A1) | `Decimal` | error text, never raises | 5 (2) |
| `rules/lib.py` (753 lines, `LIB_VERSION` 1.1.2) | `rules_lib`: what generated Python rules repeat: unknown handling (`known`, `gaps`, `unknown`), text and name matching (`norm`, `same_person`, `same_org`), `ratio`, `percent`, rounding, `total`/`average`/`lowest`/`highest`, thresholds, dates (`edate`, `eomonth`, `months_between`, `business_days_between`), `latest`, `pair_off`, `explains` | `int`/`float`/`Decimal`, answers `Decimal` when mixed | `None`, never raises | 18 (11) |
| `finance/` (11 files) and `pipelines/financial/spread.py` | The spreading primitives: structure a statement, the `FinancialSpread` and its package, Decimal controls (`finance/validation.py`: scale errors, balance control), periods, workbook; the pipeline that assembles them | `Decimal` for controls | findings, not exceptions | (spread pipeline only) |

What the survey found, which shapes everything below:

- **Two function tables inside one file.** The DSL has a fixed `if`/`elif` chain of built-in functions in the full evaluator (`if`, `min`, `max`, `cap`, `prior`, `avg`, `cagr`, `ltm`, and four `*_entities` aggregations; `evaluate.py:283-330`) and a second, smaller chain in the light `evaluate_over_namespace` path (`if`, `min`, `max`, `cap` only; `evaluate.py:474-520`). The calculator, formula conditions (`fabric/canonical/condition_evaluator.py`) and derived metrics (`pack/assessment.py`) all reach the DSL, but a function added to one table is invisible to the other, and nothing is resolved by name from a registry.
- **Three zero-denominator policies.** The DSL refuses with a reason, `finance/metrics.py` returns `None`, `rules_lib` returns `None`, the calculator returns error text. Each is reasonable alone; a user moving a formula between them gets a different answer shape.
- **float against Decimal.** `finance/metrics.py` and `util/math/ratios.py` compute in `float`; the DSL, the calculator, `rules_lib` (when mixed) and the spread controls use `Decimal`. A ratio the model calculates through the calculator and the same ratio from `finance.metrics` can differ in the last digits.
- **`rules_lib` has a hard constraint the others do not.** `rules/lib.py` is delivered whole into the executor's child process, which has no SDK: it imports only `datetime`, `decimal` and `re` (`lib.py:3-12`). It carries a version (`LIB_VERSION`), a per-version manifest (`rules/manifests/`, `rules/api.py`) and a rendered API list for prompts. By the user's 2026-11-02 ruling it stays on 1.1.2.
- **The "income-worksheet helpers" landed in `rules_lib`, not in `expressions/`.** CHANGELOG [2.6.8]: `total`, `average`, `lowest`, `highest` and `edate`, `eomonth`, plus rounding. The DSL has none of them; `evaluate_over_namespace` cannot round or total.
- **`util/math/ratios.py` and `finance/metrics.py` overlap little.** One computes a ratio, the other judges a ratio against a threshold. The overlap is the division and the non-finite handling, written twice.

## 2. The library: shape

### One resolution path

A function is looked up by name in one registry. The DSL's two evaluators, `calculate_tool`, formula conditions, derived metrics and generated code all resolve a call the same way; adding a function is one registry entry, visible everywhere at once. The registry is data about functions (name, signature, units, summary, tests, version, unknown policy); the callables live beside it.

### Two layers, because of `rules_lib`

1. **Core**: pure, stdlib-only modules (the `rules/lib.py` discipline: `datetime`, `decimal`, `re`; no I/O, no clock, no randomness). It can be delivered whole into a child process with no SDK, as `rules_lib` is. `rules_lib` is the first content of the core, unchanged (1.1.2).
2. **Registry**: in the SDK. It indexes the core's functions and the DSL builtins, holds their metadata and tests, renders the API list for prompts (as `render_api` does for `rules_lib`), and resolves calls for the evaluators and the tool.

### What a function returns: a value, and a derivation made by the registry

A function is a plain callable that returns a value (or the declared unknown). Making every function return a derivation would burden the child process. Instead the registry wraps a call to produce a derivation when the caller wants one: the function name, library version, arguments, value; a composite function (a pack-declared formula, below) lists the steps it ran. The DSL's `MetricDerivation` already has this shape, so the wrapper fills it.

### Packs add functions by declaration

A pack function is data, not Python: a name, typed inputs, a body in the DSL calling registry functions, and test cases, validated at load (`expressions/validate.py` already checks undefined references, unit mismatches and cycles). `MetricDefinition` is the existing example for a metric; a function definition is the same idea without the period and approval fields. Python-bodied functions are added to the SDK only, through review.

### What a function must satisfy to be admitted

The user accepts breadth here, so the bar is about being predictable, not small:

1. **Named and typed.** A unique name in a dotted namespace, a signature with units where there are any (percent, months, USD).
2. **Pure.** No I/O, clock or randomness; a date a function needs "now" for is an argument.
3. **Decimal-safe.** Takes `int`, `Decimal` or text; a `float` is read as its printed text; computes and returns `Decimal` (never float arithmetic); never takes a `bool` as a number (the `rules_lib` rule).
4. **A declared unknown policy**, one of a small named set: propagate the unknown, refuse with a reason, treat as zero. Not left to each function.
5. **Tests in the entry.** At least three golden cases: a normal one, a boundary, and an unknown input. The registry test runs every entry.
6. **A version rule.** When an answer a function gives changes, the library version changes and the manifest for the old version is kept (`LIB_VERSION` and `rules/manifests/` today).
7. **A summary** (the first paragraph of the docstring), because the prompt list is generated from it.
8. **No consumer names**, and stdlib-only if it belongs to the core.

## 3. The income worksheet, and extract-then-compute

What macer built (`origin/feat/income-worksheet-formula-metrics`, 61 files, +20,041 lines, read in part: `design/income_worksheet.md`, the stat and the commit titles): `metric_kind` of `formula` or `choice` on a job's metric definition (`models/jtbd_ontology.py`: `inputs`, `formula`, `options`, `default_rule`, `consistency_checks`, `notices`, `worksheet_total`); an engine that evaluates the whole set once per run over an entity-backed loan model, in dependency order, never raising ("Not calculated" with a reason); a choice reviewer (an LLM checks a choice against a quote); the engine began as a synced copy of mortgage-app's and a later commit loads it from Kernel instead ("MA-4125: Load the formula engine from Kernel instead of a synced copy (#360)"). I did not read the engine itself.

How it fits:

- **`formula` kind is the DSL's job.** A formula over inputs bound to entity fields is a `MetricDefinition` with document-field and custom-metric bindings, and the DSL already has cross-entity aggregation (`sum_entities`, `avg_entities`) and multi-period functions. What the engine adds that the DSL lacks are the income helpers (`total`, `average`, rounding, dates), which the registry would hold. Dependency order and "Not calculated with a reason" are the DSL's cycle check and typed `Refusal`.
- **`choice` kind is not a function.** Selecting among options by a default rule and consistency checks, with an LLM review against a quote, is a pack metric kind with an agent step; the registry supplies the pieces its rule bodies call and nothing more.
- **Extract-then-compute (2.6.9 item 11).** The recommendation holds and the library is what makes it safe: the model extracts raw values with provenance (A2 in `docs/plans/adjudication/plan_adjudication_superset_of_macer_2026-11-18.md`), and the SDK computes every derived figure through registry functions, so no figure rests on model arithmetic. The model's own calculator (A1) is for checking, not for the figure of record.
- **Open for the user, not decided here:** whether the SDK's evaluator and the Kernel-hosted engine become one. The library should make the engine a consumer of the registry, not a second implementation.

## 4. What A1 should call now so it is not rework

A1 (`tools/calculate.py`, `evidence.calculator`) reaches the DSL only through `evaluate_over_namespace` and keeps `Calculator.calculate(expression, inputs)`, `CalculationLog`, `calculate_tool` and the recorded shape (`as_record`: expression, inputs as text, value or error). That is the right dependency and needs no change: when the registry exists, the evaluator's function chain is replaced by a lookup, and the calculator gains `round`, `total`, dates and the rest without a line changed. Do not add functions or helpers inside `tools/calculate.py`, and do not copy `finance/metrics.py` formulas into it. One addition later, in A2 not A1: record the library version beside each call, so a recorded calculation can be replayed against the version that ran.

## 5. Placement and migration cost

Rule 7: the `jazzx_sdk/` root holds only cross-cutting core, and a new root module needs a stated reason. A new package is justified (the one thing the five places share), and it must sit below every package that uses it (`expressions`, `tools`, `rules`, `finance`, `pack`). The `sdk-layers` contract in `.importlinter` puts `util` at the bottom and `clients : handlers : identity : models : concurrency : safety : failures : streaming` above it, and `expressions` is not listed in it at all, so the exact tier is for stage 1 to settle. Core goes in a `core/` subpackage with stdlib-only imports; the registry above it.

Migration, staged, each stage shippable and none starting before the library is chosen:

| Stage | Change | Files touched (importers) | Risk |
|---|---|---|---|
| 1 | New package with the registry and `rules_lib` as its first entries (no moves; `rules_lib` stays byte-identical) | 0 existing | none |
| 2 | The DSL's two evaluators resolve calls through the registry (one file, two functions) | `expressions/evaluate.py` (12 importers of the package) | a changed answer in a builtin: the DSL tests pin them |
| 3 | The calculator and formula conditions get the registry for free; render the function list into the calculator's description | `tools/calculate.py` (5) | the prompt text changes; the prompt snapshot test (G2) shows it |
| 4 | `finance/metrics.py` functions become Decimal registry entries; the module re-exports them | 5 in source, 2 in tests | float outputs change in the last digits: a version bump and a check of the callers |
| 5 | `util/math/ratios.py` keeps threshold and sensitivity logic (it is not a function library); its division and non-finite handling use the registry | 5 in source | low |
| 6 | `rules/lib.py` becomes generated from the core and delivered whole, as now; the `rules_lib` import name and the manifests are unchanged | 18 (11 in source) | a generated-code regression; `LIB_VERSION` and manifests guard it |

Stage 1 plus 2 is the minimum that gives one resolution path; 4 and 6 carry the real cost and can wait.

## 6. Name

The user finds `expressions` too narrow and `compute` too general. The package holds functions and their registry, used by a DSL, a tool and generated code.

| Name | For | Against |
|---|---|---|
| `stdlib` | Carries the JDK analogy: the standard library every pack, tool and generated rule can count on; breadth is expected; cannot be read as DSL syntax or a runtime | Reads like Python's own `stdlib` in conversation; the import `jazzx_sdk.stdlib` is unambiguous but speech is not |
| `functions` | Says exactly what it holds | Generic; every module has functions |
| `formulas` | Matches the DSL and the worksheet | Narrow again: dates, text matching and unknown handling are not formulas |
| `calc` | Short; matches the calculator | Narrow in the same way as `expressions`; suggests arithmetic only |
| `builtins` | "What is available everywhere", which is the point | Collides with Python's `builtins`; implies a fixed set, not a registry packs extend |
| `fx` | Spreadsheet convention for functions | Cryptic outside finance |
| `measures` | Fits finance metrics | Misses dates and text |
| `derive` / `derivations` | The output is a derivation | The helpers (`norm`, `same_org`) derive nothing |
| `numerics` | Honest about decimal safety | Dates, text matching and unknown handling are not numeric |

**Recommendation: `stdlib`**, with `functions` as the fallback. The reason is the one you gave: the aim is a library every pack, tool and generated rule can assume, broad by design, and no other candidate says that without being either narrow (`formulas`, `calc`, `measures`) or empty (`functions`, `compute`). The cost is a spoken clash with Python's standard library, which the import path (`jazzx_sdk.stdlib`) removes in code. Your call; the name is the cheapest thing here to change before stage 1.

## What I did not verify

- I did not read the rest of `finance/` (periods, package, filings, workbook), `formal/compiler.py`'s use of `util/math`, or `pack/assessment.py`'s use of the DSL beyond the import.
- macer's engine (`income_worksheet_engine.py`, `formula_engine.py`) was not read; the design doc and commit titles are the only evidence for the engine's shape, and I could not tell where in Kernel it now lives.
- Importer counts are files that mention the module, not call sites, and not the downstream repos that vendor `rules_lib` text.
- The claim that two functions' answers differ in the last digits (calculator against `finance.metrics`) is by reading float against Decimal arithmetic, not by running both.
- I did not check whether the import-linter tiers allow a package at the position the placement section proposes; stage 1 would settle it.
