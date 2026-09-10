# Lifting the pack-store surface out of Plato and into the SDK

Status: plan, 2026-09-10. Nothing moved. Written against japes `d3db880` on `v2.5.1` (unpushed).

Companion to `plan_pack_store.md`, which decides the *schema* and table placement. This one decides
which of the **code** added around that schema is Plato's and which is the SDK's. The two do not
overlap: that plan's §4.5 settles where tables live, and takes as given that some stores are
"SDK-origin" and some are "Plato's own". Nothing there says which side the seeder, the inventory
projection, or the posture gates fall on, and this branch built all three inside `plato/`.

## 1. Why now

`v2.5.1` added ~1,100 lines of Plato code around the pack store: a seeder, an inventory
projection, an operator page, two posture gates, a tenant resolver, and env-driven blob wiring.
Plato is the first consumer of `PackVersionStore`, so everything landed there by default rather
than by decision. Three consequences already visible in this branch's review rounds:

- Two of the session's defects were in `tenancy.py` and `posture.py` — the two files whose logic
  every other japes service will need to write again.
- The one guard in the repo that catches an unrecognised blob backend lives in Plato, protecting
  the library rather than the other way round.
- `plato/seed.py` reached 196 lines with **zero** framework imports, which is the signature of
  code that is in the wrong package.

The window argument from CLAUDE.md applies: japes has few external consumers, so moving a boundary
now costs less than it ever will again.

## 2. What moves, and the evidence

### 2.1 `seed_packs` / `_manifest_of` → `jazzx_sdk/pack/` (strongest)

`plato/seed.py` is 196 lines, imports no framework, and has exactly one `plato` import
(`acting_user_id`, which §2.2 dissolves). It takes a `PackVersionStore` — an SDK type — and a
directory, and publishes one row per pack directory. `pack_archive`, the other half of the job,
moved into `jazzx_sdk/pack/store.py` in this same branch on the argument that the archive shape is
the store's contract; the writer that *calls* it has the same claim.

What stays behind: `default_seed_root()` and `PLATO_SEED_PACKS_DIR`. Where *this* service's bundled
packs live is the service's business; the SDK function should take a root.

The four-bucket result (`published` / `skipped` / `not_packs` / `failed`) moves with it. Its
distinctions were paid for in this branch — conflating the middle two claimed rows existed that
never did — and a second consumer re-deriving them would re-derive that bug.

### 2.2 `acting_user_id` → SDK

A best-effort read of `CallerIdentity.from_context()`, which is already SDK, wrapped in a
`try`/`except` so attribution can never fail a write. Nothing about it is Plato's. It also lost its
underscore this round on reaching two importers, which is the same signal one step earlier.

Moving it is what lets §2.1 move cleanly.

### 2.3 `pack_inventory(store)` → SDK

Pure: store in, dict out, no framework. The subtlety it encodes — `versions()` is `published_at`
order, which is *not* version order, so a backport reads oddly and `last_published_version` is
deliberately not named `latest` — is a fact about `PackVersionStore`, not about a page. A second
operator surface elsewhere would either re-derive it or get it wrong.

The routes around it (`GET`, `DELETE`, `POST .../initialize`), the prefix, the nav entry and
`packs.html` all stay in Plato. Those are the service's own surface.

### 2.4 The unrecognised-backend warning → the `BlobStore` boundary

`BlobStore` dispatches on `self._backend == "azure"` and treats **everything else** as local,
silently. `Fabric.__init__` passes `config.blob_backend` straight through with no check.
`plato/wiring_default._pack_blob` is the only place in the repo that notices `Azure`,
`azure-blob` or `s3` and says so — a consumer protecting the library.

The warning belongs where the dispatch is. Two shapes to choose between:

1. `BlobStore.__init__` warns on a backend it does not recognise. Simplest, catches every caller,
   including `Fabric`.
2. A shared `blob_store_from_env(prefix)` builder that both `Fabric` and Plato call.

Prefer (1) — it is smaller and cannot be bypassed. (2) additionally collapses the
`JAPES_BLOB_*` / `PLATO_PACK_BLOB_*` duplication, but those two are *legitimately* different
stores (a deployment may want pack archives in their own container), so collapsing them is a
separate decision and not obviously right.

### 2.5 `tenant_of`, `relaxed_only`, `withholding`, `withheld`, `require_if_match` → `jazzx_sdk/server/`

The posture *policy* is already SDK: `strict_mode()` and `environment_tier()` live in
`jazzx_sdk.config.envvars`. What sits in `plato/posture.py` and `plato/tenancy.py` is that
policy's HTTP expression, and there is no equivalent in `jazzx_sdk/server/` today (checked:
no tenant resolution anywhere in that package).

Every multi-tenant japes service needs both:

- "resolve this request's tenant, or answer 400 naming what is missing" — and serving an
  unlabelled request as an arbitrary tenant is a cross-tenant read, so the answer must be a
  refusal, not a default.
- "refuse this write outside a relaxed tier".

Both were defect sites this session, which is the argument rather than a coincidence: `tenant_of`
served a Python type name to an unauthenticated caller, missed a `LookupError`-shaped resolver, and
answered a message naming nothing; `relaxed_only` gated on `strict_mode()` and so admitted a
staging write that its own docstring promised to refuse. Three bugs in the code every service is
about to copy.

`check_settings` and `PostureError` stay: `check_settings` refuses a *Plato* start, is called from
`plato/app.py` and `plato/__main__.py`, and reads Plato's own settings object.

## 3. Checked, and deliberately not moving

**The ORM model / migration split is not drift.** `jazzx_sdk/pack/store_db.py` defines
`PackVersionRow` including `retired_at`, while the migration that adds that column is hand-written
in `plato/migrations/versions/0004_*`. That looks like a gap until you read line 14 of the same
file: *"Table DDL belongs in the consuming service's alembic."* It is a considered decision, and
`plan_pack_store.md` §4.5 depends on it (`TABLE_SCHEMAS` gaining a row per table is described as
"the intended forcing function"). Leave it.

## 4. Sequence

Three commits, in this order, each landing on its own review:

1. **Pure moves, no behaviour change** — §2.1, §2.2, §2.3. Re-export from the old paths so nothing
   outside changes, or update the call sites; either way the diff is a move plus imports.
2. **`BlobStore` warning** — §2.4 shape (1). Changes library behaviour for every caller, so it
   wants its own round. `Fabric` picks up the warning by construction, which is the point.
3. **Server-tier posture and tenancy** — §2.5. Largest and the only one touching a governance
   gate, so it goes last and alone.

Not before the `v2.5.1` push. The review in flight is against `d3db880`; moving four boundaries
underneath it invalidates that review and repeats this session's pattern, where each round's fixes
generated the next round's findings.

## 5. What would make this wrong

- **If no second consumer materialises.** Every item here is justified by "the next service will
  need this", and that is a prediction. `juno` and `assistant` are the candidates. If neither
  adopts `PackVersionStore` within a release or two, §2.1 and §2.3 were speculative generality and
  should come back. §2.4 stands regardless — it is a defect in the library, not a generalization.
- **If Plato's page needs its own inventory shape.** §2.3 assumes one projection serves every
  operator surface. A second surface wanting different fields turns the SDK function into a
  parameterised one, which is worse than two small local ones.
- **If `jazzx_sdk/server/` is the wrong tier for §2.5.** It imports FastAPI, so anything landing
  there is server-mode only, per the three-tier split. That is correct for these five functions,
  but it does mean a queue-mode consumer gets nothing from the move.
