# Sibling repo survey, 2026-09-02

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Read-only survey via `scripts/local/sister_repo_activity.sh --days 4`, across juno, eval-service,
macer, jaci, kernel, client-api, knowledge_hub, jazzx-assistant and assistant. Four days rather than
fourteen, because the 14-day window was surveyed on 2026-09-01 and its findings are recorded
separately.

## The finding worth acting on

**japes' mock Knowledge Hub validates entities on create and not on update, and real KH validates
both.**

Found by following jazzx-assistant `336bb1e` ("Added ontology validation on mock kh update entity
endpoint", 2026-09-02). Two things fell out of that one commit.

**1. The gap is in japes too.** `MockKnowledgeHubClient._validate_entity` exists and is called from
`create_entity` (`jazzx_sdk/clients/mocks.py:1058`). The `update_entity` body calls it nowhere. So a
mock-backed test can write a valid entity and then update it into a shape its ontology forbids, and
nothing objects. Real KH does object -- `update_entity_with_validation` is the function name, and
KH's own `93ea215` recently tightened *which* ontology it validates against ("json_value validated
against the pre-update schema -> now validated against the effective ontology_id/entity_type"). The
mock is weaker than the thing it stands in for, which is the one property a mock must not have.

Worth fixing in japes. It is a small change -- the validation helper already exists -- and it makes
every mock-backed suite in every consuming repo slightly more honest.

**2. jazzx-assistant maintains its own mock KH.** The change landed in
`src/mock_knowledge_hub/app.py` and `store.py` -- a hand-rolled implementation, in a repository that
depends on japes, where `jazzx_sdk/server/mock_knowledge_hub_app.py` exists and whose docstring
describes it as "the reusable *every pack rebuilds an HTTP mock Knowledge Hub* primitive". That is
precisely the duplication it was written to end, and it is still happening.

This is an adoption question rather than a defect: either japes' mock is missing something theirs
has, or nobody told them it exists. The validation gap above suggests at least partly the former.
Worth asking rather than assuming.

## Other movement, and why it is not actionable here

**juno `774c0c52` -- "redact secrets from inline evidence + total-size guard".** Two-pass redaction:
by key name in dict-shaped fields (`password`/`token`/`api_key`/`secret`/`authorization`/`cookie`/
`ssn`, case- and style-insensitive, recursing into nested structures) and by value shape in free
text. japes' `failures.py` already has the second half -- `redact_secrets` scans text, `redact_fields`
takes explicit paths, `redact_code_blocks` handles fenced content -- but japes takes a **caller-supplied
path list**, where juno infers from key names and recurses.

The prior art matters: japes' redaction primitives were themselves generalized from a juno guardrail
bug. So this is the second time juno has been ahead on this, which is the pattern the standing
"watch for japes evolution opportunities" lens exists to catch. **Not** proposing to lift it yet:
key-name inference is a heuristic, and a heuristic that redacts the wrong field is a data-loss bug
rather than a leak. Worth a proper look when something in japes actually needs to redact a structure
whose shape it does not know.

**knowledge_hub `970c606` -- scope-mismatch 403 in `read_entities_minimal`** (now merged to main;
it was on a branch at the last survey). japes' KH client should be checked for whether it surfaces
403 distinctly from other failures on that path. Not verified in this pass.

**macer `8216d0f3` -- "refactor(jtbd): group condition resolvers into a package".** Convergent with
the root-module grouping just done in japes. No action; noting it because two repositories reaching
the same conclusion in the same week is mild evidence the instinct was right.

**eval-service, kernel, assistant, jaci** -- test coverage, merges and feature work with no japes
surface. jaci has not moved since `ac68dd8` (v0.20.6, 2026-08-30).

## Suggested order

1. Fix the mock KH update-validation gap in japes. Small, self-contained, and it strengthens every
   consumer's tests.
2. Ask jazzx-assistant why they have their own mock. The answer determines whether japes' version
   needs work or advertising.
3. Leave the juno redaction question until japes has the need. Note it, do not lift it.
