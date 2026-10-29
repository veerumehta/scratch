# rule: acra-standard.income_stability_sufficiency_analysis.apply_scenario_specific_minimum_dscr.python
# origin: written from a job
# description: Python formalization of acra-standard.income_stability_sufficiency_analysis.apply_scenario_specific_minimum_dscr
# reads: LoanCore.cltv_percent, LoanCore.total_loan_amount_usd, CreditReport.score_count, CreditReport.tradelines_meet_requirement, Borrower.is_first_time_homebuyer, RatioSet.total_monthly_income_usd, RatioSet.total_monthly_obligation_usd, RatioSet.reserves_months, SubjectProperty.listed_for_sale_last_6_months, LoanCore.loan_purpose, SubjectProperty.is_mixed_use, SubjectProperty.occupancy_subtype, SubjectProperty.is_vacant
# implements job: acra-standard.income_stability_sufficiency_analysis.apply_scenario_specific_minimum_dscr

import rules_lib


def check(ctx):
    cltv = ctx['LoanCore.cltv_percent']
    loan_amount = ctx['LoanCore.total_loan_amount_usd']
    score_count = ctx['CreditReport.score_count']
    tradelines_raw = ctx['CreditReport.tradelines_meet_requirement']
    first_time_raw = ctx['Borrower.is_first_time_homebuyer']
    income = ctx['RatioSet.total_monthly_income_usd']
    obligation = ctx['RatioSet.total_monthly_obligation_usd']
    reserves = ctx['RatioSet.reserves_months']
    listed_raw = ctx['SubjectProperty.listed_for_sale_last_6_months']
    loan_purpose = ctx['LoanCore.loan_purpose']
    mixed_use_raw = ctx['SubjectProperty.is_mixed_use']
    occupancy_subtype = ctx['SubjectProperty.occupancy_subtype']
    vacant_raw = ctx['SubjectProperty.is_vacant']

    ltv = rules_lib.percent(cltv, 'percent')
    tradelines = rules_lib.flag(tradelines_raw)
    first_time = rules_lib.flag(first_time_raw)
    listed = rules_lib.flag(listed_raw)
    mixed_use = rules_lib.flag(mixed_use_raw)
    vacant = rules_lib.flag(vacant_raw)
    dscr = rules_lib.ratio(income, obligation)

    missing = rules_lib.gaps(
        cltv=ltv, loan_amount=loan_amount, score_count=score_count,
        tradelines=tradelines, first_time=first_time, income=income,
        obligation=obligation, dscr=dscr, reserves=reserves, listed=listed,
        loan_purpose=loan_purpose, mixed_use=mixed_use,
        occupancy_subtype=occupancy_subtype, vacant=vacant,
    )
    if missing:
        return rules_lib.unknown(*missing)

    if ltv > 80.00 and (dscr < 1.20 or reserves < 6):
        return False
    if loan_amount > 2000000 and dscr < 1.0:
        return False
    if (score_count <= 1 or not tradelines) and dscr < 1.1:
        return False
    if first_time and dscr < 1.150:
        return False
    if vacant and rules_lib.same(loan_purpose, 'rate & term refinance') and dscr < 1.000:
        return False
    if vacant and rules_lib.same(loan_purpose, 'cash-out refinance') and dscr < 1.15:
        return False
    if listed and dscr < 1.0:
        return False
    if (mixed_use or rules_lib.same(occupancy_subtype, 'adult care', 'assisted living')) and dscr < 1.2:
        return False
    return True
