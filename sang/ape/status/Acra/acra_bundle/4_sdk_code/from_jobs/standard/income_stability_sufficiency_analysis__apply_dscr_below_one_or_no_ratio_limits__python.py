# rule: acra-standard.income_stability_sufficiency_analysis.apply_dscr_below_one_or_no_ratio_limits.python
# origin: written from a job
# description: Python formalization of acra-standard.income_stability_sufficiency_analysis.apply_dscr_below_one_or_no_ratio_limits
# reads: LoanCore.dscr_qualification_method, LoanCore.loan_purpose, LoanCore.cltv_percent, CreditReport.representative_score
# implements job: acra-standard.income_stability_sufficiency_analysis.apply_dscr_below_one_or_no_ratio_limits

import rules_lib


def check(ctx):
    method = ctx['LoanCore.dscr_qualification_method']
    missing = rules_lib.gaps(method=method)
    if missing:
        return rules_lib.unknown(*missing)

    applies = rules_lib.same(method, 'No Ratio', 'DSCR below 1.0', 'DSCR < 1.0')
    if not applies:
        return True

    purpose = ctx['LoanCore.loan_purpose']
    missing = rules_lib.gaps(purpose=purpose)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(purpose, 'purchase'):
        cltv_limit = 75
    elif rules_lib.same(purpose, 'refinance rate & term', 'rate & term refinance'):
        cltv_limit = 70
    elif rules_lib.same(purpose, 'refinance cash-out', 'cash-out refinance'):
        cltv_limit = 65
    else:
        return True

    cltv_raw = ctx['LoanCore.cltv_percent']
    score = ctx['CreditReport.representative_score']
    missing = rules_lib.gaps(cltv=cltv_raw, fico=score)
    if missing:
        return rules_lib.unknown(*missing)

    cltv = rules_lib.percent(cltv_raw, 'percent')
    if cltv is None:
        return rules_lib.unknown('cltv')

    return cltv <= cltv_limit and score >= 640
