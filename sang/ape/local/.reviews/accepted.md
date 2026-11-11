# Findings weighed and closed without a fix. One `path :: slug` per line; lines starting with # are the reasoning.

# mock-latest-default-diverges (NOTE, low), 2026-11-11, v2.7.1 whole-range review.
# The in-memory MockKnowledgeHubClient lists every version when `latest` is not named, as it always did; the real hub defaults to
# latest=true. Kept on purpose: a caller that names nothing has always got every row from the mock, and changing the default would
# change every local-mode test that lists entities. Blast radius checked: the one fabric caller that depends on the difference,
# EntityStore._find_by_fingerprint, names latest=False explicitly; the HTTP mock app's facade path sends latest=true, so the two
# mock paths disagree only for a hand-built in-memory call that names nothing.
jazzx_sdk/clients/mocks.py :: mock-latest-default-diverges
