"""Catalog and field coverage for a lender pack, from the ontology and the JTBD set only.

Usage: PYTHONPATH=<japes worktree> python packs_catalog_and_coverage.py <lender> <jtbds.json> <pack dir> (the pack folder from packs_build_pack.py)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>
"""
import json, re, sys, hashlib, collections
from pathlib import Path
import yaml
from jazzx_sdk.pack.catalog_adopt import adopt
from jazzx_sdk.pack.catalog import entity_properties, is_entity
from packs_res import split

ONT = Path("/Users/sangit/src/policy-workbench/backend/policyforge/prompts/ontology/mortgage_ontology_v2.json")
REF_ID = "mortgage-ontology@2.0.0"
B = Path("/Users/sangit/src/kernel-lab/codec-suite/workflows/customers/")

def job_text(j):
    parts = [j.get("skill", "")] + [r.get("requirement_text", "") for r in j.get("requirements") or []]
    return "\n".join(parts)

def reads_of(j, entities_fields):
    declared = list(dict.fromkeys(m["metric_key"] for m in (j.get("loan_metrics") or []) if m.get("metric_key")))
    names = "|".join(sorted(entities_fields, key=len, reverse=True))
    text = job_text(j)
    mentioned = sorted({f"{e}.{f}" for e, f in re.findall(rf"\b({names})(?:\[[^\]]*\])?\.([a-z][a-z0-9_]*)", text)})
    return declared, mentioned

def main(lender, jtbds, pack):
    ont = json.loads(ONT.read_text()); raw = ONT.read_bytes()
    defs = ont["$defs"]
    ent_fields = {}
    for name, spec in defs.items():
        if is_entity(spec):
            ent_fields[name] = set(entity_properties(spec, defs)[0])
    S = json.loads(Path(jtbds).read_text())["values"]
    rows = []
    used = collections.Counter()
    for j in S:
        declared, mentioned = reads_of(j, ent_fields)
        def ok(k):
            e, f = split(k); top = f.split(".")[0].split("[")[0] if f else ""
            filt = re.match(r"^[A-Za-z_]+\[([^\]]*)\]", k)
            filtered = [c.strip().split("=")[0].rstrip("!<>").strip() for c in filt.group(1).split(",")] if filt else []
            return e in ent_fields and (not top or top in ent_fields[e]) and all(c in ent_fields[e] for c in filtered)
        dres = {k: ok(k) for k in declared}
        mres = {k: ok(k) for k in mentioned}
        allk = {**dres, **mres}
        for k in allk: used[split(k)[0]] += 1
        status = ("no reads named" if not allk else "fully mapped" if all(allk.values()) else "partly mapped")
        rows.append({"job": j["mnemonic"], "section": j["section"], "status": status,
                     "declared_reads": declared, "text_named_reads": [k for k in mentioned if k not in set(split(d)[0] + "." + split(d)[1] for d in declared)],
                     "unmapped": sorted(k for k, v in allk.items() if not v)})
    named = sorted({split(k)[0] for r in rows for k in r["declared_reads"] + r["text_named_reads"] if split(k)[0] in ent_fields})
    entities = sorted(ent_fields)
    catalog = {"$schema": ont["$schema"], "title": f"{lender} home mortgage catalog", "version": "0.1.0", "$defs": defs}   # the title and version are the pack's; $defs is the ontology's, unedited
    catalog["x-provenance"] = {"source_file": "mortgage_ontology_v2.json", "source_id": ont.get("$id"),
        "source_version": ont.get("version"), "source_sha256": hashlib.sha256(raw).hexdigest(),
        "scope": f"all {len(entities)} entities of the ontology with every field; entities_read lists the {len(named)} the JTBD set names in its loan_metrics or text",
        "entities_read": named, "status": "policy-workbench copy of the mortgage ontology v2; not confirmed against the snapshot Codec reads"}
    (pack / "catalog.schema.json").write_text(json.dumps(catalog, indent=2))
    m = yaml.safe_load((pack / "pack_manifest.yaml").read_text()); m["catalog"] = "catalog.schema.json"
    (pack / "pack_manifest.yaml").write_text(yaml.safe_dump(m, sort_keys=False, allow_unicode=True))
    (pack / "coverage").mkdir(exist_ok=True)
    counts = collections.Counter(r["status"] for r in rows)
    summary = {"jobs": len(rows), "by_status": dict(counts),
               "declared_read_keys": len({k for r in rows for k in r["declared_reads"]}),
               "text_named_read_keys": len({k for r in rows for k in r["text_named_reads"]}),
               "unmapped_keys": sorted({k for r in rows for k in r["unmapped"]}),
               "entities": entities, "entities_read": named,
               "mapping": "Each read is Entity.field in the ontology; the snapshot path is assumed identical (not checked against a snapshot, which is loan data)",
               "inputs": ["the policy-workbench copy of mortgage_ontology_v2.json", "the JTBD set's loan_metrics and requirement text"], "evaluator_reads_used": "none"}
    (pack / "coverage" / "field_coverage.yaml").write_text(yaml.safe_dump({"summary": summary, "jobs": rows}, sort_keys=False, allow_unicode=True, width=120))
    print(lender, summary["by_status"], "declared keys", summary["declared_read_keys"], "text-named", summary["text_named_read_keys"], "unmapped", summary["unmapped_keys"], "entities", len(entities))
    return rows

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], Path(sys.argv[3]))
