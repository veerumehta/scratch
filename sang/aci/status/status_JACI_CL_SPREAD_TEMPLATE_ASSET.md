# Plan: Spread Template as a Pack Asset (VP-2 demo beat 1)

**Status: Phases 1-3 done (2026-07-26).** Phase 4 (capability fragment declaration) not done —
out of the scope the user asked for this pass; still valid future work per the plan below.

Author: Virendra Mehta · 2026-07-26
Repo: jaci · Baseline: 0.9.8 (dev) · Depends on: nothing unlanded. Sits beside plan_JACI_CL_MVDP_VP2_WEDGE.md Phase 1 (SpreadPackage), which is already in.

Driver: the VP-2 exec demo opens on the institution's desired outcome format and then walks input documents through the pipeline into that format. Today the outcome format exists only as the `_TEMPLATE` constant in `capabilities/commercial_lending/template.py`, so it cannot be shown as an institution artifact and it undercuts the code/config story the demo is meant to make. This plan moves the template to pack data and makes the map step inspectable. No change to spreading behavior, no change to `jazzx_sdk/`.

## Grounding notes (verified 2026-07-26 against dev)

- `capabilities/commercial_lending/template.py` holds `_TEMPLATE`: a list of `(section_label, [(row_label, locator), ...])`. A locator is `("is"|"bs"|"cf", *candidates)` for a statement line or `("m", metric_key, fmt)` for a computed metric. `fmt` is one of `n|p|x|d`.
- Consumers of `_TEMPLATE` in the same file: `template_rows`, `template_csv_text`, `curated_template_values`, `spreader_template_values`, and the `row_key(section, label)` cell key. Three row labels repeat across sections (Net income, D&A, Stock-based compensation), which is why `row_key` exists. Preserve it.
- `analytics._vals(spread, stmt_type, *candidates)` matches exact `line.key` across all candidates first, then falls back to label-substring across all candidates. It returns values only, with no record of which candidate matched.
- `spread_anchors.yaml` in the same package is the existing precedent for pack-side extraction data loaded through `ExtractionTemplate.from_dict`, read via a `@lru_cache` accessor. Mirror that pattern.
- `capabilities/registry.py` `Capability` model already carries a `fragments: list[str]` field described as the pack-fragment kinds a capability ships. `financial_spreading/capability.yaml` does not populate it.
- `spread_package.py` is in: `SpreadLineItem` carries `key`, `label`, `period`, `DecimalValue`, `ProvenanceEntry` with `SourceCoordinate`, and `Confidence`. This is the per-cell lineage the mapping view cites.
- `config/packs/ci-spread-core/` has manifest, ontology, policies, playbooks, evidence_types, pipelines, mode_tuning. No template asset.

## Phase 1 - The template asset

New `config/packs/ci-spread-core/spread_template.yaml`, authored as a faithful transcription of the current `_TEMPLATE` (all sections, all rows, same order, same labels). Shape:

```yaml
template_id: ci_credit_spread
label: "C&I Credit Spread"
units: thousands
sections:
  - id: income_statement
    label: "INCOME STATEMENT ($000s)"
    rows:
      - label: "Net sales"
        source: {statement: income_statement, accepts: [net_sales, revenue, net_revenue]}
      - label: "Depreciation and amortization"
        source: {metric: da, format: n}
```

Mapping from the existing locators: `("is", ...)` becomes `statement: income_statement`, `("bs", ...)` becomes `balance_sheet`, `("cf", ...)` becomes `cash_flow`, and the candidate tail becomes `accepts`. `("m", key, fmt)` becomes `metric` plus `format`. Statement rows carry no `format`; they render as `n` as they do today.

New loader in `template.py` beside the existing module docstring: a `@lru_cache` accessor reading the pack YAML and returning the same in-memory `_TEMPLATE` structure the rest of the file already consumes, so `template_rows`, `template_csv_text`, `curated_template_values`, and `spreader_template_values` are untouched. Resolve the pack path the way the pack loader does rather than hardcoding a relative path; fall back to the in-code constant if the asset is missing so nothing hard-fails mid-demo.

Design intent to state in the module docstring: the template is the institution's declared output contract and belongs to the pack. The machinery that fills it belongs to the capability. `accepts` is the declared alias vocabulary for a target row, replacing what was previously an undocumented candidate tuple.

Acceptance: `template_csv_text` output for the YETI spread is byte-identical before and after the port. A test asserts the YAML-derived structure equals the retired in-code constant.

## Phase 2 - Target template view (demo beat 1)

New Streamlit view rendering the template with no run behind it: sections, row labels, empty period columns, and the declared `accepts` terms visible per row on expand. This is the screen the demo opens on, before any document is touched.

Place it in the ci_spread demo page as a tab ahead of the existing Spread tab, and reuse it from the Concepts view where the other crafted assets (policies, checklist, playbooks, extraction template) are already surfaced, so the template sits alongside them as a pack asset rather than as demo furniture.

Caption to carry the claim: this file is pack config; a different institution's spread format is a different YAML, and the pipeline below it does not change.

Acceptance: the view renders from the YAML alone with no `FinancialSpread` in session state.

## Phase 3 - Mapping trace (demo beat 2)

The map step is currently invisible. Add a traced sibling to `_vals` in `analytics.py`:

```python
def _vals_traced(spread, stmt_type, *candidates) -> tuple[list, str | None, str]:
    """Values plus the candidate that matched and how: 'key' | 'label' | 'none'."""
```

Same matching order as `_vals`, which stays as-is so no existing caller changes. Add a `spreader_template_trace(spread)` in `template.py` returning, per `row_key`, the matched term and match kind, and for statement rows the `SpreadLineItem` provenance and confidence for each populated cell when a `SpreadPackage` is supplied.

Render it as a third column in the existing curated-versus-spreader comparison on the Spread tab: matched on `net_sales` (exact key), matched on `revenue` (alias, label), or unmatched. Rows resolving to a metric show the derivation formula from `MetricResult` instead.

Design intent: every filled cell in the output format answers where it came from, at both levels, which source line it mapped to and which source coordinate that line came from.

Acceptance: on the YETI spread, every populated template row reports a match kind, and the unmatched set is printed rather than silently blank.

## Phase 4 - Capability fragment declaration (optional, do only if Phases 1-3 are done)

Populate `fragments: [spread_template]` in `financial_spreading/capability.yaml` and have the capability's step registration assert the fragment resolves for the active pack. This makes the slide claim literal: the capability declares the contract, the pack supplies the knowledge.

Acceptance: composing the capability against a pack with no `spread_template.yaml` fails loud with a message naming the missing fragment.

## Out of scope

Authoring a second institution's template (the CRE anchors already demonstrate the swap), a mapping-confidence score on the target row, changes to `structure.py` or the LLM key vocabulary, the corpus schema import (foundation plan Phases 2-3), and any change under `jazzx_sdk/`.

## Sequencing

Phases 1 through 3 are the demo. Phase 1 is a data transcription plus a loader and carries the byte-identical test, so it lands first and de-risks the rest. Phase 2 depends only on Phase 1 and is the highest-value screen if time runs short. Phase 3 is the differentiator but is additive and can be dropped without breaking anything. Phase 4 is a two-line YAML edit plus an assertion; skip it under time pressure.

## Known weak spot to have an answer for

Mapping today is exact key, then label substring, then blank. Phase 3 makes that visible rather than fixing it. If asked how mapping accuracy is governed, the honest answer is that the alias vocabulary is now declared and inspectable per target row, and that the corpus schema work is where a validated line taxonomy lands. Do not claim a mapping confidence score exists.
