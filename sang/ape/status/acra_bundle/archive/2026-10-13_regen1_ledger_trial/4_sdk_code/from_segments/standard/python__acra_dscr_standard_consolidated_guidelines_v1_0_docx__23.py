# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.23
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
    first_time = rules_lib.flag(first_time_homebuyer)
    if documents_complete is None or first_time is None:
        invalid = []
        if documents_complete is None:
            invalid.append('entity_documents_complete')
        if first_time is None:
            invalid.append('first_time_homebuyer')
        return rules_lib.unknown(*invalid)

    allowed_type = any(
        rules_lib.same(
            borrower_entity_type,
            'Domestic Corporation', 'Domestic C Corp', 'Domestic S Corp',
            'C Corp', 'S Corp',
            'Single Purpose LLC',
            'Limited Liability Partnership', 'LLP',
            'Limited Liability Limited Partnership', 'LLLP',
            'General Partnership', 'GP',
            'Limited Partnership', 'LP',
            'Sole Proprietorship',
        )
        for _ in (0,)
    )

    return allowed_type and documents_complete and not first_time
