# rule: acra-platinum.credit_review_analysis_credit.tradelines.python
# origin: written from a job
# description: Python formalization of acra-platinum.credit_review_analysis_credit.tradelines
# reads: CreditReport.score_count, CreditReport.tradelines_meet_requirement
# implements job: acra-platinum.credit_review_analysis_credit.tradelines

import rules_lib

def check(ctx):
    score_count = ctx['CreditReport.score_count']
    missing = rules_lib.gaps(score_count=score_count)
    if missing:
        return rules_lib.unknown(*missing)

    if score_count == 3:
        return True
    if score_count <= 2:
        tradelines_meet_requirement = ctx['CreditReport.tradelines_meet_requirement']
        missing = rules_lib.gaps(tradelines_meet_requirement=tradelines_meet_requirement)
        if missing:
            return rules_lib.unknown(*missing)
        return rules_lib.flag(tradelines_meet_requirement)
    return False
