# Plan: Unified snake_case queue envelope

Status: proposal (gitignored planning doc). Owner: japes SDK.
Goal: converge japes' queue wire contract (`jazzx_sdk/models.py`) toward one well-designed
snake_case envelope that keeps the structural rigor of flowable-core's generic `MessageEnvelope`
while staying compatible with what macer/flowable exchange today.

## Why

flowable-core (the BPMN process engine) drives japes handlers (japes-macer, japes-document-analyzer)
over Azure Storage Queues. It ships **two** envelope families:

- **Generic** (`MessageEnvelope`/`ResponseEnvelope`, camelCase): has `inline`, `payload.data.targetId`,
  nested `result.{status,data,metadata}`, typed `error.{code,message,details,retryable}`, process-origin
  `source`, W3C `traceparent`.
- **Macer** (`MacerMessageEnvelope`/`MacerResponseEnvelope`, snake_case): flat `payload.data`,
  `target_id` in `header.source`, root-level `status`/`error`, thinner `error.{message,type,invocation_id}`.

japes/macer speaks the **Macer** variant. On substance the generic is the better-engineered contract
(inline for >64KB payloads, structured response metadata, a `retryable` error flag for retry-vs-DLQ,
process-origin traceability). The Macer variant is a Python-ergonomics fork that codifies what macer
already emits. The real debt is maintaining two variants — that's where skew is born.

North-star: japes replaces kernel in v2 and should own one canonical wire contract — the generic's
bones, snake_case skin.

## Verified findings (against code, not the design doc)

1. **macer emits NESTED tracking** — `ResponseMessage(header=ctx.message.header, ...)` mirrors the
   request header as-is; `MessageHeader.tracking` is a nested model. Wire shape:
   `header.tracking.{trace_id,span_id,notepad_pointer_id}`. Uses japes SDK models, not hand-built dicts.
   (`macer/src/macer/japes/main.py`, `jazzx_sdk/models.py`, `jazzx_sdk/queue_processor.py:356`.)
2. **macer request consumption** — reads `target_id` from `header.source.target_id`; reads
   `tracking.traceparent` (W3C) with a `trace_id`/`span_id` hex fallback
   (`macer/src/macer/telemetry.py:143-190`); no `inline` handling.
3. **flowable-core ignores unknown JSON props** — `FAIL_ON_UNKNOWN_PROPERTIES=false` on the queue
   ObjectMapper (`azure-storage-queue-support/.../config/AzureStorageQueueConfiguration.java:51-53`),
   used for all three envelope deserializers. => Adding new emitted fields is non-breaking on flowable's side.
4. **Latent bug (flowable side, not ours):** macer emits nested tracking, but
   `MacerResponseEnvelope.Header` reads FLAT `header.trace_id` — so flowable-core currently discards
   macer's response tracking (flat fields read null). Fix belongs on flowable-core (read nested / both),
   not by flattening japes.

## Proposed unified envelope (`jazzx_sdk/models.py` v2)

snake_case wire. Response stays FLAT (root `status`/`error`/`payload.data`) — does NOT adopt the
generic's nested `result.*` (that would break `MacerResponseEnvelope`). Tracking stays NESTED (macer
already emits nested; correct + consistent). New fields are additive/optional with back-compat defaults.

```python
class MessageType(str, Enum):
    INVOKE_AGENT = "invokeAgent"; INVOKE_TOOL = "invokeTool"
    AGENT_RESPONSE = "agentResponse"; TOOL_RESPONSE = "toolResponse"

class Source(BaseModel):                 # who sent it (process origin)
    service: str
    process_instance_id: str | None = None
    execution_id: str | None = None
    activity_id: str | None = None

class Target(BaseModel):                 # what to invoke (NEW, split out of source)
    target_id: str
    version: str | None = None

class Routing(BaseModel):
    queue_name: str | None = None
    reply_to_queue: str | None = None
    partition_key: str | None = None
    message_group: str | None = None

class Tracking(BaseModel):               # stays nested
    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None
    notepad_pointer_id: str | None = None
    parent_invocation_id: str | None = None
    traceparent: str | None = None       # NEW — W3C cross-service continuity

class Header(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    message_id: str = Field(default_factory=...)        # uuid
    correlation_key: str = Field(default_factory=...)   # uuid
    message_type: MessageType
    timestamp: datetime = Field(default_factory=...)    # utc
    version: str = "1.0"
    inline: bool = True                  # NEW — inline payload vs blob pointer; default True = back-compat
    source: Source
    target: Target | None = None         # NEW — reader also accepts source.target_id (tolerant)
    routing: Routing | None = None
    tracking: Tracking | None = None
    security_context: str | None = Field(
        None, validation_alias=AliasChoices("security_context", "x_security_context"))

class ErrorInfo(BaseModel):              # typed SUPERSET of both variants
    message: str | None = None
    type: str | None = None              # macer
    invocation_id: str | None = None     # macer
    code: str | None = None              # generic
    details: Any | None = None           # generic
    retryable: bool | None = None        # generic — retry vs dead-letter

class ResultMetadata(BaseModel):         # NEW — optional top-level sibling, NOT nested under result
    execution_time: float | None = None
    processing_node: str | None = None
    schema_version: str | None = None
    queue_processing_time: int | None = None
    visibility_timeout: int | None = None

class InvocationMessage(BaseModel):      # request
    header: Header
    payload: dict[str, Any]              # {"data": {...}} — flat
    context: dict[str, Any] | None = None   # {timeout, priority, retry_policy}

class InvocationResponse(BaseModel):     # response — FLAT root (Macer-compatible)
    header: Header
    payload: dict[str, Any]              # {"data": {...}}
    status: str = "success"
    error: ErrorInfo | None = None
    metadata: ResultMetadata | None = None
```

Tolerant reads (Postel): accept `target_id` from `header.target` OR `header.source`; accept tracking
nested (`header.tracking.*`) OR flattened (`header.*`) on input.

Rollout: keep existing `QueueMessage`/`QueueResponse`/`MessageHeader` names and fields; extend, don't
rename. Every new field optional. `MessageSource` gains process-origin fields; `target` is additive and
`source.target_id` stays readable for a deprecation window.

## Will it break macer?

No, if rolled out additively. Verified guardrails:

- **flowable tolerates unknown fields** (finding #3) => new emitted fields (`inline`, `target`,
  `metadata`, `error.retryable`, `traceparent`) won't fail flowable deserialization. ✓ (removes the
  one risk that wasn't in our hands)
- **Keep response flat** (no nested `result.*`) => `MacerResponseEnvelope` still parses. ✓
- **Keep tracking nested** (finding #1) => matches macer's current emit; no change to macer needed. ✓
- **All new fields optional with back-compat defaults** => current macer messages validate unchanged;
  current japes responses are a subset of the new model. ✓
- macer reads `traceparent` already (finding #2) => populating it end-to-end is a pure win. ✓

Net: safe as a **consumer** immediately; safe as a **producer** because flowable ignores unknowns.
No macer code change required for the japes-side additions.

## Large-payload handling: reference/offload, not inline

Principle: **the queue carries references, not content.** Azure Storage Queue caps a message at 64KB,
so documents and heavy artifacts must never travel inline in `payload`.

- **Documents in** — passed by reference. jaci/ci_spread sends `loan_id` in `payload.data`; the
  conductor derives `collection_id=f"ci-spread:{loan_id}"` and fetches the docs from the Knowledge Hub
  via fabric. No document bytes on the wire. (`jaci/scenarios/ci_spread/conductor.py:302`.)
- **Results out** — summary + persistence. The handler returns `ResponseMessage(payload={"data": summary})`
  and writes the spread + canonical objects through the fabric/KH, not the queue.
  (`jaci/japes_handler.py:247`, `conductor.py:269+`.)

What `inline` actually means (it's mis-named): it does NOT mean "put the document in the message." It
signals that a producer **offloaded** a large payload to blob storage and the message carries a
**pointer** (`inline: false`) for the consumer to materialize. japes already has the mechanism
(`fabric.blob` offload/materialize). But no jaci/macer path produces a blob-pointer payload today —
they use KH references — so nothing needs to set `inline`. That's why it stays deferred (adding it now
would be plumbing with no caller).

**Trigger to un-defer:** if a response ever returns a payload that is both large AND not naturally
storage-resident — e.g. the *full* spread inline (all statements × periods × line items) rather than a
summary + reference, which can approach/exceed 64KB for a complex borrower. The fix then is
`fabric.blob.offload(...)` the payload and set `inline=false` with a pointer — not "add the field and
hope." Until a path deliberately does that, `inline` (and `ResultMetadata`) stay out.

ci_spread was checked against this and is fully on the reference side — no `inline` needed.

### Two reference mechanisms (they are not the same store)

| | Backing store | Pointer | Offload logic | Governance | Used by |
|---|---|---|---|---|---|
| **KH reference** | Knowledge Hub → Azure Blob (same `common.core.storage`) | `collection_id` / `doc_id` | automatic/transparent (`use_blob_storage` flag per entity; docs are blob-first) | full (collection/RBAC/security-context); async GC via `pending_cleanup` | ci_spread docs (`fabric.docs`, `fabric.entities`) |
| **`fabric.blob`** | Azure Blob direct (or local FS) — `common.core.storage`, no KH in path | `blob://<key>` | manual (`offload(threshold_bytes)`) | none — raw spill, opaque key | japes-internal large-payload offload |

KH is effectively a **governed, auto-offloading blob layer already**: an entity row keeps `json_value`
inline in Postgres when small (indexed/queryable) and NULL-in-DB + blob-backed when `use_blob_storage`
(migration 0012); documents are stored blob-first by path (`collections/{cid}/documents/{did}/blob`).
The caller only ever sees `collection_id`/`doc_id` — KH handles DB-vs-blob placement, RBAC, and cleanup.

Pointer-resolution nuance — this drives *which* mechanism a large-payload path should use:

- **Cross-service (flowable ⇄ japes, or japes ⇄ japes):** prefer a **KH reference**. It's the
  well-integrated route — both sides already speak KH with a shared identity/security context, and the
  object is discoverable/governed. A `blob://` pointer only resolves if both sides share the same blob
  store + credentials, which isn't guaranteed across services.
- **japes-internal offload:** `fabric.blob` is cleanest — the producing handler `offload()`s and, if the
  result must go on the wire, `materialize()`s before responding (so the consumer never sees a raw
  `blob://`), or the payload stays a summary + KH reference.

So if `inline=false`/offload is ever un-deferred, the default should be **offload-to-KH-and-reference**
for cross-service payloads; `fabric.blob` + `blob://` is for japes-internal spill, not a cross-service
wire pointer, unless a shared blob store is explicitly provisioned.

### fabric.blob — improvements worth pulling from KH

`fabric.blob` is deliberately thin (put/get/delete + offload/materialize, opaque `uuid4` keys,
in-memory bytes). KH's mature blob usage suggests four upgrades — none has an active offload caller
today, so capture-not-build unless one lands:

1. **Content-hash keying (dedup + idempotent offload)** — key an offloaded blob by `sha256(payload)`
   so re-offloading the same value reuses one blob and retries are idempotent (KH's dedup/idempotency
   ethos). Small, opt-in, "right while the surface is young." *The one worth doing now if any.*
2. **Orphan lifecycle / cleanup** — offloaded blobs leak when the owning row is deleted or re-offloaded.
   KH solved this with `pending_cleanup` + async GC. In japes the home is the fabric.db⊕blob seam (an
   offloading column type that deletes the old blob on row delete/update — the already-deferred
   "auto-offloading column"). Capture; ties to that work.
3. **Streaming / spooled I/O** — `get()` returns all bytes in memory; the whole point of blob is large
   payloads. KH streams big downloads via `SpooledTemporaryFile` (spills to disk past a threshold). A
   streaming get (to a path / async iterator) removes the memory ceiling. Real, but bigger API surface
   and no caller yet — trigger: first genuinely-large offload.
4. **Key namespacing** — `offload()` mints flat `uuid4` keys; a `prefix`/namespace (tenant/collection/
   type) mirrors KH's structured paths and enables scoping + cleanup-by-prefix + debuggability. Minor.

Not worth pulling: KH's JSON-index-vs-blob trade-off (Postgres-specific) and server-side blob copy
(niche, clone-only).

## Cross-repo follow-ups (not japes changes)

1. **flowable-core:** fix `MacerResponseEnvelope.Header` to read nested `tracking` (or both) — today it
   reads flat `header.trace_id` and silently drops macer's nested response tracking (finding #4).
2. **flowable-core (optional):** if the Macer request path should carry `inline`/`target`, add those
   fields to `MacerMessageEnvelope` (currently only the generic envelope has them).

## Migration steps (japes)

1. [DONE — `a1c3d67`] **Contract test first** — `tests/test_envelope_contract.py` pins japes'
   emitted/parsed envelope to the Macer schema (nested tracking, snake_case, flat root status/error),
   with a regression guard that tracking is never flattened.
2. [DONE — `a1c3d67`] Add `traceparent` to `Tracking` + `build_invocation(traceparent=…)` (round-trips
   today; macer already reads it). OTel auto-population on produce is a handler concern, not the SDK.
3. [deferred — see Large-payload handling] `inline` + `ResultMetadata`: no producer needs them yet.
4. [deferred] `ErrorInfo.retryable`/`code`/`details`: type the error dict when a consumer uses `retryable`.
5. [deferred] Process-origin fields on `Source`; optional `Target` with `source.target_id` fallback;
   `Routing` (esp. `reply_to_queue`) — add when a consumer needs them or japes takes contract ownership.
6. Coordinate the two flowable-core follow-ups above (the response-tracking fix is done on branch
   `fix/macer-response-nested-tracking`).

## Open decisions

- **Canonical ownership:** does japes define the one envelope and flowable-core conform (v2 north-star),
  or does japes stay conformant to flowable's variants near-term? (This plan is non-breaking either way;
  it just makes japes a superset + tolerant reader.)
- **Deprecate `source.target_id`?** Or keep it permanently as an accepted alias for `target.target_id`.
- **Emit metadata/inline unconditionally** (safe, flowable ignores them) vs gate per-target until
  flowable-core models them explicitly.
```
