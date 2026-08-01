# Plan — DB & blobs behind `fabric`

Goal (Veeru): **hide `common.core.db` behind `fabric`; everyone goes through fabric even for their
own service schemas.** Plus **blob offloading** (large values → blob storage, DB keeps a pointer).

## Principle
`fabric` is the single entry to persistence. A service still **owns its schema** (defines its
SQLModel models + alembic chain), but gets the **session, engine, placement, and blob offloading**
from fabric — it never imports `common.core.db` / `common.core.storage` directly. Placement (pg via
common.core.db, sqlite for local/test, blob provider) is a fabric detail, exactly as
`fabric.conversation` already hides its backend (`in_process`/`local`/`sql`).

## Current state
- `common.core.db` — thin async wrapper: `get_async_engine`, `async_session_factory`,
  `get_async_session`; config = env `DB_ASYNC_CONNECTION_STR`; SQLModel mixins.
- `common.core.storage` — `AsyncAzureBlobStorageProvider` (`upload_blob`/`download_blob`/`delete_blob`).
- **Precedent**: `fabric.conversation`'s `SqlConversationStore` already fronts `common.core.db`
  (lazy `async_session_factory`, owns its DDL via `.metadata`, service points alembic at it). This
  plan *generalizes that one-off* into a first-class surface.
- No generic `fabric.db` / `fabric.blob` exists yet.

## Design

### `fabric.db` — relational surface
- **`fabric.db.session()`** → async context manager yielding an `AsyncSession` (fronts
  `common.core.db.async_session_factory`; injectable sessionmaker for tests / sqlite). Services stop
  importing `common.core.db.get_async_session`.
- **`fabric.db.register_metadata(md)` + `fabric.db.metadata`** — services register their SQLModel
  `MetaData`; fabric aggregates so alembic `target_metadata = fabric.db.metadata` and
  `create_all()` (local/test) go through one place.
- **`fabric.db.repository(Model)` → `Repository[T]`** (optional but high-value): generic typed CRUD
  over a SQLModel — `get/create/update/delete/list` — so services stop hand-rolling session
  boilerplate. Mirrors `fabric.entities` but for the service's *own* relational tables (vs KH JSONB).
- Placement via `FabricConfig`: `db_backend = common` (default, common.core.db) | `sqlite`
  (local/test, no server) — matches the conversation-backend pattern.

### `fabric.blob` — blob surface
- **`put(data, *, key=None) -> pointer`**, **`get(pointer) -> bytes`**, **`delete(pointer) -> bool`**
  over `common.core.storage` (Azure) with a **local-fs backend** for dev/test (fabric pattern).
- Pointer = an opaque `blob://<container>/<key>` string stored in the DB.

### Blob offloading
- **`fabric.blob.offload(value, *, threshold_bytes) -> value | {"__blob__": pointer}`** and
  **`fabric.blob.materialize(value) -> value`** — a large value is pushed to blob and replaced by a
  pointer ref; materialize resolves it back. Opt-in helper (not magic).
- Later (if wanted): a SQLModel `OffloadedJSON` column type that auto-offloads on write / materializes
  on read, so a table field transparently spills to blob past a threshold. Deferred — helper first.

## Phasing
1. **`fabric.db` core** — `session()` + `register_metadata`/`metadata` + `FabricConfig.db_backend`
   (common | sqlite). Migrate `SqlConversationStore` to use `fabric.db.session()` (dogfood the one
   existing consumer). Tests on sqlite (no server).
2. **`Repository[T]`** — generic typed CRUD; test on sqlite with a sample model.
3. **`fabric.blob`** — provider surface + local-fs backend; tests on local-fs.
4. **Offload helpers** — `offload`/`materialize`; test round-trip on local-fs. (Column type deferred.)

Each phase is its own commit; Phase 1 is the bounded unblocker.

## Open decisions (for review)
- **D1 Surface shape**: full `fabric.db` (session + metadata + Repository) vs minimal (session +
  metadata only, no Repository). Recommend full — Repository is where the client-code savings are.
- **D2 Local/test backend**: sqlite (real SQL, no server — best for tests) vs in-memory dict.
  Recommend sqlite.
- **D3 Scope now**: implement Phase 1 after alignment, or plan-only.
- **D4 fabric availability**: `fabric.db`/`fabric.blob` need config even in LOCAL mode (they're not
  KH-backed). Default to sqlite + local-fs so `local_fabric()` has them without a server.
