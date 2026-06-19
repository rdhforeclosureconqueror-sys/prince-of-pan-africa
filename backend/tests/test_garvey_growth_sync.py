import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


class GarveyGrowthSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(cls.temp_dir.name) / "test_garvey_growth.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["ENVIRONMENT"] = "test"
        os.environ["SESSION_SECRET"] = "test-session-secret"
        os.environ["GARVEY_CALLBACK_SECRET"] = "callback-secret"
        os.environ["GARVEY_ALLOWED_ISSUER"] = "simba_wajuma"

        from app.database import Base, SessionLocal, engine
        from app.main import app

        Base.metadata.create_all(bind=engine)
        cls.SessionLocal = SessionLocal
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def setUp(self):
        from app.authz import seed_rbac_defaults
        from app.models import ActivityLog, GarveySyncEvent, MemberProfile, Permission, Role, RolePermission, User, UserRole

        db = self.SessionLocal()
        try:
            for model in [GarveySyncEvent, ActivityLog, MemberProfile, UserRole, RolePermission, Role, Permission, User]:
                db.query(model).delete()
            db.commit()
            member = User(email="growth-member@example.com", password_hash="x", role="member")
            db.add(member)
            db.commit()
            db.refresh(member)
            seed_rbac_defaults(db)
            self.member_id = member.id
        finally:
            db.close()

    def test_completion_callback_updates_growth_profile_and_results(self):
        response = self.client.post(
            "/api/simbawajuma/assessment-callback",
            headers={"X-Garvey-Callback-Secret": "callback-secret"},
            json={
                "event": "assessment.completed",
                "issuer": "simba_wajuma",
                "member_id": str(self.member_id),
                "assessment_id": "leadership-core",
                "assessment_type": "leadership",
                "assessment_name": "Leadership Core",
                "result_id": "garvey-result-1",
                "completion_status": "completed",
                "overall_score": 82,
                "percentile": 73,
                "strengths": ["decision making"],
                "opportunities_for_growth": ["delegation"],
                "recommended_next_assessment": "Community Builder Assessment",
                "recommendation_confidence": 0.88,
                "completed_at": "2026-06-19T12:00:00Z",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["stored"]["overall_score"], 82)

        growth = self.client.get("/member/assessments/growth-profile", cookies=session_cookie(self.member_id))
        self.assertEqual(growth.status_code, 200)
        profile = growth.json()["growth_profile"]
        self.assertEqual(profile["categories"]["Leadership Archetype Engine"]["latest_score"], 82)
        self.assertEqual(profile["categories"]["Leadership Archetype Engine"]["assessments"]["leadership-core"]["attempts"], 1)
        self.assertIn("First Assessment", [badge["label"] for badge in profile["badges"]])

    def test_signed_garvey_callback_saves_result_for_member_by_email(self):
        response = self.client.post(
            "/garvey/callback",
            headers={"X-Garvey-Callback-Secret": "callback-secret"},
            json={
                "event": "assessment.completed",
                "issuer": "simba_wajuma",
                "member_email": "growth-member@example.com",
                "assessment_id": "voice-of-customer",
                "assessment_type": "voice-of-customer",
                "assessment_name": "Voice of Customer",
                "result_id": "garvey-email-result-1",
                "completion_status": "completed",
                "overall_score": 91,
                "primary_result": {"label": "Community Listener"},
                "completed_at": "2026-06-19T13:00:00Z",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])

        results = self.client.get("/member/assessments/results", cookies=session_cookie(self.member_id))
        self.assertEqual(results.status_code, 200)
        saved = results.json()["results"][0]
        self.assertEqual(saved["result_id"], "garvey-email-result-1")
        self.assertEqual(saved["assessment_name"], "Voice of Customer")
        self.assertEqual(saved["primary_result"]["label"], "Community Listener")

    def test_callback_routes_are_registered(self):
        from app.main import app

        post_routes = {route.path for route in app.routes if "POST" in getattr(route, "methods", set())}
        get_routes = {route.path for route in app.routes if "GET" in getattr(route, "methods", set())}
        self.assertIn("/garvey/callback", post_routes)
        self.assertIn("/api/garvey/callback", post_routes)
        self.assertIn("/api/simbawajuma/assessment-callback", post_routes)
        self.assertIn("/garvey/callback", get_routes)
        self.assertIn("/api/garvey/callback", get_routes)

    def test_unknown_member_callback_is_queued_for_retry(self):
        response = self.client.post(
            "/api/simbawajuma/assessment-callback",
            headers={"X-Garvey-Callback-Secret": "callback-secret"},
            json={
                "event": "assessment.completed",
                "issuer": "simba_wajuma",
                "member_id": "99999",
                "assessment_name": "Leadership Core",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["queued"])


if __name__ == "__main__":
    unittest.main()
