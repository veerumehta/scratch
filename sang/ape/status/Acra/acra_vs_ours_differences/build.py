"""Build the HTML and Excel versions of the Acra-versus-ours differences note from its markdown.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Usage: python3 build.py   (reads docs/status/note_acra_vs_ours_differences_and_provenance.md, writes beside this file)
"""
import re
import shutil
from pathlib import Path

from markdown_it import MarkdownIt
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HERE = Path(__file__).parent
SOURCE = HERE.parents[1] / "note_acra_vs_ours_differences_and_provenance.md"
NAME = "acra_vs_ours_differences_and_provenance"
MAX_SHEET = 31
WIDTH_CAP, WIDTH_MIN = 60, 10

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Acra against ours: differences and provenance</title>
<style>
:root{color-scheme:light dark;--line:#8886;--head:#8882;--zebra:#8881}
body{font:15px/1.5 system-ui,sans-serif;margin:0 auto;padding:1rem 1.5rem 4rem;max-width:110rem}
h1,h2,h3{line-height:1.25} h2{margin-top:2.5rem;border-bottom:1px solid var(--line)}
nav{position:sticky;top:0;background:Canvas;padding:.4rem 0;border-bottom:1px solid var(--line);z-index:5;font-size:14px}
nav a{margin-right:1rem;white-space:nowrap}
.wrap{overflow-x:auto;margin:1rem 0}
table{border-collapse:collapse;min-width:100%}
th,td{border:1px solid var(--line);padding:.35rem .6rem;text-align:left;vertical-align:top;min-width:7rem;max-width:36rem}
th{background:var(--head);position:sticky;top:0}
tbody tr:nth-child(even){background:var(--zebra)}
td:first-child{min-width:2.5rem}
code{background:var(--head);padding:0 .25em;border-radius:3px;font-size:.92em}
</style></head><body>
{nav}
{body}
</body></html>
"""


def plain(text: str) -> str:
    """Inline markdown to plain text."""
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    return re.sub(r"\*([^*]+)\*", r"\1", text)


def sheet_title(heading: str, used: set[str]) -> str:
    base = re.sub(r"[\[\]:*?/\\]", "", plain(heading))[:MAX_SHEET].strip() or "Sheet"
    title, n = base, 2
    while title in used:
        suffix = f" {n}"
        title, n = base[: MAX_SHEET - len(suffix)] + suffix, n + 1
    used.add(title)
    return title


def parse(text: str):
    """The note as headings, tables and prose blocks: [(heading, kind, payload)]."""
    md = MarkdownIt("commonmark").enable("table")
    tokens = md.parse(text)
    out, heading, i = [], "Overview", 0
    while i < len(tokens):
        t = tokens[i]
        if t.type == "heading_open":
            heading = plain(tokens[i + 1].content)
            level = int(t.tag[1])
            out.append((heading, "heading", level))
        elif t.type == "table_open":
            rows, row = [], None
            while tokens[i].type != "table_close":
                tk = tokens[i]
                if tk.type == "tr_open":
                    row = []
                elif tk.type == "inline" and row is not None:
                    row.append(plain(tk.content))
                elif tk.type == "tr_close":
                    rows.append(row)
                i += 1
            out.append((heading, "table", rows))
        elif t.type in ("paragraph_open", "bullet_list_open", "ordered_list_open"):
            close = t.type.replace("_open", "_close")
            lines, depth = [], 0
            while True:
                tk = tokens[i]
                if tk.type == t.type:
                    depth += 1
                elif tk.type == close:
                    depth -= 1
                    if depth == 0:
                        break
                elif tk.type == "inline":
                    lines.append(plain(tk.content))
                i += 1
            out.append((heading, "text", lines))
        i += 1
    return out


def build_html(text: str) -> None:
    body = MarkdownIt("commonmark").enable("table").render(text)
    body = re.sub(r"<table>", '<div class="wrap"><table>', body).replace("</table>", "</table></div>")
    heads = re.findall(r"<h2>(.*?)</h2>", body)
    ids = {}
    for h in heads:
        slug = re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", h).lower()).strip("-")
        ids[h] = slug
        body = body.replace(f"<h2>{h}</h2>", f'<h2 id="{slug}">{h}</h2>', 1)
    nav = "<nav>" + "".join(f'<a href="#{s}">{re.sub(r"<[^>]+>", "", h)[:38]}</a>' for h, s in ids.items()) + "</nav>"
    (HERE / f"{NAME}.html").write_text(PAGE.replace("{nav}", nav).replace("{body}", body))


def build_xlsx(text: str) -> None:
    wb = Workbook()
    wb.remove(wb.active)
    used: set[str] = set()
    blocks = parse(text)
    # one sheet per table, named by its nearest heading; prose goes to "Text"
    head_fill = PatternFill("solid", fgColor="D9D9D9")
    counts: dict[str, int] = {}
    for heading, kind, payload in blocks:
        if kind != "table":
            continue
        counts[heading] = counts.get(heading, 0) + 1
        ws = wb.create_sheet(sheet_title(heading if counts[heading] == 1 else f"{heading} {counts[heading]}", used))
        widths = {}
        for r, row in enumerate(payload, 1):
            for c, value in enumerate(row, 1):
                cell = ws.cell(row=r, column=c, value=value)
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                widths[c] = max(widths.get(c, WIDTH_MIN), min(len(value) // 2 + 2, WIDTH_CAP))
                if r == 1:
                    cell.font, cell.fill = Font(bold=True), head_fill
        for c, w in widths.items():
            ws.column_dimensions[get_column_letter(c)].width = w
        ws.freeze_panes = "B2"
    ws = wb.create_sheet(sheet_title("Text", used), 0)
    ws.column_dimensions["A"].width = 40
    ws.column_dimensions["B"].width = 140
    row = 1
    for heading, kind, payload in blocks:
        if kind == "heading":
            ws.cell(row=row, column=1, value=heading).font = Font(bold=True, size=14 - min(payload, 3) * 2)
            row += 1
        elif kind == "text":
            for line in payload:
                cell = ws.cell(row=row, column=2, value=line)
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                row += 1
    wb.save(HERE / f"{NAME}.xlsx")


def main() -> None:
    text = SOURCE.read_text()
    shutil.copy(SOURCE, HERE / f"{NAME}.md")
    build_html(text)
    build_xlsx(text)
    print("wrote", *(p.name for p in sorted(HERE.glob(f"{NAME}.*"))))


if __name__ == "__main__":
    main()
