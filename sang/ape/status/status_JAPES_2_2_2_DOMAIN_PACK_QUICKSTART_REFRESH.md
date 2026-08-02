# Status: Domain Pack Quickstart refresh to 2.2.2

Author: Virendra Mehta · Updated 2026-08-01
Repo: japes · Plan: docs/plans/plan_JAPES_2_2_2_DOMAIN_PACK_QUICKSTART_REFRESH.md

**Phase 1 (correctness pass) done. Phases 2-6 not started** — Phase 3 alone is described by the
plan itself as "the bulk of the work" (9 new subsections, each needing independent verification
against real code); left for a separate pass rather than rushed. Docs-only, no version bump, per
the plan's own header.

## Phase 1 — Correctness pass (done)

Every anchor the plan named, checked and fixed in `docs/DOMAIN_PACK_QUICKSTART.md`:

- Header architecture marker `1.8.x` → `2.2.x`, with the substrate sentence extended to name what
  landed since (authority/execution profiles, governed automation chassis, structured failures,
  pack composition, expression/finance modules) — one clause each, per the plan's own instruction
  not to let it become a feature list.
- Both root-`CHANGELOG.md` links repointed to `status/CHANGELOG.md` (sibling path, not `../`).
- Essential Reading items 8/10 (both pointed at `ARCHITECTURE.md`): kept item 8, replaced item 10
  with `docs/LOCAL_TESTING.md` + `docs/SETTINGS_CONFIGURATION.md` (verified both exist) — the
  "only if extending the platform itself" framing moved onto item 8 as the plan preferred.
- `poetry add jazzx-runtime-sdk` → `poetry add japes` (verified against `pyproject.toml`'s real
  `name = "japes"`).
- "Do the 7-step design" → "Do the design pass" (verified 8 real methodology steps, not 7).
- All five stale version markers (`v0.3.4+`, `v1.1.2+`, two `v1.4.1+`, `v1.9.0+`) dropped — each
  names a capability now long-baseline at 2.2.x, per the plan's own "old enough to be noise"
  reasoning. Left Step 8's "(optional)" wording itself alone (Phase 4's job, a retitle, not a
  version-marker removal).
- The stale `**Breaking Changes:**` list (stops at v1.4.1) replaced with a pointer to
  `status/CHANGELOG.md`, per the plan's own explicit preference ("this doc cannot stay a second
  changelog").
- `README.md`'s stale `**Current Version:** 2.1.3` line (and the "Previous" line below it)
  rewritten to 2.2.4, generic rather than re-enumerating every landed primitive (same "don't become
  a second changelog" reasoning) — plus, found while there and fixed as the same mechanical class
  of defect: **3 more broken root-`CHANGELOG.md` links elsewhere in `README.md`** (Version History
  section, x2) that the plan didn't name but sit two lines from the one it did — a small, deliberate
  scope extension since leaving 3 identical broken links right next to the one just fixed would
  have been a worse outcome than the small amount of extra care.

**Caveat worth stating plainly**: `docs/status/CHANGELOG.md` is itself a gitignored path (a
symlink into an external scratch directory per this repo's established convention — see
`.gitignore:87`, `docs/status*`). Every link now pointing there resolves correctly in this
environment but would 404 on a genuinely fresh clone with no local scratch directory. This isn't a
new defect introduced here — the plan's own grounding notes explicitly instruct repointing to
`status/CHANGELOG.md` twice, so this is the plan's accepted posture (a personal/working-copy
convention), not an oversight; flagging it once here rather than re-discovering it each time a doc
link review touches this file.

**Acceptance criteria verified**: no `1.8.x`, no `jazzx-runtime-sdk`, no `7-step` remain (grep-
confirmed, zero hits). Every relative link in `docs/DOMAIN_PACK_QUICKSTART.md` — including the
`README.md#anchor` fragments — checked against a real target file/header (not just the file
existing). `README.md`'s version now matches `jazzx_sdk/_version.py` (2.2.4). File went from
1521 to 1518 lines (net shrink, expected for a correctness-only pass with no new material).

## Deliberately not done (stated, not silently dropped)

- **Phase 2** (fabric surface rewrite against `platform_catalog.FABRIC_SURFACES`, the
  `resolve_mode_prompt`/`compose_mode_prompt` conflation fix) — not started. The stale `policy`
  fabric-store entry (`fabric.policy` does not exist; live accessor is `fabric.opa`) is still in the
  doc, unfixed — flagging explicitly since it's exactly the kind of "reader copies this and gets an
  `AttributeError`" defect Phase 1's own philosophy targets, but it's Phase 2's named scope, not
  Phase 1's, and doing it properly means rewriting a whole section per the plan's own instructions,
  not a one-line fix.
- **Phase 3** (the 9 new governance/execution-primitive subsections) — not started; the plan's own
  largest phase, deliberately deferred.
- **Phase 4** (assistant surface / worked-example section rewrite) — not started.
- **Phase 5** (folding in the Jazz Assistant Notion evidence) — not started; also the "Time to
  production-ready domain pack: 2-3 weeks" header line, which the plan itself explicitly defers to
  this phase, is still unchanged.
- **Phase 6** (full mechanical verification pass over the merged result) — not run as a distinct
  step; Phase 1's own acceptance criteria were verified directly above, but the file-length ceiling
  check (~1,400 lines) and full import-path verification are Phase 6's job once Phase 3 lands new
  material, not before.
