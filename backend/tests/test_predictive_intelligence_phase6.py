import importlib, os, tempfile, unittest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import event

class PredictiveIntelligencePhase6Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(self.temp_dir.name) / 'predictive.db'}"
        os.environ["ALLOW_INSECURE_DEV_SESSION_SECRET"] = "true"; os.environ["APP_ENV"] = "test"; os.environ["SOCIETY_BUILDER_ENABLED"] = "true"
        import app.config as config_module, app.database as database_module, app.models as models_module, app.authz as authz_module
        import app.services.predictive_intelligence as predictive_module
        for m in [config_module, database_module, models_module, authz_module, predictive_module]: importlib.reload(m)
        database_module.init_db(); self.dbm, self.models, self.authz, self.pred = database_module, models_module, authz_module, predictive_module
        db = self.dbm.SessionLocal()
        try:
            self.authz.seed_rbac_defaults(db)
            self.admin = self.models.User(email="admin@example.com", password_hash="x", role="admin")
            self.member = self.models.User(email="member@example.com", password_hash="x", role="community_member")
            db.add_all([self.admin, self.member]); db.flush()
            self.society = self.models.Society(slug="phase6", name="Phase 6 Society", founder_user_id=self.admin.id, type="Mutual Aid Society")
            db.add(self.society); db.flush()
            db.add_all([
                self.models.SocietyMembership(society_id=self.society.id, user_id=self.admin.id, role="Facilitator", status="active"),
                self.models.SocietyMembership(society_id=self.society.id, user_id=self.member.id, role="Member", status="active"),
                self.models.SocietyFirstTenMember(society_id=self.society.id, user_id=self.admin.id, name="Admin", role="Facilitator", reliability_score=5, confidentiality_score=5, relationship_capacity_score=5, skill_capacity_score=5, financial_steadiness_score=4),
                self.models.SocietyBlueprintAudit(society_id=self.society.id, trust_score=2, relationships_score=3, mutual_aid_score=3, organization_score=3, institutions_score=2, businesses_score=4, property_score=1, community_wealth_score=2, political_power_score=1),
                self.models.SocietyContainer(society_id=self.society.id, title="First 100 Days", status="active", percent_complete=35),
                self.models.SocietyTrustTask(society_id=self.society.id, title="Read chapter", status="backlog", linked_handbook_chapter="Chapter 1", created_from_template=False),
                self.models.SocietyInstitutionalProfile(society_id=self.society.id, user_id=self.member.id, display_name="Builder", availability="weekly", primary_contribution="business operations", contribution_type="Organizer", current_projects_json=["co-op"]),
            ])
            db.commit(); self.society_id, self.admin_id, self.member_id = self.society.id, self.admin.id, self.member.id
        finally: db.close()
    def tearDown(self): self.temp_dir.cleanup()
    def generate(self):
        db = self.dbm.SessionLocal()
        try: return self.pred.generate_predictive_intelligence(db, society_id=self.society_id, include_debug=True)
        finally: db.close()
    def test_forecasts_include_trend_probability_confidence_risk_opportunity_leadership_institution_business_trust(self):
        data = self.generate(); types = {p["prediction_type"] for p in data["predictions"]}
        for typ in ["member_growth", "leadership_readiness", "assessment_completion_likelihood", "participation_trend", "trust_trend", "knowledge_growth", "business_readiness", "burnout_risk", "container_failure_risk", "institution_stability", "opportunity_urgency"]: self.assertIn(typ, types)
        for p in data["predictions"]:
            self.assertIsInstance(p["probability"], int); self.assertIn(p["confidence"], {"limited", "developing", "substantial"}); self.assertIn(p["trend"], {"Improving", "Stable", "Declining", "Rapid Growth", "Rapid Decline", "Unknown"}); self.assertTrue(p["explanation"]); self.assertTrue(p["assumptions"]); self.assertTrue(p["requires_manual_review"]); self.assertTrue(p["no_workflow_executed"])
        self.assertTrue(data["dashboard"]["emerging_risks"]); self.assertTrue(data["dashboard"]["business_forecast"]); self.assertTrue(data["dashboard"]["trust_forecast"])
    def test_read_only_no_persistence_no_workflows_and_admin_debug_api(self):
        writes=[]
        def guard(conn, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")): writes.append(statement)
        event.listen(self.dbm.engine, "before_cursor_execute", guard)
        try: data = self.generate()
        finally: event.remove(self.dbm.engine, "before_cursor_execute", guard)
        self.assertEqual(writes, []); self.assertIn("does not write records", data["warnings"][0])
        import app.main as main_module; importlib.reload(main_module)
        from app.session import build_session_cookie_value
        client = TestClient(main_module.app)
        admin = client.get(f"/society-builder/predictive/intelligence?society_id={self.society_id}&debug=true", cookies={"mufasa_session": build_session_cookie_value(self.admin_id)})
        self.assertEqual(admin.status_code, 200, admin.text); self.assertIsNotNone(admin.json()["debug"])
        member = client.get(f"/society-builder/predictive/intelligence?society_id={self.society_id}", cookies={"mufasa_session": build_session_cookie_value(self.member_id)})
        self.assertEqual(member.status_code, 403)
    def test_dashboard_static_rendering_contract(self):
        src = Path("src/pages/PredictiveIntelligencePage.jsx").read_text(); api = Path("src/api/societyBuilder.js").read_text(); app = Path("src/App.jsx").read_text()
        for text in ["Overall Forecast", "High Confidence Predictions", "Improving Trends", "Declining Trends", "Emerging Risks", "Future Opportunities", "Leadership Forecast", "Institution Forecast", "Business Forecast", "Trust Forecast", "Container Forecast", "Probability", "Confidence", "Evidence", "Missing Evidence", "Time Horizon", "Prediction Explanation"]: self.assertIn(text, src)
        self.assertIn("getPredictiveIntelligence", api); self.assertIn("/societies/:societyId/predictive", app)

if __name__ == "__main__": unittest.main()
