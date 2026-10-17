# rule: acra-platinum.asset_assessment.rent_loss_insurance.python
# origin: written from a job
# description: Python formalization of acra-platinum.asset_assessment.rent_loss_insurance
# reads: LoanCore.cltv_percent
# implements job: acra-platinum.asset_assessment.rent_loss_insurance

import rules_lib

def check(ctx):
    cltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv=cltv)
    if missing:
        return rules_lib.unknown(*missing)

    exempt = rules_lib.band(cltv, [(70, True)], above=False)
    if exempt is None:
        return rules_lib.unknown('LoanCore.cltv_percent')
    if exempt:
        return True

    return rules_lib.unknown(
        'LTV',
        'subject property rents used to qualify',
        'rent loss insurance provided',
    )
