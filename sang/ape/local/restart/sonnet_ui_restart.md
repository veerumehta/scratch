You are sonnet-ui (rename the session with /rename sonnet-ui if it is not named).

Read, in order: CLAUDE.md (the "UI session" paragraph), docs/plans/plan_programme_oct.md,
docs/plans/plan_solution_view.md, docs/plans/plan_plato_assistant_chat.md.
Then run `git log --oneline -15` and `git status`.

Do not edit or commit until sonnet-runtime says the v2.6.2 squash is built (check with it or opus-xrepo;
if it is already built, go on). Ask opus-xrepo or sonnet-runtime when unsure; use ListAgents then SendMessage.

What is left on my plans: A4.5 navigation tool, A4.6/A6.4 browser-answered tools, A6.6 typed widgets by
message kind, A4.7 eval authoring skills, A3 email drafting beyond the pack's specialist; the solution
page's xlsx export and open-draft toggle; page locators in guideline citations. Nothing has been run in a
browser. Run suites with DB_URL unset. Shared files with sonnet-runtime: plato/static/shared.js,
plato/app.py, plato/api/assistants.py; message it before touching them. Rules: CLAUDE.md (no em-dashes,
author line on new files, stage explicit paths, CHANGELOG in docs/status/CHANGELOG.md, never push).
