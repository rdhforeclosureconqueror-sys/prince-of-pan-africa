import importlib
import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


class SocietyRoleAssignmentWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "role_assignment.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["ALLOW_INSECURE_DEV_SESSION_SECRET"] = "true"
        os.environ["APP_ENV"] = "test"
        os.environ["SOCIETY_BUILDER_ENABLED"] = "true"

        import app.config as config_module
        import app.database as database_module
        import app.models as models_module
        import app.authz as authz_module
        import app.services.society_builder as service_module

        importlib.reload(config_module)
        importlib.reload(database_module)
        importlib.reload(models_module)
        importlib.reload(authz_module)
        importlib.reload(service_module)
        database_module.init_db()
        self.dbm = database_module
        self.models = models_module
        self.authz = authz_module
        db = self.dbm.SessionLocal()
        try:
            self.authz.seed_rbac_defaults(db)
            self.user = self.models.User(email="leader@example.com", password_hash="x", role="community_member")
            self.viewer = self.models.User(email="viewer@example.com", password_hash="x", role="community_member")
            db.add_all([self.user, self.viewer])
            db.commit()
            db.refresh(self.user); db.refresh(self.viewer)
            self.user_id, self.viewer_id = self.user.id, self.viewer.id
        finally:
            db.close()

        import app.main as main_module
        importlib.reload(main_module)
        self.client = TestClient(main_module.app)
        from app.session import build_session_cookie_value
        self.leader_cookie = {"mufasa_session": build_session_cookie_value(self.user_id)}
        self.viewer_cookie = {"mufasa_session": build_session_cookie_value(self.viewer_id)}

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_society(self):
        res = self.client.post("/society-builder/societies", json={"name": "Harlem Care Circle", "type": "Neighborhood", "first_focus": "Care"}, cookies=self.leader_cookie)
        self.assertEqual(res.status_code, 200, res.text)
        return res.json()["society"]

    def test_role_assignment_review_decision_development_and_history(self):
        society = self.create_society()
        strong = self.client.post(f"/society-builder/societies/{society['id']}/first-ten", json={"name": "Amina", "role": "Member", "reliability_score": 5, "confidentiality_score": 5, "skill_capacity_score": 4, "financial_steadiness_score": 4, "relationship_capacity_score": 5, "possible_contribution": "Comfortable facilitating meetings", "notes": "Has served faithfully."}, cookies=self.leader_cookie).json()["member"]
        emerging = self.client.post(f"/society-builder/societies/{society['id']}/first-ten", json={"name": "Kwame", "role": "Member", "reliability_score": 2, "confidentiality_score": 3, "skill_capacity_score": 2, "financial_steadiness_score": 2, "relationship_capacity_score": 3}, cookies=self.leader_cookie).json()["member"]

        role_res = self.client.post(f"/society-builder/societies/{society['id']}/role-assignment/open-roles", json={"title": "Facilitator", "purpose": "Keep meetings focused and participatory.", "responsibilities": ["Prepare agendas", "Guide discussion"], "required_behaviors": ["Excellent listener", "Comfortable facilitating meetings"], "handbook_chapters": ["Appendix N: Roles"], "recommended_assessments": ["Leadership style assessment"]}, cookies=self.leader_cookie)
        self.assertEqual(role_res.status_code, 200, role_res.text)
        role = role_res.json()["role"]

        suggested = self.client.post(f"/society-builder/societies/{society['id']}/role-assignment/open-roles/{role['id']}/suggest-candidates", cookies=self.leader_cookie)
        self.assertEqual(suggested.status_code, 200, suggested.text)
        groups = suggested.json()["suggested_candidates"]
        self.assertEqual(groups["Strong Alignment"][0]["candidate_member"]["id"], strong["id"])
        self.assertTrue(groups["Emerging Alignment"])
        self.assertNotIn("Best", str(suggested.json()))
        strong_review = groups["Strong Alignment"][0]["review"]
        emerging_review = groups["Emerging Alignment"][0]["review"]

        view = self.client.get(f"/society-builder/societies/{society['id']}/role-assignment/open-roles/{role['id']}/reviews/{strong_review['id']}", cookies=self.leader_cookie).json()
        self.assertIn("Behavioral", str(view["review"]["behavioral_evidence"]))
        self.assertIn("Leadership style assessment", view["review"]["missing_assessments"])
        self.assertIn("Appendix N: Roles", view["review"]["handbook_references"])

        note = self.client.post(f"/society-builder/societies/{society['id']}/role-assignment/open-roles/{role['id']}/discussion-notes", json={"candidate_review_id": strong_review["id"], "note": "Shows initiative and is an excellent listener."}, cookies=self.leader_cookie)
        self.assertEqual(note.status_code, 200, note.text)

        development = self.client.post(f"/society-builder/societies/{society['id']}/role-assignment/open-roles/{role['id']}/reviews/{emerging_review['id']}/decision", json={"decision": "needs_development", "reason": "Needs additional mentoring."}, cookies=self.leader_cookie).json()
        self.assertIn("suggested_assessments", development["review"]["development_plan"])
        self.assertNotIn("Reject", str(development))
        self.assertNotIn("Denied", str(development))

        appointed = self.client.post(f"/society-builder/societies/{society['id']}/role-assignment/open-roles/{role['id']}/reviews/{strong_review['id']}/decision", json={"decision": "appoint", "reason": "Community approval after discussion.", "mentor": "Elder Mentor", "training_status": "Scheduled"}, cookies=self.leader_cookie)
        self.assertEqual(appointed.status_code, 200, appointed.text)
        self.assertIn("did not appoint anyone automatically", appointed.json()["software_boundary"])
        self.assertEqual(appointed.json()["appointment"]["role_title"], "Facilitator")

        history = self.client.get(f"/society-builder/societies/{society['id']}/role-assignment/appointment-history", cookies=self.leader_cookie).json()["history"]
        self.assertEqual(history[0]["reason"], "Community approval after discussion.")
        self.assertIn("Shows initiative", str(history[0]["community_notes"]))

        dashboard = self.client.get(f"/society-builder/societies/{society['id']}/role-assignment/dashboard", cookies=self.leader_cookie).json()
        self.assertTrue(dashboard["recently_appointed"])
        self.assertTrue(dashboard["needs_development"])
        self.assertIn("open_roles", dashboard)
        self.assertNotIn("leaderboard", str(dashboard).lower())

    def test_non_member_cannot_view_society_workflow(self):
        society = self.create_society()
        res = self.client.get(f"/society-builder/societies/{society['id']}/role-assignment/dashboard", cookies=self.viewer_cookie)
        self.assertEqual(res.status_code, 403)


if __name__ == "__main__":
    unittest.main()
