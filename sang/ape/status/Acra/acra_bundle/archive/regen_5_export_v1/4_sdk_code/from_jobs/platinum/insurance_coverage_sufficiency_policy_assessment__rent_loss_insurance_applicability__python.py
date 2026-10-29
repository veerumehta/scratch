# rule: acra-platinum.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_applicability.python
# origin: written from a job
# description: Python formalization of acra-platinum.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_applicability
# reads: SubjectProperty.number_of_units, SubjectProperty.occupancy_subtype, LoanCore.cltv_percent
# implements job: acra-platinum.insurance_coverage_sufficiency_policy_assessment.rent_loss_insurance_applicability

import rules_lib

def check(ctx):
    units = ctx['SubjectProperty.number_of_units']
    occupancy = ctx['SubjectProperty.occupancy_subtype']
    cltv_raw = ctx['LoanCore.cltv_percent']

    missing = rules_lib.gaps(
        number_of_units=units,
        occupancy_subtype=occupancy,
        cltv_percent=cltv_raw,
    )
    if missing:
        return rules_lib.unknown(*missing)

    cltv = rules_lib.percent(cltv_raw, 'percent')
    if cltv is None:
        return rules_lib.unknown('cltv_percent')

    if rules_lib.same(occupancy, 'non-owner occupied'):
        non_owner_occupied = True
    elif rules_lib.same(occupancy, 'owner occupied'):
        non_owner_occupied = False
    else:
        return rules_lib.unknown('occupancy_subtype')

    return 1 <= units <= 4 and non_owner_occupied and cltv <= 70
