# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.42
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶21
# reads: delayed_financing, loan_amount

import decimal
import math
import rules_lib

def check(ctx):
    delayed_financing = ctx['delayed_financing']
    loan_amount = ctx['loan_amount']
    missing = rules_lib.gaps(delayed_financing=delayed_financing, loan_amount=loan_amount)
    if missing:
        return rules_lib.unknown(*missing)

    delayed = rules_lib.flag(delayed_financing)
    if delayed is None:
        return rules_lib.unknown('delayed_financing')
    if not delayed:
        return True

    numeric = isinstance(loan_amount, (int, float, decimal.Decimal)) and not isinstance(loan_amount, bool)
    finite = not isinstance(loan_amount, float) or math.isfinite(loan_amount)
    finite = finite and (not isinstance(loan_amount, decimal.Decimal) or loan_amount.is_finite())
    if not numeric or not finite:
        return rules_lib.unknown('loan_amount')
    return loan_amount <= 1_500_000
