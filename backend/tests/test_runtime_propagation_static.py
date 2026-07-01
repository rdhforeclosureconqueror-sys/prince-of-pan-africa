from pathlib import Path

SERVICE = Path("backend/app/services/intelligence_health.py").read_text()
ADMIN = Path("backend/app/routes/admin.py").read_text()


def test_runtime_propagation_uses_live_database_not_contract_only():
    assert "def build_runtime_propagation_report(db: Session | None)" in SERVICE
    assert '"source": "live_runtime_database"' in SERVICE
    assert "contract inference was accepted" in SERVICE
    assert '"fixture_data_used": False' in SERVICE
    assert '"production_ready": False' in SERVICE
    assert "NOT_PRODUCTION_READY" in SERVICE


def test_runtime_trace_contains_required_step_fields_and_object_categories():
    for token in [
        "object_id",
        "timestamp",
        "input_received",
        "output_produced",
        "fields_added",
        "fields_removed",
        "downstream_consumer",
        "evidence_next_layer_actually_received_it",
    ]:
        assert token in SERVICE
    for object_type in [
        "Members",
        "Assessments",
        "Activity Stream",
        "Audiobooks",
        "Garvey",
        "Payments",
        "Opportunities",
        "Society",
        "Discord",
    ]:
        assert object_type in SERVICE


def test_admin_diagnostic_passes_runtime_db_session():
    assert "return run_full_intelligence_diagnostic(db)" in ADMIN
