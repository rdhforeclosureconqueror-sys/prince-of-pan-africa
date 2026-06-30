import importlib, os, tempfile, unittest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import event

class OpportunityIntelligencePhase5Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(self.temp_dir.name) / 'opportunity.db'}"
        os.environ["ALLOW_INSECURE_DEV_SESSION_SECRET"] = "true"; os.environ["APP_ENV"] = "test"; os.environ["SOCIETY_BUILDER_ENABLED"] = "true"
        import app.config as config_module, app.database as database_module, app.models as models_module, app.authz as authz_module
        import app.services.member_intelligence as member_intel_module, app.services.society_intelligence as society_intel_module, app.services.institution_intelligence as institution_intel_module, app.services.opportunity_intelligence as opp_module
        for m in [config_module, database_module, models_module, authz_module, member_intel_module, society_intel_module, institution_intel_module, opp_module]: importlib.reload(m)
        database_module.init_db(); self.dbm, self.models, self.authz, self.opp = database_module, models_module, authz_module, opp_module
        db = self.dbm.SessionLocal()
        try:
            self.authz.seed_rbac_defaults(db)
            self.admin = self.models.User(email="admin@example.com", password_hash="x", role="admin")
            self.member = self.models.User(email="member@example.com", password_hash="x", role="community_member")
            self.new = self.models.User(email="new@example.com", password_hash="x", role="community_member")
            db.add_all([self.admin, self.member, self.new]); db.flush()
            self.society = self.models.Society(slug="phase5", name="Phase 5 Society", founder_user_id=self.admin.id, type="Mutual Aid Society")
            db.add(self.society); db.flush()
            db.add_all([
                self.models.SocietyMembership(society_id=self.society.id, user_id=self.admin.id, role="Facilitator", status="active"),
                self.models.SocietyMembership(society_id=self.society.id, user_id=self.member.id, role="Member", status="active"),
                self.models.SocietyMembership(society_id=self.society.id, user_id=self.new.id, role="Member", status="active"),
                self.models.SocietyFirstTenMember(society_id=self.society.id, user_id=self.admin.id, name="Admin", role="Facilitator", reliability_score=5, confidentiality_score=5, relationship_capacity_score=5, skill_capacity_score=5, financial_steadiness_score=4),
                self.models.SocietyBlueprintAudit(society_id=self.society.id, trust_score=2, relationships_score=3, mutual_aid_score=3, organization_score=3, institutions_score=2, businesses_score=4, property_score=1, community_wealth_score=2, political_power_score=1),
            ])
            db.commit(); self.society_id, self.admin_id, self.member_id = self.society.id, self.admin.id, self.member.id
        finally: db.close()
    def tearDown(self): self.temp_dir.cleanup()
    def generate(self):
        db = self.dbm.SessionLocal()
        try: return self.opp.generate_opportunity_intelligence(db, society_id=self.society_id, include_debug=True)
        finally: db.close()
    def test_detects_leadership_missing_role_assessment_trust_and_missing_evidence(self):
        data = self.generate(); types = {o["type"] for o in data["opportunities"]}
        for typ in ["leadership", "role", "assessment", "trust", "education"]: self.assertIn(typ, types)
        self.assertTrue(any("Treasurer" in o["related_roles"] for o in data["opportunities"] if o["type"] == "role"))
        self.assertTrue(data["missing_evidence"]); self.assertIn(data["confidence"], {"limited", "developing", "substantial"})
        self.assertTrue(all(o["no_workflow_executed"] and o["requires_manual_review"] for o in data["opportunities"]))
    def test_priority_recalculates_volunteer_mentorship_business_institution_recommendations_after_evidence_changes(self):
        before = self.generate()["overall_priority"]["score"]
        db = self.dbm.SessionLocal()
        try:
            container = self.models.SocietyContainer(society_id=self.society_id, title="First 100 Days", status="active", percent_complete=95); db.add(container); db.flush()
            db.add(self.models.SocietyTrustTask(society_id=self.society_id, container_id=container.id, title="Open task", status="backlog", created_from_template=False))
            db.add_all([
                self.models.SocietyInstitutionalProfile(society_id=self.society_id, user_id=self.member_id, display_name="Experienced", availability="weekly", primary_contribution="business operations", contribution_type="Organizer", current_projects_json=["co-op"]),
                self.models.SocietyInstitutionalProfile(society_id=self.society_id, user_id=self.new.id, display_name="New", availability="monthly", skills_to_learn_json=["finance"]),
                self.models.LeadershipAssessment(user_id=self.member_id, submission_id="s1", responses="{}", scores='{"strengths":["Planning"]}'),
                self.models.MemberProfile(user_id=self.member_id, role="member", attributes={"growth_profile": {"categories": {"Leadership Archetype Engine": {"assessments": {"core": {"assessment_name": "Leadership Core"}}}}}}),
                self.models.SocietyPurpose(society_id=self.society_id, purpose_statement="Build institutions"), self.models.SocietyCovenant(society_id=self.society_id, covenant_text="Trust"),
            ])
            audit = db.query(self.models.SocietyBlueprintAudit).filter_by(society_id=self.society_id).first(); audit.trust_score = 5; audit.institutions_score = 5
            db.commit()
        finally: db.close()
        data = self.generate(); types = {o["type"] for o in data["opportunities"]}
        for typ in ["volunteer", "mentorship", "business", "institution", "recognition"]: self.assertIn(typ, types)
        self.assertNotEqual(before, data["overall_priority"]["score"])
    def test_read_only_no_writes_no_workflows_and_api_admin_debug_permissions(self):
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
        admin = client.get(f"/society-builder/opportunities/intelligence?society_id={self.society_id}&debug=true", cookies={"mufasa_session": build_session_cookie_value(self.admin_id)})
        self.assertEqual(admin.status_code, 200, admin.text); self.assertIsNotNone(admin.json()["debug"])
        member = client.get(f"/society-builder/opportunities/intelligence?society_id={self.society_id}&debug=true", cookies={"mufasa_session": build_session_cookie_value(self.member_id)})
        self.assertEqual(member.status_code, 403)
    def test_dashboard_static_rendering_contract(self):
        src = Path("src/pages/OpportunityIntelligencePage.jsx").read_text(); api = Path("src/api/societyBuilder.js").read_text(); app = Path("src/App.jsx").read_text(); home = Path("src/pages/SocietyHomePage.jsx").read_text()
        for text in ["Top Opportunities", "High Priority", "Medium Priority", "Low Priority", "Leadership Opportunities", "Volunteer Opportunities", "Business Opportunities", "Institution Opportunities", "Education Opportunities", "Trust Opportunities", "Recognition Opportunities", "Recently Changed", "Confidence", "Evidence Count", "Missing Evidence", "Recommendations", "Warnings", "Health Summary"]: self.assertIn(text, src)
        self.assertIn("getOpportunityIntelligence", api); self.assertIn("/societies/:societyId/opportunities", app); self.assertIn("Open Opportunity Intelligence", home)

if __name__ == "__main__": unittest.main()
