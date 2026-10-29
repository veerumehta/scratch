# rule: acra-standard.appraisal_review_property_eligibility.vacant_property_rate_and_term_refinance.python
# origin: written from a job
# description: Python formalization of acra-standard.appraisal_review_property_eligibility.vacant_property_rate_and_term_refinance
# reads: SubjectProperty.is_vacant, LoanCore.loan_purpose, CreditReport.representative_score, LoanCore.total_loan_amount_usd, LoanCore.cltv_percent, LoanCore.dscr_qualification_method, RatioSet.total_monthly_income_usd, RatioSet.total_monthly_obligation_usd, LoanCore.prepayment_penalty_structure, MortgageLoanInformation.is_interest_only, LoanCore.is_escrow_waived, RatioSet.reserves_months
# implements job: acra-standard.appraisal_review_property_eligibility.vacant_property_rate_and_term_refinance

import re
import rules_lib

def check(ctx):
    vacant = ctx['SubjectProperty.is_vacant']
    purpose = ctx['LoanCore.loan_purpose']
    score = ctx['CreditReport.representative_score']
    amount = ctx['LoanCore.total_loan_amount_usd']
    cltv = ctx['LoanCore.cltv_percent']
    method = ctx['LoanCore.dscr_qualification_method']
    income = ctx['RatioSet.total_monthly_income_usd']
    obligations = ctx['RatioSet.total_monthly_obligation_usd']
    penalty = ctx['LoanCore.prepayment_penalty_structure']
    interest_only = ctx['MortgageLoanInformation.is_interest_only']
    escrow_waived = ctx['LoanCore.is_escrow_waived']
    reserves = ctx['RatioSet.reserves_months']

    missing = rules_lib.gaps(
        vacant=vacant, purpose=purpose, score=score, amount=amount,
        cltv=cltv, method=method, income=income, obligations=obligations,
        penalty=penalty, interest_only=interest_only,
        escrow_waived=escrow_waived, reserves=reserves
    )
    if missing:
        return rules_lib.unknown(*missing)

    vacant_flag = rules_lib.flag(vacant)
    io_flag = rules_lib.flag(interest_only)
    escrow_flag = rules_lib.flag(escrow_waived)
    if vacant_flag is None or io_flag is None or escrow_flag is None:
        return rules_lib.unknown('vacant', 'interest_only', 'escrow_waived')

    if not vacant_flag or not rules_lib.same(
        purpose, 'rate and term refinance', 'rate/term refinance',
        'rate-term refinance', 'rate term refinance'
    ):
        return False
    if score < 700:
        return False

    if amount == 1000000 or amount == 2000000:
        return rules_lib.unknown('Acra confirmation (Q-10)')
    if amount < 1000000:
        max_cltv = 70
    elif amount < 2000000:
        max_cltv = 65
    else:
        return rules_lib.unknown('loan_amount_tier')
    cltv_value = rules_lib.percent(cltv, 'percent')
    if cltv_value is None:
        return rules_lib.unknown('cltv')
    if cltv_value > max_cltv:
        return False

    if rules_lib.same(method, 'DTI', 'debt-to-income', 'debt to income'):
        dti = rules_lib.ratio(obligations, income)
        if dti is None:
            return rules_lib.unknown('income', 'obligations')
        if dti > 0.40:
            return False
    elif rules_lib.same(method, 'DSCR', 'debt service coverage ratio'):
        return rules_lib.unknown('DSCR')
    else:
        return rules_lib.unknown('dscr_qualification_method')

    penalty_match = re.search(r'(\d+)\s*[- ]?\s*(?:years?|yrs?)', str(penalty), re.IGNORECASE)
    if penalty_match is None:
        return rules_lib.unknown('prepayment_penalty_structure')
    if int(penalty_match.group(1)) < 2:
        return False
    if io_flag or escrow_flag:
        return False
    if reserves < 6:
        return False
    return True
