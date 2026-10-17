# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.28
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶7
# reads: housing_history, loan_purpose, cltv_pct

import rules_lib

def check(ctx):
    housing_history = ctx['housing_history']
    loan_purpose = ctx['loan_purpose']
    cltv_pct = ctx['cltv_pct']

    missing = rules_lib.gaps(
        housing_history=housing_history,
        loan_purpose=loan_purpose,
        cltv_pct=cltv_pct,
    )
    if missing:
        return rules_lib.unknown(*missing)

    purchase = rules_lib.same(loan_purpose, 'Purchase')
    refinance = rules_lib.same(loan_purpose, 'Refi R/T', 'Refi C/O')
    if not purchase and not refinance:
        return False

    if rules_lib.same(housing_history, '1x30x12'):
        limit = 80 if purchase else 75
    elif rules_lib.same(housing_history, '0x60x12'):
        limit = 75 if purchase else 70
    elif rules_lib.same(housing_history, '0x90x12'):
        limit = 65
    elif rules_lib.same(housing_history, '0x120x12'):
        return False
    else:
        return False

    result = rules_lib.band(cltv_pct, [(limit, True)], above=False)
    if result is None:
        return rules_lib.unknown('cltv_pct')
    return result
