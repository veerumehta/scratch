# plan_PLATO_DEMOS_SECTION

Author: Virendra Mehta <virendra.mehta@jazzx.ai>
Repo: japes (`jazzx_sdk`, `plato`), version in progress 2.7.3

## Status and modifications

How to use this section: the plan author may read and update it; implementers append one dated line per slice (what landed, the commit, anything the plan got wrong). Newest line last.

- 2026-11-12 drafted by opus-xrepo from the user's ask: "in Plato, a section on demos that accumulates them all, with a menu to run them one by one". Nothing built. The vocabulary growth demo (`plan_PLATO_VOCABULARY_GROWTH_DEMO.md`, shipped in 2.7.2: pack `mortgage_vocabulary_demo`, the Grow section on `ontology.html`, `scripts/pack_demo_check.py`) is the first entry.

## Goal

One Plato page, "Demos", that lists every demo the product can show, each with what it shows, what it needs, and a way to start it; choosing one prepares it (seeds its pack if absent, opens what it needs) and walks the presenter through its steps, linking to the real pages. Adding a demo is adding data, not code.

## Design

- **A demo is a manifest.** A file per demo under a demos data directory (location chosen by sonnet-packs, beside the seed packs): `id`, `title`, `shows` (one sentence), `domain`, `packs` (pack ids it needs, seeded by the existing seeder), `steps` (ordered: a label, the Plato page it opens with its query prefill, what the presenter does, what to expect on screen), `run` (optional: the one launch that costs money, as request fields), `cost` (an expectation in words, never a number the code trusts), `recorded` (optional: a recorded run's proposals for replay without a provider call), `expected` (a pointer to the demo's expected-results file, like `expected_proposals.yaml`).
- **The page** lists demos from a read route, shows the manifest, and its Start button calls a prepare route. Steps render as a checklist with links that carry the prefill; nothing the page does needs a provider unless the presenter starts the `run` step, which uses the page's required budget field exactly as `ontology.html` does.
- **Prepare is idempotent and free**: it seeds the demo's packs for the tenant if absent and reports what it did; it makes no provider call.
- **Replay**: a demo with `recorded` data can show its proposals from the record, so a presentation never depends on a provider, rate limits or a 6-minute 429 delay.
- **Every demo declares its prerequisites**, so the page can say "pack X is not seeded" instead of failing.

## Slices

### D1. The manifest format and the first two manifests (sonnet-packs)
- Define the manifest (a schema or a typed loader with a test), move the vocabulary growth demo onto it, and inventory the other demos the repo already has (for example `examples/adjudication_demo`, the Acra jobs and assessment walk-throughs, policy to pack, the spread pipeline); write the second manifest for the cheapest of them. Report the inventory with, for each, what it needs and what it costs.
- Acceptance: a loader test validates every manifest (steps reference real pages, packs exist in the seed set, `recorded` matches `expected`); `pack_demo_check.py` keeps working or is subsumed.

### D2. List and prepare routes (sonnet-runtime)
- `GET .../demos` and `GET .../demos/{id}` from the manifests; `POST .../demos/{id}/prepare` seeds the packs for the request's tenant, idempotent, free, strict-posture gated like the other POST routes; a client method for each route (the route-vs-client test fails without them).
- Acceptance: prepare twice changes nothing the second time; an unknown id is 404; a deployed posture without auth is 403 and writes nothing.

### D3. The Demos page (sonnet-ui)
- A page in the rail's core set if the user decides so (see Decisions); the menu of demos, the selected demo's steps as a checklist with prefilled links, the Start (prepare) button, and the optional run step with the required budget field. Same mount and tenant helpers as the other pages; it passes the mount test.
- Acceptance: with a recorded demo a presenter can go from the list to the finished compare without typing; the mount test and the page tests pass.

### D4. Add the demos that exist (sonnet-packs, then others)
- One demo per slice, ordered by cost: free ones first.

## Order

D1, then D2 and D3 in parallel against the manifest, then D4.

## Decisions for the user

1. **Is "Demos" in the core rail** (Dashboard, Guide, Demos), or reached by typed URL like the other pages? Recommended: core, since demos are what QA and a presenter open first.
2. **Which demos next** after the vocabulary one (D4 order), once D1's inventory is in.
3. **Replay by default** or live by default for a demo that has a recording? Recommended: replay, with a visible "run live" step.

## Out of scope

- A scripted browser walk-through (a click-through robot); the checklist is for a human presenter.
- Multi-tenant demo isolation beyond seeding for the request's tenant.

## Not verified

- Whether the seeder can seed a pack for a tenant on request (as opposed to at boot).
- Which existing examples can run from a seeded pack alone.
- Whether `NAV_CORE` can take a third entry without changing the degraded replica's rail.
