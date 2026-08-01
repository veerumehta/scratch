# Done: CiSpreadPolicyExpert — FR-SOP Closure

Author: Virendra Mehta · Updated 2026-08-01
Repo: jaci (+ japes, per the two decisions below) · Plan: docs/plans/plan_JACI_CL_POLICY_EXPERT.md

**All 6 phases done** (2026-08-01).

## Git findings (Phase 0's own ask)

`git log --diff-filter=D -- 'src/jaci/scenarios/ci_spread/experts/policy.py'` → one commit,
`f165c64` ("v0.9.5: data-configured PolicyExpert + evidence-type vocabulary", 2026-06-17). The old
`CIPolicyExpert` subclass was not abandoned — it was deliberately deleted *because* its
overlay-aware `resolve()`/`check_compliance()` logic was generalized into the SDK's
`DefaultPolicyExpert`, configured from plain data (`registry=`/`core_policy_ids=`/`overlay_map=`),
no subclass. Commit message: "The pack ships only data for policy; overlay-aware resolution +
gates live in the SDK."

## A correction to the plan's own Phase 2, found by reading the current code rather than assuming

This is still true today, live: `conductor.py:185-190` constructs
`DefaultPolicyExpert(pack_id=..., registry=CI_REGISTRY, core_policy_ids=CI_CORE_POLICY_IDS,
overlay_map=OVERLAY_MAP)` directly, no subclass, and registers it via
`register_instance("policy", ...)`. Reading `jazzx_sdk/experts/policy/default.py` confirms
`resolve()` already implements the full core→overlay precedence ladder, conflict detection
(`_detect_overlay_conflicts`), and stale-policy filtering; `check_compliance()` already evaluates
both flat-`Expression` and `DslExpression` rule conditions with correct field-precedence-across-
policies semantics (a higher-precedence policy's claimed field is skipped by lower-precedence
policies; unclaimed fields still evaluate).

So Phase 2 as literally written ("Subclass `DefaultPolicyExpert`. Override `resolve()` with the
precedence ladder: deal → program overlay → core → conventions") would re-implement working SDK
logic. The only genuinely new tier is **deal** (per-package special instructions), which sits above
program overlay and has no equivalent anywhere in the SDK today (`overlay_map` is a flat
`program_id → ids` dict with no third scope, and no per-call ephemeral-policy concept exists).

**Decided 2026-07-31** (asked, confirmed): extend `DefaultPolicyExpert` in japes itself with an
ephemeral top-tier-policy parameter on `resolve()`, rather than a jaci-only subclass — the same
"deal overrides everything, ephemeral, never persisted" shape is generically useful (AML
jurisdiction overrides, mortgage per-loan overlays would want it too), not C&I-specific.

Two stub confirmations (not corrections — Phases 4/5 are already framed as building these from
scratch, this just confirms there's nothing partial to reuse): `DefaultPolicyExpert.interpret()`
returns a canned string with empty `ambiguities`/`examples`/`cited_clauses` today; `.detect_staleness()`'s
per-policy loop body is literally `pass`. Neither does real work yet.

## Policy-vs-profile split (Phase 0's second ask)

Confirmed the plan's own recommendation, no objection raised: anything that can block or flag
(thresholds, caps, precedence rules, exception policy) is a Policy; anything that only
parameterizes rendering or math (tolerances, workbook layout, period method selection) stays
profile config.

## Policy schema scope field (Phase 1's "japes seam" decision point)

Checked `jazzx_sdk/fabric/canonical/policy.py`'s `Policy` model directly: no `scope` field exists
today — only `overlay_id: Optional[str]` (a bare institutional-override marker) and a generic
`domain_extensions: dict[str, Any]` escape hatch. Given `scope` (institution/product/deal) is the
load-bearing concept for this entire plan's precedence ladder, **decided 2026-07-31** (asked,
confirmed): add a first-class `scope` field to `Policy` in japes rather than carrying it in
`domain_extensions`.

## A real, unresolved gap found while grounding Phase 1 — the "special-instructions file"

`config/packs/ci-spread-core/policies/overlays/` exists but is **empty** — the RB program overlay
(`RB_CI_OVERLAY`) actually lives inline in `conventions.yaml`, not in that directory (the plan's
Phase 1 text reads as if `overlays/` already holds program-overlay content; it doesn't — it's
reserved but unused today, which does make it a reasonable home for new deal-scope content).

More materially: searched the whole repo for `special.instruction`/`special_instruction`/
`SpecialInstruction` and for `FR-SOP` — every hit is inside this plan document itself. There is no
PRD text, no fixture, no existing document, and no prior code defining what a "per-package
special-instructions file" actually looks like (format, which fields it can override, how it's
attached to a deal/package). `docs/LoanSamples/Regional Bank/` (the exit-criterion deal) has no
such document either — just financial statements and a credit app.

**This blocks Phase 1's second bullet and Phase 5's gold case** (both depend on parsing this file
into an ephemeral deal-scoped Policy). Not something to invent unilaterally — asking rather than
guessing a shape for a load-bearing, previously-undefined artifact.

## Phase 1 — done, with one real gap resolved by asking rather than inventing

Since "special-instructions file" had zero grounding anywhere in the repo, asked directly:
confirmed structured YAML — same shape as `core.yaml`/`conventions.yaml` (a `policies:` list of
one canonical `Policy`), not free text or a bespoke format. No new schema needed as a result.

- `scope` added to every policy in `core.yaml` (institution) and `conventions.yaml`
  (`CI_CORE_FCCR_POLICY`/`CI_CORE_ABL_POLICY`/`CI_CORE_LIEN_POLICY`: institution;
  `RB_CI_OVERLAY`: product).
- `load_deal_special_instructions(path)` added to `policies/loaders.py` — parses a
  special-instructions YAML into a `Policy` via the same `load_policies()` the other loaders
  already use; returns `None` if the file doesn't exist. Deliberately does not touch
  `CI_REGISTRY` — the policy it returns is handed to a caller per-call, never persisted.
- Example fixture: `config/packs/ci-spread-core/policies/overlays/deal_si_rb_example.yaml` —
  overrides `RB-CI-LEVERAGE-CEILING` (RB_CI_OVERLAY's 3.5x) down to 3.25x for one deal. (Briefly
  written to `policies/` directly and moved once `policies/overlays/`'s permissions — owned by a
  different local user on this checkout, mode 755 — were fixed; flagged rather than worked around
  with chmod/sudo at the time.)
- 6 tests in `tests/unit/test_ci_policy_loaders.py` covering scope round-trip and the loader.

## Phase 2 — done, without restoring `experts/policy.py`

Per the confirmed direction (extend japes, not a jaci subclass): `DefaultPolicyExpert.resolve()`
and `.check_compliance()` (`jazzx_sdk/experts/policy/default.py`) both gained an optional
`deal_policy: Policy | None` parameter. When given, it's prepended to `applicable_policies`/
`precedence_order` (highest precedence — evaluated, and its fields claimed, before any overlay or
core policy), never written into `self.registry` (a local dict copy is built for the one call
that needs it), and any rule id it shares with an already-applicable policy is recorded under
`resolution.metadata["deal_overrides"]` — informational (the deal policy wins by construction),
kept distinct from `conflicts` (same-tier ties between two overlays, unchanged).

This means the live `conductor.py:185-190` `DefaultPolicyExpert(pack_id=..., registry=CI_REGISTRY,
core_policy_ids=CI_CORE_POLICY_IDS, overlay_map=OVERLAY_MAP)` instance can resolve the full
3-tier ladder (deal → overlay → core) today by passing `deal_policy=` at call time — no new
jaci class, no change to `conductor.py`'s construction, `CI_CORE_POLICY_IDS`/`OVERLAY_MAP` stay
exactly as public as they were before (no retirement attempted — that's now moot, since there's no
subclass to retire them into).

Also added a `PolicyScope` enum (`institution`/`product`/`deal`) and a `scope: Optional[PolicyScope]`
field on the canonical `Policy` model (`jazzx_sdk/fabric/canonical/policy.py`), exported from
`jazzx_sdk.fabric.canonical`.

9 new tests in `jazzx_sdk`'s `tests/test_default_policy_expert.py` (deal-tier precedence, no
persistence into the registry, field-claim ordering, override-not-conflict, scope round-trip) plus
the 3 end-to-end tests in jaci's `test_ci_policy_loaders.py` (listed above) proving the real
`CI_REGISTRY`/`CI_CORE_POLICY_IDS`/`OVERLAY_MAP`-configured instance resolves the full RB ladder
correctly against the real deal fixture.

## Conductor wiring — done

Found the real call site: `CIConductor._step_policy()` (`conductor.py:639`), the only place
`self.policy_expert.resolve()`/`.check_compliance()` are ever actually invoked — always through
`.execute(ExpertRequest)`, not a direct method call. `ExpertRequest` has no dedicated field for a
deal policy, so it travels as a `context["deal_policy"]` entry, the same bag `question`/
`policy_id`/`proposed_action`/`policy_ids` already travel in for the other operations.

**A real cross-cutting risk found and fixed before it shipped**: `BasePolicyExpert._execute_operation()`
(`jazzx_sdk/experts/policy/base.py`) is the dispatch layer every `BasePolicyExpert` subclass shares
— not just `DefaultPolicyExpert`. jaci also has `AMLPolicyExpert(BasePolicyExpert)` and
`CREPolicyExpert(DefaultPolicyExpert)`, both of which **fully override** `resolve()`/
`check_compliance()` with the pre-existing signature (no `deal_policy` parameter). An early version
of this change forwarded `deal_policy=context.get("deal_policy")` unconditionally — which would
have raised `TypeError: check_compliance() got an unexpected keyword argument 'deal_policy'` on
every AML and CRE compliance check, immediately, in production. Fixed to forward `deal_policy` only
when `context["deal_policy"]` is actually present (`**deal_kwargs` built conditionally) — a pack
that never sets it sees the exact same call it always has. Verified directly: AML's and CRE's own
test suites (`tests/unit/test_aml_policy_expert.py`, `tests/test_cre_policies.py`,
`tests/integration/test_expert_layer_integration.py`, 45 tests) all still pass.

- `LoanApplication` (`ci_spread/schemas/__init__.py`) gained `special_instructions_path: str | None`.
- `_step_policy` loads it via `load_deal_special_instructions()` when set and adds it to the
  `ExpertRequest.context` sent to `policy_expert.execute()` — silently skipped (no `deal_policy` key
  at all) when the path is unset or the file doesn't exist, matching the loader's own `None`
  contract.
- 2 new japes tests proving the real dispatch path (`ExpertRequest` → `execute()` →
  `_execute_operation()` → `check_compliance(deal_policy=...)`) works end-to-end, not just direct
  method calls. 3 new jaci tests (`tests/unit/test_ci_conductor_deal_policy.py`) proving
  `_step_policy` itself wires the fixture through, is a no-op with no path set, and is a no-op
  (not an exception) when the path doesn't resolve to a real file.

**Still not done as of Phase 2:** Phases 3-6 in full. Phase 3 closed below; Phases 4-6 remain.

Verified through Phase 2: japes full suite 1987 passed (was 1978 at session start), 3 skipped, no
regressions. jaci full suite 768 passed (was 756 at session start), 8 skipped, 5 xfailed, same 5
pre-existing unrelated failures (`test_anthropic_reasoner`/`test_threat_intel_handler`, an
unrelated signature drift) unchanged throughout.

## Phase 3 — done (FR-SOP-3, FR-SOP-4)

**A discovery before building anything**: read the existing correction/approval machinery
(`corrections.py`, `hitl_approval.py`) closely before assuming Phase 3's second half needed new
code. It didn't. `Correction._rationale_required` already rejects a rationale-less override at
construction (`test_correction_without_a_rationale_is_refused`, pre-existing); `apply_corrections`
already produces a new package layer without mutating the as-reported one; `hitl_approval.py`'s
`_apply()` already routes *every* correction-bearing decision through `check_maker_checker_roles`
and `promote_spread(matrix=...)` (the cl.am.005 authority pattern), unconditional on why the
correction exists. A policy-driven override is just a `Correction` like any other — it already
gets this gate for free. Nothing here needed rebuilding, exactly as the plan's own text says not
to.

The actual gap: `check_compliance()` ran (`CIConductor._step_policy`, since v0.9.5) but its output
never became a real `ValidationFinding` — it was flattened into `CreditRecommendation.key_concerns`
strings, invisible to the exception summary, review queue, or governed workbook, all of which read
`ValidationFinding` lists. `cl_capability.py`'s `CL_SPREAD_PIPELINE` (the pipeline that actually
produces those) never called the PolicyExpert at all. Closed:

- `DefectClass.POLICY_VIOLATION` + `Severity.POLICY` (added Wave 2a, unused until now — the
  enum's own docstring already described exactly this case) on every converted finding, never a
  blocking severity, matching FR-SOP-3's "flags for the approver, not decisions" literally
  (`Severity.blocks_promotion` is `False` for `POLICY`).
- `policy_violations_to_findings(compliance_result, period=)` (`validation.py`) converts a
  `ComplianceResult`'s violations, citing `policy_id`/`rule_id` in `detail`. `validate_package()`
  gained an optional `compliance_result=` parameter folding these in — additive, every existing
  caller unaffected.
- `credit_validation.provides.validate` (the `CL_SPREAD_PIPELINE` step) is now async and, when
  `CLSpreadContext.policy_expert` is set, runs `check_compliance()` against the latest period's
  computed metrics (+ `program_id`, + `deal_policy` when set) before folding the result in.
  `policy_expert=None` (the default) is a byte-for-byte no-op — proven by test, not assumed.
- `CI_ADDBACK_POLICY` (new policy, `CI-ADDBACK-OWNER-COMP-CAP` rule, placeholder ceiling matching
  `addbacks.yaml`'s own already-existing-but-never-live `owner_compensation` cap mechanism —
  confirmed by grep that no profile anywhere ever set `owner_compensation_ceiling`, so that cap
  had never actually fired in this codebase). Added to `CI_CORE_POLICY_IDS`, so it resolves by
  default. Proves the acceptance criterion directly: `check_compliance({},
  {"owner_compensation_addback_amount": 300000})` yields exactly one violation citing
  `CI_ADDBACK_POLICY`/`CI-ADDBACK-OWNER-COMP-CAP`.
- `_run_ci_spread_phase` (the demo's real YETI run) now constructs and passes a real
  `DefaultPolicyExpert` — the same `CI_REGISTRY`/`CI_CORE_POLICY_IDS`/`OVERLAY_MAP` configuration
  `CIConductor` already uses — so the live demo path is genuinely wired, not just testable.

**Verified against the real YETI run, not assumed**: instrumented `check_compliance()` to print
its actual context — confirmed it receives real computed metrics (`ebitda`, `gross_margin_pct`,
etc.). Zero violations fire on the real YETI package, and that's *correct*, not a bug: YETI's
current metric set doesn't include `leverage_x`/`fccr_x`/`owner_compensation_addback_amount`
(`compute_metric_results` only emits a metric when its inputs resolve), so no declared rule has a
context field to check against — an honest "no data to evaluate," not a false negative. Flagging
this rather than letting the wiring look more exercised on real data than it is.

**Deliberately not done:**
- `CIConductor._step_policy` (the *other*, older C&I conductor) is untouched — it still flattens
  violations into `key_concerns` strings. Only `cl_capability.py`'s pipeline (the one the governed
  layer — exception summary, review queue, workbook — actually reads from) got the structured
  wiring. Unifying the two conductors is out of scope here.
- Threading `owner_compensation_addback_amount` (or any other add-back's amount) into the live
  compliance context — `build_add_backs_from_library`'s output isn't currently read anywhere near
  `credit_validation.provides.validate`. The mechanism is proven correct via direct
  `check_compliance()` calls; wiring a real add-back amount through the full pipeline is a real,
  separate follow-up.

9 new tests (`test_validation.py` x4, `test_ci_policy_loaders.py` x2, `test_cl_capability.py` x3).
Full suites: japes unaffected (no japes changes this phase); jaci 777 passed (was 768), 8 skipped,
5 xfailed, same 5 pre-existing unrelated failures.

## Phase 4 — done (FR-SOP-5)

**`interpret()` — not the SDK stub, a new jaci-level function instead.** `DefaultPolicyExpert.interpret()`
is built for the ambiguous, LLM/GovernorMode case; a clause citation for a deterministic threshold
rule needs no LLM call at all — the same "deterministic first" reasoning Phase 3's `check_compliance()`
already follows. `interpret_policy_finding()` (`source_view.py`, FR-HIL-2's module — this is
literally that surface's "why" click-through extended to policy findings) takes one
`POLICY_VIOLATION` finding and returns:
- the violated rule's own `description` as the clause citation, and `approval_authority`,
- the flagged field's chart-of-accounts key and `resolve_source_region()`-rendered source, resolved
  two ways: an add-back-cap field (by convention, `"{addback_key}_addback_amount"`) against a
  supplied `NormalizationAdjustment` list, or a real reported line by key against the package,
- an honest "unresolvable" region (never a raise) when the field is a computed metric
  (`leverage_x`) with no single source cell — the same posture `resolve_source_region` itself
  already takes for a missing coordinate.

Proven directly against the Phase 3 acceptance scenario: interpreting the owner-compensation
cap-exceeded finding returns the `CI-ADDBACK-OWNER-COMP-CAP` clause, `senior_credit_committee`
approval authority, the `owner_compensation` SCOA key, the add-back's own capped-amount rationale,
and a resolved source region — the full derivation chain in one call.

**Version pinning.** Checked first: `SpreadPackage` had nothing usable (grepped for any
version/policy field — none). Added `policy_versions: dict[str, str]` (policy_id -> version),
populated by a new `PolicyResolutionResult.policy_versions` field (japes,
`DefaultPolicyExpert.resolve()`, also surfaced in `ComplianceResult.metadata` for a caller working
from a compliance result instead). Populated **at package-creation time** (`financial_spreading.
provides.spread`), not retrofitted after `validate` runs downstream — `resolve()` needs no
metrics, only `program_id`/`deal_policy`, so it can run at the same moment the package itself is
created. This also respects the as-reported package's own append-only convention: the field is
set once, at construction, never mutated onto an already-emitted package.

Verified live against the real YETI run: `policy_versions` correctly shows all 5 applicable core
policies at `1.0.0`.

7 new tests (japes `test_default_policy_expert.py` x4, jaci `test_source_view.py` x3,
`test_cl_capability.py` x2 — 9 total, 2 counted in Phase 3's file already existed). Full suites:
japes 2006 passed (was 1978 at session start), 3 skipped, no regressions. jaci 782 passed (was 756
at session start), 8 skipped, 5 xfailed, same 5 pre-existing unrelated failures throughout.

**Still not done as of Phase 4:** Phase 5 (`detect_staleness()`, the end-to-end gold case) and
Phase 6 (routing the three existing UI surfaces through the expert). Phase 5 closed below.

## Phase 5 — done (staleness + the FR-SOP gold case)

**`detect_staleness()` — real, not the SDK stub.** Like `interpret()`, the stub assumed a
KH-tool-backed lookup; a hydrated `self.registry` (real `Policy` objects, live since Phase 1-2)
makes the tool call unnecessary. Three checks, first match wins per policy: `Policy.is_active`
false (status/expiry — the same check `resolve()` already uses for its own `stale_policies`, not
reimplemented differently here), older than 18 months since `effective_date`, or a NEW third
check — `pinned_versions` (e.g. a `SpreadPackage.policy_versions` read from Phase 4) naming a
version that no longer matches the registry's current one. `_execute_operation` forwards
`pinned_versions` the same conditionally-opt-in way `deal_policy` already travels. jaci's
`detect_stale_pinned_policies(package, policy_expert=)` is the thin wrapper closing the loop:
"which of this package's pinned policies have since been superseded," empty when nothing was
pinned (no policy checking configured) rather than raising. Verified against the real
`CI_REGISTRY`: nothing is stale today (every policy is `effective 2026-01-01`, active, freshly
pinned) — an honest, checked negative, not assumed.

**The end-to-end gold case** (`tests/eval/gold_cases/ci/sop_rb_deal_policy_ladder.json` +
`tests/eval/test_sop_gold_case.py`, a third distinct prefix alongside `case_*`/`trap_*` since this
asserts a multi-step ladder, not a loan decision or one defect class) reuses Phase 1's own RB
special-instructions fixture directly — no new YAML invented for this. Asserts, against the real
`CI_REGISTRY` and the real fixture:
1. the deal tier outranks the program overlay in `precedence_order`,
2. a 3.3x leverage breach is flagged at `Severity.POLICY`, citing `RB_DEAL_SI_2026Q3`/
   `RB-CI-LEVERAGE-CEILING`, never a blocking severity,
3. an SME override on a real reported line without a rationale is rejected; with one, it produces
   a new package layer and re-propagates (`apply_corrections`, asserted, not rebuilt),
4. the resolved `policy_versions` are what a spread built under this ladder would pin,
5. **the acceptance criterion's own check**: simulating the special-instructions file's absence
   (`load_deal_special_instructions` on a nonexistent path — its own already-tested `None`
   contract, not a synthetic stand-in) changes `precedence_order[0]` to the program overlay AND
   changes the actual outcome — the same 3.3x leverage no longer violates the overlay's looser
   3.5x ceiling. Not just "the list looks different": the compliance result flips too.

14 new tests (japes `test_default_policy_expert.py` x9, jaci `test_validation.py` x2,
`test_sop_gold_case.py` x6 — 17 total, 3 already counted). Full suites: japes 2014 passed (was
1978 at session start), 3 skipped, no regressions. jaci 790 passed (was 756 at session start), 8
skipped, 5 xfailed, same 5 pre-existing unrelated failures throughout.

## Phase 6 — done (routing the three UI surfaces through the expert)

**Concepts tab.** `ui/registry.py`'s `Scenario` gained `policy_resolution_target` (a lazy-loaded,
no-arg Streamlit renderer — same `(module, attr)` convention as `pipeline_target`/`demo_target`)
and `.policy_resolution_renderer()`. `ui/concepts_view.py`'s `render()` calls it generically
(`if renderer is not None: renderer()`) — zero ci-specific code landed there, exactly as
directed. `ci_spread`'s entry points at a new `render_policy_resolution()`
(`demo_page.py`): a program selector, then the real `CI_REGISTRY`-configured
`DefaultPolicyExpert.resolve()` rendered in ladder order with each policy's scope badge,
effective date, and pinned version, plus conflicts. Verified directly (not just by inspection):
resolving with no program gives core-only order; resolving with `rb-abl-2026` puts
`RB_CI_OVERLAY` first — the RB overlay visibly narrowing core, per the acceptance criterion.
Non-C&I scenarios have no `policy_resolution_target`, so `concepts_view.render()`'s existing
behavior for them is untouched — proven by test, not assumed.

**Docs & Policies tab (tab 7).** `render_docs_and_policies` itself stays generic — it renders
whatever order/scope it's handed, it never resolves anything (kept exactly `credit_policies: list`
in, per the plan's own instruction not to teach the shared helper about resolution). Tab 7's own
call site now resolves via the same `DefaultPolicyExpert` and passes `credit_policies` in
`precedence_order`, not a raw registry dict's insertion order; each entry's expander now shows
its ladder position (`#1`, `#2`, ...) and scope badge alongside the existing `stub`/extracted tag.
Tab_d (a different tab, the application-stage checklist) was deliberately left untouched — the
plan names "tab 7" specifically.

**Covenants tab, Policy sources expander.** Kept exactly as-is, per the plan's own instruction.
Added the "why" affordance immediately after it: a `🔍 Why?` expander over
`st.session_state["ci_spread_findings"]`'s `POLICY_VIOLATION` entries, calling
`interpret_policy_finding()` (Phase 4) to show the clause citation, approval authority, SCOA key,
and source region for whichever finding is picked. No review queue exists yet
(that plan's own Phase 2 is unstarted) to embed this in, so it stands alone, with a comment
pointing whoever builds that queue at this same function rather than re-deriving it — the "do
not build two queues" instruction, honored by not building a second citation mechanism either.
Verified directly with a real `ComplianceResult`-derived finding: clause and approval authority
render correctly; the source region honestly reports "no source coordinate" for a computed metric
(`leverage_x`) with no single source cell, the same posture established in Phase 4.

3 new tests (`test_ui_registry.py`). Full suites: japes unaffected (no japes changes this phase);
jaci 793 passed (was 790), 8 skipped, 5 xfailed, same 5 pre-existing unrelated failures.

**All six phases of the plan are now done.** `docs/plans/plan_JACI_CL_POLICY_EXPERT.md` is fully
implemented. The plan's own "Adjacent scope" note (populating the Concepts tab for AML/CRE/
insurance diligence/KYC to the C&I standard) is explicitly named as a separate, later plan — not
something this one ever claimed to finish — so it doesn't block promoting this to a `done_` file.
Renamed accordingly.
