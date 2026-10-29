# rule: acra-platinum.unassigned_provisions.no_ratio_or_sub_1_0_dscr_treatment.python
# origin: written from a job
# description: Python formalization of acra-platinum.unassigned_provisions.no_ratio_or_sub_1_0_dscr_treatment
# reads: LoanCore.dscr_qualification_method
# implements job: acra-platinum.unassigned_provisions.no_ratio_or_sub_1_0_dscr_treatment

import rules_lib

def check(ctx):
    method = ctx['LoanCore.dscr_qualification_method']
    missing = rules_lib.gaps(method=method)
    if missing:
        return rules_lib.unknown(*missing)
    if rules_lib.same(method, 'No Ratio', 'No Ratio DSCR'):
        return True
    return rules_lib.unknown('DSCR value', 'channel minimum')
