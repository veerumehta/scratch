# Base mode prompts: assumptions a pack's data can contradict

Audit of `jazzx_sdk/modes/prompts/*.md` (investigator, verifier, reasoner, governor, narrator,
sentinel, evaluator). Audit only; nothing rewritten. Pack tuning is appended after the base
(`base + "## Domain Configuration" + tuning`), so a pack can add to a base prompt but cannot take a
sentence out of it, and a contradicting sentence stays in force.

Severity: **H** = a pack in a non-AML domain (DSCR lending today) hits it now; **M** = hit by a
different data shape or workflow; **L** = wording only.

## Verifier (3.1.0, already reworked)

| # | Assumption | Sev | Contradicted by |
|---|---|---|---|
| V1 | "`source` ... as the platform recorded it: `input`, `fixture:<file>`, a connector or tool name, `document:<id>`, `unavailable`" is the complete source vocabulary | M | a pack with its own source names (a `lease_ledger` connector reads as a tool; fine) or an object with no `source` |
| V2 | `params_applied` is present on every evidence object | M | evidence from a path that does not set it: the verifier must treat absence as "not applied" or "applied"; the prompt is silent |
| V3 | "Transaction records" with amounts that "reconcile (totals match sums)" | M | evidence that carries no totals (appraisal, rent roll): the flag reasons are transaction-shaped |
| V4 | "Customer ID does not match case subject" as a flag reason | H | a case whose subject is a loan, property or borrower id: the prompt names one identity kind |
| V5 | "Dates ... not in future, proper sequence" | M | forward-looking evidence (effective dates, lease end dates, expiry) is legitimately in the future |
| V6 | Contradiction with "previously attested evidence" flags the later object | M | two sources that legitimately disagree (appraisal rent vs lease rent): the prompt flags rather than recording the conflict |

## Investigator

| # | Assumption | Sev | Contradicted by |
|---|---|---|---|
| I1 | The task is "typology candidates" from "the alert trigger"; hypotheses have a `typology_name_from_pack` | H | an assessment workflow (is this loan eligible?) has no alert and no typology |
| I2 | Start confidence 0.50-0.65; converge at >=0.85 or all <0.15; status bands 0.15/0.85 | H | a pack whose hypotheses are deterministic or whose conductor sets other thresholds; these numbers are also hard-coded in the status definitions |
| I3 | "At least 2 evidence types, at least 2 iterations (enforced by guardrails)" | M | pack config that sets other minimums (`min_evidence`, `min_iterations`) makes the prompt wrong; it states the default as fact |
| I4 | Evidence categories "Core: customer/entity profiles, transaction patterns, watchlist/screening; Corroborating: relationship mapping; Policy: historical cases, regulatory clauses" | H | lending evidence types (appraisal, rent roll, credit, title); the categories steer which tools get called first |
| I5 | Initial turn requests "2-4 pieces of core evidence", later "1-2" | M | a pack where the first pass needs all eight documents |
| I6 | "Duplicate evidence requests waste API calls" and "same tool with same params" | L | tools that are legitimately re-read after a correction; the loop already refuses re-requests of flagged evidence |
| I7 | Output ids are `uuid` | L | packs with their own ids |

## Reasoner

| # | Assumption | Sev | Contradicted by |
|---|---|---|---|
| R1 | Recommendation vocabulary is `close\|escalate` | H | a pack whose decision is `eligible\|eligible_with_conditions\|ineligible` (DSCR): the output format section contradicts the pack's schema |
| R2 | "**Most alerts are false positives. Default to close. When in doubt, close**" | H | a lending decision has no default; the bias pushes toward one outcome |
| R3 | "Never recommend escalate without citing at least one policy clause" | M | escalation that rests on evidence only; also the word "escalate" |
| R4 | "False positive indicators" and "immediate dismissal" step | H | no false-positive concept in lending |
| R5 | Confidence bands (0.85/0.65/0.40) and "if the investigator's highest is 0.84 ... you may still escalate at 0.90+" | M | packs where confidence is not the investigator's hypothesis confidence |
| R6 | Evidence quality tiers (identity verification, transaction records, pattern library, prior cases are "medium", "closed cases may indicate false alarm") | H | AML-specific ranking; a lending pack's strongest evidence (a signed lease, an appraisal) is not in the list |
| R7 | "Only attested evidence: do not reference flagged or unavailable evidence" | M | the verifier flags on data problems that a pack may want cited as such |
| R8 | Output keys `recommendation`, `confirmed_typology`, `supporting_evidence_ids`, `policy_clauses_cited` | H | the pack's decision schema (see R1); the prompt's JSON example competes with the schema the model is given |

## Governor

| # | Assumption | Sev | Contradicted by |
|---|---|---|---|
| G1 | Input is "a Disposition Recommendation"; output is `decision: approve\|conditional_approve\|block` | H | the schema is `approved: bool` (`GovernorDecision`); the prompt's output example names a different shape |
| G2 | "Autonomy ceiling" and "risk tier" checks | M | packs with no autonomy or risk-tier data; the model invents a verdict on absent data |
| G3 | "Required policy citations present" is an approval condition | M | the case runner now cites rules deterministically; a missing citation by the model is not a policy gap |
| G4 | "Insufficient evidence for escalation claim" | H | escalation vocabulary again |
| G5 | The model's rationale is the final rationale | M | deterministic overrides now record beside it (`overrides`); the prompt does not tell the model its verdict may be overridden, which is correct, but the conflict text it sees later is not shown to it |

## Narrator

| # | Assumption | Sev | Contradicted by |
|---|---|---|---|
| N1 | "A narrative generator for escalated cases" and "approved disposition" | H | a lending case narrates a denial or a condition set; adverse decisions are now narrated (VerdictRule), the prompt still says escalated |
| N2 | Fixed sections: executive summary, subject information, activity summary, evidence summary, conclusion | H | "activity summary: suspicious patterns" is AML; a lending narrative has terms, collateral, conditions |
| N3 | "Every claim must cite evidence ID" with `EV-001` ids | M | claims that rest on the case input, not on an evidence object |
| N4 | Output has `evidence_citations`, `policy_citations` lists | L | a narrative schema without them |

## Sentinel

| # | Assumption | Sev | Contradicted by |
|---|---|---|---|
| S1 | Signal decay = "last 2 iterations with no hypothesis confidence change > 0.05" | H | a loop whose progress is evidence arriving, not confidence moving: the metric fires on healthy loops (the conductor now computes sentinel metrics; the prompt still describes the model doing it) |
| S2 | `max_iterations` default 10; `signal_decay_threshold` default 2 | M | pack config overrides |
| S3 | Error accumulation: "any single tool failed 3+ times" | L | retry config differs per pack |
| S4 | The model computes the metrics from "CaseContext" | M | metrics are computed in code; the model only sees them |

## Evaluator

| # | Assumption | Sev | Contradicted by |
|---|---|---|---|
| E1 | Escalated cases have a report draft; "close cases" have none | H | adverse lending decisions have a narrative too |
| E2 | The four pre-computed scores (decision_accuracy, evidence_efficiency, policy_compliance, loop_efficiency) | M | a pack with its own scorers (DSCR's eval has others) |
| E3 | Report-quality criteria: subject identification, activity description, supporting transaction detail | H | AML report criteria |
| E4 | Closed set of six improvement tags | L | intentional |

## Patterns

1. **Vocabulary baked into output examples** (R1, R8, G1, N1, E1): the prompt's JSON example names
   keys and values that the pack's schema (given to the model separately) replaces. Two conflicting
   instructions; the model resolves it unpredictably. Highest value to fix.
2. **Domain voice in the "how to think" sections** (R2, R4, R6, I1, I4, N2, E3): AML priors that
   are correct for AML and wrong elsewhere. Tuning appends but cannot negate them.
3. **Numbers stated as fact that config owns** (I2, I3, S2, R5): thresholds repeated in prose.
   They drift from the pack's config and from the conductor's enforcement.
4. **Things done in code now** (S1, S4, G3, G5, V1): the conductor computes sentinel metrics and
   cites rules; the prompt describes the model doing it.

## Proposal: named base sections a pack may replace

Today: `final = base + tuning`. Proposed: base prompts are split into **named sections**, each
delimited by a marker comment the loader reads and the model never sees:

```
<!-- section: decision_vocabulary -->
...
<!-- /section -->
```

Sections per mode (initial set, from the table above): `role`, `decision_vocabulary` (reasoner,
governor), `defaults_and_priors` (reasoner), `evidence_quality` (reasoner), `evidence_categories`
(investigator), `hypothesis_thresholds` (investigator), `report_structure` (narrator),
`report_criteria` (evaluator), `loop_signals` (sentinel), `output_format` (all).

A pack declares in its mode tuning file front matter:

```yaml
---
replaces:
  reasoner: [decision_vocabulary, defaults_and_priors, evidence_quality, output_format]
---
```

and supplies each replacement as a `## replaces: <section>` block in the same file. Rules:

- A section a pack does not replace stays as the base wrote it; one it does is swapped whole
  (no partial edits, so a reviewer can read the base text and the replacement side by side).
- An unknown section name is a pack-check error (`unknown_prompt_section`), and a replaced section
  with no replacement text is too. Names are the SDK's contract, versioned with the prompt.
- Prompt provenance (the `PromptRef` the run records) lists `replaces: [mode.section, ...]` and
  the base version, so a run says exactly which base text was in force.
- `output_format` replacement is how a pack ends the competing-JSON problem; better still, the
  loader could drop the base `output_format` automatically when the pack supplies a typed output
  schema (pattern 1), leaving the schema the only statement of shape. Suggest doing both: replace
  is explicit, auto-drop is the default for modes with a schema.
- `requires: {japes: ...}` (done) gates a pack that uses `replaces` on an SDK that has it.

Alternatives considered: (a) rewrite every base prompt domain-neutral: cheapest, but loses AML
quality for packs that need it and needs a decision per sentence; (b) a free-text `replaces` of
arbitrary spans: fragile, breaks on any base wording change. Named sections are the middle path.

Decision for the user: the sectioned replace, and whether the base prompts should also be made
neutral where the audit says H and the vocabulary is plainly AML (reasoner `close|escalate`,
governor `approve|block`, narrator sections), since a neutral base plus sections avoids shipping
AML defaults to every pack.
