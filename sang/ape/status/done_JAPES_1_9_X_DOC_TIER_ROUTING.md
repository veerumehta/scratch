# JAPES 1.9.x - Document Tier Routing and Online Fallback
## Claude Code Handoff

**Author:** Virendra Mehta
**Branch:** main (or feature/doc-tier-routing)
**Repo:** `japes/` only - no JACI changes
**JAPES version at time of writing:** 1.9.2

---

## Background and motivation

Document processing in commercial lending predates DocIntel and AI. For decades, lenders
used structured feeds (Compustat, Bloomberg), EDI, and MISMO XML for machine-readable
exchange - the "document" was already a typed record long before OCR. DocIntel is a
substitute for human keying on genuinely unstructured documents, not the only path to
structure.

The current conversion layer has two modes: readable (direct extraction) and unreadable
(DocIntel). This plan introduces a four-tier routing model that reflects how documents
actually arrive and what the right processing strategy is for each tier.

---

## Four-tier document model

**Tier 1 - SDK-native, industry-standard documents**
Known format, stable structure across the industry. The SDK ships the extraction template,
the online retriever, and the fallback source. A pack author declares the document type and
gets everything for free. Example: SEC 10-K via EDGAR.

**Tier 2 - Lender-configured, known-structure documents**
Consistent structure within a lender's world, varies across lenders. Knowable and
authorable at domain pack bring-up. Lives in the domain pack (JACI) or registered into the
SDK template registry with pack-supplied YAML. Example: a bank's borrowing base certificate
layout, their credit memo template.

**Tier 3 - Borrower-supplied, variable-structure documents**
Readable (digital PDF, xlsx, docx) but not templatable in advance. The borrower sends
whatever they have. LLM is invoked dynamically to map their line labels to the target
spread schema. Example: CPA-prepared financials, accountant compilations, Excel-based T-12s.

**Tier 4 - Rasterized or binary documents**
No text layer. DocIntel is the only entry point. After DocIntel produces markdown, the
result promotes to the appropriate earlier tier based on document type recognition - it is
never a terminal state.

**Cross-tier promotion** is the key design invariant. A rasterized 10-K enters as Tier 4,
DocIntel produces markdown, classification recognizes it as a 10-K, and it is processed as
Tier 1 from that point forward. The markdown is cached in the fabric so subsequent runs
skip DocIntel entirely. For Tier-1 documents, an online fallback (e.g. EDGAR) can bypass
DocIntel entirely when the canonical digital version is available.

---

## What this plan changes

Four additive changes to `jazzx_sdk/tools/`. Nothing is removed or renamed. Existing
callers of `convert_document`, `classify_document`, and `TEMPLATES` are unaffected.

---

## Change 1 - Filename heuristics in `classify.py`

### Why

The current `classify_document` sends a text sample to the LLM to identify the document
type. For many documents, the filename alone gives a reliable high-confidence answer at
zero cost - "YETI FY 2025 SEC 10-K_1.3.2026.pdf" requires no LLM call to classify.

### What to add

In `jazzx_sdk/tools/classify.py`, add a private function before `classify_document`:

```python
import re as _re

# (filename stem, lowercased) -> (label, confidence)
# Patterns are tried in order; first match wins.
_FILENAME_PATTERNS: list[tuple[str, str, float]] = [
    # Tier-1 SEC filings
    (r"10[-_\s]?k\b",                    "10-k",                      0.95),
    (r"10[-_\s]?q\b",                    "10-q",                      0.95),
    (r"\bannual\s+report\b",             "10-k",                      0.85),
    (r"\bearnings[-_\s]release\b",       "earnings-release",          0.90),
    (r"\bdef[-_\s]?14a\b",               "proxy-statement",           0.95),
    (r"\b8[-_\s]?k\b",                   "8-k",                       0.90),
    # Tier-2 lender docs (common naming conventions)
    (r"borrowing[-_\s]base",             "borrowing-base-certificate", 0.90),
    (r"credit[-_\s]memo",                "credit-memo",               0.85),
    (r"loan[-_\s]agreement",             "loan-agreement",            0.85),
    (r"closing[-_\s]pack",               "closing-package",           0.80),
    # Tier-3 borrower-supplied financials
    (r"\bt[-_\s]?12\b",                  "t12-operating-statement",   0.90),
    (r"t[-_\s]?three\b|trailing[-_\s]3", "t3-operating-statement",    0.85),
    (r"rent[-_\s]roll",                  "rent-roll",                 0.95),
    (r"operating[-_\s]statement",        "t12-operating-statement",   0.80),
    (r"appraisal",                       "appraisal",                 0.85),
    (r"inspection[-_\s]report|pca\b",    "inspection-report",         0.85),
    (r"title[-_\s]report|title[-_\s]commitment", "title-report",      0.85),
    (r"spread\b",                        "financial-spread",          0.75),
]


def _filename_heuristic(
    filename: str, taxonomy: list[DocClass]
) -> "Classification | None":
    """Return a high-confidence Classification from filename patterns alone, or None.

    Only returns a match when the label is in the caller-supplied taxonomy (or taxonomy
    is empty, meaning no restriction). Tries each pattern against the lowercased filename
    stem in order; first match wins.
    """
    stem = _re.sub(r"\.[^.]+$", "", filename).lower()
    valid = {c.label.lower() for c in taxonomy} if taxonomy else None

    for pattern, label, confidence in _FILENAME_PATTERNS:
        if _re.search(pattern, stem):
            if valid is None or label in valid:
                return Classification(
                    label=label,
                    confidence=confidence,
                    rationale=f"filename heuristic matched pattern '{pattern}'",
                )
    return None
```

Then modify `classify_document` to accept `filename: str | None = None` and try the
heuristic before the LLM:

```python
async def classify_document(
    source: str,
    taxonomy: list,
    *,
    filename: str | None = None,
    agents: Any = None,
    model: str | None = None,
    di_provider: Any = None,
    require_readable: bool = False,
    max_chars: int = 8000,
) -> Classification:
    classes = _normalize(taxonomy)
    if not classes:
        raise ValueError("taxonomy is empty")

    # Try filename heuristic before any LLM call.
    if filename:
        hit = _filename_heuristic(filename, classes)
        if hit is not None:
            return hit

    # Fall through to LLM-based classification (existing logic unchanged).
    ...
```

If `source` is a file path and `filename` is not supplied, auto-extract it:

```python
    if filename is None:
        from pathlib import Path
        try:
            p = Path(source)
            if "\n" not in source and p.exists():
                filename = p.name
        except Exception:
            pass
    if filename:
        hit = _filename_heuristic(filename, classes)
        if hit is not None:
            return hit
```

### Acceptance check

```bash
python3 -c "
from jazzx_sdk.tools.classify import _filename_heuristic, DocClass
taxonomy = [DocClass('10-k'), DocClass('rent-roll'), DocClass('credit-memo')]
assert _filename_heuristic('YETI FY 2025 SEC 10-K_1.3.2026.pdf', taxonomy).label == '10-k'
assert _filename_heuristic('Mesa_Verde_T12_Spread.xlsx', taxonomy) is None  # t12 not in taxonomy
assert _filename_heuristic('Rent Roll Q1 2025.pdf', taxonomy).label == 'rent-roll'
assert _filename_heuristic('random_document.pdf', taxonomy) is None
print('PASS')
"
```

---

## Change 2 - Tier tagging on the template registry

### Why

Routing logic (Change 4) needs to know whether a document type has SDK-level handling
(Tier 1) or pack-configured handling (Tier 2). The registry currently stores templates
without tier metadata.

### What to change in `jazzx_sdk/tools/templates.py`

Add a parallel `_tiers` dict to `TemplateRegistry`:

```python
class TemplateRegistry(NamedRegistry):
    _kind = "extraction template"

    def __init__(self) -> None:
        super().__init__()
        self._tiers: dict[str, int] = {}

    def _key(self, name: str) -> str:
        return name.lower()

    def register(self, name: str, template: Any, *, tier: int = 3) -> None:
        self._put(name, template)
        self._tiers[self._key(name)] = tier

    def register_dict(self, name: str, anchors: dict, *, tier: int = 3) -> None:
        from jazzx_sdk.tools.extraction import ExtractionTemplate
        self.register(name, ExtractionTemplate.from_dict(anchors), tier=tier)

    def load_yaml(self, path: str, *, tier: int = 2) -> None:
        """Register every template in a YAML mapping {name: {anchors: ...}}.
        Defaults to tier=2 (pack-configured) for YAML-loaded templates."""
        import yaml
        data = yaml.safe_load(open(path).read()) or {}
        for name, anchors in data.items():
            self.register_dict(name, anchors, tier=tier)

    def tier_of(self, name: str) -> int:
        """Return the tier for a registered template name, or 3 if not registered."""
        return self._tiers.get(self._key(name), 3)
```

Update the SDK tier-1 registrations at the bottom of the file:

```python
TEMPLATES = TemplateRegistry()
for _name, _anchors in _TIER1.items():
    TEMPLATES.register_dict(_name, _anchors, tier=1)
```

### Acceptance check

```bash
python3 -c "
from jazzx_sdk.tools.templates import TEMPLATES
assert TEMPLATES.tier_of('10-k') == 1
assert TEMPLATES.tier_of('financial-statements') == 1
assert TEMPLATES.tier_of('unknown-doc-type') == 3
print('PASS')
"
```

---

## Change 3 - Online fallback registry (`fallback_sources.py`)

### Why

For Tier-1 documents that arrive as Tier-4 (rasterized), a canonical digital version often
exists online. Fetching from the authoritative source bypasses DocIntel entirely and
produces a more reliable result with cleaner provenance.

### New file: `jazzx_sdk/tools/fallback_sources.py`

```python
"""
Online fallback source registry for document types.

When a document is unreadable (rasterized/binary) and has a known document type,
the fallback registry is checked before falling through to DocIntel. If an online
source can supply the canonical digital version, DocIntel is bypassed.

Sources are keyed by the same document-type slugs used in the template registry
(e.g. "10-k", "10-q"). SDK ships tier-1 sources (EDGAR). Pack authors register
additional sources at bring-up.

This is not a cache or a data product - it is a retrieval fallback. Each fetch is
scoped to the case that triggered it; the result is stored in that case's fabric
Evidence, not in a shared store.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class FallbackNotAvailable(Exception):
    """Raised when an online fallback cannot be attempted (missing metadata, fetch failed)."""


@dataclass(frozen=True)
class FallbackResult:
    """The outcome of a successful online fallback fetch."""
    markdown: str
    source_url: str
    document_type: str
    provenance: dict  # arbitrary key-value pairs for Evidence metadata


class OnlineFallbackSource(ABC):
    """Base class for a document-type-specific online retrieval strategy.

    SDK ships EdgarFallbackSource for "10-k" and "10-q".
    Pack authors subclass this for domain-specific sources and register at bring-up.
    """

    @property
    @abstractmethod
    def document_type(self) -> str:
        """Document-type slug - must match the template registry key (e.g. "10-k")."""
        ...

    @abstractmethod
    def can_fetch(self, metadata: dict) -> bool:
        """Return True if enough context exists in metadata to attempt a fetch.

        metadata keys that callers typically supply:
          filename (str): original filename, may contain ticker/CIK clues
          ticker (str): borrower ticker symbol if known
          cik (str): SEC CIK if known
          period (str): fiscal period if known (e.g. "2025-01-03")
        """
        ...

    @abstractmethod
    def fetch(self, metadata: dict) -> FallbackResult:
        """Fetch the canonical digital version and return markdown + provenance.

        Raises FallbackNotAvailable if the fetch cannot be completed.
        """
        ...


class FallbackSourceRegistry:
    """Registry of online fallback sources keyed by document-type slug."""

    def __init__(self) -> None:
        self._sources: dict[str, OnlineFallbackSource] = {}

    def register(self, source: OnlineFallbackSource) -> None:
        """Register a fallback source. Overwrites any existing source for the same type."""
        self._sources[source.document_type.lower()] = source

    def get(self, document_type: str) -> OnlineFallbackSource | None:
        return self._sources.get(document_type.lower())

    def has(self, document_type: str) -> bool:
        return document_type.lower() in self._sources

    def registered_types(self) -> list[str]:
        return sorted(self._sources)


# ---------------------------------------------------------------------------
# Tier-1 SDK source: SEC EDGAR (10-K and 10-Q)
# ---------------------------------------------------------------------------

class EdgarFallbackSource(OnlineFallbackSource):
    """Fetch a 10-K or 10-Q from SEC EDGAR given a ticker in metadata.

    Wraps jazzx_sdk.tools.filings.fetch_10k / the EDGAR submission API.
    Caller must supply metadata["ticker"] or metadata["cik"].

    The fetched HTML is converted to markdown via the standard conversion
    layer (HTML path - no DocIntel). The result includes the EDGAR archive
    URL in provenance so the Evidence object carries an auditable source link.
    """

    def __init__(self, form: str = "10-K", *, dest_dir: str = "/tmp/japes_edgar_cache") -> None:
        self._form = form.upper()
        self._dest_dir = dest_dir

    @property
    def document_type(self) -> str:
        return "10-k" if self._form == "10-K" else "10-q"

    def can_fetch(self, metadata: dict) -> bool:
        return bool(metadata.get("ticker") or metadata.get("cik"))

    def fetch(self, metadata: dict) -> FallbackResult:
        import re
        from jazzx_sdk.tools.filings import (
            DEFAULT_USER_AGENT, _get_json, _TICKERS_URL, _SUBMISSIONS_URL,
            cik_for_ticker, latest_filing, filing_document_url,
        )
        from jazzx_sdk.tools.conversion import convert_document

        ticker = metadata.get("ticker")
        cik = metadata.get("cik")

        try:
            if not cik:
                tickers_json = _get_json(_TICKERS_URL, DEFAULT_USER_AGENT)
                cik = cik_for_ticker(tickers_json, ticker)

            submissions = _get_json(
                _SUBMISSIONS_URL.format(cik=cik), DEFAULT_USER_AGENT
            )
            filing = latest_filing(submissions, form=self._form)
            url = filing_document_url(cik, filing["accession"], filing["primary_document"])

            # Fetch the HTML filing and convert via the standard HTML path (no DocIntel).
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as resp:
                html_bytes = resp.read()

            import tempfile, os
            suffix = ".htm"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(html_bytes)
                tmp_path = tmp.name

            try:
                markdown = convert_document(tmp_path)
            finally:
                os.unlink(tmp_path)

            return FallbackResult(
                markdown=markdown,
                source_url=url,
                document_type=self.document_type,
                provenance={
                    "source": "sec_edgar",
                    "form": self._form,
                    "ticker": ticker,
                    "cik": cik,
                    "filing_date": filing.get("filing_date"),
                    "accession": filing.get("accession"),
                    "edgar_url": url,
                },
            )
        except Exception as exc:
            raise FallbackNotAvailable(
                f"EDGAR fetch failed for {ticker or cik} ({self._form}): {exc}"
            ) from exc


# Module-level default registry - SDK tier-1 sources pre-registered.
FALLBACK_SOURCES = FallbackSourceRegistry()
FALLBACK_SOURCES.register(EdgarFallbackSource(form="10-K"))
FALLBACK_SOURCES.register(EdgarFallbackSource(form="10-Q"))
```

### Acceptance check

```bash
python3 -c "
from jazzx_sdk.tools.fallback_sources import FALLBACK_SOURCES, FallbackNotAvailable
assert FALLBACK_SOURCES.has('10-k')
assert FALLBACK_SOURCES.has('10-q')
assert not FALLBACK_SOURCES.has('rent-roll')
src = FALLBACK_SOURCES.get('10-k')
assert src.can_fetch({'ticker': 'YETI'})
assert not src.can_fetch({})
print('PASS')
"
```

---

## Change 4 - `convert_with_fallback` in `conversion.py`

### Why

This is the routing entry point that stitches changes 1-3 together. Callers that want
tier-aware routing call this instead of `convert_document`. The existing `convert_document`
is unchanged.

### What to add in `jazzx_sdk/tools/conversion.py`

```python
@dataclass
class ConversionResult:
    """Outcome of convert_with_fallback - markdown plus provenance."""
    markdown: str
    method: str          # "direct" | "online_fallback" | "docintel"
    tier: int            # 1-4 as determined at conversion time
    document_type: str   # classified label or "unknown"
    provenance: dict     # source-specific metadata for Evidence


def convert_with_fallback(
    file_path: str,
    *,
    metadata: dict | None = None,
    taxonomy: list | None = None,
    di_provider: "DocumentIntelligenceProvider | None" = None,
    fallback_registry: "Any | None" = None,
) -> "ConversionResult":
    """Tier-aware document conversion with online fallback before DocIntel.

    Resolution order:
      1. Attempt direct conversion (readable document - Tiers 1, 2, 3).
         On success: classify to determine tier; return ConversionResult.
      2. If unreadable: check fallback_registry for this document type.
         Classify from filename/metadata first (no LLM, no text needed).
         If a fallback source exists and can_fetch: fetch online, convert HTML.
         Return ConversionResult with method="online_fallback".
      3. If no fallback or fetch fails: invoke di_provider (DocIntel).
         On success: reclassify the resulting markdown; assign tier.
         Return ConversionResult with method="docintel".

    Args:
        file_path: Path to the source document.
        metadata: Caller-supplied context (filename, ticker, cik, period, ...).
                  filename defaults to Path(file_path).name if not supplied.
        taxonomy: List of DocClass/str/dict for classification. Defaults to
                  the SDK template registry's registered types.
        di_provider: Provider for scanned PDFs. Defaults to LocalMarkdownStubProvider.
        fallback_registry: FallbackSourceRegistry to consult. Defaults to
                           jazzx_sdk.tools.fallback_sources.FALLBACK_SOURCES.

    Returns:
        ConversionResult with markdown, method, tier, document_type, provenance.

    Raises:
        DocumentConversionError: if all three paths fail.
    """
    from pathlib import Path
    from jazzx_sdk.tools.classify import _filename_heuristic, DocClass, _normalize
    from jazzx_sdk.tools.templates import TEMPLATES

    path = Path(file_path)
    meta = dict(metadata or {})
    if "filename" not in meta:
        meta["filename"] = path.name

    # Build taxonomy from template registry if not supplied.
    if taxonomy is None:
        taxonomy = [DocClass(label=name) for name in TEMPLATES.list()]

    classes = _normalize(taxonomy)

    # --- Classify from filename alone (no LLM, no file read needed) ---
    classification = _filename_heuristic(meta["filename"], classes)
    doc_type = classification.label if classification else "unknown"

    # --- Step 1: try direct conversion ---
    try:
        markdown = convert_document(file_path, require_readable=True)
        tier = TEMPLATES.tier_of(doc_type) if doc_type != "unknown" else 3
        return ConversionResult(
            markdown=markdown,
            method="direct",
            tier=tier,
            document_type=doc_type,
            provenance={"source": "local_file", "path": str(path)},
        )
    except DocumentNotReadableError:
        pass  # fall through to tier-2 and tier-4 paths

    # --- Step 2: online fallback ---
    if fallback_registry is None:
        from jazzx_sdk.tools.fallback_sources import FALLBACK_SOURCES
        fallback_registry = FALLBACK_SOURCES

    if doc_type != "unknown" and fallback_registry.has(doc_type):
        source = fallback_registry.get(doc_type)
        if source.can_fetch(meta):
            try:
                from jazzx_sdk.tools.fallback_sources import FallbackNotAvailable
                result = source.fetch(meta)
                tier = TEMPLATES.tier_of(doc_type)
                return ConversionResult(
                    markdown=result.markdown,
                    method="online_fallback",
                    tier=tier,
                    document_type=doc_type,
                    provenance=result.provenance,
                )
            except Exception:
                pass  # fallback failed - proceed to DocIntel

    # --- Step 3: DocIntel ---
    provider = di_provider or LocalMarkdownStubProvider()
    try:
        markdown = provider.convert(file_path)
    except Exception as exc:
        raise DocumentConversionError(
            f"All conversion paths failed for '{path.name}': {exc}"
        ) from exc

    # After DocIntel, reclassify from content if filename gave nothing.
    if doc_type == "unknown" and markdown:
        hit = _filename_heuristic(meta["filename"], classes)
        doc_type = hit.label if hit else "unknown"

    tier = TEMPLATES.tier_of(doc_type) if doc_type != "unknown" else 4
    return ConversionResult(
        markdown=markdown,
        method="docintel",
        tier=tier,
        document_type=doc_type,
        provenance={
            "source": "docintel",
            "provider": type(provider).__name__,
            "path": str(path),
        },
    )
```

### Acceptance check (requires no network - uses LocalMarkdownStubProvider)

```bash
python3 -c "
import tempfile, pathlib
from jazzx_sdk.tools.conversion import convert_with_fallback, ConversionResult

# Readable HTML file - should route direct.
with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as f:
    f.write('<html><body><p>Test</p></body></html>')
    tmp = f.name

result = convert_with_fallback(tmp, metadata={'filename': 'YETI 10-K 2025.html'})
assert result.method == 'direct', result.method
assert result.document_type == '10-k', result.document_type
assert result.tier == 1, result.tier

import os; os.unlink(tmp)
print('PASS')
"
```

---

## Change 5 - Exports in `tools/__init__.py`

Add to the import block:

```python
from jazzx_sdk.tools.conversion import ConversionResult, convert_with_fallback
from jazzx_sdk.tools.fallback_sources import (
    FALLBACK_SOURCES,
    EdgarFallbackSource,
    FallbackNotAvailable,
    FallbackResult,
    FallbackSourceRegistry,
    OnlineFallbackSource,
)
```

Add to `__all__`:

```python
    # Tier-aware conversion with online fallback (v1.9.x)
    "ConversionResult",
    "convert_with_fallback",
    "FALLBACK_SOURCES",
    "OnlineFallbackSource",
    "FallbackSourceRegistry",
    "FallbackNotAvailable",
    "FallbackResult",
    "EdgarFallbackSource",
```

---

## What this does NOT change

- `convert_document` signature or behavior - unchanged
- `classify_document` LLM path - unchanged (heuristic fires first; LLM is fallback)
- `ExtractionTemplate` mechanics - unchanged
- `extract.py` entry points - unchanged
- JACI pack code - no changes required; packs get the new behavior by calling
  `convert_with_fallback` instead of `convert_document` at their document intake point
- Existing `TEMPLATES` registrations - unchanged; tier defaults to 1 for existing SDK
  entries after the tier-param addition
- `BaseDocumentClassifier` / `DocumentClassifierRegistry` - unchanged

---

## File change table

| File | Type | Change |
|---|---|---|
| `jazzx_sdk/tools/classify.py` | Modify | Add `_FILENAME_PATTERNS`, `_filename_heuristic()`; wire into `classify_document` |
| `jazzx_sdk/tools/templates.py` | Modify | Add `tier` param to `register`/`register_dict`/`load_yaml`; add `tier_of()`; update tier-1 registrations |
| `jazzx_sdk/tools/fallback_sources.py` | New | `OnlineFallbackSource` ABC, `FallbackSourceRegistry`, `FallbackResult`, `FallbackNotAvailable`, `EdgarFallbackSource`, module-level `FALLBACK_SOURCES` |
| `jazzx_sdk/tools/conversion.py` | Modify | Add `ConversionResult` dataclass, `convert_with_fallback()` function |
| `jazzx_sdk/tools/__init__.py` | Modify | Export new public symbols |

---

## Notes for implementation

**`_filename_heuristic` is pure** - no I/O, no imports beyond `re`. Keep it that way.
It must be importable in the `convert_with_fallback` path before any file read occurs.

**Tier-of-unknown is 3 for readable, 4 for DocIntel output.** The distinction matters
for provenance but does not affect extraction behavior downstream.

**EDGAR fetch uses a temp file then deletes it** - the markdown is what gets stored,
not the HTML. The temp file is an implementation detail of the conversion path.

**`TemplateRegistry.list()`** - check if this method exists; if the base `NamedRegistry`
uses a different name, adjust `convert_with_fallback` accordingly. The intent is to get
all registered template names for default taxonomy construction.

**Pack bring-up pattern** (for JACI doc authors, no code change needed now):

```python
# In pack initialization (e.g. jaci/scenarios/.../pack.py)
from jazzx_sdk.tools.fallback_sources import FALLBACK_SOURCES, OnlineFallbackSource

class NaicSerrfSource(OnlineFallbackSource):
    document_type = "insurance-rate-filing"
    def can_fetch(self, metadata): return bool(metadata.get("serff_id"))
    def fetch(self, metadata): ...

FALLBACK_SOURCES.register(NaicSerrfSource())

# Template registry for lender-specific docs
from jazzx_sdk.tools.templates import TEMPLATES
TEMPLATES.load_yaml("config/doc_templates.yaml", tier=2)
```

---

## Suggested test additions

File: `tests/test_doc_tier_routing.py`

- `test_filename_heuristic_10k` - various 10-K filename patterns
- `test_filename_heuristic_no_match` - unrecognized filename returns None
- `test_filename_heuristic_taxonomy_filter` - label not in taxonomy returns None
- `test_templates_tier_of` - SDK templates are tier 1, unknown is 3
- `test_fallback_registry_register_and_get`
- `test_edgar_source_can_fetch` - with and without ticker
- `test_convert_with_fallback_direct_readable` - HTML file routes direct
- `test_convert_with_fallback_docintel_stub` - scanned PDF routes to LocalMarkdownStubProvider

---

## Implementation notes for Claude Code

These notes are here so this plan is self-contained. Read them before writing any code.

### `TemplateRegistry.list()` does not exist - use `names()`

`TemplateRegistry` extends `NamedRegistry` from `jazzx_sdk/_registry.py`. The method
that returns all registered keys is `names()`, not `list()`. In `convert_with_fallback`,
where the plan says `TEMPLATES.list()`, write `TEMPLATES.names()` instead.

```python
# Correct:
taxonomy = [DocClass(label=name) for name in TEMPLATES.names()]
```

### `EdgarFallbackSource.fetch()` does not use `fetch_10k`

`jazzx_sdk/tools/filings.fetch_10k` writes the HTML filing to a `dest_dir` on disk and
returns the local path. The fallback path does not want a persistent file - it wants
markdown in memory scoped to the current conversion call. That is why `fetch()` in
`EdgarFallbackSource` uses the internal helpers (`_get_json`, `_TICKERS_URL`,
`_SUBMISSIONS_URL`, `filing_document_url`) directly, fetches the HTML into a temp file,
calls `convert_document` on it, then deletes the temp file. The markdown - not the HTML -
is what gets returned and eventually stored in the fabric.

Do not refactor this to reuse `fetch_10k`. The on-disk caching behavior of `fetch_10k`
conflicts with the scoped-to-case intent of the fallback path.

### `ConversionResult.provenance` must flow to fabric `Evidence` - but not in this plan

This plan stops at the SDK boundary. The `provenance` dict on `ConversionResult` carries
everything needed to construct an auditable `Evidence` object: source (local vs. EDGAR vs.
DocIntel), URL if online, provider class name, ticker/CIK/accession if applicable.

The wire-up from `ConversionResult.provenance` into the pack's `Evidence` object happens
at the document intake step in the conductor (JACI side, not JAPES). That is a separate
plan. For now, `provenance` is populated correctly by this plan; the conductor is
responsible for consuming it. Do not add any fabric or Evidence imports to
`jazzx_sdk/tools/conversion.py` - the conversion layer must remain fabric-agnostic.

### `convert_with_fallback` is additive - `convert_document` is unchanged

Do not modify `convert_document`. `convert_with_fallback` is a new function that calls
`convert_document` internally. Any existing JACI or JAPES code that calls
`convert_document` continues to work exactly as before. The new function is opt-in.

### `_filename_heuristic` must be importable before any file I/O

Keep `_filename_heuristic` a pure function with no imports beyond `re` (already in
stdlib). It is called inside `convert_with_fallback` before any file read, and it is
also called from `classify_document` before the LLM. If it acquires any lazy imports,
the import-before-read contract breaks. Do not add any imports inside it.

### `_normalize` in `classify.py` is already defined - do not duplicate it

`convert_with_fallback` calls `_filename_heuristic` which needs `DocClass` instances.
Import `_normalize` from `classify.py` (it is already there) rather than re-implementing
the taxonomy normalization in `conversion.py`.

### Tier assignment for `convert_with_fallback` direct path when doc type is unknown

If filename heuristic returns nothing and the document is readable, tier defaults to 3
(borrower-supplied variable structure). This is intentional - an unrecognized readable
document is Tier 3 by definition. Do not invoke the LLM to resolve the tier at
conversion time; classification can happen downstream when the content is needed.

### EDGAR rate limit - 10 requests per second

`EdgarFallbackSource.fetch()` makes two HTTP calls: one for `company_tickers.json` (only
if CIK not already in metadata) and one for the filing HTML. Both use `DEFAULT_USER_AGENT`
from `filings.py`. No additional rate-limit handling is needed in this plan - the fallback
is called once per document, not in bulk. If batch scenarios arise later, a rate limiter
between calls is the right addition, not here.

### Do not add `tier` to `TemplateRegistry.__init__` params

The `_tiers` dict is an internal implementation detail of `TemplateRegistry`. It is not
a constructor parameter. The tier for each template is set at `register` / `register_dict`
/ `load_yaml` call time. The `TEMPLATES` singleton is constructed once at module level;
the tier-1 templates are registered immediately after with `tier=1` explicitly. Do not
change the `TemplateRegistry()` constructor signature.

### `load_yaml` default tier is 2, not 1

YAML-loaded templates come from pack bring-up, making them Tier 2 by default. The `tier`
param on `load_yaml` allows a pack to override if needed (e.g. `tier=1` for a pack that
extends the SDK standard set), but the default must be 2. Do not change this default.

---

## End-to-end trace for a rasterized 10-K (for verification)

This is the primary scenario this plan enables. Walk through it manually after
implementation to confirm all pieces connect.

1. Intake receives `"YETI FY 2025 SEC 10-K_1.3.2026.pdf"` (rasterized - no text layer).
2. `convert_with_fallback(file_path, metadata={"ticker": "YETI"})` is called.
3. `_filename_heuristic("YETI FY 2025 SEC 10-K_1.3.2026.pdf", ...)` matches `10-k`,
   confidence 0.95.
4. `convert_document(..., require_readable=True)` raises `DocumentNotReadableError`
   (PyMuPDF detects no text layer).
5. `FALLBACK_SOURCES.has("10-k")` is True. `EdgarFallbackSource.can_fetch({"ticker": "YETI"})`
   is True.
6. EDGAR fetch: resolves CIK for YETI, fetches latest 10-K submission, downloads the
   iXBRL HTML filing, converts to markdown via the HTML conversion path.
7. Returns `ConversionResult(method="online_fallback", tier=1, document_type="10-k",
   provenance={"source": "sec_edgar", "ticker": "YETI", "edgar_url": "...", ...})`.
8. DocIntel is never called.
9. The conductor stores the markdown in fabric Evidence with provenance metadata.
   Subsequent runs of the same case find the cached Evidence and skip conversion entirely.

Expected `ConversionResult` fields after step 7:
```python
result.method == "online_fallback"
result.tier == 1
result.document_type == "10-k"
result.provenance["source"] == "sec_edgar"
result.provenance["ticker"] == "YETI"
"edgar_url" in result.provenance
"filing_date" in result.provenance
```
