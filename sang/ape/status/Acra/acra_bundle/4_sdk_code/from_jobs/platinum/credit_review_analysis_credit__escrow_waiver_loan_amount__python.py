# rule: acra-platinum.credit_review_analysis_credit.escrow_waiver_loan_amount.python
# origin: written from a job
# description: Python formalization of acra-platinum.credit_review_analysis_credit.escrow_waiver_loan_amount
# reads: LoanCore.is_escrow_waived, LoanCore.total_loan_amount_usd
# implements job: acra-platinum.credit_review_analysis_credit.escrow_waiver_loan_amount

import rules_lib

def check(ctx):
    escrow_waived = ctx['LoanCore.is_escrow_waived']
    missing = rules_lib.gaps(escrow_waived=escrow_waived)
    if missing:
        return rules_lib.unknown(*missing)

    escrow_waived = rules_lib.flag(escrow_waived)
    if escrow_waived is None:
        return rules_lib.unknown('LoanCore.is_escrow_waived')
    if not escrow_waived:
        return True

    total_loan_amount_usd = ctx['LoanCore.total_loan_amount_usd']
    missing = rules_lib.gaps(total_loan_amount_usd=total_loan_amount_usd)
    if missing:
        return rules_lib.unknown(*missing)

    result = rules_lib.band(total_loan_amount_usd, [(1500000, True)], above=False)
    if result is None:
        return rules_lib.unknown('LoanCore.total_loan_amount_usd')
    return result
