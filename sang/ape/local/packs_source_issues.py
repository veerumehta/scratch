"""Source-data issues in the Revolution v6.7 set (read-only).

Usage: python packs_source_issues.py

Author: Virendra Mehta <virendra.mehta@jazzx.ai>
"""
import json,re,sys
d=json.load(open('/Users/sangit/src/kernel-lab/codec-suite/workflows/customers/revolution/jtbds.json'))
J={j['mnemonic']:j for j in d['values']}
def T(m,inv='COMMON'): return {r['investor']:r['requirement_text'] for r in J[m]['requirements']}[inv]
def grep(m,inv,pat,w=220):
    t=T(m,inv)
    for x in re.finditer(pat,t,re.I):
        print(f'[{m} {inv}]',t[max(0,x.start()-w):x.end()+w].replace('\n',' / ')); print()
grep('APR-IPT','COMMON',r'co-?op',200)
print('-----AVA'); 
for inv in ('COMMON','VA'): grep('APR-AVA',inv,r'IRRRL',200)
print('-----RSLE'); grep('AST-RSLE','FHA',r'haircut',220)
print('-----WTR'); grep('APR-WTR','COMMON',r'(4\.2|purif)',200)
print('=====more')
t=T('APR-WTR'); i=t.find('4.2'); print('WTR 4.2:',t[max(0,i-100):i+500].replace('\n',' / ') if i>=0 else 'none')
for m in ('AST-RSLE',):
    for inv in ('COMMON','FHA'):
        tt=T(m,inv)
        for x in re.finditer(r'(?i)(100%|no reduction|reduc|discount|net equity|retirement)',tt):
            print(m,inv,tt[max(0,x.start()-120):x.end()+160].replace('\n',' / ')); print(); break
import collections
c=0
for m,j in J.items():
    for inv in ('COMMON',):
        tt=T(m,inv)
        if re.search(r'(?i)\bcount\b[^.\n]{0,80}\b(default|0|zero)\b',tt): c+=1; 
print('jobs matching count..default/0:',c)
for m in ('COM-ECOA',): pass
