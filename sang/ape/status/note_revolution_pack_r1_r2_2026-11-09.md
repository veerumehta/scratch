# Revolution pack and field catalog (slices R1 and R2), 2026-11-09

Off the VM, no spend, no model call, no loan file, snapshot, evaluator or answer key opened. Nothing in jaci, kernel-lab or the SDK was edited,
and nothing was committed: the SDK's existing importer did the work, so no SDK change was needed. The pack is in a scratch folder for
`sonnet-jaci` to place (path below).

## What was built

`/private/tmp/claude-506/-Users-sangit-src-japes/be664afe-a0b9-40b7-9e47-7e92d6062643/scratchpad/out/revolution_home_mortgage_policy/`
(7.7 MB; the folder lives in this session's scratch directory, so copy it before the session ends). Scripts that produced it, beside it:
`build_pack.py` (R1), `r2.py` and `res.py` (R2).

R1 and R2 in one folder: 17 policy files, `pack_manifest.yaml` (pack id `revolution-home-mortgage-policy`, 0.1.0, draft, `catalog:` set),
`jtbd_template.yaml`, `catalog.schema.json`, `coverage/field_coverage.yaml`, `coverage/shared_with_pulte_jobs.yaml`, `README.md`.

## R1: Revolution v6.7 imports directly

- **No converter was needed.** `import_jtbdset` (`jazzx_sdk/pipelines/policy/jtbdset.py`) takes the v6.7 file as it is. Pulte and Revolution go through the
  same call and the same folder-writing step (`build_pack.py`, the logic of jaci's `scripts/import_jtbd_catalog.py`, with the file names written the same way).
  Nothing in the SDK is named for a lender; the pack carries the customer name only in its id and README.
- **Counts:** 183 base rules in 12 section policies, ids equal to the 183 v6.7 mnemonics (checked, no duplicates). Overlay rules per investor:

  | Investor | Overlay rules | Pulte (for comparison) |
  |---|---|---|
  | FNMA | 9 | 9 |
  | FHLMC | 91 | 53 |
  | FHA | 154 | 58 |
  | VA | 111 | 57 |
  | USDA | 36 | none |
  | Total | 401 | 177 |

  `NO_CHANGE` blocks import nothing; a `NOT_APPLICABLE` block imports a suppression, not a rule (5 here: 3 in FHLMC, 2 in FHA), so the counts above are rules only.
- **Loads and lints:** `Pack.from_manifest` loads 17 policies; `lint_pack` reports 685 findings of three kinds: 584 `rule_without_citation`, 57 `filter_value_unchecked`, 44
  `unreachable_filter_field`. The Pulte pack gives the same three kinds (plus 2 `unreachable_input`) at 359. There is no unresolved read and no missing ontology.
- **Rule ids are mnemonics** and the 107 shared jobs are listed in `coverage/shared_with_pulte_jobs.yaml` and named in the README.

### A correction to the pack-assembly plan

`plan_JAPES_PACK_ASSEMBLY_BASE_AND_OVERLAY.md` lists as a risk that "68 of 115 steps in jaci's Pulte pack differ from CODEC's 6.2.3 text for reasons nobody has diagnosed".
Settled: importing Pulte 6.2.3 through `import_jtbdset` reproduces jaci's Pulte pack exactly, **292 of 292 rule conditions equal** (kind, purpose, steps, checks, outcomes; 115 base and
177 overlay rules, no other key differs). The earlier 47-of-115 figure compared the importer's `steps` list with the whole COMMON text; the importer splits that text into purpose, steps,
checks and outcomes, so they were never the same string. The Pulte pack is a lossless SDK import of 6.2.3 (not of 6.2.0), which also makes the S5 equivalence test simpler.

## R2: the catalog and field coverage

Built only from the ontology and the JTBD set. **No evaluator was read**; evaluator reads used: none (nothing to list as a declared leak).

- **Catalog:** the whole mortgage ontology v2 as the policy-workbench copy carries it (the same source and sha256 as the Pulte catalog), unedited, 40 entities, with `x-provenance`.
  Five copies of "mortgage ontology v2" exist with different hashes (policy-workbench, mortgage-app-ontology, mortgage-app, macer, a juno fixture). I tested four of them and juno's v4 fixture: the macer copy lacks 62 of
  Revolution's 177 declared keys, the others resolve all 177 (juno's v2 copy was not tested). It is not confirmed which one CODEC's snapshot follows. It is the whole ontology, not only the entities the set names, so the code
  writer is not told which entities matter. (The Pulte pack carries only the 17 entities its set names.) The SDK's `adopt` was tried and left: it marks fields as adopted and the lint then reports
  608 unused adopted fields; copying the definitions unedited, as the Pulte catalog does, gives none.
- **Reads:** every read is `Entity.field`; the mapping to the snapshot is assumed identical to the ontology names. A snapshot is loan data and was not opened, so the mapping table is
  an identity mapping stated as an assumption, to be confirmed by a list of snapshot paths that carries no values.

### Coverage report (`coverage/field_coverage.yaml`)

| | Jobs |
|---|---|
| Fully mapped (every named read resolves in the catalog) | 48 |
| Partly mapped | 0 |
| No read named in the job definition | 135 |
| Total | 183 |

- 177 distinct declared `loan_metrics` keys, all resolving (0 unmapped); 1 further key found by text (`Entity.field` tokens), also resolving. Pulte, for comparison: 173 keys, 1 unresolved
  (`LoanCore.total_undisclosed_monthly_payment_usd`), 69 of 115 jobs with no read named.
- **The 135 jobs with no named read are the gap.** The set declares `loan_metrics` for only 48 jobs and the text names a field in only a handful (3 of the 135 mention a snake_case ontology field
  name, e.g. `loan_type`, `year_built`). They are mostly compliance, appraisal, eligibility, title and credit jobs (Compliance and Closing 36, Appraisal Review 30, Loan Program Eligibility 14, Title 11,
  Assets 11, Credit 11, Insurance 10, Income 6, Liabilities 3, Identification 2, Property Tax 1). The acceptance line "every job lists its mapped reads" is met only as "none named" for them. Closing it needs either a model pass over
  the text to propose reads (spend, and a method gap rather than a mapping gap) or the evaluators' reads, which would be a declared leak: decision for opus-xrepo and the user.
- **Method vs mapping:** the 48 jobs are a mapping question (identity assumed); the 135 are a method question.

## Domain-general against lender-specific, and a proposed namespace (proposal only, nothing built)

From the declared reads (evaluators not read): Pulte and Revolution share **152 of their 173 and 177 keys**.
- **General (read by both lenders):** income by type (`IncomeSource` base, bonus, commission, overtime, rental, retirement, SSA, self-employment: 25 keys),
  `Borrower` and `CreditReport` totals, `Liability` payments (revolving, installment, excluded from DTI), `LoanCore` LTV, CLTV, HCLTV, assets and down payment, `RatioSet` front and back end DTI,
  reserves months, residual income, housing expense, `EmploymentRecord`, `SubjectProperty`, `TitleInformation`, `HazardInsurance`.
- **Specific to one set, but by program, not by lender policy:** Revolution only: `CondoProject` (18 keys; the Condo Project Review section), USDA guarantee fee, `LoanCore.investor_name`
  (agency direct), trust name. Pulte only: military income types (6 of them), pension, earnest-money deposit, undisclosed liabilities. These follow what each lender originates, so they belong
  in a condo module, a government or military module, and so on, not in either lender's pack.
- **Proposed namespace (a rules_lib domain module, not per customer):** a mortgage module inside the helper library `jazzx_sdk/rules/` (the executor imports `rules_lib`), exposed as
  `rules_lib.mortgage` with submodules mirroring how the finance code is split (`jazzx_sdk/finance/`): `income` (monthly amount by type, the averaging and trend tests, annualizing), `ratios` (DTI front and
  back, LTV, CLTV, HCLTV), `reserves` (months of PITIA, haircut by asset type, usable balance), `liabilities` (what counts, excluded-from-DTI), and later `government` (FHA, VA, USDA fixed
  numbers and tables) and `condo`. Helpers take plain values and return plain values (like the current `ratio`, `percent`, `total`, `lowest`), carry a manifest entry per version
  as the existing `manifests/` do, and are added only when two jobs need the same calculation. The field catalog stays one shared ontology; a lender never owns a helper.
- Which helpers: not decided here. The code writer's output on the 48 mapped jobs (R3) is the evidence; promote a helper when two lenders' jobs use it.

## Open for opus-xrepo and the user

1. How to give the 135 jobs a read list (model pass, evaluator reads as a declared leak, or leave to the code writer).
2. Which ontology copy CODEC's snapshot follows; ask the kernel-lab side for a path list with no values.
3. Placement: `sonnet-jaci` copies the pack folder to `config/packs/revolution_home_mortgage_policy` (and `catalog.schema.json` as is); the scratch folder is not durable.
