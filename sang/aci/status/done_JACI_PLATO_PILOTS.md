# Done: DSCR and clinical intake on Plato

Author: Virendra Mehta · Completed 2026-09-28
Repo: jaci only (japes findings reported, not fixed — see below) · Landed: uncommitted on `dev`
(on top of `d587a50`, the `japes-2.5.5` merge that pins japes `@plato`), commit pending explicit
go-ahead; no version bump (that merge already claims 0.20.7)
Plan: `docs/plans/plan_JACI_PLATO_PILOTS.md` (superseded by this file). Platform half: japes
`docs/plans/plan_plato_domain_pack_runtime.md`, built on japes' local `v2.5.6` branch.

The two pilot scenarios now run either in-process (unchanged, keyless where they were) or on a
Plato deployment, chosen per page. Both paths read one set of pack files, and the Plato path is
checked against the in-process one: the DSCR grid over all 5 gold loans, and the 4 clinical
personas' decisions and escalation clauses. Built against japes' local `v2.5.6` checkout, then
re-verified on the pinned `@plato` (`43c13d18`, the squash of that work); japes' new pieces are
imported lazily, so on a japes without them every Plato-dependent test skips and the rest pass.

## What shipped

- **Glue** — `scenarios/shared/plato.py`: `JACI_PLATO_*` settings (`JACI_PLATO_URL` is the API
  root, the `japes-2.5.5` branch's convention; `PlatoConfig.from_api_root` splits it into service
  root — a gateway mount included — and prefix). With the URL unset, `api_root_for_page` finds
  Plato beside the page: `https://<host>/jaci/…` → `https://<host>/plato/api/v1` (dev-daily),
  localhost → `http://localhost:8000/api/v1`; the tenant falls back to the gateway's
  `X-Tenant-Id`, and page calls forward the caller's `x-security-context`/`x-user-*`.
  ci_spread's feedback sink resolves its URL the same way. `plato_status()`, `open_plato()`, a deterministic `pack_archive()` (an assistant
  folder's `pack_manifest.yaml` left out), `publish_pack()` (check → publish → activate; identical
  contents reactivate, changed contents under a published version raise
  `PackVersionConflictError`), and the shared `render_backend_choice()` radio.
- **Env templates** — `.env.local` (was `.env.local.example`; now committed, with the local
  Plato settings) and `.env.dev-daily` (new; `JACI_PLATO_URL` left unset on purpose), the japes
  repo's convention. This machine's `.env` gained `JACI_PLATO_URL=http://localhost:8000/api/v1`
  and `JACI_PLATO_TENANT_ID=acme-hospital`.
- **Scripts** — `publish_packs_to_plato.py` (CLI over `publish_pack`), `export_pack_schemas.py`
  (`dscr_core/schemas/*.json` from the Pydantic models, `--check`).
- **DSCR** — pack gains the `conductor:` block, `metrics.yaml`, `evidence_tools.yaml` +
  `fixtures/`, `mode_tuning/`, `schemas/` (ported from japes' seed copy, `gold_cases_path` kept).
  `prompts/dscr/` removed; `DSCRConductor` reads `mode_tuning/` whole (behaviour unchanged but the
  evidence key, now `policy_assessment`); `DSCRToolRegistry` answers from the fixtures.
  `plato_review.py` adapts `assess` and case-run output to the page's types; the page shows step
  progress, the pack pin, trace and decision ids on the Plato path.
- **Clinical intake** — pack reshaped to Plato's assistant layout (`profile/`, `protocol.yaml`,
  `record:`, `guardrails.yaml`, assistant `manifest.yaml` 0.1.2 with its intake topics in scope).
  `plato_session.py:PlatoIntakeSession` mirrors `IntakeSession` over Plato's recorded sessions;
  `handoff_summary` shared. The live path's broken `jaci.common.llm` import fixed.
- **C&I** — `RB_CI_OVERLAY` and the RB deal rule declare `replaces:` (japes 2.5.6's per-rule
  precedence); the overlay change is byte-identical to `japes-2.5.5`'s.
- **Tests** — `requires_plato` marker in `conftest.py`; `test_plato_glue.py`,
  `test_clinical_intake_plato_session.py` (fake Plato over `httpx.MockTransport`),
  `test_dscr_pack_schemas.py`, `test_dscr_pack_assessment_parity.py`, `test_dscr_plato_adapters.py`,
  `test_clinical_intake_gold.py` (keyless personas), `integration/test_plato_pilots.py` (live).

## Acceptance criteria — verified

- Full suite on the pinned japes `@plato` with a live Plato: 1032 passed, 8 skipped, 1 failed —
  the known live-API `test_anthropic_token_tracking` (fails identically on japes 2.5.1). As this
  machine's `.env` stands (Plato on :8000 answering 503, no Knowledge Hub): 1022 passed, the 10 live
  Plato tests skipped with that reason, the same 1 failure. Earlier, on the `@dev` pin (no Plato
  pieces in japes): 982 passed, 29 skipped (each Plato/SDK-dependent test, with its reason).
- The `/jaci/` → `/plato/` derivation is unit-tested from given page URLs only: `AppTest` has no
  browser, so `st.context.url` is None there (the page correctly reports no Plato). Not yet seen
  behind the real dev-daily gateway.
- A local `packs`-equivalent Plato (port 8765, sqlite + blobs in a scratch dir): both packs publish
  and activate; `dscr_core` reports `unverifiable_rules` (no ontology) as a non-blocking error — the
  seed copy does too. Republishing unchanged → `unchanged`; after a content change → refused, then
  published as 0.1.1 after the bump.
- `assess` over HTTP matches in-process on all 5 gold loans (allowed, violated rules, binding rule
  and cap). The 4 clinical personas on Plato with a live agent: `cooperative` → INTAKE_COMPLETE;
  `redflag`, `downplaying` → ESCALATED on CI-ESC-001; `medication_conflict` → ESCALATED on
  CI-ESC-003; `/record` shows one outcome after review; re-closing returns the same decision.
- A DSCR case run (`double_cap`): completed in ~13s, pinned to `0.1.0-draft` + digest, trace and
  decision persisted, governor not approved over the failed grid, one journal event per step.
- Both pages driven with Streamlit `AppTest` on both backends (ad-hoc, not committed); with no
  Plato the radio is disabled and says why, and both pages run in-process as before.
- Mutation checks: the schema drift test fails on an edited schema; the parity test fails on an
  edited `cltv_pct` formula; the glue test fails if the archive keeps `pack_manifest.yaml`.

## Found along the way, not fixed here (japes — reported, the other session owns the tree)

Written up for the japes side, with repro, code location and suggested fix for each, in japes
`docs/plans/plan_plato_pilot_findings.md`. The list below is the summary.

**Fixed on japes' local `v2.5.6` the same day, and verified from jaci** (not yet in jaci's `@plato`
pin; jaci's workarounds stay until the pin carries them):
- 3 → `025367ef`: in-process SDK conductor on `clean_pass` — investigator 14-25 s per iteration
  (was ~8 ms), 3 iterations with evidence, `failed_modes` empty; jaci's in-process `DSCRConductor`
  now 5 iterations, 6 evidence types.
- 1 → `12a4a356`, 2 → `b7befdea`: on a restarted Plato, a variant of the clinical pack (empty
  in-scope list, a keyword out-of-scope rule with a distinctive decline) published and activated
  *without* a restart — its decline message answered (the new manifest is bound), and the red-flag
  persona still escalated on CI-ESC-001 (an empty in-scope list no longer declines everything).
- 4 → `e1e6b4c2`: a DSCR case run's decision, and the schema model's serialized output with nested
  `condition_id: null`, validate as jaci's `EligibilityRecommendation` without `_without_nulls`.
- 5 → `ac1b2e7d`: Plato now refuses an archive holding both manifests (`ambiguous_manifest`), so
  jaci's archive exclusion is required rather than a workaround; jaci's archive stays publishable.
- The live suite (`tests/integration/test_plato_pilots.py`) passes 10/10 on the fixed code.

1. **Scope gate declines every turn for an assistant with no in-scope topics.**
   `build_from_manifest` hands the scope guardrail `extra["llm_manager"]` unconditionally (its
   docstrings say only when `out_of_scope_check_model` is set), so on a deployment the LLM gate
   runs against `in_scope_action_classes: []` and admits nothing — Plato's bundled `demo_pack`
   included. `test_plato_recorded_session.py` masks it (its scripted LLM always says in-scope).
   Worked around by declaring the intake topics in jaci's manifest.
2. **Activation serves a stale assistant manifest.** Publishing 0.1.1 recomposed while 0.1.0 was
   still pinned; activating 0.1.1 dropped the caches but did not recompose, and `agent_for` reads
   the stored (0.1.0) manifest before composing — so the next turn bound, and cached, the old
   agent. A restart served 0.1.1.
3. **The investigator fails on every OpenAI call when `rich_evidence_requests=True`.**
   `EvidenceRequestSpec.query_params: dict[str, Any]` is not valid under the Agents SDK's strict
   output schema; the mode fails in ~8ms, the loop degrades to one iteration with no evidence, and
   the run still reports `completed`. Since japes 2.3.3; affects jaci's in-process DSCR the same way.
4. **JSON-Schema-derived decision models admit null for non-required fields** (`conditions: null`,
   `conditions[].condition_id: null`). jaci's adapter drops nulls so its defaults apply.
5. **`cltv_pct` rounding differs**: the pack metric rounds to 2 places, jaci's in-process adapter
   does not — equal on the gold loans, but at a cap boundary (80.004%) the two paths would disagree.
   A policy call; not changed.
6. Also: `MANIFEST_NAMES` reads `pack_manifest.yaml` first, so a folder with both manifests
   publishes as a domain pack (handled by the archive builder).

## After the first push attempt

jaci's pre-push review (`scripts/local/pre_push_check.sh`) blocked the push on four defects in this
work, all fixed and tested (`38d3204`, `8da5241`, `7b36bc9`): the ci_spread feedback sink sent no
caller identity or gateway tenant (refused on dev-daily) and, with the localhost fallback, could no
longer fall back to in-process; the DSCR page misreported a failed case run; the publish script
died on the first HTTP error. Also fixed: stale folder names, `.env.example`, a 0% CLTV fallback.
Left for its owner: `ci-spread-core`'s `programs:` map (from the `japes-2.5.5` merge) duplicates
`OVERLAY_MAP` in `ci_spread/policies/registry.py`. The hook's suite gate still fails on the
pre-existing live-API `test_anthropic_token_tracking`.
