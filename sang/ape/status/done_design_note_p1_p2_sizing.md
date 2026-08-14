# Design note: sizing P1 (`run_replicated_segments`) and P2 (`EnsembleCollapse`)

Local design note (gitignored). Author: Virendra Mehta / measured by Claude, 2026-08-02.
Companion to `reasoner-chassis-analysis.md` (defines P1/P2) and `policy-ir-abstraction.md` (P8,
`evaluator.stochastic`). This is the "Phase 0" measurement the build-sequence calls for, turned
into concrete sizing decisions for the two primitives it's meant to size — not a build plan for
either primitive yet, just the parameters/defaults their eventual implementation should carry.

## The data behind these decisions

Real measurement against `integ_data/loan_1_sarah`'s "Appraisal Review" section (3 real JTBDs:
`APR-CLT`, `APR-RPT`, `APR-AVA`), gpt-5.2, ~$0.20 total spend, run twice (a bug in the first pass
— shared loan-program-detection cost contaminating the sequential bucket — was caught and fixed
before trusting the numbers):

| | Sequential (`verify_jtbd` ×3) | Batched (`verify_all_jtbds` ×1) |
|---|---|---|
| Wall-clock | 33.8s | 13.2s |
| Tokens | 119,852 | 56,371 |
| Cost | $0.06 | $0.03 |

- Batching: ~2.1x fewer tokens, ~2.6x faster, **identical findings** both ways.
- k=3 ensemble: 3 independent batched replicas agreed on every JTBD, 9/9 — zero measured
  variance reduction, at the full 3.1x cost multiplier (176,606 vs 56,371 tokens).

Caveats, stated plainly: one fixture, one section, 3 JTBDs (one of them a free synthetic
`NOT_APPLICABLE`, so only 2 JTBDs actually exercised the LLM) — a real data point, not a
statistically robust sample. The quick-test `max_turns=4` config forced a retry-continuation on
nearly every call in both paths, inflating absolute costs roughly equally — the *ratio* is more
trustworthy than the absolute numbers. Re-running against a second, larger fixture (ideally one
with a JTBD known to be genuinely judgment-heavy, where replica disagreement is plausible) would
strengthen the P2 decision below; not done yet.

## P1 sizing decisions

1. **Batched-prompt-per-segment is the right default shape.** Confirmed, not just asserted —
   adopt the `run_replicated_segments` signature in `reasoner-chassis-analysis.md` §4/P1 as
   designed: one agent call per (segment, replica) covering every applicable item in that
   segment, not one call per item.
2. **`precompute` (once per segment, outside the replica loop) is a load-bearing separation, not
   a nice-to-have.** The methodology bug in this measurement's own first pass — a shared,
   one-time cost (loan-program detection) silently bleeding into a per-path measurement because
   nothing structurally separated it — is a small real-world proof of exactly why P1's signature
   keeps `precompute` distinct from the replica loop. Carries a concrete follow-through: whatever
   tracing wraps this primitive (`RunTracer`/`on_step`) should tag precompute-phase spans
   distinctly from per-replica spans, specifically so a chassis operator reading a cost dashboard
   doesn't make the same mistake this measurement did.
3. **Preserve the zero-cost applicability short-circuit.** `APR-CLT`'s synthetic `NOT_APPLICABLE`
   (no LLM call at all) is real and already correct in MACER today. P1 should treat "skip
   entirely, no model call" as a first-class outcome of the per-item plan, not an incidental
   JTBD-specific hack — this is the runtime half of P8's `applicability: Condition` field.
4. **`session_for(segment, replica)` — unchanged.** No new data from this measurement bears on
   session-scoping directly; the earlier code-reading analysis (distinct sessions per replica so
   cache keys scatter) stands as designed.

## P2 sizing decisions

1. **Default `replicas=1`, not 3.** MACER's k=3 was inherited, not measured — this session's own
   Phase 0 data is the first real measurement of it, and it shows a 3.1x cost multiplier for zero
   observed benefit on real (if limited) obligations. A chassis primitive shouldn't bake in an
   unmeasured assumption just because the client it was extracted from happened to default to it.
2. **Gate replication on `evaluator.stochastic` (P8), not a blanket per-pack setting.** For
   `stochastic=False` (deterministic-leaning) rule kinds, force `k=1` unconditionally — no reason
   to pay for replicas on a check that isn't actually variable run-to-run. For `stochastic=True`
   (`natural_language`, genuinely judgmental) rules, `k` becomes a pack-tunable parameter with
   *no* SDK-shipped default of "3" — the pack decides its own cost/risk tradeoff per obligation
   class, informed by its own measurement, not a number carried over from MACER by convention.
3. **Exclude failed replicas from the vote by construction.** Independent of whatever `k` default
   is chosen, `reasoner-chassis-analysis.md`'s own P2 bug-to-fix (a replica that exhausts retries
   synthesizes an `ERROR` row that silently dilutes the majority vote — `jtbd_runner.py:456-485`)
   needs the `EnsembleCollapse` contract to structurally exclude failures from the start
   (`excluded: Sequence[Failure]` in the `collapse()` signature already anticipates this) — not a
   later patch once someone notices the dilution in production.
4. **New option worth naming for judgment-heavy rules, prompted directly by this data**: instead
   of a uniformly high `k` as the default way to buy safety on stochastic rules, prefer
   *escalate-on-disagreement* — start at a low `k` (1 or 2), and only spend more replicas (or
   route to a human) when a cheap secondary signal suggests real uncertainty, rather than paying
   3x on every single judgment call regardless of whether that particular one is actually
   ambiguous. `AnyEscalate` (already named in §6 for AML's asymmetric-risk profile) is the natural
   home for this — worth considering as the *default* posture for stochastic rules generally, not
   just AML's special case.

## What this doesn't decide

Whether `k>1` genuinely helps on rules that are *actually* judgment-heavy (this fixture's two
LLM-requiring JTBDs — confirm document presence, compute a value from stated figures — were both
closer to mechanical verification than genuine judgment; something like "does this letter
adequately explain a large deposit" would be a better stress test for whether ensembling earns its
cost). Re-running Phase 0 against a JTBD picked specifically for likely disagreement is the
natural next measurement before committing P2's stochastic-path defaults further than "no baked-in
3."
