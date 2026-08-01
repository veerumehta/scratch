# CRE Local Document Store

**Using local files instead of mocks for CRE demo and app**

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│ JAPES (Platform)                                        │
│ ├── MockKernelClient         ← Generic tool execution  │
│ └── MockKnowledgeHubClient   ← Generic knowledge (KH)  │
│     └── data_dir parameter   ← Supports local files    │
└─────────────────────────────────────────────────────────┘
                        ▲
                        │ Inherits pattern
                        │
┌─────────────────────────────────────────────────────────┐
│ JACI (Application)                                      │
│ ├── AML: mock_connectors.py      ← AML-specific        │
│ ├── KYC: kyc_mock_connectors.py  ← KYC-specific        │
│ └── CRE: mock_connectors.py      ← CRE-specific (NEW)  │
│     └── LocalCREDocumentStore                           │
│         ├── Reads from local directory                  │
│         └── Falls back to golden cases                  │
└─────────────────────────────────────────────────────────┘
```

## Key Concepts

### 1. Document Store vs Knowledge Hub

**Document Store** (`document_store_client`):
- Loan-specific documents (rent rolls, appraisals, financials)
- Organized by `loan_id`
- Changes per deal

**Knowledge Hub** (`knowledge_hub_client`):
- Shared knowledge (lending policies, market comps library)
- Reusable across loans
- Stable reference data

**These are complementary, not overlapping!**

### 2. Mock Modes

CRE tools support **three modes**:

```python
# Mode 1: Pure mocks (no files needed)
tool_registry = CREToolRegistry(use_mocks=True)
# → Returns hardcoded mock data

# Mode 2: Local files with golden case fallback
doc_store = LocalCREDocumentStore(base_path="./cre_documents")
tool_registry = CREToolRegistry(
    document_store_client=doc_store,
    use_mocks=False
)
# → Reads from ./cre_documents/LN001/*.json
# → Falls back to golden cases if not found

# Mode 3: Real connectors (future)
doc_store = AzureBlobDocumentStore(...)
tool_registry = CREToolRegistry(
    document_store_client=doc_store,
    use_mocks=False
)
# → Fetches from cloud storage
```

## Directory Structure

### Local Documents Layout:

```
cre_documents/
├── LN2026MAA001/
│   ├── rent_roll.json          # Current rent roll
│   ├── operating_statement.json # T-12 operating statement
│   ├── appraisal.json          # Appraisal report
│   ├── market_study.json       # Market comps
│   ├── title_report.json       # Title report
│   ├── sponsor_financials.json # Sponsor statements
│   └── property_inspection.json # Inspection report
│
├── LN2026XYZ002/
│   └── ...
│
└── README.md                   # Document structure guide
```

### Example Document Format:

**rent_roll.json:**
```json
{
  "loan_id": "LN2026MAA001",
  "property_name": "Mesa Verde Apartments",
  "as_of_date": "2026-03-01",
  "total_units": 120,
  "occupied_units": 107,
  "physical_occupancy": 0.892,
  "economic_occupancy": 0.848,
  "summary": {
    "occupied_and_paying": 102,
    "leased_but_non_paying": 5,
    "vacant": 13,
    "occupancy_gap_percentage_points": 4.4
  },
  "units": [
    {
      "unit_number": "101",
      "unit_type": "1BR",
      "sq_ft": 650,
      "tenant_name": "John Smith",
      "lease_start": "2025-06-01",
      "lease_end": "2026-05-31",
      "current_rent": 1250,
      "market_rent": 1300,
      "status": "occupied_paying"
    }
  ]
}
```

## Usage Examples

### Example 1: Streamlit CRE Demo with Local Files

```python
# scripts/streamlit_cre_demo.py
import streamlit as st
from jaci.scenarios.cre_underwriting import CREConductor
from jaci.scenarios.cre_underwriting.tools import LocalCREDocumentStore, CREToolRegistry

# Option 1: Use golden cases (default)
doc_store = LocalCREDocumentStore(
    base_path="tests/fixtures/golden_cases"
)

# Option 2: Use custom local directory
# doc_store = LocalCREDocumentStore(base_path="./demo_loans")

tool_registry = CREToolRegistry(
    document_store_client=doc_store,
    use_mocks=False  # Use local files, not hardcoded mocks
)

# Initialize conductor
conductor = CREConductor(
    ctx=test_context,
    tool_registry=tool_registry,
)

# Run investigation
loan_app = LoanApplication(loan_id="LN2026MAA001", ...)
case_file = await conductor.run_underwriting(loan_app)
```

### Example 2: App.py with User-Specified Directory

```python
# app.py - CRE Demo page
import streamlit as st
from pathlib import Path

st.title("🏢 CRE Demo with Local Documents")

# User can specify custom document directory
doc_dir = st.text_input(
    "Local Documents Directory",
    value="./cre_documents",
    help="Path to directory containing loan documents"
)

if st.button("Load Documents"):
    try:
        doc_store = LocalCREDocumentStore(base_path=doc_dir)
        tool_registry = CREToolRegistry(
            document_store_client=doc_store,
            use_mocks=False
        )
        st.success(f"✅ Loaded documents from {doc_dir}")
    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.info("Falling back to golden cases...")
        doc_store = LocalCREDocumentStore(
            base_path="tests/fixtures/golden_cases"
        )
```

### Example 3: Evaluation Harness with Local Files

```python
# tests/eval/run_cre_eval.py
from jaci.scenarios.cre_underwriting.tools import get_mock_document_store

# Use local documents if available, golden cases otherwise
doc_store = get_mock_document_store(base_path="./eval_loans")

tool_registry = CREToolRegistry(
    document_store_client=doc_store,
    use_mocks=False
)

conductor = CREConductor(ctx=ctx, tool_registry=tool_registry)
```

## Fallback Logic

`LocalCREDocumentStore` has smart fallback:

1. **Try local directory first**: `./cre_documents/LN2026MAA001/rent_roll.json`
2. **Fall back to golden cases**: `tests/fixtures/golden_cases/maa_lease_up.json`
3. **Raise error if neither found**: Clear error message

This means:
- ✅ **Demo works out-of-box** with golden cases
- ✅ **Easy to add real loans** by dropping files in directory
- ✅ **Graceful degradation** if custom directory not found

## Benefits vs Pure Mocks

| Feature | Pure Mocks | LocalDocumentStore |
|---------|-----------|-------------------|
| **Works offline** | ✅ | ✅ |
| **No setup needed** | ✅ | ⚠️ (but has fallback) |
| **Real loan data** | ❌ | ✅ |
| **Easy to update** | ❌ (code change) | ✅ (drop JSON file) |
| **Demo-ready** | ✅ | ✅ (with golden cases) |
| **Realistic testing** | ⚠️ (fake data) | ✅ (real structure) |

## Migration Path

### Today: Mocks
```python
tool_registry = CREToolRegistry(use_mocks=True)
# → Hardcoded data
```

### Tomorrow: Local Files
```python
doc_store = LocalCREDocumentStore(base_path="./demo_loans")
tool_registry = CREToolRegistry(document_store_client=doc_store, use_mocks=False)
# → Real loan files from directory
```

### Future: Cloud Storage
```python
doc_store = AzureBlobDocumentStore(container="cre-loans")
tool_registry = CREToolRegistry(document_store_client=doc_store, use_mocks=False)
# → Documents from Azure Blob Storage
```

**No code changes needed** - just swap the `document_store_client`!

## Creating Local Document Directories

### Quick Start:

```bash
# 1. Create directory structure
mkdir -p cre_documents/LN2026MAA001

# 2. Copy golden case as template
cp tests/fixtures/golden_cases/maa_lease_up.json /tmp/golden.json

# 3. Extract documents (Python helper)
python -c "
import json
from pathlib import Path

with open('/tmp/golden.json') as f:
    case = json.load(f)

loan_dir = Path('cre_documents/LN2026MAA001')
loan_dir.mkdir(parents=True, exist_ok=True)

for doc_type, content in case['mock_evidence'].items():
    with open(loan_dir / f'{doc_type}.json', 'w') as out:
        json.dump(content, out, indent=2)

print(f'✅ Created {len(case[\"mock_evidence\"])} document files')
"

# 4. Now you have:
# cre_documents/LN2026MAA001/
# ├── rent_roll.json
# ├── operating_statement.json
# └── ...
```

## Next Steps

1. **Extract golden case to directory** (see Quick Start above)
2. **Test in demo**: `streamlit run scripts/streamlit_cre_demo.py`
3. **Add more loans**: Create new directories (LN002, LN003, etc.)
4. **Real data**: Replace JSON with actual loan documents

## FAQ

**Q: Do I need to set up local files for the demo to work?**  
A: No! It falls back to golden cases automatically.

**Q: Can I use PDF/Excel files instead of JSON?**  
A: Not yet, but you can extend `LocalCREDocumentStore.get_document()` to parse PDFs/Excel.

**Q: How does this relate to MockKnowledgeHubClient?**  
A: `LocalCREDocumentStore` is for **loan documents**. MockKH is for **shared knowledge** (policies, comps). Use both together.

**Q: Can I use this in production?**  
A: Not recommended. This is for demos and testing. Production should use cloud storage with proper auth/audit.

---

**See also:**
- `src/jaci/scenarios/cre_underwriting/tools/mock_connectors.py` - Implementation
- `tests/fixtures/golden_cases/maa_lease_up.json` - Example golden case
- `src/jaci/scenarios/cre_underwriting/tools/registry.py` - Tool registry
