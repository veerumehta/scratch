# Coverage: a clause decided by partial code is not decided by code (sonnet-runtime, 2026-10-28)

**Finding (sonnet-packs, via opus-xrepo).** A job whose only code link is a ledger alignment of relation `partial` counts as
coded: `ledger.coverage` sets `JobCoverageInput.coded = disposition in CODED`, and `_disposition` answers `code_and_procedure`
as soon as any rule holds for the job (`HOLDS_FOR` = implements, partial, duplicate). `coverage_by_check._decided_by_code`
then answers `code` for every computable check of that job, so each clause such a check names reads "decided by code" when the
rule may implement one part of the job (Platinum condo/two-unit 75% cap aligned `partial` to `property_type_status`).

**Rule.** A clause is decided by `code` only when a computable check naming it belongs to a job some rule implements in full
(written from it, or aligned `implements`). A job whose code is only `partial` (or a `duplicate` of one check) decides its
clauses by `partial_code`: code decides some of the job, which of its checks is not known. `procedure` is unchanged.
Precedence over several jobs: `code`, then `partial_code`, then `procedure`.

**Shape.**
- `JobCoverageInput.code_in_full: bool` beside `coded` (true when the job is in the ledger's `implemented` set).
- `UnitCoverage.decided_by` takes `partial_code`; `coverage_summary` adds `by_partial_code`.
- Workbook: Summary row `units partly coded`; Clauses `decided by` shows `partial_code`; Legend rows for the value and the
  count. No new sheet. The job-level disposition stays (`code_and_procedure` already says part of it is code).
- Not changed: `coded_share` (jobs, not clauses), the release report and the corrections code (they read dispositions).

**Not done here.** The numeric lint (a clause's printed figures absent from its linked jobs, sonnet-packs' script) finds the
gap this note's column only labels; it is the 2.6.7 item that needs the ledger links.
