# rule: acra-platinum.appraisal_review_property_eligibility.listed_property_prepayment_penalty.python
# origin: written from a job
# description: Python formalization of acra-platinum.appraisal_review_property_eligibility.listed_property_prepayment_penalty
# reads: SubjectProperty.listed_for_sale_last_6_months, LoanCore.prepayment_penalty_structure
# implements job: acra-platinum.appraisal_review_property_eligibility.listed_property_prepayment_penalty

import re
import rules_lib


def check(ctx):
    listed = rules_lib.flag(ctx['SubjectProperty.listed_for_sale_last_6_months'])
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)
    if listed is False:
        return True

    penalty = ctx['LoanCore.prepayment_penalty_structure']
    missing = rules_lib.gaps(penalty=penalty)
    if missing:
        return rules_lib.unknown(*missing)

    if not isinstance(penalty, str):
        return rules_lib.unknown('prepayment_penalty_duration')

    match = re.search(r'(\d+(?:\.\d+)?)\s*(years?|yrs?|months?|mos?)\b', penalty, re.IGNORECASE)
    if match is None:
        return rules_lib.unknown('prepayment_penalty_duration')

    duration = float(match.group(1))
    unit = rules_lib.norm(match.group(2))
    if unit in ('year', 'years', 'yr', 'yrs'):
        return duration >= 3
    if unit in ('month', 'months', 'mo', 'mos'):
        return duration >= 36
    return rules_lib.unknown('prepayment_penalty_duration')
