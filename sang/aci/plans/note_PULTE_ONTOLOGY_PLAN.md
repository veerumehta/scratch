# Pulte home mortgage: the ontology the policy pack lacks (plan, no build)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>
Date: 2026-10-30
Status: plan; read-only survey, nothing built or published. Written for opus-xrepo.

Plato's check on `pulte-home-mortgage-policy` 0.1.0 reports `no_ontology` (warning) and `unverifiable_rules`
(292 rules, error severity). Both come from one condition in `jazzx_sdk/pack/lint.py`: `pack.vocabulary is None`.

## What the SDK reads

- A pack declares an ontology in its manifest, one of two ways:
  - `vocabulary:` block: `chain` (SDK layers, today `jazzx-core`, `jazzx-finance`), an `aliases` file, and a catalog.
    The catalog is `catalog.schema.json`, a JSON Schema whose `$defs` are entities with `properties` (fields), or,
    when absent, it is derived from the conductor's input schema (`catalog_from_facts`: `Entity.field` names).
    Acra's pack uses this.
  - `ontology: ontology/<file>.yaml`: a concept graph (C&I's `ci_lending.yaml`).
- `lint_pack` resolves each rule's inputs, which are its condition's `reads` (a `procedure` condition's `reads` and
  `evidence_types`), against what the vocabulary supplies, and reports `unreachable_input` for a read nothing supplies.
  `_template_reads_outside_catalog` compares `jtbd_template.yaml` reads with `catalog_reads(catalog)`.
- Declaring any vocabulary clears `no_ontology` and `unverifiable_rules`. It would NOT, by itself, verify anything:
  all 292 imported rules carry `reads: []` and `evidence_types: []` (checked in the generated policy files), so
  there is no input to resolve. The 46 jobs that declare `loan_metrics` keep them under `domain_extensions.jtbd`
  only. So a clean report after a thin ontology would be a pass on nothing, which is what the finding warns about.

## Sources, and which is authoritative for Pulte's field names

| Source | What it holds | Count | Form |
|---|---|---|---|
| Pulte catalog 6.2.3 `loan_metrics` (kernel-lab `workflows/pulte-6-2-jtbds.json`) | the fields each job reads, as `Entity.field` with a label and an `indicator_context` | 46 of 115 jobs, 182 entries, 173 unique keys; 85 unique paths over 17 entities once `[borrower_type=Primary]`-style filters are dropped | `Entity[filter].field` |
| policy-workbench bundled seed `backend/policyforge/prompts/ontology/mortgage_ontology_v2.json` | MISMO 3.4 based mortgage ontology v2.0.0 | 49 entities, 690 top-level `Entity.field` | JSON Schema `$defs` (the catalog form the SDK reads) |
| policy-workbench `mortgage_jtbd_ontology_v1.json` | the JTBD document schema (JTBDSet, JTBD, InvestorRequirement ...) | 12 defs | JSON Schema; not loan fields |
| kernel-lab `workflows/data_ontology` | the database schema the evaluators read | 252 tables, 5,727 columns; evaluators use 185 tables, 1,842 attributes | snake_case tables and columns, not `Entity.field`; `jtbd_registry.json` has per-job doc types and section, no fields |

How they differ: the catalog's keys and the workbench seed share one vocabulary: after dropping filters, 84 of the
catalog's 85 paths resolve in the seed (17 of 17 entities exist; the one that does not is
`LoanCore.total_undisclosed_monthly_payment_usd`). Resolution follows nested paths such as `LoanCore.down_payment.*`.
The kernel-lab data ontology is a different vocabulary (database columns) and does not map to `Entity.field` without
a crosswalk; I would not use it for field names.

Authority. The workbench engineering note (`docs/engineering-notes/ontology.md`) says Knowledge Hub holds the
authoritative mortgage ontology and the bundled JSON is a seed, kept so a replica that never reached the Hub still
validates. Its test (`test_bundled_ontology_agreement.py`) pins the seed's internal agreement, not its equality with
the Hub. I cannot reach the Hub from here (its test docstring says dev machines have no APP_CONFIG access), so I
cannot say the seed is a faithful export; I can only say the catalog's keys agree with it at 84 of 85. So:
- authoritative for Pulte's field names: the Knowledge Hub mortgage ontology (not read);
- the best evidence in hand: the bundled seed v2.0.0, which the catalog's own keys match almost entirely;
- the catalog's `loan_metrics` is authoritative for which fields each job reads, not for what a field means.

## Proposed shape (for the user's decision)

1. `catalog.schema.json` in the policy pack, taken from the seed, with a provenance stamp (source file, version 2.0.0,
   sha256, "bundled seed, not confirmed against Knowledge Hub"). Options for scope:
   (a) the 17 entities the catalog uses, about 85 fields plus what those entities define (small, reviewable);
   (b) the whole seed (49 entities, 690 fields; a faithful copy, but it claims more than the catalog uses).
   I would take (a) and keep the stamp, so the pack does not assert fields nobody reads.
2. A `vocabulary:` block naming the chain (to verify which SDK layer fits a mortgage pack; `jazzx-finance` is the
   candidate) and the catalog.
3. Declared reads: the 46 jobs' `loan_metrics` become the rules' `reads` (status: declared by the catalog). The
   importer does not carry them. That is an SDK change (importer to condition reads, consumer-neutral), for
   sonnet-runtime with a repro: `import_jtbdset` on the catalog gives 0 rules with reads although 46 jobs declare metrics.
   Then lint would verify each read against the catalog and `unreachable_input` would mean something.
4. The one missing key and the filter syntax go to the user, below.

## Content questions for the user

1. Which ontology version is Pulte's: the Knowledge Hub's current one, or the bundled seed v2.0.0? Can someone export
   the Hub's document so the pack carries the real artifact, with its id and version?
2. `LoanCore.total_undisclosed_monthly_payment_usd` is in the catalog and not in the seed: a seed gap, a catalog typo,
   or a newer Hub field?
3. 99 of the 182 catalog entries (97 unique keys) use filters (`Asset[borrower_type=Primary,asset_type=GiftFunds].current_balance_usd`,
   `Liability[is_undisclosed=true]...`). A catalog declares entity fields, not filtered views: do we record the
   filter as part of the read (a string the engine understands) or map it to separate fields?
4. 69 of 115 jobs declare no `loan_metrics`: do they read nothing, or is it undeclared? Pulte's call.
5. Scope (a) or (b) above, and whether Pulte wants its own ontology additions kept in the pack or only in the Hub.

## Republish and version

A published version is immutable and a changed pack at 0.1.0 is refused. The ontology, the declared reads and (from
runtime's adoption build) citations and units all change the pack's behavior, so this is material:
- propose `pulte-home-mortgage-policy` **0.2.0** for the republish that carries the ontology and the declared reads;
  citations and units, if they arrive in the same publish, ride along in 0.2.0, otherwise they are 0.2.1;
- the assistant `pulte-home-mortgage-core` stays 1.2.0 (its `policy_pack_version_range` `>=0.1` still holds);
- the guideline pin stays G1 (`bd650af1...`) unless the guide edition changes;
- the blueprint ranges (`policy >=0.1`) resolve the newest live version, so no blueprint change is needed.
Not published; the number is a proposal for the user to approve.

## Not decided here

- Which SDK layer(s) a mortgage vocabulary chains to (`jazzx-finance` covers rates and amounts; no mortgage layer exists
  under `jazzx_sdk/vocabulary/data`, only `jazzx-core` and `jazzx-finance`). A mortgage layer would be a consumer-neutral
  SDK addition, or the pack carries everything in its own catalog.
- Whether Plato's check then reports anything other than the 292 `rule_without_citation` warnings (units, a separate gap).

## Review findings left open (adversarial review 20261031T041258Z, 2026-10-31)

Fixed in the working tree (uncommitted): rulemap Part E total (642), topic index regenerated on the SDK reader (388 units; B6-1-01 spans 1839092-1844599, no `B2-1.5-02 (2)`),
mapping `edition_flags` (B3-5.3-09 added, undated 156), `jtbd_template.yaml` comment.

- TODO(pulte-ontology-keys), medium, blocks the JTBDSet export readiness lint: `LoanCore.total_undisclosed_monthly_payment_usd` (absent),
  `LoanCore.down_payment.total_amount_usd` (nested object, not a scalar key), `Borrower.current_address` and its `[borrower_type=...]`
  forms (`ResidenceAddress` is an allOf, read as a relationship), bare `Borrower` in COM-DEC; selector field `Liability.is_undisclosed`
  is missing. Same Knowledge Hub content questions 2 and 3 above; no field is invented here. Either the Hub export adds the fields or the
  jobs are re-keyed.
- TODO(pulte-catalog-scope), low: `catalog_to_ontology` reads 22 entities, not 17 (Address, BorrowerIdentifierPair, CreditScore,
  LoanOriginatorAssignmentAudit, ResidenceAddress pass its entity test); their scalar fields reach writers as bare names.
- TODO(pulte-percent-unit), unknown importance: no `x-unit` on the percent types, so a writer's scale for `*_percent` is unstated.
  Needs a japes answer on the default when `units` is empty.
- TODO(rulemap-null-key), low: chapters B2-3 and B3-2 use a bare `null:` key (loads as None) where totals say `no_score`.
- TODO(rulemap-models-null), low: `source.models` is null; the model names are not recorded.
- TODO(topic-index-null-dates), low: 10 topics with `date: null`, C3-5-02's title looks cut at a wrapped heading.
- TODO(topic-index-b4-1.4-01), low: the index has no B4-1.4-01; retired in June 2026 or folded into B4-1.3-12, undetermined.
- TODO(topic-index-escapes), low: titles keep `\(` escapes; the mapping file does not.
- TODO(mapping-undated-from-path), low: 156 undated cortex sections, many carry a date in `chunk_path`.
- TODO(mapping-absent-flag-table), low: `cortex_sections_absent_from_rule_map: []` was checked against the topic index, not this file's table.
- TODO(mapping-p-best-name), low: `p_best` is the cheap-pass score, not the best job p.
- Acra, low, not edited (0.3.0 is active in Plato byte-identical; a comment edit would need a bump): `document_types.yaml:140` says a missing
  attestation can be reported but neither type is in `required_classes`; the 13 new fields are read by no rule (intended, per the model comment).
