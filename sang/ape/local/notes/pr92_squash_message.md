v2.6.3 (plato v0.2.4): typed conditions, the job writer folds duplicates, blueprint chain, SDK-typed KernelClient

SDK 2.6.3, Plato and jazzx-plato-client 0.2.4.

Job writing
- The job writer folds duplicate jobs across sections and reads missing data as the catalog field it names;
  folding keeps a distinct requirement and what a folded job knew.
- A condition is open once or resolved, never both; conditions have stable ids, a tied vote keeps every vote's
  conditions, a batched answer's conditions are validated and the model is asked again.
- Typed conditions are visible: step output, runs page, scorer, quickstart. A condition can name one subject of the case.
- Adjudication evidence is scoped per segment; guideline citations name their page.

Solution view and Plato pages
- A blueprint carries its narrowing chain (checked for widening) and the solution page draws it.
- The solution page reads the open draft and downloads as a workbook; the extraction page refreshes while a run goes.
- Plato's pages send X-Trace-Id; the authoring assistant opens Plato pages; browser-answered questions and rule cards;
  email drafts from a case's open conditions.

SDK and client
- KernelClient takes SDK types for an agent invocation and can start one or stream it; it works without a token.
- Client methods for the solution workbook and a draft's rules.
- Plato closes its grounding sessions at shutdown.

Security and housekeeping
- mcp floor 1.30.0 and Mako 1.4.3 in the lock (Dependabot); three code-scanning alerts closed (numeric-suffix regex,
  trial copy path confinement, solution page blueprint id).
- The pre-push model check runs on a bare interpreter; model pricing re-verified on 2026-10-16.
