# rule: acra-standard.loan_program_eligibility.qualification_method.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_program_eligibility.qualification_method
# reads: LoanCore.dscr_qualification_method
# implements job: acra-standard.loan_program_eligibility.qualification_method

import rules_lib

def check(ctx):
    method = ctx['LoanCore.dscr_qualification_method']
    missing = rules_lib.gaps(method=method)
    if missing:
        return rules_lib.unknown(*missing)
    return rules_lib.same(method, 'calculated DSCR', 'No Ratio DSCR')
