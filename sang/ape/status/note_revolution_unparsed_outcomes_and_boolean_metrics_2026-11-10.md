# Revolution pack: unparsed outcomes by shape, and metrics on boolean fields (2026-11-10)

Read-only. No model call, no spend, no loan data, nothing in jaci or kernel-lab edited; the parser is not extended. Source: Revolution v6.7 and
Pulte 6.2.3 job text and `loan_metrics` (the CODEC job sets), the policy-workbench ontology copy, and the SDK importer at `65c1b524`/`84cf6486`.

## 1. The 73 rules flagged `outcomes_unparsed`

Counts: 1 base rule (COM-HOEPA) and 72 overlays (FHA 64, FHLMC 4, VA 4). They fall into three shapes. In all three the source text is
still in the rule (the overlay's purpose or steps carry the section); what is not recovered is the structured criterion per status, which stays
at the default. (Per sonnet-runtime, the reasoner does not see `source_text`; the text it does see is the rule's purpose, steps and checks.)

| Shape | Rules | Example and text shape | A parser extension? |
|---|---|---|---|
| **A. `### Outcome Remap`**: one bullet per status, `- **Pass** -- ...`, `- **Conditional** -- ...`, `- **Fail** -- ...`, `- **N/A** -- ...` | 18 (all FHA) | LPE-COO.FHA: `- **Pass** -- At least one new-loan borrower was on the prior FHA-insured Note; ...` / `- **N/A** -- Not an FHA Streamline (Base Conventional COO rule governs).` | **Yes, safe.** The statuses and criteria are explicit and the importer already reads this bullet form; it fails only because the nested-heading match accepts the exact title `Outcomes`. Accepting `Outcome Remap` as a title is a one-line regex change. Ids: LPE-COO, INS-FCO, INS-FLD, INS-HO, TTL-INS, COM-FHA-CA, COM-NCO, COM-NJM, COM-CTC, COM-FRD, COM-HPML, IDN-NUS, IDN-SSA, IDN-SSV, IDN-DPV, LIA-DTI, CRD-MERGED, CRD-UDN (each `.FHA`). |
| **B. `### Outcome Mapping`**: one prose line routing the two FHA Streamline cases to a status | 42 (all FHA) | APR-VCO.FHA: `NCQ Streamline → N/A (suppress finding entirely). CQ Streamline with no appraisal ordered → N/A. CQ Streamline with appraisal in file → Pass/Conditional/Fail per standard base JTBD.` Sub-shapes: 19 say only "per base JTBD" or "same" (INS-HO6.FHA: `NCQ Streamline → Pass/Conditional/Fail per base JTBD. CQ Streamline → same.`), 17 mix N/A with "per base", 5 say N/A only (TTL-AC.FHA: `NCQ Streamline → N/A. CQ Streamline → N/A. No purchase contract or seller exists.`), 1 other. | **No.** It is a routing of scenarios to statuses, not a criterion per status. Turning it into criteria would invent text. Recommend the job-set owner rewrites it as the other overlays do (a bullet per status, or a stated N/A condition), or that the overlay's outcomes are declared as "the base job's" for the 19 where nothing changes. Until then the flag is the right signal. Ids: the 42 listed below. |
| **C. `### Outcomes` that states only some statuses** | 13 (COM-HOEPA; LIA-PITIA, CRD-DERG, CRD-DUF, CRD-FB each in FHLMC, FHA and VA) | LIA-PITIA.FHLMC: `- **Pass**: PITIA correct, LPA aligned.` / `- **Conditional**: HOA statement pending.` / `- **Fail**: MI premium omitted; ...` and no N/A line. COM-HOEPA states Pass and Fail only. | **No parser change; the flag is wrong here.** These were parsed (Pass, Conditional, Fail are the source's). The flag fires because a status the source does not state keeps its default. Recommend narrowing the flag: `outcomes_unparsed` only when the section had no readable status, and a separate informational list (for example `outcomes_unstated`) for statuses the section leaves out. That moves these 13 out of the flagged set. |

Effect if both recommendations are taken: Shape A is read (18 fewer), Shape C is reclassified (13 fewer), leaving the 42 in Shape B for the owner.
Shape B ids: APR-VCO, APR-VMX, APR-14U, APR-IPT, APR-FRV, APR-CLT, APR-IMH, APR-MFH, APR-VCD, APR-VLS, APR-VMD, APR-FLP, APR-SEP, APR-TRM, APR-WTR, LPE-PSRR,
LPE-CMP, INS-REQ, INS-HO6, INS-FDC, INS-PROJ, INS-LOS, TTL-AUS, TTL-CPT, TTL-AC, TTL-ELG, TTL-COV, TTL-AOL, COM-PA, COM-EW, COM-EI, COM-PR, VAL-ADR, VAL-PCL,
AST-FCDP, LIA-PMT, LIA-EXC, LIA-BAS, TAX-CAL, TAX-BASE, CRD-EXT, BOR-NE (each `.FHA`). For these the overlay's four outcomes are the generic defaults; the mapping text sits in the overlay's purpose or steps.
Pulte has one flagged rule (APR-VCD, base) that I did not group.

## 2. Metrics keyed to a boolean catalog field

**Where the type comes from.** A `loan_metrics` entry carries `metric_key`, `label`, `indicator_context`, `description_template`, `metric_mnemonic` and sometimes
`calculation_context`; it has **no declared value type**. The value kind is only what `indicator_context` says (quoted words such as 'Reconciled' or 'Yes'). The field type
is the policy-workbench ontology's (`type: [boolean, null]`). So "string-like value on a boolean field" is read from the context text, not from a declared type.

**Who chose the key.** The job set did: the importer copies `loan_metrics` as written and sets the rule's `reads` to the metric keys (`jtbdset.py`, `import_jtbdset`); it
neither picks nor retypes a key. I found no pack-assignment step in my path that maps metrics to fields. The catalog typing is the ontology's. So the choice is the job-set owner's, against an ontology they do not control.

Metrics whose key resolves to a boolean field (Revolution 7, Pulte 6; Pulte's list is Revolution's without COM-DEC):

| Job | Metric (mnemonic) | Key (boolean field) | Value the context defines | What the catalog field should be |
|---|---|---|---|---|
| COM-DEC | DEC_REC_LM1 | `Borrower.has_outstanding_judgments` | 'Reconciled' or 'Open Items' over all URLA Section 5 declarations (a composite) | Not that field. Pulte keys the same metric to the entity `Borrower` (COM_DEC_LM1, "composite over the Borrower declaration fields"); do the same, or add a string field such as `declarations_status` and key to it. Revolution anchored the composite on one of its component fields. |
| IDN-DPV | IDN_DPV_LM4, LM5, LM6 (Pulte the same) | `Borrower[...].power_of_attorney_used` | 'Not used', 'Present', 'Missing' (three states) | A boolean cannot hold three states. An enum string field (for example `power_of_attorney_status`: not_used, present, missing), keyed by the metric. |
| INS-HO | INS_HO_LM7 (Pulte the same) | `LoanCore.is_escrow_waived` | 'Yes' when `is_escrow_waived=false`, 'No' when true (inverted) | The boolean is right as the source; the metric is a derived label. Either key the metric to a derived string field (`insurance_escrowed`) or declare the metric value as a boolean with the inversion in the context. |
| TAX-CAL | TAX_CAL_LM3 (Pulte the same) | `LoanCore.is_escrow_waived` | 'Yes'/'No' (inverted), plus an indicator 'Required' or 'Waived' | Same as INS-HO. |
| INS-FZD | INS_FZD_LM1 (Pulte the same) | `FloodDetermination.is_in_sfha` | 'In Flood Zone (SFHA)' or 'Not in Flood Zone' | Boolean is the right field; the two strings are display labels for true/false. Keep the field boolean and declare the metric value as boolean with those labels in the context, or add a string `flood_zone_status`. |

Recommendation: the clean fix is a declared value type on each metric (boolean, enum with its values, number) in the job set, and a catalog field of that type for every metric; where a value is a composite or a label, key it to a derived field or to the entity, as Pulte already does for COM-DEC.
In the Revolution pack nothing resolves differently from the ontology: all 7 keys exist, so lint does not flag them; the mismatch shows only when a value is written.
Not examined: other mismatches (an enum or string value on a number or integer field), and whether CODEC's runtime writes the label or the boolean. I did not check the Plato metric writer; sonnet-runtime's note covers that boundary.
