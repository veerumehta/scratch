"""Tests for check_plan_refs.py: what fails, what only warns, and what is left alone.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

    python -m pytest scripts/local/test_check_plan_refs.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_plan_refs as checker  # noqa: E402


def severities(text: str) -> set[str]:
    return {severity for severity, _ in checker.findings_in(text)}


def test_a_plan_item_code_in_a_commit_message_line_fails():
    assert "FAIL" in severities("- job lint gates K3 K4 K9 K10")


def test_the_same_line_in_plain_language_passes():
    assert severities("- job lint gates that bound a call, refuse an unguarded read and cap a retry") == set()


def test_a_gitignored_path_or_file_name_fails():
    for text in ("See docs/plans/plan_eval_service_contract_convergence.md for the build-out",
                 "# done_2_6_9_scope.md says so", "recorded in the CHANGELOG.md", "per CLAUDE.md",
                 "plan_JAPES_2_7_0_EXPERT_SURFACE_AND_ANSWER_CONTRACT"):
        assert "FAIL" in severities(text), text


def test_plan_phase_and_item_labels_fail():
    for text in ("# Phase 3 of the plan", "UAF item 7", "the E18 item", "kernel-salvage hardening"):
        assert "FAIL" in severities(text), text


def test_real_terms_are_left_alone():
    for text in ('policy_id="P1", version="1.0.0"', "(ARCHITECTURE.md P10)", "a version as 3 or G3",
                 "(Schema Spec v1.0 §7.1)", "plan_input_tokens and plan_estimate", "the plan call crossed the ceiling",
                 "K-means over the rows", "a hex id 0xE12F", "See https://example.com/docs/plans/overview"):
        assert "FAIL" not in severities(text), text


def test_shapes_with_legitimate_uses_only_warn():
    for text in ("item 4 of the list", "see the Studio design doc", "per the plan"):
        assert severities(text) == {"WARN"}, text


def test_the_marker_silences_a_line():
    assert severities("the vendor's Phase 3 rollout  # plan-ref-ok") == set()


def test_a_message_file_ignores_git_comment_lines_and_reports_hard_findings_only(tmp_path):
    message = tmp_path / "msg"
    message.write_text("Plain headline\n\n# K9 in a git comment line\nitem 4 of the list\n")
    assert checker.check_message(str(message)) == []
    message.write_text("job lint gates K3 K4\n")
    assert len(checker.check_message(str(message))) == 1


def test_the_self_test_passes():
    assert checker.self_test() == 0
