# rule: acra-standard.loan_program_eligibility.interest_only_availability_restrictions.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_program_eligibility.interest_only_availability_restrictions
# reads: MortgageLoanInformation.is_interest_only, Borrower.is_first_time_homebuyer, LoanCore.loan_purpose, SubjectProperty.is_vacant, SubjectProperty.is_listed_for_sale
# implements job: acra-standard.loan_program_eligibility.interest_only_availability_restrictions

import rules_lib


def check(ctx):
    interest_only = rules_lib.flag(ctx['MortgageLoanInformation.is_interest_only'])
    missing = rules_lib.gaps(interest_only=interest_only)
    if missing:
        return rules_lib.unknown(*missing)
    if not interest_only:
        return True

    first_time_homebuyer = rules_lib.flag(ctx['Borrower.is_first_time_homebuyer'])
    loan_purpose = ctx['LoanCore.loan_purpose']
    is_vacant = rules_lib.flag(ctx['SubjectProperty.is_vacant'])
    is_listed_for_sale = rules_lib.flag(ctx['SubjectProperty.is_listed_for_sale'])

    missing = rules_lib.gaps(
        first_time_homebuyer=first_time_homebuyer,
        loan_purpose=loan_purpose,
        is_vacant=is_vacant,
        is_listed_for_sale=is_listed_for_sale,
    )
    if missing:
        return rules_lib.unknown(*missing)

    if first_time_homebuyer or is_listed_for_sale:
        return False
    if rules_lib.same(loan_purpose, 'refinance') and is_vacant:
        return False
    return True
