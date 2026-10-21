# Addendum - plan_JAPES_2_7_0_EXPERT_SURFACE_AND_ANSWER_CONTRACT - alignment with the platform roadmap and Studio decks

Author: Virendra Mehta. Applies to `plan_JAPES_2_7_0_EXPERT_SURFACE_AND_ANSWER_CONTRACT.md`; the same changes are applied in place in that plan. This addendum records what changed and why, so a reader of the plan can see the deltas without a diff.

Sources: the platform roadmap deck (Knowledge and SDK track, "capabilities exposed to external entities at GA level") and the Studio capabilities deck (Domain Pack path, step 5 "Expert surfaces per audience, each with an autonomy ceiling"; "Both studios in full" slide, "three experts").

## Changes

1. Phase 3 is now "multi-Pack and per-audience binding". `ExpertBinding` is keyed by Pack and by audience: one binding per Pack, and within it one envelope per calling surface (the RM co-worker, the underwriter Workspace, an outside application under a service contract). Each envelope declares visibility and admissible question classes. Reason: the Studio deck promises Expert surfaces per audience; the plan had bindings per Pack only.

2. An Expert's ceiling stays advisory by construction. The per-audience "ceiling" the Studio deck mentions narrows visibility and question classes; a binding that grants an Expert any autonomy above advisory fails validation. Reason: Deck 4 rule 2 (it never holds authority) is a hard invariant and the two decks must not be read as loosening it.

3. The Expert route is named as part of the externally exposed capability set (packs, runs, assessments, evaluation, and now Experts) through `jazzx-plato-client`, with the same client test coverage. Reason: the roadmap's GA exposure list omits Experts; this is the SDK item behind "Expert surfaces" in the Studio deck.

4. Two Expert routes only, `policy` and `playbook`. The Evidence Expert named in older material and in the Studio deck's "three experts" is a Skill (`jazzx_sdk/skills/evidence`), not a surface. Reason: prevents a third route from being added on the strength of the deck wording.

5. Version-bump guidance removed from the guardrails. Release versioning is handled separately and is not part of this plan.

## Not changed

- The answer envelope (Phase 1), the Governor guard and the three Expert scorers (Phase 5) are unchanged; the decks do not touch them.
- "Bring your own agent framework through certified adapters" appears in both decks and is out of scope here; it is a runtime item, not an Expert surface item.
