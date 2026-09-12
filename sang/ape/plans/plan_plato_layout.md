# Giving `plato/` a folder hierarchy

Status: plan, 2026-09-11. Nothing moved. Target 2.5.2. Written against japes `a3ea206` on `v2.5.2`.

## 1. What is there now

27 modules and 6,171 lines flat at the top of `plato/`, plus six subdirectories that already exist
for other reasons. The flat part is the problem: eight of those modules are HTTP routers that only
`app.py` composes, and they sit beside the entry point, the ORM models and the auth code with
nothing in the layout saying which is which.

Two directory names are also actively confusing:

| Directory | What it is |
|---|---|
| `migrations/` | the alembic tree (this repo's only one) |
| `migration/` | a strangler that reads kernel rows and writes the Plato equivalent |

Singular and plural, adjacent, unrelated. Nothing about the names distinguishes a schema migration
from a data migration off another service.

## 2. The one constraint that shapes everything

`PLATO_WIRING` is a **deployment-set environment variable naming a module path**:

```
PLATO_WIRING=plato.wiring_default:build
```

That string lives in an ACA configuration this repository cannot edit, and in
`docs/DEPLOYMENT_ENV.md`, `scripts/plato-local.sh`, `scripts/README.md` and `plato/guide.md`.
Moving `wiring_default.py` renames a value someone else has already set.

It fails loudly rather than silently -- `load_wiring` raises `WiringError`, a job exits 4 and a
serving replica comes up on `/info` with the reason, which is exactly what the boot contract is
for -- but it fails, on deploy, for every deployment at once.

So the wiring modules are not free to move, and that is the only part of this that is not
mechanical. Everything else is imports inside this repo.

## 3. Proposed layout

```
plato/
  __init__.py  __main__.py  _version.py  app.py     entry and composition
  runtime.py  models.py  schemas.py  jobs.py  seed.py  prefix.py
  api/         assistants  config  database  feedback  info  logs  metrics  packs
  boot/        contract  posture  schema_version
  auth/        oidc  tenancy
  wiring/      (see §4)
  packs/       unchanged
  reference/   unchanged
  kernel_sync/ was migration/
  migrations/  unchanged (alembic.ini points here)
  data/  static/  guide.md  alembic.ini
```

Ten modules stay at the top, which is the set a reader opening `plato/` should see first: how it
starts, how it composes, what it serves, and its own types.

**`api/`** is the biggest single win: eight files, 1,828 lines, imported by `app.py` and their own
tests and nothing else. Dropping the `_api` suffix on the way in (`api/assistants.py`) is the point
of the folder; `api/assistants_api.py` would keep the stutter the folder exists to remove.

**`boot/`** collects what `plato/__main__.py` consults before serving: the contract table, the
posture gates, the schema check. `boot_contract.py` becomes `boot/contract.py` for the same reason.

**`auth/`** is `oidc.py` (464 lines, one importer) and `tenancy.py` (154, seven). Both answer "who
is calling", and `tenancy.py` is one of the two files `plan_plato_to_sdk_lift.md` §2.5 wants lifted
into `jazzx_sdk/server/` later -- a folder makes that lift a directory move rather than an
archaeology exercise.

**`kernel_sync/`** renames `migration/`. The collision with `migrations/` is the whole reason; if
`kernel_sync` is wrong, anything that is not a near-homograph of the alembic directory will do.

## 4. The wiring decision, which is yours

Three options, and they differ in what a deployment has to do.

**A. Leave `wiring*.py` at the top level.** No deployment touches anything. The top level keeps
four files it would rather not have, and the layout says nothing about the fact that
`wiring_default` and `wiring_local` are two implementations of one contract. Cheapest and safest.

**B. Move, with a re-export shim.** `plato/wiring/{contract,default,local,settings_store}.py`, and
`plato/wiring_default.py` survives as three lines re-exporting `build`. Old `PLATO_WIRING` values
keep working, the layout is right, and the shim is deleted a release later once deployments have
moved. Costs two files that exist only to be deleted, and somebody has to actually delete them.

**C. Move, no shim.** Correct layout immediately, and every deployment must update `PLATO_WIRING`
in the same release. Only defensible with a coordinated deploy, and Plato is at 0.1.3 with few
deployments, so it is not absurd -- but it is a flag day.

**Recommendation: B**, because the shim is small, the deletion is a one-line follow-up, and the
alternative is either a permanent wart (A) or a flag day (C) for a layout change. If there is
exactly one deployment and we control it, A becomes less attractive and C becomes reasonable.

## 5. Cost, measured

Import sites per module, counted across `plato/`, `tests/` and `scripts/`:

| Module | Files importing |
|---|---|
| `posture` | 11 |
| `wiring` | 9 |
| `wiring_default` | 8 |
| `tenancy` | 7 |
| `config_api`, `info_api` | 6 each |
| `settings_store` | 5 |
| `schema_version` | 4 |
| `database_api`, `logs_api`, `metrics_api` | 3 each |
| the rest | 1-2 each |

Nothing above single digits. The whole move is roughly 80 import statements, every one of them
inside this repository, and the test suite covers the result.

## 6. Sequencing

Each step is its own commit, and the suite must pass between them.

1. **`kernel_sync/`** -- rename only, 2 files, settles the `migration`/`migrations` collision.
2. **`api/`** -- 8 files, the largest reduction, no external names.
3. **`boot/`** and **`auth/`** -- 5 files between them.
4. **`wiring/`** -- only after §4 is decided, and carrying whatever shim that decision implies.

Steps 1 to 3 are unblocked and independent of the wiring question.

## 7. What would make this wrong

- **If `plato` is about to be split to its own repository.** `plato/__init__.py` says a split
  should stay "a mechanical `git filter-repo`", and that is true of a subtree whatever its internal
  shape, so this does not obstruct it. Worth confirming the split is not imminent, because doing
  both at once turns two mechanical changes into one confusing one.
- **If more than a handful of deployments set `PLATO_WIRING`.** That turns option C from a flag day
  into an outage and makes the §4 recommendation firmer, not softer.
- **If the folders get deeper than one level.** `api/` holding eight flat modules is the point.
  `api/routers/assistants.py` would be the same clutter one directory down.
