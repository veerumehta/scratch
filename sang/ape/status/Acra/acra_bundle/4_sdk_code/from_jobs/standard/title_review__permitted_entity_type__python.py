# rule: acra-standard.title_review.permitted_entity_type.python
# origin: written from a job
# description: Python formalization of acra-standard.title_review.permitted_entity_type
# reads: Borrower.entity_type
# implements job: acra-standard.title_review.permitted_entity_type

import rules_lib

def check(ctx):
    entity_type = ctx['Borrower.entity_type']
    missing = rules_lib.gaps(entity_type=entity_type)
    if missing:
        return rules_lib.unknown(*missing)

    return rules_lib.same(
        entity_type,
        'Domestic Corporation', 'C Corp', 'C Corporation',
        'S Corp', 'S Corporation',
        'Limited Liability Company', 'LLC', 'Single Purpose LLC',
        'Series LLC', 'Series Limited Liability Company',
        'Limited Liability Partnership', 'LLP',
        'Limited Liability Limited Partnership', 'LLLP',
        'General Partnership', 'GP',
        'Limited Partnership', 'LP',
        'Sole Proprietorship',
    )
