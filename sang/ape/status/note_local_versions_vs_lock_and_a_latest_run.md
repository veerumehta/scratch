# Local package versions, the lock, and a "latest" run

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: a note, no work queued. Decide later whether the problem is big enough to act on (2026-11-17).

## Question

Should the local environment always equal `poetry.lock` (what CI installs), so that a problem found and fixed by a bump re-syncs it?

## What happened that raised it

- The primary checkout's venv was 9 packages behind the lock and 39 ahead (packaging 26.3 vs 25.0, sqlalchemy 2.1.9 vs 2.0.44, starlette 1.10 vs 1.3.1, multidict 7.2 vs 6.9, wrapt 2.5 vs 1.17, uvicorn 0.54 vs 0.34).
- Ahead hid nothing and found something: `activation.py` used an empty `SpecifierSet` as a PEP 440 validity probe, which packaging 26 accepts for any string, so the "(not a PEP 440 version)" note vanished. CI (lock, packaging 25.0) was green; a consumer on packaging 26 would have seen the wrong message. Fixed in code (`is_pack_version`), not by a lock bump.
- Separate cause of the three `0.3.3 vs 0.3.4` failures: the venv's editable `.pth` files pointed at another worktree. Unrelated to versions of third-party packages.

## Position

1. Day to day: venv equals the lock, so a local failure reproduces CI and a local pass means CI passes. Never behind (`scripts/local/raise_behind_pins.sh` fixes behind; `pre_push_check.sh` step 2 flags behind and summarizes ahead).
2. japes is a library and its consumers (jaci, jazzx-assistant, macer, assistant) do not use our lock: they resolve fresh against our `>=` floors with no caps. Testing only at the lock pins therefore misses defects that appear on newer releases. A deliberate "ahead" pass is the second matrix.
3. A bug in our code under a newer version is fixed in our code so it works across the range; bumping the lock alone would leave the floor in `pyproject.toml` permitting the broken combination for consumers. Bump the lock for a needed fix, a security advisory or a floor change.

## What is missing (not built)

- No CI job tests the latest resolved versions (tests.yml installs from the lock only).
- No lowest-versions run (`uv --resolution lowest-direct`) to check the floors.
- Dependabot is disabled (no `.github/dependabot.yml`; the user disabled it temporarily).

## If it becomes worth doing

A scheduled (weekly, non-blocking) workflow with two jobs: latest resolved versions, and lowest-direct. Report failures; do not gate merges. Before a release, run the latest pass once by hand in a throwaway environment.
