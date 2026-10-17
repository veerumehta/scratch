# rule: acra-standard.credit_review_analysis.one_or_no_score_deficient_tradelines.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_review_analysis.one_or_no_score_deficient_tradelines
# reads: CreditReport.score_count, CreditReport.tradelines_meet_requirement, LoanCore.cltv_percent
# implements job: acra-standard.credit_review_analysis.one_or_no_score_deficient_tradelines

def check(ctx):
    score_count = ctx['CreditReport.score_count']
    tradelines_meet_requirement = ctx['CreditReport.tradelines_meet_requirement']
    cltv_percent = ctx['LoanCore.cltv_percent']

    missing = rules_lib.gaps(
        score_count=score_count,
        tradelines_meet_requirement=tradelines_meet_requirement,
        cltv_percent=cltv_percent,
    )
    if missing:
        return rules_lib.unknown(*missing)

    tradelines_ok = rules_lib.flag(tradelines_meet_requirement)
    if tradelines_ok is None:
        return rules_lib.unknown('tradelines_meet_requirement')

    if score_count <= 1 or not tradelines_ok:
        return cltv_percent <= 65
    return True
