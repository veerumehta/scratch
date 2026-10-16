# rule: acra-standard.loan_program_eligibility.interest_only_eligibility.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_program_eligibility.interest_only_eligibility
# reads: LoanCore.total_loan_amount_usd, CreditReport.representative_score, LoanCore.is_interest_only_10_40, LoanCore.cltv_percent, Borrower.is_first_time_homebuyer, LoanCore.loan_purpose, SubjectProperty.is_vacant, SubjectProperty.is_listed_for_sale
# implements job: acra-standard.loan_program_eligibility.interest_only_eligibility

import rules_lib

def check(ctx):
    amount = ctx['LoanCore.total_loan_amount_usd']
    fico = ctx['CreditReport.representative_score']
    is_10_40 = ctx['LoanCore.is_interest_only_10_40']
    cltv = ctx['LoanCore.cltv_percent']
    first_time = ctx['Borrower.is_first_time_homebuyer']
    loan_purpose = ctx['LoanCore.loan_purpose']
    vacant = ctx['SubjectProperty.is_vacant']
    listed = ctx['SubjectProperty.is_listed_for_sale']

    missing = rules_lib.gaps(
        amount=amount, fico=fico, is_10_40=is_10_40, cltv=cltv,
        first_time=first_time, loan_purpose=loan_purpose,
        vacant=vacant, listed=listed
    )
    if missing:
        return rules_lib.unknown(*missing)

    is_10_40 = rules_lib.flag(is_10_40)
    first_time = rules_lib.flag(first_time)
    vacant = rules_lib.flag(vacant)
    listed = rules_lib.flag(listed)
    if is_10_40 is None:
        return rules_lib.unknown('LoanCore.is_interest_only_10_40')
    if first_time is None:
        return rules_lib.unknown('Borrower.is_first_time_homebuyer')
    if vacant is None:
        return rules_lib.unknown('SubjectProperty.is_vacant')
    if listed is None:
        return rules_lib.unknown('SubjectProperty.is_listed_for_sale')

    is_refinance = rules_lib.same(
        loan_purpose, 'refinance', 'rate and term', 'cash-out', 'cash-out refinance'
    )
    if (
        amount < 250000
        or fico < 640
        or first_time
        or (is_refinance and vacant)
        or listed
    ):
        return False

    if is_10_40 and (amount > 3000000 or cltv > 80):
        return False
    return True
