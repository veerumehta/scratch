# DocIntel as an alternate engine and as a fallback (sonnet-runtime, 2026-10-18)

Direction (user, via opus-xrepo): Azure Document Intelligence is an alternate engine and a fallback where that makes
sense. Credentials are in the environment (`AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` / `_KEY`). Nothing here is built, and
no loan file goes to Azure until the user approves that provider send in the builder session.

## What exists
- (a) Engine selection is built: `pages/engine.py` parses `auto | vision | docintel | docintel:<model>`; chosen in the
  document agent's `engine:` (`default`, `by_class`), on a `document_ingest` step (`engine`), and per run
  (`engine=` on the read and case-run routes, over the step's). `auto` is DocIntel OCR where credentials exist, else vision.
  A DocIntel form model reads fields for one class (`by_class` only).
- Per page: `PageReadRecord(page, engine, low_confidence, failed, reason, cached)`; a failed page is tolerated and
  reported, and only "every page failed" raises (`_check_not_all_failed`).
- Cost: document usage rows carry model cost and DocIntel pages by model (`page_models`, priced by `page_price`);
  `vision_budget` summarises vision spend.
- `fallback_sources.py` is a different thing (an online source for the canonical digital copy of a known type, e.g. a
  filing); it is not an OCR fallback.

## What is missing
1. No engine fallback. A page the primary engine fails on (`failed=True`, e.g. a vision page whose output did not
   validate after the retries, or a refusal on budget) stays failed; a page that comes back with no text is not treated
   as a failure. In the loan-2 read a few vision pages failed this way.
2. Fallback is not recorded as such: nothing says "page N was read by B because A failed".
3. Cost is not split by engine in one place: vision tokens sit in the model row, DocIntel in `page_models`, with no
   per-engine total on the run.
4. Whole-document failures (a provider outage, a conversion error) have no second engine either.

## Design
- `EngineConfig.fallback: str | None` (an engine name as above; default none, so nothing changes unless declared) and
  the same on a step and per run (`fallback_engine=`). Validation: the fallback differs from the primary; a DocIntel
  fallback without credentials is refused at publish check, not at read time.
- Page level, in `_read_scanned`: pages the primary reader returns `failed` or empty text for are read again by the
  fallback reader (same `PageReader` interface: `VisionReader`, `DocIntelReader`). A page read this way records
  `PageReadRecord(engine=<fallback>, fallback_from=<primary>, reason=<primary's reason>)`.
- Document level: when the primary raises for the whole document (`_check_not_all_failed` or a provider error that
  `is_transient_error` retries have not cleared), the fallback reads every page that needed reading, once.
- Tolerant first: a fallback that also fails leaves the page failed, as today; nothing refuses.
- Cost by engine: `DocumentResult.engine_usage: {engine: {pages, calls, cost_usd}}`, summed into the document step's
  usage as `by_engine`, so a run shows vision and DocIntel side by side and the fallback share is a number.
- Run record (case run, document read, extraction): `fallbacks: n pages, from -> to` in the step's settings.
## Tests
Primary fails one page: fallback reads it, record names both engines; primary returns empty text: same; both fail:
page stays failed, no raise; no `fallback` declared: unchanged records and calls; per-engine usage sums to the step total;
a DocIntel fallback without credentials fails the publish check.
## Consent
The DocIntel path sends page images to Azure. Declaring it as a fallback in a pack is configuration; using it on loan files
needs the user's approval in the session that runs them, each time that provider is first used for them.
