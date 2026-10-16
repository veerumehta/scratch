# rule: acra-platinum.income_stability_sufficiency_analysis.channel_minimum_dscr.python
# origin: written from a job
# description: Python formalization of acra-platinum.income_stability_sufficiency_analysis.channel_minimum_dscr
# reads: LoanCore.channel
# implements job: acra-platinum.income_stability_sufficiency_analysis.channel_minimum_dscr

import rules_lib

def check(ctx):
    channel = ctx['LoanCore.channel']
    missing = rules_lib.gaps(channel=channel)
    if missing:
        return rules_lib.unknown(*missing)
    return rules_lib.same(channel, 'Correspondent') or rules_lib.same(channel, 'Wholesale')
