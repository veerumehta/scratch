# rule: acra-standard.identification_requirements.permanent_resident_documents.python
# origin: written from a job
# description: Python formalization of acra-standard.identification_requirements.permanent_resident_documents
# reads: Borrower.citizenship_status
# implements job: acra-standard.identification_requirements.permanent_resident_documents

import rules_lib

def check(ctx):
    citizenship_status = ctx['Borrower.citizenship_status']
    missing = rules_lib.gaps(citizenship_status=citizenship_status)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(citizenship_status, 'Permanent Resident'):
        return rules_lib.unknown('unexpired PRA ID', 'SSA card or SSA-89')

    return True
