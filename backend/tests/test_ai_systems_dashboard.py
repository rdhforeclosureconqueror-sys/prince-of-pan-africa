from app.services.intelligence_health import (
    dependency_impact,
    executive_summary,
    recommended_next_actions,
    run_full_intelligence_diagnostic,
    sanitize_diagnostic_for_public_report,
)


def sample_layers():
    return [
        {"layer": "Member Intelligence", "status": "PASS", "regression": None},
        {"layer": "Society Intelligence", "status": "PASS", "regression": None},
        {"layer": "Institution Intelligence", "status": "PASS", "regression": None},
        {"layer": "Opportunity Intelligence", "status": "WARNING", "regression": "Minor"},
        {"layer": "Predictive Intelligence", "status": "PASS", "regression": None},
        {"layer": "Decision Support", "status": "WARNING", "regression": "Minor"},
        {"layer": "Execution Planning", "status": "WARNING", "regression": "Minor"},
        {"layer": "Execution Intelligence", "status": "PASS", "regression": None},
        {"layer": "Institutional Memory", "status": "PASS", "regression": None},
        {"layer": "Institutional Learning", "status": "PASS", "regression": None},
    ]


def test_executive_summary_first_drift_downstream_and_stable_detection():
    impact = dependency_impact(sample_layers())
    assert impact["first_changed_layer"] == "Opportunity Intelligence"
    assert impact["downstream_affected_layers"] == ["Decision Support", "Execution Planning"]
    assert "Member Intelligence" in impact["stable_layers"]
    assert "Institutional Learning" in impact["stable_layers"]
    summary = executive_summary(sample_layers())
    assert "3 regressions detected" in summary
    assert "First drift appears in Opportunity Intelligence" in summary
    assert "No production records were modified" in summary


def test_suggested_admin_actions_and_read_only_run_contract():
    run = run_full_intelligence_diagnostic()
    assert run["production_writes"] == 0
    assert run["workflow_execution"] is False
    assert run["assignment_count"] == 0
    assert run["notification_count"] == 0
    assert run["persistence_of_intelligence_outputs"] is False
    assert run["recommended_next_actions"] == recommended_next_actions(run["layers"])
    assert "Review scoring logic" in run["recommended_next_actions"]
    assert all("suggested_admin_action" in layer for layer in run["layers"])
    assert all("why_this_changed" in layer for layer in run["layers"])


def test_public_report_sanitization_includes_summary_explanations_dependency_and_no_write_confirmation():
    run = run_full_intelligence_diagnostic()
    public = sanitize_diagnostic_for_public_report(run)
    raw = str(public)
    assert public["overall_summary"]
    assert public["dependency_impact"]["ordered_chain"]
    assert public["no_write_confirmation"]["production_writes"] == 0
    assert public["no_write_confirmation"]["workflow_execution"] is False
    assert all("why_this_changed" in layer for layer in public["layers"])
    assert "debug_payload" not in raw
    assert "diagnostic-admin@example.test" not in raw
    assert "password_hash" not in raw
    assert "private" not in raw.lower()
