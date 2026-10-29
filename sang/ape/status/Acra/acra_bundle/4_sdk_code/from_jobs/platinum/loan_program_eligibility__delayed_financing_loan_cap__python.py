# rule: acra-platinum.loan_program_eligibility.delayed_financing_loan_cap.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.delayed_financing_loan_cap
# reads: LoanCore.loan_purpose, LoanCore.total_loan_amount_usd
# implements job: acra-platinum.loan_program_eligibility.delayed_financing_loan_cap

import rules_lib

def check(ctx):
    purpose = ctx['LoanCore.loan_purpose']
    missing = rules_lib.gaps(purpose=purpose)
    if missing:
        return rules_lib.unknown(*missing)
    if not rules_lib.same(purpose, 'Delayed Financing'):
        return True

    amount = ctx['LoanCore.total_loan_amount_usd']
    missing = rules_lib.gaps(amount=amount)
    if missing:
        return rules_lib.unknown(*missing)
    return amount <= 1500000
