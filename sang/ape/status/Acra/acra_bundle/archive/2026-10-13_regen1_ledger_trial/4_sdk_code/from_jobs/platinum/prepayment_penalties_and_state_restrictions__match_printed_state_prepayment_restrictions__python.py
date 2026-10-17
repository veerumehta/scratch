# rule: acra-platinum.prepayment_penalties_and_state_restrictions.match_printed_state_prepayment_restrictions.python
# origin: written from a job
# description: Python formalization of acra-platinum.prepayment_penalties_and_state_restrictions.match_printed_state_prepayment_restrictions
# reads: property_state, property_type, residential_unit_count, borrower_entity_type, loan_amount, interest_rate, loan_purpose
# implements job: acra-platinum.prepayment_penalties_and_state_restrictions.match_printed_state_prepayment_restrictions

import rules_lib

def check(ctx):
    property_state = ctx['property_state']
    missing = rules_lib.gaps(property_state=property_state)
    if missing:
        return rules_lib.unknown(*missing)

    def residential_units_in_range(property_type, residential_unit_count, low, high):
        if not (
            rules_lib.same(property_type, 'residential')
            or rules_lib.same(property_type, 'residential 1-4')
            or rules_lib.same(property_type, 'residential 1-2')
            or rules_lib.same(property_type, 'residential 1 unit')
        ):
            return False
        if not rules_lib.known(residential_unit_count):
            return None
        return low <= residential_unit_count <= high

    if rules_lib.same(property_state, 'AK'):
        property_type = ctx['property_type']
        residential_unit_count = ctx['residential_unit_count']
        missing = rules_lib.gaps(property_type=property_type, residential_unit_count=residential_unit_count)
        if missing:
            return rules_lib.unknown(*missing)
        result = residential_units_in_range(property_type, residential_unit_count, 1, 4)
        return rules_lib.unknown('residential_unit_count') if result is None else result

    if rules_lib.same(property_state, 'IL'):
        property_type = ctx['property_type']
        residential_unit_count = ctx['residential_unit_count']
        borrower_entity_type = ctx['borrower_entity_type']
        loan_amount = ctx['loan_amount']
        missing = rules_lib.gaps(
            property_type=property_type,
            residential_unit_count=residential_unit_count,
            borrower_entity_type=borrower_entity_type,
            loan_amount=loan_amount,
        )
        if missing:
            return rules_lib.unknown(*missing)
        residential = residential_units_in_range(property_type, residential_unit_count, 1, 4)
        if residential is None:
            return rules_lib.unknown('residential_unit_count')
        if not residential:
            return False
        entity_or_individual = (
            rules_lib.same(borrower_entity_type, 'entity')
            or rules_lib.same(borrower_entity_type, 'individual')
        )
        if not entity_or_individual:
            return False
        if loan_amount <= 250000:
            return True
        if rules_lib.same(borrower_entity_type, 'individual'):
            interest_rate = ctx['interest_rate']
            missing = rules_lib.gaps(interest_rate=interest_rate)
            if missing:
                return rules_lib.unknown(*missing)
            return loan_amount > 250000 and interest_rate > 8
        return False

    if rules_lib.same(property_state, 'KS') or rules_lib.same(property_state, 'MI') or rules_lib.same(property_state, 'MN') or rules_lib.same(property_state, 'NM'):
        property_type = ctx['property_type']
        residential_unit_count = ctx['residential_unit_count']
        missing = rules_lib.gaps(property_type=property_type, residential_unit_count=residential_unit_count)
        if missing:
            return rules_lib.unknown(*missing)
        result = residential_units_in_range(property_type, residential_unit_count, 1, 4)
        return rules_lib.unknown('residential_unit_count') if result is None else result

    if rules_lib.same(property_state, 'MD'):
        return True

    if rules_lib.same(property_state, 'MS'):
        property_type = ctx['property_type']
        residential_unit_count = ctx['residential_unit_count']
        missing = rules_lib.gaps(property_type=property_type, residential_unit_count=residential_unit_count)
        if missing:
            return rules_lib.unknown(*missing)
        result = residential_units_in_range(property_type, residential_unit_count, 1, 1)
        return rules_lib.unknown('residential_unit_count') if result is None else result

    if rules_lib.same(property_state, 'NJ'):
        borrower_entity_type = ctx['borrower_entity_type']
        missing = rules_lib.gaps(borrower_entity_type=borrower_entity_type)
        if missing:
            return rules_lib.unknown(*missing)
        return rules_lib.same(borrower_entity_type, 'individual')

    if rules_lib.same(property_state, 'OH') or rules_lib.same(property_state, 'PA'):
        property_type = ctx['property_type']
        residential_unit_count = ctx['residential_unit_count']
        missing = rules_lib.gaps(property_type=property_type, residential_unit_count=residential_unit_count)
        if missing:
            return rules_lib.unknown(*missing)
        residential = residential_units_in_range(property_type, residential_unit_count, 1, 2)
        if residential is None:
            return rules_lib.unknown('residential_unit_count')
        if not residential:
            return False
        if rules_lib.same(property_state, 'OH'):
            return True
        borrower_entity_type = ctx['borrower_entity_type']
        loan_amount = ctx['loan_amount']
        missing = rules_lib.gaps(borrower_entity_type=borrower_entity_type, loan_amount=loan_amount)
        if missing:
            return rules_lib.unknown(*missing)
        return rules_lib.same(borrower_entity_type, 'individual') and loan_amount < 319777

    if rules_lib.same(property_state, 'RI'):
        loan_purpose = ctx['loan_purpose']
        missing = rules_lib.gaps(loan_purpose=loan_purpose)
        if missing:
            return rules_lib.unknown(*missing)
        return rules_lib.same(loan_purpose, 'purchase')

    if rules_lib.same(property_state, 'VA'):
        property_type = ctx['property_type']
        residential_unit_count = ctx['residential_unit_count']
        borrower_entity_type = ctx['borrower_entity_type']
        missing = rules_lib.gaps(
            property_type=property_type,
            residential_unit_count=residential_unit_count,
            borrower_entity_type=borrower_entity_type,
        )
        if missing:
            return rules_lib.unknown(*missing)
        residential = residential_units_in_range(property_type, residential_unit_count, 1, 4)
        if residential is None:
            return rules_lib.unknown('residential_unit_count')
        return residential and rules_lib.same(borrower_entity_type, 'individual')

    if rules_lib.same(property_state, 'VT'):
        loan_amount = ctx['loan_amount']
        missing = rules_lib.gaps(loan_amount=loan_amount)
        if missing:
            return rules_lib.unknown(*missing)
        return loan_amount < 1000000

    return False
