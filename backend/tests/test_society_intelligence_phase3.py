import importlib
import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import event


class SocietyIntelligencePhase3Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(self.temp_dir.name) / 'society_intel.db'}"
        os.environ["ALLOW_INSECURE_DEV_SESSION_SECRET"] = "true"
        os.environ["APP_ENV"] = "test"
        os.environ["SOCIETY_BUILDER_ENABLED"] = "true"
        import app.config as config_module
        import app.database as database_module
        import app.models as models_module
        import app.authz as authz_module
        import app.services.member_intelligence as member_intel_module
        import app.services.society_intelligence as society_intel_module
        importlib.reload(config_module); importlib.reload(database_module); importlib.reload(models_module); importlib.reload(authz_module); importlib.reload(member_intel_module); importlib.reload(society_intel_module)
        database_module.init_db()
        self.dbm, self.models, self.authz, self.intel = database_module, models_module, authz_module, society_intel_module
        db = self.dbm.SessionLocal()
        try:
            self.authz.seed_rbac_defaults(db)
            self.admin = self.models.User(email="admin@example.com", password_hash="x", role="admin")
            self.member = self.models.User(email="member@example.com", password_hash="x", role="community_member")
            db.add_all([self.admin, self.member]); db.flush()
            self.society = self.models.Society(slug="phase3", name="Phase 3 Society", founder_user_id=self.admin.id, type="Neighborhood")
            db.add(self.society); db.flush()
            db.add_all([
                self.models.SocietyMembership(society_id=self.society.id, user_id=self.admin.id, role="Founder/Admin", status="active"),
                self.models.SocietyMembership(society_id=self.society.id, user_id=self.member.id, role="Member", status="active"),
                self.models.SocietyFirstTenMember(society_id=self.society.id, user_id=self.admin.id, name="Admin", role="Facilitator", reliability_score=5, confidentiality_score=5, relationship_capacity_score=5, skill_capacity_score=4, financial_steadiness_score=4),
                self.models.SocietyBlueprintAudit(society_id=self.society.id, trust_score=3, relationships_score=3, mutual_aid_score=3, organization_score=3, institutions_score=2, businesses_score=1, property_score=1, community_wealth_score=2, political_power_score=1),
            ])
            db.commit(); self.society_id, self.admin_id, self.member_id = self.society.id, self.admin.id, self.member.id
        finally:
            db.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def generate(self):
        db = self.dbm.SessionLocal()
        try:
            return self.intel.generate_society_intelligence(db, society_id=self.society_id, include_debug=True)
        finally:
            db.close()

    def test_scores_change_when_member_data_changes_and_assessment_completion_updates(self):
        before = self.generate()
        db = self.dbm.SessionLocal()
        try:
            growth = {"categories": {"Leadership Archetype Engine": {"assessments": {"core": {"assessment_name": "Leadership Core", "strengths": ["Listening"]}}}}}
            db.add(self.models.MemberProfile(user_id=self.member_id, role="member", attributes={"growth_profile": growth}))
            db.add(self.models.LeadershipAssessment(user_id=self.member_id, scores='{"strengths":["Planning"]}'))
            db.commit()
        finally:
            db.close()
        after = self.generate()
        self.assertGreater(after["scores"]["assessment_completion"]["score"], before["scores"]["assessment_completion"]["score"])
        self.assertNotEqual(after["scores"]["society_health_score"]["score"], before["scores"]["society_health_score"]["score"])
        self.assertIn("calculation", after["scores"]["assessment_completion"])

    def test_leadership_trust_role_coverage_update(self):
        before = self.generate()
        db = self.dbm.SessionLocal()
        try:
            db.add_all([
                self.models.SocietyFirstTenMember(society_id=self.society_id, user_id=self.member_id, name="Member", role="Treasurer", reliability_score=5, confidentiality_score=5, relationship_capacity_score=5, skill_capacity_score=5, financial_steadiness_score=5),
                self.models.SocietyRoleOpening(society_id=self.society_id, title="Treasurer", status="open"),
            ])
            audit = db.query(self.models.SocietyBlueprintAudit).filter_by(society_id=self.society_id).first(); audit.trust_score = 5
            db.commit()
        finally:
            db.close()
        after = self.generate()
        self.assertGreater(after["scores"]["leadership_coverage"]["score"], before["scores"]["leadership_coverage"]["score"])
        self.assertGreater(after["scores"]["trust_score"]["score"], before["scores"]["trust_score"]["score"])
        self.assertGreater(after["scores"]["role_coverage"]["score"], before["scores"]["role_coverage"]["score"])

    def test_missing_evidence_lowers_confidence_and_read_only_no_workflows(self):
        writes = []
        def guard(conn, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                writes.append(statement)
        event.listen(self.dbm.engine, "before_cursor_execute", guard)
        try:
            data = self.generate()
        finally:
            event.remove(self.dbm.engine, "before_cursor_execute", guard)
        self.assertEqual(writes, [])
        self.assertIn(data["confidence"], {"limited", "developing"})
        self.assertTrue(data["missing_information"])
        self.assertIn("does not write records", data["warnings"][0])
        db = self.dbm.SessionLocal()
        try:
            self.assertEqual(db.query(self.models.SocietyRoleAppointmentHistory).count(), 0)
            self.assertEqual(db.query(self.models.SocietyTrustTask).count(), 0)
        finally:
            db.close()

    def test_route_admin_debug_only(self):
        import app.main as main_module
        importlib.reload(main_module)
        client = TestClient(main_module.app)
        from app.session import build_session_cookie_value
        admin_cookie = {"mufasa_session": build_session_cookie_value(self.admin_id)}
        member_cookie = {"mufasa_session": build_session_cookie_value(self.member_id)}
        admin = client.get(f"/society-builder/societies/{self.society_id}/intelligence?debug=true", cookies=admin_cookie)
        self.assertEqual(admin.status_code, 200, admin.text)
        self.assertIsNotNone(admin.json()["debug"])
        member = client.get(f"/society-builder/societies/{self.society_id}/intelligence?debug=true", cookies=member_cookie)
        self.assertEqual(member.status_code, 200, member.text)
        self.assertIsNone(member.json()["debug"])


if __name__ == "__main__":
    unittest.main()
