"""Validate scanned-document support on the Acra closing package (local only).

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Runs the shipped DSCR document agent config over the four PDFs of
``tests/fixtures/local/acra_godocs_mixed`` joined into one package, through each engine, and reports
AGGREGATE figures only: segment labels and page ranges, which pages were scanned, which appraisal
fields were read (present or not, never the value), agreement between engines (a boolean), cost and
time. It prints no text from the documents and writes nothing but the aggregate JSON.

    python scripts/local/acra_scanned_validation.py --phase split-vision
    python scripts/local/acra_scanned_validation.py --phase split-docintel
    python scripts/local/acra_scanned_validation.py --phase appraisal

Needs the provider key and the DocIntel endpoint and key in the environment (see japes' .env).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4] / "japes" if False else Path("/Users/sangit/src/japes")
sys.path.insert(0, str(ROOT))

SEED = ROOT / "plato" / "data" / "seed_packs" / "acra_dscr_policy"
FIXTURE = ROOT / "tests" / "fixtures" / "local" / "acra_godocs_mixed"
REPORT = FIXTURE / "REPORT.json"       # gitignored with the folder; aggregate figures only
VISION_MODEL = os.getenv("ACRA_VISION_MODEL", "gpt-5.6-luna")
VISION_BUDGET_USD = 5.0


def _load_env() -> None:
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            if key.strip().startswith("AZURE_DOCUMENT_INTELLIGENCE"):
                os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _package(tmp: Path) -> Path:
    import fitz

    out = fitz.open()
    for name in sorted(p.name for p in FIXTURE.glob("*.pdf")):
        src = fitz.open(FIXTURE / name)
        out.insert_pdf(src)
        src.close()
    path = tmp / "package.pdf"
    out.save(path)
    out.close()
    return path


class Tally:
    """Wraps the agent service: counts calls, tokens and cost, and says nothing about content."""

    def __init__(self, inner):
        self._inner = inner
        self.calls = self.input = self.output = 0
        self.cost = 0.0
        self.upper = False

    def __getattr__(self, name):
        return getattr(self._inner, name)

    async def run(self, **kwargs):
        result = await self._inner.run(**kwargs)
        trace = getattr(result, "trace", None)
        self.calls += 1
        if trace is not None:
            self.input += trace.tokens_input
            self.output += trace.tokens_output
            self.cost += trace.cost_usd
            self.upper |= bool(getattr(trace, "cost_is_upper_bound", False))
        return result

    def summary(self) -> dict:
        return {"calls": self.calls, "input_tokens": self.input, "output_tokens": self.output,
                "cost_usd": round(self.cost, 4), "cost_is_upper_bound": self.upper}


def _spec(**over):
    from jazzx_sdk.agents.document.spec import DocumentAgentSpec

    base = DocumentAgentSpec.from_dir(SEED).model_dump()
    base.update(over)
    return DocumentAgentSpec.from_config(base)


def _di_cost(pages_by_model: dict) -> float:
    from jazzx_sdk.llm.page_pricing import price_pages

    return price_pages(pages_by_model)[0]


def _scanned_pages(path: Path) -> list[int]:
    from jazzx_sdk.tools.documents.pages.assess import assess_pages

    return [i + 1 for i, a in enumerate(assess_pages(str(path))) if a.needs_reading]


def _segments(segs) -> list[dict]:
    return [{"label": s.label, "pages": [s.start_page + 1, s.end_page + 1],
             "confidence": round(s.confidence, 2), "review_pages": len(s.review_pages)}
            for s in segs]


async def split_phase(engine: str, package: Path) -> dict:
    from jazzx_sdk.agents.document.agent import DocumentAgent
    from jazzx_sdk.agents.service import AgentExecutionService
    from jazzx_sdk.tools.documents.conversion import get_di_pages_by_model, reset_di_page_count
    from jazzx_sdk.tools.documents.docintel_azure import AzureDocIntelligenceProvider

    tally = Tally(AgentExecutionService())
    if engine == "vision":
        spec = _spec(split_vision=True, split_identity=os.getenv("ACRA_IDENTITY", "1") == "1",
                     vision_model=VISION_MODEL,
                     vision_budget_usd=VISION_BUDGET_USD, split_ocr_fallback=False)
        agent = DocumentAgent(spec, agents=tally, cache_dir=tempfile.mkdtemp(prefix="acra-cache-"))
    else:
        spec = _spec(split_vision=False, split_ocr_fallback=True, split_identity=False)
        agent = DocumentAgent(spec, agents=tally,
                              di_provider=AzureDocIntelligenceProvider(model_id="prebuilt-layout"))
    reset_di_page_count()
    began = time.monotonic()
    segments = await agent._split(str(package), use_bookmarks=False, max_pages=None, concurrency=4,
                                  ocr_fallback=None)
    seconds = round(time.monotonic() - began, 1)
    pages = get_di_pages_by_model()
    out = {"engine": engine, "seconds": seconds, "segments": _segments(segments),
           "scanned_pages": _scanned_pages(package), "model_usage": tally.summary(),
           "docintel_pages": pages, "docintel_cost_usd": round(_di_cost(pages), 4)}
    out["total_cost_usd"] = round(out["model_usage"]["cost_usd"] + out["docintel_cost_usd"], 4)
    return out


FIELDS = ("property_value", "property_address", "residential_unit_count", "property_type",
          "gross_rental_income")


def _appraisal_pdf(package: Path, segments: list[dict], tmp: Path) -> Path | None:
    import fitz

    picks = [s for s in segments if s["label"] == "appraisal_report"]
    if not picks:
        return None
    seg = max(picks, key=lambda s: s["pages"][1] - s["pages"][0])
    src = fitz.open(package)
    out = fitz.open()
    out.insert_pdf(src, from_page=seg["pages"][0] - 1, to_page=seg["pages"][1] - 1)
    path = tmp / "appraisal.pdf"
    out.save(path)
    return path


def _schema():
    from pydantic import create_model

    from jazzx_sdk.pack.schemas import load_schema_model

    full = load_schema_model(SEED / "schemas" / "loan_document_fields.json")
    kept = {n: (i.annotation, i) for n, i in full.model_fields.items() if n in FIELDS}
    return create_model("Appraisal", **kept)


async def appraisal_phase(package: Path, split: dict, tmp: Path) -> dict:
    from jazzx_sdk.agents.document.agent import DocumentAgent
    from jazzx_sdk.agents.service import AgentExecutionService
    from jazzx_sdk.tools.documents.conversion import get_di_pages_by_model, reset_di_page_count

    path = _appraisal_pdf(package, split["segments"], tmp)
    if path is None:
        return {"error": "no appraisal_report segment to read"}
    schema = _schema()
    import fitz

    pages = fitz.open(path).page_count
    runs, values = {}, {}
    for name, engine, over in (
            ("vision", "vision", {}),
            ("docintel-layout", "docintel:prebuilt-layout", {}),
            ("docintel-mortgage-1004", "docintel:prebuilt-mortgage.us.1004", {})):
        tally = Tally(AgentExecutionService())
        spec = _spec(engine={"default": "auto", "by_class": {"appraisal_report": engine}},
                     vision_model=VISION_MODEL, vision_budget_usd=VISION_BUDGET_USD,
                     field_maps=FORM_MAP if name.endswith("1004") else {}, **over)
        agent = DocumentAgent(spec, agents=tally)
        if name != "docintel-mortgage-1004":
            agent._engine_override = engine
        reset_di_page_count()
        began = time.monotonic()
        try:
            result = await agent.process(str(path), schema=schema)
        except Exception as exc:  # noqa: BLE001 - aggregate only: the class, never a message
            runs[name] = {"error": type(exc).__name__}
            continue
        seconds = round(time.monotonic() - began, 1)
        pages_by_model = {**get_di_pages_by_model(), **result.di_pages}
        fields = {f.field: f for f in result.fields}
        values[name] = {k: fields[k].value for k in fields}
        runs[name] = {
            "seconds": seconds, "model_usage": tally.summary(), "docintel_pages": pages_by_model,
            "docintel_cost_usd": round(_di_cost(pages_by_model), 4),
            "fields_read": sorted(fields), "fields_refused": sorted(
                getattr(r, "domain_extensions", {}).get("field", "?") for r in result.refused),
            "unmapped_reads": len(result.unmapped_reads),
            "min_confidence": round(min((f.confidence.score for f in fields.values()), default=0), 2),
            "doc_type": result.doc_type.value if result.doc_type else None,
            "pages_read_by_engine": len(result.pages_read)}
        runs[name]["total_cost_usd"] = round(
            runs[name]["model_usage"]["cost_usd"] + runs[name]["docintel_cost_usd"], 4)

    def same(a, b, key):
        x, y = values.get(a, {}).get(key), values.get(b, {}).get(key)
        if x is None or y is None:
            return None
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return abs(x - y) <= max(abs(x) * 0.01, 1)
        return str(x).strip().casefold() == str(y).strip().casefold()

    agreement = {f"{a}~{b}": {k: same(a, b, k) for k in FIELDS}
                 for a, b in (("vision", "docintel-layout"), ("vision", "docintel-mortgage-1004"),
                              ("docintel-layout", "docintel-mortgage-1004"))}
    return {"appraisal_pages": pages, "engines": runs, "agreement": agreement}


#: Filled in after the form model's field names are known (see --names).
FORM_MAP: dict = {"prebuilt-mortgage.us.1004": {
    "Reconciliation.AppraisedMarketValue": "property_value",
    "Subject.PropertyAddress": "property_address",
    "Improvements.Type": "property_type"}}


async def names_phase(package: Path, split: dict, tmp: Path) -> dict:
    """The field NAMES a prebuilt form model returns for the appraisal (no values)."""
    from jazzx_sdk.tools.documents.docintel_azure import AzureDocIntelligenceProvider
    from jazzx_sdk.tools.documents.pages.forms import fields_from_analyze_result

    path = _appraisal_pdf(package, split["segments"], tmp)
    provider = AzureDocIntelligenceProvider(model_id="prebuilt-mortgage.us.1004")
    result = await asyncio.to_thread(provider.analyze, path.read_bytes())
    found = fields_from_analyze_result(result)
    return {"pages": len(getattr(result, "pages", None) or []),
            "field_names": sorted({f.name for f in found}), "count": len(found)}


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True,
                        choices=["split-vision", "split-docintel", "names", "appraisal"])
    parser.add_argument("--split-report", default=str(REPORT))
    args = parser.parse_args()
    _load_env()
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        package = _package(tmp)
        if args.phase.startswith("split-"):
            out = await split_phase(args.phase.split("-", 1)[1], package)
            report = json.loads(REPORT.read_text()) if REPORT.exists() else {}
            report[args.phase] = out
            REPORT.write_text(json.dumps(report, indent=2))
            print(json.dumps(out, indent=2))
            return
        report = json.loads(Path(args.split_report).read_text())
        split = report.get("split-vision") or report["split-docintel"]
        if args.phase == "names":
            print(json.dumps(await names_phase(package, split, tmp), indent=2))
            return
        out = await appraisal_phase(package, split, tmp)
        report["appraisal"] = out
        REPORT.write_text(json.dumps(report, indent=2))
        print(json.dumps(out, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
