# rule: acra-platinum.loan_program_eligibility.listed_for_sale_cltv_cap.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.listed_for_sale_cltv_cap
# reads: SubjectProperty.listed_for_sale_last_6_months, LoanCore.cltv_percent
# implements job: acra-platinum.loan_program_eligibility.listed_for_sale_cltv_cap

import rules_lib

def check(ctx):
    listed = ctx['SubjectProperty.listed_for_sale_last_6_months']
    listed_flag = rules_lib.flag(listed)
    if listed_flag is None:
        return rules_lib.unknown('SubjectProperty.listed_for_sale_last_6_months')
    if not listed_flag:
        return True

    cltv = ctx['LoanCore.cltv_percent']
    cltv_percent = rules_lib.percent(cltv, 'percent')
    if cltv_percent is None:
        return rules_lib.unknown('LoanCore.cltv_percent')
    return cltv_percent <= 65
