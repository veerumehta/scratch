# rule: acra-platinum.compliance_and_closing.prepayment_penalty_requirements.python
# origin: written from a job
# description: Python formalization of acra-platinum.compliance_and_closing.prepayment_penalty_requirements
# reads: SubjectProperty.listed_for_sale_last_6_months, LoanCore.prepayment_penalty_structure, SubjectProperty.state, SubjectProperty.property_type, SubjectProperty.number_of_units
# implements job: acra-platinum.compliance_and_closing.prepayment_penalty_requirements

import rules_lib

def check(ctx):
    listed_raw = ctx['SubjectProperty.listed_for_sale_last_6_months']
    structure = ctx['LoanCore.prepayment_penalty_structure']
    state = ctx['SubjectProperty.state']
    missing = rules_lib.gaps(listed_for_sale_last_6_months=listed_raw, prepayment_penalty_structure=structure, state=state)
    if missing:
        return rules_lib.unknown(*missing)

    listed = rules_lib.flag(listed_raw)
    if listed is None:
        return rules_lib.unknown('listed_for_sale_last_6_months')

    five_fixed = rules_lib.same(structure, '5 Year 5% Fixed') or rules_lib.same(structure, '5% Fixed (5% / 5% / 5% / 5% / 5%)')
    stepdown = rules_lib.same(structure, 'Sequential Stepdown') or rules_lib.same(structure, 'Sequential Stepdown (5% / 4% / 3% / 2% / 1%)')
    three_five = rules_lib.same(structure, '3 Year 5% Fixed') or rules_lib.same(structure, '5% Fixed (5% / 5% / 5%)')
    three_fixed = rules_lib.same(structure, '3% Fixed (3% / 3% / 3%)')
    two_fixed = rules_lib.same(structure, '2 Year 3% Fixed') or rules_lib.same(structure, '3% Fixed (3% / 3%)')
    one_fixed = rules_lib.same(structure, '1 Year 3% Fixed') or rules_lib.same(structure, '3% Fixed (3%)')
    no_prepay = rules_lib.same(structure, 'No Prepay')

    if not (five_fixed or stepdown or three_five or three_fixed or two_fixed or one_fixed or no_prepay):
        return False
    if listed and (two_fixed or one_fixed or no_prepay):
        return False

    if rules_lib.same(state, 'MS'):
        property_type = ctx['SubjectProperty.property_type']
        units = ctx['SubjectProperty.number_of_units']
        missing = rules_lib.gaps(property_type=property_type, number_of_units=units)
        if missing:
            return rules_lib.unknown(*missing)
        if rules_lib.same(property_type, 'Residential') and (units == 1 or rules_lib.same(units, '1')):
            return stepdown

    return True
