# Status: Memory, and what earns a place in the SDK

Author: Virendra Mehta · Updated 2026-08-01
Repo: japes · Plan: docs/plans/plan_memory_scoping_and_sdk_principles.md

**Not a build plan — a position/review note addressed to Sourav, reviewing an external PR (#54,
"the memory plane") this repo doesn't own.** Every action item in "What I'd like to do" is either a
cross-team alignment ask (cite Hermes, decide who gets `fabric.memory` — a joint decision with
whoever owns PR #54) or a design-doc restructuring request (move M3-M8 into its own doc), not
`jazzx_sdk` code. The "Things I don't know" section is explicitly open questions for elsewhere
(the assistant team, an AML/lending requirements answer, "which runtime emits the authoritative
committed-turn event" — the design's own open item). Nothing here is mine to decide or build
unilaterally. Reviewed, no code changes.
