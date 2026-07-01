from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return (ROOT / path).read_text()


def test_new_read_only_services_exist_and_guard_boundaries():
    for path, layer in [
        ("backend/app/services/execution_intelligence.py", "Execution Intelligence"),
        ("backend/app/services/institutional_memory.py", "Institutional Memory"),
        ("backend/app/services/institutional_learning.py", "Institutional Learning"),
    ]:
        src = read(path)
        assert layer in src
        assert "read_only" in src
        assert "No" in src or "never" in src
        assert ".commit(" not in src
        assert ".add(" not in src
        assert ".delete(" not in src


def test_routes_and_frontend_api_are_registered():
    routes = read("backend/app/routes/society_builder.py")
    api = read("src/api/societyBuilder.js")
    app = read("src/App.jsx")
    home = read("src/pages/SocietyHomePage.jsx")
    for route in ["/execution-intelligence", "/institutional-memory", "/institutional-learning"]:
        assert route in routes
    for fn in ["getExecutionIntelligence", "getInstitutionalMemory", "getInstitutionalLearning"]:
        assert fn in api
    for route in ["execution-intelligence", "institutional-memory", "institutional-learning"]:
        assert route in app
        assert route in home


def test_health_monitor_registers_complete_v1_loop():
    service = read("backend/app/services/intelligence_health.py")
    component = read("src/components/IntelligenceHealthMonitor.jsx")
    expected = ["Execution Intelligence", "Institutional Memory", "Institutional Learning"]
    for layer in expected:
        assert layer in service
        assert layer in component
    assert "generate_execution_intelligence" in service
    assert "generate_institutional_memory" in service
    assert "generate_institutional_learning" in service


def test_version1_completion_doc_freezes_v2():
    doc = read("docs/version1_institutional_intelligence_complete.md")
    assert "Version 1 is feature complete" in doc
    assert "Future capabilities belong exclusively to Version 2" in doc
    assert "Society Simulator" in doc
    assert "Do Not Implement" in doc
