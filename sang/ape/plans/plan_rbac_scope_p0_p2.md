# RBAC scope, first slice: selector grammar (P0) and require-context (P2) at HEAD (sonnet-runtime, 2026-10-21)

Scope (user-approved routing via opus-xrepo): P0 and P2 of `plan_JDK_RBAC_PERMISSION_SCOPE_AND_PACK_KEYS.md` only. P1, P3, P4 and
P5 wait on that draft's section 9 decisions (9.1 to 9.4). Plan first; nothing built; next batch, after the 2.6.5 squash is
pushed; no version bump. This document corrects the draft against HEAD (`v2.6.5`) and orders the work.

## 1. What the draft gets wrong at HEAD

1. **"No service entry point establishes an `InvocationContext`" (G4, section 6) is wrong.** Establishment exists:
   `ServerSettings.require_identity` (`server/app.py:53`) adds `SecurityContextGate`, which builds a context from the request's
   identity headers (`build_invocation_context_from_headers`, `authority/context.py:~130`) and sets it for the request; every
   `GovernedRouter` route does the same when asked (`server/governed_http.py:~98`); `config/posture.py:~65` refuses to start a
   strict tier (staging, production, `JAPES_STRICTNESS=strict`) with `require_identity` off, naming the fail-open as the reason; and
   Plato's own default settings are `require_identity=True` (`plato/app.py:55`), read from the environment by
   `plato/__main__.py:_require_identity_from_env`. What is true: (a) it is opt-in and off in non-strict tiers; (b) the context
   it builds carries `PermissionScope.unrestricted()` (selectors `[""]`), so it narrows nothing: no production code builds a
   narrower scope than that, and no pack or data file in the repo declares a selector; (c) the queue path
   (`jazzx_sdk/queue/processor.py`) neither establishes a context nor carries identity (only a durable `TurnRun` stores and
   restores one, `runs/runner.py:restored_caller`); (d) `GovernedRouter` builds a second context beside the gate's and clears it
   (`clear_invocation_context`, not a token reset) when its dependency exits.
2. **Section 11 item 9: yes.** Plato establishes a context on every route when `require_identity` is on, through the gate (and
   again in `GovernedRouter` routes). It is unrestricted and has no tenant.
3. **`queue_processor.py` does not exist**; the path is `jazzx_sdk/queue/processor.py` (and `queue/execution.py`).
4. **"Identity verification is absent; OIDC is out of scope" is stale.** `safety/oidc.py` exists: `OidcSettings`, `TokenVerifier`
   (JWKS cache, audience and https checks, rotation refetch) and `identity_from_claims`, which returns the same shape
   `x-security-context` carries. Nothing wires it: no server module, no Plato route imports it. P2 should be the place it is
   consumed (behind a seam), not improvised.
5. **The axis registry (3.2) omits axes the code mints today**: `mount:` (adjudication `EvidenceWorkspace`,
   `workspace.py:47`), `canonical:` and `docs:` (knowledge bindings, `agents/interactive/knowledge.py:77`), `ground:`
   (`pipelines/grounding.py:435`), plus pack-declared free strings (`GroundSource.hops`). Minted and admitted by `admit_hop`
   today: `assistant:` (`agent.py:666, 1152`), `skill:` (`:936`), `tool:` (`:949, 972, 1076`), `ref:` (`:988`), `doc_source:`
   (`:980`), and those four. The draft's `connector:` is only a provenance label (`pack/evidence_tools.py:161`), not an admitted
   selector; `mode:`, `process:`, `action:` and `resource:` are new (P1 and later, not P0).
6. **`*` and `""` already mean "everything".** `PermissionScope.unrestricted()` is `[""]`; tests use `["*"]`
   (`tests/test_authority.py:288, 322`; with the raw prefix matcher a lone `*` admits nothing, those tests never rely on it). The
   draft's "`*` only as a trailing whole segment" needs a rule for a lone `*`.
7. **`warn` mode as drafted would break callers.** "Establish an empty-scope context" in `warn` mode makes every hop deny (an
   empty `resource_selectors` admits nothing), which is `enforce` by another name. A warn mode has to keep admitting and log: it
   instruments the fail-open branch of `admit_hop` instead (section 4, P2.2).
8. **Tenant is not on the context, and where it comes from matters.** Each route resolves a tenant with a host-supplied
   `tenant_from_request(request)` (`fabric/tenancy.tenant_of`); Plato's is the client-supplied `X-Tenant-Id` header
   (`plato/wiring/default.py:521`). A tenant on the context is only as trustworthy as that header; with verified OIDC claims the
   tenant should come from the claim and a mismatch should refuse.
9. **Where Plato's own author and reviewer gates fit.** `server/authoring_roles.py` (`AuthoringRoles`: author and reviewer from
   the roles a gateway forwards, names set by `PLATO_AUTHOR_ROLE` and `PLATO_REVIEWER_ROLE`), `plato/api/authoring.py:85`
   `_refuse_unless_author`, the same helper in `pack_review`, `catalogs` and `blueprints`, and `server/gates.py`
   (`write_gate` and `read_gate`) are not scope checks. The first two read the caller's identity roles straight from
   `CallerIdentity`; the gates are posture checks (`withholding`: strict, an auth dependency, required identity). The draft's
   ban on a `role:` selector axis does not touch them: they never go through `PermissionScope`. Recommendation: leave them as a
   deliberate platform-owned exception in P0 and P2 (Plato's own actions, env-configured role names, not a pack's vocabulary);
   when P1 and P3 land, Plato's actions can be declared as `action:plato/...` keys and `AuthoringRoles` becomes one scope
   source among others, but that is P3's decision with 9.1, not this slice. `server/directory.py` (`UserDirectory`) is a
   reviewer-picker over a gateway directory; it has no part in authorization and needs no change.
10. **Segment-boundary matching is a real defect (3.1, section 10).** `PermissionScope.admits` is
    `selector == c or selector.startswith(c)` (`context.py:~84`): `skill:aml` admits `skill:amlanything`, and `tool:read` admits
    `tool:read_secret`. Confirmed; no test pins the raw prefix behavior. Section 4 says how existing bare-prefix grants keep
    working.
11. Smaller: `admit_hop` returns `(True, None)` with no ambient context (`:~266`) while `check_hop` raises
    (`require_invocation_context`) as the draft says; `InvocationContext` has `principal_ref`, `actor_class`, `permission_scope`,
    `human_initiated`, `matrix`, `binding`, `overlay`, `execution_profile`, `trace_id`, `depth` and no tenant or audience;
    `common/core/keto` has `check_permission`, `batch_check_permission`, `require_project_permission` and reads `enable_keto`
    (default `False`) in `runtime.py`, `authorization.py` and `dependencies.py`, as the draft says (not needed by P0 or P2).

## 2. Every selector prefix minted today, and what the grammar does to it

| Prefix | Minted at | In the draft's registry | Proposed |
|---|---|---|---|
| `assistant:<spec name>` | `agents/interactive/agent.py` turn entry and spawn | yes | keep |
| `skill:<name>` | `agent.py` parent tools | yes | keep |
| `tool:<name>` | `agent.py` (3 sites) | yes | keep |
| `ref:<name>` | `agent.py` per-skill narrowing | yes | keep |
| `doc_source:<name>` | `agent.py` per-skill narrowing | yes | keep |
| `mount:<name>` | `agents/adjudication/workspace.py` | no | add to the registry |
| `canonical:<Class>` | `agents/interactive/knowledge.py` | no | add |
| `docs:<name>` | `agents/interactive/knowledge.py` | no | add |
| `ground:<name>` | `pipelines/grounding.py` (default hop) | no | add |
| pack-declared `hops` | `GroundSource.hops` strings | no | must parse under a registered axis, else a load finding |
| `loan:<id>` | tests only | no | test fixtures move to a registered axis, or the registry gains a test-only axis |
| `connector:` | a provenance label, not admitted | draft: new | not a selector yet |

A segment's characters: the draft's `[A-Za-z0-9_.:-]+` has to be checked against the names the code mints (assistant spec
names, skill and tool names, document source names, canonical class names). The validator's character set is derived from a test
that builds every selector the repo mints from real fixtures, so a name with a space or a slash is found before it is refused.

## 3. P0: grammar, registry, validator, boundary matching (S-M, five commits)

Order, tests first, one commit each.

1. **Boundary matching (S).** New matcher in `authority/context.py`, with the test `skill:aml` does not admit `skill:amlanything`
   written failing first. A grant `c` admits `s` when: `s == c`; or `c` ends with a delimiter (`:` or `/`), the axis-wide and
   path-wide forms already in use (`tool:`, `loan:` in the class docstring) and `s.startswith(c)`; or `c` ends with `/*` or `:*` and
   the rest is a prefix at that delimiter; or `s.startswith(c + "/")` (a path grant covers its children, never a longer name); or
   `c` is `*` or `""` (everything: `unrestricted()` switches to `*`, `""` stays an accepted alias for one minor version).
   Deny entries use the same matcher, deny wins as today. `narrow()` keeps its contract (intersection through `admits`). Migration
   note for packs: a grant that relied on a raw character prefix (`skill:aml` meaning "every skill starting with aml") becomes
   `skill:aml/*` if the names are paths, or an explicit list; no pack in this repo does it. The note
   goes in the CHANGELOG and the `PermissionScope` docstring.
2. **Selector module (S).** `authority/selectors.py`: `parse_selector(text) -> Selector(axis, path, ability)`, the closed
   `AXES` registry (assistant, skill, tool, ref, doc_source, mount, canonical, docs, ground) with a `version`, reserved `role:` and
   `permission:` rejected by name, `validate_selector(text) -> list[SelectorProblem]` with codes `unknown_axis`, `reserved_axis`,
   `bad_segment`, `bad_wildcard`, `ability_not_allowed`. Pure, no SDK imports, no pack data.
3. **Builders (S).** One builder per axis (`assistant_selector(name)` and the rest) replaces the roughly twenty f-string sites
   (`agent.py`, `knowledge.py`, `grounding.py`, `workspace.py`), so the family is enumerated once and a test can hold every
   builder to the grammar (section 8 of the project rules).
4. **Validation on construction, tolerant first (S).** `PermissionScope` records `problems` and logs a warning for a grant or
   denial outside the grammar; `admits` of a selector with an unknown axis is False with the `unknown_axis` reason in the refusal
   (`check_hop`), never silently admitted. Refusing at construction is a decision for the next minor: a loud warning first, per the
   project's tolerant-first direction.
5. **Docs and CHANGELOG (S).** The grammar, the registry, the migration note, the axis table above.

Acceptance (from the draft, section 10, the P0 items): every in-repo minted selector parses; unknown axis denies with
`unknown_axis`; `skill:aml` does not admit `skill:amlanything`; deny beats allow at every specificity; `descend()` cannot widen
(a property test over generated scope pairs, new); `role:` and `permission:` rejected.

## 4. P2: require-context, in warn mode, time-boxed, with tenant (M, six commits)

Reframed from the draft because most of the middleware exists (section 1).

1. **Tenant and audience on the context (S).** `InvocationContext` gains `tenant_ref: str | None = None` and
   `audience: str | None = None` (the calling surface, from `X-Surface-Ref`, which `GovernedRouter` already reads into the
   governed context but never puts on the `InvocationContext`; the existing `binding: SurfaceBinding` field is never populated by
   the header builder either). Both default to None, so a stored `TurnRun.invocation_context` loads unchanged.
   `build_invocation_context_from_headers` takes a `tenant` resolver (the host's own `tenant_from_request`) and fills both.
2. **Warn mode on the fail-open branch (S).** `admit_hop` with no ambient context consults a process-level
   `ContextPolicy` (`allow` today's behavior, `warn`, `deny`), configured in `ServerSettings`/Plato settings. `warn` still admits
   and logs once per selector and route at ERROR with a counter, so the deployment sees where a hop runs with no context before
   it enforces. The setting carries an expiry date (comment and a lint/log line after it), as the draft asks. `deny` flips the
   branch for a surface (P5 in the draft).
3. **A principal seam that consumes a verified identity (S-M).** `PrincipalSource` protocol with `HeaderPrincipalSource` (today:
   `identity_from_headers`) and `OidcPrincipalSource` (wraps `TokenVerifier.verify` and `identity_from_claims`; the bearer token
   verified, the same `x-security-context`-shaped identity out, a tenant claim when the issuer carries one). `SecurityContextGate`'s
   `check` uses the configured source; with OIDC off it is byte-identical to today. A tenant from the verified claim that
   disagrees with the resolver's is refused (401/403 with a reason), never reconciled. Composition rule written down:
   `oidc.py` authenticates, `require_identity` says some identity was resolved, the scope source (P3) authorizes.
4. **One context per request (S).** `GovernedRouter` stops building a second context when the gate already set one (it reuses
   it, adding `trace_id`), and both restore with a token reset instead of `clear_invocation_context`, so a nested route cannot wipe
   the outer context. A test: a governed route under the gate sees one context object with the gate's tenant.
5. **Queue and job entry (M).** `queue/processor.py` establishes a context from the message's identity headers when it carries
   them (and warns, in `warn` mode, when it does not), through the same builder, and clears it with a token reset. Needs a read of
   what a queue message carries before it is sized; if it carries no identity, the first step is to carry it (a message field),
   which is a contract change to flag.
6. **Plato (S).** Plato passes its `tenant_from_request` to the gate so its context carries the tenant, sets the policy from its
   settings (`warn` until the date), and the Expert route's tests assert the context it runs under.

Acceptance: no HTTP, queue or job entry runs without a context once `deny` is set for it; in `warn` it is logged with the route
or queue name; the context carries tenant and audience; with OIDC off nothing changes; with OIDC on a bad token is refused and a
tenant mismatch is refused.

## 5. What P2 must provide for the Expert visibility envelope (2.7.0 P4)

The envelope is per pack and per audience (one `SurfaceBinding` per calling surface, `surface_type=API_SERVICE`, the Expert plan's
user decision). For it P2 provides, per request: `tenant_ref` (the envelope is read for a tenant's published pack),
`audience` (the surface the call came through, from `X-Surface-Ref` or a verified claim), a verified principal and its roles
(the `PrincipalSource`), and an `InvocationContext.binding` populated from the pack's binding for that audience so the existing
`check_action` and the envelope's question-class check read one place. The envelope's own enforcement then needs two things
outside P2: an `expert:` axis (policy, playbook) in the closed registry (an SDK change in P0's registry, one line once the
registry exists, so P0 should land first), and a visibility check at the Expert route (`admit_hop(expert_selector(...))`
before the operation), which P4 adds. Advisory-by-construction (a binding granting above advisory fails validation) is P4's
validator, not P2's.

## 6. Order and effort

P0.1 boundary fix, P0.2 module, P0.3 builders, P0.4 construction warning, P0.5 docs (S-M together); then P2.1 tenant and
audience, P2.2 warn policy, P2.4 one context per request, P2.3 principal seam, P2.5 queue entry, P2.6 Plato wiring (M together).
P2.1 and P2.2 first: they are small and give opus-xrepo's Expert P4 its inputs and the warn data the draft's P5 needs.
Open for the user, none blocking P0: whether a lone `*` and `""` both stay (recommended: `*` canonical, `""` an alias for one
minor); whether construction-time refusal of an unknown axis follows the warning in the next minor (recommended); whether the
queue message should start carrying identity (needs the queue owner).

## 7. Review points folded in (user's critique, 2026-10-21)

These change sections 3 and 4; where they conflict, this section wins.

### 7.1 Tenant: the cheap invariants now, the audit deferred
Production is single tenant today, so only what is hard to retrofit is kept.
- **Kept (P0 and P2.1, all small).** `InvocationContext.tenant_ref` is optional (None allowed by default, no policy change).
  Selectors are tenant-implicit: `admits(selector)` is always evaluated inside one tenant, a selector never names one, and a
  grant has no cross-tenant form. `tenant:` is a reserved axis the validator rejects, like `role:`. `descend()` takes only a
  narrower `permission_scope` and cannot change `tenant_ref`, `principal_ref`, `actor_class` or `audience` (a test builds a child
  with a different one and expects it refused). `require_tenant(tenant)` exists beside `tenant_of`, raising when a call's tenant
  differs from the ambient context's, and is called nowhere by default.
- **Deferred, trigger: a second tenant.** Making `tenant_ref` required, and the store audit and fixes. Recorded as
  `TODO(tenant-keyed-store-reads)` at `fabric/tenancy.py`'s `tenant_of`, naming the trigger. `fabric/tenancy.py` already proves
  every registered table has `tenant_id` in its key, so the schema is covered; what is not covered is the list below. It is from
  a grep for the word, not an audit, and each needs a read when the trigger fires: `runs/store.py` and `runs/store_db.py`
  (`TurnRun` rows shared, the tenant only in the run's `input` JSON via `input_equals`, so an omitted filter reads every tenant's
  runs: the first to fix), `runs/turn_store.py`, `conductor/suspension_store*.py`, `queue/execution_db.py`,
  `automation/idempotency_db.py`, `llm/cost_store.py`, `manifest/store.py`, `agents/definition_store*.py`, the fabric `db`,
  `blob`, `collections`, `conversation_store`, `docs`, `entities`, `graph` and `rag` stores, `guidance/eval_service_store.py`,
  and `evaluation/experiment/store.py` with the mlflow experiment store.

### 7.2 Non-human principals
`actor_class` already separates agent from human but a queue job, reaper, eval runner or scheduler is neither. P2 adds
`principal_kind` (`human`, `service`, `job`) and for `job` and `service` a `principal_ref` of the role (`job:run-reaper`,
`job:feedback-process`, `job:eval-reclaim`, `job:session-reaper`, `job:migrate`, as named in `plato/jobs.py`), established by the
entry that starts the work (the job runner, the queue processor), not by headers. A job's scope is declared per role, small and
tenant-wide where the job is (a reaper works across tenants by design; that is the one place `tenant_ref` is a set the role
declares, never a client value), and `human_initiated` is False. A queue message that carries work for one tenant restores that
tenant, the originating principal as `on_behalf_of` (a field, never the acting principal), so the audit shows who asked and what
ran.

### 7.3 Audience is the Expert plan's definition
One definition: `audience` is the calling surface, the same string the Expert envelope keys its per-audience binding on
(`X-Surface-Ref` / the `SurfaceBinding.surface_ref`). P2 does not invent a second field; the Expert plan and P2 import it from
one place (`authority/context.py`), and a request with no surface is audience `None`, which the envelope treats as the
most-restricted default.

### 7.4 Delegation
`authority/delegation.py` is `resolve_authority`: given a role and the case's attribute values it walks an `AuthMatrix`'s
`escalation_target` chain to the role whose ceiling covers the decision (human approval authority). It is a different axis from
`descend()`: `descend()` narrows what one machine call may reach; delegation picks which human role approves. Relation, to be
written down in both docstrings: delegation never widens a scope (the role it resolves is an approver, not a grant), the resolved
approver acts under their own context (own tenant check, own scope), and a delegated approval is recorded as
`delegated_from` on the approval, never by copying the delegator's context. No code change in P0 or P2.

### 7.5 Reachability versus autonomy, structurally
A scope entry is a selector string only: no level, no approval, no `human_only` field, and the validator rejects any such key
in a loader (P3's `permissions:` block too). The two layers answer different questions: `PermissionScope.admits` is
"may this request reach the thing", `check_action` is "at what autonomy may it act". Precedence when both apply: reachability
first. A scope denial returns the `OUT_OF_SCOPE`/scope refusal and `check_action` is never consulted (nothing about an
unreachable cell is revealed); a reachable cell with `human_only` still refuses a non-human initiator with
`HUMAN_ONLY_ACTION`; a scope denial wins over a human-only cell for a human too. One test per cell of that table.

### 7.6 The CI check
The draft's grep for `RESOURCE:ACTION` literals would match `HTTP:GET` and `MODE:LIVE`. Restrict it to the two places
that mint or read keys: calls to the `action:` builder (`action_selector(...)`) and the `permissions:` loader, and have it run
the real validator over those values instead of pattern-matching source text.

### 7.7 Doors P0 and P2 must not close (later phases, no action now)
- **Hiding a skill the principal cannot use changes the prompt prefix** per permission set, and prompt caching is pinned by
  `prompt_cache_key`. Before any hiding is built, measure the hit rate across permission sets; then leave a trace record
  and a surface message (`skill unavailable: <reason>`) rather than silent absence. P0's builders and the refusal reason code
  must therefore carry which selector was refused, so that record can be written.
- **`persona_resolution` is not an SDK default.** It is required whenever a pack declares more than one persona, with
  `EXPLICIT` the safe choice; the loader refuses a multi-persona pack that leaves it unset. Nothing in P0 or P2 defaults it.
- **A Keto batch check per turn** needs a latency budget and a cache (per principal, per tenant, short TTL with the Keto
  revision as the key); the scope source (P3) is where it goes, behind the same `PermissionScope`, so P0 and P2 stay
  provider-neutral.
- **The `ENABLE_KETO` shim** may be unnecessary (no compatibility constraint from the one consumer); P2 does not add or keep
  one, and `common/core/keto` is untouched.
- **9.1 stays the user's decision.** The recommendation recorded here for them: the pack declares the key space, holder data
  lives in a tenant-scoped store the control plane owns and writes to Keto, and any app-repo YAML is seed data only.

### 7.8 Steps changed
P2.1 stays S: an optional `tenant_ref`, `principal_kind`, `on_behalf_of` and `audience` on the context, the `require_tenant`
helper unused. No store reads. P2.5 (queue entry) establishes the `job` principal with the role, not headers. P0.2 adds `tenant:`
to the reserved axes. P0.1's matcher test gains: no grant crosses a tenant. New tests: `descend()` cannot change tenant,
principal or audience; the reachability-before-autonomy table; a loader rejects a level or approval key in a scope entry. The
RBAC build stays in the next batch, after replicate stability.
