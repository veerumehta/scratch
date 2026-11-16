# How japes produces and runs generated code, against five kernel-lab fixer points (survey, 2026-11-15)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>. Read-only survey for the user; it decides nothing and absorbs nothing from kernel-lab.
Status marks: **[code]** read in the source this session; **[run]** observed by running something; **[doc]** taken from a docstring, a bundle
file or the brief without checking it against behavior. The five points are as the coordinator wrote them; kernel-lab's loop README
(`codec-suite/workflows/customers/revolution/tools/loop/README.md`) was only skimmed, not read through, and none of its code was read.

## 1. Where generated code comes from and runs

| Stage | Where | What it does |
|---|---|---|
| Write | `jazzx_sdk/pipelines/policy/code.py` (`PythonExtractor`, `JobCodeExtractor`, prompts in `jazzx_sdk/prompts/files/policy_code/`) | One structured model call per clause or job returns `_DraftCode` (source, reads, cases). **[code]** |
| Static gate | `jazzx_sdk/fabric/canonical/python_check.py` (`check_python_rule`) | AST check before anything runs: one `check(ctx)`, imports only `math decimal fractions statistics datetime re rules_lib`, no `exec eval open getattr` or dunders, context read only as `ctx['key']` with keys declared. Its own docstring: "a gate, not a sandbox". **[code]** |
| Own cases | `PythonExtractor._repaired_by_cases`, `pack/rule_cases.py` | The draft's own cases run on the executor; up to `CASE_REPAIR_ROUNDS = 2` repair calls send back expected-vs-got; a repair that fails the static check is not taken. Optional second call writes independent cases from the clause alone. Boundary probes add warnings. **[code]** |
| Execute | `fabric/canonical/local_executor.py` (`LocalPythonExecutor`) | Each run in a fresh child (`python -I -S`). Used by authoring (`server/authoring_context.py`, default `LocalPythonExecutor()`), assessment (`pack/assessment.py`), trials (`pack/rule_trial.py`), diagnosis, release report, custom scorers. **[code]** |
| Fix | `pack/rule_fix.py` (`fix_proposal`, modes `expand` and `redo`) | Regenerates a rule from a reviewer note plus failing trial cases as a new proposal that supersedes the old; never an edit in place; the id carries `~N`. **[code]** |
| Exact fixes | `pack/lint_fix.py` | Pure `(document) -> (document, edits, refusals)` fixers for lint findings with guards: parse before and after, only declared fields change, finding count must fall; a failing file is refused whole. Applies to pack YAML, not to generated Python. **[code]** |
| Library | `jazzx_sdk/rules/lib.py` (`rules_lib`, `LIB_VERSION` 1.1.2), `rules/api.py`, `rules/manifests/{1.1.0,1.1.1,1.1.2}.json` | 38 public helpers in 1.1.2 (18, 22, 38 by version). The writer's prompt gets `render_api()` (name, signature, first sentence of each docstring). A rule that imports the library records `lib_version`. **[code]** |
| Plato surface | `plato/api/packs.py`: `GET .../{version}/rules`, `.../rules/{rule_id}`, `rules/library`, `rules/library/compare`, `packs/{id}/rules/compare`; the Code page reads them | Read-only views of rules and library versions. Generation runs through the authoring run routes (`policy_extract_api.py`, `policy_extract_runs.py`). **[code]** |
| jaci | `scripts/extract_policy.py`, `scripts/import_jtbd_catalog.py` only | jaci has no code-generation or execution of its own; it calls the SDK. Not edited. **[code]** (grep of `src`, `scripts`, `app.py`) |

## 2. The five points

**(1) Typed tools over a workspace with exact-snippet edits, no shell.** Largely absent for generated code. [code] The writer is one
structured-output call, not an agent with a workspace; its only tool is `calculate` (a `CalculationLog`) for checking its cases' arithmetic,
when the template asks. Repair re-sends the whole draft with the mismatches and takes a whole new draft. There are no snippet edits to a rule.
What does exist is the shape on neighboring artifacts: `rule_fix` supersedes rather than edits, and `lint_fix` is exact, guarded and
refuses rather than guesses, on pack data. No shell is reachable by the writer because it has no tools beyond `calculate`.

**(2) A closed-path list of what judges the work, as pack data.** Not present as a list. [code] What judges a rule today: the static gate,
the draft's own cases and the independent cases (generated per run, stored with the proposal), boundary probes, the library's answers,
the trial's cases, and gold cases (pack data, changed only by the user). The gate and the library are SDK code; the cases are data, but
nothing stops a run from reading or regenerating the cases that judge it, because there is no declared set of paths the writer may not
touch (the writer cannot touch files at all, which is why this has not mattered). It becomes a question only if a workspace agent is added.

**(3) Isolation by copy, a hard USD, wall-clock and turn budget, free checks before paid.** Partly.
- Copy: pack work happens in a draft (`draft_db`), a copy of a published version; `publish_gate.refuse_moved_base` stops a stale publish. **[code]**
- USD: a run takes `budget_usd`; `CallMeter` refuses a call made once spend has reached it, and a call already running finishes. **[code]**
  (`agents/metering.py`, `server/policy_extract_runs.py`)
- Turns: no turn budget on the writer; the bounds are one static repair plus `CASE_REPAIR_ROUNDS = 2` case repairs per rule. **[code]**
- Wall clock: the executor has a 5 s limit per rule run; no wall-clock bound on a generation run that I found. **[code]** (absence of a hit
  in `code.py` and `policy_extract_runs.py`, not proven for every path)
- Free before paid: inside one draft the order is static check (free), own cases on the executor (free), then a paid repair call; so the
  paid step is reached only after the free ones fail. Lint gates (free) run separately from generation, not as a pre-spend gate on a run. **[code]**

**(4) A real sandbox for running generated code.** Present and substantial, not kernel-grade by its own account. **[code]** The child runs
`python -I -S` with `env={}`, a fresh temp working directory made read-only (`0o500`), its own session, and limits: CPU (timeout + 1 s),
`RLIMIT_FSIZE` 0, address space 256 MB (**not enforced on macOS**, the code says), open files 32, `RLIMIT_NPROC` 0, no core. On Linux it
unshares user and network namespaces. An audit hook refuses `socket.`, `subprocess.`, `os.`, `shutil.`, `ctypes.`, `resource.`, `signal.`,
and any open outside a read of the stdlib; a list of refused stdlib modules backs it. Result size is capped (1,000,000 bytes). The rules
library is delivered as source on the command line, so the repo is not mounted. Plato (`plato/wiring/contract.py`, `_KernelChecked`) runs a
boot-time `probe_isolation` in a worker thread and, in a deployed posture, refuses to run any rule if the network namespace or process
limit is not in effect, reporting why. **[code]** Gaps against the point as written: no seccomp or container boundary of its own, no
memory cap on macOS, and the network layer needs Linux user namespaces (the probe itself reports a default container seccomp profile
as a refusal). **[run]** `tests/test_local_executor.py`: 26 passed on this macOS host. The one error first reported was a teardown error of
`test_it_runs_in_a_deployed_posture` (an environment leak from importing `plato`, a test-fixture cause fixed afterward; it says nothing
about isolation, because that test patches the probe).

**(5) Provenance of engine and model per artifact.** Partial. [code] A rule records `lib_version` when it imports the library, `origin`
and a header comment (`# origin: written from a job`, `# implements job: ...`), and the proposal records `created_by` (a user). A
proposal's `origin` is the chat turn. The model and prompt version are **not** on the rule or proposal; they are in the bundle's
`bundle.json` per stage per bundle (for regen-5: `flex_gpt-6-luna`, provider `openai (agents sdk)`, prompt versions per stage), so the
provenance is per export, not per artifact. **[doc]** (read from `bundle.json`; the pipeline that writes it was not read.)

## 3. How much of the code is library reference (measured)

Scope: the only generated Python in reach is the Acra regen-5 export, `docs/status/Acra/acra_bundle/4_sdk_code/from_jobs/{standard,platinum}`
(97 rules; bundle `library_version` 1.1.1, SDK 2.6.6). The seed packs hold no generated Python (`grep` of `acra_dscr_policy/policies`), and the
Revolution and Pulte sets have no generated code yet (R3 is on hold). So "per job set" is these two sets. **[run]** by a script over the
files (scratchpad, not kept in the repo): per rule, non-blank lines excluding `import` and `def` lines; a library line is one that calls
`rules_lib.`.

| Set | Rules | Code lines | Lines calling `rules_lib` | Of those, the missing-data guard (`gaps`, `unknown`) | Lines calling a helper that decides something | Rules with no deciding helper |
|---|---|---|---|---|---|---|
| Standard | 50 | 1,054 | 380 (36%) | 233 | 147 (14% of code lines) | 2 |
| Platinum Select | 47 | 585 | 237 (41%) | 165 | 72 (12%) | 2 |

- The guard idiom the prompt prescribes (read each field, `missing = rules_lib.gaps(...)`, `return rules_lib.unknown(*missing)`) is most of
  the library use: 398 of 617 helper calls. Counting it, about 40% of lines are references; not counting it, 12 to 14%.
- Only **11 of the 22 helpers in 1.1.1** are called at all (10 in each set): `unknown`, `gaps`, `same`, `flag`, `percent`, `band`, `ratio`, `match`,
  `close`, `known`, and `norm` (once, Platinum only). `at_least`, `at_most`, `in_set` and `within` (added in 1.1.1, so available to this export) are never
  called.
- The remaining logic is written inline: 72 of 97 rules contain a comparison (43 `<=`, 30 `>=`, 25 `<`, 7 `>`, 9 `==`), with **96 numeric
  literals in those comparisons**, the figures the policy text states (e.g. `cltv <= 80`), written into code. The median rule is 13 code
  lines, 30 rules have 8 or fewer, the longest has 76.
- 1.1.2 (current) added 16 helpers (`average`, `edate`, `eomonth`, `highest`, `latest`, `lowest`, `total`, `round_*`, `same_org`,
  `same_person`, `pair_off`, `uncovered_months`, `names`, `explains`); this export predates it, so their use is unmeasured. A regen on 1.1.2
  would show whether they are picked up.

## 4. Where generation still happens, why, and what blocks more reuse

Generation happens for every job with a computable check: the model decides which fields to read, writes the comparison, and writes the
literals. Why the share of library references is low once the guard is excluded:

1. **The thresholds are the content.** The numbers (80, 700, 120 days) come from the guideline text. The code is a comparison against a
   figure; no library function can hold the figure. Today the figure lives in the generated source, not in pack data. [measured above]
2. **Comparisons are written inline though helpers exist.** `at_least` and `at_most` return None for an unknown (the library's rule: the
   unknown is None, not False), but the prompt already has the model guard unknowns with `gaps`/`unknown` first, so the helpers add
   nothing the writer sees a need for. The prompt text (`job_prompt.md`) names only the guard idiom and `import rules_lib` plus the
   rendered API; it never mentions `at_least`, `at_most` or `band` by use. [code] Whether that wording is the cause is **not measured**:
   no regen with a changed prompt was compared.
3. **A one-line API summary is what the writer gets.** `render_api()` gives name, signature and a one-sentence summary. **[code]** Whether
   a worked example per helper would be used is unmeasured. (A job-kind example mechanism exists: `JobExamples`, first attempt only.)
4. **Domain gaps.** Rules in the 1.1.2 additions (dates, sums, rounding, matching names across documents) exist because earlier exports
   wrote that logic by hand; the effect is unmeasured until a regen.
5. **No path from a repeated shape to a helper.** Nothing counts which inline patterns recur across rules and proposes a helper; the
   library grows by hand (`LIB_VERSION` bumps, manifests). A scan like the one above could feed that; it is not built.

Candidates the data suggests, for the user to weigh (none started): (a) move thresholds to pack data (job parameters) so a rule reads
`params['cltv_cap']` and the figure is reviewable and changeable without regenerating code, which would cut the literals and make rules
shorter; (b) a `compare(value, op, threshold)`-style helper or a stronger prompt rule to use `at_least`/`at_most`/`within`, measured by
the same script on a regen; (c) a recurrence report over generated rules to pick the next helpers. Each needs the runtime session and, for
a regen, the user's typed approval.

## 5. What was verified and what was not

- Verified by reading source: the pipeline stages, the static gate's rules, the executor's limits and hook, the Plato boot probe, the
  budget meter's behavior, `rule_fix` and `lint_fix` semantics, the library's versions and helper counts, jaci's lack of its own paths.
- Verified by running: the reuse numbers (script over 97 files), the helper counts per library version, 26 executor tests passing (the teardown error was a fixture leak, fixed).
- Not verified: that the executor's network and process isolation holds on this host (the one erroring test); anything about kernel-lab's
  code; whether the bundle's `bundle.json` is written per artifact anywhere I did not look; how often the Code page is used; the 1.1.2
  helpers' uptake; a wall-clock bound on whole generation runs in every path.
