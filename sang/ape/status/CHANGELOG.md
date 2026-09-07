# Changelog

All notable changes to JAPES (JazzX SDK) will be documented in this file.

## [2.5.0] - 2026-09-07

*Post-push round: the sliced adversarial review (see below) and PR #67's bot both ran against the
pushed commit, which the size-capped review had skipped.*

- **Review round 9.** One defect, and it undid the safety of round 6's own fix: a header that is
  present but blank produced an identity. `email or name` yields `""`, and the context builder
  tested `is None`, so `x-user-name:` gave a context whose principal is the empty string -- an
  anonymous request the middleware admitted, and the `identity_required` gate then opened for.
  On a strict deployment `GET /api/v1/logs` returned the buffered records and `/api/v1/metrics`
  the full per-route inventory, both of which were withheld before that gate existed. It is the
  same empty-identity hole closed on the token path earlier in this section, left open on the
  header path the gate actually rests on. An empty identity is not an identity, in
  `build_invocation_context_from_headers` as in `verify`.

  Three notes: the refresh floor used `fetched_at > 0` as its "has fetched" sentinel, so an
  injected clock with a zero origin made a successful fetch indistinguishable from never having
  fetched and the floor failed open again -- a separate flag now; the security-header test
  asserted only that *a* policy was present, which would have passed with the dashboard silently
  getting the API's `default-src 'none'` and rendering as unstyled text; and a docstring still
  described the Swagger route that round 8 deleted.

- **Review round 8: no defects.** Five non-blocking findings, fixed anyway, one of which was
  substantive: the degraded app is built by hand rather than by `create_app`, so it attached none
  of the response security headers -- every degraded response went out with no CSP, no
  frame-ancestors and no nosniff, on the replica an operator is most likely to open in a browser.
  The `/` page had one only because it sets its own. FastAPI's CDN-loaded `/docs` is dropped there
  too, as the working app already does: it was mounted and reachable, so the nav omission had been
  hiding a page that worked, for a reason (the CSP blanking it) that no header was being set to
  make true.

  The rest: `sync_collection` passed `manifest_scope or collection_id`, which is `materialize`'s
  own default now -- and passing it made `manifest_scope is None` false in there, silently
  disabling the adoption of a manifest recorded under the previous path-based scope. A comment
  claimed `_dsn_summary` resolved the engine accessor when both callers still did it themselves,
  so it now does. `fetch_validated` accepted `validate` and `allow_hosts` together and quietly
  honoured only the first. `_safe_fetch` still had its own `max_redirects=10` beside the constant
  extracted for it. And the new `env_*` test file promised coverage of the numeric readers and
  contained one test for the text one.

- **Review round 7.** The SSRF guard added earlier in this section broke an ordinary
  deployment: `validate_url_safe` refuses any host resolving private *and* fails closed on one
  that does not resolve, so a Knowledge Hub whose blob URLs point in-cluster
  (`http://minio:9000`, a compose stack, or a hub serving blobs from its own address) had every
  `download_document_v2` raise. It now accepts hosts the deployment has declared: the hub's own,
  automatically, plus `JAPES_KH_BLOB_HOSTS`. The scheme rule and the private-IP rule still apply
  to everything else, so this admits a named host rather than disabling the guard.

  `_probe_failed` was added to and never discarded, so a document whose first metadata call
  failed had its *successful* retry thrown away for the listing's weaker digest -- and
  re-downloaded on the run after the retry worked. The test passed because it asserted only the
  call count; it asserts the recorded digest now.

  `create_config_router` was the third member of the withholding family without the new
  `identity_required` kwarg, so one predicate meant two things. That asymmetry is real and is now
  stated rather than implied by an omission: a gateway-injected header identifies who is asking
  without being an authorization decision, which is enough to *read* diagnostics and not enough
  to *write* configuration. The guide and the logs docstring said these routes need an `auth`
  dependency, which stopped being true when `require_identity` began unlocking them.

- **Review round 6.** The consequential defect: the withholding gate keyed on `auth is None`,
  and *no shipped wiring sets `PlatoWiring.auth`* -- so on every strict deployment there is, an
  authenticated operator saw a permanently empty metrics table and no log records, while
  `require_identity` was already authenticating each request and the guide described an `auth`
  path no wiring takes. Identity middleware is now the other way a caller can be known, so a
  working replica serves both and the degraded app -- which has no middleware and cannot be given
  any -- still withholds.

  The digest preservation added in round 5 covered the probed document and not the batch behind
  it: a failed metadata call reports `None` for any document, and letting that overwrite a listing
  digest costs a re-download on every run. It applies to all of them now.

  `create_config_router` -- which `logs_api` cites as the shape it copied -- was the one member of
  that family still spelling the predicate out after it was extracted for the other two.

  Three notes: a docstring reflow had lost its indentation and read as a fragment; two
  `fetch_validated` tests and the `env_text` test had landed in the materialize file rather than
  beside what they test; and the `data:` branch matched `;base64` case-sensitively where the
  grammar is case-insensitive, and returned a zero-byte document for a URL with no comma at all
  instead of refusing it.

- **Review round 5.** Three defects, all in rounds 3 and 4's own changes.

  The sharpest was a branch that could not fire: `get_document_metadata` swallows every error and
  returns `None`, so `_current_hash` stored `{}` and the "the probe call failed" test was
  indistinguishable from "the record was empty". The test pinning it passed only because its stub
  *raised*, which the production client never does -- so against a real hub a timeout on the
  probed document still concluded "this hub does not hash" and denied every other document its
  backfill, while overwriting the probed document's listing digest with `None` so it re-downloaded
  on every run. Failures are recorded explicitly now, and the listing's digest is kept when the
  call does not answer.

  `fetch_validated`'s no-`Location` exit returned before the status check, and httpx calls any 3xx
  a redirect -- so a `302` without the header, or a `304`, came back as an empty body the caller
  read as content. Both exits are one path now. And delegating `read_from_url` to that helper
  imported a 200-only rule into a general web fetch that legitimately meets `203` and `206`, so
  the rule is opt-in and only the Knowledge Hub client asks for it.

  Three notes: the scope docstring claimed a default that only holds when a collection is given;
  the guide said log records and metrics are withheld in a "deployed" posture when the gate is
  strictness, and `dev-daily` is deployed but deliberately relaxed; and `DEFAULT_TIMEOUT` is an
  `httpx.Timeout` passed into two `float` parameters.

- **Review round 4.** The defect was round 3's fix again: a document the listing never returned
  has no digest at all, not even the `updated_at` fallback -- and the walk gives up after its page
  budget, so partial coverage is a designed state rather than an edge. The probe's conclusion is
  about what the metadata endpoint adds to a *listed* row, so unlisted ids are now always asked.

  Two symmetry findings, both duplication this session created: the withholding gate and its
  `{"withheld": True, "reason": ...}` reply were spelled once in `logs_api` and again in
  `metrics_api`, and now live in `plato.posture`; and `resolve_kh_token` kept its own copy of the
  blank-is-unset loop that `env_text` had just been extracted from, while its docstring cited it
  as the precedent.

  Three notes: the dashboard's withheld branch dropped the totals the router keeps deliberately,
  so a deployed replica rendered as having served nothing; the "transient, so it raises" comment
  had come to sit over a refused host and a storage 404, neither of which a retry fixes; and a
  non-base64 `data:` URL was returned without percent-decoding, so `data:text/plain,a%20b` gave
  `b"a%20b"`.

- **Review round 3.** Both defects were in round 2's own fix: the one-document probe conflated
  "the listing gave a weak digest" with "no listing ran at all". Below the threshold every id is
  weak by construction, so one probe decided the strategy for documents nothing was known about
  and left the rest with no digest -- `_needs_download` then said yes on every run and
  `page_count` was never filled, silently disabling the per-document path the threshold exists to
  select. And `_current_hash` reports any failure as `None`, indistinguishable from "no hash", so
  one timeout suppressed the metadata call for every remaining document. The probe now runs only
  when a listing produced no hashes, picks the lowest id rather than whatever set ordering
  offered, and falls back to asking everyone when it fails rather than concluding from it.

  The blank-is-unset rule was hand-spelled at four sites in `wiring_local`; `envvars` owns env
  reading and already stated it once, so it is now `env_text` beside `env` and `env_int`.

  Three notes: `raise_for_status` accepts every 2xx, so a `204` returned its empty body as the
  document -- only 200 is content now; the test named "not walked pointlessly" only ever avoided
  the metadata calls, not the walk; and two comments claimed the degraded app has no `/docs` when
  FastAPI's Swagger UI is mounted there -- the link resolves, to a CDN page the CSP blanks, which
  is a reason to omit it but not the one given.

- **Review round 2 (the loop now runs after every commit).** Three of the four defects were the
  same shape: a guard applied to one member of a family and not the others.

  The dashboard's metrics panel had no reader for the `withheld` response the logs panel was given,
  so a deployed replica that had served traffic rendered "No requests served yet." beside a
  non-zero request total in the same payload. The nav omission was applied to `/` and not to
  `/info/ui`, which renders the same nav -- so the three 404s moved one click away instead of
  going. And `status` was the third member of the script's port family without the ownership check
  `start` and `stop` had just been given, so it still reported another repo's uvicorn as a running
  Plato.

  The redirect-following loop was a line-for-line re-derivation of `tools.documents.local`'s.
  `clients` sits *below* `tools` in the layer contract and cannot import it, so the loop moved to
  `net_safety` -- where `validate_url_safe` already lives and both tiers already import from --
  and both now call it. Converting the `tools` side broke 13 of its SSRF tests, which patch a
  module-local alias my delegation bypassed: they had gone on passing against the real resolver
  instead of the stub. The validator is injectable now, so each caller's seam survives.

  Three notes with it: PyJWT's `require` checks a claim's presence and not its content, so
  `"sub": ""` decoded fine and reached a direct caller; `listing_has_sha256` put an all-legacy
  collection on a hashing hub on the wrong side of the cost model, which one probe call now
  settles instead of a guess; and the guide offered an `auth` dependency on the degraded path,
  where there is no way to supply one.

- **SSRF on the signed-URL fetches.** The URL comes out of a Knowledge Hub response and was
  fetched with `follow_redirects=True` and no validation, at both sites -- so a manipulated or
  open-redirecting response was an unauthenticated GET from inside the deployment's network.
  `net_safety.validate_url_safe` already existed for this. Both sites now share one
  `fetch_signed_url` that validates every hop before fetching it, because that helper's own
  docstring says a caller following redirects must, and follows redirects itself rather than
  leaving it to httpx. A `data:` URL is decoded locally and never fetched -- that is what the
  Mock Knowledge Hub hands out, and it touches no network.

- **A signed token without a subject is refused.** PyJWT does not require `sub`, so one produced
  `{"userId": ""}` -- which a caller keying storage on it reads as a single shared anonymous user
  rather than as no identity. Required in `verify`, and refused again in `identity_from_claims`
  for claims that did not come through it.

- **An issuer publishing no usable keys could be hammered.** The 30-second refresh floor was
  gated on the cache *holding* keys, so `{"keys": []}` -- or entries with no `kid`, which are
  dropped -- failed open: both the unforced and the forced load re-fetched on every request, two
  issuer fetches per request, unbounded. A fetch counts even when it yielded nothing.

- **Per-route metrics are withheld like log records.** `logs` was gated for a deployed posture
  because the degraded app has no identity middleware; `metrics` sits on that same app with no
  `auth` and no guard, serving the route inventory and per-route request and error volumes to
  anything that could reach the port. The totals and uptime stay, because a probe needs them and
  they name nothing.

- **The degraded nav offered three routes it does not mount.** Guide, config and database each
  404'd from a nav an operator was reading while already debugging a replica that would not start.

- **The guide promised logs a deployed posture withholds,** and `boot_contract.py` had it right
  all along. Corrected, along with the routes table. Its em-dashes are gone too.

- **A hub with no `sha256` at all is no longer walked pointlessly.** A weaker digest is worth a
  metadata call only where that call can improve it: on a hub predating hash computation nothing
  has one, so the paginated walk *plus* N metadata calls was strictly worse than the N calls
  alone. Told apart now by whether any listing row carried one.

- **`./scripts/plato-local.sh` stopped killing whatever held the port.** `listening()` is pure
  port occupancy, so `stop` and `restart` SIGTERMed another repo's uvicorn, a Streamlit or a
  Docker proxy and `kill -9`'d it five seconds later, while `start` called it "already running".
  It checks the process is Plato now, and refuses rather than guessing.

  `wait_until_up` also used `curl -fsS`, which treats the degraded replica's 503 `/health` as a
  failure -- so a typo'd `PLATO_WIRING` burned the full 30 seconds and reported that nothing came
  up, the exact confusion the fallback `/health` exists to remove. It waits for an answer, then
  reports the reason: two seconds instead of thirty.

- **Three `wiring_local` knobs treated an empty variable as a value,** where two others in the
  same file already guarded it. `PLATO_LOCAL_DB=` made the database path the root *directory*;
  `PLATO_LOCAL_CACHE=` pointed the pack cache there; `PLATO_LOCAL_TENANT=` put `""` on every
  session and manifest row. The boot line also prints paths through `display_path` now, for the
  reason the dashboard does.

- **The external-reference check could not see a stylesheet load.** It matched `src=`/`href=`
  attributes only, so `@font-face { src: url(https://...) }` or `@import` passed all three "no
  CDN, no external font" assertions -- which the bare `"http://" not in body` check they replaced
  did catch.

- **The review itself: sliced rather than skipped.** The push went out unreviewed because the diff
  exceeded the one-pass cap and the hook exits 0 there -- so the gate passed silently on exactly
  the pushes big enough to need it, which a workflow that squashes several rounds into one commit
  produces every time. It now packs whole files into slices, blocks if any slice reports a defect,
  caps the slice count, and names the files in any slice it could not reach.

- **Smaller corrections.** `_dsn_summary` already owned the engine/URL introspection
  `effective_settings` re-spelled; `materialize` and `sync_collection` documented a default scope
  the code no longer uses; an explicit `timeout_seconds=0` bypassed the floor its own constant
  documents; the v2 entity docstrings named `KnowledgeHubError` where the code raises the
  `Unsupported` subclass a caller is meant to branch on; a duplicated span-shape test that read
  the ambient cap moved beside the pair that owns that contract; two subprocess tests parsed
  stdout without checking the exit code; a registered test model card had no cleanup; and an OIDC
  test's name described a path it did not exercise.

## [2.5.0] - 2026-09-06

*Continues the [2.5.0] section below, which carries `plato 0.1.1`. `2.4.9` sits between the two, and
`2.4.8` below them, because both merged in from `dev` while this release was in progress; the
interleaving is how that shows.*

- **Inbound token verification hardened (PR review).** Three findings on `plato/oidc.py`, all
  latent because nothing wires `TokenVerifier` into a request path yet, which is the window to fix
  the shape rather than patch it.

  **An `http://` issuer is refused at construction.** Signing keys over plaintext are worse than
  no verification: an observer between Plato and the issuer can substitute their own public key,
  after which every token they sign passes. The review named `issuer`; `jwks_uri` is the URL
  actually fetched, so both are checked. `http` on loopback still works, which is the normal shape
  for a local identity provider and has no network for an observer to sit on.

  **`verify` is async.** The key fetch was a blocking `httpx.get` with a 10s timeout, and Plato's
  identity middleware is an `async def` -- so wiring it there would have stalled every request on
  the loop for as long as the issuer took. `fetch_jwks` stays injectable and now takes either a
  sync or an async callable.

  **One fetch under contention.** Check-then-fetch let every caller arriving on a stale cache read
  it as stale and call the issuer before any of them wrote, so a burst naming an unknown `kid`
  dispatched as many fetches as there were callers. Double-checked under an `asyncio.Lock`; the
  30-second floor now actually holds.

- **The health probe and the server agree on the port.** They read `PORT` differently, so they
  disagreed on every value `env_int` normalises: with `PORT=""` the server bound 8000 while the
  probe built `http://127.0.0.1:/health`, which urllib connects to port 80 -- so `--health`
  reported `unhealthy` and exited 1 for a replica that was serving. Converting the two
  `uvicorn.run` calls in the previous change is what made this reachable: before that, the same
  environment crashed uvicorn at startup and the mismatch could not be observed.

- **The Mock Knowledge Hub's HTTP double serves the v2 routes.** The in-process
  `MockKnowledgeHubClient` was given the single-document and bulk methods while the double kept
  only the v1 archive route -- so a replica wired to Mock KH took `_probe_v2`'s doomed path on
  every new `DocStore`, and nothing short of a real hub exercised the route that is now the
  default. All four steps are there (document access, trigger, status, link), the bulk trigger
  requires the same `x-user-id` the real one declares, and a `data:` URL stands in for the signed
  one.

- **A suffixed filename is attributed even when its base name is also requested.** The collision
  check ran before the exact-name lookup, so a document really called `Report (2).pdf` was
  discarded from the archive whenever `Report.pdf` was in the same request -- the strip matched
  and it was read as a KH rename -- and re-fetched individually every run. The earlier fix only
  covered the case where no `Report.pdf` exists, which is what its test asserted.

- **Three claims trimmed to what the code does.** `_bulk_fetch`'s docstring said bulk "must not be
  able to fail the materialize" while a denial deliberately propagates eight lines below, and
  `bulk_download_documents` claimed it never raises while raising for an old pin, a missing user
  id and a denial. And a comment added in the previous change blamed a hazard on a call site that
  never had it: the `os.getenv(a) or os.getenv(b)` chain it replaced already skipped an empty
  value -- the hazard is in routing such a chain through `env`, not in the chain itself.

- **A transient failure on the probing document no longer downgrades the whole store.**
  `_v2_probed` was set *before* awaiting the probe, so a refused signed URL raised out with the
  route still unknown but recorded as probed -- and `DocStore` is long-lived behind
  `fabric.docs`, so that one bad moment sent every later `materialize` down v1 as well. Exactly
  what `_v2_unsupported` exists to prevent, undone by the ordering of two lines. The flag is set
  only once the probe returns.

- **An empty variable no longer ends a fallback chain.** `env` treats a set-but-empty value as
  set, so `env_int("JAPES_UI_PORT", "PORT", ...)` took its default without ever consulting `PORT`:
  with a blank `JAPES_UI_PORT` and the platform's `PORT=8080` the UI bound 8501, a port nothing
  routes to. An empty string is not a number, so `env_number` now takes the first *non-empty*
  name. This is the hazard its own docstring cites, reintroduced one layer up while fixing it.

- **`env_int` reaches Plato's own entry points.** Both called `int(os.getenv("PORT", "8000"))`,
  where `PORT=""` raises and the server does not start -- the same conversion applied to the
  queue, the launcher and the span cap in the previous change, and not to the two call sites in
  the service being changed.

- **The JWKS fetcher is dispatched by `call_maybe_async`.** `_fetch_and_cache` hand-rolled
  sync/async dispatch by calling the injected fetcher inline and testing the result -- which runs a
  synchronous fetcher *on the event loop*, the precise stall this class was made async to avoid.
  The repo has one home for that dispatch, which offloads a sync callable, and this same change
  already used it in `settings_api`.

- **A narrowed poll ceiling is reported rather than reversed.** `floor=BULK_POLL_INITIAL_SECONDS`
  silently handed back the initial interval, so an operator lowering the ceiling got the opposite
  of what they set with no indication. The invariant holds, and now says so.

- **A test that pinned formatting instead of behaviour is gone.** It regexed the inline JS for an
  exact expression, so hoisting that expression into a local would fail it with nothing changed.
  The branch logic is asserted through the router; the page test now only checks what the router
  cannot.

- **The same false-claim defect, one field over.** `PLATO_SQLITE_PATH`'s effective value went
  through `display_path`, so an absolute stored path could never equal its own resolved value and
  the panel reported it as not applied -- exactly what had just been fixed for `PLATO_DB_BACKEND`
  six lines above. Compared in the same form now, and omitted when the two agree. The router also
  drops any hint equal to the stored value, so a provider that spells a value differently cannot
  produce that claim again.

- **An unsettled probe no longer serialises the batch.** `_probe_v2` is documented as running once
  under a lock, and that held only when a probe *settled* the flag. It cannot settle when neither
  route has the document -- a stale KG reference, a deleted document -- so every document took the
  lock in turn and a ten-at-a-time batch ran at peak concurrency 1. Whether a probe has run is now
  recorded separately from what it concluded.

- **`env_int` reaches the rest of the estate.** Six queue knobs and two launcher knobs still did
  `int(env(...))` / `int(os.getenv(...))`, which is the empty-string hazard the helper was
  introduced for -- converted in `agent_hooks` and not in its siblings.

- **A manifest recorded under the previous default scope is adopted.** The default moved from the
  output directory to the collection id; `DbMaterializeManifestStore` keys its rows on the scope,
  so those rows were addressed by the old key and invisible under the new one. The file store had
  a flat-map bridge and this had none, so an upgrade cost one re-download of everything.
  `materialize` reads the old key once when the new one is empty and re-saves under the new one.

- **Two tests said less than they looked like.** Both `test_a_document_the_listing_cannot_identify`
  and the legacy-document test built a client and immediately rebound the name to a subclass, so
  the setup between them mutated a discarded object. And the dashboard assertion checked only that
  `f.effective` and "in effect" appeared in the page -- it would have passed with the comparison
  inverted, which is the defect above it. It now asserts the rendered guard.

- **The collection listing now implements the cost model it documents.** `list_probe_threshold`'s
  comment states it -- the listing's cost is the size of the *collection*, the per-document cost is
  the size of the *request* -- and the gate only ever read the request. Six documents out of a
  thirty-thousand-document collection therefore walked the full page ceiling, identified none of
  them, logged a WARNING every run, and then made the six metadata calls it was meant to replace:
  strictly worse than not listing at all. The walk now carries a budget of one page per requested
  document, so it can never spend more calls than the alternative would, and giving up is logged
  as the cost model working rather than as a fault.

- **The configuration panel stopped contradicting itself about the database backend.**
  `effective_settings` reported SQLAlchemy's drivername while the field's vocabulary is
  `sqlite`/`common`, so the two could never be equal and the page took its "differs from stored"
  branch every time: `in effect: postgresql+asyncpg (the stored value is not applied)` when it was
  applied. It now answers in the field's own terms.

- **A document legitimately named `Report (2).pdf` is attributed from a bulk archive.** The
  collision matcher claimed any basename ending ` (N)`, so a real filename of that shape was read
  as one KH had renamed and re-fetched individually on every run. A rename is only a rename when
  the un-suffixed name is another wanted document, which is now the test.

- **`span_text_max_chars` reads through `env_int`,** rather than hand-rolling the same
  empty/unparseable/floor contract the helper had just been introduced for -- and which
  `effective_settings` calls it to obtain. `KnowledgeHubUnsupportedError` is exported from
  `jazzx_sdk.clients` beside its siblings: it is the one new error whose documented purpose is for
  a caller to branch on, and it was the one not exported.

- **Two smaller corrections.** A malformed document id in a bulk request raised a bare
  `ValueError` from above the `try`, out of a method whose every other failure is a logged `None`.
  And four `getattr(self._config, ..., <literal>)` fallbacks were dead branches -- `__init__`
  always builds a `FabricConfig` -- one of which carried a literal contradicting the real default
  (`0`, bulk off, against the field's `25`).

- **A bulk task whose status call fails no longer polls out the window.** The generated
  `asyncio_detailed` does not raise on an error response, so a 404 (the task record expired) or a
  500 arrived as `parsed is None` -- read as an unknown state, which this code deliberately treats
  as "still running", it polled the full patience window before the caller could fall back. Five
  minutes by default, and the test for it took 30 seconds to fail against the old behaviour.
  `BULK_POLL_TIMEOUT_SECONDS` is also floored now, the one member of that family read without one:
  at zero or below, `_await_task` gave up after a single status call and bulk was silently off for
  every caller that did not pass `timeout_seconds` itself.

- **A `NullMaterializeManifestStore` spends no identifying calls again,** which is the whole
  contract of that store. The listing had been gated on set size alone, so a large set walked the
  collection for a store that cannot skip a single download -- and populated `page_count` where
  the field's own comment said it would be `None`.

  Fixing that naively coupled two callers that want the listing for different reasons: the probe
  wants digests, and the bulk path wants the names it attributes archive members with, which is
  worth the walk whatever the manifest store is. Three tests caught it. Both are asked now, and
  `unique_ids` bounds `to_download` from above so a set too small for bulk cannot claim to need
  it.

- **A denial is not retried per document.** `retry_async` owns which exceptions retry via
  `retryable=`, and the rule was stated only in the handler above it -- so a 403 burned the full
  exponential backoff for every document before the re-raise could surface it. One kwarg, in the
  place that decides.

- **The dashboard no longer reports a Postgres database name as the SQLite path.**
  `PLATO_SQLITE_PATH`'s effective value came from `url.database` for every backend, and that field
  is labelled "sqlite backend only". The driver name was already being read one line above.

- **Two smaller corrections.** The dead `if not worth_listing: unresolved = ...` assignment is
  gone -- the comprehension above already yielded every id in that case. The configuration panel's
  "(overridden below)" pointed at nothing below it and reversed the meaning: when the stored value
  differs from the effective one, the stored value is the one *not* applied. And the mock's
  `download_document_v2` ignored `collection_id`, answering for a document that lives in another
  collection where the real route 404s.

- **Numeric environment variables get one guarded reader.** `envvars.env_number` /
  `env_int` now handle the three ways an env-configured number goes wrong -- unset, empty, and
  unparseable -- in the module that documents the empty-string hazard in the first place. Two
  defects closed with it:

  `FabricConfig`'s four new int knobs did `int(env(...) or N)` unguarded, and they are its only
  int env fields, so `JAPES_KH_LIST_PAGE_SIZE=none` raised out of `default_factory` and *no*
  `FabricConfig` could be constructed at all. The `_seconds` helper added in the same change
  guarded exactly this for its own knobs and the config siblings did not get it -- so the helper
  is gone and both read the shared one.

  And the floor was applied only on the parse path, so it did not hold when the variable was
  merely unset: `JAPES_KH_BULK_POLL_INITIAL_SECONDS=10` against a defaulted ceiling gave
  `initial=10, max=5`, and `min(delay, MAX, remaining)` silently discarded the configured
  interval. The floor now applies to the answer.

- **A bulk job is not started without the names to attribute it.** `bulk_download_threshold` and
  `list_probe_threshold` are set independently, so a bulk threshold below the probe threshold is
  reachable by configuration alone -- and there the job ran, attributed nothing (KH names members
  after the document, and no listing means no names), latched `_bulk_available=True`, and every
  document was fetched individually anyway. Every call, with one INFO line.

- **Every task's exception is retrieved when a document is denied.** `_fetch` was given a
  `KnowledgeHubAccessError` re-raise inside a bare `asyncio.gather`, which surfaces the first and
  leaves the siblings running unawaited -- each then reporting "Task exception was never
  retrieved" for the identical 403, with nothing able to catch it. Outcomes are collected first,
  then one is raised.

- **`page_count`'s comment is honest.** It said "None elsewhere and where KH has not computed it",
  but it only ever comes from the probe or the listing -- so a `NullMaterializeManifestStore`,
  which exists to spend no calls, leaves it `None` for a PDF that does have one. Stated rather
  than papered over: spending calls to fill a field would contradict that store's whole contract.

- **The bulk user-id guard is shared, not copied.** The mock had a verbatim duplicate of the
  client's `_current_user_id` and its three-line message; both now come from one module-level
  helper and one constant, so the guard that decides whether a bulk download is attempted cannot
  drift between them.

- **The v2 entity comment is back above its own flag,** having been stranded ~70 lines up by the
  bulk and download blocks inserted beneath it -- where it read as documenting
  `KH_V2_BULK_AVAILABLE`.

- **An empty duration variable no longer breaks the import.** `float(os.getenv(NAME, "300"))`
  runs at module scope, and `os.getenv`'s default covers *unset*, not *empty* -- so
  `JAPES_KH_BULK_TIMEOUT_SECONDS=` (a compose file or configmap entry with no value) raised
  `ValueError` and took the whole `jazzx_sdk.clients` package down. `jazzx_sdk.config.envvars.env`
  documents this exact hazard, which is why the fabric knobs in the same change read
  `env(...) or <default>`. All three durations now go through one helper that treats empty and
  unparseable alike: default, with a warning.

- **The collection listing has to earn its place.** It was made unconditional on the reasoning
  that it is "a single call". It is a paginated walk, and its worst case is a requested id no
  longer in the collection: neither of the loop's exits ("a short page", "found everything asked
  for") fires, so one stale KG entity walks the whole collection to conclude what a single
  metadata call answers with a 404. The listing's cost is the size of the *collection* and the
  per-document cost is the size of the *request*, so `list_probe_threshold` (default 5) decides
  between them -- and below it the metadata call answers the digest and the page count together
  anyway.

- **`bulk_download_threshold` is floored,** like the two paging fields twelve lines below it.
  At `-1` the value stayed truthy and `len(to_download) >= -1` was always true, so every
  `materialize` took the bulk path -- a one-document one included, and a queue job with no
  identity header for it to use.

- **A denied listing is not an empty collection.** `_bulk_fetch` and `_fetch` were each given an
  explicit `KnowledgeHubAccessError` re-raise; `_collection_metadata`, the third new call site on
  the same path, still swallowed it. The import is hoisted to module scope now rather than
  repeated in three function bodies.

- **Two smaller corrections.** The mock's access response read `mime_type`, a key the mock never
  writes (`create_document` stores `content_type`), unobservable only because that value is
  currently hardcoded. And `plato/oidc.py`'s docstring justified the async conversion with a
  middleware that does not exist yet -- the reasoning is sound as a choice made while the shape is
  still free to change, which is what it now says.

- **A denied per-document download is no longer an empty result.** `_bulk_fetch` was given a
  `KnowledgeHubAccessError` re-raise last round and `_fetch` was left swallowing the identical
  error three hundred lines below -- so below the bulk threshold, or with it set to 0 (a
  documented setting), a caller with no grant on the collection got `materialize` returning
  nothing but warnings. The comment justifying the bulk re-raise named this exact path.

- **A hub without the bulk route is asked once.** The single-document route latches
  `_v2_download`; the bulk route caught bare `Exception` and re-probed on every call, so a v1-only
  hub paid a doomed trigger round trip per `materialize`. It now classifies with the same
  `_v2_unsupported` predicate and latches `_bulk_available`, which is what
  `KnowledgeHubUnsupportedError`'s own docstring exists to allow.

- **The mock requires a user id for a bulk download, like the real route.** It ignored `user_id`
  entirely while the same mock had just been given the empty-selection refusal on the stated
  grounds that a mock must not pass where production fails -- and the identity requirement is the
  one that bites in a queue job, where no inbound request supplies one.

- **Computed fields are read from the listing row as well as from `meta_data`.** KH writes
  `sha256`/`page_count` into the `meta_data` column on upload and on backfill, so the bag is where
  a listing row carries them -- confirmed in Knowledge Hub's own source, against a review finding
  that read the generated model's declared fields and concluded otherwise. But
  `DocumentMetadataResponse` shows KH also has a shape that carries them flat, and an unknown
  top-level key lands in the row's `additional_properties`, so both are read now. Breadth rather
  than a fix, and one line.

- **Two orphaned comments reunited with what they describe,** both left behind by insertions in
  this same change: the listing-page note above a class it no longer applied to, and the
  single-document flag's note above the bulk flag.

- **A legacy document gets its metadata call again.** `_doc_hash_from_metadata` falls back to
  `updated_at`, and every listing row carries one -- so a document with no computed `sha256` still
  produced a truthy digest, `unresolved` was always empty, and the metadata call that is the only
  thing which backfills `sha256` and `page_count` was never made. The documented fallback was
  unreachable, and the tell was in this diff's own test, which had to strip `updated_at` from a
  synthetic listing to reach the branch. The fallback now fires on a digest that is not a
  `sha256:`, not on the absence of one.

- **The default manifest scope is the collection, as `sync_collection` always had it.** It was the
  output directory as the caller spelled it, which was harmless while the manifest was one flat
  map and is not now that storage is partitioned by that key: the same directory reached
  relatively on one run and absolutely on the next, or a volume mounted at two paths, is a
  different scope with nothing in it, so the whole set re-downloads.

- **A denied bulk download is no longer reported as an unavailable one.** `_bulk_fetch`'s blanket
  handler caught `KnowledgeHubAccessError`, which every `except Exception` in the client is
  careful to re-raise -- so a 403 for the forwarded `x-user-id` logged "bulk download
  unavailable", downgraded to per-document, and the identical denial there exhausted the retries
  and dropped the documents with only warnings.

- **`meta_data` cannot override the row it rides on.** Spread after `name` and `updated_at`, a
  document whose uploader stored either key in that free-form bag would drive archive member
  attribution and the change probe with it.

- **The listing knobs live in `FabricConfig`,** beside `bulk_download_threshold`, rather than as
  module-level `os.getenv` globals added in the same change. They can now be set per fabric, and
  the test for the zero-page-size floor no longer needs `importlib.reload`.

- **The mock refuses an empty document selection like the real client.** It still built a valid
  empty archive for `[]`, and the new mock bulk route delegated to it -- a mock a test passes
  against and production does not.

- **`"[::1]"` dropped from the OIDC loopback set:** `urlsplit` strips the brackets, so the entry
  could never match and `"::1"` already covered it.

- **The configuration panel reports what the replica resolved, not just what is stored.** Blank
  fields, including `JAPES_ENVIRONMENT` on a replica whose `/info` said `local`. The page was
  accurate and useless: those variables are genuinely unset, and the values come from defaults or
  from the wiring. The posture keys default when absent, the span cap has its own default, and the
  local wiring hands the database backend and path to `DbStore` in code -- so the two read-only
  posture fields, on the page precisely to show what the replica decided, showed nothing.

  `SettingField` gains an `effective` value and `create_settings_router` an optional provider for
  it; Plato resolves the posture, the span cap and the live database URL. The page renders it as
  the field's placeholder plus an "in effect" line, marked `(default)` or `(overridden below)` so
  a stored value is never confused with a resolved one.

  Never populated for a secret: masking `value` is pointless if the same string is reported under
  another name, and the router drops the hint rather than trusting each provider to remember. A
  provider that raises is logged and omitted -- a hint is not worth failing the panel for.

- **The bulk poll intervals are floored, like the listing knobs already were.**
  `JAPES_KH_BULK_POLL_INITIAL_SECONDS=0` left the backoff at zero forever (`0 * 2` is still zero)
  and `sleep(0)` returns at once, so the poll became a tight loop against KH for the whole
  patience window -- thousands of status calls for one archive. `JAPES_KH_BULK_POLL_MAX_SECONDS=0`
  did the same from the other side, pinning every sleep to zero whatever the initial value was.
  `_LIST_PAGE_SIZE` and `_LIST_MAX_PAGES` were already floored against exactly this input class,
  which is what made the omission a real inconsistency rather than a hypothetical one.

- **`KnowledgeHubUnsupportedError` reaches the whole optional-binding family.** It was introduced
  for the v2 download routes while `create_entity_v2` and `read_entities_v2` -- the precedent the
  new code's own comment cites -- still raised a bare `KnowledgeHubError` for the identical
  "this client pin lacks the binding" condition, so a caller could downgrade permanently on one
  and not the others.

- **Smaller corrections from the same review.** The per-call `manifest_store` is typed against
  `MaterializeManifestStore` rather than `Any`, which matters because `materialize` compares it
  against `NullMaterializeManifestStore` to decide whether to probe at all. `_bulk_fetch` takes
  the listing as a required argument, since the only caller always supplied it and the optional
  branch could never run. `AttributeError` no longer counts as "this hub has no v2": `hasattr`
  already covers the absent method, so the only ones left come from inside the client and would
  have downgraded the store while hiding themselves.

- **Only one document probes the v2 route.** The comment claimed the probe "costs one call rather
  than one per document", but `materialize` runs documents concurrently and the flag is read per
  coroutine -- so on a hub with no v2 route, up to `concurrency` documents each paid a doomed call
  before any of them wrote the answer. The probe now happens once under a lock, and lives in its
  own `_probe_v2` rather than as a branch inside the download path.

- **`download_document_v2` reports absence and failure differently (PR review).** It returned
  `None` for everything: a 404, a non-200 access call, an expired or refused signed URL, an
  unreachable blob host. On a hub already proven to serve v2, one 403 mid-batch therefore looked
  exactly like a missing document -- `materialize` dropped it from the result, and `retry_async`
  never saw it, because it only retries a raise. Now `None` means 404 and nothing else; every
  other failure raises. `KnowledgeHubUnsupportedError` separates "this pin or hub has no v2 route"
  (downgrade permanently) from "this call failed" (retry), which were the same type. `materialize`
  keeps the probe fallback on `None`, because a hub with no v2 route 404s it exactly as a missing
  document does -- that one ambiguity is real and unavoidable, and it is now the only one.

  A transient v2 failure also no longer downgrades the rest of the batch: the blanket handler
  flipped `_v2_download` False for the life of the store, so a single `ConnectError` sent every
  later document down v1 on a hub that does serve v2.

- **An empty `document_ids` no longer downloads the whole collection.** `if document_ids else
  UNSET` mapped `[]` to `UNSET`, which the API reads as "everything", so an explicit empty
  selection archived and downloaded the entire collection. `download_documents` was cited here as
  getting it right and did not: it passed `[]` through, httpx drops an empty-list query param
  entirely, and KH's own filter is `if document_ids:` -- equally falsy -- so the server saw no
  filter and archived everything by a different route to the same place. Both refuse an empty
  selection now. An explicit `timeout_seconds=0` is also honoured rather than becoming the 300s
  default.

- **The collection listing terminates on its own.** `JAPES_KH_LIST_PAGE_SIZE=0` -- a plausible
  reading of "no paging", and the neighbouring `bulk_download_threshold` does document 0 as
  meaningful -- left `skip` unchanged with `len(batch) < page` false forever, hanging every
  `materialize` inside a `try` that cannot catch a hang. The size is floored at 1, and the loop
  now has a page ceiling (`JAPES_KH_LIST_MAX_PAGES`) so it does not depend on the hub returning a
  short page: a hub answering full pages of documents nobody asked about satisfied neither exit
  condition.

- **The bulk path stopped listing the collection twice.** `_bulk_fetch` re-fetched the listing
  `materialize` already held for exactly those ids -- on the bulk path, which is the large
  collection by definition, that doubled the full paginated walk. It also now guards
  `download_document_v2` with `hasattr` the way it always guarded `bulk_download_documents`, so an
  older client's `AttributeError` reaches the feature check rather than the blanket handler.

- **One fabric can keep more than one manifest.** `FileMaterializeManifestStore` accepted `scope`
  and ignored it, on the reasoning that one directory needs one manifest. The reason first given
  here was wrong and is corrected: the two runs did *not* overwrite each other, because
  `materialize` loads the map, updates only its own doc ids and saves the union. What the flat
  file did not give is isolation -- every scope read every other scope's entries, and
  `DbMaterializeManifestStore` partitioned where this did not, so the two stores answered the same
  question differently. The file is now
  partitioned by scope, as the DB store always was, and `materialize()`/`sync_collection()` also
  take a `manifest_store` per call for when the two should not share a file at all. A manifest
  written by the previous version is kept as a fallback for any scope that has not written yet, so
  the upgrade does not cost one re-download of everything per scope.

- **The change probe is one call per collection, not one per document.** It made a
  `get_document_metadata` request for every unique document. KH's `listDocuments` returns
  `meta_data` -- a free-form bag where its upload pipeline stores `sha256` and `page_count`,
  verified to survive the generated model's `to_dict()` -- along with `updated_at` and `name`, for
  every document in the collection. One paginated listing now answers
  the probe, the page count and the bulk archive's member attribution together. Only a document
  the listing cannot identify still costs its own call: `sha256` is absent until KH's metadata
  endpoint backfills a legacy upload, and only that endpoint does the backfill.

- **`MaterializedDoc.page_count`.** From the same listing, so it costs nothing extra. `None` for
  non-PDFs and for a document whose count KH has not computed, which is what KH itself reports.

- **Bulk download, and fabric choosing between the two routes.** `bulk_download_documents`
  drives KH's v2 job: trigger, poll to a terminal state, ask for the link, fetch the archive from
  storage. Backed-off polling with a cap (`JAPES_KH_BULK_TIMEOUT_SECONDS`,
  `JAPES_KH_BULK_POLL_INITIAL_SECONDS`, `JAPES_KH_BULK_POLL_MAX_SECONDS`). An unrecognised task
  state counts as still running: guessing "done" loses the archive and guessing "failed" abandons
  a job that would have succeeded, so the timeout is what ends it.

  **Bulk is not simply better, which is why fabric picks.** `materialize` uses one archive at or
  above `bulk_download_threshold` (default 25, `JAPES_KH_BULK_THRESHOLD`, 0 disables) and the
  per-document route below it. Three round trips plus an archive build cost more than a handful of
  documents' bytes. More decisively, **the bulk route requires an `x-user-id` header and the
  per-document route does not** -- it is the subject KH authorizes against, so bulk is unavailable
  in a queue job or anywhere else with no inbound request, which is where a batch download looks
  most attractive. Rather than send an empty header, the method raises and names the alternative;
  `materialize` treats that as a fallback, never an error, because per-document already works.

  **Archive members are attributed, not assumed.** KH names them after the document, not its id,
  so fabric resolves `{doc_id: name}` in one `list_documents` call and matches on that, with the
  id as a second chance. Anything ambiguous is deliberately left out and fetched individually:
  two documents sharing a name would otherwise write one document's bytes to the other's file,
  which is silently wrong content and worse than a slower download. A partial archive tops up
  per document; a response that is not an archive falls back whole.

  Member naming is now read from Knowledge Hub's own source rather than inferred:
  `sanitize_string(doc.name)`, with a repeated name broken by an appended ` (1)`, ` (2)` in
  whatever order KH iterates the documents. That order is not reproducible from here, so a
  suffixed member is never attributed -- it is detected and fetched individually. Matching also
  tries an ASCII-normalized form, because the sanitizer strips non-ASCII. KH skips a document it
  cannot read rather than failing the archive, which confirms a partial archive as a normal case
  the top-up path already covers. The task-state vocabulary is still read from the generated
  client, which is why an unknown state waits rather than deciding.

- **`download_document_v2`: one document over the v2 signed-URL path.** The v1 route has KH read
  the blob, build a one-member ZIP around it and stream that back through the service, so
  `fabric.docs.materialize`'s per-document loop paid compression and a proxy hop on every
  document. v2 answers with a short JSON access response and the bytes come straight from storage.
  The generated client already carried the bindings and japes was not calling them.

  `access_only=True` returns that response (`url`, `expires_at`, `file_name`, `content_type`,
  `size`, `disposition`) without fetching the blob, for a caller that can hand the URL to a
  browser and never move the bytes through this process.

  The signed URL is fetched with a bare client, deliberately: it carries its own authorization,
  and reusing the configured one would send the Knowledge Hub bearer token and the identity
  headers its hook injects to the storage host. A test asserts that, and fails if the configured
  client is used.

  `materialize` prefers v2 and falls back to v1, because a deployment may not serve v2 yet. The
  fallback is not just an exception guard: `download_document_v2` reports failure as `None` rather
  than raising, and a v1-only deployment 404s the v2 route exactly as a missing document would --
  so while probing, whichever route answers settles it, and once v2 has worked a `None` means the
  document is genuinely absent rather than costing a wasted v1 round trip per miss. Available on
  the same terms as the v2 entity API: an older client pin loses this method and nothing else.

- **A degraded replica no longer serves its log buffer to anyone who can reach the port.** The
  fallback app is a bare `FastAPI` with no identity middleware, and it is exactly where an
  unresolvable `PLATO_WIRING` lands in a deployed environment -- so an unauthenticated caller could
  read every buffered record. Log records are content, not counters, so a deployed posture now
  withholds them unless the deployment passed an `auth` dependency, which is the same shape
  `create_config_router` uses for writes. The panel shows the reason instead of the records.
  `boot_contract.py` claimed the degraded surface was "`/info` alone ... strictly smaller than a
  gated app"; it has not been that since the diagnostics were added, and the row now says what is
  actually served.

- **The guide ships.** `_GUIDE` pointed at `docs/PLATO.md`, and `docs/` is copied into neither the
  image nor a wheel -- so `/docs` and `/redoc` served "The guide is not present in this image" in
  every artifact except a source checkout, while the nav still linked to it. The file moved to
  `plato/guide.md`, beside the module. Verified by building the wheel: it carries the guide, the
  alembic ini, the migration tree and the dashboard.

- **`create_feedback_router` follows `API_V1_PREFIX`.** It is the one router a consumer constructs
  itself and passes through `extra_routes`, so its static default left feedback on `/api/v1` while
  every route `create_plato_app` built moved.

- **The local boot output names a path that exists.** Both branches printed `/v1/info`, which has
  404'd since the prefix moved; the same stale path survived in the boot contract, the wiring
  docstring and the feedback module docstring.

- **A test fixture stopped evicting third-party modules.** `tests/test_plato_wiring.py` deleted
  every module imported during a test, to clean up the fake wiring modules it installs. Importing
  `plato.wiring_local` pulls in `sqlalchemy.orm` for the first time, so that got deleted while
  `sqlalchemy.inspection` survived, and a later test failed with `Type <class 'object'> is already
  registered`. The full suite passed only because something earlier happened to import
  `sqlalchemy.orm` first. The fixture now drops only the `plato_test_*` modules it created.

- **`logger.exception(...)` reaches the log panel with its traceback.** Only `getMessage()` was
  kept, so the call an operator opens that panel to read arrived as its least informative line.
  Redacted and tail-trimmed like the message, and rendered under it in the same cell.

- **`?limit=0` returns no records.** `max(1, min(limit, maxlen))` handed back one to a caller who
  asked for none.

- **A trailing slash in `API_V1_PREFIX` no longer takes the replica down.** FastAPI asserts a
  router prefix starts with `/` and does not end with one, and it asserts while the app is being
  built -- so `API_V1_PREFIX=/api/v1/` raised in `create_plato_app`, `run_role` fell back to the
  info-only app, and that raised the same assertion: the container exited on a traceback,
  contradicting both the "a serving role always comes up" contract and the promise that setting
  the variable moves the routes. `api_prefix()` now normalizes, so `api/v1`, `/api/v1/` and
  `//api//` all resolve to something a router accepts.

- **Flex is asked for only where it exists.** `vision_flex=True` prefixed `flex_` onto whatever
  model was resolved, and only the OpenAI provider strips that alias -- so on
  `JAPES_LLM_PROVIDER=anthropic` it reached `messages.create()` as part of the model name and
  would have 400'd on the first call. The eligibility rule existed as a set in a test file, which
  is why nothing in the library could apply it; it now lives in `llm.model_identity` as
  `FLEX_ELIGIBLE` and `supports_flex()`, and the test imports it rather than keeping a copy that
  could drift while both looked green.

- **An unconfigured deployment names no vision model at all.** `vision_model_for` was annotated
  `-> str | None` and documented as returning `None` when the runner's own default already reads
  images, but it could never return `None`: `resolve_model()` always answers, falling back to the
  global default. So an `AgentExecutionService(default_provider="anthropic")` passed as `agents=`
  got an OpenAI model pinned onto it, and `agents.run` infers the provider from an explicit model
  name -- the override the docstring said it avoided. It now returns `None` unless the caller
  named a model or the environment named a provider or model.

- **`./scripts/plato-local.sh --help` prints the header, and stops there.** The usage branch had a
  hardcoded line range that ran four lines past it, presenting `set -uo pipefail` and a `cd` as
  usage. It now reads to the first line that is not a comment, so the text cannot drift from the
  header again.

- **`GET {prefix}/database?count_rows=false` reports `truncated`** like the counting path, so a
  consumer tests the field rather than its absence.

- **A markdown table needs a real separator.** `set(line) <= set("|-: ")` is satisfied by a blank
  line, so a lone `|`-prefixed row followed by one rendered an empty `<table>`. Not reachable from
  the current guide, only from a future edit to it.

- **The tool-span output shape is pinned.** It changed from a bare string to `{"text": ...}` when
  the cap became configurable, and nothing recorded that, so a span reader treating the field as
  text would have found a mapping.

- **A degraded replica serves `/info` where a healthy one would.** The fallback app mounted every
  router on the static constant while `create_plato_app` resolved through `api_prefix()`, so with
  `API_V1_PREFIX` set the two disagreed -- and an operator probing the configured path during a
  wiring failure would have got a 404, which reads as "the process never started" rather than "it
  started and cannot serve". That is the exact drift the comment removed in the previous change
  had warned about, reintroduced by making only one side configurable. The app is now built by
  `_info_only_app`, separately from serving it, which is also what lets the boot-contract tests
  assert on real routes instead of grepping the function's source.

- **`/redoc` is served, not left blank.** `/docs` was fixed by dropping FastAPI's CDN page; its
  sibling was left in place under the same `default-src 'none'`, so it returned 200 with
  `cdn.jsdelivr.net` assets and rendered nothing. Both now serve the guide.

- **The guide's routes table follows the prefix.** `guide_html` substituted the nav and left the
  table on `/api/v1`, so a moved deployment read a page that contradicted itself. The substitution
  now runs over the body, and the file keeps the default prefix on disk so it still reads correctly
  in the repository. The logs row also said "the last 500 log records" where the endpoint returns
  200 per request from a 500-record buffer.

- **The local wiring no longer writes into `site-packages`.** `parents[1]` is the repo root in a
  source or editable checkout and `site-packages` from a wheel, which is where the sqlite file,
  the pack cache and alembic's working directory would have gone -- and the stated reason for
  moving this module into the package was precisely that it should work when installed. The root
  is now the checkout when it looks like one, and otherwise `PLATO_LOCAL_ROOT` or the working
  directory. Alembic is pointed at the ini by absolute path, since `script_location` is relative
  to the ini itself.

- **A second `attach_log_buffer` applies what it asked for.** The call was gated on "already
  attached", and `run_role` attaches with defaults before `create_plato_app` attaches again, so a
  non-default capacity was unreachable in the serving path. There is still one handler; a resize
  keeps the records already buffered.

- **Reviewed and rejected: the Fable 5.1 cache rate.** `cached_input: 0.25` against `input: 10.0`
  is 0.025x where every other Claude model is 0.1x, which reads as a missing digit. It is not: the
  pricing page footnotes Fable 5.1 and Mythos 5.1 as the documented exception. The row's
  provenance note now says so, so the next reader has the answer without re-deriving it from the
  ratio.

- **Reviewed and rejected: the metrics middleware's `500` seed.** Reported as counting a dropped
  SSE stream as a server error. A mid-stream disconnect does not reach that path -- `call_next`
  returns the response before the body streams, so the recorded status is the response's own 200.
  The seed covers an unhandled handler error, which does arrive as a raise because this middleware
  sits inside `ServerErrorMiddleware` and outside `ExceptionMiddleware`, and 500 is correct there.
  Changing it to a client-error code was tried and dropped real failures out of the error count. A
  test now pins both halves.

- **The vision flex tier is a model alias, not a provider argument.** `classify_page_images` and
  `split_document` took a `service_tier` string and passed it to the provider verbatim, where
  OpenAI accepts only `auto`/`default`/`flex`/`priority` -- so the default `"standard"` was an
  invalid value, and it also suppressed japes' own flex translation, which is guarded on
  `service_tier` being absent. Asking for flex therefore disabled it. Flex is now expressed as the
  `flex_` model prefix that `parse_model_tier` already strips, which is the one mechanism japes
  owns end to end.

- **The vision default no longer overrides the deployment's provider.** A hardcoded
  `gpt-5.6-luna` meant a deployment on `JAPES_LLM_PROVIDER=anthropic`, holding only an Anthropic
  key, was routed to OpenAI for page classification and failed on a call that used to work.
  `vision_model_for()` keeps the configured default whenever its card says it reads images, and
  substitutes only for a text-only default. An uncarded model is left alone: it may well have
  vision, and swapping it on a guess is the override being fixed.

- **One missing table no longer hides every later row count.** The database panel counted all
  tables in a single session; postgres aborts the whole transaction on the first failed statement,
  so the alphabetically-first table the migration had not created turned every subsequent count
  into `PendingRollbackError` -- in exactly the degraded-schema state `/info` exists to report. A
  session per table now. Every table failing is reported as one connection problem rather than as
  many table problems.

- **`API_V1_PREFIX` moves the routes, as the guide already claimed.** `api_prefix()` was written
  and exported and then never called, so `create_plato_app` used the constant and the environment
  variable did nothing. The prefix now resolves through it when the caller passes none, an explicit
  argument still wins, and the page links follow. `docs/DEPLOYMENT_ENV.md` said Plato served `/v1`
  and that the variable was read by nothing; both were true until 2.5.0 and are corrected.

- **The default model moves to `flex_gpt-5.6-luna` and `claude-sonnet-5`.** Both are newer and
  cheaper than what they replaced: for 1M input and 100k output, $0.58 against $7.25 on OpenAI and
  $3.00 against $4.50 on Anthropic. The `flex_` prefix is kept, so OpenAI calls stay on the
  cost-optimized tier as they already were. `split_document` takes `vision_flex` to opt a page
  split into flex -- throughput-bound work, where the `429 Resource Unavailable` flex returns is a
  normal outcome the llm tier already falls back from. Two tests hold the line: every provider
  default must be carded, and a future bump must not silently make the default more expensive.

- **Claude Fable 5.1 is carded**: 1M context, 128K output, vision and tools, `$10/$50`, and cache
  reads at `$0.25/MTok` -- a quarter of Fable 5's, which is the headline change. Its provenance
  records the retrieval time, not just the date: vendor pages move during a day. Note that forced
  tool use returns an error on this model, unlike Fable 5.

- **What a span retains is capped, and the cap is configurable.** Tool spans truncated at a bare
  `1000` characters and LLM spans recorded no output at all, so the larger of the two was the one
  not covered. Both now use `JAPES_SPAN_TEXT_MAX_CHARS` (default 4000, editable from the
  dashboard), and a truncated output carries its `raw_length` -- a cut 40KB answer and a short one
  look identical otherwise, and the difference is usually what the reader is chasing. An LLM
  summary also keeps `output_types` and `status` whole, which is what separates "the model refused"
  from "the model answered and we cut it". A bad value falls back rather than raising: tracing must
  never fail the run it is tracing.

- **Commits are shown short.** A 40-character hash wraps onto a second line in the Build card;
  12 identify a commit uniquely in a repository this size, and the full value stays on the tooltip.

- **`common` reports its commit instead of "installed (unversioned)".** It is a submodule whose
  packaging version has not moved in a long time, so the old string said something was installed
  and nothing about which. Fixing it surfaced that `build_info()` ran twice per `/info` request,
  shelling out to git each time in a working tree; it now runs once.

- **Plato serves a dashboard at `/`, and the pages it serves now actually run.** Seven panels over
  the JSON APIs -- deployment tier, versions, schema revision, database tables and row counts,
  request counters, recent logs, configuration -- refreshing every 10s and pausing when the tab is
  hidden, so a dashboard left open does not keep counting itself in the metrics it displays.

  **The pages were dead in a browser, including the `/info/ui` that already shipped.** The API's
  `default-src 'none'` blocks a self-contained page's own inline `<style>` and `<script>`, so a
  browser rendered the labels as unstyled text and ran nothing. `security_headers.page_csp()` is
  the policy for a single-file page; the middleware already used `setdefault` for exactly this, and
  the JSON API keeps the strict default. `spa_csp` does not fit: its `script-src 'self'` permits a
  *file* and still blocks an inline script.

  Three new read-only routes back the panels. `{prefix}/logs` is a bounded ring buffer (500
  records) on the root logger, redacted through `redact_secrets` -- a connection string logged once
  would otherwise sit in memory and be served to whoever opens the page -- and it reports the
  effective log level, so an empty panel reads as "nothing logged at WARNING" rather than as a
  broken capture. `{prefix}/metrics` counts requests per route *template*, never the raw path,
  because per-id keys grow without bound; an unmatched request collapses to one key so a scanner
  cannot mint one per URL. `{prefix}/database` reports backend, host and per-table row counts, and
  never the DSN, which carries the password.

  Logs, metrics and the dashboard are served on the degraded path too. A replica that could not
  build an app now shows what it is and the boot warning explaining why, which is when an operator
  most needs both.

  **The configuration panel writes.** Fields render from the catalogue with the right input type,
  and Save posts to the `PATCH {prefix}/config` that already validates, persists and re-wires -- so
  the posture gate stays on the endpoint rather than being re-implemented in a page. Two details
  are load-bearing: only changed fields are sent, because posting the whole form would rewrite a
  field another operator edited between the read and the write; and a password box still showing
  its mask is not an edit, or saving anything would overwrite every secret with the placeholder.
  `JAPES_ENVIRONMENT` and `JAPES_STRICTNESS` render disabled -- a replica must not promote or relax
  its own posture over HTTP.

  **One nav across all three pages**, defined once rather than in each file, so they cannot drift
  into three link sets. The page you are on renders as text rather than a link, and the JSON routes
  sit behind a divider -- `info` the page and `info` the JSON are the same information, and a
  reader should be able to tell which they are about to open.

  **`/docs` serves a written guide instead of a blank page.** FastAPI registers its own Swagger UI
  there first, so it won the route and then failed to load, pulling from a CDN the CSP blocks.
  Dropping that route and serving `docs/PLATO.md` makes the path useful: how to run Plato, every
  route, how configuration changes, and what a degraded replica does. Rendered by a small markdown
  function rather than a library, since a dependency in the wheel for one page is not worth it.

  **`scripts/plato-local.sh`** is `start`/`stop`/`restart`/`status`/`logs`/`run`. `start` waits for
  `/health` and tails the log if it never answers -- with a non-fatal boot, silence is the only real
  failure. `status` reports version, tier, posture, commit and anything degraded.

  **Nothing on the page names the machine it runs on.** An absolute path carries the username, and
  this page gets screenshotted, so paths are shown relative to the working directory or `~`-elided.
  Both pages carry an inline favicon, having previously generated a `/favicon.ico` 404 per load -- requests the
  metrics panel then reported as unmatched.

- **A scanned package can now be split and classified by looking at its pages.**
  `split_document(..., vision=True)` renders the pages and classifies what they show, where it
  previously raised `DocumentNotReadableError` and sent the caller to DocIntel. DocIntel returns
  text and leaves the split unsolved; this answers both in one pass.

  **The algorithm did not change, and that is the point.** `split` already windowed pages with
  overlap and voted per page weighted by confidence *and* centrality; smoothing, short-run
  absorption and family merging all operate on labels. Exactly one line coupled any of it to text
  -- how a window becomes classifier input -- so the vision route is a fork there and reaches the
  same machinery. A second implementation for images would have been the mistake.

  **A page counts as scanned when it has no text *and* carries an image.** "No text" alone is not
  enough in either direction: requiring *every* page to be blank meant `vision=True` was silently
  ignored on a combined packet with a digital cover sheet, which is the shape this route exists
  for; counting any blank page meant one genuine separator sheet rasterized an entire digital
  document and threw away a good text layer. Once one page qualifies every page is rendered, since
  a window holding images for some pages and text for others puts two kinds of evidence in one
  ballot.

  `ocr_fallback` does not also run when vision answered -- DocIntel bills per page and its text
  would be discarded -- and `max_pages` is applied before rendering rather than after, since
  rasterizing 500 pages to classify 10 is minutes of work for nothing.

  Two smaller decisions follow from what the evidence is. The filename heuristic does not run on
  the image path: it fires before any model call on the text path, but a scanned package is
  precisely where one filename covers forty pages. Bookmarks are skipped too, since labelling an
  outline segment joins its pages' text, which is empty by definition here.

- **An image reaches any provider from one neutral part.** `ImagePart` is the counterpart to
  `format_tools`: a caller builds one and the provider it reaches converts it, rather than
  hand-writing `input_image` for OpenAI, `source.base64` for Anthropic and `inline_data` for
  Gemini and picking correctly every time. Bytes are held as bytes, so a caller that read a file
  does not encode for a format it has not chosen, and the same part can go to two providers.

  `detail` is the one knob carried neutrally, because it is the one that sets tokens per page:
  OpenAI names it `detail`, Gemini `media_resolution`, and Anthropic has no equivalent.

  **Images are not the only thing that needs translating.** A Responses content list accepts
  `input_text`/`input_image`/`input_file` and nothing else, so the neutral `{"type": "text"}` block
  -- which Anthropic takes verbatim and Gemini maps -- is rejected by OpenAI. Every block of a
  list-content message is converted, so one block shape cannot go out two ways in a request.

  **Conversion happens on every path a caller actually reaches**, which took several passes to get
  right. `AgentExecutionService.run` delegates to `LLMManager` for any call without tools, so the
  llm tier needed it as much as the agent tier -- and that tier speaks Chat Completions, where an
  image is `image_url` wrapped in an object rather than Responses' flat `input_image`. Two APIs
  carrying the same idea in different shapes, so there are two translators. `OpenAIProvider.run`
  also returns from a single-message fast path, which is the *default* route for a bare
  `AgentExecutionService()`, so the conversion sits above that branch rather than below it.

  `llm.providers.local` flattens content for a text-only backend, naming an image rather than
  serialising it: base64 in a prompt is noise a model cannot read. And the request ledger records
  `{"type": "image", "media_type", "bytes"}` instead of the bytes -- `CostTracker._offload_payload`
  serialises then regex-scans what it captures, so a 40-page split would have written and scanned
  tens of megabytes nobody reads back.

  **`supports_vision` has its first reader.** It had been defined on `ModelCard` and fed from
  `model_data.json` since it was added, and nothing consulted it. An image bound for a text-only
  model now fails before the request goes out. Only a card that positively says no refuses --
  the card set is incomplete by design, and refusing everything unregistered would make vision
  unusable on any new model.

- **Message content reaching Gemini was converted in three places and each got a content list
  wrong differently.** The agent tier wrapped it in `str()` and sent the Python repr as text; the
  llm tier passed the list itself where a string belongs; the native models joined the text parts
  and dropped everything else silently. Three implementations, three wrong answers for one input.
  `llm.gemini_content` owns the conversion now, and an unknown block raises rather than vanishing.

  **The native models raise too**, which matters more than it sounds: `resolve_model` routes a
  `claude...` or `gemini...` model through `AnthropicNativeModel`/`GeminiNativeModel`, whose content
  flattening kept only blocks carrying a `text` key. Once the SDK began producing image blocks, an
  image sent through the generic provider was discarded, nothing warned, and the model answered
  plausibly from the prompt alone. Asking about a page without sending the page is worse than not
  asking.

  An empty turn still produces one empty part rather than none: a `Content` with `parts=[]` is
  rejected outright, and `{"role": "assistant", "content": ""}` is a legitimate history entry.

- **PDF pages render to a pixel budget rather than a fixed DPI.** Measured against a real loan
  corpus: US Letter at 110 DPI lands at 1.13 MP, just inside Anthropic's downscale threshold, while
  Legal at the same DPI is 1.44 MP and gets downscaled on arrival -- and that corpus is *majority*
  Legal, so a Letter-tuned DPI would have been wrong for most of it. Fitting each page to 1.15 MP
  gives every page size the most resolution that survives. PNG rather than JPEG, which is
  counterintuitive and measured: a rendered text page is mostly flat white, and PNG wins by 13 KB
  at these sizes.

- **Measured, and it inverts the premise the work was proposed on.** Vision is *not* cheaper than
  extracted text: 1.4x on OpenAI, 1.9x on Gemini, 2.7x on Anthropic, per page, on the pages where
  both routes are possible. The corpus-wide figure of 13x cheaper-for-text is an artifact -- 80% of
  those pages have no text layer, where text is not more expensive but unavailable.

  So the justification is capability, not cost. Vision is the only route that reads a scanned
  package, and it is cheaper than DocIntel while also deciding boundaries. On a readable page it
  stays the fallback. An image is a fixed cost per page and text scales with density, so a dense
  enough page does cross over -- above ~765 text tokens on OpenAI, ~1508 on Anthropic -- but that
  is a per-corpus measurement, not a default. Accuracy is not measured: a cheaper route that is
  wrong more often is not cheaper.

- **Three SWIG shutdown warnings are filtered, by exact message.** PyMuPDF's generated bindings
  define types with no `__module__`, which Python 3.12 deprecates, and the warning fires at
  interpreter shutdown so it lands after pytest's summary with nothing to attribute it to. Scoped
  to those three messages rather than a blanket `DeprecationWarning` ignore, which would hide the
  ones worth seeing -- the anthropic 1.0 migration among them.

- **The MLflow reporter addressed runs through process-global state and blocked the event loop.**
  `MlflowReporter.report` was `async def` and did every MLflow call inline: `set_experiment`,
  `start_run`, three `log_*` calls and an artifact upload, all synchronous HTTP against a tracking
  server. The `async` signature hid it, since a caller awaiting this reasonably assumes it yields.
  It now runs under `asyncio.to_thread`.

  `mlflow.start_run` keys off a *thread-local* active run, so two concurrent publishes interleaved
  into whichever entered last. Runs are now created through `MlflowClient` and addressed by explicit
  `run_id` on every call -- which `observability/backends/mlflow/tracer.py` already did, and stated
  the reason for. One module had the answer and its sibling did not.

  `create_run` has no context manager, so the run is terminated explicitly in a `finally` with
  `FINISHED`/`FAILED`; without it a failed publish leaves a run `RUNNING` forever, which reads as a
  job that never finished rather than one that failed. `experiment_run_to_mlflow` lost its one line
  of global state (`mlflow.set_experiment`) for the same reason, and `log_artifact_with_retry` now
  documents that it sleeps up to 30s and must be called off the loop.

  Its return value is checked rather than dropped: it reports exhaustion by returning `False`
  instead of raising, so a run whose results artifact never uploaded was reported `FINISHED` with
  params and metrics and no results, and the caller had no way to know.

- **Importing `jazzx_sdk` no longer imports SQLAlchemy.** `evaluation/__init__` eagerly imported the
  two DB-backed stores, which define ORM models at class-definition time, and `fabric.guidance`
  reaches them through `evaluation.prompt_registry` -- so anyone touching guidance paid for the ORM.
  They resolve through `__getattr__` now, matching the pattern `observability/__init__` already
  used. 1697 modules to 1572 on a bare import.

- **The Plato boot contract is one table, and `--health` is the readiness probe.** The policy -- a
  serving role comes up and reports, a `job:*` role refuses -- was stated as prose in eight places,
  and changing it meant finding all eight. It is data in `plato/boot_contract.py` now, the
  documentation table is rendered from it, and `tests/test_plato_boot_contract.py` holds each row to
  the code path it describes.

  Making the boot non-fatal removed the signal an orchestrator relied on, and nothing replaced it.
  `python -m plato --health` probes the container's own `/v1/health` and exits non-zero unless
  `configured` is true. `--check` cannot answer that: it parses the environment in a second process
  and never sees what this one resolved, so it is documented as a parse diagnostic, not a gate.
  `create_app` grew a `readiness_provider` hook to put the answer on `/health`, the one path the
  identity middleware exempts -- a probe against `/info` was 401'd on every strict-posture replica.

  Building the table surfaced one thing the prose had wrong. Three situations leave a replica
  serving `/info` alone, so "blocks chat" is meaningless for them: there are no chat routes to
  block. Exactly one row turns a turn into a 503.

- **Configuration written through `/v1/config` now survives a restart, and the database itself can
  be swapped at runtime.** Migration `0002_setting` adds `plato_setting`, and `DbSettingsStore`
  reads the environment overlaid with what the database holds -- the database winning, because a
  value written through the API is a later decision than the container's environment.

  **Two layers, because one is impossible.** `PLATO_DB_BACKEND`, `PLATO_SQLITE_PATH` and
  `DATABASE_URL` say *which* database the durable layer is in, so writing them into it and then
  swapping the database leaves the new value in the old one. Those stay in the environment;
  everything else persists.

  **A NULL value is not a missing row.** Writing an empty value persists "explicitly unset", which
  has to survive a restart or the environment's value silently returns. `forget()` drops the row
  instead, so the deployment's own configuration applies again. Both intentions come up.

  **`tenant_id` on a deployment-wide table.** `plato.tenancy` requires it in every table's key, and
  the rule earns its bluntness -- the table exempted "because it is not tenant data" is the one that
  later holds some. Deployment-wide rows carry the reserved `_platform` id, the same answer
  `PLATO_PACK_TABLE_DESIGN.md` reached for shared packs, and per-tenant settings stay possible
  without a migration.

  **The live database swap.** `DbStore.dispose()` marks a store permanently dead, so a swap cannot
  mutate one in place: `DatabaseHandle` holds the current store behind a single reference every
  per-tenant store resolves through, and the caches are keyed on the store they were built against
  so a swap cannot hand back one bound to the retired engine. The replacement is built and its
  tables created *before* the swap, so an unreachable database leaves the running one in place.

  In-flight requests finish against the old database. Nothing can know when the last session on the
  retired engine closes, so it is kept referenced rather than disposed -- disposing immediately
  fails a request that was already mid-flight and did nothing wrong. Only reachable in a relaxed
  posture, since that is where config writes are, which is also why `create_all()` is acceptable
  there rather than the alembic chain.

  Durable settings are exported into the environment at boot, before the wiring resolves anything:
  a setting written yesterday is only durable if something reads it back, and every consumer of it
  reads the environment. Never fatal -- a replica that cannot reach its settings table starts on
  its environment, degraded and saying so.

- **Plato serves its own configuration at `/v1/config`, and a relaxed replica can be fixed over
  HTTP without a redeploy.** Most of this already existed and nothing mounted it:
  `jazzx_sdk.server.settings_api` does masking, unknown- and non-editable-key rejection,
  `If-Match` concurrency and audit. Plato now supplies the catalogue its wiring actually reads --
  and no more, because a field nothing reads is a control that appears to work.

  **`SettingsStore` accepts async implementations.** It was a sync protocol, which quietly ruled
  out every store a deployment wants: `fabric.db` is async-only, so a database-backed store could
  only have honoured a sync `read` by calling `asyncio.run` on the loop already running the
  request, which raises. The router awaits either through `call_maybe_async`, so existing sync
  stores are unaffected.

  **The posture gate is injectable.** `settings_api` refuses unauthenticated writes in a *deployed*
  posture, which would have blocked dev-daily -- the one environment where someone needs to fix a
  Knowledge Hub URL without a redeploy. `posture_gate` lets a caller that has thought about it pass
  `strict_mode` instead; the default stays `deployed_posture`, because that is the safe answer for a
  library whose consumer has not.

  **`degraded` is a callable now, not a boot snapshot.** `missing_config()` recomputes from the
  environment as it is, so `/info` and the chat gate see a value set a moment ago. A snapshot would
  have meant the endpoint asked to confirm a fix denying the fix happened. Verified end to end: a
  strict replica 503s, the value is set over HTTP, and the same process serves.

  Read is open in every posture, since "what is this replica configured with" is the question asked
  about a box behaving oddly and the answer is already masked. Writes need a relaxed posture or an
  `auth` dependency, and the posture keys themselves are non-editable -- a replica must not be able
  to promote or relax itself in response to a request.

  Re-wiring lives in the store's `write`, not in a wrapper around the route: replacing a FastAPI
  endpoint with a generic `*args, **kwargs` function leaves FastAPI seeing no parameters, and the
  body it then never parses comes back as a 422 that looks like the caller's fault. That was the
  first shape of it.

- **A real-shaped profile now ships with the suite.** Two pack tests ran against a jazzx-assistant
  checkout beside japes, so they only ever ran on a machine that had both -- in CI they skipped,
  printing a path under the runner's home that read like a misconfiguration. `tests/fixtures/
  reference_profile` mirrors the structure (persona in its own file, empty `scope`, both streaming
  flags, three skills as separate documents with tools and references) and two tests cover the
  loader and the runtime binding path everywhere. Confirmed by breaking the fixture: a dangling
  `persona.md` reference and a dropped skill each fail a different one.

  Generic on purpose. Pinning the fixture to a consumer's domain would make every edit here a
  question about whether their assistant still works, which is a contract test belonging in their
  repo -- their CI has the profile by definition, and a failure would land where the fix is. The
  sibling-gated pair stays as local extra assurance, with a skip reason that says so.

- **The suite runs clean: zero warnings, down from eleven.** Two unrelated causes, both of them
  noise that trained the eye to skip the warning block.

  Nine classes named `Test*` are subjects, not tests: experts, skills and pydantic models whose
  bases take constructor arguments, so pytest tried to collect each one and skipped it with a
  warning. `__test__ = False` is the documented opt-out and keeps each name matching the thing it
  implements, rather than renaming the subject to please the collector.

  Two `datetime.utcnow()` calls in `test_automation_handler.py` are deliberately naive -- they
  assert the handler tolerates a datetime with no tzinfo. `utcnow()` is deprecated, and its
  naive-UTC replacement is an aware `now()` with the tzinfo dropped, which keeps the input naive
  instead of quietly fixing the thing under test.

- **The double's own contract is now pinned by tests, after two rounds of getting it wrong.**
  Recording calls on the class made the base class's list process-global for directly-constructed
  instances: a scripted list resumed at whatever the previous test left behind, so a fresh agent's
  *first* call returned the second response, and `last_call()` handed back another test's call
  instead of raising. Class-level state is only safe on a `returning()` subclass, which belongs to
  one test; the base class is shared by the whole process. Bound subclasses record on the class
  (one flow, several agents), direct instances record on themselves, and the scripted index follows
  whichever is authoritative.

  `last_call()` had the same split-brain: a `classmethod` reads the class list either way, so a
  directly-constructed agent that *had* been called raised "was never called". It is a descriptor
  now, binding to the instance's record on an instance and the class's on a bound subclass. The
  test that was meant to cover it asserted only the never-called case, which is the one path where
  the empty class list happens to give the right answer -- it passed against the broken code.

  Also: `returning(RuntimeError)` raises rather than handing the class back as a result, an empty
  script is a loud error rather than `None` on every call, and the module docstring's em-dash is
  gone along with the ones in the Plato modules added alongside it.

  Nine tests now cover the shapes, each one a case a hand-rolled double had and a draft of this got
  wrong. A test double's failures are silent by construction, which is exactly how a two-value
  unpack survived against a three-value contract.

- **A real bug, found by migrating the hand-rolled doubles onto `ScriptedReasoningAgent`.**
  `ReasoningAgent.run` returns `tuple[Any, SQLiteSession, TokenUsage]`, and
  `agents/reasoning/grounding.py:184` unpacked two. Every real call to `HeadingsOnlySelector`
  raised `ValueError: too many values to unpack` -- caught by the surrounding `except`, logged as
  "selection call failed", and degraded to no selection. So headings-only grounding selected
  nothing, on every call, quietly.

  The test could not catch it because its hand-rolled double returned two values as well: the
  double agreed with the bug instead of with the contract. That is the argument for a shipped
  double in one line -- seven test files each wrote their own, and each was free to be wrong in its
  own direction. Confirmed by restoring the two-value unpack against the migrated test, which now
  fails.

  Seven files migrated (`curator_synthesis`, `evaluator_mode`, `adjudication_agent`,
  `adjudication_segment`, `learning_candidate_adapter`, `precomputed_grounding`,
  `condition_evaluator`); no hand-rolled `ReasoningAgent` double remains. `test_split.py` keeps
  its own, correctly -- that one doubles `AgentExecutionService`, a different interface.

  Three defects in the shipped double surfaced while migrating real usages, each from a shape a
  hand-rolled version had and the first draft did not: a callable response stored as a class
  attribute became a *bound method* and arrived with `self` as an extra positional; a scripted list
  restarted per instance, so a flow building one agent per segment handed every segment the first
  response; and calls recorded only on the class meant two directly-constructed instances shared
  one history. Responses that are exceptions are now raised rather than returned, which is how a
  test says "this call fails".

- **`ScriptedReasoningAgent`, and the last `synthesize_bucket(llm=...)` caller is gone.** The SDK
  deprecated `llm=` in favour of `agents=` while shipping a test double only for the deprecated
  path, so every caller testing the replacement hand-rolled one -- five test files here did, and
  `test_learning_loop_end_to_end.py` stayed on the deprecated call for exactly that reason, its
  docstring saying "swapping it is a separate change". A deprecation whose replacement is harder to
  test than the thing it replaces does not get adopted.

  `jazzx_sdk.agents.scripted.ScriptedReasoningAgent` is the counterpart to `ScriptedLLM`: a fixed
  response, a list consumed in order, or a callable receiving the call's kwargs -- the three shapes
  the hand-rolled versions grew, including routing on `name` where one flow makes several
  differently-named calls. `returning()` builds the bound subclass each of them defined by hand.

  The suite now runs clean of that warning, verified with `-W error::DeprecationWarning`.

- **A pricing overlay for any model with a long-context tier registered broken.**
  `plato/reference/model_overlay.py` stored pricing with `asdict()`, which renders `long_context`
  as a nested dict, and reloaded it with `ModelPricing(**payload)`, which takes that dict as-is.
  Construction *succeeds*, so the overlay registered with a plain dict where a `LongContextPricing`
  belongs, past the `except` that would have logged and skipped a malformed row. The failure then
  surfaced as `AttributeError: 'dict' object has no attribute 'threshold_prompt_tokens'` from
  `for_prompt_size`, at cost-computation time, far from the load that caused it.

  Every frontier model with a large-prompt premium carries a tier, so this was the common case for
  exactly the models an operator is most likely to correct a rate on.

  `_pricing_from_json` already did this correctly for the bundled `model_data.json` and was
  private, so the overlay hand-rolled its own version and got it wrong. It is now
  `pricing_from_mapping`, public, and both callers use it: reconstructing pricing from a dict is
  one operation, and the second hand-rolled copy was the bug. The card path alongside it had
  already been written carefully for the same class of problem (`_CARD_TUPLE_FIELDS` rehydrates its
  tuples), which is what makes the pricing omission an oversight rather than a shared gap.

  Reported in review of the pushed branch; confirmed by restoring `ModelPricing(**payload)` against
  the new test, which fails.

- **Four fixes from the first real deployment's environment, and the boot is now unstoppable.**

  `PLATO_WIRING` was set to `acme.plato_wiring:build` -- the placeholder from this repo's own
  documentation, written before a shipped wiring existed. The docs now name
  `plato.wiring_default:build`. (A placeholder failed at boot when this landed; the boot contract
  above later reversed that for serving roles, which come up on `/info` with the reason instead.
  A `job:*` role still exits 4.)

  `JAPES_REQUIRE_IDENTITY=true` was silently ignored: the wiring built
  `ServerSettings(require_identity=strict)`, and with no environment tier that is `False`. A
  deployment asking for identity enforcement got none and was told nothing. An explicit request now
  wins in any posture, and still cannot turn enforcement *off* in a strict one.

  `KH_API_KEY` -- the name the platform actually sets -- was read by nothing, so a deployment that
  supplied its Knowledge Hub token got an unauthenticated client. Accepted now, with the
  JAPES-prefixed names still winning.

  **Blank means unset only where blank is not a value the field could hold.** The first attempt
  dropped every blank key so the field's default applied -- fine for a `bool` or a `Literal`, which
  cannot be `""`, and wrong for a `str` whose default is non-empty. `llm_fallback_provider=""` is
  how a deployment says "no fallback" (`llm/manager.py` gates on `if fallback and
  fallback_provider`), so clearing it silently re-enabled Anthropic on every primary failure for an
  OpenAI-only deployment. It also contradicted `env()`, whose contract is that an empty string
  counts as set.

  Making the documented "every field" true then needed a settings *source*, not a validator: the
  env source JSON-decodes a complex field before any validator runs, so `JAPES_LLM_TASK_ROUTING=""`
  raised `SettingsError` regardless. `_BlankAwareEnvSource` drops a blank per field, ahead of the
  decode. Its type test unwraps unions only -- recursing into a generic's parameters made
  `dict[str, dict[str, str]]` report `str` among its types, so a dict field read as one a blank
  could legitimately fill. The alias lookup matters for the same reason: pydantic-settings keys an
  aliased field by its alias, so every `JAPES_`-prefixed variable was taking the unknown-key branch.

  A blank value crashed `JAPESSettings` -- first `JAPES_ENVIRONMENT`, and after a per-field fix
  still `use_managed_identity` and `llm_enable_local`, booleans on the same model fed by the same
  platform. The coercion is model-wide now, dropping blank keys so each field's own default
  applies, because a rule stated unconditionally in the docs cannot have an unwritten list of
  exceptions. Relatedly, a *blank* `JAPES_KNOWLEDGE_HUB_TOKEN` shadowed a filled `KH_API_KEY`:
  `env()` treats an empty string as set by design, so the token lookup now takes the first
  non-blank name. An empty `JAPES_ENVIRONMENT=""` crashed `JAPESSettings`. Container platforms render a
  declared-but-valueless variable as `""`, so the literal rejected it and every caller of
  `get_runtime_settings()` raised. Empty now means unset, which is what the operator meant; a typo
  is still rejected loudly.

  **And a schema behind the image no longer exits 5 for a serving role.** `/info` reports which
  revision the image expects against what the database has, and a replica that answers that is
  worth more than one that exits having printed it once. A `job:*` role still refuses: it takes no
  requests, consults no gate, and writes, so a sweeper deleting rows through the image's models
  against an older schema corrupts quietly -- which is the failure the check exists for, and which
  the first version of this change removed for every role at once.

  Getting that reported at all took two corrections. `build()` returned a *snapshot* of what was
  missing, so a note recorded a moment later never reached `/info`, which answered
  `configured: true` against a mismatched schema -- strictly worse than the exit it replaced. It
  now hands over the function. And the note lived in `plato/__main__`, which under `python -m plato`
  runs as `__main__`: importing `plato.__main__` executes the file a second time and binds a
  *different* list than the one appended to, so the value was never going to arrive. State shared
  across that boundary now lives in an ordinarily-imported module.

  **What `degraded` reports is the running process, not the environment and not a boot snapshot.**
  Both of those were wrong in opposite directions. Reading the environment cleared the pack gap the
  moment `PLATO_PACK_DIR` was set, while the process kept the empty registries it loaded once --
  `/info` claiming assistants the replica could not serve. A boot note went stale the other way: a
  database corrected through `swap_database` kept being reported as sqlite until a restart.

  So each check reads whatever actually decides the answer: the process for the pack (are there
  skills?) and the database (what is the *current* store?), the environment for the Knowledge Hub
  URL, LLM key and tenants, and boot notes only for what neither can rediscover -- a schema behind
  the image, and a pack path that was set but would not load. The pack message says a restart is
  what fixes it, since setting the variable will not.

  The pack predicate itself then got written twice. The first version probed `_skills` and `all()`
  -- names `SkillRegistry` does not have; it is a `NamedRegistry` with `_items` and `__len__` --
  so every registry read as empty and a *correctly configured* deployment permanently reported
  "No assistants loaded", 503-ing its chat routes in a strict posture. Guessing at an API
  defensively was worse than reading it: `getattr` with a default does not raise, so the `except`
  written to catch exactly that never fired. It is `len(skills)` now.

  Nothing caught it because no test in that file had ever built against a pack that loads -- every
  one pointed `PLATO_PACK_DIR` at `/nonexistent/pack`, so the negative case asserted the absence of
  three other reasons and never that the pack gap was absent. There is a loadable pack from the
  shipped reference profile now, and the always-on predicate fails against it.

  `PlatoWiring.degraded` is declared as the tuple-or-callable it now is, with `resolve_degraded()`
  for consumers; it had kept a `tuple[str, ...]` annotation while the shipped wiring assigned a
  function, so `" ".join(wiring.degraded)` raised `TypeError`.

  **Boot notes reach every wiring, not just the shipped one.** They were merged inside
  `plato.wiring_default`, so a deployment naming its own factory -- the documented normal case --
  got `configured: true` and an open chat gate against a mismatched schema, having also lost the
  exit that used to catch it. The merge is in `plato.wiring.resolve_degraded`, which every role's
  app goes through whoever built the wiring.

  **And the posture gate applies the rule the wiring applies.** It checked
  `JAPES_REQUIRE_IDENTITY` alone while `build()` had been changed to `strict or requested`, so a
  production replica with the variable unset returned 3 and never started -- the gate refusing the
  very configuration it was about to produce. That is the exact sibling of the bug it was fixing,
  one file away.

  `resolve_kh_token` moved to `jazzx_sdk.config.envvars`, the tier both readers can import.
  `ClientLayer` and `FabricConfig` read the same platform credential under *different name lists*,
  so a deployment could end up with an authenticated Knowledge Hub client and an unauthenticated
  fabric one. The import-linter contract caught the first attempt, which had `fabric` importing
  `client_layer`.

  Also: `_apply_durable_settings` called `asyncio.run` unconditionally, so building inside a
  running loop raised and leaked an un-awaited coroutine, surfacing as a RuntimeWarning against
  whichever test was collecting garbage. It now closes the coroutine and says why it skipped.

  First-boot logging is one line rather than a traceback: before migrations the settings table
  legitimately does not exist, and a stack trace there reads as a failure in a log whose next line
  says the replica started fine.

- **Plato 0.1.2.** The deployable wiring, the four deployment tiers, the strictness axis, and
  `/v1/config` with durable settings and a runtime database swap. The SDK stays at 2.5.0: Plato's
  version tracks the service, not the library it is built on.

- **Plato ships a deployable wiring, and `dev-daily` is now a posture the platform recognises.**
  The cloud replica reached `PLATO_WIRING is not set` -- correct behaviour, since the package
  deliberately ships no default: Plato hosts *someone's* assistant. That argument holds for the
  pack and the tenants and does not hold for the plumbing around them, which every environment
  resolves identically and was about to be re-derived per deployment.

  **Four deployment tiers, one canonical name each: `local`, `dev-daily`, `staging`,
  `production`.** `deployed_posture()` recognised only `production`/`prod`/`staging`, so a shared
  cloud environment reported `environment=local` and ran with identity enforcement off, in-process
  stores allowed and a Mock Knowledge Hub permitted -- the same exposure as production, since other
  people can reach it, with none of the guards.

  The cloud tier is `dev-daily` rather than `dev` deliberately. `dev` reads as a synonym for "my
  laptop" and means exactly that in jaci's `.env.template` and juno, so naming the cloud tier `dev`
  would flip both to deployed and take away the Mock fallback their developers rely on -- a failure
  landing on laptops, pointed the opposite way to the one the tier exists to prevent. `dev` and
  `test` are accepted aliases of `local`, and `prod` of `production`; aliases resolve rather than
  being rejected because a name the table does not know reads as *not deployed*, which loses a
  fail-safe quietly.

  **Strictness is a second axis, and `dev-daily` is relaxed by default.** Deployed and strict came
  apart the moment dev-daily existed: *deployed* is about what a replica holds, *strict* is about
  what the environment is for. dev-daily is where someone pushes a branch to see whether it works,
  so a tier that refuses to start without a real Knowledge Hub, Postgres and identity headers does
  not serve it. `strict_mode()` is strict on `staging`/`production` and relaxed on
  `local`/`dev-daily`, and `JAPES_STRICTNESS` overrides it -- tightening any tier, loosening every
  one except `production`, where the guards it would disable are the only thing between an
  anonymous caller and real data.

  Relaxed, a Plato replica comes up the way a laptop does: Mock Knowledge Hub, sqlite, identity
  off, chat serving. What is missing is still collected, logged at boot and reported by `/info`; it
  is advice there and enforcement (`enforce_degraded`) on staging and production.

  Four guards moved onto the new axis -- the Mock Knowledge Hub refusals in `client_layer` and
  `fabric`, the durable-queue-store requirement in `runtime`, and Plato's `require_identity`
  refusal. Two deliberately did not: an unauthenticated configuration write and an unattributed
  actor stay gated on *deployed*, since neither stops a replica coming up and relaxing them costs
  real exposure on a shared environment for no gain. A first pass moved all six, which is what
  five posture tests caught.

  `check_settings(environment=...)` takes the environment as an argument so tests need not mutate
  the process, so strictness reads it through `strict_for(name)` rather than the process
  environment -- otherwise the check reads one environment and its strictness another, and the
  injection seam silently stops working.

  `environment_tier()` returns the tier and `deployed_posture()` still returns the operator's own
  spelling, since that is what lands in logs and error messages. One table backs both, and
  `JAPESSettings.environment` now derives its allowed values from it rather than restating them.

  **`plato/wiring_default.py`** is the shipped factory: `PLATO_WIRING=plato.wiring_default:build`.
  One file for both postures, deciding by posture rather than by two files drifting apart.
  Deployed, it expects Postgres via `common.core.db`, a Knowledge Hub URL, an LLM provider key, an
  explicit `PLATO_TENANTS`, and `X-Tenant-Id` per request, and turns `require_identity` on.
  `scripts/plato_wiring.py` stays the zero-infra demo.

  **It starts anyway when those are missing, and says so in three places.** Refusing to boot was
  the first shape of this, and it was the wrong trade: the exit reports only the first missing
  variable, so four missing variables cost four deploy cycles. Now every missing item is collected
  into `PlatoWiring.degraded` and the boot continues. The startup log lists all of them; `GET
  /info` reports `extra.configured` and `extra.degraded`; and the chat routes answer 503
  `plato_not_configured` naming what is missing, rather than serving a Mock Knowledge Hub's empty
  context as though it were real. Sessions, `/info` and the migration check keep working, which is
  why the database falls back to sqlite (itself reported) instead of being withheld: those are the
  surfaces you diagnose with. Identity is not relaxed by degradation.

  **A pre-existing crash surfaced on the way, and is why the list is derived rather than
  restated.** `JAPESSettings.environment` was `Literal["dev", "staging", "prod"]` while
  `deployed_posture()` treats `production` as its canonical deployed value, so any service setting
  `JAPES_ENVIRONMENT=production` died inside `get_runtime_settings()` instead of being recognised
  as deployed. Restating the names in two places is what allowed that, so the literal is now
  `Literal[ENVIRONMENT_NAMES]` off the tier table and a test asserts the derivation holds.

  The two reads fail in opposite directions on purpose: `environment_tier()` treats an unknown name
  as `local`, because guessing that a typo means production would refuse to start a laptop, and
  `JAPESSettings` rejects it loudly. Together a typo gets one clear error instead of a quiet loss
  of every fail-safe.

  **The environment-resolved `ClientLayer` moved out of `jazzx_sdk.ui`.** `get_client_layer` and
  friends were named for their first caller; nothing in them was Streamlit-specific, and a server
  wiring should not reach into a module called `ui` for the platform handle a deployment runs on.
  They now live in `client_layer.py`, beside the `ClientLayer` they build and the env resolution
  they use, with `jazzx_sdk.ui` re-exporting the public three so jaci's imports keep working
  (surveyed first: only jaci's two UI pages and one japes test).

  Nine tests, including the one distinction the tier rests on -- `dev` non-deployed, `dev-daily`
  deployed, `production` deployed but not pre-production -- and a fixture that clears the LLM keys,
  because a developer's own key silently satisfied that check while the test was being written.

- **The reference chat conductor can require its grounding, and no longer loses escalated turns
  from history.** Both came out of reading what jazzx-assistant's handler does above a single agent
  call, and both are cases where the pipeline could not express something a consumer had to
  orchestrate outside it -- which is the thing `ground_step` was written to prevent.

  **Required grounding.** `gather_degrading` degrades every source to its default so one dead
  system cannot sink a turn. That is right for advisory context and wrong for evidence: a turn
  grounding on a loan record that is down answered confidently from an empty default, and nothing
  in `turn.grounded` could tell that default from a real empty result. `ground_step(required=...)`
  and `build_chat_components(required_sources=...)` name the sources whose absence must stop the
  turn (`True` for all), raising `GroundingRequiredError`, which `run_chat_turn`'s existing
  `on_step_error` already turns into an incomplete reply that halts the run. Default stays
  `False`, so every current caller keeps degrade-everything.

  Which sources degraded is read off `gather_degrading`'s own `SourceProgress.failed` reports
  rather than re-derived, by chaining a recording hook onto the caller's. The primitive needed no
  change: it already knew, it just had no one to tell. A second return value would have been a
  thing every other caller had to ignore.

  **Side-branch persistence.** `respond` persists its own turn, so the direct route was covered and
  the other two were not: `escalate` and `refuse` both hand back an answer the user reads without
  touching the agent, leaving conversation history with a hole exactly where the turn was most
  worth keeping, and the next turn then loaded a history that skipped it. Closing it needed a
  public seam -- `_persist_turn` was private, so a pack could not do it either -- so
  `InteractiveAgent.persist_turn` now exposes the same decision `respond` makes, with the same
  conversation guard. `persist_side_branch` is shared by `finalize_step` and `stream_chat_turn`'s
  three one-shot returns, because a copy in each is two chances for the routes to disagree about
  what history contains. It fails soft: bookkeeping must never lose a delivered answer.

  Eight tests, each confirmed to fail against the previous behaviour: required-source failure stops
  the turn and the agent is never called, `required=True` covers every source, a non-required
  failure still degrades, the caller's progress hook still fires alongside the recorder, escalated
  and refused answers are persisted, the direct branch is *not* persisted twice, a store failure
  still delivers the answer, and the streaming route persists its side branches too.

- **`aiosqlite` became a core dependency, having been declared as a dev one.** It was added for
  tests ("zero-infra backend for testing SqlConversationStore") and a runtime branch then grew onto
  it: `DbStore._sessionmaker` builds a `sqlite+aiosqlite://` engine whenever `backend="sqlite"` is
  selected. A dev-group dependency is absent from every non-dev install, so that path raised
  `ModuleNotFoundError: No module named 'aiosqlite'`.

  The first attempt put it in the `plato` extra, which was the wrong home twice over. The backend is
  chosen by `FabricConfig.db_backend` -- core SDK config read from `JAPES_DB_BACKEND` /
  `JAZZX_DB_BACKEND`, nothing to do with hosting -- so a plain `pip install japes` could select
  `"sqlite"` and still break. And extras are not installed by a bare `poetry install`, which
  `docs/LOCAL_TESTING.md` documents, so the suite's own sqlite tests would have errored rather than
  skipped: the comment claiming they "skip w/o aiosqlite" described a guard that does not exist.

  Core is the honest placement, and cheap: 55 KB, no runtime dependencies of its own. Verified on a
  plain install with no extras at all -- `JAPES_DB_BACKEND=sqlite` resolves and a session opens,
  while `alembic` correctly stays absent as an extras-gated dependency. The lock diff is one field,
  `optional = true` to `false`. The image guard names `aiosqlite` too, since it is the one core
  dependency nothing on the eager import path pulls.

- **The Plato image shipped empty, and the build reported success.** The container died on
  `import pydantic` at `jazzx_sdk/models.py:30`, a core dependency, which meant nothing at all had
  installed rather than an extra being missed.

  Three faults, compounding. `pyproject.toml` declares `jazzx-eval-contracts` as a *path*
  dependency and `README.md` as the readme, but the builder stage copied only `pyproject.toml` and
  `poetry.lock`, so `poetry install` failed with `Path /build/jazzx_eval_contracts ... does not
  exist`. The install line then ended `&& git config --unset ... || true`, and since `&&` and `||`
  associate left at equal precedence that binds to the whole chain: a failed install short-circuits
  to `true` and the RUN exits 0. And the stage boundary copies `site-packages` whether or not
  anything landed in it, so the empty result was invisible until deploy.

  A fourth fault sat behind those, and the first pass at this missed it: `jazzx-eval-contracts` is
  declared `develop = true`, so poetry installs it *editable*. site-packages receives a `.pth`
  holding the absolute builder path `/build/jazzx_eval_contracts`, never a copy of the package, and
  the runtime stage copies site-packages without that directory. A `.pth` naming a missing directory
  is ignored in silence, so the build would have gone green and the image still could not import the
  package -- reached through `EvalServiceFeedbackSink` behind `POST /v1/feedback`, among others. The
  source is now copied into `/app`, but not the way the neighbouring copies work, and the first
  attempt at this got that wrong too: `jazzx_sdk`, `common` and `plato` are directories that *are*
  packages, while `jazzx_eval_contracts/` is a project root holding `pyproject.toml`, `tests/`,
  `scripts/` and the package one level down. Copying the root puts an `__init__.py`-less directory
  on `PYTHONPATH`, where `import jazzx_eval_contracts` quietly succeeds as an empty namespace
  package while every submodule import fails. The builder stage wants the root, because poetry reads
  its `pyproject.toml`; the runtime stage wants the package. The two paths are deliberately
  different.

  That asymmetry also disarmed the check: a bare `import jazzx_eval_contracts` passes in exactly the
  broken state, so the assertion imports `jazzx_eval_contracts.feedback` instead.

  So: the directory and README are copied into the builder, the contracts source into the runtime
  stage, the `|| true` is braced to cover only the cleanup, and the runtime stage asserts the five
  imports that each stand for one way this can break, plus `jazzx_sdk.evaluation.feedback_sink`,
  which is lazy and therefore invisible to a bare `import jazzx_sdk`.

  The same faults were in `examples/document_analyzer/Dockerfile` and
  `examples/basic/Dockerfile.sample`, which build from the repo root against the same manifest;
  both are fixed rather than left to fail the same way, and both gained the import check.

  `examples/basic/` is excluded by `.dockerignore`, so that one is a template nobody builds from
  here. It is fixed anyway: a sample is copied, and a broken sample propagates.

  Verified without a daemon: `poetry check --lock` passes on the fixed builder context and still
  reports both errors on the old one; the braced form exits 1 on a failed install while still
  tolerating a failed cleanup; an editable install's `.pth` was shown to hold an absolute source
  path and to raise `ModuleNotFoundError` once that directory is moved away; the new assertion fails
  on exactly that condition; and each `RUN python -c` payload is reassembled the way Docker joins
  continuation lines and parsed with `ast.parse`, which is what catches a doubled backslash making
  the guard-rail line itself a syntax error.

- **MLflow moved behind a backend boundary, and the SDK's public surface is now the abstractions
  only.** The four abstract base classes already existed -- `RunTracer`, `TraceSource`,
  `AgentTraceHooks`, `EvaluationReporter`, `ExperimentStore` -- but their mlflow implementations sat
  beside them, in three cases inside the same file. `run_tracer.py` was the clearest: 383 lines of
  which the ABC was about forty.

  Implementations now live in `observability/backends/mlflow/` (tracer, trace source, hooks,
  runtime, env) and `evaluation/backends/mlflow/` (reporter, experiment store and its bridge).
  `MlflowTracer`, `MlflowTraceSource` and `MlflowTraceHooks` have left `jazzx_sdk.__all__`, and
  `MlflowExperimentStore` has left `evaluation`'s: a backend is reached at its own path or built by
  `resolve_tracer`, never exported as though it were the interface.

  **Two directories, not one, and the tier contract is what determined that.** The first attempt put
  every mlflow file under `observability/backends/`, and the contract broke: `evaluation` sits above
  `observability`, so a class implementing `EvaluationReporter` cannot live below it without
  importing upward. A backend belongs with the abstraction it implements, which is a better rule
  than "all mlflow code in one place" and would not have been obvious without the check.

  **`AgentTraceHooks` turned out to be an abstraction living in the mlflow file.** The assessment
  that preceded this work recorded `agent_hooks.py` as 319 lines with "no abstraction above it" --
  wrong. It contains an ABC (needing only openai-agents) *and* the mlflow subclass, coupled through
  a factory call rather than an import, so they separated cleanly. The base class no longer sits
  behind an optional dependency it does not use.

  A fourth contract now enforces the boundary: nothing may import a backend at module scope, with
  one registered exemption for `resolve_tracer`, the factory whose job is choosing one. That
  exemption is explicit because import-linter counts a function-level import like any other --
  which is the better outcome, since any *other* module reaching for a backend now fails even if it
  does so lazily. Verified by adding such an import and watching it break.

  **Two follow-up fixes, both found in review of the above.** The lazy `AgentTraceHooks` entry was
  retargeted at `backends/mlflow/hooks.py`, which serves only `MlflowTraceHooks`, so an export that
  stayed listed in `__all__` stopped resolving -- `from jazzx_sdk import AgentTraceHooks` raised, and
  the whole suite passed, because the surface test compares name *sets*. `test_every_exported_name_
  actually_resolves` now gets every name in `__all__` on all three packages.

  And the boundary the contract names had a crossing it structurally cannot see:
  `observability/__init__.py` re-exported three helpers from `backends/mlflow/env.py` at module
  scope. An import-linter `forbidden` contract skips any pair whose forbidden module descends from
  the source, so `observability -> observability.backends.**` reports KEPT however it is listed
  (measured: the edge is in the grimp graph and the contract still passes). The crossing is now
  gone -- those three resolve lazily, like `AgentTraceHooks` -- and `test_no_backend_on_the_eager_
  path` asserts in a subprocess that no backend module reaches `sys.modules` on a bare package
  import. The contract was renamed to `no abstraction imports a backend at module scope`, which is
  what it actually checks. Both tests were confirmed to fail against the defects they describe.

  `RunContext` moved with the mlflow half rather than staying in `span_mapping.py`. It is a handle
  whose purpose is carrying an `MlflowClient`, so keeping it in the module that advertises importing
  no mlflow was the same mismatch the split existed to fix, and its callers use it alongside
  `log_artifact_with_retry`. Nothing in japes constructs one yet: it and `log_artifact_with_retry`
  are two thirds of macer's `utils/run.py` trio, ported for the SDK consolidation, and the
  `create_run` factory is still outstanding.

  `observability/mlflow_bridge.py` is gone, split rather than renamed. The name was the visible
  problem and the mixed contents were the real one: `spans_to_canonical_trace` and its helpers work
  on anything span-shaped and import no mlflow, but `safe_link_traces_to_run`,
  `safe_update_current_trace`, `log_artifact_with_retry` and `mlflow_run_to_canonical_trace` all
  `import mlflow` in their bodies. One file, both sides of the boundary the rest of this change
  draws. The generic half is now `observability/span_mapping.py`, next to the abstractions it
  serves; the mlflow half is `observability/backends/mlflow/bridge.py`. `trace_source.py`'s
  docstring had asserted the whole file imported no mlflow, which was true of the part it used and
  false of the file.

  Part of the motivation is version containment rather than tidiness: mlflow's constraints have
  pinned unrelated packages before, and it currently carries a high-severity advisory with no fixed
  release. Confined to two directories the SDK never imports eagerly, that is a contained problem.

  Consumers: k9 imports `RunTracer`/`RunHandle`/`SpanHandle` and ships its own `PrintingTracer` on
  that base -- untouched by this, and standing proof the seam works. jaci imported `MlflowReporter`
  by its old path; that one line is fixed alongside. No other repository referenced any of it.

- **LiteLLM is gone, and `openai-agents` moves 0.20 -> 0.22 with `openai` 2.x -> 3.3.** One optional
  dependency was setting the floor for the whole SDK: every litellm release through 1.98.0 pinned
  `openai<3.0.0`, while openai-agents 0.21+ requires `openai>=3.0.0`. Removing it was blocked on
  capability, not on will, and the three things it still did have each been replaced first:

  - Claude as an Agents-SDK model -> `AnthropicNativeModel`, including the `cache_control` injection
    that was the litellm-backed model's whole reason for existing.
  - Bare Gemini -> `GeminiNativeModel`.
  - **Gemini on Vertex AI** -> `build_genai_client`, the last capability only the passthrough had.

  Deleted: `jazzx_sdk/agents/anthropic_model.py`, its lazy export from `jazzx_sdk.agents`, the
  `litellm/<provider>/<model>` dispatch in `resolve_model`, `_litellm_model`,
  `_litellm_anthropic_name`, the `JAPES_ANTHROPIC_LITELLM` escape hatch, and the `litellm` extra.

  **A stale `litellm/` prefix still resolves.** Names recorded while that was the route carry the
  qualifier, and a stored name should not fail on a prefix that has merely stopped meaning
  something -- it is stripped and the provider inferred from what is left. The prefix also stays in
  `model_identity`'s strip list for the same reason. What is gone is any *dispatch* on it: a
  provider japes has no adapter for is now unreachable through `resolve_model`, and writing an
  adapter is the route rather than a passthrough that constrains every other dependency.

  Four tests went with the deleted module. Their coverage did not: cache_control injection and its
  empty-block skip are the native adapter's now and are tested there, which a comment in
  `test_agent_models.py` records so the deletion does not read as lost coverage. One test asserted
  the passthrough still existed by grepping `resolve_model`'s source; it now asserts the opposite
  behaviourally -- a `litellm/vertex_ai/...` name resolving to `GeminiNativeModel` with the
  qualifier stripped -- because the source form also matched the docstring explaining the
  tolerance, and would have failed for the wrong reason.

  Consumers: jaci pinned `japes[litellm]` and is fixed separately (it imports no litellm; its
  Anthropic eval harness passes a model *name* and lets `resolve_model` choose, which has been the
  native path since that adapter landed). macer and eval-service use litellm as their own direct
  dependency, unrelated to this extra. k9, juno, jazzx-assistant, assistant, kernel: no usage.

- **Gemini reaches Vertex AI natively, which was the last thing only LiteLLM could do.** Vertex
  takes a Google Cloud project and location and authenticates with ambient credentials, none of
  which a bare model name can express -- so `litellm/vertex_ai/<model>` was the only route, and that
  one passthrough kept the whole SDK pinned at `openai-agents` 0.20.

  `build_genai_client` is now the single place a `google-genai` client is constructed, taking
  `vertexai`/`project`/`location`. Both tiers use it -- the LLM tier's single-shot `run` and the
  agent tier's tool loop each had their own `Client(api_key=...)` line, and a second one is how the
  two come to disagree about which account a request bills.

  Vertex turns on when asked, or when `GOOGLE_GENAI_USE_VERTEXAI` is set *and* a project resolves.
  That is the variable `google-genai` reads itself, so a deployment already configured for Vertex
  needs no japes-specific setting. The flag alone is deliberately not enough: Vertex without a
  project cannot work, and switching paths on it would turn a missing setting into a confusing
  credentials error. Asking for Vertex explicitly with no project is refused outright rather than
  falling back to the api-key path, which would silently bill a different account.

  `is_available()` no longer means "has an api key". On Vertex there is no key, and reporting a
  correctly configured deployment as unavailable is worse than the check being slightly longer.

  Two things the tier contract caught while this was written, both worth recording. Importing
  `jazzx_sdk.config` -- the package -- pulls `config.settings`, which imports `client_layer` and
  through it most of the SDK; a two-line env helper should not drag the runtime facade in behind
  it, so the import is `jazzx_sdk.config.envvars` directly. And the first draft added Vertex to the
  agent-tier provider alone, leaving the LLM tier on its own client: the contract did not object to
  that, but the duplication is the shape CLAUDE.md's symmetry rule names, which is why the builder
  is shared rather than copied.

- **The native Anthropic model asks for prompt caching, not just reports it.** `AnthropicNativeModel`
  read Anthropic's cache counts back into `InputTokensDetails` but never injected a `cache_control`
  directive, so every Claude turn on the native path paid full price while the usage fields dutifully
  reported zero cached tokens. The LiteLLM-backed `AnthropicModel` it replaces did inject them --
  that was the reason it existed, in its own words, "(LiteLLM doesn't do this for you)".

  The failure mode is why this mattered: nothing errors. A request without breakpoints succeeds,
  returns the right answer, and reports a cache hit rate of zero. The bill is the only signal.

  Breakpoints are spent as the LiteLLM path spent them -- the system prompt, the message before each
  of the last two user turns, and the final message. Everything *before* a breakpoint becomes
  eligible for reuse, so they sit behind the parts that do not change between turns. Anthropic
  allows four; a test asserts we never exceed that, since going over is a 400 rather than a
  degradation.

  Empty blocks are skipped, because Anthropic rejects `cache_control` on empty text and a breakpoint
  spent there would buy a 400 in exchange for saving nothing. Caller blocks are copied rather than
  marked in place.

  One existing test changed shape: `system` now reaches the API as a cached text block rather than a
  bare string, because the directive attaches to a block and that is the only form Anthropic accepts
  it on. The test's purpose -- parity between the streaming and blocking paths -- is untouched; both
  still go through one `_request` builder.

  This is a prerequisite for dropping the `litellm` extra rather than part of it. Verified
  separately: with litellm's declaration removed, `openai-agents` resolves to 0.22.0 and `openai` to
  3.3.0, and the whole suite passes on them -- so litellm is indeed the wall holding the SDK at
  0.20, and the only thing it was still doing for us is the caching now ported here.

- **The mock Knowledge Hub validates updates, not just creates.** `MockKnowledgeHubClient` called
  `_validate_entity` from `create_entity` and nowhere else, so a mock-backed test could write a
  valid entity and then update it into a shape its ontology forbids with nothing objecting. Real KH
  validates both (`update_entity_with_validation`), which made the mock weaker than the thing it
  stands in for -- the one property a mock must not have.

  Validation is against the **effective** ontology and entity type: a partial update may change
  either, and checking the new value against the stored pair would validate it against the schema it
  is leaving rather than the one it is joining. Real KH shipped that exact bug and fixed it in its
  own `93ea215` ("json_value validated against the pre-update schema -> now validated against the
  effective ontology_id/entity_type"), so a mock repeating it would be wrong the same way twice.

  It runs before the write, so a rejected update leaves the stored entity untouched. Raising after
  mutating would be worse than not validating: the store would hold a value the schema forbids, and
  the next read would look authoritative.

  A name-only update is not re-validated. Nothing the schema describes has changed, and checking
  anyway would surface invalidity predating the call, reported as a failure of the rename.

  A metadata-only update is not re-validated either. That case is the seam between two changes that
  landed separately -- write provenance added `metadata` to this method, validation was added around
  `json_value` -- and metadata is the provenance envelope rather than part of the value the ontology
  describes. Stamping who touched an entity must not fail on invalidity predating the stamp.

  Found by surveying sibling repositories: jazzx-assistant added the same validation to its own
  hand-rolled mock KH on 2026-09-02. That japes ships a reusable mock KH precisely so packs stop
  hand-rolling one, and a consuming repo has its own anyway, is a separate question worth asking
  them -- recorded in `SIBLING_SURVEY_2026-09-02.md`.

- **`settings.py` and `env.py` became `config/`.** One concern read from two directions: `env()`
  resolves a `JAPES_`-preferred variable name with a legacy fallback, and `JAPESSettings` is the
  typed surface built on that same convention -- which `settings.py`'s own docstring already pointed
  at. Neither had a consumer outside this repository, so nothing needed a shim.

  `env.py` is `config/envvars.py` rather than `config/env.py`, and the reason is worth recording
  because the first attempt shipped the bug: re-exporting the `env()` function from the package
  `__init__` **shadows a submodule of the same name**. `jazzx_sdk.config.env` then resolves to the
  function, and three tests that `monkeypatch.setattr` against
  `jazzx_sdk.config.env.deployed_posture` failed with "'function' object has no attribute". Renaming
  the module removes the collision rather than working around it.

- **The shared-contracts grouping was proposed here and then dropped, because the data said no.**
  `models.py`, `events_domain.py` and `failures.py` are each bottom-tier and widely imported, which
  is what made them look like a set. Their consumers are nearly disjoint: `models` reaches 10
  packages, all transport and runtime (`server`, `channels`, `clients`, `queue`, `observability`);
  `events_domain` reaches 2 (`automation`, `statemachine`); `failures` reaches 7 and none of them
  overlap the first group meaningfully (`agents`, `llm`, `tools`, `evaluation`). A package holding
  all three would have no coherent audience, which is structure for its own sake.

  `contracts.py` does not belong with them either, for the opposite reason: it imports *upward*,
  from `fabric.canonical` and `evaluation`, because it is the curated Tier-1 import surface a
  library consumer opens -- a facade over definitions, not a definition. Grouping a top-of-stack
  re-export with bottom-of-stack primitives would have been flagged by the tier contract.

- **Three root-level clusters became packages: `queue/`, `runtime/`, `concurrency/`.** Seven modules
  that sat as peers of `fabric` and `agents` while being one tier's worth of one concern each.
  `queue_processor.py`, `queue_execution.py` and `queue_execution_db.py` are now
  `queue/processor.py`, `queue/execution.py` and `queue/execution_db.py`; `launcher.py` joins
  `runtime/`; `concurrency_guard.py` joins `concurrency/`.

  Two of the three cost nothing to import. `concurrency.py` and `runtime.py` became the packages'
  `__init__.py`, so every `from jazzx_sdk.concurrency import ...` and `from jazzx_sdk.runtime
  import ...` still resolves -- and `concurrency` has fifteen importers.

  The queue move does break one import path, deliberately. Four repositories -- jaci, k9,
  jazzx-assistant and macer -- do `from jazzx_sdk.queue_processor import QueueSettings`, reaching
  past the public API into a private module path. `QueueSettings` is already exported from
  `jazzx_sdk` itself and listed in `__all__`, so the fix on each side is `from jazzx_sdk import
  QueueSettings`: one line per repository, and an import that will not break the next time a module
  moves. A shim would have preserved the habit that made a rename breaking in the first place.

  No change to the debt list -- grouping alters shape, not direction, and it would be misleading to
  report otherwise. Top-level entries went from 55 to 53, which is the honest measure of what
  grouping alone buys.

- **Two server-tier route modules moved into `server/`, where their imports already pointed.**
  `observability/trace_routes.py` and `runs/server.py` both import `server.governed_http`: route
  factories living in core packages. Their own docstrings said as much -- one described itself as
  "consistent with the rest of japes' server tier" -- so the code had known for a while.

  They are now `server/trace_routes.py` and `server/run_routes.py` (renamed, because
  `server/server.py` names nothing). No shim: a survey across japes, jaci, k9, jazzx-assistant,
  juno, macer, assistant and eval-service found them referenced only by japes' own two tests.
  Neither was ever exported from its package `__init__`, which is why nothing depended on them.

  The debt count went 16 -> 17, and the direction is worth explaining. `runs -> server` cleared,
  which is -1. `observability` was never in the layer list at all, so its inversion was invisible to
  the contract -- and an unpoliced module is exactly where the next one hides. Bringing it under the
  contract exposed two pre-existing edges (`observability -> agents`, `identity -> observability`),
  which is +2. The longer list is the stronger one: one real inversion is gone for good, and the
  package that hid it is now policed.

  Left alone deliberately: `identity.with_trace_context` imports `observability.trace_context`, and
  its own docstring says trace propagation is orthogonal to identity. Moving it would relocate the
  edge rather than remove it, since `kernel_request_headers` in the same module composes with it.

- **The tier debt list is down from 29 pairs to 16, with no code moved.** All of it came from making
  the contract describe the code more accurately rather than from loosening it -- the ratchet still
  catches a new cross-tier edge, verified again by adding `fabric -> server` and watching it break.

  `exclude_type_checking_imports = True` accounts for 7 of the 13. Type-only imports are not runtime
  dependencies, and counting them had one `if TYPE_CHECKING` annotation in `handlers.py` reporting
  the SDK's identity primitives as dependents of llm, agents, mcp and fabric -- through
  `ClientLayer`, which they never touch at runtime.

  The other 6 were the layer order being wrong, in three ways worth naming because each was a
  mistaken assumption about the architecture rather than a defect:

  - `streaming` is a transport primitive agents publish *to*, not a host sitting above them.
  - `statemachine` consults `authority`, so it cannot sit below it.
  - `pack` and `manifest` are configuration nothing lower reads, so they belong near the top.
    Moving them cleared five pairs and introduced three (`fabric -> manifest`,
    `authority -> manifest`, `pipelines -> pack`), which is where ordering stops paying.

  What remains needs code, not a different sort. Two are files in the wrong package -- `runs/server.py`
  and `observability/trace_routes.py` both import `server.governed_http`, being server-tier route
  modules living in core packages. One is a client reaching into runtime internals
  (`clients/japes_queue_client.py` importing `queue_processor._build_provider_pair` and
  `_parse_message`). The rest are shared *types* sitting inside higher packages -- `modes.schemas`
  read by `tools`, `finance.vocabulary` read by `expressions` -- where the fix is to move the type,
  and each move is a breaking import for consumers.

- **Caller identity moved out of `handlers.py` into `jazzx_sdk.identity`, with no shim.**
  `handlers.py` held two unrelated things: the handler contract a consumer implements
  (`Handler`, `BaseHandler`, `HandlerContext`, `job_id_for`) and the platform's identity
  primitives -- security context, inbound-header capture, `CallerIdentity`, and the outbound header
  set that forwards them. Fourteen packages imported it, more than any module here except `fabric`
  and `concurrency`, so under a name that reads as message-handling runtime nothing said whether a
  core module depending on it was reaching upward or sideways.

  A correction to the earlier note in this file: `handlers.py` was described as containing no
  handlers. It does -- `HandlerContext` alone is imported 23 times by consumer repos. The first
  reading covered only the file's first 300 lines. It was never misnamed; it was two concerns
  sharing a file, which makes the fix a split rather than a rename and far cheaper.

  **No shim, because the survey said none was needed.** Consumers were counted before anything
  moved: juno and macer import `jazzx_sdk.handlers` not at all; jaci (16 files), k9 (5) and
  jazzx-assistant (2) import `HandlerContext` and `BaseHandler`, which have not moved. Exactly one
  external import touches the identity half -- `default_request_headers`, in one jazzx-assistant
  test -- so a compatibility layer would have existed for a single line in a single test.

  The halves turned out to share no code at all, only a file: the one apparent crossing,
  `security_context`, is a `HandlerContext` *field* carrying the inbound value, not a call into
  that machinery. So neither module imports the other. 22 files inside this repo were repointed,
  including four tests that reached for the module object rather than importing names.

  `identity` joins the tier contract in the bottom layer. The debt list went from 30 pairs to 29 --
  the split was about making the tiers nameable, not about breaking the cycle, and it is honest that
  it barely moved that number.

- **The SDK's tiers are declared and enforced, and the measurement says they are not tiers yet.**
  `.importlinter` guarded only package boundaries (`jazzx_sdk` never imports `plato`, `common`
  imports neither). Nothing constrained direction *inside* `jazzx_sdk`, so the core/queue/server
  split lived in prose and a lower tier importing its host was a review-time question at best.

  What the measurement found, before any contract was written:

  - **26 of the SDK's top-level modules form a single import cycle** -- `fabric`, `agents`,
    `server`, `clients`, `conductor`, `modes`, `llm`, `tools`, `handlers` and 17 more are all
    mutually reachable. No ordering of layers can pass outright against that.
  - **39% of cross-package imports (241 of 605) are deferred inside functions.** That is what keeps
    the cycle from failing at import time, and why it went unseen.
  - `handlers.py` contains no handlers. It is security context, header propagation and
    `CallerIdentity` -- the third most depended-upon module in the SDK (14 importers, behind
    `fabric` at 23 and `concurrency` at 15) under a name that says nothing about which tier it is.
  - `observability/trace_routes.py` imports `server.governed_http`: server-tier code inside a core
    package.

  The contract that landed is a **ratchet**, not a clean bill of health: seven tiers ordered by the
  measured direction of dependencies rather than by intent, and 30 wrong-way pairs registered as a
  debt list that may only shrink. It passes today and any *new* cross-tier edge fails CI -- verified
  by adding a `fabric -> server` import and watching it break, then removing it. The ordering itself
  was iterated against the graph: the first attempt (written from the intended architecture) had 32
  violating pairs, and correcting it to the real direction cut that to 27. `mcp` moved into the
  `agents` tier for the same reason -- it exposes agent capabilities, so it is a peer, not a layer
  below.

  One registered edge is explicitly not debt: `handlers -> client_layer` exists only under
  `if TYPE_CHECKING`, for a single annotation. import-linter reads the AST and counts it, and
  through it everything `ClientLayer` touches -- which would report the SDK's identity primitives as
  depending on llm, agents, mcp and fabric, which at runtime they do not.

  Known limitation, worth stating: the debt entries are per top-level *pair*, so a new import
  between two modules already on the list is not caught. Tightening that means shrinking the list,
  which is the point.

- **Two suite warnings fixed, one left standing with its cause named.** `plato/alembic.ini` now
  declares `path_separator = os` instead of inheriting the legacy split on spaces, commas and
  colons -- which alembic warns is going away, and which would silently fragment the repo-root path
  under a directory containing any of those characters. `test_transaction_context.py` reads
  `model_fields` off the model class rather than an instance, deprecated in pydantic 2.11 and gone
  in v3; it was the only instance-level use in the repo.

- **`DbStore.dispose()`, and the suite stops leaking sqlite worker threads.** `DbStore` opened an
  `aiosqlite` engine lazily and offered no way to close it, so each of the ~50 stores the suite
  builds left a worker thread bound to the loop it was created under. When such a store was
  collected -- often several files later -- the thread woke to a closed loop and raised, and pytest
  reported it against whichever test happened to be running. No file emitted it alone, which is
  what made it hard to place.

  `dispose()` closes only an engine the store opened itself: a `common.core.db` factory or an
  injected sessionmaker belongs to whoever built it, and closing those from here would drop
  connections other callers still hold. It is idempotent and a no-op on a store that never resolved
  an engine.

  A disposed store refuses reuse rather than reopening. Reopening reads as harmless and is not: on
  the `:memory:` default a second engine is a different, empty database, so the next query fails as
  `no such table` with nothing naming the dispose that caused it.

  Tests get it through an autouse fixture that tracks instances, rather than 49 inline call sites
  opting in one by one -- none of them sit in a fixture, and one written tomorrow would not opt in.
  The tracking holds **strong** references: a store that falls out of scope mid-test is exactly the
  one that leaks, and a `WeakSet` (tried first) let it be collected before teardown saw it, which is
  why the first attempt changed nothing. Verified causally: 0 warnings with the fixture, 10 with it
  switched off.

- **A gateway without routing no longer breaks model resolution.** `resolve_agent_model_name` read
  `gateway.task_routing` directly, while the branch above it already treated "no gateway" as "no
  routing". `gateway` is duck-typed, so any stand-in that is not an `LLMManager` -- a scripted
  manager wired into a local host, say -- raised `AttributeError` from inside model resolution and
  surfaced as a 500 on the first agentic turn. It now reads through `getattr` and falls through to
  the default, which is what "no routing" already meant one line earlier.

- **`scripts/plato_wiring.py`: Plato runs on a workstation.** The manifest's `allowed_skills` is
  derived from the profile's own `skills/*.yaml`, for the same reason the stub tool catalog is
  derived: a hardcoded mirror of a sibling checkout drifts silently when a skill is added, and
  fails the manifest write with a bare `ValueError` when one is renamed.

  The stubs are real `FunctionTool` objects, not bare callables. `Agent(tools=[...])` accepts a
  plain function and stores it unwrapped, so the mistake survives construction and every turn that
  never reaches a skill; it fails later inside `Converter.tool_to_openai` with "Hosted tools are not
  supported ... Got tool type: `<class 'function'>`". Verified at that exact call: a plain callable
  raises there, and all 11 stubs now serialise. `@function_tool` derives its schema from a
  signature, which a stub generated per tool name has none of, so the schema is declared explicitly
  and left non-strict -- the real skills call these with argument sets this file cannot know, and a
  strict schema would reject the call rather than stub it.

  `_assemble_pack` refuses to `rmtree` a directory it did not create, checked by a marker file it
  writes. `PLATO_LOCAL_CACHE` is a path a person types, and the unconditional delete would have
  taken whatever they pointed it at, and the marker is written *before* the copy so a boot
  interrupted partway leaves a directory the next boot still recognises as its own.

  The manifest write runs under a throwaway `asyncio.run` loop, opening the engine under a loop
  that closes immediately -- left alone deliberately, because plato does the same thing to the same
  store moments later, when `check_schema_or_report` runs `assert_schema_current(db)` before
  uvicorn starts. An earlier revision seeded through a separate short-lived store to keep the
  runtime's engine pristine; it bought nothing for that reason and is gone. File-backed sqlite
  serves correctly afterwards, verified against a running server.

  Plato ships no default `PLATO_WIRING`
  on purpose -- a container that boots into a stub looks healthy to an orchestrator -- which is
  right for a deployment and a wall for anyone who wants to watch it serve. This supplies one:
  sqlite on disk, `ScriptedLLM`, and stub tools derived from whatever the profile's skills declare
  rather than a fixed list, so a tool added to the profile is covered instead of breaking the boot.

  The database is built by running the real alembic tree, not `create_all`: Plato refuses a
  database carrying no revision stamp, and satisfying that check any other way would be lying to
  it. A local boot therefore exercises the migrations the way a deployment does.

  Tracked in `scripts/` rather than gitignored under `scripts/local/`, because the wall is not
  workstation-specific -- every clone meets it -- and `scripts/` is outside `packages`, so nothing
  reaches a consumer's install.

  **Stated plainly because the wiring makes it look free: a chat turn calls the real OpenAI API.**
  `ScriptedLLM` answers the scope guardrail and the non-agentic path, but this profile's turns take
  the agentic path, which builds an OpenAI agent directly rather than going through `llm_manager`.
  Measured against a live server: sessions, `/health` and `/v1/info` need no key; one turn was ~7k
  input tokens on `OPENAI_API_KEY`, and with no key it fails outright rather than falling back to
  the script. Boot prints which state you are in.

- **A guard so CI's extras cannot silently fall behind again.** `tests/test_ci_extras_coverage.py`
  asserts every extra `pyproject.toml` declares is either installed by the workflow or named in an
  `EXCLUDED` map with the reason it is safe to leave out. Adding an extra now forces that decision
  rather than defaulting to silence, and three companion checks keep the map honest: nothing may be
  both installed and excluded, `EXCLUDED` may not name an extra that no longer exists, and the
  gitignored pre-push hook's `CI_EXTRAS` must match the workflow (skipped where the hook is absent).

  Deliberately not an import scan. The `gemini` failure came from a *lazy* import inside
  `jazzx_sdk.agents.gemini_provider`, not from anything the test files import at module level, so no
  static scan of `tests/` could have seen it -- and reproducing it needs a CI-shaped install, which
  a test running inside the developer's own environment cannot conjure. The list itself is what is
  checkable exactly and cheaply.

  `greenlet` gets its own check, because it is a main-group dependency with a platform marker
  rather than an extra: nothing in the extras logic can see it, and deleting its declaration would
  look harmless on any machine that already carries the package. That check evaluates the marker
  against an `arm64` environment rather than looking for the string, so an unconditional
  `greenlet = ">=3.0.0"` -- which covers Apple Silicon and more besides -- passes. A guard that
  reddened on the safer declaration is one somebody deletes.

  The `bpmn` exclusion is the one reason mechanically checkable from data the file already parses,
  so it is checked: `extras["bpmn"] <= extras["plato"]`. If `bpmn` ever gains a package `plato`
  lacks, "adds nothing" stops being true, and an exclusion that quietly became wrong is worse than
  one never written down.

  Each was verified by reintroducing the drift it targets and confirming it fails: dropping `plato`
  from the workflow, pointing the hook at a stale set, marking an installed extra as excluded,
  naming an extra that does not exist, deleting greenlet outright, and narrowing its marker to
  SQLAlchemy's own platform list -- plus the converse, that the unconditional declaration passes.

  The workflow lookup anchors on the `run:` line rather than the first `--extras` in the file --
  roughly fifty lines of prose about extras sit above it, and an example command quoted there would
  otherwise be compared instead of the real one, with every assertion still green.

- **`greenlet` is declared for Apple Silicon, which SQLAlchemy's own marker misses.** SQLAlchemy's
  async layer requires greenlet and declares it, but its marker lists `aarch64` -- Linux's name for
  the chip -- and not `arm64`, macOS's name for the same chip. A fresh `poetry install` on Apple
  Silicon therefore omits it, and 178 tests die with `ValueError: the greenlet library is required`.
  Nothing warns; the package simply is not there.

  It only surfaces on a rebuild. Any environment created before this carries greenlet from some
  earlier install and looks healthy, which is why a working machine is not evidence.

  Declared for `arm64`/`ARM64` only -- the spellings SQLAlchemy's marker misses -- so no platform
  resolves it twice; the lock change is two lines, appending those two values to the existing
  marker. Verified by uninstalling greenlet, confirming it was gone, and re-running `poetry install`:
  it comes back from the lock. Removable once SQLAlchemy's own marker covers macOS.

- **CI installs the `plato` extra, so the BPMN resolver tests run and `alembic` stops being
  accidental.** `common/refs/extract.py` imports `defusedxml`, which only the `bpmn` and `plato`
  extras supply, so all 22 tests in `test_bpmn_resolver.py` failed at import in a CI-shaped
  install -- the same shape as the `gemini` gap: a branch adds tests needing an extra, CI's list
  does not move with it. Found by rebuilding the local venv from scratch, which is the only way it
  surfaces; an older environment carries the package from some earlier install and looks fine.

  `plato` rather than the narrower `bpmn` because it also declares **`alembic`**, which nothing
  else in CI's list does. Plato's migration tests were getting it transitively from `mlflow`, so
  dropping the mlflow extra would have broken migration tests with nothing naming the connection.
  Verified rather than assumed: uninstalling both packages and re-running `poetry install` with
  this extras list brings back `alembic 1.18.4` and `defusedxml 0.7.1` from the list itself.

- **The Gemini provider tests run in CI instead of failing, and the ones that need no SDK keep
  running without it.** CI installed `mcp templating finance pptx mlflow` but not `gemini`, so
  `google.genai` was absent and tests died at the first lazy `from google.genai import types`.

  The SDK modules were already right -- they import `google.genai` inside the functions that need
  it, so importing `gemini_provider`/`gemini_native` costs nothing without the extra. Two changes
  sit on top of that:

  *CI installs the `gemini` extra.* One package, and the tests are offline (fake key, stubbed
  client). Without it, `GeminiProvider` and `GeminiNativeModel` -- both shipped and exported -- had
  no CI coverage at all. The extra lands *with* the marks rather than instead of them: before this,
  a CI without it failed outright, and marks alone would have turned that into a green run
  verifying nothing -- a skip reading as a pass, the failure the `mlflow` extra was added to fix.

  *The guard is a per-test marker, not a module-level `importorskip`.* Only 21 of the 31 tests build
  requests through `google.genai` types; the other 10 exercise `_usage`, `_output_items`,
  `resolve_model` and the `AgentExecutionService` registry and touch no Gemini SDK type. Skipping
  the file wholesale would have stopped those 10 running for anyone installed without the extra --
  turning tests that passed into tests that no longer run. Which 21 need it was determined by making
  `google.genai` unimportable and reading the failures, not by inspection.

  Verified in both installs: with the extra, 31 pass; without it, 10 pass and 21 skip with a stated
  reason. The lock is bumped in the same commit so CI tests what was verified: it pinned
  `google-genai` 2.8.0 while this work was done against a newer local install, which is exactly the
  gap that makes a local pass meaningless. `poetry update google-genai --lock` moved two packages --
  `google-genai` 2.8.0 -> 2.21.0 and its dependency `google-auth` 2.55.0 -> 2.57.0 -- and the 31
  tests were re-run against 2.21.0 rather than assumed compatible. The pre-push hook's `CI_EXTRAS` is updated in the same breath -- it had drifted when
  `mlflow` was added, and that drift is what let a local pass look like a CI pass.

- **The curator tests exercise the supported synthesis path, not the deprecated one.**
  `synthesize_bucket` has taken `agents=<AgentExecutionService>` since `llm=` was deprecated, but
  five tests still called it the old way, so every suite run carried five `DeprecationWarning`s.

  The warnings were the symptom; the problem was where the coverage sat. Everything substantive --
  applicability, feedback/attribution/evidence provenance, the red-teaming batch, draft persistence
  -- ran through the path scheduled for deletion, while `agents=` had a single test. When `llm=`
  goes, those tests would have gone with it and taken the coverage rather than moving it.

  Those five now use `agents=` through the existing `ReasoningAgent` monkeypatch seam (moved above
  the tests in `test_curator_synthesis.py`, with a local stub added to
  `test_learning_candidate_adapter.py`). The deprecated path keeps exactly one test, which asserts
  the warning fires via `pytest.deprecated_call()` -- so the shim stays covered until it is removed,
  and no warning leaks. Both files pass under `-W error::DeprecationWarning`. Suite warnings 20 -> 15.

- **The last pydantic v1-style `class Config` is gone.** `FabricConfig` still declared its settings
  through the inner class pydantic v2 deprecated and v3 removes, so every test run carried a
  `PydanticDeprecatedSince20` warning. It is now `model_config = ConfigDict(use_enum_values=True)`,
  and it was the only one left in `jazzx_sdk` -- every other model had already migrated.

  `use_enum_values` is carried across verbatim and noted in place, because what it changes is
  subtle: it alters the *stored* type, so `retrieval_mode` holds the string `"strict"` rather than
  `RetrievalMode.STRICT` and `model_dump()` emits a plain string. Comparisons are unaffected --
  `RetrievalMode` is a `str, Enum`, so `mode == RetrievalMode.STRICT` holds either way -- which is
  precisely the trap: dropping the setting would look harmless at every in-repo call site while
  changing the serialised shape for anything persisting or transmitting the config.

- **The open MLflow SSRF advisory is recorded where the floor is declared.**
  GHSA-h7x2-h6g9-p789 / CVE-2026-71211 (unvalidated `api_base` in MLflow's AI Gateway) has **no
  fixed release**: it covers `>=3.13.0,<=3.15.2` and 3.15.2 is the latest published version, so
  there is nothing to bump to, and dropping below 3.13 reinstates the webhook-delivery SSRF this
  floor was raised to close. It is also not reachable from japes, which uses only mlflow tracking
  (`MlflowClient`, entities, runs) and runs no gateway. Documented rather than silently carried, so
  the next person to see the alert does not re-derive the analysis.

- **The real-assistant test no longer hardcodes a workstation path.**
  `tests/test_plato_packs.py` pinned the `jazzx-assistant` profile to an absolute path under one
  developer's home directory, so on every other machine the skip read as "the sibling is absent"
  when the real reason was "you are not that person". It now resolves the sibling relative to this
  checkout -- the `<workspace>/japes`, `<workspace>/jazzx-assistant` layout every JazzX repo already
  uses, so the default needs no configuration -- with `JAPES_ASSISTANT_PROFILE_DIR` to override,
  matching the existing `JAPES_REAL_PACKS_DIR` convention. The skip reason now names the path it
  looked at and the variable that changes it.

- **Entity write provenance verified against the landed Knowledge Hub contract.** KH `93ea215`
  ("add metadata JSONB column") added an optional, free-form, client-owned `metadata` JSONB column
  on `entity`, exposed on `EntityCreate`/`EntityUpdate`/`EntityRead` under the wire name `metadata`.
  That confirms the key this client already wrote to, so `WRITE_METADATA_KEY` stops hedging about a
  spelling it had to guess. It still rides on `additional_properties` because japes' vendored
  `EntityCreate` predates the change; the serialised body is byte-identical to what a regenerated
  client produces, so regenerating `client-api` is a drop-in rather than a migration.

  **Updates merge, they do not replace** (KH's `_merge_metadata_on_update`): adding
  `updated_by_process_id` leaves `created_by_process_id` in place. The mock now merges on both
  update paths, and the docstring that claimed the opposite -- written when the contract was still
  unknown -- is corrected. Omitting the key leaves the column untouched; this client sends omission
  for an empty dict too, so KH's explicit-null "clear the column" case is deliberately not
  expressible, the safe default being to say nothing.

  The test that pinned the old behaviour reused a single metadata key, where merge and replace give
  identical results and the assertion proved nothing. It now uses distinct
  `created_by_process_id` / `updated_by_process_id` keys, covers a repeated update (the rerun case),
  and fails if the mock reverts to overwriting.

  **`update_entity_json` no longer takes `metadata` at all.** KH's json-patch endpoint accepts only
  `path`/`value`/`updates` plus the `x-user-id` header, and its body has no `metadata` field now or
  after client regeneration -- so the parameter was accepted and dropped on every call. An earlier
  revision of this work argued the opposite (that omitting it would make json-patch "the one write
  that records nothing"); checking the endpoint rather than reasoning by symmetry showed the
  parameter itself was the thing recording nothing. A parameter that silently discards what it is
  given is worse than its absence, so it is gone and the docstring says why.

  japes does not interpret the object's contents: the process-id keys belong to the caller, so KH
  and its callers can add keys without japes changing.
- **Fixed: a successful `create_triple` could not return.** `create_entity` returns the entity dict,
  or None when the write failed -- never an HTTP `Response`. `create_triple` checked
  `hasattr(response, "parsed")` and then read `response.status_code`, so a *successful* create
  failed the first probe, fell into the error branch, and raised `AttributeError: 'dict' object has
  no attribute 'status_code'`. The success path could not return at all. Nothing exercised it, so
  the bug sat behind a green suite; a failure now raises naming the triple that failed.

- **Fixed: the MCP `knowledge_hub_create_entity` tool reported failures as successes.** The same
  shape confusion, found by checking the family rather than the one instance. Both the `parsed` and
  `status_code` probes were False on failure, so the tool fell through to `json.dumps(None)` and
  answered the literal string `null` -- an ordinary successful result, as far as whatever drives the
  MCP session can tell. It now returns an error object naming the entity and collection.

  The existing test asserted `status_code == 201` against a Response-shaped `MagicMock` the real
  client never returns, so the fixture had encoded the bug rather than catching it. It now returns a
  dict, and a failure-path test was added. `test_policy_store.py` had the same drift -- a
  Response-shaped `create_entity` beside a dict-returning `create_collection` in one fixture -- so
  it exercised only the canonical store's tolerance arm and never the path production takes.

- **Fixed: `check_kh_connection.py` reported a successful entity create as skipped.** The same
  shape confusion in the script whose entire job is saying whether KH works. It read
  `response.parsed` off the dict `create_entity` returns, raising `AttributeError` straight into a
  bare `except` that logged "create_entity (person_result) skipped" -- so a healthy KH looked
  degraded, and the HTTP-status branch below it was unreachable.

  The canonical stores keep their `.parsed` arm deliberately: `KnowledgeHubLike.create_entity` is
  declared `-> Any`, so unlike the concrete client there is no contract there saying a Response
  cannot arrive, and the arm is tolerance across an untyped protocol boundary rather than dead code.

- **`KernelLLMModel` conformed to the protocol the runner actually calls — both halves were
  broken.** Found while using it as the template for the native Anthropic model, and broken in the
  same way twice: the adapter returned what read like a reply rather than what `agents.Model`
  defines.

  `get_response` built its `ModelResponse` from `content=` / `raw_response=`, neither of which is a
  field on it — required are `output`, `usage`, `response_id`. Every call raised a pydantic
  `ValidationError` before the runner ever saw a reply, so the Kernel path could not have been
  exercised through `Runner` at all. It now returns real output items and a real `Usage`, with a
  reply that reports no usage counting zero rather than `None`: the turn still happened, and a cost
  tracker summing `None` crashes where summing zero is a known gap.

  `stream_response` carried `# TODO`s and did `yield response` — a `ModelResponse` where a stream
  event belongs, so the type error surfaced somewhere downstream in a caller with no way to know
  why. Kernel's LLM API has no streaming endpoint, so it now runs the blocking call and emits the
  sequence the runner expects around the result: created, one text delta, completed. Not
  token-incremental, and the docstring says so — but a stream of the right shape, and an empty
  answer still opens and closes it rather than hanging a consumer waiting on `completed`.

- **An assertion now carries where it came from, typed: `Triple.coordinate`.**
  `source` and `section` are strings a reader has to re-parse and a machine cannot navigate --
  "page 4", "4" and "p.4" mean one place and none of them resolves back to it. The document stack
  already resolved a real `SourceCoordinate` per field (a Page/Section/Cell locator plus a content
  hash), and `emit_assertions` was flattening it to those two strings at the moment the assertion
  was built: the typed value existed and was discarded one layer before anything could use it. It
  is now carried, not re-derived. `source`/`section` are untouched, for display and for every
  caller already reading them; the field is optional because a merged triple has several origins
  and an asserted one may have no document at all.

  Verified across every hop that could quietly drop it -- `CaseGraph.build`, `model_dump` +
  revalidation, and `merge_subjects` -- because a flag is worth its weakest hop, and this is the
  boundary that ate `truncated` and then `cost_is_upper_bound`.

  **Where the chain stops is documented rather than left to be discovered.** The Knowledge Hub
  write contract (`create_triple`/`bulk_create_triples`) is a flat six-field projection, so
  persisting through `KGStore` drops the coordinate silently. Closing that needs the KH API to
  accept it -- a cross-service change, not one this layer can make alone -- so `add_triples` now
  says so in the place someone would be about to rely on it.

  `triple.py` called itself a leaf module with "no fabric/runtime imports"; it now imports
  `fabric.canonical.evidence`, which is stdlib-and-pydantic only. The docstring says what the one
  dependency is and that the real constraint -- no store, client or runtime import -- still holds,
  rather than leaving a claim that had quietly become false.

  In the policy pipeline this closes the deferral its own docstring recorded: `ClauseSegment` now
  resolves a `SectionLocator`-based coordinate (a clause's address is its section marker; the page
  it falls on is typesetting), an extracted rule cites its clause through `Rule.citations`, and a
  proposal carries the clause text as its `excerpt` -- because a reviewer ruling on an extracted
  rule needs the sentence it came from, which is the only question being asked of them.

- **`lint_pack` no longer reports a pass because it had nothing to check with.**
  A pack with no ontology got a `no_ontology` *warning* and an immediate return -- before its
  policies were counted or examined. So a pack whose every rule was unverifiable came back
  `ok=True, rules=0`: rules reported as *absent* rather than as *unchecked*, and a clean bill on a
  governance asset nobody had looked at.

  Found by pointing the machinery at a real pack rather than by reading it. jaci's `dscr-core` has
  41 authored eligibility rules and declares no ontology, and the report said `ok=True, rules=0`.
  It now counts what it was handed and raises `unverifiable_rules` as an **error**, so `ok` is
  False and the count is 41. A pack with no ontology *and* no policies stays a warning: nothing was
  asked of the lint, so nothing went unanswered.

  This is the failure `pipelines.policy_extract`'s own `lint_step` was written to avoid -- "a lint
  that passes because it had no vocabulary is the most misleading result available" -- present in
  the function underneath it. The pipeline guarded the case; the primitive did not.

- **A policy corpus becomes a pack's rules: `pipelines.policy_extract`, and `Proposal` learns to
  carry one.** The vocabulary pipeline turns a corpus into what a domain *can say*; this turns one
  into what a domain *requires*, and they are halves of one arc -- an extracted rule is only worth
  having if the vocabulary can supply what its condition reads.

  **`Proposal` was the blocker.** `kind` was `Literal["concept", "relationship"]`, so a rule could
  not enter the queue at all. Widening it to `"rule"` makes the whole existing lifecycle -- admission
  thresholds, the persisted `ProposalStore`, the review surface, the audit trail -- apply to rules
  unchanged, rather than growing a second curation system beside the first. `Rule` is
  forward-referenced and resolved by a `model_rebuild` at the end of policy.py: `fabric.canonical.
  policy` reaches `tools/__init__` -> `graph.triple` and back into `fabric.graph`, so a module-scope
  import is a real cycle (the same one that keeps `check.py` out of `graph/__init__`), and the
  pattern mirrors periods.py -> profiles.py.

  **A Proposal is deliberately not the answer for a case graph.** A proposal changes what is true
  for every future case; a case-level finding changes what is true for one. A loan's own facts are
  never proposed -- they are asserted with evidence or refused, and their machinery is
  `Assertion.confidence`/`admit`, `Contradiction`, `Coverage`, `Refusal`, and
  `agents.adjudication` where a person must decide. Accepting a proposal writes to a *shared*
  artifact, so admitting one case's income would change the pack on the strength of a single
  document. Evidence still flows case graph -> `FrequencyAccumulator` -> proposal; the accumulator
  crossing a threshold is the boundary, and it is what keeps the two apart. Written into the type's
  own docstring, because this is the distinction the next person will be tempted to collapse.

  **Lint is a stage, not a lint.** `lint_pack`'s `unreachable_input` check already catches the
  failure that matters -- it found `FCCR` reading `taxes` where the ontology declares `tax_expense`.
  An *extracted* rule is far likelier to invent a name than an authored one, so the periodic audit
  becomes a gate: the gap is reported on the run that proposed it, beside its evidence, while
  somebody is still looking. It reports and never repairs; binding `taxes` to `tax_expense` on a
  name-similarity guess would be a wrong auto-binding on a policy input, which is worse than an
  honest gap. Without a pack the stage reports nothing rather than passing -- a lint that "passes"
  because it had no vocabulary is the most misleading result available.

  **Conditions come out `natural_language`, deliberately.** A one-shot parse from prose into an
  `expression` is where extraction quietly invents thresholds. Promotion to a deterministic kind is
  a separate reviewable act once the thresholds are actually identified, so a half-understood rule
  degrades to "stated but stochastic" rather than to a confident wrong number. Extraction itself is
  a seam (`ObligationExtractor`) -- the pipeline owns the governance around it, which is the part
  that is the same whatever the extractor is. `ModalClauseExtractor` is a labelled floor for tests,
  and declares `reads=[]` rather than guessing field names it cannot identify.

  Segmentation is clause-level, not page-level: a rule's boundary is a section marker, and the page
  it falls on is an artifact of typesetting. Text with no markers comes back as one segment rather
  than none -- an unmarked policy is still a policy. "should" is not an obligation; admitting
  advisory language as a rule would overstate what the document requires.

- **The remaining three signature annotations that resolved nowhere.** `Path` (twice) and
  `DirectoryResult` in `agents/document/agent.py` -- the same defect as the five closed in 2.4.9,
  left with this release because the module carries the KG `emit_assertions` work.
  `DirectoryResult` joined the existing `document.schema` import rather than opening a second one
  from the same module.

- **An unpriced cost now says it is a ceiling: `cost_is_upper_bound` on both tiers.**
  An uncatalogued model costs at `DEFAULT_PRICING`, which is deliberately the *most expensive*
  card, so the figure over-reports rather than under-reports. `compute_cost` warns once per model
  at the point it happens, but a warning is not carried on the result: everything downstream saw a
  float indistinguishable from measured spend. On 100k/50k tokens that float is $10.50 where
  `gemini-2.5-flash` is $0.155.

  The flag rides beside the number on `AgentExecutionTrace`, `ProviderResult` and `LLMResult`, and
  says what is true of it: `DEFAULT_PRICING` being the top card makes the cost a genuine upper
  bound, safe to budget against but not to bill, report as spend, or average into a rate. The point
  is the aggregate — one unpriced model in a run makes the whole total a ceiling, and a consumer
  can now notice that instead of publishing it.

  It is set through one `record_cost(trace, model, **buckets)` helper rather than a second line at
  each of the four provider sites, because the pair must not come apart: a `cost_usd` written
  without its provenance is a guess wearing the costume of a measurement. The buckets differ by
  provider (OpenAI's `reasoning_tokens`, Anthropic's `cache_creation_tokens`) and pass straight
  through. On the LLM tier the flag is derived from the name that was actually costed — the
  tier-adjusted one for a `flex_`/`batch_` call — so it cannot disagree with the number beside it.

  **Propagated through `LLMResult`, not left at the provider.** `LLMResult.truncated`'s own
  docstring records this failure already: computed correctly by every provider, then dropped at
  exactly that dataclass boundary. A flag is worth its weakest hop, so a test asserts every
  `LLMResult` construction in the manager carries it — the primary path and the fallback path —
  rather than pinning one instance.

  Five test doubles hand-rolled `SimpleNamespace` in place of `ProviderResult` and broke on the new
  field. They now construct the real dataclass, which is the actual fix: a lookalike double stops
  matching the contract silently, so the next field added breaks the tests instead of the code
  under test. That is the second time this shape has bitten, after `truncated`.

- **Gemini reaches the agent tier: `AgentExecutionService.gemini`, and a real tool loop behind it.**
  AES already *inferred* `gemini` from a model name and then refused it, with a hint saying to use
  OpenAI or Anthropic for anything with tools. That was the last asymmetry in the provider story —
  three backends, two of which could run an agent and one that could only answer.

  `agents/gemini_provider.py` implements the same `run` contract its siblings satisfy: same
  arguments, same `AgentResult`, same `AgentExecutionTrace`, same shared `compute_cost`. A caller
  writing against the generic tier cannot tell which provider answered from the shape of what comes
  back, which is the entire promise of a generic tier. The one place the loops genuinely differ is
  that Gemini matches a tool result to its call by **name** rather than by a call id.

  A failing tool is reported to the model as its result rather than raised — the model asked for
  something that did not work, and telling it so is what lets it recover, where raising ends a turn
  it could have finished. Usage accumulates across rounds, because a turn's cost is every round it
  took; `thoughts_token_count` counts toward output because it is billed.

  All three refusal paths now share one message — `Unsupported provider: X. Supported: openai,
  anthropic, gemini.` — where a third site had been raising its own hardcoded string, so a caller
  who named a bad provider *with* a model got different words than one who named it without. The
  message names the supported set and stops there, and that is the SDK-level stance rather than a
  tidying preference: reaching a model is the smallest part of running one usefully. Pricing,
  guardrails and the per-model request quirks (`unsupported_request_params`, caching, reasoning
  settings) are all keyed by model family, so a model japes does not know is a model it cannot cost
  or constrain — an uncatalogued one falls back to `DEFAULT_PRICING` and bills 100k/50k tokens at
  $10.50 where `gemini-2.5-flash` costs $0.155. Knowing the family is the precondition for the rest
  of the SDK doing its job, and an adapter added on purpose when something is actually needed is
  worth more than a passthrough that makes every provider look half-available. Existing tests used **gemini**
  as their example of an unsupported provider — the set that message rejects is exactly the set
  with no adapter, and it shrinks by one each time an adapter is written, so they moved to
  `kimi-k3` and `vertex`.

  The LLM tier's own refusal was misdirecting in the same way, and worse: `_get_provider` reported
  `Provider kimi-k3 not enabled` for a provider it has no adapter for, sending someone to look for
  a switch that does not exist, while the `Unknown provider` line beneath it was unreachable —
  `_provider_config` holds exactly the four constructible names, so the enabled-check caught
  everything first. Those are two different problems (**unsupported**: nothing you can do;
  **supported but disabled**: `local` with `enable_local=False`, genuinely a switch) and they now
  say so separately, with the supported set read off the config so it cannot drift. The dead branch
  became the wiring assertion it actually is: a provider configured with no constructor.

  **Providers are strict, models are not, and that asymmetry is deliberate.** The two are
  distinguishable — `provider_for_model()` resolves a family by pattern, `is_priced()` says whether
  the catalogue knows a specific model — and they are treated differently on purpose. Provider
  support is a fact about code japes has written, so an unsupported one is a hard error. Model
  support is a fact about a catalogue that is always behind: `gpt-5.4-mini` is priced,
  `gpt-5.9-turbo-preview` is not, and both route to OpenAI correctly because the pattern matches
  the family rather than an enumerated list. Gating on the catalogue would break every new model on
  the day it ships, so nothing does. The real cost of an uncatalogued model is not a refusal but a
  silent one: it prices at `DEFAULT_PRICING` and overstates by orders of magnitude, which
  `compute_cost` already warns about at the point it happens.

  **The provider story, whole:** four backends (OpenAI, Anthropic, Gemini, Kernel) behind two
  layers japes owns — `AgentProvider` for the agent tier's loop, `agents.Model` for the Agents SDK
  runner — with `resolve_model` dispatching and `RetryingModel` decorating any of them. What LiteLLM
  offered was one interface over many providers; what it cost was a dependency pinning
  `openai<3.0.0` and translating in a layer japes did not own. The equivalence a LiteLLM user should
  check is exactly this: one `run` contract, one trace shape, one cost model, and per-provider
  quirks handled where they are visible.

- **`GeminiNativeModel`: the last provider off LiteLLM.** `google-genai` was already an optional
  dependency here serving `GeminiProvider`, so the layer being removed was never fetching anything
  the SDK could not fetch itself — it was translating, and this does the same translation one hop
  closer in. Blocking, streaming and a real tool call all verified against the live API.

  **Two mismatches that fail silently rather than loudly, which is why they are pinned.** Gemini's
  assistant role is `model`; sending `assistant` does not error, it makes the model read its own
  previous turns as the user's and answer accordingly. And Gemini identifies a tool result by the
  function's **name** where Responses uses the `call_id` of the call it answers — nothing in a
  `function_call_output` carries that name, so the mapping walks the input in order and remembers
  what the earlier `function_call` was called.

  Gemini streams whole parts rather than opening and closing a block the way Anthropic does, so the
  item lifecycle is synthesised: the first chunk carrying text opens the item, later chunks delta
  into it, and it closes when the stream ends. A consumer sees one shape whichever provider
  answered, which is the point of doing this at the model layer.

  Usage needed care: Gemini counts `thoughts_token_count` inside `total_token_count` but **outside**
  `candidates_token_count`, so output is the sum of the two — reporting candidates alone understates
  what the turn produced. Verified against a live response reporting 9 / 1 / 24 / 34.

  **LiteLLM now serves one thing only:** an explicit `litellm/<provider>/<model>` name — a genuine
  passthrough for a provider japes has written no adapter for, including Vertex AI's
  project/location routing, which a bare model name cannot express. Dropping the extra is now a
  question about that passthrough rather than about Claude or Gemini, and dropping it lifts the
  openai-agents ceiling its `openai<3.0.0` pin imposes.

- **The Claude catalogue, rebuilt from the API rather than from memory.** Five models added
  (`claude-opus-5`, `claude-sonnet-5`, `claude-opus-4.7`, `claude-opus-4.6`, `claude-fable-5`) and
  two existing rows given the cards they lacked (`claude-opus-4.5`, `claude-sonnet-4.5`). Limits and
  capabilities come from `GET /v1/models`, which reports `max_input_tokens`, `max_tokens` and a
  capability object per model; rates from the pricing page. Nothing was recalled — the one existing
  row that overlapped, `claude-opus-4.8`, matched the fetched rates exactly, which is what made the
  field mapping trustworthy.

  Provenance records the sources and the date and deliberately claims **no human reviewer**: these
  are machine-read and unreviewed, and signing them off as reviewed would be the kind of false
  attribution the block exists to prevent. `claude-fable-5` is documented as current but 404s on the
  account used to probe, and its provenance says so.

- **`temperature` is rejected by Claude's adaptive-thinking models, and we were sending it.** Found
  by probing every catalogue id live: `claude-opus-5`, `claude-sonnet-5`, `claude-opus-4.8` and
  `claude-opus-4.7` answer a request carrying `temperature` with a 400 — *"`temperature` is
  deprecated for this model"* — while 4.6 and earlier accept it. Four of the nine reachable models,
  including the two newest, failed every call the native path made.

  This is the same class of thing OpenAI's reasoning tier does and which
  `unsupported_request_params` already describes per model, so the fix reuses it rather than
  hard-coding a list: the four cards declare it, and `AnthropicNativeModel` strips what the card
  names. A future model needs a card edit, not a code change. All nine reachable models now
  round-trip live.

- **A live smoke test found what a faked stream could not: our own Claude ids 404.** The catalogue
  writes a version as `claude-haiku-4.5`; Anthropic's API wants `claude-haiku-4-5` and returns a
  flat 404 for the dotted form. Nothing caught it because the LiteLLM path never sent our id
  straight through and a faked SSE answers to any string. One real call found it.
  `AnthropicNativeModel` now normalises on the way out; dated ids carry no dots and pass unchanged.

  Probing every Claude id in the catalogue against the live API turned up a second, separate
  problem this does **not** fix: five of the ten are models the account cannot reach at all —
  `claude-opus-4.1`, `claude-opus-4`, `claude-sonnet-4`, `claude-3.5-haiku`, `claude-3-haiku` — and
  the live list carries four we do not have (`claude-opus-4-6`, `claude-opus-4-7`, `claude-opus-5`,
  `claude-sonnet-5`). That is catalogue currency, and each row needs pricing nobody should invent,
  so it is reported rather than guessed at.

  The live tests are opt-in beside the existing ones (`RUN_LIVE_LLM=1` plus the key), cheap, and
  cover blocking, streaming, and a real tool call — the last being the half a fake vouches for
  least, since it is where Anthropic either accepts the tool schema we build or does not.

- **`AnthropicNativeModel`: Claude through the Agents SDK without LiteLLM in the middle.** One
  dependency sets the ceiling on the whole SDK — LiteLLM pins `openai<3.0.0` while openai-agents
  0.21+ needs `openai>=3.0.0` — for an extra exactly one consumer installs. This is the same model
  without that layer: japes' own Anthropic client wired straight to the `agents.Model` protocol.

  **Both halves are native.** `get_response` sends one request; `stream_response` reads Anthropic's
  SSE and translates it into the Responses events the runner expects. Two streams describing the
  same thing in different vocabularies — Anthropic opens a content block and deltas into it, the
  Responses API adds an output item and deltas into it — and that translation is precisely what
  LiteLLM was performing one hop further out, which is why doing it here removes the layer rather
  than duplicating it.

  Text and tool arguments both stream. Arguments arrive as JSON fragments where only the
  concatenation parses, so the call is assembled once at the block's end rather than re-parsed per
  delta; `sequence_number` increases monotonically across every branch, because a consumer ordering
  by it must never see two events claim the same slot. A `ThinkingDelta` is deliberately not
  emitted: the Responses vocabulary has no event for it here, and inventing one would put Claude's
  reasoning trace into a stream a UI renders verbatim. Anthropic reports input tokens at the start
  and output tokens at the end, so usage is merged across both — reading either alone reports a
  turn that cost nothing to send or nothing to receive.

  **Unmapped input shapes raise.** An item silently dropped is a tool result that never reached the
  model, or a turn of history that vanished — both of which read as the model behaving badly rather
  than as a missing branch. A `NotImplementedError` naming the item type is the failure that gets
  the branch written. Handoffs raise for the same reason. Malformed tool arguments do *not*: the
  model wrote them, so they surface as an empty call for the tool to reject, not an exception
  inside the request path.

  **Native is now the default.** Claude used to raise `ImportError` without the extra, leaving a
  consumer who never wanted LiteLLM unable to reach Claude at all. The remaining argument for
  keeping LiteLLM in front was that it had carried Claude in production — it has not, since the one
  consumer installing the extra is a proof of concept. `JAPES_ANTHROPIC_LITELLM=1` forces the old
  path back. The extra still serves everything else it did (Gemini, any explicit
  `litellm/<provider>` name), so this narrows what depends on it; dropping it entirely is what
  lifts the openai-agents ceiling its `openai<3.0.0` pin imposes.

- **`preserve_raw_usage`: a provider's own usage payload survives normalisation.** Not what it
  looked like from the outside. It does **not** replace the extractor's field-by-field reading —
  the snapshot it keeps is rawer, not tidier, and still has to be parsed. What it does is make a
  count survive that `Usage` has no field for.

  `Usage` models `cached_tokens` and `cache_write_tokens` and nothing else about caching, so a
  provider's own `cache_creation_input_tokens` reaches the cost tracker today only because the
  object handed over happens to still carry the attribute — an accident of which path produced it,
  not a guarantee. With this on, the SDK keeps a snapshot of the provider payload taken before it
  normalises, and `extract_token_usage` prefers it for exactly the fields normalisation drops.

  Read at the top level *and* one nesting down, because a snapshot is unnormalised by definition and
  the same count sits beside its siblings in one provider's payload and under a details object in
  another. A non-numeric value counts as absent rather than raising: a usage figure is telemetry,
  and a malformed one must not take down the call it describes. The snapshot never lowers a count
  already reported, and with no snapshot the extraction is byte-identical to before.

- **`prompt_cache_options`: a pack can say how its prompts should be cached, not just where.**
  japes already had `build_prompt_cache_key`, and cached tokens were already *measured* in the
  usage extractor and the cost tracker — but nothing could influence whether a hit happened.

  The two are complementary and the distinction is the point. `prompt_cache_key` decides **which**
  cache a turn routes to, and stays in `extra_args` because the SDK still has no field for it —
  checked, not assumed. `prompt_cache_options` decides **how** caching behaves:
  `{"mode": "explicit"}` opts a call in deliberately rather than relying on implicit prefix
  matching, and `{"ttl": "30m"}` holds the entry far longer than the implicit window. A persona plus
  a knowledge block plus a tool catalog is a long static prefix repeated on every turn of a session,
  where the gap between a hit and a miss is most of the prompt.

  Named on `build_model_settings` rather than falling through `**extra`, for the reason already
  stated there for `reasoning_summary` and `response_include`: it is a `ModelSettings` field, not a
  raw provider arg. Passed only when asked for — sending `{"mode": "implicit"}` explicitly is not
  the same request as sending no options at all — so a spec that does not set it still builds no
  settings object, unchanged.

- **`InteractiveAgentSpec.tool_name_collision`: a pack can refuse a run whose tools collide.**
  The agent composes its catalog from several independent sources — a skill registry, knowledge
  bindings, and MCP servers — none of which knows what the others named their tools. `parent_tools`
  is a plain list, so two tools sharing a name both reach the model and one of them wins; what the
  model then calls is not what it meant to call, silently.

  Set to `"error"` and the run is refused instead. The default stays the SDK's own `"warn"`, so an
  existing pack with a benign duplicate is unaffected and raising the bar is opt-in rather than a
  migration. Threaded through all three `Runner` call sites — blocking, reasoning-stream, and token
  stream — because a collision does not become acceptable because the caller wanted tokens.

  **Delegated to the SDK rather than checked here, and that is the finding**: MCP tool names are
  fetched from the server at run time, so the cross-source collision that matters most is invisible
  to anything japes could inspect while building the agent. A build-time diagnostic naming which
  sources clashed would have missed exactly the case worth catching. The `RunConfig` is built only
  when the policy differs from the default, so a pack that never sets it gets byte-identically the
  `Runner` call it got before.

- **openai-agents floor raised 0.17.0 → 0.20.0.** Eight releases behind, and the suite passes on
  the new one unchanged — 4000 tests, no code change needed. `Model.get_response`/`stream_response`
  are untouched across the range, which is why `kernel_model`, `anthropic_model` and
  `openai_provider` are unaffected.

  **The ceiling is 0.20.x, and the wall is litellm rather than us.** 0.21+ requires
  `openai>=3.0.0`; every litellm release through 1.98.0 pins `openai<3.0.0`. Verified against PyPI
  metadata rather than assumed. Worth knowing precisely, because litellm is an *optional* extra:
  the suite also passes on **0.22.0 with openai 3.6.0**, so nothing in japes blocks the newest — a
  consumer who does not install the litellm extra can resolve straight past it, which the `>=` floor
  deliberately permits. The floor is not capped; only the lock sits at 0.20.0, because the lock
  resolves every extra together.

  What 0.20 brings that we can now reach: `ModelSettings.prompt_cache_options` (we already *measure*
  cached tokens without being able to steer them, and a pack's static instruction block is exactly
  the long-prefix case), `preserve_raw_usage` (instead of scraping provider usage field by field),
  `ToolNameCollisionPolicy` (`InteractiveAgent` composes tools from a skill registry, KH and MCP
  servers, where a clash is currently undefined), and `FunctionTool.allowed_callers` — a native hook
  for the boundary the tool zero-data-retention note describes. All verified present, none wired up
  yet.

  Also: the document-analyzer example still floored at `openai-agents>=0.1.0`; raised to match.

- **A chat turn can be stopped, and stopping is not failing.** `chat.py` had no vocabulary for "a
  turn in flight was told to stop" — the closest was `GeneratorExit`, which means something else
  entirely: the reader left, nobody stopped the turn. `InteractiveResponse` gains `cancelled` /
  `cancel_reason` as a third terminal state beside `blocked` and `incomplete`, and `chat.cancelled`
  is its own metric rather than folded into `chat.failed`, so a deploy that drained cleanly does not
  read as an outage.

  **Two mechanisms, because there are two real ones.** `ChatTurn.cancel` is anything with
  `is_set()`, checked before the turn starts, before the gather, and between deltas — cooperative,
  so a barge-in closes the stream with a terminal event rather than just stopping, since a stream
  that stops is indistinguishable from a crashed one. `asyncio.CancelledError` is the hard path: it
  is recorded and then **re-raised**, never swallowed. Swallowing it would leave `task.cancel()`
  unable to stop the task, which is the one thing the caller asked for; letting it propagate
  unrecorded would file a deliberate stop as an unexplained failure.

  How a cancel *request* reaches the turn is deliberately not modelled — a second HTTP call, a
  pub/sub message to the owning worker, a shutdown handler are all the runtime's business. japes
  owns the state and the guarantees around it: the workspace is released, `on_complete` fires, and
  the metrics say what happened.

- **`chat.py` gains a pre-answer `ground` step and a per-turn workspace.** The reference chat
  pipeline was introduced as the substrate for exactly the consumers that then did not adopt it,
  and reading their turn flows says why: both do real work between routing and answering that
  `validate → gate → answer → refuse → finalize` has no place for.

  **`ground`** gathers what the turn needs before the model is asked anything.
  `InteractiveAgent` grounds itself from its knowledge bindings, and for a pack whose context is a
  retrieval query that is the whole story — it is not, when the context is several independent
  fetches from different systems, any of which can fail alone. The bindings have no way to say
  "four sources at once, and a missing one degrades rather than sinking the turn", so a consumer
  needing that orchestrates it outside the pipeline, where it stops being traced, stops being a
  stage, and stops being visible to progress. Sources are declared on `ChatTurn` as
  `label -> (thunk, default)`; `gather_degrading` already did the hard part, including its own
  in-flight progress hook at a finer granularity than the engine's per-step events. Off by default,
  and skipped for a turn declaring no sources.

  **`workspace`** holds a per-turn resource for the length of the turn and releases it however the
  turn ends. Two consumers converged on this from different domains — a scratch directory the
  retrieval and the answer both read, and a checked-out working copy reconciled afterwards — and
  neither fits a step: the resource outlives the stage that creates it, and release has to run on
  the failure and abandonment paths too. On the streaming route it is released even when the
  consumer walks away mid-stream, which is the case a plain `async with` around a yield misses and
  the one that strands a directory or a checkout.

  Both are additive: a pack that passes neither sees no change.

## [2.4.9] - 2026-08-28

Mostly about the reference chat pipeline learning to host a real consumer's turn. `chat.py` was
shipped as the substrate for exactly the consumers that then did not adopt it, and reading their
flows says why: both do work between routing and answering that `validate → gate → answer → refuse →
finalize` had no place for. It gains a pre-answer `ground` step, a per-turn `workspace`, and a
vocabulary for a turn being stopped; `respond_stream` gains the output schema that made a caller run
every structured turn twice. Alongside that, package splitting stops reading one page at a time.

Also here: a pack's rules can live entirely in YAML its manifest already names, which removes the
Python module a YAML-only pack had to keep alive purely to hold a list, and closes two ways a pack
could lose its policies without a sound.

Everything is additive — every default reproduces the previous behaviour — and the commits behind
these entries were squashed on the way in, so the reasoning lives here.

- **Consumer names removed from the SDK's published schema.**
  A first pass stripped every mention of a consumer repo from the tree, which was too much: a README
  or ARCHITECTURE naming its consumers is doing its job, and a comment or test may reasonably cite
  the caller a behaviour came from. That pass was reverted whole. What stays fixed is the line that
  is not a matter of taste.

  Pydantic puts a model's **class docstring** into `model_json_schema()["description"]` and each
  `Field(description=...)` into the property beside it, so those strings are not comments -- they
  are the SDK's public contract, and they reach generated API docs, client generators and anything
  that introspects a model. Scanning every `BaseModel` under `jazzx_sdk/` found **30 classes whose
  published schema carried a consumer's name** across 16 distinct lines: `"Semantic slug (not
  UUID). e.g., 'jaci-aml'"` on `DomainPack.pack_id`, `"Target handler ID (e.g., 'macer',
  'macer-agent')"` on `MessageSource` (inherited by three more schemas), a gitignored plan filename
  in `ValidationFinding`'s severities, and a dozen more. All 16 now name a role rather than a repo,
  and the scan reports zero.

  The distinction worth keeping: prose about *why* something exists may cite who needed it; a string
  the SDK publishes may not.

- **The SDK no longer reaches into a consumer package.**
  `GovernorMode` did `from jaci.pack.policy_registry import RULE_INDEX` inside a `try/except
  ImportError`, to warn when a decision cites a sunset or deprecated clause. That is the dependency
  the wrong way round -- an SDK importing a downstream pack by name -- and because the failure was
  swallowed, the check was dead in every installation but one while looking wired. It now reads an
  injected `policy_registry`, alongside the `authority_matrix`/`client_overlay`/`execution_profile`
  the constructor already takes, so any pack gets the check rather than one. It reads `rule_index`
  rather than `current_rules`, since the latter drops exactly the legacy aliases the sunset warning
  exists to find, and a registry of an unexpected shape is logged and skipped rather than allowed
  to fail a governance turn.

  `tests/conftest.py` faked `jaci.schemas`, `jaci.utils.prompt_loader` and `jaci.settings` in
  `sys.modules` before collection, so the modes' lazy imports would resolve. Nothing under
  `jazzx_sdk/` imports a consumer package any more, and the suite passes unchanged with the stubs
  removed -- so `tests/mocks/` is deleted and the file says why its former contents are gone. An
  SDK that needs its consumer stubbed to be testable has the dependency inverted; the absence is
  the point.

  Three docstring examples named a consumer's module path (`from jaci.pack.policy_registry import
  ...`) and now use a neutral `mypack`. Prose and provenance mentions elsewhere are untouched and
  counted separately.

- **Two more review findings, both invisible to a test run by construction.**
  `_windows(0, size>1, ...)` returned `[(0, -1)]` -- one window over an empty slice, costing a
  classification call on `""` where the per-page path made none. Guarded at the top now. The
  coverage sweep added alongside the stride fix swept `n in range(1, 24)`: it started at 1, so it
  excluded the exact input that breaks. It starts at 0.

  `tests/test_pack_policy_files.py` hardcoded an absolute workstation path, `skipif`-guarded, so it
  ran on one machine and silently did nothing everywhere else -- a test that cannot fail is not
  coverage. It is driven by `JAPES_REAL_PACKS_DIR` now, and its skip reason says how to run it.

  Neither was catchable by the pre-push hook as it stood: one is an input nothing tested, the other
  a test that never ran. The second is mechanically detectable though, so the hook grew a check for
  absolute home paths in *tracked* files (`scripts/local/` is gitignored and is exactly where such
  a path belongs) -- verified against the offending line before it was fixed.

- **Two review findings on the 2.4.9 PR, both real, one worse than reported.**
  `split_document` accepted a `window_stride` wider than `window_pages`, which skips pages outright:
  the trailing guard covers a document's tail and cannot cover the interior gaps a wider stride
  opens between every pair of windows. `n=10, size=2, stride=4` leaves pages 2, 3, 6 and 7 uncovered;
  `n=20, size=4, stride=8` loses eight. An uncovered page collects no votes and lands as `"unknown"`
  with zero confidence, so it reads downstream as a page nothing *recognised* rather than a page
  nothing *looked at* -- and only one of those is a real finding. Unreachable by default, where
  stride equals window size; now refused rather than clamped, because clamping runs something other
  than what was asked for and this is a configuration error, not a hard document.

  The grounding finding was directionally right and its premise was wrong, which made the bug
  bigger. `ground` declares `when="route != refuse"`, but `when` is descriptive -- `chat_guards()`
  is its executable side, and it had no `ground` entry, so an unguarded step ran for every route.
  The blocking path was not "getting this right": **both** paths grounded a refused turn. A refused
  turn was fanning out to retrieval and discarding the result -- latency and cost for an answer
  nobody sees, and an out-of-scope question still reaching systems the gate had declined to consult
  on its behalf. The guard now exists, and the streaming path grounds after the refuse return
  rather than before it. Placed above the escalate branch, because the guard excludes only
  `refuse`: an escalated turn still grounds, and the two paths have to agree.

- **A pack's rules can live entirely in YAML the manifest already names.**
  `load_policies` and `from_policy_dir` could turn policy YAML into a working registry, and real
  manifests were already writing `core: policies/core.yaml` and
  `overlays: [{path: policies/overlays/rb_ci.yaml}]`. Nothing joined the two: `Pack.policy_registry`
  read only the `registry:` dotted pointer into consumer Python, so those declared paths were
  inert and a pack whose rules were entirely in YAML still needed a Python module alive purely to
  hold a list. `PackManifestLoader.policy_files()` now resolves them, in precedence order, and
  `Pack` builds a `PolicyRegistry` from what it finds.

  So the hop uses keys packs are already writing rather than a new one -- `dir:` is additionally
  honoured for a folder a manifest would otherwise enumerate file by file, which is the shape an
  extraction pipeline writes into. Measured on a real authored pack: `clinical-intake-core`
  declares `core:` and no pointer, and `Pack.policies` was empty for it before this.

  **The `registry:` pointer still wins where a pack has one.** Every existing pack uses it, and a
  registry quietly assembled from YAML behind its back would be a different set of rules under the
  same accessor. `checklist:` is excluded by name -- it is declared in the same manifest block and
  is not a policy document -- and a `dir` skips non-policy assets through `is_policy_document`
  rather than failing the load or, as before, contributing nothing silently. A declared file that
  is missing warns and is skipped: real manifests point at overlays that are not on disk, and
  losing a whole registry over one of them is worse than loading what is there.

  A stub loader in the existing pack tests broke on the new contract method -- the third instance
  this cycle of a hand-rolled double drifting from the interface it stands in for. Fixed on the base
  stub rather than by making `Pack` defensive, since the loader contract is the thing being tested.

- **Two silent-failure fixes in the policy loader, found by testing the round-trip.**
  `Policy -> model_dump -> YAML -> load_policies` was verified against real authored packs (9
  policies, 60 rules, 5/5 clean) since the pipeline's output contract is "emit YAML `load_policies`
  validates" -- proven for `expression`, `matrix`, `ratio` and `all_of`; `natural_language`, `dsl`
  and `any_of` have no authored coverage and remain untested.

  `load_policies` answered a non-policy YAML with `[]`, which is indistinguishable from an empty
  policy set -- the same principle `get_condition_evaluator` already applies to an unregistered
  kind: a real, deliberate failure, not a silent skip. It now raises and names what it found.
  `DefaultPolicyExpert.from_policy_dir` consequently skipped such a file without a sound (pointed at
  a real pack it loaded 6 policies and contributed 0 from the checklist beside them); it now uses
  the new `is_policy_document` to skip non-policy assets **by name**, and logs which. A pack's
  policy folder legitimately holds other assets; losing rules to a malformed emission is the failure
  this closes, and it is exactly the trap an extraction pipeline writing into that folder would fall
  into.

- **Five signature annotations that resolved nowhere now resolve.**
  Audited rather than bulk-fixed. `CanonicalEvidenceObject`, `CanonicalDecision`,
  `ImprovementSignal`, `EvaluationReporter` and `DiscoverySourcesConfig` named real, importable
  types that were simply never imported, and `KGStore.get_ontology` annotated `Optional[dict]`
  without importing `Optional`. Nothing broke at runtime -- the annotations are strings that are
  never evaluated -- but `typing.get_type_hints()` raised on the public callables carrying them, so
  they were unreadable to a type checker and a trap for any consumer using pydantic
  `@validate_call`, FastAPI, or signature-derived tool schemas.

  **Real imports, not `TYPE_CHECKING` ones**, which was the first attempt and the wrong one:
  `TYPE_CHECKING` is false at runtime, so it satisfies a linter while `get_type_hints()` keeps
  raising -- it fixes the appearance of the problem and not the problem. No module imports back, so
  there is no cycle to dodge, and import cost is unchanged.

  `fabric/canonical/profiles.py` is correct as written and marked `# noqa: F821` rather than
  "fixed": its forward reference breaks an import cycle and `periods.py`'s `model_rebuild()`
  resolves it, verified against a fresh interpreter. Importing it would hide that the runtime
  rebuild is doing real work.

  Also audited and deliberately left alone: all 15 `F811` findings, which are one pytest fixture
  (`rb_appendix_d`) imported into a test module and then used as a parameter name by 15 tests. Ruff
  reads each parameter as shadowing the import; the tests run. One `# noqa` cannot cover it because
  F811 fires at each use site, and the real fix is moving the fixture to a `conftest.py`.

- **`respond_stream` can produce the object as well as the tokens.** It took no `output_schema`, so
  a caller wanting both streamed text and a parsed result had to run the turn twice — and the
  second, separately-sampled run need not agree with what was streamed. The plumbing already
  existed: `_stream_agentic` accepted a schema and shaped the run with it, but `respond_stream`
  passed a hardcoded `None` and the final object was dropped on the floor. It is now threaded
  through and lands on the done event's `response.output`.

  The result is captured per turn rather than stashed on the agent: an agent is shared and a turn is
  not, so two concurrent streams would overwrite each other's output. Read only once the stream is
  exhausted, since `final_output` is not populated before the run completes.

  **Only the agentic path can do this**, and passing a schema to a skill-less agent raises rather
  than returning `output=None` — which a caller would read as "the model produced nothing" instead
  of "this path cannot do that at all". The constructor's own `output_schema` default is still
  ignored on the single-shot path, exactly as before, so nothing existing changes behaviour.

- **The streaming chat route forwards `ChatTurn.output_schema` too.** It was honoured on the
  blocking route and dropped on the streaming one, so the same field meant different things
  depending on which way the gate happened to route a turn. It was dropped because
  `respond_stream` could not take a schema; now that it can, both routes agree.

- **`DELETE /agents/{name}` honours `If-Match`, like `PUT`.** `strict_concurrency` was wired through
  `check_if_match` on the write path and ignored on the delete path, so a client could remove
  whichever revision happened to be current — including one written after its last `GET`. Gated by
  the same flag, so a caller that never sends the header is unaffected; a stale one gets 409 and a
  missing one under strict mode gets 428, keeping "you forgot a precondition" distinct from "someone
  else won the race".

- **Package splitting reads a window of pages, not one page at a time.** A page classified alone is
  often unlabelable — page four of a form has no letterhead and no signature block, and the taxonomy
  has nothing to match, so it came back `unknown` and was swallowed into whichever run it fell in.
  `split_document` gains `window_pages`, which gives the classifier the continuity a reader has, for
  *fewer* calls rather than more. `window_pages=1` is exactly the per-page behaviour it had before.

  **The seam is the hard part, and it is solved by weighting rather than a second pass.** A window
  straddling a boundary sees two documents. `window_stride` makes windows overlap so each page is
  voted on by several, and a vote carries two weights: **confidence**, so two unsure windows
  agreeing on `unknown` cannot outvote one that recognised the document; and **centrality**, so a
  window speaks loudest about the pages at its middle. Without the second weight a page sitting at
  one window's edge and another's centre ties, and the tie breaks arbitrarily — landing the boundary
  in the wrong place, at exactly the seams overlap exists to resolve. Centrality is free and needs
  no extra classification round.

- **`absorb_below` folds a short unrecognised run into its longer neighbour**, which
  `smooth_max_gap` could not: that only closes a gap between two runs of the *same* label, so a
  stray page between two different documents stayed its own segment. **Length alone is not the
  test** — a one-page bank statement is a whole document, and absorbing it for being short would
  destroy a correct classification. Only `absorb_labels` (default the classifier's own `unknown`)
  are eligible, absorption recomputes after each fold rather than deciding everything against a
  stale run list, and a document that is nothing but short runs is left alone rather than collapsed
  toward whichever end came first.

- **`families` merges contiguous runs whose labels belong together**, e.g.
  `{"Property File": ["Title", "Survey"]}`. Only adjacent members merge: the same labels appearing
  again later stay a separate segment, because a second occurrence is a second document. Which
  labels form such a set is domain knowledge, so a pack declares it rather than this inferring it.

- All four are also on `DocumentAgentSpec` (`split_window_pages`, `split_window_stride`,
  `split_absorb_below`, `split_families`), beside the `split_ocr_fallback` that was already there —
  a knob a pack cannot set is a knob a pack cannot use. Every default reproduces the previous
  behaviour exactly.

## [2.5.0] - 2026-08-28

**`KGAgent` is the new platform agent and `pipelines.vocabulary_build` the pipeline that feeds it.**
A corpus of documents becomes typed assertions, those accumulate into proposals against a pack's
vocabulary, and what a reviewer or an admission policy accepts is merged into a new version. The
agent owns exactly one question — *should this enter the domain's vocabulary* — and composes the
answers to the rest, because extraction already had a chassis and this was the half that did not.

Around that sit the other three capabilities the graph work names: **grounding** a model in a
vocabulary as context or as a queryable tool, and recording which way it reached the model;
**asserting** case facts with provenance back to a page and section; and **checking** those facts
against a pack's policy into citable findings. A pack's authored ontology is read as the same
`Vocabulary` the loop grows, so construction and execution meet on one object rather than two.

Everything is additive — no existing behaviour changes — and the commits behind these entries were
squashed on the way in, so the reasoning lives here.

- **An audit backend going down no longer reports failure for a write that succeeded.**
  `agent_config`'s `PUT` appended its audit event after `store.put` had already committed, and let
  the append raise. The client got a 500 for a definition that was in fact written, and the natural
  retry then collided on `If-Match` against a revision that had moved — a 409 for a request that
  worked. The review surface had the same shape one step further along: a reviewer would click
  approve again and find the trigger illegal from the new state.

  `audit.record_best_effort(store, event)` is now the one place that behaviour lives, and both
  surfaces call it rather than each carrying its own `try`. It logs the unrecorded event at `error`
  with its full payload and returns whether it was recorded: an audit trail whose backend is down
  should degrade to a line that can be reconciled later, not vanish, and a caller that genuinely
  must refuse an unaudited change can still act on the return value. A store that must never miss
  an event belongs in the same transaction as the change it audits, not behind this helper.

  Only two call sites exist in this family and both are fixed.

- **`DELETE /agents/{name}` now audits, and is held to the same attribution bar as `PUT`.** A
  deletion was the one write on that surface leaving no trace: an edit was recorded and a removal
  was not. `before_digest` carries what was removed, which is the whole value of auditing a delete
  — the row is gone, so the digest is the only remaining evidence of what it had been, and
  `after_digest` is null. A 404 records nothing, since an attempt is not a change and a trail that
  logs attempts stops being a record of what happened.

  `ConfigAuditAction` gains `delete`. Mapping a hard delete onto the existing `retire` would have
  described the wrong event: retiring takes a definition out of service while its row and history
  remain, deleting removes the row. Nothing matches exhaustively on the action and the column is a
  plain string, so widening it needs no migration.

  The route also gained `_require_resolved_actor_in_deployed_posture`, which only `PUT` had. A
  deletion is the least reversible thing the surface does, so an unattributable one is the last
  write that should have been getting through.

- **`server.vocabulary_review`: the HTTP surface a person works the queue through.** japes owns the
  contract — what a reviewer can see and what they can do — and a studio or thin client renders it.
  Putting the rendering here would make every consumer inherit one team's idea of a review screen.

  **A decision goes through the lifecycle, never straight into the store.** This is the whole reason
  it is a module rather than four lines of CRUD. `store.record` writes any status it is handed,
  because reversing a ruling is legitimate; a route reaching for it directly would let an HTTP call
  admit a proposal without passing the transition that says who may do that and from where. So a
  decision is `admit(...)` against the pack's own machine, and the store only records what the
  machine returned. A refused trigger comes back as the machine's own typed reason with the triggers
  that *are* available, since "not from this state" and "not by you" are different things to see.

  **`available_triggers` is derived, and the endpoint enforces what it advertises.** The view is
  filtered to `TriggerType.HUMAN`, so a pack composing a different lifecycle automatically offers
  different actions and a client cannot hardcode approve/reject. The decision route then refuses
  anything outside that same set — the state machine checks that a *human* trigger was
  human-initiated but has no converse rule, so a request naming a system trigger like `promote`
  would otherwise fire it whenever its guard happened to pass, admitting on evidence through the
  door marked review. That mostly failed closed already because a missing profile refuses the
  guard, which is luck rather than a decision.

  **Attribution splits two facts that were being conflated.** `TransitionContext.actor_class` is
  what the transition authorises against ("reviewer"); the resolved caller is who the decision is
  filed under. `ProposalStore` had been reading `Proposal.admitted_actor` as the identity, which
  would have filed every human approval under "reviewer" — `decided_by` now always comes from the
  request context, and stays empty rather than guessing when no caller resolves.

  Merging returns the new vocabulary rather than adopting it, matching `KGAgent`: a surface that
  republished a pack whenever somebody approved a proposal would make approval mean something nobody
  agreed to. The merge route is only mounted when a `vocabulary_for` resolver is supplied, since a
  route that always fails is worse than one that is not there. Audit appends are best-effort,
  deliberately unlike the agent-configuration surface: the store write has already happened, so
  raising would answer a recorded decision with a 500 and send the reviewer to click approve again,
  where the trigger is now illegal from the new state.

- **`pack.lint` + `scripts/pack_lint.py`: a pack's assets read together.** Each is valid on its own
  and they are authored separately, so the failure that matters is a **join** — a policy rule or a
  derivation formula reading a name nothing in the pack produces. Nothing raises at load; it
  surfaces much later as a covenant coming back indeterminate with no explanation, which reads like
  a broken evaluator rather than a naming gap.

  Run against a real authored pack it immediately found two: the `FCCR` formula reads `taxes` while
  the ontology declares `tax_expense` — and the metric's own `inputs:` list says
  `FinancialPeriod.tax_expense`, so the formula disagrees with its own declared inputs — and
  `scheduled_principal` is read by two formulas and declared nowhere.

  Reports, never repairs: binding `taxes` to `tax_expense` on a name-similarity guess would be a
  wrong auto-binding on a covenant input, worse than an honest gap. Qualified and bare names both
  resolve, matching what `GraphContext` actually offers, so the lint does not invent a gap the
  evaluator would not hit. A condition kind with no registered evaluator is reported rather than
  read as "reads nothing", which would hide it behind a clean run. Underivable metrics are warnings,
  not errors — they can still be supplied through the evaluation context.

  The logic is a module so the Studio can render it; the script is a thin CLI over it and exits 1 on
  errors so it can gate a pack build. `--policies` is opt-in: a pack naming its registry by dotted
  path into the consumer's own code cannot be imported from japes.

- **`fabric.graph.derive`: a pack's declared ratio metrics computed from what its case asserts.**
  Run against a real authored pack, the policy read `leverage_x` and the case graph asserted
  `funded_debt` and `adj_ebitda` — **no overlap at all**, so every rule came back indeterminate
  until a caller hand-fed the metrics. Meanwhile the pack had already said how to compute them:
  `concept_graph` entries carry a `formula`, and nothing read it.

  **Deliberately not a formula language.** Of the six derivations in the pack this was built
  against, three are ratios and three are not: two need multiplication, one contains a literal
  `+/-` that has no single value. The grammar is exactly one division whose sides are sums and
  differences of names and numbers, and **anything else is reported as unsupported with the
  reason** — a metric silently absent looks identical to one that computed to nothing, and the
  point of the layer is that a covenant is never evaluated against a number nobody produced. A
  missing input, a zero denominator and an unresolvable dependency each say which name to go and
  find; a metric built on another resolves in a later pass.

  Kept out of `Vocabulary`, which is a schema graph — folding formulas in would make it a
  computation graph too — and read from the authored ontology instead, surfaced as
  `pack.derivations`. Distinct from `RatioCondition`, which is the *checking* shape (a ratio against
  a threshold, inside a rule); this is the *producing* shape (a named value a rule can then read).

  `check_graph` takes `derivations=` and reports `derived` / `underived`. Precedence is assertion,
  then derived, then supplied: an assertion carries provenance a computed value does not, and a
  computed value states how it was reached where a bare supplied number does not.

- **`Contradiction`: assertions that cannot all be right — a data problem, not a vocabulary one.**
  That distinction is the reason the type exists. A *conflicting proposal* says the corpus keeps
  asserting a shape the vocabulary does not declare, and the answer may well be that the vocabulary
  is stale. A contradiction says this particular assertion cannot be right: the value was misread,
  the wrong entity was typed, or two documents disagree. One is settled by curating the domain, the
  other by going back to the document, and reporting them through the same channel would send a
  reviewer to fix a schema when the extraction was wrong.

  `CaseGraph.contradictions(vocabulary=None)` reports three kinds. `value` needs no vocabulary and
  always runs: one subject, one predicate, two different objects. `type` is an object incompatible
  with what the vocabulary declares. `domain` is a predicate asserted about a concept it is not
  declared on — distinct from an *unknown* concept, which `unknown_concepts` already reports as the
  gap the curation loop exists to close; calling that a contradiction would send somebody to fix a
  document that is fine.

  **A contradicted value never reaches a verdict.** `GraphContext` withholds it exactly as it
  withholds an ambiguous one, so a covenant comes back `INDETERMINATE` rather than confidently
  wrong — the concrete failure being prevented is a document stating DSCR 0.95 against a 1.25 floor
  while another states 1.31, where taking the first assertion reports a breach the second denies.
  `contradicted` is reported apart from `ambiguous` because the remedies differ: one needs the rule
  qualified to say which subject it means, the other needs two documents reconciled.

  The type-compatibility rule moved to `vocabulary.satisfies` and is now shared with the
  accumulator, so a shape treated as *matched* there can never simultaneously read as a
  contradiction here.

- **`DELETE /agents/{name}` honours `If-Match`, like `PUT`.** `strict_concurrency` was wired through
  `check_if_match` on the write path and ignored on the delete path, so a client could remove
  whichever revision happened to be current — including one written after its last `GET`. Gated by
  the same flag, so a caller that never sends the header is unaffected; a stale one now gets 409 and
  a missing one under strict mode gets 428, keeping "you forgot a precondition" distinct from
  "someone else won the race".

- **`fabric.graph.check`: a case graph evaluated against a pack's policy, with the citation kept.**
  The fourth capability, and the one regulated industries pay for: an instance graph plus a policy
  plus an evaluation is "this facility breaches covenant 6.1, here is the clause, here is the page
  the number came from".

  **Almost none of it is new machinery, deliberately.** The rule model, the registered condition
  evaluators, `Verdict`, `RuleOutcome` and its `citations` field already existed, and
  `CanonicalDecision` is already the Finding shape — a finding is a decision, not a fifth object
  beside it. What was missing was narrow: a `Rule.condition` reads a flat mapping, a `CaseGraph` is
  not one, and nothing carried provenance across the gap. `GraphContext` is that join, offering each
  assertion under its bare predicate and under one qualified by the subject's concept
  (`Borrower.dscr`), since packs author conditions both ways.

  **An ambiguous name resolves to nothing rather than to a guess.** Two borrowers in one case both
  asserting `dscr` means the bare key cannot mean either, so it is omitted and the rule comes back
  `INDETERMINATE` — the correct answer, and the one the qualified key then answers properly. Picking
  whichever assertion was seen last would produce a confident covenant verdict about the wrong
  company. The ambiguous names are reported on `CheckResult`, because a rule untested for that
  reason is a different problem from one untested because the number was never extracted.

  **Untested is not passed.** `CheckResult.clean` requires nothing violated *and* nothing
  indeterminate, and an indeterminate rule produces a finding of its own — the same lesson
  `Coverage` encodes, since a check that quietly omits what it could not test reads as a clean bill
  of health. Its rationale names the input the rule wanted, taken from the evaluator's static
  evidence contract rather than from `RuleOutcome.inputs`, which describes the failure in the
  evaluator's own vocabulary. It carries zero confidence: there is no verdict to be confident about,
  and reporting the evaluator's own score would dress "we could not tell" as a weak finding rather
  than an absent one.

  Not re-exported from `fabric.graph`: it reads `fabric.canonical.policy`, which reaches
  `tools/__init__` and back into the graph package. Import from `jazzx_sdk.fabric.graph.check`
  directly, the same as `DbProposalStore`.

- **A pack's authored ontology is now readable as a `Vocabulary`, closing the loop back to the
  pack.** `KGAgent` produced a versioned vocabulary and packs authored one as YAML, and nothing
  connected them: a merged vocabulary was something no pack could load, and a pack's ontology was
  something no run could grow. `Vocabulary.from_pack_ontology` reads the shape packs actually
  author, surfaced as `PackManifestLoader.load_vocabulary()` and `pack.vocabulary`. **The version is
  the ontology's own**, so a vocabulary versions with the pack that ships it rather than beside it.

  Both `relationships` and `relations` are read, because both are live in authored packs today and
  honouring one would silently drop the other's edges. `concept_graph` entries become concepts of
  kind `property` — a derived metric is something the domain talks about and is not a class — while
  their formulas and inputs are not represented, since a vocabulary is a schema graph rather than a
  computation graph. `pack.ontology` still returns the authored dict unchanged for what reads those.

  Field types map onto the same XSD names `emit_assertions` emits, which is load-bearing: a declared
  relationship and an observed one have to compare equal. A declared type with no XSD equivalent
  (`list`, `dict`) is kept verbatim rather than forced into a wrong one.

- **Two accumulator defects that only a real vocabulary could surface.** Loading an authored pack
  turned both into immediate false conflicts:

  `_category` looked a candidate up **by predicate alone** while `Candidate` is keyed by shape. A
  predicate is not an identity in a real vocabulary — `name`, `description` and `company_name` are
  declared on many entities — so the index kept whichever entity happened to be authored last and
  reported every other entity's identical field as disagreeing with it. Lookup is now by
  `(predicate, source)`, falling back to predicate-only for an untyped subject, where shape cannot
  be matched. A predicate declared elsewhere but not on this entity reads `new`, which is what it
  is: a new edge, not a contradiction of one.

  Numeric widening was missing. `xsd:integer` derives from `xsd:decimal`, so a money field declared
  `float` and observed as whole dollars was reported as a conflict — which would have been every
  whole-numbered amount in a real corpus, arriving as noise in a review queue rather than evidence.

  Both were latent while vocabularies were hand-written for tests, where predicates happened to be
  unique. Verified against the two authored ontologies in the live consumer: 30 concepts / 214
  relationships and 6 concepts / 25 relationships, both resolving completely, with a confirming
  corpus now proposing nothing.

- **`ProposalStore`: a review queue that outlives the process that filled it.** An accumulator
  produces proposals in memory and a lifecycle decides them, which is enough for a run that decides
  its own output and exits. It is not enough for the shape that actually wants review: somebody
  opens a queue tomorrow, rules on what a run proposed today, and expects that ruling to still mean
  something the next time the corpus is processed.

  **The deterministic id is what makes that possible.** Proposal ids are derived from the
  candidate's shape and carry nothing about the run, so two runs over entirely different corpora
  that observe the same candidate produce the same `proposal_id`. That determinism already existed
  so a reviewer's queue would not double on a rerun; it is also exactly what lets a store recognise
  a re-proposal as the thing somebody already ruled on. Without it, persistence would be a filing
  cabinet rather than a memory.

  **Two write paths, because they answer different questions.** `put_set` is a run reporting what it
  saw: a decided proposal keeps its decision and only its evidence is refreshed, since a rerun is
  new evidence about a settled question rather than a reopening of it. `record` is a person or a
  policy deciding, and overrides whatever was stored, because reversing a ruling is legitimate and a
  store that ignored it would misreport what it holds. Collapsing them would force a choice between
  a rerun quietly resurrecting a rejected candidate and a reviewer being unable to change their
  mind.

  **Evidence is replaced, never accumulated** — adding the counts would let a rerun over an
  overlapping corpus drift a candidate's occurrences upward with nothing new observed. What the
  store adds instead is what memory genuinely cannot reconstruct: `first_seen`, `last_seen` and
  `times_proposed`. `ProposalEvidence.first_seen` is stamped fresh by each run, so it says when
  *that run* saw the candidate; a candidate four runs have vouched for and nobody has ruled on is a
  different thing from one proposed this morning, and only a store can tell them apart.

  Two backends: `InProcessProposalStore` and `DbProposalStore` on `fabric.db` (table
  `vocabulary_proposal`, DDL belonging to the consuming service's own alembic). The folding rules
  are shared functions rather than reimplemented per backend, and the behavioural tests run against
  both — whether a rerun reopens a rejected candidate is the one thing they must never disagree
  about.

  `pipelines.vocabulary_build` takes an optional `store`. With one, `propose` writes through it and
  continues with what came *back*, so a candidate somebody already rejected never reaches a reviewer
  again; decisions and merges are recorded as they happen, so the queue drains.

- **A vocabulary can now be bootstrapped by a domain that has no ontology to start from.** The
  blocker was not the accumulator — an empty `Vocabulary` already categorises everything as `new`
  and proposes it. It was upstream: types reached an assertion only from hand-authored
  `subject_concept` / `field_concepts`, so a domain with no ontology had nothing to write there, its
  assertions were untyped, and untyped assertions propose predicates forever. The vocabulary could
  never acquire its first concept.

  The seed was already on the result and unused. `DocumentResult.doc_type` is a classification, and
  classifying is the one thing that does not need a vocabulary. `emit_assertions` now falls back to
  it when `subject_concept` is empty — which `emit_entity` was already doing for an entity's type,
  making the assertion path the asymmetric half rather than this the new behaviour.

  The admission floor comes along for free: `process` leaves `doc_type` unset when the
  classification is sub-floor, so a shaky classification arrives as no classification and seeds
  nothing. The label is used verbatim, since reshaping it would put a name in the vocabulary that
  appears nowhere in the taxonomy that produced it. **Only the subject end bootstraps** — an
  object's concept still has to be declared, because nothing about a document says that a string
  value names an entity.

  End to end with no ontology anywhere: an empty `Vocabulary`, a spec naming no concepts, and a
  classified corpus produce a vocabulary holding its first concept with every relationship hanging
  off it and nothing dangling.

- **`pipelines.vocabulary_build`: a corpus becomes a vocabulary as one routed run.** `DocumentAgent`
  extracts and `KGAgent` curates; between them sat a join every caller was wiring by hand. Three
  calls in a fixed order with one stateful object threaded through them is a pipeline, not an idiom,
  and hand-wiring it also forfeited what the engine gives free: per-stage traces, progress
  streaming, per-stage timing. Stages are `ingest → emit → observe → propose → [decide] → [merge] →
  finalize`.

  **Ingest delegates rather than re-derives.** `DocTurn` already names a corpus five ways (folder,
  KH collection, zip, urls, blob pointers), so the ingest step runs the document pipeline and
  normalizes what comes back. A caller who already ingested passes `documents` and the step is a
  pass-through, which makes this composable with a run that was going to happen anyway rather than a
  reason to ingest twice.

  **Deciding and merging are off by default, and the asymmetry is the point.** Observing and
  proposing read a corpus and fill a queue. Deciding admits into a domain's vocabulary and merging
  cuts a version, and a pipeline doing both unasked would make an unattended corpus enough to change
  what a pack means. `KGAgentSpec` already defaults to review-only for the same reason. Merge is
  additionally guarded on something having been accepted: a "new" version identical to the old one
  is worse than no version. Adoption stays outside the pipeline entirely.

  **A corpus and a case file are different questions.** Without `case_id` each document is its own
  case, which is what a policy library or a regulation set actually is. With one, the assertions are
  pooled into a single graph so `Coverage` is derived across the documents rather than per document
  — the whole reason `documents_expected` exists.

  `CorpusObservation` reports documents, assertions and **untyped** counts, with `typed_ratio`
  returning `None` for an empty corpus rather than a misleading 1.0. The untyped count is the
  diagnostic worth reading first: a largely untyped corpus grows a vocabulary's relationships and
  leaves its concepts untouched, and surfacing that as a number beats discovering it later as a
  puzzling proposal set. A failed ingest surfaces as a typed `Refusal` rather than an empty
  vocabulary, since proposing from a corpus that could not be read would under-count evidence
  silently. Registered in `PIPELINE_REGISTRY` as `vocabulary_build`.

- **A vocabulary can be put in front of a model both ways, and which way it was used is recorded.**
  japes had both halves — prompt formatting and a tool registry — and paired neither. `grounding.py`
  pairs them, because the question behind the pairing is a cost lever: does a cheaper model given
  the domain's vocabulary reach the answer an expensive one reaches? That is unmeasurable without
  knowing which path produced what, so attribution is the feature rather than bookkeeping.

  **Additive, never substitutive.** A graph built from documents is a lossy compression of them;
  when one stood in for loan documents the reasoner's confidence that all relevant data was present
  fell and approvals came back conditional. So the rendered context is deliberately a **summary of
  what the domain talks about**, not of what the documents say — no assertions appear in it, it is
  bounded, and truncation says so rather than ending quietly. Where a case graph is present the
  context also states what it omits and that the documents remain the source, since a model told
  what a graph contains and not what it lacks is exactly the situation that produced hedging.

  The tools are plain callables — a caller wraps them for whatever runtime it has — and they answer
  what a summary cannot: the cross-document view a reader of one document cannot assemble. An
  unknown concept comes back naming what is known, so a model that asked wrongly can correct itself
  without another turn.

  Attribution resolves to **tool when the graph was queried**, even if context was also shown: the
  context is always present once rendered, so crediting it whenever it appeared would make every
  assertion look context-grounded. Usage counts calls rather than availability, because "the tool
  was there" and "the tool was used four times" are different facts. The recorded path stamps the
  assertions produced under it, which closes the chain from grounding to evidence.

- **`DocumentAgent.emit_assertions`: extraction can now feed vocabulary construction.** The other
  half of `emit_entity` — the same admitted fields, the same provenance, a different shape. A domain
  object answers "what is this document about"; a graph answers "what does the corpus say", and only
  the second accumulates across cases.

  **Both ends are typed, which is the point.** An assertion whose subject and object are proper
  nouns states a fact and generalises nothing: it can propose a *predicate* to a vocabulary but never
  a *concept*. `subject_concept` on the spec says what an entity from these documents is;
  `field_concepts` names the fields whose value is another entity. Everything else is typed from its
  Python value.

  That inference is deliberately shallow. A string holding `"2026-01-01"` stays `xsd:string`,
  because inferring a date is parsing dressed as typing — and a wrong type is worse than a vague one
  when it is what a vocabulary gets built from. `bool` is checked before `int`, since Python makes
  the obvious ordering wrong. A spec that never said what its documents are about produces untyped
  assertions rather than a guess.

  Refused fields are not asserted: a sub-confidence value that was not good enough to store is not
  good enough to state. Section, confidence and the grounding path travel with each assertion, so a
  proposal built from them averages the extraction's own confidence rather than inventing one.

  Two tests run the loop end to end and show the difference the types make: a typed corpus grows
  both the concepts and the predicates, while the same corpus from an untyped spec grows only the
  predicates — thirty relationships and zero entities, reproduced from first principles.

- **`KGAgent`: a pack's vocabulary can be derived from its documents rather than hand-authored.**
  A pack manifest declares an ontology and `PackLoader` registers it, but it arrives as a file
  somebody wrote. The agent closes that loop — observe what a corpus asserts, propose what the
  vocabulary is missing, decide each proposal under the pack's admission policy, merge what was
  accepted — and is the next step of the collapse that already took policies and evidence types out
  of code and into configuration.

  **It owns one question and composes the rest.** Extraction already has a chassis: `DocumentAgent`
  ingests, classifies, extracts under an admission floor and emits with provenance, and its
  `emit_entity` is already ontology-scoped. What had no home is the *other* admission question — not
  "is this assertion good enough" but "should this enter the domain's vocabulary". So the agent has
  no `extract` and no `process`, and a test says so.

  `KGAgentSpec` is pack data: which admission policies are allowed, the accumulator's noise floor,
  and the thresholds guards resolve against. **Review-only is the default** — a pack whose vocabulary
  grows unattended has to say so — and an unknown policy name fails at construction rather than
  producing a lifecycle quietly missing a route.

  Three separations the tests pin, because collapsing any of them would look tidier and be wrong:
  a **refusal leaves a proposal pending**, since an unmet guard means *not yet* rather than *no*;
  the accumulator's floor and the admission bar are **two questions**, so clearing the first says
  nothing about the second; and **merging cuts a version rather than editing one** — the merged
  vocabulary is returned, the current one is untouched, and `adopt` is a separate act so a caller
  that merges to inspect has not silently changed what the next run is measured against.

  A merged vocabulary carries **no version** until its pack releases it: carrying the old one
  forward would let a changed vocabulary answer to a version describing something else. An accepted
  *conflicting* proposal replaces the existing definition, because accepting it was the decision
  that the corpus is right and the vocabulary is stale.

- **Vocabulary construction is run-scoped, through a pluggable accumulator.** Some questions are
  only answerable across a corpus: "this relationship appears in enough documents to be real" cannot
  be decided while looking at one. `accumulate.py` watches assertions as a run produces them, groups
  them into candidates, and emits proposals carrying what it saw — occurrences, distinct documents,
  which documents, and what the run covered.

  It draws the division that keeps the lifecycle honest: **the accumulator decides what is worth
  proposing, the lifecycle decides what is worth admitting.** A candidate seen once never reaches a
  reviewer at all — that is noise filtering, not refusal — while a candidate above the floor becomes
  a proposal whose admission may still be held to a higher bar. Collapsing the two would either
  flood a review queue or let a single mention edit a domain's vocabulary.

  Candidates are keyed by **shape**, not name: the same predicate asserted between different
  concepts is two candidates, because merging them would invent a relationship nobody observed.
  Occurrences and distinct sources are counted separately, since five appearances in one document
  is not the evidence twice-in-two-documents is, and a guard downstream has to be able to tell.
  Confidence is reported separately from frequency — a candidate can be frequent and uncertain, or
  rare and clearly stated, and a reviewer needs both numbers.

  Conflict is decided narrowly and mechanically: a predicate the vocabulary already defines,
  asserted with a different shape. That is a real disagreement somebody must settle and the only
  kind detectable without a model; anything subtler is a judge's question.

  Output is deterministic — same corpus, same proposals, same order, same ids, derived from the
  candidate's shape rather than generated. A reviewer whose queue fills with fresh ids for
  candidates they already judged stops trusting the queue.

- **A vocabulary proposal has one lifecycle and several ways into it.** A concept entering a pack's
  vocabulary is a governed act — proposed, matched against what exists, admitted or refused — and
  that shape had no home. `proposal.py` gives it four states (`proposed`, `accepted`, `merged`,
  `rejected`) over `jazzx_sdk.statemachine`, and supplies the admission policies as composable
  transition sets rather than as alternative implementations.

  A studio reviewer approving, a relationship seen across enough documents to be real, a judge
  model's verdict, and a trusted import are **four transitions into one state**. The differences
  live in `trigger_type`, `actor_class` and `guard`, which is where a status enum that grew
  `ACCEPTED`, `AUTO_ACCEPTED` and `APPROVED` had been trying to record them: those were never three
  states, they were one state reached three ways with the trigger smeared into the name.

  A pack composes what it allows — `proposal_lifecycle(AdmissionPolicy.review(),
  AdmissionPolicy.frequency())` — and review-only is the default, so nothing enters a vocabulary
  unattended unless a pack says it may. `merge` is added unconditionally, since a lifecycle that can
  decide and never take effect is not one. **Accepted is not merged**: approving one proposal must
  not release the pack.

  The frequency guard compares **distinct sources**, not raw occurrences: five appearances in one
  document is a repeated phrase, twice across two is a pattern. A guard is a single comparison, so
  the occurrence floor sits upstream in the accumulator — what is worth *proposing* and what is
  worth *admitting* are different questions. Both guards fail closed: a thin candidate is refused,
  and a missing threshold refuses rather than assuming one.

  Evidence is first-class on the proposal — occurrences, distinct sources, which documents, what it
  was accumulated over — rather than a bag keyed by whichever system produced it. Guard values are
  read from that evidence, so a frequency guard cannot be satisfied by numbers disagreeing with what
  a reviewer sees. And one `Proposal` type with a `kind` discriminator replaces parallel concept and
  relationship classes that shared a lifecycle, an evidence shape, a category and their
  serialisation.

- **The two graph objects are named apart: `Vocabulary` and `CaseGraph`.** Three independent efforts
  each produced a different graph shape because the schema graph and the instance graph were never
  distinguished. They have different lifecycles -- a vocabulary is a released artifact with a version
  and a rollback; an assertion is evidence with provenance and a confidence -- and conflating them is
  what made each effort re-derive its own.

  **A vocabulary is a closure.** Concepts reference parents, relationships reference the concepts at
  each end, so `jazzx_sdk.closure` walks it, reports what did not resolve, and digests what did.
  Validation and version identity therefore come from a primitive that already existed: a
  relationship pointing at an undefined concept is an unresolved reference, not a special-cased
  error. A literal target (`xsd:decimal`) resolves rather than dangling, since it points outside the
  vocabulary on purpose. It versions **with** its pack -- one release, one closure, one rollback.

  **A case graph reports its coverage**, and that is the point of it. A graph built from documents is
  a lossy compression of them; standing one in for its sources cost a reasoner the ability to tell a
  sparse graph from a complete one, and approvals came back conditional rather than approved. So
  `Coverage` states which documents were read, which expected ones were not, and what fraction of the
  vocabulary is represented -- and an *unstated* expectation is never reported as completeness, which
  is the exact failure it exists to prevent. It reports the ratio and refuses to judge it: what
  counts as sufficient is a policy decision.

  **`Assertion` types both ends.** A triple whose subject and object are proper nouns can propose a
  predicate but never a concept, because nothing says what kind of thing either end was -- the
  mechanism behind a real promotion set of 30 relationships and zero entities. It extends `Triple`
  rather than replacing it, so prompt formatting, merging and the store keep working, and it records
  whether the vocabulary reached the model as context or as a tool, without which the
  cheaper-model-with-grounding question cannot be measured.

  `jazzx_sdk/closure.py` arrives here from the Plato branch, byte-identical, since it is SDK-level
  and gate-independent.

### plato 0.1.1

- **`jazzx_sdk` and `plato` are lint-clean, and three tests that never ran now do.** A sweep of
  208 findings, most of them mechanical, but two kinds were not.

  Twenty-two names appeared only in annotations and were imported nowhere. `from __future__ import
  annotations` kept them from raising, which is why nothing caught it, but the names stayed
  unresolvable: `typing.get_type_hints()` on any of them raises. That is the exact shape of the
  failure that made every route 422 twice on this branch. Each now has a real import, under
  `TYPE_CHECKING` where it is annotation-only.

  Two test classes shared a name, so the first one's three tests were silently discarded by the
  second. The two are not duplicates: the live class registers **async** hooks and the shadowed one
  registers **sync** hooks, so deleting the shadowed class would have dropped a calling convention
  from coverage entirely. Renamed instead, and both now run.

  Left alone: 69 stylistic findings in tests (semicolons, import order, a pytest-fixture false
  positive), none of which is a defect. Also left, and noted at the site rather than tidied away:
  the mock Knowledge Hub's `search_documents` resolves a collection id and then ignores it,
  fabricating five results regardless of what the caller stored. A test that populates a collection
  and searches it is asserting against invented documents.

- **An out-of-range `reasoning_effort` is named before the API rejects it.**
  `unsupported_request_params` said which *params* a model rejects; nothing said which *values* of
  the reasoning param it takes, so an effort the model does not accept reached the API and came
  back as a 400 whose message does not name what would have worked. Cards now carry
  `reasoning_efforts`, and `unsupported_reasoning_effort()` reports the mismatch alongside the
  values that would have.

  **Advisory, and deliberately so.** The guard warns and sends rather than refusing. These lists
  are authored per model and go stale the moment a vendor adds a tier; a guard that refused on a
  stale list would block a call that works, which is strictly worse than the 400 it replaces. A
  wrong entry costs a spurious warning instead. Empty means "unknown", never "none allowed", so a
  model whose list has not been authored stays silent rather than warning on every valid effort.
  Populated for the gpt-5.6 family only, where the accepted set is confirmed.

- **The durable model overlay covers cards, not just pricing.** Phase 5 task 4 half-landed: an
  operator could correct a rate without a deploy but not a context window, though both are
  reference data and neither is code. A window that ships wrong caps every request short and a
  reasoning flag that ships wrong changes which parameters get sent, so both need fixing without a
  release. `put_card` writes on the same append-only trail and `apply_overlays` applies both kinds.

  No migration: the row already carried a `kind` column, which the read had simply hardcoded to
  `pricing`. The two kinds are read separately rather than merged into one mapping, or whichever
  was written second would silently discard the other. Tuple-valued card fields are restored on
  the way back, since JSON has only lists and a card carrying a list where the codebase expects a
  tuple works until something hashes or compares it.

- **`EvalServiceClient` now covers what a consumer had to write for itself.** A service injecting
  approved feedback into its own system prompt needed four things beyond the HTTP read, and each
  was being written per-service -- which is how a limit ends up enforced in one place and not
  another. `list_static_feedback` joins `get_feedback_config` and `find_similar` on the client;
  `evaluation/feedback_render.py` holds the rest.

  The split is deliberate: the client does I/O, `feedback_render` shapes text. `clamp_top_n` bounds
  what a *remote* config may request, because `max_results` is authored in eval-service and would
  otherwise let one service decide how much text lands in the highest-trust slot of another's
  prompt. `cap_block` bounds the rendered size separately, since a handful of very long entries is
  the other way to blow a prompt and an item count cannot see it. `render_feedback_block` falls
  back to plain bullets when a template is missing or broken, so a mistyped template costs the
  formatting rather than the reviewer's instruction.

  Two things japes already had and did not need a second copy of: `normalize_feedback_text` unwraps
  a feedback row that stored a JSON envelope instead of prose, and `render_prompt_template` is
  already the sandboxed fail-soft renderer -- its docstring even notes that callers were each
  building their own. The sandboxed environment gained `trim_blocks`/`lstrip_blocks` so an
  operator-authored template renders the same here as elsewhere in the estate.

  Error containment is now stated on the class and applied uniformly: these reads may never raise
  into a live turn, and the catches are broad on purpose. `httpx.InvalidURL` -- raised for a
  malformed base URL, such as an unclosed IPv6 bracket in a misconfigured environment variable --
  is not an `httpx.HTTPError` subclass and escaped the narrower handlers that were there.

- **`evaluation/README.md` describes what shipped.** It claimed "Phase 1 Complete (v1.6.0)" and
  listed L3 review, the harness and the UI as "coming" long after all three landed, so a reader
  orienting from it concluded the opposite of the truth. It now maps every stage to its module,
  points at the end-to-end test as the place the handoffs are visible, and states the known gaps
  rather than leaving them to be rediscovered.

- **The mock Knowledge Hub client no longer differs from the real one, and two `RAGStore` calls
  that could never have worked are fixed.** Reported from an outside build as "`fabric.rag` does
  not work against `local_fabric()`". The diagnosis was the mock; the mock was the smaller half.

  `RAGStore.create_collection` passed `metadata=` and `RAGStore.retrieve_by_metadata` passed
  `limit=`. **Neither parameter exists on the real Knowledge Hub client**, so both calls would have
  raised `TypeError` against a real deployment; `create_collection` had therefore never worked
  against one. A broad `except Exception` reported each as
  `KnowledgeFabricError("Failed to ...")`, which reads as a service outage rather than a signature
  mismatch, and the mock accepted both because it had grown parameters the real client never had.
  Both are now applied client-side, the same treatment `search`'s own `limit`/`metadata_filters`
  already had, and both are documented as not reaching the endpoint.

  The mock's signatures now match the real client's exactly, including order and required-ness:
  `create_document` had `**kwargs` swallowing `document_type`/`indexing_enabled`, and had made
  `collection_id`/`content`/`name` optional, so code omitting them passed every test and failed in
  production. Its `search_documents` also ignored the collection and fabricated five documents per
  call, so a test that populated a collection and searched it asserted against invented content and
  passed regardless of the code under test; it now searches what was stored.

  A parameter-parity test already existed with all three methods on a known-drift allowlist -- the
  drift was tracked and deferred, and the exemption is what let it reach a real build. The
  allowlist is now empty, the comparison is order-sensitive (mapping equality is not), and a
  separate check refuses `**kwargs` on the mock, since an argument accepted and discarded is the
  failure that looks most like success.

- **The learning loop's routing stage no longer discards provenance, and its tag vocabulary is
  actually extensible.** Composing the loop end to end for the first time surfaced both.

  `CuratorQueueEntry` flattened an `ImprovementSignal` to a tag and a string, dropping
  `attribution_id` and `evidence_ids` -- the provenance `learning_candidate_to_signal` exists to
  attach. A governed learning candidate and a raw thumbs-down reached synthesis
  indistinguishable, so the governance established one stage earlier was undone by the next. The
  entry now carries the whole signal; the flattened fields stay, so existing readers are
  unaffected. That also lets Layer 1 feed Layer 2, which previously could not be written as a
  pipeline at all since routing returned one type and synthesis took another.

  `Feedback.to_signal()` copied `category` straight into the tag, and the router validates tags
  against a registered set. So `from_case_result`, japes' own factory for turning an evaluation
  result into feedback, emitted `eval_fail` and had it rejected: the automated half of the loop
  discarded every signal it created, and human feedback worked only because a human happened to
  pick a registered word. The tag is now mapped rather than copied, with the original category
  preserved in `context` and a platform fallback.

  `VALID_SIGNAL_TAGS` was an alias of the defaults, so a pack "injecting its own tags" -- which the
  module's comment invited -- mutated the platform set for every other pack in the process.
  Platform tags are now separate from the two AML-specific ones (`sar_template`,
  `typology_threshold`, kept registered because jaci routes them), and `register_signal_tags()` is
  the mechanism the module always described and never had.

- **Concurrent migrators are serialized, and schema work gets its own timeouts.** Plato is
  deliberately multi-replica, so a rollout starts every replica at once and each runs
  `upgrade head` against one database; they then race on an ACCESS EXCLUSIVE lock and the deploy
  fails. A session-scoped advisory lock now means one replica migrates and the rest block, then
  find the work done and no-op. Session-scoped rather than transaction-scoped because alembic
  commits between revisions, and a transaction lock would release at the first commit.

  `lock_timeout` (30s) bounds how long a statement inside a migration waits for a table lock;
  `statement_timeout` (30min) replaces a server default tuned for queries that would kill a
  backfill part-way. The advisory-lock wait itself stays unbounded on purpose: a replica queued
  behind another migrator should wait, not fail. The unlock rolls back first, or a failed migration
  leaves the transaction aborted and the release silently never runs.

- **OpenAI cache-write tokens were billed at the input rate.** `ModelPricing` has carried a
  `cache_creation` rate for a long time and `compute_cost` has always accepted the tokens, but
  nothing populated them from an OpenAI response, so on the families that bill cache writes every
  cost figure, trace and budget understated. The Anthropic provider already did this correctly on
  both its paths, which makes it a symmetry gap rather than a missing feature.

  Both OpenAI paths now read the field, under either of the two names the API surfaces use, and
  subtract the writes from the uncached remainder: they are part of `prompt_tokens`, not additional
  to it, so billing them at the higher rate while still counting them as input charges twice.
  Usage extraction moved to a module-level `extract_usage` so a test can exercise the real
  arithmetic instead of restating it.

  Known and left alone: the long-context tier defines no `cache_creation`, so a write in a prompt
  over the threshold is billed at that tier's input rate. Whether the vendor charges a premium
  there is unconfirmed, and a guessed rate would be worse than a recorded assumption.

- **A BPMN/DMN repository can be walked as a reference graph.** `closure.py`'s `Resolver.expand`
  docstring named this case as its reason for existing, and shipped with nothing able to read BPMN:
  the seam was there and empty. `jazzx_sdk/bpmn.py` fills it, which is step 1 of the promotion
  retirement path and gate-invariant.

  It walks call activities and decision references to a fixed point, so a process called two levels
  down is in the closure rather than a deploy that fails on its first step, and it pulls in the
  tools, agents and decisions that only a process's *content* names. Lookup is by key first and
  display name second, because the estate's authoring path writes a display name into the field a
  key belongs in; a name matching two definitions is reported as ambiguous rather than picked, since
  picking one yields a stable digest for a graph nobody chose. Expression-valued references
  (`calledElement="${nextProcess}"`) are carried as unresolvable rather than dropped, and they
  change the digest, so an incomplete closure cannot be mistaken for a complete one.

  **The parsing is `common.refs`, not a second implementation.** That is the shared extractor every
  other dependency graph in the estate is built from, and two parsers of one format drift until what
  a release bundles and what a dependency view shows disagree. The `common` submodule moved 29
  commits to origin/HEAD to pick it up; the full suite passes against the bump.

  **The walk crosses component kinds.** A process names things in its own XML, an agent names them
  in its descriptor, and a tool's *executable* calls further tools and agents that neither of the
  first two mention. A closure that stopped at the first tool leaves those uncreated wherever the
  release is applied. `ComponentSource` supplies content for the kinds a BPMN export does not
  carry, and the walk continues through them to a fixed point across kinds, cycles included.
  Without a source they stay terminal, because a resolver that guessed at content it does not have
  would report a closure it never walked. Components are fetched once each however many references
  reach them, since a real source is a network call per fetch.

  One exception, and it is one because the shared extractor answers a different question:
  `dmn_decision_ids` reads what a DMN document *defines*. `common.refs` reports outgoing references,
  and a document's own identity is not one, so without this a `decisionRef` could never resolve to
  the DMN carrying it and a missing decision would look the same as a present one. Identity only,
  so there is still one implementation of what a document points at.

  `defusedxml` is now an optional dependency behind the `bpmn` and `plato` extras. `common.refs`
  requires it, and the one local read uses the same defused parser rather than the standard-library
  one, which is documented as vulnerable to entity-expansion denial of service.

- **An assistant can be frozen into a digest-addressable release.** Phase 2's gate-invariant half:
  the parts of versioned config that no answer to "who owns the durable store" can invalidate.
  `jazzx_sdk/agents/interactive/release.py` produces and validates a release as a *value*. It
  stores nothing and reads no database, which is exactly what lets it exist before that decision
  lands; whoever ends up owning the store stores these values unchanged.

  **Pins, not names.** Every dependency enters the digest as `(kind, name, version)` with its
  content digest. That is the single property making the acceptance criterion hold: publishing a
  new version of a skill cannot alter an existing release, because the release never referred to
  "the skill", it referred to version 3 of it. A name-keyed digest follows the registry forward,
  which is the failure a release exists to prevent, and it is also how the whole thing gets faked:
  such a digest is stable across a rollback for the uninteresting reason that names did not change.
  So the tests move content under a stable name and assert the digest notices, then move the
  version and assert existing releases do not.

  The plan's definition of done passes: rollback reproduces the same closure digest *and* the same
  effective spec on a graph whose registries have since moved.

  Validation is `ProfileRegistry.validate()` called against the frozen set, not a fork of it.
  Whether a graph is admissible does not depend on where its members came from, and a second
  implementation would drift from the one every boot exercises. It runs *before* the digest is
  taken, since a digest over a graph with a dangling reference is stable, trustworthy-looking, and
  describes something that cannot run.

  One trap found and closed: `ProfileRegistry.register()` keys off `spec.name` while the closure
  walk keys off the mapping key. When those disagree the graph is validated under one identity and
  digested under another, and both steps pass while describing different things. Now a refusal.

- **A service details page at `GET {prefix}/info/ui`.** One self-contained HTML file: no build step,
  no CDN, no external font. A deployed service fetching an asset from someone else's host is a
  dependency nobody reviewed and a CSP exemption nobody wanted.

  It fetches `/info` from the browser rather than being rendered server-side, so the contract has
  one shape and Refresh does not reload the document. The schema banner is the reason the page
  exists, so it is not one card among many: current reads green, a mismatch reads red and says the
  container should not be serving, and *cannot verify* reads amber rather than red, because "no
  answer" is not the same as "the answer is no".

  It sits behind the same identity requirement as everything else. Exempting it would create an
  unauthenticated route, which is exactly the posture a deployed start refuses; reached without
  identity headers the page explains that instead of rendering blank, and an `x-user-id` field
  makes it usable locally by adding a header client-side while asking nothing of the server.

- **Versions and the commit, together.** The page and `/info` now report every version available
  (`plato`, `sdk`, `common`) plus the commit that produced the image. A version says what a
  container claims to be; a commit says what it contains, and they diverge on exactly the case
  worth diagnosing -- a rebuild from a branch, a hotfix with no version bump.

  `common` is the awkward one and worth stating plainly: it is a git submodule whose packaging
  version has been static for a long time, so its *commit* is what identifies which one is
  installed. Both are reported, since an operator who looks for a version and finds the key missing
  assumes the lookup is broken.

  The commit is read from the environment first and a working tree only as a fallback, never
  merged, and `source` distinguishes the two so a page showing `working tree` tells the reader they
  are looking at a checkout rather than a built image. `Dockerfile` takes `JAPES_GIT_COMMIT` and
  `JAPES_COMMON_COMMIT` as build args; without them a built image honestly reports the commit as
  unknown, since no `.git` reaches the runtime stage. These stay plain ARGs rather than BuildKit
  secrets: a commit sha is not a secret, unlike the dependency token in the same file.

### Earlier on this branch

- **A container refuses to start against a schema it was not built for.** A service version says
  which code is running, not which schema that code expects, and the gap between them is the
  classic deploy failure: a replica rolls out ahead of its migration, every write touching a new
  column fails, and the symptom is scattered 500s rather than "this container should not have
  started". An orchestrator sees a healthy process and sends it traffic.

  `plato/schema_version.py` compares the migration tree's head against the database's recorded
  revision, and the entry point refuses on a mismatch with its own exit code, the same stance
  `check_posture` already takes there. Both directions refuse: a database *ahead* of the image is
  refused too, because a newer migration may have dropped something the running code still writes
  and "probably compatible" is not a property this can check.

  The expected revision is read from the migration tree rather than pinned in a constant, since a
  constant is a second declaration that can disagree with the migrations, and the failure mode
  would be a service refusing to start over a number nobody had updated. Unmigrated is reported
  distinctly from mismatched: different mistake, different fix. **No environment variable disables
  the check** -- an escape hatch on a safety check is set once during an incident and inherited by
  every deployment after it; a caller with no database simply does not call it, and the unreachable
  case is reported as its own message so "cannot answer" never reads as "the answer is yes".

  Alembic's version row is now pinned to `plato_control` rather than left to the connection's
  search path, so the revision sits with the configuration it describes. That schema is created in
  `env.py` before the migration body runs, because alembic writes its version table first and the
  migration's own `CREATE SCHEMA` would come too late.

- **`config_info()`: one call for what a process is running.** The SDK's version was reachable only
  by importing it, the model inventory only by calling `list_model_cards`, and which optional
  dependencies an image actually shipped was not answerable at all. `jazzx_sdk.config_info()`
  gathers versions, the resolved default model and carded inventory, optional-package presence, and
  the non-secret fields of a `FabricConfig`. Plato serves it at `GET {prefix}/info`, adding its own
  version, the resolved role, and the expected-versus-actual schema revision.

  Distinct from `server/settings_api.py`, which edits a caller-declared catalog and is a write
  surface. This one is read-only and derived, so it cannot go stale against what is installed.

  **No secret values, not even masked.** A mask still discloses length and invites "just the first
  four characters" as the next change; what an operator needs is whether a credential is
  *configured*, which is a boolean. The subtle cases set the policy: `DATABASE_URL` and
  `APPLICATIONINSIGHTS_CONNECTION_STRING` carry a password and an instrumentation key inside
  strings that look nothing like credentials, and a surface reporting "just the config" publishes
  both. So credentials are an allowlist of variables known to carry secrets, reported as
  present/absent, and the `FabricConfig` summary names its safe fields one by one rather than
  dumping the model -- a dump would carry `api_key`, and would keep carrying whatever secret field
  is added to that model next. A test asserts a field added later is absent rather than included.

  Extension is by composition (`extra=`) rather than a registration hook, because `jazzx_sdk` must
  not import its consumers.

- **`docs/DEPLOYMENT_ENV.md`: every environment variable a deployment reads**, derived from source
  rather than from a working deployment. It surfaces something a running instance would not: with
  the default `common` database backend, six of `common`'s settings fields have no defaults, so a
  missing one fails at import with a pydantic validation error naming the field -- which looks
  nothing like the database problem it actually is. None of the six are `JAPES_`-prefixed.

- **Plato has its own version, on its own clock, and services now report the one they declare.**
  `plato/_version.py` starts at 0.1.0, mirroring `jazzx_sdk/_version.py`'s shape.

  Separate rather than shared because the two answer different questions. `jazzx_sdk`'s version is
  what a consumer pins, so bumping it is a release to every repo that installs japes. Plato's
  identifies a deployed image. Fusing them would mean a Plato deploy required a library release,
  and a japes patch silently renumbered a running service that had not changed.

  Plato takes no `pyproject.toml` version and needs no sync test: it ships inside the `japes`
  distribution behind the `plato` extra, so it has one declaration and nothing to drift from. The
  SDK needs its sync test only because poetry-core requires a static version in `pyproject.toml`.
  Adding a second declaration for Plato would create the problem that test exists to catch.

  Surfacing it exposed a standing bug: `create_app` advertised a hardcoded `version="0.2.0"` while
  the SDK was at 2.4.7, so every service built on it, in every repo, reported a version that had
  been wrong for a long time and that nothing checked. It is now an `app_version` parameter
  defaulting to the SDK version, so an existing caller gets a true answer without changing, a
  service passes its own, and a deployment that genuinely wants an API version distinct from either
  can say so. `/health` reports it alongside the handler name, since `/docs` is routinely disabled
  in a deployment while `/health` is what an operator can reach.

- **Plato's schema is now something a deployment can create, and the three untenanted tables were
  fixed rather than recorded as debt.** Plato owns five schemas and six tables but had no migration,
  so a deployment's only route to a schema was `create_all()` -- which builds from whatever stores
  happened to be imported, and cannot place a table in a schema at all.

  The larger finding came first. `DbTurnRunStore` and `DbConfigAuditStore` had no tenant column, so
  in a multi-tenant deployment one tenant's run id could collide with another's and `history()`
  returned every tenant's audit trail. Nothing released depends on the old shape (verified across
  the sibling checkouts: nothing deploys either store), so both were corrected at the model rather
  than migrated later: `tenant_id` joins both of `turn_run`'s and `turn_run_event`'s composite
  primary keys, `config_audit_event` gains a `(tenant_id, event_id)` unique constraint, each store
  is scoped at construction, and all twelve query sites filter. `plato.tenancy.find_untenanted_tables`
  now returns nothing, where it previously named three tables.

  `plato/models.py` is the one place every Plato-owned store is imported, so the table set is
  enumerable rather than emergent -- a module that quietly stopped being imported would otherwise
  drop its tables out of the migration chain without failing anything. It deliberately excludes
  `japes_feedback`: eval-service is the system of record, and a second durable copy makes "which one
  is right" a question somebody answers under pressure. A test asserts the absence.

  Schemas are assigned in the migration, not on the models, so the models stay portable to sqlite,
  which has none. That means the two can drift, and drift here fails only when a deployment's table
  is missing a column the code writes to. So the migration is **run** under test and its output
  compared column-by-column against the registered metadata, rather than its source being read --
  a `create_all` comparison could only ever agree with itself. The migration is dialect-aware for
  this reason, and reversible, which a release that has not shipped yet should be.

- **A pack can be read from anywhere, not only from a directory.** `load_pack` read the filesystem,
  which quietly made a new tenant a deploy: the manifest was durable in `plato_control` while the
  profile, personas and skills that give it meaning were files in the container image. That is the
  opposite of what Phase 1 claimed, and on jaci's scale it is ten scenarios' worth of
  `pack_manifest.yaml` / `pipelines.yaml` / `document_agent.yaml` with no durable home.

  `plato/packs/sources.py` splits *where the bytes come from* from *what they mean*, the same split
  `fabric` already makes for blobs and databases. It differs from those in one respect and
  deliberately: `BlobStore` and `DbStore` take a `backend="..."` string because their backend set is
  closed and small, while a pack can arrive from a directory, a bundle, a config store that does
  not exist yet, or a tenant upload. A protocol stays open to the fourth without editing the first
  three.

  Three sources ship: `DirectoryPackSource` (the authoring loop, and still the default),
  `BundlePackSource` over the existing `pack_bundle`/`unpack_bundle` so zip-slip protection is
  inherited rather than reimplemented, and `MappingPackSource` for bytes from anywhere else. The
  last is the seam Phase 2 lands on: `ConfigAssetVersion` rows resolve to exactly that shape, so
  adopting a durable store is a new caller rather than a change to `load_pack`. A bare path still
  works, so no existing caller changes.

  The tested property is **equivalence**: the same pack from all three sources yields the same
  manifest, profile and skills. If that stops holding, behaviour depends on how config was
  delivered, which is the failure the split exists to prevent. Files are materialised to a temp
  directory so `InteractiveAgentSpec.from_dir` does the parsing, reused rather than forked because
  a second mapping-based implementation of the same rules is a place for the two to disagree about
  what a pack means; the cost is one write at composition time, not per request, and a test asserts
  nothing is left behind.

- **The sqlparse CVE floor is scoped to the `mlflow` extra, matching what landed on `main`.** It was
  declared non-optional, so it installed for every consumer, and japes imports it nowhere: it
  arrives only through `mlflow-skinny`. Now optional and listed in the `mlflow` extra.

  The floor itself stays, and the comment now says why it cannot be inherited: `mlflow-skinny` asks
  for `sqlparse >=0.4.0,<1`, a range that still admits the vulnerable 0.5.5, so bumping mlflow alone
  does not close the CVEs. A PR review suggested dropping the direct pin on the argument that mlflow
  would enforce it transitively; that would have reintroduced all four.

  Brought back from `fix/vulnerabilities` rather than cherry-picked: that commit's `poetry.lock` was
  generated against a `main`-based lock with no alembic or import-linter, so it would have fought
  this branch's. Same pyproject change, re-locked here.


- **`MockKnowledgeHubClient(data_dir=...)` finishes what its docstring promised (issue #57).**
  The docstring said entities were "saved to / loaded from" `data_dir`; nothing wrote them back, so
  a caller believed cross-process persistence worked and got an empty store with no error.
  Entities, ontologies and documents were wired since the issue was filed. Collections and policies
  were not, and that was the worse remainder: documents persisted while the collections holding
  them did not, so a round trip restored documents whose `collection_id` named a collection that no
  longer existed and `list_documents(collection_id=...)` found nothing. Data present and
  unreachable is harder to diagnose than data plainly absent.

  Both stores now persist and reload, and a collection delete writes both files, since the cascade
  to its documents already happened in memory. The name-to-id index is rebuilt on load rather than
  stored: two files that must agree are a way for them to disagree. The docstring now names every
  file it writes instead of one.

  **A second bug fell out of writing the tests.** `list_collections` returned three hardcoded
  collections and never read `self._collections`, so a collection created through
  `create_collection` was invisible to it *within the same process*, and the canned entries carried
  document counts (42, 15, 128) matching no document the mock ever held. It reads the store now.
  The canned data is deleted rather than kept as seed: nothing in japes or any sibling repo
  referenced those names, and anything that had been relying on them was relying on a fiction.

  Issue #57's second item, `FabricConfig.validate_for_mode()` demanding `knowledge_hub_url` for a
  Mock client, was already fixed: `has_client` is threaded from `KnowledgeFabric.__init__`, and it
  relaxes for any supplied client rather than special-casing `is_mock`, on the reasoning that the
  URL exists so something can build a client and is redundant once one is handed over.

- **A registry's contents can be exposed as MCP tools, which is how a configured assistant becomes
  callable by another agent.** `kernel_tools.py` and `knowledge_hub_tools.py` hand-write their
  tools, which is right for a fixed surface and wrong for anything a deployment configures: a
  tenant's assistants are not known at import, so a hand-written tool per assistant means a code
  change per assistant.

  **The registry says which items, an adapter says how to call one.** The first sketch was "expose
  any `NamedRegistry`", and thinking it through killed that: the registries are not homogeneous in
  the way that matters. `ProfileRegistry` holds specs that run a turn and `GuardrailRegistry` holds
  `check(text)` callables, but a `Skill` is a spec fragment with no meaning outside a parent agent
  and a `SchemaRegistry` entry is a pydantic class that is not callable at all. A blanket seam
  would have emitted broken tools for two of five. An adapter that returns `None` for an item it
  cannot express is what keeps that honest, and declining is tested as carefully as succeeding.

  **Authorization reuses the existing selector rather than inventing one.** An exposed assistant is
  admitted through `admit_hop(f"assistant:{name}")`, character for character what
  `_build_composed_skill_tool` checks for in-process composition, because calling an assistant over
  MCP is the same act across a process boundary. A refused item is never registered, so a caller
  does not learn a capability exists by being denied it. A failed authority check fails closed.

  **Deliberately not mounted anywhere.** MCP carries no convention for the trace id and idempotency
  key `GovernedRouter` requires on every governed route, so a host exposing assistants this way
  would either invent one or route around its own governance. That is a posture decision for the
  mounting host and it is not made here. Prompted by eval-service exposing scorers over MCP, which
  is the same shape arrived at independently.

- **Tailing a run no longer polls every 100ms while nothing is happening.** `ResilientRunner.resume`
  polled at a flat 100ms whether or not the run was producing. Every SSE client holds one of those
  loops and each iteration is two queries, so a turn thinking for ten minutes before its first
  token cost roughly 6,000 iterations per connected client. The interval now widens while the run
  is silent and snaps back the moment it speaks.

  `concurrency.adaptive_interval` is the primitive, and the design decision worth recording is
  which loops it applies to. japes has five of this shape and they are **not one family**:
  sweepers (`Reaper`, `SessionReaper`, plato's `OverlayRefresher`) reconcile on a cadence with no
  endpoint, so widening one only makes reconciliation lag; waiters wait for one specific thing, so
  their cost scales with how long it takes. A test pins the sweepers as flat, so a later
  consistency pass cannot helpfully back them off.

  **Keyed on idleness, not the run's age**, which is where this departs from eval-service's
  `e1ca595` that prompted it. Their poller waits for a terminal state with no intermediate output,
  so age is a fine proxy. `resume` yields events as they arrive, and backing off on age would have
  delivered a long streaming turn in multi-second chunks: a regression in experience to save
  queries. Any event resets the clock. An explicitly passed `poll_seconds` stays flat, so a caller
  that had tuned its own cadence is unaffected.

- **A turn waiting on a slow model was reaped as a dead worker.** `ResilientRunner.execute` beat
  once before opening the stream and then only *inside* the `async for` loop, so the entire window
  before the first event was unguarded. A reasoning model thinking for longer than
  `Reaper.ttl_seconds` (30s) emits nothing in that window: the heartbeat went stale while the
  worker was perfectly healthy, the reaper marked the run `FAILED` with "reaped: heartbeat stale",
  the dispatcher's FIFO gate released the conversation, and the turn's own completion later wrote
  over a run somebody had already been told failed. A 45-second first token is ordinary; the
  defaults made it a failure.

  Liveness now beats on its own timer, cancelled when the turn ends. "This worker is alive" and
  "here is my progress" had been sharing a trigger and are different things: the in-loop beat still
  snapshots partial output, while the reaper's signal no longer depends on the model producing
  anything. A missed beat logs and continues rather than ending the loop, since a transient store
  error should not get a healthy run reaped.

  Found by reading eval-service's `e1ca595` ("stop the poller failing a process that is merely
  slow"), which hit the same class of bug from the other side: a watcher whose deadline marked
  failure rather than merely stopping watching. japes reaps on heartbeat staleness rather than a
  wall clock, which is the better shape, and still had the hole. Mutation-verified: reverting the
  runner change fails the test.

- **A spec can name its structured output, so a composed assistant can finally have one.**
  `InteractiveAgentSpec` had no `output_schema` field: structured output was a constructor argument
  only. Invisible for an agent built in code, and fatal for a composed `spec_ref` assistant, which
  is built from a spec and never from a constructor argument, so it could not have one by any
  route. `spec.output_schema` names a model in a new `SchemaRegistry`, resolved at build time.

  A name rather than a dotted import path, deliberately: a spec is data, written in YAML and read
  back from a store, and a dotted path would turn configuration into arbitrary code execution when
  configuration is exactly what a tenant is allowed to add. The registry takes the same name-keyed
  shape as `router`, `guardrails` and `skills`, refuses anything that is not a `BaseModel` subclass
  at registration rather than failing mid-turn, and inherits `freeze()` with the rest of the
  family. An explicit `output_schema=` argument still wins, so every existing caller is unchanged,
  and an unresolvable name warns and returns text rather than raising, since raising would make
  adding the field a breaking change for a deployment shipping a spec that names a schema it has
  not registered yet.

  **The backlog item this came from was two-thirds wrong, and checking beat building.** It asked
  for `guardrails`, `knowledge` and `output_schema` on `Skill`. The first two already work: a
  `spec_ref` skill resolves a full spec, whose own guardrails and knowledge apply through the
  shared catalog and fabric, so adding them to `Skill` would have duplicated what the referenced
  spec owns with no rule for which wins. The item predates `spec_ref`, which did not satisfy those
  two so much as make them obsolete. Two docstrings claiming all three "apply, not flattened away"
  were true for two and false for the third; both are corrected.

  What crosses to a parent is JSON text, not an object: a function tool returns a string to the
  model by construction, and `InteractiveResponse.answer` already holds the schema's JSON. The
  parent gets something parseable instead of prose, which is the benefit; a typed object crossing
  that boundary is not available under the Agents SDK tool contract.

- **Registries can be sealed, so capability is decided before an instance serves rather than
  during.** A domain's extension point in v2 is skills and prompts, not code, which makes the
  registry the thing a use case or a tenant expands. That only holds if the expansion stops: a
  tenant skill registered after serving began changes what an already-bound agent can reach with
  nothing recording when or why. `NamedRegistry.freeze()` draws the line, and `RegistryFrozenError`
  says plainly that the caller is too late for the change to be reviewable.

  Guarded at `_put`, the one mutation point the whole family routes through, so `register`,
  `register_dict`, `load_dir` and the tiered writes are all covered without each having to remember
  the check. One-way on purpose: an `unfreeze` would make the guarantee conditional on nobody
  calling it, which is not a guarantee. `_frozen` is a class attribute as well as an instance one,
  so a subclass that never calls `__init__` reads as unfrozen instead of raising `AttributeError`
  on its first write.

  `plato.packs.loader.tenant_registries` is the composition that uses it: platform packs layer
  first at tier 1, tenant packs at tier 3, and both registries come back frozen. The tiering means
  adding a tenant pack cannot silently shadow a platform skill, while overriding one on purpose
  stays possible and still has to be written down.

- **kernel agents convert to `InteractiveAgentSpec`, and what will not convert is counted.**
  kernel is being retired in favour of japes patterns, and a strangler only finishes if the number
  of rows not yet moved goes down where somebody can see it. Tasks close without rows moving; the
  count does not, which is why it is the metric worth reporting.

  The mapping is not invented: `plan_kernel_salvage_hardening.md` already decided field by field
  what japes carries and what it rejects, and this implements that decision rather than reopening
  it. What it adds is that nothing is dropped in silence. Four outcomes, deliberately distinct: a
  field is *carried*, *superseded* (japes solves it better, and the replacement is named, so
  `max_steps` to `max_turns` is not filed alongside `learning_strategy` to the guidance layer),
  *carried elsewhere* (`autonomy` belongs on the manifest and `description` on the exposing skill,
  so they survive but the caller still has to place them), or *unresolved*. A row with anything
  unresolved is not counted as converted, the same discipline `jazzx_sdk.closure` applies: a
  partial result that presents as complete is worse than an obvious failure, because it gets
  trusted. A dangling `callable_agent_ids` entry blocks conversion rather than vanishing, since an
  agent whose sub-agent quietly disappeared routes to nothing at its first turn.

  Nothing here reads kernel's database. Rows arrive as dicts, so the converter is testable without
  a kernel checkout and japes gains no dependency on a schema it is retiring.

  A completeness test asserts every field kernel's `AgentCreate` declares is accounted for in one
  of the four categories, so a field added to kernel later surfaces as a failing test rather than
  as a value that silently stopped arriving. It earned its place immediately: it caught
  `reasoning_mode` and `text_verbosity` being handled inline rather than declared, which had made
  the declaration a second source of truth that could drift from the behaviour.

- **A retried feedback submission wrote a second row, and the code said the opposite.**
  `feedback_to_submission_v1` minted `event_id=uuid4()` per call while the sink's docstring
  claimed a blind retry was safe "because eval-service dedupes on that key". A key generated fresh
  per attempt cannot dedupe anything, so an ambiguous failure the caller retried turned one user's
  thumbs-down into two rows. `event_id` is now `uuid5` over the feedback's own id: stable across
  attempts, processes and restarts, distinct per item. One existing test asserted the old
  behaviour outright ("two calls generate distinct event ids"), so it encoded the bug; it is
  replaced, and the change is called out as deliberate rather than left to look like a break.

  Two more of the queue's four sub-tasks landed with it. `EvalServiceFeedbackSink` no longer
  inherits the broad local `FeedbackStore`: a new narrow `FeedbackSink` ABC carries `submit` and
  `append` only, and `list`/`clear` are gone rather than present-and-refusing, because a method
  that exists and raises is a worse contract than one that is absent (a caller typed against the
  wider interface type-checks clean and fails in production). And the calling request's identity
  headers are propagated on submission, so eval-service attributes feedback to the person who gave
  it rather than to the japes service account, which is what the attribution spine needs to be
  worth building. `content-type` cannot be displaced by an inbound header of the same name.

  The fourth sub-task, pointing at the agreed V1 route and response shape, stays blocked on
  eval-service publishing it.

- **`POST /v1/feedback` on Plato: a pass-through that stores nothing.** eval-service is the system
  of record, and a second durable copy would make "which one is right" a question somebody answers
  under pressure. What the route adds over calling eval-service directly is the two things a
  browser cannot supply for itself: the caller's identity, propagated rather than replaced by a
  service account, and an idempotency key stable across retries. A neutral reaction is refused
  rather than mapped, since the wire contract's reaction is binary and guessing would invent an
  opinion the user never gave; an upstream failure is a 502, which tells the caller to retry rather
  than reading as Plato being broken.

- **The `feedback` table name is eval-service's, and japes has stopped claiming it.** Both sides
  declared a table called `feedback` with different schemas and different lifecycle owners, while
  being expected to coexist in one Postgres instance. The japes table is now `japes_feedback`, and
  `assert_not_eval_service_database` refuses a database that already holds the contested name,
  naming both causes because from inside the guard they are indistinguishable: it is either
  eval-service's database, or a japes database from before the rename. **This needs a migration in
  any deployment already running `DbFeedbackStore`** (`ALTER TABLE feedback RENAME TO
  japes_feedback`); without one the store silently starts writing to a new empty table while the
  old rows sit unread. A test asserts no module in `jazzx_sdk` declares the old name, so a table
  added later fails without anyone having to remember the rule.

- **A pricing correction now reaches every replica, not just the one that took the request.**
  `register_model_pricing` writes a process-local dict, which is right for a consumer compiling in
  its own rates at import and wrong for an operator correcting a shipped rate at 2am: the
  correction lands on whichever replica served the call, every other one keeps billing the old
  number, and nothing reports that they disagree. `plato/reference/model_overlay.py` is the durable
  half, and the in-process `register_*` keeps exactly its previous meaning.

  Append-only, because a rate is a claim about money and overwriting the previous row would destroy
  the record of what was in force when an old trace ran; the newest row wins on read and the
  history stays queryable with its actor and reason. Applying is explicit rather than read-through,
  since costing is a hot path that must not touch a database: rows are pushed into the process
  table at boot and on a refresh tick, so a replica is at most one interval stale and that interval
  is a stated number. `OverlayRefresher` takes the same `sweep`/`run_forever` shape as the run and
  session reapers rather than inventing a third way to reconcile a replica. Durable overlays apply
  with `overwrite=True` deliberately: an operator correcting a rate has decided, and losing to a
  code-level registration would make the API look like it did nothing.

  Two bugs found while building it, both worth recording. sqlite rejects autoincrement on a
  composite primary key, so `tenant_id` sits in a unique constraint rather than the PK, which is
  weaker than intended and is now stated in the model rather than left to be discovered. And the
  schema assignment (`plato_reference`) belongs in the migration, not the model, for the same
  reason the other Plato stores omit it: sqlite has no schemas.

- **Plato requires `If-Match` on a settings write.** `settings_api` honours it when supplied but
  does not require it, deliberately, since requiring it in the SDK would break every existing
  caller. Plato has no such callers and the write edits configuration and secrets at runtime, so
  the blind write it would otherwise permit is a last-writer-wins race between two operators with
  no sign that either lost. `posture.require_if_match` refuses with 428 rather than 400: the
  request is well-formed and would be accepted with the header, and the client should re-read and
  retry rather than fix its body. It keys on the method, so a router that later grows a POST cannot
  quietly escape the requirement, and reads are untouched.

  Plato serves no SPA, and the SDK's `static_dir` gating was already correct, so that item is a
  test pinning the behaviour rather than a change: no mounts, `static_dir` unset, and an unknown
  path is a 404 rather than a catch-all returning HTML.

- **A tool catalog can now follow the turn instead of the agent.** `InteractiveAgent`'s `tools=`
  accepts a zero-arg callable as well as a dict, resolved fresh each turn. Found by trying to host
  `jazzx-assistant` on Plato and discovering the two are structurally incompatible: it builds a new
  agent every turn because its eleven file tools are each bound to that turn's grounding directory,
  while Plato binds once and caches per `(tenant, assistant, release)`. Rebuilding per turn to get
  turn-scoped tools defeats the reason for caching a bound agent at all. Additive and small: `tools`
  was already re-read on every turn, it was simply fixed at construction, so this changes where the
  value comes from and nothing else. Every existing caller passes a dict and is unaffected, which a
  test asserts directly.

- **`plato/packs/`: a pack is the manifest, profile and skills a host binds, as data.** The loader
  reads a directory of exactly the shape the estate's assistants already ship (`profile.yaml`,
  `persona.md`, `skills/*.yaml`) plus the manifest beside it, and registers it into shared
  registries so several packs populate one catalog, which is the multi-assistant case Phase 1
  exists to serve. A pack that is missing a piece fails whole rather than half-loading: a partial
  pack binds an agent whose skills silently do not exist, and the first symptom is a turn that
  cannot route.

  `jazzx-assistant`'s real profile loads and binds through Plato's runtime, with its three
  specialist skills resolving and its streaming flags carried through. Stated precisely, because
  the test proves less than the phase heading suggests: it stops at binding, since a turn against a
  profile with skills takes the agentic path and `ScriptedLLM` covers single-shot only, and it is
  skipped when the sibling checkout is absent, so it does not run on CI at all.

- **`jazzx_sdk.closure`: resolving a reference graph to a frozen, digest-addressable set.** Phase 2
  is gated on decisions that are not ours alone to make, so this is the part of it that no answer
  can invalidate: it sits in the SDK rather than in `plato/`, and whichever system ends up owning
  versioned configuration consumes it rather than rebuilding it.

  It exists because the obvious implementation is wrong in a way that hides. Walking an asset's
  declared references one level produces a digest that is stable and trusted and does not describe
  what will actually run. Four properties, each one a failure the estate's existing promotion path
  already shipped and fixed: the walk is a **fixed point** with a visited set, because a process
  calls a process calls a decision and the graph has cycles; **ordering is imposed at
  serialization**, never inherited from traversal, because a walk over a set has no inherent order
  and digesting in visit order makes two runs over identical input disagree; the digest is over
  **resolved identity**, because the same thing arrives as a key in one place and a display name in
  another and hashing what was stored makes identical content hash twice; and what could not be
  resolved is **carried, never dropped**, because an expression-valued reference that vanishes
  leaves a digest that is reproducible and incomplete, which is worse than an unstable one for
  being believed.

  Domain-neutral by construction: it knows nothing about processes, tools or BPMN. The caller
  supplies a `Resolver` saying how to resolve one reference and what a resolved node references in
  turn, which is where content-derived references enter the walk (a process's service task naming a
  tool no declared list mentions was a real production failure, not a hypothetical). It never
  resolves by name-with-create-if-absent, and a test asserts that by source: that upsert is the
  workaround an immutable release primitive exists to replace.

  18 tests, one per failure mode. Two mutation-verified: removing the sort breaks three ordering
  tests, and dropping unresolved references from the digest breaks the test that a silently-dropped
  reference would otherwise hash identical to a complete closure.

- **Two assistants, different manifests and personas, served from one running instance by writing
  configuration.** This is phase 1's whole claim and it now has a test that makes it: a second
  assistant is published into the durable store mid-test and the same process serves it, with no
  route added, no agent constructed by hand and nothing redeployed. Before the publish that
  assistant is a 404 on the same instance.

  `plato/runtime.py` is the piece `server/app.py` never had. It resolves `(tenant, assistant_id)`
  to a bound `InteractiveAgent` through `build_from_manifest`, and caches it on a key that carries
  `release_id` from the start even though nothing populates it until phase 2: adding a field to a
  live cache key later invalidates nothing and quietly keeps serving the old shape. The manifest
  itself is read every request, so a new release is noticed rather than waiting for a restart, and
  `invalidate()` exists for the write path that makes a bound agent stale. Registries are supplied
  per tenant through a callable, which is the seam phase 2 replaces with a lookup against released
  configuration.

  `plato/assistants_api.py` serves chat, durable streaming and sessions under
  `/v1/assistants/{id}`, on `GovernedRouter` like the rest of the server tier. Streaming is the
  existing `runs/` machinery rather than a second SSE implementation: a turn is submitted as a
  `TurnRun` and the response streams its journal, so a dropped connection resumes from a sequence
  number and a stop is a durable flag any replica can set. The stream names its run id before the
  first delta, because a client whose connection drops on that delta still needs something to
  reconnect with. The run store is not tenant-scoped, so ownership is recorded on the run at
  submission and checked on resume and stop; without that, a run id from any tenant streams to any
  other. A missing assistant, another tenant's assistant, and another tenant's run are all 404,
  never 403, since distinguishing them answers the question an unauthorised caller was asking.
  Continuing a session the sweeper already expired is a typed `Refusal` at 412, not a 500: the
  caller needs to know it may start a new session rather than retry something that cannot succeed.
  The streaming routes are absent, not broken, when no run store is wired, rather than advertising
  durability a deployment does not have.

  `plato/app.py` composes `create_app` through `extra_routes` rather than forking it, so CORS,
  identity middleware, health and the security headers stay in one place. It defaults
  `require_identity` on and runs the posture check even when a caller supplies its own settings, so
  opting out is not something a settings object can do quietly. `/invoke` refuses with a named
  reason and a pointer to the assistant routes rather than running something no configuration
  described.

  `plato/wiring.py` is the one seam a deployment fills: `PLATO_WIRING` names a `module:callable`
  returning a `PlatoWiring`, and every role in the image reads the same variable, so a sweeper job
  and a replica cannot disagree about which database they are on. A role that cannot resolve it
  exits non-zero rather than starting. `plato/jobs.py` runs the session sweep as a `job:*` role
  that completes and exits: as a background task in a replica it would run once per replica, so
  scaling out multiplies the sweeps and scaling to zero stops them. One tenant's failure does not
  end the sweep, and a sweep over no tenants warns rather than reporting success for doing nothing.

- **The durable stores are tenant-scoped, and the image no longer leaks its build credential.**

  Plato's phase 1 requires a request for another tenant's assistant to return 404 rather than that
  tenant's data, and `assistant_manifest_record` had no tenant column at all: Plato's own tenancy
  guard would have rejected it. Both durable stores gained `tenant_id` in a unique constraint
  rather than as a plain column, since a column is a filter a query can forget while a key is a
  constraint the database applies regardless. The scope is fixed at construction rather than passed
  per call, so a caller cannot omit it. A `DEFAULT_TENANT` keeps every existing caller working
  unchanged, and the column is present from the first migration, which is the only point at which
  adding it is free.

  Isolation is asserted rather than assumed: the same assistant id under two tenants holds
  different content and neither `put` demotes the other's head, a rollback cannot reach across, two
  tenants can hold the same caller-supplied session id, and one tenant's reaper leaves another's
  sessions alone. Both tables now check themselves against the tenancy rule directly.

  The Dockerfile took the shape kernel already proved. It had passed the GitHub token as a build
  argument, which is recorded in image history and readable by anyone who can pull the image; it is
  now a BuildKit secret, present only for the step that needs it. The build is two-stage, so no
  compiler, git or credential reaches the runtime image. `POETRY_INSTALLER_MAX_WORKERS=1` replaces
  the retry loop the estate has been carrying for the client-api double-clone failure: serialising
  the installer makes that race impossible rather than retried. A healthcheck runs the entry
  point's own `--check`, so a container without a runtime reports unhealthy instead of looking
  fine.

- **Queue dedupe is now asserted across a restart, not just across replicas.** The existing
  coverage shares an `InProcessQueueExecutionStore` between two runtimes, which demonstrates two
  replicas of one process. Azure Storage Queue is at-least-once, so the case that actually costs
  something is a worker that takes a message, dies, and comes back to find it redelivered with no
  memory of having run it. The new tests build a separate store per simulated worker over one
  database, with nothing shared in memory, and confirm the handler runs once. Verified by mutation:
  giving the second worker its own database makes it fail.

- **Plato verifies inbound tokens itself, and enforces tenancy before it has tables.**

  Nothing in this estate verified an inbound token. Every JWT reference across `japes` and
  `common` was outbound, a token being *sent*, and identity arrived as headers a gateway injected
  after doing the verifying elsewhere. UAF item 7 left "who verifies the token" to the service
  boundary; Plato is that boundary, and answers it in the direction that does not assume a trusted
  gateway sits in front.

  `plato/oidc.py` validates a bearer token against the issuer's published signing keys. No new
  dependency: `pyjwt` and `cryptography` are already core. Signing keys are cached, because a fetch
  per request makes the identity provider a hard dependency of every call, and rotation is handled
  by refetching when a token names a key the cache does not hold, which is the event that actually
  signals rotation rather than a timer guessing at it. That refetch is rate limited so an
  unrecognised key id cannot be used to hammer Keycloak, and one unusable key in a JWKS document
  does not void the rest. Verified claims map to the same shape `x-security-context` carries, so a
  verified token and a gateway-injected header produce the same identity and nothing downstream
  needs to know which path a request arrived by. Header-borne identity keeps working: verification
  turns on by configuring an issuer, and an unconfigured verifier refuses rather than accepting
  everything.

  Tested with real RSA keys and real signed tokens rather than a mocked verifier, which would
  prove the calling code works and say nothing about whether a forged token is rejected. Covered:
  a well-formed token from the wrong signer, an expired one, a wrong issuer, a token minted for a
  sibling service by the same realm, an unknown key id, and rotation.

  `plato/tenancy.py` requires `tenant_id` in a primary key or unique constraint rather than merely
  as a column: a column is a filter a query can forget, a key is a constraint the database applies
  whether or not the query remembered. The guard lands before any table exists, because
  retrofitting tenancy is not a schema change but a backfill against rows whose owner nobody
  recorded. It reports every offender at once, and its check against the live registry is vacuous
  today and committed deliberately, since it starts failing the moment a Plato table forgets.

  Keto wiring is deferred rather than written unverified: `keto_client` is not installed, so
  `common.core.keto` cannot be imported or tested here, and there are no routes to attach a
  permission check to until Phase 1. It is genuinely wiring when that time comes, since
  `Namespace.Assistant` already exists and `check_permission` is generic.

- **`scripts/run_tests.sh`** runs the suite and prints the failures plus the counts line, keeping
  the full output at a path. The suite is now large enough that a plain run buries its own result
  in the warnings summary, so the usual invocation had become pytest plus a redirect plus a tail,
  retyped slightly differently every time.

- **Plato refuses to boot deployed without identity enforcement.** `ServerSettings.require_identity`
  defaults to off in the SDK, which is right there: a library cannot know whether its consumer's
  callers send identity headers yet, and flipping it on would break them. It is not defensible for
  a multi-tenant service that serves assistant configuration and traces, so Plato decides otherwise
  for itself rather than asking the SDK to change its default.

  The failure this prevents is silent. `authority.context.admit_hop` fails open when no
  `InvocationContext` is ambient, so a deployment that never enabled identity admits every
  unauthenticated caller and reports healthy while doing it. `plato/posture.py` checks at startup
  and refuses with exit code 3, distinct from the unknown-role exit so the two are not confused,
  and the refusal names the setting, the reason and the escape hatch. `--check` is gated too, so
  the failure lands in a readiness probe rather than on the first request. Nothing is enforced
  outside a deployed posture, which is what keeps the check from being switched off out of
  annoyance, and a settings object lacking the attribute is treated as off rather than compliant.

  Also records the five database schemas and, more importantly, the rule attached to
  `plato_projection`: a JAPES service may hold a read projection of another system's facts and may
  not become a second writable copy of them. Naming the schema is what makes a write into it look
  wrong in a diff. No migration yet, deliberately: there are no tables, and five empty namespaces
  would be ceremony. The first table migration creates the schema it names.

  **`queue_processor`'s in-memory message dedupe, which the Plato plan lists as a latent
  correctness bug to fix here, no longer exists.** It was replaced by a durable claim in
  `QueueExecutionStore` keyed on `header.message_id`, with a lease and a
  `duplicate_invocation_skipped` response, which is a stronger answer than the plan proposed. No
  work was needed.

- **Durable session and manifest stores (Plato phase 0b).** `AssistantManifestStore` and
  `SessionStore` shipped as abstractions with in-process implementations only, which is right for
  a library and unusable for a service: two replicas behind a load balancer do not see each
  other's sessions, so a resume lands wherever the balancer sends it and finds nothing, and
  `history()` and `rollback()` were promises the process could not keep past its own lifetime.

  `DbSessionStore` and `DbAssistantManifestStore` supply the durable half on `fabric.db`,
  following `audit/events_db.py` and `prompt_registry_db.py` rather than inventing a third
  persistence idiom: typed columns over a JSON blob, `metadata` registered in `__init__` for the
  consuming service's alembic, and DDL left to that service. They live beside their protocols in
  `jazzx_sdk` for the same reason the existing two do, so a consumer other than Plato can use
  them; Plato owns the schema and the migrations.

  Both preserve the in-process semantics exactly, which is the point of a second implementation:
  `touch` never revives an expired session, `expire` is a new state rather than a delete, a
  rollback appends a new record rather than resurrecting an old one, and a `put` that fails
  validation leaves nothing behind. 22 of the session tests run against **both** implementations
  through one parametrized contract, so a divergence is caught here rather than in a replica.

  Found while testing: **sqlite discards tzinfo regardless of `DateTime(timezone=True)`**, so a
  round-tripped timestamp came back naive and could not be compared with the aware value its
  record was built from. Both stores now re-attach UTC on read, since every column is written in
  UTC and the store's contract should not depend on which backend is under it.

  Two claims in the Plato plan were wrong and are corrected here rather than carried: a durable
  `ConfigAuditStore` already exists (`audit/events_db.py`), so two abstractions needed backing
  rather than three; and `tenant_id` is not absent everywhere, since `ConfigAuditEvent` and its
  row already carry it.

- **Plato (Platform Two) Phase 0a: the package, the boundary, and the deployable skeleton.**
  `plato/` is a new top-level package, a sibling of `jazzx_sdk/` rather than a subpackage of it,
  that will host the SDK as a service (`japes-plato`). Nothing runs yet: this phase lays the
  boundary and the deployable skeleton so later phases have somewhere defensible to build.

  The dependency runs one way. `plato` imports `jazzx_sdk` and `common`; the reverse never
  happens, and `.importlinter` enforces it in CI on every push and pull request. That check
  landed in the same change as the package, because a boundary added after the first violation is
  a refactor rather than a rule. A second contract keeps `common` from importing either, since it
  is vendored into other repositories and a dependency back into this one would make it
  unvendorable there. The contract was verified by planting a violation: it exits 1 and names the
  importing line.

  **The repository gains its first Dockerfile and its first alembic tree.** One image, with the
  role selected at run time by `JAPES_RUN_MODE`, so a deployment promotes a single digest.
  Migrations are a job, never a container-start step, because a replica that migrates on boot
  races every other replica in the same rollout. The alembic tree belongs to `plato/` and targets
  Plato's metadata only: every `*_db.py` store in `jazzx_sdk` says DDL belongs in the consuming
  service's alembic, and Plato is that service, so `jazzx_sdk` still ships no migrations. It
  resolves its engine through `fabric.db`, whose `engine()` docstring already names alembic as
  the caller, and carries no connection string. Autogenerate is filtered to `plato_*` schemas:
  the database sits on a shared server, and reflecting without that filter produces a migration
  that drops another service's tables while looking entirely plausible.

  `python -m plato` resolves and reports its role, and **refuses to serve**. The runtime lands in
  Phase 1, and a container that boots into a stub reports healthy to an orchestrator, which is
  worse than one that fails.

  Costs a plain consumer nothing: `fastapi`, `sqlalchemy` and `asyncpg` are already core, so the
  `plato` extra adds only `alembic`. 18 tests cover the boundary, the packaging, the alembic
  scoping and the entry point.

## [2.4.8] - 2026-08-28

- **Converters record where each span of markdown came from, so a chunk can name its page, sheet
  and row.** The last two entries gave chunks a span and a section path; this fills the fields that
  were declared and empty, and it closes the chain end to end.

  Conversion is the last point at which a document's structure is known -- afterwards the text is
  markdown, and a page or a spreadsheet row can only be recovered by searching for a value, the
  step `extraction.py` already warns "would hit almost every page and produce a meaningless
  locator". `Conversion` now carries `ConversionRegion`s alongside the markdown, and
  `chunking.apply_regions` intersects a chunk's span against them. Neither side searches text, so
  neither can match the wrong occurrence.

  Three routes carry structure today. A digital PDF's markdown is its page texts concatenated with
  a blank line between, so page boundaries are arithmetic rather than a guess. A workbook names
  each sheet with its **source** row range -- numbered before empty rows are dropped, because the
  spreadsheet's own 1-based row is what an operator opens the file to, and recording the
  post-filter index would name a row nobody can find. A CSV gets the same treatment under its
  synthetic sheet name. A passthrough `.md` or a flow-layout `.docx` reports no regions, which is a
  statement that the format has no structure to carry rather than that it was lost.

  Ranges rather than first-values: a chunk spanning pages 4 to 6 says so, because claiming page 4
  sends a reader to the wrong place two thirds of the time, and a chunk overlapping two sheets
  claims neither -- the same rule a merged chunk already followed.

  `convert_document` and `convert_document_and_structure` are unchanged; `convert_document_located`
  is the third entry point, over one implementation, matching how `extract`/`extract_located` split.

- **Locators reach the extraction path.** The previous entry put a locator on the chunker in
  `documents/chunking.py`, which nothing uses: `extract()` -- and therefore `DocumentAgent` and
  `document_ingest` -- runs on a second chunker in `documents/extract.py` whose contract was
  `Callable[[str, int], list[str]]`. Bare strings, so provenance stopped at the chunk boundary.

  That seam is now `Callable[[str, int], list[Chunk]]`. The chunkers already sliced by offset and
  already promised losslessness, so the spans were derivable all along and simply discarded; the
  recursion now carries absolute offsets rather than substrings, and each chunk is named by the
  heading it opens with.

  `_merge_extractions`' rule -- "the first chunk that reports a non-empty value wins" -- was
  *already an attribution*, naming exactly which region produced each field, and it was being
  thrown away. It is now returned: `extract_located()` gives the instance plus a
  `{field: ChunkLocator}` map, and `extract()` is a thin wrapper over it that returns the instance
  alone, so the two cannot disagree about what was extracted.

  `DocumentAgent` uses it. A field whose chunk is known now gets a `SectionLocator` naming that
  section and its path, slotted **below** the page and cell locators (which are more precise) and
  **above** the generic `section="document"` fallback (which names nothing). That is the same
  answer `_resolve_locator` previously reached by searching the markdown for the extracted value --
  the step `extraction.py` already warned "would hit almost every page and produce a meaningless
  locator" -- arrived at without a search that can mis-match.

- **A document chunk carries where it came from, instead of that being rediscovered later.**
  `DocumentChunker.chunk_document` returned `(name, content)` pairs, so by the time a chunk existed
  the source structure was gone. Provenance was then reconstructed downstream by *searching*:
  `DocumentAgent` matches an extracted value back against the markdown to resolve a
  `SectionLocator`. That works until the anchor is loose, and `extraction.py` already named the
  consequence -- an anchor that hits almost every page produces "a meaningless locator".

  Chunks now carry a `ChunkLocator`. Two fields are populated today because the chunker already
  knows them and was discarding them: the character span it cut, and the header hierarchy it cut
  under -- `("Article VI", "Covenants", "6.1 Financial Covenants")` rather than a flat matched
  header, which is the difference between a citation a reviewer can act on and one they have to go
  looking for. `page`, `sheet_name` and the row range are declared but empty, so a converter can
  fill them without every downstream reader changing shape.

  Merging is where provenance would have vanished quietly, since it builds new text rather than
  passing a slice through. A merged chunk spans everything that went into it and keeps only the
  ancestry that stays true of the pair: merging 6.1 with 6.2 gives a chunk under Covenants, not one
  claiming to be 6.1, and a merge across two spreadsheet sheets claims neither.

  **Nothing existing changes.** `Chunk` is a tuple subclass, so `for name, content in chunks`,
  indexing, and equality against a plain pair all still work. A separate richer return type was the
  alternative and would have meant two code paths over one splitting algorithm, which is the drift
  this module would then have to police.

  The span bounds the *source region*, not a byte-identical slice: for a single section
  `content[start:end].strip()` is the chunk, but a merged chunk's text is re-joined. Stated in the
  docstring because "exact offsets" is the natural reading and is wrong in the merged case.

## [Unreleased] - SDK (pre-2.4.7)

- **25 provider tests passed only on machines with an `OPENAI_API_KEY` exported.** CI found them
  the first time it ran, which is the point of it. They construct `OpenAIProvider()` the default
  way on purpose, and that path reads the environment and raises without a key, so the suite had a
  silent dependency on a credential nobody had declared. Every call through the provider is mocked,
  so what they need is a constructible client, not a usable one: an autouse fixture in
  `tests/agents/conftest.py` fills in a placeholder only when the variable is absent, leaving a
  real key to win and the live smoke tests to keep theirs. Verified by running the full suite with
  the variable unset, which is what CI does.

  The workflow reports failures as well as skips now (`-rfs`, was `-rs`). The first red run named
  no failing tests in its summary, so finding them meant grepping the log body for section
  headers.

- **The suite now runs in CI, so a pull request arrives with signal rather than an assertion.**
  Nothing ran pytest outside the machine of whoever wrote the change, which made "tests pass
  locally" a claim about an environment nobody else had. `.github/workflows/tests.yml` runs it on
  every pull request and on pushes to `dev`, `main` and `plato`, with a concurrency group so a
  branch pushed three times does not hold three runners and leave the reviewer reading whichever
  finished last.

  The extras are matched to what the suite is actually verified against rather than chosen for
  breadth: installing more would run tests nobody has seen pass, and installing fewer would drop
  coverage the local run has. `pandoc` is installed because it is a system binary several document
  tests skip silently without, and silent skipping is the failure this job exists to remove; `-rs`
  prints every remaining skip with its reason, so a test that stopped running for an environmental
  reason is visible instead of absorbed into the counts. The live-LLM smokes stay skipped: a suite
  that spends money and fails on someone else's rate limit stops being trusted within a week. The
  private-dependency credential is passed through `GIT_CONFIG_*` for the one step that needs it,
  not written to `~/.gitconfig`, where a failing install would skip the cleanup and leave it for
  everything after.

- **Every poetry pin in the repository was too old to read the repository's own lockfile.**
  `poetry.lock` is `lock-version = "2.1"`, written by poetry 2.2.1, and both example images pinned
  1.8.3, which refuses to read it. Every image build would have failed at the install step. The
  pins are now 2.4.1, and `tests/test_dockerfiles.py` derives the floor from the committed
  lockfile rather than restating it, so relocking with a newer poetry fails the check instead of
  silently invalidating a pin nobody revisits. It covers the workflows for the same reason.

- **Both example images were unbuildable, and one leaked its build credential into every running
  container.** They copied `jazzx_runtime_sdk/`, a package renamed long enough ago that nothing
  remembered, so the `COPY` failed and the build stopped there. Nothing caught it because nothing
  in the suite reads a Dockerfile and neither image is built in CI. The basic sample was worse off
  still: it pinned python 3.11 against a project floor of 3.12 and called `poetry install --no-dev`,
  an option poetry removed, so it could not have installed even with the paths right.

  The credential handling was the more serious half. `ARG GITHUB_TOKEN` is recorded in image
  history and readable with `docker history` by anyone who can pull the image, and the document
  analyzer additionally promoted it to `ENV GIT_TOKEN`, where it was readable inside every running
  container. Both now take it as a BuildKit secret, mounted only for the step that needs it.

  Both images took the two-stage shape, so no compiler, git or credential reaches the runtime
  image, and `POETRY_INSTALLER_MAX_WORKERS=1` replaces the retry loop that worked around the
  client-api double-clone failure: serialising the installer makes that race impossible rather
  than retried. The healthcheck was `python -c "import sys; sys.exit(0)"`, which reports healthy
  for a container that cannot start and so guarantees an orchestrator never restarts it; it now
  imports what the entry point imports. The separate `pip install -r requirements.txt` step is
  gone, since `openai-agents` has been a core dependency for some time.

  The publishing workflow moved with them. It passed `build-args: GITHUB_TOKEN=...`, which no
  Dockerfile reads any more, so the build would have failed at the poetry install with an
  authentication error naming nothing useful; it now passes a `secrets:` entry and sets up Buildx
  explicitly rather than relying on the runner's default builder, since `--mount=type=secret` is a
  BuildKit feature and the fallback is silent.

  `tests/test_dockerfiles.py` is the part that stops this recurring: every `COPY` source must
  exist, no `ARG` may name a credential, and no base image may sit below the project's python
  floor. A rename is exactly the change that leaves a `COPY` behind. Verified by mutation:
  restoring the old path fails the check. `common/` is excluded as a submodule, and its
  devcontainer image does pass `ARG GITHUB_TOKEN`, which is a fix for that repository to make.

- **`DbConfigAuditStore` returned timestamps that could not be compared with the ones it was
  given.** sqlite has no timestamp type and hands back a naive datetime whatever the column
  declares, so an audit event written with an aware `occurred_at` read back naive: the event did
  not equal itself across a round-trip, and `history()` could not be ordered against a caller's own
  timestamps. Postgres `timestamptz` masks this, so it only bit the sqlite path. UTC is now
  re-attached on read, which restates how the column is written rather than guessing.

  The shared exercise both audit-store implementations already run through now asserts the
  timestamp contract, so the durable and in-process stores cannot disagree about it. Verified by
  reverting the fix: the durable store fails and the in-process one passes.

- **`scripts/run_tests.sh`** runs the suite and prints the failures plus the counts line, keeping
  the full output at a path. The suite is large enough that a plain run buries its own result in
  the warnings summary.

## [2.4.7] - 2026-08-23

- **Model data is versioned, and overlays leave a trace.** Per-row `Provenance` says where a rate
  came from; `MODEL_DATA_VERSION` says *which snapshot of the file* answered a call, so a cost
  figure can be tied back to the rates that produced it. `register_model_pricing` /
  `register_model_card` now record an `OverlayRegistration` (model, kind, source, whether it
  overwrote) instead of writing silently. A consumer carrying data ahead of the SDK, as jaci does
  for the Claude 5 family, previously left nothing behind, so two processes on the same release
  could answer differently with nothing to explain why. `overlay_registrations()` exposes the log;
  `model_data_version_tags()` shapes it for a run.

  `ensure_run` stamps those tags on every run japes opens, so all five reference pipelines carry it
  without each remembering. Tags rather than a trace-schema field on purpose: `VersionBundle` is
  frozen under the Spec-v1.5 contract, so extending it is a cross-team change while tags are the
  sanctioned hatch.

- **`jazzx_sdk.digest.content_digest`**: the content hash as a primitive with no dependencies.
  `evaluation.prompt_registry.content_version` has been the de-facto one, and `fabric.guidance` and
  `manifest.store` already import it from there; but `llm` sits *below* `evaluation` (nine imports
  one way, none the other), so nothing under `llm` could reach it without inverting the dependency.
  `content_version` now delegates and returns a byte-identical hash: same name, same length, same
  callers. Accepts dicts via canonical JSON, so a reformat that changes no value is not a new
  version.

- **Response security headers** (`server.security_headers`): CSP, X-Frame-Options,
  X-Content-Type-Options, Referrer-Policy, applied by `create_app` with an API-shaped default of
  `default-src 'none'`. japes set none of these, which is defensible for a service-to-service API
  and not for `ServerSettings.static_dir`, which serves a SPA from the same origin. **HSTS stays
  off unless asked for**: a browser *caches* it, so one response from a plain-HTTP dev origin pins
  that host to HTTPS locally with no convenient undo. `spa_csp()` builds the same-origin policy a
  served bundle needs, and a route setting its own header keeps it.

- **Settings writes get concurrency control and an audit line.** `GET {prefix}` returns an `ETag`
  over the stored values, not the masked catalogue, since two different secrets both render as the
  mask and must not look like the same state, and PATCH honours `If-Match` with a 412. Optional,
  because requiring it would break every existing caller. Each write logs `settings.write` with the
  actor and the **key names only**: this endpoint writes secrets, and an audit trail that quotes
  what was written is a second copy of the secret in the log. (The deployed-posture refusal for
  unauthenticated writes already existed.)

  Fixing this surfaced a trap worth recording: `settings_api` imports fastapi function-locally so
  the module stays importable without the server extra, but under `from __future__ import
  annotations` FastAPI resolves handler annotations against **module globals**: a function-local
  `Response`/`Header` is invisible there and the parameter is treated as a request field, 422 on
  every call. Those two imports are now module-level behind an ImportError guard.

- **A read-only console view** (`server.console_api`, opt-in via `extra_routes`): three GETs on a
  `GovernedRouter` exposing the platform catalog, the full model-data picture (rates, tiers, cards,
  provenance, unreviewed rows, overlays, data version) and registry contents via the existing
  `describe()` convention. All of it is already computed in-process with no way out; answering "why
  did this turn cost that" otherwise means reading someone's logs or their source. A registry
  without `describe()` reports that rather than vanishing, since omitting it would read as "empty".

- **Added `gpt-5.5`** ($5.00/$30.00, cached $0.50) with its long-context tier above 272,000 input
  tokens ($10.00/$45.00), the last OpenAI model the vendor tiers that japes did not carry. Priced
  only: the row's `(<272K context length)` annotation marks the tier boundary, not the context
  window, so a card needs a human to source the real limits.

- **Reconciled all three vendor pricing pages; three write guards added after the run proposed
  corrupting data.** A live fetch found no real rate drift, but `--write` would have applied 13
  changes, of which 10 were wrong:
  - **7 un-deprecations.** A pricing page carries rates, not lifecycle: a retired model still
    listed there is not thereby current, and the deprecation flags came from the vendor's separate
    deprecations page, which this script never reads. It read absence-of-a-notice as `deprecated:
    false` and would have silently un-retired `gpt-4o`, `gpt-4o-mini` and five o-series models. A
    pricing page can now only ever flag a model as *newly* deprecated, never un-deprecate one.
  - **An 8x price jump.** `gpt-4o-mini` was proposed at $1.25/$5.00 against its real $0.15/$0.60.
    the page lists that model under standard, batch, fast-mode *and* fine-tuning tables at once,
    and the extractor mixed them. A change beyond 3x is now reported and skipped rather than
    written, since real rate moves are incremental.
  - **A storage price read as a cache-write price.** Gemini has no per-token cache-write rate; it
    lists "$1.00 / 1,000,000 tokens per hour" of cache *storage*. The extraction prompt now names
    that trap explicitly.

  Applied from the run: `cache_creation` for the three `gpt-5.6` models ($5.00 / $2.50 / $0.25),
  which had been entered without it, each confirmed as 1.25x its input rate before writing. All
  three provider `verified` dates bumped, so the weekly staleness job now passes instead of
  arriving red.

- **Changing a rate clears that row's sign-off.** A review vouches for the numbers a person
  actually saw and cannot survive them changing, or the row keeps asserting a human checked a
  value written after they looked. The three `gpt-5.6` rows went back on the review list for
  exactly this reason: their cache-write rate was added after they were signed off.

- **Per-row pricing provenance, and a review step for a human.** `PricingSource` answers "when did
  anyone last look at this vendor's page": right for a staleness sweep, wrong for an audit. Rows
  are transcribed one at a time, from different pages, on different days. New `Provenance`
  (`source`, `retrieved`, `reviewed_by`, `reviewed_on`, `note`) records that per row, read via
  `model_provenance(model)`, which falls back to the provider sweep for rows carrying none,
  honest rather than blank, since that genuinely is all that is known about them.

  `reviewed_by`/`reviewed_on` record a **human** confirming a transcription, deliberately separate
  from retrieving it. A rate cannot be validated by a test: it is plausible whatever column it came
  from, and vendor pages put standard beside long-context, preview beside GA, free beside paid. So
  a machine-read rate stays unreviewed until a person says otherwise, and a provider-wide sweep
  never counts as a per-row confirmation.

  `update_model_pricing.py --review` prints every rate grouped under the URL it was read from:
  base rates, tier, retrieval date and note, so the check is a comparison rather than an
  excavation; `--mark-reviewed 'Name' --models a,b` records the sign-off. It refuses a row with no
  provenance, since there would be no source to have checked it against. `unreviewed_models()`
  exposes the work list.

  Provenance resolves through an alias the same way pricing does. An alias answers with its
  target's numbers, so it was read from the same page on the same day and confirmed by the same
  person; reporting it as unsourced would misdescribe rates that have both. Caught because the two
  pending counts disagreed: `unreviewed_models()` walks pricing keys (aliases included) while the
  review tooling walks JSON rows, and a sign-off that can never complete is worse than none. An
  invariant test now asserts the two agree.

  The 13 rows read from vendor pages on 2026-08-23 are signed off by Veeru; 32 rows carried over
  from earlier sweeps remain unreviewed, which is accurate.

- **`gemini-3-flash` re-verified and left unchanged at $0.50/$3.00/$0.05.** It had been flagged as
  possibly understated against a $0.75/$3.75 figure; a focused re-read of the vendor page shows no
  GA row for that id at all, only `gemini-3-flash-preview` at the rates already recorded. The
  $0.75 came from a broad "list every price" extraction, the same unreliable shape that produced a
  wrong figure for this exact model once before. Its provenance note now carries that warning so
  the next reader doesn't "correct" it a third time.

- **Added `gemini-3.5-flash`** ($1.50/$9.00/$0.15), the model `gemini-3-flash` keeps getting
  conflated with, and genuinely missing, so it was worst-casing at $21/$168: a 1M-in/100k-out call
  reported $37.80 instead of $2.40. Priced only, with the conflation warning in its note; its
  context window and capabilities need a person before a card is written.

- **MLflow spans no longer go through the fluent API.** `_MlflowRun` already documented why runs
  are addressed by explicit `run_id` through `MlflowClient`: the fluent API keys off a
  **thread-local** active run while every call here is offloaded to the event loop's shared thread
  pool. `MlflowTracer.span` had never been given the same treatment: it called `mlflow.start_span`
  and `mlflow.update_current_trace`, so a span could be opened on one pool thread, tagged from
  another and ended on a third, each consulting a different (usually empty) thread-local stack.
  Under concurrent turns on one loop that interleaves: spans orphaned into no trace, or a stage
  tag landing on another turn's. The sibling had the fix and this one didn't.

  Spans now use `MlflowClient.start_trace` / `start_span(trace_id, parent_id)` / `end_span` /
  `end_trace` / `set_trace_tag`, all addressed by explicit id, so the executing thread is
  irrelevant. A root span *is* its trace, so its stage tag is set at creation and is present even
  if the turn dies before anything tags it; a nested span tags its trace by id rather than
  "whichever trace this thread thinks is current".

  Nesting comes from a new `_ACTIVE_SPAN` ContextVar. That is sound here in a way it deliberately
  is not for runs (see `ensure_run`): a span is always opened and closed by one `async with` in a
  single task, so the set/reset pair can never split across tasks or be observed after the block,
  and `conductor.fan_out`'s tasks copy the context at creation so concurrent children correctly
  see the enclosing span as parent. Because a fake accepts any signature, a boundary contract test
  binds all seven call shapes against the installed `MlflowClient`, skipped when the extra is
  absent. That is the failure a mocked suite would otherwise carry green into a deployment.

- **An uncarded model now announces itself.** Costing has warned since it gained
  `register_model_pricing`, but facts were silent: `context_window_for` answered `None` and
  `unsupported_request_params` answered "nothing is blocked", and a caller could not tell a real
  fact from a stand-in. New `is_carded()` (mirroring `cost.is_priced`) plus a warn-once that names
  the consequence rather than just the absence. 34 of 42 model rows are priced-but-uncarded, so
  this is a live condition, not a theoretical one. The deliberate o-series fallback stays silent:
  it is an authored fact, not a guess.

- **Compaction sizes itself from the model's context window.** `ModelCard.compaction_threshold`
  existed for exactly this and had no callers, while `build_responses_compaction_session` took the
  model *and* a separate hardcoded `200_000`. That number is wrong for all eight carded models:
  20% of the window on the 1M-token cards (compacting constantly for nothing) and equal to the
  whole window on `claude-haiku-4.5`, where compaction could only fire once the context was
  already full. New `resolve_compaction_threshold(model, explicit=, fraction=)` derives it at 80%
  of the real window; an explicit value still wins, and an uncarded model falls back to a named
  constant with a warning instead of a bare literal.

- **GPT-5.6 family registered**: `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`, with `gpt-5.6`
  as an alias of Sol. 1,050,000-token context, 128,000 max output, reasoning-tier params stripped.
  Prices verified against the vendor's own pricing page after two aggregators disagreed on Sol:
  they were quoting its **long-context** output rate ($30) as if it were standard ($20).

- **Long-context pricing tiers are modelled.** Several vendors charge more once a prompt crosses a
  size threshold, and japes billed every such call at the short-context rate, so an oversized
  request **understated** spend, and an understated figure is indistinguishable from a correct
  one. The premium applies to the *whole* request, not the tokens past the threshold, so cost
  steps rather than ramps: a 273k-token prompt on `gpt-5.6-sol` costs nearly double what billing
  the overage alone would suggest.

  New `LongContextPricing` (threshold + its own rates) hangs off `ModelPricing.long_context`, with
  `for_prompt_size()` selecting the tier and `compute_cost` applying it. Threshold semantics are
  explicit: it counts *everything sent* (uncached input, cache reads and cache writes alike)
  because a vendor sizes the request by the whole prompt, and counting only the uncached remainder
  would keep a heavily-cached 500k prompt on the cheap tier indefinitely. Output tokens don't
  count. `for_prompt_size` returns rates carrying no tier of their own, so resolving twice can't
  compound the premium.

  Tiers declared in `model_data.json` (data, not code) after sweeping **every** priced model
  against its vendor's table rather than only the ones in hand: OpenAI `gpt-5.4` and the three
  `gpt-5.6` models above 272,000 input tokens (2x input, 1.5x output; multipliers that reproduce
  the vendor's long-context columns exactly, which is what confirmed the reading), and
  `gemini-3-pro`, `gemini-3.1-pro-preview` and `gemini-2.5-pro` above a 200,000-token prompt. A
  300k-token `gemini-2.5-pro` prompt was being billed at half its real rate.

  **Absence is a checked fact, not an unfilled gap**: the two look identical in the data, so
  "nobody transcribed it yet" would otherwise pass for "flat". Sixteen models are asserted
  single-rate, including every current Anthropic model: 4.6 and later carry the full 1M window at
  standard pricing, and everything earlier (Sonnet 4.5 included) is a 200k-context model. The 1M
  beta that once charged a premium no longer exists. The vendor states 1M needs no beta header
  and bills at standard rates, so a tier there would invent a charge and *overstate*.

  The cost-optimized (batch/flex) discount now scales *through* the tier via a new
  `ModelPricing.scaled()`; the old inline rebuild would have dropped it, silently putting every
  oversized batch call back on the cheap rate. `update_model_pricing.py` maintains the base tier
  only and leaves a declared `long_context` block untouched, stated in the script so the
  hand-maintained part is a known limit rather than a discovered one.

  Removed the duplicated `gemini-3-pro-preview` pricing row: it copied `gemini-3-pro`'s rates
  under the alias id, and aliases now resolve to their target, so the copy was exactly the drift
  hazard aliases exist to avoid. Also found while transcribing: `gpt-5.4` had an unmodelled tier
  too, not just the newly-added 5.6 family.

- **`register_model_card` no longer overwrites by default**, matching `register_model_pricing`'s
  long-standing `overwrite=False`. The two halves of the same registration seam disagreed: a
  consumer registering a rate was protected from silently re-rating a shipped model, while the
  same consumer registering a card silently re-spec'd one.

  The default is what makes the overlay pattern safe: a consumer carrying model data ahead of an
  SDK release has to *stop* outranking the SDK once the real card ships, or it keeps serving a
  stale copy nobody remembers is in play. Pass `overwrite=True` to deliberately re-spec a model.
  Each key is considered on its own, so an alias already claimed by a different card is not
  stolen: the primary id registers and the alias stays where it pointed.

- **Pricing staleness is now a gate, not just a printout.** `update_model_pricing.py --check`
  reported how old each vendor source was and always exited 0, so nothing could act on it. It
  gains `--max-age-days N`, which exits 1 when any provider is overdue; without the flag it only
  reports, so interactive use is unchanged. A weekly workflow runs it. Staleness is the condition
  that precedes every concrete failure this data has: a model published after the last check has
  no row at all, worst-cases on price, and answers with stand-ins for its limits. All three
  sources were 46 days old when this landed, and GPT-5.6 had shipped in the gap.

  The script also stopped importing the package to read one path constant. `import
  jazzx_sdk.llm._model_data` runs `jazzx_sdk/__init__.py` first, which eagerly pulls the runtime,
  the queue processor and the `common` submodule, so `--check` needed azure-storage-queue
  installed to read a filename. It now loads `_model_data.py` by path, safe precisely because
  that module documents itself as depending on nothing else in the package, and the two
  fetch-path imports became lazy, so `--check` runs on a bare interpreter.

- **Corrected max output for Claude Opus 4.8 and Sonnet 4.6**: both were recorded as 64,000 when
  the vendor publishes 128,000, understating the real limit by half. Found while transcribing the
  Claude 5 family's limits from the same table.

- **An alias now resolves for pricing, not just for cards.** Registering GPT-5.6 exposed it
  immediately: `gpt-5.6` resolved to Sol's card but had no price, so it worst-cased at $21/$168,
  a 5x overstatement of a model that costs $4/$20. Aliases were only working for pricing where the
  rate had been *duplicated* under the alias id, which is the drift hazard aliases exist to avoid
  (two ids answering with different money, invisibly). Rates are declared once and aliases resolve
  to them; an alias carrying its own explicit rate is left alone, since a separately-priced id is
  not an alias. A new invariant test asserts every alias prices identically to its target and
  resolves to the same card object.

- **Per-turn observability runs are wired into the reference pipelines.** `RunTracer.run()` had
  been fully built since the runtime-observability work but had **zero production call sites**:
  the same "capability present, never wired" shape zero-data-retention had in 2.4.6.
  `ConductorEngine` opens per-stage *spans* but never a *run*, so there was no container for a
  turn's params/metrics/artifacts and no binding to the inbound trace id. A downstream service had
  consequently grown its own tracing module whose run-tagging was a verbatim re-derivation of
  `build_run_tags`.

  New `jazzx_sdk.observability.ensure_run(tracer, *, run=, name=, tags=)` yields
  `(handle, owned)`. A caller already inside a run passes its handle as `run=` and it is
  **borrowed**, used as-is, never terminated and never status-changed, because a run's status is
  its opener's to decide. Otherwise a run is opened for the turn. `tracer=None` resolves to
  `NoOpTracer`, whose handle is free, so call sites wrap work unconditionally with no branching.

  `run_chat_turn`, `stream_chat_turn`, `run_document`, `run_investigation` and
  `run_spread_pipeline` each gained `run=`/`run_name=`/`run_tags=` and now log latency, usage and
  outcome: every reference pipeline, so the shape is uniform rather than something a consumer has
  to check per entry point. Defaults are unchanged: with no tracer the whole mechanism no-ops and
  every return value is what it was.

  What each pipeline reports is chosen for what its failures actually look like. Spreading logs
  the **locate → structure → assemble funnel** rather than only the final spread, because a region
  that never located and one that located but wouldn't structure are both simply absent from the
  result and only the stage counts separate them; it also carries `vocabulary_gaps`, the pack's
  chart of accounts failing to cover what the document reported. An investigation logs *how the
  loop exited*: converging in three iterations and giving up at max-iterations both produce a
  "complete" run, so the exit reason is the aggregatable fact, split into flags since metrics are
  numeric.

  An ambient (ContextVar) variant was designed and **rejected on evidence**. Async generators have
  no private `Context` (PEP 568 was never implemented), which was verified rather than assumed:
  a `set()` inside `stream_chat_turn` executes in the *consumer's* context during `__anext__` and
  escapes to it; two streams multiplexed in one task overwrite each other and leave the context
  pinned to a terminated run; and a cross-task `reset()` raises, which inside the tracer's
  `finally` would leave the run RUNNING forever. Notably `gather`/`create_task` *do* isolate, so
  the ambient design would have passed ordinary tests and failed only under a real SSE fan-out.
  Explicit `run=` delivers the same "don't double-open" guarantee with no ambient state.

  Three details that a straightforward implementation gets wrong, each covered by a test:
  - **Metric keys are namespaced per pipeline** (`chat.latency_ms`, `document.latency_ms`, …).
    A metric is an append-only *series*, not a value, so two pipelines sharing a borrowed run
    would otherwise interleave into one unreadable series. Params are logged only by the run's
    owner, since a conflicting `log_param` is rejected by the backend and silently, `log_*` being
    best-effort background writes.
  - **A degraded turn is a metric, not a failed run.** `default_step_error` returns a substitute
    reply *without raising*, so the run genuinely completed; it records `chat.failed=1` and leaves
    status alone. `set_status(False)` is never called: on a borrowed run it would mark the
    caller's run failed.
  - **Streaming reports `ttft_ms`/`stream_ms`, not wall-clock**, which on a generator measures how
    fast the consumer drained it. Terminal logging hangs off `_notify_turn_complete`, the one
    funnel all six terminal paths already pass through, rather than the run context manager,
    since `break` out of an `async for` runs no finaliser. An abandoned stream records
    `chat.abandoned` and closes FINISHED; a disconnect is not a failure.

  Token usage is normalized to one canonical key set. `InteractiveResponse.usage` is
  path-dependent: the single-shot path reports a cost and no breakdown, the agentic path the
  reverse, so emitting it verbatim gave one run name two metric schemas and split every
  aggregate silently. All keys are always present and zero-filled, with `cost_usd_known`
  separating "cost nothing" from "cost wasn't reported". Cost is never *derived*:
  `InteractiveResponse` carries no model name, and inferring one is how a cost figure lands orders
  of magnitude off. 28 new tests, including the interleaved-generator case the rejected ambient
  design failed.

## [2.4.6] - 2026-08-22

- **`build_source_tools`** — directory tools bound to one directory, so isolation is a property
  of the tools rather than a rule the model is asked to follow. `build_directory_tools` keys its
  directories by a runtime `source` argument, which can express "these directories" but never
  "not that one": an agent holding those tools can read any registered directory. With the
  directory closed over at build time, `source` doesn't exist in the schema the model is given, so
  a loan agent built with only its own documents has no way to name the guidelines corpus.
  `prefix=` renames the tools (`list_loan_documents`, …) for an agent holding several bound sets;
  omit it for the common one-set-per-sub-agent case. Wrappers invoke the shared tools through
  their real `on_invoke_tool` path, so they inherit the same validation and path-traversal
  refusal rather than growing a second, divergent one. japes' heaviest consumer rebuilt ~792 lines
  of these tools, chiefly to get this binding. 6 new tests.

- **Zero-data-retention is wired to real boundaries.** `redact_for_zero_retention` had been
  exported since 2.1 with **zero call sites** — a governance surface japes claimed but didn't
  have. New `jazzx_sdk.tools.retention.RetentionPolicy` makes the decision once and answers it per
  destination (`args_for_persistence`/`args_for_span`/`args_for_stream`/`response_for_*`/
  `error_for_persistence`/`allows_blob_offload`/`log_detail`/`include_exc_info`/`describe_call`),
  so a call site reads as what it is about to write rather than as a policy test — deciding
  independently at each boundary is how one of them quietly keeps what the others dropped. Tools
  opt in at `register_tool(..., zero_data_retention=True)`; the SDK never infers it, and an
  undeclared tool is unrestricted. `RetentionPolicy.from_flag` reconstructs a policy from a
  persisted flag so a **replay** redacts identically without the original registration — the case
  where naive re-derivation silently un-redacts. `redact_tool_results_in_history` walks a replayed
  conversation so withheld payloads can't return to the model in the next request, and
  **over-redacts when it can't match results to calls**: withholding a result that could have been
  kept is cosmetic, keeping one that shouldn't have been is the failure this exists to prevent.
  Wired into the stream boundary (`ToolStreamHooks(registry=...)`), where a per-tool commitment
  now outranks the caller's `stream_tool_args` display preference. 18 new tests. Found surveying
  kernel.

- **`gather_degrading(on_progress=...)`** reports which sources are still in flight as each lands,
  for a caller showing "still fetching X, Y" during a long fan-out. Snapshot and delivery happen
  under one lock, so two sources finishing together can't deliver out of order and make `active`
  appear to *grow* — a consumer rendering a shrinking checklist can rely on that. A hook that
  raises is logged, never disturbing the gather. japes' heaviest consumer hand-rolls exactly this
  (a lock, a shrinking set, per-thunk wrappers) today. 5 new tests.

- **`MlflowTracer` addresses its run by explicit `run_id` through `MlflowClient` instead of
  MLflow's thread-local fluent API.** `set_experiment`/`start_run`/`log_*`/`end_run` all key off a
  *thread-local* active run, but the tracer offloads every call to the event loop's shared default
  executor — so a run could start on one pool thread, log from another, and terminate on a third,
  each consulting a different (usually empty) stack, and two concurrent runs on one loop could
  stomp each other. Kernel hit exactly this and measured it: 40/100 concurrent calls lost their
  root span. `run()` now resolves the experiment to an id (creating it once if absent), calls
  `create_run`, and passes `run_id` explicitly to every `log_param`/`log_metric`/`log_dict`/
  `set_terminated` — which pool thread executes them stops mattering. The injected
  `mlflow_module=` test seam now supplies `MlflowClient()`. 2 new tests, including a concurrency
  guard verified to fail when runs share an id. Found surveying kernel.

- **Completion webhooks are delivered at most once across queue redeliveries.** Azure Queue
  Storage is at-least-once, and a crash between response-enqueue and input-delete replays the
  message through the DELIVER claim — re-enqueuing the response is fine (the response queue is
  idempotent by contract) but the webhook is an outbound call the caller *sees*, and it was
  re-firing on every pass with no persisted marker anywhere in the SDK. `QueueExecution` gains
  `webhook_delivered_at` and the store a `mark_webhook_delivered(key)` (both implementations;
  nullable column, no migration needed to start reading), threaded through
  `QueueProcessingResult.webhook_already_delivered`/`on_webhook_delivered`. Deliberately a
  *persisted* marker rather than "suppress on replay": a run that crashed before delivering still
  sends on the replay instead of losing the notification. A delivery that raises is not marked, so
  it retries. `send_response()` — a direct-send API with no execution record, and no production
  caller — documents that it carries no guard. Found surveying the assistant repo. 6 new tests.

- **Unpriced models no longer overstate cost silently.** `get_model_pricing` falls back to
  `DEFAULT_PRICING` — deliberately the most expensive card, so unknown spend over-reports rather
  than under-reports — but the fallback was silent, so a cheap unpriced model's cost read like
  real data while being ~40-120x too high (measured: $189.00 vs $2.25 for the same 1M/1M tokens).
  It now warns once per model, naming the overstatement. New `register_model_pricing(name,
  pricing, *, overwrite=False)` is the supported way to price a model the SDK doesn't card —
  japes' heaviest consumer was mutating `MODEL_PRICING` by `setdefault` at import to work around
  its absence — and `is_priced(name)` tests for the fallback without triggering the warning.
  `compute_cost()` called with neither `model_name` nor `pricing` warns for the same reason.
  Found surveying jazzx-assistant. 8 new tests.

- **Financial spreading becomes a reference pipeline, and the validation engine joins the SDK.**
  Three related moves, driven by asking whether spreading wanted a platform agent (it didn't — all
  three platform agents own an LLM loop, and spreading's only LLM step was already an SDK
  primitive):
  - **`jazzx_sdk/pipelines/financial_spread.py`** — japes shipped every spreading primitive
    (region location, `structure_statement`, the vocabulary resolver, the spread schema, export)
    and *zero* orchestration: `structure_statement` had no caller anywhere in the SDK. This is the
    wiring — locate → structure (fan-out per statement) → assemble per source → merge — following
    the `document_ingest` convention (`SpreadTurn` + build/run trio + `on_step_error`/
    `on_complete`), registered in `pipelines/catalog.py`. Anchors, vocabulary and the LLM are
    injected; the pipeline never reads a pack file. `merge_spreads` moves in beside the schema it
    operates on, verified byte-identical to the previous implementation on real multi-year filings.
  - **`finance/package.py`** — `SpreadPackage`/`SpreadLineItem` and their `FinancialSpread`
    round-trip: the governed twin of a spread, carrying per-cell provenance and confidence. It had
    no dependency on its previous home; every type it referenced was already here.
  - **`finance/validation.py`** — the validation engine. japes could already *render* findings
    (`workbook.GovernedFinding` and its findings sheet) without being able to *produce* one; this
    is the missing half, and `ValidationFinding` satisfies that protocol structurally so the
    protocol stays untouched. Domain content stays with the pack: a control needing named
    canonical lines reads them from `ControlKeys` and **does not run at all when they're unset**,
    rather than inventing a key or letting an unevaluable control read as a silent pass.
    `SeverityPolicy` replaces a hardcoded severity map (there was no override seam at all), and
    findings carry an open `code` so a pack can emit a defect class the SDK has no member for.
  Verified finding-for-finding and spread-for-spread against the previous implementation on real
  YETI (C&I) and MAA (CRE) filings — two segments, since the same engine serves both. 34 new tests.
  Full suite green (3395 passed, 5 skipped).

- **`DocumentAgentSpec.save_taxonomy(path, taxonomy)`** — the write counterpart to `from_dir`'s
  read: a read-modify-write over the same `<path>/document_agent.yaml`, preserving any other
  fields already there (e.g. `admission_floor`). Every `Spec.from_dir` in japes (Document/
  Adjudication/Interactive) was read-only until now — this is the first write-back, scoped
  narrowly to `taxonomy` (not a general save-any-field mechanism), for a jaci scenario UI that
  needs to edit a document taxonomy from a "Domain" tab rather than a code change. 6 new tests
  (`test_document_agent_spec_yaml.py`). Full suite green (3361 passed, 5 skipped).

- **`DocumentAgent.process_dir` is now safe for a recursive `**` pattern**, closing a real gap
  found while migrating jaci scenarios onto `document_ingest`: a nested match (e.g. a real,
  non-flat deal folder) was keyed by its bare filename and written into the same flat
  `output_dir` regardless of subdirectory — two same-named files in different subfolders would
  silently overwrite each other's `.md`/`.result.json` artifacts and collide on the manifest
  key. A nested match now keys by its path relative to `folder` and mirrors that subdirectory
  under `output_dir`, matching the convention the zip-unpack branch already used. A flat,
  top-level match (the default, non-recursive case) is byte-for-byte unchanged — verified with
  a dedicated regression test alongside a new same-filename-collision test. 2 new tests
  (`test_doc_pipeline_gaps.py`). Full suite green (3355 passed, 5 skipped).

- **`classify_document` pins `temperature=0.0`**, closing a real non-determinism gap found while
  re-validating the Acra packet split: the same page's real text classified differently across
  two otherwise-identical `split_document` runs (confirmed live, not assumed) because the
  provider default (~0.1) was never overridden — a page-classification/splitting mechanism whose
  entire job is consistent document boundaries had no repeatability guarantee at all. Checked
  this doesn't collide with the existing reasoning-tier parameter guards (OpenAI temperature/
  reasoning_effort conflict) before pinning it: `classify_document`'s default `AgentExecutionService()`
  (no `llm_manager`) always reaches `OpenAIProvider`'s tool-calling path, which already strips
  `temperature` unconditionally for any model whose card lists it unsupported, regardless of
  `reasoning_effort` — and this call never sets `reasoning_effort` in the first place, so it never
  hits the narrower `temperature`+`reasoning_effort` 400 the other (`LLMManager`-path) guard exists
  for. Re-ran the real page-7 classification twice against the live API after the change — label
  and confidence now match exactly run to run (only the free-text rationale wording varies, which
  nothing downstream depends on). 1 new test (`test_classify.py`). Full suite green (3353 passed,
  5 skipped).

- **`split_document` gains an opt-in `ocr_fallback`**, closing a real gap found while validating
  against a real, large Acra DSCR closing packet (not a toy fixture): a combined PDF is often
  *mixed* — some constituent documents digital, others scanned (a stamped title-company exhibit,
  an appraisal) — and a scanned page has no text at all, so page-classification alone can't split
  or label it; it just comes back `unknown` regardless of taxonomy quality, confirmed by manually
  rendering and reading the actual scanned pages of a real 429-page packet. `ocr_fallback=True`
  (default `False` — no behavior or cost change for any existing caller) OCRs just the scanned
  pages individually via a `DocumentIntelligenceProvider` (billed one page at a time, reusing the
  same per-page routing `conversion.py`'s mixed-mode path already does for whole-document
  conversion — new shared `ocr_scanned_page_texts` helper) before classifying. `DocumentAgent.
  process_package` gained the matching `ocr_fallback` param (`None` → `DocumentAgentSpec.
  split_ocr_fallback`, default `False`) plus forwards the agent's own `di_provider` — a pack turns
  this on globally via spec config, or overrides per call; real per-page Azure Document
  Intelligence spend either way, so it stays opt-in rather than a silent default. 4 new tests
  across `test_split.py`/`test_document_agent.py`. A local-only (gitignored) regression fixture —
  real extracted segments from the Acra packet, never committed (real borrower PII) — lives at
  `tests/fixtures/local/acra_godocs_mixed/` for manual re-testing. Full suite green (3352 passed,
  5 skipped).

- **`pipelines.document_ingest.run_document` and `pipelines.investigation_loop.run_investigation`
  gain `on_step_error`/`on_complete`**, closing a real symmetry gap against `pipelines.chat.
  run_chat_turn` (the only one of the three reference pipelines that had them). Both new params
  default to `None` — today's propagate-uncaught behavior is unchanged for every existing caller.
  Each module also exports an opt-in `default_step_error` with domain-appropriate recovery, not a
  copy of chat's: `document_ingest.default_step_error` degrades a failing step to a typed
  `Refusal` (the same shape `refuse_step()` already produces); `investigation_loop.
  default_step_error` halts the run cleanly with no fabricated decision (mirrors the module's own
  existing `halt_on_reasoner_failure` precedent — a credit/compliance investigation must never
  synthesize a decision on an unknown failure). `on_complete` fires once, best-effort, with the
  finished `ConductorRun`, same contract as `ConductorEngine.on_complete`. Confirmed no base-class
  refactor is warranted: all three pipelines are already thin `ConductorPipeline` wrappers
  composing over the shared `ConductorEngine` primitive, and the remaining duplication across
  their `run_X()` wrappers is a few lines, not worth a new abstraction layer. 8 new tests across
  `test_document_pipeline.py`/`test_investigation_loop.py`. Full suite green (3348 passed, 5
  skipped).

- **`ResilientRunner.execute`'s new `stream_factory` param** closes the real gap behind "queryable
  last-turn status without holding a stream open": `TurnRunStore` already had exactly that
  (`latest_run(conversation_id)`, `has_active_run`, write-time status stamping, durable journal,
  cooperative stop, resume-from-cursor) via `ResilientRunner` — but `execute()` always called
  `agent.respond_stream(...)` directly, bypassing `pipelines.chat`'s routing (gate/escalate/refuse)
  entirely. A durable/resumable turn and a *routed* turn were two separate, non-composable paths.
  `stream_factory` (optional, defaults to today's exact behavior) lets a caller supply
  `stream_chat_turn(...)` — or any `InteractiveStreamEvent` async generator — in place of the
  direct call, with zero new coupling (`runs/runner.py` still doesn't import `pipelines.chat`).
  A turn refused by the gate is now durably journaled and shows up in `latest_run` like any other
  turn. 2 new tests proving the composition end-to-end. Full suite green (3340 passed, 5 skipped).

- **`ConductorEngine.on_complete`, `pipelines.chat`'s own `on_complete`, and
  `channels.notify.notify_on_conductor_complete`** — a run/turn-completion hook, generalized at
  the layer it actually belongs: `ConductorEngine` (every conductor-based pipeline — CRE, AML,
  KYC, document processing, chat) gains `on_complete: Callable[[ConductorRun], ...]`, fired
  best-effort after `run()`/`resume()`/`resume_durable()`, same never-affects-the-run contract as
  `on_step`. `pipelines.chat.run_chat_turn`/`stream_chat_turn` gain their own `on_complete`
  (fires with the resolved `InteractiveResponse`, not the raw `ConductorRun` — `stream_chat_turn`'s
  inner engine only covers validate→gate, so its own completion isn't the turn's). New
  `channels.notify.notify_on_conductor_complete(channel, *, when=, to_message=)` bridges either
  level to the *existing* `Channel` abstraction `notify_on_complete`/`deliver_completion_hook`
  already use, instead of a second notification transport. 20 new tests across
  `test_conductor_engine.py`/`test_interactive_chat.py`/`test_notify_on_complete.py`. Full suite
  green (3338 passed, 5 skipped).

- **`pipelines.chat.structured_classifier_gate`** — a reusable `classify` builder for
  `gate_step`/`build_chat_components`: one deterministic (`temperature=0`), structured LLM call
  classifies the turn into a caller-supplied verdict schema, then a pure `verdict_to_route(verdict)`
  mapper decides direct/escalate/refuse. Every non-trivial chat gate ends up re-deriving this exact
  shape by hand (schema-only classifier agent, pinned temperature, dict-or-instance output
  coercion, wrap-a-bare-route-string-in-GateDecision) — this factors it out so a pack supplies
  only the schema and the mapping function. Precedence across multiple verdict signals stays an
  ordinary if/elif chain in the mapper (domain-specific per schema, not something a shared helper
  should generalize). 7 new tests. Full suite green (3318 passed, 5 skipped).

- **`InteractiveResponse.truncated`** — the truncation signal already threaded from
  `ProviderResult` through `LLMResult`/`AgentExecutionTrace` earlier this cycle stopped one hop
  short of the thing every real caller (`jazzx_sdk.pipelines.chat`, jazzx-assistant, jaci)
  actually consumes: `InteractiveAgent.respond()`'s returned `InteractiveResponse` had no field
  for it, so a single-shot reply cut off at the model's output-token limit carried no signal a
  caller could check. `_respond_single_shot` now reads `trace.truncated` and sets it. Agentic
  (skills-present) path unaffected — its equivalent condition already raises
  `IncompleteOutputError` inside `RetryingModel` rather than returning a silent value. 2 new
  tests. Full suite green (3311 passed, 5 skipped).

- **`expressions.validate()` flags a `MetricDefinition` with no explicitly-authored `version`**
  (closes the last gap in Phase 2 of `plan_JAPES_2_5_0_LOCATOR_AND_INVENTORY_DISCIPLINE.md`).
  Uses `model_fields_set` to distinguish "author wrote `version: 1`" from "never set it" —
  both produce the identical `"1"` string once constructed, so the field's default value alone
  can't tell them apart. New `missing_version` issue code. 2 new tests; existing
  `test_expressions_validate.py` fixtures updated to pass an explicit version (the omission was
  never the point of those tests).

- **`finance/metrics.py` strict mode (Phase 7 of `plan_JAPES_2_5_0_LOCATOR_AND_INVENTORY_DISCIPLINE.md`,
  SDK side only).** Every helper (`safe_div`/`pct`/`days`, the scalar formulas, and the
  `credit_metrics`/`working_capital_days` batch entry points) gains `strict: bool = False`.
  Default unchanged — a missing input or zero denominator still yields `None`. `strict=True`
  raises `MetricRefusal` instead, carrying the same typed `Refusal` shape
  `jazzx_sdk.expressions.evaluate` raises on the identical condition. **No pack sets it yet** —
  the plan's chosen adopter (a greenfield `cremf` pack) turned out not to exist; CREMF is the
  multifamily case inside the already-shipping `cre_underwriting` scenario, which still has
  legacy permissive-float code (`operating_spread.py`'s `or 0.0` accumulation,
  `analytics.py`'s float `_div`/`_pct`) that a real adoption would need to retire first. SDK-side
  plumbing landed regardless, adopter choice left open. 6 new tests in `tests/test_financial.py`.
  Full suite green (3307 passed, 5 skipped).

- **Config-versioning Phase 2: append-only `ConfigAuditEvent` audit trail.** New
  `jazzx_sdk.audit` (protocol + `InProcessConfigAuditStore` + `fabric.db`-backed
  `DbConfigAuditStore`, mirroring `evaluation.prompt_registry`'s three-file shape) — answers *who
  changed this, when, and what did it look like before/after*, which an actor column alone
  (Phase 1) can't. Wired into `PUT /agents/{name}` (optional `audit_store=` param, no-op when
  omitted): each write appends one `create`/`edit` event carrying the resolved actor, the active
  OTel trace id (`observability.get_current_trace_id()`), and before/after content digests (a
  local SHA-256 over the definition's meaningful fields — not `content_version()`, which stays
  gated on Phase 3's D2 decision). Append-only is asserted by test (the protocol exposes only
  `record`/`history`; source-text checks confirm no update/delete path exists), not by
  convention. 9 new tests. Full suite green (3301 passed, 5 skipped).

- **Config-versioning Phase 1: actor attribution + optimistic concurrency on
  `PUT /agents/{name}`.** First slice of `docs/plans/plan_JAPES_2_6_0_CONFIG_VERSIONING_AND_AUDIT.md`
  — closes a real, live data-loss path: the endpoint was last-write-wins, authenticated, with real
  consumers, and every day it stayed that way was a day of unrecoverable overwrites. (1) **F7**:
  `AgentDefinition.agent_id` was a computed `@property` recomputed from `spec.agent_id or spec.name`
  on every access, never persisted — a `PUT` that later filled in a previously-unset
  `spec.agent_id` silently changed the row's own identity, 404-ing any existing `GET
  /agents/by-agent-id/{old}` lookup with no error anywhere. Now a stored field (a
  `model_validator` derives it once, only when unset); the write path compares old-vs-new and
  refuses a drift with 422. (2) **F5**: `AgentDefinition` gains `created_by`/`updated_by`,
  resolved from `CallerIdentity.from_context()` — never request JSON — via a new shared
  `_stamped_for_write` helper both `InProcessAgentDefinitionStore` and `DbAgentDefinitionStore`
  call (the latter bypasses `fabric.db`'s `Repository`/`_stamp_created` entirely via `s.merge()`,
  so it had no audit-stamping path to inherit). `created_by` is set once and never overwritten;
  `updated_by` changes on every write. (3) An authenticated-but-unattributed write (e.g. a static
  API key with no identity headers) in a deployed posture now fails closed (403) instead of
  silently storing NULL actor columns. (4) **F3**: new `AgentDefinition.revision: int` +
  `jazzx_sdk/server/concurrency.py` (`check_if_match`, new optimistic-concurrency machinery —
  there was no precedent for it anywhere in `jazzx_sdk` before this) — `PUT` reads `If-Match`;
  a stale revision is `409`, a missing header on an existing row is `428`. Gated behind
  `strict_concurrency` (default `False` for one release, breaking-change discipline; on in
  japes' own CI immediately) so an existing caller that never sends `If-Match` is unaffected.
  19 new/updated tests in `tests/test_agent_config_api.py`, parametrized across both
  `InProcessAgentDefinitionStore` and `DbAgentDefinitionStore`. Full suite green (3292 passed,
  5 skipped). Phases 2-7 (audit-event log, versioned skill/profile stores, release resolver,
  aliases/promotion, runtime pinning, retiring mutable writes) remain, each behind its own gate
  per the plan.

- **UAF Phase 9 lands — 13/13 shipped.** `common` PR #212 ("reserve the `reasoning`/thinking-mode
  stream event type," `StreamEventType.reasoning` + `ReasoningEvent`) reviewed, approved, and
  merged to `common`'s `main`. japes' submodule pointer bumped to match. The japes-side producer
  (`InteractiveAgent.stream_reasoning`, `jazzx_sdk/agents/interactive/stream_hooks.py`) was already
  built and shipped in v2.4.2/2.4.3 against the unreviewed feature branch; live-verified
  `ReasoningEvent` now resolves through `jazzx_sdk.streaming.ReasoningEvent` with its `agent`/
  `agent_label` attribution fields intact. `docs/plans/plan_uaf_phase1_additive.md` moved to
  `docs/status/done_JAPES_2_4_0_UAF_PHASE1_ADDITIVE.md`.

- **Reasoning-model parameter guards, truncation-signal propagation, DB-session boundary
  checks.** Fixed OpenAI's temperature/reasoning_effort conflict (Responses and Chat Completions
  APIs both reject `temperature`/`top_p`/etc. once `reasoning_effort` is set) and Anthropic's
  thinking-shape/temperature-value constraints (Claude 4.7+ needs the `adaptive` thinking shape;
  `temperature` must be pinned to 1 when thinking is enabled) via new `model_cards` fields
  (`unsupported_request_params`, `thinking_shape`), applied precisely (gated on
  `reasoning_effort` actually being present, not blanket-on-model) at every raw-provider and
  Agents-SDK call site. Fixed `InteractiveAgent`'s agentic (skills-present) path never applying
  `spec.temperature` at all. Wired `fabric.db.session_guard.assert_no_open_db_session` into
  every LLM-call boundary (`InteractiveAgent`, `ConductorEngine` steps) so a DB session held
  across an LLM call fails loudly instead of risking a killed connection under
  `idle_in_transaction_session_timeout`. Propagated `ProviderResult.truncated` through
  `LLMResult` and `AgentExecutionTrace`, previously dropped silently at both construction
  boundaries. Fixed inconsistent truncation handling in the tool-calling agent providers
  (Anthropic raised a bare `ValueError`; OpenAI had no detection at all — built a raw
  `OpenAIResponsesModel` instead of the retry-wrapped model its own fast path already used).
  38 files changed, full suite green (3280 passed, 5 skipped).

- **Images (`.png`/`.jpg`/`.jpeg`/`.tif`/`.tiff`) are now a supported `convert_document` type** —
  previously "Unsupported document type" (no branch existed at all). Always routed to the
  `DocumentIntelligenceProvider` (the same `prebuilt-layout` call already handles images, not
  just PDFs) — there's no digital-text path for a raw image. `require_readable=True` refuses one
  outright, matching the existing scanned-PDF behavior.
- **New DocIntel page/cost accounting** — `reset_di_page_count()`/`get_di_page_count()` tally
  pages sent to a `DocumentIntelligenceProvider` (whole-document scanned, per-page mixed-mode, or
  image), per `asyncio` task via a `ContextVar` (confirmed empirically that concurrent tasks each
  get an isolated counter — no shared-state race in `process_dir`'s `fan_out`). `DocumentAgent.
  process()`'s `"convert"` tracer span now carries a `di_pages` attribute; `process_dir` sums
  every file's own count into a new `DirectoryResult.di_pages_processed` (zero for a run where
  nothing needed DocIntel, and zero for a file whose conversion was skipped via cached `.md`
  reuse or an already-current manifest entry, since no conversion ran that time). No OTel metric
  emission added — the repo has no metric plane yet; that's its own item.
- 18 new tests (`tests/test_tools/test_di_page_accounting.py` new, `tests/test_document_agent.py`,
  `tests/test_tools/test_conversion.py`, `tests/test_doc_pipeline_gaps.py` — the last one's
  existing `strict_inventory` fixture also updated: `.jpg` moved from `unsupported_type` to
  `excluded_by_pattern` now that images are supported). Full suite green (3201 passed, 3 skipped,
  no regressions). jaci audit: zero references to images or the new accounting functions
  anywhere in jaci; `docintel.py`'s real `.pdf` path still bypasses this module's routing
  entirely (confirmed earlier this session) — no behavior change for any existing caller.

- **Mixed-mode PDFs (some digital pages, some scanned) now route per page, not by one whole-
  document verdict.** `is_scanned` was a single document-wide average (`chars_per_page < 50`) —
  a 200-page package with 10 scanned pages stayed "digital" at that average, so those 10 pages
  contributed empty content, silently. `SimplePDFProcessor.process()` now also returns
  `page_texts` (per-page text, no extra file read) and a new `is_page_scanned` classmethod
  classifies each page independently. `convert_document`/`convert_document_and_structure`: fully
  digital or fully scanned stays the existing single-path behavior (no per-page cost for a
  uniform document); a genuinely mixed document extracts each scanned page as its own single-page
  PDF and sends it to the provider individually — cheaper than sending the whole document (only
  the scanned pages are billed) — merging back into one markdown string and one page-structured
  JSON, in page order and correctly renumbered. `require_readable=True` still refuses a mixed-mode
  document outright, as it already did for a fully-scanned one. 7 new tests (`tests/test_tools/
  test_pdf_mixed_mode.py`). Full suite green (3190 passed, 3 skipped, no regressions). jaci
  caller audit: the real `.pdf` path (`docintel.py`) never reaches this — it calls
  `SimplePDFProcessor().process()` directly with its own whole-document check, not
  `convert_document`/`convert_document_and_structure` — zero behavior change for any existing
  caller.

- **New `jazzx_sdk.tools.documents.workbook` — a full-fidelity workbook reader, the evidence-side
  counterpart to `conversion._xlsx_to_markdown`'s LLM-input flatten.** That function is lossy on
  purpose for markdown (formulas discarded, blank rows dropped, no merged ranges, no number
  formats) — fine for LLM input, not for citing where a value came from. `read_workbook(path)`
  keeps all of it: formula string *and* cached value together (confirmed empirically that
  `openpyxl`'s `data_only` flag is exclusive — a single load never gives both, so this opens the
  file twice and correlates by coordinate), merged-cell ranges, every row preserved (blank rows
  included, so a row index always matches the real sheet), and each cell's raw number format
  string verbatim (faithful, not interpreted — scale/sign/date semantics are a downstream
  decision, not this reader's). New `locate_cell_for_value` resolves a value to its `(sheet,
  cell)`. `DocumentAgent._resolve_locator` gained a `workbook` parameter (alongside the existing
  `structured` one from `PageLocator` resolution): an `.xlsx`/`.xlsm` processed with a `schema`
  now resolves each admitted field to a real `CellLocator` when found on a sheet, the existing
  `SectionLocator` fallback otherwise. `DocumentResult.had_workbook_view` + `assert_
  provenance_complete(strict_locators=True)` extended the same way the `PageLocator` gate already
  was. Namespace: `tools/documents/workbook.py`, not `finance/workbook.py` (that one's the write-
  side governed-export reporter — different package, different direction of data flow, no real
  collision despite the shared base name). 21 new tests (`tests/test_tools/test_workbook.py` new,
  `tests/test_document_agent.py`). Full suite green (3183 passed, 3 skipped, no regressions). jaci
  caller audit: the one real `schema=`-passing call site only ever hands it PDFs, never an
  `.xlsx` — zero behavior change for any existing caller; this capability has no live consumer
  yet, same as the `PageLocator` work before its own first real caller was built.

- **Added `.csv` support to `convert_document`** — previously absent entirely (`Unsupported
  document type`). Dialect-sniffed (delimiter/quoting, via `csv.Sniffer`) and encoding-fallback
  (utf-8 first, `latin-1` as the practical floor — it never actually fails to decode). Raises
  rather than guessing when the dialect can't be confidently detected from the file's own first
  lines. Renders under a synthetic `Sheet1` heading, same table-preserving markdown shape as the
  existing `.xlsx` route. New `csv_to_rows(path)` exposes the parsed grid directly — row/column-
  addressable, blank rows preserved (not dropped, unlike `.xlsx`'s current conversion) so a row
  index always matches the file's real row count. Purely additive: a `.csv` that used to raise
  now parses; nothing else changes. 6 new tests (`tests/test_tools/test_conversion.py`). Full
  suite green (3167 passed, 3 skipped, no regressions).

- **Breaking (behind `strict_inventory`, defaults off)** — `DocumentAgent.process_dir` used to
  silently omit any file that didn't match `pattern` (default `*.pdf`) — an `.xlsx`/`.csv`/image
  in the folder appeared in neither `processed`, `skipped`, nor `failed`. New `FileDisposition`
  enum (`processed`/`skipped_unchanged`/`failed`/`encrypted`/`unsupported_type`/
  `excluded_by_pattern`) + `DirectoryResult.dispositions: dict[str, FileDisposition]`.
  `strict_inventory=True` walks every file directly under the base path (non-recursive, matching
  `pattern`'s own scope) instead of just the glob match, so nothing is invisible. Default off:
  `False` is byte-for-byte the pre-existing scan scope.
- **Fixed, unconditional (not behind a flag) — `SimplePDFProcessor` no longer fabricates
  placeholder content on a corrupt or unreadable PDF.** It used to catch any read failure
  (missing PyMuPDF, corrupt file) and return a string like `"PDF file: x.pdf (error: ...)"` as
  the document's *successful* content — `convert_document`/`DocumentAgent.process` then
  classified and extracted from that fabricated string with no signal anywhere that it wasn't
  real. Now raises `DocumentConversionError` (or its new `DocumentEncryptedError` subclass for a
  password-protected PDF, detected via `needs_pass` before any page is read, not a downstream
  read failing opaquely). `DocumentAgent.process` propagates it; `process_dir` catches it
  per-file (existing `degrade` semantics) and records the right `FileDisposition` — `encrypted`
  gets its own reason, not lumped into generic `failed`. `is_readable()` catches the same error
  and returns `False` (a `bool`-only contract, unchanged) rather than raising.
- 12 new tests (`tests/test_tools/test_pdf_processor.py` new, `tests/test_doc_pipeline_gaps.py`,
  `tests/test_tools/test_conversion.py`, `tests/test_document_agent.py`). Full suite green (3161
  passed, 3 skipped, no regressions). jaci caller audit: one real `process_dir` call site
  (`portfolio_monitoring`), already uses `pattern="*"` — `strict_inventory`'s full-walk is a
  no-op there since that pattern already sees everything; the refusal fix is a pure correctness
  improvement, not a behavior change, for that caller.

- **Four phases of `plan_JAPES_2_5_0_LOCATOR_AND_INVENTORY_DISCIPLINE.md` landed (Phases 2, 6, 8,
  1 — the fully unblocked ones; Phase 4's inventory/refusal work, Phase 3's workbook/CSV work,
  Phase 5's routing-honesty work, and Phase 7's fail-loud floats remain, each gated on either a
  caller audit or an open design decision per the plan).**
  - **Phase 2 — `formula_version`/`approval_status` on `MetricDerivation`.** `evaluate()` now
    copies `MetricDefinition.version`/`.approval_status` onto every `MetricResult.derivation` it
    produces; `VersionBundle` gained an optional `metric_catalog_version`. (jaci-side mirroring —
    `MetricDerivation`, `metrics.yaml` explicit `version:` values — is separate, unstarted work.)
  - **Phase 6 — wired `check_completeness` onto `process_dir`.** New `required: Iterable[str] |
    None` param; when given, `DirectoryResult.completeness` carries the `CompletenessReport`
    reconciling this run's classifications against the checklist (`None` when omitted, unchanged).
  - **Phase 8 — `require_approver` on the suspension store.** `InProcessSuspensionStore`/
    `DbSuspensionStore(require_approver=True)` makes `mark_resumed` raise without an
    `approver_ref`. Found and fixed a real ordering gap while implementing this: `ConductorEngine.
    resume_durable` claims and runs the tail *before* calling `mark_resumed` — a store-level-only
    guard would have let an unapproved resume's side effects run before failing at the very last
    step. `resume_durable` now checks the same flag itself, before claiming anything.
  - **Phase 1 (P0) — `PageLocator` wiring, "ship page alone first".** Every extracted field's
    `SourceCoordinate` pointed at a filename + the field's own name (`SectionLocator(path=name)`)
    even though `PageLocator`/`CellLocator` have existed, unconstructed, since the evidence schema
    was authored. New `DocumentIntelligenceProvider.convert_both` (one `analyze()` call for both
    markdown and page-structured JSON — `AzureDocIntelligenceProvider` overrides it to actually
    share the call; avoids doubling Azure spend for a caller wanting both views) and
    `convert_document_and_structure` (the structure-carrying sibling of `convert_document`).
    `DocumentAgent.process` now resolves each admitted field to a `PageLocator` via a new
    `locate_page_for_value` (a value→page text search — deliberately simpler than the anchor/
    template locators in `tools.extraction`, since the generic schema-extraction path has no
    anchors to locate against) when a structured view exists and the value is found on a page;
    falls back to the pre-existing `SectionLocator` otherwise (unchanged default). `region` is
    deliberately left unset — the open region-shape decision doesn't block page-level precision.
    `assert_provenance_complete` gained `strict_locators: bool = False`: when true, fails on a
    `SectionLocator` field where a structured view was available (`DocumentResult.
    had_structured_view`, new); `doc_type` is exempt (a whole-document classification has no
    single page even when a structured view exists). 34 new tests across `tests/
    test_locate_page_for_value.py` (new), `tests/test_document_agent.py`, `tests/
    test_docintel_azure.py`, `tests/test_doc_tier_routing.py`. Full suite green (3149 passed, 3
    skipped, no regressions) — including a real bug the refactor surfaced and fixed in the
    process: `test_document_agent.py`'s `_stub_convert` fixture was silently patching the wrong
    (now-unused) function, so several `process()` tests were passing by accident (a fake-PDF
    fabricated-error-string plus a classify fake that ignores its input masked it).

- **Two fixes from an external review of `ToolStreamHooks`/tool-arg streaming.** (1)
  **`InteractiveAgentSpec.stream_tool_events=True` used to silently discard a caller-supplied
  `hooks=`** — `_agent_hooks` picked `_tool_stream_hooks` over `hooks` outright, so a caller
  wanting both tool-event streaming and their own `AgentHooks` had no way to get both short of
  reimplementing `ToolStreamHooks` themselves. New `CompositeAgentHooks` runs both for every
  `AgentHooksBase` callback instead of one discarding the other. (2) **New `InteractiveAgentSpec.
  stream_tool_args: bool = True`** — `False` publishes `ToolStartEvent.tool_name` only, no
  arguments at all, for a caller that doesn't want raw tool args (which can carry an internal
  search pattern, a storage filename, an internal finding key) reaching a stream consumer.
  Field-level redaction (vs. this all-or-nothing cutoff) already has a home:
  `StreamPublisher(event_transformer=...)`, shipped this same release — runs on the constructed
  event right before publish, with access to whatever per-turn state the caller closes over
  (e.g. `get_streaming_id()` to key into a per-turn display-name map). 7 new tests
  (`tests/test_tool_stream_hooks.py`, `tests/test_interactive_agent.py`). Full suite green (3120
  passed, 3 skipped, no regressions).

- **Two document-ingest gaps closed, found while reviewing real client documents against the
  pipeline.** (1) **`convert_document` gained `.pptx` support** — new `_pptx_to_markdown`
  (`python-pptx`, new optional `pptx` extra), one `## Slide N` section per slide, text frames and
  tables rendered in original shape (z-)order (no pandoc path: pandoc can write pptx but not read
  it). (2) **`split_document`'s page-classification fallback (used when a combined PDF has no
  outline/bookmarks) is no longer fully sequential.** It ran one `classify_document` LLM call per
  page in a plain loop — for a real multi-hundred-page combined loan-document package with no
  bookmarks, that's hundreds of sequential calls just to segment it before any extraction starts.
  Now dispatched via the existing `jazzx_sdk.conductor.fan_out` (order-preserving, bounded
  concurrency — same primitive `DocumentAgent.process_package`/`process_dir` already use for their
  own fan-outs). New `split_document(..., concurrency: int = 8)`, and
  `DocumentAgent.process_package`'s existing `concurrency` param now also bounds this pass, not
  just its own post-split per-segment fan-out. 5 new tests (`tests/test_split.py`,
  `tests/test_tools/test_conversion.py`). Full suite green (3115 passed, 3 skipped, no
  regressions).

- **Follow-on to the reasoning-summary streaming work above: closes the per-agent-attribution gap
  it explicitly left open, plus three more issues from the same external review.** (1)
  **Agent attribution.** `common.core.streaming.ReasoningEvent` gained `agent`/`agent_label`
  fields (bumped `common` submodule pin) — the gap really did need a schema change there
  (verified empirically before touching the submodule: constructing `ReasoningEvent(...,
  agent=...)` against the unmodified class silently dropped the kwarg, pydantic's default
  `extra="ignore"`). `publish_reasoning_delta` now takes `agent: str | None`; the top-level drain
  passes the parent agent's own `.name`, and each skill's `on_stream` closure passes
  `stream_event["agent"].name` — the OpenAI Agents SDK's own `AgentToolStreamEvent["agent"]`,
  the actual emitting sub-agent, not assumed to equal the parent. Degrades silently against an
  older pinned `common` (unrecognized constructor kwarg, same as `ReasoningEvent` itself being
  absent). (2) **Per-skill `Skill.stream_reasoning: bool | None`** — overrides the parent
  `InteractiveAgentSpec.stream_reasoning` for just that skill when set; `None` inherits
  unchanged. (3) **The streamed reasoning path now gets the same retry `run_with_recovery`
  already gives the non-streamed path** (`ModelBehaviorError` schema-validation retry,
  `IncompleteOutputError` truncation retry, `APIStatusError` backoff) — turning on
  `stream_reasoning` was silently trading this away, since `_respond_agentic` called
  `_run_streamed_once` directly instead of wrapping it. Only the context-window-fallback tier
  stays skipped (retries via forced session compaction, not meaningful mid-stream). (4) **New
  `StreamPublisher(event_transformer=...)` hook** — runs on every event immediately before
  publish (sync or async, via `concurrency.call_maybe_async`); return the event unchanged, a
  modified one, or `None` to suppress. Fail-closed on a transformer exception: suppresses rather
  than publishing the untransformed original, since a transformer may exist specifically to
  redact. Closes a real gap: japes published `ReasoningEvent`s straight to Redis with no
  interception point, so a consuming service couldn't humanize, redact, or gate reasoning content
  reaching a UI. 11 new/updated tests across `tests/test_sse_streaming.py` and
  `tests/test_interactive_agent.py`. Full suite green (3112 passed, 3 skipped, no regressions).

- **New `jazzx_sdk.authority.resolve_authority` — closes a real gap in the RBAC/authority survey:
  `fabric.canonical.policy.AuthMatrix`/`AuthorityEntry` (role, `action_scope`, threshold
  `ceiling`, `escalation_target`, `delegation_chain`) was schema only — nothing in the SDK
  actually walked it.** Distinct from `authority.resolver`'s `check_action`/`AuthorityMatrixV2`
  (autonomy *ceilings* — how much an AI decision can act without a human, across
  binding/overlay/profile layers): this resolves human **approval authority** — which role in a
  compliance-style delegation chain (an L1 investigator escalating to L2, then to a BSA officer)
  actually covers a decision's attributes, given the role attempting it. Walks
  `escalation_target` from the starting role until a `ceiling` covers the case or the chain
  refuses — numeric ceiling dimensions compare by magnitude; a non-numeric one (e.g. a
  categorical `risk_tier`) needs a caller-supplied rank (`tier_orders`) since the SDK can't know
  a domain's ordering, same discipline `authority.context.PermissionScope` already applies to its
  own opaque resource selectors — and fails **closed** (escalates) rather than guessing when it
  can't rank a value. Returns the resolving `AuthorityEntry` plus the `escalation_path` walked (an
  audit trail, not just yes/no) or a typed `Refusal` — reusing the existing `RefusalClass` taxonomy
  (`OUT_OF_SCOPE` for an unknown role/action, `AUTHORITY_EXCEEDED` when the chain dead-ends with
  nowhere left to escalate, `POLICY_CONFLICT_UNRESOLVED` for a matrix bug — an escalation cycle or
  a pathologically long chain), matching `check_action`'s own established return-shape convention
  exactly. 17 new tests (`test_authority_delegation.py`). Full suite green (3103 passed, 3
  skipped, no regressions).
- **Three findings from surveying `kernel`'s recent history for japes evolution opportunities,
  all built.** (1) `QueueProcessor.process_loop` no longer treats every dequeue error the same —
  `kernel`'s `common` submodule grew a permanent/transient distinction after a real incident
  (retrying a bad-credentials or missing-queue error forever at the same fixed poll cadence);
  japes' own queue processor didn't have this independent of whatever `common` has. New
  `dequeue_message` classification (via the already-existing `jazzx_sdk.failures.classify_failure`
  taxonomy — status-code 401/403/5xx already covered there; 404 checked directly since a missing
  queue is unambiguous, unlike `classify_failure`'s other, more general callers) sets
  `last_dequeue_error` and tracks a consecutive-error streak; `process_loop` backs off
  exponentially (`jazzx_sdk.concurrency.backoff_delay`, capped at 5 minutes) on any dequeue error
  instead of `poll_interval` — a genuinely empty queue is unaffected, byte-identical to before.
  (2) New `jazzx_sdk.failures.redact_for_zero_retention(value)` — the whole-value **substitution**
  counterpart to `redact_fields`/`redact_code_blocks`'s content-**scanning** redaction (those scrub
  known-sensitive substrings from a payload that's still stored; this is for a caller-declared
  policy — "do not persist this tool's args/response at all" — replacing the whole value
  regardless of content). `kernel` built a per-tool zero-data-retention flag doing exactly this;
  japes had the scan-and-scrub half of this family but not the substitution half. Deliberately just
  the mechanism, not a "which tools are ZDR" policy API — that's pack/service data japes doesn't
  own. (3) `DbStore.get_session()`'s docstring now warns explicitly against manually driving the
  generator outside a real DI framework's teardown guarantee — `kernel` just fixed the exact
  incident this enables in production (an early return abandoning the generator mid-yield, pool
  exhaustion since cleanup then only runs on GC): 47 files, 186 call sites. Japes' shape is
  identical; the context-manager alternative (`DbStore.session()`, already the documented default)
  was already correct, this closes the gap where the risky path wasn't warned against by name.
  34 new tests (`test_queue_processor.py`, `test_failures.py`, `test_fabric_db.py`). Full suite
  green (3086 passed, 3 skipped, no regressions).
- **New `jazzx_sdk.fabric.db.session_guard` — catch a DB session held open across a slow call
  ("transaction islands"), at the point of misuse instead of minutes later as a killed
  connection.** A DB session/transaction left open while awaiting an LLM call, a tool/sub-agent
  run, an MCP round trip, or an SSE yield ties up a connection (and, on Postgres, an open
  transaction) for however long that call takes — under
  `idle_in_transaction_session_timeout` the connection is killed out from under the caller,
  typically losing whatever the call produced with no clear error at the point that caused it. A
  subtle, load-dependent failure mode (SQLAlchemy autobegins a transaction on the first
  statement, not on session-open, so it's easy to write by accident) that's hard to reproduce
  outside production LLM latencies — surfaced by a real, well-evidenced incident in `juno`'s own
  history (its postmortem-driven fix there: an enforced three-phase
  prepare-with-db/run-without-db/finalize-with-fresh-db invariant). Checked `jazzx_sdk/fabric/db/`
  first — no equivalent guard existed, and japes' own `DbStore`/`SqlConversationStore` are the
  identical shape (a DB row read/written around a potentially long-running operation), so any
  pack using them today has the same latent exposure. New `assert_no_open_db_session(label)` —
  call immediately before the slow operation; raises `DbSessionHeldError` right there if a
  session is still open, turning a load-dependent production incident into an immediate,
  deterministic, testable failure. `DbStore.session()` and `SqlConversationStore`'s two session
  paths (`fabric.db`-backed and the raw-sessionmaker fallback) now track their own lifetime via
  `track_open_session()` automatically — no caller-side change needed for the assertion to see
  them; per-task via `contextvars` (concurrent tasks never see each other's open sessions) and
  nesting-safe. 10 new tests (`test_session_guard.py`, `test_fabric_db.py`,
  `test_fabric_conversation.py`). Full suite green (3077 passed, 3 skipped, no regressions).
- **New `jazzx_sdk.concurrency_guard.ConcurrencyGuard`** — a Redis `SET NX EX` lock keyed by a
  caller-extracted business key, wired as an optional `QueueProcessor(concurrency_guard=...)`
  param (mirrors how `idempotency_store` is already wired). Distinct problem from
  `automation.idempotency.IdempotencyStore`: that answers "have I already processed *this exact
  message*" (same message id, redelivery/retry dedup); this answers "is a run already in
  progress for *this business key*" — two genuinely different messages (a double-submit, a
  legitimate re-invocation) that both target the same downstream resource (a case, a loan, a
  conversation) can race even though neither is a redelivery of the other. Generalized from a
  design built for one caller's own hardcoded key (`loan_collection_id`, gated on a specific
  routing target) into a caller-parameterized primitive: `key_extractor(message) -> str | None`
  decides both which messages need guarding at all and what key identifies "the same resource"
  — the mechanism (owner-safe Lua-script release/extend so one worker can never touch another's
  lock, TTL matched to typical queue visibility timeouts, fail-open on a Redis error rather than
  stalling all queue processing on one dependency) is the platform's; the key policy is the
  caller's. Motivated by the same structural risk showing up anywhere a queue-driven, case-keyed
  conductor run exists — `AdjudicationAgent`-shaped scenarios included, not just the original's
  single caller. Checked the one live production consumer this generalizes from directly (its
  own worker code, not just the stale, never-merged design it came from) and found two follow-on
  gaps worth closing in the same pass, not deferred: (1) no backend existed for tests/single-
  worker dev without standing up real Redis — new `InProcessConcurrencyGuard` (an `asyncio.Lock`
  per key, explicitly documented as carrying no cross-process guarantee at all), with both
  implementations now formalized behind a `ConcurrencyGuardProtocol` `QueueProcessor` accepts,
  matching the `IdempotencyStore`-family Protocol convention already used elsewhere in this SDK.
  (2) The module docstring now explicitly warns against scoping `key_extractor` to a resource id
  alone (e.g. just a loan id) — two *unrelated* operations sharing a resource (an ad-hoc Q&A
  query and a scheduled job for the same loan) aren't duplicates and would be wrongly serialized;
  recommends `(resource, operation)` instead, matching what the original single-caller design
  was itself careful about (gated on a specific routing target, not the resource id alone) —
  care a naive generalization could otherwise have quietly dropped. 32 new tests
  (`test_concurrency_guard.py`, `test_queue_processor.py`). Full suite green (3067 passed, 3
  skipped, no regressions).
- **`DocumentAgentSpec.classify_max_chars`** — a per-agent override for `classify_document`'s
  text-sample cap, previously hardcoded at 8000 chars with no way for `DocumentAgent.classify()`
  to raise it. Prompted by a real report: a healthcare document misclassified even after adding a
  taxonomy class for it. Traced through the actual classify/extract contract to confirm two
  separate things: (1) `DocumentAgentSpec.taxonomy` is genuinely domain-builder-supplied (defaults
  to empty; `classify_document` raises if empty) — expected, not a bug; (2) extraction needs its
  own caller-supplied schema independent of the taxonomy (`DocumentAgent.process(schema=None)`
  skips extraction entirely) — a mismatched/generic schema there, not a japes bug, is the more
  likely explanation for a separately-reported extraction-mislabeling case. But classification
  itself had a real, confirmed gap: `classify_document`'s LLM call only ever sees the document's
  first 8000 characters, and nothing in `DocumentAgentSpec` could raise that — a document whose
  type-identifying content sits past the first few pages is architecturally invisible to the
  classifier regardless of taxonomy quality. New `classify_max_chars: int | None = None` on
  `DocumentAgentSpec`, threaded through `DocumentAgent.classify()`; unset behaves exactly as
  before (classify_document's own 8000 default). 2 new tests (`test_document_agent.py`). Full
  suite green (3035 passed, 3 skipped, no regressions).
- **Per-skill `max_turns` now falls back to the parent's own resolved turn budget, not the SDK's
  bare default of 10.** The other half of this session's earlier `InteractiveAgent` MaxTurns fix
  — that one only raised the *parent* orchestrator's `Runner.run`/`run_streamed` default (10 →
  30); a skill's own sub-agent run (`Agent.as_tool(max_turns=...)`) still passed an unset
  `Skill.max_turns` straight through as `None`, landing on the SDK's bare 10. Surfaced by a real
  consumer independently hitting it: their skill YAMLs each hand-set `max_turns: 50` with a
  comment explaining the exact same gap, on every one of their skills. `_build_parent_tools` now
  resolves a `default_skill_max_turns` once (mirroring `spec.max_turns` unset →
  `_DEFAULT_AGENTIC_MAX_TURNS`, same as the parent) and a skill without its own `max_turns`
  inherits that — same fallback shape `model` already uses. 2 new/updated tests
  (`test_interactive_agent.py`). Full suite green (3033 passed, 3 skipped, no regressions).
- **Dependabot: mlflow/sqlparse floors bumped, closing 5 open alerts (1 critical, 3 high, 1
  medium).** `mlflow` floor `>=2.9` → `>=3.15.0` (fixes the critical unauthenticated SSRF in
  webhook delivery — `_validate_webhook_url` bypassed via unvalidated redirects/DNS rebinding).
  `sqlparse` — pulled in transitively by mlflow-skinny (`>=0.4.0,<1`, no upper cap) — gets a new
  explicit floor `>=0.6.0`, closing 3 ReDoS/CPU-DoS alerts plus an unescaped-backslash SQL-breakout
  one, matching the file's existing convention of pinning vulnerable transitive deps explicitly.
  `poetry lock` resolves cleanly with no forced regression elsewhere (`cryptography` stays at
  48.0.1 — the separate, already-documented, not-yet-fixable alert #98 is untouched). Verified
  by actually installing the `mlflow` extra (not just trusting the lock solve) and confirming
  `mlflow`/`mlflow-skinny` land on 3.15.1 and `sqlparse` on 0.6.0. Full suite re-confirmed against
  this repo's real baseline dev extras (`finance` + `templating`; `mlflow`/`azure` are
  genuinely absent by design — those tests exercise the extra-not-installed fallback path) —
  3032 passed, 3 skipped, byte-identical to before the bump.

## [2.4.2] - 2026-08-17

- **`ConductorEngine` gains opt-in step-failure recovery (`on_step_error`); the reference chat
  pipeline (`pipelines/chat.py`) wires a default one.** Follow-on to the `InteractiveAgent`
  MaxTurns fix above: asked whether the reference chat pipeline shared the same class of
  problem. It didn't share that *specific* bug (`answer_step` calls `agent.respond()` directly, so
  it already inherited the fix for free) — but reading `ConductorEngine._run_step` found the same
  *shape* of gap one layer up: a step component's exception was never caught anywhere in the
  engine (only `SuspendRun`, a control signal, was special-cased), so any step failing propagated
  raw out of `run()`/`resume()`. New `on_step_error` constructor param (`StepErrorHandler`, opt-in,
  default `None` — every existing pipeline is byte-identical): on a step exception (never
  `SuspendRun`), it's handed `(step, state, exc)`; its return value becomes the step's emitted
  output exactly as if the step had returned normally, and the run continues (`ExecutedStep`/
  `StepEvent` get a new `"errored"` status alongside `ran`/`skipped`/`halted`, so a recovered step
  is distinguishable from a clean one in a trace). The handler re-raising propagates unchanged.
  `pipelines/chat.py` wires this by default (`default_step_error`, overridable via
  `run_chat_turn(on_step_error=...)`, `None` to opt out): a degraded `InteractiveResponse`
  (reusing `incomplete`/`incomplete_reason`, the same fields the `InteractiveAgent` fix added)
  instead of a crash. Caught a real correctness trap while designing this, not just implementing
  it: a naive version that let the substitute value flow through normally would silently break
  `chat_guards()`'s `_route`, which expects a `GateDecision` in `state.emitted["gate"]` — a gate
  failure recovered that way would crash the *next* step's guard instead of the step itself. Fixed
  by having `default_step_error` always set `state.halt = True`, so no downstream guard ever runs
  against a substituted value regardless of which step failed; `run_chat_turn` falls back to
  scanning `emitted` for the `InteractiveResponse` when `finalize` didn't get to run because of the
  halt. 9 new tests across `test_conductor_engine.py`/`test_interactive_chat.py` (including one
  that pins down the gate-failure/guard-crash trap as a regression case). Full suite green (3032
  passed, 3 skipped, no regressions).
- **`InteractiveAgent` agentic-path latency/robustness pass.** Prompted by a production report of
  an assistant chat regularly taking >60s/query, then a direct question of whether "interactive"
  had any architectural landmines. Audited retry scoping, model/effort tiering, tool-call
  concurrency, fast-path routing, and MaxTurns handling against the actual code (not assumed);
  most were already fine (tool calls already run concurrently via the SDK's own executor; a
  nested skill's failure is already absorbed by the SDK's `as_tool` error handling, not a full
  outer-run redo). Two real gaps, both fixed: (1) the agentic path had **no MaxTurns handling at
  all** — `run_with_recovery` deliberately excludes `MaxTurnsExceeded` (rebuilding the agent isn't
  its job), so an unset `spec.max_turns` fell through to the SDK's bare default of 10 (tuned for a
  single-purpose agent, not one that may delegate through a nested skill sub-agent's own turns) and
  a genuinely complex multi-tool turn raised `MaxTurnsExceeded` straight out of `respond()`
  uncaught — a hard crash, not a slow answer. Now: an unset `spec.max_turns` defaults to 30
  (matching `run_agent`'s own tuned default) instead of the SDK's bare 10, and `_respond_agentic`
  catches `MaxTurnsExceeded` and returns a typed degraded `InteractiveResponse` (new
  `incomplete`/`incomplete_reason` fields, same shape as the existing `blocked`/`block_reason`)
  instead of propagating the raw SDK exception. (2) `Skill` had a per-skill `model` override but no
  `reasoning_effort` override — a routing/classification-style skill or a deterministic-lookup
  skill had no way to run cheaper/faster than the parent orchestrator without also switching
  models. New `Skill.reasoning_effort: str | None`, threaded into that skill's sub-agent's own
  `ModelSettings` (built fresh via `build_model_settings` when set; unset skills keep inheriting
  the parent's `ModelSettings` unchanged). 3 new/updated tests in `test_interactive_agent.py`.
  Full suite green (3024 passed, 3 skipped, no regressions).
- **`MlflowTracer` self-sanitizes leaked OTLP env vars; new `enable_mlflow_agent_autolog()`.**
  Surveyed a companion service's own tracing package (already using `InteractiveAgent`) for
  japes evolution opportunities and found `sanitize_leaked_otel_env_vars` (added earlier — strips
  the `OTEL_EXPORTER_OTLP_ENDPOINT` vars Azure Container Apps injects platform-wide, which
  otherwise silently break MLflow's span exporter) was never actually called by anything in
  japes, `MlflowTracer` included — confirmed via a full-package grep. Its own docstring claims
  to spare every consumer from reinventing the guard, but two companion services had each
  carried an independent copy anyway, since the one class that should self-apply it didn't.
  Now wired into `MlflowTracer._mf()`, once, before the first real `import mlflow` is cached —
  scoped exactly to the MLflow-tracing case the function's docstring already carves out (an
  injected `mlflow_module`, e.g. tests, is untouched; OTel infra tracing is untouched). Second
  gap from the same survey: no toggle for `mlflow.openai.autolog()` (nested-agent-call MLflow
  tracing) existed in japes at all — every consumer wanting it had to hand-roll the idempotent
  enable-once wrapper themselves. New `enable_mlflow_agent_autolog()` in
  `observability.mlflow_env`, alongside the existing `flush_mlflow_async_trace_queue` (same
  "process-level MLflow hygiene, call once" style) — idempotent, best-effort, never raises.
  Both re-exported from `jazzx_sdk.observability` and the SDK root. 5 new tests
  (`test_observability.py`, `test_otel_tracking.py`). Full suite green (3022 passed, 3 skipped,
  no regressions).
- **`ScorerResult` gains `findings: list[Finding]`.** Same `policy-workbench` survey, its third
  candidate: `policy_evaluator`'s `EvaluationIssue` (phrase/issue/suggestion triplet, an LLM
  flagging specific spans) is a recurring "list of flagged items" shape `ScorerResult` had no
  first-class slot for — every consumer was left to invent its own triplet in the freeform
  `metadata` bag. New `Finding` model (`subject`/`description`/`suggestion`/`severity`, all but
  `subject`/`description` optional) + `ScorerResult.findings`, defaulting to `[]` (existing
  callers unaffected). `CompositeScorer` and every built-in adjudication policy (`_adjudicated`)
  now union `findings` from applicable (non-skipped) sub-scorer results into their own verdict —
  same skip-exclusion rule the score/pass aggregation already uses. `AdjudicatorScorer` fills
  `findings` from the inline sub-results only when a custom `adjudicate` callable left them
  empty — never overwrites what the callable set itself. Kept the eval-service convergence
  contract (`scorer_result_to_verdict_v1`, "lossless adapter", Phase 4 acceptance criterion #13)
  actually lossless: `findings` didn't exist when that contract was negotiated and
  `ScorerVerdictV1` has no dedicated wire field for it — extending that cross-repo contract is
  out of scope for a japes-side change alone, so it's folded into `metadata["findings"]`
  (a list of dicts) instead, verified round-trip in `test_scoring_execution_adapters.py`. Both
  `jazzx_sdk.evaluation` and `jazzx_sdk.contracts` re-export `Finding` alongside `ScorerResult`.
  12 new/updated tests across `test_scorers.py`/`test_scoring_execution_adapters.py`. Full suite
  green (3017 passed, 3 skipped, no regressions).
- **`fan_out` gains `skip_if` — resumable fan-outs.** Surfaced by surveying `policy-workbench`
  (a real, independent multi-agent app, no japes awareness) for japes evolution opportunities:
  its `policy_creator` agent hand-rolls exactly this via `_staged_jtbd_files`/
  `_staged_section_files` — re-scanning a tmp/ staging dir on every call to know which
  plan-items (sections) a prior partial run already finished, so a retry doesn't redo completed
  work. `fan_out` itself had no such notion (single-shot, in-memory, verified by reading it
  directly rather than assumed). `skip_if(item, index)` — sync or async, dispatched via the
  existing `concurrency.call_maybe_async` — runs before `process`; a truthy result skips that
  item entirely (`process` never called), its slot is `None` (same convention `degrade`'s
  failure path already uses), and the skipped item still opens a tracer span (`inputs={...,
  "skipped": True}`) so it reads as "known done" in a trace, not silently absent. `None`
  default: byte-identical to before. Considered and deliberately did NOT build a bundled
  "plan → dispatch → synthesize" pipeline primitive for the same survey's other candidate
  (`policy_modifier`/`policy_creator` both hand-roll that shape too) — once `skip_if` exists,
  the remaining pieces (`output_schema` for the structured plan, `run_with_recovery` for retry,
  dict-based dispatch-by-field) are already a few lines of ordinary caller code over existing
  primitives; a new abstraction for that would be premature (no second real japes-side
  consumer asking for it, unlike `investigation_loop`, which unified 6 *existing* hand-rolled
  loops within this codebase before being built). 7 new tests (`tests/test_fanout.py`). Full
  suite green (3011 passed, 3 skipped, no regressions).
- **`InteractiveAgent` reasoning-summary streaming.** Prompted by an external review of three
  specific gaps (hardcoded `Reasoning.summary="auto"`, `respond()` had no way to observe
  reasoning deltas, nested skill sub-agents had no reasoning visibility at all); verified each
  against code, then generalized into one consistent mechanism rather than three separate
  patches. `build_model_settings` gained `reasoning_summary` (e.g. `"concise"`), threaded
  through new `InteractiveAgentSpec.reasoning_summary`. New `InteractiveAgentSpec.
  stream_reasoning: bool` mirrors `stream_tool_events`'s exact scope (parent run + every skill
  sub-agent) via the mechanism each actually requires: `_respond_agentic` switches its internal
  `_run_once` to `Runner.run_streamed` + a full `stream_events()` drain only when set (`respond()`'s
  return contract is unchanged; `run_with_recovery`/context-window-fallback retry don't apply in
  that mode — the same tradeoff `_stream_agentic` already documents, for the same reason), and
  `_build_parent_tools` passes `on_stream=` to each skill's `sub_agent.as_tool(...)`. One shared
  classifier, `stream_hooks.reasoning_delta_text`/`publish_reasoning_delta`, serves both call
  sites — `AgentToolStreamEvent["event"]` is the identical `RawResponsesStreamEvent` shape the
  top-level drain already handles (verified against the installed SDK). Reasoning deltas
  publish through the same `publish_event` sink `ToolStreamHooks` already uses, not a second
  generator-yield channel — using `common.core.streaming.ReasoningEvent` (already reserved
  ahead of any producer in `common`'s own history), imported guarded like `FinalResultEvent` so
  an older pinned `common` degrades to a silent no-op. Real, not papered over: neither
  `ReasoningEvent` nor `ToolStartEvent`/`ToolEndEvent` carry a per-event agent-attribution
  field, so nested skill reasoning publishes unattributed today — a pre-existing gap across the
  whole event family, not new here; fixing it needs a `common` schema change, out of scope for
  a japes-side pass. 10 new tests (`tests/test_reasoning_stream_hooks.py`,
  `tests/test_agent_models.py`, `tests/test_interactive_agent.py`). Full suite green (2998
  passed, 3 skipped).
- **New `jazzx_sdk.tools.documents.local_cache`** — the local dev/demo document cache (a git-
  committed filename→remote-doc-id manifest that hydrates a stubbed local file from a shared
  Knowledge Hub on demand) generalized from a jaci-specific module. Nothing in the original was
  domain-specific — pure filename↔doc-id bookkeeping — so this is a direct lift:
  `manifest_path`/`read_manifest_entry`/`record_push` (two independently-mergeable tiers,
  derived-markdown and raw-original), `ensure_local_cache`/`ensure_local_caches` (two-tier pull,
  cheapest first), `StalenessInfo`/`check_staleness` (cheap metadata-only mismatch check, never
  auto-resolves). Composes ahead of `convert_document` as a separate async pre-step (same
  "sync callers, async fabric fetch" reasoning the original had) rather than a `fabric=` param
  on `convert_document` itself. Re-exported from `jazzx_sdk.tools`. 10 new tests
  (`tests/test_local_cache.py`).
- **`DocumentAgent.process_dir(collection_id=...)` now has a real Knowledge-Hub-backed
  integration test**, not just a hand-rolled fake `DocStore`. Confirms the full path —
  `sync_collection` → `MockKnowledgeHubClient.list_documents`/`materialize`'s download →
  classification — actually works end-to-end, not just that `process_dir` calls
  `sync_collection` correctly (`tests/test_doc_pipeline_gaps.py`).
- **`MockKnowledgeHubClient` now persists documents and ontologies, not just entities (issue
  #57 part a).** `_load_from_data_dir` already loaded all three from `data_dir` on startup, but
  only entity mutations wrote back — a document or ontology created/updated/deleted during a
  session vanished the moment the process restarted (every Streamlit rerun, or any multi-
  process pipeline). `_persist_entities` generalized into a shared `_persist(store_attr,
  filename)` helper (`_persist_ontologies` reuses it directly); documents get their own
  `_persist_documents` since `content` is arbitrary bytes (PDFs, zips, not just UTF-8 text) —
  base64-encoded before `json.dumps`, decoded back on load, rather than silently mangled by
  `json.dumps(..., default=str)`'s `str(b'...')` fallback. Wired into every mutator:
  `create_document`/`update_document`/`delete_document` (`create_document_v2`'s idempotent-hit
  branch needs nothing new — it returns an existing record, doesn't mutate) and
  `create_ontology`/`upload_ontology`/`update_ontology`/`delete_ontology`. Found and left alone
  along the way: `get_document`'s docstring promises `None` on a miss but actually fabricates a
  fake document — pre-existing, unrelated, not touched. 10 new tests
  (`tests/test_mock_kh_persistence.py`, new file), each constructing a fresh client against the
  same `data_dir` to prove the write actually crossed a process boundary, not just an in-memory
  round-trip.
- **`FabricConfig.validate_for_mode()` no longer requires `knowledge_hub_url` when a client is
  already supplied (issue #57 part b).** STRICT/CACHED's `knowledge_hub_url` check exists so
  *something* can build a client from it; a caller who already constructed one (real or Mock)
  and hands it straight to `KnowledgeFabric(kh_client=..., config=...)` doesn't need it —
  before this fix that caller had to pass a throwaway URL string (e.g. jaci's
  `shared/fabric.py::build_fabric` used `knowledge_hub_url="mock://local-kh"`, "never dialed")
  just to pass validation. New `validate_for_mode(*, has_client: bool = False)` param, defaults
  to the old strict behavior (`from_env()`'s own call site, which never sees a client, is
  unaffected); `KnowledgeFabric.__init__` now passes `has_client=kh_client is not None`. 9 new
  tests (`tests/test_fabric_config.py`, new file — no prior dedicated coverage of this method).
- **`AllOfCondition`/`AnyOfCondition` — composite `Condition` combinators (P8,
  `ENCODING_NOTES.md` G1 / `policy-ir-abstraction.md` P3).** Several real conjunctive rules
  (e.g. "warrantable condo outside Florida," a multi-field prepayment-penalty gate) had no
  honest encoding: folding the extra predicate into a `MatrixCondition` axis multiplies cells
  and destroys reviewability; burying it in a `DslExpression` formula defeats the same
  reviewability discipline `RatioCondition`'s `profile:` rule protects. `AllOf`/`AnyOf` nest any
  existing kind, including each other (depth-capped at 5), and must be authored with an
  explicit `kind:` — unlike `matrix`'s axes-key sniff, a bare `conditions: [...]` list can't
  structurally distinguish the two. Verdict algebra: `AllOf` is `VIOLATED` if any child is,
  else `INDETERMINATE` if any child is (dominates `SATISFIED` — the safe direction), else
  `SATISFIED`; `AnyOf` mirrors it. Every child evaluates unconditionally, never short-circuited,
  so `RuleOutcome.inputs["limbs"]` always shows every limb's own state. `evidence_contract()` is
  the union of every child's contract, so `check_compliance`'s cross-policy field-claiming
  precedence still works for a composite. Dispatches through the existing
  `get_condition_evaluator(kind)` registry — `DefaultPolicyExpert.check_compliance` needed zero
  edits. Known, documented limitation (not fixed this pass): `execution`/`stochastic` are fixed
  DETERMINISTIC/False class attributes looked up by `kind` alone, so a composite nesting a
  `natural_language` (LIVE) child would still evaluate correctly but be misclassified as
  DETERMINISTIC by the adjudication chassis's `partition_rules` — deferred until a real
  composite mixes LIVE and DETERMINISTIC children. 19 new tests across
  `test_condition_evaluator.py`, `test_default_policy_expert.py`, `test_adjudication_
  partition.py`.

- **`find_profile_literal_drift`/`assert_no_profile_literal_drift`** (P8, `policy-ir-
  abstraction.md` P4a) — a new `jazzx_sdk/fabric/canonical/policy_lint.py`. `RatioCondition.
  threshold` must be `profile:<key>` so thresholds stay reviewable in one place; `Expression.
  value` takes bare literals, so a pack that duplicates a literal into `PolicyProfile.custom`
  for review has nothing enforcing the two stay equal. The lint checks any `Expression`
  declaring `domain_extensions["profile_custom_key"]` against its named `PolicyProfile.custom`
  twin — no schema change (`Expression.domain_extensions` already existed). 8 new tests.

- **`MatrixCondition` — a table-valued `Condition` kind (P8, D2).** Generalizes
  `RatioCondition`'s single `profile:<key>` threshold to a lookup keyed by N axes (e.g.
  loan-amount band x FICO tier x purpose), each independently numeric-banded or categorical —
  the primitive an eligibility grid needs instead of dozens of near-duplicate rules or DSL
  `if()` chains that bury the numbers. Resolved cell values live in a new
  `PolicyProfile.tables` bucket (`profile_table:<name>` reference, fail-closed
  `PolicyProfile.get_table()`) — never a literal, same discipline `RatioCondition` already
  enforces. An explicit `NA`/`False`/`None` cell evaluates to `VIOLATED` (the grid gave a real
  answer), not `INDETERMINATE`. Fully additive: `DefaultPolicyExpert.check_compliance` and the
  adjudication chassis's `partition_rules`/`impacted_rules` all dispatch via the existing
  `get_condition_evaluator(kind)` registry, so zero other call sites changed.
- Fixed a real, latent gap in `ExpressionEvaluator`: `ComparisonOperator.IN`/`NOT_IN`/`CONTAINS`
  were declared on the enum but never implemented — an `Expression(operator=IN, ...)` silently
  evaluated as always-`VIOLATED`. Now implemented (skips the numeric cast for these operators),
  closing the "N states → N rules" gap directly on the existing `Expression` kind.
- **HITL suspend now works inside a `Loop`** (D3). `ConductorEngine` previously converted a
  `SuspendRun` raised from a loop's body straight into a `RuntimeError` ("supported only for
  top-level steps"). `_run_loop` now catches a mid-body suspend per-step and can be re-entered
  from that exact point on resume — finishing the interrupted iteration's remaining steps
  without re-running the ones before it, then continuing the loop (convergence/max-iterations)
  and the rest of the pipeline completely normally. `Suspension`/`DurableSuspension` gained
  `loop_id`/`loop_iteration` (both additive, `None` for a top-level suspend — no DB migration,
  `DurableSuspension` round-trips through one JSON column). New `ConductorPipeline.get_loop()`.
  A second suspend inside the same resumed loop, and `resume_durable` through a loop suspend,
  both just work — no special-casing needed beyond the one resume path.
- **Two bug fixes to the condition-evaluator kinds landed alongside D2/D3, reported externally:**
  - `RatioCondition.direction` was typed `ComparisonOperator` (9 values) while
    `RatioEvaluator.evaluate()` only ever handled 2 (`RatioDirection`'s `>=`/`<=`) — a strict
    operator like `<` validated fine at construction and then raised `ValueError` at first
    evaluation. Narrowed the field to `RatioDirection` directly (pydantic now rejects an invalid
    value at construction, naming both legal values), plus a validator explaining *why* only
    `>=`/`<=` are evaluable (margin-to-threshold semantics) and pointing to `Expression` for a
    genuinely strict comparison. Non-breaking — every existing call site already used `>=`/`<=`.
  - `ExpressionEvaluator.evaluate()` unconditionally `float()`-cast the actual value for every
    non-membership operator, so a string-typed field (`citizenship_type == "itin"`) raised
    `ValueError` instead of evaluating. `==`/`!=` now compare raw values (no implicit numeric
    coercion — `"5" == 5` is correctly `VIOLATED`, a deliberate behavior change); ordering
    operators (`>`,`>=`,`<`,`<=`) still cast, but a cast/comparison failure is now
    `INDETERMINATE` rather than a raise, matching `DslEvaluator`'s existing convention for
    unresolvable data.
- Fixed `DefaultPolicyExpert._build_rationale` crashing (`ValueError`) on any non-numeric
  violation value (e.g. `property_state == "AK"`) — found while validating a real policy corpus
  authored against the fixes above. `_build_rationale` unconditionally `.4g`-formatted each
  violation's `actual` value, an assumption the `Expression` float-cast bug had made
  unreachable until now (a non-numeric `actual` used to raise before ever reaching this code).
  Now formats real numbers with `.4g` and everything else via `str()`. 2 new tests.
- `_describe_condition` no longer renders a `matrix` violation as the bare string `"matrix"` —
  it now names the resolved cell and value from `RuleOutcome.inputs` (e.g. `"cltv_pct <= 75
  (cell la_le_1_5m|640|purchase)"` instead of just `"matrix"`), which is load-bearing for any
  pack whose over-conditioning story depends on every violation citing what it actually failed.
  `_condition_label` needed no change — it already rendered correctly for `matrix`
  (`MatrixEvaluator.evidence_contract()` returns non-empty axis fields). 3 new tests.

## [2.4.0] - 2026-08-13

**Unified Assistant Framework ships, plus a full reliability hardening
pass.** Skill catalog, versioned manifest lifecycle with rollback, and
guardrail-gated PassBar promotion (UAF, 13 phases) -- backed by SDK-wide
reliability hardening: unified retry across every LLM provider, approver
identity on suspensions, tool timeout + a non-raising result envelope,
durable queue idempotency, blob offload at conversation/turn-event write
boundaries, an LLM invocation ledger, fan-out parent/ordinal tracing, and
an enforced RAG citation contract. Plus execution-state vs quality-verdict
separation in the eval harness, trace_id continuity on the runs API, a
wasted-probe fix in `DocStore.materialize()`, and financial-spread
vocabulary-gap tracking.

`DocStore.materialize()` skips its own metadata probe when the manifest
store can't possibly use the answer

Reported: with `NullMaterializeManifestStore` configured, `materialize()`
still ran one `get_document_metadata` HTTP call per unique document on
every call -- for zero possible benefit. `NullMaterializeManifestStore`'s
own docstring already promises "no persistence at all... every call
re-downloads everything (no skip-if-unchanged)" -- `manifest.load()`
always returns `{}` and `manifest.save()` discards, so the probe's answer
could never change the always-download outcome. Verified exactly as
reported before touching anything (`store.py:870-895`, `:963-972`).

Considered and rejected a new `skip_unchanged` public parameter (the
reported fix): it would give a caller two independently-settable things
that have to agree (`manifest_store=NullMaterializeManifestStore()` *and*
`skip_unchanged=False`) to get what picking the Null store alone should
already guarantee -- set one without the other and the same silent-waste
bug reappears, just harder to spot. Fixed instead by having the code
honor the promise `NullMaterializeManifestStore` already documents:
`probe_worthwhile = bool(get_metadata) and not
isinstance(manifest, NullMaterializeManifestStore)` gates the probe, the
`_needs_download` fallback, and the trailing manifest-save loop -- no new
public parameter, nothing for a caller to remember to keep in sync.
`sync_collection()` delegates to `materialize()`, so it's covered too;
confirmed it has no duplicate probe logic of its own.

2 new tests (test_fabric_materialize_idempotent.py: the probe is skipped
entirely with the Null store -- `metadata_calls == 0` -- and a regression
guard confirming the default `FileMaterializeManifestStore` still probes
normally).

`FinancialSpread.vocabulary_gaps` -- additive field so a caller aggregating
`structure_statement()` across a spread's statements (jaci's `spreader.py`
is the intended first consumer) has somewhere to carry
`StructuredStatement.vocabulary_gaps` forward without inventing a second
return value or a side channel

`structure_statement()` already tracked unresolved vocabulary keys per
statement (`StructuredStatement.vocabulary_gaps`, existing) but nothing
aggregated them once multiple statements get assembled into one
`FinancialSpread` -- there was no field to put them in. Followed the
exact forward-ref pattern `period_set`/`SpreadLine.semantics` already
established (`spread.py` can't import `structure.py` at runtime without
a cycle -- `structure.py` already sits downstream via `vocabulary.py` ->
`periods.py`), including the same "which module's rebuild call resolves
it" question the `period_set` precedent had already answered: extended
`periods.py`'s existing bottom-of-file `model_rebuild()` block (not a
new one in `structure.py`) to also import `VocabularyGap` and include it
in `_types_namespace` -- a second, separate `force=True` rebuild call in
a different module would have needed to re-supply `PeriodSet` too, or
risk clobbering the already-resolved `period_set` field.

3 new tests (test_finance_periods.py: unaffected-when-absent, additive,
and import-order-independent -- mirroring the three existing `period_set`
tests exactly). Full suite green (2836 passed, 3 skipped).

Eng-queue 0.2 (docs/plans/engineering_queue.md, from the eval-service
convergence analysis): separate execution state from quality verdict in
`CaseResult`/`EvaluationResults`, and fix the one place it was already
live on the wire

`EvaluationHarness._run_single_case`/`_run_cases_parallel` both set
`CaseResult.passed=False` when the conductor raised -- indistinguishable
from a case that ran to completion and genuinely scored below bar.
Traced the actual blast radius before deciding how invasive a fix could
be: `CaseResult.passed` has exactly 3 real consumers in `jazzx_sdk/`
(`harness/runner.py`'s own aggregation, `harness/results.py`'s
truth-mode breakdown, `eval_service_adapters.py`'s wire adapter) --
`pass_bars.py`'s `.passed` usages are on the unrelated `ScorerResult`
type, not `CaseResult`, confirmed by reading the code rather than
assuming from the name.

- `CaseResult.passed` widened from `bool` to `bool | None` --
  `None` now means "execution failed before quality could be evaluated,"
  distinct from `False` ("ran, scored below bar"). Backward compatible:
  every existing caller passing an explicit `bool` is unaffected; `if
  result.passed` / `not result.passed` treat `None` and `False`
  identically (both falsy), so nothing downstream silently breaks on the
  widened type.
- Both exception-handling `CaseResult(...)` construction sites in
  `harness/runner.py` now set `passed=None` instead of `passed=False`.
- `EvaluationResults` gained `errored_cases: int` -- the subset of
  `failed_cases` that never got a quality verdict at all.
  `failed_cases`/`pass_rate` keep their exact existing formulas (`total -
  passed`), so no existing consumer of those two fields sees a behavior
  change; `errored_cases` is purely additive, for a caller that wants to
  tell "the pack scored badly" apart from "the harness broke."
- **The one place this was already live and misrepresenting state on an
  actual wire contract, not just internally:**
  `eval_service_adapters.py::case_result_to_evaluation_v1` mapped
  `passed=False` (execution failure included) straight to
  `QualityVerdict.FAIL` -- reporting an unscored case to eval-service as
  a scored-and-failed one. Fixed to map `passed is None` to
  `QualityVerdict.SKIP`, a value that already existed in
  `jazzx_eval_contracts` for exactly this ("Aggregate quality decision
  for a completed case -- independent of execution/runtime state," per
  `CaseEvaluationV1`'s own docstring) -- the contract already modeled
  this distinction; only the Japes-side adapter hadn't caught up to it.
- Scoped out, not silently dropped: eval-service's wire contract also has
  a full `ExecutionResultV1` (status/output/failure/trace_refs) that
  nothing in `jazzx_sdk/` currently builds at all -- a separate,
  larger adapter-completeness item, not part of this fix.

5 new tests (test_evaluation/test_runner_failures.py +2 new aggregation
tests, 2 existing assertions corrected from `passed is False` to `passed
is None` to match the intended fix; test_scoring_execution_adapters.py
+1). Full suite green (2831 passed, 3 skipped).

trace_id continuity: runs/server.py's `start()` route now defaults
`TurnRun.trace_id` from the same governed trace context the request was
already resolved under

Follow-up to K6's own noted finding: this codebase has (at least) three
independent trace_id holders -- `authority.context.InvocationContext.trace_id`,
OpenTelemetry's `observability.telemetry.get_current_trace_id()`, and
`runs.schema.TurnRun.trace_id` -- and K6 flagged, without resolving, that
they aren't uniformly wired together. Traced each pairwise relationship
through real code paths before deciding what (if anything) needed fixing,
rather than treating "three things share a name" as automatically a bug:

- InvocationContext vs OTel's trace id: **legitimately separate, correctly
  left alone.** Different concepts that happen to share a name -- one
  identifies a distributed-tracing span tree (OTel's own instrumentation,
  typically W3C `traceparent`), the other a governed request's
  authorization scope (`X-Trace-Id`). No code anywhere threads one into
  the other; there's no missing link to add.
- OTel vs `TurnRun.trace_id`: same verdict, different layers (span tree
  vs. durable turn record), never connected, nothing to fix.
- **InvocationContext/governed-http's trace context vs `TurnRun.trace_id`:
  a real, confirmed gap.** `governed_http.py`'s dependency already
  resolves a trace_id per request (`X-Trace-Id`, or a generated one if
  absent) into `_trace_id_var` (`set_governed_context`) -- but
  `runs/server.py`'s `start()` route only ever used
  `StartRunRequest.trace_id`, a separate JSON body field with no
  connection to it. A caller could send `X-Trace-Id: abc` and either omit
  `trace_id` from the body or send a disagreeing `"trace_id": "xyz"`, and
  `TurnRun.trace_id` would end up `None` or `"xyz"` while the same
  request was governed under `"abc"` -- no code anywhere reconciling
  them. Confirmed this is exactly the kind of drift K6's own `trace_id`
  default (from ambient `InvocationContext`) was already at risk of being
  inert against on this exact route, since `runs/server.py` doesn't opt
  into `require_identity=True` either.
- Fixed with the existing precedent already in the same file
  (`governed_http.py`'s own header-vs-explicit backfill at its
  `require_identity` branch): `start()` now defaults
  `trace_id = body.trace_id or get_governed_context()["trace_id"]` --
  an explicit body value still wins (same "explicit beats ambient" rule
  K6 established), but omitting it no longer silently loses the
  trace_id the request was already governed under. Deliberately did NOT
  flip `require_identity=True` on this router -- that additionally
  requires identity headers and would be a real, separate behavior
  change (401 on requests lacking them) for something this fix doesn't
  need.

2 new tests (test_runs_server.py +2: header-default and explicit-wins).
Full suite green (2828 passed, 3 skipped).

Kernel salvage K7 (design note only, no code -- plan explicitly scopes this
"size: large, its own effort, not folded into K1-K6/K8/K10"): parent-to-
sub-agent state inheritance, docs/plans/design_note_k7_parent_child_artifacts.md
(moved 2026-08-25 to docs/plans/Plato/; path above is where it was at this release)

Authorization already cascades parent-to-child (`InvocationContext`/
`PermissionScope` via `descend()`/`narrow()`); state has no counterpart --
every sub-agent `_build_parent_tools`/`_build_composed_skill_tool` builds
starts from nothing but the tool-call argument string, and everything it
derives is discarded when `as_tool` returns. All five points the plan
required settled:

- **Shape**: a new, small `fabric` store (working name `ArtifactStore`),
  NOT an extension of `CaseContext` as first considered -- `CaseContext`
  is Conductor/case-scoped, while the gap is `InteractiveAgent`-scoped (a
  plain chat assistant has no `CaseContext` at all); forcing that
  dependency would be the wrong coupling direction. Composes with
  `CaseContext` for packs that want case-level durability (a checkpoint
  step may promote artifacts into `domain_extensions["artifacts"]`, the
  same operational-to-canonical promotion pattern this file already uses
  elsewhere) rather than being folded into it.
- **Mechanism**: a sibling ambient ContextVar (`set_/get_/reset_
  artifact_scope`), propagated with the identical idiom
  `authority.context`'s own `InvocationContext` trio already uses, at the
  same `_build_parent_tools` call sites -- not a field bolted onto
  `InvocationContext` itself, which would blur its single "authorization
  context" responsibility for no benefit.
- **Visibility = authorization**: reuses `PermissionScope`/`admit_hop`
  directly, generalized via a new `artifact:<key>` selector family --
  found `agents/adjudication/workspace.py::EvidenceWorkspace`'s existing
  `mount:<name>` pattern is *exactly* this one level removed (same
  `narrow()`+`descend()` shape); a new `Skill.reads_artifacts` field
  gates parent-artifact visibility the same way `reads` already gates
  `doc_source:` today.
- **Write-back**: one-directional (child reads parent; parent never reads
  child), matching Kernel's own answer -- the smaller, safer change, and
  avoids inventing a same-key write-conflict policy a two-way answer
  would need.
- **What not to port**: Kernel's OData-on-notepads (odata.py +
  EntityStore.filter already cover it) and its untyped `creator_source`
  enum (this design's `source_type` should reuse `ActorRef`'s existing
  typed vocabulary, the same reuse call K2 already made for
  `DurableSuspension`'s approver fields).
- Explicitly flagged, not glossed over: the plan's own required cross-
  check against `Builder_Pack_Studio_Paradigm_Assessment §6` and the
  `Skill`-composition item in `Japes_Enhancement_Backlog P2` could not be
  done -- neither document exists anywhere in this repo (searched,
  including gitignored docs/plans/). Recorded as a required step before
  anyone acts on this design, not silently skipped.

No code changes; no new tests (design note only, per the plan's own
scoping). Full suite unaffected (2826 passed, 3 skipped, unchanged from
K8).

Kernel salvage K8: enforced source attribution on `RAGStore.search` --
reused the existing `Source` citation type, and fixed a live crash bug
found while verifying the plan's premise

`RAGStore.search()` called `self._kh.search_documents(collection_id=,
query=, limit=, metadata_filters=)` -- kwargs neither the real
`KnowledgeHubClient.search_documents(collection_id, query)` (no
limit/metadata_filters at all -- "controlled by KH's own service
configuration, not by the client," per its own docstring) nor
`MockKnowledgeHubClient`'s (`top_k`/`filters`, different names) accept.
Every real call would `TypeError` before a citation question was ever
reached -- confirmed via `test_integration_followups.py`'s own tracked
mock/real param-drift set (a *different*, already-known issue: mock vs.
real disagreeing with each other, not a caller passing kwargs neither
one has). Zero existing test coverage exercised the real path, only a
guidance-store test double.

- `search()` now calls `search_documents(collection_id=, query=)` only;
  `limit` is enforced client-side by truncating the result list (the
  method's own documented contract, restored rather than silently
  broken); a non-empty `metadata_filters` is logged (not silently
  dropped with zero signal) since KH has no server-side parameter for it.
- Return type changed from `list[dict[str, Any]]` to `list[Source]` --
  reused `agents.interactive.response.Source` (kind/ref/label/uri/
  collection_id/quote/locator), the SDK's one existing citation type,
  rather than inventing a second one. Added `score: float | None` to
  `Source` (the one field K8's "document_id/chunk_id/score" ask needed
  that `Source` didn't already have); `chunk_id`, when present, folds
  into `ref` as `"{document_id}#{chunk_id}"` rather than a new field --
  none of `Source.locator`'s existing `Locator` union members
  (page/cell/section) fit a RAG chunk id, and KH doesn't always return
  one.
- Hard contract: a result with no resolvable document identity
  (`document_id`/`id`/`doc_id`, in that order) raises `KnowledgeFabricError`
  naming the offending payload, rather than silently becoming an uncited
  snippet -- reaching a SAR narrative or adjudication output unattributed
  is worse than not reaching it at all.
- Checked `fabric/docs/store.py` (the plan's other named file): its own
  citation-relevant piece, `MaterializedDoc.entity_id`, is on the
  materialize/download path, which already carries `entity_id` for
  citation -- not the search/retrieval gap K8 is about. No change needed
  there; confirmed, not skipped silently.
- Not done, per the plan's own framing: raising this as an explicit
  Kernel→KF migration exit criterion (an SDK type change can only
  enforce what KH actually returns) is a cross-team conversation, not a
  code change.

7 new tests (test_rag_store.py, new file). Full suite green (2826
passed, 3 skipped).

Kernel salvage K10: `parent_step_id` + concurrency ordinal via the
sanctioned metadata hatch, not a governed `TraceStep` schema change --
also closes K2's deferred step 3

`TraceStep` is `extra="forbid"`, frozen at Schema Spec v1.5, with no
`domain_extensions` (its own docstring calls a per-step extensions dict
"the most common v1.5 failure mode") -- so `parent_step_id`/`order`/
`concurrent_order` can't just be added as fields. The plan's own fallback
was to use `TraceStepContextHelper`'s existing `Trace.metadata` hatch
instead of waiting on a governed spec change, and to bundle this with K2's
deferred step 3 (mirroring an approver onto the suspending step) into one
request rather than two.

- New `TraceStepContextHelper.set_fanout_context(step_id, *,
  parent_step_id, concurrency_ordinal, group_size=None)` -- a typed method
  alongside the existing `set_version_bundle`/`set_ipdv_context` (this is
  an SDK/platform-level concept, not a Domain Pack's, so it gets its own
  method rather than riding the pack-specific `set_domain_context` hatch
  under a fake pack_id).
- `conductor.fanout.fan_out()` gained optional `trace`/`parent_step_id`/
  `step_id_of` params. When all three are given, each item that produces
  a result (via `step_id_of(result)`) records itself as one branch of
  `parent_step_id` automatically -- a fan_out of five branches is
  reconstructible from the persisted trace as one group of five, matching
  the plan's own verify criterion directly (tested against exactly that
  scenario). All three default to `None`: unchanged from before this
  option existed. `step_id_of` returning `None` for a given result (not
  every fan_out item necessarily produces its own `TraceStep`) is skipped,
  not an error.
- K2 step 3, closed as already-satisfied rather than needing new code:
  `ConductorEngine` deliberately has no `CanonicalTrace` of its own --
  its own module docstring says that mapping "stays pack-side" (it keeps
  a generic, schema-light `ExecutedStep` record instead). K2 already put
  `approver_ref`/`authority_basis`/`approved_at` on `DurableSuspension`,
  keyed by the same `step_id` a pack's own trace already uses. A pack
  building its `CanonicalTrace` from `ExecutedStep`/`DurableSuspension`
  already has everything needed to call
  `TraceStepContextHelper.set_domain_context` itself -- no new SDK
  coupling between the engine and `CanonicalTrace` was actually missing;
  wiring one in would have crossed the engine's own stated boundary for
  no gain.
- Not done, left as the plan's own next step: raising `parent_step_id`/
  `order`/`concurrent_order` as an actual governed Schema Spec change
  request bundling K2+K10 (a cross-team conversation, not a code change).

3 new tests (test_fanout.py +3, covering the exact "5 branches, one
group" scenario, the not-all-three-params no-op case, and the
step_id_of-returns-None skip case). Full suite green (2819 passed, 3
skipped).

Kernel salvage K6: LLM invocation ledger -- correlation, status/error/
latency, and payload references, minus a redaction claim that didn't hold
up on inspection

The plan's fourth point said "reuse the existing masking discipline
(MaskingConversationStore/OutputMaskPolicy)... for [payload] redaction."
Read both before wiring anything: `OutputMaskPolicy` truncates large
tool-call outputs at *read* time so an LLM's context window doesn't
balloon -- a context-size control, not a redaction mechanism, and not
applicable to a durable write. It doesn't address the plan's own stated
concern (borrower PII in a persisted payload) at all. Also found a second,
unrelated "trace_id" already in the tree -- OpenTelemetry's
`observability.telemetry.get_current_trace_id()`, a distinct span-level
concept from `authority.context.InvocationContext.trace_id` -- and had to
pick one deliberately rather than silently picking whichever compiled
first.

- `CostRecord`/`CostRecordRow` gained `trace_id` (indexed column -- "a
  turn's LLM calls are retrievable by trace_id"), `step_id`, `status`,
  `error_class`, `latency_ms`, `request_ref`, `response_ref`. All-default
  dataclass fields, so an old row missing them still validates
  (`CostRecord(**row.data)` fills in defaults) -- no migration needed for
  existing archives.
- `CostTracker.record()` defaults `trace_id` from the ambient
  `authority.context.get_invocation_context()` when not passed explicitly
  -- chosen over OTel's `get_current_trace_id()` (a lower-level,
  observability-layer concept, not this governance ledger's) and over
  threading `TurnRun.trace_id` through several call layers (LLMManager has
  no reachable ambient access to it). `step_id` has no ambient source in
  this codebase today, so it's explicit-only.
- `LLMManager.run()` now records status="success"/"failure" with
  latency_ms on *every* call, not just successes -- previously a failed
  call (primary or fallback) left zero cost-ledger trace of the attempt
  ever happening; a new caller-visible behavior once a cost_tracker is
  configured (which is already opt-in), not a silent addition. Gained
  `trace_id`/`step_id` passthrough params.
- Actual redaction: `CostTracker` gained an optional `blob`
  (`fabric.blob.BlobStore`) param -- K5's second real customer.
  `request_payload`/`response_payload`, when given and `blob` is
  configured, are scrubbed with `jazzx_sdk.failures.redact_secrets`
  (credential-shaped text -- Bearer tokens, JWTs, key=value secrets) then
  offloaded as references, never inlined raw. Documented explicitly, not
  glossed over: this is **not** a general PII redactor -- a borrower's
  name/SSN/account number in free-text payload content passes through
  unredacted. No existing primitive in this codebase does that job; it's
  a real, separate, unbuilt gap, not something this pass closes.
- Retention: `DbCostRecordStore.clear(before=...)` already is the
  configurable-retention lever the plan asked for -- confirmed, not
  rebuilt. An ops job schedules it periodically.

14 new tests (test_cost_store.py +9, test_llm_manager_ledger.py new x5).
Full suite green (2816 passed, 3 skipped).

Kernel salvage K5: wire `fabric.blob.offload()`/`materialize()` at the two
real write boundaries -- one of which the plan misnamed

`BlobStore.offload()`/`materialize()` was implemented, documented, and
had zero callers anywhere in jazzx_sdk/ -- confirmed via grep before
touching anything. The plan named its two boundaries as "conversation-
message persistence" and "persisted tool results (K3's envelope is the
natural place)." The first checked out as named. The second didn't:
researched whether `BaseToolRegistry`/`ToolResult` (K3's envelope) is
persisted anywhere, and it isn't -- it's a pure in-memory return value to
the caller within one request, nothing writes it to a store.
`fabric/canonical/trace.py`'s `ToolCall` deliberately stores only
`inputs_digest`/`outputs_digest` (hashes, "never raw data" per its own
field docstring) -- no overflow risk there by design. The real analogue of
"a persisted tool result" is `runs/store_db.py`'s
`TurnRunEventRecord.data.event` -- a journaled stream event, one row per
delta/tool-output/done event, and that file's own `_sanitized_dump`
docstring already said as much ("a run's data column can carry arbitrary
LLM/tool output verbatim").

- `fabric/conversation_store.py::SqlConversationStore` gained an optional
  `blob`/`blob_threshold_bytes` constructor param. `append`/`supersede`
  offload each oversized message/overlay item to a `{"__blob__": ...}`
  pointer after NUL-sanitization (so the offloaded blob content is also
  NUL-free, not just what stays inline); `load`/`load_raw` materialize
  transparently -- a caller cannot tell a value was offloaded, and gets
  the byte-identical value back either way. `blob=None` (default):
  unchanged from before this option existed.
- `runs/store_db.py::DbTurnRunStore` gained the same optional params,
  scoped to `TurnRunEventRecord.data.event` only (not
  `TurnRunRecord.data`'s whole-run snapshot, e.g. `partial_output` -- a
  separate, broader concern left out of this pass, noted here rather than
  silently skipped). `append_event`'s own return value is never a pointer
  (only the row write is offloaded); `events_since` materializes.
- Also fixed, in the two files this touched anyway: a code comment in
  `conversation_store.py` (and its test file) named another repo's PR
  number -- against this session's own standing rule that code
  comments/commit messages never carry cross-repo references (CHANGELOG
  is the one place that's fine). Pre-existing, not introduced this
  session, but directly in the diff hunk being edited.
- Out of scope, noted rather than silently dropped: purging a terminal run
  (`purge_terminal`) does not delete blobs its events offloaded to --
  orphaned-blob GC is a separate concern this pass doesn't address.

10 new tests (test_fabric_conversation.py +6, test_resilient_runs.py +4).
Full suite green (2802 passed, 3 skipped).

Kernel salvage K4: durable idempotency for the queue processor, and a real
gap the plan's own "this is wiring, not building" framing missed

The plan pointed at `automation/idempotency.py`'s `IdempotencyStore`/
`EntityIdempotencyStore` as the existing durable primitive to wire in.
Checked before wiring anything: that store's value type is hard-typed to
`Receipt` -- a governed-write proof-of-side-effect record with fields
(`matrix_cell_ref`, `target_system`, `rollback_ref`, `version_bundle`, ...)
that have no meaning for "has this raw queue message ID already been
processed." Forcing queue_processor.py to construct fake `Receipt`s just to
reuse the storage mechanism would have been exactly the kind of
architecturally-unsound reuse to push back on, not build. `fabric/
idempotency.py` (the plan's other named primitive) turned out to be pure
computation (`content_fingerprint`/`WriteOutcome`), not a store at all --
nothing to wire.

- Genericized `IdempotencyStore` (Protocol), `InProcessIdempotencyStore`,
  and `EntityIdempotencyStore` in automation/idempotency.py over the stored
  value type (`Receipt` stays the default everywhere, so
  GovernedAutomation and every existing caller are byte-identical to
  before). A store now persists any pydantic model, not just Receipt.
- New `automation/idempotency_db.py::DbIdempotencyStore` -- the
  fabric.db-backed (sqlite|postgres, no Knowledge Hub round-trip) sibling
  of EntityIdempotencyStore, completing the InProcess/Entity/Db triad that
  runs.store/conductor.suspension_store already have (runs/store.py's own
  docstring says it mirrors IdempotencyStore's shape -- ironic that the
  original was itself one backend short of its own mirror). Imported
  lazily from its own module, not re-exported by automation's `__init__`,
  matching DbSuspensionStore/DbTurnRunStore's established "SQLAlchemy
  stays opt-in" convention.
- New `queue_processor.py::ProcessedMarker` (just a message_id) -- the
  right-sized value type for this use, not a repurposed Receipt.
  QueueProcessor gained an optional `idempotency_store` param (`None`
  default: unchanged, in-memory-only, the pre-K4 behavior).
  `dequeue_message` checks the in-memory set first (no I/O), then the
  durable store when configured -- catches redelivery after a restart or
  from a second worker process, which the in-memory set alone cannot.
  `delete_message` writes the durable marker after the queue delete
  succeeds; a durable-store write failure is logged loudly but does not
  turn an already-successful delete into a reported failure.
  create_queue_processor() passes the option through.
- Verified against the plan's own acceptance criterion directly: a message
  processed by one QueueProcessor instance, then a second instance (a
  restart, in effect -- fresh in-memory set) receiving the same message
  redelivered, does not reprocess it. A companion test proves the failure
  mode without a durable store configured (redelivery after a restart
  *does* reprocess), so the fix is demonstrated against a real regression,
  not just a happy path.

13 new tests (test_automation_idempotency.py new x8, test_queue_processor.py
+5). Full suite green (2792 passed, 3 skipped).

Kernel salvage K3: per-tool timeout, non-raising ToolResult envelope,
stop_on_fail -- extended to the connectors/ sibling per the plan's own
symmetry check (docs/plans/plan_kernel_salvage_hardening.md)

BaseToolRegistry.execute_request() could hang forever on a slow handler --
call_maybe_async already offloads a blocking sync handler off the event
loop, but neither branch had a bound. And execute_request()'s raise-based
contract meant a caller wanting to inspect a failure without a try/except,
or to try several tools and keep going, had nothing but the always-succeeds
execute() -> Evidence(status=UNAVAILABLE) adapter, which swallows every
failure the same way regardless of severity.

- register_tool() gained optional timeout (seconds, applied via
  call_maybe_async's existing timeout= support -- no new dispatch logic)
  and stop_on_fail (bool) kwargs. Both default to values that leave every
  existing registered tool byte-identical to before (unbounded, swallowed
  into UNAVAILABLE evidence).
- New jazzx_sdk.tools.ToolResult (ok/value/error/error_class/duration_ms)
  and BaseToolRegistry.execute_request_enveloped() -- calls the existing
  execute_request() and catches its exception into a ToolResult rather than
  reimplementing tool lookup/circuit-breaker/timeout logic a second time.
  execute_request()'s raise-based contract is completely untouched;
  existing callers and tests pass unmodified.
- execute()'s except-block now re-raises instead of degrading to
  UNAVAILABLE evidence when the failing tool was registered with
  stop_on_fail=True -- for a tool whose absence should abort the run rather
  than continue silently.
- ToolResult.from_call() is also a standalone adapter over any raise-based
  callable, sync or async -- kernel_client.py's 13+ raise sites are
  deliberately NOT rewritten to this shape (too large/risky a change to an
  already-widely-used client for this pass); a caller that wants an
  enveloped result from one of its methods wraps the call with
  ToolResult.from_call(client.some_method, ...) instead. Documented
  directly in kernel_client.py's module docstring so the omission reads as
  a decision, not a gap.
- tools/platform/workflow.py's search_process_instances() was the one of
  its 4 functions missing the found key the other 3 already carry (a real,
  narrow inconsistency, not a full envelope rewrite of all 4) -- added
  (True on a successful search, even with zero matches; False on error).
- Followed the plan's own "check the sibling family" note into
  connectors/base.py (BaseSourceConnector.fetch(), used by DiscoveryExpert)
  and found the same unbounded-call gap, worse: scan() awaits each source
  sequentially with no bound on either the async or the legacy-sync-callable
  path. Fixed at the real call site rather than adding a fetch_with_timeout
  wrapper nobody would call: DiscoveryExpert.scan() now invokes each source
  via call_maybe_async(..., timeout=config.source_timeout), a new optional
  ScanConfig field (None default: unbounded, unchanged). A timed-out source
  is caught by scan()'s existing per-source except-block and skipped like
  any other source failure -- the rest of the scan continues.

17 new tests (test_base_tool_registry_execute.py +9, test_tool_result.py
new x5, test_tools_workflow.py +1, test_discovery_expert.py +2). Full suite
green (2779 passed, 3 skipped).

Kernel salvage K2 (steps 1-2): approver identity on suspension records

DurableSuspension's resolution field was `resolution: Any` -- no approver
identity, class, timestamp, or authority basis, so "a human approved this
step -- who, when, under what authority" wasn't in the record for a SAR
filing or credit decision, only an untyped blob.

- DurableSuspension (conductor/suspension_store.py) gained approver_ref
  (ActorRef | None), authority_basis (str | None), approved_at
  (datetime | None). Reused trace.py's OverrideEvent vocabulary verbatim,
  not a second one -- ActorRef (already has actor_type="human" as a
  documented valid literal) and authority_basis: str are literally the same
  types, confirmed by a dedicated test comparing the two models' field
  annotations directly, not just similarly-named fields. Deliberately did
  NOT add a separate approver_class field the plan's own wording named --
  ActorRef.actor_type already covers that; a second flat field next to a
  typed object that already carries it would be the exact kind of
  duplicate-vocabulary problem this phase is trying to close. Also
  deliberately did NOT reuse OverrideReasonCode for an approval reason --
  checked its values (compensating_factor, missing_evidence, ...) and
  they're about why someone overrode a system output, not why someone
  approved a step; a category mismatch, not a clean fit like the other two.
- SuspensionStore.mark_resumed (Protocol + InProcessSuspensionStore +
  DbSuspensionStore) gained optional approver_ref/authority_basis kwargs;
  approved_at is set automatically when an approver_ref is supplied.
  ConductorEngine.resume_durable -- the caller-facing entry point a human
  actually calls to resolve a suspended HITL step -- threads them through.
  All additive: a suspension resumed without an approval identity (today's
  every caller) is byte-identical to before, confirmed by a dedicated
  unaffected-default test on both backends.
- Step 3 (mirror the approver onto the TraceStep that suspended) folds into
  the K10 work (next) rather than waiting on a governed schema request --
  research this session found the existing TraceStepContextHelper.
  set_domain_context hatch already covers this without touching TraceStep's
  frozen schema at all, so the "blocked on K10" framing in the original plan
  no longer applies once K10 lands via that path.
- Step 4 (conductor/engine.py's "HITL suspend is supported only for
  top-level steps" -- a Loop can't contain one) is a real, separate
  constraint, recorded here rather than fixed -- out of scope for this pass.

25 new/updated tests (test_conductor_engine.py +2, test_suspension_store.py
+5, run against both InProcessSuspensionStore and the sqlite-backed
DbSuspensionStore where applicable). Full suite green (2761 passed, 3
skipped).

Kernel salvage K1: provider-uniform retry at the Gateway (docs/plans/
plan_kernel_salvage_hardening.md), corrected against a critical read rather
than implemented as literally scoped

The plan's own suggestion ("wire RetryStrategy into LLMManager") turned out
to be wrong -- research before writing any code found FOUR retry
implementations already in the tree, not the two the plan compared:
jazzx_sdk.concurrency.retry_async/backoff_delay (generic, already used in
channels/webhook.py, channels/websocket.py, fabric/docs/store.py -- the
plan didn't know about this one), agents.models.RetryingModel
(Agents-SDK-Model-protocol-specific, hand-rolled for input-mutation and
streaming reasons that are real and don't generalize), providers/openai.py's
own _call_with_retry (fragile str(e).lower() substring matching, a third
formula), and llm/routing.py's RetryConfig/RetryStrategy (dead, zero
callers, same file as the RoutingStrategy already deprecated this session).
Wiring the dead one in, as literally suggested, would have added a FIFTH
implementation instead of consolidating.

- New jazzx_sdk.concurrency.is_transient_error(err) -- the one shared
  retryable-classification (429/5xx/408 status code, or a known transient
  exception class name), extracted from RetryingModel's own (better) private
  _is_retryable rather than openai.py's substring approach. RetryingModel
  now calls this shared predicate instead of its own copy -- confirmed
  behavior-preserving via its full existing test suite re-run unchanged.
- LLMManager gained retry_attempts/retry_base_delay/retry_max_delay
  constructor params (defaults 3/5.0/60.0 -- exactly OpenAI's own prior
  retry defaults, so existing OpenAI-only deployments see no behavior
  change). _execute_with_provider -- the one call site every provider
  (openai/anthropic/gemini/local) already funnels through for both the
  primary and fallback attempt -- now wraps provider.run() in
  concurrency.retry_async(..., retryable=is_transient_error), uniformly.
  Anthropic/Gemini/local, which had zero retry coverage before, now get the
  same coverage OpenAI always had. Composes explicitly with the existing
  HealthMonitor/failover machinery, which was already correct and needed no
  changes: retry_async only retries the *same* provider a few times for a
  blip; run()'s own primary->fallback logic (unchanged) still decides
  whether to jump to a different provider once retries here are exhausted.
- providers/openai.py's _call_with_retry (hand-rolled loop + asyncio.sleep +
  substring-matched retryable check) is gone. Renamed to
  _create_completion, now a single non-retrying call -- kept as a named
  method (not inlined) because it's still the one place a cost-optimized-
  capacity error gets classified into CostOptimizedCapacityExhaustedError
  before it would otherwise reach the new generic retry loop, which must
  never retry it (a capacity signal, not a transient blip). Confirmed
  is_transient_error correctly excludes it (not a matched status code or
  exception class name) without any special-casing needed in the retry
  wrapper itself.
- llm/routing.py's RetryConfig/RetryStrategy formally deprecated (same
  treatment as RoutingStrategy) -- confirmed zero real callers before
  deprecating, not assumed; left in place as exported public API, documented
  as superseded by LLMManager's new retry params +
  concurrency.retry_async/is_transient_error.
- Idempotency was flagged during the same critical read as looking like a
  similar "too many ways to do the same thing" problem
  (automation.idempotency.IdempotencyStore vs fabric.idempotency), but
  checked and confirmed to be two *correctly* separated concerns instead
  (caller-key request-replay vs content-hash write-dedup) -- not touched
  here; the actual fix for that pairing is queue_processor.py adopting the
  first one it currently uses neither of (a separate, still-pending item).

18 new tests (test_llm_retry.py, new file, 9 tests -- including the plan's
own three verify criteria: 429-then-success across all three providers, one
test per provider; retry-exhaustion-triggers-failover with HealthMonitor
assertions; grep-based regression proof that no hand-rolled retry loop
remains; test_concurrency.py gained 9 for is_transient_error). Full suite
green (2754 passed, 3 skipped).

UAF plan Phase 13 (final phase of docs/plans/plan_uaf_phase1_additive.md): generalize the A/B
harness to manifests, wire the >=95% PassBar gate

The last of the 13-phase UAF additive plan. Almost everything the migration
proof needed already existed (EvaluationHarness/EvaluationResults.pass_rate,
golden_cases/ with TruthMode, content-hash case-set lineage, ExperimentRun
keyed on case_set_hash, pass_bars.py's PassBar/run_corpus_eval/
CorpusEvalResult.bars_met -- literally the >=95% mechanism the PRD's success
metric asks for). The one real gap: guidance_ab.py was parameterized on a
guidance asset only (validate_guidance(asset, ...)), not on two specs or
manifests.

- jazzx_sdk/evaluation/guidance_ab.py: extracted the baseline-vs-candidate-
  on-identical-cases core into run_ab_comparison(cases, baseline, candidate,
  *, subject_id, pack_id, ...) -- baseline/candidate are each a plain
  (inputs) -> actual callable (sync or async), so what varies between arms
  (a guidance block, a manifest binding, anything) is entirely the caller's
  concern. validate_guidance is now a thin wrapper closing over the guidance
  block; its own return shape (GuidanceABResult, field name asset_id) is
  byte-identical to before -- confirmed by re-running the full existing
  guidance A/B test suite unchanged (9 tests), the regression proof for the
  extraction per the plan's own verify criterion.
- New compare_manifests(baseline_manifest, candidate_manifest, cases,
  run_turn, *, pack_id, scorer=None) -- "old assistant vs new assistant on
  the golden set" as one function call. run_turn(manifest, inputs) -> actual
  is the caller's own agent-execution call (e.g. via build_from_manifest);
  this harness only compares scored outcomes, it does not build or bind
  agents itself -- kept it a pure comparison harness rather than growing an
  execution engine. Produces two ExperimentRuns sharing one case_set_hash,
  tagged with manifest_assistant_id and content-hash version tags for both
  arms (same content_version formula manifest.store.ManifestRecord uses,
  duplicated rather than importing manifest.store into evaluation/ for two
  lines of hashing).
- Kept the per-case over_fired() flag on both the generalized ABResult and
  the unchanged GuidanceABResult -- per-case regression detection is what
  makes an aggregate pass rate trustworthy, explicitly called out in the
  plan as the part not to lose in the generalization.
- New ABResult.match_rate property (fraction of cases the candidate didn't
  regress) and check_ab_bars(result, bars=None) wiring the PRD's own ">=95%
  match" success metric as an executable PassBar gate
  (DEFAULT_AB_PASS_BAR = PassBar(metric="match_rate", minimum=0.95)) instead
  of leaving it as prose. Shares its min/max comparison logic with
  run_corpus_eval's own per-group bar check via a newly-extracted, now-public
  pass_bars.check_metric_bar(bar, metrics_dict, label=...) -- one bar-check
  implementation, not two; confirmed behavior-preserving via the full
  existing pass_bars test suite (6 tests) re-run unchanged.
- Explicitly not built, per the plan's own instruction: shadow-traffic
  teeing. SHADOW_OBSERVATIONAL exists as a golden-case label only; a real
  tee is a deployment concern with nothing in this repo to build on.

17 new tests (test_ab_comparison.py, new file, 7 tests; test_pass_bars.py
gained 4 for check_metric_bar). Full suite green (2739 passed, 3 skipped).

This closes out plan_uaf_phase1_additive.md's 13 phases (1-13, all shipped
across this and prior sessions). Two smaller adjacent items were reviewed
but deliberately not started this session: Phase 9's common/ submodule diff
is committed locally (branch reserve-reasoning-stream-event, commit
cffefc4) but not pushed upstream -- needs a human to submit it to
JazzX-LLC/common before japes' own submodule pointer can bump; and the
separate plan_kernel_salvage_hardening.md (11 more items, K1-K11) was read
and is a real, well-scoped follow-on, but wasn't authorized for execution
this session and several of its own highest-value items (K7, K9, K10)
explicitly call for a design note or governed schema approval before code.

UAF plan Phase 12: manifest store with versioning and rollback

load_manifest(path, ...) reads from a file; there was no hosted store, no
version history, and no assistant-level rollback -- the only rollback in the
repo before this was fabric.guidance.lifecycle.GuidanceLifecycle.rollback.
Yet "keep the old version warm, have a one-click way back" is a PRD Phase-1
acceptance item, and this is additive/agnostic to the still-open
manifest-vs-profile question (AssistantManifest.profile_ref already carries
the profile binding as a plain field, so no separate wrapper struct was
needed for "the (manifest, profile_ref) pair").

- Extracted load_manifest's inline aggregated-check body into a new,
  standalone jazzx_sdk.manifest.loader.validate_manifest(manifest,
  skill_registry, profile_registry=None) -- load_manifest is now a thin
  read-file + construct + call-this wrapper. Confirmed behavior-preserving:
  the full existing manifest/loader test suite (42 tests) re-run unchanged.
  This is what lets AssistantManifestStore.put run the exact same Phase 1/2
  gate against an already-constructed manifest, with no file round-trip.
- New jazzx_sdk/manifest/store.py: ManifestRecord (immutable
  record_id/assistant_id/version/manifest/supersedes/status/created_at),
  AssistantManifestStore (put/get/history/rollback) +
  InProcessAssistantManifestStore. version is a content hash via the same
  evaluation.prompt_registry.content_version fabric.guidance.GuidanceAsset
  already uses -- reusing the versioning *vocabulary*, deliberately not the
  full TransitionEngine-admitted draft/approved/deployed/deactivated state
  machine, since that machine encodes a human-reviewer approval workflow
  Phase 12 never asked for (put/get/history/rollback only). Two states
  instead: active (current head) / superseded (kept for history, never
  deleted or mutated) -- the right-sized shape for what was actually
  requested, not a copy of GuidanceLifecycle's full surface.
- Every put() always creates a brand-new record and becomes head, demoting
  the prior head to superseded -- matches the plan's own wording literally
  ("put (returns a new immutable version)"), no content-addressed dedup-on-
  put logic (GuidanceStore's own put dedupes identical-version content by
  design; that nuance wasn't asked for here and would have fought against
  rollback needing its own new record even when content is byte-identical
  to an older one). version (the content-hash tag) may legitimately repeat
  across distinct records -- e.g. a rollback to earlier identical content --
  since record_id, not version, is the true per-entry identity.
- rollback(assistant_id, to_version, *, skill_registry, profile_registry=None)
  is literally get(to_version) + put(that content) -- reruns put's full
  validation gate rather than bypassing it, since the registries a
  deployment validates against may have drifted since the content was last
  active; a rollback to now-invalid content fails loud too, not silently.
  Never mutates or deletes the version being rolled back to.
- InProcessAssistantManifestStore.put is asyncio.Lock-serialized so the
  read-current-head-then-append sequence is atomic per call -- verified with
  a real 10-way concurrent-put test (not just asserted): no two records ever
  point at the same supersedes predecessor, exactly one record ends up
  ACTIVE, and none of the 10 concurrent puts is lost.

18 new tests total (9 in test_manifest_store.py, new file; the existing
42-test manifest/loader suite re-run to confirm the validate_manifest
extraction is behavior-preserving). Full suite green (2728 passed, 3
skipped).

UAF plan Phase 10: trace the two decisions that were previously invisible
(router selection, guardrail verdicts)

Two decisions left no record: the router's skill selection
(_select_skills returns a list and records nothing -- runs only on the
agentic paths, so a skill-less assistant never routes at all) and guardrail
verdicts (_run_guardrails sets blocked/block_reason on the response and
last_guardrail_refusal, nothing durable). "Which skill and why" is the
single most-asked debugging question.

- InteractiveAgent gained a new optional tracer= constructor param
  (jazzx_sdk.observability.RunTracer, NoOpTracer default -- same pattern
  DocumentAgent already uses). Deliberately distinct from the existing
  hooks/run_hooks params: those cover the OpenAI Agents SDK's own
  agent/llm/tool span tree via MlflowTraceHooks, which only fires inside the
  SDK's own Runner loop -- routing and guardrails both run as plain Python
  calls outside that loop entirely, so they need RunTracer's separate,
  simpler per-turn span path (observability/run_tracer.py) instead. No
  wiring into MlflowTraceHooks was needed or attempted.
- _select_skills emits one span per turn (f"{spec.name}:route") carrying the
  router name, the candidate set (spec.skills), and the chosen skill(s).
  Confidence is deliberately NOT recorded: the Router protocol's select()
  returns only list[str] | None with no slot for a score
  (_IntentFirstRouter computes one internally but never surfaces it) --
  extending that protocol's return shape is a separate, bigger change this
  phase does not make. The span carries what's actually available rather
  than inventing a field.
- _run_guardrails emits one span per guardrail *evaluated*, not just the one
  that blocks (f"{spec.name}:guardrail:{name}"), carrying guardrail name,
  phase, whether it blocked, and (when the check returned a typed Refusal)
  its reason_class -- so a guardrail verdict is durable even when it
  *passed*, not just when it refused.
- New jazzx_sdk/agents/interactive/tracing.py: interactive_name_patterns(),
  mirroring agents/adjudication/tracing.py's adjudication_name_patterns()
  exactly (same precedent: mlflow_bridge's span_type-keyed mode_map can't
  distinguish two spans of the same generic kind). route spans map to
  CONDUCTOR (EXECUTE-layer orchestration/dispatch), guardrail spans to
  SENTINEL (TRUST-layer monitoring). No change needed to mlflow_bridge.py
  itself -- name_patterns was already the extensibility seam.
- New jazzx_sdk/observability/trace_routes.py: trace_router(canonical_objects=...)
  -- a read-only GET /traces/{trace_id} route on a GovernedRouter, mirroring
  runs/server.py's shape exactly. Lookup only, deliberately -- a write path
  would prejudge the still-open trace-format-of-record question. 404s
  cleanly on a miss. Not imported from observability/__init__.py (same
  eager-import discipline as runs/server.py/trace_source -- fastapi and
  fabric.canonical stay off the `import jazzx_sdk` path); import by full
  path.
- TraceStep (fabric/canonical/trace.py) intentionally untouched -- frozen at
  Schema Spec v1.5, extra="forbid", no domain_extensions by design. Nothing
  in this phase needed to touch it; all three deliverables land through the
  existing span/name-pattern/lookup seams.

13 new tests (test_interactive_tracing.py, test_interactive_agent_tracing.py,
test_trace_routes.py -- new files). Full suite green (2719 passed, 3
skipped).

UAF plan Phase 9: reserve the reasoning stream event (prep only, needs a
human to submit upstream)

StreamEventType (common/core/streaming/models.py) has eight members and no
reasoning/thinking event; tool streaming is already fully built on the japes
side (stream_hooks.py, streaming/publisher.py, sse_reader.py, journal
resume), so only the event type itself was missing from the shared
vocabulary. The catch, stated in the plan itself: StreamEventType lives in
common/, a git submodule pointing at a separate JazzX-LLC/common repo with
other consumers -- adding a member there is a shared-package change, not a
japes-local one, and needs upstream coordination this session can't do
alone.

- Added StreamEventType.reasoning + a new ReasoningEvent class (same shape as
  LLMChunkEvent -- a text delta) to common/core/streaming/models.py, exported
  from common/core/streaming/__init__.py, added to the StreamEventModel
  discriminated union. 4 new tests in common/tests/streaming/test_models.py
  (round-trip, dict-resolution, and a regression test proving the existing
  eight members are unaffected). Nothing in jazzx_sdk/ emits it yet, matching
  the plan's own "reserve API space" framing -- deliberately not wired into
  japes' own ToolStreamHooks/InteractiveStreamEvent in this pass.
- **Committed locally within the common/ submodule's own git history only**,
  on a new branch (reserve-reasoning-stream-event, commit cffefc4) --
  NOT pushed to JazzX-LLC/common, and japes' own submodule pointer is
  deliberately NOT bumped (`git status` at the japes root shows common as
  locally modified/dirty, nothing staged or committed here). This diff needs
  a human to review, open against JazzX-LLC/common, and land there before
  japes' submodule pin can be bumped to reference a real, shared commit.
- Symmetry check run before finishing: no other file in jazzx_sdk/ depends
  on StreamEventType/StreamEventModel beyond streaming/publisher.py and
  streaming/__init__.py (both re-export only, no behavior depends on the
  member count), so this addition is safe against the rest of the japes tree
  as-is, independent of whether/when it lands upstream.

Full japes suite + the 4 new common/ tests together: 2725 passed, 3 skipped.

UAF plan Phase 8: session lifecycle (SessionStore + Reaper-shaped sweeper)

Conversation *content* handling was already ~80% there (ConversationStore
variants, durable SqlConversationStore, CompactionPolicy, resumable durable
SSE with cooperative stop). Missing: the session *record* -- session_id is
caller-supplied with no created_at/last_active_at, no TTL, no expiry, no
resume signal.

- New jazzx_sdk/agents/interactive/session.py: SessionRecord
  (session_id/conversation_id/created_at/last_active_at/status), SessionStore
  Protocol (create/touch/get/expire/reap_stale) + InProcessSessionStore, and
  SessionReaper -- deliberately copying runs/dispatcher.py's Reaper shape
  exactly (sweep()/run_forever() over a store's own reap_stale) rather than
  inventing a second sweeper design. Deliberately a separate store from
  ConversationStore, not folded into it -- a session is lifecycle metadata, a
  conversation is content; SqlConversationStore has no timestamps of its own
  on purpose, this is where they belong.
- expire() is a state transition (status -> EXPIRED), never a delete or
  mutation of conversation_id/created_at -- the audit trail survives. touch()
  never revives an already-expired session (returns None), so a caller's own
  get()/touch() result is the resume-vs-fresh-conversation signal ("Resume =
  get on a live session returning its conversation id").
- reap_stale fencing mirrors InProcessTurnRunStore's own reap_stale exactly:
  each session's staleness is re-checked fresh, immediately before its own
  write, not against a snapshot captured at sweep-loop start -- guards the
  same production race (a concurrent touch() landing during an earlier
  iteration's yield point must not be reaped off stale data). Regression test
  for this race included, mirroring the existing TurnRunStore one.
- No new caller wires this in yet -- SessionStore/SessionReaper are additive,
  standalone, opt-in. "Default configuration changes no existing test" holds
  trivially: nothing existing constructs one. Only an in-process backend
  ships (matching TurnRunStore's own InProcess/Db split) -- a fabric.db-backed
  durable variant is a documented, not-yet-built extension point, since
  nothing in this phase's verify criteria requires durability.

14 new tests (test_session_store.py, new file). Full suite green (2709
passed, 3 skipped).

UAF plan Phase 7 (conservative scope): de-hardcode the agentic path's model
literal, deprecate the unused RoutingStrategy

Scoped deliberately narrower than the plan's literal ask, per an explicit
decision made before starting (docs/plans/plan_uaf_phase1_additive.md's own
Phase 7 asks for the agentic path's model *calls* to route through LLMManager
for CostTracker/failover coverage). Investigated first: today's agentic path
builds a real OpenAI Agents SDK Agent via OpenAIProvider's own bare
AsyncOpenAI client, completely bypassing LLMManager -- and there is no
adapter anywhere between LLMManager's call shape (prompt/system_prompt/
messages -> one completion) and the Agents SDK's Model protocol (a
tool-calling loop, streaming, structured output natively integrated with
Runner). Building one is a real, materially larger change to every
skill-based turn's live execution path for every consumer. Given this was
going to land unsupervised, went conservative: de-hardcode the literal only,
document the gap explicitly, leave the real Model-adapter build as flagged
future work rather than rushing it through.

- New jazzx_sdk.agents.models.resolve_agent_model_name(spec_model, *,
  gateway=None, task_type="agentic", default="gpt-5.2") -> str. Replaces the
  three independent `self.spec.model or "gpt-5.2"` literals in
  agents/interactive/agent.py (parent agent build, sub-agent skill build, and
  ResponsesCompaction's model). Precedence: spec_model always wins (unchanged
  from before); else, when a gateway (LLMManager) is wired and its
  task_routing names "openai" as the primary provider for task_type, that
  provider's PROVIDER_DEFAULT_MODEL entry; else the same "gpt-5.2" literal as
  before. With no spec.model and no gateway wired (today's every existing
  caller), byte-identical to the code it replaces -- confirmed via the full
  existing interactive-agent suite re-run unchanged, not just asserted.
- New public properties closing the read-access gap this needed:
  LLMManager.task_routing (read-only copy of the configured routing table,
  mirroring the existing health_monitor/cost_tracker property convention) and
  AgentExecutionService.llm_manager (mirrors .openai/.anthropic). Both
  additive, zero behavior change for any existing caller.
- llm/routing.py's RoutingStrategy formally deprecated in favor of
  LLMManager.task_routing, resolving a reconciliation the module's own
  docstring had left open ("settle which is the intended surface before a
  client builds against this module"). Confirmed zero real callers of
  RoutingStrategy anywhere in jazzx_sdk before deprecating, not assumed --
  left in place (exported public API a downstream consumer may already
  import) but documented as superseded, so no third routing model gets
  written against it later. RetryConfig/RetryStrategy in the same file are a
  separate, unrelated concern and not touched by this note.
- gpt-5.2 literal confirmed zero remaining occurrences in the three files
  Phase 7 named (agent.py/service.py/factory.py) -- a regression test greps
  for it. Deliberately NOT extended repo-wide: ReasoningAgent, the
  AdjudicationAgent chassis, EvolveMode's evaluator, and
  OpenAIProvider.build_agent's own default parameter each carry their own
  independent "gpt-5.2" default and are outside Phase 7's named scope --
  left untouched rather than folding an unrelated, unreviewed change into
  this pass.

14 new tests (test_agent_models.py, tests/agents/test_service.py,
test_llm_provider_routing.py, test_interactive_agent.py -- including one
exercising a real LLMManager wired end-to-end through InteractiveAgent and
asserting the resolved model reaches the actual build_agent call). Full
suite green (2695 passed, 3 skipped).

UAF plan Phase 1: manifest name/description, is_conversational, persona
cross-validation, softened mandatory-skills gate

The last of the manifest-track UAF phases (docs/plans/plan_uaf_phase1_additive.md),
done out of the plan's own suggested order since Phase 4 (already shipped,
decoupled) and Phase 12 (next) both depend on it.

- AssistantManifest gained two required fields: name (human display; assistant_id
  stays the machine identifier) and description (the prompt that drives routing,
  out-of-scope handling, and agents.interactive.recommend's skill recommender --
  both required, no sensible default for either). Breaking for any existing
  AssistantManifest(...) construction that omits them -- every test fixture in
  this repo constructing one (4 test files, 1 YAML fixture) updated.
- New AssistantManifest.is_conversational property, delegating to a single
  CONVERSATIONAL_SURFACES constant. Moved from spec_binding.py (private
  _CONVERSATIONAL_SURFACES) to manifest/surface_types.py to avoid a manifest ->
  spec_binding import cycle (spec_binding already imports AssistantManifest at
  module level) -- spec_binding._apply_surface_defaults now imports the same
  public constant rather than defining its own, so there remains exactly one
  definition of "conversational," not two.
- load_manifest cross-validates primary_persona against the resolved profile's
  persona (only when profile_registry is given): primary_persona set but the
  profile has none now raises, naming both. Previously a dead field -- nothing
  in the SDK read it.
- Mandatory-skills gate, deliberately NOT the plan's literal "allowed_skills must
  always be non-empty" -- InteractiveAgentSpec's own docstring designs for a
  skills-less, single-shot grounded-Q&A shape, and the literal gate would have
  broken that pattern for every existing zero-skill manifest. Softened to two
  narrower, concretely-justified signals instead: an ORCHESTRATOR archetype
  (whose entire purpose is directing other skills/sub-agents) declaring no
  allowed_skills at all (checkable without a profile_registry), and, when one is
  given, a resolved profile that itself declares spec.skills but ends up with
  none of them allowed by the manifest -- a real mismatch, not a legitimate
  skills-less design. A SPECIALIST/etc. manifest with allowed_skills=[] and a
  skills-less profile is still accepted.

33 new tests (test_assistant_primitives.py); ~20 existing manifest-construction
call sites across 4 test files + 1 YAML fixture updated for the two new
required fields. Full suite green (2681 passed, 3 skipped).

UAF plan Phase 3 + Phase 4: skill record metadata, build-time skill recommender

Two more priority-sequenced phases from the 13-phase UAF additive plan
(docs/plans/plan_uaf_phase1_additive.md). Note on sequencing: Phase 4's own
spec lists it as depending on Phase 1 (manifest name/description) as well as
Phase 3; Phase 1 hasn't been built yet (an earlier session prioritized 2 and
11 first). recommend_skills() below takes description/persona as plain string
arguments rather than pulling them from AssistantManifest, so the capability
ships now, decoupled from Phase 1 -- wiring manifest.description through is a
trivial follow-up once Phase 1 lands, not a redesign.

Phase 3 -- Skill (spec.py) gained five metadata fields, declared only, none of
them touching execution: version (a stable, comparable version identifier;
"new versions don't break old ones" was unrepresentable without it),
visibility (roles that may see/attach the skill; None = visible wherever the
registry is visible, today's behavior for every existing registration),
invokes (explicit statement of what's behind the skill -- previously only
implied by which of tools/spec_ref/mcp_servers was populated), and
inputs/outputs (JSON Schema, optional and unvalidated at runtime in this
phase -- exist so a catalog/docs generator has a source; nothing reads them
yet). _build_parent_tools (agent.py) is unchanged -- confirmed via `git diff
--stat`, zero lines touched, per the plan's own acceptance criterion.

- SkillRegistry.names() gained an optional roles= kwarg (default None -> no
  filtering, byte-identical to today) implementing the visibility filter;
  catalog_text() appends "(vX, invokes=Y)" only when a skill actually
  declares those fields, so a skill declaring neither renders byte-identical
  to before this phase (confirmed against the existing exact-string test).
- SkillInventory/build_inventory surface all five new fields for a
  sub_agent-kind skill; a bare-name tool-kind skill has no Skill object to
  read them from, so they stay None there, matching existing behavior for
  that branch.
- New skill asset channel on packs: PackManifestLoader.skills() (inline list
  or a relative-path YAML file, mirroring evidence_types() exactly -- same
  convention, not a second one), FRAGMENT_KINDS gained "skills", and
  merged_assets() now supports kind="skills" (id field "name") through the
  same fragment-scoped, provenance-stamped, collision-fail-loud merge every
  other kind already uses. New Pack.skills property mirrors Pack.evidence_types.
  Deliberately distinct from an agent's own skill_defs (Pack.agent's
  InteractiveAgentSpec.from_dir already loads those) -- these are pack-level
  importable declarations another pack can pull in via depends_on/fragments,
  not one agent profile's resolved catalog.

36 new tests (test_interactive_agent.py, test_skill_registry.py,
test_pack_composition.py, test_pack_manifest_loader.py); one existing
exact-set test (test_fragment_kinds_constant) updated for the new fragment
kind.

Phase 4 -- new jazzx_sdk.agents.interactive.recommend module:
recommend_skills(llm, *, description, persona, registry, allowed=None,
roles=None, model=None, prompt=None) -> RecommendationResult. Same shape as
router.py's _IntentFirstRouter (one structured LLM call over
SkillRegistry.catalog_text) with a different input (description/persona
instead of a per-turn query) and a different lifecycle (build-time, not the
turn's hot path). Deliberately not a Router -- sharing that protocol would
put a build-time concern in the turn loop, which router.py's own docstring
already argues against; shares catalog_text's rendering and the
structured_call pattern instead, not the protocol.

- RecommendationResult carries both `ranked` (score + one-line rationale per
  skill, from the LLM) and the full `catalog` (every name the caller's
  roles/allowed filters admit) -- "View all skills" is always available,
  never a filtered-down set standing in for the catalog.
- roles= threads straight into SkillRegistry.names()/catalog_text() (Phase
  3's visibility filter) before the LLM ever sees the catalog, so a
  role-invisible skill is never in the prompt; the ranked list is additionally
  filtered against the same role-filtered name set as a second guard against
  a hallucinated skill_name the LLM might still produce. An empty
  (post-filter) catalog short-circuits to an empty result with no LLM call at
  all.

6 new tests (test_skill_recommender.py, new file), including rank order via
ScriptedLLM, a role-invisible skill never appearing in either the ranked or
full list, and the full catalog always being returned alongside the ranking.

62 new/updated tests total across both phases. Full suite green (2673 passed,
3 skipped).

UAF plan Phase 5 + Phase 6: always-on safety-floor guardrail, configurable
out-of-scope handling

Two more priority-sequenced phases from the 13-phase UAF additive plan
(docs/plans/plan_uaf_phase1_additive.md).

Phase 5 -- an assistant could previously deploy with no guardrail but the
keyword-matched manifest scope check (spec.guardrails defaulted empty; bind_spec
force-injected only the scope guardrail's name). New always-on platform-tier
safety floor closes that:

- jazzx_sdk.agents.interactive.safety: new SAFETY_FLOOR_GUARDRAIL_NAME
  ("platform_safety_floor") and build_safety_floor_guardrail(*, check=None) --
  a real, enforced Guardrail, deliberately distinct from the module's existing
  SAFETY_INSTRUCTIONS/with_safety (prompt text, never enforced; the module
  docstring now states the distinction explicitly so the two are never
  conflated). check= is the seam for an external moderation/red-teaming
  gateway (same GuardrailCheck contract registry.llm_guardrail already
  demonstrates); with none supplied, the check never blocks -- the floor is a
  structural guarantee only, since no gateway ships in this repo. Wiring a
  real one in later is a one-line change to this call's check=, not new
  framework plumbing -- the gateway integration itself stays a separate,
  future deliverable, not built here.
- manifest.spec_binding.bind_spec: force-prepends SAFETY_FLOOR_GUARDRAIL_NAME
  onto both guardrails["input"] and ["output"] (ahead of the scope guardrail),
  via a new shared _prepend_guardrail_if_missing helper (also now used for the
  scope guardrail's own prepend, replacing near-duplicate inline logic). No
  AssistantManifest field opts out -- the absence of one is the guarantee.
- manifest.spec_binding.build_from_manifest: new _ensure_safety_floor_registered
  (mirrors the existing _ensure_scope_guardrail_registered's shape) registers
  the built Guardrail into the catalog at tier 1 -- registry._TieredRegistry
  already refuses a less-trusted tier registering over a more-trusted name
  unless allow_override=True is passed explicitly; this is the first caller
  that actually uses tier=1.
- The one behavior change in this plan, as flagged by the plan itself: every
  existing manifest-bound consumer now gains this guardrail (structurally
  present, never blocks without a configured gateway). Two existing tests
  asserting exact guardrails["input"] contents updated for the new
  floor-first ordering.

Phase 6 -- the shipped scope-guardrail default was weaker than assumed:
case-insensitive substring matching against out_of_scope_action_classes that
defaults to allow when nothing matches, model= accepted and silently ignored,
decline text hardcoded. "A mortgage assistant never answers what's the
weather" did not hold.

- jazzx_sdk.agents.interactive.scope.build_scope_guardrail: new decline_message/
  redirect_target/llm params. decline_message, when set, replaces the built-in
  decline text verbatim on both the keyword-match and LLM paths; redirect_target
  replaces the Refusal.remediation field's built-in text. llm (a real
  LLMManager or a ScriptedLLM) routes the check entirely through
  registry.scope_guardrail (the existing LLM-backed, description-driven
  variant, reasoning about in_scope as the allowed-topic list) instead of the
  default keyword match, with model then selecting that call's model. Passing
  model without llm now raises at build time -- silently ignoring an unusable
  model (the old behavior) was worse than failing loud. All four params
  default to None/absent, reproducing today's exact text and keyword-match
  behavior unchanged. The module docstring now states the fail-open-to-allow
  default explicitly as a known, deliberate weakness rather than leaving it
  implicit -- flipping to deny-by-default would be a real behavior change for
  every existing consumer and isn't done here.
- jazzx_sdk.manifest.assistant_manifest.AssistantManifest: three new optional
  fields (all None by default, preserving today's behavior exactly) --
  out_of_scope_decline_message, out_of_scope_redirect,
  out_of_scope_check_model. manifest.spec_binding._ensure_scope_guardrail_registered
  forwards all three into build_scope_guardrail, plus a new llm= param peeked
  (not popped) from build_from_manifest's **extra["llm_manager"] the same way
  store= already is -- so a manifest declaring out_of_scope_check_model but
  built without an llm_manager= raises at build time rather than silently
  falling back to keyword matching.

26 new tests (test_safety_floor.py new; test_interactive_scope.py grew from 5
to 17). Full suite green (2651 passed, 3 skipped).

UAF plan Phase 2 + Phase 11: manifest silent-degradation, InvocationContext at
every service entry point

Two priority-sequenced phases from the 13-phase UAF additive plan
(docs/plans/plan_uaf_phase1_additive.md), chosen because both are live
correctness/security bugs rather than feature gaps.

Phase 2 -- jazzx_sdk.manifest.loader.resolve_pack no longer degrades silently.
Previously: a missing pack_id logged a warning and returned None (every caller
had to remember to null-check); an out-of-range pack_version_range logged a
warning and returned the pack anyway; an unparseable pack_version_range (e.g. a
typo) fell all the way through the except InvalidSpecifier branch and returned
the pack with the version constraint never evaluated at all -- the sharpest of
the three, since nothing about it looked like a failure. All three now raise
ValueError naming the assistant, pack, and (where relevant) the offending
range -- a manifest bound to a pack is a deploy-time gate, not a lookup a
caller null-checks. 3 tests rewritten from *_returns_none to *_raises, 1 new
test for the invalid-specifier path (17 passing in
test_assistant_primitives.py; 41 across the broader manifest suite).

Phase 11 -- an unauthenticated HTTP call path previously reached
authority.context.admit_hop's fail-open branch (no ambient InvocationContext
-> admitted) with nothing at any entry point requiring one be established
first. The authorization primitives themselves (PermissionScope.admits/narrow,
InvocationContext, check_hop, admit_hop) were already correct and already used
at real call sites (_check_turn_entry, _build_parent_tools,
_build_composed_skill_tool) -- the gap was purely that no entry point ever
built the context admit_hop/check_hop check against.

- jazzx_sdk.handlers: extracted _decode_security_context_value(sc) as a pure
  helper from _decoded_security_context's decode loop (zero behavior change --
  confirmed via the existing 31-test identity/RBAC suite re-run unchanged), and
  added identity_from_headers(headers) -- the same
  x-security-context-first/x-user-*-fallback resolution order as
  get_current_user_id/email/name, parameterized for an explicit header mapping
  (a live request's own headers) instead of the ambient ContextVar path those
  three read. The three existing accessors are deliberately left as-is, not
  unified onto this -- their ambient-priority chain (live request > manual
  security_context > restored propagated headers) differs meaningfully from a
  one-shot explicit-mapping resolution, and unifying them was judged too risky
  given how widely they're relied on for RBAC.
- jazzx_sdk.authority.context: PermissionScope.unrestricted() classmethod
  (resource_selectors=[""] -- "" is a prefix of every string, so it admits
  unconditionally via the existing _matches_any/startswith("") mechanics; no
  new matching logic invented). New build_invocation_context_from_headers(
  headers, *, actor_class="human", permission_scope=None) -- the shared
  entry-point constructor: resolves identity via handlers.identity_from_headers,
  returns None when nothing resolves (caller decides what that means), defaults
  permission_scope to unrestricted() since an authenticating entry point has no
  selector grammar of its own to narrow by yet.
- jazzx_sdk.server.app.ServerSettings: new require_identity: bool = False.
  Opt-in, not on by default -- jaci's own japesClient.ts sends identity headers
  as a caller-supplied option, not unconditionally on every call today, and the
  same is true for other consumers as far as could be confirmed from this repo
  alone; flipping the flag on is a per-deployment decision once that
  deployment's callers are confirmed to send identity. When True, new
  middleware on create_app() rejects any request other than /health with 401 if
  it carries no identity headers, and establishes an InvocationContext for the
  request's duration (set/cleared around call_next, mirroring
  ResilientRunner's existing set/get/clear pattern) when it does. Also
  registered common.middleware.context_headers.HeaderMiddleware in create_app
  unconditionally (non-rejecting -- it only populates a ContextVar) -- a
  pre-existing comment in the /invoke handler claimed inbound identity headers
  "are already captured by common's HeaderMiddleware"; grepped the whole repo
  and confirmed that middleware was never actually registered anywhere, so
  handlers._default_request_headers's primary source (and therefore RBAC
  forwarding to Knowledge Hub) was silently getting nothing from it for any app
  built via create_app alone. Fixed as a safe, additive, in-scope correction
  rather than deferred, since it only closes a gap the existing comment already
  assumed was closed.
- jazzx_sdk.server.governed_http.GovernedRouter: matching require_identity:
  bool = False constructor param, same opt-in default, enforced inside the
  existing governed() dependency's try/finally alongside
  set_governed_context/clear_governed_context -- covers runs/server.py's
  /runs routes the same way ServerSettings.require_identity covers the plain
  /invoke path.
- admit_hop's fail-open semantics when no context is ambient at all are
  deliberately unchanged -- it's the documented opt-in wrapper in-process
  library callers depend on; fixing the entry point removes the exposure
  without breaking them, per the plan's own explicit instruction.

19 new/updated tests across test_server.py (TestRequireIdentity),
test_governed_http.py, test_invocation_context.py
(TestBuildInvocationContextFromHeaders + unrestricted()), and
test_identity_propagation.py (identity_from_headers). Full suite green (2631
passed, 3 skipped).

DocumentAgent: downloadable/blob sources, one-call front door

Closed three source-description gaps in DocumentAgent's existing conductor-routed
pipeline (DocTurn/run_document), after confirming how much of the "fat agent" shape
(spec + turn, mirroring InteractiveAgentSpec + respond()) it already had -- most of
it: DocumentAgentSpec (policy: taxonomy, confidence floors, template mapping,
YAML-loadable), and DocTurn already unified a folder/KH-collection/standalone-zip
into one auto-routed "collection" branch over process_dir's incremental,
manifest-cached, concurrent-fan-out machinery. Template-if-available routing
(route_template) was also already correct -- confirmed, not changed.

- jazzx_sdk.tools.documents.local: new download_to_file/download_files -- raw-bytes
  downloads sharing read_from_url's SSRF guard. Extracted the shared, per-redirect-
  hop-validated GET into a private _safe_fetch both functions build on (read_from_url
  itself unchanged in behavior; its own SSRF test suite re-run unchanged as
  confirmation). Concurrent downloads use the same jazzx_sdk.conductor.fan_out
  primitive process_package's segment fan-out already uses; a failing URL is skipped
  (degrade=True) rather than sinking the batch. Filenames: the response's
  Content-Disposition filename if present, else the URL path's basename --
  Path(...).name strips any embedded path components first, so a malicious
  filename="../../etc/passwd" header can't escape the destination directory.
  Collisions get a short URL-hash suffix. Re-exported from jazzx_sdk.tools.
- DocumentAgent.materialize_blob_to(pointer, dest, *, filename): durable
  blob-to-file materialization -- the counterpart to the existing process_blob,
  which only ever materializes to a temp dir for the duration of one process() call.
- DocTurn gained urls: list[str] and blob_pointers: dict[str, str] (pointer ->
  filename; required per-pointer since a blob key carries no extension and
  convert_document routes on it). Both auto-route to the existing "collection"
  branch in detect_step; process_collection_step materializes them into a scratch
  dir (fan_out-bounded by turn.concurrency) before delegating to the unchanged
  process_dir. A downloaded .zip is unpacked by process_dir's existing
  include_zips handling for free -- no new zip logic needed.
- DocumentAgent.run(turn: DocTurn, *, tracer=None, on_step=None, detect=None,
  **pipeline_kwargs): one-call front door wrapping build_document_pipeline +
  build_document_components + run_document, mirroring InteractiveAgent.respond()'s
  ergonomics (today's alternative is three separate calls). Locally imports
  pipeline.py inside the method to avoid a circular top-level import (pipeline.py
  already imports unpack_zip from agent.py).

Designed in plan mode first given the multi-file scope; plan preserved at
~/.claude/plans/atomic-doodling-sun.md. 25 new tests (test_download_files.py new;
additions to test_document_pipeline.py, test_document_agent.py). Full suite green
(2612 passed, 3 skipped).

run_with_recovery -- schema-validation/truncated-output/API-status retry for a
caller that builds its own Agent

InteractiveAgent had none of run_agent's recoverable-failure handling
(ModelBehaviorError / IncompleteOutputError / APIStatusError) because it builds its
own Agent (skills-as-sub-agents) and calls Runner.run() directly instead of going
through run_agent, which owns Agent construction itself. Confirmed by reading the
code, not assumed: InteractiveAgent._respond_agentic called Runner.run() with zero
exception handling for any of the three; a schema-validation failure propagated
straight up uncaught.

- New jazzx_sdk.agents.run_kit.run_with_recovery(run_once, *, feedback, name,
  max_retries=3, on_retry=None): the same retry mechanism as run_agent
  (ModelBehaviorError feedback-and-retry, IncompleteOutputError feedback-and-retry,
  APIStatusError backoff) over a caller-supplied run_once()/feedback() instead of
  owning Agent construction. Deliberately does not retry MaxTurnsExceeded --
  recovering from that needs rebuilding the Agent with different tools/query, which
  isn't this primitive's job when the caller already owns construction; stays
  run_agent-only.
- run_agent's own two feedback-message bodies (schema-validation / truncated-output)
  extracted into shared _model_behavior_feedback/_incomplete_output_feedback helpers
  so wording can't drift between the two entry points. run_agent's control flow and
  retry-counting semantics are otherwise untouched -- its existing 33 tests re-run
  unchanged, confirming the refactor is behavior-neutral.
- Wired into InteractiveAgent._respond_agentic: feedback appends the retry message to
  the active session when one exists, or to the input list directly when the call is
  stateless (no conversation). Composes with the existing context-window-overflow
  fallback as the inner retry (schema/truncation/status) under the outer one
  (compaction + one retry). Not wired into _stream_agentic, which already documents
  why: can't retry after partial output has started streaming to the caller.
- Checked DocumentAgent: needs no change. Its classify/extract already route through
  AgentExecutionService -> OpenAIProvider's no-tools/single-message fast path ->
  run_agent, so they already get this retry. run_with_recovery exists for whenever
  it (or a future agent) builds its own Agent directly the way InteractiveAgent does.

jazzx_sdk.__all__ (via jazzx_sdk.agents) gained run_with_recovery. 8 new tests in
test_agents_run_kit.py, 2 in test_interactive_agent.py (stateless + active-session
retry proven through respond() itself, not just the primitive in isolation). Full
suite green (2597 passed, 3 skipped).

Sanitize NUL bytes at every JSON-column SQL write boundary; add call_maybe_async

fabric.entities already sanitized (strip_nulls) at its write boundary; audited every
other mapped_column(JSON) store in jazzx_sdk and found six more that didn't --
SqlConversationStore, DbFeedbackStore, DbPromptRegistry (sanitizes before hashing so
version stays consistent with what's stored), DbSuspensionStore, DbTurnRunStore (seven
internal call sites collapsed onto one _sanitized_dump helper), DbAgentDefinitionStore,
and DbCostRecordStore's one open metadata field. All seven now strip NUL bytes (real or
escaped-literal-text) before writing -- Postgres text/jsonb reject the raw byte outright.

New jazzx_sdk.concurrency.call_maybe_async(fn, *args, timeout=None) decides sync-vs-async
before invoking a caller-pluggable callable (never calls it eagerly), offloads a sync
callable off the event loop, and uniformly times out either branch. Replaced twelve
hand-rolled isawaitable/iscoroutinefunction dispatch sites with it across tool/scorer/
document/interactive-agent/evaluation call sites, including conductor/engine.py's step/
guard/loop-convergence dispatch -- the core path every pack conductor run goes through,
where the old eager-call shape let a blocking sync component or observer stall the loop
before on_step_timeout ever got a chance to bound it. Removed the now-dead _maybe_await
helper and simplified _emit_step_event's timeout branching in the same pass.

## [2.4.1] - 2026-08-13

**Mode chassis plan complete (all 7 phases), a new `jazzx_sdk.pipelines` home for
japes' "reference pipeline" family, and two portable cross-instance
primitives.** `Curator.synthesize_bucket` migrated onto `ReasoningAgent` --
the last cognitive mode still bypassing it -- alongside `TurnRunStore.
latest_run()` (reconnecting-caller state) and a generic bundle/publish
primitive for cross-instance promotion (`jazzx_sdk.manifest`). Plus a
symmetry pass triggered by consolidating `chat.py`/`document/pipeline.py`
into `jazzx_sdk/pipelines/`: closed a three-way "pipeline.py" naming
collision across the SDK and brought `DocumentAgentSpec` in line with its
sibling fat-agent families.

Collapse six duplicate `_reasoning` lazy-property copies into `BaseMode`; derive
`platform_catalog.MODES` from `modes.catalog.MODE_REGISTRY`

The identical lazy `_reasoning` property (plus its identical justification comment)
was independently declared in `VerifierMode`, `InvestigatorMode`, `GovernorMode`,
`ReasonerMode`, `NarratorMode`, and `EvaluatorMode` -- six copies of "construct the
`ReasoningAgent` on first use, not at `__init__` time." Moved to `BaseMode` once:
a `ctx: HandlerContext | None = None` class attribute, `self._reasoning_agent = None`
in `__init__`, and one `_reasoning` property reading `self.ctx.runtime.agents` /
`self.api_model_name`, raising a clear `RuntimeError` if `ctx` is unbound instead of
an opaque `AttributeError`. Deleted all six copies. Pure deduplication -- the full
mode test suite (239 tests) passes unchanged.

`platform_catalog.MODES` was a third, unlinked copy of "what modes exist," hand-
maintained alongside `modes.catalog.MODE_REGISTRY` and `fabric.canonical.trace`'s
`TraceStepMode` enum -- three lists that could silently drift. `MODES` now derives
its key set and descriptions from `MODE_REGISTRY` directly; only the emoji/display-
name presentation layer (which `MODE_REGISTRY` doesn't carry) stays a local dict.
`TraceStepMode` stays a separate enum rather than importing `modes` into it --
`trace.py` is a canonical-object module, and that edge would add an undocumented
cycle risk into `fabric.canonical` -- so a new test asserts the two stay set-
identical instead of deriving one from the other. Checked `jaci/ui/platform_view.py`'s
try/except-fallback import of seven `platform_catalog` symbols: every name it
imports is still exported unchanged.

2 new tests in test_platform_catalog.py (MODES tracks MODE_REGISTRY;
TraceStepMode/MODE_REGISTRY set-identity). Full suite green (2838 passed, 3 skipped).

`Curator.synthesize_bucket` migrated onto `ReasoningAgent` -- the last of the seven cognitive
modes still bypassing it

`synthesize_bucket` (Curator's Layer 2 LLM synthesis step) called a bare `llm.run()` via
`jazzx_sdk.llm.structured_call` -- no retry, no truncation handling, no token accounting, the
same gap `EvaluatorMode` had before its own v2.4.0 migration. Added `agents:
AgentExecutionService | None` alongside the existing `llm: Any | None` (both now optional;
exactly one must be given, enforced with a `ValueError`). The `agents=` path constructs a
`ReasoningAgent` and routes through `name=f"curator:synthesize:{tag}",
output_type=_SynthesizedGuidance` -- the same retry-with-feedback-on-schema-failure and
truncation-retry handling the other six modes have, plus real token usage, recorded on the
returned asset's `metadata["tokens_used"]` (nowhere else to put it -- `GuidanceAsset` has no
dedicated usage field, and inventing one for a single caller wasn't warranted). The `llm=` path
stays for one release, now emitting a `DeprecationWarning` -- jaci's
`scenarios/ci_spread/demo_correction_to_guidance.py` and `tests/unit/test_hitl_approval.py` both
call it and are left unmigrated deliberately; the deprecation window is exactly for callers like
that.

5 new tests in test_curator_synthesis.py: the `agents=` path (asset content + token-usage
metadata, via the same monkeypatched-`ReasoningAgent` seam `test_evaluator_mode.py` established),
the deprecation warning on `llm=`, and the neither/both `ValueError` guard. Full suite green
(2841 passed, 3 skipped).

`TurnRunStore.latest_run(conversation_id)` -- the most recent run for a conversation, regardless
of status

Surveyed juno's recent commits for expansion ideas: a reconnecting chat UI needs to render "what's
happening now" for a conversation, and was reaching for a separately-tracked `last_message` status
field that can drift from the run record itself. `TurnRunStore` already had `has_active_run() ->
bool` but nothing that returns the run -- added `latest_run(conversation_id) -> TurnRun | None`,
the most recently created run regardless of status (QUEUED/RUNNING/terminal), so a caller reads
state from the source of truth instead of a second, driftable copy. Implemented on both backends:
`InProcessTurnRunStore` (max by `created_at` over the conversation's runs) and `DbTurnRunStore`
(one indexed query -- `conversation_id` and `created_at` were already indexed columns on
`TurnRunRecord` for `has_active_run`/FIFO ordering, so this adds no new index).

4 new tests in test_resilient_runs.py (both backends: returns the newest run by `created_at`
across multiple runs and multiple conversations, `None` for an unknown conversation). Full suite
green (2844 passed, 3 skipped).

`jazzx_sdk.manifest.bundle`/`.publish` -- a portable, retry-safe cross-instance promotion
primitive, generalized from `assistant`'s working export/publish pattern

Surveyed `assistant`'s recent commits for expansion ideas: `app/assistant/promotion.py` exports an
assistant's full dependency closure into one portable zip, then publishes each part into another
instance's owning service -- proven, working, ~1100 lines. Read it in full before generalizing
anything: most of it (BPMN/Flowable closure-walking, kernel's agent-config YAML shape, Knowledge
Hub collection resolution, Role CRUD) is `assistant`-repo domain specifics with no japes
equivalent -- porting that would be dead code in an SDK with no BPMN/Flowable/KH-collection
consumer. What's genuinely portable: the in-memory zip-slip-safe bundle format, a per-asset-type
`Publisher` protocol (each publisher owns its own conflict policy -- upsert, skip-duplicate,
reuse-by-name; `promote()` has no opinion on it), and the retry-safety convention itself -- every
`Publisher` is idempotent, and the caller writes its "roll-up" record only *after* `promote()`
returns successfully, mirroring `assistant`'s own "create the assistant row last" trick that makes
a failed publish resumable with the same bundle.

Scoped deliberately narrow: `jazzx_sdk.manifest.AssistantManifest` (skills + pack_id +
profile_ref) has no established "dependency closure" concept the way `assistant`'s `Assistant` row
does -- guessing at one now would be inventing structure a real consumer might want differently.
Shipped the generic primitive plus exactly one real, already-upsert-shaped reference
implementation instead of speculating further:

- `jazzx_sdk/manifest/bundle.py` -- `pack_bundle`/`unpack_bundle`, in-memory (no filesystem
  intermediate, unlike the document pipeline's disk-oriented `unpack_zip`), zip-slip-safe on
  unpack, plus a `BundleManifest` top-level entry (name/groups/warnings) so a receiving side can
  introspect a bundle without guessing from entry names.
- `jazzx_sdk/manifest/publish.py` -- `Publisher` protocol, `PublishResult`/`PromotionResult`, and
  `promote(groups, publishers=..., order=...)`, the ordered orchestrator. Fails loud (not silent
  drop) on a group with no registered publisher.
- `jazzx_sdk/manifest/publishers.py` -- `AgentDefinitionStorePublisher`, wrapping the already
  upsert-by-name `AgentDefinitionStore.put` (no new conflict policy needed). The one concrete
  implementation proving the protocol against a real store, not an abstraction with zero
  implementations.

18 new tests (test_manifest_bundle.py, test_manifest_publish.py): pack/unpack round-trip, empty
groups, zip-slip/absolute-path/non-zip/missing-manifest rejection; `promote()` ordering, missing-
publisher failure, result aggregation; `AgentDefinitionStorePublisher` upsert-by-name, retry
idempotency, entry-name-vs-definition-name decoupling, malformed-entry rejection; one end-to-end
bundle-to-store test. Full suite green (2862 passed, 3 skipped).

New `jazzx_sdk/pipelines/` package -- one home and one catalog for japes' "reference pipeline"
family, plus a symmetry cleanup found while designing it

Two reference pipelines already existed -- `chat.py` (wraps `InteractiveAgent`) and
`document/pipeline.py` (wraps `DocumentAgent`) -- built independently, in the same shape (a thin
`ConductorPipeline` + step functions + a per-invocation "Turn" dataclass + a `run_X()` wrapper),
without ever cross-referencing each other. Neither had a discovery point (no catalog entry the
way modes/experts/fabric-surfaces already get from `platform_catalog.py`), and "pipeline.py" as a
filename already meant three different things in the SDK: the `ConductorPipeline` primitive
itself (`conductor/pipeline.py`), a reference-pipeline instance built from it
(`document/pipeline.py`), and an unrelated bespoke batch pipeline that doesn't use
`ConductorPipeline` at all (`adjudication/pipeline.py`).

Moved both into a new `jazzx_sdk/pipelines/` package, sibling to `agents/`/`modes/`/`conductor/`
-- not just future multi-owner pipelines, all of them, since a lightly-used pipeline today could
grow to span more than one agent over time, at which point "whose package does it live in" stops
having a good answer. `agents/document/pipeline.py` renamed to `pipelines/document_ingest.py` on
the move (matching its own docstring's self-description); `chat.py` kept its name (already
domain-named, no collision) and just moved. Clean move, no re-export shim left at the old paths
(CLAUDE.md's own anti-pattern list names "re-exporting types" as a backwards-compatibility hack
to avoid) -- every japes-internal and jaci caller fixed in this pass.

New `jazzx_sdk/pipelines/catalog.py` -- `PipelineContract`/`PIPELINE_REGISTRY`, mirroring
`jazzx_sdk/modes/catalog.py`'s `ModeContract`/`MODE_REGISTRY` shape exactly: module path, the
primitive(s) wrapped, turn type, step ids, entrypoint. References pipelines by import path rather
than physically containing their code, same as `MODE_REGISTRY` does for modes. `platform_catalog.
PIPELINES` (id -> description) derives from it, same pattern just shipped for `MODES` earlier in
this version. Deliberately lightweight: `jazzx_sdk/pipelines/__init__.py` only imports the
catalog, not `chat.py`/`document_ingest.py` themselves -- matches `jazzx_sdk/modes/__init__.py`'s
own convention of never eagerly importing its heavy per-mode implementations just to expose the
registry; confirmed empirically (no `InteractiveAgent`/`DocumentAgent` modules load transitively
via `platform_catalog.PIPELINES`).

Auditing every repeated filename across `jazzx_sdk/` (14 `base.py`, 12 `store.py`, 4 `catalog.py`,
4 `agent.py`, 3 `pipeline.py`, 3 `engine.py`, 3 `loader.py`, 7 `schema.py` + 4 `schemas.py`, ...)
to check whether "pipeline.py" was a one-off or a symptom found two more real instances of the
same failure mode (same filename, genuinely different structural role -- not just "same name,
same convention, different domain," which every other repeated name turned out to be):

- `agents/adjudication/pipeline.py` -> `agents/adjudication/segment.py` (matching its own
  `run_segment` entrypoint) -- fully closes the "pipeline.py means two things" collision this
  pass started from, rather than narrowing it. Internal-only, no jaci consumer.
- `DocumentAgentSpec` extracted from `agent.py` (651 lines, largest of the three fat-agent
  `agent.py` files) into a new `agents/document/spec.py`, matching `InteractiveAgentSpec`/
  `AdjudicationAgentSpec`'s already-dedicated `spec.py` convention.

Assessed and deliberately left alone: `schema.py`/`schemas.py`'s singular/plural spelling split
(11 files, zero semantic ambiguity, high churn for a cosmetic fix); `manifest/store.py` and
`runs/store.py` being the only two `store.py`s not nested under `fabric/` (possibly intentional --
a standing persistence-architecture note distinguishes service-owned-db from fabric-as-HTTP-
domain-service as two deliberate patterns -- flagged, not touched; moving an established
top-level package is a materially bigger, riskier change than anything else in this pass).

New `tests/test_pipeline_catalog.py` (registry shape, contract accuracy, every registered module
path actually importable) plus a `platform_catalog.PIPELINES` tracking test in
`test_platform_catalog.py`. `tests/test_adjudication_pipeline.py` renamed to
`test_adjudication_segment.py`. Full suite green (2869 passed, 3 skipped).

New `jazzx_sdk/pipelines/investigation_loop.py` -- the third reference pipeline, generalizing a
shape five jaci scenarios independently hand-rolled

Deep-read all five jaci investigation-loop conductors (AML, KYC, CRE-underwriting,
KYC-Anthropic, earnings_anthropic) plus `jazzx_sdk/conductor/{base,engine,checkpoint}.py` and
every operational mode's real constructor/`run()` signature before designing anything.
`BaseConductor` is a bare 27-line ABC; `ConductorEngine` already has native loop-until-converged
support (no pack hand-rolls a `while` loop except the pre-migration KYC baseline). All five
conductors share one real skeleton -- six modes constructed once and cached on `self`, near-
identical `_step_investigator`/`_step_evidence`/`_step_verifier` bodies, the same
`pipeline.model_copy` -> override `max_iterations` -> `ConductorEngine(...).run(context=ctx)` ->
assemble a pack-owned result object from `run.emitted_for(...)` skeleton -- but diverge on real,
load-bearing behavior: convergence representation (`LoopStatus` enum vs. a bespoke boolean
flag), convergence policy (trust the LLM's own claim vs. AML/CRE's deterministic
evidence-type-count + iteration floor), Sentinel presence (also where the per-iteration
checkpoint fires, in the two conductors that have one), checkpointing (zero in three of five),
a deadline guard (AML-only), reasoner-failure policy (halt vs. synthesize-a-fallback), and the
narrator-gate predicate (every pack has its own "is this the escalating outcome" check).

`InvestigationSpec` -- six already-constructed mode instances (mode construction is already
adequately generic via each `Mode.__init__`'s own kwargs) plus the hooks where the five
conductors actually diverge: `fulfill_evidence` (required, 100% pack-owned -- every real tool
registry has a different `execute()` signature), `sentinel` (optional), `is_active`/
`mark_converged`/`mark_guard_fired` (convergence-state indirection -- defaults read/write the
SDK's own `Context.loop_status` field directly, so any `Context` subclass works with zero
overrides; a pack with a bespoke convergence field overrides these three instead of forcing a
canonical shape), `convergence_gate` (default: trust the LLM), `deadline_guard` (default: never
fires), `on_reasoner_failure` (default: `None`, leaving the reasoner step's output `None`),
`narrator_gate` (default: governor-approved only), `checkpoint` (default: none, called from the
Sentinel step only -- matches every real conductor's own behavior, confirmed no conductor
checkpoints per-iteration without a Sentinel present). Deliberately not part of this primitive:
a `persist` step -- a pack's final checkpoint is tangled up with its own `CanonicalTrace`
construction (different fields, a termination-reason map specific to its own status
vocabulary); `build_investigation_pipeline` declares an optional `persist` step id a pack can
bind its own component to, same as `document_ingest.py`'s optional `package`/`collection` steps.
Registered in `PIPELINE_REGISTRY`.

15 new tests (`test_investigation_loop.py`, fake modes matching the six real signatures):
convergence-gate override, default hooks against `Context.loop_status`, Sentinel wired only
when set, checkpoint firing only via an active Sentinel pass (confirmed against AML's own real
behavior -- no checkpoint on the converging iteration either), narrator-gate suppression,
reasoner-failure fallback, deadline-guard short-circuit, `persist` skippable/bindable. Plus a
`test_pipeline_catalog.py` entry. Full suite green (2885 passed, 3 skipped).

Proof-of-concept migration (jaci, same day): `EarningsAnthropicConductor` -- the simplest of the
five (no Sentinel, no checkpoint, no deadline guard) -- now builds an `InvestigationSpec` instead
of hand-rolling `_components()`/`_step_*` methods; existing tests pass unchanged (parity, not a
behavior change). AML/CRE/KYC-Anthropic/KYC-plain migrations are explicitly deferred, separate,
higher-risk follow-on work once this primitive is proven -- KYC-plain additionally needs its own
prior migration onto `ConductorEngine` before it's even a candidate.

`jazzx_sdk/pipelines/investigation_loop.py` gains two additive extension points, closing the gap
between the proof-of-concept (earnings_anthropic) and the primitive's actual first-class target
(CRE) -- found by reading CRE's real, current code, not the earlier survey summary

`InvestigationSpec.halt_on_reasoner_failure: bool = False` -- CRE halts the whole run on reasoner
failure (`ConductorState.halt = True`, downstream steps recorded halted) instead of the
fallback-and-continue every other conductor uses; `on_reasoner_failure`'s existing contract is
unchanged, this is a new, independent branch in `reasoner_step`.

`build_investigation_pipeline(post_loop_steps=...)` replaces the hardcoded
`reasoner -> governor -> narrator` triplet with a pack-supplied sequence (default unchanged) --
CRE interleaves three deterministic, non-generalizable steps (DSCR stress-test math, an advisory
policy check, dependency-condition mapping) in a specific order the fixed triplet couldn't
express. `build_investigation_components(spec, overrides=...)` replaces the narrower
`persist=` param with a general override map, merged last -- lets a pack add step ids the
primitive doesn't define, or replace a generic step wholesale (CRE's real `governor` step
mutates the reasoner's own decision object and `ctx.loop_status` in place rather than returning
a decision, and its `narrator` step builds a credit-memo `Artifact`, not just a narrative --
neither fits the generic step's contract at all). Not used by any other caller today, so a safe,
non-breaking widening; updated the one existing `persist=` test to the new kwarg name.

4 new tests (`halt_on_reasoner_failure` sets `state.halt`/leaves reasoner output `None`, and the
false-path still falls through to `on_reasoner_failure`; `overrides=` replacing a generic step
wholesale; `post_loop_steps` producing a declared custom sequence). Full suite green (2889
passed, 3 skipped).

`CREConductor` migrated (jaci, same day) -- the primitive's actual first-class target, not
another proof-of-concept. `_step_investigator`/`_step_evidence`/`_step_verifier`/`_step_sentinel`/
`_step_reasoner`/`_components()` replaced by an `InvestigationSpec`;
`_step_stress`/`_step_policy`/`_step_governor`/`_step_dependencies`/`_step_narrator`/
`_step_persist` kept verbatim as `overrides=` -- genuinely pack-specific, exactly what the
primitive was designed to leave pack-owned. `describe()` returns the generic pipeline instead of
the YAML-loaded `CRE_PIPELINE` (kept as a module symbol solely for `ui/registry.py`'s diagram
lookup, same pattern earnings_anthropic's migration established). `CRE_PIPELINE` uses
`ctx.loop_status` directly (the SDK `Context` base's own field) -- exactly what the primitive's
default `is_active`/`mark_converged`/`mark_guard_fired` hooks already read/write, so CRE needed
zero overrides there, unlike earnings_anthropic's bespoke boolean flag. Existing offline
orchestration tests (`tests/unit/test_cre_conductor_engine.py`) pass unchanged -- parity, not a
behavior change.

`InvestigationSpec.on_mode_result` -- one more additive hook, for `AMLConductor`'s migration

AML accumulates real LLM token usage per mode (`ctx.metadata["token_usage_by_mode"]`) after every
investigator/verifier/reasoner/governor/narrator call, feeding a cost-tracking eval
(`tests/eval/test_anthropic_token_tracking.py` in jaci, gated behind a live-API-key marker so not
in the offline suite, but a real, tested feature not to be silently dropped). No existing hook
covered "do something with every mode's raw result" -- `on_mode_result: Callable[[ctx, step_name,
result], None] | None = None`, called from those five generic steps only (not Sentinel's, which
is deterministic/non-LLM and has nothing to accumulate). Default `None` -- no-op, unchanged
behavior for `chat`/`document_ingest`/earnings_anthropic/CRE. 2 new tests. Full suite green (2891
passed, 3 skipped).

`AMLConductor` migrated (jaci, same day) -- structurally the closest of the four migrated so far
to CRE (deterministic convergence floor, Sentinel + checkpointing, `ctx.loop_status` used
directly, zero overrides for the convergence-state hooks) but without CRE's extra steps or
mutate-in-place governor -- its governor/narrator instead follow earnings_anthropic's pattern
exactly (generic steps mid-run; the pack remaps/gates in its own post-processing). First real use
of `deadline_guard` (AML's SAR-deadline check) and `on_mode_result` outside their own test
coverage. `_step_investigator`/`_step_evidence`/`_step_verifier`/`_step_sentinel`/
`_step_reasoner`/`_step_governor`/`_step_narrator`/`_components()` replaced by an
`InvestigationSpec`; `_step_persist` kept verbatim as the one `overrides=` entry. Existing offline
orchestration tests (`tests/unit/test_aml_conductor_engine.py`) pass unchanged.

## [2.3.5] - 2026-08-10

Agent identity for eval/feedback attribution; per-skill/parent tool_use_behavior

- InteractiveAgentSpec.agent_id: a stable identity carrier for eval/feedback attribution.
  None -> falls back to spec.name (InteractiveResponse.agent_id, stamped on every turn).
  spec_binding.bind_spec() now carries manifest.assistant_id onto spec.agent_id when the
  profile didn't set one explicitly -- closes a real gap where the manifest layer already
  had a proper assistant_id, but it was dropped during manifest -> spec narrowing and never
  reached the running agent. Feedback.agent_id threaded through for_turn()/
  InteractiveResponse.feedback() so feedback records carry the same attribution as the turn.
- Skill.tool_use_behavior / InteractiveAgentSpec.tool_use_behavior: per-skill and parent-level
  overrides for Agent.tool_use_behavior ("stop_on_first_tool" skips the extra LLM round-trip
  when a tool's own output is the final answer, e.g. a deterministic lookup skill). Mirrors
  the existing max_turns override shape; both default to unset (SDK default, byte-identical
  behavior for existing specs).

Fix replicas default, document stochastic, close domain-neutrality gap; migrate
EvaluatorMode/NarratorMode/VerifierMode onto ReasoningAgent; fix BaseMode silent fallback

From an independent completeness audit against the AdjudicationAgent chassis:

- replicas default 3 -> 1 across spec.py/pipeline.py/conductor/replication.py. The
  shipped default contradicted this repo's own measurement (batched k=3 on a real
  fixture: zero variance reduction, 3.1x cost) -- an inherited-not-measured
  assumption, not a tuned one.
- ConditionEvaluator.stochastic documented as currently redundant with
  execution == LIVE across all four registered evaluators, rather than wired into
  partition_rules -- no evaluator yet needs the distinction; wiring it now would be
  an untested seam with no behavior to justify it.
- modes/catalog.py: nulled five AML literals (canonical_produces/canonical_consumes/
  derived_object on investigator/conductor/narrator) that had no business being in a
  domain-neutral mode registry -- verified nothing in jazzx_sdk reads them first.
- EvaluatorMode migrated onto ReasoningAgent: now inherits BaseMode, constructor takes
  ctx: HandlerContext, run() returns ModeResult. Previously held its own AsyncOpenAI
  client (unusable on an Anthropic-only deployment) and parsed a bare json.loads with
  no retry -- a truncated/malformed response either raised or silently produced an
  empty improvement_signals list, stopping the compounding loop with no error
  anywhere.
- Caught along the way: a dict-typed output_type field (typed or bare) breaks
  OpenAI's strict-schema mode outright. Fixed for the new _EvaluatorLlmOutput model,
  then found and fixed the same pre-existing bug in NarratorMode (NarrativeOutput)
  and VerifierMode (VerifierReport). Also cleaned up VerifierMode's empty-batch
  return, which built its result with six kwargs that aren't real fields on that
  model -- pydantic silently dropped them, so this was always producing the same
  bare-defaults object a plain call would, just via misleading dead code.
- BaseMode.system_prompt no longer swallows a missing pack asset: was catching
  FileNotFoundError and substituting a fabricated "You are the {mode} mode." prompt.
  resolve_mode_prompt documents raising as its actual contract; every mode's run()
  already wraps this access in a broad except Exception, so this now surfaces as a
  real, checkable failure instead of a silent bad prompt.


Add AdjudicationAgent chassis (jazzx_sdk.agents.adjudication)

  Per-segment obligation checking: batched replicated verification for           
  LLM-evaluated obligations, direct evaluation for deterministic ones,           
  scoped evidence access per segment, applicability gating, incremental          
  re-run support, and a fail-closed dynamic segment planner. New                 
  NaturalLanguageCondition evaluator; Trace mode-tagging fix for                 
  mlflow_bridge; toy demo pack.

  Per-segment obligation checking with replicated variance reduction --
  generalizes MACER's own section x replica x batch-verify shape into a
  reusable, domain-neutral SDK primitive.

  - workspace.py: EvidenceWorkspace/Mount -- narrows the ambient
    PermissionScope to a segment's mounts for the duration of its calls,
    restored after.
  - partition.py: partition_rules splits a segment's Rule objects into
    DETERMINISTIC/LIVE by resolved ConditionEvaluator.execution.
  - spec.py: AdjudicationAgentSpec -- domain-neutral pack config (persona,
    model, replicas, regime_values/status_vocabulary carried verbatim,
    never branched on), with from_dir(yaml + persona.md) loading.
  - pipeline.py: run_segment -- batches every LIVE obligation into one
    prompt per replica, replicates (P1 run_replicated_segments), collapses
    per obligation (P2 EnsembleCollapse); DETERMINISTIC rules go straight
    through their own evaluator, no LLM. A rule with condition=None is
    skipped, matching DefaultPolicyExpert.check_compliance exactly.
  - agent.py: AdjudicationAgent facade -- fans run_segment out across
    segments (one bad segment doesn't sink the case), reconciles, emits a
    narrative. A narrative-generation failure never discards already-
    computed outcomes.
  - fabric.canonical.policy/condition_evaluator: new NaturalLanguageCondition
    kind + NaturalLanguageEvaluator (LIVE, stochastic) -- the Condition
    union had no LLM-backed kind for a chassis-level obligation to declare
    itself LIVE with.
  - observability.mlflow_bridge: new name_patterns parameter on
    span_to_trace_step/spans_to_canonical_trace -- the existing mode_map
    is keyed on span_type (LLM/TOOL/...), too coarse to tell an adjudicate
    call from an emit call apart (both are plain LLM spans); name_patterns
    matches on the agent/session name instead, checked first.
  - examples/adjudication_demo: toy two-segment mortgage-underwriting pack
    (mirrors examples/loan_assistant's spec-plus-harness shape).

Add P3/P7 (impact resolution + segment planning) to the AdjudicationAgent
chassis

  Generalizes MACER's rerun_orchestrator.py/orchestrator_agent.py rather
  than porting them -- MACER may never adopt this chassis, but the
  primitives are useful to japes's other consumers regardless.

  - pipeline.run_segment: now honors Rule.applicability (a real gap --
    it didn't before, unlike DefaultPolicyExpert.check_compliance). An
    inapplicable rule short-circuits to RuleOutcome(verdict=NOT_APPLICABLE)
    before reaching its condition, deterministic or LIVE, no LLM call.
  - New agents.adjudication.planner: SegmentPlanner protocol +
    plan_or_fallback -- the SDK owns the fail-closed discipline (planner
    exception or empty plan falls back to the static segment list); the
    case-profile/regrouping logic itself stays pack-side.
  - New agents.adjudication.impact: impacted_rules() keys off
    ConditionEvaluator.evidence_contract() (P8) instead of MACER's
    document-classification-triple mapping file -- reusable by any pack.
    merge_with_carry_forward() + a RunMode enum/resolve_run_mode()
    matching MACER's own INITIAL/INCREMENTAL/FORCED_FULL upgrade-downgrade
    rules, plus a NO_OP mode for explicitly-empty impact.
  - AdjudicationAgent.adjudicate: new optional planner/changed_fields/
    prior_outcomes params wire both in; omitting all three is unchanged
    from the prior release.

Fix replicas default, document stochastic, close a domain-neutrality gap
(from an independent completeness audit against the chassis work above)

  - agents.adjudication.spec/pipeline, conductor.replication: replicas
    default 3 -> 1. The shipped default contradicted this repo's own
    measurement (batched k=3 on a real fixture: zero variance reduction,
    3.1x cost) -- an inherited-not-measured assumption, not a tuned one.
  - fabric.canonical.condition_evaluator.ConditionEvaluator.stochastic:
    documented, not wired -- it's currently redundant with
    execution == LIVE across all four registered evaluators, so gating
    partition_rules on it today would be an untested seam with no
    behavior to justify it.
  - modes/catalog.py: nulled five AML literals (canonical_produces/
    canonical_consumes/derived_object on investigator/conductor/
    narrator) that had no business being in a domain-neutral mode
    registry -- verified nothing in jazzx_sdk reads them first.

Migrate EvaluatorMode onto ReasoningAgent

  The one EVOLVE-layer mode left out of the v2.3.0 five-mode migration.
  Previously held its own AsyncOpenAI client (unusable on an
  Anthropic-only deployment) and parsed a bare json.loads with no
  retry -- a truncated/malformed response either raised or silently
  produced an empty improvement_signals list, stopping the compounding
  loop with no error anywhere.

  - modes/evolve/evaluator.py: now inherits BaseMode; constructor takes
    ctx: HandlerContext (matching the other five modes); run() returns
    ModeResult instead of a bare EvaluationReport. No real caller
    depended on the old shape (verified zero constructor call sites
    anywhere in japes beyond docstring mentions and re-exports).
  - Caught along the way: a dict-typed output_type field (typed or
    bare) breaks OpenAI's strict-schema mode outright
    ("additionalProperties should not be set") -- confirmed this would
    also break NarratorMode's NarrativeOutput.sections in a real call.
    Fixed only for the new _EvaluatorLlmOutput model via
    AgentOutputSchema(..., strict_json_schema=False); NarratorMode's
    pre-existing instance of the same bug is untouched, out of scope.

Fix the same strict-schema bug in NarratorMode

  - modes/operational/narrator.py: NarrativeOutput's sections/
    citations/metadata are all dict-typed -- same AgentOutputSchema(...,
    strict_json_schema=False) fix. The existing test file mocked at the
    Runner.run() level (the ReasoningAgent.run(runner=...) test seam),
    so it never reached the real get_output_schema()/AgentOutputSchema
    construction either -- added the same boundary contract test.
  - Found, then fixed same-session: VerifierMode/VerifierReport has the
    identical bug (evidence_results/notes/attestations all dict-typed).
    GovernorMode/GovernorDecision and InvestigatorMode/HypothesisUpdate
    are clean (list/bool/str only); ReasonerMode's output_schema is
    pack-supplied, not an SDK schema.

Fix the same strict-schema bug in VerifierMode

  - modes/operational/verifier.py: same AgentOutputSchema(...,
    strict_json_schema=False) fix, same test blind spot, same added
    contract test.
  - Cleaned up (not a behavior change): the empty-evidence early return
    built VerifierReport(evidence_id=..., status=..., quality_score=...,
    findings=..., flags=..., attestation=...) -- none of those are real
    VerifierReport fields; pydantic v2 silently ignores unknown kwargs,
    so this always produced the same bare-defaults object a plain
    VerifierReport() would, just via misleading dead code.

Fix BaseMode.system_prompt silently swallowing a missing pack asset

  Was: catch FileNotFoundError, log a warning, substitute a fabricated
  "You are the {mode_name} mode." prompt. resolve_mode_prompt documents
  its own contract as raising on a genuine miss; BaseMode was silently
  defeating that -- a mode running on a fabricated prompt with no
  visible error is a capability failing silently, not loud.

  - modes/base.py: system_prompt now lets FileNotFoundError propagate.
    Every mode's run() already wraps this access in a broad except
    Exception -> ModeResult(success=False, error=...), so this surfaces
    as a real, checkable failure instead of a crash or a silent bad
    prompt.

## 2.3.4
Generalize install_request_headers_hook for bare httpx clients

  Detects a bare httpx.AsyncClient/httpx.Client (not just a generated
  AuthenticatedClient/Client wrapper) and installs the hook directly on
  its own event_hooks["request"] -- covers a consumer building a plain
  httpx client by hand (e.g. jazzx-assistant's assistant_client.py)
  without needing a generated-client wrapper to hang the hook off of.

  Export install_request_headers_hook, add KernelClient.get_agent, add
  render_prompt_template
  
  - clients.__init__: install_request_headers_hook is now public -- a
    consumer wrapping their own raw generated client (not going through
    KernelClient/KnowledgeHubClient) can harden it the same way, instead
    of hand-rolling per-call header injection.
  - KernelClient.get_agent(name): mirrors get_tool(), reuses the same
    search_agent_by_name endpoint invoke_agent already uses internally.
  - New jazzx_sdk.templating.render_prompt_template: sandboxed Jinja2
    rendering of untrusted templates into prompts, fail-soft on any
    error (bad syntax, sandbox violation, jinja2 not installed). New
    optional 'templating' extra (jinja2), lazy-imported. Exported from
    jazzx_sdk.templating and the top-level jazzx_sdk package.


  Bump patch version to 2.3.4
  
  - fabric.canonical.store.core.PolicyStore.list_policies: paginate                                
    read_entities (was capped at limit=500, silently dropping policies                             
    beyond the first page).                                                                        
  - tools.documents.classifiers.classify_llm: completeness_passed was                              
    vacuously True for a document type with no registered classifier                               
    (required=[] -> not [] == True even though nothing was extracted).                             
  - server.governed_http: clear_governed_context() now runs on early                               
    400/409 exits too, not just the happy path (set_governed_context and                           
    the mutating-idempotency check moved inside the try/finally).                                  
  - tools.agent.dir_tools.build_directory_tools: show_hidden: bool =                               
    False -- dotfiles excluded from list_documents/search_documents by                             
    default (write_document also refuses to create one), with an opt-in                            
    for a caller with a legitimate dotfile.                                                        
  - fabric.fabric.KnowledgeFabric: accepts manifest_store, threaded to                             
    the lazily-constructed DocStore. Added NullMaterializeManifestStore                            
    (jazzx_sdk.fabric.docs) as a first-class no-persistence option. 

## 2.3.3 contd.
 Generalize escaped-literal-text stripping beyond NUL to surrogates and C0
  controls 
  
  sanitize.py: the double-JSON-encode mechanism that surfaces a NUL's
  "\u0000" escape as literal text applies equally to lone surrogates and
  C0 controls. _SURROGATE_LITERAL/_CONTROL_LITERAL now strip those forms
  too (control literals still opt-in via strip_control, matching the
  real-byte behavior). Both derived from the same code-point sets as the 
  real-character checks, so the two can't drift apart. 

  Fix bot-reported gaps: SSRF scheme allowlist, PreflightGate empty-refusal fail-open, sync_collection page_size drift, dir_tools path-containment bypass

  - net_safety.validate_url_safe + tools/documents/local._validate_url_safe:
    reject non-http(s) schemes (file://, gopher://, ...), not just private IPs.
    Documented (TODO) the separate, still-open DNS-rebinding gap in is_private_ip.
  - PreflightGate.evaluate: an empty-string refusal now still blocks (falls
    back to fallback_refusal) instead of silently passing the turn through --
    matches the class's own documented contract (None = pass, any string = block).
  - fabric.docs.store.sync_collection: page_size 100 -> 1000, matching the
    other 5 KH pagination fixes (was an unintentional drift, no server cap).
  - tools.agent.dir_tools._safe_relative: path-containment check now uses
    parents-based comparison instead of a naive string prefix, closing a 
    symlink-escape bypass via a sibling directory sharing root's name as a 
    prefix (same pattern as the existing zip-slip guard).
- **Fixed** — `python` floor raised to `>=3.12` (was `>=3.11`, already broken for Claude via `ReasoningAgent`/litellm; no real consumer runs 3.11).
- **Fixed** — `DslEvaluator.evidence_contract` now calls `jazzx_sdk.expressions.parse.identifiers()` (existed all along, just never wired) — a DSL rule now correctly claims its referenced fields, fixing policy precedence (a deal-level DSL rule no longer lets a lower overlay rule also fire on the same field).
- **Fixed** — `InteractiveAgent._skill_instructions` now gates `Skill.references` through `admit_hop` like `tools`/`reads` already do — a caller denied `ref:x` could previously still receive its content.
- **Fixed** — `_series_value` (time-series formulas: `prior`/`avg`/`cagr`/`ltm`) now enforces `confidence_floor`, matching the plain-field-lookup path.
- **Added** — `PreflightGate`/`PreflightGateDecision` (`jazzx_sdk.agents.interactive`) — a generic pre-agent classification gate (one LLM round-trip: structured verdict + deterministic output-guardrail refusal mapping), generalized from jazzx-assistant's hand-built mortgage-safety gate.
- **Added** — `Source.locator` (`jazzx_sdk.agents.interactive.response`) — citations can now carry a page/cell/section `Locator`, same union `SourceCoordinate` already uses; `SourceBuilder` passes it through unchanged.

Known limitation, not fixed: Dependabot alert #98 (`cryptography>=50.0.0`) still deferred — mlflow caps `cryptography<50` through at least 3.15.1. Also flagged, not yet fixed: `sync_collection()` fetches only the first 100 KH documents (no pagination) and resolves duplicate filenames by list order rather than doc id, which can silently mismatch content on a re-sync.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.3] - 2026-08-05

- **Added** — `EvidenceRequestSpec`/`RichHypothesisUpdate` + `InvestigatorMode(rich_evidence_requests=True)`: lets a domain's Investigator keep LLM-authored per-request `query_params` (e.g. which policy clause to fetch) instead of the bare `evidence_requests: list[str]` AML/CRE use. Existing callers unaffected.
- **Added** — `GovernorDecision.required_actions` — real downstream consumers (KYC-Anthropic/Earnings-Anthropic UIs) read this; the shared `GovernorMode` didn't carry it.
- **Added** — `run_kit.run_agent` now stabilizes `prompt_cache_key` across every retry/continuation of a run when the caller didn't set one, generalizing a mechanism MACER's own `agent_utils.run_agent` proved out; no `ReasoningAgent`-backed mode set one before.
- **Added** — `ReasoningGroupEvictStrategy` (`jazzx_sdk.agents.interactive`) — a `reasoning_group_evict` `CompactionStrategy`, porting MACER's `input_filter.py` group-eviction algorithm as token-triggered (via `max_chars`) instead of byte-triggered. `run_kit.evict_reasoning_groups` is the shared, budget-agnostic algorithm behind both this and the existing byte-triggered `InputFilter`.
- **Fixed** — Dependabot: bumped `aiohttp>=3.14.3` (OOB heap read, WebSocket request smuggling, unnegotiated compressed frames) and `gitpython>=3.1.57` (arbitrary file truncation/read/overwrite via unguarded git options), clearing 6 of 7 open alerts. `cryptography>=50.0.0` (alert #98, Bleichenbacher oracle) deferred: every mlflow release through 3.15.1 caps `cryptography<50`, so bumping it now would silently downgrade mlflow 3.14.0→3.2.0. Revisit once mlflow ships a compatible release.

## [2.3.2] - 2026-08-04

`docs/plans/plan_assistant_sourav.md` (Studio design-doc review — P0/P1/P2/P3 code items, all
done) + `docs/plans/plan_kh_client_bump.md` (KH v2 idempotency — entity + document sides, plus
identity/RBAC verification).

- **Added** — `Skill.reads` (`jazzx_sdk/agents/interactive/{spec,reads,agent}.py`): a skill
  declares which `KnowledgeBinding`s (by new `KnowledgeBinding.name`) it needs on-demand tool
  access to; `InteractiveAgent` generates a closure-bound `list_<name>`/`read_<name>`/
  `search_<name>` `@function_tool` triple per binding at build time, gated through the existing
  `admit_hop`/`PermissionScope.narrow()` cascade via a new `doc_source:<name>` selector. Fixes a
  real correctness gap: the push-based `docs:` grounding path (`resolve_knowledge`) only ever
  emitted `"[doc] {name}"` per document — filename only — so a grounded agent could name a
  document and read none of its content. `list_`/`search_` rendering reuses
  `tools.agent.grounding.build_summary_index` (that helper's first real internal consumer,
  closing a second near-duplicate index-renderer risk); `select_items` doesn't fold in (in-memory
  dict select vs. `reads`' remote per-id fetch — a different mechanism).
- **Added** — `Skill.spec_ref` (assistant-as-skill composition, architecture doc §6): a skill can
  name a full `InteractiveAgentSpec` (resolved via a new `InteractiveAgent(profile_registry=...)`
  param) and run it as its own independently-guarded turn — its own guardrails/knowledge/
  output_schema all apply, unlike a flattened `tools`/`references` skill — exposed to the parent
  as a plain `@function_tool` (there's no Agents-SDK `Agent` object to wrap via `as_tool()`). No
  manual permission-scope narrowing needed: the nested turn runs under the same ambient
  `InvocationContext`, and its own `_check_turn_entry` already checks `assistant:<spec_ref>`.
- **Added** — `ProfileRegistry.validate()` now also checks the `spec_ref` composition graph: a
  dangling reference (doesn't resolve within the same registry) or a cycle (A wraps B wraps A,
  which would recurse forever at runtime) both fail validation with the actual cycle chain named.
  New `ProfileRegistry.publish()` (async) runs `validate()` first, then an optional
  `evaluator(name, spec) -> reason | None` hook (the same block-reason convention as a
  `GuardrailCheck`) — a caller-supplied extension point, not a hard-wire to
  `jazzx_sdk.evaluation`'s pack/conductor-shaped `EvaluationHarness`. Side-effect classification
  (the architecture doc's 3rd publish check) is explicitly not implemented — no such concept
  exists anywhere in `jazzx_sdk.tools` yet.
- **Added** — `SkillRegistry`/`GuardrailRegistry` tiering: `register(..., tier=)` (default 3) /
  `tier_of(name)`, the same 1/2/3 platform/pack-config/builder convention as
  `tools.documents.templates.TemplateRegistry`. Goes one step past that reference pattern: a
  less-trusted tier registering over an existing more-trusted name now raises unless
  `allow_override=True` is passed explicitly (`TemplateRegistry`'s own bare `_put` has no such
  guard).
- **Added** — `jazzx_sdk.server.create_knowledge_hub_mock_app(client=None, **client_kwargs)`: a
  FastAPI adapter serving any `KnowledgeHubLike` delegate (a fresh `MockKnowledgeHubClient` by
  default — already covers `list_documents`/`download_documents`/`read_entities`/`create_entity`/
  etc., file-backed via `data_dir=`) over HTTP routes matching the real KH API 1:1. Closes "every
  pack rebuilds a mock KH server" (jazzx-assistant's own hand-rolled `mock_knowledge_hub` FastAPI
  app + `FileBackedStore` was the motivating case) without generalizing the parts that don't
  generalize: a pack's own product-specific API mock (e.g. jazzx-assistant's `mock_assistant_api`
  — no shared japes client behind it) and devcontainer/compose templates (deploy infra, not SDK
  code) both stay pack-owned.
- **Added** — `scripts/new_assistant_scaffold.py <domain-name>`: generates
  `examples/<domain>/{profile/{profile.yaml,persona.md},harness.py,handler.py,test_<domain>.py,
  README.md}` — the middle rung between the 20-line `examples/loan_assistant/` snippet and a full
  production pack. Generated profile is deliberately skill-less so its test can use
  `jazzx_sdk.llm.scripted.ScriptedLLM` directly (keyless, no live model) — `ScriptedLLM` only
  covers the single-shot path, not the agentic Runner path. `handler.py` demonstrates the six
  `HandlerContext` touchpoints (`ctx.message`, `ctx.runtime`, `ctx.extend_visibility`/
  `log_metric`/`update_status`, and building the response off `ctx.message.header`), marked 1-6
  inline.
- **Added** — `handlers.propagated_headers`: context-manager counterpart to
  `set_propagated_headers`/`clear_propagated_headers` (sync + async, clears even on exception),
  mirroring `security_context`'s exact shape — juno had independently hand-rolled the identical
  capture/restore pattern for the same queue-worker identity-propagation problem this module
  already solves.
- **Fixed** — `InProcessTurnRunStore.reap_stale` (`jazzx_sdk/runs/store.py`) swept off a
  `list(self._runs.values())` snapshot taken at loop start; a concurrent `heartbeat()` renewing a
  *later* run in the same sweep, landing during an *earlier* run's `await self.update(...)` (the
  loop's only yield point), still got reaped off stale data. Prompted by a real juno production
  incident (#227). Fix: re-read each run fresh from `self._runs` immediately before its own
  staleness check/write, matching what `store_db.py`'s row-locked `reap_stale` already does for
  the DB backend.
- **Fixed** — `EntityStore.ensure(idempotency_key=...)` (`jazzx_sdk/fabric/entities/store.py`)
  never actually deduped by key: `_find_by_fingerprint` only ever matched a candidate's *content*
  hash, but a key-derived fingerprint is never equal to a content hash, so two calls with the same
  key but different content silently created two entities instead of one — despite `ensure()`'s
  own docstring promising the opposite. Fixed: an explicit `idempotency_key` now matches by
  `(collection_id, name)` instead of content (there's nowhere else to persist an arbitrary caller
  key remotely — `json_value` must conform to the caller's ontology schema).
- **Added** — KH v2 idempotent-create wiring, entity side
  (`jazzx_sdk/clients/knowledge_hub_client.py::create_entity_v2` now returns `(entity, created)`
  instead of just `entity` — the native 201-vs-200 signal — and `EntityStore.ensure()` prefers it
  over the pre-check+v1 path when available and no explicit `idempotency_key` is given).
- **Added** — KH v2 idempotent-create wiring, document side: no generated binding exists for
  document create anywhere in `client-api` (checked the pinned rev and its latest available
  commit) — unlike entities, whose v2 bindings already existed unwired.
  `KnowledgeHubClient.create_document_v2` is hand-rolled directly against the shared httpx client
  (same `_MultipartBody` file-part encoding v1's generated binding uses, so the existing
  request-headers-provider and denied-response hooks still apply); meant to be replaced by a real
  generated binding once `client-api` regenerates. `DocStore.ensure()` prefers it the same way,
  hydrating a 200 idempotent-hit's id-only response via the existing `_outcome()` re-fetch.
  `MockKnowledgeHubClient` gets `create_entity_v2`/`create_document_v2` for parity, signatures
  exact-matching the real client's per the existing mock/real parameter-drift contract test.
- **Verified** — KH v2 bump identity/RBAC step: `x-user-id` forwarding on every KH write path
  (`create_entity`, `create_entity_v2`, `update_entity`, `create_document`, `create_document_v2`)
  and `read_entity` 401/403 → `KnowledgeHubAccessError` (404 staying a plain miss, never conflated
  with denial) were asserted in the plan but never exercised end-to-end against a real
  `KnowledgeHubClient` call — new `httpx.MockTransport` round-trip tests close that gap. No code
  change; both claims held. Cross-checked KH's own server source directly:
  `common/core/dependencies.py::get_current_user_id_optional` reads the literal `x-user-id`
  header and `api_v2.py` stamps it onto `created_by_user_id`/`updated_by_user_id`.

## [2.3.1] - 2026-08-02

`docs/plans/REFACTOR-2.4-subpackage-interiors.md`, Phases 6, 7, and 11 — landed as a patch rather
than a minor bump (module-layout reorganization + one facade-closure pass, no public behavior
change beyond what's called out below).

- **Changed** (Phase 6 — facade closure) — closed the `llm`/`agents.interactive`/`tools`/
  `fabric.canonical` package facades (cost math, model identity, provider ABC, routing types,
  router/scope/knowledge, `processors`, `Predicate` all now reachable from their package root
  instead of forcing submodule pins). Made `DbCostRecordStore` and the four LLM providers lazy
  (PEP 562), matching the SDK's `_db` convention — `import jazzx_sdk.llm` no longer pulls
  SQLAlchemy or a vendor SDK unconditionally.
- **Fixed** — an `ImportError` escaping `__getattr__` for a missing optional LLM provider extra,
  which broke `hasattr()`/`dir()` instead of just failing on construction.
- **Added** — status-marker docstrings on five real-but-unexercised surfaces (`llm/routing.py`,
  `evaluation/compounding.py`, `tools/{grounding,tool_compression,dir_tools}.py`, `skills/`), per
  the "capability shipped ahead of demand" convention, so a future audit doesn't mistake staged
  work for dead code.
- **Removed** — `tools/kg_store.py`, a 25-line back-compat shim for symbols already removed in
  1.6.7; its two real tests retargeted at `fabric.graph.triple` directly rather than deleted.
- **Changed** (Phase 7 — `fabric/canonical/store.py` split) — 1,596 LOC of 13 copy-pasted CRUD
  store classes collapsed to a generic `_EntityStore` base plus thin per-type subclasses in a new
  `store/` package (`_base.py`/`core.py`/`derived.py`/`facade.py`). `PolicyStore` kept fully
  bespoke (different method names, its own OData-escaping, a richer collection description) since
  forcing it into the generic shape would have papered over real differences. All 14 public names
  unchanged; verified identical KH call shapes for all 13 types via a recording fake KH client.
- **Changed** (Phase 11 — `tools/` regroup) — `tools/` (24 flat modules, 255 KB) regrouped into
  `documents/` (the document-processing cluster, plus the flat `documents.py`'s local-file half
  now `documents/local.py` and chunking now `documents/chunking.py`), `knowledge_hub/` (ontology,
  policy, knowledge_graph, plus `documents.py`'s KH-callable half), `platform/` (discovery,
  workflow), and `agent/` (grounding, tool_compression, dir_tools). Evicted `financial.py` ->
  `finance/metrics.py` (fixed `finance/__init__.py`'s inverted dependency on `tools/`),
  `filings.py` + `EdgarFallbackSource` -> `finance/filings.py` (untangles conversion.py's routing
  from SEC-specific ingestion), `assessment.py` -> `fabric/assessment.py`. Renamed the private
  `documents._extract_text_from_html` to public `documents/local.py::extract_text_from_html`,
  closing the one real cross-module private-name reach the split surfaced.
  `tools/__init__.py`'s 116-name facade re-exports every moved name unchanged.

## [2.3.0] - 2026-08-02

Split out of what had been accumulating as 2.2.4 — this is everything from the MACER-onto-
`jazzx_sdk.agents` migration prep through the new chassis it enabled, one coherent arc
("generalize the execution mechanism, then build the third chassis on it"). 2.2.4 shipped
separately first with just the original policy/manifest/hooks/SSRF/agent-definition-store bundle.

- **Added** — `jazzx_sdk.agents.ReasoningAgent` (`agents/reasoning/`): a new chassis alongside
  `InteractiveAgent`/`DocumentAgent`, constructor-injected with `AgentExecutionService` like its
  siblings. One primitive serves both a floor (a robust single-shot structured call — retry,
  schema-validation feedback, and truncated-output feedback via `run_kit.run_agent`, none of
  which the existing generic tier or any of the five operational modes have today) and a ceiling
  (the same call with `tools=[...]`, the agentic/batchable shape MACER's migration proved out).
  Resolves models via the SDK's existing shared `resolve_model` — no new retry/model-resolution
  implementation. Design: `docs/plans/design_note_reasoning_substrate.md`.
- **Changed** — All five operational modes (`ReasonerMode`, `InvestigatorMode`, `GovernorMode`,
  `VerifierMode`, `NarratorMode`) now call `ReasoningAgent` instead of `AgentExecutionService`'s
  generic tier, so a schema-validation failure, truncated output, or transient error gets
  retried-with-feedback instead of failing the mode outright. No public constructor/`.run()`
  signature change on any of them; each mode's own short-circuit path (Governor's authority gate,
  Verifier's empty-batch return) is untouched and still bypasses the LLM entirely.
- **Fixed** — `AgentExecutionService.run()`'s generic tier (`OpenAIProvider.run()`) gets the same
  retry/schema-feedback fix for its no-tools, single-message case — the shape every real caller
  uses. `output_type=` now goes straight to the real `Agent`, so a schema mismatch retries with
  feedback instead of a hand-parsed raw string with no correction path. The tool-calling branch
  (no real caller exercises it — `tool_executor` was never wired to anything) and
  `AnthropicProvider.run()` (a fundamentally different, non-Agents-SDK implementation) are out of
  scope, for real architectural reasons, not oversights. Also fixed two confirmed-dead branches
  found along the way: `agent.temperature`/`agent.max_tokens` being set as attributes `Agent`'s
  dataclass doesn't have (silently inert), and empty `result.messages`/`result.tool_calls` reads
  (`RunResult` has neither field).
- **Added** — `Rule.condition`/`Rule.applicability` open onto a registered, pluggable `Condition`
  union (`fabric.canonical.condition_evaluator`) instead of a closed `Union[Expression,
  DslExpression]`: a `ConditionEvaluator` registry (`register_condition_evaluator`/
  `get_condition_evaluator`, mirroring the existing compaction-strategy registry) with three
  built-ins (`ExpressionEvaluator`, `DslEvaluator`, `RatioEvaluator` — the last wrapping
  `tools.ratio_evaluator.evaluate_ratio`, threshold resolved via the existing `profile:<key>`
  convention against a `PolicyProfile` passed through the evaluation context). New `RuleOutcome`
  (`verdict`: closed governance-facing enum, vs `status`: pack-vocabulary string — deliberately
  separate fields) and `EvidenceContract` (what a condition reads, computed statically) types.
  `Rule.applicability` is a new, orthogonal field: a cheap pre-check evaluated before `condition`,
  so an inapplicable rule costs nothing. `DefaultPolicyExpert.check_compliance` now dispatches
  every condition kind through the registry, which also closes a real gap: DSL/ratio conditions
  now participate in cross-policy field-precedence (`fields_claimed`) the same way flat
  `Expression` conditions always have — previously only `Expression` conditions could be claimed/
  skipped by a higher-precedence policy. A discriminated-union `kind` tag (with shape-sniffing
  fallback for pre-P8 dicts with no `kind` key) keeps every existing pack-authored condition —
  Python or YAML — validating unchanged. Also fixed the same closed-`isinstance` gap in
  `PolicyRegistry`'s legacy `policy_clauses` shim, which would otherwise crash constructing a
  registry containing any `RatioCondition` rule. Design: `docs/plans/policy-ir-abstraction.md`.
- **Added** — `jazzx_sdk.conductor.run_replicated_segments` (P1) and `EnsembleCollapse` (P2), the
  segment × replica × regroup topology MACER's `jtbd_runner.py`/`summarization_agent.py` hand-roll
  today. `run_replicated_segments` is built over the existing `fan_out` at both the segment and
  replica level: `precompute` runs once per segment (not once per replica), a caller-supplied
  `key_of` regroups every replica's results explicitly rather than by position, and a failing
  replica is recorded as a `ReplicaFailure` and excluded from the regroup rather than sinking its
  siblings or synthesizing a vote. `EnsembleCollapse` (`DeterministicVote`, `AnyEscalate`,
  `LlmFold`) then folds a regrouped item's votes into one result, deliberately excluding any
  `ReplicaFailure` from the fold — fixing the real bug in MACER's own collapse, where a replica
  that exhausted retries synthesized an `ERROR` vote that still diluted the majority. No registry
  for `EnsembleCollapse` (unlike the P8 `ConditionEvaluator`): a pack picks its collapse strategy
  in code, not from pack-authored data. Design: `docs/plans/reasoner-chassis-analysis.md` §4/P1/P2.
- **Added** — `jazzx_sdk.agents.reasoning.PrecomputedGrounding` (P6): generalizes MACER's
  `guideline_enrichment.py` — parse a corpus into heading-scoped `Snippet`s once
  (`HeadingSnippetExtractor`), cheaply prefilter by keyword overlap (`KeywordPrefilter`, MACER's
  own weighting), select the top few via an LLM shown headings only, never body content
  (`HeadingsOnlySelector`, built on `ReasoningAgent`), and cache the parse by a content fingerprint
  so a corpus change invalidates automatically with no TTL needed (`InMemoryGroundingCache`). The
  non-negotiable part is `BrowseGate`: closes a pack's own list/search tool selectors for the
  duration of the call that consumes the selection, via the same `InvocationContext`/
  `PermissionScope` mechanism `InteractiveAgent._build_parent_tools` already uses — a no-op when no
  `InvocationContext` is ambient, same convention as `admit_hop`. Deny-only, so a direct
  `read_document` a caller wants to keep available (to follow a citation) stays admitted. Every
  part (extractor/prefilter/selector/cache) is swappable; `gate` composes separately since closing
  the door wraps the *consuming* call, not `ground()` itself. Distinct from the existing
  `tools.grounding` (`build_summary_index`/`select_items`): that has no LLM selection step, no
  cache, and no gate. Design: `docs/plans/reasoner-chassis-analysis.md` §2.1/§4/P6.
- **Added** — `"segment_tail"` registered as a named `register_compaction_strategy` entry
  (`jazzx_sdk.agents.interactive.memory.SegmentTailStrategy`), alongside the existing
  `"summarize"`/`"drop"`. Same algorithm `run_kit.strip_session` already applies directly to a
  `SQLiteSession` — user items + the last assistant turn per segment, no LLM call — extracted
  into a shared pure function (`run_kit.segment_tail_items`) so `strip_session` and the new
  strategy can't drift apart. Meaningful for a `ConversationStore` backing a Responses-API/
  agentic session (items carry a `type`); a documented no-op for a plain chat-style history with
  no `type` field. Design: `docs/plans/reasoner-chassis-analysis.md` §4/P5 (half — the other half,
  MACER's `reasoning_group_evict` byte-triggered evictor, is separate, unbuilt work).

Step 2 of the MACER-onto-`jazzx_sdk.agents` migration (a japes-side prerequisite; MACER itself not
touched yet). Prompted by a kernel-vs-japes sweep that led into comparing MACER's own hand-rolled
OpenAI-Agents-SDK code against this module — `run_kit.py`/`models.py` were originally lifted from
MACER's code; this closes the gap that opened since, and modernizes `run_kit.py` onto primitives
that didn't exist when it was lifted (`jazzx_sdk.concurrency.backoff_delay`, `jazzx_sdk.failures`'
structured classification) rather than porting MACER's older shape unchanged. No existing callers
of `run_agent`/`resolve_model` (confirmed) — zero back-compat risk.

- **Added** — `resolve_model()` now handles Gemini and any `litellm/<provider>/<model>`-prefixed
  name via the OpenAI Agents SDK's own generic `LitellmModel` (previously `NotImplementedError` for
  Gemini). Bare Gemini names default to LiteLLM's `gemini/` prefix; Vertex AI's project/location-
  scoped routing needs the explicit `litellm/vertex_ai/<model>` form. Requires the existing
  `litellm` extra.
- **Added** — `run_agent()` gains a fourth retry category, `IncompleteOutputError` (a truncated
  response), alongside `MaxTurnsExceeded`/`ModelBehaviorError`/`APIStatusError` — feeds a "write
  shorter" correction back into the session and retries, mirroring the existing schema-validation
  retry shape.
- **Changed** — `run_agent`'s `on_retry(event, attempt, failure)` now hands the callback a
  `jazzx_sdk.failures.StructuredFailure` (via `classify_failure`) instead of the bare exception —
  one shared failure taxonomy across the model layer (`RetryingModel`) and this run loop, not two
  ad hoc vocabularies. New failure rules registered for the three run-loop-specific exception types
  (mapping `APIStatusError` 429→`RATE_LIMITED`, 408→`TIMEOUT`, else→`PROVIDER_ERROR`, carefully
  scoped to not shadow the existing built-in 401/403/5xx classification).
- **Fixed** — `run_agent`'s own retry backoff was a bespoke, non-jittered exponential formula;
  now uses `jazzx_sdk.concurrency.backoff_delay` + jitter, matching `RetryingModel`'s own formula
  instead of a second, slightly different one.
- **Fixed** — the `ModelBehaviorError` retry branch fed the raw validation-error text back into the
  conversation session verbatim; now passed through `redact_secrets` first, in case the error text
  ever echoes a credential-shaped value from the model's own (rejected) output.
- **Changed** — `on_retry(event, attempt, failure)` gains a fourth positional arg, the raw
  exception, alongside the `StructuredFailure` — a caller wiring its own tracer (e.g. MLflow spans)
  needs the live exception object for `span.record_exception`, which a serializable value type
  can't carry. Upstreamed while doing step 5 of the MACER migration (MACER's `TraceHooks`
  integration is the first real caller). No existing callers besides japes' own tests — zero
  back-compat risk.
- **Changed** — upstreamed MACER's more directive `ModelBehaviorError`/`IncompleteOutputError`
  session-feedback wording (found more effective in MACER's own production use) in place of the
  generic placeholder text.
- **Fixed** — an exhausted `APIStatusError` retry loop re-raised the bare exception with no
  `request_id`; now enriches the message with it (mirroring MACER's own behavior), so a provider
  support ticket has something to reference.
- **Added** — `tests/test_retrying_model.py` (57 tests), ported from MACER's own equivalent file
  while doing step 5 of the migration (delegating MACER's `run_agent` retry loop to this module) —
  MACER's `RetryingModel` was a byte-identical duplicate of this module's own, now replaced there
  with a re-export shim, so its white-box coverage (status-code/header extraction, backoff/jitter,
  orphaned-reasoning-item retry, streaming retry-before/after-yielding) had no remaining home but
  here.
- **Added** — `build_directory_tools()` gained `write_document` (via a new `output_dir` param) and
  a `compress_search_output` hook for `search_documents`, plus `extended_regexp` support (grep
  `-E`) — step 8 of the MACER migration: comparing this factory against MACER's own
  `tools/documents.py` found real capability gaps (not a duplicate, unlike steps 1/3/4), so these
  were upstreamed rather than dismissed. MACER's own tool is unchanged — the gate/enum/settings
  coupling and `read_reference` retrieval tool that go with its own headroom compressor stay
  domain-specific, not moved here.
- **Added** — `tests/test_raw_json_schema_output.py` (16 tests) and
  `tests/test_incomplete_output_detection.py` (9 tests), ported from MACER while doing step 9 of
  the migration (deleting MACER's now-hollowed-out `json_schema_output.py`/`models/retrying.py`
  re-export shims) — both had more thorough coverage of these shared classes
  (`RawJsonSchemaOutput`; `find_incomplete_output_message`/`RetryingModel`'s incomplete-output
  handling) than this module's own existing tests.
- 13 new tests across `test_agent_models.py`/`test_agents_run_kit.py`.

`docs/plans/plan_assistant_ws_fabric_enablement.md` W3 (of W1-W4; W1/W2/W4 not started — real
accumulated open design questions, see `docs/status/status_assistant_ws_fabric_enablement.md`).

- **Added** — `jazzx_sdk.security_context(value)`: a per-turn security-context manager supporting
  both `with` and `async with` (checked directly that a plain `@contextmanager` doesn't support
  `async with` at all, so built as a class implementing both protocols), for a caller dispatching
  many turns on one long-lived task (e.g. a per-session WebSocket worker) where set/clear-in-finally
  would otherwise be hand-rolled per dispatch. Verified concurrent-task isolation directly. 5 tests.

`docs/plans/plan_JAPES_1_9_X_DIRECTORY_BACKED_TOOLS.md` complete. See
`docs/status/done_JAPES_1_9_X_DIRECTORY_BACKED_TOOLS.md`.

- **Added** — `jazzx_sdk.tools.build_directory_tools`/`DirectoryToolSet`: a source-keyed
  `@function_tool` factory (list/read/search over named local directories) for download-then-agent
  solutions, built exactly per the plan's own design. Found and fixed two real bugs the plan itself
  didn't catch: its acceptance tests called `@function_tool`-wrapped tools directly (a
  `FunctionTool` is not callable — fixed by invoking through the real `on_invoke_tool` path), and
  its module-level `agents` import broke the SDK's tier-1/tier-2 "server-free" import boundary
  (`agents` transitively pulls `uvicorn`) — fixed by deferring the import into the factory
  function, matching the lazy-import convention sibling `tools/*.py` files already use. 13 tests.

- **Changed** — `jazzx_sdk`'s root namespace regrouped from 34 flat modules into `observability/`
  and `server/` subpackages plus three targeted moves (`fabric/db/engine.py`,
  `agents/kernel_model.py`, `clients/mocks.py`) — pure module-layout reorganization, no behavior
  or public-symbol change. `tracing.py` (five unrelated concerns in one 1029-line file) split
  along its existing eager/lazy boundary, which is now structural (a lazy module simply isn't
  referenced from any `__init__.py`) rather than hand-maintained. Landed on
  `refactor/sdk-layout-2.3`, not `dev` directly, because macer/jaci/juno run live path installs
  against this working tree. Hardened `tests/test_import_boundary.py` against passing vacuously
  after a module move/rename, and added a `jazzx_sdk.__all__` snapshot test — neither existed
  before. Removed three now-dead back-compat shims (`llm/sanitize.py`, `fabric/pack/__init__.py`,
  `utils/`) after repointing their last real callers, two of them in jaci. Full design/rationale:
  `docs/plans/REFACTOR-2.3-sdk-layout.md` (gitignored).

## [2.2.4] - 2026-08-01

`docs/plans/plan_agent_definition_store_and_facade.md` Part 1 (of 3; Parts 2-3 not started — the
facade needs real design decisions the plan itself leaves open). See
`docs/status/status_agent_definition_store_and_facade.md`.

- **Added** — `jazzx_sdk.agents.AgentDefinition`/`AgentDefinitionStore`/
  `InProcessAgentDefinitionStore`, plus a `fabric.db`-backed `DbAgentDefinitionStore`
  (`jazzx_sdk.agents.definition_store_db`, lazy-imported): a persisted, name-keyed registry of
  agent definitions that can point at either a japes-native `InteractiveAgentSpec` or an opaque
  kernel-hosted agent id — the one real gap identified against kernel's own agent model, everything
  else already having a more general japes-native equivalent. 10 new tests.

`docs/plans/plan_invocation_completion_hooks.md` core mechanism. See
`docs/status/status_invocation_completion_hooks.md` for full detail, including an open decision
(deliberately not made) on whether this should absorb the existing `webhook_url` field.

- **Added** — `MessageHeader.on_complete_hook` (`HookSpec{channel, config}`): a per-invocation,
  caller-selected completion notifier that names any channel `build_channel()` supports (not just
  webhook), delivered via new `jazzx_sdk.channels.notify.deliver_completion_hook` at all three
  entry points that produce a `ResponseMessage` (queue runtime, server `/invoke`, inbound event
  router) — wider coverage than the existing webhook-only, queue-path-only `webhook_url`. A
  failing response's payload carries a `classify_failure`-derived, redacted `{code, message,
  action}` rather than a raw exception string. Best-effort throughout: a bad channel name or a
  failed delivery is logged, never raised into the invocation's own response. 9 new tests.

- **Fixed** — a real, live SSRF gap in `jazzx_sdk.channels.WebhookChannel`: neither the channel
  itself nor `QueueProcessor._deliver_webhook` (the `header.webhook_url` push-notification path
  shipped in 2.2.2) validated the caller-supplied URL before POSTing to it — a caller could point
  japes's own infrastructure at a private/internal address (e.g. a cloud metadata endpoint).
  Found while researching `docs/plans/plan_invocation_completion_hooks.md`'s own explicitly-flagged
  SSRF prerequisite for a *new* hook mechanism, then discovering the identical, already-shipped gap
  in the existing one. Fixed by extracting `read_from_url`'s tested SSRF guard
  (`_is_private_ip`/`_validate_url_safe`) out of `jazzx_sdk/tools/documents.py` into a new shared
  `jazzx_sdk/net_safety.py` (`is_private_ip`/`validate_url_safe`), and calling it from
  `WebhookChannel.send()` before every POST. `documents.py` keeps a thin local
  `_validate_url_safe` aliasing the shared `is_private_ip` so its own existing monkeypatch-based
  test keeps working unchanged. 2 new tests cover a private channel URL and a private per-message
  `target` override, both refused before any request is made.

- **Fixed** — `jazzx_sdk.manifest.spec_binding`'s surface-defaults table had two real deviations
  from its own design, found by checking the plan's own named acceptance tests against what was
  actually implemented rather than trusting that the code existing meant it was correct. (1)
  `stream` was defaulted `True` for `WORKSPACE`/`ASSISTANT`, contradicting the explicit "advisory,
  never default it" rule (`respond_stream()` can't produce structured output) — no surface
  defaults `stream` now. (2) `conversation` was defaulted `True` unconditionally, with no check
  for whether a `ConversationStore` was actually supplied — a spec that reads as memory-enabled
  but isn't, since `InteractiveAgent._conversation_active()` also needs a `session_id` per call.
  `bind_spec()`/`build_from_manifest()` gained a `store=` parameter: `conversation` now defaults
  `True` only when a store is passed through, otherwise it stays `False` with a warning naming
  both requirements. No live consumer of this feature exists yet in either repo, so the corrected
  (safer) default carries zero regression risk to anything already running on it.

- **Added** — `jazzx_sdk.llm.structured.IncompleteOutputError` (a `StructuredOutputError`
  subclass) and `validate(..., truncated=)`: a response cut off at the output token limit is now
  classified distinctly from malformed JSON, so callers stop retrying a truncation with
  "fix your JSON" feedback that can't help. Provider-agnostic — `ProviderResult.truncated` and
  each of the four `llm/providers/*` map their own signal into it (OpenAI `finish_reason ==
  "length"`, Anthropic `stop_reason == "max_tokens"`, Gemini `finish_reason == MAX_TOKENS`, Ollama
  `done_reason == "length"`). Registered with `jazzx_sdk.failures.classify_failure` under a new
  `FailureCode.INCOMPLETE_OUTPUT`, alongside `jazzx_sdk.agents.models.IncompleteOutputError`
  (the pre-existing OpenAI-Agents-SDK-layer equivalent, now classified the same way). Found via a
  survey of a sibling service (macer) that had already fixed the identical misdiagnosis on its own
  Agents-SDK path; this closes the equivalent gap on japes' separate direct-provider-call path.
- **Fixed** — a pre-existing test-isolation bug in `tests/test_failures.py`: `_clear_pack_rules()`
  did a blanket `.clear()` of the shared pack-rule lists instead of removing only the rule(s) the
  test itself added, silently wiping any rule registered permanently at import time by production
  code. Harmless until this change, since nothing previously registered a rule that way. Now
  removes by name.
- `jazzx_sdk.fabric.canonical.policy.PolicyScope` (`institution`/`product`/`deal`) added to the
  canonical `Policy` model; `DefaultPolicyExpert.resolve()`/`check_compliance()` gained an
  optional ephemeral `deal_policy` parameter (never persisted into the registry) so a caller can
  layer a deal-specific override above a program overlay without a pack-side subclass.

## [2.2.3] - 2026-07-30

- **Added** — `jazzx_sdk.authority.context` (plan_JAPES_2_5_0_INVOCATION_AUTHORIZATION.md):
  `InvocationContext`/`PermissionScope`, cascaded per-request authorization checked at every hop
  from an assistant turn to a skill sub-agent to a tool call to a conductor step, rather than each
  hop trusting the last. Canonical-independent: `PermissionScope` (tier one) is always checked; an
  `AuthorityMatrixV2` (tier two) is an additional narrowing layer only when a pack is bound, so a
  plain assistant with no decision classes is still protected. `check_hop`/`admit_hop` delegate to
  the existing `check_action` rather than reimplementing its logic. Propagates across the same
  async-dispatch boundary `capture_identity_headers`/`set_propagated_headers` already solved for
  identity (`ResilientRunner.create_run`/`execute`, `TurnRun.invocation_context`). Opt-in: every
  hop is a no-op when no context is set, so no existing caller's behavior changes.
- **Changed** — `InteractiveAgent`'s turn entry, skill/tool resolution (`_build_parent_tools`),
  and knowledge-binding resolution (`resolve_knowledge`) now check the ambient
  `InvocationContext` when one is set. A skill sub-agent's own tool resolution runs under a
  *narrowed* context (its own declared `tools`/`references` only), so it cannot reach a tool its
  definition didn't declare even if the parent could. A refused skill/tool is excluded from the
  built tool list (least-privilege) rather than surfaced as an in-band tool-call result — see
  `done_JAPES_2_5_0_INVOCATION_AUTHORIZATION.md` for why the plan's literal "returns as a tool
  result" framing wasn't achievable without deeper Agents-SDK internals than this pass takes on.
  `statemachine.engine.apply`/`automation.governed.GovernedAutomation.run` prefer the ambient
  context over their own explicit matrix/actor-class arguments when one is set, falling back
  unchanged when not.
- **Added** — `ProvenanceType.OVERRIDE` (FR-HIL-3): a human-entered correction over a
  promoted-track spread, distinct from `REVIEWER_ENTERED` because an override always supersedes a
  specific existing value.
- **Changed** — `jazzx_sdk.finance.workbook.suggested_action`/`locator_text` promoted from
  module-private to public: a caller's own per-spread exception summary can now render identically
  to the governed workbook's own Exceptions sheet by sharing these two functions instead of
  re-deriving the same text independently.
- **Fixed** — `GovernedWorkbook`'s cell/findings hyperlinks now use an internal `Hyperlink(location=...)`
  reference instead of a plain string assignment, which serialized as an external OOXML
  relationship (`TargetMode="External"`) some readers refuse to navigate. Also fixed the Sources
  and Provenance sheet's own title being clobbered by its header row.
- **Added** — `jazzx_sdk.finance.workbook.GovernedWorkbook`: a layout-driven Excel reporter over
  governed (confidence + provenance + source-coordinate complete) inputs, distinct from the
  existing plain `FinancialSpread`-only exporter. Structural `typing.Protocol` inputs so a
  jaci-defined `SpreadPackage`/`MetricResult`/etc. satisfies it without japes depending on jaci.
  Cell-level notes/tier borders/provenance styling/source hyperlinks (FR-OUT-2), an Inputs sheet +
  live-formula display sheets (FR-OUT-1), and a reported/adjustment/adjusted bridge read straight
  from the engine's own derivation, never recomputed (FR-OUT-3). `WorkbookLayout`/`load_workbook_layout`/
  `default_layout` for pack-authored or package-derived sheet layouts.
- **Fixed** — `jazzx_sdk.finance.excel._write_trends` now carries its analytics-caption line
  (`"Computed in-sheet from the Income Statement..."`), matching jaci's own copy that this
  dedup pass discovered had silently diverged from japes'.
- **Added** — `jazzx_sdk.finance.periods`: assurance attribution and source precedence (FR-SRC-1/2/3).
  `SourceStatement` (a document's account of a period, distinct from the period itself);
  `SourcePrecedencePolicy` on `PolicyProfile` (institution-declared ranking, fail-closed —
  `ASSURANCE_RANK` is never a silent fallback); `resolve_sources` (picks the winning source,
  reports losers, refuses unresolvable ties); `construct_ltm_from_sources` (policy-driven LTM
  beside the existing explicit-component `construct_ltm`, plus FR-SRC-4 findings for a
  lower-assurance interim or stale data). Verified against the PRD's RB profile.
- **Added** — `ProvenanceType` gains `ADJUSTMENT_CANDIDATE`, `APPROVED_ADJUSTMENT`,
  `POLICY_ADJUSTED` (FR-ADJ-3), the candidate/approved distinction for a normalization
  adjustment — used by jaci's `apply_normalization` to refuse a candidate add-back flowing into
  an official/covenant-bound metric.
- **Added** — `jazzx_sdk.manifest.spec_binding.bind_spec`/`build_from_manifest`
  (plan_JAPES_2_4_0_ASSISTANT_MANIFEST_BINDING.md): wires `AssistantManifest` into the interactive
  agent runtime for the first time. `bind_spec` narrows an `InteractiveAgentSpec` by a manifest
  (fails closed on any skill outside `allowed_skills`, applies a per-`SurfaceType` defaults table
  for `conversation`/`stream`/`stream_tool_events`, attaches the new stock scope guardrail).
  `build_from_manifest` resolves `manifest.profile_ref` (new field, falls back to `assistant_id`)
  against a `ProfileRegistry` and builds a running `InteractiveAgent` in one call.
- **Added** — `jazzx_sdk.agents.interactive.scope.build_scope_guardrail`: turns a manifest's
  `in_scope_action_classes`/`out_of_scope_action_classes` into a real gate (a deterministic
  keyword match against declared out-of-scope classes, returning a typed `Refusal` with
  `RefusalClass.OUT_OF_SCOPE`) instead of `with_safety`'s advisory prompt text.
- **Added** — `InteractiveAgentSpec.router` (default `"default_llm"`, resolved at wire time —
  same pattern as `CompactionPolicy.strategy`): names the agentic path's skill pre-selection
  policy. `jazzx_sdk.agents.interactive.router`: `default_llm` (today's behavior, no-op),
  `intent_first` (a one-call classifier narrowing the exposed sub-agent tools for a turn, `None`
  on low confidence).
- **Changed** — `InteractiveAgent._run_guardrails` accepts a typed `Refusal` return from a
  guardrail check (alongside the existing bare-string contract): `Refusal.message` surfaces as
  before, and the full object is retrievable via the new `agent.last_guardrail_refusal`.

## [2.2.2] - 2026-07-28

- **Fixed** — Caller identity no longer silently drops across the queue/async-dispatch task
  boundary. `jazzx_sdk.runs.ResilientRunner.create_run` now captures the submitting caller's
  identity headers (`capture_identity_headers`, new); `execute` restores them
  (`set_propagated_headers`/`clear_propagated_headers`, new) around the dispatched turn, so every
  downstream KH/kernel call the turn makes forwards the right caller even when drained by a
  different async task or worker than the one that created it. `default_request_headers` and the
  `get_current_user_id/email/name` accessors both fall back to the restored set — outbound headers
  and identity-attribution code stay consistent. Root-caused from a corroborated cross-repo pattern
  (juno #242 hit this live).
- **Added** — Webhook push notification for queue-based invocations. `MessageHeader.webhook_url`
  (+ optional `webhook_secret`) opts an invocation into a push notification on completion —
  `QueueProcessor.send_response` delivers it via `jazzx_sdk.channels.WebhookChannel` (retry + HMAC
  signing), additive to the response queue, never a substitute for it. A caller that previously had
  to hand-roll delivery, idempotency, and retry itself (assistant's own webhook deliverer had
  neither) now gets both for free from `build_invocation(webhook_url=...)`.
- **Added** — `ScorerResult.skipped` — a scorer can now report "not applicable to this case"
  (e.g. groundedness with no retrieval context) distinct from a failure. `CompositeScorer` and the
  built-in adjudication policies (`all_pass`/`any_pass`/`k_of_n`/`weighted_threshold`) exclude
  skipped sub-results from their pass/score aggregation and required-scorer veto, and propagate
  `skipped=True` themselves when every sub-result skipped, so a skip never shrinks an achievable
  pass rate or counts as a failure.

## [2.2.1] - 2026-07-27

- **Added** — `jazzx_sdk.clients.EvalServiceClient` (Phase 2 of `plan_JAPES_2_3_0_GUIDANCE_
  INJECTION_HOOK.md`): a general-purpose, best-effort read client for eval-service's feedback
  endpoints (`get_feedback_config`, `find_similar`), generalizing jazzx-assistant PR #6's own copy
  to platform level so a third consumer never reimplements it a third time (kernel has one, PR #6
  built a second). Every httpx/JSON error degrades to `None`/`[]`, never raises;
  `httpx.MockTransport`-testable, no generated client to wrap (eval-service ships none).
- **Added** — Phase 1 of `plan_JAPES_2_3_0_GUIDANCE_INJECTION_HOOK.md`: `InteractiveAgent`
  now applies `jazzx_sdk.fabric.guidance` at turn time — the runtime hook that plan's own design
  doc (`done_JAPES_GOVERNED_GUIDANCE_ASSETS.md`) explicitly deferred. New
  `InteractiveAgentSpec.guidance_pack_id`/`guidance_applicability` (both additive, default off — no
  `fabric.guidance` call is attempted at all unless `guidance_pack_id` is set, so every existing
  spec is unchanged, not just "empty guidance"). `respond()`/`respond_stream()` retrieve deployed,
  applicable guidance, append the confidence-grouped rendered block to the system prompt after
  grounding context, and return the applied `GuidanceRef`s on the new
  `InteractiveResponse.guidance_refs` for a caller to attach to its own `CanonicalDecision` (making
  Guidance Effectiveness, IIF Schema Spec §10.4, computable). Mirrors `_ground`'s exact posture: a
  spec declaring `guidance_pack_id` with no fabric raises (real misconfiguration); a fabric present
  with no configured guidance store returns empty (a valid, unconfigured state). Phase 4
  (end-to-end proof) remains open.
- **Added** — `jazzx_sdk.fabric.guidance.eval_service_store.EvalServiceGuidanceStore` (Phase 3 of
  `plan_JAPES_2_3_0_GUIDANCE_INJECTION_HOOK.md`): adapts `EvalServiceClient`'s retrieval into the
  same `GuidanceStore` seam `fabric.guidance` exposes everywhere else — `search()` only;
  `put`/`get`/`versions`/`list` raise `NotImplementedError` naming the store read-only by design
  (eval-service-sourced feedback is authored/reviewed in eval-service's own UI, not through japes's
  lifecycle). `FabricConfig.guidance_backend` (`"rag"` default / `"eval_service"` / `"none"`) +
  `eval_service_url` (env `JAPES_EVAL_SERVICE_URL`) select the backend; misconfiguring
  `"eval_service"` without a URL raises at construction time. Backend selection is independent of
  whether a KH client is configured, since eval-service needs no KH backing at all.
- **Added** — Phase 4 (final) of `done_JAPES_2_3_0_GUIDANCE_INJECTION_HOOK.md`: an end-to-end test
  proving `InteractiveAgent.respond()` applies guidance sourced from a mocked eval-service transport
  (via `EvalServiceGuidanceStore`) exactly as it already did for `InProcessGuidanceStore` — the
  rendered guidance block reaches the actual prompt sent to the LLM, and `guidance_refs` names the
  eval-service feedback item's synthesized asset id. Closes the plan: governance-side rendering/refs
  now proven identical across both `GuidanceStore` backends, not just the in-process reference one.
- **Added** — `MetricDefinition.display_method: str = ""` (plan_JACI_CL_CHART_OF_ACCOUNTS_AND_
  CATALOG.md Phase 3) — a human display label for how a formula combines its inputs (e.g.
  `"ratio"`/`"percent"`/`"sum"`), display metadata only, never interpreted by the evaluator.
  Replaces a pack's own module-level id-to-label dict for this purpose.
- **Added** — `jazzx_sdk.finance.vocabulary` (plan_JAPES_2_2_0_LINE_VOCABULARY.md, Phases 1-2):
  `LineVocabulary`/`LineDefinition`/`Recognition` — a pack's declared, versioned chart-of-accounts
  vocabulary (the SDK ships none; three private alias-list copies already exist in JACI alone,
  none of which are enforced to agree), and `resolve()` — matches a raw (key, label) pair against
  it, returning a `Resolution` naming the exact `MatchKind` (`exact_key`/`alias_key`/`exact_label`/
  `normalized_label`/`substring`/`unmatched`) and matched term. Substring matching is opt-in per
  line, never a global fallback; two lines matching at the same strength resolve to `unmatched`
  naming both, rather than silently picking the first.
- **Added** — Phase 3 of `LINE_VOCABULARY`: `structure_statement(..., vocabulary=...)` — when
  supplied, the extraction prompt carries the statement type's closed set of canonical keys
  instead of letting the model invent one, with an explicit escape (null key, label kept) when
  nothing fits. A key the model returns anyway that still doesn't resolve is never silently
  accepted — nulled and recorded in the new `StructuredStatement.vocabulary_gaps`
  (`VocabularyGap`). The vocabulary also populates each line's `SpreadLine.semantics`. Omitting
  `vocabulary` leaves behavior exactly as before.
- **Added** — Phase 4: `ResolutionContext.vocabulary` — a `SCOA_LINE`/`DOCUMENT_FIELD` binding's
  canonical `ref` now resolves through a supplied `LineVocabulary` rather than requiring `lines`
  to already be keyed by that ref, letting a caller's private candidate map be deleted rather than
  moved. Proved by rewriting JACI's `dsl_catalog.py` to use a vocabulary instead of its own
  `_CANDIDATES` dict — the existing sixteen-case parametrized fixture (`test_metric_result.py`)
  still passes byte-identical. `None` (default): no behavior change. `LINE_VOCABULARY` is now
  fully landed (all 4 phases).
- **Fixed** — `LineVocabulary`'s duplicate-key/-alias validator now scopes alias uniqueness *per
  statement type* rather than globally (canonical keys themselves stay globally unique, since
  `by_key()` has no statement type to disambiguate). Found while authoring JACI's real chart of
  accounts: the same raw term legitimately means different things in different statements (e.g.
  `accounts_receivable` as a balance-sheet balance vs. a cash-flow change-in-AR line) — the
  original global check would have wrongly rejected that as a collision.
- **Fixed** — `SpreadLine.semantics: LineSemantics | None` — the flow/stock override from Phase 2
  of the period-model work now lives on the line itself, not only as a `construct_ltm(...,
  line_semantics=...)` call-time dict. A durable per-line correction (e.g. a balance-sheet memo
  line that's actually a flow amount) shouldn't depend on every caller remembering to pass the
  override at call time. `_semantics_for()` checks the call-time dict first (for a one-off
  override a caller doesn't control the line data for), then the line's own `semantics`, then the
  per-statement-type default — additive, no existing behavior changes.

## [2.2.0] - 2026-07-26

- **Added** — `jazzx_sdk.finance.periods` (Financial Spreading PRD v0.4 §7.6, FR-PER): `Period`
  (identity = date range + kind, not the display label) and `PeriodSet` (aligns periods across
  differing fiscal calendars onto one timeline); `LineSemantics` (flow/stock, defaulted per
  `StatementType`, overridable per line); `Assurance` (audited/reviewed/compiled/tax/
  company_prepared/internal_interim/management_schedule/derived, ordered to match FR-SRC-2's
  default source-precedence hierarchy) + `ASSURANCE_RANK`; `construct_ltm()` (flow lines by
  addition of the current interim + the prior year's non-overlapping tail, stock lines at the most
  recent period-end, never a roll-forward) with typed `Refusal` guardrails (mismatched fiscal
  cutoff, unequal interim lengths, missing prior-year interim — never fabricated). Verified against
  the PRD's real Appendix D worked example (RB LTM Sept-2023): Revenue 57,581 + (61,443 - 44,326) =
  74,698, computed exactly; a permanent regression test (FR-PER-6) guards against ever
  transcribing the reference workbook's incorrectly-signed human note instead of the verified
  (and different) formula. `FinancialSpread.period_set` added alongside the existing
  `periods: list[str]` — additive, no existing caller (JACI's `analytics.py`/`template.py`/
  Streamlit views/Excel export) changes; verified against JACI's full test suite with zero JACI
  changes.
- **Added** — `jazzx_sdk.expressions` (Financial Spreading PRD v0.4 §7.7, FR-CUS): `MetricDefinition`/
  `InputBinding`/`BindingKind` (assumptions are a distinct binding kind per FR-CUS-6 — an assumed
  input can never render as a reported figure); `parse()` — a small hand-written recursive-descent
  grammar, not `eval()` (arithmetic, multi-period refs `prior`/`ltm`/`avg`/`cagr`, lazily-evaluated
  `if`/`min`/`max`/`cap`, cross-entity aggregation left as an explicit refusal stub); `evaluate()` —
  a governed `MetricResult` with full input/derivation provenance and weakest-input confidence,
  typed `Refusal`s (never `None`/silent-zero) for a missing required input, below-floor confidence,
  or division by zero; `validate()` — undefined references, unit mismatches, unreachable
  conditional branches, and circular metric references (DFS over the `CUSTOM_METRIC` graph), all
  checked before the evaluator ever runs (FR-CUS-10). Verified against the PRD's real Appendix B
  worked example (Adjusted Fixed Charge Coverage: `6.67`) and the two named grammar cases (FR-ADJ-4
  conditional bad-debt addback; FR-ADJ-6 owner-comp capped at policy limit).
- **Changed** — the canonical `Policy`/`Rule` condition type widened from `Expression` alone to
  `Optional[Union[Expression, DslExpression]]` (new `jazzx_sdk.fabric.canonical.DslExpression`, a
  DSL-authored boolean formula over context fields), so a policy rule can now express compound
  conditions (`leverage_x <= 3.5 OR covenant_waived == 1`) that don't fit a single flat
  field/operator/value triple. Evaluated via a new, separate `evaluate_over_namespace()` — a
  lightweight AST walk over a flat `{field: value}` dict, distinct from the full
  `MetricDefinition`/`ResolutionContext` machinery, since a policy condition reads context fields
  directly rather than resolving chart-of-accounts bindings. `DefaultPolicyExpert.check_compliance()`
  and `PolicyRegistry`'s backward-compat clause shim both branch on the condition's type; the
  existing flat-`Expression` path is byte-for-byte unchanged. Additive — every existing
  flat-`Expression` policy in JACI's AML, KYC, and C&I registries loads and evaluates identically
  (verified against JACI's full test suite with zero JACI changes).

## [2.1.5] - 2026-07-26

- **Fixed** — `_html_to_markdown` (pandoc path) and `_extract_text_from_html` (fallback path) let
  hidden HTML content (`style="display:none"`, `visibility:hidden`, the `hidden` attribute) leak
  into "faithful" conversion output — e.g. a SEC 10-K's inline-XBRL fact block, which filers wrap
  in a hidden `<div>` at the top of the body: raw taxonomy references and context IDs with no
  reader-visible content, dumped ahead of the actual statements. New shared
  `documents.strip_hidden_elements(soup)` removes it via a real parser (a regex can't reliably
  balance nested divs); extends the existing `<script>`/`<style>`-stripping precedent rather than
  contradicting the "never drop content" faithful-conversion contract — hidden content is
  presentational plumbing a reader never sees, not narrative text. Verified against a real 10-K:
  every one of 755 real financial figures preserved identically; only the hidden XBRL block and
  empty hidden spacer `<td>`s were removed.
- **Added** — `AzureDocIntelligenceProvider.convert_to_json()` / `analyze_result_to_json()` — a
  page-structured JSON view (role-classified paragraphs, raw table cells) alongside the existing
  markdown transform, sharing the same `analyze()` call. `DocumentIntelligenceProvider` gained an
  optional `convert_to_json()` (default: unsupported); `LocalStubProvider` (renamed from
  `LocalMarkdownStubProvider`, now that it stubs both formats) mirrors it with a co-located
  `<stem>.json` stub. Every page has a stable schema (fields always present, never conditionally
  omitted), unlike kernel's v1 dynamic-shape equivalent.
- **Added** — `jazzx_sdk.tools.extraction.locate_regions_from_json` / `ExtractionTemplate.locate_json`
  / `flatten_table_from_json` — JSON-sourced counterparts to the markdown/HTML region+table locators,
  for a document converted via `analyze_result_to_json()` (DocIntel/scanned fallback) instead of
  markdown: table-mode anchors read Azure's real table cells directly (a markdown rendering has no
  `<table>` tags for the HTML-based locator to find), and window-mode search reuses the existing
  text-window logic over a plain-text flattening of the JSON. Same anchors/templates work with either
  locator.
- **Fixed** — `DocumentAgent`'s per-field grounding check (`_grounded`) treated every whole-number
  float as ungrounded: `str(1000.0)` is `"1000.0"`, and digit-stripping the `.` left a spurious extra
  digit (`"10000"`) that could never match the source's real digit run (`"1,000"` → `"1000"`) —
  silently capping confidence below the admission floor and refusing the value. Financial figures are
  commonly whole numbers, so this was a systemic false-refusal risk for exactly the kind of data
  `DocumentAgent` is meant to extract with confidence.
- **Added** — the document pipeline (`agents.document.pipeline`) gained a `collection` route alongside
  `single`/`package`/`refuse`, fanning out via `DocumentAgent.process_dir`: a folder of documents
  (`DocTurn.folder_path`), a whole Knowledge Hub collection (`collection_id`, synced into `folder_path`
  first via `process_dir`'s existing sync), or a standalone zip archive (`file_path` ending `.zip`,
  unpacked into a scratch dir under `work_dir` first). No custom `detect()` needed for any of the three
  — the route is inferred from which `DocTurn` fields are populated; a custom `detect()` is only for
  package-vs-single on a combined single file, which can't be inferred from shape alone.
  `agent.py::_unpack_zip` renamed to `unpack_zip` (now shared with the pipeline's zip-unpack case).
  `DocTurn.degrade` changed to `bool | None = None` — a real bug caught before it shipped: forwarding a
  shared `False` default to both routes silently overrode `process_dir`'s own better default (`True`,
  one bad file in a folder shouldn't sink the batch) with `process_package`'s (`False`, a bad segment
  does call the whole combined document into question) whenever a `DocTurn` didn't set `degrade`
  explicitly. `None` now means "let the underlying `DocumentAgent` method's own default stand."

## [2.1.4] - 2026-07-25

- **Fixed** — `KnowledgeHubClient.create_document()` and `.upload_ontology()` (both file-upload
  methods) no longer rely on the generated client's own `Body*.to_multipart()`, which regressed for
  *every* binary-file-upload endpoint on `client-api@main` (commit `4bcf1f4` / PR #61, unfixed as of
  2026-07-25 — confirmed on both `BodyUploadBinaryDocument` and `BodyUploadOntology`): it stopped
  calling `File.to_tuple()` and instead sends `str(File(...)).encode()` — a Python repr of the wrapper
  object, not the real bytes. A small upload "succeeded" with the repr string stored instead of the
  actual content; a larger one 400'd (`"Part exceeded maximum size of 1024KB"`) once the
  ~3-4x-inflated repr crossed the multipart part-size limit. Both methods now build the multipart
  payload themselves via one shared, tested primitive (`_MultipartBody`), independent of whichever
  commit of the generated client is installed.
- **Changed** — `kernel-client`/`knowledge-hub-client` pinned to a fixed commit (`rev=`) instead of
  tracking `client-api@main` (`branch=`); `knowledge-hub-client` specifically pinned to the last commit
  confirmed *before* the regression above, so a future `poetry lock`/`poetry update` on it can't
  silently reintroduce the bug the way tracking `main` would.
- **Changed** — `fabric.graph.upload_ontology` renamed to `register_ontology_from_files` — pairs with
  the existing `register_ontology` (same underlying concept — both `create_ontology`/`upload_ontology`
  return the same `OntologyRead` shape server-side — sourced from raw file bytes instead of an
  already-parsed string/dict) rather than mirroring the KH client method's name verbatim.
  `_from_files` (not `_files`) deliberately: "register_ontology_files" reads as "register the files";
  the qualifier needs to mark *how*, not *what*. No consumer used the old name.
- **Added** — `agents.interactive.redact_before(guardrail, redact)`: wraps any `Guardrail` (an LLM
  classifier or a plain check) so it runs against redacted text instead of the raw text — for a
  leak-detection guardrail that can't reliably tell "known-safe content, already delivered elsewhere"
  apart from an actual leak, and shouldn't be asked to via a prompt instruction alone (a
  non-deterministic judgment call). Composes with `jazzx_sdk.failures.redact_secrets` (existing),
  the two new redaction utilities below, or a caller's own `str -> str` function.
- **Added** — `jazzx_sdk.failures.redact_code_blocks(text, suspicious_markers=, placeholder=)`: masks
  every fenced code block in `text`, so a legitimate reply containing generated code doesn't trip a
  classifier's "framing text + adjacent code block" leak heuristic. A block containing a
  `suspicious_markers` substring is left unredacted (a safety net — real leaked content must still
  reach whatever scans the text next).
- **Added** — `jazzx_sdk.failures.redact_fields(payload, paths, suspicious_markers=, placeholder=)`:
  the structured-payload counterpart — redacts known-safe string fields at dot-paths into a nested
  dict/mapping (copy-on-write; same suspicious-markers safety net), for content delivered to a caller
  through another channel already (e.g. generated code also handed to a UI's Apply button via a
  separate field) before it's serialized into text a guardrail or an LLM's context will see.
- **Added** — `modes.evolve.synthesize_bucket(signals, llm=, pack_id=, store=)`: the Curator's Layer 2
  synthesis (previously a `NotImplementedError` stub) — LLM-deduplicates a batch of same-tag
  `ImprovementSignal`s into one draft `GuidanceAsset`, persisted at `GuidanceStatus.DRAFT` for SME
  review via `GuidanceLifecycle`. Takes the universal `ImprovementSignal` shape, so it works the same
  whether signals came from eval-report routing or straight from `Feedback.to_signal()` (a red-teaming
  or in-context-correction batch). `ImprovementSignal` gained `feedback_id` so that provenance survives
  from `Feedback` through to the synthesized asset's `provenance.feedback_id`/`metadata.feedback_ids`.

## [2.1.3] - 2026-07-24

- **Fixed** — `KernelClient.invoke_agent()` imported names that don't match the current generated client; rewritten against the real contract (agent-name resolution, typed `messages`, async invoke-then-poll, response fetch). `session_id` is accepted but now a documented no-op (kernel has no server-side session concept on this endpoint).
- **Added** — `DocumentAgent.process_dir(on_progress=...)`: per-file progress callback for folder batch runs (the conductor-wrapped single-document path already streamed via `on_step`; the batch entry point had no equivalent). Best-effort — an observer error is logged, never breaks the batch.
- **Added** — `DocumentAgent.process_dir` now classifies per-file failures via `jazzx_sdk.failures.classify_failure`; `DirectoryResult.failures` (filename -> `StructuredFailure`) alongside the existing `failed` list, and the failure detail is persisted in `manifest.json` for later inspection.
- **Changed** — `kernel-client`'s git pin bumped to `client-api@main`'s current tip; no code changes needed (the shapes `invoke_agent()` was already written against are unchanged at the new commit).
- **Added** — `KnowledgeHubClient.get_document_metadata()` / `fabric.docs.DocStore.get_metadata()`: fetch a document's metadata (created_at/updated_at/doc_type/size_bytes/sha256/user metadata) without downloading its content. Wraps KH's dedicated `get_document_metadata` endpoint (already used by kernel's own agent tool of the same purpose), lighter than `get_document()`.
- **Added** — `DocStore.materialize()` is now idempotent across interrupted/repeated runs, when the KH client supports `get_document_metadata` (feature-detected; unaffected otherwise). Each doc's current hash (sha256, falling back to `updated_at`) is checked against a small manifest before downloading — unchanged docs with their target file still on disk are skipped. `materialize()` also gained `binary=True` (writes raw bytes instead of decoding as text — needed for PDFs/DOCX).
- **Added** — `DocStore.sync_collection(collection_id, output_dir)`: the collection-level counterpart to `materialize()` — lists a KH collection and syncs every document to `output_dir` by name, idempotently (same manifest-based skip). `DocumentAgent.process_dir(collection_id=...)` uses it to source a folder run's inputs from a KH collection instead of (or in addition to) whatever's already local; requires `docs=` (a `DocStore`) passed to `DocumentAgent()`.
- **Added** — `DbMaterializeManifestStore` (`fabric.docs.manifest_store_db`): persists `materialize()`/`sync_collection()`'s doc-hash manifest in `fabric.db` instead of a local file, keyed by a caller-chosen `scope` (defaults to `collection_id` for `sync_collection`) instead of the local `output_dir` path. Note: this survives a manifest lookup across a fresh `output_dir`, but a doc whose local file is actually gone (e.g. an ACA Job's per-execution `/tmp`, wiped between retries) is still re-downloaded — a hash match can't substitute for bytes that are no longer on disk. No new "japes db" needed: this reuses the same fabric.db pattern as `DbTurnRunStore`/`DbSuspensionStore` (japes owns a small SQLAlchemy table; the consuming service's alembic — or `fabric.db.create_all()` in dev/test — creates it).

## [2.1.2] - 2026-07-21

- **Fixed** — `HandlerContext.job_id` was the queue transport id in queue mode, the business id elsewhere; unified via `job_id_for()`. Transport id moved to `queue_message_id`.
- **Fixed** — inbound `traceparent` was never attached to the active OTel context; `attach_incoming_trace_context` now does, at all three entry points.
- **Fixed** — outbound calls never propagated the active trace; `inject_current_trace_context` closes it via `default_request_headers()`.
- **Fixed** — trace propagation was entangled with the kernel identity allowlist; decoupled via `with_trace_context`.
- **Added** — `KernelClient.request_headers_provider` (PAGI-1612 allowlist), matching `KnowledgeHubClient`.
- **Added** — `KnowledgeHubClient.create_entity_v2` / `read_entities_v2` for KH's v2 entity API.
- **Fixed** — `pillow` >=12.3.0: clears 13 Dependabot alerts (transitive via `matplotlib`).
- **Fixed** — `ConductorEngine.resume()` was reusable; a `Suspension` is now single-use (rejects a second resume).
- **Fixed** — a stalled `on_step` observer could block a conductor step indefinitely; now bounded by `on_step_timeout`.
- **Fixed** — `fan_out` left siblings running after a failure; now cancels and drains them before propagating.
- **Added** — `ConductorEngine.resume_durable` + `SuspensionStore`/`InProcessSuspensionStore`/`DbSuspensionStore`: an atomic-claim durable resume path for HITL suspensions across processes (non-BPMN case).
- **Added** — `timeout` on `run_offloaded`/`best_effort`/`BestEffortBackend._offload`/`_best_effort`/`_background`: a stalled backend call degrades/raises after the bound instead of hanging the caller forever. Opt-in (`None` default preserves prior behavior).
- **Changed** — `DbTurnRunStore`/`DbSuspensionStore`'s duplicated `FOR UPDATE SKIP LOCKED` + sqlite-fallback logic factored into `fabric.db.locking.skip_locked_first`/`skip_locked_all`; no behavior change.
- **Fixed** — `KernelClient` had no connection-pool cap (inherited httpx's default 100 max connections); now defaults to 20/10, matching `KnowledgeHubClient`, with an overridable `limits=` param.
- **Fixed** — a slow claimer's late `heartbeat`/`mark_resumed`/`mark_failed` could silently resurrect a `TurnRun`/`Suspension` already reaped to `FAILED` (claim_token survives reap; only status changes) — a lost-update under unlocked read-then-write. All four stores (`InProcessTurnRunStore`, `DbTurnRunStore`, `InProcessSuspensionStore`, `DbSuspensionStore`) now fence on terminal status too, and the DB stores read-modify-write under a blocking row lock (`fabric.db.locking.blocking_locked_first`/`_all`).
- **Added** — `flush_mlflow_async_trace_queue()`: drains MLflow's async trace-export queue and pins `MLFLOW_HTTP_REQUEST_TIMEOUT` before a worker process exits, so a recycled Celery worker doesn't drop buffered spans (traces stuck "in-progress" with no data).
- **Added** — `MessageHeader.session_id`: a dedicated conversation-stable key for handler memory-keying, distinct from `correlation_key` (which stays request-unique). `correlation_key`'s docstring no longer recommends repurposing it for this.
- **Added** — `JapesQueueClient`: the producer-side counterpart to `QueueProcessor` — `enqueue_invocation` + `await_response` for a caller that invokes japes over the queue and waits for the correlated reply, instead of hand-rolling a response-queue poll loop.
- **Added** — `jazzx_sdk.failures`: `classify_failure`/`StructuredFailure`/`FailureCode` (type-based classification with a regex fallback, pack-extensible via `register_failure_rule`) and `redact_secrets`. Wired into `CaseResult`/`ExperimentRun`/`EvaluationHarness` so a failed eval run carries a structured code/message/action, not just a raw string. `mlflow_bridge`'s sensitive-key list now sources from the same `SENSITIVE_KEY_NAMES`.
- **Fixed** — `gitpython` >=3.1.52, `pyasn1` >=0.6.4, `setuptools` >=83.0.0: clears the remaining 7 open Dependabot alerts (env-var exfiltration, git-option command injection, ASN.1 resource exhaustion, sdist exclusion bypass; all transitive).

## [2.1.1] - 2026-07-20

- **Added** — **feedback on interactive-agent turns** — `InteractiveResponse` now carries the turn identity (`conversation_id` / `message_id` / `trace_id`), stamped on every reply by `respond`/`respond_stream` (both gained optional `conversation_id`/`trace_id` args; `conversation_id` defaults to `session_id`). `response.feedback(reaction=…, rating=…, text=…)` builds a `Feedback` linked to that exact turn — so a chat UI can wire thumbs/ratings/corrections into the feedback→trace→learning spine in one line, instead of hand-threading identifiers.
- **Added** — **human-in-the-loop suspend/resume in the conductor** — a step can `raise SuspendRun(key, reason=, payload=)` to pause a run and hand off to a human (e.g. an SME approving a flagged spread). `ConductorEngine.run()` returns a `ConductorRun` with `status == "suspended"` and a `Suspension` (the payload to show the approver + the captured run state); `engine.resume(suspension, resolution)` continues from the next step with the decision injected as the suspended step's output (a downstream step can `state.halt` on rejection). In-process by default; the `Suspension` is persistable for cross-restart resume. Suspend is supported for top-level steps (raising inside a loop is rejected with a clear error).
- **Added** — **DOCX + ZIP intake** — `convert_document` now handles `.docx` (pandoc → table-preserving markdown, `python-docx` fallback). `DocumentAgent.process_dir(..., include_zips=True)` unpacks any `*.zip` container into `output_dir/_unpacked/<stem>/` and processes its `pattern`-matching contents recursively (unpacking is incremental on the zip's content hash; unpacked files are keyed `<stem>/<relative path>`). Closes the plan's PDF/DOCX/ZIP input requirement.
- **Added** — **structure-aware chunking** — `chunk_by_headings` splits a large untemplated doc along its markdown heading tree (chapters/sections/sub-sections — what a table of contents renders) instead of arbitrary character windows, so a chunk is a coherent unit (a statement stays with its heading). It keeps whole sections together, descends into sub-sections only when a section alone exceeds the budget, and falls back to character slicing for heading-less spans (offset-based → chunks concatenate back to the original). It's now the default chunker for `extract(..., chunk_chars=…)`; `chunker=` accepts `_chunk_by_chars` or any `(text, max_chars) -> list[str]`.
- **Added** — **package completeness check** — `check_completeness(results, required, min_confidence=…)` → `CompletenessReport` reconciles the doc types `process_dir` found against a required-doc-type checklist: `present` / `missing` / `unexpected`, plus `by_type` (which files satisfy each type) and `is_complete`. The "is this loan package complete?" gate for a classified folder (Stage 1).
- **Added** — **document pipeline: incremental folder ingestion + chunked untemplated extraction** — the raw-folder-of-PDFs flow. `DocumentAgent.process_dir(folder, pattern="*.pdf", output_dir=".japes", …)` lists a directory and processes each file (per-file tracer span, bounded concurrency), writing the `<stem>.md` conversion + `<stem>.result.json` + a `manifest.json` under `output_dir`. A `<stem>.md` already staged in `output_dir` (e.g. copied from blob) is **reused** as the conversion, skipping DocIntel/OCR. **Incremental/resumable**: a file whose content hash still matches a `complete` manifest entry is skipped; a new/overwritten (changed-hash)/previously-failed file is (re)processed — the manifest is a recreatable content-hash cache (losing it costs redo, not information). Classify-only by default (identify a folder's docs) or extract each with a shared `schema`; returns a `DirectoryResult` (processed/skipped/failed). And `extract(..., chunk_chars=…)` (also `DocumentAgentSpec.chunk_chars`) chunks a large *untemplated* readable doc, extracts each chunk, and merges field-wise — so a big doc without a template no longer overflows the model context (the templated path already narrows to located regions).
- **Added** — **feedback→trace→learning spine**: `Feedback` now carries the chat-turn linkage (`conversation_id` / `message_id`, alongside the existing `trace_id`), with `Feedback.for_turn(...)` to capture it and `FeedbackStore.list(conversation_id=/message_id=/trace_id=)` (in-process + `fabric.db`, indexed) to retrieve a turn's or conversation's feedback. Closes the gap between per-turn feedback and the run that produced it: capture (linked to the run's conv/message/trace tags) → query → `synthesize_cases_from_feedback` → `optimize_prompt`, and `Feedback.trace_id` resolves to the full trace via `TraceSource`.
- **Added** — **versioned invocation contract + boundary tests**: the queue envelope now carries a canonical `INVOCATION_CONTRACT_VERSION` (single source on `MessageHeader.version` / `build_invocation`), `models.py` documents the contract (envelope, correlation-key semantics, identity/security-context, distributed tracing, forward-compat), and `tests/test_invocation_contract.py` freezes the wire shape — a dropped/renamed field, a version bump, or correlation-key churn now fails a test instead of drifting silently across producer/consumer versions. Unknown fields are tolerated on parse (a newer producer never breaks an older consumer).
- **Added** — **groundedness guardrail + shared safety fragment** (`agents.interactive`): `grounded_guardrail(llm, get_context=…)` — an output guardrail that blocks an answer making claims its grounding context doesn't support (the "don't let an ungrounded/hallucinated answer reach the user" gate; passes when there's no context to check). And `with_safety(instructions)` / `SAFETY_INSTRUCTIONS` — the domain-neutral no-invention / retrieved-content-is-data injection-defense / no-bias-or-steering / stay-in-scope prose, authored once and composed into a skill's instructions instead of copy-pasted per skill.
- **Changed** — **env-var naming consolidated** onto the `JAPES_`-preferred convention via one resolver (`jazzx_sdk.env.env(*names, default=)` — first name set wins). Every japes-owned config var now accepts a `JAPES_`-prefixed name (preferred) with its legacy name as a back-compat fallback: fabric KG defaults (`JAPES_KH_COLLECTION_ID | KH_COLLECTION_ID`, `JAPES_KH_ONTOLOGY_ID`, `JAPES_FABRIC_MODE | FABRIC_MODE`), fabric persistence (`JAPES_CONVERSATION_BACKEND | JAZZX_CONVERSATION_BACKEND`, `JAPES_DB_BACKEND | JAZZX_DB_BACKEND`, `…_DB_SQLITE_PATH`, `…_BLOB_BACKEND`, `…_BLOB_CONTAINER`), KH URL/token/user/security-context, `JAPES_MOCK_KH_DATA_DIR`, `JAPES_PROCESS_ENGINE_BASE_URL`, and the Azure storage vars. Existing (bare / `JAZZX_` / `AZURE_`) names keep working. Vendor/ecosystem-standard vars (`OPENAI_API_KEY`, `OTEL_*`, `AZURE_DOCUMENT_INTELLIGENCE_*`, `DATABASE_URL`, …) are deliberately left un-prefixed. Scattered `os.getenv("JAPES_X") or os.getenv("X")` chains routed through the resolver; `.env.template` + README reflect the canonical names.
- **Fixed** — **`.env.template` was stale and used wrong var names** (reported): it listed `JAPES_AZURE_STORAGE_ACCOUNT_URL` / `JAPES_USE_MANAGED_IDENTITY`, which the queue settings reader never honored — a user copying it would omit the *required* storage URL and hit a startup error. Regenerated it to be complete and correct (grouped; newer vars commented-optional), and reconciled the README + `settings.py` docstring. To honor the intended `JAPES_`-namespacing convention uniformly, `create_queue_settings_from_env` now accepts `JAPES_AZURE_STORAGE_ACCOUNT_URL` / `JAPES_AZURE_STORAGE_CONNECTION_STRING` / `JAPES_USE_MANAGED_IDENTITY` as **preferred aliases** (bare `AZURE_*` remains the fallback), matching how KH/security vars already resolve (`JAPES_` first, bare second).
- **Added** — **`KernelClient.call_parallel`** — run a mix of kernel tool + agent calls concurrently (bounded, order-preserved, optional per-call degrade), built over `conductor.fan_out`. The client-side ergonomic equivalent of kernel's `parallel_tool_agent_execution`, via `KernelToolCall` / `KernelAgentCall` specs — eases migrating kernel workflows that use parallel tool/agent execution onto japes.
- **Changed** — **web search is now backend-agnostic** — a `WebSearchProvider` seam (like `DocumentIntelligenceProvider`) instead of a hardcoded vendor tool. `KernelWebSearchProvider` (default when a kernel client is present) targets a configurable kernel search tool (default `perplexity_search`), and native providers (Tavily/Google/direct API) can implement the same seam without kernel. `WebSearchConnector` composes a provider + native `read_from_url`. Fixes a latent bug: the connector previously called a non-existent kernel tool `web_search` (kernel's is `perplexity_search`), silently returning no results in real mode.
- **Changed** — model-name identity/normalization split out of `llm/cost.py` into a new leaf `llm/model_identity.py` (`provider_for_model`, `parse_model_tier`, `normalize_model_name`). `cost.py` predates model cards and had become a catch-all (pricing data + cost calc + identity utils); the identity helpers are now their own layer that both `cost.py` and `model_cards.py` build on (no cycle). Pure internal cohesion — the public API (`jazzx_sdk.parse_model_tier` / `normalize_model_name`, `jazzx_sdk.utils.*`) is unchanged; no back-compat shims (nothing outside imported these from `llm.cost`).

## [2.1.0] - 2026-07-19

Platform durability & robustness enhancements — proactively hardening the SDK's runtime primitives so they hold up as usage scales.

- **Added** — **durable-runs hardening** (`jazzx_sdk.runs`): the turn-run store gains production-grade durability. `request_stop_conversation(conversation_id)` atomically stops a whole conversation — cancels its queued turns (new terminal `TurnRunStatus.CANCELLED`) and cooperatively stops the running one, in one locked transaction so a queued turn can't slip into RUNNING mid-stop (surfaced on `ResilientRunner`). `purge_terminal(older_than_seconds)` adds journal retention (the event journal is a delivery buffer, not the transcript). And `reap_stale` is now a **fenced** sweep — it locks stale rows (`FOR UPDATE`) and finalizes them in the same transaction, re-evaluating `heartbeat_at < cutoff` under the lock so a run whose heartbeat was renewed concurrently is never retired; the reaper is safe to run aggressively at real concurrency.
- **Added** — **caller-identity resolution** as a platform capability (`jazzx_sdk.get_current_user_id/email/name`): japes already *forwards* `x-security-context` / `x-user-*` downstream; it now also *resolves* the caller from that context (decoded `userId`/`userEmail`/`userName`, raw `x-user-*` fallback), so a pack attributes authorship/creator/audit by asking the platform instead of hand-rolling a base64/JSON parse. Works across HTTP / queue / event paths.
- **Added** — **MLflow-tracing robustness** (`tracing.sanitize_leaked_otel_env_vars()`): japes owns the guard that strips a platform-injected `OTEL_EXPORTER_OTLP_ENDPOINT` / `..._TRACES_ENDPOINT` (e.g. Azure Container Apps) before MLflow tracer init, so a leaked endpoint can't silently swap MLflow's exporter for a missing gRPC OTLP one and drop every span. Not auto-invoked (`setup_telemetry` uses the OTLP endpoint legitimately); call it at startup.
- **Added** — **runtime observability tracer** (`jazzx_sdk.observability`): a backend-agnostic `RunTracer` for the per-turn lifecycle — start a run correlated to the incoming trace, tag it once (`build_run_tags`: identity `incoming.*` + caller business tags), open best-effort sub-`span`s carrying a filterable `stage` label, and log params/metrics/artifacts. `NoOpTracer` is the default (every call no-ops, so a handler wraps every turn without branching on whether tracing is on); `MlflowTracer` is one backend (lazy `mlflow` extra, best-effort — a backend failure degrades to no-op, never breaks the turn), and an OTel/App-Insights backend can implement the same base. Complements `MlflowTraceHooks` (the agent span tree) by owning the run/tag/stage layer callers otherwise reinvent.
- **Added** — **`clients.KnowledgeHubLike`** — a `runtime_checkable` Protocol naming the Knowledge Hub surface the fabric layer depends on. The fabric stores (canonical/graph/rag/docs/entities/collections/opa) and the KH-backed `tools` now annotate the *role* rather than the concrete `KnowledgeHubClient`, and both the real client and the in-memory `MockKnowledgeHubClient` are checked against the contract (a `issubclass` drift guard, so a dropped method fails a test instead of at runtime against one backend). `fabric.kh_status` keys off a robust `is_mock` flag instead of sniffing the class name.
- **Changed** — agent-session helpers are now **backend-neutral**: `tracing.create_agent_session` / `create_session_engine` accept any async SQLAlchemy URL (SQLite for dev/tests, Postgres, …) and add the asyncpg driver only for the postgres scheme — fixing the prior helpers' hard rejection of a valid `sqlite+aiosqlite://` URL. `create_postgres_session` / `create_postgres_engine` remain as deprecated aliases.
- **Added** — **`tracing.AgentTraceHooks`** — the OpenAI-Agents-SDK workflow→agent→llm→tool span tree is now a backend-agnostic base: the span-tree bookkeeping, callback flow, and token/cost accumulation live once in `AgentTraceHooks`, and a backend implements only four span primitives (`_begin_root` / `_start_span` / `_end_span` / `_finish_root`). `MlflowTraceHooks` is that base against MLflow (behaviour unchanged); an OTel/App-Insights backend implements the same base. Both are built lazily so `import jazzx_sdk` stays free of openai-agents (and its transitive uvicorn).
- **Added** — **reference chat conductor** (`agents.interactive.chat`): the reusable shape of a conversational turn as a `ConductorPipeline` (validate → gate → escalate | answer | refuse → finalize) + reference step-impls. A consumer supplies only the domain hooks — a router (`classify`) and an escalation callable — plus an `InteractiveAgent`, then runs `run_chat_turn(...)`; it gets per-stage traces, stage-progress streaming, and declarative routing for free. Deliberately thin: the direct path delegates to `InteractiveAgent.respond` (which already does grounding, guardrails, sources, and history), and escalation routes to a heavier engine the pack provides. japes ships the primitives + reference; assistants (loan chat, jaci scenarios) adopt it as config.
- **Added** — **reference document conductor** (`agents.document.pipeline`): the document analogue of the chat conductor — `build_document_pipeline` (detect → package | single | refuse → emit → finalize) + reference step-impls + `run_document`. Classification-driven routing via the gate; thin — the heavy work stays in the well-tested `DocumentAgent`. `DocumentAgent.process_package` now fans out over segments **concurrently** with a per-segment tracer span (via a new `tracer=` on `DocumentAgent`), and `process` opens `convert`/`classify`/`extract` spans for per-stage latency attribution. Domain-agnostic (taxonomy/classifiers/schema are pack-supplied), so any jaci domain configures it rather than wiring bespoke agents.
- **Added** — **`conductor.fan_out`** — the missing map-over-items primitive (the engine's `Loop` is converge-until, not map): runs an async processor over a collection with bounded concurrency, a per-item tracer span, and optional per-item degrade. Turns one emitted collection into N results (a document package → N constituents, a batch → N records).
- **Added** — **conductor step guards** (declarative branching): `PipelineStep.when` carries a human/BPMN-readable guard condition and `ConductorEngine(step_guards={...})` binds the executable predicate per step id — a step whose guard is false is recorded as `skipped(guard)` and emits no progress events. This is how a pipeline branches (e.g. a gate routing direct-answer vs escalate-to-reasoner vs refuse). Mirrors the existing `Loop.convergence` + `loop_converged` split (descriptor stays declarative/renderable; the logic is testable code — no expression-eval DSL).
- **Added** — **`ConductorEngine` observability + streaming wiring** (once, for every conductor): the engine now optionally takes a `RunTracer` and a `StepObserver`. Each step opens a tracer span tagged with its `stage` (its `phase` or id) — so per-stage traces come from the engine instead of being hand-tagged per service — and fires a `StepEvent` at start/end that a host can stream as progress ("Gating… / Grounding… / Answering…"). `ExecutedStep` now carries `started_at`/`completed_at`/`duration_ms` for per-stage latency attribution. Both hooks default to no-ops (existing callers unaffected, zero cost); the observer is best-effort and never breaks the run. The pack-specific `ConductorRun → CanonicalTrace` mapping intentionally stays pack-side (its mode/actor/autonomy are domain semantics the descriptor doesn't carry).
- **Added** — **best-effort backend contract** (`jazzx_sdk.concurrency`): `run_offloaded` (run a blocking backend call off the event loop), `best_effort` (offload **and** swallow — a side effect that must never block the loop nor break the turn), and the `BestEffortBackend` mixin (`_offload` / `_best_effort` / `_background` / `_drain`) that formalizes both guarantees plus a drained-at-boundary background-task tracker. Backend-neutral — no vendor in the contract.
- **Changed** — observability/tracing backends now honour that contract, so MLflow I/O no longer stalls the agent loop. `MlflowTraceHooks` runs its per-step span start/end off the loop (opt-in via `AgentTraceHooks._offload_blocking`, so any blocking backend inherits it); `MlflowTracer.run`/`span` offload their MLflow calls; and `RunHandle.log_params/metrics/dict` are backgrounded and drained before `end_run` (non-blocking, and never logged after the run closes). Behaviour is unchanged — only where the blocking work runs.
- **Changed** — bumped the `common` submodule pin to pick up platform fixes (telemetry fallback-handler recursion guard, settings deprecation, dependency vulnerabilities) and the new `final_result` streaming event. `jazzx_sdk.streaming` now re-exports `FinalResultEvent` (guarded — still imports against an older common). The Redis→SSE reader was already forward-compatible with unknown event types (raw pass-through, terminates only on `done`/`error`); covered by a test so a newer producer's events are never dropped by an older japes.
- **Added** — **idempotent, provenance-carrying writes across the fabric** (`fabric.idempotency`): idempotency and audit provenance are now a single write concern with one contract spanning every fabric store, instead of a per-backend bolt-on. `content_fingerprint` computes a stable, backend-portable SHA-256 key *client-side* (so dedup works before the write and against a backend that hasn't adopted native content-hashing); `WriteOutcome` returns the full object, its ref, a `created` flag, the fingerprint, and `Provenance` — so a caller learns created-vs-existing without reading an HTTP status or reconciling an id-only response. `fabric.entities.ensure(...)` and `fabric.docs.ensure(...)` create-once/return-existing against the Knowledge Hub (pre-check by hash + lost-race re-resolve), and `fabric.db.Repository.ensure(obj, key=...)` gives the relational store the same contract (unique-constraint race re-resolved, not raised). Document dedup now stamps *both* our `content_hash` and KH's native `sha256` key so the two dedup paths agree on document identity.
- **Added** — **`CallerIdentity`** (`jazzx_sdk.CallerIdentity`): the identity accessors bundled into one resolved value — `CallerIdentity.from_context()` (HTTP/queue/event), `.user_id/.email/.name`, `.is_anonymous`, and `.propagation_headers()` (the live outbound identity set). `Repository` auto-stamps `created_by_user_id`/`created_by` audit columns from it when a model exposes them (opt-in by column presence). The header-provider helper is now public as `default_request_headers`.
- **Added** — **read-back bases `TraceSource` and `evaluation.ExperimentStore`** — the write side already had pluggable backends (`RunTracer`, `EvaluationReporter`); the read side now matches. `TraceSource.read_trace(...)` reconstructs a completed run into a fabric `CanonicalTrace` (so `Decision.trace_id` resolves to a real Trace wherever the run was recorded); `ExperimentStore.write/read` persists and reconstructs an `ExperimentRun`. `MlflowTraceSource` / `MlflowExperimentStore` are the first backends; the MLflow translation stays in the `mlflow_bridge` helpers.

## [2.0.0] - 2026-07-16

A governed-composition release. Documents, packs, and pipelines become composable with provenance and
confidence carried end to end: a **document-processing chassis** that refuses sub-floor values rather than
writing them degraded; **pack composition** (`depends_on` fragment merge + a conductor `StepRegistry` so
capabilities publish step impls packs weave by reference); **governed guidance assets** (the retrieve-and-
inject learning loop); **multi-pass reconciliation**; plus platform additions (prompt-cache-key routing,
OTLP tracking→traceparent, tool-output compression). Additive except one behavioral change — `fabric.rag`
now **propagates** `KnowledgeHubAccessError` (401/403) instead of swallowing it as an empty result
(see Fixed), so an access denial surfaces rather than silently mis-driving an agent.

### Platform additions
- **Added** — prompt-cache-key routing: `agents.build_prompt_cache_key(*parts)` (deterministic, ≤64-char, provider-safe) + a `prompt_cache_key` param on `build_model_settings` (threaded to the OpenAI `extra_args`), so the repeated turns of one logical inference route to the same backend prompt cache.
- **Added** — OTLP trace-context propagation: `events_domain.otel_ids_from_tracking` / `traceparent_from_tracking` derive a stable W3C/OTel `(trace_id, span_id)` (and `traceparent`) from an opaque upstream tracking id, so a non-OTel identifier (e.g. a process-engine run id) joins one continuous distributed trace instead of each hop starting a fresh root span.
- **Added** — tool-output compression: `tools.compression_scope` / `compress_tool_output` / `read_reference` — a run-scoped `ReferenceStore` offloads large tool outputs and injects a compact head/tail preview + a reference marker into context, with `read_reference` as the agent's escape hatch to pull the full output back. Pluggable `ToolOutputCompressor` (default `PreviewCompressor`, dependency-free; a semantic backend like headroom drops in). Opt-in; passthrough outside a scope.
- **Added** — `channels.WebSocketChannel`: outbound delivery over a `ws(s)://` connection (the persistent-connection counterpart to `WebhookChannel`), registered as `"websocket"`. Same `ChannelMessage` body + optional HMAC signature (handshake header) + retry; uses `aiohttp` (already core). Additive — `WebhookChannel` (HTTP POST, Slack/Teams) stays.

### Document-processing chassis
- **Added** — `jazzx_sdk.agents.document`: a declarative `DocumentAgent` that composes the document tools (`convert_document` → `classify_document` → `extract`) into an ingest → classify → extract → emit flow whose every emitted value carries a `SourceCoordinate` + `Confidence` (tier via `PolicyProfile` floors). A value below the admission floor is **refused** as a typed `Refusal` (`SUB_CONFIDENCE_EVIDENCE`), never written as a degraded value — the XF-1 discipline. Generic `SourceFile` (content-addressed, idempotent), `ExtractedField`, `DocumentResult`; `assert_provenance_complete` gate; `register_document_steps` publishes `doc.process` as a `StepRegistry` impl so any pack pipeline can weave document processing by reference.
- **Added** — `DocumentAgent` **classify → template routing**: extraction is routed to a template by the classified doc type (`DocumentAgentSpec.templates` mapping, else the label if it names a registered template, normalising `_`↔`-`, else schema-only tier-3); a routed template that fits nothing falls back to schema-only, a caller-supplied template still overrides. The chosen template is recorded on `DocumentResult.extraction_template`.
- **Added** — `DocumentAgent` **per-field extraction confidence** (refusal is now per-field, not all-or-nothing): each field scores at `extract_score`, capped at `ungrounded_score` when the value isn't grounded in the source text (a cheap hallucination check — verbatim or digit-run match, so `1000` matches `$1,000`), with explicit `field_scores` overrides for pack-known-reliable fields.
- **Added** — `DocumentAgent.process_package(pdf, schemas=…)`: **combined-document split + fan-out**. Splits a combined PDF into constituent documents (`split_document` — outline or page-classification, no DocIntel), then runs `process` on each; `schemas` maps a doc-type label → extraction schema (a segment whose split label has a schema is extracted, others classify-only). Returns a `PackageResult` (the combined-file anchor + a provenance-complete `DocumentResult` per constituent, each with its own source anchor + page range). `register_document_steps` also publishes `doc.process_package` as a `StepRegistry` impl (`emits: PackageResult`).
- **Added** — `tools.AzureDocIntelligenceProvider`: the cloud-OCR implementation of the `DocumentIntelligenceProvider` (`di_provider`) seam — the opt-in last-resort fallback for scanned/rasterized documents (v2 stays readable-first). `convert(file_path)` reads bytes → Azure Document Intelligence (`prebuilt-layout`) → section-aware markdown. Split into a **pure** `analyze_result_to_markdown(result)` transform (sections → paragraphs/tables/figures, `**[Page N]**` markers, markdown escaping — duck-typed, no `azure` import) plus a thin client wrapper (endpoint/model from args or `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`/`_MODEL_ID`, injectable client). New optional `azure` extra (`pip install 'japes[azure]'`).
- **Added** — `DocumentAgent` **authority-gated admission**: a sub-floor value that would be refused can instead be **admitted by an authorized attestation**. `process`/`extract` accept `attestations` (field → `FieldAttestation(actor_class, human_initiated)`); a sub-floor field with an attestation that passes `authority.check_action` on the spec's `cell_ref` is admitted and marked `ExtractedField.attested_by` (the honest extractor score is kept — the admission is the attester's), otherwise it is still refused. Construct with `DocumentAgent(spec, authority=<AuthorityMatrixV2>)`.
- **Added** — `DocumentAgent.emit_entity(result, …)` + `materialize(result, schema)`: **emit the typed domain object to `fabric.entities`**. `materialize` assembles the schema instance from the *admitted* fields (refused fields omitted, never defaulted-in); `emit_entity` persists it, but when `schema` validation fails because a required field was refused it returns a typed `Refusal` (`PRECONDITION_FAILED`) instead of writing a partial/degraded object. The stored `json_value` is the domain object plus collision-safe `_source_file_id` / `_doc_type` / `_provenance` keys (pydantic field names can't start with `_`), so provenance is retained at rest; `entity_type` defaults to the classified doc type and `collection_id`/`ontology_id` fall back to the spec.

### Pack composition — dependency & fragment merge
- **Added** — `depends_on:` manifest key + `PackManifestLoader.resolve_dependencies` (ordered closure, deps before dependents, cycle detection → `PackDependencyError` naming the path) and `merged_assets(kind)` (fragment merge for playbooks/evidence_types: honors each edge's `fragments` filter, stamps `source_pack_id`/`source_pack_version`, and fails loud on an asset-id collision — no last-writer-wins). `Pack.playbooks`/`.evidence_types` return the merged view when the pack declares dependencies (`Pack.from_manifest(resolve_deps=)`); byte-identical local list otherwise. Re-declaring an imported id is a collision (fails loud); genuine narrowing stays in the Pack→SBA→Overlay→EP chain, not manifest merge. Unblocks JACI's `cl_of_core`/`cl_sp_core` importing shared ci-spread-core playbooks.

### Pack composition — conductor step registry
- **Added** — `jazzx_sdk.conductor.StepRegistry`: cross-pack step binding so a capability module can publish a named step implementation any pack pipeline weaves in by reference. `PipelineStep.impl` (optional) names a registered impl; `ConductorEngine(..., registry=)` resolves it when the scenario didn't bind that step id (explicit `components` still win, so a scenario can override a capability step). `register` fails loud on a conflicting re-registration; `ConductorPipeline.validate_against_registry` / `from_yaml(registry=)` catches unknown impls and `emits` mismatches at load. Pipelines without `impl` are byte-identical (unchanged behavior).

### Multi-pass reconciliation
- **Added** — `jazzx_sdk.reconcile`: vote N candidate observations of the same fact down to one **single-source** winner (value and every co-travelling field come from one pass, so a value can't be paired with a mismatched calculation or citation). Domain-agnostic `Candidate[T]`/`make_candidate`/`reconcile`/`reconcile_grouped`; deterministic verdict-agnostic vote with empty-dedup, core-completeness tiebreak (provenance excluded so a citation can't flip the value), representative selection (provenance included), earliest-source final tiebreak. Returns an auditable `Reconciliation` (vote counts, tie flag), not just the winner. First consumer: commercial-lending spreading over parallel extraction passes.

### Governed guidance assets (learning loop)
- **Added** — `fabric.guidance`: SME-approved, scoped guidance retrieved and injected per query (not baked into a prompt). `GuidanceAsset` (content-addressed `version` via `content_version`; `applicability` dims are pack-defined, never enumerated by the SDK; `to_guidance_ref` feeds `CanonicalDecision.guidance_refs` so effectiveness is computable). `GuidanceStore` (protocol + `InProcessGuidanceStore` + `RagGuidanceStore` over one KH collection). Wired onto `KnowledgeFabric` as `fabric.guidance` (config `guidance_collection_id`).
- **Added** — lifecycle admitted by `jazzx_sdk.statemachine` (`GUIDANCE_LIFECYCLE` table + engine): `GuidanceLifecycle` is a thin coordinator, not its own state machine. Deploy runs post-admission gates that return typed `Refusal`s (not exceptions): validation (`guidance_validation_blocked`/PRECONDITION_FAILED, flags in `domain_extensions`) and conflict (`guidance_conflict`/POLICY_CONFLICT_UNRESOLVED, `ConflictReport`). `GuardrailGuidanceValidator` composes the existing guardrail primitives; `detect_conflicts` flags near-duplicates (applicability overlap + trigger similarity). `supersede`/`rollback` never hard-delete.
- **Added** — `fabric.guidance.retrieve`/`render_guidance_block`/`to_guidance_refs`: best-effort retrieval that degrades to *no guidance applied* on fabric failure but lets `KnowledgeHubAccessError` propagate.
- **Added** — EVOLVE/PROVE integration: `evaluation.structure_feedback` (feedback → review-ready `GuidanceDraft` → `to_asset`), `evaluation.validate_guidance` (before/after harness over `PredictFn`/`TrainCase`; two `ExperimentRun`s sharing a `case_set_hash`; surfaces over-firing as per-case regressions), and compounding metrics `override_learning_rate`/`guidance_effectiveness`/`reusable_asset_growth`.

### Fixed
- **Fixed** — `fabric.rag` now re-raises `KnowledgeHubAccessError` instead of rewrapping it as `KnowledgeFabricError`, so an access denial isn't masked as an empty result at the fabric boundary (the KH-client discipline, extended to the RAG store).

## [1.9.9] - 2026-07-09

### Resilient interactive runs
- **Added** — `jazzx_sdk.runs`: durable, stoppable, resumable InteractiveAgent turns. `TurnRun` (keyed to `trace_id`; named to avoid the `ExperimentRun`/`ConductorRun` collision) + an append-only `TurnRunEvent` journal mirroring the live `InteractiveStreamEvent` vocabulary; `TurnRunStore` (protocol + `InProcess` + fabric.db `DbTurnRunStore`, with claim/heartbeat/stop-flag/`has_active_run`/`reap_stale`); `ResilientRunner.execute` (journals every event, tees to an optional live sink, snapshots partial, **cooperatively** stops via the durable `stop_requested` flag — never `task.cancel`) and `resume` (journal replay-then-follow, surviving reconnect/restart). Dispatch reuses the existing queue runtime; stop is a durable cross-pod flag. `TurnDispatcher` enforces per-conversation FIFO (durable `claim_next`: single-running + oldest-queued, so concurrent workers can't double-run a turn; different conversations run concurrently) and `Reaper` fails runs with a stale heartbeat (claim-fenced) on a loop. `runs.server.run_router` mounts governed start/stop/stream (SSE resume) endpoints via `GovernedRouter` (`serve(extra_routes=…)`): start enqueues (a queue worker drains), stop sets the durable flag, stream resumes the journal.

### InteractiveAgent & grounding
- **Added** — per-skill model override: `Skill.model` sets the model for that skill's sub-agent (else it inherits the parent agent's model) — different models for different sub-agents, declared as data.
- **Added** — `agents.interactive.SourceBuilder`: deterministically derive an answer's `Source`s by scanning for grounded anchors (finding mnemonics, filenames, entity ids) and resolving them, de-duped — sources are never invented. Pluggable anchor rules + an `add_index` convenience (longest-anchor-wins). (`Source` = InteractiveAgent provenance, distinct from the canonical `Citation` claim→evidence type.)
- **Added** — `tools.build_summary_index` + `tools.select_items`: the index + on-demand-fetch grounding pattern — inject a compact index into the persona (via `reference_loader`), fetch full detail only for the items the agent needs.

### Knowledge Hub client
- **Added** — typed `KnowledgeHubAccessError` (base `KnowledgeHubError`): a `401`/`403` from any KH endpoint now raises instead of being swallowed as `None`/`[]`/`False`, so an authorization denial is never conflated with "not found"/"no results" (which could silently mis-drive an agent). Enforced systemically at one choke point — a response event hook covering entities, documents, downloads, collections, ontology, policy, graph — and the client's `except` blocks re-raise it; fabric surfaces propagate it. A real 404 still maps to `None`.
- **Added** — `create_document(indexing_enabled=True)` (threaded through `fabric.docs.put`): KH flipped its upload server-default to `false`, which would silently leave japes-uploaded docs unindexed (RAG breaks). japes now sends the flag explicitly; it's feature-detected onto the generated client (body field or endpoint param) so it takes effect automatically once the client is regenerated, and warns once until then. See `docs/plans/plan_kh_client_bump.md`.

### Security
- **Fixed** — `tools.read_from_url` followed redirects automatically and validated the target only after the fetch, so a public URL redirecting to an internal address (e.g. cloud metadata) was still requested (SSRF-via-redirect). Redirects are now followed manually, validating each hop's host before fetching it, with a bounded redirect count.
- **Fixed** — a test validated a provenance URL by substring (`"claude.com" in url`); now checks the parsed hostname (CodeQL incomplete-URL-sanitization).

### Evaluation / EVOLVE loop
- **Added** — composable scorer contract (`evaluation.scorers`): optional `describe()`, `as_tool_schema()`, `ScorerSpec` + `build_composite()`; `ScorerResult` reconciled as the canonical shape with `evaluator_type`/`metrics`/`confidence`.
- **Added** — trajectory scorers (`evaluation.trajectory`): `ToolChoiceScorer`/`TrajectoryOrderScorer`/`StepEfficiencyScorer`/`ForbiddenToolScorer` over a `CanonicalTrace` + per-case `ExpectedTrajectory`.
- **Added** — adjudication policies: `all_pass`/`any_pass`/`k_of_n`/`majority`/`weighted_threshold`/`llm_judge` via `ADJUDICATION_POLICIES` + `adjudication_policy()`/`register_adjudication_policy()`; `AdjudicatorScorer.from_policy(...)`.
- **Changed** — `CostScorer` also prices LLM token usage (new optional `TokenUsage`/`model` on `ToolCall`) via `llm.compute_cost`, with a per-model breakdown; reports `cost_total_usd`/`cost_llm_usd`/`cost_tool_usd`.
- **Added** — feedback text normalization (`evaluation.feedback_text`): `normalize_feedback_text`/`extract_feedback_fields` unwrap a JSON-envelope payload; `render_feedback` applies it.
- **Added** — operational scorers (`evaluation.operational`): `LatencyScorer`/`CostScorer`/`TopologyScorer` over a run's `CanonicalTrace`, plus `aggregate_operational(traces)` (cross-trace, true wall-clock latency). `EvaluationResults.pass_rate` auto-derives from counts.
- **Added** — prompt optimization (`evaluation.optimization`): `optimize_prompt(...)` with the default `ReflectiveOptimizer` (LLM hill-climb) behind a `PromptOptimizer` protocol; `Feedback` objects and `synthesize_cases_from_feedback` feed it. `interactive_predict_fn` wires it to `InteractiveAgent`.
- **Added** — `EvalTemplate`/`EvalTemplateRegistry` (data-defined scorer bundles) and a `PromptRegistry` protocol (`InProcess`/`Db` + `promote()`).
- **Added** — feedback-quality LLM ops (`assess_feedback_quality`/`extract_actionable_items`) + shared `render_feedback`.
- **Added** — conversational-QA eval (`evaluation.qa`): `qa_case`, `AnswerCorrectnessScorer`, `CitationCoverageScorer`, `qa_scorers`.

### Domain events, state machines & automation chassis
- **Added** — `jazzx_sdk.events_domain`: `DomainEvent` envelope (frozen; carries `trace_id` + typed `VersionBundle`), `EventCatalog` (`from_index`/`from_dir`; fail-closed on unregistered names, JSON-Schema payload validation), `EventEmitter` (catalog-validated, in-process subscribers + `channels` delivery), and `traceparent`↔`trace_id` helpers. Distinct from the queue envelope (invocation vs fact).
- **Added** — `jazzx_sdk.statemachine`: data-driven object-lifecycle machines (`Transition`/`StateMachine`, `from_csv`) + a pure `TransitionEngine` (`apply` → `TransitionResult | Refusal`) enforcing the five corpus invariants (no-transition→OUT_OF_SCOPE, human-trigger refuses programmatic, profile-key guards fail-closed with a numeric-literal load-time lint, terminal states immutable, emit-on-success). Admissibility at the write boundary — not orchestration (flowable) or pipelines (conductor).
- **Added** — automation chassis (`jazzx_sdk.automation`): `Receipt`/`ReceiptStatus` (no receipt = no write), `IdempotencyStore` (`InProcess` + `EntityIdempotencyStore` on `fabric.entities`), and `GovernedAutomation` — a `run()` template enforcing idempotency → authority (`check_action`) → read-before-write drift (conflict → typed refusal) → execute → receipt → emit.
- **Added** — governed HTTP conventions (`jazzx_sdk.governed_http`): a `GovernedRouter` (mount via `serve(extra_routes=…)`) whose routes declare `mutating`/`cell_ref` and enforce `X-Trace-Id` (400 if absent) + `Idempotency-Key` on mutating routes with 409 replay of a prior receipt; `X-Trace-Id`/`X-Actor-Ref`/`X-Surface-Ref` propagate into a request-scoped context (cleared per request).

### Authority matrix & execution profile
- **Changed** — `manifest.AutonomyLevel` unified to one five-level ladder (`L0_ASSIST`…`L4_SELF_IMPROVEMENT`) with `to_numeric()`/`from_numeric()` (numeric is the storage form). Pre-1.11 value strings (`l0_advisory`…) still deserialize via `_missing_` (DeprecationWarning), each preserving its numeric level. `SurfaceType` gains `ASSISTANT`.
- **Added** — `fabric.canonical.authority`: `DecisionClass`, `AuthorityCell` (candidate/final kind by suffix; a final cell must be human-only or L0), `AuthorityMatrixV2` (`from_records`/`from_csv`, fail-closed `require_cell`). Distinct from `policy.AuthMatrix` (per-policy delegation).
- **Added** — `fabric.canonical.profiles`: `PolicyProfile` (fail-closed `get`, no SDK-default thresholds), `ClientOverlay`, `ExecutionProfile`, `SurfaceBinding` (YAML-loadable; fields beyond the resolver's consumption ride `extra`/`custom`).
- **Added** — `jazzx_sdk.authority`: `resolve_effective_autonomy` (most-restrictive intersection across cell/binding/overlay/EP + downgrades; human-only forces L0; records `contributing_layers`) and `check_action` → `EffectiveAuthority | Refusal`.
- **Added** — Governor integration: `GovernorMode(authority_matrix=…, surface_binding=…, client_overlay=…, execution_profile=…)` runs the authority check before any LLM step and short-circuits to a typed Refusal when inadmissible (absent a matrix, behavior unchanged); `BaseGovernanceSkill.ceiling_from_effective(...)` bridges an `EffectiveAuthority` to a `CeilingResult`; `PackManifestLoader` learns optional `authority_matrix`/`surface_bindings` keys.

### Governed value primitives
- **Added** — `fabric.canonical.Money`/`DecimalValue` (+ `Rounding`): exact-decimal values (reject floats, verbatim string serialization, no exponent input), currency-aware Money with derived `minor_units`, and minimal arithmetic requiring explicit rounding + mixed-currency guard. For governed values, not telemetry.
- **Added** — `fabric.canonical.Refusal` (+ `RefusalClass`, `RefusalRegistry`): typed refusals as first-class auditable outcomes (never exceptions); pack-loadable reason-code vocab over the SDK-owned class taxonomy. `server.py` `/invoke` maps a handler-returned `Refusal` to its HTTP status (registry override, else class default) — completed, not errored.
- **Added** — provenance/confidence on `fabric.canonical.evidence`: `SourceCoordinate` (typed document/workbook/section locators), `ProvenanceType` enum + extended `ProvenanceEntry`, `ConfidenceTier`/`Confidence` + `resolve_tier(score, floors)` (fail-closed; floors are profile data, no SDK defaults), optional `CanonicalEvidenceObject.confidence_detail`.
- **Added** — typed `fabric.canonical.VersionBundle` (`model_versions` required); `set_version_bundle` accepts it (stored as a dict, legacy kwargs kept); optional `version_bundle` on `CanonicalDecision`/`Artifact`/`ExperimentRun`. `finance.SpreadLine` gains additive `values_decimal` (float `values` unchanged; flip deferred). All surfaced via `jazzx_sdk.contracts`.
- **Fixed** — `modes/evolve/evaluator.py` read non-existent `outcome.outcome_class`/`.metadata`; now reads `result`/`learning_signals` with a getattr fallback.

### Queue envelope
- **Added** — `Tracking.traceparent` (W3C) + `build_invocation(traceparent=…)` for cross-service trace continuity; a boundary contract test pins the envelope to flowable-core's Macer schema (nested `header.tracking`, snake_case, flat root `status`/`error`).

### Fabric
- **Added** — `fabric.blob.offload(..., dedup=True)`: content-addressed (sha256) offload so identical payloads collapse to one blob and a retried offload is idempotent.

### Channels
- **Added** — `jazzx_sdk.channels`: outbound message channels (the send-out counterpart to `connectors`). `Channel` protocol + `ChannelMessage`/`ChannelResult`, a `build_channel`/`register_channel` registry, a generic `WebhookChannel` (HTTP POST + optional HMAC signature + retry; also covers Slack/Teams incoming-webhook URLs), and a keyless `CollectorChannel` for tests.

### Inbound events
- **Added** — `jazzx_sdk.events.event_router(...)`: a mountable inbound-event `APIRouter` (via `serve(extra_routes=…)`) that maps an HTTP event → `QueueMessage` → `Handler`. `mode="enqueue"` (default; 202 + caller-supplied `enqueue`) or `"sync"` (invoke inline, resolving handler/client_layer from `app.state`); optional `auth` dependency and `to_payload` transform.
- **Added** — `channels.notify_on_complete(handler, channel, …)`: a `Handler` decorator that sends the result to a channel after each `handle()` (best-effort; never breaks the response), across queue/server/event paths. Optional `when` predicate + `to_message`.

### Library adoption / layering
- **Added** — `jazzx_sdk.contracts`: server-free import surface (canonical DTOs, scorer/optimization contracts, `Feedback`); SDK Adoption Policy (tiers + P1–P7) in ARCHITECTURE.md.
- **Changed** — SDK/contract and queue layers no longer load the server stack at import (Tier-3 symbols lazy via PEP 562); locked by import-boundary tests.

### Persistence behind fabric
- **Added** — `fabric.db` (`session`/`get_session`/`engine`/`register_metadata`/`repository`, `db_backend="common"|"sqlite"`) and `fabric.blob` (`put`/`get`/`delete` + `offload`/`materialize`, `blob_backend="local"|"azure"`). Sqlmodel-free.
- **Added** — durable stores on `fabric.db`: `DbFeedbackStore` (FeedbackStore now async) and `DbCostRecordStore` (write-through cost history).

### Conversation / interactive agent
- **Added** — `MaskingConversationStore` + pluggable `MaskPolicy` (default `OutputMaskPolicy`); composes with `CompactingConversationStore`.
- **Added** — bidirectional `Session ⟷ ConversationStore` seam: public `ConversationStoreSession` + `InteractiveAgent(session_factory=…)`.
- **Added** — `InvocationConfig`: per-invocation runtime config on the wire (`payload.data.config`); `apply_to(spec)`.
- **Added** — `scope_guardrail`, agent inventory/introspection (`describe()` across spec/agent/`ProfileRegistry`), and richer `InteractiveResponse.sources` citations (`label`/`uri`/`collection_id`/`quote`).
- **Fixed** — `ToolStreamHooks.on_tool_end` classifies tool success best-effort instead of hard-coding `success=True`.

### LLM / model data
- **Changed** — model pricing + card facts live in `model_data.json` (loaded via `_model_data.py`); `scripts/update_model_pricing.py` reconciles against vendor pages. Reconciled pricing (2026-07); added the current Claude tier.
- **Added** — model-card registry (`get_model_card`/`list_model_cards`/`context_window_for`), deprecation tracking (`is_deprecated`/`DEPRECATED_MODELS`), pricing provenance (`pricing_source`).
- **Added** — text sanitization (`jazzx_sdk.sanitize`): `sanitize_text`/`strip_nulls` strip NUL + lone surrogates (opt-in control chars), applied at `LLMManager.run` and `fabric.entities` writes.
- **Added** — `structured_call(llm, prompt, schema)`; `cost_tracker_token_source` + token-compaction API exports.

### Fabric / docs / streaming
- **Changed** — fabric surfaces enforce their return contract (`fabric._contract`, raises `TypeError` on a leaked shape); + a KH-client return-shape contract test.
- **Changed** — `fabric.docs.materialize`: `doc_id_field` fallback paths, whole-entity naming callbacks, transient-download retries; content-hash dedup now paginates.
- **Added** — `local_fabric(seed_dir=…)` + Mock local store serves documents (offline fabric round-trip).
- **Added** — streaming: `stream_invocation_sse(tail=…, named_events=True)`, `StreamPublisher.from_url`, `@jazzx/japes-client` (JS thin client).
- **Changed** — `tools.discover_agents`/`discover_tools` pass through `invocation_count` + `rank_by_usage`.

### Runtime / server / security
- **Added** — settings API (`settings_api.create_settings_router`, pluggable `SettingsStore`) + `serve(extra_routes=…)`.
- **Changed** — RBAC identity forwarding is automatic (runtime sets security context before `handle()`); added `clear_security_context()` lifecycle reset.
- **Fixed** — `ClientLayer.knowledge_hub` raises (no silent Mock fallback) under a production posture.
- **Security** — OData literal escaping (`escape_odata_literal`), settings-API auth + prod-posture PATCH refusal, `mount_spa` path confinement via `StaticFiles`, and 3 resolved CodeQL alerts (PR #47).
- **Added** — `retry_async`/`backoff_delay`; `PackManifestLoader.describe()` + a Naming Conventions section in ARCHITECTURE.

## [1.9.8] - 2026-07-04

The interactive-agent & client-substrate release — grows japes into the substrate assistant-style clients build thinly on.

- **Added** — end-to-end streaming: `InteractiveAgent.respond_stream(...)` (single-shot + agentic), `LLMManager.run_stream` + provider streaming, `ScriptedLLM.run_stream`; tool streaming (`ToolStreamHooks`, `spec.stream_tool_events`) and ergonomics (`set_stream_context`/`publish_event`/`clear_stream_context`, `StreamPublisher(enabled=, maxlen=)`). XADD field key standardized to `"data"` (`streaming.EVENT_FIELD`).
- **Added** — structured output from `InteractiveAgent` (`respond(output_schema=…)` → `InteractiveResponse.output`); `spec.max_turns`; single-shot now threads the full model/settings like the agentic path.
- **Added** — `agents.run` first-class `temperature`/`reasoning_effort`/`service_tier`/`verbosity` (forwarded only when set; per-provider mapping on the LLM path, `model_settings` on the agentic path).
- **Added** — async guardrails; `llm_guardrail(llm, policy, …)` (LLM classifier/moderation as a reusable guardrail).
- **Added** — the `server` shape can front a built SPA (`ServerSettings.static_dir`/`spa_fallback`, `jazzx_sdk.mount_spa`).
- **Added** — `build_invocation(...)` (construct an invocation `QueueMessage` without re-declaring the envelope); `gather_degrading`/`degrade` (resilient concurrent fan-out).
- **Changed** — `MessageHeader`: accepts `x_security_context` input alias; `correlation_key`/`message_id` optional (default fresh UUID, never None).

## [1.9.7] - 2026-07-02

Evaluation + INTERACT primitives, config-over-code, and compounding-loop building blocks. Several concepts adapted from eval-service (reimplemented, not copied).

- **Added** — `jazzx_sdk.evaluation.scorers`: structured `Scorer`/`ScorerResult` (score/passed/comment/metadata) with weighted+required `CompositeScorer`, `AdjudicatorScorer`, `ScorerRegistry`, and `FunctionScorer.from_metric` adapters; `EvaluationHarness(scorers=...)` records `CaseResult.scorer_results`. Generalizes the flat `metric_functions`.
- **Added** — `LLMJudgeScorer`: an LLM-backed `Scorer` (the ready judge behind `AdjudicatorScorer`); works with a real `LLMManager` or a `ScriptedLLM` (keyless).
- **Added** — schema-validated golden cases: `GoldenCaseValidator.validate_schema(cases, input_schema=, expected_schema=)` (JSON-Schema check, meta-validated, non-fatal) + `GoldenCaseLoader.load_schema` (`_schema.json` sidecar). `load_cases`/`hash_cases` now skip `_`-prefixed sidecars.
- **Added** — case-set versioning: `diff_case_sets` / `CaseSetDiff` (added/removed/changed-with-fields + `summary()`) and `CaseSetVersion` / `describe_case_set` (content hash + count + lineage + change summary) — a pure diff over golden-case sets (no DB).
- **Added** — `jazzx_sdk.evaluation.feedback`: typed `Feedback` learning signal with `from_case_result` auto-emit and `to_signal()` → EVOLVE `ImprovementSignal`; pluggable `FeedbackStore` (`InProcessFeedbackStore` default).
- **Added** — `GoldenCase.from_outcome` / `from_override`: promote a production outcome or a human override into a gold case (the "outcomes/overrides flow into better gold sets" building block).
- **Added** — `jazzx_sdk.llm.ScriptedLLM`: a keyless, deterministic `LLMManager` double (canned replies in order or via callable; structured-output aware; records `.calls`) — run/demo/test InteractiveAgents without API keys.
- **Added** — `jazzx_sdk.agents.build_interactive_agent(spec, fabric=, llm_manager=, ...)`: one-call factory for a grounded ("jazz") `InteractiveAgent` (wires `AgentExecutionService`; extra kwargs pass through).
- **Added** — `Pack.agent` / PackLoader `agent:` support: a pack's `agent:` manifest section resolves natively to an `InteractiveAgentSpec` (the INTERACT counterpart to `conductor:`); build a live agent with `build_interactive_agent(pack.agent, ...)`.

## [1.9.6] - 2026-06-28

- **Added** — SSE streaming: `stream_invocation_sse` + gated `GET /stream/{streaming_id}` (`create_app(stream_client=...)`), client-supplied `streaming_id`. See README / ARCHITECTURE.
- **Added** — `fabric.entities.list_all` (auto-paginating) and `fabric.docs.materialize` (download KH entity documents to a named local dir; unzips archives) + `MaterializedDoc`.
- **Fixed** — `EvaluatorMode` constructed `EvaluationReport` without the required `pack_id` (runtime `ValidationError`); `L3ReviewStorage` read case results under the wrong key (`cases` vs `case_results`).
- **Added** — assistant surface primitives (`jazzx_sdk.manifest`): `AssistantManifest` + `ArchetypeType`/`AutonomyLevel`/`SurfaceType`; `load_manifest` (sync, skill fail-fast) + `resolve_pack` (async, opt-in).
- **Added** — `ExperimentRun` (`jazzx_sdk.evaluation.experiment`): comparison/index record over eval runs, auto-created by `EvaluationHarness`; adds `GoldenCaseLoader.hash_cases`, `EvaluationConfig.dimensions`, lazy `mlflow_bridge`.
- **Added** — `EvaluationHarness` gate `gate_claims` (signature-based dispatch; role-aware-gating forward-compat).
- **Added** — `fabric.entities` (`EntityStore`): first-class generic typed-entity CRUD, replacing the raw `fabric.kh` escape hatch.
- **Added** — `InteractiveAgent` `hooks` + `model_settings`; `InteractiveAgentSpec.reasoning_effort`/`service_tier`; `Skill.mcp_servers`.
- **Added** — `fabric.pack` property; `Outcome.from_context(...)` factory.
- **Added** — `jazzx_sdk.streaming.StreamPublisher` over `common`'s `RedisStreamClient` (optional `streaming` extra); typed events re-exported from `common.core.streaming`.
- **Added** — security-context propagation (`set/get_security_context`); `ClientLayer` forwards the full inbound identity set (incl. `x-user-id`) for RBAC-enabled KH.
- **Added** — `KnowledgeHubClient.get_document_content`/`get_run_findings` wrappers; per-group imports with diagnostics; mock/real parameter contract test (dev).
- **Changed** — KH/fabric return-shape cleanup: `create_entity`/`update_entity` return `dict` (not raw `Response`); deletes return `bool`; single-resource reads return `Optional[dict]` (None on miss); `get_policy_bundle` returns `Optional[bytes]`.
- **Changed** — renamed `fabric.policy` to `fabric.opa` (`OpaBundleStore`) to disambiguate from the canonical `Policy`; placeholder pending the OPA-via-canonical-Policy rework.
- **Changed** — `datetime.utcnow()` to tz-aware `datetime.now(timezone.utc)` across `jazzx_sdk`; `Policy.is_active` tolerates a naive `expiry_date`.
- **Changed** — `KnowledgeFabric` refuses the in-process Mock under a production posture (`JAPES_ENV`/`ENVIRONMENT`/`APP_ENV`).
- **Fixed** — `ExpertRegistry.get_expert(evidence|governance|investigative)` now raises a clear `ValueError` (those moved to `jazzx_sdk.skills.*` in 1.5.0), not `ImportError`.

## [1.9.5] - 2026-06-25

- **Added** — `fabric.conversation`: fabric-managed conversation memory; `FabricConfig.conversation_backend` = `in_process`/`local`/`sql` (lossless file or `common.core.db`).
- **Added** — token-authoritative agentic compaction: `CompactionPolicy(strategy="responses")` (compacts on input-tokens over threshold, Responses-API item fidelity, overflow-retry + mid-flow guard) + compaction telemetry.
- **Fixed** — session conforms to the openai-agents 0.17.x `Session` protocol; `AnthropicProvider` lazy-inits (no raise when the key is unset).

## [1.9.4] - 2026-06-24

- **Added** — conversation memory for `InteractiveAgent`, declared on the spec: `conversation` (enable turn-threading) + `compaction` (`CompactionPolicy`). `ConversationStore` (default `InProcessConversationStore`) is lossless — `load` serves the working view, `load_raw` the full archive, `supersede` replaces the working view in place. Compaction strategies are pluggable via a registry (`CompactionStrategy` + `register_compaction_strategy`/`build_compaction_strategy`); built-ins `summarize` (LLM; count/char/both trigger) and `drop` (sliding window). `AgentExecutionService.conversation_store(spec, store)` wires the store and policy.
- **Added** — `ConversationBinding` + `OpenAIAgentsBinding` (+ `AgentExecutionService.bind_conversation`): adapts a `ConversationStore` to the OpenAI Agents SDK `Session` protocol (`get_items`/`add_items`/`pop_item`/`clear_session`), so the agentic path runs with substrate-managed history and persistence while the archive stays in the store. Provider-specific item serialization is isolated behind hooks on the binding.
- **Changed** — renamed the conversation/compaction surface to concept names: `spec.memory` → `spec.conversation`; `spec.compression`/`CompressionConfig` → `spec.compaction`/`CompactionPolicy`; `MemoryStore` → `ConversationStore`; `InMemoryStore` → `InProcessConversationStore`; `CompactingMemoryStore` → `CompactingConversationStore`; `SummarizeCompaction`/`DropCompaction` → `SummarizeStrategy`/`DropStrategy`; `InteractiveAgent(memory=…)` → `(store=…)`. `memory` is reserved for a future durable-recall binding.
- **Added** — `finance.structure_statement`: the LLM convert step of spreading (located/flattened grid → typed `Statement` + periods/units), with the domain structuring prompt (`STATEMENT_STRUCTURE_SYSTEM`/`STATEMENT_STRUCTURE_PROMPT`) and a `statement_prompt_preview()` for UI display. Completes the spreading pipeline in the SDK — packs supply only the per-segment anchors; the schema, structuring, export, and metrics are all SDK-owned.
- **Added** — `Portfolio[T]`: a generic collection-of-transactions aggregate (`state_counts`/`in_state`/`group_by`/`total`/`where`/`filter`/`batch`; attr/dict-key/callable accessors) for book-level views over many transactions (e.g. a loan book).

## [1.9.2] - 2026-06-20

- **Changed** — bump `common` submodule to `a436b9e` (OTel queue tracing); the queue consumer now handles its decoded-dict content.
- **Fixed** — `queue_processor.dequeue_message` accepts message content as a dict or a JSON string (provider/common-version dependent); previously `json.loads` on a dict failed and the message was dropped as malformed.

- **Added** — `InteractiveAgent` input/output guardrails (`blocked=True` on trip); `examples/loan_assistant`.
- **Added** — `fabric.local_fabric` + `CanonicalObjectStore.put`: seed canonical objects into an in-memory fabric.
- **Added** — `tools.build_assessment` → the canonical chain Policy→Evidence→Decision→Trace→Outcome.
- **Added** — `tools.extract(doc, schema, template=…)`: typed document extraction — templated or schema-only for unknown readable formats; readable-first triage (`is_readable`/`require_readable` → `DocumentNotReadableError`, DocIntel an explicit fallback).
- **Added** — `tools.classify_document(doc, taxonomy)`: classify a document into a caller-supplied taxonomy (LLM over readable text; label validated, `"unknown"` fallback). `DocumentClassifierRegistry` gains `classify_llm`/`taxonomy` (generic-LLM routing via `classify_document`/`extract`); `BaseDocumentClassifier` gains optional `description`/`schema` — one classification surface, generic engines + typed registry layered.
- **Added** — `tools.split_document(pdf, taxonomy)`: split a combined PDF into labelled segments (bookmarks, else page-classification with run-smoothing; no DocIntel) + `write_segments`.
- **Added** — `tools.TEMPLATES` extraction-template registry: tier-1 SDK defaults (`10-k`, `financial-statements`) ⊕ pack-registered; `extract`/`extract_financials` accept a template by name.
- **Added** — `tools.filings`: SEC 10-K → typed `Financials` (`fetch_10k`/`extract_financials`/`process_10k`).
- **Added** — document **tier routing** (additive; `convert_document`/`classify_document` unchanged): `classify_document` runs a zero-cost filename heuristic before the LLM; `TEMPLATES` tags each template with a tier (1 SDK-native / 2 pack-config / 3 borrower); `tools.fallback_sources` (`OnlineFallbackSource`/`FallbackSourceRegistry` + SDK `EdgarFallbackSource`); `tools.convert_with_fallback` → `ConversionResult` routes direct → online-fallback (canonical digital version, bypassing DocIntel) → DocIntel.
- **Added** — `conductor.ConductorEngine`: drives a `ConductorPipeline` descriptor as execution (Stage 2) — walks steps in order, repeats loop groups to convergence (per-loop predicate + `max_iterations`), threads emitted objects via `ConductorState`, records a `ConductorRun`. A pack supplies step id → component; the engine owns the sequencing + loop a pack conductor's `run()` hand-writes today. Unwired steps are skipped (incremental adoption).

## [1.9.1] - 2026-06-19

- **Changed** — `InteractiveAgent` skill defs run as isolated sub-agents via `Agent.as_tool`; bare skill names stay direct tools. `Skill` gains `description`.
- **Added** — `InteractiveAgent` skill catalog: `SkillRegistry` (shared, filterable; `load_dir`/`catalog_text`) — `spec.skills` resolves against it; spec gains `mcp_servers`; `Skill` gains `references`.
- **Added** — `ProfileRegistry`: host many named `InteractiveAgentSpec` profiles resolved by name (`load_dir` over `profile.yaml` folders / `*.yaml`); `validate(skills=, guardrails=, mcp_servers=)` cross-checks every profile's references against the catalogs at boot, raising once with all dangling refs (+ guardrail phase mismatches).
- **Added** — `GuardrailRegistry`/`Guardrail`: one phase-aware guardrail catalog; `InteractiveAgent` accepts it or a `{name: callable}` dict.
- **Added** — session memory: `spec.memory="session"` + a pluggable `MemoryStore` (`InMemoryStore` default); `respond(session_id=…)` loads prior turns and persists the new one (blocked turns excluded).
- **Added** — `CompactingMemoryStore` + `llm_summarizer`: a `MemoryStore` wrapper that summarizes the oldest turns past a budget and keeps recent ones — compaction is transparent to the agent.
- **Added** — skill `references` ground their sub-agent (loaded into its prompt via `reference_loader`, default `to_markdown`); the parent prompt auto-lists available skills; `CompactingMemoryStore` gains a `max_chars` size/token-budget trigger.
- **Changed** — Skill/Profile/Guardrail/Template registries share a `NamedRegistry` base (consistent `get`/`names`/`__contains__`); `ProfileRegistry` gains `register_dict`, `DocumentClassifierRegistry` a `names()` alias.
- **Added** — `convert_document` handles Excel (`.xlsx`/`.xlsm`) → markdown (needs `openpyxl`).

## [1.9.0] - 2026-06-19

Profile-driven **interactive agents** — stand up a knowledge-grounded query agent from a declarative profile. (Road to 2.0.)

- **Added** — `InteractiveAgent` (`jazzx_sdk.agents.interactive`): a data-defined (`InteractiveAgentSpec`), fabric-grounded, scoped query agent; `.respond()` does single-shot grounded Q&A or an agentic skills loop. Lazy-loaded.
- **Added** — `fabric.canonical.find(Model, where=…) -> Page[T]`: typed query over canonical objects (`Outcome`/`Evidence`/`Trace`/`Decision`/`Policy`), plus `required_indexes()`/`index_schema()`. Additive.

## [1.8.9] - 2026-06-18

OpenAI-Agents-SDK enablement kit — ready-wired model setup, retry, Claude wiring, and observability for clients driving `Agent`/`Runner` directly.

- **Added** — `jazzx_sdk.agents.models`: `resolve_model()`/`build_model_settings()`/`RetryingModel` (transient, orphaned-reasoning, and truncated-output handling).
- **Added** — `AgentExecutionService.openai.build_agent(...)` → a ready-wired `Agent` (caller drives `Runner`).
- **Added** — `jazzx_sdk.agents.AnthropicModel`: Claude as a `Model` in the OpenAI Agents SDK, via LiteLLM (`litellm` extra).
- **Added** — `jazzx_sdk.tracing.MlflowTraceHooks`: nested MLflow spans + token/cost accounting (`mlflow` extra).
- **Changed** — `import jazzx_sdk` no longer eagerly pulls the agents/modes stack; loads lazily.
- **Changed** — dependency floors: `openai-agents>=0.17.0`, `anthropic>=0.69.0`.
- **Fixed** — bounded `python` to `>=3.11,<4.0` so `poetry lock` resolves.

## [1.8.8] - 2026-06-17

- **Added** — `EvidenceTypeRegistry` + `EvidenceTypeDef` + `load_evidence_types(path)` (`jazzx_sdk.fabric.canonical`): a pack's evidence vocabulary authored as YAML (id + description + data-shape `fields` + `requestable`) instead of a per-pack `EvidenceType` enum. Adding a source becomes a YAML edit. Case-insensitive lookup; mirrors the PolicyRegistry / `load_policies` pattern. `Evidence`/`CanonicalEvidenceObject.evidence_type` stay plain strings — this is the authoritative vocabulary they're drawn from.
- **Changed** — `BaseToolRegistry` takes an optional `evidence_types=` registry. `get_available_tools()` is now concrete (no longer abstract): returns the registry's `requestable_ids()` if set, else the registered tools' evidence types — packs stop hand-maintaining the list. New `validate_evidence_types()` flags drift (a tool for an undeclared type; a requestable type with no tool), `raise_on_error=` optional.
- **Changed** — `InvestigatorMode` accepts `evidence_types=` and injects the requestable types (id + description) into its prompt, so the pack's `evidence_types.yaml` is the single source of the requestable vocabulary rather than a hand-maintained list in the mode tuning. Omitted → prior behavior (vocabulary stays in the tuning prose).
- **Changed** — `DefaultPolicyExpert` now works with zero subclassing for the common case. Configure it from pack data — `registry` (a `PolicyRegistry`/`list[Policy]`), `core_policy_ids`, `overlay_map` — and it runs built-in overlay-aware `resolve()` (core + program overlays, precedence, conflict/staleness detection) and condition-gate `check_compliance()` (field-precedence across policies; two-tier gates within a policy), stamping `GUIDANCE_REFS` on every response. No registry configured → both stay no-ops (legacy KH-tool-backed behavior preserved). `DefaultPolicyExpert.from_policy_dir(dir)` hydrates every `*.yaml` in a pack's policy dir.
- **Added** — `ExpertRegistry.register_instance(type, expert)`: register a pre-configured Expert instance (e.g. a data-hydrated `DefaultPolicyExpert`) so `get_expert()` serves it — lets a pack stay subclass-free yet still route through the registry.

## [1.8.7] - 2026-06-16

- **Fixed** — `KnowledgeHubClient.read_entities()` returned `[]` on a successful 200 because the generated `_parse_response` for `GET /reasoning/entities` has no 2xx branch (`parsed` is None). Now recovers the entity list from the raw 2xx body (bare array or `{entities:[…]}`) before treating it as empty — also unblocks `read_triples`/`fabric.graph`, which ride on it. Bumps `pyjwt` floor to `>=2.13.0`. (Cherry-picked from #40 on main.)
- **Added** — `jazzx_sdk.fabric.canonical.load_policies(path)`: load canonical `Policy` objects from a YAML file (a top-level list or a `policies:` mapping; `model_validate` per policy handles nested rules, source refs, escalation/authority, enums), so packs author policy sets as data instead of in-code `Policy(...)` literals.
- **Added** — `ConductorPipeline.from_yaml(path, name=...)`: load a conductor pipeline from a declarative YAML (or select one of several nested under a top-level `pipelines:` map), so packs can own pipelines as data instead of in-code `ConductorPipeline(...)` literals.
- **Added** — `jazzx_sdk.evaluation.metrics`: generic metric primitives (`exact_match` / `within_tolerance` / `set_coverage`) that pack `metric_functions` compose. Replaces the broken docstring reference to a non-existent `metrics.DecisionAccuracy`.
- **Changed** — `jazzx_sdk.evaluation` is now a single front door: docstring maps the L1/L2/L3 layers + run aggregate (`EvaluationResults`) vs per-case canonical artifact (`EvaluationReport`), and re-exports `EvaluatorMode` (modes.evolve) and `EvaluationReport` (fabric.canonical) so the whole framework is reachable from one import. Guardrail test asserts the front door stays complete.
- **Added** — L2/EVOLVE hook in the harness: optional `evaluate_fn(case_file, golden_case) -> dict` run post-case (the pack owns the Outcome + EvaluatorMode + Curator), stored on `CaseResult.evaluation`. Makes the previously-dead `evaluator_factory` placeholder real.
- **Added** — token/cost capture in the harness: optional `token_metrics_fn(case_file)` (mirrors `case_detail_fn`) populates `CaseResult.token_metrics`, summed onto `EvaluationResults.token_metrics`; `MlflowReporter` logs them. Lets packs route per-case usage (tokens, cost, llm_calls) through the standard results instead of a bespoke aggregator.
- **Added** — `jazzx_sdk.evaluation.reporters.mlflow.MlflowReporter`: an optional `EvaluationReporter` that publishes a run to MLflow (config/labels → params/tags, pass-rate/averages/summary → metrics, results JSON → artifact, run id → `external_ref`). Behind the `mlflow` extra (`pip install 'jazzx_sdk[mlflow]'`); core stays MLflow-free.
- **Added** — `jazzx_sdk.evaluation.EvaluationReporter`: pluggable persistence/publish backend for the evaluation harness (`report(results)` once; optional `report_case(...)` streaming). `EvaluationHarness` now accepts a `reporter=` and calls it; `report()`'s return is stored on the new `EvaluationResults.external_ref`. Built-in JSON `save()` stays the default local sink; MLflow / eval-service become reporters outside the SDK.

## [1.8.6] - 2026-06-15

- **Added** — env-driven LLM resolution in `jazzx_sdk.llm` (`resolve_provider` / `resolve_model` / `resolve_key` / `ensure_provider_key` / `llm_from_env`): build an `LLMManager` from `{PREFIX}_LLM_PROVIDER` / `{PREFIX}_LLM_MODEL` + standard provider key envs (with nearest-`.env` fallback). Prefix-namespaced so multiple apps coexist.
- **Added** — `jazzx_sdk.fabric.FabricConfig.from_env()` + `fabric_from_env()`: build a fabric from `FABRIC_MODE` / `JAPES_KNOWLEDGE_HUB_URL`|`KNOWLEDGE_HUB_URL` / `KH_API_KEY` / `LOCAL_DATA_DIR` / `GOLDEN_CASES_DIR`. Also fixed `validate_for_mode` to not `AttributeError` on the error path when `retrieval_mode` is a coerced str.
- **Added** — `jazzx_sdk.modes.compose_mode_prompt` / `make_prompt_resolver`: assemble a mode's system prompt as **platform base ⊕ pack `mode_tuning`** (distinct from the single-file `resolve_mode_prompt`), so packs get the same base+skill composition instead of hand-rolling it.
- **Added** — `tools.extraction`: template-based document region location + extraction. `RegionAnchor` / `ExtractionTemplate` declare how to find a region in a converted (markdown/iXBRL) doc — title cues + signature line items, `window` or `table`-stitch mode, and a `start_after` skip marker (e.g. skip MD&A to the auditor's report). `locate_region` / `flatten_region` / `structure_region` locate it, flatten the HTML to `label | v | v` rows, and LLM-structure those rows into JSON. Generalizes the financial-statement spreader so domain packs feed a declarative template instead of hand-rolling the search.
- **Added** — `PipelineStep.phase` (optional): a label for grouping a conductor's steps into a few phases (e.g. Intake / Investigate / Synthesize / Govern / Record) so a long flat step list can render as a handful of labelled clusters. Backward-compatible (None → ungrouped).
- **Added** — `platform_catalog.MODE_KINDS` / `MODE_KIND_LABELS`: classify each cognitive mode by how it's implemented today — `agent` (LLM), `rule` (deterministic guards, e.g. sentinel), `python` (orchestration/logic, e.g. conductor/curator), `hybrid` (e.g. evaluator), `planned` (stub). Lets UIs answer "which modes are real LLM agents vs deterministic code vs not-yet-built" without guessing.
- **Docs** — `DOMAIN_PACK_QUICKSTART.md`: added a design-first "Domain Pack Crafting Methodology" (policies→PolicyExpert, playbooks→PlaybookExpert, ontology, conductor for dominant+secondary workflows, specialize canonical objects/modes/experts, gold cases + metrics + compounding loop, then flow gold cases through before real transactions), grounded in the JACI reference packs and current SDK substrate (`platform_catalog`, `Pack`, `conductor`, experts, evaluation). Refreshed the stale version banner.

## [1.8.5] - 2026-06-14

- **Added** — UI KH path (`jazzx_sdk.ui`) now sends both caller-identity headers when set: `x-user-id` (`JAPES_KH_USER_ID`/`KH_USER_ID`, for Keto) and `x-security-context` (`JAPES_SECURITY_CONTEXT`/`SECURITY_CONTEXT`, the process-engine token — env-sourced since the UI has no per-message context). Distinct keys, each independent, so no conflict.
- **Fixed** — OpenAI agent provider (tool-loop path) read the agent result from a nonexistent `result.data`, falling back to `str(RunResult)` (`"RunResult:\n- Last agent..."`) → structured-output parsing always failed. Now reads `result.final_output` and parses via the shared `validate` helper (accepts instance / dict / JSON text). This had broken every mode that runs through the agent tool path (investigator, etc.) on OpenAI.

## [1.8.4] - 2026-06-14

- **Added** — Gemini provider (`jazzx_sdk.llm.providers.gemini.GeminiProvider`): text + native structured output (`response_schema`), wired into `LLMManager` (`gemini_api_key`, `_get_provider`, model→provider inference for `gemini-*`). Reads `GEMINI_API_KEY`/`GOOGLE_API_KEY`. Optional dep via the `[gemini]` extra (`google-genai`).
- **Added** — `jazzx_sdk.conductor.Checkpointer`: reusable versioned `CaseContext` checkpoint emission for conductors. Owns the generic plumbing (monotonic seq, versioned id `ctx_{case_id}_{seq:02d}`, best-effort persist that never aborts the loop, trace stamping); a scenario supplies only the domain mapping + one `await cp.emit(case_ctx)` per iteration boundary. Lifts the pattern prototyped in jaci's ci_spread into the SDK.
- **Added** — `CaseContextStore.latest(case_id)` and `Pack.resume(case_id)`: recover the newest checkpoint for a case to restart a loop (checkpoints were audit-only before).
- **Fixed** — OpenAI provider sent a `flex_`-prefixed model alias (e.g. `flex_gpt-5.4`) to the API verbatim → `model_not_found` 404, and never sent `service_tier`. It now resolves the alias via `parse_model_tier` to the base model + `service_tier="flex"` (japes owns the translation; callers pass the alias directly).
- **Fixed** — `get_client_layer()` now sends KH caller identity (`x-user-id` from `JAPES_KH_USER_ID` / `KH_USER_ID`, via `request_headers_provider`) — KH authorizes via Ory Keto keyed on `x-user-id`, so without it every call was 401 (`auth=none`). Also passes an optional bearer token (`JAPES_KNOWLEDGE_HUB_TOKEN` / `KNOWLEDGE_HUB_TOKEN`). Unset = unchanged. (The `x-user-id` user must have Keto project access to the target collections.)
- **Fixed** — `LLMManager` now infers the provider from the model name when no `provider=` is given (a `claude-*` model routes to Anthropic, a `gpt`/o-series to OpenAI) instead of always falling back to `default_provider` (= openai). This was the anthropic dev-daily failure: a direct `LLMManager().run(model="claude-…")` sent claude to OpenAI. Explicit `provider=` and task routing still take precedence.
- **Tests** — added provider boundary-contract tests (assert the model/`service_tier`/token params we actually send — catches this class without live calls), provider-routing tests (model→provider inference), and an opt-in live smoke test per provider (`RUN_LIVE_LLM=1` + key; cheap nano/haiku model, tiny prompt).

## [1.8.3] - 2026-06-13

- **Added** — `jazzx_sdk.platform_catalog`: the reusable-substrate inventory (13 cognitive modes grouped by faculty, experts derived from `EXPERT_REGISTRY`, 5 fabric surfaces, 13 canonical objects) for UIs/docs to render instead of hand-maintaining drift-prone lists.
- **Changed** — `ExecutionKind` now describes a step's *intended wiring* only: `live` / `deterministic` / `offline_asset` / `integration`. Dropped `stubbed` / `mock` — whether a step ran as a stub in a given environment is a property of that run's trace, not of the conductor design.

## [1.8.2] - 2026-06-12

- **Added** — `jazzx_sdk.evaluation.load_run_history` / `RunHistory`: aggregate a pack's eval runs over time, sliceable by run `labels` (model, prompt_version, dataset, …). Runs now carry `labels` (from `EvaluationConfig`).
- **Added** — `jazzx_sdk.conductor`: declarative `ConductorPipeline` descriptor (steps, canonical-object lineage, execution kind, sub-actions, loop groups) + `BaseConductor.describe()` contract. Static counterpart of `CanonicalTrace`; one source for the conductor diagram instead of a hand mirror. Execution stays pack-defined.
- **Added** — `jazzx_sdk.pack.Pack`: access object for a domain behind one handle. Authored half — policies → `PolicyRegistry`, conductor → `ConductorPipeline`, ontology, playbooks (via manifest `policies.registry` / `conductor.pipeline` pointers). Runtime half — `pack.bind(runtime)` then `record()` / `trace(id)` / `case(id)` / `case_context(id)` / `traces()` / `cases()` / `case_contexts()` / `live_policies()` / `runs(dir)` for the audit traversal. Distinct from the canonical `DomainPack` governance record (composed, not merged).
- **Added** — `TraceStore.list` / `CaseFileStore.list` / `CaseContextStore.list` (`pack_id=…`) — pack-scoped listing (mirrors `list_policies`).

## [1.8.1] - 2026-06-12

- **Added** — `jazzx_sdk.finance`: `FinancialSpread` schema + Excel/CSV export (reusable spreading; `[finance]` extra for openpyxl).
- **Added** — `jazzx_sdk.tools.financial`: credit-metric computations (complements `ratio_evaluator`).
- **Added** — `PackManifestLoader` metadata accessors.
- **Added** — KH URL also reads the platform's `KNOWLEDGE_HUB_URL` (prefers `JAPES_KNOWLEDGE_HUB_URL`).
- **Added** — Streamlit launcher reverse-proxy env: `JAPES_UI_BASE_URL_PATH` / `JAPES_UI_BEHIND_PROXY` / `JAPES_UI_EXTRA_ARGS`.
- **Added** — launch-time startup self-check (mode, KH URL + connectivity, provider keys, UI flags).
- **Fixed** — mode schemas migrated off deprecated `pydantic.generics.GenericModel` to pydantic-v2 native generics.
- **Changed** — dependency specs use `>=` floors instead of `^` caps.

## [1.8.0] - 2026-06-12

Structured-output contract: providers return a validated instance or raise `StructuredOutputError`. OpenAI 3-tier negotiation (fixes broken native output), Anthropic native tool-use; new `jazzx_sdk/llm/structured.py`.

## [1.7.2] - 2026-06-12

`EvaluationHarness(case_detail_fn=...)` + `CaseResult.case_detail`: optional per-case snapshot (hypotheses/evidence/decision) for eval UIs.

## [1.7.1] - 2026-06-12

Moved `jazzx_sdk.fabric.pack` → top-level `jazzx_sdk.pack` (back-compat shim kept); added `PackManifestLoader`.

## [1.7.0] - 2026-06-11

`fabric.docs` named collections + content-hash dedupe; `fabric.kh_status()` connectivity probe.

## [1.6.9] - 2026-06-11

`serve()` / `launch_streamlit()` — one `JAPES_RUN_MODE` entrypoint (queue/server/ui); `jazzx_sdk.ui.get_client_layer()` for Streamlit.

## [1.6.8] - 2026-06-11

Document tools: `convert_document()` faithful router (scanned detection, table extraction); `ratio_evaluator.evaluate_value()` / `evaluate_covenant_policy()`.

## [1.6.7] - 2026-06-09

KG consolidation: `fabric.graph` is the one KG surface (triple CRUD, agent tools); offline Mock backs graph/canonical/rag/policy; removed legacy `*KGStore`.

## [1.6.6] - 2026-06-09

Closed the last `fabric.*` gaps that forced callers to `fabric.kh`: `fabric.docs.retrieve` / `download`, and `fabric.graph.update_ontology` / `delete_ontology` / `upload_ontology`.

## [1.6.5] - 2026-06-08

- **Added** — `fabric.graph` is the complete KG/triple/ontology entry point: `delete_triple`, `list_ontologies`, `resolve_ontology`; collection/ontology defaulting on `KGStore` (env `KH_COLLECTION_ID` / `KH_ONTOLOGY_ID`, per-call override, clear error if unresolved).
- **Fixed** — `KGStore.add_triple` delegates to `create_triple` (was a stale stub); `register_ontology` / `get_ontology` repointed to the real ontology API (id, not name; no `version` arg).
- **Note** — The KG is entity-backed (`entity_type="triple"`); Fuseki/RDF in the KH repo is inert leftover.

## [1.6.4] - 2026-06-08

Platform gaps surfaced by the C&I pack build (additive, backward-compatible):
- OpenAI provider selects `max_completion_tokens` vs `max_tokens` per model (gpt-5.x/o-series/flex were broken).
- `Context` loop methods (`apply_hypothesis_update`, `add_evidence`, `apply_verifier_report`, `pending_*`) on the base class; `BaseToolRegistry.execute(evidence_type, query_params) -> Evidence`; `CanonicalTrace.for_pack(...)`.

## [1.6.3] - 2026-06-07

Canonical schema consolidation + DomainPack v1.5 manifest, freeze-prep for v1.5 contracts:
- DomainPack v1.5 manifest minimums (per-mode registry/matrix versions; fail-closed for CERTIFIED packs); `DomainPackHelper.from_yaml()`.
- `TransactionContext` / `TransactionStatus` (single-pass operational contract) + `InvestigationContext` alias for `Context`.
- Single source of truth for `Attestation`/`Freshness`/`Outcome` (re-exported from `fabric.canonical`); TraceStep observability fields documented.

## [1.6.2] - 2026-06-06

Evaluation Framework (Phase 3): `EvaluationHarness` / `EvaluationConfig` / `EvaluationResults` / `CaseResult` — systematic L1→L2 execution (sequential/parallel) with metrics and JSON save/load.

## [1.6.1] - 2026-06-06

Evaluation Framework (Phase 2): L3 review infrastructure — `L3Review`, `ReviewAgreement`, `IssueType`, `L3ReviewStorage`, `L3ReviewSummary`, CSV export.

## [1.6.0] - 2026-06-06

Evaluation Framework (Phase 1): golden cases — `GoldenCase[TInput, TExpected]`, `GoldenCaseLoader`, `GoldenCaseValidator` under `jazzx_sdk/evaluation/`. Pydantic v2 patterns.

## [1.5.1] - 2026-06-04

Fabric retrieval modes: `FabricConfig` + `RetrievalMode` (STRICT/CACHED/LOCAL/TEST) with `for_production`/`for_development`/`for_testing` factories; `DocStore` routes by mode; KH client optional for LOCAL/TEST. `DocStore.get(location=)` and `local_dir` deprecated. Backward compatible.

## [1.5.0] - 2026-06-03

**Breaking** — IIF v1.5 Expert/Skill restructure: Governance/Evidence/Investigation move to `jazzx_sdk/skills/`; EXPERT_REGISTRY 6→3; TraceStep frozen; `experts` re-exports skills.

## [1.4.5] - 2026-06-09

**Breaking** — Removed the `jazzx_runtime_sdk` backward-compat alias. `import jazzx_runtime_sdk` now fails; use `jazzx_sdk` (renamed in 1.4.0). Consumers must update imports.

## [1.4.4] - 2026-06-09

Made the `jazzx_runtime_sdk` alias survive wheel packaging (real shim package + meta-path finder mapping every submodule to the same `jazzx_sdk` objects); emits `DeprecationWarning`. (Superseded by 1.4.5.)

## [1.4.3] - 2026-06-03

Schema Spec v1.0 completion: eight derived canonical objects (`CaseContext`, `CanonicalCaseFile`, `ScenarioReport`, `Artifact`, `EngagementPlan`, `AgreementRecord`, `EvaluationReport`, `DomainPack`) + KH-backed stores; TraceStep / CanonicalTrace / OverrideEvent aligned to §5-7. Canonical fabric now 5 core + 8 derived.

## [1.4.2] - 2026-05-31

**Breaking** — Document module consolidation to 2 modules: removed `jazzx_sdk/documents/`; all ops in `tools/documents.py`. `fabric.docs` gains local filesystem storage via `location="local"|"hub"`.

## [1.4.1] - 2026-05-31

Added `fabric.docs` governed document store (5th fabric store; `DocType` vocabulary, `put/get/list/delete`, `MockDocStore`; k9 migrated). **Breaking**: removed duplicate `jazzx_sdk.document/` module.

## [1.4.0] - 2026-05-31

**Breaking** — Package renamed `jazzx_runtime_sdk` → `jazzx_sdk`. Introduced the Knowledge Fabric (`ctx.runtime.fabric`): `canonical`, `graph`, `rag`, `policy` stores + Domain Pack loader (`fabric.pack.DomainPackFabric`). `.knowledge_hub` unchanged.

## [1.3.0 and earlier] - 2025-12 -> 2026-05

Pre-1.4.0 history (package `jazzx_runtime_sdk`, before the `jazzx_sdk` rename) is condensed. That line built the foundation carried forward today: queue/server runtime + Handler + service clients + tracing (1.0.0); the 13-mode cognition framework and operational/EVOLVE modes (0.3.x); canonical objects + `CanonicalObjectStore` (0.2.x); the tool registry and KH tool layer (0.4.x); the expert layer (0.5.0); discovery/workflow tools (0.6.0); and 1.1-1.3 platform services (agents/LLM, documents, connectors, KG store, unified `service_tier`). Full detail in `git log`.
