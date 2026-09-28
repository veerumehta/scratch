# Findings weighed and lived with
#
# One `path :: slug` per line, with the reason. `#` comments and blank lines are ignored.
# For findings with nothing to fix. Anything still intended gets a TODO(slug) in the file instead.

# `plato` is a service package, not a consumer library: its internal modules are not a public
# import surface, and no use of this path was found in any sibling checkout. Four identical lifts
# in the same release (seed, oidc, pack draft, model overlay) removed the old path without a
# forwarding shim; a shim only here would contradict that and leave a module whose only job is to
# forward. `docs/DEPLOYMENT_ENV.md` was updated to the new path.
jazzx_sdk/server/prefix.py :: documented-prefix-import-removed

# A deliberate breaking change in an unreleased version, authorised before it was made. Nine
# paths moved: oidc, net_safety, path_safety, sanitize, templating, odata (-> safety/), bpmn
# (-> closure/), portfolio and reconcile (-> aggregate/). `jazzx_sdk.closure` and `jazzx_sdk.ui`
# kept their paths deliberately, which is why they are not in that list.
#
# Verified rather than assumed: no import of any moved path exists in jaci, juno, kernel,
# assistant, knowledge-hub, macer or common. juno imports one SDK symbol in total
# (`client_layer.ClientLayer`); jaci's only affected module is `jazzx_sdk.ui`, whose path did not
# move. Nine forwarding shims would leave the root exactly as cluttered as the change set out to
# fix, so the old paths are gone rather than deprecated.
jazzx_sdk/aggregate/reconcile.py :: removed-public-module-paths

# A `Feedback` whose rating is outside [0, 1] validates locally and is refused with a 422 by the
# host, which `FeedbackApiSink` raises as `httpx.HTTPError`: loud, with the server's reason. Bounding
# `Feedback.rating` itself would change a long-standing public model other producers build.
jazzx_sdk/evaluation/feedback_sink.py :: rating-bound-asymmetry

# `added` on `…/to-dataset` is a status flag; the stored data is right either way. Two concurrent
# adds of the same feedback case can both report `added: true`. Closing it means changing
# `add_feedback_case`'s return shape for a message, not for data.
jazzx_sdk/server/feedback_api.py :: added-flag-second-read

# A JTBD `sequence` above 2**53 would lose precision through `float`. Sequences are small ordinals
# in every JTBDSet this reads; `int` first would add a branch for a value no artifact carries.
jazzx_sdk/pipelines/jtbdset.py :: integer-routed-through-float

# A draft row stored before paths were normalized under a spelling like `a//b` is not reachable by
# that spelling now. Drafts are written from the pack page's own file list and from `rel_path`s the
# SDK builds, neither of which produces such a spelling; a row that did would still publish, since
# the archive member name is the stored path.
jazzx_sdk/pack/draft_db.py :: normalization-orphans-old-rows

# The output-type sweep skips a module that fails to import. It runs in every CI extras set, and
# modules behind an optional extra (mlflow, azure) cannot import where that extra is absent; their
# import is covered by the extras' own suites. The sweep asserts it checked at least one type.
tests/test_policy_extraction_prompts.py :: cwd-relative-sweep-vacuous

# Publish refuses a pack carrying `conductor.pipeline` or `policies.registry`, which blocks jaci's
# `ci-spread-core` and `cl_of_core` as they stand. Deliberate (Plato domain-pack runtime plan, D2):
# Plato never imports Python a pack names, and a pack relying on a pointer cannot run there. Those
# packs reach Plato through the conductor-kind path (Phase 2's `conductor_pipeline`), not as-is.
plato/packs/check.py :: pointer-refusal-blocks-known-packs
