# Knowledge Hub global config on `KnowledgeHubClient`

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Scope note, 2026-11-18. Decides nothing beyond the shape below; the build follows in 2.7.5. Evidence: the generated client at japes' pin (client-api 96c42edb, `api/global_config/`), `knowledge_hub` (route code, `knowledge_hub_openapi_schema.yaml`, commit 71edfe58 on branch `feat/BSD-5668-workspace-global-config`), jazzx-assistant `src/jazzx_assistant/clients/app_config.py`, juno `app/feedback_labeling/kh_config.py`.

## What exists

Five routes under `/api/v1/global-config/`, all bound in the generated client: `list_configs` (GET, `name` exact match, `skip`, `limit`), `create_config` (POST, 201), `get_config` (GET `{config_id}`), `update_config` (PATCH `{config_id}`), `delete_config` (DELETE `{config_id}`, 204). A config is `name` (unique), `value` (a JSON object), `ttl_seconds` (optional cache hint), and on a read `id`, `created_at`, `updated_at`. Errors: 404 "Config not found" (get, patch, delete), 409 on a name that is taken (create, patch), 422 on a bad body; a denial is 401 or 403.

`KnowledgeHubClient` has none of them. Two consumers reach the generated binding through `_raw_client`: jazzx-assistant (`list_configs.asyncio(client=raw, name=...)`, which reads `APP_CONFIG` once per session and treats "no row", "more than one row" and any exception as `ConfigUnavailable`) and juno (`list_configs.asyncio_detailed`). Builder Studio (BSD-5668) is about to write them.

## Shape (the client's own conventions)

Results are plain dicts (`to_dict()` of the generated model, so a field the pin does not know, such as `origin`, comes through in `additional_properties`), as `create_collection` and `get_collection` return.

| Method | Returns | Not found, refused, denied, unavailable |
|---|---|---|
| `list_global_configs(name=None, *, skip=0, limit=100)` | `list[dict]` | No match: `[]`. Denied (401/403): `KnowledgeHubAccessError`, always (the response hook). Outage: `[]` on the plain client, `KnowledgeHubUnavailableError` on `strict()`, as `list_collections`. |
| `get_global_config(config_id)` | `dict` or `None` | Missing (404): `None`. Denied and outage as above. |
| `create_global_config(name, value, *, ttl_seconds=None)` | `dict` (the created config) | A status other than 201 (a taken name is 409, a bad body 422): `KnowledgeHubRequestError` with the status and an excerpt of the body. Raises rather than returning a default: a write that did not happen must not read as one that did. |
| `update_global_config(config_id, *, name=None, value=None, ttl_seconds=None)` | `dict` or `None` | Missing (404): `None`. 409 and 422: `KnowledgeHubRequestError`. Only the fields given are sent. |
| `delete_global_config(config_id)` | `bool` | Deleted (204): `True`; missing (404): `False`. Any other refusal: `KnowledgeHubRequestError`. |

The Strict wrapper delegates every coroutine method generically, so `client.strict().list_global_configs(...)` raises on an outage with no change to it. `kh_protocol.py` gains the five names (it takes `*args, **kwargs`); `MockKnowledgeHubClient` gets the same five over an in-memory dict with the same refusals (a taken name raises `KnowledgeHubRequestError` 409, a missing id answers `None` or `False`).

## jazzx-assistant's swap

`fetch_grounding_targets` today reaches the binding and wraps every failure. After this it becomes one call, `rows = await kh_client.strict().list_global_configs(name=config_name)`, and the `_raw_client` lookup, the `list_configs` import and the "no longer exposes `_raw_client`" branch go. It should use `strict()`: on the plain client an outage reads as `[]` and the session would say "no config named", where today it says "could not read". `_matching_documents` already handles dicts. juno's call becomes the same line (it uses `asyncio_detailed` only to read the status, which the method now maps).

## Workspaces (KH 71edfe58): what it adds and what the client does

The commit makes global config copy-on-write inside a workspace: a workspace caller (header `x-workspace-id`) reads Host's configs plus its own changes, its first edit copies a Host config, its delete writes a tombstone, and Host changes only through base-scope calls (what Builder Studio makes at merge). Responses gain `origin` (`base`, `workspace_copy`, `workspace`, `workspace_deleted`) and the list takes `include_deleted`.

- It is on a feature branch of `knowledge_hub`, not on its main, and neither the generated client at japes' pin nor the main schema has `origin` or `include_deleted`. Nothing can be tested against it from here.
- **No `workspace_id` parameter.** The client already forwards headers on every request through `request_headers_provider` (the hook that carries `x-user-id` and the rest), and the workspace is a property of the caller's session, not of one call; a workspace caller sets `x-workspace-id` there, a base-scope caller (Builder Studio's merge) does not. A per-call parameter would be speculative API for a route scope that has not shipped. When the branch merges and the client is regenerated, `origin` arrives in the dicts for free; `include_deleted` is one optional argument to add then.

## Size

About 110 lines in the client, 25 in the mock, 6 in the protocol, and a test file of about 150 lines (the request sent for each call over a transport, each refusal, the strict view, the mock held to the same cases). Well under a few hundred lines; no new module, no generated-code change.
