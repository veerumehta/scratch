# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.6
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶7
# reads: loan_amount, fico

import rules_lib


def check(ctx):
    loan_amount = ctx['loan_amount']
    fico = ctx['fico']
    missing = rules_lib.gaps(loan_amount=loan_amount, fico=fico)
    if missing:
        return rules_lib.unknown(*missing)

    if loan_amount < 100000 or loan_amount > 3000000 or loan_amount % 50 != 0:
        return False

    minimum_fico = rules_lib.band(
        loan_amount,
        [(1500000, 600), (2000000, 620), (3000000, 700)],
        above=None,
    )
    return minimum_fico is not None and fico >= minimum_fico
