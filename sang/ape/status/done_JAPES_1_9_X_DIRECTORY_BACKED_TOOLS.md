# Done: JAPES 1.9.x — Directory-Backed Tool Factory

Author: Virendra Mehta · Updated 2026-08-01
Repo: japes · Plan: docs/plans/plan_JAPES_1_9_X_DIRECTORY_BACKED_TOOLS.md

**Built as specified, both open questions resolved per the plan's own stated leaning, one real bug
found and fixed in the plan's own acceptance-test code before it ever shipped.**

## What landed

- `jazzx_sdk/tools/dir_tools.py`: `build_directory_tools(sources, *, read_limit_kb=10) ->
  DirectoryToolSet` — exactly the design in the plan (source-keyed `list_documents`/
  `read_document`/`search_documents`, all `@function_tool`-wrapped, path-traversal-safe, grep-
  backed search), copied faithfully rather than reinvented since the plan's own code was already
  correct at the implementation level.
- **Open question 1 resolved yes** (per the plan's own "leaning yes"): `DirectoryToolSet.as_dict()`
  added, returning exactly the `{"list_documents": ..., "read_document": ..., "search_documents":
  ...}` shape `InteractiveAgent(tools={...})` wants.
- **Open question 2 resolved no** (per the plan's own "leaning no"): no pure-Python/Windows
  fallback for `search_documents` — grep-only, as the plan itself preferred for now.
- Exported from `jazzx_sdk.tools`: `DirectoryToolSet`, `build_directory_tools`.

## A real bug found in the plan's own acceptance tests, not shipped

The plan's own "Acceptance tests" section calls the built tools directly —
`t.list_documents("src", "*")` — as if they were plain functions. **They are not.**
`@function_tool` (the OpenAI Agents SDK decorator) returns a `FunctionTool` dataclass object,
confirmed directly: calling one raises `TypeError: 'FunctionTool' object is not callable`. The only
real invocation path is `await tool.on_invoke_tool(ToolContext(...), json_args_string)`.

Checked whether this invalidates the design itself (not just the tests) — it doesn't: this is
exactly how `InteractiveAgent`/the OpenAI Agents `Runner` invoke any `FunctionTool` internally, so
the tools work correctly in their real, intended usage. Only the plan's own illustrative test code
was wrong (never actually run against the real SDK before being written into the plan). Fixed by
writing `tests/test_dir_tools.py`'s tests through the real `on_invoke_tool(ctx, json_args)` path
(a small `_call(tool, **kwargs)` helper building a minimal `ToolContext`), verified directly against
a real `@function_tool`-wrapped function before writing the full suite, to be certain the corrected
invocation convention itself was right before relying on it 13 times.

13 tests (up from the plan's own 6): the plan's 6 acceptance scenarios (list, read a line range,
search, unknown source, path traversal rejected, missing directory raises) rewritten against the
real invocation path, plus 7 more: a path that exists but isn't a directory raises, read on a
missing file, the read-size-limit message, `max_count`/case-insensitivity in search,
`file_pattern` actually limiting which files are searched, `as_dict()`'s exact shape, and
`sources` reflecting the real source names.

## A second real bug found: the plan's own code breaks the SDK's tier boundary

The plan's design has `from agents import function_tool` at module level in `dir_tools.py`
(literally what the plan text shows). Building it exactly as specified and running the full suite
caught a real regression: `tests/test_import_boundary.py`'s 4 "server-free" tests (`import
jazzx_sdk`, `jazzx_sdk.evaluation`, `jazzx_sdk.contracts`, `jazzx_sdk.runtime`) started failing —
each now transitively pulled in `uvicorn` via `jazzx_sdk.tools.__init__` → `dir_tools` → `agents`.
Verified directly (not assumed) that this is real: confirmed `import jazzx_sdk` on the clean,
pre-change tree imports neither `agents` nor `uvicorn` at all, and confirmed in isolation that
`from agents import function_tool` (or even just `Agent`/`Runner`) always pulls `uvicorn` in a
fresh subprocess — the OpenAI Agents SDK carries that dependency itself.

This is exactly the tiered-import discipline the SDK already has elsewhere (sibling `tools/*.py`
files — `documents.py`, `policy.py` — only ever mention `from agents import function_tool` inside
*docstring examples* of what a caller should do, never as a real top-level import, precisely to
keep `jazzx_sdk.tools` safe to import from tier-1/tier-2 consumers that never touch the Agents SDK).
Fixed by moving the import inside `build_directory_tools()`'s own body (lazy, resolved only when a
caller actually builds a tool set) — the plan's own design intent (pre-wrapped `FunctionTool`
objects) is unchanged, only *when* the SDK import happens moved to match the established
convention. Re-verified: `test_import_boundary.py` back to 6/6, `test_dir_tools.py` still 13/13.

Full japes suite: 2051 passed, 3 skipped, no failures (confirmed after the lazy-import fix; the
same run before the fix showed 2047 passed + the 4 import-boundary failures above, which is what
caught this).

## Deliberately not done (stated, not silently dropped)

- No changes to existing `jazzx_sdk/tools/documents.py` utilities, MACER's tools, or any
  KH-backed/write tool — all explicitly out of scope per the plan's own "What this plan does NOT
  change" section.
