# Status: Caller Migration Plan — jaci & k9

Author: Virendra Mehta · Updated 2026-08-01
Repo: japes · Plan: docs/plans/plan_caller_migration_jaci_k9.md

**Too stale to execute mechanically as written — flagging rather than blindly working the
checklist.** The plan's own header dates its last full pass to 2026-06-07, against japes 1.6.3.
japes is now at 2.2.4 (2.0.0, 2.1.x, and all of 2.2.x have landed since), and jaci has moved from
whatever it was in June to v0.19.0 as of this same session — including multiple sessions' worth of
direct work on exactly the scenario this plan's PLAT-04 section names (`ci_spread`, which this
session alone took from v0.9.9-era through the entire governed-layer-UI plan). The plan is
explicitly self-described as "ONGOING — accumulates as JAPES-side freeze-prep lands," i.e. a living
checklist meant to be re-visited each time, not a fixed one-time task list — treating it as
executable-as-is two months and several major versions later risks checking against a jaci/k9
shape that no longer exists rather than the real one.

## What I did check, briefly

- The plan's own PLAT-04 item for `ci_spread` ("replace the bespoke single-pass flow... rename its
  colliding `class CaseFile`... decide promotion") predates essentially everything this session did
  to `ci_spread` (the entire governed layer UI, policy expert, corrections/approval loop, etc.).
  Whether `ci_spread` ever adopted `TransactionContext[LoanApplication, CreditDecision]` as this
  item asks, or evolved past the need for it, is a real open question — not re-derived here, since
  answering it properly means re-reading `ci_spread`'s current conductor shape against this specific
  claim, which is its own non-trivial audit, not a quick check.
- `japes_types.py:38`'s `Outcome` re-export item (PLAT-01) and the review-completion-handler items
  (XCUT-OUTCOME-01) are still plausible open items in principle (re-exports and missing handlers
  don't get fixed by unrelated feature work), but not verified against current jaci source in this
  pass — would need the same grep-and-read the plan itself specifies, done fresh.

## Recommendation

This plan needs a fresh audit pass (not a resume of this one) before any of its checklist items are
acted on — re-verify each `[ ]` against jaci's *current* source, not the June state, and likely
retire several items that later jaci work has already superseded independently. Not attempted as a
full re-audit in this pass; flagging the staleness is the honest deliverable here.
