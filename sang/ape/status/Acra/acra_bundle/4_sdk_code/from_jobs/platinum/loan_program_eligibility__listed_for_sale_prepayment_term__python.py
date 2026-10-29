# rule: acra-platinum.loan_program_eligibility.listed_for_sale_prepayment_term.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.listed_for_sale_prepayment_term
# reads: SubjectProperty.listed_for_sale_last_6_months, LoanCore.prepayment_penalty_structure
# implements job: acra-platinum.loan_program_eligibility.listed_for_sale_prepayment_term

import rules_lib

def check(ctx):
    listed = ctx['SubjectProperty.listed_for_sale_last_6_months']
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)

    listed_flag = rules_lib.flag(listed)
    if listed_flag is None:
        return rules_lib.unknown('SubjectProperty.listed_for_sale_last_6_months')
    if not listed_flag:
        return True

    structure = ctx['LoanCore.prepayment_penalty_structure']
    missing = rules_lib.gaps(structure=structure)
    if missing:
        return rules_lib.unknown(*missing)

    term = rules_lib.match(structure, (
        '5 Year',
        '5% Fixed (5% / 5% / 5% / 5% / 5%)',
        'Sequential Stepdown (5% / 4% / 3% / 2% / 1%)',
        '3 Year',
        '5% Fixed (5% / 5% / 5%)',
        '3% Fixed (3% / 3% / 3%)',
        '2 Year',
        '3% Fixed (3% / 3%)',
        '1 Year',
        '3% Fixed (3%)',
        'No Prepay',
    ))
    if term is None:
        return rules_lib.unknown('LoanCore.prepayment_penalty_structure')

    years = {
        '5 Year': 5,
        '5% Fixed (5% / 5% / 5% / 5% / 5%)': 5,
        'Sequential Stepdown (5% / 4% / 3% / 2% / 1%)': 5,
        '3 Year': 3,
        '5% Fixed (5% / 5% / 5%)': 3,
        '3% Fixed (3% / 3% / 3%)': 3,
        '2 Year': 2,
        '3% Fixed (3% / 3%)': 2,
        '1 Year': 1,
        '3% Fixed (3%)': 1,
        'No Prepay': 0,
    }[term]

    if term == 'No Prepay':
        return rules_lib.unknown('PLAT-7.8 state exception')
    return years >= 3
