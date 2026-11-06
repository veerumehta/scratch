# 2.7.0 candidate list and sibling pass, 2026-11-06

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Read only. Sources: `plan_2_6_9_carried_work.md`, `plan_2_6_9_scope.md`, `note_deeper_sibling_and_symmetry_review_2026-11-05.md`, the four roadmap plans for 2.7.0 to 2.9.0, and
`scripts/local/sister_repo_activity.sh --no-fetch --days 4` plus `git log` over juno (JAPES_V2), policy-workbench, kernel-lab (dev). No diffs read for the sibling commits unless named.
Nothing run against a provider.

## 1. 2.7.0 candidates, grouped

A. Small and verified (from the 2026-11-05 note, section 6): 1a (15 lines), 3a (25 lines), drop the two legacy tenant keys (40 lines), guide stage 1 and 4b, the Kernel
   posture and mock parity (1b, 1c, 1e), the shared retry policy (1d), then the strict-posture umbrella (idea A).
B. Carried from the 2.6.9 plan: 14 thinking fill, 16 workbench ranks 7 to 9, 19 xdist, 21 `prefixItems`, 22 eval comparison drift, 23 mock KH parity, 24 DocIntel 429, 25 CI hygiene,
   26 chat two-stage answer, 28 visible failure when a trace is not written, 29 clear logs by range and type (scoping done), E18 git subdirectory deps (needs a main sha), common 0.4.0
   (needs a tag).
C. Bigger, already planned (verify first, written against 2.6.4): `plan_JAPES_2_7_0_EXPERT_SURFACE_AND_ANSWER_CONTRACT` (typed `ExpertAnswer` envelope, a Plato Expert route,
   multi-pack binding, caller visibility, authority-leakage scorer), then 2.7.1 knowledge loop, 2.8.0 supervision, 2.9.0 job-writer coverage and codability. The Expert surface is the
   one candidate that is a theme rather than a list; it needs a drift check against 2.6.9 before it is scoped.
D. Decisions needed first: tenancy model (string versus common's UUID), K gates in the publish path, PR #108 (Flipt in the LLM path), PR #101 (workspace claim home), Integration Hub
   or Notifications Hub first, KH bulk delete (wait for the regenerated client or wrap now).

## 2. Sibling pass (what changed, what helps)

- **juno (JAPES_V2)**: still `japes = { git, branch = "main" }` (pyproject.toml:60); one module imports `jazzx_sdk` (`app/core/jazzx_clients.py`). The recent commits are copilot and
  Integration Hub tool-editor fixes plus the AI Gateway behind a Flipt flag; no SDK adoption step from `plan_juno_sdk_adoption` has landed. Step 1 (pin and lock) is still the
  blocker, and it needs a main commit or tag to pin (2.6.9 is on plato only). The helpful SDK work is the same as before: a pinned main release, the fabric adapter, `local_fabric`.
- **policy-workbench**: pinned to japes rev f3101079 (floor 2.6.4), so it is behind by several versions. New there: "Reasoner Send: choose Evaluation Studio or a regular MACER run per
  Send" (#253). That is a second runner choice on a surface the SDK evaluation control plane could serve; read before ranking workbench item 16. Slices 4 to 8 of its migration plan are
  unbuilt.
- **assistant and jazzx-assistant**: no new SDK surface. The parent-team access fix (assistant #272) is service-side. jazzx-assistant now documents the flag-gated gateway vars (PR #108).
- **kernel-lab, codec-transformers-ann**: a ModernBERT classifier that predicts whether a CODEC verdict is Correct or Wrong (648 test rows; Correct precision 0.18, recall 0.98),
  plus a wording-sensitivity experiment over 11 text mappings. Exploratory by its own statement, test set reused, labels not rechecked. Not an input to job-to-code. It suggests one
  idea only: a cheap verdict-correctness prefilter for a reviewer queue, not worth building at 0.18 precision.
- **kernel-lab, codec-suite**: continued per-check generator prompts (16 for Liabilities, Identification, Taxes, Condo), data cards rebuilt with full column descriptions, reader rules
  (SSN fault line, last-four). This extends the worked-example-per-check and scoped-prompt ideas already in `note_kernel_lab_codegen_lessons_for_job_code`; nothing new in kind.
- **kernel-lab, jtbd-dependency-graph**: a repo with the Pulte JTBD v4.1 workbook and loan file timelines, not read. Its subject (job order and dependency) touches our JTBD to code
  path; read its design folder before 2.7.0 job-to-code scoping.

## 3. Not verified

Diffs of the sibling commits above; whether `jtbd-dependency-graph` is current; whether the 2.7.0 Expert plan still matches the code; local clones were pulled by the user, not fetched
here.
