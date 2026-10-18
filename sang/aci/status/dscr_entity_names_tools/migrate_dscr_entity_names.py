"""One-off: rename acra-dscr-policy's flat fact names to Entity.field (D2). Not SDK code.

Usage: migrate_dscr_entity_names.py <pack_dir> <gold_cases_dir>
Edits only structured positions (rule fields, metric formulas and inputs, the manifest's field
references, the job template's reads and units, the registry's yields, gold-case records); prose
and comments are left for a person.
"""
import json
import re
import sys
from pathlib import Path

from jaci.scenarios.dscr.schemas.dscr_schemas import CLTV, DSCR, ENTITY_NAMES

NAMES = {**ENTITY_NAMES, "cltv_pct": CLTV, "dscr": DSCR}
TOKEN = re.compile(r"(?<![\w.])(" + "|".join(sorted(map(re.escape, NAMES), key=len, reverse=True)) + r")(?![\w.])")


def sub(text: str) -> str:
    return TOKEN.sub(lambda m: NAMES[m.group(1)], text)


def code_part(line: str) -> tuple[str, str]:
    """A YAML line split into its content and a trailing comment (no quoted '#' in these files)."""
    i = line.find(" #")
    return (line, "") if line.lstrip().startswith("#") else ((line[:i], line[i:]) if i >= 0 else (line, ""))


def rewrite(path: Path, keep) -> int:
    lines, n, out = path.read_text().splitlines(keepends=True), 0, []
    state = {"block": None}
    for line in lines:
        body, comment = code_part(line)
        if not line.lstrip().startswith("#") and keep(body, state):
            new = sub(body)
            n += new != body
            body = new
        out.append(body + comment if comment else body)
    path.write_text("".join(out))
    return n


FIELD_KEYS = re.compile(r"^\s*-?\s*(field|compare_field|numerator|denominator):\s")


def policy_line(body, state):
    return bool(FIELD_KEYS.match(body))


def metrics_line(body, state):
    return bool(re.match(r"^\s*-?\s*(id|formula|inputs):|^\s*- \{name:", body))


def manifest_line(body, state):
    return "compose_caps:" in body or "when: {" in body


def template_line(body, state):
    m = re.match(r"^([a-z_]+):", body)
    if m:
        state["block"] = m.group(1)
    return state["block"] in ("reads", "units") and not m


def registry_line(body, state):
    if re.match(r"^\s*-?\s*[a-z_]+:", body):
        state["block"] = "yields" if re.match(r"^\s*yields:", body) else None
    return state["block"] == "yields"


def main(pack: Path, gold: Path) -> None:
    counts = {}
    for p in sorted((pack / "policies").glob("*.yaml")):
        counts[p.name] = rewrite(p, policy_line)
    counts["metrics.yaml"] = rewrite(pack / "metrics.yaml", metrics_line)
    counts["pack_manifest.yaml"] = rewrite(pack / "pack_manifest.yaml", manifest_line)
    counts["jtbd_template.yaml"] = rewrite(pack / "jtbd_template.yaml", template_line)
    counts["document_types.yaml"] = rewrite(pack / "document_types.yaml", registry_line)
    for p in sorted(gold.glob("*.json")):
        case = json.loads(p.read_text())
        case["loan_application"] = {NAMES.get(k, k): v for k, v in case["loan_application"].items()}
        p.write_text(json.dumps(case, indent=2) + "\n")
        counts[p.name] = len(case["loan_application"])
    for k, v in counts.items():
        print(f"{v:5}  {k}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
