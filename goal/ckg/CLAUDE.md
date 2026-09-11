# Culture-Graph

Runtime implementation of the Spherex CKG (Cultural Knowledge Graph) specification.

## What This Is

This repo implements the MCP server and data store specified in `spherex-ckg`. It provides cultural intelligence tools that AI agents can call for content compliance and cultural guidance.

## Quick Start

```bash
# Memory backend (no Neo4j required)
BACKEND=memory streamlit run streamlit_app/app.py

# Demo page for stakeholder presentations
BACKEND=memory streamlit run streamlit_app/pages/demo.py
```

## MCP Tools (8 total)

### From spherex-ckg spec (4):
| Tool | Purpose | Latency |
|------|---------|---------|
| `compliance_check` | Detect compliance patterns in content | <200ms |
| `cultural_guidance` | Merged compliance + cultural knowledge | <500ms |
| `regulatory_check` | Territory + category regulatory lookup | <50ms |
| `cultural_context` | Cultural briefing without content eval | <100ms |

### Added by us (4):
| Tool | Purpose | Latency |
|------|---------|---------|
| `cultural_lookup` | Direct query by territory + domain + keyword | <100ms |
| `cultural_query` | Natural language interface with NLU extraction | <300ms |
| `smart_query` | Auto-routing entry point (detects intent) | <300ms |
| `get_metadata` | Returns territories, categories, config | <50ms |

## Data Loaded

| Dataset | Count |
|---------|-------|
| Cultural criteria | 39,566 |
| Content rating rules | 61,722 |
| Territories | 127 |
| Cultural domains | 21 |
| Detection keywords | 1,385 |
| Context categories | 13 |

## Key Features

### Semantic Routing (Hybrid)
- **Layer 1: Keywords** - 1,385 detection terms, deterministic, <5ms
- **Layer 2: Embeddings** - `all-MiniLM-L6-v2` fallback when keywords miss
- Cosine similarity threshold: 0.25

### Relevance Scoring
- **Dimension-aware**: "dietary rules" queries boost Ingredients/Preparation dimensions
- **Gap-based filtering**: Cuts off when score drops >25% from previous result
- **Generic keyword downweighting**: Common words (dietary, rules, food) get 0.25x weight
- **Configurable sensitivity**: 0.0 (strict) to 1.0 (loose)

### Content Ratings Integration
- 61,722 territory-specific age ratings from `CKG_Ratings_Master_R15.1.xlsx`
- Exposed via `regulatory_check` and `cultural_guidance` tools
- Includes sensitivity scores (1-10), target audiences (Kids/Teens/Adults)

## Project Structure

```
culture-graph/
├── src/ckg/
│   ├── mcp/server.py          # MCP server with 8 tools
│   ├── store/
│   │   ├── memory_store.py    # In-memory backend (file-based)
│   │   └── neo4j_store.py     # Neo4j backend
│   ├── queries/
│   │   ├── resolvers.py       # NLU: territory/domain extraction, scoring
│   │   └── context_classifier.py  # Semantic routing with embeddings
│   └── loaders/               # Data loading utilities
├── streamlit_app/
│   ├── app.py                 # Main 9-tab application
│   └── pages/
│       ├── demo.py            # Stakeholder demo page
│       └── chat_assistant.py  # Chat interface
├── data/ckg/
│   ├── v7.4/                  # Cultural criteria by category
│   ├── rules/                 # Ratings master, regulatory data
│   └── schemas/               # JSON schemas for tool I/O
└── docs/
    └── DEMO_PAGE_SCRIPT.md    # Presenter script for demos
```

## Recent Changes

### v0.9.8 (Current)
- **Externalized query configuration** - Keywords/patterns now in JSON files (`data/ckg/config/`)
  - `domain_keywords.json` - 21 domains, ~400 keywords
  - `generic_keywords.json` - Terms to downweight in scoring
  - `query_patterns.json` - Query type classification patterns
  - Config exposed via `get_metadata` MCP tool
- **Cross-domain query aggregation** - Holiday queries search both Holidays + National_Observances
- **Exploratory query classification** - "What are the forms/holidays/figures" returns 10 results
- **Primary keyword selection** - Skips generic terms (rules, dietary) to find specific keywords (bbq)

### v0.9.6
- **Semantic search with pre-computed embeddings**: Embeddings for all 39,566 criteria pre-computed offline
- **Primary topic boost**: Entries where quoted topic matches query keyword get 15-point bonus
- Hybrid ranking: keyword scores + semantic similarity bonus + topic bonus
- Model: `all-MiniLM-L6-v2` (384 dimensions)
- Run `python scripts/generate_embeddings.py` to regenerate embeddings after data changes

### v0.9.5
- Integrated 61,722 content rating rules
- Added dimension-aware scoring for better relevance
- Gap-based filtering (replaces fixed ratio threshold)
- Configurable sensitivity parameter (0.0-1.0)
- Added known food topics (bhog, prasad, etc.) to domain keywords
- Demo page with sensitivity slider
- Fixed keyword matching for compound words (yellow vs orange-yellow)

## Known Limitations

1. **Cross-reference matches**: Largely resolved by primary topic boost (v0.9.6). Entries where the main topic matches the query now rank significantly higher than entries that merely mention the term.

2. **Domain detection**: Queries need recognizable keywords to route correctly. Adding specific terms (like "bhog") to domain keywords helps.

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `BACKEND` | `neo4j` | Store backend: `memory` or `neo4j` |
| `ENABLE_HOT_RELOAD` | `false` | Auto-reload data on file changes |
| `RELOAD_CHECK_INTERVAL` | `30` | Seconds between reload checks |

## Testing

```bash
# Run tests
pytest tests/

# Test MCP tools directly
python -c "from src.ckg.mcp.server import create_mcp_server; ..."
```

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Documentation and attribution
- Code should not look like it came from AI, including any comments or commits that say Co-authored by Claude Sonnet etc
- CHANGELOG, README, and ARCHITECTURE md files should be regularly updated
- If significant changes, bump up at least patch version. For major version update, enquire
- Commit messages should be SHORT - details go in CHANGELOG.md

## 6. Git restrictions
- **NEVER run `git push`** - user handles all pushes
- Commits are allowed, but keep messages brief
---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
