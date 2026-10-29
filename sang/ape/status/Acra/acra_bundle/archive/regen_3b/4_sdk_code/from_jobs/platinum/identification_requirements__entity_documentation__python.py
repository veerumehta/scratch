# rule: acra-platinum.identification_requirements.entity_documentation.python
# origin: written from a job
# description: Python formalization of acra-platinum.identification_requirements.entity_documentation
# reads: Borrower.is_entity_borrower_1, Borrower.entity_documents_complete
# implements job: acra-platinum.identification_requirements.entity_documentation

import rules_lib

def check(ctx):
    is_entity = ctx['Borrower.is_entity_borrower_1']
    documents_complete = ctx['Borrower.entity_documents_complete']

    missing = rules_lib.gaps(
        is_entity_borrower_1=is_entity,
        entity_documents_complete=documents_complete,
    )
    if missing:
        return rules_lib.unknown(*missing)

    is_entity = rules_lib.flag(is_entity)
    documents_complete = rules_lib.flag(documents_complete)

    if is_entity is None:
        return rules_lib.unknown('is_entity_borrower_1')
    if documents_complete is None:
        return rules_lib.unknown('entity_documents_complete')
    return not is_entity or documents_complete
