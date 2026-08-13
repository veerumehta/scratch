# Commercial Lending — Domain Page

**The operating model: how a customer's own spread format becomes a running capability.**

Author: Claude (Cowork) for Virendra Mehta · 2026-08-08
Grounded in the real case files under `jaci/docs/LoanSamples/`. Every figure, formula, label and
cell reference below was read out of the customer artifacts named beside it. Where something could
not be determined from the files, it says so rather than filling the gap.

Part 1 is the operating model. Parts 2 and 3 are two worked cases, C&I and CRE, with the actual
induced template and the actual skill changes. Part 4 covers the remaining cases in the corpus.
Part 5 is the honest status. Appendix A is the engineering detail.

---

## 1. The operating model

### 1.1 The claim

> An FDE works with the customer to establish their output format. They express it once as a
> template, and teach the agent the handful of things the template alone can't say by editing a
> skill. From then on, every incoming transaction runs through the same path automatically.

Four moments, and only two of them involve a human.

| Moment | Who | What happens | Frequency |
|---|---|---|---|
| **Onboard** | Customer | Hands over their existing spread workbook and a sample loan package | Once |
| **Induce** | FDE + agent | The workbook is parsed into an `OutputTemplate`; the FDE reviews and publishes it | Once, ~hours |
| **Teach** | FDE | Writes or edits skills for what the template can't express | Once, plus as cases surface |
| **Run** | Nobody | Document agent → fill agent → validation → governed workbook | Every transaction |

The measure of success is not the first customer. It is that the tenth is boring.

### 1.2 What each party actually supplies

**The customer supplies two things**, and they already have both: their standard spread workbook —
the one an analyst opens today and fills by hand — and one representative loan package. They do not
write configuration, do not learn a schema, and do not describe their format in prose. Their
spreadsheet *is* the specification.

**The FDE does three things.** Runs induction over the workbook. Reviews the draft, which is mostly
confirming and occasionally correcting how a row was typed. Then writes the small number of rules
that live in the analyst's head rather than in the sheet — and those become skills.

**Per transaction, nobody does anything.** A package arrives, the document agent normalises it, the
fill agent produces the customer's own workbook, validation runs, and anything uncertain lands in a
review queue with the evidence attached.

### 1.3 Why the template is the contract

A spread is not a neutral rendering of a borrower's financials. It is an institution's opinion
about which lines matter, what they are called, how they are ordered, and which ratios govern.
Two banks looking at the same 10-K produce different spreads, and both are right.

Three properties make the template a contract rather than a layout:

**Every row is present, populated or not.** A field that could not be filled has
`status: unmatched`, so the unmatched set is enumerable. A blank cell in the delivered workbook is
never silent — it is a named field with a reason attached. This is the invariant jaci's existing
`spreader_template_trace()` already enforces for its render path, carried into the fill path.

**Computed rows are computed, never inferred.** A row with a `derivation` is evaluated
deterministically through the expression DSL. The model is never asked what Gross Profit is when
the template says it is Revenue minus COGS. The scope of what an LLM decides is exactly the scope
of what genuinely requires judgment.

**The key is the identity, not the label.** In the Regional Bank workbook, *four different rows are
labelled "Margin"* (sheet rows 8, 13, 17 and 20). A row's label can be relabelled by the customer
next quarter without breaking anything, because bindings, citations and covenant references are all
by `key`.

That last point resolves an objection worth naming, because it looks like a contradiction with an
existing decision. `plan_JACI_CL_PRD_DEMO_ARC.md` §87 says: *do not add a `cited_rows` field and do
not ask the credit-phase prompt to emit row keys… emitting it from a cognitive mode couples the
reasoner to one institution's layout.* That prohibition stands and this does not violate it. The
thing being protected is a **reasoning mode** — the credit reasoner must never learn the layout.
The fill agent *is* the presentation layer; the template is its input contract, not a leak into a
judgment prompt. And what it echoes is the canonical `key`, never the `(section, label)` row key
the prohibition is about — so the specific failure it names, "a relabelled row silently breaks
citation," cannot occur.

### 1.4 Why a skill, and not a prompt edit or a code branch

Some things a template cannot say. That this institution's "EBITDA" is Gross Profit minus SG&A
minus Rent. That when two statements cover the same period the audited one wins, except for the
interim leg where the only source available is a company-prepared export. That a 38% jump in one
expense line means go find the letter of explanation.

Those are real, they are customer-specific, and today they land as prompt edits or code branches.
Neither is governable: a prompt edit is invisible to review and a code branch makes the tenth
customer a fork.

A skill is the third option, and the registry that holds it already has the right shape. `SkillRegistry`
is tiered — **tier 1 platform, tier 2 pack config, tier 3 builder/customer overlay** — and refuses a
less-trusted tier that tries to shadow a more-trusted name unless the caller passes `allow_override=True`
explicitly. That maps one-to-one onto the Assistant Binding Annex's overlay rules (§11.1 what
overlays may narrow, §11.2 what they may not change). A customer overlay may add and narrow. It may
not silently replace a pack rule.

Skills are ordered tier 1 → 2 → 3 when the prompt is assembled, so the customer overlay is read
last and is the most specific instruction the model sees. Each filled cell records which skills
applied to it. An FDE debugging a wrong number can see why it is wrong; a reviewer can see who
taught the system to produce it.

---

## 2. Case 1 — Regional Bank / C-DIVE, LLC (C&I)

`docs/LoanSamples/Regional Bank/` · segment: C&I · pack: `ci-spread-core`

### 2.1 What came in

Five financial statement PDFs at four different assurance levels, a credit application, and — the
important one — the analyst's own working spread, `Output Cleaned.xlsx`.

| Document | Covers | Assurance |
|---|---|---|
| `2018 and 2019.pdf` | FY2018–FY2019 | Reviewed |
| `2020 and 2021.pdf` | FY2020–FY2021 | **Audited** |
| `2022 - 9 months.pdf` | 9M to 9/30/2022 | Compilation |
| `2022 and 2023.pdf` | FY2022–FY2023 | **Audited** |
| `2023 - 9 months.pdf` | 9M to 9/30/2023 | Company-prepared |

Four assurance levels across five documents, with two of them covering FY2022. Source precedence is
not a nicety here; without it the spread is wrong.

### 2.2 The template, induced

`Output Cleaned.xlsx` → sheet **"First Citizens Format"**, 48 fields across three sections. Full
induced template: `artifacts/rb/output_template.yaml`.

What the deterministic pass gets for free, with no model call at all:

- **Structure** — three blocks: income statement (sheet rows 4–31), summary balance sheet (33–43),
  and a separately-columned "Adjusted Fixed Charge Coverage Calculation" (48–77).
- **The column axis** from row 3: `2019, 2020, 2021, 2022, PY 9/22, CY 9/23, LTM Sept 23`.
- **Units and dtype** from number formats: `_(* #,##0_)...` → decimal in thousands; `0.00%` →
  percent; `0.00` → ratio.
- **Derivations from formulas.** `=D4-D6` becomes `gross_profit = net_sales - cost_of_goods_sold`.
  `=SUM(D22:D25)` becomes the `total_other` summation. These are lifted, not guessed, and they are
  then evaluated deterministically forever after.
- **Emphasis** — bold rows are the customer's own subtotals.

Only what remains — a canonical `key`, a `dtype` where the format is ambiguous, aliases — goes to a
bounded model call, one per section.

### 2.3 What only the workbook could tell us

This is the part that justifies the whole exercise. None of it is in the loan documents.

**`CIT EBITDA = Gross Profit − SG&A − Rent`** (row 12, `=D7-D10-D11`). It never touches operating
income, D&A or interest, and it *subtracts* rent. It is not EBITDA in any textbook sense. It is
this institution's house metric, it is what their covenants reference, and it is knowable only from
their spreadsheet.

**Three stacked definitions, in order.** `Adj. EBITDA = CIT EBITDA + Adjustments`;
`Adj. EBITDAR = Adj. EBITDA + Rent`. Note that rent is subtracted at the first step and added back
at the third — deliberate, not a double count. And "Adj. EBITDAR" here is a *different lineage*
from the pack's existing `ebitdar` metric (`operating_income + D&A + rent`): same word, different
number. Binding that row to the pack metric would be a silent, plausible, wrong answer.

**The LTM rule differs by line semantics.** Flow rows roll forward — `=G4-H4+I4`, i.e.
FY2022 − PY 9/22 + CY 9/23. Stock rows take the latest interim — Cash is `=I34`. A filler that
applies one rule to both produces a balance sheet that is nonsense. Verified against the PRD's own
worked example: 61,443 − 44,326 + 57,581 = **74,698**, matching cell J4 exactly.

**Net income is derived downward.** `=D19-D26-D28-D11-D15` — from Adj. EBITDAR, not up from
revenue. Arithmetically sound because EBITDAR added rent and adjustments back; structurally
unusual. Do not "correct" it: the customer's covenant language references these rows.

**Two hardcoded plugs, in the reference file itself.** Cell H10 contains `=10853-1`. Cell D39
contains `=25007-D37`. An analyst typed arithmetic into data cells. Induction records both as
defects rather than reproducing them — and `detect_hardcoded_plugs` should fire on the customer's
own workbook, which is a useful thing to be able to tell them.

**Assumptions masquerading as figures.** Maintenance capex is flat 1,000 in every period including
LTM. It is not reported anywhere; it is an analyst convention for splitting total capex. Growth
capex is the remainder. Financed capex likewise. All three must render as assumptions with editable
values and rationales, never as reported figures (FR-CUS-6).

**Cash interest ≠ interest expense.** 1,892 vs 2,096 in FY2019, and they differ in every period.
Two labels, two keys. Collapsing them corrupts the fixed-charge coverage ratio, which is a covenant.

### 2.4 The skill changes

Three tier-3 skills. Full text in `artifacts/rb/skills/`.

**Before** — what the pack ships (tier 2), the same for every C&I customer:

```yaml
skills: [ci_statement_mapping, ci_addback_library, ci_source_precedence_default]
```

**After** — what the FDE adds for this customer:

```yaml
skills: [ci_statement_mapping, ci_addback_library, ci_source_precedence_default,
         rb_house_ebitda,          # + tier 3
         rb_source_precedence,     # + tier 3, narrows the pack default
         rb_capex_split]           # + tier 3
```

| Skill | `applies_to` | What it teaches |
|---|---|---|
| `rb_house_ebitda` | the 5 EBITDA rows | The three house definitions, in order; that rent is subtracted then added back; that `Adj. EBITDAR` must not bind to the pack `ebitdar` metric; that four rows share the label "Margin" so resolution is by key |
| `rb_source_precedence` | whole template | `audited > reviewed > compilation > company_prepared`; that the FY2022 audit supersedes the compilation's comparative and the supersession is recorded, not dropped; that the CY 9/23 column is company-prepared and must carry that assurance rather than inherit the audit's; that the 9M-2022 compilation has no cash flow statement, so those rows are *unavailable*, not zero; that the late-arriving audit is still read for the ERC footnote (a $2,331,124 refund, ~$573,000 unrecorded obligation) |
| `rb_capex_split` | 4 capex/interest rows | That maintenance capex is a house placeholder to be surfaced for confirmation on every borrower; that growth capex inherits the assumption; that cash interest and interest expense are different figures and must never share a key |

A representative excerpt, from `rb_house_ebitda`:

```yaml
name: rb_house_ebitda
applies_to: [cit_ebitda, cit_ebitda_margin_pct, adjusted_ebitda,
             adjusted_ebitdar, adjusted_ebitdar_margin_pct]
instructions: |
  This institution does not use textbook EBITDA. Three house definitions apply, in this order:
    CIT EBITDA    = Gross Profit - SG&A - Rent
    Adj. EBITDA   = CIT EBITDA + Adjustments (policy-approved add-backs only)
    Adj. EBITDAR  = Adj. EBITDA + Rent
  - CIT EBITDA never references operating income, D&A, or interest...
  - "Adj. EBITDAR" here is NOT the pack's `ebitdar` metric. Same word, different lineage
    and a different number. Never bind this row to that metric.
```

That is the whole customisation. Three YAML files, no code, no fork.

### 2.5 What runs per transaction

Nothing above repeats. A new C-DIVE package arrives and: documents normalise → the deterministic
pre-pass resolves every row whose key matches the chart of accounts (most of them, no model call)
→ the remainder goes to one bounded call per section with the three skills layered in tier order →
derivations evaluate → validation runs, including the arithmetic controls → anything uncertain
lands in the review queue with its evidence.

---

## 3. Case 2 — Mesa Verde Apartments (CRE multifamily)

`docs/LoanSamples/MesaVerde/` · segment: CRE multifamily · pack: `cre_underwriting_core`

The contrast case, and the one that shows this is a platform mechanism rather than a C&I feature.
Different segment, one-fifth the size, whole dollars instead of thousands, and a workflow semantic
the C&I template does not have.

### 3.1 What came in

Two files. `Mesa_Verde_T12_Spread.xlsx` — whose own subtitle reads *"Bank CRE Multifamily
Template"*, so the customer is telling us plainly this is their standard — and
`MesaVerde_Insurance_LOE_RachelKim.pdf`, a letter of explanation sitting **beside** the workbook,
not inside it.

### 3.2 The template, induced

13 fields, one section. Full template: `artifacts/mesaverde/output_template.yaml`.

Everything the C&I case demonstrated applies, and two new things appear:

**The column axis is relative, not absolute.** `Year 1 | Year 2 | T-12`. There are no fiscal years
and no period-end dates anywhere in the sheet. Induction records that faithfully and leaves period
binding to fill time, driven by the operating statements. Inventing calendar years here would be
fabricating information the customer did not give us.

**Units differ from the C&I template.** `$#,##0` — whole dollars, against thousands for Regional
Bank. A fill agent that carries a units assumption between templates produces a 1000× scale error,
which is precisely what `detect_scale_errors` exists to catch.

One detail worth flagging for anyone implementing: DSCR's number format is `0.00"x"`. The trailing
`x` is a display suffix, not a unit. A reader that treats the format string as a unit emits `1.30x x`.

### 3.3 The gate the customer wrote in prose

Row 19 of the sheet, verbatim:

> *Note: Insurance and Property Tax pending analyst confirmation. Post-flag NOI/DSCR locks once
> cleared.*

And rows 15 and 17 are literally labelled **"NOI (pre-flag)"** and **"DSCR (pre-flag)"**.

This is a real gating rule. The customer wrote it into a free-text note and into row labels because
a spreadsheet has nowhere else to put workflow state. It is the single clearest argument for why the
template is not the whole contract: no schema of rows and formats can express *"these two figures
are provisional until a human clears two specific inputs, and while they are provisional they must
not reach the credit decision."*

In the platform that becomes a gate with candidate-versus-approved discipline, and the promotion is
a human action with an actor recorded — never automatic on a re-run. We keep the customer's labels
and carry the state properly alongside them.

### 3.4 The skill changes

Two tier-3 skills. Full text in `artifacts/mesaverde/skills/`.

```yaml
# before
skills: [cre_t12_mapping, cre_noi_conventions]
# after
skills: [cre_t12_mapping, cre_noi_conventions,
         mv_insurance_loe,          # + tier 3
         mv_pending_confirmation]   # + tier 3
```

`mv_insurance_loe` encodes the variance rule and the evidence hunt. The trigger is real and
measured from the file: insurance moves 193,200 → 266,600, **+38.0%**, while total operating
expenses move **+6.2%**. The rule generalises that to *any* operating line moving more than 15%
while total opex moves less than 10%, and then: hold the figure as `confirmation_required`, find
the letter of explanation in the application package, **bind it as evidence on the cell** so the
reviewer opens it from the cell rather than hunting for it, and — if no explanation exists — say
so explicitly rather than passing the figure through quietly. It deliberately does not judge
whether the increase is reasonable. It surfaces, binds, and defers.

`mv_pending_confirmation` implements row 19 as a gate: NOI and DSCR emit at `state: pre_flag` while
either gated input is unconfirmed; a pre-flag DSCR does not flow into covenant testing; promotion
is human and recorded; and the row labels are left alone.

### 3.5 The generated Excel

`MesaVerde_T12_filled_by_agent.xlsx` accompanies this page — the customer's own template, filled,
as the agent would emit it. Two sheets:

**"T-12 Spread"** reproduces their layout exactly. Extracted values are blue, formulas black, and
the tripped variance gate is shaded. Formulas are live, not baked results — `Total Operating
Expenses` is `=SUM(B6:B13)`, NOI is `=B5-B14`, DSCR is `=B15/B16` — so the workbook recalculates
when an input is corrected. Provenance rides on the cells as comments: hover Insurance and you get
the variance, the skill that fired, and the bound LOE.

Computed and verified: total opex 1,738,600 / 1,784,200 / 1,894,000; NOI 3,451,400 / 3,535,800 /
**3,559,000**; DSCR 1.26x / 1.29x / **1.30x** — all still labelled pre-flag, because the gate has
not cleared.

**"Fill Trace"** is the audit artifact: one row per template field with its status, match kind,
source, confidence and applied skill. Gated rows are shaded. It ends with
*"Unmatched fields: 0 of 13. Every template row is present."*

---

## 4. The other cases in the corpus

Covered honestly, because a coverage claim assembled from recollection is unreliable in both
directions.

**YETI** (`docs/LoanSamples/YETI/`, C&I) — the richest package: three SEC 10-Ks, a borrower
application summary, two borrowing base certificates, a closing binder, and **three** analyst spread
PDFs. It is the corpus's most-worked case and already drives the live demo path. Its output format
exists only as PDF, so induction there is the harder OCR-and-layout path rather than the direct
workbook parse — which is exactly why RB and MesaVerde are the right two to lead with. YETI is the
natural third once PDF induction is real.

**MAA** (CRE multifamily REIT) — three 10-Ks in PDF, HTML and markdown, a full application package
with a CRE document checklist, and a credit memo *plus* a `Credit Memo Supplement — MAA Spreads and
Financial Appendix`. That supplement is a genuine analyst output and a genuine induction target. It
is a public REIT, so it also exercises the multi-entity path the corpus otherwise lacks.

**CFI Case Studies** — three ZIP archives (Woodchucks, Rocky Mountain Holdings, RockCrusher
Rentals), unextracted. Training-style case studies rather than live packages. Potentially useful as
additional template shapes; nothing has been read, and I am not claiming otherwise.

**ParseBench** — 2,113 files of PDFs, JSONL and a notebook. **Not a lending case at all**: it is a
document-parsing benchmark (annual reports, ESG reports, IRS instructions). It is valuable for the
*document* agent's layout and table extraction, and irrelevant to templates and skills. Worth
saying plainly so nobody counts it as a sixth case.

---

## 5. What this does not yet do

The operating model above describes a capability that is partly built. Stated plainly:

- **`OutputTemplate` and `TemplateFillAgent` do not exist yet.** The plan is
  `plan_JAPES_TEMPLATE_FILL_AGENT_AND_SKILLS.md`. The two templates in this page are real
  inductions of real customer files, hand-derived to prove the schema carries what the artifacts
  actually contain — they are not machine output.
- **Induction is not built.** Everything in §2.2 marked "free from the deterministic pass" is
  derivable from openpyxl today and was in fact derived that way to write this page. It is not yet
  a CLI verb.
- **Wave 4b already owns customer-workbook parsing** (FR-ING-2, FR-EXT-8, FR-CUS-3) and was
  sequenced last on the stated grounds that *"building the generator before the target schema has
  been proven by hand is the wrong order."* That precondition is now met — Wave 1e proved the RB
  schema by hand, and this page proves it a second time against a different segment. This work is
  how 4b gets delivered, not a rival to it.
- **`Skill.applies_to` does not exist** on the japes `Skill` model. It is one optional field, and
  the alternative (a parallel skill type and registry) splits governance in two.
- **Pack Studio stays CLI-and-SDK for now.** The positioning question — what "Studio" is relative
  to Pack Studio — is explicitly still open, with a recorded recommendation to harden the SDK and
  prove it on real customers first. The FDE surface here is a CLI. A UI is a later skin over the
  same verbs.

---

## Appendix A — Engineering

### A1. Objects and where they live

| Object | Home | Status |
|---|---|---|
| `OutputTemplate`, `TemplateField` | `jazzx_sdk/agents/template_fill/template.py` | proposed |
| `TemplateFillAgent`, `FilledTemplate`, `FilledField` | `jazzx_sdk/agents/template_fill/` | proposed |
| `induce_template` + `jazzx template` CLI | `jazzx_sdk/agents/template_fill/induction.py` | proposed |
| `Skill`, `SkillRegistry` (tiered 1/2/3) | `jazzx_sdk/agents/interactive/{spec,registry}.py` | **exists** |
| `LineVocabulary` / `resolve` / `MatchKind` | `jazzx_sdk/finance/vocabulary.py` | **exists** |
| `WorkbookLayout`, governed export | `jazzx_sdk/finance/workbook.py`, `excel.py` | **exists** |
| Expression DSL (`validate`, `evaluate`) | `jazzx_sdk/expressions/` | **exists** |
| `EvidenceWorkspace`, `enforce_read_cap` | `jazzx_sdk/agents/adjudication/workspace.py` | **exists** |
| Per-case templates and skills | `config/packs/<pack>/agent/skills/*.yaml` | convention **exists** (`clinical-intake-core`) |

Note the placement constraint: this must **not** be a top-level `jazzx_sdk/templates/`. That
violates P8 (module placement) and the Unified Documents ruling, and collides with the existing
`jazzx_sdk/templating` and `tools/documents/templates.py`. It belongs under `agents/` as a fifth
sibling to `interactive/`, `document/`, `reasoning/`, `adjudication/` — all named for the shape of
work.

### A2. The two-template problem

`config/packs/ci-spread-core/spread_template_rb.yaml` already exists and describes the same RB
layout as *render* rows (label + source binding, with `unbound: true` and a reason where nothing
resolves). The `OutputTemplate` here describes it as a *fill contract* (key + dtype + unit +
derivation + column semantics + assumption/gate flags).

Both are legitimate and they overlap by about 60%. **Do not maintain them separately.** The fill
contract is the superset; the render template should be generated from it. Deciding that before
either grows is cheaper than reconciling two drifted files later — this is the same drift the
13-mode list is currently demonstrating in three places in japes.

### A3. Skill resolution order

For each field group the fill agent assembles: every allow-listed skill whose `applies_to`
intersects the group, plus every skill with an empty `applies_to`, ordered **tier 1 → 2 → 3** so the
customer overlay is read last and is the most specific instruction the model sees. Applied skill
names and tiers are recorded on each `FilledField.rationale`.

A tier-3 skill may not shadow a tier-1 or tier-2 name without an explicit `allow_override=True`.
That is `SkillRegistry`'s existing guard, and it is what makes ABA §11.2 ("what overlays may not
change") mechanical rather than aspirational.

### A4. Build order

1. `OutputTemplate` + registry (`_TieredRegistry` extracted to `jazzx_sdk/_registry.py` first).
2. `TemplateFillAgent`, with the deterministic pre-pass doing most of the work before any model call.
3. `Skill.applies_to` + tier-ordered resolution.
4. Induction + the `jazzx template` CLI verbs, with a mandatory FDE review gate.
5. jaci adapter — gate is the RB reference case reproducing `_RB_LTM_EXPECTED` at the pack's
   `ltm_reproduction_tolerance`, with `cit_ebitda == 11810` still holding, **through the new agent**.

The second consumer after RB should deliberately be non-financial (CRE property summary, KYC file
summary). A second finance consumer will not surface the finance assumptions still leaking into the
schema, and that is the abstraction's only real test.

### A5. Artifacts accompanying this page

```
artifacts/rb/output_template.yaml               48 fields, induced from Output Cleaned.xlsx
artifacts/rb/skills/rb_house_ebitda.yaml
artifacts/rb/skills/rb_source_precedence.yaml
artifacts/rb/skills/rb_capex_split.yaml
artifacts/mesaverde/output_template.yaml        13 fields, induced from Mesa_Verde_T12_Spread.xlsx
artifacts/mesaverde/skills/mv_insurance_loe.yaml
artifacts/mesaverde/skills/mv_pending_confirmation.yaml
MesaVerde_T12_filled_by_agent.xlsx              generated output + fill trace
```
