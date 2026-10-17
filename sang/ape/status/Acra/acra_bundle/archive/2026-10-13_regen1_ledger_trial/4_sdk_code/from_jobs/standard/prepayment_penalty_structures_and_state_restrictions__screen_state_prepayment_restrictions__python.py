# rule: acra-standard.prepayment_penalty_structures_and_state_restrictions.screen_state_prepayment_restrictions.python
# origin: written from a job
# description: Python formalization of acra-standard.prepayment_penalty_structures_and_state_restrictions.screen_state_prepayment_restrictions
# reads: property_state, residential_unit_count, borrower_entity_type, loan_amount, interest_rate, loan_purpose
# implements job: acra-standard.prepayment_penalty_structures_and_state_restrictions.screen_state_prepayment_restrictions

import rules_lib


def check(ctx):
    property_state = ctx['property_state']
    residential_unit_count = ctx['residential_unit_count']
    borrower_entity_type = ctx['borrower_entity_type']
    loan_amount = ctx['loan_amount']
    interest_rate = ctx['interest_rate']
    loan_purpose = ctx['loan_purpose']

    missing = rules_lib.gaps(
        property_state=property_state,
        residential_unit_count=residential_unit_count,
        borrower_entity_type=borrower_entity_type,
        loan_amount=loan_amount,
        interest_rate=interest_rate,
        loan_purpose=loan_purpose,
    )
    if missing:
        return rules_lib.unknown(*missing)

    state = rules_lib.norm(property_state)
    individual = rules_lib.same(borrower_entity_type, 'individual')
    entity_or_individual = (
        individual or rules_lib.same(borrower_entity_type, 'entity')
    )
    unit_count = residential_unit_count
    applicable = []

    if rules_lib.same(state, 'Alaska') and 1 <= unit_count <= 4:
        applicable.append('Alaska')
    if (
        rules_lib.same(state, 'Illinois')
        and 1 <= unit_count <= 4
        and entity_or_individual
        and loan_amount <= 250000
    ):
        applicable.append('Illinois clause 1')
    if (
        rules_lib.same(state, 'Illinois')
        and 1 <= unit_count <= 4
        and individual
        and loan_amount > 250000
        and interest_rate > 8
    ):
        applicable.append('Illinois clause 2')
    if rules_lib.same(state, 'Kansas') and 1 <= unit_count <= 4:
        applicable.append('Kansas')
    if rules_lib.same(state, 'Maryland'):
        applicable.append('Maryland')
    if rules_lib.same(state, 'Michigan') and 1 <= unit_count <= 4:
        applicable.append('Michigan')
    if rules_lib.same(state, 'Minnesota') and 1 <= unit_count <= 4:
        applicable.append('Minnesota')
    if rules_lib.same(state, 'Mississippi') and unit_count == 1:
        applicable.append('Mississippi')
    if rules_lib.same(state, 'New Jersey') and individual:
        applicable.append('New Jersey')
    if rules_lib.same(state, 'New Mexico') and 1 <= unit_count <= 4:
        applicable.append('New Mexico')
    if rules_lib.same(state, 'Ohio') and 1 <= unit_count <= 2:
        applicable.append('Ohio')
    if (
        rules_lib.same(state, 'Pennsylvania')
        and 1 <= unit_count <= 2
        and individual
        and loan_amount < 319777
    ):
        applicable.append('Pennsylvania')
    if (
        rules_lib.same(state, 'Rhode Island')
        and rules_lib.same(loan_purpose, 'purchase')
    ):
        applicable.append('Rhode Island')
    if rules_lib.same(state, 'Virginia') and 1 <= unit_count <= 4 and individual:
        applicable.append('Virginia')
    if rules_lib.same(state, 'Vermont') and loan_amount < 1000000:
        applicable.append('Vermont')

    buy_out_confirmation_review = [
        name for name in applicable if name != 'Mississippi'
    ]
    return bool(applicable), {
        'applicable_restrictions': applicable,
        'acra_confirmation_review': buy_out_confirmation_review,
        'mississippi_structure_review': 'Mississippi' in applicable,
    }
