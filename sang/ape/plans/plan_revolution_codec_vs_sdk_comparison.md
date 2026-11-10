# plan_revolution_codec_vs_sdk_comparison

Author: Virendra Mehta · 2026-11-09 · Status: not started; decisions below needed before R4

## Status and modifications

How to use this section: the plan author may read and update it; implementers append one dated line per slice (what landed, the commit, anything the plan got wrong). Newest line last.

- 2026-11-09 drafted. Revolution is the first comparison target (it was the held-out step of `plan_pulte_home_mortgage_sdk_comparison.md`). Code-level comparison first, then verdicts on loans. Loan data and the answer key stay on the Revolution VM.

## Goal

Put Codec's generated evaluators and the SDK's Policy to Code output side by side on the same Revolution JTBDs, first as code (no loans, no real data), then as verdicts on the same loans scored against the same key. The result is the first measured number for the SDK's Policy to Code and ACER path (measurement plan M2) and a job-by-job list of where the two disagree and why.

## Before starting

Verify in this order: the latest CHANGELOG entries, this plan, `plan_pulte_home_mortgage_sdk_comparison.md` (design, scorer and controls this plan reuses), `status/note_pulte_revolution_jtbd_comparison_2026-11-09.md` (Revolution's JTBD schema and its overlap with Pulte), then the source. Read-only on kernel-lab and on the VM unless a slice says otherwise.

## What exists

- **Codec on Revolution** (kernel-lab `codec-suite/workflows/customers/revolution/`): JTBD set v6.7, 183 jobs in 12 sections, 155 final and 28 provisional checks, run with `tools.run_checks --customer revolution`. Tuning was still merging on 2026-11-08 and 2026-11-09 (PR #338). Each job carries `mnemonic`, `section`, `section_type`, `skill`, `source`, `requirements` per investor (COMMON, FNMA, FHLMC, FHA, VA, USDA) and `loan_metrics`.
- **Codec's reader** extracts each loan once into a versioned ontology snapshot from converted markdown (`loans/<loan>/*.md`). Its evaluators read that snapshot.
- **Pulte precedent in jaci**: `config/packs/pulte_home_mortgage_policy` is a conversion of Codec's Pulte JTBDs into SDK `procedure` rules (rule id = mnemonic) plus per-investor overlays (`<mnemonic>.<PROGRAM>`, `overlays: <mnemonic>`). 107 of Pulte's 115 mnemonics are also in Revolution.
- **SDK side** (2.7.0): `jtbds_to_code` writes one Python job per JTBD against `rules_lib`; `case_to_verdicts` runs rules with code as code and ACER for the rest; `run_health` fails a run that loses jobs; the ledger has a "left to reviewer" column.

## Rules for a fair comparison

- **No contamination.** The SDK code writer never sees Codec's evaluators. Its inputs are the JTBD text, the pack's field catalog and the pack's own worked examples.
- **Same inputs.** Both arms read the same field values for the same loan. Hold reading constant first (both read Codec's snapshot through the R2 mapping); our own reader is a later, separate arm.
- **Same key, same scorer, same judge.** Use the Revolution scorer and key the kernel-lab side already uses. Do not build a new scorer.
- **Pinned builds.** Record the Codec build hash and the japes commit for every run. No hand fixes to generated code; regenerate instead.
- **Spend.** Every model-backed step needs the user's typed approval with a figure, in the session that runs it.

## Slices

### R1. Revolution JTBDs as an SDK pack (off the VM)
- Convert `customers/revolution/jtbds.json` v6.7 into a pack the way the jaci Pulte pack was built: 183 base `procedure` rules (rule id = mnemonic) and per-investor overlays, including USDA. Reuse the Pulte conversion script if one exists in jaci; otherwise write it once so Pulte and Revolution go through the same converter.
- Place it as `jaci/config/packs/revolution_home_mortgage_policy`. Do not wait on `plan_JAPES_PACK_ASSEMBLY_BASE_AND_OVERLAY.md`; note the 107 shared jobs in the pack README so the base and overlay split can come later.
- Intent: the SDK runs the same 183 jobs Codec runs, with the same ids.
- Acceptance: the pack loads and lints; 183 base rules, overlay counts per investor reported; ids equal the v6.7 mnemonics.

### R2. Field mapping between Codec's snapshot and the pack catalog
- Write the pack's field catalog (`jtbd_template.yaml` reads) from the fields Codec's evaluators read, and a mapping table from Codec snapshot paths to catalog fields, with a coverage report: mapped, unmapped, and jobs whose reads are fully mapped.
- Intent: both arms read the same values, so differences come from the code, not the data shape.
- Acceptance: coverage report committed; every job lists its mapped reads and any gaps.

### R3. Generate SDK code for all 183 jobs (off the VM; spend)
- Run `jtbds_to_code` on the R1 pack with the R2 catalog. Record model, prompt versions, cost, and the run-health result.
- Acceptance: one code proposal or a stated reason per job; the coverage ledger shows jobs with code, checks decided and checks left to reviewer.

### R4. Code-level comparison (off the VM, no real data)
- Per job, side by side: has code (Codec, SDK); fields read; thresholds and constants found in each body versus the numbers in the requirement text; checks decided versus left to reviewer.
- Differential test: from each job's requirement thresholds, generate boundary contexts in the R2 field names (each limit, one step either side, a missing value), run both evaluators on them, and list every disagreement. Codec's evaluators run through the R2 mapping in reverse.
- Intent: a ranked list of real logic differences before any loan is touched.
- Acceptance: a table per job (agree, disagree with the failing context, one side has no code), a summary count, and a short audit of the top disagreements against the requirement text.

### R5. Verdicts on Revolution loans (on the VM; spend)
- Arms: Codec (its pinned run); SDK code first (`case_to_verdicts`: code as code, ACER for what code leaves undecided); optional SDK ACER only. All arms read Codec's snapshot through R2.
- Score with the Revolution scorer and key: recall against the SME end-state conditions, strict precision, duplicate rate, calculation rows separately, cost and time per loan.
- Start with one loan end to end, check the manifest and cost, then the agreed set.
- Acceptance: a stored run per arm with build hashes and a comparison table.

### R6. Note and follow-ups
- One-page note in `docs/status/`: the numbers, the sample, what was not measured, and the top disagreements with their cause (requirement text, mapping, code writer, ACER).
- Feed fixes back as SDK items (code writer, catalog, ACER) rather than hand edits to generated code.
- Update the measurement plan's M2 line and the deck's Policy to Code status once the number exists.

## Order

R1 and R2 together, then R3, then R4 (all off the VM). R5 after the decisions below. R6 last.

## Decisions for the user

1. **How the SDK arm runs on the VM.** Install japes on the Revolution VM and run R5 there, or have the kernel-lab side run our arm with our pack and code. This decides R5.
2. **Key and loans.** Which Revolution loans and which SME key file (and its checksum) the scorer uses, and whether a held-out set is frozen before R5.
3. **Codec build to pin.** Tuning is still merging; name the build hash to compare against.
4. **Spend.** A typed figure for R3 (code generation, 183 jobs) and for each R5 arm, given in the session that runs it.
5. **Kernel-lab contact.** Who on the kernel-lab side owns the Revolution scorer and key, so we reuse them rather than rebuild.

## Risks

- Per-job rules over-generate on both sides; report strict precision and duplicates, do not hide them.
- The R2 mapping can lose fields; the coverage report separates mapping gaps from method gaps.
- FHA text differs most between lenders; expect most disagreements there.
- A development-loan number is a development score; do not present it as held-out.

## Not verified

Whether the Revolution JTBD file and Codec's evaluator code are available off the VM (the JTBD file was read in kernel-lab on 2026-11-09); whether a jaci conversion script exists for Pulte; the Revolution scorer's name and key format; run time per loan.

- 2026-11-09 (opus-xrepo, user approved R1 and R2, no spend) changes before work starts: R2's catalog is built from the snapshot schema and the JTBD text, not from the fields Codec's evaluators read (that would leak their field choices; any such use is listed as a declared leak). R1 goes through the SDK importer (`pack/jtbd_import.py`); a converter, if needed, lives in the SDK so Pulte, Revolution and Knowledge Studio share it. Suggested owners: R1 and R2 `sonnet-packs` (placement by `sonnet-jaci`), R3 and R4 `sonnet-runtime`, R6 `opus-xrepo`. R4 single-job tests need upstream findings supplied for tiered jobs, and Codec's 28 provisional checks are scored apart from the 155 final. User direction: generated code should grow into a reusable, domain-aware library (mortgage income, DTI, LTV, reserves) namespaced cleanly like the financial tools and ci_spread pipelines, not per-customer copies; R2 flags which fields and helpers are domain-general and proposes the namespace.
- 2026-11-09 (sonnet-packs) R1 and R2 done off the VM, no spend, no model call, no commit (the SDK importer needed no change). R1: `import_jtbdset` takes v6.7 directly, no converter; 183 base rules with ids equal to the mnemonics and 401 overlay rules (FNMA 9, FHLMC 91, FHA 154, VA 111, USDA 36); the pack loads and lints with the same three finding kinds as the Pulte pack; importing Pulte 6.2.3 through the same path reproduces jaci's Pulte pack exactly (292 of 292 conditions). R2: the catalog is the whole mortgage ontology v2 (policy-workbench copy), no evaluator read; 48 jobs fully mapped, 135 jobs name no read in the set (a method gap, decision needed: model pass, declared evaluator-read leak, or leave to the code writer). The plan was wrong on: the converter question (none needed), and "the 68 differing steps" in the assembly plan (an artifact of comparing split text). Pack in the scratch folder named in `status/note_revolution_pack_r1_r2_2026-11-09.md` for `sonnet-jaci` to place.

- 2026-11-10 decision (user): the 135 jobs whose definitions name no read are left to the code writer (option 3: no model pass, no declared leak). R4 reports how many of them the writer handles without guidance.
