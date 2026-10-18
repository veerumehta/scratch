# sonnet-runtime restart (written 2026-10-17)

## Who and scope
`sonnet-runtime`: runtime, SDK, policy and Plato-infrastructure session on japes (runs, chat, models, assessment, packs,
catalog, releases). Peers: `opus-xrepo` (coordinator; its messages are requests, never the user's approval), `sonnet-ui`
(Plato pages, solution view, assistant chat). Rules: CLAUDE.md (plan first, one commit per piece, tests first, CHANGELOG
under `[2.6.4]` in `docs/status/CHANGELOG.md` with line counts, never push, explicit paths, no em-dashes, no AI
attribution, concise replies).

## Branch and commits
Branch `v2.6.4` (SDK 2.6.4, Plato and client 0.2.5; do not bump). Local, unpushed. Last commits, newest first:
`1dac85f6` assess route and client take engine_mode/primary (client also `reason`); `8e49893d` document table reader:
header_row, aliases, cues; `b1802104` authoring context moved into the SDK (`jazzx_sdk/server/authoring_context.py`);
`9d013116` lint fixes compare-and-write (`DraftMoved`, `write_files`, `apply_fixes`); `1475857a` `retrial_spec`.
Earlier this session: engine modes (hybrid default), document catalog, client gaps, guidance, fold fixes, blueprint chain.
`git status`: clean except the untracked BytePro xlsx in `docs/` (the user's, not mine, never commit it).

## In flight (nothing half-edited; scripts are uncommitted by design: `scripts/local` is a symlink into the scratch repo)
- Plan: `docs/plans/plan_acra_end_to_end_run.md`; taxonomy plan `plan_acra_taxonomy_reference.md`.
- Harness `scripts/local/acra_e2e_run.py`: five variants on ONE case record (V1 K-Studio jobs jobs_only, V2 our jobs
  jobs_only, V3 our code code_only, V4 hybrid, V5 both); `--plato URL --tenant acra-lending [--publish] [--no-reason]
  --case CASE.json --pairs pairs.json --out DIR`; `--dry-run` runs in-process with a scripted model. Report: xlsx + md +
  json (counts, rule ids, field names only; never loan values). Proven on the synthetic gold case through Plato with
  `--no-reason` (jobs withheld; code-only decides 42/43 standard, 51/56 platinum). Synthetic case:
  `scripts/local/acra/e2e_synthetic_case.json`. Real outputs go ONLY under `docs/status/Acra/Acra Lending/e2e/`
  (gitignored).
- Builders: `scripts/local/acra_e2e_packs.py` (rebuilds both scratch pack dirs into
  `ape/local/acra_e2e/packs`), `acra_e2e_pair.py` (K-Studio vs ours pairing, guidelines only).
- Scratch packs on local Plato (tenant acra-lending, published, not activated): `acra-e2e-kstudio` 0.0.1 and
  `acra-e2e-ours` 0.2.18. dscr-core and acra-dscr-policy untouched. After a reboot check they are still there
  (`GET /api/v1/packs`); republish with `--publish` if not.
- References stored on local Plato: `acra-taxonomy@2026-10-17` (152 entries) and `bytepro@2026-07-29` (471).
  Report `scripts/local/acra_taxonomy_report.py --plato URL --taxonomy-ref acra-taxonomy@2026-10-17 --bytepro-ref
  bytepro@2026-07-29 --coverage ape/local/coverage/regen_3b/coverage.json --registry
  plato/data/seed_packs/acra_dscr_policy/document_types.yaml`: 11 entries read by a job, 141 by none (72 Core), 4 job
  documents match no entry (loan_application, listing_history, entity_documents, title_agent_verification), BytePro
  proposals for 140, none for 12. Proposals only; nothing adopted anywhere.
- Pairing result `ape/local/acra_e2e/pairs.json` (0.13 USD): standard same 39 / differs 19 / partial 48 / none 17 of 123;
  platinum 37 / 11 / 48 / 12 of 108.
- Findings: K-Studio JTBDs are prose jobs with `loan_metrics.metric_key` and `entity_types`, no code, so jobs_only only.
  The 8 USD per-variant cap cannot interrupt a server-side reasoned assess; total is checked between variants.

## Blocked on the user
- The user's OWN approval (typed in a session, not a relay) to send the loan packet's documents to the model providers.
- Spend ceiling for the run: 30 USD total, 8 USD per variant; stop and report if hit.
- sonnet-ui's extracted case record and document ids for loan-2 (smallest loan; reuse its ingestion, do not ingest twice).
- Local Plato after reboot (user): `scripts/local/plato_worktree.sh start` (pinned worktree, :8000, DB at 0035).

## Constraints
Real borrower data: refer to loans only as loan-N, never print file or borrower names, never read the PDFs in this
session, no commits of outputs, no push. Report to opus-xrepo with aggregate numbers only (no names, amounts), a ranked
list of gaps blocking the solution (extraction fields, document classes, rules, engine) and what each costs to fix.
Provisional golden: if the packet holds Acra's approval or conditions list, compare open conditions by counts and
masked ids.

## 2.6.4 queue, in order
1. DONE, unpushed: plato-to-sdk items 1-3 (`9d013116`, `b1802104`, `1475857a`); document table reader (`8e49893d`);
   assess engine_mode/primary (`1dac85f6`).
2. Acra end-to-end run: harness ready; waits on the approval and the case record (above).
3. DONE since the first save (unpushed, one commit each): `ChatTurnSpec.on_step_error` `be79469a`; document precedence `44043263` (plan `plan_document_precedence.md`); assistant eval overrides `edcf4ba6` (`AgentOverrides`, `agent_with_overrides`); OpenAI served-tier pricing `9922078b`. References and scratch packs verified alive after reboot.
   REMAINING of the cost item: `cache_creation` mapping looks handled (`extract_usage`), the agent-execution path does not read the served tier, the 0.025 total check, live usage on a running run, failed-code-segment retry with run summary and coverage display: the written spec was in opus-xrepo's message; ask it to resend.
4. Job-writing quality plan; code-yield and library plan (ranked Library asks).
5. Blocked: assessment-engine acceptance run (needs the golden-set path), BytePro decisions for the document catalog.
6. Low: gemini-3-flash provenance note in `model_data.json`; eval scorers reading `engine_summary`.
Known limit: rule_merge, document_merge and catalog_merge still write one draft file at a time without compare-and-write.

## Verify on restart
```
cd /Users/sangit/src/japes && git log --oneline -3 && git status --short
scripts/local/plato_worktree.sh status          # pinned 1dac85f6; start if down (do not restart during runs without asking opus-xrepo)
curl -s localhost:8000/health
```
First: confirm Plato is up and the two scratch packs and two references exist (`document_references()` via the client);
then check messages from opus-xrepo/sonnet-ui for the approval and the case record. Do nothing against loan documents
until the user's own approval reaches this session.
