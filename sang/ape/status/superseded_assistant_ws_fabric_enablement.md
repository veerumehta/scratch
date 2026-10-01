# Assistant WS v2 — deprecate direct-KH in favor of fabric (JAPES enablement)

Local planning note (gitignored). Author: Virendra Mehta. Target repo: `jazzx_sdk` (JAPES, currently
2.1.4). Companion to the Notion design "Jazz Assistant — Engineering Design (japes-based, v2)" and to
`plan_assistant_vertical.md` / `plan_memory_fabric.md`.

Instructions are for Claude Code: each work item names the file, the anchor, the change, and the intent.
Code appears only for acceptance checks and critical signatures. **Ground before you build** — read the
cited files first; if a premise below is stale, fold the correction back into this plan before writing code.

## TLDR

The v2 WebSocket design leans on the Knowledge Hub (KH) in three places — grounding (§9), conversation
persistence (§12), auth passthrough (§13). We audited the fabric source: **two of the three already map
1:1 onto existing fabric surfaces**, so "deprecate KH" mostly means the assistant calls
`ctx.runtime.fabric.*` instead of a raw `KnowledgeHubClient`. There is exactly **one real SDK gap** — a
conversation store that write-throughs to KH entities as `canonical_conversation` so the frontend can read
the thread. We close it with `fabric.entities` (no canonical-core edit) plus a small per-turn
security-context context manager. Net effect: the §16 "required upstream japes changes" list shrinks to
one true net-new item (inbound WS), because canonical-type registration is sidestepped and
ConversationStore wiring already exists.

Decision locked with the design owner: **store conversations via `fabric.entities`**
(`entity_type="canonical_conversation" / "canonical_conversation_turn"`), not by adding a first-class
canonical type. Frontend reads through `fabric.entities.filter(...)`; no core registry edit.

## 1. What already exists (adopt, do not rebuild)

Verified against source on 2026-07-26. The v2 design's KH calls have direct fabric equivalents:

| v2 design needs (§) | Fabric surface (verified) | Notes |
|---|---|---|
| Grounding: loan docs download to local dir (§9) | `fabric.docs.materialize(entities, output_dir, *, doc_id_field, collection_id, name_fn, ...)` — `docs/store.py:710` | Already does concurrent download + retries + dedupe + collided-name handling. This *is* the grounding-download pattern. |
| Grounding: findings / LOS entities (§9) | `fabric.entities.filter(entity_type, filters, ...)` + `fabric.entities.list_all(...)` — `entities/store.py:209,177` | Arbitrary typed entities, filtered by field (loan id, etc.). |
| Grounding: guidelines collection (§9) | `fabric.guidance` (`RagGuidanceStore`) — `guidance/store.py` | Purpose-built: versioned, pack-scoped, status-filtered. Prefer over a raw RAG-collection download. |
| Cross-turn thread + compaction (§11) | `AES.bind_conversation(store, session_id, *, compaction)` — `agents/service.py:126`; `ConversationStore` ABC (`load/append/clear/load_raw/supersede`) — `agents/interactive/memory.py:44` | The 5-method ABC the design specifies already exists, with in-process / local / sql impls. |
| Conversation persistence backend selection (§12) | `KnowledgeFabric._build_conversation_store(config, db)` — `fabric.py:169`; `conversation_backend` in `{in_process, local, sql}` | Pluggable seam already present. We add one backend (below). |
| Auth passthrough to KH (§13) | `set_security_context()` / `clear_security_context()` contextvar — `handlers.py:30,40`; per-request httpx header hook emits `x-security-context`; `CallerIdentity` / `default_request_headers` | The passthrough model the design describes is already the fabric mechanism. See §3 for the WS-specific constraint. |
| Idempotent answer persistence (§12 audit) | `fabric.entities.ensure(...) -> WriteOutcome` — `entities/store.py:59` | Content-fingerprint idempotency; already the `persist_answer` pattern per `plan_assistant_vertical.md`. |

Corollary: per `plan_assistant_vertical.md`, most of the assistant vertical is already in
`jazzx_sdk.agents.interactive`. The dominant task is adoption, not construction.

## 2. The one real gap and the chosen route

The design wants conversation turns stored as KH `canonical_conversation` entities so the frontend sidebar
reads them and they double as audit (§12, D17-D20). Two facts from the audit:

- The **canonical layer has no open registry** to add a `canonical_conversation` type without a core edit
  (`_find_registry()` / `_put_routes()` are hardcoded — `canonical/store.py:66,1421`, with an inline
  "extend as more types need querying" comment). Adding a first-class type = core edit.
- `fabric.entities` stores **any** `entity_type` with no registry, queryable by field
  (`filter`/`list_all`). It already backs idempotent answer persistence.

**Route (locked):** persist via `fabric.entities` as `canonical_conversation` (parent) and
`canonical_conversation_turn` (child, keyed `(conversation_id, seq)`). We accept the trade: no typed
canonical model/validation and no typed `find()` — in exchange for zero core edit and a frontend read path
that is just `fabric.entities.filter("canonical_conversation_turn", [("conversation_id", "eq", cid)], orderby="seq")`.

## 3. Per-turn security-context contract (WS-specific, do not skip)

The security context is **ambient (a contextvar), not a per-call argument and not per-client-instance**
(`handlers.py:27`). The runtime sets it at handler entry and clears it in `finally` for job-mode. The v2
per-session-process WS model runs many turns on one long-lived process and possibly interleaves them, so:

- Set `set_security_context(<turn token>)` on the **same async task** that will call fabric, **before** the
  first fabric call of the turn, and clear it in `finally`.
- Never share one contextvar set across concurrent turns on the same task — that clobbers identity. The
  per-task set/clear is the isolation boundary.
- A single long-lived `KnowledgeFabric` + KH client per session process is correct; identity is resolved
  fresh at each outbound HTTP call from the contextvar.
- This is also the **audit-stamping mechanism**, not only auth passthrough: KH populates
  `created_by_user_id` server-side from `X-User-Id`, which `CallerIdentity.propagation_headers()` already
  forwards; `entities.ensure()`'s write path takes no explicit creator param. So honoring §3 per turn is
  sufficient for D19 audit attribution on `canonical_conversation_turn` entities — no separate client-side
  stamping step needed.

## 4. Work items (JAPES)

### W1 — `EntitiesConversationStore` (the gap-closer)
- **File:** new `jazzx_sdk/agents/interactive/memory_entities.py` (or extend `fabric/conversation_store.py`
  alongside `SqlConversationStore`; pick the location that keeps the `fabric.entities` import clean).
- **Change:** implement the `ConversationStore` ABC (`load/append/clear/load_raw/supersede`) write-through
  to `fabric.entities`. `append` writes one `canonical_conversation_turn` per message via
  `entities.ensure(...)` (idempotent), keyed `(conversation_id, seq)`; ensure/upsert the parent
  `canonical_conversation` on first append. `load` / `load_raw` read via
  `entities.filter("canonical_conversation_turn", [("conversation_id","eq",cid)], orderby="seq")`.
  `supersede` writes the compacted working view (mirror `SqlConversationStore`'s overlay idea — a
  `canonical_conversation` field or a single overlay entity; do not lose the raw turns).
- **Intent:** one store satisfies both consumers — the agent thread (ABC) and the frontend/audit
  (KH-readable entities). No new KH surface, no canonical core edit.
- **Acceptance:** a session appends N turns, a fresh store instance `load()`s them back in order; the same
  turns are visible via `fabric.entities.filter("canonical_conversation_turn", ...)`; a re-`append` with the
  same `(conversation_id, seq)` does not duplicate (WriteOutcome reports the dedupe).
- **Known v1-fragile edge (self-resolves on the `plan_kh_client_bump.md` bump):** `entities.ensure()`'s
  pre-check matches by name, then compares content-hash among same-named candidates. If a turn is ever
  *edited* (same `(conversation_id, seq)` key re-appended with different content — not a plain re-append),
  v1's name-uniqueness 409s and the fingerprint won't match the old hash, so `WriteOutcome.object` can come
  back `None`. Plain append-only writes are unaffected. Once KH v2 content-hash uniqueness lands, same-name
  different-content entities coexist and this disappears — don't block W1 on it, just don't build turn-edit
  support on top of `ensure()` until the v2 bump lands.

### W2 — wire the new backend
- **File:** `jazzx_sdk/fabric/fabric.py`, `_build_conversation_store` (line 169); `jazzx_sdk/fabric/config.py`
  (`conversation_backend` field / validation).
- **Change:** add `conversation_backend="entities"` (or `"kh"`) that constructs the W1 store bound to
  `self.entities`. Keep `in_process` the default.
- **Intent:** the assistant service opts in via config, same pattern as `sql`; nothing else changes.
- **Acceptance:** `FabricConfig(conversation_backend="entities")` yields a `fabric.conversation` whose
  writes land as `canonical_conversation_turn` entities; existing backends unchanged (default still
  `InProcessConversationStore`).

### W3 — per-turn security-context context manager
- **File:** `jazzx_sdk/handlers.py`, beside `set_security_context` / `clear_security_context` (lines 30-43).
- **Change:** add an async (or sync) context manager `security_context(token)` that sets on enter and clears
  in `finally`, so the WS turn loop wraps each dispatch in `async with security_context(turn_token):`.
- **Intent:** make the §3 contract a one-liner the assistant cannot get wrong; removes hand-rolled
  set/clear in the WS worker.
- **Acceptance:** entering sets the contextvar (verified via `get`-equivalent), exiting clears it even on
  exception; nested/concurrent tasks do not see each other's token.

### W4 — adoption doc (thin)
- **File:** new `docs/assistant_on_fabric.md` (or a section appended to `plan_assistant_vertical.md`).
- **Change:** a short "assistant WS on fabric" map: grounding via `fabric.docs.materialize` +
  `fabric.entities` + `fabric.guidance`; persistence via `conversation_backend="entities"`; auth via
  `security_context(...)`. Point the assistant team at the surfaces, not the KH client.
- **Intent:** the "SDK enriched so they write minimal code" hand-off; make the deprecation actionable for
  the other engineer.
- **Acceptance:** doc lists each v2 §9/§12/§13 KH call and its fabric replacement with a working signature.

## 5. Explicitly deferred / not doing

- **First-class canonical `canonical_conversation` type + registry hook.** Sidestepped by W1 (entities
  route). Revisit only if typed canonical `find()` / validation on conversations is required — that is the
  §16 "custom canonical type registration" ask, now optional rather than blocking.
- **`SqlConversationStore` for conversations.** Available and durable, but persists to the service DB, not
  KH; it does not satisfy "frontend reads the conversation from KH." Not chosen. Keep as the fallback if the
  entities read path underperforms.
- **Inbound WebSocket in japes (§16, D5).** Out of scope for *this* plan — it is the one true net-new japes
  deliverable and the design's critical path. Track separately.
- **RAG pack/status-scoped search; `RAGStore.list_collections`.** Minor; guidance already works around it.
  Only touch if the guidelines path needs it.

## 6. Open questions for the design owner (Notion page author)

These decide whether the plan above is complete. They are the follow-ups to the "deprecate KH for fabric"
message already sent:

1. **Frontend read contract (§12, D20):** confirm the frontend can read the thread via
   `fabric.entities.filter(entity_type="canonical_conversation_turn", conversation_id=...)` rather than a
   first-class canonical type. If it must be a typed canonical entity, W1 changes and W4/W5 pull in the
   canonical registry hook (extra japes work).
2. **Audit sufficiency (§12, D19):** are the `canonical_conversation_turn` entity rows (with
   `model_name` / `invocation_id` / `interrupted` fields) a sufficient audit record, or is a separate
   `AssistantAnswer`-family record still required in parallel? (Attribution itself — *who* wrote the row —
   is already covered: KH's `created_by_user_id` populates from `X-User-Id` via the existing §3 passthrough,
   no new mechanism needed. This question is only about record *content* sufficiency.)
3. **Auth mechanism (§13, D6):** confirm the assistant will thread identity through
   `set_security_context()` / the `security_context(...)` manager (contextvar), not by manually setting an
   `x-security-context` header on a KH client. Confirm the per-turn/per-task isolation requirement is
   acceptable in the per-session-process model.
4. **Guidelines home (§9):** move the guidelines collection onto `fabric.guidance` (versioned, pack-scoped)
   or keep a raw RAG-collection download for parity with v1 first, then migrate?
5. **§16 retirement:** with fabric in place, confirm the only remaining net-new japes dependency is the
   inbound WebSocket; "custom canonical type registration" becomes optional and "custom ConversationStore
   wiring" is satisfied by `fabric.conversation` + W1/W2.
6. **PII redaction before persistence:** `fabric.entities` is a broadly-queryable, frontend+audit-readable
   surface — a materially wider blast radius than a private DB row. Loan/financial chat turns plausibly
   carry account numbers/SSNs in free text. Should `EntitiesConversationStore.append()` redact PII from
   turn content before persisting? If yes: what's redactable, and does the frontend need the raw value
   verbatim? (This session's `redact_secrets`/`redact_before` guardrails are shaped for secrets — API
   keys/tokens — not PII, so this is a new build item if the answer is yes, not an existing primitive to
   wire in.)

## 7. Verification

- Unit: W1 round-trip (append → load → filter), W2 backend selection, W3 set/clear-on-exception + isolation.
- Grounding parity: a real loan session downloads grounding once via `fabric.docs.materialize` and a second
  turn performs zero download (trace-verified), matching the design's P2 exit criterion.
- Contract: no direct `KnowledgeHubClient` construction remains on the assistant turn path — every KH touch
  goes through `ctx.runtime.fabric.*`. Grep the assistant repo for raw client use as the cutover gate.
