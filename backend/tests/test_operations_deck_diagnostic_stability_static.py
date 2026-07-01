from pathlib import Path

MONITOR = Path("src/components/IntelligenceHealthMonitor.jsx").read_text()
OPS_DASHBOARD = Path("src/pages/AdminOperationsDashboard.jsx").read_text()
API = Path("src/api/societyBuilder.js").read_text()


def test_operations_deck_mounts_health_monitor_without_blocking_initial_load():
    assert "<IntelligenceHealthMonitor />" in OPS_DASHBOARD
    assert 'api("/discord/diagnostics").catch(() => null)' in OPS_DASHBOARD
    assert 'api("/member/assessments/sync-diagnostics").catch(() => null)' in OPS_DASHBOARD


def test_health_endpoint_failures_render_fallback_cards_instead_of_throwing():
    assert "loadHistory().catch" not in MONITOR
    assert "Last run could not be loaded" in MONITOR
    assert "Diagnostics unavailable" in MONITOR
    assert "setHistory([])" in MONITOR
    assert "adminErrorMessage" in MONITOR


def test_empty_null_history_and_missing_layer_data_are_guarded():
    assert "normalizeHistory" in MONITOR
    assert "asArray(payload?.history)" in MONITOR
    assert "safeObject(layer.expected)" in MONITOR
    assert "safeObject(layer.actual)" in MONITOR
    assert "safeObject(layer.confidence_difference)" in MONITOR
    assert "safeObject(layer.priority_difference)" in MONITOR
    assert "Layer data is missing or could not be loaded." in MONITOR


def test_public_report_failure_does_not_poison_full_diagnostic_action():
    assert "reportError" in MONITOR
    assert "Public report could not be generated" in MONITOR
    assert "setReportError(adminErrorMessage" in MONITOR
    assert "setError(\"\"); setReportError(\"\");" in MONITOR
    assert "normalizeReport" in MONITOR
    assert "payload?.report || payload?.public_report || payload" in MONITOR


def test_rapid_clicks_and_hanging_diagnostics_recover_safely():
    assert "DIAGNOSTIC_TIMEOUT_MS" in MONITOR
    assert "Promise.race" in MONITOR
    assert "if (running || generatingReport) return;" in MONITOR
    assert "const actionDisabled = running || generatingReport;" in MONITOR
    assert "disabled={actionDisabled}" in MONITOR
    assert "mountedRef.current" in MONITOR


def test_intelligence_health_api_exports_are_still_stabilization_only():
    assert 'post("/admin/intelligence-health/run", {})' in API
    assert 'get("/admin/intelligence-health/history")' in API
    assert 'post("/admin/intelligence-health/public-report", {})' in API
    assert "V2" not in MONITOR
