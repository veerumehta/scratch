# rule: acra-standard.loan_program_eligibility.interest_only_loan_amount_and_credit_minimums.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_program_eligibility.interest_only_loan_amount_and_credit_minimums
# reads: MortgageLoanInformation.is_interest_only, LoanCore.total_loan_amount_usd, CreditReport.representative_score
# implements job: acra-standard.loan_program_eligibility.interest_only_loan_amount_and_credit_minimums

import rules_lib

def check(ctx):
    interest_only_raw = ctx['MortgageLoanInformation.is_interest_only']
    missing = rules_lib.gaps(interest_only=interest_only_raw)
    if missing:
        return rules_lib.unknown(*missing)
    interest_only = rules_lib.flag(interest_only_raw)
    if interest_only is None:
        return rules_lib.unknown('interest_only')
    if not interest_only:
        return True

    loan_amount = ctx['LoanCore.total_loan_amount_usd']
    representative_fico = ctx['CreditReport.representative_score']
    missing = rules_lib.gaps(loan_amount=loan_amount, representative_fico=representative_fico)
    if missing:
        return rules_lib.unknown(*missing)
    return loan_amount >= 250000 and loan_amount <= 3000000 and representative_fico >= 640
