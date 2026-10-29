# rule: acra-platinum.loan_program_eligibility.interest_only_cltv_cap.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.interest_only_cltv_cap
# reads: MortgageLoanInformation.is_interest_only, LoanCore.cltv_percent
# implements job: acra-platinum.loan_program_eligibility.interest_only_cltv_cap

import decimal
import rules_lib

def check(ctx):
    io_value = ctx['MortgageLoanInformation.is_interest_only']
    missing = rules_lib.gaps(is_interest_only=io_value)
    if missing:
        return rules_lib.unknown(*missing)
    is_interest_only = rules_lib.flag(io_value)
    if is_interest_only is None:
        return rules_lib.unknown('MortgageLoanInformation.is_interest_only')
    if not is_interest_only:
        return True

    cltv_value = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv=cltv_value)
    if missing:
        return rules_lib.unknown(*missing)
    try:
        cltv = decimal.Decimal(str(cltv_value).strip().removesuffix('%').strip())
    except decimal.InvalidOperation:
        return rules_lib.unknown('LoanCore.cltv_percent')
    return cltv <= decimal.Decimal('75.00')
