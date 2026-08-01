# Done: Line Vocabulary and Resolver

Author: Virendra Mehta · Completed 2026-07-27
Repo: japes (Phases 1-4) + jaci (Phase 4 proof step, cross-repo) · Landed: japes dev commits
`db563d1` (Phases 1-2), `02af9a9` (unrelated FR-PER follow-up, same day), `d2e8da0` (Phases 3-4);
jaci dev commit `3b22503`.
Plan: docs/plans/plan_JAPES_2_2_0_LINE_VOCABULARY.md (superseded by this file)

All 4 phases landed as planned. No deviations from the acceptance criteria.

## What shipped

- `jazzx_sdk/finance/vocabulary.py`: `LineVocabulary`/`LineDefinition`/`Recognition` (Phase 1) —
  a pack's declared, versioned chart-of-accounts vocabulary, the SDK ships none. `resolve()`/
  `Resolution`/`MatchKind` (Phase 2) — matches a raw (key, label) pair, strongest tier wins,
  ambiguity at the same tier resolves to `unmatched` naming every tied candidate.
- `jazzx_sdk/finance/structure.py::structure_statement(..., vocabulary=...)` (Phase 3) — when
  supplied, the extraction prompt carries the closed set of canonical keys for the statement
  type, with an explicit null-key escape. A key returned anyway that still doesn't resolve is
  nulled and recorded in the new `StructuredStatement.vocabulary_gaps` (`VocabularyGap`) rather
  than silently accepted. Also populates each line's `SpreadLine.semantics` from the vocabulary's
  declaration. Omitting `vocabulary` leaves behavior exactly as before.
- `jazzx_sdk/expressions/evaluate.py::ResolutionContext.vocabulary` (Phase 4) — a `SCOA_LINE`/
  `DOCUMENT_FIELD` binding's canonical `ref` resolves through a supplied vocabulary instead of
  requiring `lines` to already be keyed by that ref (`lines` may instead be raw-keyed).
- 24 new tests: `tests/test_finance_vocabulary.py` (18), `tests/test_finance_structure.py` (+6),
  `tests/test_expressions_evaluate.py` (+3).

## Acceptance criteria — verified

- Phase 1: YAML round-trip with no loss; two lines declaring the same alias fail to load, naming
  both (`test_duplicate_alias_key_fails_to_load_naming_both`) — caught and fixed a real bug in the
  first draft of this exact validator (it compared canonical-key *strings*, so two distinct lines
  sharing the same key with zero aliases slipped through; fixed to compare by line index).
- Phase 2: a representative-YETI-lines fixture resolves everything, with the unmatched set
  explicitly reported, not silently empty; an ambiguous match resolves to `unmatched` naming both
  candidates.
- Phase 3: without a vocabulary, behavior is provably unchanged (`test_without_vocabulary_...`);
  with one, the prompt carries the closed set and a disobedient model response is nulled and
  recorded as a gap rather than accepted or invented around. Not literally run against a live
  LLM call against the real YETI 10-K (no live-LLM harness available in this environment) — proven
  structurally instead: every code path that could accept an out-of-vocabulary key is exercised
  by a test showing it doesn't.
- Phase 4: `dsl_catalog` (jaci) computes identically with `_CANDIDATES` removed and a vocabulary
  supplied, asserted against the existing sixteen-case parametrized fixture — all 16 pass
  byte-identical. The module-local `_VOCABULARY` built for this is explicitly *not* the authored
  pack-YAML chart of accounts (that's `plan_JACI_CL_CHART_OF_ACCOUNTS_AND_CATALOG.md`'s own
  Phase 1) — it's this plan's own proof vehicle, covering the same 13-key inventory `_CANDIDATES`
  did.

## Notes for next time

- `plan_JACI_CL_CHART_OF_ACCOUNTS_AND_CATALOG.md` Phase 2's `dsl_catalog.py` bullet is now
  effectively pre-satisfied by this plan's Phase 4 proof step — when that plan runs, its real job
  there is replacing this module-local `_VOCABULARY` with the authored pack-YAML one (plus the
  `spread_template.yaml`/`template.py` collapse, which this plan did not touch).
- Reclassification/break-out rules (FR-MAP-3/4), many-to-one rollups, and customer-template-derived
  vocabularies remain out of scope, as the plan said.
