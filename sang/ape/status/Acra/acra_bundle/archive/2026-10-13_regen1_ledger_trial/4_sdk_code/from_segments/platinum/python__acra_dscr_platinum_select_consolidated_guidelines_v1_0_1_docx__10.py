# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.10
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶11
# reads: fico, loan_purpose, cltv_pct

import rules_lib

def check(ctx):
    fico = ctx['fico']
    loan_purpose = ctx['loan_purpose']
    cltv_pct = ctx['cltv_pct']
    missing = rules_lib.gaps(fico=fico, loan_purpose=loan_purpose, cltv_pct=cltv_pct)
    if missing:
        return rules_lib.unknown(*missing)
    if fico == 720 and rules_lib.same(loan_purpose, 'cash-out'):
        return cltv_pct <= 55
    return True
