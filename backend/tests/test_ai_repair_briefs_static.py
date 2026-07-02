from pathlib import Path

MONITOR = (Path(__file__).resolve().parents[2] / "src/components/IntelligenceHealthMonitor.jsx").read_text()


def test_technical_view_contains_full_ai_repair_briefs_section():
    assert "AI Repair Briefs" in MONITOR
    assert "likely_backend_file" in MONITOR
    assert "verification_command" in MONITOR
    assert "safe_baseline_update" in MONITOR


def test_executive_view_summarizes_only_top_three_repair_briefs():
    assert "Top 3 AI Repair Briefs" in MONITOR
    assert "executiveRepairBriefs = asArray(result?.executive_repair_brief_summary).slice(0, 3)" in MONITOR
