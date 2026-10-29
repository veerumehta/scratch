Browser check of the new Plato pages. Base: http://localhost:8000/api/v1 (restart local Plato on the v2.6.3 tip first).
Anything that shows "400 X-Trace-Id required", a red error bar, or "[object Object]" is a bug: note the page and the text.

1. X-Trace-Id fix (every page)
   Open /packs/ui, /cases/ui, /coverage/ui, /extraction/ui, /assistants/ui, /logs/ui, /info/ui.
   Each should load its list with no red error bar.

2. Runs page, Start a case: /cases/ui
   - "Start a case": pack id of a pack with a case pipeline (Acra DSCR), leave version/model/engine empty.
   - Pick a local Acra file, leave the record empty, click "Start the run".
   - Expect "Uploading <file> (1 of 1)", then "Started run ...", and the run opening below with Steps filling in.
   - Try a file over the cap: the server's sentence shows, nothing starts.
   - Try a record only (paste {"borrower": "x"} and no file): a run still starts.

3. Extraction auto-refresh: /extraction/ui?pack=<pack>
   - With a run going (or start one from the Packs page): the line beside the count reads "Refreshing every 5s; updated <time>".
   - Open a row, scroll, set a filter: all stay after a refresh. Parts reads "n of m" while it runs.
   - When every run has ended the line reads "All runs have ended." and the polling stops.

4. Assistants page: /assistants/ui
   - Pick policy-authoring, send "open the extraction page for pack X": a link card appears (nothing opens until clicked).
   - Ask it to start an extraction: an approval card comes first.
   - Pick the Acra case assistant with a case subject: ask about a finding; sources should link to the cited page.
   - Select some text on the page and ask "what did I select?": the assistant should ask the page and answer (a note "Asking this page for selection.").
   - Ask for a borrower email: a card with subject, body, Copy and "Open in mail client" (nothing is sent).
   - Pick eval-authoring: "draft test cases for <assistant id>": a card with Save and Discard (Save creates a dataset).
   - Thumbs up/down, the inspector drawer, reload (the conversation should rebuild).

5. Solution page: /blueprints/acra-dscr/ui
   - The narrowing chain strip appears above Members only if the blueprint declares a chain; a card is amber only when a widening names it.
   - Job table, click a job: history popup. Click a rule link: its code.
   - Tick "the open draft": the table switches to the draft; "Download table (xlsx)" works; the bundle link says "the published version: not the draft".
   - Untick it and download the bundle (zip).

6. Page lists (every page)
   - The page list shows at the head and at the foot of every page, including /docs.

7. Ontology page compare: /ontology/ui
   - "Compare versions": pick a reference (or pack:<id>), the newest two versions are prefilled; Compare shows counts, a filter, rows opening to before and after. A pack lists only its newest version, so type the other.

8. Code page: /code/ui
   - Pick a domain pack and a version, Load: the rules table fills; Library cells are amber where the rule's rules_lib differs from the current one.
   - Tick "written for another library version" and "needs a field": the table narrows. Click a row: the rule's source opens.
   - Compare two versions: counts, rows, and "Rules to re-test" when a rule's library or a read field changed.

9. Vocabulary page: /vocabulary/ui
   - Core catalog: a reference whose id holds "core" is first (none exists until the core is loaded; any reference works). Show lists Entity.field, type, unit.
   - Compare two versions as above. A pack id, "Open aliases.yaml": the draft file opens in the editor; Save writes the draft (no publish); Changes shows its diff; with no draft, "Open a draft" appears.
