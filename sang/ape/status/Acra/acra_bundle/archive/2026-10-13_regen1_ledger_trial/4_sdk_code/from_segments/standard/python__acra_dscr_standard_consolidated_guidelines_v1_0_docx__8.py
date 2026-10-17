# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.8
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶9
# reads: delayed_financing, loan_amount

import rules_lib

def check(ctx):
    delayed_financing = ctx['delayed_financing']
    missing = rules_lib.gaps(delayed_financing=delayed_financing)
    if missing:
        return rules_lib.unknown(*missing)

    delayed = rules_lib.flag(delayed_financing)
    if delayed is None:
        return rules_lib.unknown('delayed_financing')
    if not delayed:
        return True

    loan_amount = ctx['loan_amount']
    missing = rules_lib.gaps(loan_amount=loan_amount)
    if missing:
        return rules_lib.unknown(*missing)
    return loan_amount <= 1_500_000
