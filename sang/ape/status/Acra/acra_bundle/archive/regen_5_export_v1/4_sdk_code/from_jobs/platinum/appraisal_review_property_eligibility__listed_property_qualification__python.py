# rule: acra-platinum.appraisal_review_property_eligibility.listed_property_qualification.python
# origin: written from a job
# description: Python formalization of acra-platinum.appraisal_review_property_eligibility.listed_property_qualification
# reads: SubjectProperty.listed_for_sale_last_6_months, LoanCore.channel
# implements job: acra-platinum.appraisal_review_property_eligibility.listed_property_qualification

import rules_lib

def check(ctx):
    listed_raw = ctx['SubjectProperty.listed_for_sale_last_6_months']
    channel = ctx['LoanCore.channel']

    listed = rules_lib.flag(listed_raw)
    missing = rules_lib.gaps(listed=listed, channel=channel)
    if missing:
        return rules_lib.unknown(*missing)
    if not listed:
        return False
    if not rules_lib.same(channel, 'Wholesale', 'Correspondent'):
        return rules_lib.unknown('LoanCore.channel DSCR minimum')

    # The permitted fields contain neither a DSCR value nor a DTI value.
    # The DTI alternative is also identified as unresolved (Q-14).
    return rules_lib.unknown('DSCR value', 'DTI value (Q-14)')
