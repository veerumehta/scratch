# Memory, and what earns a place in the SDK

Virendra Mehta, 2026-07-28. Working note for Sourav and me.

What I went through for this: PR #54 and the memory plane doc, juno's actual mem0 code
(`app/core/memory.py` and `app/copilot/memory_tools.py`), the jazzx-assistant enablement plan, what
AML and lending need from durable memory in a regulated setting, and the Hermes Agent docs.

## The short version

I don't think we disagree about memory. I think we're using one word for eight things, and that's
why the scope conversation keeps going in circles. Any cut I propose looks like I'm deleting
something somebody needs, because with a word this broad, it always is.

Worth keeping from PR #54: the access context, the trust fence, candidate-is-never-active, the
capability manifest. Those are hard to retrofit and I'd rather have them early. What I want to
change is the hardcoded governance posture, the procedural memory type, and shipping M3-M8 as
contract rather than as a design doc.

## How we decide what goes into japes

Writing these out because I think most of our disagreement is here rather than in the memory
design itself.

**Named consumer first.** `SqlConversationStore` exists because juno had already run
`copilot_session_items` in prod and we generalized behind it. My own memory fabric note has sat
untouched for months and it's not because it was wrong, it's because it described machinery
instead of a failure. I couldn't name the turn that goes wrong without it. Still can't.

**Two clients only count if they need the same thing.** My own rule has been to design when a
need shows up once and build when a second instance appears, and I nearly fell for it here. Juno
and the assistant both
"need memory," but juno needs a preferences bucket with semantic search and the assistant needs
conversation persistence plus grounding. Different rows in the table below. Two specific needs can
justify a general abstraction that serves neither cleanly.

**Absorb behind proven patterns, don't design ahead of them.** This one is about direction, not
just reuse. Design the shape first and we're taking on migration risk we can't see, because the
consumer hasn't had to fit their call sites to it yet.

**Contracts yes, platforms no.** Contracts are cheap to hold and expensive to retrofit, so be
generous. Ledgers, workers, approval services, admin UIs belong to whoever owns the deployment.
Publishing their contract commits us to building them. The design says this itself about M3 onward
and I'd draw the line exactly there.

Also worth saying: every new `fabric.*` attribute is a surface we support indefinitely.
`fabric.memory` with an ephemeral default in local and test mode means every pack gets a memory
surface whether it wants one or not.

**Policy belongs in config, not in invariants.** AML needs approval gates on anything that becomes
active truth. A copilot that only remembers your preferences after a human signs off is useless.
Hardcode either posture and the other client can't adopt, which kills the adoption goal that
started this.

## The eight things we're calling memory

<table header-row="true">
<tr><td>Row</td><td>Thing</td><td>Where it lives today</td><td>Who needs it</td></tr>
<tr><td>1</td><td>Run scratch</td><td>run context, ConductorState</td><td>exists, no gap</td></tr>
<tr><td>2</td><td>Conversation continuity</td><td>fabric.conversation</td><td>assistant, exists</td></tr>
<tr><td>3</td><td>Lossless session archive + search</td><td>nowhere</td><td>nobody asked</td></tr>
<tr><td>4</td><td>User preferences bucket</td><td>juno's mem0</td><td>juno</td></tr>
<tr><td>5</td><td>Distilled grounding facts</td><td>nowhere, memory fabric note</td><td>LUNA, AML, lending</td></tr>
<tr><td>6</td><td>Procedural knowledge</td><td>fabric.guidance</td><td>exists</td></tr>
<tr><td>7</td><td>Canonical durable record</td><td>fabric.entities, canonical</td><td>exists</td></tr>
<tr><td>8</td><td>Learned improvement loop</td><td>feedback spine, partial</td><td>later</td></tr>
</table>

Juno wants row 4. The assistant wants 2 and 5. AML and lending want 5 with row 7's governance.
Nobody's asked for 3, though it's cheap and might be the best value on the list.

Ownership, type and retrieval are all storage axes. None of them separates row 4 from row 5, which
is exactly where our two clients diverge and where the governance fight is.

The Status section of the design actually gets here on its own: "these are not the complete
placement model, lifetime and prompt-serving behavior and storage state are separate decisions."
Right. I just want to fix the v0 contract rather than defer it, otherwise we're shipping the model
we've already called incomplete.

## What juno actually uses

Went through the code so we're arguing from the same numbers. Two files, 520 lines, two call sites
(`copilot/agent.py`, `skills/tool_defs/run_skill.py`). Two mem0 methods:

- `memory.add([{role, content}], user_id=..., metadata={memory_type, timestamp})`
- `memory.search(query, filters={"user_id": ...}, top_k, threshold, rerank=True)`

That's it. No `get_all`, `update`, `delete`, `history`, `agent_id`, `run_id`. One scope key with two
values in practice, the user's UUID and the literal `"system"`. The four `memory_type` values go
into metadata and never get used as a filter. pgvector on juno's own Postgres.

So: 2 of 6 ownership scopes, 1 of 5 retrieval modes, 0 of 4 types used in retrieval.

The interesting bit isn't that it's small. It's that `save_memory` is an LLM-invoked tool that
fires a background task and writes active searchable memory with no approval, including to the
shared `"system"` scope. Right behavior for a copilot. Also violates invariants 3 and 8 as written.
So moving juno onto the plane as specced is a behavior change, not a port. Better to decide that
now than find it mid-migration.

## Hermes

Good call. Went through the docs and I think it argues for the smaller version.

Three separate tiers: a bounded core of two markdown files (2,200 and 1,375 chars, ~1,300 tokens
total, frozen snapshot at session start to keep the prefix cache), a lossless session archive in
SQLite with FTS5, and eight optional external providers that run alongside built-in memory rather
than replacing it.

The three bits I'd take:

Governance is a boolean. `memory.write_approval`, default false, and when true writes stage for
review via `/memory pending`. That's the config-not-invariant point shipped as one line of YAML.
Juno sets false, AML sets true, both adopt.

Procedures are a separate surface. Hermes has `skills.write_approval` separate from
`memory.write_approval` because procedures live in SKILL.md, not the memory store. They landed
independently on the split the memory fabric note argued for. Enough for me to drop the procedural
memory type and leave it with `fabric.guidance`.

Formation is a background review. Runs after a turn, replays the conversation, optionally on a
cheaper model with a digest instead of the full transcript. That's our M4, as a config block.

Two things to steal outright: the hard char cap with no auto-compaction (overflow returns an error
listing current entries and the agent consolidates in the same turn), which is basically our
`CoreMemoryBlock` proposal already; and write-time scanning for injection and exfiltration, since
entries land in the system prompt. We fence on read but I didn't find write-time scanning, and for
a shared `"system"` scope that's a real hole.

Where it doesn't help: single user, self hosted, one home directory. No tenants, no principals, no
bitemporal model. `MemoryAccessContext`, exact-grant enforcement and per-scope fan-out are ours to
solve and they're the best original content in the PR. Valid time vs knowledge time is a real AML
requirement Hermes has never had to hit.

We should cite it either way. The design already converges with it on the bounded core and the
provider lifecycle, and it's easier to argue against a shared reference than to rediscover things.

## What I'd like to do

1. Cite Hermes, move capture and authority to per-binding policy, keep the strict regulated posture
   as a named preset instead of the floor.
2. Drop the procedural memory type.
3. mem0 adapter as M1, not M5. Right now the consumer that motivated the whole thing gets served
   after four milestones of infrastructure it never asked for. Hermes has an MIT mem0 provider we
   can read for the shape.
4. M3-M8 into its own design doc so the PR is reviewable as a contract.
5. Decide who gets `fabric.memory`. The memory fabric note claimed it for row 5, the PR takes it
   for the plane.

## Things I don't know

- Does the assistant actually want agent-written durable memory, or just rows 2 and 5? I'm going
  off the enablement plan, not its code. If it's 2 and 5 we have one client for the plane and our
  own rule says design now, build on the second instance.
- Do we want row 3? Hermes gets a lot out of it cheaply and we have nothing.
- For AML and lending, is agent-formed memory admissible at all, or does everything durable need
  a human? If it's the latter the agentic slice is nearly empty there and most of M4-M8 collapses.
  That's a requirements answer, not a design failure, but we should say it.
- Which runtime emits the authoritative committed-turn and skill-result events? Listed as open in
  the design and it blocks the ledger schema.
