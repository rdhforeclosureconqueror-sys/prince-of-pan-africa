import pytest

pytest.importorskip("sqlalchemy", reason="SQLAlchemy is required for intelligence validation suite tests")

from app.services.intelligence_health import run_full_intelligence_diagnostic


def test_validation_suite_proves_layer_connectivity_and_scoring_integrity():
    run = run_full_intelligence_diagnostic()
    suite = run["validation_suite"]

    expected_layers = [layer["layer"] for layer in run["layers"]]
    assert [item["layer"] for item in suite["connectivity"]] == expected_layers
    assert suite["system_readiness_report"]["layer_connectivity_status"] == "PASS"
    assert suite["system_readiness_report"]["scoring_integrity"] == "PASS"
    assert all("starting_baseline" in item for item in suite["scoring"])
    assert all("fields_causing_drift" in item for item in suite["scoring"])


def test_decision_model_keeps_root_cause_dependency_and_sprint_consistent():
    run = run_full_intelligence_diagnostic()
    decision = run["validation_suite"]["decision_model"]
    first = decision["first_changed_layer"]

    assert run["dependency_impact"]["first_changed_layer"] == first
    assert run["dependency_impact"]["highest_priority_layer"] == decision["highest_priority_layer"]
    if first:
        assert first in run["root_cause_analysis"][0]
        assert first in run["executive_summary"]
        assert first in run["ai_chief_operating_officer"]["sprint_planning"]["sprint_goal"]


def test_recommendations_are_deduped_traceable_and_readiness_is_conservative():
    run = run_full_intelligence_diagnostic()
    recs = run["validation_suite"]["recommendations"]
    assert len(recs) == len({rec["id"] for rec in recs})
    for rec in recs:
        assert rec["source_layer"]
        assert rec["reason"]
        assert rec["affected_layers"]
        assert rec["expected_health_impact"]
        assert rec["confidence"]

    sprint = run["ai_chief_operating_officer"]["sprint_planning"]
    unresolved = [layer for layer in run["layers"] if layer["status"] != "PASS"]
    if unresolved:
        assert sprint["expected_health_after_sprint_completion"] != "100%"


def test_public_pipeline_and_ai_ready_share_verification_source_of_truth():
    run = run_full_intelligence_diagnostic()
    truth = run["verification_source_of_truth"]
    pipeline_truth = run["pipeline"]["verification_source_of_truth"]
    assert truth == pipeline_truth
    assert truth["source"] == "intelligence_layer_validation_suite"
    assert truth["intelligence_pipeline"] == "PASS"
    assert truth["ai_ready"] == "PASS"
