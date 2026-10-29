# An aggregate job kind: the governing value across several contributors (sonnet-runtime, 2026-10-28)

Plan note, no build, no spend. Source: sonnet-packs' comparison (K-Studio has jobs that state "the governing cap, minimum
DSCR, minimum FICO and reserves" with the -5 adjustments stacked and flagged conditional; ours leaves Q-07/Q-08 open),
and the kernel-lab note's aggregate-cap example (`min()` over named caps, each cap's value reported).

## 1. What exists
- **Assessment side.** `AssessmentSpec.compose_caps = CapSpec(compare_field, strategy="min")` composes the effective cap on
  one field across every applicable cap rule (matrix cells included): `CapComposition` carries `applicable_rules`, `resolved`
  (rule id to cell), `unresolved`, `ineligible_via`, `binding_cap`, `binding_rule_id`, `passed`. It answers one
  field with `min`; it is not authored by a job and has no stacking of adjustments, minimums (a floor, not a cap) or a
  conditional flag.
- **Job side.** Template `kinds` (`JobKind`: description, `maps_to`, `expects_code`); Acra's are determination, limit,
  verification, condition, judgment. A `limit` job is "a cap, threshold or matrix": one job per tier or one job with the table
  in its checks. Nothing says "this job's answer is the governing value of several others".
- **Code side.** One job to one `check(ctx)` returning True/False/unknown (+ a dict of values); no kind-aware example yet
  (kernel-lab item h).

## 2. The gap, stated
The aggregate jobs answer a different question: not "does the loan pass this cap" but "what is the cap that governs": the
lowest of the applicable caps, the highest of the applicable minimums, the sum of the adjustments (declining market -5),
with a flag when a contributor depends on a reading nobody confirmed (Q-07, Q-08). Our generator writes one threshold or none
for these, and the comparison jobs (loan amount against the governing cap) then have no value to compare to.

## 3. Proposal
**A job kind `aggregate`** (template data, `expects_code: true`, `maps_to: derived_governing_value`) and **a block on the job**:

```yaml
aggregate:
  governs: max_cltv_percent          # the value this job produces (a derived field of the catalog)
  combine: min                       # min | max | sum
  contributors:                      # named, each with where it comes from
    - {name: matrix_cap,        source: matrix, clause: PLAT-7.1}
    - {name: loan_size_cap,     source: matrix, clause: PLAT-2.3}
    - {name: declining_market,  source: adjustment, amount: -5, clause: STD-1.14, applies_when: declining_market}
  open_readings: [Q-07, Q-08]        # contributors whose combination the guideline leaves open
```
- The writer produces the block (it is a typed field of the draft job, like `checks` and `reads`); the template's
  `kinds.aggregate` tells it when. Contributors name the other jobs or matrix cells by mnemonic where they exist (a contributor
  with no job is a gap, reported by the readiness lint as `aggregate_contributor_missing`).
- **Code:** the generator gets the aggregate example (kernel-lab item 4): constants for the adjustments with their clause id,
  `min`/`max`/sum over the contributors that apply, the dict reporting each contributor's value and which governs. A missing
  contributor value is unknown, never skipped (a skipped cap would raise the governing value).
- **Assessment:** the job's `governs` field becomes a derived field (`derivations`), so `compose_caps` and the comparison jobs
  read one value instead of re-deriving it; `CapComposition` stays the engine for the matrix contributors.
- **Conditional flag:** `open_readings` non-empty makes the job's verdict at best CONDITIONAL with the readings named as
  open conditions (the existing condition ids), until a pack-data decision (`readings:` resolved by the user or Acra)
  empties it. This is how Q-07/Q-08 stay visible instead of silently chosen.

## 4. Where it lands, and size
`pipelines/policy/jtbd.py` (the `aggregate` field on the draft job, template `kinds` entry), `JobKind` gains nothing (the block is
the job's), `pipelines/policy/code.py` + `prompts/files/policy_code/job_prompt.md` (the example slot), `pack/lint.py` or
`jtbdset_lint` (contributors resolve, readings named), `pipelines/policy/jtbdset.py` (the block exported to `domain_extensions`
and, as text, in the job's requirement), `pack/ledger.py` (kind `aggregate` expects code: the gap by kind already works).
Size: one to two days, most of it the writer's prompt and a measuring run; part of it (lint, derivation) is no-spend.

## 5. Not decided here
- Whether `combine` needs more than min/max/sum (a clamp of a sum, a lookup after the min): wait for a second guideline.
- Who owns resolving an open reading: pack data written by the user; the SDK only carries it.
- The kernel-lab example for this kind should refer to the readings, not choose one (their note's caveat).
