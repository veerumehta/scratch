# rule: acra-standard.asset_assessment.loan_amount_limits.python
# origin: written from a job
# description: Python formalization of acra-standard.asset_assessment.loan_amount_limits
# reads: LoanCore.total_loan_amount_usd
# implements job: acra-standard.asset_assessment.loan_amount_limits

import decimal
import rules_lib

def check(ctx):
    amount = ctx['LoanCore.total_loan_amount_usd']
    missing = rules_lib.gaps(amount=amount)
    if missing:
        return rules_lib.unknown(*missing)
    amount = decimal.Decimal(str(amount))
    return decimal.Decimal('100000') <= amount <= decimal.Decimal('3000000') and amount % decimal.Decimal('50') == 0
