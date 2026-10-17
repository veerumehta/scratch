# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.35
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶21
# reads: delayed_financing, loan_amount, channel, fico, cltv_pct

import rules_lib

def check(ctx):
    delayed_financing = ctx['delayed_financing']
    loan_amount = ctx['loan_amount']
    channel = ctx['channel']
    fico = ctx['fico']
    cltv_pct = ctx['cltv_pct']

    missing = rules_lib.gaps(
        delayed_financing=delayed_financing,
        loan_amount=loan_amount,
        channel=channel,
        fico=fico,
        cltv_pct=cltv_pct,
    )
    if missing:
        return rules_lib.unknown(*missing)

    delayed = rules_lib.flag(delayed_financing)
    if delayed is None:
        return rules_lib.unknown('delayed_financing')
    if delayed and loan_amount > 1500000:
        return False

    if (rules_lib.same(channel, 'correspondent')
            and 700 <= fico <= 719
            and cltv_pct > 60):
        return False

    return True
