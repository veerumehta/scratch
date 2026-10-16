# Typed conditions in AdjudicationAgent

Plan, sonnet-runtime, 2026-10-14. Status: built on v2.6.3 (T1 `37a6c71f`, T2 `69516358`, T3 `201bf005`, T4 `2b61f6b9`, T4b `851a6126`, T5 `fb0bc9c1`); review owed. Source: gap 1 (and its validator half, gap 6)
of `note_parity_adjudication_20261012.md`. Decisions owed are in section 6.

## 1. Why

An adjudicated job that reaches a status such as CONDITIONAL carries conditions as free strings
(`segment.py::_BatchItemVerdict.conditions: list[str]`, `condition_evaluator.py::_procedure_outcome`). So:

- nothing says a condition is a missing document or a verification, who owes it, or when;
- "CONDITIONAL needs at least one condition, other statuses none" is unchecked;
- a condition's identity is its normalized text (`_condition_key`), so a rewording on a rerun is a new condition;
- a natural-language rule's `batch_outcome` drops its conditions;
- the vote collapse can lose a CONDITIONAL's conditions (PASS and CONDITIONAL are both SATISFIED).

## 2. Shape

New model in `fabric/canonical/policy.py`, beside `ProcedureOutcome`:

```
OutcomeCondition{id, kind, title, description, timing, party, resolution, subject_id, documents}
```

- `kind`, `timing`, `party` are strings checked against vocabularies the pack declares (pack data, not SDK enums).
  Declared once per job set as `ConditionVocabulary{kinds, timings, parties}`; a pack with none keeps `kind` etc. empty
  and conditions stay as `title` + `description` only (tolerant first).
- `ProcedureOutcome.carries_conditions: bool | None`. `True`: at least one condition required. `False`: none allowed.
  `None` (default): unchecked, so existing packs are unchanged.
- `id`: stable, assigned by the step, not the model. Format `C<n>` continued from a watermark on `RerunBasis`
  (`condition_watermark: int`). A carried condition keeps its id; a restated one is matched by the model naming the
  prior id in `restates`, not by text.
- `resolution` is one of the vocabulary's resolution values (a pack's data, e.g. auto-pass, manual clear, waived,
  override); empty while open.
- `documents`: document registry ids the condition names (validated against the registry when the pack has one).
- `subject_id`: at most one, validated against the run's subject roster. The roster is built by the step from a
  pack-named record collection and shown to the model as tokens (`S1`, `S2`), never raw ids; the validator maps tokens
  back and rejects unknown ones. A pack flag `one_subject_per_condition` (default true) is pack data.
- Vocabularies (kinds, timings, parties, resolutions) are pack data. The production condition ontology
  (`mortgage-app-ontology/.../condition_ontology.json`) is the source for a pack's values and goes into the pack's
  YAML, never SDK code.

Storage: `RuleOutcome.narrative["conditions"]` becomes a list of `OutcomeCondition` dumps. `outcome_conditions()`
returns `list[OutcomeCondition]` and reads the old `list[str]` form as `title=text` conditions, so prior runs
loaded through `RerunBasis.outcomes` still work.

## 3. Phases

### T1. Model and vocabulary (SDK, no behaviour change)
`OutcomeCondition`, `ConditionVocabulary`, `ProcedureOutcome.carries_conditions`, legacy-string reader in
`outcome_conditions`. Pack-lint rule: a `carries_conditions` outcome with no vocabulary is a warning, not an error.
Verify: model tests, round trip of a legacy string narrative.

### T2. Batch contract
`_BatchItemVerdict.conditions: list[_BatchCondition]` (kind, title, description, timing, party, `restates: str | None`);
`resolved` takes prior condition ids, not text. `_render_batch_prompt` lists each prior condition with its id and the
vocabulary's allowed values. `batch_outcome` takes the typed list; the NL evaluator keeps conditions when the pack
declares them (today dropped). Update `batch_header.md`.
Verify: a stub answer with an unknown id in `resolved` does not resolve anything.

### T3. Validator and retry
A validator on the batch model, run through `run_kit.ValidatedOutput`: kind, timing and party in the vocabulary;
`carries_conditions` honoured against the item's status; `resolved` and `restates` name known ids. Errors name
locations, never values (the existing `ValidatedOutput` rule). Bounded by the existing retry budget; after it, the
rule is INDETERMINATE `CONDITION_UNEVALUABLE` rather than a silently repaired answer. Validators read the
declared outcomes and prior ids through a context variable (same seam gap 6 uses for page counts, so T3 builds it
once and gap 6 reuses it).
Verify: a CONDITIONAL with no condition triggers one retry carrying only the directive; two bad answers go INDETERMINATE.

### T4. Ids, carry and vote
Step assigns ids from the watermark after the vote; `_carry_conditions` matches on id; `RerunBasis` gains
`condition_watermark`, written by `basis_from`. Vote: collapse stays on verdict, but the winning vote is the one with
the most conditions among tied statuses (already `steps.py:1371`), and conditions of tied votes that share the winning
status are unioned by `restates`/title key. This is the narrow half of gap 7; collapse on pack status order stays gap 7.
Verify: a rerun that rewords a condition keeps its id; a 2-replica CONDITIONAL/PASS tie keeps the conditions.

### T4b. Subjects
Roster from a pack-named record collection, tokens in the prompt, mapping back in the validator (T3 seam),
`subject_id` on the typed condition, detokenizing names in free text. Verify: a condition naming an unknown token retries.

### T5. Surfaces
`steps.py` output: `adjudication.open_conditions` (flat, with rule id) beside `settled`. Plato run page and the
export read the typed fields; the CHANGELOG, README adjudication section and `docs/` pack guide (vocabulary) updated.
Scorers: `condition_present` (CONDITIONAL carries a typed condition) added next to `VerdictAgreementScorer`.

## 4. Family to enumerate before editing (section 8 of the project rules)

Every reader or writer of `narrative["conditions"]`: `segment.py` (render, carry, resolve), `agent.py:96` (prior),
`steps.py:1366-1371` (vote tie-break), `condition_evaluator.py` (NL and procedure `batch_outcome`, `_ProcedureVerdict`,
`_procedure_outcome`, the non-batched evaluate path at ~773), `pipelines/rerun.py` (`basis_from`), Plato run page
scripts, export, eval scorers, tests at `test_adjudication_segment.py` / `test_adjudication_agent.py`. T1 starts with
a grep of `"conditions"` across `plato/` static JS, which this plan has not done.

## 5. Out of scope here

Cross-rule dedup (gap 4); resolution messages and cites per condition, externally
created conditions (gap 5, builds on the ids from T4); page-range cite validators (gap 6, reuses T3's seam);
collapse on pack status order (gap 7).

## 6. Decisions (user, 2026-10-15)

1. Kinds are pack-declared only (no SDK default kinds); the SDK ships timings, parties and resolutions from the
   production condition ontology as a packaged YAML a pack overrides per field.
2. `carries_conditions` defaults to `None` (unchecked); `DEFAULT_OUTCOMES` sets it on its own outcomes.
3. After exhausted validator retries the batch is INDETERMINATE (the retries are per call, so every rule in that
   call); no `strict_conditions` flag. An unknown subject id is refused the same way.
4. Roster: a `subjects:` block on the job set naming the record collection and its id and display fields; no
   block, no subject checks.
5. Legacy string conditions are read forever, written only typed; they get ids on first carry.

## 7. Deviations from the plan

- `subjects:` lives on `JtbdTemplate` (read at run time through `pack_jtbd_template`), not on the imported job set.
- The vocabulary lives in `adjudication.yaml` (`AdjudicationAgentSpec.conditions`), not beside the outcomes.
- The scorer is `ConditionTypingScorer` (share of open conditions with an id and the declared fields), opt-in.
- Not done: the non-batched `ProcedureEvaluator.evaluate` path still takes text conditions with no vocabulary check;
  the retry cost is per call (see the changelog). No export reads `narrative.conditions` (checked 2026-10-15: the
  JTBDSet export is of the pack's rules; a run's conditions reach readers through `open_condition_rows` and the runs page).
