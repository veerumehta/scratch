# rule: acra-platinum.loan_amount_decisioning_score_and_cltv_limits.determine_decisioning_score_and_tradelines.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_amount_decisioning_score_and_cltv_limits.determine_decisioning_score_and_tradelines
# reads: fico, credit_score_count, tradelines_meet_requirement
# implements job: acra-platinum.loan_amount_decisioning_score_and_cltv_limits.determine_decisioning_score_and_tradelines

import rules_lib

def check(ctx):
    fico = ctx['fico']
    credit_score_count = ctx['credit_score_count']
    missing = rules_lib.gaps(fico=fico, credit_score_count=credit_score_count)
    if missing:
        return rules_lib.unknown(*missing)

    if fico < 700:
        return False
    if credit_score_count == 3:
        return True
    if credit_score_count <= 2:
        tradelines_meet_requirement = ctx['tradelines_meet_requirement']
        missing = rules_lib.gaps(tradelines_meet_requirement=tradelines_meet_requirement)
        if missing:
            return rules_lib.unknown(*missing)
        tradelines_meet_requirement = rules_lib.flag(tradelines_meet_requirement)
        if tradelines_meet_requirement is None:
            return rules_lib.unknown('tradelines_meet_requirement')
        return tradelines_meet_requirement
    return False
