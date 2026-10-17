# rule: acra-platinum.asset_assessment.listed_property_ltv_and_cltv.python
# origin: written from a job
# description: Python formalization of acra-platinum.asset_assessment.listed_property_ltv_and_cltv
# reads: SubjectProperty.listed_for_sale_last_6_months, LoanCore.cltv_percent
# implements job: acra-platinum.asset_assessment.listed_property_ltv_and_cltv

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

    cltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv=cltv)
    if missing:
        return rules_lib.unknown(*missing)

    result = rules_lib.band(cltv, [(65, True)], above=False)
    if result is None:
        return rules_lib.unknown('LoanCore.cltv_percent')
    return result
