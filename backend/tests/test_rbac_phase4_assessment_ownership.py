import os
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


def _payload(user_id: str | None = None) -> dict:
    body = {
        "responses": [3] * 30,
        "accountId": "acct-1",
        "parentId": "parent-1",
        "childId": "child-1",
    }
    if user_id is not None:
        body["userId"] = user_id
    return body


class RBACPhase4AssessmentOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = Path("/tmp/test_rbac_phase4_assessment_ownership.db")
        if db_path.exists():
            db_path.unlink()
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["ENVIRONMENT"] = "test"
        os.environ["SESSION_SECRET"] = "test-session-secret"

        from app import models  # noqa: F401
        from app.database import Base, SessionLocal, engine
        from app.main import app

        Base.metadata.create_all(bind=engine)
        cls.SessionLocal = SessionLocal
        cls.client = TestClient(app)

    def setUp(self):
        from app.authz import seed_rbac_defaults
        from app.models import LeadershipAssessment, Permission, Role, RolePermission, User, UserRole

        db = self.SessionLocal()
        try:
            db.query(UserRole).delete()
            db.query(RolePermission).delete()
            db.query(Role).delete()
            db.query(Permission).delete()
            db.query(LeadershipAssessment).delete()
            db.query(User).delete()
            db.commit()

            member_one = User(email="member-one-phase4@example.com", password_hash="x", role="member")
            member_two = User(email="member-two-phase4@example.com", password_hash="x", role="member")
            admin = User(email="admin-phase4@example.com", password_hash="x", role="admin")
            superadmin = User(email="superadmin-phase4@example.com", password_hash="x", role="superadmin")
            db.add_all([member_one, member_two, admin, superadmin])
            db.commit()

            seed_rbac_defaults(db)

            self.member_one_id = member_one.id
            self.member_two_id = member_two.id
            self.admin_id = admin.id
            self.superadmin_id = superadmin.id
        finally:
            db.close()

    def test_unauthenticated_submit_and_read_rejected(self):
        submit_response = self.client.post("/assessment/submit", json=_payload())
        read_response = self.client.get(f"/assessment/results/{self.member_one_id}")

        self.assertEqual(submit_response.status_code, 401)
        self.assertEqual(read_response.status_code, 401)

    def test_member_can_submit_and_read_own_assessment(self):
        submit_response = self.client.post(
            "/assessment/submit",
            json=_payload(),
            cookies=session_cookie(self.member_one_id),
        )
        self.assertEqual(submit_response.status_code, 200)
        submit_payload = submit_response.json()
        self.assertEqual(int(submit_payload["userId"]), self.member_one_id)

        read_response = self.client.get(
            f"/assessment/results/{self.member_one_id}",
            cookies=session_cookie(self.member_one_id),
        )
        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(int(read_response.json()["userId"]), self.member_one_id)

    def test_member_cannot_read_other_user_via_path_or_query_override(self):
        self.client.post("/assessment/submit", json=_payload(), cookies=session_cookie(self.member_one_id))

        response = self.client.get(
            f"/assessment/results/{self.member_one_id}?userId={self.member_one_id}&user_id={self.member_one_id}",
            cookies=session_cookie(self.member_two_id),
        )

        self.assertEqual(response.status_code, 404)

    def test_member_cannot_override_submit_user_id_or_create_arbitrary_user(self):
        with self.SessionLocal() as db:
            from app.models import User

            before_users = db.query(User).count()

        response = self.client.post(
            "/assessment/submit",
            json=_payload(user_id="totally-new-user"),
            cookies=session_cookie(self.member_two_id),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.json()["userId"]), self.member_two_id)

        with self.SessionLocal() as db:
            from app.models import LeadershipAssessment, Permission, Role, RolePermission, User, UserRole

            after_users = db.query(User).count()
            member_two_assessments = (
                db.query(LeadershipAssessment)
                .filter(LeadershipAssessment.user_id == self.member_two_id)
                .count()
            )

        self.assertEqual(before_users, after_users)
        self.assertEqual(member_two_assessments, 1)

    def test_member_cannot_access_analytics(self):
        response = self.client.get("/assessment/analytics/roles", cookies=session_cookie(self.member_one_id))
        self.assertEqual(response.status_code, 403)

    def test_admin_and_superadmin_can_access_analytics(self):
        admin_response = self.client.get("/assessment/analytics/roles", cookies=session_cookie(self.admin_id))
        superadmin_response = self.client.get(
            "/assessment/analytics/roles",
            cookies=session_cookie(self.superadmin_id),
        )

        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(superadmin_response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
