Build the blueprint narrowing chain, phases N1 and N2 first (see CLAUDE.md for the session state).

Read first:
- docs/plans/plan_blueprint_narrowing_chain.md (all of it; the four decisions are answered at its end).
- docs/status/done_JAPES_2_0_0_AUTHORITY_MATRIX_AND_EXECUTION_PROFILE.md (the authority objects already built).
- docs/plans/plan_BLUEPRINT_UMBRELLA_OVER_PACKS.md section 10 and section 9 (the blueprint, and the decisions the chain keeps).
- jazzx_sdk/pack/blueprint.py, blueprint_db.py, solution_view.py (what a blueprint is and how its page reads it);
  fabric/canonical/authority.py and profiles.py (AuthorityMatrixV2, SurfaceBinding, ClientOverlay, ExecutionProfile);
  authority/resolver.py (resolve_effective_autonomy, check_action, the narrowing semantics N2 repeats over a table).
- Grep docs/plans and docs/status for prior art before writing anything new.

State: branch v2.6.3 (SDK 2.6.3, Plato and the client 0.2.4). origin/plato is the v2.6.3 squash (71961a88); work
continues on v2.6.3 with commits there, no push, no version bump, no new branch. sonnet-ui owns the solution page
(plato/static/solution.html) and plans/plan_solution_view.md; message it for the header strip (N1) rather than
editing its files, unless it is idle with a clean tree. jaci changes go through sonnet-jaci (N5 is its data).

Do this, in order, one commit each, tests first (a test that fails on the old code, stubs shaped like production):
1. N1: the blueprint version names the chain artifacts its members declare (read from each member's manifest keys
   `authority_matrix:`, `surface_bindings:`, overlay, profile; no copies), and GET /blueprints/{id} returns a `chain`
   view (layer, member, artifact, summary: decision classes, action classes, ceilings), client contract included.
2. N2: the static non-widening check at blueprint publish and activation, per decision cell and action class
   (profile <= overlay <= surface binding <= matrix launch autonomy; human_only is L0 at every layer and not in scope of
   an Automation surface; an action class in scope at a surface exists in the matrix), the same semantics as
   resolve_effective_autonomy run over the whole table. Findings are warnings naming the layer that widened, recorded and
   surfaced (tolerant first); a pack-data `strict:` flag turns them into a refusal. No chain declared: unchanged behaviour.
Then stop and report; N3 (runtime), N4 (activation writes the Execution Profile), N5 and N6 follow in the plan's order,
each after the user has seen N1 and N2.

Rules: consumer-neutral (no client or repo names; settings as pack data); CHANGELOG entries with line counts in the
2.6.3 section; update the plan with a built section and deviations; family checked before each commit (grep for the
siblings of anything you change); no em-dashes, no AI attribution, new files carry the Author line; stage explicit paths
(other sessions' uncommitted work shares the tree); the user runs the one review at the end.

Open and not yours: Acra's case date; the browser check of the new pages; gemini-4-argon needs a context window and a
status before a card, and a re-price on 2026-12-01.
