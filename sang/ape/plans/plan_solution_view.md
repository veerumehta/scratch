# Solution view: one page per blueprint, latest of each piece, history one click away

Plan, opus-xrepo, 2026-10-13. Status: written. Owner: sonnet-runtime (SDK routes, Plato page). Origin: the
user wants the `/tmp/acra_bundle` material reachable from Plato, from one main view.

## 1. What the user asked

- The main view shows only the latest of each piece: the newest job set, the newest code, the newest
  guideline version.
- Every earlier version stays reachable from the row it belongs to, for example a popup on a job row.
  Acra's hand-built set counts as **version 0** of the job set.

## 2. What exists

| Piece | Where today | Gap |
|---|---|---|
| Blueprint `acra-dscr` (policy, core, assistant members, versions resolved) | `plato/api/blueprints.py`, packs page card | names packs only |
| Guideline sets and versions, diff, certification | `plato/api/guidelines.py`, packs page | Acra's set never published locally; no file download |
| Our jobs, code, ledger | policy pack drafts and versions; draft file viewer; coverage page | no per-rule code view; trial is a draft |
| Hand-built set | compare page upload; `POST /packs/{id}/jtbdset[/programs]` imports into a draft | not stored |
| Coverage and aligned comparison, xlsx | coverage and compare pages | separate pages |
| Published archive | `GET /packs/{id}/{version}/archive` | no UI link |

## 3. Design

### V1. The blueprint carries a reference job set and its guidelines

- **New blueprint member role, `reference`:** a published pack holding a job set imported from
  outside, such as a hand-built set. It is shown as job-set version 0 and is never activated.
  - The roles are pack data in `jazzx_sdk.pack.blueprint`.
  - Activation skips `reference` members.
- **`Blueprint.guidelines: {set_id}`:** the main view shows the set's newest version, and earlier
  ones in its history.
- **For Acra:**
  - publish the two guideline documents as set `acra-dscr` (G1);
  - import the hand-built Standard and Platinum sets with `/jtbdset/programs` into a pack
    `acra-dscr-reference`, published as `0.0.0`;
  - add it to the blueprint as `reference`.

  This is local Plato data, not code. opus-xrepo does it once V1 lands.

### V2. The solution page, `/blueprints/{id}/ui`

A list-first page in the style of coverage and extraction.

- **Header:**
  - the blueprint, its members at their resolved versions, and the guideline set at its newest
    version, each with a download;
  - the coverage summary for the policy member's newest version.
- **Main table: one row per job of the newest job set**, which is the policy member's newest
  published version, or its open draft when the toggle says so. Columns:
  - job (mnemonic, section, kind);
  - source clause;
  - disposition;
  - code: the implementing rules, each opening the rule's source;
  - reads, and missing data;
  - **history**: a count, opening the popup.
- **History popup for a job:**
  - **Earlier versions of this job** in earlier published versions of the policy pack, matched
    through stable ids and aliases (the registry plan's D1 rule). Each entry shows the version,
    a diff of requirement text, checks and reads against the newest, and the code that version
    linked.
  - **Version 0:** the reference job or jobs aligned to it, with the label (same, differs, partial)
    from the stored alignment, and its requirement text.
- **Reverse view:** a toggle lists the reference set's jobs with the newest job they map to, or
  none. That is where "we missed this" shows.
- **Downloads:**
  - the page's table as xlsx;
  - per row, the job as JSON and its code;
  - for the whole solution, the bundle (V3).

### V3. Bundle download

`GET /blueprints/{id}/bundle.zip` builds what `acra_bundle.py` builds:

- the guidelines at the newest version;
- version 0 and the newest job set (and readable markdown);
- code as one file per rule, from jobs and, if any, from segments still proposed;
- the ledger;
- the coverage and comparison workbooks;
- a README.

`?versions=all` adds earlier versions. The logic lives in the SDK (`jazzx_sdk.pack.bundle`) and
Plato hosts it.

### V4. Small routes the page needs

- `GET /guidelines/{set}/versions/{n}/files/{path}`: a guideline file's bytes.
- A link to the published archive on the packs page.
- `GET /packs/{id}/{version}/rules/{rule_id}`: one rule, with its source for python rules, for the
  code view.
- The stored alignment between a job set and its reference, so the popup does not rerun a model.
  The aligned comparison already returns labels; store its result per (version, reference version).

## 4. Posture

Tolerant first:

- a blueprint without a reference or guidelines shows what it has;
- a job with no earlier version shows "new";
- an unaligned reference job shows "no match".

## 5. Order

V4 first (small), then V1, then V2, then V3. Size: V1 and V4 are one pass, V2 one pass, V3 small.
It follows the registry plan's D1, because the popup's matching across versions relies on stable ids.
Until D1 lands, versions match by rule id only.

## 6. Decisions

None needed beyond the user's ask: latest in the main view, history in a popup, hand-built as
version 0.
