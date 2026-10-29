# rule: acra-standard.appraisal_review_property_eligibility.rural_or_unique_property_limits.python
# origin: written from a job
# description: Python formalization of acra-standard.appraisal_review_property_eligibility.rural_or_unique_property_limits
# reads: SubjectProperty.is_rural, LoanCore.loan_purpose, LoanCore.cltv_percent, CreditReport.representative_score
# implements job: acra-standard.appraisal_review_property_eligibility.rural_or_unique_property_limits

import decimal
import rules_lib


def check(ctx):
    rural_raw = ctx['SubjectProperty.is_rural']
    rural = rules_lib.flag(rural_raw)
    missing = rules_lib.gaps(rural=rural)
    if missing:
        return rules_lib.unknown(*missing)
    if rural is None:
        return rules_lib.unknown('rural')
    if not rural:
        return True

    purpose = ctx['LoanCore.loan_purpose']
    cltv_raw = ctx['LoanCore.cltv_percent']
    score_raw = ctx['CreditReport.representative_score']
    missing = rules_lib.gaps(purpose=purpose, cltv=cltv_raw, score=score_raw)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(purpose, 'purchase'):
        cltv_limit = 80
    elif rules_lib.same(purpose, 'refinance — rate & term', 'refi r/t'):
        cltv_limit = 75
    elif rules_lib.same(purpose, 'refinance — cash-out', 'refi c/o'):
        cltv_limit = 70
    else:
        return rules_lib.unknown('purpose')

    cltv = rules_lib.percent(cltv_raw, 'percent')
    if cltv is None:
        return rules_lib.unknown('cltv')
    try:
        score = decimal.Decimal(str(score_raw))
    except (decimal.InvalidOperation, TypeError, ValueError):
        return rules_lib.unknown('score')

    return cltv <= cltv_limit and score >= 700
