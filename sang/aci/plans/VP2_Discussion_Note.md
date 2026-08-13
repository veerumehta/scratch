# VP-2 spreading — discussion note

Companion to `VP2_Spreading_Demo_Companion.pptx`. **This is the material that should not be on
screen during the demo.** It is for the conversation after it, or before it with the small group.

Author: Claude (Cowork) for Virendra Mehta · 2026-08-09

---

## 1. Should spread be its own scenario?

**Short answer: it already is separate, at the layer that matters — and the KYC pattern is the one
to avoid, not to copy.**

The only KYC-as-shared-thing that exists today is `kyc_anthropic` reaching into the `kyc` package
for `KYCToolRegistry`, `KYCEvidenceRequest` and `kyc_schemas`. That is a cross-package Python
import: no manifest, no version, no declared dependency, no way for a pack to state that it needs
it. It works, and it does not compose.

The designed mechanism exists and spread already uses it. Each capability carries a
`capability.yaml` with `capability_id`, `version`, `register`, `step_impls` (each with `emits` and
an `execution` kind) and `depends_on`; `capabilities/registry.py` does manifest discovery and
dependency-closure resolution.

| Capability | Steps | Depends on |
|---|---|---|
| `document-intake` | `intake.ingest` (integration), `intake.classify` (deterministic) | — |
| `financial-spreading` | `spread.spread` (live), `spread.metrics` (deterministic) | `document-intake` |
| `credit-validation` | `credit.validate`, `credit.gate` (deterministic) | `financial-spreading` |
| `underwriting-decision` | none — publishes an API, human-only | `credit-validation`, `financial-spreading` |
| `commercial-lending` | none — pure aggregator | all four |

So a new pack is `depends_on: [document-intake, financial-spreading, …]`, not a fork. That is
exactly the "craft a new pack by pulling capabilities" direction, and it is already load-bearing
for CL.

**What is genuinely missing for a cleaner demo is the surface, not the capability.**
`ci_spread/ui/demo_page.py` is a monolith carrying credit analysis, the three demo acts, and the
spread phase together. A spread-only demo surface over the existing `financial-spreading`
capability is thin work — a page plus a registry entry. Splitting the *capability* is already done.

**Recommendation.** Don't restructure before the demo. Afterwards: (a) build the spread-only demo
surface, (b) give `insurance-diligence` and `kyc` capability manifests so they compose the same
way, (c) assemble one pack purely by `depends_on` as the proof.

**The honest caveat, if anyone probes.** The composition machinery is real, but no *second* pack has
been assembled through it yet. `underwriting-decision` is a manifest with no code by design.
`cl_of_core` and `cl_sp_core` are still scaffolds with dangling references — `CIPolicyExpert`
doesn't exist and the gold-case paths are missing. Spread proved the unit; assembly is unproven.

---

## 2. Real / staged / not built

Worth saying out loud before someone asks.

**Real and running.** Governed spread pipeline end-to-end on a real 10-K. `SpreadPackage` with
provenance on 100% of line items. 17 validation detectors; the four arithmetic controls are now
wired into the governed pipeline and set from a policy profile (fixed 2026-08-08/09, commits
`0b86788` and `5440ede`). Governed workbook export, risk-ranked review queue, maker-checker.
The RB reference case reproduces the analyst's LTM income-statement column exactly, `cit_ebitda ==
11810`.

**Staged for the demo.** Acts 2 and 3 of the demo arc are held pending real fixtures and two
detectors that don't exist (footnote-surfacing, cash-flow-gap). Ground truth is four keys plus a
30-row as-filed table that is rendered but never asserted. Per-cell confidence is a constant `0.98`
— which means the XF-2 refusal gate ("values below profile floor refuse admission") can never fire,
and four shipped features rank on a constant.

**Not built.** `OutputTemplate` and `TemplateFillAgent`. Induction from a customer workbook as a CLI
verb. `Skill.applies_to` on the SDK `Skill` model. Row-by-row spreading accuracy in the eval
harness. The two induced templates behind the demo are hand-derived from real customer files —
real inputs, but not machine output, and that distinction should not be blurred.

---

## 3. The three layers, and where the moat is

| Layer | What it holds | Should be |
|---|---|---|
| **SDK** (`jazzx_sdk`) | Canonical chain, conductor, state machine, finance schema/vocabulary/workbook, expression DSL, authority, evaluation, agents | Horizontal. Nothing lending-specific. |
| **Pack** (`config/packs`) | Chart of accounts, metric catalog, add-backs, reclassifications, spread templates, policies, playbooks, workbook layouts, per-customer skill overlays | **The moat.** Authored, versioned, certifiable. This is what compounds. |
| **jaci** (`src/jaci`) | Capability manifests and step registration, domain glue, demo surfaces, lending-specific detectors | Thin, and shrinking as SDK primitives land. |

The test of whether the split is real: a new segment should be pack data plus a capability
manifest, not a jaci fork. We are close on spread and not yet proven elsewhere.

Measured on the spread path (`src/jaci/capabilities/` + `src/jaci/scenarios/ci_spread/`,
2026-08-09): 67 distinct `jazzx_sdk` modules, 153 import sites, 43 of 59 files, 13,162 lines.

---

## 4. Asks and next steps

1. **Land the japes mode-chassis batch.** Uncommitted on `55d6e85`: `EvaluatorMode` migrated onto
   `ReasoningAgent`, `replicas` default corrected 3 → 1, `BaseMode` failing loud on a missing pack
   asset, the `modes/catalog.py` domain-neutrality fix. Version not yet bumped; the `BaseMode`
   change is breaking for a pack with a missing asset and should be labelled as such.
2. **Decide on the spread-only demo surface** — thin, and it is what makes the next demo clean.
3. **Capability manifests for insurance and KYC**, then assemble one pack by `depends_on` as proof.
4. **Confidence from `MatchKind`** — a few hours, deterministic, and it un-breaks XF-2. Do this
   before any replication work; the k=3 measurement says replication buys nothing on the one
   fixture anyone has run.
5. **`OutputTemplate` + fill agent**, delivering Wave 4b induction through it. 4b's own precondition
   ("prove the target schema by hand first") is now met twice, across two segments.

---

## 5. Open questions worth putting to the room

- Is the demo's job to show **spreading accuracy**, or to show **the operating model**? The
  artifacts support the second far better than the first, and the deck is built for the second.
- Do we want the RB case (real analyst workbook, C&I) or YETI (richest package, but its output
  format is PDF-only) as the flagship? Currently the code favours YETI and the evidence favours RB.
- How much of the "customer's own format" claim do we want to make before induction is a CLI verb
  rather than a hand-derivation?
