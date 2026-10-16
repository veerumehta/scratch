# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.19
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.10 ¶1
# reads: loan_purpose, occupancy_subtype

import rules_lib

def check(ctx):
    loan_purpose = ctx['loan_purpose']
    occupancy_subtype = ctx['occupancy_subtype']
    missing = rules_lib.gaps(loan_purpose=loan_purpose, occupancy_subtype=occupancy_subtype)
    if missing:
        return rules_lib.unknown(*missing)
    return (
        rules_lib.same(loan_purpose, 'business purpose')
        and rules_lib.same(occupancy_subtype, 'investment')
    )
