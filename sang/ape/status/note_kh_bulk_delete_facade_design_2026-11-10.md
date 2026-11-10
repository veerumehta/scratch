# Design note: a bulk-delete facade on `KnowledgeHubClient`, and what QA needs from the SDK (sonnet-runtime, 2026-11-10)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Design only; nothing built, nothing committed to the SDK. "Read" means I opened it; "not found" is said where I could not find it. Sources: JazzXQAAutomation PR #768 (read with `gh pr view` and `gh pr diff`; head `test/use-kh-client-bulk-delete`, base `develop`, 88 additions, experimental), japes PR #110 (`feat/use-kh-client-pr78`, base `plato`, open), the local clones of `client-api` and `JazzXQAAutomation`, and the v2.7.1 tree.

## 0. What the PR shows

- QA's bulk-delete tests were rewritten to call the SDK client, and they go round the facade: `KnowledgeHubClient(...).generated_client` (a property only PR #110 adds) and `knowledge_hub_client.api.reasoning.bulk_delete_entities.asyncio_detailed` with `BulkEntityDeleteRequest(collection_id, entity_ids | UNSET, delete_all, dry_run)`, then `parsed.to_dict()` or, when `parsed` is `None`, `json.loads(response.content)`.
- The fallback is the whole story of the 202: the generated `_parse_response` handles only 200 and 422, so on `delete_all` (a 202 with a task id) `parsed` is `None` and the body has to be read by hand. This is true at our pin and at the bot revision (below).
- The PR moves only the success-path tests (200 by ids, repeat delete, PARTIAL_SUCCESS, dry run, 202 for `delete_all`); the 403/RBAC cases still use the raw REST client. Through the SDK client a 401 or 403 is raised by the response hook as `KnowledgeHubAccessError(status_code, url)`, so an RBAC test would assert `pytest.raises(KnowledgeHubAccessError)` and read `.status_code`.
- Install: `japes @ git+https://github.com/JazzX-LLC/japes.git@3a291b2e...` in `requirements.txt` (a 2.6.9-era commit, not a release), with a `CLASSIC_PAT` secret fed to git through `GIT_CONFIG_*` in ten workflows.

The four cases (the spec): by ids returns 200 `SUCCESS` with `deleted_ids`, and an already-deleted id is not in `failed`; a missing id gives 200 `PARTIAL_SUCCESS` with a `failed` entry; `dry_run` gives 200 with `dry_run: true` and `matched_count`, deleting nothing; `delete_all` gives 202 with `task_id` and a `Location` header holding the task status URL.

## 1. The facade

**Two methods, one result type.** Deleting everything is a different act from deleting a list; one boolean flag between them is how a collection gets emptied by a typo.

```python
async def bulk_delete_entities(self, collection_id: str, entity_ids: Sequence[str], *, dry_run: bool = False) -> BulkDeleteResult
async def delete_all_entities(self, collection_id: str, *, dry_run: bool = False) -> BulkDeleteResult
```

- `entity_ids` is required and non-empty: an empty list never reaches the API (the same guard `bulk_download_documents` has: "an absent filter means the whole collection"), it raises `KnowledgeHubError`. `delete_all_entities` always sends `delete_all=True` and no ids.
- Ids are validated as UUIDs before the call (a malformed one is a `KnowledgeHubError`, not a logged `False` as the older methods do).

**Result type** (a frozen dataclass in `clients/`, not the generated attrs model, so the facade does not leak the pin):

```python
@dataclass(frozen=True)
class BulkDeleteFailure: id: str; error_code: str; message: str
@dataclass(frozen=True)
class BulkDeleteResult:
    collection_id: str
    outcome: Literal["deleted", "dry_run", "accepted"]   # 200 body, 200 dry run, 202
    status: Literal["SUCCESS", "PARTIAL_SUCCESS", ""]     # the 200 body's status; empty for the other two
    requested_count: int; deleted_count: int; deleted_ids: tuple[str, ...]
    failed: tuple[BulkDeleteFailure, ...]
    matched_count: int | None; deletable_count: int | None; blocked_count: int | None   # dry run
    task_id: str | None; poll_url: str | None; location: str | None                     # 202
    execution_time_ms: int | None
```

`partial` is a property (`status == "PARTIAL_SUCCESS"`). Field names are the API's (`BulkEntityDeleteResponse`, `...DryRunResponse`, `...AcceptedResponse`, `...Failure` read at client-api `da8c607`; the first two and the failure are the same at our pin).

**202 versus 200: a typed result, never an exception.** A 202 is the documented answer to `delete_all` (the API starts a task), not an unexpected status, so a method that raises on it would make the main use of `delete_all_entities` an error path. The result says `outcome="accepted"` with `task_id`, `poll_url` and the `Location` header; a caller that wants the outcome waits on the task. Add `wait_for_task(task_id)` only when a second consumer asks (the existing `_await_task` is built for the download job: its done and failed states are the download's; reusing it for the delete task needs the delete task's status vocabulary, which I did not find documented). Anything else unexpected (a 200 whose body is none of the three shapes, a 2xx that is neither 200 nor 202) raises `KnowledgeHubError` naming the status and a body excerpt through `_body_excerpt`.

**Parsing.** The facade reads the response by status code: 200 gets the dry-run shape if `dry_run` is in the body, else the delete shape; 202 reads `task_id`, `poll_url`, `collection_id` from the JSON and the `Location` header. It does not depend on `parsed`, so it works at our current pin, which has the endpoint and request model but no 202 model (section 2).

**Errors.** 401 and 403: `KnowledgeHubAccessError` from the existing response hook (status code on the exception); the facade lets it through (`KH_PASS_THROUGH`), as every method does. 422: `KnowledgeHubError` with the validation detail (a caller mistake, never swallowed). 404 or any other non-2xx: `KnowledgeHubError` with status and excerpt. 5xx, timeout, connection: `KnowledgeHubUnavailableError` when the client was built `raise_on_unavailable=True`; otherwise it must STILL raise, because this method answers a destructive request: unlike `delete_entity` (`False` on failure) the result of a delete must never read as "nothing happened" when the call did not complete. So the new methods raise `KnowledgeHubUnavailableError` regardless of the client flag.

**Headers and scope.** The generated call takes optional `x-user-id` and `x-security-context`; the facade sends neither itself: the client's `request_headers_provider` hook forwards the caller's headers on every request (`setdefault`), as for every other method, so tenant and scope follow the inbound request. Unlike `bulk_download_documents` the API does not require `x-user-id` here, so there is no `BULK_NEEDS_USER_ID` guard.

**Retries.** The client has no retry layer (callers such as `fabric.docs` own theirs), and the facade adds none. What is safe: a by-ids delete is idempotent (the QA case: an already-deleted id is not reported failed), so a caller may retry it after a timeout or a 5xx; a dry run is always safe; a `delete_all` retried after a timeout may start a second task for the same end state (soft delete again), so the docstring says to check for an `accepted` result before repeating. No automatic retry on any of them.

**Mock parity (two places).** `MockKnowledgeHubClient` (`clients/mocks.py`, in-memory `_entities`): the same two methods with the same semantics (soft delete: an id not in the collection is a `failed` entry with an `error_code`, so the status is `PARTIAL_SUCCESS`; an id already removed is neither deleted nor failed; `dry_run` counts and removes nothing; `delete_all` returns `outcome="accepted"` with a generated task id and poll URL and removes the collection's entities when the mock "runs" it; the same empty-list and UUID guards). `kh_protocol.py` (the shared protocol both clients satisfy) gets the signatures. The HTTP mock app (`server/mock_knowledge_hub_app.py`, which has entities, collections and the v2 bulk download but no bulk delete): a `POST /api/v1/reasoning/entities/bulk-delete` route with the same three bodies and the 202 plus `Location`, so a consumer pointed at the mock app over HTTP sees the same contract. A contract test runs one case table against the real facade (over an `httpx.MockTransport` that answers as the API does) and both mocks, so they cannot drift.

## 2. Which client-api revision, and what moving the pin means

- **Our pin already has the endpoint.** `knowledge-hub-client` is pinned at `767b3d6c` (main, "Regenerate knowledge-hub-client from knowledge_hub", 2026-10-07). Read there: `api/reasoning/bulk_delete_entities.py`, `BulkEntityDeleteRequest`, `BulkEntityDeleteResponse` (`status` enum SUCCESS or PARTIAL_SUCCESS, `deleted_ids`, `failed`), `BulkEntityDeleteDryRunResponse`, `BulkEntityDeleteFailure`. It has no `BulkEntityDeleteAcceptedResponse`.
- **The bot revision** `da8c607` (2026-11-06, "Regenerate knowledge_hub client", reachable only from `origin/automation/regenerate-knowledge_hub-42150531521-1`, NOT in `main`; 181 files, 2164 additions, 34835 deletions, mostly old OpenAPI snapshot files removed) adds `BulkEntityDeleteAcceptedResponse` (`task_id`, `collection_id`, `poll_url`, `status` QUEUED) and widens the 200 parse union to include it. Even there the parser reads the 202 as an unexpected status (the OpenAPI schema declares the accepted shape under 200), so `parsed` is still `None` for a real 202. PR #110 and QA's PR pin this revision.
- **So the facade does not need a pin move.** It reads by status code and builds its own result type, which works at `767b3d6c`. Moving to `da8c607` buys only the generated accepted model, which the facade would not use. Recommendation: build the facade on the current pin; take `da8c607` (or its merged successor) later, as its own change with the usual regeneration checks, not as a prerequisite.
- **Mixed revisions across kernel-client and knowledge-hub-client.** They are separate distributions in subdirectories of one repository, each pinned by its own `rev` (kernel `1d0cc4ab`, knowledge-hub `767b3d6c` today). That is fine for resolution: they install as different packages with the same loose dependency ranges (attrs, httpx, python-dateutil), and the lock records each resolved sha. The costs: two clones of one URL (the CI comment about concurrent clones into one path is why the shard job runs poetry with one installer worker), and a consumer cannot take "client-api at one sha" as a single unit. The multipart note on the current pin (client-api `4bcf1f4`, `_MultipartBody` in the client covers uploads) says a regenerated revision can regress a wire detail the facade papers over: every move needs the facade's own wire tests (`tests/` for uploads, headers, the 202) run against the new pin before it is taken.
- **`rev` versus `branch` in pyproject and in a consumer's requirements.** A `rev` is a sha: reproducible, and the lock records it. A `branch` in `pyproject.toml` is resolved to a sha at `poetry lock` time and then fixed by the lock (so the lock is reproducible, the file is not: the next re-lock moves it). In a consumer's `requirements.txt` (`japes @ git+...@<branch>`) nothing is fixed: pip resolves it at install time, a force-push changes what CI installs between two runs, and a deleted branch (a bot branch is deleted after merge) breaks every install. QA's PR pins a japes sha, which is right; japes' own pin of the client should be a sha on `main` or a tag.
- **Ask the client-api owner for:** (1) merge the regeneration PR to `main` so the revision is reachable from a protected branch; (2) a tag on the revision japes pins (for example one per regeneration), and a rule that tags are not moved; (3) no force-push to the bot branches or `main`; (4) fix the generated parse so a 202 is parsed (declare it under 202 in the OpenAPI), which would make the facade's status-code read a fallback instead of the only path.

## 3. Expose `generated_client` publicly (PR #110) or not

**Recommendation: keep it private and cover consumer needs with facade methods, with one named exception.** `_raw_client` is whatever the pin generates: its module paths, models and parsing change with every regeneration (the 202 above is the example), so a public property turns each regeneration into a breaking change for QA, and QA's imports of `knowledge_hub_client.api...` would be a second, undeclared dependency on the pin. If PR #110 lands anyway, document the property as an unsupported escape hatch whose shape follows the pin, and say so in its docstring.

The user wants wider use of japes: that argues for a larger facade, not a wider door. What QA's knowledge-hub tests call (counted over `qa_tests/api/knowledge_hub` by path string; "in facade" is the v2.7.1 `KnowledgeHubClient`):

| Call (count of mentions) | In the facade today |
|---|---|
| `/reasoning/entities` (65) and `/entities/filter` (48), `/entities/{id}` and `/json` (27) | yes: create, read, filter, update, delete, json path |
| `/reasoning/ontologies` (69) | yes: create, read, update, delete, upload |
| `/collections`, `/collections/{id}`, `by-name` (about 95) | yes: create, get, list, delete, by name |
| `/collections/documents/{id}`, `/newdocuments`, `/documents`, `/metadata` (about 90) | yes: upload, get, list, update, delete, metadata, content |
| `/reasoning/entities/bulk-delete` | NO (this note) |
| `/reasoning/entities/summary` (6) | NO (`read_entities_summary` exists in the generated client) |
| `/collections/{id}/clone` and clone status (about 12) | NO (`clone_collection`, `get_clone_status`) |
| `/collections/{id}/scope` (9) | NO (`update_collection_scope`) |
| `/collections/.../collection_indexes` (about 15) | NO (create, list, get, update, delete index) |
| `/reasoning/indexes/async` (13) and `/indexes/tasks/{id}` (5) | NO (`sync_global_indexes_async`, `get_index_task_status`) |
| `/collections/search/{value}` (2), `/collections/chat` (3) | partly (`search_documents`, retrieval); not checked method for method |
| `/project/resources` (about 54) | not Knowledge Hub: a different service, not in this client |

The gap is six groups of generated calls, about 60 mentions. The second thing QA needs, which the facade's style does not give them: their tests assert HTTP status codes (a 400 on a bad payload, a 404 for a missing id, a 409 on a duplicate), and the older facade methods answer `False` or `None` and log. So the new methods follow the bulk-delete shape (a typed result for 2xx, `KnowledgeHubAccessError` with the status for 401 and 403, `KnowledgeHubError` carrying `status_code` and a body excerpt for other non-2xx), and the older methods are left alone. That gives QA statuses through exceptions without opening the generated client.

## 4. Symmetry: `KernelClient`

Same gap in kind, not in kind of fix. `KernelClient` has typed service namespaces (`agents`, `tools`, `llms`, `notepads`, `chat`, `config`, in `clients/kernel_admin.py`) over a private `_raw_client`, and no property exposes the generated client. QA's kernel tests (`/agents`, `/agents/tools`, `/agents/tools/test-run` 40 mentions, `/agents/invoke` 14) call endpoints some of which the namespaces cover (agents, tools list/get/create, invoke through `invoke_agent`) and some not (tool test-run, agent update and delete, tool update and delete): not checked method by method. The same rule applies: add the missing calls as namespace methods with the same status-carrying error shape, and do not publish `_raw_client`.

## 5. Size, order, where it lands

- **Bulk delete facade** (both methods, result types, error mapping, both mocks, protocol, contract test over a transport that answers as the API does, docs section): about one slice. No pin change.
- **The other five groups** (summary, clone and status, scope, collection indexes, global index sync and task status): about one slice each for the first two together and the rest in one more, i.e. about two further slices, in the QA call-count order: clone and indexes first (about 27 and 18 mentions).
- **Where**: v2.7.1 is full (guidance, gateway, audit, cards, pipelines); the bulk-delete facade is small and QA is waiting on it, so I would put it on v2.7.1 after the whole-range review's findings are closed, or at the head of 2.7.2 if the review is already running; the other groups on 2.7.2. The user decides.
- **Integration note for QA** (short, to hand over): (1) pin japes to a release tag or a squash sha on `main`, never a branch; (2) install in CI with a token that can read only what the install needs: a fine-grained personal access token (or a GitHub App installation token) with "Contents: read" on `JazzX-LLC/japes` and `JazzX-LLC/client-api` (the two private repositories the install clones), fed to git per job through `GIT_CONFIG_COUNT=1`, `GIT_CONFIG_KEY_0=url.https://x-access-token:${TOKEN}@github.com/.insteadOf`, `GIT_CONFIG_VALUE_0=https://github.com/` (the PR does this with a classic PAT, which can read every repository its owner can); (3) `pip install` of a git URL does not fetch submodules, and japes' `common` is a submodule imported lazily by some modules, so the knowledge-hub client works but anything that imports `common` fails with an import error: say which japes modules QA uses, and if more are wanted the install needs the submodule fetched; (4) call `KnowledgeHubClient` as an async context manager with `request_headers_provider` for the caller's headers, and catch `KnowledgeHubAccessError` for 401 and 403; (5) the client-api tag and the japes tag must be bumped together when the facade is extended.

## 6. Recommendation

Build the two-method facade on the current pin, typed result including the 202, raising for every failure of a destructive call, both mocks and a shared contract test; do not publish `generated_client`; extend the facade with the five other groups QA calls (clone, scope, indexes, index sync, summary) in the same status-carrying style; ask the client-api owner for the merge, a tag and no force-push; give QA the install note.

## 7. Open questions for the user

1. Two methods (`bulk_delete_entities`, `delete_all_entities`) or one with a flag? I recommend two.
2. A 202 as a typed result, not an exception: agreed? (The alternative is a method that raises `KnowledgeHubError("accepted")`, which makes the intended use of `delete_all` an error path.)
3. Should the new methods raise on a 5xx even when the client was built without `raise_on_unavailable`? I recommend yes, for destructive calls.
4. Public `generated_client`: decline PR #110's property, or accept it as a documented unsupported escape hatch?
5. Does the delete task have a status API we should wrap (`wait_for_task`), and where is its status vocabulary documented? I did not find it.
6. Which release carries it: v2.7.1 (small, QA waiting) or 2.7.2?
7. Does QA need the `common` submodule from a pip install of japes (section 5, item 3)?
