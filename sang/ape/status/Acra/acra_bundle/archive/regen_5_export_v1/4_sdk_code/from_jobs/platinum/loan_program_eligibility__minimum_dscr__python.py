# rule: acra-platinum.loan_program_eligibility.minimum_dscr.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.minimum_dscr
# reads: LoanCore.channel, RatioSet.total_monthly_income_usd, RatioSet.total_monthly_obligation_usd
# implements job: acra-platinum.loan_program_eligibility.minimum_dscr

import rules_lib

def check(ctx):
    channel = ctx['LoanCore.channel']
    missing = rules_lib.gaps(channel=channel)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(channel, 'Correspondent'):
        minimum = 1.2
    elif rules_lib.same(channel, 'Wholesale'):
        minimum = 1.0
    else:
        return True

    income = ctx['RatioSet.total_monthly_income_usd']
    obligation = ctx['RatioSet.total_monthly_obligation_usd']
    missing = rules_lib.gaps(income=income, obligation=obligation)
    if missing:
        return rules_lib.unknown(*missing)

    dscr = rules_lib.ratio(income, obligation)
    if dscr is None:
        return rules_lib.unknown('income', 'obligation')
    return dscr >= minimum
