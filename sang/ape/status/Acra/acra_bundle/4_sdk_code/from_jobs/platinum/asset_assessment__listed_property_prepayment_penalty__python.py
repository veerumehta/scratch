# rule: acra-platinum.asset_assessment.listed_property_prepayment_penalty.python
# origin: written from a job
# description: Python formalization of acra-platinum.asset_assessment.listed_property_prepayment_penalty
# reads: LoanCore.prepayment_penalty_structure, SubjectProperty.state
# implements job: acra-platinum.asset_assessment.listed_property_prepayment_penalty

import re
import rules_lib


def check(ctx):
    structure = ctx['LoanCore.prepayment_penalty_structure']
    missing = rules_lib.gaps(structure=structure)
    if missing:
        return rules_lib.unknown(*missing)

    match = re.search(r'(?<!\d)(\d+(?:\.\d+)?)\s*[- ]?\s*years?', str(structure), re.IGNORECASE)
    if match is None:
        return rules_lib.unknown('prepayment penalty term')

    years = float(match.group(1))
    if years >= 3:
        return (True, {'prepayment_penalty_term_years': years})

    state = ctx['SubjectProperty.state']
    missing = rules_lib.gaps(state=state)
    if missing:
        return rules_lib.unknown(*missing)

    state_text = rules_lib.norm(state)
    if isinstance(state_text, str) and 'does not allow prepayment penalties' in state_text:
        return (True, {'prepayment_penalty_term_years': years, 'state': state})
    if isinstance(state_text, str) and 'allows prepayment penalties' in state_text:
        return (False, {'prepayment_penalty_term_years': years, 'state': state})

    # A state name alone does not establish the state-law exception; no state-law
    # mapping is supplied by the clause.
    return rules_lib.unknown('whether state law allows prepayment penalties')
