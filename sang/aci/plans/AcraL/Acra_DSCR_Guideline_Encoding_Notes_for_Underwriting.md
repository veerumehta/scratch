---
title: "Acra DSCR Guidelines: How the Eligibility Engine Reads Them"
subtitle: "Standard and Platinum Select, for underwriting review"
date: "September 29, 2026"
author: "JazzX Team"
---

# Purpose

The JazzX eligibility engine checks each DSCR loan against Acra's two consolidated guidelines:

- **Acra DSCR Standard Consolidated Guidelines v1.0** (Program Summary 8.17.2026 and the Seller's
  Guide DSCR excerpt of August 28, 2026), cited as STD-x.
- **Acra DSCR Platinum Select Consolidated Guidelines v1.0** (Platinum Select Program Summary
  8.17.2026 and the same excerpt), cited as PLAT-x.

Each loan is checked against the guideline of the program it applies for. A small set of process
gates from the Commercial DSCR Loan Process Flow (July 2026) applies to both programs.

This note is for underwriters. It sets out:

1. how the engine reads the guidelines in general;
2. where it has taken a particular reading of a provision, pending Acra's answer;
3. what it does not check yet, which stays with underwriting.

Question numbers (Q-nn) refer to Appendix A of each consolidation. The Standard and Platinum
documents number their questions separately.

# 1. How the engine reads the guidelines

**Caps combine as the lowest one that applies.** The program matrix sets the starting maximum
CLTV. Every other applicable cap (borrower, property, credit, transaction) can only lower it, and
the loan is held to the lowest. The engine reports which provision set the binding cap. How Acra
combines caps is open (Standard Q-07, Platinum Q-08). The declining-market -5% is therefore not
applied yet (section 4).

**LTV provisions are applied to CLTV.** Where a provision is stated in LTV but the matrix is in
CLTV (for example "LTV > 80.00%" in STD-3.16), the engine applies it to CLTV (Standard Q-17,
Platinum Q-16).

**Terms that must be stated are treated as failing until they are.** A loan that leaves any of
these blank is held to the stricter answer:

| Item | If not stated |
|----|----|
| Prepayment penalty structure | Fails every state buy-out rule that applies |
| Channel (Platinum) | Held to the Correspondent limits (DSCR 1.2; 60% CLTV at FICO 700-719) |
| Housing history (Platinum) | Fails the 0x30x12 requirement |
| Current lease (cash-out refinance, Platinum) | Fails PLAT-1.5 |
| 0x30x24 mortgage history | Fails where it is required (escrow waiver; 1 or no score) |
| Months since a flagged credit event | Read as 0 months, the least seasoned tier |
| Months of ownership (vacant cash-out, Standard) | Read as 0, below the 15 months required |
| Interest rate (Illinois, individual, over $250,000) | The application is refused until stated |

**Features must be flagged to apply.** The engine applies these provisions only when the loan
says they are present, so underwriting needs to flag them when it finds them:

- first-time homebuyer
- rural / unique property
- vacant property
- listed for sale in the last six months
- delayed financing
- mixed use, adult care or assisted living (Standard)
- a bankruptcy or foreclosure, or a short sale, deed-in-lieu or modification, with the months since
- 1 or no credit score, or deficient tradelines
- escrow waiver requested
- Interest Only 10 Yr / 40 Year Term (Standard)

**Housing history on Standard.** The Standard caps for 1x30x12, 0x60x12, 0x90x12 and 0x120x12
apply when the history is stated. A Standard loan that does not state it gets no housing-history
cap. The labels themselves are open (Standard Q-05, Platinum Q-06).

**Credit events are two kinds.** Bankruptcy or foreclosure is one; short sale, deed-in-lieu or
modification is the other. Each carries its own seasoning. Forbearance ("FB Taken <= 6 Mos:
Case-by-case", STD-7.11) is not checked (section 4).

**No Ratio files.** The situation-specific DSCR minimums cannot be checked on a No Ratio file,
because there is no ratio to check. These are the first-time homebuyer 1.15, rural 1.0, condo type
1.0, vacant refinance, listed-for-sale, mixed-use and 1-or-no-score minimums. The No Ratio caps and
minimum FICO (STD-3.17) and the over-$2,000,000 rule (STD-2.6) do apply. Whether No Ratio is
available in those situations at all is Standard Q-13; please review such files by hand until then.

**Qualifying rent is taken as supplied.** The engine uses the rent on the file. It does not choose
between the lesser-of formula and the higher-of note (Standard Q-01), or apply Platinum's
greater-of rule (Platinum Q-03).

# 2. Standard program: readings taken

| Provision | Engine's reading | Open point |
|----|----|----|
| Summary version (STD-1.4 table) | 8.17.2026 governs: SD the only ineligible state; Alaska must buy out; Mississippi single-unit allows buy-out or the 5-year step only | Q-23 |
| FICO below 600, loans up to $1,500,000 (STD-2.2) | Ineligible, as no matrix row exists | Q-16 |
| Delayed financing (STD-1.4, 2.4) | Loan amount capped at $1,500,000; the matrix column is the purpose on the file | Q-06 |
| Above 80% LTV (STD-3.16, 8.2) | SFR, townhome, PUD, or warrantable condo outside Florida | Q-17 |
| Florida non-warrantable condo, condotel / PUDtel (STD-8.1) | The property-type cap less 5%: non-warrantable condo 75% / 70% / 70%, condotel 70% / 65% / 60% | Q-07 |
| Non-Permanent Resident (STD-4.3) | Two independent limits: loan amount up to $1.5M, and CLTV up to 80% | Q-21 |
| Foreign National (STD-4.4) | 70% / 65% caps; no maximum loan amount applied | Q-21 |
| "Foreign National ineligible" under Credit Requirements (STD-4.8) | Not applied, since its scope is unstated | Q-04 |
| ITIN tier "FICO 700" (STD-4.5) | 700 and above | Q-03 |
| 1 or no score / deficient tradelines (STD-7.3) | Applies to 0 or 1 reported score, or to tradelines short of STD-7.2: 65% cap, DSCR 1.1, 0x30x24 | none |
| Vacant rate and term refinance (STD-8.6) | 70% below $1,000,000; 65% from $1,000,000 to below $2,000,000; ineligible at $2,000,000 and above | Q-10 |
| Vacant cash-out refinance (STD-8.7) | 60% below $1,500,000; ineligible at $1,500,000 and above, which the sources do not address | Q-10 |
| First-time homebuyer "Must Impound" (STD-4.10) | Read as no escrow waiver; the same for vacant refinances and listed-for-sale | Q-15 |
| Escrow waiver (STD-7.12) | Loan up to $1.5M, CLTV up to 80%, FICO 700, 0x30x24; Foreign Nationals ineligible | none |

# 3. Platinum Select program: readings taken

| Provision | Engine's reading | Open point |
|----|----|----|
| FICO 720 (PLAT-2.1) | Takes the 700 row as printed, so cash-out is capped at 55% | Q-01 |
| Correspondent 700-719 (PLAT-2.3) | 60% for every purpose; the lower matrix figure still governs cash-out | Q-01 |
| Channel minimum DSCR (PLAT-3.7) | 1.0 for every loan; 1.2 unless the loan is stated as Wholesale | none |
| "U.S. Terrs." (PLAT-1.16) | Puerto Rico, Guam, U.S. Virgin Islands, American Samoa, Northern Mariana Islands | none |
| Property types (PLAT-7.1, 7.2) | Only the listed types. Of 2-4 units, only two units. Three- and four-unit, manufactured and PUDtel are treated as ineligible. Mixed use is not checked. | Q-07 |
| No Ratio (PLAT-1.8) | Ineligible | Q-12 |
| Previous credit events, 48 months (PLAT-6.8) | Applied separately to bankruptcy/foreclosure and to short sale, deed-in-lieu or modification | Q-06 |
| Tradelines (PLAT-6.3) | With 2 or fewer scores, the tradeline requirement must be met; 1 or no score is not treated separately | Q-05 |
| Escrow waiver (PLAT-6.13) | Loan up to $1.5M and 0x30x24; no CLTV or FICO limit applied; Section 35 not checked | Q-09, Q-14 |
| Interest-only (PLAT-9.3, 9.4) | 75% cap; no minimum loan amount or FICO applied; the 10/40 product is not offered | Q-09 |
| Listed for sale (PLAT-7.8) | 65% cap, 24 months reserves, no interest-only, impounds | Q-13 |
| Delayed financing (PLAT-1.4, 2.4) | Loan amount capped at $1,500,000 | Q-02 |

# 4. Not checked yet: stays with underwriting

These provisions are not checked by the engine. Most wait on an answer from Acra; some need
information the application does not carry today.

| Provision | Standard | Platinum Select |
|----|----|----|
| Declining market -5% | STD-1.14, Q-07 | PLAT-1.17, Q-08 |
| Cash-in-hand limits when LTV > 65% | STD-2.3, Q-17 | PLAT-2.2, Q-16 |
| Loan amount in $50 increments | STD-1.10 | PLAT-1.13 |
| 10% own funds with gift funds | STD-1.12, 9.1 | PLAT-1.15, 8.1 |
| Seller concessions | Checked (3%) | Not addressed, Q-09 |
| Minimum prepayment term (vacant refinances; listed for sale) | STD-11.2, Q-24 | PLAT-10.2, Q-19 |
| Subordinate financing and HELOC CLTV | STD-10.7, Q-18 | PLAT-3.6, Q-15 |
| Rent loss insurance, or 2 months reserves per month missing | STD-8.12 to 8.14, Q-11 | PLAT-7.10 to 7.12, Q-10 |
| Forbearance or lates in 12 months: 2 months rent receipts or 12 months reserves | STD-3.15, Q-20 | PLAT-3.12, Q-17 |
| Forbearance taken within 6 months, case-by-case | STD-7.11, Q-05 | none |
| Short-term rental ledgers as actual rent | STD-3.13, Q-02 | STR ineligible |
| Seasoning, verification and repatriation of funds | STD-9.2 to 9.5, Q-12 | PLAT-8.2 to 8.5, Q-11 |
| ARM terms and margins | STD-10.2 | PLAT-9.2 |
| Foreign national program documentation | STD-5.1 to 5.12 | Not eligible |
| Entity, guarantor and trust documentation beyond the document-completeness check | STD-6.1 to 6.13 | PLAT-5.1 to 5.13 |
| Rent schedules (1007 / 1025) | STD-1.7, 3.9 to 3.11, Q-08 | PLAT-1.10, 3.9 to 3.10, Q-04 |

# 5. The answers that would change the engine most

**Standard:** Q-07 (how caps combine, including the declining market and Florida adjustments),
Q-10 (vacant refinance boundaries), Q-13 (No Ratio where a minimum DSCR applies), Q-16 (FICO below
600), Q-21 (Non-Permanent Resident and Foreign National limits), Q-23 (which Summary version
governs), Q-24 (state restrictions against minimum prepayment terms).

**Platinum Select:** Q-01 (the 721 threshold and a score of 720), Q-06 (which credit events the 48
months covers), Q-07 (property types not listed), Q-08 (how caps combine), Q-09 (interest-only and
escrow-waiver limits), Q-12 (No Ratio).

When an answer arrives, the engine's reading is updated to match and the change is listed against
the question number.
