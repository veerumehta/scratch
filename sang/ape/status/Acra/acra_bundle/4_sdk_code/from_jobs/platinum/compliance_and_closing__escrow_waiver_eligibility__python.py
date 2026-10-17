# rule: acra-platinum.compliance_and_closing.escrow_waiver_eligibility.python
# origin: written from a job
# description: Python formalization of acra-platinum.compliance_and_closing.escrow_waiver_eligibility
# reads: LoanCore.total_loan_amount_usd
# implements job: acra-platinum.compliance_and_closing.escrow_waiver_eligibility

import rules_lib

def check(ctx):
    total_loan_amount_usd = ctx['LoanCore.total_loan_amount_usd']
    missing = rules_lib.gaps(total_loan_amount_usd=total_loan_amount_usd)
    if missing:
        return rules_lib.unknown(*missing)
    return total_loan_amount_usd <= 1500000
