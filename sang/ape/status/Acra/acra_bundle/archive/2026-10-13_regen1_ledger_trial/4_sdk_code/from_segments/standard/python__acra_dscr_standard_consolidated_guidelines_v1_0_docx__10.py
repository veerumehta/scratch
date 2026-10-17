# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.10
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶11
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

    if loan_amount > 1500000:
        return rules_lib.unknown('CLTV for loan amount tier')

    if rules_lib.same(loan_purpose, 'purchase'):
        column = 0
    elif rules_lib.same(loan_purpose, 'rate & term'):
        column = 1
    elif rules_lib.same(loan_purpose, 'cash-out'):
        column = 2
    else:
        return False

    if fico >= 780:
        limits = (0.85, 0.80, 0.80)
    elif fico >= 760:
        limits = (0.85, 0.80, 0.80)
    elif fico >= 740:
        limits = (0.85, 0.80, 0.80)
    elif fico >= 720:
        limits = (0.85, 0.80, 0.80)
    elif fico >= 700:
        limits = (0.80, 0.80, 0.75)
    elif fico >= 680:
        limits = (0.80, 0.75, 0.75)
    elif fico >= 660:
        limits = (0.80, 0.75, 0.75)
    elif fico >= 640:
        limits = (0.75, 0.70, 0.70)
    elif fico >= 620:
        limits = (0.65, 0.65, 0.65)
    elif fico >= 600:
        limits = (0.60, 0.60, 0.60)
    else:
        return False

    return cltv_pct <= limits[column]
