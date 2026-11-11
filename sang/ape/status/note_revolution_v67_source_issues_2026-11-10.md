# Revolution JTBD V6.7: content issues for the job-set owner (2026-11-10)

For whoever owns the set. Nothing in the source was edited. Origin: jaci's pre-push review of the imported pack
(`jaci/scripts/local/.reviews/20261110T232139Z-23129.md`). I re-read the job text for the first three;
the last two are the review's, not re-checked by me. Job ids are v6.7 mnemonics.

| Job | Issue | What I confirmed in the text |
|---|---|---|
| APR-IPT | The check "Property must not be a Co-Op or Condotel" fails every co-op, while APR-META lists a co-op unit as acceptable and APR-VCO passes a co-op with a complete Form 2090 (review). | The check and its Step 5 are in COMMON as quoted. |
| APR-AVA | The job is titled "VA IRRRL - (Info Only)" and checks the appraisal against VA IRRRL requirements, but states no applicability condition and its not-applicable outcome says there is no case. A conventional or FHA loan is evaluated against VA IRRRL (review). | The title, the purpose and the VA overlay (Clear Capital AVM, else the original principal balance) are in the text; no loan-type gate is. |
| AST-RSLE | The retirement section tells the model to apply no haircut, while the FHA overlay counts retirement accounts at 60% of the vested amount (review). | The FHA overlay's "FHA retirement-account discount" paragraph (60%, "FHA-specific rules take precedence") is in the text. |
| APR-WTR | Step 4.2 and the checks call a property that needs a water purification system ineligible (Fail), while the Conditional outcome lists a required purification system (review). | Not re-checked; the COMMON text I searched has no "4.2" marker and does say a purification reliance is Conditional on existing construction. The review's step numbering may come from the guide layout. |
| Count metrics | Count-type metrics default to 0 when the input is missing, which reads as a perfect result (review). | Not re-checked. |

The same defect list names the Pulte set (`water-purification-status-split` is an open finding on the Pulte pack too).
