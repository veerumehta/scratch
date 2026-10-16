# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.13
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶14
# reads: citizenship_type, first_time_homebuyer, loan_purpose, current_lease_in_place

import rules_lib


def check(ctx):
    citizenship_type = ctx['citizenship_type']
    first_time_homebuyer = ctx['first_time_homebuyer']
    missing = rules_lib.gaps(
        citizenship_type=citizenship_type,
        first_time_homebuyer=first_time_homebuyer,
    )
    if missing:
        return rules_lib.unknown(*missing)

    first_time = rules_lib.flag(first_time_homebuyer)
    if first_time is None:
        return rules_lib.unknown('first_time_homebuyer')
    if first_time:
        return False

    eligible_citizenship = (
        rules_lib.same(citizenship_type, 'US Citizen')
        or rules_lib.same(citizenship_type, 'Permanent Resident')
    )
    if not eligible_citizenship:
        return False

    loan_purpose = ctx['loan_purpose']
    missing = rules_lib.gaps(loan_purpose=loan_purpose)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(loan_purpose, 'cash-out refinance'):
        current_lease_in_place = ctx['current_lease_in_place']
        missing = rules_lib.gaps(current_lease_in_place=current_lease_in_place)
        if missing:
            return rules_lib.unknown(*missing)
        lease_in_place = rules_lib.flag(current_lease_in_place)
        if lease_in_place is None:
            return rules_lib.unknown('current_lease_in_place')
        if not lease_in_place:
            return False

    return True
