# jazzx_sdk subpackage interiors — 2.4

**Owner:** Virendra Mehta
**Status:** ✅ **Phase 6 LANDED** (see §14 for what was verified and what still needs running on a 3.11+ box). Phases 7–12 outstanding. Audited against the tree *after* the 2.3 root refactor landed.
**Target release:** 2.4
**Predecessor:** `REFACTOR-2.3-sdk-layout.md` — Phases 0–4 landed; the root went 34 → 22 modules.
**Scope:** module placement *inside* subpackages, plus facade closure and status-marking of staged capability. One deletion. No behaviour change except where noted.

> **Read §10 before acting on anything here.** This SDK deliberately ships capability ahead of demand — `macer` and `juno` are currently KH-client-only consumers — so a module with no importers is more likely staged than dead. An earlier draft of this plan got that wrong.

> Note: this repo's convention appears to be `docs/plans/` (a symlink outside the repo). This file is in `docs/` because that path isn't writable from where it was drafted — move it if you want it alongside the others.

---

## 1. Verdict

The 2.3 refactor fixed the root. It did not fix the package, because **the clutter was never only at the root** — and the previous plan asserted "the subpackages are sound" on the basis of tree shape without opening them. That was wrong.

Post-refactor flat-module counts:

| Directory | Flat `.py` | Size | Verdict |
|---|---|---|---|
| `tools/` | 24 (+`processors/`) | 255 KB / 7,676 LOC | **Worse than the root ever was.** Real structure hiding inside. |
| `agents/interactive/` | 18 | 154 KB | **Flat is correct** — hub-and-spoke. Fix the facade instead. |
| `evaluation/` | 18 (+5 subdirs) | 128 KB | Mostly right. One subpackage never got made. |
| `fabric/canonical/` | 16 | `store.py` alone is 1,596 LOC | Flat is right; **`store.py` is 13-fold copy-paste.** |
| `llm/` | 15 (+`providers/`) | — | Flat is correct. But 267 LOC of dead code. |
| `conductor/` | 11 | 1,436 LOC | One real grouping, near-zero blast radius. |
| root | 22 | — | Done. |

The headline: **`tools/` is 24 flat modules and 255 KB — larger and flatter than the root was before 2.3.** Its import graph is one dense 11-module cluster plus 13 modules with *zero* intra-package edges, and it contains three distinguishable docstring dialects — three authors' intents in one namespace.

The single highest-value change in this plan is not a regroup at all: `fabric/canonical/store.py` is 13 copy-pasted classes that collapse to ~250 LOC behind one generic base.

---

## 2. Method: close the facade before you move the files

The audits produced one generalizable rule, and it predicts the cost of every item below. **A regroup costs whatever its package's `__init__.py` fails to re-export.** Consumers reaching a package through its root are insulated from internal moves; consumers pinned to full submodule paths are not.

Measured facade quality, and the resulting cost:

| Package | Facade | Production full-path pins | Regroup cost |
|---|---|---|---|
| `conductor/` | **complete** — 34/34 public names, only the documented `_db` omission | **1** (`fabric/canonical/condition_evaluator.py:18`) | Cheapest in the package |
| `evaluation/` | **exact** — 106 names, zero drift, guardrail-tested | 2 | Cheap; cost is ~30 *test* pins |
| `tools/` | near-complete — 23 of 24 modules, ~120 names | 5 | Cheap for production, ~24 test files |
| `fabric/canonical/` | 116 names, one real gap (`Predicate`) | **70** vs 4 root imports | **Expensive** — don't regroup |
| `llm/` | **33 names, large gaps** — all of `providers/`, all cost math, all of `model_identity` | 15 internal + 4 external | Close the gaps *first* |
| `agents/interactive/` | **incomplete** — `router`, `scope`, `knowledge` invisible from root | 15 | Fix the facade *instead of* moving |

⚠️ **The corollary, learned the hard way: a low importer count is not evidence of deadness.** This SDK deliberately ships capability ahead of demand — `macer` and `juno` currently use japes only for KH access, so whole subsystems are staged and waiting. An audit that sorts modules by "who imports this" cannot tell staged capability from rot, and will confidently propose deleting the former. §10 gives the rule for telling them apart, and it is a documentation rule, not a code one.

Two consequences worth acting on directly:

- **`llm/`'s facade is worse than the root package's.** Six cost/identity functions are re-exported from `jazzx_sdk/__init__.py` but *not* from `jazzx_sdk.llm` — so the top-level package is a more complete cost facade than the cost package. That is why external consumers pin `jazzx_sdk.llm.cost`. Closing the gap (§7.4) lets them migrate to the facade *before* any file moves, which de-risks a later `cost/` grouping to nearly nothing.
- **`agents/interactive/`'s missing exports are the reason production code pins submodules.** `manifest/spec_binding.py` reaches into `.interactive.scope` twice (lines 125, 143) purely because there is no root path. Adding ~8 names to `__all__` converts production pins into free root imports without touching a single file location.

---

## 3. `tools/` — the big one

### 3.1 Evidence for structure

The grouping below is not invented; every boundary is drawn from an existing import edge or an existing docstring cross-reference.

- **One dense cluster:** `conversion` → `extraction`/`extract` → `classify`/`split`, with `templates` and `fallback_sources` woven in. 11 modules with mutual edges and a documented design contract ("Keep conversion faithful; push interpretation downstream" — motivated by a named past failure: *"an over-eager 'conversion' that summarized a filing silently discarded most of its content"*).
- **Thirteen modules with zero intra-package importers.** They are in this directory by naming, not by coupling.
- **Three docstring dialects:** the *"Universal X tools … SDK-agnostic functions that domain packs can wrap"* boilerplate (`ontology`, `policy`, `documents`, `knowledge_graph`); the *"Migrated into JAPES in v0.6.x — platform-level capability"* boilerplate (`discovery`, `workflow`); and the faithful-conversion contract dialect (the document chain).

### 3.2 Target layout

```
tools/
├── __init__.py              # facade — absorbs the moves, stays ~120 names
├── documents/               # the one true cluster
│   ├── conversion.py  extraction.py  extract.py  templates.py
│   ├── classify.py    classifiers.py  split.py    fallback_sources.py
│   ├── local.py             ← the local-file half of today's documents.py
│   ├── chunking.py          ← ChunkingConfig/DocumentChunker/load_chunking_config
│   ├── processors/          (unchanged, nested)
│   └── providers/
│       ├── base.py          ← the DocumentIntelligenceProvider ABC from conversion.py
│       ├── azure.py         ← docintel_azure.py
│       └── stub.py          ← LocalStubProvider
├── knowledge_hub/           # identical shape, identical clients.KnowledgeHubLike dep
│   ├── ontology.py  policy.py  knowledge_graph.py
│   └── documents.py         ← the KH half of today's documents.py
├── platform/                # both "migrated into JAPES v0.6.x"
│   └── discovery.py  workflow.py
└── agent/                   # zero intra-package edges, zero jazzx_sdk imports
    └── grounding.py  tool_compression.py  dir_tools.py
```

### 3.3 `documents.py` is two modules in one file, and its docstring admits it

1,020 lines, self-described as **"1. LLM-Callable Tools (for agent use)"** (4 async KH functions: `read_document`, `search_documents`, `list_documents`, `get_document_chunks`) versus **"2. Operational Utilities (for handler/conductor use)"** (`read_local_file`, `read_from_url`, `chunk_document`, `search_local_files`, `list_local_files`, `save_local_file`, plus the chunking machinery and HTML helpers). The KH half belongs with `ontology`/`policy`; the local half with `conversion`/`processors`; the chunking config is a third thing.

⚠️ **This does not contradict the Unified Documents ruling** (ARCHITECTURE.md:554–555, *"not a separate `documents/` package; there is no `jazzx_sdk.documents`"*). That ruling forbids a **top-level** `jazzx_sdk.documents` and insists the pipeline live under `tools/`. This plan keeps it under `tools/` — as `tools/documents/`. The ruling's substance (organise by operation, not by source location; source-agnostic processing) is preserved.

### 3.4 Two defects to fix while in there

**A seam violation.** `conversion.py` imports two helpers out of `documents.py`, one of them private:
```python
from jazzx_sdk.tools.documents import strip_hidden_elements
from jazzx_sdk.tools.documents import _extract_text_from_html
```
HTML-to-text helpers living in the KH-document module and being imported *by* the conversion router is backwards — and `conversion.py` also owns its own `_html_to_markdown`. Two overlapping HTML paths, one crossing a boundary into a private name. Consolidate into `documents/local.py` or `documents/_html.py`.

**Two undocumented entry points for the same operation — RESOLVED: `conversion.convert_document()` is canonical.**
`documents.read_local_file()` goes through `processors.DocumentProcessor` (the coordinator; dict-returning,
`status`/`processor_used`, 3 file types: pdf/txt/json). `conversion.convert_document()` bypasses the
coordinator and instantiates `processors.pdf.SimplePDFProcessor` directly (str-returning, markdown-faithful,
7 file types: md/txt/html/docx/xlsx/xlsm/pdf, with scanned-PDF→DocIntel escalation and a tiered fallback
system built on top via `convert_with_fallback`). Checked real callers, not just shape: `read_local_file`
has **zero** callers anywhere in japes (prod or test) — only its own docstring example — and exactly **one**
straggler in jaci (`commercial_lending/pipeline.py:79`). `convert_document` has 2 real japes production
callers (`fallback_sources.py`, `agents/document/agent.py`) and **7** real jaci callers across
ci_spread/insurance_diligence/commercial_lending/portfolio_monitoring/cre_underwriting — including
jaci's own `commercial_lending/docintel.py`, which wraps *this* function as `_sdk_convert_document`, while
its sibling `pipeline.py` in the same package still calls `read_local_file` — the exact live inconsistency
this section predicted. **Rule:** `convert_document` is the canonical local-document-read entry point;
`read_local_file`/`DocumentProcessor` is legacy and narrower. Don't migrate jaci's `pipeline.py` blindly as
part of this refactor — it relies on `read_local_file`'s checked-status dict shape, and switching to
`convert_document`'s exception-based contract is a deliberate behavior change for jaci to make on its own,
not a mechanical import fix.

### 3.5 Evict four modules from `tools/`

Per the decision to keep SEC handling in the SDK rather than push it to a pack:

| Module | → | Why |
|---|---|---|
| `financial.py` | `finance/metrics.py` | **Inverted dependency.** `finance/__init__.py` currently imports its own leaf formulas *up* from `tools/`: *"`Financials` / `credit_metrics` / `working_capital_days` — derived metrics (re-exported from `jazzx_sdk.tools.financial`)"*. Pure, dependency-free, one intra-`tools/` importer (`filings.py`). |
| `filings.py` | `finance/filings.py` | Flatly domain-specific — `"SEC 10-K processing"`, hardcoded `sec.gov` URLs, `DEFAULT_USER_AGENT = "jazzx-sdk filings (contact: ops@jazzx.ai)"`. Stays in the SDK as a platform capability (same call as Flowable), but not in a *generic tools* namespace. |
| `assessment.py` | `fabric/assessment.py` | Not generic tooling at all — builds the `Policy → Evidence → Decision → Trace → Outcome` lineage and imports four `fabric.canonical` modules. Fabric plumbing. |
| `base_registry.py` | beside the evidence layer | `BaseToolRegistry` — evidence-type→connector dispatch with circuit breaker and retry. **Zero** intra-`tools/` importers; reaches into `fabric.canonical` and `modes.schemas`. |

⚠️ **Untangle before moving `filings.py`.** There is a live chain `conversion.py → fallback_sources.py → filings.py → financial.py`, so the *generic conversion router* currently reaches into SEC-specific credit ingestion. `fallback_sources.py`'s ABC/registry is clean; it just ships `EdgarFallbackSource` as a tier-1 default and lazily imports `filings`. Keep the registry in `documents/`, move `EdgarFallbackSource` to `finance/` and register it from there.

**Judgement call — RESOLVED: `ratio_evaluator.py` stays in `tools/` whole, not split, not moved.**
Checked real callers first: `evaluate_covenant_policy` has **4** real jaci callers (`cre_underwriting/
{ui/demo_page.py, ui/property_case_page.py, conductor.py}`, `ci_spread/ui/demo_page.py`) plus
`assessment.py` (leaving to `fabric/`); the pure math (`evaluate_ratio`/`RatioDirection`/`run_sensitivity`)
has its own real jaci caller (`cre_underwriting/conductor.py:344`) plus `fabric/canonical/
condition_evaluator.py` (itself moving out of `canonical/` per §4.3/Phase 8). **All jaci call sites import
via the `jazzx_sdk.tools` facade**, not the submodule path — so the facade re-export, not the physical
file location, is what insulates them; this was already low-risk either way.
The real question was never "which callers does it have" but "does it belong beside `assessment.py` in
`fabric/`" — and the answer is no, on the same test §4.4 applies to `refusal.py`/`values.py`:
`ratio_evaluator.py` has **zero** `fabric.canonical` imports (vs. `assessment.py`'s four), and its one
fabric-shaped surface, `evaluate_covenant_policy`, is *deliberately* duck-typed over
`policy.rules[].condition.{field,operator,value}` specifically to avoid a `fabric.canonical` import — its
own docstring says so. Moving it to `fabric/` would either preserve that duck-typing for no reason (it's
already inside fabric, importing `Policy` would cost nothing) or drop it for a trivial-but-unforced
simplification — neither is worth splitting one cohesive ratio-scoring file across two top-level areas,
when jaci's own call sites already treat `evaluate_ratio`/`RatioDirection`/`run_sensitivity`/
`evaluate_covenant_policy` as one family reached from one place. `assessment.py`'s existing
`from jazzx_sdk.tools.ratio_evaluator import evaluate_covenant_policy` (a submodule pin, not a facade
call) is unaffected by `assessment.py`'s own move — it's a cross-package import either way, and
`tools` importing nothing from `fabric` means `fabric` importing `tools` is directionally cycle-safe.

### 3.6 Delete `kg_store.py`

25 lines of pure re-export from `fabric.graph.triple`, carrying its own removal note (*"Removed in 1.6.7: `BaseKGStore`, `InMemoryKGStore`, `KnowledgeHubKGStore`"*). **Not imported by `tools/__init__.py`** — the facade pulls `Triple`/`format_triples_for_prompt`/`merge_subjects` straight from `fabric.graph.triple`. Its only two importers are `tests/test_kg_store.py` and `tests/test_fabric_kg_store.py` — the tests that test the stub. Delete both.

### 3.7 Cost

**Production full-path pins — 5, all one-line:**

| File:line | Pinned target |
|---|---|
| `agents/document/agent.py` | `tools.templates.TEMPLATES` |
| `experts/policy/default.py:467` | `tools.policy.read_policy` |
| `fabric/canonical/condition_evaluator.py` | `tools.ratio_evaluator` |
| `finance/__init__.py` | `tools.financial` |
| `finance/structure.py` | `tools.extraction.structure_region` |

Everything else in-SDK goes through the facade and absorbs the move for free: `documents` (from `connectors/rss_feed.py`, `connectors/web_search.py`), `conversion`/`classify`/`split` (from `agents/document/agent.py`), `base_registry` (from `jazzx_sdk/__init__.py`), `to_markdown` (from `agents/interactive/agent.py`).

**Test cost is the bulk of it:** ~24 of 33 test files bypass the facade, and several do so specifically to reach privates — `extract._chunk_by_chars`, `extract._merge_extractions`, `classify._filename_heuristic`, `documents._extract_text_from_html`, `kg_store._normalize_key`. That is a separate smell; fix the imports, don't preserve the private reach.

**One monkeypatch string to rewrite:** `"jazzx_sdk.tools.conversion.convert_document"`. The others (`"jazzx_sdk.tools.extract"`, `"jazzx_sdk.tools.split_document"`, `"jazzx_sdk.tools.write_segments"`) patch facade attributes and survive as long as the re-export names are preserved.

**Three facade gaps to close first** (currently forcing full-path imports): `templates.resolve_template`, `documents.strip_hidden_elements`, and `processors` — none is exported.

---

## 4. `fabric/canonical/` — highest value, and it is not a regroup

### 4.1 Do NOT group the schema modules

Twelve of the sixteen modules are 49–709 LOC leaves, each owning exactly one Schema Spec section or one registry, mean ~200 LOC. Six of them (`trace`, `evidence`, `decision`, `outcome`, `values`, `query`) import *nothing* from `jazzx_sdk` at all. Renesting into `models/` + `registries/` would rewrite **70 pinned production import edges and 39 test edges** to buy nothing — the modules are already correctly sized and discoverable.

### 4.2 Split `store.py` — 1,596 LOC of 13-fold copy-paste

The only file here with a genuine internal seam, and the seam is duplication rather than concerns.

Structure: 13 per-type store classes (~60–110 LOC each) — `PolicyStore`, `EvidenceStore`, `DecisionStore`, `TraceStore`, `OutcomeStore`, plus the 8 derived (`CaseContextStore` … `DomainPackStore`) — then a ~430-LOC `CanonicalObjectStore` facade with 13 property accessors, `find()`, `_put_routes`, a polymorphic `put()`, and ~30 flat delegation shims.

Every per-type store has the same five methods. A diff of `EvidenceStore` (L266–335) against `DecisionStore` (L336–403) yields **only** the class name, the docstring, the id attribute name, the `_ENTITY_TYPE_*` constant, and the model class in the lazy import. That is copy-paste, not design.

```
canonical/store/
├── __init__.py     # re-exports all 14 names — callers unaffected
├── _base.py        # one generic _EntityStore(entity_type, id_field, model_ref)
│                   #   ~1,100 LOC → ~250
├── core.py         # Policy/Evidence/Decision/Trace/Outcome specializations
│                   #   + the list_policies/latest/list extras
├── derived.py      # the 8 derived stores
└── facade.py       # CanonicalObjectStore, find, _find_registry,
                    #   required_indexes, _put_routes, delegation shims
```

**Why this is cheap:** only three production files reference `canonical.store` (`fabric/fabric.py:14,75` and `manifest/loader.py:24`), and `canonical/__init__.py` already re-exports all 14 store names — so `from jazzx_sdk.fabric.canonical import CanonicalObjectStore` keeps working untouched.

### 4.3 Move `condition_evaluator.py` out — it is the directory's only import cycle

Module-scope imports at lines 18–30: `conductor.pipeline`, `expressions.evaluate`, `canonical.policy`, `tools.ratio_evaluator`. And `canonical/__init__.py:35` imports it at module scope, so all of that is on the critical path of `import jazzx_sdk.fabric.canonical`.

Three problems, in ascending severity:

1. **It is neither schema nor persistence** — the only module in the directory that is neither, and the only one importing `conductor/`, `tools/`, and `expressions/`.
2. **It drags all of `tools/` and all of `conductor/` onto the canonical facade's critical path.** `contracts.py` already routes around this — its docstring says DTOs come from *"the canonical leaf model modules (not `fabric.canonical`, whose package init also pulls the KH-backed stores)"*. That stated reason is understated: the stores are lazy *inside* `store.py`; `condition_evaluator` is not.
3. **A real cycle:** `canonical/__init__` → `condition_evaluator` → `jazzx_sdk.expressions` (package init) → `expressions/evaluate.py:31–33` → `canonical.evidence` / `canonical.refusal` / `canonical.values`. It survives *only* because every back-edge targets a submodule, which resolves against a partially-initialised parent. **The day anything in `expressions/`, `tools/`, or `conductor/` writes `from jazzx_sdk.fabric.canonical import X` at module scope, `import jazzx_sdk.fabric.canonical` breaks with a partial-init ImportError.** Undocumented, untested.

Its only consumer is `experts/policy/default.py`. Move it beside that consumer or into a `fabric/policy_eval/` layer; keep the four names re-exported from `canonical/__init__` if compatibility matters. **Cost: 3 import edges.** Payoff: the inversion goes, the cycle goes, and the canonical facade becomes cheap enough that `contracts.py` no longer needs its workaround.

### 4.4 `refusal.py` and `values.py` are not canonical objects — decide whether to pay for it

Neither has a Schema Spec section, an entity type, a store, or a single intra-`canonical/` consumer (nothing but `__init__.py` imports either).

- **`refusal.py`** — *"a refusal is a successful, auditable outcome, never an exception"*. 28 inbound references, essentially all non-fabric: `server/app.py`, `agents/interactive/{agent,scope}.py`, `agents/document/{agent,pipeline}.py`, `statemachine/engine.py`, `automation/governed.py`, `finance/periods.py`, `expressions/evaluate.py`, `modes/operational/governor.py`, `authority/{context,resolver}.py`, `fabric/guidance/lifecycle.py`, `contracts.py`. It is a cross-cutting control-flow result type. `default_http_status` is HTTP transport concern sitting in the schema layer.
- **`values.py`** — `Money`, `DecimalValue`, `Rounding`. Never persisted standalone; used by `contracts.py`, `finance/{workbook,spread}.py`, `expressions/evaluate.py`. It is here because canonical objects *contain* these — by that logic `datetime` would live here too.

Correct homes are `jazzx_sdk/refusal.py` and `jazzx_sdk/values.py`, and both pass the P8 root test (zero `jazzx_sdk` imports, multiple subpackage consumers). **Cost: ~34 edge rewrites.** If you don't want to pay it in 2.4, the cheap alternative is to state the widened contract in `canonical/__init__.py`'s docstring — *"canonical objects plus the governance primitives they are built from: values, refusals, authority, profiles"* — so the next reader doesn't have to derive it. Be honest that this documents a compromise rather than a design.

Related but sound, do not touch: `canonical/authority.py` (the matrix **data model**) versus `jazzx_sdk/authority/` (the stateless **resolver** that consumes it) have zero class overlap and both docstrings explain the split deliberately. The only cost is two importable modules named `authority`, and `authority/context.py:28–31` carries a 5-line comment explaining why its canonical import is cycle-safe — a sign the collision costs reader effort, not that it's wrong.

### 4.5 Two one-line fixes

- **Export `Predicate` from `canonical/__init__.py`.** It is the documented type of `find(where=[...])` and is currently unreachable via the facade — the only real gap in 116 names. (`Locator` in `evidence.py` is a minor second; all three of its members are exported.)
- **Rename the four module-level `logger` globals to `_logger`** (`store`, `policy_registry`, `evidence_types`, `condition_evaluator`) — they leak into the public surface.

### 4.6 Naming notes, no action

`evidence.py` and `evidence_types.py` have **no import edge in either direction** — they are coupled only by the string in `CanonicalEvidenceObject.evidence_type: str`, unenforced. `evidence_types.py` is really `evidence_type_registry`, a sibling of `RefusalRegistry` and `policy_registry`, not of `evidence.py`. By contrast `policy.py` → `policy_registry.py` *is* cleanly layered (model → index).

---

## 5. `conductor/` — one grouping, near-zero blast radius

### 5.1 Correction: `engine.py` is not a hub

The 2.3 plan hypothesised hub-and-spoke here. The evidence is the opposite. `engine.py`'s only intra-package imports are `pipeline` (41) and `suspension_store` (42). It contains **no import of and no reference to** `fan_out`, `Checkpointer`, `EnsembleCollapse`, `run_replicated_segments`, or `StepRegistry` — the only hit is an untyped `registry: Any = None` constructor param whose `.get(step.impl)` is duck-typed. `engine.py` never names `StepRegistry`.

The actual graph is three disjoint chains plus an isolated leaf:

```
pipeline (leaf) ─┬─► base
                 ├─► step_registry
                 └─► engine ─► suspension_store ─► suspension_store_db
observability ───┬─► fanout ─► replication ─► ensemble
                 └─► engine
checkpoint  (isolated — zero in-package edges)
```

`engine` and the `fanout → replication → ensemble` chain **never touch each other.** The only thing binding them is `__init__.py`.

### 5.2 Target layout

```
conductor/
├── __init__.py           # facade unchanged — still 34 names
├── pipeline.py           # ⚠️ MUST NOT MOVE (see 5.3)
├── base.py               # Stage 1 ABC
├── engine.py             # Stage 2 executor
├── step_registry.py
├── checkpoint.py         # ⚠️ MUST NOT MOVE (see 5.4)
├── strategies/
│   ├── __init__.py
│   ├── fanout.py  replication.py  ensemble.py
├── suspension_store.py
└── suspension_store_db.py
```

`fanout`/`replication`/`ensemble` are a self-contained 324-LOC chain that `engine.py` never imports and that share one design-doc lineage (`reasoner-chassis-analysis.md` §4/P1, §4/P2). Grouping them makes visible the fact — currently invisible in a flat listing — that **these are not engine internals.**

**Blast radius: `conductor/__init__.py` lines 33–48, `replication.py:33`, `ensemble.py:24`. Nothing else, in any repo.** All 15 of jaci's consuming files go through the facade; `macer`, `juno`, `k9`, and `jazzx-assistant` reference `conductor` zero times.

### 5.3 `pipeline.py` must stay put

`fabric/canonical/condition_evaluator.py:18` pins `from jazzx_sdk.conductor.pipeline import ExecutionKind` at **module scope**, and `pipeline.py`'s zero-dependency leaf status (only `__future__`, `enum`, `pydantic`) is exactly what makes that import cheap — it avoids dragging in `observability`, `fabric.db`, and SQLAlchemy. Keep it a leaf; keep it at the package root.

Two related facts, both verified: `conductor/__init__.py` does import `.pipeline` (line 9) before `.engine` (17), but **that ordering is not load-bearing** — `engine.py:41`, `base.py:14`, and `step_registry.py:20` all import `jazzx_sdk.conductor.pipeline` by full path, which Python resolves regardless of statement order in `__init__.py`. And the reciprocal constraint is already documented: `observability/__init__.py:8` notes *"several `jazzx_sdk.conductor` modules import this package"* — so `observability` must stay free of `conductor`.

### 5.4 `checkpoint.py` must stay put, for an unobvious reason

Three external monkeypatch strings target it, all in jaci, all patching the **facade attribute**:

- `jaci/tests/unit/test_aml_conductor_engine.py:113` — `monkeypatch.setattr("jazzx_sdk.conductor.Checkpointer", …)`
- `jaci/tests/unit/test_cre_conductor_engine.py:125` — same
- `jaci/tests/unit/test_ci_conductor_engine.py:139` — same

Because they patch `jazzx_sdk.conductor.Checkpointer` rather than `jazzx_sdk.conductor.checkpoint.Checkpointer`, a move is safe **only if `Checkpointer` remains an attribute of `jazzx_sdk.conductor`**. It also belongs in neither group: it is not an execution strategy (zero engine coupling) and not a claim/fence store (wrong shape entirely — it writes versioned `CaseContext` via a duck-typed `canonical: Any`). Root of the package is correct for it. Its `fabric.canonical` coupling arguably means it's misfiled in `conductor/` at all, but that is a different question.

### 5.5 `base.py` vs `engine.py` — leave split

Not ABC-vs-impl: `ConductorEngine` is **not** a `BaseConductor` subclass and has no `describe()`. `base.py` (27 LOC) is Stage 1 — a single-abstract-method ABC subclassed by pack authors (five jaci scenario conductors do exactly this at module scope). `engine.py` (447 LOC) is Stage 2 — instantiated later and lazily by those same files. Merging would force every `describe()`-only subclass to import 447 LOC of execution machinery. 27 LOC is the right size for that boundary.

---

## 6. `evaluation/` — one subpackage, one rename

### 6.1 Create `evaluation/feedback/`

The only concern here that is a subpackage struggling to exist. Four modules, one shared prefix, 21 KB, a clean acyclic internal tree:

```
feedback_text.py (no deps) ◄── feedback.py:184 (lazy)
feedback.py ◄── feedback_db.py:21        (the FeedbackStore impl)
            ◄── feedback_quality.py:21   (render_feedback)
            ◄── optimization.py:103      (render_feedback)
```

No symbol is defined twice; roles are disjoint (types+ABC+in-process impl / one SQLAlchemy impl / 3 LLM ops / 2 pure string functions). Critically, **the group's only outbound edges are `render_feedback` and `Feedback`**, both of which a package `__init__.py` re-exports.

```
evaluation/feedback/
├── __init__.py     # re-exports; keeps `from jazzx_sdk.evaluation import Feedback` working
├── core.py         ← feedback.py
├── text.py         ← feedback_text.py
├── quality.py      ← feedback_quality.py
└── db.py           ← feedback_db.py     # preserves the _db convention as db.py
```

Cost: 7 test files plus one production lazy import at `agents/interactive/response.py:62`.

### 6.2 `reporter.py` → `reporters/base.py`

`reporter.py` is one ABC (`EvaluationReporter`, two methods) whose docstring says *"Implementations live outside jazzx_sdk."* `reporters/` holds `mlflow.py` plus an `__init__.py` that has **no imports and no `__all__`**, and `reporters/mlflow.py:29` imports *up* out of the directory to reach the ABC. `reporter` versus `reporters` differ by one character and mean ABC versus impls.

The directory's stated justification is real — *"each guards its own heavy dependency"*, i.e. mlflow import cost stays opt-in — but that justifies the directory, not the ABC's location. Move to `reporters/base.py`; have `reporters/__init__.py` re-export `EvaluationReporter` and continue **not** importing `mlflow`. Cost: `reporters/mlflow.py:29` and one line in `evaluation/__init__.py`; the one external consumer already uses the root.

### 6.3 Leave the rest flat, deliberately

- **The scoring axis** — `scorers.py`, `metrics.py`, `operational.py`, `trajectory.py`, `qa.py`, `templates.py`. Four distinct axes, correctly layered and cross-documented: `metrics.py` is the arithmetic below `scorers.py` (which comments *"Matches `jazzx_sdk.evaluation.metrics`' (actual, expected) argument order"* and bridges via `FunctionScorer.from_metric`); `operational.py` says it *"complement[s] the answer-quality scorers in `scorers.py`"* and reads a `CanonicalTrace` rather than an answer; `qa.py` is the domain-specialised chat/QA case. **Do not create `scoring/`** — `scorers.py` is imported by 7 things and burying it costs more than it saves.
- **The EVOLVE cluster** — `optimization.py`, `guidance_ab.py`, `prompt_registry.py`, `prompt_registry_db.py`. A real cluster, but only 27 KB, and the `_db` pair must stay adjacent.
- **`compounding.py` and `history.py` are islands.** There is exactly **one** import edge among `optimization`/`compounding`/`guidance_ab`/`history` — `guidance_ab.py:20` → `optimization.py`. `compounding.py` imports nothing from `jazzx_sdk` at all; `history.py` reads `harness/results.py` and is a sibling of `reporter.py` in spirit. Grouping these four would be grouping by narrative, not by dependency.

### 6.4 Why the subdirectory inconsistency exists

`golden_cases/`, `harness/`, `l3_review/`, `experiment/` are all well-formed (facade `__init__` with explicit `__all__`). `reporters/` is the outlier. The pattern is **chronological, not principled**: the four well-formed dirs date to Jun 21 – Jul 8; the flat feedback / prompt-registry / compounding / guidance_ab cluster is all Jul 14–24. The original design used directories; the later EVOLVE work was added flat. Worth writing down so the next addition follows the older convention.

Minor fixes: `l3_review/__init__.py`'s docstring lists a `ui_template` component that does not exist; `test_optimization.py:72` depends on the private `optimization._feedback_text`; `resolve_trace` lives in `operational.py` while `trajectory.py:13` reaches in for it (the one cross-edge in that group that isn't about scoring).

---

## 7. `llm/` — not a layout problem

**Flat is correct here, because** the modules resolve into two coherent hub-and-spoke clusters (`manager` ← `health`/`cost_tracker`/`providers`; `config` → `manager`) plus one clean data pipeline (`model_data.json` → `_model_data` → {`cost`, `model_cards`}, both keyed on `model_identity`), with a strictly acyclic graph, **zero `TYPE_CHECKING` blocks anywhere**, and every deferred import justified by an optional dependency. `providers/` is textbook: `base.py:45`'s `BaseProvider(ABC)` with three `@abstractmethod`s, and all four concretes subclass it.

Four independent actions, in priority order.

### 7.1 `routing.py` — pre-adoption capability, not dead code. Mark it and expose it.

An earlier draft of this plan recommended deleting this file. **That was wrong**, and the reasoning error is instructive enough to record: importer count cannot distinguish capability shipped ahead of demand from code that has rotted. See §10.

`routing.py` is 267 LOC of routing/retry policy — `TaskComplexity`, `RoutingStrategy`, `RetryStrategy`, `ModelTier`, `RetryConfig` — waiting on the large clients (`macer`, `juno`) to move beyond their current KH-client-only usage of japes. It is intentional.

But it is **invisible to the clients it is waiting for**, which is a real defect:

- None of its five classes is in `llm/__init__.py`'s `__all__`, and `llm/`'s facade is already the weakest in the package (§7.4). A client cannot adopt what it cannot import.
- It carries **no status marker**, unlike every other pre-adoption surface in this SDK (§10). Nothing in the file tells a reader it is deliberately unexercised, which is precisely why an audit flagged it for deletion.

**Actions:** add the five classes to `llm/__init__.py`'s `__all__`; add the status marker per §10.

⚠️ **And reconcile it with `manager.py` before anyone adopts it.** `manager.py` implements routing inline via a `task_routing: dict` constructor arg (lines 91, 126, 193–235) and does not reference `RoutingStrategy`. So there are currently **two routing models in one package** — one shipped and exercised, one declared and waiting. That is fine today and expensive later: the moment macer builds against `RoutingStrategy`, reconciling the two becomes a breaking change for a client rather than an internal edit. Decide now which is the intended surface, and either fold `manager`'s inline routing onto `routing.py`'s types or narrow `routing.py` to the part that genuinely extends what `manager` already does.

### 7.2 Rename `structured.py` → `structured_contract.py`

`structured.py` and `structured_call.py` share **no import edge in either direction** — they are opposite sides of one boundary, not layers.

- `structured.py` (314 LOC) is the **provider-side contract**: `StructuredMode`, `StructuredOutputError`, `IncompleteOutputError`, `schema_name`, `openai_structured`, `anthropic_tool`, `prompt_instruction`, `extract_json`, `validate`. All five provider modules import it; callers touch only the two exception types.
- `structured_call.py` (27 LOC, one function) is the **caller-side** entry point, and the more widely used: 11 lazy call sites across `agents/interactive/{registry,router}.py`, `evaluation/{feedback_quality,optimization,qa,scorers}.py`, `modes/evolve/curator.py`.

Rename, or move `structured.py` into `providers/` since its only real consumers are the five provider modules. Update 6 in-package edges plus `agents/openai_provider.py:312`, `tests/test_llm_truncation.py:21`, `tests/test_failures.py:323`.

### 7.3 Make `DbCostRecordStore` lazy

`llm/__init__.py:39` eagerly re-exports it, so `import jazzx_sdk.llm` unconditionally imports SQLAlchemy. This is **the only `_db` module in the repo that is eagerly re-exported**, and it directly contradicts the policy `conductor/suspension_store.py`'s own docstring states: *"imported lazily — not re-exported by `conductor/__init__.py`, so pulling in SQLAlchemy stays opt-in, same split as `jazzx_sdk.runs`."* `conductor/__init__.py` honours it; `llm/__init__.py` does not.

Nothing breaks either way (SQLAlchemy is a hard dep, `pyproject.toml:35`) — it is a tier-purity inconsistency. Fix it, or delete the "opt-in" claim from the conductor docstring so the two packages stop contradicting each other.

### 7.4 Close the facade gaps — do this first

`llm/__init__.py`'s `__all__` is 33 names and omits: all of `providers/`; all of `cost.py`'s math (`compute_cost`, `compute_cost_from_metrics`, `get_model_pricing`, `MODEL_PRICING`, `ModelPricing`, `DEFAULT_PRICING`, `compare_model_costs`, `suggest_flex_savings`, `estimate_monthly_cost`); all of `model_identity`; `structured.py`'s helpers; `cost_tracker.CostRecord` and `Budget`; all of `health.py`.

Six of those are re-exported from `jazzx_sdk/__init__.py:177–185`, so **the root package is a more complete cost facade than the cost package is.** Add them to `llm/__init__.py`. That lets the four external pinned `llm.cost` / `llm.model_identity` imports migrate to the facade *before* any file moves, which de-risks §7.5 to almost nothing.

### 7.5 `cost/` subpackage — defensible, but last

`cost.py` + `cost_tracker.py` + `cost_store.py` + `cost_store_db.py` is 1,245 LOC in a genuine one-directional chain, and the shared prefix already reads as a namespace. But `cost` is the most externally-pinned module in the package, so do it only after §7.4, and keep `jazzx_sdk.llm.cost` importable.

One clarification on the layering, since the prefix misleads: `cost_tracker.py` is **not** a layer over `cost.py`. It is the definition site of `CostRecord` (which both stores import) and owns budget enforcement; its only touch of `cost.py` is one lazy `get_model_pricing` call at line 480. So `cost_tracker` is the domain model and the stores are its persistence — an orthogonal concern to `cost.py`'s arithmetic, not a wrapper around it.

### 7.6 Two non-findings, recorded

- **`llm/sanitize.py` does not exist** — it was deleted in the 2.3 Phase 4 work. `llm/__init__.py:37` and `llm/manager.py:20` already import from the root `jazzx_sdk.sanitize`. Nothing to do.
- **`scripted.py` is not the `mock_services.py` problem.** It is a *published* keyless `LLMManager` implementation: exported from `llm/__init__.py:35` and `__all__`, referenced as a supported mode by production SDK docstrings (`agents/interactive/factory.py:7,33`, `agents/interactive/registry.py:220,269`, `evaluation/scorers.py:226`, `structured_call.py:5`), and used in **production code in another repo** (`jaci/src/jaci/scenarios/clinical_intake/session.py:37` and its demo page). Leave it.

---

## 8. `agents/interactive/` — flat is correct; fix the facade

**Flat is correct here, because** `agent.py` is a genuine hub: it imports **10 of the 17** siblings directly (`response`, `spec`, `stream_hooks`, `memory`, `inventory`, `registry`, `knowledge`, `router`, `responses_compaction`, `binding`). Of the other seven, two are adapters *above* it (`factory`, `optimize`, both importing `agent.py`), one is deliberately decoupled (`chat.py`, taking `agent: Any`), one is registered indirectly (`scope`, via `GuardrailRegistry`), and three are consumer-composed helpers `agent.py` never calls (`safety`, `source_builder`, and `inventory` shared with `spec`). The graph is an acyclic hub-and-spoke with maximum intra-package fan-in of 4 — there is no second hub.

Every candidate subgroup fails on evidence, not taste:

- **`memory/`** (`memory` + `binding` + `responses_compaction`) is the strongest candidate — 38 KB, internally coupled, and `binding.py` marks itself as *"the only SDK-aware layer"*. But `agent.py` imports all three directly, so the group would encapsulate nothing from anyone.
- **`safety/`** (`safety` + `scope` + the guardrails) would require splitting the 15 KB `registry.py`, since the stock guardrails live there alongside the skill/profile registries.
- **`runtime/`** (`stream_hooks` + `responses_compaction`) is 12 KB of two unrelated files.

### 8.1 The real problem: three modules are invisible from the root

`interactive/__init__.py` imports from 14 of 17 submodules; `__all__` is 59 names. Unreachable from the package root:

| Module | Missing | Consequence |
|---|---|---|
| `router.py` | `Router`, `register_router`, `resolve_router`, `intent_first` | entire module invisible |
| `scope.py` | `build_scope_guardrail`, `SCOPE_GUARDRAIL_NAME` | entire module invisible — **and this is why `manifest/spec_binding.py` pins it at lines 125 and 143** |
| `knowledge.py` | `resolve_knowledge` | entire module invisible |
| `inventory.py` | `build_inventory` | partial (the types are exported) |
| `responses_compaction.py` | `context_management_setting`, `model_settings_with_context_management` | partial |
| `chat.py` | the 6 step factories | partial; plausibly intentional |

Adding ~8 names converts several **production** submodule pins into free root imports. That is the fix here — not a directory.

### 8.2 Kill the `scope_guardrail` collision

`scope_guardrail` **is** exported — but it comes from `registry.py:253`, not from `scope.py`, whose function is `build_scope_guardrail`. The exported name and the module name point at different things. Rename one.

### 8.3 Two load-bearing edges to respect

`fabric/conversation_store.py:32` is a **module-scope** production import of `.interactive.memory` (`ConversationStore`) — `memory.py` is pinned by 4 production sites total. And `tests/test_binding.py` depends on the private `binding._to_responses_items` in three places. These break loudest under any move.

---

## 9. The `_db` convention — document it, don't touch it

The 2.3 audit initially read `_db` as the same smell as `events_domain`. It is not. Verified across **six** pairs, all identical in structure: the base file holds the abstraction plus an in-process reference impl; the `_db` file holds exactly one durable SQLAlchemy implementation and imports **only** from its sibling.

| Base | Abstraction | In-process impl | `_db` impl |
|---|---|---|---|
| `evaluation/prompt_registry.py` | `PromptRegistry(Protocol)` L36 | `InProcessPromptRegistry` L58 | `DbPromptRegistry` |
| `evaluation/feedback.py` | `FeedbackStore(ABC)` L130 | `InProcessFeedbackStore` L151 | `DbFeedbackStore` |
| `agents/definition_store.py` | `AgentDefinitionStore(Protocol)` L43 | `InProcessAgentDefinitionStore` L50 | `DbAgentDefinitionStore` |
| `conductor/suspension_store.py` | `SuspensionStore(Protocol)` L61 | `InProcessSuspensionStore` L71 | `DbSuspensionStore` |
| `runs/store.py` | `TurnRunStore(Protocol)` L23 | `InProcessTurnRunStore` L39 | `DbTurnRunStore` |
| `fabric/docs/manifest_store.py` | `MaterializeManifestStore(Protocol)` L33 | — | `DbMaterializeManifestStore` |
| `llm/cost_store.py` | `CostRecordStore(ABC)` | `InProcessCostRecordStore` | `DbCostRecordStore` |

The docstrings cross-reference each other as a family (*"Dogfoods `fabric.db` like `DbTurnRunStore`/`DbFeedbackStore`"*, *"mirrors `jazzx_sdk.runs.store_db.DbTurnRunStore`"*) and all repeat the same *"table DDL belongs in the consuming service's alembic"* contract. `conductor/suspension_store*` is the reference implementation, including the correctly-lazy, non-re-exported DB layer.

Proposed for ARCHITECTURE.md, following the P8 that landed at line 995:

> **P9 — Protocol and durable implementation split by file, not by package.**
> Where a store has both an abstraction and a durable backend, the base module owns the Protocol/ABC
> and an in-process reference implementation; a sibling `<name>_db.py` owns the single SQLAlchemy
> implementation and imports only from that base. The `_db` module is **not** re-exported from its
> package `__init__`, so importing the protocol never pulls SQLAlchemy. Table DDL belongs in the
> consuming service's migrations, never in the SDK.

That principle is currently honoured everywhere except `llm/__init__.py:39` (§7.3).

---

## 10. Pre-adoption capability — the convention already exists; apply it consistently

The SDK ships capability ahead of demand on purpose. `macer` and `juno` are today KH-client-only consumers; large parts of japes are staged for when they adopt the runtime, the conductor, and LLM routing properly. **This is a deliberate strategy and the audit process must not erode it.**

The SDK already has a good convention for this. Four places do it well:

| Site | Marker |
|---|---|
| `platform_catalog.py:47` | `# planned — defined in the IIF catalog but not yet implemented (stub raises)` |
| `experts/stubs.py` | `ExpertNotImplementedError` + *"Placeholder implementations for not-yet-implemented Experts"*; raises with a clear message naming expert and operation |
| `modes/` | `NotImplementedMode` / `ModeNotImplementedError`, catalog entry present, and the fallback prompt says so: *"This mode is not yet implemented. This is a catalog-only stub that raises ModeNotImplementedError when executed."* |
| `clients/mocks.py:1721` | `Note: Process client integration is not yet implemented.` — which is why `MockProcessClient` has no non-mock sibling |

The pattern in all four: **declared in the catalog/facade, marked in the docstring, and — where callable — failing with a typed error rather than silently.** A reader can tell the difference between "staged" and "abandoned" without asking anyone.

The problem is that this convention is applied unevenly. Surfaces that follow it read as intentional; surfaces that don't read as dead and get proposed for deletion.

**Unmarked and invisible from their facade — the actual defect list:**

| Surface | State | Why it reads as dead |
|---|---|---|
| `llm/routing.py` | 267 LOC, 5 classes | no marker, absent from `llm.__all__`, and `manager.py` implements the same concern differently (§7.1) |
| `evaluation/compounding.py` | imports nothing, imported only by `__init__` | fully duck-typed over `Sequence[Any]`, no marker |
| `tools/grounding.py`, `tool_compression.py`, `dir_tools.py` | zero intra-package edges, zero `jazzx_sdk` imports | no marker |
| `skills/` | 3 bundles against 13 modes; `base.py` only, no `default.py`, no `schemas.py` | asymmetry with `experts/` is unexplained |
| `l3_review/__init__.py` | docstring lists a `ui_template` component that doesn't exist | reads as stale rather than staged |

⚠️ I cannot tell from the code which of these are staged and which have genuinely been superseded — only the roadmap can. §11 Phase 6 assumes **staged** for all of them and marks rather than deletes, which is the safe default. Correct the list if any are actually retired.

Proposed for ARCHITECTURE.md, after P9:

> **P10 — Capability shipped ahead of demand is declared, marked, and reachable.**
> The SDK deliberately provides surfaces before any client exercises them. Such a surface must be
> (a) **reachable** — exported from its package `__init__`, because a client cannot adopt what it
> cannot import; (b) **marked** — a one-line status note in the module docstring naming what it is
> waiting on (a client, a service, a spec section); and (c) **fail-fast if callable but incomplete** —
> a typed `…NotImplementedError`, per `experts/stubs.py` and `modes.NotImplementedMode`.
>
> A low importer count is therefore never sufficient grounds to remove a module. Absence of a marker
> is a documentation bug, not evidence of death. Conversely, a staged surface that duplicates a
> shipped one must be reconciled *before* a client adopts it — afterwards it is a breaking change.

Applying (a) has a second benefit worth naming: it converts the facade from an inventory of what is *used* into an inventory of what is *offered*. Given that `macer` and `juno` adopting japes properly is the point, the facade is the adoption surface — and `llm/`'s facade currently hides the cost math, the providers, and all of routing (§7.4).

---

## 11. Phases

Ordered so that each phase reduces the cost of the next. Every phase leaves the tree green.

### Phase 6 — facade closure and status marking (no moves, no deletions except one shim)

The cheapest, highest-yield work, and it de-risks everything after it. Note this phase is now **additive** — the earlier draft's deletions were mostly wrong (§10).

1. **Mark the five unmarked pre-adoption surfaces** per P10 (§10): `llm/routing.py`, `evaluation/compounding.py`, `tools/{grounding,tool_compression,dir_tools}.py`, `skills/`, and fix `l3_review/__init__.py`'s phantom `ui_template` line. One docstring line each, naming what each is waiting on.
2. **Delete `tools/kg_store.py`** and its two tests (§3.6) — the one genuine removal, because it is *backward*-looking: its own docstring records `"Removed in 1.6.7: BaseKGStore, InMemoryKGStore, KnowledgeHubKGStore"`. ⚠️ Confirm it isn't staged for a KG-store return before deleting.
3. **Close `llm/__init__.py`** (§7.4) — add the cost math, `model_identity`, `providers`, `structured` helpers, **and `routing.py`'s five classes** (§7.1). This is the adoption surface macer and juno will build against.
4. **Close `agents/interactive/__init__.py`** (§8.1) — ~8 names; then convert `manifest/spec_binding.py:125,143` from submodule pins to root imports.
5. **Close `tools/__init__.py`** — export `templates.resolve_template`, `documents.strip_hidden_elements`, `processors`.
6. **Export `Predicate`** from `canonical/__init__.py`; rename the four `logger` globals to `_logger` (§4.5).
7. **Make `DbCostRecordStore` lazy** in `llm/__init__.py:39` (§7.3).
8. **Migrate the four external pinned imports** in `jaci` and `jazzx-assistant` from `llm.cost` / `llm.model_identity` to the `jazzx_sdk.llm` facade.

**Verify:** full suite; `-X importtime` diff against `docs/_importtime_baseline.txt` — expect SQLAlchemy to *leave* the `import jazzx_sdk.llm` path; `tests/test_import_boundary.py`'s `__all__` snapshot unchanged.

### Phase 7 — `fabric/canonical/store.py`

Split into `store/` with a generic `_EntityStore` (§4.2). Pure refactor, ~1,100 LOC → ~250, three production importers, facade absorbs it.

**Verify:** full suite; behavioural parity on all 13 object types — this is the one phase where a subtle behaviour change is plausible, so diff the generated SQL / KH calls per type before and after.

### Phase 8 — `condition_evaluator.py` out of `canonical/`

Move it beside `experts/policy/default.py` or into `fabric/policy_eval/` (§4.3). Then **add a regression test** asserting `import jazzx_sdk.fabric.canonical` pulls neither `jazzx_sdk.tools` nor `jazzx_sdk.conductor` — the cycle was undocumented and untested, and this is what stops it coming back.

**Verify:** the new test; confirm `contracts.py`'s leaf-module workaround is no longer needed (leave it in place regardless — it's harmless and P5-aligned).

### Phase 9 — `conductor/strategies/`

Three files, three edges (§5.2). Leave `pipeline.py` and `checkpoint.py` at the package root, for the reasons in §5.3 and §5.4.

**Verify:** full suite; `jazzx_sdk.conductor.Checkpointer` still resolves as a facade attribute (jaci patches it by string); the 34-name facade unchanged.

### Phase 10 — `evaluation/feedback/` and `reporters/base.py`

Both cheap; the facade is an exact 106-name match with a guardrail test (§6.1, §6.2).

**Verify:** `tests/test_evaluation/test_metrics.py:28`'s reachability guardrail still passes.

### Phase 11 — `tools/` regroup

The largest phase. Sequence within it:

1. Untangle `conversion → fallback_sources → filings` (§3.5) — this gates the eviction.
2. Evict `financial.py` → `finance/metrics.py`, fixing `finance/__init__.py`'s inverted import.
3. Evict `filings.py` → `finance/filings.py`; move `EdgarFallbackSource` with it and register it from `finance/`.
4. Evict `assessment.py` → `fabric/assessment.py`; decide `ratio_evaluator.py` at this point (§3.5).
5. Evict `base_registry.py` to the evidence layer.
6. Split `documents.py` into `documents/local.py` + `knowledge_hub/documents.py` + `documents/chunking.py` (§3.3); consolidate the duplicated HTML helpers (§3.4).
7. Create `documents/`, `knowledge_hub/`, `platform/`, `agent/`; move `docintel_azure.py` under `documents/providers/` beside the ABC and the stub.
8. Rewrite the 5 production pins and ~24 test files; fix the `"jazzx_sdk.tools.conversion.convert_document"` monkeypatch string.

**Verify:** full suite; `-X importtime` diff; grep that no test reaches a private that the reorg relocated.

### Phase 12 — documentation

1. Add **P9** (§9) and **P10** (§10) after the P8 that landed at ARCHITECTURE.md:995. P10 matters most: it is the principle whose absence caused this plan's worst error, and the one that protects the staged surfaces from the next audit.
   Also record the adoption context it depends on — that `macer` and `juno` are currently KH-client-only consumers and that large parts of the SDK are staged for their fuller adoption. Nothing in `docs/` says this today, which is why it has to be learned by asking.
2. Add the **deprecation policy** — this was Phase 5 item 4 of the 2.3 plan and did **not** land. The house pattern is already in `fabric/db/engine.py`'s postgres aliases (`warnings.warn(…, DeprecationWarning)` + delegate).
3. Write down the two undocumented rules this audit had to reverse-engineer: which local-text-extraction entry point to call (§3.4), and that `observability` must stay free of `conductor` while `conductor.pipeline` must stay a zero-dependency leaf (§5.3).
4. Update the Repository Structure tree again for the new subpackages.
5. Note in `evaluation/`'s README that new concerns follow the directory convention, not the flat one (§6.4).

### Deferred beyond 2.4

`refusal.py` / `values.py` → root primitives (§4.4, ~34 edges — decide explicitly rather than by drift) · `llm/cost/` subpackage (§7.5) · `structured.py` rename (§7.2) if it doesn't fit Phase 6 · `checkpoint.py`'s membership in `conductor/` at all (§5.4).

---

## 12. What this plan deliberately does not do

- **No `core/` or `foundation/` package for the root primitives.** Nine dependency-free modules in a directory named `foundation/` are *less* discoverable than nine at the root, not more — and it would recreate exactly the `utils/` grab-bag that 2.3 Phase 4 deleted. The P8 test that landed at ARCHITECTURE.md:995 already licenses them at root: they import nothing from `jazzx_sdk` and two or more subpackages import them.
- **No regroup of the `fabric/canonical/` schema modules** (§4.1) — 70 pinned production edges to buy nothing.
- **No regroup of `agents/interactive/`** (§8) — every candidate subgroup would hide code from nothing.
- **No `scoring/` in `evaluation/`** (§6.3) — burying a module with 7 importers costs more than it saves.
- **No change to the `_db` convention** (§9) — it is a documented seam, not a suffix workaround.
- **No removal of unexercised capability** (§10). `macer` and `juno` adopting japes beyond KH access is the point; the staged surfaces are assets, not debt. The only deletion left in this plan is `tools/kg_store.py`, and it qualifies because it looks *backward* — it documents its own 1.6.7 removals — not forward.

---

## 13. Phase 6 execution record

**Landed.** Facade sizes before → after:

| Package | `__all__` before | after |
|---|---|---|
| `llm` | 33 | **69** |
| `agents.interactive` | 59 | **69** |
| `tools` | ~113 | **116** |
| `fabric.canonical` | 116 | **117** |
| `evaluation` | 106 | 106 (already exact) |
| `conductor` | 34 | 34 (already complete) |

Changes made:

1. **Status markers** on the five staged surfaces (§10) — `llm/routing.py`, `evaluation/compounding.py`, `tools/{grounding,tool_compression,dir_tools}.py`, `skills/__init__.py`. Each names what it waits on. `l3_review/__init__.py`'s phantom `ui_template` line replaced with the reason a review UI isn't shipped (P1 — the consuming service owns its app shell).
2. **`llm/` facade closed** — cost arithmetic, `model_identity`, `BaseProvider`/`ProviderResult`, the `structured` contract helpers, `HealthMonitor`, `CostRecord`/`Budget`, and routing's five staged classes.
3. **`DbCostRecordStore` made lazy** (P9 consistency) alongside the four concrete providers, via PEP-562 `__getattr__`.
4. **`agents.interactive` facade closed** — `Router`/`register_router`/`resolve_router`/`intent_first`, `build_scope_guardrail`/`SCOPE_GUARDRAIL_NAME`, `resolve_knowledge`, `build_inventory`, the two `responses_compaction` model-settings helpers. The `scope_guardrail` vs `build_scope_guardrail` trap is now an explanatory comment at the export site rather than a rename — renaming would have broken the guardrail name `registry.py` registers.
5. **`manifest/spec_binding.py:125,143` converted** from submodule pins to root imports — the two production pins that existed only because those names were unreachable.
6. **`tools/` facade closed** — `processors`, `strip_hidden_elements`, `resolve_template`.
7. **`canonical/`** — `Predicate` exported; the four leaked `logger` globals renamed to `_logger` (35 references; no external consumers).
8. **`tools/kg_store.py` deleted.** Confirmed backward-looking first (*"Backward-compatible re-exports"*, *"Removed in 1.6.7"*, points at `fabric.graph` as the replacement, and not wired into `tools/__init__.py`). Its two test consumers were **retargeted, not deleted** — `test_kg_store.py` is 83 lines of real `Triple`/helper tests that belong on `fabric.graph.triple`; only the 3-line compat assertion went.

### 13.1 One defect found by running it, not by reading it

The first version of `llm/__init__.py`'s lazy block let `ImportError` escape `__getattr__`, so on a machine without the `anthropic` extra, `hasattr(jazzx_sdk.llm, "AnthropicProvider")` raised `ModuleNotFoundError` instead of returning `False` — breaking `dir()`, tab-completion, and any introspecting tooling.

Fixed by mirroring `observability/agent_hooks.py:294`'s `_MissingExtra`: a missing vendor SDK yields a placeholder that raises on **construction**, with the install command in the message. Attribute access stays safe. Verified — `hasattr(...)` is `True`, and `AnthropicProvider()` raises `ImportError: AnthropicProvider requires the 'anthropic' SDK. Install with: pip install anthropic`.

Worth generalising: P10(a) requires a staged surface to be *reachable*, and this is the mechanism that makes reachable-but-uninstalled safe rather than explosive.

### 13.2 Verification performed

| Check | Result |
|---|---|
| `tests/test_import_boundary.py` | **8/8 pass**, including the 2.3 guard-hardening test and the root `__all__` snapshot |
| Facade resolution, all six packages | **0 unresolvable names** in any `__all__` |
| Facade-adjacent suite (kg_store, templates, odata, llm_sanitize, cost_token_pricing, prompt_registry, interactive_scope/router, domain_pack_helper) | **51 pass** |
| evaluation, scorers, feedback, optimization, suspension_store, governed_values, llm_truncation, flex_tier, reasoning_effort | **140 pass** |
| tools suite (test_tools/, documents, ontology, policy, workflow, discovery) + streaming, channels | **135 pass, 2 skip** |
| interactive + manifest-binding (assistant_manifest_binding, assistant_primitives, binding, session_seam, conversation_masking, interactive_optimize/authorization, tool_stream_hooks) | **71 pass** |
| AST check — nothing in `__all__` unimported, nothing imported unexported, no duplicates | clean |

### 13.3 ⚠️ Not verified — run before merging

The environment this was executed in is **Python 3.10**; `pyproject.toml` requires `>=3.11`. Anything reaching `datetime.UTC` fails at import, blocking 13 test files including `test_consistency_enrichment.py`, `test_interactive_agent.py`, and every `fabric.canonical` mock test. A further group needs the private `knowledge_hub_client` / `kernel_client` distributions, unavailable there. The full-suite run also terminated at ~17% for an environmental reason not diagnosed.

**Run the full suite on 3.11+ with the private packages installed.** The `canonical/` `_logger` rename and the `tools/` facade additions are the two changes whose blast radius went least exercised — watch `test_canonical_find.py`, `test_fabric_canonical_mock.py`, and `test_mock_entity_validation.py`.

Still outstanding from Phase 6 as planned: **step 8, migrating the four external pinned imports** in `jaci` (`hooks.py:22`, `settings.py:13`) and `jazzx-assistant` (`handler.py:31`) onto the now-complete `jazzx_sdk.llm` facade. Nothing breaks without it — the submodule paths still work — but doing it is what de-risks a later `cost/` grouping (§7.5). `jazzx-assistant` is externally owned, so that one is a request rather than an edit.

---

## 14. Verification note (plan accuracy)

Every count, line number, and import edge above was read from the tree *after* the 2.3 refactor landed. Two things could not be verified from where this was drafted:

- `docs/plans/` and `docs/status/` are symlinks to `/Users/foo/src/research/.scratch/sang/ape/`, outside the repo — as is `CLAUDE.md`. If any of them documents module-placement conventions, those are unchecked.
- Whether `import agents` (openai-agents) *executes* `import uvicorn`. Dependency metadata supports it (`openai_agents` → `mcp>=1.19.0` → `uvicorn>=0.31.1`) but it was not confirmed at runtime. This matters only to the lazy-import discipline that 2.3 already put in place.

Two corrections to carry forward, both from the same root cause — inferring intent from structure instead of reading it.

1. The 2.3 plan's claim that *"the subpackages are sound"* was based on tree shape, not on reading them. It was wrong about `tools/`, wrong about `engine.py` being a hub in `conductor/`, and wrong to read `_db` as a smell.
2. An earlier draft of *this* plan called `llm/routing.py` "267 LOC of dead code" and recommended deleting it. It is staged capability awaiting `macer`/`juno` adoption. Importer count cannot distinguish staged from rotted, and the audit had no way to know because the file carries no marker — hence P10 (§10).

The two lessons, and they pull in different directions, which is the point: **§2 — measure the facade, because it determines the cost of moving anything. §10 — never infer deadness from the facade, because this SDK ships ahead of demand.** The facade tells you what a change costs; it does not tell you what a module is for.
