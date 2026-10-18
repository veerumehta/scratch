"""Compare before/after DSCR assessments through the flat -> Entity.field mapping."""
import json, re, sys
from jaci.scenarios.dscr.schemas.dscr_schemas import CLTV, DSCR, ENTITY_NAMES

NAMES = {**ENTITY_NAMES, "cltv_pct": CLTV, "dscr": DSCR}
TOK = re.compile(r"(?<![\w.])(" + "|".join(sorted(map(re.escape, NAMES), key=len, reverse=True)) + r")(?![\w.])")
VOLATILE = {"assessed_at", "run_id", "trace_id", "timestamp", "created_at", "id"}


def scrub(x):
    if isinstance(x, dict):
        return {k: scrub(v) for k, v in x.items() if k not in VOLATILE}
    if isinstance(x, list):
        return [scrub(v) for v in x]
    return x


FIELDS = re.compile(r"((?:[\w.]+, )+[\w.]+)(?= = not satisfied)")


def order_free(x):
    """A compound rule's field list ("a, b = ...") in sorted order: it is listed sorted by name,
    so renaming reorders it without changing which fields it names."""
    if isinstance(x, dict):
        return {k: (", ".join(sorted(v.split(", "))) if k == "field" and isinstance(v, str)
                    else order_free(v)) for k, v in x.items()}
    if isinstance(x, list):
        return [order_free(v) for v in x]
    if isinstance(x, str):
        return FIELDS.sub(lambda m: ", ".join(sorted(m.group(1).split(", "))), x)
    return x


def renamed(x):
    """Every flat name, as a key or anywhere in a string, in its entity spelling."""
    if isinstance(x, dict):
        return {TOK.sub(lambda m: NAMES[m.group(1)], k): renamed(v) for k, v in x.items()}
    if isinstance(x, list):
        return [renamed(v) for v in x]
    if isinstance(x, str):
        return TOK.sub(lambda m: NAMES[m.group(1)], x)
    return x


def key(record):
    return json.dumps({NAMES.get(k, k): v for k, v in record.items() if k != "submission_date"},
                      sort_keys=True, default=str)


before = {key(r["record"]): scrub(r["answer"]) for r in map(json.loads, open(sys.argv[1]))}
after = {key(r["record"]): scrub(r["answer"]) for r in map(json.loads, open(sys.argv[2]))}
same = differ = 0
missing = [k for k in before if k not in after]
for k, b in before.items():
    if k not in after:
        continue
    if order_free(renamed(b)) == order_free(after[k]):
        same += 1
    else:
        differ += 1
        if differ <= 3:
            bb, aa = order_free(renamed(b)), order_free(after[k])
            for f in bb:
                if bb[f] != aa.get(f):
                    print("DIFF", f, json.dumps(bb[f], default=str)[:400], "\n  vs", json.dumps(aa.get(f), default=str)[:400])
print(f"records: before {len(before)}, after {len(after)}, compared {same + differ}, identical {same}, differ {differ}, unmatched {len(missing)}")
for k in missing[:3]:
    print("UNMATCHED", k[:300])
