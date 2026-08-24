# Plato — program folder

**Plato (Platform Two)** is the proposed deployable that hosts the JAPES SDK as a service:
`japes-plato`, a `plato/` package sibling to `jazzx_sdk/` in this repo, with its own Postgres
database as the durable control plane for assistant configuration. Target release **JAPES 2.5.0**.

Everything Plato-related lives in this folder. Two docs today, one job each.

| File | What it is | Audience |
|---|---|---|
| `Plato_Service_Architecture_and_Build_Plan.md` | **The charter.** Why Plato exists, the boundary against Kernel / `jazzx-assistant` / eval-service / Studio, the five planes, the Azure shape, the database, the API tiers, the strangler path, and the four gating decisions. Revised rarely; the thing to argue about. | Platform architects; the D1/Studio conversation |
| `plan_JAPES_PLATO_SERVICE.md` | **The build plan.** Verified anchors at a named HEAD, seven phases with tasks and acceptance criteria, the "Running this with Claude Code" protocol and guardrails. | Whoever builds it, human or agent |

The charter is also published in project knowledge (`claude/`) so it is visible outside this repo;
this copy and that one are the same document and should be updated together.

## Where Plato came from

Plato is not a new idea in this tree — it is the name for a shape three other documents converged on
independently:

- `../../status/done_JAPES_2_4_0_UAF_PHASE1_ADDITIVE.md` shipped 13/13 phases and left a "blocked on
  someone else" list whose items 5, 6, 7 and 9 are all *"a service boundary decision."* That list is
  Plato's scope.
- `../plan_JAPES_2_6_0_CONFIG_VERSIONING_D1_D2_D3_ADDENDUM.md` puts three system-of-record shapes on
  the table and describes **shape 3** — *"a dedicated JAPES SDK service, its own deployable
  container, with its own DB"* — as under active consideration. **Plato is shape 3, named.**
- The same addendum found `assistant/app/assistant/promotion.py`: ~1100 lines of hand-rolled,
  closure-walking, name-keyed release machinery built because no immutable-release primitive existed.
  Retiring that is Plato's Plane B acceptance test.

Read those three before the charter if you want the argument rather than the conclusion.

## Status

**Proposed. Nothing agreed.** Four decisions gate real work — D1 (adopt shape 3), D2 (does Studio
write to Plato or keep its own store), D3 (process-start owner), D4 (per-skill IO on the execution
path). Phases 0 and 1 run without any of them, so there is work available while they are pending.

## Convention for this folder

- **The charter and the build plan stay separate.** Program scope and per-phase anchors go stale at
  different rates; re-verifying a phase should not mean touching the eval-service absorption
  argument.
- **Per-phase plans get their own files when a phase actually starts** — `plan_PLATO_P0_*.md`,
  `plan_PLATO_P1_*.md` — cut from the build plan with freshly verified anchors at then-current HEAD.
  Writing them before anyone runs the phase is the same content in more files. When that happens,
  `plan_JAPES_PLATO_SERVICE.md` becomes the index and the phases move out.
- **Anchors carry their HEAD.** Every doc here states the commit it was read against. Line numbers
  and file paths drift; if an anchor has moved, fix it, and **if an anchor is gone, stop and
  report** — something landed the plan did not account for. This has already happened twice to
  Plato's predecessors.
- Nothing in this folder is committed to the repo (`ape/` is scratch). Outcomes land in
  `CHANGELOG.md` / `ARCHITECTURE.md` per `CLAUDE.md`'s documentation standards; the planning stays
  here.
