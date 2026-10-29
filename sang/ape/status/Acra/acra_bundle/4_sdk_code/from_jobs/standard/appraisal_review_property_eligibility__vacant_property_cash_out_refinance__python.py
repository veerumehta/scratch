# rule: acra-standard.appraisal_review_property_eligibility.vacant_property_cash_out_refinance.python
# origin: written from a job
# description: Python formalization of acra-standard.appraisal_review_property_eligibility.vacant_property_cash_out_refinance
# reads: CreditReport.representative_score, RatioSet.total_monthly_income_usd, RatioSet.total_monthly_obligation_usd, LoanCore.prepayment_penalty_structure, MortgageLoanInformation.is_interest_only, LoanCore.is_escrow_waived, RatioSet.reserves_months, LoanCore.total_loan_amount_usd, SubjectProperty.ownership_months, LoanCore.cltv_percent
# implements job: acra-standard.appraisal_review_property_eligibility.vacant_property_cash_out_refinance

import re
import rules_lib


def check(ctx):
    score = ctx['CreditReport.representative_score']
    income = ctx['RatioSet.total_monthly_income_usd']
    obligation = ctx['RatioSet.total_monthly_obligation_usd']
    ppp = ctx['LoanCore.prepayment_penalty_structure']
    interest_only = ctx['MortgageLoanInformation.is_interest_only']
    escrow_waived = ctx['LoanCore.is_escrow_waived']
    reserves = ctx['RatioSet.reserves_months']
    loan_amount = ctx['LoanCore.total_loan_amount_usd']
    ownership_months = ctx['SubjectProperty.ownership_months']

    missing = rules_lib.gaps(
        score=score, income=income, obligation=obligation, ppp=ppp,
        interest_only=interest_only, escrow_waived=escrow_waived,
        reserves=reserves, loan_amount=loan_amount,
        ownership_months=ownership_months,
    )
    if missing:
        return rules_lib.unknown(*missing)

    dscr = rules_lib.ratio(income, obligation)
    interest_only_flag = rules_lib.flag(interest_only)
    escrow_waived_flag = rules_lib.flag(escrow_waived)

    duration = re.search(r'(\d+(?:\.\d+)?)\s*(years?|yrs?|months?|mos?)', str(ppp), re.I)
    ppp_years = None
    if duration:
        ppp_years = float(duration.group(1))
        if duration.group(2).lower().startswith(('month', 'mo')):
            ppp_years /= 12

    cltv = None
    if loan_amount < 1500000:
        cltv = rules_lib.percent(ctx['LoanCore.cltv_percent'], 'percent')

    missing = rules_lib.gaps(
        dscr=dscr, interest_only=interest_only_flag,
        escrow_waived=escrow_waived_flag, ppp_years=ppp_years,
    )
    if loan_amount < 1500000 and cltv is None:
        missing += ('cltv_percent',)
    if missing:
        return rules_lib.unknown(*missing)

    passed = (
        score >= 700
        and dscr >= 1.15
        and ppp_years >= 3
        and not interest_only_flag
        and not escrow_waived_flag
        and reserves >= 6
        and ownership_months >= 15
        and (loan_amount >= 1500000 or cltv <= 60)
    )
    return passed, {
        'fico': score,
        'dscr': dscr,
        'ppp_years': ppp_years,
        'interest_only': interest_only_flag,
        'escrow_waived': escrow_waived_flag,
        'reserves_months': reserves,
        'loan_amount_usd': loan_amount,
        'cltv_percent': cltv,
        'ownership_months': ownership_months,
        'acra_confirmation_required_for_loan_amount': loan_amount >= 1500000,
        'acra_confirmation_required_for_ownership_measurement': True,
    }
