# rule: acra-platinum.asset_assessment.listed_property_amortization.python
# origin: written from a job
# description: Python formalization of acra-platinum.asset_assessment.listed_property_amortization
# reads: MortgageLoanInformation.is_interest_only, LoanCore.is_interest_only_10_40
# implements job: acra-platinum.asset_assessment.listed_property_amortization

import rules_lib

def check(ctx):
    mortgage_io = ctx['MortgageLoanInformation.is_interest_only']
    loan_core_io_10_40 = ctx['LoanCore.is_interest_only_10_40']

    missing = rules_lib.gaps(
        mortgage_io=mortgage_io,
        loan_core_io_10_40=loan_core_io_10_40,
    )
    if missing:
        return rules_lib.unknown(*missing)

    mortgage_io = rules_lib.flag(mortgage_io)
    loan_core_io_10_40 = rules_lib.flag(loan_core_io_10_40)
    if mortgage_io is None or loan_core_io_10_40 is None:
        return rules_lib.unknown('interest_only')

    return not (mortgage_io or loan_core_io_10_40)
