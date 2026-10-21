# Addendum - plan_JAPES_2_7_1_KNOWLEDGE_LOOP_CHANGE_CLASSES - alignment with the platform roadmap and Studio decks

Author: Virendra Mehta. Applies to `plan_JAPES_2_7_1_KNOWLEDGE_LOOP_CHANGE_CLASSES.md`; the same changes are applied in place in that plan.

Sources: the Knowledge Studio slides in both decks ("What an SME can do without writing code": maker checker, immutable atomic versioned publish, one click rollback, drafts never execute in production, Juno proposes every directive a change affects; "policy bundle" and "GSE bundle" in the roadmap glossary).

## Changes

1. Maker-checker is its own rule in Phase 2, separate from forum membership: the principal who authored or last edited a candidate version cannot approve it at any class, including `administrative`. Refusal reason `self_approval`, read from provenance and the audit trail, not from an author-set flag. Reason: the Studio deck states it as "an author cannot approve their own change"; the plan had only forum membership and approver classes.

2. Two acceptance items added to Phase 2: a `draft` asset is never served to a caller (the Expert route and `DefaultPolicyExpert` read `approved` and `deployed` only); rolling a pack version back restores every asset activation in that version atomically with one `rollback` audit event. Reason: "drafts never execute in production" and "one click rollback" are promises in the Studio deck; the mechanisms exist (`plato/api/packs.py` revert and archive, `pack/activation.py`) and the plan now tests them at the bundle level.

3. Vocabulary: where the plan says "a published pack version" it means what the product calls a policy bundle. A bundle is published, activated and rolled back as one unit; the per-asset class and gate decide what tests the bundle's publish must pass. Reason: the roadmap glossary uses "policy bundle" and "GSE bundle"; the plan should read the same way.

4. Phase 4's citation index gains `directives_citing(asset_id)` beside `cells_citing`, built from the pack's JTBD set (`pack/jtbd_align.py`, `jtbd_match.py`), so an impact report names every policy directive a change touches with the citing text as the reason. Reason: the Studio deck's "Juno proposes every directive a change affects, with a reason and a confidence" needs this index; the plan covered authority cells only.

5. Version-bump guidance removed from the guardrails.

## Not changed

- The six change classes, the gate table, the Curator proposal and Sentinel signal records, per-asset case binding and case stability are unchanged.
- "Effective dates so the version in force on a date is recoverable" is already covered by `pack/version_windows.py` and needs no plan change.
