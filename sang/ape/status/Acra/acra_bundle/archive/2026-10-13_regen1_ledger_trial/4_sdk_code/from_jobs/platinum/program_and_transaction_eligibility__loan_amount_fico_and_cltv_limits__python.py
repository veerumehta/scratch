# rule: acra-platinum.program_and_transaction_eligibility.loan_amount_fico_and_cltv_limits.python
# origin: written from a job
# description: Python formalization of acra-platinum.program_and_transaction_eligibility.loan_amount_fico_and_cltv_limits
# reads: loan_amount, fico, loan_purpose, cltv_pct
# implements job: acra-platinum.program_and_transaction_eligibility.loan_amount_fico_and_cltv_limits

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

    if not (100000 <= loan_amount <= 2000000 and loan_amount % 50 == 0):
        return False
    if fico < 700:
        return False
    if rules_lib.same(loan_purpose, 'purchase', 'rate & term refinance'):
        return cltv_pct <= 80
    if rules_lib.same(loan_purpose, 'cash-out refinance') and fico >= 730:
        return cltv_pct <= 75
    return True
