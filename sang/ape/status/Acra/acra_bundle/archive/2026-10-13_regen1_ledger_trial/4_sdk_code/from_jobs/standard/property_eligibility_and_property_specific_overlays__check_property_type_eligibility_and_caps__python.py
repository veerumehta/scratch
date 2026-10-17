# rule: acra-standard.property_eligibility_and_property_specific_overlays.check_property_type_eligibility_and_caps.python
# origin: written from a job
# description: Python formalization of acra-standard.property_eligibility_and_property_specific_overlays.check_property_type_eligibility_and_caps
# reads: property_type, cltv_pct, loan_purpose, property_state
# implements job: acra-standard.property_eligibility_and_property_specific_overlays.check_property_type_eligibility_and_caps

import rules_lib

def check(ctx):
    property_type = ctx['property_type']
    missing = rules_lib.gaps(property_type=property_type)
    if missing:
        return rules_lib.unknown(*missing)

    kind = rules_lib.match(property_type, (
        'SFR', 'Townhome', 'PUD', 'Warrantable Condo',
        'Non-Warrantable Condo', 'Condotel / PUDtel',
        '2-4 Units', '2-4 Unit', 'Manufactured', 'Manufactured Home',
    ))
    if kind is None:
        return False

    if rules_lib.same(kind, 'SFR', 'Townhome', 'PUD', 'Warrantable Condo'):
        return True

    if rules_lib.same(kind, '2-4 Units', '2-4 Unit'):
        cltv_pct = ctx['cltv_pct']
        missing = rules_lib.gaps(cltv_pct=cltv_pct)
        if missing:
            return rules_lib.unknown(*missing)
        return cltv_pct <= 80

    cltv_pct = ctx['cltv_pct']
    loan_purpose = ctx['loan_purpose']
    needs_florida_check = rules_lib.same(
        kind, 'Non-Warrantable Condo', 'Condotel / PUDtel'
    )
    if needs_florida_check:
        property_state = ctx['property_state']
        missing = rules_lib.gaps(
            cltv_pct=cltv_pct,
            loan_purpose=loan_purpose,
            property_state=property_state,
        )
    else:
        missing = rules_lib.gaps(cltv_pct=cltv_pct, loan_purpose=loan_purpose)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(kind, 'Non-Warrantable Condo'):
        if rules_lib.same(loan_purpose, 'Purchase'):
            cap = 80
        elif rules_lib.same(loan_purpose, 'Refi R/T'):
            cap = 75
        elif rules_lib.same(loan_purpose, 'Refi C/O'):
            cap = 75
        else:
            return False
    elif rules_lib.same(kind, 'Condotel / PUDtel'):
        if rules_lib.same(loan_purpose, 'Purchase'):
            cap = 75
        elif rules_lib.same(loan_purpose, 'Refi R/T'):
            cap = 70
        elif rules_lib.same(loan_purpose, 'Refi C/O'):
            cap = 65
        else:
            return False
    elif rules_lib.same(kind, 'Manufactured', 'Manufactured Home'):
        if rules_lib.same(loan_purpose, 'Purchase'):
            cap = 65
        elif rules_lib.same(loan_purpose, 'Refi R/T'):
            cap = 60
        elif rules_lib.same(loan_purpose, 'Refi C/O'):
            cap = 60
        else:
            return False
    else:
        return False

    if needs_florida_check and rules_lib.same(property_state, 'Florida', 'FL'):
        cap -= 5
    return cltv_pct <= cap
