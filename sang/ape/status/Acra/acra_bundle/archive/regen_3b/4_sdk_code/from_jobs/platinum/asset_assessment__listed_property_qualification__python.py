# rule: acra-platinum.asset_assessment.listed_property_qualification.python
# origin: written from a job
# description: Python formalization of acra-platinum.asset_assessment.listed_property_qualification
# reads: RatioSet.total_monthly_obligation_usd, RatioSet.total_monthly_income_usd
# implements job: acra-platinum.asset_assessment.listed_property_qualification

import rules_lib


def check(ctx):
    obligations = ctx['RatioSet.total_monthly_obligation_usd']
    income = ctx['RatioSet.total_monthly_income_usd']

    missing = rules_lib.gaps(obligations=obligations, income=income)
    if missing:
        return rules_lib.unknown(*missing)

    dti = rules_lib.ratio(obligations, income)
    if dti is None:
        return rules_lib.unknown('DTI inputs')
    if dti <= 0.43:
        return True

    # The permitted fields include no DSCR value, so a DTI above 43% does
    # not establish whether the alternative DSCR route qualifies.
    return rules_lib.unknown('DSCR qualification')
