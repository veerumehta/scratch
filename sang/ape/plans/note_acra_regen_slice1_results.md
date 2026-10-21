# Acra regeneration, slice 1 job-writer quality: results (sonnet-runtime, 2026-10-21)

Two arms on the same config (4a, 4b; Plato at 17cfe8ff, before the later fixes), merged jobs only, files read with
`scripts/local/acra_regen_measure.py`. Baseline is 3b (and regen 1/2 where noted). Outputs: `scripts/local/coverage/regen_4a|4b`.
Spend: well under the approved $2 (cost ledger rebuilt, no loan files used).

| Measure | Std 3b | Std 4a | Std 4b | Plat 3b | Plat 4a | Plat 4b |
|---|---|---|---|---|---|---|
| Jobs | 121 | 112 | 100 | 110 | 79 | 76 |
| Citations spanning sections | 18 | 0 | 0 | 46 | 0 | 0 |
| Most jobs from one citation | 16 | 13 | 11 | 32 | 10 | 10 |
| Near-duplicate pairs | 13 | 6 | 10 | 22 | 7 | 10 |
| Reads but none computable | 56 | 61 | 34 | 19 | 38 | 27 |

Coded share (code + code_and_procedure over assessed jobs, harness figure): 4a 52.9%, 4b 54.7% (98/179); 3b 50%, regen2 55.6%.

## Reading (noise rule: a move counts only if both arms sit outside the baseline range and the arm gap is smaller than the distance)

- **Structural, deterministic (W1): moved.** Citations spanning sections 0 in every arm (was 18/46); jobs per policy down.
- **Most jobs from one citation: Platinum moved** (32 to 10 in both arms; the target of under 8 is missed). Standard 13 and 11 vs 16: gap 2, distance 3 and 5, not a clear move.
- **Near-duplicate pairs: Platinum moved** (22 to 7 and 10). **Standard not claimed**: arms 6 and 10, 3b 13, the 4-pair arm gap exceeds the 3-pair distance of the nearer arm.
- **Coded share: no move** (both arms inside 50 to 55.6%).
- **Reads but none computable: noisy, no claim** (Standard 61 vs 34 between arms; Platinum doubled in 4a, 27 to 38 between arms vs 19 baseline).
- Clauses (4a, fixed rule): 79 units, 79 checked, 0 cited-only. 4b clause counts not recomputed.
- Harness flaw: the Standard jtbd extraction re-ran whole after one failed part, leaving duplicate pending proposals in 4a; merged-jobs counts are unaffected, "jobs in coverage" figures are inflated.
- Both arms ran before the later cite-keyed fixes (citations change); a third arm on current code is optional.
