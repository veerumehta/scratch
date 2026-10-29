# rule: acra-standard.identification_requirements.foreign_national_credit_reference.python
# origin: written from a job
# description: Python formalization of acra-standard.identification_requirements.foreign_national_credit_reference
# reads: CreditReport.tradelines_meet_requirement
# implements job: acra-standard.identification_requirements.foreign_national_credit_reference

import rules_lib

def check(ctx):
    tradelines = ctx['CreditReport.tradelines_meet_requirement']
    missing = rules_lib.gaps(tradelines=tradelines)
    if missing:
        return rules_lib.unknown(*missing)

    meets_us_report_alternative = rules_lib.flag(tradelines)
    if meets_us_report_alternative is None:
        return rules_lib.unknown('CreditReport.tradelines_meet_requirement')
    if meets_us_report_alternative:
        return True

    # The other three alternatives are not represented by readable case fields.
    return rules_lib.unknown(
        'international credit report',
        'original credit reference letter',
        'foreign banking relationship statement',
    )
