# Worked examples for the code writer: the skeptic pass, and the measuring run's cost (sonnet-runtime, 2026-10-28)

Built (SDK half, no spend): `{example}` slot in `policy_code/job_prompt.md` and `regenerate.md` (both 1.1.0), the loader
(`pipelines/policy/job_examples.py`: never fatal, label + content digest + kinds + problems), the per-kind pick in
`PythonExtractor.formalize`, the template field, and `job_examples` in `bundle.json`. The examples themselves are pack data
(`job_examples.yaml`), written by opus-xrepo from reviewed Acra rules; none exists yet.

## 1. The skeptic pass (the process, run before any new line is added to a prompt)
For each candidate line, write one row; a line is added only when every answer is "no":
1. **Lender-specific?** Does it name Acra, a program or a figure that belongs to one guideline? (Then it is pack data, not SDK prompt.)
2. **Already covered?** Is it a restatement of a line in `instructions.md`, `job_prompt.md`, `regenerate.md`, `write_prompt.md` or a
   lint that already refuses the failure (`rule_unguarded_read`, unprinted figures, type problems)? Merge into the existing line.
3. **Conflicts?** Does it contradict a line, a job set (K-Studio's or ours) or an example in the pack? Run it against the 25 to 30
   jobs of the measuring run, read, before it goes in.
4. **One check only?** Does it fix a failure seen on a single job? (Then a lint or the job's own repair feedback, not a prompt line.)
5. **Runtime only?** Is it enforced better by code (a validator, a helper) than by a sentence? (Prefer the code.)
Each row records the evidence: the job id and the failure it came from. The candidate lines on the table now (from sonnet-packs
and the kernel-lab note): "every figure, cap, list item and footnote in the source units is decided by a check of some job",
"state every figure a check relies on in the check, not by reference to the printed table", "a check already decided by another
job in this section is not written again" (writer, `write_prompt.md`); "report every figure used in the dict", "a footnote or cap
the clause prints is its own check", "a cell not printed in the grid is unknown" (code, `job_prompt.md`). Not yet run through
the pass; that is the first step of the measuring run's preparation.

## 2. The measuring run
**Question:** do worked examples (and, separately, the new prompt lines) make the generated code state the printed figures, get
matrix cells right, answer unknown not False on a missing fact, and pass its own cases, against a no-example arm?
**Subset:** ~25 to 30 jobs of one program (matrix, aggregate cap and footnote jobs), same models, same job set.
**Arms:** A1 no example, A2 no example again (the noise floor; a difference smaller than A1 against A2 is not a finding), B with the
per-kind examples. Optional C: B plus the new prompt lines, only after the skeptic pass.
**Measured:** rules whose code states every figure the clause prints (the unprinted-figure and figure lint counts, both
directions), matrix cells correct against a hand-read grid, unknown-versus-False on a case missing a field, the rule's own cases
passing, code without a job, calls and cost per job. Also scan the generated code for constants that appear in the example and not
in the job's clause (an example that anchors the model on its figures).

**Cost, from the price table (estimate, not measured; model `flex_gpt-6-luna`):**

| | tokens in / out | per call |
|---|---|---|
| one code call, no example | 3,000 / 2,000 | 0.0007 USD |
| with an example (+3,000 in) | 6,000 / 2,000 | 0.0008 USD |
| a job's worst path: first call, static-check fix, one case repair (3 calls, example only on the first) | | about 0.002 USD |

A 30-job arm is therefore about 0.02 to 0.06 USD; three arms (A1, A2, B) about 0.1 to 0.2 USD. At the non-flex `gpt-6-luna` price
(twice) and with the independent-cases call on, the upper bound is about 0.5 USD for all arms. The earlier 5b measurement was
about 0.25 USD, consistent. The job writer is not re-run (the job set is fixed), so the writer-prompt lines are measured
separately by a regeneration of the jobs (the Acra regen is the larger cost, about 2 USD, as measured before); not part of this run.
**Needs the user's approval before any call**: not run, nothing spent.

## 2.6.7: record the examples fingerprint in the SDK

`JobExamples.fingerprint()` is recorded only by the host (the Acra bundle script); the SDK keeps no record. Candidate: a field on the step provenance of a `python_jobs` run, beside the model and prompt versions, with a test that two different `job_examples.yaml` give different recorded fingerprints. Builds with the several-examples-per-kind (shape) work; no code on v2.6.6.
