# Authoring defects in the packs vendored into plato/data/seed_packs

Found by review rounds over japes' vendored snapshot of a consumer's `config/packs`. **None is a
japes code defect.** Every one is in the authored pack content, so the fix belongs in the consumer
repo that owns it; japes' copy is a snapshot and editing it there would diverge from the source of
truth while leaving the real packs wrong.

Verified against the vendored copies at the commit that added them.

## Credit-consequential

**IO products claim a FICO floor nothing enforces.** `dscr_core/policies/eligibility.yaml`
`DSCR-IO-MIN-LOAN` reads "Interest-only products require a minimum loan amount of $250,000 **and
minimum FICO 640**", and its only condition is `loan_amount >= <io_loan_amount_min>`. Confirmed: of
41 rules, 5 carry a `fico` predicate (`DSCR-ELIG-CLTV-GRID`, `DSCR-SUB-1-DSCR-FICO`,
`DSCR-FICO-LT-620-RESERVES`, `DSCR-ITIN-CLTV`, `DSCR-NO-RATIO-FICO`) and none is IO-scoped. The
profile authors `custom.fico_min_io: 640` and **nothing reads it**. So an interest-only file at FICO
620 passes on the main grid. `DSCR-NO-RATIO-FICO` makes the same style of claim and *does* enforce
it, so this is an asymmetry rather than a convention.

**Florida caps are described and not encoded, twice.** `DSCR-PROPERTY-TYPE-CLTV` defers a Florida
-5% modifier to "see ENCODING_NOTES G1", and `DSCR-HIGH-LTV-PROPERTY-TYPE` says "warrantable condo
(outside Florida)" with its own NOTE admitting the qualifier is unencoded. Both return SATISFIED for
a Florida file the program would cap lower.

The deferral's stated blocker is stale: `ENCODING_NOTES.md` records G1 (`all_of`/`any_of`) as
resolved japes-side, and the corpus already uses `kind: all_of`. One correction to the review that
raised this -- it said 10 rules use `all_of`; the actual count in this file is **1**
(`DSCR-NMLS-VERIFIED`). The capability being live is what makes the deferral stale, and one rule
proves that, but the count was wrong.

## Wrong prompts to a human

**Two PDF line-wrap orphans became required documents.** `ci-spread-core/policies/checklist_ci.yaml`
`purpose_specific_documents.required_documents` lists `schedule` and `available)` as documents,
while the entries they were wrapped from lost their heads. So an application run against this
checklist asks for a document named `available)` and never asks for the equipment schedule or the
acquisition documents. The file's own `description` says "Extracted verbatim from the source
checklist".

## Declared-but-absent, and present-but-undeclared

- `ci-spread-core` declares `overlays: [{path: policies/overlays/rb_ci.yaml}]`; the pack ships
  `policies/overlays/deal_si_rb_example.yaml` and no `rb_ci.yaml`. A missing declared ref is a
  warn-and-skip, so the narrowing overlay is silently absent.
- `ci-spread-core/policies/conventions.yaml` is declared nowhere, so its FCCR/ABL/LIEN policies and
  `RB_CI_OVERLAY` never load -- despite its header claiming "loaded via jazzx_sdk load_policies".
  The manifest has no `policies.dir`, which is what would pick both files up. `dscr_core` uses
  `dir:` and gets this right.
- `cl_of_core` and `cl_sp_core` both declare `experts.playbook.diagnose_map: diagnose_map.yaml` and
  neither ships the file. `ci-spread-core` ships a real one beside the same declaration.
- `ci-spread-core/spread_template.yaml` binds `{metric: da}` and `{metric: stock_based_compensation}`,
  which exist in neither the pack's 16 `metrics.yaml` ids nor the SDK's builtin metric dicts. Both
  exist as `cash_flow` chart-of-accounts keys and are bound that way elsewhere in the same file, so
  the two income-statement rows render empty for every period. The sibling templates
  (`spread_template_rb.yaml`, both `workbook_layout*.yaml`) resolve 100%.

## Documentation

`dscr_core/ENCODING_NOTES.md` §1b says the 14 PPP rules split "8 plain / 6 all_of"; §3 G1 says no
rule uses `all_of` yet. Both are contradicted by the corpus and by §1a. Its other counts (41 rules,
14 PPP, grid cell totals) verify.

## The declarative route does not carry the pack (settles the options)

`ci-spread-core`'s declarative path reaches **1 of its 7 authored policies**. Measured:

```
declared    policies/core.yaml                 -> CI_CORE_LEVERAGE_POLICY
undeclared  policies/conventions.yaml          -> FCCR, ABL, LIEN, RB_CI_OVERLAY, ADDBACK
undeclared  policies/overlays/deal_si_rb_...   -> RB_DEAL_SI_2026Q3
declared    policies/overlays/rb_ci.yaml       -> absent from the tree, one WARNING
```

So **"strip the `jaci.*` pointers"** -- the option sketched when this came up -- is not safe: it
converts a loud `ModuleNotFoundError` into a pack that silently enforces leverage and nothing else,
with one warning line as the only trace. `conventions.yaml`'s own header claims it is "loaded via
jazzx_sdk load_policies"; nothing declares it.

`dscr_core` gets this right with `policies: {dir: policies}`, which would pick up both undeclared
files and skip the checklist by shape. Applying that here is a one-line change *and* a credit
decision -- it changes which policies the pack enforces -- so it belongs to whoever owns the pack.

Same shape, smaller: `cl_of_core` and `cl_sp_core` declare `experts.playbook.diagnose_map:
diagnose_map.yaml` and neither ships the file.

## Wrong figures under a correct label

- `spread_template_rb.yaml`'s "Less Cash Taxes (Refund)" row binds `income_statement.
  income_tax_expense` -- book tax including deferred -- under a Cash Taxes label, while the pack
  carries `income_taxes_paid_net_of_refunds` and `spread_template.yaml` uses it. Two rows below,
  "Cash Interest" is left `unbound: true` on the stated grounds that binding it "would overstate
  confidence", so the discipline exists in the same file and was not applied here.
- `workbook_layout.yaml`'s header claims every `key` is checked at load "see workbook_layout.py's
  validator". There is no such module, and `load_workbook_layout` validates shape only -- a typo'd
  key emits a labeled row of empty cells. Both shipped layouts also state a `live_formula` sheet
  ordering rule the library cannot apply. Recorded japes-side as
  `TODO(layout-key-resolution)` and `TODO(layout-live-formula-order)`.

## A stated dollar floor that is not encoded

`ci-spread-core/policies/conventions.yaml` `CI-ABL-MIN-AVAILABILITY` describes "10% of borrowing
base **or $2M, whichever is greater**" and its condition is `excess_availability_pct >= 0.1` alone.
A borrowing base of $8M with $1.0M excess availability (12.5%) satisfies the rule while the stated
policy requires >= $2M. Fails open, and this file is now loaded -- `policies: {dir: policies}`
picks it up, so the rule is live rather than shadowed by the old registry pointer.

## Published archives carry the consumer's private references

`dscr_core/ENCODING_NOTES.md` ships in the wheel and is zipped into every published `dscr-core`
archive, carrying jaci commit hashes, `cd jaci && pytest` instructions, gitignored `plan_*.md`
filenames and client-internal source paths. Eleven seed-pack files name a `plan_*.md`. A published
archive is what a customer can materialize.

## Still in the two packs kept as seed data

`dscr_core` and `ci-spread-core` are the seed set now; their manifests are fixed and both load.
What remains in their content, for whoever authors them next:

- `ENCODING_NOTES.md` §3 G1 says "no rule in `policies/eligibility.yaml` uses `kind: all_of`/
  `any_of` yet -- the Florida-modifier and 13-state prepayment-penalty rules G1 was blocking remain
  unauthored", contradicting §1a/§1b of the same file and the shipped YAML, which has eight
  `all_of` rules and all fourteen PPP rules. Only the Florida modifier is genuinely open. A later
  author reading §3 re-authors rules that already exist.
- §1's completeness guarantee ("an absent cell raises `KeyError` at runtime -- hence
  `test_grid_is_fully_authored`") has no guard in japes' copy, and the `loan_purpose` axis declares
  no `bands`, so an unmapped purpose is a raw missing key. The grid as shipped is complete
  (3 x 11 x 3, counted), so it is coverage rather than a live gap.
- `ENCODING_NOTES.md` also states `pack_manifest.yaml` is "**still not wired** (`policies.registry`
  needs a Python `PolicyRegistry` object)", which the manifest committed beside it now contradicts,
  and §5 points a reader at `config/packs/dscr_core/` and `cd jaci && pytest` -- neither path exists
  in the repo the file ships in.
- `ci-spread-core/policies/core.yaml`, `checklist_ci.yaml` and `playbooks/loan_package_scaffold.md`
  carry provenance strings naming the consumer repo without a dot (`jaci/scripts/extract_policy.py`)
  and one tree's document layout (`docs/LoanSamples/YETI/...`). Inert, unresolvable outside that
  checkout, and shipped in the wheel. japes' guard pins files containing `jaci.` and cannot see
  these.

## What this says about the vendoring

Sixteen defects across four review rounds, nearly all in authored content, found because the
content came into japes -- three consecutive rounds spent their attention on a consumer's config
rather than on japes code. That is the
argument against keeping it here rather than a naming rule: a snapshot makes japes the place these
are *found* and the wrong place for them to be *fixed*. The seed mechanism plus
`PLATO_SEED_PACKS_DIR` gives the same dev-daily result while leaving the packs where their author
can correct them -- with one or two small generic packs authored in japes so `initialize` still
works out of the box and the tests have something to publish.
