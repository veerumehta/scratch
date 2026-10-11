"""Print distinct bodies of a named evaluator method across kernel-lab evaluators.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Usage: python show_helper_bodies.py NAME [max_variants]
"""

import ast
import sys
from collections import Counter
from pathlib import Path

ROOT = Path("/Users/sangit/src/kernel-lab/codec-core/workflows/evaluators")
name, limit = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2
bodies = Counter()
example = {}
for path in ROOT.rglob("*.py"):
    if path.name.startswith("test_"):
        continue
    src = path.read_text()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            seg = ast.get_source_segment(src, node)
            key = ast.dump(node, include_attributes=False)
            bodies[key] += 1
            example.setdefault(key, (path.parent.name, seg))
print(f"{name}: {sum(bodies.values())} defs, {len(bodies)} distinct")
for key, n in bodies.most_common(limit):
    where, seg = example[key]
    print(f"--- x{n} e.g. {where}\n{seg}")
