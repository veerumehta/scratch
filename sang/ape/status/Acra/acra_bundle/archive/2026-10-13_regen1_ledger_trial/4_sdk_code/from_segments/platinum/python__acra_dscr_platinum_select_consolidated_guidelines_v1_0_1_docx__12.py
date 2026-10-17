# rule: acra-platinum.python.acra_dscr_platinum_select_consolidated_guidelines_v1_0_1_docx.12
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of segment ¶13
# reads: channel, gross_rental_income, pitia

import rules_lib


def check(ctx):
    channel = ctx['channel']
    gross_rental_income = ctx['gross_rental_income']
    pitia = ctx['pitia']

    missing = rules_lib.gaps(
        channel=channel,
        gross_rental_income=gross_rental_income,
        pitia=pitia,
    )
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(channel, 'Correspondent'):
        minimum = 1.2
    elif rules_lib.same(channel, 'Wholesale'):
        minimum = 1.0
    else:
        return rules_lib.unknown('channel')

    dscr = rules_lib.ratio(gross_rental_income, pitia)
    if dscr is None:
        return rules_lib.unknown('dscr')

    return dscr >= minimum, {'dscr': dscr, 'minimum': minimum}
