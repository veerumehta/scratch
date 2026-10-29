# rule: acra-platinum.loan_program_eligibility.loan_size_cltv_cap.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.loan_size_cltv_cap
# reads: LoanCore.total_loan_amount_usd, LoanCore.cltv_percent
# implements job: acra-platinum.loan_program_eligibility.loan_size_cltv_cap

import rules_lib

def check(ctx):
    amount = ctx['LoanCore.total_loan_amount_usd']
    missing = rules_lib.gaps(amount=amount)
    if missing:
        return rules_lib.unknown(*missing)

    if amount < 350000 or amount > 1500000:
        cltv = ctx['LoanCore.cltv_percent']
        missing = rules_lib.gaps(cltv=cltv)
        if missing:
            return rules_lib.unknown(*missing)
        cltv_value = rules_lib.percent(cltv, 'percent')
        if cltv_value is None:
            return rules_lib.unknown('LoanCore.cltv_percent')
        return cltv_value <= 75.00

    return True
