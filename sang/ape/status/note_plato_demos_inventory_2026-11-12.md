# Plato demos: what the repo already has (D1 inventory, 2026-11-12)

Author: Virendra Mehta <virendra.mehta@jazzx.ai>. Inventory only; it decides nothing. Costs are estimates from the prompts and
`jazzx_sdk/llm/model_data.json` (gpt-5.2: 1.75 USD in, 14.0 USD out per million tokens); no provider call was made. Manifest format:
`plato/demos.py`, files `plato/data/demos/<id>.yaml`.

| Demo | Shows | Packs it needs | How to run today | Cost |
|---|---|---|---|---|
| **Vocabulary growth** (manifest written) | Three invented policy excerpts imply new catalog entries and two conflicts; a run proposes, a person approves, merges, publishes, compares | `mortgage-vocabulary-demo` (seeded) | Ontology page: open the draft, choose the three documents, start the run, review, merge, publish, compare | About 0.002 USD a run, measured by sonnet-runtime on four runs; minutes of wall time when the provider rate-limits |
| **Acra DSCR jobs and code** (manifest written) | A published pack's jobs as one list with what decides each, and the rules of a version | `acra-dscr-policy` (seeded) | Coverage page, then Code page; neither reads a query string, so the pack id is typed | Free: the pages call no model |
| `examples/adjudication_demo` | An `AdjudicationAgent` checks per-segment obligations on a toy lending case, expression rules directly and natural-language rules by a model | None (code in `harness.py`, spec `adjudication.yaml`) | `python -m examples.adjudication_demo.harness` with a key for gpt-5.2; no Plato page | Three natural-language conditions, one replica: about 3 calls of a few thousand tokens, so a cent or two (unmeasured) |
| `examples/loan_assistant` | An `InteractiveAgent` from a profile: persona, a scoped skill, guardrails | None (profile in the folder) | `python -m examples.loan_assistant.harness` with a key for claude-sonnet-4-6; the Assistants page serves an assistant pack, not this profile | A few cents a conversation (unmeasured; claude-sonnet-4-6 has no price in the model data) |
| Bundled assistant pack (`plato/data/demo_pack`) | Two declarative skills (`medication_capture`, `symptom_probe`) and a persona, no Python | It is the pack a replica serves with no configuration | Assistants page, chat | Per turn, a model call; model set by the replica's default (unmeasured) |
| Policy to pack (document extraction) | Policy documents become jobs and code in a pack's draft | `acra-dscr-policy` or a new pack; the guideline documents are the input | Packs page "start document extraction", Extraction page for the run | The heaviest of the pack demos: a guideline is dozens of pages, one call per chunk, then job, code and verifier stages; dollars, not cents (unmeasured; the Acra regeneration ledger has the measured figures) |
| Acra assessment walk-through | A case's runs, what decided each job and on what evidence | `acra-dscr-policy`; input is a loan file | Runs page after an assessment run | Needs borrower data, which this repo never opens; the seeded `fixtures/` (appraisal, credit report) are the only demo-safe inputs; a run is a provider call needing the user's typed approval |
| Spreading (`ci-spread-core`) | A 10-K to a spread workbook | `ci-spread-core` (seeded) | A pipeline run with documents | Multi-document, multi-stage; dollars (unmeasured); needs a public filing as input |
| `examples/document_analyzer`, `examples/basic`, `examples/formal` | A queue handler and Knowledge Hub documents; a minimal handler; an SMT contradiction check | None | Their READMEs | Not Plato demos: they need a queue or Knowledge Hub, or run offline (`formal`) |

## Reading this

- The two free demos need no key and no loan data, so both can be rehearsed in a room with no network: Acra jobs and code first.
- The vocabulary demo costs almost nothing in money; its risk is the rate-limit delay, which is why replay (a `recorded` file) matters. No recording exists: sonnet-runtime's retest kept only ids and stability, and a recording needs one run with the dump script and the user's typed cap (sonnet-runtime proposed 0.05 USD).
- The adjudication and loan-assistant examples are code-first and would need a Plato page or route to become a menu entry; as manifests they could only name a command. D4 should decide whether a demo may carry a shell command step (the schema has no field for one).

## Not verified

- That the Coverage page lists the seeded Acra pack's jobs without a published job set: the pack carries `policies/jobs.yaml` (48 ids), but the page was not opened against a fresh tenant.
- That the Packs page shows `acra-dscr-policy` after boot seeding (D2's prepare makes it so for a demo).
- claude-sonnet-4-6 and the Assistants default model have no entry in the model data, so those estimates are order of magnitude only.
