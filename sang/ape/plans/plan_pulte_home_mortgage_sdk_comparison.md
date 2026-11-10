# Pulte home mortgage on the SDK: a comparison run beside CODEC and MACER

Author: Virendra Mehta

Written 2026-11-09 by opus-xrepo from a read-only survey of the kernel-lab checkout (`/Users/sangit/src/kernel-lab`, branch `dev`, tip 40e7cc2f of 2026-11-09), our CODEC lessons note (`note_codec_m1_lessons_for_policy_to_code.md`, which cites CODEC's Milestone 1 report of 2026-10-21) and the SDK at 2.7.0. Plan only: nothing run, no spend, no loan file opened. `[V]` checked in a file or git, `[U]` not verified.

## Status and modifications

How to use this section: the plan author may read and update it; implementers append one dated line per slice. Newest line last.

- 2026-11-09 drafted. Needs the user's decisions in "Decisions" before anything starts.
- 2026-11-09 how CODEC runs today (kernel-lab docs): `codec-core` is a CLI-first, filesystem-backed pipeline with no service or database (`codec extract`, `generate-parallel`, `reason`, `calibrator`, `gap-analyze`); its input is `loans/<loan>/*.md` (already-converted markdown) plus a ground-truth `GT.csv`, the JTBD file and `conditions.json`; model-backed commands need an OpenAI key; the Pulte benchmark runs on the Pulte VM per the Pulte layer README. `codec-suite` adds a UI and API shell deployed to Azure Container Apps. The repo tracks per-loan folders under `codec-suite/workflows/loans/` and calibration evidence; no document says whether any of it is anonymized (some folder names look synthetic, others look like real loan numbers), so that is a question for the kernel-lab owner, not something to assume.
- 2026-11-09 the Desktop plan `plan_revolution_codec_vs_sdk_comparison.md` makes Revolution the first comparison target and reuses this plan's design, scorer and controls; this plan stays the design reference and Pulte follows or runs beside it.
- 2026-11-09 correction: the line below under "What the SDK has for this" says the SDK side has no Pulte JTBDs. jaci already holds a Pulte home mortgage solution: blueprint `pulte-home-mortgage` (client pulte, guideline set fannie-mae-selling-guide, published to the pulte tenant only) and policy pack `pulte-home-mortgage-policy` 0.2.2 (draft) with 15 JTBD policy files by group and program (FNMA, FHLMC, FHA, VA), written from the June 2026 Selling Guide, plus an assistant pack. Whether it shares lineage with CODEC's 6.2.3 set is not known; an overlap analysis is with `sonnet-packs`. Slice 2 is therefore a comparison of the two sets, not an import from nothing. A second customer, Revolution (183 JTBDs in v6.7 in kernel-lab), is being worked by the CODEC side and is the natural held-out customer for this comparison.
- 2026-11-09 modification: because CODEC's reader starts from converted markdown, an SDK arm can read the same markdown with the SDK document agent, which holds the reading input constant without a snapshot adapter. Slice 3 becomes optional: the adapter is needed only to feed our checks CODEC's own extracted tables.

## Why this plan

The measurement plan's M2 (Policy to Code correctness) is blocked because Acra has no SME-cleared answer key. Pulte has one, and CODEC and MACER are already scored against it. So the quickest honest way to put a correctness number on the SDK's Policy to Code and ACER path is to run it on Pulte against the same key and the same scoring, and compare with CODEC and MACER on the same table. That also gives the executives a like-for-like comparison, not three separate claims.

## What is already running elsewhere

- **CODEC** (kernel-lab `codec-core`, `codec-suite`): a reader that extracts a loan once into a versioned ontology snapshot, plus 115 generated Python evaluators, one per JTBD, run in dependency tiers. Milestone 1 (2026-10-21), seven Pulte development loans: 155 of 172 SME end-state conditions (90.1%), MACER 132 (76.7%). Strict precision 10.8 to 15.6%, exact duplicates 8.6% (MACER 1.4%), 83 of 115 checks hand-fixed, calculations weakest (income 27 of 70), nothing held out [from our note; U against the report]. The kernel-lab README quotes an earlier baseline: 145 of 170 rows (MACER 136) on 2026-10-14 [V].
- **MACER**: the incumbent agentic verifier that re-checks each JTBD against the documents on every run.
- **Pulte layer in kernel-lab** (`codec-suite/workflows/customers/pulte/`) [V]: `sme_extract.py` (SME workbooks to `sme_conditions.json`, MACER's workbook conditions as a scoreable arm), `sme_match.py` (scores arms against the SME conditions with an LLM judge, and checks the judge against the SMEs' own verdict on MACER), `sme_label_audit.py`, `v2_baseline.py`, `run_manifest.py` (code, models, settings, stage times, priced calls per run), JTBD version 6.2.3. Its README says everything runs on the Pulte VM and the SME workbooks and every output are real loan data that stay there.
- **Revolution** (second customer, same engine, `customers/revolution/`) [V]: JTBD set v6.7 with 183 JTBDs, 155 final and 28 provisional checks, run with `tools.run_checks --customer revolution`; tuning rounds were still being merged on 2026-11-08 and 2026-11-09 (PR #338), and `run_checks` now writes MACER's run files with `--artifacts` (PR #337), so a MACER-format comparison already exists on their side.
- **codec-transformers-ann**: exploratory (a ModernBERT classifier; precision 0.18 on "Correct" when we looked), not an input.

## What the SDK has for this

- JTBD sets move into packs through `import_jtbdset` (`jazzx_sdk/pipelines/policy/jtbdset.py`); `plan_adopt_existing_jtbds.md` covers adopting an existing set [V that the importer exists].
- `jtbds_to_code` writes one Python job per JTBD; `case_to_verdicts` runs rules with code as code and lets ACER judge the rest against the evidence; ACER merges duplicate conditions, votes across replicas and carries only changed rules forward [V from the 2.7.0 tree and the deck notes].
- The SDK pack for Pulte today is only two sample packs (`pulte-home-mortgage-core`, `pulte-home-mortgage-macer`: persona, profile, a process declaration); it has no JTBDs, no code and no answer key [V].
- Known weak points on our side, from Acra: about half of the jobs get code; correctness unmeasured; ACER unmeasured against MACER [from the deck].

## The comparison design

Same inputs, same key, same judge, same scoring definitions, so the numbers line up.

| Arm | What runs | Source of its number |
|---|---|---|
| CODEC | Their evaluators on their reader snapshot | Their published run and `run_manifest.json`; rerun only if the pinned build is available |
| MACER | The incumbent | Their workbook conditions through `sme_extract` |
| SDK-1: ACER only | The Pulte JTBDs imported as a pack, every rule judged by ACER on the case record | New |
| SDK-2: code first | `jtbds_to_code` for every JTBD, then `case_to_verdicts` (code as code, ACER for what code leaves undecided) | New |
| SDK-3: our reader | SDK-2 with the SDK document agent reading the loan instead of CODEC's reader | New, later |

Order of work: first hold the reading stage constant. Feed SDK-1 and SDK-2 the same case record CODEC's reader produced, so the comparison isolates how checks are generated and judged. Only then swap in our reader (SDK-3), which measures reading separately. A single end-to-end number would blur which stage is better.

Scoring: reuse CODEC's own scorer and judge (`sme_match.py`, three-vote judge, Cohen's kappa across repeats), not a new one, and report the same columns: recall against the SME end-state conditions, strict precision, exact duplicate rate, the calculation rows separately, cost and latency per loan. Record a run manifest per arm (code hashes, models, settings, priced calls) in the same shape as theirs.

Controls we adopt from their lessons: no hand fixes (regenerate without them; a no-edit regeneration is the standard), every miss audited row by row, key checksum pinned, and a held-out set frozen before any held-out run. Their report says none is held out, so the held-out set is a fresh contribution: either loans of the seven that nobody tuned on, or the Revolution set as a second customer with its own key, which also shows the path generalizes beyond one lender.

## Slices

1. **Access and inputs.** Settle where the data lives and who runs it (Decisions 1 and 2). Obtain the Pulte JTBD set 6.2.3 file, the SME conditions JSON and the case snapshot format; write down the checksums. Owner: you for access, `sonnet-packs` for the import. Size: small, mostly waiting.
2. **Import the JTBD set as a pack and run a dry check with no model calls.** `import_jtbdset`, lint, and the coverage view (how many JTBDs name at least one field the snapshot has). Owner: `sonnet-packs`. Size: one slice.
3. **A snapshot-to-case adapter.** Map CODEC's ontology snapshot (252 tables) onto the pack's case record, field by field, with a coverage report of what maps and what does not. This is the real cost of holding the reading stage constant. Owner: `sonnet-runtime` with `sonnet-packs`. Size: one to two slices; the risk of the plan.
4. **Run SDK-1 and SDK-2 on one loan** end to end, check the manifest and cost, then on the seven. Spend needs a typed figure per arm (Decision 3). Owner: `sonnet-runtime`.
5. **Score with their scorer**, write the one-page note per arm and the comparison table, with the audit of every miss. Owner: `opus-xrepo` coordinates; the scoring runs where the data is.
6. **Held-out run** after a freeze, on the held-out set or Revolution, with the same arms.
7. **SDK-3** (our reader) once 3 to 6 stand, reusing the classification and extraction measurement from M1.

## Decisions for the user

1. **Data access.** Pulte data is real loan data that stays on the Pulte VM. Do our runs happen there (the SDK installed on that VM), or do you obtain an approved, masked copy, or does the kernel-lab side run our arms for us? This decides everything after slice 1.
2. **Who owns it on the kernel-lab side.** The Pulte and Revolution layers were most recently worked by `huaxing-jazzx`; confirm who we coordinate with so we reuse their scorer and key instead of rebuilding them.
3. **Spend.** Each model-backed arm needs your typed approval with a figure in the session that runs it. Nothing is estimated here; slice 4 produces a measured cost per loan from the dry run first.
4. **Scope of the first comparison.** Recall and strict precision on the seven development loans only, or also the held-out set before it goes in front of anyone.

## Risks

- Per-JTBD rules over-generate everywhere (strict precision 10.8 to 15.6%, duplicates); expect ours to as well. Report it, do not hide it.
- The snapshot-to-case adapter may lose fields; the coverage report shows how much of any gap is the adapter and how much the method.
- The SME key has its own label noise (`sme_label_audit.py` exists for that); score with the audited key and say so.
- A number built on the development loans is a development score, as CODEC's is; do not present it as held-out.
- CODEC's build moves (Revolution tuning is ongoing); pin the build hash we compare against.

## Not verified

The Milestone 1 report itself (figures come from our earlier note); whether the pinned CODEC build is runnable on the VM; the format and size of the SME conditions file; whether the seven Pulte development loans are the same loans in the 2026-10-14 baseline; how long a run takes per loan; whether the JTBD set 6.2.3 file is available outside the Pulte VM.
