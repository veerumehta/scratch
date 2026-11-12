# Findings weighed and closed without a fix. One `path :: slug` per line; lines starting with # are the reasoning.

# mock-latest-default-diverges (NOTE, low), 2026-11-11, v2.7.1 whole-range review.
# The in-memory MockKnowledgeHubClient lists every version when `latest` is not named, as it always did; the real hub defaults to
# latest=true. Kept on purpose: a caller that names nothing has always got every row from the mock, and changing the default would
# change every local-mode test that lists entities. Blast radius checked: the one fabric caller that depends on the difference,
# EntityStore._find_by_fingerprint, names latest=False explicitly; the HTTP mock app's facade path sends latest=true, so the two
# mock paths disagree only for a hand-built in-memory call that names nothing.
jazzx_sdk/clients/mocks.py :: mock-latest-default-diverges

# strict-view-skips-non-coroutines (NOTE, low), 2026-11-12, v2.7.2 whole-range review.
# StrictKnowledgeHubClient wraps coroutine methods only, as its docstring says. Blast radius checked: KnowledgeHubClient has no async
# generator method and only two plain methods (`generated_client`, `strict`), neither of which calls the hub, so no outage path
# escapes the strict flag today. Revisit when a streaming method is added.
jazzx_sdk/clients/knowledge_hub_client.py :: strict-view-skips-non-coroutines

# pack-dir-overcrowded (PLACEMENT, low), 2026-11-12, v2.7.2 whole-range review.
# alias_merge.py writes pack draft files and sits beside catalog_merge.py, its sibling and its imports' home. jazzx_sdk/pack/ already
# holds about 97 modules before this file; splitting the package is its own change (every importer moves), not part of this round.
# Blast radius checked: one importing module (`server/vocabulary_review.py`), two docstring mentions in `pack/`, and the tests.
jazzx_sdk/pack/alias_merge.py :: pack-dir-overcrowded
