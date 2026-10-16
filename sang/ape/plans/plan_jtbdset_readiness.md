# Plan: job-set readiness checks on the export, against a contract the pack declares

Origin: `note_sibling_check_20261012.md` item 1 (routed by opus-xrepo, user-approved routing). Owner:
sonnet-runtime. Status: R1-R4 built on v2.6.2 (5d1b5a62, 2026-10-12); R5 and a coverage-page column not built. Constraint from the user: no client or repo name in code,
comments, check ids or prompts; the work serves an external consumer that pins japes AND our own
`AdjudicationAgent`.

## Why

`export_jtbdset` / `export_pack_jtbdset` build the artifact and check nothing about whether a downstream
engine will load it. A downstream consumer applies about eleven checks at load; a set japes exports can
be rejected there (field length caps, a metric key it does not know) or load with wrong results (a
metric key owned by two jobs, a requirement text cut or flattened, a job depending on another
section's job). The JTBD writer also never fills a metric's `calculation_context`, which that consumer
now requires for a computed metric.

## What exists (read before building)

- `pipelines/policy/jtbdset.py`: `export_jtbdset(policies, ...)` renders each base procedure rule's
  requirements; metadata rides in `rule.domain_extensions["jtbd"]` (`loan_metrics`, `entity_types`,
  `mnemonic`, `section_type`, `assistant`, ...). `pack/jtbdset_export.py` wraps it; the draft route
  (`GET /packs/drafts/{id}/jtbdset`) turns a `ValueError` into a 422.
- `pipelines/policy/jtbd.py`: `JtbdTemplate` already is "what a pack says a job looks like":
  `limits` (`skill_max_chars`, `section_type_min_chars`), `outcomes` (the status vocabulary, each with
  a verdict), `mnemonics`, `roles`, `entities`, `metric_keys` (bound to the pack's catalog via
  `bound_to_catalog`), `requirement_template`. `_DraftMetric` has `metric_key`, `label`,
  `indicator_context`, `description_template`; the writer assigns `metric_mnemonic`.
- `pack/lint.py`: `PackLintFinding(code, subject, detail, severity)` and `PackLintReport`; the coverage
  routes and page already render findings.
- `AdjudicationAgentSpec.status_vocabulary` is declared pack data nothing reads
  (`TODO(adjudication-spec-fields-unread)`); `ProcedureOutcome.status` is the same vocabulary on the job.

## Design

**Two kinds of check, one report.**

1. *Structural, consumer-neutral* (always run): `duplicate-id` (mnemonics and metric mnemonics are
   unique across the set), `metric-key-owned-twice` (one writer per metric key), `cross-section-dependency`
   (no job depends on a job of another section, no dependency cycle), `text-lost` (a requirement text is
   not empty, cut mid-sentence, or flattened to one line when the job's blocks have structure),
   `metric-key-format` (`Entity`, `Entity.field`, `Entity.field.sub`, `Entity[f=v].field`),
   `metric-key-not-in-ontology` (the key resolves in the pack's catalog).
2. *Contract checks, limits from data*: `schema-invalid` (field length caps), `output-contract` (the
   outcome status vocabulary; which statuses may carry conditions; allowed condition types; one subject
   per condition), `calc-context-wrong` (a computed metric carries its formula in
   `calculation_context`). None of these numbers or words live in code.

**The contract profile.** A named profile declared in the pack, next to the job template: its field caps,
status vocabulary (each status with whether it may carry conditions), allowed condition types, and
whether a computed metric needs `calculation_context`. The export and the coverage page take a profile
name; no name runs the structural checks only. A consumer is a profile, not a branch in code. The status
vocabulary is the same list `AdjudicationAgentSpec.status_vocabulary` should read (so that field gets a
reader here, and the TODO closes), and `JtbdTemplate.outcomes` is checked against it.

**Where the report goes.** `PackLintFinding` rows with the check ids above as `code` (neutral ids; `error`
for what the consumer rejects or loads wrongly, `warning` for what only reads badly). `GET .../jtbdset?profile=<name>` returns the set and the findings
(an `errors` count; refuse with 422 only when asked: `strict=true`), the coverage page lists them per
job, and the client gets the same.

**Writer.** `_DraftMetric` gains `calculation_context`; the template says when a metric needs one (a
`computed` key declared by the catalog, or the profile's rule); the export carries it; the writer prompt
asks for it only where required.

## Phases

| | Work | Done when |
|---|---|---|
| R1 | `jazzx_sdk/pack/jtbdset_lint.py`: the structural checks over an exported set (artifact in, findings out); metric-key grammar and catalog lookup | each check has a failing test on a set built to trip it, and passes on a clean one |
| R2 | The profile: model, declared in the pack beside the template, loaded and validated at pack load; the contract checks read it | a pack with a profile lints; one without gets structural only; a profile naming an unknown status is refused at load |
| R3 | Export and routes: `?profile=`, findings in the answer, `strict`; client method; coverage page column | route tests for clean, warned and strict-refused; the page shows the findings |
| R4 | Writer: `calculation_context` on `_DraftMetric`, template rule, prompt line; digest recorded | a computed metric without it is a finding; with it, clean; prompt digests updated |
| R5 | `AdjudicationAgentSpec.status_vocabulary` read: the vote's order and the outcome check (the unread-field TODO closes) | the vocabulary a pack declares orders a tie and refuses an undeclared status |

R1 and R2 are independent of the writer and can ship first; R4 changes a prompt, so it lands last and is the
only phase with model-facing risk.

## Decisions (the user's, 2026-10-12: all four recommendations taken)

1. Profile home: its own file, `export_profiles/<name>.yaml`, one per consumer.
2. `text-lost`: empty text and a cut mid-word are errors; "flattened" is a warning only.
3. `cross-section-dependency`: inferred from what exists (a job's text naming another job's mnemonic, and a
   `depends_on` list when a job carries one); "cannot tell" is not a finding. No new authoring field.
4. Severity per check, overridable in the profile.
Direction (user, same day): tolerant first. The export returns its findings; only `strict=true` refuses.

Scope note: the profile's condition-type and one-subject-per-condition rules concern conditions a
decision carries at run time, which the export does not contain; they are not built
(`TODO(profile-condition-rules)`), the status vocabulary, field caps and calculation-context rule are.

## Tests

Each check: a failing case, a clean case, and the check id asserted from the report (not a literal the
code derives). The profile: a load that refuses an undeclared status; a limit read from the profile, not
a constant (change the profile, the finding changes). One route test through the real router; the coverage
page asserted on its served HTML for the findings column. Boot and import checks unchanged.

## Not in this plan

Item 4 of the note (`ValidatedOutput` keeping tools callable): no validator in japes has a tool-call
remedy yet. Items 3, 5 and 6 are the user's to prioritise.
