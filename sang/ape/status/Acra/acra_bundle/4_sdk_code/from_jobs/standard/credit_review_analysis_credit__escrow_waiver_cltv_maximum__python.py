# rule: acra-standard.credit_review_analysis_credit.escrow_waiver_cltv_maximum.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_review_analysis_credit.escrow_waiver_cltv_maximum
# reads: LoanCore.is_escrow_waived, LoanCore.cltv_percent
# implements job: acra-standard.credit_review_analysis_credit.escrow_waiver_cltv_maximum

import rules_lib

def check(ctx):
    waiver = ctx['LoanCore.is_escrow_waived']
    missing = rules_lib.gaps(waiver=waiver)
    if missing:
        return rules_lib.unknown(*missing)

    waiver_flag = rules_lib.flag(waiver)
    if waiver_flag is None:
        return rules_lib.unknown('LoanCore.is_escrow_waived')
    if not waiver_flag:
        return True

    cltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv=cltv)
    if missing:
        return rules_lib.unknown(*missing)
    cltv_percent = rules_lib.percent(cltv, 'percent')
    if cltv_percent is None:
        return rules_lib.unknown('LoanCore.cltv_percent')
    return cltv_percent <= 80
