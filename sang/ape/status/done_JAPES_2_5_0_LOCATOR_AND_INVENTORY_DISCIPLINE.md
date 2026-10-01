# plan_JAPES_2_5_0_LOCATOR_AND_INVENTORY_DISCIPLINE — evidence that points at a place, and an inventory that admits everything

Repos: `japes` (all of it), `jaci` (first consumer: CREMF multifamily; second: `dscr`, `ci_spread`).
**Revision 2** — written against `japes` **2.4.2** (HEAD `f9eb0ef`) and `jaci` **0.20.3** (HEAD `d8ba7d7`), both read in the working tree. R2 incorporates three review pushbacks: Phase 3 split into 3a/3b so the evidence fix is not blocked on CSV dialect uncertainty; Phase 5(a) committed to per-page routing rather than left as "route or warn"; and Phase 7 given a named adopter, because a flag nobody sets is this plan's own thesis failing in miniature. Risk 6 generalizes that last point into a rule for every phase. Driven by the CREMF-POC-01 PRD, but **nothing in this plan is CRE-specific** — every phase closes a general defect that Acra DSCR and AML hit identically.

**Read first.** In this repo's own rules: the **P8 module-placement** test and the **Unified Documents ruling** (`docs/ARCHITECTURE.md:554-555` — *"not a separate `documents/` package; there is no `jazzx_sdk.documents`"*), both quoted in `ape/plans/plan_JAPES_TEMPLATE_FILL_AGENT_AND_SKILLS.md` §2; `ape/plans/REFACTOR-2.4-subpackage-interiors.md` §10 (**P10** — capability ahead of demand must be *reachable*, *marked*, and *fail-fast if callable but incomplete*); `ape/plans/engineering_queue.md`; and the breaking-change discipline — a `strict_*` flag, a new typed error, a CHANGELOG **"Breaking"** heading, and pre-landing checks against dependent packs.

**Housekeeping found while writing this.** `docs/_to_delete/plan_JAPES_TEMPLATE_FILL_AGENT_AND_SKILLS.md` and `docs/_to_delete/plan_JAPES_2_4_0_MODE_CHASSIS_COMPLETION.md` are **byte-identical duplicates** of live plans in `ape/plans/` (verified with `diff -q`). The live copies are authoritative; the `_to_delete` pair is stale and should be removed so nobody reads a shelved-looking copy of an active plan. This matters here because the template-fill plan is **active, not abandoned** — see *Deliberately not in this plan*.

In code: `jazzx_sdk/agents/document/{agent,schema,spec,manifest,completeness}.py`, `jazzx_sdk/tools/documents/{conversion,docintel_azure,processors/pdf,split,templates}.py`, `jazzx_sdk/fabric/canonical/evidence.py`, `jazzx_sdk/expressions/{evaluate,definition}.py`, `jazzx_sdk/finance/metrics.py`. Consumer side: `jaci/src/jaci/capabilities/commercial_lending/{source_view,metric_result}.py`.

---

## The one-sentence version

The SDK's document chassis refuses ungrounded values, content-addresses its ingest, and lands on the canonical chain — and then emits an evidence coordinate that **points at a field name instead of a place**, while its directory walk **silently omits every file that isn't a PDF**. Phases 1 and 4 fix those two. Everything else here is smaller.

---

## Three things to settle before writing code

### 1. The locator types are already right; nothing constructs them

`fabric/canonical/evidence.py:78-108` ships a discriminated union that is exactly what a reviewer needs:

```python
class PageLocator(BaseModel):
    locator_type: Literal["document"] = "document"
    page: int
    region: str | None = None

class CellLocator(BaseModel):
    locator_type: Literal["workbook"] = "workbook"
    sheet: str
    cell: str

class SectionLocator(BaseModel):
    locator_type: Literal["section"] = "section"
    section: str
    path: str | None = None
```

`DocumentAgent._field` (`agents/document/agent.py:107-118`) hardcodes the third one, with the **field name** in the `path` slot:

```python
coord = SourceCoordinate(
    source_file_ref=source_file.source_file_id,
    locator=SectionLocator(section="document", path=name),   # `name` is the field name
    content_hash=source_file.content_hash,
)
```

`rg -n "PageLocator\(|CellLocator\("` across `jazzx_sdk` and `jaci/src` returns **only the two class definitions** — no construction site in any production path. Both are constructed in tests (`japes/tests/test_governed_values.py:118-124`, `jaci/tests/unit/test_source_view.py:41-55`).

Two facts make this a wiring job rather than a design job:

- **The producer exists and is tested.** `tools/documents/docintel_azure.py:198-254` — `analyze_result_to_json` returns `{"pages":[{page_number, title, page_header, page_footer, section_headings, footnotes, tables[]}]}`, and `_table_to_dict` (`:198-214`) preserves per-cell `content / row_index / column_index / row_span / column_span / kind`.
- **The consumer exists.** `jaci/.../source_view.py:53-92` already renders `PageLocator` and `CellLocator` for display. Downstream is waiting.

What is missing is the middle. `convert_to_json` and `locate_regions_from_json` are exported from `jazzx_sdk.tools` and have **no caller in `jazzx_sdk` or `jaci/src`**; the chassis calls only `convert()`, i.e. markdown (`agent.py:192-240`). This is a live **P10** violation: reachable, unmarked, and never exercised.

**Also note what Azure gives us and we throw away.** `_element_page` (`docintel_azure.py:48-51`) reads `bounding_regions` solely to extract `page_number`; `rg "polygon" jazzx_sdk` returns zero hits. We are strictly *losing* precision the provider already hands over.

### 2. `assert_provenance_complete` passes today on a coordinate that locates nothing

```python
# agents/document/agent.py:571-577
def assert_provenance_complete(result: DocumentResult) -> None:
    """XF-1 gate: every admitted field (doc_type + fields) carries a source coordinate + confidence."""
    admitted = [f for f in (result.doc_type, *result.fields) if f is not None]
    bad = [f.field for f in admitted
           if not (f.source and f.source.source_file_ref and f.confidence is not None)]
```

It checks `source_file_ref` and `confidence`. It does not look at the locator. So the gate is green while every fact in the system points at a filename and a field name. Phase 1 must tighten this gate in the same change that fixes the producer, or the regression walks back in the first time someone adds an extraction path.

### 3. Input-side workbook parsing needs a namespace decision before code

Per the Unified Documents ruling, this work lives under `tools/documents/` — there is no `jazzx_sdk.documents` and this plan does not propose one. But `jazzx_sdk/finance/workbook.py` already exists (write-side, 33 KB), and the template-fill plan records the house wariness about a third same-stemmed module: *"If a module needs a suffix to avoid colliding with a sibling, the namespace is wrong, not the name"* — cited there against `jazzx_sdk/templating` vs `tools/documents/templates.py`.

`tools/documents/workbook.py` and `finance/workbook.py` are **not siblings**, so P8's letter is satisfied. Whether the resulting two-`workbook.py` tree is acceptable is the SDK owner's call. **Decide it before Phase 3 starts**; the options are `tools/documents/workbook.py`, `tools/documents/workbook_source.py`, or extending `conversion.py` in place.

---

## Answering the objection this will draw

**"Phase 1 changes the locator type on every emitted fact — that's a breaking change to the evidence shape."**

It is a change, and it is the *intended* one. Three mitigations make it safe:

1. `SourceCoordinate.locator` is a **discriminated union** on `locator_type`, and `PageLocator` is already a member. Any consumer written against the union handles it; the one real consumer (`jaci/.../source_view.py`) handles it *today*.
2. Where a page cannot be determined — a passthrough `.md`, a `.txt`, a `LocalStubProvider` fixture — `SectionLocator` remains correct and is still emitted. This is additive precision, not a replacement.
3. The tightened gate in Phase 1 fails only when a `PageLocator` **was obtainable** and a `SectionLocator` was emitted anyway. Behind `strict_locators`, defaulting to off for one release, per the house breaking-change pattern.

**"Phase 4 changes `DirectoryResult`'s shape."** Yes, and this one is genuinely breaking — see Phase 4's gate. It gets the full pattern: `strict_inventory` flag, typed error, CHANGELOG **Breaking** heading, and a pre-landing check against `jaci`'s scenarios. **Do not put a day estimate on Phase 4.**

---

## Phase 1 — `PageLocator` through the chassis (P0)

**Why P0:** three separate product requirements across CREMF, Acra and AML reduce to *"a reviewer clicks a number and sees where it came from."* Today they cannot. This also unblocks `jaci`'s already-built source view.

**Tasks**

1. **One `analyze()` call, two views.** `docintel_azure.py:265-268` documents the footgun in its own docstring: `convert()` and `convert_to_json()` each issue a separate `analyze()`, so wanting both **doubles Azure spend**. Add a single entry point that calls `begin_analyze_document` once and derives both the markdown and the page/table JSON from the one `AnalyzeResult`. `analyze_result_to_markdown` and `analyze_result_to_json` are already pure functions over that object — no re-implementation, just a shared call site.
2. **Carry the structured view out of conversion.** `ConversionResult` (`conversion.py:328-402`) gains an optional structured-page payload. Absent for passthrough and PyMuPDF paths; present whenever the DI path ran.
3. **Resolve a page (and region) per extracted value.** `locate_regions_from_json` exists for this and has no caller. Wire it. `_field` gains an optional locator argument; when a page is resolved it emits `PageLocator(page=…, region=…)`, else it falls back to today's `SectionLocator`. `region` carries a table-and-cell or paragraph identifier that `source_view.py` can already render; a polygon only if it is free.
4. **Tighten the gate.** `assert_provenance_complete` grows a `strict_locators: bool = False` parameter. When true, an admitted field whose locator is a `SectionLocator` while the result carries a structured page view is a failure. Default off for one release, on in `japes`' own CI immediately.
5. **Mark it.** Per P10, the new entry point is exported from `tools/__init__.py` and its docstring states what it supersedes.

**Acceptance**

- A scanned two-page fixture yields fields whose `locator_type == "document"` with a `page` matching the page the value appears on, verified against a hand-labelled fixture.
- Exactly one `analyze()` call per document when both views are requested — asserted with a counting stub, not by inspection.
- `strict_locators=True` fails on a fixture where the page view is present and a field carries `SectionLocator`; passes on the `.md` passthrough fixture.
- `jaci`'s `source_view.py` renders a real page reference with no change to `jaci`.

**Size:** S–M. **Risk:** the `region` identifier's shape — settle it with whoever owns the click-through UI before task 3.

---

## Phase 2 — `formula_version` on the calculation record (P0, XS)

**Why P0:** *"no calculation exists without a formula version and inputs"* is a stated non-negotiable in the consuming PRD, and `VersionBundle` has nothing to pin until this exists. It is one field.

**Present state.** Inputs ship; the version does not:

```python
# jazzx_sdk/expressions/evaluate.py:57-63
class MetricDerivation(BaseModel):
    formula: str
    inputs: list[MetricInput] = Field(default_factory=list)
```

`MetricDefinition.version: str = "1"` and `approval_status` already exist (`expressions/definition.py:138-139`) and are simply never copied. `rg -n "formula_version|formula_id|calc_version"` over `jazzx_sdk` and `jaci/src` returns **zero hits**.

**Tasks**

1. `MetricDerivation` gains `formula_version: str | None` and `approval_status: str | None`, populated from the `MetricDefinition` at `evaluate()` (`evaluate.py:435-440`).
2. Mirror onto `jaci`'s `MetricDerivation` (`capabilities/commercial_lending/metric_result.py:41-46`) so a promoted spread carries it.
3. `VersionBundle` (`fabric/canonical/trace.py:116-135`) gains an optional `metric_catalog_version`. `model_versions` stays required and non-empty; this is one more optional pin alongside `policy_bundle_version`.
4. Every definition in `config/packs/ci-spread-core/metrics.yaml` sets an explicit `version`. Today none do.

**Acceptance:** a `MetricResult` round-tripped through the store reports the catalog revision that produced it; a metric definition with no `version` fails static validation rather than defaulting silently.

**Size:** XS. Do it first — it is the cheapest item in the plan and it unblocks a trust rule.

---

## Phase 3 — workbooks and CSV as evidence sources

**Split into 3a and 3b** (revision 1 bundled them; that was wrong). 3a is the evidence fix and is well understood. 3b is a separate, smaller job whose uncertainty is dialect and encoding handling, and there is no reason for the first to wait on the second.

**Scope note:** the *decision* of whether the consuming pack needs this is Product's, not the SDK's. But the SDK gap is real, general, and worth closing regardless — every financial pack eventually receives a workbook.

**Present state — the only workbook reader in the repo:**

```python
# tools/documents/conversion.py:181-217
wb = load_workbook(filename=str(path), read_only=True, data_only=True)
...
rows = [[_cell(c) for c in row] for row in ws.iter_rows(values_only=True)]
rows = [r for r in rows if any(r)]  # drop fully-empty rows
```

Each clause destroys something a reviewer needs:

- `data_only=True` → **formulas discarded**; the cached value only, and `None` if Excel never opened the file.
- `read_only=True, values_only=True` → `ws.merged_cells` never read (`rg "merged_cell"` → zero hits in source); no styles, so **no number-format-derived scale, sign or date semantics**; everything stringified.
- `if any(r)` → blank rows dropped, so **row indices no longer correspond to the sheet and a cell reference is unrecoverable in principle**, not merely unimplemented.

`.csv` is absent from `_READABLE_SUFFIXES` and from `convert_document`'s router (`:288-314`) and raises `Unsupported document type`. Every other `openpyxl` use in both repos is write-side.

### Phase 3a — workbook fidelity and `CellLocator`

**Tasks**

1. Namespace decision from §3 above.
2. A workbook source reader: `data_only=False` with both formula and cached value retained; `merged_cells` ranges preserved; **row and column indices preserved** (no blank-row dropping); number formats read for scale, sign and date typing.
3. `_field` emits `CellLocator(sheet, cell)` for workbook-sourced values — the Phase 1 locator argument makes this a second caller, not a second mechanism.
4. Parsing errors surface as typed failures via the existing `classify_failure` shape (`tools/documents/failures.py:32-52`) — do not invent a second error envelope.

**Acceptance**

- A workbook fixture with a merged header, a formula cell, an intentionally blank row and a thousands-scaled column yields facts whose `CellLocator` resolves to the correct `sheet!A1` **after** the blank row, with the formula string retained alongside the value.
- The markdown-flattening path still exists for LLM input and is documented as *not* the evidence path.

**Size:** M–L. **Risk:** openpyxl's read-only and formula modes are mutually exclusive in places; expect to open the file more than once and to measure the cost on a large rent roll.

### Phase 3b — the `.csv` route

A `.csv` branch in `convert_document`'s router: dialect sniffing, encoding fallback, and a synthetic single sheet name so `CellLocator` still applies. Independent of 3a and independently shippable.

**Acceptance:** a `.csv` fixture no longer raises; a semicolon-delimited and a Latin-1 fixture both parse; a cell reference resolves.

**Size:** S. **Risk:** contained — dialect sniffing fails loudly on an ambiguous file rather than guessing.

---

## Phase 4 — a total inventory, and refusal instead of substitution (P0)

**Why P0:** this is a correctness defect with a *silent* failure mode, which is the worst kind. Two behaviours, both live:

**(a) Silent omission by glob.** `process_dir` defaults to `pattern: str = "*.pdf"` (`agent.py:333`) and builds candidates solely from `base.glob(pattern)` (`:397-399`). An `.xlsx`, `.csv`, `.docx` or image in the folder appears in **neither `processed`, `skipped` nor `failed`** — it is invisible in the result *and* the manifest. Manifest status vocabulary is exactly `complete | failed` (`manifest.py:48`): no `pending`, `refused`, `unsupported`, `excluded`.

**(b) Synthetic content substitution.** A failed `fitz.open` is caught broadly and a fabricated string is passed downstream **as the document's content**:

```python
# tools/documents/processors/pdf.py:112-114
except Exception as e:
    self.logger.error(f"Error processing PDF: {e}")
    content = f"PDF file: {path.name} (error: {e})"
```

`extraction_method` stays `"fallback"`, so the `is_scanned` test at `:120` is False, so `convert_document` returns that one-line error string as the document's faithful markdown — and classification and extraction proceed on it. This directly contradicts the module's own faithful-conversion contract (`conversion.py:1-22`).

There is also **no encryption handling at all**: `rg -ni "encrypted|password|decrypt|is_encrypted"` over `jazzx_sdk` and `jaci/src` finds only API-key field types and the log-redaction key list.

**Tasks**

1. A `FileDisposition` vocabulary on the manifest and on `DirectoryResult`: at minimum `processed`, `skipped_unchanged`, `failed`, `unsupported_type`, `encrypted`, `excluded_by_pattern`.
2. `process_dir` inventories **every** file under the base path. Non-matching files get `excluded_by_pattern` with the pattern recorded; unsupported types get `unsupported_type`. Nothing is invisible.
3. Replace the substitution at `processors/pdf.py:112-114` with a typed `Refusal` (`fabric/canonical/refusal.py` — `RefusalClass.PRECONDITION_FAILED`) carrying the disposition. A file that cannot be read never contributes content.
4. Encryption detection ahead of the read, with its own disposition and reason.
5. Behind `strict_inventory`, defaulting off for one release. CHANGELOG under **Breaking**. Pre-landing check against every `jaci` scenario that calls `process_dir`.

**Acceptance**

- A folder holding one PDF, one XLSX, one encrypted PDF and one `.txt` produces four inventory entries with four distinct dispositions and one processed document.
- A corrupt PDF produces a `Refusal`, and **no `DocumentResult` whose content is a synthesized error string** — asserted directly, since that is the defect.
- One file's failure still leaves the other three intact (today's `degrade=True` behaviour, now covered by a test).

**Size:** M. **No day estimate** — it is breaking and the caller audit sets the cost.

---

## Phase 5 — routing honesty: mixed-mode pages, images, DI page accounting

**(a) Mixed-mode PDFs — route per page.** `is_scanned` is a whole-document verdict: `chars_per_page < 50` (`processors/pdf.py:49, 120-122`). A 200-page package with 190 digital and 10 scanned pages goes **wholly** down the digital path, and those 10 pages contribute nothing, silently.

**Route per page; do not settle for a warning.** Revision 1 left this as "either/or, decide later" — that was a decision deferred into implementation, which is where deferred decisions become whatever the first engineer does. Three reasons per-page routing is the answer:

- Phase 1 already builds per-page plumbing. Per-page routing is the natural extension of the same seam, not additional machinery.
- It is **cheaper**, not more expensive. Today's two options are "lose the scanned pages" or "send the whole document to DI." Per-page sends only the scanned pages, so a 200-page package bills 10 pages instead of 200 or 0.
- A warning puts the work on the operator, who cannot act on it — the remedy for "this document has 10 scanned pages we skipped" is exactly what the code should have done.

`chars_per_page` becomes a per-page test; pages failing it go to the provider individually and their output merges back in page order.

**(b) Images.** `convert_document` (`:289-314`) has no `.png` / `.jpg` / `.jpeg` / `.tif` branch. Add one via the DI provider — the same `prebuilt-layout` call already handles images.

**(c) DI page and cost accounting.** None exists: `rg -ni "page_count|cost|billing" jazzx_sdk/tools/documents/` returns only the scanned heuristic and log strings. Return a per-run page tally on `DirectoryResult` and attach it to the existing tracer span. Do **not** add OTel metric emission here — the repo has no metric plane yet and that is its own salvage item.

**Acceptance:** a bimodal fixture (mostly digital, a few rasterized pages) yields text for **every** page, with a counting stub asserting that only the rasterized pages were sent to the provider; a `.png` fixture converts; a run reports pages sent to DI.

**Size:** S–M.

---

## Phase 6 — wire `check_completeness` (XS)

`agents/document/completeness.py:29-58` is built, typed and tested, returning `{required, present, missing, unexpected, by_type, is_complete}`. Its only caller anywhere is `japes/tests/test_doc_pipeline_gaps.py`. Every consuming pack has a document-coverage requirement.

Expose it on `process_dir` via an optional `required` argument, returning the report on `DirectoryResult`. Nothing else changes. Another **P10** violation closed.

---

## Phase 7 — make the float metric helpers fail loud

`finance/metrics.py:10-11, 31` states its own contract as the thing the DSL exists to prevent:

> *"a missing input or a zero denominator yields `None` rather than raising"* · `Num = float | None`

Meanwhile `expressions/evaluate.py:11-13` promises *"never a silent zero, never `None` standing in for 'couldn't compute'"* and raises a typed refusal with a remediation string on division by zero (`:257-261`).

Both cannot be house style. Add a `strict` mode to the `finance/metrics.py` helpers that raises the same typed refusal, and mark the permissive path as display-only in the module docstring. **Breaking behind a flag**, house pattern, no day estimate.

**A named adopter, or this phase recreates the defect it fixes.** This plan's thesis is that a capability without a caller is dead — `check_completeness`, `locate_regions_from_json` and `MetricDefinition.version` are all in here for exactly that reason. Shipping `strict` behind a flag nobody sets would be the same failure in miniature. So:

- **Adopter:** the new `cremf` pack in `jaci` sets `strict=True` from its first commit. It is greenfield, has no legacy callers to migrate, and its consuming PRD already forbids a silent zero — so it is the cheapest possible first adopter and the flag is exercised on day one rather than at some later audit.
- **Acceptance is on the pack, not the SDK.** Phase 7 is not done when the flag exists; it is done when a CREMF metric evaluation with a missing operating-expense line **refuses** rather than returning a value computed from an implied zero. Put that test in the pack's suite.
- **P10 marking:** the permissive path's docstring names `strict=True` as the governed setting and names the pack that uses it, so the next reader knows the flag is live rather than aspirational.

**Then retire the existing callers.** `jaci`'s CRE paths use the permissive helpers plus `or 0.0` silent-zero accumulation (`scenarios/cre_underwriting/operating_spread.py:43-47`) and float `_div`/`_pct` (`capabilities/commercial_lending/analytics.py:96-124`). That retirement is `jaci` work and out of scope here — but with an adopter on `strict=True`, the two behaviours can no longer both look correct, which is the point.

---

## Phase 8 — require an approver on resume, at the pack boundary (S)

`DurableSuspension` carries `approver_ref: ActorRef | None`, `authority_basis: str | None`, `approved_at: datetime | None`, and `approved_at` is auto-stamped when an approver is supplied (`conductor/suspension_store.py:69-71, 135-140`; `suspension_store_db.py:128-133`). All three **default to `None`**, and nothing forces an approver on `resume_durable`.

Add a `require_approver: bool = False` construction option on the store; when set, `mark_resumed` without an `approver_ref` raises. Credit- and SAR-adjacent packs set it. No schema change, so no governed-change process.

**Related and already fixed — do not re-raise it:** suspend inside a `Loop` works. `_LoopSuspend` carries `loop_id` / `iteration` / `seq` (`conductor/engine.py:136-150`), `Suspension` and `DurableSuspension` carry `loop_id` / `loop_iteration` (`engine.py:183-184`, `suspension_store.py:54`), `resume_durable` threads them into `_resume_tail`, and there is a dedicated test section (`japes/tests/test_conductor_engine.py:543`). Any backlog still carrying *"HITL suspend raises inside a Loop"* is stale — **close it.**

---

## Deliberately not in this plan

- **`OutputTemplate` / `TemplateFillAgent`.** An **active Revision-2 plan** already exists at `ape/plans/plan_JAPES_TEMPLATE_FILL_AGENT_AND_SKILLS.md` — 379 lines, five phases, placement already argued to `agents/template_fill/` against P8, and it carries the invariant worth keeping verbatim: *"every template row is present, populated or not, so the unmatched set is enumerable and never a silent blank."* **Follow that plan; do not rewrite it.** (The identical copy under `docs/_to_delete/` misled an earlier draft of this document into calling it abandoned — delete that copy.) It is only on the critical path if the consuming product must fill a *customer's* workbook rather than author its own — a Product decision, and the cheaper reading does not need it. Its own §1 also draws the distinction this plan depends on: `ExtractionTemplate` is input-side, the output template is output-side, and Phase 3 here touches only the former.
- **Per-dimension confidence.** A nine-dimension decomposition has been requested elsewhere. `Confidence` is `{score, tier}` (`evidence.py:163-167`) and the extractor's score is the constant `extract_score=0.9` modulated only by the `_grounded()` string check (`agent.py:67-82`). Decomposing one synthetic number into nine synthetic numbers manufactures the appearance of calibration. Add a dimension only when a real signal sits behind it.
- **Dependency-graph recalculation.** `jaci`'s full re-run is correct and documented (`capabilities/commercial_lending/corrections.py:17-22`); evaluation is pure, so a re-run is sufficient. Add a purity test, not a graph.
- **CRE templates, chart of accounts, metric catalog.** Pack data in `jaci`, tier 2 via `TEMPLATES.load_yaml(path, tier=2)`. Not SDK work. (For the record: `TEMPLATES._TIER1` is still exactly `10-k` and `financial-statements`, `templates.py:38-51`.)
- **Chunking strategies, tenant-ID propagation, OTel metric emission, `fabric/opa/store.py`.** Existing salvage items with their own sizing; unrelated to this plan's thread.
- **`UNSUPPORTED` on `ProvenanceType`.** `evidence.py:118-123` records the deliberate deferral — *"a separate, later addition once a consumer needs it."* Leave it until a consumer does.

---

## Sequencing and gates

```
Phase 2  (formula_version, XS)          ──►  start now, no dependencies
Phase 6  (wire check_completeness, XS)  ──►  start now, no dependencies
Phase 3b (.csv route, S)                ──►  start now, no dependencies
Phase 1  (PageLocator, P0)              ──►  start now; gate = the `region` shape decision
Phase 4  (inventory + refusal, P0)      ──►  after the caller audit; breaking, no estimate
Phase 5  (per-page routing, images,     ──►  after Phase 1 (per-page seam) AND
          DI accounting)                     after Phase 4 (disposition vocabulary)
Phase 3a (workbook fidelity +           ──►  after Phase 1 (reuses its locator seam) AND
          CellLocator)                       after the namespace decision in §3
Phase 7  (fail-loud floats)             ──►  independent; breaking; lands with its
                                             `cremf` adopter, not before
Phase 8  (require_approver)             ──►  independent, small
```

**Two decisions gate real work.** The `region` identifier's shape (Phase 1 task 3) and the input-side workbook namespace (§3). Both belong to the SDK owner and neither needs a meeting.

**One ordering trap.** Phase 3a must not invent its own locator plumbing. If it starts before Phase 1 lands, `CellLocator` will arrive through a second mechanism and the two will diverge — which is exactly the shape of the `jazzx_sdk/templating` vs `tools/documents/templates.py` problem the template-fill plan warns about. Phase 3b has no such coupling, which is why it moves to the front.

---

## Risks

1. **Phase 1's `region` becomes a design project.** Mitigation: ship `page` alone first if the region shape is contested. A page number is already the difference between "somewhere in this 300-page file" and "here."
2. **Phase 3a is larger than it looks** and openpyxl's modes fight each other. Mitigation: fixture-first — write the merged-header/formula/blank-row/scaled-column fixture before any implementation, and let it define done. Splitting 3b out removes the dialect-sniffing unknown from this risk entirely.
3. **Phase 4's caller audit finds more than expected.** Mitigation: the flag defaults off; land the vocabulary and the inventory before flipping strictness.
4. **Both repos are moving fast.** `japes` HEAD `f9eb0ef` was committed the same day this plan was written, and `jaci` shipped 0.20.3 the day before. Re-run every grep in this document before estimating; prefer re-running them to trusting the counts.
5. **A pack ships around a gap instead of through it.** The mitigation is Phase 1: once a fact can carry a page, a pack that emits `SectionLocator` for a DI-processed document is visibly wrong rather than merely imprecise.
6. **A phase here ships a capability with no caller — the defect this plan exists to fix.** Live in Phase 7 (the `strict` flag) and latent in Phase 5's cost accounting. Mitigation: every phase names its adopter and puts at least one acceptance criterion **in the consuming pack's suite**, not only in `japes`' own tests. If a phase cannot name an adopter, it does not land this cycle.

---

## Why this is the right slice

Every phase closes a defect where **the SDK already has the harder half built and the cheap half missing**: the locator types without a producer, the structured DI view without a caller, `check_completeness` without a call site, approver fields without enforcement, `MetricDefinition.version` without a copy into the result. That is an unusually good ratio, and it is why this is a plan about wiring rather than architecture.

It also means the work is not CREMF's to fund alone. Acra DSCR needs Phase 1 for its guideline citations, AML needs Phase 4 for corpus coverage, and every pack that ever receives a spreadsheet needs Phase 3.

---

*Every file path, line number and quoted fragment above was read in `/Users/sangit/src/japes` (2.4.2, `f9eb0ef`) and `/Users/sangit/src/jaci` (0.20.3, `d8ba7d7`). Negative claims show the search that produced them so they can be re-run rather than believed.*
