# The imdoc Acra taxonomy, and whether the DSCR scenario should use it

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: assessment, 2026-09-02. Read-only; nothing changed in either repository.

## Verdict

**Yes, and it is the largest single asset available to the DSCR scenario right now.** jaci's
`dscr_core` pack declares **one** document label. imdoc's new taxonomy declares **485**, authored
against Acra's own document set, with classification cues, aliases, PII markers and condition codes.

Two caveats sit alongside that, and both matter more than the headline: the condition codes do **not**
join to anything in jaci today, and the taxonomy is authored for a different pipeline. Details below.

## What imdoc has

Commit `cab579f` "added acra taxonomy" (2026-09-02), later renamed by `54ab052`. Now at
`python/src/imdoc/assets/taxonomy/tree/`: 16 category files, **485 document types**.

Categories: application, assets, borrowing-entity, broker-channel, closing-and-settlement, credit,
disclosures, income, lender-administration, miscellaneous, property-collateral, quality-control,
root, servicing, taxes-and-insurance, title.

Each type carries a `cues` string doing considerable work at once. From `borrowing-entity.yaml`:

> **CertificateOfGoodStanding** -- "Current state certificate confirming the entity is active and
> compliant with filing and franchise-tax obligations. Dated document -- staleness matters.
> Condition 5003. AKA: Certificate of Status; Certificate of Existence; Good Standing Certificate."

That single field holds: a classifier description, a temporal-validity warning, an Acra condition
code, and three aliases. Others carry PII handling (`EINNumber`: "Sensitive-PII -- masked in all
views") and data-quality notes (`OperatingAgreementByLaws`: "Two BytePro codes exist for the same
document -- one must be retired before either is used as a classifier label").

That last one is the tell that this was authored by someone reading Acra's real document inventory,
not generated.

## What jaci's DSCR pack has

`config/packs/dscr_core/`:
- `document_agent.yaml` -- **one** label, `appraisal_report`
- `policies/eligibility.yaml` -- 41 eligibility rules
- `profiles/dscr_profile.yaml`, `ENCODING_NOTES.md`

## The condition-code question, answered carefully

My first pass looked promising and was wrong, so the method matters here.

`grep` for `5000` in jaci's `eligibility.yaml` returns hits, which looked like a shared code
vocabulary. It is a substring of `max: 1500001`. Extracting properly:

- **imdoc** declares 15 distinct condition codes: `4500`, `4609`, `4901`, `5001`-`5007`, `8002`,
  `8105`, `8205`, `8211`, `8303`, `8400`. 24 of the 485 types carry one.
- **jaci** declares **none**.
- Overlap: **none** -- because jaci has no codes, not because the two disagree.

The 51 occurrences of "condition" in `eligibility.yaml` are a different concept entirely:
`condition: {kind: matrix, axes: [...]}` and `condition: {kind: expression, field: loan_amount}` --
the policy predicate a rule evaluates. Acra's conditions are **outstanding items a borrower must
satisfy**. Same word, unrelated meanings, and conflating them would be a real modelling error.

## What is worth taking, and in what order

**1. The document taxonomy, directly.** 485 types against 1 is not an incremental improvement. The
`cues` strings are already shaped like classifier prompts, which is what `DocumentAgent` consumes.
This is the immediate win and needs no new concepts.

**2. The aliases, as a distinct field.** Every AKA list is currently prose inside `cues`. Classifiers
benefit from aliases as data -- they are matched against, not read. Lifting `AKA:` out of the cue
into an `aliases: []` field is mechanical and makes the taxonomy queryable.

**3. The PII markers, as policy rather than prose.** "Sensitive-PII -- masked in all views" is a
handling instruction sitting in a description field where nothing enforces it. japes has redaction
primitives (`redact_before`, `redact_fields`); a `pii: true` flag could drive them. Prose cannot.

**4. The condition codes -- only after deciding what they are for.** 24 types name an Acra condition.
That is the beginning of *document satisfies condition*, which is exactly what a conditions engine
needs and what jaci's DSCR scenario does not model at all today. It is also the piece most likely to
be built wrong: Acra's condition ids are theirs, and importing them means jaci carries a foreign
identifier space. Worth doing, worth doing deliberately.

## Two things to check before adopting

**Authored for a different pipeline.** imdoc's taxonomy feeds its own Go and Python classifiers
(`go/internal/taxonomy/`, `python/src/imdoc/taxonomy.py`). The tree shape -- `children` with `name`
and `cues` -- is not japes' `document_agent.yaml` shape (`taxonomy: [{label, description}]`). A
conversion is small, but it is a conversion, and the question of which repository owns the source of
truth afterwards should be answered before it is copied rather than after it has diverged.

**485 labels may be too many for one classifier.** A flat 485-way choice is a different problem from
a 16-way category choice followed by a within-category one. The taxonomy is already a tree, so the
hierarchy is available; japes' `DocumentAgent` would need to use it in two passes to benefit. Worth
measuring before assuming the flat form works.

## Recommendation

Take the taxonomy; leave the condition codes for a separate decision.

Concretely: convert the 16 category files into `dscr_core`'s `document_agent.yaml` shape, keeping
category as a first-class field so the two-pass option stays open, and lifting aliases and PII out of
the cue text into their own fields. That replaces one label with 485 and costs nothing conceptually.

Then, separately, decide whether jaci models Acra conditions at all. If it does, the 24 coded types
are the seed of a document-to-condition mapping and the most valuable part of the whole artefact. If
it does not, they are provenance notes and should stay in the cue text where they do no harm.

## A note on ownership

Both repositories would then hold the same taxonomy, and they will drift. The options are the usual
three -- imdoc owns it and jaci imports at build time, jaci owns it and imdoc imports, or japes holds
it as a shared pack fragment (`depends_on` already supports fragment-limited imports, which is what
that mechanism is for). The third is the one that matches how packs are meant to compose, and it is
worth raising with imdoc's author before either side copies.
