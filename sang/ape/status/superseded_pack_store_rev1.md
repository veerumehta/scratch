# Pack store: `pack_record` and what it does not solve

Sketch, not a decision. Written against the tree at `1137294`.

## The finding that shapes this

A `pack_record` table is the easy half. `PackManifestLoader` does not read a manifest *document* —
it reads a **directory tree**, and roughly a third of its accessors hand back a `Path` or read a
file relative to `self._root`:

| Accessor | Returns |
|---|---|
| `root()` | `Path` |
| `policy_files()` | `list[Path]` |
| `get_agent_dir()` | `Path \| None` |
| `get_mode_tuning_path(mode)` | `Path \| None` |
| `load_playbook_content(asset_id)` | reads `self._root / ref` |
| `load_ontology()`, `load_vocabulary()`, `load_diagnose_map()` | read under `_root` |
| `resolve_dependencies(packs_root)` | walks the filesystem for `depends_on` |
| `from_pack_id(pack_id, packs_root)` | tries three directory spellings |

A real pack (jaci's `dscr_core`) is `pack_manifest.yaml` **plus** `policies/`, `profiles/`,
`document_agent.yaml`, `ENCODING_NOTES.md`. Storing the manifest as a JSON column leaves every one
of those on disk, so an uploaded pack would be half-configured — the metadata queryable and the
content missing.

So the design has three parts, and only the first is a table.

## 1. The table

Following `assistant_manifest_record`, which is the same shape one level down (what an assistant
is, plus who changed it) and whose column choices were argued already:

```python
class PackRecordRow(_Base):
    __tablename__ = "pack_record"
    __table_args__ = (
        # tenant_id inside the constraint, not merely a column: the manifest store's comment
        # applies verbatim -- a plain column is a filter a query can forget, and the failure is
        # one tenant reading another's domain config.
        UniqueConstraint("tenant_id", "record_id", name="uq_pack_tenant_record"),
    )

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String, index=True, default=DEFAULT_TENANT)
    record_id: Mapped[str] = mapped_column(String, index=True)   # the identity a caller uses

    # From the manifest, promoted to columns because they are what a list view filters on.
    pack_id: Mapped[str] = mapped_column(String, index=True)     # "dscr-core"
    pack_version: Mapped[str] = mapped_column(String, index=True)
    domain: Mapped[str] = mapped_column(String, index=True)      # "commercial_lending"
    segment: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    certification_status: Mapped[str] = mapped_column(String, index=True)  # draft|certified|...

    manifest_json: Mapped[dict] = mapped_column(JSON)            # the parsed manifest, whole
    # Where the tree lives. See part 2 -- without this the row describes a pack nobody can load.
    content_pointer: Mapped[str | None] = mapped_column(String, nullable=True)
    content_sha256: Mapped[str | None] = mapped_column(String, nullable=True)

    supersedes: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, index=True)       # active|superseded|...
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
```

Deliberate choices, each with the reason:

* **`pack_version` indexed, not unique.** Same argument the manifest store makes: a rollback to
  byte-identical content legitimately produces a second record carrying the same version.
* **`depends_on` stays inside `manifest_json`.** It is a list of `{pack_id, version, allowed}`
  that only the fragment merge reads, and a join table would have to be kept in step with the
  document that is already the source of truth. Promote it only if a query needs "what depends on
  this pack", which nothing does yet.
* **Both `manifest_json` and `content_pointer`.** The manifest is queryable and small; the tree is
  neither. Splitting them is what lets a list view answer without touching blob storage.
* **`certification_status` as a column.** `draft | certified | suspended | retired` already exists
  in the manifests and is the field a deployment would gate on, so it should be filterable rather
  than buried in JSON.
* **Schema: `CONTROL`.** A pack decides what the deployment *is*, and `plato/models.py` puts
  `assistant_manifest_record` and `config_audit_event` there for that reason. Adding a row to
  `TABLE_SCHEMAS` is required or the migration check fails, which is the intended forcing function.

## 2. Where the tree goes

`fabric.blob` already has the two operations this needs: `put(data, key=...) -> pointer` and
`get(pointer) -> bytes | None`. So: **one archive per pack version**, pointer in the row, digest
beside it.

The digest is not decoration. `fabric.docs.materialize` already keeps a manifest of
`sha256:`/`updated_at:` digests to avoid re-downloading unchanged documents, and a pack tree wants
exactly that: materialize once per version, skip when the digest matches.

## 3. Getting the loader a root — the part that needs a decision

Two options, and this is the choice worth making explicitly:

**(a) Materialize to a directory, keep the loader as it is.**
`PackStore.materialize(record_id) -> Path` fetches the archive, unpacks under a cache dir keyed by
`content_sha256`, and hands the path to `PackManifestLoader.from_pack_id`. Every path-based
accessor keeps working untouched.

* *For*: no change to `pack/`, and the precedent exists — `fabric.docs.materialize` is the same
  move for documents, digest-skip included.
* *Against*: needs writable local storage, and `depends_on` resolution needs the whole closure
  materialized before the merge can run.

**(b) Abstract the path accessors behind a reader.**
`PackManifestLoader` takes something with `open(relpath)` / `iterdir(relpath)`, with a filesystem
implementation and a blob one.

* *For*: no local disk, no cache invalidation.
* *Against*: touches every accessor in the table above, and `packs_root`-walking dependency
  resolution has to be rewritten. Much larger change, and it buys nothing until a deployment
  actually cannot write to disk.

**Recommendation: (a).** It is smaller, it reuses a pattern this repo has already argued through,
and (b) remains available later — a reader abstraction over a materialized directory is a strictly
smaller step from (a) than from where we are now.

## What this unblocks, and what it does not

Unblocks the 2.5.1 items that currently have nowhere to put a pack: dynamic pack loading, and the
pack upload UI. Both need a pack that is not baked into the image.

Does **not** change how packs are authored. jaci keeps `config/packs/` as the authoring surface;
the store is a distribution and versioning mechanism, and the filesystem loader stays the path a
developer uses. That matters for the boundary this repo keeps: japes owns the mechanism, the
consumer owns the content.

## Open questions

1. **Archive format and layout.** A zip of the pack directory is the obvious choice
   (`fabric.docs` already unpacks zips), but the member-naming collision handling there was
   non-trivial and worth reading before repeating.
2. **Who validates on upload?** `pack/lint.py` exists. Running it at upload and refusing a pack
   that fails is the difference between a store and a dumping ground — but it is also a policy
   decision about whether `draft` packs may be uploaded at all.
3. **Audit.** `config_audit_event` is the trail for settings and manifests. A pack upload is the
   same kind of event and should probably use it rather than a second trail.
4. **Does this belong in Plato or in the JAPES service?** Plato has the DB and the config routes
   today. The dedicated japes service + DB direction would make this the shared config-versioning
   control plane instead, in which case `pack_record` lives there and Plato reads it. Worth
   settling before the table lands, because moving it later is a migration in two services.
