# Plato pilot findings: bugs jaci hit running DSCR and clinical intake on Plato

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: open, 2026-09-28. Found by the jaci session building the consumer half of
`plan_plato_domain_pack_runtime.md`, against japes `v2.5.6` (`1ac629ae`, re-checked at `ab080492`:
every site below is unchanged) and a live local Plato on the default wiring at `JAPES_ENVIRONMENT=local`.
jaci's record: `jaci/docs/status/done_JACI_PLATO_PILOTS.md`. None of these are fixed in japes; where
jaci worked around one, the workaround is named so it can be removed once the fix lands.

**Resolved on `v2.5.6`, 2026-09-29** (reviewed clean, `99a0ef16..a58ecd1f`): 3 `025367ef`
(investigator output relaxed like the verifier/narrator; `CaseResult.failed_modes`, `failed` /
`degraded`); 1 `12a4a356` (scope LLM only with `out_of_scope_check_model`); 2 `b7befdea`
(`activate` recomposes); 4 `e1e6b4c2` (`PackModel`: nulls only where the schema allows); 5
`ac1b2e7d` (`ambiguous_manifest` publish finding). jaci can drop the workarounds for 1, 4 and 5.
Still open: item 1's design question (the scope gate runs before pack guardrails), and item 6
(`cltv_pct` rounding is the DSCR corpus owner's decision).

Ordered by how much they hurt a real deployment.

## 1. The scope gate declines every turn for an assistant with no in-scope topics

**Where.** `jazzx_sdk/manifest/spec_binding.py:254` —
`_ensure_scope_guardrail_registered(manifest, guardrails, llm=extra.get("llm_manager"))`.

**What.** The LLM is handed to the scope guardrail unconditionally, but the docstrings of
`_ensure_scope_guardrail_registered` (≈:171) and `build_from_manifest` (≈:240) say it is forwarded
only "when `manifest.out_of_scope_check_model` is set". Plato's wiring always supplies
`llm_manager` in `agent_extra`, so `build_scope_guardrail` (`agents/interactive/scope.py:75`) takes
its LLM path, which classifies each turn against `in_scope_action_classes` as the list of allowed
topics. With that list empty, nothing is in scope.

**Effect.** Every turn answers "I can only help with topics within my scope." — **including the
bundled `plato/data/demo_pack`** (`in_scope_action_classes: []`, `out_of_scope_check_model: null`)
on any replica with an LLM key. Seen live: jaci's clinical pack, same manifest shape, declined the
identity turn and the chest-pain turn alike.

**Why the suite misses it.** `tests/test_plato_recorded_session.py:45` `_reply` answers every
scope-gate prompt `{"in_scope": true}`, so the gate that production runs never refuses there.

**Fix.** Pass `llm=` only when `manifest.out_of_scope_check_model` is set, as the docstrings say
(the keyword path against `out_of_scope_action_classes` then applies otherwise). Add a test whose
scripted LLM *refuses* scope, over a manifest with empty `in_scope_action_classes`.

**Related, a design question.** The scope gate runs before the pack's own input guardrails. A red
flag ("my chest hurts") that an LLM scope check misjudges as out of scope is declined with the
generic message and never reaches `CI-ESC-*`, so no escalation is recorded. Consider running
pack-declared guardrails ahead of the scope gate.

**jaci workaround.** `config/packs/clinical-intake-core/manifest.yaml` lists its intake topics in
`in_scope_action_classes`, red-flag disclosures included.

## 2. Activating a new assistant-pack version serves the old manifest until restart

**Where.** `plato/wiring/default.py` `activate` (≈:749-806) vs `forget_packs` (≈:851).

**What.** Repro:
1. publish + activate `clinical-intake-core 0.1.0`, chat once;
2. publish `0.1.1` — `_publish_archive` calls `_forget(tenant)` → `forget_packs(tenant)`, which
   recomposes *eagerly*, but under the pin that still says 0.1.0, so the manifest store is
   rewritten with 0.1.0's manifest;
3. activate `0.1.1` — the pin moves and `_tenant_registries` / `runtime.invalidate_all()` are
   dropped, **but nothing recomposes**;
4. chat — `AssistantRuntime.agent_for` reads the stored manifest (`assistant_runtime.py:131`)
   *before* `_resolve_registries` recomposes, so it binds 0.1.0's manifest, and caches that agent.

`forget_packs`' own docstring states the ordering hazard ("Eager, not lazy: `agent_for` resolves
the manifest before the registries…"); `activate` does not apply the same remedy.

**Effect.** The activation reports success; the replica keeps serving the previous version's
manifest (seen: 0.1.1's `in_scope_action_classes` had no effect) until a restart.

**Fix.** After moving the pin in `activate`, recompose eagerly — `await forget_packs(tenant)` (or
`registries_for(tenant)` after the invalidation), so the manifest store holds the activated
version's manifest before the next `agent_for`. Test: activate a second version whose manifest
differs, then assert the bound agent reflects it without a restart.

## 3. The investigator fails every OpenAI call when `rich_evidence_requests=True`, silently

**Where.** `jazzx_sdk/modes/schemas.py:288` —
`EvidenceRequestSpec.query_params: dict[str, Any]`, inside `RichHypothesisUpdate`.

**What.** A free-form object is not valid under the OpenAI Agents SDK's strict output schema:
```python
from agents import AgentOutputSchema
from jazzx_sdk.modes.schemas import HypothesisUpdate, RichHypothesisUpdate
AgentOutputSchema(HypothesisUpdate[X])       # ok
AgentOutputSchema(RichHypothesisUpdate[X])   # UserError: additionalProperties should not be set
```
Independent of the hypothesis type (reproduced with jaci's Pydantic model and with the one
`pack/schemas.py` builds). Present since `rich_evidence_requests` landed (2.3.3).

**Effect.** `InvestigatorMode` fails in ~8 ms on every call; the loop proceeds with no hypotheses
and no evidence requests, the verifier has nothing, and the run **still reports `completed`** with a
decision. Every DSCR case run on Plato (`investigation_loop` sets `rich_evidence_requests=True`) is
affected, and so is jaci's in-process `DSCRConductor`, which sets the same flag.

**Fix, two parts.**
- Make the type strict-compatible: e.g. `query_params: list[QueryParam]` with
  `QueryParam(key: str, value: str)`, converted to a dict for `fulfill_evidence`; or build the
  output with `AgentOutputSchema(..., strict_json_schema=False)` for this type.
- Don't let a failed mode pass as success: `run_investigation_case` already records
  `on_mode_result(name, success)` in `calls` — surface it on `CaseResult` (e.g. `failed_modes`) and
  mark the run degraded/failed when the investigator never succeeded.

## 4. JSON-Schema-derived models admit null for every non-required field

**Where.** `jazzx_sdk/pack/schemas.py:69` — a non-required property becomes
`Optional[annotation]` with its default.

**What.** Under strict structured output every field is required and the model fills non-required
ones with `null`, so a case run's decision carries `conditions: null` and
`conditions[].condition_id: null` where the source schema's default was `[]` / a generated id.

**Effect.** A consumer validating the decision against the pack's original model (jaci's
`EligibilityRecommendation`) fails.

**Fix.** Keep defaulted fields non-nullable (`annotation` with its default) unless the schema says
`null` is allowed (`anyOf` with `{"type": "null"}`), or drop `None`s so defaults apply when
validating the model's output.

**jaci workaround.** `scenarios/dscr/plato_review.py:_without_nulls`.

## 5. `MANIFEST_NAMES` prefers `pack_manifest.yaml`, so a folder with both manifests is not an assistant

**Where.** `jazzx_sdk/pack/store.py:89` — `("pack_manifest.yaml", "manifest.yaml")`.

**What.** An assistant pack that also carries domain assets and a domain manifest (jaci's
clinical-intake: policies, protocol, profile) publishes as a *domain* pack, and is never served as
an assistant; nothing warns.

**Fix.** Either prefer `manifest.yaml` when it carries `assistant_id`, or have `/packs/check` report
an archive holding both as a finding.

**jaci workaround.** `scripts/publish_packs_to_plato.py` leaves `pack_manifest.yaml` out of an
assistant folder's archive.

## 6. Lower priority

- **`cltv_pct` rounding.** The seed `dscr_core/metrics.yaml:13` declares `rounding_places: 2`; jaci's
  in-process derivation does not round. Equal on the gold loans, but at a cap boundary (80.004%
  against an 80% cap) Plato allows and in-process denies. A policy decision — round before
  comparing to a cap or not — for whoever owns the DSCR corpus.
- **`dscr_core` fails `/packs/check` as `ok`** (seed and jaci's copy alike): `no_ontology` warning plus
  an `unverifiable_rules` error for its 42 rules. Non-blocking, so it publishes — just noting that
  the reference domain pack does not pass its own check cleanly.
