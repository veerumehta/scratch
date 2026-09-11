# Findings reported, weighed, and accepted as they stand.
#
# One `path :: slug` per line, exactly as the review keys them. `#` comments and blank lines are
# ignored. Every round appends this list to the review prompt; a finding named here is answered
# with a single `ACCEPTED: <key>` line instead of being reported and rated again.
#
# This is the closure for a finding with nothing to fix -- an extraction artifact in a vendored
# corpus nobody will re-run, a shape the author has decided to live with.
#
# It is NOT the only closure available to pack data. A `# TODO(slug)` comment in a .yaml file is
# read and honoured exactly as one in Python is: TODO(conductor-pipeline-from-yaml) in
# ci-spread-core/pack_manifest.yaml has been picked up under CHECKED: and not re-reported.
# Findings in pack YAML repeated because nobody wrote a TODO, not because the file cannot hold
# one. Prefer the TODO -- it sits at the row a future author edits, and it says "deferred, still
# intended" where this file says "weighed, not fixing". Use the review's own finding slug for it,
# so the two key spaces match (see CLAUDE.md section 7).
#
# Accept a finding here only after reading it. A `high` does not belong on this list: accepting one
# hides silent wrong data behind a green gate. Delete a line to put the finding back in scope.
#
# ── candidates from the 2026-09-09/11 rounds, commented out until you decide ──────────────
#
# Reported in 9 separate rounds, 05:28 through 14:30, never fixed. Two orphaned PDF line-wrap
# fragments (`schedule`, `available)`) in a vendored checklist, rated medium each time.
# plato/data/seed_packs/ci-spread-core/policies/checklist_ci.yaml :: orphaned-wrap-fragments
#
# Reported in 4 rounds (07:19, 08:22, 13:49, 21:11). DSCR-IO-MIN-LOAN's description promises a
# FICO 640 floor its condition does not encode.
# plato/data/seed_packs/dscr_core/policies/eligibility.yaml :: io-fico-floor-not-encoded
