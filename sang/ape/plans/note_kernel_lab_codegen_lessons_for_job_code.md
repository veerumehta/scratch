# Note: kernel-lab JTBD-to-code generator work, and what fits our job-to-code path (2026-10-28)

Read-only; no spend. Sources: kernel-lab `dev`, 9bc68fb2a9, d9772ff20c, b69c5000cd, 214f12ed95 (prompt partials
`codec_lessons.md`, `income_asset_figures.md`, `type_coercion_guide.md`, and `reference_examples.py`). Nothing copied; ideas only.

## 1. What they do
- **Lessons as generator rules (9bc68fb, 214f12e).** The generator prompt carries ~640 lines of named, general rules (G-STATUS,
  G-NOTE, G-STEPS, G-PREREQ, G-ANSWER, G-ROOT...) harvested from earlier tuning of one lender (Pulte) and review-loan defects.
  Each candidate went through a skeptic pass: general vs lender practice, already covered, conflicts with the current JTBD set.
  Result: 284 candidates, 24 added, 70 merged, 47 runtime-only, 40 lender-specific, 28 one-check-only, 6 conflicting left out.
  The rules are "how to turn a JTBD sentence into an ask" (when a note is an ask, when a missing paper is a hold, one ask per
  paper, release only on same-subject evidence, build every output before deciding status, a missing figure is unknown never 0).
  214f12e rewords eight so the JTBD's own wording wins ("the JTBD's grouping wins both ways").
- **Worked example per check (b69c500, d9772ff).** Each check's prompt gets one tuned, hand-validated evaluator plus the JTBD text
  it was tuned against, from a frozen release (git tag, cached by content hash). Pick: same mnemonic, else closest by tf-idf cosine
  over skill + requirement text (same section first, then any). The prompt says: use it for HOW (table access, matching, wording,
  release tests), implement only what the current text says, take numbers and wording from the current text, current text wins.
  Only the first attempt carries it; the retry is slim. Failure to load costs that check its example, never the run. The library
  label and hash go in the run fingerprint. Dry run: 107 of 183 same mnemonic, 73 closest in section, 3 any section.

## 2. What fits our path
Our path: `policy_code/job_prompt.md` (one job to one `check(ctx)`, helpers from `jazzx_sdk/rules/lib.py`: known/gaps/unknown/same/
at_least/within/band/ratio/percent/monthly/months_between), `regenerate.md`, `case_author.md`, and `prompt.md` for segments. Our prompts
are 14 to 20 lines; they have no named rules and no examples. Our rules are pure functions over typed facts returning True/False/
unknown, so most of their rules (asks, conditions, releases, LOS/1003 matching) do not apply. What transfers:

| Idea | Fit | Why |
|---|---|---|
| Worked example per check | High | Biggest gap in our prompt: the model sees helper names, never a finished rule for a matrix, aggregate or cap. |
| Current text wins, example is "how" not "what" | High | Our figure gap (rule rounds or drops a figure the clause prints) is the same failure from the other side. |
| Frozen reference, never the live tree, fingerprinted | High | Our generated code is overwritten each regen; a reference must be a pinned, reviewed set recorded in `bundle.json`. |
| Never fatal, drop the example on failure | High | Matches our tolerant-first rule. |
| tf-idf nearest pick, same section first | Medium | We have `jtbd_match`; but a stable per-kind example (below) beats text similarity for our few job shapes. |
| "Build every output, decide status last" | Medium | Our `(bool, dict)` return: report all values used even on False. |
| "Missing figure is unknown, never 0 or the declared value" (G-PRESENT) | Already ours | `gaps`/`unknown` in prompt; keep. |
| Skeptic pass over candidate lessons (general / covered / conflicting) | High | The process, not the text: use it before adding any line to our prompts. |
| Ask/condition/release/matching rules (G-ANSWER, G-SHARED...) | None | We emit no asks; those are for their evaluator shape. |

## 3. Our gaps and which idea helps (from the regen-5 comparison)
- **Matrix jobs without values** (Platinum LTV/FICO/DSCR tiers, K-Studio splits to 4 jobs, ours 1): the job states the grid in
  prose, the code gets one threshold or none. A worked matrix example (axes as `band` lookups over a table printed in the clause,
  one cell per assertion test) fixes the shape; the job-writer needs a "one job per tier or one job with the table in its checks"
  line (SDK prompt).
- **Aggregate cap jobs** (stacking of caps, 75% Condo/Two-Unit cap, lowest-cap-governs; reserve triggers combined): needs an
  example of `min()` over named caps with each cap's value reported in the dict. The cap's governing rule itself is a reading
  (items 3, 8 on the readings list): the example must refer, not choose.
- **Missing caps and footnotes** (cash-in-hand, ARM terms, prepay by state, HELOC CLTV): a code-side lesson is "every footnote is its
  own check, constant read from the clause, reported in the dict". The main cause is upstream, in the job writer (no job exists).
- **Figures the code writes that the text does not print:** the "take every figure as printed" line exists; a worked example showing
  a constant with its source clause id in a comment gives `figure_lint.py` something to verify.

## 4. What a worked example per check looks like for Acra
Per **job kind**, not per mnemonic (we have ~200 jobs, kinds few; library of ~6 reviewed rules, each with its job text):
1. Single threshold with unit (`DSCR >= 1.0`, `percent`, `at_least`, unknown on a missing field).
2. Matrix cell (CLTV cap by program x purpose x FICO band x property type): grid as a literal table copied from the clause, `band`
   per axis, an explicit not-listed cell returns unknown not False, dict reports axis values and cap.
3. Eligibility list (ineligible states, property types): `same(value, *options)`, as the existing `ineligible_state` rule.
4. Aggregate cap: several caps as named constants, `min`, dict of each cap's value and which governs (refer when the guideline is silent).
5. Conditional footnote: applies only when a trigger fact is true, otherwise returns True (not applicable) rather than unknown.
6. Date/seasoning: `months_between`, both dates required.
Each example = job text (checks, source clause) + the rule + its test cases (a ctx and expected, one each side of every threshold).
The prompt wraps it as theirs does: "how to code, not what; current job text and its clause win; take figures from the clause."
Selection: by the job's kind (job-kind data exists), not by similarity, since our shapes are few and a wrong nearest pick is the
risk their dry run measured (no reference serves more than 9 of 76).

## 5. What would not transfer
- Their JTBD shape: free-form requirement text per investor with "CONDITION"/"obtain" sentences, condition ids, `jtbd_clause_map`,
  `max_items`, ask wording and parties. Ours: typed checks with computable positions, clause unit ids, a single True/False/unknown.
- Their data: LOS/1003/AUS tables, DU lists, tradeline identity, payment matching, letters and signatures (G-SIGN, G-LETTER...).
- Lender-tuned code as the library: our library must be Acra-reviewed rules, not Pulte evaluators; a cross-customer example is fine
  for shape but must be scrubbed of lender wording (pack names carry the customer only in packs).
- Their 640-line prompt: our context per job is small and we pay per rule; a short, per-kind block beats a long rule list.

## 6. What I would change, by owner
**Route to sonnet-runtime (SDK prompt and code):**
1. `policy_code/job_prompt.md` and `regenerate.md`: add an optional `{example}` slot (empty when none) with the "how, not what" wrapper;
   keep it out of the retry as theirs does if the context cost shows.
2. A loader for per-kind worked examples from pack data (see below), never fatal, listed in `bundle.json` with a content hash.
3. Prompt lines: "report every figure used in the dict"; "a footnote or cap the clause prints is its own check"; "a cell not printed in
   the grid is unknown". The job-writer lines (every figure/cap/footnote decided by some check; matrix as one job per tier or a
   table in the checks) are already routed.
4. Skeptic pass before any new line: general vs Acra-only, already covered, conflicts with a job set.

**Mine (pack data, after sonnet-runtime has the slot):** pick and write the ~6 reference rules per kind from existing reviewed Acra
rules (`from_jobs/*`: `ineligible_state` for the list kind, a matrix cell, a ratio threshold), their job text and tests; gold-case
additions only with your approval. Scrub names; store as pack data beside the prompt files.

**Needs a measuring run (needs the user's approval, unspent so far):** regenerate the same job subset (matrix, aggregate and
footnote jobs, ~25 to 30 jobs, one program) with and without the examples, same models, and compare: rules that state the printed
figures, matrix cells correct, unknown-vs-False on missing facts, test cases passing, code without a job, cost per job (an example
adds a prompt of maybe 2-4k tokens). Include a repeat of the no-example arm ("3c") so a difference is sized against noise. I will
not run it without that approval.

## 7. Caveats
- Kernel-lab's gains are claimed, not measured against a no-example arm in these commits (dry runs only count picks); our measure should be.
- An example can anchor the model on its figures; their wrapper forbids copying but the check is ours: scan generated rules for
  constants that appear in the example and not in the clause (extends `figure_lint.py`).
