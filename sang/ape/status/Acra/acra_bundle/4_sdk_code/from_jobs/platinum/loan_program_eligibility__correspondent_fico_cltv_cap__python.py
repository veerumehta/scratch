# rule: acra-platinum.loan_program_eligibility.correspondent_fico_cltv_cap.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.correspondent_fico_cltv_cap
# reads: LoanCore.channel, CreditReport.representative_score, LoanCore.cltv_percent
# implements job: acra-platinum.loan_program_eligibility.correspondent_fico_cltv_cap

import rules_lib


def check(ctx):
    channel = ctx['LoanCore.channel']
    score = ctx['CreditReport.representative_score']

    missing = rules_lib.gaps(channel=channel, score=score)
    if missing:
        return rules_lib.unknown(*missing)

    if not rules_lib.same(channel, 'Correspondent') or not (700 <= score <= 719):
        return True

    cltv_percent = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv_percent=cltv_percent)
    if missing:
        return rules_lib.unknown(*missing)

    cltv = rules_lib.percent(cltv_percent, 'percent')
    if cltv is None:
        return rules_lib.unknown('cltv_percent')
    return cltv <= 60
