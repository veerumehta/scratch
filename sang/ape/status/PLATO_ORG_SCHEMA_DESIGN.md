# Plato's organisation schema

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: design, 2026-09-02. Nothing built. Follows `PLATO_DB_TABLE_MAPPING.md`, which established
that Plato owns the organisation -- the one substantial gap between the SDK's 17 tables and what
kernel and assistant hold between them.

## What is being decided

Nine assistant tables have no japes equivalent: `project`, `team`, `team_membership`,
`user_membership`, `project_membership`, `role`, `user_session`, and the two `assistant_role` /
`resource` strays. This proposes what Plato should hold instead. It is not a port: three things
about assistant's shape do not survive contact with Plato's rules.

## Three findings from assistant's schema that shape this

**Users are already external, and that is right.** `project_membership.user_id` carries the comment
`# External user DB` and, unlike `team_id` and `role_id`, has no foreign key. Assistant references
users; it does not own them. Plato should keep that. There is no `user` table below, and
`CallerIdentity.user_id` is the identifier that reaches Plato from the platform's identity headers.

**`role.name` is globally unique**, declared `unique=True` on the column. Under Plato's tenancy rule
that is a defect rather than a constraint to copy: two tenants could not both have a role called
`reviewer`. Every unique constraint below is scoped by `tenant_id`.

**`user_membership` is polymorphic** -- `(user_id, entity_id, entity_type)` -- so one table records
membership of anything. It is flexible and it is also why "who can see this project" cannot be
answered by the database alone: nothing constrains `entity_id` to point at a row that exists.
Splitting it is the recommendation below.

## Tenancy, applied

`plato/tenancy.py` requires `tenant_id` in a primary key or unique constraint, and `verify_tables`
enforces it over registered metadata. The established SDK pattern (`agent_session`) is a composite
primary key of natural id plus tenant, with an explicit named unique constraint alongside:

```python
__table_args__ = (UniqueConstraint("tenant_id", "session_id", name="uq_session_tenant_session"),)
session_id: Mapped[str] = mapped_column(String, primary_key=True)
tenant_id:  Mapped[str] = mapped_column(String, primary_key=True, default=DEFAULT_TENANT)
```

Every table below follows it. That has a consequence worth stating: **foreign keys become
composite**, `(tenant_id, project_id)` rather than `project_id`, which is what makes a cross-tenant
reference impossible to write rather than merely unlikely.

## Proposed tables

Seven, down from nine. Each row carries `tenant_id`, `created_at`, `updated_at` and the
`created_by_user_id` / `updated_by_user_id` pair the SDK's audit stamping already writes
(`Repository._stamp_created` reads `CallerIdentity`).

### 1. `plato_project`

The unit of work people organise around. `tenant_id` is the deployment boundary; a project is a
workspace inside it.

| column | notes |
| --- | --- |
| `project_id`, `tenant_id` | composite PK |
| `name`, `description` | `UniqueConstraint(tenant_id, name)` -- a tenant's project names are its own |
| `status` | enum: `active`, `archived`. Assistant's `ProjectStatus` is the reference. |
| `scope` | enum, from assistant's `ProjectScope` -- needs reading before the values are fixed |

### 2. `plato_team`

| column | notes |
| --- | --- |
| `team_id`, `tenant_id` | composite PK |
| `name` | `UniqueConstraint(tenant_id, name)` |
| `parent_team_id` | self-reference, composite `(tenant_id, parent_team_id)`. Assistant has this; it means teams nest. |
| `visibility` | assistant's `VisibilityEnum` |
| `privileged` | assistant carries this flag; its meaning needs confirming before it is copied |

**Open:** nested teams make "is this user in this team" a recursive query. Assistant already pays
that cost. If nesting is not used in practice, dropping `parent_team_id` removes a class of
authorisation bug. Worth checking real data before building it.

### 3. `plato_role`

| column | notes |
| --- | --- |
| `role_id`, `tenant_id` | composite PK |
| `name` | `UniqueConstraint(tenant_id, name)` -- **not** globally unique, unlike assistant |
| `type` | assistant's `RoleTypeEnum` (system vs custom, on the evidence of the name) |

### 4. `plato_team_member`

Replaces `team_membership`. A person's place in a team.

| column | notes |
| --- | --- |
| `tenant_id`, `team_id`, `user_id` | composite PK -- the natural key, and it makes duplicate membership impossible |
| `status` | assistant's `TeamMembershipStatus` (invited / active / removed, presumably) |

`user_id` is an external identifier with no foreign key, as above.

### 5. `plato_project_grant`

Replaces `project_membership`, renamed because it is a grant rather than a membership: it says
*which role* a user or team holds *on a project*.

| column | notes |
| --- | --- |
| `grant_id`, `tenant_id` | composite PK |
| `project_id` | composite FK `(tenant_id, project_id)` |
| `role_id` | composite FK `(tenant_id, role_id)` |
| `user_id` **or** `team_id` | exactly one set -- a CHECK constraint, not a convention |
| | `UniqueConstraint(tenant_id, project_id, user_id, role_id)` and the team equivalent |

The CHECK is the point. Assistant allows both columns to be null or both set; the database should
refuse a grant that names nobody.

### 6. `plato_user_session`

A person's login, distinct from `agent_session` (a conversation). Keeping the names apart matters --
they are different lifetimes and assistant's `user_session` has been mistaken for the other before.

| column | notes |
| --- | --- |
| `session_id`, `tenant_id` | composite PK |
| `user_id` | external |
| `correlation_id` | assistant constrains to exactly 12 characters, indexed |
| `status`, `logoff_at` | |

**Open:** does Plato need this at all? If sessions are minted and validated by the platform's
identity service, Plato storing them duplicates a source of truth. Assistant has it because it
terminates the browser session. If Plato does not, this table should not exist.

### 7. `plato_project_resource`

Replaces the polymorphic `user_membership` and `resource`. What a project is allowed to reach --
a collection, a pack, an assistant.

| column | notes |
| --- | --- |
| `tenant_id`, `project_id`, `resource_type`, `resource_id` | composite PK |
| `resource_type` | enum, closed set |
| `resource_id` | opaque; the referent lives in Knowledge Hub or elsewhere, so no FK |

This is deliberately narrower than `user_membership`. That table answers "is X a member of any
entity", which is flexible and unconstrainable. Splitting it into `plato_team_member` (people in
teams) and this (projects to resources) gives each half a real key.

## What is deliberately absent

- **No `user` table.** Users are the platform's. Plato stores `user_id` and nothing else about them.
- **No `assistant_role` / `assistant_agent` / `assistant_tool` join tables.** The manifest already
  declares what an assistant may use; a join table would make declared configuration into mutable
  state, and the two would disagree.
- **No global roles.** Every role belongs to a tenant. A platform-wide role, if needed later, is a
  `type` value, not an unscoped row.

## Order of work

1. Confirm the three enums by reading assistant's definitions (`ProjectStatus`, `ProjectScope`,
   `RoleTypeEnum`, `VisibilityEnum`, the two membership statuses). This note names them from usage,
   which is not good enough to build from.
2. Settle the two opens: nested teams, and whether `plato_user_session` should exist.
3. Tables 1-3 first (project, team, role), then 4-5 (membership and grants), then 7. Each lands in
   the SDK's alembic chain, so `verify_tables` checks tenancy as it goes.
4. `plato_user_session` last, or not at all.

## Why grants are worth this much care

Five of the seven tables are about who may do what. Authorisation bugs are silent -- a missing row
denies access visibly, an extra row grants it invisibly -- so the constraints that make a wrong row
impossible to insert are more valuable here than anywhere else in Plato's schema. That is the
reasoning behind composite foreign keys, the CHECK on `plato_project_grant`, and splitting the
polymorphic membership table.
