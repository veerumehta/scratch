# rule: acra-standard.asset_assessment_assets_and_funds_to_close.loan_amount_limits.python
# origin: written from a job
# description: Python formalization of acra-standard.asset_assessment_assets_and_funds_to_close.loan_amount_limits
# reads: LoanCore.total_loan_amount_usd
# implements job: acra-standard.asset_assessment_assets_and_funds_to_close.loan_amount_limits

import decimal
import rules_lib

def check(ctx):
    total_loan_amount_usd = ctx['LoanCore.total_loan_amount_usd']
    missing = rules_lib.gaps(total_loan_amount_usd=total_loan_amount_usd)
    if missing:
        return rules_lib.unknown(*missing)

    try:
        amount = decimal.Decimal(str(total_loan_amount_usd))
    except (decimal.InvalidOperation, TypeError, ValueError):
        return rules_lib.unknown('total_loan_amount_usd')

    if not amount.is_finite():
        return rules_lib.unknown('total_loan_amount_usd')

    return (
        amount >= decimal.Decimal('100000')
        and amount <= decimal.Decimal('3000000')
        and amount % decimal.Decimal('50') == 0
    )
