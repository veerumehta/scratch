# rule: acra-platinum.title_review.listed_property_qualification.python
# origin: written from a job
# description: Python formalization of acra-platinum.title_review.listed_property_qualification
# reads: RatioSet.total_monthly_income_usd, RatioSet.total_monthly_obligation_usd, LoanCore.channel
# implements job: acra-platinum.title_review.listed_property_qualification

import rules_lib

def check(ctx):
    income = ctx['RatioSet.total_monthly_income_usd']
    obligations = ctx['RatioSet.total_monthly_obligation_usd']
    missing = rules_lib.gaps(income=income, obligations=obligations)
    if missing:
        return rules_lib.unknown(*missing)

    dti = rules_lib.ratio(obligations, income)
    if dti is None:
        return rules_lib.unknown('RatioSet.total_monthly_income_usd', 'RatioSet.total_monthly_obligation_usd')
    if dti <= 0.43:
        return True

    channel = ctx['LoanCore.channel']
    missing = rules_lib.gaps(channel=channel)
    if missing:
        return rules_lib.unknown(*missing)
    if rules_lib.same(channel, 'Wholesale'):
        minimum_dscr = 1.0
    elif rules_lib.same(channel, 'Correspondent'):
        minimum_dscr = 1.2
    else:
        return rules_lib.unknown('LoanCore.channel')

    # No DSCR value is among the permitted case fields, so the DSCR alternative
    # cannot be decided when the DTI alternative fails.
    return rules_lib.unknown(f'DSCR value (channel minimum {minimum_dscr})')
