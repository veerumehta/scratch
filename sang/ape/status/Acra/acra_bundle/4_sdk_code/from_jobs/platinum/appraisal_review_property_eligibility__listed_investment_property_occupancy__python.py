# rule: acra-platinum.appraisal_review_property_eligibility.listed_investment_property_occupancy.python
# origin: written from a job
# description: Python formalization of acra-platinum.appraisal_review_property_eligibility.listed_investment_property_occupancy
# reads: SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.occupancy_subtype, SubjectProperty.has_current_lease, SubjectProperty.is_vacant
# implements job: acra-platinum.appraisal_review_property_eligibility.listed_investment_property_occupancy

import rules_lib


def check(ctx):
    listed = ctx['SubjectProperty.listed_for_sale_last_6_months']
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)
    listed = rules_lib.flag(listed)
    if listed is None:
        return rules_lib.unknown('listed')
    if not listed:
        return True

    occupancy_subtype = ctx['SubjectProperty.occupancy_subtype']
    missing = rules_lib.gaps(occupancy_subtype=occupancy_subtype)
    if missing:
        return rules_lib.unknown(*missing)
    if not rules_lib.same(occupancy_subtype, 'investment', 'investment property'):
        return True

    has_current_lease = ctx['SubjectProperty.has_current_lease']
    is_vacant = ctx['SubjectProperty.is_vacant']
    missing = rules_lib.gaps(has_current_lease=has_current_lease, is_vacant=is_vacant)
    if missing:
        return rules_lib.unknown(*missing)
    has_current_lease = rules_lib.flag(has_current_lease)
    is_vacant = rules_lib.flag(is_vacant)
    if has_current_lease is None or is_vacant is None:
        return rules_lib.unknown('has_current_lease', 'is_vacant')
    return has_current_lease and not is_vacant
