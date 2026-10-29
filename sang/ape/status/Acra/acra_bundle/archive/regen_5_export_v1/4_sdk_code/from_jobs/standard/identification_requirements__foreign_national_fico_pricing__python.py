# rule: acra-standard.identification_requirements.foreign_national_fico_pricing.python
# origin: written from a job
# description: Python formalization of acra-standard.identification_requirements.foreign_national_fico_pricing
# reads: Borrower.citizenship_status, CreditReport.representative_score
# implements job: acra-standard.identification_requirements.foreign_national_fico_pricing

import rules_lib

def check(ctx):
    citizenship = ctx['Borrower.citizenship_status']
    missing = rules_lib.gaps(citizenship=citizenship)
    if missing:
        return rules_lib.unknown(*missing)

    if not rules_lib.same(citizenship, 'Foreign National'):
        return True

    representative_score = ctx['CreditReport.representative_score']
    missing = rules_lib.gaps(representative_score=representative_score)
    if missing:
        return rules_lib.unknown(*missing)

    return representative_score == 700
