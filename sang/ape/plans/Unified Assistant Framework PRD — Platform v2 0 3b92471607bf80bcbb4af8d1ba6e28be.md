# Unified Assistant Framework PRD — Platform v2.0

## Objective

**The problem today**

- Assistants on the JazzX platform are built in multiple ways. The Q&A chat in the mortgage app is wired into the app, Juno runs on its own setup, and the PWB (Policy Workbench) chat is built separately again — **three assistants, each built its own way** and every new assistant needs its own code package on Azure.
- Nothing is shared — the same question can get different answers depending on which of these assistants you ask.
- No assistant gets built without core engineering.
- A domain-agnostic "build your own assistant" capability of the Jazz Platform.

**What the Unified Assistant Framework (UAF) does**

- **The product, in one line:** UAF is the single platform service on which every assistant — conversational or non-conversational — is built and run. The end outcome of building an assistant is a live, working assistant with its capabilities exposed as APIs (for Phase 1), created in minutes through configuration.
- One idea: **an assistant is a configuration, not code.** A builder fills a Manifest and deploys it.
- One shared service gives every assistant its routing, guardrails, access control, conversation handling, memory, and tracing — built once in the framework, never rebuilt per assistant.
- **Built once, but not one-size-fits-all.** Each capability comes with multiple options — multiple routing strategies, multiple guardrail profiles, memory on or off, different autonomy levels — and the manifest picks the combination each assistant needs. The same framework serves chat assistants and screen assistants alike.
- Skills are the only way an assistant does work — each skill invokes an existing agent, tool, or process.
- Because skills are shared, **learning is shared too**: feedback and traces improve a skill once, and every assistant using that skill gets better. Democratization of building assistants — and of improving them.

## What this PRD does NOT cover

- **Building agents, tools, or processes.** That stays in Builder Studio (workflows run on the Process Engine). UAF only *invokes* them through skills.
- **Domain knowledge.** The framework itself carries no domain knowledge — skills call the right agents, tools, and processes, and those carry the domain knowledge.
- **Custom frontend UI.** Whoever builds the assistant owns its screen — UAF powers the backend, and any surface can build its own UX on the assistant's APIs. What UAF will offer (later phases) is an optional **Chat Control Module**: a ready-made, embeddable chat component that any app can drop in, tailored with different themes, colors, and branding as needed. Teams that want a chat UI out of the box use the module; teams that want their own UX build on the APIs.

## Simple definitions

- **Assistant** — a digital worker for an end user (bank employee or borrower). Two types: **conversational** (chat — like Jazz Assistant or Juno) and **non-conversational** (a screen where buttons trigger work — for example, an Underwriter assistant or a Loan Officer assistant in the mortgage app; these are examples only, the framework itself is domain-agnostic).
- **End user** — the person who uses an assistant. Not a user of UAF itself.
- **Builder** — the person who creates an assistant. In Phase 1: FDEs and SEs, through Builder Studio.
- **Skill** — one unit of work an assistant can invoke. Behind every skill is an existing agent, tool, or process. The skill is just the standard way to call it.
- **Manifest** — the configuration file that fully defines an assistant. No code.
- **Skill Library** — the shared catalog of skills: certified skills and skills you add yourself. Third-party and open-source skills come in later phases.
- **UAF runtime** — the one shared service that all assistants run on.

## Success metrics for Phase 1

- **Build a conversational assistant in minutes, with zero code** (today: 8 days and 81 lines of code).
    - **That assistant works at par with the Jazz Assistant we have in place** — matching it on ≥95% of a test set of real questions.
- **Build a non-conversational assistant in minutes, with zero code, through the same manifest flow**
    - Describe the assistant, pick its skills, deploy. Every skill then becomes a ready API endpoint:
        - **Sync** — quick asks that return the answer immediately (e.g., "get the DTI").
        - **Async** — longer work that runs as a workflow behind the scenes (e.g., "fetch loan conditions"): the API confirms it started, reports status, and returns the result when done.
        - Alongside the APIs, a **docs page is auto-generated from the manifest** — every endpoint, its inputs, its outputs — always current, never hand-written.
        - **Measured by:** a frontend developer builds the screen using only these APIs and the docs page — no core engineering involved.

## Phase-1 acceptance — in simple words

Phase 1 is done when we can show these two things working on the shared runtime:

1. **One conversational assistant.** The Jazz Assistant Underwriter runs on UAF as a manifest. It answers through one chat API. Underwriters notice no difference from today.
2. **One non-conversational assistant.** An assistant defined as a manifest whose skills are available as separate APIs — enough that a frontend developer can build a screen using only those APIs and the docs page, without asking core engineering anything.

---

# Phase 1 — Goals

## Goal 1 — The Manifest: shared runtime and basic information

**Scope — what we will do**

- Build one always-running UAF service that serves every assistant. Deploying an assistant just means saving its manifest.
- The manifest starts with the assistant's **basic information**:
    - **Name** — what the assistant is called (e.g., Underwriting Assistant).
    - **Description** — a prompt describing what the assistant should do. This drives everything downstream: routing, out-of-scope handling, and skill recommendations.
    - **Persona** — how the assistant speaks and behaves (tone, formality, how it explains, how it refuses), chosen for who will use the assistant — the end user. Two options:
        - **Pick from a defined list** of platform-tested personas matched to the audience — e.g., precise and policy-toned for underwriters; warm and jargon-free for borrowers.
        - **Define a custom persona** when the list doesn't fit — validated against the guardrails before use, so nobody ships a risky or over-promising voice.
    - **Type** — conversational or non-conversational.
- The persona applies everywhere the assistant speaks in its own voice: direct answers when no skill fits, delivering skill results, and refusing out-of-scope questions.
- Everything else an assistant needs — skills, routing and LLM, out-of-scope handling, guardrails, access control, memory, feedback — is covered by the goals that follow; each adds its own settings to this same manifest.
- Check every manifest at deploy time. If it points to a skill that doesn't exist or a setting that's wrong, it fails immediately with a clear message — it never half-works silently.
- Build the manifest authoring screen in Builder Studio (simple form, plus raw view).

**Expected outcome**

- A builder creates a new assistant from scratch and it is live within minutes, with zero code written.
- **The mandatory bar to go live:** a manifest must have, at minimum — a **name**, a **description** (the prompt), a **persona**, a **type** (conversational or non-conversational), and **at least one skill attached**. Deploy fails if any of these is missing.
- **On top of the bar, every assistant gets the non-negotiables automatically:** safety-floor guardrails, access control, tracing, and feedback capture are always on — no manifest can opt out of them.
- Two assistants with the same skills can serve different audiences — same capability, different voice — just by picking a different persona.
- A bad or incomplete manifest is rejected at deploy with the exact field and reason.
- Changing an assistant (add a skill, tighten scope) is just editing the manifest and redeploying.
- Both assistant types — chat and screen-based — are described by the same manifest format.

## Goal 2 — The Skill Catalog

**What is a skill:** one unit of work an assistant can invoke. Behind every skill sits an **agent**, a **tool**, or a **process** that already exists. The skill is the standard wrapper that lets any assistant use it. Building agents, tools, and processes stays in Builder Studio — this goal builds the **catalog** that makes them discoverable and usable.

**Scope — what we will do**

- Build one shared **skill catalog**, browsable from Builder Studio.
- Every entry has below information so a builder understands it at a glance:
    - **Skill Name**
    - **The skill** — what it does (e.g., "Answers questions about a specific loan file").
    - **What's behind it** — which agent, tool, or process it invokes (e.g., "invokes the Loan Data agent, which reads live loan data from the LOS").
    - Plus the working details: inputs/outputs, who can see it, guardrail rules, version.
- Three categories of skills:
    - **Available skills** — skills already in the catalog, ready to attach.
    - **Contribute your own skills** — wrap an agent, tool, or process you've built in Builder Studio and add it to the catalog (how, in Goal 4).
    - **Third-party and open-source skills** — **later phases.** These need a **skill optimizer** so third-party capabilities can be understood by the Jazz platform.
- Show each builder only the skills their role allows. (TBD on how do we have access control at builder level)
- Seed the catalog with Jazz Assistant's skills (Talk to Loan, Talk to Policy, Talk to Documents, Compose Borrower Email, Out-of-Scope Refusal), Juno's skills, and the PWB skills.

**Expected outcome**

- A builder understands any skill without opening Builder Studio — the information tell what it does and what's behind it.
- Picking skills feels like an app store — no wiring, no code.
- Skills recommended based on skills recommender (Goal 3) should be visible at the top
- A skill built once is reused by many assistants; new versions don't break old ones.
- Nobody can attach a skill their role isn't allowed to see. (depending on what we finalize on the access control)

## Goal 3 — Skill Recommender

**Scope — what we will do**

- Build a **Skill Recommender** inside the catalog: when a builder creates an assistant, it reads the **description** (what the assistant should do) and the **persona** (who it serves and how it speaks) and recommends the top skills to attach.
- Both inputs matter: the description finds skills that match the job (a loan-conditions assistant → Talk to Loan, Fetch Loan Conditions), and the persona filters for the audience (a borrower-facing persona surfaces borrower-safe skills, not internal-analyst ones).
- Recommendations respect access control — a builder is never recommended a skill their role can't see.
- Always show a **"View all skills"** option — the builder can browse the full catalog when the recommendation isn't what they're looking for, and the recommendation is never forced: it suggests, the builder decides.
- Recommendations improve as the catalog grows — better skill one-liners mean better matches.

**Expected outcome**

- A builder writes the description, picks the persona, and sees the right skills proposed immediately — no scrolling through the whole catalog to start.
- The recommendation is a head start, never a cage — "View all skills" is always one click away.

## Goal 4 — Contributing your own skills

**Scope — what we will do**

- Let any builder (FDE/SE) add their own skill to the library. Contributing a skill means **wrapping an existing agent, tool, or process** so assistants can invoke it — filling in the skill record: what it invokes, inputs/outputs, who can see it, guardrail rules.
- If the agent or process a builder needs doesn't exist yet, they build it in Builder Studio first (outside UAF), then come back and register it as a skill.
- New skills land in the **Add your own** tier, visible to the builder's org right away.
- **Later phases:** the certification process — review checklist, reviewer queue, and promotion of contributed skills to **Certified**.

**Expected outcome**

- A builder wraps what they have already built in Builder Studio as a skill, no core engineering involved.
- The library grows on its own as builders contribute, and everyone benefits from each other's work.

## Goal 5 — Invoking Skills -> agents, tools, and processes

**Scope — what we will do**

- Build the execution layer: when an assistant invokes a skill, UAF calls the agent, tool, or process behind it and brings the result back. Once a skill is attached to an assistant, it is **live** — nothing extra to wire, deploy, or integrate.
- Examples of the three kinds of skills:
    - **Skill → agent:** "What's the DTI on this loan?" → the Talk to Loan skill → the loan agent reads the loan file and answers.
    - **Skill → tool:** "Calculate the qualifying income" → the Income Calculator skill → the calculation tool runs and returns the number.
    - **Skill → process:** "Fetch loan conditions" → the Fetch Loan Conditions skill → a workflow runs on the Process Engine and returns the conditions.
- A skill can run in two ways, and UAF supports both:
    - **Sync — ask now, answer now.** The answer comes back in the same interaction; the user waits a few seconds at most. The DTI and income examples above are sync.
    - **Async — start now, finish later.** The skill kicks off longer-running work (usually a workflow) and immediately confirms it has started; UAF reports status while it runs and delivers the result when it finishes. "Fetch loan conditions" is async: the assistant says "started," shows progress, and reports completion with the conditions.
- **A skill inherits its inputs and outputs from the agent, tool, or process it invokes.** We don't force one common IO shape — whatever the underlying thing accepts and returns is what the skill declares in its skill record, and that's what shows in the catalog and the auto-generated docs. This works the same for platform skills and user-contributed skills, whatever their IO structure.
- Return clean, structured errors when the thing behind the skill fails or times out — never a silent hang.

***To be clear on scope:** building agents, tools, and processes is NOT part of UAF — that happens in Builder Studio as it does today. Invoking any of them through a skill IS the scope of this goal.*

**Expected outcome**

- Attach a skill to an assistant and it's live: invoked from chat or called as an API, it executes and returns the result.
- All three examples run end to end — DTI (agent), income calculation (tool), loan conditions (process).
- A contributed skill with any IO structure just works — its inputs and outputs are inherited from what it wraps, not forced into a template.
- Failures show up as graceful messages and are recorded — never silence.

## Goal 6 — Picking the Routing Logic (Orchestration)

**Scope — what we will do**

- The manifest defines how the assistant identifies the right skill — and it differs by assistant type:
- **Conversational assistants — the default orchestrator.** One orchestrator, built once in the framework and shared by every conversational assistant. For each query it:
    - holds the context of **all the skills the builder has attached** to the assistant (their one-liners, inputs, outputs),
    - leverages an **LLM** to read the query against that context,
    - identifies and **invokes** the right skill.
    - The orchestration machinery is common — ***the only thing the builder picks is the LLM inside it.*** Every model call goes through the **LLM Gateway** (fallback, cost tracking, caching); agents behind other skills selected keep their own LLM choices — UAF never overrides them.
- **Custom orchestration —** a builder can bring their own:
    - build an **agent** that decides which skill to invoke, and register an intent-classifier skill that invokes that agent; or
    - build a **rule-based engine as a tool** and orchestrate on rules.
    - Either way, custom orchestration plugs in and runs exactly like invoking a skill — the framework itself doesn't change.
- **Non-conversational assistants — no routing needed.** Every skill is already an individual API; the frontend calls the right one directly. Nothing to interpret, so no intent identification sits in between.
- If a query is within the assistant's description but no skill fits, the orchestrator's LLM answers directly in the assistant's persona.
- Record every orchestration decision in the trace.

**Expected outcome**

- Every conversational assistant gets orchestration from the framework — the default works out of the box with just an LLM pick.
- Builders with special needs orchestrate their own way — an agent or a rule-based engine — plugged in like a skill, without touching the framework.
- Non-conversational assistants stay lean: APIs called directly, no unnecessary interpretation layer.
- No model call ever bypasses the Gateway, and every orchestration decision is traceable.

## Goal 7 — Handling out-of-scope questions

**Scope — what we will do**

- Every assistant gets a defined behavior for questions outside what it is described to do — configurable, not hardcoded:
    - **Default:** a polite, standard refusal — provided by the Out-of-Scope Refusal skill from the library.
    - **Builder's strategy:** the builder can set how the assistant responds — a custom message, a different tone, or a redirect (e.g., point the user to the right assistant or channel).
    - Out-of-scope handling is itself a skill — builders can pick a different refusal skill or contribute their own.
- Record every out-of-scope hit in the trace.

**Expected outcome**

- A mortgage assistant never answers "what's the weather" — it responds the way its builder chose, staying in its lane.
- Refusals are consistent and on-persona — and, being a skill, they improve like any other skill.

## Goal 8 — Guardrails

**Scope — what we will do**

- **For Phase 1, one guardrail, used everywhere:** the red-teaming gateway we already built for Jazz Assistant, plugged into the framework **as a skill**. Every assistant gets it, always on — no manifest can turn it off.
    - Block unsafe questions — sexual content, discrimination, harmful requests, prompt injection (the seven red-teamed categories).
- **Customization option:** if a customer-specific guardrail capability already exists — e.g., an agent built to capture all of that customer's guardrail concerns — it can be wrapped and attached **as a skill.**
- **Later phases: ready-made custom guardrail skills per customer.** A customer's specific needs — including **allow/deny lists** (topics to block, phrases to never use, things fine for one bank but off-limits for another) — offered as custom guardrail skills, built and attached the same way as any other skill.

**Expected outcome**

- Every assistant on the framework is protected by the proven Jazz Assistant red-teaming gateway from day one — nothing to configure, nothing to build.
- Unsafe questions get the same clean, standard refusal on every assistant.
- Every guardrail hit is logged and traceable.
- Because guardrails are skills, extending them — a customer-specific guardrail agent today, allow/deny lists and custom rules later — means attaching a skill, not changing the framework.

## Goal 9 — Assistant Role Based Access control (RBAC) [Require Discussion]

**Scope — what we will do**

- Make UAF the checkpoint, not the record-keeper: before any skill fires, UAF checks the user's role (from Keycloak, decisions via Ory Keto) and the user's data access (from the LOS). UAF stores no roles or entitlements of its own.
- **Build-time:** each skill's visibility setting controls which builders can see and use it. The more regulated a skill, the tighter its visibility — this is how governance is enforced: a builder who shouldn't use a regulated capability never even sees it listed.
- **Run-time:** three underwriters using the same assistant each see only their own loans. This should not be UAF RBAC, but user RBAC that is already part of platform.
- Pass the user's identity and access scope along with every skill invocation, so what runs downstream knows who this is for. (Checking at every downstream hop — agent → sub-agent → workflow → tool — comes as a later enhancement.)

**Expected outcome**

- Nobody ever sees data outside their access — asking about a loan outside your book gets a polite, logged refusal.
- Access control is built once in the framework, inherited by every assistant — never rebuilt per assistant again.
- Permission checks are fast enough that users never feel them.

## Goal 10 — Conversation management (conversational assistants only)

**Scope — what we will do**

Build conversation handling once, in the framework, so no team builds it again. This applies **only to conversational assistants** — a non-conversational assistant has no conversation: every API call stands alone, and the state of long-running work is already covered by async status tracking (the skills goal).

- **Multi-turn context** — follow-up questions work without repeating yourself: "and what about the income?" needs no loan restated.
- **Session handling** — start, resume, and expire sessions cleanly; a user who steps away and comes back continues where they left off (within the session).
- **Streaming responses** — answers appear as they are being generated, not after a long silent wait.
- **Automatic compaction** — long conversations get summarized behind the scenes, so answer quality and cost stay stable no matter how long the chat runs.
- Chat UIs keep owning only the look and feel — rendering, scrolling, input box.
- Reserve space in the API for future "thinking mode" events (showing step-by-step reasoning) so it can be added later without breaking anything.

**What the builder can configure (in the manifest)**

- **Session expiry** — how long an idle session stays alive before it ends.
- **Streaming** — on (default) or off, for surfaces that want complete answers only.
- **Compaction** — on by default; can be tuned or turned off for short-lived assistants.

**Expected outcome**

- Follow-ups just work: "and what about the income?" doesn't need the loan restated.
- A 40-turn session keeps working smoothly — compaction is invisible to the user.
- One conversation engine serves Jazz Assistant and Juno in Phase 2 — no team builds conversation handling again.
- The builder shapes conversation behavior with settings, never with code.

## Goal 11 — Memory

**Scope — what we will do**

- Once an assistant is built, session memory just works: the assistant remembers everything within the current conversation — what was asked, what was answered, which loan or policy is in context.
- Give the builder memory options in the manifest:
    - **Memory off** — every question stands alone; nothing is remembered.
    - **Single-session memory (default)** — the assistant remembers within the current conversation; a new session starts fresh.
    - **Multi-session memory** — the assistant remembers across sessions: come back tomorrow and continue where you left off.
    - **User-level memory (later phases, not now)** — the assistant knows the user: the loans they work on, their preferences, their role context (arrives with Memory Fabric) — and it will serve **both** assistant types, because user-based personalization matters for non-conversational assistants too (e.g., a processor's screen pre-loading their loans and preferences).
- The session options (off / single / multi) apply to conversational assistants — a non-conversational assistant's calls are standalone; its screen state lives in the frontend.
- Task memory (how agents do their work) stays with the agents — not UAF's job. And "what the user is allowed to see" is not memory at all — it's checked live at every request (the access control goal).

**Expected outcome**

- Within a conversation, the assistant never loses context — follow-ups work naturally.
- The builder controls memory by picking an option — no code.
- When user-level memory arrives, it plugs into the same options list — chat and screen assistants both get personalization.

## Goal 12 — Trace and audit

**Scope — what we will do**

- Record every interaction, on every assistant, in one standard format: what was asked → what the guardrails said → which skill was chosen and why → what ran behind it → what data was touched → what came back → what the user got.
- Same format for both assistant types, so audit, debugging, and evaluation work identically everywhere.
- Provide a basic way to look traces up for debugging and audit.
- Attach user feedback (thumbs up/down with detail) to the trace.

**Expected outcome**

- For any answer any assistant ever gave, we can show exactly what happened, step by step — enough for an auditor in regulated lending.
- Debugging and evaluation work the same way no matter which team built the assistant.
- This same trace feeds evaluation and the learning loop (Goal 12).

## Goal 13 — Feedback and learning

**Scope — what we will do**

- Give every assistant — conversational and non-conversational — a feedback mechanism out of the box:
    - **Conversational:** the end user rates an answer (thumbs up/down) and can add detail on what was wrong or missing.
    - **Non-conversational:** the same feedback APIs are available per skill result, so screens can offer their own feedback buttons.
- Store every piece of feedback in the **Feedback Manager** (the platform's existing feedback store), linked to the trace of the exact interaction it came from — feedback always carries its full context.
- **Approving feedback is not UAF's job.** Review and approval happen in the Feedback Manager, outside this framework.
- **Use approved feedback as learning:** an assistant built on UAF takes the approved feedback as added context — the next time a similar question comes, it answers with that learning applied. This is not automated self-learning; only human-approved feedback flows back into the assistant.
- Make learning part of building the assistant: feedback capture is on by default, and the manifest controls whether the assistant uses approved learning.

**Expected outcome**

- Every assistant ships with feedback capture from day one — no team builds their own thumbs-up/down again and also the form against. thumps up/down responses
- Feedback is never an orphan: each item links to the exact trace, so a reviewer sees precisely what happened before approving.
- Once feedback is approved, the assistant gets better without a redeploy — approved learning is picked up as context automatically.
- Because skills are shared, approved learning on a skill improves every assistant that uses it — the democratized learning loop from the objective.

## Goal 14 — The assistant's APIs and docs

**Scope — what we will do**

- **Chat API:** one standard way to send a message, stream the reply, and manage sessions — same for every conversational assistant. (Design reference - OpenAI's Responses API, and why Assistant API are getting depricated)
- **Action APIs:** every skill an assistant has becomes a callable API endpoint. This is what a non-conversational assistant is to a frontend developer: a set of ready APIs to build screens on.
- **Auto-generated docs:** Builder Studio shows a page per assistant listing its APIs, what each does, and its inputs/outputs — generated straight from the manifest and skill records, so it's always up to date.
- The APIs are the Phase-1 product outcome.

**Expected outcome**

- A frontend developer opens the assistant's docs page and builds a screen against its APIs without talking to core engineering.
- Adding a skill to a manifest automatically adds its API and its docs entry.
- This is the "end outcome" of building an assistant: a live, documented set of APIs.

## Goal 15 — Prove it with real migrations

**Scope — what we will do**

- **Conversational proof:** move the Jazz Assistant Underwriter onto UAF as a manifest. Run the golden test set (real underwriter questions) against old and new; SMEs compare. Keep the old version warm; have a one-click way back.
- **Non-conversational proof:** build one screen-based assistant as a manifest (proposal: a processor screen with "fetch loan conditions" and "request documents" — swappable), with its frontend built purely on the generated APIs and docs.

**Expected outcome**

- Underwriters get the same quality answers as before — ≥95% match on the test set, no visible regression in the first two weeks.
- Rollback is tested and documented, not theoretical.
- Both assistant types are live on the shared runtime — the Phase-1 acceptance bar is met.

---

## Out of scope for this PRD

- **Building agents, tools, or processes.** Creating these stays in Builder Studio, as it does today — workflows run on the Process Engine. UAF's job is only to *invoke* them, through skills. If a capability doesn't exist yet, it gets built in Builder Studio first and then registered as a skill.
- **Domain knowledge inside the framework.** The framework core stays domain-neutral — no mortgage rule, policy, or calculation is ever coded into UAF itself. This does *not* limit the framework to generic work: **skills call the right agents, tools, and processes, and those carry the domain knowledge.** "Talk to Loan" is mortgage-specific; "Compose Email" is generic — both plug into the framework the same way. This is exactly how the framework delivers deep domain-specific capability while staying clean and reusable across mortgage, commercial lending, AML, and whatever comes next.
- **Chat Control Module** — an embeddable, ready-made chat UI component (message list, input, streaming, feedback buttons) that any surface can drop in instead of building chat UX from scratch — tailorable with themes, colors, and branding per customer. Custom frontends on the APIs remain fully supported; the module is an option, not a requirement. (Its theming connects to the brand and tenant customization work in Phase 3.)

## Later Phases Plan

Everything we discussed but deliberately kept out of Phase 1 lives here. Nothing is dropped — only sequenced. Phase numbers show the intended order; exact timing is set release by release.

**Phase 2 — Migrate everything and open the SDK**

- Migrate the remaining assistants: Loan Officer, Loan Processor, Borrower; Juno as a manifest; SME and Policy Workbenches. Retire the legacy runtimes and the old per-assistant Azure packages.
- **Skill certification** — the review process for contributed skills: checklist, reviewer queue, and promotion to the Certified tier.
- **Classifier-based routing** — a fast intent classifier that routes clear queries without an LLM call; more routing strategies over time.
- **User-level memory via Memory Fabric** — the assistant remembers the user across sessions: loans they work on, preferences, role context. (Phase 1 ships session memory only.)
- **Cross-session (multi-session) continuity** — resume yesterday's conversation where you left off.
- **AI authoring helper for Builder** ("an assistant to create an assistant") — the builder describes the assistant in plain English; the helper helps write the right prompt, drafts the manifest, suggests and exposes the right skills based on the assistant's description, and polishes the persona wording. (Phase 2–3.)
- Skills expansion: remaining Juno-native skills (create agent, create tool, deploy assistant) and workbench skills.

**Phase 3 — New domains and customer self-service** *(pulled forward — commercial lending and other domains are on this year's roadmap)*

- **Next domains** — Commercial Lending, CRE, AML assistants using the same manifest pattern; domain skills added to the library.
- **Business users build their own assistants** — self-service authoring for customer business users, not just FDEs/SEs.
- **Brand and tenant customization** — colors, logos, block lists per customer.
- **Language and policy variability** — multi-language support (e.g., Spanish) and state-level policy variation handled through domain packs, not framework forks.
- **Assistant package export** — generate a standalone, deployable bundle of an assistant for customers who need isolated or sidecar deployments (e.g., a bank embedding the assistant into its own LOS). The shared runtime stays the default; the package becomes an *option*, produced from the same manifest.
- **Smart LLM routing** — the Gateway recommends the model per query based on context (LLM Gateway v2), and UAF simply benefits.

**Continuous enhancements — parallel workstreams** *(run alongside Phases 2–3; not gated on any phase)*

*Observe and harden:*

- **Observability dashboard** — per-assistant view of latency, cost, errors, guardrail hits, autonomy escalations, and user feedback. No custom monitoring per assistant.
- **Full permission cascade** — permission checks at every downstream hop (agent → sub-agent → workflow → tool), all validated against the original user's scope. (Phase 1 checks the UAF-owned hops and passes the user context down.)
- **Full autonomy enforcement** — the complete Governor + Verifier machinery: gate decisions above the assistant's autonomy ceiling and verify outputs. (Phase 1 ships declare + basic gating.)
- **A/B deployments** — run v2 of an assistant for a slice of users while v1 keeps serving the rest; one-click rollback if metrics degrade.
- **Custom-coded guardrails** — written via the SDK, beyond the declarative rule types of Phase 1.
- **Thinking-mode streaming** — show the assistant's step-by-step reasoning while it works, toggleable per assistant. (Phase 1 reserves the API event types so this adds without breaking changes.)
- Skill versioning and rollback maturity in the registry.

*Multi-user and simulation:*

- **Multi-user conversations** — two or more people in the same assistant conversation (e.g., a Processor and an Underwriter on the same loan file at the same time).
- **Simulation with golden datasets** — test a manifest against a set of test conversations before deploying; compare versions; catch regressions before users see them.
- **Bring-your-own framework via JAPES** — customers run assistants built on LangChain, Semantic Kernel, or the Claude SDK alongside native ones.
- **Third-party skills** — skills brought in by external teams, with versioning and rollback in the registry.

*Always:*

- New skills added to the library every phase — both to power new assistants and to broaden what existing ones can do.
- **Skill learning loop, deepened** — Phase 1 already captures feedback and feeds approved learning back as context; over time this deepens: richer learning signals from traces, learning applied at the skill level so one improvement reaches every assistant, and connection to the Continuous Learning Layer on the platform roadmap.