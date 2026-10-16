# rule: acra-platinum.title_review.entity_ownership_structure.python
# origin: written from a job
# description: Python formalization of acra-platinum.title_review.entity_ownership_structure
# reads: Borrower.entity_type
# implements job: acra-platinum.title_review.entity_ownership_structure

import rules_lib

def check(ctx):
    entity_type = ctx['Borrower.entity_type']
    missing = rules_lib.gaps(entity_type=entity_type)
    if missing:
        return rules_lib.unknown(*missing)
    prohibited = rules_lib.same(
        entity_type,
        'Cooperatives',
        'Irrevocable Trusts',
        'Land Trusts',
        'IRAs',
        'Non-Profit',
        'Joint Ventures',
    )
    return not prohibited
