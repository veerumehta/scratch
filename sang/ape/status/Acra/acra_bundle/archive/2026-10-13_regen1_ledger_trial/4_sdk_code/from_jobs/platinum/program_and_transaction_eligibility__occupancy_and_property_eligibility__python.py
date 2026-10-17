# rule: acra-platinum.program_and_transaction_eligibility.occupancy_and_property_eligibility.python
# origin: written from a job
# description: Python formalization of acra-platinum.program_and_transaction_eligibility.occupancy_and_property_eligibility
# reads: occupancy_subtype, vacant_property, property_type, property_state
# implements job: acra-platinum.program_and_transaction_eligibility.occupancy_and_property_eligibility

import rules_lib


def check(ctx):
    occupancy_subtype = ctx['occupancy_subtype']
    vacant_property = ctx['vacant_property']
    property_type = ctx['property_type']
    property_state = ctx['property_state']

    missing = rules_lib.gaps(
        occupancy_subtype=occupancy_subtype,
        vacant_property=vacant_property,
        property_type=property_type,
        property_state=property_state,
    )
    if missing:
        return rules_lib.unknown(*missing)

    is_non_owner_occupied = rules_lib.same(occupancy_subtype, 'non-owner occupied')
    is_not_vacant = rules_lib.flag(vacant_property) is False
    is_eligible_property_type = rules_lib.same(
        property_type, 'SFR', 'Townhome', 'PUD', 'Warrantable Condo', 'Two-Units'
    )
    is_south_dakota = rules_lib.same(property_state, 'SD')
    is_us_territory = rules_lib.same(
        property_state,
        'U.S. Terr.', 'U.S. Terrs.', 'US Territory', 'US Territories',
        'Puerto Rico', 'PR', 'Guam', 'GU', 'U.S. Virgin Islands', 'USVI', 'VI',
        'American Samoa', 'AS', 'Northern Mariana Islands', 'CNMI', 'MP',
    )

    satisfied = (
        is_non_owner_occupied
        and is_not_vacant
        and is_eligible_property_type
        and not is_south_dakota
        and not is_us_territory
    )
    return satisfied, {
        'occupancy_subtype': occupancy_subtype,
        'vacant_property': vacant_property,
        'property_type': property_type,
        'property_state': property_state,
    }
