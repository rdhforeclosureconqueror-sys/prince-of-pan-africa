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
    assert "publicReportError" in MONITOR
    assert "Public report could not be generated" in MONITOR
    assert "setPublicReportError(adminErrorMessage" in MONITOR
    assert "setError(\"\"); setPublicReportError(\"\");" in MONITOR
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

PUBLIC_PAGE = Path("src/pages/PublicIntelligenceDiagnosticReportPage.jsx").read_text()
APP = Path("src/App.jsx").read_text()


def test_public_report_response_contract_is_normalized_before_rendering():
    assert "normalizePublicReportResponse" in MONITOR
    assert "publicReportState" in MONITOR
    assert "publicReportError" in MONITOR
    assert "publicReportUrl" in MONITOR
    assert "PUBLIC_REPORT_MISSING_URL_MESSAGE" in MONITOR
    assert "Public report was generated but no valid public URL was returned." in MONITOR
    assert "new URL(publicUrl.trim(), origin).href" in MONITOR
    assert "publicReportPathFromToken(token)" in MONITOR


def test_public_report_link_is_plain_safe_anchor_and_clearable():
    assert 'href={publicReportUrl}' in MONITOR
    assert 'target="_blank"' in MONITOR
    assert 'rel="noopener noreferrer"' in MONITOR
    assert "Open public diagnostic report" in MONITOR
    assert "Clear Public Report Link" in MONITOR
    assert "clearPublicReport" in MONITOR
    assert "window.location.assign" not in MONITOR
    assert "useNavigate" not in MONITOR


def test_public_route_registered_without_admin_wrapper():
    assert '<Route path="/public/intelligence-diagnostics/:token" element={<PublicIntelligenceDiagnosticReportPage />} />' in APP
    assert 'AdminMutualAidOperationsDashboardRoute' not in APP.split('<Route path="/public/intelligence-diagnostics/:token"')[1].split('/>')[0]


def test_public_page_handles_invalid_expired_missing_and_malformed_reports_safely():
    assert "PUBLIC_REPORT_TIMEOUT_MS" in PUBLIC_PAGE
    assert "withTimeout(getPublicIntelligenceDiagnosticReport(token))" in PUBLIC_PAGE
    assert "missing a token" in PUBLIC_PAGE
    assert "has expired" in PUBLIC_PAGE
    assert "invalid or no longer available" in PUBLIC_PAGE
    assert "malformed or empty" in PUBLIC_PAGE
    assert "Layer data unavailable" in PUBLIC_PAGE
    assert "safeObject(layer.expected)" in PUBLIC_PAGE
    assert "safeObject(layer.actual)" in PUBLIC_PAGE
    assert "PublicReportError" in PUBLIC_PAGE


def test_public_generation_keeps_full_diagnostic_state_separate():
    assert "diagnosticRunState" in MONITOR
    assert "setDiagnosticRunState" in MONITOR
    assert "setPublicReportState" in MONITOR
    assert "setPublicReportUrl" in MONITOR
    assert "setDiagnosticRunState" not in MONITOR.split("const generateReport = async () =>", 1)[1].split("const result =", 1)[0]


def test_admin_public_debug_output_is_debug_gated():
    assert "DEBUG_ERRORS &&" in MONITOR
    assert "Public Report Debug Output" in MONITOR
    assert "JSON.stringify({ publicReportState, publicReportError }" in MONITOR
