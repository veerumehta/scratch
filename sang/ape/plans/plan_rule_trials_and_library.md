# Plan: trialling generated rules, and the library they are written against

Status: draft for the user's review. Nothing here is built. Read first: `status/done_JAPES_2_2_0_EXPRESSION_DSL.md`
(the expression language), `plans/plan_plato_authoring_review.md` (review, roles, P7's eval entity over
a pinned draft), `plans/plan_case_rerun.md` (rerun basis, unchanged documents reused),
`plans/plan_policy_jtbd_extraction.md`, `plans/plan_scanned_documents.md`.

## 1. The problem

Extraction produces rules (python first, conditions too). Today the only checks between a generated
rule and a published pack are static: lint (`pack/lint.py`), `check_python_rule`, the rule's own
generated test cases. Nothing says whether a rule **gives the right verdict on a real loan package**,
which fields it needs that the documents did not supply, or whether it fails at a boundary. A review
of 51 generated Python rules found 45 `return False` paths, none indeterminate, and `loan_purpose`
compared as `'purchase'` in 11 and `'Purchase'` in 24: the same few mistakes written 51 ways. The
second half of this plan removes that class of mistake at the source; the first half finds the rest.

```
extract -> trial -> judge -> fix -> (re-trial) -> merge -> publish
```

## 2. What exists, and what does not

| Piece | Exists | Gap |
|---|---|---|
| Run a pack on a case with documents | `conductor_pipeline` (`document_ingest` then `policy_assessment`), case runs, `rerun` basis, unchanged documents reused | runs the **published** rules only |
| Assess with chosen rules | `assess(pack, record, policy_ids=, spec=)`; `JsonRulePack` loads policies | no way to add **unmerged proposals** for one run |
| Proposals to rules | `rule_merge.py` (merge-rules) writes into the draft | a pure "proposals as rules, in memory" function is not exposed |
| Eval plane | datasets, experiments, scorers, comparison; P7 pins a draft and runs adjudication | no experiment kind over **document cases**; no per-proposal result |
| Outcome provenance | `documents.filled` records `document_id`, page per read; outcomes carry inputs | an outcome does not list the reads behind **its** verdict |
| Python rules | `LocalPythonExecutor` (hardened child), `check_python_rule`, allowlist `math decimal fractions statistics datetime re` | no shared helpers; every rule re-implements dates, ratios, units |
| Expression evaluator | `jazzx_sdk.expressions` | its helpers are not shared with python rules |
| Indeterminate | assessment outcomes `pending_evidence` / `pending_calculation` | a python rule has no way to say "I cannot tell" except by raising |

## 3. Trial

A **trial** runs a chosen set of proposals, unmerged and unpublished, against a **case set** of real
document packages and records what each proposal did on each case.

**Case**: `{case_id, documents: [{document_id}], record: {...}, gold?: {...}}`. A *document case
dataset* is a dataset (`evaluation/datasets.py`) whose cases have this shape; documents are uploaded
once (`POST /documents`) and pinned by digest as in case runs.

**Run per case**
1. `document_ingest` once for the case, through the case-run path, reusing a prior read when the
   document digests match (`RerunBasis`). Ingest is the expensive step and is independent of the
   proposals, so N proposals cost one read.
2. `assess` the filled record with **published rules + the proposals as an overlay**: a function
   `overlay_pack(pack, proposals) -> pack'` builds the candidate rules in memory (the same conversion
   `merge-rules` uses, refactored out so both call it), marks them `source: trial:<trial_id>`, and
   never writes a store. A proposal whose rule id collides with a published one **replaces** it in
   the overlay and says so.
3. Record, per **(proposal, case)**:
   - `verdict`: `satisfied | violated | not_applicable | indeterminate` (indeterminate covers
     pending evidence, pending calculation, and a python rule that returned "unknown", section 8);
   - `reads`: the values the rule read, each with `field`, `value`, `document_id`, `page` (from
     `documents.filled`, or `input` when the record supplied it);
   - `missing`: fields the rule needs that nothing supplied (computed from the rule's declared `reads`
     minus what the case filled);
   - `error`: a python rule that raised or timed out, with the executor's reason.

**Eval-plane shape**: a new experiment *kind* `rule_trial` beside P7's `adjudication` kind. Entity
`{kind: "rule_trial", pack_id, draft_digest, proposal_ids}` pinned like P7 (the proposals' content
digests are part of the pin, so a re-extracted proposal is a different trial). The invoker is
`DocumentCaseInvoker`: ingest through case runs, then the overlay assess. The experiment's per-case
result carries the per-proposal rows above, so the existing comparison view (candidate vs baseline)
compares two trials, e.g. a proposal before and after a fix.

**Cost and concurrency**: ingest dominates, so cases run in parallel at the ingest's own limits
(`ExperimentRunner.concurrency`); assess is deterministic and free for conditions and python. A trial
reports its model cost (ingest) separately from its rule cost (none, unless a rule falls to "live").

## 4. Judge

- **Proposals tabs** (packs page) gain, per proposal, the trial summary (satisfied / violated /
  indeterminate counts, boundary hits) and an expandable per-case table, beside the generated test
  cases the proposal already carries. Route: `GET /authoring/review/{pack}/proposals/{id}/trials`,
  from the latest completed trial that included it.
- **Gold cases**: a case may carry `gold: {decision?, rules: {rule_id_or_proposal_name: verdict}}`.
  Gold is expected *per case and per rule*, so a disagreement is attributable to one rule. The tab
  highlights `disagree` (trial verdict differs from gold), `unexpected_indeterminate`, and
  `false_fail_at_boundary` (a violation within one band edge of the threshold, section 10).
- **Where gold comes from**: a DSCR gold-case set does not exist. The seed's `dscr_gold_cases` give
  per-case decisions and violated-rule ids for synthetic loans; they are a start for the *record*
  half but have no documents. The document half needs a **sanitized Acra loan package** (names,
  addresses, account numbers redacted or replaced consistently) that the user supplies, plus a
  one-page expected-outcomes sheet per case. **Decision for the user** (section 13).

## 5. Fix

Three operations, all producing **new proposals** that supersede old ones, never edits in place.

1. **Redo a subset**: the reviewer rejects selected proposals with a note; `POST
   /authoring/extract/{pack}/runs` accepts `redo: {proposal_ids, note}`, which re-extracts **only the
   clauses or sections those proposals came from** (their `source_refs`), with the note and the
   failing trial cases (inputs, expected, got) added to the generation prompt as feedback. A segment
   is re-read, not the whole corpus.
2. **Expand a partial rule**: `POST .../proposals/{id}/expand` regenerates one rule from its current
   code, its clause, and the cases where it was indeterminate or wrong. The prompt variant
   (`policy_code/expand`) is told which `missing` fields to compute from what the documents supply and
   to return "unknown" where it truly cannot.
3. **Lineage**: the new proposal carries `derived_from: <old id>`; the old one is marked
   `superseded_by`. Both live in the `StoredProposal` JSON blob (no migration). Creating a
   superseding proposal **starts a trial** for it over the last trial's case set, so the reviewer sees
   the effect of the fix without asking.

## 6. Merge, and provenance

- `merge-rules` merges only proposals that are **accepted and trialled**: each carries the id of the
  trial that justified it (the latest completed trial that included its current content digest). A
  setting (`require_trial: true`, default on for deployed tenants, off for local) lets a tenant keep
  the old behaviour; the refusal names the missing trial.
- The merged rule records `trial_ref: {trial_id, passed, cases, indeterminate}` in its
  extensions, so a published pack says which evidence justified each rule.
- **Verdict-to-document provenance on every rule outcome**: each `RuleOutcome` of an assessment lists
  `reads: [{field, value, document_id, page}]` for the fields that rule read. Built in `_run_assessment`
  from `documents.filled` (already keyed by field) and the record; no new reads. This is useful far
  beyond trials (the runs page, the adjudication citations), and it is the trial's `reads`.

## 7. The ladder

A rule is expressed in the lowest rung that can state it, and a pack author sees which rung each rule
landed on:

1. **conditions (Z3)**: compilable by `formal/`; exact, checkable, contradiction-pruned.
2. **python + library**: deterministic, tested, may need a helper or two.
3. **live**: a model judges at run time. Expensive, non-deterministic, last resort.

The extraction prompt prefers rung 1, then 2; a rung-3 rule is flagged for review. The trial reports
the rung of each rule, and the success metrics (section 10) are computed per rung.

## 8. The rules library: `jazzx_sdk.rules.lib`

**Mined, not speculated.** Step zero is a mining pass over every generated Python rule available
(the 51 above and the new runs' 26 and 25): extract the helper patterns they re-implement, count
them, and put only what appears **at least three times** in the library. The categories we expect
(to be confirmed by the count, not assumed):

| Category | Shape |
|---|---|
| Dates | `parse_date(v)`, `months_between(a, b)`, `within_months(d, n, as_of)`, `within_days` |
| Safe ratios and units | `ratio(n, d)` (None on zero or missing), `pct(v)`, `as_fraction(v)`, `as_percent(v)`; one rule for "0.75 or 75" |
| Rounding | `round_half_up(v, places)`, `ceil_to`, `floor_to` (money and ratios round the way the guideline says) |
| Bands and matrices | `band(value, edges, labels)`, `lookup(matrix, row, col)` with edge-inclusive semantics stated once |
| Enum normalisation | `norm(value, aliases)`: case, spacing, `purchase` vs `Purchase` vs `PURCHASE` |
| Counting | `count_where(items, pred)`, `count_in(items, key, values)` |
| Indeterminate | see below |

**Indeterminate convention.** A rule returns `True`, `False`, or `lib.UNKNOWN` (None under the hood),
with details naming what was missing: `return lib.unknown(missing=["dscr", "pitia"])`. The executor
maps it to the assessment outcome `pending_evidence` with those fields. A rule never returns `False`
for "I could not read it": that is the 45-of-51 pattern, and the library makes the honest answer the
short one (`need(ctx, "dscr", "pitia")` returns the missing names or None).

**Purity.** No I/O, no clock reads (`as_of` is always an argument), no randomness, no imports beyond
the allowlist. Every function is total on its input type and returns `UNKNOWN`/None rather than
raising on a missing value.

**How a rule reaches it.** The sandbox child is `python -I -S` with a restricted import set. The
library ships as **one stdlib-only source file** with a `LIB_VERSION`, written read-only into the
child's working directory at start and importable as `rules_lib` (added to `ALLOWED_IMPORTS`,
usable as `rules_lib.attr` like the other modules, so `check_python_rule`'s "module used only as
`module.attr`" holds). No SDK import reaches the child.

**Pinned per rule.** A python rule stores `lib_version`. A bump of the library re-runs every pinned
rule's tests (its generated cases and any gold) and lists the rules whose answers changed; a rule is
re-pinned only when its tests pass or a person accepts the change. The policy_code prompt gets the
**API rendered from the library's own docstrings** (one source), so what the model is told is what
exists.

**Shared with the expression evaluator.** `expressions/evaluate.py` and the library call the same
functions for ratio, percent, rounding and bands, so a condition and a python rule agree on `0.75`
and on `half_up`. The SMT compiler maps the library functions it can express (ratio, band) to terms;
those that it cannot (dates) keep a rule on rung 2, by design.

## 9. The Linux executor, a blocker for deployed use

`LocalPythonExecutor`'s Linux layers (network namespace, `RLIMIT_NPROC`, `RLIMIT_AS`) are untested:
macOS ignores them, which is where it has run. Deployed Plato is Linux. Until they are tested, python
rules **must not run in a deployed tenant**.

How it gets tested:
1. **A Linux container job** (`/tmp/japes_executor_linux_check.sh` becomes `scripts/executor_linux_check.sh`,
   run in CI on the deployed image's base): a suite of escape attempts run *as rules* through the real
   executor: open a socket, connect out, read `/etc/passwd`, write outside the cwd, spawn a process,
   fork-bomb to `RLIMIT_NPROC`, allocate past the memory limit, spin past the CPU limit, import a
   refused module, reach `__import__` through attribute chains. Each must be refused or killed within
   its limit and report a structured error, and a benign rule must still pass beside it.
2. **The library import path** works in the child on Linux (read-only cwd, `-I -S`).
3. **A boot check**: `python -m plato` runs a three-case probe at start (network refused, process cap
   holds, memory cap holds) and, on failure, **refuses to serve python rules** (conditions still
   serve), with the reason in `GET /info`. This is a `BOOT_CONTRACT` row, per the repo's rule that a
   behavior change is a change to what declares it.
4. The container needs the capabilities the network namespace requires; if the deploy platform
   cannot grant them, the plan says so up front and python rules stay off there.

## 10. Success metrics

Defined so a trial can compute them, per pack and per rung:

| Metric | Definition |
|---|---|
| **Computable coverage** | rules whose every `read` is filled by the case's documents or record, over rules applicable to the case; also per document class |
| **Deterministic share** | rules on rung 1 or 2, over all rules in the pack |
| **Trial pass rate** | over gold (proposal, case) pairs with a gold verdict: the share where the trial verdict equals gold; indeterminate counts as a miss against a decided gold, and as a hit against an indeterminate gold |
| **False fails at boundaries** | violations whose value sits within one band edge (or one rounding unit) of the threshold where gold says satisfied; reported by rule, since the cause is almost always rounding, units or inclusive-vs-exclusive edges |
| **Indeterminate honesty** | share of indeterminate verdicts whose `missing` fields are in fact missing (guards against UNKNOWN used to dodge a decision) |

## 11. Phases

| Phase | Scope | Gate |
|---|---|---|
| **R0 Mine** | the mining pass over existing generated rules; a report of helper patterns by frequency; the success-metric baseline on the 51 | numbers in hand before any library code |
| **R1 Library** | `jazzx_sdk.rules.lib`, the indeterminate convention, import allowlist, executor delivery of the file, prompt rendering, version pin and bump re-test; expression evaluator shares it | rules written against it pass on macOS and the Linux job |
| **R2 Provenance** | `reads` on every rule outcome; surfaced on the runs page | tests on the seed |
| **R3 Overlay and trial** | `overlay_pack`, `rule_trial` experiment kind, `DocumentCaseInvoker`, per-proposal results, comparison | a trial on the DSCR seed over synthetic cases |
| **R4 Judge** | proposals-tab trial view, gold schema and highlights | with the user's sanitized package (or synthetic gold) |
| **R5 Fix** | redo-subset, expand, lineage, auto re-trial | one fix loop end to end |
| **R6 Merge gating** | `require_trial`, `trial_ref` on the rule | |
| **R7 Linux** | the container job, the boot check, the `BOOT_CONTRACT` row | before any deployed python rule |

R0 and R7 do not depend on the rest and can start first; R1 can precede R3.

## 12. Risks

- A trial's value is only as good as its cases. Without real document cases the trial measures
  nothing the generated test cases do not; the sanitized package is the long pole.
- Overlay semantics: a proposal that replaces a published rule changes the **decision**, not only that
  rule's verdict. The trial reports the case's decision with and without the overlay.
- Library lock-in: a bad helper fixes one wrong answer in many rules at once. That is the point, and it
  is why a bump re-tests every pinned rule.
- Mining may show the repeated patterns are fewer than expected; then the library is small, and the
  larger win is the indeterminate convention and the ladder, not helper count.

## 13. Decisions for the user

1. **Gold cases**: will you supply a sanitized Acra package (and an expected-outcomes sheet), or do we
   start on synthetic documents rendered from the seed's gold loans (weaker for the document half)?
2. **`require_trial` default**: on everywhere, or only deployed tenants?
3. **Library home**: `jazzx_sdk.rules.lib` as proposed, shipped inside the SDK and versioned with it,
   or its own distribution so a pack can pin a library version independently of the SDK release?
4. **Order**: R0 (mine) then R1, or R3 (trial) first so the 51 existing rules get judged before the
   library changes what is generated?
5. **Deployed python**: confirm python rules stay off in deployed tenants until R7 passes.
