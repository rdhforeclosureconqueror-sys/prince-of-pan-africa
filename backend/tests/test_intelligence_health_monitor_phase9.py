import unittest
from pathlib import Path

SERVICE = Path("backend/app/services/intelligence_health.py").read_text()
ADMIN_ROUTES = Path("backend/app/routes/admin.py").read_text()
OPS_DASHBOARD = Path("src/pages/AdminOperationsDashboard.jsx").read_text()
MONITOR = Path("src/components/IntelligenceHealthMonitor.jsx").read_text()
API = Path("src/api/societyBuilder.js").read_text()


class IntelligenceHealthMonitorPhase9StaticTests(unittest.TestCase):
    def test_admin_only_routes_and_operations_desk_button_exist(self):
        self.assertIn('@legacy_router.post("/intelligence-health/run")', ADMIN_ROUTES)
        self.assertIn('require_permission("admin:read_dashboard")', ADMIN_ROUTES)
        self.assertIn("IntelligenceHealthMonitor", OPS_DASHBOARD)
        self.assertIn("Run Full Intelligence Diagnostic", MONITOR)
        self.assertIn("runIntelligenceHealthDiagnostic", API)

    def test_deterministic_isolated_fixture_and_no_production_writes(self):
        self.assertIn('sqlite:///:memory:', SERVICE)
        self.assertIn("_seed_fixture", SERVICE)
        self.assertIn("Intelligence Health Fixture Society", SERVICE)
        self.assertIn('"isolated_fixture": True', SERVICE)
        self.assertIn('"production_writes": 0', SERVICE)
        self.assertIn('"workflow_execution": False', SERVICE)
        self.assertIn('"notification_count": 0', SERVICE)
        self.assertIn('"assignment_count": 0', SERVICE)
        self.assertIn('"persistence_of_intelligence_outputs": False', SERVICE)

    def test_layer_execution_order_baseline_and_future_framework(self):
        expected = ["Member Intelligence", "Society Intelligence", "Institution Intelligence", "Opportunity Intelligence", "Predictive Intelligence", "Decision Support", "Execution Planning"]
        for layer in expected:
            self.assertIn(layer, SERVICE)
        self.assertIn("DIAGNOSTIC_LAYER_ORDER", SERVICE)
        self.assertIn("EXPECTED_BASELINE", SERVICE)
        self.assertIn("outputs[\"Opportunity Intelligence\"]", SERVICE)

    def test_regression_detection_root_cause_performance_and_history(self):
        for token in ["Minor", "Moderate", "Critical", "difference_summary", "confidence_difference", "missing_evidence_difference", "priority_difference", "root_cause_analysis", "diagnostic_history", "compare_diagnostics", "slowest_layer", "fastest_layer", "largest_payload_layer"]:
            self.assertIn(token, SERVICE)

    def test_frontend_sections_cover_health_dashboard_requirements(self):
        for text in ["Overall Health", "Layer Status", "Regression Summary", "Critical Failures", "Performance Metrics", "Root Cause Analysis", "Diagnostic History", "Compare Previous Run", "Health Trend", "Debug Output"]:
            self.assertIn(text, MONITOR)
        for icon in ["🟢 Healthy", "🟡 Warning", "🟠 Regression", "🔴 Failure"]:
            self.assertIn(icon, MONITOR)


if __name__ == "__main__":
    unittest.main()
