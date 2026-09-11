# CREMF: what the corpus asks for, and what japes does not yet have

Assessment of `jaci/docs/CRE/Commercial_Lending_Corpus_v1_0` (763 files, v1.0) against japes
2.5.1, for a `cremf` pack. Decides nothing; it names the gaps and which side each belongs on.

## What the corpus is

A client Product/Engineering specification for a six-value-process commercial lending suite, with
CRE and agency multifamily as an annex. It is not a policy library and says so repeatedly. The
part that matters for a pack:

| Where | What | Size |
| --- | --- | --- |
| `02_Functional/FRD-07_CRE_and_Agency_Multifamily_v1_0.md` | 13 CRE functional requirements + ~40 agency seeds | 2983 lines |
| `07_Reference_Data/agency_multifamily/data/*.csv` | 7 registers, machine-readable | 41 rules, 34 thresholds, 6 evidence floors, 8 calcs, 4 triggers, 6 features, 17 tests |
| `04_Engineering/schemas/runtime_contracts.schema.json` | 160 `$defs`, incl. `ProgramRule`, `ProgramEvaluation` | 472 KB |
| `05_Registers/effective_action_authority_v1_0.csv` | authority cells per action class | 5 CRE rows |
| `06_Assurance/` | fixtures, schema examples, semantic tests | 187 files |

The registers are the useful surface: `agency_requirement_register.csv` carries 25 uniform columns
per rule, which is pack-YAML shaped already. This is a corpus-to-vocabulary pipeline input, not a
document to read into prose.

## The governing constraint

Everything in the agency registers is **`status: seed`**, `provenance_class:
unofficial_secondary_source`, `confidence: medium`, `sme_validation_status: pending`. The corpus is
explicit about what that means at runtime:

> Numeric eligibility/sizing rules may be executed only after an official-source edition, effective
> date, applicability, approved calculation convention and accountable review are pinned. If that
> content is unavailable, return Unable to Evaluate/Pending Configuration. Never use a
> secondary-source threshold as a silent default.

So the pack cannot be "the thresholds, encoded". A CREMF pack has to carry rules that are inert
until activated, and a runtime that can say *why* it declined rather than computing with a seed
value. That is the whole design problem, and it is where japes is short.

## Gaps, japes side

**1. Rules cannot be activation-gated.** `ProgramRule` requires `official_source_ref`,
`source_edition`, `source_section`, `effective_from`, `approval_refs`, `test_refs`, and a `status`
of `seed | draft | approved | suspended | superseded`. japes gates at the *policy* level only:
`Policy.status` is `draft | active | deprecated | archived` (no `seed`, no `suspended`,
no `superseded`), and `Rule` carries none of it -- `rule_id`, `condition`, `applicability`,
`action`, `parameters`, `priority`, `description`, `citations`, `domain_extensions`. A seed rule and
an approved rule are indistinguishable to `PolicyRegistry`.

*Where it belongs:* japes. Rule-level status plus effective dating is not CRE-specific; AML and
DSCR both have the same "authored but not approved" state and neither can express it either.

**2. Thresholds carry no provenance.** `PolicyProfile.thresholds` is `dict[str, str]`. The corpus's
`agency_default_thresholds.csv` carries `provenance_class`, `confidence`, `source`,
`adjustment_rule` per threshold, precisely so that `1.25x / 80%` from Form 4660 via a secondary
source cannot be served as an approved figure. `PolicyProfile` already has `confidence_floors` and
`source_precedence`, so the shape is half there -- a threshold needs to be a value *with*
provenance, not a bare string.

*Where it belongs:* japes, as an optional richer value type. A plain string must keep working.

**3. The outcome vocabulary is missing four states.** `ProgramEvaluation.outcome` is an 8-value
enum: `Pass`, `Fail`, `Pending Evidence`, `Pending Calculation`, `Pre-Review Required`,
`Waiver Required`, `Not Applicable`, `Unable to Evaluate`. japes' `RefusalClass` is a different
axis (6 values, about why an *action* was refused). Nothing in japes expresses "the rule exists,
the evidence is fine, and I cannot evaluate because the program data is not pinned" -- which is the
one outcome the corpus insists on. `Pending Calculation` and `Unable to Evaluate` are the
fail-closed states; `Pre-Review Required` and `Waiver Required` are workflow routings.

*Where it belongs:* japes. This is the generalization of "sub-confidence evidence routes to review"
that `RefusalClass` already half-encodes, and the corpus's insistence that "a missing rule does not
become Not Applicable" is a rule the SDK should enforce rather than each pack re-deriving.

**4. Evidence floors are thinner than the matrix needs.** `EvidenceTypeDef` is `id`, `label`,
`description`, `fields`, `requestable`, `connector`. `agency_evidence_floor_matrix.csv` needs
`freshness_window` (90 days), `source_precedence`
(`borrower_certified > property_mgmt > estimated`), `quality_checks`, `missing_behavior`
(`Pending Evidence`), `human_gate`, `condition_tier`. Freshness and missing-behavior are the two
that change runtime behavior rather than documentation.

*Where it belongs:* japes, and it is the same gap the doc-processing taxonomy work keeps circling.

**5. Overlay-without-merge has no expression.** FR-CRE-08: "the agency ruleset overlays, never
replaces, base CRE underwriting; Fannie and Freddie are distinct profiles whose findings never
merge." japes has `depends_on` with fragment merging, and `PolicyProfile.institution_ref` for
per-institution profiles -- but nothing that says *these two profiles must not compose*. A pack
declaring both agency profiles today would merge cleanly and silently, which is the failure the
requirement is written against.

*Where it belongs:* japes. Note `policy_profiles` already refuses to guess among several profiles
with no default, which is the same instinct one level down.

## Gaps, Plato side

**6. The publish gate is the activation gate.** `plan_pack_store.md` step 3 defers a publish gate;
this corpus is the use case that defines it. A `seed`-status rule set should be publishable (so it
is versioned and citable) but not *activatable*, and the `pack_version` row already carries
`authored_status` separately from an operated status precisely so the log can disagree with the
manifest. What is missing is the transition: who approves a seed -> approved move, against which
`approval_refs`, and what the store records.

**7. Program data as a first-class pinned asset.** `ProgramRule.official_source_ref` +
`source_edition` means the agency guide edition is a pinned dependency of an evaluation, and
FR-CRE-09 makes a stale pin "a registered defect". The pack store versions *packs*; it has no
notion of a pack version depending on an external source edition. `depends_on` is the nearest
shape and it points at other packs.

## What a CREMF pack looks like

Not a new pack from scratch. `cre_underwriting_core` exists in jaci but is a stub (mode tuning and
a document agent, no manifest), and `dscr_core` is the working example of the manifest +
`policies/` + `profiles/` shape 2.5.1 just finished. CREMF is that shape plus a program overlay:

```
cremf_core/
  pack_manifest.yaml          policies: {dir: policies}, profiles: {dir: profiles}
  policies/
    eligibility.yaml          <- agency_requirement_register.csv, status: seed
    pre_review.yaml           <- agency_pre_review_waiver_register.csv
  profiles/
    fnma_dus.yaml             <- agency_default_thresholds.csv, provenance-tagged
    fhlmc_optigo.yaml         <- the sibling that must not merge with it
  evidence_types.yaml         <- agency_evidence_floor_matrix.csv
  derivations/                <- agency_calculation_contracts.csv (NCF, DSCR, sizing)
```

The 17 rows of `agency_test_cases.csv` are the acceptance set, and they are written
given/when/then, so they convert to tests directly.

## Order I would take it in

1. **Rule-level status + effective dating** (gap 1) -- nothing else can be encoded honestly first,
   because encoding 41 seed rules with no way to mark them seed is worse than not encoding them.
2. **The four outcome states** (gap 3) -- so the pack can fail closed and say why.
3. **Threshold provenance** (gap 2) -- unblocks `agency_default_thresholds.csv`.
4. Encode the pack against 1-3, with every rule `seed`, and run the 17 acceptance cases expecting
   `Unable to Evaluate` until a threshold is pinned. That run is the proof the gating works.
5. **Evidence floors** (gap 4) and **overlay-without-merge** (gap 5) as the pack needs them.
6. Plato's activation gate (gap 6) once there is a pack whose rules are worth activating.

Steps 1-3 are japes changes with no CRE in them, which is the test of whether they are the right
generalizations.
