# Plato UI: runs, cost, evaluation, and the workbench gap

Status: live. U1-U3 built 2026-10-04 on `v2.6.1` (runs page at `/cases/ui`, with spend and queue; per-metric view on an experiment); U4-U8 open. Written 2026-10-04 on `v2.6.1`. Survey by an explorer over `plato/static`, `plato/api`,
the workbench frontend and `status/note_plato_vs_policy_workbench.md`; claims about what the UI has
were read from the pages. Companion to `plan_case_rerun.md` (U1 is that plan's P5).

## What exists

`ui/` in the repo is a stale extension-registry app (only `src/types`), not Plato's UI. Plato's UI is
four self-contained static pages in `plato/static` (dashboard, evaluation, packs, info), vanilla JS
over `fetch`, a placeholder-substituted shell (`nav_html`, `*_html` in `plato/api/info.py`, one route
each), no build step, no CDN. The workbench frontend is React + Vite and is the donor for ideas, not
code.

Built and with no UI: case runs (submit, stream, resume, chain, outcome, now rerun), queue and cost
stats, traces, the pack review lifecycle (reviews, diff, comments, lint-run triage), eval datasets
editing, baselines, custom scorers, and the new adjudication and split scorers.

## Decisions (judgment; the user stepped away)

1. **Stay on static pages.** A React shell is a separate, larger decision; none of U1-U6 needs it.
   U7 (workbench parity) is where it starts to hurt and is queued, not started.
2. **One page per working surface**, in the nav: Runs is new; cost and queue go on the dashboard;
   scorer drill-down goes on the evaluation page.
3. **Every control a route refuses is hidden by the server's own predicate**, as the other pages do.
4. **No new backend for U1-U6.** U8 (searchable logs and metrics) needs one and waits.

## Items, in build order

| # | Surface | Routes | Value |
|---|---|---|---|
| U1 | **Runs page**: a case's runs and chain, a run's steps, decision, adjudicated outcomes (verdict, conditions, cites, vote split), documents (split parts, unsure pages, missing, conflicts); stop, resume, outcome; **rerun** with rejected cites | `/runs`, `/runs/{id}`, `/stream`, `/chain`, `/resume`, `/outcome`, `/packs/{id}/runs` | high, both domains |
| U2 | **Cost and queue** on the runs page (the dashboard has no tenant; both routes need one) | `/cost-stats`, `/queue-stats` | S; intake spend |
| U3 | **Scorer breakdown** on an experiment: per-case metrics, the adjudication and split scorers' own numbers (false pass, fragile, status counts) | `/eval/experiments/{id}/cases`, `/scorers` | high |
| U4 | Dataset golden-case editor | `/eval/datasets/...` | M |
| U5 | Baseline trend and regression gate view | `/eval/baselines`, `/compare` | M |
| U6 | Custom scorer editor with a dry run | `/eval/scorers`, `/scorers/score` | M |
| U7 | Pack review inbox, diff, anchored comments, lint triage (workbench parity) | `/packs/reviews*`, `/drafts/{id}/diff|comments|lint-runs` | L; needs the React decision |
| U8 | Searchable logs and metrics | none today: `/logs` and `/metrics` are in-process rings | L; new backend first |

## Guards

- A test that every static page's inline script parses (`node --check`), since nothing else runs them.
- Each page's rendered route returns 200 with no `__PLACEHOLDER__` left and the nav entry present.
