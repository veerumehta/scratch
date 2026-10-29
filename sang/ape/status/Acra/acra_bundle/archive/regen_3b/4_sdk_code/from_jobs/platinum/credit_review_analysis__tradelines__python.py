# rule: acra-platinum.credit_review_analysis.tradelines.python
# origin: written from a job
# description: Python formalization of acra-platinum.credit_review_analysis.tradelines
# reads: CreditReport.score_count, CreditReport.tradelines_meet_requirement
# implements job: acra-platinum.credit_review_analysis.tradelines

import rules_lib

def check(ctx):
    score_count = ctx['CreditReport.score_count']
    missing = rules_lib.gaps(score_count=score_count)
    if missing:
        return rules_lib.unknown(*missing)

    if score_count == 3:
        return True
    if score_count == 0:
        return rules_lib.unknown('no_score_pathway')
    if score_count == 1 or score_count == 2:
        tradelines_meet_requirement = ctx['CreditReport.tradelines_meet_requirement']
        missing = rules_lib.gaps(tradelines_meet_requirement=tradelines_meet_requirement)
        if missing:
            return rules_lib.unknown(*missing)
        result = rules_lib.flag(tradelines_meet_requirement)
        if result is None:
            return rules_lib.unknown('tradelines_meet_requirement')
        return result
    return rules_lib.unknown('score_count_category')
