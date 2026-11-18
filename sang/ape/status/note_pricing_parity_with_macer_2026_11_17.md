# Pricing parity: japes model cards against macer's table

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Parity check, 2026-11-17. Decides nothing beyond the card fixes listed. No provider calls. macer's table is `src/macer/utils/cost.py` on `origin/cost-breakdown` (6a419482; macer main has no long-context tiers yet), 36 rows. Compared field by field through each side's own pricing lookup (macer's dashed Claude ids map to our dotted ones), standard and `flex_`.

## Result

27 of macer's 36 models agree on every rate, every long-context rate, every threshold and the flex discount. Thresholds: GPT-6/6.1/5.6/5.5/5.4 families above 272K, Gemini 3.1 Pro Preview above 200K, Haiku 5.5 above 100K, all identical. Flex is 0.5 on both sides and applies to both tiers on both sides. Claude and Gemini 4 base prices agree except as below.

## Differences

| Model | Field | macer | ours | Right | Action |
|---|---|---|---|---|---|
| gpt-5.6-sol (and alias gpt-5.6) | long-context cache write | 10.00 | 8.00 (fell back to the tier input rate) | macer: OpenAI pricing page, "Long context 30m write" column, fetched 2026-11-17 | Fixed |
| gpt-5.6-terra | long-context cache write | 5.00 | 4.00 | macer, same page | Fixed |
| gpt-5.6-luna | long-context cache write | 0.50 | 0.40 | macer, same page | Fixed |
| gemini-4-argon | input / output / cached | 4 / 20 / 0.20 | 2 / 10 / 0.10 | Both, by date: the Gemini page gives $2 / $10 / $0.10 through 2026-11-30 and doubles it from 2026-12-01 (our card's provenance note says so; macer's comment says the same and uses the post-promotion price) | Left. Re-price on 2026-12-01; flex follows |

An older test recorded the long-context write rate as "unconfirmed"; it is replaced by one pinned to the page's values.

## Models macer prices that we do not carry

- `gemini-3.8-flash` (macer: single tier, on a 50% promotion; no source of ours read): priced by us at the default (highest) price with a warning.
- `kimi-k3p1-pro`, `deepseek-v4p1-flash-1017` (Fireworks serverless): no cards. The per-token source is the vendor's pricing page (see `note_fireworks_provider_scope.md`); not added, since no consumer calls Fireworks cost helpers through japes yet.
- `gpt-6`: macer aliases it to gpt-6-astra. The OpenAI page lists gpt-6-sol, gpt-6-astra and gpt-6-luna and no plain gpt-6; we carry all three, no alias, so a bare `gpt-6` is priced at the default and warns. Adding the alias is a one-line decision, not made here.

Everything else macer lists, including the Claude ids (fable 5/5.1/5.2, opus 4.6 to 5.5, sonnet 4.6/5/5.5, haiku 5.5) and gpt-5.2/5.4/5.5 pro rows, we carry; we carry 49 models macer does not.

## Before macer can delete its table

Our side now matches macer wherever both have a real source. The remaining gaps are the three unpriced models and the `gpt-6` alias above, and the argon price after 2026-12-01. Also macer's tier-aware `compute_cost*(prompt_tokens=...)` has an equivalent in `ModelPricing.for_prompt_size`; per-request pricing (not totals summed across calls) is the caller's job on both sides.
