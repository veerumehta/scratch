"""List loan_metrics keys that name a boolean catalog field, per lender.

Usage: PYTHONPATH=<japes worktree> python packs_boolean_metrics.py

Author: Virendra Mehta <virendra.mehta@jazzx.ai>
"""
import json,re,sys,collections
sys.path.insert(0,'/Users/sangit/src/japes-v27')
from jazzx_sdk.pack.catalog import entity_properties,is_entity
from packs_res import split
ONT='/Users/sangit/src/policy-workbench/backend/policyforge/prompts/ontology/mortgage_ontology_v2.json'
defs=json.load(open(ONT))['$defs']
props={n:entity_properties(s,defs)[0] for n,s in defs.items() if is_entity(s)}
def ftype(k):
    e,f=split(k); top=f.split('.')[0].split('[')[0] if f else ''
    p=props.get(e,{}).get(top)
    if p is None: return None
    t=p.get('type') if isinstance(p,dict) else str(p)
    return '|'.join(t) if isinstance(t,list) else t
out={}
for lender in ('revolution','pulte'):
    d=json.load(open(f'/Users/sangit/src/kernel-lab/codec-suite/workflows/customers/{lender}/jtbds.json'))
    rows=[]
    tc=collections.Counter()
    for j in d['values']:
        for m in j.get('loan_metrics') or []:
            t=ftype(m['metric_key']); tc[t]+=1
            if t and 'boolean' in t.split('|'): rows.append((j['mnemonic'],m['metric_key'],m['metric_mnemonic'],m.get('indicator_context','')))
    print(lender,dict(tc),'boolean-typed',len(rows))
    out[lender]=rows
json.dump(out,open('boolm.json','w'))
