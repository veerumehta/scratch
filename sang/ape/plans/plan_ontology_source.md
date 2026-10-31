# Ontology source: a catalog that says where it came from, refreshed from the Knowledge Hub without ever failing a caller

**Status:** building in 2.6.8, 2026-10-31. Source: `note_workbench_to_sdk_enhancements.md` items F1 and F4, approved by the user through
opus-xrepo. Checked first: neither `plato/` nor `jazzx_sdk/` has an ontology poll, corruption gate, provenance stamp or seed fallback
(`resolve_current_ontology` and `fabric.graph.resolve_ontology` are pass-throughs that raise; `catalog_reference_db.py` stores what a
caller hands it). Not checked: the workbench's own config lookup. Author: sonnet-runtime.

## What it is
A consumer-neutral module, `jazzx_sdk/pack/ontology_source.py`, with no client names:

- `unwrap_ontology(body)`: the schema document out of whichever envelope the Hub answers in (`json_ontology` first; eight more keys, a
  JSON string, or a bare schema). Without it a measured sandbox run rejected every fetch.
- `reject_reason(document, min_entities=, required_entities=)`: a corruption gate, not a policy gate. Not an object, no `$defs`, fewer
  entities than the floor, no entity with properties, a required entity missing. A refusal keeps what is in force.
- `OntologyStamp`: the provenance of the document in force. Typed `source_status` (`seed` or `hub`); `confirmed` means fetched from the
  Hub with the digest recorded.
- `OntologySource`: holds the seed, `current()` is a local read, `refresh(kh)` fetches by Hub id or by registry key, gates, adopts or
  keeps, and never raises (outcomes `adopted`, `unchanged`, `rejected` with reason, `unavailable`). A TTL gates it, and it starts the
  clock after a failure too, so a dead Hub is not retried on every call.

## How a pack declares it
A `catalog_source:` block in the pack manifest beside `catalog:` (read like `rerun:`, by `catalog_source_config()`):

```yaml
catalog: catalog.schema.json            # the bundled seed
catalog_source:
  ontology_key: <registry key>          # or ontology_id: <Hub id>; exactly one
  required_entities: [JTBDSet]          # optional; the gate refuses a document without them
  min_entities: 5                       # optional; the floor
  ttl_seconds: 3600                     # optional
```

## What the stamp looks like (additive over the `x-provenance` keys a pack has today)
Kept as they are: `source_file`, `source_id`, `source_version`, `source_sha256`, `scope`, `entities_read`. New and typed:
`source_status` (`seed` or `hub`), `fetched_at` (UTC, Hub only), `hub_id`, `hub_version` (Hub only). The reader takes the free-text
`status` an existing seed carries ("bundled seed, not confirmed against Knowledge Hub") as `seed`, so a pack with that stamp loads
unchanged. A seed's digest is whatever its author recorded; a Hub document's is the canonical-JSON SHA-256 (`util.digest.content_digest`),
so the two are not comparable and the stamp never claims they are.

## How a seed pack upgrades to a Hub-sourced catalog
The catalog file changes, so it is a new pack version: `stamped_catalog(document, stamp)` returns the document with `x-provenance` set,
the author writes it as the pack's catalog and publishes. Nothing writes into a published pack. The seed stays the fallback.

## Out of scope
Persisting the adopted document (the in-memory hold is the first cut; `DbCatalogReferenceStore` is the place when a host needs history),
the removal and addition delta at adoption (`vocab_compare.diff_catalogs`, F2, not verified against raw Hub JSON Schema), a client
helper (the unwrap is a module function), wiring a host's startup refresh (the host calls `refresh`).

## Tests (production-shaped stub: the Hub's `json_ontology` envelope, `None` when missing, `ValueError` from the registry when none)
Unwrap per envelope; the gate per reason; stamp round trip and jaci's real `x-provenance` keys; adopt, unchanged, rejected keeps the
seed, unavailable on `None` and on a raised error, TTL and force, registry-key path; manifest block read; `stamped_catalog`.
