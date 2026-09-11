# Changelog

All notable changes to JACI (JazzX Contextual Intelligence) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Entries are intentionally terse; `git log`/`git diff` carries the full detail.

## [Unreleased]

### Changed — japes 2.5.1 (branch `japes-2.5.1`, needs an unreleased japes)

- **An unstated prepayment-penalty structure now denies where a state requires a buyout.**
  `prepayment_penalty_requested` defaulted to `"no_prepay"`, the one value satisfying every
  `DSCR-PPP-*` rule, so a loan whose prepay terms nobody had asked about reported clean in all
  13 states with a buyout requirement. The default is `"unspecified"`, which satisfies none of
  them. Not `None`: that reads INDETERMINATE and `check_compliance` skips the rule silently,
  restoring the same pass. Four new cases build the context through `LoanApplication` so the
  default is what the rule sees; every existing case set the field itself, which is why the
  suite stayed green over it.

- **Pack paths resolve through one seam instead of counting directories.** Modules computed
  their own root by walking up from `__file__` -- `parents[4]`, `parents[5]`, `parent` five or
  six times -- each count correct only for the nesting of the file it sat in, so moving a
  module breaks its path and nothing else. `jaci.paths` replaces that for DSCR:
  `pack_root("dscr-core")`, `packs_dir()`, `prompts_dir()`, `repo_root()`.

  The mechanism is japes' (`jazzx_sdk.pack.roots`): marker-based discovery, an environment
  override consulted first, and `-`/`_` reconciliation so `dscr-core` finds `dscr_core/`.
  Every domain needs it and none of it is jaci's, so what stays here is the vocabulary -- the
  variable names, and that prompts live in `prompts/`. That is also what makes a *published*
  pack reachable later without touching jaci: `resolve_packs_root` is where a pack-store
  lookup lands, in japes.

  DSCR's six sites are converted. The rest of the repo still counts directories; converting
  them is mechanical but wide, and each scenario deserves its own pass.

### Fixed — pack corpus corrections (branch `japes-2.5.1`)

Found by adversarial review of the japes branch, which vendors copies of `dscr_core` and
`ci-spread-core` as plato seed data and so read them properly for the first time.

- **Two C&I checklist requirements were extraction debris.** `checklist_ci.yaml`'s
  Purpose-Specific Documents section carried `- schedule` and `- available)` where the source
  PDF has "Equipment purchase: vendor quote / invoice, purchase agreement, delivery schedule"
  and "Acquisition: LOI, purchase agreement, target financials, quality of earnings (if
  available)" -- two wrapped table cells whose first lines the extractor dropped, keeping only
  their continuations. Any package assessment asked for documents literally named `schedule`
  and `available)` and never for the two that were listed. Restored verbatim from the source;
  all twelve sections audited against it, and those are the only two wrapped cells in the
  document.

- **`CI-ABL-MIN-AVAILABILITY` enforced half of what it says.** "10% of borrowing base or $2M,
  whichever is greater" is both legs at once, and only the percentage was encoded, so a $10M
  base with $1.5M available read SATISFIED against a floor of $2M. The source document states
  the dollar leg (`min_excess_availability: "$2M or 10% BBC"`); it is now an `all_of`, and the
  conductor passes the dollar figure beside the ratio it already computed.

  Both figures share one guard. `BorrowingBase.excess_availability` defaults to `0.0`, so a
  deal with no borrowing-base data would have been reported as $0 available and the dollar leg
  returns VIOLATED -- which dominates the missing-data INDETERMINATE inside `all_of`, a denial
  manufactured from a figure nobody supplied. Also recorded in the rule: the percentage is
  computed against total availability, not the borrowing base its description names.

- **A 2-4 unit application inherited the single-unit prepayment gates.**
  `residential_unit_count` defaulted to `1` with nothing reconciling it against
  `property_type`, so `{property_type: two_to_four_unit}` with the count unset tripped
  Mississippi's single-unit PPP restriction and Ohio's `<= 2` on a loan neither rule covers --
  a denial in the restrictive direction, which the Governor enforces. The rules were authored
  correctly; the schema was the defect. The count is now derived from `property_type` where
  that is unambiguous and left unset for a 2-4 unit property, so the gate is INDETERMINATE: a
  data gap rather than a verdict.

- **`DSCR-SUB-1-DSCR-FICO` was outside the drift lint.** It hardcoded `640` with no
  `profile_custom_key`, while its twin `DSCR-NO-RATIO-FICO` -- same sentence in the source,
  same threshold -- declares one. Recalibrating `profile.custom.fico_min_no_ratio` would have
  left this rule on the old number with the lint green. Nine twins covered now, not eight.

- **Provenance comments named gitignored plan documents**, in nineteen places across eleven
  pack files. Rewritten to name the subject instead, keeping every phase and FR reference.

- **`ENCODING_NOTES.md` contradicted the corpus beside it**: it said no rule used
  `all_of`/`any_of` and that the state prepayment rules were unauthored (ten rules use them,
  nine of those being those rules), that `pack_manifest.yaml` was "still not wired" (it
  declares both corpora), and that eight profile twins were covered. Counted and corrected,
  along with a false provenance claim on the owner-compensation ceiling: `addbacks.yaml`'s cap
  is symbolic and this pack ships no profile, so the literal is the number's only home.

### Fixed — pack corpus, second review pass (branch `japes-2.5.1`)

- **An Illinois loan could omit the rate its own PPP rule gates on.** `DSCR-PPP-IL-2`'s `all_of`
  applicability reads `interest_rate > 8`; an absent rate makes that limb INDETERMINATE, which
  leaves the gate neither satisfied nor blocking, so `check_compliance` skips the rule and a loan
  that should have been denied passes in silence. ENCODING_NOTES section 1a settled the same
  problem for the attestation booleans by choosing defaults that block; a rate has no safe
  default, so it is required exactly where a rule reads it -- Illinois, individual borrower, over
  $250,000 -- and the gap surfaces as a validation error at intake instead.

- **"Less Cash Taxes" was bound to the accrued book tax.** `spread_template_rb.yaml` pointed the
  row at `income_tax_expense` off the income statement while
  `income_taxes_paid_net_of_refunds` sits in the same pack's chart of accounts as the cash-flow
  figure the row asks for, so any deferral, refund or timing difference put the wrong number in
  the Adjusted Fixed Charge Coverage numerator under a label saying "Cash". `Cash Interest` eight
  lines down is deliberately left unbound on exactly this objection.

- **Two warning rules described a band they do not encode.** `CI-LEVERAGE-WARNING` said "above
  3.0x but below 3.5x" and `CI-FCCR-WARNING` "between 1.15x and 1.25x", each with a single
  threshold predicate, so both also fire well past the stated band. The behaviour is a defensible
  superset (the hard floor fires alongside) and the text is what a caller renders, so the
  descriptions now say what the predicates are.

- **Counts corrected.** ENCODING_NOTES' rule-shape table said the 14 PPP rules were "8 plain
  `expression`, 6 `all_of`" and a later line said "6 of the 14" while naming nine; it is 5 and 9,
  which is what makes section 3's "10 of the 41" add up. And `metrics.yaml`'s header said what
  stays in Python is "behavior, not knowledge" while seven ids the spread templates reference
  resolve only against `analytics.py::compute_metrics` -- definitions, not behaviour, now recorded
  as the gap they are.

### Fixed — the unit-count field, both directions (branch `japes-2.5.1`)

- **`residential_unit_count` had a hole on each side, and the first fix opened the second.** It
  defaulted to `1`, so a `two_to_four_unit` application that left it unset read as single-unit and
  tripped Mississippi's single-unit prepayment restriction and Ohio's `<= 2` on a loan neither
  rule covers: a wrong denial. Leaving it unset instead closed that and opened the opposite hole,
  which is worse: the gates read INDETERMINATE, `check_compliance` skips a rule whose gate is not
  SATISFIED and records nothing, so a genuine two-unit Ohio property cleared with a penalty Ohio
  requires bought out -- permissive, and silent.

  Neither direction is a default's job. A 2-4 unit property's unit count is known at intake and
  three rules read it, so it is required there, which is the same answer `interest_rate` got for
  Illinois and for the same reason: require the field where a rule reads it. The Illinois fix
  should have been generalized to this family at the time and was not.

  The tests moved to the production path with it. Every case in the eligibility table hands the
  evaluator a context dict and sets the count itself, which is why neither failure appeared there.

- **Two documentation claims corrected.** `workbook_layout.yaml` said every `key` resolving
  against the chart of accounts and metric catalog "is this file's own load-time acceptance check
  (see workbook_layout.py's validator)" -- there is no such validator and no such file:
  `load_workbook_layout` checks shape only, so an unresolvable key loads clean and writes a
  labelled empty row. It is an authoring rule, now stated as one. And ENCODING_NOTES still
  described `residential_unit_count` as defaulting to `1`, which is the behaviour the first fix
  above removed.

### Fixed — interest-only FICO floor, and three claims (branch `japes-2.5.1`)

- **`DSCR-IO-MIN-LOAN` enforced half of what it says.** Its description reads "minimum loan amount
  of $250,000 and minimum FICO 640" and the condition checked only the amount, so an
  interest-only loan at FICO 620 returned SATISFIED. `profile.custom.fico_min_io` was authored at
  640 with no rule reading it, which is the same omission seen from the profile side. And
  `rule.description` is not inert prose: the policy registry returns it verbatim as guidance
  text, so a caller was told a 640 check ran when none did. Both legs are encoded now, each
  declaring its profile key.

  This needed a japes fix first: `find_profile_literal_drift` only inspected a rule's top-level
  `condition`/`applicability`, so wrapping the rule in an `all_of` would have moved *both*
  declarations out of the lint's reach while appearing to add one. The lint walks composites as
  of japes `e0f8442`, and this pack's drift test now uses its traversal rather than a second copy.

- **Three claims corrected.** ENCODING_NOTES enumerated `PropertyType` as including a bare
  `condo`; there is no such member (`warrantable_condo` and `non_warrantable_condo` are the two
  spellings, which is what every rule matches on) and the bare-state prepayment rules were
  justified by that list. `core.yaml` said FCCR, ABL and LIEN "remain in registry.py until
  similarly extracted" after `conventions.yaml` had authored all three beside it, sending a reader
  editing an FCCR threshold to a file the deployment does not have. And `checklist_ci.yaml`'s
  provenance field named `sha256` held sixteen hex characters, so it is `sha256_prefix` now --
  the full digest is not recoverable from it and nothing verifies the source against it.

### Fixed — a No Ratio file could clear the >$2M DSCR floor (branch `japes-2.5.1`)

- **The first high-severity finding of this arc, and a hazard the corpus documents.**
  `DSCR-OVER-2M-DSCR` states the floor as a `ratio` condition, which reads INDETERMINATE on a No
  Ratio file, so `check_compliance` skipped it: a $2.5M no-ratio loan returned `allowed=True` with
  zero violations and zero warnings, while the same loan with a documented DSCR of 0.9 was denied.
  ENCODING_NOTES G2 describes exactly this and prescribes a twin rule keyed on
  `dscr_documentation_type`; that fix was applied to `DSCR-SUB-1-DSCR-CLTV` and `-FICO` and not
  here. `DSCR-OVER-2M-NO-RATIO` is the third site.

  Swept the corpus for the same shape: two rules have a bare `ratio` condition, and the other,
  `DSCR-HIGH-LTV-DSCR`, needs no twin because a no-ratio file is capped at 75% CLTV, below its own
  `cltv_pct > 80` gate — verified by running a no-ratio file at 85% and watching the cap deny it.
  Masked rather than absent, so the rule now records that raising the cap would open the hole.

- **`evidence_types.yaml` was never declared.** The file ships with seven ids in the shape the
  loader reads and the manifest named no `evidence_types:` key, so `Pack.evidence_types` was empty
  while `convergence_evidence_required` in the same manifest named three of those ids. The tool
  registry derives its requestable set from that list, so an Investigator built from this pack
  could request no evidence at all.

- **Four stale claims in the pack notes**, three of them made stale by this branch: the paragraph
  saying nested `profile_custom_key` declarations are not lint-checked (they are, as of japes
  `e0f8442`, and this corpus depends on it — which also means the four PPP literals left unlinked
  for that reason can now be linked); the rule-shape counts, now stated corpus-wide rather than
  per-group because the per-group breakdown drifted on every rule added; and `fico_min_io`'s place
  on the orphaned-keys list, which it left when the interest-only rule grew its second leg.

### Fixed — an overlay evaluating as core (branch `japes-2.5.1`)

- **`RB_CI_OVERLAY` displaced the institution policy it narrows.** It ships in
  `conventions.yaml` inside the `dir: policies` corpus, so a consumer hydrating
  `DefaultPolicyExpert` from `Pack.policy_registry` got all six policies as core — and field
  precedence is registry order, so the overlay's `RB-CI-LEVERAGE-CEILING` claimed `leverage_x`
  ahead of `CI_CORE_LEVERAGE_POLICY` purely because `conventions.yaml` sorts before `core.yaml`.
  Both core leverage rules stopped running: `leverage_x=3.2` produced zero findings where
  `CI-LEVERAGE-WARNING` should have fired. Silent, and it survived only because the overlay's
  placeholder 3.5x happens to equal the core ceiling.

  The pack already declared the distinction: `RB_CI_OVERLAY` is `scope: product` where the core
  policies are `scope: institution`, and `PolicyScope`'s own docstring states the ladder
  ("product takes precedence over institution"). Nothing in japes read it. `Pack.core_policy_ids`
  and `Pack.overlay_policy_ids` (japes `6e5cc24`+) now derive from it, so hydration is mechanical
  rather than guessed. With them, core governs by default and `program_id: rb` makes the overlay
  supersede core exactly as its `supersedes_core_rule` declares — which is also what fixes
  `RB-CI-FCCR-FLOOR` never evaluating.

- **`evidence_types.yaml` authored for dscr_core**, from the eight ids its own rules already name
  in `parameters.evidence_types`, and declared in the manifest. Until now `Pack.evidence_types`
  was empty for this pack, so a tool registry built from it derived a requestable set of nothing —
  the same gap ci-spread-core's declaration was added for one round earlier, in the half of the
  family that was missed.

- **Three claims and a binding.** `CI-ABL-MIN-AVAILABILITY` described its percentage leg as "10%
  of borrowing base" when it is computed against total availability: on a $30M base with the line
  capped at $10M, $2.5M clears both legs while 10% of the base is $3.0M. Restated rather than
  re-encoded, because a base-relative leg needs a figure no producer supplies and picking that
  denominator is a credit decision.

  The description names *both* forms. Saying only "borrowing base" told a caller a test had run
  that had not, since this text is returned verbatim as guidance; saying only "total availability"
  was the opposite error, making the pack misstate its own authority, which records "$2M or 10%
  BBC". An SME comparing pack to source has to be able to see the gap, so it is written down. "Cash Interest" is bound to `interest_paid`, like its tax twin
  three rows up and as both are already bound elsewhere in the pack. And ENCODING_NOTES' `all_of`
  enumeration named ten of twelve rules, omitting the two added since, while its version note
  stopped at 1.2.0 where the file ships 1.3.0.

### Fixed — a vocabulary mismatch, two undeclared fields, contradicting rating bands

- **The ontology named a `loan_type` value no matcher accepts.** It enumerated
  `abl | revolver | term_loan | ddtl`, while all five matchers in the pack spell the fourth
  `delayed_draw_term_loan` (diagnose_map's three term-loan rules, two manifest `applies_to`
  lists). A facility authored to the pack's *own* documented vocabulary matched none of them and
  fell through diagnose_map's fallback to **the ABL revolver playbook** — wrong guidance for a
  delayed-draw term loan, not an empty result. `ddtl` appeared in exactly one place; it is gone.

- **Two fields rules read were declared nowhere.** `CI-ABL-MIN-AVAILABILITY`'s first leg reads
  `excess_availability_pct`, which appeared only at its use site, so the rule returned
  INDETERMINATE on any context lacking it — and `check_compliance` skips that without recording,
  meaning the rule could return VIOLATED or INDETERMINATE and *never* SATISFIED. Declared on
  `BorrowingBaseResult` as the derived figure it is. Sweeping every field the pack's rules read
  against what the ontology declares then found a second, `owner_compensation_addback_amount`,
  which no finding had reported; that sweep is now clean.

- **`term_loan.md` contradicted itself by a full notch.** §term-005's leverage bands rated
  3.5–4.5x SPECIAL MENTION and >4.5x SUBSTANDARD; §term-007 rates 3.0–3.5x SPECIAL MENTION and
  >3.5x SUBSTANDARD. A borrower at 4.0x read one from each, and both reach the Reasoner as
  guidance on the same playbook. §term-007 is the one that maps onto the encoded policy
  (`CI-LEVERAGE-WARNING` 3.0x, `CI-LEVERAGE-CEILING` 3.5x), so §005 keeps its structuring
  guidance and defers the rating scale to it rather than restating it differently.

- **`DSCR-ITIN-LOAN-MAX`'s $1,000,000 is linked to the profile** as every other loan-amount bound
  in the file already was — and as ENCODING_NOTES already claimed it was, while it was a bare
  literal the drift lint could not check.

- **The missing-field deferral said where it does not hold.** ENCODING_NOTES discharged the
  silent-skip risk on `residential_unit_count`/`interest_rate` by requiring them on
  `LoanApplication` — which is authoring-repo code. The pack ships only rules, so any other
  consumer, including plato's vendored copy where no such schema exists, still gets the skip:
  four of the fourteen PPP rules report NOT_APPLICABLE instead of denying. The IR cannot gate on
  a field's presence, so the pack cannot close it; it now says so.

- **The truncated-digest rename covers all four sites** (`source_sha_prefix`, the scaffold's
  `sha256_prefix=`, the ontology field), not the one renamed last round, and `abl_revolver.md`
  carries the availability caveat the rule's own description got. Plus corrected counts: seven
  ratio thresholds not six, and six of eighteen profile keys unreferenced rather than two.

### Fixed — the fourth `applies_to`, and counts my own edits made stale

- **The `ddtl` vocabulary pass covered three of four `applies_to` lists.** `pb-ci-loanpkg-001` was
  `[abl, revolver, term_loan]` — every facility type except the one term-loan variant — while
  `pb-ci-memo-001` beside it carries all four. The ontology comment written in that same pass
  claimed "the manifest's two playbook `applies_to` lists", counting the two that already had the
  long spelling and treating the manifest as covered.

- **Counts corrected in the row that was correcting counts.** Fixing "6 ratio thresholds" to 7 left
  "11 custom scalars" and "those 18 keys" stale, because the same change added
  `itin_loan_amount_max` to `custom:`. The profile holds 7 + 12 = 19; six are still unreferenced.
  And `term_loan.md`'s new parenthetical called §term-007 "the only [rating scale] in this
  playbook" while §term-004 also assigns ratings — agreeing ones, so nothing contradicts, but the
  claim was wider than the file.

### Changed — japes 2.5.0

- **The `[litellm]` extra is gone from the japes pin.** Not optional: japes 2.5.0 removed the
  extra entirely, so `japes[litellm] @ ...` no longer resolves at all. Claude is reached by
  japes' own native Agents-SDK model now. Removing the stale `litellm` from an existing
  environment is also required -- it pins `openai<3.0.0` while 2.5.0 pulls `openai` 3.x, which
  `pip check` reports as a conflict until it goes.

- **The MLflow reporter moved too.** `jazzx_sdk.evaluation.reporters.mlflow` became
  `jazzx_sdk.evaluation.backends.mlflow.reporter` -- japes 2.5.0 put its MLflow
  implementations behind a backend boundary. The old path raises `ModuleNotFoundError`, so
  `JACI_EVAL_MLFLOW=1` would have failed at the import rather than at anything to do with
  MLflow. Second of the two stale japes paths in the repo, after `queue_processor`.

  The `run_eval_anthropic` header no longer claims the litellm extra is required, since
  japes resolves an Anthropic `model_name` to its own native model now.

- **`uv.lock` regenerated, which is the only way it moves.** Dropping the extra from
  `pyproject.toml` left the lock still requesting `japes[litellm]`, so `uv sync --frozen`
  would have failed in CI before a test ran -- and the lock still pinned japes at 2.4.9.
  `uv lock` alone keeps the old commit and `uv lock --upgrade-package japes` does not move
  it either, both confirmed here; the lock has to be regenerated, exactly as `tests.yml`
  already documents. Now at japes 2.5.0 (`e61fbc2`), with `litellm` gone entirely and
  `openai` 3.11.0, `openai-agents` 0.22.2 and `gitpython` 3.1.62 following from it. The
  file shrinks by ~300 lines: litellm was pulling `tiktoken`, `tokenizers`, `boto3` and
  `regex` behind it.

- **A pre-push check, as japes has.** Five steps: lock consistency, open Dependabot alerts,
  japes freshness, the suite, and the adversarial review. The review script is *referenced*
  from the japes checkout rather than copied, since it takes the repo name as its only
  argument and works in any checkout; a copy would be a second thing to keep in step.

  Installed by `scripts/local/install_hooks.sh`, which wraps rather than replaces: jaci's
  `pre-push` is git-lfs's and overwriting it stops LFS objects uploading, silently, until
  someone clones and finds pointer files. Checks run first and LFS second -- uploading
  objects for a push the suite is about to reject leaves the remote holding objects for a
  commit that never arrives.

  The freshness step exists because `uv.lock` pins japes to a commit even for `@dev`, so a
  laptop on an editable install and CI run different japes. It reads PEP 610's
  `direct_url.json` for that; a first version scanned `distribution.files` for
  `__editable__` and was silently false for this install.

- **`QueueSettings` moved with the queue package.** `jazzx_sdk.queue_processor` became
  `jazzx_sdk.queue.processor` in japes 2.5.0, one of thirteen root modules that moved into
  packages. Imported from `jazzx_sdk.queue`, which re-exports it -- the package path rather than
  the submodule, so a later reshuffle inside `queue/` does not reach us. This was the only stale
  japes path in the repo; the other fourteen moved names appear nowhere here.

- **`spread_approval` is registered as a signal tag.** japes 2.5.0 stopped copying a `Feedback`
  category straight into an `ImprovementSignal` tag, because an unregistered category produced
  signals the Curator's router silently rejected -- so these approvals were being dropped rather
  than routed, and the mapping to `other` is what made it visible. `register_signal_tags` (new in
  2.5.0) exists for exactly this: the capability registers its own tag at import, before any
  approval can record feedback, and registration is additive so it cannot disturb another pack's
  taxonomy.

  Not a workaround for the change -- the change surfaced a real loss. The tag now survives
  `to_signal()` and the signal routes.

## [0.20.6] - 2026-08-31

Pinned onto the current japes dev, and given a way to find out when that breaks.

- **A test workflow.** jaci had none: the only CI was a nightly Docker build, so nothing verified a
  branch and nothing caught a japes regression. jaci pins `japes @ dev`, a moving ref, so a green
  jaci commit can go red without jaci changing at all -- the workflow runs on PRs, on pushes to
  dev/main, and nightly, and it deliberately does *not* use `uv sync --frozen`: resolving japes
  fresh is the entire point, and a frozen install would test yesterday's japes forever. It prints
  the japes version under test so a red nightly says which one, without a re-run.
- **`uv.lock` refreshed onto japes 2.4.9** (`5fa4d43`), up from 2.4.6 (`9c28116`), 18 commits
  stale. `uv lock --upgrade-package japes` will not move an already-resolved git rev -- nor will
  `--refresh-package`, `uv cache clean`, or `--no-cache`; the lock had to be regenerated. Same 174
  packages, 26 routine patch bumps alongside.
- **`dscr_core` declares its policy corpus** (`policies: {dir: policies}`), so its 41 eligibility
  rules reach `Pack.policies` instead of being loadable only by path. Needs japes 2.4.9's
  `PackManifestLoader.policy_files()`, which is why the lock refresh comes with it. The
  `policies/registry.py` that Phase 1 of the DSCR plan called for is no longer needed -- it existed
  only to hold a list.
- **`ci_lending` ontology v0.2.1: two covenant formulas that could never resolve.** `FCCR` read
  `taxes` while the entity declares `tax_expense` -- and its own `inputs:` list already named
  `tax_expense`, so the formula disagreed with its own declaration. `scheduled_principal` was
  divided by in both `FCCR` and `DebtServiceCoverage`, declared nowhere, and absent from both
  inputs lists. Neither raises: the metric silently fails to resolve and every covenant reading it
  comes back indeterminate, which reads as a broken evaluator rather than a naming mismatch. Found
  by japes' `lint_pack` run against the authored pack, which is what that check exists for.

- **Local `poetry.lock` removed.** Already gitignored and untracked, so nothing consumed it; it sat
  on disk pinning japes 2.4.0 and misleading anyone who read it.


- **Model-data overlay** (`jaci.sdk.model_overlay`): registers the Claude 5 family
  (`claude-opus-5`, `claude-sonnet-5`, `claude-fable-5`) with the SDK at package import, ahead of
  JAPES shipping them. Prices and limits transcribed from Anthropic's own pages (verified
  2026-08-23), not from memory or a summary. Without it these models are unknown to JAPES: costing
  worst-cases at `DEFAULT_PRICING` (a 1M-in/100k-out Opus 5 call reports $37.80 instead of $7.50),
  the context window is unknown so compaction falls back to a fixed threshold, and `thinking_shape`
  defaults to the legacy `enabled` request shape, which these models reject outright.

  The overlay only ever **adds** — each entry is skipped when JAPES already knows the model, so it
  becomes a no-op and can be deleted once the SDK ships these rows. Guarded by a test, because
  `register_model_card` overwrites unconditionally: if the overlay stopped checking first it would
  silently outrank the SDK's own data.

## [0.20.5] - 2026-08-22

- Dependency refresh: japes 2.4.4 → 2.4.6, litellm 1.98, plus scipy/ruff/narwhals bumps and the
  boto3 stack litellm now pulls. **anthropic held at <1.0.0** (a deliberate upper cap, against the
  usual ">= floors" rule, documented inline): 1.0.0 removes `temperature` from
  `messages.create()`, which japes' Anthropic providers still pass, so a live Claude call raises
  `TypeError`. Neither suite catches it — every anthropic test on both sides mocks the client, so
  japes was fully green with the real path broken; only a live smoke call surfaced it. Lift the cap
  once japes migrates to the 1.0 API (`temperature` has no direct equivalent; the nearest concept
  is the new `output_config.effort` tier).

- Consolidated ci_spread's two spreading orchestrations into one. The scenario declared its own
  five-step `spread` pipeline and a `CIConductor.run_spread` to execute it, while every spread
  button in the demo actually ran the commercial-lending capability's `run_cl_spread`. The
  scenario-local one had no caller at all -- but its *descriptor* was what the Concepts tab
  diagrammed as the demo focus, so the diagram showed a pipeline nothing executed. The Concepts
  focus now points at `CL_SPREAD_PIPELINE` (the live path), and `run_spread`, its components, the
  `CI_SPREAD_PIPELINE` descriptor and the pack's `spread` entry are gone.
  **Retired with it** (they only ever ran in that dead path, and are not in `run_cl_spread`):
  entity-extraction/KG during the spread phase, and canonical persistence of the spread. If either
  is wanted they belong as deliberate steps on the live pipeline, not a second orchestration.
  Note a third, thinner path remains by design: `spread_filings()` direct from
  `render_spreading_tab`, which serves the multi-filing 10-K tab for both C&I and CRE and needs no
  metrics/validation.

- Spreading and validation now delegate to the SDK. `spreader`, `spread_package` and `validation`
  are thin shims over `jazzx_sdk.pipelines.financial_spread` and `jazzx_sdk.finance.{package,
  validation}`, keeping every public name and signature so no caller changed. What stays behind is
  genuinely this pack's: the per-segment anchors, the chart of accounts, `CONTROL_KEYS` naming the
  canonical lines the arithmetic controls read (previously hardcoded inside each detector), and
  `detect_undisclosed_obligations`, which reads back through our own metric engine and so carries
  an open `code` rather than an SDK enum member.
- `ci_spread`'s declared five-step `spread` pipeline actually executes now. Its step ids
  (`document_intake` → `entity_extraction` → `spread_financials` → `validate_spread` →
  `persist_spread`) had never been bound — describe/UI metadata only, while `run_spread` ran the
  sequence imperatively. Deliberately preserved: the phase never aborts (an `on_step_error` hook
  replaces the per-phase try/except), and `checks` stays the caller's own ground-truth comparison
  with structural findings under their own key. The spread pipeline gets its own component map
  rather than sharing one flat dict, since both declared pipelines name `document_intake`/
  `entity_extraction`. First tests this method has ever had.
- New characterization test pinning spread + validation output against the real YETI and MAA
  filings; it held byte-identical through every phase above. Requires japes `dev` past `bbef95e`.

- Document-classification taxonomies for `dscr`, `cre_underwriting`, and `insurance_diligence`
  moved from hardcoded Python constants to `config/packs/<pack>/document_agent.yaml`
  (`DocumentAgentSpec.from_dir`), and are now editable from a new "🗂️ Domain" tab in each
  scenario's UI (`src/jaci/scenarios/shared/domain_tab.py`, new shared `st.data_editor`
  component, save via japes' new `DocumentAgentSpec.save_taxonomy`). `insurance_diligence` got
  its own new `config/packs/insurance_diligence_core/` pack dir (it previously had none, only
  reusing `cre_underwriting_core`'s `pack_id` for unrelated config). Requires japes `dev` past
  commit `ea8c8d9`. Verified: existing intake tests pass unchanged (YAML load produces the same
  taxonomy the hardcoded constant did) plus a real end-to-end check via Streamlit's `AppTest` —
  ran each scenario's actual demo page (no exceptions, correct tabs render) and clicked the real
  "Save taxonomy" button, confirming it persists through the full widget tree, not just a direct
  function call. No browser click-through was possible in this environment (no browser-automation
  tool available) — that verification still needs a human pass before calling this fully done.

- `dscr`'s `extract_appraisal`, `cre_underwriting`'s `classify_docs_dir`, and
  `insurance_diligence`'s `classify_docs_dir` now go through japes' `document_ingest` reference
  pipeline (single-file / collection route) instead of calling `DocumentAgent` directly — same
  public signature/return shape for all three, no caller changes needed
  (`conductor.py`/`case.py`/`ui/demo_page.py` unaffected). `cre_underwriting`/
  `insurance_diligence`'s folder walk is now `pattern="**/*"` (real deal folders aren't flat)
  instead of a hand-rolled `rglob` loop.
- **Requires japes `dev` past commit `f76f205`** (unpushed as of this entry) — that commit fixes
  a real `process_dir` bug the `**/*` migration above would otherwise have hit: a recursive
  pattern previously keyed by bare filename into one flat output dir, so two same-named files in
  different subfolders (a real shape in a nested deal folder) would silently overwrite each
  other's artifacts. Verified live against the real Mesa Verde (cre_underwriting) and Solmara Bay
  (insurance_diligence) gold document fixtures — full suite green (946 passed, 8 skipped, 4
  xfailed, 1 xpassed, matching the pre-change baseline exactly).


- `dscr`'s `cltv_pct` computation (`eligibility/context.py`) now goes through japes'
  `finance.metrics.pct(..., strict=True)` instead of raw division — a zero/missing
  `property_value` previously crashed with a bare `ZeroDivisionError`, now raises a typed,
  catchable `MetricRefusal`.
- Every definition in `config/packs/ci-spread-core/metrics.yaml` now carries an explicit
  `version` (japes' metric-definition validation now requires one). `MetricDerivation`
  (`metric_result.py`) gains `formula_version`/`approval_status`, populated on the DSL path
  (`dsl_catalog.py`'s `_to_jaci_result`) from the source `MetricDefinition`; the legacy
  Decimal-arithmetic path leaves both `None`.
- **Requires japes `dev` past commit `8192574`** (unpushed as of this entry) — verified live
  here only through the local editable install; a fresh `uv sync`/`poetry install` elsewhere
  won't see this SDK surface until japes' `dev` is pushed.

## [Unreleased]

- Fixed `ci_spread`'s YETI borrowing-base excess-availability calc: a missing `indicative_bbc`/
  `requested_line` no longer silently zeros to a fabricated "breach"; reports `"n/a"` instead,
  matching the SDK's own missing-data convention (`ratio_evaluator.evaluate_value`).
- Added `dscr` real document-derived evidence: `DocumentAgent.process(schema=AppraisalExtraction)`
  via new `scenarios/dscr/document_intake.py`; `DSCRConductor.run_review(appraisal_path=...)`
  attaches the extraction as evidence with real `PageLocator` provenance (japes locator-wiring
  plan Phase 1's first live jaci caller). Optional param, no change when omitted.

## [0.20.3] - 2026-08-18

- Settings page and `build_info()`/`GET /build.json` now also surface japes' own version and
  commit hash, not just jaci's. New `jaci.build_info.dependency_commit_sha(package)` reads the
  installed distribution's `direct_url.json` (a git-installed dependency's resolved commit),
  falling back to a `git` call against the editable-install path (our own dev setup) — japes is a
  git dependency, not part of this repo, so it has no `.git` here to check directly.
- **`acra_dscr` scenario renamed to `dscr`**, plus a model-tier fix and the 13-state
  prepayment-penalty rules. The scenario is meant to generalize beyond one client (Acra Lending
  inspired it, doesn't define it), so everything that was our own naming choice moved: directory
  (`src/jaci/scenarios/acra_dscr` → `dscr`), pack (`config/packs/acra_dscr_core` → `dscr_core`,
  `pack_id` `acra-dscr-core` → `dscr-core`), prompts (`prompts/acra-dscr` → `prompts/dscr`),
  classes (`AcraDSCRConductor` → `DSCRConductor`, `AcraToolRegistry`/`AcraHypothesisContent`/
  `AcraContext` → `DSCR*`), policy/rule IDs (`ACRA_DSCR_ELIGIBILITY` → `DSCR_ELIGIBILITY`,
  all 27 `ACRA-*` rule IDs → `DSCR-*`), UI (`key="acra_dscr"` → `"dscr"`, `label`/`display` →
  `"DSCR"`/`"DSCR Eligibility"`). Acra Lending stays only where it's a real citation
  (`source_refs.authority`, `institution_ref`, the DSCR Program Summary/Process Flow doc titles)
  — trimmed the redundant "Acra Lending" out of `title:`/`description:` prose since `authority:`
  already carries it. Caught and fixed an "an DSCR" → "a DSCR" grammar leftover from the phrase
  rename across 6 files. Full suite green throughout (900 passed both before and after — pure
  rename, zero behavior change), then two real fixes landed after it: (1) the conductor's five
  mode-model defaults were still `gpt-4o`, unlike the other high-priority conductors
  (`cre_underwriting`/`ci_spread`/`aml`, all `flex_gpt-5.4`) — bumped, and swapped the
  scenario's own identity-mapping `model_tier_parser` for the shared `jaci.settings.
  parse_model_tier` (the old one silently didn't strip the new `flex_` prefix — never exercised
  against a prefixed model name before). (2) Authored the 13-state prepayment-penalty (PPP)
  buyout rules (`DSCR-PPP-*`, ENCODING_NOTES.md §1b) — the item G1 (`AllOf`/`AnyOf`, resolved
  japes-side 2026-08-14) was explicitly blocking; 14 rules (Illinois split into its two
  independent triggers), 6 of them genuinely multi-predicate (state + entity type/amount/rate/
  unit-count/purpose) via `kind: all_of` — G1's first real consumer in this corpus. New
  `LoanApplication` fields: `prepayment_penalty_requested` (default `"no_prepay"`, so existing
  loans can't trip these), `residential_unit_count`, `interest_rate`. "Residential 1-4" needed no
  unit-count check (every existing `PropertyType` already tops out at 4 units); only Ohio/
  Pennsylvania's "Residential 1-2" and Mississippi's "single unit" carve-outs did. Mississippi's
  "5 Yr (step)/3 Year (3x3)/2 Yr (2x3)/1 Yr (1x3)" read as naming four already-catalogued
  structures by shorthand rather than new ones — flagged as an interpretive call in
  ENCODING_NOTES, worth confirming against Acra directly before a real Mississippi loan hits it.
  Found in passing (not chased): `find_profile_literal_drift` doesn't recurse into `all_of`/
  `any_of` children, so a `profile_custom_key` on these rules' literals would be decorative, not
  lint-checked — a real japes-side gap, left for later. 33 new test cases (one VIOLATED + one
  SATISFIED per rule, plus NOT_APPLICABLE spot-checks on every multi-predicate rule). None of the
  5 existing gold cases needed updating. Full suite green (932 passed, 8 skipped, 4 xfailed, 1
  xpassed — same skip/xfail/xpass counts as before, zero regressions).

## [0.20.2] - 2026-08-15

- **DSCR gains 8 condo/entity/fraud policy gates**, sourced from a newly-supplied reference
  doc (Acra's "Commercial DSCR Loan Process Flow," July 2026) rather than the DSCR Program
  Summary the existing 19-rule corpus is built on — this doc has no CLTV/DSCR content, just
  Stage 1 (duplicate-SSN check, NMLS verification, refinance-listing check), Stage 3B (HOA
  reserve/litigation review, entity-is-Borrower-1, no-multiple-title-transfers, entity-document
  completeness) gates. New rules: `ACRA-DUPLICATE-SSN-CLEARED`, `ACRA-NMLS-VERIFIED` (japes'
  `AllOfCondition` combinator's first real consumer in this corpus — verifies both broker and
  loan-officer NMLS credentials), `ACRA-REFI-LISTING-CHECK`, `ACRA-CONDO-HOA-RESERVES`,
  `ACRA-CONDO-HOA-LITIGATION`, `ACRA-ENTITY-BORROWER-1`, `ACRA-ENTITY-TITLE-TRANSFERS`,
  `ACRA-ENTITY-DOCS`. Policy version `1.1.0` -> `1.2.0`. 10 new `LoanApplication` fields, each
  defaulted deliberately rather than uniformly: the three fields backing an affirmative human
  attestation (SSN check, NMLS verification, entity docs) default fail-closed (`False`) since
  `check_compliance` silently skips (never fails) a rule reading a missing/`None` field, which
  would otherwise let an unset attestation quietly pass; the rest default to the "clean" value
  since they're findings that are normally absent (title-transfer history, HOA litigation, HOA
  reserve adequacy). No numeric HOA-reserve or owner-occupancy-ratio standard exists in either
  source document — `ACRA-CONDO-HOA-RESERVES` is authored as a qualitative AM determination
  (`hoa_reserves_adequate: bool`), and an owner-occupancy-ratio rule was deliberately not
  authored at all rather than invented. Updated all 5 existing gold-case/demo fixtures
  (`cases.py`, `tests/eval/gold_cases/acra_dscr/*.json`,
  `test_acra_dscr_conductor_engine.py`'s `_trigger()`) to attest clean on the 3 fail-closed
  fields so they stay "clean pass" rather than newly violating on fields they predate. Also
  refreshed `ENCODING_NOTES.md`'s G1 note (composite `AllOf`/`AnyOf` applicability, previously
  listed as an open platform gap) to reflect it landed japes-side and is no longer a gap.
  Along the way, found and fixed a real, previously-latent bug surfaced by a live (non-mocked)
  reasoner run: `LoanCondition.cell_value` was typed `Any`, which Pydantic renders as a
  type-less `{}` JSON-schema node — invalid under OpenAI's strict structured-output mode
  (`schema must have a 'type' key`), the same defect class as the `EvaluatorMode`/
  `NarratorMode`/`VerifierMode` dict-field fixes earlier this session, just never caught by any
  mocked test since none of them construct the real `AgentOutputSchema`. Retyped to
  `float | str | None` (its real domain — a numeric CLTV percent or the literal `"NA"`,
  matching `compose.py`'s own typing), dropping the now-unused `Any` import. 19 new behavioural
  test cases (`tests/scenarios/acra_dscr/test_acra_eligibility.py`); full `acra_dscr` suite
  47/47, full jaci suite 900 passed / 8 skipped / 4 xfailed / 1 xpassed, no regressions.
- **`docintel.py` shrunk to conversion only — its KH-manifest half deleted, not just superseded.**
  Asked to delete `docintel.py` and its dead callers outright; checked first and found the
  premise didn't fully hold — `convert_document`/`convert_document_json` (the `.japes`-stub-
  preferring conversion wrapper, with no equivalent in japes) were still live in 4 places none
  of the 4 `DocumentAgent` migrations touched (`cre_underwriting/operating_spread.py`,
  `portfolio_monitoring/intake.py`, `insurance_diligence/intake.py`,
  `ci_spread/ui/demo_page.py`). The KH-manifest half (`ensure_local_cache`/`kh_manifest_path`/
  `read_kh_manifest_entry`/`record_kh_push`/`check_staleness`) had 3 more real callers never
  migrated to japes' `local_cache.py` in the earlier pass: `commercial_lending/spreader.py`,
  `commercial_lending/document_packet.py`, `scenarios/shared/packet_picker.py`. Migrated all
  three (import-source swap + the two renamed functions, `kh_manifest_path`→`manifest_path`/
  `read_kh_manifest_entry`→`read_manifest_entry`/`record_kh_push`→`record_push`; `convert_document`
  stays on `docintel` in `spreader.py`/`document_packet.py`, unrelated to this half). With every
  real caller gone, deleted the now-genuinely-dead KH-manifest functions from `docintel.py`
  itself (not just left unused) — it's conversion-only now. Deleted the now-dead
  `tests/unit/test_docintel_manifest.py` (4 tests, all exclusively exercising the removed
  functions; equivalent coverage already exists in japes' `tests/test_local_cache.py`, ported
  there in the earlier pass). Updated 4 stale docstring references elsewhere
  (`scripts/push_source_docs_to_fabric.py`, `scenarios/shared/{fabric,document_upload}.py`)
  that still named `docintel.ensure_local_cache`/`docintel.record_kh_push`. All 89 tests across
  the affected files pass unchanged; no code deleted that still had a real caller.
- **`ci_spread` gains a `DocumentAgent`-based Phase-0 route, complementing (not replacing) its
  existing intake** (docintel-vs-DocumentAgent migration, 4 of 4 — the last, and deliberately
  saved for last given it's the actively-demoed, sales-critical scenario). Different shape from
  the other three again: `ci_spread` already has a real production Phase-0 (`run_document_intake`,
  filename-keyword `classify_document`, wired into `CIConductor`) that works fine for the common
  case and was left untouched — no naive-guess or hard-required-filename bug to fix here. The
  real gap, found by reading the code rather than assumed: two *disconnected* demo-only
  `DocumentAgent` usages already existed (`_seed_uploaded_financials` writes straight to
  `fabric.docs`, bypassing `ctx.evidence`; `_render_bulk_intake` is pure display, no downstream
  effect at all) — real content classification was proven in the demo but never actually fed
  the conductor's evidence/hypothesis system. New `commercial_lending.pipeline.
  run_document_intake_from_folder`: classifies every file in a folder via `DocumentAgent`
  against `doc_type_map`'s own keys as the taxonomy (content-based, not filename-keyword), and
  feeds the *exact* same `ctx.evidence`/`fabric.docs`/DATA_GAP-hypothesis machinery
  `run_document_intake` does — refactored the shared per-document ingest logic into `_ingest_one`
  so both routes produce identical Evidence regardless of which one ran (pure refactor,
  zero behavior change, confirmed by the pre-existing 3 tests passing unchanged). Genuinely
  different from the other three migrations in one respect: a loan package can carry several
  files of the *same* type (multiple years of financials) — every classified file is ingested,
  not just one per class. New `CIConductor._run_document_intake_from_folder`, wired as an
  alternative to the keyword route in both `_step_document_intake` (checks
  `ctx.metadata["document_folder"]`) and `run_spread` (new `document_folder=` param) — the
  keyword route stays the default in both, the folder route only runs when `document_paths`
  isn't given. `run_spread`'s Phase 2 (`spread_filings`) still needs individual paths, so a
  folder-only call covers Phase 0/1 only; documented, not silently incomplete. 4 new tests,
  including one against the real YETI sample folder (which genuinely contains one scanned PDF
  among readable ones) proving classification degrades gracefully — skips the unreadable file,
  doesn't abort the batch. All 57 pre-existing `ci_spread` tests pass unchanged.
- **`insurance_diligence` migrated onto `DocumentAgent` classification** (docintel-vs-
  DocumentAgent migration, 3 of 4). Same shape as `portfolio_monitoring`'s pilot: one real,
  document-derived case (`SOLMARA_BAY`), a fixed generic-filename convention
  (`acord_28_property.md`/`acord_25_liability.md`/`statement_of_values.xlsx`/
  `flood_determination.md`) `build_case_from_documents` assumed, and an upload flow that
  *required* exact matches (worse than `cre_underwriting`'s "first .xlsx wins" guess — no
  fallback at all, just a raw file-not-found-style error on any mismatch). New
  `document_intake.classify_docs_dir` (4-class taxonomy, recursive scan) resolves the four
  files by content; `build_case_from_documents` gained optional `acord_28_path`/`acord_25_path`/
  `sov_path`/`flood_path` overrides (default unchanged — `cases.py`'s eager-import construction
  is untouched, zero risk). The upload flow now classifies first and passes the resolved paths
  through, falling back to the fixed-filename default for any class classification didn't
  resolve. Extraction is unchanged — `parse_sov`/`parse_flood`/`parse_acord`'s regex parsers
  still do the actual reading. Proven end to end: renaming all 4 real Solmara files to
  non-conventional names, classification still resolves them and `build_case_from_documents`
  reproduces the identical `InsuranceDiligenceCase` (certificate, collateral count, SFHA ids,
  all 12 category statuses) the fixed-filename convention produces. Also tested against the
  real, messy Solmara folder (which carries several decoy/revision files beyond the 4 core
  docs, e.g. `SolmaraBay_UpdatedSOV_Rev2.pdf`) with a deliberately permissive fake classifier:
  ambiguous classes come back omitted, never a silently wrong guess — the two classes with no
  real-world decoys (ACORD 28/25) still resolve cleanly regardless. Local-cache import in
  `ui/demo_page.py` switched from `docintel` to japes' `jazzx_sdk.tools.documents.local_cache`.
  3 new tests; all 38 pre-existing `insurance_diligence` tests pass unchanged.
- **`cre_underwriting` migrated onto `DocumentAgent` classification** (docintel-vs-DocumentAgent
  migration, 2 of 4 — `portfolio_monitoring` was the pilot). Real shape here differs from that
  pilot: `CREConductor` never touched documents at all, there's one real case (Mesa Verde) with
  explicit hardcoded `spread_path`/`insurance_loe_path`, and the insurance LOE already extracted
  via `jazzx_sdk.tools.extract` (the modern path) — so there was no conductor step to add. The
  actual live gap, found by reading the code rather than assumed: `ui/property_case_page.py`'s
  document-upload flow did `sorted(folder.rglob("*.xlsx"))[0]` and assumed it was the T-12 — no
  classification at all, would silently pick the wrong file if a zip had more than one `.xlsx`
  (a rent roll, an appraisal workbook), and never picked up an uploaded insurance LOE at all
  (only `spread_path` got set from an upload). Fixed: new `document_intake.classify_docs_dir`
  walks a deal folder recursively (real CRE folders nest — Mesa Verde's T-12 sits under
  `Application Package/Financials/`, `DocumentAgent.process_dir` doesn't recurse, so this uses
  `DocumentAgent.process()` per file instead) against a 2-class taxonomy (T-12, insurance LOE).
  New `case.resolve_case_docs()` fills in `CRECase`'s `spread_path`/`insurance_loe_path` from
  `docs_dir` classification when either is left `""` — `spread_path` gained a `""` default
  (previously required) to support this; explicit paths still win entirely, matching
  `portfolio_monitoring`'s pattern. The upload flow now resets both paths before resolving (the
  old code left a stale `insurance_loe_path` from the base case leaking into an uploaded case
  that might not carry one — a second real bug fixed alongside the classification gap).
  Extraction is unchanged: `load_t12_spread`'s regex parser and `extract_insurance_loe`'s
  schema-only LLM extraction both still do the actual reading. Proven end to end: a docs_dir-
  only case classified against the real Mesa Verde documents resolves to the exact same two
  paths the hardcoded case uses, and `case_spread()` on it produces identical NOI/DSCR/periods.
  Local-cache import in `ui/property_case_page.py` switched from `docintel` to japes'
  `jazzx_sdk.tools.documents.local_cache`. 7 new tests across 2 new files; all 64 pre-existing
  `cre_underwriting` tests pass unchanged (Mesa Verde's own explicit-path construction is
  untouched by the new default).

## [0.20.0] - 2026-08-14

- **`portfolio_monitoring` piloted onto japes' `DocumentAgent`/`document_ingest` classification**
  (docintel-vs-DocumentAgent migration, pilot 1 of 4 — see `docs/plans/` for the full scope and
  why this scenario went first). New `document_intake.classify_docs_dir` runs `DocumentAgent`
  against a 4-class taxonomy (T-12, loan agreement, CCC, rent roll) over a relationship's
  `docs_dir`; a new `sp.classify` conductor step resolves `PortfolioReviewContext`'s
  `t12_file`/`loan_agreement_file`/`ccc_file`/`rent_roll_file` from it instead of assuming
  fixed filenames. Extraction is unchanged — classification only decides *which* file is which;
  the existing hand-tuned regex parsers (`load_t12_spread`/`parse_loan_agreement`/`parse_ccc`/
  `parse_occupancy`) still do the actual reading, more reliable for numeric tables than a
  general LLM pass (a deliberate scope decision, not a gap). An explicit `t12_file=`/etc.
  override still works and skips classification for that slot entirely — a `_UNSET` sentinel
  (not `None`) distinguishes "classify this" from `rent_roll_file=None`'s pre-existing, real
  meaning ("no occupancy covenant for this relationship"); conflating the two was a real bug
  caught before it shipped (would have silently triggered classification, and a real
  `AgentExecutionService()`, for every relationship missing an explicit rent-roll override).
  Proven end to end: `run_portfolio_review` with **zero** explicit filenames (classification
  alone) against the real Grove Commons documents produces the exact same `PortfolioReviewCase`
  as `cases.py`'s existing fixed-filename-built `GROVE_COMMONS`. The three retail relationships
  (`demo_cases.py`'s `DEMO_CONTEXTS` — Cedar Grove, Shops at Worthington, Maple Run) keep
  explicit overrides for all four fields (a real, repo-wide filename convention for
  `loan_agreement_file`/`ccc_file` across every relationship, not just Grove Commons — removing
  those two fields' old fixed defaults without preserving them here would have silently
  triggered classification, and a real LLM call, for a caller that never wanted it). Local-cache
  imports in `ui/demo_page.py` switched from `docintel` to japes' new generalized
  `jazzx_sdk.tools.documents.local_cache`. `cases.py`'s monolithic `build_case_from_documents`
  path (used at module-import time) is untouched — that's a separate, already-known eager-import
  architecture question, not this pass's scope. 10 new tests across 3 new files; 2 pre-existing
  test files (`test_portfolio_conductor.py`, `test_pm_retail_conductor.py`) updated for the new
  `sp.classify` step id and the `_UNSET`-vs-`None` semantics.
- **Two security findings from PR #5's automated review fixed** (both still current when
  checked against the working tree, unrelated to anything else in this release). (1)
  `Dockerfile`'s post-install `git config --global --unset` targeted
  `url."https://github.com/".insteadOf`, but the credential rewrite rule set a few lines above
  was written to `url."https://${TOKEN}@github.com/".insteadOf` — a different key. Git exited 5
  (key not found), swallowed by `|| true`, so the token-bearing rule was never actually removed
  and stayed live in the committed image layer's `/root/.gitconfig`. Fixed to target the same
  key it set. (2) `.github/workflows/release-nightly.yml` passed `GITHUB_TOKEN`/`TOKEN` as
  Docker `build-args` in both build steps *in addition to* the `secrets:` block a few lines
  below — build-args are stored verbatim in the OCI image config and recoverable via `docker
  history --no-trunc`/`docker inspect` by anyone with registry read access, while `secrets:`
  already delivers the token safely via a BuildKit secret mount that the Dockerfile's `RUN
  --mount=type=secret` already prefers. Removed both redundant build-arg lines; `COMMIT_SHA`/
  `GIT_TAG` (non-secret) stay as build-args.
- **The remaining 5 correctness findings from PR #5's automated review fixed** (all still
  current when checked against the working tree). `validation.py`'s
  `detect_cross_period_addback_inconsistency` caught `KeyError` around
  `Severity(profile.get("cross_period_addback_severity"))`, but `dict.get()` never raises
  `KeyError` — an invalid severity string raises `ValueError`, uncaught, crashing the whole
  check; now catches `ValueError`. `document_packet.list_packets` raised an unhandled `KeyError`
  from bare `payload["name"]`-style subscripts on any live packet doc missing one of 4 required
  keys, aborting the entire listing (live packets silently vanish from the UI picker via the
  `except Exception` fallback in `list_all_packets`); now caught alongside the existing
  `json.loads` guard, skipping just the malformed entry. `docintel.py`'s
  `read_kh_manifest_entry`/`record_kh_push` both `json.loads`'d `.kh_manifest.json` with no
  error handling — a truncated/corrupt manifest (concurrent push, interrupted write) would
  abort a folder push mid-loop or crash a read; both now go through a shared `_load_manifest`
  helper that treats a corrupt file as empty (logged) rather than raising — see also this
  session's note on `docintel.py`'s scope below. `pipeline.py`'s Phase-1 KG-write logging did
  `len(ids)` on a value that could be `None` if `graph.add_entity` hits its error path,
  `TypeError`-crashing into a misleading "non-blocking" log after triples were already
  partially written/deleted; now `len(ids or [])`. `pipeline.py`'s Phase-0 document intake
  added `doc_type` to `ingested_types` verbatim (case preserved from `doc_type_map`) while the
  `structured_data` branch explicitly lowercased — no current pack config triggers it (all use
  lowercase keys), but a future mixed-case `doc_type_map` would raise a spurious `DATA_GAP`
  hypothesis for a type that was actually ingested; both branches now lowercase consistently.
  `hooks.py`'s `TraceHooks` declared and accumulated `cache_creation_tokens` but never read
  Anthropic's `usage.cache_creation_input_tokens` into it — always reported 0, understating
  cost on any cache-writing run; now reads it the same tolerant top-level way
  `jazzx_sdk.agents.anthropic_provider` already does (a no-op for OpenAI's differently-shaped
  `Usage`, which has no such field). 12 new tests across 5 new test files.
- **`docintel.py` scope question raised and settled**: its `.kh_manifest.json` bookkeeping
  (`read_kh_manifest_entry`/`record_kh_push`/`ensure_local_cache`/`check_staleness`) solves a
  different problem than japes' `jazzx_sdk.pipelines.document_ingest` (the new `DocumentAgent`-
  based classify/extract/route pipeline) and isn't redundant with it. `document_ingest` assumes
  you already have a document's bytes in hand; `docintel.py`'s manifest exists precisely for
  when you don't — jaci vendors small stubs for its large sample docs (the YETI/MAA `.japes`
  convention) and needs a committed, git-tracked filename→remote-doc-id mapping to resolve the
  real content from a shared/mock Knowledge Hub without ever hashing bytes that aren't present
  locally. `fabric.docs.ensure()`'s server-side content-hash idempotency (what `document_ingest`
  and `document_packet.py`'s push path both lean on) can't do that lookup either, for the same
  reason — it needs the content to hash. Conclusion: stays in jaci, fixed in place above, not
  migrated. (`convert_document`'s synchronous conversion stub, used directly by
  `cre_underwriting`/`portfolio_monitoring`/`insurance_diligence`'s hand-rolled T-12/ACORD/rent-
  roll parsers rather than through `DocumentAgent`, is a separate and larger question — whether
  those scenarios' intake should migrate onto `document_ingest`'s classify/extract flow at all —
  not resolved here, flagged as a real follow-on if it comes up again.)

- **`acra_dscr` A5: profile-literal vs `custom` twin drift lint** (`plan_JAPES_POLICY_IR_
  AUTHORING_DEFECTS.md` P4a, G4). Eight `Expression` rules in `eligibility.yaml`
  (`ACRA-LA-MIN`, `ACRA-LA-MAX`, `ACRA-STATE-INELIGIBLE`, `ACRA-HIGH-LTV-PROPERTY-TYPE`,
  `ACRA-HIGH-LTV-RESERVES`, `ACRA-FICO-LT-620-RESERVES`, `ACRA-IO-MIN-LOAN`,
  `ACRA-NO-RATIO-FICO`) annotated with `domain_extensions.profile_custom_key`, linking each
  hardcoded literal to its `PolicyProfile.custom` review twin — matched by value and by rule
  semantics against the real corpus, not by guessing a naming convention (the `custom` keys
  don't follow one). New test asserts zero drift against the real corpus, plus a second test
  guarding the 8 links themselves stay declared. Found along the way: three `custom` keys
  (`fico_min_str`, `fico_min_io`, `seller_concession_max_pct`) have no consuming rule at all
  today — noted in `ENCODING_NOTES.md`, not a drift bug. `ENCODING_NOTES.md`'s G3 (cap
  composition) and G4 status both updated to reflect Phases 2.2/2.3 landing. Depends on new
  japes `jazzx_sdk.fabric.canonical.policy_lint` and `AllOfCondition`/`AnyOfCondition` (G1),
  both shipped upstream alongside two other IR fixes found authoring the corpus
  (`RatioCondition.direction` over-typing, `Expression`'s float-cast breaking string equality,
  matrix violations rendering as a bare `"matrix"` string).
- **`acra_dscr` D3 rev 2 Phase 2.4 + 3.1-3.3.** Investigator/narrator/verifier prompts now each
  state the deterministic eligibility assessment is given, not inferred (reasoner/governor
  already had this from Phase 2.3), scoped to what each mode actually does with it —
  investigator: don't request evidence to re-derive a grid fact; narrator: cite the
  assessment's own numbers faithfully; verifier: it arrives pre-attested and never appears in
  the pending queue. New demo page (`ui/registry.py`'s `acra_dscr` entry gains `demo_target`/
  `gold_dir`) renders the deterministic grid resolution (inputs → band keys → composed cap,
  binding rule named) unconditionally — no model call — and the live investigation loop only
  on request, in a visually separate section, per the program plan's own "an underwriter should
  see at a glance which findings are arithmetic and which are inference." 5 new gold cases
  under `tests/eval/gold_cases/acra_dscr/`, one per `cases.py` fixture, `expected` blocks
  computed by running the real evaluator against each fixture (not assumed) — also feeds the
  Concepts tab's case-fleet view. Phase 3.4 (real appraisal-driven LTV, gated on decision G2)
  remains open; CLTV stays the `loan_amount / property_value` book proxy, labeled as such in
  the demo.
- **Two small fixes found along the way.** `clinical_intake`'s demo page resolved its repo
  root one directory too shallow (`parents[4]` instead of `[5]`) — `_PACK`/`_GOLD` pointed at a
  nonexistent `<repo>/src/config`/`<repo>/src/tests`, so the persona picker silently returned
  empty. `shared/fabric.py::build_fabric`'s throwaway `knowledge_hub_url="mock://local-kh"`
  (needed only to satisfy japes' `FabricConfig.validate_for_mode()` when the actual client is
  a Mock) is removed now that japes no longer requires a URL when a `kh_client` is already
  supplied.
- **`test_decision_type_all_values` fixed — was asserting a stale member count, not a
  regression.** japes' `DecisionType` grew a 4th member, `ATTRIBUTION`, for the eval-service
  contract convergence work (already used elsewhere in jaci's own
  `test_eval_service_adapters.py`); this test still asserted `len(DecisionType) == 3` and never
  got updated. Now asserts 4 and covers `ATTRIBUTION` explicitly. Full suite now genuinely
  green (854 passed, 0 failed) — this was the one standing pre-existing failure carried in
  status notes since June.
- **`acra_dscr` promoted to the default (first-listed) scenario** in `ui/registry.py`'s
  `SCENARIOS` — the list's own top comment ("the first entry is the default selection") makes
  this a one-line reorder, no other registry fields changed.

## [0.19.9] - 2026-08-14

- **`acra_dscr` Phase 2.3: wire the eligibility corpus into `AcraDSCRConductor`.** New
  `eligibility/assessment.py::run_eligibility_assessment`/`EligibilityAssessment` combines
  Phase 1's `build_eligibility_context` and Phase 2.2's `compose_caps` into one deterministic
  answer, run before the model loop starts (plain Python in `run_review()`, not a formal
  pipeline step -- `investigation_loop` has no pre-loop hook, and adding one for this single
  consumer would be premature). Surfaced to the LLM modes via two channels, traced from the
  actual `ReasonerMode`/`GovernorMode` source rather than assumed: a synthetic `ATTESTED`
  `Evidence` entry (`ReasonerMode` serializes full evidence content but not `ctx.metadata`) and
  `ctx.metadata["eligibility_assessment"]` (`GovernorMode` serializes full metadata but only
  evidence counts). New `_enforce_deterministic_verdict`: a model-produced Governor approval
  cannot override a deterministic policy violation -- forces `approved=False` and cites the
  violated `rule_id`(s) regardless of what the LLM said. Not registered as an `AcraToolRegistry`
  tool (deviating from the plan doc) -- checked `AcraToolRegistry.execute()`'s signature, it only
  ever receives `query_params`, no loan/context reference, and the registry is built once per
  conductor while the assessment is per-review; forcing it through that shape would mean the LLM
  re-supplying loan fields it already has. `reasoner.md`/`governor.md` each gained one paragraph
  stating the assessment's verdicts are given, not inferred. `ReviewFile` gained an
  `eligibility_assessment` field. 3 new tests, including one proving the Governor override fires
  even when the scripted Governor mode itself approves. No UI/gold cases (Phase 3), no
  `AllOf`/`AnyOf` (G1).

## [0.19.8] - 2026-08-13

- **`acra_dscr` Phase 2.2: cap composition** (D3 rev 2, `ENCODING_NOTES.md` G3 -- the one
  genuinely undesigned piece of the program). New `eligibility/compose.py::compose_caps` +
  `ComposedCap`: `min()` across every applicable max-CLTV rule, the binding rule named. Which
  rules compose is structural, not a hardcoded list -- any `Rule` whose `condition.kind ==
  "matrix"` and `compare_field == "cltv_pct"` (today 6: the base grid, property-type overlay,
  short-term-rental, sub-1.0-DSCR, No-Ratio, ITIN); a future cap rule joins automatically once
  authored. An authored `"NA"` cell is tracked separately (`ineligible_via`) rather than folded
  into the `min()` as "an infinitely tight cap"; a cap rule that can't resolve (missing per-loan
  data) is tracked separately too (`blocked_by_indeterminate`) and forces `passed=False`
  regardless of the known caps -- an unknown constraint is never assumed looser than what's
  visible. Runs alongside `check_compliance`, not instead of it -- each cap rule still fires its
  own independent verdict citing its own directive. 7 new tests against the real corpus and the
  5 `cases.py` fixtures, including `DOUBLE_CAP` (built in Phase 1 specifically to exercise this)
  and two inline edge cases (a blocked axis field, a forced tie). No conductor/tool/Governor
  wiring yet (Phase 2.3), no `EligibilityAssessment` (Phase 2.1).

## [0.19.7] - 2026-08-13

- **`acra_dscr` Phase 1: bind the eligibility corpus to the skeleton's schemas** (D3 rev 2).
  `LoanApplication` field names now match what the 19 authored rules read directly — renamed
  `fico_score`→`fico`, `citizenship`→`citizenship_type`; `property_type` closed to a real
  8-value `PropertyType` enum (drawn from the corpus's own authored vocabulary, not guessed);
  added `property_state`, `gross_rental_income`, `pitia`, `reserves_months`,
  `occupancy_subtype`/`dscr_documentation_type` (defaulted), `escrow_waiver_requested`,
  `product_is_interest_only`. No separate field-mapping adapter needed — the one real consumer
  in the repo was the skeleton's own scripted-mode test, updated in place. New
  `eligibility/context.py::build_eligibility_context` handles what's genuinely derived: `cltv_pct`
  as a book-LTV proxy (`100 * loan_amount / property_value`, explicitly labeled — no
  appraisal-driven calculator exists yet). `LoanCondition` gained required `rule_id`/
  `policy_refs` (a condition cannot be constructed without citing what it violated, ABA §5.9)
  plus optional `cell_key`/`cell_value` for matrix-derived violations. New `cases.py` — 5
  synthetic `LoanApplication` fixtures (clean pass, loan-amount band boundary, an authored NA
  grid cell, two caps binding at once, sub-1.0-DSCR cash-out), each verified via
  `DefaultPolicyExpert.check_compliance` against the real corpus to confirm its intended verdict.
  New guard test (`tests/scenarios/acra_dscr/test_eligibility_context.py`) asserts every field
  the 19 rules read resolves on the adapter's output — a rename on either side now fails loud
  instead of silently reading `INDETERMINATE`. No conductor/UI wiring yet (Phase 2/3).

## [0.19.6] - 2026-08-13

- **`acra_dscr` eligibility policy corpus landed (Phase 0 of `plan_JACI_ACRA_DSCR_SCENARIO.md`
  rev 2).** `config/packs/acra_dscr_core/{profiles/acra_dscr_profile.yaml,
  policies/eligibility.yaml, ENCODING_NOTES.md}` and `tests/scenarios/acra_dscr/
  test_acra_eligibility.py` (18 tests: 17 behavioural + grid completeness) -- the first real
  consumer of japes' `MatrixCondition` (99-cell CLTV grid, 3 loan-amount bands x 11 FICO bands x
  3 purposes) plus `RatioCondition`/`Expression` conditions, 19 rules total. Verified against
  japes `1576f8e`, run from jaci's own test environment. Six single-element `in`/`not_in`
  occurrences that stood in for `==`/`!=` (`ACRA-STR-CLTV`, `ACRA-ITIN-CLTV`,
  `ACRA-ITIN-LOAN-MAX`, `ACRA-FOREIGN-NATIONAL-ESCROW`, `ACRA-NO-RATIO-CLTV`,
  `ACRA-NO-RATIO-FICO`) rewritten to plain `==`/`!=` now that japes' `Expression` float-cast bug
  is fixed; re-verified 18/18 green after the rewrite. The `dscr_sub_1_ceiling: "0.9999"`
  ratio-direction workaround is *not* un-scarred -- `RatioCondition.direction` was deliberately
  not widened to support strict `<`/`>` (see `ENCODING_NOTES.md` §2), so that pattern remains the
  correct way to express a strict ratio bound. `pack_manifest.yaml` documents the new files but
  does not yet wire a `policies:` section -- that needs a `PolicyRegistry` Python module
  (`policies/registry.py`), which is Phase 1, not this pass. No scenario/conductor code touched.

## [0.19.5] - 2026-08-13

- **japes reference-pipeline reorg.** `chat`/`document_ingest` moved from
  `jazzx_sdk.agents.interactive.chat`/`jazzx_sdk.agents.document.pipeline` to
  `jazzx_sdk.pipelines.{chat,document_ingest}`; `DocumentAgentSpec` moved from
  `jazzx_sdk.agents.document.agent` to `jazzx_sdk.agents.document.spec` (still re-exported from
  the `jazzx_sdk.agents.document` package). Updated `demo_page.py` (7 import sites) and
  `test_yeti_credit_outcome.py` (2 import sites) to match.
- **`EarningsAnthropicConductor` migrated onto japes' new `jazzx_sdk.pipelines.
  investigation_loop`** (proof-of-concept for the pattern all five investigation-loop scenarios
  independently hand-roll -- AML/CRE next, once proven). `_step_*`/`_components()` replaced by an
  `InvestigationSpec`; `describe()` now returns the generic pipeline instead of the YAML-loaded
  `EARNINGS_PIPELINE` (kept as a module symbol solely for `ui/registry.py`'s diagram lookup).
  Behavior-neutral -- existing tests pass unchanged.
- **`CREConductor` migrated onto the same primitive** -- the real target it was designed for
  (richer than earnings_anthropic: Sentinel, checkpointing, a deterministic convergence floor,
  plus three pack-only deterministic steps and a custom governor/narrator). japes'
  `investigation_loop` gained `halt_on_reasoner_failure` and `post_loop_steps`/`overrides=` to
  cover CRE's real shape (found by reading the current code, not assumed). `_step_stress`/
  `_step_policy`/`_step_governor`/`_step_dependencies`/`_step_narrator`/`_step_persist` kept
  verbatim as overrides -- genuinely pack-specific. `tests/unit/test_cre_conductor_engine.py`
  passes unchanged.
- **`AMLConductor` migrated onto the same primitive** -- closest structurally to CRE (Sentinel,
  checkpointing, deterministic convergence floor, `ctx.loop_status` used directly) but without
  CRE's extra steps or mutate-in-place governor; governor/narrator follow earnings_anthropic's
  remap-in-post-processing pattern instead. First real use of `deadline_guard` (AML's SAR-deadline
  check) and japes' new `on_mode_result` hook (AML's per-mode token-usage accumulation into
  `ctx.metadata["token_usage_by_mode"]`, feeding `tests/eval/test_anthropic_token_tracking.py`).
  Only `_step_persist` kept as an override. `tests/unit/test_aml_conductor_engine.py` passes
  unchanged.
- **`KYCAnthropicConductor` migrated onto the same primitive** -- no japes-side changes needed
  this time, everything already fit: `is_active`/`mark_converged`/`mark_guard_fired` overridden
  for its bespoke boolean `converged` flag (like earnings_anthropic); only `governor` kept as an
  override (it stashes risk-tier document requirements onto `ctx.metadata` before calling
  `GovernorMode`, a single-use pre-call side effect). `investigator`/`evidence`/`verifier`/
  `reasoner`/`narrator` are now fully generic. `tests/unit/test_kyc_anthropic_conductor_engine.py`
  passes unchanged. Four of five investigation-loop scenarios now migrated -- only KYC-plain
  remains, and it needs its own prior migration onto `ConductorEngine` first (unrelated,
  separate work).
- **`KYCConductor` (plain, OpenAI-based) migrated onto the same primitive -- the fifth and
  last.** Previously a hand-rolled `while` loop with no `BaseConductor`/`describe()`/declarative
  pipeline at all (UI-unregistered, but real and test-alive: `tests/unit/
  test_kyc_conductor_equivalence.py` is a deliberate KYC-vs-KYC-Anthropic parity suite for
  SymphonyAI prep). Now a proper `BaseConductor` subclass. Fits the primitive's defaults even
  more directly than KYC-Anthropic: `ReviewContext.converged` is a read-only property computed
  from the base `Context.loop_status` field, and governor has no pre-call side effect, so
  neither needs an override -- only evidence-fulfillment's per-request `try`/`except` (a
  resilience feature unique to this conductor among the five) and the reasoner-failure fallback
  are pack-specific hooks. No japes-side primitive changes needed. All 6 parametrized
  equivalence-suite tests (both `kyc` and `kyc_anthropic` adapters) pass unchanged. **All five
  investigation-loop scenarios are now on `jazzx_sdk.pipelines.investigation_loop`.**
- **`acra_dscr` scenario carved as a new skeleton** -- the first jaci scenario built directly on
  `jazzx_sdk.pipelines.investigation_loop` from day one (no hand-rolled loop, no later
  migration). Structural scaffolding only; see `docs/plans/
  Acra_DSCR_on_Platform_v2_Reuse_and_Build_Plan.md` for the real (separate, not-yet-built) work:
  taxonomy, policy corpus (`MatrixCondition`-based eligibility grid), vendor integrations.
  `AcraDSCRConductor` mirrors `KYCConductor`'s just-migrated shape (the simplest of the five --
  no Sentinel, no checkpoint, convergence read straight off `Context.loop_status`).
  `schemas/acra_schemas.py` copies `ConditionType`/`LoanCondition` verbatim from
  `cre_underwriting` (Acra's Byte PTC/PTF buckets map onto them directly); `AcraToolRegistry` is
  mock-only, two illustrative evidence types. New `config/packs/acra_dscr_core/pack_manifest.yaml`
  (draft, no conductor/experts/policies sections yet -- both optional in `jazzx_sdk.pack.Pack`).
  One `ui/registry.py` `SCENARIOS` entry, no demo/dashboard/gold_dir yet. New
  `tests/unit/test_acra_dscr_conductor_engine.py` (4 tests, scripted-mode orchestration parity).
  Also fixed a real, pre-existing circular import surfaced while verifying this change (unrelated
  to acra_dscr itself): `jaci.scenarios.kyc/__init__.py` eagerly importing `conductor.py` created
  a 3-hop cycle through `jaci.schemas.japes_types` (introduced by the KYC-plain migration above).
  Fixed with a lazy `__getattr__` for the conductor exports, same pattern already used for
  `jaci.modes`' EVOLVE-mode exports.

## [0.19.4] - 2026-08-13

- **Vocabulary enforcement wired into live spreading.** `spreader.spread_financials()` gained
  `vocabulary=`, threaded into `structure_statement()`; `spread_financials_package()` defaults to
  the pack's `CHART_OF_ACCOUNTS`. Unresolved keys surface as `SpreadPackage.vocabulary_gaps` ->
  new `DefectClass.VOCABULARY_GAP` finding (Medium, non-blocking) via `detect_vocabulary_gaps()`,
  wired into `validate_package()`. (japes side: `FinancialSpread.vocabulary_gaps`, additive.)
- `DocStore.materialize()` (japes) no longer runs its metadata probe when
  `NullMaterializeManifestStore` is configured -- was one wasted `get_document_metadata` HTTP call
  per document for an answer that could never be used.

## [0.19.3] - 2026-08-11

- **Docs** — `docs/ARCHITECTURE.md` rewritten from scratch. The prior version described the AML
  scenario's own code as if it were the platform (several cited paths no longer exist there); the
  new version reflects the current multi-scenario reality — the shared `jazzx_sdk` platform layer
  (`BaseConductor`, shared Modes, canonical object chain, Experts/Skills, EVOLVE), domain pack
  governance, the previously-undocumented commercial-lending capabilities layer (including this
  round's document-packet pipeline, scoped honestly as opt-in, not canonical), and a rebuilt,
  verified file reference appendix.
- **Added** — Document upload widget (`scenarios/shared/document_upload.py`, `render_document_upload`) wired into `ci_spread`, `cre_underwriting`, `portfolio_monitoring`, `insurance_diligence`: a zip stands in for a folder upload, unpacked via `jazzx_sdk`'s `unpack_zip`. `ci_spread` gains `_seed_uploaded_financials` to feed uploaded docs into `CIToolRegistry`'s evidence pipeline.
- **Fixed** — `ci_spread`'s `_run_fabric` never set `FabricConfig.local_cache_dir`, so LOCAL-mode `fabric.docs` silently missed the per-loan `artifact_dir` entirely — anything written there was unreadable on the next call.
- **Added** — `commercial_lending/docintel.py`'s `.japes/`-or-co-located-`.md` local-cache fallback (previously only used by `ci_spread`) wired into `cre_underwriting`, `portfolio_monitoring`, `insurance_diligence` too (swapped their raw `jazzx_sdk.convert_document` import for the `.japes`-aware wrapper).
- **Added** — `docintel.ensure_local_cache`/`ensure_local_caches`: an async Knowledge-Hub pull tier ahead of live conversion (derived doc first, falling back to pulling+converting the original), backed by a `.kh_manifest.json` sibling manifest. `docintel.check_staleness` flags when a doc's fabric copy changed since last pull (metadata-only, never auto-resolves).
- **Added** — `scenarios/shared/fabric.py`: `build_fabric()` (connected-KH-vs-local-Mock switch, factored out of three duplicate copies) and `cached_build_fabric()`.
- **Fixed** — `MockKnowledgeHubClient` doesn't persist across process/script-rerun boundaries (no save-back to `data_dir`); since Streamlit reruns the whole script on every interaction, an uncached fabric would forget a just-pushed packet before it could ever appear in a dropdown. `cached_build_fabric()` caches the fabric object in `st.session_state` for the session's lifetime. Filed upstream as [japes#57](https://github.com/JazzX-LLC/japes/issues/57) (along with a second `FabricConfig` validation papercut also found and worked around).
- **Added** — Named "document packet" system: `capabilities/commercial_lending/document_packet.py` (`push_folder_as_packet`, `list_packets`/`list_all_packets`, `save_packets_to_manifest`) and `scenarios/shared/packet_picker.py` (dropdown UI, wired into `ci_spread`'s upload flow). Pushes both original bytes and derived `.japes` markdown per doc, dedups via `fabric.docs.ensure()`'s content-hash idempotency. `local_path` auto-detected when a packet's source folder is already inside the repo (vendored, zero-fabric-dependency pick). `config/demo_document_packets.json` is the committed offline registry, merged with live Knowledge Hub results — populated via new `scripts/export_document_packet_manifest.py`. Two more new scripts: `scripts/push_source_docs_to_fabric.py`, `scripts/refresh_and_push_japes.py`. Named "packet", not "pack", to avoid colliding with the existing governed-domain-pack concept (`config/packs/`, `pack_id`, `pack_manifest.yaml`).
- **Added** — `scripts/shrink_source_pdfs.py`: swaps a large source PDF for a small labeled stub + its `.japes/<stem>.md` (existence-only resolution, so the stub's actual bytes never matter). Used to shrink and commit the YETI/MAA 10-K sample PDFs (50-70MB → <1MB each); originals preserved locally under a gitignored `_originals/`.
- **Migrated** — KYC, KYC-Anthropic, and Earnings-Anthropic conductors onto the shared `jazzx_sdk.modes.operational` chassis, replacing per-scenario hand-rolled mode subclasses (several with no real Pydantic output schema, no retry/truncation handling).
- **Fixed** — `Context.apply_verifier_report` raised `AttributeError` against real evidence (`EvidenceObject.status` is read-only); KYC/KYC-Anthropic's `ReviewContext` now override it, matching AML's `CaseContext`.
- **Simplified** — `CREPolicyExpert` wires its registry/overlay-map into `DefaultPolicyExpert` instead of duplicating ~230 lines of overlay/compliance logic.
- **Fixed** — `CLSpreadContext` had no `control_tolerance` field, so `credit_validation.provides.validate()` never passed one to `validate_package()`, which gates the four arithmetic controls (`detect_balance_control`/`_cash_flow_tie`/`_equity_rollforward`/`_period_continuity`, FR-VAL-1/3/4/5) on it being non-`None` — all four were dead in the governed pipeline regardless of a real imbalance, exercised only by tests calling the detectors directly. Added the field (`Decimal | None = None`, off by default — tolerance is institution policy, never a module default) and threaded it through; 2 new regression tests in `tests/unit/test_cl_capability.py` (both directions: off by default, surfaces the finding when set). `scenarios/ci_spread/ui/demo_page.py` now sets `control_tolerance=Decimal("2")` (matching the PRD's own documented RB rounding fact) so the controls actually run in the one live-demo call site, not just when a caller opts in.
- **Fixed** — `ci_spread`'s demo/dashboard pages displayed the leverage covenant ceiling as a hardcoded "policy max 3.0x" label in 3 places (2 in `demo_page.py`, 1 in `dashboard.py`) — stale against `CI_CORE_LEVERAGE_POLICY`'s real `CI-LEVERAGE-CEILING` of 3.5x (3.0x is a separate, lower `CI-LEVERAGE-WARNING` tier that isn't the ceiling at all). Added `_ci_policy_rule_value()`, reading the real value from `CI_REGISTRY` — the same registry `DefaultPolicyExpert.check_compliance()` actually gates the decision on — instead of a hand-maintained string. 4 new tests in `tests/unit/test_ci_spread_demo_page.py`.

## [0.19.0] - 2026-08-01

`plan_JACI_CONCEPTS_TAB_PARITY.md` Phases 0/1/4 (of 5; Phases 2-3 are real pack-authoring work, not
started; Phase 5 blocked on Phase 2). See `docs/status/status_JACI_CONCEPTS_TAB_PARITY.md`.

- **Verified** — `clinical-intake-core`'s pack already loads and its Concepts tab renders clean
  end-to-end; nothing was wrong, now confirmed rather than assumed.
- **Fixed a false premise** — `aml_investigation_core.yaml`/`earnings_review.yaml` do not actually
  load via `Pack.from_manifest` (wrong location/shape entirely, not just incomplete) — the plan's
  own Phase 1 "cheap wiring" for these two does not apply; correctly left unwired rather than wired
  into a crash.
- **Added** — `portfolio_monitoring` gains a `pipeline_target` pointing at its existing, previously
  unwired `PORTFOLIO_REVIEW_PIPELINE`, so its Concepts tab now shows the real assembly diagram
  instead of degrading to platform-layer-only.

## [0.18.0] - 2026-08-01

`plan_JACI_CL_GOVERNED_LAYER_UI.md` Phase 5 — plan now fully complete (all 5 phases, 0 added
during execution). See `docs/status/done_JACI_CL_GOVERNED_LAYER_UI.md` for full detail.

- **Added** — Covenants tab gains a layered-spread-views table: reported beside reclassified
  (and, once a correction has run, underwritten), a period picker, and a caption stating whether
  Total assets stayed identical while Total current assets moved. Only the layers that genuinely
  exist as whole-statement projections today are shown — a real "normalized" layer would be new
  capability work, not UI wiring, so it's flagged rather than faked.

## [0.17.0] - 2026-08-01

`plan_JACI_CL_GOVERNED_LAYER_UI.md` Phase 4 (of 5; Phase 5 not started, the hardest phase now
behind it). See `docs/status/status_JACI_CL_GOVERNED_LAYER_UI.md` for full detail.

- **Added** — Covenants tab gains a corrections-and-approval expander driving
  `spread_approval_engine`'s suspend/resume cycle from Streamlit: draft a rationale-required
  correction against a flagged spread, approve or reject, and see exactly which metrics and
  covenant tests (via `evaluate_covenant_policy`) flipped as a result. Verified stateless-engine
  safety across Streamlit reruns and the single-use suspension guard before wiring it up.

## [0.16.0] - 2026-08-01

`plan_JACI_CL_GOVERNED_LAYER_UI.md` Phase 3 (of 5; Phases 4-5 not started). See
`docs/status/status_JACI_CL_GOVERNED_LAYER_UI.md` for full detail.

- **Added** — Covenants tab gains a source-region view: a table of every populated cell's
  resolved provenance (`cell_source_regions`), plus a reverse-lookup picker showing every other
  cell fed by the same source coordinate (`cells_fed_by`) — pure UI wiring around already-shipped,
  already-tested functions from Wave 3b.

## [0.15.0] - 2026-08-01

`plan_JACI_CL_GOVERNED_LAYER_UI.md` Phase 2 (of 5; Phases 3-5 not started). See
`docs/status/status_JACI_CL_GOVERNED_LAYER_UI.md` for full detail.

- **Added** — Covenants tab gains an aggregate status banner (`aggregate_status`, pass/pass-with-
  flags/blocked) at the top, and a review-queue expander ranking session findings via
  `rank_for_review` with adjustable severity/confidence/magnitude/covenant weight sliders, each
  row showing the raw confidence and covenant-feeding rationale behind its rank (new
  `review_rationale()`), plus the credit file's exception summary (`exception_summary`, proven
  identical to the governed workbook's Exceptions sheet content).

## [0.14.0] - 2026-08-01

- **Added** — `CiSpreadPolicyExpert`'s deal-scope tier (FR-SOP-1): every core/convention/overlay
  policy gains a `scope` (institution/product/deal); `load_deal_special_instructions()` parses a
  per-package special-instructions YAML into an ephemeral deal-scoped `Policy`; `CIConductor`'s
  policy step passes it through when `LoanApplication.special_instructions_path` is set, so a
  deal override outranks the program overlay and core for that run only, never persisted.
- **Fixed** — `docintel.py`'s conversion stub only checked a co-located `<stem>.md`, missing a
  valid staged conversion under a document pipeline's own `.japes/` artifact-cache subdirectory;
  that location now takes priority when present.
- **Fixed** — the C&I spreading tab had two separate run paths and only one populated the
  governed-package session state the workbook download button, review queue, and Target
  Template all read from; the tab's own run button now routes through the richer pipeline for
  the single-filing case (the multi-year merge case has no governed-pipeline equivalent yet, and
  keeps its prior behavior).
- **Fixed** — `detect_income_statement_cross_foot` had never been run against a real income
  statement carrying interest/gain-loss/other-income as separate reported lines below operating
  income; verified clean against real figures and added as a permanent regression case.

## [0.13.0] - 2026-07-30

`plan_JACI_CL_GOVERNED_LAYER_UI.md` Phases 0-1 (of 5; Phases 2-5 not started). See
`docs/status/status_JACI_CL_GOVERNED_LAYER_UI.md` for full detail.

- **Fixed** — `detect_income_statement_cross_foot` was checking `income_before_income_taxes`
  against `operating_income - 0`, ignoring that `interest_expense_income_net`/
  `other_income_expense_net` are deliberately excluded from its subtraction chain (correct — their
  sign isn't uniform across filings) but still real, signed components of that subtotal. Produced
  3 guaranteed-false `BLOCKING` findings on every real YETI 10-K run since Wave 1; no test fixture
  built a complete enough income statement to catch it. Now skips a subtotal check entirely when
  an unchecked line precedes it, rather than comparing against an incomplete sum. YETI now
  reports 0 findings.
- **Added** — `_run_ci_spread_phase()` (demo) now also captures `MetricResult[]`/
  `ValidationFinding[]` into session state — `CL_SPREAD_PIPELINE` has emitted both since Wave 1;
  only `SpreadPackage` was ever captured.
- **Added** — `render_spreading_tab` gains optional `package`/`metrics`/`findings` params (same
  seam as `spreader_template_trace(spread, package=...)`) and a governed-workbook download button
  when a `SpreadPackage` is available, distinct from the existing plain-`FinancialSpread` export.
- **Fixed** — `load_ci_workbook_layout`/`load_rb_workbook_layout` (existed since 0.11.0) were never
  exported from the package `__init__`.

## [0.12.0] - 2026-07-30

Wave 3b of `plan_JACI_CL_PRD_COMPLETION.md`: `plan_JACI_CL_REVIEW_SURFACE.md`, all 5 phases
landed. Closes the HIL area (FR-HIL-1/2/3/4, 25% → 100% P0 coverage). See
`docs/status/done_JACI_CL_REVIEW_SURFACE.md` for full detail.

- **Added** — `Correction`/`apply_corrections` (`corrections.py`): a governed, per-correction
  override lineage (author, timestamp, superseded value read from the package, category, required
  rationale) replacing `SmeDecision.corrections`' old bare dict. Corrections produce a new
  `SpreadPackage` layer (`ProvenanceType.OVERRIDE`); `hitl_approval._apply` now re-validates the
  corrected package instead of rectifying flagged findings by fiat, so a correction's effect
  propagates transitively into every metric and covenant test that reads it.
- **Added** — `rank_for_review`/`covenant_feeding_keys` (`review_ranking.py`): a risk-ranked
  review queue ordered by severity, cell confidence, line magnitude, and whether the cell feeds a
  covenant test (the shared chart-of-accounts binding closure `template.py` already used for
  decision-dependency marking). Weights are profile config, not constants.
- **Added** — `resolve_source_region`/`reverse_lookup` (`source_view.py`): a spread cell's source
  coordinate resolved to a viewable region (or an honest reason it can't be), and the reverse
  lookup from a source region to every cell it feeds.
- **Added** — Maker-checker roles (`MakerCheckerRoles`, `check_maker_checker_roles`): three
  distinct, authority-gated actors (analyst/reviewer/approver) rather than one SME id;
  `promote_spread` gained an optional authority gate (approver role, cl.am.005) alongside
  `affirm_spread`'s existing one. Self-review permission is read from the profile, never
  hardcoded. `exception_summary` renders identically to the governed workbook's own Exceptions
  sheet (Wave 3a) by sharing japes' `suggested_action`/`locator_text` rather than re-deriving them.

## [0.11.0] - 2026-07-30

Wave 3a of `plan_JACI_CL_PRD_COMPLETION.md`: `plan_JAPES_2_3_0_GOVERNED_WORKBOOK.md`, all 4 phases
landed. Closes the OUT area (FR-OUT-1/2/3, 17% → 100% P0 coverage). See
`docs/status/done_JAPES_2_3_0_GOVERNED_WORKBOOK.md` (japes) for full detail.

- **Added** — `config/packs/ci-spread-core/workbook_layout.yaml` (the primary governed-workbook
  layout: every statement's full chart-of-accounts row set, the 16-metric catalog, an EBITDA
  Bridge) and `workbook_layout_rb.yaml` (RB's own smaller, differently-shaped sheet set, proving
  japes' new `GovernedWorkbook` reporter is genuinely layout-driven).
- **Added** — `capabilities/commercial_lending/workbook_layout.py`:
  `load_ci_workbook_layout`/`load_rb_workbook_layout`, validating every row against the chart of
  accounts or metric catalog at load time.
- **Changed** — `capabilities/commercial_lending/excel.py`'s cover/statement/trends sheets now
  delegate to `jazzx_sdk.finance.excel`'s own writers instead of a near-duplicate
  reimplementation (the fifth instance of a pattern Wave 1 already collapsed elsewhere).

## [0.10.0] - 2026-07-29

Wave 1 of `plan_JACI_CL_PRD_COMPLETION.md` (the Financial Spreading PRD gap list), all five plans
landed and re-audited: P0 coverage 42% → 61%. See `docs/status/done_JACI_CL_*.md` for full detail
per plan.

- **Added** — Add-back library as pack data (`addbacks.yaml`), categorized/conditional/cappable,
  with a candidate/approved provenance gate on `apply_normalization` and a cross-period
  addback-inconsistency detector extending the existing one (FR-ADJ-2/3/4/5/6/7, FR-VAL-7).
- **Added** — Four arithmetic validation controls (balance control, cash-flow tie, equity
  roll-forward, period continuity), income-statement cross-foot, an FR-VAL-8 disclosure check, and
  `Severity` expanded to the PRD's six levels with an aggregate spread status
  (FR-VAL-1/2/3/4/5/8/10).
- **Added** — Reclassification and break-out engine: Appendix A's move/split/conditional-move
  rules as pack data with a real as-spread `SpreadPackage` projection, the four Appendix A
  break-out cases, `tangible_net_worth`, and a standardized-statement render composing
  reclassification with the existing template (FR-MAP-3/4, unblocks FR-SPR-1/2/FR-RAT-2).
- **Added** — A real Regional Bank (C-DIVE, LLC) reference case: LTM Sep-2023 reproduces the
  borrower's own reference workbook exactly via a real six-period source-precedence stack (assurance
  levels confirmed against each source document's own opinion letter); balance control, leverage,
  current ratio, and fixed-charge coverage all now compute against real figures for all six
  periods; the three PRD-named exit-criterion findings (bad-debt inconsistency, unrecorded ERC tax,
  relief-refund tagging) and the reference workbook's own cash-tie discrepancy are all raised
  against real numbers.

## [0.9.9] - 2026-07-27

- **Added** — Phase 6 of `plan_JACI_CL_PRD_DEMO_ARC.md` (rev 2): a new **Depends** column on the
  🎯 Target Template tab marks rows a credit decision mathematically depended on — derived via a
  graph walk over the covenant policy + metric catalog + template asset
  (`policies.covenant_metric_ids`, `template.rows_this_decision_depends_on`), never from a model
  self-report or a label match. Surfaced a real pre-existing gap: 2 of YETI's 4 covenant-scored
  metric ids have no `MetricDefinition`/template row at all; the walk correctly marks nothing for
  those rather than fabricating a binding.
- **Added** — Phase 5 (Act 1 only) of `plan_JACI_CL_PRD_DEMO_ARC.md` (rev 2): new "🎬 Acts" tab
  presents the demo as an explicit sequence instead of tabs to navigate from memory. Act 1 (clean
  YETI path) runs end to end from one button, sharing a new `_run_ci_spread_phase()` helper with
  the existing 🔗 Trace tab button rather than duplicating the run logic. Acts 2-3 are declared but
  intentionally not built — both need fixture packages arriving from outside plus at least one
  detector Phase 4 declared unguarded (footnote-only-item surfacing; the cash-flow-gap flag).
- **Added** — Phase 4 of `plan_JACI_CL_PRD_DEMO_ARC.md` (rev 2): reconciled the corpus's six defect
  classes with the Financial Spreading PRD's six known traps — 4 map onto existing detectors (2 via
  `validation.py`'s `detect_cross_period_addbacks`/`detect_cross_document_contradictions`, 2 via
  japes' `construct_ltm`, which turn out to be unrelated to `DefectClass.SIGN_LABEL` despite the
  name overlap), 2 have no detector anywhere and are declared `unguarded` via `pytest.mark.xfail`.
  New `tests/eval/gold_cases/ci/trap_*.json` (6 files) + `tests/eval/trap_cases.py` (loader) +
  `tests/eval/test_ci_trap_cases.py` (6 passed, 2 xfailed, plus a coverage-report test).
- **Added** — Phase 3 of `plan_JACI_CL_PRD_DEMO_ARC.md` (rev 2): the 🎯 Target Template tab now
  accrues real columns (As filed / Curated / Extracted + Match) in its existing per-section
  expanders instead of static `"Period 1/2/3" -> "—"` placeholders — populated before any run
  (As filed, Curated) and after the 🔗 Trace tab's spread run (Extracted, with per-row match kind
  and confidence). Retired the duplicate post-run template viewer in `render_spreading_tab()`
  ("📋 Template spread — analyst layout"), so there's one template surface, not two.
- **Added** — Phase 2 of `plan_JACI_CL_PRD_DEMO_ARC.md` (rev 2): `render_pipeline_map()` (`jaci.
  capabilities.commercial_lending.ui.shared`) is now additive/parameterized
  (`pipeline=`/`events=`, both optional, existing callers unchanged) and gains a **Fills** column
  (`template.step_fills()`, derived from `spread_template.yaml` via `template_sections()` — no
  hand-written step-to-section list) and a **Status** column sourced from `vp.activity.*` events
  rather than UI bookkeeping. The demo's spread-phase button now passes a `cl_event_emitter` into
  `run_cl_spread`, and the "🔗 Trace" tab's Phase-1 expander renders the live `CL_SPREAD_PIPELINE`
  map instead of a static, now-stale `CI_SPREAD_PIPELINE` diagram.
- **Added** — Phase 1 of `plan_JACI_CL_PRD_DEMO_ARC.md` (rev 2): the ci_spread demo's spread-phase
  button now runs `CL_SPREAD_PIPELINE`/`run_cl_spread` instead of `CIConductor`.
  `SpreadPackage.from_spread_package()` projects the capability pipeline's richer `SpreadPackage`
  back onto the `FinancialSpread` shape the Target Template tab already consumes; `spreader_
  template_trace` now receives the real `SpreadPackage` so match kind, source coordinate, and
  confidence come from the governed object directly. `CIConductor`/`CI_PIPELINE` remain intact and
  reachable via the "10-K Spreading" tab.
- **Added** — Phase 3 of `plan_JACI_CL_SPREAD_PHASE_CHAT_ASSISTANT.md`:
  `credit_outcome.attach_demo_guidance(fabric)` seeds one deployed, demo-relevant `GuidanceAsset`
  (a field-exam/borrowing-base caveat) into an `InProcessGuidanceStore` and attaches it as
  `fabric.guidance` — a deliberate override of `local_fabric`'s own default (a real
  `RagGuidanceStore` over its mock-backed RAG; routing a fixed demo instruction through the mock's
  embedding-search pipeline is unnecessary fragility). Wired into `_get_jazz_response` for both
  grounding branches. This is the first time `fabric.guidance` produces a visible effect anywhere
  in jaci, not just in an SDK-level japes test — a leverage/borrowing-base question now returns
  `InteractiveResponse.guidance_refs` naming the asset, with the rendered block reflected in the
  system prompt. `plan_JACI_CL_SPREAD_PHASE_CHAT_ASSISTANT.md` is now fully landed (all 3 phases).
- **Added** — Phase 2 of `plan_JACI_CL_SPREAD_PHASE_CHAT_ASSISTANT.md`: Jazz's turn now routes
  through `jazzx_sdk.agents.interactive.chat` (`run_chat_turn`/`build_chat_pipeline`/
  `build_chat_components`) instead of calling `agent.respond()` directly — no escalation in v1
  (every question still answers directly, matching prior behavior exactly; a heavier-reasoner
  hookup is a real follow-up, not built here). Also wires `guidance_pack_id="ci-spread-core"` on
  the spec, connecting Jazz to the guidance-injection hook (japes `plan_JAPES_2_3_0_
  GUIDANCE_INJECTION_HOOK.md` Phase 1) for the first time — a no-op today since no guidance is yet
  deployed for this pack (Phase 3 next).
- **Added** — Phase 1 of `plan_JACI_CL_SPREAD_PHASE_CHAT_ASSISTANT.md`: Jazz (the existing "Jazz
  Assistant" tab in `ci_spread`) now grounds on *this session's live spread*
  (`st.session_state["ci_spread_result"]`) when one exists, instead of always answering about the
  static curated YETI fixture. New `credit_outcome.live_spread_outcome()`/
  `seed_live_spread_fabric()` — the live-grounding counterpart to `yeti_assessment`/
  `seed_yeti_fabric`, carrying computed metrics only (leverage, current ratio, EBITDA, margins;
  no covenant/decision context, since an arbitrary live spread has no YETI-ABL-specific covenant
  policy attached). Same mechanism (`Outcome` → `local_fabric` → `fabric.canonical.find`), just a
  different, generic source; falls back to the curated fixture exactly as before when no live
  spread is present.
- **Added** — a "Chart of accounts & metric catalog" pack-asset section on `ci_spread`'s 🎯 Target
  Template tab (plan_JACI_CL_CHART_OF_ACCOUNTS_AND_CATALOG.md, Phase 4), beside the spread
  template: both `chart_of_accounts.yaml` and `metrics.yaml`, raw YAML viewable, reading live from
  the loaded vocabulary/catalog (not a hardcoded snapshot) — a line or metric added to either pack
  YAML appears with no code change, verified as a test against the loader mechanism directly
  (Streamlit itself isn't unit-testable). `CHART_OF_ACCOUNTS_AND_CATALOG` is now fully landed (all
  4 phases).
- **Added** — `config/packs/ci-spread-core/metrics.yaml` (plan_JACI_CL_CHART_OF_ACCOUNTS_AND_
  CATALOG.md, Phase 3): the 11 C&I metric definitions `dsl_catalog.py` held as Python objects
  (`_DEFINITIONS`, deleted) are now pack data, loaded via the new `metrics_catalog.py`
  (`METRIC_CATALOG`/`METRIC_ORDER`). Execution order (a `CUSTOM_METRIC` dependency before its
  dependent) is derived from the binding graph, not hand-maintained — a circular reference fails
  to load rather than reaching the evaluator (`jazzx_sdk.expressions.validate`, reused as-is).
  `display_method` (new `MetricDefinition` field — see japes CHANGELOG) replaces the old
  module-level `_METHOD` dict. What stays in Python: the `funded_debt` OR-gate (`_any_present`),
  converting a DSL `MetricResult` to jaci's own shape, and copying the package's units onto a
  level metric at evaluation time — behavior, not knowledge. Verified: the YAML-loaded catalog
  computes identically to the retired `_DEFINITIONS` (same sixteen-case parity fixture); adding a
  twelfth metric to a fixture catalog and computing it requires editing only data, demonstrated as
  a test.
- **Added** — `config/packs/ci-spread-core/chart_of_accounts.yaml`
  (plan_JACI_CL_CHART_OF_ACCOUNTS_AND_CATALOG.md, Phases 1-2): the single C&I chart of accounts,
  in the japes `LineVocabulary` schema, collapsing what were four separately-drifting alias
  copies — `dsl_catalog.py`'s `_CANDIDATES` (deleted), `spread_template.yaml`'s per-row `accepts`
  lists (now a single canonical `key` per row) and `template.py`'s matching locator tuples (one
  copy in two forms), and a fourth copy this plan's own investigation found that the written
  plan's grounding notes didn't name: `analytics.py`'s own inline candidate lists inside
  `compute_metrics()`. `analytics._vals`/`_vals_traced` now resolve through the vocabulary
  (statement-scoped first, falling back unscoped for a concept that legitimately repeats verbatim
  across statements, e.g. `net_income`); `_vals_traced` reports the resolver's real `MatchKind`
  (`exact_key`/`alias_key`/`exact_label`/`normalized_label`/`substring`/`unmatched`) instead of an
  inferred `"key"`/`"label"`/`"none"` bucket. `compute_cre_metrics` (CRE/REIT, explicitly out of
  scope) is untouched, kept on a preserved `_vals_legacy`. Classification follows PRD Appendix A
  verbatim, only where it calls out an explicit GAAP-deviation (most lines correctly carry none).
  Verified byte-identical against a representative 64-row fixture's `template_csv_text` output
  captured before this change — three rows needed a narrow, empirically-justified opt-in
  `allow_substring` (found via that exact diff, not guessed) to preserve output; documented inline
  in the YAML. `dsl_catalog.py` now resolves through this same authored vocabulary instead of its
  own Phase-4 proof vocabulary from `plan_JAPES_2_2_0_LINE_VOCABULARY.md`.
- **Changed** — `dsl_catalog.py`'s line resolution is now vocabulary-backed
  (plan_JAPES_2_2_0_LINE_VOCABULARY.md Phase 4, requires japes ≥ 2.2.0 with `LINE_VOCABULARY`
  landed) instead of its own private `_CANDIDATES` candidate map, which is deleted. A small,
  module-local `LineVocabulary` (`_VOCABULARY`) covers the same 13-key inventory `_CANDIDATES`
  did — this is *not* yet the authored pack-YAML chart of accounts reconciling all three of
  JACI's alias copies (that's `plan_JACI_CL_CHART_OF_ACCOUNTS_AND_CATALOG.md` Phase 1); this is
  the proof step for japes's own Phase 4 acceptance criterion. Verified byte-identical to the
  pre-change output across the existing sixteen-case parametrized fixture.
- **Added** — `compute_metric_results(..., use_dsl=True)`: the C&I metric catalog (EBITDA, free
  cash flow, funded debt, margins, current ratio, debt-to-equity, leverage, revenue growth) is now
  also computable via japes's Expression DSL (`jazzx_sdk.expressions`, requires japes ≥ 2.2.0)
  instead of hand-written Decimal arithmetic — same candidate-based line lookup, same
  skip-if-missing-input/skip-if-zero-denominator behavior, same per-metric rounding. Kept opt-in
  behind the flag for one release; the default Python path is unchanged. Verified byte-identical
  to the existing Python path across `tests/unit/test_metric_result.py`'s full fixture (its 8
  tests now run parametrized over both paths) — there is no separate C&I gold-case corpus for
  this specific function to verify against.
- **Added** — the C&I spread template is now a pack asset (`config/packs/ci-spread-core/spread_template.yaml`) instead of an in-code constant (`plan_JACI_CL_SPREAD_TEMPLATE_ASSET.md`, Phases 1-3): `template.py::_load_template()` reconstructs the same in-code shape from the YAML (byte-identical, with a fallback if the asset is missing); each row's alias vocabulary (`accepts`) is now declared and inspectable instead of an undocumented tuple. A new **"🎯 Target Template"** tab on `ci_spread` renders the sections/rows/accepts with no run behind it (also surfaced in the Concepts view alongside the other pack assets). The **📊 Spread** tab's curated-vs-spreader comparison gained a **Match** column (`analytics._vals_traced` + `template.spreader_template_trace`): which alias a statement row matched on (`key`/`label`) or the `MetricResult` derivation formula for a computed row, with an unmatched-rows warning printed rather than silently blank.
- **Added** — a "Bulk intake" tab on `ci_spread`'s spreading page demonstrating japes's new document-pipeline `collection` route (`agents.document.pipeline`): classify a folder of loan documents, a standalone zip, or a whole Knowledge Hub collection in one batch via `DocumentAgent.process_dir`, run through `run_document`/`DocTurn` — no combined-PDF assumption, one bad/scanned file doesn't sink the rest of the batch. The EDGAR-fetch tab now also runs through this same pipeline (its `single` route) for consistency. Requires japes ≥ 2.1.5 (needs its document-pipeline collection route + `DocTurn.degrade` fix — see japes CHANGELOG).
- **Changed** — `ci_spread`'s EDGAR-fetch and package-intake demo tabs now extract via `DocumentAgent` (`agents.document.agent`) instead of calling `process_10k`/`extract_financials` directly — same UI, but every field now carries per-field confidence and grounding, with sub-floor values refused (never silently written) instead of trusted as-is. Requires japes ≥ 2.1.5 (needs its `DocumentAgent._grounded` whole-number-float fix — see japes CHANGELOG).
- **Added** — `commercial_lending.spreader.spread_financials(doc_json=...)` — a JSON-sourced counterpart to the markdown/HTML statement locator, for a scanned filing converted via Azure DocIntel's structured JSON output instead of its markdown rendering (which has no real `<table>` tags for table-mode anchors to find, and can silently drop multi-line cell content through markdown-tag-stripping). `docintel.convert_document_json` mirrors the existing `.md` stub with a co-located `.json` one; `spread_filings` prefers it when staged. Requires japes ≥ 2.1.5.
- **Added** — **HITL corrections feed the learning loop** — `hitl_approval`'s recorded `Feedback` now also flows through `to_signal()` into japes's Curator Layer 2 (`synthesize_bucket`), landing a draft `GuidanceAsset` an SME can review/approve — closing the loop from a corrected spread line (e.g. `gross_profit`) to reviewable guidance for future runs. Requires japes ≥ 2.1.4.
- **Changed** — consolidated scattered root demo scripts into their scenarios: `ci_spread` (`demo_correction_to_guidance.py`), `earnings_anthropic` (`run_earnings_demo.py`/`run_spread.py`, promoted in as its first interactive demos), `kyc_anthropic` (dropped the stale `demo_kyc_minimal.py`/`demo_kyc_case.py`/`run_kyc_demo.py`, folding their policy-citation-completeness check and canonical-trace summary into `demo_page.py`'s Review tab instead).

## [0.9.7] - 2026-07-22

- **Added** — **Stage 5: SME-governed spread approval (human-in-the-loop, with learning)** — `spread_approval_engine` composes the JAPES conductor's suspend/resume (`SuspendRun` → `engine.resume`) with jaci's `affirm_spread`/`promote_spread`: a spread with blocking (ambiguous) findings pauses the run for SME review (`ApprovalRequest` payload lists the flagged lines); on approval it affirms + promotes (the flagged findings rectified) and records the SME's judgment as `Feedback` linked to the deal (feeds `synthesize_cases_from_feedback` → `optimize_prompt`, so the learning persists); on rejection it halts. A clean spread auto-approves without pausing. New `commercial_lending.hitl_approval`. Requires japes ≥ 2.1.1.
- **Added** — **feedback on the Jazz assistant** — the C&I "Jazz" chat (`InteractiveAgent`) now passes a `conversation_id` and surfaces each reply's turn ids, with 👍/👎 + a correction box per answer that records `Feedback` to a session `FeedbackStore` — the turn→trace→feedback→learning spine on the live assistant. Requires japes ≥ 2.1.1.

## [0.9.6] - 2026-06-19

- **Changed** — the spreader's LLM convert step (statement grid → typed `Statement`) now delegates to the SDK's `jazzx_sdk.finance.structure_statement`; the structuring prompt lives there, next to the `FinancialSpread` schema it produces. The pack supplies only the per-segment anchors. Requires jazzx_sdk ≥ 1.9.4. (This also resolves a regression where the spread-anchors YAML refactor had dropped the local prompt, breaking the YETI markdown-spread path and the Concepts "Mode tunings" view.)
- **Fixed** — a `_render_cases` name-shadowing in `dashboard_view` (a demo-only-branch local import shadowed the module-level helper) that raised on any scenario with a dashboard.
- **Fixed** — Demo tab now degrades gracefully on a load error: `scenario.demo()` lazily imports the demo module, which was evaluated as a `_safe(...)` argument (outside its try), so an import error escaped to Streamlit's full-page error screen; deferred into `_safe`'s try so it renders in-tab like the other views.
- **Added** — `portfolio_monitoring`: a Portfolio-Manager CRE annual-review scenario rendered as the *JazzTrack* book — a multi-loan `jazzx_sdk.Portfolio` across the pipeline states (most loans autonomous/reaffirmed, a single-digit Attention Zone) with state-count/by-PM/exposure tiles. The one worked exception, Grove Commons, carries the full document-derived review: bank-side DSCR spread from the T-12 (commercial-lending spreader), CCC→loan-agreement covenant reconciliation, occupancy from the rent roll, and the AR package + watchlist recommendation. Requires jazzx_sdk ≥ 1.9.4 (`Portfolio`).
- **Added** — Mesa Verde: a second CRE case (property T-12 acquisition) alongside MAA, with a deal selector on the CRE demo. T-12 spread live from the `.xlsx` (SDK `convert_document`); Jazz is the SDK `InteractiveAgent` grounded in the underwriting `Outcome` via `fabric.canonical.find`; golden case + conductor trigger + Trace tab.
- **Changed** — ci_spread (YETI) Jazz now routes through the SDK `InteractiveAgent`, grounded in a deterministically-computed credit `Outcome` (`fabric.canonical.find`). The Outcome (covenant status + indicative decision, no LLM) is also surfaced on the covenant tab.

## [0.9.5] - 2026-06-17

- **Added** — C&I demo: a live "Run credit analysis" button on each application-stage case (ACE / TechFlow / HighLev / MidMarket) runs the Phase 2 conductor loop and renders the decision, leverage/FCCR, policy-gate concerns, and expected-vs-actual.
- **Changed** — ci_spread evidence types are authored as data: `config/packs/ci-spread-core/evidence_types.yaml` loaded via the SDK `EvidenceTypeRegistry` and passed to `CIToolRegistry`. Drops the `CIEvidenceType` enum (`EvidenceRequest.evidence_type` is now `str`) and the hard-coded `get_available_tools()` (inherited from the registry); the registry validates its tools against the declared vocabulary. The Investigator's requestable vocabulary is injected from the same YAML (the mode tuning keeps only request strategy/order). Adding a source is a YAML edit.
- **Changed** — ci_spread drops its `CIPolicyExpert` subclass. The conductor now configures the SDK's `DefaultPolicyExpert` directly from pack data (`CI_REGISTRY` + `CI_CORE_POLICY_IDS` + `OVERLAY_MAP`) and registers the instance via `ExpertRegistry.register_instance`. Overlay-aware resolution and condition-gate compliance now live in the SDK; the pack ships only data. Requires jazzx_sdk ≥ 1.8.8.

## [0.9.4] - 2026-06-16

- **Added** — the harness-based eval runners (ci / cre / kyc) can publish each run to MLflow via the SDK's `MlflowReporter`, **opt-in** with `JACI_EVAL_MLFLOW=1` (shared `tests/eval/eval_reporter.py`, using jaci's configured tracking URI / experiment). Default is unchanged (local JSON / `RunHistory`). Requires jazzx_sdk ≥ 1.8.7.

- **Changed** — spread statement anchors and Phase-0 intake config are now authored as data: `commercial_lending/spread_anchors.yaml` (per-segment titles/keys/window-or-table mode/auditor-report skip, loaded via `ExtractionTemplate.from_dict`; spreader 225→167 LOC) and `config/packs/ci-spread-core/intake.yaml` (doc-type keyword map + required types). Completes the conductor/policy/anchors/intake config→YAML pass.

- **Changed** — all four policy registries now author their canonical `Policy` objects as data (loaded via `jazzx_sdk … load_policies`) instead of in-code `Policy(...)` literals — **~1,600 Python LOC moved to config**: aml 627→33, kyc 488→20, cre 362→22, ci_spread 237→28. ci_spread splits into `core.yaml` (doc-extracted: leverage) + new `conventions.yaml` (hand-authored FCCR/ABL/lien + Regional Bank overlay), preserving the demo's extracted-vs-`stub` distinction. Registry objects, indexes, named-policy constants, overlays, and accessors preserved; round-trips verified identical.

- **Changed** — all scenario conductor pipelines now load from declarative YAML via `ConductorPipeline.from_yaml` instead of in-code `ConductorPipeline(...)` literals: ci_spread (`config/packs/ci-spread-core/pipelines.yaml`) and cre/aml/kyc_anthropic/earnings (`scenarios/<scenario>/pipeline.yaml`). ~205 Python lines moved to config; pipelines verified structurally identical. First wave of the code-as-config → pack-YAML effort.

## [0.9.3] - 2026-06-15

- **Changed** — JACI now delegates platform plumbing to the SDK: LLM provider/model/key resolution (`commercial_lending/_llm.py` → `jazzx_sdk.llm` resolvers, prefix `JACI_`), mode-prompt assembly (`common/utils/prompt_loader.py` → `modes.compose_mode_prompt`, base ⊕ pack tuning), and fabric config (`common/fabric_config.py` → `fabric.FabricConfig.from_env` / `fabric_from_env`). Mode prompts are byte-identical; `create_fabric()` now works (it previously imported a non-existent `Fabric`). Requires a jazzx_sdk build with these helpers.

- **Changed** — the commercial-lending spreader now delegates document region location, HTML flattening, and LLM structuring to the SDK's `jazzx_sdk.tools.extraction` (`ExtractionTemplate` / `locate_region` / `flatten_region` / `structure_region`) instead of its own private `_find_region` / `_find_table_region` / `_region_rows`. The segment anchors (`_SEGMENTS`) now build an `ExtractionTemplate`; behavior is unchanged. Requires a jazzx_sdk build that includes `tools.extraction`.

- **Added** — Concepts "Mode tunings / prompts" now shows the actual **spreading extraction prompt** (system + user) for C&I/CRE — the LLM step the Phase 1 spread runs to convert located statement rows into canonical JSON. The prompt is refactored into a reusable `_EXTRACT_PROMPT` template with an `extraction_prompt_preview()` accessor (`commercial_lending/spreader.py`); no behavior change to extraction.

- **Added** — Concepts page now surfaces the **spread extraction template** (the statement anchors the spreader uses to locate the audited statements in a 10-K) as a crafted asset alongside the policies/checklist/playbooks — title cues, signature line items, and locate mode per statement, plus the statement-end cues. Read-only view of the in-code `_SEGMENTS` config (`commercial_lending/spreader.py`). Includes an **inspector** — pick a statement to run the real anchor search on a sample 10-K (YETI) and see the located snippet plus the preceding lines, so the search is narratable in the demo (`spreader.locate_preview`).

- **Added** — Spread tab now has a **SEC as-filed evidence** reconciliation: the audited FY2025/FY2024 figures parsed from the YETI 10-K, shown as the authoritative third reference that adjudicates each Curated-vs-Spreader mismatch (Curated ≠ SEC → the analyst fixture rounded; the Spreader extracts the as-filed number). Surfaces which curated lines diverge (net income, total assets, equity, …).

- **Added** — `CIConductor.run_spread()` and `CI_SPREAD_PIPELINE`: the spread phase (intake → entity extraction → spreading → validate → persist) as a standalone conductor entry, separate from the full credit-analysis loop (`run_analysis`/`CI_PIPELINE`). The Trace tab now splits into **Phase 1: Spread** (runs live) and **Phase 2: Credit analysis** (built/runnable, shown as next), with a dedicated "Run spread phase" button and a spread-phase result panel. The Concepts page and Trace tab both show the spread flow as the primary conductor diagram, with the full pipeline (renamed **C&I Lending — Credit Analysis**) collapsed in an "extended (speak-to)" expander; the full diagram shows the Phase 1 `FinancialSpread` as an input box feeding the loop. Driven by optional `focus_pipeline_target` / `focus_handoff` on the scenario registry. Honest about what each phase does; the loop wiring of the spread into Phase 2 evidence remains future work.
- **Changed** — CI Spread tab is now an always-visible **Curated vs. Spreader** template comparison. The Curated column is built from the analyst fixture (`yeti_financials.json`); the Spreader and Δ columns show `—` until **10-K Spreading** runs, then fill in live with a ✅/⚠ match indicator (≤1% tolerance). New `curated_template_values` / `spreader_template_values` helpers in `template.py`. Replaces the old run-gated analytics view.
- **Changed** — Concepts tab now surfaces the ontology properly: the section is expanded with the entity/relationship graph, an **entity inspector** (pick an entity → its description, `source_schema`, and fields), the relationship predicates, and the derived-concept formulas with `policy_ref` / `resolved_by`. Previously a collapsed expander with just a flat name list — now it reflects the richer v0.2.0 ontology (24 entities).

- **Added** — CI ontology `ci_lending.yaml` → v0.2.0: extended from 9 entities/8 relationships to **24 entities / 32 relationships**. Adds the **spread layer** (FinancialSpread, SpreadStatement, SpreadLine, BorrowingBaseResult), **metrics layer** (CreditMetrics, WorkingCapitalMetrics), **decision layer** (CreditDecision, CreditCondition), and the **doc/policy/evidence layer** (SourceDocument, Evidence, Hypothesis, Policy, Rule, SourceRef, Playbook) — so the doc→object + PolicyExpert flow is first-class in the KG (e.g. `FinancialSpread extracted_from SourceDocument`, `CreditDecision validated_against Policy`, `Policy cites SourceRef`). Entity fields trace to the real schemas via `source_schema`; `BorrowingBase`/`FCCR` concept formulas cross-linked to their backing entities (`resolved_by`). YAML-only, no code change.

- **Fixed** — PolicyExpert two-tier gating now actually fires. `check_compliance` claimed fields globally, so only the first rule per metric ran — the second-tier rules (e.g. leverage `≤3.0 → require_evidence` behind `≤3.5 → require_approval`; FCCR `≥1.25` behind `≥1.15`) were silently skipped. Field precedence is now per-policy: overlay-over-core still wins a field, but both tiers within a policy evaluate (verified: leverage 3.2x → `CI-LEVERAGE-WARNING` require_evidence; 4.0x → both gates).
- **Added** — 10-K Spreading tab: an **inline viewer** for the template spread (analyst layout — statements + Credit Metrics + Working-Capital days), rendered from `template_rows` as a table so you can read it online without downloading the CSV.

- **Added** — deck-alignment: surfaced existing-but-hidden logic in the YETI demo to match the platform deck's claims (UI-only). (1) **Three-column spread** (reported / adjustment / adjusted, FY2025) on the Spread tab once the 10-K is spread, matched by `SpreadLine.key` vs the analyst spread. (2) **Policy sources** table on the Covenants tab — every rule → its source document (from real `source_refs`, clickable). (3) **Accuracy scorecard** — Overview relabeled + a live `validate_spread` grade when the spread has run; `EvaluationReport` promoted to the top of the live trace. (4) **KG/Entities** snapshot on Overview (Borrower/Facility/Lien from the golden case) + a **Playbook Expert** expander in the fixture trace (synchronous `diagnose_map` replica → matched playbook + `guidance_refs`, no LLM).

- **Changed** — consolidated the policy sources so every surface reads the same artifacts. The application checklist is now built from the **extracted `checklist_ci.yaml`** (88 items, from the PDF) instead of a duplicate hardcoded `_SEGMENTS` list (`document_checklist_policy` reads the pack YAML, `_SEGMENTS` is a fallback — CRE unchanged). The **Docs & Policies** tab now also shows the credit-underwriting policies (`CI_REGISTRY`) with `extracted` vs `stub` marks — previously it showed only checklist + covenants (the "2"). Concepts, Docs & Policies, and Covenants now reflect one consistent set.
- **Changed** — the Covenants scorecard sources its thresholds from the canonical `covenant_policy('ci')` Policy object (the same canonical form the conductor's PolicyExpert/Governor enforce), not the curated `yeti_financials.json` config — so the policies are visibly used in the credit view, not only in the live conductor run. (Values unchanged; source is now canonical.)
- **Added** — "🔍 The SDK at work" panel on the YETI Overview: maps the demo to the SDK substrate — the **canonical objects** the conductor emits (`fabric.canonical`), that each mode step runs through `AgentExecutionService` (on the **OpenAI Agents SDK** when the provider is OpenAI), and the fabric surfaces in use. Sourced from the conductor pipeline + `platform_catalog` (no hand-maintained copy).
- **Changed** — the conductor diagram groups its 13 steps into 5 labelled phases (Intake → Investigate (loop) → Synthesize → Govern → Record) via `PipelineStep.phase` + Graphviz clusters, so the flow reads as a handful of phases instead of a long flat list. No pipeline change — display only (needs japes with `PipelineStep.phase`; ungrouped fallback otherwise).
- **Fixed** — the 10-K spreading tab now actually does what it claimed: it **reconciles** the LLM-extracted figures against the filing's reported numbers (`validate_spread`, ≤1% tolerance, recurring keys pinned to their statement) and shows a pass/fail table — previously "validated against SEC XBRL" was asserted but never run. Demo copy corrected to say the model is **the configured one** (default OpenAI `flex_gpt-5.4`), not a hardcoded Anthropic model.
- **Changed** — made the LLM-vs-us split explicit in the demo: the LLM **only extracts** the as-reported statement lines; **we compute all derived analytics deterministically** (margins, Adj. EBITDA, credit ratios, working-capital days, borrowing base, covenants via `jazzx_sdk.tools.financial`) and reconcile to the filing. (No code change to the split — it was already this way — just surfaced honestly.)

- **Added** — surfaced the doc→object story in the demo: YETI **Overview** tab ends with which pack assets are extracted from a source document (checklist PDF, OCC handbook + 10-K, loan package) and a **our-outcome vs. curated loan-package** comparison table (decision/advance-rates/financials match; borrowing-base + lien-condition gaps). On **Concepts**, policies/playbooks not extracted from a source are flagged **`stub`** (honest-by-exception — no broad "these are real" claims); extracted ones show their doc → object provenance.
- **Added** — doc → Playbook extraction: `scripts/extract_policy.py playbook` parses a source doc's section outline into a playbook markdown scaffold (with the `## section_id:` anchors PlaybookExpert reads) + `source_doc` provenance, emitted "pending SME review" (honest about auto-extraction). First output: `playbooks/loan_package_scaffold.md` from the real YETI Comprehensive Loan Package; registered in the manifest; Concepts shows the doc → playbook lineage.
- **Added** — doc → Policy/checklist extraction pipeline (offline, scripted; interim before a Domain Pack Studio + DiscoveryExpert). `scripts/extract_policy.py` parses a source doc (local path *or* online URL) into pack YAML with source provenance, and `verify-policy` checks each cited passage really appears in its source + the schema validates. First outputs from real YETI/regulatory docs: `policies/checklist_ci.yaml` (12 sections / 88 items, extracted verbatim from the application checklist PDF) and `policies/core.yaml` (leverage policy citing the OCC handbook framework + the YETI 10-K net-leverage covenant, numeric ceiling marked as the credit-agreement term). The Python registry now loads leverage from `core.yaml` (YAML is the source of truth); Concepts shows the **doc → object** lineage (source doc, cited passages, the resulting policy as YAML) and the checklist object.
- **Changed** — Platform view (🔍 JazzX): each cognitive mode is now badged by how it's implemented — 🤖 LLM agent · ⚙️ rule engine · 🐍 Python logic · 🔀 agent+rules · 🚧 planned (from `platform_catalog.MODE_KINDS`, with a legend), answering the recurring "which modes are real agents?" question. Modes are laid out by faculty across columns and experts/fabric/objects in a 3-column row, fixing the prior right-column overflow / needless horizontal scroll. Falls back to a local copy if the installed japes lacks `MODE_KINDS`.
- **Added** — security-context propagation (queue/server handler): the per-message token (`ctx.security_context`) is forwarded onto every outbound Knowledge Hub call as an `x-security-context` header, via a ContextVar set/reset around `handle()` and a `request_headers_provider` registered on `JazzXRuntime` (mirrors macer's pattern; japes already exposes both hooks). KH 403s without it. On the UI path it's settable from Settings (`JAPES_SECURITY_CONTEXT`) and sent alongside `x-user-id` (japes ≥ 1.8.5).
- **Fixed** — `japes_handler` imported `AlertTrigger` from `jaci.schemas` (which doesn't export it — only a docstring example), so the queue/server handler couldn't import at all; now imports from `jaci.scenarios.aml.schemas.case_context`.
- **Fixed** — the UI app reads `LOG_LEVEL` at startup (previously hardcoded INFO), matching the queue runner + the Settings live-apply.
- **Fixed** — AML conductor mapped `GovernorMode`'s output (japes `modes.schemas.GovernorDecision`) to this pack's `GovernorDecision` before building the `CaseFile`; passing the foreign instance through raised a Pydantic `model_type` error (cross-package class identity). [was tracked issue (c)]
- **Tests** — conftest now loads the repo `.env` so live-LLM tests actually run locally (keys were invisible to the test process, so they silently skipped); the `requires_api_key` gate accepts any provider key (OpenAI/Anthropic/Gemini). The AML conductor integration tests are no longer hard-skipped — they run live when a key is present (3 pass; `test_full_investigation_loop` stays `xfail` on the remaining tracked issue **(b)**: the OpenAI agent path can't strictly enforce the generic `HypothesisUpdate` schema, so the LLM may omit `hypotheses[].content`). Requires japes ≥ 1.8.5 (OpenAI agent provider `final_output` fix).
- **Fixed** — CRE/MAA demo crashed (`TypeError: ...NoneType.__format__`) when a spread metric was None for the latest period; metric rendering now goes through a None-safe `_fmt_metric` (renders `n/a`). Regression test added.
- **Changed** — every view (Concepts / Demo / Dashboard / system views) renders through a `_safe` wrapper: a view error is logged and shown in-place (message + collapsible traceback) instead of taking down the whole Streamlit app. The MAA Jazz fallback message is now provider-neutral (was hardcoded to "Anthropic").

## [0.9.2] - 2026-06-14

- **Added** — every scenario now declares its own `ConductorPipeline` via `<X>Conductor.describe()` (CRE, AML, KYC, Earnings — joining C&I); the Concepts conductor diagram renders each domain's real flow instead of borrowing C&I's. CRE adds a DSCR stress-test step; AML a SAR + deadline-guard tail; KYC/Earnings are Anthropic-agent review loops (no Sentinel). All scenario conductors are now `jazzx_sdk.conductor.BaseConductor`. Registry `pipeline_target` wired per scenario.
- **Added** — CRE and AML emit versioned `CaseContext` checkpoints at loop boundaries (run open / each iteration / final) via the new `jazzx_sdk.conductor.Checkpointer`, restartable with `Pack.resume(case_id)`. ci_spread refactored onto the same SDK Checkpointer (drops its hand-rolled seq/persist code); each conductor now supplies only the domain `_build_case_context` mapping. Requires japes ≥ 1.8.4.
- **Changed** — model currency: Anthropic default Sonnet 4.5 → 4.6 (and Opus 4.7 → 4.8) across scenarios/UI. Model pickers add Haiku/Opus variants (Sonnet stays the Anthropic default). The Settings `JACI_LLM_MODEL` picker is now a combo — pick a preset or type any model not in the list (no raw-`.env` editing).
- **Added** — Gemini as a selectable provider (`JACI_LLM_PROVIDER=gemini`, key from `GEMINI_API_KEY`/`GOOGLE_API_KEY`); model presets `gemini-2.5-flash`/`-pro` in both pickers; Settings gains a `GEMINI_API_KEY` field. Requires japes ≥ 1.8.4 (GeminiProvider). Tool-calling agent loops remain openai/anthropic; structured-output modes + entity extraction work on Gemini.
- **Added** — C&I policy `SourceRef`s carry authoritative URLs (OCC Comptroller's Handbook, FDIC Risk Management Manual); the Concepts policy inspector renders sources as clickable links when a `url` is set.
- **Fixed** — Settings: KH group now exposes the auth knobs japes actually reads — `JAPES_KH_USER_ID` (the `x-user-id` KH's Keto authz keys on) and `JAPES_KNOWLEDGE_HUB_TOKEN` (bearer); previously only `KH_API_KEY` was shown, so a UI-only setup would 401. When `JAPES_KNOWLEDGE_HUB_URL` is unset but the platform `KNOWLEDGE_HUB_URL` is, the field shows that effective value (placeholder + caption) without pinning it into the namespaced key on save (mirrors japes' runtime resolution); `LOG_LEVEL` is now honored (`basicConfig` reads it; Save applies it to the root logger live). Added a note that edits take effect only after Save & apply.

## [0.9.1] - 2026-06-13

- **Changed** — Concepts/demo read one `jazzx_sdk.pack.Pack` (policies/conductor/ontology/playbooks) instead of stitching loader + registry + pipeline; `CIConductor` declares its pipeline via `describe()` (manifest `policies.registry` / `conductor.pipeline` pointers). Requires japes 1.8.2.
- **Added** — Concepts leads with a Domain Pack assembly diagram (sources → policies/playbooks/ontology → experts → conductor); expandable detail shows each policy/playbook as the authored asset *and its end format in the expert*; the conductor diagram renders the investigation loop.
- **Added** — `CIConductor` writes versioned `CaseContext` checkpoints (§7.1) — run start, each iteration, pre-synthesis, run end; the Trace tab surfaces the per-iteration trail via `pack.case_contexts()`.
- **Fixed** — Platform view (🔍 JazzX) was stale (7/13 modes, 2 invented experts, 5/13 canonical objects); now reads `jazzx_sdk.platform_catalog` (13 modes, experts from the registry, 13 objects) with a corrected local fallback. Needs japes 1.8.3 for the SDK source.
- **Changed** — conductor execution kinds now describe a step's *intended wiring* (live / deterministic / offline_asset / integration), not "forever a stub"; the diagram shows the design as fully wired, with a per-run overlay to mark steps that ran as stubs in a given environment. Needs japes 1.8.3.
- **Added** — evidence tools serve **real** YETI 10-K data (financials + borrowing base) from `yeti_financials.json` via the fabric→real cascade; A/R aging, debt schedule, and UCC remain labelled placeholders (`source_system: mock.*`) until a real source is wired.
- **Added** — one-click **template-CSV** download of the full spread (analyst layout: statements + Credit Metrics + Working-Capital days) alongside the Excel workbook; reference template committed at `docs/ci_spread/YETI_Spread_Template.csv`.
- **Added** — the demo conductor run uses the **connected Knowledge Hub** fabric when configured (`JAPES_KNOWLEDGE_HUB_URL` + `FABRIC_MODE=cached|strict`), else a local Mock; evidence tools read from it and fall back to local data when a doc is absent. The Diagnostics "Ingest → KH" button now also **seeds structured evidence** under the `{loan_id}/<type>.json` keys the tools read. Logs the fabric in use + real/stub evidence counts (visible in `jaci_logs/jaci.log` and the Trace-tab per-run conductor caption). `.dockerignore` now drops all LoanSamples PDFs (the `.md`/`.json` ship).

## [0.9.0] - 2026-06-12

- **Changed** — UI restructured around a scenario registry: top-bar nav + ⚙ menu replace the left sidebar; Concepts → Demo → Dashboard tabs; "JACI" → "JazzX".
- **Added** — Concepts landing tab (conductor flow, ontology, policies, playbooks, cases) + global Platform overview.
- **Added** — spread output conforms to the analyst template (Credit Metrics + Working-Capital days).
- **Changed** — adopt the SDK: Concepts reads the pack via `PackManifestLoader`; spread schema + metrics come from `jazzx_sdk.finance` / `tools.financial`. Requires japes 1.8.1.

## [0.8.4] - 2026-06-12

- **Fixed** — Case Explorer / Flow Viewer showed 0 hypotheses/evidence and a ❓ decision (harness stored only pass/fail). `run_ci_eval` now captures per-case hypotheses/evidence/decision via `case_detail_fn`; loader and decision emoji map updated. Re-run the eval to populate.
- **Requires japes 1.8.0** — the OpenAI default provider now works (japes structured-output fix); also provides `case_detail_fn`.

## [0.8.3] - 2026-06-12

- **Fixed** — Docker build shipped an image missing `jazzx_sdk` (README.md not copied → hatchling metadata failed; `|| true` masked it). Copy README, `set -e`, build-time import assertion.
- **Added** — `GITHUB_TOKEN` build-arg fallback to the BuildKit secret.

## [0.8.2] - 2026-06-12

- **Added** — PlaybookExpert surfaced in the Trace tab (pipeline step + `guidance_refs`).

## [0.8.1] - 2026-06-12

- **Added** — `CIPlaybookExpert` (config-driven via `diagnose_map.yaml`; emits `guidance_refs`); wired into `CIConductor` (advisory) + Evaluator. Requires japes 1.7.1.

## [0.8.0] - 2026-06-11

dev-daily enablement (requires japes 1.7.0): selectable LLM (`JACI_LLM_PROVIDER`/`MODEL`, default OpenAI), Diagnostics page (KH status + doc ingestion to KH), Settings page (edit `.env` from the UI).

## [0.7.9] - 2026-06-11

Self-contained demo image: committed demo fixtures (10-K `.md`, spreads, loan PDFs) + `.dockerignore`.

## [0.7.8] - 2026-06-11

Containerization for dev-daily (requires japes 1.6.9): `jaci.main` `JAPES_RUN_MODE` entrypoint via `jazzx_sdk.serve`; Dockerfile with `[ui]` extras + pandoc.

## [0.7.7] - 2026-06-11

Two-borrower commercial-lending demo (YETI C&I + MAA CRE) + eval-framework wiring (requires japes 1.6.8): financial spreading engine (10-K → `FinancialSpread` → Excel/CSV, validated vs SEC XBRL), segment-aware spreader, policy/covenant canonical objects, shared demo UI, wired onto japes document/ratio tools.

## [0.7.6] - 2026-06-09

- **Fixed** — dashboard prompt-editor path, eval-runner target (`jazzx_sdk.evaluation`), L3 KYC path; stale eval scripts (`max_iterations`, `recommendation`).

## [0.7.5] - 2026-06-08

- ci_spread Phase 1 KG writes via `fabric.graph` (not `fabric.kh`), with a mock fallback so triples persist in dev/demo.

## [0.7.4] - 2026-06-08

- ci_spread PRD Phases 0-1 (document intake + entity-extraction/KG) + evaluator wiring + fixture-driven Trace tab.
- Aligned AML/CRE/KYC/kyc_anthropic conductors to JAPES 1.6.4 base contracts (`Context` loop methods, `evidence_requests`, `CanonicalTrace.for_pack`) and fixed their stale-contract breakages.

## [0.7.2] - 2026-06-08

- C&I Spread full pack buildout (`ci-spread-core`): schemas, `CIContext`, policy registry + overlay, `CIPolicyExpert`, 7-tool registry, `CIConductor` loop, evaluator, prompts, golden cases. Live multi-provider Jazz tab. Aligned to JAPES 1.6.4.

## [0.7.1] - 2026-06-06

- Adopt the JAPES evaluation framework (`GoldenCase`/`EvaluationHarness` from `jazzx_sdk`); KYC/CRE/CI eval scripts + golden cases.

## [0.7.0] - 2026-06-06

- C&I Spread scenario intro; modularized dashboard (1375 -> 49 lines) + extracted UI pages; `app.py` 2873 -> 71; removed the monolithic patch script.

## [0.6.4] - 2026-06-05

- CRE/AML fixes (`uuid4`, ReasonerMode `output_schema`); CRE adopts JAPES 1.5.x infra (`Depend`, `RatioEvaluator`, `ScenarioReport`, `Artifact`).

## [0.6.3] - 2026-06-04

- Tool registries use JAPES Fabric for mode-based retrieval; deprecated `use_mocks` / hub-client params.

## [0.6.2] - 2026-06-04

- Scenario-registry architecture (truly multi-domain); CRE eval harness; rebrand: JACI = "Contextual" Intelligence.

## [0.6.1] - 2026-06-04

- Interactive CRE demo in the main app (Jazz sidebar, drill-down findings).

## [0.6.0] - 2026-06-03

- CRE underwriting scenario: domain models, 8-tool registry, conductor, 5-mode prompts, evaluator, golden case.

## [pre-0.6.0] - 2026-05-28

- Removed ~198 lines now in JAPES 1.3.0 (agent utils, `parse_model_tier`); updated to JAPES 1.3.0.

## [0.3.0] - 2026-05-27

- KYC (OpenAI) scenario parallel to kyc-anthropic; multi-provider benchmark infra; shared KYC gold cases.

## [0.2.1] - 2026-05-24

- ThreatIntelHandler wires `kernel_client` for real web search (requires JAPES 1.2.3+).

## [0.2.0] - 2026-05-14

- AML Expert layer (5 experts: Investigative/Governance/Evidence/Policy/Playbook) on JAPES 0.5.0.
- Canonical Policy schema (`Policy`/`Rule`/`Expression`, Schema Spec v1.0); policy registry refactor 14 clauses -> 4 policies / 18 rules (backward-compat shim). Disposition accuracy 80% -> 90.9%.

## [0.1.0] - 2026-04-20

- Initial JACI-AML PoC: 6-mode investigation loop, conductor, 8-tool registry, 10 gold cases, EVOLVE layer, MLflow, Streamlit. 80% disposition-accuracy baseline.

[Unreleased]: https://github.com/yourusername/jaci/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/jaci/releases/tag/v0.1.0
