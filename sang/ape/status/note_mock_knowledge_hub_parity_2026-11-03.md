# Mock Knowledge Hub parity: what the HTTP mock lacks (sonnet-runtime, 2026-11-03)

Measurement for plan item 23 ("measure what the mock lacks before building"). Method: the routes the mock app declares
(`jazzx_sdk/server/mock_knowledge_hub_app.py`, `@app.<verb>("<path>")`, 13 declarations) against the routes the installed generated client
(`knowledge_hub_client/api/**`, the `"url"` of each `_get_kwargs`) can call, with path parameters normalized. Run on this checkout's venv client; a
different pinned client revision may differ.

- The generated client reaches **113 distinct paths**. The mock serves **12 of them** (collections read and download, documents list, the v2 document download and async
  download, reasoning entities and ontologies, the task routes), plus `/`. It serves no path the client lacks.
- Missing by area (paths): reasoner 16, collections 14 (v1) and 8 (v2), registry 11, reasoning 11 (v1) and 5 (v2), mappings 10, fs 7, **taxonomies 6**, **prompts 6**,
  audit 4, global-config 2, and two health routes.
- The plan's named items: **versioned taxonomy and prompt APIs** are the two areas above with all six paths missing (list, read, drafts, versions). **Update validation**
  (the 2026-09-02 finding), **synthetic-object marking**, **imdoc hiding** and the **pipeline filter** are behaviours of routes the mock either serves loosely or does not
  serve; I did not open the real service to say what they should answer, so they are not measured here.
- `MockKnowledgeHubClient` (`jazzx_sdk/clients/mocks.py`, the in-process mock most tests use) is a separate surface from the HTTP app and was not compared.

## Reading

The HTTP mock is a small stand-in serving about a tenth of the client's paths. Building parity for all of it is large; building the two versioned APIs is six routes each plus their state. No consumer has been named that calls them against the
mock, so nothing is built. If one is, the order that costs least is taxonomies then prompts (same draft, version and publish shape), validated against the real service's
responses, which needs the real service.
