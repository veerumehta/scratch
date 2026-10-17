# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.29
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶8
# reads: bankruptcy_or_foreclosure, short_sale_dil_or_modification, escrow_waiver_requested, property_type, loan_purpose, months_since_bankruptcy_or_foreclosure, months_since_short_sale_dil_or_modification, property_state, gross_rental_income, pitia, loan_amount, fico, mortgage_history_0x30x24, citizenship_type, cltv_pct

import rules_lib


def check(ctx):
    bankruptcy_or_foreclosure = ctx['bankruptcy_or_foreclosure']
    short_sale_dil_or_modification = ctx['short_sale_dil_or_modification']
    escrow_waiver_requested = ctx['escrow_waiver_requested']
    property_type = ctx['property_type']
    loan_purpose = ctx['loan_purpose']

    missing = rules_lib.gaps(
        bankruptcy_or_foreclosure=bankruptcy_or_foreclosure,
        short_sale_dil_or_modification=short_sale_dil_or_modification,
        escrow_waiver_requested=escrow_waiver_requested,
        property_type=property_type,
    )
    if missing:
        return rules_lib.unknown(*missing)

    bankruptcy = rules_lib.flag(bankruptcy_or_foreclosure)
    short_sale = rules_lib.flag(short_sale_dil_or_modification)
    escrow_requested = rules_lib.flag(escrow_waiver_requested)
    if bankruptcy is None:
        return rules_lib.unknown('bankruptcy_or_foreclosure')
    if short_sale is None:
        return rules_lib.unknown('short_sale_dil_or_modification')
    if escrow_requested is None:
        return rules_lib.unknown('escrow_waiver_requested')

    caps = []

    if bankruptcy:
        months_since_bankruptcy_or_foreclosure = ctx['months_since_bankruptcy_or_foreclosure']
        missing = rules_lib.gaps(months_since_bankruptcy_or_foreclosure=months_since_bankruptcy_or_foreclosure)
        if missing:
            return rules_lib.unknown(*missing)
        if months_since_bankruptcy_or_foreclosure < 12:
            return False
        if months_since_bankruptcy_or_foreclosure < 24:
            if rules_lib.same(loan_purpose, 'purchase'):
                caps.append(65)
            elif rules_lib.same(loan_purpose, 'refi r/t', 'refi c/o'):
                caps.append(65)
            else:
                return rules_lib.unknown('loan_purpose')
        elif months_since_bankruptcy_or_foreclosure < 36:
            if rules_lib.same(loan_purpose, 'purchase'):
                caps.append(80)
            elif rules_lib.same(loan_purpose, 'refi r/t', 'refi c/o'):
                caps.append(75)
            else:
                return rules_lib.unknown('loan_purpose')

    if short_sale:
        months_since_short_sale_dil_or_modification = ctx['months_since_short_sale_dil_or_modification']
        missing = rules_lib.gaps(months_since_short_sale_dil_or_modification=months_since_short_sale_dil_or_modification)
        if missing:
            return rules_lib.unknown(*missing)
        if months_since_short_sale_dil_or_modification < 12:
            if rules_lib.same(loan_purpose, 'purchase'):
                caps.append(75)
            elif rules_lib.same(loan_purpose, 'refi r/t', 'refi c/o'):
                caps.append(70)
            else:
                return rules_lib.unknown('loan_purpose')
        elif months_since_short_sale_dil_or_modification < 24:
            if rules_lib.same(loan_purpose, 'purchase'):
                caps.append(80)
            elif rules_lib.same(loan_purpose, 'refi r/t', 'refi c/o'):
                caps.append(75)
            else:
                return rules_lib.unknown('loan_purpose')

    if rules_lib.same(property_type, 'non-warrantable condo'):
        if rules_lib.same(loan_purpose, 'purchase'):
            property_cap = 80
        elif rules_lib.same(loan_purpose, 'refi r/t'):
            property_cap = 75
        elif rules_lib.same(loan_purpose, 'refi c/o'):
            property_cap = 75
        else:
            return rules_lib.unknown('loan_purpose')
        property_state = ctx['property_state']
        gross_rental_income = ctx['gross_rental_income']
        pitia = ctx['pitia']
        missing = rules_lib.gaps(
            property_state=property_state,
            gross_rental_income=gross_rental_income,
            pitia=pitia,
        )
        if missing:
            return rules_lib.unknown(*missing)
        dscr = rules_lib.ratio(gross_rental_income, pitia)
        if dscr is None:
            return rules_lib.unknown('gross_rental_income', 'pitia')
        if dscr < 1.0:
            return False
        if rules_lib.same(property_state, 'florida'):
            property_cap -= 5
        caps.append(property_cap)
    elif rules_lib.same(property_type, 'condotel / pudtel'):
        if rules_lib.same(loan_purpose, 'purchase'):
            property_cap = 75
        elif rules_lib.same(loan_purpose, 'refi r/t'):
            property_cap = 70
        elif rules_lib.same(loan_purpose, 'refi c/o'):
            property_cap = 65
        else:
            return rules_lib.unknown('loan_purpose')
        property_state = ctx['property_state']
        gross_rental_income = ctx['gross_rental_income']
        pitia = ctx['pitia']
        missing = rules_lib.gaps(
            property_state=property_state,
            gross_rental_income=gross_rental_income,
            pitia=pitia,
        )
        if missing:
            return rules_lib.unknown(*missing)
        dscr = rules_lib.ratio(gross_rental_income, pitia)
        if dscr is None:
            return rules_lib.unknown('gross_rental_income', 'pitia')
        if dscr < 1.0:
            return False
        if rules_lib.same(property_state, 'florida'):
            property_cap -= 5
        caps.append(property_cap)
    elif rules_lib.same(property_type, '2-4 unit', '2-4 units'):
        caps.append(80)
    elif rules_lib.same(property_type, 'manufactured', 'manufactured home'):
        if rules_lib.same(loan_purpose, 'purchase'):
            caps.append(65)
        elif rules_lib.same(loan_purpose, 'refi r/t', 'refi c/o'):
            caps.append(60)
        else:
            return rules_lib.unknown('loan_purpose')
    elif not rules_lib.same(
        property_type,
        'sfr', 'townhome', 'pud', 'warrantable condo',
    ):
        return False

    if escrow_requested:
        loan_amount = ctx['loan_amount']
        fico = ctx['fico']
        mortgage_history_0x30x24 = ctx['mortgage_history_0x30x24']
        citizenship_type = ctx['citizenship_type']
        missing = rules_lib.gaps(
            loan_amount=loan_amount,
            fico=fico,
            mortgage_history_0x30x24=mortgage_history_0x30x24,
            citizenship_type=citizenship_type,
        )
        if missing:
            return rules_lib.unknown(*missing)
        if loan_amount > 1500000 or fico < 700:
            return False
        mortgage_history_ok = rules_lib.flag(mortgage_history_0x30x24)
        if mortgage_history_ok is None:
            return rules_lib.unknown('mortgage_history_0x30x24')
        if not mortgage_history_ok or rules_lib.same(citizenship_type, 'foreign national'):
            return False
        caps.append(80)

    if caps:
        cltv_pct = ctx['cltv_pct']
        missing = rules_lib.gaps(cltv_pct=cltv_pct)
        if missing:
            return rules_lib.unknown(*missing)
        if cltv_pct > min(caps):
            return False

    return True
