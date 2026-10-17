# sonnet-jaci: restart notes (written 2026-10-17)

## Who and scope
You are sonnet-jaci, the session that owns the jaci repo (`/Users/sangit/src/jaci`). Every jaci change goes through you. Other sessions message you:
- opus-xrepo: cross-repo coordination and the japes pushes
- sonnet-runtime: japes SDK and Plato
- sonnet-ui

Leave japes code alone. The one exception: syncing the Acra DSCR seed into `japes/plato/data/seed_packs/acra_dscr_policy`, committed by path only (`git commit -- <that folder>`), with `SYNCED_FROM` updated.

## jaci repo state
- Branch `dev`. The working tree was clean when this was written; `output/` run files are ignored.
- `origin/dev` is at `f31c9a9`.
- **Two commits are unpushed:**
  - `a1f6b15`: stop passing the KYC dashboard's notes box to the eval subprocess (CodeQL alert 5)
  - `030eb83`: name the missing field, not its value, in the KYC document sync check (CodeQL alert 4)
- **To push:** the user pushes, after `scripts/local/pre_push_check.sh`.
  - The check fails on the Dependabot alerts (Werkzeug, Mako, multidict). Those are on `main`; `dev` already locks the fixed versions.
  - So the push command is `git push --no-verify origin dev`, once the suite and review in that check pass.
- jaci's `.venv` runs the local japes checkout, installed editable. When tests break on imports, check which branch japes has checked out (`v2.6.4` at the time of writing).
- `uv.lock` pins japes `plato` at `71961a88` (2.6.3, jazzx-plato-client 0.2.4).
- The DSCR pack is `acra-dscr-policy` 0.2.18:
  - `Entity.field` fact names
  - a document registry (`document_types.yaml`)
  - job kinds, prefix families, variants, extraction settings, `export_profiles/agency_blocks.yaml`
- The seed in japes was synced at 0.2.18 (`3f2a30bb`).

## Plan: `docs/plans/plan_JACI_PLATO_CLIENT_ADOPTION.md` (revised 2026-10-17)
**Gate:** relock jaci to the next `plato` pin that carries jazzx-plato-client 0.2.5 (japes v2.6.4). Do nothing in that plan before then.

Adoption order after the relock:
1. Small fixes:
   - `follow_case_run(from_seq=)` replaces `shared/plato_runs.follow_case_run`
   - `REACTIONS` replaces the SDK `Reaction` enum
   - call `whoami` in `plato_status`
   - move `dscr/eligibility/programs.py` under `tests/`
2. Clinical intake on scripted sessions; drop the in-process path.
3. Cut the SDK out of AML's Plato import path.
4. CRE and insurance intake through `upload_document` and `read_document`; document packets become a subject plus labels (`documents(subject=, label=)`).
5. `record_outcome` for C&I and CRE results so `chat(scope=)` is grounded; then guidance (`draft_guidance_from_feedback`, approve, deploy).
6. `extract_policy.py` through the draft and `start_extraction`.
7. CRE `assess` and Plato experiments.
8. The feedback sink through `open_plato`.
9. C&I on Plato, last.

`RetryPolicy`: on for batch scripts only.

## Acra document-registry work (not started)
- Acra's Master Taxonomy (152 entries, ids like APP-001) and the BytePro LoS list are loaded as references on local Plato.
- Adopt entries into `acra-dscr-policy` through Plato's document catalog page or route, never by hand.
- **First**, draft the mapping in a `docs/plans` plan and get the user's OK:
  - the 11 coarse evidence types → taxonomy categories or entries, as parents;
  - Core vs Conditional → `required_classes`;
  - keep jaci's slugs, with the taxonomy id as an external id;
  - BytePro names and codes as aliases.
- Known gaps: Listing history has no LoS type; Rent roll → Multi-Family Rent Roll plus Rental Agreement is a guess.
- **Nothing is adopted yet.** Any registry change needs a `pack_version` bump, and the user must OK every bump.

## Constraints
- **Real Acra borrower data** lives in `/Users/sangit/src/japes/docs/status/Acra/Acra Lending`. Never read it or commit it; nothing of it goes into jaci.
- Never copy the taxonomy or BytePro xlsx files into jaci.
- Never bump a pack or project version without asking.
- Never push. Commit with explicit paths, and quote hashes from git's output.
- Ask before changing any gold case or fixture.
- The DSCR `Entity.field` names are provisional ("for now", 2026-10-13). The table and open questions are in jaci `docs/status/done_DSCR_ENTITY_NAMES.md`.
- The rename tooling was saved from `/tmp` to jaci `docs/status/dscr_entity_names_tools/`: mapping YAML, migration script, quoted-name rename, and the assessment recorder plus compare.

## Waiting on the user
- Push the two jaci commits (above).
- CodeQL alerts 1 to 3 (synthetic KYC document generators): dismiss them as "used in tests", or switch the repo to an advanced CodeQL setup that excludes those scripts. Default setup can't exclude paths.
- Merge `dev` into `main` to close the Dependabot alerts, or apply a three-package fix off `main`. Not asked for yet.

## On restart: verify, then wait
```
cd /Users/sangit/src/jaci && git status -sb && git log --oneline origin/dev..dev
git -C /Users/sangit/src/japes branch --show-current
.venv/bin/python -c "import jazzx_sdk, importlib.metadata as m; print(jazzx_sdk.__file__, m.version('japes'))"
.venv/bin/python -m pytest tests/scenarios/dscr -q -p no:logging | tail -1   # expect 220 passed
git ls-remote https://github.com/JazzX-LLC/japes.git plato                   # has the pin moved past 71961a88?
```
What to do first:
1. Report the state to the user.
2. If `plato` now carries client 0.2.5, propose the relock: `uv lock --upgrade-package japes --upgrade-package jazzx-plato-client --upgrade-package jazzx-eval-contracts`, then the suite.
3. Otherwise wait for the user or opus-xrepo.
