# rule: acra-platinum.asset_assessment.listed_property_occupancy.python
# origin: written from a job
# description: Python formalization of acra-platinum.asset_assessment.listed_property_occupancy
# reads: SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.occupancy_subtype, SubjectProperty.has_current_lease, SubjectProperty.is_vacant
# implements job: acra-platinum.asset_assessment.listed_property_occupancy

import rules_lib


def check(ctx):
    listed = rules_lib.flag(ctx['SubjectProperty.listed_for_sale_last_6_months'])
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)
    if not listed:
        return True

    occupancy = ctx['SubjectProperty.occupancy_subtype']
    missing = rules_lib.gaps(occupancy=occupancy)
    if missing:
        return rules_lib.unknown(*missing)
    if not rules_lib.same(occupancy, 'investment'):
        return True

    has_current_lease = rules_lib.flag(ctx['SubjectProperty.has_current_lease'])
    is_vacant = rules_lib.flag(ctx['SubjectProperty.is_vacant'])
    missing = rules_lib.gaps(
        has_current_lease=has_current_lease,
        is_vacant=is_vacant,
    )
    if missing:
        return rules_lib.unknown(*missing)
    return has_current_lease and not is_vacant
