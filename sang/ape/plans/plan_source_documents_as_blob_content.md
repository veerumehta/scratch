# Plan: source documents as blob-addressed content that rules, units and links cite (sonnet-runtime, 2026-10-30)

Plan only; nothing built. Survey first, then the proposal. Queue position: after the adoption path, except the `SourceRef` type (section 3), which the adoption build needs first.

## 1. What already exists (read from the code)
| Piece | What it gives | Gap for this ask |
|---|---|---|
| `fabric.blob` (`BlobStore`) | `put(data, key=)`, `get`, `content_key(data)` = `sha256/<hex>`, `offload(dedup=True)`; backend `local` or `azure` (`JAPES_BLOB_BACKEND`, `JAPES_BLOB_CONTAINER`); keys checked against `..` and absolute paths | none: the same calls on both backends |
| `BlobDocumentStore` (`fabric/blob/documents.py`) | tenant-keyed, document id = sha256 of bytes, JSON sidecar (filename, size, media type), idempotent repeat upload | I found no caller in `jazzx_sdk` or `plato` by grep; it holds whole documents, no topic addressing |
| **Guideline sets** (`pack/guidelines.py`, `guidelines_db.py`, client `publish_guideline`) | versioned file sets: each `GuidelineFile` has `path`, `sha256`, `size`, blob `pointer`, a text pointer and text sha; `GuidelineVersion.digest`; `GuidelineRef {set_id, version, digest}`; a pack manifest pins one (`pin_of`); proposals are stamped with the guideline label and digest (`_stamp_guideline`); `diff_versions`, withdrawal checks; limits 200 files, 50 MB a file, 200 MB a version | no edition or published date per file (only `effective_from` per version); no topic index; the reference stops at the proposal, rules and units do not carry it |
| Draft store | 1 MB a file, 500 files (`MAX_DRAFT_FILE_BYTES`, `MAX_DRAFT_FILES`) | wrong home for source documents: it holds the pack's own files, and per-topic files would use 389 of the 500 |
| Rule citations | `Rule.citations` are strings (`<source>#<topic>`); `ProposalEvidence.source_refs` the same strings | free text: no digest, no edition, no offsets |

**The main finding: the June guide does not need to go into the draft store at all.** A guideline set holds it as one 2.6 MB file (limit 50 MB), blob-stored by
content on local or azure, with a version digest a pack pins. The draft-store limits do not apply to it. Per-topic files are not needed.

## 2. Proposal
1. **Store**: publish the guide as a guideline set (one file, or one per edition). No new store, no new route: `publish_guideline` exists.
2. **Topic index** (new, SDK): the single-markdown reader (being built for the adoption path) already finds each topic's id, title, date and span. Keep that as a
   sidecar of the stored file: `topics: [{topic_id, title, date, start, end, sha256}]` (byte offsets into the stored bytes, `sha256` of that slice),
   written with the version and covered by its digest, so the index cannot drift from the bytes.
3. **`SourceRef`** (new, small, the part adoption needs first): `{set_id, version, digest, topic_id, edition, start?, end?, topic_sha256}`. Units from the corpus
   reader carry one; an adopted link (`CHECK_LINKS_KEY` row) carries the unit's; a generated rule's `citations` keep the readable string and gain the
   `SourceRef`s in its metadata. A rule is traced to exact bytes by `digest` plus offsets, verified against `topic_sha256`.
4. **Resolver** (new): `resolve_source_ref(ref) -> text` reads the version from the guideline store, the file's blob, slices, verifies the slice digest, and
   raises on mismatch (never returns different text). The draft and a published pack resolve the same ref the same way, because the ref names the guideline
   version (not a pack version or a draft revision); the pack's pin only decides which version new work reads.
5. **Local dev and azure behave the same** because every read and write is `BlobStore`; keys are content digests, so a local directory and an azure
   container hold identical key sets. A test over the local backend plus a contract test on the key shape is what proves it; azure itself needs the
   `common` provider and a live container (not testable here).
6. **Next edition**: published as a new guideline version with a new digest; unchanged files share their blob by content key; old rules keep their
   `SourceRef` (old version, old digest) and still resolve to the old bytes; `diff_versions` reports what changed by section; withdrawal of an old
   version is already refused while something pins it (`check_withdrawal`). A link whose `edition` differs from its unit's is the `edition_mismatch` of the adoption plan.

## 3. Order and dependency
`SourceRef` goes **inside the adoption build** (units and links carry it from the start, so no second migration of link rows). The topic index and the
resolver come after the adoption path, as a second commit set. Nothing here reorders the queue otherwise.

## 4. What jaci can do now, with no SDK change
Publish the June markdown as a guideline set with the existing client call (`publish_guideline`, one file), pin the pack to it, and keep the mapping
file's edition and topic ids as they are. Do **not** put per-topic files in the draft. A `source/` folder with a manifest in the pack would duplicate
what the guideline version already records (path, sha256, size, pointer), so it is not needed; the one thing it could add (edition and published date)
should land on the guideline file's record in the SDK, not in a pack folder.

## 5. Not checked, to say plainly
The fabric persistence roadmap's blob phases: I did not re-read that note for this survey, so I do not say which phases cover part of this; I will before building.
Whether any host already uses `BlobDocumentStore` outside the two trees I grepped (`jazzx_sdk`, `plato`).
