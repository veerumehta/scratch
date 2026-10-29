# rule: acra-standard.loan_program_eligibility.prepayment_penalty_minimum_terms.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_program_eligibility.prepayment_penalty_minimum_terms
# reads: LoanCore.loan_purpose, SubjectProperty.is_vacant, SubjectProperty.is_listed_for_sale, LoanCore.prepayment_penalty_structure
# implements job: acra-standard.loan_program_eligibility.prepayment_penalty_minimum_terms

import rules_lib

def check(ctx):
    purpose = ctx['LoanCore.loan_purpose']
    vacant_raw = ctx['SubjectProperty.is_vacant']
    listed_raw = ctx['SubjectProperty.is_listed_for_sale']
    missing = rules_lib.gaps(purpose=purpose, vacant_raw=vacant_raw, listed_raw=listed_raw)
    if missing:
        return rules_lib.unknown(*missing)

    vacant = rules_lib.flag(vacant_raw)
    listed = rules_lib.flag(listed_raw)
    if vacant is None or listed is None:
        return rules_lib.unknown(*(["SubjectProperty.is_vacant"] if vacant is None else []) + (["SubjectProperty.is_listed_for_sale"] if listed is None else []))

    minimum = 0
    if vacant and rules_lib.same(purpose, 'rate & term refinance'):
        minimum = max(minimum, 2)
    if vacant and rules_lib.same(purpose, 'cash-out refinance'):
        minimum = max(minimum, 3)
    if listed:
        minimum = max(minimum, 3)
    if minimum == 0:
        return True

    structure = ctx['LoanCore.prepayment_penalty_structure']
    missing = rules_lib.gaps(structure=structure)
    if missing:
        return rules_lib.unknown(*missing)
    term = rules_lib.match(structure, ('5 Year', '4 Year', '3 Year', '2 Year', '1 Year', 'No Prepay'))
    if term is None:
        return rules_lib.unknown('LoanCore.prepayment_penalty_structure')
    years = {'5 Year': 5, '4 Year': 4, '3 Year': 3, '2 Year': 2, '1 Year': 1, 'No Prepay': 0}[term]
    return years >= minimum
