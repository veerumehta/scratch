# plan_JAPES_POLICY_IR_AUTHORING_DEFECTS

**Repo:** japes · **Baseline:** 2.4.1 (`577c28d`) plus the uncommitted `MatrixCondition` change set
**Origin:** surfaced by authoring the Acra Lending DSCR eligibility grid (99 cells, 19 rules) against the IR — the first real consumer of `MatrixCondition`. Both defects were hit within the first twenty minutes of authoring, by a non-SDK author doing the natural thing.
**Shape:** two small fail-late→fail-early fixes (P1, P2), then one design decision that gates full program encoding (P3).

Both defects share a signature: **the model validates, the evaluator raises.** A pack author writes plausible YAML, pydantic accepts it, and the failure arrives at evaluation time on a specific loan — which in a governance artifact means it may arrive in production on an unusual file rather than in review. The fixes are small; the reason to do them is that this class of failure is exactly what a policy IR exists to prevent.

---

## P1 — `RatioCondition.direction` accepts operators the evaluator cannot execute

**Symptom.** Authoring the Acra "DSCR below 1.0" applicability probe:

```yaml
condition:
  kind: ratio
  ratio_name: DSCR
  numerator: gross_rental_income
  denominator: pitia
  threshold: profile:dscr_min_no_ratio_floor
  direction: "<"
```

validates cleanly, then raises on first evaluation:

```
ValueError: '<' is not a valid RatioDirection
  condition_evaluator.py:234  direction=RatioDirection(condition.direction.value)
```

**Cause.** `RatioCondition.direction` is typed `ComparisonOperator` — nine values (`>`, `>=`, `<`, `<=`, `==`, `!=`, `in`, `not_in`, `contains`). `RatioDirection` (`tools/ratio_evaluator.py:20-23`) has two: `AT_LEAST ">="`, `AT_MOST "<="`. Seven of the nine authorable values are unreachable, and six of them are silently wrong rather than obviously wrong (`<` is the natural way to write a floor breach).

**Fix.** Constrain at the model boundary so the error lands at authoring time and names the two legal values. Preferred: narrow the field's type to a two-member enum or `Literal[">=", "<="]`; acceptable alternative: a pydantic field validator on `RatioCondition` that rejects anything outside `{GTE, LTE}` with a message naming both. Either way the error must mention that a strict comparison should be expressed as its non-strict complement against an adjusted profile threshold, because that is what an author will need to do next.

Do **not** widen `RatioDirection` to cover strict comparisons unless `evaluate_ratio`'s margin/warning-buffer semantics are worked through — `RatioResult` reports margin-to-threshold, and a strict boundary makes "margin zero" mean pass in one direction and fail in the other. Narrowing is the cheap correct move.

**Tests** (`tests/test_condition_evaluator.py`): authoring `direction: "<"` raises `ValidationError`, not `ValueError`, and the message names `>=` / `<=`; `>=` and `<=` continue to evaluate unchanged (existing cases must stay green).

**Blast radius.** Grep for `RatioCondition(` and `kind: ratio` across japes and jaci before landing — any existing rule authored with a non-`>=`/`<=` direction is already broken at runtime, so this change surfaces latent breakage rather than causing it. That surfacing is the point; expect to fix a call site or two.

---

## P2 — `Expression` float-casts the actual value for every non-membership operator

**Symptom.** The natural way to write a borrower-type overlay:

```yaml
applicability: {kind: expression, field: citizenship_type, operator: "==", value: itin}
```

raises:

```
ValueError: could not convert string to float: 'itin'
  condition_evaluator.py:129
  satisfied = self._OPS.get(condition.operator, lambda a, v: False)(float(actual), condition.value)
```

**Cause.** `float(actual)` is applied before operator dispatch. The `MatrixCondition` change set correctly exempted the new membership operators (`_MEMBERSHIP_OPS`, `:108-112`) from the cast — equality was not exempted, so string equality is unusable while string membership works. That asymmetry is itself a tell: authors will write `==` first.

**Fix.** Cast only for ordering operators (`>`, `>=`, `<`, `<=`). Compare `==` / `!=` on raw values. Two decisions to make explicitly rather than by accident:

1. **Numeric equality across types.** After the change, `"5" == 5` is False where it may previously have been True via the cast. That is the correct strictness for a policy IR, but it is a behaviour change — state it in the commit message and check existing rules for numeric `==` authored against string-typed context fields.
2. **Non-numeric actual under an ordering operator.** Today `float("itin") > 5` raises `ValueError`. It should return **INDETERMINATE** with a message naming the field and its actual type — consistent with the evaluator's own stated rule that missing or unresolvable data yields INDETERMINATE and never an exception. A type mismatch is unresolvable data, not an authoring crash.

**Tests:** string `==` / `!=` evaluate correctly on non-numeric fields; boolean fields keep working (`escrow_waiver_requested == true` — currently passes only because `float(True)` is `1.0`, so this needs an explicit case); ordering operator against a non-numeric actual returns INDETERMINATE, not a raise; existing numeric cases unchanged.

**Why it matters beyond ergonomics.** With P2 unfixed, every string overlay in a pack has to be authored as a single-element `in` list. Four rules in the Acra slice carry that workaround. It reads as a deliberate set-membership rule to a governance reviewer when it is nothing of the kind — the artifact stops saying what it means, which is the one property a reviewed policy corpus cannot lose.

---

## P3 — Composite applicability (`AllOf` / `AnyOf`) — decision, then build

**This is the item that gates full encoding of the Acra program**, and it needs a decision before it needs code.

`Rule.applicability` is a single `Condition`. Several real rules are natively conjunctive:

- "warrantable condo **outside Florida**" in the >80% LTV eligible-property-type list;
- the **−5% CLTV Florida modifier** on non-warrantable condo and condotel/PUDtel;
- Illinois prepayment buyout: *residential 1-4* **and** *entity or individual* **and** *amount ≤ $250,000*; plus a second Illinois rule on *amount > $250,000* **and** *rate > 8%*;
- Pennsylvania: *individual* **and** *residential 1-2* **and** *< $319,777*.

Thirteen states carry prepayment rules and several are conjunctive, so this is not one awkward rule — it is a whole rule family that currently cannot be authored honestly.

**Three options.**

| | Approach | Cost | Consequence |
|---|---|---|---|
| **A** | New `AllOf` / `AnyOf` combinator kind holding `conditions: list[Condition]` | One kind + one evaluator + union tag + sniff branch | Recursive evaluation; needs a depth cap and a decision on how child `RuleOutcome.inputs` merge into the parent trace |
| **B** | Fold the extra predicate into the matrix as another axis | No SDK change | `property_state` as an axis multiplies cells by ~50; the grid stops being reviewable against the source PDF |
| **C** | Use `DslExpression` for applicability | No SDK change | Buries eligibility predicates in formula strings — defeats the reviewability that `RatioCondition`'s "threshold must be `profile:`" rule exists to protect |

**Recommend A.** The registry is genuinely open (`register_condition_evaluator`, last-registration-wins, unknown kind raises a deliberate `KeyError`), the union is callable-discriminated with a shape sniffer, and `MatrixCondition` just proved the extension path works end to end. The real design work is not the evaluator — it is **trace composition**: a combinator's `RuleOutcome.inputs` must let an underwriter see *which* limb failed, or the audit trail degrades to "the composite was violated," which is worse than the workaround it replaces. Decide that before writing the evaluator.

Also settle **verdict algebra** up front, in the spec and in tests: for `AllOf`, one VIOLATED limb ⇒ VIOLATED; otherwise any INDETERMINATE ⇒ INDETERMINATE; all SATISFIED ⇒ SATISFIED. For `AnyOf`, one SATISFIED ⇒ SATISFIED; otherwise any INDETERMINATE ⇒ INDETERMINATE. The INDETERMINATE-dominates-over-SATISFIED rule for `AllOf` is the safe direction and should be a named test, not an emergent property.

`evidence_contract()` must return the union of child contracts, or the combinator silently opts out of cross-policy field-claiming precedence (`experts/policy/default.py:393`).

---

## P4 — Two smaller items, batch with the above if convenient

**P4a — Profile-referenced literals in `Expression`.** `RatioCondition.threshold` must be `profile:<key>` so thresholds stay reviewable in one place; `Expression.value` takes bare literals. Result: in the Acra slice, `dscr_min_high_ltv` lives in the profile while `reserves_months >= 6` and `loan_amount <= 3000000` are hardcoded in the policy YAML. The scalars were duplicated into `profile.custom` for review, but nothing enforces agreement. Either accept `profile:<key>` in `Expression.value`, or ship a lint that fails when a policy literal has a diverging `custom` twin. **The lint is the cheaper half and catches the actual failure mode** (silent drift after a program update).

**P4b — Render new Condition kinds in violation messages.** `experts/policy/default.py:33-50` (`_condition_label` / `_describe_condition`) and `policy_registry.py:33-56` (`_machine_readable_threshold`) fall back to a bare `condition.kind` string for unrecognised kinds. `matrix` hits that path today, so an Acra grid violation currently renders as `"matrix"` rather than "CLTV 85.01% exceeds the 85% maximum for $900,000 / FICO 740 / purchase." Cosmetic in the SDK; **load-bearing for Acra**, because the deck's answer to their over-conditioning concern is that every condition cites the directive it failed. Render `cell_key` and `cell_value` from `RuleOutcome.inputs` — they are already populated.

---

## Sequencing and acceptance

1. **P1 + P2 together** — same file, same class of fix, one review. Acceptance: the four Acra workaround rules (`ACRA-ITIN-*`, `ACRA-NO-RATIO-*`, `ACRA-STR-CLTV`, `ACRA-FOREIGN-NATIONAL-ESCROW`) can be rewritten to plain `==` and the strict-comparison probe expressed directly or rejected at authoring time with a message that says what to do instead.
2. **P4b** — small, unblocks the Acra condition-citation story.
3. **P3 decision** — needs an architecture call on trace composition, not just an implementation. Until it lands, the prepayment-penalty family and the Florida modifiers cannot be authored without option B or C, and both damage reviewability.
4. **P4a lint** — whenever.

**Regression bar for all of it:** `tests/test_condition_evaluator.py` (40 tests, 13 matrix) and `tests/test_default_policy_expert.py` stay green, and the Acra slice — `config/packs/acra_dscr_core/{profiles,policies}` with `tests/test_acra_eligibility.py`, 17 behavioural cases + a grid-completeness test — stays green. That slice is a useful second consumer to run against every IR change: it exercises `matrix`, `ratio`, and `expression` kinds, `applicability` pre-checks, band boundaries, NA sentinels, and the INDETERMINATE path in one file.

**Out of scope here:** anything in `fabric/opa/store.py` (still four `NotImplementedError`); the `MatrixCondition` change set itself, which is under separate review — this plan assumes it lands as-is.
