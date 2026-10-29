# rule: acra-standard.loan_program_eligibility.delayed_financing_loan_amount_cap.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_program_eligibility.delayed_financing_loan_amount_cap
# reads: LoanCore.is_delayed_financing, LoanCore.total_loan_amount_usd
# implements job: acra-standard.loan_program_eligibility.delayed_financing_loan_amount_cap

import rules_lib

def check(ctx):
    delayed_financing = ctx['LoanCore.is_delayed_financing']
    loan_amount_usd = ctx['LoanCore.total_loan_amount_usd']

    missing = rules_lib.gaps(
        delayed_financing=delayed_financing,
        loan_amount_usd=loan_amount_usd,
    )
    if missing:
        return rules_lib.unknown(*missing)

    delayed_financing = rules_lib.flag(delayed_financing)
    if delayed_financing is None:
        return rules_lib.unknown('delayed_financing')

    return not delayed_financing or loan_amount_usd <= 1_500_000
