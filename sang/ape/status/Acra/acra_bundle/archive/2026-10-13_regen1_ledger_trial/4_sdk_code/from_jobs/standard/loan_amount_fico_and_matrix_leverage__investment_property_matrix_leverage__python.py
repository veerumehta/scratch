# rule: acra-standard.loan_amount_fico_and_matrix_leverage.investment_property_matrix_leverage.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_amount_fico_and_matrix_leverage.investment_property_matrix_leverage
# reads: loan_amount, fico, loan_purpose, cltv_pct
# implements job: acra-standard.loan_amount_fico_and_matrix_leverage.investment_property_matrix_leverage

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

    # STD-2.2 states that loans of $1,500,000 or less have no published
    # matrix row below FICO 600.
    if loan_amount <= 1500000 and fico < 600:
        return False

    # The clause supplies no loan-amount boundaries or labels for its three
    # tables, so the applicable tier and matrix cell cannot be determined.
    return rules_lib.unknown('published loan-amount tier')
