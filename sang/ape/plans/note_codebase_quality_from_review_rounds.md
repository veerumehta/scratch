# What the review rounds say about the codebase, and what they do not

Status: assessment, 2026-09-11. Decides nothing. Written against the 29 transcripts retained in
`scripts/local/.reviews` (2026-09-10T03:04Z through 2026-09-11T05:07Z). `REVIEW_KEEP` trims older
rounds, so the true count is higher -- at least 35 runs were observed across this session.

Companion to `note_review_loop_prompt_assessment.md`, which covers why the loop is long. This one
covers the separate question that came out of it: what do 35 rounds of findings imply about the
quality of the code they were run against.

## 1. What was actually reviewed

**One branch.** 23 of the retained rounds ran `origin/v2.5.1...HEAD`, which grew from 1,391 to
12,526 lines; the remaining 6 are the incremental rounds that followed the harness fix. Nothing
outside this branch has ever been put through this tool.

**The branch has not been pushed.** Every finding below was raised against code that has not
reached `main`.

That pair of facts governs everything that follows, in both directions.

## 2. The finding corpus

385 findings, of which 125 are `[DEFECT]`.

| severity | count |
|---|---|
| high | 16 |
| medium | 95 |
| low | 13 |
| unknown | 1 |

By area:

| area | findings | defects | highs |
|---|---|---|---|
| shipped python | 205 | 57 | 9 |
| pack data (YAML) | 104 | 50 | 7 |
| tests | 36 | 10 | 0 |
| docs / notes | 24 | 2 | 0 |
| static / html | 16 | 6 | 0 |

Roughly **1.3 highs per 1,000 lines** of branch, or one per 780 lines.

## 3. The highs are not nitpicks

Grouped by what they are, rather than by file:

**Pack corpus, silently permissive or silently dropped (6).** `DSCR-OVER-2M-DSCR` stating the >$2M
floor as a ratio condition only, so a No Ratio file reads INDETERMINATE and the rule is skipped in
the permissive direction -- verified by running the shipped corpus through `check_compliance`.
`DSCR-PPP-IL-2` gating on `interest_rate`, which is `None` on most files. `RB_CI_OVERLAY` shipping
outside the declared dir, so a policy gate is lost with no error. `conventions.yaml`'s header
claiming a load path that warn-and-skips. `checklist_ci.yaml`'s two orphaned PDF line-wrap
fragments. The `ci_lending.yaml` ontology enumerating `Facility.loan_type` short of what the
matchers accept.

**Wiring and deployed-posture seams (3).** `pack_store_for` never wired, so the whole packs feature
was dead outside tests. `tenant_from_request` called unguarded, so every browser request to
`{prefix}/packs` broke on any `deployed_posture()` replica. `missing_config` carrying a
permanently-true entry, so `/health` reported degraded forever on every deployed role.

**The applicability-gate family (2).** A non-SATISFIED gate collapsing to `NOT_APPLICABLE` at
`default.py:418`, then the third site at `check.py:375` after the first two were fixed.

**Threshold provenance (2).** `_looks_authored` requiring `"value" in found`, reachable from the
only shipped authoring path; and the `TODO(threshold-grid-provenance)` deferral understating its own
gap.

**Boot contract drift (2).** `job_exit=SERVES` left in `BOOT_CONTRACT` after `run_role` began
exiting 6, with the docs rendered from the stale row and every test comparing the artifacts to each
other -- then, one round later, a row promising an exit code that never fires, so an ACA job runs to
its platform timeout.

**Shipped hygiene (1).** Consumer repo names in the bundled pack tree, reaching every installer of
the wheel or image. This one sits in `seed_packs/` by path, which is why section 2 counts 7 highs
against pack data while the grouping above names 6 corpus-semantics highs.

**Zero of the sixteen shipped.**

## 4. What this establishes, and what it does not

**Establishes: the gate works.** Sixteen highs found, none on `main`.

**Establishes: the branch's pre-review density was ordinary.** One high per ~780 lines is an
unremarkable rate for code nothing has exercised yet. It reads as alarming because the gate fired
once, at push, against 12,526 accumulated lines. The same work reviewed in 500-line increments is
one finding per round over weeks.

**Does not establish anything about the rest of the repo.** It has never been examined. There is no
evidence it is bad and no evidence it is good. This is the real open question and section 5 is how
to close it.

Three things temper the prior in the meantime, all of them from the transcripts rather than from
optimism:

- **Half the problem is data, not code.** 50 of 125 defects and 7 of 16 highs are in
  `plato/data/seed_packs/**`, which is extracted PDF corpus. That is a bounded problem with a
  mechanical fix (section 6) and it says nothing about the Python.
- **The Python highs cluster in unadopted surface.** "No in-repo callers outside tests", "no
  shipped caller yet", "the first consumer is an external one" recur through the blast-radius
  lines. New code concentrates defects because nothing has run it; code in service has had usage as
  a filter.
- **jaci is editable-installed against this checkout**, so the SDK paths jaci exercises are hit
  daily against the working tree, independent of any review.

## 5. The measurement that would settle it

Never done, costs about an hour, and converts the open question into a number.

The script already supports an arbitrary range. From a detached checkout at a shipped tag:

```
git checkout v2.5.0
REVIEW_UPSTREAM=v2.4.0 REVIEW_FULL=1 ./scripts/local/adversarial_review.sh japes
```

Record: diff size, `[DEFECT]` count, and highs per 1,000 lines. Repeat over two or three shipped
release ranges so the number is not one sample.

Reading the result:

- **near zero highs** -- this branch was unusually dense (new subsystem, new APIs, vendored corpus
  all landing at once) and the rest of the codebase does not warrant an audit.
- **a similar rate** -- the prior holds, you know the scale, and an audit can be planned against a
  number rather than a worry. Prioritise by the groups in section 3, not file by file.

It also yields something never measured: **the reviewer's false-positive floor.** This prompt has
never been run against code believed to be clean, so there is currently no way to tell a real
finding rate from the rate it returns against anything.

## 6. Two bounded sub-problems worth doing regardless of the base rate

**A lint over pack YAML.** Two rules would have caught four of the seven corpus highs: a rule's
`description` must be backed by its encoded `condition`, and a value enumerated anywhere in a pack
must appear in every list that enumerates that field. This is the one class where a deterministic
check retires the class permanently instead of reducing its probability, and it is the class with a
credit verdict behind it.

**One sweep of the wiring / deployed-posture seam.** The three wiring highs are one category, and
the family is small and enumerable: every `create_plato_app` call site, every `deployed_posture()`
and `environment_tier()` reader (13 non-test hits, already enumerated in the 04:20 transcript),
every `missing_config` contributor. A two-hour grep-driven pass over that seam is worth more than
another thirty review rounds.

## 7. The round count is a property of the fix cycle, not of the codebase

Since the harness fix, the rounds are small and the accounting is visible:

| round | lines | defects | FIXED | STILL OPEN |
|---|---|---|---|---|
| 03:40 | 503 | 1 medium | 16 | 10 |
| 04:07 | 160 | 1 medium | 7 | 3 |
| 04:20 | 131 | 1 medium | 2 | 2 |
| 04:37 | 188 | 1 medium | 4 | 2 |
| 04:48 | 120 | 1 **high** | 4 | 2 |
| 05:07 | 157 | 1 high + 1 medium | 3 | 2 |

Thirty-six findings closed in six rounds, zero REGRESSED, open list down from ten to two -- and
exactly one new defect per round, every round. The 05:07 high was created by fixing the 04:48 high,
in the same file. The loop does not terminate because the injection rate is pinned at one and the
gate blocks on any defect, not because the branch is running out of quality. See
`note_review_loop_prompt_assessment.md` and CLAUDE.md §9.

## 8. What I would not conclude from any of this

- Not that the branch is bad. It is the best-reviewed code in the repository by a wide margin, and
  holding it costs more than landing it.
- Not that the loop should stop. It caught sixteen highs that would otherwise have shipped, three
  of which broke a deployed replica outright.
- Not that a full-codebase audit is warranted. That decision needs section 5's number first, and
  running it is cheaper than deciding without it.
