# rule: acra-standard.program_scope_occupancy_and_transaction_setup.check_published_program_scope.python
# origin: written from a job
# description: Python formalization of acra-standard.program_scope_occupancy_and_transaction_setup.check_published_program_scope
# reads: loan_amount, fico, property_type, property_state, citizenship_type, delayed_financing, loan_purpose, cltv_pct
# implements job: acra-standard.program_scope_occupancy_and_transaction_setup.check_published_program_scope

def check(ctx):
    loan_amount = ctx['loan_amount']
    fico = ctx['fico']
    property_type = ctx['property_type']
    property_state = ctx['property_state']
    citizenship_type = ctx['citizenship_type']
    delayed_financing = ctx['delayed_financing']

    missing = rules_lib.gaps(
        loan_amount=loan_amount,
        fico=fico,
        property_type=property_type,
        property_state=property_state,
        citizenship_type=citizenship_type,
        delayed_financing=delayed_financing,
    )
    if missing:
        return rules_lib.unknown(*missing)

    delayed = rules_lib.flag(delayed_financing)
    if delayed is None:
        return rules_lib.unknown('delayed_financing')

    meets = (
        100000 <= loan_amount <= 3000000
        and (loan_amount - 100000) % 50 == 0
        and not rules_lib.same(property_state, 'SD')
        and any(rules_lib.same(property_type, option) for option in (
            'SFR', 'Townhome', 'PUD', 'Warrantable Condo',
            'Non-Warrantable Condo', 'Condotel / PUDtel', '2-4 Units',
            'Manufactured',
        ))
        and any(rules_lib.same(citizenship_type, option) for option in (
            'US Citizen', 'Permanent Resident', 'Non-Permanent Resident',
            'Foreign National', 'ITIN',
        ))
        and (not delayed or loan_amount <= 1500000)
    )

    if loan_amount <= 1500000:
        meets = meets and fico >= 600
    elif loan_amount <= 2000000:
        meets = meets and fico >= 620
    elif loan_amount <= 3000000:
        meets = meets and fico >= 700

    if loan_amount <= 1500000 and fico >= 720:
        loan_purpose = ctx['loan_purpose']
        cltv_pct = ctx['cltv_pct']
        missing = rules_lib.gaps(loan_purpose=loan_purpose, cltv_pct=cltv_pct)
        if missing:
            return rules_lib.unknown(*missing)

        if rules_lib.same(loan_purpose, 'purchase'):
            cltv_limit = 85
        elif rules_lib.same(loan_purpose, 'rate & term') or rules_lib.same(loan_purpose, 'cash-out'):
            cltv_limit = 80
        else:
            return rules_lib.unknown('loan_purpose')
        meets = meets and cltv_pct <= cltv_limit

    return bool(meets)
