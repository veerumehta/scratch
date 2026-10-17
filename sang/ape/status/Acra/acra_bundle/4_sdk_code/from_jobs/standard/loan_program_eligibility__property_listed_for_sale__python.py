# rule: acra-standard.loan_program_eligibility.property_listed_for_sale.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_program_eligibility.property_listed_for_sale
# reads: SubjectProperty.listed_for_sale_last_6_months, RatioSet.reserves_months, MortgageLoanInformation.is_interest_only
# implements job: acra-standard.loan_program_eligibility.property_listed_for_sale

import decimal
import rules_lib


def check(ctx):
    listed_raw = ctx['SubjectProperty.listed_for_sale_last_6_months']
    reserves_raw = ctx['RatioSet.reserves_months']
    interest_only_raw = ctx['MortgageLoanInformation.is_interest_only']

    listed = rules_lib.flag(listed_raw)
    interest_only = rules_lib.flag(interest_only_raw)
    missing = rules_lib.gaps(
        listed=listed,
        reserves_months=reserves_raw,
        interest_only=interest_only,
    )
    if missing:
        return rules_lib.unknown(*missing)

    try:
        reserves = decimal.Decimal(str(reserves_raw))
    except (decimal.InvalidOperation, TypeError, ValueError):
        return rules_lib.unknown('reserves_months')
    if not reserves.is_finite():
        return rules_lib.unknown('reserves_months')

    return listed and reserves >= decimal.Decimal(24) and not interest_only
