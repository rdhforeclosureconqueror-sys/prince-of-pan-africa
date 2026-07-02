from app.services.intelligence_health import (
    build_repair_briefs,
    public_report_to_markdown,
    run_full_intelligence_diagnostic,
    sanitize_diagnostic_for_public_report,
)


def test_repair_briefs_are_generated_for_every_warning_or_regression():
    run = run_full_intelligence_diagnostic()
    problem_layers = [layer for layer in run["layers"] if layer["status"] != "PASS" or layer.get("regression")]
    briefs = run["repair_briefs"]

    assert len(briefs) >= len(problem_layers)
    assert {brief["layer_name"] for brief in briefs} >= {layer["layer"] for layer in problem_layers}


def test_repair_briefs_include_actionable_repo_fields_and_default_baseline_safety():
    run = run_full_intelligence_diagnostic()
    brief = run["repair_briefs"][0]

    assert brief["likely_backend_file"].startswith("backend/app/services/")
    assert brief["likely_function_service"]
    assert brief["fix_type"] in {"code_change", "config_change", "data_issue", "baseline_update", "rerun_required", "permission_issue", "frontend_display"}
    assert brief["verification_command"]
    assert brief["recommended_fix_steps"]
    assert brief["field_that_drifted"]
    if brief["safe_baseline_update"] == "no":
        assert "Do not update baseline." in brief["do_not_change_notes"]


def test_discord_permission_warnings_are_separate_from_intelligence_health():
    briefs = build_repair_briefs([], [{"warning": "bot_log_post returned 403 Forbidden", "recommended_fix": "Verify bot permissions."}])

    assert briefs[0]["layer_name"] == "Discord Permissions"
    assert briefs[0]["failure_type"] == "discord_permission"
    assert briefs[0]["fix_type"] == "permission_issue"
    assert "not intelligence drift" in briefs[0]["do_not_change_notes"]


def test_public_json_contains_repair_briefs_and_markdown_ai_hints():
    run = run_full_intelligence_diagnostic()
    public = sanitize_diagnostic_for_public_report(run)
    markdown = public_report_to_markdown(public)

    assert public["repair_briefs"]
    assert public["layers"][0].get("repair_brief") is not None
    assert "## AI Repair Briefs" in markdown
    assert "AI_REPAIR_HINT" in markdown
    assert "Likely Function" in markdown


def test_executive_summary_is_limited_to_top_three_repair_briefs():
    run = run_full_intelligence_diagnostic()

    assert "executive_repair_brief_summary" in run
    assert len(run["executive_repair_brief_summary"]) <= 3
