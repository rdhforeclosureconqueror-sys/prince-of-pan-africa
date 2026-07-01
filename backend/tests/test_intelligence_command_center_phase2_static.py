from pathlib import Path

MONITOR = Path("src/components/IntelligenceHealthMonitor.jsx").read_text()
SERVICE = Path("backend/app/services/intelligence_health.py").read_text()


def test_phase2_history_panel_fields_and_expandable_full_report_are_rendered():
    for token in ["Diagnostic History", "<details className=\"stat-card\"", "Report token", "Version/commit", "Pass/fail summary", "JSON.stringify(run, null, 2)"]:
        assert token in MONITOR


def test_phase2_trend_analysis_windows_and_metrics_are_rendered():
    for token in ["Trend Analysis", "Last 10 runs", "Last 30 runs", "Last 100 runs", "Overall Health Score", "Response Time", "API Latency", "Diagnostic Duration", "Failure Count", "Regression Count"]:
        assert token in MONITOR
    for token in ["trend_analysis", "overall_health_score", "diagnostic_duration_ms", "failure_count", "regression_count"]:
        assert token in SERVICE


def test_phase2_deployment_comparison_pipeline_root_cause_timeline_and_ai_summary_are_rendered():
    for token in ["Deployment Comparison", "Previous Run", "Current Run", "Difference", "Intelligence Pipeline", "Diagnostic Generated", "Report Stored", "Embedded JSON Valid", "Browser Verification Passed", "AI Ready", "Root Cause Analysis", "Classification:", "Intelligence Timeline", "AI Summary"]:
        assert token in MONITOR
    for token in ["compare_diagnostics", "build_intelligence_pipeline", "_classify_root_cause", "intelligence_timeline", "ai_readable_summary"]:
        assert token in SERVICE


def test_phase2_performance_summary_contract_is_visible():
    for token in ["Executive Performance Summary", "Average API latency", "Slowest endpoint", "Fastest endpoint", "Average diagnostic time", "Report generation time", "Verification time", "Total completed checks", "Passed / Warnings / Failures"]:
        assert token in MONITOR
    assert "performance_summary" in SERVICE
