# rule: acra-platinum.title_review.entity_documentation.python
# origin: written from a job
# description: Python formalization of acra-platinum.title_review.entity_documentation
# reads: Borrower.entity_documents_complete
# implements job: acra-platinum.title_review.entity_documentation

import rules_lib

def check(ctx):
    entity_documents_complete = ctx['Borrower.entity_documents_complete']
    missing = rules_lib.gaps(entity_documents_complete=entity_documents_complete)
    if missing:
        return rules_lib.unknown(*missing)
    result = rules_lib.flag(entity_documents_complete)
    if result is None:
        return rules_lib.unknown('Borrower.entity_documents_complete')
    return result
