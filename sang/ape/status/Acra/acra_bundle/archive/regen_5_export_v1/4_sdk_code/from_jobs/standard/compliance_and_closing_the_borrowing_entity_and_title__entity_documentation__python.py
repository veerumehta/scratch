# rule: acra-standard.compliance_and_closing_the_borrowing_entity_and_title.entity_documentation.python
# origin: written from a job
# description: Python formalization of acra-standard.compliance_and_closing_the_borrowing_entity_and_title.entity_documentation
# reads: Borrower.entity_documents_complete
# implements job: acra-standard.compliance_and_closing_the_borrowing_entity_and_title.entity_documentation

import rules_lib

def check(ctx):
    complete = ctx['Borrower.entity_documents_complete']
    missing = rules_lib.gaps(entity_documents_complete=complete)
    if missing:
        return rules_lib.unknown(*missing)

    complete_flag = rules_lib.flag(complete)
    if complete_flag is None:
        return rules_lib.unknown('Borrower.entity_documents_complete')
    return complete_flag
