# The disagreement verifier on loan-2 V5 (sonnet-runtime, 2026-10-22)

V5 (our jobs and code, `both`, hybrid answer by the jobs) on the loan-2 case record with `verify_disagreements` on, through local
Plato at de008490, approved by the user in session. Counts only; summary in
`docs/status/Acra/Acra Lending/e2e/loan-2/verifier_run.json`.

| | Standard | Platinum Select | Both |
|---|---|---|---|
| requirement pairs (job and code) | 43 | 56 | 99 |
| code and job disagree | 11 | 11 | 22 |
| verifier backs the code | 6 | 4 | 10 |
| verifier backs the job | 3 | 4 | 7 |
| verifier undecided (left open) | 2 | 3 | 5 |

- 17 of the 22 disagreements got a side (77%); the verifier leaned to the code slightly more than to the job (10 to 7).
- The whole V5 assessment, jobs and verifier, cost 0.022 USD over 253 model calls and took about 50 minutes; the verifier's own
  22 calls are a small part of it (the jobs are the rest). Well under the 1 to 2 USD the user approved.
- The verifier saw the stated facts, not document pages (`assess` has the facts only), so "backs the code" means the facts
  settle it the code's way. Without a gold answer this says which engine the verifier agrees with, not which is right.
- Next: ask a person to rule on a sample of the 17 and the 5 to see whether the verifier's ruling is right.
