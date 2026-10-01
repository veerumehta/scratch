# Findings weighed and closed: one `path :: slug` per line.
# Plato's stream frames changed shape with the chat coordinator (terminal frame carries `value`,
# not `response`); nothing outside this repo reads them, and the CHANGELOG records the change.
plato/api/assistants.py :: stream-wire-shape-changed
# The mcp >= 2 start is tested against a stand-in because the venv carries mcp 1.28.1. The
# keyword-only host/port/transport_security were read from the 2.0.0, 2.1.1 and 2.2.0 sources
# (uv cache); a wrong name would raise TypeError at start, not fail silently.
tests/test_mcp_transport_security.py :: mcp2-stub-self-authored-signature
# The Z3 check withholds a whole item on a zero ratio denominator, like a missing fact; the
# evaluator withholds one rule. Both report CANNOT_DETERMINE with a reason, not a wrong verdict.
jazzx_sdk/formal/json_rules.py :: zero-denominator-withholds-item
# A non-numeric ratio operand reads as uncomputable; `assess` validates fact types first.
jazzx_sdk/fabric/canonical/condition_evaluator.py :: float-coercion-inside-uncomputable
# `declared_lifecycle` raises only ValueError; serving catches the same type.
plato/packs/check.py :: lifecycle-stage-can-raise
# Test-harness notes: engine disposal, a TTL stub, a claim-window constant.
tests/test_runs_duplicates.py :: db-store-never-disposed
tests/test_runs_slow_turn_not_reaped.py :: accepting-ttl-tied-to-default
tests/test_run_worker.py :: claim-window-assert-narrow
# Pack check runs without a runtime, so it assumes the fabric a deployed Plato has; a wiring
# built without one answers 409 at the first turn instead.
plato/packs/check.py :: pack-check-assumes-fabric
# 2.6.0 moved leaf modules under `jazzx_sdk.util` (`utc`, `digest`, `math.ratios`); the old paths
# are gone in an unreleased version, no sibling repo imports them, and the CHANGELOG marks it breaking.
jazzx_sdk/tools/ratio_evaluator.py :: old-paths-dropped-unshimmed
