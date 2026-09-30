# Findings weighed and closed: one `path :: slug` per line.
# Plato's stream frames changed shape with the chat coordinator (terminal frame carries `value`,
# not `response`); nothing outside this repo reads them, and the CHANGELOG records the change.
plato/api/assistants.py :: stream-wire-shape-changed
# The mcp >= 2 start is tested against a stand-in because the venv carries mcp 1.28.1. The
# keyword-only host/port/transport_security were read from the 2.0.0, 2.1.1 and 2.2.0 sources
# (uv cache); a wrong name would raise TypeError at start, not fail silently.
tests/test_mcp_transport_security.py :: mcp2-stub-self-authored-signature
