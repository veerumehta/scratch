# rule: acra-standard.loan_program_eligibility.loan_amount.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_program_eligibility.loan_amount
# reads: LoanCore.total_loan_amount_usd, LoanCore.is_delayed_financing, MortgageLoanInformation.is_interest_only
# implements job: acra-standard.loan_program_eligibility.loan_amount

import decimal
import rules_lib


def check(ctx):
    amount_raw = ctx['LoanCore.total_loan_amount_usd']
    delayed_raw = ctx['LoanCore.is_delayed_financing']
    interest_only_raw = ctx['MortgageLoanInformation.is_interest_only']

    missing = rules_lib.gaps(
        amount=amount_raw,
        delayed_financing=delayed_raw,
        interest_only=interest_only_raw,
    )
    if missing:
        return rules_lib.unknown(*missing)

    try:
        amount = decimal.Decimal(str(amount_raw))
    except (decimal.InvalidOperation, ValueError, TypeError):
        return rules_lib.unknown('amount')
    if not amount.is_finite():
        return rules_lib.unknown('amount')

    delayed = rules_lib.flag(delayed_raw)
    interest_only = rules_lib.flag(interest_only_raw)
    if delayed is None:
        return rules_lib.unknown('delayed_financing')
    if interest_only is None:
        return rules_lib.unknown('interest_only')

    meets_requirements = (
        decimal.Decimal('100000') <= amount <= decimal.Decimal('3000000')
        and amount % decimal.Decimal('50') == 0
    )
    if interest_only:
        meets_requirements = (
            meets_requirements
            and amount >= decimal.Decimal('250000')
            and amount <= decimal.Decimal('3000000')
        )
    if delayed:
        meets_requirements = meets_requirements and amount <= decimal.Decimal('1500000')

    return meets_requirements
