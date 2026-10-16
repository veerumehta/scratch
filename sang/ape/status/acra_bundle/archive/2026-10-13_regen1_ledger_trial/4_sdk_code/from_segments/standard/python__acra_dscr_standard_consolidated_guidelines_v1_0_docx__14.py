# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.14
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶15
# reads: vacant_property, loan_purpose, dscr_documentation_type

import rules_lib

def check(ctx):
    vacant_property = ctx['vacant_property']
    loan_purpose = ctx['loan_purpose']
    missing = rules_lib.gaps(vacant_property=vacant_property, loan_purpose=loan_purpose)
    if missing:
        return rules_lib.unknown(*missing)

    vacant = rules_lib.flag(vacant_property)
    if vacant is None:
        return rules_lib.unknown('vacant_property')
    if not vacant or not rules_lib.same(loan_purpose, 'purchase'):
        return True

    dscr_documentation_type = ctx['dscr_documentation_type']
    missing = rules_lib.gaps(dscr_documentation_type=dscr_documentation_type)
    if missing:
        return rules_lib.unknown(*missing)
    return rules_lib.same(dscr_documentation_type, '1007', 'FNMA Form 1007', '1007 survey')
