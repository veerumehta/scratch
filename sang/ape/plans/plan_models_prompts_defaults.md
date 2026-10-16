# Plan: Acra/DSCR defaults, selectable models, versioned prompts, recorded provenance

Status: proposed (2026-10-06), not started. Asked by the user after a policy extraction run on the
packs page; they want to compare extraction output against JTBDs from another source.

## Why

An extraction run today (a) lands in whatever tenant the request names or the server defaults to
(`acme-hospital`), (b) uses one model nobody chose (`flex_gpt-6-luna`, from `resolve_model()`),
(c) uses prompts that are string constants in code, and (d) records neither the model nor the
prompt. Output cannot be compared across models or prompt wordings, and a learning loop has
nothing to attribute a change to.

## What exists (verified in code, 2026-10-06)

- `evaluation/prompt_registry.py` + `prompt_registry_db.py`: versioned, aliased prompts
  (`register`, `get(version|alias)`, `set_alias`, `list_versions`; unchanged content reuses its
  version via `content_version`). Used by `guidance_ab`; nothing in the pipelines reads it.
- `modes/prompt_loader.resolve_mode_prompt`: pack-tuned, then pack default, then bundled file, for
  the five investigation modes only.
- `llm/model_data.json` model cards + pricing, and `plato/api/model_overlay.py` (what is in force).
- Case runs: `mode_overrides={mode: {model, temperature}}` and per-mode `usage` with `model`
  (`CaseResult.usage`). Eval `case_run` takes it as `config["modes"]`.
- Extraction: `ReasoningAgent(..., model=resolve_model())`, one model for every step; the run record
  (`ExtractionRun`) holds `stage`, counts and lint only. `ReasoningAgent` now tells a metering
  service each call's `(model, usage)` (`record_usage`), which case runs use for adjudication.
- 32 `instructions=` call sites in 25 modules; the extraction ones are `_PLAN_*` and `_WRITE_*`
  constants in `pipelines/policy_jtbd.py` (and the python and conditions extractors).

## Design

### P0. Defaults: tenant `acra-lending`, pack DSCR
- `_DEFAULT_LOCAL_TENANT` becomes `acra-lending`; `plato-local.sh` lists it first; the packs page
  opens on it and preselects the DSCR domain pack. Tests that assume `acme-hospital` as the default
  move with it. Deployed tiers still never guess (they require `X-Tenant-Id`).
- The server keeps defaulting a headerless local request to that tenant; refusing it is separate.

### P1. Record provenance on every LLM run (first, because the rest reads it)
- One `RunProvenance` shape: per step `{step, model, prompt: {name, version, digest}, calls, tokens,
  cost_usd}`, filled by the metered agent (generalising the `_MeteredService`/`record_usage` seam).
- `ExtractionRun.models` (JSON in the existing `data` column, no migration) and the same shape in
  `CaseResult.usage` entries (which already carry `model`; add `prompt`). Shown on the packs page
  run line and the runs page; included in the proposals JSON download.

### P2. Model selection
- `GET /models` lists selectable models: model cards (plus overlay) whose provider has a key.
- A run takes `model` (run default) and optional `models: {step: model}`: extraction submit
  (form field), case run submit (exists for modes; add the run default), eval experiments (exists).
- UI: a dropdown on the authoring panel, the runs page submit, and the evaluation page; the choice
  is remembered per browser. The default stays `JAPES_LLM_MODEL` / provider default.

### P3. Prompts as versioned files
- Files under `jazzx_sdk/prompts/<pipeline>/<name>.md`, front matter `name`, `version` (semver the
  author bumps), `description`; body is the template (`{section}`-style fields as today).
- Loader: file by name, a pack's `prompts/` overrides it (same order as `resolve_mode_prompt`), and
  `register`s the content in the `PromptRegistry` so every use has `(name, version, digest)`. A file
  whose content changed without a version bump is a lint finding, not a silent new version.
- Every extraction step reads its prompt through the loader; the constants go. The other 20-odd
  call sites follow, pipeline by pipeline, extraction first.
- Compare: `GET /prompts/{name}` lists versions with a diff; an eval experiment varies the prompt
  version like a model (config), and the comparison view groups by it. The optimizer registers
  candidates under an alias (`staging`) instead of editing files, and promotion writes the file.

## Order
P0 (small, one commit) then P1 (extraction + case runs) then P2 then P3 (extraction prompts, then
the rest). Each lands on `v2.6.1` with its tests and CHANGELOG, then a `plato` follow-up commit.

## Decisions (2026-10-06)
1. Default pack: `dscr-core` (the DSCR domain pack), not the `acra-dscr-core` assistant sample.
2. Prompt home: SDK files (`jazzx_sdk/prompts/`) with a pack `prompts/` override, both versioned.
3. First slice: extraction, case runs and adjudication; the other call sites follow.
4. Interactive/chat agents keep their profile-owned prompts for now (revisit after the first slice).
