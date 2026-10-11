"""Count repeated helper patterns in kernel-lab's mortgage evaluators (codec-core).

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Usage: python mine_kernel_lab_mortgage.py [evaluators_dir]
"""

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else
            "/Users/sangit/src/kernel-lab/codec-core/workflows/evaluators")
FILES = sorted(p for p in ROOT.rglob("*.py") if not p.name.startswith("test_"))

PATTERNS = {
    "abs-diff tolerance compare": r"abs\([^)]*-[^)]*\)\s*(<=|<|>|>=)",
    "TOLERANCE constant": r"TOLERANCE\w*\s*=|_TOL\s*=",
    ".quantize(": r"\.quantize\(",
    "round(": r"(?<![\w.])round\(",
    "x100 or /100 (percent)": r"(/|\*)\s*(Decimal\(\"100\"\)|100\b)",
    "x12 or /12 (monthly/annual)": r"(/|\*)\s*(Decimal\(\"12\"\)|12\b)",
    "sum(": r"(?<![\w.])sum\(",
    "timedelta/relativedelta": r"relativedelta|timedelta\(",
    ".days": r"\.days\b",
    "fromisoformat/strptime": r"fromisoformat|strptime",
    "today/now": r"date\.today|datetime\.now|utcnow",
    "MONTHS/DAYS constant": r"_(MONTHS|DAYS)\w*\s*=",
    "max/min(key=) latest": r"(max|min)\([^)]*key\s*=",
    "Decimal(str(": r"Decimal\(str\(",
    ".upper() token": r"\.upper\(\)",
    "re.sub non-alnum": r"re\.sub\(r?[\"']\[\^A-Za-z0-9",
}


def main():
    print(f"files: {len(FILES)}")
    defs, module_defs = Counter(), Counter()
    def_files = {}
    for path in FILES:
        text = path.read_text()
        for name in set(re.findall(r"^    (?:async )?def (\w+)", text, re.M)):
            defs[name] += 1
            def_files.setdefault(name, path)
        for name in set(re.findall(r"^def (\w+)", text, re.M)):
            module_defs[name] += 1
    print("\n# methods defined in >=3 evaluators")
    for name, n in defs.most_common():
        if n >= 3:
            print(f"{n:4} {name}")
    print("\n# module-level defs in >=3 evaluators")
    for name, n in module_defs.most_common():
        if n >= 3:
            print(f"{n:4} {name}")
    print("\n# inline patterns (files, hits)")
    for label, pat in PATTERNS.items():
        rx = re.compile(pat)
        hits = [len(rx.findall(p.read_text())) for p in FILES]
        print(f"{sum(1 for h in hits if h):4} files {sum(hits):5} hits  {label}")


if __name__ == "__main__":
    main()
