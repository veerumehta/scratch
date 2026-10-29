# rule: acra-platinum.loan_program_eligibility.loan_amount_range_and_increment.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.loan_amount_range_and_increment
# reads: LoanCore.total_loan_amount_usd
# implements job: acra-platinum.loan_program_eligibility.loan_amount_range_and_increment

import decimal
import rules_lib

def check(ctx):
    amount = ctx['LoanCore.total_loan_amount_usd']
    missing = rules_lib.gaps(total_loan_amount_usd=amount)
    if missing:
        return rules_lib.unknown(*missing)
    try:
        amount = decimal.Decimal(str(amount))
    except (decimal.InvalidOperation, ValueError, TypeError):
        return rules_lib.unknown('total_loan_amount_usd')
    if not amount.is_finite():
        return rules_lib.unknown('total_loan_amount_usd')
    return (
        decimal.Decimal('100000') <= amount <= decimal.Decimal('2000000')
        and amount % decimal.Decimal('50') == 0
    )
