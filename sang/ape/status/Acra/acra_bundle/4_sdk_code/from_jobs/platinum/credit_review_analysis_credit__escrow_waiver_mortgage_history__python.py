# rule: acra-platinum.credit_review_analysis_credit.escrow_waiver_mortgage_history.python
# origin: written from a job
# description: Python formalization of acra-platinum.credit_review_analysis_credit.escrow_waiver_mortgage_history
# reads: LoanCore.is_escrow_waived, CreditReport.mortgage_0x30x24
# implements job: acra-platinum.credit_review_analysis_credit.escrow_waiver_mortgage_history

import rules_lib

def check(ctx):
    escrow_waived = rules_lib.flag(ctx['LoanCore.is_escrow_waived'])
    mortgage_history = rules_lib.flag(ctx['CreditReport.mortgage_0x30x24'])
    missing = rules_lib.gaps(
        escrow_waived=escrow_waived,
        mortgage_history=mortgage_history,
    )
    if missing:
        return rules_lib.unknown(*missing)
    return (not escrow_waived) or mortgage_history
