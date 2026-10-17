# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.37
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶16
# reads: loan_amount, fico, loan_purpose, cltv_pct

import rules_lib


def check(ctx):
    loan_amount = ctx['loan_amount']
    fico = ctx['fico']
    loan_purpose = ctx['loan_purpose']
    cltv_pct = ctx['cltv_pct']

    missing = rules_lib.gaps(
        loan_amount=loan_amount,
        fico=fico,
        loan_purpose=loan_purpose,
        cltv_pct=cltv_pct,
    )
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(loan_purpose, 'purchase'):
        purpose_index = 0
    elif rules_lib.same(loan_purpose, 'rate & term'):
        purpose_index = 1
    elif rules_lib.same(loan_purpose, 'cash-out'):
        purpose_index = 2
    else:
        return False

    if loan_amount <= 1500000:
        cap = rules_lib.band(
            fico,
            [(600, (60, 60, 60)), (619, (65, 65, 65)),
             (639, (75, 75, 75)), (659, (80, 70, 70)),
             (699, (80, 75, 75)), (719, (80, 80, 75))],
            above=(85, 80, 80),
        )
    elif 1500001 <= loan_amount <= 2000000:
        cap = rules_lib.band(
            fico,
            [(620, (65, None, None)), (639, (75, 65, 65)),
             (659, (75, 70, 65)), (679, (75, 70, 70)),
             (719, (75, 75, 75))],
            above=(75, 75, 75),
        )
    elif 2000001 <= loan_amount <= 3000000:
        cap = (70, 70, 65) if fico >= 700 else None
    else:
        cap = None

    if cap is None:
        return False

    max_cltv = cap[purpose_index]
    if max_cltv is None:
        return False

    if loan_amount < 200000:
        small_loan_cap = (80, 75, 75)[purpose_index]
        max_cltv = min(max_cltv, small_loan_cap)

    return (cltv_pct <= max_cltv, {'max_cltv_pct': max_cltv})
