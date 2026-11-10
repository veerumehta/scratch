# Design note: composing a base pack and an overlay pack into an assembled pack (S1 of the pack assembly plan; sonnet-runtime, 2026-11-10)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Design only; no code, no commits to the SDK. Names are studio-neutral (base, overlay, assembled; nothing named for a lender or customer). Read from the v2.7.1 tree: `jazzx_sdk/pack/manifest_loader.py`, `fabric/canonical/policy.py`, `pack/lint.py`, `pack/jtbd_import.py` and `jtbd_match.py`, `pack/blueprint_chain.py`, `pack/store.py` and `store_db.py`, `formal/json_rules.py`, `fabric/guidance/governance.py` (2.7.1). `[V]` is read in code; `[I]` is my inference; `[U]` not verified. The plan decisions it follows: assembly at publish time; a lender loosening is refused by default and allowed only as a declared `relax` that cites the agency text permitting it and goes through the widening class and the certification forum.

## 0. What already exists that the design leans on

- **Precedence.** A manifest's `policies:` block lists `core` then `overlays` and the loader returns the files in that order; `programs:` maps a program id to the overlay policy ids that apply [V manifest_loader].
- **Override vocabulary is in the policy model already.** `Rule.replaces` ("rule ids in lower-precedence policies this rule stands in for, skipped wherever this rule applies"), `Policy.suppresses: list[RuleSuppression(rule_id, reason, citations)]`, `Policy.overlay_id` ("client-specific overlay identifier if this policy is an institutional override"), `Policy.scope` (institution, product, deal) [V policy.py]. The formal compiler refuses a base rule that replaces anything: `only overlay rules may replace another rule` (`overlay_id` must be set) [V json_rules.py:272]. So an overlay is a policy with `overlay_id` whose rules use `replaces`; assembly does not invent a new override mechanism.
- **Dangling relations are linted.** `lint_pack` reports `dangling_relation` when a rule `replaces` or a policy `suppresses` an id "which no other policy in the pack declares" [V lint.py:249]. So the base policies must be in the same pack as the overlay that replaces them: this is exactly what an assembled pack is.
- **The matcher.** `pack/jtbd_import.py` matches two JTBD sets rule by rule (same text in the same section goes to the core once; a different one to its program's overlay) and exposes `deterministic_numbers(rule)` (the numbers a rule's checks name); `jtbd_match.py` has `match_items`, `same_text` [V]. S3 and S4 extend this; compose does not need the matcher, only the result.
- **A deterministic archive.** `pack_archive(pack_dir)` writes a flat zip with sorted entries and a fixed timestamp [V store.py], so the same files give the same `content_digest`.
- **The non-widening rule exists for autonomy, not content.** `check_non_widening` in `blueprint_chain.py` compares action classes and autonomy levels across blueprint layers; nothing compares policy rules [V].

## 1. The compose function

Where: a new subpackage, `jazzx_sdk/pack/assembly/` (the `pack/` directory holds 49 modules, past the guideline's about 25, so a subpackage; not the `jazzx_sdk/` root). Modules: `compose.py` (the function), `declarations.py` (the overlay's declarations), `provenance.py`, `non_widening.py` (the content check), `stale.py`. Tests in `tests/pack/assembly/`.

```python
@dataclass(frozen=True)
class PackInput:               # a pack as compose reads it: no store, no tenant
    pack_id: str
    version: str
    content_digest: str
    files: Mapping[str, str]   # relative path to text

def compose(bases: Sequence[PackInput], overlay: PackInput, *, assembled_id: str, assembled_version: str,
            approvals: Sequence[RelaxApproval] = ()) -> AssemblyResult
```

`AssemblyResult`: `files` (the assembled pack's files, path to text), `findings` (list of `AssemblyFinding(code, severity, subject, detail)`), `provenance` (section 2), `inputs_digest`, and `status`: `assembled`, `needs_review` (assembled, with findings a person must clear) or `refused` (no files). Pure: it reads only its arguments, so the host decides who may read which pack (section 6) and a test needs no store.

Steps, in order:
1. **Validate inputs.** Each base and the overlay has a manifest; base pack ids are distinct; the overlay declares which bases it targets (`assembly.yaml`, section 3) and the versions it was written against.
2. **Place files.** Base policy files go to `policies/base/<base pack id>/...` and are listed under `policies.core` (several families: several core entries, in the order the bases were given); the overlay's policy files go to `policies/overlay/...` listed under `overlays`. This is the existing precedence, unchanged, so the loader, resolver and `lint_pack` apply as they are.
3. **Stamp overlay policies.** An overlay policy gets `overlay_id` (the overlay pack id) if it has none, so its `replaces` pass the compiler's check.
4. **Apply declarations** (section 3): refuse an overlay rule that reuses a base rule id without declaring it; for `tighten` and `relax` set `replaces` to the base id; check every target exists.
5. **Run the content check** (section 4) over every `tighten`; a `relax` is accepted only with an approval (section 3).
6. **Merge the manifest.** `programs:` is the union (a program id declared by two bases is a conflict, section 5); vocabulary layers keep their order (base layer, then overlay layer: a vocabulary chain term redefined by the overlay is the existing `lint_pack` error "a layer redefining a term" [V lint.py]); `pack_id`, `pack_version`, `domain`, `segment` come from the arguments and the primary base, and a mismatch of domain or segment among inputs is a refusal.
7. **Write provenance and the assembly block** (section 2), then return. No timestamps, no random ids, YAML dumped through `policy_document` (already deterministic), files sorted: the same inputs give the same `files`, so `pack_archive` gives the same `content_digest`. `inputs_digest` is a hash over the ordered input digests, the declarations and the approvals, recorded in the manifest, so "same inputs, same assembly" is a test (compose twice, compare, and compare after reordering dict keys).

A script (`scripts/assemble_pack.py`, later) takes directories or archives, calls `compose`, writes the pack directory or archive and prints the findings. A Plato route later (`POST {prefix}/packs/assemble`, a studio calls it) reads the inputs from the caller's own tenant store, calls `compose` and publishes the result as a draft or version; the route is where tenant access is decided.

## 2. Provenance

Two places, both inside the assembled pack so they travel with it and are part of its digest:

- `assembly/provenance.json`: one record per assembled rule, sorted by policy id then rule id:
  `{policy_id, rule_id, layer: "base"|"overlay", source_pack, source_version, source_digest, file, kind: "inherited"|"add"|"tighten"|"relax", replaces: [base rule ids], base_rule_digest, review: "none"|"needs_review"|"approved", approval_ref}`
  `file` is the path in the source pack; `base_rule_digest` (a hash of the base rule's canonical form) is what stale detection compares.
- the manifest's `assembly:` block: `{inputs: [{role: "base"|"overlay", pack_id, version, content_digest}], inputs_digest, composed_with: "<compose version>", findings_open: n}`. The assembled version "cites its input versions" here.

A guard in `lint_pack`: an assembled pack (a manifest with `assembly:`) whose files differ from what its provenance records (a rule edited by hand after assembly) gets a finding `assembled_pack_edited`; re-composing is how a change is made.

## 3. How an overlay declares an override

Declarations live in the overlay pack's own `assembly.yaml`, not in the policy files, so the policy files stay plain canonical policies a studio already produces:

```yaml
targets: [{pack: <base pack id>, version: ">=1.0 <2.0"}]
rules:
  - rule: OV_DTI_CAP          # an overlay rule id
    kind: tighten             # add | tighten | relax
    base: BASE_DTI_CAP        # required for tighten and relax; absent for add
  - rule: OV_COST_CAP
    kind: relax
    base: BASE_COST_CAP
    cites: [{ref: "<agency handbook section>", quote: "..."}]   # required for relax: the agency text that permits it
suppress:                      # a base rule removed outright: always a relax
  - rule: BASE_SOME_RULE
    kind: relax
    cites: [...]
```

- **add**: a new rule id. If the id exists in a base: refused (`id_collision`).
- **tighten**: the overlay rule `replaces` the base rule and must pass the content check; one that does not pass is a refusal when the check can show it widens, and `needs_review` when the check cannot decide (section 4).
- **relax**: refused unless an approval is supplied (`RelaxApproval(rule, approver, forum_id, class="boundary_widening", cites)`), because it loosens agency text. The approval is the widening class and the certification forum of 2.7.1's guidance governance, reused rather than rebuilt: `GuidanceGovernance` (forums in `governance/*.yaml`, `approval_steps`, `is_member`) already says who may approve a widening and that an unclassified or forum-less approval is refused. `[I]` Which file declares the forum for a pack-assembly approval (the same `governance/guidance.yaml` or a sibling `governance/assembly.yaml` with the same schema) is an open question below. The approval is recorded in provenance (`review: approved`, `approval_ref`) and in the audit trail when it goes through Plato.
- A policy `suppresses:` entry in an overlay with no declaration is a refusal (`undeclared_relax`): suppressing a base rule is a relaxation by definition.
- An overlay that targets a base version outside its declared range is `needs_review`, not silent.

## 4. What the non-widening check can decide, and what it flags

Assumption to verify `[U]`: in japes a rule's `condition` states what must hold, a violation is `condition not satisfied` (`Verdict.VIOLATED`, routed by `on_violation`), and `action` says what to do when the rule applies. The orientation below follows that: a tighter rule is satisfied in fewer cases. If a pack uses the other orientation (the condition names the bad state) the comparator directions invert; the check must read the orientation from the rule, which the model does not carry today, so the first cut states the assumption and lets a pack declare the opposite per policy.

What the check decides from structure (result: `tighter`, `same`, `looser`; `looser` is a refusal unless declared `relax`):

| Content | Decided how |
|---|---|
| `Expression` (field, operator, value), same field and operator family | numeric values only: `>=` or `>` raised, `<=` or `<` lowered is tighter; the reverse looser; `==`, `in`, `not_in`, `contains`: a smaller allowed set is tighter (`in` list a strict subset, `not_in` a strict superset), equal is same |
| `RatioCondition` | `threshold` as a number and `direction` (min or max) the same on both sides: raised min or lowered max is tighter |
| `MatrixCondition` | same axes and table shape and a declared `direction`: cell-by-cell numeric comparison; any shape difference is flagged |
| `AllOfCondition` | the base's conjuncts all present in the overlay's with each equal or tighter, plus extra conjuncts: tighter; a base conjunct dropped or loosened: looser |
| `AnyOfCondition` | the reverse: extra disjuncts loosen, dropped disjuncts tighten |
| `applicability` | broader (fewer cases skipped) is tighter, narrower is looser: decided only where both sides are `Expression` or `AllOf` of expressions over the same fields; otherwise flagged |
| `action` | an order declared in code and stated here: `allow` < `log` < `notify` < `require_evidence` < `require_approval` < `escalate` < `deny`; lower is looser, equal same, higher tighter. `[I]` the plan's "deny, refer, allow" has no `refer` in `RuleAction`; I would treat `escalate` as refer. A pack may pin its own order. |
| `on_violation` | `fail` is the strictest; `waiver_required` and `pre_review_required` are not comparable with each other, so a move between them is flagged; from `fail` to either is looser |
| `ProcedureCondition` (most imported mortgage content) | `steps` identical and the base's `checks` a subset of the overlay's (exact strings) with `outcomes` unchanged: tighter (checks added); anything else (steps reworded or reordered, a check removed or reworded, an outcome added or removed) is flagged |
| `suppresses` | always looser (a `relax` declaration) |
| `effective_from` / `effective_to` | an overlay start later than the base's, or an end earlier, narrows when the rule applies: flagged, not decided |

What it must flag for human review, never guess (finding `needs_review`, the assembled pack is `needs_review` until each is cleared): `NaturalLanguageCondition` of different text; `PythonCondition` and `DslExpression` (code); a changed condition kind; reworded procedure steps or checks; changed numbers inside prose (`deterministic_numbers` already extracts them; the direction is not inferable from prose, so a changed number is flagged, not graded); changed `parameters`; a `tighten` whose target a later base version removed; two overlay rules replacing one base rule. A tighten that looks tighter on one axis and looser on another (a cap lowered and an applicability narrowed) is flagged as mixed, since "tighter overall" is not decidable.

Cost of the table: about a screen of code per row for `Expression`, `Ratio`, `AllOf`/`AnyOf`, `action`, `on_violation`, `Procedure`; `Matrix` and `applicability` are the harder two; the rest is "flag". The check returns a finding per rule and the reason, so a reviewer sees why.

## 5. Conflict cases

- Same rule id in two bases (a family overlap, such as government programs inlined in a conventional base): refused unless the two rules are byte-equal after canonical dump (then kept once, both sources in provenance); otherwise `id_collision` and the overlay or a base owner must resolve it.
- Overlay `add` with an existing id: refused. Overlay `tighten` or `relax` whose `base` does not exist: refused (`dangling_relation`, the existing lint code).
- Two overlay rules `replaces` the same base rule: `needs_review` (a tighten chain is order-dependent); two overlays in one assembly are out of the first cut (one overlay per assembly; the declared `targets` allow several bases).
- A base rule that itself has `replaces` (the base already overrides something): the existing semantics carry over ("a replaced rule's own replacements carry over"), and an overlay that replaces the replacing rule is checked against that rule.
- A program id (`programs:`) declared by two bases or by a base and the overlay with different policy lists: refused (`program_collision`), identical lists merge.
- Policy-level mismatch: `scope` of an overlay policy below the scope of what it replaces (the narrowing ladder: deal outranks product outranks institution) is a finding; `policy_type` mismatch is `needs_review`.
- Vocabulary chain: an overlay layer that redefines a base term is the existing error.
- `effective_from` of an overlay rule after the assembled pack's effective date leaves the base rule live until then: reported, not an error.
- An overlay written against base version X assembled with version Y: `needs_review` with the base rule digests that changed (from `pack/diff.py`).

## 6. Stale assembly

The assembled manifest records each input's pack id, version and `content_digest`, and each rule's `base_rule_digest`. `assembly_status(assembled, latest_bases)` (a pure function in `stale.py`; the host supplies the latest published versions of the same pack ids from the caller's own store) returns, per input, `current` or `stale` (a newer version exists), and for a stale base the list of rule ids whose digest changed, were added or were removed, split into: changes to a rule an overlay tightens or relaxes (`overlay_affected`, must be reviewed: the tighten may now be a loosening or point at nothing), and the rest (inherited, safe to take). A Plato list view (a later slice) shows assembled packs by status. Re-assembly is a new version of the assembled pack, never an edit; the old version stays published.

## 7. Tenant access for shared base packs

`compose` takes `PackInput` values, so it reads no store and crosses no tenant by itself. The pack store is tenant-scoped (`store_for(tenant)`, rows keyed by tenant) and the stored `visibility` field (`"tenant"`) is not read by any cross-tenant path I found [V grep over `jazzx_sdk` and `plato`]; the 2.7.0 and 2.7.1 tenancy work removed reads that reach across tenants, and a shared-read path would reintroduce one.

Recommendation: **copy, do not share.** A base pack is published in a library tenant (a host-chosen name, config, not an SDK constant) and brought into an assembling tenant by an explicit copy step (publish the same archive there: the blob is content-addressed, so the bytes are shared and the rows are the tenant's own; the seed packs already work this way) before assembly; the assembled pack's manifest cites the base's id, version and digest, so the copy is verifiable against the library's. Compose and stale detection then read only the assembling tenant's store. This needs a small "bring a library pack into my tenant" route or script (about half a slice), and a decision on who may do it (open question 4). The alternative, a `shared` visibility with a read-through for a named library tenant, is smaller to use and larger to get right (every store read, the guard tests, audit), and I would not take it for this.

## 8. Size and order

- Compose, provenance, declarations, assembled-pack lint guard, the determinism and refusal tests: about 1.5 slices.
- The non-widening content check (the table in section 4, with its findings): about 1 slice for the decidable rows and the flag-everything-else default; the harder rows (`Matrix`, `applicability`) can follow when a real pack needs them.
- Stale detection: about 0.5 slice. Script: 0.2. Library-copy step: 0.5. Plato assemble route and a list view: about 1 slice, after the SDK pieces and with `sonnet-ui` for any page.
- Equivalence test (S2 of the plan): assemble a base and an overlay that came from a split job and compare to the original rules after whitespace normalization; it needs S3 and S4 output (real bases and overlays), so the first version uses small synthetic packs and the real comparison lands with S5.
- Order: compose and provenance, then the content check, then stale detection, then the route. The first deliverable already assembles and refuses; the check can begin as "flag every tighten" and grow.

## 9. Open questions for the user

1. The approval for a declared `relax`: reuse the guidance governance (the certification forum named in a `governance/` file of the overlay or assembled pack, the `boundary_widening` class), or a separate approver list for assembly? I recommend reusing it, with a `governance/assembly.yaml` of the same schema so a pack can name different people.
2. The condition orientation (a condition states what must hold; a violation is not satisfying it): is that the convention for every pack, including the imported mortgage jobs? If not, which policies carry the opposite?
3. The action severity order and `on_violation` order in section 4: confirm, or give the pack's own.
4. Who may copy a library base pack into a tenant, and what is the library tenant's name (config)?
5. One overlay per assembly in the first cut, several bases allowed: is that enough, or does a lender sit on more than one overlay (a lender plus a program overlay)?
6. A `needs_review` assembly: may it be published as a draft (not activated) until each finding is cleared, or must nothing publish with an open finding? I recommend draft allowed, activation refused.
7. Version branch: the user decides; nothing is bumped here. The first slices are SDK-only and need no migration.
