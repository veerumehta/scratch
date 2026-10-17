# rule: acra-platinum.entity_guarantor_and_trust_requirements.entity_eligibility_and_guarantees.python
# origin: written from a job
# description: Python formalization of acra-platinum.entity_guarantor_and_trust_requirements.entity_eligibility_and_guarantees
# reads: loan_purpose, occupancy_subtype, mixed_use
# implements job: acra-platinum.entity_guarantor_and_trust_requirements.entity_eligibility_and_guarantees

import rules_lib

def check(ctx):
    loan_purpose = ctx['loan_purpose']
    occupancy_subtype = ctx['occupancy_subtype']
    mixed_use = ctx['mixed_use']

    missing = rules_lib.gaps(
        loan_purpose=loan_purpose,
        occupancy_subtype=occupancy_subtype,
        mixed_use=mixed_use,
    )
    if missing:
        return rules_lib.unknown(*missing)

    mixed_use_flag = rules_lib.flag(mixed_use)
    if mixed_use_flag is None:
        return rules_lib.unknown('mixed_use')

    return (
        rules_lib.same(loan_purpose, 'business purpose')
        and rules_lib.same(occupancy_subtype, 'investment property')
        and not mixed_use_flag
    )
