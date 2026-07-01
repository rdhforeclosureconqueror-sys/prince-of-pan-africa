import importlib, os, tempfile, unittest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import event

class ExecutionPlanningPhase8Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(self.temp_dir.name) / 'execution.db'}"
        os.environ["ALLOW_INSECURE_DEV_SESSION_SECRET"] = "true"; os.environ["APP_ENV"] = "test"; os.environ["SOCIETY_BUILDER_ENABLED"] = "true"
        import app.config as config_module, app.database as database_module, app.models as models_module, app.authz as authz_module
        import app.services.member_intelligence as member_intel_module, app.services.society_intelligence as society_intel_module, app.services.institution_intelligence as institution_intel_module, app.services.opportunity_intelligence as opp_module, app.services.decision_support as decision_module, app.services.execution_planning as execution_module
        for m in [config_module, database_module, models_module, authz_module, member_intel_module, society_intel_module, institution_intel_module, opp_module, decision_module, execution_module]: importlib.reload(m)
        database_module.init_db(); self.dbm, self.models, self.authz, self.execution = database_module, models_module, authz_module, execution_module
        db = self.dbm.SessionLocal()
        try:
            self.authz.seed_rbac_defaults(db)
            self.admin = self.models.User(email="admin@example.com", password_hash="x", role="admin")
            self.member = self.models.User(email="member@example.com", password_hash="x", role="community_member")
            db.add_all([self.admin, self.member]); db.flush()
            self.society = self.models.Society(slug="phase8", name="Phase 8 Society", founder_user_id=self.admin.id, type="Mutual Aid Society")
            db.add(self.society); db.flush()
            db.add_all([
                self.models.SocietyMembership(society_id=self.society.id, user_id=self.admin.id, role="Facilitator", status="active"),
                self.models.SocietyMembership(society_id=self.society.id, user_id=self.member.id, role="Member", status="active"),
                self.models.SocietyFirstTenMember(society_id=self.society.id, user_id=self.admin.id, name="Admin", role="Facilitator", reliability_score=5, confidentiality_score=5, relationship_capacity_score=5, skill_capacity_score=5, financial_steadiness_score=4),
                self.models.SocietyBlueprintAudit(society_id=self.society.id, trust_score=2, relationships_score=3, mutual_aid_score=3, organization_score=3, institutions_score=2, businesses_score=4, property_score=1, community_wealth_score=2, political_power_score=1),
                self.models.SocietyInstitutionalProfile(society_id=self.society.id, user_id=self.member.id, display_name="Builder", availability="weekly", primary_contribution="business operations", current_projects_json=["co-op"], skills_to_learn_json=["finance"]),
            ])
            db.commit(); self.society_id, self.admin_id, self.member_id = self.society.id, self.admin.id, self.member.id
        finally: db.close()
    def tearDown(self): self.temp_dir.cleanup()
    def generate(self):
        db = self.dbm.SessionLocal()
        try: return self.execution.generate_execution_plans(db, society_id=self.society_id, include_debug=True)
        finally: db.close()
    def test_execution_plans_include_required_phase8_fields_and_categories(self):
        data = self.generate(); plans = data["execution_plans"]
        self.assertTrue(plans)
        required = {"objective", "why_this_matters", "expected_impact", "priority", "confidence", "estimated_effort", "time_estimate", "required_roles", "required_skills", "required_members", "required_institutions", "required_containers", "dependencies", "risks", "mitigation_suggestions", "recommended_sequence_of_steps", "milestones", "success_metrics", "required_resources", "estimated_cost", "estimated_community_benefit", "estimated_institutional_benefit", "evidence_supporting_recommendation", "missing_evidence", "assumptions", "manual_review_requirements", "readiness_score"}
        for p in plans:
            self.assertTrue(required.issubset(p.keys()))
            self.assertIn(p["category"], data["plan_categories"])
            self.assertTrue(p["requires_manual_review"]); self.assertTrue(p["no_execution_performed"])
        for category in ["Quick Wins", "High Impact Projects", "Society Growth", "Leadership Development", "Institution Building", "Business Development", "Education", "Community Trust", "Volunteer Expansion", "Infrastructure", "Technology", "Resource Allocation", "Risk Reduction"]:
            self.assertIn(category, data["grouped_plans"])
    def test_dashboard_sections_and_readiness_score(self):
        d = self.generate()["dashboard"]
        for section in ["executive_summary", "recommended_plans", "quick_wins", "long_term_initiatives", "timeline_view", "dependencies", "required_people", "required_resources", "expected_outcomes", "risks", "success_metrics", "readiness_score"]:
            self.assertIn(section, d)
        self.assertGreaterEqual(d["readiness_score"], 0); self.assertLessEqual(d["readiness_score"], 100)
    def test_read_only_no_database_writes(self):
        writes=[]
        def guard(conn, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")): writes.append(statement)
        event.listen(self.dbm.engine, "before_cursor_execute", guard)
        try: data = self.generate()
        finally: event.remove(self.dbm.engine, "before_cursor_execute", guard)
        self.assertEqual(writes, [])
        self.assertIn("No workflows", data["warnings"][0])
        self.assertIn("database writes", data["warnings"][0])
    def test_api_admin_only_debug_and_frontend_static_rendering(self):
        import app.main as main_module; importlib.reload(main_module)
        from app.session import build_session_cookie_value
        client = TestClient(main_module.app)
        admin = client.get(f"/society-builder/execution-plans?society_id={self.society_id}&debug=true", cookies={"mufasa_session": build_session_cookie_value(self.admin_id)})
        self.assertEqual(admin.status_code, 200, admin.text); self.assertIsNotNone(admin.json()["debug"])
        member = client.get(f"/society-builder/execution-plans?society_id={self.society_id}&debug=true", cookies={"mufasa_session": build_session_cookie_value(self.member_id)})
        self.assertEqual(member.status_code, 403)
        src = Path("src/pages/ExecutionPlanningPage.jsx").read_text(); api = Path("src/api/societyBuilder.js").read_text(); app = Path("src/App.jsx").read_text(); home = Path("src/pages/SocietyHomePage.jsx").read_text()
        for text in ["Executive Summary", "Recommended Plans", "Quick Wins", "Long-Term Initiatives", "Timeline View", "Dependencies", "Required People", "Required Resources", "Expected Outcomes", "Risks", "Success Metrics", "Readiness Score", "These are recommendations only", "No workflows, assignments, notifications, tasks, calendar events, Kanban cards, or database writes are performed"]: self.assertIn(text, src)
        self.assertIn("getExecutionPlans", api); self.assertIn("/societies/:societyId/execution-plans", app); self.assertIn("Open Execution Plans", home)

if __name__ == "__main__": unittest.main()
