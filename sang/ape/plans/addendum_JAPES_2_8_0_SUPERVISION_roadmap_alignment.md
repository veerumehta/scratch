# Addendum - plan_JAPES_2_8_0_SUPERVISION_COORDINATOR_AND_DOWNGRADE - alignment with the platform roadmap and Studio decks

Author: Virendra Mehta. Applies to `plan_JAPES_2_8_0_SUPERVISION_COORDINATOR_AND_DOWNGRADE.md`; the same changes are applied in place in that plan.

Sources: the Studio deck's Admin Center ("budgets and kill switches per action class"; "health, latency, cost per decision and drift") and the roadmap's core platform services track (budgets, quotas and circuit breakers; drift and implicit feedback).

## Changes

1. Phase 3's `RuntimeDowngrade` gains a `MANUAL` trigger: a platform owner's kill switch, tenant-scoped, on one action class or cell, to `recommend` or `refuse`, carrying the actor and a reason, applied through a Plato route and visible on every resolution it affects (`contributing_layers.runtime_downgrades`). The record shape changes accordingly: `evidence` becomes optional (Sentinel triggers), `applied_by` and `reason` are added (manual). Reason: the Admin Center promises kill switches per action class; without this the promise is a UI feature with no primitive under it.

2. A manual switch is lifted by the same forum path as an automatic downgrade; the actor who threw it cannot lift it. Reason: keeps the "seconds down, weeks up" posture symmetric and stops a kill switch being quietly reversed.

3. Scope note: budgets, quotas and spend ceilings stay in the `llm/` gateway. The downgrade record is the authority-side switch, not the cost-side one. Reason: the decks list both under one heading; the SDK keeps them in two places.

4. Acceptance for Phase 3 extended with the manual switch case.

5. Version-bump guidance removed from the guardrails.

## Not changed

- Generic supersession (Phase 1), coordinator objects and maker-checker (Phase 2), the six output kinds (Phase 4) and break-glass (Phase 5) are unchanged.
- Harness-based learning, memory as a first-class service and bring-your-own-agent adapters appear in the decks with no plan behind them; they are not folded into this plan.
