# Note: JTBD generation, policy-workbench against Plato (2026-10-15)

Author: opus-xrepo. Assessment only; decides nothing. Sources read: `policy-workbench/backend/policyforge/prompts/policy_creator/{planner,writer}_system.md`,
`backend/jtbd_audit/` (vendored upstream lint), Plato's `jazzx_sdk/prompts/files/policy_jtbd/*.md`, `jtbd_template.yaml` (Acra seed),
`documents/Acra/acra_New_Guideline_JTBD.json`. Prior art: `note_plato_vs_policy_workbench.md` (2026-10-03, broad), `note_sibling_parity.md`.

## What the Acra "hand crafted" set is

`Acra-Lending-Standard-DSCR-JTBDs-Fable-Improved`, version 9.0.0, 123 jobs (Standard). Nine versions, an "improved" pass, and human edits in the
knowledge studio. A job in it and not in ours may be human knowledge that the guideline text never states, not a generation gap. Regen 2 produced 130
Standard jobs, regen 3b 121.

## Same approach (Plato's template was built from the workbench guide)

Four-step outline (Initial Document Review, Eligibility Verification, Validation and Verification, Final Determination), the requirement template,
section types, mnemonic families and limits, `NEW` source, roles, a skill of at most a few hundred characters.

## Where Plato is ahead

- Exhaustive: every unit that states a requirement is grouped into a section. The workbench planner is instruction-driven ("follow the user's
  request EXACTLY", "do not complete a framework"), so coverage depends on what a person asked for.
- `reads` and evidence types chosen only from the pack's lists (registry), each job carrying the units it came from.
- Code from jobs, the ledger, coverage, fold across sections, variants per program.

## Gaps

1. **Predicate-quality rules in the writer prompt.** The workbench writer carries about ten CRITICAL rules: one testable predicate per bullet that
   names (a) the document or data source, (b) the field, (c) the pass condition; no standalone "verify/confirm/review"; no vague "satisfies/meets
   requirements"; no delegation ("see program overlays"); each validation rule self-contained; step depth proportional to what the source covers;
   COMMON program-agnostic. Plato's `write_instructions` is one paragraph and `write_prompt` asks for "one predicate each". Cheapest gap to close.
2. **Deterministic language lint.** The workbench vendors upstream `jtbd_audit` (lint rules, slop spans with offsets, redundancy, cycles, severity and
   fix tiers, strip plan). Plato has readiness checks against a downstream engine, fold for duplicates, and mechanical slop for rules only.
3. Planner step sizing for parallel writers (8 to 10 policies per step): a speed choice, not quality.
4. Human editing of generated jobs in a studio: Plato has the draft, review, comments and lint triage; no studio-grade job editor.

## How to compare fairly

Group Acra-only jobs by cause: (a) the guideline states it and we missed it (generation gap), (b) the guideline does not state it (human
addition), (c) we split or merged it differently (shape). Only (a) is a prompt gap.

## Correction (the user, 2026-10-15): the workbench is built for home mortgage

Acra's set was made with it because it was the tool available, so the set carries mortgage-shaped structure Acra's DSCR product does not need:
investor blocks (COMMON, FNMA, FHLMC, FHA, VA, USDA, mostly `NO_CHANGE`; an Acra job has five `requirements` blocks), the four-step scaffold forced on every
job whatever its kind, `<metric>` blocks bound to the mortgage ontology, and GSE-flavoured guidance ("non-GSE overlay content goes in COMMON").

What changes in the analysis:

- Gap 1 (predicate quality) is generic and stays. Port it as the SDK's neutral default; nothing in it names a program.
- Gap 2 (language lint): take only the generic rules (vague and boilerplate language, redundancy, cycles). Leave investor-block, B-code and
  ontology-path rules out; Plato already has per-pack `variants` (Standard, Platinum), `kinds` and a catalog of Acra's own fields.
- Comparison category (d): differences that are mortgage-shape artifacts, not substance. Do not count a missing `NO_CHANGE` block, a missing
  investor column, or the four-step scaffold on a pure limit or determination as a generation gap. Compare a job's criterion, thresholds and the
  fields it reads.
- Open question: a cap, matrix or determination job does not need four document-review steps. The `kinds` already say which jobs expect code; a
  kind-dependent step shape would fit DSCR better than the forced outline. Acra's set uses the outline only because the tool did.
