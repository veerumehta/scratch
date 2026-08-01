# plan_JAPES_CONVERSATION_GAP_CLOSURE.md

**Status:** in progress — closing the conversation-compaction quality gap vs juno by lifting juno's
production logic behind the japes interfaces (1.9.4/1.9.5). Source attributions in code cite the juno
file. This is a patch staged for Huaxing to review/agree; proceed if the live conversation slips.

## The three gaps (japes has the architecture; juno has the internals)

| Gap | juno source | japes target (interface that exists) | This patch |
|---|---|---|---|
| **Item fidelity** — mask large `function_call_output`, drop non-SDK shapes, preserve `function_call`↔output / reasoning pairing so the Responses API never 400s | `app/copilot/session.py` (`_mask_function_call_output`, `get_items` pass 1/2) | `binding.py` `_to_responses_items` / `_from_responses_items` (already the seam) | **LIFTED** |
| **Token-authoritative compaction** — fire on real rendered input-tokens (char/4 only as turn-1 fallback); summarize via the SDK's Responses-aware compaction | `app/copilot/compaction.py` (`_estimate_tokens`, `make_token_compaction_trigger`, `build_compaction_session`) | a `responses` path on `OpenAIAgentsBinding` wrapping `agents.memory.OpenAIResponsesCompactionSession` | **LIFTED + WIRED** |
| **Defense-in-depth** — between-turn target + mid-flow overflow guard + overflow-retry | `compaction.py` `context_management_setting` + the run loop | `_respond_agentic` run options + retry | **deferred** (specced below) |

## Lifted in this patch
- **Item fidelity** → `binding.py`: `_mask_function_call_output` + `_to_responses_items` (the get_items
  masking pass) lifted near-verbatim from `app/copilot/session.py`, source-attributed. Generic
  Responses-API correctness only; juno-app-specific bits (interaction_data/XML stripping,
  attachment sanitization) are left as no-ops/hooks — they're juno UI conventions, not SDK contract.
- **Token trigger helpers** → `responses_compaction.py`: `estimate_tokens` + `token_compaction_trigger`
  lifted from `app/copilot/compaction.py` (source-attributed), ready to feed the SDK compaction session.

## Wiring done (was "review decisions"; resolved with defaults — still confirm with Huaxing)
1. **Authoritative token source — RESOLVED (a).** Inject `token_source: () -> int|None` into the binding
   (`ResponsesCompaction.token_source`); japes stays cost-tracker-agnostic, char/4 fallback identical to
   juno. A service with a usage tracker injects it; default None.
2. **Client/model into the binding — RESOLVED.** `_respond_agentic` builds `ResponsesCompaction(client=
   self._agents.openai.client, model=spec.model or default, token_threshold=spec.compaction.token_threshold)`
   when `spec.compaction.strategy=="responses"`, and hands it to `AES.bind_conversation(..., compaction=)`.
   `OpenAIAgentsBinding.session()` wraps the store-backed session in `OpenAIResponsesCompactionSession`.
3. **Where compaction runs — RESOLVED for between-turn.** Binding wraps the base session (Runner path).
   `build_conversation_store` leaves the store plain for `"responses"` (no double-compaction); single-shot
   path gets plain session memory under `"responses"`.

## Defense-in-depth — DONE (with one version caveat)
4. **Mid-flow guard + overflow-retry — LIFTED + WIRED.**
   - Tier 1 (mid-flow): `context_management_setting` → `ModelSettings(context_management=…)` on the
     agent, **version-gated** via `model_settings_with_context_management` — the installed agents SDK's
     `ModelSettings` lacks `context_management` (juno pins a newer `^0.17.0`), so japes applies it only
     when supported and degrades gracefully otherwise (tiers 2/between-turn still apply). To enable it
     here, bump japes's agents SDK to juno's line.
   - Tier 2 (overflow-retry): `is_context_window_error` + `run_with_context_window_fallback` lifted
     from juno `app/copilot/skill_service.py` — on a context-window 400, force one compaction
     (`session.run_compaction({"force": True})`) and retry once; re-raise otherwise.
   - `CompactionPolicy.mid_flow_threshold` (default 900K) added alongside `token_threshold` (200K).

## Still open
- Confirm thresholds (200K between-turn / 900K mid-flow / 272K cliff) with Huaxing.
- Confirm the token_source contract (who injects authoritative tokens in a deployed japes service).
- Bump japes openai-agents to juno's line so the mid-flow tier is active (currently gated off).

## Acceptance
- Masking: large `function_call_output` → placeholder (size + tool name; error suffix); pairing/ids kept;
  non-SDK shapes dropped; small outputs verbatim; non-string outputs JSON-normalized. (unit tests)
- Token trigger: ≥ threshold on authoritative tokens; char/4 fallback when none. (unit tests)
- No japes-only regression; the binding still conforms to `agents.memory.Session`.
