You are sonnet-jaci. Two tasks, in order. Plan first for task 2; do not edit japes.

## 1. Verify dev against the pushed japes, then report

jaci `dev` is 5 commits ahead of `origin/dev` (c1cb2a0, 180182b, 563e1d4, 4e3e87a, 9c87267). jaci pins
`japes[server,documents] @ git+https://github.com/JazzX-LLC/japes.git@plato`, and `origin/plato` is now
`71961a88` (SDK 2.6.3, Plato and jazzx-plato-client 0.2.4), after being at 846d8bde (2.6.2).
- Reinstall jaci's venv from that pin (a fresh install from the git pin, not a local japes checkout), then run
  the jaci test suite. jaci's venv is not editable against japes.
- Report: pass or fail, and anything that broke because of 2.6.3 (typed conditions, carry rule, fold and
  data_mapping blocks, blueprint chain, upload cap 100 MB).
- Do not push. If it is green, say so and the user pushes.
- The untracked output/evaluations/plato_*.json files are run output: do not commit them; suggest a .gitignore line.

## 2. Where jaci still uses the SDK where jazzx-plato-client (or Plato's API) should be used

Read-only audit, then a plan document in jaci's docs/plans. Rules: jaci is configuration, the SDK holds the logic,
and Plato's reusable logic lives in the SDK with the client as the thin wire to Plato.
- List each call site where jaci imports jazzx_sdk (or a japes server module) to do something that a Plato
  route and a jazzx-plato-client method already cover: pack publish/activate/describe/whoami, case runs and
  documents, assess, extraction runs, evals, feedback, chat/skill invocation, traces, coverage, release report.
- For each: file:line, what it does, the client method that replaces it (check
  jazzx-plato-client in the japes checkout /Users/sangit/src/japes, not from memory), and whether behavior
  differs (tenant header, auth, idempotency, streaming).
- Separate three groups: (a) replace now, (b) must stay on the SDK (pack-local code, tool registration,
  in-process pipelines Plato does not host), (c) a client method or route is missing: name the gap with a
  repro. Group (c) goes to sonnet-runtime through opus-xrepo; do not edit japes.
- Keep it consumer-neutral where it touches japes asks: describe the gap, not jaci's name.
- No em-dashes. No AI attribution. Tolerant first. Be concise.

Send me (opus-xrepo) a short summary when the plan is written.
