# rule: acra-standard.property_eligibility_and_property_specific_overlays.determine_rent_loss_insurance_requirement.python
# origin: written from a job
# description: Python formalization of acra-standard.property_eligibility_and_property_specific_overlays.determine_rent_loss_insurance_requirement
# reads: cltv_pct, occupancy_subtype, residential_unit_count
# implements job: acra-standard.property_eligibility_and_property_specific_overlays.determine_rent_loss_insurance_requirement

import rules_lib

def check(ctx):
    cltv_pct = ctx['cltv_pct']
    occupancy_subtype = ctx['occupancy_subtype']
    residential_unit_count = ctx['residential_unit_count']

    missing = rules_lib.gaps(
        cltv_pct=cltv_pct,
        occupancy_subtype=occupancy_subtype,
        residential_unit_count=residential_unit_count,
    )
    if missing:
        return rules_lib.unknown(*missing)

    units_in_range = rules_lib.match(residential_unit_count, (1, 2, 3, 4)) is not None
    non_owner_income_property = rules_lib.match(
        occupancy_subtype,
        (
            'Investment',
            'Investment Property',
            'Non-Owner Occupied',
            'Non-Owner Occupied Investment Property',
            'Non-Owner Occupied Income Property',
            'Rental',
            'Rental Property',
        ),
    ) is not None

    return units_in_range and non_owner_income_property and cltv_pct > 70
