# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.30
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶9
# reads: rural_property, vacant_property, loan_purpose, cltv_pct, property_type, property_state, fico, gross_rental_income, pitia, loan_amount, reserves_months, escrow_waiver_requested, product_is_interest_only, prepayment_penalty_requested, ownership_months

import rules_lib


def check(ctx):
    rural_raw = ctx['rural_property']
    vacant_raw = ctx['vacant_property']
    rural = rules_lib.flag(rural_raw)
    vacant = rules_lib.flag(vacant_raw)
    missing = rules_lib.gaps(rural=rural, vacant=vacant)
    if missing:
        return rules_lib.unknown(*missing)

    purpose = ctx['loan_purpose']
    cltv = ctx['cltv_pct']
    missing = rules_lib.gaps(purpose=purpose, cltv=cltv)
    if missing:
        return rules_lib.unknown(*missing)

    purchase = rules_lib.same(purpose, 'purchase')
    rate_term = rules_lib.same(purpose, 'rate and term refinance')
    cash_out = rules_lib.same(purpose, 'cash-out refinance')

    if cltv > 80.00:
        property_type = ctx['property_type']
        missing = rules_lib.gaps(property_type=property_type)
        if missing:
            return rules_lib.unknown(*missing)
        if rules_lib.same(property_type, 'condo'):
            return rules_lib.unknown('warrantable_condo_status')
        if rules_lib.same(property_type, 'warrantable condo'):
            property_state = ctx['property_state']
            missing = rules_lib.gaps(property_state=property_state)
            if missing:
                return rules_lib.unknown(*missing)
            if rules_lib.same(property_state, 'Florida'):
                return False
        elif not any(rules_lib.same(property_type, item) for item in ('SFR', 'townhome', 'PUD')):
            return False

    if rural:
        if purchase:
            rural_max_cltv = 80
        elif rate_term:
            rural_max_cltv = 75
        elif cash_out:
            rural_max_cltv = 70
        else:
            return rules_lib.unknown('loan_purpose')
        if cltv > rural_max_cltv:
            return False

        fico = ctx['fico']
        gross_rental_income = ctx['gross_rental_income']
        pitia = ctx['pitia']
        missing = rules_lib.gaps(fico=fico, gross_rental_income=gross_rental_income, pitia=pitia)
        if missing:
            return rules_lib.unknown(*missing)
        dscr = rules_lib.ratio(gross_rental_income, pitia)
        if fico < 700 or dscr < 1.00:
            return False

    if not vacant:
        return True

    if purchase:
        return True
    if not (rate_term or cash_out):
        return False

    fico = ctx['fico']
    loan_amount = ctx['loan_amount']
    reserves_months = ctx['reserves_months']
    escrow_waiver_requested = rules_lib.flag(ctx['escrow_waiver_requested'])
    product_is_interest_only = rules_lib.flag(ctx['product_is_interest_only'])
    prepayment_penalty_requested = rules_lib.flag(ctx['prepayment_penalty_requested'])
    missing = rules_lib.gaps(
        fico=fico,
        loan_amount=loan_amount,
        reserves_months=reserves_months,
        escrow_waiver_requested=escrow_waiver_requested,
        product_is_interest_only=product_is_interest_only,
        prepayment_penalty_requested=prepayment_penalty_requested,
    )
    if missing:
        return rules_lib.unknown(*missing)
    if fico < 700 or reserves_months < 6 or escrow_waiver_requested or product_is_interest_only:
        return False

    if rate_term:
        if loan_amount > 2000000:
            return False
        if loan_amount == 1000000 or loan_amount == 2000000:
            return rules_lib.unknown('loan_amount_threshold_confirmation')
        max_cltv = 70 if loan_amount < 1000000 else 65
        if cltv > max_cltv:
            return False

        gross_rental_income = ctx['gross_rental_income']
        pitia = ctx['pitia']
        missing = rules_lib.gaps(gross_rental_income=gross_rental_income, pitia=pitia)
        if missing:
            return rules_lib.unknown(*missing)
        dscr = rules_lib.ratio(gross_rental_income, pitia)
        if dscr is not None and dscr >= 1.000:
            pass
        else:
            return rules_lib.unknown('DTI (40.0% maximum)')

        if prepayment_penalty_requested is False:
            return rules_lib.unknown('prepayment_penalty_allowability')
        return rules_lib.unknown('prepayment_penalty_term', 'prepayment_penalty_allowability')

    if loan_amount >= 1500000:
        return rules_lib.unknown('cash_out_CLTV_at_or_above_1500000_confirmation')
    if cltv > 60:
        return False

    ownership_months = ctx['ownership_months']
    missing = rules_lib.gaps(ownership_months=ownership_months)
    if missing:
        return rules_lib.unknown(*missing)
    if ownership_months < 15:
        return False
    if ownership_months == 15:
        return rules_lib.unknown('15_month_ownership_measurement_confirmation')

    gross_rental_income = ctx['gross_rental_income']
    pitia = ctx['pitia']
    missing = rules_lib.gaps(gross_rental_income=gross_rental_income, pitia=pitia)
    if missing:
        return rules_lib.unknown(*missing)
    dscr = rules_lib.ratio(gross_rental_income, pitia)
    if dscr is None:
        return rules_lib.unknown('gross_rental_income', 'pitia')
    if dscr < 1.15:
        return False
    if prepayment_penalty_requested is False:
        return rules_lib.unknown('prepayment_penalty_allowability')
    return rules_lib.unknown('prepayment_penalty_term', 'prepayment_penalty_allowability')
