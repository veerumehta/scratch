# Rerun on changed input facts (sonnet-runtime, 2026-10-17)

Today `RerunBasis` copies the followed run's record, items (by source file), outcomes, rejected cites and condition
watermark; only changed documents select work. A changed submitted fact reruns nothing selectively.

## Design
- Record the values each run used per fact (`RerunBasis.facts: {name: value}` from the followed run's input record,
  already in `record`) and diff on read: a rerun's submitted record against the basis. A changed or new value names
  its fact in `RerunBasis.changed_facts`.
- Dependencies: a rule's `reads` already name the facts it reads. A changed fact selects the rules that read it (and
  their dependent job sections) for re-evaluation; other outcomes carry over as for unchanged documents.
- A fact whose value could not be fetched (a refresh that failed) is not diffed: the rule is rerun and the
  adjudication prompt says the value could not be checked against the earlier run, never that it was unchanged.
- `full` still overrides (a different pack version carries nothing).
- Run summary lists `changed_facts` and the rules rerun because of them.
## Tests
Changed fact reruns exactly the rules reading it; unchanged record carries all outcomes; failed fetch reruns and says
so in the prompt; new pack version unchanged behaviour.
## Open
Whether derived metrics (computed from several facts) invalidate by their inputs: yes by `through_metrics`, which
already maps changed facts to metrics.
