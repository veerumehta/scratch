# rule: acra-standard.credit_housing_history_and_escrow_waiver.review_bankruptcy_and_foreclosure_restrictions.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_housing_history_and_escrow_waiver.review_bankruptcy_and_foreclosure_restrictions
# reads: bankruptcy_or_foreclosure, months_since_bankruptcy_or_foreclosure, loan_purpose, cltv_pct
# implements job: acra-standard.credit_housing_history_and_escrow_waiver.review_bankruptcy_and_foreclosure_restrictions

import rules_lib

def check(ctx):
    bankruptcy_or_foreclosure = ctx['bankruptcy_or_foreclosure']
    missing = rules_lib.gaps(bankruptcy_or_foreclosure=bankruptcy_or_foreclosure)
    if missing:
        return rules_lib.unknown(*missing)

    applies = rules_lib.flag(bankruptcy_or_foreclosure)
    if applies is None:
        return rules_lib.unknown('bankruptcy_or_foreclosure')
    if not applies:
        return True

    months_since_bankruptcy_or_foreclosure = ctx['months_since_bankruptcy_or_foreclosure']
    missing = rules_lib.gaps(months_since_bankruptcy_or_foreclosure=months_since_bankruptcy_or_foreclosure)
    if missing:
        return rules_lib.unknown(*missing)

    if months_since_bankruptcy_or_foreclosure < 12:
        return False
    if months_since_bankruptcy_or_foreclosure >= 36:
        return True

    loan_purpose = ctx['loan_purpose']
    cltv_pct = ctx['cltv_pct']
    missing = rules_lib.gaps(loan_purpose=loan_purpose, cltv_pct=cltv_pct)
    if missing:
        return rules_lib.unknown(*missing)

    if months_since_bankruptcy_or_foreclosure < 24:
        maximum_cltv = 65
    elif rules_lib.same(loan_purpose, 'purchase'):
        maximum_cltv = 80
    elif rules_lib.same(loan_purpose, 'Refi R/T') or rules_lib.same(loan_purpose, 'Refi C/O'):
        maximum_cltv = 75
    else:
        return rules_lib.unknown('loan_purpose')

    return cltv_pct <= maximum_cltv
