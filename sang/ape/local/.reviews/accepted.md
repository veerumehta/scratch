# Findings reported, weighed, and accepted as they stand.
#
# Author: Virendra Mehta <virendra.mehta@jazzx.ai>
#
# One `path :: slug` per line, exactly as the review keys them. `#` comments and blank lines are
# ignored. Every round appends this list to the review prompt; a finding named here is answered
# with a single `ACCEPTED: <key>` line instead of being reported, rated and carried again.
#
# This is the closure a `TODO(...)` gives a defect in code. Pack YAML and other data have nowhere
# to put a TODO, and a finding the author declines in conversation has nowhere at all -- which is
# why the long-lived repeats in this directory are all in data files and low-rated notes.
#
# Accept a finding here only after reading it. A `high` does not belong on this list: accepting one
# hides silent wrong data behind a green gate. Delete a line to put the finding back in scope; if
# the code around an accepted finding gets worse than its slug describes, the review is instructed
# to raise that as new.

# ── already declined in code, recorded here so the round-over-round accounting stops carrying them

# `TODO(seed-pack-vendoring)` plus the pinning test. Five `source_schema: jaci.*` values and the
# metric/template bindings stay until the vendoring question is settled.
plato/data/seed_packs/ci-spread-core :: consumer-repo-names-shipped

# The file claims `CIConductor` loads it; the retraction lives in the manifest TODO rather than in
# the file. Inert either way -- nothing in japes reads it.
plato/data/seed_packs/ci-spread-core/pipelines.yaml :: inert-loader-claim

# ── low notes, reported and left, carried unchanged for several rounds ──────────────────────────

# `relaxed_only` inherits `environment_tier()`'s fail-open: a tier outside `_TIERS` reads as
# `local`. Closed by TODO(relaxed-only-fails-open-on-unknown-tier) on the gate itself, as this
# entry asked for -- CHECKED owns it now, so the line is gone rather than accepted.

# The backend sweep pins four unrecognised values and neither recognised one. Test-only; the gap it
# would catch is one spurious boot-log line.
tests/test_plato_packs_api.py :: backend-sweep-omits-recognised

# `TODO(local-wiring-build-test)` names three frozen globals where `wiring_local` defines two. The
# TODO overstates the leak rather than understating it, and nothing reads either global.
tests/test_plato_packs_api.py :: local-wiring-todo-overstates

# The effective-dating sweep uses 2099 and 2020, never the bound itself, so inclusivity at
# `effective_from`/`effective_to` is unpinned. `activation_block`/`is_executable` have no caller
# outside tests yet; revisit when the first one lands.
tests/test_policy_rule_activation.py :: activation-boundary-untested

# ── pack data: the producer is the consumer's, by design ────────────────────────────────────────

# "No producer" is true of this repo and is the architecture, not a gap: japes ships pack data and
# the consumer builds the policy context. jaci derives the field in its conductor --
# `bb.excess_availability / bb.total_availability` -- guarded so an absent borrowing base stays
# absent rather than reporting $0 and manufacturing a VIOLATED out of the dollar leg. The ontology
# comment beside the declaration states the same derivation. Inside the pack would be the wrong
# place for it.
plato/data/seed_packs/ci-spread-core/policies/conventions.yaml :: availability-pct-has-no-producer
