# YETI — our pipeline outcome vs. curated loan-package outcome

**Curated** = `docs/LoanSamples/YETI/Yeti Credit Package/YETI_Secure LOC_Comprehensive_Loan_Package.pdf`
(human-prepared $20M ABL underwriting package, drafted 2026-03-30).
**Ours** = ci_spread pipeline: spreader output (`output/ci_spread/yeti_fy2025_spread.json`) +
the pipeline's expected outcome (`tests/eval/gold_cases/ci/case_01_yeti.json`).

> Note: this compares our existing spread output + the gold-case expected outcome against the
> curated package. A fresh live `run_ci_eval` (full conductor) should be run in an env with API
> keys to confirm end-to-end — gated by the known OpenAI agent-path structured-output limitation
> (prefer Anthropic). The spreader itself runs live and reproduces the figures below.

## Side by side

| Dimension | Curated (loan package) | Our pipeline | Match |
|---|---|---|---|
| Decision | **Approve in concept** ($20M ABL), subject to conditions | `approved: true`, $20M | ✅ |
| Facility | $20.0M senior secured ABL revolver | loan_type ABL, $20M | ✅ |
| A/R advance rate | 85.0% | 0.85 | ✅ |
| Inventory advance rate | 50.0% | 0.50 | ✅ |
| Net sales FY2025 | $1,868.5M (10-K) | $1,868.494M | ✅ exact |
| Net income FY2025 | $165.4M | $165.387M | ✅ exact |
| Leverage | low (TLA $73.8M out) | debt/EBITDA 0.49 | ✅ consistent |
| Borrowing base (net avail) | **$226.7M** — 10% A/R inelig, 15% inv inelig, $5M reserve | **$265.5M** — no haircuts/reserves | ⚠️ delta ~$39M |
| Existing-lien / intercreditor | **Prominent condition** — existing $300M revolver + $84.4M TLA → amend / refi / intercreditor | not surfaced in expected covenants | ⚠️ gap |
| Covenants | term sheet (Appendix B) | FCCR ≥ 1.00x, min avail $2.5M/10%, inv turns | partial overlap |

## Findings

**Strong agreement** on the things that decide the deal: approve $20M ABL, the 85%/50% advance
rates, the underlying financials (our spreader reproduces the curated 10-K numbers exactly), and
low leverage (0.49x ≪ the 3.5x `CI_CORE_LEVERAGE_POLICY` ceiling → no approval gate). Both anchor
on the real SEC 10-K.

**Two real deltas:**

1. **Borrowing-base conservatism.** The curated package applies ineligible haircuts (10% A/R,
   15% inventory) and a $5M reserve → net availability $226.7M. Our borrowing-base calc uses full
   book A/R and inventory as "eligible" (no haircuts/reserves) → $265.5M. The *decision* is
   unaffected (both ≫ the $20M request), but our availability is overstated ~$39M / less
   conservative than an underwriter would book.

2. **Existing-lien / intercreditor condition.** The curated package's dominant structural caveat
   is that YETI already discloses a $300M revolver + $84.4M term loan, so a new first lien needs an
   amendment / refinance / intercreditor structure. Our expected outcome doesn't surface this as a
   condition. (The conductor *has* an `intercreditor_required` path in `_build_case_context`; check
   whether it's triggered for YETI given the existing-facility disclosure.)

## Follow-ups (for when you're back)

- Add ineligible-haircut + reserve logic to the borrowing-base tool to match underwriter
  conservatism (and cite the loan-package assumptions as the basis).
- Wire existing-debt / lien detection (`CI_CORE_LIEN_POLICY` + intercreditor) so the conductor
  raises the amendment/intercreditor condition for borrowers with a disclosed senior facility.
- Run a fresh live `scripts/run_ci_eval.py` (or the demo) for `ci_yeti_abl` in the full env to
  confirm the conductor reproduces this end-to-end; record the live recommendation + conditions
  here. Mind the OpenAI agent-path structured-output limitation (tracked); Anthropic enforces the
  schema and is the safer provider for the full loop.
