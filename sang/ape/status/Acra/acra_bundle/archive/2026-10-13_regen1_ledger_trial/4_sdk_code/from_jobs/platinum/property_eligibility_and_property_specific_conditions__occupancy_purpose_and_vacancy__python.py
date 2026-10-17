# rule: acra-platinum.property_eligibility_and_property_specific_conditions.occupancy_purpose_and_vacancy.python
# origin: written from a job
# description: Python formalization of acra-platinum.property_eligibility_and_property_specific_conditions.occupancy_purpose_and_vacancy
# reads: occupancy_subtype, loan_purpose, vacant_property, loan_amount, current_lease_in_place
# implements job: acra-platinum.property_eligibility_and_property_specific_conditions.occupancy_purpose_and_vacancy

import rules_lib

def check(ctx):
    occupancy_subtype = ctx['occupancy_subtype']
    loan_purpose = ctx['loan_purpose']
    vacant_property = ctx['vacant_property']
    missing = rules_lib.gaps(
        occupancy_subtype=occupancy_subtype,
        loan_purpose=loan_purpose,
        vacant_property=vacant_property,
    )
    if missing:
        return rules_lib.unknown(*missing)

    vacant = rules_lib.flag(vacant_property)
    if vacant is None:
        return rules_lib.unknown('vacant_property')
    if vacant or not rules_lib.same(occupancy_subtype, 'Non-Owner Occupied'):
        return False

    is_delayed_financing = rules_lib.same(loan_purpose, 'Delayed Financing')
    is_cash_out = rules_lib.same(loan_purpose, 'Cash-Out Refinance')
    if not any(rules_lib.same(loan_purpose, purpose) for purpose in (
        'Purchase', 'Rate & Term Refinance', 'Cash-Out Refinance', 'Delayed Financing'
    )):
        return False

    if is_delayed_financing:
        loan_amount = ctx['loan_amount']
        missing = rules_lib.gaps(loan_amount=loan_amount)
        if missing:
            return rules_lib.unknown(*missing)
        if loan_amount > 1_500_000:
            return False

    if is_cash_out:
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
