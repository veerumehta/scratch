# jaci callers of fabric.graph delete_triple(s) and KH deletes

Author: Virendra Mehta

Written 2026-11-10 by sonnet-jaci for opus-xrepo. Read-only; no change in jaci. Searched `src/`, `tests/`, `scripts/`, `config/`, `ui/` and `app.py` for `delete_triple`, `delete_triples`, `fabric.graph` deletes, entity deletes, bulk deletes and any `.delete(` call.

## Callers

One production caller, one test double.

1. `src/jaci/capabilities/commercial_lending/pipeline.py:265`, `run_entity_extraction` (Phase 1):
   `await graph.delete_triples(subject=f"loan:{loan_id}", collection_id=..., ontology_id=...)`, then `add_entity` and one `add_triple` per lien.
   - **Relies on a silent failure?** Not on purpose. The call sits in a block marked best-effort, and its return value is never read.
   - **Today:** a failed delete returns False unseen; the code then writes the new triples, so a loan whose old triples could not be deleted ends up with the old and the new set side by side (duplicates, possibly stale liens).
   - **After the change:** `KnowledgeFabricError` is caught by the inner `except Exception` at line 285. The three write steps are skipped for that loan, the old triples stay as they were, and the message goes to `logger.debug` only, so nobody would see it at the default log level. `ctx.metadata["extracted_entities"]` is still set and the function still returns the entities, because the outer flow does not depend on the graph write. No test, caller or UI branch reads the graph back, so nothing else changes.
   - **Net:** safer (no duplicates), but the failure is as quiet as before. If the SDK now raises, I would raise that log line to `warning` in jaci, and that is a separate change I would only make on the user's yes.
2. `tests/unit/test_ci_entity_extraction.py:19`, the `_Graph` stub: `delete_triples` returns None and never raises. It keeps passing after the change. There is no test of the failing path; one would need a stub that raises and an assert that the entities are still returned and no `add_*` call happened.

## Not found

- No other `delete_triple`, `delete_triples`, `fabric.graph` delete, `delete_entity`/`delete_entities` or `.delete(` anywhere in code, tests, scripts or config.
- No KH client bulk delete, and no loop that deletes KH entities one by one, so there is nothing a bulk delete would replace. Cleanup of stale data in jaci is done by overwriting a case's own triples (the call above) or by the demo caches, not by deleting through the client.
- No code catches `KnowledgeFabricError` by name; jaci catches `Exception` around fabric writes.

## Follow-up (2026-11-10)

On the user's yes, the log at `pipeline.py:286` is now `logger.warning`, and `tests/unit/test_ci_entity_extraction.py` has a test where `delete_triples` raises (entities still returned, no writes, warning logged). Uncommitted.
