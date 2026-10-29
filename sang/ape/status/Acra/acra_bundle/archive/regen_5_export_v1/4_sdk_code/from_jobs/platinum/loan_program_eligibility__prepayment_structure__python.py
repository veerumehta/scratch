# rule: acra-platinum.loan_program_eligibility.prepayment_structure.python
# origin: written from a job
# description: Python formalization of acra-platinum.loan_program_eligibility.prepayment_structure
# reads: LoanCore.prepayment_penalty_structure
# implements job: acra-platinum.loan_program_eligibility.prepayment_structure

import rules_lib


def check(ctx):
    structure = ctx['LoanCore.prepayment_penalty_structure']
    missing = rules_lib.gaps(structure=structure)
    if missing:
        return rules_lib.unknown(*missing)

    return rules_lib.same(
        structure,
        '5% Fixed (5% / 5% / 5% / 5% / 5%)',
        'Sequential Stepdown (5% / 4% / 3% / 2% / 1%)',
        '5% Fixed (5% / 5% / 5%)',
        '3% Fixed (3% / 3% / 3%)',
        '3% Fixed (3% / 3%)',
        '3% Fixed (3%)',
        'No Prepay',
    )
