# What `promotion.py` still does that Plato cannot

Phase 2's last acceptance item, and the one the plan calls "the real one": a written assessment of
what `assistant/app/assistant/promotion.py` does that Plato cannot, with a retirement path or an
explicit statement of what stays.

Read against `promotion.py` (1100 lines) and its caller `assistant/app/assistant/api.py` at the
current checkout. Verified by reading; not by running either system.

---

## The short version

Retirement is not blocked by code volume. It is blocked by **one disagreement about whether
creating a dependency by name is admissible**, and by **four outbound service integrations that
belong in a service whatever owns releases**.

Plato is already ahead on the part everyone assumes is hardest (the closure walk), and has nothing
at all for the part nobody counts (talking to Flowable).

---

## What Plato already does better

`expand_process_closure` is the origin of `jazzx_sdk/closure.py`, and the generalization is
faithful on every property that matters:

| Property | `promotion.py` | `closure.py` |
|---|---|---|
| Fixed-point walk with a visited set | yes | yes |
| Key first, display name second | yes | yes, via the `Resolver` contract |
| Ambiguity is an outcome, not a guess | yes, warns and skips | yes, `AMBIGUOUS` status |
| Unresolved refs carried, not dropped | yes, as warnings | yes, `UnresolvedRef` in the digest |
| Domain coupling | BPMN/DMN throughout | none; the caller supplies the resolver |

And Plato now has what `promotion.py` has no equivalent of at all:

- **Version pins.** `promotion.py` closes over *names*. Nothing in it records which version of a
  process or agent a package contained, so re-running an export after the source instance changed
  produces a different package under the same identity, silently.
- **A closure digest.** There is no content-addressable identity for a promoted assistant, so there
  is no way to ask "is what is deployed what we approved".
- **Resolve-then-freeze validation.** Validation in `promotion.py` is per-step and interleaved with
  deployment (below), so a package can be half-applied before a later step rejects it.

So on the release primitive itself, retirement is not a question of catching up.

## What Plato cannot do

### 1. Parse BPMN and DMN

`bpmn_references`, `bpmn_process_names`, `dmn_decision_ids`, `extract_prompt_process_names`,
`normalize_process_refs`. This is the content-derived half of the walk: a process's `callActivity`
and `decisionRef` name things no declared list mentions.

`closure.py`'s `Resolver.expand` docstring names exactly this case as its reason for existing, but
**no BPMN resolver has been written**. The seam is there and empty. This is real, contained work:
one `Resolver` implementation, no changes to `closure.py`.

There is also a live quirk worth carrying over rather than rediscovering: Builder Studio's create
path stores a process *display name* in `process_id` and leaves `definition_key` empty, so seeds
must be matched by key first and name second. That is not a defensive nicety, it is load-bearing.

### 2. Talk to four services

`upload_agent_bundles` (kernel), `deploy_processes` (Flowable), `resolve_or_create_collections`
(Knowledge Hub), `resolve_or_create_roles` (its own database). Credentialed outbound integrations.

These do not go away when Plato owns releases. Something still has to apply a release to an estate.
**Recommendation: they stay in a service, and Plato is that service** once D1 lands as shape 3.
They are exactly what the plan means by "belongs in the service, not the library".

### 3. Ordered, resumable application with per-step blocking checks

The caller applies dependencies first and creates the assistant row last, checking after each step
and refusing on a blocking failure (`blocking_kernel_skips`, `blocking_process_failures`). A partial
failure leaves dependencies created and no assistant, which is resumable by re-running.

The final create catches `IntegrityError` and converts a lost race on the unique name to a 409
rather than a raw database error, with a comment noting the up-front existence check is a fast path
and not a guarantee. Plato's `If-Match` concurrency (Phase 2 task 5) is the equivalent for pointer
moves, but **nothing in Plato yet sequences a multi-service application**, and the resumability
property is a design choice that has to be made deliberately rather than inherited.

---

## The disagreement that actually blocks retirement

`resolve_or_create_roles` and `resolve_or_create_collections` resolve by exact name and **create
what does not exist**.

`closure.py` refuses this explicitly:

> It never resolves by name-with-create-if-absent. That is the upsert-by-name workaround that
> exists in name-keyed systems because no immutable release primitive was available; this is that
> primitive, and adopting the workaround here would defeat it.

Both positions are defensible in their own context. `promotion.py` is moving an assistant into an
instance that may genuinely lack a role or a collection, and refusing would make promotion
unusable. Plato is trying to make a release mean one thing forever, and name-based creation makes
that impossible: the same package applied twice against different instance states produces two
different deployments under one identity.

**This is the retirement blocker.** Not the parsing, not the integrations. A migration that keeps
`resolve_or_create` semantics gets Plato's storage without Plato's guarantee.

**Proposed resolution**, consistent with Phase 2 task 7's "create-or-verify-digest":

- Creating a *missing* dependency stays allowed, because the alternative is unusable.
- Creating it under a name that already exists with **different content** becomes a refusal, not a
  reuse. Today `resolve_or_create_collections` reuses a collection already owned by another
  assistant and reports a warning; under a release primitive that is a digest mismatch.
- The release records the digest of everything it created, so the second application of the same
  release is a verify rather than a create.

That keeps promotion usable and makes a release mean something. It is also a **behaviour change for
existing callers**, which is why it needs stating here rather than discovering during migration.

---

## Retirement path

Sequenced so each step is independently useful and none is blocked on D1:

1. **Write the BPMN/DMN `Resolver`** against `closure.py`. Gate-invariant. Carries the
   key-then-name lookup rule. Contained, testable against the existing repository export shape.
2. **Settle create-or-verify** as a written policy before any code moves. This is a contract
   change, and it is the thing that decides whether retirement is worth doing.
3. **Plato grows the application path** (D1 as shape 3): the four integrations, applied in the
   existing order, with the resumability property made explicit rather than emergent.
4. **`promotion.py` becomes a caller** of Plato's release API, keeping its own HTTP surface, so
   Builder Studio does not change on the same day the storage does. `api.py` is its only caller,
   so this step has exactly one blast radius.
5. **Retire the closure and packaging halves** of `promotion.py` once Plato's release is the source
   of identity. The service integrations do not retire; they move.

## What stays regardless

- The four outbound integrations. They move, they do not disappear.
- The ordering and resumability discipline. Proven in production; inherit it rather than re-derive.
- The key-then-name lookup for Builder Studio-authored processes, until Studio stops writing
  display names into `process_id`.

## Not verified

- Whether the Flowable deploy is idempotent on redeploy of an identical definition. This decides
  how much of step 3 is genuinely new work, and it is the first thing to check before committing to
  a date.
