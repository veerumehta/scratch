# rule: acra-standard.title_review.business_entity_transaction.python
# origin: written from a job
# description: Python formalization of acra-standard.title_review.business_entity_transaction
# reads: Borrower.is_entity_borrower_1, LoanCore.loan_purpose, SubjectProperty.occupancy_subtype
# implements job: acra-standard.title_review.business_entity_transaction

import rules_lib


def check(ctx):
    entity_borrower = ctx['Borrower.is_entity_borrower_1']
    loan_purpose = ctx['LoanCore.loan_purpose']
    occupancy_subtype = ctx['SubjectProperty.occupancy_subtype']

    missing = rules_lib.gaps(
        entity_borrower=entity_borrower,
        loan_purpose=loan_purpose,
        occupancy_subtype=occupancy_subtype,
    )
    if missing:
        return rules_lib.unknown(*missing)

    entity_flag = rules_lib.flag(entity_borrower)
    if entity_flag is None:
        return rules_lib.unknown('entity_borrower')

    return (
        entity_flag
        and rules_lib.same(loan_purpose, 'business purpose')
        and rules_lib.same(occupancy_subtype, 'investment')
    )
