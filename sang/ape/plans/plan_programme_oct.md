# Programme, October: from policy to jobs to code, the solution view and the assistant page

Programme, opus-xrepo, 2026-10-13. It orders the plans below, says who builds each and what each waits on.
Decisions are the user's, dated.

## Plans in scope

| Plan | State |
|---|---|
| `plan_decision_corrections.md` | C1-C3 and C5 built (`b43087f9`, `867f10a8`, `90c373c1`); C4 waits for real corrections |
| `plan_document_registry_and_job_shape.md` | D1 and D2 (SDK half) built 2026-10-13, uncommitted at the time; open D1 items: the registry proposal passes, and the cross-version lint against the last published pack (after D3); D3 in progress; seed migration with sonnet-jaci |
| `plan_solution_view.md` | approved; V1-V4 to build |
| `plan_plato_assistant_chat.md` | approved; A1-A6 to build |
| `plan_guideline_release.md` | to approve (section "Decisions owed") |
| `plan_jtbdset_readiness.md` | routed; small |

## Who builds

- **sonnet-runtime** (SDK, policy, packs, runtime): the registry plan D1-D4, the guideline release,
  the readiness checks, and the routed small items (the `run_agent_with_retry` transient rule, the
  adjudication vote, unread spec fields).
- **sonnet-ui** (new session, started 2026-10-13 at the user's direction): the solution view
  V1-V4 and the assistant chat A1-A6, including their SDK parts (`pack.bundle`, the platform
  event codec, the ground kinds, typed artifacts on the response). It works on `v2.6.2` like the
  others.
  - **Shared files:** `plato/static/shared.js`, `plato/app.py` and `plato/api/assistants.py`. Run
    `git status` before editing; message sonnet-runtime when touching a file it also edits.
- **sonnet-jaci:** the DSCR seed migration to entity names, and the seed's document registry, on
  sonnet-runtime's go after D2's SDK half.
- **opus-xrepo:** regenerating the Acra jobs and code after D3 and comparing with the baseline;
  importing the hand-built sets as the reference pack after V1; the cost sheet; coordination.

## Order and dependencies

```
sonnet-runtime:  D1 ─► D2 (SDK half) ─► D3 ─► [opus-xrepo: regenerate + compare] ─► D4 ─► R1 ─► R2
                        └─► sonnet-jaci: seed migration
sonnet-ui:       V4 ─► (wait D1) ─► V1 ─► [opus-xrepo: reference pack] ─► V2 ─► V3
                 A1 (+ A6.1 docked panel, A4.1-4 cards, approve, context) ─► A2 (+ A5 codec) ─► A3 (+ A6.2-6)
small items:     between phases, sonnet-runtime
```

sonnet-ui starts with V4 and A1 at once, since neither needs D1. V1 and the history popup wait for
D1's stable ids.

## Reviews

**Code review:** one adversarial review over the whole range at the end. The user runs it
(`REVIEW_UPSTREAM` at the programme's base, `da41f07b`'s parent range, or the user's choice). The
user's decision, 2026-10-13.

## Posture

Tolerant first; consumer-neutral; no reliance on other services; no version bumps; CHANGELOG
entries per commit round; commit headlines only.

## Measures at the end

- **Acra regenerated:** job count and grain against Acra's 123/108; the partial share against the
  baseline of 41/123; the code share against the baseline of 40-50%; the lacks-data share against
  the baseline of 60%; cost per pass.
- **Solution view:** every bundle item reachable from the blueprint page; job history opens with
  version 0.
- **Assistant page:**
  - the authoring assistant runs an extraction behind an approval card;
  - the Acra case assistant answers with a finding and a guideline page cited;
  - the production chat UI renders a `?format=platform` stream from Plato (fixture).
