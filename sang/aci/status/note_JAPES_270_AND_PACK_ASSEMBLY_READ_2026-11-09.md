# jaci: moving to japes 2.7.0, and what pack assembly would change here

Author: Virendra Mehta

Written 2026-11-09 by sonnet-jaci for opus-xrepo. Read-only: no jaci edit, relock, commit or provider call. `[V]` checked in a file or by a run, `[U]` not checked.

## 1. What jaci pins, and what moving to 2.7.0 involves

Pin today [V]: `pyproject.toml:29` has `japes[server,documents] @ git+https://github.com/JazzX-LLC/japes.git@plato`. `uv.lock` resolves it to `433b89d2` (japes 2.6.8, plato-client 0.2.8), committed as `9eb07d8` and pushed. jaci `dev` is level with `origin/dev`.

A trial against 2.7.0 [V]: I ran jaci's whole suite against a throwaway worktree of `v2.7.0` (`PYTHONPATH`, no install, no jaci file touched; worktree removed after). Result: 1194 passed, 4 skipped, 2 xfailed, the same counts as on 2.6.8. Only 3 warnings, all SWIG `DeprecationWarning`s from a PDF library; none is a pipeline-id deprecation. So no test is expected to break. Tests that need a live Plato or a provider key stay skipped, so they say nothing about 2.7.0.

Relock mechanics [V from the 2026-11-03 relock]: jaci pins a branch name, not a commit. `uv lock` keeps the old commit for a moving ref, so the relock is two steps: put the target sha in `pyproject.toml`, `uv lock`, put the branch name back, `uv lock`, then `git diff` to confirm only `uv.lock` moved and `pyproject.toml` did not. Then `uv pip install -e ../japes` to put the venv back on the editable checkout. The question to settle first is which ref jaci pins. 2.7.0 is on `main` (`2c8274b0`); jaci pins `@plato`. If `2c8274b0` is not on `plato`, pointing the pin at it means changing the ref in `pyproject.toml` (a one-line change, then the same two-step relock) or waiting until `plato` carries it. [U] whether `plato` already contains `2c8274b0`; I did not check the remote.

Auth [V]:
- **Dockerfile:** the build takes a BuildKit secret `github_token`, writes a git `insteadOf` rewrite for the install, and unsets it afterwards. A missing token now fails the build. A new ref on the same repo needs no Dockerfile change.
- **CI:** `.github/workflows/tests.yml` uses the `DEVOPS_JAZZX_TOKEN` secret as an `http.extraheader`. No change for a new ref.
- **CI mismatch worth knowing:** the workflow's "Install japes from the tip of dev" step installs `japes[litellm] @ ...git@dev` over the locked environment. So CI tests japes `dev`, not the `@plato` pin that the lock and the Dockerfile use, and it still asks for a `litellm` extra that `pyproject.toml` says jaci no longer wants. The workflow's header comments also still say jaci pins `@dev`. This is separate from 2.7.0, but a move to `main` is the moment to decide what CI should track. I have not touched it.

Known 2.7.0 changes against jaci's use:
- **Converted-document staging (`.japes/<file name>.md`):** this one touches jaci. `capabilities/commercial_lending/docintel.py` looks up `.japes/<stem>.md` (lines 5, 36, 49), and `document_packet.py:131` says it regenerates `.japes/<stem>.md`. jaci's own reader would not find a regenerated `x.pdf.md`. The YETI path in `config/packs/ci-spread-core/policies/core.yaml:38` names `.../.japes/YETI FY 2025 SEC 10-K_1.3.2026.md`; the cached file there stays valid as long as nobody regenerates it, but a regeneration would write `YETI FY 2025 SEC 10-K_1.3.2026.pdf.md` and the pack path would dangle. Changing that path edits a published pack, so it needs a `ci-spread-core` bump (the user's call). The suite passed because those tests use fixtures and stubs, not a regenerated cache. [U] whether the `<stem>.md` fallback in docintel still matches anything in a real regenerated folder.
- **Pipeline ids renamed:** [V] none of jaci's Python or YAML under `src/` or `config/` spells `pipeline_id`, and the suite showed no deprecation warning, so jaci appears not to use an old id. [U] the conductor pipelines are built through SDK types whose ids I did not trace one by one.
- **Tenant-keyed stores:** [V] jaci uses `tenant_id` only in `settings.py`, `solutions/shared/plato.py` and `ci_spread/feedback.py`, as a plain header or setting. I found no use of an SDK host-owned store, so the new required argument should not apply. [U] `ci_spread/feedback.py`, which I did not read for store classes.
- **`common` past 0.3.0:** jaci does not import `common` directly [U: only grepped by name], and the suite passes.

## 2. Pack assembly (base plus lender overlay): what changes in jaci

Starting point [V]: pack `pulte_home_mortgage_policy` 0.2.2 is one folder: `pack_manifest.yaml` with `policies: {dir: policies}`, a `programs:` map (FNMA, FHLMC, FHA, VA, each to one `JTBD_PROGRAM_*` policy), 11 job files plus 4 `jtbd_program_*` files, a `catalog.schema.json`, `jtbd_template.yaml`, and `coverage/` (rule map, topic index and the Pulte mapping, all against the Fannie Mae guide). The manifest pins one guideline set (`fannie-mae-selling-guide`, version 1, one digest). The blueprint `config/blueprints/pulte-home-mortgage.yaml` has one `guideline_set` field, one policy member (`pulte-home-mortgage-policy`, `>=0.1`) and one assistant member (`pulte-home-mortgage-core`, `>=1.2`).

What the plan needs that does not fit today:
1. **Manifest shape.** The plan assembles into `policies.core` plus `overlays` lists, but this pack uses `policies.dir` and `programs:`. An assembled pack's manifest is generated, so jaci would hold base packs and overlay packs as source folders and the assembled pack as a build output, not a checked-in folder. That decision (check the assembled folder in, or build it at publish) is the biggest one for jaci. Plato versions are immutable and the review gate checks pack files in the repo, so I would check in the assembled folder with its recorded input versions, and let a test rebuild it and compare.
2. **Guideline set.** Three families means three guide sets (Fannie Mae, Freddie Mac, government programs). Both the manifest `guidelines:` block and the blueprint's single `guideline_set` hold one. An assembled pack that mixes bases would need `guidelines:` to list more than one, or the blueprint to name one per family. This is an SDK schema question, not a jaci one. The Pulte `coverage/` files (rule map, topic index) are Fannie-only and live inside the pack folder; they would belong to the Fannie base pack, not to the lender overlay.
3. **`scripts/publish_packs_to_plato.py`.** It takes folder names under `config/packs/` and publishes each under its own tenant (`open_plato(pack=name)`, tenant from `PACK_TENANTS` in `solutions/shared/plato.py:135`). For assembly it would need: a step that calls the SDK compose function with the input versions and writes or publishes the result; a rule that base packs publish to a tenant every lender can read (the plan's open tenancy question; today the script has no shared tenant and no way to publish one pack to two tenants); and a stale check that prints which assembled packs were built from an older base. `--blueprint` resolves the tenant from the policy member's pack, which still works if the assembled pack is the policy member.
4. **Second lender.** What a Revolution lender needs in jaci, in order: an overlay pack folder, an assembled pack folder, a blueprint file `config/blueprints/<lender>-home-mortgage.yaml`, two `PACK_TENANTS` entries (assembled policy and assistant), a tenant on the Plato, the assistant pack (jaci's `pulte_home_mortgage_core` carries Pulte's name in its profile, manifest and skill file name), a registry entry in `ui/registry.py`, and tests (below). A new tenant is the user's call and a publish to the local Plato needs their yes in this session.
5. **Tests.** `tests/unit/test_pulte_blueprint.py` checks the blueprint against the SDK validator and the named pack ids. `tests/unit/test_pulte_page.py` covers the page's offline reads. Per lender I would add the same two, and one equivalence test: assemble base plus overlay and compare to the original job set after whitespace normalization (the plan's S2 check). Pulte's 68 steps that differ from CODEC (the plan's risk) have to be settled before that test means anything.
6. **Published versions.** Any pack change here, including a base split, forces a bump. The assembled Pulte would be a new pack version (0.3.0 is the natural next number, since the contents are rebuilt, not edited). I would not bump without the user's yes.

What I would want from the compose step:
- A function that takes pack folders (or published pack ids and versions) and writes a pack folder, deterministic, so a jaci test can rebuild it and diff.
- A recorded provenance block in the manifest (layer, source pack id and version, source file per rule) that Plato and the page can show; the Pulte page's Jobs tab could add a "layer" column from it.
- Rule ids stable across assembly (jaci's `JTBD_*` ids equal CODEC's mnemonics; a split must not rename them, or the coverage and guide-link files that key on them break).
- A report, as data and not only prose: stale inputs, refused overlays (reused id with no declared override, a relaxing overlay) and rules it could not classify.
- `programs:` handled explicitly: the Pulte `JTBD_PROGRAM_*` policies are already agency-scope overlays (FNMA 9, FHLMC 53, FHA 58, VA 57), so say whether they stay as program overlays inside the assembled pack or become part of the family bases.
- Guideline sets per family, as in item 2 above.
- A way to publish one base to several tenants, or a shared tenant, from the client (`put_pack` today is per tenant).
- No jaci-side code: if compose lives in the SDK, jaci's script stays a thin caller.

## 3. What a studio-neutral design would trip over in jaci

Naming [V]:
- **Code:** `src/jaci/solutions/pulte_home_mortgage/ui/demo_page.py` hardcodes `BLUEPRINT`, `POLICY_PACK`, `_FOLDER` and `pulte_*` session and widget keys, plus Pulte wording in headings and captions (lines 5, 26-28, 154, 160, 172). `ui/registry.py:158-165` has one Pulte entry. `solutions/shared/plato.py:140-141` maps two Pulte pack folders to the tenant `pulte`. A lender-neutral page would take the blueprint id, policy pack and folder from the registry entry (a few arguments to `render_demo_page`), and the registry would hold one entry per lender. That is a small change and the one I would do first.
- **Config:** pack ids, blueprint id, `client: pulte`, the manifest and the assistant pack's file names (`pulte_home_mortgage_core_intake.yaml`).
- **Rule content:** `coverage/pulte_jtbd_guide_mapping.yaml` and `scripts/adopt_guide_links.py` are named for Pulte and key on its catalog's cited topics. The Fannie rule map and topic index are not Pulte data and would move to the base pack.
- **Job text:** lender practice is inline in 36 of the Pulte jobs per the plan; it is not separable by code until S0 and its review settle it.

Structural [V]: nothing in jaci's solution code assumes a single policy folder with no layering beyond the page's `_repo_jobs()`, which reads `policies/jtbd_*.yaml` and skips `jtbd_program_*` by file name prefix. An assembled pack with `core` and `overlays` lists would need that offline fallback to read the manifest instead of globbing.

Not touched: no loan data, no Pulte VM, no Plato restart, no publish.
