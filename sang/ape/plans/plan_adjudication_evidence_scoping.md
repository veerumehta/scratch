# Plan: evidence scoped per segment in AdjudicationAgent

Status: plan, not built. Branch `v2.6.3` (SDK 2.6.3), local, unpushed, no version bump.
Source: `note_parity_adjudication_20261012.md` gap 2 and rows 2.1, 2.3, 2.4; `note_sibling_parity.md` macer row 10-12;
`plan_programme_oct.md`. Prior art checked: `status/done_reasoner-chassis-analysis.md` (P4 workspace, P7 planner),
`status/done_design_note_p1_p2_sizing.md` (k=3 replicas bought no variance reduction: measure before defaulting),
`status/done_JAPES_1_9_X_DIRECTORY_BACKED_TOOLS.md` (`build_source_tools`). No earlier plan covers the step side.

## 1. The problem, as the code stands

- `steps.py:_run_adjudication` builds ONE `SegmentSpec(key=config.id, rules=live)` and puts every document class's full
  text in `context` (`_document_texts`, by class, all documents of the class concatenated).
- `segment.py:_render_batch_prompt` renders each live rule with `render_for_batch`, which calls
  `condition_evaluator._batch_evidence`: `context.get(field)` printed under each rule. A class read by k rules is
  inlined k times in the one prompt.
- `run_segment` calls `ReasoningAgent.run` with no `tools`. `EvidenceWorkspace`, `enforce_read_cap`, `PrecomputedGrounding`
  and `BrowseGate` exist and have no caller in `jazzx_sdk` or `plato`; `AdjudicationAgentSpec.mounts` and `.segments` are
  declared and unread (`TODO(adjudication-spec-fields-unread)`).
- A failed call (validator retries exhausted, transport) makes every rule in it INDETERMINATE
  (`failed_segments`), so one segment means one blast radius.
- Cost: `_MeteredService` adds every call to one `trace.usage["adjudication"]`; no per-segment figure.

## 2. Design

All settings are pack data in `adjudication.yaml` (new `evidence:` block on `AdjudicationAgentSpec`). Defaults keep today's
behaviour except E1 and E2, which change no verdict semantics. Nothing here names a consumer.

```yaml
evidence:
  mode: inline            # inline | tools
  read_cap_kb: 10         # tools mode: a read above it errors, the model pages
  max_turns: 30           # tools mode
  inline_min_chars: 2000  # E2: a field this long, read by two or more rules, is rendered once
  grounding: null         # E4: {source: <reference set>, top_k: 3}
  strict: false           # opt-in refusal, see 2.6
```

Named constants in the SDK for each default (no bare literals).

### E1. Segment by policy in the step

`_run_adjudication` groups `live` by the policy each rule came from (it already iterates `policies_in_force`) and passes
one `SegmentSpec(key=f"{config.id}:{policy_id}", rules=...)` per policy. `AdjudicationAgent` already fans segments out
(`fan_out`, `degrade=True`, `DEFAULT_SEGMENT_CONCURRENCY`), so a failed segment only INDETERMINATEs its own policy's
rules, and `impacted_rules` already narrows per segment on reruns. Trace span names become
`<step>:<policy>:adjudicate:<replica>`; `adjudication_name_patterns` matches by substring and keeps working.
A single-policy pack yields one segment, as today.

Not changed: the planner seam (`SegmentPlanner`) stays a pack extension; a pack with a planner supplies its own segments.
Cross-rule effects within one call (the model seeing sibling rules) are lost across policies; that is the intended trade,
and it is measured in the eval (section 5).

### E2. Render each evidence field once per segment

Keep the `render_for_batch` protocol unchanged. In `_render_batch_prompt`, before rendering, compute the fields read by
two or more live rules whose value is longer than `inline_min_chars`. Emit them once in an `EVIDENCE` section
(`=== <field> ===`), and render rules against a context where those fields are replaced by `(see EVIDENCE <field>)`.
Short fields (record scalars) and single-reader fields stay inline. Pure function, no model change; the saving is
(k-1) x field length for each shared field.

### E3. Opt-in tool mode in `run_segment`

`evidence.mode: tools`:

1. The step materializes the run's documents once into a temporary directory, one file per document named by its alias
   (`D1.md`, `D2.md`), with the same page markers `_document_texts` writes today (so cites and `_citations` are
   unchanged). It reuses `converted_document`, which already checks the pinned digest. The directory lives for the step.
2. The class-to-document map goes into the prompt as a short index (`class X: D1, D3`), replacing the inline text a rule's
   `reads` would have pulled in. A rule's block says which classes it reads; the model opens them on demand.
3. `run_segment` gains `evidence_tools` and `max_turns`; it builds `build_source_tools(dir, read_limit_kb=read_cap_kb,
   compress_search_output=...)` and passes `tools=` and `max_turns=` to `ReasoningAgent.run` (which already accepts both).
   `run_segment` wraps the call in `EvidenceWorkspace(spec.mounts or ["documents"]).open()` (this wires `mounts`).
4. The read cap is `build_directory_tools`' own: a read over the limit returns an error that names the range option, never
   a truncation. `enforce_read_cap` / `ReadTooLarge` are used for any non-file mount a pack supplies (E4's corpus when
   mounted); for the run's files they would duplicate the tool's own check.
5. Tool compression: `compress_search_output` hook from `dir_tools`, default a line cap named constant.

Honest limits, to verify while building, not assume:
- `EvidenceWorkspace.open()` only narrows an ambient `InvocationContext`; `dir_tools` does not call `admit_hop`. The real
  isolation is that `build_source_tools` binds ONE directory and takes no `source` argument. Test that the bound set cannot
  name another path (traversal) and say so in the docstring; the workspace is the second layer.
- Tool turns multiply calls. Replicas times turns can cost more than the inlined prompt it replaces. Default stays `inline`
  until the eval in section 5 shows the saving on a real fixture.
- A failed materialization (bytes gone, digest changed) is tolerant: that document falls back to inline for the segment and
  a warning is recorded; `strict` fails the segment.

### E4. PrecomputedGrounding for a pack's reference corpus

`evidence.grounding: {source, top_k}` names a reference set the pack carries (guideline or reference material). Per segment
the step builds `corpus = {file: text}`, `query` = the segment's rule texts, calls
`PrecomputedGrounding(selector=HeadingsOnlySelector(), cache=InMemoryGroundingCache()).ground(...)` and adds
`format_injection()` to the segment header. Default selector is the no-model one; an LLM `SnippetSelector` is a pack
extension (cost is then metered). The cache is keyed by corpus fingerprint, so a changed reference set re-parses.
Missing source or empty corpus: tolerant proceeds without the injection and records a warning; `strict` fails the segment.

`BrowseGate` stays unwired: in this design the corpus is injected, not offered as browse tools, so there is no door to
close. It becomes relevant only if a pack mounts the corpus as tools too (a decision below).

### E5. Per-segment cost in the trace

`_MeteredService` gets an optional part key (the segment key). It still adds to `trace.usage["adjudication"]` (every
existing cost reader keeps its total) and also to a per-part `ModeUsage`. The step writes
`state.adjudication["evidence"] = {"mode": ..., "segments": [{key, rules, calls, input_tokens, output_tokens, cost_usd,
cost_is_upper_bound, failed, warnings}], "warnings": [...]}`. Read-only for pages (sonnet-ui owns the runs page; it is
told the shape when this lands). The key comes from the call's `name` prefix, so no change to `ReasoningAgent`.

### 2.6 Tolerant first, strict opt-in

Warn, record in `evidence.warnings`, proceed: materialization fallback, missing or empty grounding source, a segment whose
rendered prompt exceeds `evidence.warn_prompt_chars` (named constant). `strict: true` (pack data, never an SDK default)
fails the segment, so its rules are INDETERMINATE and `failed_segments` names it. Refusal only where proceeding would write
a wrong verdict; none of the warnings does.

## 3. Build order (each one commit on `v2.6.3`, tests first)

1. E5 plumbing (per-part metering) plus the `evidence:` spec block and its named constants. verify: usage totals unchanged,
   part sums equal the total.
2. E1 segment by policy. verify: two policies give two segments, a failing stub for one leaves the other's verdicts, the
   total equals today's for one policy.
3. E2 render once. verify: a long field read by three rules appears once in the prompt (fails on current code, three times).
4. E3 tool mode. verify: stub `ReasoningAgent.run` receives `tools`; reading a document over the cap returns the error;
   bound tools cannot reach outside the directory; fallback warning on a missing document.
5. E4 grounding. verify: injection appears in the header; second call hits the cache; changed corpus misses.
6. Eval measurement (section 5), then CHANGELOG, README/ARCHITECTURE adjudication section, and the TODO slug updated
   (`adjudication-spec-fields-unread`: `mounts` now read; `segments`, `regime_values`, `status_vocabulary` still unread).

Test stubs mimic production: `ReasoningAgent.run` returns `(batch, session, usage)`; a tool's over-cap result is the
error string the real tool returns, not an exception.

## 4. Files

`agents/adjudication/{spec,segment,agent,workspace}.py` (spec block, shared-evidence render, `evidence_tools`),
`pipelines/steps.py` (`_run_adjudication`, `_document_texts` split per document, `_MeteredService` part key, directory
lifecycle), `tools/agent/dir_tools.py` (read only; a line-cap compressor if none exists), `agents/reasoning/grounding.py`
(read only), tests `test_adjudication_segment.py`, `test_case_adjudication.py`, `test_adjudication_spec.py`.
CHANGELOG entries with line counts. Plato: nothing in this plan; the run page reads `adjudication.evidence` later.

## 5. How we know it helps

Run the existing adjudication eval and a real multi-policy fixture three ways (today, E1+E2, E1+E2+E3) and record input
tokens, cost, verdict agreement with today's, and failed-segment count. E1+E2 should be verdict-neutral; E3 is accepted only
if cost does not rise or the prompt-size failures it removes justify it. The result goes in the CHANGELOG, not asserted.

## 6. Not in this plan

Splitting an oversized segment into rule chunks, requiring that a cited document was actually read, LLM grounding selector,
the non-batched `ProcedureEvaluator.evaluate` path, the Acra job-writer fixes and everything else queued after this plan.

## 7. Decisions owed

1. **Segment key and grouping.** By policy as above (recommended), or by a section field a pack declares on its rules
   (finer, needs data most packs lack)?
2. **E2 threshold.** `inline_min_chars` default 2000 and "read by two or more rules" (recommended), or share every
   multi-read field regardless of length?
3. **Defaults.** E1 and E2 on for every pack (recommended, verdict-neutral); `mode: inline` stays the default until the
   eval, then flip only per pack?
4. **Tool mode reach.** Run documents only (recommended), or also let a pack mount the reference corpus as bound tools,
   which brings `BrowseGate` and `enforce_read_cap` into play?
5. **Grounding selector.** No-model headings selector as the default (recommended), LLM selector as a pack extension?
6. **Per-segment cost surface.** `adjudication.evidence` in the step's state as above (recommended), or also a new
   `ModeUsage.parts` field every cost reader sees (touches the cost pages)?
7. **Strict.** One `strict` flag for the block (recommended), or one per feature?

## 8. Built (2026-10-15, `v2.6.3`, `6f25fee1`, `8eb37cb1`, `d3a6fc4b`)

Decisions taken as recommended. Deviations:
- E4 default selector: `HeadingsOnlySelector` is an LLM call, not a no-model one, so a new `TopRankedSelector` (the
  prefilter's best `top_k`) is the default; the LLM selector is not exposed in `adjudication.yaml`.
- E4 source: a directory of `.md`/`.txt` files inside the pack (`grounding.source`), read through the loader.
- E3 materialization fallback dropped: conversion failures already fail the step in inline mode too, and writing the
  file cannot meaningfully fail. `strict` covers only a missing grounding source and an oversized prompt.
- E3 tool-call counts are not recorded per segment (calls are model calls); no `ModeUsage.parts`.
- Not done: the section 5 eval (live model calls; wants the user's go-ahead and a real multi-policy fixture).
  `mode: inline` stays the default until it runs.
- Segment order follows policy load order; a planner supplying its own segments gets no grounding (keys differ).
