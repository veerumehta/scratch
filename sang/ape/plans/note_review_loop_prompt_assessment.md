# Why the review loop recurs: the two prompts, and what the round data says

Status: assessment, 2026-09-10. Decides nothing. Written against japes `75cbc25` on `v2.5.1`,
after nine review runs / 25 slices in one session.

## 1. The two prompts, side by side

### 1.1 What directs the code-writing

Three layers, roughly 200 + 90 + N lines:

| Layer | Contents | Character |
|---|---|---|
| `CLAUDE.md` | 7 numbered sections: think before coding, simplicity first, surgical changes, goal-driven execution, docs/attribution, dependency specs, symmetry | Mostly **virtues and process** |
| ~90 memory files | Version policy, commit style, plan locations, never-push, no em-dashes, terse output, per-repo traps | Mostly **process and preference** |
| Session instructions | Output style, delivery norms | Behavioural |

Of that surface, the parts that name a *defect class* are: §1 ("state assumptions"), §4 ("a test is
not evidence until it fails against the old code"), and §7 ("enumerate the family before editing").
Everything else is how to work, not what goes wrong.

### 1.2 What directs the review

One prompt, ~110 lines, structurally different. It opens by naming eight defect classes
**"because they are what has actually shipped broken here before"**:

1. an input the code excludes: empty, zero, one, None, range/loop boundaries
2. a comment, docstring or name claiming a guarantee the code does not enforce
3. an exception handler missing a type the block can raise, or sitting above the raise
4. an error swallowed so a caller's mistake returns as an ordinary result
5. a hardcoded path, one machine's layout, or a consumer/repo name in shipped code
6. a declared branch condition with no predicate behind it
7. a fix applied in one place where a sibling has the same defect
8. a knob added to one member of a family and not the others

Then: a three-tag taxonomy (`[DEFECT]` / `[SYMMETRY]` / `[NOTE]`), a requirement that every
finding name **the concrete input or state that triggers it**, a severity rating whose blast radius
must be *"what you actually checked, not an adjective"*, an instruction to verify existing
`TODO`s rather than re-report them, and caps (2 symmetry findings, 3 notes).

**The asymmetry is the finding.** The review prompt is a checklist of concrete failure modes with
triggers. The authoring instructions are a set of dispositions. Only §7 overlaps items 7 and 8 —
and §7 is the rule that failed most often this session, by its own admission ("still failed six
times in one session").

## 2. What the rounds actually found

Nine runs, 25 slices, on a branch that grew 11,895 diff lines.

| Run | Defects | Symmetry | Notes | Verdicts |
|---|---|---|---|---|
| 13:49 | 6 | 3 | 9 | BLOCK BLOCK PASS |
| 14:30 | 6 | 4 | 8 | BLOCK BLOCK PASS |
| 16:34 | 2 | 4 | 10 | BLOCK PASS BLOCK |
| 17:45 | 3 | 4 | 8 | BLOCK BLOCK BLOCK |
| 17:45b | 4 | 3 | 7 | BLOCK BLOCK BLOCK |
| 20:32 | 5 | 2 | 9 | BLOCK BLOCK BLOCK |
| 21:11 | 2 | 1 | 9 | PASS BLOCK BLOCK |
| 21:50 | 1 | 4 | 9 | PASS BLOCK PASS |
| 22:32 | 2 | 3 | 6 | BLOCK PASS … |

**Severity across all 25 slices: 2 high, ~24 medium, ~8 low.** Nothing catastrophic; almost
everything is "reachable, fails loudly or the caller can work around it".

**The trend is real and measurable.** Defects per run: 6, 6, 2, 3, 4, 5, 2, 1, 2. PASS slices per
run: 1, 1, 1, 0, 0, 0, 1, 2, 1. The last three runs produced 5 defects between them against 15 in
the first three, on a *larger* diff each time.

## 3. Why it recurs: four mechanisms, ranked by evidence

### 3.1 One defect class dominates: a claim the code does not back

Roughly **two-thirds** of the session's defects and most of the notes are the same shape — prose
asserting more than the encoding enforces. In code: `tenant_of`'s docstring promising a message it
did not send; `_UNTESTED_RATIONALE` describing three of four enum members; `Threshold`'s
`extra="forbid"` comment; `_apply_applicability_gate` claiming to "mirror exactly"; `not_yet_effective`
described as withheld when nothing withholds; `current_policies` / `active_only` describing the old
`is_active`; `config_api`'s "exact set … and no more"; `packs_api`'s "load-bearing" guards.
In pack data: three rule descriptions stating a leg the condition omitted; two warning rules
describing a band with no lower predicate; `workbook_layout.yaml` claiming a load-time check that
does not exist; a field named `sha256` holding sixteen characters; four stale counts in one notes
file.

This is item 2 on the review's list. It appears nowhere in the authoring instructions as a class.

### 3.2 Fix churn generates the next round's findings

At least eight of this session's defects were introduced by the previous round's fixes, not by the
original branch: the `packs.html` failure path going silent, `_evaluate_composite`'s `fallback`,
`validation.py` dropping the `warnings` shape, `looks_authored` false-positiving on `status`,
`reason()` leaking a type name into a served 400, `relaxed_only` losing its tightening direction,
`not_yet_effective` breaking the pinned-version check, and `residential_unit_count` trading a wrong
denial for a wrong approval.

Two of those were caught only because a fix's own delta was reviewed. One inline pass over a delta
found four things, two of them regressions — and the round after an inline pass that declared
convergence found two mediums in the same code.

### 3.3 The review reaches material the instructions do not govern

The last three runs' defects are overwhelmingly in the vendored credit corpus — `all_of` gating,
rule descriptions, undeclared pack assets — not in the plato or SDK code. There is no authoring
rule anywhere for "a rule's description must be backed by its condition", and no lint for it. The
review found the `>$2M` no-ratio skip (`high`) in a corpus the notes themselves had documented the
hazard for, with the prescribed fix applied to two of three sites.

### 3.4 Full re-review every round

Every run this session used `origin/v2.5.1...HEAD` — 11–12k lines, three slices, three independent
reviewers with no shared state. The script *supports* incremental mode (a `.state` baseline plus
the prior transcript appended, with an explicit `WAS: … FIXED | STILL OPEN | REGRESSED` accounting
step) and it was not used. That mode targets §3.2 directly and costs a fraction of the wall clock.

## 4. What I checked and found *not* to be a driver

**The "low defects still BLOCK" tension.** The prompt defines `low` as "no reachable trigger in any
shipped configuration … a `TODO` in the code is a complete response", yet the verdict rule blocks on
any `[DEFECT]`. That reads like a significant source of false stops. It is not: only **2 of 19**
BLOCKs were driven purely by low-rated defects.

It does surface an inconsistency worth fixing cheaply, though: two slices with a single `low`
defect returned *different* verdicts (17:45b slice1 → BLOCK, 21:11 slice1 → PASS). The rule is
being applied differently run to run.

## 5. Changes worth making, with honest magnitudes

| # | Change | Targets | Expected effect |
|---|---|---|---|
| 1 | Add the review's eight classes to the authoring instructions **as a pre-commit checklist**, not as virtues — especially "a claim the code does not enforce" | §3.1 | Largest available. Two-thirds of findings are this class; even half caught pre-commit halves the rounds |
| 2 | Review the **fix delta** before declaring a round done | §3.2 | Demonstrated: one such pass found 4 items, 2 of them regressions |
| 3 | Use the script's incremental mode (`.state` + prior transcript) | §3.4 | Rounds get much cheaper, and the `WAS: FIXED / REGRESSED` step makes churn visible instead of implicit |
| 4 | An authoring rule and, ideally, a lint for **rule description vs encoded condition** in pack YAML | §3.3 | Would have caught three of this session's defects including the one `high` |
| 5 | Gate `VERDICT: BLOCK` on `medium`+ and state it once | §4 | Small (2 of 19) but free, and removes the run-to-run inconsistency |

**What I would not spend effort on:** rewriting the review prompt's taxonomy or caps. It is
well-calibrated — every finding this session carried a reachable trigger, the `CHECKED:` mechanism
correctly refused to re-litigate ten deferrals, and it twice declined to guess (`IMPORTANCE:
unknown`) rather than inflate. The prompt is not why the loop is long.

## 6. The honest read on convergence

The loop is converging: 6 → 1–2 defects per run across nine runs on a growing diff, with PASS
slices appearing where there were none. But it has not converged *because* the defect supply
changed character rather than stopping — it moved from the plato/SDK machinery into the credit
corpus, which is the part with no authoring rules, no lint, and the least self-checkable content.

Two consequences worth stating plainly:

- The remaining findings are in the material where a missed defect matters most (a wrong credit
  verdict) and where I am least able to self-check. That argues for §5 item 4 before more rounds.
- "One more round" has been the right call every time so far, and each round has cost roughly
  20 minutes of wall clock plus a fix cycle. The cost is not the review; it is that a fix cycle
  has been generating about one new defect per round (§3.2). Item 2 is the cheapest thing that
  changes that number.
