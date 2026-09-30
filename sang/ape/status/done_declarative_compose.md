# Plan: declarative compose for the chat lifecycle

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

Status: done. K0-K3 built on `v2.5.7` 2026-09-30 (`16e230bf` K0, `378cc703` K1-K3, review fixes
to `e037e55c`), full-range review (`6ec19406..e037e55c`) clean after 4 rounds;
Q1-Q4 decided as recommended. Plan dated 2026-09-30. Follows `status/done_declarative_grounding.md` (ground is
declared; compose is the next open item named in `plan_chat_runtime_coordinator.md` C7). Prior
art read first: `status/done_chat_turn_engine.md` (the `compose` step id, unbound by default;
jazz's `_compose` as an override), `plan_chat_runtime_coordinator.md` ("compose kinds: identifier
humanizing, leak checks as output guardrail kinds, an email draft as a declared output schema"),
jazzx-assistant `origin/dev` `engine.py::_compose` and `identifier_leaks`.

## What exists

japes:
- The `compose` stage: unbound unless a component is given; a bound one takes the branch's
  `InteractiveResponse` and returns the one delivered. `finalize` returns it.
- Citations: every grounded source's `Source`s join the reply (`GroundedContext.citations`), used
  or not.
- Output guardrails (`guardrail_kinds`, `policy_keywords`): run inside the agent on the answer
  text, before compose, and can only block.
- A declared output schema: `InteractiveAgentSpec.output_schema` names a registered model, so a
  structured reply (an email draft) is already data.
- `GroundedSource` knows each file's display label only through its manifest text and citations.

jazzx-assistant `_compose`, step by step:
1. The chat text is the answer field of the structured reply, or a fixed note when the turn was a
   pure email draft.
2. Grounding filenames become display names in the answer, the draft subject and the draft body
   (`humanize_sources` over `grounded.mappings`).
3. Citations are built from what the answer cites, not from everything grounded.
4. Draft recipients are overwritten from the grounded LOS record.
5. Leak checks: finding mnemonics and named LOS records in any delivered surface. Detection
   only: logged, traced with a count (0 included) so a compliance rate is filterable, never
   rewritten.
6. The reasoning relay is flushed before the final frame (a runtime concern; not compose data).

## The design

One concept, the twin of a ground source: a **compose step**, declared with a `kind`, that
transforms the turn's response. Steps run in declaration order (a chain, where ground sources
are concurrent), over the response's **surfaces**: the answer text plus any string fields of the
structured output a step names (`output.subject`, `output.body_markdown`).

```yaml
lifecycle:
  compose:
    steps:
      - {kind: present, field: answer_markdown, fallback: "I've drafted an email for you."}
      - {kind: cite}                                    # only the sources the answer cites
      - {kind: humanize, surfaces: [answer, output.subject, output.body_markdown]}
      - {kind: leak_check, name: los_names, sources: [los], action: report,
         surfaces: [answer, output.subject, output.body_markdown]}
```

### K1. Kinds, request, result (`jazzx_sdk.pipelines.compose`)

- `ComposeKinds(NamedRegistry)`, entry point `jazzx_sdk.compose_kinds`, built-ins first and not
  overridable, then frozen; a kind installed with the wrong shape is logged and skipped. The
  loader is shared with `ground_kinds` (see Q4).
- A kind: `problems(config) -> list[str]` and `async apply(request) -> ComposeResult`.
  `ComposeRequest`: the response, the turn's `GroundedContext`, the message, the scope, the
  step's config. `ComposeResult`: the new response, plus the step's `DeliveryCheck`s.
- `DeliveryCheck(step, kind, passed, surfaces: {surface: [items]}, detail)` goes on
  `InteractiveResponse.checks` (new) and on the compose span's attributes, count always set.
- Steps apply to an answered response; a blocked, refused or failed one passes through.

### K2. Built-in kinds

- `present`: the chat text is `output.<field>` when set, else `fallback`; the structured output
  stays on `response.output`. The draft-vs-answer split, as data.
- `cite`: the reply's citations become the grounded `Source`s whose file name or label a surface
  mentions, in order of first mention; `sources:` limits which sources count. An answer citing
  nothing keeps none, and says so in a check.
- `humanize`: each grounded file name in a surface becomes its display label. Needs the
  mapping as data: `GroundedSource.names: {file name: label}`, filled by `documents` and
  `entities` (they compute both today).
- `leak_check`: identifiers in a surface. Identifiers come from `sources:` (their file names and
  labels) and/or `patterns:` (regexes). `action: report` (default; a failed check, logged and
  traced, text untouched), `redact` (replaced by `replacement`), `block` (the response becomes a
  refusal with `message`).
- Recipients-from-LOS stays jazzx's: a registered kind, since which record holds an email address
  is domain data. (A generic `set_field` from a grounded record is the obvious extension; not
  built until a second consumer needs it.)

### K3. Declaration and hosting

- `ChatLifecycleSpec.compose: {steps: [...]}`, each step `extra="allow"` with `kind` and the
  kind's own keys, checked by the kind. `declared_lifecycle` compiles it into a `ComposePlan`;
  `DeclaredLifecycle.components` binds `compose` when steps are declared.
- A surface naming an output field needs a declared `output_schema` with that field: lint.
- Plato: nothing new beyond passing the plan through; pack check reports a step that does not
  check as `invalid_lifecycle`.

## What jazzx-assistant changes

Its `_compose` becomes four declared steps (`present`, `cite`, `humanize`, `leak_check` twice:
mnemonics by pattern or a findings source, LOS names by source) plus one registered kind for
recipients. `DocumentMappings` becomes `GroundedSource.names`; `AnswerResult`'s citations,
text and draft come off the composed `InteractiveResponse`; the leak counts ride `checks`.

## Open questions

- Q1 `cite` narrows citations to what the answer cites. Without a declared `cite` step the reply
  keeps every grounded source's citations, as today. Recommend: yes, opt-in.
- Q2 Streaming: `humanize` and `redact` rewrite the final response; deltas already streamed
  carry the raw file names. Recommend: final-only, documented (a UI renders the final event), and
  a buffered delta rewriter only if a consumer needs raw-free deltas.
- Q3 `InteractiveResponse.checks: list[DeliveryCheck]` for step results. Recommend: yes.
- Q4 One kinds loader for ground and compose now, and move the conductor, guardrail and evidence
  registries onto it, which closes `TODO(entry-point-kind-shape-unchecked)` (shape checks and
  load errors for all five, one cache). Recommend: yes, as K0.
