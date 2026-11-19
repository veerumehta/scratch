# Plan: `std`, all six stages, built in 2.7.6

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Executes `status/computation/note_shared_function_library_design_2026-11-18.md` (sections 2 and 5) and the eight Acra entries in `status/Acra/note_acra_code_generation_baseline_and_std_needs_2026-11-19.md` (section 2). Branch `v2.7.6`, cut from `plato`; the version stays 2.7.6 (no bump; stage 4 asks the user first). Owner `sonnet-runtime`; `sonnet-packs` confirms definitions and reports which generated rules lack a std function. No provider calls.

## Order

1, 2, 3, then 6 (generated `rules_lib`, guarded by `LIB_VERSION` and the manifests) before 4 (finance metrics to Decimal), then 5. The eight Acra entries follow stage 1 and need not wait for the later stages. Each stage is one commit round with its own tests and CHANGELOG entry, and is shippable alone.

## Stage 1: package, registry, first entries

- `jazzx_sdk/std/core/`: stdlib-only modules (`datetime`, `decimal`, `re`; no I/O, clock or randomness). `rules/lib.py` stays byte-identical at 1.1.2 and is registered as the first entries, not moved.
- `jazzx_sdk/std/registry.py`: an entry is name, signature, units, summary (first docstring paragraph), unknown policy (propagate, refuse, zero, raise), version, golden cases, the callable. `render_api` text for prompts comes from the registry.
- Import-linter tier: `sdk-layers` gets a new `std` row at the bottom, below `util`. `std` imports nothing else of the SDK (the registry reads `core/`, which is stdlib-only), so every package, `util` included, may import it. Checked by `lint-imports`.
- Tests under `tests/std/`: every entry's three golden cases run from the registry; `rules_lib` bytes and manifest 1.1.2 unchanged; the registry lists every public `rules_lib` helper; layering contract passes.
- Adding a function is one entry plus its goldens; the registry test needs no other edit.

## Eight Acra entries (after stage 1)

`loan_to_value` first, then `pitia`, `multiple_of`, `grid`, `middle_score`, `dscr`, `amortized_payment`, `interest_only_payment`. Signatures, unknown policies and goldens are the table in the Acra note. `dscr`, `pitia`, `amortized_payment`, `interest_only_payment` and `middle_score` encode policy-adjacent choices: ask `sonnet-packs` to confirm each definition against the guideline clause before it is built. Loan-purpose and property-type spellings stay in the case schema, not in std. A change to `rules_lib` content needs a `LIB_VERSION` decision (the user's 2026-11-02 ruling holds 1.1.2 until stage 6); until then these entries live in the std core and are not delivered to the child process.

## Stage 2: the DSL resolves calls through the registry

`expressions/evaluate.py`: `_eval_call` and `_eval_namespace` look up `min`, `max`, `cap` (and `if`, which stays lazy) by name; the period and entity functions stay evaluator-local because they need a `ResolutionContext`. Tests: the existing DSL tests pass unchanged (they pin builtins); one new test fails on the old code (a function registered in std is callable from both evaluators).

## Stage 3: calculator and conditions

`tools/calculate.py` gets the registry through the evaluator; the calculator description renders the function list. The prompt snapshot test shows the text change. No helper added in `tools/calculate.py`.

## Stage 6: `rules/lib.py` generated from the core

`rules_lib` is generated from the core and delivered whole; import name, `LIB_VERSION` and manifests unchanged. Guard: generated text compared with the shipped file, manifest diff empty, executor child-process tests.

## Stage 4: `finance/metrics.py` to Decimal entries

Functions become Decimal registry entries and the module re-exports them. Float last digits change: check the five source and two test callers first, and ask the user whether a version change is needed before committing.

## Stage 5: `util/math/ratios.py`

Keeps threshold and sensitivity logic; its division goes through the std core (`util` may import `std`, which sits below it); the finite check stays, because it guards the float the result model holds.

## Out of scope

Pack-declared functions (DSL-bodied), the income-worksheet engine decision, a `months_elapsed_prorated` entry, and anything needing a provider call.

## Verification

`ruff`, `lint-imports`, and the area tests per stage; the sharded suite once before the squash. No pytest before a commit round per standing rule, except the new `tests/std/` files and the DSL tests the stage touches.
