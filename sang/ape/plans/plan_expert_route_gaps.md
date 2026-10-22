# Expert route gaps from the workshop-bank run (sonnet-runtime, 2026-10-21)

Plan only. Same batch as the other Expert items, after replicate stability. Findings are from reading `experts/policy/*`,
`experts/attestation.py`, `server/expert_api.py` at `v2.6.5`; nothing was run against the live Plato.

## Findings

| # | Gap | At HEAD | Verdict |
|---|---|---|---|
| 2 | `check_compliance` reference is a rule id, version `unknown`, no section | `default.py` puts `rule.rule_id` in `applied_policies`; `answer.py::_references` treats each as a policy id, finds none, falls back to `unknown` | **Defect.** |
| 3 | `interpret` is always `uncited`, no reason | `DefaultPolicyExpert.interpret` is a placeholder: no model, no clauses, constant text; `_cited` then has no references and gives no reason | **Defect in the answer** (no reason), not a missing model: nothing to wire in the default expert. |
| 4 | A draft policy makes every answer "not active" and lists it superseded | `resolve` puts every `not is_active` policy in `stale_policies`; `answer.py` copies that into `freshness.superseded`; a draft has no activated predecessor | **Defect.** Only a policy that was active and was replaced or lapsed is superseded. |
| 5 | Unsigned answers | `attest` already adds `UNSIGNED_WARNING` to `freshness.warnings` when there is no key (tested); the trace record does not say it | Warning is visible in the answer; **add it to the trace**. |
| - | `resolve` gives every question the same line | `resolve` ignores `question`; it returns the policies of the program (`core_policy_ids` + overlay), highest precedence first | **Keyword-blind by design.** Say so in the operation description and the answer. |
| 1 | Guidance assets and playbooks are never cited | The expert's registry holds policies only; `answer_for` has no guidance input; `EXPERT_OPERATIONS` has no playbook; `DefaultPlaybookExpert` has no route | **Missing capability**, below. |

## Steps (tests first, one commit each)

1. **E1 reference carries policy, version, section (S).** `check_compliance` records, per applied rule, `(policy_id, rule_id)`;
   the answer builds one reference per policy (version from `policy_versions`) with the rule's section
   (`domain_extensions.jtbd.section`, else the id's section) on each rule it cites. Test: a rule of a two-policy pack.
2. **E2 `interpret` says why (S).** The placeholder returns a result that names itself; `answer_for` gives
   `reason="interpret has no reader in this expert: a pack's expert overrides it"` when no clause is cited. A pack expert that
   cites clauses is unchanged. Test the reason; no behavior change otherwise.
3. **E3 a draft is not superseded (S).** `resolve` leaves a `DRAFT` policy out of `applicable` and `references`, and notes it
   (`freshness.warnings`: "draft, not served: <id>"); `stale_policies` keeps only a policy that was active and is not now
   (superseded, archived, or past its window). `detect_staleness` follows the same split. Test with a draft beside an active policy.
   Recommendation for the user to confirm: a draft is not served at all (the alternative is serving it flagged, which is what
   makes the answer say "not active" today).
4. **E4 unsigned in the trace (S).** `_record` writes `attested: false` and the warnings into the trace metadata. Test.
5. **E5 resolve says what it selects by (S).** The operation description and a `reason`/note on the answer say it chooses by
   program, not by the question. No behavior change.
6. **E6 cite a GuidanceAsset (M, one commit per part, needs the user's answer to the two questions below).**
   - Read: the route gets a tenant-scoped `GuidanceStore` (the same one `plato/api/guidance.py` uses) through a new optional
     `guidance_for` on `create_expert_router`, as `keyring_for` is wired; none: behavior unchanged.
   - Select, deterministically (no model): assets with `pack_id` of the served pack, status `deployed`, not expired, whose
     `applicability` names the policy or rule asked about (or the program). The expert's `resolve`/`check_compliance`/
     `interpret` results gain `guidance` (asset id, version = content hash, kind, `effective_from` from `created_at`).
   - Cite: `answer_for` adds one `GuidanceReference` per consulted asset (`asset_kind` = the asset's `asset_type`, `section` none);
     `references` stays the envelope's one list, so the guard and ledger read it unchanged.
   - Freshness: `superseded` from the `supersedes` chain (a deployed asset whose successor is deployed), `warnings` for
     `expires_at` and `review_at` past; this is the "freshness" case.
   - Conflict: two deployed assets that share a `topic` key in `applicability` and differ in `guidance` give `status=conflict`
     with both as `positions`; this is the "both positions" case. `topic` is a convention this adds to `applicability`,
     not a field.
7. **E7 Playbook Expert route (deferred).** No route today. 2.7.1's closed `GuidanceKind`, `consumed_by_modes` and the four
   retrieval dimensions are what `DefaultPlaybookExpert` filters on; `DefaultPlaybookExpert.recommend` is a stub packs override.
   After 2.7.1: `answer_for` gets a `PlaybookRecommendation` branch over the same reference shape and `EXPERT_OPERATIONS`
   gains `recommend`. Not before; E6 builds the guidance read both need.

## Questions for the user (E6 only)
- Selection key: is `applicability` naming the policy or rule id the pack author's way to attach a note, or does the pack need a
  declared `cites:` list on the asset (a 2.7.1 field)? Recommendation: `applicability` now, `cites` when 2.7.1 lands.
- Conflict: is a shared `topic` key acceptable as the way two positions are recognized, or should conflict wait for 2.7.1?

## Effort
E1 to E5: one small commit each, about half a day together. E6: one to two days. E7: after 2.7.1.
