# Plan: the SDK says case and subject, never loan (sonnet-runtime, 2026-10-30)

Plan only, for opus-xrepo and the user; nothing built. Inventory by grep over `jazzx_sdk`, `plato`, `jazzx_plato_client` (py, md, yaml, json, html, js);
counts are files/hits and exclude `tests/` and other repos. The metrics-key literal is already reduced to one constant (`METRICS_KEY`) by the import-reads
work, but seven literals still bypass it (below).

## 1. Two words, not one
- **Case**: the unit of work (`CaseContext.case_id`, stable across trace segments and handoffs; `state`; `parent_case_id`/`source_case_ids`). One subject can
  have several cases (the same loan runs as two cases either side of the funding gate), so nothing may assume one subject has one case.
- **Subject**: the entity the case is about (`CaseContext.subject`: mortgage a borrower or loan, KYC a customer, AML an alert or customer, healthcare a patient).
  The packs already name it: `pack_manifest.yaml` has `subject_field: loan_id` (read by `pipelines/kinds.py` `CasePlan.subject_field` and
  `pack/case_runs.py`), and `eval_subject_baseline` is keyed by subject. `loan_id` in Acra's data is therefore a **subject** id, not a case id; do not collapse them.
- One inconsistency to fix on the way: `evaluation/experiments.py:165` glosses subject as "(a loan, a case)", which merges the two words.

## 2. Inventory, classified
| Name | Files / hits | Kind | Case or subject | On a wire or persisted shape? | Neutral name |
|---|---|---|---|---|---|
| `loan_metrics` (JTBDSet key) | 4 / 11: constant `jtbd.py:78`, `jtbd.py:536` (the writer's output field, so also a prompt/schema), literals in `jtbdset_export.py:98`, `jtbdset_lint.py:169,181,229,242`, `jtbd_match.py:121,162` | interchange key | subject | **JTBDSet files** (Pulte, Acra, kernel-lab, jaci) and the model's output schema | key configurable per pack; SDK default `subject_metrics` |
| `loan_id` | 10 / 13: docstrings (`concurrency`, `evaluation/qa.py`, `aggregate/portfolio.py` example), `fabric/graph/store.py` (`loan:{loan_id}` triples), seed packs (`subject_field: loan_id`, schemas, ontology) | identifier | subject | graph subject IRIs `loan:<id>` (persisted); pack schemas (pack data) | `subject_id`; pack data keeps its own field, named by `subject_field` |
| `loan_collection_id` | 1 / 2 (`concurrency/guard.py` docstring) | docstring | subject (the set of a subject's documents) | no | `subject_id` |
| `loan_number` | 2 / 4: `tools/documents/split.py` `IDENTITY_KINDS`, page-identity prompt | identity kind | subject | the page-identity output (`kind:value` keys) and its prompt | `subject_number`; the host's kinds are a parameter |
| `loan_docs`, `loan_dir`, `loan_packet`, `Loan_Application` | 1+1+1+4 files / 5+2+1+8: mocks, tool docstrings, KH and rag examples | example strings | subject / document class | `Loan_Application` is a classification label KH stores; the rest is docstrings and mocks | examples say `case_docs`, `case_dir`, a neutral class |
| `loan_purpose` | 15 / 62: seed packs (data field), `rules/lib.py` docstring examples and the 1.1.x manifests | pack data field and examples | subject attribute | the Acra schema and rules (pack data) | none in the SDK: it is the pack's field; docstring examples say `ctx['purpose']` |
| `loan_application`, `loan_applications` | 6 / 7: `fabric/rag/store.py:92` collection name, pack input schema names and document-type ids | pack data and one SDK literal | subject's input | a rag collection name (persisted) | pack names stay; the SDK's rag example becomes neutral |
| the word loan/loans in docstrings and comments | 42 py files | prose | mixed | no | rewrite by hand when a file is touched, not as a sweep |

Not found: any `loan_*` name in a Plato route, an API field or a DB column (grep over `plato/`), so no persisted column needs migrating. The persisted or
wire shapes are: the JTBDSet key, the model's output field for metrics, `loan:<id>` graph IRIs, the page-identity kind, a rag collection name, and the
`Loan_Application` classification label in KH.

## 3. The metrics key: `subject_metrics`, configurable per pack
`CaseContext` holds ids and references (`subject` as an entity reference, `evidence_bundle`, `decisions_history`, `state`), not field values, and
`CanonicalCaseFile` holds a timeline and findings, so a metric is not a read of `CaseContext`. A metric key (`LoanCore.dscr`,
`Asset[borrower_type=Primary].current_balance_usd`, `SubjectProperty.value`) names a field of the case's input data about the subject and its related entities,
the input the pack's `input_schema` types. So the honest word is **subject**: `subject_metrics` (not `case_metrics`, which would suggest measures of the case's
process or state, such as time in state). The pack config points at an existing concept already: `subject_field` names the subject id, and the JTBD
template's `metric_keys` name the fields.
- SDK default (internal, default export): `subject_metrics`.
- Interchange key per pack, in the export profile or `jtbd_template.yaml`: `metrics_key: loan_metrics` for Pulte and Acra, whose JTBDSet files carry that key.
  Import accepts the configured name (and the default); export writes the configured one. Resolved by one function, never a literal.

## 4. Rules for the change
1. **Code-only** names (docstrings, examples, mocks, private variables): renamed outright when a file is touched.
2. **Wire or persisted** shapes keep the old name readable with a one-time warning (as the `workspace=` to `turn_resource=` rename did, `warn_renamed`):
   the JTBDSet key through the pack's `metrics_key`; graph IRIs `loan:<id>` read for old data, written as `subject:<id>`; the page-identity kind `loan_number`
   accepted and normalized; the rag collection name through config. Cost: the JTBDSet files in storage need no migration (the pack declares its key);
   graph triples written by earlier runs stay under `loan:` until re-extracted (the helper deletes by subject, so it must delete both prefixes for one release);
   KH classification labels belong to the host.
3. **Pack data** (field names in a pack's schema, ontology, rules) is the pack's own domain language and is never renamed by the SDK.
4. Prompts and docs say case and subject; the prompt version moves, as for any prompt edit.
5. No assumption of one case per subject: `concurrency/guard.py` keys locks as `{loan_id}:{operation}` in its docstring; with two cases per subject the key
   must be able to carry `case_id` (a lock on the subject serializes both cases, which may be wanted or not: a decision to take, not to default).

## 5. A healthcare pack would write
Care case, subject patient: `subject_field: patient_id`; `input_schema: schemas/patient_encounter.json`; export profile `metrics_key: patient_metrics` (or
the default `subject_metrics`); entities such as `Encounter`, `Medication`; `jtbd_template.yaml` `metric_keys` for those fields. No SDK change is needed
for any of it once the metrics key is configurable.

## 6. Order
1. `metrics_key` in the export profile and template, one resolver, the seven literals through it, default `subject_metrics` (the only change with a wire cost; pack-declared, no data migration).
2. The model's output field and prompt (`loan_metrics` in `jtbd.py:536` and its prompt) to the key, with the old name accepted.
3. Code-only renames (docstrings, examples, mocks) as files are touched.
4. Graph IRI prefix, page-identity kind, rag collection name behind config with the warning, one release.
5. `experiments.py` gloss and the lock-key decision (section 4.5), after the user decides how two cases on one subject should lock.
Open for the user: whether the default is `subject_metrics` (my proposal) and whether graph IRIs move at all in 2.6.x.
