# rule: acra-platinum.unassigned_provisions.one_or_no_credit_score_treatment.python
# origin: written from a job
# description: Python formalization of acra-platinum.unassigned_provisions.one_or_no_credit_score_treatment
# reads: CreditReport.score_count
# implements job: acra-platinum.unassigned_provisions.one_or_no_credit_score_treatment

import rules_lib

def check(ctx):
    score_count = ctx['CreditReport.score_count']
    missing = rules_lib.gaps(score_count=score_count)
    if missing:
        return rules_lib.unknown(*missing)
    return score_count in (0, 1)
