from app.services import intelligence_health as ih


def test_duplicate_recommendations_are_consolidated_into_ranked_initiatives():
    layers = []
    duplicate = "Review Opportunity Intelligence scoring and qualifying-opportunity rules before updating baselines."
    for name in ["Opportunity Intelligence", "Predictive Intelligence", "Decision Support", "Execution Planning"]:
        layers.append({
            "layer": name,
            "status": "WARNING",
            "regression": "Minor",
            "score_delta": -4,
            "confidence_score": 94,
            "suggested_admin_action": duplicate,
        })

    initiatives = ih.synthesize_ai_coo_initiatives(layers, [])

    assert len(initiatives) == 1
    assert initiatives[0]["title"] == "Stabilize Opportunity Intelligence"
    assert initiatives[0]["affected_layers"] == ["Opportunity Intelligence", "Predictive Intelligence", "Decision Support", "Execution Planning"]
    assert initiatives[0]["source_recommendation_count"] == 1
    assert initiatives[0]["status"] == "recommended"


def test_sprint_tasks_are_not_repeated_after_initiative_synthesis():
    duplicate = {
        "title": "Opportunity Intelligence WARNING",
        "suggested_fix": "Review Opportunity Intelligence scoring and qualifying-opportunity rules before updating baselines.",
        "confidence": 94,
    }
    run = {
        "overall_health_percent": 76,
        "regression_count": 4,
        "executive_summary": "4 regressions detected.",
        "layers": [
            {"layer": layer, "status": "WARNING", "regression": "Minor", "score_delta": -4, "confidence_score": 94, "suggested_admin_action": duplicate["suggested_fix"]}
            for layer in ["Opportunity Intelligence", "Predictive Intelligence", "Decision Support", "Execution Planning"]
        ],
    }

    coo = ih.ai_chief_operating_officer(run, [duplicate, duplicate, duplicate])
    tasks = coo["sprint_planning"]["highest_roi_tasks"]

    assert tasks == list(dict.fromkeys(tasks))
    assert len(tasks) == 1
    assert coo["forecast_scenarios"][0]["scenario"] == "If no action is taken"
    assert coo["forecast_scenarios"][1]["scenario"] == "If recommended sprint is completed"
