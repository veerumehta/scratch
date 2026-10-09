# Plan: scanned documents in DocumentAgent (v2.6.2)

Status: approved by the user, building back to back on `v2.6.2`, one review at the end.
Test bed: `tests/fixtures/local/acra_godocs_mixed` (real borrower data, gitignored: never commit,
log or quote its contents; reports are aggregate figures only).

Prior art read first: japes already has `rasterize.py` (pixel budget), `split.py` (scanned-page
detection, vision route, windowed vote), `conversion._convert_pdf_mixed_mode` (per-page digital vs
DocIntel), the `.japes` markdown cache, `classify_page_images`. Not present anywhere (imdoc, macer,
japes): per-page routing on the vision route, garbage-text-layer detection, vision transcription,
DocIntel pricing, dollar budget.

## 1. Seams

```
jazzx_sdk/tools/documents/pages/
  assess.py     page kind: digital | scanned | bad_text (text-layer quality)         [S2]
  readers.py    PageReader protocol; VisionReader, DocIntelReader (read/layout)       [S3]
  forms.py      FormReader: a DocIntel prebuilt form model -> mapped fields           [S6]
  cache.py      content-hash cache of rendered pages, labels, transcripts            [S5]
  budget.py     VisionBudget: pages in flight and dollars                             [S5]
jazzx_sdk/tools/documents/docintel_models.py  GET /documentModels discovery, cached [S6]
jazzx_sdk/llm/page_pricing.py                 per-page rows of model_data.json       [S5]
jazzx_sdk/prompts/documents/*.md  versioned prompts via load_prompt                  [S4]
```

Engine names (`engine` in `document_agent.yaml`, run-level override on the step and the run):

- `vision`: a vision model transcribes each scanned page (own higher resolution, one page per call).
- `docintel`: DocIntel `prebuilt-read` / `prebuilt-layout` OCR (`docintel:<model id>` names one).
- `auto`: `docintel` when `AZURE_DOCUMENT_INTELLIGENCE_KEY` (or an Azure identity) and
  `_ENDPOINT` are set, else `vision`.
- `docintel:prebuilt-<form>`: a prebuilt form model; opt-in per class only, never the default.

```yaml
engine:
  default: auto
  by_class:                       # opt-in; absent = no prebuilt model is used
    appraisal_report: docintel:prebuilt-mortgage.us.1004
field_maps:                       # data, not code: prebuilt field -> pack field or Entity.field
  prebuilt-mortgage.us.1004:
    MarketValue: property_value
```

A class's `fields:` still limits what is filled. An unmapped prebuilt field is reported on the
document item (`unmapped_reads`, with value and page), never dropped.

## 2. Phases

- **S1 Plumbing.** `DocumentAgentSpec`: `split_vision`, `vision_model`, `vision_detail`,
  `vision_flex`, `engine`, `field_maps`, `vision_budget_usd`; through `_split`, `process_package`,
  `split_blob`, `DocumentIngestStep` (engine override), run-level override on the case run.
  Credentials: `AzureKeyCredential` when `_KEY` is set, else `DefaultAzureCredential`; asking for
  OCR with neither (or no `_ENDPOINT`) fails naming both.
- **S2 Per page.** `assess.py`: a page is `scanned` (no text, has image), `bad_text` (replacement or
  non-printable ratio, implausible words, text area vs image area) or `digital`. Split renders and
  reads only non-digital pages; digital pages keep their PyMuPDF text; windows mix both.
- **S3 Transcription.** A scanned page is transcribed at 300 dpi / 2200 px, one call per page,
  large `max_tokens`, `low_confidence` plus reason per page; one failed page is tolerated, all
  failing raises. Extraction runs on the transcript, so `_grounded` still has text to check.
  `docintel` OCR fills the same seam.
- **S4 Split quality on image-only runs.** Versioned prompts (pass one, continuation, attachment):
  per-page `observations` before the label; e-sign certificates and disclosures belong to the signed
  document; transmittals, addenda and exhibits stay with their parent, peers stay separate; a
  vision identify step (printed names or numbers) so identity split and attach work without text
  (`attach_below` stops being skipped on the vision route); attachment reconciliation where the
  longer fragment leads. Form 70 / 1004 / 1007 and photo-addendum guidance written here.
- **S5 Cost and budget.** `model_data.json` gains `document_models` (per page, source URL, verified
  date, `sources.azure_docintel`), fetched from Azure's pricing page, add-ons noted. DocIntel pages
  are priced into the same `ModeUsage` and `StepProvenance` as model calls; the push-time check
  (`update_model_pricing.py --check`) covers the rows. `VisionBudget` caps dollars as well as pages
  in flight; spend recorded in provenance. Cache rendered pages, per-page labels and transcripts by
  content hash beside the `.japes` markdown cache; Anthropic `cache_control` on window images.
- **S6 Prebuilt forms and the models page.** Discovery from `GET {endpoint}/documentintelligence/
  documentModels?api-version=2024-11-30`, cached. `FormReader` runs the class's configured model and
  applies `field_maps`. Plato's models page lists DocIntel models beside the LLM models: provider,
  model id, kind (OCR, layout, prebuilt form), unit (per page), price (or "price not recorded"),
  verified date, offered by the resource.
- **S7 Validation (local, gated test, skips when the folder is missing).** Both engines on the
  Acra folder with jaci's 0.2.10 split config; the appraisal also through `prebuilt-layout` and
  `prebuilt-mortgage.us.1004`. Reported per engine, aggregate only: segments and labels, scanned
  pages, fields read (value, address, units, property type, rent present), accuracy against the
  page, cost from the table, time.

## 3. Decisions

- Per-page, not per-file: today one scanned page makes every page render.
- `auto` never selects a prebuilt form model; those are per class and opt-in.
- DocIntel rows live in their own `document_models` section, so token pricing code is untouched;
  the staleness check reads both.
- Real borrower data goes only to the user's own Azure resource and the configured vision model,
  from the gated test, run by the user's explicit approval of this plan.

## 4. Open

- Anthropic `cache_control` on window images depends on the Anthropic provider's content mapping.
- Prebuilt field names per model are read from a live analyse result, not assumed.
