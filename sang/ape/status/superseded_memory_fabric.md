# Design note: Memory Fabric (#8)

Local design note (gitignored). Design-first — Chanpreet's "Memory Fabric" is at PRD stage on the RM
side; the point of this note is to stake japes's position *before* we react, and to size the build.

## What it is (and isn't)

**Memory Fabric = a distilled, fast-retrieval, provenance-linked grounding layer over canonical
findings/decisions.** Its job is to give an assistant (LUNA first) the grounding context for a turn
*without re-running the reasoner* — "reasoner output as context, not a second brain" (the v1 consensus
from the working group). Every item traces back to the raw finding / trace / document it was distilled
from, so a citation resolves and nothing drifts silently from source.

It is a **fourth memory tier**, distinct from the three we already have:
1. **Working memory** (one run) — SDK run `context` / `ConductorState`.
2. **Conversation memory** (per session) — `fabric.conversation`.
3. **Durable objects** — `fabric.entities` / canonical / KH.
4. **Memory Fabric** — *distilled knowledge for grounding*, retrieval-optimized, provenance-linked. ← new

Not: a chat-history store (that's #2), not raw entity CRUD (#3), not working scratch (#1). It's the
"what do we know about this subject, distilled and retrievable" layer.

## Where it sits / what it builds on

`fabric.memory`, a new surface composed from existing primitives (don't reinvent):
- **Retrieval:** `fabric.rag` (semantic search over a KH collection) — the read path.
- **Provenance:** links to `fabric.canonical` (Findings *are* canonical Decisions; Trace; SourceCoordinate)
  and `agents.document` SourceFile — the audit trail.
- **Idempotent write / supersede:** `fabric.idempotency` (`content_fingerprint` / `WriteOutcome`) —
  dedup a distilled item, supersede when its source changes.
- **Governance:** confidence/authority floors (`fabric.canonical.authority`, `Confidence`) — admit only
  above a floor; `fabric.guidance`'s lifecycle pattern for admit/supersede/expire.

## Shape (P1 sketch)

    class MemoryItem(BaseModel):
        memory_id: str
        content: str                       # the distilled fact/summary (the grounding text)
        scope: dict[str, str]              # {pack_id, subject_id (loan/case), collection_id}
        provenance: list[SourceRef]        # {kind: finding|trace|document, ref, content_hash}
        confidence: Confidence
        content_hash: str                  # dedup / supersede key (fabric.idempotency)
        superseded_by: str | None = None   # lifecycle: newer item replacing this
        created_at / valid_until           # freshness

- **Write (distill):** `memory.remember(source, *, scope) -> WriteOutcome[MemoryItem]` — summarize a
  reasoner finding / eval result / doc into a scoped, provenance-linked item; idempotent on content hash;
  refuses sub-floor confidence (XF-1 discipline, reused).
- **Read (ground):** `memory.recall(query, *, scope, k) -> list[MemoryItem]` — retrieval-optimized
  grounding for a turn. Feeds the assistant's grounding step **and** `grounded_guardrail`'s `get_context`.
- **Supersede:** re-distilling a changed source supersedes the old item (never two live truths for one
  fact); `content_fingerprint` keys the match.

## Multi-source ingestion (ties to the feedback question)

Memory Fabric is where **learnings from logs / documents / feedback** land as retrievable memory — the
"read logs/docs to improve things" ask. Sources, all provenance-linked, all through `remember`:
- **Reasoner/MACER findings** (Chanpreet's primary) — distilled to grounding facts.
- **Feedback-derived** — `Feedback` (any source: USER/JUDGE/SYSTEM, incl. future LOG/DOCUMENT) →
  structured learning → memory. (The feedback spine already links feedback to trace/turn; a log/doc
  ingestion source emits `Feedback(source=SYSTEM/…)`, which distills into memory.)
- **Document-derived** — SME review docs / red-team findings via `convert_document` + `structure_feedback`.

So the compounding loop closes: turn → trace → feedback (any origin) → distilled memory → grounds the
next turn.

## Relationship to `fabric.guidance` (important — avoid overlap)

We already ship `fabric.guidance` (governed, validated *authored assets* — prompt/policy guidance with a
lifecycle + A/B validation). Memory Fabric is the **retrieval-optimized grounding-facts** view, not
authored assets: guidance = "how the agent should behave" (validated), memory = "what we know about this
subject" (distilled, provenance-linked). They share the lifecycle + provenance patterns but are distinct
surfaces. Decision to lock: keep them separate; memory may *cite* guidance but doesn't replace it.

## Phasing

- **P1** — schema + `remember` (distill, idempotent, provenance, confidence-gated) + `recall` (retrieve
  by scope+query over `fabric.rag`). LUNA grounding + `grounded_guardrail` as first consumers.
- **P2** — lifecycle: supersede-on-source-change, freshness/expiry, dedup via `content_fingerprint`.
- **P3** — multi-source ingestion (feedback/log/document → memory), incl. a `FeedbackSource.LOG|DOCUMENT`
  + a trace-scanning batch signal-extractor.
- **P4** — retrieval tuning (embeddings/backend), scope/ranking, eval of grounding quality (reuse
  `evaluation` scorers).

## Open questions (decide before P1)

- **Storage:** a dedicated KH collection (via `fabric.rag`) vs `fabric.db` vs both (rag for retrieval,
  db for lifecycle/provenance index). Lean: rag-backed content + a provenance/lifecycle index.
- **Embeddings:** which backend; does retrieval need vectors in P1 or is metadata+token-scoring enough
  (the guidance store deliberately uses metadata + Python token-scoring today — same constraint applies).
- **Scope model:** subject granularity (per-loan? per-collection?) and cross-subject general memory.
- **Distillation owner:** does japes distill (LLM summarize) or does the pack supply the distilled item?
  Lean: japes provides `remember` with a default LLM distiller + a pass-through for pack-distilled items.

## Why now

Chanpreet's PRD is in flight and LUNA needs grounding context that isn't "re-run the reasoner." If japes
ships `fabric.memory` (P1) as the distilled-grounding surface, the assistant consumes it instead of each
team inventing a store — and it becomes the home for the log/doc/feedback-derived learning the compounding
loop produces. See [[luna-assistant-vertical]], [[jazzx-persistence-architecture]], [[fabric-idempotent-writes]].
