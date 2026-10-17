# rule: acra-standard.prepayment_penalty_structures_and_state_restrictions.apply_transaction_minimum_terms.python
# origin: written from a job
# description: Python formalization of acra-standard.prepayment_penalty_structures_and_state_restrictions.apply_transaction_minimum_terms
# reads: vacant_property, loan_purpose, property_currently_listed_for_sale
# implements job: acra-standard.prepayment_penalty_structures_and_state_restrictions.apply_transaction_minimum_terms

import rules_lib

def check(ctx):
    vacant_property = ctx['vacant_property']
    loan_purpose = ctx['loan_purpose']
    property_currently_listed_for_sale = ctx['property_currently_listed_for_sale']

    missing = rules_lib.gaps(
        vacant_property=vacant_property,
        loan_purpose=loan_purpose,
        property_currently_listed_for_sale=property_currently_listed_for_sale,
    )
    if missing:
        return rules_lib.unknown(*missing)

    vacant = rules_lib.flag(vacant_property)
    listed = rules_lib.flag(property_currently_listed_for_sale)
    if vacant is None:
        return rules_lib.unknown('vacant_property')
    if listed is None:
        return rules_lib.unknown('property_currently_listed_for_sale')

    rate_term = rules_lib.same(
        loan_purpose,
        'rate & term refinance',
        'rate and term refinance',
        'rate-term refinance',
    )
    cash_out = rules_lib.same(
        loan_purpose,
        'cash-out refinance',
        'cash out refinance',
    )

    return True, {
        'vacant_property_rate_term_refinance': vacant and rate_term,
        'vacant_property_cash_out_refinance': vacant and cash_out,
        'property_listed_for_sale': listed,
    }
