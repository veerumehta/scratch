# Changelog

The earlier changelog is archived as `CHANGELOG.md.gz` (last changed Oct 13); this file starts again from here.
Entries are terse; the plans in `docs/plans` and `git log` carry the detail.

## [Unreleased]

### Changed: workshop bank Expert packs (branch `cl-experts-p1`)
- Relocked japes at `plato` 116ac14e (2.6.5) for the Expert surface (`41fa263`).
- `workshop_bank_cl_of` declares its policy Expert as an advisory `api_service` surface binding, checked with japes'
  `check_non_widening`; the overlay lost a narrowing above the binding's ceiling (`7e52662`).
- Two story cases run on the Expert route (`check_compliance`, rule facts in `context`); the other ten are in
  `fixtures/cases_deferred/`, each naming what it waits for (japes E1 to E6, and 2.7.1 for playbooks). They move back
  when those land (`6d7adcc`).
