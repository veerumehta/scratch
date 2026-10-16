# rule: acra-platinum.compliance_and_closing.cash_out_lease_verification.python
# origin: written from a job
# description: Python formalization of acra-platinum.compliance_and_closing.cash_out_lease_verification
# reads: LoanCore.loan_purpose, LoanCore.dscr_qualification_method, SubjectProperty.has_current_lease
# implements job: acra-platinum.compliance_and_closing.cash_out_lease_verification

def check(ctx):
    loan_purpose = ctx['LoanCore.loan_purpose']
    missing = rules_lib.gaps(loan_purpose=loan_purpose)
    if missing:
        return rules_lib.unknown(*missing)

    if not rules_lib.same(loan_purpose, 'Cash-Out Refinance'):
        return True

    dscr_method = ctx['LoanCore.dscr_qualification_method']
    missing = rules_lib.gaps(dscr_method=dscr_method)
    if missing:
        return rules_lib.unknown(*missing)

    has_current_lease = ctx['SubjectProperty.has_current_lease']
    missing = rules_lib.gaps(has_current_lease=has_current_lease)
    if missing:
        return rules_lib.unknown(*missing)

    lease_present = rules_lib.flag(has_current_lease)
    if lease_present is None:
        return rules_lib.unknown('has_current_lease')
    return lease_present
