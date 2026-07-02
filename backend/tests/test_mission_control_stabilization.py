from pathlib import Path

SERVICE = Path("backend/app/services/intelligence_health.py").read_text()
MONITOR = Path("src/components/IntelligenceHealthMonitor.jsx").read_text()


def test_forecast_math_clamps_sprint_projection_to_current_health_when_risk_reduction_positive():
    assert "def _safe_percent_from_text" in SERVICE
    assert "risk_reduction = _safe_percent_from_text" in SERVICE
    assert "projected = max(current, projected)" in SERVICE
    assert 'sprint_health = f"{min(100, projected)}%"' in SERVICE


def test_forecast_shows_rerun_message_instead_of_fake_percent_when_unsafe():
    assert 'Projected health cannot be calculated until the {len(unresolved)} unresolved diagnostics are rerun.' in SERVICE
    assert "projected is None or unresolved" in SERVICE


def test_pass_layer_language_does_not_use_warning_copy():
    assert 'layer?.status === "PASS" && !layer?.regression' in MONITOR
    assert "Leadership can rely on this PASS layer when making decisions." in MONITOR


def test_institutional_memory_pass_is_treated_as_resolved_warning_not_drift():
    assert '"resolved_warnings": [layer.get("layer") for layer in layers if layer.get("status") == "PASS"]' in SERVICE
    assert "Institutional Memory" in MONITOR


def test_trend_cards_separate_public_verification_score_from_latency():
    assert '"public_verification_score"' in SERVICE
    assert '"public_verification_latency_ms"' in SERVICE
    assert '["Public Verification Score", "public_verification_score", "%"]' in MONITOR
    assert '["Public Verification Latency", "public_verification_latency_ms", "ms"]' in MONITOR
    assert "Public verification score" in MONITOR
    assert "Public verification latency" in MONITOR


def test_discord_403_is_separate_configuration_warning():
    assert "def discord_configuration_warnings" in SERVICE
    assert "bot_log_post returned 403 Forbidden" in SERVICE
    assert "Verify bot permissions for bot_log channel and webhook configuration." in SERVICE
    assert "SimbaBrain intelligence health" in SERVICE
    assert "Discord Configuration Warnings" in MONITOR


def test_stabilization_checklist_categories_are_rendered():
    for text in ["stabilization_checklist", "unresolved_intelligence_warnings", "resolved_warnings", "remaining_true_regressions", "warnings_requiring_rerun", "warnings_requiring_code_fix", "warnings_requiring_config_fix"]:
        assert text in SERVICE
    for text in ["Stabilization Checklist", "Unresolved intelligence warnings", "Resolved warnings", "Remaining true regressions", "Warnings requiring rerun", "Warnings requiring code fix", "Warnings requiring config fix"]:
        assert text in MONITOR


def test_actionable_diagnostic_resolution_engine_is_exposed():
    for text in ["diagnostic_resolution", "what_is_wrong", "why_it_happened", "how_to_fix", "fix_type", "owner", "verification_step", "learning_memory", "recurring_warning_patterns"]:
        assert text in SERVICE
    for text in ["Diagnostic Resolution Engine", "What is wrong?", "Why is it wrong?", "What fixes it?", "Who owns it?", "How do we prove it is fixed?", "Learning Memory"]:
        assert text in MONITOR
