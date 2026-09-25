# jaci on Plato: DSCR and clinical intake as the first two scenarios

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: plan, 2026-09-24. Nothing built. Written against jaci `0a3e7ab` on `dev` (japes pinned
`@dev`, 2.5.3) and japes `5534f5e` on `v2.5.4` (Plato 0.1.6).

Companion (platform side): japes `docs/plans/plan_plato_domain_pack_runtime.md` — referenced below as
**japes §N**. This file is the consumer half only: what jaci changes so that DSCR and clinical intake
can run on Plato instead of calling `jazzx_sdk` in-process. Every platform capability they need is
scoped there, per the jaci/japes boundary (general mechanism → japes; demo convenience → jaci).

## 1. Scope and end state

Two scenarios, each gaining a **"Run on: in-process | Plato"** switch. The in-process path stays:
it is the offline, keyless demo path and the parity reference.

| Scenario | On Plato it becomes | Plato surface used |
|---|---|---|
| **DSCR** | a pack-declared case run: deterministic assessment + investigation loop, streamed | `POST /packs/dscr-core/assess`, `POST /packs/dscr-core/runs`, `GET /runs/{id}/stream` (japes §4.5) |
| **Clinical intake** | an assistant pack with pack-declared guardrails, a session recorder and a completeness contract | assistants sessions / chat / close / outcome / record (japes §5.4) |

`config/packs/` stays the authoring source. jaci publishes into Plato. The copies bundled under
Plato's `seed_packs` are for seeding only, not production, and are out of scope.

## 2. What jaci does today (the parts that move)

- **DSCR**:
  - `scenarios/dscr/conductor.py` runs `run_eligibility_assessment` (`DefaultPolicyExpert` + jaci
    `compose_caps`) and then `investigation_loop` with five modes.
  - Prompts come from `prompts/dscr/*.md` via a custom `_load_dscr_prompt`, not the pack.
  - The schemas are Pydantic in `schemas/dscr_schemas.py`; the tools are a two-tool mock
    `DSCRToolRegistry`.
  - The pack (`config/packs/dscr_core/`) declares policies + profiles only. It has no `conductor:`
    block.
- **Clinical intake**:
  - `scenarios/clinical_intake/session.py` wraps `build_interactive_agent` over
    `config/packs/clinical-intake-core/agent/`.
  - `guardrails.py` builds keyword detectors from `policies/core.yaml`, and `IntakeSession` writes
    the canonical chain.
  - The demo is keyless (`ScriptedLLM`, skills dropped).
  - The live path is **broken**: `session.py:227` imports `jaci.common.llm`, which does not exist.

## 3. Work items

### J0 — Prerequisites (no japes dependency; do first)

| # | Work | Verify |
|---|---|---|
| J0.1 | Fix clinical intake's live LLM import (`session.py:227`) to `jaci.capabilities.commercial_lending._llm.default_llm`, or to `jazzx_sdk.llm.llm_from_env(prefix="JACI")` directly. | A unit test builds a live-path `IntakeSession` with the LLM factory patched, so no provider call is made. |
| J0.2 | Route DSCR's prompts through the pack: move `prompts/dscr/*.md` → `config/packs/dscr_core/mode_tuning/` and drop `_load_dscr_prompt` for `compose_mode_prompt`. **Behaviour risk**: today these are whole prompts; after the move they sit on top of the SDK base prompt. Either trim them to deltas or keep them whole behind a `replace_base: true` flag if the SDK offers one. Check with `tests/scenarios/dscr` and a gold-case run before and after. | Existing DSCR tests pass. A live run on the 5 gold cases gives the same decisions as before the move (`requires_api_key`). |
| J0.3 | Two things the japes work can't use if they stay jaci-only. First, add `metrics.yaml` with `cltv_pct` as a `MetricDefinition` (today it's derived in `eligibility/context.py`). Second, make `build_eligibility_context` read that definition, so both paths derive `cltv_pct` from one place. | `test_dscr_eligibility.py` passes unchanged. |
| J0.4 | Add `schemas/` to `dscr_core`: `loan_application.json`, `hypothesis.json`, `eligibility_recommendation.json`. Generate them from the Pydantic models with `scripts/export_pack_schemas.py` (`model_json_schema()`), so Pydantic remains the source of truth in jaci. Add a drift test that regenerates them and diffs. | The drift test passes. |
| J0.5 | Add `evidence_tools.yaml` + `fixtures/` to `dscr_core`: `credit_report` and `appraisal` as `fixture` sources holding today's mock payloads. `DSCRToolRegistry` reads the same fixtures, so there's one copy of the mock data. | DSCR conductor tests pass. |
| J0.6 | Clinical intake pack in Plato's assistant shape: `agent/` → `profile/`, plus a root `manifest.yaml` (`assistant_id: clinical-intake-core`, `allowed_skills` ⊇ the profile's skills, `domain_manifest: pack_manifest.yaml`, japes D3). Update `pack_manifest.yaml`'s `agent:` key and the two `from_dir(... / "agent")` call sites (`session.py:218`, `ui/demo_page.py:61`). | The clinical-intake eval and demo still run in-process. |
| J0.7 | `guardrails.yaml` in the clinical pack, declaring `clinical_governor_in` / `clinical_governor_out` as `policy_keywords` over `CI_ESC_POLICY` / `CI_SCOPE_POLICY` (japes §5.2.1). jaci's `build_guardrails` keeps working until the SDK kind lands, then is deleted. | — |

### J1 — Client and configuration (needs japes Phase 0: `PlatoClient`)

| # | Work |
|---|---|
| J1.1 | Settings: `JACI_PLATO_URL`, `JACI_PLATO_TENANT`, and optionally `JACI_PLATO_TOKEN`, added to `settings_fields.py` so they show on the Settings page. Nothing else reads Plato configuration. |
| J1.2 | `scenarios/shared/plato.py`: `plato_client()` (a cached `PlatoClient` built from settings), `plato_available()` (a cheap `/health` check), and the shared "Run on" radio. The radio is disabled, with the reason shown, when Plato is unreachable. |
| J1.3 | `scripts/publish_packs_to_plato.py <pack_dir>...`:<br>1. Zip the pack (skipping dotfiles and `.DS_Store`).<br>2. `POST /packs/check`, and stop on errors.<br>3. Publish, then activate.<br>4. Skip the upload when the archive digest matches the active version.<br>Since a pack version is immutable (a republish answers 409), a changed pack needs a new version: the script refuses and asks for a bump rather than auto-bumping `pack_version`. |

### J2 — Clinical intake on Plato (needs japes Phase 1)

| # | Work |
|---|---|
| J2.1 | `PlatoIntakeSession`, the same interface as `IntakeSession` (`turn`, `completeness`, `close`, `record_nurse_review`) over HTTP:<br>- create a session;<br>- chat with `scope={patient_id, encounter_id, section}`;<br>- `/close`, `/outcome` and `/record`.<br>The demo page picks the class from the "Run on" switch and is otherwise unchanged. |
| J2.2 | The page's canonical column reads from `/record` on the Plato path. The escalation banner uses `block_rule_id` instead of parsing `[CI-ESC-…]` out of the reason string. |
| J2.3 | Persona replay: the gold personas' patient turns and sections drive both paths. Their `agent_replies` only apply in-process (scripted). On Plato the agent is live, so each turn bills the provider; the page says so. |

### J3 — DSCR on Plato (needs japes Phase 2)

| # | Work |
|---|---|
| J3.1 | Add the `conductor:` block to `dscr_core/pack_manifest.yaml` (japes §4.3). The in-process `DSCRConductor` keeps its own wiring. Collapsing it onto the SDK kind is a follow-up once parity holds, and is not required for the pilot. |
| J3.2 | Deterministic section. On the Plato path the page calls `POST /packs/dscr-core/assess` and renders the same `EligibilityAssessment` view. Add an adapter from the SDK's `PolicyAssessment` to the page's shape. |
| J3.3 | Run section:<br>- `POST /packs/dscr-core/runs`, then consume `/runs/{id}/stream`, showing per-step progress as events arrive;<br>- when the run finishes, `GET /runs/{id}` returns the output, which an adapter maps into today's `ReviewFile` rendering;<br>- a Stop button calls `/runs/{id}/stop`. |
| J3.4 | Show the run's pack pin (id, version, digest) and the Trace's per-mode steps. Today's in-process run has no granular trace, so this is a visible gain from the Plato path. |

### J4 — Tests

| # | Work |
|---|---|
| J4.1 | Unit tests for `PlatoIntakeSession`, the DSCR adapters and the publish script, against a mocked transport (`httpx.MockTransport`). They need no Plato and no key. |
| J4.2 | A `requires_plato` marker, auto-skipped in `tests/conftest.py` when `JACI_PLATO_URL` is unset or unreachable. This is the same pattern as `requires_api_key`: no decorator to remove, just point it at a Plato. |
| J4.3 | Parity (`requires_plato`): for each of the 5 `tests/eval/gold_cases/dscr` cases, `assess` on Plato must match in-process `run_eligibility_assessment` on `allowed`, the violated rule ids and the binding cap. For each of the 4 clinical personas, the Plato session must block on the same `CI-ESC-*` clause (or not block) and close with the same decision. |
| J4.4 | End-to-end (`requires_plato` + `requires_api_key`): one DSCR run and one clinical session against a local-profile Plato. |

### J5 — Docs

`docs/status/CHANGELOG.md` entries per landed item; `docs/status/done_JACI_PLATO_PILOTS.md` at the
end; CLAUDE.md "Recent Session Status"; a short "Running against Plato" section in `APP_README.md`
(start it with `PLATO_PROFILE=local ./scripts/plato-local.sh start` in `../japes`, then run the publish
script).

## 4. Order and dependencies

```
J0 (now, jaci only) ──► J1 ◄── japes Phase 0
                         ├─► J2 ◄── japes Phase 1   (clinical intake first: smaller, no migration)
                         └─► J3 ◄── japes Phase 2
J4 alongside each; J5 at the end
```

J0 is valuable even if Plato slipped: it moves DSCR's prompts, metrics, schemas and fixtures into
the pack, where the in-process path also reads them.

## 5. Risks

- **Prompt composition change (J0.2).** DSCR's prompts become deltas over the SDK base. This is the
  April 2026 AML lesson: measure before and after, and don't reason about it.
- **Live cost on the Plato clinical path.** Plato's agentic path builds an OpenAI agent directly
  (per `plato/guide.md`), so there's no keyless mode there. Keep the in-process path for keyless
  demos.
- **japes decisions still open** (D1–D8): the manifest keys in J0.6/J3.1 are illustrative until
  japes Phases 1–2 are reviewed. Expect a rename pass.
- **Local Plato profile.** Your laptop Plato currently runs `deployed`/`dev-daily`, which refuses
  publishes and 503s chat. The pilots assume the local profile after japes §3 0.3.

## 6. Found along the way (not in scope, recorded)

- `src/jaci/japes_handler.py:190` calls an undefined `Conductor(...)`, so the queue/server
  `investigate` path raises NameError.
- `ci-spread-core`, `cl_of_core` and `cl_sp_core` bind
  `jaci.scenarios.ci_spread.experts.policy.CIPolicyExpert`, which doesn't exist. The SDK never
  resolves `experts.*.class`, so nothing fails today, but Plato's check (japes §2) will refuse these
  packs.
- `pyproject.toml [project.scripts]` declares `jaci.cli:main`; `src/jaci/cli.py` does not exist.
