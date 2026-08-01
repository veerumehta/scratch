# Status: PRD Demo Arc

Author: Virendra Mehta · Updated 2026-08-01
Repo: jaci · Plan: docs/plans/plan_JACI_CL_PRD_DEMO_ARC.md

**Phases 1, 2, 3, 4, 6 done — verified against real code and tests, not assumed from the plan's
own "LANDED" header or general impression. Phase 5 genuinely partial**: Act 1 real and runnable,
Acts 2-3 explicitly held in the UI itself, blocked on real fixture packages and two detectors that
don't exist yet (not a code gap someone forgot — a stated, honest placeholder). This is a
`status_` file, not a `done_` file, because of Phase 5.

## Verified done

- **Phase 1** — self-declared "LANDED (rev 2)" in the plan's own header; `_run_ci_spread_phase()`
  runs `CL_SPREAD_PIPELINE` and reaches session state. Confirmed unchanged.
- **Phase 2** — `render_pipeline_map()` (`ui/shared.py`) has both a `Status` column (driven from
  `events`, i.e. `vp.activity.*` from the current session's actual run) and a `Fills (output
  template)` column. Checked `step_fills()` (`template.py`) directly: it derives from
  `template_sections()`, itself read from `spread_template.yaml` — not a hand-written list, per
  the acceptance criterion's specific wording.
- **Phase 3** — the Target Template tab (`demo_page.py`, `tab_target`) reads
  `st.session_state.get("ci_spread_result"/"ci_spread_package")`, degrading to empty dicts when
  neither is set (renders with no run in session state), and layers in `spreader_template_trace`'s
  per-row match/confidence once a spread exists — one table, columns accrue, no re-render into a
  different table. The plan's own named duplicate ("the duplicate inline viewer" in the spreading
  tab) is confirmed retired — its removal is documented inline where it used to be.
- **Phase 4** — `tests/eval/trap_cases.py` / `tests/eval/test_ci_trap_cases.py`: 6 PRD traps, 4 guarded
  (2 via jaci `validation.py` detectors, 2 via japes' `construct_ltm`), 2 declared-but-unguarded
  with `xfail(strict=True)` naming the real reason. Matches the acceptance criterion exactly.
- **Phase 6** — `rows_this_decision_depends_on()` (`template.py`) is a real graph walk (metric ids
  → `scoa_leaves_for_metric` → canonical-key matching against template rows, never by label).
  `tests/unit/test_decision_dependency_marking.py` has both of the plan's specific acceptance
  tests: `test_yeti_marked_set_is_exactly_the_covenant_metrics_plus_their_binding_closure` and
  `test_renaming_a_template_row_label_moves_the_mark_not_breaks_it` — the rename-safety property
  is proven by test, not just claimed in a docstring.

## Genuinely partial — Phase 5 (the three acts)

Checked `demo_page.py`'s Acts tab directly. Act 1 is real: it runs `_run_ci_spread_phase`,
displays real metrics from the real run, and links to `case_01_yeti.json` (runs in CI via
`run_ci_eval.py`). Acts 2 and 3 are literally titled `"Act 2 — Three failure classes (held)"` and
`"Act 3 — The LTM column (held)"` in the UI, each with a caption naming exactly what's missing:

- **Act 2**: held on real fixture packages and a footnote-surfacing detector that doesn't exist
  yet (`trap_footnote_only_items.json` is declared-but-unguarded, consistent with Phase 4's own
  finding). The bad-debt add-back beat is already guarded and could run today.
- **Act 3**: held on real fixture packages and a cash-flow-gap detector that doesn't exist yet
  (`trap_cashflow_gap.json`, also declared-but-unguarded). `construct_ltm` itself is complete —
  the LTM sign-label beat could run today; the gap is UI + the missing detector, not the
  underlying period-construction logic, exactly as the plan itself predicted ("the largest build").

This matches the plan's own acceptance criterion honestly: "each act runs from the demo page...
and every beat corresponds to a gold case in CI" is true for Act 1 and the two already-guarded
sub-beats inside Acts 2-3; it is not yet true for the acts as a whole.

## Minor, not fixed (out of scope for a status write-up)

A few source comments in `template.py`/`demo_page.py` still name
`plan_JACI_CL_PRD_DEMO_ARC.md` directly (a convention this session moved away from for new code,
since docs/plans is gitignored and a comment naming a plan file points at something nobody else
will ever see). Pre-existing, not touched here since this pass is documentation, not a cleanup
sweep; flagged for whoever next edits those specific lines.

## Not yet decided

Whether Act 2/3's two missing detectors (footnote-surfacing, cash-flow-gap) and real fixture
packages are worth building now, or whether Phase 5 stays intentionally held. Not assumed either
way.
