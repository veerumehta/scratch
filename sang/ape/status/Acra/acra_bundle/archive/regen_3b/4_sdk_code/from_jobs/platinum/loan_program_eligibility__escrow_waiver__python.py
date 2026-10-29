# rule: acra-platinum.loan_program_eligibility.escrow_waiver.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.escrow_waiver
# reads: LoanCore.total_loan_amount_usd
# implements job: acra-platinum.loan_program_eligibility.escrow_waiver

def check(ctx):
    loan_amount = ctx['LoanCore.total_loan_amount_usd']
    missing = rules_lib.gaps(loan_amount=loan_amount)
    if missing:
        return rules_lib.unknown(*missing)
    return loan_amount <= 1_500_000
