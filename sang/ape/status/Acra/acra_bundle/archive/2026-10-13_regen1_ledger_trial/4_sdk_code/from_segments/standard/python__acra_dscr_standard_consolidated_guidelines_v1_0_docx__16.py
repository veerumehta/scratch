# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.16
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶17
# reads: loan_amount, credit_score_count, tradelines_meet_requirement, rural_property, property_type, first_time_homebuyer, vacant_property, loan_purpose, listed_for_sale_last_6_months, mixed_use, dscr_documentation_type, gross_rental_income, pitia

import rules_lib

def check(ctx):
    loan_amount = ctx['loan_amount']
    credit_score_count = ctx['credit_score_count']
    tradelines_meet_requirement = ctx['tradelines_meet_requirement']
    rural_property = ctx['rural_property']
    property_type = ctx['property_type']
    first_time_homebuyer = ctx['first_time_homebuyer']
    vacant_property = ctx['vacant_property']
    loan_purpose = ctx['loan_purpose']
    listed_for_sale_last_6_months = ctx['listed_for_sale_last_6_months']
    mixed_use = ctx['mixed_use']
    dscr_documentation_type = ctx['dscr_documentation_type']
    gross_rental_income = ctx['gross_rental_income']
    pitia = ctx['pitia']

    missing = rules_lib.gaps(
        loan_amount=loan_amount,
        credit_score_count=credit_score_count,
        tradelines_meet_requirement=tradelines_meet_requirement,
        rural_property=rural_property,
        property_type=property_type,
        first_time_homebuyer=first_time_homebuyer,
        vacant_property=vacant_property,
        loan_purpose=loan_purpose,
        listed_for_sale_last_6_months=listed_for_sale_last_6_months,
        mixed_use=mixed_use,
        dscr_documentation_type=dscr_documentation_type,
        gross_rental_income=gross_rental_income,
        pitia=pitia,
    )
    if missing:
        return rules_lib.unknown(*missing)

    rural = rules_lib.flag(rural_property)
    fthb = rules_lib.flag(first_time_homebuyer)
    vacant = rules_lib.flag(vacant_property)
    listed = rules_lib.flag(listed_for_sale_last_6_months)
    mixed = rules_lib.flag(mixed_use)
    tradelines_ok = rules_lib.flag(tradelines_meet_requirement)
    if None in (rural, fthb, vacant, listed, mixed, tradelines_ok):
        return rules_lib.unknown('a required eligibility flag')

    triggers = []
    if loan_amount > 2_000_000:
        triggers.append(1.0)
    if credit_score_count <= 1 or not tradelines_ok:
        triggers.append(1.1)
    if rural or rules_lib.same(property_type, 'unique property'):
        triggers.append(1.00)
    if rules_lib.same(property_type, 'non-warrantable condo', 'condotel', 'PUDtel'):
        triggers.append(1.0)
    if fthb:
        triggers.append(1.150)
    if vacant and rules_lib.same(loan_purpose, 'rate and term refinance'):
        triggers.append(1.000)
    if vacant and rules_lib.same(loan_purpose, 'cash-out refinance'):
        triggers.append(1.15)
    if listed:
        triggers.append(1.0)
    if mixed or rules_lib.same(property_type, 'adult care', 'assisted living'):
        triggers.append(1.2)

    if not triggers:
        return rules_lib.unknown('whether LTV is above 80.00%')

    if rules_lib.same(dscr_documentation_type, 'No Ratio'):
        return rules_lib.unknown('whether No Ratio is available when another condition carries a minimum DSCR (Q-13)')

    dscr = rules_lib.ratio(gross_rental_income, pitia)
    if dscr is None:
        return rules_lib.unknown('gross_rental_income', 'pitia')
    return dscr >= max(triggers)
