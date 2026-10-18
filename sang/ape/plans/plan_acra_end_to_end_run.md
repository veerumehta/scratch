# Acra end to end: one real packet, five variants (sonnet-runtime, 2026-10-17)

Request: opus-xrepo for the user; the step that sends loan documents to a provider needs the user's own approval in
sonnet-ui's session (or in this one). Until then: no run touches loan documents. Loans are loan-1..loan-5 only; outputs
only under `docs/status/Acra/Acra Lending/e2e/` (gitignored); nothing committed from there; spend ceiling 30 USD
total, 8 per variant.

## Facts found (no loan data read)
- K-Studio JTBDs (`acra_bundle/2_kstudio_jtbds`): per program `values[]` = one job each (123 Standard, 108 Platinum)
  with `skill`, `mnemonic`, `section`, `entity_types[]` (named catalog entities), `loan_metrics[]` (`metric_key`
  `Entity.field`, indicator text), `requirements[]` (prose steps, `investor`), no explicit reads other than metric
  keys and entity types, no code. They run as jobs only (reasoning), and the fields they read are the metric keys.
- Ours (`acra_bundle/3_sdk_jtbds`): 121 Standard / 110 Platinum jobs, code on 43 / 56 (ledger links code to jobs).
- Assessment takes a fact dict (`inputs`) and `engine_mode` (hybrid default, all, code_only, jobs_only, both); a
  `both` run lists code and job side by side. The packet's facts come from the case run's extraction, so the case
  record is built once (sonnet-ui ingests; no second ingestion) and each variant assesses that same record.
- Local Plato runs 0.2.4; the document-reference, engine-mode and guidance routes need the v2.6.4 tip and
  migrations to 0035 (the user runs the pin/migrate script).

## Steps
0. (blocked on approval) the smallest loan's ingestion and classification: sonnet-ui. Nothing here reads it.
1. Scratch packs: `acra-e2e-kstudio` (K-Studio jobs as jobs, through the JTBDSet import) and `acra-e2e-ours`
   (regen 3b jobs and code); neither touches `dscr-core` or `acra-dscr-policy`.
2. Pairing: `acra_compare_sets.py` pairs K-Studio jobs with ours (matched requirements for agreement).
3. Harness `scripts/local/acra_e2e_run.py`: for a case record, runs V1 (kstudio, jobs_only), V2 (ours, jobs_only),
   V3 (ours, code_only), V4 (ours, hybrid), V5 (ours, both) and writes per variant: decided share (pass, fail, not
   applicable) vs indeterminate vs withheld with the reason of each undecided requirement, data readiness (fields
   filled vs read, `missing_reads`), open conditions, cost and latency; across variants: agreement on paired
   requirements, code-vs-job disagreements (V5), open conditions against the packet's own conditions list by counts.
4. Dry run on a synthetic record (no real data) to prove the harness; stub reasoning where a model would be called.
5. Report: xlsx and a short md in the ignored folder; aggregate numbers only in messages.

## Decisions owed to the user
- Approval to send the packet's documents to the providers Plato already uses (typed in a session).
- Upgrade local Plato to the tip (needed for the scratch packs through the routes).
