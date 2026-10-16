# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.5
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶6
# reads: loan_amount

import decimal
import rules_lib

def check(ctx):
    loan_amount = ctx['loan_amount']
    missing = rules_lib.gaps(loan_amount=loan_amount)
    if missing:
        return rules_lib.unknown(*missing)
    try:
        amount = decimal.Decimal(str(loan_amount))
    except (decimal.InvalidOperation, ValueError, TypeError):
        return rules_lib.unknown('loan_amount')
    if not amount.is_finite():
        return rules_lib.unknown('loan_amount')
    return (decimal.Decimal('100000') <= amount <= decimal.Decimal('2000000') and
            amount % decimal.Decimal('50') == 0, {'loan_amount': amount})
