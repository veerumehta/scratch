# Mock/Local Implementation Plan for JAPES & JACI

**Goal:** Replace scattered `use_mocks` parameters with centralized fabric configuration

## Summary

**JAPES (Platform):** Provides fabric infrastructure for retrieval modes  
**JACI (Application):** Uses fabric, provides domain-specific local connectors  

**Key Principle:** Explicit configuration, no silent fallback

---

## Architecture Division

```
┌─────────────────────────────────────────────────────────┐
│ JAPES (Platform SDK)                                    │
│                                                          │
│ ✅ Owns:                                                │
│   - Fabric class with retrieval modes                   │
│   - FabricConfig (STRICT, CACHED, LOCAL, TEST modes)    │
│   - Base connector interfaces                           │
│   - KnowledgeHubClient (real implementation)            │
│   - MockKnowledgeHubClient (mock implementation)        │
│   - Fabric.get_document() with mode-based routing       │
│                                                          │
│ ❌ Does NOT own:                                        │
│   - Domain-specific document structures                 │
│   - Application-level tool registries                   │
│   - Scenario-specific mock data                         │
└─────────────────────────────────────────────────────────┘
                        ▲
                        │ Uses
                        │
┌─────────────────────────────────────────────────────────┐
│ JACI (Application)                                      │
│                                                          │
│ ✅ Owns:                                                │
│   - fabric_config.py (environment-based config)         │
│   - create_fabric() helper                              │
│   - Scenario tool registries (CREToolRegistry, etc.)    │
│   - Domain-specific mock connectors                     │
│   - Local document directory structures                 │
│   - .env files for different environments               │
│                                                          │
│ ❌ Does NOT own:                                        │
│   - Fabric base implementation                          │
│   - Retrieval mode logic                                │
│   - Generic KH client                                   │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 1: JAPES Changes (Platform Foundation)

### 1.1 Add Retrieval Modes

**File:** `jazzx_sdk/fabric/config.py`

```python
from enum import Enum
from pydantic import BaseModel

class RetrievalMode(Enum):
    """Document retrieval modes."""
    STRICT = "strict"    # KH only, fail if unavailable
    CACHED = "cached"    # KH with local cache fallback
    LOCAL = "local"      # Local files only
    TEST = "test"        # Test fixtures only

class FabricConfig(BaseModel):
    """Fabric configuration."""
    retrieval_mode: RetrievalMode = RetrievalMode.LOCAL
    knowledge_hub_url: str | None = None
    local_cache_dir: str = "./documents"
    golden_cases_dir: str | None = None
    api_key: str | None = None
```

### 1.2 Implement Fabric Class

**File:** `jazzx_sdk/fabric/fabric.py`

```python
class Fabric:
    """
    Fabric manages service connections and document retrieval.
    
    Behavior controlled by config.retrieval_mode:
    - STRICT: KH only, fail loudly
    - CACHED: Try KH, fall back to cache (log warning)
    - LOCAL: Local files only, no KH calls
    - TEST: Test fixtures only
    """
    
    def __init__(self, config: FabricConfig):
        self.config = config
        self._kh_client = None
        
        if config.retrieval_mode in (RetrievalMode.STRICT, RetrievalMode.CACHED):
            self._kh_client = self._connect_kh(...)
    
    async def get_document(
        self, 
        loan_id: str, 
        document_type: str,
        **kwargs
    ) -> dict:
        """Retrieve document based on configured mode."""
        if self.config.retrieval_mode == RetrievalMode.STRICT:
            return await self._get_strict(...)
        elif self.config.retrieval_mode == RetrievalMode.CACHED:
            return await self._get_cached(...)
        elif self.config.retrieval_mode == RetrievalMode.LOCAL:
            return await self._get_local(...)
        elif self.config.retrieval_mode == RetrievalMode.TEST:
            return await self._get_test(...)
```

### 1.3 Update Exports

**File:** `jazzx_sdk/fabric/__init__.py`

```python
from jazzx_sdk.fabric.config import FabricConfig, RetrievalMode
from jazzx_sdk.fabric.fabric import Fabric

__all__ = ["Fabric", "FabricConfig", "RetrievalMode"]
```

### 1.4 JAPES Deliverables

- [ ] `jazzx_sdk/fabric/config.py` - FabricConfig and RetrievalMode
- [ ] `jazzx_sdk/fabric/fabric.py` - Fabric class with get_document()
- [ ] Unit tests for each retrieval mode
- [ ] Documentation in JAPES docs/

**Estimated Effort:** 1-2 days

---

## Phase 2: JACI Integration (Application Layer)

### 2.1 Add Environment Config Helper

**File:** `src/jaci/common/fabric_config.py` ✅ (Already created)

```python
def create_fabric() -> Fabric:
    """Create fabric from environment variables."""
    config = FabricConfig(
        retrieval_mode=RetrievalMode(os.getenv("FABRIC_MODE", "local")),
        knowledge_hub_url=os.getenv("KNOWLEDGE_HUB_URL"),
        local_cache_dir=os.getenv("LOCAL_DATA_DIR", "./documents"),
        api_key=os.getenv("KH_API_KEY"),
    )
    return Fabric(config)
```

### 2.2 Update Tool Registries

**Before (Current):**
```python
class CREToolRegistry(BaseToolRegistry):
    def __init__(
        self,
        document_store_client: Any = None,
        knowledge_hub_client: Any = None,
        use_mocks: bool = False,  # ❌ Scattered
    ):
        self.use_mocks = use_mocks
        self.document_store = document_store_client
        # ...
```

**After:**
```python
class CREToolRegistry(BaseToolRegistry):
    def __init__(self, fabric: Fabric):
        self.fabric = fabric
        # Fabric handles retrieval based on mode
    
    async def _get_rent_roll(self, loan_id: str, **kwargs) -> dict:
        # No if use_mocks needed!
        return await self.fabric.get_document(loan_id, "rent_roll", **kwargs)
```

### 2.3 Update Scenarios

Apply to all scenarios:
- ✅ CRE (`src/jaci/scenarios/cre_underwriting/`)
- ⏳ AML (`src/jaci/scenarios/aml/`)
- ⏳ KYC (`src/jaci/scenarios/kyc/`)
- ⏳ Earnings (`src/jaci/scenarios/earnings_anthropic/`)

**Changes per scenario:**
1. Update `tools/registry.py` to accept `fabric: Fabric`
2. Remove `use_mocks` parameters
3. Remove direct client instantiation
4. Use `fabric.get_document()` in tool methods

### 2.4 Add Environment Files

✅ Already created:
- `.env.example`
- `.env.local.example`
- `.env.cloud.example`
- `.env.staging.example`

### 2.5 Update Apps & Demos

**Before:**
```python
doc_store = LocalCREDocumentStore(base_path="./docs")
tool_registry = CREToolRegistry(
    document_store_client=doc_store,
    use_mocks=False
)
```

**After:**
```python
from jaci.common.fabric_config import create_fabric

fabric = create_fabric()  # Reads .env
tool_registry = CREToolRegistry(fabric=fabric)
```

**Files to update:**
- `app.py`
- `scripts/streamlit_cre_demo.py`
- `tests/eval/run_cre_eval.py`
- All other eval harnesses

### 2.6 JACI Deliverables

- [x] `src/jaci/common/fabric_config.py` - create_fabric() helper
- [x] `.env.*` example files
- [ ] Update CREToolRegistry to use Fabric
- [ ] Update AML/KYC/Earnings registries to use Fabric
- [ ] Update app.py to use create_fabric()
- [ ] Update all demos to use create_fabric()
- [ ] Update eval harnesses to use create_fabric()
- [ ] Integration tests verifying all modes work

**Estimated Effort:** 2-3 days

---

## Phase 3: Migration & Backward Compatibility

### 3.1 Backward Compatibility Shim

Support old API during transition:

```python
class CREToolRegistry(BaseToolRegistry):
    def __init__(
        self,
        fabric: Fabric | None = None,
        # Deprecated parameters (for migration)
        document_store_client: Any = None,
        use_mocks: bool = False,
    ):
        if fabric is None:
            # Legacy mode - create fabric from old params
            warnings.warn(
                "Passing document_store_client/use_mocks is deprecated. "
                "Use fabric parameter instead.",
                DeprecationWarning
            )
            mode = RetrievalMode.LOCAL if use_mocks else RetrievalMode.STRICT
            fabric = Fabric(FabricConfig(retrieval_mode=mode))
        
        self.fabric = fabric
```

### 3.2 Migration Checklist

For each JACI scenario:

1. ✅ Add fabric parameter to tool registry
2. ✅ Keep old parameters with deprecation warning
3. ✅ Update internal methods to use fabric.get_document()
4. ✅ Update tests to use new API
5. ✅ Update demos/apps to use new API
6. ✅ Remove deprecated parameters after 1-2 versions

### 3.3 Documentation Updates

- [ ] Update README.md with new fabric usage
- [x] Add FABRIC_ENVIRONMENT_SETUP.md guide
- [x] Add FABRIC_DOCUMENT_RETRIEVAL.md design doc
- [ ] Update ARCHITECTURE.md if exists
- [ ] Add migration guide for users

---

## Phase 4: Testing & Validation

### 4.1 JAPES Tests

```python
# test_fabric_modes.py
@pytest.mark.asyncio
async def test_strict_mode_fails_without_kh():
    config = FabricConfig(retrieval_mode=RetrievalMode.STRICT)
    fabric = Fabric(config)
    
    with pytest.raises(ConfigurationError):
        await fabric.get_document("LN001", "rent_roll")

@pytest.mark.asyncio
async def test_local_mode_reads_from_directory():
    config = FabricConfig(
        retrieval_mode=RetrievalMode.LOCAL,
        local_cache_dir="./test_data"
    )
    fabric = Fabric(config)
    
    doc = await fabric.get_document("LN001", "rent_roll")
    assert doc is not None

@pytest.mark.asyncio
async def test_cached_mode_falls_back_with_warning(caplog):
    config = FabricConfig(
        retrieval_mode=RetrievalMode.CACHED,
        knowledge_hub_url="http://unreachable.example.com",
        local_cache_dir="./test_data"
    )
    fabric = Fabric(config)
    
    doc = await fabric.get_document("LN001", "rent_roll")
    assert "falling back to cache" in caplog.text
```

### 4.2 JACI Integration Tests

```python
# test_cre_with_fabric.py
@pytest.mark.asyncio
async def test_cre_conductor_with_local_fabric():
    """Test CRE conductor works with LOCAL mode."""
    config = FabricConfig.for_development(local_dir="./test_loans")
    fabric = Fabric(config)
    
    tool_registry = CREToolRegistry(fabric=fabric)
    conductor = CREConductor(ctx=test_ctx, tool_registry=tool_registry)
    
    loan_app = LoanApplication(loan_id="LN001", ...)
    case_file = await conductor.run_underwriting(loan_app)
    
    assert case_file.recommendation is not None

@pytest.mark.asyncio
async def test_cre_conductor_with_test_fabric():
    """Test CRE conductor works with TEST mode (fixtures)."""
    config = FabricConfig.for_testing(fixtures_dir="./tests/fixtures")
    fabric = Fabric(config)
    
    tool_registry = CREToolRegistry(fabric=fabric)
    conductor = CREConductor(ctx=test_ctx, tool_registry=tool_registry)
    
    # Should use golden case fixtures
    loan_app = LoanApplication(loan_id="maa_lease_up", ...)
    case_file = await conductor.run_underwriting(loan_app)
    
    assert case_file.recommendation is not None
```

### 4.3 Manual Testing Checklist

- [ ] Local development: `FABRIC_MODE=local streamlit run app.py`
- [ ] With KH (if available): `FABRIC_MODE=strict streamlit run app.py`
- [ ] Cached mode: `FABRIC_MODE=cached streamlit run app.py`
- [ ] Test mode: `FABRIC_MODE=test pytest tests/`
- [ ] Verify fallback logs appear in CACHED mode
- [ ] Verify STRICT mode fails loudly without KH
- [ ] All eval harnesses work with new fabric

---

## Timeline & Ownership

### Week 1: JAPES Foundation
**Owner:** JAPES team (or you if maintaining both)

- [ ] Implement FabricConfig and RetrievalMode
- [ ] Implement Fabric class with retrieval modes
- [ ] Write unit tests for each mode
- [ ] Review and merge to JAPES

### Week 2: JACI Integration - Part 1
**Owner:** JACI team

- [x] Create fabric_config.py helper
- [x] Create .env examples
- [ ] Update CRE tool registry
- [ ] Test CRE with all modes
- [ ] Update CRE app and demo

### Week 3: JACI Integration - Part 2
**Owner:** JACI team

- [ ] Update AML tool registry
- [ ] Update KYC tool registry
- [ ] Update Earnings tool registry
- [ ] Update all eval harnesses
- [ ] Integration tests for all scenarios

### Week 4: Polish & Documentation
**Owner:** Both teams

- [ ] Migration guide
- [ ] Remove deprecated parameters
- [ ] Final testing across all scenarios
- [ ] Update README and docs
- [ ] Release notes

---

## Benefits After Implementation

### For Developers

✅ **One line setup:** `fabric = create_fabric()`  
✅ **Works offline:** LOCAL mode needs no KH  
✅ **Fast iteration:** No network overhead in dev  
✅ **Clear intent:** Config shows exactly what mode  

### For Operations

✅ **Environment-driven:** Same code, different .env  
✅ **Production-safe:** STRICT mode fails loudly  
✅ **Resilient:** CACHED mode with explicit fallback  
✅ **Observable:** Logs show which mode, source used  

### For Testing

✅ **Isolated tests:** TEST mode uses fixtures only  
✅ **No mocks needed:** Fabric handles retrieval  
✅ **Predictable:** No network calls, fast tests  

### For Codebase

✅ **No scattered config:** Removed ~50 `use_mocks` parameters  
✅ **Centralized:** All retrieval logic in Fabric  
✅ **Maintainable:** New scenarios just use Fabric  
✅ **Cross-scenario:** AML, KYC, CRE all use same pattern  

---

## Open Questions

1. **Q:** Should Fabric be in its own JAPES package or part of handlers?  
   **A:** TBD - depends on JAPES architecture

2. **Q:** Do we support PDF/Excel parsing in Fabric or leave to apps?  
   **A:** Leave to apps - Fabric provides dict, apps parse formats

3. **Q:** How to handle KH authentication (OAuth vs API key)?  
   **A:** FabricConfig.api_key for now, extend auth later if needed

4. **Q:** Should CACHED mode update cache on successful KH fetch?  
   **A:** Yes - good feature for resilience (implement in Phase 1)

---

## Success Criteria

✅ JAPES has Fabric with 4 retrieval modes  
✅ All JACI scenarios use Fabric (no use_mocks)  
✅ Apps work locally with `FABRIC_MODE=local`  
✅ Apps work in cloud with `FABRIC_MODE=strict`  
✅ Tests use `FABRIC_MODE=test` with fixtures  
✅ Documentation complete with examples  
✅ All existing tests pass with new implementation  

---

**Next Immediate Action:** Implement Phase 1 in JAPES (FabricConfig + Fabric class)
