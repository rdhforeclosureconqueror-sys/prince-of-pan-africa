from app.services import intelligence_health as ih


def test_phase2_history_comparison_trends_pipeline_timeline_and_performance(monkeypatch, tmp_path):
    monkeypatch.setattr(ih, "DIAGNOSTIC_HISTORY_STORAGE_PATH", tmp_path / "history.json")
    ih._DIAGNOSTIC_HISTORY.clear()

    first = ih.run_full_intelligence_diagnostic()
    second = ih.run_full_intelligence_diagnostic()
    history = ih.diagnostic_history()

    assert (tmp_path / "history.json").exists()
    assert history[0]["diagnostic_id"] == second["diagnostic_id"]
    assert second["environment"]
    assert "build_commit" in second
    assert second["overall_status"] in {"PASS", "WARNING", "FAIL"}
    assert second["pass_fail_summary"]["passed"] + second["pass_fail_summary"]["warnings"] + second["pass_fail_summary"]["failed"] == len(second["layers"])

    comparison = second["comparison_to_previous"]
    assert comparison["available"] is True
    assert {row["metric"] for row in comparison["rows"]} >= {"Health Score", "API Latency", "Diagnostic Duration", "Failures", "Warnings", "Public Verification"}
    assert all(row["direction"] in {"improvement", "unchanged", "regression"} for row in comparison["rows"])

    trends = second["trends"]["10"]
    assert set(trends) >= {"overall_health_score", "response_time_ms", "api_latency_ms", "diagnostic_duration_ms", "failure_count", "regression_count"}
    assert trends["overall_health_score"][-1]["value"] == second["overall_health_percent"]

    assert second["pipeline"]["overall_status"] in {"Intelligence Pipeline Healthy", "Pipeline Warning", "Pipeline Failure"}
    assert [step["label"] for step in second["pipeline"]["steps"]] == [
        "Diagnostic Generated", "Report Stored", "HTML Available", "Embedded JSON Valid", "JSON Endpoint Reachable",
        "Markdown Endpoint Reachable", "Public Report Sanitized", "Read Only Confirmed", "Browser Verification Passed", "AI Ready",
    ]
    assert second["performance_summary"]["total_completed_checks"] == len(second["layers"])
    assert second["timeline"][0]["event"] == "Diagnostic Started"
    assert "Overall platform health" in second["ai_summary"]


def test_phase2_root_cause_classification_and_public_report_pipeline(monkeypatch, tmp_path):
    monkeypatch.setattr(ih, "DIAGNOSTIC_HISTORY_STORAGE_PATH", tmp_path / "history.json")
    monkeypatch.setattr(ih, "PUBLIC_REPORT_STORAGE_DIR", tmp_path / "reports")
    ih._DIAGNOSTIC_HISTORY.clear()
    ih._PUBLIC_DIAGNOSTIC_REPORTS.clear()

    assert ih._classify_root_cause("JSON parse failed at reverse proxy")["category"] == "Reverse Proxy"
    timeout = ih._classify_root_cause("request timed out")
    assert timeout["category"] == "Timeout"
    assert timeout["heuristic"] is True

    run = ih.run_full_intelligence_diagnostic()
    report = ih.generate_public_diagnostic_report(run)
    history = ih.diagnostic_history()
    assert history[0]["report_token"] == report["token"]
    assert history[0]["pipeline"]["overall_status"] == "Intelligence Pipeline Healthy"
    public = ih.sanitize_diagnostic_for_public_report(run)
    assert "previous_run_comparison" in public
    assert "performance_timings" in public
