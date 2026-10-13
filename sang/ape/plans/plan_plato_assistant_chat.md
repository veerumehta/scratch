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
