# rule: acra-platinum.loan_program_eligibility.cash_out_current_lease.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.cash_out_current_lease
# reads: LoanCore.loan_purpose, SubjectProperty.has_current_lease
# implements job: acra-platinum.loan_program_eligibility.cash_out_current_lease

import rules_lib

def check(ctx):
    loan_purpose = ctx['LoanCore.loan_purpose']
    missing = rules_lib.gaps(loan_purpose=loan_purpose)
    if missing:
        return rules_lib.unknown(*missing)

    if not rules_lib.same(loan_purpose, 'Cash-Out Refinance'):
        return True

    lease_value = ctx['SubjectProperty.has_current_lease']
    lease = rules_lib.flag(lease_value)
    missing = rules_lib.gaps(lease=lease)
    if missing:
        return rules_lib.unknown(*missing)
    return lease
