# Acra: the whole conditioned pipeline on loan-2 (sonnet-runtime, 2026-10-25)

Plan only; nothing built, nothing sent to a provider. Request: opus-xrepo for the user (20 USD ceiling). Masking, no PDF reads,
outputs under `docs/status/Acra/Acra Lending/e2e/loan-2/pipeline/`, aggregate numbers only in messages, never push.

## What runs
A scratch pack `acra-e2e-pipeline` (seed skeleton + our regen jobs and code; no published pack touched) whose conductor is the whole
pipeline: `document_ingest` (split, classify) -> `policy_assessment` (engine mode per variant) -> `adjudication` (the jobs against
the packet's evidence) -> `investigation` (loop, sentinel, convergence, max 5 iterations) -> `policy_check` -> `narrate` (ungated, so
it is measured). No human checkpoint. Run through local Plato (`POST /packs/acra-e2e-pipeline/runs`), tolerant mode.

- **Ingest reuse**: the loan-2 documents and record exist (`upload.json`, `case.json`, the fallback read). The documents step reads
  through the page cache (`JAPES_PAGE_CACHE_DIR`), so a rerun costs no model calls if the engine settings match the fallback run;
  the harness checks the cache hit count first and says what it cost (0.55 USD if the cache misses).
- **Variants**: V-hybrid (`engine_mode=hybrid`), then V-both (`both`, `verify_disagreements` off) if the budget holds.
- **Case date**: the assumed lock date, unconfirmed with Acra; every report line that depends on it says so.
- **Tolerant**: proceed, record, surface. `RatioSet.reserves_months` is stated 0 and recorded as a data-quality note (as in the
  earlier report); the owed `missing_inputs: default` decision is not taken here.

## What is measured (counts only)
Decided share per requirement (pass, fail, not applicable) against indeterminate and evidence-missing, with the reason of each
undecided one; open conditions against the packet's own conditions list; per stage cost, calls and latency; the investigation
loop's status, iterations, guard and convergence reasons (where it does not converge); adjudication segments failed or partial;
document read quality as before.

## Cost estimate (per variant; the adjudication figure is the uncertain one, no loan-2 measurement exists)
Measured anchors: loan-2 ingest 0.56 USD; a whole V5 assess with jobs 0.022 USD (253 calls, 123k tokens in: about 0.15 USD per
million tokens blended on the default model).

| Stage | Expected | Upper bound |
|---|---|---|
| ingest (cache) | 0 | 0.55 |
| assessment | 0.02 | 0.05 |
| adjudication | 1.5 | 5 |
| investigation loop | 0.3 | 1 |
| policy_check, narrate | 0.05 | 0.2 |
| **hybrid** | **about 2** | **about 7** |
| **both** (adds the jobs side by side) | **about 2** | **about 7** (cumulative with hybrid 14) |

Expected total about 4 to 5 USD; upper bound about 15 USD, inside the 20 USD ceiling.

## Gates
Hard stop per variant at 7 USD and in total at 15 USD (5 held back), checked after each stage from the run's meter; the run stops and
reports, it does not continue. A first dry run on a synthetic record with scripted agents proves the harness and the pack
(no provider call). Nothing touches a provider until the user types their own approval in the builder session.

## Steps
1. `acra_e2e_packs.py`: add `acra-e2e-pipeline` (conductor above). 2. Harness `acra_e2e_pipeline.py` (submit, poll, collect from
the `CaseResult`: steps, `usage.modes`, adjudication, investigation, checks). 3. Dry run, synthetic. 4. Cache-hit check on loan-2
(no model call). 5. Hybrid, report; 6. both if the total so far is under 7 USD.

## Next loan
Sizes only (masked order): dir 1: 2 files, 1.0 MB; dir 2 (loan-2): 169 files, 159 MB; dir 3: 3 files, under 0.1 MB; dir 4: 5 files,
474 MB. Proposed next: **loan-1**, the smallest real packet (1 MB), to see a minimal packet through tolerant mode (required classes
missing is exactly what tolerant mode must surface); it needs ingest (about 0.05 USD at loan-2's per-page rate) and the same
approval. loan-4 (about 3x loan-2's bytes, ingest about 1.5 to 2 USD, one 474 MB file that needs splitting) after that. loan-3
looks like placeholders (no size): I would ask what it holds before spending.
