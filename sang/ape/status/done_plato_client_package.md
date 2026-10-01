# A Plato client that does not carry the SDK: `jazzx-plato-client`

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: plan, 2026-09-30. Written against japes `eacaac6d` on `v2.5.8` (SDK 2.5.8, Plato 0.1.9),
with that branch's uncommitted working tree (it adds `resume_case_run` and `case_run_outcome` to
`PlatoClient`). Ships as SDK 2.6.0 / Plato 0.2.0 / `jazzx-plato-client` 0.2.0 (§4 D3).

**Progress on `v2.6.0` (local, unpushed):** Phase 1 `a4ff0566`, Phase 2 `baacd9ac`, version bump
`304a5403`. **Phases 1–2 are built.** Note: git records `client.py` as a new file, not a rename,
because the SDK path keeps a re-export shim. Phase 3 (jaci) waits for a pushed branch to pin. Analysis that led here: jaci `docs/plans/note_JACI_SDK_USAGE_AND_CARVEOUT.md` §7.

## 1. Why

A caller that only talks to Plato — a jaci page on the Plato path, a script that publishes packs, a
future author who never runs anything in-process — has to install and import the whole SDK to get
`PlatoClient`. Importing `jazzx_sdk.clients.plato_client` loads **1,502 modules** (through
`jazzx_sdk/__init__.py`: FastAPI, Azure, `common`); `jazzx_eval_contracts` loads 221. The client
itself needs almost none of it: `plato_client.py` imports httpx, the standard library and one
helper from `_header_hooks`.

Feedback is worse. Plato's `/feedback` is reached through `evaluation.feedback_sink.FeedbackApiSink`,
which pulls in datasets → golden cases, `feedback_records` → `feedback_quality` and
`jazzx_sdk.identity`; and the two constants a caller needs alongside it (`ASSISTANT_ENTITY`,
`TURN_METADATA_KEY`) live in `jazzx_sdk.server.*`, which loads ~4,070 modules.

## 2. Decision: a separate distribution, built in this repo

Settled 2026-09-30 (jaci note §7, "Packaging"). `jazzx_plato_client/` sits beside
`jazzx_eval_contracts/` with its own `pyproject.toml`, the same layout:

```
jazzx_plato_client/
  pyproject.toml            # name = "jazzx-plato-client"; deps: httpx, pyyaml
  README.md
  jazzx_plato_client/
    __init__.py             # PlatoClient, PlatoError, the constants
    client.py               # today's plato_client.py
    packs.py                # Phase 2
```

Not a separate repo: the client restates Plato's routes, headers and stream format, and its tests
(`tests/test_plato_client.py`) round-trip every method against a real `create_plato_app`. That
check only works with both in one tree, and it is what keeps the two from drifting. Split it out
only when it gains consumers without access to this repo, a release cadence apart from Plato's, or
another owner.

Consumers pin it the way jaci already resolves `jazzx-eval-contracts` (jaci's `uv.lock` has
`git = "https://github.com/JazzX-LLC/japes.git?subdirectory=jazzx_eval_contracts&rev=plato"`):

```
"jazzx-plato-client @ git+https://github.com/JazzX-LLC/japes.git@plato#subdirectory=jazzx_plato_client"
```

`jazzx_sdk` takes it as a path dependency (`develop = true`, as `jazzx-eval-contracts`) and
`jazzx_sdk/clients/plato_client.py` becomes a re-export, so no existing import breaks.

## 3. What goes in, what stays

**In:**

| Piece | From | Notes |
|---|---|---|
| `PlatoClient`, `PlatoError`, `DEFAULT_PREFIX`, `DEFAULT_TIMEOUT_SECONDS`, `STREAM_READ_TIMEOUT` | `jazzx_sdk/clients/plato_client.py` | Moved whole (`git mv`, so history follows). |
| Header forwarding | `_header_hooks.install_request_headers_hook` | Only the bare `httpx.AsyncClient` branch (~10 lines), inlined. The SDK keeps `_header_hooks` for its generated clients. |
| `submit_feedback(body)` | new; replaces what `FeedbackApiSink.submit` does | `POST /feedback` through `_call`, so it gets the tenant, trace and idempotency headers every other call gets. Takes a mapping with `FeedbackSubmit`'s fields (`jazzx_sdk/server/feedback_api.py:119`) and returns the stored record as a dict. |
| `server_info()` | new | `GET /info`: Plato's version, role, tier, schema revision, `degraded`. See D1. |
| `ASSISTANT_ENTITY = "assistant"`, `TURN_METADATA_KEY = "turn"` | `server/eval_api.py`, `server/feedback_api.py` | Restated as `DEFAULT_PREFIX` is; a test holds each equal to the server's. |
| Pack packaging (Phase 2) | jaci `scenarios/shared/plato.py` | `pack_archive`, `archive_files`, `pack_manifest`, `publish_pack`, `PackVersionConflictError`. Any pack author needs these, not just jaci; it is why `pyyaml` is a dependency. |

**Stays in the SDK:** `jazzx_sdk.identity` (the caller passes `request_headers_provider`; jaci's
`caller_identity_headers()` already does), the `Feedback`/`FeedbackRecord` models and
`FeedbackApiSink` (unchanged for SDK callers), the eval and dataset routes' clients, the Kernel and
Knowledge Hub clients, the server tier. No typed response models: the client returns dicts, as it
does today, and a pack's generated JSON schemas are the contract for its payloads.

**Why not reuse `jazzx_eval_contracts` for feedback:** Plato's `/feedback` body is `FeedbackSubmit`
(`reaction: str`, optional `feedback_id`, `rating`, `entity`, linkage ids, `metadata`), not
`FeedbackSubmissionV1` (the eval-service wire shape) and not the SDK's `Feedback`. A dict with
`FeedbackSubmit`'s fields, checked by a round-trip test against the real route, is the smallest
thing that is right.

## 4. Decisions

- **D1 — how the client says which Plato it speaks. Decided 2026-09-30: lockstep.**
  `jazzx-plato-client` carries Plato's version (`plato/_version.py`), held equal by a test the way
  `tests/test_version_sync.py` holds the SDK's two versions; plus `server_info()` for a caller that
  wants to compare at run time. No automatic check per call: `/info` may sit behind auth on a
  strict deployment (`plato/app.py` notes a probe against it being 401'd). Not taken, kept in
  reserve: a separate integer API version in `/info` and the client, bumped only on a breaking
  route change, if lockstep proves too coarse.
- **D2 — pack packaging in the client (Phase 2). Decided 2026-09-30: yes.** Without it every author
  reimplements deterministic zipping and the 409-means-compare-contents publish flow. Part of the
  0.2.0 release.
- **D3 — version bumps. Decided 2026-09-30 by the user:** this work ships as **SDK 2.6.0, Plato
  0.2.0, `jazzx-plato-client` 0.2.0** (its first release, at Plato's version per D1). The user is
  making the SDK and Plato bumps alongside the package changes.

## 5. Phases

**Phase 1 — the package (japes).** After the uncommitted `resume_case_run` / `case_run_outcome`
work on `v2.5.8` is committed, so the move does not fight it.

1.1 Create `jazzx_plato_client/` (layout in §2); `git mv jazzx_sdk/clients/plato_client.py
    jazzx_plato_client/jazzx_plato_client/client.py`; inline the header hook.
1.2 `jazzx_sdk/clients/plato_client.py` becomes a re-export of the public names.
1.3 `pyproject.toml`: `jazzx-plato-client = { path = "jazzx_plato_client", develop = true }`; relock.
1.4 `Dockerfile`: copy `jazzx_plato_client/` into the builder and its inner package into the
    runtime stage, exactly as the comments at lines 47–99 do for `jazzx_eval_contracts` (an editable
    path dependency installs as a `.pth` to the builder path, so the runtime copy is required).
1.5 Add `submit_feedback`, `server_info` and the two constants.
1.6 Tests (all in `tests/`, since they need Plato):
    - `tests/test_plato_client.py` imports from `jazzx_plato_client`. Add round-trips for
      `submit_feedback` (a retry with the same `feedback_id` returns the same record) and
      `server_info`.
    - The prefix test grows to cover `ASSISTANT_ENTITY` and `TURN_METADATA_KEY`, and the D1
      version test.
    - A lightness test: in a subprocess, `import jazzx_plato_client`, then assert no module under
      `jazzx_sdk`, `plato`, `common` or `fastapi` was loaded. This is the property the package
      exists for.
    - The re-export shim: `jazzx_sdk.clients.plato_client.PlatoClient is jazzx_plato_client.PlatoClient`.
1.7 Docs: `jazzx_plato_client/README.md`; mention it wherever `docs/DOMAIN_PACK_QUICKSTART.md` and
    the README introduce `PlatoClient`; CHANGELOG.

*Done when* the suite passes, the lightness test passes, and a fresh venv with only
`pip install ./jazzx_plato_client` can publish a pack and run a chat turn against a local Plato.

**Phase 2 — pack packaging (japes).** Move jaci's packaging helpers into
`jazzx_plato_client/packs.py`. Their constants (`DOMAIN_MANIFEST`, `ASSISTANT_MANIFEST`, the fixed
zip timestamp) come too. Tests: deterministic bytes for an unchanged folder; an assistant folder
leaves out `pack_manifest.yaml`; republishing identical contents is `unchanged`; changed contents
under the same version raise `PackVersionConflictError`; a blocking check finding raises before
publish.

**Phase 3 — jaci adopts it (jaci, its own change).** Not part of this plan's japes work; listed so
the boundary is clear:
- pin `jazzx-plato-client` directly;
- `scenarios/shared/plato.py` imports `PlatoClient`/`PlatoError` and the packaging helpers from
  it, and deletes its own copies;
- `ci_spread/feedback.py` drops `CallerFeedbackSink` for `PlatoClient.submit_feedback` with the
  caller's identity headers as `request_headers_provider`, and takes the two constants from the
  client;
- `scripts/publish_packs_to_plato.py` takes `PlatoError` from the client. It still loads the SDK,
  as every `jaci` import does: `jaci/__init__.py` applies the SDK's model overlay at package
  import (found 2026-09-30, Phase 3). A publish path without the SDK has to live outside the
  `jaci` package, or that overlay has to move off package import.

The rest of jaci still needs the SDK for its in-process paths (jaci note §5).

## 6. Out of scope

- The pack-contracts package (jaci note §4): Pydantic models for policies, profiles, manifests and
  canonical objects. A separate, larger carve-out; this client neither needs nor blocks it.
- Typed clients for the eval, dataset, authoring-draft and admin routes. Add one when a
  non-SDK caller needs it.
- A sync client. Every current caller is async; jaci pages already bridge to async.

## 7. Risks

- **A client method drifts from its route.** This is why the package stays here; the round-trip
  tests catch it at the commit that causes it.
- **The Docker image misses the package.** Step 1.4. The image build's import smoke test (the
  `Dockerfile` comment near line 120 describes it for `jazzx_eval_contracts`) should name
  `jazzx_plato_client.client` too. Import the submodule, for the reason that comment gives: a
  wrongly nested COPY leaves the bare name importable as an empty namespace package.
- **A caller depended on `jazzx_sdk.clients.plato_client` internals** (`_detail`, `_turn`).
  The shim re-exports public names only. Nothing in jaci imports the private ones (checked).
