# rule: acra-platinum.funds_to_close_seasoning_and_reserves.loan_amount_limits.python
# origin: written from a job
# description: Python formalization of acra-platinum.funds_to_close_seasoning_and_reserves.loan_amount_limits
# reads: loan_amount, cltv_pct
# implements job: acra-platinum.funds_to_close_seasoning_and_reserves.loan_amount_limits

import rules_lib

def check(ctx):
    loan_amount = ctx['loan_amount']
    missing = rules_lib.gaps(loan_amount=loan_amount)
    if missing:
        return rules_lib.unknown(*missing)

    if not (100000 <= loan_amount <= 2000000):
        return False
    if loan_amount % 50 != 0:
        return False

    if loan_amount < 350000 or loan_amount > 1500000:
        cltv_pct = ctx['cltv_pct']
        missing = rules_lib.gaps(cltv_pct=cltv_pct)
        if missing:
            return rules_lib.unknown(*missing)
        if cltv_pct > 75.00:
            return False

    return True
