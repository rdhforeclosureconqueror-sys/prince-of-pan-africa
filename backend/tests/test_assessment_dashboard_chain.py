import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


def _build_answers(value: int):
    return [value for _ in range(30)]


class AssessmentDashboardChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(cls.temp_dir.name) / "test_assessment.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["ENVIRONMENT"] = "test"
        os.environ["SESSION_SECRET"] = "test-session-secret"

        from app import models  # noqa: F401
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
        from app.models import ActivityLog, LeadershipAssessment, Permission, Role, RolePermission, User, UserRole

        db = self.SessionLocal()
        try:
            db.query(ActivityLog).delete()
            db.query(LeadershipAssessment).delete()
            db.query(UserRole).delete()
            db.query(RolePermission).delete()
            db.query(Role).delete()
            db.query(Permission).delete()
            db.query(User).delete()
            db.commit()

            member = User(email="assess-member@example.com", password_hash="x", role="member")
            db.add(member)
            db.commit()
            db.refresh(member)
            seed_rbac_defaults(db)
            self.member_id = member.id
        finally:
            db.close()

    def test_dashboard_returns_saved_latest_and_history(self):
        cookies = session_cookie(self.member_id)

        first = self.client.post(
            "/assessment/submit",
            json={
                "userId": "family-42",
                "accountId": "acct-1",
                "parentId": "parent-1",
                "childId": "child-9",
                "submissionId": "sub-1",
                "responses": _build_answers(4),
            },
            cookies=cookies,
        )
        self.assertEqual(first.status_code, 200)

        second = self.client.post(
            "/assessment/submit",
            json={
                "userId": "family-42",
                "accountId": "acct-1",
                "parentId": "parent-1",
                "childId": "child-9",
                "submissionId": "sub-2",
                "responses": _build_answers(5),
            },
            cookies=cookies,
        )
        self.assertEqual(second.status_code, 200)
        second_payload = second.json()

        dashboard = self.client.get(f"/assessment/dashboard/{second_payload['userId']}", cookies=cookies)
        self.assertEqual(dashboard.status_code, 200)
        payload = dashboard.json()

        self.assertTrue(payload["saved"])
        self.assertEqual(payload["latest"]["submissionId"], "sub-2")
        self.assertEqual(payload["latest"]["childId"], "child-9")
        self.assertGreaterEqual(len(payload["history"]), 2)

    def test_no_false_success_when_result_missing(self):
        response = self.client.get("/assessment/dashboard/99999", cookies=session_cookie(self.member_id))
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
