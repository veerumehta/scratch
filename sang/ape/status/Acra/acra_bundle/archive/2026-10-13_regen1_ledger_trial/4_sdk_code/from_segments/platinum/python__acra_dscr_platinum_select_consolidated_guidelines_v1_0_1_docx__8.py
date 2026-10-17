# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.8
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶9
# reads: loan_amount, cltv_pct

import rules_lib


def check(ctx):
    loan_amount = ctx['loan_amount']
    missing = rules_lib.gaps(loan_amount=loan_amount)
    if missing:
        return rules_lib.unknown(*missing)

    if loan_amount < 100000 or loan_amount > 2000000 or loan_amount % 50 != 0:
        return False

    if loan_amount < 350000 or loan_amount > 1500000:
        cltv_pct = ctx['cltv_pct']
        missing = rules_lib.gaps(cltv_pct=cltv_pct)
        if missing:
            return rules_lib.unknown(*missing)
        return cltv_pct <= 75.00

    return True
