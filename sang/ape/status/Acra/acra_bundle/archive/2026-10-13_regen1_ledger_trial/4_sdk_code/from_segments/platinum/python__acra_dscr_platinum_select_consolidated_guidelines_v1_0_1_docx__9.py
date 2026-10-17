# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.9
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶10
# reads: loan_amount, fico, loan_purpose, cltv_pct

import rules_lib


def check(ctx):
    loan_amount = ctx['loan_amount']
    fico = ctx['fico']
    loan_purpose = ctx['loan_purpose']
    cltv_pct = ctx['cltv_pct']

    missing = rules_lib.gaps(
        loan_amount=loan_amount,
        fico=fico,
        loan_purpose=loan_purpose,
        cltv_pct=cltv_pct,
    )
    if missing:
        return rules_lib.unknown(*missing)

    if loan_amount > 2000000 or fico < 700:
        return False

    if rules_lib.same(loan_purpose, 'purchase') or rules_lib.same(loan_purpose, 'rate & term'):
        maximum_cltv = 80
    elif rules_lib.same(loan_purpose, 'cash-out'):
        if fico >= 730:
            maximum_cltv = 75
        elif fico >= 721:
            maximum_cltv = 65
        else:
            maximum_cltv = 55
    else:
        return False

    return cltv_pct <= maximum_cltv
