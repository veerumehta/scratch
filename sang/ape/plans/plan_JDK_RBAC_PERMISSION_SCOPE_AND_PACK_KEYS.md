# JDK RBAC — PermissionScope Selector Vocabulary and Pack-Owned Permission Keys

**Engineering specification for `jazzx_sdk` (JDK/JAPES), written to be executed by Claude Code**

Author: Virendra Mehta · 2026-08-30 · **Status: draft for review — not yet accepted**

**Written against:** the two Notion sources — [Assistant, Ory Keto, and Mortgage RBAC](https://www.notion.so/jazzx/Assistant-Ory-Keto-and-Mortgage-RBAC-3b42471607bf80948626e9976cef1ce8) (architecture position) and [A view of Ory Keto](https://www.notion.so/jazzx/A-view-of-Ory-Keto-in-Production-3cb2471607bf809aa683dde00992da7a) (read-only production inventory, Keto **v0.14.0**) — plus `UAF_PRD_vs_JAPES_Gap_and_Pushback.md` row 9 (RBAC), `Plato_Service_Architecture_and_Build_Plan.md` §3.3/§5.4/§7.1, `Assistant_Binding_Annex_v1_0.docx` §7.2/§11, `Canonical_Object_Schema_Specification_v1_0.docx`, and `AML_Domain_Pack_Appendix.md` §1.

> **Repo not read for this draft.** Every path and symbol below is cited from the project's own gap analysis, not from a working tree. §11 is the verification checklist Claude Code must run **first**; if an anchor has moved, fix the anchor, not the design.

---

## 0. TLDR

`authority/context.py` already ships the hard part: `PermissionScope` with exact+prefix `admits()`, deny-wins, and a `narrow()` that cannot widen; `InvocationContext` carrying `principal_ref`/`actor_class`/`permission_scope`/`matrix`/`binding`/`trace_id`/`depth` with `descend()` and ContextVar propagation; `check_hop`/`admit_hop`; and live call sites at `_check_turn_entry` (`assistant:<name>`), `_build_parent_tools` (`skill:<name>`, narrowed to `tool:`/`ref:`/`doc_source:`) and `_build_composed_skill_tool`. A refused skill is never exposed to the model — which is the right primitive and better than a post-hoc check.

**Four things are missing, and only one of them is code-heavy.**

| # | Gap | This spec |
|---|---|---|
| G1 | **The selector vocabulary is undefined.** Five prefixes exist by usage, none normatively. Nothing stops an AML pack inventing `docsource:` while mortgage uses `doc_source:`. | §3 — a closed, versioned axis grammar |
| G2 | **Permission keys have no home in the SDK's world.** Keto's `RESOURCE:ACTION` keys are owned by one app's YAML in one repo. AML and CRE would each need a copy of that machinery. | §4 — `permissions:` block on the pack manifest, and a hard ban on SDK-side constants |
| G3 | **Nothing bridges Keto's answer to a `PermissionScope`.** `common/core/keto/` has `check_permission`/`batch_check_permission`/`require_project_permission`; nothing turns "this principal's grants" into a scope object. | §5 — `KetoScopeSource`, fail-closed, with an explicit posture enum |
| G4 | **`admit_hop` fails open when no context is ambient** (`authority/context.py:210-211`) while `check_hop` raises (`:166-173`). No service entry point is required to establish an `InvocationContext`. | §6 — require-context middleware; the fix is the entry point, not the helper |

Two findings from the second Notion doc are load-bearing on the design and are carried into it as invariants: **`public` is stored as `editor`**, so a public resource is write-capable, not read-only (§3.4); and **`ENABLE_KETO=false` makes authorization return success**, so enforcement posture is part of the security posture and must be visible in the trace (§5.3), never a silent boolean.

**Scope boundary.** This spec covers the JDK only. It does not move the mortgage matrix, does not write Keto tuples, and does not decide whether Plato or the app repo owns a pack's persona matrix — that conflict is real, is named in §9.1, and is a human decision.

---

## 1. Position in the layered model

The first Notion doc's central move is refusing the word "role." This spec inherits that refusal and states where the JDK sits:

| Layer | Question it answers | Owner | JDK's role |
|---|---|---|---|
| Identity | Who is this principal? | Keycloak *(absent — no OIDC/JWT verification anywhere; identity is header-borne today)* | Consumes `principal_ref`; verifies nothing |
| Application persona | Which business role(s) do they hold? | Identity/LOS sync + Keto `Role#members` | Reads; never writes |
| Feature permission | May that persona do `RESOURCE:ACTION`? | **Pack** (this spec) → deployed to Keto | Declares the key; asks Keto the question |
| Resource access | May they touch *this* project/conversation? | Assistant/LOS sync + Keto | Asks; renders as a scope selector |
| **Reachability** | **May this principal reach this assistant / skill / tool / doc source at this hop?** | **`PermissionScope` — the JDK** | **Owns entirely** |
| Autonomy | *How* autonomously may it act once reachable? | `AuthorityMatrixV2` / `authority/resolver.py` | Owns; **kept separate** — see below |
| Workflow enforcement | Is the check performed before the irreversible work? | Flowable BPMN + Plato Plane C | Provides the key; does not enforce |

**Invariant A — reachability and autonomy are different axes and never collapse.** `PermissionScope` answers *may this run at all*. `AuthorityMatrixV2` answers *at what autonomy level, with what approval*. A pack that expresses "the assistant may draft but not execute a SAR filing" writes an authority cell (`aml.am.006` is permanently L0-advisory), **not** a scope selector. Reviewers should reject any PR that encodes an approval requirement as a scope entry — that is how the two systems silently merge and the ABA's `annex_ceiling` stops being enforceable.

---

## 2. Design rules

1. **Nothing product-shaped is a constant in `jazzx_sdk/`.** Plato §3.3's review question applies verbatim: *what row does this value come from?* A `DOCUMENT:CREATE` literal in the SDK is the jstack failure mode (a Go constant listing assistant grants) repeating in Python.
2. **Fail closed, loudly.** Absent context, unreachable Keto, unresolvable principal, unknown selector axis — all denials with a distinguishable reason. Never conflate *denied* with *could not determine*. (Second Notion doc, "Rules for answers.")
3. **Narrowing only.** `descend()` and every overlay may narrow. Widening is a certification violation, consistent with `bind_spec` and ABA §11.2.
4. **Never silently union personas.** Mortgage UI's live behaviour is single-primary (`Underwriter → Loan Processor → Loan Officer`), and Assistant routing expects exactly one row. The SDK must make resolution an explicit, recorded strategy (§5.4).
5. **Every decision is evidence.** A scope verdict emits a trace record naming the layer that decided it, per the second doc's answer contract (§7).
6. **Additive.** No existing call site changes behaviour until the pack declares a `permissions:` block and the posture is set to enforce.

---

## 3. The selector vocabulary (G1)

### 3.1 Grammar

```
selector   := axis ":" path
axis       := lowercase identifier from the closed registry (§3.2)
path       := segment ( "/" segment )* [ "#" ability ]
segment    := [A-Za-z0-9_.:-]+   |   "*"
ability    := "read" | "create" | "write" | "admin"
```

- `*` is legal **only as a whole trailing segment** (`skill:aml/*`). No infix or partial-token wildcards — `skill:aml*` is a syntax error, because prefix matching over unbounded strings is how `skill:aml` accidentally admits `skill:amlanything`.
- Matching is **case-sensitive**, exact-or-prefix-at-a-segment-boundary. Deny entries win over allow entries at any specificity. *(Confirm this matches `PermissionScope.admits()`'s existing semantics before writing new tests — if the shipped matcher does raw string-prefix matching, tighten it to segment boundaries and treat that as a behaviour fix with its own test.)*
- The `#ability` suffix is legal only on the `resource:` axis (§3.4).

### 3.2 The closed axis registry

Adding an axis is an SDK change with a version bump, not something a pack may do. Unknown axis ⇒ **deny + `unknown_axis` reason**, never ignore.

| Axis | Denotes | Example | Status |
|---|---|---|---|
| `assistant:` | An assistant identity by manifest name | `assistant:aml-investigator` | **shipped** (`_check_turn_entry`) |
| `skill:` | A skill by registry name | `skill:sar-narrative-draft` | **shipped** (`_build_parent_tools`) |
| `tool:` | A concrete tool binding | `tool:documents.chunk` | **shipped** |
| `ref:` | An inlined reference asset | `ref:aml/typologies/structuring` | **shipped** |
| `doc_source:` | A document source / collection binding | `doc_source:sar-corpus` | **shipped** |
| `mode:` | A registered mode from `MODE_REGISTRY` | `mode:governor` | new |
| `connector:` | An outbound connector from the ABA connector inventory (§9.1 of the ABA) | `connector:rfi-customer-comm` | new |
| `process:` | A BPMN process definition key the assistant may start | `process:uploadDocumentsFromDashboard` | new |
| `action:` | **A pack-owned business capability** (§4) | `action:mortgage/DOCUMENT:CREATE` | new — the Keto bridge lands here |
| `resource:` | One resource instance with an ability | `resource:project/{id}#write` | new |

Two axes are **reserved and must never be minted**: `role:` and `permission:`. Those are Keto's namespaces; mirroring them into scope-selector space would create a second vocabulary for the same facts and invite exactly the "which role do you mean" confusion the first Notion doc exists to kill.

### 3.3 `action:` — the Keto bridge point

```
action:<pack_id>/<RESOURCE>:<ACTION>
```

`<pack_id>` is the **semantic pack slug** (`mortgage`, `aml`, `cre`), not a runtime UUID, matching the Canonical Object Schema's `pack_id` rule. `<RESOURCE>` and `<ACTION>` are `UPPER_SNAKE`, and together they are byte-identical to the Keto `Permission` object string for that pack — so `action:mortgage/DOCUMENT:CREATE` maps to Keto `Permission:DOCUMENT:CREATE`.

The pack namespace is the whole point: it is what lets an AML `CASE:CLOSE` and a CRE `CASE:CLOSE` coexist. **Note explicitly for the reviewer:** Keto's `Permission` namespace is currently *flat and un-namespaced*. Two packs shipping the same `RESOURCE:ACTION` string collide in the graph today. The JDK must therefore (a) namespace on its own side, and (b) emit a `pack_key_collision` warning at pack-load time when two loaded packs declare the same raw key. Whether Keto's key space eventually gains a pack prefix is §9.2 — a cross-team decision, deliberately not made here.

### 3.4 `resource:` and the `public` trap

```
resource:<type>/<id>#<ability>       ability ∈ read | create | write | admin
```

`<type>` ∈ `project | conversation` today, extensible as Keto namespaces are added. Abilities are the namespace policy's derived permits, not stored relations — the JDK asks for an ability, never for a relation.

Three invariants, straight from the production inventory:

- **B — `public` is `editor`.** The synthetic `public` subject is stored as an `editor` relationship and satisfies read **and write**. Any JDK-side helper, log line, docstring or field name that renders `public` as "read-only" or "view" is a defect. Where the SDK surfaces a resource's public state, it must render **`public (write-capable)`**.
- **C — `everyone` ≠ `public`.** `everyone` is a distinct synthetic subject added specifically for Project reads. Two subjects, two renderings, never one "shared" flag.
- **D — `contributor` and `create` are policy-valid but unused.** The namespace defines `contributor` ⇒ `read, create`; Assistant's `KPermission` enum does not expose `create`, and no `contributor` row exists in production. The JDK's ability enum must include `create` (the policy is the contract), and any resolver that cannot express it must return `unknown`, not `denied`.

### 3.5 Rendering and reserved words

`public`, `everyone`, and any future synthetic subject are **reserved subject tokens, not principals**. A `principal_ref` equal to one of them is a load error.

---

## 4. Pack-owned permission keys (G2)

### 4.1 Where they live

A new optional block on the pack manifest, loaded by `pack/manifest_loader.py`, subject to the same fragment-overlay and `regulatory_context` rules already shipped there.

```yaml
# pack.yaml  (mortgage pack)
pack_id: mortgage
pack_version: 3.2.0

permissions:
  version: 1                       # vocabulary version, not the pack's
  keto_namespace: Permission       # external mapping target; informational
  resources:
    - resource: DOCUMENT
      label: Document
      description: Loan file documents and their metadata.
      actions:
        - action: CREATE
          label: Create document
          enforced_at: [process, api]        # ui | api | process | skill
          bpmn_ref: uploadDocumentsFromDashboard.bpmn20.xml#checkPermission
        - action: VIEW
          label: View document
          enforced_at: [ui, api]
    - resource: JAZZ_ASSISTANT
      label: Assistant access
      actions:
        - action: VIEW
          label: Discover the assistant
        - action: EXECUTE
          label: Invoke the assistant
  stale:                            # explicit revocations — see §4.4
    - LOAN_STATUS:SUBMIT
```

**What the block is *not*:** it is a **declaration of the key space and its meaning**, not a role-to-permission matrix. There is no `role:` in it and there must never be. Which persona holds which key is a deployment fact owned outside the SDK (mortgage RBAC YAML today; possibly Plato Plane B tomorrow — §9.1). The pack says *this capability exists, this is what it means, here is where it is enforced*; the environment says *who has it*.

That split is what makes the AML and CRE cases work without cloning mortgage's machinery: a new domain ships a pack with its own key space and inherits every mechanism below unchanged.

### 4.2 Validation at pack load

Fail the load, do not warn, on:

1. `RESOURCE` or `ACTION` not matching `^[A-Z][A-Z0-9_]*$`.
2. Duplicate `RESOURCE:ACTION` within a pack.
3. A key appearing in both `actions` and `stale`.
4. A selector referenced by any skill/manifest as `action:<this_pack>/K` where `K` is undeclared. **This is the rule that makes the ban in §2.1 enforceable** — you cannot request a permission the pack has not declared.
5. `enforced_at` containing a value outside the closed set.

Warn (loud, structured, non-fatal) on:

6. Same raw `RESOURCE:ACTION` declared by two loaded packs (§3.3 collision).
7. A declared key that no skill, manifest or BPMN reference in the loaded set consumes — dead capability.
8. `enforced_at: [ui]` alone. UI-only gating is not an authorization boundary; the first Notion doc §3.2 says so and the pack should be told at load time.

### 4.3 Extend `Skill` and `AssistantManifest`

The skill record already carries `version`/`visibility`/`invokes`/`inputs`/`outputs` from UAF Phase 1. Add:

```python
requires_actions: list[str] = []   # ["action:mortgage/DOCUMENT:CREATE"]
```

Semantics: at `_build_parent_tools` time, a skill whose `requires_actions` are not admitted by the ambient scope **is not exposed to the model at all** — reusing the existing and correct refusal path rather than adding a second one. This is the single highest-value integration point in the spec: it makes business permissions affect what the model can even see, which no current layer does.

On `AssistantManifest`, add the same field for turn-entry checks, so `JAZZ_ASSISTANT:VIEW` / `:EXECUTE` become declarative rather than convention. Keep them separate keys — the first doc's open question 4 is answered *yes, separate* on the JDK side by default, because collapsing them is a one-way door.

### 4.4 `stale` — carry the semantics, not the deployment

`stale` exists so the SDK can *report* an intentional revocation. The deployment behaviour (deleting only explicitly-stale tuples) stays with whoever runs the deploy. The JDK's obligation is narrow and useful: when a live Keto grant matches a `stale` entry, surface `drift: stale_grant_present` rather than treating it as a valid permission. **The JDK never deletes a tuple.**

---

## 5. The Keto bridge (G3)

### 5.1 Shape

```python
# jazzx_sdk/authority/sources/base.py
class ScopeSource(Protocol):
    async def scope_for(self, principal: PrincipalRef, *, pack_ids: Sequence[str],
                        environment: str) -> ScopeResolution: ...

@dataclass(frozen=True)
class ScopeResolution:
    scope: PermissionScope
    personas: tuple[str, ...]          # every persona observed, in observed order
    active_persona: str | None         # after §5.4 resolution
    posture: KetoPosture
    observed_at: datetime
    evidence: tuple[ScopeEvidence, ...]
    unresolved: tuple[str, ...]        # keys/questions that could not be answered
```

`KetoScopeSource` in `jazzx_sdk/authority/sources/keto.py` implements it over the existing `common/core/keto/authorization.py` client. **Batch, don't loop:** resolve a principal's whole action space with `batch_check_permission` against the loaded packs' declared key sets, one round trip per resolution. Cache per `(principal, environment, pack_version_set)` with a short TTL and an explicit `observed_at` on every result — a stale grant presented without its observation time is the exact thing the second Notion doc says never to do.

Resource-instance questions (`resource:...#write`) are **not** pre-resolved into the scope — that would mean enumerating every project. They are resolved on demand via `require_project_permission`, and the resolver must evaluate direct, `Team#members`, `public` and `everyone` paths before returning denied. *"No row returned" is not "denied" until every path has been walked.*

### 5.2 Fail-closed

| Condition | Result | Reason code |
|---|---|---|
| Keto unreachable / 5xx after retries | **deny** | `authz_unavailable` |
| 401/403 from the gateway | **deny** | `authz_forbidden` |
| Principal unresolvable | **deny** | `principal_unresolved` |
| Key declared by pack, absent from Keto | **deny** | `grant_absent` |
| Key present in Keto, undeclared by any pack | admit **+ drift warning** | `undeclared_grant` |
| Key present and listed `stale` | **deny** + drift | `stale_grant_present` |

`authz_unavailable` must be distinguishable from `grant_absent` everywhere it surfaces — in the exception type, the trace field and the log. Flowable already models this correctly with separate BPMN boundary error paths for denial versus Keto failure; the SDK should not be the layer that loses that distinction.

### 5.3 Posture is explicit, never a silent boolean

```python
class KetoPosture(StrEnum):
    ENFORCE  = "enforce"   # default
    SHADOW   = "shadow"    # evaluate, record, admit; for rollout only
    DISABLED = "disabled"  # requires explicit config + a stated reason
```

`DISABLED` must require a non-empty `keto_disabled_reason`, log at WARN on every resolution, and stamp `posture` on the trace. The production finding was that `ENABLE_KETO=false` causes checks to *succeed silently*; a deployment may still choose that, but it may not do it invisibly. Map the legacy `ENABLE_KETO` env var onto this enum for one minor version, then remove it.

### 5.4 Multi-persona resolution

```python
class PersonaResolution(StrEnum):
    PRIORITY = "priority"   # ordered list; first match wins — matches mortgage UI today
    UNION    = "union"
    EXPLICIT = "explicit"   # caller names the active persona; must be one they hold
```

Configured on the pack (`permissions.persona_resolution` + `persona_priority: [Underwriter, Loan Processor, Loan Officer]`), defaulting to `PRIORITY` so the JDK reproduces live behaviour rather than quietly widening it. `active_persona` and the strategy both go on the trace. Under `EXPLICIT`, a persona the principal does not hold is a `persona_not_held` denial, never a fallback.

**Also record the split the first doc warns about:** identity/session roles and Keto `Role#members` can disagree. When the JDK can see both, a mismatch is `drift: persona_mismatch` — surfaced, not reconciled. The SDK does not fix identity systems.

---

## 6. Require-context middleware (G4)

`admit_hop` fails open with no ambient `InvocationContext`. Do **not** change the helper — the second Notion doc's reasoning applies: the defect is that a service entry point can run without establishing context.

Add `jazzx_sdk/server/require_context.py`:

- ASGI middleware establishing an `InvocationContext` from verified identity + headers at every HTTP entry, and an equivalent wrapper for the queue path (`queue_processor.py`) and any CLI/job entry.
- Modes: `enforce` (reject with 401/403 and a reason code) and `warn` (establish an empty-scope context, log at ERROR with the route name) for a **time-boxed** rollout — put an expiry date in the config comment.
- Composes with `GovernedRouter`, which already requires `X-Trace-Id` and `Idempotency-Key` on mutations; context establishment happens before the governed route body.
- Once `enforce` is on for a surface, flip `admit_hop`'s no-context branch to deny for that surface and delete the fail-open path.
- **Carry tenant.** The Kernel salvage assessment flags tenant propagation as absent and cheapest-now. A scope resolved in the wrong tenant is worse than no scope; add `tenant_ref` to the context in this same pass.

Identity verification itself (Keycloak/OIDC) remains genuinely absent and is **out of scope here** — the middleware consumes a verified principal and must be written so that swapping header-borne identity for verified JWT claims is a one-file change. Do not let this spec become the place OIDC gets improvised.

---

## 7. Trace and explainability

Every resolution and every hop decision emits, on the `TraceStep`:

```
authz.selector           the selector asked about
authz.verdict            admitted | denied | unknown
authz.reason             reason code from §5.2
authz.decided_by         scope | keto | pack_declaration | authority_matrix | posture
authz.posture            enforce | shadow | disabled
authz.personas           observed personas
authz.active_persona     after resolution
authz.persona_strategy   priority | union | explicit
authz.observed_at        source observation time
authz.pack_version_set   which pack versions defined the key space
authz.drift              [] | reason codes
```

This is deliberately the SDK-side half of the second Notion doc's answer contract, so a future access-catalog BFF can compose "why is this person denied" from real trace records instead of re-deriving it. Reuse `OverrideEvent`'s existing vocabulary (`overriding_actor`, `authority_basis`, `reason_code`) rather than inventing a second one; do not add a parallel authz event type.

---

## 8. Build order

| Phase | Content | Size | Independently valuable? |
|---|---|---|---|
| P0 | §3 grammar + validator + axis registry + tests; segment-boundary matching fix | S | Yes — kills the vocabulary drift immediately |
| P1 | §4 pack `permissions:` block, loader, validation, `Skill.requires_actions`, manifest keys | M | Yes — packs become self-describing |
| P2 | §6 require-context middleware in `warn`, tenant on context | S–M | Yes — closes the fail-open with no behaviour change |
| P3 | §5 `ScopeSource` + `KetoScopeSource` + posture + persona resolution, `SHADOW` by default | M | Yes — produces drift data before it enforces anything |
| P4 | §7 trace fields; drift reporting surface | S | Yes — feeds the access catalog |
| P5 | Flip P2 to `enforce` per surface; P3 to `ENFORCE` per environment; delete fail-open | S | Gated on P4's drift data being clean |

P0–P2 touch no authorization outcome. P3 is where behaviour can change, which is why it ships in `SHADOW`.

---

## 9. Decisions this spec does not make

**9.1 — Who owns a pack's persona→permission matrix?** The first Notion doc puts it in the application repo's YAML, deployed by a GitHub Action. Plato Plane B claims to be the config system of record, under a hard rule that exactly one system writes any given fact. These collide the first time an AML or CRE pack needs a matrix. This spec is deliberately compatible with either — the pack declares the key space; something else declares the holders — but the question needs an owner and an answer before P3 enforces anything. *(Note the precedent: `app/assistant/promotion.py` is ~1100 lines of hand-rolled release machinery built because no proper primitive existed. A second RBAC deployment path would be the same mistake in the same shape.)*

**9.2 — Does Keto's `Permission` key space gain a pack prefix?** Today it is flat. The JDK namespaces on its own side either way, but two packs with the same raw key genuinely collide in the graph. Cross-team; needs the Keto owners.

**9.3 — Is `public` staying write-capable?** The SDK will render it honestly (Invariant B). Whether product wants a real public-viewer policy is a product decision, and doc 1's open question 6.

**9.4 — Union or priority, platform-wide?** This spec defaults to `PRIORITY` to reproduce live behaviour. Making `UNION` the default is a real product change with a real blast radius; it belongs to whoever owns the mortgage UI's role selection.

**9.5 — Does Assistant routing ever move into Keto?** Today it is DB rows with the tuple code commented out. Nothing in this spec depends on the answer, and nothing in it should be written as if Keto knows about assistant routing.

---

## 10. Acceptance criteria

- [ ] Every selector in the tree parses under §3.1 and belongs to a registered axis; an unknown axis denies with `unknown_axis`.
- [ ] `skill:aml` does not admit `skill:amlanything`.
- [ ] Deny beats allow at every specificity, including when the deny is less specific.
- [ ] `descend()` cannot widen — property test over generated scope pairs.
- [ ] No `RESOURCE:ACTION` string literal exists anywhere in `jazzx_sdk/` outside tests and fixtures — **CI-enforced grep**, in the same spirit as the import-linter contract.
- [ ] A skill whose `requires_actions` are unmet is absent from the model's tool list, not present-and-erroring.
- [ ] Pack load fails on each of §4.2's five fatal conditions and warns on each of the three warnings.
- [ ] Keto unavailable ⇒ denial with `authz_unavailable`, distinguishable from `grant_absent` in exception type, trace and log.
- [ ] `DISABLED` posture without a reason string fails startup.
- [ ] `public` never renders as read-only anywhere in the SDK, docstrings and log strings included.
- [ ] `everyone` and `public` are distinct in every rendering.
- [ ] `create` is expressible as an ability; a resolver that cannot answer it returns `unknown`, not `denied`.
- [ ] Multi-persona principal produces a recorded strategy and `active_persona`; `UNION` never happens implicitly.
- [ ] No HTTP, queue or job entry point can run without an `InvocationContext` once `enforce` is set for it.
- [ ] Every hop decision emits the §7 trace fields.
- [ ] Reserved axes `role:` and `permission:` are rejected by the validator.
- [ ] `principal_ref` of `public` or `everyone` is a load error.

**Test matrix** (mirroring the production inventory's edge cases, SDK-applicable subset): no ambient context · Keto down · posture disabled · posture shadow · unknown axis · exact vs prefix · deny-wins · descend-narrows · principal with zero personas · one persona · multiple personas under each strategy · persona held in identity but not Keto and vice versa · key declared but absent in Keto · key present but undeclared · key listed stale but present · `public` resource · `everyone` resource · team-derived access · unresolved principal · two packs colliding on a raw key.

---

## 11. Verify before writing code

Claude Code: confirm each of these at HEAD and **correct this document** where it is wrong before implementing.

1. `jazzx_sdk/authority/context.py` — `PermissionScope.admits()` matching semantics (exact/prefix, boundary or raw string), `narrow()`, deny-wins representation, `InvocationContext` field names, `descend()`, ContextVar name, `check_hop`/`admit_hop` and the fail-open branch (cited at `:210-211`, raise at `:166-173`).
2. `jazzx_sdk/authority/resolver.py` — `resolve_effective_autonomy`, `contributing_layers`; confirm the reachability/autonomy separation in §1 holds in code.
3. Call sites: `agents/interactive/agent.py` `_check_turn_entry`, `_build_parent_tools` (~`:543`), `_build_composed_skill_tool` (~`:717`) — and the exact set of prefixes currently minted.
4. `common/core/keto/authorization.py` — `check_permission`, `batch_check_permission`, `require_project_permission` signatures; `dependencies.py`; `runtime.py`; `CommonSettings.keto`; how `ENABLE_KETO` is actually read.
5. `pack/manifest_loader.py` — fragment overlay and `regulatory_context` handling, so `permissions:` composes with overlays under ABA §11.2 narrowing rules.
6. `Skill` record — current fields (`version`, `visibility`, `invokes`, `inputs`, `outputs`) before adding `requires_actions`.
7. `common/middleware/context_headers.py:HeaderMiddleware`, `handlers.py:capture_identity_headers` (~`:148`), `KERNEL_HEADER_ALLOWLIST` (~`:321`) — what identity actually arrives today.
8. `server/governed_http.py:GovernedRouter` — ordering relative to the new middleware.
9. Whether `plato/` already establishes an `InvocationContext` on Plane A; if it does, P2 is a Plato change as much as an SDK one.
10. `AuthorityMatrixV2` / `AuthorityCell` field names, to keep §1 Invariant A checkable in review.

---

## 12. Sources

- Notion — [Assistant, Ory Keto, and Mortgage RBAC](https://www.notion.so/jazzx/Assistant-Ory-Keto-and-Mortgage-RBAC-3b42471607bf80948626e9976cef1ce8)
- Notion — [A view of Ory Keto](https://www.notion.so/jazzx/A-view-of-Ory-Keto-in-Production-3cb2471607bf809aa683dde00992da7a)
- Project — `claude/UAF_PRD_vs_JAPES_Gap_and_Pushback.md` (row 9, RBAC; critical-path item 7)
- Project — `claude/Plato_Service_Architecture_and_Build_Plan.md` (§3.3 no product semantics; §5.4 single writer; §7.1 owns/projects/never)
- Project — `claude/Kernel_Salvage_Assessment_for_JAPES.md` (tenant propagation; approver identity; the `InvocationContext` cascade as the model to follow)
- Project — `Assistant_Binding_Annex_v1_0.docx` (§7.2 authority matrix; §11.1–11.2 overlay narrowing)
- Project — `Canonical_Object_Schema_Specification_v1_0.docx` (`pack_id` semantic-slug rule; vocabulary precedence)
- Project — `AML_Domain_Pack_Appendix.md` (§1, the 15-cell authority matrix — the worked example of what does *not* belong in a scope selector)
