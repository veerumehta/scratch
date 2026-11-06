# plan_2_7_0_tenancy_hardening - keep the string tenant, harden its keys, add one name-to-UUID resolver at the boundary

Repo: `japes`. Owner: sonnet-runtime. Status: scoped, nothing built.

Author: Virendra Mehta. Written against `v2.6.9` (`2066c67d`, the tree equal to `origin/plato` plus the scorer-context commit), 2026-11-06. Decision applied (the user's, relayed by opus-xrepo): tenancy option C. The SDK
keeps the free-form string tenant (`DEFAULT_TENANT = "default"`, `jazzx_sdk/identity.py:16`), hardens it now, and adds one tenant name to UUID resolver used only where code crosses into `common`
or a sibling service. Full adoption of `common`'s UUID model and `DB_TENANCY_MODE` waits until `common` 0.4.0 is rebased and tagged and a consumer needs it.

What I read versus inferred is marked throughout. "Read" means I opened the file or ran the introspection and saw it; "inferred" is reasoning from what I read. No migration was run, no row count was
measured (none is available here), and nothing was changed.

## TLDR

- There are 54 store tables. 47 are Plato's (`plato/models.py` `register_all`); 7 are SDK-only and carry no tenant at all. Read, by introspecting the live metadata of every registered store plus a grep of
  every `__tablename__`.
- Of Plato's 47, every table has a NOT NULL `tenant_id` column. 21 lead their primary key with it, 5 hold it in the key but not first, and 21 hold it only in a unique constraint (their primary key is a
  surrogate id or a global natural id). The five natural-id primary keys the user named are the real exposure; the other 16 in that group are surrogate ids with a tenant-leading unique twin.
- Seven tables need a column and a backfill: `agent_definition`, `japes_queue_execution`, `conversation_message`, `conversation_overlay`, `materialize_manifest`, `automation_idempotency`, `cost_record`.
  The user's list named three families; the family is seven tables.
- No foreign key exists anywhere in the SDK or Plato (read: `grep ForeignKey` finds nothing), so changing a primary key touches the table and its stores and nothing else.
- Five migrations, each stoppable, ordered by risk. About 700 lines of change in all, half of it tests.
- The resolver is one small module. At the `common` boundary the UUID is assigned by the platform, so a deterministic `uuid5` cannot match it; the mapping has to come from config or a table.

## 1. Hardening

### 1.1 The inventory (every store table, its key shape, read from the live metadata)

`PK` is the primary key in column order. "Tenant-leading" means `tenant_id` is the first PK column. Counts: 21 leading, 5 in-key-not-leading, 21 unique-only, 7 absent (54).

**A. Tenant-leading primary key (21). No change.**
`assistant_conversation`, `blueprint`, `blueprint_member`, `blueprint_pin`, `document_record`, `eval_baseline`, `eval_judge_cache`, `eval_subject_baseline`, `guidance_asset`, `guideline_version`,
`japes_feedback`, `japes_feedback_config`, `japes_request_idempotency`, `japes_turn_cost`, `pack_alignment`, `pack_lint_triage`, `pack_version`, `plato_setting`, `prompt_alias`, `proposal`, `proposal_comment`.

**B. Tenant in the primary key, not first (5).**

| Table | PK now | Tenant-leading unique twin |
|---|---|---|
| `agent_session` | `(session_id, tenant_id)` | `uq_session_tenant_session (tenant_id, session_id)` |
| `turn_run` | `(run_id, tenant_id)` | `uq_turn_run_tenant_run` |
| `turn_run_event` | `(run_id, tenant_id, seq)` | `uq_turn_run_event_tenant_run_seq` |
| `conductor_suspension` | `(suspension_id, tenant_id)` | none |
| `japes_policy_extraction_run` | `(run_id, tenant_id)` | none |

**C. Tenant only in a unique constraint; the primary key has none (21).**

*C1, natural id as the whole primary key (the real exposure, 6 tables).* Two tenants cannot hold the same id, and `s.get(Row, id)` reaches across tenants unless the store adds the tenant filter itself.

| Table | PK now | Unique twin today |
|---|---|---|
| `eval_dataset` | `dataset_id` | `uq_eval_dataset_tenant_name (tenant_id, name)` |
| `eval_custom_scorer` | `scorer_id` | `uq_eval_custom_scorer_tenant_name (tenant_id, name)` |
| `eval_optimization_job` | `job_id` | `uq_eval_optimization_job_tenant (tenant_id, job_id)` |
| `eval_experiment` | `experiment_id` | `uq_eval_experiment_tenant (tenant_id, experiment_id)` |
| `config_audit_event` | `event_id` | `uq_config_audit_tenant_event (tenant_id, event_id)` |
| `eval_case_run` | `(experiment_id, case_id)` | `uq_eval_case_run_tenant (tenant_id, experiment_id, case_id)` |

`eval_case_run` is not in the user's list; it is the sixth member of the family (a case run's key has no tenant either).

*C2, surrogate integer or opaque id as the primary key, tenant-leading unique twin present (15 tables).*
`assistant_manifest_record` (`seq`), `catalog_reference` (`id`), `document_reference` (`id`), `eval_custom_scorer_revision` (`id`; also the legacy `uq_eval_custom_scorer_revision`), `eval_dataset_version` (`id`; also
the legacy `uq_eval_dataset_version`), `japes_feedback_history` (`id`), `model_overlay` (`seq`), `pack_activation` (`id`), `pack_comment` (`id`), `pack_draft` (`id`), `pack_draft_event` (`id`), `pack_draft_file`
(`id`), `pack_lint_run` (`id`), `pack_review` (`id`), `prompt_version` (`id`). The surrogate is a global autoincrement; the tenant-leading unique key already makes the natural identity per tenant.
Recommendation: leave these as they are (open question 1).

**D. No tenant column at all (7, SDK-only, not registered by Plato).**

| Table | PK now | Store | Notes (read unless marked) |
|---|---|---|---|
| `agent_definition` | `name` | `agents/definition_store_db.py` | the `schema_version.py` header says its DDL belongs to the consuming service's alembic |
| `japes_queue_execution` | `key` | `queue/execution_db.py` | `purge_completed` deletes by status and age with no tenant filter (`:289`) |
| `conversation_message` | `id` (autoincrement); `session_id`, `seq` unindexed together | `fabric/conversation_store.py` | |
| `conversation_overlay` | `session_id` | same | |
| `materialize_manifest` | `(scope, doc_id)` | `fabric/docs/manifest_store_db.py` | `scope` may already carry a tenant-like value (inferred, not read) |
| `automation_idempotency` | `idempotency_key` | `automation/idempotency_db.py` | |
| `cost_record` | `id` (autoincrement) | `llm/cost_store_db.py` | has `user_id`, `project_id`, `trace_id`; Plato uses `japes_turn_cost` instead (inferred: `cost_record` is not registered) |

Plato never registers these seven, so `plato/migrations` has no DDL for them (read: `register_all`, and the migration list `0001` to `0036`; note `0018_pack_draft_event` exists, so numbering has no gap). A host that
uses them owns their DDL (read: `schema_version.py` says so for `agents.definition` and `llm.cost`).

**Not audited.** Whether every query of every store filters by tenant. I read `runs/store_db.py` (every query carries `tenant_id == self._tenant_id`, `:194` onward), `conductor/suspension_store_db.py` and
`evaluation/datasets_db.py`; I did not read the rest. The KH-backed canonical stores (`fabric/canonical/store/*`) take no tenant parameter (read: their constructors take only the KH client); how a tenant reaches
them is not something I traced. Row counts per table in any deployment: unknown.

### 1.2 `TODO(tenant-keyed-store-reads)` in `fabric/tenancy.py:107` is partly stale

It says `runs/store*.py` keeps a run's tenant only in its input JSON and lists `conductor/suspension_store*.py`, `queue/execution_db.py`, `llm/cost_store.py` and "the fabric stores". Read: `turn_run` and
`turn_run_event` carry `tenant_id` as a column and a key, every `runs/store_db.py` query filters by it, and `conductor_suspension` keys on `(suspension_id, tenant_id)`. What is still true is exactly group D
(`japes_queue_execution`, `cost_record`, the conversation tables, `materialize_manifest`, `automation_idempotency`, `agent_definition`). The resolution is migration M4 below plus rewriting the marker to
name whatever remains (the canonical KH stores, not audited). The in-memory `runs/store.py` I did not read.

### 1.3 The guard test

`tests/test_plato_tenancy.py::test_platos_own_tables_comply` (`:103`) runs `verify_tables` over `register_all` (47 tables). The rule it enforces (`fabric/tenancy.py:5`, "`tenant_id` is in the primary key or a
unique constraint") passes all 21 of group C, so it cannot see C1, and it does not see group D because those tables are not registered. The module docstring and the test's own docstring ("Every table Plato
registers keys on the tenant") describe the weak rule as if it were the strong one. I could not pin which docstring the 2026-11-05 note called stale; these two are the candidates.

Replace it with a test over every store table (registered or not) that fails when:
1. a table has no `tenant_id` column, unless it is on a named exemption list with a reason (the planned `tenant_directory`, and any deployment-wide table);
2. a table whose primary key is a natural id (a non-integer column) lacks `tenant_id` in the primary key;
3. a table has a `tenant_id` column that is nullable.
Enumerate the stores through one list that `register_all` and the seven SDK-only stores both feed, so a new store joins it (the family is the unit). Fix the two docstrings to state the rule actually enforced.

### 1.4 Migrations, ordered by risk. One migration per family, each stoppable (a stop leaves a consistent schema)

The next revision is `0037`, `down_revision = "0036_eval_subject_baseline"`. Migrations use `op.batch_alter_table` (read: `0013`), which recreates a table on sqlite and alters in place on Postgres. Line
estimates include the migration, the model edits, the store edits and the tests that fail on the old shape.

| # | Migration | Tables | Data risk on existing rows | Lines (est.) | Test that fails on the old shape |
|---|---|---|---|---|---|
| M1 | `0037_drop_legacy_unique_keys` | `eval_dataset_version` (`uq_eval_dataset_version`), `eval_custom_scorer_revision` (`uq_eval_custom_scorer_revision`) | None. It loosens a constraint; the tenant-leading twin (`uq_*_tenant`) stays, so the same `(dataset_id, version)` can exist in two tenants. Until M2 the global id key still blocks that. | 30 migration, 4 model, 40 test: about 75 | two tenants, one dataset id and version each: the second insert succeeds after M1 and M2, fails before |
| M3 | `0038_tenant_first_in_keys` | `conductor_suspension`, `japes_policy_extraction_run` (the two with no leading twin); the other three of group B keep their twins | None for duplicates (the new key is a permutation). Postgres rebuilds the key index. | 45 migration, 6 model, 40 test: about 90 | introspect the key order |
| M2 | `0039_tenant_leading_natural_keys` | the six of C1 | No duplicates are possible (the old primary key was unique on fewer columns). No nulls (`tenant_id` is NOT NULL on all six, read). `tenant_id` is `"default"` on rows written by an unconfigured store, which stays what it was. Operational risk: Postgres takes an exclusive lock for the key rebuild, longest on `eval_case_run` and `config_audit_event` (the two likely large; inferred, no counts). The now-redundant `uq_*_tenant` twins can be dropped in the same revision or kept. | 70 migration, 25 model, 30 store (every `s.get(Row, id)` becomes `s.get(Row, (tenant, id))`), 80 test: about 205 | a second tenant creates the same `experiment_id` or `dataset_id` and is not refused; a store for tenant B cannot read tenant A's row by id |
| M4 | `0040_tenant_for_unregistered_stores` | group D, 7 tables | Highest. Existing rows have no tenant. They are backfilled to one value; if the deployment's real tenant is not `"default"`, reads by the real tenant miss every old row. See open question 2. Primary keys become `(tenant_id, <old key>)`. | per table 8 model plus 6 store: about 100; migration plus backfill helper 70; test 90: about 260 | a store for tenant B does not see tenant A's rows, and the purge of one tenant leaves the other |
| M5 | no migration: the guard test of 1.3, flipped to enforcing after M2 and M4 | all | None | about 70 | the test is the new check |

Order to ship: M1, M3, M2, M4, then flip the guard (M5). M1 and M3 are the safe warm-ups; M2 and M4 are where a deployment can be hurt. M4 is where the SDK, which has no alembic tree of its own, hands
hosts DDL: ship the backfill and the `CREATE`/`ALTER` as a documented function plus a boot-time `SchemaVersion` check (read: `schema_version.py` already exists for exactly this), not as a Plato migration,
because Plato does not own these tables.

Total: about 700 lines, about 350 of them tests.

### 1.5 Interaction with item 29 (clear logs by range and type)

- A range purge deletes by `(tenant, created_at)` and type. After M2 the audit, case-run and experiment tables are tenant-scoped by key, so a purge cannot touch another tenant's rows even if a caller forgets
  the filter. None of these tables has an index leading with `tenant_id` then a time column (read: each has a single-column `index=True` on `tenant_id`); a purge on a large table wants `(tenant_id, created_at)`.
  Add it in the purge work, not here.
- `japes_queue_execution.purge_completed` and `cost_record` have no tenant column today, so a per-tenant purge of them is impossible. M4 must land before item 29 offers those types, or they are excluded.
- `config_audit_event` is a governance record in item 29's scoping (audit is deleted only on explicit opt-in). M2 changes its primary key; the purge code should be written against `(tenant_id, event_id)`.
- `eval_case_run` and `turn_run_event` are the log-like tables by volume (inferred). Their keys are `(experiment_id, case_id)` and `(run_id, tenant_id, seq)`; M2 and M3 are what make a per-tenant range delete safe on them.

### 1.6 Interaction with the Expert trace and attestation keys

None on the schema. An Expert answer is traced as a canonical Trace object in Knowledge Hub, with the tenant in `metadata[TENANT_KEY]` (read in `expert_api.py` and `plato/api/experts.py`, inferred for
the storage), not in any of these tables. The attestation key is per deployment from the environment (`PLATO_EXPERT_ATTESTATION_KEYS`, read), so no table holds it. A future per-tenant attestation key (the
Expert plan's D1) would need a keyed store; build it tenant-leading from the start, and it joins the guard test's list.

### 1.7 What these keys cost a later UUID move

Small, and mostly mechanical, because the keys are already tenant-leading:
- One migration per table converts `tenant_id` from string to UUID using the resolver's table as the mapping (`UPDATE ... FROM tenant_directory` then `ALTER COLUMN ... TYPE uuid`). Keys, unique constraints and
  indexes keep their shape, and there are no foreign keys to cascade (read). Postgres can do the type change with `USING`; sqlite recreates the table.
- Each store's default changes from `DEFAULT_TENANT` to a UUID; each `tenant_id: str` annotation changes; the stores that take a tenant string at construction take a UUID.
- Without this plan the same move would also have to design the keys for 27 tables (C1, D, and the 21 of C), so it would be a redesign instead of a type change.
- What it does not remove: RLS and `TenantAwareSession` from `common` (a separate program), and the headers and tokens, which the resolver covers.

## 2. The resolver

### 2.1 Where the boundary calls are today (read unless marked)

| Point | Where | What crosses |
|---|---|---|
| `common` request context | `common/middleware/request_context.py` (the checked-out submodule is `v0.3.0-1`, `5fa4775`, which is the recorded gitlink) | the verified context token carries `tid` and `stid`; `PLATFORM_TENANT_ID` (alias `IDENTITY_TENANT_ID`) is the deployment's platform tenant; `_same_tenant` compares them as UUIDs (`:444`). These are platform-issued UUIDs |
| SDK principal source | `authority/principal.py:56-84` | a token claim named by `tenant_claim` (default `"tenant"`) is compared by string equality to the request's tenant name (`:73`) and refused as 403 if different. If the claim carries a UUID this compares a UUID with a name |
| Invocation context | `authority/context.py:141` `tenant_ref`; `require_tenant` `:336` (called nowhere by default) | a free string |
| Queue messages | `queue/processor.py:119`, `server/app.py:315` read `message.context["tenantId"]` and pass it as the tenant | sibling services send `tenantId`; its form (name or UUID) is not something I read (inferred: a UUID) |
| Outbound to Kernel and Knowledge Hub | `client_layer.py`, `clients/*` | identity headers and scope claims only; no tenant header (read: `grep tenant` over `clients/` and `client_layer.py` finds none). The Knowledge Hub has no tenant concept (the 2026-11-05 note) |
| Feedback sink to a Plato | `evaluation/feedback/sink.py:117` `X-Tenant-Id` | the SDK's own namespace; no UUID needed |
| Plato ingress | `plato/wiring/default.py:523` reads `X-Tenant-Id` (a name), refuses its absence when deployed | the SDK's own namespace |

So the crossing points are three: the token claim at `authority/principal.py`, the queue message `tenantId`, and any future `common` data-layer call. None exists as a UUID to name today except the token claim.

### 2.2 Module

`jazzx_sdk/fabric/tenant_directory.py` (or `jazzx_sdk/tenant_directory.py`; it must import nothing from the SDK, like `identity.py`, so import-linter keeps it in the bottom tier), about 90 lines:

```python
class TenantDirectory(Protocol):
    def uuid_for(self, name: str) -> UUID: ...        # LookupError when the name is unknown
    def name_for(self, tenant: UUID | str) -> str: ...  # LookupError when the UUID is unknown
```

with one implementation over a mapping validated at construction (bijective, no duplicate UUID or name, names trimmed the way `tenant_from_request` trims them). Unknown is a `LookupError`, which
`tenant_of` already turns into a 400; a request never silently falls back to `"default"`. About 80 lines of tests.

### 2.3 The mapping source

| Source | For | Against |
|---|---|---|
| Config (an env variable holding a JSON object, or a file path) | Explicit, reviewable, no migration, matches how `TENANTS_ENV` already lists the deployment's tenants (read: `plato/wiring/default.py:42`, `PLATO_TENANTS`). Can hold the platform-issued UUIDs, which is the only thing that interoperates with `common` | Drift between the platform's registry and ours; edited by hand; a new tenant needs a config change and a restart |
| A table (`tenant_directory(name, uuid, created_at)`) | Self-service, queryable, one source for the purge and for a UUID migration | A migration and a bootstrap; the table is itself global, so it is on the guard test's exemption list; one more thing a deployment must populate |
| Deterministic `uuid5(fixed_namespace, name)` | No state; the same name always gives the same UUID; reverse needs only the known names | The UUID is invented by us. At the `common` boundary the UUID is issued by the platform (`PLATFORM_TENANT_ID`, token `tid`), so it will not equal ours. It works only for ids that stay inside the SDK, which is not the boundary this module is for. Renaming a tenant changes its UUID |

Recommendation: config first, behind the Protocol, so a table-backed directory can replace it with no caller change. `uuid5` only as a fallback for an internal synthetic id, never for a platform tenant.

### 2.4 What must stay unaware of it

Every store and every `fabric.db` model, `runs`, `evaluation`, `pack`, the Plato routes and `tenant_from_request`, the KH-backed canonical stores and the guard test: all keep the string. Only
`authority/principal.py` (the claim comparison), the queue message ingestion (`queue/processor.py`, `server/app.py`) and a future `common` bridge import the directory. A test enforces this by import: nothing under
`fabric/` or `pack/` or `evaluation/` imports it (an import-linter contract, a few lines).

## 3. What not to do now

1. Do not change the type of `tenant_id` anywhere; that is the UUID migration of 1.7.
2. Do not adopt `DB_TENANCY_MODE`, `TenantAwareSession`, RLS or the workspace and sub-tenant headers; they depend on `common` 0.4.0, which is not tagged.
3. Do not add foreign keys. There are none, and the hardening does not need them.
4. Do not convert the 15 surrogate-key tables of C2 unless the user decides they should be (open question 1); they are safe as they are.
5. Do not backfill group D by guessing a tenant in a deployed posture (open question 2).
6. Do not make the resolver global or mandatory: a deployment with no mapping must run as before.
7. Do not rewrite stores to take a UUID. Do not rename `X-Tenant-Id` or send a tenant to Knowledge Hub or the Kernel.
8. Do not drop the `uq_*_tenant` twins in M2 in the same revision if a downgrade must stay cheap; they are harmless duplicates.

## 4. Open questions for the user

1. The 15 surrogate-key tables (C2): leave the surrogate primary key and the tenant-leading unique twin (my recommendation), or make every table's primary key tenant-leading for uniformity? The guard test of
   1.3 can enforce either; the second is about 15 more key rebuilds for no isolation gain.
2. The backfill tenant for group D: `"default"`, or a name the host configures? In a deployed posture should the migration refuse to run when none is configured? (Rows written before this are single-tenant by
   construction, so one value is right; which value is the deployment's choice.)
3. Do the seven group-D tables ship as an SDK-supplied DDL function and a boot check (my proposal), or does each host be told in the CHANGELOG to alter its own tables?
4. Which deployments have rows in `eval_case_run`, `config_audit_event` and `turn_run_event`, and is an exclusive lock on them during M2 and M3 acceptable? I have no row counts.
5. The mapping source (2.3): config now, as recommended? Who is the authority for the UUIDs, the platform gateway (so the directory mirrors it), or does Plato own tenant creation?
6. Does the queue message `tenantId` carry a name or a UUID in the sibling services? That decides whether the queue path needs the directory today.
7. Does the `uq_*_tenant` twin on a table made tenant-leading in M2 get dropped (smaller schema) or kept (cheaper downgrade)?
8. Is `japes_policy_extraction_run`'s and `conductor_suspension`'s key order worth a migration (M3) while their unique twins are absent but the table is small (inferred)?

## 5. Not verified

Row counts, lock durations, and any deployment's actual tenant names. Every store's every query (only three stores read). The KH-backed canonical stores' tenant handling. The form of `tenantId` in
sibling queue messages. Whether `common` 0.4.0 changes the context token's tenant claim. Whether the 2026-11-05 note's "stale docstring" is the one I named in 1.3.
