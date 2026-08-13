# Done: Document Upload → Knowledge-Hub-Backed "Document Packet" System

Author: Virendra Mehta · Completed 2026-08-11
Repo: jaci only (japes papercuts found, not fixed — see below) · Landed: jaci dev `a6b068b`
carries the YETI/MAA doc-stub commits only; everything else below is uncommitted in the working
tree (commit pending explicit go-ahead), no version bump on either repo
Plan: no pre-existing `docs/plans/plan_*.md` — planned incrementally across the session via
Claude Code's own plan-mode checkpoints, not this repo's plan-file convention. This file is the
first artifact of the work in `docs/plans`/`docs/status` terms.

Built up in stages, each verified before the next: a document upload widget, generalizing the
`.japes` local-markdown-cache convention beyond `ci_spread`, shrinking and committing the real
YETI/MAA 10-K samples, a Knowledge-Hub push/pull tier in `docintel.py`, and a named "document
packet" registry + picker UI on top of all of it. Two real bugs found and fixed along the way
(`ci_spread`'s `_run_fabric` missing `local_cache_dir`; `MockKnowledgeHubClient`'s Streamlit-rerun
persistence gap). Two japes-side papercuts found, worked around in jaci, filed upstream rather
than silently routed around.

## What shipped

- `scenarios/shared/document_upload.py` (new `shared/` package): `render_document_upload()` — a
  zip stands in for a folder upload (browsers can't upload directories), unpacked via
  `jazzx_sdk`'s own `unpack_zip`. Wired into `ci_spread` (new `_seed_uploaded_financials` feeds
  uploads into `CIToolRegistry`'s evidence pipeline), `cre_underwriting`, `portfolio_monitoring`,
  `insurance_diligence`.
- `commercial_lending/docintel.py`'s `.japes/`-or-co-located-`.md` local-cache fallback (only
  `ci_spread` used it before) generalized into `cre_underwriting`, `portfolio_monitoring`,
  `insurance_diligence` — swapped their raw `jazzx_sdk.convert_document` import for the
  `.japes`-aware wrapper. Behavior-preserving today (their sample docs are tiny); means a real
  large doc there gets the same truncate-and-cache treatment as YETI/MAA.
- `docintel.ensure_local_cache`/`ensure_local_caches` (async): a Knowledge-Hub pull tier ahead of
  live conversion. Tries a pushed **derived** doc first (cheap); falls back to pulling the
  **original** and converting it locally if that's all that was ever pushed (the one place real
  conversion cost can land on a pull — documented explicitly since it's a real behavioral
  difference from the cheap-hit path). Deliberately a separate async function, not a `fabric=`
  param on the sync `convert_document` — bridging an async fetch inside an already-sync function
  risks "asyncio.run() cannot be called from a running event loop" for callers that are
  themselves async (e.g. `ci_spread/spreader.py`'s `spread_filings`, which now takes an optional
  `fabric=` and calls `ensure_local_cache` before conversion).
- `docintel.check_staleness`: cheap metadata-only hash comparison (no content download) — flags
  when a doc's fabric copy changed remotely since this was last pulled. Never auto-resolves; the
  caller decides.
- `scenarios/shared/fabric.py`: `build_fabric()` (connected-KH-vs-local-Mock dev/prod switch,
  factored out of three separate copies that had accumulated across `ci_spread`'s `_run_fabric`
  and the push script's own `_build_fabric`) and `cached_build_fabric()` (session-state-cached —
  see the bug below).
- `capabilities/commercial_lending/document_packet.py` + `scenarios/shared/packet_picker.py`: a
  named "document packet" system. `push_folder_as_packet()` pushes *both* tiers (original bytes
  and derived `.japes` markdown) per file, deduping via `fabric.docs.ensure()`'s content-hash
  idempotency (not reimplemented — `force_reconvert`/`skip_originals` flags support a
  refresh-derived-only flow). `local_path` is auto-set when the source folder is already inside
  the repo (vendored, zero-fabric-dependency pick — same story as the YETI/MAA stubs).
  `config/demo_document_packets.json` (repo root, deliberately **not** under `config/packs/`,
  which already means governed domain packs here) is the committed offline registry
  `list_all_packets()` always reads first, merged with live Knowledge Hub results on top.
  `packet_picker` wired into `ci_spread`'s upload flow (tries the picker first, falls through to
  direct upload).
- Four new scripts: `scripts/shrink_source_pdfs.py` (truncate a large source PDF to a labeled
  stub + its real `.japes/<stem>.md` — existence-only resolution, stub bytes never matter),
  `scripts/push_source_docs_to_fabric.py`, `scripts/refresh_and_push_japes.py`,
  `scripts/export_document_packet_manifest.py` (the cloud-run-then-commit-back workflow).
- YETI/MAA 10-K PDFs shrunk (50-70MB → <1MB each) and committed via `git add -f` (`docs/
  LoanSamples` is fully gitignored; explicit force-adds still work) — originals preserved under a
  gitignored sibling `_originals/`. MAA's staging was co-located `.md` (no `.japes/` subfolder);
  migrated to the `.japes/` convention as part of the shrink.

## Two real bugs found and fixed

- `ci_spread`'s `_run_fabric` never set `FabricConfig.local_cache_dir` — LOCAL-mode `fabric.docs`
  silently missed the per-loan `artifact_dir` entirely, so anything written there was unreadable
  on the next call. One-line fix once found; found by tracing the actual resolution path rather
  than assuming the existing wiring worked.
- `MockKnowledgeHubClient` doesn't persist across process/script-rerun boundaries (confirmed by
  reading the source: `_load_from_data_dir` exists, no corresponding `_save_to_data_dir` anywhere)
  — since Streamlit reruns the whole script on every interaction, an uncached `build_fabric()`
  would forget a just-pushed packet before a user could ever see it in the picker dropdown. Fixed
  with `cached_build_fabric()` (`st.session_state`), verified against `AppTest`'s real session
  machinery (`at.session_state.filtered_state`), not a hand-rolled substitute for it.

## Two japes papercuts found, not fixed here

Can't be fixed from this repo — japes is a pinned git dependency
(`japes[litellm] @ git+https://github.com/JazzX-LLC/japes.git@dev`), not an editable sibling,
though a local checkout exists at `../japes` (used to verify both findings against source before
filing, same `dev` branch, version-matched at 2.3.6). Filed as
[japes#57](https://github.com/JazzX-LLC/japes/issues/57):

1. `MockKnowledgeHubClient`'s `data_dir` is load-only (see above) — its own docstring implies
   real persistence ("entities are saved to / loaded from `data_dir/entities.json`") that doesn't
   exist.
2. `FabricConfig.validate_for_mode()` requires `knowledge_hub_url` for STRICT/CACHED mode even
   when `kh_client` is the Mock (which already carries `is_mock=True` specifically as a marker
   for this kind of check) — worked around with a placeholder `"mock://local-kh"` string.

## Deliberately not done

- `cre_underwriting`/`portfolio_monitoring`/`insurance_diligence`'s core intake call chains are
  synchronous; fabric pre-hydration (`_hydrate_from_fabric`) is only wired at the
  Streamlit-boundary (`asyncio.run()`) ahead of the upload path, not deep inside the sync parsing
  pipeline. Making the whole chain async is a bigger, more invasive change than this round
  attempted.
- `portfolio_monitoring`/`insurance_diligence`'s *default* (non-uploaded) review cases are built
  eagerly at Python import time (`cases.py` module load) — fabric pre-hydration only covers the
  upload/packet-pick path, not that eager-import path.
- No direct Azure Blob backend (bypassing Knowledge Hub) — confirmed
  `jazzx_sdk.clients.knowledge_hub_client.KnowledgeHubClient` (the real, non-Mock client) is
  HTTP-only, no Blob SDK usage anywhere in japes; a real KH deployment is already Blob-backed
  server-side, so `build_fabric()`'s existing connected-KH branch already covers it. Revisit only
  if a concrete "KH unreachable but Blob is" deployment gap shows up.

## Acceptance criteria — verified

- Full push→pull round trip (local Mock fabric): both original and derived entries land in
  `.kh_manifest.json`; both dedup correctly (`created=False`) on a second push of identical
  content.
- Originals-fallback pull tier: seeded a manifest with only `original_doc_id` set, deleted local
  `.japes`, confirmed it pulls the original and produces correct `.japes/<stem>.md` via
  conversion — both the success path (digitally-readable synthetic PDF) and the graceful-failure
  path (a too-sparse PDF correctly reads as "scanned," `ensure_local_cache` returns `False`
  rather than raising).
- `check_staleness`: push, then mutate the fabric-side doc's content — flagged; unchanged content
  — not flagged. (Caught and fixed a real bug in this check itself: the hash lives nested under
  `meta_data`/`metadata`, not top-level, matching `DocStore._find_by_hash`'s own convention —
  wrong on the first pass, fixed once the test actually exercised the mutated-content branch.)
- `local_path` auto-detection: pushed the real YETI folder (inside the repo), confirmed
  `local_path` was set to the correct relative path; reloaded from a written manifest file and
  confirmed it round-trips.
- Session-cached fabric: pushed a packet into the *same* fabric object an `AppTest` session's
  `cached_build_fabric()` had already constructed, reran the page, confirmed the packet appeared
  in the picker dropdown — proves the fix against the real Streamlit session-state machinery, not
  a simulated stand-in.
- `docintel.convert_document` still resolves both YETI and MAA correctly post-shrink and
  post-commit (real markdown content returned, not the stub's literal bytes).
- All four scenario pages (`ci_spread`, `cre_underwriting`, `portfolio_monitoring`,
  `insurance_diligence`) render without exceptions under `streamlit.testing.v1.AppTest`,
  re-checked after every round of changes this session.
- Zero new `ruff check` violations across every touched/new file, verified by diffing against
  each file's pre-existing baseline (not just running ruff cold — several touched files carry
  large pre-existing violation counts unrelated to this work).
- Full jaci test suite: 809 passed, 8 skipped, 4 xfailed, 1 xpassed, 1 known pre-existing failure
  (`test_decision_canonical.py::TestDecisionType::test_decision_type_all_values` — last touched
  June 6, untouched this session, unrelated).
