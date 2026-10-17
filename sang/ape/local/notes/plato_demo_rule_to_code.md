# Demo: one guideline rule, its job, and its Python code, in Plato's UI

Not opened in a browser by me: walk it once before presenting. Local Plato is at http://localhost:8000 (the nav bar
links every page). Use the trial pack `acra-regen-3b` (tenant `acra-lending`); the coverage numbers on screen match
`ape/local/coverage/regen_3b`.

Example job (clean: one check, no disagreement, no missing data):
`acra-platinum.liabilities_assessment.listed_property_reserves`
"Verify the 24-month reserve requirement for a property listed for sale within the last six months."
Alternatives: `acra-platinum.credit_review_analysis.loan_amount` (range and increment, shortest code),
`acra-platinum.liabilities_assessment.property_listed_within_six_months` (a determination).

Walk:
1. **Packs page** -> open draft `acra-regen-3b` -> `policies/acra-platinum.yaml`. Find the rule id
   `acra-platinum.liabilities_assessment.listed_property_reserves.python`: its Python body is the code.
2. **Extraction page** -> the Platinum jtbd run shows the job that was written from the guideline section; the
   code run (python_jobs) shows the 5 jobs it wrote code for (5 of 5 on the retry).
3. **Coverage page** -> pack `acra-regen-3b`, row for the job: disposition `code`, the rule ids, the document classes
   it reads, folds and mapped data. This is the one place that shows job to code to coverage together.
4. Optional live: **Runs page** -> "start a case" with a loan, to show the rule firing on a case (needs a pack
   that is published: `acra-dscr-policy`, not the draft trial).

Say in one line: guideline text -> job (what to check, from where) -> Python rule (what decides it) -> coverage (how
much of the guideline now has code: 50% of 240 jobs, 35% lack data the case schema does not hold yet).
Numbers to state honestly: regen 2 was 56% and the gap to regen 3b is not yet explained (a repeat run measures it).
