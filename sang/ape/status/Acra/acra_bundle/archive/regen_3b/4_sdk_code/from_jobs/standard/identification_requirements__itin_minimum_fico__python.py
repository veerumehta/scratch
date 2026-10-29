# rule: acra-standard.identification_requirements.itin_minimum_fico.python
# origin: written from a job
# description: Python formalization of acra-standard.identification_requirements.itin_minimum_fico
# reads: CreditReport.representative_score
# implements job: acra-standard.identification_requirements.itin_minimum_fico

import rules_lib

def check(ctx):
    representative_score = ctx['CreditReport.representative_score']
    missing = rules_lib.gaps(representative_score=representative_score)
    if missing:
        return rules_lib.unknown(*missing)
    return representative_score >= 640
