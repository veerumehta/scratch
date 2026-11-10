# Pack assembly: a domain base plus lender overlays, assembled into the pack a customer publishes

Author: Virendra Mehta

Written 2026-11-09 by opus-xrepo. Sources: the user's direction (below), `sonnet-packs`' read-only comparison (`docs/status/note_pulte_revolution_jtbd_comparison_2026-11-09.md`), and a read of the 2.7.1 tree (`jazzx_sdk/pack/blueprint.py`, `blueprint_chain.py`, `manifest_loader.py`, `fabric/canonical/policy.py`) and of jaci's Pulte pack (`/Users/sangit/src/jaci/config/`). Plan only: nothing built, no spend, no loan data opened. `[V]` checked in code or a file, `[U]` not verified.

## Status and modifications

How to use this section: the plan author may read and update it; implementers append one dated line per slice. Newest line last. Branch: not chosen (the user decides the version branch; no version bump is implied).

- 2026-11-09 drafted from the user's decisions: assemble at publish time first; the base is three families (Fannie Mae, Freddie Mac, government programs) and a lender overlay may only add checks or tighten, never relax; `sonnet-packs` extracts the lender-practice passages from the existing job texts.

- 2026-11-09 S0 done by `sonnet-packs` (`docs/status/note_lender_practice_passages_s0_2026-11-09.md` and a 214-row CSV; rule-based on headings and phrases, candidates for a lender SME, not verdicts). Findings that change this plan: (a) the existing sets already have the shape of a base plus overlays: COMMON is conventional text with a Fannie lean, and the FNMA, FHLMC, FHA, VA and USDA texts are deltas on it, most a `NO_CHANGE` stub; (b) the add-or-tighten rule will not hold throughout: Pulte APR-BASE raises a cost cap from 10% to 15% and Revolution's reps-and-warrants asset text drops conditioning, both loosenings of agency text, and several other passages are unclear; (c) "overlay" headings are not reliably lender policy: 37 of Revolution's 129 passages are USDA, FHA and FNMA program text under a "(Revolution overlay)" heading that cites the agency handbook, and Pulte's 7 other flagged jobs carry only a stock sentence; (d) 14 jobs carry lender passages in both sets with different wording, only 3 shared nearly verbatim (INC-SEL self-employed conditions); (e) government material also sits inline in Revolution's COMMON (160 HUD 4000.1 citations), so the government base needs extraction from COMMON too; (f) USDA belongs to the government family by Revolution's grouping, with one lender's wording behind it; (g) base candidates by size of real text: Freddie 55K and 62K characters, FHA 57K and 182K, VA 52K and 63K, USDA 20K (Revolution only). Decision 2 needs a refinement for loosenings: see "Decisions still open".

- 2026-11-09 decision (user): a lender loosening of agency text is refused by default; it is allowed only as a declared `relax` that cites the agency text that permits it and goes through the widening class and the certification forum (2.7.1 guidance governance already has that class and forum). The S1 design note and the non-widening lint follow this.

- 2026-11-09 found while reviewing the Desktop plan `plan_revolution_codec_vs_sdk_comparison.md`: the SDK already has an importer for the program-level version of this idea (`jazzx_sdk/pack/jtbd_import.py`: one JTBDSet becomes a section policy per section and an overlay per program block; two sets, one per program, are matched so a job whose text is the same in the same section goes to the core once and a different job goes to its program's overlay [V from its docstring]). S3 and S4 should extend that matcher to lender passages, not start over. The code-level differential harness in R4 of that plan doubles as the equivalence test in S5 here.

## Goal

US home mortgage solutions start from an agency's guidelines, Fannie Mae or Freddie Mac depending on who will buy the loan, and a lender (Pulte, Revolution) applies its own overlay on top. The final pack set for a lender is the base for the loans it originates plus that lender's overlay. Today the Pulte and Revolution job sets are one monolithic text per job, so nothing can be reused between lenders and Revolution's 183 jobs share almost nothing as text with Pulte's 115 even though they are the same lineage.

## What the user decided

1. Assemble at publish time first. Run-time layering across packs is a later feature, only if evidence asks for it.
2. The base is three families: Fannie Mae, Freddie Mac, and government programs (FHA, VA, USDA, which do not start from Fannie or Freddie). A lender overlay may add checks or tighten agency rules and never relax them.
3. `sonnet-packs` extracts the lender-practice passages from the existing jobs, as candidate overlay lists.
4. Studio framing (user): crafting the solutions was always expected to happen offline with the various studios. The Pulte and Revolution work in jaci is a local path until the existing studios (Knowledge Studio, Builder Studio) catch up to the SDK. So what the SDK ships must be studio-neutral: a base pack, an overlay pack and an assembled pack are plain pack artifacts any studio can produce or consume, and nothing in the SDK or jaci config is named for a lender.

## What exists today

- A pack's manifest lists policy files in precedence order, `policies.core` then `overlays`, and a `programs:` map from a program id to the overlay policy ids that apply; a policy carries an `overlay_id` for an institutional override [V `pack/manifest_loader.py` 191 to 216, `fabric/canonical/policy.py` 708].
- A blueprint needs exactly one `policy` member and allows at most one each of `assistant`, `core` and `reference`; I found no code that merges a `core` pack's policies into the policy pack at run time [V `pack/blueprint.py`; `ROLE_CORE` is declared and ordered, nothing more].
- The blueprint chain (domain pack, surface binding, client overlay, execution profile, each layer only narrows) governs autonomy, not job content [V; `sonnet-packs` agrees].
- jaci's Pulte pack: blueprint `pulte-home-mortgage`, policy pack 0.2.2 (draft) with 15 job files, 115 institution-scope rule ids equal to CODEC's Pulte mnemonics and 177 program-overlay rules (FNMA 9, FHLMC 53, FHA 58, VA 57); same lineage as CODEC's set [from the comparison note].
- Revolution (kernel-lab): 183 jobs, 107 shared with Pulte by id, 8 Pulte-only, 76 Revolution-only (mostly government-program depth and a Condo Project section), same section and skill for the shared ones, none with identical requirement text. Lender-practice passages sit inline in 36 of Pulte's jobs and 58 of Revolution's [from the comparison note; the guide-versus-lender split is the note's reading of headings and phrases, not a measured classification].

## Design

Layers.
- **Base pack, one per family:** the jobs that come from the agency's guide only. Versioned and immutable like any pack.
- **Overlay pack, one per lender:** the lender's additions and tightenings, each overlay rule naming the base rule it narrows (or declaring itself an addition).
- **Assembled pack, one per lender and base mix:** what the lender publishes to its tenant and what the blueprint's policy member points at. Its manifest lists the base files as `policies.core` and the overlay files as `overlays`, so the existing loader, precedence and lint apply unchanged. Each rule keeps a provenance record: layer, source pack id and version, file.

The compose step (design by `sonnet-runtime`, SDK first, a function and a script, later a Plato route studios can call):
- Inputs: base pack versions, overlay pack version, the assembled pack's id and version.
- Output: a new pack version, deterministic (same inputs give the same digest), with the layer provenance and the exact input versions recorded in its manifest.
- Refuses: an overlay rule that reuses a base rule id without declaring an override; an overlay that relaxes a base rule (below); unresolved references.
- Updating a base means re-assembling each lender's pack; the recorded versions show which assembled packs are stale.

Overlay may only narrow or add. Rule: an overlay rule is either `add` (new id) or `tighten` (an override of a base id). The lint checks what it can decide structurally (a numeric comparator that moves toward stricter, an action that moves up the severity order deny, refer, allow, extra required conditions) and flags everything else for human review rather than guessing. This is the policy-content counterpart of the blueprint chain's non-widening check, which today covers autonomy only.

## Slices

S0. **Extract candidate lender passages.** `sonnet-packs`, read-only, no spend: for Pulte's 36 and Revolution's 58 jobs with inline lender practice, list job id, passage, and a guide-versus-lender call with a confidence, using headings and phrases only; no model. Output: a note in `docs/status`. Needs review by the lender's SME or the studio owner before anything is split.
S1. **Compose design note.** `sonnet-runtime`, after its current queue: the function's contract, the provenance record, the override and non-widening rules, the conflict cases, and how the assembled pack's digest and the blueprint cite versions. No code.
S2. **Build compose, provenance and the non-widening lint**, with tests, in a neutral package (CLAUDE.md guideline 7: not the `jazzx_sdk/` root). Equivalence test: assembling a base plus an overlay that came from a split job gives the same rules as the original, after whitespace normalization. One to two slices.
S3. **Base packs, guide only.** Start with Fannie Mae from the 107 shared jobs' guide content, then Freddie Mac, then the government family (FHA, VA, USDA). `sonnet-packs`.
S4. **Lender overlays.** Pulte first, then Revolution, split from the reviewed S0 output. Crafted offline with the studios or the lender's SME; jaci config is the local path.
S5. **Assemble both lenders' packs** and compare to the originals (jaci's Pulte pack and Revolution's v6.7) job by job; the assembled Pulte should reproduce the original behavior.
S6. **Hand-off to the studios:** a short contract note on what a studio produces (base pack, overlay pack, declared overrides) and what the SDK assembles and checks, so Knowledge Studio can author the same artifacts.
S7. **jaci config** for the two lenders (blueprints and the assembled packs published to each tenant). This needs a jaci session, which is the user's call; jaci changes never come from a japes session.

## Relationships

- `plan_pulte_home_mortgage_sdk_comparison.md` compares the SDK on Pulte against CODEC and MACER with the original monolithic set; the assembled pack comes later and is checked against the same key. Revolution is its held-out customer.
- `plan_adopt_existing_jtbds.md` covers adopting an existing JTBD set into a pack; S3 to S5 reuse that path.
- Run-time layering across packs (a blueprint with several policy layers, resolver and assessment reading them in precedence order) stays out until evidence asks for it.

## Risks

- The guide-versus-lender split is judgment, not measured; S0's confidence marks and the SME review are the control. A wrong split changes behavior, which S5's equivalence comparison catches.
- 68 of 115 steps in jaci's Pulte pack differ from CODEC's 6.2.3 text for reasons nobody has diagnosed; the equivalence test needs that settled first.
- FHA text differs most between the lenders (similarity upper bound 0.44, against 0.74 to 0.88 for other investors); the government family may need its own review.
- Re-assembly drift: base updates must trigger a stale-pack report or lenders run old bases without knowing.
- Tenancy: assembled packs publish to a lender's tenant only; the base packs need a home that every tenant can read, which is a decision for the Plato owner.

## Decisions still open

- Which version branch carries S1 and S2 (the user decides; nothing is bumped here).
- Who reviews the S0 output on the lender side, and whether the studio owner or the lender's SME decides guide versus lender.
- Where shared base packs live for tenant access.

## Not verified

Run-time behavior of a `core` member next to a `policy` member; whether USDA belongs in the government family or is its own; whether Freddie Mac's overlay texts in the existing sets are cleanly separable; the 68 differing steps; how the studios store packs today.

- 2026-11-09 from `sonnet-packs` R1 (note `note_revolution_pack_r1_r2_2026-11-09.md`): importing Pulte 6.2.3 through `import_jtbdset` reproduces jaci's Pulte pack exactly (292 of 292 rule conditions equal), so the risk "68 of 115 steps differ" is settled: the earlier figure compared split steps with whole COMMON text. The S5 equivalence test no longer needs that diagnosis first. Revolution imports unchanged (183 base rules, 401 overlay rules).
