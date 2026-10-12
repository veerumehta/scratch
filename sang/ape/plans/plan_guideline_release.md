# Guideline release: date-selected pack versions and a release report

Plan, opus-xrepo, 2026-10-12. Status: written, not started. Owner: sonnet-runtime. Decisions owed are in
section 6. Companion plans: `plan_document_registry_and_job_shape.md` (stable ids),
`plan_decision_corrections.md` (versioned expected answers).

## 1. Why

When Acra issues a new guideline (say 4.9 after 4.8), two things must hold:

- **Each loan is judged by the guideline in force on its date.** Today assessment picks a program
  from the case's inputs (`pack/assessment.py::policies_in_force`, `_program_policy_ids`) and never
  a date. A pack has one active version (`pack/activation.py` references), so a loan locked under 4.8
  is judged by whatever is active now. `Policy.effective_date` / `expiry_date` and
  `Policy.not_in_force(as_of)` exist (`fabric/canonical/policy.py`), but assessment does not select
  by them. Not verified end to end: whether any caller passes an `as_of`.
- **A person sees what the new guideline changes before it goes live.** We can diff guideline text
  (`pack/guidelines_db.py::diff`) and pack files, but not the jobs, rules, coverage and gold cases
  that a change touches.

## 2. What exists

| Piece | Where |
|---|---|
| Guideline versions: content digests, diff, certification, rollback refused while a live pack is certified against a version | `pack/guidelines_db.py`, migration 0027 |
| Diff-scoped re-extraction (changed sections only) | the guideline versioning work plus `DocumentFocus` |
| Policy effective and expiry windows, `not_in_force` | `fabric/canonical/policy.py` |
| Pack versions, publish, activation by reference | pack store, `pack/activation.py` |
| Job ledger, coverage, aligned comparison | `pack/ledger.py`, `pack/jtbd_align.py` |
| Rule trials, pass bars | `pack/rule_trial.py`, `evaluation/pass_bars.py` |

## 2a. Posture: tolerant first (the user, 2026-10-12)

The user wants quick uptake over restriction. Every check below proceeds and records rather than
refuses: the run carries a `selection_notes` list saying what was assumed, the runs page shows it, and
the coverage page counts it. A pack can later tighten any of them to a refusal with a per-pack
`strict:` switch. The only refusals are ones where proceeding would write something wrong.

## 3. R1. Date-selected versions

- **The case date.** A pack declares a `case_date_field` in its assessment spec (for Acra, the lock
  date or the application date; see decision 1). This is optional. A case that lacks the date, or
  has one that cannot be parsed, is judged by today's version with a selection note.
- **Several live versions.** Activation holds a list per pack rather than one version. Each entry is
  a pack version with an `effective_from`, by default the effective date of the guideline it is
  certified against, and optionally an `effective_to`. A version with neither date is in force from
  its activation.
  - Overlapping windows are allowed with a warning at activation. Inside an overlap, the most
    recently published version wins, with a note.
  - A case dated in a gap or before the first window takes the nearest earlier version (else the
    earliest), with a note.
- **Selection.**
  - A case run or assess call resolves the version in force on the case date, then the program as
    today.
  - The run records the pinned version, the case date and the reason the version was chosen.
  - An explicit version on the request still wins: replays, trials and evals.
- **Inside a version.** `Policy.not_in_force(case_date)` drops policies outside their own window,
  using the same date.
- **Compatibility.** A pack that declares no case date behaves as today: one active version, no date
  selection.
- **Multi-replica activation** keeps its If-Match on `stored_version`. The list is one stored value.
- **Verify:**
  - two versions with adjacent windows: a case dated in each is judged by its own;
  - a case in a gap, an undated case and a case in an overlap each run, with the expected
    selection note;
  - `strict: true` turns each of those into a refusal;
  - an explicit version overrides the date;
  - a pack with no case date is unchanged (the existing tests are the check).

## 4. R2. Release report

`GET /packs/{id}/release-report?from=<version>&to=<version>`, and in the client, the CLI and the
coverage page. Built from things that exist:

- **Guideline:** the changed sections between the two certified guideline versions.
- **Jobs:** added, removed, and changed (requirement text, kind, documents, reads). The match uses
  stable ids and their aliases.
- **Rules:** added, removed, and changed (code digest, thresholds, tables), each with the job it
  implements.
- **Documents and catalog:** registry and catalog entries added, renamed (by alias) and retired.
  Retirements without a successor come from the cross-version lint.
- **Coverage:** before and after by disposition, plus the change in the schema backlog.
- **Gold cases:**
  - each case run against both versions, as a rule trial over the pack's datasets;
  - listed as unchanged, newly passing, newly failing, or answer changed with the rule changed;
  - the last group is the candidate set for marking `superseded` (corrections plan C2).
- **Output:** JSON, plus an xlsx for the reviewer, through `util.xlsx_safe`.
- **Cost:** only the gold case runs spend model time. Everything else is deterministic, and the
  report states its cost.
- **Verify:** a scripted pair of versions with one changed threshold, one renamed document and one
  added job. The report lists each change, and the one gold case on the changed rule shows as
  "answer changed with the rule changed".

## 5. Order

- R1 first, because it is what makes a new guideline safe to activate.
- R2 needs stable ids from the registry plan's D1 for documents. For jobs and rules it can start on
  mnemonics and rule ids.
- Both are independent of the corrections plan except for the `superseded` hand-off.

## 6. Decisions

Settled by the posture (the user, 2026-10-12):

- Windows default to the certified guideline's effective date.
- An undated case is judged by today's version, with a note.
- A retroactive version (`effective_from` in the past) is allowed, with a warning; open runs it
  would have judged differently are listed for rerun, never rerun automatically.

Still open:

1. **Acra's case date.** Lock date, application date, or note date? This is a question for Acra.
   Until it is answered, the pack declares none and behaves as today.
