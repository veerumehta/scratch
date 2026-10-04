# jaci: pending work as of 2026-10-01

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: plan, 2026-10-01 — written at the close of a session so the next one can pick up. Nothing
here is started. Read with memory `project_plato_pilots_state` (full history) and
`docs/plans/note_JACI_SDK_USAGE_AND_CARVEOUT.md`.

## 0. Where things stand

- `dev` = `origin/dev` = `4db04c4`. Nothing uncommitted.
- A **local, unpushed stack** on top of it, each branch built on the previous:

  | Branch | Tip | Commits past `origin/dev` | What |
  |---|---|---|---|
  | `dscr-acra-0.2` | `0fd586a` | 9 | Acra programs (other session's `acra-programs`, rebased), Plato-client adoption + model-overlay removal (`618e030`), dscr-core 0.2.0 with human checkpoint (`543a116`), version 0.20.8 |
  | `cre-pack` | `aedd711` | 17 | `cre_underwriting_core` as a Plato-runnable pack: real Mesa/MAA fixtures, appraisal evidence fields, reasoner tuning, T-12 confirmation hold |
  | `policy-extract` | `6d189a2` | 18 | `scripts/extract_policy.py policy` drafting C&I rules with the SDK policy pipeline (checked out now) |
  | `wip-plato-client-dscr` | `2101914` | — | pre-merge WIP, superseded by `dscr-acra-0.2`; deletable |

- jaci's `.venv` runs japes (`v2.6.0`), `jazzx_plato_client` and `jazzx_eval_contracts` **editable**
  from `/Users/sangit/src/japes` — keep it so (memory `reference_japes_branch_flow`).
- japes `v2.6.0` is local and unpushed; the stack above cannot reach `origin` until it is (task 3).

## 1. Decisions waiting on the user

| # | Decision | Context |
|---|---|---|
| D1 | Should japes-3e write the **`case_pipeline` plan**? | Proposed by japes-3e 2026-10-01, nothing built: a conductor kind declared as an ordered list of japes step kinds — `document_ingest` (DocumentAgent convert/classify/extract into the input schema), `policy_assessment`, `adjudication` (AdjudicationAgent over live/JTBD rules, classified docs as evidence), `narrate`, human checkpoint — run through `/runs`. Overlaps `conductor_pipeline` ("Later" in `plan_plato_domain_pack_runtime.md`). If yes, ask that it **state CRE's post-loop policy check over the reasoner's underwritten figures as a requirement** (not yet designed). japes-3e suggests DSCR as the first pack, CRE next. |
| D2 | Re-run the **C&I policy extraction** now that japes fixed its five defects? | Task 1. Live LLM calls (cost). |
| D3 | Does `ci-spread-core/policies/core.yaml` move to the extraction pipeline? | **Decided 2026-10-02: no (option B).** `core.yaml` stays hand-authored, its passages checked by `verify-policy`; `extract_policy.py policy` stays a drafting tool for review. The re-run on japes' fixes gave 3 rules, and the only checkable one is YETI's own springing FCCR covenant (deal term, not pack policy). Not done, and why: making that covenant a deal-tier overlay waits on (a) 1.10x (draft agreement) vs 1.00x (`tests/eval/gold_cases/ci/case_01_yeti.json`), (b) the clause's denominator being the revolving commitment, not total availability, and (c) Plato's `policy_check` applying program/deal policies. |
| D4 | `cltv_pct` rounding | Pack `metrics.yaml` rounds to 2 places (Plato); the in-process path did not. Now moot for DSCR if 0.2.0's in-process path is the SDK pack assess (it is, per `543a116`) — confirm, then drop this. |
| D5 | `ci-spread-core` `programs:` vs `OVERLAY_MAP` | Two program→overlay tables (`pack_manifest.yaml:52`, `ci_spread/policies/registry.py:53`); the pre-push review keeps reporting it. Owner's call which becomes the source. |

## 2. Tasks

### Task 1 — Re-run the C&I policy extraction (needs D2)

On `policy-extract`, against the editable japes (`fab0793e` or later):

1. Drop the `flex_` workaround: `scripts/extract_policy.py:271-272`
   (`model = parse_model_tier(resolve_model())[0]` and its comment) — `resolve_model` now strips the
   prefix and `with_cost_tier` restores `service_tier="flex"` on every OpenAI path. Remove the
   then-unused `parse_model_tier` import (`:246`).
2. Re-run `extract_policy.py policy` over the ci-spread-core corpus **with `--reads`** (the fields
   the rules read), so clauses reading none of them are not proposed.
3. Compare with the hand-authored `config/packs/ci-spread-core/policies/core.yaml`, and report:
   - rule count (was 8 natural-language rules from 119 clauses);
   - rule ids — now `{policy_id}.{doc file name}.{position}`, unique per clause;
   - the springing FCCR covenant — expected as applicability `excess_availability_pct < 10`
     with condition `fccr_x >= 1.10` (was lost to an id collision);
   - long unnumbered prose split at ~2000 characters.
4. Report before touching `core.yaml` (D3). Commit the script fix on `policy-extract`.

Also from fab0793e, untested live: `gpt-6-luna` strips `temperature` on every call, which should fix
the live ACORD extraction test — run it once and confirm.

### Task 2 — `case_pipeline` (needs D1; japes builds, jaci authors)

- Do **not** hand-roll a jaci-side conductor or new Python step runners for document ingest,
  adjudication or post-loop checks (japes-3e's explicit ask). Keep DSCR and CRE on
  `investigation_loop` until the kind lands.
- When it lands: author `dscr_core` against it first (its seed in Plato mirrors jaci, it has the
  human checkpoint, the Acra documents exist), then CRE with the post-loop check, then C&I.
- What exists today to build on: `investigation_loop`; pre-loop `policy_assessment` (refuses an
  input missing a field a rule in force reads unless the pack sets `missing_inputs: skip`; optional
  pre-loop reasoning); `DocumentAgent` + `run_document`; `AdjudicationAgent` as a library.

### Task 3 — Move the pin when japes 2.6.0 is pushed (user signals it), then push the stack

In **one** change (from memory `project_plato_pilots_state`):

1. `pyproject.toml`: `"japes[server,documents] @ git+…japes.git@<branch>"` — 2.6.0 moved uvicorn
   (server; needed for `JAPES_RUN_MODE=server/both`) and pymupdf/python-docx/bs4/feedparser
   (documents) out of core; anthropic is pinned directly by jaci; FastAPI stays core.
2. Add `"jazzx-plato-client @ git+…japes.git@<branch>#subdirectory=jazzx_plato_client"`.
3. `jazzx-eval-scorers` is gone (now `jazzx_eval_contracts.scorers`); jaci never imported it —
   nothing to add.
4. Relock; reinstall japes, `jazzx_plato_client` and `jazzx_eval_contracts` editable again.
5. If the pinned japes carries the pack-schema null fix (`e1e6b4c2`), delete `_without_nulls` in
   `scenarios/dscr/plato_review.py` (still present on `cre-pack`).
6. `./scripts/local/pre_push_check.sh`, CHANGELOG (`docs/status/CHANGELOG.md`), then hand the user
   `! git -C /Users/sangit/src/jaci push origin <branch>` (the hook blocks pushes from Claude).
7. Order: land `dscr-acra-0.2` → `cre-pack` → `policy-extract` on `dev` (fast-forward; they are
   stacked). jaci version is 0.20.8 on the stack — one patch above origin's 0.20.7; no further bump
   without the user (memory `feedback_version_bumps`).

### Task 4 — Small items

- Delete `wip-plato-client-dscr` once the stack is on `dev` (user's go-ahead).
- Check the reported japes bug "`/assess` ignores schema defaults (raw JSON → 422)" — fixed on
  `v2.6.0`? If so, drop any jaci-side default-filling that worked around it.
- The `/jaci/` → `/plato/` URL derivation is unit-tested only — verify behind the real dev-daily
  gateway when jaci is next deployed there (identity headers reach Plato; tenant from the gateway).
- CRE: `CFI-DSCR-FLOOR` duplicates the core floor (lint warning) — owner's call.
- SDK carve-out (`note_JACI_SDK_USAGE_AND_CARVEOUT.md`): direction since set — jaci uses no
  `jazzx_sdk`, Plato only via `jazzx-plato-client`; `jaci/paths.py` and the `dscr/` and
  `clinical_intake/` package `__init__`s still load the SDK, by choice, until a Plato-only consumer
  exists (memory).
