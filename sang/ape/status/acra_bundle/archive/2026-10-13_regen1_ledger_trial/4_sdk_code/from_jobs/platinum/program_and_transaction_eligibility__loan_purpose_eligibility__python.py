# rule: acra-platinum.program_and_transaction_eligibility.loan_purpose_eligibility.python
# origin: written from a job
# description: Python formalization of acra-platinum.program_and_transaction_eligibility.loan_purpose_eligibility
# reads: loan_purpose, loan_amount, current_lease_in_place
# implements job: acra-platinum.program_and_transaction_eligibility.loan_purpose_eligibility

import rules_lib

def check(ctx):
    loan_purpose = ctx['loan_purpose']
    missing = rules_lib.gaps(loan_purpose=loan_purpose)
    if missing:
        return rules_lib.unknown(*missing)

    is_purchase = rules_lib.same(loan_purpose, 'Purchase')
    is_rate_term = rules_lib.same(loan_purpose, 'Rate & Term Refinance')
    is_cash_out = rules_lib.same(loan_purpose, 'Cash-Out Refinance')
    is_delayed = rules_lib.same(loan_purpose, 'Delayed Financing')

    if not (is_purchase or is_rate_term or is_cash_out or is_delayed):
        return False

    if is_delayed:
        loan_amount = ctx['loan_amount']
        missing = rules_lib.gaps(loan_amount=loan_amount)
        if missing:
            return rules_lib.unknown(*missing)
        if loan_amount > 1500000:
            return False

    if is_cash_out:
        current_lease_in_place = ctx['current_lease_in_place']
        missing = rules_lib.gaps(current_lease_in_place=current_lease_in_place)
        if missing:
            return rules_lib.unknown(*missing)
        has_current_lease = rules_lib.flag(current_lease_in_place)
        if has_current_lease is None:
            return rules_lib.unknown('current_lease_in_place')
        if not has_current_lease:
            return False

    return True
