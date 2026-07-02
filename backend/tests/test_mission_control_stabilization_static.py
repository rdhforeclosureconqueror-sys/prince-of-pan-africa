from pathlib import Path

MONITOR = Path("src/components/IntelligenceHealthMonitor.jsx").read_text()


def test_pass_layer_language_does_not_use_warning_copy():
    assert 'layer?.status === "PASS" && !layer?.regression' in MONITOR
    assert "Leadership can rely on this PASS layer when making decisions." in MONITOR


def test_executive_trends_deduplicates_public_verification_cards():
    assert "public_verification_score" in MONITOR
    assert "public_verification_latency_ms" in MONITOR
    assert "Public verification result" in MONITOR
    assert "Public verification latency" in MONITOR


def test_discord_warning_and_stabilization_checklist_are_visible():
    for text in ["Stabilization Checklist", "Unresolved intelligence warnings", "Resolved warnings", "Remaining true regressions", "Warnings requiring rerun", "Warnings requiring code fix", "Warnings requiring config fix", "Discord Configuration Warnings", "grant the Simba bot View Channel and Send Messages"]:
        assert text in MONITOR
