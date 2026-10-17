# rule: acra-platinum.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_applicability.python
# origin: written from a job
# description: Python formalization of acra-platinum.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_applicability
# reads: SubjectProperty.number_of_units, SubjectProperty.occupancy_subtype
# implements job: acra-platinum.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_applicability

import rules_lib

def check(ctx):
    units = ctx['SubjectProperty.number_of_units']
    occupancy = ctx['SubjectProperty.occupancy_subtype']
    missing = rules_lib.gaps(units=units, occupancy=occupancy)
    if missing:
        return rules_lib.unknown(*missing)
    return 1 <= units <= 4 and not rules_lib.same(occupancy, 'owner occupied')
