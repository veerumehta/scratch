# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.12
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶13
# reads: loan_amount, delayed_financing, product_is_interest_only, fico, loan_purpose, cltv_pct

import rules_lib


def check(ctx):
    loan_amount = ctx['loan_amount']
    delayed_raw = ctx['delayed_financing']
    interest_only_raw = ctx['product_is_interest_only']

    missing = rules_lib.gaps(
        loan_amount=loan_amount,
        delayed_financing=delayed_raw,
        product_is_interest_only=interest_only_raw,
    )
    if missing:
        return rules_lib.unknown(*missing)

    delayed = rules_lib.flag(delayed_raw)
    interest_only = rules_lib.flag(interest_only_raw)
    if delayed is None:
        return rules_lib.unknown('delayed_financing')
    if interest_only is None:
        return rules_lib.unknown('product_is_interest_only')

    if delayed and loan_amount > 1500000:
        return False

    if interest_only:
        fico = ctx['fico']
        missing = rules_lib.gaps(fico=fico)
        if missing:
            return rules_lib.unknown(*missing)
        if loan_amount < 250000 or loan_amount > 3000000 or fico < 640:
            return False

    if loan_amount < 200000:
        loan_purpose = ctx['loan_purpose']
        missing = rules_lib.gaps(loan_purpose=loan_purpose)
        if missing:
            return rules_lib.unknown(*missing)

        if rules_lib.same(loan_purpose, 'purchase'):
            cltv_pct = ctx['cltv_pct']
            missing = rules_lib.gaps(cltv_pct=cltv_pct)
            if missing:
                return rules_lib.unknown(*missing)
            if cltv_pct > 80:
                return False
        elif rules_lib.same(
            loan_purpose,
            'rate & term',
            'cash-out',
            'refinance rate & term',
            'refinance cash-out',
        ):
            cltv_pct = ctx['cltv_pct']
            missing = rules_lib.gaps(cltv_pct=cltv_pct)
            if missing:
                return rules_lib.unknown(*missing)
            if cltv_pct > 75:
                return False

    # The supplied fields do not provide all inputs needed to determine DSCR
    # under §3.1, so a loan over $2,000,000 cannot be adjudicated here.
    if loan_amount > 2000000:
        return rules_lib.unknown('DSCR inputs required by §3.1')

    return True
