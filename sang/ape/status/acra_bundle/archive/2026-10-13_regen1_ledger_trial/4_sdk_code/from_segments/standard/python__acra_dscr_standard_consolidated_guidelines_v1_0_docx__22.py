# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.22
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶1
# reads: entity_is_borrower_1, loan_purpose, property_type

import rules_lib

def check(ctx):
    entity_is_borrower_1 = ctx['entity_is_borrower_1']
    missing = rules_lib.gaps(entity_is_borrower_1=entity_is_borrower_1)
    if missing:
        return rules_lib.unknown(*missing)

    entity_borrower = rules_lib.flag(entity_is_borrower_1)
    if entity_borrower is None:
        return rules_lib.unknown('entity_is_borrower_1')
    if not entity_borrower:
        return True

    loan_purpose = ctx['loan_purpose']
    property_type = ctx['property_type']
    missing = rules_lib.gaps(loan_purpose=loan_purpose, property_type=property_type)
    if missing:
        return rules_lib.unknown(*missing)

    return (
        rules_lib.same(loan_purpose, 'business purpose')
        and rules_lib.same(property_type, 'investment property')
    )
