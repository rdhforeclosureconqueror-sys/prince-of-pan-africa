import importlib
import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import event


class InstitutionIntelligencePhase4Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(self.temp_dir.name) / 'institution_intel.db'}"
        os.environ["ALLOW_INSECURE_DEV_SESSION_SECRET"] = "true"
        os.environ["APP_ENV"] = "test"
        os.environ["SOCIETY_BUILDER_ENABLED"] = "true"
        import app.config as config_module, app.database as database_module, app.models as models_module, app.authz as authz_module
        import app.services.member_intelligence as member_intel_module, app.services.society_intelligence as society_intel_module, app.services.institution_intelligence as institution_intel_module
        importlib.reload(config_module); importlib.reload(database_module); importlib.reload(models_module); importlib.reload(authz_module); importlib.reload(member_intel_module); importlib.reload(society_intel_module); importlib.reload(institution_intel_module)
        database_module.init_db()
        self.dbm, self.models, self.authz, self.intel = database_module, models_module, authz_module, institution_intel_module
        db = self.dbm.SessionLocal()
        try:
            self.authz.seed_rbac_defaults(db)
            self.admin = self.models.User(email="admin@example.com", password_hash="x", role="admin")
            self.member = self.models.User(email="member@example.com", password_hash="x", role="community_member")
            db.add_all([self.admin, self.member]); db.flush()
            self.institution = self.models.Society(slug="phase4", name="Phase 4 Cooperative", founder_user_id=self.admin.id, type="Cooperative")
            db.add(self.institution); db.flush()
            db.add_all([
                self.models.SocietyMembership(society_id=self.institution.id, user_id=self.admin.id, role="Founder/Admin", status="active"),
                self.models.SocietyMembership(society_id=self.institution.id, user_id=self.member.id, role="Member", status="active"),
                self.models.SocietyFirstTenMember(society_id=self.institution.id, user_id=self.admin.id, name="Admin", role="Facilitator", reliability_score=4, confidentiality_score=4, relationship_capacity_score=4, skill_capacity_score=3, financial_steadiness_score=3),
                self.models.SocietyBlueprintAudit(society_id=self.institution.id, trust_score=2, relationships_score=3, mutual_aid_score=2, organization_score=2, institutions_score=2, businesses_score=1, property_score=1, community_wealth_score=2, political_power_score=1),
            ])
            db.commit(); self.institution_id, self.admin_id, self.member_id = self.institution.id, self.admin.id, self.member.id
        finally:
            db.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def generate(self):
        db = self.dbm.SessionLocal()
        try:
            return self.intel.generate_institution_intelligence(db, institution_id=self.institution_id, include_debug=True)
        finally:
            db.close()

    def test_institution_health_changes_when_society_and_member_intelligence_changes(self):
        before = self.generate()
        db = self.dbm.SessionLocal()
        try:
            growth = {"categories": {"Leadership Archetype Engine": {"assessments": {"core": {"assessment_name": "Leadership Core", "strengths": ["Planning"]}}}}}
            db.add(self.models.MemberProfile(user_id=self.member_id, role="member", attributes={"growth_profile": growth}))
            db.add(self.models.LeadershipAssessment(user_id=self.member_id, scores='{"strengths":["Planning"]}'))
            audit = db.query(self.models.SocietyBlueprintAudit).filter_by(society_id=self.institution_id).first(); audit.trust_score = 5; audit.institutions_score = 5; audit.businesses_score = 4
            db.commit()
        finally:
            db.close()
        after = self.generate()
        self.assertGreater(after["scores"]["assessment_coverage"]["score"], before["scores"]["assessment_coverage"]["score"])
        self.assertNotEqual(after["institution_health"]["score"], before["institution_health"]["score"])
        self.assertIn("because", after["institution_health"]["why"])

    def test_leadership_participation_trust_assessment_container_recommendations_and_confidence_update(self):
        before = self.generate()
        db = self.dbm.SessionLocal()
        try:
            container = self.models.SocietyContainer(society_id=self.institution_id, title="First 100 Days", status="active", percent_complete=80)
            db.add(container); db.flush()
            member_row = self.models.SocietyFirstTenMember(society_id=self.institution_id, user_id=self.member_id, name="Member", role="Treasurer", reliability_score=5, confidentiality_score=5, relationship_capacity_score=5, skill_capacity_score=5, financial_steadiness_score=5)
            db.add(member_row); db.flush()
            opening = self.models.SocietyRoleOpening(society_id=self.institution_id, title="Treasurer", status="appointed")
            db.add(opening); db.flush()
            db.add(self.models.SocietyRoleAppointmentHistory(society_id=self.institution_id, role_opening_id=opening.id, candidate_member_id=member_row.id, role_title="Treasurer"))
            db.add(self.models.SocietyInstitutionalProfile(society_id=self.institution_id, user_id=self.member_id, display_name="Member", availability="weekly", primary_contribution="operations"))
            db.add(self.models.SocietyPurpose(society_id=self.institution_id, purpose_statement="Build together"))
            db.add(self.models.SocietyCovenant(society_id=self.institution_id, covenant_text="Care and accountability"))
            db.commit()
        finally:
            db.close()
        after = self.generate()
        for key in ["leadership_health", "participation_health", "trust_health", "assessment_coverage", "container_completion"]:
            self.assertGreaterEqual(after["scores"][key]["score"], before["scores"][key]["score"])
            self.assertTrue(after["scores"][key]["calculation"])
        self.assertNotEqual(after["recommended_next_actions"], before["recommended_next_actions"])
        self.assertGreaterEqual(len(after["evidence"]), len(before["evidence"]))

    def test_missing_evidence_lowers_confidence_and_read_only_no_writes_no_workflows(self):
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
        self.assertTrue(data["missing_evidence"])
        self.assertIn("does not write records", data["warnings"][0])
        self.assertIn("Adaptive Kanban", data["warnings"][0])
        db = self.dbm.SessionLocal()
        try:
            self.assertEqual(db.query(self.models.SocietyTrustTask).count(), 0)
        finally:
            db.close()

    def test_route_admin_debug_only(self):
        import app.main as main_module
        importlib.reload(main_module)
        client = TestClient(main_module.app)
        from app.session import build_session_cookie_value
        admin = client.get(f"/society-builder/institutions/{self.institution_id}/intelligence?debug=true", cookies={"mufasa_session": build_session_cookie_value(self.admin_id)})
        self.assertEqual(admin.status_code, 200, admin.text)
        self.assertIsNotNone(admin.json()["debug"])
        member = client.get(f"/society-builder/institutions/{self.institution_id}/intelligence?debug=true", cookies={"mufasa_session": build_session_cookie_value(self.member_id)})
        self.assertEqual(member.status_code, 200, member.text)
        self.assertIsNone(member.json()["debug"])


if __name__ == "__main__":
    unittest.main()
