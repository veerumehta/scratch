# rule: acra-standard.property_eligibility_and_property_specific_overlays.apply_rural_or_unique_property_overlay.python
# origin: written from a job
# description: Python formalization of acra-standard.property_eligibility_and_property_specific_overlays.apply_rural_or_unique_property_overlay
# reads: rural_property, loan_purpose, cltv_pct, fico
# implements job: acra-standard.property_eligibility_and_property_specific_overlays.apply_rural_or_unique_property_overlay

import rules_lib

def check(ctx):
    rural_property = ctx['rural_property']
    rural_property = rules_lib.flag(rural_property)
    missing = rules_lib.gaps(rural_property=rural_property)
    if missing:
        return rules_lib.unknown(*missing)
    if rural_property is False:
        return True

    loan_purpose = ctx['loan_purpose']
    cltv_pct = ctx['cltv_pct']
    fico = ctx['fico']
    missing = rules_lib.gaps(loan_purpose=loan_purpose, cltv_pct=cltv_pct, fico=fico)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(loan_purpose, 'purchase'):
        max_cltv = 80
    elif rules_lib.same(loan_purpose, 'refinance rate & term', 'refinance rate and term', 'refi r/t'):
        max_cltv = 75
    elif rules_lib.same(loan_purpose, 'refinance cash-out', 'refinance cash out', 'refi cash-out'):
        max_cltv = 70
    else:
        return rules_lib.unknown('loan_purpose')

    return cltv_pct <= max_cltv and fico >= 700
