# CKG / Niffler — Claim Remediation Backlog

Purpose: keep the document's claims strong and make them true. Each task below closes a gap the audit found, and names the assertion it protects so that finishing the task is what earns the claim. Nothing here softens the story; it hardens the ground under it.

Priority is by exposure, not schedule. P0 items are the ones a diligence or patent reader relies on being true now.

## P0 — claim-critical, diligence-exposed

| ID | Protects the claim that... | Task | Done when |
|----|----------------------------|------|-----------|
| R1 | The baseline is human-verified with sourced provenance | Backfill primary-source citations for every baseline criterion and run them through review and approval, or a defined bulk retrospective sign-off, so each carries a source and a recorded human decision. Track the verified percentage as it climbs. | Every baseline criterion carries a primary source and a recorded human sign-off, queryable per row. |
| R2 | Nothing enters or changes without independent human review | Any substantive edit by an approver (text, risk level, or territory) clears prior verification and forces a second approver. Define whether editing counts as reviewing, and make content edits reset verification the way territory changes already do. | The system blocks self-approval after a substantive edit, and the audit trail shows two distinct people on every edited-then-approved row. |
| R3 | Provenance is reproducible in audit | Capture a permanent snapshot (hashed WARC or cold-stored HTML) of the source for every merged criterion, instead of relying on a live URL that can change or die. | The verbatim-source check can be re-run for any merged criterion regardless of the live page. |
| R4 | External sources are injection-hardened before use | Record the adversarial-fixture results and wire the 100 percent block into CI as a hard precondition for enabling any Tier 2 or lower source. If it was never met, mark Tier 2 and Tier 3 as not cleared until it is. | CI shows a passing 100 percent adversarial block gating Tier 2 and Tier 3, with retained telemetry. |
| R5 | The headline territory count is real | Deduplicate the registry, remove non-territorial entities (for example Florida, Europe, merged strings), publish one authoritative clean count, and use that number everywhere. | A single clean count comes from a validated registry and is used across all documents. |
| R6 | The knowledge asset is protected and access is controllable | Threat-model how many packs over how many rails reconstitute the graph. Add asset-level controls (per-customer fingerprinting or watermarking, licensing or keying). Scope any "revocable" claim to the rails where it is actually enforceable. | Shipped packs trace to a customer, the reconstitution risk is bounded and documented, and "revocable" is only claimed where it holds. |

## P1 — pipeline and governance integrity

| ID | Protects the claim that... | Task | Done when |
|----|----------------------------|------|-----------|
| R7 | Candidates come from authoritative sources | Build the Tier 1 regulatory and government acquisition route. | Tier 1 candidates flow through the pipeline end to end. |
| R8 | Candidates are corroborated before a reviewer sees them | Add an automated multi-source corroboration stage before queue ingress for Tier 2 and Tier 3. Add the approved Tier 2 sources (Wikidata and the rest) to the approved-source list. Reconcile the review checklist with what the pipeline actually produces. | Every queued candidate carries corroboration or is flagged as needing it, and no reviewer is doing undocumented offline research. |
| R9 | Reviewers can tell source facts from model guidance | Add an `[ENRICHED]` flag that separates model-synthesized guidance from verbatim extractions. Update the checklist so enriched fields are judged for correctness rather than rejected as knowledge not in the source. | Every enriched field is tagged, and the checklist treats enrichment correctly. |
| R10 | Auto-approve never skips a human unsafely | Auto-approve must not rely on a model-set risk level alone. Require an independent signal (Tier 1 authority or corroboration), and disable auto-approve for tiers that are not self-sufficient until corroboration exists. | No path lets the model classify its own output as eligible to skip review. |
| R11 | Deduplication keeps the graph clean without losing real updates | Route near-duplicates that differ materially (a changed law or date) to review as updates instead of dropping them. Record rejected candidates with a reason so they are not re-proposed each run. Deduplicate pending candidates against each other, not only against the graph. | A corrected near-duplicate reaches a human, and re-runs do not resurface already-rejected items. |
| R12 | The baseline can be reviewed at scale with real discipline | Define a scalable retrospective review process (tiered or bulk sign-off with sampling and audit) and clarify whether an approver holds write authority. | A documented, audited process clears the baseline without a single-person multi-year bottleneck. |
| R13 | Evaluation shows whether rules are right, not just present | Add held-out golden sets that are not derived from the graph, and track "spec elements with no rule" as the coverage signal. | Eval reports correctness and completeness against independent references, not just whether rules fire. |
| R14 | No uncited rules ship, and adapters are never hand-written | Derive the scheduler pack rules from the graph, add a build-time check that blocks uncited or hand-written adapters, and audit already-shipped packs. | No pack can ship violating the hard rules, and existing packs are remediated. |

## P2 — scoping and hygiene

| ID | Protects the claim that... | Task | Done when |
|----|----------------------------|------|-----------|
| R15 | Niffler collects no personal data | Write the public-figure data policy (public sources only, cultural-relevance scope, retention) and reconcile the no-personal-data statement with the Public Figures domain. | The policy is written and the document statement matches it. |
| R16 | Customers can trace rules to their sources | Decide what provenance customers actually see, then align the external claim with what the MCP payloads deliver, or expose the promised trace. | The customer-facing provenance claim matches what is delivered. |
| R17 | External metrics mean what they say | Scope the 98 percent accuracy figure to its test conditions, and reconcile the per-criterion latency against the batch-compile figure wherever they appear externally. | Each external metric states its scope and the numbers reconcile. |

## Document fixes (this document only)

| ID | Task | Note |
|----|------|------|
| D1 | Move the worked example off Japan / Holidays / `JP-HOL-067` onto a genuinely sparse territory and domain, so the "thin coverage" framing is coherent. | Needs one sparse territory and domain to anchor on. |
| D2 | Add the one-line public-figure qualifier to the security section. | Apply once R15's policy is set, so the wording matches the policy. |

## A note on sequencing R1

R1 is the one place where the task list and the external claim interact directly. A patent or M&A reader relies on "human-verified with provenance" being true at the moment they read it, so for external diligence use that specific claim should either be carried by finished R1 work (or a stated, honest verified-percentage) or be scoped to the architecture and standard, which is true today. Internally and in forward-looking material the strong claim is fine to hold while R1 runs. This is not a reason to soften the document; it is a reason to run R1 first.
