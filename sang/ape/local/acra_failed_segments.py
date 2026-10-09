"""Why six Acra extraction segments failed: re-run only those segments, writing nothing (local).

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Reads the draft's jtbd_template from the local Plato, converts the two guideline documents, and runs
the Python extractor on the three Platinum segments (3.12 paragraphs 2 to 4) and the JTBD extractor on
the three Standard sections that failed, with the model the runs used. Prints the exception class
and message of each, which the run record does not keep; stores nothing in Plato.

    python scripts/local/acra_failed_segments.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx
import yaml

ROOT = Path("/Users/sangit/src/japes")
sys.path.insert(0, str(ROOT))
DOCS = ROOT / "documents" / "Acra"
API = "http://localhost:8000/api/v1"
HEAD = {"x-tenant-id": "acra-lending"}
PLATINUM = DOCS / "Acra_DSCR_Platinum_Select_Consolidated_Guidelines_v1_0 1.docx"
STANDARD = DOCS / "Acra_DSCR_Standard_Consolidated_Guidelines_v1_0.docx"
PY_FAILED = ["Section 3.12 ¶2", "Section 3.12 ¶3", "Section 3.12 ¶4"]
JTBD_FAILED = ["Products, interest-only terms and subordinate financing",
               "Prepayment penalty structures and state restrictions",
               "Cross-feature CLTV caps, adjustments and minimum FICO reference"]


def _template():
    from jazzx_sdk.pipelines.policy_jtbd import JtbdTemplate

    text = httpx.get(f"{API}/packs/drafts/acra-dscr-policy", headers=HEAD,
                     params={"path": "jtbd_template.yaml"}, timeout=30).json()["content"]
    return JtbdTemplate.model_validate(yaml.safe_load(text) or {})


async def main() -> None:
    from jazzx_sdk.agents.metering import CallMeter, use_meter
    from jazzx_sdk.agents.reasoning.agent import ReasoningAgent
    from jazzx_sdk.agents.service import AgentExecutionService
    from jazzx_sdk.failures import SERVED_REASON_LIMIT, reason
    from jazzx_sdk.llm.config import resolve_model
    from jazzx_sdk.pipelines.policy_code import PythonExtractor
    from jazzx_sdk.pipelines.policy_extract import ClauseSegmenter
    from jazzx_sdk.pipelines.policy_jtbd import JtbdExtractor, SectionSegmenter
    from jazzx_sdk.tools import convert_document

    template = _template()
    reasoning = ReasoningAgent(AgentExecutionService(), model=resolve_model())
    meter = CallMeter()
    report = []
    with use_meter(meter):
        docs = [(PLATINUM.name, convert_document(str(PLATINUM)))]
        segments = ClauseSegmenter().segment(docs)
        extractor = PythonExtractor(reasoning, reads=template.reads, policy_id="acra-platinum",
                                    units=template.units)
        for wanted in PY_FAILED:
            hits = [s for s in segments if (s.section or s.marker or "") .endswith(wanted.split("¶")[0].strip())
                    or wanted in s.citation]
            if not hits:
                report.append({"run": "fa8c8374 python platinum", "segment": wanted,
                               "reason": "not reproduced: no segment of that name this time"})
                continue
            for seg in hits[:1]:
                try:
                    await extractor.extract(seg)
                    report.append({"run": "fa8c8374 python platinum", "segment": wanted,
                                   "reason": "not reproduced: it extracted this time",
                                   "chars": len(seg.text)})
                except Exception as exc:  # noqa: BLE001
                    report.append({"run": "fa8c8374 python platinum", "segment": wanted,
                                   "reason": f"{type(exc).__name__}: {reason(exc, limit=SERVED_REASON_LIMIT)}",
                                   "chars": len(seg.text)})
        sdocs = [(STANDARD.name, convert_document(str(STANDARD)))]
        sections = await SectionSegmenter(reasoning, template=template).segment(sdocs)
        jx = JtbdExtractor(reasoning, template=template, policy_id="acra-standard")
        for wanted in JTBD_FAILED:
            hit = next((s for s in sections if wanted.casefold() in (s.section or s.marker or "").casefold()
                        or (s.section or s.marker or "").casefold() in wanted.casefold() and (s.section or s.marker)), None)
            if hit is None:
                report.append({"run": "230d1542 jtbd standard", "segment": wanted,
                               "reason": "not reproduced: the sectioning named it differently this time"})
                continue
            try:
                await jx.extract(hit)
                report.append({"run": "230d1542 jtbd standard", "segment": wanted,
                               "reason": "not reproduced: it extracted this time", "chars": len(hit.text)})
            except Exception as exc:  # noqa: BLE001
                report.append({"run": "230d1542 jtbd standard", "segment": wanted,
                               "reason": f"{type(exc).__name__}: {reason(exc, limit=SERVED_REASON_LIMIT)}",
                               "chars": len(hit.text)})
    for row in report:
        row["representation"] = "python" if "python" in row["run"] else "jtbd"
    Path("/tmp/cov").mkdir(exist_ok=True)
    Path("/tmp/cov/failed_segments.json").write_text(json.dumps(report, indent=2))
    cost = meter.total()
    print(json.dumps({"failed": report, "cost_usd": round(cost.get("cost_usd", 0), 4)}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
