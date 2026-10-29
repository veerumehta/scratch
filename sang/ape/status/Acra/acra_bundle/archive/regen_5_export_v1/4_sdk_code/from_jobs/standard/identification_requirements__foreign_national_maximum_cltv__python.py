# rule: acra-standard.identification_requirements.foreign_national_maximum_cltv.python
# origin: written from a job
# description: Python formalization of acra-standard.identification_requirements.foreign_national_maximum_cltv
# reads: Borrower.citizenship_status, LoanCore.loan_purpose, LoanCore.cltv_percent
# implements job: acra-standard.identification_requirements.foreign_national_maximum_cltv

import rules_lib

def check(ctx):
    citizenship = ctx['Borrower.citizenship_status']
    missing = rules_lib.gaps(citizenship=citizenship)
    if missing:
        return rules_lib.unknown(*missing)
    if not rules_lib.same(citizenship, 'Foreign National'):
        return True

    purpose = ctx['LoanCore.loan_purpose']
    cltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(purpose=purpose, cltv=cltv)
    if missing:
        return rules_lib.unknown(*missing)

    cltv_value = rules_lib.percent(cltv, 'percent')
    if cltv_value is None:
        return rules_lib.unknown('LoanCore.cltv_percent')
    if rules_lib.same(purpose, 'purchase'):
        return cltv_value <= 70
    if rules_lib.same(purpose, 'refinance', 'rate & term', 'rate and term refinance', 'refinance rate & term', 'refinance rate and term', 'cash-out', 'cash out', 'cash-out refinance', 'cash out refinance', 'refinance cash-out', 'refinance cash out'):
        return cltv_value <= 65
    return rules_lib.unknown('LoanCore.loan_purpose')
