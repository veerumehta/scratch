# rule: acra-standard.credit_review_analysis.interest_only_loan_amount_and_fico.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_review_analysis.interest_only_loan_amount_and_fico
# reads: MortgageLoanInformation.is_interest_only, LoanCore.total_loan_amount_usd, CreditReport.representative_score
# implements job: acra-standard.credit_review_analysis.interest_only_loan_amount_and_fico

import rules_lib

def check(ctx):
    is_interest_only = ctx['MortgageLoanInformation.is_interest_only']
    missing = rules_lib.gaps(is_interest_only=is_interest_only)
    if missing:
        return rules_lib.unknown(*missing)

    interest_only = rules_lib.flag(is_interest_only)
    if interest_only is None:
        return rules_lib.unknown('is_interest_only')
    if not interest_only:
        return True

    loan_amount = ctx['LoanCore.total_loan_amount_usd']
    fico = ctx['CreditReport.representative_score']
    missing = rules_lib.gaps(loan_amount=loan_amount, fico=fico)
    if missing:
        return rules_lib.unknown(*missing)

    return loan_amount >= 250000 and loan_amount <= 3000000 and fico >= 640
