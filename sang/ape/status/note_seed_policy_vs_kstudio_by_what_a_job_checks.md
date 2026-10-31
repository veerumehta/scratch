# Seed policy vs K-Studio v17 and v7, by what a job checks (sonnet-packs, 2026-10-30)

Read-only, no run, no spend. Equivalence is by what is checked and the figures, never by mnemonic (`note_job_identity_equivalence.md`
part 4); I invented no equivalence rule. One reader, rule descriptions and K-Studio skill text only: figures were then checked in
the profile and conditions (section "Condition-level pass").

**Scope.** Seed = `policies/standard.yaml` (54 rules), `platinum_select.yaml` (29), `process.yaml` (23, shared). Theirs = Standard v17
(124 jobs), Platinum v7 (108). Clause to K-Studio job links come from `jobs_vs_kstudio_regen5.xlsx` sheets 2 (my earlier reading);
seed rule to clause links are the STD/PLAT ids each rule's description cites (every policy rule cites one).

## Result

| | Standard | Platinum |
|---|---|---|
| Numbered clauses | 123 | 94 |
| Clauses with a K-Studio job | 119 | 92 |
| Clauses a seed rule cites | 31 | 23 |
| Cited, and K-Studio has a job | 31 | 23 |
| Cited, K-Studio has none | 0 | 0 |
| K-Studio job, no seed rule | 88 | 69 |

Every clause the seed encodes has a K-Studio job that checks the same thing. The seed is the numeric eligibility policy (grids,
caps, minimums, per-state prepay); K-Studio also carries what the seed leaves to the document pipeline. The 88 and 69 are mostly that:
entity eligibility and guarantees (9 each), occupancy and purpose (8 each), rent schedules and evidence, gift funds and funds to
close, rent loss insurance (4 each), qualifying rent, foreign-account assets (Standard), forbearance and late applicants (Platinum),
the ratio and No Ratio definitions, interest-only mechanics, matrix footnotes, due diligence. None is a figure disagreement; they are
checks the seed does not make.

## Same check, different grain (equivalent, no action)

- **Seed finer:** STD-3.16 (3 rules: DSCR 1.20, reserves, property type) vs K `DRT-LTV80` (one); STD-3.17 (4) vs `DRT-SUBCAPS`;
  STD-7.3 (3) vs `CRD-1SCORE`; STD-4.10 (3) vs `BCE-FTHBTERMS`; STD-8.3, 8.6, 8.7, 8.9 each 3 rules vs one K job; PLAT-6.8 (2) vs two
  K jobs that duplicate each other (`CRD-PCESEASON`, `CRD-PCE-SEASON`); the 14 state prepay restrictions (15 rules, IL has two) vs
  `PPP-STATE` / `PPT-PPP-STATE`; the state list matches (AK IL KS MD MI MN MS NJ NM OH PA RI VA VT).
- **K-Studio finer:** STD-2.1 grid (seed 1 rule, K 4: governing cap plus three loan-size tiers); STD-8.1 property-type caps (seed 1 plus
  DSCR and Florida, K 5 jobs); STD-4.1 to 4.5 citizenship (seed 5, K 7); escrow waiver (seed 2 rules, K 2 jobs split differently).
- **Figures agree** on every matched pair I could read: loan range $100,000 to $3,000,000 Standard and $2,000,000 Platinum, 3% concession,
  SD ineligible, small-loan 80/75, over-$2M DSCR 1.0, IO $250,000 and 640, STR 75/70 and 640, high-LTV 1.20 and 6 months, sub-1.0 and
  No Ratio 75/70/65 and 640, NPR $1.5M and 80%, Foreign National 70/65, ITIN $1.0M and 640, FTHB 700/$1M/70%/1.15, thin file 65%/1.1/24 months,
  FICO under 620 reserves 12 months, mixed-use 1.2, 10/40 IO 80%, Platinum 75% for loan size, Correspondent 60% at 700-719 and DSCR 1.2,
  tradelines, 48-month PCE seasoning, escrow waiver $1.5M and 0x30x24, 6 months above 75% CLTV, IO 5 Yr 75%.

## Differences that need a decision or a pack change

1. **Vacant rate & term refinance boundaries (STD-8.6, Q-10).** Seed bands are exclusive (under $1,000,000 takes 70%, $1,000,000 to
   under $2,000,000 takes 65%, $2,000,000 and over is ineligible), following the Summary's "under". K-Studio `PVL-VACRTREFI` is inclusive
   ("up to $1,000,000" 70%, "up to $2,000,000" 65%), following the guide's "maximum". At exactly $1,000,000 the seed gives 65% and
   K-Studio 70%; at exactly $2,000,000 the seed refuses and K-Studio allows 65%. A reading for the user, with the existing readings.
2. **Cash-in-hand footnotes (STD-2.3, PLAT-2.2).** K-Studio checks them (`LAC-CASHHAND`, `LFC-CASHHAND`); the seed does not encode them
   (stated in its header, Q-17). Covered by proposal `cash_in_hand_limits` in `draft_missing_jobs_acra_dscr_policy.yaml`.
3. **Listed for sale (STD-8.9, PLAT-7.8).** K-Studio `PVL-LISTDSCRCLTV` allows 1.0 DSCR or 43% DTI and bases the 65% on the lesser of appraised
   value or lowest recent listing price; seed has DSCR 1.0 and 65% only. K-Studio also checks the 3-year prepay and no subordinate
   financing (seed omits both on purpose: Q-24, Q-18). Whether the DTI alternative and the listing-price basis are printed in the
   guideline needs a read of STD-8.9 before any rule changes.
4. **Vacant refinances (STD-8.6, 8.7).** K-Studio adds the minimum prepay term (2 and 3 years); seed omits it (Q-24).
5. **Loan-amount increment ($50, STD-1.10, PLAT-1.13).** K-Studio checks it; seed does not (the policy header lists it as not encoded).
6. **Platinum products (PLAT-9.1).** Seed only bars 10/40 IO; K-Studio `PPT-PRODUCTS` checks the product is one of the four. ARM terms
   are the proposal `arm_terms`.
7. **Foreign National FICO 700 pricing rule (STD-4.4).** In K-Studio `BCE-FNCLTV`; not in the seed rule description. Pricing, probably out
   of eligibility scope; confirm against the guideline.
8. **Cross-cutting K-Studio jobs with no clause** (source version, `LFC-CLTV-FINAL` governing CLTV, `AFC-RESERVE-TOTAL`): aggregates the
   seed expresses as the policy taking the lowest applicable cap. Equivalent in effect, not in shape; no action.

## Condition-level pass (added 2026-10-30)

Opened the profile (`dscr_v6_15_2026_v1_1`) and the 106 rule conditions.

- **Printed grids match.** Standard matrix (3 loan-amount bands by 11 FICO rows by 3 purposes), Platinum matrix (730 / 721 / 700),
  housing history, bankruptcy and foreclosure, short sale / DIL / modification, property-type and Florida caps, rural, ITIN (three tiers),
  vacant and listed-for-sale caps, all equal the guideline's printed tables cell for cell.
- **720 on Platinum is not a difference.** Seed bands are 700 to under 721, 721 to under 730, 730 and over, so a 720 takes the 700 row
  (cash-out 55%), the same literal reading K-Studio `LFC-FICO-MTX` states (Q-01). My first note said the two differed; they do not.
- **No drift inside the pack.** Every `profile:`, `profile_table:` and `profile_custom_key` a rule names exists in the profile, and
  where a rule also carries an inline value it equals the profile's (0 mismatches across 23 linked custom keys; the DSCR thresholds are
  referenced by name only).
- **Inline literals not in the profile:** the 80% CLTV and 700 FICO inside `DSCR-ESCROW-WAIVER-TERMS` and the `0x30x24` flags are written
  in the rule, not read from the profile. Values are right; they would need a profile key to be edited in one place.
- **Listed-for-sale basis (item 3 above) confirmed against the guideline.** STD-8.9 prints "(a) >= 1.0 DSCR or (b) 43% maximum DTI (Q-14)"
  and "the lesser of appraised value or lowest recent listing price"; the seed encodes neither, the DTI alternative on purpose (Q-14,
  no DTI field), the listing-price basis not at all (no listing-price field). The same Q-14 DTI alternative is printed for STD-8.6.

## Not claimed

- Applicability conditions (when a rule applies) were not traced, only the figures and tables each rule reads.
- The clause-to-K-Studio links are my earlier single-reader judgement; this note inherits them.
- No variance figure exists for any of this (the seed is hand-built, so it is a stable comparison; the regen-5 side is not).
