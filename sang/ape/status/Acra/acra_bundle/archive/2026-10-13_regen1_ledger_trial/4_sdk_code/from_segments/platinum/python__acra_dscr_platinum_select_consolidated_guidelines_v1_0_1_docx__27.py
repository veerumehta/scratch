# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.27
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶13
# reads: product_is_interest_only, cltv_pct, property_currently_listed_for_sale

import rules_lib


def check(ctx):
    product_raw = ctx['product_is_interest_only']
    missing = rules_lib.gaps(product_is_interest_only=product_raw)
    if missing:
        return rules_lib.unknown(*missing)

    product_is_interest_only = rules_lib.flag(product_raw)
    if product_is_interest_only is None:
        return rules_lib.unknown('product_is_interest_only')
    if not product_is_interest_only:
        return True

    cltv_pct = ctx['cltv_pct']
    listed_raw = ctx['property_currently_listed_for_sale']
    missing = rules_lib.gaps(
        cltv_pct=cltv_pct,
        property_currently_listed_for_sale=listed_raw,
    )
    if missing:
        return rules_lib.unknown(*missing)

    listed = rules_lib.flag(listed_raw)
    if listed is None:
        return rules_lib.unknown('property_currently_listed_for_sale')

    cltv_ok = rules_lib.band(cltv_pct, [(75.00, True)], above=False)
    if cltv_ok is None:
        return rules_lib.unknown('cltv_pct')

    return cltv_ok and not listed
