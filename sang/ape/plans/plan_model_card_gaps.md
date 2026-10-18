# Model card gaps (sonnet-runtime, 2026-10-18)

Checked `llm/model_data.json`, `llm/cost.py`, `llm/model_identity.py`.
1. Mythos rows: none exist (`claude-mythos-5`, `claude-mythos-5-1`). Plan: add both rows from the provider's published
   pricing, verified date and UTC timestamp per the card convention; the user supplies or approves the figures first.
2. One-hour cache write rate: not covered. The card has `cache_creation` (one rate); there is no 1h variant. Plan: an
   optional `cache_creation_1h` on pricing (None: 2.0x input, the provider's published multiple), a `cache_ttl` on the
   usage row where the provider reports it, and cost reads it; without a reported TTL, today's rate.
3. Unknown-model fallback: not covered as asked. Unknown models cost at `DEFAULT_PRICING` (21/168 USD per M, "most
   expensive card", warned once per model) and the start-up check can refuse. Plan: an optional deployment fallback
   (`JAPES_FALLBACK_PRICING` or a named card id) read before `DEFAULT_PRICING`; the cost stays flagged
   `cost_is_upper_bound`/unpriced either way.
4. Id normalisation: partly. A trailing date is stripped (`claude-sonnet-4-5-20250929` becomes `claude-sonnet-4.5`) and
   dashes become dots for the 4.x/5.x ids; `-latest`, `[1m]` and `-0` suffixes are not (`claude-opus-5-5-latest` stays
   `claude-opus-5.5-latest`, unpriced). Plan: strip `-latest`, a `[1m]`-style context suffix and `-0`
   in `_normalize_claude_name`, test each id. Verified: `claude-3-5-haiku-20241022` is unpriced (`is_priced` False) because the dashed 3-x form does not reach the dotted card `claude-3.5-haiku`, so the 3.x ids need the dash-to-dot step too; `claude-opus-4-0`, `-latest` and `[1m]` ids are also unpriced today.
5. `claude-3.5-haiku`: the row exists and is already `deprecated: true`. It carries no successor field: add an optional
   `replaced_by` (here `claude-haiku-5.5`) read by the deprecation warning and the start-up check; do not add pricing rows.
