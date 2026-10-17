# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.15
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶1
# reads: borrower_entity_type, loan_purpose, property_type

import rules_lib

def check(ctx):
    borrower_entity_type = ctx['borrower_entity_type']
    loan_purpose = ctx['loan_purpose']
    property_type = ctx['property_type']

    missing = rules_lib.gaps(
        borrower_entity_type=borrower_entity_type,
        loan_purpose=loan_purpose,
        property_type=property_type,
    )
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(borrower_entity_type, 'individual person', 'individual'):
        return True

    if rules_lib.same(borrower_entity_type, 'series limited liability company'):
        return False

    if not rules_lib.same(loan_purpose, 'business purpose'):
        return False
    if not rules_lib.same(property_type, 'investment property'):
        return False
    if not rules_lib.same(borrower_entity_type, 'SPE'):
        return False

    return True
