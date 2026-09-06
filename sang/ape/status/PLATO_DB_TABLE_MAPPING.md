# Plato's database: what kernel and assistant hold, and what Plato should

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: design note, 2026-09-02. Nothing here is built. The purpose is to agree the shape before
any DDL, because a table added is far harder to retract than one not yet written.

Plato is meant to serve v2 for both the kernel and assistant surfaces. That is a claim about data
before it is a claim about endpoints, so this starts from the four schemas as they exist today.

## Method, and what it is worth

Tables were enumerated by scanning `__tablename__` declarations across each repository, excluding
tests and migrations. Counts are reliable. **Column lists are not** -- they were extracted by
proximity in the source and several bled across neighbouring classes, so the per-table columns below
are indicative of *purpose* and should not be trusted for field-level design. Anything at that level
needs reading the model, and where a decision turns on it that is called out rather than guessed.

## The four schemas today

| | Tables | Character |
| --- | ---: | --- |
| kernel | 21 | execution plane: agent/plan/step/tool, four `*_invocation` tables, LLM and MCP registries, and content/RAG storage |
| assistant | 19 | organisational plane: project/team/role/membership/session, `assistant_*` bindings, conversation/message, invocation |
| jazzx_sdk | 17 | already defined as models, hosted by whoever runs the SDK |
| **plato** | **3 migrated** | `agent_session`, `assistant_manifest_record` (both SDK), `model_overlay` (Plato's own) |

The other 14 SDK models are declared but absent from Plato's migration chain. So the work is less
"design 40 tables" than "decide which of the 40 Plato owns, and bring the SDK's own chain up to
match".

## Bucket A -- already covered by a japes table

Adopting these means pointing the surface at the SDK store, not writing DDL.

| kernel / assistant | japes table | Note |
| --- | --- | --- |
| `assistant.conversation` | `agent_session` + `conversation_message` + `conversation_overlay` | The SDK splits lifecycle from content; assistant keeps both on one row. See the conversation question below. |
| `assistant.message` | `conversation_message` | |
| `assistant.assistant` | `assistant_manifest_record` | The manifest already carries `allowed_skills`, archetype, autonomy. |
| `assistant.invocation` | `turn_run` | Both are "one request being served"; `turn_run` adds heartbeat and stop_requested. |
| `assistant.message_trace` | `turn_run_event` | Plus the MLflow bridge for the trace half. |
| `kernel.agent` | `agent_definition` | |
| `kernel.feedback_config` | `japes_feedback` | |
| `kernel.llm` | `model_data.json` + `plato.model_overlay` | Deliberately *not* a table in the SDK: pricing and cards ship as data, with a durable per-deployment overlay. |

## Bucket B -- belongs to Knowledge Hub, not Plato

Five kernel tables are content storage and retrieval. Knowledge Hub owns that domain as an HTTP
service; kernel carries them because it predates that split. Rebuilding them inside Plato would
recreate the thing kernel is being deprecated for.

`collection`, `document`, `chunk`, `collection_index`, `text_search_vector`

`assistant.assistant_collection` is a binding to the same domain and follows the same rule: a
reference, not a copy.

## Bucket C -- genuinely missing, and Plato probably needs them

This is the real gap, and it is almost entirely one thing: **nothing in japes models an
organisation**. There is no project, team, role or membership anywhere in the SDK's 17 tables.

| assistant table | Why it has no japes equivalent |
| --- | --- |
| `project` | The SDK's unit of scope is `tenant_id`, which is coarser than a project. |
| `team`, `team_membership` | No group concept exists. |
| `role`, `project_membership`, `user_membership` | Authorisation in japes is `CallerIdentity` plus whatever the downstream service enforces; there is no local grant table. |
| `user_session` | Distinct from `agent_session`: a person's login, not a conversation. |

`kernel.notepad` and `kernel.artifact` are also unmatched -- durable working content produced during
a run. Whether those are Plato's or Knowledge Hub's is an open question, not an omission.

## Bucket D -- do not port

| Tables | Why |
| --- | --- |
| `kernel.plan`, `kernel.step`, `kernel.tool`, `kernel.response` | Kernel's agent is a stored plan/step graph. japes' equivalent is a declared pipeline plus skills, which is a different execution model, not a missing table. Porting the tables would import the model. |
| `kernel.agent_invocation`, `llm_invocation`, `tool_invocation`, `mcp_tool_invocation`, `hook_execution` | Five OLTP tables recording what happened. japes records the same through `turn_run`/`turn_run_event`, `cost_record` and the MLflow bridge. See the observability question. |
| `kernel.mcp_server_config`, `kernel.mcp_tool` | japes' MCP seam is code, and the registry question is deliberately open (`jazzx_sdk/mcp/registry_tools.py` is unmounted pending real usage). Tables would settle a question nobody has asked yet. |
| `assistant.assistant_agent`, `_process`, `_role`, `_tool` | Join tables between an assistant and what it may use. The manifest already carries this as declared configuration; a join table makes it mutable state instead. |
| `assistant.invocation_project_summary` | A read model. If it is needed, it is a view or a projection, not a base table. |
| `assistant.resource` | Purpose unclear from the schema alone; needs a reading before it is classified. |

Rough totals: **8 covered, 6 to Knowledge Hub, 9 genuinely missing, 17 not ported.**

## Two constraints the design already has

**Tenancy is settled, and it is stricter than either source.** `plato/tenancy.py` requires
`tenant_id` in the primary key or a unique constraint -- not merely as a column -- because "a plain
column is a filter a query can forget; a key is a constraint the database applies whether or not the
query remembered". **Neither kernel nor assistant tables carry `tenant_id` at all**; assistant scopes
by `project_id` and `creator_user_id`. So nothing transplants unchanged. Every ported table is
re-keyed, and `verify_tables` will say so mechanically.

**The SDK's migration chain is the delivery mechanism.** Plato's `0001_initial` covers 2 of the 17
SDK tables. Whatever is adopted arrives by extending that chain, which also means each addition gets
the tenancy check for free.

## Open questions -- these change the answer, and I cannot settle them from the schemas

**1. Does Plato own the organisation, or consume it?** Bucket C is nine tables of identity and
grants. If another v2 service owns projects, teams and roles, Plato needs foreign keys and a client,
not tables -- and Bucket C mostly disappears. If Plato owns it, this is the largest piece of new
schema and deserves its own design pass, because membership and grant tables are where authorisation
bugs live.

**2. Do kernel's five execution tables become rows, or traces?** japes already records runs and cost
and bridges to MLflow. Reproducing `agent_invocation`/`llm_invocation`/`tool_invocation`/
`mcp_tool_invocation` as tables risks rebuilding observability as OLTP -- five tables written on
every turn, queried rarely. The counter-argument is that a durable, queryable invocation history is
a product feature and MLflow is not a system of record. Worth deciding explicitly rather than by
default.

**3. Which conversation shape wins?** assistant's `conversation` row carries `messages`,
`current_message`, `message_content`, `pagination` and `payload_patch` -- denormalised UI state.
japes splits lifecycle (`agent_session`), content (`conversation_message`) and execution
(`turn_run`). The SDK's shape is the better one, but adopting it means deciding where `payload_patch`
and `pagination` go, and they look like presentation concerns rather than persistence.

**4. Are `notepad` and `artifact` Plato's or Knowledge Hub's?** Both are durable content produced by
a run. The KH boundary argument in Bucket B applies if they are documents; it does not if they are
run scratch space.

## Suggested next step

Answer question 1 first. It determines whether the remaining work is nine new tables plus a schema
design pass, or a handful of reference columns and a client. Nothing else on this page is worth
detailing until that is settled.
