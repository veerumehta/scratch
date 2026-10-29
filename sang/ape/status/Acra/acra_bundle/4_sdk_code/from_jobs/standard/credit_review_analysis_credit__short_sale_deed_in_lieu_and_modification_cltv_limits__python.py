# rule: acra-standard.credit_review_analysis_credit.short_sale_deed_in_lieu_and_modification_cltv_limits.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_review_analysis_credit.short_sale_deed_in_lieu_and_modification_cltv_limits
# reads: Borrower.has_short_sale_dil_or_modification, Borrower.months_since_short_sale_dil_or_modification, LoanCore.loan_purpose, LoanCore.cltv_percent
# implements job: acra-standard.credit_review_analysis_credit.short_sale_deed_in_lieu_and_modification_cltv_limits

import decimal
import rules_lib


def check(ctx):
    has_event = ctx['Borrower.has_short_sale_dil_or_modification']
    missing = rules_lib.gaps(has_event=has_event)
    if missing:
        return rules_lib.unknown(*missing)

    has_event = rules_lib.flag(has_event)
    if has_event is None:
        return rules_lib.unknown('has_event')
    if not has_event:
        return True

    months = ctx['Borrower.months_since_short_sale_dil_or_modification']
    purpose = ctx['LoanCore.loan_purpose']
    missing = rules_lib.gaps(months=months, purpose=purpose)
    if missing:
        return rules_lib.unknown(*missing)

    try:
        months = decimal.Decimal(str(months))
        if not months.is_finite():
            return rules_lib.unknown('months')
    except (decimal.InvalidOperation, TypeError, ValueError):
        return rules_lib.unknown('months')

    if rules_lib.same(purpose, 'purchase'):
        if months < 12:
            maximum = 75
        elif months < 24:
            maximum = 80
        else:
            return True
    elif rules_lib.same(purpose, 'Refi R/T', 'Refi C/O'):
        if months < 12:
            maximum = 70
        elif months < 24:
            maximum = 75
        else:
            return True
    else:
        return rules_lib.unknown('purpose')

    cltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv=cltv)
    if missing:
        return rules_lib.unknown(*missing)
    cltv = rules_lib.percent(cltv, 'percent')
    if cltv is None:
        return rules_lib.unknown('cltv')
    return cltv <= maximum
