# Two read-only answers for jaci's Revolution review (sonnet-runtime, 2026-11-10)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Read from the v2.7.1 tree and run against the in-process code (no live Plato, no network, no spend). `[V]` is read or run here; `[U]` not verified.

## 1. Does the assessment path see `domain_extensions.jtbd.source_text`? No

- The reasoner is shown the rule's condition, not its metadata. For a `ProcedureCondition` (what the JTBD importer writes) the prompt is `PURPOSE`, numbered `STEPS`, `CHECKS`, `OUTCOMES` (each `status: criterion`), `EVIDENCE TYPES TO REVIEW` and the evidence the rule reads [V `fabric/canonical/condition_evaluator.py` `_render_procedure`, line 712; the adjudication batch prompt `agents/adjudication/segment.py` `_render_batch_prompt` renders each rule through the evaluator, `render_for_batch`]. Nothing in either reads `domain_extensions`.
- Where `jtbd.source_text` is read [V grep]: `pipelines/policy/jtbdset.py` `_render` (an export of an imported block nobody edited returns the stored text when its `source_digest` still matches the condition, so an unchanged set round-trips), `pack/jtbd_match.py:134` (the matcher compares imported text), `pack/jtbd_import.py:164` (the variants a two-program import keeps), `pipelines/policy/ledger.py`. The only other `domain_extensions.jtbd` key the runtime reads is `section` (`agents/adjudication/planner.py:99`, to group rules into a segment).
- So outcome text the importer loses from `outcomes` or `steps` is not recovered at assessment time: the reasoner decides from the lossy condition, and `source_text` stays a record for export and matching. A rule whose outcomes lost their criterion will be assessed against the lost version. The fix has to be in the importer (as `sonnet-packs` is doing), or the rule's `checks`/`steps` have to carry the text.

## 2. A string metric written to a boolean catalog field: rejected or stored?

It depends on which boundary the value crosses; none of them stores `'Reconciled'` in a boolean as a string. Which one jaci's COM-DEC metric crosses I could not tell from japes (the term "metric" as a value written to a catalog field is not a japes concept I found `[U]`).

| Boundary | What happens to a string such as `'Reconciled'` or `'Open Items'` |
|---|---|
| The catalog itself (`pack/catalog.py`): a field's `type: ["boolean", "null"]` | read as `bool` plus `nullable`; the catalog declares, it does not validate values [V docstring and `_TO_AUTHORED`] |
| A pack schema model (`util/schema_model.py`, what document extraction output is validated against): `anyOf [boolean, null]` | RUN: `'Reconciled'` and `'Open Items'` are rejected (validation error); `'true'`, `'yes'`, `'1'` and `1` are accepted and coerced to `True` (pydantic's lax boolean), `None` stays `None`. A `type` given as an array is refused when the model is built (`type must be a single name; write a union as anyOf`) [V] |
| The deterministic and formal fact boundary (`FactBinding`, `fabric/canonical/facts.py` `typed_scalar`; `formal/json_rules.py`): a fact of type `boolean` | strict: anything that is not a JSON boolean raises (`expected a boolean`, `must be a JSON boolean`); no coercion, `'true'` is rejected too [V] |
| A Knowledge Hub entity whose ontology types the field as boolean | the hub validates against the ontology; the in-process mock does (`MockKnowledgeHubClient._validate_entity`, "failed ontology" error) [V]; the real hub's behavior was not exercised here `[U]` |

So: a free-text status word cannot go to a boolean field in Plato; it is refused where the field is validated, and where lax coercion applies only boolean-looking words pass. Keying the metric to a composite entity field of string type (as Pulte does with `COM_DEC_LM1`) is the shape that stores it.
