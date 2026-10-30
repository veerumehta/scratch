# The skeptic pass on the six candidate prompt lines (sonnet-runtime, 2026-10-30)

Done before any line was added, as `note_job_examples_skeptic_pass_and_measuring_run.md` section 1 asks. The user said "go ahead on the
writer prompt edit" (2026-10-30). Evidence is what the repo and sonnet-packs' comparison state (counts from `regen-5`, the Acra
comparison workbook); I did not re-derive per-job ids for each row, so the evidence column says where each claim comes from.

| # | Candidate | Lender-specific | Already covered | Conflicts | One check only | Code better | Verdict |
|---|---|---|---|---|---|---|---|
| W1 | Writer: "every figure, cap, list item and footnote in the source units is decided by a check of some job" | no | partly: the write prompt already asks which units each check decides, and coverage reports `cited_only` units; nothing tells the writer to leave none undecided | no | no: 8 published items without a job in regen-5 (cash-in-hand footnotes, HELOC CLTV, 75% condo cap...) across both programs, sonnet-packs' workbook "Gaps in ours" | the coverage report is the check; the line is the instruction it enforces | **ADDED** to `write_prompt.md` (1.3.0 to 1.4.0), one clause in the first sentence |
| W2 | Writer: "state every figure a check relies on in the check, not by reference to the printed table" | no | yes: the code prompt already says "take every figure and table from the source clause, as printed" | yes: stating every cell of a matrix in a check bloats the job and fights the matrix-granularity choice | n/a | the code writer reads the clause table | **REFUSED** |
| W3 | Writer: "a check already decided by another job in this section is not written again" | no | partly: `jtbd_fold` folds duplicates after the fact | yes: the writer is called once per section and sees no other job, so it cannot know; an instruction it cannot follow | n/a | yes: folding and the near-duplicate report | **REFUSED** |
| C1 | Code: "report every figure used in the dict" | no | yes: the prompt already says `(bool, dict)` to report values used | no | n/a | n/a | **MERGED** into that clause (`job_prompt.md` 1.1.0 to 1.2.0): "to report every value used (each figure the case is compared against, and the case's own value)"; no second line |
| C2 | Code: "a footnote or cap the clause prints is its own check" | no | yes: it is the writer's decision (W1), not the code writer's, which encodes the checks it is given | n/a | n/a | n/a | **REFUSED** (W1 carries it) |
| C3 | Code: "a cell not printed in the grid is unknown" | no | partly: "a case that does not state a field is undecided, never False" is about fields, not about a table with nothing printed | no: `rules_lib.band` already answers None where no tier is printed (checked) | no: the readings and the kernel-lab note both ask for it on matrix and cap jobs | the right home is the helper's own docstring, but a docstring edit is a library change (`render_api` shows the first paragraph, which the version manifest pins), and a library bump was not asked for | **ADDED as one sentence** in the existing paragraph of `job_prompt.md`, naming `band` |

Pinned by `tests/test_writer_prompt_lines.py` (the two kept lines, the merged clause, and that the three refused lines are not in the
prompts); `tests/test_policy_jtbd.py` pins the writer prompt's new version.

## Not measured yet
Whether the lines change what the models write is unmeasured. W1 acts on the job writer, so it is measured by a regeneration of the jobs:
the jtbd-step regen of both programs cost 0.047 USD on 2026-10-29 (regen-6), the aligned comparisons against v17 and v7 0.081 USD, so
about 0.13 USD for a before and after on this one line (the earlier "about 2 USD" figure was a full regen with code). C1 and C3 act on the
code writer: three 30-job arms (no lines, no lines again, with) are about 0.1 to 0.2 USD by the note's table. **No run is made without
the user's typed approval of a figure.**
