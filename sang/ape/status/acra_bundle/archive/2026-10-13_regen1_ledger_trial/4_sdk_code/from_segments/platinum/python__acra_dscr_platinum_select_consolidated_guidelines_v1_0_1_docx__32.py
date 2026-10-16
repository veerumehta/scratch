# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.32
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶18
# reads: delayed_financing, loan_amount

import rules_lib

def check(ctx):
    delayed_financing = ctx['delayed_financing']
    loan_amount = ctx['loan_amount']
    missing = rules_lib.gaps(delayed_financing=delayed_financing, loan_amount=loan_amount)
    if missing:
        return rules_lib.unknown(*missing)

    delayed_financing = rules_lib.flag(delayed_financing)
    if delayed_financing is None:
        return rules_lib.unknown('delayed_financing')
    if not delayed_financing:
        return True
    if not rules_lib.known(loan_amount):
        return rules_lib.unknown('loan_amount')
    return loan_amount <= 1500000
