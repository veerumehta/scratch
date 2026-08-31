# Where versioned agent configuration lives in v2

Author: Virendra Mehta · 2026-08-24 · for the Builder Studio owner

**Two decisions, one recommendation, and a small ask of Studio.** About ten minutes to read.
Nothing is blocked on agreeing with the reasoning; it is blocked on the decision being written down
either way.

Written against `japes` `plato`@`d273f47`. Companion notes:
`note_PLANE_B_CLOSURE_FROM_PROMOTION.md`, a full read of the existing promotion path, and
`Plato_Service_Architecture_and_Build_Plan.md`.

---

## The recommendation

**D1: Plato is the system of record for versioned agent configuration.**

**D2: Studio writes to Plato's API, and Plato remains the only writer of that store.**

The rest of this memo is why, what it costs Studio, and what we are asking for.

---

## What changed since this question was last framed

The v2 extension model is now settled: **a domain adds capability as skills and prompts, not as
code.** No per-domain Python, no sandbox client. Studio is building against that.

It has a consequence that reframes D1 entirely. If capability is code, then configuration is
metadata about a deployment and versioning it is hygiene. If capability *is* configuration, then a
configuration version **is** the release. "Which version is running" stops being a bookkeeping
question and becomes the only question, because there is no separate artifact to fall back on.

Today that question has no answer anywhere in the estate. `promotion.py` (1117 lines, in
`assistant`) exports a dependency closure and replays it into another instance. That is a transfer
mechanism, and a good one. It is not a release primitive: there is no immutable version, no
rollback that reproduces a prior state, and no way to answer "what exactly ran last Tuesday".

---

## D1: the two live shapes

| | **Studio owns it** | **Plato owns it (recommended)** |
|---|---|---|
| System of record | Builder Studio's store | Plato's `plato_control` schema |
| Who resolves a release | Studio, at publish | Plato, at publish **and at load** |
| Runtime reads config from | Studio's API, per turn | Its own database |
| Multi-tenancy | Studio's to solve | Built and tested |
| `promotion.py` | Stays, and grows | Retired against Plato |

**The argument that decides it, in one paragraph.** A release whose stored digest does not match
its recomputed closure has to fail *at load*, before a turn runs, because once a turn is running
the wrong configuration is already answering a customer. The thing that loads a release is Plato.
Under the other shape that check is either a remote call on the hot path or it does not happen, and
in practice it does not happen. Every other row in that table is a matter of effort. This one is a
matter of whether the guarantee exists at all.

**The honest case for Studio owning it**, which we are not dismissing. Studio is where
configuration is authored, and the shortest path from author to release is one system. A service
boundary in the middle adds a sync problem that does not exist today. If versioning is already on
Studio's roadmap, our shape is a second implementation of it, and that is a real cost we would be
asking you to absorb.

**Why we still recommend against it.** Authoring and serving have different failure modes.
Authoring optimises for iteration speed, and it should. Serving has to refuse to start when
something does not verify. Those two instincts fight inside one system, and they run on different
clocks: a release has to stay loadable and reproducible long after the tool that authored it has
moved on.

---

## What already exists on the Plato side

Not a proposal. Built, tested and on the branch above:

- **Tenant-scoped durable stores**, with `tenant_id` in a key rather than in a filterable column,
  and a test asserting no table escapes it.
- **An assistant-addressed runtime.** Two assistants with different manifests, packs and personas
  served from one instance by writing configuration only, with no deploy and no code change. That
  is Phase 1's acceptance test and it passes.
- **Sealed registries.** Skills and prompts layer per tenant and then freeze, so what an instance
  can reach is fixed before it serves. This is what makes "what is running" answerable at all, and
  it follows directly from the skills-and-prompts model.
- **The closure primitive**, built in the SDK rather than in Plato, deliberately: transitive
  fixed-point resolution, references reachable through artifact content rather than only through
  declared fields, digests over resolved identity, and unresolvable references carried rather than
  dropped. Whoever wins D1 consumes it. It was built during this decision precisely so the answer
  could not invalidate it.
- OIDC verification, an audit trail, a deployable with role selection, and CI.

---

## D2: one writer, and which one

Live only if D1 lands on Plato. **If both Studio and Plato can write configuration, neither is the
system of record**, and the release digest stops meaning "this is what will run".

| | **Studio writes to Plato's API (recommended)** | **Studio keeps its store, Plato reads** |
|---|---|---|
| System of record | Plato, unambiguously | Ambiguous by construction |
| Studio-side work | Repoint writes | None initially |
| Failure mode | Studio blocked when Plato is down | Divergence nobody notices until a release is wrong |
| Migration | One backfill | Continuous reconciliation, indefinitely |

**What the second column costs, concretely**, taken from the closure note rather than from
principle. Studio's create path stores a process *display name* where a key belongs, and
`{{TOOL_X}}` aliases are resolved at export time rather than stored resolved. Under one writer
those are fixed once, at the write boundary. Under two they become permanent inputs Plato
compensates for indefinitely, and the compensation is a guess whenever a display name matches more
than one definition.

**If Studio cannot repoint immediately**, the interim we would accept is Plato reading Studio's
store **read-only**, with a stated end date. What we would not accept is a second write path, since
that is the state the whole exercise exists to avoid.

### There is already a second writer, and it is not Studio

A caller audit run on 2026-08-24 across every sibling checkout found something the framing above
misses. **`eval-service` calls kernel's `update_agent`** (`app/evals/invokers.py`), so its
optimization loop mutates agent configuration directly. Under any shape where configuration is
versioned, an out-of-band write is the exact failure D2 is meant to prevent: a release digest that
no longer describes what will run, changed by a system that never published a version.

This is not an argument against the recommendation. It is a third party nobody has counted, and it
means D2 is not solely a Studio question. Whatever we agree, eval-service's optimization writes
need one of three answers:

1. It proposes rather than writes, and a promotion through Plato applies the change. Preferred:
   an optimizer suggesting a better prompt is exactly the case an approval lifecycle exists for,
   and `fabric.guidance` already has one.
2. It writes through Plato's API like any other publisher, and its changes become versioned
   releases with an actor recorded.
3. It keeps writing directly, and versioned configuration is understood not to cover the agents it
   touches. Honest, and worth saying out loud rather than discovering later.

**The rest of the audit is good news**, and worth stating because it changes the cost of the
recommendation. Nothing in the estate reads kernel's `agent` table directly: every remaining caller
goes through the HTTP client, so the retirement is not gated on kernel's database. Eight files
across three repos, and only three of them read agent *definitions* at all. The rest read
invocations and traces, which is a different plane and a different phase.

---

## What we are asking Studio for

1. **A decision on D1 and D2 in writing.** Either answer unblocks us; silence does not.
2. **If D2 lands on Studio writing to Plato:** repointing Studio's configuration writes at Plato's
   API. We supply the API surface, the contracts, and the migration for existing rows.
3. **Answers to the three schema questions below**, which we need before designing tables rather
   than after.

What Studio gets back: rollback that reproduces a prior state rather than approximating it, an
audit trail of who promoted what, tenant isolation you do not have to build, and the ability to say
what is running in production without reading a database by hand.

---

## Three questions the schema needs either way

Decisions, not details. We have opinions; we do not think we should settle these alone.

1. **Does a release carry BPMN bytes, or a Flowable deployment id?** Carrying bytes makes a release
   self-contained and rollback total. Referencing makes Flowable the owner of process content and
   reopens what rollback means for the process half. `promotion.py` bundles the bytes today.
2. **Who resolves `{{TOOL_X}}`-style aliases**, the publisher as today, or the runtime at bind
   time? Publisher-side keeps a release reproducible. Runtime-side keeps it portable across
   environments with different tool ids. These are in genuine tension.
3. **Is `assistant`'s `assistant_process` table in scope for D2?** It holds the references whose
   identity is inconsistent, and nothing in the current framing names it either way.

---

## What happens on each answer

- **Plato owns it, Studio writes to its API.** Phase 2 starts as scoped.
- **Plato owns it, Studio keeps its store.** Phase 2 starts, plus a reconciliation surface and a
  resolution rule for existing rows. Larger, and the acceptance test "rollback reproduces the same
  closure digest" becomes conditional on Studio not having written in the meantime.
- **Studio owns it.** Plato's Phase 2 does not happen. Phases 3 to 5 still do: the runtime,
  generated skill routes, trace of record and reference data are all independent of who owns
  config. The closure primitive is already in the SDK, so Studio consumes it rather than building
  its own.

**Nothing is wasted on any answer.** That was deliberate, and it is also why we can afford to wait
for a considered answer rather than a fast one.
