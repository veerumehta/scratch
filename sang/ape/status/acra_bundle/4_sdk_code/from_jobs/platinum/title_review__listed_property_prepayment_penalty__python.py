# rule: acra-platinum.title_review.listed_property_prepayment_penalty.python
# origin: written from a job
# description: Python formalization of acra-platinum.title_review.listed_property_prepayment_penalty
# reads: LoanCore.prepayment_penalty_structure, SubjectProperty.state
# implements job: acra-platinum.title_review.listed_property_prepayment_penalty

import re
import rules_lib


def check(ctx):
    penalty = ctx['LoanCore.prepayment_penalty_structure']
    state = ctx['SubjectProperty.state']
    missing = rules_lib.gaps(penalty=penalty, state=state)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(penalty, 'no penalty', 'no prepayment penalty', 'none'):
        years = 0
    else:
        match = re.search(r'(?<![\d.])(\d+(?:\.\d+)?)\s*[- ]?\s*years?\b', str(penalty), re.IGNORECASE)
        if not match:
            return rules_lib.unknown('prepayment penalty duration')
        years = float(match.group(1))

    if years >= 3:
        return True
    if rules_lib.same(state, 'does not allow prepayment penalties', 'prohibits prepayment penalties'):
        return True
    if rules_lib.same(state, 'allows prepayment penalties', 'permits prepayment penalties'):
        return False
    return rules_lib.unknown('whether the state allows prepayment penalties')
