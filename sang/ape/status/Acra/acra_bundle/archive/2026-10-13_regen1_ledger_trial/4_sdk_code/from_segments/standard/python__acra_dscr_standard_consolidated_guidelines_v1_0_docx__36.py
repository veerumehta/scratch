# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.36
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶15
# reads: prepayment_penalty_requested, property_state, property_type, residential_unit_count, borrower_entity_type, loan_amount, interest_rate, loan_purpose

import rules_lib


def check(ctx):
    requested = ctx['prepayment_penalty_requested']
    requested = rules_lib.flag(requested)
    if requested is None:
        return rules_lib.unknown('prepayment_penalty_requested')
    if not requested:
        return True

    state = ctx['property_state']
    missing = rules_lib.gaps(state=state)
    if missing:
        return rules_lib.unknown(*missing)

    def residential(low, high):
        property_type = ctx['property_type']
        unit_count = ctx['residential_unit_count']
        missing_fields = rules_lib.gaps(
            property_type=property_type,
            residential_unit_count=unit_count,
        )
        if missing_fields:
            return None, missing_fields
        if not rules_lib.same(property_type, 'residential'):
            return False, []
        return low <= unit_count <= high, []

    restriction = False

    if rules_lib.same(state, 'Alaska', 'Kansas', 'Michigan', 'Minnesota', 'New Mexico'):
        restriction, missing = residential(1, 4)
        if missing:
            return rules_lib.unknown(*missing)

    elif rules_lib.same(state, 'Maryland'):
        restriction = True

    elif rules_lib.same(state, 'Mississippi'):
        restriction, missing = residential(1, 1)
        if missing:
            return rules_lib.unknown(*missing)

    elif rules_lib.same(state, 'New Jersey', 'Virginia'):
        borrower_entity_type = ctx['borrower_entity_type']
        missing = rules_lib.gaps(borrower_entity_type=borrower_entity_type)
        if missing:
            return rules_lib.unknown(*missing)
        individual = rules_lib.same(borrower_entity_type, 'individual')
        if rules_lib.same(state, 'New Jersey'):
            restriction = individual
        else:
            residential_match, missing = residential(1, 4)
            if missing:
                return rules_lib.unknown(*missing)
            restriction = individual and residential_match

    elif rules_lib.same(state, 'Ohio'):
        restriction, missing = residential(1, 2)
        if missing:
            return rules_lib.unknown(*missing)

    elif rules_lib.same(state, 'Rhode Island'):
        loan_purpose = ctx['loan_purpose']
        missing = rules_lib.gaps(loan_purpose=loan_purpose)
        if missing:
            return rules_lib.unknown(*missing)
        restriction = rules_lib.same(loan_purpose, 'purchase')

    elif rules_lib.same(state, 'Vermont'):
        loan_amount = ctx['loan_amount']
        missing = rules_lib.gaps(loan_amount=loan_amount)
        if missing:
            return rules_lib.unknown(*missing)
        restriction = loan_amount < 1000000

    elif rules_lib.same(state, 'Pennsylvania'):
        borrower_entity_type = ctx['borrower_entity_type']
        missing = rules_lib.gaps(borrower_entity_type=borrower_entity_type)
        if missing:
            return rules_lib.unknown(*missing)
        residential_match, missing = residential(1, 2)
        if missing:
            return rules_lib.unknown(*missing)
        if rules_lib.same(borrower_entity_type, 'individual') and residential_match:
            loan_amount = ctx['loan_amount']
            missing = rules_lib.gaps(loan_amount=loan_amount)
            if missing:
                return rules_lib.unknown(*missing)
            restriction = loan_amount < 319777

    elif rules_lib.same(state, 'Illinois'):
        residential_match, missing = residential(1, 4)
        if missing:
            return rules_lib.unknown(*missing)
        if residential_match:
            borrower_entity_type = ctx['borrower_entity_type']
            loan_amount = ctx['loan_amount']
            missing = rules_lib.gaps(
                borrower_entity_type=borrower_entity_type,
                loan_amount=loan_amount,
            )
            if missing:
                return rules_lib.unknown(*missing)
            entity_or_individual = rules_lib.same(
                borrower_entity_type, 'entity', 'individual'
            )
            if loan_amount <= 250000:
                restriction = entity_or_individual
            elif rules_lib.same(borrower_entity_type, 'individual'):
                interest_rate = ctx['interest_rate']
                missing = rules_lib.gaps(interest_rate=interest_rate)
                if missing:
                    return rules_lib.unknown(*missing)
                restriction = interest_rate > 8

    return not restriction
