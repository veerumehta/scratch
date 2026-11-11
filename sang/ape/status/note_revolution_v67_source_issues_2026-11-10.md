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

## Added 2026-11-10: items found by the import, for the job-set owner

The set is not edited here. "Where" says which artifact the fix belongs in: the job set (CODEC's `jtbds.json`) or the ontology (the catalog's source).

### Outcome sections that state no criteria: 42 FHA overlays (job set)

The overlay's outcome section is one prose line routing the two FHA Streamline cases (NCQ, CQ) to a status; the importer cannot make criteria from it, so these 42 overlay rules keep the
generic default outcomes and carry `outcomes_unparsed` (the mapping text stays in the overlay's steps). Shapes (counts from the text):
- 19 say only "per base JTBD" or "same" (nothing changes from the base job). Example INS-HO6.FHA: `NCQ Streamline -> Pass/Conditional/Fail per base JTBD. CQ Streamline -> same.`
- 17 mix N/A with "per base". Example APR-VCO.FHA: `NCQ Streamline -> N/A (suppress finding entirely). CQ Streamline with no appraisal ordered -> N/A. CQ Streamline with appraisal in file -> Pass/Conditional/Fail per standard base JTBD.`
- 5 say N/A only. Example TTL-AC.FHA: `NCQ Streamline -> N/A. CQ Streamline -> N/A. No purchase contract or seller exists.`
- 1 other.
Fix in the job set: write these the way the 18 `### Outcome Remap` overlays already do (a bullet per status, with the N/A condition stated), or for the 19 say the overlay changes no outcome.
Ids (each `.FHA`): APR-VCO, APR-VMX, APR-14U, APR-IPT, APR-FRV, APR-CLT, APR-IMH, APR-MFH, APR-VCD, APR-VLS, APR-VMD, APR-FLP, APR-SEP, APR-TRM, APR-WTR, LPE-PSRR, LPE-CMP, INS-REQ, INS-HO6, INS-FDC,
INS-PROJ, INS-LOS, TTL-AUS, TTL-CPT, TTL-AC, TTL-ELG, TTL-COV, TTL-AOL, COM-PA, COM-EW, COM-EI, COM-PR, VAL-ADR, VAL-PCL, AST-FCDP, LIA-PMT, LIA-EXC, LIA-BAS, TAX-CAL, TAX-BASE, CRD-EXT, BOR-NE.

### Metrics whose value does not fit the boolean catalog field they are keyed to (Revolution 7, Pulte 6)

A metric carries no declared value type; the value kind is in its `indicator_context`. Pulte has the same six minus COM-DEC. Suggested field per metric:

| Job, metric | Keyed to (boolean) | Value in the context | Suggested field | Where |
|---|---|---|---|---|
| COM-DEC, DEC_REC_LM1 (Revolution only) | `Borrower.has_outstanding_judgments` | 'Reconciled' / 'Open Items' over all URLA Section 5 declarations | The entity `Borrower`, as Pulte's COM_DEC_LM1 does, or a new string field `declarations_status` | Job set (re-key); the new field would be the ontology |
| IDN-DPV, IDN_DPV_LM4, LM5, LM6 | `Borrower[...].power_of_attorney_used` | 'Not used' / 'Present' / 'Missing' (three states) | A new enum field `power_of_attorney_status` (not_used, present, missing) | Ontology (new field), then the job set (re-key) |
| INS-HO, INS_HO_LM7 | `LoanCore.is_escrow_waived` | 'Yes' when false, 'No' when true (inverted) | Keep the boolean; declare the metric value as boolean with the inversion in the context (or a derived `insurance_escrowed`) | Job set; the derived field would be the ontology |
| TAX-CAL, TAX_CAL_LM3 | `LoanCore.is_escrow_waived` | 'Yes' / 'No' (inverted), indicator 'Required' or 'Waived' | As INS-HO | Job set |
| INS-FZD, INS_FZD_LM1 | `FloodDetermination.is_in_sfha` | 'In Flood Zone (SFHA)' / 'Not in Flood Zone' | Keep the boolean; the strings are labels for true and false; declare the metric value as boolean (or a `flood_zone_status` string field) | Job set; the string field would be the ontology |

Underneath all of it: each metric should declare its value type (boolean, an enum with its values, a number), so the catalog field it is keyed to can be checked against it. The importer copies the metrics as written and does not choose or retype a key.

