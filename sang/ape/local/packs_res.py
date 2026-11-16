"""Resolve a JTBD set's declared reads against each mortgage ontology v2 copy; `split` is shared with packs_catalog_and_coverage.py.

Usage: PYTHONPATH=<japes worktree> python packs_res.py

Author: Virendra Mehta <virendra.mehta@jazzx.ai>
"""
import json,re,collections
from jazzx_sdk.pack.catalog import entity_properties,is_entity
B="/Users/sangit/src/kernel-lab/codec-suite/workflows/customers/"
ONT={"policy-workbench(411fe46)":"/Users/sangit/src/policy-workbench/backend/policyforge/prompts/ontology/mortgage_ontology_v2.json",
"mortgage-app-ontology(83509d)":"/Users/sangit/src/mortgage-app-ontology/common/resources/ontologies/mortgage_ontology_v2.json",
"macer(c1c617)":"/Users/sangit/src/macer/src/macer/data/ontologies/common/mortgage_ontology_v2.json",
"mortgage-app(27ebc5)":"/Users/sangit/src/mortgage-app/ontologies/common/mortgage_ontology_v2.json",
"juno-fixture v4":"/Users/sangit/src/juno/tests/copilot/fixtures/ontologies/mortgage_ontology_v4_juno.json"}
def split(k):
    m=re.match(r"^([A-Za-z_]+)(?:\[[^\]]*\])?(?:\.(.+))?$",k); return m.group(1),(m.group(2) or "")
def fields(d,ent):
    defs=d["$defs"]; spec=defs.get(ent)
    if spec is None or not is_entity(spec): return None
    props,_=entity_properties(spec,defs); return set(props)
if __name__=="__main__":
    for lender in("pulte","revolution"):
        S=json.load(open(B+lender+"/jtbds.json"))["values"]
        keys=sorted({m["metric_key"] for j in S for m in (j.get("loan_metrics") or [])})
        for name,p in ONT.items():
            d=json.load(open(p)); miss=[];
            for k in keys:
                e,f=split(k); fs=fields(d,e)
                top=f.split(".")[0].split("[")[0] if f else ""
                if fs is None or (top and top not in fs): miss.append(k)
            print(lender,name,"keys",len(keys),"unresolved",len(miss),miss[:4])
