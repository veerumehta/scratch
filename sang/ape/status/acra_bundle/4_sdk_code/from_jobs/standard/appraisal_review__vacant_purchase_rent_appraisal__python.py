# rule: acra-standard.appraisal_review.vacant_purchase_rent_appraisal.python
# origin: written from a job
# description: Python formalization of acra-standard.appraisal_review.vacant_purchase_rent_appraisal
# reads: SubjectProperty.is_vacant, LoanCore.loan_purpose
# implements job: acra-standard.appraisal_review.vacant_purchase_rent_appraisal

import rules_lib

def check(ctx):
    vacant_raw = ctx['SubjectProperty.is_vacant']
    purpose = ctx['LoanCore.loan_purpose']

    missing = rules_lib.gaps(vacant=vacant_raw, purpose=purpose)
    if missing:
        return rules_lib.unknown(*missing)

    vacant = rules_lib.flag(vacant_raw)
    if vacant is None:
        return rules_lib.unknown('SubjectProperty.is_vacant')

    if not vacant or not rules_lib.same(purpose, 'purchase'):
        return True

    return rules_lib.unknown('qualifying rent source (Form 1007 or Form 1025)')
