# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.34
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶13
# reads: product_is_interest_only, interest_only_10_40, loan_amount, fico, first_time_homebuyer, vacant_property, property_currently_listed_for_sale, loan_purpose, cltv_pct

import rules_lib


def check(ctx):
    product_is_interest_only = ctx['product_is_interest_only']
    io = rules_lib.flag(product_is_interest_only)
    missing = rules_lib.gaps(product_is_interest_only=io)
    if missing:
        return rules_lib.unknown(*missing)
    if not io:
        return True

    interest_only_10_40 = ctx['interest_only_10_40']
    loan_amount = ctx['loan_amount']
    fico = ctx['fico']
    first_time_homebuyer = rules_lib.flag(ctx['first_time_homebuyer'])
    vacant_property = rules_lib.flag(ctx['vacant_property'])
    property_currently_listed_for_sale = rules_lib.flag(ctx['property_currently_listed_for_sale'])

    missing = rules_lib.gaps(
        interest_only_10_40=interest_only_10_40,
        loan_amount=loan_amount,
        fico=fico,
        first_time_homebuyer=first_time_homebuyer,
        vacant_property=vacant_property,
        property_currently_listed_for_sale=property_currently_listed_for_sale,
    )
    if missing:
        return rules_lib.unknown(*missing)

    loan_purpose = None
    if vacant_property:
        loan_purpose = ctx['loan_purpose']
        missing = rules_lib.gaps(loan_purpose=loan_purpose)
        if missing:
            return rules_lib.unknown(*missing)

    if loan_amount < 250000 or fico < 640:
        return False
    if first_time_homebuyer or property_currently_listed_for_sale:
        return False
    if vacant_property and rules_lib.same(
        loan_purpose, 'refinance', 'cash-out refinance', 'rate/term refinance'
    ):
        return False

    if rules_lib.flag(interest_only_10_40) is None:
        return rules_lib.unknown('interest_only_10_40')
    if rules_lib.flag(interest_only_10_40):
        cltv_pct = ctx['cltv_pct']
        missing = rules_lib.gaps(cltv_pct=cltv_pct)
        if missing:
            return rules_lib.unknown(*missing)
        if cltv_pct > 80 or loan_amount > 3000000:
            return False

    return True
