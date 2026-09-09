# Vision in `document_ingest`, as an alternative to DocIntel

Status: proposed, not started. 2026-09-06.

## Why

`tools/documents/split.py` raises `DocumentNotReadableError` on a package with no text layer and
hands off to DocIntel, the paid per-page path. DocIntel returns text and leaves the split unsolved:
it says what the pages say, not where one document ends and the next begins.

A VLM over rendered pages answers both in one pass, and it is the only option that decides
boundaries. So the fallback chain becomes:

1. readable text, with per-type templates (existing, and where most inputs should land)
2. **vision** for split-and-classify on scanned packages (this plan)
3. DocIntel only where faithful field-level transcription is actually needed

Vision goes *before* DocIntel, not instead of it.

## What already works

Three findings that make this smaller than it looks.

**The Agents SDK supports images natively.** `Runner.run` takes `str | list[TResponseInputItem]`,
`EasyInputMessageParam.content` takes a content list, and `ResponseInputImageParam` is
`{type: "input_image", image_url | file_id, detail, prompt_cache_breakpoint}`. `openai_provider.py`
already passes `messages` straight into `Runner.run`, so the multi-turn path needs no change.

**Anthropic works by pass-through.** `anthropic_provider.py` forwards `messages` verbatim into
`client.messages.create`, so native image blocks go through today.

**Caching needs nothing.** `anthropic_native._cache_last_block` skips only empty text and empty
`tool_result` blocks, so an image block already receives the `cache_control` directive. OpenAI
carries `prompt_cache_breakpoint` on the image part itself.

## What does not work

**Gemini silently corrupts structured content.** `gemini_provider._to_contents` builds
`types.Part(text=str(m.get("content", "")))`, so a content list becomes the repr of a Python list,
sent as text. This is a latent defect independent of vision: *any* structured content degrades
silently rather than erroring.

**`supports_vision` is dead metadata.** Defined in `model_cards.py`, fed from `model_data.json`,
read by nothing. An image sent to a text-only model would fail as a provider 400.

**There is no rasterizer.** `pymupdf` is already a dependency, so rendering is available, but
nothing renders pages today.

## The Gemini SDK question

Much easier on a current SDK. `types.Part.from_bytes(data=..., mime_type=..., media_resolution=...)`
replaces hand-built `inlineData` entirely.

`media_resolution` takes `MEDIA_RESOLUTION_LOW | MEDIUM | HIGH | ULTRA_HIGH`, which is a direct
token-cost lever and the counterpart to OpenAI's `detail`. That pairing is worth exposing as one
neutral concept rather than two provider quirks.

**The pin is stale.** `pyproject.toml` has `google-genai = ">=1.0.0"`; 2.21.0 is installed and
2.22.0 is current. `media_resolution` is not in the 1.x line, so the floor needs raising to
whatever version introduced it -- to be verified, not assumed.

## Shape: a fourth route, not a new pipeline and not a new mechanism

`build_document_pipeline` already routes `detect -> (package | collection | single | refuse)` with
`PipelineStep.when` guards, and `build_document_components` returns a plain `{step_id: callable}`
map a caller can override. A vision route is `when="route == vision"` plus a step-impl, with
`detect` returning that route for a package with no text layer. That is a step and a routing rule,
using machinery that exists.

**One caution.** `when` is *descriptive* by its own docstring: "the executable predicate is bound
separately via `ConductorEngine(step_guards=...)`". So a vision branch needs both the declarative
guard and a registered predicate, and they can disagree -- the diagram saying one thing while the
run does another. Whatever lands here wants a test that the two agree.

## The YAML question is already answered

Every piece of "a YAML describing the pipeline, with code implementing helpers the steps
reference, stored as pack config" exists today:

| Wanted | Exists as |
|---|---|
| pipeline described in YAML | `ConductorPipeline.from_yaml(path, name=, registry=)` -- one file may hold several under `pipelines:` |
| code helpers steps reference by name | `StepRegistry` + `StepImpl`; a step names one via `impl:` |
| capability modules publishing steps across packs | the registry's stated purpose: a capability publishes, any pack's pipeline weaves it in by name |
| a pack override winning over the shared impl | explicit `components` binding beats the registry |
| shipped as pack config | manifest `conductor.pipeline` pointer, read by `Pack.pipeline` |
| mis-wiring caught early | `validate_against_registry` fails at load if an `impl:` is missing or its `emits` disagrees |

So the gap is **adoption, not mechanism**. `document_ingest.py` builds its pipeline as a Python
literal in `build_document_pipeline` and hand-binds every component, while the declarative path it
would use already ships. Moving it is a separate piece of work from vision, and doing both at once
would confuse which change broke what.

**The one genuine gap** is per-step configuration. `PipelineStep` carries `id`, `label`,
`component`, `impl`, `emits`, `consumes`, `execution`, `note`, `substeps`, `loop`, `phase`, `when`
-- and nothing for a model, a provider, or step parameters. Today a caller gets a different model
by binding a differently-configured agent into the components map, which works and is clunky.

Deliberately deferred. Adding `config:` to `PipelineStep` before there is a second real variant
asking for it is inventing the profile mechanism ahead of its consumer. The vision route is the
first variant; if a second arrives wanting a different model per step, that is the moment.

## Phases

Each phase is independently landable and independently useful.

### P1 — Gemini content conversion (defect fix, no vision)

Rewrite `_to_contents` to build real `Part`s from a content list instead of `str()`-ing it, with a
test that a structured content list survives. Lands as a bug fix; nothing depends on it.

### P2 — the neutral image part and its converters

A small `ImagePart` (bytes or base64, media type, optional detail/resolution hint) plus a
`format_content` counterpart to `format_tools` on `AgentProvider` -- the seam japes already uses
for tools, so vision does not become a second model-calling layer.

Three converters: Anthropic `{"type":"image","source":{"type":"base64",...}}`, OpenAI
`{"type":"input_image","image_url":"data:..."}`, Gemini `Part.from_bytes`.

`supports_vision` gets its first reader: an image bound for a text-only model fails with a clear
message rather than a provider 400.

Verification is a contract test per provider asserting the wire shape, plus one gated live smoke
per provider -- mocks cannot catch a wrong field name, which is the whole failure mode here.

### P3 — rasterization

`tools/documents/` grows a page renderer on `pymupdf`. **The open decision is DPI and downscaling**,
which sets the economics of the entire path: resolution drives token count, and token count is the
reason to prefer this over DocIntel. Needs a measured answer, not a default.

### P4 — split-and-classify over images

The vision branch of `split.py`, reached where `DocumentNotReadableError` is raised today. Two
algorithm ideas are worth taking, as design rather than code:

- **overlapping windows with interior-page preference** -- pages classified in windows with a
  shared overlap; where a page appears twice the call that had it as an interior page wins, ties on
  confidence. Every page gets one full-context classification without re-running the package per
  page.
- **identity as a hard veto on merges** -- a narrow "transcribe, never infer" call extracts printed
  identity strings, and two adjacent same-type fragments are never merged when those conflict,
  however visually continuous they look. Folding both signals into one score lets a strong
  "looks continuous" read outvote a real name mismatch.

### P5 — the cost question, answered (measured 2026-09-06)

**Vision is not cheaper than extracted text. It is 1.4x to 2.7x more expensive per page**, and the
claim that motivated this work does not hold on a real corpus. Measured over the 40-page Acra
corpus with `scripts/local/measure_document_evidence.py`, on the 8 pages where both routes are
possible:

| evidence | tokens/page | vs text |
|---|---|---|
| extracted text | 556 | -- |
| image (openai) | 765 | 1.4x |
| image (gemini) | 1032 | 1.9x |
| image (anthropic) | 1508 | 2.7x |

**But that comparison covers a fifth of the corpus.** The other 32 pages (80%) have no text layer,
and there the text route is not more expensive, it is *unavailable* -- `split_document` raised on
exactly these pages until this work. Averaging across all 40 makes text look 13x cheaper, which is
an artifact of counting zero for pages it cannot read at all.

**So the justification is capability, not cost**, and the plan's framing was wrong. Vision is the
only route that answers a scanned package, and it is cheaper than DocIntel ($0.32 for those 32
pages) while also deciding boundaries, which DocIntel does not. On a readable page it should stay
the fallback it is: the text route is cheaper *and* the more accurate of the two on text.

**The crossover is real but rare.** An image is a fixed cost per page; text scales with density, so
a dense enough page costs more as text. That needs >765 tokens/page on OpenAI (3 of 8 pages here),
>1032 on Gemini (1 of 8), >1508 on Anthropic (0 of 8). Dense-text packages exist, and for those the
routing decision could go the other way -- but it is a per-corpus question, not a default.

**Not measured: accuracy.** Whether a model reads a rendered page as well as it reads extracted
text needs labelled documents and live calls. A cheaper route that is wrong more often is not
cheaper, and no token count substitutes for that.



Measure vision against DocIntel on scanned pages, and against text extraction on readable ones.
The token claim motivating this has no benchmark behind it anywhere yet. P3's DPI decision and the
choice in the fallback chain both depend on the answer, so it should be a real measurement before
this is presented as a cost win.

## Adjacent: the usage metric keys

`pipelines/chat.py` declares `_USAGE_METRIC_KEYS` as a bare tuple of six names that
`llm/cost_tracker.py` already defines as fields, with `prompt_tokens`/`completion_tokens`/
`total_tokens` derived on top. Eighteen modules mention `cached_tokens`; the ones that *produce*
counts are fine, the ones that restate the *name set* are the problem, because nothing derives
from a single declaration.

Vision makes this concrete rather than tidy: image tokens are their own bucket on every provider,
and they are the number the whole vision-versus-DocIntel argument turns on. Adding a seventh bucket
today means finding every site by grep.

The fix is to export the key set from `cost_tracker` and have the emitters derive from it, keeping
`chat.` namespacing as a prefix applied to a shared list. Two behaviours must survive: `_turn_metrics`
deliberately emits the *union* of both paths' keys zero-filled, because emitting either verbatim
"would give one run name two metric schemas and silently split every aggregate"; and
`cost_usd_known` separates "cost nothing" from "cost not reported". Neither is incidental.

Landable before any vision work, and worth doing first so the new bucket has one home to go in.

## Open decisions

1. **DPI and downscaling** (P3). Blocks the cost story.
2. **Where the seam sits** -- `AgentProvider`, or one level down in the native clients. The
   OpenAI path routes through the Agents SDK, which may not accept arbitrary parts identically.
   (Partly answered: `Runner.run` takes `list[TResponseInputItem]` and japes already passes
   `messages` straight through, so the multi-turn path is fine; the simple-query branch coerces.)
3. **The `google-genai` floor** -- which version first carried `media_resolution`.
4. **Scope of the first cut** -- classify-only over a caller-supplied page range would exercise the
   whole stack with far less surface than full split-and-classify, and would answer P5 sooner.
