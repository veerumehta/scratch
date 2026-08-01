# plan_JACI_COMMERCIAL_LENDING_LIVE_WIRING

Author: Virendra Mehta
Date: Friday, July 3, 2026
Status: SUPERSEDED (2026-07-15) by plan_JACI_CL_SURFACES_EXPERTS_AND_WRITEBACK.md.
  Shipped from this plan: Phase 0 submodule intake (web/commercial-lending-demo @ 34a1666), SPA served
  from the existing `server` run shape (not a new `web` shape), settings/scenario routers, /scenario.json,
  badge overlay, multi-stage Dockerfile. The badge -> cre-underwriting operation is the only live
  integration. NOT built and now obsolete: the `web` run shape (dropped by decision — rides `server`),
  the /api router (web_api.py), and the runtimeConfig.ts / JACI_WEB_MODE submodule seam. The surfaces
  plan rebuilds the API against the corpus openapi.json contract shapes (GovernedRouter), replacing this
  plan's ad-hoc endpoint list (assess/verify-evidence/trace). Do not implement the remaining phases here.
Repos touched: jaci (primary), commercial-lending-demo (Phase 0 submodule source and Phase 4 seam adapter)
Repos NOT touched: japes. Nothing under jazzx_sdk/ changes in this plan.

## Context and decision

commercial-lending-demo at /Users/sangit/src/commercial-lending-demo is a Lovable-built Vite + React + TypeScript SPA with three scripted scenarios: CA (credit analyst), PM (portfolio manager), and CID (commercial insurance diligence). It is a pure frontend. All state lives in React contexts, all AI moments are choreographed with hardcoded fixtures and setTimeout transitions, and there are no network calls anywhere in the app.

Decision: the demo will be shown connected to JAPES via the jaci repo. The Lovable frontend comes into jaci as a git submodule (chosen over pyproject wheel packaging and plain cp, rationale below). JACI serves the built SPA plus a scenario API from a new `web` run shape, deployed to dev-daily as a sibling ACA app from the same image. Over time the demo transitions scenario by scenario into native Streamlit views the way ins_diligence was crafted from the CAandPM export, and the submodule retires when the last route ports.

Why submodule and not the alternatives:
- Plain cp repeats the docs/plans/CAandPM problem: a 6.8 MB dist snapshot with no record of which demo commit produced it, full hashed-bundle churn in git history on every refresh, and manual refresh.
- A pyproject dependency (git tag carrying a built dist, installed like japes) is the best pure serving mechanism but ships only minified bundles. The Streamlit transition needs the TypeScript source, fixtures, and copy as reference material for Claude Code. It also makes refresh a deliberate tag-and-pin ceremony, which conflicts with the requirement that the intake keeps refreshing as changes land in the demo repo.
- A submodule provides source access for the transition, exact provenance (the gitlink records the demo SHA), an automatable one-command refresh, and the Docker build produces the servable SPA from it. Since the SPA is a transitional artifact that shrinks as Streamlit views land, do not invest in wheel packaging for it.

Core design principle: the JAPES wiring lands in the JACI scenario API, not in either frontend. The React SPA now and the Streamlit views later consume the same /api endpoints returning Decision, Evidence, policy clause references, and trace ids. The Streamlit port is then purely presentational.

Dependency direction is preserved throughout: React SPA -> JACI scenario API -> JAPES. The frontend never imports or calls jazzx_sdk directly.

## Phase 0: submodule intake and refresh process

### 0.1 Add the submodule

In the jaci repo root:

```
git submodule add https://github.com/<org>/commercial-lending-demo.git web/commercial-lending-demo
```

Pin to a specific SHA (the current main head at time of intake). The path is `web/commercial-lending-demo` so the eventual `jaci/web.py` and the Docker build stage have a stable anchor.

### 0.2 CI checkout changes

File: .github/workflows/* (every workflow that builds the image or runs tests touching the web shape).

Change actions/checkout to fetch the submodule:

```yaml
- uses: actions/checkout@v4
  with:
    submodules: recursive
    token: ${{ secrets.GH_PAT_JAPES }}
```

Use the same PAT/token that already authorizes the private japes install. If the checkout token cannot read the demo repo, extend that token's scope rather than minting a second secret.

### 0.3 Refresh process

Two mechanisms, both required:

Makefile target (manual refresh during active work). Add to the jaci Makefile:

```
refresh-demo:
	git -C web/commercial-lending-demo fetch origin
	git -C web/commercial-lending-demo checkout origin/main
	git add web/commercial-lending-demo
	git commit -m "chore: bump commercial-lending-demo to $$(git -C web/commercial-lending-demo rev-parse --short HEAD)"
```

Nightly bump job (automated refresh). Add a scheduled workflow step (or extend the existing nightly) that runs the same sequence, builds the image, and only pushes the gitlink bump commit if the image build and the smoke check in Phase 5 acceptance pass. A failed demo build must never advance the pin; dev-daily keeps serving the last good SHA.

Design intent: the pin is always a known-good SHA and the commit message carries the demo short SHA for provenance. This is the governed replacement for the CAandPM hand-copy.

### 0.4 Retire the CAandPM snapshot

Once the web shape serves on dev-daily, delete docs/plans/CAandPM in a standalone commit. Its only remaining value is historical and git history preserves it.

## Phase 1: scenario API in JACI

### 1.1 New module: src/jaci/web_api.py

A FastAPI APIRouter mounted at /api. This is JACI scenario code, peer to the existing scenario modules, exercising JAPES modes through the same paths the Streamlit views use today (the CI Spread / CRE conductors and the CID assessment logic).

Endpoints (contract, not exhaustive signatures):

- GET /api/health. Liveness for ACA probes. Returns build info including COMMIT_SHA and the demo submodule SHA (bake the latter in at image build, see Phase 3).
- GET /api/config.json. Runtime config for the SPA: `{ "mode": "live" | "scripted", "apiBase": "/api" }`. Mode is read from env var JACI_WEB_MODE, default "scripted". This is how one built artifact serves both choreographed-demo and live-PoC behavior without a rebuild. Vite bakes import.meta.env at build time, so mode must NOT be a VITE_ flag.
- POST /api/cases/{case_id}/assess. Runs the relevant scenario mode for the case, returns the Decision with policy clause references, Evidence summaries, and the canonical trace id.
- POST /api/evidence/{evidence_key}/verify. Drives the CID evidence lifecycle for real: accepts the returned document reference, runs verification, returns the Evidence object state and trace id. This replaces the SPA's 1.6 second setTimeout in CIDDemoContext.startEvidenceReading.
- GET /api/traces/{trace_id}. Returns the canonical trace for the inspect-the-governed-trace moment in the UI.

### 1.2 Response shape discipline

The SPA's existing TypeScript interfaces are the de facto contract. AssistantInsight in src/contexts/AssistantContext.tsx (kind, title, body, confidence, confidenceLabel, sourceLabel, meta) maps onto Decision and Evidence fields. Mirror those field names in the API response models so the React adapter in Phase 4 is a thin fetch, not a transformation layer. Where a field is genuinely canonical (trace_id, clause refs), add it; do not rename the fields the UI already binds to.

Acceptance check for Phase 1: `curl -s localhost:8000/api/health` returns 200 with both SHAs; POST assess on a gold case returns a Decision containing at least one policy clause reference and a resolvable trace id.

## Phase 2: the web run shape

### 2.1 New module: src/jaci/web.py

A FastAPI app that composes:
1. The Phase 1 router at /api.
2. StaticFiles mount of the built SPA. Static dir resolution order: env var JACI_WEB_STATIC_DIR if set, else /app/web/dist (the image path from Phase 3), else web/commercial-lending-demo/dist relative to repo root (local dev after a manual vite build).
3. SPA fallback: any GET path not matching /api/* or a real static asset returns index.html so BrowserRouter deep links (/cid-highlights/:dealId and friends) survive refresh.

### 2.2 Dispatch in src/jaci/main.py

Add a fourth shape to the existing JAPES_RUN_MODE dispatch (current shapes: ui, server, queue):

```python
elif mode == "web":
    import uvicorn
    uvicorn.run("jaci.web:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
```

Design intent: this deliberately does NOT go through jazzx_sdk.serve. serve() knows ui (Streamlit) and handler (FastAPI /invoke) shapes; teaching it a static-SPA shape would be an SDK change for a single scenario's need. If the pattern recurs (Juno frontend, Jazz Assistant frontend), a serve(web_app=..., static_dir=...) enrichment becomes justified platform work. Record that as a JAPES roadmap input; do not implement it here.

Acceptance check for Phase 2: JAPES_RUN_MODE=web python -m jaci.main serves index.html at /, serves /cid-dashboard (deep link) as index.html, and serves /api/health as JSON.

## Phase 3: image and dev-daily deployment

### 3.1 Dockerfile changes

The current image is single-stage python:3.11-slim. Convert to multi-stage:

Stage 1 (new, first): `FROM node:20-slim AS webbuild`. Copy web/commercial-lending-demo, run `npm ci && npm run build`. The submodule must be checked out in the build context (guaranteed by 0.2 in CI; locally, git submodule update --init).

Stage 2 (existing python stage): after the existing COPY lines, add `COPY --from=webbuild /web/commercial-lending-demo/dist ./web/dist` and `ENV JACI_WEB_STATIC_DIR=/app/web/dist`. Also bake `ARG DEMO_SHA=""` / `ENV DEMO_SHA=${DEMO_SHA}` and have the nightly pass the submodule short SHA, so /api/health can report it.

Keep JAPES_RUN_MODE=ui as the image default. The web shape is selected per ACA app via env, same one-image-many-shapes philosophy the Dockerfile header already documents.

### 3.2 Healthcheck

The Dockerfile HEALTHCHECK targets Streamlit's /_stcore/health and the header already says to override for other shapes. For the web ACA app, configure the ACA probe (or container healthcheck override) to GET /api/health on $PORT.

### 3.3 dev-daily topology

Same image, two ACA apps:
- Existing JACI app: JAPES_RUN_MODE=ui (unchanged).
- New app, e.g. jaci-web-daily: JAPES_RUN_MODE=web, JACI_WEB_MODE=scripted initially, flip to live once Phase 4 lands and the gold-case smoke passes. Own ingress hostname, so Vite base stays '/'.

Note the SPA and API are same-origin by construction, so no CORS configuration is needed and no VITE_JAPES_API_URL is baked. The Anthropic key never leaves the server side.

### 3.4 Visibility inside the JACI Streamlit app

Register a Commercial Lending Demo scenario entry in ui/registry whose Demo tab renders a short framing paragraph plus a link button to the jaci-web-daily URL (env var JACI_WEB_DEMO_URL surfaced through settings). Linking out is preferred over iframing: the password gate, client routing, and html2pdf behave better in their own window. Do not iframe unless a stakeholder explicitly requires in-page rendering.

## Phase 4: React seam adapter (lands in commercial-lending-demo)

This phase is demo-repo work. Run it as its own Claude Code session in /Users/sangit/src/commercial-lending-demo; everything needed is described here.

### 4.1 Runtime config

New module src/lib/runtimeConfig.ts: on app boot, fetch /config.json (same origin). On 404 or network failure, resolve `{ mode: "scripted", apiBase: "/api" }`. Expose via a context or module singleton. This means the SPA still runs standalone under `npm run dev` and inside Lovable with zero backend, exactly as today.

### 4.2 API client

New module src/lib/japesClient.ts: thin typed fetch wrappers for the Phase 1 endpoints, using apiBase from runtime config. Response types reuse the existing interfaces (AssistantInsight and the CID lifecycle types) plus a traceId field.

### 4.3 Context seam

The contexts are the only integration boundary. Do not touch page or component code except where a trace id is newly displayed.

- src/cid/CIDDemoContext.tsx startEvidenceReading: when mode is live, replace the setTimeout with a call to japesClient.verifyEvidence(key); transition reading -> verified on response, and store the returned traceId per evidence key. When mode is scripted, keep the existing setTimeout path verbatim.
- src/contexts/AssistantContext.tsx: when mode is live, insights for the active category come from japesClient.assess (mapped one to one thanks to 1.2); scripted mode keeps the existing fixture flow. The app already ships @tanstack/react-query with an instantiated but unused queryClient; use it for these calls.

### 4.4 The governed-trace moment

Where an insight or verified evidence carries a traceId, render an "Inspect governed trace" affordance (link to /api/traces/{id} pretty-printed, or a modal). This is the demo's differentiator beat: the confidence badge stops being decoration and becomes a door into the canonical trace.

Acceptance check for Phase 4: with JACI_WEB_MODE=live on a local web-shape run, walking the CID flow produces evidence verification backed by real API calls, each verified item exposes a resolvable trace id, and with JACI_WEB_MODE=scripted the app is behaviorally identical to today's demo.

## Phase 5: Streamlit transition process

The end state is a fully native JACI experience and the submodule removed. The transition is scenario by scenario, following the ins_diligence precedent (crafted from the CAandPM export using the same UI elements).

### 5.1 Transition ledger

New file: docs/plans/COMMERCIAL_LENDING_TRANSITION_LEDGER.md. A table, newest first, with columns: SPA route, scenario, Streamlit view (module path once it exists), status (spa-only | porting | native | retired), demo SHA last reviewed. Seed it from the route table in the SPA's App.tsx (ca-*, pm-*, cid-* routes plus presentation and onboarding pages).

### 5.2 Port order

CID first (ins_diligence precedent exists and the CID lifecycle is the first thing wired live), then CA, then PM. Each port is its own small plan doc if nontrivial; simple views go straight to code.

### 5.3 Port mechanics

For each route: build the Streamlit view under ui/ consuming the SAME Phase 1 endpoints (no new backend work per port), register it in ui/registry, mark the ledger row native, and remove the corresponding link emphasis from the registry Demo tab. When every row for a scenario is native, remove that scenario's routes from the SPA in the demo repo (keeps the served bundle shrinking). When all rows are native or retired: delete the web run shape's static mount config, remove the submodule, drop the node build stage, and close this plan.

### 5.4 Refresh interaction with the ledger

The nightly bump job appends nothing to the ledger, but any manual `make refresh-demo` during active porting should be followed by a scan of demo-repo changes against ledger rows marked porting, so a port does not silently target stale UI.

## Out of scope

- Any change under jazzx_sdk/. The serve() web_app enrichment is recorded as a roadmap input only.
- MACER, Juno, Jazz Assistant.
- Auth hardening beyond the existing PasswordGate (fine for dev-daily; revisit for any client-facing environment).
- Wheel/pyproject packaging of the demo (explicitly rejected for this transitional artifact, see Context and decision).

## Acceptance summary

1. web/commercial-lending-demo submodule pinned; make refresh-demo bumps it with the demo short SHA in the commit message; nightly bump only advances on green build.
2. JAPES_RUN_MODE=web serves SPA + /api same-origin; deep links survive refresh; /api/health reports both SHAs.
3. dev-daily runs jaci-web-daily as a sibling ACA app from the same nightly image; JACI Streamlit registry links to it.
4. JACI_WEB_MODE toggles scripted vs live per deploy with a single built artifact; live CID flow returns real Evidence, Decisions, clause refs, and resolvable trace ids.
5. Transition ledger exists, seeded from App.tsx routes, CID marked as first port target.
