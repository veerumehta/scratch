# Plan: multi-program assessment, Acra's JTBD sets as version 0.0.0, and a comparison with ours

Status: proposed (2026-10-06). Asked through opus-xrepo as user-approved; the precedence in item 1
is the user's decision. Not started.

## What the Acra files are (read 2026-10-06; documents/ is local and untracked, never committed)

- `acra_New_Guideline_JTBD.json`: JTBDSet "Acra-Lending-Standard-DSCR-JTBDs-Fable-Improved"
  9.0.0, 123 values. `acra_New_Guideline_JTBD_Platinum.json`: "Acra-Lending-Platinum-DSCR-Fable-improved"
  7.0.0, 108 values.
- A value has `mnemonic` (PRE-TYPES), `section`, `skill`, `sequence`, `entity_types`,
  `loan_metrics`, `extraction_targets`, `notes`, and `requirements`: one block per `investor`.
  Every value's blocks are `COMMON` (the text) plus `FNMA`, `FHLMC`, `FHA`, `VA`, all `NO_CHANGE`.
  So `import_jtbdset` already turns each file into core-only policies (one section policy each, a
  `procedure` rule per JTBD, ids = mnemonics); the agency blocks add nothing.
- Standard and Platinum are therefore two corpora, not one corpus with program blocks. 71 mnemonics
  appear in both files (123 and 108 in all).
- Our `dscr_core` has `programs: {standard: [DSCR_STANDARD], platinum_select: [DSCR_PLATINUM_SELECT]}`
  over a core (`DSCR_PROCESS`); `assess` evaluates one program per call (`_program_policy_ids`).

## What exists

`jazzx_sdk.pipelines.jtbdset` (`import_jtbdset`, `export_jtbdset`), `GET .../jtbdset` exports (draft and
version), `merge-rules` (writes accepted rules into a draft), `pack.diff.diff_files` (file and rule
diff of two trees), `pack.assessment.assess` and `POST /packs/{id}/assess`, openpyxl (the Excel
Trends sheet), `jazzx_plato_client` (no `__main__` yet).

## Phase 1. Multi-program assess

- Precedence, as decided: the input's `program_id` names one: only that program runs, as today.
  Else the call's `programs: [..]` or `programs: "all"`. Else the manifest: `default_program` (one,
  unchanged), or an assessment block's `default_programs: [...]` with `select: first_eligible`.
- The core policies are evaluated once and each overlay's policies once, then composed per program
  (a reasoned core rule is judged once, so it cannot disagree with itself). Per-program results:
  verdict, findings, and for `first_eligible` the selected program and why each earlier one failed.
- Additive on `PolicyAssessment`: `programs: dict[str, ProgramAssessment]`, `selected_program`,
  `skipped: {program: reason}`; a single-program call returns today's fields and an empty `programs`.
  jaci's DSCR page and the eval `pack`/`case_run` entities see no change.
- Route: `POST /packs/{id}/assess` takes `programs`; client `assess(..., programs=)`. A test pins the
  single-program answer byte for byte against today's.

## Phase 2. Version notes

`notes` (free text, provenance) on `pack_version` and on a draft: migration 0022 adds both columns;
`publish`/`publish_draft` and the import take it; `GET` of a version, history and the packs page show
it; client contracts carry it. Existing rows read empty.

## Phase 3. JTBDSet import, and the two-file import

- `POST /packs/{id}/jtbdset` (body: the artifact, optional `program`): `import_jtbdset` into the
  pack's draft as policy files, like `merge-rules` (publishing stays separate). Client method.
- `POST /packs/{id}/jtbdset/programs` (body: `{standard: <artifact>, platinum_select: <artifact>}`):
  the shared matcher pairs JTBDs across the files. Same in both: the core, once. Different, or in one
  file only: that program's overlay policy (`DSCR_STANDARD`, `DSCR_PLATINUM_SELECT`), with the
  manifest's `programs:` map written to match.
- Then, for Acra: import both files into a dscr-core draft opened from the seed, set
  `pack_version: 0.0.0`, publish with notes "Acra 9.0.0, imported from acra_New_Guideline_JTBD.json +
  _Platinum.json". Our extraction is published separately as 1.0.0. The import script is local
  (reads `documents/`), not shipped.

## Shared matcher (phases 3 and 4)

Rule ids differ (their mnemonics, our extracted ids), so match on content, deterministic first:
1. exact id; 2. same section (slug) and normalised skill text; 3. same section and the closest
skill text by token overlap and shared metric keys (`loan_metrics[].metric_key`, our rules' `reads`),
accepted above a high threshold with a clear winner. Anything left ambiguous (a close second, or
below the threshold but above a floor) goes to the model, one batched call per section, and the
answer is recorded with the model and prompt version (the provenance work). Pairs below the floor
stay unmatched. The matcher returns pairs, the unmatched on each side and, per pair, how it matched.

## Phase 4. Comparison

Two inputs, each a pack version or a JTBDSet artifact. Output: only-theirs, only-ours, and
both-but-different with the differing fields (skill text, section, steps, outcomes, metric keys,
evidence types). Route `GET/POST .../compare` + client `compare()`; JSON and xlsx downloads (a sheet
each for the three groups and a summary).

## Phase 5. CLI

`python -m jazzx_plato_client export-jtbdset --pack <id> (--draft | --version V)` (JSON to stdout),
`proposals --pack <id>` and `compare ...`. URL, tenant and token from `PLATO_URL`, `PLATO_TENANT`
and `PLATO_TOKEN` or flags.

## Order and tests

1 then 2 then 3 then 4 then 5; each lands on `v2.6.1` with its tests, a CHANGELOG entry and its
client method (the route/client parity test enforces it); one adversarial review at the end.

## Decisions (2026-10-06)

1. Publish 0.0.0 first, so 1.0.0 stays the newest and the default.
2. A model may break ties for ambiguous pairs only.
3. "Same in both" is identical normalised text in the same section; near matches go to each program's
   overlay and are listed in the comparison.
