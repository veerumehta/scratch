"""Switch every `node -e <script>` test call to the stdin helper `run_node` (tests/page_scripts.py).

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Run from the checkout to change: python3 scripts/local/switch_node_stdin.py [checkout]. Edits tests only and prints the
files it changed. A long generated script does not fit in one argv element on Linux (about 128 KB), so node reads it on stdin.
"""

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
HELPER = '''

def run_node(source: str, *, timeout: float | None = None, check: bool = False, module: bool = False) -> subprocess.CompletedProcess:
    """Run ``source`` in node with the script on stdin: a long generated script does not fit in one argv element (Linux
    limits each to about 128 KB), and stdin has no such limit."""
    command = ["node", *(["--input-type=module"] if module else []), "-"]
    return subprocess.run(command, input=source, capture_output=True, text=True, timeout=timeout, check=check)
'''
IMPORT = "from tests.page_scripts import run_node"

helper = ROOT / "tests/page_scripts.py"
text = helper.read_text()
if "def run_node" not in text:
    text = text.replace("from html.parser import HTMLParser\n", "import subprocess\nfrom html.parser import HTMLParser\n", 1)
    helper.write_text(text.rstrip("\n") + "\n" + HELPER)

files = subprocess.run(["grep", "-rl", '"-e"', "tests", "--include=*.py"], capture_output=True, text=True, cwd=ROOT).stdout.split()
changed = []
for name in files:
    path = ROOT / name
    source = path.read_text()
    new = source
    new = new.replace('subprocess.run(["node", "-e", source], capture_output=True, text=True, timeout=60)', "run_node(source, timeout=60)")
    new = new.replace('subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)', "run_node(script, check=True)")
    new = re.sub(r'subprocess\.run\(\["node", "-e", script\], capture_output=True, text=True,\n\s+check=True\)', "run_node(script, check=True)", new)
    new = new.replace('subprocess.run(["node", "-e", program], capture_output=True, text=True, check=True)', "run_node(program, check=True)")
    new = re.sub(r'subprocess\.run\(\["node", "--input-type=module", "-e", program\],\n\s+capture_output=True, text=True, timeout=30\)',
                 "run_node(program, timeout=30, module=True)", new)
    if new == source:
        continue
    if name == "tests/test_plato_info_api.py":
        new = new.replace("    out = run_node(program, check=True)", f"    {IMPORT}\n\n    out = run_node(program, check=True)", 1)
    elif "import run_node" not in new and ", run_node" not in new:
        found = re.search(r"^from tests\.page_scripts import (.+)$", new, re.M)
        if found:
            new = new.replace(found.group(0), f"{found.group(0)}, run_node", 1)
        else:
            lines = new.split("\n")
            last = max(i for i, line in enumerate(lines) if re.match(r"(from|import) ", line))
            lines.insert(last + 1, IMPORT)
            new = "\n".join(lines)
    path.write_text(new)
    changed.append(name)

if changed:
    # only the files this script edited: a wider run would re-sort imports across the whole tree
    subprocess.run(["ruff", "check", "--select", "I,F401,F811", "--fix", "tests/page_scripts.py", *changed], cwd=ROOT)
print(len(changed), "files changed")
print("\n".join(changed))
left = subprocess.run(["grep", "-rn", '"-e"', "tests"], capture_output=True, text=True, cwd=ROOT).stdout
print("remaining node -e call sites:", len(left.splitlines()))
