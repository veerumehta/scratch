# Document precedence on extracted fields (sonnet-runtime, 2026-10-17)

Source: sibling review (a reader that chooses which document wins a field). Today `document_ingest` with
`fills: input` keeps the first document read for a field and lists a later differing value under `docs.conflicts`.
Nothing says one document class is more authoritative than another.

## Design (consumer-neutral, pack data)
- `DocumentIngestStep.precedence: {field: [class, ...]}`; the key `"*"` is the default for a field with no entry.
  Each list orders document classes best first; a class names a registry type, alias or label and also stands for
  its descendants (as `required_classes` do). A class the list omits ranks after every listed one; a document with
  several classes ranks by its best.
- A value read from a better-ranked document replaces the one held (a value filled from an earlier document); a tie
  or a worse rank keeps the held value (today's behaviour). A value the case submitted is never replaced.
- Every disagreement is still recorded in `docs.conflicts`, now with `resolved_by: precedence` and `kept` (the
  document id whose value stands) when precedence decided it, so nothing is hidden (tolerant first). With no
  `precedence` declared the behaviour and the records are unchanged.
- Lint (publish-time step check): an entry naming a class the registry does not know, or a field the schema lacks,
  is a problem of the step.

## Not built
Document date as a second key: extracted items carry no document date today; adding one is a document-agent change
and its own plan.

## Tests (each fails on the old code)
Better class replaces a held value and records the conflict with `kept`; a tie keeps the first; a submitted value
survives; `*` default; descendants rank as their parent; no precedence leaves records as before; bad class named by
the check.
