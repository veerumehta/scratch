"""List the overlay and base rules of the Revolution set whose outcomes the importer could not read.

Usage: PYTHONPATH=<japes worktree> python packs_unparsed_outcomes.py

Author: Virendra Mehta <virendra.mehta@jazzx.ai>
"""
import json,re,collections,sys
sys.path.insert(0,'/Users/sangit/src/japes-v27')
from jazzx_sdk.pipelines.policy.jtbdset import import_jtbdset,UNPARSED_OUTCOMES_KEY,_OUTCOME_SECTION
d=json.load(open('/Users/sangit/src/kernel-lab/codec-suite/workflows/customers/revolution/jtbds.json'))
J={j['mnemonic']:{r['investor']:r['requirement_text'] for r in j['requirements']} for j in d['values']}
imp=import_jtbdset(d,pack_id='x',metrics_key='loan_metrics')
rows=[]
for p in imp.policies:
    for r in p.rules:
        u=r.domain_extensions['jtbd'].get(UNPARSED_OUTCOMES_KEY)
        if not u: continue
        m,_,prog=r.rule_id.partition('.')
        t=J[m]['COMMON' if not prog else prog]
        L=t.splitlines()
        heads=[(i,l.strip()) for i,l in enumerate(L) if re.match(r'^\s{0,3}#{1,6}\s+.*outcome',l,re.I)]
        rows.append((r.rule_id,tuple(u),heads,t,L))
def shape(row):
    rid,u,heads,t,L=row
    h=heads[0][1] if heads else ''
    i=heads[0][0] if heads else 0
    body=[x.strip() for x in L[i+1:i+8] if x.strip()]
    return h,body
groups=collections.defaultdict(list)
for row in rows:
    h,body=shape(row)
    key=re.sub(r'^#+\s*','',h)
    groups[key].append(row)
for k,v in sorted(groups.items(),key=lambda x:-len(x[1])):
    print('###',repr(k),len(v),[x[0] for x in v][:12])
    h,body=shape(v[0]); print('   e.g.',v[0][0],v[0][1]); 
    for b in body[:6]: print('     |',b[:200])
print('=========== detail')
for k in ('Outcomes',):
    for row in groups[k]:
        h,body=shape(row)
        print(row[0],row[1]); 
        for b in body[:5]: print('    |',b[:150])
print('--- mapping variants: first body line shape')
c=collections.Counter()
for row in groups['Outcome Mapping']:
    h,body=shape(row)
    first=body[0] if body else ''
    c[re.sub(r'[A-Za-z0-9]','x',first[:14])+'|'+('bullets' if first.startswith(('-','*')) else 'prose')]+=1
print(c)
for row in groups['Outcome Mapping'][:40:6]:
    h,body=shape(row); print(row[0],'|',body[0][:230] if body else '')
print('=========== mapping subsplit + text kept')
R={r.rule_id:r for p in imp.policies for r in p.rules}
sub=collections.Counter(); kept=collections.Counter()
for row in groups['Outcome Mapping']:
    h,body=shape(row); first=body[0]
    na='N/A' in first; base=bool(re.search(r'per base|same',first,re.I))
    sub[('N/A' if na else '')+('+base' if base and na else ('base-only' if base else ''))]+=1
for k,v in groups.items():
    for row in v:
        c=R[row[0]].condition; hay=c.purpose+'\n'+'\n'.join(c.steps)+'\n'.join(c.checks)
        marker=shape(row)[0].lstrip('# ').strip()
        kept[(k,marker in hay)]+=1
print(sub); print(kept)
print('=========== ids')
for k,v in groups.items(): print(k,len(v),', '.join(x[0] for x in v)); print()
