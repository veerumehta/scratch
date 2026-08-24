# plan_JAPES_2_6_0_CONFIG_VERSIONING_D1_D2_D3_ADDENDUM — Phase 3 gating decisions, for the Notion source doc

Repos: `japes`. Companion to `plan_JAPES_2_6_0_CONFIG_VERSIONING_AND_AUDIT.md` — written to be
copied into the Notion doc that plan was derived from (*Skill, profile, and agent versioning and
audit*, JazzX Platform v2.0), so D1/D2/D3 get decided in writing there rather than defaulted into
silently once Phase 3 starts.

**Written against** `japes` `dev` at commits `e19d749` (Phase 1) / `f5156f5` (Phase 2), both
shipped and unpushed as of this writing (awaiting review). Phase 3 (versioned, immutable
Skill/AgentProfile stores) is written in the parent plan but explicitly gated on the three
decisions below — none of it should start before they're answered.

---

## What's already shipped (Phases 1–2, no gate needed)

- **Actor attribution + optimistic concurrency** on `PUT /agents/{name}`: every write now records
  who made it (`created_by`/`updated_by`, resolved from the authenticated caller — never request
  JSON); a `revision` + `If-Match` header makes concurrent writes fail loud (409/428) instead of
  silently overwriting each other, opt-in via a `strict_concurrency` flag for one release.
- **`agent_id` identity stability**: an agent's lookup identity is now a stored field, not
  recomputed on every read — a write can no longer silently change which id an agent resolves
  under (previously: a `PUT` that filled in a previously-unset `spec.agent_id` silently changed
  the row's own identity, 404-ing any existing `by-agent-id` lookup with no error anywhere).
- **Append-only `ConfigAuditEvent` audit log**: who changed what, when, with before/after content
  digests and trace correlation — wired into the write path above.

None of this needed the decisions below; it's pure defect-closure on machinery that already
existed. Phase 3 — turning Skill/AgentProfile from name-keyed-and-overwritable into versioned,
immutable, alias-resolved assets, the actual point of the source doc — does.

---

## D1 — Who is the durable system of record for skills/profiles/agent releases?

Current state, confirmed: **Builder Studio has its own DB. Services that embed the JAPES SDK
typically have their own DB too** (`DbAgentDefinitionStore`/`fabric.db`'s existing, deliberate
posture — "each consuming service instantiates this against its own Postgres, not a shared
central store"). That's already two-plus independent databases with no single owner of "what is
the current, real version of this skill/profile" — the exact gap this plan exists to close.

Three shapes are on the table, not two:

1. **Builder Studio owns authoring/governance; JAPES owns contracts, validation, and runtime
   execution.** JAPES resolves and executes against whatever Studio publishes; JAPES's own DB (if
   any) is a cache/projection, not a source of truth.
2. **Each consuming service's own DB stays the store**, as it is today — no shared control plane;
   Phase 3's versioned store is just another table in each service's existing Postgres.
3. **A dedicated JAPES SDK service — its own deployable container, with its own DB — becomes the
   shared control plane.** Under active consideration. Builder Studio (and any other authoring
   surface) publishes *into* it; every consuming service (jaci, jazzx-assistant, …) resolves
   versioned skills/profiles/releases *from* it rather than each keeping an independent local
   copy. This is a new deployment mode, not a bigger library — closest existing precedent is the
   "server runtime" tier in japes's own SDK/queue-runtime/server-runtime layering, but as a
   platform-owned config/versioning service rather than a per-consumer HTTP surface.

This isn't a japes-internal call — it determines:
- Whether **tenant scoping** (see D3) is enforced inside japes or inherited from Studio's own
  tenancy model — and if shape 3 is chosen, tenant scoping stops being optional-for-now: a single
  shared service serving multiple tenants needs real per-tenant isolation from day one, not a
  column added later.
- Whether Phase 3's `DbConfigAssetStore` is built as a **reference implementation** (protocol-
  conformant, swappable — shapes 1/2) or as **the** production store behind a real service
  boundary (shape 3) from day one.
- Who owns migration/backfill if the answer changes later, and — if shape 3 — who operates the
  new service (on-call, scaling, its own DB migrations) versus who just consumes it.

**Ask: SDK owner + Studio owner pick one of the three shapes above before Phase 3 starts.**
Phases 1–2 (shipped) are unaffected either way — they operate on a store that already exists
regardless of who ends up owning it long-term. If shape 3 is the direction, say so explicitly
here so Phase 3's store is designed as a real multi-tenant service boundary from the start rather
than retrofitted into one later.

### Independent real-world evidence: the `assistant` repo already builds this by hand

Found while surveying sibling repos for unrelated reasons — worth folding in here because it
bears directly on D1, not because anyone built it to inform this plan. The separate "Assistant
Repo" (`app/assistant/promotion.py`, ~1100 lines, a real shipped PR) is a working cross-instance
"release" system for exactly this class of asset:

- **Export walks the full dependency closure** of an assistant (agents/tools/LLMs, BPMN/DMN
  processes, roles, KH collections) and bundles it into one zip, **keyed by name** — portable
  across environments, not tied to any one deployment's DB ids.
- **Publish routes each part of the bundle to whichever service owns that asset kind**: kernel
  for agents/tools/LLMs, Flowable for BPMN/DMN, Knowledge Hub for collections, the local DB for
  roles. The assistant row itself is created *last*, so a publish that fails partway is
  resumable rather than left in a half-migrated state.
- Kernel's own agent/tool/LLM upload endpoint **upserts by name** — the same upsert-by-name
  posture F2 (in the parent plan) already flags as the wrong policy for a versioned asset. This
  is independent, real-world confirmation of that finding: a team hit the exact gap this plan
  exists to close and built a **1100-line, name-keyed, per-asset-kind-routed workaround**
  because no proper immutable-release primitive existed to reach for.

Two concrete implications for whichever D1 shape is picked:
1. This **validates Phase 4's `pack_bundle`-as-closure-carrier design** (F1) — an independently-
   built system converged on almost the same shape (one bundle, closure-walked, keyed by name)
   without knowledge of this plan.
2. If D1 lands on shape 3 (a dedicated JAPES service), the "publish routes each part to the
   service that owns that asset kind" pattern is a real, load-bearing design detail worth
   carrying forward — not every asset in a release belongs in the same store, and `assistant`'s
   system already proves that split works in production. A proper japes release primitive
   should aim to let `assistant` retire this hand-rolled system, not add a fourth option beside
   Studio's own DB, each service's own DB, and this one.

---

## D2 — `content_digest()` beside `content_version()`, or widen `content_version()` in place?

`content_version()` (japes `evaluation/prompt_registry.py`) is a 12-hex-character SHA-256 prefix,
and it's shared, unmodified, by three separate subsystems' version identifiers: `PromptVersion`,
`GuidanceAsset`, and `ManifestRecord`. Widening it in place (e.g. to a full 64-hex digest, or a
different hash) would silently change every one of those three subsystems' stored version values
— a data migration across three subsystems that nothing currently flags as needed.

**Recommendation: add a new `content_digest()` function beside it** (full 64-hex, canonical JSON),
rather than touch `content_version()`. Keep `content_version()` exactly as it is today — a short
display tag, which is what it's actually good for and already used for. `content_digest()` becomes
the thing Phase 3's version identifiers and Phase 4's `closure_digest` build on, where collision
resistance actually matters.

Phase 2 (shipped) already needed a similar "before/after content fingerprint" for audit events —
rather than pre-empt this decision, it computes its own local, private digest, scoped to
`AgentDefinition` only, explicitly not reusing or extending `content_version()`. That local digest
is not a proposal for what Phase 3 should use; it's a scoping choice to avoid deciding D2 by
accident.

**Ask: confirm add-beside (not widen-in-place) before Phase 3 starts.** If widening is chosen
instead, Phase 3 grows a dedicated migration phase for the three affected subsystems.

---

## D3 — Is there a tenant column anywhere in these stores today? (Answered — escalate the implication)

Ran the exact greps the parent plan calls for, against current japes `dev`:

```
rg -n "tenant_id|tenant" --include=*.py jazzx_sdk/agents jazzx_sdk/manifest jazzx_sdk/evaluation jazzx_sdk/fabric/db
rg -n "tenant" --include=*.py common/core
```

**Result: no tenant column or scoping mechanism exists anywhere in japes' config stores.** The
only hit in `common/core` is a telemetry/logging attribute name (`jazzx.tenant_id`, used for log
correlation, not access scoping) — not an enforcement mechanism.

This confirms the parent plan's own fallback: **adding tenant scoping in Phase 3 is a schema
decision to make with Studio, not a japes-local implementation detail.** It should be decided
alongside D1 (same owners), since "where is tenancy enforced" and "who owns the store" are the
same question asked two ways. Recommend folding D3 into the D1 conversation rather than treating
it as separate — and if D1 lands on shape 3 (a dedicated JAPES service with its own DB), this
stops being a "nice to have later" and becomes a launch requirement for that service.

---

## Net ask

Before Phase 3 (versioned Skill/AgentProfile stores) starts:
1. **D1**: SDK owner + Studio owner pick one of the three system-of-record shapes above, and settle
   tenant enforcement (D3) as part of the same conversation. The `assistant` repo's own hand-rolled
   `promotion.py` (see D1) is real, independent evidence for why this can't stay undecided
   indefinitely — teams are already building around the gap.
2. **D2**: confirm `content_digest()` as a new function beside `content_version()`, not a
   widen-in-place.

Phases 1–2 ship regardless and don't need to wait on either.
