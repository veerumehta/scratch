# Document Analyzer Roadmap

**Date**: 2025-12-18 (Updated: 2025-12-28)
**Status**: Planning document for future enhancements
**Context**: Learning from MACER patterns to evolve document_analyzer into a comprehensive template

## Current State

**document_analyzer** supports:
- Single operation: analyze documents
- Retrieves documents from Knowledge Hub
- Basic stats (word count, char count)
- AI analysis using OpenAI Agent SDK
- Structured output with Pydantic models
- Streaming support
- Postgres session persistence
- Demonstrates ctx.runtime integration
- ✅ **NEW (2025-12-28)**: Token usage tracking with DebugHooks
- ✅ **NEW (2025-12-28)**: Context size management with input filters

**MACER** demonstrates:
- Multi-operation routing (guidelines, loan, jtbd, classify)
- Batch processing with parallel category-based processing
- PDF classification using Kernel + Knowledge Hub
- Custom JSON schema support for structured output
- Usage/stats tracking (tokens, LLM turns, caching)
- Retry logic for transient failures
- Per-operation custom logging

## Proposed Enhancements

### 1. Multi-Operation Routing

Add operation-based routing similar to MACER:

```python
operations = {
    "analyze": self._handle_analyze,      # Current functionality
    "classify": self._handle_classify,    # New: PDF classification
    "compare": self._handle_compare,      # New: Compare multiple docs
    "extract": self._handle_extract,      # New: Extract specific data
    "summarize": self._handle_summarize   # New: Batch summarization
}
```

**Message format:**
```json
{
  "payload": {
    "data": {
      "operation": "classify|analyze|compare|extract|summarize",
      "document_ids": [...],
      "collection_id": "...",
      "options": {...}
    }
  }
}
```

### 2. Batch Processing with Parallelization

Process multiple documents in parallel, inspired by MACER's JTBD category processing:

```python
# Group documents by type/category
docs_by_type = defaultdict(list)
for doc in documents:
    doc_type = doc.get("metadata", {}).get("type", "unknown")
    docs_by_type[doc_type].append(doc)

# Process each type in parallel
tasks = [
    self._process_document_type(doc_type, docs)
    for doc_type, docs in docs_by_type.items()
]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

### 3. Document Classification Operation

Add classify operation using Kernel's PDF processing tools:

```python
async def _handle_classify(self, ctx: HandlerContext, data: dict) -> dict:
    """
    Classify documents using Kernel's Azure Document Intelligence.

    Flow:
    1. Get PDF from Knowledge Hub or accept base64
    2. Convert to markdown via ctx.runtime.kernel.call_tool("azure_pdf_to_md")
    3. Classify using AI agent with taxonomy
    4. Store classified document back to Knowledge Hub
    5. Return classification results
    """
```

**Benefits:**
- Demonstrates Kernel tool usage
- Shows Knowledge Hub write operations
- Provides document organization capability

### 4. Custom JSON Schema Support

Support user-provided schemas for structured output:

```python
# User provides schema
schema = {
    "type": "object",
    "properties": {
        "entities": {"type": "array"},
        "dates": {"type": "array"},
        "amounts": {"type": "array"}
    }
}

# Generate Pydantic model from schema
OutputModel = create_model_from_schema(schema)

# Use in Agent
agent = Agent(
    output_type=OutputModel,
    ...
)
```

### 5. Usage and Cost Tracking ✅ COMPLETED (2025-12-28)

Track OpenAI API usage like MACER:

```python
from jazzx_sdk.agent_utils import DebugHooks

# Track token usage
hooks = DebugHooks(name="document_analyzer")
result = await Runner.run(agent, input=prompt, hooks=hooks)

# Get statistics
stats = hooks.get_stats()
logger.info(
    f"Token usage - LLM turns: {stats.llm_turns}, "
    f"Input: {stats.total_input_tokens}, "
    f"Output: {stats.total_output_tokens}, "
    f"Cached: {stats.total_cached_tokens}, "
    f"Reasoning: {stats.total_reasoning_tokens}"
)
```

**Implementation:** Uses `jazzx_sdk.agent_utils.DebugHooks` generalized from MACER.

**Also added:** Context size management with `create_size_limit_filter` to prevent context length errors in long sessions.

### 6. Retry Logic

Add retry wrapper for transient failures:

```python
async def _with_retry(self, operation, max_retries=3):
    """Retry operation with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await operation()
        except TransientError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

### 7. Document Comparison Operation

Compare multiple documents and identify differences/similarities:

```python
async def _handle_compare(self, ctx: HandlerContext, data: dict) -> dict:
    """
    Compare multiple documents.

    Returns:
    - Common themes
    - Unique points per document
    - Similarity scores
    - Recommendations
    """
```

### 8. Structured Data Extraction

Extract specific data from documents using schemas:

```python
async def _handle_extract(self, ctx: HandlerContext, data: dict) -> dict:
    """
    Extract structured data from documents.

    User provides:
    - Extraction schema (what to extract)
    - Validation rules

    Returns validated structured data per document.
    """
```

## Implementation Priority

**Phase 1** (High Value, Low Complexity):
1. ✅ **DONE** Usage tracking - easy win, valuable for cost monitoring (DebugHooks + input filters)
2. Multi-operation routing - clean refactor, enables other features

**Phase 2** (Medium Value, Medium Complexity):
3. Document classification - demonstrates Kernel integration
4. Batch parallelization - performance improvement

**Phase 3** (High Value, High Complexity):
5. Custom JSON schema support - requires schema validation
6. Document comparison - advanced AI feature
7. Structured extraction - specialized use case

## Next Steps

1. Start with usage tracking and multi-operation routing
2. Add classify operation to demonstrate Kernel PDF tools
3. Implement batch parallelization for performance
4. Add comparison and extraction as advanced features

## Notes

- Keep backward compatibility with current analyze operation
- Document each operation with clear examples
- Add comprehensive tests for each operation
- Update README with operation descriptions
