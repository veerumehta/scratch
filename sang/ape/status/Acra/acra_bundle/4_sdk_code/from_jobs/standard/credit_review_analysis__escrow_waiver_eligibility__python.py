# rule: acra-standard.credit_review_analysis.escrow_waiver_eligibility.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_review_analysis.escrow_waiver_eligibility
# reads: LoanCore.total_loan_amount_usd, LoanCore.cltv_percent, CreditReport.representative_score, Borrower.citizenship_status
# implements job: acra-standard.credit_review_analysis.escrow_waiver_eligibility

import rules_lib

def check(ctx):
    loan_amount = ctx['LoanCore.total_loan_amount_usd']
    cltv = ctx['LoanCore.cltv_percent']
    fico = ctx['CreditReport.representative_score']
    citizenship = ctx['Borrower.citizenship_status']

    missing = rules_lib.gaps(
        loan_amount=loan_amount,
        cltv=cltv,
        fico=fico,
        citizenship=citizenship,
    )
    if missing:
        return rules_lib.unknown(*missing)

    return (
        loan_amount <= 1_500_000
        and cltv <= 80
        and fico >= 700
        and not rules_lib.same(citizenship, 'Foreign National')
    )
