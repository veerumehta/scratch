# JAPES SDK Additions — CRE Domain Analysis Findings
*Author: Virendra Mehta*
*Date: June 2026*
*Derived from: Commercial Lending Mini-Workshop (April 2026), CRE Deep Dive (March 2026)*

---

## Context and Constraint

The Schema Specification v1.0 §11.2 freeze guidance is explicit:

> "Do not introduce new canonical objects. Do not introduce new derived objects beyond the eight already formalized."

This plan respects that constraint fully. Nothing here introduces a new canonical or derived object. All three workstreams below are either (a) sub-schema completions within existing objects, (b) utility infrastructure in the tools layer, or (c) domain pack usage work that belongs in JACI rather than JAPES.

---

## Finding 1 — `Depend` sub-schema is undefined on `CaseContext`

### Background

`CaseContext.pending_dependencies` is specified in Schema Spec v1.0 §7.1 as:

> `pending_dependencies | array[Depend] | Optional | External dependencies blocking progress (e.g., pending RFI, pending approval).`

The `Depend` type is referenced but its field structure is not defined in the spec. In the current `derived.py` implementation it is typed as `array[object]` — a plain dict with no enforced shape.

### Why this matters for CRE

The CRE underwriting workflow has three structurally distinct dependency types that all need to be tracked on a case:

- Conditions prior to closing (evidence-gated: appraisal, title, environmental, rent roll)
- Post-close conditions (time-gated: lease-up milestones, monthly reporting)
- Ongoing covenants (ratio-gated: DSCR, occupancy, debt yield testing on schedule)

Without a governed `Depend` shape, the CRE conductor cannot emit structured conditions that downstream stages (closing, servicing, portfolio monitoring) can reliably consume and test. The same gap exists for AML (pending RFI responses), KYC (outstanding document conditions), and mortgage (prior-to-doc conditions).

### Proposed addition — JAPES v1.5.x patch

Add `Depend` as a governed sub-schema on `CaseContext` in `jazzx_sdk/fabric/canonical/derived.py`.

```python
class DependencyStatus(str, Enum):
    OPEN = "open"
    SATISFIED = "satisfied"
    WAIVED = "waived"
    BREACHED = "breached"
    EXPIRED = "expired"

class DependencyType(str, Enum):
    EVIDENCE_REQUIRED = "evidence_required"      # blocking: must obtain before proceeding
    APPROVAL_REQUIRED = "approval_required"      # blocking: human or system approval gate
    CONDITION_PRECEDENT = "condition_precedent"  # closing-gate: must clear before funding
    POST_CLOSE = "post_close"                    # non-blocking at close; tracked post-fund
    ONGOING_COVENANT = "ongoing_covenant"        # recurring obligation; tested on schedule
    EXTERNAL_RESPONSE = "external_response"      # waiting on RFI, third-party, regulator

class Depend(BaseModel):
    dependency_id: str = Field(default_factory=lambda: f"dep_{uuid4()}")
    dependency_type: DependencyType
    description: str
    status: DependencyStatus = DependencyStatus.OPEN
    evidence_required: list[str] = Field(default_factory=list)  # evidence_type refs
    policy_refs: list[str] = Field(default_factory=list)        # governing policy_ids
    owner: str | None = None                                     # actor_id responsible
    due_date: datetime | None = None
    satisfied_by: str | None = None   # evidence_id or actor_id that closed it
    satisfied_at: datetime | None = None
    domain_extensions: dict[str, Any] = Field(default_factory=dict)
```

`CaseContext.pending_dependencies` type changes from `list[dict]` to `list[Depend]`.

### Scope

- File: `jazzx_sdk/fabric/canonical/derived.py`
- Export: add `Depend`, `DependencyStatus`, `DependencyType` to `__init__.py`
- Tests: add to `tests/test_canonical_derived.py`
- No schema spec recertification required - this completes an already-defined field

---

## Finding 2 — `RatioEvaluator` utility (tools layer)

### Background

Every regulated domain has mandatory ratio tests: DSCR, LTV, debt yield (CRE/lending); capital adequacy, reserve ratio (banking); loss rate, severity (insurance); FCCR, leverage (C&I). Currently each domain pack either (a) defers ratio computation to the LLM, creating hallucination risk, or (b) reimplements deterministic math locally with no shared pattern.

This is not a schema gap - it is a utility infrastructure gap in `jazzx_sdk/tools/`.

### Why this is genuinely universal

The computation pattern is identical across all domains: given a numerator, a denominator, a threshold, and a direction (>= or <=), compute the ratio, determine pass/fail, compute margin to threshold, and return a structured result that TraceStep can consume. The ratio *definitions* (what constitutes DSCR vs. capital adequacy vs. FCCR) live in the domain pack's policy config. The evaluator is pure math infrastructure.

### Proposed addition — JAPES v1.5.x

New file: `jazzx_sdk/tools/ratio_evaluator.py`

```python
class RatioDirection(str, Enum):
    AT_LEAST = ">="   # pass when ratio >= threshold (DSCR, coverage)
    AT_MOST = "<="    # pass when ratio <= threshold (LTV, leverage)

class RatioResult(BaseModel):
    ratio_name: str
    numerator: float
    denominator: float
    computed_value: float
    threshold: float
    direction: RatioDirection
    passed: bool
    margin: float        # distance from threshold; positive = passing headroom
    severity: str        # "pass" | "warning" | "breach"
    warning_buffer: float | None = None  # optional soft limit for warning zone
    domain_extensions: dict[str, Any] = Field(default_factory=dict)

def evaluate_ratio(
    ratio_name: str,
    numerator: float,
    denominator: float,
    threshold: float,
    direction: RatioDirection,
    warning_buffer: float | None = None,
) -> RatioResult:
    """
    Compute a ratio and evaluate it against a threshold.
    Domain-agnostic. Domain packs supply ratio definitions from policy config.
    
    Examples:
      CRE:  evaluate_ratio("DSCR", noi, debt_service, 1.25, AT_LEAST)
      C&I:  evaluate_ratio("leverage", total_debt, ebitda, 4.0, AT_MOST)
      Ins:  evaluate_ratio("loss_ratio", losses, premiums, 0.70, AT_MOST)
    """
    ...

def evaluate_ratios(ratio_specs: list[dict]) -> list[RatioResult]:
    """Batch evaluation. Each spec is a dict matching evaluate_ratio kwargs."""
    ...
```

**Stress extension** (same file or `ratio_stress.py`):

```python
def apply_shock(
    base_value: float,
    shock_pct: float,
    direction: str = "down",  # "up" | "down"
) -> float:
    """Apply a percentage shock to a base value. Direction-aware."""
    ...

def run_sensitivity(
    base_inputs: dict[str, float],
    shock_vector: dict[str, float],   # field_name -> shock_pct
    compute_fn: Callable[[dict], RatioResult],
) -> list[RatioResult]:
    """
    Run a sensitivity analysis over a shock vector.
    Domain packs supply compute_fn (wraps evaluate_ratio with their inputs).
    Returns one RatioResult per shocked scenario.
    """
    ...
```

### Domain pack usage pattern

```python
# In CREPolicyExpert.check_compliance():
from jazzx_sdk.tools.ratio_evaluator import evaluate_ratio, RatioDirection

dscr_result = evaluate_ratio(
    ratio_name="DSCR",
    numerator=loan_app.noi_stated,
    denominator=loan_app.annual_debt_service,
    threshold=policy_schedule.min_dscr,
    direction=RatioDirection.AT_LEAST,
    warning_buffer=0.05,  # warn when within 5pts of floor
)
ltv_result = evaluate_ratio(
    ratio_name="LTV",
    numerator=loan_app.loan_amount,
    denominator=loan_app.appraised_value,
    threshold=policy_schedule.max_ltv,
    direction=RatioDirection.AT_MOST,
)
```

The domain pack never reimplements the math. JAPES owns the computation pattern; the pack owns the thresholds (from its policy library).

### Scope

- File: `jazzx_sdk/tools/ratio_evaluator.py`
- Export: add to `jazzx_sdk/tools/__init__.py`
- Tests: `tests/test_tools_ratio_evaluator.py`
- No schema objects involved; pure utility

---

## Finding 3 — `BaseDocumentClassifier` pattern (tools layer)

### Background

The CRE RM's Assistant and Credit Analyst assistant both describe a universal document pipeline: split bundled uploads, classify by document type, extract key fields, validate completeness against a schema. The same pattern appears in AML (SWIFT messages, bank statements, corporate records), KYC (ID documents, corporate filings), and mortgage (income docs, appraisals, title commitments).

`jazzx_sdk/documents/` already handles acquire/chunk/transform. What is missing is a **classification registry** that domain packs can contribute typed classifiers to.

This follows exactly the same extensibility pattern as `BaseToolRegistry` and `ExpertRegistry`.

### Proposed addition — JAPES v1.5.x

New file: `jazzx_sdk/documents/classifiers.py`

```python
class DocumentClassificationResult(BaseModel):
    document_type: str            # domain-specific type slug
    confidence: float             # 0.0-1.0
    extracted_fields: dict[str, Any]
    missing_required_fields: list[str]
    completeness_passed: bool
    domain_extensions: dict[str, Any] = Field(default_factory=dict)

class BaseDocumentClassifier(ABC):
    """
    Base class for domain-specific document classifiers.
    Domain packs subclass this for each document type they handle.
    Register instances with DocumentClassifierRegistry.
    """

    @property
    @abstractmethod
    def document_type(self) -> str:
        """Stable slug identifying this document type (e.g. 'rent_roll', 'w2', 'sar')."""
        ...

    @property
    @abstractmethod
    def required_fields(self) -> list[str]:
        """Field names that must be present for completeness check to pass."""
        ...

    @abstractmethod
    def matches(self, raw_text: str, metadata: dict) -> float:
        """
        Return confidence 0.0-1.0 that raw_text is this document type.
        Classifier implementations may use heuristics, regex, or LLM routing.
        """
        ...

    @abstractmethod
    def extract(self, raw_text: str, metadata: dict) -> dict[str, Any]:
        """Extract structured fields from the document text."""
        ...

    def classify(self, raw_text: str, metadata: dict) -> DocumentClassificationResult:
        """Full classify + extract + validate pipeline. Not abstract; uses matches/extract."""
        confidence = self.matches(raw_text, metadata)
        fields = self.extract(raw_text, metadata) if confidence > 0.5 else {}
        missing = [f for f in self.required_fields if f not in fields or fields[f] is None]
        return DocumentClassificationResult(
            document_type=self.document_type,
            confidence=confidence,
            extracted_fields=fields,
            missing_required_fields=missing,
            completeness_passed=len(missing) == 0,
        )


class DocumentClassifierRegistry:
    """
    Registry of domain-specific document classifiers.
    Domain packs register their classifiers at pack initialization.
    Pattern mirrors BaseToolRegistry.
    """

    def __init__(self):
        self._classifiers: dict[str, BaseDocumentClassifier] = {}

    def register(self, classifier: BaseDocumentClassifier) -> None:
        self._classifiers[classifier.document_type] = classifier

    def classify(
        self,
        raw_text: str,
        metadata: dict,
        top_n: int = 1,
    ) -> list[DocumentClassificationResult]:
        """
        Run all registered classifiers and return top_n results by confidence.
        """
        results = [c.classify(raw_text, metadata) for c in self._classifiers.values()]
        return sorted(results, key=lambda r: r.confidence, reverse=True)[:top_n]

    def classify_by_type(
        self,
        document_type: str,
        raw_text: str,
        metadata: dict,
    ) -> DocumentClassificationResult:
        """Run a specific classifier by document_type slug."""
        if document_type not in self._classifiers:
            raise KeyError(f"No classifier registered for document_type '{document_type}'")
        return self._classifiers[document_type].classify(raw_text, metadata)
```

### Domain pack usage pattern

```python
# In jaci/src/jaci/scenarios/cre_underwriting/documents/classifiers.py:
from jazzx_sdk.documents.classifiers import BaseDocumentClassifier

class RentRollClassifier(BaseDocumentClassifier):
    @property
    def document_type(self) -> str:
        return "rent_roll"

    @property
    def required_fields(self) -> list[str]:
        return ["unit_count", "physical_occupancy", "avg_in_place_rent", "as_of_date"]

    def matches(self, raw_text, metadata) -> float:
        # heuristic: look for unit/rent/occupancy column headers
        ...

    def extract(self, raw_text, metadata) -> dict:
        # extract unit-level rent roll data
        ...
```

CRE pack registers: `RentRollClassifier`, `OperatingStatementClassifier`, `AppraisalClassifier`, `MarketStudyClassifier`, `SponsorFinancialsClassifier`.

AML pack registers: `SWIFTMessageClassifier`, `BankStatementClassifier`, `CorporateRegistryClassifier`.

The registry itself lives in JAPES and is shared infrastructure; the classifiers live in domain packs.

### Scope

- File: `jazzx_sdk/documents/classifiers.py`
- Export: add `BaseDocumentClassifier`, `DocumentClassifierRegistry`, `DocumentClassificationResult` to `jazzx_sdk/documents/__init__.py`
- Tests: `tests/test_documents_classifiers.py`
- No schema objects involved; pure extensibility infrastructure

---

## Finding 4 — CRE pack usage of existing derived objects (domain pack work, not JAPES)

The CRE domain docs reveal three derived objects that JACI's CRE scenario should be using but currently isn't. These are not JAPES SDK gaps - they are CRE domain pack wiring tasks.

**4a. Narrator should emit `Artifact` (type: `credit_memo`)**

The credit memo the Narrator mode produces is currently a plain string output. It should be emitted as a governed `Artifact` with `artifact_type="credit_memo"`, full `citations[]` back to each evidence object cited, `policy_refs[]` to the policy clauses that governed the structure, and `audience="credit_committee"`. This enables the audit trail the Underwriter Assistant positioning requires.

**4b. Governor conditions should populate `CaseContext.pending_dependencies`**

When the Governor emits conditions (prior-to-closing, post-close, ongoing covenants), these should be written as `Depend` objects on the `CaseContext.pending_dependencies` list. This makes the condition list machine-readable for downstream stages (closing, servicing) rather than embedded in a narrative string.

Dependency on Finding 1 above: needs the `Depend` sub-schema to be formalized first.

**4c. Stress testing should emit `ScenarioReport`**

When the Reasoner runs DSCR/LTV stress tests (occupancy shock, rate shock), the results should be emitted as a `ScenarioReport` linked to the `CanonicalDecision`. This is exactly what `ScenarioReport` was designed for - scenario analysis results with calibration history and decision linkage.

---

## Implementation order

| # | Item | Layer | Target version | Depends on |
|---|---|---|---|---|
| 1 | `Depend` sub-schema on `CaseContext` | JAPES SDK | v1.5.x patch | - |
| 2 | `RatioEvaluator` + `run_sensitivity` | JAPES SDK | v1.5.x | - |
| 3 | `BaseDocumentClassifier` + Registry | JAPES SDK | v1.5.x | - |
| 4a | CRE Narrator emits `Artifact` | JACI CRE pack | Post-1 | - |
| 4b | Governor conditions as `Depend` objects | JACI CRE pack | Post-1 | Item 1 |
| 4c | Stress output as `ScenarioReport` | JACI CRE pack | Post-2 | Item 2 |

Items 1, 2, 3 are independent and can be built in parallel. Items 4a-4c are domain pack tasks that unblock once the SDK additions land.

---

## What was explicitly ruled out

| Proposed item | Ruling | Reason |
|---|---|---|
| `ConditionRecord` new derived object | Rejected | Maps to `CaseContext.pending_dependencies` + `Depend` sub-schema. Freeze in §11.2 |
| Domain-specific financial calculators (DSCR formula, NOI normalization, T-12 spreading) | Domain pack only | CRE/lending-specific; not universal. Belongs in `jaci/scenarios/cre_underwriting/calculators.py` |
| CRE document type classifiers (rent roll, op statement, appraisal) | Domain pack only | CRE-specific format adapters. `BaseDocumentClassifier` base class is JAPES; classifiers are pack |
| `PipelineStageTimer` SLA tracker | Deferred | `CaseContext.sla` field already exists with deadline and aging thresholds. Extend that before adding new infrastructure |
| New canonical objects | Rejected | Schema Spec v1.0 §11.2 freeze. Recertification required |
| New derived objects beyond 8 | Rejected | Schema Spec v1.0 §11.2 freeze. Recertification required |
