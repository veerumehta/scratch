# rule: acra-standard.borrower_citizenship_and_foreign_national_requirements.verify_citizenship_type_and_citizenship_specific_requirements.python
# origin: written from a job
# description: Python formalization of acra-standard.borrower_citizenship_and_foreign_national_requirements.verify_citizenship_type_and_citizenship_specific_requirements
# reads: citizenship_type, loan_amount, fico, cltv_pct, loan_purpose
# implements job: acra-standard.borrower_citizenship_and_foreign_national_requirements.verify_citizenship_type_and_citizenship_specific_requirements

import rules_lib

def check(ctx):
    citizenship_type = ctx['citizenship_type']
    citizenship = rules_lib.match(citizenship_type, [
        'US Citizen', 'Permanent Resident', 'Non-Permanent Resident',
        'Foreign National', 'ITIN'
    ])
    missing = rules_lib.gaps(citizenship_type=citizenship_type)
    if missing:
        return rules_lib.unknown(*missing)
    if citizenship is None:
        return False
    if not rules_lib.same(citizenship, 'ITIN'):
        return True

    loan_amount = ctx['loan_amount']
    fico = ctx['fico']
    cltv_pct = ctx['cltv_pct']
    loan_purpose = ctx['loan_purpose']
    missing = rules_lib.gaps(
        loan_amount=loan_amount, fico=fico,
        cltv_pct=cltv_pct, loan_purpose=loan_purpose
    )
    if missing:
        return rules_lib.unknown(*missing)

    if loan_amount > 1000000 or fico < 640:
        return False

    if rules_lib.same(loan_purpose, 'purchase'):
        is_purchase = True
    elif rules_lib.same(loan_purpose, 'refinance') or rules_lib.same(
        loan_purpose, 'rate and term'
    ) or rules_lib.same(loan_purpose, 'cash-out'):
        is_purchase = False
    else:
        return rules_lib.unknown('loan_purpose')

    # Apply only the FICO tiers stated in the table; do not extend the
    # printed “FICO 700” tier to scores above 700.
    if 640 <= fico <= 659:
        max_cltv = 60
    elif 660 <= fico <= 699:
        max_cltv = 65 if is_purchase else 60
    elif fico == 700:
        max_cltv = 70 if is_purchase else 65
    else:
        max_cltv = None

    return max_cltv is None or cltv_pct <= max_cltv
