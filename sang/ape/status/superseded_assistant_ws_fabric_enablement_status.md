# Status: Assistant WS v2 — deprecate direct-KH in favor of fabric

Author: Virendra Mehta · Updated 2026-08-01
Repo: japes · Plan: docs/plans/plan_assistant_ws_fabric_enablement.md

**W3 done and tested. W1/W2/W4 not started — not because they're hard, but because researching
them surfaced enough accumulated open design questions (the plan's own §6, plus two more found
during research) that building them now would mean deciding several of those questions
unilaterally rather than at the "design owner" checkpoint the plan itself calls for.**

## W3 — per-turn security-context context manager (done)

`jazzx_sdk/handlers.py` gains `security_context(value)`, beside `set_security_context`/
`clear_security_context`. **Built as a class, not `@contextmanager`** — checked directly that a
plain `@contextmanager`-decorated function does not support `async with` at all (confirmed by
running it: `TypeError: '_GeneratorContextManager' object does not support the asynchronous
context manager protocol`), and the plan's own usage sketch (§3, and `plan_luna_adoption.md`'s
`handle_turn`) explicitly writes `async with security_context(turn_token):`. The class implements
both `__enter__`/`__exit__` and `__aenter__`/`__aexit__` over the same sync set/clear (there's
nothing to actually await), so it works as either `with` or `async with`.

Verified directly (not just by reading): sets on enter, clears on exit; clears even on exception,
both sync and async; concurrent tasks under `asyncio.gather` never see each other's value (ran
three concurrent workers with staggered sleeps, each asserted its own token mid-flight). Exported
from `jazzx_sdk` top-level alongside `set_security_context`/`get_security_context`/
`clear_security_context`. 5 new tests in `tests/test_identity_propagation.py` (the existing
security-context test file), all passing alongside the 7 already there.

## W1/W2 — not started: what research surfaced beyond the plan's own §6

Researched `ConversationStore`, `SqlConversationStore`, `fabric.entities`, `_build_conversation_store`,
and `FabricConfig` directly before writing anything, per this session's own "verify before build"
discipline. Found real gaps the plan doesn't name:

- **`entities.ensure()` requires both `collection_id` and `ontology_id` as mandatory kwargs** — the
  plan's W1 sketch names neither. Checked for an existing convention to default to: **none exists**
  — `fabric.entities.ensure()` has *zero* real call sites anywhere in japes today (only tested, never
  actually used by application code), and the one existing `ontology_id` convention in the codebase
  (`CANONICAL_ONTOLOGY_ID`) belongs to the *different* `fabric.canonical` store — reusing it for
  `fabric.entities` writes would conflate two separate governed surfaces the plan chose `entities`
  specifically to avoid conflating with `canonical`. This is a real, un-anchored design decision,
  not a lookup gap.
- **`_build_conversation_store` is a `@staticmethod(config, db=None)` with no access to
  `self.entities` at all** — adding an `"entities"` branch is a real signature change (passing the
  entities store in, or converting to an instance method), with a knock-on need to handle
  `self.entities is None` (STRICT/CACHED fabric mode with no client) explicitly, matching the
  existing `fabric.pack` property's `KnowledgeFabricError` pattern rather than crashing on
  `None.ensure(...)`.
- **The plan's own "v1-fragile edge" (same-name-different-content collision) is not reproducible
  against the Mock/LOCAL backend** — verified via the existing `test_entities_ensure_new_content_
  same_name_creates` test, which proves the Mock does *not* enforce name-uniqueness (both writes
  succeed as distinct entities). The 409 behavior the plan describes is real-KH-only; any W1 test
  for that specific edge needs a purpose-built stub simulating a 409, not the existing Mock.
- **The audit-attribution claim (`created_by_user_id` populated server-side from `X-User-Id`) is
  unverified from japes' side** — it rests on a comment in `CallerIdentity`'s own docstring, not a
  cross-repo-confirmed fact (KH's own source isn't in this session's working directories). The
  plan's §6 question 2 assumes this is settled; it isn't, independently of anything else.
- **§6's own open question 6 (PII redaction before persistence)** is the one this status file
  weighs most: `fabric.entities` is a broadly-queryable, frontend-and-audit-readable surface, and
  loan/financial chat turns plausibly carry account numbers/SSNs in free text. Building
  `EntitiesConversationStore.append()` without redaction and shipping it risks normalizing an
  unreviewed privacy posture; building *with* speculative redaction risks guessing at a scope
  ("what's redactable") the plan explicitly says needs its own build decision. Neither direction is
  mine to pick.

## Net

W1's real gaps (ontology_id/collection_id, the None-entities error path, the untestable-against-Mock
edge case) plus §6's six open questions (especially PII redaction) add up to more unresolved design
surface than "read the ABC and implement it." Recommend the plan owner resolve §6 plus the
ontology_id/collection_id question explicitly before W1/W2 are attempted — at that point they
become a much more mechanical build. W4 (the adoption doc) depends on W1-W3 all existing and
stable, so it's deferred with them.
