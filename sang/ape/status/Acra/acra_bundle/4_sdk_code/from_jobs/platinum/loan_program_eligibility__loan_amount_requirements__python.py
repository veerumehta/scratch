# rule: acra-platinum.loan_program_eligibility.loan_amount_requirements.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.loan_amount_requirements
# reads: LoanCore.total_loan_amount_usd
# implements job: acra-platinum.loan_program_eligibility.loan_amount_requirements

import decimal
import rules_lib

def check(ctx):
    amount = ctx['LoanCore.total_loan_amount_usd']
    missing = rules_lib.gaps(amount=amount)
    if missing:
        return rules_lib.unknown(*missing)
    try:
        amount = decimal.Decimal(str(amount))
        if not amount.is_finite():
            return False
        return (
            decimal.Decimal('100000') <= amount <= decimal.Decimal('2000000')
            and amount % decimal.Decimal('50') == 0
        )
    except (decimal.InvalidOperation, TypeError, ValueError):
        return False
