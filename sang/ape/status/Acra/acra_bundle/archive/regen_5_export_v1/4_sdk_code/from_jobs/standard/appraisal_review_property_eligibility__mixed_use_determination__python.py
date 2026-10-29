# rule: acra-standard.appraisal_review_property_eligibility.mixed_use_determination.python
# origin: written from a job
# description: Python formalization of acra-standard.appraisal_review_property_eligibility.mixed_use_determination
# reads: SubjectProperty.is_mixed_use
# implements job: acra-standard.appraisal_review_property_eligibility.mixed_use_determination

import rules_lib

def check(ctx):
    mixed_use = ctx['SubjectProperty.is_mixed_use']
    missing = rules_lib.gaps(mixed_use=mixed_use)
    if missing:
        return rules_lib.unknown(*missing)
    result = rules_lib.flag(mixed_use)
    if result is None:
        return rules_lib.unknown('SubjectProperty.is_mixed_use')
    return result
