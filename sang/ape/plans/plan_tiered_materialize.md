# Tiered materialize: block on a few documents, background the rest, fetch the tail on demand

Status: plan, 2026-09-11. Nothing built. Target 2.5.2. Written against japes `097c049` on `v2.5.1`
(pushed), with `e8a7a9c` local.

Companion to `done_JAPES_1_9_X_FABRIC_MATERIALIZE.md`, which shipped `materialize()` and decided
what it owns. That doc's exclusion list does not mention lazy, background or partial completion, so
nothing here reverses a decision; it extends the method's *shape* while leaving its semantics
alone. Worth noting one precedent from it: it says "Does not add retry logic on individual document
downloads -- that belongs in the KH client layer", and the shipped code carries per-document
`retry_async` regardless. `materialize` has already absorbed concerns that plan pushed outward, so
concurrency policy landing here too is consistent rather than novel.

## 1. Why now

jazzx-assistant is on 2.5.0 and grounding latency is its live problem, with more latency work
scoped for the release after next. The team spent a night on two candidate fixes, and the measured
facts say neither moves the number.

**Verified against the tree, not inferred:**

- `materialize` writes raw bytes to a local `output_dir` and converts nothing.
- `_needs_download` (`fabric/docs/store.py:1416`) returns True when the expected files are absent
  from disk *even on a manifest hash match*. A fresh container has an empty `output_dir`, so every
  document re-downloads whatever the manifest says. So a durable manifest store alone buys nothing
  for a cold start: what it survives is a fresh `output_dir` for the *manifest*, not for the files.
- `_listing_metadata` (`:1015`) returns `{doc_id: {name, sha256, page_count, ...}}` from one
  listing call, so hashes are nearly free and the per-document probe only covers documents KH had
  not hashed yet.
- The v2 download route answers with a signed blob URL, so bytes already come straight from
  storage rather than through the service (`:1429`).

Two conclusions follow, and the second one retracts an idea worth recording as retracted:

1. **N is the dominant term.** Cold-start cost is roughly one listing call plus N signed-URL
   fetches, each already direct from storage. Reducing N beats making each fetch cheaper.
2. **Caching raw bytes in `fabric.blob` is not the win it looks like.** With v2 serving signed blob
   URLs, a `fabric.blob` cache replaces an Azure blob GET with an Azure blob GET. `content_key()`
   is the right tool for caching a *derived* artifact keyed by the sha256 the listing already
   hands over; it is close to pointless for the source bytes.

**And the manifest swap is not merely useless, it is a regression.** The consumer's grounding
directory is a fresh `mkdtemp` per turn, so a manifest can never match anything on disk. Passing a
real manifest store also re-arms the metadata probe, because `materialize` gates its
skip-if-unchanged check on `probe_worthwhile = bool(get_metadata) and not isinstance(manifest,
NullMaterializeManifestStore)`. The consumer measured that: the armed probe doubled the Hub
requests grounding makes, 38 extra on one loan, for zero downloads saved. Their own code comment
records it and a test holds it. So the null store there is a deliberate choice with a number behind
it, not an oversight to be swapped out.

The one concern that *would* be fixed by the DB-backed store is the smaller half of that comment:
`NullMaterializeManifestStore` is also keeping `.materialize_manifest.json` out of a directory the
agent's file tools `glob`, and a DB-backed manifest writes no file there. That is a real
improvement and it is worth nothing on its own, because the probe cost returns with it.

**What this bounds.** Nothing manifest-shaped helps while the output directory is per-turn. Tiering
is unaffected by that, because it reorders work *within* one turn rather than reusing anything
across turns, which is why it is the plan and the manifest is not.

The consumer-side lever that does attack N is scoping the download to the investors a conversation
actually concerns instead of the whole org collection. That was raised and then dropped, for a
sound reason: a question about a different investor then has nothing to read. Tiering is what makes
the lever usable, because the objection is an argument for fetching the remainder *late*, not for
fetching everything *first*.

## 2. What exists today

| Surface | What it is |
|---|---|
| `fabric.docs.download()` | A pass-through to KH's v1 bulk route. Returns archive bytes, wraps the exception, nothing else. |
| `fabric.docs.materialize()` | The engine: N concurrent per-document fetches, hash-based skip through the manifest, per-document retry with backoff, caller-supplied naming, metadata sidecars, page counts, v2-probe-then-v1-fallback. |
| `fabric.docs.sync_collection()` | A collection-wide wrapper over `materialize`. |

`materialize` deliberately declines the bulk route: v1 bulk builds a one-member ZIP per document
and streams it back through the service, where v2 per-document gives a signed URL. So "bulk" here
means fan-out, not one bulk call.

**An unused capability worth knowing about.** KH serves a v2 *async* bulk download: trigger, poll
status, collect a signed link. japes' own mock app serves all three routes
(`server/mock_knowledge_hub_app.py:151/174/181`, "so a caller drives the real four-step flow") and
`KnowledgeHubClient` implements none of them: it has `download_document_v2` and the v1
`download_documents`, nothing else. The mock is ahead of the client. That async job is a plausible
substrate for the background tier, which is why it is recorded here rather than left to be
rediscovered. It is not a prerequisite: fan-out on the existing pool already backgrounds fine.

## 3. The design

Three tiers over one call, additive, with today's behaviour as the default.

**Required.** The documents the turn cannot start without. Awaited, exactly as `materialize`
behaves now.

**Background.** Everything else in the set. Scheduled on the same concurrency pool and not
awaited. The call returns once the required tier is on disk, carrying a handle for the rest so a
caller can await it at a natural boundary or ignore it.

**On demand.** A single-document entry point that blocks only on a cache miss. This is the tier
that answers the out-of-scope question, and it is the reason the whole thing is worth building:
without it, scoping the required set means some questions cannot be answered at all.

Sketch, not a signature:

```
result = await fabric.docs.materialize(
    entities, output_dir, ..., required=lambda e: e["investor"] in scoped,
)
# result.ready  -> the required tier, on disk now
# result.pending -> awaitable handle for the remainder

doc = await fabric.docs.materialize_one(doc_id, output_dir, ...)  # miss -> fetch; hit -> return
```

A predicate rather than two entity lists: the caller already has one list and a rule for which
documents matter, and making it pass two means partitioning at every call site.

## 4. The part that will be got wrong

**In-flight deduplication.** A question arriving while the background tier is running must join the
download already in progress for that document, not start a second one. Without it, the on-demand
tier races the background tier and the common case (a question about a document that was already
being fetched) costs two fetches and possibly a partial file on disk.

This is the one piece with no precedent in the current code: `materialize` fans out once and
returns, so it has never had to answer "is this document already being fetched right now". It
needs a per-`DocStore` map from doc id to an in-flight future, and `DocStore` is long-lived behind
`fabric.docs`, so that map is process-scoped state with all that implies.

Two failure modes to test explicitly, because both are silent:

- a background fetch that fails leaves its future rejected, and an on-demand caller arriving later
  must retry rather than inherit the failure forever;
- a partially written file must never satisfy the on-disk check that `_needs_download` performs.
  The existing code writes into `output_dir` directly, which is safe when nothing reads
  concurrently and is exactly what changes here.

## 5. Out of scope

- **No change to `materialize`'s existing semantics.** A caller that passes no `required` predicate
  gets today's await-everything behaviour, byte for byte. The callers are japes' own document agent
  (through `sync_collection`) and jazzx-assistant's grounding; jaci does not call it.
- **No conversion or derived-artifact caching.** If a consumer's grounding phase parses or converts
  after materialize, that artifact is theirs to cache, keyed by the sha256 the listing supplies.
  japes holding a cache of someone else's derived format is a different plan.
- **No `fabric.blob` source-byte cache** (§1, conclusion 2).
- **No async bulk client work** unless fan-out proves insufficient under measurement.
- **No hot-replica or shared-volume infrastructure.** That is the other real answer to cold starts
  and it is an infra change, not an SDK one.

## 6. Sequencing

1. **In-flight dedup, alone, behind the existing API.** No new surface: `materialize` gains the map
   and joins its own duplicate doc ids within one call. Independently useful, and it is the piece
   the rest rests on.
2. **`materialize_one`.** The on-demand tier, which is the smallest new surface and the one with a
   caller waiting.
3. **`required=` plus the pending handle.** Last, because it is the only part that changes what a
   call returns.

Each lands on its own review. Not before `v2.5.1` is closed.

## 7. What would make this wrong

- **If the measurement says N is not the cost.** Everything here assumes the fan-out dominates.
  Nobody has yet broken the grounding phase into listing, hash probe, fetch, and the consumer's own
  post-processing. If post-processing dominates, this plan is aimed at the wrong term and the
  derived-artifact cache in §5 is the real work. **Ask for that breakdown before building.**
- **If the required set cannot be computed cheaply.** Scoping by investor assumes the conversation
  knows its investors before grounding. If deciding that needs the documents, the tiers collapse.
- **Not "only one consumer asked for it".** jazzx-assistant is the only external caller of
  `materialize` today, and on an earlier reading that counted against building this here. It does
  not. That consumer is the canonical assistant: its turn shape is what the next assistant
  (policy workbench, a DSCR one) will start from, so absorbing its needs is the point rather than
  a favour to one caller. The risk worth tracking is the opposite one -- building the tiering
  *around* one consumer's current call site instead of the shape every assistant needs, which is
  what a `required=` predicate tuned to "investor" rather than to an arbitrary caller rule would
  look like.
