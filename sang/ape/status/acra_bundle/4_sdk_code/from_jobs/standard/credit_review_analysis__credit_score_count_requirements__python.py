# rule: acra-standard.credit_review_analysis.credit_score_count_requirements.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_review_analysis.credit_score_count_requirements
# reads: CreditReport.score_count
# implements job: acra-standard.credit_review_analysis.credit_score_count_requirements

import rules_lib

def check(ctx):
    score_count = ctx['CreditReport.score_count']
    missing = rules_lib.gaps(score_count=score_count)
    if missing:
        return rules_lib.unknown(*missing)
    return True
