# rule: acra-standard.python.acra_dscr_standard_consolidated_guidelines_v1_0_docx.25
# origin: written from a guideline segment, proposal proposed
# description: Python formalization of Section 3.12 ¶4
# reads: entity_documents_complete

import rules_lib


def check(ctx):
    entity_documents_complete = ctx['entity_documents_complete']
    missing = rules_lib.gaps(entity_documents_complete=entity_documents_complete)
    if missing:
        return rules_lib.unknown(*missing)

    complete = rules_lib.flag(entity_documents_complete)
    if complete is None:
        return rules_lib.unknown('entity_documents_complete')
    return complete
