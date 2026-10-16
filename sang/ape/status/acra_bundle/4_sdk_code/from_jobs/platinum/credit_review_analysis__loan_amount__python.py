# rule: acra-platinum.credit_review_analysis.loan_amount.python
# origin: written from a job
# description: Python formalization of acra-platinum.credit_review_analysis.loan_amount
# reads: LoanCore.total_loan_amount_usd
# implements job: acra-platinum.credit_review_analysis.loan_amount

import decimal
import rules_lib


def check(ctx):
    amount = ctx['LoanCore.total_loan_amount_usd']
    missing = rules_lib.gaps(total_loan_amount_usd=amount)
    if missing:
        return rules_lib.unknown(*missing)

    try:
        value = decimal.Decimal(str(amount))
    except (decimal.InvalidOperation, ValueError, TypeError):
        return False

    if not value.is_finite():
        return False
    return decimal.Decimal('100000') <= value <= decimal.Decimal('2000000') and value % decimal.Decimal('50') == 0
