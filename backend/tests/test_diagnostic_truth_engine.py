from app.services.intelligence_health import (
    _compare,
    _predictive,
    _extract,
    _field_mismatches,
    _decision_model,
    apply_dependency_classification,
    build_ai_forecast_scenarios,
    build_repair_brief,
    ai_chief_operating_officer,
    dependency_impact,
    executive_summary,
)


def test_opportunity_count_only_emitted_for_opportunity_layer():
    member = _extract("Member Intelligence", {"confidence_level": "substantial", "missing_assessments": [], "recommended_actions": []})
    assert "opportunity_count" not in member
    opportunity = _extract("Opportunity Intelligence", {
        "overall_priority": {"score": 74, "label": "medium"},
        "missing_evidence": [],
        "opportunities": [1, 2],
        "dashboard": {"recommendations_count": 0, "confidence": "developing"},
    })
    assert opportunity["opportunity_count"] == 2


def test_missing_count_is_only_compared_for_layers_that_own_missing_evidence():
    predictive = _compare("Predictive Intelligence", {"score": 79, "confidence": "substantial", "recommendations": 3, "priority": "medium"}, 1.0, {})
    assert "missing_count" not in predictive["difference_summary"]
    assert all(m["field"] != "missing_count" for m in predictive["owned_field_mismatches"])
    society = _compare("Society Intelligence", {"score": 60, "confidence": "substantial", "recommendations": 6, "priority": "medium", "missing_count": 5}, 1.0, {})
    assert any(m["field"] == "missing_count" for m in society["owned_field_mismatches"])


def test_predictive_priority_matches_advisory_baseline_when_readiness_is_high():
    output = _predictive({"overall_priority": {"score": 74}, "opportunities": [{}] * 12})
    extracted = _extract("Predictive Intelligence", output)
    comparison = _compare("Predictive Intelligence", extracted, 1.0, output)

    assert extracted["score"] == 79
    assert extracted["priority"] == "medium"
    assert comparison["status"] == "PASS"
    assert comparison["owned_field_mismatches"] == []


def test_decision_support_extract_prefers_diagnostic_contract_fields():
    output = {
        "confidence": "developing",
        "diagnostic": {
            "score": 74,
            "confidence": "substantial",
            "missing_count": 4,
            "priority": "medium",
            "recommendation_count": 12,
        },
        "overall_priority": {"label": "high"},
        "recommendations": [
            {"scores": {"overall_priority": {"score": 100}}, "missing_evidence": ["fallback-only"]}
        ],
    }

    extracted = _extract("Decision Support", output)

    assert extracted == {
        "score": 74,
        "confidence": "substantial",
        "priority": "medium",
        "recommendations": 12,
        "missing_count": 4,
    }


def test_decision_support_extract_accepts_legacy_diagnostic_recommendations_alias():
    extracted = _extract("Decision Support", {
        "diagnostic": {
            "score": 74,
            "confidence": "substantial",
            "missing_count": 4,
            "priority": "medium",
            "recommendations": 12,
        },
        "recommendations": [],
    })

    assert extracted["recommendations"] == 12


def test_first_point_of_failure_uses_dependency_graph_rule():
    layers = [
        {"layer": "Member Intelligence", "status": "PASS", "regression": None},
        {"layer": "Society Intelligence", "status": "WARNING", "regression": "Minor", "owned_field_mismatches": [{"field": "missing_count"}]},
        {"layer": "Opportunity Intelligence", "status": "WARNING", "regression": "Minor", "diagnostic_category": "downstream_impacted", "owned_field_mismatches": []},
    ]
    assert _decision_model(layers)["first_changed_layer"] == "Society Intelligence"
    assert dependency_impact(layers)["first_changed_layer"] == "Society Intelligence"
    assert "First drift appears in Society Intelligence" in executive_summary(layers)


def test_root_cause_selection_trace_prints_each_candidate_and_mismatch_reason():
    layers = [
        {"layer": "Member Intelligence", "status": "PASS", "regression": None, "owned_field_mismatches": []},
        {"layer": "Decision Support", "status": "WARNING", "regression": None, "diagnostic_category": "baseline_drift", "display_status": "Connected with actionable drift", "owned_field_mismatches": [{"field": "recommendations", "expected": 12, "actual": 11}]},
        {"layer": "Execution Planning", "status": "WARNING", "regression": None, "diagnostic_category": "downstream_impacted", "owned_field_mismatches": []},
    ]

    trace = _decision_model(layers)["root_cause_selection_trace"]

    assert trace["selected_layer"] is None
    assert trace["selected_because"] == "No active regression selected; warning-only runs are queued for operational verification."
    assert trace["selection_boolean_or_comparison"] == "next(name for name in DIAGNOSTIC_LAYER_ORDER if any(layer.layer == name for layer in impacted))"
    assert [candidate["layer"] for candidate in trace["candidate_layers"]] == [
        "Member Intelligence",
        "Society Intelligence",
        "Institution Intelligence",
        "Opportunity Intelligence",
        "Predictive Intelligence",
        "Decision Support",
        "Execution Planning",
        "Execution Intelligence",
        "Institutional Memory",
        "Institutional Learning",
    ]
    selected = next(candidate for candidate in trace["candidate_layers"] if candidate["layer"] == "Decision Support")
    downstream = next(candidate for candidate in trace["candidate_layers"] if candidate["layer"] == "Execution Planning")
    assert selected["pass_fail_values"]["combined_result"] is True
    assert trace["selected_layer_mismatches"] == []
    assert downstream["pass_fail_values"]["diagnostic_category not excluded"] is False


def test_zero_regression_narrative_does_not_select_root_cause_or_stale_drift_language():
    layers = [
        {"layer": "Decision Support", "status": "WARNING", "regression": None, "diagnostic_category": "baseline_drift", "display_status": "Connected with actionable drift", "owned_field_mismatches": [{"field": "recommendations", "expected": 12, "actual": 11}], "suggested_admin_action": "Verify Decision Support warning"},
        {"layer": "Execution Planning", "status": "WARNING", "regression": None, "diagnostic_category": "baseline_drift", "display_status": "Connected with actionable drift", "owned_field_mismatches": [{"field": "priority", "expected": "medium", "actual": "high"}], "suggested_admin_action": "Verify Execution Planning warning"},
        {"layer": "Execution Intelligence", "status": "WARNING", "regression": None, "diagnostic_category": "baseline_drift", "display_status": "Connected with actionable drift", "owned_field_mismatches": [{"field": "missing_count", "expected": 0, "actual": 1}], "suggested_admin_action": "Verify Execution Intelligence warning"},
    ]
    summary = executive_summary(layers)
    decision = _decision_model(layers)
    coo = ai_chief_operating_officer({"overall_health_percent": 91, "regression_count": 0, "layers": layers, "executive_summary": summary}, [])
    forecast = build_ai_forecast_scenarios({"overall_health_percent": 91, "regression_count": 0, "layers": layers}, {"expected_health_after_sprint_completion": "Completion health is not measured yet.", "confidence": 94})

    combined = " ".join([summary, decision["root_cause_selection_trace"]["selected_because"], coo["recommendation"], coo["why_this_matters"]["what_should_be_fixed_first"], forecast[0]["primary_reason"]])

    assert decision["first_changed_layer"] is None
    assert decision["root_cause_selection_trace"]["selected_layer"] is None
    assert "0 regressions detected" in summary
    assert "Clear remaining operational warnings" in coo["why_this_matters"]["what_should_be_fixed_first"]
    assert "Operational warnings remain unresolved" in forecast[0]["primary_reason"]
    for stale in ["First drift appears", "downstream affected", "fix Decision Support first", "Stabilize Decision Support diagnostic drift", "compound downstream"]:
        assert stale not in combined


def test_downstream_warnings_are_classified_not_independent_when_no_owned_mismatch():
    layers = [
        {"layer": "Society Intelligence", "status": "WARNING", "owned_field_mismatches": [{"field": "missing_count"}], "diagnostic_resolution": {}},
        {"layer": "Institution Intelligence", "status": "WARNING", "owned_field_mismatches": [], "diagnostic_resolution": {}, "plain_language_reason": "old"},
    ]
    classified = apply_dependency_classification(layers)
    downstream = classified[1]
    assert downstream["diagnostic_category"] == "downstream_impacted"
    assert downstream["fix_type"] == "RERUN_REQUIRED"
    assert downstream["upstream_root_cause_layer"] == "Society Intelligence"


def test_repair_brief_identifies_field_ownership():
    layer = _compare("Predictive Intelligence", {"score": 79, "confidence": "substantial", "recommendations": 3, "priority": "medium"}, 1.0, {})
    layer["status"] = "WARNING"
    layer["diagnostic_category"] = "downstream_impacted"
    brief = build_repair_brief(layer)
    assert brief["layer_owns_field"] is False or brief["field_that_drifted"] != "missing_count"
    assert brief["likely_issue_type"] in {"rerun-required issue", "extraction issue"}
