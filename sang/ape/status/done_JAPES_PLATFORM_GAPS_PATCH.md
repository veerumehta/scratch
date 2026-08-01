# JAPES Patch -- Platform Gaps Surfaced by ci_spread Build

**Author:** Virendra Mehta
**Execute with:** Claude Code from `/Users/sangit/src/japes/`
**Scope:** Four targeted fixes. No new features, no schema additions. Additive/backward-compatible.
**Verify with:** Import smoke tests + the ci_spread integration test after each change.

---

## STATUS: EXECUTED -- shipped as japes 1.6.4 (5ee46cb)

All four changes are live. Plan smokes pass. One intentional divergence from spec in Change 3
-- see note below. The code is authoritative; this doc is retained for the record.

| Change | Plan spec | Shipped (1.6.4) | Status |
|---|---|---|---|
| 1 -- OpenAI token param | `_requires_completion_tokens_param` at module level | Exactly as specced (gpt-5/o1/o3/flex_ handled) | matches |
| 2 -- Context loop methods | 5 methods/props on base Context, TransactionContext untouched | All present, dual .status/.verifier_status, pending_dependencies via metadata.setdefault | matches |
| 3 -- registry execute() | `execute(self, request_obj) -> dict` | `execute(self, evidence_type: str, query_params=None) -> Evidence` | **diverged (intentional)** |
| 4 -- CanonicalTrace.for_pack() | factory with binding_id/deployment_id="pending" | Exactly as specced | matches |

**Change 3 divergence:** The plan specced `execute(request_obj) -> dict`. Shipped as
`execute(evidence_type: str, query_params=None) -> Evidence` because the SDK
`InvestigatorMode` emits `evidence_requests: list[str]` (bare type strings, no request
object), and callers need a canonical `Evidence` back (with `.data`/`.status`), not a raw
dict. Actual call site: `await self.tool_registry.execute(req, {"loan_id": ...})`.
The Change 3 smoke test in this doc would fail against the real signature -- ignore it.

**Follow-ups beyond the plan (also done in 0.7.2-0.7.3):**
- ci_spread updated post-patch: CIContext -> alias, for_pack, tools via base execute (0.7.2)
- CRE conductor fixed (0.7.3)
- AML, KYC, kyc_anthropic conductors fixed (0.7.3, squashed) -- plan only anticipated CRE

---

## Context

These four gaps were surfaced during the ci_spread conductor build. Each was worked around
2-3 times across AML/CRE/ci_spread, confirming they belong in the SDK rather than each
pack re-solving them.

**Important note on #2:** `schemas.py` now has `TransactionContext` which its own docstring
explicitly says covers C&I credit spread (`TransactionContext[LoanApplication, CreditDecision]`).
Before adding loop methods to base `Context`, confirm with a quick read of the existing
`TransactionContext` docstring that the split is still valid. The loop methods belong on
`Context` (for investigation/hypothesis-elimination loops). `TransactionContext` stays as-is
(no loop methods -- it's a single-pass shape).

---

## Change 1 -- OpenAI `max_tokens` fix (`jazzx_sdk/llm/providers/openai.py`)

**Problem:** Line ~213 in `run()` sets `"max_tokens": max_tokens` unconditionally. Newer
OpenAI models (gpt-5.x flex tier) require `max_completion_tokens` instead. This silently
breaks all conductor runs on those models.

**Fix:** Before building `api_params`, detect whether the model requires
`max_completion_tokens`:

```python
_COMPLETION_TOKENS_MODELS = {
    "o1", "o3", "o1-mini", "o3-mini",
}

def _requires_completion_tokens_param(model_name: str) -> bool:
    model_lower = model_name.lower()
    if model_lower in _COMPLETION_TOKENS_MODELS:
        return True
    if model_lower.startswith("flex_"):
        return _requires_completion_tokens_param(model_lower[5:])
    if model_lower.startswith("gpt-5"):
        return True
    return False
```

Then in `run()`:
```python
token_param = "max_completion_tokens" if _requires_completion_tokens_param(model) else "max_tokens"
api_params: dict[str, Any] = {
    "model": model,
    "messages": messages,
    "temperature": temperature,
    token_param: max_tokens,
    **kwargs,
}
```

**Test:**
```python
from jazzx_sdk.llm.providers.openai import _requires_completion_tokens_param
assert _requires_completion_tokens_param("gpt-5.4") == True
assert _requires_completion_tokens_param("flex_gpt-5.4") == True
assert _requires_completion_tokens_param("o1") == True
assert _requires_completion_tokens_param("gpt-4o") == False
print("Change 1 ok")
```

---

## Change 2 -- Context loop methods (`jazzx_sdk/modes/schemas.py`)

**Problem:** Base `Context` has the fields but no mutation methods. Every pack re-implements
the same four methods. AML and ci_spread re-implemented them locally; CRE didn't and was
latently broken.

**Fix:** Add to the `Context` class: `apply_hypothesis_update()`, `add_evidence()`,
`apply_verifier_report()`, `pending_evidence` (property), `pending_dependencies` (property).

See shipped code in `jazzx_sdk/modes/schemas.py` for the authoritative implementation.
Key design points:
- `apply_verifier_report()` handles both `.status` (generic Evidence) and `.verifier_status`
  (legacy AML EvidenceObject) via hasattr checks.
- `pending_dependencies` uses `metadata.setdefault("pending_dependencies", [])` to avoid
  adding a new typed field to the generic base.
- `TransactionContext` is untouched.

**Test:**
```python
from jazzx_sdk.modes.schemas import Context, EvidenceStatus

class _I: pass
ctx = Context(input=_I())
assert callable(getattr(ctx, "apply_hypothesis_update", None))
assert callable(getattr(ctx, "add_evidence", None))
assert callable(getattr(ctx, "apply_verifier_report", None))
assert isinstance(ctx.pending_evidence, list)
assert isinstance(ctx.pending_dependencies, list)
print("Change 2 ok")
```

---

## Change 3 -- BaseToolRegistry.execute() (`jazzx_sdk/tools/base_registry.py`)

**Plan spec (superseded):** `execute(self, request_obj) -> dict` -- accepts an
EvidenceRequest-like object.

**Shipped (authoritative):** `execute(self, evidence_type: str, query_params=None) -> Evidence`

The shipped signature was chosen because `InvestigatorMode` emits bare `evidence_type`
strings, not request objects, and callers need an `Evidence` canonical object back.
The `_find_tool_by_evidence_type()` helper does case-insensitive lookup.

Actual call site pattern:
```python
evidence = await self.tool_registry.execute(evidence_type, {"loan_id": loan_id})
```

**The smoke test in the original plan spec is stale -- do not run it.** See shipped code
for the correct signature and test.

---

## Change 4 -- CanonicalTrace.for_pack() (`jazzx_sdk/fabric/canonical/trace.py`)

**Problem:** `CanonicalTrace` has required fields (`pack_version`, `binding_id`,
`deployment_id`) that packs can't supply at construction time. Every pack either
subclasses with defaults or fails validation.

**Fix:** `CanonicalTrace.for_pack(workflow_id, case_id, pack_id, pack_version="dev",
binding_id="pending", deployment_id="pending", **kwargs)` classmethod.

**Test:**
```python
from jazzx_sdk.fabric.canonical.trace import CanonicalTrace

t = CanonicalTrace.for_pack("test-loop", "ctx_001", "test-pack")
assert t.binding_id == "pending"
assert t.status.value == "completed"
print("Change 4 ok")
```

---

## Post-patch: ci_spread and conductor fixes (all done)

- ci_spread CIContext thinned to alias (loop methods now on base Context)
- ci_spread conductor uses `CanonicalTrace.for_pack()`
- ci_spread tool registry calls `base.execute(evidence_type, params)` -- matches shipped sig
- CRE conductor: both latent bugs fixed (Context loop methods inherited, for_pack used)
- AML, KYC, kyc_anthropic: same drift fixed in same pass

---

## Smoke test sequence (reference -- all pass as of 1.6.4)

```bash
cd /Users/sangit/src/japes && source /Users/sangit/src/jaci/.venv/bin/activate

python -c "
from jazzx_sdk.llm.providers.openai import _requires_completion_tokens_param
assert _requires_completion_tokens_param('gpt-5.4') == True
assert _requires_completion_tokens_param('flex_gpt-5.4') == True
assert _requires_completion_tokens_param('o1') == True
assert _requires_completion_tokens_param('gpt-4o') == False
print('Change 1 ok')
"

python -c "
from jazzx_sdk.modes.schemas import Context
class _I: pass
ctx = Context(input=_I())
assert callable(getattr(ctx, 'apply_hypothesis_update', None))
assert isinstance(ctx.pending_evidence, list)
print('Change 2 ok')
"

# Change 3: use shipped signature, not plan spec
python -c "
from jazzx_sdk.tools.base_registry import BaseToolRegistry
import inspect
sig = inspect.signature(BaseToolRegistry.execute)
print('Change 3 shipped signature:', sig)
# Should show (self, evidence_type: str, query_params=None)
"

python -c "
from jazzx_sdk.fabric.canonical.trace import CanonicalTrace
t = CanonicalTrace.for_pack('test-loop', 'ctx_001', 'test-pack')
assert t.binding_id == 'pending'
print('Change 4 ok')
"

python -c "
import jazzx_sdk.modes.schemas
import jazzx_sdk.tools
import jazzx_sdk.fabric.canonical
import jazzx_sdk.llm.providers.openai
print('All imports clean')
"
```
