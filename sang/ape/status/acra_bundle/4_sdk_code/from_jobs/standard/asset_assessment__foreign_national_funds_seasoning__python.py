# rule: acra-standard.asset_assessment.foreign_national_funds_seasoning.python
# origin: written from a job
# description: Python formalization of acra-standard.asset_assessment.foreign_national_funds_seasoning
# reads: Borrower.citizenship_status
# implements job: acra-standard.asset_assessment.foreign_national_funds_seasoning

import rules_lib

def check(ctx):
    citizenship_status = ctx['Borrower.citizenship_status']
    missing = rules_lib.gaps(citizenship_status=citizenship_status)
    if missing:
        return rules_lib.unknown(*missing)
    if rules_lib.same(citizenship_status, 'foreign national'):
        return rules_lib.unknown('60-day seasoning documentation')
    return True
