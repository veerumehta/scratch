# rule: acra-platinum.compliance_and_closing.entity_type_eligibility.python
# origin: written from a job
# description: Python formalization of acra-platinum.compliance_and_closing.entity_type_eligibility
# reads: Borrower.entity_type
# implements job: acra-platinum.compliance_and_closing.entity_type_eligibility

import rules_lib

def check(ctx):
    entity_type = ctx['Borrower.entity_type']
    missing = rules_lib.gaps(entity_type=entity_type)
    if missing:
        return rules_lib.unknown(*missing)

    return rules_lib.same(
        entity_type,
        'Domestic Corporation', 'C Corp', 'S Corp',
        'Single Purpose LLC', 'Single Purpose Limited Liability Company',
        'LLC', 'Limited Liability Company',
        'Limited Liability Partnership', 'LLP',
        'Limited Liability Limited Partnership', 'LLLP',
        'General Partnership', 'GP',
        'Limited Partnership', 'LP',
        'Sole Proprietorship'
    )
