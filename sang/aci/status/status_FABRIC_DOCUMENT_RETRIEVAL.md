# Fabric Document Retrieval Design

**Principle: Explicit configuration, no silent fallback**

## Architecture

### Fabric Retrieval Modes

```python
from enum import Enum

class RetrievalMode(Enum):
    """Controls document retrieval behavior and fallback policy."""
    
    STRICT = "strict"
    """
    KH only, fail if unavailable or document not found.
    Use in: Production where data freshness is critical.
    """
    
    CACHED = "cached"
    """
    Try KH first, fall back to local cache if KH fails.
    Logs warning when falling back.
    Use in: Production with caching for resilience.
    """
    
    LOCAL = "local"
    """
    Local files only, never call KH.
    Use in: Development, demos, offline work.
    """
    
    TEST = "test"
    """
    Test fixtures only, fail if not found.
    Use in: Automated tests.
    """
```

### Fabric Configuration

```python
# jazzx_sdk/fabric/config.py
from pydantic import BaseModel, Field
from typing import Literal

class FabricConfig(BaseModel):
    """Fabric configuration - explicit, no surprises."""
    
    retrieval_mode: RetrievalMode = Field(
        default=RetrievalMode.LOCAL,
        description="Document retrieval mode - controls fallback behavior"
    )
    
    # Service endpoints
    knowledge_hub_url: str | None = None
    document_store_url: str | None = None
    
    # Local directories
    local_cache_dir: str = "./documents"
    golden_cases_dir: str | None = None  # For TEST mode
    
    # Auth
    api_key: str | None = None
    
    @classmethod
    def for_production(cls, kh_url: str, api_key: str, enable_cache: bool = False):
        """Production config factory."""
        return cls(
            retrieval_mode=RetrievalMode.CACHED if enable_cache else RetrievalMode.STRICT,
            knowledge_hub_url=kh_url,
            local_cache_dir="./cache" if enable_cache else None,
            api_key=api_key
        )
    
    @classmethod
    def for_development(cls, local_dir: str = "./demo_loans"):
        """Development config factory."""
        return cls(
            retrieval_mode=RetrievalMode.LOCAL,
            local_cache_dir=local_dir
        )
    
    @classmethod
    def for_testing(cls, fixtures_dir: str):
        """Test config factory."""
        return cls(
            retrieval_mode=RetrievalMode.TEST,
            golden_cases_dir=fixtures_dir
        )
```

### Fabric Implementation

```python
# jazzx_sdk/fabric/fabric.py
class Fabric:
    """
    Fabric manages service connections and document retrieval.
    
    Retrieval behavior is EXPLICIT via config.retrieval_mode:
    - STRICT: KH only, fail loudly
    - CACHED: KH with explicit cache fallback
    - LOCAL: Local files only
    - TEST: Test fixtures only
    """
    
    def __init__(self, config: FabricConfig):
        self.config = config
        self._kh_client = None
        
        # Connect to KH if configured
        if config.knowledge_hub_url and config.retrieval_mode in (
            RetrievalMode.STRICT, 
            RetrievalMode.CACHED
        ):
            self._kh_client = self._connect_kh(
                config.knowledge_hub_url,
                config.api_key
            )
    
    async def get_document(
        self,
        loan_id: str,
        document_type: str,
        **kwargs
    ) -> dict[str, Any]:
        """
        Retrieve document according to configured retrieval mode.
        
        Behavior is EXPLICIT based on config.retrieval_mode:
        - STRICT: Must come from KH, fail if not found
        - CACHED: Try KH, fall back to cache (logs warning)
        - LOCAL: Load from local directory only
        - TEST: Load from test fixtures only
        
        Raises:
            ConfigurationError: If mode requires service not configured
            DocumentNotFoundError: If document not found in primary source (STRICT)
                                   or all sources (CACHED, LOCAL, TEST)
        """
        mode = self.config.retrieval_mode
        
        if mode == RetrievalMode.STRICT:
            return await self._get_strict(loan_id, document_type, **kwargs)
        
        elif mode == RetrievalMode.CACHED:
            return await self._get_cached(loan_id, document_type, **kwargs)
        
        elif mode == RetrievalMode.LOCAL:
            return await self._get_local(loan_id, document_type, **kwargs)
        
        elif mode == RetrievalMode.TEST:
            return await self._get_test(loan_id, document_type, **kwargs)
    
    async def _get_strict(self, loan_id: str, doc_type: str, **kwargs) -> dict:
        """STRICT mode: KH only, fail if unavailable."""
        if not self._kh_client:
            raise ConfigurationError(
                "STRICT mode requires Knowledge Hub connection. "
                "Set knowledge_hub_url in config."
            )
        
        try:
            doc = await self._kh_client.get_document(
                path=f"{loan_id}/{doc_type}",
                **kwargs
            )
            logger.info(f"[STRICT] Retrieved {doc_type} from KH")
            return doc
        except DocumentNotFoundError:
            logger.error(
                f"[STRICT] Document not found in KH: {loan_id}/{doc_type}. "
                "STRICT mode does not fall back. Check KH data."
            )
            raise  # Re-raise, no fallback
    
    async def _get_cached(self, loan_id: str, doc_type: str, **kwargs) -> dict:
        """CACHED mode: Try KH, fall back to cache (explicit, logged)."""
        # Try KH first
        if self._kh_client:
            try:
                doc = await self._kh_client.get_document(
                    path=f"{loan_id}/{doc_type}",
                    **kwargs
                )
                logger.info(f"[CACHED] Retrieved {doc_type} from KH (fresh)")
                return doc
            except (DocumentNotFoundError, TimeoutError, ConnectionError) as e:
                logger.warning(
                    f"[CACHED] KH unavailable ({type(e).__name__}), "
                    f"falling back to cache for {doc_type}"
                )
        else:
            logger.warning("[CACHED] KH not connected, using cache")
        
        # Explicit fallback to cache
        cache_path = Path(self.config.local_cache_dir) / loan_id / f"{doc_type}.json"
        if cache_path.exists():
            logger.info(f"[CACHED] Retrieved {doc_type} from cache (stale): {cache_path}")
            with open(cache_path) as f:
                return json.load(f)
        
        raise DocumentNotFoundError(
            f"Document not found in KH or cache: {loan_id}/{doc_type}"
        )
    
    async def _get_local(self, loan_id: str, doc_type: str, **kwargs) -> dict:
        """LOCAL mode: Local directory only, no KH calls."""
        local_path = Path(self.config.local_cache_dir) / loan_id / f"{doc_type}.json"
        if local_path.exists():
            logger.info(f"[LOCAL] Retrieved {doc_type} from: {local_path}")
            with open(local_path) as f:
                return json.load(f)
        
        raise DocumentNotFoundError(
            f"Document not found locally: {local_path}. "
            "LOCAL mode does not query KH."
        )
    
    async def _get_test(self, loan_id: str, doc_type: str, **kwargs) -> dict:
        """TEST mode: Test fixtures only."""
        if not self.config.golden_cases_dir:
            raise ConfigurationError("TEST mode requires golden_cases_dir in config")
        
        # Map loan_id to golden case file
        golden_path = Path(self.config.golden_cases_dir) / f"{loan_id}.json"
        if not golden_path.exists():
            # Try common test case mapping
            golden_path = Path(self.config.golden_cases_dir) / "maa_lease_up.json"
        
        if not golden_path.exists():
            raise DocumentNotFoundError(f"Test fixture not found: {loan_id}")
        
        with open(golden_path) as f:
            case = json.load(f)
        
        mock_evidence = case.get("mock_evidence", {})
        if doc_type not in mock_evidence:
            raise DocumentNotFoundError(
                f"Document '{doc_type}' not in test fixture for {loan_id}"
            )
        
        logger.info(f"[TEST] Retrieved {doc_type} from fixture: {golden_path}")
        return mock_evidence[doc_type]
```

## Usage Examples

### Production (Strict - No Fallback)

```python
# Production underwriting - data MUST be fresh from KH
config = FabricConfig.for_production(
    kh_url="https://kh.prod.example.com",
    api_key=os.getenv("KH_API_KEY"),
    enable_cache=False  # STRICT mode
)

fabric = Fabric(config)

# If KH down or doc not found → raises error, investigation STOPS
# This is correct behavior for compliance/underwriting
```

### Production (Cached - Explicit Fallback)

```python
# Production with resilience - cache fallback OK for non-critical ops
config = FabricConfig.for_production(
    kh_url="https://kh.prod.example.com",
    api_key=os.getenv("KH_API_KEY"),
    enable_cache=True  # CACHED mode
)

fabric = Fabric(config)

# Tries KH, falls back to cache with warning log
# You KNOW from config this can happen
```

### Development (Local Only)

```python
# Development - no KH needed, fast iteration
config = FabricConfig.for_development(local_dir="./demo_loans")

fabric = Fabric(config)

# Never calls KH, uses local files only
# Fast, works offline
```

### Testing (Fixtures Only)

```python
# Automated tests - use fixtures, fail if missing
config = FabricConfig.for_testing(fixtures_dir="./tests/fixtures/golden_cases")

fabric = Fabric(config)

# Uses test fixtures only
# Tests fail if fixture missing (correct behavior)
```

### Tool Registry Usage

```python
# Tool registries accept Fabric, not individual clients
class CREToolRegistry(BaseToolRegistry):
    def __init__(self, fabric: Fabric):
        self.fabric = fabric
        # No more use_mocks, document_store_client, etc.
    
    async def _get_rent_roll(self, loan_id: str, **kwargs) -> dict:
        # Fabric handles retrieval according to its mode
        return await self.fabric.get_document(loan_id, "rent_roll", **kwargs)
```

### Backward Compatibility: fabric | None

```python
# New way (recommended)
fabric = Fabric(FabricConfig.for_development())
registry = CREToolRegistry(fabric=fabric)

# Legacy way (deprecated, for migration)
registry = CREToolRegistry(fabric=None, use_mocks=True)
# → Internally creates Fabric(FabricConfig(mode=LOCAL))
```

## Environment-Based Configuration

```bash
# .env.production
FABRIC_RETRIEVAL_MODE=strict
KNOWLEDGE_HUB_URL=https://kh.prod.example.com
KH_API_KEY=sk-...

# .env.development
FABRIC_RETRIEVAL_MODE=local
LOCAL_CACHE_DIR=./demo_loans

# .env.staging
FABRIC_RETRIEVAL_MODE=cached  # Fallback OK in staging
KNOWLEDGE_HUB_URL=https://kh.staging.example.com
LOCAL_CACHE_DIR=./cache
KH_API_KEY=sk-staging-...
```

```python
# Load from environment
config = FabricConfig(
    retrieval_mode=RetrievalMode(os.getenv("FABRIC_RETRIEVAL_MODE", "local")),
    knowledge_hub_url=os.getenv("KNOWLEDGE_HUB_URL"),
    local_cache_dir=os.getenv("LOCAL_CACHE_DIR", "./documents"),
    api_key=os.getenv("KH_API_KEY"),
)

fabric = Fabric(config)
```

## Benefits

✅ **No silent fallback** - Mode explicitly controls behavior  
✅ **Fail loudly in prod** - STRICT mode enforces data freshness  
✅ **Explicit cache fallback** - CACHED mode logs when falling back  
✅ **Fast development** - LOCAL mode skips network entirely  
✅ **Safe testing** - TEST mode isolated from real services  
✅ **Clear intent** - Code shows what mode you're in  
✅ **Easy debugging** - Logs prefix with [MODE] for traceability  
✅ **12-factor app** - Environment-driven configuration  

## Migration Path

### Phase 1: Add to JAPES
```python
# Add to jazzx_sdk/fabric/
- config.py (RetrievalMode, FabricConfig)
- fabric.py (Fabric class with get_document)
```

### Phase 2: Update JACI Tool Registries
```python
# Old:
registry = CREToolRegistry(
    document_store_client=doc_store,
    use_mocks=False
)

# New:
fabric = Fabric(FabricConfig.for_development())
registry = CREToolRegistry(fabric=fabric)
```

### Phase 3: Update App/Demo
```python
# Old:
doc_store = LocalCREDocumentStore(base_path="./docs")
tool_registry = CREToolRegistry(document_store_client=doc_store)

# New:
config = FabricConfig.for_development(local_dir="./docs")
fabric = Fabric(config)
tool_registry = CREToolRegistry(fabric=fabric)
```

---

**Key Principle: Fallback is NEVER silent. It's explicitly configured and logged.**
