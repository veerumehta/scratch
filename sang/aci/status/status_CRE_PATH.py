# CRE Policy Expert - Patch Instructions
# =========================================
# Apply these two changes to existing files after copying the policies/ directory.
#
# Author: Virendra Mehta


# ===========================================================================
# PATCH 1: schemas/case_context.py
# Add program_id field to LoanApplication
# Location: after the `occupancy_stated` field, before `# Metadata`
# ===========================================================================

# FIND this block in LoanApplication:
#
#     occupancy_stated: float | None = Field(default=None, description="Physical occupancy percentage (stated)")
#
#     # Metadata
#     submission_date: datetime = Field(default_factory=datetime.utcnow)

# REPLACE WITH:
#
#     occupancy_stated: float | None = Field(default=None, description="Physical occupancy percentage (stated)")
#
#     # Policy overlay selector
#     program_id: str | None = Field(
#         default=None,
#         description=(
#             "Lender program identifier used by CREPolicyExpert to select the "
#             "correct institutional policy overlay via OVERLAY_MAP. "
#             "Examples: 'maa-bridge-2026', 'cfi-stabilized', "
#             "'regional-bank-multifamily'. "
#             "None = core policies only (no institutional overlay applied)."
#         ),
#     )
#
#     # Metadata
#     submission_date: datetime = Field(default_factory=datetime.utcnow)


# ===========================================================================
# PATCH 2: conductor.py
# (a) Add import after CREToolRegistry import
# (b) Instantiate policy_expert in __init__
# (c) Add PolicyExpert call before Governor turn in run_underwriting()
# ===========================================================================

# --- (a) ADD import line ---
# FIND:
#     from jaci.scenarios.cre_underwriting.tools.registry import CREToolRegistry
#     from jaci.common.utils.prompt_loader import load_mode_prompt
#
# REPLACE WITH:
#     from jaci.scenarios.cre_underwriting.tools.registry import CREToolRegistry
#     from jaci.scenarios.cre_underwriting.policies import CREPolicyExpert
#     from jaci.common.utils.prompt_loader import load_mode_prompt


# --- (b) ADD policy_expert instantiation in __init__ ---
# FIND:
#         self.max_iterations = max_iterations
#
#         # Expert registry integration (JAPES v1.5.0)
#
# REPLACE WITH:
#         self.max_iterations = max_iterations
#
#         # PolicyExpert for overlay-aware threshold resolution
#         self.policy_expert = CREPolicyExpert(pack_id=pack_id or "cre-underwriting-core")
#
#         # Expert registry integration (JAPES v1.5.0)


# --- (c) ADD PolicyExpert call before Governor turn ---
# FIND the Governor Turn comment block:
#
#         # ─── Governor Turn ───────────────────────────────────────────
#         # Enforces policy gates (LTV, DSCR, occupancy, sponsor net worth)
#         governor_result = await self.governor.run(ctx, recommendation)
#
# REPLACE WITH the full block below:

CONDUCTOR_GOVERNOR_REPLACEMENT = '''
        # ─── Governor Turn ───────────────────────────────────────────
        # Enforces policy gates (LTV, DSCR, occupancy, sponsor net worth)

        # Step 1: PolicyExpert resolves applicable policies and checks
        # compliance against underwritten metrics (advisory gate).
        # output_classification=GUIDANCE_REFS - advisory only.
        from jazzx_sdk.experts.base import ExpertRequest

        _nw_ratio = (
            loan_application.sponsor_net_worth / loan_application.loan_amount
            if loan_application.sponsor_net_worth and loan_application.loan_amount
            else None
        )
        _liq_ratio = (
            loan_application.sponsor_liquidity / loan_application.loan_amount
            if loan_application.sponsor_liquidity and loan_application.loan_amount
            else None
        )

        policy_request = ExpertRequest(
            operation="check_compliance",
            context={
                "program_id": loan_application.program_id,
                "dscr": recommendation.underwritten_dscr,
                "ltv": recommendation.underwritten_ltv,
                "debt_yield_pct": (
                    (recommendation.underwritten_noi / loan_application.loan_amount * 100)
                    if recommendation.underwritten_noi and loan_application.loan_amount
                    else None
                ),
                "physical_occupancy": recommendation.underwritten_occupancy,
                "sponsor_nw_to_loan_ratio": _nw_ratio,
                "sponsor_liquidity_to_loan_ratio": _liq_ratio,
            },
            pack_id=self.pack_id,
            trace_id=ctx.context_id,
        )
        policy_response = await self.policy_expert.execute(policy_request)

        if policy_response.success and policy_response.result:
            compliance = policy_response.result
            if not compliance.allowed:
                logger.warning(
                    f"PolicyExpert compliance check: {len(compliance.policy_violations)} "
                    f"violation(s) - {compliance.rationale}"
                )
                # Surface violations into key_concerns for the Governor LLM
                # (not a hard block - Governor owns the binding decision)
                for v in compliance.policy_violations:
                    recommendation.key_concerns.append(
                        f"Policy gate [{v[\'rule_id\']}]: "
                        f"{v[\'field\']}={v[\'actual\']:.4g} "
                        f"(required {v[\'required\']})"
                    )
            else:
                logger.info(
                    f"PolicyExpert: all {len(compliance.applied_policies)} "
                    f"policy gates passed"
                )
        else:
            logger.warning(f"PolicyExpert.execute failed: {policy_response.error}")

        # Step 2: Governor LLM enforces binding policy decision
        governor_result = await self.governor.run(ctx, recommendation)
'''
