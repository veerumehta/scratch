# rule: acra-platinum.loan_program_eligibility.eligible_loan_purpose.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.eligible_loan_purpose
# reads: LoanCore.loan_purpose
# implements job: acra-platinum.loan_program_eligibility.eligible_loan_purpose

import rules_lib


def check(ctx):
    loan_purpose = ctx['LoanCore.loan_purpose']
    missing = rules_lib.gaps(loan_purpose=loan_purpose)
    if missing:
        return rules_lib.unknown(*missing)
    return any(
        rules_lib.same(loan_purpose, purpose)
        for purpose in (
            'Purchase',
            'Rate & Term Refinance',
            'Cash-Out Refinance',
            'Delayed Financing',
        )
    )
