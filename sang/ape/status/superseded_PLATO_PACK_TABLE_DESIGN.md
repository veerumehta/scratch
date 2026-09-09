# A pack table for Plato

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: design, 2026-09-02. Nothing built. Third note in the sequence, after
`PLATO_DB_TABLE_MAPPING.md` and `PLATO_ORG_SCHEMA_DESIGN.md`.

## What a pack is today

`jazzx_sdk.pack.Pack` composes a directory of authored YAML behind one object. Its manifest carries
identity (`pack_id`, `pack_version`, `certification_status`, `domain`, `segment`,
`regulatory_context`), composition (`depends_on`, version-pinned and fragment-limited), and pointers
to assets: ontology, policies, playbooks, evidence types, skills, modes, experts, conductor config,
agent directory, evaluation config, authority matrix, surface bindings.

It is loaded from `packs_root` on disk. There is no pack row anywhere, and `Pack.from_manifest`
reads the filesystem. That is the thing this changes.

## The question that decides the schema

**Does the table hold the pack, or point at it?**

Storing the content makes Plato the registry: a pack is published once, immutable thereafter, and
every deployment reads the same bytes. Pointing at a path keeps the filesystem as the source of
truth and makes the row a cache, which is worth almost nothing -- a cache of a directory nobody can
version.

This proposes **holding it**, because the value is not storage. It is being able to answer *which
pack version produced this decision*, six months later, when the working tree has moved on. That
answer requires the version to be immutable and addressable, which a path is not.

## Immutability is the design

A published `(pack_id, version)` never changes. Everything mutable is modelled around it rather than
in it:

- **Certification moves, the version does not.** `draft -> certified -> suspended -> retired` is a
  lifecycle over a fixed artefact. Keeping it in the pack row means the row changes after
  publication, so it goes in its own event table and the current value is derived.
- **Correcting a pack means publishing a new version.** There is no edit path. This is the same
  bargain every package registry makes, and it is what makes provenance work.

## Proposed tables

Three. Each carries `tenant_id` in its primary key per `plato/tenancy.py`, plus the SDK's audit
stamping.

### 1. `plato_pack_version`

One row per published version. The unit of everything else.

| column | notes |
| --- | --- |
| `tenant_id`, `pack_id`, `version` | composite PK. Three parts, because a pack id means nothing across tenants. |
| `manifest` | JSONB -- the whole manifest as authored. Queryable, so "which packs declare this regulatory context" is a query rather than a filesystem walk. |
| `content_digest` | sha256 over the pack's asset bytes. What makes the version verifiable. |
| `content_ref` | blob location for the bytes. Assets are authored and read as a unit, so they are stored as one; `fabric.blob` is the intended home. |
| `domain`, `segment` | denormalised out of the manifest, because these are the two everything filters on |
| `published_at`, `published_by_user_id` | |
| `visibility` | `tenant` or `platform`. See the open question. |

**Why the manifest is JSONB and the assets are a blob.** The manifest is small, structured and
queried; the assets are large, opaque to SQL and read whole. Splitting them that way avoids both a
table nobody can query and a row nobody wants to fetch.

**Why not a row per asset.** Tempting -- ontology, policies, playbooks each in their own table --
and wrong for the same reason a package registry does not shred a wheel: the pack is authored,
reviewed and versioned as a unit, and shredding it makes publication non-atomic and reassembly a
join. The pack's *content* becomes queryable through the vocabulary and policy stores it loads into,
which already exist.

### 2. `plato_pack_dependency`

The `depends_on` closure, as edges. One row per declared dependency.

| column | notes |
| --- | --- |
| `tenant_id`, `pack_id`, `version`, `depends_on_pack_id` | composite PK |
| `version_spec` | as declared -- a pin or a range |
| `resolved_version` | what it resolved to at publication, so the closure is reproducible later |
| `fragments` | which fragment kinds are imported; the loader already validates the kind set |

**Why edges rather than a JSON list inside the manifest** (which is where they live today): the
question asked in practice is the reverse one -- *what breaks if this pack is retired* -- and that is
a query over edges, not a scan of every manifest. Recording `resolved_version` alongside the spec is
what makes a six-month-old closure re-derivable; a range alone is not.

### 3. `plato_pack_status`

Certification as an append-only log.

| column | notes |
| --- | --- |
| `event_id`, `tenant_id` | composite PK |
| `pack_id`, `version` | composite FK to the version row |
| `status` | `draft`, `certified`, `suspended`, `retired` -- the values `certification_status` already uses |
| `reason` | free text; a suspension without a reason is not actionable |
| `occurred_at`, `actor_user_id` | |

Current status is the latest event. That costs a query and buys the history: *when was this
suspended, and by whom* is the question asked during an incident, and a mutable column cannot answer
it.

## Binding: deliberately not here

Which project or assistant uses which pack version is a *separate* relation, and it belongs with the
organisation schema rather than this one -- `plato_project_resource` in `PLATO_ORG_SCHEMA_DESIGN.md`
already has the shape (`resource_type='pack'`, `resource_id`), and it needs one addition: a pack
binding must name a **version**, not just a pack. Left as a note there rather than a fourth table
here, because the alternative is two tables that both claim to say what a project uses.

## Open questions

**1. Platform packs versus tenant packs.** A pack authored once and used by every tenant does not
fit `tenant_id` in the primary key. Three options: a reserved tenant id (simple, slightly dishonest),
a `visibility` column with a nullable tenant (breaks the tenancy rule), or copy-on-adopt so each
tenant holds its own row (honest, duplicates bytes -- though `content_digest` means the blob is
shared). Copy-on-adopt is the one that keeps the tenancy rule intact and should be the default unless
it proves painful.

**2. Does publication go through Plato, or land here after the fact?** If a pack is authored in a
repository and CI publishes it, Plato is a registry with a write API. If Plato is where packs are
edited, this schema needs a draft workspace that the immutability rule above deliberately excludes.
The `certification_status: draft` value in today's manifests suggests the latter was assumed; the
`depends_on` version-pinning suggests the former. Worth settling.

**3. What happens to `packs_root`?** Every current caller does `Pack.from_manifest(pack_id,
packs_root)`. A database-backed pack needs a loader that resolves from the registry, and the
filesystem path becomes the local-development case. That is an SDK change (`PackManifestLoader`),
not a schema one, but the schema is not usable without it.

## Order of work

1. Settle open question 2. Registry-after-the-fact and edit-in-place are different products.
2. `plato_pack_version` alone, with a loader that reads it. That is enough to answer the provenance
   question, which is the point.
3. `plato_pack_dependency` when a second pack depends on a first in anger.
4. `plato_pack_status` when certification is actually operated rather than declared.

Building 1 and 2 first is deliberate: they carry the value, and 3 and 4 are cheap to add against an
immutable version row but expensive to retrofit against a mutable one.
