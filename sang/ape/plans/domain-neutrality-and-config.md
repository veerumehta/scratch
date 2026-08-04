# Domain neutrality in japes, and the domain-config mechanism

Companion to `reasoner-chassis-analysis.md` and `policy-ir-abstraction.md`. Audited against
`/Users/sangit/src/japes` `jazzx_sdk/` (SDK package only — tests/, examples/, docs/, ui/, common/,
.venv/ excluded).

---

## 0. The instinct is correct, and it's already violated once

You're asking for two things: (1) the SDK stays domain-neutral even where a client (MACER) hard-codes
"mortgage," and (2) the domain name flows through a **generated config**, read by the platform, rather
than being typed anywhere in code. Good news / bad news: the platform mostly already holds the line,
but it has one real violation, and the config mechanism you're describing **already exists in the
schema and is currently dead**. Both are fixable in the same change.

---

## 1. The one real violation: `jazzx_sdk/modes/catalog.py`

`MODE_REGISTRY` — the platform's single source of truth for "what modes exist," exported, read by
`get_mode_contract()` — has AML-specific literals baked into `ModeContract` fields that exist
precisely to be domain-neutral:

```python
"investigator": ModeContract(
    ...,
    canonical_consumes=["Alert"],       # domain term
    derived_object="case_file",         # domain term
),
"conductor": ModeContract(
    ...,
    derived_object="case_file",         # domain term
),
"narrator": ModeContract(
    ...,
    canonical_produces=["SARDraft"],    # AML/BSA term — Suspicious Activity Report
    derived_object="sar_draft",         # AML/BSA term
),
```

This is the mirror image of your mortgage concern, in the other domain: `SARDraft` and `sar_draft`
are AML vocabulary hard-coded into the mode catalog the same way `mortgage`/`loan`/`JTBD` are hard-coded
into MACER. The four genuinely unimplemented modes (`simulator`, `optimizer`, `influencer`,
`negotiator`) got this right — `canonical_produces=None` — which is the pattern the other three should
follow. `None` means "not yet mapped," and a pack supplies the concrete type.

Everywhere else checked — `fabric/canonical/*.py` (`PolicyType`, `PolicyScope`, `RuleAction`,
`DecisionType`, `OutcomeType`, `AttestationVerdict`, `ProvenanceType`, `ConfidenceTier`, all enum
values), `tools/ratio_evaluator.py`, `tools/financial.py`, `experts/catalog.py`, `skills/*/base.py` —
domain terms (mortgage, DSCR, LTV, KYC, SAR, typology, borrower, etc.) appear **only in docstrings and
`Field(description=...)` examples**, never as an enforced value, default, or enum member. That's the
right shape and the right place for a domain example to live. Two secondary items worth a look, lower
severity:

- `tools/filings.py` — `ticker` as a public parameter name, and a hard-coded system prompt
  (`"You are extracting a company's financials from its 10-K statements..."`). This is arguably
  inherent to "the tool wraps SEC EDGAR," which is an equities-specific data source by definition —
  less clear-cut than the mode catalog, worth a judgment call rather than an automatic fix.
- `finance/structure.py` — `STATEMENT_STRUCTURE_SYSTEM = "You are a credit analyst spreading financial
  statements..."`, a baked-in prompt framing the model as a credit analyst. Same category as above.
- Both are runtime-affecting (prompts, not comments), which is why they're listed as "worth a look"
  rather than "internal, ignore."

One thing already in the codebase worth citing as the pattern to imitate: `finance/workbook.py`'s own
docstring documents a caught-and-fixed leak — an earlier version named `SpreadPackage`, `MetricResult`,
`ValidationFinding`, `NormalizationAdjustment` as its inputs without noticing all four were JACI-defined
(a specific pack's) types, and *"japes cannot depend on jaci."* The fix was `Protocol` structural
typing (`GovernedLineItem`, `GovernedPackage`, ...) instead of importing the pack's concrete types.
That's the right general technique for this class of bug: type against the shape, not the pack.

---

## 2. The config mechanism you're asking for already exists — and is dead

`pack_manifest.yaml` / `PackManifestLoader` already declares exactly the fields you're describing:

```python
@property
def domain(self) -> str:            return self._manifest.get("domain", "")
@property
def segment(self) -> str:           return self._manifest.get("segment", "")
@property
def regulatory_context(self) -> list[str]:
    return self._manifest.get("regulatory_context", []) or []
```

`Pack` passes these through as its own `.domain` / `.segment` / `.regulatory_context`. This is
precisely "domain pack creation generates a config file with the domain name, read by the system" —
except right now, **nothing downstream reads it**. The canonical `DomainPack` object persisted to
Knowledge Hub has no `domain`/`segment`/`regulatory_context` fields at all (it has `domain_thesis`,
`scope_boundary`, but the manifest's three fields never get promoted into it). No policy resolution,
authority gating, certification check, or trace tagging consumes them. The test suite sets them on a
stub loader but never asserts on the values. Structurally, this is the same failure mode as
`ExecutionKind` in the conductor (declared, plumbed one hop, then dropped) — a pattern worth naming
once it's the second time you've found it, because it suggests the SDK's habit is to add the metadata
slot and defer wiring it, which is fine until three separate features are all waiting on the same wire.

So the fix isn't "add a domain config" — it's **wire the one that's already there**, and stop typing
the domain anywhere else.

---

## 3. What this means for the adjudication chassis specifically

Everywhere the chassis design (`reasoner-chassis-analysis.md`) or the policy-IR design
(`policy-ir-abstraction.md`) risked naming a domain, the fix is the same move: read it from
`Pack.domain` / `.segment` / `.regulatory_context` instead.

- **`AdjudicationAgentSpec` / `reasoner_agent.yaml`.** The example spec in `reasoner-chassis-analysis.md`
  §4.3 is pack data already — `name: mortgage-reasoner`, `regime.values: [fannie_mae, ...]` — so it's
  compliant by construction; the SDK classes reading it (`ReasonerAgentSpec.from_dir`, now
  `AdjudicationAgentSpec.from_dir`) never see the word "mortgage." Confirm on implementation: no
  `Literal["mortgage", "aml", ...]` anywhere in the chassis code, and no default obligation register,
  regime enum, or status vocabulary shipped in the SDK. Status enums (`PASS/FAIL/CONDITIONAL` vs.
  `CLOSE/ESCALATE/SAR_REFER`) are pack data, per §6 of the chassis doc — keep that.
- **Tracing tags.** `build_run_tags(operation=...)` and `spans_to_canonical_trace(mode_map=...)` should
  pull `domain=pack.domain` from the wired manifest field rather than a hard-coded tag, so the "Trace
  must not lie about what happened" concern from the mode-naming discussion extends to "must not lie
  about which domain ran," using the same field.
- **`ObligationSet` / `Policy` naming (P8 companion doc).** No change needed — `Rule`, `Policy`,
  `Condition` are already generic. Just don't let a `natural_language` evaluator's default prompt
  template default to mortgage examples the way `finance/structure.py`'s prompt defaults to "credit
  analyst." Write the fallback prompt generic; let the pack's `persona`/`skill_defs` supply the
  domain framing, the same way `InteractiveAgentSpec.persona` already works.
- **The Docker/CI naming problem, concretely.** `reasoner-chassis-analysis.md` Appendix A already
  flagged that japes CI hard-codes an `image_context` enum (`root` | `document_analyzer`) with no
  matrix strategy. If a mortgage-adjudication service is added the same way MACER was, the temptation
  is `image_context: mortgage_reasoner`. Don't — parameterize the workflow input as `pack_id` (already
  a manifest field) and let the Dockerfile take `pack_id` as a build arg. Otherwise the domain leaks
  into the one place hardest to lint: CI YAML.

---

## 4. Fix list

1. **`modes/catalog.py`** — change `investigator.canonical_consumes`, `investigator.derived_object`,
   `conductor.derived_object`, `narrator.canonical_produces`, `narrator.derived_object` to `None`,
   matching the pattern already used for `simulator`/`optimizer`/`influencer`/`negotiator`. A pack
   (JACI-AML) that wants `SARDraft`/`case_file` semantics for its own instantiation of these modes
   supplies them via its own contract binding — nothing in the SDK needs the literal.
2. **Wire `Pack.domain` / `.segment` / `.regulatory_context`** into at minimum: trace tags
   (`build_run_tags`, `spans_to_canonical_trace`), and — if it's meant to gate anything — the
   certification validator. If it's genuinely meant to stay descriptive-only, say so in the docstring
   explicitly (the way `ExecutionKind`'s docstring says "there is deliberately no stubbed/mock kind —
   that's a trace property, not a design property"), rather than leaving it ambiguous between "not
   wired yet" and "not supposed to be wired."
3. **Add a domain-neutrality lint**, in the style of the two existing structural-contract tests:
   - `tests/test_version_sync.py` is the model for "read structured data, assert equality" (it reads
     `pyproject.toml` via `tomllib` and compares to `jazzx_sdk.__version__`).
   - `tests/test_import_boundary.py` is the model for "spawn a subprocess, assert a set is empty" —
     the isolation technique matters if you want to catch *dynamic* leakage (an import pulling in a
     vocabulary module), not just static.
   - A naive string-grep test will false-positive on the `modes/schemas.py` and `skills/*/base.py`
     "Examples:" docstring blocks, which intentionally show AML/Mortgage/Healthcare side by side as a
     *positive* pattern (proof the schema is generic). The lint needs to be AST-based: walk
     `jazzx_sdk/` with `ast.parse`, and flag domain tokens only when they appear as `ast.Constant`
     values inside **enum member assignments, dict-literal values, or `Field(default=...)`** — not
     inside string literals that are docstrings or `description=` arguments.
   - Concrete first assertion this lint should make pass immediately after fix #1: every
     `ModeContract.canonical_produces` / `canonical_consumes` / `derived_object` value across
     `MODE_REGISTRY` is either `None` or drawn from an explicit allow-list of platform-canonical names
     (`Evidence`, `Decision`, `Policy`, `Trace`, `Outcome`, `Attestation`, `GovernorDecision`,
     `LoopStatus`, `EvaluationReport`, `SignalRoute`). That turns today's violation into tomorrow's
     regression test.

None of this blocks the adjudication chassis build sequence in `reasoner-chassis-analysis.md` — it's
a parallel, small fix (a few hours for #1 and #3; #2 is a design decision plus a half-day of wiring)
worth landing before or during Phase 1 (the SDK version upgrade), since Phase 1 already touches
`jazzx_sdk` version skew and is the natural place to also fix what's broken in the version you're
upgrading to.
