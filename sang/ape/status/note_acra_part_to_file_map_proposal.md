# Proposal: settling the Acra Part-to-file map (sonnet-ui, 2026-11-09)

Status: proposal only. Nothing read, uploaded or run. Needs the user's decision before any step.

Facts: six Parts (1, 2, 3b, 4, 5, 6) with 101, 90, 52, 117, 35, 69 labeled pages (463), 112 ranges, 56 labels (0-based). Five loan PDFs of
534, 551, 786, 788, 1063 pages (golden/loan_files.json). No Part's page count equals a file's, so each Part is an excerpt at an unknown
file and offset. What 3b is: unknown. The user's typed vision run approval (5 USD) is on record in this session; ask again when the run starts.

## 1. Method (local, no model, no spend)

1. **Text layer.** Extract text per page from each loan PDF with the SDK's own conversion step in text-only mode (the readable-first tier;
   confirm in `tools/documents/` which entry point does that without a model call before building; if it can call a model, use a plain PDF
   text extractor already in the lockfile instead). Result per file: page index to extracted text, kept in memory only.
2. **Coarse page signature.** Reduce each page to a document-type token from a fixed marker list, nothing else:
   - a form title or form number line from a closed list (for example the standard uniform forms: loan application, note, deed of trust or
     mortgage, closing disclosure, appraisal report, title commitment, insurance declarations, tax return form numbers, bank statement,
     pay stub, W-2, 4506-T, ID, credit report);
   - a marker present or absent (title keyword in the first 400 characters), else `other`, or `blank` (under 20 characters of text).
   The marker list is written first, in a file reviewed by the user, and contains no names, numbers or addresses. Matching is
   case-insensitive keyword presence; no text is stored, only the token.
3. **Expected sequence per Part.** From the SME ranges: each labeled range gives (label, start, end), so a Part's expected token sequence
   per page comes from a label-to-marker table (label_mapping.csv gives the labels; the user or SME maps each label to zero or more markers,
   or `unknown`). Labels with no marker are wildcards.
4. **Alignment.** For each Part and each file, slide the Part's expected sequence over every offset (file pages minus Part length plus 1,
   at most about 1000 offsets) and score: matches over non-wildcard, non-blank positions. Use only the positions where a marker is
   expected and the page has text. Complexity is trivial (3,000 pages x 6 Parts).
5. **Confidence rule.** A Part maps to (file, offset) when all hold: best score at least 0.80 over at least 15 scored positions; best
   exceeds the runner-up (any other file or offset more than 5 pages away) by at least 0.15; and the first and last labeled page both
   match their expected markers when those labels have one. Otherwise the Part is `undecided`. Two Parts may not claim overlapping pages of
   one file; an overlap sends both to `undecided`.
6. **Scanned pages (no text layer).** They score as `blank` and drop out of the score; they count in a coverage figure (scored positions
   over Part length). If a file has under 60% of pages with text, the method cannot decide for that file and says so. It does not OCR (OCR
   is a model call or a new dependency: out of scope without a separate yes).

## 2. What it reads and writes

- Reads: the five loan PDFs locally, inside one script; text is never printed, logged, or sent to a model.
- Writes: only to the ignored `docs/status/Acra/Acra Lending/golden/` folder: `part_map_candidates.json` with per Part: file as masked
  `loan-N`, offset, score, runner-up score, scored positions, coverage, verdict. No text, no snippets.
- Prints: masked loan-N, counts, scores and verdicts only. Never file names, borrower names, amounts, or page text. Nothing to chat, /tmp,
  a commit or logs; exceptions are caught and reported by type only (tracebacks can echo text).
- The script itself lives in `scripts/local/` (not loan data) and carries no loan content; the marker list holds only generic form titles.

## 3. What it cannot decide, and what it then asks

- Part 3b: no expected shape is known, so it runs as the other Parts do but flagged `unverified`; the user is asked what 3b is (a re-label
  of 3, a continuation, a different case) and, if a map exists, which file.
- A Part with under 60% text coverage, a tie, or no match at 0.80: reported as `undecided` with the top three (file, offset) candidates by
  masked id and score, for the user to confirm or reject.
- Duplicate content (the same form set in two loans) will show as a runner-up inside the margin: `undecided`.
- It proves a fit, not provenance: a confident match still goes to the user for a yes before the dataset is built.

## 4. Time and cost

Costs nothing: no model, no network. Estimate (unmeasured, to be confirmed on the first file): text extraction about 0.05 to 0.3 s per
page, so 3,000 pages in roughly 3 to 15 minutes; alignment under a minute. Build and review of the script and marker list: about half a day
of session time, and the marker list needs the user or SME to look at it once.

## 5. Alternative: no loan content at all

The user or SME states the map. Questions, per Part (1, 2, 3b, 4, 5, 6):
1. Which loan (masked loan-N) is it excerpted from?
2. First page of the excerpt in that file, 0-based, or 1-based (say which)?
3. Is the excerpt one contiguous run of pages, or several runs? If several, the start page of each and its length.
4. What is 3b (separate Part, sub-Part of 3, other loan)?
5. Are page numbers in the labels the excerpt's own (0 is its first page) or the original file's?
This is the fastest path if the SME still has the source of the excerpts; answers are five lines in a table.

## 6. When the vision run could start

After the map is confirmed and the dataset (excerpt pages plus labels, built locally with no model call) exists: the run can start the
same day. 463 pages in one pass on a vision model: unmeasured, probably 15 to 45 minutes at modest concurrency; cost against the 5 USD
ceiling is also unmeasured (I will measure on a 5-page probe before the full run and stop if the projection exceeds the ceiling). A number by
tomorrow evening is realistic only if the map is settled by tomorrow midday: with the SME's answers (section 5) that is likely; with the
local alignment (section 1) it depends on how many files have a text layer and on the marker list review. The user's yes to run is needed
again at that point.
