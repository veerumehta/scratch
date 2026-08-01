# Fabric Environment Setup

**Same code, different environments - configured via .env files**

## Quick Start

### 1. Set Up Your Local Environment

```bash
# Copy example to .env
cp .env.local.example .env

# Edit .env with your settings
# FABRIC_MODE=local  ← Already set for local dev
# LOCAL_DATA_DIR=./demo_loans
```

### 2. Use in Your App - One Line!

```python
# app.py or streamlit_cre_demo.py
from jaci.common.fabric_config import create_fabric

# This ONE line adapts to environment automatically!
fabric = create_fabric()  # Reads .env, picks mode

# Use fabric everywhere
from jaci.scenarios.cre_underwriting import CREConductor
from jaci.scenarios.cre_underwriting.tools import CREToolRegistry

tool_registry = CREToolRegistry(fabric=fabric)
conductor = CREConductor(ctx=ctx, tool_registry=tool_registry)

# That's it! Works locally AND in cloud with no code changes
```

## How It Works

### On Your Machine (Local)

```bash
# .env
FABRIC_MODE=local
LOCAL_DATA_DIR=./demo_loans
```

**What happens:**
1. `create_fabric()` reads `.env`
2. Sees `FABRIC_MODE=local`
3. Creates fabric in LOCAL mode
4. All document requests → `./demo_loans/LN001/*.json`
5. No network calls, works offline ✅

**Output:**
```
INFO: Fabric configured: mode=local
INFO:   → Using local files from: ./demo_loans
```

### In the Cloud (Production)

```bash
# .env
FABRIC_MODE=strict
KNOWLEDGE_HUB_URL=https://kh.prod.example.com
KH_API_KEY=sk-prod-xxxxxxxxxxxxx
```

**What happens:**
1. `create_fabric()` reads `.env`
2. Sees `FABRIC_MODE=strict`
3. Connects to KH at `https://kh.prod.example.com`
4. All document requests → KH
5. Fails loudly if KH unavailable ✅

**Output:**
```
INFO: Fabric configured: mode=strict
INFO:   → Knowledge Hub: https://kh.prod.example.com
```

## Environment Files for Different Scenarios

### Scenario 1: Local Development (You)

```bash
# .env
FABRIC_MODE=local
LOCAL_DATA_DIR=./demo_loans
ANTHROPIC_API_KEY=sk-ant-dev-xxxxx
```

**Use case:** Working on laptop, no KH needed, fast iteration

```bash
streamlit run app.py
# → Uses local files from ./demo_loans
```

### Scenario 2: Cloud Production (Strict)

```bash
# .env (set via cloud environment variables)
FABRIC_MODE=strict
KNOWLEDGE_HUB_URL=https://kh.prod.example.com
KH_API_KEY=sk-prod-xxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-prod-xxxxx
```

**Use case:** Production underwriting - must use fresh KH data

```bash
# Cloud deployment
docker run -e FABRIC_MODE=strict -e KNOWLEDGE_HUB_URL=... jaci-app
# → Uses KH only, fails if KH down (correct!)
```

### Scenario 3: Cloud Staging (Cached)

```bash
# .env
FABRIC_MODE=cached
KNOWLEDGE_HUB_URL=https://kh.staging.example.com
KH_API_KEY=sk-staging-xxxxxxxxxxxxx
LOCAL_DATA_DIR=./cache
```

**Use case:** QA environment - prefer KH but tolerate fallback

```bash
# Staging deployment
# → Tries KH, falls back to cache if KH unavailable
# → Logs warning when falling back
```

### Scenario 4: Automated Tests

```bash
# .env.test
FABRIC_MODE=test
GOLDEN_CASES_DIR=./tests/fixtures/golden_cases
```

**Use case:** CI/CD pipeline - isolated test fixtures only

```bash
pytest tests/
# → Uses only test fixtures
# → Never calls real services
```

## App Integration Examples

### Example 1: Streamlit CRE Demo

```python
# scripts/streamlit_cre_demo.py
import streamlit as st
from jaci.common.fabric_config import create_fabric, is_local_mode
from jaci.scenarios.cre_underwriting import CREConductor, LoanApplication
from jaci.scenarios.cre_underwriting.tools import CREToolRegistry

# Create fabric from environment (ONE LINE!)
fabric = create_fabric()

# Show mode in UI
if is_local_mode():
    st.info("📁 Running in LOCAL mode - using demo files")
else:
    st.info("☁️ Connected to Knowledge Hub")

# Use fabric
tool_registry = CREToolRegistry(fabric=fabric)
conductor = CREConductor(ctx=test_context, tool_registry=tool_registry)

# Rest of demo...
loan_app = LoanApplication(...)
case_file = await conductor.run_underwriting(loan_app)
```

### Example 2: Main App with Config Display

```python
# app.py
from jaci.common.fabric_config import create_fabric, get_fabric_config

# Get fabric
fabric = create_fabric()
config = get_fabric_config()

# Show in sidebar
with st.sidebar:
    st.markdown("### Environment")
    st.text(f"Mode: {config.retrieval_mode.value}")
    
    if config.retrieval_mode == "local":
        st.text(f"Data: {config.local_cache_dir}")
    else:
        st.text(f"KH: {config.knowledge_hub_url}")

# Use fabric in scenarios
if scenario == "CRE Underwriting":
    tool_registry = CREToolRegistry(fabric=fabric)
    conductor = CREConductor(ctx=ctx, tool_registry=tool_registry)
```

### Example 3: Eval Harness

```python
# tests/eval/run_cre_eval.py
from jaci.common.fabric_config import create_fabric

def main():
    # Use environment configuration
    fabric = create_fabric()
    
    # Override for testing if needed
    if os.getenv("EVAL_USE_MOCKS"):
        from jazzx_sdk.fabric import FabricConfig, RetrievalMode
        fabric = Fabric(FabricConfig(retrieval_mode=RetrievalMode.LOCAL))
    
    tool_registry = CREToolRegistry(fabric=fabric)
    conductor = CREConductor(ctx=ctx, tool_registry=tool_registry)
    
    # Run evaluation...
```

## Deployment Workflows

### Local Development

```bash
# 1. Copy local example
cp .env.local.example .env

# 2. Add your API keys
echo "ANTHROPIC_API_KEY=sk-ant-xxxxx" >> .env

# 3. Run app - automatically uses local mode!
streamlit run app.py
```

### Deploy to Cloud

```bash
# 1. Set environment variables in cloud platform
export FABRIC_MODE=strict
export KNOWLEDGE_HUB_URL=https://kh.prod.example.com
export KH_API_KEY=sk-prod-xxxxx

# 2. Deploy (same code as local!)
docker build -t jaci-app .
docker push jaci-app
kubectl apply -f deployment.yaml

# 3. App automatically uses strict mode in cloud
```

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml
- name: Run Tests
  env:
    FABRIC_MODE: test
    GOLDEN_CASES_DIR: ./tests/fixtures/golden_cases
  run: pytest tests/
```

## Troubleshooting

### Issue: "FABRIC_MODE=strict requires KNOWLEDGE_HUB_URL"

**Problem:** Set mode to strict but forgot KH URL

**Solution:**
```bash
# Add to .env
KNOWLEDGE_HUB_URL=https://kh.example.com
KH_API_KEY=sk-xxxxx
```

### Issue: Documents not found in local mode

**Problem:** `DocumentNotFoundError` when running locally

**Solution:**
```bash
# Check LOCAL_DATA_DIR is correct
echo $LOCAL_DATA_DIR

# Verify files exist
ls $LOCAL_DATA_DIR/LN2026MAA001/

# Should see: rent_roll.json, appraisal.json, etc.
```

### Issue: KH connection fails in cloud

**Problem:** Cloud deployment can't reach KH

**Solution:**
```bash
# Check environment variables are set
env | grep FABRIC
env | grep KNOWLEDGE

# Test KH connection
curl $KNOWLEDGE_HUB_URL/health

# Check API key is valid
curl -H "Authorization: Bearer $KH_API_KEY" $KNOWLEDGE_HUB_URL/api/v1/documents
```

## Security Notes

### DO NOT Commit .env Files!

```bash
# Already in .gitignore (verify)
grep ".env" .gitignore

# Output should include:
# .env
# .env.local
# .env.*.local
```

### Use Secret Management in Cloud

```bash
# Bad: Environment variables in Dockerfile ❌
ENV KH_API_KEY=sk-prod-xxxxx

# Good: Mount secrets at runtime ✅
docker run \
  --env-file /run/secrets/jaci.env \
  jaci-app

# Or use cloud secret managers:
# - AWS: Secrets Manager
# - Azure: Key Vault
# - GCP: Secret Manager
```

## Summary

✅ **One line:** `fabric = create_fabric()` works everywhere  
✅ **Environment-driven:** Different .env for local/cloud/staging  
✅ **No code changes:** Same app.py for all environments  
✅ **Explicit mode:** You choose strict/cached/local via config  
✅ **Secure:** Secrets in .env files, not committed to git  

---

**Next:** Set up your `.env` file and run `streamlit run app.py` - it just works! 🚀
