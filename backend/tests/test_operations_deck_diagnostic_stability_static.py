from pathlib import Path

MONITOR = Path("src/components/IntelligenceHealthMonitor.jsx").read_text()
OPS_DASHBOARD = Path("src/pages/AdminOperationsDashboard.jsx").read_text()
API = Path("src/api/societyBuilder.js").read_text()
PUBLIC_PAGE = Path("src/pages/PublicIntelligenceDiagnosticReportPage.jsx").read_text()
APP = Path("src/App.jsx").read_text()
PACKAGE = Path("package.json").read_text()


def test_operations_deck_mounts_health_monitor_inside_error_boundary_without_blocking_initial_load():
    assert "class IntelligenceHealthMonitorErrorBoundary" in OPS_DASHBOARD
    assert "getDerivedStateFromError" in OPS_DASHBOARD
    assert "Intelligence Health Monitor failed to render. Other admin tools are still available." in OPS_DASHBOARD
    assert "<IntelligenceHealthMonitorErrorBoundary>" in OPS_DASHBOARD
    assert "<IntelligenceHealthMonitor />" in OPS_DASHBOARD
    assert 'api("/discord/diagnostics").catch(() => null)' in OPS_DASHBOARD
    assert 'api("/member/assessments/sync-diagnostics").catch(() => null)' in OPS_DASHBOARD


def test_project_has_no_frontend_test_runner_so_static_unit_path_is_used():
    assert '"test"' not in PACKAGE
    assert "vitest" not in PACKAGE
    assert "jest" not in PACKAGE


def test_operations_deck_renders_with_null_diagnostic_data_and_missing_layers():
    assert "const result = safeObject(diagnosticRunState || history[0]);" in MONITOR
    assert "const layers = asArray(result?.layers).filter" in MONITOR
    assert "Layer data is missing or could not be loaded." in MONITOR
    assert "Diagnostics unavailable" in MONITOR
    assert "setHistory([])" in MONITOR


def test_health_endpoint_failures_render_fallback_cards_instead_of_throwing():
    assert "loadHistory().catch" not in MONITOR
    assert "Last run could not be loaded" in MONITOR
    assert "Diagnostics unavailable" in MONITOR
    assert "adminErrorMessage" in MONITOR


def test_empty_null_history_and_missing_layer_data_are_guarded():
    assert "normalizeHistory" in MONITOR
    assert "asArray(payload?.history)" in MONITOR
    assert "safeObject(layer.expected)" in MONITOR
    assert "safeObject(layer.actual)" in MONITOR
    assert "safeObject(layer.confidence_difference)" in MONITOR
    assert "safeObject(layer.priority_difference)" in MONITOR


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


def test_public_report_response_contract_is_normalized_before_rendering():
    assert "normalizePublicReportResponse" in MONITOR
    assert "publicReportState" in MONITOR
    assert "publicReportError" in MONITOR
    assert "publicReportUrl" in MONITOR
    assert "PUBLIC_REPORT_MISSING_URL_MESSAGE" in MONITOR
    assert "Public report was generated but no valid public URL was returned." in MONITOR
    assert "new URL(publicUrl.trim(), origin).href" in MONITOR
    assert "publicReportPathFromToken(token)" in MONITOR


def test_public_report_url_must_be_safe_before_rendering():
    assert "isSafePublicReportHref" in MONITOR
    assert 'url.protocol === "http:" || url.protocol === "https:"' in MONITOR
    assert "const safePublicReportUrl = isSafePublicReportHref(publicReportUrl) ? publicReportUrl : \"\";" in MONITOR
    assert "{safePublicReportUrl &&" in MONITOR
    assert "href={safePublicReportUrl}" in MONITOR
    assert "href={publicReportUrl}" not in MONITOR


def test_public_report_link_is_plain_safe_anchor_and_clearable():
    assert 'target="_blank"' in MONITOR
    assert 'rel="noopener noreferrer"' in MONITOR
    assert "Open public diagnostic report" in MONITOR
    assert "Clear Public Report Link" in MONITOR
    assert "clearPublicReport" in MONITOR
    assert "window.location.assign" not in MONITOR
    assert "useNavigate" not in MONITOR


def test_public_report_url_renders_as_selectable_read_only_text_with_copy_button():
    assert 'id="public-diagnostic-report-url"' in MONITOR
    assert 'aria-label="Public diagnostic report URL"' in MONITOR
    assert "readOnly value={safePublicReportUrl}" in MONITOR
    assert "event.target.select()" in MONITOR
    assert ">Copy URL</button>" in MONITOR


def test_public_report_copy_uses_clipboard_and_surfaces_success_or_manual_fallback():
    assert "const copyPublicReportUrl = async () =>" in MONITOR
    assert "navigator.clipboard.writeText(safePublicReportUrl)" in MONITOR
    assert "Copied public diagnostic URL." in MONITOR
    assert "Copy failed. Select the URL manually." in MONITOR
    assert 'role="status"' in MONITOR


def test_public_report_copy_and_open_do_not_rerun_or_mutate_diagnostic_state():
    copy_body = MONITOR.split("const copyPublicReportUrl = async () =>", 1)[1].split("const result =", 1)[0]
    assert "runIntelligenceHealthDiagnostic" not in copy_body
    assert "generatePublicIntelligenceDiagnosticReport" not in copy_body
    assert "setDiagnosticRunState" not in copy_body
    assert "setHistory" not in copy_body
    assert "loadHistory" not in copy_body
    anchor_fragment = MONITOR.split("Open public diagnostic report", 1)[0].rsplit("<a ", 1)[1]
    assert "onClick" not in anchor_fragment
    assert "href={safePublicReportUrl}" in anchor_fragment


def test_operations_deck_handles_missing_malformed_or_empty_public_urls_without_crashing():
    assert "PUBLIC_REPORT_MISSING_URL_MESSAGE" in MONITOR
    assert "return { publicReportState, publicReportUrl: \"\", error: PUBLIC_REPORT_MISSING_URL_MESSAGE }" in MONITOR
    assert "const safePublicReportUrl = isSafePublicReportHref(publicReportUrl) ? publicReportUrl : \"\";" in MONITOR
    assert "{(publicReportState || safePublicReportUrl) &&" in MONITOR
    assert "{safePublicReportUrl &&" in MONITOR


def test_public_route_registered_without_admin_wrapper():
    assert '<Route path="/public/intelligence-diagnostics/:token" element={<PublicIntelligenceDiagnosticReportPage />} />' in APP
    route_fragment = APP.split('<Route path="/public/intelligence-diagnostics/:token"')[1].split('/>')[0]
    assert 'AdminMutualAidOperationsDashboardRoute' not in route_fragment
    assert 'DashboardRoute' not in route_fragment
    assert 'authChecked' not in route_fragment
    assert 'isAdmin' not in route_fragment


def test_public_page_handles_invalid_expired_missing_and_malformed_reports_safely():
    assert "PUBLIC_REPORT_TIMEOUT_MS" in PUBLIC_PAGE
    assert "withTimeout(Promise.all" in PUBLIC_PAGE
    assert "getPublicIntelligenceDiagnosticReport(token).catch" in PUBLIC_PAGE
    assert "fetchMarkdown(reportUrls.markdown).catch" in PUBLIC_PAGE
    assert "missing a token" in PUBLIC_PAGE
    assert "Report expired" in PUBLIC_PAGE
    assert "Invalid token" in PUBLIC_PAGE
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
    generate_report_body = MONITOR.split("const generateReport = async () =>", 1)[1].split("const result =", 1)[0]
    assert "setDiagnosticRunState" not in generate_report_body
    run_body = MONITOR.split("const run = async () =>", 1)[1].split("const generateReport = async () =>", 1)[0]
    assert "setPublicReportState" not in run_body
    assert "setPublicReportUrl" not in run_body


def test_clear_public_report_link_resets_only_public_report_state():
    clear_body = MONITOR.split("const clearPublicReport = () =>", 1)[1].split("const loadHistory", 1)[0]
    assert "setPublicReportState(null)" in clear_body
    assert "setPublicReportUrl(\"\")" in clear_body
    assert "setPublicReportError(\"\")" in clear_body
    assert "setDiagnosticRunState" not in clear_body
    assert "setHistory" not in clear_body


def test_admin_public_debug_output_is_debug_gated():
    assert "DEBUG_ERRORS &&" in MONITOR
    assert "Public Report Debug Output" in MONITOR
    assert "JSON.stringify({ publicReportState, publicReportError }" in MONITOR
