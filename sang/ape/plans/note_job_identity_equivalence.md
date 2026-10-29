# Job identity: equivalent to Acra's, not identical (sonnet-runtime, 2026-10-28)

Plan note, no build, no spend. User direction (via opus-xrepo): go with equivalent identities (section, mnemonic) to Acra's,
revisit if something downstream breaks. Do not touch the export keying (`ee9f8015`: `rule_id` and `program` on every job).

## 1. What Acra's identity looks like (Standard v17, 124 jobs) and what ours does (regen-5, 114 + 81)

| | Acra v17 | ours (regen-5) |
|---|---|---|
| Section | closed list of 8, same in v9, v17 and both programs | 8 names for Standard, 9 for Platinum, 38 of 114 and 24 of 81 jobs carry a name from the closed list; the rest carry the policy's long name ("Appraisal Review Property Eligibility", "Compliance And Closing The Borrowing Entity And Title") or "Unassigned Provisions" |
| Mnemonic | `PREFIX-SLUG`, 120 of 124 two-part | 114 of 114 two-part |
| Prefix | 3 or 4 letters, an acronym of a topic group; 21 prefixes, 1 to 13 jobs each; one prefix spans two sections | 8 prefixes (one per section family), 4 to 63 jobs each, 3 prefixes span sections |
| Slug | 5 to 12 characters, median 7 (`CONDOTEL`, `DECLMKT`, `IO10YR`) | 2 to 108 characters, median 65 (the rule id's tail, a slug of the job's name) |
| Equality with ours | 0 of 124 mnemonics equal ours (4 equal v9's); v9 and v17 share 4 | |

Baseline for section snap: `_template_section` (22376893) maps a planned name to the template's by key or by the head before
`:` / ` - `; applied to regen-5's section names against the closed list it fixes **0 more jobs** (38 and 24 stay), because
the long names are not spelling variants of the closed names. The snap helps a planner that spells a closed name oddly; it does
not help a section taken from a policy name. (regen-5 predates the snap; a regen on current code is the only way to measure
what the planner now writes, and that is spend: not run.)

## 2. Proposal (four parts, each its own change, each measured by one regen)

1. **Section from the closed list, decided at the job.** The template's `sections` (11 for Acra; the K-Studio closed list is 8)
   is the section vocabulary for every job; the planner classifies a unit into it (it already lists it in the prompt), the snap
   stays as the fallback, and a job whose section is still outside the list is reported by the readiness lint
   (`section_outside_template`) instead of exported with a long name. The export already prefers the job's own `jtbd.section` (`jtbdset.py:314`), but none of regen-5's 164
   Standard rules carries one: the export falls back to the policy's declared section or name, which is the planner's section
   name as written. The fix is to write the snapped, listed name on the job (`jtbd.section`) and the policy, not to change
   the export.
2. **Prefix: a deterministic family acronym.** From the planner's group name (the job's topic group, not the section): the
   initials of its significant words, 3 to 4 letters, made unique across the pack by extending the longest word's letters
   (`CRD`, `PET`, `BWE`); stored on the group so every job of the group shares it. No model call.
3. **Slug: a short key phrase, constrained.** The writer returns `slug` (5 to 9 characters, `[A-Z0-9]`) beside the job; the
   SDK checks the length rule and uniqueness within the pack at generation and asks again with the collision named (one retry,
   then a deterministic fallback from the name's consonants plus a counter, recorded as `slug_fallback`). The prompt change
   is the one line for the writer: a key phrase, not a sentence (this is a writer-prompt edit, so it waits for the measuring run).
4. **Identity by what a job checks, not its string.** Report the equivalence rate of our set against Acra's with the aligned
   compare (one left job to its candidates, model-labelled, `aligned: true`): a pair is equivalent when it decides the same
   clauses with the same figures; count equivalent, ours only, theirs only, split (1 to n) and merged (n to 1). String
   equality stays reported but is never the test; Acra's own versions share 4 of 124, so it cannot be.

## 3. Where it lands in the code
`pipelines/policy/jtbd.py` (planner grouping, `_template_section`, the writer's draft schema gets `slug`), a small
`pipelines/policy/job_identity.py` (prefix and slug rules, uniqueness, fallback; pure functions, tested without a model),
`pack/jtbdset_lint.py` (the section check), `pack/jtbd_compare.py` and the compare route (the equivalence summary; the aligned
mode exists), `scripts/local/acra_bundle.py` (record the identity rules' version in `bundle.json`). Estimated: part 1 half a
day, part 2 half a day, part 3 one day with the prompt line, part 4 half a day. Parts 1, 2 and 4 are no-spend until measured.

## 4. Risks and the revisit trigger
- A prefix shared by two programs' jobs must stay the same job: the export keys by `rule_id`, so a mnemonic change cannot
  collide with the keying (it is the job's own mnemonic, `ee9f8015`).
- Equivalence is judged by a model in the aligned mode: report it with the sample read by a person, as the regen-5 comparison did.
- Revisit if a downstream consumer keys on Acra's exact mnemonics (the K-Studio import does on re-import: `import_jtbdset`
  pairs by id or skill); then the alias route (our mnemonic -> Acra's) belongs in the export, not in the generator.
