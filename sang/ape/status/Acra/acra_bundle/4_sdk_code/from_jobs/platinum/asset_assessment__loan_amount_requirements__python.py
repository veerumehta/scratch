# rule: acra-platinum.asset_assessment.loan_amount_requirements.python
# origin: written from a job
# description: Python formalization of acra-platinum.asset_assessment.loan_amount_requirements
# reads: LoanCore.total_loan_amount_usd, LoanCore.cltv_percent
# implements job: acra-platinum.asset_assessment.loan_amount_requirements

import decimal
import rules_lib

def check(ctx):
    amount = ctx['LoanCore.total_loan_amount_usd']
    missing = rules_lib.gaps(amount=amount)
    if missing:
        return rules_lib.unknown(*missing)
    try:
        amount = decimal.Decimal(str(amount))
        applies_cltv = amount < decimal.Decimal('350000') or amount > decimal.Decimal('1500000')
        amount_ok = (
            amount >= decimal.Decimal('100000')
            and amount <= decimal.Decimal('2000000')
            and amount % decimal.Decimal('50') == 0
        )
    except (decimal.InvalidOperation, ValueError, TypeError):
        return rules_lib.unknown('LoanCore.total_loan_amount_usd')

    if not applies_cltv:
        return amount_ok

    cltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv=cltv)
    if missing:
        return rules_lib.unknown(*missing)
    try:
        cltv = decimal.Decimal(str(cltv))
        cltv_ok = cltv <= decimal.Decimal('75.00')
    except (decimal.InvalidOperation, ValueError, TypeError):
        return rules_lib.unknown('LoanCore.cltv_percent')

    return amount_ok and cltv_ok
