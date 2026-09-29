# Findings weighed and closed: one `path :: slug` per line.
# Plato's stream frames changed shape with the chat coordinator (terminal frame carries `value`,
# not `response`); nothing outside this repo reads them, and the CHANGELOG records the change.
plato/api/assistants.py :: stream-wire-shape-changed
