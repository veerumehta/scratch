# rule: acra-platinum.title_review.entity_form_eligibility.python
# origin: written from a job
# description: Python formalization of acra-platinum.title_review.entity_form_eligibility
# reads: Borrower.entity_type
# implements job: acra-platinum.title_review.entity_form_eligibility

import rules_lib

def check(ctx):
    entity_type = ctx['Borrower.entity_type']
    missing = rules_lib.gaps(entity_type=entity_type)
    if missing:
        return rules_lib.unknown(*missing)

    return rules_lib.same(
        entity_type,
        'Domestic Corporation',
        'C Corp',
        'S Corp',
        'LLC',
        'Single Purpose LLC',
        'Limited Liability Company',
        'Single Purpose Limited Liability Company',
        'LLP',
        'Limited Liability Partnership',
        'LLLP',
        'Limited Liability Limited Partnership',
        'GP',
        'General Partnership',
        'LP',
        'Limited Partnership',
        'Sole Proprietorship',
    )
