# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.17
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶18
# reads: citizenship_type, fico, cltv_pct, loan_purpose, loan_amount

import rules_lib

def check(ctx):
    citizenship_type = ctx['citizenship_type']
    missing = rules_lib.gaps(citizenship_type=citizenship_type)
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(citizenship_type, 'permanent resident'):
        return rules_lib.unknown('unavailable PRA ID and SSA card / SSA-89 evidence')

    if rules_lib.same(citizenship_type, 'non-permanent resident'):
        return rules_lib.unknown('unavailable proof of legal residency', 'Q-21 limit interpretation')

    if rules_lib.same(citizenship_type, 'foreign national'):
        fico = ctx['fico']
        cltv_pct = ctx['cltv_pct']
        loan_purpose = ctx['loan_purpose']
        missing = rules_lib.gaps(fico=fico, cltv_pct=cltv_pct, loan_purpose=loan_purpose)
        if missing:
            return rules_lib.unknown(*missing)
        if not rules_lib.same(loan_purpose, 'purchase'):
            if not rules_lib.same(loan_purpose, 'refinance'):
                return rules_lib.unknown('loan_purpose')
            cltv_limit = 65
        else:
            cltv_limit = 70
        return (fico == 700 and cltv_pct <= cltv_limit, {
            'fico': fico,
            'required_fico': 700,
            'cltv_pct': cltv_pct,
            'cltv_limit_pct': cltv_limit,
            'loan_purpose': loan_purpose,
        })

    if rules_lib.same(citizenship_type, 'itin'):
        loan_amount = ctx['loan_amount']
        fico = ctx['fico']
        cltv_pct = ctx['cltv_pct']
        loan_purpose = ctx['loan_purpose']
        missing = rules_lib.gaps(
            loan_amount=loan_amount,
            fico=fico,
            cltv_pct=cltv_pct,
            loan_purpose=loan_purpose,
        )
        if missing:
            return rules_lib.unknown(*missing)
        if not rules_lib.same(loan_purpose, 'purchase'):
            if not rules_lib.same(loan_purpose, 'refinance'):
                return rules_lib.unknown('loan_purpose')
            purpose_index = 1
        else:
            purpose_index = 0

        if fico < 640:
            return (False, {'loan_amount': loan_amount, 'fico': fico, 'cltv_pct': cltv_pct})
        tier_limits = rules_lib.band(
            fico,
            [(659, (60, 60)), (699, (65, 60)), (700, (70, 65))],
            above=None,
        )
        if tier_limits is None:
            return rules_lib.unknown('FICO tier')
        cltv_limit = tier_limits[purpose_index]
        return (loan_amount <= 1000000 and cltv_pct <= cltv_limit, {
            'loan_amount': loan_amount,
            'loan_amount_limit': 1000000,
            'fico': fico,
            'cltv_pct': cltv_pct,
            'cltv_limit_pct': cltv_limit,
            'loan_purpose': loan_purpose,
        })

    if rules_lib.same(citizenship_type, 'us citizen'):
        return True

    return False
