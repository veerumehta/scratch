# rule: acra-platinum.compliance_and_closing.listed_property_requirements.python
# origin: written from a job
# description: Python formalization of acra-platinum.compliance_and_closing.listed_property_requirements
# reads: SubjectProperty.listed_for_sale_last_6_months, MortgageLoanInformation.is_interest_only
# implements job: acra-platinum.compliance_and_closing.listed_property_requirements

def check(ctx):
    listed = ctx['SubjectProperty.listed_for_sale_last_6_months']
    missing = rules_lib.gaps(listed=listed)
    if missing:
        return rules_lib.unknown(*missing)
    listed = rules_lib.flag(listed)
    if listed is None:
        return rules_lib.unknown('listed_for_sale_last_6_months')
    if not listed:
        return True

    interest_only = ctx['MortgageLoanInformation.is_interest_only']
    missing = rules_lib.gaps(interest_only=interest_only)
    if missing:
        return rules_lib.unknown(*missing)
    interest_only = rules_lib.flag(interest_only)
    if interest_only is None:
        return rules_lib.unknown('is_interest_only')
    return not interest_only
