# rule: acra-standard.income_stability_sufficiency_analysis.verify_vacant_property_rent_source.python
# origin: written from a job
# description: Python formalization of acra-standard.income_stability_sufficiency_analysis.verify_vacant_property_rent_source
# reads: LoanCore.loan_purpose, SubjectProperty.is_vacant
# implements job: acra-standard.income_stability_sufficiency_analysis.verify_vacant_property_rent_source

import rules_lib

def check(ctx):
    purpose = ctx['LoanCore.loan_purpose']
    vacant = ctx['SubjectProperty.is_vacant']

    missing = rules_lib.gaps(purpose=purpose, vacant=vacant)
    if missing:
        return rules_lib.unknown(*missing)

    vacant_flag = rules_lib.flag(vacant)
    if vacant_flag is None:
        return rules_lib.unknown('SubjectProperty.is_vacant')

    if not rules_lib.same(purpose, 'purchase') or not vacant_flag:
        return True

    # No allowed context field states whether the rents came from Form 1007 or 1025.
    return rules_lib.unknown('appraisal rent source (Form 1007 or Form 1025)')
