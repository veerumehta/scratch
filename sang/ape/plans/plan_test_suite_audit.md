# Plan: audit the test suite (shrink, combine, speed up)

Author: opus-xrepo, 2026-10-16. Not started. Owner: a fresh session, plan first; start after v2.6.3 lands (v2.6.4).

## Why
The full suite takes about 15 minutes serially (CI's pytest 15 to 16 minutes, the pre-push hook runs it too), so a push
costs a quarter hour and invites `JAPES_SKIP_SUITE=1`. Pace of change is high, and tests written for earlier shapes
may now guard nothing.

## Measured today (static, 2026-10-16)
- 615 test files, about 8,100 test functions (about 8,900 collected with parametrization), about 150k lines of test
  code against about 164k lines of source (jazzx_sdk, plato, client, eval contracts).
- Biggest files: test_plato_packs_api 3,125 lines / 102 tests, test_plato_info_api 2,490 / 129, test_interactive_agent
  2,172 / 97, test_fabric_materialize 2,106 / 86.
- 384 `parametrize` decorators, 103 skip / xfail / importorskip markers, no pytest markers declared, no xdist, no
  timeout, one small `conftest.py` (6 functions).
- No durations data yet: the suite was running when this was written.

## Goals, in order of payoff
1. Wall time: run in parallel and tier it. Try `pytest-xdist` (`-n auto`) on the whole suite; what breaks is the
   shared-state tests (ports, `/tmp` dirs, env vars, sqlite files, module globals, the Postgres variants). Fix or mark
   those serial. Declare markers (`slow`, `postgres`, `live`) and run slow ones in CI only. Target: under 5 minutes
   locally, under 8 in CI.
2. Slowest tests: `pytest --durations=50` on a quiet machine; anything over 2 seconds is a candidate to speed up (a
   real sleep, a real subprocess, a rebuilt app per test) before it is a candidate to delete.
3. Redundant tests: use per-test coverage (`coverage run -m pytest --cov-context=test`, then `coverage json
   --show-contexts`) to find tests whose every covered line is also covered by another test and which assert nothing
   distinct. Candidates only; a person confirms each.
4. Combine: near-identical tests over one function with different literals become one parametrized test; repeated app
   or pack construction becomes a shared fixture in `conftest.py` (today almost nothing is shared there).
5. Dead tests: the 103 skip / xfail markers (does the reason still hold?), tests of removed or renamed behaviour that
   still pass because they assert on a stub, and tests whose subject is a docstring or a string literal.
6. Tests that cannot fail: assertions derived from the artifact under test (the contract-versus-behaviour rule in the
   project instructions), stubs that raise where production returns `None`, assertions on the stub's own return value.
   Fix these rather than delete them.

## Rules for deleting
- A test that guards a closed review finding stays: grep the finding slug in `.reviews/accepted.md`, `TODO(...)`
  comments and the CHANGELOG before removing it, and keep one assertion for it if the test is folded.
- No deletion without a reason in the commit (covered by test X, or subject removed in commit Y). One commit per
  theme, never mixed with source changes.
- Coverage of the package must not drop: record the number before and after (`jazzx_sdk`, `plato` separately).
- Per file, the suite passes before and after; a deleted test is first shown to be redundant by running without it.

## Output
A report in `plans/` listing each candidate with evidence (duration, coverage overlap, skip reason), then the commits.
Update the CI workflow (`tests.yml`) for the parallel run and the marker tiers, and the pre-push hook so a full run
is fast enough that skipping it is not tempting.

## Not in scope
Behaviour changes; the live-model smoke tests (kept as they are); jaci's tests.
