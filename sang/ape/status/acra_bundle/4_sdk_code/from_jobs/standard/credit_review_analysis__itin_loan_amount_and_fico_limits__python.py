# rule: acra-standard.credit_review_analysis.itin_loan_amount_and_fico_limits.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_review_analysis.itin_loan_amount_and_fico_limits
# reads: Borrower.citizenship_status, LoanCore.total_loan_amount_usd, CreditReport.representative_score
# implements job: acra-standard.credit_review_analysis.itin_loan_amount_and_fico_limits

import rules_lib

def check(ctx):
    status = ctx['Borrower.citizenship_status']
    missing = rules_lib.gaps(status=status)
    if missing:
        return rules_lib.unknown(*missing)
    if not rules_lib.same(status, 'ITIN'):
        return True

    amount = ctx['LoanCore.total_loan_amount_usd']
    score = ctx['CreditReport.representative_score']
    missing = rules_lib.gaps(amount=amount, score=score)
    if missing:
        return rules_lib.unknown(*missing)
    return amount <= 1000000 and score >= 640
