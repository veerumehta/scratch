# rule: acra-standard.loan_program_eligibility.matrix_fico_and_cltv.python
# origin: written from a job
# description: Python formalization of acra-standard.loan_program_eligibility.matrix_fico_and_cltv
# reads: LoanCore.total_loan_amount_usd, CreditReport.representative_score, LoanCore.loan_purpose, LoanCore.cltv_percent
# implements job: acra-standard.loan_program_eligibility.matrix_fico_and_cltv

import decimal
import rules_lib


def check(ctx):
    amount = ctx['LoanCore.total_loan_amount_usd']
    score = ctx['CreditReport.representative_score']
    purpose = ctx['LoanCore.loan_purpose']
    cltv_percent = ctx['LoanCore.cltv_percent']

    missing = rules_lib.gaps(
        amount=amount,
        score=score,
        purpose=purpose,
        cltv_percent=cltv_percent,
    )
    if missing:
        return rules_lib.unknown(*missing)

    if rules_lib.same(purpose, 'purchase'):
        purpose_index = 0
    elif rules_lib.same(purpose, 'rate & term'):
        purpose_index = 1
    elif rules_lib.same(purpose, 'cash-out'):
        purpose_index = 2
    else:
        return rules_lib.unknown('loan_purpose')

    try:
        score = decimal.Decimal(str(score))
        cltv = decimal.Decimal(str(cltv_percent)) / decimal.Decimal(100)
    except (decimal.InvalidOperation, TypeError, ValueError):
        return rules_lib.unknown('representative_score', 'cltv_percent')

    # The excerpt prints the three tables, but does not print their loan-amount
    # tier labels. Keep each printed table separate rather than guessing which
    # loan amounts select it.
    tables = [
        [
            (600, (60, 60, 60)), (620, (65, 65, 65)),
            (640, (75, 70, 70)), (660, (80, 75, 75)),
            (680, (80, 75, 75)), (700, (80, 80, 75)),
            (720, (85, 80, 80)), (740, (85, 80, 80)),
            (760, (85, 80, 80)), (780, (85, 80, 80)),
        ],
        [
            (620, (65, None, None)), (640, (75, 65, 65)),
            (660, (75, 70, 65)), (680, (75, 70, 70)),
            (700, (75, 70, 70)), (720, (75, 75, 75)),
            (740, (75, 75, 75)), (760, (75, 75, 75)),
            (780, (75, 75, 75)),
        ],
        [
            (700, (70, 70, 65)), (720, (70, 70, 65)),
            (740, (70, 70, 65)), (760, (70, 70, 65)),
            (780, (70, 70, 65)),
        ],
    ]

    verdicts = []
    for rows in tables:
        limits = None
        for minimum_fico, row_limits in rows:
            if score >= minimum_fico:
                limits = row_limits
        if limits is None or limits[purpose_index] is None:
            verdicts.append(False)
        else:
            limit = decimal.Decimal(limits[purpose_index]) / decimal.Decimal(100)
            verdicts.append(cltv <= limit)

    if all(verdicts):
        return True
    if not any(verdicts):
        return False
    return rules_lib.unknown('applicable_matrix_tier')
