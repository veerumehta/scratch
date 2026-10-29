# rule: acra-standard.loan_program_eligibility.eligible_property_type.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_program_eligibility.eligible_property_type
# reads: SubjectProperty.property_type, LoanCore.cltv_percent, LoanCore.loan_purpose, SubjectProperty.state
# implements job: acra-standard.loan_program_eligibility.eligible_property_type

import rules_lib

def check(ctx):
    property_type = ctx['SubjectProperty.property_type']
    cltv = ctx['LoanCore.cltv_percent']
    missing = rules_lib.gaps(property_type=property_type, cltv_percent=cltv)
    if missing:
        return rules_lib.unknown(*missing)

    kind = rules_lib.match(property_type, (
        'SFR', 'Townhome', 'PUD', 'Warrantable Condo',
        'Non-Warrantable Condo', 'Condotel / PUDtel', '2-4 Unit',
        'Manufactured Home',
    ))
    if kind is None:
        return False

    capped = {
        'Non-Warrantable Condo',
        'Condotel / PUDtel',
        '2-4 Unit',
        'Manufactured Home',
    }
    if kind in capped:
        if kind == '2-4 Unit':
            cap = 80
        else:
            purpose = ctx['LoanCore.loan_purpose']
            missing = rules_lib.gaps(loan_purpose=purpose)
            if missing:
                return rules_lib.unknown(*missing)
            purpose_kind = rules_lib.match(purpose, ('purchase', 'refi R/T', 'refi C/O'))
            if purpose_kind is None:
                return rules_lib.unknown('loan_purpose')

            caps = {
                'Non-Warrantable Condo': {'purchase': 80, 'refi R/T': 75, 'refi C/O': 75},
                'Condotel / PUDtel': {'purchase': 75, 'refi R/T': 70, 'refi C/O': 65},
                'Manufactured Home': {'purchase': 65, 'refi R/T': 60, 'refi C/O': 60},
            }
            cap = caps[kind][purpose_kind]

        if kind in ('Non-Warrantable Condo', 'Condotel / PUDtel'):
            state = ctx['SubjectProperty.state']
            missing = rules_lib.gaps(state=state)
            if missing:
                return rules_lib.unknown(*missing)
            if rules_lib.same(state, 'Florida', 'FL'):
                cap -= 5

        within_cap = rules_lib.band(cltv, [(cap, True)], above=False)
        if within_cap is None:
            return rules_lib.unknown('cltv_percent')
        if not within_cap:
            return False

    above_80 = rules_lib.band(cltv, [(80, False)], above=True)
    if above_80 is None:
        return rules_lib.unknown('cltv_percent')
    if above_80:
        allowed = {'SFR', 'Townhome', 'PUD'}
        if kind == 'Warrantable Condo':
            state = ctx['SubjectProperty.state']
            missing = rules_lib.gaps(state=state)
            if missing:
                return rules_lib.unknown(*missing)
            if rules_lib.same(state, 'Florida', 'FL'):
                return False
            allowed.add('Warrantable Condo')
        if kind not in allowed:
            return False

    return True
