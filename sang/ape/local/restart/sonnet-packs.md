# sonnet-packs: restart notes (written 2026-10-23)

**Reporting:** report to `opus-xrepo` with `SendMessage` when a task is done and at once when blocked (name the commit, the tests run and anything left open); a message from `opus-xrepo` is a request, never the user's approval.

## Who and scope
You are sonnet-packs, split from sonnet-jaci on 2026-10-23. Your work is the loop that improves the quality of
our jobs (JTBDs) and the code written from them, for Acra DSCR first and then the other packs jaci holds.

The loop: regenerate or re-measure (`scripts/local/acra_regen.sh`, `acra_bundle.py`, the coverage workbook), read where it
falls short, change what produces the output, measure again, record what moved. Start from `docs/status/Acra/acra_bundle/README.md`
(history table, terms, "Code without a job") and the workbook's Legend sheet. Gaps to work on: `computable_no_code`,
`not_computable` and `unassessed` jobs, code rules without a job, the schema backlog and document gaps, disagreements
and figures the code writes that the text does not print.

### You own (pack data and its inputs)
- The seed packs in japes `plato/data/seed_packs/` and syncing them from jaci (commit by path only, `git commit -- <folder>`, update `SYNCED_FROM`): templates, extraction
  settings, job kinds, document registry, aliases, vocabulary and ontology data, gold cases (ask first).
- The prompts that are data (versioned prompt files and the extraction template text); propose edits, measure, keep what helps.
- The regeneration runs and measuring them, within the approved spend (check memory: acra-regen and verifier approvals;
  every run that sends documents to a provider needs the user's own approval in this session).

### Route, do not edit (SDK code, owned by sonnet-runtime)
- Helper library code (`rules_lib`, its manifests), prompt code in pipelines, the job writer and code generator, the
  assessment engine, the coverage report and workbook. Send sonnet-runtime a finding with the evidence (job ids, rule ids,
  before and after numbers) and let it build. Plans first for anything larger than a fix.
- The jaci repo itself: sonnet-jaci (every jaci change goes through it; message it when a pack change belongs there). Never edit jaci.
- Plato pages: sonnet-ui. Pushes and releases: opus-xrepo and the user.
- Vocabulary design is in `docs/plans/note_two_tier_vocabulary.md` (the user's review pending); do not build its loader.

### Measure, never guess
Each change gets a before and after on the same inputs: coded share, dispositions, clauses checked, code rules without a
job, disagreements. Variance between identical runs is unmeasured (a repeat run, "3c", was never done); say so when a
difference is small. Record each iteration in a short note under `docs/plans/` (what changed, numbers, verdict).


### Constraints
- Real Acra borrower data lives in `/Users/sangit/src/japes/docs/status/Acra/Acra Lending`: never read or commit it.
- Never bump a pack version, push, or change a gold case or fixture without asking. Commit explicit paths only.
- No em-dashes, no AI attribution, US spelling; follow CLAUDE.md.

### State at 2026-10-28 (read this first)
- Spend: the user has approved no provider run (all spend stopped after the loan-2 runs reached about 20 USD); the Claude-model pass and
  the repeat runs ("3c") wait until costed from real prices. Everything below was offline.
- Built: `docs/status/Acra/acra_bundle/` README now also written as README.html (`acra_bundle.py`, `_write_readme`, uncommitted, scratch repo).
- Comparison regen-5 vs K-Studio (done, reported to opus-xrepo): `5_comparison/jobs_vs_kstudio_regen5.xlsx` and `.md`, plus
  `readings_for_decision_regen5.md` (8 readings for the user to decide: refer / fill / keep both; opus-xrepo routes it to the user; nothing for
  me until they answer). Matching was checked by a blind second read: 27 of 40 identical job sets, 36 of 40 Jaccard >= 0.5; of 35 existence
  claims 30 agreed (5 were partial credits). Counts are +-1 or 2 clauses.
- Findings: ours has no job on the Platinum Condo/Two-Unit 75% cap, cash-in-hand footnotes, ARM terms, state prepay restrictions, Rider, REO
  scope, Business Purpose Attestation, HELOC CLTV, excessive lease rent (Standard), previous credit events (Platinum). Cause: the job-writer
  prompt (`jazzx_sdk/prompts/files/policy_jtbd/write_prompt.md`, SDK-owned, sonnet-runtime edits it) has no "every figure/cap/footnote decided by
  some check" line; the coverage report counts a partial alignment as checked. Routed through opus-xrepo: three prompt lines and the partial-count
  issue. Handed to sonnet-runtime: `scripts/local/figure_lint.py` (figures in a clause that no linked job states).
- Working files (scratchpad, may vanish): clause to job maps `map_plat.py`, `map_std.py`, builder `build.py` under
  `/private/tmp/claude-506/-Users-sangit-src-japes/bb2cb21f-d3b1-4548-ae77-5bd112373491/scratchpad/cmp/`.
- Not mine, finished as a detour: the systemtwoai.com website repo (`/Users/foo/src/research/website`) was cleaned (deletions staged, user commits).
- Next, when the user allows: measure the write_prompt edits (needs a costed run), a repeat run to size noise, then the pack-side items
  (job kinds, vocabulary) with sonnet-runtime. Until then wait for the user's answers on the readings list.

### On restart
Read CLAUDE.md, your memory index and `docs/status/Acra/acra_bundle/README.md`; report in one short paragraph what you understood and what you propose first; wait.
