# plan_PLATO_REGULATED_DEPLOYMENTS

Author: Virendra Mehta · 2026-11-12 · Status: not scheduled

## Status and modifications

How to use this section: the plan author may read and update it; implementers append one dated line per slice (what landed, the commit, anything the plan got wrong). Newest line last.

- 2026-11-12 drafted from the discussion of Plato for regulated banks and a read of `main` (SDK 2.7.0, Plato 0.3.0). Not planned for the current cycle; kept so the work is ready when a bank deal needs it. The Notion page "Plato for Regulated and On-Premises Deployments" (04 · Engineering Workstreams) holds the reasoning.

## Goal

Let Plato run where a regulated bank requires: in the bank's own cloud account or in its data center, possibly with no internet. Protect our IP as far as that allows:

- Authoring and learning stay in JazzX's cloud.
- The bank runs a signed, licensed Plato and signed pack versions.
- Nothing depends on reaching us at run time.

## Before starting

Verify in this order:

1. The latest CHANGELOG entries.
2. This plan.
3. `plan_JAPES_NOV10_ROADMAP_ENABLERS.md` (A4 model per role, E5 cost report).
4. `plan_JAPES_2_6_0_CONFIG_VERSIONING_AND_AUDIT.md` (pack versions and rollback).
5. The source.

## Deployment options this plan serves

| Option | Who runs it | Data leaves the bank | What changes for us |
|---|---|---|---|
| 1. Tenant on our Plato | JazzX | Yes | Nothing new |
| 2. Dedicated Plato in our cloud, bank's region | JazzX | Yes, to a fixed region | Region pinning only |
| 3. Plato in the bank's cloud account | JazzX, with bank access rules | No | Slices P1 to P7 |
| 4. Plato in the bank's data center, maybe offline | The bank | No | P1 to P9 |

## What exists on main

- **Pack archives.**
  - Plato accepts a pack archive upload, checks its manifest and guideline pin, publishes, activates and rolls back (`plato/api/packs.py`).
  - Archives carry no signature, and nothing checks who built one.
- **Azure dependencies.**
  - Reached through `jazzx_sdk/queue/processor.py`, `jazzx_sdk/runtime/`, `jazzx_sdk/fabric/blob/store.py`, `jazzx_sdk/fabric/config.py`, `jazzx_sdk/tools/documents/docintel_azure.py` and `plato/wiring/default.py`.
  - Packages: `azure-storage-queue`, `azure-storage-blob`, `azure-identity`, `azure-ai-documentintelligence`, `azure-monitor-opentelemetry-exporter`.
  - Document reading has a page engine with fallbacks (`tools/documents/pages/engine.py`).
- **Tenancy.**
  - Plato is multi-tenant.
  - `plato/wiring/default.py` serves a single default tenant only for unconfigured local runs.
- **Models.**
  - Model choice, pricing overlays and routing live in `jazzx_sdk/llm/` (`routing.py`, `selection.py`, `gateway/`, `model_overlay_db.py`).
- **Not present:** a license check and a diagnostic bundle.

## Slices

### P1. Signed pack versions

- **Sign.** JazzX's build signs a pack archive: a detached signature over the archive digest, plus the signer's key id in the manifest.
- **Verify.** Plato verifies on upload and on load against trusted keys from configuration.
  - Unsigned or wrongly signed archives are refused when `require_signed_packs` is on.
  - The setting is on by default for options 3 and 4.
- **Intent.** The bank can prove a pack came from us unchanged. We can prove the bank runs what we shipped.
- **Acceptance:**
  - A signed archive publishes.
  - One changed byte is refused with the reason.
  - A key not in the trusted set is refused.
  - With the setting off, local development is unchanged.

### P2. Offline pack and release bundles

- **Bundle.** One file holds pack versions, their signatures and release notes, imported through a Plato command or route with no network access.
- **Import behavior.**
  - Import is all or nothing.
  - Existing versions are kept, so rollback works across imports.
- **Intent.** Packs carried into an offline site by hand, through the bank's change process.
- **Acceptance:** an import on a host with no internet publishes three pack versions; a bundle with one bad signature imports none.

### P3. Single-company mode

- A Plato setting for one company:
  - one fixed tenant
  - tenant creation routes off
  - plato-client calls that name another tenant refused
- Keep tenant isolation code paths as they are; this only narrows what is reachable.
- **Acceptance:**
  - With the mode on, a request for another tenant is refused.
  - Tenant admin routes are not served.
  - Existing multi-tenant tests pass with the mode off.

### P4. Replacements for Azure dependencies

- **Interfaces.** Put each Azure use behind an interface Plato already has or gains: queue, blob store, secrets, document reading, telemetry export.
- **Second implementations.**
  - Queue: a Postgres-backed queue (Postgres is already a dependency).
  - Blob store: filesystem or S3-compatible store.
  - Secrets: environment and file secrets, or HashiCorp Vault.
  - Document reading: the non-Azure page engine path.
  - Telemetry: OpenTelemetry to the bank's collector.
- **Configuration.** Selection by configuration. Azure stays the default.
- **Intent.** Option 4 on Kubernetes or OpenShift without Azure. Option 3 on Azure keeps today's path.
- **Acceptance:**
  - A Plato image with no Azure credentials and no Azure SDK installed runs a pack publish, a document upload with extraction, and a case run against Postgres and a local blob store.
  - The Azure path still passes.
- **Not verified:** which SDK modules import Azure packages at import time rather than lazily. Check before the first slice.

### P5. Platform services in a bank install

- **Inventory.** List every external service Plato calls in a case run and a chat turn: Knowledge Hub, Kernel, Flowable, Evaluation-service, the LLM gateway. For each, state:
  - ships with the install
  - optional, and what stops working without it
  - replaced by an SDK path
- **Health report.** `/info` reports which are configured and reachable.
- **Intent.** A bank install is a known set of containers, not a discovery exercise.
- **Acceptance:**
  - The inventory is committed in `plato/guide`.
  - With Kernel and Evaluation-service absent, Plato starts, reports them unavailable, and serves packs and case runs.

### P6. The bank's model endpoints, and a qualification run

- **Endpoints.** Model endpoints per role from configuration, including the bank's own (Azure OpenAI in their account, or a self-hosted model). Builds on A4 of `plan_JAPES_NOV10_ROADMAP_ENABLERS.md`.
- **Qualification run.** Runs a pack's gold cases and rubric on the bank's models before go-live, against our reference results, and reports per-case differences, cost and latency.
  - It writes a report the bank's model-risk team can file.
- **Spend.** Every model-backed run needs a typed approval with a dollar figure in the session that runs it.
- **Acceptance:** pointing one role at a different model and running qualification on a test pack produces a report with per-case deltas, and blocks activation when a pass bar fails.

### P7. Diagnostic bundle without customer data

- **Contents.** A Plato command writes a bundle for support:
  - versions and configuration with secrets removed
  - recent errors, with `redact_secrets` and the pack's obfuscation map applied
  - run metrics and health
  - no case data, prompts or model outputs unless the bank turns that on per bundle
- **Acceptance:** a bundle from a test install contains no value from the obfuscation map and no secret, and lists what was left out.

### P8. Offline license check

- **License file.** A signed license file lists:
  - the company
  - allowed packs and versions
  - an expiry
  - optional limits, such as cases per month
- **Checks.** Plato checks it at start and daily, with no network call.
  - Near expiry, Plato warns.
  - Past expiry, it serves read-only (records, audit, export) and refuses new runs.
- **Usage report.** A usage report is exported for renewal; nothing is sent to us.
- **Acceptance:** an expired license refuses a new case run and still serves a record read; a tampered file is refused at start.

### P9. Hardened image

- **Build.**
  - Release images ship compiled modules for the SDK and Plato (Cython or Nuitka), with no source files and no docstrings.
  - A software bill of materials ships with each image.
  - Images are signed.
- **Intent.** Raise the effort to read our code at a bank-run site. This is the last layer, not the protection itself: prompts, packs and traces stay readable by design.
- **Acceptance:**
  - The image runs the full test suite's smoke set.
  - No `.py` file from `jazzx_sdk` or `plato` is present except entry points.
  - The bill of materials lists every package.
  - The image signature verifies.

## Order

1. P1, P3 and P5 (useful for option 3 on Azure).
2. P6.
3. P7.
4. P2, P4, P8 and P9 when an option 4 deal is real.

## Decisions for the user

1. **Which options we offer** first, and whether option 4 offline is in scope at all.
2. **Signing.** Key custody and rotation for packs, images and licenses: which team holds them and where.
3. **Base packs at bank sites.** Ship agency guideline base packs to bank-run sites (readable there) or only bank-specific packs.
4. **Cross-bank learning.** Whether, with a bank's consent, corrections can flow back to improve shared packs.
5. **Confidential containers.** Whether to support Azure confidential containers with key release to an attested image for banks that accept them.

## Out of scope

- Contract terms (license, reverse-engineering clause, escrow, output use).
- Running a bank's models.
- Bank security reviews and penetration tests.

## Not verified

- Which SDK modules import Azure packages at import time.
- Whether Plato's background jobs (run reaper, sweeps) depend on Azure queues.
- How Flowable is deployed today and whether a bank install can include it.
- Whether the gateway client accepts a custom endpoint per role.
