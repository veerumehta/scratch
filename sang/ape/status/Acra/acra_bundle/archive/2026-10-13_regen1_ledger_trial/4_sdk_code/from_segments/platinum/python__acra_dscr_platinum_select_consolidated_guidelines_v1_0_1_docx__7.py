# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.7
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶8
# reads: loan_purpose, vacant_property, channel, gross_rental_income, pitia, current_lease_in_place

import rules_lib

def check(ctx):
    loan_purpose = ctx['loan_purpose']
    missing = rules_lib.gaps(loan_purpose=loan_purpose)
    if missing:
        return rules_lib.unknown(*missing)
    if not any(rules_lib.same(loan_purpose, purpose) for purpose in (
        'Purchase', 'Rate & Term Refinance', 'Cash-Out Refinance', 'Delayed Financing'
    )):
        return False

    vacant_property = ctx['vacant_property']
    channel = ctx['channel']
    gross_rental_income = ctx['gross_rental_income']
    pitia = ctx['pitia']
    missing = rules_lib.gaps(
        vacant_property=vacant_property,
        channel=channel,
        gross_rental_income=gross_rental_income,
        pitia=pitia,
    )
    if missing:
        return rules_lib.unknown(*missing)

    vacant = rules_lib.flag(vacant_property)
    if vacant is None:
        return rules_lib.unknown('vacant_property')
    if vacant:
        return False

    dscr = rules_lib.ratio(gross_rental_income, pitia)
    if dscr is None:
        return rules_lib.unknown('gross_rental_income', 'pitia')

    if rules_lib.same(channel, 'Correspondent'):
        minimum_dscr = 1.2
    elif rules_lib.same(channel, 'Wholesale'):
        minimum_dscr = 1.0
    else:
        return False

    if dscr < minimum_dscr:
        return False

    if rules_lib.same(loan_purpose, 'Cash-Out Refinance'):
        current_lease_in_place = ctx['current_lease_in_place']
        missing = rules_lib.gaps(current_lease_in_place=current_lease_in_place)
        if missing:
            return rules_lib.unknown(*missing)
        lease = rules_lib.flag(current_lease_in_place)
        if lease is None:
            return rules_lib.unknown('current_lease_in_place')
        if not lease:
            return False

    return True
