import importlib
import os
import tempfile
import unittest
from pathlib import Path


class MemberIntelligencePhase1Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "member_intelligence.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["ALLOW_INSECURE_DEV_SESSION_SECRET"] = "true"
        os.environ["APP_ENV"] = "test"
        os.environ["SOCIETY_BUILDER_ENABLED"] = "true"

        import app.config as config_module
        import app.database as database_module
        import app.models as models_module
        import app.authz as authz_module
        import app.services.member_intelligence as intelligence_module

        importlib.reload(config_module)
        importlib.reload(database_module)
        importlib.reload(models_module)
        importlib.reload(authz_module)
        importlib.reload(intelligence_module)
        database_module.init_db()
        self.dbm = database_module
        self.models = models_module
        self.intelligence = intelligence_module
        db = self.dbm.SessionLocal()
        try:
            self.member = self.models.User(email="member@example.com", password_hash="x", role="community_member")
            self.leader = self.models.User(email="leader@example.com", password_hash="x", role="community_member")
            db.add_all([self.member, self.leader]); db.flush()
            self.society = self.models.Society(slug="harlem-care", name="Harlem Care Circle", type="Neighborhood", founder_user_id=self.leader.id)
            db.add(self.society); db.flush()
            db.add(self.models.SocietyMembership(society_id=self.society.id, user_id=self.member.id, role="Member", status="active"))
            db.commit()
            self.member_id = self.member.id
            self.society_id = self.society.id
        finally:
            db.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _generate(self):
        db = self.dbm.SessionLocal()
        try:
            return self.intelligence.generate_member_intelligence(db, society_id=self.society_id, member_id=self.member_id)
        finally:
            db.close()

    def test_member_intelligence_generates_without_assessment_data_and_surfaces_missing_assessments(self):
        profile = self._generate()
        self.assertEqual(profile["member_id"], self.member_id)
        self.assertEqual(profile["society_id"], self.society_id)
        self.assertEqual(profile["completed_assessments"], [])
        self.assertTrue(profile["missing_assessments"])
        self.assertEqual(profile["confidence_level"], "limited")
        self.assertIn("Read-only generated intelligence", profile["software_boundary"])
        db = self.dbm.SessionLocal()
        try:
            self.assertEqual(db.query(self.models.SocietyRoleAppointmentHistory).count(), 0)
        finally:
            db.close()

    def test_member_intelligence_generates_with_partial_assessment_data_and_confidence_changes(self):
        db = self.dbm.SessionLocal()
        try:
            growth_profile = {
                "categories": {
                    "Leadership Archetype Engine": {
                        "status": "completed",
                        "assessments": {
                            "leadership-core": {
                                "assessment_id": "leadership-core",
                                "assessment_name": "Leadership Core",
                                "strengths": ["Listening"],
                                "opportunities_for_growth": ["Delegation"],
                                "primary_result": "Bridge Builder",
                            }
                        },
                    }
                }
            }
            db.add(self.models.MemberProfile(user_id=self.member_id, role="member", attributes={"growth_profile": growth_profile}))
            db.add(self.models.SocietyFirstTenMember(society_id=self.society_id, user_id=self.member_id, name="Amina", role="Facilitator", status="Considering", reliability_score=5, confidentiality_score=4, skill_capacity_score=3, financial_steadiness_score=2, relationship_capacity_score=5, possible_contribution="Comfortable facilitating meetings"))
            db.commit()
        finally:
            db.close()
        profile = self._generate()
        self.assertIn("Leadership Core", profile["completed_assessments"])
        self.assertIn("Listening", profile["behavioral_strengths"])
        self.assertIn("Delegation", profile["development_areas"])
        self.assertIn("Bridge Builder", profile["archetypes"])
        self.assertEqual(profile["confidence_level"], "developing")

    def test_includes_first_ten_role_consideration_and_role_assignment_history(self):
        db = self.dbm.SessionLocal()
        try:
            candidate = self.models.SocietyFirstTenMember(society_id=self.society_id, user_id=self.member_id, name="Amina", role="Treasurer", status="Considering", reliability_score=5, confidentiality_score=5, skill_capacity_score=4, financial_steadiness_score=5, relationship_capacity_score=4, notes="Trusted with records.")
            db.add(candidate); db.flush()
            opening = self.models.SocietyRoleOpening(society_id=self.society_id, title="Treasurer", recommended_assessments=["Leadership style assessment"])
            db.add(opening); db.flush()
            db.add(self.models.SocietyRoleCandidateReview(society_id=self.society_id, role_opening_id=opening.id, candidate_member_id=candidate.id, alignment_label="Good Alignment", behavioral_confidence="Developing community evidence", behavioral_evidence=["Trusted with records."], missing_assessments=["Leadership style assessment"]))
            db.add(self.models.SocietyRoleAppointmentHistory(society_id=self.society_id, role_opening_id=opening.id, candidate_member_id=candidate.id, role_title="Treasurer", reason="Community approval after discussion.", training_status="Scheduled"))
            db.commit()
        finally:
            db.close()
        profile = self._generate()
        self.assertIn({"role": "Treasurer", "status": "Considering", "evidence": "Trusted with records."}, profile["considered_roles"])
        self.assertTrue(any(item["role"] == "Treasurer" for item in profile["role_alignment_summaries"]))
        self.assertEqual(profile["past_roles"][0]["role"], "Treasurer")
        self.assertTrue(any(src["system"] == "role assignment history" for src in profile["evidence_sources"]))
        db = self.dbm.SessionLocal()
        try:
            self.assertEqual(db.query(self.models.SocietyRoleAppointmentHistory).count(), 1)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
