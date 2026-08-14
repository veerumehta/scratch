"""Behavioural tests for the Acra DSCR eligibility policy.

Drop into jaci as tests/scenarios/acra_dscr/test_acra_eligibility.py (adjust PACK below).
Verified green against japes 2.4.1 + the working-tree MatrixCondition change set,
2026-08-13: 17/17.

Each case is a real loan shape, not a schema assertion -- the point is that the authored
grid resolves to the same cell a human picks off the DSCR Program Summary PDF.
"""
from pathlib import Path

import pytest
import yaml

from jazzx_sdk.fabric.canonical.condition_evaluator import (
    RATIO_PROFILE_CONTEXT_KEY,
    get_condition_evaluator,
)
from jazzx_sdk.fabric.canonical.policy import Verdict, load_policies
from jazzx_sdk.fabric.canonical.profiles import PolicyProfile

PACK = Path(__file__).parents[3] / "config" / "packs" / "acra_dscr_core"
POLICY_YAML = PACK / "policies" / "eligibility.yaml"
PROFILE_YAML = PACK / "profiles" / "acra_dscr_profile.yaml"


@pytest.fixture(scope="module")
def policy():
    return load_policies(str(POLICY_YAML))[0]


@pytest.fixture(scope="module")
def profile():
    return PolicyProfile.model_validate(yaml.safe_load(PROFILE_YAML.read_text()))


async def _verdict(rule, ctx, profile):
    """Applicability first (a non-SATISFIED pre-check means the rule never fires), then condition."""
    ctx = dict(ctx)
    ctx[RATIO_PROFILE_CONTEXT_KEY] = profile
    if rule.applicability is not None:
        pre = await get_condition_evaluator(rule.applicability.kind).evaluate(rule.applicability, ctx)
        if pre.verdict is not Verdict.SATISFIED:
            return Verdict.NOT_APPLICABLE
    out = await get_condition_evaluator(rule.condition.kind).evaluate(rule.condition, ctx)
    return out.verdict


B = dict(property_state="CA", property_type="sfr", gross_rental_income=5000, pitia=4000, reserves_months=6)
CASES = [
 ("740 / $900k / purchase / CLTV 85.0 (at cap)", {**B, "loan_amount":900000,"fico":740,"loan_purpose":"purchase","cltv_pct":85},"ACRA-ELIG-CLTV-GRID",Verdict.SATISFIED),
 ("same but CLTV 85.01 (over cap)", {**B,"loan_amount":900000,"fico":740,"loan_purpose":"purchase","cltv_pct":85.01},"ACRA-ELIG-CLTV-GRID",Verdict.VIOLATED),
 ("620 / $1.6M / R&T -> published NA cell", {**B,"loan_amount":1600000,"fico":620,"loan_purpose":"rate_term_refinance","cltv_pct":50},"ACRA-ELIG-CLTV-GRID",Verdict.VIOLATED),
 ("690 / $2.5M -> band-3 <700 NA", {**B,"loan_amount":2500000,"fico":690,"loan_purpose":"purchase","cltv_pct":60},"ACRA-ELIG-CLTV-GRID",Verdict.VIOLATED),
 ("FICO exactly 780 -> top tier", {**B,"loan_amount":1000000,"fico":780,"loan_purpose":"cash_out_refinance","cltv_pct":80},"ACRA-ELIG-CLTV-GRID",Verdict.SATISFIED),
 ("loan exactly $1,500,000 -> band 1 (cap 80)", {**B,"loan_amount":1500000,"fico":700,"loan_purpose":"purchase","cltv_pct":80},"ACRA-ELIG-CLTV-GRID",Verdict.SATISFIED),
 ("loan $1,500,001 -> band 2 (cap 75)", {**B,"loan_amount":1500001,"fico":700,"loan_purpose":"purchase","cltv_pct":80},"ACRA-ELIG-CLTV-GRID",Verdict.VIOLATED),
 ("ineligible state SD", {**B,"property_state":"SD","loan_amount":500000,"fico":740,"loan_purpose":"purchase","cltv_pct":70},"ACRA-STATE-INELIGIBLE",Verdict.VIOLATED),
 ("eligible state CA (not_in operator)", {**B,"loan_amount":500000,"fico":740,"loan_purpose":"purchase","cltv_pct":70},"ACRA-STATE-INELIGIBLE",Verdict.SATISFIED),
 ("CLTV 82 + DSCR 1.10 -> fails 1.20 gate", {**B,"loan_amount":800000,"fico":760,"loan_purpose":"purchase","cltv_pct":82,"gross_rental_income":4400},"ACRA-HIGH-LTV-DSCR",Verdict.VIOLATED),
 ("CLTV 78 -> high-LTV gate not applicable", {**B,"loan_amount":800000,"fico":760,"loan_purpose":"purchase","cltv_pct":78,"gross_rental_income":4400},"ACRA-HIGH-LTV-DSCR",Verdict.NOT_APPLICABLE),
 ("CLTV 82 + condotel -> property type fails", {**B,"property_type":"condotel","loan_amount":800000,"fico":760,"loan_purpose":"purchase","cltv_pct":82},"ACRA-HIGH-LTV-PROPERTY-TYPE",Verdict.VIOLATED),
 ("DSCR 0.90 cash-out CLTV 66 -> sub-1.0 cap 65", {**B,"loan_amount":700000,"fico":700,"loan_purpose":"cash_out_refinance","cltv_pct":66,"gross_rental_income":3600},"ACRA-SUB-1-DSCR-CLTV",Verdict.VIOLATED),
 ("$2.4M + DSCR 0.95 -> >$2M needs 1.0", {**B,"loan_amount":2400000,"fico":760,"loan_purpose":"purchase","cltv_pct":65,"gross_rental_income":9500,"pitia":10000},"ACRA-OVER-2M-DSCR",Verdict.VIOLATED),
 ("ITIN 660 purchase CLTV 66 -> cap 65", {**B,"loan_amount":600000,"fico":660,"loan_purpose":"purchase","cltv_pct":66,"citizenship_type":"itin","gross_rental_income":3000,"pitia":2000},"ACRA-ITIN-CLTV",Verdict.VIOLATED),
 ("missing FICO -> indeterminate, never a pass", {**B,"loan_amount":900000,"loan_purpose":"purchase","cltv_pct":85},"ACRA-ELIG-CLTV-GRID",Verdict.INDETERMINATE),
 ("FICO 599 -> below-grid row is authored NA", {**B,"loan_amount":900000,"fico":599,"loan_purpose":"purchase","cltv_pct":50},"ACRA-ELIG-CLTV-GRID",Verdict.VIOLATED),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("label,ctx,rule_id,expected", CASES, ids=[c[0] for c in CASES])
async def test_acra_eligibility(label, ctx, rule_id, expected, policy, profile):
    rule = {r.rule_id: r for r in policy.rules}[rule_id]
    assert await _verdict(rule, ctx, profile) is expected


def test_grid_is_fully_authored(profile):
    """99 cells = 3 loan-amount bands x 11 FICO bands x 3 purposes. No hole may be absent:
    an absent cell raises KeyError at runtime; an ineligible one must be an authored "NA"."""
    grid = profile.tables["max_cltv_grid"]
    assert len(grid) == 99
    assert sum(1 for v in grid.values() if v != "NA") == 70