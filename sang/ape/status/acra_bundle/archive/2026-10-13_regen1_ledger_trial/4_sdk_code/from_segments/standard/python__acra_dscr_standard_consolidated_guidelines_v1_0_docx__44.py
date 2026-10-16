# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.44
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶23
# reads: loan_amount, fico

import rules_lib

def check(ctx):
    loan_amount = ctx['loan_amount']
    fico = ctx['fico']
    missing = rules_lib.gaps(loan_amount=loan_amount, fico=fico)
    if missing:
        return rules_lib.unknown(*missing)

    # This checks only the stated matrix-floor condition. Loans above the
    # stated amount range are outside this condition, not deemed eligible.
    if loan_amount <= 1500000:
        return fico >= 600
    return True
