# Plato assistant chat: a production-shaped interactive assistant built only on the SDK

Plan, opus-xrepo, 2026-10-13. Status: approved in principle by the user; written for sonnet-runtime. Not yet
scheduled against the queue (corrections, registry, solution view).

## 1. Goal and the constraint

Goal: a chat page in Plato on which an assistant pack behaves like the production assistant
(orchestrator plus specialists, grounded tools, cited answers, conversations that persist), so packs
are built and tested where they are authored.

**The constraint (the user, 2026-10-13):** no reliance on any other service, including eval-service,
the Assistant service, Kernel and Knowledge Hub. Everything runs on SDK functionality that Plato
hosts:

| Need | Not this | This (SDK, hosted by Plato) |
|---|---|---|
| Conversations and turns | Knowledge Hub or Assistant stores | `runs.ChatTurnStore` and sessions on `fabric.db` |
| Approved feedback in the prompt | eval-service static feedback, Kernel's `use_feedback` | the SDK feedback store (Plato `/feedback`) through `evaluation.feedback.render_feedback_block`, gated by the assistant pack's own flag |
| Guidance | `EvalServiceGuidanceStore` | `InProcessGuidanceStore` or `RagGuidanceStore`, or none |
| Documents, guidelines, findings | Knowledge Hub, LOS | Plato's documents API, guideline store, case runs, packs |
| Traces | external tracing backends | `CanonicalTrace`, `GET /traces/{id}` |

The page is a test and authoring surface, not a second production assistant. Every engine change
lands in the SDK, so the production assistant gets it when it updates its japes pin.

## 2. What exists (do not rebuild)

| Capability | Where |
|---|---|
| Orchestrator with skills as tools, typed skill tools, skill invoke | `agents/interactive/`, Plato `/assistants/{id}/skills/...` |
| Chat lifecycle: gate, ground, compose (present, cite, humanize, leak check), persist | `pipelines/chat/` |
| Coordinator: barge-in, interrupt, single flight, deadlines, lanes | `runs.ChatCoordinator`, `ChatTurnStore` |
| Status events with lanes, titles, persona suffix, display-name rewriting, typed stage errors | `72957e4d` |
| Declarative grounding with pluggable kinds (`documents`, `entities`, `canonical`, `rag`, `docs`; entry point `jazzx_sdk.ground_kinds`) | `pipelines/grounding.py` |
| Guidance injection with spans recording why it was or was not applied | `InteractiveAgent._apply_guidance` |
| Feedback records, review, `render_feedback_block` (no caller yet) | `evaluation/feedback/`, Plato `/feedback` |
| Assistant routes: chat, stream (SSE), sessions, progress, chain, record, stop, skills, OpenAPI | `plato/api/assistants.py` |
| Traces | `GET /traces/{id}` |
| Guideline sets (Acra set `acra-dscr` G1 is published locally) | `plato/api/guidelines.py` |

## 3. Phases

### A1. Conversation routes and the chat page

- **Conversation routes** on the assistant router, over `ChatTurnStore` and sessions:
  - list conversations by assistant and subject, the subject being a case or loan id;
  - read a conversation, with paged history;
  - rename (`set_title`) and archive;
  - recover a turn stuck pending past its deadline (marked interrupted, the same rule as
    reconcile).
  - Ownership by caller identity and tenant; foreign, archived and missing conversations are
    indistinguishable.
- **Page `/assistants/ui`**, list-first in the style of the other Plato pages (plain HTML and JS
  with `shared.js`; no framework):
  - an assistant picker, a subject field, and the conversation list;
  - the transcript, with markdown;
  - the live turn: streamed text, status lanes and tool activity as they arrive, and a stop
    button;
  - the final answer's citations as links;
  - an inspector drawer showing the turn's trace (stages, tools, model calls, cost);
  - thumbs up or down and a note on a turn, writing a feedback record tied to the turn.
- **Verify:**
  - chat with `policy-authoring` and `clinical-intake` end to end with a scripted model;
  - barge-in marks the earlier turn interrupted;
  - a reload rebuilds the conversation from history.

### A2. Grounding from Plato's own data, and the case assistant pack

- **Four ground kinds**, registered like the built-ins. Each yields a manifest for the prompt
  plus tools confined to its source, with capped reads and search, and content treated as data:

| Kind | Source | Tools |
|---|---|---|
| `case_run` | a case run's Decision, rule outcomes, conditions, derived values | list findings, read finding, list conditions |
| `case_documents` | the case's documents (`documents_for`) | list, read pages, search |
| `guidelines` | a guideline set version, by page | list, read, search; citable by file and page |
| `pack_policy` | the pack's jobs and rules | list jobs, read job, read rule |

- **An assistant pack for the Acra case,** replacing the one-skill sample. Configuration only:
  - **orchestrator persona:** routing and answer rules;
  - **specialists:** loan or case (the `case_run` and `case_documents` kinds), policy
    (`guidelines` and `pack_policy`) and email drafting (`case_run` conditions);
  - each specialist gets only its tools.
- **Static feedback:** approved, entity-scoped feedback from the SDK store, through
  `render_feedback_block`, added to the orchestrator only when the pack enables it. A failure
  leaves the prompt unchanged.
- **Verify:**
  - a question about a case cites a finding and a document page;
  - a policy question cites a guideline page;
  - a tool cannot read outside its source;
  - feedback is applied only when enabled, and the span says why.

### A3. Polish

- Citations open the cited document page, or the guideline page, in a viewer. This is shared with
  the solution view plan's code and job links.
- Conversation export: transcript plus trace, as JSON.
- Email drafting from outstanding borrower conditions, once typed conditions exist (the parity
  item). Until then it drafts from free-text conditions.

### A4. Interaction features adopted from a sibling copilot (scan: `note_juno_scan_20261013.md`)

All in-process and service-free. Ranked:

1. **Questions as tools, as cards, remembered.**
   - Tools `ask_choice(options)` and `ask_text` end the turn on an open question. The page
     renders a card. The answer is checked against the offered options, stored by key in the
     session, and never asked twice.
   - The card is stored on the message that asked, so it survives a reload. A newer question
     supersedes a stale one, and the card is drawn from normalized arguments.
   - japes already declares `InteractiveResponse.needs_decision` / `Decision`
     (`agents/interactive/response.py`), but nothing sets it. This wires it end to end.
   - Size: medium.
2. **Prose-question repair.** A task turn that ends with a question in prose is told to ask it as a
   card instead. Small.
3. **Propose, then approve, before expensive work.**
   - A generic SDK approval tool: the assistant proposes an action with its estimated cost, and the
     approval is fingerprinted, so a later edit against a changed proposal is refused as outdated.
   - The first user is the authoring assistant: `start_extraction` today runs as soon as it is
     called. Under this, it proposes the documents, pack, representations and estimated cost, and
     runs only after approval.
   - Built on item 1. Medium.
4. **Page context.** The page sends its state (route, selected pack, draft, proposal, form
   values); a tool exposes it, so the user need not name what is on screen. Small.
5. **Navigation.** A Plato tool emits a one-way `navigate` event ("open the DSCR pack's review
   queue"), matching names against Plato's own lists. Plato-only. Small.
6. **Browser-answered tools.** The tool emits an event and waits, with a timeout, for the page to
   answer (e.g. unsaved edits in a rule editor). It needs a resolve route and a status-event
   kind. Small; after 4, only if a use appears.
7. **Eval authoring skills** for the test half of the page, bound to the SDK's datasets, custom
   scorers and experiments (not a service). Prompts are rewritten, not copied.
   - generate test cases from an assistant spec, previewed, saved only on request;
   - turn a plain-language check into a scorer draft;
   - diagnose failing cases, citing them, with a revised prompt.
   - Medium. These also serve the corrections plan's diagnosis.

Order: items 1-4 with A1 or straight after it, since they make the authoring assistant usable;
5 with A2; 6 and 7 with A3.

### A5. Speak the production chat UI's event vocabulary

- **The production chat UI.** It is the `ChatModule` in the sibling front-end repo
  (`src/modules/ChatModule`, about 65 files, React, MUI and Redux, plus private
  `@JazzX-LLC/jaxi-*` packages). It renders a turn from the platform vocabulary:
  - `status`;
  - `reasoning`;
  - `llm_chunk`;
  - `tool_call_request` and `tool_call_result`;
  - `agent_invocation`, with `agent_invocation_id`;
  - `citations`;
  - `email_draft`;
  - `final_result`;
  - `done`.

  Its views include agent invocation steps, a thought process, citation and email-draft actions,
  a feedback dialog, and interrupted, error and execution-time notes.
- **The SDK's stream** today is `InteractiveStreamEvent` (`delta`, `done`, `response`) plus the
  status events with lanes.
- **Do not embed the React module in Plato.** It needs the private packages, a Redux store and the
  host app's context. Plato's pages stay plain HTML and JS.
- **Do add a platform codec to the SDK.** One serializer maps the SDK's stream events to the
  platform vocabulary (`?format=platform` on the stream routes):
  - deltas become `llm_chunk`;
  - skill or specialist calls become `agent_invocation`, with their tool calls as
    `tool_call_request` and `tool_call_result`;
  - status events become `status`;
  - the reasoning stream becomes `reasoning`;
  - compose's citations become `citations`;
  - a drafted email from the email specialist becomes `email_draft`;
  - the reply becomes `final_result`, then `done`.

  The vocabulary's names and payload shapes are pack-free constants in one module, checked against
  a recorded fixture of the UI's expected frames.
- **Payoff:**
  - the production chat UI can point at any SDK-backed assistant, Plato's included, unchanged;
  - the production assistant can retire its own frame mapping when it updates its japes pin;
  - Plato's own page renders the same vocabulary, so both UIs mean the same thing by each frame.
- **Plato's page borrows the module's views,** written in plain JS:
  - an agent-invocation accordion, with the thought process folded;
  - citations and email-draft actions;
  - copy;
  - a feedback dialog, whose fields map onto SDK feedback records;
  - interrupted and error notes;
  - execution time.
- **Size:** the codec is small to medium; the views fold into A1 and A3.
- **Verify:**
  - a scripted turn with two specialist calls, a citation and an email draft produces the frame
    sequence the module expects (fixture);
  - the default format is unchanged.

### A6. Engineering UI, built like the copilot host (the user, 2026-10-13)

The user: this is an engineering UI, not for external consumption. Build something similar; embed
nothing. The copilot's chat itself is a private micro-frontend package not in our checkouts. Its host
app (`builder-studio-ui/src/juno/`, about 70 files) shows the integration patterns worth copying:

1. **A docked assistant on every page,** not only a separate page.
   - `/assistants/ui` stays as the full view.
   - Each Plato page (packs, coverage, solution view, extraction, runs) gets a dockable chat panel
     from `shared.js`.
   - The page registers its context in a small registry: the pack, draft, version, selected job,
     rule, proposal or case. The panel sends it with each turn (A4 item 4).
   - Host: `contextRegistry.ts`, `usePublishJunoContext.ts`.
2. **Intents from the page to the assistant.** An "ask about this" action on a job, rule, proposal
   or coverage row opens the panel with a prefilled question and that object as context. Host:
   `JUNO_HOST_INTENT_EVENT`.
3. **Artifacts with review, then apply.**
   - When the assistant produces something appliable, such as a rule edit, a job rewrite, a test
     case set or a scorer, it arrives as a card showing a diff against the current draft, with
     Apply and Discard.
   - Apply goes through the existing draft write path, or creates proposals. A partial or
     conflicting apply opens a warning dialog rather than a toast.
   - Host: `xmlReviewStore.ts`, `xmlReviewMerger.ts`, `xmlDiffLineMapper.ts`,
     `JunoApplyWarningDialog.tsx`, `EvalTestcasesGeneratedCard.tsx`, `EvalScorerGeneratedCard.tsx`.
   - SDK side: the assistant returns typed artifacts (kind, target, content, base digest). The
     page renders them by kind; the base digest makes a stale apply a conflict.
4. **Message actions the page answers.** `can_apply` and `apply` actions are checked by the page
   before the button is enabled. This is A4 item 6 (browser-answered tools) in its first concrete
   use. Host: `actionType: 'process.can_apply_xml'` / `'process.apply_xml'`.
5. **Edit lock while applying.** The page locks the edited object while an apply runs, so the user
   and the assistant do not both write it. Host: `processValidationLock.ts`.
6. **Widgets by message type.** A message can carry widgets the page renders after its body: a job
   card, a rule's code, a coverage row, a dependency graph. In markdown, code blocks get actions
   (copy, open in the draft viewer, apply). Host: `uiExtensions.tsx`, `getMessageWidgets`,
   `codeBlockWrapper`.

Order: item 1 with A1 (the panel is the same component as the page). Items 2-6 with A2 and A3, as
the authoring assistant's tools produce appliable artifacts. Size: medium overall; most of it is
page JS plus a typed-artifact field on the response.

### A7. The assistant in the rest of the UI (the user, 2026-10-13)

The assistant shows today in the dock, its own page, spend and feedback. A7 adds it everywhere else
work is listed:

1. **Runs list.** Assistant turns are listed beside case runs on the runs page:
   - a type filter: case run, turn;
   - status, cost, assistant and subject;
   - a link to the conversation;
   - stuck turns flagged, with the recover action.
2. **One trace viewer.** The assistant page's inspector becomes a shared viewer. Every trace id
   on any page links to it: feedback rows, runs and logs.
3. **Origin on work the assistant starts.** Extraction runs, proposals and corrections started by a
   tool call record the conversation and turn they came from (`origin: {conversation_id,
   turn_id, assistant_id}`).
   - The extraction, review and runs pages show "from conversation ..." with a link.
   - The turn's tool activity links to the run or proposals it made.
   - Provenance, not a gate: work started outside chat has no origin.
4. **Logs by conversation.** A conversation or turn filter on the logs page.

Order: after A3 and A6. Size: small to medium; item 3 needs one optional field on the run and
proposal records (no migration where records are JSON).

## 4. Not brought over

- The Socket.IO transport (SSE is enough for the page).
- Two conversation stores.
- External identity proxies.
- LOS data, until an entity source exists in the SDK.

## 5. Posture

Tolerant first:

- a missing grounding source leaves that specialist without tools and says so in the status
  lane;
- an assistant without the feedback flag runs without feedback;
- an unavailable trace leaves the inspector empty.

## 6. Order

A1, then A2, then A3, after the solution view's V4 routes, because citation links and the viewer
are shared. Size: A1 one pass, A2 one pass, A3 small.

## 7. Decisions

- SDK only, no other services (the user, 2026-10-13).
- The page also hosts the policy-authoring assistant with its tools (extraction runs, proposals,
  wording checks), so authoring and testing share one chat surface (the user, 2026-10-13). A1
  verifies it against `policy-authoring`, including a tool that starts an extraction and the
  progress showing in the status lane.
