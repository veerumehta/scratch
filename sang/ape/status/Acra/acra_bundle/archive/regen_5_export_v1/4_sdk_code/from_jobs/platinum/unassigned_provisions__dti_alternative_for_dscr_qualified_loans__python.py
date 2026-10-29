# rule: acra-platinum.unassigned_provisions.dti_alternative_for_dscr_qualified_loans.python
# origin: written from a job
# description: Python formalization of acra-platinum.unassigned_provisions.dti_alternative_for_dscr_qualified_loans
# reads: LoanCore.dscr_qualification_method, RatioSet.total_monthly_income_usd, RatioSet.total_monthly_obligation_usd
# implements job: acra-platinum.unassigned_provisions.dti_alternative_for_dscr_qualified_loans

import rules_lib


def check(ctx):
    method = ctx['LoanCore.dscr_qualification_method']
    income = ctx['RatioSet.total_monthly_income_usd']
    obligation = ctx['RatioSet.total_monthly_obligation_usd']

    missing = rules_lib.gaps(method=method, income=income, obligation=obligation)
    if missing:
        return rules_lib.unknown(*missing)

    dti = rules_lib.ratio(obligation, income)
    if dti is None:
        return rules_lib.unknown('DTI ratio')

    return rules_lib.same(method, 'DSCR') and dti <= 0.43
