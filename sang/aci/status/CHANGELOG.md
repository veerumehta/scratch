# Changelog

The earlier changelog is archived as `CHANGELOG.md.gz` (last changed Oct 13); this file starts again from here.
Entries are terse; the plans in `docs/plans` and `git log` carry the detail.

## [Unreleased]

### Changed: Acra DSCR pack 0.3.0 (`0ed0d27`)
- `LoanApplication` gains 14 optional fields the missing jobs read (LTV, cash in hand, product type, ARM index, margin and three caps, subordinate financing type, HELOC limit and balance, lowest recent listing price, lease rent, `reo_properties`); names follow the production ontology where it has them (`LoanCore.arm_index_type`, `arm_margin_percent`, `arm_*_cap_percent`, `ltv_percent`), provisional elsewhere. Nothing reads them yet.
- Document registry: One- to Four-Family Rider and Business Purpose Attestation (Exhibit 8), kind `closing`, read for nothing. Not classifier-measured yet.
- `DSCR-ESCROW-WAIVER-TERMS` reads its CLTV limit from profile key `escrow_waiver_cltv_max` (80), as the japes seed does.

### Security: mlflow 3.16.0 -> 3.17.2 (`77920c1`)
- Clears Dependabot #54 (SSRF via scorer kwargs) and #55 (FileStore trace-ID path traversal); lockfile only, no version bump.

### Changed: Acra DSCR pack vocabulary (`acra-dscr-policy` 0.2.19)
- Adopted the seed's `aliases.yaml` (Acra terms over the SDK layers `jazzx-core` and `jazzx-finance`) and the manifest's
  `vocabulary:` block, so jaci's pack and Plato's seed copy match; `SYNCED_FROM` stays seed-only.
- Relocked japes at `plato` cb256157 (2.6.6, jazzx-plato-client 0.2.6); opentelemetry 1.45.1 comes with it.

### Changed: workshop bank Expert packs (branch `cl-experts-p1`)
- Relocked japes at `plato` 116ac14e (2.6.5) for the Expert surface (`41fa263`).
- `workshop_bank_cl_of` declares its policy Expert as an advisory `api_service` surface binding, checked with japes'
  `check_non_widening`; the overlay lost a narrowing above the binding's ceiling (`7e52662`).
- Two story cases run on the Expert route (`check_compliance`, rule facts in `context`); the other ten are in
  `fixtures/cases_deferred/`, each naming what it waits for (japes E1 to E6, and 2.7.1 for playbooks). They move back
  when those land (`6d7adcc`).
