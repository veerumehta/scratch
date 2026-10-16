# rule: acra-standard.loan_amount_fico_and_matrix_leverage.loan_amount_conditions_and_matrix_footnotes.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_amount_fico_and_matrix_leverage.loan_amount_conditions_and_matrix_footnotes
# reads: loan_amount, delayed_financing, product_is_interest_only, loan_purpose, cltv_pct, fico
# implements job: acra-standard.loan_amount_fico_and_matrix_leverage.loan_amount_conditions_and_matrix_footnotes

import rules_lib


def check(ctx):
    loan_amount = rules_lib.ratio(ctx['loan_amount'], 1)
    missing = rules_lib.gaps(loan_amount=loan_amount)
    if missing:
        return rules_lib.unknown(*missing)

    delayed_financing = rules_lib.flag(ctx['delayed_financing'])
    missing = rules_lib.gaps(delayed_financing=delayed_financing)
    if missing:
        return rules_lib.unknown(*missing)

    product_is_interest_only = rules_lib.flag(ctx['product_is_interest_only'])
    missing = rules_lib.gaps(product_is_interest_only=product_is_interest_only)
    if missing:
        return rules_lib.unknown(*missing)

    if loan_amount < 200000:
        loan_purpose = ctx['loan_purpose']
        missing = rules_lib.gaps(loan_purpose=loan_purpose)
        if missing:
            return rules_lib.unknown(*missing)

        if rules_lib.same(loan_purpose, 'purchase'):
            cltv_pct = rules_lib.ratio(ctx['cltv_pct'], 1)
            missing = rules_lib.gaps(cltv_pct=cltv_pct)
            if missing:
                return rules_lib.unknown(*missing)
            if cltv_pct > 0.80:
                return False
        elif rules_lib.same(loan_purpose, 'rate & term', 'cash-out'):
            cltv_pct = rules_lib.ratio(ctx['cltv_pct'], 1)
            missing = rules_lib.gaps(cltv_pct=cltv_pct)
            if missing:
                return rules_lib.unknown(*missing)
            if cltv_pct > 0.75:
                return False

    if product_is_interest_only:
        if loan_amount > 3000000:
            return False
        fico = rules_lib.ratio(ctx['fico'], 1)
        missing = rules_lib.gaps(fico=fico)
        if missing:
            return rules_lib.unknown(*missing)
        if fico < 640:
            return False

    if delayed_financing and loan_amount > 1500000:
        return False

    return True
