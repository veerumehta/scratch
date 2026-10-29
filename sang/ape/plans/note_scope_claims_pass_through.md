# Note: scope claims as a generic pass-through (the sub-tenant request, PR #101)

Status: design only, no build, no spend. Written 2026-10-28 for opus-xrepo and the user.

## The ask

PR #101 forwards a shared workspace id ("sub-tenant": copy-on-write overlay on base data, enforced by RLS in kernel, KH and
common; active only in shared runtime mode) from `header.jazzx_context.sub_tenant_id` of a queue message to kernel as
`x-sub-tenant-id`, with a second contextvar and set/clear pairs at three doors. Overlay, promotion and discard are platform
domain; the SDK should only carry the value. This note is the generic version.

## What the code does today (checked on v2.6.7)

- One builder serves the three doors: `message_invocation_context(security_context, tenant=, trace_id=)` in
  `authority/context.py`, called from `queue/processor.py`, `server/app.py` (/invoke) and `server/inbound.py` (sync router).
  It builds an `InvocationContext` only when the message carries an identity and no ambient context exists, and resets the
  one existing contextvar on exit. Nothing else needs a set/clear pair.
- Tenant already rides the body as `message.context["tenantId"]` (an unvalidated str), not in the header.
- Outbound headers come from `identity.default_request_headers()`; the kernel client narrows them with
  `KERNEL_HEADER_ALLOWLIST = ("x-security-context", "x-request-project-id")` in `client_layer.py` (PAGI-1612: kernel wants only
  those). Under a verified principal, raw identity headers are dropped and the verified context is forwarded instead
  (`_default_request_headers`).
- `MessageHeader` has no free mapping today; `PermissionScope` selectors have a closed axis registry
  (`assistant skill tool ref doc_source mount canonical docs ground`), with `role permission tenant` reserved (never named
  in a selector; the context carries `tenant_ref`).

## Design

### 1. Wire: `MessageHeader.jazzx_context` is a validated `dict[str, str]`

Keep PR #101's wire name (the contract is already drafted) but give it no JazzX-specific meaning in the SDK. Validator:

- keys match `^[a-z][a-z0-9_]{0,63}$`; values are `str` only (a dict, list, number or bool is refused, which is what
  kernel#883 needed: a dict reached an HTTP header);
- values printable ASCII, no CR/LF/NUL (header-injection guard), length cap per value, entry cap, total-bytes cap, each a named
  constant in the module;
- not echoed on the response (`correlation_key` already matches request to response); echo only when a consumer shows it needs
  one.

An undeclared key (see 3) is shape-checked and kept in the context mapping but never forwarded or interpreted: it may be
another host's.

### 2. `InvocationContext.claims`: an immutable `Mapping[str, str]`

Built inside the one `message_invocation_context` (new keyword `claims=`; the three doors pass `header.jazzx_context`). No
new contextvar and no new set/clear pairs: the claims live and die with the context, which is already reset in the builder's
`finally`. `descend()` copies the mapping; no hop can edit it (`MappingProxyType`). PR #101's second contextvar and its three
set/clear pairs are not needed.

### 3. Host declares which claims exist and where they go

A host registers specs at startup (`register_scope_claims([...])`; the SDK ships none):

```
ScopeClaim(name="sub_tenant_id", header="x-sub-tenant-id", kind="uuid", max_length=64,
           clients=("kernel",), required=False, sources=("token", "message"))
```

`kind` is `uuid` or `string` (length-capped). Forwarding has one seam: `default_request_headers()` adds the declared headers of
the ambient context's claims, and the per-client allowlist becomes a function (`kernel_header_allowlist()` = the two fixed
names plus the declared headers whose `clients` include kernel; same for KH if the host says so). A host that supplies its
own `request_headers_provider` gets what it asked for and no claim headers; the docs say so. Plato's wiring declares
`sub_tenant_id -> x-sub-tenant-id (uuid)` and nothing else. The SDK then names no workspace or sub-tenant anywhere.

### 4. Trust

| Door / state | Where a declared claim may come from |
|---|---|
| Queue message | the message header (a queue is a trusted producer path) |
| /invoke or sync router, verified principal (OIDC) | the verified token's claim of the same name, or the body only where the spec lists `message` in `sources` (the body is caller-supplied; entitlement to a sub-tenant is the data layer's RLS decision, not the SDK's); never a raw inbound header |
| Trusted-gateway path (no verification) | the raw header named in the spec, accepted on the same switch that admits raw `x-user-*` today |

A body value that disagrees with the token's refuses (see 5); equal values pass.

### 5. Refusal, never silent drop

A declared claim that is present but invalid (not a UUID for `uuid`, over its cap, wrong type, from a source the spec does
not allow) raises a typed `ScopeClaimRefused` (code `scope_claim_invalid`, names the claim and the rule, never echoes the value
into logs); queue: a failed response carrying it; HTTP: 400 through the error-serving path. Missing claim: nothing forwarded
(`required=True` in a spec refuses a missing one; Plato says false). A claim with no identity to hang it on (message has claims
but no security context and no ambient context) also refuses for a declared claim.

No strict-off flag, and I argue against one: the tolerant-first rule is about parsing documents and records, and here failing
open means a request meant for an overlay silently reads or writes base data. That is a wrong-scope answer, worse than a
refused call. If the user still wants one, it is a per-spec `on_invalid="drop"` the host sets, never a global switch.

### 6. Permission selector grammar

No generic scope axis now. `tenant` is already reserved (data scope belongs to the context, not to a grant); a sub-tenant is
the same class, enforced by RLS where the data lives. Add nothing. If the SDK itself ever has to gate on a claim (say, deny a
tool inside a shared workspace), the answer is a generic `scope:<claim>/<value>` axis, built when a real case exists, not now.

## Generic versus named

Generic (SDK): the header mapping and its validator, `InvocationContext.claims`, the claim spec registry, the validator kinds,
the forwarding seam, the refusal type. Named (outside the SDK): `sub_tenant_id`, `x-sub-tenant-id` and the kernel contract in
Plato's wiring; RLS semantics in kernel/KH/common. The typed `JazzxContext` model suggested to the PR author collapses into
this mapping: the typed accessor lives in the host (`ctx.claims.get("sub_tenant_id")`), so the SDK needs no model for it.
`message.context["tenantId"]` could fold into the same mapping later; not now.

## Cost and order

About 300 lines with tests: `models.py` validator (~30), `authority/context.py` field and builder keyword (~30), `identity.py`
registry and header seam (~50), `client_layer.py` allowlist function (~10), Plato wiring (~5), tests (~170: validator
rejections, builder per door, trust table rows, header seam with and without a declared claim, allowlist per client, a
refusal that is typed and never drops). One commit if kept small, otherwise validator and builder, then forwarding. No
provider spend. Suggested for 2.6.7 if the PR is to land on it; otherwise after the rerun and `stop_reason` items.

## For the user

1. Refuse a declared claim sent without any identity (above), or accept it on the trusted-gateway path only?
2. `on_invalid="drop"` per spec: yes or no (recommended no).
3. Keep the wire name `jazzx_context`, or rename to `claims` before PR #101 lands (it is cheaper to rename now)?
