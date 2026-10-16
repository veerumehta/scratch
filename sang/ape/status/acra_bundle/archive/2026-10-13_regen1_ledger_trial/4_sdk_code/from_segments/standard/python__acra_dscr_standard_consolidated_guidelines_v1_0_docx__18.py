# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.18
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶19
# reads: tradelines_meet_requirement

import rules_lib

def check(ctx):
    tradelines_meet_requirement = ctx['tradelines_meet_requirement']
    missing = rules_lib.gaps(tradelines_meet_requirement=tradelines_meet_requirement)
    if missing:
        return rules_lib.unknown(*missing)
    meets_requirement = rules_lib.flag(tradelines_meet_requirement)
    if meets_requirement is None:
        return rules_lib.unknown('tradelines_meet_requirement')
    return meets_requirement
