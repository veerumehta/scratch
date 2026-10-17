# rule: acra-standard.compliance_and_closing.listed_property_tenant_occupancy.python
# origin: written from a job
# description: Python formalization of acra-standard.compliance_and_closing.listed_property_tenant_occupancy
# reads: SubjectProperty.occupancy_subtype, SubjectProperty.has_current_lease, SubjectProperty.is_vacant
# implements job: acra-standard.compliance_and_closing.listed_property_tenant_occupancy

import rules_lib


def check(ctx):
    occupancy_subtype = ctx['SubjectProperty.occupancy_subtype']
    missing = rules_lib.gaps(occupancy_subtype=occupancy_subtype)
    if missing:
        return rules_lib.unknown(*missing)

    if not rules_lib.same(occupancy_subtype, 'investment', 'investment property'):
        return True

    has_current_lease = ctx['SubjectProperty.has_current_lease']
    is_vacant = ctx['SubjectProperty.is_vacant']
    missing = rules_lib.gaps(
        has_current_lease=has_current_lease,
        is_vacant=is_vacant,
    )
    if missing:
        return rules_lib.unknown(*missing)

    has_current_lease = rules_lib.flag(has_current_lease)
    is_vacant = rules_lib.flag(is_vacant)
    if has_current_lease is None or is_vacant is None:
        return rules_lib.unknown('SubjectProperty.has_current_lease', 'SubjectProperty.is_vacant')

    return has_current_lease and not is_vacant
