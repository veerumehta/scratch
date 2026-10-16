# rule: acra-platinum.title_review.single_purpose_entity.python
# origin: written from a job
# description: Python formalization of acra-platinum.title_review.single_purpose_entity
# reads: Borrower.entity_type
# implements job: acra-platinum.title_review.single_purpose_entity

import rules_lib

def check(ctx):
    entity_type = ctx['Borrower.entity_type']
    missing = rules_lib.gaps(entity_type=entity_type)
    if missing:
        return rules_lib.unknown(*missing)
    return not rules_lib.same(entity_type, 'series LLC', 'series limited liability company')
