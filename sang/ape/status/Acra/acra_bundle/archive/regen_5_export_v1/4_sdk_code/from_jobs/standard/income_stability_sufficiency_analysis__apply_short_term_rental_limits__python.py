# rule: acra-standard.income_stability_sufficiency_analysis.apply_short_term_rental_limits.python
# origin: written from a job
# description: Python formalization of acra-standard.income_stability_sufficiency_analysis.apply_short_term_rental_limits
# reads: SubjectProperty.occupancy_subtype, LoanCore.loan_purpose, LoanCore.cltv_percent, CreditReport.representative_score
# implements job: acra-standard.income_stability_sufficiency_analysis.apply_short_term_rental_limits

import decimal
import rules_lib

def check(ctx):
    occupancy_subtype = ctx['SubjectProperty.occupancy_subtype']
    missing = rules_lib.gaps(occupancy_subtype=occupancy_subtype)
    if missing:
        return rules_lib.unknown(*missing)
    if not rules_lib.same(occupancy_subtype, 'short-term rental', 'STR'):
        return True

    loan_purpose = ctx['LoanCore.loan_purpose']
    missing = rules_lib.gaps(loan_purpose=loan_purpose)
    if missing:
        return rules_lib.unknown(*missing)

    is_purchase = rules_lib.same(loan_purpose, 'purchase')
    is_refinance = rules_lib.same(
        loan_purpose,
        'refinance',
        'rate & term',
        'rate & term refinance',
        'cash-out',
        'cash-out refinance',
    )
    if not is_purchase and not is_refinance:
        return True

    cltv_percent = ctx['LoanCore.cltv_percent']
    representative_score = ctx['CreditReport.representative_score']
    missing = rules_lib.gaps(
        cltv_percent=cltv_percent,
        representative_score=representative_score,
    )
    if missing:
        return rules_lib.unknown(*missing)

    cltv = rules_lib.percent(cltv_percent, 'percent')
    if cltv is None:
        return rules_lib.unknown('LoanCore.cltv_percent')
    try:
        fico = decimal.Decimal(str(representative_score))
        if not fico.is_finite():
            return rules_lib.unknown('CreditReport.representative_score')
    except (decimal.InvalidOperation, ValueError, TypeError):
        return rules_lib.unknown('CreditReport.representative_score')

    maximum_cltv = 75 if is_purchase else 70
    return cltv <= maximum_cltv and fico >= 640
