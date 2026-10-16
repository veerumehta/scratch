# rule: acra-platinum.title_review.listed_investment_property_occupancy.python
# origin: written from a job
# description: Python formalization of acra-platinum.title_review.listed_investment_property_occupancy
# reads: SubjectProperty.listed_for_sale_last_6_months, SubjectProperty.occupancy_subtype, SubjectProperty.has_current_lease, SubjectProperty.is_vacant
# implements job: acra-platinum.title_review.listed_investment_property_occupancy

def check(ctx):
    listed = ctx['SubjectProperty.listed_for_sale_last_6_months']
    occupancy = ctx['SubjectProperty.occupancy_subtype']
    missing = rules_lib.gaps(listed=listed, occupancy=occupancy)
    if missing:
        return rules_lib.unknown(*missing)

    listed_flag = rules_lib.flag(listed)
    if listed_flag is None:
        return rules_lib.unknown('SubjectProperty.listed_for_sale_last_6_months')
    if not listed_flag or not rules_lib.same(occupancy, 'investment', 'investment property'):
        return True

    lease = ctx['SubjectProperty.has_current_lease']
    vacant = ctx['SubjectProperty.is_vacant']
    missing = rules_lib.gaps(lease=lease, vacant=vacant)
    if missing:
        return rules_lib.unknown(*missing)

    lease_flag = rules_lib.flag(lease)
    vacant_flag = rules_lib.flag(vacant)
    if lease_flag is None:
        return rules_lib.unknown('SubjectProperty.has_current_lease')
    if vacant_flag is None:
        return rules_lib.unknown('SubjectProperty.is_vacant')
    return lease_flag and not vacant_flag
