# rule: acra-platinum.title_review.business_purpose_entity_use.python
# origin: written from a job
# description: Python formalization of acra-platinum.title_review.business_purpose_entity_use
# reads: LoanCore.loan_purpose, SubjectProperty.occupancy_subtype
# implements job: acra-platinum.title_review.business_purpose_entity_use

import rules_lib

def check(ctx):
    loan_purpose = ctx['LoanCore.loan_purpose']
    occupancy_subtype = ctx['SubjectProperty.occupancy_subtype']
    missing = rules_lib.gaps(loan_purpose=loan_purpose, occupancy_subtype=occupancy_subtype)
    if missing:
        return rules_lib.unknown(*missing)
    return rules_lib.same(loan_purpose, 'business purpose') and rules_lib.same(occupancy_subtype, 'investment property')
