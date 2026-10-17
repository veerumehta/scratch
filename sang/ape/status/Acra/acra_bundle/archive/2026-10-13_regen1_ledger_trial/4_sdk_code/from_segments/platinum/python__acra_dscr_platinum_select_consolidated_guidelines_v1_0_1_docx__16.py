# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.16
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶2
# reads: borrower_entity_type, entity_documents_complete, first_time_homebuyer

import rules_lib


def check(ctx):
    borrower_entity_type = ctx['borrower_entity_type']
    entity_documents_complete = ctx['entity_documents_complete']
    first_time_homebuyer = ctx['first_time_homebuyer']

    missing = rules_lib.gaps(
        borrower_entity_type=borrower_entity_type,
        entity_documents_complete=entity_documents_complete,
        first_time_homebuyer=first_time_homebuyer,
    )
    if missing:
        return rules_lib.unknown(*missing)

    documents_complete = rules_lib.flag(entity_documents_complete)
    is_first_time = rules_lib.flag(first_time_homebuyer)
    if documents_complete is None or is_first_time is None:
        uncertain = []
        if documents_complete is None:
            uncertain.append('entity_documents_complete')
        if is_first_time is None:
            uncertain.append('first_time_homebuyer')
        return rules_lib.unknown(*uncertain)

    allowed_type = any(rules_lib.same(borrower_entity_type, option) for option in (
        'C Corp', 'C Corporation', 'S Corp', 'S Corporation',
        'Single Purpose LLC', 'Single Purpose Limited Liability Company',
        'LLP', 'Limited Liability Partnership',
        'LLLP', 'Limited Liability Limited Partnership',
        'GP', 'General Partnership',
        'LP', 'Limited Partnership',
        'Sole Proprietorship',
    ))

    return allowed_type and documents_complete and not is_first_time
