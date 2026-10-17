# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.11
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶12
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

    # The loan-amount scope of the first matrix is not stated in the excerpt.
    if not (2_000_001 <= loan_amount <= 3_000_000):
        return rules_lib.unknown('loan_amount')

    if rules_lib.same(loan_purpose, 'purchase') or rules_lib.same(loan_purpose, 'rate & term'):
        max_cltv = 70 if fico >= 700 else None
    elif rules_lib.same(loan_purpose, 'cash-out'):
        max_cltv = 65 if fico >= 700 else None
    else:
        return False

    if max_cltv is None:
        return False
    return cltv_pct <= max_cltv
