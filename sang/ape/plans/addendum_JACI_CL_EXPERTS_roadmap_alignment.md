# Addendum - plan_JACI_CL_EXPERTS_ON_PACKS - alignment with the platform roadmap and Studio decks

Author: Virendra Mehta. Applies to `plan_JACI_CL_EXPERTS_ON_PACKS.md`; the same changes are applied in place in that plan.

Sources: the roadmap's Knowledge and SDK track (KYC, AML and clinical intake prototypes as generalization tests; the SDK proven on commercial lending before financial-crime and clinical suites depend on it).

## Changes

1. New P7, a generalization test on financial crime: bind the Policy Expert to `config/packs/aml_investigation_core` in the four-binding shape (AML, Sanctions, KYC/CDD, Fraud; thin seed packs where none exist) with one cross-Pack contract on the AML binding, and run the partial-name sanctions story as gold, edge and regression cases. Depends on japes 2.7.0 Phase 3. Reason: the roadmap uses financial crime as the proof that the SDK generalizes; the Expert surface is the piece most likely to carry domain assumptions, so it is the piece to test.

2. Version-bump guidance removed from the guardrails. The `japes` pin in `pyproject.toml` still moves when the japes phases land; that is a dependency pin, not release versioning.

## Not changed

- P1 to P6 are unchanged. The roadmap's second commercial lending program on the same pack contract and the Acra-specific calculators and access controls are Acra plan items, not Expert plan items.
