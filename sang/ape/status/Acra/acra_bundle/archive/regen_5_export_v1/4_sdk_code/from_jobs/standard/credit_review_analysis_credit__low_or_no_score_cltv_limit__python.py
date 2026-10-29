# rule: acra-standard.credit_review_analysis_credit.low_or_no_score_cltv_limit.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_review_analysis_credit.low_or_no_score_cltv_limit
# reads: CreditReport.score_count, CreditReport.tradelines_meet_requirement, LoanCore.cltv_percent
# implements job: acra-standard.credit_review_analysis_credit.low_or_no_score_cltv_limit

import rules_lib

def check(ctx):
    score_count = ctx['CreditReport.score_count']
    tradelines_meet_requirement = ctx['CreditReport.tradelines_meet_requirement']
    missing = rules_lib.gaps(
        score_count=score_count,
        tradelines_meet_requirement=tradelines_meet_requirement,
    )
    if missing:
        return rules_lib.unknown(*missing)

    score_count_is_one_or_less = rules_lib.band(score_count, [(1, True)], above=False)
    tradelines_meet_requirement = rules_lib.flag(tradelines_meet_requirement)
    if score_count_is_one_or_less is None:
        return rules_lib.unknown('score_count')
    if tradelines_meet_requirement is None:
        return rules_lib.unknown('tradelines_meet_requirement')

    if score_count_is_one_or_less or not tradelines_meet_requirement:
        cltv_percent = ctx['LoanCore.cltv_percent']
        missing = rules_lib.gaps(cltv_percent=cltv_percent)
        if missing:
            return rules_lib.unknown(*missing)
        cltv_percent = rules_lib.percent(cltv_percent, 'percent')
        if cltv_percent is None:
            return rules_lib.unknown('cltv_percent')
        return cltv_percent <= 65

    return True
