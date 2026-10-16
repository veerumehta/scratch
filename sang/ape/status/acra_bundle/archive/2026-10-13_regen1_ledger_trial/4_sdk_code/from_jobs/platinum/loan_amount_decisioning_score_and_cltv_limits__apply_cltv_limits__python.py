# rule: acra-platinum.loan_amount_decisioning_score_and_cltv_limits.apply_cltv_limits.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_amount_decisioning_score_and_cltv_limits.apply_cltv_limits
# reads: fico, loan_purpose, cltv_pct, loan_amount, property_type, product_is_interest_only, listed_for_sale_last_6_months, channel
# implements job: acra-platinum.loan_amount_decisioning_score_and_cltv_limits.apply_cltv_limits

import rules_lib

def check(ctx):
    fico = ctx['fico']
    loan_purpose = ctx['loan_purpose']
    cltv_pct = ctx['cltv_pct']
    loan_amount = ctx['loan_amount']
    property_type = ctx['property_type']
    product_is_interest_only = ctx['product_is_interest_only']
    listed_for_sale_last_6_months = ctx['listed_for_sale_last_6_months']
    channel = ctx['channel']

    missing = rules_lib.gaps(
        fico=fico,
        loan_purpose=loan_purpose,
        cltv_pct=cltv_pct,
        loan_amount=loan_amount,
        property_type=property_type,
        product_is_interest_only=product_is_interest_only,
        listed_for_sale_last_6_months=listed_for_sale_last_6_months,
        channel=channel,
    )
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(loan_purpose, 'purchase'):
        purpose = 'purchase'
    elif rules_lib.same(loan_purpose, 'rate & term'):
        purpose = 'rate_term'
    elif rules_lib.same(loan_purpose, 'cash-out'):
        purpose = 'cash_out'
    else:
        return rules_lib.unknown('loan_purpose')

    if fico >= 730:
        matrix_max = {'purchase': 80, 'rate_term': 80, 'cash_out': 75}[purpose]
    elif fico >= 721:
        matrix_max = {'purchase': 80, 'rate_term': 80, 'cash_out': 65}[purpose]
    elif fico >= 700:
        matrix_max = {'purchase': 80, 'rate_term': 80, 'cash_out': 55}[purpose]
    else:
        return rules_lib.unknown('fico')

    maxima = [matrix_max]
    if loan_amount < 350000 or loan_amount > 1500000:
        maxima.append(75.00)
    if rules_lib.same(property_type, 'Warrantable Condo') or rules_lib.same(property_type, 'Two-Units'):
        maxima.append(75.00)

    interest_only = rules_lib.flag(product_is_interest_only)
    if interest_only is None:
        return rules_lib.unknown('product_is_interest_only')
    if interest_only:
        maxima.append(75.00)

    listed = rules_lib.flag(listed_for_sale_last_6_months)
    if listed is None:
        return rules_lib.unknown('listed_for_sale_last_6_months')
    if listed:
        maxima.append(65)

    if rules_lib.same(channel, 'Correspondent') and 700 <= fico <= 719:
        maxima.append(60)

    return cltv_pct <= min(maxima)
