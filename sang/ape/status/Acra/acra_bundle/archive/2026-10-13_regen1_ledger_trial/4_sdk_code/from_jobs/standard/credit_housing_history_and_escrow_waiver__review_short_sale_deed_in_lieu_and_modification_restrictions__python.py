# rule: acra-standard.credit_housing_history_and_escrow_waiver.review_short_sale_deed_in_lieu_and_modification_restrictions.python
# origin: written from a job
# description: Python formalization of acra-standard.credit_housing_history_and_escrow_waiver.review_short_sale_deed_in_lieu_and_modification_restrictions
# reads: short_sale_dil_or_modification, months_since_short_sale_dil_or_modification, loan_purpose, cltv_pct
# implements job: acra-standard.credit_housing_history_and_escrow_waiver.review_short_sale_deed_in_lieu_and_modification_restrictions

import rules_lib

def check(ctx):
    event_value = ctx['short_sale_dil_or_modification']
    missing = rules_lib.gaps(short_sale_dil_or_modification=event_value)
    if missing:
        return rules_lib.unknown(*missing)
    applies = rules_lib.flag(event_value)
    if applies is None:
        return rules_lib.unknown('short_sale_dil_or_modification')
    if not applies:
        return True

    months = ctx['months_since_short_sale_dil_or_modification']
    missing = rules_lib.gaps(months_since_short_sale_dil_or_modification=months)
    if missing:
        return rules_lib.unknown(*missing)
    if months >= 24:
        return True

    purpose = ctx['loan_purpose']
    cltv = ctx['cltv_pct']
    missing = rules_lib.gaps(loan_purpose=purpose, cltv_pct=cltv)
    if missing:
        return rules_lib.unknown(*missing)

    if months < 12:
        if rules_lib.same(purpose, 'purchase'):
            return cltv <= 75
        if rules_lib.same(purpose, 'Refi R/T') or rules_lib.same(purpose, 'Refi C/O'):
            return cltv <= 70
        return True

    if months <= 23:
        if rules_lib.same(purpose, 'purchase'):
            return cltv <= 80
        if rules_lib.same(purpose, 'Refi R/T') or rules_lib.same(purpose, 'Refi C/O'):
            return cltv <= 75
        return True

    return True
