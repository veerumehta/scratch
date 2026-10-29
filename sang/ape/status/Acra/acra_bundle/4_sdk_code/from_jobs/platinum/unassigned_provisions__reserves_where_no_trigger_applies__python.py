# rule: acra-platinum.unassigned_provisions.reserves_where_no_trigger_applies.python
# origin: written from a job
# description: Python formalization of acra-platinum.unassigned_provisions.reserves_where_no_trigger_applies
# reads: LoanCore.cltv_percent
# implements job: acra-platinum.unassigned_provisions.reserves_where_no_trigger_applies

import rules_lib

def check(ctx):
    cltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(cltv=cltv)
    if missing:
        return rules_lib.unknown(*missing)
    cltv = rules_lib.percent(cltv, 'percent')
    if cltv is None:
        return rules_lib.unknown('cltv')
    return cltv <= 75.00
