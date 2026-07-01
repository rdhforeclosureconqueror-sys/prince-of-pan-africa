import importlib, os, tempfile, unittest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import event

class DecisionSupportPhase7Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(self.temp_dir.name) / 'decision.db'}"
        os.environ["ALLOW_INSECURE_DEV_SESSION_SECRET"] = "true"; os.environ["APP_ENV"] = "test"; os.environ["SOCIETY_BUILDER_ENABLED"] = "true"
        import app.config as config_module, app.database as database_module, app.models as models_module, app.authz as authz_module
        import app.services.member_intelligence as member_intel_module, app.services.society_intelligence as society_intel_module, app.services.institution_intelligence as institution_intel_module, app.services.opportunity_intelligence as opp_module, app.services.decision_support as decision_module
        for m in [config_module, database_module, models_module, authz_module, member_intel_module, society_intel_module, institution_intel_module, opp_module, decision_module]: importlib.reload(m)
        database_module.init_db(); self.dbm, self.models, self.authz, self.decision = database_module, models_module, authz_module, decision_module
        db = self.dbm.SessionLocal()
        try:
            self.authz.seed_rbac_defaults(db)
            self.admin = self.models.User(email="admin@example.com", password_hash="x", role="admin")
            self.member = self.models.User(email="member@example.com", password_hash="x", role="community_member")
            self.helper = self.models.User(email="helper@example.com", password_hash="x", role="community_member")
            db.add_all([self.admin, self.member, self.helper]); db.flush()
            self.society = self.models.Society(slug="phase7", name="Phase 7 Society", founder_user_id=self.admin.id, type="Mutual Aid Society")
            db.add(self.society); db.flush()
            db.add_all([
                self.models.SocietyMembership(society_id=self.society.id, user_id=self.admin.id, role="Facilitator", status="active"),
                self.models.SocietyMembership(society_id=self.society.id, user_id=self.member.id, role="Member", status="active"),
                self.models.SocietyMembership(society_id=self.society.id, user_id=self.helper.id, role="Member", status="active"),
                self.models.SocietyFirstTenMember(society_id=self.society.id, user_id=self.admin.id, name="Admin", role="Facilitator", reliability_score=5, confidentiality_score=5, relationship_capacity_score=5, skill_capacity_score=5, financial_steadiness_score=4),
                self.models.SocietyBlueprintAudit(society_id=self.society.id, trust_score=2, relationships_score=3, mutual_aid_score=3, organization_score=3, institutions_score=2, businesses_score=4, property_score=1, community_wealth_score=2, political_power_score=1),
                self.models.SocietyInstitutionalProfile(society_id=self.society.id, user_id=self.member.id, display_name="Builder", availability="weekly", primary_contribution="business operations", current_projects_json=["co-op"], skills_to_learn_json=["finance"]),
            ])
            db.commit(); self.society_id, self.admin_id, self.member_id = self.society.id, self.admin.id, self.member.id
        finally: db.close()
    def tearDown(self): self.temp_dir.cleanup()
    def generate(self):
        db = self.dbm.SessionLocal()
        try: return self.decision.generate_decision_support(db, society_id=self.society_id, include_debug=True)
        finally: db.close()
    def test_recommendations_are_ranked_explainable_and_cover_phase7_fields(self):
        data = self.generate(); recs = data["recommendations"]
        self.assertTrue(recs)
        scores = [r["scores"]["overall_priority"]["score"] for r in recs]
        self.assertEqual(scores, sorted(scores, reverse=True))
        required = {"id", "title", "decision_type", "priority", "impact_score", "effort_score", "urgency", "confidence", "evidence", "missing_evidence", "assumptions", "reasoning", "expected_outcomes", "tradeoffs", "dependencies", "related_entities", "requires_manual_review", "no_workflow_executed"}
        for r in recs:
            self.assertTrue(required.issubset(r.keys()))
            for key in ["impact", "urgency", "confidence", "effort", "risk_reduction", "community_benefit", "institution_benefit", "long_term_value", "overall_priority"]:
                self.assertIn("why", r["scores"][key])
            self.assertTrue(r["requires_manual_review"]); self.assertTrue(r["no_workflow_executed"])
            self.assertIn("human", r["human_final_decision"].lower())
    def test_dashboard_buckets_and_missing_evidence_confidence_behavior(self):
        data = self.generate(); d = data["dashboard"]
        for section in ["executive_summary", "top_10_priorities", "quick_wins", "high_impact_low_effort", "high_impact_high_effort", "critical_risks", "leadership_decisions", "institution_decisions", "container_decisions", "business_decisions", "resource_allocation", "strategic_roadmap"]:
            self.assertIn(section, d)
        self.assertTrue(any(r["missing_evidence"] for r in data["recommendations"]))
        self.assertTrue(all(r["confidence"] in {"limited", "developing", "substantial"} for r in data["recommendations"]))
    def test_read_only_no_persistence_workflows_tasks_assignments_or_notifications(self):
        writes=[]
        def guard(conn, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")): writes.append(statement)
        event.listen(self.dbm.engine, "before_cursor_execute", guard)
        try: data = self.generate()
        finally: event.remove(self.dbm.engine, "before_cursor_execute", guard)
        self.assertEqual(writes, [])
        self.assertIn("no workflows are executed", data["warnings"][0])
        self.assertIn("no tasks are created", data["warnings"][0])
        self.assertIn("no members are assigned", data["warnings"][0])
        self.assertIn("no notifications are sent", data["warnings"][0])
        db = self.dbm.SessionLocal()
        try: self.assertEqual(db.query(self.models.SocietyTrustTask).count(), 0)
        finally: db.close()
    def test_api_admin_debug_permissions_and_dashboard_static_rendering(self):
        import app.main as main_module; importlib.reload(main_module)
        from app.session import build_session_cookie_value
        client = TestClient(main_module.app)
        admin = client.get(f"/society-builder/decision-support?society_id={self.society_id}&debug=true", cookies={"mufasa_session": build_session_cookie_value(self.admin_id)})
        self.assertEqual(admin.status_code, 200, admin.text); self.assertIsNotNone(admin.json()["debug"])
        member = client.get(f"/society-builder/decision-support?society_id={self.society_id}&debug=true", cookies={"mufasa_session": build_session_cookie_value(self.member_id)})
        self.assertEqual(member.status_code, 403)
        src = Path("src/pages/DecisionSupportPage.jsx").read_text(); api = Path("src/api/societyBuilder.js").read_text(); app = Path("src/App.jsx").read_text(); home = Path("src/pages/SocietyHomePage.jsx").read_text()
        for text in ["Executive Summary", "Top 10 Priorities", "Quick Wins", "High Impact / Low Effort", "High Impact / High Effort", "Critical Risks", "Leadership Decisions", "Institution Decisions", "Container Decisions", "Business Decisions", "Resource Allocation", "Strategic Roadmap", "Manual Review Required", "No Workflow Executed"]: self.assertIn(text, src)
        self.assertIn("getDecisionSupport", api); self.assertIn("/societies/:societyId/decision-support", app); self.assertIn("Open Decision Support", home)

if __name__ == "__main__": unittest.main()
