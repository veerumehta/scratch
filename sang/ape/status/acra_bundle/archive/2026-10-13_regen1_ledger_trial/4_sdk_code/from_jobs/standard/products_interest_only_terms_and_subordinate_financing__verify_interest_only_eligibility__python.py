# rule: acra-standard.products_interest_only_terms_and_subordinate_financing.verify_interest_only_eligibility.python
# origin: written from a job
# description: Python formalization of acra-standard.products_interest_only_terms_and_subordinate_financing.verify_interest_only_eligibility
# reads: product_is_interest_only, interest_only_10_40, loan_amount, fico, first_time_homebuyer, vacant_property, property_currently_listed_for_sale, loan_purpose, cltv_pct
# implements job: acra-standard.products_interest_only_terms_and_subordinate_financing.verify_interest_only_eligibility

import rules_lib

def check(ctx):
    product_raw = ctx['product_is_interest_only']
    missing = rules_lib.gaps(product_is_interest_only=product_raw)
    if missing:
        return rules_lib.unknown(*missing)
    product = rules_lib.flag(product_raw)
    if product is None:
        return rules_lib.unknown('product_is_interest_only')
    if not product:
        return True

    term_raw = ctx['interest_only_10_40']
    amount = ctx['loan_amount']
    fico = ctx['fico']
    first_time_raw = ctx['first_time_homebuyer']
    vacant_raw = ctx['vacant_property']
    listed_raw = ctx['property_currently_listed_for_sale']
    missing = rules_lib.gaps(
        interest_only_10_40=term_raw,
        loan_amount=amount,
        fico=fico,
        first_time_homebuyer=first_time_raw,
        vacant_property=vacant_raw,
        property_currently_listed_for_sale=listed_raw,
    )
    if missing:
        return rules_lib.unknown(*missing)

    term_10_40 = rules_lib.flag(term_raw)
    first_time = rules_lib.flag(first_time_raw)
    vacant = rules_lib.flag(vacant_raw)
    listed = rules_lib.flag(listed_raw)
    if term_10_40 is None:
        return rules_lib.unknown('interest_only_10_40')
    if first_time is None:
        return rules_lib.unknown('first_time_homebuyer')
    if vacant is None:
        return rules_lib.unknown('vacant_property')
    if listed is None:
        return rules_lib.unknown('property_currently_listed_for_sale')

    if amount < 250000 or fico < 640 or first_time or listed:
        return False

    if vacant:
        loan_purpose = ctx['loan_purpose']
        missing = rules_lib.gaps(loan_purpose=loan_purpose)
        if missing:
            return rules_lib.unknown(*missing)
        if rules_lib.same(
            loan_purpose,
            'refinance',
            'rate/term refinance',
            'cash-out refinance',
        ):
            return False

    if term_10_40:
        cltv_pct = ctx['cltv_pct']
        missing = rules_lib.gaps(cltv_pct=cltv_pct)
        if missing:
            return rules_lib.unknown(*missing)
        if cltv_pct > 80 or amount > 3000000:
            return False

    return True
