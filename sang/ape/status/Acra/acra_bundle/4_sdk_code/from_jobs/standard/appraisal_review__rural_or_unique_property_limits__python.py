# rule: acra-standard.appraisal_review.rural_or_unique_property_limits.python
# origin: written from a job
# description: Python formalization of acra-standard.appraisal_review.rural_or_unique_property_limits
# reads: SubjectProperty.is_rural, LoanCore.loan_purpose, LoanCore.cltv_percent
# implements job: acra-standard.appraisal_review.rural_or_unique_property_limits

import decimal
import rules_lib


def check(ctx):
    rural = ctx['SubjectProperty.is_rural']
    missing = rules_lib.gaps(rural=rural)
    if missing:
        return rules_lib.unknown(*missing)

    rural_flag = rules_lib.flag(rural)
    if rural_flag is None:
        return rules_lib.unknown('SubjectProperty.is_rural')
    if not rural_flag:
        return True

    purpose = ctx['LoanCore.loan_purpose']
    cltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(purpose=purpose, cltv=cltv)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(purpose, 'purchase'):
        maximum = decimal.Decimal('80')
    elif rules_lib.same(purpose, 'refi r/t', 'refinance rate & term'):
        maximum = decimal.Decimal('75')
    elif rules_lib.same(purpose, 'refi c/o', 'refinance cash-out'):
        maximum = decimal.Decimal('70')
    else:
        return rules_lib.unknown('LoanCore.loan_purpose')

    try:
        cltv_number = decimal.Decimal(str(cltv))
    except (decimal.InvalidOperation, ValueError, TypeError):
        return rules_lib.unknown('LoanCore.cltv_percent')
    return cltv_number <= maximum
