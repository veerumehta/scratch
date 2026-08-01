# ci_spread financial spreading — status (autonomous session)

## Goal
ci_spread demo: ingest the borrower's 10-K and produce the **Excel/CSV financial spread**.
BPMN is the eventual conductor; the Python conductor + `commercial_lending` are transitional.

## Built (all committed on `dev`, NOT pushed)
- **DocIntel stub** (`commercial_lending/docintel.py`): `convert_document(path) -> markdown`,
  resolves a co-located `<stem>.md`. Production seam = Azure Document Intelligence
  (mortgage-app pattern). Option (c), real DocIntel conversion, pending keys.
- **FinancialSpread schema** (`commercial_lending/spread_schema.py`): standardized,
  **as-reported** IS/BS/CF line items × periods (no derived analytics — those are downstream).
- **Spreading engine** (`commercial_lending/spreader.py`):
  - `spread_financials(md)` — locate IS/BS/CF regions, flatten HTML, LLM-structure into the
    schema (Claude structures; numbers verbatim). Faithful, not summarized.
  - `validate_spread(spread, truth, key_statement=)` — cross-checks vs SEC XBRL ground truth
    (statement-scoped). **YETI FY2025: IS 14 / BS 30 / CF 32 lines, 13/13 key values exact.**
  - `merge_spreads` / `spread_filings` — multi-year merge across filings (restatement = most
    recent filing wins).
- **Excel skill** (`commercial_lending/excel.py`): formatted workbook (cover + IS/BS/CF +
  in-sheet YoY Trends) + CSV; `spread_to_xlsx_bytes` / `statement_csv_text` for downloads.
- **Demo tab** "10-K Spreading" (`ci_spread/ui/demo_page.py`): choose single FY2025 or all
  filings (FY2020-2025); runs DocIntel stub -> spread -> table view + Excel/CSV download.
- **Tests** (`tests/unit/test_commercial_lending_spreading.py`, 8, no-LLM, CI-safe).

## Inputs (gitignored, local under docs/LoanSamples/.../Yeti FInancials/)
The local 10-K PDFs are 56MB rasterized "Print to PDF" (0 extractable text). So extractable
sources were downloaded from **SEC EDGAR** (YETI CIK 1670592) and converted to markdown via
**pandoc** (faithful), staged as co-located `.md` for the stub:
- FY2025 filing (yeti-20260103) -> "YETI FY 2025 SEC 10-K_1.3.2026.md"
- FY2023 filing (yeti-20231230) -> "YETI 2024 SEC 10-K_12.30.2023.md"
- FY2022 filing (yeti-20221231) -> "YETI 2023 SEC 10-K_12.31.2022.md"
Ground truth: SEC XBRL companyfacts (`/tmp/yeti_xbrl_truth.json` during the session).

## Runs in jaci's current venv
The spreading path uses `jazzx_sdk.llm.LLMManager` (works in the stale-japes venv) — no new-japes
dependency. (The live-conductor Trace tab DOES need japes 1.6.7.)

## Next steps
- Swap option (c): real Azure DocIntel conversion script (keys pending) -> cleaner md tables.
- Offline-convert the **application document checklist** -> a canonical document-completeness
  Policy (build-time domain asset), consumed at runtime (see the two-layer model).
- Optionally wire Tab 1 ("Spread") to render the live spread output instead of yeti_financials.json.
- Promote the Excel writer to a JAPES skill if other packs need it; CRE can reuse the pipeline.
