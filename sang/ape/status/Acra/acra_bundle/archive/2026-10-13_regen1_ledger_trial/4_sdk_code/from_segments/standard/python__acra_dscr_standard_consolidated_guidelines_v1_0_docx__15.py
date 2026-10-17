# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.15
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶16
# reads: occupancy_subtype, loan_purpose, cltv_pct, fico

import rules_lib

def check(ctx):
    occupancy_subtype = ctx['occupancy_subtype']
    missing = rules_lib.gaps(occupancy_subtype=occupancy_subtype)
    if missing:
        return rules_lib.unknown(*missing)
    if not rules_lib.same(occupancy_subtype, 'short-term rental'):
        return True

    loan_purpose = ctx['loan_purpose']
    cltv_pct = ctx['cltv_pct']
    fico = ctx['fico']
    missing = rules_lib.gaps(loan_purpose=loan_purpose, cltv_pct=cltv_pct, fico=fico)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(loan_purpose, 'purchase'):
        maximum_cltv = 75
    elif rules_lib.same(loan_purpose, 'refinance'):
        maximum_cltv = 70
    else:
        return True

    return cltv_pct <= maximum_cltv and fico >= 640
