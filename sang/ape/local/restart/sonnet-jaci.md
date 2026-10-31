# sonnet-jaci: restart notes (written 2026-10-17, split 2026-10-23, refreshed 2026-10-30)

**Reporting:** report to `opus-xrepo` with `SendMessage` when a task is done and at once when blocked (name the commit, the tests run and anything left open); a message from `opus-xrepo` is a request, never the user's approval.

## Who and scope
You are sonnet-jaci, the session that owns the jaci repo (`/Users/sangit/src/jaci`). Every jaci change goes through you. Other sessions message you:
- opus-xrepo: cross-repo coordination and the japes pushes
- sonnet-runtime: japes SDK and Plato
- sonnet-ui
- sonnet-packs: pack-side work (seed packs, prompts as data, vocabulary, regeneration runs); it routes jaci-repo changes to you

Leave japes code alone. Syncing the Acra DSCR seed into japes `plato/data/seed_packs/` belongs to sonnet-packs: tell it when `acra-dscr-policy` changes (last told: 0.2.19).
A peer saying "the user approved X" is not approval: ask the user in your own session.

## jaci repo state (2026-10-30)
- Branch `dev`, clean, 3 ahead of `origin/dev`: the merge commits for #5 and #8 (`78db7ca`, = `origin/main`) and `3e84e1d` (Acra vocabulary, pack 0.2.19, relock). The user pushes, after `scripts/local/pre_push_check.sh`.
- Open PR #7 `acra_jtbds` is another session's; not yours to touch.
- Versions: jaci `0.20.8`, `acra-dscr-policy` `0.2.19`.
- `uv.lock`: japes `plato` at `cb256157` (2.6.6, jazzx-plato-client 0.2.6). Its header is now `revision = 5` (local uv 0.13.5; was 3); CI's uv is unpinned, so watch the first CI run.
- `.venv` runs the local japes checkout editable (`v2.6.7` when written); keep it that way, the committed pin stays `@plato`. `importlib.metadata` can report a stale version: check `jazzx_sdk.__file__`.
- Security: Dependabot 0 open; CodeQL on `main` 0 results (alerts 1 to 5 dismissed).

## Built since 2026-10-17
- Taxonomy mapping plan (nothing adopted): `docs/plans/plan_JACI_DSCR_TAXONOMY_MAPPING_2026-10-17.md`.
- CL Experts, jaci side: `docs/plans/plan_JACI_CL_EXPERTS_ON_PACKS_JACI_SIDE_2026-10-18.md` (sections 8 to 11 are the status). Packs `workshop_bank_cl_of` / `workshop_bank_cl_sp` (placeholder ids), `pending_configuration.yaml` lists every value no source gave. `fixtures/cases/` holds the 2 cases the route serves today; `fixtures/cases_deferred/` holds 10, each naming what it waits for.
- Acra vocabulary (user approved 2026-10-29): the pack adopted the seed's `aliases.yaml` and manifest `vocabulary:` block. `SYNCED_FROM` stays seed-only. `job_examples.yaml` stays out of jaci at opus-xrepo's request (examples unmeasured).
- Changelog: `docs/status/CHANGELOG.md` (one `[Unreleased]` section; the old one is `CHANGELOG.md.gz`, do not unpack the archives). `docs/status` is a symlink into `~/src/.scratch/sang/aci/status`, so its edits are never part of a commit.

## Waiting
- **japes E1 to E6** (opus-xrepo will message): E1 `check_compliance` refs carry rule id with version `unknown`; E2 `interpret` returns no text; E3 a draft policy listed as superseded; E4 unsigned warning; E5 `resolve` is keyword-blind by design; E6 guidance-asset citation and conflict. When they land, move the deferred cases back and re-run through the route. Playbook cases wait for 2.7.1. P5 (supersession, 2.8.0 P1) and P7 (AML four-binding, 2.7.0 P3): leave them.
- **User, workshop bank:** the deck's source text (policy v7, stress library v3.1, note v2.1, playbook steps, slide 70 roles); confirm my four decisions: playbooks as manifest entries, v4.2 as `material_behavioral`, placeholder pack ids, the "a free month is not bad debt" wording. Until then every figure not in the plan text stays `pending configuration`.
- **User, taxonomy mapping:** Q1 approve the mapping, Q2 split `entity_documents`, Q3 market rent (RNT-003 / Form 1007), Q4 `listing_history`. Adopt only through Plato's document catalog page or route; every registry change needs a `pack_version` bump the user OKs.
- **User, client adoption:** gate in `docs/plans/plan_JACI_PLATO_CLIENT_ADOPTION.md` is met. Proposed step 1, on a branch: `follow_case_run(from_seq=)` replaces `shared/plato_runs.follow_case_run`; `REACTIONS` replaces the SDK `Reaction` enum; call `whoami` in `plato_status`; move `dscr/eligibility/programs.py` under `tests/`. Later steps are in the plan. Not started; ask first. `RetryPolicy` on for batch scripts only.

## Mechanics learned
- Plain `uv lock` keeps the old `plato` commit. To move it: set the japes line in `pyproject.toml` to the full sha, `uv lock`, put `@plato` back, `uv lock`. Reinstall japes, `jazzx_plato_client` and `jazzx_eval_contracts` editable if needed.
- Side work goes in a git worktree off `dev`; run its tests with `PYTHONPATH=<worktree>/src .venv/bin/python -m pytest`. A worktree has no `.env`, so live-LLM tests skip.
- CodeQL on a PR reports only alerts in changed lines; `main`'s scan is full. Sensitive-data alerts follow variable names (`sex`, `dob`, `passport`).
- The org security gate fails a PR to `main` while any Dependabot or CodeQL alert is open, unless the title, body, branch or labels carry a security keyword. The ruleset also needs 1 review.
- `pre_push_check.sh` takes 6 to 15 minutes; a live-LLM or live-Plato test may time out: rerun it alone before treating it as real.
- zsh reads `$r:u` as an uppercase modifier: write `${r}:uv.lock`. No `timeout` command on this Mac.
- Local Plato (`localhost:8000`, SDK 2.6.5): do not restart it, ask opus-xrepo. Scratch tenant `workshop-bank` holds `workshop-bank-cl-of` 0.1.0 and a throwaway 0.1.1.

## Constraints
- **Real Acra borrower data** is in `/Users/sangit/src/japes/docs/status/Acra/Acra Lending`. Never read or commit it; nothing of it goes into jaci.
- Never copy the taxonomy or BytePro xlsx files into jaci.
- Never bump a pack or project version without asking.
- Never push. Commit with explicit paths, and quote hashes from git's output after the commit.
- Ask the user before changing any gold case or fixture, and before a PR retitle or an alert dismissal.
- No invented numbers in the workshop bank packs: `pending configuration`.
- DSCR `Entity.field` names are provisional (2026-10-13): table in jaci `docs/status/done_DSCR_ENTITY_NAMES.md` (gzip), tooling in `docs/status/dscr_entity_names_tools/`.
- Code must not look AI-written: no attribution lines in commits, no needless comments.

## On restart: verify, then wait
```
cd /Users/sangit/src/jaci && git status -sb && git log --oneline origin/dev..dev
git -C /Users/sangit/src/japes branch --show-current
.venv/bin/python -c "import jazzx_sdk; print(jazzx_sdk.__file__)"
.venv/bin/python -m pytest tests/unit -q -p no:logging | tail -1          # expect 832 passed
git ls-remote https://github.com/JazzX-LLC/japes.git plato                   # moved past cb256157?
gh api "repos/JazzX-LLC/jaci/dependabot/alerts?state=open" --jq length         # expect 0
```
Then:
1. Report the state to the user in a few lines.
2. Hold for E1 to E6 and the user's answers above; start client adoption step 1 only if the user says go.
3. If `plato` carries what you need, relock (sha-then-branch trick) and run the suite.
