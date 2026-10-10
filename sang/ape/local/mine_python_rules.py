#!/usr/bin/env python3
"""R0 mining: what generated Python rules repeat, and the baseline metrics a trial would compute.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Reads the python rule proposals through a Plato's API (read-only, no model calls), analyses each
rule's source with `ast`, runs each rule's own generated cases through the executor, and writes an
aggregate report. Rule text is policy, not borrower data; nothing here reads a document.

    mine_python_rules.py --base http://localhost:8000/api/v1 --pack acra-dscr-policy \
        --tenant acra-lending --schema plato/data/seed_packs/acra_dscr_policy/schemas/loan_application.json \
        --out ape/local/mining
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import collections
import json
import re
import statistics
import urllib.request
from pathlib import Path

DATE_NAMES = {"datetime", "date", "strptime", "fromisoformat", "timedelta", "days", "months"}
NORMALIZERS = {"lower", "upper", "strip", "casefold", "title"}
ROUNDERS = {"round", "quantize", "Decimal", "Fraction", "floor", "ceil", "isclose"}
UNKNOWN_RETURNS = {"None", "'unknown'"}
UNIT_WORDS = re.compile(r"(pct|percent|ratio|bps|rate|_x$)", re.I)


def fetch(base: str, pack: str, tenant: str) -> list[dict]:
    request = urllib.request.Request(f"{base}/authoring/review/{pack}/proposals?kind=rule&limit=5000",
                                     headers={"x-tenant-id": tenant})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


class Analysis(ast.NodeVisitor):
    def __init__(self, ctx: str) -> None:
        self.ctx = ctx
        self.returns: collections.Counter = collections.Counter()
        self.subscript_reads: set[str] = set()
        self.get_reads: set[str] = set()
        self.none_guards = 0
        self.normalizers: collections.Counter = collections.Counter()
        self.rounders: collections.Counter = collections.Counter()
        self.date_uses = 0
        self.divisions = 0
        self.hundreds = 0
        self.helpers = 0
        self.imports: set[str] = set()
        self.compares: collections.Counter = collections.Counter()
        self.enum_literals: dict[str, set[str]] = collections.defaultdict(set)
        self.vars_from_ctx: dict[str, str] = {}
        self.chain_vars: collections.Counter = collections.Counter()
        self.membership = 0
        self.bool_compare = 0

    # ctx reads
    def visit_Assign(self, node: ast.Assign) -> None:
        field = self._ctx_field(node.value)
        if field:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.vars_from_ctx[target.id] = field
        self.generic_visit(node)

    def _ctx_field(self, node: ast.AST) -> str | None:
        if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
                and node.value.id == self.ctx and isinstance(node.slice, ast.Constant)):
            return str(node.slice.value)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get" and isinstance(node.func.value, ast.Name)
                and node.func.value.id == self.ctx and node.args
                and isinstance(node.args[0], ast.Constant)):
            return str(node.args[0].value)
        return None

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if (field := self._ctx_field(node)):
            self.subscript_reads.add(field)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if (field := self._ctx_field(node)):
            self.get_reads.add(field)
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if name in NORMALIZERS:
            self.normalizers[name] += 1
        if name in ROUNDERS:
            self.rounders[name] += 1
        if name in DATE_NAMES:
            self.date_uses += 1
        if name == "bool":
            self.bool_compare += 1
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in DATE_NAMES:
            self.date_uses += 1
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name != "check":
            self.helpers += 1
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        self.imports.update(a.name for a in node.names)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.imports.add(node.module or "")

    def visit_Return(self, node: ast.Return) -> None:
        v = node.value
        if isinstance(v, ast.Tuple) and v.elts:
            v = v.elts[0]        # the convention is (verdict, values)
        key = repr(v.value) if isinstance(v, ast.Constant) else type(v).__name__ if v else "None"
        self.returns[key] += 1
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        if isinstance(node.op, (ast.Div, ast.FloorDiv)):
            self.divisions += 1
        for side in (node.left, node.right):
            if isinstance(side, ast.Constant) and side.value in (100, 100.0):
                self.hundreds += 1
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        operands = [node.left, *node.comparators]
        for op, a, b in zip(node.ops, operands, operands[1:]):
            self.compares[type(op).__name__] += 1
            if isinstance(op, (ast.Is, ast.IsNot)) and any(
                    isinstance(x, ast.Constant) and x.value is None for x in (a, b)):
                self.none_guards += 1
            if isinstance(op, (ast.In, ast.NotIn)):
                self.membership += 1
            for var, lit in ((a, b), (b, a)):
                if isinstance(lit, ast.Constant) and lit.value in (True, False) and lit.value is not None \
                        and isinstance(lit.value, bool):
                    self.bool_compare += 1
                field = self._field_of(var)
                if field:
                    for const in _strings(lit):
                        self.enum_literals[field].add(const)
                    if isinstance(lit, ast.Constant) and isinstance(lit.value, (int, float)) \
                            and not isinstance(lit.value, bool):
                        self.chain_vars[field] += 1
        self.generic_visit(node)

    def _field_of(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return self.vars_from_ctx.get(node.id)
        return self._ctx_field(node)


def _strings(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return [e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
    return []


def analyse(source: str) -> Analysis | None:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    function = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "check"), None)
    if function is None or not function.args.args:
        return None
    analysis = Analysis(function.args.args[0].arg)
    analysis.visit(tree)
    return analysis


async def run_cases(source: str, entrypoint: str, cases: list[dict]) -> dict:
    from jazzx_sdk.fabric.canonical.local_executor import LocalExecutorError, LocalPythonExecutor

    executor = LocalPythonExecutor()
    outcome = collections.Counter()
    boundary_misses = 0
    for case in cases:
        try:
            got = await executor.run(source, entrypoint, case["context"])
        except LocalExecutorError as exc:
            outcome["raised"] += 1
            if "KeyError" in str(exc):
                outcome["keyerror"] += 1
            continue
        if isinstance(got, (tuple, list)) and got:
            got = got[0]
        verdict = ("satisfied" if got is True else "violated" if got is False else "indeterminate")
        want = case.get("expected")
        outcome["agrees" if verdict == want else "disagrees"] += 1
    outcome["boundary_misses"] = boundary_misses
    return dict(outcome)


def case_variants(per_field: dict[str, set[str]]) -> dict[str, list[str]]:
    """Fields compared to values that differ only by case or separators across the rules."""
    out = {}
    for field, values in per_field.items():
        groups: dict[str, set[str]] = collections.defaultdict(set)
        for v in values:
            groups[re.sub(r"[\s_\-]+", "", v).casefold()].add(v)
        spread = sorted(v for g in groups.values() if len(g) > 1 for v in g)
        if spread:
            out[field] = spread
    return out


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8000/api/v1")
    parser.add_argument("--pack", default="acra-dscr-policy")
    parser.add_argument("--tenant", default="acra-lending")
    parser.add_argument("--schema", default="")
    parser.add_argument("--metrics", default="", help="metrics.yaml: derived names count as available")
    parser.add_argument("--out", default="mining")
    args = parser.parse_args()

    proposals = fetch(args.base, args.pack, args.tenant)
    rules = [p for p in proposals if p["kind"] == "rule"]
    python = [p for p in rules if (p["rule"]["condition"] or {}).get("kind") == "python"]
    schema_fields = set()
    if args.schema:
        schema_fields = set(json.loads(Path(args.schema).read_text()).get("properties", {}))
    if args.metrics:
        schema_fields |= set(re.findall(r"^\s*-\s*id:\s*(\S+)", Path(args.metrics).read_text(), re.M))

    per_rule, all_enums = [], collections.defaultdict(set)
    totals: collections.Counter = collections.Counter()
    read_freq: collections.Counter = collections.Counter()
    case_totals: collections.Counter = collections.Counter()
    for p in python:
        cond = p["rule"]["condition"]
        a = analyse(cond["source"])
        if a is None:
            totals["unparseable"] += 1
            continue
        reads = list(cond.get("reads") or [])
        read_freq.update(reads)
        for f, vals in a.enum_literals.items():
            all_enums[f] |= vals
        accessed = a.subscript_reads | a.get_reads
        ran = await run_cases(cond["source"], cond.get("entrypoint", "check"), cond.get("cases") or [])
        case_totals.update(ran)
        row = {
            "set": p["set_id"], "reads": len(reads), "undeclared": sorted(accessed - set(reads)),
            "unused_reads": sorted(set(reads) - accessed),
            "hard_reads": len(a.subscript_reads), "soft_reads": len(a.get_reads),
            "returns": dict(a.returns), "none_guards": a.none_guards,
            "normalizers": dict(a.normalizers), "rounders": dict(a.rounders),
            "date_uses": a.date_uses, "divisions": a.divisions, "hundreds": a.hundreds,
            "helpers": a.helpers, "imports": sorted(a.imports), "compares": dict(a.compares),
            "membership": a.membership, "cases": len(cond.get("cases") or []),
            "unknown_reads": sorted(set(reads) - schema_fields) if schema_fields else [],
            "case_outcomes": ran, "source_lines": len(cond["source"].splitlines()),
        }
        per_rule.append(row)
        totals["rules"] += 1
        totals["has_false_return"] += "False" in a.returns
        totals["has_true_return"] += "True" in a.returns
        totals["has_other_return"] += any(k not in ("True", "False") for k in a.returns)
        totals["uses_hard_read"] += bool(a.subscript_reads)
        totals["uses_none_guard"] += bool(a.none_guards)
        totals["uses_normalizer"] += bool(a.normalizers)
        totals["uses_rounding"] += bool(a.rounders)
        totals["uses_dates"] += bool(a.date_uses)
        totals["uses_division"] += bool(a.divisions)
        totals["uses_hundred_units"] += bool(a.hundreds)
        totals["defines_helper"] += bool(a.helpers)
        totals["imports_anything"] += bool(a.imports)
        totals["uses_membership"] += bool(a.membership)
        totals["reads_not_in_schema"] += bool(row["unknown_reads"])
        totals["undeclared_access"] += bool(row["undeclared"])
        totals["all_reads_in_schema"] += (not row["unknown_reads"]) if schema_fields else 0

    n = max(totals["rules"], 1)
    pct = lambda k: f"{100 * totals[k] / n:.0f}% ({totals[k]}/{n})"
    kinds = collections.Counter((p["rule"]["condition"] or {}).get("kind") for p in rules)
    lines_of = [r["source_lines"] for r in per_rule]
    variants = case_variants(all_enums)
    case_n = sum(v for k, v in case_totals.items() if k in ("agrees", "disagrees", "raised"))

    report = [
        "# R0 mining: generated Python rules",
        "",
        f"Source: {args.base}, pack {args.pack}, tenant {args.tenant}. {len(rules)} rule proposals, "
        f"{len(python)} Python ({', '.join(f'{k} {v}' for k, v in sorted(collections.Counter(p['set_id'] for p in python).items()))}). "
        f"Rule kinds: {dict(kinds)}.",
        "",
        "## Metric baseline (R0 share of section 10)",
        "",
        f"- Deterministic share (rung 1 or 2: conditions and procedures over all rule proposals): "
        f"{sum(v for k, v in kinds.items() if k != 'python')}/{len(rules)} "
        f"({100 * sum(v for k, v in kinds.items() if k != 'python') / max(len(rules), 1):.0f}%)",
        f"- Computable coverage by schema (every read is a field of the loan application schema): "
        + (f"{totals['all_reads_in_schema']}/{n}" if schema_fields else "not computed (no --schema)"),
        f"- Indeterminate honesty: rules whose verdict can be something other than True/False "
        f"(None, 'unknown'): {sum(1 for r in per_rule if set(r['returns']) & UNKNOWN_RETURNS)}/{n}; "
        f"rules whose verdict is an expression (Compare/BoolOp/Name): "
        f"{sum(1 for r in per_rule if set(r['returns']) - {'True', 'False'})}/{n}",
        f"- Generated cases: {case_totals.get('agrees', 0)} agree with the rule, "
        f"{case_totals.get('disagrees', 0)} disagree, {case_totals.get('raised', 0)} raised "
        f"({case_totals.get('keyerror', 0)} KeyError) of {case_n}",
        "- Trial pass rate on gold and false fails at boundaries need real or synthetic document cases "
        "(R3); the generated cases above are the rule's own and prove less.",
        "",
        "## What the rules repeat (share of Python rules)",
        "",
        f"| Pattern | Rules |",
        f"|---|---|",
        f"| reads a field with `ctx['x']` (KeyError when the field is missing) | {pct('uses_hard_read')} |",
        f"| guards a read against None | {pct('uses_none_guard')} |",
        f"| compares to string literals (enum values) | {sum(1 for r in per_rule if r['compares'].get('Eq') or r['compares'].get('In'))}/{n} use ==/in |",
        f"| normalises text (lower, strip, upper) | {pct('uses_normalizer')} |",
        f"| rounds or uses Decimal/Fraction | {pct('uses_rounding')} |",
        f"| handles dates | {pct('uses_dates')} |",
        f"| divides (ratios) | {pct('uses_division')} |",
        f"| converts units with 100 | {pct('uses_hundred_units')} |",
        f"| membership tests (in a list or set) | {pct('uses_membership')} |",
        f"| defines its own helper function | {pct('defines_helper')} |",
        f"| imports a module | {pct('imports_anything')} |",
        f"| accesses a field not in its `reads` | {pct('undeclared_access')} |",
        f"| reads a field the loan schema does not have | {pct('reads_not_in_schema')} |",
        "",
        f"Return values across rules: {dict(sum((collections.Counter(r['returns']) for r in per_rule), collections.Counter()))}.",
        f"Rule length: median {statistics.median(lines_of) if lines_of else 0} lines, max {max(lines_of, default=0)}.",
        f"Imports used: {dict(sum((collections.Counter(r['imports']) for r in per_rule), collections.Counter()))}.",
        f"Comparison operators: {dict(sum((collections.Counter(r['compares']) for r in per_rule), collections.Counter()))}.",
        "",
        "## Enum literals that differ only by case or separator across rules",
        "",
    ]
    report += [f"- `{f}`: {', '.join(repr(v) for v in vals)}" for f, vals in sorted(variants.items())] \
        or ["- none"]
    report += ["", "## Most read fields", ""]
    report += [f"- `{f}`: {c} rules" for f, c in read_freq.most_common(15)]
    unknown = collections.Counter(f for r in per_rule for f in r["unknown_reads"])
    if unknown:
        report += ["", "## Reads that are not fields of the loan application schema", ""]
        report += [f"- `{f}`: {c} rules" for f, c in unknown.most_common(20)]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "r0_report.md").write_text("\n".join(report) + "\n")
    (out / "r0_per_rule.json").write_text(json.dumps(per_rule, indent=1))
    print("\n".join(report))


if __name__ == "__main__":
    asyncio.run(main())
