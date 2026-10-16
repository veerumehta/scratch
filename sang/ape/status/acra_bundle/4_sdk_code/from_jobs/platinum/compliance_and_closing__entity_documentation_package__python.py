# rule: acra-platinum.compliance_and_closing.entity_documentation_package.python
# origin: written from a job
# description: Python formalization of acra-platinum.compliance_and_closing.entity_documentation_package
# reads: Borrower.entity_documents_complete
# implements job: acra-platinum.compliance_and_closing.entity_documentation_package

import rules_lib

def check(ctx):
    entity_documents_complete = ctx['Borrower.entity_documents_complete']
    missing = rules_lib.gaps(entity_documents_complete=entity_documents_complete)
    if missing:
        return rules_lib.unknown(*missing)
    complete = rules_lib.flag(entity_documents_complete)
    if complete is None:
        return rules_lib.unknown('Borrower.entity_documents_complete')
    return complete
