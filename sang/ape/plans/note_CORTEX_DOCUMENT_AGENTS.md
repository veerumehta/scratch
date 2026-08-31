# CORTEX document agents, read against japes

A 10-agent pipeline turning compliance PDFs into a knowledge graph. Agents 1–4 are the document
half: organise, extract entities, extract rules, merge. This note is about what japes should take
from agent 1 in particular, since that is where the two designs actually disagree.

Read against the current tree of both. Nothing was run.

---

## The one architectural difference

**japes converts, then chunks. CORTEX chunks natively, per format.**

japes: `conversion.py` turns PDF/DOCX/XLSX/CSV into markdown, then `chunking.py` splits that
markdown by section headers under config rules. One chunker, many converters.

CORTEX: a `BaseChunker` per format — `MarkdownChunker`, `CSVChunker`, `ExcelChunker`, `DocxChunker`,
plus a PDF path — each reading the source in its own terms, behind a `ChunkerToolRegistry` keyed by
extension.

Both are defensible and the trade is clean. japes' shape means format support is added once, at
conversion, and every downstream stage sees one thing. CORTEX's means each chunk knows where in the
*source* it came from.

That second property is the whole finding, because it is the one japes cannot currently express.

## What japes cannot say about a chunk

`DocumentChunker.chunk_document(filename, content, mode) -> list[tuple[str, str]]`.

A chunk is a name and a string. By the time it runs, the source has been flattened to markdown, so
there is nothing left to say which page, row, or sheet the text came from.

CORTEX's `DocumentChunk` carries `page_start`/`page_end`, `row_start`/`row_end`, `sheet_name`, and
`section_path` — a hierarchical list like `["Chapter 1", "Section 1.1"]`.

**japes is not locator-blind overall** — that would be the wrong conclusion. `SectionLocator`,
`_resolve_locator` and `assert_provenance_complete(strict_locators=True)` all exist, and the
DocumentAgent attaches locators to extracted *fields*. But it does so by **recovering** the location
— matching the extracted value back against the markdown — rather than **preserving** it from the
source. `extraction.py` already knows the failure mode and says so: an anchor that is too loose
"would hit almost every page and produce a meaningless locator".

So the gap is specific: japes recovers a locator by search and can mis-hit; CORTEX carries one it
never lost. For covenant and compliance work, where the citation *is* the deliverable, preserving
beats recovering.

## What japes already has, and should not re-take

Worth stating so a port does not duplicate:

- **PDF outline reading.** `split.py:split_by_bookmarks` already parses the outline — for splitting
  a combined package into documents. CORTEX uses the same primitive for *sections within* a
  document. Same reader, different question; japes has the reader.
- **Format coverage.** `conversion.py` handles PDF, DOCX, XLSX/XLSM, CSV, MD/TXT with pandoc and
  library fallbacks, plus DocIntel and an offline stub. Broader than CORTEX's chunker set.
- **A registry keyed by document type.** `DocumentClassifierRegistry` is the same pattern as
  `ChunkerToolRegistry`.
- **Config-driven chunk rules.** `ChunkingConfig`/`ChunkingRule` with per-pattern modes, plus
  small-section merging. CORTEX's config is three size numbers.
- **Schema-driven extraction.** `tools.extract` against a pydantic schema, with templates and
  anchors, is more general than agents 2/3's fixed entity/rule shapes.

## Worth taking

1. **A locator on the chunk.** The change is to make chunking able to *carry* provenance rather
   than have extraction rediscover it. Concretely: a chunk type with an optional page/row/sheet and
   a `section_path`, populated where the converter knows it and left empty where it does not. This
   is the item with real downstream value — it is what would let a covenant citation name a page
   without a text search that can hit the wrong one.

2. **Section hierarchy.** `section_path` as a list beats a flat title: "Section 6.1 under Covenants
   under Article VI" is the answer a reviewer wants, and japes currently keeps only the matched
   header string.

3. **TOC-driven chunking for PDFs.** japes splits *documents* by outline; chunking *sections* by
   outline is the same primitive one level down, and it is strictly better than header-regex on
   converted markdown for a 500-page document that has bookmarks.

4. **Chunk-size normalisation as a second pass.** CORTEX chunks structurally first, then normalises
   sizes with sub-chunking. japes' rules decide size during the split, so a structurally-correct
   section that happens to be huge has no path to being divided while keeping its identity.

## Worth noting, not taking

- **The LLM TOC detection and LLM structure analysis.** Reasonable in a batch pipeline; japes'
  equivalent decision belongs behind the same "readable first, model last" ordering the document
  tier already uses, not as agent 1's default.
- **`ThreadPoolExecutor` with 10 workers** (agent 3). japes is async throughout; the concurrency
  primitive already exists in `jazzx_sdk.concurrency`.
- **Per-provider batch sizes** (`rules_per_batch_anthropic: 4` vs `openai: 10`). That is a model
  capability fact, and japes has a place for those — the model cards — rather than a pipeline
  config.
- **The meta-agent prompt optimisation loop** in agent 2. japes has `evaluation/optimization.py`
  for this and it is more general; a second loop is not wanted.
- **Quality scoring as fixed weights in config** (5 factors × 20 points). japes' `scorers.py`
  composes scorers; the weights belong there.

## Not verified

- Whether CORTEX's chunkers are used anywhere outside this pipeline, which would decide whether a
  japes equivalent is an absorption or a parallel implementation.
- How agent 1 behaves on a scanned PDF beyond the per-page OCR fallback, and whether that path is
  exercised.
- Whether `section_path` survives into the knowledge graph or is dropped at agent 4's merge — which
  decides whether the hierarchy is load-bearing or incidental.


---

# Follow-up: is the locator on the ingest path, and what pipeline is worth crafting

## The locator is *not* exercised by `document_ingest`

japes has **two independent chunkers with different contracts**, and the ingest path uses the other
one:

| | `tools/documents/chunking.py` | `tools/documents/extract.py` |
|---|---|---|
| Entry point | `chunk_document(filename, content, mode)` | `chunk_by_headings` / `_chunk_by_chars` |
| Returns | `(name, content)` pairs -- now `Chunk` with a locator | `list[str]` -- bare strings |
| Config-driven | yes (`ChunkingConfig`, per-pattern rules, skip lists, merge) | no (a char budget) |
| Used by | **nothing** -- the only reference is a docstring example in `local.py` | `extract()` -> `DocumentAgent` -> `document_ingest` |

So the richer, configurable chunker is unused, and the pipeline runs on the simpler one. The
locator work landed on the unused side.

**What it would take to reach the pipeline.** `Chunker = Callable[[str, int], list[str]]` is the
seam. Widening it to return `Chunk` rather than `str` puts locators on the extract path, and
`extract()` merges field-wise across chunks -- so it already knows which chunk produced which
field, and could attach that chunk's locator to the field directly. That is the same answer
`DocumentAgent._resolve_locator` currently reaches by searching the markdown, arrived at without a
search that can mis-hit.

Worth doing, and worth doing as its own change: it touches the extraction path every document
flows through, and the two-chunker split is a question in its own right (one of them should
probably absorb the other).

## The ten agents, grouped

They are three pipelines, not one, and japes' coverage differs sharply per group:

**A. Document → structured rules (1–4).** Chunk, extract entities, extract rules, merge.
japes has the parts and they are more general: `tools.extract` takes any pydantic schema where
agents 2–3 have fixed entity/rule shapes, and the merge is a join. What japes lacks is a *named*
pipeline for "turn a corpus into a rule set" -- but that is assembly over existing pieces, which is
what `pipelines/` is for.

**B. Graph optimisation (5).** Conservative dedup plus typed dependency inference across 7 kinds
(prerequisite, sequential, conditional, complementary, contradictory, override, validation).
japes has `fabric.graph` for ontology, triples, query and traverse -- but nothing that *infers*
dependencies between rules. Genuinely absent, and non-trivial.

**C. Two-graph comparison (7–10).** Cluster rules by behaviour, match semantically within cluster,
compute set operations, visualise.
**japes has nothing here, and this is the group worth building.**

## Recommendation: the comparison pipeline

Four reasons it is the right subset:

1. **It is genuinely absent.** A and B overlap what japes already does; C does not.
2. **It is domain-general.** "Given two rule corpora, what is shared, what is only in each, and
   what contradicts" is not a compliance question -- it is a set question. The CORTEX framing (an
   agency guideline versus a lender overlay) is one instance; policy version A versus B, or a
   pack's rules before and after a release, are others.
3. **It has direct product value here.** "What does this overlay change against the base
   guideline" is the CRE question, and the contradiction set is the interesting half: two documents
   that each look fine and disagree with each other is exactly what a reviewer cannot find by
   reading.
4. **It generalises a primitive japes already has.** `evaluation/golden_cases/versioning.py`
   computes `CaseSetDiff` -- added / removed / changed / unchanged over two versioned collections.
   Agents 7–9 are that same operation with two substitutions: a **semantic matcher** in place of
   identity comparison, and **contradiction** as a fourth outcome alongside added/removed/shared.

That last point is what makes it an evolution rather than a transplant. The shape to aim for is a
matcher-pluggable set diff -- exact identity for case sets, an LLM judge for rules -- rather than a
second diff implementation that happens to be about rules.

**What not to carry over:** the behaviour taxonomy (8 kinds) and domain list (10) are authored
content, not platform concepts -- they belong in a pack, registered the way signal tags now are.
The `ThreadPoolExecutor` batching is `jazzx_sdk.concurrency`'s job. The HTML visualisers (6 and 10)
are a surface, not SDK.

**Sequence:** the matcher-pluggable diff first, since it is the reusable core and testable without
an LLM; the clustering and set operations on top of it; contradiction detection last, because it is
the one that needs a real model and a real corpus to tune.
