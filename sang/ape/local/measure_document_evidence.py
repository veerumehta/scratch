"""What a page costs to classify as text versus as an image.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

The vision route was built on a claim nobody had measured: that looking at a page costs fewer
tokens than extracting its text. This settles it per corpus, because the answer depends on how
dense the pages are -- a sparse form and a wall of body text sit on opposite sides of it.

    python scripts/local/measure_document_evidence.py tests/fixtures/local/acra_godocs_mixed
    python scripts/local/measure_document_evidence.py somefile.pdf --model claude-opus-4.5

Token counts for images are the providers' published formulas, applied to the size
`tools.documents.rasterize` actually renders. Text is char/4, the SDK's own convention
(`agents.interactive.responses_compaction.estimate_tokens`) -- good to roughly 10-15% on English
prose, which is well inside the margin that matters here.

What this does **not** measure is accuracy: whether a model reads a rendered page as well as it
reads extracted text. That needs labelled documents and live calls, and no token count substitutes
for it. A cheaper route that is wrong more often is not cheaper.
"""

from __future__ import annotations

import argparse
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from jazzx_sdk.tools.documents.rasterize import dpi_for  # noqa: E402
from jazzx_sdk.tools.documents.split import page_texts  # noqa: E402

#: Azure Document Intelligence prebuilt-layout, list price per 1000 pages at time of writing.
#: Here to put the token numbers in context -- DocIntel is charged per page whatever the page holds,
#: which is the comparison a caller actually faces.
DOCINTEL_USD_PER_PAGE = 10.0 / 1000


def image_tokens(width: int, height: int, provider: str) -> int:
    """Published formulas, not estimates."""
    if provider == "anthropic":
        return round(width * height / 750)
    if provider == "openai":
        # Fit to 2048, then shortest side to 768, then 85 + 170 per 512px tile.
        scale = min(2048 / max(width, height), 1.0)
        width, height = width * scale, height * scale
        scale = min(768 / min(width, height), 1.0)
        width, height = width * scale, height * scale
        return 85 + 170 * (math.ceil(width / 512) * math.ceil(height / 512))
    if provider == "gemini":
        if width <= 384 and height <= 384:
            return 258
        return 258 * (math.ceil(width / 768) * math.ceil(height / 768))
    raise ValueError(provider)


def measure(pdf: pathlib.Path) -> list[dict]:
    import fitz

    texts = page_texts(str(pdf))
    doc = fitz.open(pdf)
    rows = []
    for index, page in enumerate(doc):
        dpi = dpi_for(page.rect.width, page.rect.height)
        width = round(page.rect.width / 72 * dpi)
        height = round(page.rect.height / 72 * dpi)
        text = texts[index] if index < len(texts) else ""
        rows.append({
            "file": pdf.name,
            "page": index,
            "chars": len(text),
            "text_tokens": len(text) // 4,
            "anthropic": image_tokens(width, height, "anthropic"),
            "openai": image_tokens(width, height, "openai"),
            "gemini": image_tokens(width, height, "gemini"),
        })
    doc.close()
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("target", help="a PDF, or a directory of them")
    ap.add_argument("--model", default="claude-opus-4.5", help="for the cost column")
    ap.add_argument("--per-page", action="store_true", help="one row per page, not a summary")
    args = ap.parse_args()

    target = pathlib.Path(args.target)
    pdfs = sorted(target.rglob("*.pdf")) if target.is_dir() else [target]
    rows = [row for pdf in pdfs for row in measure(pdf)]
    if not rows:
        print("no pages found")
        return 1

    if args.per_page:
        print(f"{'file':38} {'pg':>3} {'chars':>7} {'text':>7} {'anthr':>7} {'openai':>7} {'gemini':>7}")
        for r in rows:
            print(f"{r['file'][:38]:38} {r['page']:>3} {r['chars']:>7} {r['text_tokens']:>7} "
                  f"{r['anthropic']:>7} {r['openai']:>7} {r['gemini']:>7}")
        print()

    pages = len(rows)
    text_total = sum(r["text_tokens"] for r in rows)
    print(f"{pages} pages across {len(pdfs)} file(s)\n")
    print(f"{'evidence':22} {'tokens':>10} {'per page':>10} {'vs text':>10}")
    print("-" * 54)
    print(f"{'extracted text':22} {text_total:>10} {text_total / pages:>10.0f} {'--':>10}")
    for provider in ("anthropic", "openai", "gemini"):
        total = sum(r[provider] for r in rows)
        ratio = total / text_total if text_total else float("inf")
        print(f"{'image (' + provider + ')':22} {total:>10} {total / pages:>10.0f} {ratio:>9.2f}x")

    from jazzx_sdk.llm.cost import compute_cost

    print()
    text_cost = compute_cost(input_tokens=text_total, model_name=args.model)
    image_cost = compute_cost(input_tokens=sum(r["anthropic"] for r in rows), model_name=args.model)
    di_cost = pages * DOCINTEL_USD_PER_PAGE
    print(f"input cost for this corpus on {args.model}:")
    print(f"  extracted text        ${text_cost:.4f}")
    print(f"  rendered images       ${image_cost:.4f}")
    print(f"  DocIntel (layout)     ${di_cost:.4f}   + whatever the text then costs to classify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
