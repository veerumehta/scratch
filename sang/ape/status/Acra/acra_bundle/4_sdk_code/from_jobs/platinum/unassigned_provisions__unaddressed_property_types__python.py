# rule: acra-platinum.unassigned_provisions.unaddressed_property_types.python
# origin: written from a job
# description: Python formalization of acra-platinum.unassigned_provisions.unaddressed_property_types
# reads: SubjectProperty.number_of_units, SubjectProperty.property_type, SubjectProperty.is_mixed_use
# implements job: acra-platinum.unassigned_provisions.unaddressed_property_types

import rules_lib

def check(ctx):
    units = ctx['SubjectProperty.number_of_units']
    property_type = ctx['SubjectProperty.property_type']
    mixed_use_value = ctx['SubjectProperty.is_mixed_use']

    missing = rules_lib.gaps(units=units, property_type=property_type, mixed_use=mixed_use_value)
    if missing:
        return rules_lib.unknown(*missing)

    mixed_use = rules_lib.flag(mixed_use_value)
    unit_match = rules_lib.band(units, [(2, False), (4, True)], above=False)
    if mixed_use is None or unit_match is None:
        return rules_lib.unknown('mixed_use' if mixed_use is None else 'units')

    return (
        mixed_use
        or unit_match
        or rules_lib.same(property_type, 'manufactured home', 'PUDtel')
    )
