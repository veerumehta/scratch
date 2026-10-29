# rule: acra-standard.asset_assessment_assets_and_funds_to_close.funds_to_close_seasoning_trigger.python
# origin: written from a job
# description: Python formalization of acra-standard.asset_assessment_assets_and_funds_to_close.funds_to_close_seasoning_trigger
# reads: LoanCore.cltv_percent
# implements job: acra-standard.asset_assessment_assets_and_funds_to_close.funds_to_close_seasoning_trigger

import rules_lib

def check(ctx):
    cltv_raw = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv=cltv_raw)
    if missing:
        return rules_lib.unknown(*missing)

    cltv = rules_lib.percent(cltv_raw, 'percent')
    if cltv is None:
        return rules_lib.unknown('LoanCore.cltv_percent')

    # This settles only the stated CLTV threshold; transaction classification,
    # funds-to-close, and seasoning verification remain for reviewer assessment.
    return cltv > 70
