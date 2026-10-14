# Blueprint as the narrowing chain: wiring the authority objects japes already has into the solution

Plan, opus-xrepo, 2026-10-14. Status: written, for the user's decisions (section 7). Owner when approved:
sonnet-runtime (SDK, Plato runtime), sonnet-ui (pages), sonnet-jaci (Acra pack data).

## 1. Why

`SBP-00` (Solution Blueprint overview, IIF v1.5) defines a solution as a narrowing chain:

```
Domain Pack -> Surface Binding Annex -> Certified Client Overlay -> Execution Profile
```

Each layer only narrows the one above it. The chain is also built from:

- an autonomy ladder (L0-L4), earned per decision cell;
- four gate families (Conformance, Launch, Promotion, Recertification);
- four surface types (Assistant, Workspace, API/Service, Automation).

japes' blueprint (`jazzx_sdk.pack.blueprint`, `plan_BLUEPRINT_UMBRELLA_OVER_PACKS.md` section 10) is
a parts list: it names the policy, assistant and core packs that make a solution, resolves version
ranges, and activates and pins them. It does not express the chain.

## 2. What exists: more than the first comparison said

My first comparison (2026-10-14, in chat) said japes lacks a Surface Binding, Execution Profile,
non-widening and the ladder. That was wrong. `status/done_JAPES_2_0_0_AUTHORITY_MATRIX_AND_EXECUTION_PROFILE.md`
(2026-07, shipped) built them:

| SBP-00 | japes (built) | Used today |
|---|---|---|
| Autonomy ladder L0-L4 | `manifest/autonomy.py` `AutonomyLevel`, five members, numeric storage | yes |
| Decision classes, authority cells, matrix | `fabric/canonical/authority.py` `DecisionClass`, `AuthorityCell`, `AuthorityMatrixV2`; manifest key `authority_matrix:` | governor; AML pack in jaci |
| Surface Binding Annex | `fabric/canonical/profiles.py` `SurfaceBinding` (surface_type, autonomy ceilings per action class, in/out of scope); manifest key `surface_bindings:`; `SurfaceType` incl. ASSISTANT | loaded by the manifest loader; no pack declares one |
| Client overlay, policy profile | `ClientOverlay`, `PolicyProfile` | not loaded from any pack or by Plato |
| Execution Profile | `ExecutionProfile` (activated modes, capabilities, `extra.non_widening_attestation`) | not loaded or written by Plato |
| Narrowing semantics | `authority/resolver.py` `resolve_effective_autonomy` (min across layers, human_only forces L0, contributing layers for the trace); `check_action` returns typed refusals | governor, state machine, document agent, governed automation |
| Canonical chain P/E/D/T/O, 13 modes | `fabric/canonical`, `modes/` | yes |

So the gap is wiring, not modelling:

- the blueprint does not reference the chain;
- Plato's case runs and assistant turns do not resolve effective authority from it;
- activation does not record an Execution Profile;
- nothing checks non-widening when a solution is put together;
- the Acra DSCR packs declare no matrix, surface bindings, overlay or profile.

## 3. Decisions this plan keeps

From `plan_BLUEPRINT_UMBRELLA_OVER_PACKS.md` section 9 (user, 2026-10-06):

- **Customer first.** `acra-dscr-policy` and `acra-dscr-assistant` are whole, runnable packs.
- **Roles.** `-policy` / `-assistant` suffixes.
- **No composition.** The blueprint names the set and does not compose.
- **Core extracted later.**

The chain does not change any of that. It adds which governance artifacts each member carries, and
a check that they narrow.

## 4. Mapping (the decision ARCHITECTURE.md records)

| Chain layer | Carried by | Artifact |
|---|---|---|
| Domain Pack | the policy pack (and the core, once extracted) | rules, jobs, catalog, registry, and `authority_matrix:` (decision classes, cells, launch autonomy, human_only, evidence floors) |
| Surface Binding Annex | each surface's pack: the assistant pack (Assistant surface); the policy pack's case-run step (API/Service or Automation surface) | `surface_bindings:` (surface_type, in-scope action classes, autonomy ceiling per action class) |
| Certified Client Overlay | the customer policy pack | `client_overlay:` (jurisdictions, role mappings, thresholds, approved evidence sources); certification against a guideline version already exists |
| Execution Profile | the blueprint's activation | an `ExecutionProfile` record written at activation: activated modes, capability catalog (skills, step kinds), autonomy posture per action class, version bundle (the pins), non-widening attestation |

The four gate families, named onto what exists:

| Gate | What exists |
|---|---|
| Conformance | pack lint and check |
| Launch | publish gates, plus the blueprint check (N2) |
| Promotion | pass bars, rule trials |
| Recertification | guideline release and certification |

## 5. Phases

- **N1. The blueprint carries the chain.**
  - The blueprint version names the chain artifacts its members declare, read from each member's
    manifest. It adds no copies.
  - `GET /blueprints/{id}` returns a `chain` view: layer, member, artifact, and a summary (decision
    classes, action classes, ceilings).
  - The solution page shows it as a header strip: Domain Pack, then Surfaces, then Overlay, then
    Profile.
- **N2. Non-widening check at blueprint publish and activation.**
  - Static, per decision cell and action class: profile ≤ overlay ≤ surface binding ≤ matrix launch
    autonomy.
  - A `human_only` cell must be L0 at every layer, and must not be in scope of an Automation surface.
  - An action class in scope at a surface must exist in the matrix.
  - Findings are warnings with the layer that widened (tolerant first); a pack-data `strict:` flag
    turns them into a refusal.
  - The same resolver semantics as `resolve_effective_autonomy`, run over the whole table instead of
    one action.
- **N3. Runtime: resolve effective authority from the active blueprint.**
  - Case runs (governor and human checkpoint steps) and assistant turns (skill invoke,
    approve-before-run tools) build the authority context from the active blueprint's chain, and call
    `check_action` before any consequential action.
  - Traces record `contributing_layers`.
  - The runs page and the trace viewer show the effective autonomy, and which layer set it.
  - With no chain declared, behaviour is unchanged.
- **N4. Activation writes the Execution Profile.**
  - The blueprint's activation records an `ExecutionProfile` next to the pins, in the
    `pack_activation` history: the modes and step kinds in use, skills, the posture per action class
    (the resolver's result), the version bundle, and an attestation that N2 found no widening, or
    the warnings it accepted.
  - Run records cite it.
- **N5. Acra DSCR data** (sonnet-jaci; pack data, not code). A minimal, honest first matrix:
  - decision classes: eligibility decision, condition issue, exception, adverse action;
  - cells with launch autonomy, for example eligibility at L1 Recommend and an exception human_only;
  - a surface binding for the assistant (Assistant: answer and draft; no decision actions);
  - a surface binding for the case-run API (recommend; conditions L2 with approval);
  - an overlay holding Acra's role mappings and approved evidence sources.

  The figures are the user's or Acra's to set; this phase only gives them a home.
- **N6. Documentation.** ARCHITECTURE.md: the blueprint as an instance of the narrowing chain, the
  mapping table above, and the gate-family naming. CHANGELOG per phase.

## 6. Order and size

- N1 and N2 together, one pass, mostly SDK logic over existing models.
- N4 is small.
- N3 is the substantial one: the runtime call sites.
- N5 runs in parallel, as data.
- N6 comes last.

## 7. Decisions for the user

1. **Where the Execution Profile lives:** written by the blueprint's activation (recommended), or as
   a file in a pack?
2. **Strictness:** N2 warns by default and refuses only with `strict:` (recommended, tolerant
   first)? Or should non-widening be a hard rule from the start, since it is the chain's safety
   property?
3. **Acra's first matrix:** who sets the launch autonomy per decision class: you, Acra, or a proposed
   default that you then review?
4. **Surface types for case runs:** is the case-run endpoint an API/Service surface, or Automation
   when triggered by an event or a schedule? Proposed: API/Service, plus Automation when a schedule or
   trigger is declared.
